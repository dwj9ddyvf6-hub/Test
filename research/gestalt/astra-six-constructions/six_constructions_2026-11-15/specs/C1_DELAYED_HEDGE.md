# C1 — buy panic; hedge reassurance

**Evidence:** exploratory historical prototype. **Build entry:** `run_historical.py`. **Minimal timing function:** `reference.delayed_hedge_fractions`. **Originals:** `original/two_clocks.py`, its tests, designs, initial/amended results, event paths and fractional comparison.

## Economic object

Hold common-market rebound first, then change exposure toward residual repair. Potential entry compensation is liquidity supplied to urgent sellers. The alternative explanation is ordinary market exposure. A short hedge is a separate risk-transfer cost, not a free component of the entry thesis. Target incremental net outcome or portfolio utility versus a feasible fixed-exposure policy.

## Exact frozen input and entry convention

Inputs are four-hour spot bars for BTC and six surviving altcoins, BTC linear perpetual bars, archived funding, and the preserved parent event list. Returns for beta and bar signals are close/open minus one. Beta is rolling covariance with BTC divided by rolling BTC variance over 180 bars, shifted one bar. Residual score is current residual minus its prior 180-bar average, divided by prior root-mean-square residual. It is not a three-standard-deviation normal test.

The parent policy `CL-03226` selects negative residual score below −3, systemic market magnitude at least 1.5 lagged BTC RMS, long asset, 18-bar holding period. Its selector suppresses overlapping entries per symbol. The local prototype reads that already-selected list, then removes nonnegative BTC signal bars. This order matters: a removed positive-BTC event may have blocked a later event in the parent selection. Six-hour/horizon redesign or filtering-before-spacing is a new version.

Both tested horizons (6 and 18 bars, 24 and 72 hours) use that same parent event list. All required bar and funding timestamps must be present. The funding history must match the complete expected eight-hour clock and recorded interval. Unavailable intervals are excluded and listed, not changed to zero funding. The prototype excludes six event/horizon rows for incomplete market/funding clocks.

## State transitions

`WAITING -> LONG_UNHEDGED` at the next bar open after the selected signal. At each completed post-entry BTC bar, increment a positive-return streak when close > open; reset it otherwise. When the streak first reaches two, schedule `LONG_HEDGED` for the next bar open. Once hedged, stay hedged until the original endpoint. A trigger on the final bar does not create a hedge after the trade has ended. Without a trigger, exit unhedged.

At the endpoint, close the asset and any remaining hedge. The source uses the last held bar's close for terminal prices. It does not infer an intrabar stop, limit fill, exchange liquidation, or continuous hedge adjustment. Its terminal funding mark convention is a proxy, documented below.

## Sizing and cash accounting

Normalize initial asset notional to $1. Asset units are 1 / asset entry price. Hedge units are beta / original perpetual entry price multiplied by the policy's active fraction. Thus the later activated hedge is not reset to beta dollars at the later market price. Price P&L is the sum of short units times the negative price change over held intervals.

Charge 0.001 times every absolute change in hedge units times its execution price, including the exit. Charge the asset entry and exit at the same per-turnover rate. Positive funding pays a short; when a quantity change coincides with a funding timestamp, take the minimum cash flow under the before/after quantities. Include zero as the alternate boundary quantity at opening and closing. Bar opens proxy funding marks; terminal funding uses the last close. This addresses one ordering ambiguity, not all execution risk.

No leverage or margin-account return is computed. Positive beta is observed in this retained sample; the general loader does not establish future beta behavior. A new universe needs an explicit policy for unstable or negative beta.

## Preserved comparisons

The full family is in `original/design.json`: unhedged, fixed beta, first-positive/two-positive/buy-flow/repair/time-based hedge release, repeated market switching, and four inverse hedge-addition policies. Keep all 24 policy/horizon outputs. The four inverse policies were added after inspecting the initial eight. Seven-day calendar blocks and 500 bootstrap draws give exploratory intervals only. Period names containing `audit` or `replay` do not restore an untouched holdout.

Reference 72-hour means are in the report. Retain negative/tail outcomes, asset/date clustering, source availability, and the half-hedge comparator. A previously seen sample cannot become confirmatory by renaming it.

## Build tasks and acceptance cases

1. Restore and hash-check all raw inputs. Reproduce full `results.json` and `event_paths.json` within 1e-12 numerical tolerance.
2. Verify no future bar changes earlier exposure; current bar return cannot affect that bar's entry hedge; zeros break the streak; hedge activation is one-way.
3. Verify constant hedge telescopes, actual turnover is charged, and adverse funding boundary ordering is preserved.
4. For new research, implement portfolio cash/margin, quote sides, slippage/impact, and contemporaneous historical membership. Add a defined clock for simultaneous events and constrained capital.
5. Freeze a fresh test menu against no hedge, fixed fractions, and fixed/random activation clocks drawn independently of outcomes. Evaluate matched-capital results and risk, not only mean trade P&L.

**Unresolved:** fills, funding marks, liquidation, historical survivor bias, capacity, venue access, prospective effect, independent confirmation. These are data/evidence gaps, not reasons to erase the construction.
