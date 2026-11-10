"""Database, rate-limit, leaderboard and reset tests for the CTF core."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from ctf_scoreboard.core import db
from ctf_scoreboard.core.config import FLAG_POINTS, HINT_PENALTY, parse_session_start

UTC = timezone.utc


def iso(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).isoformat(timespec="microseconds")


class DatabaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "scoreboard.db")
        db.init_db(self.db_path)

    def solve_at(self, username: str, flag_no: int, moment: datetime) -> None:
        with db.connect(self.db_path) as conn:
            player_id = db.register_or_get_player(conn, username)
            conn.execute(
                """
                INSERT INTO solves (player_id, flag_no, solved_at, points)
                VALUES (?, ?, ?, ?)
                """,
                (player_id, flag_no, iso(moment), FLAG_POINTS[flag_no]),
            )

    def hint_at(self, username: str, flag_no: int) -> None:
        with db.connect(self.db_path) as conn:
            player_id = db.register_or_get_player(conn, username)
            conn.execute(
                """
                INSERT INTO hint_uses (player_id, flag_no, used_at, penalty)
                VALUES (?, ?, ?, ?)
                """,
                (player_id, flag_no, iso(datetime.now(UTC)), HINT_PENALTY),
            )

    def count(self, table: str) -> int:
        queries = {
            "players": "SELECT COUNT(*) FROM players",
            "solves": "SELECT COUNT(*) FROM solves",
            "hint_uses": "SELECT COUNT(*) FROM hint_uses",
            "attempts": "SELECT COUNT(*) FROM attempts",
        }
        with db.connect(self.db_path) as conn:
            row = conn.execute(queries[table]).fetchone()
        return int(row[0])


class InitTests(DatabaseTestCase):
    def test_init_is_idempotent_and_keeps_session_start(self) -> None:
        fresh_path = os.path.join(self._tmp.name, "fresh.db")
        initial = "2024-01-01T00:00:00Z"
        with patch.dict(os.environ, {"SESSION_START": initial}, clear=False):
            db.init_db(fresh_path)
        self.assertEqual(db.get_session_start(fresh_path), parse_session_start(initial))

        with patch.dict(os.environ, {"SESSION_START": "2030-06-06T00:00:00Z"}, clear=False):
            db.init_db(fresh_path)
        self.assertEqual(db.get_session_start(fresh_path), parse_session_start(initial))

    def test_env_path_is_used_when_no_argument(self) -> None:
        env_path = os.path.join(self._tmp.name, "from-env", "ctf.db")
        with patch.dict(os.environ, {"CTF_DB_PATH": env_path}, clear=False):
            db.init_db()
        self.assertTrue(os.path.exists(env_path))


class PlayerTests(DatabaseTestCase):
    def test_register_or_get_player_is_case_insensitive(self) -> None:
        with db.connect(self.db_path) as conn:
            first = db.register_or_get_player(conn, "Alice")
            second = db.register_or_get_player(conn, "  alice  ")
            third = db.register_or_get_player(conn, "ALICE")
        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_register_rejects_invalid_username(self) -> None:
        with db.connect(self.db_path) as conn:
            with self.assertRaises(ValueError):
                db.register_or_get_player(conn, "x")

    def test_duplicate_solve_does_not_double_score(self) -> None:
        with db.connect(self.db_path) as conn:
            self.assertTrue(db.record_solve(conn, "Alice", 1, FLAG_POINTS[1]))
            self.assertFalse(db.record_solve(conn, "Alice", 1, FLAG_POINTS[1]))
        progress = db.get_player_progress("Alice", self.db_path)
        self.assertEqual(progress.solved, frozenset({1}))
        self.assertEqual(progress.score, 100)

    def test_duplicate_hint_does_not_double_penalize(self) -> None:
        with db.connect(self.db_path) as conn:
            db.record_solve(conn, "Alice", 1, FLAG_POINTS[1])
            self.assertTrue(db.record_hint(conn, "Alice", 1, HINT_PENALTY))
            self.assertFalse(db.record_hint(conn, "Alice", 1, HINT_PENALTY))
        progress = db.get_player_progress("Alice", self.db_path)
        self.assertEqual(progress.hints, frozenset({1}))
        self.assertEqual(progress.score, 75)

    def test_progress_for_unknown_and_invalid_player(self) -> None:
        unknown = db.get_player_progress("Ghost", self.db_path)
        self.assertEqual(unknown.username, "Ghost")
        self.assertEqual(unknown.solved, frozenset())
        self.assertEqual(unknown.score, 0)

        invalid = db.get_player_progress("x", self.db_path)
        self.assertEqual(invalid.username, "")
        self.assertEqual(invalid.hints, frozenset())


class RateLimitTests(DatabaseTestCase):
    def test_allows_five_attempts_then_blocks(self) -> None:
        results = [
            db.try_consume_attempt("10.0.0.1", "alice", self.db_path)
            for _ in range(6)
        ]
        self.assertEqual(results, [True, True, True, True, True, False])

    def test_blocks_sixth_attempt_for_same_ip(self) -> None:
        results = [
            db.try_consume_attempt("10.0.0.2", f"user{i}", self.db_path)
            for i in range(6)
        ]
        self.assertEqual(results[:5], [True] * 5)
        self.assertFalse(results[5])

    def test_blocks_sixth_attempt_for_same_username(self) -> None:
        results = [
            db.try_consume_attempt(f"10.0.1.{i}", "shared", self.db_path)
            for i in range(6)
        ]
        self.assertEqual(results[:5], [True] * 5)
        self.assertFalse(results[5])

    def test_prunes_stale_attempts(self) -> None:
        with db.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO attempts (ts, ip, username_key, success) VALUES (?, ?, ?, 0)",
                (0.0, "10.0.0.3", "alice"),
            )
        self.assertTrue(db.try_consume_attempt("10.0.0.3", "alice", self.db_path))
        self.assertEqual(self.count("attempts"), 1)


class LeaderboardTests(DatabaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    def test_orders_by_flags_then_elapsed_then_score(self) -> None:
        self.solve_at("Alice", 1, self.start + timedelta(seconds=100))
        self.solve_at("Bob", 1, self.start + timedelta(seconds=50))
        self.solve_at("Carol", 1, self.start + timedelta(seconds=200))
        self.solve_at("Carol", 2, self.start + timedelta(seconds=200))
        self.solve_at("Dave", 1, self.start + timedelta(seconds=100))
        self.hint_at("Dave", 1)

        rows = db.get_leaderboard(self.start, self.db_path)

        self.assertEqual([row.username for row in rows], ["Carol", "Bob", "Alice", "Dave"])
        self.assertEqual([row.rank for row in rows], [1, 2, 3, 4])
        self.assertEqual(rows[0].flags_found, 2)
        self.assertEqual(rows[0].score, 250)
        self.assertEqual(rows[2].elapsed_seconds, 100)
        self.assertEqual(rows[3].score, 75)
        self.assertEqual(rows[0].last_solve_at.tzinfo, UTC)

    def test_only_players_with_solves_appear(self) -> None:
        self.solve_at("Alice", 1, self.start + timedelta(seconds=10))
        with db.connect(self.db_path) as conn:
            db.register_or_get_player(conn, "Lurker")
        rows = db.get_leaderboard(self.start, self.db_path)
        self.assertEqual([row.username for row in rows], ["Alice"])

    def test_negative_elapsed_is_clamped(self) -> None:
        self.solve_at("Alice", 1, self.start - timedelta(seconds=30))
        rows = db.get_leaderboard(self.start, self.db_path)
        self.assertEqual(rows[0].elapsed_seconds, 0)

    def test_first_blood_counts(self) -> None:
        first = self.start + timedelta(seconds=10)
        later = self.start + timedelta(seconds=20)
        third = self.start + timedelta(seconds=25)
        last = self.start + timedelta(seconds=30)
        self.solve_at("Alice", 1, first)
        self.solve_at("Bob", 1, later)
        self.solve_at("Bob", 2, first)
        self.solve_at("Bob", 3, third)
        self.solve_at("Carol", 3, last)

        rows = {row.username: row for row in db.get_leaderboard(self.start, self.db_path)}

        self.assertEqual(rows["Alice"].first_bloods, 1)
        self.assertEqual(rows["Bob"].first_bloods, 2)
        self.assertEqual(rows["Carol"].first_bloods, 0)

    def test_uses_db_session_start_when_argument_omitted(self) -> None:
        db.set_session_start(self.start, self.db_path)
        self.solve_at("Alice", 1, self.start + timedelta(seconds=42))
        rows = db.get_leaderboard(None, self.db_path)
        self.assertEqual(rows[0].elapsed_seconds, 42)


class SessionAndResetTests(DatabaseTestCase):
    def test_set_and_get_session_start(self) -> None:
        naive = datetime(2025, 5, 5, 5, 5, 5)
        db.set_session_start(naive, self.db_path)
        stored = db.get_session_start(self.db_path)
        self.assertEqual(stored.tzinfo, UTC)
        self.assertEqual(stored.replace(tzinfo=None), naive)

    def test_reset_clears_everything_and_updates_start(self) -> None:
        with db.connect(self.db_path) as conn:
            db.record_solve(conn, "Alice", 1, FLAG_POINTS[1])
            db.record_hint(conn, "Alice", 1, HINT_PENALTY)
        db.try_consume_attempt("10.0.0.9", "alice", self.db_path)

        new_start = datetime(2026, 2, 3, 4, 5, 6, tzinfo=UTC)
        db.reset_leaderboard(new_start, self.db_path)

        self.assertEqual(db.get_session_start(self.db_path), new_start)
        self.assertEqual(db.get_leaderboard(None, self.db_path), [])
        self.assertEqual(db.get_player_progress("Alice", self.db_path).solved, frozenset())
        for table in ("players", "solves", "hint_uses", "attempts"):
            with self.subTest(table=table):
                self.assertEqual(self.count(table), 0)


if __name__ == "__main__":
    unittest.main()
