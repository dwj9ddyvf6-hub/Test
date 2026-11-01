# bta_onebar_qqq: Recreation Package

## Provenance

- Family algorithm doc in this repo: `docs/BTA-ONEBAR-ALGORITHM.md` (Algorithm 1 states this sleeve's complete algorithm with its own values). Build record: `docs/BTA-ONEBAR-BUILD.md`.
- Live desk roster row (muse-desk-v3 `config/sleeves.json`): module `adapters3.bta_onebar_qqq`, slice {capital_usd 10000.0, cash_usd 10000.0}, cadence_s 60, session rth, parked false, params {}, inputs [bars, bars:QQQ:30Min, positions, quotes, session_fills]. Test roster index row (`docs/SLEEVES.json`): same id and module, code_path `adapters3/bta_onebar_qqq.py`, parked false, catalogued false, in_repo true.
- Provenance of the strategy itself, per the family doc: a post by Breakout Trading Academy (verified X account, handle shown truncated in the supplied screenshot; the full handle is not visible and is not invented here), 2026-10-30. Edge status UNPROVEN: no backtest was run or is claimed; the desk's forward paper record is the judge.
- This package was added 2026-10-31 by the algorithm audit cure B (findings-b6-roster: the sleeve had a complete algorithm in the family doc and live config rows, but no RECREATE doc and no ALL-SLEEVES entry).

## What this strategy is

The base translation of the one-bar family on QQQ: rest a buy stop at the highest high of the last 50 bars and a sell stop at the lowest low, on 30-minute bars. Whichever stop fills, hold for one bar only and close at the next bar's open. In desk terms the entry is a 50-bar Donchian breakout. Long and short, paper only, on its own $10,000 slice.

## Full algorithm

From `docs/BTA-ONEBAR-ALGORITHM.md`, Algorithm 1. Instrument: QQQ shares, long and short. Timeframe: 30-minute bars, completed bars only, every bar in the desk warm product for QQQ. Slice: $10,000. Cadence: 60 seconds. Parked: false. Paper only.

1. Channel. At each evaluation, take the prior 50 completed bars before the latest completed bar. Channel high = their highest high. Channel low = their lowest low. Fewer than 51 completed bars in total: no action.
2. Entries. If the latest completed bar's high is at or above the channel high, a long entry fills at the channel high, or at that bar's open if the bar opened above the channel high. If the latest bar's low is at or below the channel low, a short entry fills at the channel low, or at that bar's open if it opened below it. If the bar spans both extremes, no entry. One position at a time. An entry is counted on the entry bar's ET date; at most 2 entries per day, and entries are only taken on the current session's bars.
3. Size. qty = floor(slice equity / entry price), whole shares. If the live snapshot carries no slice, the configured $10,000 slice is used.
4. Protective stop. Long: entry x 0.998. Short: entry x 1.002. Declared as an ExitRule on the entry intent and executed by the dispatcher. No target, no trailing rule. (Translation note in the family doc: the source's $1,000 money stop on one NQ contract becomes this 0.20 percent stop; the $10,000 slice is the notional cap and the binding sizing constraint.)
5. Time exit. A position entered on bar T exits in full at the open of bar T+1, at market, with the closing position intent (sell_to_close for a long, buy_to_close for a short). No re-entry in the same bar as an exit.

Filters and gates: the channel gate in step 1 and the no-entry rules in step 2 are the only gates; the family summary records "no filters and no other rules".

## Files in this repo

- This package: `docs/BTA_ONEBAR_QQQ-RECREATE.md`
- Family algorithm doc: `docs/BTA-ONEBAR-ALGORITHM.md`; build record: `docs/BTA-ONEBAR-BUILD.md`
- Code: `sleeves/bta_onebar_qqq.py`, `adapters/bta_onebar_qqq.py`, `adapters3/bta_onebar_qqq.py`
- Install proof: `proof/install/bta_onebar_qqq.json`
- Family tests: `tests/test_bta_onebar_blockers.py`
- Roster index: `docs/SLEEVES.json`; accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`
- Named remainder (from the roster index notes): `sleeves/bta_onebar_qqq.py` in Test is a gate-clean copy differing from desk bytes by one word in a provenance sentence; the `adapters3/` code file is byte-identical to the desk's.

## Configuration

- Module: `adapters3.bta_onebar_qqq`. Slice: capital_usd 10000.0, cash_usd 10000.0. Cadence: 60 seconds. Session: rth. Parked: false. Params: {}.
- Inputs: bars, bars_30min, bars:QQQ:30Min, positions, quotes, session_fills.

## Data inputs

- 30-minute bars from the desk warm product (Alpaca SIP), completed bars only; positions, quotes and session fills per the roster inputs above.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path.
3. Register the roster row from Configuration (module `adapters3.bta_onebar_qqq`, $10,000 slice, cadence 60 seconds) and wire the inputs named under Data inputs.
4. Run the sleeve's evaluate path on a fixture snapshot and confirm the behaviour in Verification before any live use.

## Verification

Family blockers: `tests/test_bta_onebar_blockers.py` (24/24 pass at install, per the family doc's Install State). Behaviour checklist from the algorithm above:

- Fewer than 51 completed bars: no action.
- A bar spanning both channel extremes produces no entry; at most 2 entries per ET day; one position at a time.
- Size equals floor($10,000 / entry price) whole shares when no live slice is present.
- A position entered on bar T exits in full at the open of bar T+1; the protective stop sits at entry x 0.998 (long) or entry x 1.002 (short); no target and no trailing rule exists.
