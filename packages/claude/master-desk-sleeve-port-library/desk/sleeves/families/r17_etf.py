"""R17 ETF ladder rules (6): ACCEL3, ESCAPE1, LEADER3, RELATIVE3, REPAIR3, VOLADJ3.

Source: quant-research-backup@d170596b research-archives/2026-10-09-third-pass-edge-r17/inventions/run_ladder.py
(blob 0392bb5d) and its EXPERIMENT_PROTOCOL.json (blob e0c26c42), both vendored byte-exact in desk/vendor/quant_r17/
and loaded from there (the module reads its protocol from its own directory, as in its own tree).

The vendored `weights(rule, closes, i)` decides on the completed month-end close. This wrapper carries out the
book law of the source's `run_account` for the protocol's primary cell: a cash account, gross target 0.98,
15 bp per side, $100,000. That is the cell the R17 precursors (LEADER1 / *_HOLD) were superseded into as the
R19 C098 books.
  * closes: all-adjusted (total-return) daily closes on QQQ's session axis, NaN where a fund has no bar. A
    decision needs 252 QQQ sessions through the signal close (the source's i >= 251).
  * decision: after each month-end close. At inception it is the last month-end before the first open (the
    source's origins[-1]). Pending weights x gross become desired units at the next open, from that open's marks
    and the pretrade NAV. Desired units persist until the next decision, and residuals keep trading.
  * each open: sells first. Each fund is capped at 0.1% of its prior-session raw dollar volume, and the cap is
    shared by sells, then buys. Buys are capped the same way and scaled to settled cash / (1 + cost). Sale
    proceeds settle on the source's settlement_lag table (T+1 now) and cannot be spent before then. Units are
    fractional. Each side costs 15 bp.
  * margin cells (gross > 1; parameterised, not the deployed cell): buying power is gross x NAV - held, with a
    10%/yr debit carry (the engine's carry). Under the maintenance rule, a prior-close gross/NAV > 2 replaces that
    day's decision with a proportional reduction to the target gross at the next open.
Gone under the cutover doctrine: nothing. The source has no desk-wide gates.
Named divergences (the research ledger's plumbing and timing, moved onto this engine):
  1. open price: the quote source's session open (Alpaca snapshot daily bar / Yahoo quote) when it is today's,
     else the live mid. The research filled at the official adjusted open. Here fills are live marketable orders
     in the first minutes, so the fill price differs from the open. The cash scale uses the open, so a cash book
     can dip marginally below zero on an adverse fill.
  2. decision clock: the month-end decision is taken in a pass after the month-end close. If that pass was
     missed, it is taken at the next open on the same completed closes. The open pass converts it.
  3. data: a decision waits while QQQ, or a fund with history, lacks its bar at the signal close. The research's
     NaN there meant "not yet listed"; live it is a fetch gap. The open retries on the next pass or session.
  4. a missed open (desk down) executes at the next observed open, which is the source's own "next observed"
     proxy.
  5. execution granularity: the engine skips target changes under $1 notional (min_rebalance_usd); the venue order
     is floored to 1e-6 shares while a complete fill books the sleeve's own quantity (the OMS re-bases the replica
     target). The source traded any amount over 1e-10 units.
  6. dividends: research prices are total-return adjusted. The virtual book marks raw prices and does not
     accrue distributions.
Parity: tools/parity/r17_etf.py -> docs/receipts/parity/r17_etf.json."""
import functools
import importlib.util
import math
import os
from datetime import date, timedelta

import numpy as np

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig

VDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor", "quant_r17")
SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
          "path": "research-archives/2026-10-09-third-pass-edge-r17/inventions/run_ladder.py",
          "blob": "0392bb5d96b99f5ada412fbeaa92e95704f55a87",
          "protocol_blob": "e0c26c420e92f0e9a2bc0b9690998941468c41fe"}
RULES = ("ACCEL3", "ESCAPE1", "LEADER3", "RELATIVE3", "REPAIR3", "VOLADJ3")
EVENING = 20 * 60          # a session's daily bar is final 20 minutes after its close (the hub's equity delay)
_MOD = None


