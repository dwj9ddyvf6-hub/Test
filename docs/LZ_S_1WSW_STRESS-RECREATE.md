# lz_s_1wsw_stress - Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "1W Swing stress pockets (test)", type forecast and ML models (classification evidence: desk3/lazarus.py SPECS s_1wsw_stress: Tensor 1W swing fire gated by deep drawdown and min_vix 20, so entry only in VIX stress pockets), algorithm grade PARTIAL with gap: sizing not recorded in the accounting; alias lz_s_1wsw_stress (md2_catalog, status installed).
- Accounting algorithm record: entry policy fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day; exit: the sleeve feed fire's plan (15% disaster stop / time exit; hold = 52 weeks (W52)), hold_from plan, hold_unit_kind 1w; data: sleeve_feed composer :: shadow/paper_sleeve/live/sleeve_fires_v1.json.
- Code found in Test already for the same cell without the lz_ prefix: `sleeves/s_1wsw_stress.py` and `adapters3/s_1wsw_stress.py` (SLEEVE_ID = "s_1wsw_stress", delegating to desk3/lazarus.py), `desk3/lazarus.py` SPECS entry s_1wsw_stress, and the existing package `docs/S_1WSW_STRESS-RECREATE.md` plus `docs/S_1WSW_STRESS-ALGORITHM.md`. The lz_ prefix is the md2 catalog form of the same sleeve id, as stated in prior Q07/Lazarus packages.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree taken in this run, 4,609 paths, plus content reads of the files named below); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 paths; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 paths; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 paths; no path named for this id except where stated for mn-tsmom-12-1-etf). Desk source read only: /home/hatch/workspace/muse-desk-v3/desk3/ where stated.

## What this strategy is

A long-only US equity Lazarus fire-consumer sleeve (test form): Tensor 1W swing fires gated by a deep-drawdown tag and VIX >= 20, so entries occur only in VIX stress pockets. It buys fresh matching fires into its single slot and manages the position with a 15% stop and a time exit.

## Full algorithm

From `docs/S_1WSW_STRESS-RECREATE.md` and desk3/lazarus.py SPECS, in code order:

1. SPECS entry s_1wsw_stress: slots=1, capital=1335.0, cadence_s=3600, session="rth", max_age_min=60*24*8, stop_pct=0.15, horizon_sessions=252, family="swing", tf="1W", max_price=5.0, deep=True, min_vix=20.0. No qqq_down, cap_tier or signal_tier key is set. Adapter docstring: 1W Swing stress pockets (CSV off, Disabled).
2. Sleeve-specific gates: family swing / tf 1W enforced only on fires carrying that field; max_price refuses a fire price at or above 5.0 (the bound guard re-checks the fresh price); deep requires the fire or its tags to carry deep or deep70; the VIX gate requires vix >= 20.0 in the fire or tags, a missing VIX value is skipped (not failed) per the existing package.
3. Exits first, per held position, first trigger wins, and any exit intent returns with no entries: (1) stop: current price at or below avg_price * (1 - 0.15), sold in full, reason <sleeve>_stop15, entry stop_price = round(price * 0.85, 4); (2) target: current price at or above the stored target_price; (3) time: sessions held >= horizon_sessions (252, or the stored horizon), sold in full. Sessions counted from session_dates if supplied, else SPY bar dates, else business days. Exits are market, day, sell.
4. Entries, only when no exit fired and open positions < slots: fires from view lazarus_fires, extra lazarus_fires, view tensor_fires, or extra fires (first list found). Skip non-dict fires, mismatched sleeve_id, missing/held symbol, non-buy side, unparseable or out-of-age fired_at (age < 0 or > max_age_min). Then the sleeve-specific gates in step 2. Price: fire price, falling back to latest bar close; with the fresh-price enhancement on by default (ENH-LAZ-REPRICE-20261024), sizing/stop/price_hint use the freshest completed bar close when it exists and differs. Bound guard (ENH19, on by default) refuses a fresh price at/above the fire target_price or the spec max_price. Sizing: per_slot = capital / slots = 1335.0; qty = int(per_slot // execution price); qty < 1 emits nothing. Entry intents are market, day, buy, reason <sleeve>_tensor_fire.

## Files in this repo

- This package: `docs/LZ_S_1WSW_STRESS-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/s_1wsw_stress.py`, `adapters3/s_1wsw_stress.py`, `integration/s_1wsw_stress_adapter.py`, shared engine `desk3/lazarus.py`
- Existing packages/docs: `docs/S_1WSW_STRESS-RECREATE.md`, `docs/S_1WSW_STRESS-ALGORITHM.md`, `docs/S_1WSW-ALGORITHM.md`
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`

## Configuration

SPECS as in step 1 above. Existing S_1WSW_STRESS package records the roster config row: module adapters3.s_1wsw_stress; cadence_s 3600; session rth; capital_usd 1335.0, cash_usd 1335.0; bp_buffer_frac 0.02; flat_by_close false; params {}; inputs [lazarus_fires, bars, positions]; parked true. Accounting entry policy (fear_day etc.) is in Provenance; the executing desk3 engine mechanics are in the Full algorithm section.

## Data inputs

Lazarus fires {sleeve_id, symbol, fired_at, price, target_price?, horizon_sessions?, cap_tier?, signal_tier?, color/family?, tags?} from the Tensor bundle producer into view lazarus_fires (or the alternative channels in step 4); daily bars and SPY bars; positions; sleeve state laz_state.json under ctx state_dir. Fail-closed: no fresh matching fire means no entry.

## Install and run

1. Clone dwj9ddyvf6-hub/Test and keep its layout.
2. Place/confirm the adapter and desk3/lazarus.py at their Test paths.
3. Register the config row for s_1wsw_stress exactly as in Configuration, parked as recorded.
4. Wire lazarus_fires, bars and positions into the snapshot view.
5. Run the desk cycle via the adapter's evaluate(view, ctx), which delegates to desk3.lazarus.evaluate("s_1wsw_stress", view, ctx).
6. Run the Verification checks on fixtures before enabling routing.

## Verification

- Fixture entry: one fresh fire passing family, deep and VIX >= 20 gates, with price < 5.0 and a free slot, produces one market buy sized int(1335.0 // execution price) with stop_price round(price * 0.85, 4).
- The same fire aged past max_age_min, with VIX < 20, without a deep tag, or at price >= 5.0 produces no entry.
- A position at or below 85% of entry exits in full with the stop reason; a position held 252 sessions exits on time.
- Read-back check: this doc was written through the PII gate and read back from Test; its sha256 matches the intended bytes.
