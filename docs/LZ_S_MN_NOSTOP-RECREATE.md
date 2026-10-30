# lz_s_mn_nostop: Recreation Package

## Provenance

- Canonical id: `lz_s_mn_nostop`; canonical name: Midna Nostop (Midna port); aliases: lz_s_mn_nostop. The lz_ prefix is the md2 Lazarus host's sleeve id ('lz_' + the config id `s_mn_nostop`).
- ALL-SLEEVES accounting: type other, family 1h, algorithm grade PARTIAL, gaps: sizing not recorded; sources: md2 catalog entry/exit/strategy text. Accounting lines: entry policy midna_block, max_delay_minutes 30, limit_band_pct 3.0, limit_buffer_pct 1.0, order capped_limit_day; exit 'Midna plan: no stop / time exit 60 bars', hold_from plan, hold_unit_kind 1h, stop_pct 99.0, max_bars 60, rest time; data sleeve_midna :: shadow/paper_sleeve/live/midna/midna_fires_v1.json. Status history: installed.
- Config in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry `s_mn_nostop` (kind 1h, enabled true, state live, sizing budget_usd 1000, max_slots 1, position_usd 1000, global_slot_usd 1000, cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000; research: 'Midna shadow.ts markNostop'; flags include 'turned ON at cutover 2026-10-14 (was shadow)' and 'L-146 scaled x0.611: $2,000 -> $1,000 / 1 slots'). This closes the accounting sizing gap.
- Code in Test: the v3 module and shared engine named in Files; the sibling package `docs/S_MN_NOSTOP-RECREATE.md` covers the unprefixed v3 sleeve from the same code.
- Code search: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4609 entries, plus the file reads named in Provenance); dwj9ddyvf6-hub/Silicon (recursive tree, 21337 entries; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47379 entries; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7855 entries; no path named for this id). Desk source /home/hatch/workspace/muse-desk-v3 was also read for the v3 engines named below. Code was found in Test, so nothing was vendored.

## What this strategy is

The no-stop variant of the hourly Midna signal sleeve: it buys one name flagged by the desk Tensor-bundle hourly signal at $1,000 and exits only after more than 60 hourly bars, with no price stop. Catalog SS5.2: the same hourly Tensor signal as s_mn_hourly, run with NO stop; time exit after 60 bars only. 1 slot x $1,000. Source status Live.

## Full algorithm

Module (`laz_sleeves/s_mn_nostop.py`): SLEEVE_ID = "s_mn_nostop", INPUTS = ("bars_1hour", "positions", "midna_signals"); evaluate returns mn_hourly_evaluate(view, ctx, "s_mn_nostop", stop=False, slots=1) with shared defaults slot_usd=1000.0 and time_bars=60.
Shared evaluation (`engines/laz_sleeves/_common.py` mn_hourly_evaluate), in code order:
1. Session: sess = the date from view now; unparseable means no intents.
2. Exit, for this sleeve's non-zero position: bars are view bars under "SYM|1Hour"; with no bars the position is skipped. The stop branch is disabled (stop=False), so no price fall exits it. If bars held (hourly bars with t after opened_at) > 60, emit a full-qty exit, reason mn_time_bars.
3. Slot gate: if 1 position is held, return the exit only.
4. Entries: signals = view midna_signals {symbol: {signal: bool}}; symbols in sorted order, skipping the held symbol, falsy signals, and symbols with no hourly bars.
5. Cross-stale gate (ENH20, on by default; off via extra s_mn_nostop_enh20 xstale_gate=False): refuse when the symbol's last 1Hour bar lags the latest 1Hour bar among signalled symbols by more than 4 hours, with a paired journal record.
6. Sizing: qty = int(1000.0 // last hourly close); qty at or below 0 is skipped. Emit a market, day entry, price_hint = last, reason mn_hourly_signal. ENH19 slot guard (on by default) stops entries once held + entries emitted reaches 1.
The md2 entry policy above (midna_block, 30 minutes, 3.0% band, 1.0% buffer, capped_limit_day) is the config record for the same lane in the lz_engine book.

## Files in this repo

- This package: `docs/LZ_S_MN_NOSTOP-RECREATE.md`
- Code (already in Test; nothing vendored): `laz_sleeves/s_mn_nostop.py` (also `sleeves/lazarus/s_mn_nostop.py`, `integration/s_mn_nostop_adapter.py`), shared engine `engines/laz_sleeves/_common.py` (mn_hourly_evaluate)
- Config: `packages/grokbot/rl64/lz_engine/config/sleeves.json` entry `s_mn_nostop`; roster row `config/sleeves.json`
- Existing docs: `docs/S_MN_NOSTOP-RECREATE.md`, family card `strategies/midna/mn-hourly-playbook.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

- Module call: stop=False, slots=1, slot_usd 1000.0, time_bars 60. Timeframe 1h.
- Roster row: capital_usd 1000.0, cadence 3600 s, session rth, bp_buffer_frac 0.02, params {}, inputs bars_1hour / positions / midna_signals, parked false.
- md2 config: as in Provenance (budget 1000, 1 slot, position 1000).

## Data inputs

- bars_1hour: view bars under "SYM|1Hour" (t, c). Positions: rows with symbol, qty, avg_price, opened_at, sleeve_id.
- midna_signals: view midna_signals {symbol: {signal: bool}}, the desk Tensor-bundle hourly signal product; the upstream fire file shadow/paper_sleeve/live/midna/midna_fires_v1.json is the config source.

## Install and run

1. Clone dwj9ddyvf6-hub/Test.
2. Place the module at laz_sleeves/s_mn_nostop.py and its shared engine at laz_sleeves/_common.py (repo copy at engines/laz_sleeves/_common.py).
3. Register the roster row in Configuration in config/sleeves.json, and (for the md2 book) the rl64 config entry unchanged.
4. Wire producers so every snapshot carries 1Hour bars, positions, midna_signals and view now.
5. First evaluation: call evaluate(view, ctx); confirm empty midna_signals returns no intents, then run Verification.

## Verification

No dedicated test file for this exact id was found in Test. Behaviour checklist:
- A position down 30 percent with 60 or fewer bars held produces no exit.
- A position with 61 hourly bars after opened_at exits with reason mn_time_bars; at exactly 60 it does not.
- The first signalled symbol in sorted order enters at int(1000 // last); a held position suppresses all entries; unflagged symbols never enter.
- A signalled symbol whose last hourly bar lags the universe latest by more than 4 hours is refused under ENH20; switching it off restores the entry.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
