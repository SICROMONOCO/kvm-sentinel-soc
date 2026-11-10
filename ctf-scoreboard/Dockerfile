# syntax=docker/dockerfile:1
#
# Single-container production image for the CTF scoreboard.
#
#   Stage 1 (builder) : install Python deps with uv, export the static Reflex
#                       frontend with bun, and keep .web/backend for runtime.
#   Stage 2 (runtime) : Python + Caddy only. Caddy serves the exported frontend
#                       on the one published port and proxies Reflex backend
#                       routes to 127.0.0.1:8000. SQLite lives in /data.
#
# Modeled on Reflex 0.10.0's official production Dockerfile, minus Redis and
# Alembic, which this application does not use.

ARG PORT=8080

# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# uv installs Python packages. Reflex uses the bun found on PATH instead of
# downloading its own copy during export.
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
COPY --from=oven/bun:1 /usr/local/bin/bun /usr/local/bin/bun

ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install requirements first so application edits do not invalidate the layer.
COPY requirements.txt .
RUN uv venv && uv pip install -r requirements.txt

# Copy the app module, rxconfig.py, Caddyfile and assets (see .dockerignore).
COPY . .

ARG PORT=8080
# Build the static frontend. The browser reaches the backend through Caddy on
# the same origin, so localhost:${PORT} is the correct public API URL at build
# time; Caddy proxies the backend paths on that port.
RUN --mount=type=cache,target=/root/.bun/install/cache \
    REFLEX_API_URL=http://localhost:${PORT} reflex export --frontend-only --no-zip

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

# ca-certificates is the only extra system package. No curl, no redis, and the
# healthcheck uses the Python standard library instead of curl.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Caddy binary only; the upstream image's entrypoint and defaults are unused.
COPY --from=caddy:2 /usr/bin/caddy /usr/bin/caddy

ARG PORT=8080
ENV PATH="/app/.venv/bin:$PATH" \
    PORT=${PORT} \
    PYTHONUNBUFFERED=1 \
    GRANIAN_WORKERS=1 \
    HOME=/app

WORKDIR /app

# Unprivileged runtime user. Reflex writes .states under /app and SQLite under
# /data, so both trees must be owned by reflex. PORT stays above 1024, which
# lets the unprivileged user bind it without CAP_NET_BIND_SERVICE.
RUN adduser --disabled-password --gecos "" --home /app reflex \
    && mkdir -p /data \
    && chown -R reflex:reflex /app /data

# Python environment and backend state first, then the app source.
COPY --chown=reflex:reflex --from=builder /app/.venv /app/.venv
COPY --chown=reflex:reflex --from=builder /app/.web/backend /app/.web/backend
# Caddy serves the exported static frontend from /srv. Read-only is sufficient.
COPY --from=builder /app/.web/build/client /srv
# The exported env module bakes in the build-time host/port. Caddy serves this
# same-origin replacement for the hashed asset so host-port mapping stays free.
COPY reflex-env.js /srv/reflex-env.js
COPY --chown=reflex:reflex . /app

USER reflex

EXPOSE 8080
STOPSIGNAL SIGTERM

# SQLite database volume: /data/scoreboard.db.
VOLUME ["/data"]

# Standard-library healthcheck; no curl in the runtime image.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=4)" || exit 1

# Caddy daemonizes and owns :8080; the Reflex backend stays in the foreground
# and receives SIGTERM as PID 1's exec target.
CMD ["sh", "-c", "caddy start --config /app/Caddyfile && exec reflex run --env prod --backend-only"]
