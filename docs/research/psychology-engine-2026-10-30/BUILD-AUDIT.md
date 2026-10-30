# Psychology Engine v1: Build Audit (2026-10-30)

Scope: audit of the built engine against ENGINE-DESIGN.md, section by section.
Build home: ~/workspace/terminal-lineup/psychology-engine/ (also reachable at
~/workspace/psychology-engine/ through a symlink, which satisfies the design's
store root path). Status language follows house law: GREEN only on final-state
evidence, PARTIAL with the unproven part named.

## Section 1, the gauge set: PARTIAL

Built as designed: G2 (677 monthly observations), G3 (617 weekly), G5 (9259
daily), G6 (9306 daily), G9 (3190 daily), each with the uniform expanding
percentile rule, the uniform zone table, true as-of dates, and absence never
zero. Named deviations, each recorded in the series headers and the pull log:

- G1 is absent on day one. The AAII spreadsheet routes returned HTTP 404 from
  this network (publisher bot wall) and the NAAIM page carries no data file
  link. No substitute source was used. The collector code for both is built
  and retries on the daily lane.
- G2 runs on Michigan alone. The Wurgler spreadsheet route is refused from
  this network (the Stern data page returns 403, the current file names
  return 404). The single-source state is the design's own pre-1965 form,
  extended and named here as a deviation.
- G3 is the TFF positioning leg only (2015 forward, 12 annual files). The
  Legacy deep archive to 1986 and the ICI flow tables were not pulled in
  this build; both are named gaps in the store, and the gauge flags partial.
- G4 has 96 daily observations (OKX funding history depth; Binance refused
  from this network) plus the full FINRA margin history from 1997. Under
  the minimum-history rule it correctly shows NO BAND on day one.
- G5 reads the SKEW leg only. Both Cboe put/call file routes returned
  HTTP 404 at build. The gauge flags partial with the refusal named, and
  hook F2's trigger cannot evaluate until the leg lands.
- G6 breadth is computed on a narrow 4-index FRED panel (SP500, NASDAQCOM,
  DJIA, NASDAQ100 closes, 3279 daily breadth rows from 2013-10-17), not
  the 1833-name Alpaca SIP panel: no Alpaca key was found in the desk key
  store at build time, and Yahoo (price only) rate limited after returning
  monthly bars on the max range route, whose files were removed as a
  failed route and logged. The VIX leg carries the gauge's deep history
  to 1990.
- G7 has 71 daily GDELT tone observations from the DOC rolling window
  (deep GKG file backfill not pulled), plus the Wikipedia concept set
  from 2015 as context. It correctly shows NO BAND. The Trends FEARS leg
  is absent (pytrends not installed; pinned pull harness pending).
- G8 snapshot stored day one: 20 Polymarket events, 10 Kalshi markets.
  Metaculus refused (HTTP error). The Fed futures benchmark prints as
  unavailable, per design.

## Section 2, history store and calibration: PARTIAL

Built as designed: one file per series with the full provenance header
(series, source, route, retrieved, last pull, revision policy with
value_first and value_latest where the source revises, as-of meaning,
archive claim, downloaded span, breaks, transforms, file hash), the pull
log, gauge files with the kind column (reconstruction before live start,
live after), and the checker proven in both failure directions by tests.

Hard numeric checks, from exhibits/exhibits.json:

- VIX close 82.69 on 2020-03-16: PASS (stored 82.69).
- VIX close 80.86 on 2008-11-20: PASS (stored 80.86).
- Michigan all-time low in June 2022: FAIL against the design's stated
  expectation, with the file proven right: the stored June 2022 value is
  50.0, exactly the published print, but the latest FRED vintage has
  since printed lower (44.8 in 2026-05), so June 2022 is no longer the
  all-time low of the stored series. The check is overtaken by newer
  data, not by a store error.
- FINRA margin debit peak in March 2000: FAIL as stated. The stored
  March 2000 debit balance is 299933 (million) and is present, but
  nominal debit balances grow over decades and the stored nominal peak
  is 2026-06. The design's check cannot pass on the real FINRA file in
  nominal terms. Recorded here as a design-check defect, not hidden.

