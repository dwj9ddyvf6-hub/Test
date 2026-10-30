# s_mn_faber: Recreation package

Provenance: Source row in strategies/midna/mn-faber.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk; also the Griffith R4 parallel strategy lab (ETF_SMA10_MONTHLY); Mebane Faber's 10-month rule (family Midna, asset US ETFs, timeframe 1d (monthly average), style trend filter). The card's Variants table gives the Midna v3 row for s_mn_faber.

## What this sleeve is
This sleeve holds each of five asset-class ETFs while its daily close is above its 210-session (10-month) average, at $600 per ETF from a $3,000 budget, evaluating every session. It exits an ETF in full when its close falls below that average. The v3 adapter rebuilds the v2 SleeveContext from the cycle snapshot and delegates to sleeves/s_mn_faber.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_faber.py): ETFS = ("SPY", "EFA", "EEM", "VNQ", "AGG"), BUDGET = 3000.0, PER_ETF = 600.0, MA_BARS = 210. CONFIG: sleeve_id s_mn_faber, cadence_s 300, universe ETFS.

Evaluation, in code order, for each ETF in ETFS order:
1. Bars: the symbol needs at least 210 daily bars; otherwise it is skipped. ma = the simple mean of the last 210 closes; px = the last close.
2. Exit: if the ETF is held and px < ma, emit a full-qty sell_to_close exit, price_hint = px, reason naming the close and the 10-month average.
3. Entry: otherwise, if the ETF is not held and px > ma, and the ENH19 stale-bar gate does not refuse, qty = floor(600.0 / px); if qty > 0 emit a buy_to_open entry, price_hint = px, reason naming the close and the average. A close exactly equal to the average produces neither an entry nor an exit.
4. ENH19 stale-bar gate (ENH19-FABER-STALE-20261024, on by default; off via extra s_mn_faber_enh19 stale_gate=False): an entry is refused when the last bar's date (str(t)[:10]) is more than 4 calendar days before context.session; unparseable dates do not gate; a refusal journals a paired record to extra enh19_journal. Exits are never gated.

Position management: at most one position per ETF, equal $600 target per qualifying ETF, no stop or target beyond the average cross.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_faber.py): `sleeves/s_mn_faber.py`.
- Adapter (desk adapters/s_mn_faber.py): `adapters/s_mn_faber.py`; also present as `integration/s_mn_faber_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-faber.md`.

## Configuration
- Universe: SPY, EFA, EEM, VNQ, AGG. Asset: US ETFs. Timeframe: 1d (daily closes against a 210-session average).
- Sizing / slice: capital_usd 3000.0, cash_usd 3000.0 in the roster row; $600 per ETF in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c} (at least 210 per ETF). Producer named bars in the adapter, freshness SLA 900 seconds.
- positions: view["positions"] broker rows, converted by the adapter to slice_state {symbol: {position: {qty, avg_price, entry_date}}}. Producer named positions, freshness SLA 900 seconds.
- context.session supplies the ENH19 stale-gate session date.

## Install and run
1. Place the sleeve module at sleeves/s_mn_faber.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_faber.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_faber` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_faber).
3. Wire the producers so every snapshot carries: daily bars for SPY, EFA, EEM, VNQ and AGG, and this sleeve's positions.
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the average: with 209 bars an ETF is skipped; with 210 bars the average is the mean of all 210 closes.
- Check the cross: a held ETF closing below the average exits in full; an unheld ETF closing above it enters with qty floor(600 / close); a close equal to the average does nothing.
- Check independence: each of the five ETFs is evaluated separately, so a mix of above- and below-average ETFs produces entries and exits in the same pass.
- Check the stale gate: an entry whose last bar is more than 4 calendar days before the session is refused and journaled, an exit in the same state is still emitted, and turning the ENH19 switch off restores the entry.
