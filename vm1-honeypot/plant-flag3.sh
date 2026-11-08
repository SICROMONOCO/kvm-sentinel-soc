#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/auth.log"
FLAG="${FLAG_PART3:-}"

if [[ -z "$FLAG" ]]; then
  echo "FLAG_PART3 is not set; skipping stage 3" >&2
  exit 0
fi

mkdir -p -- "$(dirname -- "$LOG_FILE")"
touch "$LOG_FILE"

if grep -Fq -- "flag_part3=$FLAG" "$LOG_FILE"; then
  echo "stage 3 flag already planted in $LOG_FILE"
  exit 0
fi

printf '%s vm-honeypot sshd[4242]: Accepted password for flag_part3=%s from 203.0.113.66 port 52222 ssh2\n' \
  "$(date -u '+%Y-%m-%dT%H:%M:%S.%6N+00:00')" "$FLAG" >> "$LOG_FILE"

echo "stage 3 flag planted in $LOG_FILE"
