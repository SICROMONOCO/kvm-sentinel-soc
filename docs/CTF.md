# KVM-Sentinel-SOC CTF Challenge

This is an optional, instructor-run flag chain for the lab. The normal lab is
unchanged when all `FLAG_PART*` variables are empty.

The chain forces students to use both sides of the SOC:

1. the honeypot shell, where the attacker starts;
2. the SOC records, where the defender sees the attacker's usernames.

## Prerequisites

- The lab is deployed and the honeypot stack is running.
- You can SSH to `soc@10.10.0.10` with the lab key.
- You can reach Grafana at `http://192.168.122.20:3000` (`admin` / `sentinel`).

## Configure the flags

Choose three different values and place them in the compose environment on
vm-honeypot. Docker Compose reads `/opt/honeypot/.env` automatically.

```bash
ssh soc@10.10.0.10
cd /opt/honeypot
sudo tee .env >/dev/null <<'EOF'
FLAG_PART1=flag{stage1-change-me}
FLAG_PART2=flag{stage2-change-me}
FLAG_PART3=flag{stage3-change-me}
EOF
```

Plant the stage 3 line before recreating the honeypot:

```bash
sudo FLAG_PART3='flag{stage3-change-me}' ./plant-flag3.sh
sudo docker compose up -d --force-recreate ssh-honeypot
```

Verify that the container received the first two values:

```bash
sudo docker inspect ssh-honeypot \
  --format '{{range .Config.Env}}{{println .}}{{end}}' | grep FLAG_PART
```

## Stage 1 — the honeypot filesystem

Connect to the trap with the documented weak credential:

```bash
ssh -p 2222 root@10.10.0.10
# password: toor
```

Read the hidden file:

```bash
cat /var/backups/.flag1
```

## Stage 2 — the SOC is watching usernames

The root shell contains a short hint in its history:

```bash
cat /root/.bash_history
```

It reveals the stage 2 value as `flag_part2=<value>`. Prove that the SOC can
record the username by attempting it from the isolated network:

```bash
cd /opt/honeypot
sudo docker compose run --rm simulator \
  --users 'flag_part2=<value>' \
  --attempts-per-round 5 --rounds 1 --delay 1 --no-success
```

Use the simulator rather than the OpenSSH client: OpenSSH rejects `{` and `}`
in `ssh -l`, while the lab simulator sends the username through Paramiko.

Five failed authentications from one IP inside the 30-second window create an
incident. The report's targeted-accounts field contains
`flag_part2=<value>`. See `/opt/soc/reports/` on vm-soc, or the Grafana
dashboard.

The detector has a 120-second cooldown per source IP. If the first burst
already fired, wait for the cooldown before repeating the test. Avoid sending
more than five failures per 30 seconds for other stages if you do not want the
SOC to raise an incident.

## Stage 3 — the SOC's own record

The stage 3 line is a fabricated successful login written directly into the
honeypot audit log. It is intentionally not part of an alert.

Query Loki or Grafana Explore for it:

```text
{job="ssh-honeypot"} |= "flag_part3"
```

Or query Loki from vm-soc:

```bash
ssh soc@192.168.122.20 \
  "curl -sG http://127.0.0.1:3100/loki/api/v1/query_range \
   --data-urlencode 'query={job=\"ssh-honeypot\"} |= \"flag_part3\"' \
   --data-urlencode 'limit=20'"
```

The value in the `Accepted password for flag_part3=...` line is the final flag.

## Reset and rotation

Change the three values in `/opt/honeypot/.env`, recreate the honeypot, and
rerun `plant-flag3.sh`. Existing log lines keep the old values, so use a fresh
lab snapshot or remove the old stage 3 line when rotating flags for a live
class.
