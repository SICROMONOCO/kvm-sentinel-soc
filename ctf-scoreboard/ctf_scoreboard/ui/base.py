"""Shared theme primitives for the scoreboard UI."""

from __future__ import annotations

import reflex as rx


BG = "#070b0e"


PANEL = "#0c1419"


PANEL_2 = "#101b21"


BORDER = "#1c2b33"


TEXT = "#e6f4f1"


MUTED = "#8aa4ad"


ACCENT = "#35f2c1"


ACCENT_2 = "#67e8f9"


WARNING = "#fbbf24"


DANGER = "#fb7185"


MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


BODY = "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"


INPUT_STYLE = {
    "bg": PANEL_2,
    "border": f"1px solid {BORDER}",
    "border_radius": "10px",
    "color": TEXT,
    "font_family": MONO,
    "font_size": "13px",
    "height": "44px",
    "width": "100%",
    "_placeholder": {"color": "#5f7881"},
    "_focus": {
        "border_color": ACCENT,
        "box_shadow": f"0 0 0 1px {ACCENT}",
        "outline": "none",
    },
}


BUTTON_STYLE = {
    "bg": ACCENT,
    "color": BG,
    "border": f"1px solid {ACCENT}",
    "border_radius": "10px",
    "font_family": MONO,
    "font_size": "12px",
    "font_weight": "700",
    "letter_spacing": "0.08em",
    "height": "44px",
    "width": "100%",
    "cursor": "pointer",
    "_hover": {"bg": "#63f7d2", "border_color": "#63f7d2"},
    "_active": {"bg": "#21d6a8"},
}


GHOST_BUTTON_STYLE = {
    "bg": "transparent",
    "color": ACCENT,
    "border": f"1px solid {BORDER}",
    "border_radius": "9px",
    "font_family": MONO,
    "font_size": "11px",
    "font_weight": "700",
    "letter_spacing": "0.08em",
    "height": "34px",
    "cursor": "pointer",
    "_hover": {"border_color": ACCENT, "bg": "rgba(53,242,193,0.06)"},
}


def _label(text: str) -> rx.Component:
    """Small uppercase monospace label used across panels."""

    return rx.text(
        text,
        font_family=MONO,
        font_size="10px",
        font_weight="600",
        letter_spacing="0.16em",
        text_transform="uppercase",
        color=MUTED,
    )


def _panel(*children: rx.Component, **props) -> rx.Component:
    """Shared dark panel surface."""

    style = {
        "background": PANEL,
        "border": f"1px solid {BORDER}",
        "border_radius": "16px",
        "padding": "22px",
        "box_shadow": "0 18px 60px rgba(0,0,0,0.28)",
        "width": "100%",
    }
    style.update(props)
    return rx.box(*children, style=style)


def _badge(text: str, color: str, bg: str | None = None) -> rx.Component:
    return rx.badge(
        text,
        color=color,
        bg=bg or "rgba(255,255,255,0.04)",
        border=f"1px solid {BORDER}",
        font_family=MONO,
        font_size="10px",
        letter_spacing="0.08em",
        padding="4px 8px",
    )


def _kind_color(kind: str | rx.Var[str]) -> rx.Var[str]:
    return rx.cond(
        kind == "success",
        ACCENT,
        rx.cond(
            kind == "error",
            DANGER,
            rx.cond(kind == "warning", WARNING, ACCENT_2),
        ),
    )


def _stage_badge(stage: int, solved: bool | rx.Var[bool]) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(f"0{stage}", font_family=MONO, font_size="10px"),
            rx.icon(
                rx.cond(solved, "check", "minus"),
                size=12,
                color=rx.cond(solved, ACCENT, MUTED),
            ),
            spacing="1",
            align="center",
        ),
        border=rx.cond(solved, f"1px solid {ACCENT}", f"1px solid {BORDER}"),
        bg=rx.cond(solved, "rgba(53,242,193,0.08)", "transparent"),
        color=rx.cond(solved, ACCENT, MUTED),
        border_radius="8px",
        padding="5px 8px",
    )


def _stat_card(label: str, value: rx.Var | str | int, sub: str, icon: str) -> rx.Component:
    return _panel(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=14, color=ACCENT),
                _label(label),
                spacing="2",
                align="center",
            ),
            rx.text(
                value,
                font_family=MONO,
                font_size="28px",
                font_weight="700",
                letter_spacing="-0.04em",
                color=TEXT,
                line_height="1.05",
            ),
            rx.text(sub, color=MUTED, font_size="11px"),
            spacing="2",
            align="start",
        ),
        padding="16px",
    )


def message_box(
    message: str | rx.Var[str], kind: str | rx.Var[str]
) -> rx.Component:
    """Render one dismiss-free status message with a semantic colour."""

    return rx.cond(
        message != "",
        rx.box(
            rx.text(
                message,
                color=_kind_color(kind),
                font_family=MONO,
                font_size="12px",
                line_height="1.55",
            ),
            border=f"1px solid {BORDER}",
            border_radius="10px",
            bg="rgba(255,255,255,0.025)",
            padding="10px 12px",
            width="100%",
        ),
        rx.fragment(),
    )
