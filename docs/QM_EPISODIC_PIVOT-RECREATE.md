# qm-episodic-pivot: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Qullamaggie episodic pivot", type breakout, family qullamaggie, style "Catalyst breakout", universe "1,838-name genome", asset class US equities, timeframe "1d setup, 1m trigger", creator recorded as Kristjan Kullamagi (Qullamaggie), "How to master a setup: episodic pivots"; the pass-3 research desk. Algorithm grade PARTIAL, gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card and code in this repo (see Files).
- Test catalog entry `qm-episodic-pivot` (`docs/CATALOG.json`): status waiting (1), card `strategies/qullamaggie/qm-episodic-pivot.md`, master-desk row `qm_episodic_pivot`.
- Alias: `qm_episodic_pivot`.

## What this strategy is

Buys a quiet stock that gaps up 10% or more on a verified catalyst with heavy early volume, when it takes out the opening-range high from minute 20.

## Full algorithm

From `strategies/qullamaggie/qm-episodic-pivot.md` and `sleeves/qullamaggie/qullamaggie.py` (setup `qm_episodic_pivot` / `episodic_pivot`), in evaluation order:

1. Pool: 20-day dollar volume at or above $5M and a 126-session return at or below 30%, while QQQ is risk-on.
2. Open: gap at or above 10% over the last close and first-20-minute volume at or above 0.5 times the 20-day average.
3. Catalyst: a verified 8-K / 6-K public before the trigger minute.
4. Trigger: from minute 20, price crosses the opening-range high; stop = the low before the trigger bar, within 1 ATR.
5. Exit, hard stop: at the entry stop.
6. Exit, partial: after the third session held, in profit, sells a third (at the close) and moves the stop to breakeven.
7. Exit, trailing rule: after 3 sessions, a close below the 10-day SMA (the 20-day when the close is more than 1.5 ATR above the 10-day) exits at the next open.
8. One setup per sleeve (per the card's code note).

## Files in this repo

- This doc: `docs/QM_EPISODIC_PIVOT-RECREATE.md`
- Strategy card: `strategies/qullamaggie/qm-episodic-pivot.md`
- Code (already in Test): `sleeves/qullamaggie/qullamaggie.py`, `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py`; a copy of the EDGAR / metadata producer named on the card as `desk/feedlib/qm_inputs.py` is present in Test at `packages/claude/master-desk-feedlib/desk/feedlib/qm_inputs.py`
- Rule lines: `docs/verify/qullamaggie.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Code search (this package): Test tree at batch start (sleeves/, strategies/, packages/, adapters/, adapters3/, integration/, tests/), Silicon tree, quant-research-backup tree and Midna tree were searched for the canonical id, its alias and family terms. quant-research-backup holds a different, smaller `femto-lean/sleeves/qullamaggie.py` port; it is not the pass-3 code above and was not vendored, because the strategy's code is already in Test.

## Configuration

- Universe: 1,838-name genome. Timeframe: 1d setup, 1m trigger. Asset class: US equities.
- Book: $100,000. Sizing: 0.35% of the session's opening equity on the stressed loss per share (stop distance + the 95th-percentile adverse overnight gap over 126 sessions + round-trip friction); capped at 20% of equity per name, 100% gross, 25% per sector, 4% total open risk, 1% of 20-day dollar volume, 15 positions.
- State / cadence: not in the record beyond the session-based rules above.

## Data inputs

- Genome daily bars, 1-minute tapes, SEC EDGAR current reports (acceptance time), per the card.

## Install and run

1. Clone the Test repo.
2. Read `strategies/qullamaggie/qm-episodic-pivot.md` and `docs/verify/qullamaggie.md`.
3. Open `sleeves/qullamaggie/qullamaggie.py` (setup `episodic_pivot`) with `sleeves/qullamaggie/vendor/qullamaggie_pass3/desk_fixed.py`.
4. Provide genome daily bars, 1-minute tapes and the EDGAR catalyst / metadata feed (`qm_inputs` in Files).
5. Run each session: build the pool, check the gap and first-20-minute volume, verify the catalyst, then watch the opening-range trigger from minute 20. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist:

- No entry when QQQ is not risk-on, 20-day dollar volume is under $5M, or the 126-session return is over 30%.
- No entry on a gap under 10% or first-20-minute volume under 0.5 times the 20-day average.
- No trigger before minute 20, and no entry without a verified 8-K / 6-K public before the trigger minute.
- The entry stop is the low before the trigger bar and must be within 1 ATR.
- After the third session in profit, exactly one third is sold at the close and the stop moves to breakeven; the 10-day / 20-day SMA exit rule applies after 3 sessions as recorded.
