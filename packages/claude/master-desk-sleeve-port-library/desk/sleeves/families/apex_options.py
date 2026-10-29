"""APEX options (family "apex_options") — the research desk's 15 option sleeves on the engine.

Source: cursor2 main @ca8ac1f650670e1d — desk/options/strategies.py (O1-O12, pre-registered in
research/PREREGISTRATION_OPTIONS.md, _v2, _v3; run by research/run_options_study.py, _v2, _v3 on QQQ with the
VXN-based calibrated surface, dividend 0.55%, OptionCosts()) and desk/strategies.py e4_tail_hedge on
desk/backtest/options.py tail_hedge_overlay (E4; research/run_study.py). The strategies and their Book are vendored in
desk/vendor/apex/ (verbatim excerpts); each sleeve runs its strategy function unchanged with the Book replaced by a
LiveBook (desk/sleeves/families/apex.py) that holds the sleeve's own contracts and equity, so the source's decide()
makes today's decision on the source's own inputs (desk/feedlib/apex.option_context: the signals through the last
finished session, today's QQQ price, T-bill rate, month start and surface at today's live index levels).

  apex_o1_convex               core QQQ up to min(L*, 1) (its band and lag), the rest via 3-month ATM calls,
                               re-struck at each month start or on a 0.5 exposure mismatch
  apex_o1b_convex_incremental  the same tranche, adjusted in units of the held call, rolled < 45 days / delta out
                               of [0.30, 0.85]
  apex_o2_leaps_apex           the whole L* in 1-year 0.80-delta calls (re-struck on a 0.5 mismatch, < 183 days)
  apex_o2b_leaps_incremental   the same, adjusted in units, rolled < 183 days or delta out of [0.60, 0.95]
  apex_o10_leaps_vv            O2b plus the Variance Value monthly rule
  apex_o3_regime_putwrite      month start, L* > 0: puts 0.5 sigma below spot on min(L*, 3) x NAV; L* = 0 closes
  apex_o4_phoenix / o5_chop_harvest / o8_fear_put_spread / o9_omega / o11_apex_vv
                               the APEX-50F core plus the PHOENIX calls, the CHOP condor, the FEAR put spread,
                               all three, or the Variance Value fly / straddle
  apex_o6_variance_value       a QQQ core plus the Variance Value rule
  apex_o7_skew_risk_reversal   a QQQ core plus 25-delta risk reversals in strong calm trends
  apex_o12_hybrid_leaps        1-year 0.80-delta calls for 75% of L*, a QQQ trim for the rest (traded on a 0.2 move)
  apex_e4_rolling_tail_puts    the APEX-30 core plus, each month while its exposure exceeds 1.5, puts 15% below spot
                               for 63 sessions on exposure x NAV (closed and re-bought at every month start)

Execution: options in the last 45 minutes before the auction cutoff, once per session (frozen): a structure the
source opens in one decision (fly, straddle, condor, put spread, risk reversal) is one multi-leg package, single
contracts are marketable limits; the core is the sleeve's own book (QQQ / TQQQ / BIL by the source desk's
alpaca_weights, O12's trim in QQQ, long or short), market-on-close, on the equity left after the options the
decision leaves held (the source's Book core: NAV less its legs after decide(); held contracts at their marks, the
decision's new ones at the listed mid). Expiration is the engine's settlement (QQQ is exercised / assigned). When the
options cannot decide (no context, an error, a refusal on impossible inputs: OPT-03) the core still goes to its plan
from the daily decision, net of the options held at their marks, in the window's second half (OPT-02).

Gone under the cutover doctrine: nothing desk-wide existed in these research strategies (they never ran live); the
source desk's Compliance block and the options' shadow-only status do not apply.

Named divergences: the book is $1,000,000 (the source's NAV was unitless; whole contracts at ~$60,000 notional each
track its continuous units to ~1%); each contract is the listed QQQ monthly (E4: the listed expiration nearest 63
sessions) and the listed strike nearest the source's continuous strike, in whole contracts (rounded), and a decision
under one contract is skipped; fills are the market's (natural / marketable) in the last hour, not the model's
close price plus a modelled half-spread; the surface reads today's live VXN / VIX family levels (Yahoo's when it has
today's, else CBOE's delayed quote; else the last close; the source read the close of the same day); O12's futures trim is QQQ shares; the source's simulated core accounting (O12's futures P&L line,
LETF / futures cost models) is the book's own marks; E4's puts are QQQ puts 15% below QQQ's price on exposure x NAV
of QQQ (the source struck them on the Nasdaq-100 total-return level, the same proportions), on the listed expiration
(weekly or monthly) nearest its 63 sessions, priced by the market, not its Black-Scholes with a 0.7-point skew and a
5% spread."""
import math

