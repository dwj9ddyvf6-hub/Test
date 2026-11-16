# WAVE 4, V4 AND V7 RECORD (Sat 2026-11-14 night)

Program home: ~/workspace/research_notes/decisions-api-leverage-20261114/
Work folder: keepgoing2/wave4/
Rails held: no desk tree edits (desk files read only), Tensor engine
untouched (bundle archive read only), paper and shadow only, no
credential values printed or logged, heavy jobs run one at a time.

## V4 CHAIN ACCRUAL READY FOR MONDAY: GREEN (dry proof on final artifacts; first production accrual lands Mon 2026-11-16 on the armed schedule)

Collector: keepgoing2/wave4/v4_chain_panel.py. It imports the estate
machinery from ~/workspace/terminal-lineup/site/collect_chains.py
(validate_chain_payload, build_snapshot_doc, fetch_alpaca_content,
fetch_spot_fresh, atomic_write_gz, manifest_line, append_manifest,
append_iv_ledger) and rebinds only that imported module's store
globals inside its own process, so the panel writes to its own store
and no index-store file is touched. It never imports
desk/research/bilbo-options/iv_snapshot.py. Panel: 29 Focus names
(SMH, SOXX, NVDA, AVGO, AMD, MRVL, ARM, TSM, AMAT, MU, SNDK, WDC,
AAOI, COHR, LITE, CRDO, ALAB, AXTI, CRWV, PLTR, RKLB, FLNC, EOSE,
FCEL, BE, OKLO, VST, CEG, XLE) plus SPY and QQQ controls, 31 symbols.
One canonical close snapshot per symbol per session at
~/workspace/morgue/state/morgue/chains_panel/<SYM>/<YYYY-MM-DD>.json.gz
with manifest.jsonl and iv_ledger_modelled.jsonl in that directory,
same snapshot document shape as the index store. The script refuses
outside the weekday 16:00 to 17:30 ET close window unless --force;
--store-dir overrides the store for dry runs; --dry-capture labels
every stored document and manifest line.

Two source defects found and cured in the panel collector during
the dry run (the imported index validator assumes exactly one
chain item with a standard OCC root, true for SPY/QQQ/IWM, false
for two panel names):
- WDC and FCEL: TastyTrade returns 2 items for the same underlying.
  Item 0 is the standard chain (WDC 3,124 contracts; FCEL 770).
  Item 1 is the adjusted chain with digit-suffixed OCC roots
  (WDC1, 106 contracts; FCEL1, 8 contracts) for non-standard
  deliverables, whose codes cannot parse under the estate OCC
  contract. Cure: merged_payload keeps standard-root items only,
  excludes adjusted items, and records the exclusion on the
  snapshot as nonstandard_items_excluded. Both names then stored
  clean (WDC 17 expirations, FCEL 11).

DRY CAPTURE PROOF (evidence: dry_capture/store/, dry_capture/run.log,
v4_cw_proof.json, computed by v4_proof.py from the stored artifacts):
run Sat 2026-11-14 with --force --dry-capture into the scratch store
dry_capture/store (NOT the production store; every document and
manifest line carries dry_capture true and the real capture
timestamp; the chains served are Monday's layout on Friday's close).
Result: 31 of 31 symbols stored ok, 115,718 contracts total,
27,405 contracts with MODELLED IV (Black-Scholes inversion of
Alpaca indicative mids, chain_content band 0.75 to 1.25 moneyness,
expiries within 120 days), measured OI and volume on the same rows.
Controls: SPY 32 expirations, 12,412 contracts, 4,997 with IV;
QQQ 29 expirations, 10,602 contracts, 4,865 with IV.
Cremers-Weinbaum spread (mean call IV minus put IV at matched
strike and expiry, from the stored snapshot rows) computed for all
31 symbols; single-name samples: NVDA -0.0129 (365 matched pairs),
ALAB +0.0654 (200 pairs), MU +0.0233 (924 pairs), AMD +0.0240
(753 pairs), ARM +0.0437 (193 pairs), FCEL +0.0420 (67 pairs),
EOSE -0.0307 (17 pairs), FLNC +0.0297 (8 pairs). Controls: SPY
-0.0717 (2,066 pairs), QQQ -0.0945 (2,048 pairs). The computation
the accrual unblocks now runs end to end on panel data; before
this build the single-name count was zero sessions.

