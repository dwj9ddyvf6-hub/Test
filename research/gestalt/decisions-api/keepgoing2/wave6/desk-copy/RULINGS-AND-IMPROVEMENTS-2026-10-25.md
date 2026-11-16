# Rulings and Improvements — muse-desk-v3, 2026-10-25

Program: the delegated decisions pass on the 2026-10-25 full audit's
open items. Delegation: The owner, 2026-10-25 15:55 ET — "You decide those
issues; I leave it all up to your wisdom and discernment." Every item
below is a named MIDNA RULING with its rationale and its one-line
revert, executed and proven on the final tree, and reported to the owner
as a vetoable list. Workflow run workflow-run-a68b2b628d10431fbd7faf2dc5b9d200:
phases rulings-a, rulings-b, efficiency, proofs, verify completed and
independently verified; the backup-cure phase hit the 2-hour agent
ceiling mid-work (its cures landed — see the backup section); the
report phase never ran, so this report was written by the parent
from the verified phase evidence.

## Verdict

PARTIAL — every ruling landed and the verify phase passed on the
final tree of the program (gate 1166/1166, census 140 FED /
149 UNFED / 23 PARKED, Silicon mirror == HEAD 27119c3). The items
still open are named at the end; none is silent.

## The rulings

**R1 — Funding source swap (Binance 451 cure).** The snapshot
`funding` scalar's source moved from Binance (HTTP 451 geo-block,
46 sleeves dark) to Coinalyze's current funding rate, fetched with
the case-exact `api_key` header through the producers3 client;
Coinalyze percent values are divided by 100 at parse to match the
history series' fraction units. One snapshot key, source-stamped,
fail-closed on a missing key (`coinalyze_key_missing`) or a cache
older than 3h. Commit d023a9d; 11 blockers, fail-first proven.
Live proof: FED 63 → 109, exactly the 46 formerly-451 sleeves.
Revert: restore the Binance scalar source in the funding producer.

**R2 — raschke_rre event calendar.** Code semantics proved the
sleeve's admission gates are SPY-session MACRO blackout gates
(EVENT_COVERAGE_UNKNOWN / EVENT_BLACKOUT), not earnings — the
earnings producer was considered and rejected on that evidence.
Built desk3/macro_calendar.py + macro_calendar.json: 64 events
(16 FOMC + 24 CPI + 24 NFP), coverage 2026-01-01..2027-12-31,
copied from the official Federal Reserve and BLS schedules (the
sources and refresh path are recorded in the JSON). The sleeve's
core is untouched. Proven both directions: 2026-10-28 (FOMC)
blocks, 2026-10-26 clears, absent payload blocks strict.
Commit 56c31a4; 20 blockers, fail-first at import.
Revert: remove the macro_calendar producer registration.

**R3 — vix_hedge sizing.** The sleeve's own arithmetic (1% risk
fraction, ×100 multiplier, design premium $1.10) priced one
contract at $110 against a $100 budget on the $10,000 slice —
floor = 0 contracts, the EDGE-B26 defect. Slice raised
$10,000 → $11,000: exactly one contract at the design premium.
Commit 8b388e6; 5 blockers proven failing both ways. Takes live
effect on the runner's next natural watchdog restart (config is
loaded at startup; the runner was never force-restarted for it).
Revert: restore slice 10000.0 and drop the +1e-9 in size_contracts.

**R4 — Tensor warmer.** v3 had no vendor/ tree at all; 33 sleeves
sat UNFED on tensor keys. Byte-identical ports from v2 @3593668
(vendor/canonical_bars.py, vendor/tensor_exact.py + tree — engine
hash pin v698 verified, engine untouched; core/tensor_feeds.py)
plus a new desk3/tensor_warm.py (3600s rebuild, 900s failure
backoff, errors named). Live proof: the runner's own bundle
signals are byte-equal to v2's bundle on the same data;
tensor and tensor_fires cured. Commit 4f0f203; 8 blockers.
tensor_daily20 stays UNFED by name (no faithful source).
Revert: deregister the tensor_warm producer.

**R5 — Ingest drops: dispositioned EXTERNAL, no code cure.**
lazarus_fires, sleeve_fires, rule_fires, and timing_signals were
each proven external products on source evidence; the rule_fires
journal-bridge hypothesis was tested and DISPROVEN (the five rule
sleeves are consumers; their journals hold only "unfed" events —
a bridge would be a second source of truth). opening_events was
proven not faithfully buildable in a ~275s-cycle desk (its causal
chain needs a ≤5s break stamp plus a prior-afternoon R5 the desk
does not produce). The ask was posted to the dead-drop and
read-back verified (inbox commit f1b2c367, marker
midna-inbox:2026-10-25-external-drops-request): all four drops,
Ausar's aster_saty_research v030 source, and the R5 definition.
Doc commit d28a76e. Claude's reply (same evening): forwarding
master-desk products is a new data flow awaiting the owner's
decision there, and the the desk alt-data producers behind the
Lazarus fires were switched off 2026-10-19 by owner rule — the
fires may not exist on that side either.

