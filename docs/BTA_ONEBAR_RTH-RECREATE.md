# bta_onebar_rth: Recreation Package

## Provenance

- Family algorithm doc in this repo: `docs/BTA-ONEBAR-ALGORITHM.md` (Algorithm 3 states this sleeve's complete algorithm with its own values). Build record: `docs/BTA-ONEBAR-BUILD.md`.
- Live desk roster row (muse-desk-v3 `config/sleeves.json`): module `adapters3.bta_onebar_rth`, slice {capital_usd 10000.0, cash_usd 10000.0}, cadence_s 60, session rth, parked false, params {}, inputs [bars, bars:QQQ:30Min, positions, quotes, session_fills]. Test roster index row (`docs/SLEEVES.json`): same id and module, parked false, catalogued false, in_repo true.
- Provenance of the strategy itself, per the family doc: a post by Breakout Trading Academy (verified X account, handle shown truncated in the supplied screenshot; the full handle is not visible and is not invented here), 2026-10-30. Edge status UNPROVEN: no backtest was run or is claimed; the desk's forward paper record is the judge.
- This package was added 2026-10-31 by the algorithm audit cure B (findings-b6-roster: the sleeve had a complete algorithm in the family doc and live config rows, but no RECREATE doc and no ALL-SLEEVES entry).

## What this strategy is

The regular-session-only variant of the one-bar family on QQQ: the identical 50-bar Donchian one-bar-hold rules of Algorithm 1, computed only on regular trading hours bars, with a 15:55 ET flat so no position is carried past the close. Long and short, paper only, on its own $10,000 slice.

## Full algorithm

From `docs/BTA-ONEBAR-ALGORITHM.md`, Algorithm 3. Instrument: QQQ shares, long and short. Slice: $10,000. Cadence: 60 seconds. Parked: false. Paper only.

Identical to Algorithm 1 (see `docs/BTA_ONEBAR_QQQ-RECREATE.md` for the numbered steps: 50-bar channel on 30-minute completed bars, breakout entry at the channel edge, qty = floor(slice equity / entry price) with the configured $10,000 slice as fallback, protective stop at entry x 0.998 long / entry x 1.002 short with no target and no trailing rule, one position at a time, at most 2 entries per day, time exit in full at the open of bar T+1), with three session restrictions:

1. RTH bars only. The channel and all entry decisions are computed only on bars whose start time is from 09:30 ET to before 16:00 ET. Premarket and after-hours bars in the warm product are ignored entirely.
2. Entries only during RTH, which follows from the bar filter: no bar outside the session can trigger an entry.
3. 15:55 ET flat. Any position still open at 15:55 ET exits at market at that time, instead of the next-bar-open exit carrying it past the close. This flat is the sleeve's own rule (config flat_by_close stays false), so there is exactly one flatten path.

Filters and gates: the Algorithm 1 channel gate and no-entry rules, plus the three session restrictions above; the family summary records "no filters and no other rules".

## Files in this repo

- This package: `docs/BTA_ONEBAR_RTH-RECREATE.md`
- Family algorithm doc: `docs/BTA-ONEBAR-ALGORITHM.md`; build record: `docs/BTA-ONEBAR-BUILD.md`
- Code: `sleeves/bta_onebar_rth.py`, `adapters/bta_onebar_rth.py`, `adapters3/bta_onebar_rth.py`
- Install proof: `proof/install/bta_onebar_rth.json`
- Family tests: `tests/test_bta_onebar_blockers.py`
- Roster index: `docs/SLEEVES.json`; accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`

## Configuration

- Module: `adapters3.bta_onebar_rth`. Slice: capital_usd 10000.0, cash_usd 10000.0. Cadence: 60 seconds. Session: rth. Parked: false. Params: {}. flat_by_close: false (the 15:55 ET flat is the sleeve's own rule).
- Inputs: bars, bars_30min, bars:QQQ:30Min, positions, quotes, session_fills.

## Data inputs

- 30-minute bars from the desk warm product (Alpaca SIP) for QQQ, completed bars only, restricted to bars starting 09:30 ET to before 16:00 ET; positions, quotes and session fills per the roster inputs above.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path.
3. Register the roster row from Configuration (module `adapters3.bta_onebar_rth`, $10,000 slice, cadence 60 seconds) and wire the inputs named under Data inputs.
4. Run the sleeve's evaluate path on a fixture snapshot and confirm the behaviour in Verification before any live use.

## Verification

Family blockers: `tests/test_bta_onebar_blockers.py` (24/24 pass at install, per the family doc's Install State). Behaviour checklist from the algorithm above:

- Premarket and after-hours bars never enter the channel and never trigger an entry.
- Any position still open at 15:55 ET exits at market at that time; no position is carried past the close.
- Otherwise Algorithm 1 behaviour holds exactly: 50-bar channel, at most 2 entries per ET day, one position at a time, stop 0.20 percent from entry, time exit at the open of bar T+1.
