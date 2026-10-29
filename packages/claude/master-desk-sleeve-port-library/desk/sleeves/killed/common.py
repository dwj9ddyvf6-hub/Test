"""Shared machinery of the killed-study sleeves: the study's trade list kept as a tranche ledger, executed by the engine.

Every killed study is a list of trades - (symbol, direction, entry moment, exit moment) - with its own entry and exit
conventions (open_{t+1}, close_t, close_{t+20}, next open ...). A sleeve writes each trade into its state as a
TRANCHE the moment the study's rule fires, then the ledger drives the orders:

  enter   "open"   the first pass of the entry session (marketable, until 11 minutes before the close)
          "close"  market-on-close, routed inside the auction window (close-30 .. close-11 minutes)
  exit    "close"  market-on-close on the exit session; an exit session already past exits at the next pass
          "open"   the first pass of the exit session
          "now"    a rule exit decided this pass (pairs |z|, touch exits): marketable now (or "close": at the auction)

A symbol's order is the difference between the ledger's net position (every entered, not yet exited tranche,
signed) and the sleeve's virtual book (the filled position plus every working child, signed). Tranches of the same
symbol net exactly as the study's trades do (P&L is linear in position): two studies' arms that hold the same stock
at once hold the sum. A residual the book still lacks (an entry child that expired unfilled) is traded at the next
pass (named divergence of every sleeve: the ledger is the record, the book follows it).

Per-tranche P&L is the study's own return: entry and exit reference prices are recorded on the tranche (the
decision quote), the engine's fills carry the real prices."""
import hashlib
import math
from datetime import datetime, timezone

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...util import ET

FAMILY = "killed_studies"
REPO = {"repo": "midna", "ref": "main", "commit": "7969b5229c46403a92290d16da23228e59e7b064"}
RESEARCH = "workspace/alpaca-swing-desk/desk/research/"
CAPITAL = 100_000.0
MOC_OPEN_MIN, MOC_CUTOFF_MIN = 30.0, 11.0     # the auction window this family routes market-on-close orders in
KEEP_CLOSED_DAYS = 45
EPS = 1e-9
LONG_ONLY_RAIL = ("the desk's long-only rail: Femto never shorted, and the study flagged trading its short side as a "
                  "hard-rail change needing explicit approval (a desk-wide constraint, not the study's rule)")
COMMON_DIVERGENCES = [
    "fills are engine children: an open entry is the first pass of the session (marketable), a close leg is a "
    "market-on-close order routed 30-11 minutes before the close; the study's open/close prints are the reference",
    "a tranche the book did not fill (expired child) is re-traded at the next pass (the ledger is the record)",
    "per-trade costs are the engine's fills and fees, not the study's flat bp charge",
]


def source(path, blob, **kw):
    return dict(REPO, path=RESEARCH + path, blob=blob, **kw)


# -- clocks ------------------------------------------------------------------------------------------------
def et_day(ts):
    return datetime.fromtimestamp(float(ts), tz=ET).date().isoformat()


def et_hm(ts):
    t = datetime.fromtimestamp(float(ts), tz=ET)
    return t.strftime("%H:%M")


_DAYS = {}


def bar_day(b):
    """a daily bar's session date (Alpaca stamps 04:00/05:00Z, Yahoo 13:30Z: +4h is the same UTC date)."""
    t = b["t"]
    d = _DAYS.get(t)
    if d is None:
        if len(_DAYS) > 500_000:
            _DAYS.clear()
        d = _DAYS[t] = datetime.fromtimestamp(float(t) + 4 * 3600, tz=timezone.utc).date().isoformat()
    return d


def bar_et(b):
    return datetime.fromtimestamp(float(b["t"]), tz=ET)


def is_session(day):
    return cal.is_trading_day(day)


def add_sessions(day, k):
    """the trading day k sessions after (k > 0) or before (k < 0) `day`; k = 0 -> day."""
    if k == 0:
        return str(day)[:10]
    return (cal.next_trading_day(day, k) if k > 0 else cal.prev_trading_day(day, -k)).isoformat()


def sessions_between(a, b):
    """trading days in (a, b]."""
    return cal.trading_days_between(a, b)


def last_closed_session(now):
    """the latest session whose close has passed (its daily bar is final 15 minutes later)."""
    d = cal._as_date(now)
    if cal.is_trading_day(d) and now >= cal.session_close(d):
        return d.isoformat()
    return cal.prev_trading_day(d).isoformat()


