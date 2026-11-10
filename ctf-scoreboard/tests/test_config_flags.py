"""Tests for configuration, flag fragments and session-start parsing."""

from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from ctf_scoreboard.core import config
from ctf_scoreboard.core.config import (
    FLAG_POINTS,
    HINT_PENALTY,
    HINTS,
    parse_session_start,
)
from ctf_scoreboard.core.flags import FlagConfig, flag_config_from_env
from ctf_scoreboard.core.validation import validate_flag

UTC = timezone.utc


class ConfigTests(unittest.TestCase):
    def test_constants_and_hints(self) -> None:
        self.assertEqual(FLAG_POINTS, {1: 100, 2: 150, 3: 200})
        self.assertEqual(HINT_PENALTY, 25)
        self.assertEqual(set(HINTS), {1, 2, 3})
        self.assertTrue(all(isinstance(text, str) and text for text in HINTS.values()))

    def test_parse_session_start_with_z(self) -> None:
        parsed = parse_session_start("2024-01-02T03:04:05Z")
        self.assertEqual(parsed.tzinfo, UTC)
        self.assertEqual((parsed.hour, parsed.minute, parsed.second), (3, 4, 5))

    def test_parse_session_start_naive_is_utc(self) -> None:
        parsed = parse_session_start("2024-01-02T03:04:05")
        self.assertEqual(parsed.tzinfo, UTC)
        self.assertEqual(parsed.hour, 3)

    def test_parse_session_start_converts_offset(self) -> None:
        parsed = parse_session_start("2024-01-02T03:04:05+02:00")
        self.assertEqual(parsed.tzinfo, UTC)
        self.assertEqual(parsed.hour, 1)

    def test_parse_session_start_blank_means_now(self) -> None:
        before = datetime.now(UTC)
        for value in (None, "", "   "):
            with self.subTest(value=value):
                parsed = parse_session_start(value)
                self.assertEqual(parsed.tzinfo, UTC)
                self.assertLessEqual(abs((parsed - before).total_seconds()), 5)

    def test_parse_session_start_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_session_start("not-a-timestamp")

    def test_admin_token_read_from_env(self) -> None:
        with patch.dict(os.environ, {"ADMIN_TOKEN": "  token-value  "}, clear=False):
            self.assertEqual(config.get_admin_token(), "token-value")


class FlagTests(unittest.TestCase):
    def test_three_flags_validate_independently(self) -> None:
        env = {
            "FLAG_PART1": "first-fragment",
            "FLAG_PART2": "second-fragment",
            "FLAG_PART3": "third-fragment",
        }
        with patch.dict(os.environ, env, clear=False):
            config_value = flag_config_from_env()
        self.assertTrue(validate_flag(1, "first-fragment", config_value))
        self.assertTrue(validate_flag(2, "second-fragment", config_value))
        self.assertTrue(validate_flag(3, "third-fragment", config_value))
        self.assertFalse(validate_flag(1, "second-fragment", config_value))
        self.assertTrue(validate_flag(2, "second-fragment", config_value))

    def test_flag_candidate_is_trimmed(self) -> None:
        cfg = FlagConfig("one", "two", "three")
        self.assertTrue(validate_flag(1, "  one  ", cfg))

    def test_wrong_empty_and_unconfigured_flags_fail(self) -> None:
        cfg = FlagConfig("one", "", "three")
        self.assertFalse(validate_flag(1, "wrong", cfg))
        self.assertFalse(validate_flag(1, "", cfg))
        self.assertFalse(validate_flag(2, "", cfg))
        self.assertFalse(validate_flag(2, "anything", cfg))
        self.assertFalse(validate_flag(0, "one", cfg))
        self.assertFalse(validate_flag(4, "three", cfg))

    def test_non_ascii_candidate_does_not_raise(self) -> None:
        cfg = FlagConfig("one", "two", "three")
        for candidate in ("\u2603", "\U0001f4a5\U0001f4a5", "\u00e9\u00e8"):
            with self.subTest(candidate=candidate):
                self.assertFalse(validate_flag(1, candidate, cfg))

    def test_flag_config_from_env_reads_once_per_call(self) -> None:
        with patch.dict(os.environ, {"FLAG_PART1": "alpha"}, clear=False):
            self.assertEqual(flag_config_from_env().part1, "alpha")
        with patch.dict(os.environ, {"FLAG_PART1": "beta"}, clear=False):
            self.assertEqual(flag_config_from_env().part1, "beta")


if __name__ == "__main__":
    unittest.main()