from ... import calendar as cal
from ...contract import Intent, OrderSpec
from ...feedlib import apex as AF, apex_rules as R
from .apex import (ApexOptionSleeve, OptionRefusal, _intent_dict, _intent_of, allocate, impossible_inputs, legs_of,
                   rate_of, share_targets, value_after)

TRIGGER, OTM, TENOR = 1.5, 0.15, 63                 # tail_hedge_overlay's defaults (e4_tail_hedge passes spread only)
CORE_ALONE_MIN = 30         # OPT-02: without options the core goes from 30 minutes before the close (the window's
                            # second half, which a 600 s cadence from close-45 always reaches)


def _costs():
    from ...vendor.apex import sim as VS
    return VS.OptionCosts()


class OptionBook(ApexOptionSleeve):
    """an option sleeve: the source's options decision once per session + its core, market-on-close."""
    CORE = "cash"

    def __init__(self, sid, title):
        super().__init__(sid, title, feeds=("apex", "apex_live"))     # "apex": the core when options cannot run

    def core_plan(self, live):
        if self.CORE == "apex50f":
            return {"NDX": float(live["plans"]["apex50f"])}
        if self.CORE == "apex30":
            return {"NDX": float(live["plans"]["apex30"])}
        if self.CORE == "qqq":
            return {"NDX": 1.0}
        if self.CORE == "o1":                            # simulate(min(L*, 1), LETF costs, band 0.2): its plan
            from ...vendor.apex import agents as AG
            a, kw, out = self._core_calls[-1]
            t = live["m"].index[-1]
            return {"NDX": AG.planned_position(float(a[0].reindex(out.index).loc[t]), float(out["position"].loc[t]),
                                               kw.get("band", 0.20))}
        return {}

    def trim(self, view):
        return 0.0

    def core_targets(self, view, core, v, px):
        """the core plan on the equity less the options' value v (the source's Book core), O12's QQQ trim out of the
        T-bills, never T-bills below zero -> (share targets, the trim)."""
        eq = float(view.equity)
        usd = allocate([[(eq - v) / eq if eq else 0.0, core, "CASH"]], eq)
        fe = self.trim(view)
        if fe:
            usd["QQQ"] = usd.get("QQQ", 0.0) + fe * eq
            usd["BIL"] = usd.get("BIL", 0.0) - fe * eq
        if usd.get("BIL", 0.0) < 0:
            usd["BIL"] = 0.0                              # the core is overdrawn: a debit, no T-bills
        return share_targets(usd, px), fe

    def fallback_core(self, feed):
        """the core's plan without the option context: the daily decision the apex sleeves trade (APEX-50F is the live
        tier's plan, APEX-30 its tier: option_context computes the same numbers on the same history), QQQ 1x, or none
        (T-bills). O1 / O1b's band-0.2 core exists only inside the option strategy's own run: its last decided plan
        holds. None when there is no plan."""
        tiers = (feed.get("sleeves") or {}).get("apex_trend_har_tiers") or {}
        if self.CORE == "qqq":
            return {"NDX": 1.0}
        if self.CORE == "o1":
            return ((self._st.get("plan") or {}).get("decision") or {}).get("plan")
        if self.CORE not in ("apex50f", "apex30"):
            return {}
        v = (tiers.get("plan") or {}).get("NDX") if self.CORE == "apex50f" else (tiers.get("obs") or {}).get("APEX-30")
        return {"NDX": float(v)} if v is not None and math.isfinite(float(v)) else None

    def core_without_options(self, view):
        """OPT-02 (Edge audit 2026-10-25): the core keeps its decided target when the option decision cannot run (no
        option context, an options error, an OPT-03 refusal). 2026-10-19 and 10-20 the context failed every pass and
        the 15 books left their cores alone: the five APEX-50F clones held L* 2.653 for two sessions while the live
        tier traded 1.407. The fallback plan is sized as the normal path sizes the core, on the equity less the
        options held at their marks (no option trades today), and frozen under the context's own key
        (completed_through, live["as_of"]): a context that returns later in the window keeps it, as VVSleeve's
        exposure books do, so no core is ordered twice. It waits for the window's second half: a context that returns
        before then decides the options and the core together, and the core's orders are market-on-close either way."""
        left = cal.minutes_to_close(view.now)
        if left is not None and left > CORE_ALONE_MIN:
            return []
        feed = view.extra.get("apex") or {}
        if feed.get("error") or not feed.get("px"):
            err = feed.get("error") or "no daily decision"
            return [self._obs(view, "core: no decision: %s" % err, {"error": err})]
        if feed.get("exec") != view.session:
            return [self._obs(view, "core: the decision of %s executes on %s, not %s: waiting" % (
                feed.get("as_of"), feed.get("exec"), view.session), {"as_of": feed.get("as_of"), "exec": feed.get("exec")})]
        st = self._st
        as_of = AF.A.completed_through(view.now).isoformat()
        plan = st.get("plan") or {}
        if plan.get("as_of") != as_of:
            core = self.fallback_core(feed)
            if core is None:
                return [self._obs(view, "core: no plan without the option context", {"core": self.CORE})]
            v = value_after(view, self.TAGS, (), None)
            try:
                targets, fe = self.core_targets(view, core, v, feed["px"])
            except RuntimeError as e:
                return [self._obs(view, "no targets: %s" % e, {"error": str(e)})]
            plan = {"as_of": as_of, "exec": view.session, "targets": targets, "equity": float(view.equity),
                    "decision": {"plan": core, "options_value": v, "trim": fe, "without_options": feed.get("as_of")},
                    "obs": {"ops": 0}}
            st["plan"] = plan
        return self.exposure_intents(view, plan, feed["px"])

    def signal(self, view):
        sid = self.CONFIG.sleeve_id
        st = dict(view.state or {})
        self._st = st
        live = view.extra.get("apex_live") or {}
        if not live or live.get("error"):
            err = live.get("error") if live else "no option context"
            return [self._obs(view, "no decision: %s" % err, {"error": err})] + self.core_without_options(view)
        if live.get("session") != view.session:
            return []
        try:
            fr = self.decide_options(view, live, None)
        except OptionRefusal as e:                       # OPT-03: impossible inputs, no option order
            return [self._refused(view, e)] + self.core_without_options(view)
        except Exception as e:
            return [self._obs(view, "options error: %s: %s" % (type(e).__name__, str(e)[:160]), {"error": str(e)[:200]})
                    ] + self.core_without_options(view)
        out = [_intent_of(x) for x in fr["intents"]]
        plan = st.get("plan") or {}
        if plan.get("as_of") != live["as_of"]:
            eq = float(view.equity)
            v = value_after(view, self.TAGS, fr["ops"], live.get("listing"))
            core = self.core_plan(live)
            try:
                targets, fe = self.core_targets(view, core, v, live["px"])
            except RuntimeError as e:
                return out + [self._obs(view, "no targets: %s" % e, {"error": str(e)})]
            plan = {"as_of": live["as_of"], "exec": live["session"], "targets": targets, "equity": eq,
                    "decision": {"plan": core, "options_value": v, "trim": fe}, "obs": {"ops": len(fr["ops"])}}
            st["plan"] = plan
        out += self.exposure_intents(view, plan, live["px"])
        if fr["ops"]:
            out.append(Intent("signal", "QQQ", reason=("%s options %s: %s" % (sid, view.session, "; ".join(
                "%s %s" % (o["op"], o.get("tag")) for o in fr["ops"])))[:300], meta={"ops": fr["ops"]},
                signal_key="%s:%s:options" % (sid, view.session)))
        return out


