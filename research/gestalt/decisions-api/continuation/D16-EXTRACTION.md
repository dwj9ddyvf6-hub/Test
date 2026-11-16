# D16 Extraction: Graded Paired-Records Corpus

Task C2 of the Continuation program, Sat 2026-11-14. Built by
`d16_extraction.py` in this folder (rerunnable: `python3 d16_extraction.py`).
Corpus: `d16_paired_corpus.jsonl`, 244 lines, one per deduped cell.

## Sources

- Journals (read-only): `~/workspace/muse-desk-v3/state/<sleeve>/journal.jsonl`,
  plus the one rotated file present, `tensor_swing/journal.jsonl.1`.
  On disk at run time: 339 `journal.jsonl` files and 1 rotated file.
  The X10 census figure of 338 files and 1,330,125 lines predates the
  run; the desk is live and journals keep appending, so the counts
  below are the counts of this run, not the census.
- Forward tape (read-only): `~/workspace/muse-desk-v3/state/warm_bars.json`
  (fetched_at 2026-11-14T23:37:46+00:00). Structure: a dict with keys
  `fetched_at` and `bars`. `bars` is a dict keyed by symbol and by
  `"<SYMBOL>|1Day"` and `"<SYMBOL>|1Hour"` variants; each value is a
  list of `{"t", "o", "h", "l", "c", "v"}` bars where `t` is an ISO
  timestamp whose first 10 characters are the bar's UTC date. Daily
  bars used here are the `|1Day` series (162 symbols), the same series
  the wave 2 tooling reads; bare symbol keys duplicate the `|1Day`
  series where both exist, and `|1Day` was chosen because the
  timeframe is explicit in the key. Equity daily series end at the
  2026-11-13 session.
- Fill ledger (read-only):
  `~/workspace/muse-desk-v3/state/fill_ledger/fills-*.jsonl`
  (fills-000001.jsonl and fills-000002.jsonl), the path read by the
  wave 2 tools `disagreement_index.py` and `execution_alpha.py` under
  `research_notes/decisions-api-leverage-20261114/tools/`. 8,928 fills
  read, matching the verified ledger size.

## Schema of d16_paired_corpus.jsonl

One JSON object per line, one line per deduped (sleeve, symbol, date)
cell, sorted by sleeve, symbol, date.

- `sleeve` (string): sleeve name from the journal line.
- `symbol` (string): symbol from the paired record.
- `date` (string, YYYY-MM-DD): journal ts date in UTC.
- `entry`, `stop`, `target` (numbers): cell means of the paired
  records collapsed into the cell (the single record's values when
  the cell holds one distinct record).
- `reward_risk` (number): cell mean of the records' stated
  reward_risk.
- `n_records_in_cell` (integer): number of distinct records, after
  exact dedupe, collapsed into the cell.
- `executed` (boolean): true when the fill ledger holds at least one
  fill for the same sleeve and symbol on the same UTC date;
  false means planned_only.
- `outcome` (string or null): one of `target_first`, `stop_first`,
  `open_at_horizon`, or null when unresolvable.
- `r_multiple` (number or null): graded R, null when unresolvable.
- `sessions_to_outcome` (integer or null): 1-based forward session
  index of the resolving bar, 10 for `open_at_horizon`, null when
  unresolvable.
- `unresolvable_reason` (string or null): `no_forward_tape` or
  `insufficient_forward_sessions`, null when graded.

## Method, with every constant and its reason

- Parse: every journal line is counted and a JSON parse is attempted
  on every line. Only lines whose `event` field is exactly
  `last_evaluation` and whose `stamp.paired_records` is a non-empty
  list contribute records, per the brief. Each record contributes
  symbol, entry, stop, target and reward_risk.
- Dedupe step 1, exact repeats: drop a record that repeats an earlier
  record on (sleeve, symbol, date, entry, stop, target), date being
  the journal ts date in UTC. Reason: the same evaluation re-stamped
  across cycles is one observation, not many. reward_risk is not in
  the key because the brief defines the key without it; the first
  occurrence is kept.
- Dedupe step 2, one observation per cell (the standing discipline,
  the H2 twins rule): collapse to one observation per (sleeve,
  symbol, date) cell; a cell holding distinct records takes the
  arithmetic mean of entry, stop, target and reward_risk across its
  records.
- Fill join: executed=true when the fill ledger holds a fill for the
  same sleeve and symbol whose ts UTC date equals the cell date.
  The UTC date is used on both sides so the join uses one calendar.
