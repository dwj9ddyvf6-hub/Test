# muse-desk-v3 supervision — install and restore story (EGRESS-2)

This directory is the single source of truth for how the desk is
supervised. Rebuild supervision from this page alone.

## Pieces

- `muse-desk-v3-watchdog.service` — canonical systemd SYSTEM unit
  for the watchdog (`python3 -m desk3.watchdog --loop`). The runner
  is relaunched/adopted by the watchdog, never by the unit.
  The unit carries, in its [Service] section:
  - `EnvironmentFile=-/etc/environment.d/80-hatch-egress.conf`
    (runtime-maintained egress proxy + CA file; referenced by PATH
    only — no value from it ever appears in this repo)
  - `Environment=HOME=/home/hatch`
  - `KillMode=process` (a watchdog stop/restart must not kill the
    setsid-detached runner; the incoming watchdog adopts it via
    state/watchdog_launched.json + state/runner.json)
- `v3_supervision_guardian.sh` — canonical guardian script
  (route B, below), installed byte-identically as the Muse hook
  script `~/hooks/scripts/v3_supervision_guardian.sh`, hook id
  `v3-supervision-guardian`, poll interval 60 s.

## The defect (EGRESS-2, proven 2026-10-25 04:42Z)

A VM reboot wiped the installed unit file: the platform rebuilds
/etc/systemd/system at boot (its own egress file returned; the
desk's unit did not). Only the home directory persists across VM
replacements on this platform; everything under /etc and
/usr/local is rebuilt. Hand-reinstall restored supervision, but
any future reboot before or during a session would leave the desk
with no supervisor and no runner until a human noticed.

## Routes evaluated

### Route A — systemd USER unit: REJECTED with evidence

- `systemctl --user status` fails: "Failed to connect to bus:
  No medium found".
- systemd-logind is inactive (dead); the dbus system bus service is
  inactive (dead); there is no /run/user/<uid> tree; loginctl
  cannot connect to the bus at all.
- The guest boots a minimal `default.target`, not a login session
  (see the runtime scheduling guide: a user service is usable only
  when its manager, bus, runtime directory, and startup after
  replacement are established — none of them are here).
- Linger is a logind mechanism; with logind dead it cannot be
  enabled or proven. Route A therefore cannot be proven on this
  platform and was not adopted. Nothing depends on /etc user-unit
  state either way, but there is simply no user manager to run it.

### Route B — Muse-layer hook guardian: ADOPTED (proven)

Hook definitions are runtime-managed saved work, restored by the
runtime after replacement, and the script itself lives under the
persistent home directory. The guardian:

- polls every 60 s;
- stays silent while healthy: installed unit present and
  byte-identical to the canonical repo copy, `systemctl is-active`
  true, state/watchdog.json fresh, state/health.json fresh;
- on absence, under an flock single-healer lock, it reinstalls the
  canonical unit to /etc/systemd/system/, runs daemon-reload,
  `systemctl enable`, `systemctl start`, then verifies by effects
  (unit identical + service active + watchdog status fresh);
- wakes an agent only when its own heal fails; the woken agent
  follows the manual restore procedure below and reports.
- dry runs never heal and never write install state; they report
  the absence as a wake decision so detection can be tested.

Route C (both) was not needed: route B proved out end-to-end in
the Simulated wipe acceptance below; route A had nothing to add.

## Manual restore (fallback; the guardian does this automatically)

1. `cp desk3/systemd/muse-desk-v3-watchdog.service /etc/systemd/system/`
2. `systemctl daemon-reload && systemctl enable muse-desk-v3-watchdog.service && systemctl start muse-desk-v3-watchdog.service`
3. Verify by effects, never by a self-matching process pattern:
   `systemctl is-active muse-desk-v3-watchdog.service`;
   state/watchdog.json fresh with status ok/starting;
   state/runner.json pid alive with a desk3.run_live cmdline and
   adopted (same pid as before the cutover — not duplicated);
   exactly one desk3.run_live process in /proc;
   state/health.json fresh with producer_errors {}.

## Simulated wipe — acceptance proof (EGRESS-2)

Procedure (run 2026-10-25; evidence in BUGLOG EGRESS-2 and
HARDEN-PROGRESS): stop the system service, remove the installed
unit file and its enable symlink, daemon-reload — the platform
wipe, simulated. With no human action after that, the guardian's
next polls restore the unit, supervision returns, the pre-wipe
runner is adopted (not duplicated), health is fresh, the runner's
own cycles keep producer_errors {} with the kraken quote/funding
keys present in the snapshot, the paper door reads back ACTIVE
through the desk's own door, and the dispatcher journal shows
zero duplicate client order ids across the cutover.

## Blockers

tests/test_egress2_guardian_blockers.py (gate-wired via
run_regression_blockers.sh discover): canonical guardian carries
the reinstall/enable/start/daemon-reload lines against the
canonical unit path, the silent-when-healthy and wake-on-failed-
heal decisions, dry-run guard, effects-based verification (no
self-matching process pattern), the single-healer flock, no
credential/proxy values, and this README's route record; the unit
keeps its EGRESS-1 lines. Fail direction proven before the cure
(7 errors: artifacts absent) and after by token removal probes
recorded in BUGLOG EGRESS-2.
