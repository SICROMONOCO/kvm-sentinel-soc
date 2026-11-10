"""Public hint cards and panel."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.core.config import HINT_PENALTY
from ctf_scoreboard.state import ScoreboardState

from .base import (
    ACCENT,
    BORDER,
    GHOST_BUTTON_STYLE,
    MONO,
    MUTED,
    TEXT,
    WARNING,
    _badge,
    _label,
    _panel,
)


def _hint_card(
    stage: int,
    title: str,
    revealed: bool | rx.Var[bool],
    text: str | rx.Var[str],
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.flex(
                rx.hstack(
                    rx.text(
                        f"0{stage}",
                        font_family=MONO,
                        font_size="11px",
                        color=ACCENT,
                    ),
                    _label(title),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    revealed,
                    _badge("REVEALED", ACCENT, "rgba(53,242,193,0.07)"),
                    _badge(f"-{HINT_PENALTY} PTS", WARNING, "rgba(251,191,36,0.06)"),
                ),
                justify="between",
                align="center",
                width="100%",
                gap="3",
            ),
            rx.cond(
                revealed,
                rx.text(
                    text,
                    color=TEXT,
                    font_size="13px",
                    line_height="1.65",
                ),
                rx.text(
                    "Locked. Reveal the riddle and accept the penalty.",
                    color=MUTED,
                    font_size="12px",
                    line_height="1.55",
                ),
            ),
            rx.cond(
                revealed,
                rx.hstack(
                    rx.icon("lock_open", size=13, color=ACCENT),
                    rx.text(
                        "Unlocked for this team",
                        color=ACCENT,
                        font_family=MONO,
                        font_size="10px",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("lock", size=13),
                        rx.text("REVEAL HINT"),
                        spacing="2",
                        align="center",
                    ),
                    on_click=ScoreboardState.reveal_hint(stage),
                    style=GHOST_BUTTON_STYLE,
                ),
            ),
            spacing="3",
            align="stretch",
        ),
        border=f"1px solid {BORDER}",
        border_radius="12px",
        padding="14px",
        bg="rgba(255,255,255,0.018)",
        width="100%",
    )


def _hints_panel() -> rx.Component:
    return _panel(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    _label("Field notes"),
                    rx.heading(
                        "Hints",
                        size="4",
                        font_family=MONO,
                        letter_spacing="-0.03em",
                        color=TEXT,
                        margin="0",
                    ),
                ),
                _badge(f"-{HINT_PENALTY} PTS EACH", WARNING),
                justify="between",
                align="start",
                width="100%",
                gap="3",
            ),
            rx.text(
                "Hints are charged to the team name in the submission form. "
                "The board records the first reveal only.",
                color=MUTED,
                font_size="12px",
                line_height="1.55",
            ),
            _hint_card(
                1,
                "Filesystem",
                ScoreboardState.hint_1_revealed,
                ScoreboardState.hint_1_text,
            ),
            _hint_card(
                2,
                "Identity",
                ScoreboardState.hint_2_revealed,
                ScoreboardState.hint_2_text,
            ),
            _hint_card(
                3,
                "Telemetry",
                ScoreboardState.hint_3_revealed,
                ScoreboardState.hint_3_text,
            ),
            spacing="4",
            align="stretch",
        )
    )