class OptionRow(OptionBook):
    """one of O1-O12: the source strategy function, unchanged, on the LiveBook."""

    def __init__(self, sid, title, fn, tags, core, o12=False):
        super().__init__(sid, title)
        self.fn, self.TAGS, self.CORE, self.O12 = fn, tags, core, o12
        self._core_calls = []

    def option_call(self, view, live, d):
        x, m, surf = live["x"], live["m"], live["surface"]
        start = len(x.dates) - 1
        costs = _costs()

        def call(O, C):
            with R.spy((O,), "simulate") as (calls, _):
                self.fn(O, x, m, surf, costs, start)
            self._core_calls = calls
        return call, float(view.equity), self.title, None

    def trim(self, view):
        return float((self._st.get("o12") or {}).get("fut") or 0.0) if self.O12 else 0.0


def tail_rule(new_month, held_units, ex, S, nav, trigger=TRIGGER, otm=OTM, tenor_days=TENOR):
    """tail_hedge_overlay's monthly step (desk/backtest/options.py lines 72-85): on a new month the held puts are
    closed; while the exposure held after this close exceeds the trigger, puts struck `otm` below spot for
    `tenor_days` sessions are bought on exposure x NAV / spot units. None on any other day (puts are held)."""
    if not new_month:
        return None
    out = {"close": held_units > 0, "open": None}
    if ex > trigger:
        out["open"] = {"K": (1.0 - otm) * S, "tenor": tenor_days, "units": ex * nav / S}
    return out


