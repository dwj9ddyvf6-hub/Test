# R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_VOLUME1PCT: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "Negative-funding breakout \u00b7 ADAUSDT, 16-hour hold, 1% volume cap", type breakout, family negative_funding_squeeze. Algorithm grade PARTIAL with the gap "exit rule not recorded in any consulted source" in the accounting; the exit rule is in fact recorded in the running Test engine cited below (fixed16 saved deadline) and this package follows that Test record. Accounting entry text (ausar_pb56): "A completed four-hour close must exceed the highest high of the prior 20 bars, with an actually available negative funding observation." Accounting parameters: family negative_funding_squeeze, exit_policy fixed16, capacity volume1pct, symbol ADAUSDT, fee_bps 10. Merge evidence Tier A: ausar_map row ausar_pb56 lists the r19 link to this id; deployed mode=independent_local_paper running=True.
- Test strategy family card for the R19 crypto books: `strategies/ausar/crypto-absorption.md` lists the R19 book structure; the squeeze engine header in `desk3/aster_crypto.py` states its rules verbatim from the TSV spec.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

A negative-funding breakout book on ADAUSDT spot: on a completed 4-hour close above the prior 20 bars' highest high, with an actually observed negative funding rate, it buys sized by a 1% volume cap and holds for a fixed 16 hours. No stop in the record.

## Full algorithm

Evaluation order, from the accounting entry text and the running engine `desk3/aster_crypto.py` (SPECS row for this sleeve: sym ADAUSDT, fam nfs, exit fixed16, cap volume1pct, hold_h 16; FEE 0.001):

1. Owned-exit check first: if a position is held and its held time has reached the saved fixed16 deadline (entry + 16 h; the deadline survives missing inputs), sell the full held quantity. If a position is held and the deadline has not arrived, emit nothing else.
2. Funding gate: the latest actually-observed funding rate for ADAUSDT must exist and be < 0. Missing funding blocks the entry (the engine header: funding is a declared producer input; absent means no entry, never fake-fed).
3. Breakout: the last completed 4-hour close must be strictly above the highest high of the prior 20 bars (the engine requires at least 21 bars and compares the last close to the max high of the preceding 20).
4. Entry price reference: the last completed bar's close.
5. Sizing (volume1pct): fullcash quantity (slice cash, default $10,000 in the engine when no slice is given, times (1 - 0.001 fee) / price) additionally capped at 1% of the preceding 4-hour bar's volume; the result is floored to whole ADA units (the engine's v3 dispatcher note) and must be > 0.
6. Exit: fixed16 only: sell at or after entry + 16 h. No stop, no target, no pyramiding in the record, one position at a time.

Accounting-recorded gap note: the accounting graded this algorithm PARTIAL with the exit rule "not in the record" in its consulted sources; the fixed16 exit above is from the Test engine's SPECS row and header, not from the accounting.

## Files in this repo

- This package: `docs/R19_ADAUSDT_NEGATIVE_FUNDING_SQUEEZE_FIXED16_VOLUME1PCT-RECREATE.md`
- Running code (already in Test; nothing vendored): `sleeves/aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct.py` (wrapper, SLEEVE_ID aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct), `adapters3/aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct.py` and `integration/aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct_adapter.py` (same wrapper), `desk3/aster_crypto.py` (shared R19 crypto engine, SPECS row and `evaluate`).
- Family card: `strategies/ausar/crypto-absorption.md` (R19 crypto book structure).

## Configuration

- Universe: ADAUSDT only (Binance spot). Timeframe: 4h bars. Family: negative_funding_squeeze (nfs in the engine). Exit policy: fixed16. Capacity: volume1pct. Fee: 10 bps per side. Slice cash default: $10,000 in the engine when the view carries no slice.
- State: held position with its entry time / saved deadline.

## Data inputs

Native spot 4h OHLCV (at least 21 bars), observed funding context, and received bid/ask (accounting filter text for ausar_pb56; engine INPUTS bars, funding, positions).

## Install and run

1. Clone this repository (Test).
2. Import the wrapper: `from sleeves.aster_r19_adausdt_negative_funding_squeeze_fixed16_volume1pct import evaluate`, which delegates to `desk3/aster_crypto.py` `evaluate(SLEEVE_ID, view, ctx)`.
3. Configure symbol ADAUSDT, family nfs, exit fixed16, capacity volume1pct, fee 10 bps per side.
4. Serve completed 4h bars, positions, and observed funding; without funding the sleeve correctly refuses every entry.
5. Run the desk dispatcher / evaluate function on the sleeve cadence; it emits at most one entry per breakout and the fixed-deadline exit.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A completed 4-hour close above the highest high of the prior 20 bars, with an observed funding rate below 0 and at least 21 bars, produces exactly one entry at the last close, sized at min(fullcash quantity net of the 10 bps fee, 1% of the preceding bar's volume), floored to whole units.
- The same breakout with an observed funding rate of 0 or above, or with funding unobserved, produces no entry.
- A close at or below the prior 20 bars' highest high produces no entry.
- A held position produces no new entry, and produces exactly one full exit at the first evaluation at or after entry + 16 h, even if bars or funding are then missing.
