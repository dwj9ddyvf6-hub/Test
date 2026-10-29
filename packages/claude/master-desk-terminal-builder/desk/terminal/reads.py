"""The roster read: every roster name read once a session (desk/terminal/read), for the board's pool, the watching
list and Look up.

Job `terminal_reads` (desk/jobs.py), hourly in the evenings and at weekends, on the cache only. It gates itself: when
reads.json already holds a complete read of SPY's last session it returns at once; a read made while part of the roster
still lacks that session (the genome job's top-up runs 16:21-19:30 ET) is marked incomplete and made again next hour.
A run:
  - reads the 1,838-name roster (and the funds the names follow, and the sector funds of the desk's map) in batches of
    200 from the split-adjusted daily cache, five years each (the weekly count; the daily read uses the last two), and
    the earnings cache with the reports already made (the desk's Nasdaq archive), the market read and the fear-day rule
    for each name;
  - writes state/terminal/reads.json (internal: every public read and its record, with prices, never published; and
    the session's McClellan oscillator over the roster's stocks, "mco", for the lenses: read/lenses.py) and
    cache/terminal/reads/ (public: reads-index.json, one line per name, and reads-<letter>.json, the full read of each
    name by its first letter; no price, validated against READ_ALLOWED);
  - never raises: a name that fails to read is counted and skipped; a name whose prices stopped more than STALE
    sessions before SPY's is counted and left out; a read whose shown prices fail the publisher's check
    (desk/terminal/prices.py) is held back, its reasons kept in reads.json ("held"), never published.
The terminal job reads reads.json; the publisher copies the public files beside the edition."""
import json
import os
import time
from datetime import datetime

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic
from . import cautions as cautionsmod
from . import engine as enginemod
from . import fear as fearmod
from . import prices
from .read import clx, compose, indicators
from .read import lenses as lensmod
from .read import optnews as optfacts
from .read import sheet as sheetmod

BATCH = 200
CLX_BARS = 520                  # ChartsLector's readings on the daily read's own window (core.BARS_USED)
BARS = 1300                     # five years: the weekly count (his higher timeframe) needs them; the daily read uses
                                # the last 520 (core.BARS_USED)
READY = 0.9                     # the share of the roster that must hold SPY's last session for a read to be complete
STALE = 5                       # a name whose last close is more than 5 sessions before SPY's is left out: its prices
                                # stopped (delisted, renamed or halted), so its read is no read of the stock today
MIN_PRICE, MIN_DOLLAR_VOLUME = 5.0, 20e6
SHARD_DROP = ("marks", "lines")  # the drawing (read/geometry.py) goes on the board's cards and watching rows only: on
                                # 11 real reads it is 18% of a read's bytes and 28% gzipped, which every Look up shard
                                # (about 231 KB gzipped a letter) would carry for 1,838 names

# every key a public read may carry, by path ("[]" = each element of a list)
READ_ALLOWED = {
    "": {"symbol", "as_of", "action", "form", "conviction", "gut", "plan", "gist", "standouts", "against", "take",
         "change", "considered", "evidence", "fear", "liquid", "sheet", "material", "news", "close", "marks", "lines",
         "avgs", "sheet_side", "cautions"},
    "conviction": {"level", "word"},
    "gut": {"word", "why"},
    "plan": {"zone_lo", "zone_hi", "trigger", "out", "t1", "t2", "r", "risk_atr", "by", "window", "sessions",
             "sentence", "why_zone", "why_out", "why_t1", "breakeven", "mode", "trim", "r2", "why_t2",
             "time_stop"},
    "standouts[]": {"head", "text", "learn"},
    "against[]": {"head", "text", "learn"},
    "material[]": {"head", "text", "learn"},
    "sheet": set(sheetmod.BY_ID),                  # the owner's list: a line's id -> what the read found for it
    "sheet_side": set(sheetmod.BY_ID),             # and which way that answer points: 1, 0 or -1 (sheet.sides)
    "fear": {"state", "fund", "date", "label", "short", "text"},
    "news[]": {"headline", "source", "at", "url"},   # the latest headlines, untrusted text (read/optnews.headlines)
    "cautions[]": {"key", "head", "text", "credit"},  # ChartsLector's grade-A warnings in their tiers (cautions.py)
    "marks[]": {"d", "label", "kind"},               # the read drawn (read/geometry.py): every bar its words name,
    "lines[]": {"d1", "p1", "d2", "p2", "label", "kind"},   # its detectors' own lines in dollars,
    "avgs": {"sma20", "sma50", "sma200"},            # and the averages its words name, in dollars
}
READ_LEAVES = {"why", "considered"}


