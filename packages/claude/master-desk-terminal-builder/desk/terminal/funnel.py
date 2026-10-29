"""The Funnel: the three free public services of Muse's FUNNEL STUDY (synthesis/FUNNEL-STUDY.md section 4), as one edition
key, `funnel`, built from the edition's `morgue` key and the edition's own blocks and from nothing else.

  map    The Morning Map     one card per index (SPY, QQQ, IWM): spot, net dealer gamma and its regime word, the walls,
                             the zero-gamma flip and its distance, DIX with its one-day lag label, chain coverage, whether the
                             sources agree, one plain-English read, and yesterday's card graded.  Label CONTEXT: it measures, it
                             does not trade.
  board  The Qualified Board the Morgue board's qualified names, each row with its trigger, its ladder (support = the
                             invalidation, trigger, two targets), the confirming categories, institutional ownership /
                             insider / short-interest chips with their vintage, the chart-review rank beside it, and a label:
                             TRADE (complete grammar), CONTEXT, or STRETCH (price already past the ladder).  The gate is
                             printed verbatim, with the refusals.
  wire   The Golden Sweep    every print the rule qualifies (sweep and size >= strike open interest and premium >= $1M, or
         Wire                Heat >= 15), with premium, side, days to expiry, the opening-or-closing label, the 52-week
                             context, the bias on its label and the print's own later grade (+1h, +1d).  Never a selection.

Laws (the study's P-1 to P-8): a number is copied or computed from the `morgue` key and the edition, never made up; a
figure whose source is absent says "no data" with the reason, never a dash; the grading line is the scorecard's own text
(one source, copied byte for byte into the map, board and wire); an outcome is a forward return at a fixed horizon, never
the best moment; a record is "not yet graded - N logged, first grade on DATE" until it matures; losers stay in; no win
rate is ever computed here.  The block carries no currency sign: the page adds the dollar where it draws a price.

The reading contract for `morgue` is docs/research/FUNNEL_SCHEMA.md; the fixtures are Silicon's output/*_card.json shapes.
    build(ed)  ->  the `funnel` dict (validated by ALLOWED, merged into the terminal's contract), or None without anything
                   to say (never: an absent morgue key is a block whose three sections read "no data: <reason>")
"""
import math
import re
from datetime import date, datetime, timedelta

from .. import calendar as cal
from ..util import ET

SCHEMA = 1
WATCHED = ("SPY", "QQQ", "IWM")
PREOPEN_AT = (8, 45)            # the study's target: the Map and Board publish before the open, never updated intraday
POSTCLOSE_AT = (16, 46)         # the Tape, the scorecards and the studies
GATE = ("Qualify flag and at least 5 of 8 categories confirming and score of 65 or more and data confidence of 70 or "
        "more, over a 60% data-coverage floor; below the floor a name reads insufficient data, never a guessed score")
WIRE_RULE = ("A print publishes if and only if it is a sweep and its size is at least the strike's open interest and its "
             "premium is 1,000,000 dollars or more (a Golden Sweep), or its Heat Score is 15 or more. No human picks.")
MEASURES = "Measurements of where the market is positioned."
GATE_WORDS = {"not-qualified": "no Qualify flag", "count": "fewer than 5 of 8 categories confirming",
              "data-confidence": "data confidence under 70", "score": "score under 65", "insufficient": "insufficient data",
              "atr<2%": "range under 2% of price", "adv<=500k": "average volume of 500,000 shares or less",
              "stage-3": "Stage 3 (topping)"}
CATS = {"relativeStrength": "Relative strength", "priceAction": "Price action", "volumeParticipation": "Volume",
        "trendAlignment": "Trend", "supportResistance": "Support and resistance", "sectorLeadership": "Sector leadership",
        "institutionalPositioning": "Institutions", "marketContext": "Market context"}
CHIPS = (("instOwnership", "Institutional ownership", "13F, a quarter behind: filed up to 45 days after quarter end",
          "no 13F holdings resolved for this name (CUSIP unmatched or ambiguous)"),
         ("instActivity", "Institutional buying", "13F change, a quarter behind",
          "no two 13F quarters resolved for this name"),
         ("insiderActivity", "Insider buying", "Form 4 open-market trades, six-month window",
          "fewer than 2 open-market Form 4 trades in six months, or no SEC filer match"),
         ("shortPositioning", "Short interest", "FINRA short interest as republished, twice a month",
          "no short-interest row or no share count for this name"))
SIDES = {"above_ask": ("bought above the ask", 1), "ask": ("bought at the ask", 1), "below_bid": ("sold below the bid", -1),
         "bid": ("sold at the bid", -1), "mid": ("traded at the middle", 0), "unknown": ("side unknown", 0)}
OCC = re.compile(r"^([A-Z.]{1,6})(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")
ROWS_MAX = 40
PRINTS_MAX = 25

