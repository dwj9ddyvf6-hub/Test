"""The Desk tab's data: the desk's own books, orders and record, composed read-only beside each edition.

Built in the edition job (desk/terminal/__init__.py run) from the state the job's engine already holds (books, OMS,
desk), the small state files (heartbeat, health, scorecard, the roll call when it exists), today's ledger window, the
registry (config/manifest: sleeves.jsonl, catalog.json, blocked.json; config/terminal/evidence.json) and the bar cache,
cache-only. Nothing here fetches, writes state, or changes a sleeve, an order or the books. Three files, written to
cache/terminal/desk/ and published beside the edition (publish.DESK_FILES):

  deskview.json   (master-desk-deskview/1, at most BUDGET_GZ gzipped; fetched when the Desk tab opens)
    overview      equity, cash, invested (long - short), capital, pnl and pct since start, realized, unrealized; day
                  {date, pnl, pct}: the session the day's change belongs to (today once its session opened, else the
                  last session); spy_pct over the same span and vs_spy (points, 1 decimal); positions and distinct
                  symbols; spark (the desk's equity per curve date, at most 60); headline (10 words or fewer, its
                  numbers are these fields)
    curve         dates: the desk's first day, every session since and today; desk: total equity in % of total
                  capital; spy: SPY's close in % of its last close before the desk's first session (None where the
                  cache lacks the session); the last points are GrokBot's end pills: overview.pct and .spy_pct
    positions     n, symbols, waiting (live entry orders); top: the TOP_N largest positions; heat: the HEAT_N largest
                  symbols {value (net), gross, pnl, pct of cost, n, sleeves (at most HEAT_SLEEVES)}; sparks of top
    sleeves       n; counts by state; min_trades; families, classes, styles: one summary per group {n, up, down,
                  median ret, best, worst (all on the published ret, as the page filters read it), spark (members'
                  summed equity in %), capital, equity, in_use, pos}, the
                  most money in use first; leaders and laggards: the best and worst by ret among sleeves with at least
                  MIN_TRADES closed trades (disjoint, at most BOARD_N each); movers: the largest 1-day changes
    closed        n, wins, win %, realized; rows: the CLOSED_N newest closed trades, hold in days, why (a code)
    engine        state/label from the heartbeat's age, its errors and the health level (desk/learn/health.py
                  thresholds); last pass, its age, the pass interval, the next US open; today {signals, orders,
                  fills} from today's ledger; live_orders
    scorecards    every sleeve with a closed trade: its live record, verdict, criteria, small (below MIN_TRADES), and
                  research where config/terminal/evidence.json cites it
    labels        the display words for every code above (family, cls, style, state, verdict, why, tf)
  sleeves.json    (master-desk-sleeves/1) one row per sleeve of the books and the registry: name (from the registry
                  title), desc (12 words or fewer), family, cls, style, tf, state, verdict, small, ret, ret_1d, ret_5d,
                  dd, trades, win, capital, equity, in_use, pos, spark (at most 40 points, % since its start)
  positions.json  (master-desk-positions/1) every open position, largest first, and every symbol's spark

Definitions:
  ret          the book's return on its capital (desk/learn/attribution.py sleeve_stats, as report.json)
  ret_1d/_5d   its last daily point over the points 1 and 5 before it, on its market's days (US books: sessions)
  dd           its maximum drawdown on those days; win: winning share of closed trades
  family       the sleeve id's prefix (lz, mk, r19, apex ...), the name the owner knows it by
  cls          stocks | options | crypto | etf_macro: what it holds or traded (options > crypto > ETFs only > stocks);
               with no instruments yet, its registry type, then its configured symbols, then its title
  style        momentum/breakout | pullback/mean-reversion | event/earnings | trend | volatility/income |
               carry/funding | other: its registry type where that names a style, else the first keyword family
               (STYLE_WORDS, in order) in its title, then in its registry entry's first sentence; Tensor rows are
               trend unless they name a dip or a breakout
  tf           its config's timeframe, its exit unit, its shortest bar read, its positions' timeframe, its UTC bar
               schedule, then the registry's timeframe text
  state        firing | waiting | off | blocked: the roll call (state/rollcall.json, desk/learn/rollcall.py) when it
               is under ROLLCALL_MAX_AGE_S old (BROKEN shows as blocked); otherwise the registry: off when disabled,
               a monitor, parked or not loaded; blocked when config/manifest/blocked.json lists it; firing while it
               holds a position; else waiting
  desc         the registry entry's first sentence, or its main clause, when that is 4 to 12 words of plain prose
               opening with what the sleeve does (plain_line); otherwise composed from its style, what its config
               trades, its timeframe and its configured hold (composed_line; build's diag["composed"] lists them)
  why          a closed trade's exit: the cause its reason states, read against its published result (exit_why: a
               stop that ended in a gain is "trail", trailing stop with the gain locked; a "target" that lost is "rule")
  due/left     a position's time exit: the fire's own time_exit_at / exit_due_date / exit_at, else the engine's
               exit rule on the position, else the sleeve config's hold (exit.max_bars with its unit, hold_sessions,
               hold_weeks, counted from the fill); null when none of them says
Design: GrokBot's "Main desk" (UI_ADOPTION 1.1). Every word is composed from these fields; no disclaimer wording."""
import bisect
import gzip
import json
import math
import os
import re
import statistics
import time
from datetime import date, datetime, timedelta

from .. import calendar as cal
from .. import registry
from ..learn import attribution
from ..util import ET, read_json
from .publish import DESK_FILES as FILES  # noqa: F401  (the files this module writes)
from .publish import SECRET_SHAPES, desk_dir

SCHEMAS = {"deskview.json": "master-desk-deskview/1", "sleeves.json": "master-desk-sleeves/1",
           "positions.json": "master-desk-positions/1"}
BUDGET_GZ = 150 * 1024
MIN_TRADES = 30                 # the scorecard's own minimum sample: expectancy is judged from 30 closed trades
SPARK_DESK, SPARK_SLEEVE, SPARK_CLOSES = 60, 40, 30
TOP_N, HEAT_N, HEAT_SLEEVES, CLOSED_N, BOARD_N = 40, 100, 8, 50, 10
ROLLCALL_MAX_AGE_S = 48 * 3600
HB_WARN_TICKS, HB_CRIT_S = 6, 900   # desk/learn/health.py: heartbeat OK under 6 loop ticks, WARN under 900 s

FAMILY_NAMES = {"apex": "APEX", "ausar": "Ausar", "chatgpt": "ChatGPT", "femto": "Femto", "Author": "Author",
                "genome": "Genome", "griffith": "Griffith", "killed": "Killed studies", "lz": "Lazarus",
                "midna": "Midna", "mk": "Milkman", "mon": "Monitors", "muse": "Muse", "qm": "Qullamaggie",
                "qr": "Quant research", "r17": "R17", "r19": "R19", "ro": "Research only", "sable": "Sable",
                "span": "Span", "t": "GrokBot"}
CLS_NAMES = {"stocks": "Stocks", "options": "Options", "crypto": "Crypto", "etf_macro": "ETFs & macro"}
STYLE_NAMES = {"momentum/breakout": "Momentum & breakout", "pullback/mean-reversion": "Pullback & mean reversion",
               "event/earnings": "Events & earnings", "trend": "Trend", "volatility/income": "Volatility & income",
               "carry/funding": "Carry & funding", "other": "Other"}
STATE_NAMES = {"firing": "Firing", "waiting": "Waiting", "off": "Off", "blocked": "Blocked"}
VERDICT_NAMES = {"accumulating": "Accumulating", "below_bar": "Below bar", "review": "Review", "propose": "Proposed"}
WHY_NAMES = {"stop": "Stop hit", "trail": "Trailing stop (gain locked)", "target": "Target hit", "time": "Time exit",
             "expiry": "Expired", "rebalance": "Rebalance", "rule": "Rule exit"}
TF_NAMES = {"1m": "1-minute", "2m": "2-minute", "3m": "3-minute", "5m": "5-minute", "10m": "10-minute",
            "15m": "15-minute", "30m": "30-minute", "1h": "Hourly", "2h": "2-hour", "4h": "4-hour", "1d": "Daily",
            "1w": "Weekly", "1mo": "Monthly"}
ROLLCALL_STATE = {"FIRING": "firing", "WAITING": "waiting", "OFF": "off", "BLOCKED": "blocked", "BROKEN": "blocked"}
CRITERIA = {"expectancy": "edge", "sharpe": "sharpe", "drawdown": "drawdown", "beats_spy": "beats_spy",
            "regimes": "regimes", "paper_30d": "days30"}