**R6 — Efficiency.** Baseline from the runner's own snapshot
(pool wall 5.25s, eval sum 10.36s on the Sunday FED roster).
saty_gpt_v02 profiled at 5.30s, 4.83s of it in linear session
scans. Cure: desk3/saty_v02_agg.py, a production-side 5m→10m
aggregation cache with O(1) session lookup, served through the
strategy's existing bars_10m door; strategy bytes unchanged;
golden battery oracle-exact (identical intents and evaluation
stamps on three corpora; the sole tolerated delta, the frames
census stamp, is disclosed in the BUGLOG). v02 evaluation
5.40s → 1.09s. Companion: a (mtime_ns, size)-keyed parse memo in
WarmBars killing ~1.3s/cycle of re-parse. Commit 3906d0a.
Named, NOT cured: the hourly warm-cache-expiry cycle pays a
~163s full Alpaca refetch — the fetch contract is verified, so
the spike is a known remaining item, not a defect in hiding.

## Proofs (H28)

The GitHub mirror was pushed first (Silicon muse-desk-v3 ==
3906d0a at proof time), then a clean clone was assembled from the
Git Data API alone: 1,051/1,051 blobs fetched and SHA-verified,
tree diff vs local HEAD: 0 missing, 0 extra, 0 mismatched.
The clone's gate exposed one environmental error in both trees:
test_aster_batch16 reads two oracle JSONs by absolute path from
the Ausar archive, whose local copy the research-storage cleanup
had removed. The documented GitHub re-fetch restored them; the
final verify gate on the program tree ran 1166/1166 OK.
Standing lesson recorded: the archive directory is not purely
dead — one gate test depends on two of its files by path.

## Verify (independent)

Gate 1166/1166 OK at HEAD 27119c3. Census 140 FED / 149 UNFED /
23 PARKED (from 63/226/23 at the audit). producer_errors held
exactly four named keys, none silent: options_chain 403,
quotes 403, qulla stale session, tensor_daily20 bundle key.
Single runner; 85 legacy positions untouched.

## Backup cure (landed by the phase before its ceiling)

Diagnosis from the lane's own records: every seal driver died
with its session (cron window, agent session, runtime restart)
and took the foreground uploader with it, while pushes take
hours; and the watchdog's detached pushes completed but write
no receipts, so a landed push stood unsealed. Two cures landed
in ~/workspace/backup with fail-first blockers wired as
pre-flight arms 11 and 12: (1) the seal now launches its
uploader detached (start_new_session) so it survives its
driver; (2) the secret scan streams its diff instead of holding
1.37 GB in shell variables — the whole-diff capture had been
SIGKILLed on this memory-tight box mid-run, leaving no trace.
The run under the cures committed home HEAD 9eddc32d
(15,218 paths, scan clean). At this report's writing a seal for
that HEAD is in flight under the watchdog; verify_backup.py
remains the only judge of SEALED.

## After this program (owner actions, separately proven)

- Best Setups disconnected and disabled on the owner's ruling
  (BS-DISABLE-20261025, commit bd9a4dc; live feed verified
  carrying the disabled stamp; the vendored package is untouched
  and dormant).
- t_cci_corr installed on the owner's order (commits 80b7c99 +
  8730e3c; roster 313; gate 1185/1185; FED live; first scan found
  TEM pending for Monday's open).

## Still open, by name

1. A9 — Monday's first live RTH paper fill, read back from the
   broker. The proof the v3 build has owed since 2026-10-24.
2. options_chain + quotes producers — HTTP 403 on the SIP/OPRA
   feeds. Read-only probes (2026-10-25) found the doors on this
   account tier: quotes answer on delayed_sip, options snapshots
   on indicative (no greeks on that tier — the sleeves with a
   genuine greeks requirement keep that specific gap). Wiring is
   the next v3 pass.
3. tensor_daily20 — UNFED, no faithful source exists.
4. qulla — stale session error, producer-side.
5. External drops (R5) — awaiting peer owners; Claude's lane
   says the Lazarus alt-data producers are off by owner rule
   since 2026-10-19.
6. aster_saty_research — shell until the v030 source arrives.
7. The ~163s hourly warm-refetch spike (R6, named above).
8. vix_hedge's $11,000 slice (R3) takes live effect on the
   runner's next natural restart.
9. The workspace seal — in flight for HEAD 9eddc32d at writing;
   the home tree keeps moving under the memory loop, so the
   watchdog treadmill is the steady state until a quiet moment.
