# Aster parent-process supervision

`scripts/aster_supervisor.py` is an actual Linux parent process. It starts the existing `run.sh` in a new process group/session, retains the `Popen` child, checks the owned server and operational worker, records exits and restarts its own child with bounded exponential backoff. It adds no financial authority and does not change strategies, install/fund sleeves, edit SQLite, originate orders, or unpause trading.

## Start and inspect

The following inspection is read-only: it starts no child and creates no supervisor output files.

```sh
cd /workspace/agentic-desk
.venv/bin/python scripts/aster_supervisor.py --inspect
```

After coordinating the graceful stop of any earlier Aster server, start the supervisor in the foreground:

```sh
cd /workspace/agentic-desk
.venv/bin/python scripts/aster_supervisor.py
```

For the complete configured stack, `scripts/aster_launch.sh` sources the existing trusted Bash `.env` before the supervisor and services coordinator, derives the matching health port and receipt directory, and starts only already installed/registered independent companions. Use `scripts/aster_launch.sh --startup-grace 300` after the same coordinated earlier-server stop; it installs/funds nothing. A copied-wrapper synthetic test verified environment paths containing spaces and IPv6 health selection.

Do not run both the earlier `run.sh`/uvicorn server and this command. The supervisor refuses an occupied health port and never replaces or signals that earlier process. Parent coordination of the current server is separate from implementation/testing of this supervisor.

The default child is the existing absolute project `run.sh`, with the project as cwd, no shell interpolation, unchanged inherited environment and closed inherited file descriptors. `run.sh` itself loads the existing `.env`, honors `ASTER_HOST`, `ASTER_PORT` and `ASTER_DB_PATH`, checks the requirements/package-lock markers, builds the frontend, and execs uvicorn. The supervisor neither parses nor prints `.env` or other credentials. The launcher must have access to the same environment and project files as an ordinary `run.sh` invocation. Existing `run.sh` performs its existing dependency/build setup on every attempt; prepared dependencies shorten startup.

If the child's configured port is different, explicitly match the health URL, for example:

```sh
.venv/bin/python scripts/aster_supervisor.py --health-url http://127.0.0.1:8790/api/health
```

Health URLs are restricted to literal `127.0.0.1` or `::1`, plain HTTP, `/api/health`, with no credentials, query or fragment. Configure the child's actual host/port separately using the existing environment/`.env`; this option does not rewrite its configuration. Loopback probes ignore inherited outbound HTTP proxy variables and reject redirects.

An optional argv after `--` replaces the child command; this is primarily for isolated tests or an explicitly prepared deployment command. Its args are never printed. The exact argv is SHA-256 fingerprinted. A replacement command is responsible for its own environment-file handling; only the default `run.sh` automatically uses the established `.env` behavior.

## Liveness, leases and ownership

Every health request requires all matching listening sockets on the exact configured loopback address/family (including same-family wildcard listeners) to be held by processes in the newly started child's own Linux session/process group. The supervisor validates `/proc` birth ticks for known members, follows continuity of that group, and never treats a PID file alone as signaling authority. It does not query a foreign listener. Linux child-subreaper mode is confirmed before launching a child, so orphaned descendants remaining in the owned group are adopted and reaped.

The existing `/api/health` response's `autonomy.worker_alive` derives from the worker thread, current runtime lease and heartbeat. The supervisor requires a strict true boolean, an aware `heartbeat_at`, and finite, non-boolean `heartbeat_age_seconds`. It independently recomputes heartbeat age against current UTC, rejects more than two seconds into the future, and requires both observed ages at or below the configured limit. This checks operational liveness rather than strategy profitability or price freshness.

An operator's `running=false` is retained; the operational worker must still renew its heartbeat/lease. Slow research progress, retrying jobs, capacity-limited data and other `healthy=false` states are recorded as diagnostics, without restarting a worker whose lease and heartbeat remain fresh. A missing/unowned/unresponsive endpoint, stale heartbeat, or missing lease/thread causes a controlled own-child restart after the startup grace and consecutive-failure threshold. The HTTP client uses nonblocking I/O with one absolute monotonic deadline for connect, send, headers and body; a dribbling peer cannot renew that deadline, and stop requests interrupt polling within 100 ms. Normal JSON Content-Length or close-delimited responses are supported; redirects, duplicate/ambiguous headers and transfer/content encodings are rejected. No health bodies, raw exception messages, commands or environment values enter the supervisor event log.

Defaults are:

| Setting | Default | Effect |
|---|---:|---|
| Startup grace | 180 seconds | Initial unavailable health does not trigger premature restart |
| Poll interval | 1 second | Observe child exit and supervisor stop |
| Health interval | 30 seconds | Source and owned-worker health check |
| HTTP timeout | 10 seconds | Bound each loopback request |
| Heartbeat limit | 90 seconds | Stricter than the desk's 120-second lease |
| Failure limit | 3 | Consecutive failed checks after startup grace |
| Initial / maximum backoff | 1 / 60 seconds | Double between unsuccessful recoveries, cap at 60 |
| Stable period | 300 seconds | Continuously healthy worker resets consecutive restart count/backoff |
| Graceful / forced shutdown | 30 / 5 seconds | TERM first; KILL only surviving members of the same owned group |
| Maximum restarts | 0 | Unlimited recovery attempts, each with capped backoff; positive value bounds consecutive retries |

