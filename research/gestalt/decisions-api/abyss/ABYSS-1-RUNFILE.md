# ABYSS, SCOUTING RUN 1: PRE-REGISTRATION (written before any probe result is read)

Filed Sun 2026-11-15, before the runs. The widening order (owner,
2026-11-15 01:15 ET, all efforts x10) is applied inside this file:
every probe runs at the widest coverage its data honestly
supports, pays its true trial count, prints its null, and labels
its n. Multiplication is of coverage and depth, never of standard.

## Data inventory (availability measured tonight; no probe statistic computed yet)

- PANEL: keepgoing2/wave3/focus_bars.json. 29 Focus names plus
  SPY and QQQ, daily SIP bars, split-adjusted, 2018-01-02 to
  2026-11-13. Full-history names hold 2,230 bars; later listings
  (ARM, CRWV and kin) hold fewer, and every per-name n is printed.
- TRACKERS: abyss/tracker_bars.json. EWJ, EWY, FXI, EZU, EFA,
  daily SIP split-adjusted, 2,230 bars each, same span, fetched
  tonight through the estate Alpaca route.
- CRYPTO: abyss/coinbase_daily.json. BTC/USD and ETH/USD daily
  candles, Coinbase public route, 3,241 days, 2018-01-01 to
  2026-11-15. Cross-checks held: Kraken public OHLC (trailing
  721 daily candles only, 2024-11-25 forward; the route's cap
  was measured tonight, so no longer Kraken history exists
  through it) in abyss/kraken_daily.json, and Alpaca crypto bars
  (2021-01-01 forward) in abyss/crypto_bars.json.
- PRINTS: the estate SIP trades route, measured tonight at
  288,336 prints and about 54 s for one NVDA final-30-minute
  window (2026-11-13). Held print sequences at depth do not
  exist on the box (the friction crawl stored quotes and single
  prints only; the MK-01 probe stored aggregates), so the tape
  corpus for A-1 and A-4 is fetched tonight through the estate
  route and stored as token arrays in this folder.
- GEOMAGNETIC: GFZ Potsdam Kp/Ap JSON API, liveness and shape
  verified tonight through the browser (Kp 3-hourly values with
  definitive status flags). Daily Ap pulled per calendar year
  through the same public API route the estate uses for FINRA
  and Coinbase data.

## Standing constructions (inherited, not re-invented)

Overnight leg ON_t = open_t / close_{t-1} - 1; intraday leg
IN_t = close_t / open_t - 1. Basket series are equal-weight
means over names with both prints that day, minimum 10 names
(the Wave 3 construction, frozen). The find's anatomy on the
record: ON_focus29 gross mean about +16.5 to +18.9bp a night,
Sharpe 1.67, tail-carried (best 90 of 2,229 nights hold about
88 percent of the premium), vanishing when SPY closes below
its 200-session mean, weekday legs carrying 82.1 percent.

## A-1 TAPE LINGUISTICS

Question: do recurring print sequences (phrases) in a session's
tape carry forward information that survives a clean split?

Corpus (widened to the honest maximum the measured route
supports in one night on a shared box): SIP prints, feed sip,
for all 31 panel names (29 Focus plus SPY and QQQ), window W2 =
15:30 to 16:00 ET, over the last 30 completed panel sessions;
plus window W1 = 09:30 to 10:00 ET for the 8 highest-print
names (NVDA, AMD, MU, AVGO, TSM, PLTR, SNDK, SPY). The session
list is the panel's last 30 sessions by SPY dates, fixed here
as a rule before fetching. Split: train = first 15 sessions
chronologically, test = last 15. No session moves halves.

Tokens: one token per print. Sign by the tick rule against the
previous print inside the window (up, down, zero; the window's
first print is zero). Size bucket by shares: 1-99, 100-499,
500-4999, 5000+. Gap bucket by inter-print milliseconds:
under 10, 10-100, 100-1000, over 1000. Alphabet 3 x 4 x 4 = 48.