def closed_daily(bars, now):
    """daily bars of completed sessions only (a forming bar of today is dropped)."""
    today = et_day(now)
    d = cal._as_date(now)
    done = not cal.is_trading_day(d) or now >= cal.session_close(d)
    return [b for b in bars or () if bar_day(b) < today or (done and bar_day(b) == today)]


def in_rth(now):
    return cal.is_rth(now)


def signal_day(now):
    """at a pass of session D before its auction cutoff (pre-market included): the signal session t = the session
    before D (its daily bar is final), else None."""
    d = et_day(now)
    if not cal.is_trading_day(d):
        return None
    m = cal.minutes_to_close(now)
    if m is None or m < MOC_CUTOFF_MIN:
        return None
    return add_sessions(d, -1)


def in_moc_window(now):
    m = cal.minutes_to_close(now)
    return cal.is_rth(now) and m is not None and MOC_CUTOFF_MIN <= m <= MOC_OPEN_MIN


def before_cutoff(now):
    m = cal.minutes_to_close(now)
    return cal.is_rth(now) and m is not None and m >= MOC_CUTOFF_MIN


def price_of(view, sym):
    q = (view.quotes or {}).get(sym) or {}
    for k in ("last", "ask", "bid"):
        v = q.get(k)
        if v and float(v) > 0:
            return float(v)
    for iv in ("1m", "5m", "15m", "30m", "1h", "1d"):
        bl = ((view.bars or {}).get(iv) or {}).get(sym)
        if bl:
            return float(bl[-1]["c"])
    mark = ((view.positions or {}).get("EQ:" + sym) or {}).get("mark")
    return float(mark) if mark else None


def fresh_last(view, sym, max_age=900.0):
    """the live last price when the quote is at most max_age old (decisions made on the tape)."""
    q = (view.quotes or {}).get(sym) or {}
    v = q.get("last") or ((q.get("bid") or 0) + (q.get("ask") or 0)) / 2.0 or None
    t = q.get("t")
    if not v or float(v) <= 0:
        return None
    if t is not None and view.now - float(t) > max_age:
        return None
    return float(v)


def stable_id(*parts, n=10):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:n]


# -- the sleeve's signed virtual book ---------------------------------------------------------------------
def signed_book(view):
    """{SYM: signed qty} = filled position + every working equity child (a working order counts as done)."""
    book = {}
    for inst, p in (view.positions or {}).items():
        if str(inst).startswith("EQ:"):
            book[inst[3:]] = book.get(inst[3:], 0.0) + float(p.get("qty") or 0.0)
    for ch in (view.extra or {}).get("pending_orders", []) or []:
        inst = str(ch.get("inst", ""))
        if not inst.startswith("EQ:"):
            continue
        rem = float(ch.get("vqty") or 0.0) - float(ch.get("filled_v") or 0.0)
        if rem <= EPS:
            continue
        sym = inst[3:]
        book[sym] = book.get(sym, 0.0) + (rem if ch.get("side") == "buy" else -rem)
    return {s: q for s, q in book.items() if abs(q) > EPS}


def filled_qty(view, sym):
    p = (view.positions or {}).get("EQ:" + sym) or {}
    return float(p.get("qty") or 0.0)


