"""Public value objects and small row helpers for the SQLite layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PlayerProgress:
    """A single player's solved flags, revealed hints and current score."""

    username: str
    solved: frozenset[int]
    hints: frozenset[int]
    score: int


@dataclass(frozen=True, slots=True)
class LeaderboardRow:
    """One ranked leaderboard entry."""

    rank: int
    username: str
    flags_found: int
    score: int
    elapsed_seconds: int
    last_solve_at: datetime
    first_bloods: int


def as_int(value: object) -> int:
    """Convert a sqlite3 row value to ``int`` without a bare cast."""

    if isinstance(value, int):
        return value
    return int(str(value))