Mining (train half only): for n in 3..6, per name-window,
count n-grams. A phrase is a candidate if it occurs at least
40 times in train for that name-window. For each candidate,
the train forward mean: for W2, that night's overnight leg of
the same name; for W1, the next-hour return (15-minute bar
close at 11:00 over the 15-minute bar close at 10:00, bars
fetched for the 8 W1 names over the same sessions). Select the
top 10 candidates per name-window by absolute train forward
mean; direction is the train sign, frozen.

Test (test half only, untouched during mining): for each
selected phrase, occurrences, mean forward return, and the
one-sample t of the forward returns in the frozen direction.
A phrase CARRIES if its test mean has the train sign and
|t| >= 2. Report every selected phrase's test line, the count
of carriers, and the chance expectation beside it (binomial
mean of the test count at the nominal rate). Trial count for
A-1 = the number of phrase tests actually run, printed. No
DSR is claimed for any phrase: the mining multiplicity is the
reason, stated on the face. A pooled read (all test
occurrences of carrying phrases, date-clustered) is reported
as a diagnostic, never as a find.

## A-2 THE WORLD'S OVERNIGHT

Question: does the Focus overnight premium concentrate on
nights the world moved a particular way?

Proxy identity, on the face: EWJ (Japan), EWY (Korea) and FXI
(China) are US-listed trackers whose own overnight legs price
the Asian sessions that run inside the US night; EZU
(Eurozone) and EFA (EAFE) overnight legs price Asia plus the
European pre-open. They are trackers, not foreign cash
indices, and no futures series is held; the futures reference
route is named unavailable tonight rather than substituted
silently.

Tests, per tracker (5): split ON_focus29 basket nights by the
tracker's same-night overnight leg. Primary: sign split (world
up nights vs world down nights), Welch t on the difference.
Secondary: tercile contrast (top vs bottom tercile means,
Welch t). That is 10 primary-family trials. Widened secondary:
the same sign split and tercile contrast on the pooled per-name
overnight legs (name-nights, t clustered by date) for the
three Asia trackers only: 6 more trials. A-2 trial count 16.
Null printed per test: the unconditional basket mean and the
difference's standard error under the split.

## A-3 WEEKEND CRYPTO

Question: do BTC and ETH weekend returns condition Monday's
Focus legs?

Series: Coinbase daily (primary, labeled), weekend return
W = close Sunday UTC / close Friday UTC - 1, per asset, plus
the BTC/ETH average. Forward variables from the panel, per
Monday session: the basket overnight leg (Friday close to
Monday open) and the basket intraday leg (Monday). Tests per
series (BTC, ETH, average): sign split of Monday legs by W
sign, and tercile contrast of W, on the overnight leg
(primary family: 3 series x 2 tests = 6) and on the intraday
leg (6). Placebo: the same sign split on Tuesday overnight
legs against the same weekends (2 tests, BTC and average).
A-3 trial count 14. Data-quality cross-checks (not trials):
correlation of weekend returns across Coinbase, Kraken
(721-day overlap) and Alpaca (2021+ overlap) series.
n: Mondays in 2018-2026 panel, printed (about 460).

## A-4 ENTROPY CONDITIONING

Question: does per-name tape entropy split the overnight
premium (low-entropy names or nights carrying more)?

