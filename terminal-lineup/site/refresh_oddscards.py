#!/usr/bin/env python3
"""Refresh the Odds Cards data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: our own finished study record, read exactly as it
stands: the historical replay of every case a named setup picker
would have taken (296,093 cases across 3,446 stocks, December 20,
2019 to October 15, 2026, each case closed at its target, its stop,
or after 20 trading days), together with the second run that
re-checked the replay family by family and applied the go-live bar
(each date counting once, strength score at least 2). Every figure
on a card is read from that record by this script; nothing is
re-derived and nothing is typed in from anywhere else.

Reconstruction choices, stated as ours: (1) One card per setup
definition in the record (9 cards), in the record's own order, each
with the setup in plain words, its case count, how often its target
was reached (with the record's range), its average outcome, the
random-entry comparison for the same stocks, the edge over that
comparison (with the record's range), and the go-live verdict
printed on the card: the bar, and the strength score the family
actually reached under the second run. (2) The slices printed under
a family are exactly the slices the record itself carries: the
market-mood split (calm and rising, mixed, falling), the day-type
split (fear days and other days), the six reward-to-risk bands, the
extra condition splits the record carries for the two base families
only, and the model check the record ran for each of the three
family groups. (3) No slice with fewer than 30 cases shows a rate:
it shows its count only. The record's smallest slice holds 49
cases, so no slice is thinned on this page today, but the rule is
enforced here, not assumed. (4) The families overlap by design (the
narrower ones are subsets of the wider ones), so their case counts
add to 282,438, not to the 296,093 total; the total is the record's
own count of every case replayed, and the page says the families
overlap. (5) No time on this page comes from the clock: the replay
date comes from the record, so running this script twice produces
the same file.

Non-claims: this page does not publish any number beyond what the
replay record itself states, does not turn a family's average
outcome into a promise about any single future case, and does not
call any family ready to trade: the record's own verdict is that no
family passed the go-live bar, and every card says so.

Fail-closed rules: if any record file is missing, if the record's
family count is not 9 or its case total is not the published
296,093, if the replay's own written table or the second run's
table disagrees with the machine record on any card figure (cases,
average outcome, comparison, edge), if any family reaches the
go-live bar the page says none reached, if a slice count under 30
would carry a rate, or if any words assembled here carry an
internal file name or internal wording, the refresh stops and
publishes nothing.

Usage: python3 refresh_oddscards.py
"""

import json
import os
import re

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", ".."))
RECORD_DIR = os.path.join(WS, "terminal-lineup", "records",
                          "picker-replay-2026-10-27")
REPLAY_JSON = os.path.join(RECORD_DIR, "picker-replay-2026-10-27.json")
REPLAY_MD = os.path.join(RECORD_DIR, "picker-replay-2026-10-27.md")
FACTORY_MD = os.path.join(RECORD_DIR, "forecast-p1-2026-10-27.md")
SLATE = os.path.join(WS, "terminal-lineup",
                     "LINEUP-DESIGN-SLATE-THREE-2026-10-28.md")
OUT_PATH = os.path.join(HERE, "odds-cards", "data.json")

SOURCE_WORDS = ("Our own finished study records: a replay of every historical "
                "case a named set of stock setups would have produced, and the second "
                "run that re-checked it family by family against a go-live "
                "bar set in advance")

PUBLISHED_TOTAL = 296093
PUBLISHED_FAMILIES = 9
BAR_STRENGTH = 2.0
THIN = 30

FORBIDDEN = (".json", ".md", ".py", ".jsonl", "morgue", "ledger", "sleeve",
             "desk", "Spearman", "Newey", "t_NW", "picker_replay",
             "Femto", "Midna", "Codex", "A0", "A1", "A2", "A3",
             "B0", "B1", "B2", "B3", "C0")

FAMILIES = [
    ("A0", "Uptrend pullback to the rising lines",
     "A stock in an uptrend that pulled back to its rising 21-day or "
     "50-day average line."),
    ("A1", "Uptrend pullback into support",
     "The same uptrend pullback, landing on a swing support level or "
     "on the level of a prior breakout."),
    ("A2", "Uptrend pullback into support on a fear day",
     "The pullback into support, on a day when both the stock and the "
     "S&P 500 fund closed down."),
    ("A3", "Uptrend pullback into support on a fear-gauge spike",
     "The pullback into support, on a day when the fear gauge jumped "
     "at least 10% or stood above 22."),
    ("B0", "Deep reset with a higher low",
     "A stock down 35% to 80% from its high that stopped falling and "
     "made a higher low."),
    ("B1", "Deep reset that took back its 50-day line",
     "The deep reset, after the stock closed back above its 50-day "
     "average line."),
    ("B2", "Deep reset that closed over its base line",
     "The deep reset, after the stock closed over the line its base "
     "was built on."),
    ("B3", "Deep reset with rising volume and improving strength",
     "The deep reset that took back a line, with volume rising on the "
     "way up and the stock's strength against the S&P 500 fund "
     "improving."),
    ("C0", "Sweep under a swing low that closed back over it",
     "A stock that dipped under a recent swing low during the day and "
     "closed back above that low."),
]

