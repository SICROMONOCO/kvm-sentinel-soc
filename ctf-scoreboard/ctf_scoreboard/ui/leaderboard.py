"""Public leaderboard table and panel."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.state import ScoreboardState

from .base import (
    ACCENT,
    ACCENT_2,
    BORDER,
    MONO,
    MUTED,
    PANEL_2,
    TEXT,
    WARNING,
    _badge,
    _label,
    _panel,
)


def _leaderboard_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell(_label("#"), width="48px"),
                rx.table.column_header_cell(_label("Team")),
                rx.table.column_header_cell(_label("Flags"), width="80px"),
                rx.table.column_header_cell(_label("Score"), width="90px"),
                rx.table.column_header_cell(_label("Elapsed"), width="100px"),
                rx.table.column_header_cell(_label("Last solve"), width="110px"),
                rx.table.column_header_cell(_label("First blood"), width="130px"),
                bg="rgba(255,255,255,0.02)",
            )
        ),
        rx.table.body(
            rx.foreach(
                ScoreboardState.leaderboard,
                lambda row: rx.table.row(
                    rx.table.cell(
                        rx.text(
                            row["rank"],
                            font_family=MONO,
                            font_size="12px",
                            color=MUTED,
                        ),
                        padding_y="12px",
                    ),
                    rx.table.cell(
                        rx.text(
                            row["username"],
                            font_family=MONO,
                            font_size="13px",
                            font_weight="600",
                            color=TEXT,
                        ),
                        padding_y="12px",
                    ),
                    rx.table.cell(
                        rx.badge(
                            row["flags_found"] + "/3",
                            color=ACCENT_2,
                            bg="rgba(103,232,249,0.06)",
                            border=f"1px solid {BORDER}",
                            font_family=MONO,
                            font_size="10px",
                        ),
                        padding_y="12px",
                    ),
                    rx.table.cell(
                        rx.text(
                            row["score"] + " pts",
                            font_family=MONO,
                            font_size="12px",
                            color=ACCENT,
                        ),
                        padding_y="12px",
                    ),
                    rx.table.cell(
                        rx.text(
                            row["elapsed"],
                            font_family=MONO,
                            font_size="12px",
                            color=MUTED,
                        ),
                        padding_y="12px",
                    ),
                    rx.table.cell(
                        rx.text(
                            row["last_solve"],
                            font_family=MONO,
                            font_size="11px",
                            color=MUTED,
                        ),
                        padding_y="12px",
                    ),
                    rx.table.cell(
                        rx.cond(
                            row["first_bloods"] != "0",
                            _badge(
                                "FIRST BLOOD x" + row["first_bloods"],
                                WARNING,
                                "rgba(251,191,36,0.06)",
                            ),
                            rx.text("-", color="#4d636b", font_family=MONO),
                        ),
                        padding_y="12px",
                    ),
                    _hover={"bg": PANEL_2},
                    border_bottom=f"1px solid {BORDER}",
                ),
            )
        ),
        width="100%",
        variant="surface",
    )


def _empty_board() -> rx.Component:
    return rx.vstack(
        rx.icon("target", size=28, color="#35515b"),
        rx.text(
            "No solves yet. The board is waiting for first blood.",
            color=MUTED,
            font_family=MONO,
            font_size="12px",
            text_align="center",
        ),
        spacing="3",
        align="center",
        justify="center",
        width="100%",
        padding_y="42px",
    )


def _leaderboard_panel() -> rx.Component:
    return _panel(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    _label("Live standings"),
                    rx.heading(
                        "Leaderboard",
                        size="5",
                        font_family=MONO,
                        letter_spacing="-0.04em",
                        color=TEXT,
                        margin="0",
                    ),
                    rx.text(
                        "Ranked by flags found, elapsed time, then score.",
                        color=MUTED,
                        font_size="12px",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.hstack(
                    rx.icon("refresh-cw", size=13, color=ACCENT),
                    rx.text(
                        "5s refresh",
                        color=MUTED,
                        font_family=MONO,
                        font_size="10px",
                    ),
                    spacing="2",
                    align="center",
                ),
                justify="between",
                align="end",
                wrap="wrap",
                gap="3",
                width="100%",
            ),
            rx.box(
                rx.cond(
                    ScoreboardState.team_count > 0,
                    _leaderboard_table(),
                    _empty_board(),
                ),
                width="100%",
                overflow_x="auto",
            ),
            spacing="4",
            align="stretch",
        )
    )