_H = {"ok", "partial", "stale", "pending", "no_data"}
_STATUS = {"status", "reason"}
_GRADE = {"state", "line", "map", "board", "wire", "random", "n_logged", "n_graded", "horizons"}
_LEAF = {"cats", "cats_all", "notes"}
ALLOWED = {
    "funnel": {"schema", "as_of", "built_at", "status", "reason", "scoring", "rhythm", "labels", "summary", "map", "board", "wire"},
    "funnel.scoring": _GRADE,
    "funnel.scoring.horizons[]": {"h", "state", "line"},
    "funnel.rhythm": {"preopen", "postclose", "policy", "published", "next", "corrections"},
    "funnel.summary": {"map", "board", "wire"},
    "funnel.map": _STATUS | {"as_of", "vintage", "delay", "read", "label", "measures", "yesterday", "cards", "grade_line"},
    "funnel.map.cards[]": {"symbol", "spot", "net_gex_b", "regime", "tone", "call_wall", "call_wall_pct", "put_wall",
                           "put_wall_pct", "flip", "flip_pct", "flip_side", "dix", "dix_date", "dix_line", "dix_index",
                           "coverage_pct", "coverage_line", "agree", "agree_line", "read", "label", "as_of", "vintage"},
    "funnel.map.cards[].dix_index": _STATUS | {"value", "date", "coverage_pct", "line"},
    "funnel.board": _STATUS | {"as_of", "vintage", "delay", "gate", "counts", "headline", "rows", "refused", "shown_line",
                               "lector_line", "base_rate", "grade_line", "label"},
    "funnel.board.counts": {"universe", "scored", "qualified", "insufficient"},
    "funnel.board.refused": {"symbol", "score", "reasons", "line"},
    "funnel.board.rows[]": {"symbol", "sector", "close", "score", "confirming", "of", "dc", "stage", "triggers", "ladder",
                            "label", "label_why", "cats", "chips", "lector", "line"},
    "funnel.board.rows[].triggers[]": {"name", "level", "validated"},
    "funnel.board.rows[].ladder": _STATUS | {"support", "trigger", "t1", "t2", "close_vs", "basis"},
    "funnel.board.rows[].chips[]": {"key", "label", "status", "reason", "value", "vintage"},
    "funnel.board.rows[].lector": _STATUS | {"rank", "band"},
    "funnel.wire": _STATUS | {"as_of", "vintage", "delay", "rule", "coverage", "bias", "counts", "prints", "label",
                              "measures", "grade_line", "buys_only"},
    "funnel.wire.counts": {"prints_total", "qualified", "golden", "shown"},
    "funnel.wire.buys_only": {"status", "reason", "line"},
    "funnel.wire.prints[]": {"ts", "symbol", "contract", "kind", "strike", "expiry", "dte", "premium", "size", "heat", "tags",
                             "rules", "side", "side_word", "sentiment", "spot", "oi", "opening", "week52", "outcome",
                             "label", "line"},
    "funnel.wire.prints[].opening": _STATUS | {"word"},
    "funnel.wire.prints[].week52": _STATUS | {"word", "pos_pct"},
    "funnel.wire.prints[].outcome": {"h1", "d1", "state", "line"},
    "funnel.wire.prints[].outcome.h1": _STATUS | {"ret_pct", "due"},
    "funnel.wire.prints[].outcome.d1": _STATUS | {"ret_pct", "due"},
}
LEAVES = _LEAF | {"tags", "rules", "labels", "notes"}


# ---- small things ---------------------------------------------------------------------------------------------------

def _n(x):
    """x as a finite float, or None (a bool, a string and NaN are not numbers here)"""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return float(x) if math.isfinite(x) else None


def _r(x, d=2):
    v = _n(x)
    return None if v is None else round(v, d)


def no(reason, status="no_data", **kw):
    return {"status": status, "reason": reason, **kw}


def _list(x):
    return [v for v in x if isinstance(v, dict)] if isinstance(x, list) else []


def _cards_of(x):
    """a section given as a list of cards, as {"cards": [...]}, or as {SYMBOL: card}"""
    if isinstance(x, list):
        return _list(x)
    if isinstance(x, dict):
        for k in ("cards", "rows", "items"):
            if isinstance(x.get(k), list):
                return _list(x[k])
        if isinstance(x.get("cards"), dict):                  # the Morgue block's own shape: {"cards": {FUND: card}}
            x = x["cards"]
        return [dict(v, symbol=v.get("symbol") or k) for k, v in x.items() if isinstance(v, dict)]
    return []


def _gen(mg):
    """when the Morgue block was built: the vendor fixtures' generated_at_utc, or the edition block's own built_at"""
    return mg.get("generated_at_utc") or mg.get("generated_at") or mg.get("built_at")


def _sess(mg):
    """the session the Morgue block describes: the vendor fixtures' as_of_session, or the edition block's own as_of"""
    return str(mg.get("as_of_session") or mg.get("as_of") or "") or None


def _score(mg):
    """the grading source: the vendor fixtures' `scorecard`, or the edition block's `ledger` (counters, scorecards with the
    horizons as a list) reshaped to it"""
    if isinstance(mg.get("scorecard"), dict) and mg["scorecard"]:
        return mg["scorecard"]
    lg = mg.get("ledger")
    scs = lg.get("scorecards") if isinstance(lg, dict) else None
    if not isinstance(scs, dict):
        return None
    board = {}
    for cohort, v in (scs.get("board") or {}).items():
        hz = v.get("horizons") if isinstance(v, dict) else None
        if isinstance(hz, list):
            hz = {str(h.get("horizon")): h for h in hz if isinstance(h, dict) and h.get("horizon")}
        board[cohort] = {"n_logged": (v or {}).get("n_logged"), "horizons": hz or {}}
    return {"counters": lg.get("counters") or {}, "board": board, "map": scs.get("map") or {}}


