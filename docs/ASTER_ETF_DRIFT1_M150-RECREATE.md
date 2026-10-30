# aster_etf_drift1_m150: Recreation Package

## Provenance

Provenance: Ausar R17/R18 ETF research, frozen as the R19 ETF books (Source row in `strategies/ausar/r19-etf.md`).

## What this sleeve is

This sleeve is a monthly R19 ETF rotation using policy DRIFT1 at gross 1.5: it holds 100% of its target in the 126-session momentum leader of a 14-ETF basket, and leaves a leading incumbent's shares completely unchanged. It is a thin wrapper in `adapters3/aster_etf_drift1_m150.py` that delegates to the separate shared engine `desk3/aster_etf_b9.py` (source_id R19_ETF_DRIFT1_M150). Its designed exit is the next monthly selection; there is no price stop or target.

## Full algorithm

Evaluation order in `desk3/aster_etf_b9.py` evaluate(), as applied to SPECS['aster_etf_drift1_m150'] = policy 'DRIFT1', gross 1.5, source_id 'R19_ETF_DRIFT1_M150':

1. Timing: when a clock time is known, intents are emitted only inside 09:35-09:40 America/New_York (aware stamps converted to ET; naive stamps read as ET; a date-only or midnight stamp is ungated in the code).
2. Scores: universe = QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. A symbol is eligible only with at least 252 sessions of history (MIN_SESSIONS) and all positive closes in the last 252; score = log(close[-1] / close[-127]), the 126-session log return. No eligible score emits nothing.
3. Selection (DRIFT1, non-interval): the selected symbol is the highest score; ties break alphabetically.
4. Incumbent: the position flagged incumbent / selected if present, otherwise the held symbol with the largest held value at last close.
5. Monthly guard: if positions are held and every held position's signal_month equals the latest bar month, no intents are emitted.
6. DRIFT1 rule: if the selected symbol equals the incumbent and shares of it are held, return nothing at all: the incumbent's shares are retained unchanged.
7. Targets and NAV: NAV for this sleeve is the legacy basis, slice cash (default $10,000) plus held value at last close, because this sleeve id is not in the engine's ENH-NAVBASE set. Desired shares for the selected symbol = floor(1.0 x 1.5 x NAV / price); desired for every other held symbol = 0. A price at or below zero for a held or target symbol emits nothing. Gross is never capped in the sleeve; the dispatcher buying-power check governs the 1.5 gross target.
8. Sell-then-settle: if any holding is above its desired target, emit only the sell intents (full exits where desired is 0) on this evaluation and no buys; buys to reach the target are emitted on a later evaluation when no sells remain. Intents are market, day; entries buy_to_open, exits sell_to_close.
9. Exits: no price stop and no price target. The designed exit is the next monthly selection reducing or replacing a holding under the sell-then-settle rule.

## Files in this repo

- Sleeve module / adapter (same wrapper content in the repo):
- `adapters3/aster_etf_drift1_m150.py`
- `sleeves/aster_etf_drift1_m150.py`
- `integration/aster_etf_drift1_m150_adapter.py`
- Shared engine: `desk3/aster_etf_b9.py` (desk path `desk3/aster_etf_b9.py`)
- Config: `config/sleeves.json` and `engines/config/sleeves.json` (row id `aster_etf_drift1_m150`)
- Existing family doc: see the Provenance source doc path named in the audit record for this sleeve.

## Configuration

- Universe: QQQ, SPY, SMH, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY. Timeframe: daily bars, monthly rebalance; eligibility requires 252 sessions.
- Module: `adapters3.aster_etf_drift1_m150`; cadence_s 300; session 'rth'.
- Slice: capital_usd 10000.0, cash_usd 10000.0; bp_buffer_frac 0.02; flat_by_close false; flatten_time_et null.
- Config params: policy 'DRIFT1', gross_target 1.5, source_id 'R19_ETF_DRIFT1_M150'. Inputs declared in config: bars, positions. Parked: false.
- Engine spec: policy DRIFT1, gross 1.5, source_id R19_ETF_DRIFT1_M150.

## Data inputs

Declared inputs for this sleeve: bars, positions (engine inputs_for for a non-INTERVAL policy). Producers named in the engine: bars (freshness_sla_s 900), broker_readback (900, outputs positions). No quotes input is declared for this b9 sleeve in its config row.

## Install and run

1. Place the files listed in 'Files in this repo' at their repo paths in a fresh desk tree, keeping `desk3/`, `adapters3/`, `sleeves/` and `integration/` side by side so the wrapper imports resolve exactly as in the repo.
2. Register the config row for `aster_etf_drift1_m150` from `config/sleeves.json` (also vendored as `engines/config/sleeves.json`) with the exact values in the Configuration section; do not change cadence, slice or parked state.
3. Wire the producers named in 'Data inputs' so the declared inputs are present in the evaluation `view` at the stated freshness; a missing input must leave the sleeve unfed, never fake-fed.
4. Specific entry point: `from adapters3.aster_etf_drift1_m150 import evaluate; intents = evaluate(view, ctx)`, where `view` carries daily `bars` for the universe, `positions`, `now` and `slice`.
5. First evaluation: call the wrapper entry point `evaluate(view, ctx)` for this sleeve (see the specific call in the preceding step), confirm no intent is emitted outside the stated window / gates, then let the desk dispatcher call it on its cadence and route returned intents to the paper broker. Paper only.

## Verification

No dedicated test file for this sleeve was found in the Test tree at batch start. Prove the recreation with this behaviour checklist, derived from the algorithm above:

- Outside the 09:35-09:40 ET window (when a time is known), or when every held position's signal_month is the latest bar month, no intents are emitted.
- A symbol with fewer than 252 sessions is ineligible; the leader is the highest 126-session log return, ties alphabetical.
- When the selected leader is the held incumbent, no intents at all are emitted.
- When a holding is above target, only sells are emitted on that evaluation; buys follow on a later evaluation. Targets are floor(1.5 x NAV / price) whole shares for the leader and 0 for other holdings, with NAV as stated above.
- No intent ever carries a price stop or profit target.
- The wrapper delegates to the named shared engine with the exact sleeve id, and no rule, threshold or sizing value differs from the values stated above.
- A missing or stale declared input emits no entry intent.