# the style a registry type names outright; the Tensor types are the desk's trend-state engines
TYPE_STYLE = {"Momentum and breakout": "momentum/breakout", "Mean reversion and pullback": "pullback/mean-reversion",
              "Events, earnings and alternative data": "event/earnings", "Options income": "volatility/income",
              "Monitors and signal inputs": "other", "Pairs and relative value": "other",
              "Hedges and defensive allocation": "other"}
TENSOR_TYPES = ("Tensor and phenotype", "Tensor with alternative data", "Tensor and learned rules")
STYLE_WORDS = (       # first match wins, in this order, over the title and the registry entry
    ("carry/funding", r"funding|\bcarry\b|\bbasis\b"),
    ("volatility/income", r"premium|put[- ]?write|put spread|credit spread|condor|\bwheel\b|cash-secured|\bincome\b|"
                          r"variance|\bvix\b|volatility|straddle|strangle|theta|covered call|harvest"),
    ("event/earnings", r"\bpead\b|earnings|surprise|catalyst|\bevents?\b|\bnews\b|insider|buyback|wiki"),
    ("pullback/mean-reversion", r"pullback|reversion|revert|\bdips?\b|oversold|\brsi ?\(?2|bounce|snapback|reversal|"
                                r"beaten|capitulation|washout|support|\breset\b|red[- ]days?|double[- ]?7|\bfades?\b|"
                                r"deviation|\brest\b|down[- ]?day"),
    ("trend", r"time-series momentum|\btsmom|\bfaber|10-month|golden cross|trend[- ]follow"),
    ("momentum/breakout", r"breakout|breakdown|momentum|\bmom\d|donchian|leader|new high|52-week high|"
                          r"relative[- ]strength|blowoff|squeeze|thrust|gap[- ]up|gap continuation|opening[- ]?range|"
                          r"expansion|burst|turtle|follow[- ]through|impulse|winners?\b|\brank|\btop ?\d|strongest|"
                          r"accel"),
    ("trend", r"trend|\bsma ?\d|moving average|\bema ?\d|cyan|green|tensor"),
)
STYLE_WORD = {"momentum/breakout": "Momentum", "pullback/mean-reversion": "Pullback", "event/earnings": "Event",
              "trend": "Trend", "volatility/income": "Premium", "carry/funding": "Funding", "other": None}
CLS_WORD = {"stocks": "stocks", "options": "options", "crypto": "crypto", "etf_macro": "ETFs"}
TF_WORD = {"1m": "1-minute", "2m": "2-minute", "3m": "3-minute", "5m": "5-minute", "10m": "10-minute",
           "15m": "15-minute", "30m": "30-minute", "1h": "hourly", "2h": "2-hour", "4h": "4-hour", "1d": "daily",
           "1w": "weekly", "1mo": "monthly"}
ACRONYMS = {"APEX", "ETF", "ETFS", "SPY", "QQQ", "IWM", "VIX", "NDX", "SPX", "XSP", "OPT", "PEAD", "RSI", "VWAP",
            "SMA", "EMA", "ATR", "AI", "IU", "IV", "LEAPS", "QLD", "TQQQ", "BTC", "ETH", "SOL", "ADA", "ENJ", "LINK",
            "USD", "USDT", "SMH", "TZA", "OBV", "MACD", "CCI", "ATH", "PO", "ES", "DTE", "OTM", "ITM", "RRE", "PF"}
EXTRA_ETFS = {"BIL", "SGOV", "SHV", "USFR", "TBIL", "GOVT", "VGSH", "VGIT", "VGLT", "SCHO", "SPTL", "EDV",
              "BTAL", "GLDM", "IAU", "QQQE", "QQQM", "SPLG", "IVW", "IWD", "IWF", "IWO", "IWN", "IJR", "IJH", "VTV",
              "VUG", "XLRE", "UVIX", "SVIX", "SH", "PSQ", "DOG", "RWM", "BITU", "SBIT"}
UNSAFE = re.compile(r"\b(paper|simulated|simulation|simulate|sim|real money)\b", re.I)
EMAILISH = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
PATHISH = re.compile(r"(^|[\s(\"'])(/|~/|[A-Za-z]:\\)[\w.~-]|\.(py|json|jsonl|md|env|txt|csv|sh|ts|js)\b|https?://")
CODEISH = re.compile(r"[<>=≤≥{}\[\]|\\_^~`$#@]")
OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")


# ---- small helpers --------------------------------------------------------------------------------------------------

def _r(x, n=2):
    if x is None:
        return None
    v = round(float(x), n)
    return 0.0 if v == 0 else v                         # never a negative zero


def _px(x):
    """a price at the precision its size needs"""
    if x is None:
        return None
    x = float(x)
    return round(x, 2) if abs(x) >= 1 else round(x, 4) if abs(x) >= 0.01 else round(x, 8)


def _iso(t):
    return datetime.fromtimestamp(float(t), tz=ET).isoformat(timespec="seconds")


def _day(t):
    return cal._as_date(float(t)).isoformat()


def _mult(inst):
    return 100.0 if inst.startswith("OPT:") else 1.0


def _when(x):
    """an ISO time or date string, or an epoch, as an aware datetime (None when it is neither)"""
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)):
        return datetime.fromtimestamp(float(x), tz=ET)
    try:
        d = datetime.fromisoformat(str(x).strip().replace("Z", "+00:00").replace(" ", "T", 1))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=ET)


def family_of(sid):
    return str(sid).split("_")[0]


def family_name(code):
    return FAMILY_NAMES.get(code) or code.capitalize()


def _downsample(values, n):
    """at most n points, the first and the last kept, the rest evenly spaced"""
    if len(values) <= n:
        return list(values)
    step = (len(values) - 1) / (n - 1)
    return [values[round(i * step)] for i in range(n)]


def equity_of(book):
    """cash plus every position at its mark (attribution.sleeve_stats' equity, unrounded)"""
    marks = book.get("marks") or {}
    return float(book.get("cash", book.get("capital") or 0.0)) + sum(
        float(p.get("qty") or 0.0) * float(marks.get(i, p.get("avg") or 0.0)) * _mult(i)
        for i, p in (book.get("positions") or {}).items())


def configs_of(sleeves):
    """{sleeve_id: the config fields the desk view reads} from the engine's loaded sleeves"""
    out = {}
    for sid, s in (sleeves or {}).items():
        c = getattr(s, "CONFIG", None)
        if c is None:
            continue
        out[sid] = {"family": c.family, "params": dict(c.params or {}), "needs": dict(c.needs or {}),
                    "schedule": c.schedule, "status": c.status, "universe": list(c.universe or ())}
    return out


# ---- names, descriptions, classes, styles, timeframes -------------------------------------------------------------

def _scrub(text):
    return re.sub(r"\s{2,}", " ", UNSAFE.sub("", text)).strip(" ,;:-—")


def friendly_name(title):
    """the registry title as a display name: no file name, no sleeve number, no paper wording, words not SNAKE_CAPS"""
    t = str(title or "").strip()
    m = re.match(r"^\S+\.py\s*[—–-]\s*(.*)$", t)
    if m:
        t = m.group(1)
    t = re.sub(r"^[\w .'-]*?\bsleeve\s*#\d+\s*:\s*", "", t, flags=re.I)
    t = _scrub(t.rstrip(". "))
    letters = lambda w: re.sub(r"[^A-Za-z]", "", w)
    if "_" in t and t == t.upper():
        words = []
        for w in t.split("_"):
            a = letters(w)
            keep = a in ACRONYMS or len(a) <= 3 or re.search(r"(USD|USDT|USDC)$", a)
            words.append(w if keep else w.lower())
        t = " ".join(w for w in words if w)
        t = t[:1].upper() + t[1:]
    elif t == t.upper() and re.search(r"[A-Z]{4}", t):
        t = " ".join(w.capitalize() if (w.isalpha() and len(w) >= 4 and w not in ACRONYMS) else w
                     for w in t.split(" "))
    return re.sub(r"\s{2,}", " ", t).strip() or str(title)


def _safe_text(s):
    return not (UNSAFE.search(s) or EMAILISH.search(s) or PATHISH.search(s) or CODEISH.search(s))


ABBREV = re.compile(r"\b(et al|e\.g|i\.e|vs|approx|incl|etc)\.", re.I)
SUBORDINATE = re.compile(r"^(after|before|if|when|whenever|while|within|from|at least|at most|exactly|since|until|"
                         r"unless|using|given|once|for each|per|because|across|between|whether)\b", re.I)
CLAUSE_NEXT = re.compile(r"^(\w+ing|and|or|then|which|while|with|using|before|after|to|each|so|but|until|unless|"
                         r"when|where|if|for|as|plus|not|no|otherwise)\b", re.I)
DANGLING = {"a", "an", "the", "of", "to", "and", "or", "with", "by", "for", "in", "on", "at", "from", "into", "than",
            "as", "if", "when", "that", "which", "its", "their", "is", "are", "be", "per", "vs", "below", "above"}