def validate(rd, path=""):
    """raise ValueError on any key outside READ_ALLOWED"""
    allowed = READ_ALLOWED.get(path)
    if allowed is None:
        raise ValueError(f"unexpected object at {path or 'top'}")
    for k, v in rd.items():
        child = f"{path}.{k}" if path else k
        if k not in allowed:
            raise ValueError(f"key not in the read contract: {child}")
        if isinstance(v, dict):
            validate(v, child)
        elif isinstance(v, list) and k in READ_LEAVES:
            if any(isinstance(x, (dict, list)) for x in v):
                raise ValueError(f"{child} must hold plain values")
        elif isinstance(v, list):
            for x in v:
                validate(x, child + "[]")
    return rd


def public(pub):
    """the published form of a read: the read without its internal fields, with the plan's break-even rate"""
    out = {k: v for k, v in pub.items() if not k.startswith("_")}
    pl = dict(out["plan"])
    if pl.get("breakeven") is None:                    # the read states its own (compose.breakeven)
        pl["breakeven"] = round(1.0 / (1.0 + pl["r"]), 2) if pl.get("r") else None
    out["plan"] = pl
    return out


def today_fear(sym, fund, bars_by_sym):
    """the fear-day rule on the name's last session: its fund and the name both closed red (None when they did not or
    a close is missing)"""
    a, b = bars_by_sym.get(sym) or [], bars_by_sym.get(fund) or []
    if len(a) < 2 or len(b) < 2:
        return None
    da, db = cal._as_date(float(a[-1]["t"])), cal._as_date(float(b[-1]["t"]))
    if da != db or not (float(a[-1]["c"]) < float(a[-2]["c"]) and float(b[-1]["c"]) < float(b[-2]["c"])):
        return None
    day = fearmod._day(da)
    both = sym if fund == sym else f"{fund} and {sym}"
    return {"state": "came", "fund": fund, "date": da.isoformat(), "label": f"Fear day: {day}", "short": day,
            "text": f"{day}: {both} {'closed' if fund == sym else 'both closed'} red, the kind of day the desk's "
                    "fear-day rule buys."}


def extra_for(sym, fund, bars_by_sym, earnings, market, today, desk=None, rates=None, optnews=None):
    """the context a read weighs beside the chart: the desk's strategies, earnings, the market and the fear-day rule;
    rates: the session roster's shares of each reading (rates_of), which rank what stands out; and for the indicators
    (read/indicators.py) SPY's, QQQ's and the sector fund's bars and the earnings reports already made (with_reports);
    optnews: the session's options and news gather (desk/terminal/optnews.py), read as context"""
    ex = {"market": market or {}}
    if rates:
        ex["rates"] = rates
    if optnews:
        ex["optnews"] = optnews
    e = (earnings or {}).get(sym) or {}
    if e.get("date") and e["date"] >= today.isoformat():
        ex["earnings"] = e["date"]
    if e.get("reports"):
        ex["reports"] = e["reports"]
    if bars_by_sym.get("SPY"):
        ex["spy"] = bars_by_sym["SPY"]
    if bars_by_sym.get("QQQ"):
        ex["qqq"] = bars_by_sym["QQQ"]                   # the lenses' strength against growth (read/lenses.py)
    sec = indicators.sector_of(sym)
    if sec and bars_by_sym.get(sec):
        ex["sector"] = {"sym": sec, "bars": bars_by_sym[sec]}
    f = today_fear(sym, fund, bars_by_sym)
    if f:
        ex["fear"] = f
    if desk:
        ex["desk"] = desk
    return ex