CONDITION_WORDS = {
    "a_breakout_level": "At a prior breakout level",
    "a_hhhl": "Higher highs and higher lows in place",
    "a_ma21": "Above its 21-day line",
    "a_swing_confluence": "At a swing support area",
    "b_below_falling_200": "Below a falling 200-day line",
    "b_divergence": "A momentum divergence showing",
    "b_over_base": "Over the base line",
    "b_reclaim50": "Taking back its 50-day line",
    "b_rs_improving": "Strength against the market improving",
    "b_upvol": "Rising volume",
}

REGIME_WORDS = {
    "Risk-on": "Calm and rising markets",
    "Mixed": "Mixed markets",
    "Risk-off": "Falling markets",
}

GROUP_OF = {"A0": "A", "A1": "A", "A2": "A", "A3": "A",
            "B0": "B", "B1": "B", "B2": "B", "B3": "B", "C0": "C"}


def fail(msg):
    raise SystemExit("refresh_oddscards: FAIL: " + msg)


def read_text(path, label):
    if not os.path.exists(path):
        fail(f"record file missing: {label}")
    with open(path, encoding="utf-8") as f:
        return f.read()


def rate_or_none(n, rate):
    return rate if n >= THIN else None


def slice_row(label, s, with_base=False):
    row = {"label": label, "n": s["n"],
           "rate": rate_or_none(s["n"], s.get("rate")),
           "mean_r": s["mean_r"]}
    if with_base:
        row["base_r"] = s["base_r"]
    return row


