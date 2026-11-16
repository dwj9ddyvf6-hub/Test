# C3 — repair, then rotate

**Evidence:** proposed equity research design. **Reference:** `repair_fraction` and `rotation_increment`. Archived trade-selection and SPY-rotation results are context, not a replay of this rule.

## Economic object

Transfer a fixed allocation from an asset bought for temporary dislocation into a contemporaneously defined leader when the measured dislocation closes. Reversal and momentum have sequential roles. The rival explanation is simply market exposure or selecting a fortunate exit. Evaluate the incremental use of the same capital after the same decision time.

## Inputs and parameter provenance

Use immutable security IDs, historical universe membership, adjusted signal prices with an explicit executable-price mapping, corporate actions, delistings, benchmark total returns, quote costs, and timestamps. Estimate beta from a window ending before entry; the window length is a future research choice. Fix the initial dislocation definition before observing its recovery.

One proposed equity definition uses log-price returns: negative initial market-adjusted shock magnitude d>0; cumulative post-entry stock log return minus fixed beta times benchmark log return x; repair fraction rho=x/d. A crossing of rho>=1 is an interpretable **proposed** transition because the original measured shock has repaired. It is not a verified threshold or a claim of fair value. This log-return definition is distinct from C1's simple-return prototype; do not mix their fields.

Leadership selection uses only data available at the repair decision. The lookback, basket weighting, membership, rebalance, and risk normalization remain explicit unset research parameters. Do not reconstruct a leadership basket from future realized winners.

## State machine and comparison clock

`WAITING -> DISLOCATION_POSITION` at the chosen entry; update repair only when input observations become available. On a qualifying completed observation, schedule a comparison at the next feasible execution time. Select hold, cash, or transfer using the prescribed rule. A transfer becomes `LEADERSHIP_POSITION` only after accounting for closing the original asset and acquiring the replacement. Track interim cash, partial execution and constraints. End all arms at the original experiment's common terminal time.

The minimum version permits one transfer per episode; repeated rotations are a different policy family. Existing gains are embedded in capital V at transfer and appear in every comparator. Do not compare two independently normalized trades and call their sum a funded strategy.

## Exact comparison

`additional terminal wealth = V*(replacement subsequent return - original subsequent return) - incremental transfer cost`.

All quantities share a terminal cash-flow convention. For cash, use its attainable return. For a basket, include its own rebalancing and financing. At V=108, returns 4% versus 1%, and cost 0.40, the extra wealth is 2.84; equal subsequent returns lose exactly the transfer cost. These are synthetic acceptance fixtures.

## Experimental arms and falsifiers

Retain original asset, move to cash at repair, move to fixed-definition leadership at repair, own leadership from initial entry, and switch at a fixed elapsed time. Use the same event stream and portfolio capital. Compare post-repair paired differences and whole-book outcomes, including concurrent positions and idle cash. Preserve all attempted repair definitions and leadership variants.

If leadership-from-start or a simple fixed-time transfer explains the gain, repair has not established incremental information. If a liquidity or market exposure tilt explains it, identify that contribution. Costs exceeding the relative opportunity weaken this construction at the tested size; different sizes may be a new explicit experiment.

## Missing build inputs

Complete original equity panel and executable quote costs; point-in-time leaders; actual risk/capital objective; beta/repair/entry/horizon definitions; allocation and overlap rules. No historical returns for this policy may be inferred from the illustrative reference calculation.
