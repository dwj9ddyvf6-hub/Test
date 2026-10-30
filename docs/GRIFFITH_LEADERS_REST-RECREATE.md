# griffith-leaders-rest: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`): canonical name "Leaders Rest", type mean reversion, family griffith, style evidence "Pullback in a leader", universe "SCOPE universe: 550 US names (SPY, QQQ, IWM and the sector ETFs excluded)", US equities, timeframe 1d, creator "Griffith / Ledge desk, Leaders Rest LR_1_1_0_CORRECTED". Test catalog entry `griffith-leaders-rest`, status live (1). Algorithm grade PARTIAL with recorded gaps "entry/signal rule not recorded", "exit rule not recorded", "sizing not recorded".
- Test strategy card: `strategies/griffith/griffith-leaders-rest.md`. The card does record entry, exit and sizing in full (quoted below), and the running code in this repo is listed on the card. The accounting gaps are gaps of the accounting pass, not of this repo's record.
- Card note on scope: only the bracket exits are carried; the source's lifecycle exits (thesis break, a 15-session time exit, breakeven, trailing) are not carried.

## What this strategy is

A daily leader-pullback system: once a day it finds market leaders resting off their highs (a 3-12% pullback or a tight base) with RSI 48-68, and arms a GTC limit buy at the prior close, bracketed at -1.6 / +2.8 ATR.

## Full algorithm

From the strategy card, in evaluation order:

1. Decision: once a trading day before the open (else at the session's first pass), on the last completed bars, through the source's orchestrator over the universe.
2. Leader filter: at least 253 sessions; price at least $10 or 20-day dollar volume at least $20M; within 25% of the 52-week high; EMA 50 rising over 10 sessions; 12-1 momentum above SPY's; price above EMA 50 (or above EMA 21 with EMA 50 rising); market gate: SPY not below a falling EMA 50, and SPY's 12-1 momentum not under -4% while SPY is under its EMA 200 or its EMA 50 is falling.
3. Setup: resting (3-12% under the 20-day high, or the last 15 days' range at most 60% of the prior 20 days' with 2-18% off the 52-week high) and RSI(14) 48-68.
4. Order: a GTC buy limit at the decision close, armed 5 days.
5. Delivery, every regular-session pass (15 minutes): a plan is dropped when the name is held or the ask is at or under its stop, and waits while an entry works on the name; otherwise it goes in as a GTC order carrying its stop-loss and take-profit.
6. Exit: bracket only: stop at the limit - 1.6 ATR, target at the limit + 2.8 ATR (ATR(14), at least 1.5% of price).
7. Sizing: risk 0.5% of equity / risk per share, within the strategy's 3% risk cap less its open and armed risk; per order at most 35% of equity and at most 98% of buying power; a held name is not added to; $100,000 book.

## Files in this repo

- This package: `docs/GRIFFITH_LEADERS_REST-RECREATE.md`
- Strategy card: `strategies/griffith/griffith-leaders-rest.md`
- Running code (already in Test; nothing vendored for this package), per the card: `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_orchestrator.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`, `sleeves/griffith/feedlib/griffith.py`
- Named on the card as not in this repo: `desk/vendor/griffith/config.json` (the source desk's config; the card's parameters above are the recorded configuration).
- Rule lines referenced by the card: `docs/verify/griffith.md`

## Configuration

- Universe: SCOPE 550 US names (SPY, QQQ, IWM and sector ETFs excluded). Timeframe 1d; decision pre-open daily; delivery passes every 15 minutes in the regular session.
- Book $100,000; risk 0.5% of equity per order within a 3% strategy risk cap; order caps 35% of equity / 98% of buying power; limit armed 5 days.
- Bracket: -1.6 ATR stop / +2.8 ATR target, ATR(14) floored at 1.5% of price.

## Data inputs

Alpaca IEX raw daily bars of the SCOPE universe (IEX-only volume, unadjusted prices), the last 550 sessions, loaded once a session; Yahoo daily bars without keys (card).

## Install and run

1. Clone this repository (Test, dwj9ddyvf6-hub/Test).
2. The strategy runs inside the griffith sleeve package: `sleeves/griffith/griffith.py` driven through the vendored orchestrator/execution modules under `sleeves/griffith/vendor/griffith/`, with data from `sleeves/griffith/feedlib/griffith.py`. Supply the desk config values recorded in Configuration (the source `config.json` itself is not in this repo, per the card).
3. Feed the daily bars described in Data inputs; run the pre-open decision pass, then the 15-minute delivery passes.
4. Verify against the Verification section before treating the recreation as faithful.

## Verification

No dedicated test file for this sleeve was found in Test. Behavior checklist, from the algorithm section:

- A name failing any leader condition (e.g. under 253 sessions, more than 25% off the 52-week high, EMA 50 not rising) yields no plan; a name passing the leader filter but outside the resting bands or RSI 48-68 yields no plan.
- A qualifying name arms exactly one GTC limit at the decision close for 5 days, with stop = limit - 1.6 ATR and target = limit + 2.8 ATR (ATR floored at 1.5% of price).
- Order size equals 0.5% of equity divided by risk per share, never exceeding 35% of equity, 98% of buying power, or the remaining 3% strategy risk cap.
- A held name receives no new plan and no add; a plan whose ask is at or under its stop is dropped at delivery.
- No lifecycle exit (thesis break, time exit, breakeven, trailing) fires: the bracket is the only exit.
