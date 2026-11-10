"""SQLite connection factory and database path resolution."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .config import DEFAULT_DB_PATH


def resolve_path(path: str | None) -> str:
    """Resolve an explicit path, then env overrides, then the default."""

    if path:
        return path
    return os.environ.get("CTF_DB_PATH") or os.environ.get("DB_PATH") or DEFAULT_DB_PATH


@contextmanager
def connect(path: str | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a new autocommit connection and always close it."""

    resolved = resolve_path(path)
    parent = os.path.dirname(resolved)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(resolved, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        yield conn
    finally:
        conn.close()
