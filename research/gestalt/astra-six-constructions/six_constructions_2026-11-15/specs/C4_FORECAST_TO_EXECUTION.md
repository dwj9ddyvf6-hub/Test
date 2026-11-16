# C4 — spend a volatility forecast on execution

**Evidence:** proposed execution experiment. **Reference:** `implementation_shortfall`; this is accounting, not a fill simulator.

## Transfer and estimand

Use a movement forecast to choose urgency, passive pricing, staging or waiting for an independently justified exposure. Potential gains come from better price, less impact, appropriate patience or avoided adverse selection. A paid option can be too expensive even when the forecast of movement is correct; execution gives the forecast a different decision target.

The principal estimand is improvement over a feasible baseline across **all original intents**, with the same quantity/deadline/mandate. Filled-trade averages alone are invalid for this claim. A more profitable overall strategy may result from preserved implementation surplus without a new directional forecasting edge.

## Input ledger

An intent must precede routing and record asset, side, quantity, decision benchmark, thesis ID, deadline, mandatory versus discretionary completion, allowed order types, capital and venue constraints. Keep quote event and receipt clocks, depth, tick size, order acknowledgments, fills, partial fills, cancellations, fees, and every unfilled or rejected order. Features need available-at timestamps and forecast versions.

Do not use final bar high/low as if a limit order had a known queue fill. A resting order filling can select adverse information. Model fill probability and outcome conditional on each fill, jointly with no-fill opportunity cost.

## State and action specification

States: `INTENT_RECORDED -> ROUTE_DECIDED -> ORDER_PENDING/RESTING/PARTIALLY_FILLED -> COMPLETED/EXPIRED/CANCELED`, with unresolved acknowledgments kept explicit. At any time, multiple pending or partially filled orders still consume the possible exposure budget. A pending cancel is not a completed cancel.

The candidate menu may contain marketable execution, a configured passive limit, a configured staged schedule, wait, and no-order if discretionary. Limits, durations and slices are explicit candidate parameters. No generic forecast-volatility threshold or timer is specified as optimal. The original investment deadline constrains this menu.

## Accounting and experiment

For buy quantity Q, decision price P0, fills qj at Pj, and deadline price PT:

`shortfall = sum(qj*(Pj-P0)) + (Q-sum(qj))*(PT-P0) + fees`.

Reverse price signs for sells. If mandatory completion is simulated, use attainable completion prices instead of an ideal deadline mark. For discretionary entry, also report actual terminal wealth; treating no order as a zero-cost winner can ignore forgone investment value.

The synthetic 100-share intent at 100 with 60 filled at 99.98 and deadline 101 has shortfall 38.80, despite cheap fills; crossing the full quantity at 100.02 costs 2.00 before fees. These fixtures verify that no-fill branches matter.

Compare a baseline router using spread/depth/time-of-day/ordinary volatility and the original directional thesis with an augmented router that adds the proposed magnitude forecast. Match learning budget and action menu. Historical book replay is a model; paper shadow policies do not reveal true counterfactual fills. A future separately authorized randomized routing study needs logged assignment probabilities and supported action sets. No execution is authorized here.

## Falsifiers and missing inputs

The claim weakens if improvement disappears after missed fills, markouts, queue priority, latency, impact, or realistic completion costs. It also weakens if an ordinary volatility/spread router achieves the same result. Missing: order-level data, calibrated fill model, forecast-specific incremental information, approved urgency/completion objectives, and prospective capture evidence. Avoid turning one unsuccessful option expression into proof that this router must succeed.
