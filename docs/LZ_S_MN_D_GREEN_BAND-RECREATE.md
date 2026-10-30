# lz_s_mn_d_green_band: Recreation Package

## Provenance

- Canonical id: `lz_s_mn_d_green_band`; canonical name: Midna D green $10-20 (Midna port); aliases: lz_s_mn_d_green_band. The lz_ prefix is the md2 Lazarus host's sleeve id ('lz_' + the config id `s_mn_d_green_band`).
- ALL-SLEEVES accounting: type forecast and ML models, family 1d, algorithm grade PARTIAL, gaps: sizing not recorded; sources: md2 catalog entry/exit/strategy text. Accounting lines: entry policy midna_block, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, order capped_limit_day; exit 'Midna plan: no stop / time exit 21 sessions', hold_from fill, hold_unit_kind 1d, stop_pct 99.0, max_bars 21, rest time; data sleeve_midna :: shadow/paper_sleeve/live/midna/midna_fires_v1.json. Status history: installed.
- Config in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry `s_mn_d_green_band` (kind 1d, enabled true, state live, sizing budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000; research: 'Midna forward.ts FORWARD_SPECS id=d-green-band ruleId=V4-1D-GREEN-RAW-H21-ALL-879f9d43 FORWARD_NAV=20000 FORWARD_SLOTS=6'; flag 'L-146 scaled x0.611: $2,000 -> $1,000 / 1 slots'). This closes the accounting sizing gap.
- Code in Test: the v3 engine and adapter named in Files; the sibling package `docs/S_MN_D_GREEN_BAND-RECREATE.md` covers the unprefixed v3 sleeve from the same engine.
- Classification evidence in the accounting: muse-desk-v3 desk3/lazarus_midna.py read: s_mn_d_green_band is a Tensor 1D Green fire-consumer with a $10 to $20 price band gate, no stop, 21-session hold; the signal is the Tensor model fire.
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4609 entries, plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21337 entries; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47379 entries; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7855 entries; no path named for this id). Desk source /home/hatch/workspace/muse-desk-v3 was also read for the v3 engines named below. Code was found in Test, so nothing was vendored.

## What this strategy is

A fire-consumer: it buys one name on a daily Green Tensor fire whose price lies in the $10 to $20 band, sized from a $1,000 budget, and holds it for 21 sessions with no price stop. Signal generation stays upstream; the desk engine owns position management.

## Full algorithm

From `desk3/lazarus_midna.py` SPECS entry for `s_mn_d_green_band`: family="green", tf="1D", hold_sessions=21, stop=None, gate="band", budget=1000.0. Maximum 1 open position.
Exits, evaluated first: for each non-zero position, price is the last bar close (keys SYM|1Day, SYM|1D, SYM, SYM|1Week, SYM|1W) or avg_price if no bars; age is read from sessions_held / age_sessions / held_sessions / bars_held, or age_weeks / held_weeks x 5, or counted from entry_date / opened_at against the bars. No stop applies. If age >= 21, emit a full-qty market sell_to_close exit, reason time_21_sessions. If any exit is emitted, return it; if any position is held, return no entry.
Entries, in code order:
1. Fires are read from view midna_fires, view fires, extra midna_fires / fires, or the tensor / tensor_bundle value. No fires means no entry. (The md2 config's source file is shadow/paper_sleeve/live/midna/midna_fires_v1.json, producer sleeve_midna; the engine header records that fires are consumed via the desk Tensor bundle channel as a substitution, fail-closed if absent/stale.)
2. A fire is skipped if it is not a dict, its sleeve_id (when present) differs, its family/kind/signal text does not contain "green", its timeframe/tf does not match 1D (1D, D, DAILY, DAY accepted), it has no symbol, or its date is after the session or more than 10 days before it.
3. Cross-stale gate (ENH20, on by default; off via extra s_mn_d_green_band_enh20 xstale_gate=False): refuse when the symbol's last bar date lags the latest bar date across view bars by more than 4 days.
4. Price: ENH19 reprice is on by default: when on and a fresh last close exists, price = that close; otherwise price = the fire price or the fresh close. Price at or below 0 is skipped.
5. Band gate: refuse unless 10.0 <= price <= 20.0.
6. Sizing: qty = int(1000.0 // price); qty below 1 is skipped. Emit one market, day, buy_to_open entry, price_hint = price, then stop (one entry only).
The md2 entry policy above (midna_block, 65 minutes, 5.0% band, 1.0% buffer, capped_limit_day) is the config record for the same lane in the lz_engine book.

## Files in this repo

- This package: `docs/LZ_S_MN_D_GREEN_BAND-RECREATE.md`
- Code (already in Test; nothing vendored): `desk3/lazarus_midna.py` (SPECS entry s_mn_d_green_band), `adapters3/s_mn_d_green_band.py` (also `sleeves/s_mn_d_green_band.py`, `integration/s_mn_d_green_band_adapter.py`)
- Config: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry `s_mn_d_green_band`; roster row `config/sleeves.json`
- Existing docs: `docs/S_MN_D_GREEN_BAND-RECREATE.md`, `docs/S_MN_D_GREEN_BAND-ALGORITHM.md`, family card `strategies/midna/mn-forward-lab.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Engine: family green, tf 1D, hold 21 sessions, stop None, gate band ($10-$20), budget 1000.0, 1 slot.
- Roster row: capital_usd 1000.0, cadence 300 s, session rth, bp_buffer_frac 0.02, params {}, inputs tensor / bars / positions, parked false.
- md2 config: as in Provenance (budget 1000, 1 slot, position 1000).

## Data inputs

- Tensor / Midna fires: fire rows with sleeve_id, symbol, family, timeframe, date, price. Producer tensor_bundle, freshness SLA 86400 s (engine PRODUCERS).
- Bars: daily bars per symbol. Producer bars, SLA 900 s. Positions: broker readback, SLA 900 s.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place the engine at desk3/lazarus_midna.py and the adapter at adapters3/s_mn_d_green_band.py with SLEEVE_ID = "s_mn_d_green_band".
3. Register the roster row in Configuration in config/sleeves.json, and (for the md2 book) the rl64 config entry unchanged.
4. Wire producers so every snapshot carries Tensor bundle fires, daily bars, positions, now and session.
5. First evaluation: call evaluate(view, ctx) on the adapter; confirm a snapshot with no fires, a stale fire, or a price outside $10-$20 returns no entry, then run Verification.

## Verification

No dedicated test file for this exact id was found in Test. Behaviour checklist:
- A fire for another sleeve, a non-green family, a mismatched timeframe, a future date, or a date more than 10 days old produces no entry.
- A fresh close of $9.99 or $20.01 produces no entry; $10.00 and $20.00 can enter; sizing uses int(1000 // price).
- Any held position suppresses entries; a position aged 21 sessions exits in full and no price move alone exits it.
- A symbol whose last bar lags the snapshot latest by more than 4 days is refused under ENH20, and switching it off restores the entry.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
