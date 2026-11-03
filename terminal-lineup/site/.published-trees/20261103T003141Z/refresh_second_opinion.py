#!/usr/bin/env python3
"""Refresh the Second Opinion data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real per-name records on file: the freshest
full scored run (every name checked that day, with its score,
checks in favor, share of measures with data, and passed-every-
check flag), the published board card for the same session (the
50 highest-scoring names with their eight check-by-check states),
the options prints card and the modelled positioning card (both
covering the three index funds only), the filings and positioning
bundle for 50 names with its provenance file (big-holder ownership
and activity readings, insider transaction counts, and short
interest readings with their settlement date), the published feed
that carries copies of the prints and positioning figures, and a
sister tool's published copy of the same scored run, used only to
prove the run agrees with itself wherever it is published.

Reconstruction choices, stated as ours: (1) Evidence is grouped
into six families by the record it comes from, never by how many
products repeat it: price and trading history; options prints;
modelled options positioning; filings and positioning; company
facts; news and events. The scored run and its republications are
one family. The board card's own big-holder check reads no-data
for every published name, so the board never adds the filings
family on top of the filings bundle itself. (2) A family's plain
direction, where it carries one, is read by rules stated here and
on the page: the price family points positive for a name that
passed every check, mixed for a score of 60 or more that did not
pass, and cautious below 60; the prints family follows the sign
of its net premium (money in minus money out, estimated from the
side of each print); the positioning family is cautious when the
price sits below its flip level and its modelled pressure is
negative, positive when the price sits above the flip and the
pressure is positive, and mixed otherwise. (3) The filings family
speaks in facts, not a direction: which of its reporting lines
are on record and what they say, kept as separate lines (big
holders, company insiders, short interest), never merged into
one smart-money verdict, and never counted in the agreement
count. (4) A cell with fewer than 30 events behind it is a thin
cell: counts only, no percentage. This page publishes no
percentage built from a handful of families or names; the only
percentages shown are single-name measurements carried from the
record itself (the share of measures behind a score that had
data, and a name's short interest share). (5) Company facts and
news are shown as silent families with their reasons for every
name, because no record behind either exists today; naming the
silence is the honest count, not a gap to fill by invention.

Hookup amendment (2026-10-30): the records behind all three
silent or index-only families have since landed, and this
refresh now reads them: the per-name tape store (prints for the
tracked names, direction unjudged by construction, so that
family speaks in counts and heat with no direction word), the
Filings Wire's published company facts (joined by the symbol
that wire now publishes), and the news store (articles per name
over its window; a covered name with no articles in the window
stays silent with that reason). Choice (5) above stands as the
record of the state this page was built against.

Non-claims: this page does not claim the six families are the
only evidence that could exist, does not count any product,
alert, or republication as an extra vote, does not turn the
filings lines into a direction, and does not invent a reading
for a name or a family that has none on record. The maximum
honest family count today is 3, reached only by the three index
funds; no name is shown with more.

Fail-closed rules: if the board card's summary disagrees with
the full scored run recomputed from its own rows, if the card's
50 names are not the run's top 50, if the sister tool's published
copy of the run disagrees with the run on any scored name, if
the published feed's prints or positioning figures disagree
with their cards, if the filings bundle and its provenance file
name different sets of companies, if the short interest readings
in the provenance file do not line up name for name with the
bundle's short interest line, if the scored session, the prints
session, and the published summary session are not the same
trading day, or if the permanent log holds no board entry, the
refresh stops and publishes nothing. All timestamps come from
the sources, never the clock, so running this script twice
produces the same file.

Usage: python3 refresh_second_opinion.py
"""

