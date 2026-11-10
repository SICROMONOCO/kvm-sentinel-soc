"""Tests for the pure state-presentation helpers."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from ctf_scoreboard.core import LeaderboardRow
from ctf_scoreboard.state_support import format_elapsed, leaderboard_payload

UTC = timezone.utc


class StateSupportTests(unittest.TestCase):
    def test_format_elapsed_ranges(self) -> None:
        self.assertEqual(format_elapsed(-5), "0s")
        self.assertEqual(format_elapsed(0), "0s")
        self.assertEqual(format_elapsed(59), "59s")
        self.assertEqual(format_elapsed(60), "1m 00s")
        self.assertEqual(format_elapsed(3599), "59m 59s")
        self.assertEqual(format_elapsed(3600), "1h 00m")
        self.assertEqual(format_elapsed(3661), "1h 01m")

    def test_leaderboard_payload(self) -> None:
        row = LeaderboardRow(
            rank=1,
            username="smoke-team",
            flags_found=3,
            score=425,
            elapsed_seconds=3661,
            last_solve_at=datetime(2026, 11, 9, 19, 44, 30, tzinfo=UTC),
            first_bloods=3,
        )

        board, total_solves, updated = leaderboard_payload([row])

        self.assertEqual(total_solves, 3)
        self.assertEqual(
            board,
            [
                {
                    "rank": "1",
                    "username": "smoke-team",
                    "flags_found": "3",
                    "score": "425",
                    "elapsed": "1h 01m",
                    "last_solve": "19:44:30",
                    "first_bloods": "3",
                }
            ],
        )
        self.assertTrue(updated.endswith(" UTC"))


if __name__ == "__main__":
    unittest.main()