# -- the tranche ledger ---------------------------------------------------------------------------------------
class TrancheBook:
    """state["tranches"]: [{id, sym, side (+1/-1), notional, units, arm, enter_day, enter_at, exit_day, exit_at,
    status planned|held|closed|void, entry_ref, exit_ref, why}]."""

    def __init__(self, st, view, sleeve_id, whole_short=True):
        self.st = st
        self.view = view
        self.sid = sleeve_id
        self.now = float(view.now)
        self.today = et_day(view.now)
        self.whole_short = whole_short
        self.tr = st.setdefault("tranches", [])
        self.changes = []          # (sym, delta_units, cls, tranche_id)
        self.records = []          # observation intents describing ledger events

    # -- creation -------------------------------------------------------------------------------------------
    def add(self, sym, side, notional, arm, enter_day, enter_at, exit_day=None, exit_at=None, why="", **extra):
        tid = stable_id(self.sid, arm, sym, enter_day, enter_at, extra.get("event", ""))
        if any(t["id"] == tid for t in self.tr):
            return None
        t = {"id": tid, "sym": sym, "side": int(side), "notional": float(notional), "units": None, "arm": arm,
             "enter_day": enter_day, "enter_at": enter_at, "exit_day": exit_day, "exit_at": exit_at,
             "status": "planned", "entry_ref": None, "exit_ref": None, "why": why[:200]}
        t.update(extra)
        self.tr.append(t)
        return t

    def held(self, sym=None, arm=None):
        return [t for t in self.tr if t["status"] == "held" and (sym is None or t["sym"] == sym)
                and (arm is None or t["arm"] == arm)]

    def open_or_planned(self, sym=None, arm=None):
        return [t for t in self.tr if t["status"] in ("planned", "held") and (sym is None or t["sym"] == sym)
                and (arm is None or t["arm"] == arm)]

    def close_now(self, t, why, at="now"):
        """a rule exit decided this pass: at "now" (marketable) or "close" (the auction, when inside its window)."""
        if t["status"] == "held":
            t["exit_day"], t["exit_at"], t["exit_why"] = self.today, at, why[:160]

    # -- the pass ---------------------------------------------------------------------------------------------
    def _units(self, t, px):
        u = t["notional"] / px
        if t["side"] < 0 and self.whole_short:
            return float(max(1, math.floor(u)))
        return round(u, 4)

    def step(self):
        now, today = self.now, self.today
        trading = cal.is_trading_day(today)
        for t in self.tr:
            if t["status"] == "planned":
                if t["enter_day"] < today or (t["enter_day"] == today and trading and not before_cutoff(now)
                                              and now >= cal.session_open(today)):
                    t["status"], t["void_why"] = "void", "entry window passed unfilled"
                    continue
                if t["enter_day"] != today or not trading or not before_cutoff(now):
                    continue
                cls = None
                if t["enter_at"] == "close":
                    if in_moc_window(now):
                        cls = "cls"
                elif now >= cal.session_open(today):
                    cls = "mkt"
                if cls is None:
                    continue
                px = price_of(self.view, t["sym"])
                if not px:
                    continue
                t["units"] = self._units(t, px)
                t["entry_ref"], t["entered_at"], t["status"] = px, now, "held"
                self.changes.append((t["sym"], t["side"] * t["units"], cls, t["id"]))
            elif t["status"] == "held" and t.get("exit_day"):
                if not trading or not in_rth(now):
                    continue
                cls = None
                if t["exit_day"] < today:
                    cls = "mkt"                                   # overdue (the sleeve missed its window)
                elif t["exit_day"] == today:
                    if t["exit_at"] == "close":
                        if in_moc_window(now):
                            cls = "cls"
                        elif not before_cutoff(now):
                            cls = "mkt"                           # past the auction cutoff: trade now
                    elif t["exit_at"] in ("open", "now"):
                        cls = "mkt"
                if cls is None:
                    continue
                if cls == "cls" and self._entry_working(t["sym"]):
                    continue                                      # the entry child is still working: wait
                px = price_of(self.view, t["sym"])
                t["exit_ref"], t["exited_at"], t["status"] = px, now, "closed"
                if px and t.get("entry_ref"):
                    t["ret_ref"] = round(t["side"] * (px / t["entry_ref"] - 1.0), 6)
                self.changes.append((t["sym"], -t["side"] * t["units"], cls, t["id"]))
        self._prune()

    def _entry_working(self, sym):
        for ch in (self.view.extra or {}).get("pending_orders", []) or []:
            if ch.get("inst") == "EQ:" + sym and ":mkt:" in str(ch.get("signal_key") or "") and \
                    float(ch.get("vqty") or 0.0) - float(ch.get("filled_v") or 0.0) > EPS:
                return True
        return False

    def _prune(self):
        cut = add_sessions(self.today, -KEEP_CLOSED_DAYS) if cal.is_trading_day(self.today) else self.today
        self.tr[:] = [t for t in self.tr if t["status"] in ("planned", "held")
                      or (t.get("exit_day") or t.get("enter_day") or "") >= cut]

    def desired(self):
        out = {}
        for t in self.tr:
            if t["status"] == "held" and t.get("units"):
                out[t["sym"]] = out.get(t["sym"], 0.0) + t["side"] * t["units"]
        return out

    def intents(self, window_s=None):
        """orders taking the virtual book to the ledger's net position, split by order class."""
        if not in_rth(self.now):
            return []
        want = self.desired()
        have = signed_book(self.view)
        by_sym = {}
        for sym, d, cls, tid in self.changes:
            by_sym.setdefault(sym, {}).setdefault(cls, [0.0, []])
            by_sym[sym][cls][0] += d
            by_sym[sym][cls][1].append(tid)
        out = []
        close = cal.session_close(self.today)
        win = window_s or max(60.0, close - self.now - MOC_CUTOFF_MIN * 60)
        for sym in sorted(set(want) | set(have) | set(by_sym)):
            cur = have.get(sym, 0.0)
            target = want.get(sym, 0.0)
            px = price_of(self.view, sym) or 0.0
            parts = by_sym.get(sym, {})
            cls_d, cls_ids = parts.get("cls", [0.0, []])
            # the auction leg first (this pass's market-on-close changes), then everything else at market
            if abs(cls_d) > EPS:
                new = cur + cls_d
                if self._negligible(new, px):            # fill rounding: the book's last 1e-6 share is the same lot
                    new = 0.0
                out += self._orders(sym, cur, new, "cls", cls_ids, win)
                cur = new
            mkt_ids = parts.get("mkt", [0.0, []])[1]
            if not self._negligible(target - cur, px):
                if not mkt_ids and not before_cutoff(self.now):
                    continue
                out += self._orders(sym, cur, target, "mkt", mkt_ids or ["fix", round(target, 4)], win)
        return out

    @staticmethod
    def _negligible(q, px):
        """a quantity below a ten-thousandth of a share or worth under a dollar is fill rounding, not an order."""
        return abs(q) < 1e-4 or (px > 0 and abs(q) * px < 1.0)

    def _orders(self, sym, cur, new, cls, ids, win):
        spec = OrderSpec(type="market", tif="cls") if cls == "cls" else OrderSpec(window_s=win)
        key = f"{sym}:{self.today}:{cls}:{stable_id(*ids)}"
        px = price_of(self.view, sym)
        res = []
        if cur * new < -EPS:                                        # flip: close, then open the other side
            res.append(Intent("exit", sym, qty=abs(cur), price_hint=px, order=spec, signal_key=key + ":x",
                              reason=f"ledger flip {cur:+.4f} -> {new:+.4f}"))
            cur = 0.0
        if abs(new) > abs(cur) + EPS:
            res.append(Intent("enter", sym, side="long" if new > 0 else "short", qty=round(abs(new) - abs(cur), 6),
                              price_hint=px, order=spec, signal_key=key + ":e",
                              reason=f"ledger {cur:+.4f} -> {new:+.4f} ({cls})"))
        elif abs(new) < abs(cur) - EPS:
            res.append(Intent("exit", sym, qty=round(abs(cur) - abs(new), 6), price_hint=px, order=spec,
                              signal_key=key + ":x", reason=f"ledger {cur:+.4f} -> {new:+.4f} ({cls})"))
        return res