def _mid(q):
    b, a = q.get("bid"), q.get("ask")
    return (float(b) + float(a)) / 2.0 if b and a and float(a) >= float(b) > 0 else None


def nearest_listed(rows, typ, target_exp, K, today):
    """the listed expiration nearest `target_exp` (ties: the later) and its strike nearest K (ties: the lower)."""
    from datetime import date
    exps = sorted({str(r["expiration"])[:10] for r in rows or [] if r.get("type") == typ
                   and str(r["expiration"])[:10] > today.isoformat()})
    if not exps:
        return None
    exp = min(exps, key=lambda e: (abs((date.fromisoformat(e) - target_exp).days), -date.fromisoformat(e).toordinal()))
    ks = [(float(r["strike"]), r["symbol"]) for r in rows if r.get("type") == typ and str(r["expiration"])[:10] == exp]
    if not ks:
        return None
    k, occ = min(ks, key=lambda kv: (abs(kv[0] - K), kv[0]))
    row = next(r for r in rows if r["symbol"] == occ)
    return {"expiration": exp, "strike": k, "occ": occ, "bid": row.get("bid"), "ask": row.get("ask")}


class TailPuts(OptionBook):
    """E4: the APEX-30 core plus the rolling tail puts."""
    TAGS = ("tail",)
    CORE = "apex30"

    def decide_options(self, view, live, d):
        st = self._st
        frozen = st.get("options") or {}
        if frozen.get("session") == view.session:
            return frozen
        bad = impossible_inputs(rate_of(live))          # OPT-03 (E4's puts are struck off spot, not a delta)
        if bad:
            raise OptionRefusal(bad)
        x = live["x"]
        t = len(x.dates) - 1
        today = cal._as_date(view.session)
        held = legs_of(view, self.TAGS)
        units = sum(abs(l["units"]) for l in held)
        dec = tail_rule(bool(x.month_start[t]), units, float(live["plans"]["apex30"]), float(x.S[t]),
                        float(view.equity))
        sid, close_at = self.CONFIG.sleeve_id, cal.session_close(view.session)
        ops, intents = [], []
        if dec and dec["close"]:
            for l in held:
                n = int(abs(l["units"]) / 100.0 + 0.5)
                ops.append({"op": "close", "tag": "tail", "occ": l["occ"], "units": l["units"]})
                intents.append(Intent("exit", l["occ"], side="long" if l["units"] > 0 else "short", asset="option",
                                      qty=float(n), order=OrderSpec(type="marketable_limit", not_after=close_at),
                                      signal_key="%s:%s:close:%s" % (sid, view.session, l["occ"]),
                                      reason="%s E4 month start: close the tail puts %s" % (sid, l["occ"])))
        if dec and dec["open"]:
            o = dec["open"]
            target = cal.next_trading_day(today, o["tenor"])
            c = nearest_listed(live.get("chain"), "put", target, o["K"], today)
            n = int(o["units"] / 100.0 + 0.5)
            if c is None or n == 0:
                ops.append({"op": "skip_open", "tag": "tail", "K_model": o["K"], "units_model": o["units"],
                            "why": "no listed put" if c is None else "under one contract"})
            else:
                ops.append({"op": "open", "tag": "tail", "K": c["strike"], "K_model": o["K"], "expiry": c["expiration"],
                            "expiry_model": target.isoformat(), "units": 100.0 * n, "units_model": o["units"],
                            "occ": c["occ"], "px": _mid(c)})
                intents.append(Intent("enter", c["occ"], side="long", asset="option", qty=float(n),
                                      order=OrderSpec(type="marketable_limit", not_after=close_at),
                                      signal_key="%s:%s:open:%s" % (sid, view.session, c["occ"]),
                                      reason="%s E4: exposure %.2f > %.1f -> %d puts %s (K %.2f ~ %.2f, %s for %d "
                                             "sessions)" % (sid, live["plans"]["apex30"], TRIGGER, n, c["occ"],
                                                            c["strike"], o["K"], c["expiration"], o["tenor"]),
                                      meta={"underlying": "QQQ", "position_meta": {
                                          "tag": "tail", "K_model": o["K"], "units_model": o["units"],
                                          "expiry": c["expiration"]}}))
        frozen = {"session": view.session, "ops": ops, "nav": float(view.equity),
                  "intents": [_intent_dict(i) for i in intents]}
        st["options"] = frozen
        return frozen


