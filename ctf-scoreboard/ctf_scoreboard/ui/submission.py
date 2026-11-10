"""Public fragment submission panel."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.state import ScoreboardState

from .base import (
    ACCENT_2,
    BORDER,
    BUTTON_STYLE,
    INPUT_STYLE,
    MONO,
    MUTED,
    TEXT,
    _label,
    _panel,
    _stage_badge,
    message_box,
)


def _submission_panel() -> rx.Component:
    return _panel(
        rx.vstack(
            _label("Submission terminal"),
            rx.heading(
                "Submit a fragment",
                size="4",
                font_family=MONO,
                letter_spacing="-0.03em",
                color=TEXT,
                margin="0",
            ),
            rx.text(
                "Enter only the fragment value. Do not include ",
                rx.code("flag_partN=", color=ACCENT_2, font_family=MONO),
                ".",
                color=MUTED,
                font_size="12px",
                line_height="1.55",
            ),
            rx.vstack(
                _label("Team name"),
                rx.input(
                    value=ScoreboardState.username,
                    on_change=ScoreboardState.set_username,
                    placeholder="team-orion",
                    max_length=32,
                    style=INPUT_STYLE,
                ),
                spacing="2",
                align="stretch",
                width="100%",
            ),
            rx.flex(
                rx.vstack(
                    _label("Stage"),
                    rx.select(
                        ["1", "2", "3"],
                        value=ScoreboardState.flag_no,
                        on_change=ScoreboardState.set_flag_no,
                        style=INPUT_STYLE,
                    ),
                    spacing="2",
                    align="stretch",
                    flex="0 0 108px",
                    min_width="108px",
                ),
                rx.vstack(
                    _label("Fragment"),
                    rx.input(
                        value=ScoreboardState.flag_value,
                        on_change=ScoreboardState.set_flag_value,
                        placeholder="paste the recovered fragment",
                        max_length=128,
                        style=INPUT_STYLE,
                    ),
                    spacing="2",
                    align="stretch",
                    flex="1 1 220px",
                    min_width="0",
                ),
                gap="3",
                align="end",
                wrap="wrap",
                width="100%",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("terminal", size=15),
                    rx.text("SUBMIT FRAGMENT"),
                    spacing="2",
                    align="center",
                ),
                on_click=ScoreboardState.submit_flag,
                style=BUTTON_STYLE,
            ),
            message_box(ScoreboardState.message, ScoreboardState.message_kind),
            rx.divider(border_color=BORDER, margin_y="2px"),
            rx.flex(
                rx.vstack(
                    _label("Current score"),
                    rx.text(
                        ScoreboardState.player_score,
                        font_family=MONO,
                        font_size="24px",
                        font_weight="700",
                        color=TEXT,
                    ),
                    spacing="1",
                    align="start",
                    min_width="120px",
                ),
                rx.vstack(
                    _label("Stages cleared"),
                    rx.hstack(
                        _stage_badge(1, ScoreboardState.flag_1_solved),
                        _stage_badge(2, ScoreboardState.flag_2_solved),
                        _stage_badge(3, ScoreboardState.flag_3_solved),
                        spacing="2",
                        wrap="wrap",
                    ),
                    spacing="1",
                    align="start",
                ),
                justify="between",
                align="end",
                wrap="wrap",
                gap="4",
                width="100%",
            ),
            spacing="4",
            align="stretch",
        )
    )
