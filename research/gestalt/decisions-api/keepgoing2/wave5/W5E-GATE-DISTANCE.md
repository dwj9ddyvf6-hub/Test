# W5-5 GATE-DISTANCE STAMP QUESTION: Wave 5, Lane E

Date: Sat 2026-11-14 late night ET (work run 2026-11-15 about 00:00 ET, file
stamps in UTC as recorded). Desk repo: ~/workspace/muse-desk-v3, HEAD 3e474e1
at start and at finish, tree clean, NO CODE LANDED (see verdict).

SCOPE: Surface, state/gate_distance.jsonl and the rsi2 probe in
desk3/gate_distance.py plus its caller seam and its QQQ|1Day producer.
Constraints, no strategy, gate, sizing, risk, saty or Tensor change; cure only
if the recorder is convicted. Outcome, a reproduced count set and a verdict in
the words UPSTREAM or RECORDER. Proof, snapshot series, an independent RSI
implementation, and a live SIP fetch, all below. Edges, the warm bars cache
(3600s) and the daily bar integrity gate in desk3/warm.py.

## 1. REPRODUCTION (from state/gate_distance.jsonl, own count)

Parent recon window, rows with asof at or before 2026-11-15T04:15:13Z,
reproduced EXACTLY:

| probe | rows | distinct measured | distinct asof |
|---|---|---|---|
| rsi2 | 232 | 1 | 29 |
| absorption | 87 | 58 | 29 |
| breakout | 58 | 3 | 29 |
| funding | 145 | 4 | 29 |
| sma200 | 58 | 16 | 29 |
| nsm_band | 20 | 15 | 10 |
| total | 600 | n/a | 29 |

The single rsi2 measured value is 34.78674565049475 (distance +24.7867 over
threshold 10.0), across 8 sleeves (aster_rec_rsi2_long_fixed_a/b,
long_touch_a/b, vertical_fixed_a/b, vertical_touch_a/b), and every rsi2 row
carries the identical note: "RSI2 34.78674565049475; close 679.89 vs SMA200
682.24 (below)".

Live file at my copy (one cycle later than the recon, the runner is live):
620 rows total, rsi2 240 rows, 30 distinct asof, span
2026-11-14T21:10:30.803479+00:00 to 2026-11-15T04:38:45.153311+00:00, still
exactly 1 distinct rsi2 measured value. In ET that span is Sat 2026-11-14
16:10 to Sat 2026-11-14 23:38. Rows inside any Mon to Fri 09:30 to 16:00 ET
RTH window: 0. The recon numbers are confirmed, not corrected; the delta is
one additional live cycle (20 rows, 8 of them rsi2).

## 2. DISCRIMINATING EVIDENCE

### (a) The series the recorder actually saw, and the RSI math

Latest retained snapshot state/snapshots/e8632a86....json (asof
2026-11-15T04:38:45Z, one of 3 retained snapshots; all 3 carry the same
QQQ|1Day tail):

- bars["QQQ|1Day"]: 345 bars, first 2025-07-03, last five closes
  679.35 (2026-11-09), 674.76 (2026-11-10), 690.38 (2026-11-11),
  688.17 (2026-11-12), 679.89 (2026-11-13T05:00:00Z, Friday's session).
- SMA200 over the last 200 closes: 682.2389, which is the note's 682.24.
- Independent Wilder RSI(2) implementation written for this lane, run over
  those 345 closes: 34.78674565049475. Exact float match to the recorded
  value.
- desk3/gate_distance.py's own route, _common()._rsi(closes, 2) from
  aster_sleeves/_common.py, returns a list whose last element is
  34.78674565049475. The recorder takes r[-1] correctly.
- The sleeves' own gate math, desk3/aster_b2.py _rsi2(closes) (the function
  the 8 aster_rec_rsi2 sleeves themselves evaluate, same _bars(view, "QQQ")
  series, gate r < 10 and close over SMA200): 34.78674565049475. Three
  implementations, one number. The recorder measures the gate the sleeves
  actually run, with the sleeves' own arithmetic result.

### (b) Door series vs QQQ's actual Friday close (live SIP fetch)

