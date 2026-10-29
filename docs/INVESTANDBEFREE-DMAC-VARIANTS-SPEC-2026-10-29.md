# INVESTANDBEFREE-DMAC VARIANTS — FROZEN FAMILY SPEC (2026-10-29)

Base sleeve: `investandbefree_dmac` per
INVESTANDBEFREE-DMAC-SPEC-2026-10-29.md (FROZEN). This doc freezes
four variants by owner order 2026-10-29. Each variant differs from
the base in EXACTLY ONE axis, named below; everything not named
stays exactly as the base: SPY and QQQ; Wilder plus exponential
MACD 12/26/9 on closes, closed bars only; alignment means both
MACDs on the same side of their own signals; dominance means the
slowest aligned timeframe; triggers are crossover or curl on the
last closed entry-timeframe bar; long premium only; 10% spread
gate; USD 2,000 premium budget with a 25% slice hard cap; exits
50% premium stop, dominant-alignment break (total alignment loss
counts as a break), +100% partial to a runner (qty 1 is a full
exit, fires once), runner out on an entry-timeframe MACD-E cross
against the position or at 5 DTE; one position per underlying.

Architecture: one parameterized pure core
(`sleeves/investandbefree_dmac.py`, `DmacParams` /
`PRIMARY_PARAMS` / `variant_params`); each variant is a thin
subclass module carrying exactly one parameter difference, plus
its own adapter pair, its own config row, its own $10,000 slice,
its own state file and its own live record. parked=false,
paper_only, live paper from install for all four.

Family judging rules (frozen):
- NO BACKTESTS for any variant. The live paper record is the
  test for every variant, exactly as for the base.
- No variant is judged on fewer than 30 of its own trades.
- Performance yardstick: percent gain compared to SPY and QQQ
  over the same window. The paper account's dollar size is
  arbitrary by design; the percentage versus the two benchmarks
  is the measure that matters.
- Edge for every variant: UNPROVEN until its own live record
  says otherwise.

Provenance labels: **extracted** (stated in public material
about the vendor method), **recreated** (public record silent;
a default frozen here so the rule set is executable),
**deviation** (a named difference from the base or from the
vendor form, with its reasoning stated).

## V1 investandbefree_dmac_intraday

Axis changed: timeframe stack and session shape. This is the
vendor's ORIGINAL intraday form: the documented method began
as a 15/30-minute day-trading system; the base sleeve is its
long-term variant. **extracted** that the method began in this
form; the exact desk parameters below are **recreated**.

- Stack: 15-minute, 30-minute, 4H, aggregated in-core from
  5-minute bars, the finest intraday bars the desk producers
  serve for BOTH SPY and QQQ with a long history (warm product:
  SPY/QQQ 5Min, 60 calendar days; producer keys bars:SPY:5Min
  added at this install, bars:QQQ:5Min already present; the
  desk serves no native 15Min/30Min bars for SPY and no
  bars:*:30Min key at all). Aggregation is RTH-anchored
  (buckets start at 09:30 ET), complete buckets only, closed
  bars only: a 15-minute bucket holds exactly 3 consecutive
  closed 5-minute bars, a 30-minute bucket exactly 6, a 4H
  bucket exactly 48 (09:30 to 13:30 ET; the remainder of the
  session never completes a second 4H bucket and is never
  emitted). **recreated** operational form.
- Entry timeframe: 30-minute. Dominance: slowest aligned
  (4H, then 30-minute, then 15-minute); a trade requires the
  dominant direction to equal the 30-minute direction.
- Triggers: crossover or curl on the last closed 30-minute
  bar. **recreated** (the base trigger forms, moved timeframe).
- Expiry: nearest listed expiry at least 5 calendar days out.
  **recreated**.
- flat_by_close TRUE: every position exits by 15:55 ET,
  runner included (config flat_by_close=true with
  flatten_time_et 15:55, and the sleeve itself emits a full
  exit at or after 15:55 ET and takes no new entry at or after
  15:55 ET; the +100% partial may still fire intraday; no
  overnight runners). **recreated** flat time.
- Strike: ATM, as the base. Spread gate, budget, cap, premium
  stop: as the base. Cadence 300 seconds. Session rth.

## V2 investandbefree_dmac_dailyonly

Axis changed: stack composition. The 4H layer is REMOVED: the
stack is weekly plus daily only. Dominance: weekly when
aligned, else daily; a trade requires the dominant direction
to equal the daily direction (unchanged meaning). Its adapter
does not even request 1Hour bars. Everything else is
base-identical. Purpose: isolate whether the 4H layer adds or
subtracts. All parameters **extracted/recreated** exactly as
the base labels them; the removal itself is a desk
**deviation** run as a controlled variant, not a claim about
the vendor method.

## V3 investandbefree_dmac_deep

Axis changed: contract construction.
- Strike: the nearest strike at least 2% in the money: calls
  take the highest strike at or below 0.98 times spot; puts
  take the lowest strike at or above 1.02 times spot. If no
  such strike exists at the chosen expiry, no trade.
  **recreated**.
- Expiry: nearest listed expiry at least 45 calendar days
  out. **recreated**.
Everything else base-identical (same budget, cap, spread gate,
exits, stack, triggers). Purpose: isolate the delta/theta
profile of the construction.

## V4 investandbefree_dmac_premacd

Axis changed: the exit signals' data series. This variant
tests the hypothesis (attributed in the commission to Paul
@Radolfi_Clan, 2026-10-29) that the method runs MACD on the
OPTION's premium rather than the underlying.

- Entries stay base-identical (underlying stack). **deviation**,
  with its reasoning named here: a pre-entry premium series for
  a not-yet-held contract is discontinuous across strike rolls
  and no honest series exists, so premium-MACD entries cannot
  be formed honestly; only exits are tested on premium.
- Once in a position, the sleeve accrues the held contract's
  mid price once per cycle into its own state (timestamped
  samples, at the sleeve's configured hourly cadence). Samples
  persist across restarts in the sleeve state file; a contract
  roll or a new position resets the series.
- After at least 40 accrued samples, premium MACD-E (12/26/9,
  exponential, on the accrued premium closes) governs two
  exits INSTEAD of their underlying-based forms: a premium
  MACD-E cross against the position direction replaces both
  the dominant-alignment-break exit and the runner cross exit.
- Before 40 samples, the base exits apply. **deviation** named
  here as the warmup deviation.
- The 50% premium stop, +100% partial, 5-DTE runner bound and
  the daily-layer structure are unchanged.

## Roster

329 to 333 with exactly four additions:
investandbefree_dmac_intraday, investandbefree_dmac_dailyonly,
investandbefree_dmac_deep, investandbefree_dmac_premacd. Each:
slice capital_usd 10000 / cash_usd 10000, session rth,
parked=false, paper_only; cadence 3600 for dailyonly, deep and
premacd, 300 for intraday; flat_by_close true ONLY for
intraday (flatten_time_et 15:55).
