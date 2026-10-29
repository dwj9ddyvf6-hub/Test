# Running and recovering Aster

`./run.sh` runs the desk until its process stops. Docker Compose supplies restart/health behavior:

```bash
docker compose up --build -d
docker compose logs -f desk
```

The named volume holds SQLite state. The systemd example expects installation at `/opt/aster-desk`; adapt that path and install it on the chosen host. Neither service nor an off-host monitor was installed remotely during the build. Run `scripts/monitor.py --url URL` from a separate host/scheduler to detect heartbeat or host loss.

## Backups and restoration

```bash
python scripts/backup.py --database data/aster.sqlite --destination backups
```

The consistent SQLite backup includes ledger, observations, jobs, inbox and studies. Each timestamped copy has a hash/integrity receipt. Older backups and source state remain. Run backups under the chosen host's scheduler and copy them to independent storage; this local script does not configure remote storage.

Restoration hashes the exact bytes copied to its private temporary file before checking integrity and publishing the new database. It does not replay sidecar files adjacent to the backup: those bytes are outside the receipt. Keep backups immutable after creation.

Restore only into a **new** path:

```bash
python scripts/restore.py --backup backups/aster-TIMESTAMP.sqlite --destination recovered/aster.sqlite
```

The command requires the matching JSON receipt and refuses existing database/sidecar paths. It never overwrites an active desk. Stop the desk before choosing the restored file through `ASTER_DB_PATH`, restart, inspect journal integrity and reconciliation, and let paper broker truth resolve outstanding instructions before supplying new ones. Local database recovery cannot undo an externally accepted paper-broker order; durable client IDs and reconciliation handle that boundary. The restored file retains original instructions and settings, so do not start it alongside the original book against the same broker account.

## Managed cloud Docker builds

The read-only monitor and container healthcheck inspect `/api/health`. A fresh heartbeat alone does not pass: a stalled worker, journal/database error, active-job stall or degraded autonomous runtime causes a failure. Docker records an unhealthy state; `restart: unless-stopped` restarts an exited process, and does not restart a still-running unhealthy container. Inspect the reported reason before taking recovery action.

Ordinary hosts use their standard certificate trust. In the managed cloud workspace, build network steps use the supplied proxy CA through optional BuildKit mounts; no session certificate is saved in image layers:

```bash
docker build --secret id=proxy_ca,src="$CODEX_PROXY_CERT" --secret id=ca_bundle,src=/etc/ssl/certs/ca-certificates.crt -t aster-desk:local .
```

A running container collecting HTTPS data in that workspace also needs the managed CA mounted read-only and its client trust configured. Manual-feed container checks need no external data connection. TLS verification stays enabled.
