"""Pure scoring rules for the CTF scoreboard."""

from __future__ import annotations

from collections.abc import Iterable

from .config import FLAG_POINTS, HINT_PENALTY


def score_for(solved: Iterable[int], hinted: Iterable[int]) -> int:
    """Return a player's score, clamped at zero.

    ``hinted`` may include slots that were never solved; each revealed hint
    costs the same fixed penalty.
    """

    solved_slots = set(solved)
    pointed = sum(FLAG_POINTS.get(slot, 0) for slot in solved_slots)
    penalty = HINT_PENALTY * len(set(hinted))
    return max(0, pointed - penalty)
