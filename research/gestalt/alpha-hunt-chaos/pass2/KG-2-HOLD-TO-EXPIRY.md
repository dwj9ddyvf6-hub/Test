# KG-2: HOLD-TO-EXPIRY RESOLVER VARIANT

Built 2026-11-15 under the Keep-Going wave (method ledger owed
application #6: when a dimension has zero observations, build
the cheapest instrument that creates them). The instrument is
`~/workspace/midna-book/tools/shadow_resolver_hold.py`; its
records stand in `~/workspace/midna-book/ghost-book-hold-resolutions.jsonl`
(21 records, appended 2026-11-15; originals never edited).

## POTENTIAL EDGE FOUND

The hold dimension now has an instrument and a first read.
The read, stated with its limit in the same breath: **0 of 21
fires are settleable today** (20 expire 2026-11-27, TTMI
expires 2026-12-18; neither session has printed), so every
number below on the hold basis is a MARK at the last printed
close (2026-11-13), not a settlement. The settlement read
exists only after the expiries print, and the deciding rerun
is named at the end of this section.

### The per-fire table (first-touch grade beside hold mark)

All values per contract. Mark R is the hold-basis mark on the
selector's shared risk denominator; it is not a realized R.
"To long strike" is how far the 2026-11-13 close sits below
the spread's long strike: the rise needed before the hold is
worth anything at all at expiry.

| Symbol | Viable | Entry R | First-touch | FT R | FT P&L | 11-13 close | Hold value | Mark R | Mark P&L | To long strike | Expiry |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NBIS | yes | 9.511 | STOPPED_OUT | -1.000 | -70.50 | 115.88 | 0.0 | -1.000 | -70.50 | +35.9% | 2026-11-27 |
| LITE | yes | 1.534 | STOPPED_OUT | -1.000 | -1015.00 | 596.62 | 0.0 | -1.000 | -1015.00 | +10.6% | 2026-11-27 |
| SOXL | yes | 1.769 | STOPPED_OUT | -1.000 | -162.50 | 58.32 | 0.0 | -1.000 | -162.50 | +16.6% | 2026-11-27 |
| AAOI | yes | 1.832 | STOPPED_OUT | -1.000 | -92.50 | 49.89 | 0.0 | -1.000 | -92.50 | +14.3% | 2026-11-27 |
| WDC | no | 0.889 | STOPPED_OUT | -1.000 | -302.50 | 295.65 | 0.0 | -1.000 | -302.50 | +7.4% | 2026-11-27 |
| IREN | yes | 1.866 | STOPPED_OUT | -1.000 | -36.00 | 18.17 | 0.0 | -1.000 | -36.00 | +18.3% | 2026-11-27 |
| AXTI | yes | 2.172 | STOPPED_OUT | -1.000 | -72.50 | 41.84 | 0.0 | -1.000 | -72.50 | +14.7% | 2026-11-27 |
| ALAB | no | 0.728 | STOPPED_OUT | -1.000 | -215.00 | 221.83 | 0.0 | -1.000 | -215.00 | +7.1% | 2026-11-27 |
| CRDO | yes | 1.053 | STOPPED_OUT | -1.000 | -310.00 | 131.51 | 0.0 | -1.000 | -310.00 | +9.5% | 2026-11-27 |
| FCEL | yes | 1.109 | STOPPED_OUT | -1.000 | -27.50 | 9.68 | 0.0 | -1.000 | -27.50 | +13.6% | 2026-11-27 |
| HIVE | no | -1.000 | STOPPED_OUT | -1.000 | -2.50 | 1.57 | 0.0 | -1.000 | -2.50 | +27.4% | 2026-11-27 |
| SNDK | yes | 1.872 | STOPPED_OUT | -1.000 | -1115.00 | 885.01 | 0.0 | -1.000 | -1115.00 | +12.7% | 2026-11-27 |
| TSEM | no | 0.821 | STOPPED_OUT | -1.000 | -190.00 | 146.89 | 0.0 | -1.000 | -190.00 | +10.6% | 2026-11-27 |
| ARM | no | 0.999 | STOPPED_OUT | -1.000 | -182.50 | 190.53 | 0.0 | -1.000 | -182.50 | +8.9% | 2026-11-27 |
| KEEL | no | -1.000 | STOPPED_OUT | -1.000 | -1.50 | 1.86 | 0.0 | -1.000 | -1.50 | +34.4% | 2026-11-27 |
| MU | yes | 1.311 | STOPPED_OUT | -1.000 | -912.50 | 778.31 | 0.0 | -1.000 | -912.50 | +5.4% | 2026-11-27 |
| CLS | no | 0.184 | TARGET_HIT | +1.1065 | +343.00 | 240.34 | 0.0 | -1.000 | -310.00 | +3.0% | 2026-11-27 |
| TTMI | no | -1.000 | STOPPED_OUT | -1.000 | -125.00 | 74.08 | 0.0 | -1.000 | -125.00 | +14.7% | 2026-12-18 |
| CVNA | yes | 1.217 | STOPPED_OUT | -1.000 | -60.00 | 72.37 | 0.0 | -1.000 | -60.00 | +2.3% | 2026-11-27 |
| VRT | no | 0.726 | STOPPED_OUT | -1.000 | -312.50 | 202.07 | 0.0 | -1.000 | -312.50 | +3.9% | 2026-11-27 |
| USAR | no | -1.000 | STOPPED_OUT | -1.000 | -13.00 | 8.16 | 0.0 | -1.000 | -13.00 | +10.3% | 2026-11-27 |