ROWS_O = (
    ("apex_o1_convex", "O1 CONVEX", lambda O, x, m, s, c, t: O.o1_convex(x, m, s, c, t), ("call",), "o1", False),
    ("apex_o1b_convex_incremental", "O1b CONVEX incremental",
     lambda O, x, m, s, c, t: O.o1b_convex(x, m, s, c, t), ("call",), "o1", False),
    ("apex_o2_leaps_apex", "O2 LEAPS-APEX", lambda O, x, m, s, c, t: O.o2_leaps(x, s, c, t), ("leap",), "cash", False),
    ("apex_o2b_leaps_incremental", "O2b LEAPS incremental", lambda O, x, m, s, c, t: O.o2b_leaps(x, s, c, t),
     ("leap",), "cash", False),
    ("apex_o10_leaps_vv", "O10 LEAPS + Variance Value",
     lambda O, x, m, s, c, t: O.o2b_leaps(x, s, c, t, with_variance_value=True), ("leap", "vv"), "cash", False),
    ("apex_o3_regime_putwrite", "O3 Regime put-write", lambda O, x, m, s, c, t: O.o3_putwrite(x, s, c, t), ("put",),
     "cash", False),
    ("apex_o4_phoenix", "O4 PHOENIX", lambda O, x, m, s, c, t: O.overlay(x, s, c, t, ("phoenix",)), ("phx",),
     "apex50f", False),
    ("apex_o5_chop_harvest", "O5 CHOP HARVEST", lambda O, x, m, s, c, t: O.overlay(x, s, c, t, ("chop",)), ("chop",),
     "apex50f", False),
    ("apex_o8_fear_put_spread", "O8 Fear put spread", lambda O, x, m, s, c, t: O.overlay(x, s, c, t, ("fear",)),
     ("fear",), "apex50f", False),
    ("apex_o9_omega", "O9 OMEGA", lambda O, x, m, s, c, t: O.overlay(x, s, c, t, ("phoenix", "chop", "fear")),
     ("phx", "chop", "fear"), "apex50f", False),
    ("apex_o11_apex_vv", "O11 APEX + Variance Value", lambda O, x, m, s, c, t: O.overlay(x, s, c, t, ("vv",)),
     ("vv",), "apex50f", False),
    ("apex_o6_variance_value", "O6 Variance Value", lambda O, x, m, s, c, t: O.o6_variance_value(x, s, c, t), ("vv",),
     "qqq", False),
    ("apex_o7_skew_risk_reversal", "O7 Skew risk reversal", lambda O, x, m, s, c, t: O.o7_skew_rr(x, s, c, t),
     ("rr",), "qqq", False),
    ("apex_o12_hybrid_leaps", "O12 Hybrid LEAPS/futures", lambda O, x, m, s, c, t: O.o12_hybrid(x, s, c, t),
     ("base",), "cash", True),
)


def sleeves():
    out = [OptionRow(sid, title, fn, tags, core, o12) for sid, title, fn, tags, core, o12 in ROWS_O]
    out.append(TailPuts("apex_e4_rolling_tail_puts", "E4 Rolling tail puts"))
    return out