# a line for the owner opens with what the sleeve does (the registry's plain-English entries do; its research
# shorthand opens with a noun, a precondition or a formula): an action verb, a cadence, or "At the open/close"
START_OK = re.compile(
    r"^(Buys?|Sells?|Shorts?|Holds?|Watch(es)?|Checks?|Ranks?|Adjusts?|Rotates?|Trades?|Tracks?|Picks?|Records?|"
    r"Fades?|Follows?|Owns?|Keeps?|Scans?|Allocates?|Hedges?|Collects?|Measures?|Times?|Rides?|Waits?|Enters?|"
    r"Exits?|Writes?|Rolls?|Opens?|Closes?|Moves?|Splits?|Goes|Go|Bets?|Leans?|Switch(es)?|Rebalances?|Harvests?|"
    r"Captures?|Chases?)\b|^(Monthly|Weekly|Daily|Hourly|Nightly)\s+(?!bars?\b)|^At the (open|close)\b")
JARGON_TOKEN = re.compile(r"[A-Za-z]\d|\d[A-Za-z]")       # EMA13, near91, 1H: a code, not a word (20-day is a word)


def _words(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def _restates(line, name):
    """the line says little the name does not: it contains the name, or most of its words are the name's"""
    if not name:
        return False
    lw, nw = _words(line), _words(name)
    if len(nw) >= 2 and " ".join(nw) in " ".join(lw):
        return True
    return bool(lw) and sum(1 for w in lw if w in set(nw)) / len(lw) >= 0.6


def plain_line(text, limit=12, name=None):
    """the registry entry's first sentence, or its main clause, when that is 4 to `limit` words of plain prose that
    opens with what the sleeve does (START_OK) and carries one code-like token at most (no code, path, address or
    paper wording; no subordinate opening, no dangling end; not the name again); else None"""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if not t or t.startswith(("{", "[")):
        return None
    m = re.match(r"^\S+\.py\s*[—–-]\s*(.*)$", t)
    if m:
        t = m.group(1)
    t = re.sub(r"\b(top|of|by|over|within|above|below|than|for|in|at|last|first|every)(\d)", r"\1 \2", t,
               flags=re.I)
    t = ABBREV.sub(lambda mm: mm.group(0)[:-1] + "\x00", t)              # an abbreviation's period ends nothing
    first = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", t)[0].strip().rstrip(".;:!? ")
    cands = [first]
    head, sep, rest = first.partition(", ")
    if sep and CLAUSE_NEXT.match(rest):                                 # a comma before a new clause ends the main one
        cands.append(head)
    for raw in cands:
        cand = raw.replace("\x00", ".")
        words = cand.split()
        if not (4 <= len(words) <= limit) or not START_OK.match(cand):
            continue
        if not _safe_text(cand) or any(len(w) > 24 for w in words) or SUBORDINATE.match(cand) or \
                sum(1 for w in words if JARGON_TOKEN.search(w)) > 1 or re.search(r"[*+]", cand):
            continue
        if words[-1].lower().strip(",.;:") in DANGLING or _restates(cand, name):
            continue
        return cand
    return None


def _hold_of(cfg, due=False):
    """(count, unit word) of the sleeve config's time exit, or None: its exit's bar count and unit, the hold its exit
    rule states, hold_sessions or hold_weeks. due: only a hold counted from the fill (a position's due date)"""
    p = (cfg or {}).get("params") or {}
    ex = p.get("exit")
    if isinstance(ex, dict):
        units = {"1d": "sessions", "1w": "weeks", "1h": "hourly bars"}
        unit = units.get(str(ex.get("hold_unit_kind")))
        from_fill = ex.get("hold_from") in (None, "fill")
        if unit and isinstance(ex.get("max_bars"), (int, float)) and ex.get("max_bars") and (from_fill or not due):
            return int(ex["max_bars"]), unit
        m = re.search(r"(?:hold =|time exit) (\d+) (weeks|sessions)\b", str(ex.get("rule") or ""))
        if m and not due:
            return int(m.group(1)), m.group(2)
    for key, unit in (("hold_sessions", "sessions"), ("hold_weeks", "weeks")):
        v = p.get(key)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            return int(v), unit
    return None


def _coin(sym):
    return re.sub(r"([-/]?USDT?|[-/]USD)$", "", str(sym).upper()) or str(sym)


def _what(cls, cfg):
    """what a sleeve trades, from its config: one to three symbols by name, a count of more, else its class"""
    c = cfg or {}
    syms = set(c.get("universe") or ())
    needs = c.get("needs") or {}
    for b in needs.get("bars") or ():
        if isinstance(b, dict):
            syms |= set(b.get("symbols") or ())
    q = needs.get("quotes")
    if isinstance(q, dict):
        syms |= set(q.get("symbols") or ())
    if cls == "crypto":
        syms |= {f.split(":", 1)[1] for f in needs.get("feeds") or () if re.search(r":[A-Z0-9]+USDT?$", str(f))}
        syms = {_coin(s) for s in syms}
    syms = sorted(str(s) for s in syms if s)
    noun = CLS_WORD.get(cls, "stocks")
    if 1 <= len(syms) <= 3:
        names = syms[0] if len(syms) == 1 else ", ".join(syms[:-1]) + " and " + syms[-1]
        return f"{names} options" if cls == "options" else names
    if len(syms) > 3:
        return f"options on {len(syms):,} names" if cls == "options" else f"{len(syms):,} {noun}"
    return noun


def composed_line(style, cls, tf, cfg, monitor=False, limit=12):
    """the shortest true line its rules give: what it trades, on which bars, held how long (the hold, then the bars,
    dropped while the line is longer than `limit` words)"""
    what = _what(cls, cfg)
    s = STYLE_WORD.get(style)
    head = f"Watches {what}" if monitor else f"{s} trades in {what}" if s else f"Trades {what}"
    bars = f" on {TF_WORD[tf]} bars" if tf in TF_WORD else ""
    hold = None if monitor else _hold_of(cfg)
    tail = ", no orders" if monitor else (f", held {hold[0]} {hold[1]}" if hold else "")
    for line in (head + bars + tail, head + bars, head):
        if len(line.split()) <= limit:
            return line
    return head


def is_etf(sym):
    from ..feedlib.node_source import ETFS
    return sym in ETFS or sym in EXTRA_ETFS


def inst_class(inst):
    kind, _, sym = inst.partition(":")
    if kind == "OPT":
        return "options"
    if kind in ("CR", "PERP", "SPOT"):
        return "crypto"
    return "etf_macro" if is_etf(sym) else "stocks"


def sleeve_class(insts, row, cfg):
    kinds = {i.split(":", 1)[0] for i in insts}
    if "OPT" in kinds:
        return "options"
    if kinds & {"CR", "PERP", "SPOT"}:
        return "crypto"
    eq = [i.split(":", 1)[1] for i in insts if i.startswith("EQ:")]
    if eq:
        return "etf_macro" if all(is_etf(s) for s in eq) else "stocks"
    t = (row or {}).get("type") or ""
    if t.startswith("Options"):
        return "options"
    if t == "Crypto":
        return "crypto"
    if t in ("ETF and cross-asset allocation", "Hedges and defensive allocation"):
        return "etf_macro"
    syms = set((cfg or {}).get("universe") or ())
    needs = (cfg or {}).get("needs") or {}
    for b in needs.get("bars") or ():
        if isinstance(b, dict):
            syms |= set(b.get("symbols") or ())
    q = needs.get("quotes")
    if isinstance(q, dict):
        syms |= set(q.get("symbols") or ())
    syms = {str(s) for s in syms}
    if syms and any("/" in s or s.endswith(("-USD", "USDT")) for s in syms):
        return "crypto"
    if syms and all(is_etf(s) for s in syms):
        return "etf_macro"
    title = str((row or {}).get("title") or "")
    if re.search(r"USDT?(\b|_)|\b(BTC|ETH|SOL|ADA|ENJ|LINK|bitcoin|ethereum|crypto|coins?)\b", title, re.I):
        return "crypto"
    if re.search(r"(^|[^A-Za-z])OPT([^A-Za-z]|$)|\boptions?\b|LEAPS", title):
        return "options"
    if re.search(r"\bETFs?\b", title):
        return "etf_macro"
    return "stocks"


def sleeve_style(row, text):
    """the registry type's style where it names one; else the first STYLE_WORDS family in the title, then in the
    entry's first sentence (its rule; later sentences are context); a Tensor row is trend unless it names a dip or a
    breakout"""
    t = (row or {}).get("type") or ""
    if t in TYPE_STYLE:
        return TYPE_STYLE[t]
    words = STYLE_WORDS
    if t in TENSOR_TYPES:
        words = [w for w in STYLE_WORDS if w[0] in ("pullback/mean-reversion", "momentum/breakout")]
    first = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", ABBREV.sub("", str(text or "").strip()))[0]
    for hay in (str((row or {}).get("title") or ""), first):
        for style, pat in words:
            if re.search(pat, hay.lower()):
                return style
    return "trend" if t in TENSOR_TYPES else "other"


_TF_UNIT = r"(minutes?|mins?|m|hours?|hrs?|h|days?|d|weeks?|wks?|w|months?|mo)\b"
_TF_WORDS = {"one": 1, "two": 2, "three": 3, "five": 5, "ten": 10, "fifteen": 15, "thirty": 30, "sixty": 60}


def _tf_code(n, u):
    if u.startswith("mo"):
        return f"{n}mo"
    u = u[0]
    if u == "m" and n % 60 == 0:
        n, u = n // 60, "h"
    if u == "h" and n == 24:
        n, u = 1, "d"
    return f"{n}{u}"


def norm_tf(x):
    """a bar timeframe code (5m, 1h, 4h, 1d, 1w ...) from a config value or registry text: a leading bar code, then
    an hourly/daily/weekly/monthly word, then an "N-minute" form anywhere; None when the text names none"""
    s = str(x or "").strip().lower()
    if not s:
        return None
    m = re.match(r"(\d+)[\s-]*" + _TF_UNIT, s)
    if m:
        return _tf_code(int(m.group(1)), m.group(2))
    m = re.search(r"(hourly|daily|weekly|monthly)\b", s)
    if m:
        return {"hourly": "1h", "daily": "1d", "weekly": "1w", "monthly": "1mo"}[m.group(1)]
    m = re.search(r"\b(one|two|three|five|ten|fifteen|thirty|sixty)[\s-]minute\b", s)
    if m:
        return _tf_code(_TF_WORDS[m.group(1)], "m")
    m = re.search(r"\b(\d+)[\s-]*(minutes?|mins?|m)\b", s)
    return _tf_code(int(m.group(1)), "m") if m else None


def sleeve_tf(cfg, book, cat_tf):
    p = (cfg or {}).get("params") or {}
    for v in (p.get("timeframe"), (p.get("exit") or {}).get("hold_unit_kind") if isinstance(p.get("exit"), dict)
              else None):
        tf = norm_tf(v)
        if tf:
            return tf
    secs = []
    for b in ((cfg or {}).get("needs") or {}).get("bars") or ():
        tf = norm_tf((b or {}).get("interval")) if isinstance(b, dict) else None
        if tf:
            secs.append((_tf_seconds(tf), tf))
    if secs:
        return min(secs)[1]
    seen = {}
    for p_ in ((book or {}).get("positions") or {}).values():
        m = p_.get("meta") or {}
        pm = m.get("position_meta") if isinstance(m.get("position_meta"), dict) else {}
        tf = norm_tf(m.get("timeframe") or pm.get("unit"))
        if tf:
            seen[tf] = seen.get(tf, 0) + 1
    if seen:
        return max(sorted(seen), key=seen.get)
    m = re.match(r"utc_bar:(\d+)", str((cfg or {}).get("schedule") or ""))
    if m:
        return norm_tf(f"{m.group(1)}m")
    return norm_tf(re.sub(r"^native\s*", "", str(cat_tf or "").strip().lower()).split("/")[0])


def _tf_seconds(tf):
    n, u = int(re.match(r"\d+", tf).group()), re.sub(r"\d+", "", tf)
    return n * {"m": 60, "h": 3600, "d": 86400, "w": 604800, "mo": 2592000}.get(u, 86400)


# ---- time exits ---------------------------------------------------------------------------------------------------

def _hourly_due(opened, n):
    """the session of the nth regular-session hourly bar after the entry (cal.hour_bars grid)"""
    d = cal._as_date(opened)
    left = int(n)
    while True:
        if cal.is_trading_day(d):
            left -= sum(1 for s, _ in cal.hour_bars(d) if s >= opened)
            if left <= 0:
                return d
        d += timedelta(days=1)


def time_exit(p, cfg):
    """the date a position's time exit falls on, or None: the fire's own exit time, the engine's rule on the
    position, then the sleeve config's hold counted from the fill"""
    meta = p.get("meta") or {}
    pm = meta.get("position_meta") if isinstance(meta.get("position_meta"), dict) else {}
    for k in ("time_exit_at", "exit_due_date", "exit_at"):
        w = _when(pm.get(k))
        if w is not None:
            return w.astimezone(ET).date()
    opened = float(p.get("opened_at") or 0)
    if not opened:
        return None
    d0 = cal._as_date(opened)
    for kind, val in meta.get("exit_rules") or ():
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if kind == "time_sessions" and v >= 1:
            return cal.next_trading_day(d0, int(math.ceil(v)))
        if kind == "time_sessions_close" and v >= 1:
            return cal.next_trading_day(d0, int(math.ceil(v)) - 1) if v > 1 else d0
        if kind == "time_hours":
            return cal._as_date(opened + v * 3600)
        if kind == "expire_at":
            return cal._as_date(v)
    hold = _hold_of(cfg, due=True)
    if hold:
        n, unit = hold
        if unit == "sessions":
            return cal.next_trading_day(d0, n)
        if unit == "weeks":
            return d0 + timedelta(weeks=n)
        if unit == "hourly bars":
            return _hourly_due(opened, n)
    return None


# ---- positions ----------------------------------------------------------------------------------------------------

def display_symbol(inst):
    kind, _, rest = inst.partition(":")
    if kind == "OPT":
        m = OCC.match(rest)
        if m:
            k = int(m.group(4)) / 1000.0
            return f"{m.group(1)} {m.group(2)} {k:g}{m.group(3)}"
        return rest
    if kind in ("PERP", "SPOT"):
        sym = rest.split(":")[-1]
        return f"{sym} perp" if kind == "PERP" else sym
    return rest


def position_row(sid, inst, p, marks, now, cfg):
    qty, avg = float(p.get("qty") or 0.0), float(p.get("avg") or 0.0)
    mark = float((marks or {}).get(inst, avg))
    m = _mult(inst)
    pnl = (mark - avg) * qty * m
    pct = ((mark / avg - 1.0) * (1 if qty > 0 else -1) * 100.0) if avg else None
    opened = float(p.get("opened_at") or 0.0) or None
    today = cal._as_date(now)
    due = time_exit(p, cfg)
    row = {"sym": display_symbol(inst), "cls": inst_class(inst), "side": "long" if qty > 0 else "short",
           "sleeve": sid, "family": family_of(sid), "qty": round(qty, 6), "entry": _px(avg), "last": _px(mark),
           "value": _r(qty * mark * m), "pnl": _r(pnl), "pct": _r(pct), "opened": _day(opened) if opened else None,
           "days": int((now - opened) // 86400) if opened else None, "due": None, "left": None, "hold": None}
    if due is not None:
        row.update(due=due.isoformat(), left=max(0, (due - today).days),
                   hold=max(1, (due - cal._as_date(opened)).days) if opened else None)
    return row


def tail_closes(cache, source, symbol, n=SPARK_CLOSES, windows=(4096, 16384)):
    """the last n daily closes of a cached series, read from the file's tail: the cache writes compact JSON lists of
    flat bars, so the tail's whole bars parse alone (a wider tail when one holds fewer than n); anything else is read
    whole (BarCache.read)"""
    p = cache.path(source, "1d", symbol)
    try:
        size = os.path.getsize(p)
    except OSError:
        return []
    got = None
    for window in windows:
        if size <= window:
            break
        try:
            with open(p, "rb") as f:
                f.seek(size - window)
                tail = f.read().decode("utf-8")
            i = tail.find('{"t":')
            if i < 0 or not tail.rstrip().endswith("]"):
                break
            bars = json.loads("[" + tail[i:])
            ts = [b["t"] for b in bars]
            if not all(a < b for a, b in zip(ts, ts[1:])):
                break
            if len(bars) >= n:
                got = bars
                break
        except (OSError, ValueError, KeyError, TypeError, UnicodeDecodeError):
            break
    if got is None:
        got = cache.read(source, "1d", symbol)
    return [_px(b["c"]) for b in got[-n:] if isinstance(b, dict) and b.get("c") is not None]


def _spark_source(hub, inst):
    kind, _, rest = inst.partition(":")
    if kind == "EQ":
        return hub.resolve("equity_split"), rest
    if kind == "CR":
        return "coinbase", rest.replace("/", "-")
    return None, None


# ---- closed trades, the engine ------------------------------------------------------------------------------------

def _stated_why(reason):
    """the cause a closed trade's reason states, in WHY_NAMES' codes (a trailing exit as "trail")"""
    r = re.sub(r"\w+=False", "", str(reason or "")).lower()
    if not r.strip():
        return "rule"
    if re.search(r"time_stop|dte_time", r):
        return "time"
    if "stop=true" in r:
        return "stop"
    if "target=true" in r or "reverted=true" in r:          # ema_vwap: back at its average is its profit exit
        return "target"
    if re.search(r"\bexpired?\b|expiration|cash settlement|assign", r):
        return "expiry"
    if re.search(r"rebalanc|rerank|\bdecided\b|->\s*[a-z]+ \d|\bweight|topkdropout|rotation", r):
        return "rebalance"                                   # "rebalance to the frozen daily target": a weight
    if re.search(r"\btarget\b|take[- ]profit", r):
        return "target"
    if re.search(r"trail|donchian_exit|channel exit", r):
        return "trail"
    if re.search(r"\bstop\b|stop_|stopped|invalidat", r):
        return "stop"
    if re.search(r"\bheld\b|\bbar \d+ close|deadline|scheduled_time_exit|time[ _]exit|session \d+ of|\bhold\b|"
                 r"expire_at|max_bars|horizon", r):
        return "time"
    return "rule"


def exit_why(reason, result=None):
    """a closed trade's exit in WHY_NAMES' codes: the cause its reason states, read against its published result
    (% or $): a stop that ended in a gain was raised above entry, a trailing stop that locked the gain ("trail"); a
    trailing stop that ended in a loss is a stop; a "target" that lost money was no profit target ("rule")"""
    why = _stated_why(reason)
    if result is None:
        return "stop" if why == "trail" else why
    if why in ("stop", "trail"):
        return "trail" if result > 0 else "stop"
    if why == "target" and result < 0:
        return "rule"
    return why


def engine_state(age_s, level, errors, tick_s=30.0):
    """(state, label) of the loop from its heartbeat age, the last pass's errors and the health level"""
    if age_s is None or age_s >= HB_CRIT_S:
        return "stalled", "Stalled"
    if level == "CRIT" or (errors or 0) > 0:
        return "attention", "Needs attention"
    if level == "WARN" or age_s >= HB_WARN_TICKS * tick_s:
        return "warn", "Running with warnings"
    return "ok", "Running normally"


def ledger_today(path, t_cut, chunk=1 << 22, max_bytes=128 << 20):
    """{starts, signals, orders, fills} of the passes that started at or after t_cut, read backwards from the file's
    end (desk/terminal/distill.py ledger_signals' method): signals = intents the sleeves emitted, orders = children
    the passes created, fills = fills booked to the sleeves. None without a ledger."""
    if not os.path.exists(path):
        return None
    kept, stop = [], False
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        look = min(size, 1 << 20)
        f.seek(size - look)
        cut = f.read(look).rfind(b"\n")
        if cut < 0:
            return {"starts": [], "signals": 0, "orders": 0, "fills": 0}
        end = pos = size - look + cut + 1
        carry = b""
        while pos > 0 and not stop and end - pos < max_bytes:
            step = min(chunk, pos)
            pos -= step
            f.seek(pos)
            lines = (f.read(step) + carry).split(b"\n")
            carry = lines.pop(0) if pos > 0 else b""
            for ln in reversed(lines):
                if b'"kind": "pass_start"' in ln:
                    try:
                        at = _when(json.loads(ln).get("at"))
                    except ValueError:
                        continue
                    if at is None:
                        continue
                    if at.timestamp() < t_cut:
                        stop = True
                        break
                    kept.append(("start", at.timestamp()))
                elif b'"kind": "signals"' in ln:
                    m = re.search(rb'"kind": "signals", "n": (\d+)', ln)
                    kept.append(("signals", int(m.group(1)) if m else 0))
                elif b'"kind": "book_fill"' in ln:
                    kept.append(("fill", 1))
                elif b'"kind": "pass_end"' in ln:
                    m = re.search(rb'"children_created": (\d+)', ln)
                    kept.append(("orders", int(m.group(1)) if m else 0))
    out = {"starts": [], "signals": 0, "orders": 0, "fills": 0}
    started = False
    for kind, v in reversed(kept):
        if kind == "start":
            started = True
            out["starts"].append(v)
        elif started:
            out[{"signals": "signals", "fill": "fills", "orders": "orders"}[kind]] += v
    return out


# ---- the contract -------------------------------------------------------------------------------------------------

POS_KEYS = {"sym", "cls", "side", "sleeve", "family", "qty", "entry", "last", "value", "pnl", "pct", "opened", "days",
            "due", "left", "hold"}
GROUP_KEYS = {"id", "name", "n", "up", "down", "median", "best", "worst", "spark", "capital", "equity", "in_use",
              "pos"}
BOARD_KEYS = {"id", "name", "family", "ret", "ret_1d", "spark"}
ROW_KEYS = {"id", "name", "desc", "family", "cls", "style", "tf", "state", "verdict", "small", "ret", "ret_1d",
            "ret_5d", "dd", "trades", "win", "capital", "equity", "in_use", "pos", "spark"}
ALLOWED = {
    "deskview.json": {
        "": {"schema", "generated_at", "as_of", "start", "labels", "overview", "curve", "positions", "sleeves",
             "closed", "engine", "scorecards"},
        "labels": {"family", "cls", "style", "state", "verdict", "why", "tf"},
        "overview": {"equity", "cash", "invested", "long", "short", "capital", "pnl", "pct", "realized",
                     "unrealized", "day", "spy_pct", "vs_spy", "positions", "symbols", "spark", "headline"},
        "overview.day": {"date", "pnl", "pct"},
        "curve": {"dates", "desk", "spy", "spy_as_of"},
        "positions": {"n", "symbols", "waiting", "top", "heat", "sparks"},
        "positions.top[]": POS_KEYS,
        "positions.heat[]": {"sym", "cls", "value", "gross", "pnl", "pct", "n", "sleeves"},
        "sleeves": {"n", "counts", "min_trades", "families", "classes", "styles", "leaders", "laggards", "movers"},
        "sleeves.counts": set(STATE_NAMES),
        "sleeves.families[]": GROUP_KEYS, "sleeves.classes[]": GROUP_KEYS, "sleeves.styles[]": GROUP_KEYS,
        "sleeves.families[].best": {"id", "name", "ret"}, "sleeves.families[].worst": {"id", "name", "ret"},
        "sleeves.classes[].best": {"id", "name", "ret"}, "sleeves.classes[].worst": {"id", "name", "ret"},
        "sleeves.styles[].best": {"id", "name", "ret"}, "sleeves.styles[].worst": {"id", "name", "ret"},
        "sleeves.leaders[]": BOARD_KEYS, "sleeves.laggards[]": BOARD_KEYS, "sleeves.movers[]": BOARD_KEYS,
        "closed": {"n", "wins", "win", "realized", "rows"},
        "closed.rows[]": {"sym", "sleeve", "family", "side", "opened", "entry", "closed", "exit", "days", "pnl", "pct",
                          "why"},
        "engine": {"state", "label", "last_pass", "age_s", "every_s", "next_open", "passes", "errors", "health",
                   "today", "live_orders"},
        "engine.today": {"date", "signals", "orders", "fills"},
        "scorecards": {"min_trades", "rows"},
        "scorecards.rows[]": {"id", "name", "family", "trades", "wins", "win", "avg_ret", "avg_hold", "realized",
                              "verdict", "small", "crit", "research"},
        "scorecards.rows[].crit": set(CRITERIA.values()),
        "scorecards.rows[].research": {"grade", "why"},
    },
    "sleeves.json": {"": {"schema", "generated_at", "as_of", "min_trades", "rows"}, "rows[]": ROW_KEYS},
    "positions.json": {"": {"schema", "generated_at", "as_of", "n", "rows", "sparks"}, "rows[]": POS_KEYS},
}
MAPS = {"labels.family", "labels.cls", "labels.style", "labels.state", "labels.verdict", "labels.why", "labels.tf",
        "positions.sparks", "sparks"}            # {code: plain value}: any key, never an object
LEAVES = {"spark", "dates", "desk", "spy", "sleeves"}


def _plain(v):
    return v is None or isinstance(v, (str, int, float, bool))


def _check(x, path, allowed):
    if path in MAPS:
        if not isinstance(x, dict):
            raise ValueError(f"{path} must be a map")
        for v in x.values():
            if not (_plain(v) or (isinstance(v, list) and all(_plain(e) for e in v))):
                raise ValueError(f"{path} must hold plain values")
        return
    if isinstance(x, dict):
        keys = allowed.get(path)
        if keys is None:
            raise ValueError(f"unexpected object at {path or 'top'}")
        for k, v in x.items():
            child = f"{path}.{k}" if path else k
            if k not in keys:
                raise ValueError(f"key not in the desk contract: {child}")
            if isinstance(v, (dict, list)):
                _check(v, child, allowed)
            elif not _plain(v):
                raise ValueError(f"{child} must be a plain value")
    elif isinstance(x, list):
        leaf = path.split(".")[-1]
        if leaf in LEAVES and (path + "[]") not in allowed:
            if not all(_plain(e) for e in x):
                raise ValueError(f"{path} must hold plain values")
            return
        for e in x:
            if not isinstance(e, dict):
                raise ValueError(f"{path} must hold objects")
            _check(e, path + "[]", allowed)


def validate(name, doc):
    """raise ValueError on any key the file's contract does not name, or on secret-shaped or disclaimer wording"""
    if name not in ALLOWED:
        raise ValueError(f"not a desk file: {name}")
    _check(doc, "", ALLOWED[name])
    text = "\n".join(_strings(doc))                    # one pass a pattern: none of them spans a line break
    if UNSAFE.search(text) or any(p.search(text) for p in SECRET_SHAPES):
        raise ValueError(f"{name}: a string fails the wording or secret check")
    return doc


def _strings(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield str(k)
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


# ---- the build ----------------------------------------------------------------------------------------------------

def _catalog(root):
    try:
        return {x.get("idx"): x for x in json.load(open(os.path.join(root, "config", "manifest", "catalog.json")))}
    except (OSError, ValueError):
        return {}


def _evidence(root):
    doc = read_json(os.path.join(root, "config", "terminal", "evidence.json"), {}) or {}
    return [(r.get("match"), r) for r in doc.get("grades") or () if r.get("match")]


def _research(sid, ev):
    """the desk's own research citation for a sleeve (config/terminal/evidence.json): its grade and why, the why
    dropped when it names an address or a path"""
    for match, r in ev:
        if match == sid or (match.endswith("*") and sid.startswith(match[:-1])):
            why = _scrub(str(r.get("why") or ""))
            return {"grade": r.get("grade"), "why": why if why and not (EMAILISH.search(why) or PATHISH.search(why))
                    else None}
    return None


def _rollcall(st, now):
    doc = read_json(os.path.join(st, "rollcall.json"), None)
    if not isinstance(doc, dict):
        return {}
    at = _when(doc.get("at"))
    if at is None or now - at.timestamp() > ROLLCALL_MAX_AGE_S:
        return {}
    return {r.get("sleeve_id"): ROLLCALL_STATE.get(str(r.get("class") or "").upper())
            for r in doc.get("rows") or () if isinstance(r, dict) and r.get("sleeve_id")}


def _at(points, d, default):
    """the value of the last (date, value) point on or before d, else default"""
    i = bisect.bisect_right(points, (d, float("inf")))
    return points[i - 1][1] if i else default


def _pct(a, b):
    return (a / b - 1.0) * 100.0 if a is not None and b else None


def build(root, now, hub=None, books=None, oms=None, desk=None, configs=None, state_dir=None, tick_s=30.0,
          diag=None):
    """-> {file name: document} for FILES, read-only over the state at root (or state_dir), each validated"""
    t0 = time.perf_counter()
    diag = diag if diag is not None else {}
    st = state_dir or os.path.join(root, "state")
    books = books if books is not None else (read_json(os.path.join(st, "books.json"), {}) or {})
    oms = oms if oms is not None else (read_json(os.path.join(st, "oms.json"), {}) or {})
    desk = desk if desk is not None else (read_json(os.path.join(st, "desk.json"), {}) or {})
    hb = read_json(os.path.join(st, "heartbeat.json"), {}) or {}
    health = read_json(os.path.join(st, "health.json"), {}) or {}
    cards = read_json(os.path.join(st, "scorecard.json"), {}) or {}
    rows_m = registry.manifest_rows(root)
    catalog = _catalog(root)
    blocked = read_json(os.path.join(root, "config", "manifest", "blocked.json"), {}) or {}
    ev = _evidence(root)
    roll = _rollcall(st, now)
    today = cal._as_date(now)
    gen = _iso(now)
    as_of = _iso(float(desk.get("last_pass") or hb.get("at") or now))

    # -- per sleeve: its stats and its daily record --------------------------------------------------------------
    stats, pts, alld = {}, {}, {}
    for sid, b in books.items():
        stats[sid] = attribution.sleeve_stats(b)
        sessions = attribution.market(b) == "us"
        pts[sid] = attribution._daily_curve(b.get("curve"), sessions=sessions)
        alld[sid] = attribution._daily_curve(b.get("curve"))
    diag["ms_stats"] = round((time.perf_counter() - t0) * 1000)
    capital = sum(float(s["capital"]) for s in stats.values())
    live = {sid: equity_of(b) for sid, b in books.items()}
    equity = sum(live.values())

    def total_on(d):
        if d >= today:
            return equity
        return sum(_at(alld[sid], d.isoformat(), float(stats[sid]["capital"])) for sid in books)

    firsts = [p[0][0] for p in alld.values() if p]
    start = min(firsts) if firsts else None
    t_start = min((float(b["curve"][0][0]) for b in books.values() if b.get("curve")), default=None)
    dates = []
    if start:
        d = date.fromisoformat(start)
        while d <= today:
            if d.isoformat() == start or cal.is_trading_day(d) or d == today:
                dates.append(d)
            d += timedelta(days=1)
    totals = [total_on(d) for d in dates]

    # -- SPY over the same span ----------------------------------------------------------------------------------
    spy_rows = []
    if hub is not None:
        try:
            spy_rows = [(cal._as_date(float(b["t"])).isoformat(), float(b["c"]))
                        for b in hub.cache.read(hub.resolve("equity_split"), "1d", "SPY") if b.get("c")]
        except Exception:                                 # noqa: BLE001  (no SPY: the curve shows the desk alone)
            spy_rows = []
    base = None
    if start:                      # SPY from its last close before the desk's first session, as the desk from capital
        d0 = date.fromisoformat(start)
        first_session = d0 if (cal.is_trading_day(d0) and t_start < cal.session_close(d0)) else \
            cal.next_trading_day(d0)
        before = [c for d_, c in spy_rows if d_ < first_session.isoformat()]
        base = before[-1] if before else None

    def spy_on(d):
        if not base:
            return None
        need = d if (cal.is_trading_day(d) and d < today) else cal.prev_trading_day(d)
        i = bisect.bisect_right(spy_rows, (d.isoformat(), float("inf")))
        if not i or spy_rows[i - 1][0] < need.isoformat():
            return None
        return _pct(spy_rows[i - 1][1], base)

    spy = [spy_on(d) for d in dates]
    spy_as_of = None
    if spy_rows and base:
        i = bisect.bisect_right(spy_rows, (today.isoformat(), float("inf")))
        spy_as_of = spy_rows[i - 1][0] if i else None
    desk_pct = [_pct(t, capital) for t in totals]

    # -- the overview ---------------------------------------------------------------------------------------------
    day_d = today if (cal.is_trading_day(today) and now >= cal.session_open(today)) else cal.prev_trading_day(today)
    t_day, t_prev = total_on(day_d), total_on(cal.prev_trading_day(day_d))
    longv = shortv = 0.0
    for sid, b in books.items():
        marks = b.get("marks") or {}
        for inst, p in (b.get("positions") or {}).items():
            v = float(p.get("qty") or 0.0) * float(marks.get(inst, p.get("avg") or 0.0)) * _mult(inst)
            longv, shortv = (longv + v, shortv) if v >= 0 else (longv, shortv - v)
    cash = sum(float(b.get("cash", b.get("capital") or 0.0)) for b in books.values())
    pct_all = _pct(equity, capital)
    spy_last = spy[-1] if spy else None
    overview = {
        "equity": _r(equity), "cash": _r(cash), "invested": _r(longv - shortv), "long": _r(longv),
        "short": _r(shortv), "capital": _r(capital), "pnl": _r(equity - capital), "pct": _r(pct_all),
        "realized": _r(sum(float(b.get("realized") or 0.0) for b in books.values())),
        "unrealized": _r(sum(float(s["unrealized"]) for s in stats.values())),
        "day": {"date": day_d.isoformat(), "pnl": _r(t_day - t_prev), "pct": _r(_pct(t_day, t_prev))},
        "spy_pct": _r(spy_last), "vs_spy": _r(pct_all - spy_last, 1) if (pct_all is not None and spy_last is not None)
        else None,
        "positions": 0, "symbols": 0, "spark": [_r(t) for t in _downsample(totals, SPARK_DESK)], "headline": ""}
    curve = {"dates": [d.isoformat() for d in dates], "desk": [_r(x) for x in desk_pct], "spy": [_r(x) for x in spy],
             "spy_as_of": spy_as_of}

    # -- the sleeves ----------------------------------------------------------------------------------------------
    t1 = time.perf_counter()
    # a book whose row the registry no longer lists (the owner's 2026-10-26 removal) is a row only while it holds a
    # position; its record stays in the desk's totals
    ids = sorted(set(rows_m) | {sid for sid, b in books.items()
                                if any(float(p.get("qty") or 0.0) for p in (b.get("positions") or {}).values())})
    rows, composed = [], []
    names_seen = {}
    for sid in ids:
        m = rows_m.get(sid) or {}
        cfg = (configs or {}).get(sid)
        b = books.get(sid)
        s = stats.get(sid)
        cat = catalog.get(m.get("catalog_idx")) or {}
        entry = cat.get("entry") or ""
        insts = set((b or {}).get("positions") or {}) | {t.get("inst") for t in (b or {}).get("trades") or ()
                                                         if t.get("inst")}
        name = friendly_name(m.get("title") or sid)
        cls = sleeve_class(insts, m, cfg)
        style = sleeve_style(m, entry if not str(entry).lstrip().startswith("{") else "")
        tf = sleeve_tf(cfg, b, cat.get("timeframe"))
        monitor = m.get("kind") == "monitor"
        desc = plain_line(entry, name=name)
        if not desc:
            desc = composed_line(style, cls, tf, cfg, monitor=monitor)
            composed.append(sid)
        p = pts.get(sid) or []
        cap = float(s["capital"]) if s else None
        r1 = _pct(p[-1][1], p[-2][1]) if len(p) >= 2 else None
        r5 = _pct(p[-1][1], p[-6][1]) if len(p) >= 6 else None
        state = roll.get(sid)
        if not state:
            if m.get("status") == "disabled" or monitor or (configs is not None and cfg is None) or \
                    (cfg or {}).get("status") in ("parked", "monitor"):
                state = "off"
            elif sid in blocked:
                state = "blocked"
            elif s and s["open_positions"]:
                state = "firing"
            else:
                state = "waiting"
        verdict = str((cards.get(sid) or {}).get("verdict") or "").lower() or None
        trades = int(s["trades"]) if s else 0
        row = {"id": sid, "name": name, "desc": desc, "family": family_of(sid), "cls": cls, "style": style, "tf": tf,
               "state": state, "verdict": verdict, "small": trades < MIN_TRADES,
               "ret": _r(s["return_pct"]) if s else None, "ret_1d": _r(r1), "ret_5d": _r(r5),
               "dd": _r(s["max_drawdown_pct"]) if s else None, "trades": trades,
               "win": _r(s["win_rate"] * 100.0, 1) if s and s["win_rate"] is not None else None,
               "capital": _r(cap), "equity": _r(s["equity"]) if s else None,
               "in_use": _r(s["gross"]) if s else 0.0, "pos": int(s["open_positions"]) if s else 0,
               "spark": [_r(_pct(v, cap)) for _, v in _downsample(p, SPARK_SLEEVE)] if cap else []}
        key = name.lower()
        names_seen.setdefault(key, []).append(row)
        rows.append(row)
    for same in names_seen.values():             # one name, two sleeves: the family, then the id, tells them apart
        if len(same) > 1:
            fams = [r["family"] for r in same]
            for r in same:
                r["name"] += f" · {family_name(r['family'])}" if fams.count(r["family"]) == 1 else f" · {r['id']}"
    diag["composed"] = composed
    diag["ms_sleeves"] = round((time.perf_counter() - t1) * 1000)
    by_id = {r["id"]: r for r in rows}

    def group(key, label):
        out = []
        for gid in sorted({r[key] for r in rows}):
            mem = [r for r in rows if r[key] == gid]
            rets = [(r["ret"], r["id"]) for r in mem if r["ret"] is not None]    # as published: header = filters
            withb = [r["id"] for r in mem if r["id"] in books]
            dts = sorted({d for sid in withb for d, _ in pts[sid]})
            capg = sum(float(stats[sid]["capital"]) for sid in withb)
            gspark = [_r(_pct(sum(_at(pts[sid], d, float(stats[sid]["capital"])) for sid in withb), capg))
                      for d in dts] if capg else []
            best = sorted(rets, key=lambda x: (-x[0], x[1]))[0] if rets else None
            worst = sorted(rets, key=lambda x: (x[0], x[1]))[0] if rets else None
            pick = lambda x: {"id": x[1], "name": by_id[x[1]]["name"], "ret": _r(x[0])} if x else None
            out.append({"id": gid, "name": label(gid), "n": len(mem), "up": sum(1 for r, _ in rets if r > 0),
                        "down": sum(1 for r, _ in rets if r < 0),
                        "median": _r(statistics.median([r for r, _ in rets])) if rets else None,
                        "best": pick(best), "worst": pick(worst), "spark": _downsample(gspark, SPARK_SLEEVE),
                        "capital": _r(capg), "equity": _r(sum(live[sid] for sid in withb)),
                        "in_use": _r(sum(float(stats[sid]["gross"]) for sid in withb)),
                        "pos": sum(int(stats[sid]["open_positions"]) for sid in withb)})
        return sorted(out, key=lambda g: (-(g["in_use"] or 0), -g["n"], g["id"]))

    board = lambda r: {"id": r["id"], "name": r["name"], "family": r["family"], "ret": r["ret"],
                       "ret_1d": r["ret_1d"], "spark": r["spark"]}
    q = sorted((r for r in rows if r["trades"] >= MIN_TRADES and r["ret"] is not None),
               key=lambda r: (-r["ret"], r["id"]))
    k = min(BOARD_N, math.ceil(len(q) / 2))
    rest = sorted(q[k:], key=lambda r: (r["ret"], r["id"]))
    movers = sorted((r for r in rows if r["ret_1d"]), key=lambda r: (-abs(r["ret_1d"]), r["id"]))
    sleeves_block = {"n": len(rows), "counts": {s_: sum(1 for r in rows if r["state"] == s_) for s_ in STATE_NAMES},
                     "min_trades": MIN_TRADES, "families": group("family", family_name),
                     "classes": group("cls", lambda x: CLS_NAMES.get(x, x)),
                     "styles": group("style", lambda x: STYLE_NAMES.get(x, x)),
                     "leaders": [board(r) for r in q[:k]], "laggards": [board(r) for r in rest[:BOARD_N]],
                     "movers": [board(r) for r in movers[:BOARD_N]]}

    # -- positions ------------------------------------------------------------------------------------------------
    t2 = time.perf_counter()
    prow = []
    for sid, b in books.items():
        cfg = (configs or {}).get(sid)
        for inst, p in (b.get("positions") or {}).items():
            if not float(p.get("qty") or 0.0):
                continue
            r = position_row(sid, inst, p, b.get("marks") or {}, now, cfg)
            r["_inst"] = inst
            r["_cost"] = abs(float(p.get("qty") or 0.0) * float(p.get("avg") or 0.0) * _mult(inst))
            prow.append(r)
    prow.sort(key=lambda r: (-abs(r["value"] or 0.0), r["sleeve"], r["sym"]))
    heat = {}
    for r in prow:
        h = heat.setdefault(r["sym"], {"sym": r["sym"], "cls": r["cls"], "value": 0.0, "gross": 0.0, "pnl": 0.0,
                                       "_cost": 0.0, "n": 0, "sleeves": []})
        h["value"] += r["value"] or 0.0
        h["gross"] += abs(r["value"] or 0.0)
        h["pnl"] += r["pnl"] or 0.0
        h["_cost"] += r["_cost"]
        h["n"] += 1
        if r["sleeve"] not in h["sleeves"]:
            h["sleeves"].append(r["sleeve"])
    heat_rows = []
    for h in sorted(heat.values(), key=lambda h: (-h["gross"], h["sym"]))[:HEAT_N]:
        cost = h.pop("_cost")
        h.update(value=_r(h["value"]), gross=_r(h["gross"]), pnl=_r(h["pnl"]),
                 pct=_r(h["pnl"] / cost * 100.0) if cost else None, sleeves=sorted(h["sleeves"])[:HEAT_SLEEVES])
        heat_rows.append(h)
    sparks = {}
    if hub is not None:
        for r in prow:
            if r["sym"] in sparks:
                continue
            src, sym = _spark_source(hub, r["_inst"])
            if src:
                c = tail_closes(hub.cache, src, sym)
                if c:
                    sparks[r["sym"]] = c
    for r in prow:
        r.pop("_inst")
        r.pop("_cost")
    diag["ms_positions"] = round((time.perf_counter() - t2) * 1000)
    live_children = [c for c in ((oms or {}).get("children") or {}).values() if c.get("status") in ("pending",
                                                                                                   "working")]
    overview["positions"], overview["symbols"] = len(prow), len(heat)
    top = prow[:TOP_N]
    positions_block = {"n": len(prow), "symbols": len(heat),
                       "waiting": sum(1 for c in live_children if c.get("action") == "enter"),
                       "top": top, "heat": heat_rows,
                       "sparks": {r["sym"]: sparks[r["sym"]] for r in top if r["sym"] in sparks}}

    # -- closed trades --------------------------------------------------------------------------------------------
    trades = [(sid, t) for sid, b in books.items() for t in (b.get("trades") or ()) if t.get("closed_at")]
    trades.sort(key=lambda x: (-float(x[1]["closed_at"]), x[0], str(x[1].get("inst"))))
    crow = []
    for sid, t in trades[:CLOSED_N]:
        inst = str(t.get("inst") or "")
        o, c = float(t.get("opened_at") or 0) or None, float(t["closed_at"])
        pct, pnl = (_r(float(t["ret"]) * 100.0) if t.get("ret") is not None else None), _r(t.get("pnl"))
        crow.append({"sym": display_symbol(inst), "sleeve": sid, "family": family_of(sid), "side": t.get("side"),
                     "opened": _day(o) if o else None, "entry": _px(t.get("entry")), "closed": _day(c),
                     "exit": _px(t.get("exit")), "days": _r((c - o) / 86400.0, 1) if o else None, "pnl": pnl,
                     "pct": pct, "why": exit_why(t.get("reason"), pct if pct is not None else pnl)})
    wins = sum(1 for _, t in trades if float(t.get("pnl") or 0) > 0)
    closed = {"n": len(trades), "wins": wins, "win": _r(wins / len(trades) * 100.0, 1) if trades else None,
              "realized": overview["realized"], "rows": crow}

    # -- the engine -----------------------------------------------------------------------------------------------
    t3 = time.perf_counter()
    hb_at = float(hb.get("at") or 0) or None
    age = round(now - hb_at) if hb_at else None
    level = health.get("level") or None
    state, label = engine_state(age, level, int(hb.get("errors") or 0), tick_s)
    midnight = datetime(today.year, today.month, today.day, tzinfo=ET).timestamp()
    lg = ledger_today(os.path.join(st, "ledger.jsonl"), midnight)
    gaps = [b_ - a_ for a_, b_ in zip(lg["starts"], lg["starts"][1:])] if lg else []
    if cal.is_rth(now):
        nxt = None
    elif cal.is_trading_day(today) and now < cal.session_open(today):
        nxt = cal.session_open(today)
    else:
        nxt = cal.session_open(cal.next_trading_day(today))
    last_pass = float(desk.get("last_pass") or hb_at or 0) or None
    engine = {"state": state, "label": label, "last_pass": _iso(last_pass) if last_pass else None, "age_s": age,
              "every_s": round(statistics.median(gaps)) if gaps else None, "next_open": _iso(nxt) if nxt else None,
              "passes": hb.get("passes"), "errors": int(hb.get("errors") or 0), "health": level,
              "today": {"date": today.isoformat(), "signals": lg["signals"] if lg else None,
                        "orders": lg["orders"] if lg else None, "fills": lg["fills"] if lg else None},
              "live_orders": len(live_children)}
    diag["ms_ledger"] = round((time.perf_counter() - t3) * 1000)

    # -- scorecards -----------------------------------------------------------------------------------------------
    srows = []
    for sid, s in stats.items():
        if not s["trades"] or sid not in by_id:          # a book with no sleeve row has no scorecard
            continue
        card = cards.get(sid) or {}
        crit = {CRITERIA[k]: v for k, v in (card.get("criteria") or {}).items() if k in CRITERIA}
        srows.append({"id": sid, "name": by_id[sid]["name"], "family": family_of(sid), "trades": int(s["trades"]),
                      "wins": sum(1 for t in books[sid].get("trades") or () if float(t.get("pnl") or 0) > 0),
                      "win": _r(s["win_rate"] * 100.0, 1) if s["win_rate"] is not None else None,
                      "avg_ret": _r(s["expectancy_ret"] * 100.0) if s["expectancy_ret"] is not None else None,
                      "avg_hold": _r(s["avg_hold_days"], 1), "realized": _r(s["realized"]),
                      "verdict": by_id[sid]["verdict"], "small": int(s["trades"]) < MIN_TRADES, "crit": crit,
                      "research": _research(sid, ev)})
    srows.sort(key=lambda r: (-r["trades"], r["id"]))

    labels = {"family": {f: family_name(f) for f in sorted({r["family"] for r in rows})}, "cls": dict(CLS_NAMES),
              "style": dict(STYLE_NAMES), "state": dict(STATE_NAMES), "verdict": dict(VERDICT_NAMES),
              "why": dict(WHY_NAMES), "tf": dict(TF_NAMES)}
    overview["headline"] = headline(overview, today.isoformat())
    view = {"schema": SCHEMAS["deskview.json"], "generated_at": gen, "as_of": as_of, "start": start,
            "labels": labels, "overview": overview, "curve": curve, "positions": positions_block,
            "sleeves": sleeves_block, "closed": closed, "engine": engine,
            "scorecards": {"min_trades": MIN_TRADES, "rows": srows}}
    docs = {"deskview.json": view,
            "sleeves.json": {"schema": SCHEMAS["sleeves.json"], "generated_at": gen, "as_of": as_of,
                             "min_trades": MIN_TRADES, "rows": rows},
            "positions.json": {"schema": SCHEMAS["positions.json"], "generated_at": gen, "as_of": as_of,
                               "n": len(prow), "rows": prow, "sparks": sparks}}
    for name, doc in docs.items():
        validate(name, doc)
    diag["ms"] = round((time.perf_counter() - t0) * 1000)
    return docs


def headline(o, today_iso):
    """one line, 10 words or fewer, every number in it one of the overview's fields"""
    f = lambda x: f"{x:+.2f}".replace("-", "−")
    day = o.get("day") or {}
    parts = []
    if day.get("pct") is not None and day.get("date"):
        when = "today" if day["date"] == today_iso else datetime.fromisoformat(day["date"]).strftime("%a")
        parts.append(f"{f(day['pct'])}% {when}")
    if o.get("pct") is not None:
        parts.append(f"{f(o['pct'])}% since start")
    v = o.get("vs_spy")
    if v is not None and parts:
        parts.append("level with SPY" if v == 0 else f"{abs(v):.1f} points {'above' if v > 0 else 'below'} SPY")
    return ("Desk " + ", ".join(parts)) if parts else ""


# ---- the job ------------------------------------------------------------------------------------------------------

def out_dir(root):
    return desk_dir(root)


def _engine_books(engine):
    b = getattr(engine, "books", None)
    books = getattr(b, "books", None)
    if not isinstance(books, dict):
        return None
    return {sid: {"capital": x.capital, "cash": x.cash, "positions": x.positions, "groups": x.groups,
                  "realized": x.realized, "fees": x.fees, "trades": x.trades, "marks": x.marks, "curve": x.curve,
                  "n_fills": x.n_fills} for sid, x in books.items()}


def _write(path, data):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def run(engine, now=None):
    """build the three files from the job's engine and write them for the publisher -> the job's info (sizes, time,
    counts); a failure is reported and leaves the last good files in place"""
    root = engine.root
    now = float(engine.clock() if now is None else now)
    t0 = time.perf_counter()
    try:
        sleeves = getattr(engine, "sleeves", None)
        diag = {}
        docs = build(root, now, hub=getattr(engine, "hub", None), books=_engine_books(engine),
                     oms=getattr(engine, "oms_state", None), desk=getattr(engine, "desk", None),
                     configs=configs_of(sleeves) if isinstance(sleeves, dict) else None,
                     tick_s=float(((getattr(engine, "cfg", None) or {}).get("loop_tick_s")) or 30.0), diag=diag)
        blobs = {n: json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode() for n, d in docs.items()}
        out = out_dir(root)
        os.makedirs(out, exist_ok=True)
        for name, data in blobs.items():
            _write(os.path.join(out, name), data)
        gz = {n: len(gzip.compress(b, 6)) for n, b in blobs.items()}
        return {"ok": True, "ms": round((time.perf_counter() - t0) * 1000),
                "bytes": {n: len(b) for n, b in blobs.items()}, "gz": gz,
                "sleeves": docs["deskview.json"]["sleeves"]["n"], "positions": docs["positions.json"]["n"],
                "composed": len(diag.get("composed") or ())}
    except Exception as e:                              # noqa: BLE001  (the desk view never stops an edition)
        msg = re.sub(r"(/[^\s'\":]+)+", "<path>", str(e))[:200]
        return {"ok": False, "error": f"{type(e).__name__}: {msg}", "ms": round((time.perf_counter() - t0) * 1000)}
