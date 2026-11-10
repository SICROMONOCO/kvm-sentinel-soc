"""Public Reflex state for the standalone CTF scoreboard.

Only non-secret presentation state is client-visible. Expected flag values
never enter a normal state variable: the environment-backed ``FlagConfig`` is
created inside ``submit_flag`` and discarded immediately after validation.
"""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard import core
from ctf_scoreboard.core import db
from ctf_scoreboard.core.config import FLAG_POINTS, HINTS
from ctf_scoreboard.core.flags import flag_config_from_env
from ctf_scoreboard.core.validation import (
    normalize_flag_input,
    normalize_username,
    validate_flag,
)
from ctf_scoreboard.state_support import client_ip, leaderboard_payload


class ScoreboardState(rx.State):
    """Public leaderboard, submission form and per-team progress."""

    # --- Submission form -------------------------------------------------
    username: str = ""
    flag_no: str = "1"
    flag_value: str = ""
    message: str = ""
    message_kind: str = "info"  # info | success | error | warning

    # --- Leaderboard / session ------------------------------------------
    leaderboard: list[dict[str, str]] = []
    team_count: int = 0
    solve_count: int = 0
    session_start_display: str = ""
    updated_display: str = ""

    # --- Current player view --------------------------------------------
    player_name: str = ""
    player_score: int = 0
    flag_1_solved: bool = False
    flag_2_solved: bool = False
    flag_3_solved: bool = False
    hint_1_revealed: bool = False
    hint_1_text: str = ""
    hint_2_revealed: bool = False
    hint_2_text: str = ""
    hint_3_revealed: bool = False
    hint_3_text: str = ""

    # ------------------------------------------------------------------
    # Lifecycle / refresh
    # ------------------------------------------------------------------
    @rx.event
    def load(self) -> None:
        """Initialise storage and populate the board for a fresh page load."""

        db.init_db()
        self.session_start_display = db.get_session_start().strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        self.refresh_leaderboard()

    @rx.event
    def tick(self, _date: str | None = None) -> None:
        """Refresh only the leaderboard; called by the 5-second page ticker."""

        self.refresh_leaderboard()

    # ------------------------------------------------------------------
    # Submission form events
    # ------------------------------------------------------------------
    @rx.event
    def set_username(self, value: str) -> None:
        """Store the typed team name and drop progress from a different team."""

        previous_key = (normalize_username(self.username) or "").casefold()
        next_key = (normalize_username(value) or "").casefold()
        self.username = value
        if previous_key != next_key:
            self._clear_player_view()
            self.message = ""
            self.message_kind = "info"

    @rx.event
    def set_flag_no(self, value: str) -> None:
        """Accept only the three real stage numbers."""

        self.flag_no = value if value in ("1", "2", "3") else "1"

    @rx.event
    def set_flag_value(self, value: str) -> None:
        """Store the fragment candidate without validating it client-side."""

        self.flag_value = value

    @rx.event
    def submit_flag(self) -> None:
        """Validate one fragment server-side and record the first solve."""

        username = normalize_username(self.username)
        if username is None:
            self._message(
                "Enter a team name with 3-32 characters: letters, digits, "
                "underscore, hyphen or dot.",
                "error",
            )
            return
        self.username = username

        candidate = normalize_flag_input(self.flag_value)
        if candidate is None:
            self._message(
                "Enter a valid fragment: 1-128 characters with no whitespace.",
                "error",
            )
            return

        try:
            flag_no = int(self.flag_no)
        except (TypeError, ValueError):
            self._message("Select a valid flag stage (1, 2 or 3).", "error")
            return
        if flag_no not in FLAG_POINTS:
            self._message("Select a valid flag stage (1, 2 or 3).", "error")
            return

        ip = self._client_ip()
        try:
            admitted = db.try_consume_attempt(ip, username.casefold())
        except Exception:
            self._message(
                "Scoreboard storage is unavailable. Try again shortly.",
                "error",
            )
            return
        if not admitted:
            self._message(
                f"Rate limit reached: {core.RATE_LIMIT_ATTEMPTS} attempts per minute per IP and team. "
                "Wait a minute and try again.",
                "warning",
            )
            return

        flags = flag_config_from_env()
        if not validate_flag(flag_no, candidate, flags):
            self._message(
                "Flag not accepted. Verify the fragment and the selected stage.",
                "error",
            )
            return

        try:
            with db.connect() as conn:
                recorded = db.record_solve(
                    conn, username, flag_no, FLAG_POINTS[flag_no]
                )
        except Exception:
            self._message(
                "Scoreboard storage is unavailable. Try again shortly.",
                "error",
            )
            return

        if not recorded:
            self._message("Already recorded for this team.", "warning")
            self._refresh_progress(username)
            self.refresh_leaderboard()
            return

        self.flag_value = ""
        self._message(
            f"Flag {flag_no} accepted. +{FLAG_POINTS[flag_no]} points.",
            "success",
        )
        self._refresh_progress(username)
        self.refresh_leaderboard()

    @rx.event
    def reveal_hint(self, flag_no: int) -> None:
        """Record the one-time hint penalty and only then expose the riddle."""

        username = normalize_username(self.username)
        if username is None:
            self._message(
                "Enter a valid team name before revealing a hint.",
                "error",
            )
            return
        if flag_no not in HINTS:
            self._message("Invalid hint selection.", "error")
            return

        already_visible = (
            (flag_no == 1 and self.hint_1_revealed)
            or (flag_no == 2 and self.hint_2_revealed)
            or (flag_no == 3 and self.hint_3_revealed)
        )

        if already_visible:
            self._message(
                "Hint already revealed for this team. No additional penalty.",
                "info",
            )
        else:
            try:
                with db.connect() as conn:
                    recorded = db.record_hint(
                        conn, username, flag_no, core.HINT_PENALTY
                    )
            except Exception:
                self._message(
                    "Scoreboard storage is unavailable. Try again shortly.",
                    "error",
                )
                return

            if recorded:
                self._message(
                    f"Hint {flag_no} revealed. -{core.HINT_PENALTY} points.",
                    "warning",
                )
            else:
                self._message(
                    "Hint already revealed for this team. No additional penalty.",
                    "info",
                )

        self._show_hint(flag_no)
        self._refresh_progress(username)
        self.refresh_leaderboard()

    # ------------------------------------------------------------------
    # Private helpers (not events)
    # ------------------------------------------------------------------
    def _client_ip(self) -> str:
        """Resolve the best available client IP without trusting a full chain."""

        return client_ip(self.router)

    def _refresh_progress(self, username: str) -> None:
        """Load one team's solves, score and already-revealed hints."""

        progress = db.get_player_progress(username)
        self.player_name = progress.username
        self.player_score = progress.score
        self.flag_1_solved = 1 in progress.solved
        self.flag_2_solved = 2 in progress.solved
        self.flag_3_solved = 3 in progress.solved
        self._sync_hint_state(progress.hints)

    def _clear_player_view(self) -> None:
        """Forget the current team, its score, solves and revealed hints."""

        self.player_name = ""
        self.player_score = 0
        self.flag_1_solved = False
        self.flag_2_solved = False
        self.flag_3_solved = False
        self.hint_1_revealed = False
        self.hint_1_text = ""
        self.hint_2_revealed = False
        self.hint_2_text = ""
        self.hint_3_revealed = False
        self.hint_3_text = ""

    def _sync_hint_state(self, hints: frozenset[int]) -> None:
        """Mirror only already-paid hints into the client-visible state."""

        self.hint_1_revealed = 1 in hints
        self.hint_1_text = HINTS[1] if 1 in hints else ""
        self.hint_2_revealed = 2 in hints
        self.hint_2_text = HINTS[2] if 2 in hints else ""
        self.hint_3_revealed = 3 in hints
        self.hint_3_text = HINTS[3] if 3 in hints else ""

    def _show_hint(self, flag_no: int) -> None:
        """Expose one riddle after its penalty has been recorded."""

        if flag_no == 1:
            self.hint_1_revealed = True
            self.hint_1_text = HINTS[1]
        elif flag_no == 2:
            self.hint_2_revealed = True
            self.hint_2_text = HINTS[2]
        elif flag_no == 3:
            self.hint_3_revealed = True
            self.hint_3_text = HINTS[3]

    def refresh_leaderboard(self) -> None:
        """Rebuild the string-only leaderboard payload for the table."""

        try:
            rows = db.get_leaderboard()
        except Exception:
            self.updated_display = "sync unavailable"
            return

        self.leaderboard, self.solve_count, self.updated_display = leaderboard_payload(
            rows
        )
        self.team_count = len(self.leaderboard)

    def _message(self, text: str, kind: str = "info") -> None:
        """Set the public form message and its colour category."""

        self.message = text
        self.message_kind = kind
