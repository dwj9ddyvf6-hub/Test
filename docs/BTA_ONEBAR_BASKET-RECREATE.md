# bta_onebar_basket: Recreation Package

## Provenance

- Family algorithm doc in this repo: `docs/BTA-ONEBAR-ALGORITHM.md` (Algorithm 2 states this sleeve's complete algorithm with its own values). Build record: `docs/BTA-ONEBAR-BUILD.md`.
- Live desk roster row (muse-desk-v3 `config/sleeves.json`): module `adapters3.bta_onebar_basket`, slice {capital_usd 10000.0, cash_usd 10000.0}, cadence_s 60, session rth, parked false, params {}, inputs [bars, bars:SPY:30Min, bars:QQQ:30Min, bars:MDY:30Min, bars:DIA:30Min, positions, quotes, session_fills]. Test roster index row (`docs/SLEEVES.json`): same id and module, parked false, catalogued false, in_repo true.
- Provenance of the strategy itself, per the family doc: a post by Breakout Trading Academy (verified X account, handle shown truncated in the supplied screenshot; the full handle is not visible and is not invented here), 2026-10-30. This sleeve implements the post's portability claim (the same rules on the S&P 500, MidCap 400 and Dow Jones instruments with zero changes). Edge status UNPROVEN: no backtest was run or is claimed; the desk's forward paper record is the judge.
- This package was added 2026-10-31 by the algorithm audit cure B (findings-b6-roster: the sleeve had a complete algorithm in the family doc and live config rows, but no RECREATE doc and no ALL-SLEEVES entry).

## What this strategy is

The portability-claim translation of the one-bar family: the identical 50-bar Donchian one-bar-hold rules of Algorithm 1, run independently on each of SPY, QQQ, MDY and DIA shares, long and short, paper only, on its own $10,000 sleeve slice.

## Full algorithm

From `docs/BTA-ONEBAR-ALGORITHM.md`, Algorithm 2. Instruments: SPY, QQQ, MDY, DIA shares, long and short. Slice: $10,000 for the sleeve. Cadence: 60 seconds. Parked: false. Paper only.

Everything is identical to Algorithm 1 (see `docs/BTA_ONEBAR_QQQ-RECREATE.md` for the numbered steps), applied independently to each symbol:

- Its own 50-bar channel from its own 30-minute bars (prior 50 completed bars; fewer than 51 completed bars in total: no action for that symbol).
- Its own position: one at a time per symbol, so up to four positions at once across the basket.
- Its own protective stop at 0.20 percent (long: entry x 0.998; short: entry x 1.002). No target, no trailing rule.
- Its own size from the same $10,000 sleeve slice cap formula per entry: qty = floor(slice equity / entry price), whole shares; if the live snapshot carries no slice, the configured $10,000 slice is used.
- Its own counter of at most 2 entries per day per symbol (counted on the entry bar's ET date), so up to 8 entries a day across the basket.
- Its own one-bar time exit: a position entered on bar T exits in full at the open of bar T+1, at market. No re-entry in the same bar as an exit.
- A bar spanning both of a symbol's channel extremes takes no entry for that symbol.

No symbol's state, cap or position affects any other symbol. Filters and gates: the per-symbol channel gate and no-entry rules are the only gates; the family summary records "no filters and no other rules".

## Files in this repo

- This package: `docs/BTA_ONEBAR_BASKET-RECREATE.md`
- Family algorithm doc: `docs/BTA-ONEBAR-ALGORITHM.md`; build record: `docs/BTA-ONEBAR-BUILD.md`
- Code: `sleeves/bta_onebar_basket.py`, `adapters/bta_onebar_basket.py`, `adapters3/bta_onebar_basket.py`
- Install proof: `proof/install/bta_onebar_basket.json`
- Family tests: `tests/test_bta_onebar_blockers.py`
- Roster index: `docs/SLEEVES.json`; accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Module: `adapters3.bta_onebar_basket`. Slice: capital_usd 10000.0, cash_usd 10000.0. Cadence: 60 seconds. Session: rth. Parked: false. Params: {}.
- Inputs: bars, bars_30min, bars:SPY:30Min, bars:QQQ:30Min, bars:MDY:30Min, bars:DIA:30Min, positions, quotes, session_fills.

## Data inputs

- 30-minute bars from the desk warm product (Alpaca SIP) for SPY, QQQ, MDY and DIA, completed bars only; positions, quotes and session fills per the roster inputs above.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path.
3. Register the roster row from Configuration (module `adapters3.bta_onebar_basket`, $10,000 slice, cadence 60 seconds) and wire the inputs named under Data inputs.
4. Run the sleeve's evaluate path on a fixture snapshot and confirm the behaviour in Verification before any live use.

## Verification

Family blockers: `tests/test_bta_onebar_blockers.py` (24/24 pass at install, per the family doc's Install State). Behaviour checklist from the algorithm above:

- Each symbol acts only on its own channel, position, stop, size and daily counter; no symbol's state affects another.
- At most 2 entries per symbol per ET day (8 across the basket); at most one open position per symbol (4 across the basket).
- A position entered on bar T exits in full at the open of bar T+1; the protective stop sits 0.20 percent from entry; no target and no trailing rule exists.
