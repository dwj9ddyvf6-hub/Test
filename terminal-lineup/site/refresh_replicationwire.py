#!/usr/bin/env python3
"""Refresh the Replication Wire data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: our own study records, read exactly as they stand:
the written analysis of the forecast program's searches and reruns,
the finished setup studies (bull flag, the multi-timeframe VWAP
stack, dip-buying in uptrends, the washout pullback, long-only
momentum), the board backtest, the live grading record for the
published board and the published index walls, and the gap study
record. Every claim on the page traces to one named study with its
sample and its headline numbers; a claim with no finished study
behind it is listed as not yet tested, never implied tested.

Reconstruction choices, stated as ours: (1) One entry per checked
claim, in the order the studies were assembled, each with the claim
in plain words, who made it, the verdict in plain words (held up /
partly held up / did not hold up / not yet tested / cannot be tested
on the records on hand, added 2026-10-30 for claims whose deciding
record does not exist on hand, each such entry naming the missing
record), the study's
sample, its headline numbers, and when the study was done. (2) The
two live grading entries (the published board's first-day grades
and the index walls) are read fresh from the grading record every
run and carry that record's own run time, so the page can never
quote a grading run that has been replaced. An older wall record
that still says the walls are ungraded is stale beside the newer
grading record and is never blended in. (3) One pair of entries in
the assembled record carried the same two numbers under two names
(a pullback-depth ranking and a fear-day ranking): the underlying
study record attaches those numbers to the pullback-depth ranking,
which includes fear days, so the page carries one entry for that
study, counted once, and says so on the entry. (4) Counts at the
top are counted from the entries themselves, with the total as the
denominator, never typed in separately. (5) Every time on this
page comes from a source record, never from the clock, so running
this script twice produces the same file.

Non-claims: this page does not claim any study it lists was run by
anyone but the maker named on the entry, does not turn a
calculation check (a rebuilt formula matching its author's own
worked examples) into a trading result, and does not publish any
number beyond what the named study record itself states.

Fail-closed rules: if any named source file is missing, if any
claim's headline numbers cannot be re-read from its named source
(the exact figures are checked in the source text), if the live
grading record's shape is not the shape this page states, or if
any words assembled here carry an internal file name or desk
wording, the refresh stops and publishes nothing.

Usage: python3 refresh_replicationwire.py
"""

import json
import os
import sys
from datetime import datetime

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_PATH = os.path.join(HERE, "replication-wire", "data.json")

SOURCE_WORDS = ("Our own study records: the forecast program's rerun analysis, "
                "the finished setup studies, the board backtest, and the live "
                "grading record for the published calls")

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "Femto", "Midna",
             "Codex", "ledger", "Spearman", "INCONCLUSIVE", "CONFIRMED DEAD",
             "PARK", "KILL", "FAIL", " bp", "bp/", "IC ", "MAR ", "CAGR")

try:
    from verdict_vocabulary import VERDICT_WORDS
except ImportError:  # producer stays runnable standalone
    VERDICT_WORDS = {
        "held": "Held up",
        "partly": "Partly held up",
        "did_not": "Did not hold up",
        "not_yet": "Not yet tested",
        "untestable": "Cannot be tested on the records on hand",
    }


def fail(msg):
    raise SystemExit("refresh_replicationwire: FAIL: " + msg)


def read(rel):
    path = os.path.join(WS, rel)
    if not os.path.exists(path):
        fail(f"source file missing: {rel}")
    with open(path, encoding="utf-8") as f:
        return f.read()


def check(rel, needles):
    text = read(rel)
    for n in needles:
        if n not in text:
            fail(f"{rel}: a claim's numbers could not be re-read "
                 f"(missing: {n!r})")


