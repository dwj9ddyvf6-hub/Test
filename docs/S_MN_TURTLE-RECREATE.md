# s_mn_turtle: Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- Batch plan (universe_batches.json, batch 44): canonical id `s_mn_turtle`, canonical name "s_mn_turtle", algorithm grade FULL, unresolved true. Home per plan: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "s_mn_turtle" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: lz_engine config (entry/exit/sizing); alias record sources: md2_lz_engine
- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): this id sits in the UNRESOLVED section as a singleton with no Test entry and no recorded strategy description; the accounting note says it would be settled by the sleeve module docstring or a catalog description. No such module or description for this exact id was found in the search below.
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_mn_turtle`, label "Midna Turtle (Midna port)", kind 1d, enabled True, state live. The full row is quoted in Configuration.
- Searched: fresh trees of dwj9ddyvf6-hub/Test, dwj9ddyvf6-hub/Silicon, dwj9ddyvf6-hub/quant-research-backup and dwj9ddyvf6-hub/Midna (tree files in this run's workspace) were searched by filename for the canonical id; the Test config files packages/grokbot/rl64/lz_engine/config/sleeves.json, packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json, config/sleeves.json and sleeves/lazarus/vendor/lazarus/sleeves.json were fetched and searched by content for the canonical id. No standalone code file named for this exact id was found in Silicon, quant-research-backup or Midna.

## What this strategy is

Midna Turtle port: Turtle System 1 on US equities. It buys 20-day (or 55-day) closing breakouts with Turtle unit sizing and pyramiding, and exits on a 2N stop or a close under the prior 10-day low. In the ALL-SLEEVES accounting this exact id is UNRESOLVED (singleton, no Test entry, no recorded strategy description); the same label and config appear under the related `lz_s_mn_turtle` alias in a separate accounting entry, classified breakout (20-day or 55-day high breakouts with a 2-ATR stop or 10-day-low exit).

## Full algorithm

From the card, `docs/verify/midna.md`, `sleeves/midna/board.py` and `sleeves/midna/vendor/midna/board_signals.py`, in evaluation order:
1. Entry signal: a close above the prior 20-day high, or above the prior 55-day high, new today. At most 4 names, alphabetical.
2. Skip rule: a 20-day breakout right after a winning exit is skipped once; the 55-day breakout is taken.
3. Pyramiding: add a unit at each +0.5N move over the last add, up to 4 units per name. N = ATR(20).
4. Sizing (upstream book): one unit = min(floor(1% of equity / N), floor(cash / price)). Config research line: board.ts turtle enter20/enter55 BOARD_MAX_NAMES=4 BOARD_RISK=0.01.
5. Exit, stop: entry - 2N, raised with adds, acting on any regular-hours print.
6. Exit, signal: a close under the prior 10-day low.
7. Lane wrapper (config row for this id): entry policy `midna_block`, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, order `capped_limit_day`; exit rule "Midna plan: turtle ATR stop / exit10", hold_from plan, hold_unit_kind 1d, stop_pct 99.0 (the stop is ATR-based, not a fixed percent), max_bars 0 (no time exit). Lane sizing row: budget_usd 2000, max_slots 2, position_usd 1000, cap_pct_of_dv20 1.0, min_dv20_usd 100000. Flags in the row: lane budget raised to $4,000 / 4 slots, then L-146 scaled x0.611: $4,000 -> $2,000 / 2 slots.

## Files in this repo

- This doc: `docs/S_MN_TURTLE-RECREATE.md`
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json` row for this id (also in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`).
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id; the related `lz_` form of this lane is a separate strategy entry in the accounting.
- Signal code (already in Test): `sleeves/midna/board.py` (Turtle book: enter_turtle, the Turtle stop and 10-day exit paths), `sleeves/midna/vendor/midna/board_signals.py` (breakout signals), `sleeves/midna/common.py`.
- Strategy card (already in Test): `strategies/midna/mn-turtle.md` (Turtle System 1); rule lines: `docs/verify/midna.md` (Turtle System 1 section).
- Related but different id (already in Test): `sleeves/s_mn_opt_turtle.py` is the listed-options expression of the same Turtle rule and is a different canonical id.
- Related recreation doc (already in Test): `docs/LZ_S_MN_TURTLE-RECREATE.md` (the `lz_` form of this lane, same label and config).

## Configuration

Full lz_engine config row for `s_mn_turtle` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim):

```json
{
  "id": "s_mn_turtle",
  "account": "TEST",
  "broker_account": "TEST_MWJW",
  "kind": "1d",
  "label": "Midna Turtle (Midna port)",
  "enabled": true,
  "state": "live",
  "status_text": "ready (Midna port; start FLAT; Midna positions are reference only)",
  "source": {
    "producer": "sleeve_midna (Midna entire-branch signal files + Yahoo)",
    "file": "shadow/paper_sleeve/live/midna/midna_fires_v1.json",
    "lane": "s_mn_turtle"
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
    "rule": "Midna plan: turtle ATR stop / exit10",
    "hold_from": "plan",
    "hold_unit_kind": "1d",
    "stop_pct": 99.0,
    "max_bars": 0,
    "rest": "time",
    "plan_overrides": []
  },
  "sizing": {
    "budget_usd": 2000,
    "max_slots": 2,
    "position_usd": 1000,
    "position_usd_by_class": {},
    "one_share_max_usd": null,
    "cap_pct_of_dv20": 1.0,
    "min_slot_fraction": 0.9,
    "global_slot_usd": 1000,
    "min_dv20_usd": 100000
  },
  "research": [
    "Midna board.ts turtle enter20/enter55 BOARD_MAX_NAMES=4 BOARD_RISK=0.01",
    "InfinityBlade: faithful Midna rules; start FLAT; no fake feeds/fills",
    "live/midna/reference_positions.json (comparison only)"
  ],
  "flags": [
    "lane budget raised to $4,000 / 4 slots (Trader 2026-10-15)",
    "L-146 scaled x0.611: $4,000 -> $2,000 / 2 slots"
  ]
}
```

## Data inputs

- Source producer and file are named in the config row's `source` block (see Configuration).
- Bars / positions / fires in the shape the host code named in Files consumes; a missing fire or missing filter evidence fails closed in the host family rule.

## Install and run

1. Clone the Test repo.
2. Read this doc and the UNRESOLVED accounting entry for `s_mn_turtle` in `docs/ALL-SLEEVES.json`.
3. Open the config row for `s_mn_turtle` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` and the host / signal code named in Files; confirm the entry, exit and sizing values match Configuration.
4. Wire the data inputs named above.
5. Run one evaluation with no qualifying fire and confirm no entry intent is emitted (fail-closed), then run the Verification checklist before any live use.

## Verification

No dedicated test file for this id was found in Test. Behaviour checklist from the record above:

- A close that does not exceed the prior 20-day and prior 55-day highs produces no entry.
- A 20-day breakout immediately after a winning exit is skipped exactly once; a 55-day breakout in the same situation is taken.
- Adds happen only at +0.5N steps over the last add and never past 4 units.
- A regular-hours print at or below entry - 2N (as raised by adds) exits the name; a close under the prior 10-day low also exits it.
- No more than 4 names are held at once in the upstream book; the lane config caps this port at 2 slots of $1,000.
