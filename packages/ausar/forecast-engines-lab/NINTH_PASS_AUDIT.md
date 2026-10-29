# Ninth Pass — Score Semantics and Forecast-Target Alignment

## Finding

The previous output contract turned every signed model into `UP`, `DOWN`, or `NEUTRAL` using a fixed ±0.10 deadband. Those values are scores with different constructions and no shared calibrated scale. The risk scorers likewise used 0.40/0.60 labels that looked like empirical risk bands even though each score is a hand-set logit passed through a sigmoid. The displayed labels therefore claimed more than the model outputs established.

This pass sharpens the forecast/target boundary without changing the 30 signal transforms or implying that any has predictive edge:

- Signed models now report `POSITIVE_SCORE`, `NEGATIVE_SCORE`, or `ZERO_SCORE`. There is no shared magnitude deadband. The label means orientation in that engine's declared target coordinate, not a calibrated return estimate or a universal price call.
- Heuristic risk models report `RISK_RANK_ONLY`. Their continuous sigmoid output remains available for ranking; the output does not invent a high/low threshold without held-out outcome evidence.
- Continuous point forecasts report `NOT_DIRECTIONAL`.
- Every record carries `direction_semantics`; the model version is now `0.8.0-hypothesis` and forecast schema `1.6`.
- Collision diagnostics now partition by direction semantics. Legacy records lacking the field retain `legacy_direction_label` and old direction strings remain readable. Score-orientation entropy is explicitly not accuracy.
- The README's 30 target descriptions were reconciled to the primary label contracts. FE15 remains a scenario-only sensitivity and cannot be scored as an unconditional realized-return forecast.

## Per-engine output audit

| Engine | Emitted value | Score-orientation semantics | Primary outcome kept separate |
|---|---|---|---|
| FE01 | signed score | Higher benchmark-adjusted return coordinate | Fixed 5/10/20-session benchmark-adjusted return |
| FE02 | signed score | Higher residual-spread-return coordinate | Fixed 1/3/5-session residual spread return |
| FE03 | signed score | Higher underlying-return coordinate after the frozen breakout reference | Fixed 1/3/5-session underlying return |
| FE04 | signed score | More gap-residual continuation than fade | Declared open-reference residual return at 30-minute/close/next-close endpoint |
| FE05 | signed score | Higher index return relative to the fixed benchmark | Fixed 1/3/5-session relative return |
| FE06 | signed score | Higher sector return relative to the benchmark | Fixed 5/10/20-session relative return |
| FE07 | signed score | Higher follower residual return at the selected lag | One predeclared lag endpoint |
| FE08 | variance | No directional interpretation | Fixed-window realized variance |
| FE09 | heuristic risk rank | Rank only; no high/low direction label | Binary absolute-return barrier event |
| FE10 | heuristic risk rank | Rank only; no high/low direction label | Binary predeclared regime transition |
| FE11 | signed score | Higher close-to-next-open return | Venue/session-specific close-to-next-open return |
| FE12 | heuristic risk rank | Rank only; no high/low direction label | Binary depth/spread impairment event |
| FE13 | signed score | Higher midquote-return coordinate after flow | Fixed elapsed-time midquote return |
| FE14 | heuristic risk rank | Rank only; no high/low direction label | Binary predeclared left-tail barrier event |
| FE15 | signed scenario score | Sensitivity sign under caller-specified spot path only | No unconditional realized-outcome label; scenario-only |
| FE16 | signed score | Higher conditional underlying residual-return coordinate | Fixed endpoint after classified flow event |
| FE17 | absolute-return point estimate | Not directional; output estimates magnitude | Absolute release-to-next-session-close return |
| FE18 | signed score | Higher sector-residual return coordinate | Fixed 5/10/20-session return after executable open |
| FE19 | signed score | Higher issuer-residual return coordinate | Fixed 20/40/60-session return from revision availability |
| FE20 | signed score | Higher standardized next-period fundamental surprise | Frozen-consensus next-period surprise z-score |
| FE21 | signed score | Higher cash-conversion-change coordinate | Change to next comparable filing |
| FE22 | signed score | Positive parser-normalized disclosure-delta coordinate | Same-section/type delta at next comparable filing |
| FE23 | signed score | Higher issuer-residual return coordinate | Fixed 20/40/60-session return from filing availability |
| FE24 | heuristic risk rank | Rank only; no high/low direction label | Binary crowded-position unwind event |
| FE25 | signed score | Higher issuer-residual return coordinate | Fixed return window from executed-buyback report availability |
| FE26 | signed score | Higher constituent return relative to frozen index | Return through effective-date close |
| FE27 | signed score | Higher return coordinate for the declared cross-asset instrument | 30-minute post-release return |
| FE28 | heuristic risk rank | Rank only; no high/low direction label | Binary stress transition by selected quarter end |
| FE29 | signed score | Higher commodity excess-return coordinate | Fixed 1/4/8-week excess return |
| FE30 | heuristic risk rank | Rank only; no high/low direction label | Binary venue-specific liquidation/depth event |

The orientation is generated by the starter score formulas, not by fitted coefficients. For FE20–22, a positive coordinate is meaningful only after the associated surprise/change transform is frozen in the label transform. For FE15, the sign remains conditional on the caller's spot path and dealer-gamma assumption. For FE09/10/12/14/24/28/30, rank ordering is available for research; probability calibration and operational thresholds remain unestablished.

## Next falsification gate

For every engine, freeze the target window, transform, and units before outcome access; then evaluate the score against the matching primary label and the card's named price-aware baseline. Keep point forecasts, score rankings, scenarios, and realized outcomes in separate columns. Any later fit must be point-in-time, purged for overlapping horizons, time-blocked, cost-aware where execution is claimed, and counted in the full multiple-testing family. This pass changes contract semantics and descriptions only; it does not fit, backtest, connect data, or authorize orders.
