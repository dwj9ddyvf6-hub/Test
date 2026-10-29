"""The public terminal: each edition distils the desk's state into one small public page.

Every 30 minutes on the ET clock (job `terminal`, desk/jobs.py) the job:
  1. reads what the desk already keeps -- the ledger's recent passes, the manifest, the books, the roster's reads
     (state/terminal/reads.json, written once a session by job `terminal_reads`, desk/terminal/reads.py), and the
     caches of daily and hourly bars, the VIX series and the release calendar; it fetches no market data;
  2. reads afresh every name a desk strategy signalled to buy (desk/terminal/read: one decisive long plan from
     everything the desk measures, its strategies counted as evidence), picks the board, keeps a listed name while its
     call is live and ranks in the top ten, and lists the breakout plans nearest their triggers (board.py); every
     listed setup becomes a call, written before its outcome and scored on daily bars (calls.py); the market read
     (market.py) and the owner's fear-day status (fear.py);
  3. writes the edition (state/terminal/edition.json, schema master-desk-terminal/2: allow-listed, no prices, no
     positions, no balances) and publishes it with the static page, the roster's reads and the Desk tab's data (the
     desk's own books and record, deskview.py: its own allow-listed files, never the edition's).
Nothing here changes a sleeve, an order or the books; a failure is the job's, never the loop's.
Design and acceptance matrices: docs/research/2026-10-18-terminal/DESIGN.md and SETUPS_V2.md."""
import os
from datetime import datetime, timedelta

from .. import calendar as cal
from .. import registry
from ..util import ET, read_json, write_json_atomic
from . import board as boardmod
from . import calls as callbook
from . import cautions as cautionsmod
from ..morgue import edition as morgue_edition                 # the Morgue Engine's `morgue` key (desk/morgue/edition.py)
from . import deskview, distill, market, optnews, prices, publish
from . import engine as enginemod
from . import funnel as funnelmod
from . import fear as fearmod
from . import lod as lodmod
from . import coherence as coherencemod
from . import context as contextmod
from . import vendor_ext
from . import pickcard
from .read.call import R_HIGH
from . import lector as lectormod
from ..picker import fearday as feardaymod
from ..picker import heur as heurmod
from ..picker import lens as lenspick
from . import ranking
from . import record as recordmod
from . import reads as readsmod
from .read import diet, geometry, integrity
from .read import lenses as lensmod
from .read import optnews as optfacts
from .read import sheet as sheetmod
from .read.compose import face_guard, watch_guard

SCHEMA = "master-desk-terminal/2"
CADENCE_MIN = 10
NAME = "Master Desk"
DEPARTURES_KEPT = 6
PICKERS = ("fearday", "v2")
DEFAULT_PICKER = "fearday"      # config terminal.picker (owner, 2026-10-27): the Fear-Day Buy List; "v2" the old board
PICKER_BARS = 420               # the fear-day list's history: 252-day norms plus their own windows
BARS = 1300                     # five years, as the roster read (reads.BARS): the weekly count

_READ = readsmod.READ_ALLOWED
RECORD_LINE = {"type", "state", "n", "first", "hit_rate", "avg_r", "text"}       # record.py: the row's type, graded
SUMMARY = {"calls", "closed", "won", "lost", "even", "hit_rate", "avg_r", "total_r", "avg_give_back", "small_n",
           "to_first_read"}
