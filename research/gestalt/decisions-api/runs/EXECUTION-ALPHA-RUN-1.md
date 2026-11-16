# EXECUTION ALPHA, RUN 1 (Sat 2026-11-14)

Invention 8 (INVENTION-BRAINSTORM.md). Question: does a
slippage-signed view of the fleet's own fills re-rank sleeves on an
axis invisible to signal grading? Data: the full fill ledger
(8,928 fills, 2026-10-27 to 2026-11-13) and warm daily bars.
Tool: tools/execution_alpha.py. Numbers: runs/execution_alpha_v1.json.

## The exhaust's shape, stated first because it bounds everything

The ledger window begins mid-book. Of 1,525 close fills, 1,509
settle positions opened before 2026-10-27 and cannot be paired
honestly. Only 18 round trips open and close inside the window
across 9 sleeves. Any re-ranking built on 18 trips would be
theatre, and none is claimed. The large-n exhaust is the markouts:
5,024 labeled entry fills and 1,413 close fills with a next-session
bar.

## Headline results

1. **The execution axis is real and separates sleeves far beyond
   noise.** Mean +1-session entry markout by sleeve (n >= 30):
   aster_tensor_d20_tensor +8.50% (n=282), aster_tensor_d20_pv
   +7.87% (n=173), s_mn_hourly_1w +7.49% (n=184), s_mn_macd +1.64%
   (n=175), aster_trader_donchian55 +1.26% (n=42) at the top;
   tensor_swing -1.09% (n=3,633) and red_day_reversal -1.36%
   (n=164) at the bottom. A spread of ten points between sleeve
   populations at these sample sizes is not sampling error. The
   invention's falsifier (slippage-signed rankings do not differ
   from raw rankings beyond noise) is NOT triggered: the axis
   carries sleeve-specific structure no signal grade has ever
   shown.
2. **Interpretation discipline, applied to our own result.** A
   1-session markout is not pure execution quality. tensor_swing's
   3,633 labeled opens are all buy_to_open dip entries; a dip
   buyer's first session is expected to be underwater while the
   knife falls, which is the signal's shape, not its fills' fault.
   The large positive markouts on the d20 and hourly families
   likewise mix entry-timing (the signal fires into strength) with
   fill quality. The registered follow-up is horizon-matched
   markouts: each sleeve's entries graded at its own median
   holding horizon, where signal shape and execution separate.
3. **Exits leak at the 1-session horizon.** Mean exit markout
   -0.237% (n=1,413): after our exits, price kept moving the way
   that made exiting wrong by about 24bp per exit. Small per
   trade, relentless in aggregate, and invisible until measured.
4. **The trip decomposition, for the record and no more.** On the
   18 in-window trips: realized +$8,398 versus bar-path +$18,845,
   an execution component of -$10,447, of which -$10,046 is ONE
   aster_trader_donchian55 trip whose bar-path twin (+$16,034) is
   not credible against its fill (+$5,988): flagged as a suspect
   artifact (raw fill prices versus bar prices on a name with a
   corporate-action or scale break in window), named here for
   audit, excluded from every headline above. The remaining 17
   trips show a consistent small negative execution component
   (roughly -$20 to -$150 per trip), in line with the exit leak.

## Verdict and forward registration

STATUS: MEASURED, NOT FLAT. The execution axis exists, separates
sleeves, and has produced two estate facts (the dip-buyer markout
signature; the 24bp exit leak) that no prior grading surface
carried. Forward grading registered: nightly markout accrual joins
the harvester population from Mon 2026-11-16; horizon-matched
markouts are the run-2 build; the re-ranking claim itself is
graded once the fleet flip gives the ledger complete round trips
(the attribution ledger's unblocker, same date). If, at that
point, slippage-signed expectancy ranks sleeves no differently
than raw expectancy beyond noise, the invention's falsifier binds
and it dies in the open.
