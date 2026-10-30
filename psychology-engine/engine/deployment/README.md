# Inactive deployment templates

Nothing in this directory is installed, enabled or activated. No service account, credential, subscription, cloud resource or paid endpoint was created.

The package runs directly from its source directory with Python 3.10+ and no runtime dependencies. For a reviewed deployment, provision a dedicated least-privilege local account, copy only reviewed source files, create a virtual environment, and install this local package without fetching runtime dependencies. Resolve filesystem permissions and trusted Python/setuptools provenance through the deployment process. The service templates expect `/opt/psychology-engine/venv/bin/python`; this path is an installation placeholder, not an existing environment claim.

Keep the persistent SQLite file and its WAL/SHM files in `/var/lib/psychology-research` on a local persistent volume. Do not use network filesystems for this single-writer reference deployment. The service templates serialize collectors with `flock`; lock contention is visible as a failed job rather than a second writer. Every new process resumes the same immutable observation/revision store. First-seen dates do not reset on restart. Never point these templates at live-desk databases.

Copy and review the source-config template outside the public repository before use. All `persistent_use_authorized` flags remain false by default. Set one true only after documenting scope, retention, attribution and entitlement for that source; the flag is an operator attestation, not a legal rights checker. Retention and license expiry must be supervised externally; the engine does not automatically decide ownership or delete evidence. A scheduled one-shot command includes `--scheduled`, so it cannot silently evade the persistent-use gate by asking for only one cycle. Keep operator contacts, credentials and local source contracts out of public Test.

The `.timer.example` files are conservative polling opportunities, not publisher release guarantees:

| Source | Suggested opportunity | Why |
|---|---|---|
| Fed policy RSS | Hourly | Event-driven official announcements; no claim of tick latency |
| VIX historical file | Daily 23:30 UTC | End-of-day history; rights and exact canonical endpoint require review |
| FRBSF news tone | Daily 15:00 UTC | Detect weekly updates without pretending daily rows were published daily |
| Wikimedia | Daily 06:00 UTC | Previous completed UTC day; late loading remains missing, never zero |

Intervals and UTC windows require operator review for actual service requirements. No timer has an Install section. Installing/starting timers or adding such a section is a distinct deployment action, not performed here. `Persistent=false` avoids a burst of missed timer firings after a downtime interval. The collector does not infer missing observations from a missed job.

Preserve the configured proxy and CA trust when deploying in a managed environment. Do not unset proxy variables, route through another host, follow redirects or modify `/etc/codex/network-policy.json`. Outside that environment, an explicitly reviewed application policy file is required; the included policy example grants no hosts. A local application allowlist cannot override infrastructure controls.

Wikimedia additionally requires an identifying User-Agent with an appropriate public project contact. Once public Test publication exists, its actual repository URL can be used as the project contact; no personal email is necessary. No contact URL is invented in the template.

Operational checks:

```bash
python -m psychology_engine --db /path/to/evidence.sqlite health --source fed_press --max-check-age-hours 48
python -m psychology_engine --db /path/to/evidence.sqlite backup /path/to/new-backup.sqlite
```

Health uses a read-only SQLite connection and does not create a missing store. It checks database integrity, logged collector outcomes, check age and presence of fresh observed values. It does not call sources or certify prediction quality. Backup uses SQLite's online backup API rather than copying a live database file while ignoring WAL. It refuses an existing destination and validates the result. Restore into a separate reviewed path and inspect it with health before using it; never overwrite an active store as a recovery shortcut.

Logs are JSON outcomes. Monitor exit 0 means complete success, 1 total failure, 3 partial success; health uses 0 healthy, 1 unavailable, 3 degraded. Application/configuration errors use 2. A supervisor may alert on these statuses only after alert destination and delivery authorization are configured. No email, Slack, pager or persistent alert was activated.

The templates are not a production certification. Remaining work includes actual permission review, source connectivity, measured collection latency, retention enforcement, backups/restoration drills in the chosen infrastructure, timezone/calendar review, load/resource budgeting, external monitoring and explicit deployment authorization.
