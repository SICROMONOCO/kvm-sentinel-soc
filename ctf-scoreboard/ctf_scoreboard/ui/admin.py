"""Operator-only reset page."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.admin_state import AdminState

from .base import (
    BG,
    BORDER,
    DANGER,
    INPUT_STYLE,
    MONO,
    MUTED,
    TEXT,
    WARNING,
    _label,
    _panel,
    message_box,
)
from .layout import _page_shell


def _admin_form() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            _label("Admin token"),
            rx.input(
                type="password",
                placeholder="ADMIN_TOKEN",
                auto_complete=False,
                on_change=AdminState.set_admin_token,
                style=INPUT_STYLE,
            ),
            rx.text(
                "The token is kept in backend-only state and is never rendered "
                "back to the browser.",
                color=MUTED,
                font_size="11px",
                line_height="1.55",
            ),
            spacing="2",
            align="stretch",
            width="100%",
        ),
        rx.vstack(
            _label("New session start (optional)"),
            rx.input(
                value=AdminState.admin_session_start,
                on_change=AdminState.set_admin_session_start,
                placeholder="2026-11-09T09:00:00Z",
                style=INPUT_STYLE,
            ),
            rx.text(
                "Leave blank to start the new session now. ISO-8601 UTC is safest.",
                color=MUTED,
                font_size="11px",
            ),
            spacing="2",
            align="stretch",
            width="100%",
        ),
        rx.checkbox(
            "I understand this clears all teams, solves, hints, and attempts.",
            checked=AdminState.admin_confirm,
            on_change=AdminState.set_admin_confirm,
            color_scheme="teal",
            font_size="12px",
            color=TEXT,
            align="start",
        ),
        rx.button(
            rx.hstack(
                rx.icon("triangle_alert", size=15),
                rx.text("RESET LEADERBOARD"),
                spacing="2",
                align="center",
            ),
            on_click=AdminState.reset_leaderboard,
            bg=DANGER,
            color=BG,
            border=f"1px solid {DANGER}",
            border_radius="10px",
            font_family=MONO,
            font_size="12px",
            font_weight="700",
            letter_spacing="0.08em",
            height="44px",
            width="100%",
            cursor="pointer",
            _hover={"bg": "#ff8da0"},
        ),
        message_box(AdminState.admin_message, AdminState.admin_message_kind),
        spacing="4",
        align="stretch",
        width="100%",
    )


def _admin_disabled() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon("lock", size=16, color=WARNING),
            rx.text(
                "Admin reset is disabled because ADMIN_TOKEN is empty. Set it in "
                "the deployment environment and recreate the container.",
                color=WARNING,
                font_family=MONO,
                font_size="12px",
                line_height="1.6",
            ),
            spacing="2",
            align="start",
        ),
        border=f"1px solid {BORDER}",
        border_radius="12px",
        bg="rgba(251,191,36,0.04)",
        padding="14px",
        width="100%",
    )


def admin_page() -> rx.Component:
    """Destructive session reset page."""

    return _page_shell(
        rx.vstack(
            rx.link(
                rx.hstack(
                    rx.icon("arrow-left", size=13, color=MUTED),
                    rx.text(
                        "BACK TO SCOREBOARD",
                        color=MUTED,
                        font_family=MONO,
                        font_size="10px",
                        letter_spacing="0.1em",
                    ),
                    spacing="2",
                    align="center",
                ),
                href="/",
                text_decoration="none",
                _hover={"opacity": "0.8"},
            ),
            _panel(
                rx.vstack(
                    _label("Admin console"),
                    rx.heading(
                        "Reset the session",
                        size="6",
                        font_family=MONO,
                        letter_spacing="-0.04em",
                        color=TEXT,
                        margin="0",
                    ),
                    rx.text(
                        "This is destructive. It clears every team, solve, revealed "
                        "hint, and rate-limit attempt, then starts a fresh clock.",
                        color=DANGER,
                        font_size="13px",
                        line_height="1.65",
                    ),
                    rx.cond(
                        AdminState.admin_enabled,
                        _admin_form(),
                        _admin_disabled(),
                    ),
                    spacing="4",
                    align="stretch",
                ),
                padding="24px",
                max_width="760px",
            ),
            spacing="5",
            align="stretch",
            width="100%",
        ),
        AdminState,
    )
