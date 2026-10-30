# muse-shen-fade: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Shen first-touch fade (SPY 0DTE)", type mean reversion, family muse. Algorithm grade in the accounting: PARTIAL, with entry, exit and sizing "not recorded in any consulted source". Those gaps are gaps of the accounting's consulted sources only: the full rule is recorded in the Test strategy card and the running Test code cited below, and this package follows those Test records.
- Aliases merged (Tier A): `muse_shen_fade` (Test catalog) and `shen_fade` (Test catalog; md2 catalog status blocked).
- Test catalog entry (Test `docs/CATALOG.json`): id `muse-shen-fade`, status counts {'waiting': 1}, card `strategies/muse/muse-shen-fade.md`.
- Test strategy card: `strategies/muse/muse-shen-fade.md`. Creator per the card and the code header: Shen Lao, his 10-step SPY 0DTE playbook (the code header records the playbook post of 2026-10-21 and the frozen design of 2026-10-22).
- Running code in Test (verified present at batch start): `sleeves/femto/shen_fade.py` (sleeve_id `shen_fade`, cadence 60 s). The card also names `sleeves/muse/muse.py` on the master-desk side in this repo and a master-desk strategy file not in this repo; the Femto-lean file in this repo is the complete running implementation used here.

## What this strategy is

Buys same-day SPY puts when price first touches a marked level with RSI(14) over 70, calls when under 30, with a +20% / -15% bracket, flat by 11:15.

## Full algorithm

Evaluation order (card, confirmed against the code header's 10 steps in `sleeves/femto/shen_fade.py`):

1. Plan (fixed at 09:29:30): levels are the prior session's high and low, today's premarket high and low, and the three whole dollars nearest the last premarket close; levels within $0.10 merge.
2. Bias latched at the plan and never re-evaluated: above the prior high only puts, below the prior low only calls, otherwise both.
3. First touch only: the first completed 1-minute bar reaching a level's plus-or-minus $0.10 zone burns that level for the day, whether or not it trades.
4. RSI confirmation on the touch bar's close: RSI(14) (Wilder, 1-minute closes) above 70 buys puts, below 30 buys calls, otherwise nothing.
5. Contract: today's SPY expiry, strike nearest the touch bar's close, its quote two-sided, spread at most 5% of mid, at most 60 s old.
6. Entry order ladder: a limit at the mid, at the ask from 60 seconds (the ladder's middle step, mid plus half the spread, is the ask), cancelled at 180 seconds or once price leaves the zone or RSI leaves its extreme. Entries 09:30-11:10, one position at a time. Never a market entry order. On the master desk a re-priced entry for the same contract and size counts as the working order.
7. Bracket on the fill: take-profit resting limit at 1.20 x the premium paid; stop at the first pass with the option's mid at or under 0.85 x the premium paid, sold at the mid.
8. Flat at 11:15: a mid limit, then the bid, then market at 11:17. Half days closing by 11:15 are skipped.
9. Day latches: new entries end for the day once realized P and L reaches -1.80% or +2.40% of the slice; an open bracket still completes.
10. State: the day state (plan / working / position / day) round-trips through the persisted slice state; first-touch latches are also re-derived from today's completed bars each evaluation, and position / day P and L come from the broker position record and the sleeve's own session fills, so a lost state can never re-arm the day.

## Files in this repo

- This package: `docs/MUSE_SHEN_FADE-RECREATE.md`
- Strategy card: `strategies/muse/muse-shen-fade.md`
- Running code (already in Test; nothing vendored for this package):
  - `sleeves/femto/shen_fade.py` (the complete sleeve: CONFIG with sleeve_id `shen_fade`, cadence_s 60, universe (SPY,), risk_pct 0.04)
  - `packages/claude/master-desk-sleeve-port-library/desk/sleeves/muse/sleeves/shen_fade.py` (the same strategy file in the master-desk port library)
  - `sleeves/muse/muse.py` (master-desk side named by the card)
- Rule lines: `docs/verify/muse.md`.

## Configuration

- Universe: SPY only. Asset class: SPY options (0DTE). Timeframe: 1m.
- Slice: $10,000; sizing 4% of the slice in premium per trade, whole contracts, at least 1; the master desk sends no entry costing more than the slice's free cash.
- Cadence: 60 s. Entries 09:30-11:10 ET; flat 11:15 ET.
- Status in the accounting/catalog: waiting (Test catalog); blocked (md2 catalog, for the `shen_fade` row).

## Data inputs

SPY 1-minute bars (2,400: the prior session, the premarket and today; SIP bars per the code header), today's SPY option chain with quotes, and the sleeve's own fills.

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. Place `sleeves/femto/shen_fade.py` on the lean paper desk it was written for (it imports the desk's `core.data` and `core.sleeve` modules, which live with that desk in this repo's sleeve tree).
3. Configure the sleeve from its CONFIG: sleeve_id `shen_fade`, cadence 60 s, universe SPY, risk_pct 0.04 of the $10,000 slice.
4. Serve SPY 1-minute bars and today's SPY option chain with quotes.
5. Run the desk cycle; the sleeve plans at 09:29:30, evaluates every 60 s, and manages its own bracket and 11:15 flattening.
6. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A first touch of a marked level with the touch bar's RSI(14) close above 70 produces a puts entry attempt via the mid / ask ladder; a touch with RSI between 30 and 70 inclusive produces nothing.
- A level touched once never trades again that day, even if the first touch did not trade.
- A filled position carries a resting take-profit at 1.20 x premium and exits at the mid on the first pass with mid at or under 0.85 x premium.
- Any open position is flat by 11:17 at the latest; no new entry is placed after 11:10, or after the day's realized P and L reaches -1.80% or +2.40% of the slice.
- With the reference price above the prior session's high, only puts are bought all day.