Instrument: from the A-1 corpus, per name-session (W2 window),
the Shannon entropy of the print-sign unigram distribution and
of the sign bigram distribution, each normalized to [0,1] by
its support maximum. Population: all name-sessions in the
corpus with at least 5,000 prints in W2 (the print floor is
registered here; name-sessions under it are excluded and
counted). Tests: (1) primary: pooled tercile contrast of that
night's overnight leg, bottom vs top unigram-entropy tercile,
Welch t; (2) bigram-entropy tercile contrast, same forward;
(3) within-name median split pooled (each name-session signed
by its own name's median), unigram; (4) W1 unigram entropy
tercile contrast against the next-hour return on the 8-name
subset. A-4 trial count 4. The recent-window n is printed on
every line; this probe is a conditioner screen, not an exam.

## A-5 DIGIT FORENSICS

Question: are the digits of our own data clean, and does any
stable deviation carry forward information?

Diagnostics (data-quality first): (a) last digit (cents) of
daily closes, pooled over the 29 Focus names, chi-square
against uniformity, run separately on 2018-2021 and 2022-2026;
stability = rejection in both subperiods with the same modal
digit. (b) Per-name chi-square for names with at least 1,000
bars, counted, with the pooled result governing. (c) Print
sizes from the A-1 corpus: last-digit histogram pooled, and
the round-lot share (sizes divisible by 100), per window.
(d) Benford first-digit on daily traded share volume pooled
(volumes are the Benford-appropriate quantity; prices are
not, and that distinction is printed rather than blurred).
Predictive probe (exactly one, conditional, its form fixed
here): IF the pooled close-digit deviation is stable by the
rule above, THEN test the basket overnight leg on nights the
basket's median close ends in the modal digit vs all other
nights, Welch t. If the condition fails, no predictive probe
runs and the cell closes as a data-quality read. A-5 trial
count: 4 (three diagnostic families plus the conditional
probe, counted whether or not it fires).

## A-6 SPECTRAL

Question: does the overnight series carry power at
non-calendar frequencies?

Series: ON_focus29 basket (primary), SPY overnight leg
(control), basket intraday leg (control). Method: periodogram
(FFT of the demeaned series, session grain) per series.
Exclusion bands (calendar, by construction): periods 5 and
its sub-harmonics 2.5, plus bands at 21 +/- 2, 63 +/- 4,
252 +/- 10 sessions, and the weekly harmonics at periods
10, 15, 20 within +/- 1. Peaks: local maxima of the
periodogram outside the bands. Null: 1,000 shuffles of each
series; a peak is significant if its power exceeds the 99th
percentile of the shuffled maximum power at that same
frequency across shuffles (per-frequency null, printed), and
the count of such peaks is compared against the null's own
false-peak rate. Trial count: the number of peaks assessed,
printed per series. A significant non-calendar peak earns a
Wave 8 cell (a phase-stable sinusoid split), not a claim.

## A-7 GEOMAGNETIC (esoterica, honestly labeled)

Question: does geomagnetic activity condition next-session
volatility or the overnight legs?

Data: daily Ap (GFZ Potsdam, definitive), matched to panel
sessions by UTC date; the session's Ap is the value of the
UTC day on which the session's overnight leg begins (the
close date). Tests (the whole family, no sequels without a
survivor): (1) basket next-session realized volatility
(median per-name intraday range over close) on top-decile Ap
days vs the rest, Welch t; (2) basket overnight leg mean on
top-decile Ap nights vs the rest; (3) SPY next-session
realized volatility, same split (control). A-7 trial count 3.
The debunking literature is cited in the report beside the
numbers (the Atlanta Fed methodological critique of the
geomagnetic-market claim and the claim's own out-of-sample
record), verified by reading, not from memory. One probe,
no sequels without a survivor: that sentence is part of the
registration.

## Trial ledger

Lab cumulative count before this run: 487 (Mad Lab batches 1
and 2, per the Wave 6 record). This run adds: A-1 as printed
(phrase tests run), A-2 16, A-3 14, A-4 4, A-5 4, A-6 as
printed (peaks assessed), A-7 3. The run's total and the new
cumulative are printed in the report. Every probe prints its
null beside its result. Survivors and near-misses are labeled
with their costs; a survivor here is a Wave 8 cell with a
forward falsifier, never a promotion.

## Rails

Real data only. Paper and shadow only. No desk edits. One
heavy job at a time: the print fetch runs as a single
background stream; bar-level probes run sequentially; Wave 7
and the Conversion Engine own their lanes and this run yields
on contention. Typed seats: none seated; the probe set was
fully specified by the owner's brief and the widening order,
and the exams are deterministic. Spend $0.00, named here
rather than hidden. PII scan on the shared write. No em
dashes for the owner.
