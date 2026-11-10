"""Input parsing and constant-time secret comparison."""

from __future__ import annotations

import hmac

from .config import MAX_FLAG_LENGTH, MAX_USERNAME_LENGTH, get_admin_token
from .flags import FlagConfig

_ASCII_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
_ASCII_DIGITS = frozenset("0123456789")
_ASCII_ALNUM = _ASCII_LETTERS | _ASCII_DIGITS
_USERNAME_TAIL = _ASCII_ALNUM | frozenset("_-.")


def _encode(value: str) -> bytes:
    """Encode arbitrary text without raising on exotic code points."""

    return value.encode("utf-8", "surrogatepass")


def normalize_username(username: str) -> str | None:
    """Return the stripped display username, or ``None`` when invalid.

    Valid names are 3-32 characters, start with an ASCII alphanumeric, and
    contain only ASCII letters, digits, ``_``, ``-`` and ``.``.
    """

    if not isinstance(username, str):
        return None

    candidate = username.strip()
    if not 3 <= len(candidate) <= MAX_USERNAME_LENGTH:
        return None
    if candidate[0] not in _ASCII_ALNUM:
        return None
    if any(char not in _USERNAME_TAIL for char in candidate[1:]):
        return None
    return candidate


def normalize_flag_input(candidate: str) -> str | None:
    """Return a trimmed flag candidate, or ``None`` when it is unacceptable.

    Input is trimmed, must be non-empty, at most 128 characters, and must not
    contain whitespace or control characters.
    """

    if not isinstance(candidate, str):
        return None

    trimmed = candidate.strip()
    if not trimmed or len(trimmed) > MAX_FLAG_LENGTH:
        return None
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in trimmed):
        return None
    return trimmed


def constant_time_equal(left: str, right: str) -> bool:
    """Compare two strings in constant time using their UTF-8 bytes."""

    if not isinstance(left, str) or not isinstance(right, str):
        return False
    return hmac.compare_digest(_encode(left), _encode(right))


def validate_flag(flag_no: int, candidate: str, flags: FlagConfig) -> bool:
    """Check one flag slot against its configured fragment.

    Only the requested slot is examined, so flag 2 can validate even when
    flag 1 has not been found. Unconfigured or malformed input is False.
    """

    if flag_no not in (1, 2, 3) or not isinstance(candidate, str):
        return False

    expected = flags.expected(flag_no)
    if not expected:
        return False

    submitted = candidate.strip()
    return hmac.compare_digest(_encode(submitted), _encode(expected))


def validate_admin_token(candidate: str) -> bool:
    """Check an admin token in constant time; empty configuration disables it."""

    token = get_admin_token()
    if not token or not isinstance(candidate, str):
        return False
    return hmac.compare_digest(_encode(candidate), _encode(token))