Fetched tonight through the prescribed route (sys.path the desk root,
desk3.run_live.credential_env(), desk3.netfetch.fetch_json,
https://data.alpaca.markets/v2/stocks/bars, feed sip):

- Adjustment used for the comparison: raw, which is the adjustment
  desk3/warm.py _fetch requests. On this window split and all return
  identical closes (no corporate action in the window), so the conclusion
  does not depend on the choice.
- SIP raw, QQQ 1Day, 2026-11-13: open 688.54, high 688.75, low 671.681,
  close 679.89, volume 42304006, timestamp 2026-11-13T05:00:00Z.
- Door series last bar: open 688.54, high 688.75, low 671.681, close 679.89,
  volume 42304006, timestamp 2026-11-13T05:00:00Z. Field for field identical.
  The full SIP week (2026-11-09 to 2026-11-13 closes 679.35, 674.76, 690.38,
  688.17, 679.89) also matches the door series bar for bar.
- The series is not stale, not miskeyed, and its last bar IS Friday's bar.

### (c) Caller seam and producer: rebuilt per cycle, completed bars only

- desk3/cycle.py run_cycle() rebuilds the data dict from producers on every
  cycle, builds one snapshot (build_snapshot, saved under state/snapshots/),
  and at about line 499 calls gate_distance.record_cycle(self.state,
  now.isoformat(), list(results.keys()), data) inside a fail-open guard.
  The recorder receives that cycle's fresh view, not a stored one.
- The QQQ|1Day series comes from desk3/warm.py WarmBars/fetch_all: Alpaca
  SIP 1Day, adjustment raw. WarmBars serves state/warm_bars.json from cache
  only while fresh (max_age_s 3600; the cache on disk tonight carries
  fetched_at 2026-11-15T04:15:13Z, matching a cycle stamp), then refetches.
  Worst case staleness by design is one hour, not indefinite.
- Forming bar handling, from warm.py _fetch (WARM-DAILY-PARTIAL-BAR-20261102
  and the BARS-INTEGRITY gate): for 1Day, trailing bars dated after
  expected_latest_completed_session(now) are TRIMMED before validation, and
  the series must end exactly on the latest completed session (today ET only
  once the session has closed and settled at 16:30 ET, else the prior
  trading day, walked back over the desk calendar). So the served equity
  daily series contains ONLY completed bars, during RTH as well as on
  weekends. On Sat 2026-11-14 the latest completed session is Fri
  2026-11-13 at every stamp, so a correct recomputation returns the same
  closes, and therefore the same RSI(2), at all 30 stamps.
- The view is demonstrably not frozen as a whole: the 3 retained snapshots
  have distinct hashes (60dc85ca, 6c7f3b8c, e8632a86), 16 bars keys differ
  between the first and the last (crypto series move all weekend; the
  PF_ADAUSD 4Hour forming bar volume alone goes 169309 to 484110 to
  751068), while QQQ|1Day is byte-identical. The freeze is confined to
  exactly the one probe whose underlying market is closed. Every varying
  probe (funding, absorption, breakout, sma200, nsm_band) is fed by crypto
  or perp series that trade on weekends; rsi2 is the only equity daily
  probe in the set.

### (d) Live-hours evidence in the file

None exists, in either direction. The file's entire life begins Sat
2026-11-14 21:10:30Z (16:10 ET), after Friday's close and after the
recorder landed that evening. It contains zero RTH rows. The file simply
has no live-hours evidence; the weekend window is the whole corpus, which
is exactly why the D-02 freeze read could not discriminate on its own.

## 3. VERDICT: UPSTREAM

Root cause: UPSTREAM DATA REALITY (the read window). The recorder computes
correctly from a correct, current series whose inputs are identical because
the US equity market is closed and the warm producer serves completed daily
bars only. NO CODE LANDED. Desk HEAD remains 3e474e1, tree clean, no diff,
no blocker, no gate run, no BUGLOG entry, no restart: there is no defect to
cure, and landing a change would be a fence dressed as a fix.

What would have convicted the recorder, and why none of it holds:

- A miscomputed RSI: convicted if an independent RSI(2) over the snapshot
  closes, or the sleeves' own _rsi2, disagreed with the stamp. Both agree
  to the last digit (section 2a).
- A stale, cached or miskeyed series: convicted if the door series' last
  bar were not Friday's real bar, or ended on an older session. The SIP
  fetch matches it field for field, and the integrity gate requires the
  series to end exactly on the latest completed session or drop the symbol
  by name (section 2b, 2c).
- A frozen view: convicted if the snapshot were one object restamped. Each
  cycle rebuilds the view and the snapshot hash changes; only the equity
  daily key is constant, alongside live movement in 16 other bars keys
  (section 2c).
- Forming-bar mishandling: convicted if the recorder or producer admitted
  an in-progress daily bar. The producer trims it by construction
  (section 2c).

Separate observation, recorded and NOT cured tonight, for a future
instrumentation row: the gate_distance record schema stamps the cycle asof
but carries no bar-as-of field (the underlying series' last bar date). The
rsi2 note prints RSI, close and SMA200 but not the bar date 2026-11-13.
That omission is what made a weekend-correct repetition read as a freeze;
adding a last-bar-date field to the note or schema is a small recorder
instrumentation change for a later, separately scoped row.

## 4. OPEN ROW: LIVE-HOURS PROOF (dated)

OPEN ROW, W5-5-LIVE-RSI2, due Mon 2026-11-16 (first RTH session after the
landing): read state/gate_distance.jsonl after Monday's session and confirm
the predicted behavior below. Tonight cannot supply this proof; the file
has no RTH rows yet (section 2d).

What the code predicts: the rsi2 measured value stays at Friday's
34.78674565049475 through all of Monday RTH (the served QQQ|1Day series
still ends on Friday's completed bar, because the forming Monday bar is
trimmed), then steps exactly once to a new value on the first cycle whose
warm fetch includes Monday's completed bar, which the integrity gate only
allows after Monday 16:30 ET (plus up to the 3600s warm cache lag). It does
NOT move intraday.

What the strategy's own gate semantics require: the same behavior. The 8
sleeves evaluate the identical completed-bar series with the identical gate
(r < 10 and close over SMA200) in desk3/aster_b2.py, so their gate cannot
move intraday either; a recorder that moved intraday would be measuring a
gate the sleeves do not run. If Monday instead shows the value moving
intraday, or failing to step after Monday's completed bar is served, that
convicts the recorder or the producer and reopens this lane as a RECORDER
case.

## 5. STATUS

STATUS: PARTIAL (bounded portion proven, the rest named). The reproduction
and the root cause are proven on the final state tonight (counts, snapshot,
independent RSI, live SIP, code seam). The live-hours behavior is the one
named open row above, dated Mon 2026-11-16. No code landed, by the decide
rule, because the evidence acquits the recorder.

EVIDENCE POINTER: this file, sections 1 and 2 (counts from
state/gate_distance.jsonl copy at 620 rows; snapshot
state/snapshots/e8632a86ed1b94b5fc87538e5397edd314647e549f52a229426f5b7dae4d52b8.json;
SIP fetch through desk3.netfetch on 2026-11-15 about 04:55Z; desk tree at
3e474e1, clean).

## ONE-PARAGRAPH SUMMARY FOR THE WAVE REPORT

The frozen rsi2 stamp is the market being closed, not a recorder defect:
reproduction matched the recon exactly (600 rows in the recon window, rsi2
232 rows with one measured value, 34.78674565049475), an independent Wilder
RSI(2) over the latest snapshot's 345 QQQ daily closes reproduces that value
to the last digit and so do both the recorder's _common()._rsi and the
sleeves' own aster_b2 _rsi2, a live SIP fetch shows the door series' last
bar is Friday 2026-11-13's real bar field for field (close 679.89), and the
warm producer serves completed daily bars only (the forming bar is trimmed
by the integrity gate), so every weekend stamp correctly recomputes the same
number while crypto-fed probes in the same file vary all weekend. Verdict
UPSTREAM, no code landed; the one open row is the live-hours proof on Mon
2026-11-16, where the code predicts (and the sleeves' own gate semantics
require) a flat reading through RTH and a single step after Monday's
completed bar is served, plus a separately recorded observation that the
schema lacks a bar-as-of field, which made the correct repetition look like
a freeze.
