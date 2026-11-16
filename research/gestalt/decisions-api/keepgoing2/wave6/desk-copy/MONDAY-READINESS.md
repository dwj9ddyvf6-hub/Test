# MONDAY-READINESS — muse-desk-v3, for Mon 2026-10-26

Written Sat 2026-10-24 ET (evidence Sun 2026-10-25 02:31–02:47 UTC)
by the always-on hardening phase; REFRESHED to the final verified
state Sun 2026-10-25 03:27–03:32 UTC by the Harden + Enhance final
verify (tree 7ce35dd) and this file's own closing commit — see
HARDEN-ENHANCE-REPORT.md for the full 28-row matrix. Every row is
PASS with its evidence or OPEN by name. Nothing below is
pre-claimed: the desk's verdict rides the live RTH paper fill
read-back (A9), which is Monday's proof, not this file's.

> SUPERSESSION NOTE (loose-ends sweep, 2026-11-03): this file is the
> historical readiness record for Mon 2026-10-26 only. The roster
> figures below (312 sleeves) were correct on 2026-10-25; the roster
> grew to 336 at the 2026-10-26 capital epoch and stands at 336 in
> config/sleeves.json today. Do not cite this file for the current
> roster or current readiness; current readiness is the twice-daily
> inspection pair's latest report.

## Checklist

