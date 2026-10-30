# s_mn_w_cyan_adx: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_mn_w_cyan_adx`, canonical name "s_mn_w_cyan_adx", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_mn_w_cyan_adx" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_mn_w_cyan_adx`, label "Midna W cyan high ADX (Midna port)", kind 1d, enabled True, state live. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Midna W cyan high ADX port: a weekly Tensor Cyan rule account. It buys weekly cyan fires on thinner names whose 126-session return is at least about 44.5% and whose weekly ADX is at least about 25.8, and holds each name 126 sessions with no stop. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description); the same label and config appear under the related `lz_s_mn_w_cyan_adx` alias in a separate accounting entry, classified as forecast and ML models (fires come from the external Node GBM rule scorer with momentum and ADX thresholds).

## Full algorithm

From `sleeves/midna/forward_scan.py` (FORWARD_SPECS entry w-cyan-adx) and `sleeves/midna/forward.py`, in evaluation order:
1. Scan: for each name the forward scan builds daily and weekly rows from the panel; a hit requires the weekly state to be cyan.
2. Rule test (ruleId V2-1W-CYAN-RAW-H126-f10092bc, per the config research line): log dollar-volume feature dv <= 7.35, 126-session return (mom) >= 0.445, weekly ADX >= 25.8. Any missing feature fails the test. The lean-desk port of the same frozen rule records the thresholds at full precision: dv <= 7.350284290313721, mom >= 0.44456708133220685, ADX >= 25.795216751098632.
3. Liquid filter (forward lab): last close at least $5 and 20-session mean dollar volume at least $1,000,000.
4. Staging: when the panel's session has been scanned, the account's staged list is replaced by its hits on names it does not hold, up to its free slots (6 - open); at most 6 hits per account.
5. Entry: regular hours from 10:00 ET, on a fresh panel, on the session right after the signal session (an older row is dropped): qty = floor((20,000 / 6) / (price x (1 + cost))), capped by the cash. Config research line: FORWARD_NAV=20000, FORWARD_SLOTS=6.
6. Exit: the first pass once the sessions after the entry day reach the hold: 126 sessions. No price stop.
7. Lane wrapper (config row for this id): entry policy `midna_block`, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, order `capped_limit_day`; exit rule "Midna plan: no stop / time exit 126 sessions", hold_from fill, hold_unit_kind 1d, stop_pct 99.0, max_bars 126, rest time. Lane sizing row: budget_usd 1000, max_slots 1, position_usd 1000, cap_pct_of_dv20 1.0, min_dv20_usd 100000. Flag: L-146 scaled x0.611: $2,000 -> $1,000 / 1 slot.

## Files in this repo

- This doc: `docs/S_MN_W_CYAN_ADX-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id; the related `lz_` form of this lane is a separate strategy entry in the accounting.
- Signal code (already in Test): `sleeves/midna/forward.py` (forward-lab accounts), `sleeves/midna/forward_scan.py` (FORWARD_SPECS entry w-cyan-adx and its rule test), `sleeves/rule_1w_cyan_mom_adx.py` (lean-desk port of the same frozen rule, full-precision thresholds).
- Strategy card (already in Test): `strategies/femto/femto-rule-1w-cyan-mom-adx.md`; rule lines: `docs/verify/midna.md` (forward-lab section).
- Related recreation doc (already in Test): `docs/LZ_S_MN_W_CYAN_ADX-RECREATE.md` (the `lz_` form of this lane, same label and config).

## Configuration

Full lz_engine config row for `s_mn_w_cyan_adx` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_mn_w_cyan_adx",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1d",
  "label": "Midna W cyan high ADX (Midna port)",
  "enabled": true,
  "state": "live",
  "status_text": "ready (Midna port; start FLAT; Midna positions are reference only)",
  "source": {
    "producer": "sleeve_midna (Midna entire-branch signal files + Yahoo)",
    "file": "shadow/paper_sleeve/live/midna/midna_fires_v1.json",
    "lane": "s_mn_w_cyan_adx"
  },
  "entry": {
    "policy": "midna_block",
    "max_delay_minutes": 65,
    "limit_band_pct": 5.0,
    "limit_buffer_pct": 1.0,
    "window_sessions": null,
    "no_chase_mult": null,
    "stock_red": false,
    "qqq_red": false,
    "order": "capped_limit_day"
  },
  "exit": {
    "rule": "Midna plan: no stop / time exit 126 sessions",
    "hold_from": "fill",
    "hold_unit_kind": "1d",
    "stop_pct": 99.0,
    "max_bars": 126,
    "rest": "time",
    "plan_overrides": []
  },
  "sizing": {
    "budget_usd": 1000,
    "max_slots": 1,
    "position_usd": 1000,
    "position_usd_by_class": {},
    "one_share_max_usd": null,
    "cap_pct_of_dv20": 1.0,
    "min_slot_fraction": 0.9,
    "global_slot_usd": 1000,
    "min_dv20_usd": 100000
  },
  "research": [
    "Midna forward.ts FORWARD_SPECS id=w-cyan-adx ruleId=V2-1W-CYAN-RAW-H126-f10092bc FORWARD_NAV=20000 FORWARD_SLOTS=6",
    "InfinityBlade: faithful Midna rules; start FLAT; no fake feeds/fills",
    "live/midna/reference_positions.json (comparison only)"
  ],
  "flags": [
    "L-146 scaled x0.611: $2,000 -> $1,000 / 1 slots"
  ]
}
```

## Data inputs

- Source producer and file are named in the config row's `source` block (see Configuration).
- Bars / positions / fires in the shape the host code named in Files consumes; a missing fire or missing filter evidence fails closed in the host family rule.

## Install and run

1. Clone the Test repo.
2. Read this doc and the UNRESOLVED accounting entry for `s_mn_w_cyan_adx` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_mn_w_cyan_adx` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- A weekly-cyan name with dv above 7.35, 126-session return below 0.445, or weekly ADX below 25.8 is not a hit; a missing feature also fails.
- A hit under $5 or under $1,000,000 dv20 is filtered out.
- No seventh position opens in the forward-lab book; the lane config caps this port at 1 slot of $1,000.
- An entry is made only on the session right after the signal session, from 10:00 ET, with a fresh quote.
- A held name exits at 126 sessions from fill and is never stopped out on price before that.
