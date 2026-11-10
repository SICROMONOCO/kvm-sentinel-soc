"""SQLite persistence for the CTF scoreboard.

The schema is created idempotently by :func:`init_db`. Every statement is
parameterized; no submitted flag candidate or expected flag value is stored.
"""

from __future__ import annotations

import os
import sqlite3
import time
from datetime import datetime

from ._connection import connect
from ._leaderboard import build_leaderboard
from ._models import LeaderboardRow, PlayerProgress, as_int
from ._schema import SCHEMA
from ._time import normalize_start, to_iso, utc_now
from .config import (
    HINT_PENALTY,
    RATE_LIMIT_ATTEMPTS,
    RATE_LIMIT_PRUNE_SECONDS,
    RATE_LIMIT_WINDOW_SECONDS,
    parse_session_start,
)
from .validation import normalize_username


def init_db(path: str | None = None) -> None:
    """Create the schema (idempotently) and seed the session start if absent."""

    with connect(path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        initial = parse_session_start(os.environ.get("SESSION_START"))
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('session_start', ?)",
            (to_iso(initial),),
        )


def _read_session_start(conn: sqlite3.Connection) -> datetime:
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'session_start'"
    ).fetchone()
    if row is None:
        return utc_now()
    return parse_session_start(str(row["value"]))


def get_session_start(path: str | None = None) -> datetime:
    """Return the stored session start as a timezone-aware UTC datetime."""

    with connect(path) as conn:
        return _read_session_start(conn)


