"""Reflex-independent core for the standalone CTF scoreboard."""

from __future__ import annotations

from .config import (
    DEFAULT_DB_PATH,
    FLAG_POINTS,
    HINT_PENALTY,
    HINTS,
    MAX_FLAG_LENGTH,
    MAX_USERNAME_LENGTH,
    RATE_LIMIT_ATTEMPTS,
    RATE_LIMIT_PRUNE_SECONDS,
    RATE_LIMIT_WINDOW_SECONDS,
    get_admin_token,
    parse_session_start,
)
from .db import (
    LeaderboardRow,
    PlayerProgress,
    connect,
    get_leaderboard,
    get_player_progress,
    get_session_start,
    init_db,
    record_hint,
    record_solve,
    register_or_get_player,
    reset_leaderboard,
    set_session_start,
    try_consume_attempt,
)
from .flags import FlagConfig, flag_config_from_env
from .scoring import score_for
from .validation import (
    constant_time_equal,
    normalize_flag_input,
    normalize_username,
    validate_admin_token,
    validate_flag,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "FLAG_POINTS",
    "HINT_PENALTY",
    "HINTS",
    "MAX_FLAG_LENGTH",
    "MAX_USERNAME_LENGTH",
    "RATE_LIMIT_ATTEMPTS",
    "RATE_LIMIT_PRUNE_SECONDS",
    "RATE_LIMIT_WINDOW_SECONDS",
    "FlagConfig",
    "LeaderboardRow",
    "PlayerProgress",
    "connect",
    "constant_time_equal",
    "flag_config_from_env",
    "get_admin_token",
    "get_leaderboard",
    "get_player_progress",
    "get_session_start",
    "init_db",
    "normalize_flag_input",
    "normalize_username",
    "parse_session_start",
    "record_hint",
    "record_solve",
    "register_or_get_player",
    "reset_leaderboard",
    "score_for",
    "set_session_start",
    "try_consume_attempt",
    "validate_admin_token",
    "validate_flag",
]