def ladder():
    """the vendored run_ladder module, loaded from its own directory (it reads EXPERIMENT_PROTOCOL.json there)."""
    global _MOD
    if _MOD is None:
        spec = importlib.util.spec_from_file_location("quant_r17_run_ladder", os.path.join(VDIR, "run_ladder.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MOD = mod
    return _MOD


@functools.lru_cache(maxsize=1 << 16)
def _session_at(t):
    return cal._as_date(t + 6 * 3600).isoformat()


def session_of(bar):
    """a daily bar's session date (Alpaca stamps 04:00/05:00 UTC, Yahoo the open; +6h dates both correctly)."""
    return _session_at(float(bar["t"]))


def is_month_end(d):
    d = cal._as_date(d)
    return cal.next_trading_day(d).month != d.month


def month_end_through(d):
    """the latest month-end session <= d (d a session)."""
    d = cal._as_date(d)
    if is_month_end(d):
        return d.isoformat()
    first = date(d.year, d.month, 1)
    while not cal.is_trading_day(first):
        first += timedelta(days=1)
    return cal.prev_trading_day(first).isoformat()


def panel(bars_by_sym, syms, through):
    """(dates, closes[len(dates), len(syms)]) on QQQ's session axis up to `through` (inclusive): all-adjusted closes,
    NaN where a fund has no bar that session."""
    q = {}
    for b in bars_by_sym.get("QQQ") or []:
        s = session_of(b)
        if s <= through:
            q[s] = None
    dates = sorted(q)
    pos = {d: k for k, d in enumerate(dates)}
    c = np.full((len(dates), len(syms)), np.nan)
    for j, sym in enumerate(syms):
        for b in bars_by_sym.get(sym) or []:
            k = pos.get(session_of(b))
            if k is not None:
                c[k, j] = float(b.get("ac") or b["c"])
    return dates, c


def decision_ready(bars_by_sym, syms, signal):
    """every fund with any bar on or before the signal session has its bar AT the signal session (else a fetch gap:
    wait). Funds with no bar yet are not listed (NaN, ineligible in the source)."""
    for sym in syms:
        sess = [session_of(b) for b in bars_by_sym.get(sym) or [] if session_of(b) <= signal]
        if sym == "QQQ" and not sess:
            return False
        if sess and sess[-1] != signal:
            return False
    return True


def last_closes(bars_by_sym, syms, floor, end, inclusive=False):
    """the source's `lastclose`: per fund, the last finite positive close from `floor` (the session before the
    account's first day, cl[a-1]) up to `end` (exclusive unless inclusive); NaN when there is none in that span."""
    out = np.full(len(syms), np.nan)
    for j, s in enumerate(syms):
        for b in bars_by_sym.get(s) or []:
            d = session_of(b)
            if d < floor or (d > end if inclusive else d >= end):
                continue
            v = float(b.get("ac") or b["c"])
            if math.isfinite(v) and v > 0:
                out[j] = v
    return out


def value_held(units, marks):
    """the source's value_held (raises on a missing valuation of a held fund)."""
    active = units > 1e-12
    if not np.all(np.isfinite(units)) or np.any(units < -1e-8):
        raise ValueError("Invalid holdings")
    if not np.all(np.isfinite(marks[active]) & (marks[active] > 0)):
        raise ValueError("Missing held valuation")
    return float(units[active] @ marks[active])


def open_step(units, desired, pending, op, lastclose, dv_prev, cash_settled, receivables_total, gross, cost):
    """one session open of run_account (after interest and matured receivables): returns
    (desired, sells[], buys[], new_receivables[(qty, notional - fee)]), arrays over the universe.
    cash_settled = the source's `cash`; receivables_total = unsettled proceeds (part of NAV, not spendable)."""
    margin = gross > 1
    units = units.copy()
    marks = np.where(np.isfinite(op) & (op > 0), op, lastclose)
    nav = cash_settled + receivables_total + value_held(units, marks)
    if not math.isfinite(nav):
        raise ValueError("Nonfinite account NAV")
    if pending is not None:
        desired = np.divide(pending * nav, marks, out=units.copy(), where=np.isfinite(marks) & (marks > 0))
    cap = np.maximum(0, np.nan_to_num(dv_prev, nan=0.)) * 0.001
    sells = np.zeros(len(units))
    rec_total = receivables_total
    new_rec = []
    for j in range(len(units)):
        if not np.isfinite(op[j]) or op[j] <= 0:
            continue
        qty = min(max(0., units[j] - desired[j]), cap[j] / op[j])
        if qty > 1e-10:
            notional = qty * op[j]
            fee = notional * cost
            units[j] -= qty
            cap[j] -= notional
            sells[j] = qty
            new_rec.append(notional - fee)
            rec_total += notional - fee
    needed = np.maximum(0, desired - units)
    valid = np.isfinite(op) & (op > 0)
    needed[~valid] = 0.
    capacity = np.divide(cap, op, out=np.zeros(len(units)), where=valid)
    needed = np.minimum(needed, capacity)
    nav = cash_settled + rec_total + value_held(units, marks)
    if margin:
        available = max(0., gross * nav - value_held(units, marks))
        denom = 1 + gross * cost
    else:
        available = max(0., cash_settled)
        denom = 1 + cost
    requested = float(needed @ np.where(valid, op, 0.))
    scale = min(1., available / (requested * denom)) if requested > 0 else 0.
    buys = np.zeros(len(units))
    for j in range(len(units)):
        qty = needed[j] * scale
        if qty > 1e-10:
            buys[j] = qty
    return desired, sells, buys, new_rec


class R17Etf(Sleeve):
    def __init__(self, rule, gross=0.98, cost_bps=15.0, capital=100_000.0):
        L = ladder()
        self.rule = rule
        self.syms = list(L.SYMS)
        self.gross = float(gross)
        self.cost = float(cost_bps) / 1e4
        self.CONFIG = SleeveConfig(
            sleeve_id="r17_" + rule.lower(), family="r17_etf", cadence_s=60, universe=tuple(self.syms),
            capital=float(capital),
            # the open conversion (first minutes of the session) and the post-close decision pass
            schedule="open+1:open+10,after_close+20:after_close+240",
            needs={"bars": [{"source": "equity", "interval": "1d", "n": 300, "symbols": list(self.syms)},
                            {"source": "equity_split", "interval": "1d", "n": 5, "symbols": list(self.syms),
                             "key": "dv"}],
                   "quotes": {"source": "equity", "symbols": list(self.syms)}},
            params={"rule": rule, "gross": self.gross, "cost_bps": float(cost_bps),
                    "margin_rate": L.P["risk_and_cost_cells"]["margin_interest_annual"] if self.gross > 1 else 0.0,
                    "capacity_prior_day_dollar_volume": L.P["risk_and_cost_cells"]["capacity_prior_day_dollar_volume"]},
            source=dict(SOURCE, rule=rule),
            state_schema={"last_signal": "str|None", "pending": "dict|None", "desired": "dict", "receivables": "list",
                          "plan": "dict|None", "inception": "str|None", "decisions": "list"})

    # -- helpers -----------------------------------------------------------------------------------------
    def _units(self, view):
        u = np.zeros(len(self.syms))
        for inst, p in view.positions.items():
            if inst.startswith("EQ:") and inst[3:] in self.syms:
                u[self.syms.index(inst[3:])] = float(p["qty"])
        return u

    def _decide(self, st, bars, signal, reason):
        """month-end weights x gross from the vendored evaluator, or None while the closes are incomplete."""
        if not decision_ready(bars, self.syms, signal):
            return None
        dates, c = panel(bars, self.syms, signal)
        i = len(dates) - 1
        if i < 251 or dates[i] != signal:
            return None
        w = ladder().weights(self.rule, c, i) * self.gross
        return {"signal": signal, "weights": [float(x) for x in w], "reason": reason}

    def _maintenance(self, view, st, bars, through):
        """margin cells: prior-close gross/NAV > 2 -> proportional reduction to the target gross (or None)."""
        if self.gross <= 1:
            return None
        units = self._units(view)
        if not np.any(units > 1e-12):
            return None
        floor = cal.prev_trading_day(st["inception"]).isoformat()
        last = last_closes(bars, self.syms, floor, through, inclusive=True)
        held = value_held(units, last)
        nav = float(view.cash) + held
        if nav > 0 and held / nav > 2.:
            pw = np.zeros(len(self.syms))
            active = units > 1e-12
            pw[active] = (units[active] * last[active] / held) * self.gross
            return {"signal": through, "weights": [float(x) for x in pw], "reason": "maintenance"}
        return None

    # -- the pass ----------------------------------------------------------------------------------------
    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("desired", {})
        st.setdefault("receivables", [])
        st.setdefault("decisions", [])
        bars = view.bars.get("1d") or {}
        now, session = float(view.now), view.session
        trading = cal.is_trading_day(session)
        evening = trading and now >= cal.session_close(session) + EVENING
        opening = trading and cal.session_open(session) <= now < cal.session_close(session)
        out = []
        if evening:
            # post-close: the decision for the next open (maintenance first, as in the source's day end)
            me = month_end_through(session)
            m = self._maintenance(view, st, bars, session) if st.get("inception") else None
            if m is not None and st.get("maint_checked") != session:
                st["pending"] = m
                if me == session:
                    st["last_signal"] = session                # that day's month-end decision is replaced
            elif st.get("last_signal") != me:
                d = self._decide(st, bars, me, "month_end" if st.get("inception") else "initial")
                if d is not None:
                    st["pending"] = d
                    st["last_signal"] = me
            if st.get("inception"):
                st["maint_checked"] = session                  # one day-end check per session
            self._st = st
            return out
        if not opening:
            self._st = st
            return out
        plan = st.get("plan")
        if plan and plan.get("session") == session:
            out = self._intents(plan, session)                 # the step is taken once per session
            self._st = st
            return out
        # missed post-close pass: decide at the open on the same completed closes
        prev = cal.prev_trading_day(session).isoformat()
        me = month_end_through(prev)
        if st.get("last_signal") != me and not (st.get("pending") or {}).get("signal") == me:
            d = self._decide(st, bars, me, "month_end" if st.get("inception") else "initial")
            if d is None:
                self._st = st
                return [Intent("signal", "QQQ", reason=f"{self.rule}: waiting for the {me} closes",
                               signal_key=f"wait:{me}", meta={"waiting_for": me})]
            st["pending"] = d
            st["last_signal"] = me
        out = self._open(view, st, session, bars)
        self._st = st
        return out

    def _open(self, view, st, session, bars):
        L = ladder()
        syms = self.syms
        # matured receivables (due <= today) become settled cash; the rest stay unsettled
        recs = [r for r in st.get("receivables") or [] if r[0] > session]
        unsettled = sum(float(r[1]) for r in recs)
        cash_settled = float(view.cash) - unsettled
        units = self._units(view)
        op = np.full(len(syms), np.nan)
        for j, s in enumerate(syms):
            q = view.quotes.get(s) or {}
            o = q.get("day_open") if (q.get("day_date") or q.get("session")) == session else None
            if not o:
                bid, ask = q.get("bid"), q.get("ask")
                o = (float(bid) + float(ask)) / 2 if bid and ask else q.get("last")
            if o and float(o) > 0:
                op[j] = float(o)
        prev = cal.prev_trading_day(session).isoformat()
        floor = cal.prev_trading_day(st.get("inception") or session).isoformat()
        lastclose = last_closes(bars, syms, floor, session)
        dvb = view.extra.get("bars_dv") or {}
        dv_prev = np.full(len(syms), np.nan)
        for j, s in enumerate(syms):
            for b in dvb.get(s) or []:
                if session_of(b) == prev:
                    dv_prev[j] = float(b["c"]) * float(b.get("v") or 0)
        desired = np.array([float(st["desired"].get(s, 0.0)) for s in syms])
        pending = st.get("pending")
        pw = np.array(pending["weights"]) if pending and pending["signal"] < session else None
        desired, sells, buys, new_rec = open_step(units, desired, pw, op, lastclose, dv_prev, cash_settled, unsettled,
                                                  self.gross, self.cost)
        if pw is not None:
            st["decisions"] = (st["decisions"] + [{"signal": pending["signal"], "executed": session,
                                                   "reason": pending["reason"],
                                                   "weights": {s: w for s, w in zip(syms, pending["weights"]) if w}}])[-24:]
            st["pending"] = None
            st.setdefault("inception", session)
        st["desired"] = {s: float(x) for s, x in zip(syms, desired) if abs(x) > 0}
        lag = L.settlement_lag(session)
        due = cal.next_trading_day(session, lag).isoformat()
        st["receivables"] = recs + [[due, float(x)] for x in new_rec]
        targets = {}
        for j, s in enumerate(syms):
            if sells[j] > 0:
                targets[s] = {"side": "sell", "qty": float(units[j] - sells[j]), "trade": float(sells[j]),
                              "px": float(op[j])}
            elif buys[j] > 0:
                targets[s] = {"side": "buy", "qty": float(units[j] + buys[j]), "trade": float(buys[j]),
                              "px": float(op[j])}
        plan = {"session": session, "targets": targets}
        st["plan"] = plan
        return self._intents(plan, session)

    def _intents(self, plan, session):
        out = []
        for s, t in sorted(plan["targets"].items(), key=lambda kv: (kv[1]["side"] != "sell", kv[0])):
            out.append(Intent("target", s, qty=max(0.0, t["qty"]), price_hint=t["px"],
                              signal_key=f"{s}:{session}:{t['side']}",
                              reason=f"R17 {self.rule} {t['side']} {t['trade']:.6f} -> {t['qty']:.6f}",
                              order=OrderSpec(window_s=900)))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [R17Etf(r) for r in RULES]