# every key an edition may carry, by path ("[]" = each element of a list, "*" = each value of a dict)
ALLOWED = {
    "": {"schema", "seq", "edition", "generated_at", "next_at", "cadence_min", "session", "desk", "market", "setups", "brief",
         "watching", "lookup", "departures", "scorecard", "calls", "calls_chain", "record", "notes", "fear", "factors",
         "ranked", "lector", "strip", "picker", "heur", "morgue", "vendor"},
    **morgue_edition.ALLOWED,                      # morgue.* (desk/morgue/edition.py, docs/research/MORGUE_SCHEMA.md)
    "strip": {"as_of", "gex", "move", "fear", "agree", "day", "error"},
    "strip.gex.*": {"status", "reason", "word", "raw", "net", "flip_pct", "flip_sigma", "call_wall_pct", "put_wall_pct",
                    "as_of", "contracts", "oi_date", "method", "flip_reason", "label", "source", "delay", "dix"},
    "strip.move": {"status", "reason", "em_pct", "em_inside_pct", "band68_pct", "funded_pct", "minute", "as_of",
                   "method"},
    "strip.fear": {"status", "reason", "stress", "as_of", "vix_vs_forecast", "fear_day", "fear_day_date", "as_of_session",
                   "fear_why", "picker_state", "method"},
    "strip.agree": {"status", "reason", "word", "spy_pct", "qqq_pct", "as_of"},
    "strip.day": {"status", "reason", "word", "gap_pct", "range_pct", "as_of", "method"},
    "lector": {"as_of", "credit", "n", "rows"},
    "lector.rows[]": {"rank", "symbol", "score", "band", "parts"},
    "ranked[]": {"rank", "symbol", "take", "form", "evidence", "parts", "r", "delta", "listed"},
    "ranked[].parts[]": {"key", "label", "value"},
    "factors[]": {"n", "id", "group", "label", "none", "mark"},
    "fear": {"date", "both", "text"},
    "session": {"state", "label"},
    "desk": {"name"},
    "market": {"as_of", "live_at", "sentence", "chips", "sectors", "calendar", "badge"},
    "market.chips[]": {"id", "label", "value", "tone", "detail", "bar", "dots", "chg"},
    "market.badge": {"word", "tone", "line", "checks"},
    "market.badge.checks[]": {"key", "label", "ok"},
    "market.sectors[]": {"name", "rs", "pts"},
    "market.calendar[]": {"what", "at"},
    "setups[]": _READ[""] | {"id", "listed_at", "new", "status", "now_pct", "flags", "close", "held", "engine",
                             "earnings", "lod", "lens", "context", "record_line", "incubation", "options"},
    "setups[].record_line": RECORD_LINE,
    "setups[].options": {"status", "reason", "as_of", "method", "iv30", "iv_rank", "iv_sessions", "iv_rv", "pc_volume",
                         "pc_oi", "pc_oi_change", "spread_pct", "em_pct", "t1_beyond_2em", "express", "expiry",
                         "express_reason"},
    "setups[].options.express[]": {"kind", "legs", "debit", "max_loss", "max_gain", "breakeven", "touch_t1"}
    | vendor_ext.EXPRESS_KEYS,
    "setups[].options.express[].touch_t1": {"rate", "n", "days"},   # strip.touch_rate: the measured touch share
    **{"setups[].options.express[]." + k: v for k, v in vendor_ext.EXPRESS_ALLOWED.items()},   # EV and P&L grid
    "setups[].lens": lensmod.PUBLIC,
    **{"setups[].context" + ("." + k if k else ""): v for k, v in contextmod.ALLOWED.items()},   # context.py
    **{"picker" + ("." + k if k else ""): v for k, v in feardaymod.ALLOWED.items()},   # picker/fearday.py
    **{f"picker.{lane}[].context" + ("." + k if k else ""): v for lane in ("buy", "watch", "small")
       for k, v in pickcard.ALLOWED.items()},                                 # pickcard.py: the Buy List's decision card
    **{f"picker.{lane}[].lens": lenspick.KEYS for lane in ("buy", "watch", "small")},   # picker/lens.py
    **{"heur" + ("." + k if k else ""): v for k, v in heurmod.ALLOWED.items()},       # picker/heur.py
    **{"vendor" + ("." + k if k else ""): v for k, v in vendor_ext.ALLOWED.items()},  # vendor_ext.py
    "setups[].sheet_side": _READ["sheet_side"],
    "setups[].cautions[]": _READ["cautions[]"],
    "setups[].engine": enginemod.BLOCK,
    "setups[].lod": lodmod.KEYS,                   # ChartsLector's low-of-day entry, in the session only (lod.py)
    "setups[].conviction": _READ["conviction"],
    "setups[].gut": _READ["gut"],
    "setups[].plan": _READ["plan"],
    "setups[].standouts[]": _READ["standouts[]"],
    "setups[].material[]": _READ["material[]"],
    "setups[].sheet": _READ["sheet"],
    "setups[].against[]": _READ["against[]"],
    "setups[].fear": _READ["fear"],
    "setups[].news[]": _READ["news[]"],
    "setups[].marks[]": _READ["marks[]"],
    "setups[].lines[]": _READ["lines[]"],
    "setups[].avgs": _READ["avgs"],
    "watching[]": {"symbol", "action", "conviction", "gut", "line", "by", "close", "trigger", "zone_hi", "t1", "out",
                   "spike", "zone_lo", "mode", "marks", "lines", "avgs", "held", "engine", "lens", "now_pct", "record_line"},
    "watching[].record_line": RECORD_LINE,
    "watching[].engine": enginemod.BLOCK,
    "watching[].lens": lensmod.PUBLIC,
    "watching[].marks[]": _READ["marks[]"],
    "watching[].lines[]": _READ["lines[]"],
    "watching[].avgs": _READ["avgs"],
    "lookup": {"as_of", "count"},
    "departures[]": {"symbol", "side", "reason", "at"},
    "scorecard": {"since", "calls", "filled", "closed", "hits", "hit_rate", "mean_r", "open", "waiting",
                  "by_conviction", "by_take", "note"},
    "scorecard.by_conviction.*": {"calls", "filled", "closed", "hits", "hit_rate", "mean_r"},
    "scorecard.by_take.*": {"calls", "filled", "closed", "hits", "hit_rate", "mean_r"},
    "calls[]": set(callbook.PUBLIC_KEYS),
    "record": {"header", "summary", "horizons", "months", "excluded", "excluded_why", "type_lines", "by_type", "random", "incubation",
               "corrections", "rows", "rows_total", "even_band", "small_n", "since"} | recordmod.EXT_KEYS,
    **recordmod.EXT_ALLOWED,
    "record.summary": SUMMARY,
    "record.months[]": SUMMARY | {"month"},
    "record.horizons": {f"{k}d" for k in recordmod.HORIZONS},
    **{f"record.horizons.{k}d": {"n", "mean", "up"} for k in recordmod.HORIZONS},
    "record.excluded": set(recordmod.EXCLUDED),
    "record.by_type": {"form", "regime"},
    "record.by_type.form.*": SUMMARY,
    "record.by_type.regime.*": SUMMARY,
    "record.random": {"n", "names", "avg_r", "hit_rate", "seed", "draws", "edge_r"},
    "record.excluded_why[]": {"code", "n", "why"},
    "record.type_lines[]": RECORD_LINE,
    "record.incubation.*": {"state", "sessions", "closed", "need_sessions", "need_closed", "hash", "frozen",
                            "rule_changed"},
    "record.rows[]": {"id", "symbol", "form", "listed", "status", "code", "targets", "pct", "r", "verdict",
                      "give_back", "closed", "regime", "h1", "h5", "h21", "why", "corrections", "retired"},
    "calls[].fear": {"state", "label", "short", "date"},
    "brief": {"as_of", "regime", "allowed", "rows", "not_taking", "frozen", "hash"},   # desk/ai/worksheet.py
    "brief.rows[]": {"symbol", "verdict", "size", "close", "zone_lo", "zone_hi", "trigger", "out", "t1", "t2", "by",
                     "invalidation", "reason"},
}
LEAVES = {"why", "flags", "notes", "dots", "considered", "red", "cats"} | funnelmod.LEAVES
ALLOWED[""] = ALLOWED[""] | {"funnel"}          # the Funnel (desk/terminal/funnel.py)
ALLOWED.update(funnelmod.ALLOWED)