def load_json(rel):
    path = os.path.join(WS, rel)
    if not os.path.exists(path):
        fail(f"source file missing: {rel}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt_day(iso):
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return d.strftime("%B %-d, %Y")


def pct(x, signed=True):
    v = x * 100.0
    s = f"{v:+.2f}%" if signed else f"{v:.0f}%"
    return s


def claim(claim_text, maker, verdict, study, sample, result, when, checks,
          note=None):
    for rel, needles in checks:
        check(rel, needles)
    return {
        "claim": claim_text,
        "maker": maker,
        "verdict": verdict,
        "verdict_words": VERDICT_WORDS[verdict],
        "study": study,
        "sample": sample,
        "result": result,
        "when": when,
        "note": note,
    }


def build():
    claims = []

    A02 = "rea-master-index/analysis/02-FIDELITY-AND-EVIDENCE.md"
    A03 = "rea-master-index/analysis/03-CONFLICTS-AND-NOVELTY.md"
    SLATE = "terminal-lineup/LINEUP-DESIGN-SLATE-THREE-2026-10-28.md"
    INDEX = "rea-master-index/MASTER-INDEX.jsonl"
    BULL = "research/team2-bullflag/FINAL_VERDICT.md"
    VWAP = "research/vwap-mtf/FINAL_VERDICT.md"
    PULL = "research/pullback-uptrend/REPORT.md"
    WASH = "goals/ai-top50-pattern-study/files/WASHOUT-PULLBACK-BACKTEST-2026-10-24.md"
    TSMOM = "research/ts-momentum-clean/REPORT.md"
    BOARD = "morgue/BACKTEST-BOARD.md"
    PROGRESS = "terminal-lineup/BUILD-PROGRESS.md"

    # 1 Forecast Factory rerun
    claims.append(claim(
        "The first big forecast search found 1,217 forecast recipes worth trusting.",
        "Our forecast program, first search",
        "did_not",
        "A second search, planned and written down before it ran, re-grading every one of the 1,217 recipes on a second set of data",
        "1,217 recipes re-graded",
        "Only 63 of the 1,217 earned the top grade on the second look. 337 held up, 564 did not reproduce at all, and 253 could not be tested. The book of promoted recipes was frozen at 388 entries.",
        "Rerun graded October 2026",
        [(A02, ["1,217 promoted", "63 grade A",
                "337 confirmed, 564 not-replicated, 253 untestable"]),
         (A03, ["388 entries"])]))

    # 2 Picker replay
    claims.append(claim(
        "The named setup families are good enough to trade live.",
        "Our setup picker, checked against the forecast program's replay",
        "did_not",
        "A replay of every historical case the picker would have taken, checked family by family against a go-live bar set in advance",
        "296,093 replayed cases across 9 family definitions",
        "No setup family passed the go-live bar. The replay was itself reproduced case for case by a second run: its best family row scored an edge of +0.081 (range 0.029 to 0.133), and its baseline row scored -0.025.",
        "Replay run October 27, 2026",
        [(SLATE, ["296,093", "no setup family passed the go-live gate"]),
         (INDEX, ["forecast-p1-2026-10-27.md", "A3 edge +0.081"])]))

    # 3 Bull flag edge
    claims.append(claim(
        "A mechanical bull-flag breakout is the only setup you need: it makes money on its own.",
        "Casey (@Team2Trading), a trading educator",
        "did_not",
        "A frozen, pre-written test of the exact mechanical rule, run by us on index data",
        "611 trades over 677 trading days (QQQ, 2-minute bars, January 2, 2024 to October 5, 2026)",
        "It lost 0.0345% per trade after costs, with a strength score of -3.56 (past -2 is strong evidence, in the losing direction). It also lost on the SPY and IWM checks, and none of 6 variations of the rule changed the sign.",
        "Study finished October 2026",
        [(BULL, ["3.45bp/trade", "t = −3.56",
                 "n = 611 trades over 677 included days"])]))

    # 4 Bull flag doubling
    claims.append(claim(
        "Those bull-flag breaks can double a same-day call option, up over 100%.",
        "Casey (@Team2Trading), a trading educator",
        "did_not",
        "The same frozen bull-flag study, checking how far each break actually travelled",
        "611 mechanical breaks",
        "Only 4.3% of breaks moved far enough in the right direction to double a call; the claim needed 25%. The middle break moved just +0.026% before costs.",
        "Study finished October 2026",
        [(BULL, ["4.3%", "Median break moves +2.6bp gross"])]))

    # 5 Bull flag EMA filter. RC-13 pass, 2026-10-30: the
    # study's own per trade record was re-read in full. The
    # comparison it holds cannot decide the claim, and the
    # record that could decide it does not exist on hand, so
    # the claim is recorded as untestable with that record
    # named, not left pending.
    claims.append(claim(
        "Adding a 13/48 moving-average filter makes the bull flag better.",
        "Casey (@Team2Trading), a trading educator",
        "untestable",
        "The frozen bull-flag study's own per trade record, re-read in full for this wire",
        "611 trades on the record, 589 passing the filter and 22 not passing it",
        "Cannot be tested on the records on hand. Re-reading every trade on the study's record: the 589 filtered trades averaged -0.36 of their risk unit and the 22 unfiltered trades averaged -0.75, a difference in the filter's favour with a strength score of 1.34, below the 2.0 bar. The missing record is a sample of filter-rejected trades large enough to decide the comparison: the filter passes 96% of its own signals, so that sample would have to come from other symbols or other years, and no such record is on hand.",
        "Study finished October 2026; per trade record re-read October 30, 2026",
        [(BULL, ["589/611 signals (96%)", "Welch t = 1.34",
                 "n=22 unfiltered trades"]),
         ("research/team2-bullflag/trades.csv",
          ["ema_filter_pass", "r_multiple_net_5bp"])]))

    # 6 VWAP intraday
    claims.append(claim(
        "A multi-timeframe VWAP trend stack is a high-probability intraday trade.",
        "Anand (@TradesByAnand), a trading educator",
        "did_not",
        "A pre-registered test of the full stack in the 20 most liquid large stocks, run by us",
        "251 breakout trades over 1,699 trading days (January 2, 2020 to October 6, 2026)",
        "The breakout arm lost 0.026% per trade after costs, and lost 0.156% per trade in the held-back years. It could not beat random entries in the same stocks (strength score -0.06 against random). The study's own verdict: dead on the intraday horizon.",
        "Study dated October 6, 2026",
        [(VWAP, ["| T1 intraday breakout | 251 |", "−15.6bp",
                 "Welch t = **−0.06**"])]))

    # 7 VWAP confirmations
    claims.append(claim(
        "Strong volume plus an RSI above 50 add edge to that VWAP stack.",
        "Anand (@TradesByAnand), a trading educator",
        "did_not",
        "The same pre-registered VWAP study, comparing trades with and without the two confirmations",
        "251 breakout trades and 19 retest trades",
        "On breakouts, confirmed trades did worse than unconfirmed ones by 0.015% per trade (strength -0.53). On retests they did better by 0.054% (strength 1.73), below the +0.10% bar set before the test ran.",
        "Study dated October 6, 2026",
        [(VWAP, ["−1.5bp", "+5.4bp", "t=1.73", "+10bp"])]))

    # 8 VWAP swing. RC-13 pass, 2026-10-30: the deciding
    # record is the study's sealed holdout, and its own
    # binding protocol forbids opening it, so the claim is
    # recorded as untestable with that record named.
    claims.append(claim(
        "The same VWAP stack works if you hold for days instead of hours.",
        "Anand (@TradesByAnand), a trading educator",
        "untestable",
        "The swing arms of the same pre-registered VWAP study",
        "251 swing breakout trades and 19 swing retest trades on the spent windows",
        "Cannot be tested on the records on hand. On the windows the study spent, the swing arms were too small to decide (they could only have spotted an edge of 0.242% or 0.360% per trade, against a 0.20% ceiling). The missing record is the study's sealed final test set: its own written protocol forbids opening it before the earlier windows render a go verdict, they never did, and no ruling has opened it since.",
        "Study dated October 6, 2026; protocol re-read October 30, 2026",
        [(VWAP, ["INCONCLUSIVE", "24.2bp", "36.0bp"]),
         ("research/vwap-mtf/PREREGISTRATION.md",
          ["Sealed holdout", "never reused"])]))

    # 9 Textbook pullback cross-check
    claims.append(claim(
        "The textbook pullback, buying a dip to the 20/50-day lines in an uptrend, earns money.",
        "Trading-education sellers generally; the pattern is a staple of their courses",
        "did_not",
        "An independent cross-check on deep price history, run by our research program",
        "About 85,000 trades across 6,385 stocks including delisted ones, 2016 to 2026",
        "It earned +0.05 of its risk unit per trade, no better than random entries in the same stocks (+0.08) or random days inside uptrends (+0.03).",
        "Cross-check run October 27, 2026",
        [(A03, ["+0.05R/trade", "(n≈85k)", "+0.08R", "+0.03R",
                "6,385 names"])]))

    # 10 Dip-buying in uptrends
    claims.append(claim(
        "Buying dips in uptrends, a touch of the 20-day line with a trend filter, is a working strategy.",
        "A strategy question we set ourselves",
        "did_not",
        "A walk-forward test (rules fixed in advance, tested on later years) across the full stock list",
        "278,090 trades across 1,838 stocks, 2016 to 2026",
        "In the held-back years it shrank money at 37.8% a year, with a strength score of -18.26 against picking random days instead. All 4 versions of the trigger failed the same way. The study's verdict: kill it.",
        "Study dated October 7, 2026",
        [(PULL, ["278,090", "-37.8%", "-18.26", "KILL"])]))

    # 11 Washout pullback
    claims.append(claim(
        "Buying washed-out pullbacks to support in uptrending AI stocks pays better, per unit of fall, than simply holding the semiconductor fund SMH.",
        "Our AI top-50 pattern study, written up as a pre-registered test",
        "did_not",
        "A pre-registered backtest with its pass marks set before it ran",
        "60 trades, October 25, 2021 to October 23, 2026",
        "It grew at 9.84% a year with a worst fall of 27.25%: 0.361 of return per unit of fall, against SMH's 0.716. It failed 2 of its 4 pre-set marks and all 11 variations (best 0.517). It did pass its bear-market mark: its worst fall in the bear stretch was 1.21% against SMH's 45.30%, because it sat in cash on 98.66% of bear days.",
        "Report dated October 24, 2026",
        [(WASH, ["0.3611", "0.7161", "9.84%", "98.66%", "| 60 |"])]))

    # 12 Long-only momentum (parked)
    claims.append(claim(
        "Buying the past year's winners, long-only time-series momentum, beats picking stocks at random.",
        "A textbook claim, in the form a popular chart account published it",
        "partly",
        "A clean re-run on repaired data, after an earlier run was found to rest on faulty data",
        "1,838 stocks, 2016 to 2026, at 0.75% trading costs",
        "Half the claim held: the strongest-decile version's return per unit of fall was 0.58 in the held-back years, which clears its bar, and it scored a strength of 3.47 in the development years. But against random picks its strength was only 0.68, below the 2.0 bar, and the sealed final test (December 2024 to August 2026) has never been opened, so the verdict stays parked, neither proven nor buried. A known data fault pushes that 0.68 down; a sensitivity check bounds the corrected figure near 2.09.",
        "Clean re-run dated October 7, 2026",
        [(TSMOM, ["Verdict: PARK", "MAR clears (0.58)",
                  "t-stat FAILS (0.68)", "3.47", "t=2.09"])]))

    # 13 Pullback depth (merged with the fear-day entry: same study, same numbers)
    claims.append(claim(
        "How deep a pullback is, compared with that stock's own normal pullback size, ranks what the stock does next.",
        "Our own cross-check: a new candidate ranking found by the research program",
        "partly",
        "A cross-check on deep price history, tested separately in two eras, 2016 to 2022 and 2023 onward",
        "Deep price history, 2016 to 2026, fear days included",
        "The ranking pointed the same way in both eras: its agreement with later 20-day returns scored +0.026 in the first era and +0.031 in the second (strength 4.3 both times), and +0.062 at 60 days in the second era (strength 9.8). That is a real pattern on one family of data, still an unproven candidate, not a validated edge.",
        "Cross-check run October 27, 2026",
        [(A03, ["F3 pullback", "IC +0.026/+0.031 (t 4.3/4.3) at 20d",
                "60d 2023+ IC +0.062, t 9.8", "incl. fear days"])],
        note=("One study, counted once: the forecast program's own plan for a "
              "fear-day ranking prints these same two numbers for it, because "
              "fear days are part of this same study. The study record itself "
              "attaches the numbers to the pullback-depth ranking.")))

    # 14 Board score
    claims.append(claim(
        "The rebuilt confluence board's 0-to-100 score ranks the returns that follow.",
        "A vendor's confluence design (Leadr), rebuilt by us with its settings verbatim and our own scoring arithmetic",
        "did_not",
        "A backtest of every scored week on record",
        "52,968 scored rows over 29 weekly dates, April 8 to October 23, 2026",
        "The score's ranking agreed with later returns not at all: the rank agreement was -0.014 at 1 day, -0.021 at 5 days and -0.010 at 21 days, which is zero for practical purposes.",
        "Backtest finished October 2026",
        [(BOARD, ["52,968 scored rows",
                  "1d −0.014, 5d −0.021, 21d −0.010"])]))

    # 15 Board gate
    claims.append(claim(
        "Even if the score does not rank, the board's pass-every-check gate picks better stocks.",
        "The same rebuilt confluence board",
        "partly",
        "The same backtest, comparing the stocks that passed every check with the rest",
        "52,968 scored rows over 29 weekly dates, April 8 to October 23, 2026",
        "At 21 days the passed group averaged +2.41% against +0.52% for the rest (+0.61% against the S&P 500 fund, versus -1.12%). But its middle stock did worse than the fund at every horizon (-0.16%, -0.36%, -1.16%): the average is carried by a right tail of big winners, over one 6.5-month window.",
        "Backtest finished October 2026",
        [(BOARD, ["+2.41%", "+0.52%"]),
         (A03, ["+2.41% vs +0.52%", "+0.61% vs −1.12%",
                "−0.16%, −0.36%, −1.16%"])]))

    # 16 Live board grades (read fresh from the grading record)
    sc = load_json("morgue/output/scorecard.json")
    gen = sc.get("generated_at")
    if not gen:
        fail("scorecard: no generated_at on the grading record")
    pub = sc["board"]["published"]["horizons"]
    qual = sc["board"]["qualified"]["horizons"]
    if pub["1d"]["state"] != "graded" or qual["1d"]["state"] != "graded":
        fail("scorecard: the 1-day board grades are not in the graded state this page states")
    if pub["5d"]["state"] != "not_yet_graded" or pub["21d"]["state"] != "not_yet_graded":
        fail("scorecard: the 5-day or 21-day board grades have landed, so this page's wording is stale")
    p1, q1 = pub["1d"], qual["1d"]
    claims.append({
        "claim": "The board's live published stock calls rise more often than not after 1 day.",
        "maker": "Our own published board, graded live",
        "verdict": "partly",
        "verdict_words": VERDICT_WORDS["partly"],
        "study": "The live grading record for every call the board has published, re-read fresh for this page",
        "sample": f"{p1['n_mature']} published calls graded at 1 day so far",
        "result": (f"So far, early and small: {p1['n_mature']} published calls graded at 1 day, "
                   f"{round(p1['hit_rate'] * 100):.0f}% rose, averaging {pct(p1['mean'])}. "
                   f"The pass-every-check group: {q1['n_mature']} graded, "
                   f"{round(q1['hit_rate'] * 100):.0f}% rose, averaging {pct(q1['mean'])}. "
                   f"The 5-day grades first land after the October 30, 2026 close and the "
                   f"21-day grades after the November 23, 2026 close."),
        "when": f"Grading record run {fmt_day(gen)}",
        "note": None,
    })

    # 17 Index walls (read fresh from the grading record)
    mp = sc.get("map") or {}
    grades = mp.get("grades") or []
    if mp.get("state") != "graded" or mp.get("cards_graded") != len(grades) or not grades:
        fail("scorecard: the index-wall grades are not in the graded shape this page states")
    n_cards = len(grades)
    call_held = sum(1 for g in grades if g.get("call_wall_held"))
    put_held = sum(1 for g in grades if g.get("put_wall_held"))
    flip_ok = sum(1 for g in grades if g.get("flip_respected"))
    claims.append({
        "claim": "Big options walls hold, and the level where the picture flips is respected.",
        "maker": "A published positioning construction (SpotGamma's), rebuilt and graded by us",
        "verdict": "partly",
        "verdict_words": VERDICT_WORDS["partly"],
        "study": "The live grading record for the published index positioning cards",
        "sample": f"{n_cards} index cards graded so far",
        "result": (f"A tiny sample, stated as counts: the upper wall held on {call_held} of "
                   f"{n_cards} cards, the lower wall held on {put_held} of {n_cards}, and the "
                   f"flip level was respected on {flip_ok} of {n_cards}."),
        "when": f"Grading record run {fmt_day(gen)}",
        "note": None,
    })

    # 18 ChartsLector ranker
    claims.append(claim(
        "A chart ranker's 0.736 ranking agreement is a forecasting result.",
        "The ChartsLector chart-ranking lane",
        "did_not",
        "An audit of the ranker and its data, inside our research analysis",
        "One fitted snapshot of 55 names from the vendor",
        "Ruled not a prediction: the 0.736 measures agreement with one fitted 55-name vendor snapshot, not agreement with future returns, and it was reached only after three rotation mistakes and a split-adjustment fault in the ranker's data were corrected.",
        "Audit finished October 2026",
        [(A03, ["0.736", "not forward-return prediction",
                "agreement with one fitted"])]))

    # 19 TheStrat posted proof. RC-13 pass, 2026-10-30:
    # recorded as untestable with the missing record named.
    claims.append(claim(
        "TheStrat's posted proof, its trade recaps, backs its rule system.",
        "TheStrat, a trading-rules vendor",
        "untestable",
        "Our evidence audit of the vendor's full teardown",
        "3,615 teardown entries examined",
        "Cannot be tested on the records on hand: the teardown is the largest rule extraction in our research files and carries zero test entries and zero evidence entries, and its one posted proof item is a single trade recap (+$337.02, -21%), one anecdote, not a test. The missing record is any graded record of the system's own calls (a test or evidence entry for the rule system); none exists in the teardown or anywhere else on hand.",
        "Evidence audit finished October 2026; re-read October 30, 2026",
        [(A02, ["3,615", "(0 test, 0 ev)", "+$337.02 / −21%"])]))

    # 20 Big bundle products. RC-13 pass, 2026-10-30:
    # recorded as untestable with the missing record named.
    claims.append(claim(
        "The big bundle products' mechanisms work as sold.",
        "Nansen, FlashAlpha, OptionsCartel, GexRadar, TapeBoard and TradeEcho",
        "untestable",
        "Our evidence audit of each vendor's teardown",
        "Six teardowns, 2,042 to 3,535 entries each",
        "Cannot be tested on the records on hand: the share of each teardown that is tests or evidence is 0.7% for Nansen (3,535 entries), 0.1% for FlashAlpha (2,047) and OptionsCartel (1,942), and 0.2% for GexRadar (2,338), TapeBoard (2,560) and TradeEcho (2,042), with zero tests in each. The missing record is a test record for even one named mechanism per product that this wire could re-run; the teardowns describe mechanisms but carry no test entries, so there is nothing on hand to test the claim against. Their mechanisms are unproven either way, not disproven.",
        "Evidence audit finished October 2026; re-read October 30, 2026",
        [(A02, ["0.7% (15 test, 9 ev)", "0.1% (0 test, 2 ev)",
                "2,338 / 2,560 / 2,042", "zero tests"])]))

    # 21 The 15.87 calculation
    claims.append(claim(
        "The 15.87 expected-move formula (the day's expected move equals the close times the fear gauge divided by 15.87) reproduces its author's own published values.",
        "Azrael Options, author of the 15.87 rule",
        "held",
        "Our rebuild of the formula, checked against the author's own worked examples and every filed map",
        "The author's published example values, plus every filed map on record",
        "It reproduces the author's own values exactly: expected moves of 73.0 and 81.5, and a weekly move of 182.2, and every filed map recomputes exactly. This grades the calculation only: it says nothing about whether trading on the move makes money.",
        "Checked October 2026",
        [(PROGRESS, ["EM 73.0 and 81.5, weekly 182.2"]),
         (A03, ["15.87 map: Azrael's published construction"])]))

    # 22 Nine rebuilt calculators
    claims.append(claim(
        "Nine rebuilt vendor calculators give the same answers as hand-worked examples.",
        "A second, independent rebuild of several trading calculators",
        "held",
        "Hand-worked test cases for each calculator, including a positioning measure built from a hand-computed option formula, a spread payoff priced at three prices, and a confluence score",
        "9 hand-worked cases",
        "All 9 of 9 cases pass, with the sources for each case pinned by fingerprint in the results. This grades the calculators' arithmetic against worked examples, not any trading claim.",
        "Checked October 2026",
        [(A02, ["9/9 fixture cases PASS"])]))

    # 23 Two rebuilds cross-checked
    claims.append(claim(
        "Two independent rebuilds of the same vendor mechanisms agree with each other.",
        "Our calculator engine and the second independent rebuild, cross-checked by us",
        "partly",
        "A cross-check: one rebuild's test cases run against the other rebuild, case by case",
        "Every case where both rebuilds cover the same mechanism",
        "11 cases agree and are pinned as tests. Every disagreement is named: two were faults in our engine, fixed at the source; two were ruled faults in the second rebuild, on the vendor's own published evidence; and the cases only one rebuild covers were left uncovered, not papered over.",
        "Cross-check finished October 2026",
        [(A02, ["11 test functions in that file", "cured at the source",
                "CODEX-WRONG on vendor evidence", "are not faked here"])]))

    # 24 TheStrat replica
    claims.append(claim(
        "TheStrat's 71-rule bar-labelling system can be rebuilt faithfully from its published rules.",
        "Our replica of the vendor's published rules",
        "held",
        "A working replica tested against the rule set, including the vendor's own worked examples",
        "21 tests, including the vendor's own example cases",
        "The replica passes 21 of 21 tests. This grades whether the labels match the published rules; whether following the system makes money is untested, and its forward record does not exist yet.",
        "Checked October 2026",
        [(SLATE, ["working replica passes 21 of 21 tests including "
                  "the vendor's own golden cases"])]))

    # 25 Golden sweeps. Recounted 2026-10-30 (engine refresh
    # cure): the tape record was recounted again from the wire's
    # own page record; its pre-registered decision needs 30
    # recorded sessions and 5 stand, with 2 golden prints now on
    # the record, so the claim stays untestable today with the
    # missing record named.
    claims.append(claim(
        "Golden sweep prints, a sweep at least as large as its contract's whole open interest with at least $1 million in it, are a signal worth following.",
        "An options-tape vendor tag, rebuilt by us",
        "untestable",
        "Our recording of every options print on the three index funds, checked for golden sweeps",
        "5 recorded trading days so far on the index tape record, freshest session October 30, 2026, with two golden prints found",
        "Cannot be tested on the records on hand: two golden prints stand on the recorded sessions, but neither has the following sessions a grade needs, so there is nothing gradeable yet. The missing record is the rest of the tape its own decision rule requires: 25 more recorded sessions to reach 30, with the decision date already set at December 8, 2026. Until a golden print's following sessions exist, no verdict either way is possible.",
        "Recording started October 2026; tape record recounted October 30, 2026",
        [("terminal-lineup/site/golden-sweep-wire/data.json",
          ["\"golden_prints\": 2", "\"sessions_recorded\": 5",
           "\"decision_date\": \"2026-12-08\""])]))

    # 26 The router's record. RC-13 pass, 2026-10-30:
    # recorded as untestable with the missing record named.
    claims.append(claim(
        "The forecast program's one-verdict-per-stock router (Buy, Wait, Avoid, or Sit Out) has a track record.",
        "Our forecast program",
        "untestable",
        "The router's own published record so far",
        "7 trading sessions of record, none of them graded",
        "Cannot be tested on the records on hand: its record is 7 sessions and provisional, and the program's own plan requires its card to say exactly that, in words, until the record grows up. The missing record is a graded track record for this router: sessions of its verdicts with their outcomes graded against what the stocks did next, in the number its own maturity bar requires. No graded record for it exists on hand.",
        "Record as of October 2026; re-read October 30, 2026",
        [(SLATE, ["record is 7 sessions and provisional"])]))

    # 27 Gap fill (read from the gap study record)
    gs = load_json("morgue/output/studies_card.json")
    gf = gs.get("gap_fill") or {}
    if gf.get("state") != "graded" or not gf.get("n"):
        fail("studies record: the gap study is not in the graded shape this page states")
    bands = gf["partitions"]["by_band"]
    small, big = bands["<1%"], bands["1-2%"]
    if small["n"] + big["n"] != gf["n"] or small["fills"] + big["fills"] != gf["fills"]:
        fail("studies record: the gap study's size split does not add up to its total")
    claims.append({
        "claim": "Overnight gaps usually fill.",
        "maker": "A common trading saying, measured by our gap study",
        "verdict": "partly",
        "verdict_words": VERDICT_WORDS["partly"],
        "study": "Our gap study: every overnight gap in the index funds on record, checked for a same-day fill",
        "sample": f"{gf['n']} gap cases graded",
        "result": (f"Not usually: {gf['fills']} of {gf['n']} gaps filled "
                   f"({gf['frequency'] * 100:.1f}%). By size: gaps under 1% filled "
                   f"{small['fills']} of {small['n']} ({small['frequency'] * 100:.1f}%), "
                   f"and gaps of 1 to 2% filled only {big['fills']} of {big['n']} "
                   f"({big['frequency'] * 100:.1f}%)."),
        "when": f"Study record made {fmt_day(gs['generated_at'])}",
        "note": None,
    })

    counts = {"total": len(claims), "held": 0, "partly": 0,
              "did_not": 0, "not_yet": 0, "untestable": 0}
    for c in claims:
        counts[c["verdict"]] += 1
    if counts["total"] != 27:
        fail(f"expected 27 claims on the wire, built {counts['total']}")

    out = {
        "tool": "Replication Wire",
        "source": SOURCE_WORDS,
        "state": "published",
        "counts": counts,
        "grading_run_at": gen,
        "claims": claims,
    }

    blob = json.dumps(out, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in blob:
            fail(f"assembled output carries forbidden wording: {bad!r}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"refresh_replicationwire: wrote {OUT_PATH} with "
          f"{counts['total']} claims (held {counts['held']}, partly "
          f"{counts['partly']}, did not {counts['did_not']}, "
          f"not yet {counts['not_yet']}, "
          f"untestable {counts['untestable']})")


if __name__ == "__main__":
    build()
