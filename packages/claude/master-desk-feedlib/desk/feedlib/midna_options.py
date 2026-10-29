"""The listed chains Midna's option books and QQQ ladder trade — scripts/option-marks.ts (@ entire 43f08f96; the
paper-desk 68315288 copy is the same file without the ladder's QQQ lines) ported line for line, run as the family job
`midna_option_marks` instead of the detached script.

  names     optionChainSymbols(board, quantpedia, held roots): the board's breakout / exit names in the listed
            surface universe, the five worst prior-month losers, both legs of every |z| >= 2 pair, the roots of open
            packages — and QQQ (the ladder)
  chain     Cboe's delayed quotes (cdn.cboe.com/api/global/delayed_quotes/options/<SYM>.json): every OCC row of the
            root, per expiration its sorted strikes and {"C|P:<strike>": {bid, ask}} (a missing bid / ask is 0)
  keep      the expiration nearest 30 days (14..60, a tie takes the later), the expirations of open positions, and
            for QQQ every expiration 38..52 days out (the ladder window)
  name      {spot: current_price, day: last_trade_time[:10] (else today), error, expirations}; a failure keeps the
            name with its error
  file      {builtAt, signalAsOf (the later of the board / quantpedia asOf), names} -> cache/midna/option_marks.json

Named divergences: the detached script's file hand-off (data/equity-desk/option-marks.json) is the job's cache read
in-pass; the held positions come from the desk's books (the sleeves' option positions and their records) instead of
state.json's shadow.listed / shadow.ladder; builtAt is kept as epoch seconds."""
import os
import re
from datetime import date

from ..data.http import get
from ..sleeves.midna import common as M
from ..util import read_json, write_json_atomic

# options-surface.ts COMPARE_UNIVERSE: "the liquid listed-option set, written down before any reading"
SURFACE = ("AAPL", "AMD", "AMZN", "AVGO", "BA", "COIN", "COST", "CRM", "DIA", "GOOGL", "GS", "HD", "INTC", "IWM", "JPM",
           "LLY", "META", "MSFT", "MSTR", "MU", "NFLX", "NVDA", "ORCL", "QQQ", "SMH", "SPY", "TLT", "TSLA", "UNH", "XLF")
OCC_RE = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")
OPT_SLOTS = 5
PATH = os.path.join("cache", "midna", "option_marks.json")


def parse_occ(symbol):
    m = OCC_RE.match(symbol or "")
    if not m:
        return None
    yy = int(m.group(2)[:2])
    exp = f"{1900 + yy if yy >= 70 else 2000 + yy}-{m.group(2)[2:4]}-{m.group(2)[4:6]}"
    return {"root": m.group(1), "expiration": exp, "right": m.group(3), "strike": int(m.group(4)) / 1000}


def calendar_days(frm, to):
    return M.js_round((date.fromisoformat(to) - date.fromisoformat(frm)).days)


def pick_expiration(session, expirations):
    best = None
    for e in expirations:
        dte = calendar_days(session, e)
        if dte < 14 or dte > 60:
            continue
        dist = abs(dte - 30)
        if best is None or dist < best[1] or (dist == best[1] and e > best[0]):
            best = (e, dist)
    return best[0] if best else None


def ladder_window(session, expirations):
    return [e for e in expirations if 38 <= calendar_days(session, e) <= 52]


def contract_key(right, strike):
    return f"{right}:{M.js_num(strike)}"


def chain_symbols(board, qp, held=()):
    """option-books.ts optionChainSymbols."""
    syms = set(held)
    for bar in (board or {}).get("bars") or []:
        if (bar.get("enter20") or bar.get("enter55") or bar.get("exit10")) and bar.get("sym") in SURFACE:
            syms.add(bar["sym"])
    losers = sorted((qp or {}).get("reversal") or [], key=lambda r: r["ret"])[:OPT_SLOTS]
    for r in losers:
        syms.add(r["sym"])
    for r in (qp or {}).get("pairs") or []:
        if abs(r["z"]) < 2:
            continue
        syms.add(r["a"])
        syms.add(r["b"])
    return sorted(s for s in syms if s)