| # | Row | Status | Evidence |
|---|---|---|---|
| 1 | Supervision live, agent-layer independent, reboot-proof | PASS | Chain proven link by link: systemd unit `muse-desk-v3-watchdog` (boot-enabled, Restart=always, KillMode=process; canonical file desk3/systemd/) -> watchdog (pid 4111, status `ok`) -> runner. Final verify restart on the finished tree: runner pid 4056 killed 2026-10-25T03:27:49Z only; watchdog journaled the restart, new runner pid 7270; health.json fresh (generated 03:30:19Z, cycles advancing, cycle 4 by 03:31:49Z), watchdog status `ok` (runner_pid 7270 at 03:32:50Z). A real VM reboot at 02:54Z killed the pre-unit pair together (row 15); the unit is the cure. Desk state at 03:09Z: dispatcher 472 submitted / 472 unique / 0 duplicates across every incident of the night. |
| 2 | Kill drill: runner killed -> detected by effects -> restarted -> reconciled, zero duplicate orders | PASS | Killed runner 17669 at 02:43:07Z (its cycle 3, heartbeat 02:41:15Z). Watchdog journaled restart at 02:43:31Z (reason pid_dead, old 17669 -> new 18659); new runner's first heartbeat 02:44:19Z (cycle 1). Dispatcher read-back after: 452 order_submitted / 452 unique client order ids / 0 duplicates; 3 cross-restart duplicate intents refused by the seen-index (`intent_duplicate`, journaled); per-sleeve journals continuous (29,900 lines). |
| 3 | Restart-intensity cap + named degraded mode (R-ADOPT-1/2) | PASS | Blockers tests/test_harden_supervision_blockers.py 11/11 GREEN, fail-first proven. Live: the cap tripped DEGRADED during the WD1 incident and reset correctly (drill restart counted 1 in its window). |
| 4 | Watchdog storm defect (HARDEN-WD1) cured at the source | PASS | V1 relaunched 3 runners in 61 s because runner.json names the previous pid until a relaunched runner's first (warm) cycle lands. Cure: launch tracking (state/watchdog_launched.json, LAUNCH_GRACE_S=900, status `starting`), DEGRADED journaled once per transition. Live proof: drill relaunch showed `starting` at 02:44:01Z, `ok` at 02:45:01Z, exactly one new runner. Incident + containment in BUGLOG HARDEN-WD1; the storm wrote nothing (dispatcher 881 lines / 436 submitted / 0 dupes before and after). |
| 5 | Schedules inventory: nothing the desk needs lives in the agent layer | PASS | All 167 agent-layer cron jobs inventoried (cron.list, enabled + disabled): ZERO reference muse-desk-v3 / desk3 in id, title, or definition; no system crontab on this box. The desk's own loop is the only v3 schedule: the runner (detached) under the watchdog under its boot-enabled systemd unit (desk3/systemd/muse-desk-v3-watchdog.service) — OS-level, not agent-layer. Nothing redundant exists to stand down. Old-desk (femto/alpaca) crons are all disabled already. Workspace-level jobs that touch the repo generally, kept (backup lane, not the trading loop): `workspace-backup-daily` (daily 03:30 ET, next Sun 2026-10-25 03:30 ET) and `github-backup-watchdog` (every 5 min, last run succeeded 22:36 ET). |
| 6 | Monday dry run: full warm from real producers | PASS | state/warm_bars.json rewritten by the live runner at 02:36Z (18.7 MB, Alpaca SIP); kraken/earnings/vix/xsp producer files fresh in state/; producer_errors {} on every cycle read. |
| 7 | Monday dry run: one full roster cycle in evaluate mode over Friday's close | PASS (repeatedly) | REFRESHED 2026-10-25 (AUDIT-D07): roster **312 = 63 FED / 226 UNFED-by-name / 23 PARKED**, producer_errors named per source (binance_funding HTTP 451 named since the B3 cure; previously {} while funding was down), 0 unaccounted, 0 silent; health.json roster rows 312 == config roster 312 with exact id match, trullas_divergence present ($10,000 slice, cadence 60s, parked=false, UNFED missing quotes — weekend-expected). |
| 8 | Terminal feed fresh | PASS | REFRESHED 2026-10-25 (AUDIT-D07): state/terminal.json + terminal_feed.json regenerated per cycle; headline counts reconcile to the 312 roster (63 FED / 226 UNFED / 23 PARKED). |
| 9 | Dispatch posture read back at the paper door | PASS | PaperDoor base URL https://paper-api.alpaca.markets only (live refused in code); account read back ACTIVE, cash -168822.55 (final verify read); client-order-id namespace `v3-<sleeve>-<intent_id>`; v3- orders = 0 in the broker's recent 500 (correct for the weekend evaluate-only posture). Monday posture: supervised RTH `--dispatch` per OPERATIONS.md. |
| 10 | Legacy-85 guard intact (stopped old desk's positions never touched by v3) | PASS | Final verify read-back: broker positions exactly 85 == state/reconcile_baseline.json 85, symbols equal, 0 quantity mismatches, none missing. v3 has submitted nothing (row 9). |
| 11 | Full regression gate on the final tree | PASS | REFRESHED 2026-10-25 (AUDIT-2026-10-25): gate 1109/1109 at the audit cure head 2c50c30 (Ran 1109 tests in 84.112s, OK; independently re-run by the audit verify phase). Includes the 13 cure blockers (tests/test_audit_cure_20261025_blockers.py, gate-wired by discovery; fail direction proven 11/13 fail/error with cures stashed). |
| 12 | A9 — live RTH paper fill read back from the broker | OPEN by name (mechanism ARMED 2026-10-25, BUGLOG A9-FLIP-20261025) | Monday 2026-10-26's proof, never pre-claimed. The flip no longer needs a human: desk3/watchdog.py desired_mode() returns dispatch from FLIP_AT Mon 09:25 ET — a healthy evaluate-only runner is terminated (verified dead, A-01) and relaunched `--dispatch`, journaled `mode_flip` in state/watchdog.jsonl; any relaunch past FLIP_AT launches dispatch. Read-back procedure (automatic, in the watchdog's healthy-dispatch passes): the first `fill` event in state/dispatcher.jsonl at/after the flip is read back at the broker via PaperDoor.get_order_by_client_id + get_positions (desk3/watchdog.py a9_readback) and written once to state/a9_first_fill.json. A9's proof = that file with verdict FILLED_READ_BACK (broker status filled, filled_qty > 0, broker_position_qty present) + state/runner.json mode "dispatch" with last_dispatched advancing + the `a9_first_fill_readback` journal event. An ACK alone writes SUBMITTED_NOT_FILLED and A9 stays OPEN. Blockers tests/test_a9_monday_flip_blockers.py 12/12, fail direction proven. Until that file exists from Monday's session, the desk's live verdict stays PARTIAL. |
| 13 | Save / restore: Silicon mirror read-back == local HEAD | PASS (at 2c50c30) | REFRESHED 2026-10-25 (AUDIT-2026-10-25): Silicon mirror read back == **2c50c30a70ffb676ad0f428a976e733fa33b76f8**, the audit cure head (verify-phase read-back, STABLE) — the audit report commit after it rides the next mirror run, as with every closing tail commit. |
| 15 | VM-reboot survival of the supervision chain | PASS | The 02:54Z reboot (uptime reset proven) killed runner + hand-launched watchdog together — the gap is recorded as BUGLOG HARDEN-WD2. Cure landed + proven the same night: watchdog under the boot-enabled systemd unit relaunched the runner on unit start (pid 4025); watchdog killed -> systemd respawned it (4023 -> 4055); with KillMode=process the runner (4056) survived a watchdog restart and was adopted by the incoming watchdog via its launch record, exactly one runner at all times. A further full-VM reboot was not forced as a test (it would kill sibling work on the box); boot enablement is proven by `systemctl is-enabled` = enabled + the unit-start relaunch above. |
| 14 | Carried OPEN items (named, not hidden) | OPEN by name | (a) opening_events capture process (HARDEN-B4) — aster_open_gamma_a/b stay UNFED by name. (b) G1 raschke_rre event-gate — owner ruling naming a point-in-time event feed. (c) aster_saty_research — source-absent shell (needs v030 source). (d) Tensor bundle warmer absence — tensor channels wired + fail-closed, no warmer writes a fresh bundle on this box; dependents UNFED by name. (e) Upstream ingest drops (state/ingest/: lazarus_fires / the desk fires / rule fires / timing_signals) — producers built + fixture-proven, upstream lanes unreachable from this box; dependents UNFED by name, never fake-fed. (f) H28 fresh-clone gate on the final head (mirror half proven, row 13; clone-gate half last GREEN at the DEPLOY drill head). (g) vix_hedge sizing granularity (EDGE-B26) — owner sizing ruling. (h) `workspace-backup-daily` cron failing (last success 2026-10-18) — a backup-lane defect outside this program's surface; the desk's own Silicon mirror route (row 13) is independent of it. The former gate trio is CURED (row 11). |
| 16 | Egress bridged for the supervision chain (EGRESS-1) | PASS | The watchdog unit (canonical desk3/systemd/ + installed copy, byte-identical) now carries `EnvironmentFile=-/etc/environment.d/80-hatch-egress.conf` (runtime-maintained egress proxy + CA file; path only, no values in repo) and `Environment=HOME=/home/hatch` (service env had no HOME, so ~-relative key paths missed to /root), and every in-cycle fetch routes through desk3/netfetch.py (http.client) — urllib's forced `Connection: close` was proven to be truncated mid-body by the egress proxy under the service context. Live proof from the relaunched runner's OWN cycles (runner 11769 cycle 1, asof 2026-10-25T04:13:50Z; reproduced post-reboot by runner 1743 cycle 1, asof 04:43:33Z): producer_errors {}, 63 FED / 226 UNFED / 23 PARKED (312 roster since the Trullas landing; AUDIT-D07 refresh), all four kraken sleeves FED incl. free_kraken_link_crowded, kraken.quote real bid/ask, kraken.funding 2005 rows/perp, bars 635 symbols, warm + Coinalyze caches refreshed by the runner itself; PaperDoor read back ACTIVE with 85 positions through the desk's own door in service context. Blockers tests/test_egress_unit_blockers.py 6/6, fail directions proven. BUGLOG EGRESS-1. |
| 17 | Reboot persistence of the installed unit (EGRESS-2 / HARDEN-WD3) | PASS | Route B cured + proven 2026-10-25: hook guardian `v3-supervision-guardian` (canonical desk3/systemd/v3_supervision_guardian.sh == ~/hooks/scripts/ copy, 60 s poll, silent when healthy, single-healer flock) reinstalls the canonical unit hands-free on absence. Route A (systemd user unit) rejected with evidence (no user bus — 'No medium found'; logind/dbus dead; minimal default.target). Simulated-wipe acceptance: stop + installed unit removed + daemon-reload -> guardian healed on next poll (unit_missing); new watchdog 3571 adopted pre-wipe runner 1743 (cycle 9 -> 11, exactly one runner); health fresh, producer_errors {}, 63 FED / 226 UNFED / 23 PARKED (312 roster; AUDIT-D07 refresh); snapshot kraken.quote + kraken.funding 2006/perp from the runner's own cycles; PaperDoor ACTIVE / 85 positions; dispatcher 616 submitted / 616 unique / 0 duplicates across the cutover. Blockers tests/test_egress2_guardian_blockers.py 7/7, fail directions proven. BUGLOG EGRESS-2; desk3/systemd/README.md is the rebuild story. |

