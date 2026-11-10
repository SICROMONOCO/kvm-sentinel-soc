"""Reflex application entrypoint for the standalone CTF scoreboard."""

from __future__ import annotations

import reflex as rx

from ctf_scoreboard.admin_state import AdminState
from ctf_scoreboard.state import ScoreboardState
from ctf_scoreboard.ui import admin_page, index_page

app = rx.App(
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        radius="large",
        accent_color="teal",
    ),
)

app.add_page(
    index_page,
    route="/",
    title="KVM Sentinel CTF | Live Scoreboard",
    description="Live standings for the KVM Sentinel capture-the-flag range.",
    on_load=ScoreboardState.load,
)

app.add_page(
    admin_page,
    route="/admin",
    title="KVM Sentinel CTF | Admin",
    description="Operator-only scoreboard reset console.",
    on_load=AdminState.load,
)
