# aster_abs_enj_4h: Recreation package

Provenance: Source row in strategies/ausar/crypto-absorption.md in this repo: Ausar crypto research: the original absorption books and the R19 funding-filter books; the sleeve module header in the desk states Aster batch 1, four-hour confirmed absorption ENJUSDT, engine desk3/aster_batch1.py; the per-sleeve algorithm doc docs/ASTER_ABS_ENJ_4H-ALGORITHM.md states it was derived from the sleeve code on 2026-10-29 (no author spec on file).

## What this sleeve is
This sleeve is a long-only ENJUSDT crypto spot sleeve that buys a four-hour confirmed absorption and sells 16 hours after the confirmation completes. It is a thin adapter in adapters3/ whose evaluate(view, ctx) delegates to the shared engine desk3/aster_batch1.py with its own sleeve id. All rules below are that engine's absorption rules (kind "absorption") as applied to this sleeve's SPECS entry.

## Full algorithm
This sleeve's SPECS entry (desk3/aster_batch1.py): kind="absorption", symbol="ENJUSDT", cadence_s=14400, session="24h". The engine PRODUCERS list names bars (freshness SLA 900s), broker_readback for positions (900s) and quotes (60s) among its producers; INPUTS_BY_KIND for absorption is (bars, quotes, positions).

Exits, evaluated first: if a position in ENJUSDT with qty > 0 is held, its deadline is the first of exit_due_at, deadline_at or confirm_close_at + 16 hours found on the position or in the sleeve state file, falling back to opened_at + 16 hours. At or after the deadline, sell the full qty, reason `aster_abs_enj_4h:deadline_16h`, at the last bar close, overridden by the quote bid when a bid is present; the state entry is removed and saved. The deadline never resets. If a position is held and the deadline has not been reached, no entry is evaluated.

Entries, in code order:
1. Read completed bars for ENJUSDT under the 4Hour or 4H key; fewer than 300 bars (the 300-bar warmup) means no entry, and unparseable bars mean no entry.
2. Advance the Decimal EMA routine (precision 34) over all bars, current-inclusive: volume EMA recurrence (2 x v + 19 x prior) / 21, price EMA recurrence (2 x c + 49 x prior) / 51, each seeded on the first bar. A bar is a shock when volume > 2 x volume EMA, close < open and close < price EMA. A bar is confirmed when the previous bar was a shock and this bar closes above its open and above the previous (shock) bar's midpoint (high + low) / 2.
3. Entry only when the last completed bar is the confirmation bar, with one exception: the catch-up enhancement ENH-ABS4H-CATCHUP-20261024 (on by default) allows a one-bar-late entry when the confirmation fired on bars[-2] and the current bar still closes at or above the shock bar's midpoint (the shock bar is bars[-3] in that case); a close below that midpoint means no catch-up entry. A catch-up entry carries the paired shadow record on enhance_exp and keeps the exit deadline anchored to the original confirmation close + 16 hours.
4. Price is the last bar close, overridden by the quote ask when an ask is present; price missing or <= 0 means no entry.
5. Sizing: qty = slice cash / (price x 1.001), that is 100% of the available slice cash including the 10 bp fee allowance (rules-v1 in the engine header). No volume cap applies to this sleeve.
6. On entry the sleeve state records confirm_close_at (the confirmation bar timestamp, bars[-2] on a catch-up entry and bars[-1] otherwise), exit_due_at = confirm_close_at + 16 hours, and entry_at. The entry intent is a buy with reason `aster_abs_enj_4h:confirmed_absorption` (suffixed `_catchup` on a catch-up entry).

## Files in this repo
- Sleeve adapter (desk adapters3/aster_abs_enj_4h.py): `adapters3/aster_abs_enj_4h.py`; also present as `sleeves/aster_abs_enj_4h.py` and `integration/aster_abs_enj_4h_adapter.py`.
- Shared engine: `desk3/aster_batch1.py` (desk source desk3/aster_batch1.py, SPECS entry for `aster_abs_enj_4h`, kind absorption).
- Roster config row: `config/sleeves.json` (also `engines/config/sleeves.json`).
- Existing per-sleeve algorithm doc: `docs/ASTER_ABS_ENJ_4H-ALGORITHM.md`; existing family card: `strategies/ausar/crypto-absorption.md`.

## Configuration
- Universe: ENJUSDT only. Asset: crypto spot. Timeframe: 4-hour bars.
- Sizing / slice: capital_usd 10000.0, cash_usd 10000.0 in the roster row; sizing rule 100% of slice cash including the 10 bp fee as defined above.
- Cadence: 14400 seconds. Session: 24h. flat_by_close: false; flatten_time_et: null; bp_buffer_frac: 0.02; params: {} in the roster row.
- Parked: false.

## Data inputs
- bars: view bars for ENJUSDT under the 4Hour or 4H key, completed bars with t, o, h, l, c, v; producer bars, freshness SLA 900s in the engine PRODUCERS list. At least 300 bars are required.
- quotes: view["quotes"]["ENJUSDT"] with ask (entry price override) and bid (exit price override); producer quotes, freshness SLA 60s.
- positions: view positions rows with symbol, qty, avg_price and opened_at, plus any exit_due_at / deadline_at / confirm_close_at fields; producer broker_readback, freshness SLA 900s.
- State: the engine state file under ctx state_dir holds confirm_close_at, exit_due_at and entry_at per symbol, written on entry.

## Install and run
1. Place `desk3/aster_batch1.py` in the fresh desk at desk3/aster_batch1.py and the adapter at adapters3/aster_abs_enj_4h.py with SLEEVE_ID = "aster_abs_enj_4h".
2. Register the roster row for `aster_abs_enj_4h` exactly as in the Configuration section in config/sleeves.json (module adapters3.aster_abs_enj_4h, cadence 14400, session 24h, $10,000 slice, inputs bars, quotes, positions).
3. Wire the producers named in the engine (bars, quotes, broker_readback for positions) so every snapshot carries at least 300 completed 4-hour bars for ENJUSDT, a quote where available, and positions, plus view/ctx now and ctx state_dir.
4. First evaluation: call evaluate(view, ctx) on the adapter; it calls desk3.aster_batch1.evaluate("aster_abs_enj_4h", view, ctx). Confirm a snapshot with fewer than 300 bars returns no intents, then run the Verification checks.

## Verification
Behaviour checklist derived from the Full algorithm section (no per-sleeve test file for this sleeve is present in this repo):
- Check that 299 bars produce no entry and 300 bars with a shock bar followed by a confirmation bar (close above open and above the shock midpoint) produce exactly one entry at the last close, or at the ask when a quote ask is present.
- Check the EMA/shock/confirmation math on a fixture using the Decimal recurrences stated above, including the first-bar seeding.
- Check sizing: qty equals slice cash / (price x 1.001).
- Check the catch-up rule: a confirmation one bar old enters only when the current close is at or above the shock midpoint, and its exit deadline stays at the original confirmation close + 16 hours.
- Check the exit: a held position is sold in full at the first evaluation at or after the deadline (bid price when present), never before, and a held position suppresses entries.