RETIRED_WORDS = "The v2 board is retired; its call stays in the record"


def current_read(rd):
    """a stored read (reads.json, a listing's read in board.json) in the current public contract: a key the contract
    no longer names, from a read made before it changed (the missing list, 2026-10-19), is dropped, never published
    and never a refused edition"""
    return {k: v for k, v in rd.items() if k in _READ[""]}


def validate(ed, path=""):
    """raise ValueError on any key outside ALLOWED: nothing reaches the public site that the contract does not name"""
    if not isinstance(ed, dict):
        return ed
    if path not in ALLOWED and path + ".*" in ALLOWED:         # a dict of named objects (scorecard.by_grade)
        for v in ed.values():
            if not isinstance(v, dict):
                raise ValueError(f"{path} must hold objects")
            validate(v, path + ".*")
        return ed
    allowed = ALLOWED.get(path)
    if allowed is None:
        raise ValueError(f"unexpected object at {path or 'top'}")
    for k, v in ed.items():
        child = f"{path}.{k}" if path else k
        if k not in allowed:
            raise ValueError(f"key not in the public contract: {child}")
        if isinstance(v, dict):
            validate(v, child)
        elif isinstance(v, list) and k in LEAVES:
            if any(isinstance(x, (dict, list)) for x in v):
                raise ValueError(f"{child} must hold plain values")
        elif isinstance(v, list):
            for x in v:
                if not isinstance(x, dict) and (child + "[]") in ALLOWED:
                    raise ValueError(f"{child} must hold objects")            # a bare number among objects (F19)
                validate(x, child + "[]")
    return ed


