"""Public scoreboard page."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.core.config import FLAG_POINTS, HINT_PENALTY
from ctf_scoreboard.state import ScoreboardState

from .base import _stat_card
from .layout import _hero, _page_shell
from .leaderboard import _leaderboard_panel
from .hints import _hints_panel
from .submission import _submission_panel


def index_page() -> rx.Component:
    """Public scoreboard page."""

    return _page_shell(
        rx.vstack(
            _hero(),
            rx.grid(
                _stat_card(
                    "Teams ranked",
                    ScoreboardState.team_count,
                    "active board",
                    "trophy",
                ),
                _stat_card(
                    "Flags solved",
                    ScoreboardState.solve_count,
                    "across all teams",
                    "flag",
                ),
                _stat_card(
                    "Max score",
                    str(sum(FLAG_POINTS.values())),
                    " / ".join(str(points) for points in FLAG_POINTS.values()),
                    "target",
                ),
                _stat_card(
                    "Hint penalty",
                    f"-{HINT_PENALTY}",
                    "per revealed hint",
                    "triangle_alert",
                ),
                columns="repeat(auto-fit, minmax(170px, 1fr))",
                spacing="3",
                width="100%",
            ),
            rx.grid(
                _submission_panel(),
                _hints_panel(),
                columns="repeat(auto-fit, minmax(330px, 1fr))",
                spacing="4",
                width="100%",
                align_items="start",
            ),
            _leaderboard_panel(),
            rx.moment(
                interval=5000,
                on_change=ScoreboardState.tick,
                display="none",
            ),
            spacing="5",
            align="stretch",
            width="100%",
        ),
        ScoreboardState,
    )