def build_name(sym, body, keep, today):
    """loadName on a Cboe body (None / missing data -> the source's empty name)."""
    data = (body or {}).get("data") or {}
    if not data.get("current_price") or not (data["current_price"] > 0) or not data.get("options"):
        return {"spot": 0, "day": "", "error": "Cboe had no option chain", "expirations": {}}
    all_ = {}
    for row in data["options"]:
        p = parse_occ(str(row.get("option") if row.get("option") is not None else ""))
        if not p or p["root"] != sym:
            continue
        book = all_.setdefault(p["expiration"], {"strikes": [], "contracts": {}})
        if p["strike"] not in book["strikes"]:
            book["strikes"].append(p["strike"])
        bid = row["bid"] if isinstance(row.get("bid"), (int, float)) and not isinstance(row.get("bid"), bool) else 0
        ask = row["ask"] if isinstance(row.get("ask"), (int, float)) and not isinstance(row.get("ask"), bool) else 0
        book["contracts"][contract_key(p["right"], p["strike"])] = {"bid": bid, "ask": ask}
    for book in all_.values():
        book["strikes"].sort()
    wanted = list(dict.fromkeys(keep))
    picked = pick_expiration(today, list(all_))
    if picked and picked not in wanted:
        wanted.append(picked)
    if sym == "QQQ":
        for e in ladder_window(today, list(all_)):
            if e not in wanted:
                wanted.append(e)
    exps = {e: all_[e] for e in wanted if e in all_}
    ltt = data.get("last_trade_time")
    day = ltt[:10] if isinstance(ltt, str) and len(ltt) >= 10 else today
    return {"spot": data["current_price"], "day": day,
            "error": None if exps else "No expiration between 14 and 60 days", "expirations": exps}


def build_marks(now, board, qp, held_roots, held_exps, getter=None):
    getter = getter or (lambda url: get(url, timeout=60))
    symbols = sorted(set(chain_symbols(board, qp, held_roots)) | {"QQQ"})
    today = M.et_ymd(now)
    names = {}
    for sym in symbols:
        try:
            body = getter(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json")
        except Exception as e:                              # noqa: BLE001 — the name stays, with its error
            names[sym] = {"spot": 0, "day": "", "error": str(e)[:200], "expirations": {}}
            continue
        if body is None:
            names[sym] = {"spot": 0, "day": "", "error": "Cboe returned 404", "expirations": {}}
            continue
        names[sym] = build_name(sym, body, held_exps.get(sym) or [], today)
    days = sorted(d for d in ((board or {}).get("asOf"), (qp or {}).get("asOf")) if d)
    return {"builtAt": now, "signalAsOf": days[-1] if days else None, "names": names}


def held_options(engine):
    """the roots / expirations of every open option position of the Midna option sleeves (heldChains)."""
    roots, exps = set(), {}
    for sid in ("midna_opt_turtle_atm_call", "midna_opt_reversal_call_spread", "midna_opt_distance_pair",
                "midna_qqq_csp_ladder"):
        book = engine.books.books.get(sid) if engine is not None else None
        for inst in (book.positions if book else {}):
            if not inst.startswith("OPT:"):
                continue
            p = parse_occ(inst[4:])
            if not p:
                continue
            roots.add(p["root"])
            lst = exps.setdefault(p["root"], [])
            if p["expiration"] not in lst:
                lst.append(p["expiration"])
    return sorted(roots), exps


def job(engine):
    now = engine.clock()
    feeds = engine.feeds
    board = feeds.get("midna_board_signals", None, now) if feeds is not None else None
    qp = feeds.get("midna_qp_signals", None, now) if feeds is not None else None
    roots, exps = held_options(engine)
    marks = build_marks(now, board, qp, roots, exps)
    path = os.path.join(engine.root, PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_json_atomic(path, marks)
    return {"names": len(marks["names"]), "errors": sum(1 for n in marks["names"].values() if n["error"])}


def feed_marks(feeds, sleeve, now, arg=None):
    eng = getattr(sleeve, "engine", None)
    root = eng.root if eng is not None else os.path.dirname(os.path.dirname(feeds.hub.cache.root))
    return read_json(os.path.join(root, PATH), None)
