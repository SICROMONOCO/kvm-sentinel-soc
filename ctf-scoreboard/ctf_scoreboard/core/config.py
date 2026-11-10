"""Runtime configuration for the standalone CTF scoreboard core.

Values are read from the environment at the moment they are needed so that a
test (or a long-running process) can change them without reloading the module.
No expected flag value is ever logged or persisted by this module.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "ctf.db")
"""Fallback SQLite location: ``ctf-scoreboard/ctf.db``."""

FLAG_POINTS: dict[int, int] = {1: 100, 2: 150, 3: 200}
HINT_PENALTY: int = 25
RATE_LIMIT_ATTEMPTS: int = 5
RATE_LIMIT_WINDOW_SECONDS: int = 60
RATE_LIMIT_PRUNE_SECONDS: int = 3600
MAX_USERNAME_LENGTH: int = 32
MAX_FLAG_LENGTH: int = 128

HINTS: dict[int, str] = {
    1: "Behind the door that welcomes every knock, a whisper sleeps where backups rot.",
    2: (
        "A borrowed shell remembers a name the watchers cannot ignore; speak it back "
        "through the trap and read their incident ledger."
    ),
    3: (
        "A ghost signed in from 203.0.113.66 and left no trace but one line; ask the "
        "river of logs for the password that never was."
    ),
}


def get_admin_token() -> str:
    """Return the admin token, or an empty string when admin is disabled."""

    return os.environ.get("ADMIN_TOKEN", "").strip()


def parse_session_start(raw: str | None) -> datetime:
    """Parse an ISO-8601 session start into a timezone-aware UTC datetime.

    ``None``/blank means "now". A trailing ``Z`` is accepted as UTC, and a
    naive datetime is interpreted as UTC. Anything unparseable raises
    ``ValueError``.
    """

    if raw is None or not raw.strip():
        return datetime.now(timezone.utc)

    text = raw.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid session start: {raw!r}") from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