def set_session_start(start: datetime, path: str | None = None) -> None:
    """Persist the session start time."""

    with connect(path) as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('session_start', ?)
            ON CONFLICT (key) DO UPDATE SET value = excluded.value
            """,
            (to_iso(start),),
        )


def try_consume_attempt(
    ip: str,
    username_key: str,
    path: str | None = None,
    success: int = 0,
) -> bool:
    """Atomically admit one attempt unless an IP or username is rate-limited.

    Old rows are pruned first. The gate counts attempts for this IP and this
    username in the configured window, rejects when either reaches the limit,
    and otherwise records the attempt.
    """

    with connect(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            now = time.time()
            conn.execute(
                "DELETE FROM attempts WHERE ts < ?",
                (now - RATE_LIMIT_PRUNE_SECONDS,),
            )
            window_start = now - RATE_LIMIT_WINDOW_SECONDS
            ip_count = as_int(
                conn.execute(
                    "SELECT COUNT(*) FROM attempts WHERE ip = ? AND ts >= ?",
                    (ip, window_start),
                ).fetchone()[0]
            )
            user_count = as_int(
                conn.execute(
                    "SELECT COUNT(*) FROM attempts WHERE username_key = ? AND ts >= ?",
                    (username_key, window_start),
                ).fetchone()[0]
            )

            if ip_count >= RATE_LIMIT_ATTEMPTS or user_count >= RATE_LIMIT_ATTEMPTS:
                conn.execute("COMMIT")
                return False

            conn.execute(
                """
                INSERT INTO attempts (ts, ip, username_key, success)
                VALUES (?, ?, ?, ?)
                """,
                (now, ip, username_key, int(bool(success))),
            )
            conn.execute("COMMIT")
            return True
        except Exception:
            conn.execute("ROLLBACK")
            raise


def register_or_get_player(conn: sqlite3.Connection, username: str) -> int:
    """Return the player id, inserting a new player when needed.

    A concurrent insert that wins the unique constraint is resolved by
    re-selecting the existing row.
    """

    normalized = normalize_username(username)
    if normalized is None:
        raise ValueError("invalid username")

    key = normalized.casefold()
    try:
        cursor = conn.execute(
            """
            INSERT INTO players (username, username_key, created_at)
            VALUES (?, ?, ?)
            """,
            (normalized, key, to_iso(utc_now())),
        )
        return as_int(cursor.lastrowid)
    except sqlite3.IntegrityError:
        row = conn.execute(
            "SELECT id FROM players WHERE username_key = ?", (key,)
        ).fetchone()
        if row is None:
            raise
        return as_int(row["id"])


def record_solve(
    conn: sqlite3.Connection, username: str, flag_no: int, points: int
) -> bool:
    """Record a first solve for one flag; return False for a duplicate."""

    if flag_no not in (1, 2, 3):
        raise ValueError("flag_no must be 1, 2 or 3")

    player_id = register_or_get_player(conn, username)
    try:
        conn.execute(
            """
            INSERT INTO solves (player_id, flag_no, solved_at, points)
            VALUES (?, ?, ?, ?)
            """,
            (player_id, flag_no, to_iso(utc_now()), int(points)),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def record_hint(
    conn: sqlite3.Connection, username: str, flag_no: int, penalty: int
) -> bool:
    """Record one revealed hint; return False for a duplicate."""

    if flag_no not in (1, 2, 3):
        raise ValueError("flag_no must be 1, 2 or 3")

    player_id = register_or_get_player(conn, username)
    try:
        conn.execute(
            """
            INSERT INTO hint_uses (player_id, flag_no, used_at, penalty)
            VALUES (?, ?, ?, ?)
            """,
            (player_id, flag_no, to_iso(utc_now()), int(penalty)),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def get_player_progress(username: str, path: str | None = None) -> PlayerProgress:
    """Return solved flags, revealed hints and score for one player."""

    normalized = normalize_username(username)
    display = normalized or ""

    with connect(path) as conn:
        if normalized is None:
            return PlayerProgress(display, frozenset(), frozenset(), 0)

        player = conn.execute(
            "SELECT id, username FROM players WHERE username_key = ?",
            (normalized.casefold(),),
        ).fetchone()
        if player is None:
            return PlayerProgress(display, frozenset(), frozenset(), 0)

        player_id = as_int(player["id"])
        solved_rows = conn.execute(
            "SELECT flag_no, points FROM solves WHERE player_id = ?",
            (player_id,),
        ).fetchall()
        hint_rows = conn.execute(
            "SELECT flag_no FROM hint_uses WHERE player_id = ?",
            (player_id,),
        ).fetchall()

        solved = frozenset(as_int(row["flag_no"]) for row in solved_rows)
        hints = frozenset(as_int(row["flag_no"]) for row in hint_rows)
        pointed = sum(as_int(row["points"]) for row in solved_rows)
        score = max(0, pointed - HINT_PENALTY * len(hints))
        return PlayerProgress(str(player["username"]), solved, hints, score)


def get_leaderboard(
    session_start: datetime | None = None,
    path: str | None = None,
) -> list[LeaderboardRow]:
    """Return ranked players who have solved at least one flag."""

    with connect(path) as conn:
        start = (
            _read_session_start(conn)
            if session_start is None
            else normalize_start(session_start)
        )
        solve_rows = conn.execute(
            """
            SELECT p.id AS player_id, p.username, p.username_key,
                   s.flag_no, s.solved_at, s.points
            FROM solves AS s
            JOIN players AS p ON p.id = s.player_id
            """
        ).fetchall()
        hint_rows = conn.execute(
            "SELECT player_id, COUNT(*) AS hint_count FROM hint_uses GROUP BY player_id"
        ).fetchall()
        return build_leaderboard(solve_rows, hint_rows, start)


def reset_leaderboard(session_start: datetime, path: str | None = None) -> None:
    """Clear all participation data and set a fresh session start atomically."""

    with connect(path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("DELETE FROM attempts")
            conn.execute("DELETE FROM hint_uses")
            conn.execute("DELETE FROM solves")
            conn.execute("DELETE FROM players")
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES ('session_start', ?)
                ON CONFLICT (key) DO UPDATE SET value = excluded.value
                """,
                (to_iso(session_start),),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
