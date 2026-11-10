"""Page chrome shared by the public and admin pages."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.state import ScoreboardState

from .base import (
    ACCENT,
    BG,
    BODY,
    BORDER,
    MONO,
    MUTED,
    PANEL,
    TEXT,
    _badge,
    _label,
    _panel,
)


def _header() -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.hstack(
                rx.icon("radio", size=14, color=ACCENT),
                _label("KVM-Sentinel // SOC range"),
                spacing="2",
                align="center",
            ),
            rx.heading(
                "CAPTURE THE FLAG",
                size="8",
                font_family=MONO,
                letter_spacing="-0.055em",
                color=TEXT,
                margin="0",
                line_height="1",
            ),
            spacing="2",
            align="start",
        ),
        rx.hstack(
            _badge("LIVE", ACCENT, "rgba(53,242,193,0.07)"),
            rx.link(
                rx.hstack(
                    rx.icon("shield-check", size=13, color=MUTED),
                    rx.text(
                        "ADMIN",
                        font_family=MONO,
                        font_size="10px",
                        letter_spacing="0.12em",
                        color=MUTED,
                    ),
                    spacing="2",
                    align="center",
                ),
                href="/admin",
                text_decoration="none",
                _hover={"opacity": "0.8"},
            ),
            spacing="4",
            align="center",
        ),
        justify="between",
        align="center",
        wrap="wrap",
        gap="4",
        width="100%",
        padding_bottom="2px",
    )


def _hero() -> rx.Component:
    return _panel(
        rx.flex(
            rx.vstack(
                _label("Range status"),
                rx.heading(
                    "Three fragments. One intrusion. Prove the chain.",
                    size="5",
                    font_family=MONO,
                    letter_spacing="-0.04em",
                    color=TEXT,
                    margin="0",
                    line_height="1.15",
                ),
                rx.text(
                    "Recover each fragment from the honeypot and the SOC, then "
                    "submit it here. Validation stays on the server; the browser "
                    "never receives an expected value.",
                    color=MUTED,
                    font_size="13px",
                    line_height="1.65",
                    max_width="700px",
                ),
                spacing="2",
                align="start",
            ),
            rx.vstack(
                _label("Session start"),
                rx.text(
                    ScoreboardState.session_start_display,
                    font_family=MONO,
                    font_size="12px",
                    color=TEXT,
                ),
                _label("Last sync"),
                rx.text(
                    ScoreboardState.updated_display,
                    font_family=MONO,
                    font_size="12px",
                    color=ACCENT,
                ),
                spacing="1",
                align="start",
                min_width="180px",
            ),
            justify="between",
            align="start",
            wrap="wrap",
            gap="6",
            width="100%",
        ),
        padding="24px",
        background=f"linear-gradient(135deg, rgba(53,242,193,0.045), transparent 46%), {PANEL}",
    )


def _footer(state: type[ScoreboardState]) -> rx.Component:
    return rx.flex(
        rx.text(
            "Fragments are validated server-side. Expected values never reach the browser.",
            color=MUTED,
            font_family=MONO,
            font_size="10px",
            line_height="1.6",
        ),
        rx.hstack(
            rx.text("SESSION", color="#5f7881", font_family=MONO, font_size="9px"),
            rx.text(
                state.session_start_display,
                color=MUTED,
                font_family=MONO,
                font_size="10px",
            ),
            rx.text("|", color=BORDER, font_family=MONO, font_size="10px"),
            rx.text("SYNC", color="#5f7881", font_family=MONO, font_size="9px"),
            rx.text(
                state.updated_display,
                color=MUTED,
                font_family=MONO,
                font_size="10px",
            ),
            spacing="2",
            align="center",
            wrap="wrap",
        ),
        justify="between",
        align="center",
        wrap="wrap",
        gap="3",
        width="100%",
        border_top=f"1px solid {BORDER}",
        padding_top="16px",
    )


def _page_shell(
    content: rx.Component, state: type[ScoreboardState]
) -> rx.Component:
    return rx.box(
        rx.box(
            position="fixed",
            top="0",
            left="0",
            width="100%",
            height="100%",
            z_index="-1",
            background_image=(
                "linear-gradient(rgba(53,242,193,0.035) 1px, transparent 1px), "
                "linear-gradient(90deg, rgba(53,242,193,0.035) 1px, transparent 1px)"
            ),
            background_size="48px 48px",
            mask_image="radial-gradient(circle at 50% 0%, black, transparent 72%)",
            pointer_events="none",
        ),
        rx.box(
            rx.vstack(
                _header(),
                content,
                _footer(state),
                width="100%",
                max_width="1240px",
                margin="0 auto",
                padding_x=["18px", "28px", "40px"],
                padding_y=["22px", "32px", "40px"],
                spacing="6",
                align="stretch",
            ),
            position="relative",
            z_index="1",
        ),
        min_height="100vh",
        width="100%",
        bg=BG,
        color=TEXT,
        font_family=BODY,
    )
