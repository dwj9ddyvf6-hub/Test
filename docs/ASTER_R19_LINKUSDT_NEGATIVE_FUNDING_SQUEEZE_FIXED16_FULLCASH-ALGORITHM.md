Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash: Algorithm

## What it trades

LINKUSDT (the LINK crypto pair), long only. This is one variant of the Aster R19
negative-funding-squeeze family: a 4h breakout entry that is only taken while the
observed funding rate is negative (shorts paying, squeeze conditions).

## Implementation

The sleeve module in this repo (sleeves/aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash.py) is the desk v3 worker entrypoint:
it binds SLEEVE_ID to this variant and delegates evaluation to the shared batch-12
crypto engine (desk3/aster_b12_crypto.py in the desk repo), whose SPECS row for this
sleeve is: symbol LINKUSDT, family nfs (negative funding squeeze), exit policy
fixed16, sizing cap fullcash, hold 16 hours. The identical entrypoint is also
packaged as integration/aster_r19_linkusdt_negative_funding_squeeze_fixed16_fullcash_adapter.py.

## Data inputs

Bars (native 4h bars for LINKUSDT), funding (the latest actually-observed funding
rate), and current positions. Config row: cadence 14400 seconds (4h), session 24h,
slice capital $10,000, buying-power buffer fraction 0.02, not parked, no
flatten-by-close. Note from the engine docstring: funding is a declared producer
input and no v3 funding producer was wired yet at port time, so this sleeve lands
visibly UNFED rather than fake-fed; with no observed funding it cannot enter.

## Entry rules

- Breakout: the latest completed 4h bar's close is above the highest high of the
  prior 20 bars (at least 21 bars required).
- Funding gate (family nfs): the latest actually-observed funding rate must be
  strictly negative. The observation must have been settled and received before
  the decision and be at most 12 hours old at the signal close. Missing funding
  refuses entry; it is never assumed.
- Stale-signal gate (ENH-B8, shared with the batch-11 engine): an entry is refused
  when the signal bar's age (now minus the bar's close) exceeds 4 hours.
- Entries are only evaluated when the sleeve holds no position in the symbol.

## Sizing

fullcash: quantity = slice cash x (1 - 0.001 fee) / entry price, with no volume cap.
Quantity is rounded to 8 decimal places; a non-positive quantity refuses entry.
The entry intent is a buy_to_open with the price hint set to the signal bar's close.

## Exit rules

fixed16: the position is sold once the holding time reaches 16 hours from entry. This deadline exit fires even when bars or funding are missing.
The exit intent is a sell_to_close for the full held quantity, priced at the latest
bar close when available, otherwise the position's average price.

## Ambiguities

The code does not state a stop-loss or take-profit for this family; none exists.
Exit timing for structural arms depends on bar timestamps carried by the snapshot,
so with stale bars a structural exit can be delayed until a fresh completed bar
arrives; the 16h deadline is computed from the position's recorded open time
(or its age_hours field) and does not depend on bars.