def slot(now):
    """the edition's slot: now floored to the 30-minute ET clock"""
    t = datetime.fromtimestamp(float(now), tz=ET)
    return t.replace(minute=(t.minute // CADENCE_MIN) * CADENCE_MIN, second=0, microsecond=0)


def session_info(now):
    d = cal._as_date(now)
    hm = lambda ts: datetime.fromtimestamp(ts, tz=ET).strftime("%H:%M")
    if cal.is_trading_day(d):
        o, c = cal.session_open(d), cal.session_close(d)
        if o <= now < c:
            return {"state": "open", "label": f"Market open · closes {hm(c)} ET"}
        if now < o:
            return {"state": "pre", "label": f"Pre-market · opens {hm(o)} ET"}
    nxt = cal.next_trading_day(d)
    day = "tomorrow" if (nxt - d).days == 1 else datetime.combine(nxt, datetime.min.time()).strftime("%a")
    return {"state": "closed", "label": f"Market closed · opens {day} {hm(cal.session_open(nxt))} ET"}


def _holds(books, sym):
    """whether any sleeve's book holds a position in sym (never published beyond the yes or no)"""
    for b in (books or {}).values():
        for inst in ((b or {}).get("positions") or {}):
            if inst.split(":", 1)[-1] == sym:
                return True
    return False


def _avgs_today(bars):
    """the 20, 50 and 200-day averages at the latest bar the cache holds (geometry.avgs on the read's own cleaning),
    the dollars the card's chart draws today; None without 20 bars"""
    bars = [b for b in bars or () if b.get("c") is not None]
    return geometry.avgs(integrity.clean(bars)[0]) if len(bars) >= 20 else None


def _drawing(shown, daily, sym):
    """a listed read's marks and lines (compose.drawing), from the cache's bars through the read's own session;
    {} when they cannot be drawn. Once a listing: its state keeps "drawn"; a failure costs the drawing, never the card"""
    from ..lab import own_index
    from .read import compose
    cut = lambda bs: [b for b in bs or () if b.get("c") is not None and                       # noqa: E731
                      cal._as_date(float(b["t"])).isoformat() <= shown["as_of"]]
    fund = own_index(sym)
    try:
        return compose.drawing(shown, cut(daily.get(sym)), fund, cut(daily.get(fund)))
    except Exception:                                    # noqa: BLE001  (the card shows without its drawing)
        return {}


def _earnings_in_hold(earnings, sym, read, call):
    """the name's next earnings date (ISO) when it falls inside the call's hold, from the read's session to its time
    stop counted from the buy window's end (the read's own rule: compose's "inside the hold"), else None"""
    d = ((earnings or {}).get(sym) or {}).get("date")
    win, stop = (read.get("plan") or {}).get("window"), (call or {}).get("time_stop")
    if not d or not win or not stop or d <= read["as_of"]:
        return None
    end = cal._as_date(win)
    for _ in range(int(stop)):
        end = cal.next_trading_day(end)
    return d if d <= end.isoformat() else None


def _flags(earnings, sym, today, until):
    """the card's flags: earnings inside the plan's horizon"""
    e = (earnings or {}).get(sym) or {}
    d = e.get("date")
    if not d or d < today.isoformat() or (until and d > until):
        return []
    k = cal.trading_days_between(today, d)
    return ["Earnings today" if k == 0 else f"Earnings in {k} session{'s' if k != 1 else ''}"]


def _now_pct(rec, daily, hourly):
    """the latest close the caches hold against the read's close, in % (None without one). The read's own session
    is taken from the same split-adjusted cache when it holds it, so a split since the read compares like with like"""
    last = distill._latest(daily, hourly)
    base = next((float(b["c"]) for b in daily or () if rec.get("as_of") and
                 cal._as_date(float(b["t"])).isoformat() == rec["as_of"]), None)   # never an unscaled close (F7)
    return round((last / base - 1) * 100, 2) if last and base else None


def _last_pct(as_of, daily):
    """the latest daily close the cache holds against the read's own session's close in that cache, in % (None
    without both): a completed session, split-safe, as _now_pct"""
    base = next((float(b["c"]) for b in daily or () if cal._as_date(float(b["t"])).isoformat() == as_of), None)
    last = float(daily[-1]["c"]) if daily else None
    return (last / base - 1) * 100 if last and base else None


def nominees(recs, rows, books):
    """{symbol: {"engines", "holds", "first_at"}}: every US stock or ETF an eligible desk strategy signalled to buy"""
    cands, n = distill.candidates(recs)
    out = {}
    for (sym, side), c in cands.items():
        if side != "long":
            continue
        el = [sid for sid in c.sleeves if distill.eligible(sid, rows.get(sid))]
        if not el:
            continue
        out[sym] = {"engines": sorted({distill.engine_of(rows.get(sid)) for sid in el}), "holds": _holds(books, sym),
                    "first_at": min(c.sleeves[sid]["at"] for sid in el)}
    return out, n


def _bars(hub, syms, n, interval="1d"):
    out = {}
    if hub is None:
        return out
    syms = sorted(set(syms))
    for i in range(0, len(syms), 200):
        out.update(hub.bars("equity_split", interval, syms[i:i + 200], n, cache_only=True) or {})
    return out


def _strip(root, opt, daily, live_daily, banner, now, today, setups):
    """the market strip, and each listed long's options block (desk/terminal/strip.py); a failure costs only the
    strip, never the edition"""
    from . import strip as stripmod
    from .read import optnews as optfacts_
    try:
        doc = stripmod.build(root, opt, daily, live_daily, market.vix_doc(root, today), banner, now)
    except Exception as e:                               # noqa: BLE001
        doc = {"as_of": today.isoformat(), "error": f"{type(e).__name__}"}
    names = (opt or {}).get("names") or {}
    try:
        ivh = (read_json(os.path.join(root, optnews.IV_PATH), {}) or {}).get("names") or {}
    except (OSError, ValueError):
        ivh = {}
    prev = stripmod.prev_pcoi(root, today.isoformat())
    for s_ in setups:
        if s_.get("side", "long") != "long" or s_.get("symbol") not in names:
            continue
        closes = [float(b["c"]) for b in daily.get(s_["symbol"]) or () if b.get("c")]
        try:
            blk = stripmod.options_block(s_["symbol"], s_.get("plan"), s_.get("close"), names[s_["symbol"]],
                                         ivh.get(s_["symbol"]), prev.get(s_["symbol"]),
                                         optfacts_.rv20(closes), (opt or {}).get("session"),
                                         bars=daily.get(s_["symbol"]))
        except Exception as e:                           # noqa: BLE001
            blk = stripmod.no(f"{type(e).__name__}")
        if blk:
            s_["options"] = blk
    return doc


def _dash_market(root):
    """the last edition's market.json (dash.py: risk appetite and rotation) for the lenses, or None: their context
    never stops an edition"""
    try:
        return read_json(os.path.join(publish.dash_dir(root), "market.json"), None)
    except (OSError, ValueError):
        return None


def _fearday(root, hub, today, daily, board_state, earnings=None, fbudget=None):
    """the Fear-Day Buy List (desk/picker/fearday.py) over the roster's cached daily bars, once per session (kept in
    board_state["picker"] for the session it read); None when it cannot be built: it never stops the edition"""
    spy = daily.get("SPY") or []
    if not spy:
        return None
    last = cal._as_date(float(spy[-1]["t"])).isoformat()
    kept = board_state.get("picker") or {}
    kb = kept.get("block")
    if kept.get("as_of") == last and kb and all("context" in c for ln in ("buy", "watch", "small") for c in kb.get(ln, ())):
        return kb
    names = [s_ for s_ in market.roster_names() if s_ != "SPY"]
    uni = {k: v for k, v in _bars(hub, names, PICKER_BARS).items() if v}
    block = feardaymod.pick(uni, spy, as_of=last, vix=market.vix_doc(root, today), splits=None)
    return pickcard.enrich(block, uni, spy, today, earnings=earnings,
                           filings=lambda sym: contextmod.fetch_filings(root, sym, today, budget=fbudget))


def _heur(root, hub, today, daily, board_state, banner):
    """the Heuristics panel (desk/picker/heur.py) over the roster's cached daily bars, once per session; its per-name
    file goes beside the dashboards. None when it cannot be built: it never stops the edition"""
    spy = daily.get("SPY") or []
    if not spy:
        return None
    last = cal._as_date(float(spy[-1]["t"])).isoformat()
    kept = board_state.get("heur") or {}
    if kept.get("as_of") == last and kept.get("block") and os.path.isfile(os.path.join(publish.dash_dir(root), "heur-names.json")):
        return kept["block"]
    names = [s_ for s_ in market.roster_names() if s_ != "SPY"]
    uni = {k: v for k, v in _bars(hub, names, PICKER_BARS).items() if v}
    try:
        earn = {s_: [r[0] for r in (e.get("reports") or [])] for s_, e in
                readsmod.with_reports(root, {}, list(uni), last).items()}
    except Exception:                                        # noqa: BLE001  (no archive: judged without earnings)
        earn = None
    block, per = heurmod.build(uni, spy, as_of=last, vix=market.vix_doc(root, today), splits=heurmod.load_splits(root),
                               members=heurmod.load_members(root), earnings=earn, both_red=(banner or {}).get("both"))
    heurmod.save_names(publish.dash_dir(root), block["as_of"], per)
    return block


def _vendor(root, hub, daily, today, strip, reads_doc):
    """the edition's `vendor` block (desk/terminal/vendor_ext.py): the empirical move, clock decay, Zweig thrust, the
    straddle verdict and the intraday regime, each with its own status"""
    try:
        ivh = ((read_json(os.path.join(root, optnews.IV_PATH), {}) or {}).get("names") or {}).get("SPY")
    except (OSError, ValueError):
        ivh = None
    spy = (daily or {}).get("SPY")
    vix = market.vix_doc(root, today)
    dc = {cal._as_date(float(b["t"])).isoformat(): float(b["c"]) for b in spy or () if b.get("c") is not None}
    table, why = vendor_ext.tod_table(root, lambda: ((hub.bars("equity_split", "5m", ["SPY"], 20000, cache_only=True) or {})
                                                     .get("SPY") or []) if hub is not None else [], dc, vix,
                                      max(dc) if dc else today.isoformat())
    return vendor_ext.build(spy, vix, strip, reads_doc.get("zbt"), ivh, table, today)


def build(root, hub, now, status=None, picker=None):
    """-> (edition, board_state, calls): everything for one edition, read-only over the desk's own state. picker
    "fearday" (the default) publishes the Fear-Day Buy List and freezes the old v2 board (no new listings, its calls
    marked retired and kept in the record); "v2" runs the old board"""
    from ..lab import own_index
    picker = picker or DEFAULT_PICKER
    if picker not in PICKERS:
        raise ValueError(f"unknown picker: {picker}")
    status = status or {}
    fbudget = contextmod.FilingsBudget()              # fresh SEC lookups for this build: 20 and 90 s in all, cache free
    st = os.path.join(root, "state")
    rows = registry.manifest_rows(root)
    books = read_json(os.path.join(st, "books.json"), {}) or {}
    earnings = read_json(os.path.join(root, "cache", "earnings.json"), {}) or {}
    board_state = read_json(os.path.join(st, "terminal", "board.json"), {}) or {}
    prev = {k.split(":")[0]: dict(v, read=current_read(v["read"])) for k, v in (board_state.get("listed") or {}).items()
            if v.get("read")}                                                                  # v2 only
    calls = callbook.load(root)
    reads_doc = read_json(os.path.join(st, "terminal", "reads.json"), {}) or {}
    pool = {k: current_read(v) for k, v in (reads_doc.get("reads") or {}).items()}
    records = dict(reads_doc.get("records") or {})

    s = slot(now)
    today, iso_slot = cal._as_date(now), s.isoformat(timespec="seconds")
    mdiag = {}                                           # how much of the roster the market read had (state only)
    status["market_read"] = mdiag
    mk = market.read(root, hub, now, diag=mdiag)
    recs = distill.ledger_signals(os.path.join(st, "ledger.jsonl"), distill.window_start(now))
    nom, n_signals = nominees(recs, rows, books)
    live_calls = [c for c in calls if c["status"] in ("open", "waiting")]
    grading = {c["symbol"] for c in calls if c.get("kind") == "read" and c.get("as_of") and   # record.py's grades
               cal.next_trading_day(c["as_of"], max(recordmod.HORIZONS) + 1) >= today}
    syms = set(nom) | {c["symbol"] for c in live_calls} | set(prev) | set(fearmod.FUNDS) | {"IWM"} | grading
    syms |= {own_index(x) for x in syms}
    syms |= readsmod.sector_funds_of(syms)               # the inputs the roster read gives each name (reads.py)
    daily = _bars(hub, syms, BARS)
    live_daily, _ = market.with_today(hub, now, daily)   # the cards' 'now' only: calls keep completed sessions
    hourly = _bars(hub, syms, 3, "1h")
    fresh = dict.fromkeys(nom) | dict.fromkeys(s_ for s_ in prev if s_ not in pool)   # listed names stay read
    earnings = readsmod.with_reports(root, earnings, fresh, today.isoformat())
    opt = optnews.load(root)                             # the session's options and news (desk/terminal/optnews.py)
    scr = enginemod.latest(root, today.isoformat())     # the analysis engine's newest screen: context on the cards
    held = {}                                            # cards the price check holds back: why, never published
    for sym in fresh:
        d = nom.get(sym)
        try:
            r = readsmod.read_one(sym, daily, earnings, mk, today,
                                  desk={"engines": d["engines"], "holds": d["holds"]} if d else None,
                                  rates=reads_doc.get("rates"), optnews=opt, held=held,
                                  screen=scr)                                        # what stands out on the roster
        except Exception:                                  # noqa: BLE001  (one name never stops the edition)
            r = None
        if r:
            pool[sym], records[sym] = r
    for sym in list(pool):                               # a read an older build made: its prices checked again
        pool[sym], why = prices.check(pool[sym])
        if why:
            held[sym] = why
            del pool[sym]

    callbook.fear_days(calls, daily)                     # before resolve: a call closing now keeps today's status
    callbook.resolve(calls, daily)
    callbook.resolve_reads(calls, daily, today=today)
    live = callbook.live(calls)
    latest = max([r.get("as_of") or "" for r in pool.values()] or [""])
    current = {k: v for k, v in pool.items() if v.get("as_of") == latest or k in prev}   # no stale read lists
    spy = daily.get("SPY") or []
    last_session = cal._as_date(float(spy[-1]["t"])).isoformat() if spy else None
    # new listings only from a complete read of the latest session the prices hold (the audit's F3 and F9)
    session = last_session if (last_session and reads_doc.get("as_of") == last_session and
                               reads_doc.get("complete")) else None
    ran = {sym for sym, old in prev.items()                # a waiting buy that ran away from its buy range leaves
           if old["read"]["form"] in ("now", "pullback") and (callbook.find(calls, old.get("call")) or {}).get(
               "status") == "waiting" and boardmod.ran_away(old["read"]["plan"], _last_pct(old["read"]["as_of"],
                                                                                         daily.get(sym)))}
    spikes = {sym for sym in current if boardmod.spiked(records.get(sym))}   # up 25% in ten sessions: no new buy
    mom = {s_: enginemod.mom_of(scr, s_) for s_ in current} if scr else None  # the board's tie-break (2-19b)
    listed, ranked, reasons = boardmod.select(current, prev, live, callbook.called(calls), session, ran, spikes,
                                              mom=mom)
    if picker == "fearday":                              # the v2 board is frozen: nothing new listed, its cards leave
        listed = []
        reasons = {s_: RETIRED_WORDS for s_ in prev}
        callbook.retire(calls, today.isoformat())
    lx = lensmod.Board(records, lambda s_: ((scr or {}).get("rows") or {}).get(enginemod._key(s_)), mk,
                       _dash_market(root), daily, reads_doc.get("mco"))   # the eight lenses and Conviction 8: context
    more = {p_["symbol"] for p_ in listed} - set(daily)
    if more:                                             # a roster pick: its bars for the fear-day rule and "now"
        more |= {own_index(x) for x in more}
        daily.update(_bars(hub, more, BARS))
        hourly.update(_bars(hub, more, 3, "1h"))
    hours = _bars(hub, {p_["symbol"] for p_ in listed}, lodmod.HOURS, "1h")   # the cards' session so far (lod.py)

    new_state, setups = {}, []
    ctx_base = contextmod.baseline([r.get("kinds") for r in records.values()])   # the why panel's roster median
    for pub in listed:
        sym = pub["symbol"]
        old = prev.get(sym)
        drawn = bool(old and old.get("drawn"))
        if old and old.get("read"):
            shown, cid, listed_at = old["read"], old.get("call"), old.get("listed_at") or iso_slot
            if not drawn and "marks" not in shown and "lines" not in shown:    # listed before its read was drawn
                shown, drawn = dict(shown, **_drawing(diet.diet(shown), daily, sym)), True
        else:
            close = (records.get(sym) or {}).get("close")
            why = prices.check(dict(pub, close=close), prices.session_high(daily.get(sym), pub["as_of"], close))[1]
            if why:                                      # never listed: no call opens for a card nobody can see
                held[sym] = why
                continue
            listed_at = iso_slot
            shown = pub
            cid = callbook.open_read_call(calls, pub, records[sym], iso_slot,
                                          (nom.get(sym) or {}).get("first_at") or float(now), published=False,
                                          engine=enginemod.at_listing(scr, sym, pub))   # kept, scoring nothing
        call = callbook.find(calls, cid) or {}
        rec = records.get(sym) or {}
        sig_at = call.get("signal_at") or float(now)
        f = fearmod.status(sym, "long", sig_at, daily)
        entry = dict(shown, id=f"{sym}-{shown['as_of'].replace('-', '')}", listed_at=listed_at, new=old is None,
                     status=call.get("status") or "waiting",
                     now_pct=_now_pct({"as_of": shown["as_of"], "close": call.get("ref_close") or rec.get("close")},
                                      live_daily.get(sym), hourly.get(sym)),
                     flags=_flags(earnings, sym, today, shown["plan"].get("by")))
        entry["held"] = _holds(books, sym)              # the desk's book: a yes or no, never its size
        cv, r_ = entry.get("conviction") or {}, (entry.get("plan") or {}).get("r")
        if cv.get("level") == 3 and isinstance(r_, (int, float)) and r_ < R_HIGH:   # a card listed before the rule:
            entry["conviction"] = dict(cv, level=2, word="Solid")                    # High needs room (read/call.R_HIGH)
        e_ = _earnings_in_hold(earnings, sym, shown, call)
        if e_:
            entry["earnings"] = e_
        eng = enginemod.block(scr, sym, shown["as_of"], shown["plan"].get("sessions"), shown["plan"].get("by"))
        if eng:
            entry["engine"] = eng
        cs = [c for c in entry.get("cautions") or () if c.get("key") != cautionsmod.VETO]
        veto = cautionsmod.veto(enginemod.vetoed(scr, sym, shown["as_of"]))
        if veto:                                       # the veto beside the engine line it belongs to: context
            cs.append(veto)
        if cs:
            entry["cautions"] = cs
        else:
            entry.pop("cautions", None)
        lens = lx.block(sym, shown, rec, call, (pool.get(sym) or shown).get("liquid"))
        if lens:                                       # the eight lenses and Conviction 8 (read/lenses.py)
            entry["lens"] = lens
        a = _avgs_today(daily.get(sym))
        if a:
            entry["avgs"] = a
        z = lodmod.lod(hours.get(sym), daily.get(sym), float(now))
        if z:                                          # his low-of-day entry: levels and a word, context only
            entry["lod"] = z
        ref = call.get("ref_close") or (rec.get("close") if rec.get("as_of") == shown["as_of"] else None)
        if ref:                                        # the close the plan's percentages are measured from
            entry["close"] = round(float(ref), 4)
        if f:
            entry["fear"] = f
        else:
            entry.pop("fear", None)
        try:                                           # the card's context: why, ladder, chop, reclaim, levels,
            fl, fwhy = contextmod.fetch_filings(root, sym, today, budget=fbudget)   # catalyst (context.py); never stops the edition
            entry["context"] = contextmod.block(daily.get(sym), daily.get("SPY"), shown.get("plan") or {},
                                                entry.get("close"), entry.get("now_pct"), rec.get("kinds"), ctx_base,
                                                earnings.get(sym), fl, today, (shown.get("plan") or {}).get("by"),
                                                fwhy, form=shown.get("form"))
        except Exception:                              # noqa: BLE001
            entry.pop("context", None)
        # a listed card keeps its read; its options and news lines are the session's (context, voting nothing)
        entry = optfacts.refresh(entry, [b["c"] for b in daily.get(sym) or () if b.get("c") is not None],
                                 max(str(shown.get("as_of") or ""), last_session or ""), opt)
        entry = face_guard(diet.diet(entry))           # its words cut to the rules and its face in plain words,
                                                       # whatever code made its read (read/diet.py, read/plain.py)
        entry, why = prices.check(entry, prices.session_high(daily.get(sym), shown["as_of"], entry.get("close")))
        new_state[sym] = {"listed_at": listed_at, "call": cid, "symbol": sym, "read": shown}
        if drawn:
            new_state[sym]["drawn"] = True
        if why:                                        # held back from the page; its call keeps resolving
            held[sym] = why
            continue
        setups.append(entry)

    departures = list(board_state.get("departures") or [])
    for key, old in (board_state.get("listed") or {}).items():          # the switch from v1, once: its listings had
        if not old.get("read"):                                          # no read; their calls stay in the record
            sym_, _, side_ = key.partition(":")
            departures.insert(0, {"symbol": sym_, "side": side_ or "long", "at": iso_slot,
                                  "reason": "The board moved to the desk's chart read; its call stays in the record"})
    for sym, old in prev.items():
        if sym in new_state:
            continue
        why = reasons.get(sym) or "Made room for stronger setups"
        c = callbook.find(calls, old.get("call")) if old.get("call") else None
        if c and why == "closed":
            why = callbook.result_words(c) or "Its call closed"
        departures.insert(0, {"symbol": sym, "side": "long", "reason": why, "at": iso_slot})
    departures = departures[:DEPARTURES_KEPT]

    before = ranking.before_of(board_state.get("ranked"), latest)           # the board's ranking, drawn (P4)
    ranked_rows, now_ev = ranking.rows(ranked, records, {e["symbol"] for e in setups}, before)
    watching = [watch_guard(w) for w in boardmod.watching(current, records, set(new_state))] \
        if picker == "v2" else []
    more = {w["symbol"] for w in watching} - set(daily)
    if more:                                             # a watching row's bars: its averages today
        daily.update(_bars(hub, more, 260))
        live_daily.update(market.with_today(hub, now, {s: daily[s] for s in more if s in daily})[0])
    for w in watching:
        w["held"] = _holds(books, w["symbol"])
        rd = current.get(w["symbol"]) or {}
        np_ = _now_pct({"as_of": rd.get("as_of"), "close": w.get("close")}, live_daily.get(w["symbol"]),
                       hourly.get(w["symbol"]))      # the row's 'now', as the cards': its dot and its words read today
        if np_ is not None:
            w["now_pct"] = np_
        eng = enginemod.block(scr, w["symbol"], rd.get("as_of"), (rd.get("plan") or {}).get("sessions"), w.get("by"))
        if eng:
            w["engine"] = eng
        lens = lx.block(w["symbol"], rd, records.get(w["symbol"]), None, rd.get("liquid"))
        if lens:
            w["lens"] = lens
        a = _avgs_today(daily.get(w["symbol"]))
        if a:
            w["avgs"] = a
    pub_calls = callbook.public(calls)
    banner = fearmod.banner(daily)
    strip = _strip(root, opt, daily, live_daily, banner, now, today, setups)
    if mk:                                               # the market's state in one word, its checks on tap
        b = market.badge(mk, banner)
        mk = dict(mk, badge=b) if b else mk
    regime = ((mk or {}).get("badge") or {}).get("word")
    record = recordmod.build(root, calls, daily, today=today.isoformat(), regime=regime,
                             opened_now=[c["id"] for c in calls if c.get("published") is False])
    rrows = [r for r in record["rows"]]
    for e in setups:                                     # each card's type: its record, or when it is graded
        e["record_line"] = recordmod.record_line(e.get("form"), calls, rrows)
        inc = record["incubation"].get(recordmod.FORM_WORDS.get(e.get("form"), e.get("form")))
        if inc:
            e["incubation"] = inc["state"]
    for w in watching:
        f_ = (current.get(w["symbol"]) or {}).get("form")
        if f_:
            w["record_line"] = recordmod.record_line(f_, calls, rrows)
    funnel = {"signals": n_signals, "nominees": len(nom), "read": len(pool), "eligible": len(ranked),   # the host's
              "listed": len(setups), "held": len(held)}                                  # status only
    edition = {
        "schema": SCHEMA, "seq": int(status.get("seq") or 0) + 1, "edition": iso_slot,
        "generated_at": datetime.fromtimestamp(float(now), tz=ET).isoformat(timespec="seconds"),
        "next_at": (s + timedelta(minutes=CADENCE_MIN)).isoformat(timespec="seconds"), "cadence_min": CADENCE_MIN,
        "session": session_info(now),
        "desk": {"name": NAME},
        "market": mk or {"as_of": None, "sentence": "", "chips": [], "sectors": [], "calendar": []},
        "setups": setups, "watching": watching,
        "lookup": {"as_of": reads_doc.get("as_of"), "count": len(reads_doc.get("reads") or {})},
        "departures": departures,
        "scorecard": callbook.scorecard_reads(calls), "calls": pub_calls, "record": record,
        "calls_chain": callbook.chain(status.get("calls_chain"), pub_calls), "notes": [],
        "fear": banner, "factors": sheetmod.registry(), "ranked": ranked_rows,
        "lector": lectormod.table(root, hub, market.roster_names())}
    if strip:
        edition["strip"] = strip
    morgue_block = morgue_edition.block(root, now)         # read from state/morgue/, never the network; None before the first run
    if morgue_block:
        edition["morgue"] = morgue_block
    pick_block = None
    if picker == "fearday":
        try:
            pick_block = _fearday(root, hub, today, daily, board_state, earnings, fbudget)
        except Exception:                                # noqa: BLE001  (the list never stops the edition)
            pick_block = None
        if pick_block:
            lenspick.attach(pick_block, lx)               # the lenses and Conviction 8 on each card that has a read
            edition["picker"] = pick_block
    heur_block = None
    try:
        heur_block = _heur(root, hub, today, daily, board_state, banner)
    except Exception:                                    # noqa: BLE001  (the panel never stops the edition)
        heur_block = None
    if heur_block:
        edition["heur"] = heur_block
    try:                                                 # the vendor package's market pieces (vendor_ext.py)
        vb = _vendor(root, hub, daily, today, edition.get("strip"), reads_doc)
    except Exception:                                    # noqa: BLE001  (the panel never stops the edition)
        vb = None
    if vb:
        edition["vendor"] = vb
    try:                                                 # the Funnel reads the edition's `morgue` key; a failure costs only it
        fb = funnelmod.build(edition)
    except Exception:                                    # noqa: BLE001
        fb = None
    if fb:
        edition["funnel"] = fb
    edition, gaps = coherencemod.gate(edition, today.isoformat() if hasattr(today, "isoformat") else today)
    return validate(edition), {"slot": iso_slot, "listed": new_state, "departures": departures, "funnel": funnel, "gaps": gaps,
                               "held": held, "ranked": ranking.history(board_state.get("ranked"), latest, now_ev),
                               **({"picker": {"as_of": pick_block["as_of"], "block": pick_block}} if pick_block else {}),
                               **({"heur": {"as_of": heur_block["as_of"], "block": heur_block}} if heur_block else {})}, \
        calls


def run(engine, now=None):
    """one edition: build, record, publish -> the job's info (counts and the publish outcome; never a secret)"""
    root = engine.root
    now = float(engine.clock() if now is None else now)
    spath = os.path.join(root, "state", "terminal.json")
    status = read_json(spath, {}) or {}
    live = publish.live_seq()
    edition, board_state, calls = build(root, engine.hub, now, status,
                                        picker=(engine.cfg.get("terminal") or {}).get("picker"))
    try:                                                 # the morning sheet: frozen and logged before it is shown
        from desk.ai import worksheet as sheetbook
        edition = validate(dict(edition, brief=sheetbook.edition_block(root, edition, edition["generated_at"])))
    except (OSError, ValueError, KeyError, TypeError):
        edition.pop("brief", None)                       # a sheet that cannot be frozen is not shown
    write_json_atomic(os.path.join(root, "state", "terminal", "edition.json"), edition)
    try:                                                 # engine.json beside the edition, or none when stale
        enginemod.save(root, enginemod.published(root, now, (edition.get("market") or {}).get("as_of")))
    except (OSError, ValueError):
        enginemod.save(root, None)
    callbook.save(root, calls)
    write_json_atomic(os.path.join(root, "state", "terminal", "board.json"), board_state)
    from . import dash                                  # charts.json and market.json beside the edition (dash.py)
    dash_info = dash.write(root, engine.hub, edition, now, status.get("market_read"))
    desk = deskview.run(engine, now)                     # the Desk tab's files; a failure keeps the last good ones
    morgue_edition.write_sidecars(root, publish.morgue_dir(root), now)   # morgue-board.json, morgue-map.json (never raises)
    res = publish.publish(root, edition) if (engine.cfg.get("terminal") or {}).get("publish", True) else \
        {"status": "off"}
    if res.get("status") in ("published", "off"):        # the calls this edition opened count from now (F5)
        callbook.mark_published(calls, edition["generated_at"])
        callbook.save(root, calls)
    if res.get("status") == "published" and not status.get("first_published"):
        status["first_published"] = edition["generated_at"]
    # until the site has taken a first edition, "no access" is the owner's pending step (the repository added to the
    # host's token), not a failure to page about; after it, any refusal is a regression (an expired token, say)
    ok = res.get("status") in ("published", "off") or (res.get("status") == "no_access"
                                                       and not status.get("first_published"))
    status.update(seq=edition["seq"], edition=edition["edition"], generated_at=edition["generated_at"],
                  calls_chain=edition["calls_chain"], live_seq_before=live, publish=res.get("status"),
                  publish_error=res.get("error"), commit=res.get("commit"), funnel=board_state.get("funnel"),
                  setups=[s["symbol"] for s in edition["setups"]], dash=dash_info, desk=desk)
    write_json_atomic(spath, status)
    return {"edition": edition["edition"], "seq": edition["seq"], "funnel": board_state.get("funnel"), "ok": ok,
            "publish": res.get("status"), "error": res.get("error"), "live_seq_before": live, "desk": desk}