## Monday operating posture (explicit)

- v3 is the operating desk. The runner runs evaluate-only over the
  weekend under the watchdog; nothing can place a weekend order
  from stale Friday bars (FakeBroker in evaluate mode).
- At Mon 09:25 ET the watchdog flips the desk to `--dispatch`
  ITSELF (A9-FLIP-20261025): desired_mode() is dispatch from
  FLIP_AT onward, a healthy evaluate-only runner is terminated
  (verified dead) and relaunched in dispatch mode, and every later
  relaunch that day launches dispatch. No human step exists. The
  manual OPERATIONS.md relaunch remains only as a fallback if the
  watchdog itself is degraded (named in state/watchdog.json).
- First reconcile of the dispatch session re-baselines against the
  broker book; the legacy 85 stay unattributed, always.

---

## STATUS AMENDMENT — 2026-10-26 (A9-DOCS-20261026)

**A9 is CLOSED.** The live RTH paper fill read-back this file waited
for happened on Monday 2026-10-26, during the live dispatch session.
Proof: `state/a9_first_fill.json`, verdict **FILLED_READ_BACK**,
recorded 2026-10-26T15:39:25Z — sleeve `aster_etf_leader1_m150`,
symbol ALAB, sell 45 @ 263.8, broker status `filled`,
client_order_id `v3-aster_etf_leader1_m150-aster_etf_leader1_m150-20261026T151808-4`.
Every "A9 OPEN" statement above was true when written (Sat–Sun
2026-10-24/25) and is preserved as the historical record; this
amendment supersedes the A9 status only, as of 2026-10-26.

---

## ROSTER SUPERSESSION — 2026-11-08 (AUDIT-D07)

The roster figures in rows 7, 8, 16 and 17 above (312 sleeves:
63 FED / 226 UNFED / 23 PARKED) are the historical record of the
2026-10-25 dry run and are superseded as a statement of the current
roster. The 2026-11-03 supersession note's figure (336) is likewise
superseded. The live roster is whatever config/sleeves.json carries;
as of this amendment it carried 337 sleeves. Refreshed 2026-11-09
(coffin_rebuilt landing, CAND-ROT-04 The Coffin Rebuilt, basket (a)
ETF form, standard $10,000 slice): 338 sleeves. Refreshed
2026-11-10 (shen_fade landing, LAND-SHEN-20261110: Shen Lao's SPY
0DTE fade sleeve ported behavior-faithful from the retired
femto-lean desk on the owner's ruling, standard $10,000 slice): it
carries 339 sleeves. Current readiness is
the twice-daily inspection pair's latest report, never this file.
This amendment's count is bound mechanically to the config by
tests/test_audit_d07_roster_20261108_blockers.py: the gate goes red
the moment the roster changes without this amendment being
refreshed, so the stale-figure failure class cannot silently
recur a third time.
