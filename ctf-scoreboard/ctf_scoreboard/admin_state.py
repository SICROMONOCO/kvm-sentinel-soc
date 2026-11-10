"""Backend-only state for the destructive admin reset workflow.

The admin token is held in an underscore-prefixed field, which Reflex keeps
out of client state deltas. The class inherits the public scoreboard state so
the admin page can reuse the board refresh and player-view helpers.
"""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.core import db
from ctf_scoreboard.core.config import get_admin_token, parse_session_start
from ctf_scoreboard.core.validation import validate_admin_token
from ctf_scoreboard.state import ScoreboardState


class AdminState(ScoreboardState):
    """Admin reset fields and events, layered over the public state."""

    admin_enabled: bool = False
    admin_session_start: str = ""
    admin_confirm: bool = False
    admin_message: str = ""
    admin_message_kind: str = "info"

    # Backend-only: Reflex keeps underscore-prefixed fields out of client
    # state deltas. It is never bound to a rendered prop.
    _admin_token: str = ""

    @rx.event
    def load(self) -> None:
        """Initialise storage and expose whether the admin console is enabled."""

        db.init_db()
        self.admin_enabled = bool(get_admin_token())
        self.session_start_display = db.get_session_start().strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        self.refresh_leaderboard()

    @rx.event
    def set_admin_token(self, value: str) -> None:
        """Keep the token in the backend-only state field."""

        self._admin_token = value

    @rx.event
    def set_admin_session_start(self, value: str) -> None:
        """Store the optional ISO-8601 reset start."""

        self.admin_session_start = value

    @rx.event
    def set_admin_confirm(self, value: bool) -> None:
        """Store the destructive-action confirmation checkbox."""

        self.admin_confirm = value

    @rx.event
    def reset_leaderboard(self) -> None:
        """Authenticate and destructively start a fresh session."""

        if not self.admin_enabled:
            self._admin_message(
                "Admin reset is disabled. Set ADMIN_TOKEN and recreate the "
                "container.",
                "error",
            )
            return
        if not validate_admin_token(self._admin_token):
            self._admin_message("Invalid admin token.", "error")
            return
        if not self.admin_confirm:
            self._admin_message(
                "Confirm the destructive reset before continuing.",
                "warning",
            )
            return

        try:
            start = parse_session_start(self.admin_session_start)
        except ValueError:
            self._admin_message(
                "Session start must be a valid ISO-8601 timestamp, or blank "
                "to start now.",
                "error",
            )
            return

        try:
            db.reset_leaderboard(start)
        except Exception:
            self._admin_message(
                "Reset failed because scoreboard storage is unavailable.",
                "error",
            )
            return

        self._admin_token = ""
        self.admin_confirm = False
        self._clear_player_view()
        self.flag_value = ""
        self.message = ""
        self.message_kind = "info"
        self.refresh_leaderboard()
        self.session_start_display = start.strftime("%Y-%m-%d %H:%M UTC")
        self._admin_message(
            "Leaderboard reset complete. A new session has started.",
            "success",
        )

    def _admin_message(self, text: str, kind: str = "info") -> None:
        """Set the admin-page message and its colour category."""

        self.admin_message = text
        self.admin_message_kind = kind