SCHEDULE ARMED: cron job chain-panel-close-capture, weekly Mon to
Fri at 16:46 ET (requested about 16:05 with flexible time; the
runtime set 16:46, inside the script's 16:00 to 17:30 ET window),
timezone America/New_York, timeout_secs 3600 (effective, confirmed
by cron.view), enabled, next run Mon 2026-11-16 16:46 EST. The job
body runs the production command with no --force and no --store-dir
override and requires a manifest read-back report naming any
per-symbol error as an open defect. cron.list was checked first
(181 jobs): no existing panel job, so nothing was duplicated.

INDEX COLLECTOR UNTOUCHED: verified after all runs. Nothing in
~/workspace/terminal-lineup was edited (collect_chains.py mtime
2026-11-13 14:30 UTC, predating this session); the index store
~/workspace/morgue/state/morgue/chains still ends at the
2026-11-13 captures (newest files Nov 13, manifest tail unchanged,
11 sessions per symbol 2026-10-29 to 2026-11-13); the production
panel store chains_panel does not exist yet and is created by
Monday's first scheduled run. The existing index collector's
Monday run (cron chain-snapshot-collector, 30 minute interval)
is unaffected.

## V7(a) MK-01 FIRST HONEST PROBE: DONE, labeled a probe, not an exam

Artifact: v7_mk01_probe.json (script v7_mk01_probe.py, extending
keepgoing2/k3_probe.py TAPE-IMBALANCE-PROXY-v1). SPY and QQQ, last
20 sessions ending Fri 2026-11-13 (2026-10-19 to 2026-11-13), SIP
trades fetched for 15:50 to 16:00 ET only, fully paginated, no
truncation: 1,166,344 SPY prints and 870,383 QQQ prints. Tick-rule
side with direction carried across the window (the k3 original
restarted tick state inside the 2 minute leg; the extension
carries it). Closing move: daily close versus the 15:50 last
print price, proxied by the close of the 15:49 one-minute SIP
bar. Overnight: next session open versus close (n 19; the
2026-11-13 session's next open is Mon 2026-11-16, not yet printed).

Final-10m imbalance versus closing move: SPY Pearson r 0.448,
sign consistency 14 of 20; QQQ r 0.295, sign 14 of 20.
Final-10m imbalance versus next overnight return: SPY r -0.053,
sign 12 of 19; QQQ r -0.033, sign 10 of 19.
Final-2m legs are the same shape (versus closing move r 0.370 SPY
and 0.340 QQQ; versus overnight r -0.099 and -0.079).
Read: the proxy co-moves with the auction-window move it is
measured inside (tape pressure and the move are near the same
object), and it carries no visible relation to the next overnight
return at this size. This is a 20-session probe, not an exam: no
admission claim is made or implied.

## V7(b) D-05 ORPHAN FIRES: RESOLVED, with the orphan reframed on primary evidence

Artifact: v7_d05_orphans.json (script v7_d05_price.py). Bundle
count verified from the bundle itself: bundle-2026-11-11.json
(session 2026-11-11, generated 2026-11-12T02:34:36Z) holds exactly
21 fires. The orphan state is a naming artifact, proven by hash:
the 21 fires are fire-for-fire identical to bundle-2026-11-12.json
(sha256 of the sorted fires array 512e14aef4f15821... identical in
both files), and those fires WERE priced by the Ghost Book on
2026-11-13 (~/workspace/midna-book/ghost-book-ledger.jsonl, 21
rows, source_bundle named as the 11-12 file; 11 viable at R to
target at or above 1.0, 10 below, 4 at R -1.0). No ledger row
names the 11-11 file: that is the whole of the orphan gap, and
v7_d05_orphans.json closes it by carrying the prior pricing
against each 11-11 fire with its provenance stated.

Fresh reprice through the estate options route (desk3 producers
fetch_option_contracts and fetch_option_snapshots, feed
indicative; Ghost method, expiry 2026-11-27, vertical call debit
spread ranked by intrinsic R to target, long call fallback; IV
and delta by Black-Scholes at r 0.04, labeled indicative): 19 of
21 priced, 16 viable at R at or above 1.0. Two named failures:
HIVE (11 strikes listed at the expiry, only 3 quotable, none at
or above entry) and TTMI (no call contracts listed at 2026-11-27
on the Alpaca contracts route). Caution on the reprice numbers:
they are marked on Sat 2026-11-14 weekend indicative quotes at
the Fri 2026-11-13 close spot, after the fires' tape collapsed,
so their R values are NOT comparable to the entry-time Ghost
pricing (example: NBIS reprice R 48.4 on a 0.15 debit for the
157.5/165.0 spread with spot at 115.88, versus entry-time R
9.511). The reprice proves the route prices the panel today; the
entry-time ledger remains the pricing of record.

Forward equity path grading (raw SIP daily bars, entry session
2026-11-11 to close 2026-11-13), the new evidence in this leg:
all 21 fires touched their stop, only 1 touched its target, and
every path is negative: mean -9.47 percent, best CVNA -2.03
percent, worst NBIS -26.26 percent. The 2026-11-11 Tensor fire
set, graded as equities over its first two sessions, was a
uniform loser set into the 2026-11-13 selloff; the Ghost viable
versus non-viable split does not change that at this horizon
(resolution of the options expressions themselves is at their
2026-11-27 expiry, owned by the harvester).

## V7(c) HON RECHECK: record exists on the corrected route and still does NOT verify in bars; not mis-dated; remains unverifiable as an observed event

Artifact: v7_hon_recheck.json (script v7_hon_recheck.py). Route:
corporate actions on data.alpaca.markets only (paper host control
returns 404, confirming Lane C), type reverse_split valid.
Findings, with numbers:
- The record is real in the feed: HON reverse_splits, ex_date
  2026-06-29, old_rate 2, new_rate 1 (1-for-2), record_date,
  process_date and payable_date all stamped 2026-06-29, new CUSIP
  438516205 versus old 438516106.
- The same ex-date carries the HON to HONA spin_off (new_rate
  0.5, new_symbol HONA, record_date 2026-06-15): one separation
  event wearing two records, as Lane C suspected.
- Raw bars (adjustment raw, feed sip) refuse it again: HON close
  232.21 on 2026-06-26 to 227.80 on 2026-06-29, close ratio
  0.981, where a 1-for-2 reverse split requires a ratio near
  2.0. No HON session in 2026 shows anything close: the largest
  absolute close ratios of the year are 1.0643 (2026-06-11) and
  0.9445 (2026-11-05). A full-year scan finds no candidate date,
  so the record is not mis-dated within 2026.
Verdict: the feed carries the reverse-split record, and it had
not taken effect in the traded HON series by 2026-11-13. It
remains unverifiable as an observed event and HON must not be
cited as a reverse-split observation. Lane C's open row is
answered: rechecked on a later pull via the corrected route, same
result, now with the feed record itself on file.

## Files

- keepgoing2/wave4/v4_chain_panel.py (collector)
- keepgoing2/wave4/v4_proof.py and v4_cw_proof.json (dry proof)
- keepgoing2/wave4/dry_capture/store/ (31 symbol snapshots,
  manifest.jsonl, iv_ledger_modelled.jsonl) and dry_capture/run.log
- keepgoing2/wave4/v7_mk01_probe.py and v7_mk01_probe.json
- keepgoing2/wave4/v7_d05_price.py and v7_d05_orphans.json
- keepgoing2/wave4/v7_hon_recheck.py and v7_hon_recheck.json
- Cron: chain-panel-close-capture (Mon to Fri about 16:46 ET,
  next run Mon 2026-11-16)

STATUS: GREEN for V4 (collector proven on stored dry artifacts,
schedule armed and read back, index store verified untouched) and
for V7 (all three legs executed on the estate routes with numbers
on file). EVIDENCE POINTER: this record plus v4_cw_proof.json,
v7_mk01_probe.json, v7_d05_orphans.json, v7_hon_recheck.json and
the dry_capture/store manifest, all under keepgoing2/wave4/.
Open rows named: (1) first production panel accrual is Monday's
scheduled run, unproven until its manifest lands; (2) HON
reverse split stays unverifiable in bars (feed record only);
(3) TTMI has no 2026-11-27 calls on the Alpaca contracts route
and HIVE had no quotable strikes at or above entry, both named
in v7_d05_orphans.json.
