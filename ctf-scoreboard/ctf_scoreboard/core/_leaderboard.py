"""Leaderboard aggregation kept separate from the persistence primitives."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime

from ._models import LeaderboardRow, as_int
from ._time import from_iso
from .config import HINT_PENALTY


@dataclass(slots=True)
class _Aggregate:
    """Mutable per-player accumulator used while building the leaderboard."""

    username: str
    username_key: str
    points: int = 0
    timestamps: set[datetime] = field(default_factory=set)
    flags: set[int] = field(default_factory=set)
    flag_times: dict[int, datetime] = field(default_factory=dict)


def build_leaderboard(
    solve_rows: list[sqlite3.Row],
    hint_rows: list[sqlite3.Row],
    start: datetime,
) -> list[LeaderboardRow]:
    """Rank solve rows by flags, elapsed time, score and username.

    Only players present in ``solve_rows`` appear. First blood is the earliest
    timestamp per flag; a player earns one credit for each flag they solved at
    that earliest timestamp.
    """

    if not solve_rows:
        return []

    hints_by_player = {
        as_int(row["player_id"]): as_int(row["hint_count"]) for row in hint_rows
    }

    first_blood_at: dict[int, datetime] = {}
    players: dict[int, _Aggregate] = {}

    for row in solve_rows:
        player_id = as_int(row["player_id"])
        flag_no = as_int(row["flag_no"])
        solved_at = from_iso(str(row["solved_at"]))
        aggregate = players.get(player_id)
        if aggregate is None:
            aggregate = _Aggregate(
                username=str(row["username"]),
                username_key=str(row["username_key"]),
            )
            players[player_id] = aggregate
        aggregate.points += as_int(row["points"])
        aggregate.timestamps.add(solved_at)
        aggregate.flags.add(flag_no)
        aggregate.flag_times[flag_no] = solved_at

        current_best = first_blood_at.get(flag_no)
        if current_best is None or solved_at < current_best:
            first_blood_at[flag_no] = solved_at

    entries: list[tuple[tuple[object, ...], LeaderboardRow]] = []
    for player_id, aggregate in players.items():
        last_solve = max(aggregate.timestamps)
        elapsed = max(0, int((last_solve - start).total_seconds()))
        score = max(
            0,
            aggregate.points - HINT_PENALTY * hints_by_player.get(player_id, 0),
        )
        first_bloods = sum(
            1
            for flag_no, solved_at in aggregate.flag_times.items()
            if first_blood_at.get(flag_no) == solved_at
        )
        row = LeaderboardRow(
            rank=0,
            username=aggregate.username,
            flags_found=len(aggregate.flags),
            score=score,
            elapsed_seconds=elapsed,
            last_solve_at=last_solve,
            first_bloods=first_bloods,
        )
        sort_key = (
            -row.flags_found,
            row.elapsed_seconds,
            -row.score,
            row.last_solve_at,
            aggregate.username_key,
        )
        entries.append((sort_key, row))

    entries.sort(key=lambda item: item[0])
    return [
        LeaderboardRow(
            rank=index,
            username=row.username,
            flags_found=row.flags_found,
            score=row.score,
            elapsed_seconds=row.elapsed_seconds,
            last_solve_at=row.last_solve_at,
            first_bloods=row.first_bloods,
        )
        for index, (_sort_key, row) in enumerate(entries, start=1)
    ]