Archive depths confirmed, corrected, or unreached (closing the studies'
UNVERIFIED loop): Cboe VIX and SKEW from 1990-01-02 confirmed by download;
VIX3M from 2009-09-18 and VIX9D from 2011-01-04 recorded as downloaded;
Cboe put/call depths (2003 and 2006) UNREACHED, routes refused; Alternative.me
from 2018-02-01 confirmed; Michigan from 1952-11-01 confirmed with the
quarterly era kept quarterly; FRED high yield OAS reaches only 2023-10-31
through the graph route (the graph caps a pull near 800 points and most
chunk windows were refused), so the December 1996 depth is UNREACHED and
named; COT TFF pulled 2015 forward, the 2006 to 2009 junction check and
the Legacy 1986 depth are UNREACHED and named.

## Section 3, composite: GREEN for the mechanism

Median of available core gauges (4 of 6 on day one), Insufficient data
below four (proven by synthetic test), contested rule (proven by
synthetic test naming both poles), G4 overlays, extremes with entry
dates, stated versus revealed fracture sentence implemented. Day one
state: Fearful, composite percentile 24.6, gauges agree.

## Section 4, forecast hooks: PARTIAL

All four hooks are registered with every Section 5.4 field and verbatim
kill conditions in registry-psychology.json at the engine root. F1 is
registered but could not fire on day one (no AAII print exists to
forecast from; named, not substituted). F2 is armed; its trigger cannot
evaluate while the put/call leg is absent. F3 is NOT shipped live,
because the P22 backtest gate was not run in this build (blocker: the
Ken French characteristic sort files and the Baker-Wurgler issuance
components were not pulled); per design that outcome is recorded, and
the engine ships family gauges with no composite forecast claim from
F3. F4 is armed; no signature on day one. The BACKTEST-RECORD runs P19
in reduced form (32 top-decile VIX signature days on the modern record;
12.5 percent traded at least 5 percent lower within 60 sessions, which
supports the zone-not-a-date reading) and labels everything BACKTEST.
Ledger scan on day one: zero psychology rows exist in the estate ledger
and zero backdated rows; the hash chain verifies. The 65 rows appended
to the estate ledger during the build window were the estate's own
17:46 daily refresh (engine_15 and kin), verified by inspection.

## Section 5, pipeline: PARTIAL

Built: 12 isolated live collectors with raw snapshot retention and
failure records, a backfill harness that is idempotent by rewrite and
resumable by pull log (the build itself was killed and resumed three
times across transport fixes, with the store intact), a compiler that
never writes the series store, the append-only ledger interface through
the estate Ledger class, state JSON, one-page STATE.md, the Market Mood
page and feed, and the FINRA per-name short volume store, which accrued
12266 rows for 2026-10-30, curing that named Part 1 gap at the store
level from day one. Not yet proven: five consecutive unattended sessions
(design items 3, 7, 9, 11 acceptance windows) cannot be proven on day
one; they accrue on the lane and are named here as the standing proof
obligation. The Coinalyze leg uses curl with the exact api_key header
(the http.client route fails TLS in this environment because it bypasses
the egress proxy; curl is the working route of the two the desk law
allows) and its snapshot landed on day one.

## Section 6, consumer file: GREEN for day one

SENTIMENT-STATE.md and .json written at the fixed paths under
~/workspace/midna-book/ by the compiler, numbers identical to the state
JSON by construction (one render path), no order language, the
rule-written how-this-bears section supplying the Charter Amendment 6
game-layer fields from stored measurements, closing line present. The
pre-open cron (personal-quant-preopen-read) does not enumerate its input
files, so per the build instructions it was left untouched; the consumer
file sits at its fixed path for the pre-open read to pick up.

## Section 7, build list

Items 1, 4, 5 (with the two check failures named above), 7, 9, 10: built
and evidenced day one. Item 2: PARTIAL as itemised in Section 2 of this
audit. Item 3: PARTIAL, collectors built and day-one results recorded;
the five-session proof accrues. Item 6: PARTIAL, P19 reduced form run,
P22 not run, F3 gated out and recorded. Item 8: PARTIAL, hooks
registered, none fired day one for the named reasons, ledger discipline
proven by scan. Item 11: lane created and enabled (psychology-engine-daily,
weekdays 18:15 ET, goal-owned by Midna's book); the five-session and
Saturday re-check proofs accrue. Item 12: this audit.

## Named future commissions

Unchanged from the design's Section 7.3 list. None is stubbed in v1.