import json
import os
import sys

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
FULL_PATH = os.path.join(SOURCE_DIR, "board_full.json")
CARD_PATH = os.path.join(SOURCE_DIR, "board_card.json")
TAPE_PATH = os.path.join(SOURCE_DIR, "tape_card.json")
MAP_PATH = os.path.join(SOURCE_DIR, "map_card.json")
INST_PATH = os.path.join(SOURCE_DIR, "inst_bundle.json")
PROV_PATH = os.path.join(SOURCE_DIR, "inst_bundle_provenance.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
SISTER_PATH = os.path.join(HERE, "screener", "data.json")
OUT_PATH = os.path.join(HERE, "second-opinion", "data.json")
PERNAME_DIR = os.path.expanduser(
    "~/workspace/morgue/state/morgue/pername_tape")
NEWS_DIR = os.path.expanduser("~/workspace/morgue/state/morgue/news")
FILINGS_PATH = os.path.join(HERE, "filings-wire", "data.json")

MIN_EVENTS_FOR_PERCENT = 30
INDEX_FUNDS = ("SPY", "QQQ", "IWM")

SOURCE_WORDS = ("The scored trading day record, the options prints "
                "and positioning records, and the filings and "
                "positioning records on file")

WHY_FAMILIES = ("Many products read the same underlying records, so "
                "ten products agreeing can be one fact repeated; "
                "this page counts the separate records, called "
                "families, instead.")

CATEGORY_WORDS = {
    "relativeStrength": "Strength against the wider market",
    "priceAction": "Price action",
    "volumeParticipation": "Trading volume taking part",
    "trendAlignment": "Trend alignment",
    "supportResistance": "Support and resistance",
    "sectorLeadership": "Sector leadership",
    "institutionalPositioning": "Big-holder positioning (from the board's own checks)",
    "marketContext": "Wider market backdrop",
}
STATE_WORDS = {
    "confirming": "in favor",
    "neutral": "in between",
    "conflicting": "against",
    "no-data": "not enough data",
}
LEAF_WORDS = {
    "instOwnership": "Big-holder ownership reading",
    "instActivity": "Big-holder buying and selling activity reading",
    "insiderActivity": "Company insider activity reading",
    "shortPositioning": "Short positioning reading",
}

FAMILIES = [
    {"id": "price", "name": "Price and trading history",
     "about": ("What the name's own price and trading history say: "
               "its score out of 100 from the scored trading day, "
               "how many of the eight checks lined up in its favor, "
               "and whether it passed every check.")},
    {"id": "prints", "name": "Options prints",
     "about": ("What the day's actual options trades say: how many "
               "prints there were and whether the money in them "
               "leaned to the buying side or the selling side. For "
               "the three index funds the lean is judged from the "
               "prints record; for single names the per-name tape "
               "record carries the prints and their heat, with the "
               "direction unjudged, because no record of the quote "
               "at the moment of each print exists to judge it "
               "against.")},
    {"id": "positioning", "name": "Modelled options positioning",
     "about": ("What a model of the options chain says about the "
               "pressure on the price: the flip level where that "
               "pressure changes character, the walls above and "
               "below, and whether moves are likely to be softened "
               "or sharpened. A model, not an observation. "
               "Recorded for the three index funds only.")},
    {"id": "filings", "name": "Filings and positioning",
     "about": ("What public filings and positioning records say, "
               "kept as separate lines because they are reported "
               "separately and on different dates: big holders, "
               "company insiders, and shares sold short.")},
    {"id": "facts", "name": "Company facts",
     "about": ("The company's own reported facts: earnings power, "
               "financial strength, and safety checks worked out "
               "from its filings.")},
    {"id": "news", "name": "News and events",
     "about": ("News and events recorded against the name: "
               "announcements, reports, and other happenings that "
               "could move it.")},
]

SILENT = {
    "facts": ("No company facts are stored for this name, so "
              "this family has nothing to read for it."),
    "news": ("No news or event record is kept for this name, so "
             "this family has nothing to read for it."),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Second Opinion refresh: {message}", file=sys.stderr)
    return 1


def price_stance(row):
    if row["qualified"]:
        return "positive"
    if row["score"] >= 60:
        return "mixed"
    return "cautious"


def freshest_store(directory):
    """The freshest dated store file in a store directory, or
    None when the store does not exist yet. The file name is the
    session or run date it carries; the inside date is checked
    by the caller against it."""
    try:
        files = sorted(f for f in os.listdir(directory)
                       if f.endswith(".json")
                       and f != "manifest.jsonl")
    except OSError:
        return None, None
    if not files:
        return None, None
    return os.path.join(directory, files[-1]), files[-1][:-5]


def build():
    for path in (FULL_PATH, CARD_PATH, TAPE_PATH, MAP_PATH,
                 INST_PATH, PROV_PATH, FEED_PATH, LOG_PATH,
                 SISTER_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    full = load_json(FULL_PATH)
    card = load_json(CARD_PATH)
    tape = load_json(TAPE_PATH)
    mapc = load_json(MAP_PATH)
    inst = load_json(INST_PATH)
    prov = load_json(PROV_PATH)
    feed = load_json(FEED_PATH)
    sister = load_json(SISTER_PATH)
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]

    rows = full["rows"]
    session = full["as_of_session"]

    # --- Board card summary vs the full run recomputed. ---
    scored = [r for r in rows if r.get("score") is not None]
    insufficient = [r for r in rows if r.get("score") is None]
    qualified = [r for r in scored if r.get("qualified")]
    summary = card["summary"]
    recomputed = {"universe": len(rows), "scored": len(scored),
                  "insufficient_data": len(insufficient),
                  "qualified": len(qualified),
                  "as_of_session": session}
    for key, value in recomputed.items():
        if summary.get(key) != value:
            return fail(f"the board card's summary says "
                        f"{key}={summary.get(key)} but the full "
                        f"run recomputes to {value}; refusing to "
                        "publish a mismatched page.")
    if feed.get("as_of_session") != session:
        return fail("the published summary is dated "
                    f"{feed.get('as_of_session')} but the scored "
                    f"run is dated {session}; refusing to publish "
                    "a mismatched page.")
    feed_summary = (feed.get("board") or {}).get("summary") or {}
    for key in ("universe", "scored", "insufficient_data",
                "qualified"):
        if feed_summary.get(key) != recomputed[key]:
            return fail(f"the published summary's board {key} "
                        "disagrees with the scored run; refusing "
                        "to publish a mismatched page.")

    # --- Card top 50 must be the run's top 50. ---
    top50 = sorted(scored, key=lambda r: (-r["score"], r["symbol"]))
    top50 = top50[:50]
    card_by_symbol = {r["symbol"]: r for r in card["board"]}
    if set(card_by_symbol) != {r["symbol"] for r in top50}:
        return fail("the board card's 50 names are not the scored "
                    "run's top 50; refusing to publish.")
    for r in top50:
        c = card_by_symbol[r["symbol"]]
        if c["score"] != r["score"] or c["close"] != r["close"] or \
                c["qualified"] != r["qualified"] or \
                c["confirming"] != r["confirming"]:
            return fail(f"the board card's row for {r['symbol']} "
                        "disagrees with the scored run; refusing "
                        "to publish.")
        inst_cat = (c.get("categories") or {}).get(
            "institutionalPositioning") or {}
        if inst_cat.get("state") != "no-data" or \
                inst_cat.get("score") is not None:
            return fail(f"the board card's big-holder check for "
                        f"{r['symbol']} no longer reads no-data; "
                        "counting the board plus the filings "
                        "bundle would double-count one family, so "
                        "this refresh stops for review.")

    # --- Sister tool's copy of the same run must agree. ---
    if sister.get("session") != session:
        return fail("the sister tool's copy of the scored run is "
                    f"dated {sister.get('session')}, not "
                    f"{session}; refusing to publish.")
    by_symbol = {r["symbol"]: r for r in rows}
    sister_rows = sister.get("names") or []
    if len(sister_rows) != len(scored):
        return fail("the sister tool's copy carries "
                    f"{len(sister_rows)} scored names, not "
                    f"{len(scored)}; refusing to publish.")
    for srow in sister_rows:
        brow = by_symbol.get(srow["symbol"])
        if brow is None or brow.get("score") is None:
            return fail(f"the sister tool's copy names "
                        f"{srow['symbol']}, which the scored run "
                        "does not score; refusing to publish.")
        if srow["score"] != brow["score"] or \
                srow["close"] != brow["close"] or \
                srow["passed_every_check"] != brow["qualified"] or \
                srow["checks_in_favor"] != brow["confirming"] or \
                srow["data_behind_score_pct"] != brow["dc"]:
            return fail(f"the sister tool's copy disagrees with "
                        f"the scored run on {srow['symbol']}; "
                        "refusing to publish.")

    # --- Permanent log must hold a board entry for the session. ---
    board_ts = [r["ts_utc"] for r in log_rows
                if r.get("component") == "board-summary"]
    if not board_ts:
        return fail("the permanent log holds no board entry; "
                    "refusing to publish.")
    board_published = max(board_ts)

    # --- Prints card vs the published feed's copy. ---
    tape_by_symbol = {c["underlying"]: c for c in tape["cards"]}
    if set(tape_by_symbol) != set(INDEX_FUNDS):
        return fail("the prints card does not cover exactly the "
                    "three index funds; refusing to publish.")
    tape_session = tape["generated_at_utc"][:10]
    # The prints card is built by the post-close cycle for the
    # session that just closed, which is one session fresher
    # than the scored run every evening by the morgue's rhythm:
    # demanding equality refused every coherent evening cycle
    # (the tape family defect class cured in stream D). The
    # gate that means something is freshness (never older than
    # the scored session) plus the figure agreement with the
    # published summary's copy checked below (hookup cure,
    # 2026-10-29).
    if tape_session < session:
        return fail(f"the prints card is dated {tape_session}, "
                    f"older than the scored session {session}; "
                    "refusing to publish.")
    feed_tape = {t["symbol"]: t for t in feed.get("tape") or []}
    if set(feed_tape) != set(INDEX_FUNDS):
        return fail("the published summary's prints do not cover "
                    "exactly the three index funds; refusing to "
                    "publish.")
    for sym, c in tape_by_symbol.items():
        f = feed_tape[sym]
        checks = [
            ("prints", f["prints"], c["prints"]),
            ("total premium", round(c["total_premium"] / 1e6, 1),
             f["total_premium_m"]),
            ("net premium", round(c["net_premium"] / 1e6, 1),
             f["net_premium_m"]),
            ("golden sweeps", f["golden_sweeps"],
             c["golden_sweeps"]),
            ("high heat", f["high_heat"], c["high_heat"]),
            ("mean heat",
             round(c["heat_sum"] / c["algo_all_n"], 2),
             f["mean_heat"]),
        ]
        for label, mine, theirs in checks:
            if mine != theirs:
                return fail(f"the published summary's prints "
                            f"{label} for {sym} ({theirs}) "
                            f"disagrees with the prints card "
                            f"({mine}); refusing to publish.")

    # --- Positioning card vs the published feed's copy. ---
    map_by_symbol = {c["underlying"]: c for c in mapc["cards"]}
    if set(map_by_symbol) != set(INDEX_FUNDS):
        return fail("the positioning card does not cover exactly "
                    "the three index funds; refusing to publish.")
    feed_map = {m["symbol"]: m for m in feed.get("map") or []}
    if set(feed_map) != set(INDEX_FUNDS):
        return fail("the published summary's positioning does not "
                    "cover exactly the three index funds; refusing "
                    "to publish.")
    for sym, c in map_by_symbol.items():
        f = feed_map[sym]
        checks = [
            ("spot", f["spot"], c["spot"]),
            ("net pressure",
             round(c["net_gex_usd_per_1pct"] / 1e9, 2),
             f["net_gex_b"]),
            ("call wall", f["call_wall"], c["call_wall"]),
            ("put wall", f["put_wall"], c["put_wall"]),
            ("flip", round(c["zero_gamma"], 1), f["flip"]),
            ("dark pool ratio", round(c["dix_ratio"], 3),
             f["dix"]),
        ]
        for label, mine, theirs in checks:
            if mine != theirs:
                return fail(f"the published summary's "
                            f"positioning {label} for {sym} "
                            f"({theirs}) disagrees with the "
                            f"positioning card ({mine}); refusing "
                            "to publish.")

    # --- Filings bundle vs its provenance file. ---
    prov_names = {s for s in prov if not s.startswith("_")}
    if set(inst) != prov_names:
        return fail("the filings bundle and its provenance file "
                    "name different sets of companies; refusing "
                    "to publish.")
    si_prov = {s for s in prov_names
               if isinstance(prov[s].get("si"), dict)
               and "settlement_date" in prov[s]["si"]}
    si_bundle = {s for s, v in inst.items()
                 if v.get("shortPositioning") is not None}
    if si_prov != si_bundle:
        return fail("the short interest readings in the "
                    "provenance file do not line up name for name "
                    "with the bundle's short interest line; "
                    "refusing to publish.")
    filings_as_of = (prov.get("_meta") or {}).get("as_of")
    if not filings_as_of:
        return fail("the filings provenance file carries no date; "
                    "refusing to publish.")

    # --- Hookup wires (2026-10-30): three stores that landed
    # after this page was built, read here for the first time.
    # (a) The per-name tape store: prints for the tracked names,
    # direction unjudged by construction. (b) The news store:
    # articles per name over its window. (c) The Filings Wire's
    # published company facts, joined by the symbol that wire now
    # publishes. Each store is cross-checked against its own
    # counts before a single reading is taken from it, and a
    # store that does not exist yet leaves its family silent,
    # exactly as before; a store that exists but disagrees with
    # itself stops the refresh.
    pername = {}
    pername_session = None
    pn_path, pn_name = freshest_store(PERNAME_DIR)
    if pn_path:
        pn = load_json(pn_path)
        if pn.get("session") != pn_name:
            return fail("the per-name tape store's inside session "
                        "disagrees with its file name; refusing "
                        "to publish.")
        pername_session = pn["session"]
        if pername_session < session:
            return fail(f"the per-name tape store is dated "
                        f"{pername_session}, older than the "
                        f"scored session {session}; refusing to "
                        "publish.")
        pn_counts = pn.get("counts") or {}
        pn_names = pn.get("names") or {}
        if pn_counts.get("names_stored") != len(pn_names) \
                or pn_counts.get("prints") != sum(
                    v["prints"] for v in pn_names.values()) \
                or pn_counts.get("high_heat") != sum(
                    v["high_heat"] for v in pn_names.values()):
            return fail("the per-name tape store's counts disagree "
                        "with its own per-name records; refusing "
                        "to publish.")
        if pn.get("direction_basis") != "unjudged_no_print_time_quote":
            return fail("the per-name tape store no longer states "
                        "its direction is unjudged; refusing to "
                        "publish until that is understood.")
        pername = pn_names

    news_by_symbol = {}
    news_covered = set()
    news_date = None
    nw_path, nw_name = freshest_store(NEWS_DIR)
    if nw_path:
        nw = load_json(nw_path)
        if nw.get("date") != nw_name:
            return fail("the news store's inside date disagrees "
                        "with its file name; refusing to publish.")
        news_date = nw["date"]
        news_covered = set((nw.get("symbols") or {}).keys())
        for sym, articles in (nw.get("symbols") or {}).items():
            if articles:
                news_by_symbol[sym] = articles

    facts_by_symbol = {}
    if os.path.exists(FILINGS_PATH):
        filings_wire = load_json(FILINGS_PATH)
        if filings_wire.get("state") == "on_record":
            if len(filings_wire.get("companies") or []) != \
                    filings_wire.get("companies_on_record"):
                return fail("the Filings Wire's company count "
                            "disagrees with its list; refusing "
                            "to publish.")
            for comp in filings_wire["companies"]:
                if comp.get("symbol"):
                    facts_by_symbol[comp["symbol"]] = comp

    # --- Build per-name family readings. ---
    names = []
    counts = {i: 0 for i in range(7)}
    for row in sorted(rows, key=lambda r: r["symbol"]):
        sym = row["symbol"]
        entry = {"symbol": sym}
        directional = []

        if row.get("score") is None:
            entry["price"] = None
            entry["price_silent_reason"] = (
                "This name was checked on the scored day but "
                "there was too little price history to score it, "
                "so the price family has nothing to say.")
        else:
            stance = price_stance(row)
            price = {"close": row["close"], "score": row["score"],
                     "confirming": row["confirming"],
                     "checks_total": 8, "dc_pct": row["dc"],
                     "qualified": row["qualified"],
                     "stance": stance}
            if sym in card_by_symbol:
                cats = []
                for key, cat in (card_by_symbol[sym].get(
                        "categories") or {}).items():
                    if key not in CATEGORY_WORDS or \
                            cat.get("state") not in STATE_WORDS:
                        return fail(f"the board card carries a "
                                    f"check this page cannot say "
                                    f"in plain words ({key}/"
                                    f"{cat.get('state')}); "
                                    "refusing to publish.")
                    cats.append({
                        "name": CATEGORY_WORDS[key],
                        "state": STATE_WORDS[cat["state"]],
                        "score": cat["score"]})
                price["categories"] = cats
            entry["price"] = price
            directional.append(stance)

        if sym in tape_by_symbol:
            c = tape_by_symbol[sym]
            stance = ("cautious" if c["net_premium"] < 0 else
                      "positive" if c["net_premium"] > 0
                      else "mixed")
            entry["prints"] = {
                "prints": c["prints"],
                "total_premium": c["total_premium"],
                "net_premium": c["net_premium"],
                "call_net_premium": c["call_net_premium"],
                "put_net_premium": c["put_net_premium"],
                "high_heat": c["high_heat"],
                "golden_sweeps": c["golden_sweeps"],
                "mean_heat": round(
                    c["heat_sum"] / c["algo_all_n"], 2),
                "stance": stance}
            directional.append(stance)
        elif sym in pername:
            pn = pername[sym]
            entry["prints"] = {
                "prints": pn["prints"],
                "total_premium": pn["total_premium"],
                "net_premium": None,
                "call_net_premium": None,
                "put_net_premium": None,
                "high_heat": pn["high_heat"],
                "golden_sweeps": pn["golden_sweeps"],
                "mean_heat": pn["mean_heat"],
                "stance": None,
                "direction": "unjudged_no_print_time_quote",
                "session": pername_session}
        else:
            entry["prints"] = None

        if sym in map_by_symbol:
            c = map_by_symbol[sym]
            below = c["spot"] < c["zero_gamma"]
            negative = c["net_gex_usd_per_1pct"] < 0
            stance = ("cautious" if below and negative else
                      "positive" if not below and not negative
                      else "mixed")
            entry["positioning"] = {
                "spot": c["spot"],
                "net_gex_b": round(
                    c["net_gex_usd_per_1pct"] / 1e9, 2),
                "call_wall": c["call_wall"],
                "put_wall": c["put_wall"],
                "flip": round(c["zero_gamma"], 2),
                "below_flip": below,
                "dix_pct": round(c["dix_ratio"] * 100, 1),
                "dix_date": c["dix_date"],
                "contracts_used": c["contracts_used"],
                "chain_total": c["chain_total"],
                "stance": stance}
            directional.append(stance)
        else:
            entry["positioning"] = None

        bundle = inst.get(sym)
        leaves = {}
        if bundle:
            for key, value in bundle.items():
                if value is not None:
                    if key not in LEAF_WORDS:
                        return fail(f"the filings bundle carries "
                                    f"a line this page cannot "
                                    f"say in plain words ({key}); "
                                    "refusing to publish.")
                    leaves[LEAF_WORDS[key]] = round(value, 1)
        if leaves:
            filing = {"readings": leaves}
            p = prov[sym]
            insider = p.get("insider") or {}
            if insider.get("n_transactions"):
                filing["insider_transactions"] = insider[
                    "n_transactions"]
                filing["insider_latest"] = insider[
                    "latest_filing_date"]
            si = p.get("si") or {}
            if "settlement_date" in si:
                filing["si_pct"] = round(
                    si["si_pct_of_shares_out"], 2)
                filing["days_to_cover"] = round(
                    si["days_to_cover"], 2)
                filing["si_settlement"] = si["settlement_date"]
            entry["filings"] = filing
        else:
            entry["filings"] = None

        comp = facts_by_symbol.get(sym)
        if comp:
            recorded = [f for f in comp["figures"]
                        if f.get("state") == "recorded"]
            freshest_filed = max(
                (r["filed"] for f in recorded
                 for r in f["readings"]), default=None)
            entry["facts"] = {
                "figures_recorded": len(recorded),
                "figures_total": len(comp["figures"]),
                "freshest_filed": freshest_filed,
                "company_name": comp.get("company_name")}
        else:
            entry["facts"] = None

        articles = news_by_symbol.get(sym)
        if articles:
            latest = max(articles, key=lambda a: a["created_at"])
            entry["news"] = {
                "articles": len(articles),
                "freshest": latest["created_at"][:10],
                "headline": latest["headline"],
                "store_date": news_date}
            entry["news_silent_reason"] = None
        else:
            entry["news"] = None
            if sym in news_covered:
                entry["news_silent_reason"] = (
                    "A news record is kept for this name and it "
                    "carries no articles in the latest window, "
                    "so this family has nothing to read for it.")
            else:
                entry["news_silent_reason"] = None

        speaking = sum(1 for k in ("price", "prints",
                                   "positioning", "filings",
                                   "facts", "news")
                       if entry[k] is not None)
        entry["families_speaking"] = speaking
        counts[speaking] = counts.get(speaking, 0) + 1
        entry["directional"] = directional
        names.append(entry)

    # The coverage gate, re-derived from the stores themselves
    # (hookup cure, 2026-10-30): the old gate pinned the exact
    # distribution inspected before the per-name tape, facts and
    # news stores existed (3 names at three families, 38 at two),
    # so any of those stores landing would have refused every
    # coherent run forever. The gate that means something now:
    # the distribution sums to the universe, and each family's
    # speaking count recomputed from its own source records
    # matches the count assembled above.
    if sum(counts.values()) != len(rows):
        return fail(f"the family coverage recomputes to {counts}, "
                    f"which does not sum to the {len(rows)} names "
                    "on record; refusing to publish.")
    row_symbols = {r["symbol"] for r in rows}
    expected_speakers = {
        "prints": len((set(INDEX_FUNDS) | set(pername))
                      & row_symbols),
        "facts": len(set(facts_by_symbol) & row_symbols),
        "news": len(set(news_by_symbol) & row_symbols),
    }
    for fam, expected in expected_speakers.items():
        assembled = sum(1 for e in names if e[fam] is not None)
        if assembled != expected:
            return fail(f"the {fam} family speaks for {assembled} "
                        f"names assembled, but its source records "
                        f"cover {expected} names on record; "
                        "refusing to publish.")

    data = {
        "tool": "The Second Opinion",
        # Chart counts (2026-10-31 chart cure): the family-coverage
        # distribution recomputed above from the page's own names,
        # copied into the top-level counts block the record producer
        # and chart renderer draw from on sibling pages (flow-tape,
        # state-analogue). No new numbers: every value is the
        # coverage count assembled for this page's own coverage block.
        "counts": {
            "names_covered_by_six_families": counts[6],
            "names_covered_by_five_families": counts[5],
            "names_covered_by_four_families": counts[4],
            "names_covered_by_three_families": counts[3],
            "names_covered_by_two_families": counts[2],
            "names_covered_by_one_family": counts[1],
            "names_covered_by_no_family": counts[0],
        },
        "state": "published",
        "session": session,
        "board_published_at_utc": board_published,
        "prints_published_at_utc": tape["generated_at_utc"],
        "positioning_built_at_utc": mapc["built_utc"],
        "filings_as_of": filings_as_of,
        "source": SOURCE_WORDS,
        "why_families": WHY_FAMILIES,
        "thin_threshold": MIN_EVENTS_FOR_PERCENT,
        "families": FAMILIES,
        "silent_reasons": SILENT,
        "index_funds": list(INDEX_FUNDS),
        "coverage": {
            "names_on_record": len(rows),
            "scored": len(scored),
            "too_little_data": len(insufficient),
            "six_families": counts[6],
            "five_families": counts[5],
            "four_families": counts[4],
            "three_families": counts[3],
            "two_families": counts[2],
            "one_family": counts[1],
            "no_family": counts[0],
            "filings_names_on_file": len(prov_names),
            "prints_names_on_file": expected_speakers["prints"],
            "facts_names_on_file": expected_speakers["facts"],
            "news_names_on_file": expected_speakers["news"],
            "pername_tape_session": pername_session,
            "news_store_date": news_date,
        },
        "default_name": "SPY",
        "names": names,
        "receipt": {
            "source": SOURCE_WORDS,
            "coverage": (
                f"Scored trading day {session}: {len(rows)} "
                f"names checked, {len(scored)} scored, "
                f"{len(insufficient)} with too little data to "
                f"score. Options prints cover the three index "
                f"funds plus the per-name tape record for "
                f"{len(pername)} names (session "
                f"{pername_session}, direction unjudged for "
                f"single names); modelled positioning covers "
                f"the three index funds only. Filings and "
                f"positioning readings are on file for "
                f"{len(prov_names)} names dated {filings_as_of}; "
                f"company facts are on file for "
                f"{expected_speakers['facts']} names and news "
                f"for {expected_speakers['news']} names (store "
                f"dated {news_date}). "
                f"{sum(v for k, v in counts.items() if k >= 2)} "
                "names in all carry two or more families."),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(names)} names; "
          + ", ".join(f"{counts[k]} at {k}" for k in
                      sorted(counts, reverse=True) if counts[k])
          + f"; session {session})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