- Outcome grading, triple barrier (the dive-one standard): from the
  first daily bar strictly after the cell date, walk forward up to
  10 sessions. The horizon of 10 sessions and the barrier rules are
  fixed by the brief so nothing is tuned per sleeve or symbol.
  Long-shaped cell (stop below entry): a bar high at or above target
  is a target hit, a bar low at or below stop is a stop hit.
  Short-shaped cell (stop above entry): the math is mirrored, a bar
  low at or below target is a target hit and a bar high at or above
  stop is a stop hit. If both barriers are touched in one bar the
  outcome is stop_first (conservative, as stated in the brief).
  target_first pays R = +reward_risk (cell mean); stop_first pays
  R = -1; neither barrier within 10 sessions gives open_at_horizon
  with R = direction x (close at session 10 minus entry) /
  abs(entry minus stop), direction +1 long and -1 short.
- Unresolvable, never graded on partial tape: `no_forward_tape` when
  the symbol has no daily series in warm_bars or the series holds no
  bar strictly after the cell date; `insufficient_forward_sessions`
  when forward bars exist but fewer than 10 remain before the tape
  ends. Only resolved cells are graded.

## Coverage counts (this run, from the final artifact)

- Journal files read: 339 `journal.jsonl` plus 1 rotated
  `journal.jsonl.1` (tensor_swing).
- Lines read: 1,349,637 total. Of those, 1,333,467 from
  `journal.jsonl` files and 16,170 from the rotated file, counted
  separately as required.
- Lines parsed as JSON: 1,349,637 (every line parsed; zero parse
  failures).
- `last_evaluation` events found: 21,358. Of those, 2,114 carried a
  non-empty `stamp.paired_records` list.
- Paired records extracted (raw): 13,168. Malformed records skipped:
  0.
- After exact dedupe: 475 records (12,693 dropped as exact repeats;
  0 of the dropped records carried a reward_risk differing from the
  kept record).
- Cells after the one-observation collapse: 244. 118 cells averaged
  more than one distinct record; the largest cell holds 6 records.
- Sleeves in the corpus: 1 (tensor_swing). The string
  `paired_records` occurs only in the tensor_swing journals, verified
  by full text search of every journal file, so the corpus is
  single-sleeve by construction of the source, not by filtering.
  Distinct symbols: 41. Cell dates run 2026-10-25 to 2026-11-12.
- Short-shaped records (stop above entry): 0 raw records and 0
  cells. Every record is long-shaped, so the mirrored short math in
  the script was never exercised by this corpus.
- Fills read: 8,928. Fill-joined cells (executed=true): 118.
  Planned only cells: 126.
- Outcome-joined cells (symbol has a daily series and at least one
  forward bar): 244.
- Graded cells: 101 (target_first 28, stop_first 73,
  open_at_horizon 0). Graded cell dates run 2026-10-25 to
  2026-11-01.
- Unresolvable cells: 143, by reason: insufficient_forward_sessions
  143, no_forward_tape 0. Unresolvable cell dates run 2026-11-02 to
  2026-11-12; they become gradable only when the forward tape
  extends at least 10 sessions past each cell date.

## First three findings (computed from the graded corpus)

Finding 1. Positive mean R carried by payoff size, not hit rate.
Across the 101 graded cells the mean R is +0.74 (sum +75.18R) while
the median R is -1.00. The target-first rate is 27.7 percent (28 of
101) against a breakeven rate of 17.3 percent at the graded cells'
mean stated reward_risk of 4.77, so the average is positive only
because the minority of target-first cells pay a large stated
multiple.

Finding 2. Grading resolves almost immediately, and mostly at the
stop. 94 of 101 graded cells resolve on the first forward session
(68 stop-first, 26 target-first), 5 on session 2 and 2 on session
3; none reach the 10-session horizon unresolved
(open_at_horizon = 0) and the mean sessions to outcome is 1.09. On
daily bars, the recorded stops and targets sit inside the next
session's range for nearly every cell, so this corpus grades the
placement of the barriers more than any multi-session path.

Finding 3. Per-symbol extremes are small-n and reward-risk driven;
no symbol-level conclusion survives its n. The best graded symbol
means are LITE at +21.72R on n=2, WDC at +4.05R on n=2 and CVNA at
+3.95R on n=2, each carried by very large stated reward_risk values
(the largest cell in the corpus states 138.79). The only symbol
with n of 5 or more, ASPI (n=5), stopped out on all five cells for
a mean of -1.00R. The corpus's usable content at this size is the
aggregate in Finding 1, and 143 of 244 cells (58.6 percent) remain
unresolvable until the forward tape extends past their dates.

## Gaps named honestly

- The corpus is one sleeve (tensor_swing) because no other sleeve
  journal carries `stamp.paired_records` under `last_evaluation`
  events. Any estate-wide reading of these findings would be a
  generalization the source does not support.
- 58.6 percent of cells are unresolvable at this tape end. The
  graded subset is the earliest cells (2026-10-25 to 2026-11-01)
  only, so the findings describe that window, not the full period.
- The fill join uses the UTC calendar date on both sides. Fills are
  timestamped in UTC in the ledger, and the brief fixes the journal
  date in UTC, so one calendar was used for both; an America/New_York
  session-date join could move a small number of cells across the
  executed boundary and was not run.