def with_reports(root, earnings, names, until):
    """the earnings calendar with each name's reports already made beside its next date: [[date, release tag]],
    oldest first, from the desk's Nasdaq earnings archive (feedlib/griffith_earnings: every reporter, three years),
    dated on or before `until`, with a reported EPS. The read anchors a VWAP at the last one's first session and dates
    a listing by them (read/indicators.py); a report whose session the bars do not hold yet is passed over there"""
    from ..feedlib import griffith_earnings
    out = dict(earnings or {})
    try:
        made_by = griffith_earnings.announcements(root, list(names), until)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return out          # an unreadable archive costs the two readings it feeds, never the edition
    for sym, rows in made_by.items():
        made = [[r["date"], r.get("time")] for r in rows if r.get("eps") is not None]
        if made:
            out[sym] = dict(out.get(sym) or {}, reports=made)
    return out


def sector_funds_of(syms):
    """the sector funds of these names on the desk's map (read/indicators.sector_of): bars every read of them needs"""
    return {f for f in map(indicators.sector_of, syms) if f}


def liquid(bars):
    """(close, 20-session median dollar volume) and whether both clear the board's bar"""
    if len(bars) < 20:
        return False
    dv = sorted(float(b["c"]) * float(b.get("v") or 0) for b in bars[-20:])[10]
    return float(bars[-1]["c"]) >= MIN_PRICE and dv >= MIN_DOLLAR_VOLUME


def read_one(sym, bars_by_sym, earnings, market, today, desk=None, rates=None, optnews=None, held=None, screen=None):
    """(public read, record) for one name, or None; with the session's gather (optnews), its latest headlines; with
    the analysis engine's screen (screen), its tier, and ChartsLector's cautions in the tiers they hold for (both the
    read and its record carry them: context, voting nothing). A read whose shown prices fail the publisher's check
    (prices.check) is held back: None, its reasons in `held`"""
    from ..lab import own_index
    fund = own_index(sym)
    bars = bars_by_sym.get(sym) or []
    r = compose.read(sym, bars, fund, bars_by_sym.get(fund) or [],
                     extra_for(sym, fund, bars_by_sym, earnings, market, today, desk, rates, optnews))
    if not r:
        return None
    pub, rec = r
    tier = enginemod.tier(screen, sym, bars)
    if tier in ("micro", "nano"):                     # the tiers whose rows of the study are grade A (cautions.py)
        cs = cautionsmod.cautions(clx.readings(bars[-CLX_BARS:]), tier, bars)
        if cs:
            pub["cautions"], rec["cautions"] = cs, [c["key"] for c in cs]
    veto = cautionsmod.veto(enginemod.vetoed(screen, sym, pub["as_of"]))
    if veto:                                          # the engine's veto where it is in force: the record is unchanged
        pub["cautions"] = (pub.get("cautions") or []) + [veto]
    pub = compose.face_guard(public(pub))            # the card face in plain words, failing closed (read/plain.py)
    news = optfacts.headlines(sym, pub["as_of"], optnews)
    if news:
        pub["news"] = news
    if "fear" not in pub and pub["form"] != "wait":   # the card's fear-day label (the edition sets its own on a
                                                      # listing); the rule buys, and a read that stands aside buys nothing
        f = today_fear(sym, fund, bars_by_sym)
        if f:
            pub["fear"] = f
    pub["liquid"] = liquid(bars)
    if bars and bars[-1].get("c") is not None:     # the as-of close: every level on the page is shown in dollars
        pub["close"] = round(float(bars[-1]["c"]), 4)
    pub, why = prices.check(pub, prices.session_high(bars, pub["as_of"], pub.get("close")))
    if why:
        if held is not None:
            held[sym] = why
        return None
    return validate(pub), rec


def roster():
    from .market import ROSTER
    try:
        names = [s.strip() for s in open(ROSTER) if s.strip()]
    except OSError:
        names = []
    return sorted(set(names))


