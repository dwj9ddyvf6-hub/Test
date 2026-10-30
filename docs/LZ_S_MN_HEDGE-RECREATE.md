# lz_s_mn_hedge: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Midna QQQ→TZA hedge (Midna port)", type "market timing and rotation", family "1d", universe "not recorded in consulted sources", asset class "not recorded", timeframe "not recorded". Algorithm grade PARTIAL (sources: md2 catalog entry/exit/strategy text); gaps recorded: sizing not recorded in any consulted source. The accounting's own recorded lines for this id are: entry `{"policy": "midna_block", "max_delay_minutes": 65, "limit_band_pct": 5.0, "limit_buffer_pct": 1.0, "window_sessions": null, "no_chase_mult": null, "stock_red": false, "qqq_red": false, "order": "capped_limit_day"}`; exit `{"rule": "Midna plan: hedge exit on flip off / max 20 sessions", "hold_from": "plan", "hold_unit_kind": "1d", "stop_pct": 99.0, "max_bars": 20, "rest": "time", "plan_overrides": []}`; filter/data: sleeve_midna (Midna entire-branch signal files + Yahoo) :: shadow/paper_sleeve/live/midna/midna_fires_v1.json.
- Strategy card in Test: `strategies/midna/mn-qqq-flip5-tza.md`; rule lines in `docs/verify/midna.md` (QQQ flip5 TZA hedge section).
- Searched at batch start (fresh trees taken for this run, 2026-10-30): Test, Silicon, quant-research-backup and Midna, for the canonical id, its alias and its family terms (s_mn_*, midna_*). No code for these ids was found in Silicon, quant-research-backup or Midna beyond the traces noted in Provenance; the code named below is already in Test.

## What this strategy is

A QQQ-to-TZA hedge: when QQQ's slow Tensor state has turned bearish within the last five sessions (flip5), the book holds TZA (the 3x inverse small-cap ETF) at a 30% weight; it exits when the signal flips off or after 20 sessions. The v3 lane runs the same rule at $300 of a $1,000 sleeve budget; the master book runs it at 30% of $100,000.

## Full algorithm

A. v3 lane (`sleeves/lazarus/s_mn_hedge.py`, also at `laz_sleeves/s_mn_hedge.py`), in evaluation order:
1. Inputs: daily TZA bars, positions, and a boolean hedge_signal. No session date: return nothing.
2. Exits first, per held position: if the hedge signal is not on, exit TZA in full (reason mn_hedge_signal_off); else if sessions held reach 20 (MAX_SESSIONS = 20), exit (mn_hedge_max20). The accounting record agrees: exit on flip off / max 20 sessions, stop_pct 99.0 (no price stop).
3. Entry: with nothing held and the signal on, refuse the entry when the TZA bar is provably stale (the ENH19 stale-bar gate in the code, on by default). Otherwise buy TZA with qty = qty_for($1,000 x 0.30, last TZA close) (BUDGET_USD = 1000.0, WEIGHT = 0.30; 1 slot).

B. Master book (`sleeves/midna/shadow.py`, QqqFlip5Tza):
1. flip5: QQQ's slow state turned bearish on one of the last five closed daily bars (data: QQQ and TZA daily bars from the hourly watch).
2. With nothing held, flip5 stages a buy for the next session's open. Sizing: notional = 30% x $100,000 at the open.
3. Exit: sells at the next open when flip5 is off or after 20 held sessions.

## Files in this repo

- This doc: `docs/LZ_S_MN_HEDGE-RECREATE.md`
- Code (already in Test): `sleeves/lazarus/s_mn_hedge.py`, `laz_sleeves/s_mn_hedge.py` (the v3 lane; it reads a hedge_signal input with no producer in this repo, per the card)
- Code (already in Test, master book): `sleeves/midna/shadow.py` (QqqFlip5Tza, hedge_session)
- Strategy card: `strategies/midna/mn-qqq-flip5-tza.md`
- Rule lines: `docs/verify/midna.md` (QQQ flip5 TZA hedge section)
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Universe: TZA only (QQQ is the signal instrument). Timeframe: 1d.
- Weight: 30%. Maximum hold: 20 sessions. No price stop.
- v3 budget: $1,000 (so $300 of TZA); master book: $100,000 (so $30,000 of TZA). These are two recorded books of the same rule; do not blend them.
- State: the held TZA position with its opened_at date; the staged next-open buy (master book).

## Data inputs

QQQ and TZA daily bars from the hourly watch (master book); the v3 lane takes daily TZA bars plus the boolean hedge_signal input.

## Install and run

1. Clone the Test repo.
2. Read this doc and the accounting entry for `lz_s_mn_hedge` in `docs/ALL-SLEEVES.json`.
3. For the v3 lane, open `sleeves/lazarus/s_mn_hedge.py`; confirm BUDGET_USD = 1000.0, WEIGHT = 0.30 and MAX_SESSIONS = 20, serve TZA daily bars and the hedge_signal boolean, and call `evaluate(view, ctx)` per session. For the master book, open `sleeves/midna/shadow.py` (QqqFlip5Tza) and serve QQQ and TZA daily bars from the watch.
4. Verify against the Verification section before any live use.

## Verification

No dedicated test file for this id was found in the Test tree at batch start. Behaviour checklist from the algorithm above:

- With the signal off and nothing held, nothing is bought.
- A held position exits in full on the first evaluation with the signal off, regardless of age.
- A held position with the signal still on exits at 20 sessions held.
- The v3 entry quantity is sized off $300 (30% of $1,000), never the full budget.
- A v3 entry on a provably stale TZA bar is refused while exits are unaffected.
