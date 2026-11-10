"""Tests for input validation and scoring rules."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ctf_scoreboard.core.config import HINT_PENALTY, MAX_FLAG_LENGTH
from ctf_scoreboard.core.scoring import score_for
from ctf_scoreboard.core.validation import (
    constant_time_equal,
    normalize_flag_input,
    normalize_username,
    validate_admin_token,
)


class ValidationTests(unittest.TestCase):
    def test_username_normalization(self) -> None:
        self.assertEqual(normalize_username("  Alice_1  "), "Alice_1")
        self.assertEqual(normalize_username("abc"), "abc")
        self.assertEqual(normalize_username("9lives"), "9lives")
        self.assertEqual(normalize_username("a" * 32), "a" * 32)

    def test_username_rejection(self) -> None:
        invalid = [
            "ab",
            "a" * 33,
            "_leading",
            "-leading",
            ".leading",
            "has space",
            "bang!",
            "tab\ttab",
            "\u00e9crire",
            "",
        ]
        for value in invalid:
            with self.subTest(value=value):
                self.assertIsNone(normalize_username(value))

    def test_flag_input_normalization(self) -> None:
        self.assertEqual(normalize_flag_input("  flag{ok}  "), "flag{ok}")
        self.assertEqual(normalize_flag_input("a" * MAX_FLAG_LENGTH), "a" * MAX_FLAG_LENGTH)

    def test_flag_input_rejection(self) -> None:
        invalid = [
            "",
            "   ",
            "has space",
            "has\ttab",
            "line\nbreak",
            "\x01control",
            "\x7fdel",
            "a" * (MAX_FLAG_LENGTH + 1),
        ]
        for value in invalid:
            with self.subTest(value=value):
                self.assertIsNone(normalize_flag_input(value))

    def test_constant_time_equal(self) -> None:
        self.assertTrue(constant_time_equal("same", "same"))
        self.assertFalse(constant_time_equal("same", "different"))
        self.assertFalse(constant_time_equal("\u2603", "\u2604"))

    def test_admin_token_validation_and_disabled(self) -> None:
        with patch.dict(os.environ, {"ADMIN_TOKEN": "admin-secret"}, clear=False):
            self.assertTrue(validate_admin_token("admin-secret"))
            self.assertFalse(validate_admin_token("wrong"))
            self.assertFalse(validate_admin_token("\u2603"))
        with patch.dict(os.environ, {"ADMIN_TOKEN": ""}, clear=False):
            self.assertFalse(validate_admin_token(""))
            self.assertFalse(validate_admin_token("anything"))


class ScoringTests(unittest.TestCase):
    def test_score_for_solved_flags(self) -> None:
        self.assertEqual(score_for({1}, set()), 100)
        self.assertEqual(score_for({1, 2, 3}, set()), 450)
        self.assertEqual(score_for({2, 3}, set()), 350)

    def test_score_for_hint_penalties(self) -> None:
        self.assertEqual(score_for({1, 2}, {1}), 225)
        self.assertEqual(score_for({1}, {2}), 75)
        self.assertEqual(score_for({1, 2, 3}, {1, 2, 3}), 375)
        self.assertEqual(score_for({1}, {1}), 100 - HINT_PENALTY)

    def test_score_for_clamps_at_zero(self) -> None:
        self.assertEqual(score_for(set(), {1, 2, 3}), 0)
        self.assertEqual(score_for({1}, {1, 2, 3}), 25)


if __name__ == "__main__":
    unittest.main()
