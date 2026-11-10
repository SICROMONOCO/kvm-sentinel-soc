"""Idempotent SQLite schema for the CTF scoreboard."""

from __future__ import annotations

SCHEMA: str = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    username_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS solves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    flag_no INTEGER NOT NULL CHECK (flag_no BETWEEN 1 AND 3),
    solved_at TEXT NOT NULL,
    points INTEGER NOT NULL,
    UNIQUE (player_id, flag_no)
);

CREATE TABLE IF NOT EXISTS hint_uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    flag_no INTEGER NOT NULL CHECK (flag_no BETWEEN 1 AND 3),
    used_at TEXT NOT NULL,
    penalty INTEGER NOT NULL,
    UNIQUE (player_id, flag_no)
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    ip TEXT NOT NULL,
    username_key TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_attempts_ts ON attempts (ts);
CREATE INDEX IF NOT EXISTS idx_attempts_ip_ts ON attempts (ip, ts);
CREATE INDEX IF NOT EXISTS idx_attempts_user_ts ON attempts (username_key, ts);
"""