# -- base sleeve ----------------------------------------------------------------------------------------------------
class KilledSleeve(Sleeve):
    """subclasses set SLEEVE_ID, SOURCE, PARAMS, NEEDS, SCHEDULE, CADENCE, UNIVERSE and implement plan()."""
    SLEEVE_ID = ""
    SOURCE = {}
    PARAMS = {}
    NEEDS = {}
    SCHEDULE = "premarket,rth"
    CADENCE = 300
    UNIVERSE = ()
    QUOTE_ALWAYS = ()
    WHOLE_SHORT = True
    DIVERGENCES = []

    def __init__(self):
        params = dict(self.PARAMS, named_divergences=COMMON_DIVERGENCES + list(self.DIVERGENCES))
        self.CONFIG = SleeveConfig(sleeve_id=self.SLEEVE_ID, family=FAMILY, cadence_s=self.CADENCE,
                                   universe=tuple(self.UNIVERSE), capital=CAPITAL, needs=self.NEEDS,
                                   schedule=self.SCHEDULE, params=params, source=self.SOURCE,
                                   state_schema={"tranches": "list", "born": "str"})
        self._st = None
        self._want = set()
        self._extra_want = set()          # symbols plan() wants quoted from the next pass (e.g. pair legs)

    def quote_universe(self, now, book=None):
        """quotes for what the sleeve holds or is about to trade (the ledger's planned / held tranches)."""
        held = {p[3:] for p in (getattr(book, "positions", None) or {}) if str(p).startswith("EQ:")}
        return sorted(held | self._want | set(self.QUOTE_ALWAYS))

    def plan(self, view, st, tb):
        raise NotImplementedError

    def signal(self, view):
        import copy
        st = copy.deepcopy(dict(view.state or {}))
        st.setdefault("born", et_day(view.now))
        tb = TrancheBook(st, view, self.SLEEVE_ID, whole_short=self.WHOLE_SHORT)
        obs = self.plan(view, st, tb) or []
        tb.step()
        out = list(obs) + tb.intents()
        self._want = {t["sym"] for t in st.get("tranches", []) if t["status"] in ("planned", "held")} | \
            set(self._extra_want)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})
