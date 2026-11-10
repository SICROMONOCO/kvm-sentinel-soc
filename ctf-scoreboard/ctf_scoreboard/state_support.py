"""Pure helpers for translating backend rows into client-facing state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ctf_scoreboard.core import LeaderboardRow


def format_elapsed(seconds: int) -> str:
    """Render elapsed seconds as ``Xs``, ``Xm YYs`` or ``Xh YYm``."""

    total = max(0, int(seconds))
    if total < 60:
        return f"{total}s"
    if total < 3600:
        return f"{total // 60}m {total % 60:02d}s"
    return f"{total // 3600}h {(total % 3600) // 60:02d}m"


def leaderboard_payload(
    rows: list[LeaderboardRow],
) -> tuple[list[dict[str, str]], int, str]:
    """Return the table rows, total solve count and sync label."""

    board: list[dict[str, str]] = []
    total_solves = 0
    for row in rows:
        total_solves += row.flags_found
        board.append(
            {
                "rank": str(row.rank),
                "username": row.username,
                "flags_found": str(row.flags_found),
                "score": str(row.score),
                "elapsed": format_elapsed(row.elapsed_seconds),
                "last_solve": row.last_solve_at.astimezone(timezone.utc).strftime(
                    "%H:%M:%S"
                ),
                "first_bloods": str(row.first_bloods),
            }
        )
    updated = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    return board, total_solves, updated


def client_ip(router: Any) -> str:
    """Resolve the first forwarded hop, falling back to the session client IP."""

    forwarded = ""
    try:
        raw_headers = getattr(getattr(router, "headers", None), "raw_headers", {})
        forwarded = (raw_headers or {}).get("x-forwarded-for", "") or ""
    except Exception:
        forwarded = ""

    candidate = forwarded.split(",")[0].strip() if forwarded else ""
    if not candidate:
        try:
            candidate = getattr(getattr(router, "session", None), "client_ip", "") or ""
        except Exception:
            candidate = ""
    return candidate.strip()[:64] or "unknown"