def build():
    replay = json.loads(read_text(REPLAY_JSON, "replay record"))
    replay_md = read_text(REPLAY_MD, "replay written table")
    factory_md = read_text(FACTORY_MD, "second run record")
    slate = read_text(SLATE, "lineup design")
    if "no setup family passed the go-live gate" not in slate:
        fail("the design record no longer states that no family passed")

    if replay.get("cases") != PUBLISHED_TOTAL:
        fail(f"record case total is {replay.get('cases')}, "
             f"not the published {PUBLISHED_TOTAL}")
    defs = replay.get("definitions") or {}
    if len(defs) != PUBLISHED_FAMILIES:
        fail(f"record carries {len(defs)} family definitions, "
             f"not {PUBLISHED_FAMILIES}")
    if [c for c, _, _ in FAMILIES] != list(defs.keys()):
        fail("the record's family order differs from the published order")
    if f"{PUBLISHED_TOTAL} cases" not in replay_md.replace(",", ""):
        fail("the replay's written record does not state the case total")

    # The second run's table: per family, cases, average, comparison,
    # edge, and the date-weighted strength score behind the verdict.
    factory = {}
    for line in factory_md.splitlines():
        m = re.match(r"\| ([ABC]\d) \| (\d+) \| (-?[\d.]+) \| (-?[\d.]+) \| "
                     r"(-?[\d.]+) \[[^\]]*\] \| [^|]* \| "
                     r"(-?[\d.]+) \((-?[\d.]+), (\d+);", line)
        if m:
            factory[m.group(1)] = {
                "n": int(m.group(2)), "mean_r": float(m.group(3)),
                "base_r": float(m.group(4)), "edge_r": float(m.group(5)),
                "weighted_r": float(m.group(6)),
                "strength": float(m.group(7)), "dates": int(m.group(8)),
            }
    if set(factory) != {c for c, _, _ in FAMILIES}:
        fail("the second run's table does not cover all 9 families")

    # The replay's own written definitions table must agree on cases
    # and edge for every family.
    md_rows = {}
    for line in replay_md.splitlines():
        m = re.match(r"\| ([ABC]\d) \| [^|]* \| (\d+) \| [\d.]+ \[[^\]]*\] \| "
                     r"-?[\d.]+ ± [\d.]+ \| -?[\d.]+ \| (-?[\d.]+) ", line)
        if m:
            md_rows[m.group(1)] = (int(m.group(2)), float(m.group(3)))
    if set(md_rows) != {c for c, _, _ in FAMILIES}:
        fail("the replay's written table does not cover all 9 families")

    families = []
    row_sum = 0
    for code, name, setup in FAMILIES:
        d = defs[code]
        a = d["all"]
        f = factory[code]
        for field in ("n", "mean_r", "base_r", "edge_r"):
            if a[field] != f[field]:
                fail(f"{code}: the second run's {field} ({f[field]}) "
                     f"disagrees with the replay record ({a[field]})")
        if md_rows[code] != (a["n"], a["edge_r"]):
            fail(f"{code}: the replay's written table disagrees with "
                 f"its machine record")
        if f["strength"] >= BAR_STRENGTH:
            fail(f"{code}: a family reached the go-live bar, so the "
                 f"page's verdict wording is stale")
        row_sum += a["n"]

        regimes = [slice_row(REGIME_WORDS[k], d[k])
                   for k in ("Risk-on", "Mixed", "Risk-off")]
        days = [slice_row("Fear days (the S&P 500 fund down at least 1%)",
                          d["fear_spy_down1"], with_base=True),
                slice_row("All other days", d["calm"], with_base=True)]
        bands = [{"band": b["rr"], "n": b["n"],
                  "rate": rate_or_none(b["n"], b["rate"]),
                  "mean_r": b["mean_r"], "base_r": b["base_r"]}
                 for b in replay["rr_bands"][code]]
        conditions = None
        group = GROUP_OF[code]
        if group in replay.get("conditions", {}) and code in ("A0", "B0"):
            conditions = []
            for c in replay["conditions"][group]:
                if c["condition"] not in CONDITION_WORDS:
                    fail(f"{code}: a condition split has no plain words: "
                         f"{c['condition']}")
                conditions.append({
                    "label": CONDITION_WORDS[c["condition"]],
                    "n_with": c["n_with"],
                    "rate_with": rate_or_none(c["n_with"], c["rate_with"]),
                    "r_with": c["r_with"],
                    "rate_without": c["rate_without"],
                    "r_without": c["r_without"],
                })
        gate = replay["models"][group]["gate"]
        if gate["pass"]:
            fail(f"group {group}: the model check passed, so the "
                 f"page's wording is stale")
        families.append({
            "name": name,
            "setup": setup,
            "n": a["n"],
            "hits": a["hits"],
            "rate": rate_or_none(a["n"], a["rate"]),
            "rate_lo": a["lo"], "rate_hi": a["hi"],
            "mean_r": a["mean_r"], "se_r": a["se_r"],
            "base_r": a["base_r"],
            "edge_r": a["edge_r"],
            "edge_lo": a["edge_lo"], "edge_hi": a["edge_hi"],
            "verdict": "Did not pass the go-live bar",
            "bar_words": ("To pass, the edge over random entries had to "
                          "hold up with each trading date counting once, "
                          "at a strength score of at least 2."),
            "reached_words": (
                f"It reached a strength score of {f['strength']:+.2f} on a "
                f"date-weighted edge of {f['weighted_r']:+.3f} of its risk "
                f"unit, over {f['dates']:,} trading dates."),
            "regimes": regimes,
            "days": days,
            "rr_bands": bands,
            "conditions": conditions,
            "model_words": (
                f"The model check on this family group also failed: its "
                f"top tenth of cases did not beat random entries with its "
                f"range clear of zero, and its forecasts were off by up "
                f"to {gate['worst_calibration_pts']:.1f} points in a tenth "
                f"against a 5-point limit."),
        })

    best = max(families, key=lambda x: x["edge_r"])
    out = {
        "tool": "Odds Cards",
        "source": SOURCE_WORDS,
        "state": "published",
        "proving_state": "Backed by a finished study",
        "proving_words": ("The numbers on these cards are the counted "
                          "result of a finished study: the replay below, "
                          "re-checked by a second run."),
        "replay_date": "October 27, 2026",
        "window_words": "December 20, 2019 to October 15, 2026",
        "headline": {
            "total_cases": replay["cases"],
            "families": len(families),
            "passed": 0,
            "names": replay["names"],
            "random_entries": replay["random_entries"],
            "family_rows_sum": row_sum,
        },
        "best_words": (
            f"The strongest family was \"{best['name'].lower()}\": an edge "
            f"of {best['edge_r']:+.3f} of its risk unit over random entries "
            f"(range {best['edge_lo']:+.3f} to {best['edge_hi']:+.3f}), and "
            f"it still did not pass."),
        "how_words": (
            "How each case was played: bought at the next open after the "
            "signal day's close; sold at the next open after a close under "
            "the stop level (the level minus a quarter of the stock's "
            "usual daily range); the target was the nearest real "
            "resistance at least three quarters of that range away; if a "
            "day hit both, the stop counted first; anything still open "
            "after 20 trading days was closed. Every outcome is stated in "
            "risk units: the gain or loss divided by the amount risked to "
            "the stop. The comparison on each card is random entries in "
            "the same stocks, played under the same exits."),
        "families": families,
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
    print(f"refresh_oddscards: wrote {OUT_PATH} with {len(families)} cards, "
          f"{replay['cases']} cases, 0 passed the go-live bar")


if __name__ == "__main__":
    build()
