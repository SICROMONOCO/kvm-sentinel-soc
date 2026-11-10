import reflex as rx

config = rx.Config(
    app_name="ctf_scoreboard",
    # Reflex 0.10 treats any truthy frontend_port as an explicit CLI request,
    # which makes `reflex run --backend-only` exit. The production frontend is
    # exported statically and served by Caddy, so no frontend port is needed.
    frontend_port=0,
    backend_port=8000,
)
