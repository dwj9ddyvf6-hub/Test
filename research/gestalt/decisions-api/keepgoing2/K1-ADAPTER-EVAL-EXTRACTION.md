# K1: ADAPTER_EVAL EXTRACTION, CORPUS V2 (KEEP GOING 2, 2026-11-14 night)

Built by keepgoing2/k1_census.py and keepgoing2/k1_extract.py.
Corpus: keepgoing2/adapter_eval_corpus_v2.jsonl, 120 lines, one per
deduped cell. Stats: keepgoing2/k1_stats.json and k1_census.json.

## The census, and the correction it forces

The Continuation's open row said the estate's paired records live
in adapter_eval journal shapes. The census proves that is true of
exactly one shape and false of the rest, and this record amends
the claim rather than repeating it:

- 340 journal files, 1,350,053 lines at census time (the desk is
  live; the D-16 run counted 1,349,637 earlier the same evening).
- 62,161 adapter_eval events across 36 sleeves, in 11 distinct
  last_evaluation shapes.
- A broad key census over every adapter_eval tree (every key path
  counted, geometry pattern trig|tp|stop|target|entry|price|level)
  finds geometry in exactly four key paths, all in one shape:
  last_evaluation.pending_set.entry_trigger, .stop, .tp1, .tp2.
  No other adapter_eval shape carries an entry, a stop, or a
  target anywhere in its tree. The bb_rsi_divergence signals list
  (2 signals in 62,161 events) carries bar_close, direction,
  regime, risk_scale, rsi_delta, symbol: no stop, no target.
- The geometry shape belongs to 11 sleeves: trullas_divergence
  and trullas_v01 through trullas_v10, 5,147 events, every one
  with a complete pending_set.

So the estate-wide adapter_eval corpus exists but is one family:
the trullas divergence family's pending setups. Every other
adapter sleeve evaluates in state words (no_breakout, scanning,
blocked_stale_bar), not in priced geometry. Any future claim of
an estate-wide paired corpus must name this bound.

## Extraction method (D-16's method, unchanged)

- Symbol: pending_set carries none. All 11 sleeves trade QQQ:
  sleeves/trullas_divergence.py sets SYMBOL = "QQQ"; the variants
  are thin subclasses of the primary fed on QQQ bars
  (adapters3/trullas_v01.py INPUTS names bars:QQQ:5Min). Symbol
  is sleeve-fixed QQQ and is stated as provenance, not inferred
  per record.
- Record: entry = entry_trigger, stop = stop, target = tp1 (the
  first take profit; tp2 carried as target2 in the working data),
  date = pending_set.session. reward_risk is NOT stated by the
  shape; it is computed as |target - entry| / |entry - stop| and
  labeled computed wherever it is used.
- Dedupe: exact repeats on (sleeve, symbol, date, entry, stop,
  target) dropped; then one observation per (sleeve, symbol,
  date) cell with arithmetic means, the standing discipline.
- Fill join: executed when the fill ledger (8,928 fills, read
  tonight) holds a fill for the same sleeve and symbol on the
  same UTC date.
- Grading: triple barrier on the warm |1Day series for QQQ, 10
  sessions, both barriers in one bar graded stop_first, exactly
  as D-16.

## Coverage counts (recounted from the artifact)

- Raw pending_set records: 5,147. After exact dedupe: 310.
  Cells: 120, across 11 sleeves, 1 symbol (QQQ), dates
  2026-10-26 to 2026-11-13.
- Executed cells: 9 of 120 (7.5 percent). Planned only: 111.
- Graded: 23 (target_first 9, stop_first 14, open_at_horizon 0).
  Unresolvable: 97 (insufficient_forward_sessions 86,
  no_forward_tape 11, the last-session cells). Graded cell dates
  run 2026-10-26 to 2026-10-30 only: the graded subset is the
  earliest window, as with D-16.
- Geometry mix: 67 long-shaped cells (stop below entry), 53
  short-shaped. Graded mean reward_risk 0.575 (tp1 sits close to
  the entry by the family's design), breakeven target-first rate
  at that geometry 63.5 percent.

## Head-to-head against the D-16 tensor_swing corpus

D-16 figures recounted from d16_paired_corpus.jsonl tonight:
244 cells, 101 graded, mean R +0.744, median R -1.00,
target-first rate 27.7 percent against a 17.3 percent breakeven
at mean stated reward_risk 4.77, first-session resolution
94 of 101 (93.1 percent).

V2 (trullas): mean R -0.387, median R -1.00, target-first rate
39.1 percent against a 63.5 percent breakeven at computed mean
reward_risk 0.575, first-session resolution 23 of 23
(100 percent).

Where the two corpora AGREE: the median graded trade loses its
full risk unit in both (median R -1.00); resolution is a
first-session event in both (93 and 100 percent), so on daily
bars both corpora grade barrier placement, not multi-session
paths; and in both, the target-first rate and the payoff geometry
together decide the mean, never the hit rate alone.

Where they DISAGREE, and the disagreement is the finding: the
sign of the mean. tensor_swing's positive mean is carried by
payoff size (stated reward_risk 4.77: rare target hits paying
nearly five risk units). The trullas geometry is the opposite
shape (reward_risk 0.575: the first target pays about half a
risk unit), its target-first rate of 39.1 percent is far below
its 63.5 percent breakeven, and its mean R is negative. The
single-sleeve story from D-16, "positive expectancy carried by
payoff size," does NOT generalize across the only other priced
geometry the estate journals hold: it is a property of
tensor_swing's stated geometry, not of the estate's planned
trades. With n = 23 graded cells the v2 mean is a small-sample
reading and is labeled as such; the structural point (the two
families' geometries sit on opposite sides of their breakevens)
does not depend on the sample.

## Gaps named

- 97 of 120 cells unresolvable until the forward tape extends;
  they grade as sessions print, the same accrual D-16 carries.
- The v2 corpus is one family on one symbol. It widens the
  estate's graded paired population from 1 sleeve to 2 families
  and from 244 to 364 cells; it does not make the corpus
  fleet-wide, and no sentence in this program should say it does.
- The remaining 25 adapter_eval sleeves, and the sleeves that
  journal in eval/unfed shapes, carry no priced geometry in any
  event the census read. A fleet-wide paired corpus requires the
  desk to stamp entry/stop/target on evaluations at the source;
  that is a desk change, named here as the unblocker, not built
  by this program.