Each setting has a same-name CLI option, such as `--startup-grace 300`, `--backoff-max 120`, or `--max-restarts 10`. Startup grace must allow the actual project build. It is not permission to report a worker as healthy before a measured receipt. Health freshness and financial/provider quality remain separate checks.

SIGTERM, SIGINT and SIGHUP request supervisor termination, not reload. Shutdown sends TERM to its own group, waits a bounded grace, sends KILL only if live owned members survive, reaps the child/orphans, and records termination diagnostics. No health failure signals arbitrary other processes. The supervisor manages descendants that retain the child session/group; intentionally daemonized processes escaping it are outside this contract.

## Source pins and receipts

The supervisor hashes and modes the launch script, all Python and shell scripts (including a configured services coordinator and environment launch wrappers), available Dockerfile/compose/.dockerignore controls, requirements files, frontend package-lock, backend Python files and strategy assets at startup. It rechecks these pins at each health interval and before every child launch. A change or disappearing source stops its own child, records a blocked state and exits 78; it does not silently restart changed scientific/risk code. `--source-file` may explicitly select a smaller pinned set for isolated tests; production should use the complete default. The launcher Python executable, version and kernel are fingerprinted. Container control files are pinned when present in the application filesystem; the runtime pin is not an independently measured whole-image digest when build files are absent from a running image. Pinned lock files identify declared dependencies; this receipt does not claim a hash of every installed dependency or the child process's entire loaded memory image. The supervisor source SHA is separately rechecked even with a selected source list. `.env`, data, secrets, installed caches, frontend build output, and current financial books are excluded from source hashes.

Singleton `flock` uses `data/aster-supervisor/aster-supervisor.lock`. A losing contender starts nothing and writes no shared status/events. Closed child FDs ensure the child does not inherit and retain the singleton lock after a supervisor crash. Default receipts are:

- `data/aster-supervisor/aster-supervisor.jsonl`: UTC event records, exit status/signal, backoff, health summaries and owned shutdown.
- `data/aster-supervisor/aster-supervisor.status.json`: atomic latest state, source/runtime pins and explicit recovery scope.
- `data/aster-supervisor/aster-supervisor.child.log`: private child stdout/stderr. Raw child output may itself contain sensitive diagnostics, so keep it private and exclude it from public/shared exports without review.

Files are mode 0600. Events and child output rotate at the next write/start when exceeding 10 MB, retaining one previous file. Child output can grow during a long single attempt; the 10 MB setting is a restart-time rotation threshold, not a hard storage quota. The supervisor uses no raw error strings in structured receipts. `--output-dir` selects a dedicated data subdirectory or an external durable receipt volume. `--lock`, `--events`, `--status`, and `--child-log` may customize filenames only inside that dedicated directory. Outputs cannot target backend, strategy, dependency or other source directories. Symlink/hard-link aliases and special files are rejected, including an opened-file identity check before any append/truncate. Credential files and `.sqlite`/`.db` outputs are refused. Loss of event/status logging fails the run and still triggers guarded own-child cleanup.

Exit 0 means an intentional supervisor stop; 75 means singleton contention, exhausted consecutive restart budget, or a supervisory failure; 78 means configuration/source/occupied-port block. Actual reasons are in receipts where logging is available.

## Persistence in this managed environment

Capability inspection on 2026-10-09 observed PID 1 as `tail -f /dev/null`, `systemctl is-system-running` as `offline`, no `/run/systemd/system`, and no runit, s6, supervisord, cron or crond executable. There is no running init/service manager in which to enable an automatic host/container restart job. A systemctl binary alone does not establish an active systemd manager.

`scripts/aster_container_entrypoint.sh` is a prepared entrypoint that execs this supervisor. It was not installed as the current container's PID 1, and writing it activates no service. A managed container image/launch configuration can select it as ENTRYPOINT, mount durable source/data/receipt storage, and apply that deployment platform's supported restart policy. Actual deployment requires the container/host operator to configure that external orchestration. No restart policy or service has been enabled by this implementation.

A foreground or detached supervisor recovers its own child while the supervisor itself remains alive. SIGKILL of the supervisor, container deletion/reset, host failure, lost storage and deliberately escaped child sessions are not repaired by this script alone. Do not label a detached process as host-recovering supervision. The current implementation/testing leaves the existing server and current database untouched; the parent task separately coordinates any cutover and must publish an actual runtime receipt before claiming active supervision.

## Isolated validation

Run:

```sh
.venv/bin/python -m unittest tests.test_aster_supervisor -v
```

Tests use temporary projects, ephemeral loopback ports, private synthetic child scripts and no Aster/Alpaca/financial database. They exercise real subprocess crashes/signals, bounded restart backoff, fresh/stale/lease health, singleton contention, source changes, inherited synthetic credentials, foreign listener exclusion, operator pause, slow progress, forced shutdown, orphan adoption/reaping and injected diagnostic-write failure cleanup. Independent review receipts belong to the separate R15 operations archive.