def _day(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _when(ed):
    """the edition's moment, in Eastern time"""
    try:
        t = datetime.fromisoformat(str(ed.get("generated_at")))
        return t.astimezone(ET) if t.tzinfo else t.replace(tzinfo=ET)
    except (TypeError, ValueError):
        return datetime.now(ET)


def _et(ts):
    """a feed timestamp as 'HH:MM ET', or None"""
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (t if t.tzinfo else t.replace(tzinfo=ET)).astimezone(ET)


def _pct(a, b):
    a, b = _n(a), _n(b)
    return None if a is None or not b else round((a - b) / b * 100, 2)


def _num(v, d=2):
    return f"{v:,.{d}f}"


def _signed(v, d=1):
    return ("+" if v > 0 else "-" if v < 0 else "") + f"{abs(v):.{d}f}"


def _fresh(gen, ed_when, what, due):
    """('ok'|'pending'|'stale', note) for a card published on `gen` (a date) seen at ed_when: the Map and Board publish
    once a trading day before the open, so before that hour the previous one is the current one"""
    today = ed_when.date()
    if gen is None:
        return "ok", None
    if gen >= today:
        return "ok", None
    if not cal.is_trading_day(today):
        return ("ok", None) if gen >= cal.prev_trading_day(today) else ("stale", f"{what} last published {gen.isoformat()}")
    if ed_when.hour * 60 + ed_when.minute < due[0] * 60 + due[1]:
        return "pending", f"today's {what} publishes about {due[0]:02d}:{due[1]:02d} ET; this is the one from {gen.isoformat()}"
    return "stale", f"no {what} has published today; this is the one from {gen.isoformat()}"


# ---- the one grading line --------------------------------------------------------------------------------------------

def grade(sc):
    """the grading block, copied from the morgue's scorecard so the three sections show one source of truth. `sc` is
    morgue.scorecard; absent, every line reads no data with the reason"""
    if not isinstance(sc, dict) or not sc:
        why = "no data: the scorecard has not published, so nothing here is graded"
        return {"state": "no_data", "line": why, "map": why, "board": why, "wire": why,
                "random": "no data: edge against random entries needs matured rows", "n_logged": 0, "n_graded": 0,
                "horizons": []}
    cnt = sc.get("counters") or {}
    hs = []
    pub = ((sc.get("board") or {}).get("published") or {})
    for h, v in sorted((pub.get("horizons") or {}).items(), key=lambda kv: int(re.sub(r"\D", "", kv[0]) or 0)):
        if isinstance(v, dict):
            hs.append({"h": str(h), "state": str(v.get("state") or "not_yet_graded"),
                       "line": str(v.get("line") or "not yet graded")})
    logged = int(_n(cnt.get("units_published")) or 0)
    graded = int(_n(cnt.get("units_graded")) or 0)
    mp = sc.get("map") or {}
    qual = ((sc.get("board") or {}).get("qualified") or {})
    wr = sc.get("wire") or {}
    map_line = str(mp.get("line") or ("not yet graded - " + str(mp.get("cards_pending") or 0) + " Map cards of record"))
    first = next((h["line"] for h in hs if h["state"] != "graded"), None)
    board_line = (f"not yet graded - {int(_n(qual.get('n_logged')) or 0)} qualified rows logged. "
                  + (re.sub(r"^not yet graded\s*[—:-]\s*", "", first) if first else "")).strip()
    if any(h["state"] == "graded" for h in hs):
        board_line = "; ".join(f"{h['h']}: {h['line']}" for h in hs)
    if wr:
        wire_line = str(wr.get("line") or "not yet graded")
    else:
        wire_line = (f"not yet graded - no Wire scorecard yet; alerts are logged before they are shown and graded at +1h "
                     f"and +1d once the first ones mature")
    state = "graded" if graded else "not_yet_graded"
    line = (f"{graded} of {logged} published units graded so far" if logged else "no published units yet")
    rnd = sc.get("random") or sc.get("edge_vs_random")
    random = (str(rnd.get("line")) if isinstance(rnd, dict) and rnd.get("line") else
              "not yet measured - the comparison with random entries in the same names and days needs matured rows")
    return {"state": state, "line": line, "map": map_line, "board": board_line, "wire": wire_line, "random": random,
            "n_logged": logged, "n_graded": graded, "horizons": hs}


# ---- The Morning Map -------------------------------------------------------------------------------------------------

def _agree(sym, net, extra, strip_gex):
    """(status, line): do the sources that exist agree on the sign of net dealer gamma? Disagreement is printed, not
    resolved. Sources: the morgue's static convention, any other convention the card carries, and the desk strip's own
    chain read for the same index"""
    srcs = [("static convention", net)]
    for k, label in (("variant", "variant convention"), ("tape", "tape-signed convention")):
        v = _n((extra or {}).get(k))
        if v is not None:
            srcs.append((label, v))
    sg = (strip_gex or {}).get(sym) or {}
    if sg.get("status") in ("ok", "stale") and _n(sg.get("net")) is not None:
        srcs.append(("desk strip", sg["net"]))
    signs = [("negative" if v < 0 else "positive") for _, v in srcs if v != 0]
    if len(srcs) == 1:
        return "partial", ("1 source only (the static convention): no agreement test is possible yet; the variant and "
                           "tape-signed conventions are not built")
    neg, pos = signs.count("negative"), signs.count("positive")
    if neg and pos:
        return "ok", f"sources disagree: {neg} negative, {pos} positive"
    return "ok", f"{len(signs)} of {len(signs)} agree: {signs[0] if signs else 'flat'}"


def map_card(c, sym_strip_gex=None, vintage=None):
    sym = str(c.get("symbol") or c.get("underlying") or "").upper()
    spot = _n(c.get("spot"))
    net = _n(c.get("net_gex_b"))
    if net is None and _n(c.get("net_gex_usd_per_1pct")) is not None:
        net = c["net_gex_usd_per_1pct"] / 1e9
    flip = _n(c.get("flip")) if _n(c.get("flip")) is not None else _n(c.get("zero_gamma"))
    cw, pw = _n(c.get("call_wall")), _n(c.get("put_wall"))
    dix = _n(c.get("dix")) if _n(c.get("dix")) is not None else _n(c.get("dix_ratio"))
    if not sym or spot is None or net is None:
        return None
    fp = _pct(flip, spot)
    regime = "Amplifying" if net < 0 else "Dampening"
    cov = None
    if _n(c.get("contracts_used")) and _n(c.get("chain_total")):
        cov = c["contracts_used"] / c["chain_total"] * 100
    elif isinstance(c.get("coverage"), str) and "/" in c["coverage"]:
        a, _, b = c["coverage"].partition("/")
        try:
            cov = int(a) / int(b) * 100 if int(b) else None
        except ValueError:
            cov = None
    cov = None if cov is None else round(cov, 0)
    st, ag = _agree(sym, net, c.get("conventions"), sym_strip_gex)
    ix = c.get("dix_index") if isinstance(c.get("dix_index"), dict) else None
    dix_idx = None
    if ix and ix.get("state") == "graded" and _n(ix.get("value")) is not None:
        dix_idx = {"status": "ok", "value": _r(ix["value"], 3), "date": str(ix.get("date") or ""),
                   "coverage_pct": _r(_n(ix.get("coverage")) * 100, 1) if _n(ix.get("coverage")) is not None else None,
                   "line": "constituent-weighted, a different measure from the ETF's own ratio above"}
    elif ix:
        dix_idx = no(str(ix.get("reason") or "constituent coverage under the 80% floor"))
    dline = (f"DIX {dix:.3f}, FINRA file dated {c.get('dix_date')}: published with a one-day lag" if dix is not None and c.get("dix_date")
             else f"DIX {dix:.3f}: file date not stated" if dix is not None else
             "no data: no FINRA short-sale file for this index")
    side = None if fp is None else ("above" if fp > 0 else "below")
    if regime == "Amplifying":
        read = (f"Dealers are net short gamma, so {sym} moves tend to speed up. "
                + (f"The flip is {abs(fp):.1f}% {side} spot at {_num(flip)}; " if fp is not None else "No flip was found near spot; ")
                + (f"the walls frame {_num(pw, 0)} to {_num(cw, 0)}." if pw and cw else "no wall pair is known."))
    else:
        read = (f"Dealers are net long gamma, so {sym} moves tend to slow down and pin toward the big strikes. "
                + (f"The flip is {abs(fp):.1f}% {side} spot at {_num(flip)}; " if fp is not None else "No flip was found near spot; ")
                + (f"the walls frame {_num(pw, 0)} to {_num(cw, 0)}." if pw and cw else "no wall pair is known."))
    return {"symbol": sym, "spot": _r(spot), "net_gex_b": _r(net), "regime": regime,
            "tone": "dn" if regime == "Amplifying" else "up",
            "call_wall": _r(cw), "call_wall_pct": _pct(cw, spot), "put_wall": _r(pw), "put_wall_pct": _pct(pw, spot),
            "flip": _r(flip), "flip_pct": fp, "flip_side": side, "dix": _r(dix, 3), "dix_date": str(c.get("dix_date") or "") or None,
            "dix_line": dline, "dix_index": dix_idx, "coverage_pct": cov,
            "coverage_line": (f"{cov:.0f}% of open-interest contracts priced" if cov is not None else
                              "no data: contract coverage not stated"),
            "agree": st, "agree_line": ag, "read": read, "label": "CONTEXT", "as_of": vintage, "vintage": "overnight open interest"}


def build_map(ed, mg, gr, when):
    if mg is None:
        return no("no data: the positioning feed has not published (the edition carries no morgue block)")
    raw = _cards_of(mg.get("map"))
    if not raw:
        why = (mg.get("map") or {}).get("reason") if isinstance(mg.get("map"), dict) else None
        return no(f"no data: the morgue block carries no Map cards ({why or 'the chain job returned nothing'})")
    gen = _day(_gen(mg))
    sess = _sess(mg)
    gex = (ed.get("strip") or {}).get("gex")
    cards = []
    for c in raw:
        mc = map_card(c, gex, sess)
        if mc:
            cards.append(mc)
    if not cards:
        return no("no data: the Map cards have no spot or net gamma to read")
    order = {s: i for i, s in enumerate(WATCHED)}
    cards.sort(key=lambda c: order.get(c["symbol"], 9))
    st, note = _fresh(gen, when, "Map card", PREOPEN_AT)
    head = cards[0]
    read = head["read"]
    ys = ((_score(mg) or {}).get("map") or {})
    grades = [g for g in (ys.get("grades") or []) if isinstance(g, dict)]
    yline = gr["map"]
    if grades:
        yline = "Yesterday: " + str(grades[-1].get("line") or grades[-1].get("summary") or gr["map"])
    sess_line = (f"as of the {sess} close" if sess else "session not stated")
    return {"status": "ok" if st == "ok" else st, "reason": note, "as_of": sess,
            "vintage": f"overnight open interest, {sess_line}", "delay": "DIX is the FINRA file of the prior session",
            "read": read, "label": "CONTEXT", "measures": MEASURES, "yesterday": yline, "cards": cards,
            "grade_line": gr["map"]}


# ---- The Qualified Board ---------------------------------------------------------------------------------------------

def _tname(t):
    return str(t.get("trigger") or t.get("name") or "") if isinstance(t, dict) else str(t)


def ladder(r):
    """support / trigger / target 1 / target 2 from a row: the Saty ATR ladder (trigger 0.236 ATR, targets 0.618 and 1.0
    ATR); the support is the row's invalidation. Honest when a level is missing"""
    lad = r.get("ladder") if isinstance(r.get("ladder"), dict) else {}
    up = lad.get("up") if isinstance(lad.get("up"), dict) else {}
    sup = _n(r.get("support"))
    trig = _n(lad.get("trigger_up")) if _n(lad.get("trigger_up")) is not None else _n(r.get("trigger_up"))
    t1, t2 = _n(up.get("0.618")), _n(up.get("1.0"))
    close = _n(r.get("close"))
    if sup is None or trig is None:
        miss = " and ".join(n for n, v in (("support", sup), ("trigger", trig)) if v is None)
        return no(f"no data: the row carries no {miss}")
    out = {"status": "ok", "support": _r(sup), "trigger": _r(trig), "t1": _r(t1), "t2": _r(t2), "close_vs": "inside",
           "basis": "Saty ATR ladder: trigger 0.236 ATR, targets 0.618 and 1.0 ATR; support is the invalidation"}
    if t1 is None:
        out["basis"] = "targets: no data: the ladder levels are not in the feed"
    if close is not None:
        top = t2 if t2 is not None else t1
        if top is not None and close > top:
            out["close_vs"] = "past_t2" if t2 is not None else "past_t1"
        elif t1 is not None and close > t1:
            out["close_vs"] = "past_t1"
        elif close < sup:
            out["close_vs"] = "below_support"
        elif close < trig:
            out["close_vs"] = "below_trigger"
    return out


def label_of(lad):
    """TRADE needs the complete grammar (support < trigger < target, price inside it); STRETCH when price is already past
    the ladder; CONTEXT otherwise"""
    if lad.get("status") != "ok":
        return "CONTEXT", "no complete ladder, so this is context"
    cv = lad.get("close_vs")
    if cv in ("past_t1", "past_t2"):
        return "STRETCH", "price is already past the first target: a chase, not an entry"
    if cv == "below_support":
        return "CONTEXT", "price is below the invalidation: the setup is already wrong"
    s, t, t1 = lad["support"], lad["trigger"], lad.get("t1")
    if t1 is None or not (s < t < t1):
        return "CONTEXT", "the ladder is incomplete or out of order"
    return "TRADE", "support, trigger and targets all present and in order"


def _chip(key, label, cadence, why, sym, inst, prov):
    v = _n((inst or {}).get(key))
    p = prov or {}
    vint = cadence
    if key == "insiderActivity" and isinstance(p.get("insider"), dict) and p["insider"].get("latest_filing_date"):
        vint = f"latest Form 4 filed {p['insider']['latest_filing_date']}; six-month window"
    if key == "shortPositioning" and isinstance(p.get("si"), dict) and p["si"].get("settlement_date"):
        vint = f"short interest settled {p['si']['settlement_date']}"
    if v is None:
        reason = why
        if key == "shortPositioning" and isinstance(p.get("si"), dict) and p["si"].get("reason"):
            reason = str(p["si"]["reason"])
        if key == "insiderActivity" and isinstance(p.get("errors"), dict) and p["errors"].get("edgar"):
            reason = "no SEC filer match for this name"
        return {"key": key, "label": label, "status": "no_data", "reason": "no data: " + reason, "vintage": vint}
    return {"key": key, "label": label, "status": "ok", "value": _r(v, 0), "vintage": vint}


def _inst_of(mg):
    ins = mg.get("institutional")
    if not isinstance(ins, dict):
        return {}, {}, False
    by = ins.get("by_symbol") if isinstance(ins.get("by_symbol"), dict) else {k: v for k, v in ins.items() if isinstance(v, dict)
                                                                       and k not in ("provenance", "as_of")}
    prov = ins.get("provenance") if isinstance(ins.get("provenance"), dict) else {}
    return by, prov, True


def board_row(r, inst, prov, lector, has_inst):
    sym = str(r.get("symbol") or "").upper()
    if not sym or _n(r.get("score")) is None:
        return None
    lad = ladder(r)
    lab, why = label_of(lad)
    cats = r.get("categories") if isinstance(r.get("categories"), dict) else {}
    ok = [CATS.get(k, k) for k, v in cats.items() if isinstance(v, dict) and v.get("state") == "confirming"]
    conf = r.get("confirming")
    conf = int(conf) if _n(conf) is not None else len(ok)
    trig = []
    for t in r.get("triggers") or []:
        nm = _tname(t)
        if nm:
            trig.append({"name": nm, "level": _r(t.get("level")) if isinstance(t, dict) else None,
                         "validated": (t.get("validated") if isinstance(t, dict) and isinstance(t.get("validated"), bool) else None)})
    trig_state = [{"name": t["name"], **{k: v for k, v in t.items() if k != "name" and v is not None}} for t in trig]
    chips = ([_chip(k, lb, cd, wy, sym, inst.get(sym), prov.get(sym)) for k, lb, cd, wy in CHIPS] if has_inst else
             [{"key": k, "label": lb, "status": "no_data", "reason": "no data: the institutional feed has not published",
               "vintage": cd} for k, lb, cd, wy in CHIPS])
    lr = lector.get(sym)
    lec = ({"status": "ok", "rank": int(lr["rank"]), "band": str(lr.get("band") or "")} if lr else
           no("not in the chart-review ranking today"))
    line = (f"{_r(r['score'], 0):.0f} — {conf} of 8" + (f" · {trig[0]['name']}" if trig else " · no trigger has fired"))
    return {"symbol": sym, "sector": r.get("sector") or None, "close": _r(r.get("close")), "score": _r(r["score"], 1),
            "confirming": conf, "of": 8, "dc": _r(r.get("dc"), 1), "stage": int(r["stage"]) if _n(r.get("stage")) is not None else None,
            "triggers": trig_state, "ladder": lad, "label": lab, "label_why": why, "cats": ok, "chips": chips,
            "lector": lec, "line": line}


def _fails(r):
    out = []
    for g in (r.get("gate_fails") or []) + (r.get("qualify_fails") or []):
        w = GATE_WORDS.get(str(g), str(g))
        if w not in out:
            out.append(w)
    return out


def build_board(ed, mg, gr, when):
    if mg is None:
        return no("no data: the Morgue board has not published (the edition carries no morgue block)")
    b = mg.get("board")
    if not isinstance(b, dict):
        return no("no data: the morgue block carries no board")
    summ = b.get("summary") if isinstance(b.get("summary"), dict) else {}
    rows_all = _list(b.get("rows")) or _list(b.get("board"))
    q_raw = _list(b.get("qualified")) or [r for r in rows_all if r.get("qualified") is True]
    if not q_raw and not summ:
        return no("no data: the board carries neither names nor a summary")
    inst, prov, has_inst = _inst_of(mg)
    lector = {}
    for r in _list((ed.get("lector") or {}).get("rows")):
        if r.get("symbol") and _n(r.get("rank")) is not None:
            lector[str(r["symbol"]).upper()] = r
    q_raw = sorted(q_raw, key=lambda r: -(_n(r.get("score")) or 0))
    rows = [x for x in (board_row(r, inst, prov, lector, has_inst) for r in q_raw[:ROWS_MAX]) if x]
    universe, scored = int(_n(summ.get("universe")) or 0), int(_n(summ.get("scored")) or 0)
    nq = int(_n(summ.get("qualified")) if _n(summ.get("qualified")) is not None else len(q_raw))
    insuff = int(_n(summ.get("insufficient_data")) or 0)
    counts = {"universe": universe, "scored": scored, "qualified": nq, "insufficient": insuff}
    refused = None
    rej = [r for r in rows_all if r.get("qualified") is False and _n(r.get("score")) is not None]
    if isinstance(b.get("refused"), dict):
        rej = [b["refused"]]
    if rej:
        top = max(rej, key=lambda r: _n(r.get("score")))
        rs = _fails(top) or ([str(x) for x in top["reasons"]] if isinstance(top.get("reasons"), list) else [])
        refused = {"symbol": str(top.get("symbol") or ""), "score": _r(top["score"], 1), "reasons": rs,
                   "line": f"The highest raw score in the list, {top.get('symbol')} at {_r(top['score'], 1):.1f}, was refused: "
                           + ("; ".join(rs) if rs else "reason not stated")}
    head = (f"{nq} of {scored:,} scored names passed the gate" + (f"; {insuff} read insufficient data and carry no score" if insuff else "")
            if scored else f"{nq} names passed the gate")
    gen = _day(_gen(mg))
    sess = str(summ.get("as_of_session") or "") or _sess(mg)
    st, note = _fresh(gen, when, "Board", PREOPEN_AT)
    study = (mg.get("studies") or {}).get("gap_fill") if isinstance(mg.get("studies"), dict) else None
    base = ("Base rate for these triggers: no data: " + str(study.get("reason") if isinstance(study, dict) and study.get("reason")
            else "the studies have not published") if not (isinstance(study, dict) and study.get("state") in ("ok", "graded"))
            else f"Gap-fill study: {study.get('line') or 'published'}")
    shown = (f"Showing {len(rows)} of {nq} qualified names, best score first" if rows else
             "No names are shown: " + ("none passed the gate today" if nq == 0 else "the rows are not in the feed"))
    if not rows and nq:
        st = "partial"
        note = note or "the board summary is published but its rows are not"
    return {"status": st if st != "ok" else "ok", "reason": note, "as_of": sess,
            "vintage": f"completed sessions, as of the {sess} close" if sess else "session not stated",
            "delay": "Daily triggers only; the pre-open rows are the graded ones", "gate": GATE, "counts": counts,
            "headline": head, "rows": rows, **({"refused": refused} if refused else {}), "shown_line": shown,
            "lector_line": ("Chart-review rank is the Lector's own ranking, shown beside each row and never blended in"
                            if lector else "no data: the chart-review ranking has not published"),
            "base_rate": base, "grade_line": gr["board"], "label": "TRADE where the ladder is complete"}


# ---- The Golden Sweep Wire -------------------------------------------------------------------------------------------

def occ(sym):
    """(root, expiry date, 'call'|'put', strike) from an OCC contract symbol, or None"""
    m = OCC.match(str(sym or ""))
    if not m:
        return None
    try:
        exp = date(2000 + int(m.group(2)), int(m.group(3)), int(m.group(4)))
    except ValueError:
        return None
    return m.group(1), exp, ("call" if m.group(5) == "C" else "put"), int(m.group(6)) / 1000.0


def _outcome(a, t):
    """the print's own later grade: forward return of the underlying at +1h and +1d from the print, fixed horizons only"""
    o = a.get("outcome") if isinstance(a.get("outcome"), dict) else {}
    out = {}
    pending = "pending"
    for k, nm in (("h1", "+1h"), ("d1", "+1d")):
        v = o.get(k) if isinstance(o.get(k), dict) else o.get(k)
        r = _n(v.get("ret_pct")) if isinstance(v, dict) else _n(v)
        if r is not None:
            out[k] = {"status": "ok", "ret_pct": _r(r, 2), "reason": None}
            out[k].pop("reason")
        else:
            due = None
            if t is not None:
                due = (t + timedelta(hours=1)).strftime("%H:%M ET") if k == "h1" else "the next close"
            out[k] = {"status": pending, "reason": f"not yet graded: {nm} lands " + (f"after {due}" if due else "when it matures")}
            if due:
                out[k]["due"] = due
    done = [k for k in out if out[k]["status"] == "ok"]
    line = ("; ".join(f"{('+1h' if k == 'h1' else '+1d')} {_signed(out[k]['ret_pct'], 2)}%" for k in done) if done else
            "not yet graded: the +1h and +1d forward returns of the underlying fill in at fixed horizons, never the high")
    return {**out, "state": "graded" if len(done) == 2 else "partial" if done else "pending", "line": line}


def _opening(a, size, kind):
    oi = _n(a.get("oi"))
    if oi is None:
        return no("no data: the print carries no strike open interest, so opening or closing cannot be called")
    if oi > 0 and size is not None and size >= oi:
        return {"status": "ok", "word": f"Opening: its size is {size / oi:.1f}x the strike's whole open interest, so new positions "
                                         f"at least in part"}
    return {"status": "ok", "word": "Not called: its size is within the strike's open interest, so it could open or close"}


def _week52(a, card):
    w = a.get("week52") if isinstance(a.get("week52"), dict) else (card.get("week52") if isinstance(card.get("week52"), dict) else None)
    spot = _n(a.get("spot")) if _n(a.get("spot")) is not None else _n(card.get("spot"))
    if not w or _n(w.get("hi")) is None or _n(w.get("lo")) is None or spot is None or w["hi"] <= w["lo"]:
        return no("no data: the tape feed carries no 52-week range for this underlying yet")
    pos = round((spot - w["lo"]) / (w["hi"] - w["lo"]) * 100, 0)
    return {"status": "ok", "pos_pct": pos, "word": f"{card.get('underlying')} sits {pos:.0f}% of the way up its 52-week range "
                                                    f"({_num(w['lo'], 0)} to {_num(w['hi'], 0)})"}


def wire_print(a, card):
    prem, size, heat = _n(a.get("premium")), _n(a.get("size")), _n(a.get("heat"))
    golden = bool(a.get("golden_sweep") if "golden_sweep" in a else a.get("golden"))
    if prem is None or not (golden or (heat is not None and heat >= 15)):
        return None
    sym = str(a.get("symbol") or a.get("contract") or "")
    p = occ(sym)
    t = _et(a.get("ts"))
    under = (p[0] if p else str(card.get("underlying") or card.get("symbol") or "")).upper()
    tags = []
    rules = []
    if golden:
        tags.append("Golden Sweep")
        rules.append("Golden Sweep: a sweep, size at least the strike's open interest, premium 1,000,000 dollars or more")
    if a.get("unusual"):
        tags.append("Unusual")
        rules.append("Unusual: 10% or more out of the money and 35 days or less to expiry")
    if heat is not None and heat >= 15:
        tags.append("Heat 15+")
        rules.append("Heat 15+: the Heat Score reached 15")
    sd = str(a.get("side") or "unknown")
    sw, sg = SIDES.get(sd, (sd.replace("_", " "), 0))
    sent = str(a.get("sentiment") or "") or None
    dte = (p[1] - t.date()).days if (p and t) else None
    kind = p[2] if p else None
    spot = _n(a.get("spot")) if _n(a.get("spot")) is not None else _n(card.get("spot"))
    line = f"{under} {kind or 'option'} {_num(p[3], 2).rstrip('0').rstrip('.') if p else ''}".strip()
    return {"ts": t.strftime("%H:%M ET") if t else None, "symbol": under, "contract": sym or None, "kind": kind,
            "strike": _r(p[3]) if p else None, "expiry": p[1].isoformat() if p else None, "dte": dte, "premium": _r(prem, 0),
            "size": int(size) if size is not None else None, "heat": _r(heat, 1), "tags": tags, "rules": rules, "side": sd,
            "side_word": sw, "sentiment": sent, "spot": _r(spot), "oi": _r(a.get("oi"), 0),
            "opening": _opening(a, size, kind), "week52": _week52(a, card), "outcome": _outcome(a, t),
            "label": "CONTEXT", "line": line}


def build_wire(ed, mg, gr, when):
    base = {"rule": WIRE_RULE, "measures": MEASURES, "label": "CONTEXT", "grade_line": gr["wire"],
            "coverage": "watched: SPY, QQQ, IWM, not the whole market; contracts up to 45 days out"}
    if mg is None:
        return no("no data: the options tape has not published (the edition carries no morgue block)", **base)
    tp = _cards_of(mg.get("tape"))
    if not tp:
        return no("no data: the morgue block carries no tape cards", **base)
    prints, total, qualified, golden = [], 0, 0, 0
    bias = []
    cap = None
    buys = no("no data: the tape card does not state its buys-only intake")
    for c in tp:
        und = str(c.get("underlying") or c.get("symbol") or "").upper()
        card = dict(c, underlying=und)
        total += int(_n(c.get("prints")) or 0)
        al = _list(c.get("alerts")) or _list(c.get("top_alerts"))
        for a in al:
            a2 = dict(a)
            if "golden" in a2 and "golden_sweep" not in a2:
                a2["golden_sweep"] = a2["golden"]
            pr = wire_print(a2, card)
            if pr:
                prints.append(pr)
        golden += int(_n(c.get("golden_sweeps")) or 0)
        for lb in c.get("labels") or []:
            if isinstance(lb, str) and lb not in bias:
                bias.append(lb)
        if _n(c.get("algo_buys_only_n")) and _n(c.get("algo_all_n")) and und == (tp[0].get("underlying") or tp[0].get("symbol")):
            n1, n2 = int(c["algo_buys_only_n"]), int(c["algo_all_n"])
            buys = {"status": "ok", "line": f"A buys-only intake (the FlowAlgo construction) would have seen {n1:,} of {n2:,} {und} "
                                            f"prints ({n1 / n2 * 100:.0f}%) and no bearish print at all; the Wire shows all prints"}
        cap = c.get("window") or cap
    prints.sort(key=lambda p: -p["premium"])
    qualified = len(prints)
    gen = _day(_gen(mg))
    tdates = []
    for c in tp:
        for a in _list(c.get("alerts")) or _list(c.get("top_alerts")):
            t = _et(a.get("ts"))
            if t:
                tdates.append(t.date())
    sess = max(tdates).isoformat() if tdates else (gen.isoformat() if gen else None)
    state = ed.get("session", {}).get("state")
    today = when.date()
    st, reason = "ok", None
    sd = _day(sess)
    if state == "pre" and (sd is None or sd < today):
        st, reason = "pending", "pre-market: tape opens 09:30 ET; these are the prints of the last session" + (f" ({sess})" if sess else "")
    elif sd is not None and sd < today and cal.is_trading_day(today) and state in ("open", "closed"):
        st, reason = "stale", f"no print has been published for today yet; these are from {sess}"
    if not prints:
        why = (reason or "no print has met the rule yet") if st != "ok" else "no print met the rule on the watched underlyings"
        if state == "pre":
            why = "pre-market: tape opens 09:30 ET; no print has met the rule"
        return no("no data: " + why if st == "ok" else why, status="pending" if state == "pre" else "no_data", **base,
                  as_of=sess, vintage="tape of completed prints, delayed", delay="Measured, not marketed: published on the tape job's run",
                  bias=" · ".join(bias) if bias else "side is a quote-at-print join, our construction",
                  counts={"prints_total": total, "qualified": 0, "golden": golden, "shown": 0}, prints=[], buys_only=buys)
    shown = prints[:PRINTS_MAX]
    return {"status": st, "reason": reason, "as_of": sess, "vintage": "tape of completed prints, fetched at the job's run",
            "delay": "Not real time: the feed is published after the job runs; the delay is shown, not hidden",
            "rule": WIRE_RULE, "coverage": base["coverage"], "bias": " · ".join(bias) if bias else
            "side is a quote-at-print join, our construction", "counts": {"prints_total": total, "qualified": qualified,
                                                                         "golden": golden, "shown": len(shown)},
            "prints": shown, "label": "CONTEXT", "measures": MEASURES, "grade_line": gr["wire"], "buys_only": buys}


# ---- the block -------------------------------------------------------------------------------------------------------

def _summary(m, b, w):
    def one(sec, ok_line):
        return ok_line if sec.get("status") not in ("no_data",) else sec.get("reason") or "no data"
    c = (m.get("cards") or [None])[0]
    ml = (f"{c['symbol']} {c['regime'].lower()}, flip {_num(c['flip'])} ({_signed(c['flip_pct'])}%), walls {_num(c['put_wall'], 0)} to "
          f"{_num(c['call_wall'], 0)}" if c and c.get("flip") is not None and c.get("flip_pct") is not None and c.get("put_wall") and c.get("call_wall")
          else f"{c['symbol']} {c['regime'].lower()}" if c else None)
    bl = b.get("headline")
    c2 = w.get("counts") or {}
    wl = (f"{c2.get('qualified', 0)} print{'' if c2.get('qualified', 0) == 1 else 's'} met the rule, "
          f"{c2.get('golden', 0)} Golden Sweep{'' if c2.get('golden', 0) == 1 else 's'}" if w.get("status") != "no_data" else None)
    return {"map": one(m, ml), "board": one(b, bl), "wire": one(w, wl)}


def build(ed):
    """the `funnel` block for an edition dict `ed` (its `morgue` key is read, never changed), or None for a non-dict"""
    if not isinstance(ed, dict):
        return None
    mg = ed.get("morgue") if isinstance(ed.get("morgue"), dict) else None
    when = _when(ed)
    gr = grade(_score(mg) if mg else None)
    m, b, w = build_map(ed, mg, gr, when), build_board(ed, mg, gr, when), build_wire(ed, mg, gr, when)
    secs = (m, b, w)
    live = [s for s in secs if s["status"] in ("ok", "pending", "stale", "partial")]
    status = "ok" if len(live) == 3 and all(s["status"] == "ok" for s in secs) else "partial" if live else "no_data"
    gen = _gen(mg) if mg else None
    corr = [str(x) for x in (mg or {}).get("corrections", []) if isinstance(x, str)] if isinstance((mg or {}).get("corrections"), list) else []
    return {"schema": SCHEMA, "as_of": _sess(mg or {}), "built_at": str(gen) if gen else None, "status": status,
            "reason": None if live else (m.get("reason") or "no data"), "scoring": gr,
            "rhythm": {"preopen": f"{PREOPEN_AT[0]:02d}:{PREOPEN_AT[1]:02d} ET", "postclose": f"{POSTCLOSE_AT[0]:02d}:{POSTCLOSE_AT[1]:02d} ET",
                       "policy": "Published once a trading day, never updated intraday. A correction is a new dated note, never an edit. "
                                 "Every card is written to the record before it is shown.",
                       "published": str(gen) if gen else None,
                       "next": _next(when), "corrections": corr},
            "labels": ["TRADE: complete buy, invalidation and targets", "CONTEXT: a measurement",
                       "STRETCH: price already past the ladder"],
            "summary": _summary(m, b, w), "map": m, "board": b, "wire": w}


def _next(when):
    """the next scheduled publication, as the rhythm states it"""
    d = when.date()
    minutes = when.hour * 60 + when.minute
    if cal.is_trading_day(d):
        if minutes < PREOPEN_AT[0] * 60 + PREOPEN_AT[1]:
            return f"Map and Board today about {PREOPEN_AT[0]:02d}:{PREOPEN_AT[1]:02d} ET"
        if minutes < POSTCLOSE_AT[0] * 60 + POSTCLOSE_AT[1]:
            return f"Tape and scorecards today about {POSTCLOSE_AT[0]:02d}:{POSTCLOSE_AT[1]:02d} ET"
    n = cal.next_trading_day(d)
    return f"Map and Board {n.strftime('%a %Y-%m-%d')} about {PREOPEN_AT[0]:02d}:{PREOPEN_AT[1]:02d} ET"