Summed P&L per contract across the 21: first-touch realized
-$4,875.50; hold-basis marked -$5,528.50. The entire $653.00
difference is one fire (CLS, below).

### The viability-split read

The question this variant was built to answer: does the
entry-viability split (selector R >= 1.0, 11 fires, vs sub-1.0,
10 fires) separate on the hold-to-expiry basis where it did
not separate on first-touch (viable mean -1.000R, sub-1.0 mean
-0.789R, the gap carried entirely by the one target hit)?

- **On settlements: untested, and untestable today.** 0 of 21
  settled; both expiries are future sessions. No honest
  settlement read exists before 2026-11-27.
- **On the provisional mark basis at 2026-11-13: no
  separation.** Every underlying closed below its long strike,
  so all 21 marks sit at the floor: viable 11 mean mark R
  -1.000, sub-1.0 10 mean mark R -1.000. A split cannot
  separate while every observation is at the floor; separation
  on this basis, if it exists, appears only as the paths to
  expiry differentiate.
- **The deciding check is dated, not open-ended:** rerun
  `tools/shadow_resolver_hold.py ghost` after the 2026-11-27
  session prints (settles 20 fires) and after 2026-12-18
  (settles TTMI). The tool is idempotent; the rerun appends
  settlements beside these marks and the split read runs on
  realized R, the basis the question was asked on.

### What the first marks do establish

1. **The stops, on this sample, have so far neither saved nor
   cost anything against holding.** All 20 first-touch
   stop-outs exited at intrinsic value 0.0: the first close
   through each registered stop (0.3 to 2 percent under entry)
   was already below the spread's long strike, so the stop
   exit and the hold floor coincide at -1.0R on 20 of 21 fires
   at the 2026-11-13 mark. The live variable the first-touch
   grading could not see is not the stop; it is the remaining
   path: 9 sessions stand between the mark and the 2026-11-27
   expiry, and four names sit within one strong move of
   nonzero settlement value (CVNA +2.3% to its long strike,
   CLS +3.0%, VRT +3.9%, MU +5.4%).
2. **The one separation between the bases so far is CLS, and
   it runs against holding.** First-touch banked +1.1065R
   (+$343.00/ct) at the target touch; the hold mark stands at
   -1.0R (-$310.00/ct) after CLS fell back below its long
   strike. Gap: 2.1065R, $653.00 per contract, which is the
   whole difference between the two bases' summed P&L. On the
   only fire where the path offered an exit, the path basis
   took it and the hold basis, so far, gave it all back.
3. **The mark floor is a statement about the entry session,
   not about expiry.** All 21 fires were priced off one
   session's tape (2026-11-12, a complex-wide flush); a
   settlement read on 2026-11-27 grades the selector's
   expressions over their full registered life for the first
   time. That sample, not today's marks, is the one the
   viability question gets answered on.

## METHOD

- **Shared basis, imported not copied.** The variant imports
  `value_fn_for`, `expression_key`, the JSONL conventions, the
  data-source string, and the evidence class from
  `shadow_resolver.py`. Entry R and realized R are the same
  units on both bases by construction. A test pins this:
  where neither stop nor target is touched, the variant's
  settlement equals the original's EXPIRED grade to the cent
  (value, R, P&L, and the risk denominator all equal).
- **The semantic difference is exactly one move.** First-touch
  walks the path and exits at the first close through the
  target or the stop; the variant ignores both levels and
  settles at the expiry session's close. Tests pin both
  directions of divergence: a dip through the stop that
  recovers settles positive on the hold basis while stopping
  out at -1.0R on first-touch, and a touch of the target that
  fades settles at the faded expiry value while first-touch
  banks the touch.
- **Marks are not settlements.** An unprinted expiry produces
  a HOLD_OPEN mark record (type `expression_hold_mark`,
  realized R null, the unprinted expiry named in the record),
  the original resolver's OPEN-mark convention carried onto
  the hold basis. The comparison read above keeps the two
  apart throughout.
- **Records.** One hold record per fire in
  `ghost-book-hold-resolutions.jsonl`, each carrying the
  first-touch grade beside the hold grade by the shared
  expression key, the full per-session intrinsic path, and
  `resolution_basis: hold-to-expiry`. Reruns append nothing
  when nothing changed (verified: second run 0 new, 21
  skipped).
- **Tests.** `tools/test_shadow_resolver_hold.py`, 11 tests in
  the original suite's style (fake bars providers, no
  network). Fail direction verified against a stub at
  /tmp/hold-stub: 10 failed there, 11 pass on the built
  variant; the single stub pass is the basis-identity test,
  which exercises only the original's imported math. The
  original suite still passes 13 of 13, untouched.
- **BUGLOG.** Entry HOLD-TO-EXPIRY-RESOLVER-VARIANT-20261115
  in `~/workspace/midna-book/BUGLOG_2026-11-15.md`, closing
  the named limit in EXPRESSION-RESOLVER-20261115.

STATUS: PARTIAL — the variant is built, tested (11 of 11,
fail direction proven), and run: 21 of 21 fires carry a
hold-basis record beside their first-touch grade, and the
mark-basis viability read is printed above (no separation,
both groups at the -1.000 floor). The PARTIAL names the one
remainder no build can close today: the settlement-basis
viability read, which exists only after the 2026-11-27 and
2026-12-18 sessions print, by the dated rerun named above.
