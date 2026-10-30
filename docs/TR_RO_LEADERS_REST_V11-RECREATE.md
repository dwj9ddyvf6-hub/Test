# tr-ro-leaders-rest-v11: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Leaders Rest v1.1 on daily buy-greens", type mean reversion, family tensor_research, style "Pullback in a leader", universe "1,838-name genome roster", asset class US equities, timeframe 1d, creator "Griffith's Leaders Rest (LR_1_1_0_CORRECTED) on FolioTend's Deep Reset / Leaders Rest wrapper". Algorithm grade PARTIAL in the accounting, with gaps: entry, exit and sizing not recorded in the accounting's consulted sources. Those gaps are filled here from the Test strategy card in this repo (see Files).
- Test catalog entry `tr-ro-leaders-rest-v11` (`docs/CATALOG.json`): status live (1), card `strategies/tensor_research/tr-ro-leaders-rest-v11.md`, master-desk row `ro_leaders_rest_v11`.
- Alias: `ro_leaders_rest_v11`.

## What this strategy is

Each fresh daily Tensor buy-green that Leaders Rest calls a SETUP (a leader resting off its high) is bought with a GTC limit bracketed at -1.6 / +2.8 ATR.

## Full algorithm

From `strategies/tensor_research/tr-ro-leaders-rest-v11.md` (the card) and the code in Files, in evaluation order:

1. Candidates: names with a fresh daily buy-green (funds excluded), each run through Leaders Rest v1.1 on its daily history with SPY's.
2. Leader test: >= 253 sessions; price >= $10 or 20-day dollar volume >= $20M; within 25% of the 52-week high; EMA 50 rising over 10 sessions; 12-1 momentum above SPY's; price above EMA 50 (or above EMA 21 with EMA 50 rising); SPY not below a falling EMA 50, and SPY's 12-1 momentum not under -4% while SPY is under its EMA 200 or its EMA 50 is falling.
3. SETUP test: resting (3-12% under the 20-day high, or the last 15 days' range <= 60% of the prior 20 days' with 2-18% off the 52-week high) and RSI(14) 48-68.
4. Order: a GTC buy limit at the decision's close, armed 5 days; dropped when the name is held or the ask is at or under the stop.
5. Exit bracket: stop at the limit - 1.6 ATR, target at the limit + 2.8 ATR (ATR(14), at least 1.5% of price). No other exit is recorded on the card.
6. Notes on the card: the Doorway Deep Reset lens is computed beside each decision and never traded. The card also notes the Tensor engine and FolioTend research code are not published in this repo; the in-repo code in Files is what Test holds, and `desk/vendor/griffith/config.json` (named in the catalog code list) was not found in the Test tree searched for this package: that config is not in the record in Test.

## Files in this repo

- This doc: `docs/TR_RO_LEADERS_REST_V11-RECREATE.md`
- Strategy card: `strategies/tensor_research/tr-ro-leaders-rest-v11.md`
- Code (already in Test, master-desk paths): `sleeves/tensor_research/tensor_research.py`, `sleeves/griffith/griffith.py`, `sleeves/griffith/vendor/griffith/strategy_system.py`, `sleeves/griffith/vendor/griffith/strategy_execution.py`, `sleeves/tensor_research/feedlib/tensor_research.py`, `sleeves/tensor_research/feedlib/tensor_research.mjs`
- Rule lines: `docs/verify/tensor_research.md`
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`; catalog: `docs/CATALOG.json`
- Searched for code outside Test: Silicon, quant-research-backup and Midna trees were searched for leaders-rest code; no distinct original was found there. The code above in Test is the home used. The catalog-named `desk/vendor/griffith/config.json` was not located in any of those trees.

## Configuration

- Universe: 1,838-name genome roster. Timeframe: 1d. Asset class: US equities.
- Sizing: 0.5% of equity at risk / 1.6 ATR, within a 3% strategy risk cap less open and armed risk; per order <= 35% of equity and <= 98% of buying power.
- Order life: GTC limit armed 5 days. State: not in the record beyond the armed-order state.

## Data inputs

- Completed regular-session daily bars (2 years) of the roster and SPY, from Alpaca SIP with keys, else Yahoo; read by the pinned Tensor engine v698 and the vendored research sources (per the card).

## Install and run

1. Clone the Test repo.
2. Read `strategies/tensor_research/tr-ro-leaders-rest-v11.md` and `docs/verify/tensor_research.md`.
3. Open `sleeves/tensor_research/tensor_research.py` with `sleeves/griffith/griffith.py` and the vendored Griffith system/execution modules in Files.
4. Provide 2 years of completed daily bars for the roster and SPY (Alpaca SIP or Yahoo fallback) and the Tensor buy-green feed.
5. Supply the Griffith config that the catalog names (`desk/vendor/griffith/config.json`) from the original desk if available; it is not in Test, so a recreation must record its absence rather than inventing values.
6. Run daily after the close and verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in Test. Behaviour checklist:

- A name with fewer than 253 sessions, or more than 25% below its 52-week high, fails the Leader test.
- A Leader with RSI(14) outside 48-68 is not a SETUP.
- The buy limit is at the decision close, armed 5 days, and is dropped if the name becomes held or the ask is at or under the stop.
- Stop and target are exactly limit - 1.6 ATR and limit + 2.8 ATR, ATR floored at 1.5% of price.
- Position size respects the 0.5% risk / 1.6 ATR rule and the 3% strategy risk cap.