def run(engine, now=None):
    """read the roster into state/terminal/reads.json and cache/terminal/reads/ -> the job's info"""
    root = engine.root
    now = float(engine.clock() if now is None else now)
    t0 = time.time()
    today = cal._as_date(now)
    hub = engine.hub
    funds = ["QQQ", "SPY"] + indicators.sector_funds()       # the sector funds: each name's relative strength
    fund_bars = hub.bars("equity_split", "1d", funds, BARS, cache_only=True) or {}
    spy = fund_bars.get("SPY") or []
    if not spy:
        return {"ok": False, "error": "no SPY bars in the cache"}
    last = cal._as_date(float(spy[-1]["t"])).isoformat()
    cutoff = cal._as_date(float(spy[-STALE - 1]["t"])).isoformat() if len(spy) > STALE else last
    path = os.path.join(root, "state", "terminal", "reads.json")
    prev = read_json(path, {}) or {}
    if prev.get("as_of") == last and prev.get("complete"):
        return {"ok": True, "skipped": "current", "as_of": last}
    market = read_json(os.path.join(root, "cache", "terminal", "market.json"), {}) or {}
    names = roster()
    earnings = with_reports(root, read_json(os.path.join(root, "cache", "earnings.json"), {}) or {}, names, last)
    from .. import code_identity
    code = (code_identity() or {}).get("commit")              # which code wrote each read (the audit's F20)
    desk = strategies(root, now)                               # the desk's strategies, counted as the edition counts them
    from . import optnews
    opt = optnews.load(root)                                   # the session's options and news (the board's names)
    mom6 = {}                                                  # each name's 6-month momentum: its rank on the roster
    screen = enginemod.latest(root, last)                     # the engine's newest screen: each name's tier
    breadth = {}                                               # the roster's advancers and decliners by session

    held = {}                                                  # reads the publisher's price check held back

    def read_all(rates):
        reads, records, failed, stale = {}, {}, 0, 0
        held.clear()
        for i in range(0, len(names), BATCH):
            batch = names[i:i + BATCH]
            try:
                got = hub.bars("equity_split", "1d", batch, BARS, cache_only=True) or {}
            except Exception:                                 # noqa: BLE001  (a batch the cache cannot serve)
                failed += len(batch)
                continue
            got.update(fund_bars)
            for sym in batch:
                try:
                    r = read_one(sym, got, earnings, market, today, desk=desk.get(sym), rates=rates, optnews=opt,
                                 held=held, screen=screen)
                except Exception:                             # noqa: BLE001  (one name never stops the roster)
                    failed += 1
                    continue
                if r and r[0]["as_of"] < cutoff:
                    stale += 1                                # its prices stopped: delisted, renamed or halted
                elif r:
                    reads[sym], records[sym] = r
                    records[sym]["code"] = code
                    if rates is None:
                        mom6[sym] = indicators.mom6_of(got.get(sym))
                        if sym not in fund_bars:               # the stocks, not the funds (LDR-1's breadth)
                            lensmod.breadth(breadth, got.get(sym))
            del got
        return reads, records, failed, stale
    # twice: the first read counts how much of the session's roster shows each reading, the second ranks what stands
    # out on each name by those shares (call.surprise); the facts, the evidence and the plans are the same both times.
    # The first also keeps each name's 6-month momentum: its percentile goes to the second with the shares
    reads, records, failed, stale = read_all(None)
    rates = dict(rates_of(records), **indicators.ranks(mom6))
    if records:
        reads, records, failed, stale = read_all(rates)
    current = sum(1 for r in reads.values() if r["as_of"] == last)
    complete = bool(names) and current >= READY * len(names)
    doc = {"as_of": last, "complete": complete, "current": current,
           "generated_at": datetime.fromtimestamp(now, tz=ET).isoformat(timespec="seconds"),
           "reads": reads, "records": records, "rates": rates, "held": dict(held)}
    mco = lensmod.mcclellan(breadth, last)
    if mco is not None:                                       # the Market lens's McClellan oscillator (read/lenses.py)
        doc["mco"] = {"as_of": last, "value": mco}
    zbt = lensmod.zweig_thrust(breadth, last)
    if zbt is not None:                                       # Zweig's breadth thrust over the same counts (vendor_ext)
        doc["zbt"] = zbt
    write_json_atomic(path, doc)
    publish_files(root, reads, last)
    info = {"names": len(names), "read": len(reads), "current": current, "complete": complete, "failed": failed,
            "stale": stale, "held": len(held), "as_of": last, "seconds": round(time.time() - t0, 1), "ok": bool(reads)}
    if complete:
        info["ledger"] = run_ledger(root, hub, last, reads, records)
    return info


