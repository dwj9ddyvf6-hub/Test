# s_mn_pairs: Recreation package

Provenance: Source row in strategies/midna/mn-distance-pair.md in this repo: Midna's TypeScript desk (equity books), ported line for line to the master desk (family Midna, asset US equities, timeframe 1d, universe 40 large caps, style pairs). The card's Notes state the Midna v3 s_mn_pairs uses declared pairs and a 60-session z, trades both legs and exits at |z| at most 0.25.

## What this sleeve is
This sleeve trades three declared same-sector large-cap pairs by the Gatev distance method: when a pair's 60-session log-price spread is at least 2 standard deviations from its mean, it goes long the cheap leg and short the rich leg at $500 per leg, and closes both legs when the spread reverts to |z| at most 0.25. The v3 adapter rebuilds the v2 SleeveContext and delegates to sleeves/s_mn_pairs.py signal(bars, slice_state, context).

## Full algorithm
Module constants (sleeves/s_mn_pairs.py): PAIRS = (("KO", "PEP"), ("XOM", "CVX"), ("JPM", "BAC")), LOOKBACK = 60, ENTRY_Z = 2.0, EXIT_Z = 0.25, PER_LEG = 500.0, MAX_PAIRS = 3. CONFIG: sleeve_id s_mn_pairs, cadence_s 300.

Spread (spread_z): both legs need at least 60 bars; the second leg's last 60 bars are matched to the first leg's bars by bar timestamp (str(int(t))); any missing match makes the spread None. spread per session = log(close of first leg) - log(close of second leg); z = (last spread - mean of the 60) / population standard deviation; a zero standard deviation gives z = 0.0 if the last spread equals the mean, else +99.0 or -99.0 by direction.

Evaluation, in code order:
1. Pair status scan, in PAIRS order: if both legs of a pair are held, the pair is working: if |z| <= 0.25, emit exits for both legs in full (a negative-qty leg exits buy_to_close / buy, a positive-qty leg sell_to_close / sell), reason exit spread_reverted with the z; otherwise count it as one open pair. A pair with exactly one leg held is neither exited nor a candidate.
2. If open pairs reach 3, return the exits only.
3. Entries, in PAIRS order, while open pairs < 3: skip a pair with either leg held, a None spread, or |z| < 2.0; apply the cross-stale gate to both legs; Cross-symbol stale gate (ENH20, on by default; switch extra[<sleeve>_enh20] stale_gate=False turns it off): an entry is refused when the symbol's last bar lags the latest bar date across the snapshot bars by more than 4 calendar days, with a paired shadow journal record in extra enh20_journal; exits are never gated. z > 0 means the first leg is rich (spread = log(first) - log(second)): short the rich leg and buy the cheap leg; z < 0 reverses them. qty per leg = floor(500.0 / that leg's last close); if either qty is at or below 0, skip the pair. Emit the cheap leg as a buy_to_open entry and the rich leg as a sell_to_open entry, reasons naming z, and count one more open pair.

Position management: at most 3 open pairs ($1,000 per pair, $500 per leg); the only exit is the spread reversion at |z| <= 0.25; no stop or time exit.

## Files in this repo
- Sleeve module (desk sleeves/s_mn_pairs.py): `sleeves/s_mn_pairs.py`.
- Adapter (desk adapters/s_mn_pairs.py): `adapters/s_mn_pairs.py`; also present as `integration/s_mn_pairs_adapter.py`. The adapter is glue only: adapters/laz8_common.py make_evaluate, repo copies at `engines/adapters/laz8_common.py`.
- Shared sleeve helpers (desk sleeves/laz8_common.py): `engines/sleeves/laz8_common.py` (vendored per engines_map.json).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing family card: `strategies/midna/mn-distance-pair.md`.

## Configuration
- Universe: KO, PEP, XOM, CVX, JPM, BAC as the three declared pairs. Asset: US equities (long/short). Timeframe: 1d.
- Sizing / slice: capital_usd 3000.0, cash_usd 3000.0 in the roster row; $500 per leg, at most 3 pairs, in the module.
- Cadence: 300 seconds. Session: rth. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.
- Roster inputs: bars, positions.

## Data inputs
- bars: view["bars"] {symbol: daily bars with t, c} for the six pair symbols, at least 60 sessions with matching timestamps per pair. Producer named bars, freshness SLA 900 seconds.
- positions: view["positions"] broker rows (signed quantities: the short leg carries a negative qty), converted by the adapter to slice_state. Producer named positions, freshness SLA 900 seconds.

## Install and run
1. Place the sleeve module at sleeves/s_mn_pairs.py, the shared helpers at sleeves/laz8_common.py (repo copy `engines/sleeves/laz8_common.py`), and the adapter at adapters/s_mn_pairs.py with its glue at adapters/laz8_common.py (repo copy `engines/adapters/laz8_common.py`).
2. Register the roster row for `s_mn_pairs` exactly as in the Configuration section in config/sleeves.json (module adapters.s_mn_pairs).
3. Wire the producers so every snapshot carries: daily bars for KO, PEP, XOM, CVX, JPM and BAC, and this sleeve's positions.
4. First evaluation: call evaluate(view, ctx) on the adapter; it normalises bar timestamps and timeframe-suffixed keys, rebuilds slice_state from positions, merges fires/chains/quotes into context.extra, and delegates to the sleeve's signal(bars, slice_state, context). Confirm a snapshot missing the required inputs returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check the spread: a pair with 59 bars or one mismatched timestamp produces no entry; |z| of 1.99 produces no entry and 2.00 can.
- Check direction: a positive z shorts the first-named leg and buys the second; a negative z reverses them; each leg's qty equals floor(500 / its close).
- Check the exit: a fully held pair at |z| <= 0.25 exits both legs (the short leg as buy_to_close), at |z| above 0.25 it stays open, and a pair with only one leg held is left alone.
- Check limits and staleness: no fourth pair opens, and a pair with either leg's bar more than 4 days behind the universe is refused.
