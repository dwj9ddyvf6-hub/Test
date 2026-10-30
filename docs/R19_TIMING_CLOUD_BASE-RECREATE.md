# R19_TIMING_CLOUD_BASE: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Intraday EMA cloud reclaim", type mean reversion, family cloud. Algorithm grade in the accounting: PARTIAL; recorded gap: "exit rule not recorded in any consulted source". Recorded accounting entry text: "Requires an hourly EMA34 > EMA50 trend, then the first ten-minute EMA5/EMA12 cloud touch and causal reclaim. Rejects broken cloud episodes and repeated reclaims." Accounting parameters for this id: kind cloud, slots 8, notional 0.1, fee_bps 5. The exit rule the accounting lacked is recorded in the Test strategy card and the running Test code cited below; this package follows those Test records.
- Merge evidence (Tier A): the ausar_map row for alias `ausar_pb150` lists the r19 link to this id; that alias's own variant form is recorded in the accounting as "variant not recorded in any source". Deployed status in the accounting: mode=independent_local_paper running=False.
- Test strategy card: `strategies/ausar/r19-timing-cloud.md` (variants table: CLOUD_BASE risk 0.25% / notional 10%; CLOUD_AGGRESSIVE risk 0.5% / notional 20%).

## What this strategy is

An intraday pullback book on a frozen 42-name US equity list: on an hourly uptrend it buys the first 10-minute bar that reclaims the EMA 5/12 cloud after a shallow dip, targeting the prior session's high. This is the BASE variant: risk budget 0.25% of the $100,000 book per trade, notional cap 10% of $100,000, 8 slots, fee 5 bps per side.

## Full algorithm

Evaluation order, from the card and the running engine `desk3/aster_batch15.py` (`cloud_signal`, stated in the code to be the archive `r19_timing.cloud_signal` verbatim):

1. Owned exits first: a held position exits at the observed bid when the bid is at or below its stop, or at or above its target; otherwise at its scheduled time exit (entry + 100 minutes, and by 15:50 ET at the latest); the engine also applies the archive's 20-native-bar deadline handling for the timing family.
2. Hourly bias gate: EMA34 > EMA50 on each of the last 3 hourly closes (the code requires at least 53 hourly bars and checks the last 3 EMA pairs).
3. Cloud episode scan (10-minute bars, at least 30 required): find a bar that was fully above the EMA 5/12 cloud, then a dip whose low touches or enters the cloud (low at or below the cloud's upper edge, high at or above its lower edge). The episode must be at most 3 bars long and must not dip deeper than 0.5 ATR (RMA ATR of the 10-minute bars) below the cloud's lower edge.
4. Reclaim: the last 10-minute bar closes back above the cloud's upper edge with the EMA5 minus EMA12 spread widening versus the prior bar, and no earlier bar inside the episode already closed above the cloud with a widening spread (first reclaim only; repeated reclaims and broken episodes are rejected).
5. Session and reward gate: entries only 09:50-15:30 ET, and only if the target (prior session high) is at least 2x the risk (the distance from entry to the stop) — the engine re-checks the price guard stop < bid <= price < target and the 2R condition at entry.
6. Signal outputs: stop = the episode's lowest low minus 0.1 ATR; target = prior session high; deadline 100 minutes.
7. Sizing: quantity is the smaller of the notional cap (10% of $100,000, and available cash) and the risk budget (0.25% of $100,000 divided by entry minus stop), whole shares, at most 8 concurrent slots. Fee 5 bps per side.

Accounting-recorded gap note: the accounting graded this algorithm PARTIAL with the exit rule "not in the record" in its consulted sources; the exit rules above are from the Test card and the Test code, not from the accounting.

## Files in this repo

- This package: `docs/R19_TIMING_CLOUD_BASE-RECREATE.md`
- Strategy card: `strategies/ausar/r19-timing-cloud.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/aster_r19_timing_cloud_base.py` (wrapper; SLEEVE_ID `aster_r19_timing_cloud_base`, INPUTS bars/positions/quotes)
  - `adapters3/aster_r19_timing_cloud_base.py` and `integration/aster_r19_timing_cloud_base_adapter.py` (same wrapper)
  - `desk3/aster_batch15.py` (shared engine; SPECS row kind cloud, risk 0.0025, notional 0.1, fee_bps 5, slots 8, cadence_s 300; `cloud_signal`)
- Master-desk family form (also already in Test): `packages/claude/master-desk-sleeve-port-library/desk/sleeves/families/r19_timing.py` (class `R19Timing`; the vendored evaluator decides end to end over its own snapshot).

## Configuration

- Universe: the frozen 42-name US equity list in the engine's timing configs (the accounting records the universe as "not recorded in consulted sources"; the card records "Frozen 42-name list"). Asset class: US equities.
- Timeframes: 10-minute bars for the cloud, hourly bars for the bias, prior daily high for the target.
- Book: $100,000 notional basis (card and engine agree). Risk 0.25%, notional cap 10%, slots 8, fee 5 bps per side.
- Cadence: 300 s (engine SPECS). Session: regular session, entries 09:50-15:30 ET, flat by the 15:50 ET latest time exit.
- State: held positions with their stop, target and exit time; slot count.

## Data inputs

IEX 10-minute and hourly regular-session bars and the prior session's daily high (card); the engine's declared inputs are bars, positions and quotes. The accounting's recorded filter text agrees: completed hourly and ten-minute OHLC bars, prior-session high.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Import the wrapper: `from sleeves.aster_r19_timing_cloud_base import evaluate`, which delegates to `desk3/aster_batch15.py` `evaluate(SLEEVE_ID, view, ctx)`.
3. Configure the cell with the SPECS row for `aster_r19_timing_cloud_base` (kind cloud, risk 0.0025, notional 0.1, fee_bps 5, slots 8, cadence_s 300).
4. Serve completed hourly and 10-minute bars, the prior daily high, quotes and positions for the 42-name list.
5. Run on the 300 s cadence during the regular session; verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- With EMA34 above EMA50 on the last 3 hourly closes, a 1-to-3-bar dip into the EMA 5/12 cloud no deeper than 0.5 ATR below it, and a final close back above the cloud with a widening EMA spread, exactly one entry is produced, with stop at the episode low minus 0.1 ATR and target at the prior session high.
- The same episode with a second reclaim bar inside it, a dip deeper than 0.5 ATR below the cloud, or an hourly bias failure produces no entry.
- An episode whose prior-high target is less than 2x the entry-to-stop risk produces no entry; no entry occurs outside 09:50-15:30 ET.
- A held position exits at the bid at or below its stop, at or above its target, or at its 100-minute time exit (15:50 ET at the latest), whichever comes first.
- Position size never exceeds the 10% notional cap or the quantity implied by the 0.25% risk budget, and no more than 8 positions are held.