def strategies(root, now):
    """{symbol: {"engines", "holds"}}: every name an eligible desk strategy signalled to buy in the edition's window
    (the session's after its close), as the edition reads it (terminal.nominees), so a name reads the same on the
    board and in Look up. {} when the ledger or the manifest cannot be read"""
    try:
        from .. import registry
        from . import distill, nominees
        recs = distill.ledger_signals(os.path.join(root, "state", "ledger.jsonl"), distill.window_start(now))
        books = read_json(os.path.join(root, "state", "books.json"), {}) or {}
        nom, _ = nominees(recs, registry.manifest_rows(root), books)
    except Exception:                                         # noqa: BLE001  (the read never stops on the ledger)
        return {}
    return {s: {"engines": d["engines"], "holds": d["holds"]} for s, d in nom.items()}


def rates_of(records):
    """{key|side: the share of the session's reads showing that reading, "_n": the reads}: each read counted once
    per reading (the records' facts, every fact with a side)"""
    n, counts = len(records), {}
    for rec in records.values():
        for k in {f"{key}|{side}" for key, side, _ in rec.get("facts") or ()}:
            counts[k] = counts.get(k, 0) + 1
    out = {k: round(v / n, 6) for k, v in sorted(counts.items())} if n else {}
    out["_n"] = n
    return out


def run_ledger(root, hub, last, reads, records):
    """the forward ledger (ledger.py): the session's reads written once, then every unsettled read scored on the cache.
    It never stops the roster job: a failure is reported and the next session tries again"""
    from . import ledger
    t0 = time.time()
    try:
        rows = ledger.record_session(root, last, reads, records)
        summary = ledger.update(root, lambda syms: hub.bars("equity_split", "1d", syms, BARS, cache_only=True) or {},
                                last)
        return {"rows": rows, "final": summary["final_episodes"], "live": summary["live_episodes"],
                "seconds": round(time.time() - t0, 1)}
    except Exception as e:                                    # noqa: BLE001  (the ledger never stops the read)
        return {"error": repr(e)[:200], "seconds": round(time.time() - t0, 1)}


def shard(sym):
    c = sym[:1].upper()
    return c if "A" <= c <= "Z" else "0"


def publish_files(root, reads, as_of):
    """cache/terminal/reads/: reads-index.json ({as_of, names: {symbol: [action, conviction word, take word]}}) and
    reads-<letter>.json ({symbol: read}). Each file is written aside and moved into place whole, and a shard that is
    no longer needed is removed only after, so the publisher never copies a cut file (the audit's F21)"""
    out = os.path.join(root, "cache", "terminal", "reads")
    os.makedirs(out, exist_ok=True)

    def put(name, doc):
        tmp = os.path.join(out, "." + name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, os.path.join(out, name))
    index = {s: [r["action"], r["conviction"]["word"], r["gut"]["word"]] for s, r in sorted(reads.items())}
    by = {}
    for s, r in reads.items():                           # Look up's cards carry no chart drawing (SHARD_DROP)
        by.setdefault(shard(s), {})[s] = {k: v for k, v in r.items() if k not in SHARD_DROP}
    for k, v in by.items():
        put(f"reads-{k}.json", v)
    put("reads-index.json", {"as_of": as_of, "names": index})
    keep = {f"reads-{k}.json" for k in by} | {"reads-index.json"}
    for name in os.listdir(out):
        if name.startswith("reads-") and name.endswith(".json") and name not in keep:
            os.remove(os.path.join(out, name))
