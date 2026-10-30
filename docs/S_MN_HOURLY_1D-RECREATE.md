# s_mn_hourly_1d: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_mn_hourly_1d`, canonical name "s_mn_hourly_1d", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_mn_hourly_1d" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_mn_hourly_1d`, label "Midna Hourly 1D (Midna port)", kind 1d, enabled True, state live. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Midna Hourly 1D port: the 1D lane of the Hourly Tensor playbook. It buys first-of-setup Tensor consensus-buy fires on the daily timeframe and exits on the calibrated plan, else a 40-session time exit with a 15% stop. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description); the same label and config appear under the related `lz_s_mn_hourly_1d` alias in a separate accounting entry, classified as forecast and ML models (the family signal is the Tensor hourly signal).

## Full algorithm

1. Fire (from `sleeves/midna/hourly.py` and the playbook card): a gap20, first-of-setup 1H consensus-buy fire of the swing basket; a fire is decided once and skipped when its setup episode already traded, when it matches a killed rule, when it is not tradeable or not from Yahoo bars, or when dv20 is unknown or below $1,000,000. For this lane the fires are the canonical tracker's 1D fires.
2. Entry window: entries on the session after the fire's daily bar, window [09:30, +65 min], a DAY limit capped at the fire close + 5%; playbook lane cap for 1d is 5.
3. Lane entry wrapper (config row for this id): policy `midna_block`, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions null, no_chase_mult null, stock_red false, qqq_red false, order `capped_limit_day`.
4. Exit: the calibrated plan (the tracker's planForNewEntry: calibrated stop / max bars, else 40 sessions); config exit row: rule "Midna plan: calibrated plan / time exit 40 sessions", hold_from plan, hold_unit_kind 1d, stop_pct 15.0, max_bars 40, rest time, plan_overrides [].
5. Sizing: the lane config row runs $1,000 a position, 1 slot, $1,000 budget, cap 1.0% of dv20, min_dv20_usd 100000 (see Configuration). The upstream playbook book on the card is a $100,000 account, 20 slots of min($5,000, 1% of dv20), lane caps 1h 5 / 1d 5 / 1w 10; both records are kept because they describe the upstream book and this port respectively. Research lines in the row: Midna rules.ts Hourly 1D; LANE_CAPS 1d:5 MAX_DELAY 65. Flag: L-146 scaled x0.611: $2,000 -> $1,000 / 1 slot.

## Files in this repo

- This doc: `docs/S_MN_HOURLY_1D-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id; the related `lz_` form of this lane is a separate strategy entry in the accounting.
- Signal code (already in Test): `sleeves/midna/lanes.py` (the lane for s_mn_hourly_1d), `sleeves/midna/hourly.py` (Hourly Tensor playbook engine), `sleeves/lazarus/s_mn_hourly.py` (the related hourly port).
- Strategy card (already in Test): `strategies/midna/mn-hourly-playbook.md`; rule lines: `docs/verify/midna.md` (Hourly Tensor playbook section).
- Related recreation doc (already in Test): `docs/LZ_S_MN_HOURLY_1D-RECREATE.md` (the `lz_` form of this lane, same label and config).

## Configuration

Full lz_engine config row for `s_mn_hourly_1d` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_mn_hourly_1d",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1d",
  "label": "Midna Hourly 1D (Midna port)",
  "enabled": true,
  "state": "live",
  "status_text": "ready (Midna port; start FLAT; Midna positions are reference only)",
  "source": {
    "producer": "sleeve_midna (Midna entire-branch signal files + Yahoo)",
    "file": "shadow/paper_sleeve/live/midna/midna_fires_v1.json",
    "lane": "s_mn_hourly_1d"
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
    "rule": "Midna plan: calibrated plan / time exit 40 sessions",
    "hold_from": "plan",
    "hold_unit_kind": "1d",
    "stop_pct": 15.0,
    "max_bars": 40,
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
    "Midna rules.ts Hourly 1D",
    "LANE_CAPS 1d:5 MAX_DELAY 65",
    "InfinityBlade: faithful Midna rules; start FLAT; no fake feeds/fills"
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
2. Read this doc and the UNRESOLVED accounting entry for `s_mn_hourly_1d` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_mn_hourly_1d` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- A 1D fire that is not first-of-setup, matches a killed rule, is not tradeable, or has dv20 under $1,000,000 produces no entry.
- Entry occurs only on the session after the fire's daily bar, inside [09:30, +65 min], as a DAY limit capped at fire close + 5%.
- Exit fires on the calibrated plan stop / max bars, defaulting to the 40-session time exit, and on no other condition.
