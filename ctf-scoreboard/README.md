# CTF Scoreboard

A standalone, single-container scoreboard for the KVM-Sentinel-SOC capture-the-flag
chain. It runs on the **host**, outside the VM1 (honeypot) and VM2 (SOC) lab
structure, and is reached by students over the host's LAN address.

The scoreboard is deliberately independent of the lab stacks: it has its own
Docker Compose project, its own bridge network, and one published host port.

## Contents

- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Scoring and ranking](#scoring-and-ranking)
- [Hints](#hints)
- [Admin reset](#admin-reset)
- [Security model](#security-model)
- [Isolation](#isolation)
- [TLS](#tls)
- [Persistence and backups](#persistence-and-backups)
- [Troubleshooting](#troubleshooting)
- [Validation](#validation)
- [Instructor notes](#instructor-notes)

## Architecture

One container, one published port, two internal listeners:

```text
 Student browser
       │  HTTP  http://<HOST_LAN_IP>:8080
       ▼
 Host  0.0.0.0:${SCOREBOARD_PORT:-8080}
       │  docker-proxy port mapping
       ▼
 ┌───────────────────────── container: ctf-scoreboard ─────────────────────────┐
 │                                                                             │
 │  Caddy  :8080                                                               │
 │    ├── /healthz                                   -> Reflex readiness       │
 │    ├── /_event, /_event/*, /ping, /_health,      -> 127.0.0.1:8000         │
 │    │   /_upload, /_upload/*                          Reflex backend         │
 │    └── everything else                            -> /srv                   │
 │                                                       exported Reflex       │
 │                                                       static frontend       │
 │                                                                             │
 │  Reflex backend  127.0.0.1:8000  (never published directly)                 │
 │       │                                                                     │
 │       ▼                                                                     │
 │  SQLite  /data/scoreboard.db                                                │
 │       │                                                                     │
 │       ▼                                                                     │
 │  Docker named volume  scoreboard-data                                       │
 └─────────────────────────────────────────────────────────────────────────────┘
```

Caddy serves the exported frontend and proxies Reflex backend routes on the same
origin, so the browser only ever talks to one port. The Reflex backend listens
on loopback inside the container and is not reachable from the host.

Build details:

- Base images: `python:3.13-slim` for build and runtime, `oven/bun:1` for the
  frontend export, `ghcr.io/astral-sh/uv:0.12` for Python packages, `caddy:2` for
  the reverse proxy binary.
- `requirements.txt` pins `reflex==0.10.0`.
- The app module is `ctf_scoreboard.ctf_scoreboard`, configured by
  `rxconfig.py` (`backend_port=8000`; `frontend_port=0` is intentional because
  production serves the exported frontend through Caddy and runs Reflex
  backend-only).
- The runtime image is non-root (`reflex` user), drops all Linux capabilities,
  and contains no curl or Redis.

## Quick start

```bash
cd ctf-scoreboard

# 1. Create the local environment file.
cp .env.example .env

# 2. Fill in the three flags, a long ADMIN_TOKEN, and optionally SESSION_START.
#    See .env.example for the exact format. Never commit .env.
$EDITOR .env

# 3. Build and start. The first build exports the Reflex frontend.
docker compose up -d --build

# 4. Verify the health endpoint.
curl http://127.0.0.1:8080/healthz
```

Open the scoreboard from a student machine:

```text
http://<HOST_LAN_IP>:8080
```

If the host firewall is enabled, allow inbound TCP `8080` (or whatever you set
`SCOREBOARD_PORT` to) on the LAN interface only. Do not expose this port to the
public internet.

To change the host port without touching Compose:

```bash
SCOREBOARD_PORT=9090 docker compose up -d
```

## Scoring and ranking

| Stage | Points |
|-------|--------|
| 1     | 100    |
| 2     | 150    |
| 3     | 200    |

- Each hint reveal costs **25 points** against the team's total.
- Ranking order:
  1. number of flags found (descending);
  2. elapsed time from session start to the team's latest solve (ascending);
  3. total score (descending).
- The board shows a **first blood** marker for the first team to solve each stage.
- Elapsed time is measured from `SESSION_START` when set, otherwise from the
  session start recorded when the database was first initialized. Use the admin
  reset page to start a fresh clock between classes.

## Hints

The three in-app riddles are fixed:

1. "Behind the door that welcomes every knock, a whisper sleeps where backups
   rot."
2. "A borrowed shell remembers a name the watchers cannot ignore; speak it back
   through the trap and read their incident ledger."
3. "A ghost signed in from 203.0.113.66 and left no trace but one line; ask the
   river of logs for the password that never was."

Each reveal is deducted from that team's score. Rotate or remove hints only by
editing the application; this deployment layer does not manage hint text.

## Admin reset

The reset page is available at:

```text
http://<HOST_LAN_IP>:8080/admin
```

Use the value of `ADMIN_TOKEN` to authenticate. If `ADMIN_TOKEN` is empty, the
admin page is disabled.

A reset is **destructive**. It clears stored attempts and solves for the
session so a class can start fresh. Optionally set an explicit ISO-8601 start
time for the new session:

```bash
# .env
SESSION_START=2026-11-09T09:00:00Z
```

Back up the database before resetting if the previous session must be kept. See
[Persistence and backups](#persistence-and-backups).

## Security model

- **Flags stay in the backend.** `FLAG_PART1`–`FLAG_PART3` are injected as
  container environment variables and read by Python code only. They are never
  placed in Reflex state, page props, or the browser bundle.
- **Constant-time comparison.** Submitted values are checked with
  `hmac.compare_digest`, so a wrong flag does not leak timing information.
- **No expected flags in Reflex state.** The client cannot inspect or recover a
  flag by reading page source or state deltas.
- **Rate limiting.** Submissions are limited to 5 attempts per minute per source
  IP and per username.
- **Input limits.** Usernames are capped at 32 characters and submitted flag
  values at 128 characters.
- **Response headers.** Caddy sends `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, a restrictive
  `Permissions-Policy`, `Cross-Origin-Opener-Policy: same-origin`, and a
  Content-Security-Policy that allows Reflex while denying framing.
- **Non-root container.** The runtime process runs as the unprivileged `reflex`
  user with all capabilities dropped and `no-new-privileges` set.
- **No secrets in the image.** `.env` is excluded by `.dockerignore`; the
  database is a runtime volume, not a build input.

## Isolation

The Compose project is named `ctf-scoreboard` and uses exactly one network,
`scoreboard-net`, a private bridge created for this project.

- It is **not** attached to `virbr0`, `virbr1`, `honeypot-net`, or `soc-net`.
- It declares **no external networks**.
- It does **not** use `network_mode: host`.
- Exactly one host port is published:
  `0.0.0.0:${SCOREBOARD_PORT:-8080}:8080`.

The host port is intentional LAN exposure so students can reach the scoreboard.
The container itself has no route into the lab's internal Docker networks.

## TLS

Plain HTTP is intentional for the lab: the scoreboard carries no credentials
and the lab is isolated. If the scoreboard must cross an untrusted network,
terminate TLS at a reverse proxy (for example Caddy, nginx, or the institution's
ingress) and forward plain HTTP to `127.0.0.1:8080` on the host.

When TLS is added, keep the same origin for the frontend and backend paths, or
adjust `connect-src` in `Caddyfile` accordingly.

## Persistence and backups

SQLite lives at `/data/scoreboard.db` inside the container, backed by the named
Compose volume `scoreboard-data`. Docker prefixes it with the project name, so
the real volume is `ctf-scoreboard_scoreboard-data`.

A consistent backup is easiest while the container is stopped:

```bash
cd ctf-scoreboard
docker compose stop
docker run --rm \
  -v ctf-scoreboard_scoreboard-data:/data:ro \
  -v "$PWD":/backup \
  alpine tar czf /backup/scoreboard-backup.tgz -C /data .
docker compose start
```

Restore by stopping the stack, extracting the archive into a fresh volume, and
starting again. Do not copy a live database without its `-wal` and `-shm` files.

To intentionally wipe the scoreboard:

```bash
cd ctf-scoreboard
docker compose down -v   # deletes the scoreboard-data volume
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Flags never accepted | Verify `.env` values match the configured fragments; recreate container. |
| `/admin` disabled | Set a non-empty `ADMIN_TOKEN` in `.env`; recreate the container. |
| Port already in use | `ss -ltnp \| grep :8080`; set `SCOREBOARD_PORT` to a free host port. |
| Container unhealthy | Check `docker compose ps`, `docker inspect`, and `docker compose logs`. |
| Health endpoint fails | `curl -v http://127.0.0.1:8080/healthz`; check Caddy and backend logs. |
| Reset scores | Back up first, then use `/admin`, or `docker compose down -v`. |
| Browser shows CSP errors | Keep the CSP in `Caddyfile`; rebuild after changing it. |

Useful diagnostics:

```bash
cd ctf-scoreboard
docker compose ps
docker compose logs -f scoreboard
docker inspect --format '{{json .State.Health}}' ctf-scoreboard
```

## Validation

Run these from `ctf-scoreboard/`:

```bash
python3 -m py_compile rxconfig.py
docker compose config -q
docker compose up -d --build
curl http://127.0.0.1:8080/healthz
```

Expected results:

- `py_compile` exits 0 and creates `__pycache__/` (safe to delete).
- `docker compose config -q` exits 0 using only defaults, with no `.env` needed.
- `docker compose up -d --build` builds the image and starts one container.
- The `curl` prints `ok` and exits 0.

## Instructor notes

- **Rotating flags.** Edit the three values in `.env`, then recreate the
  container so the backend receives the new environment:

  ```bash
  docker compose up -d --force-recreate
  ```

- **Old evidence retains old values.** Lab reports and log retention may still
  contain previously planted fragments. For a clean rotation, start from a
  fresh lab snapshot or clear the retained evidence.
- **Scores survive restarts.** The SQLite volume is not removed by
  `docker compose down`; only `docker compose down -v` deletes it.
- **Reset between classes.** Use `/admin` with the current `ADMIN_TOKEN`, and set
  `SESSION_START` if the new session should begin at a known time.
- **Never commit `.env`.** It is gitignored and excluded from the image. Treat
  `ADMIN_TOKEN` like a password and the three flag values like exam answers.
