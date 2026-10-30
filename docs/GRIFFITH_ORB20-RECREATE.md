# griffith-orb20: Recreation Package

## Provenance

- ALL-SLEEVES accounting: canonical name "20-minute opening range breakout", type breakout, family griffith, universe "SCOPE universe: 550 US names", asset US equities, timeframe 5m, creator "Griffith R4 parallel strategy lab (ORB20_RVOL_1_0_0)". Algorithm grade PARTIAL with entry, exit and sizing "not recorded in any consulted source" in the accounting; those rules are in the Test card and running Test code below.
- Test catalog entry `griffith-orb20`: card `strategies/griffith/griffith-orb20.md`, code `sleeves/griffith/griffith_intraday.py`, `sleeves/griffith/feedlib/griffith.py`, status waiting.
- Code search record: Searched for code: Test tree at batch start (sleeves/, strategies/, packages/, desk3/, engines/) - found as listed below; Silicon tree (research/, desk trees) and quant-research-backup tree and Midna tree - no additional code file for this canonical id was found in those trees (tree grep for the id, alias and card slug).

## What this strategy is

Buys the first 5-minute close above the 09:30-09:50 range on a name whose opening volume is at least twice its usual, stopped at the range low and flat at 15:55 (card summary).

## Full algorithm

Evaluation order, from the card and the ORB20 class in `sleeves/griffith/griffith_intraday.py` (spec ORB20_RVOL_1_0_0, cadence_s 300):

1. Qualify after 09:51 ET: take the four completed 5-minute bars of 09:30-09:50 ET; the window volume must be >= 2 x the median of the same window over the prior 20 complete sessions.
2. Entry: the first completed 5-minute bar after the range that closes above the range high, while the ask is above the range low; a marketable limit order good for 10 minutes; once per name per day.
3. Exit: stop at the range low; flat from 15:55 ET (the code emits the flat exit with reason ORB20 flat at 15:55 ET).
4. Sizing: a fixed slot of $100,000 / 550 (about $182) per name.

## Files in this repo

- This package: `docs/GRIFFITH_ORB20-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-orb20.md`
- Running code (already in Test; nothing vendored): `sleeves/griffith/griffith_intraday.py` (class ORB20, SLEEVE_ID griffith_orb20), `sleeves/griffith/feedlib/griffith.py` (feed helpers).

## Configuration

- Universe: 550 US names (SCOPE). Timeframe: 5-minute bars. Slot: $100,000 / 550 per name. Cadence: 300 s (code CONFIG). Session: regular session, flat 15:55 ET.

## Data inputs

5-minute bars of the universe (Alpaca; Yahoo without keys per the card), about 22 sessions.

## Install and run

1. Clone this repository (Test).
2. Import the ORB20 sleeve from `sleeves/griffith/griffith_intraday.py` (it is returned by that module's `sleeves()` list) and register it with the desk runtime.
3. Configure the 550-name universe and 5-minute bar feed with at least 22 sessions of history.
4. Run on the 300 s cadence during the regular session.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist:

- A name whose 09:30-09:50 volume is below 2 x its 20-session median for that window gets no entry that day.
- The first 5-minute close above the range high after qualification produces exactly one marketable-limit entry (10-minute validity); a second breakout the same day produces none.
- A print at or below the range low after entry produces the stop exit; any position still held at 15:55 ET is flattened.
