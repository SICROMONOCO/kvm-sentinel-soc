#!/usr/bin/env bash
#
# entrypoint.sh — start rsyslog, mirror auth.log to stdout, then sshd.
#
# rsyslogd is what turns sshd's syslog() calls into the traditional
# "Oct 30 10:11:12 <host> sshd[pid]: Failed password for root from ..." lines
# that promtail ships and the SOC parser understands. sshd alone (-E file)
# would give a different, harder-to-parse format.
set -Eeuo pipefail

LOG_FILE="/var/log/auth.log"
mkdir -p /run/sshd

# Host keys are generated on first start: baking them into the image would give
# every student the same fingerprint.
ssh-keygen -A >/dev/null

# Fake, intentionally weak root password (documented in the README).
echo 'root:toor' | chpasswd

if [ -n "${FLAG_PART1:-}" ]; then
  install -d -m 0700 /var/backups
  printf '%s\n' "$FLAG_PART1" > /var/backups/.flag1
  chmod 0600 /var/backups/.flag1
fi

if [ -n "${FLAG_PART2:-}" ]; then
  {
    echo "# The SOC records every username attempted against this host."
    echo "# Stage 2: make them record this exact username."
    echo "flag_part2=${FLAG_PART2}"
  } >> /root/.bash_history
  chmod 0600 /root/.bash_history
fi

# The bind mount may be empty on a fresh VM; rsyslog drops to syslog:adm, so
# the file must be writable by that account rather than only by root.
touch "$LOG_FILE"
chown syslog:adm "$LOG_FILE"
chmod 0644 "$LOG_FILE"

echo "[honeypot] starting rsyslog (auth -> ${LOG_FILE})"
rsyslogd

# Mirror the auth stream into the container log so that `docker compose logs -f`
# is enough to debug a demo without shelling into the VM.
tail -n0 -F "$LOG_FILE" &

echo "[honeypot] starting sshd on 0.0.0.0:2222 (LogLevel VERBOSE)"
# Do not pass -e here: it sends sshd logs straight to stderr and bypasses
# rsyslog, so /var/log/auth.log stays empty and the SOC pipeline sees nothing.
exec /usr/sbin/sshd -D -f /etc/ssh/sshd_config
