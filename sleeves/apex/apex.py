"""APEX / Aurelia (Cursor2) — the research desk's 24 allocation sleeves (family "apex") on the engine.

Source: cursor2 main @ca8ac1f650670e1d — desk/strategies.py (APEX-NDX v1.0: the six-vote trend score x a
walk-forward HAR volatility forecast, the core variants, E1-E7, APEX-50F, v1.1), desk/inventions.py (N1-N7),
desk/round3.py (C1-C7), desk/options/* (the Variance Value sleeve of N7 / C7), each called as its research runner
called it (research/run_study.py, run_inventions.py, run_round3.py). The decision code is vendored in
desk/vendor/apex/ (byte-exact files and verbatim excerpts, re-hashed by the tests); desk/feedlib/apex.py feeds it
the source's own data (full Yahoo daily histories, the source's parse) and reads its answer. This module only
carries out the source runtime's execution obligations.

What runs (every sleeve: the decision on the last finished session t, held from the close of the next session t+1,
the source's "signal at the close of t, filled at the close of t+1"):
  apex_trend_har_tiers  APEX-50F (sigma 50%, L_max 4: the desk's live tier, desk/config.py LIVE_ID); the six tiers'
                        positions (APEX-20/25/30/40/50F/K) recorded with every decision
  apex_benchmarks       QQQ buy-and-hold (the benchmark of desk/strategies.py core_variants); the eight baselines'
                        positions (QQQ, BH2, BH3, SMA200-1x/3x, TREND-1x/3x, VOL-3x) recorded with every decision
  apex_v11_defensive_bond  APEX-50F with a 0.50 band; idle capital in 7-10y Treasuries (IEF) while their total
                        return is above its 200-day average, else T-bills (BIL)
  apex_e1..e7           APEX-30 with E1 (VIX/VIX3M > 1 halves it), E2 (Double-7 dip +0.5x), E3 (idle Treasuries),
                        E5 (a third of the exposure in SMH on semis' relative strength), E6 (+1x QQQ from the close
                        to the next open while the trend score is >= 0.5), E7 (+0.5x over the turn of the month)
  apex_n1..n6           Duration Shield, Silicon Switch (NDX or SOX/SMH), PRISM Classic / Paradigm (NDX, IEF, GLD,
                        USO, UUP / NDX, SMH, GLD, BTC), GESTALT, GESTALT x APEX
  apex_n7_omni          N1's core plus the Variance Value option sleeve on the whole book
  apex_c1..c6           AURELIA (QQQ + GC=F PRISM pair), Sector Kings, Follow-through, Broken Hedge (idle in the
                        most negatively correlated of IEF / GLD / UUP), REFLEX, Slingshot
  apex_c7_council       55% N6, 25% the gold trend sleeve (GLD), 20% Variance Value on a T-bill core
  apex_council_btc      the Council with Bitcoin (INVENTIONS_REPORT.md section 5): see its named divergence

Execution (the source desk's own live mapping, desk/agents/portfolio.py alpaca_weights, vendored): a Nasdaq-100
exposure L <= 1 is QQQ L + the idle asset; 1 < L <= 3 is QQQ + TQQQ with QQQ + 3 x TQQQ = L on 100% of the
capital; every other series is carried by the instrument whose total return it is (IEF, GLD, USO, UUP, SMH, the
sector ETFs, BTC/USD); idle capital sits in T-bills (BIL) unless the rule names another asset. Share targets =
floor(weight x the book's equity / the last finished close) (the source's PortfolioManager), sent market-on-close
(the source's ExecutionTrader: time_in_force "cls", submitted in the next session before the auction cutoff), one
frozen set per decision date; the book is re-synced to its targets every decision (the source re-derived the shares
from the planned exposure every run). Bitcoin trades on Alpaca crypto in the last ten minutes of the equity session.

Gone under the cutover doctrine: the Data Steward's block (stale or > 20% moves hold positions), the Compliance
Officer's block (path cap, instrument list, spec hash, ledger chain), the Alpaca path's 3x exposure cap, the
DESK_ALLOW_ORDERS / --execute staging; the shadow-only status of everything but APEX-50F.

Named divergences:
  * the book is the sleeve's own ($100,000, the source DeskChief's BASE_NAV; $1,000,000 for the option-carrying
    N7 / C7 / Council so whole contracts track the source's continuous units), sized on its equity (the source
    sized on its model NAV);
  * above 3x a Nasdaq exposure is TQQQ alone at L / 3 of the capital, the excess a margin debit (the Alpaca path
    capped at 3x; the futures path carried 4x), and any book whose instruments use more than its capital carries
    the debit at Alpaca's margin rate (the source modelled financing at the T-bill + 0.30-0.40%); costs are the
    engine's real-world schedule, not the source's modelled bps;
  * E6's boost is sold at the first pass of the next session's open window (the source's overnight return ran
    to the official open);
  * apex_council_btc: the report's "Bitcoin capped at 10% of risk" was never implemented by the source (C7, its
    implemented successor, dropped Bitcoin): the Bitcoin sleeve is N4's own PRISM Bitcoin sleeve (trend x min(1,
    20% / HAR vol), its 0.20 band) on 10% of the book, a 20%-vol unit as C7's gold sleeve is, and C7's components
    keep C7's 55/25/20 proportions on the remaining 90%;
  * the Variance Value legs are the listed QQQ monthly nearest the source's strike, whole contracts, priced at the
    natural (the source priced a continuous strike on its model surface at the close plus a modelled half-spread);
    the options' share is T-bills less the options it holds after the day's trades (at their marks, new contracts
    at the listed mid); the surface reads today's VXN / VIX family (Yahoo's, else CBOE's delayed quote, else the last
    close; the source read the same day's close).
Inputs: view.extra["apex"] (desk/feedlib/apex.py feed; the job apex_decisions computes it after each close so no
pass waits on it), view.extra["apex_live"] (the option context, in the pass: 1.5 s)."""
import json
import math
import os

from ... import calendar as cal
from ...contract import Intent, Leg, OrderSpec, Sleeve, SleeveConfig
from ...data.options import occ_parse, occ_symbol
from ...feedlib import apex as AF
from ...util import short_hash

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MARGIN_RATE = 0.0775 * 365 / 360          # Alpaca: debit x 7.75% / 360 per day (the engine's carry is / 365)
SCHEDULE = "rth&close-400:close-20"       # the next session, from the open until 20 minutes before the close
CADENCE = 1800
OPTION_SCHEDULE = "rth&close-45:close-15"  # the option decisions: the last hour before the auction cutoff
OPTION_CADENCE = 600
IDLE_OF = {"CASH": "BIL", "TSY": "IEF", "GOLD": "GLD", "DXY": "UUP"}


def manifest_rows(families):
    out = {}
    for line in open(os.path.join(ROOT, "config", "manifest", "sleeves.jsonl")):
        if line.strip():
            r = json.loads(line)
            if r.get("family") in families:
                out[r["sleeve_id"]] = r
    return out


ROWS = manifest_rows(("apex", "apex_options"))


# -- holdings ---------------------------------------------------------------------------------------------------
def ndx_weights(e):
    """the source's alpaca_weights for 0 < L <= 3 (idle part removed: the book's idle is computed once); above
    3x, TQQQ alone at L / 3 (a named divergence)."""
    from ...vendor.apex import agents as AG
    if e <= 0:
        return {}, 0.0
    if e <= 3.0:
        w = AG.alpaca_weights(e, "BIL")
        w.pop("BIL", None)
        return w, min(e, 1.0)
    return {"TQQQ": e / 3.0}, e / 3.0


def allocate(books, equity):
    """books [[fraction of equity, {asset: exposure}, idle]] -> {instrument: dollars}. Each sub-book holds its
    exposures on its own capital and keeps the rest in its idle asset; a sub-book using more than its capital
    runs a debit."""
    out = {}
    for b in books:
        frac, plan = float(b[0]), b[1] or {}
        idle = b[2] if len(b) > 2 and b[2] else "CASH"
        base = frac * float(equity)
        if base == 0:
            continue
        used = 0.0
        for asset, e in sorted(plan.items()):
            e = float(e)
            if e <= 0:
                continue
            if asset == "NDX":
                w, cap = ndx_weights(e)
                for s, x in w.items():
                    out[s] = out.get(s, 0.0) + x * base
                used += cap
            else:
                s = AF.INSTRUMENT[asset]
                out[s] = out.get(s, 0.0) + e * base
                used += e
        free = 1.0 - used
        if free > 1e-9:
            s = IDLE_OF.get(idle, "BIL")
            out[s] = out.get(s, 0.0) + free * base
    return out


def share_targets(dollars, px):
    """whole shares (floor, the source's PortfolioManager; a short toward zero); crypto to 1e-6."""
    out = {}
    for s, usd in dollars.items():
        p = px.get(s)
        if not p or p <= 0:
            raise RuntimeError(f"no finished close for {s}")
        q = usd / p
        sign = 1.0 if q >= 0 else -1.0
        if "/" in s:
            out[s] = sign * math.floor(abs(q) * 1e6) / 1e6
        else:
            out[s] = sign * float(math.floor(abs(q) + 1e-9))
    return out


def _held(view):
    out = {}
    for inst, p in view.positions.items():
        kind, sym = inst.split(":", 1)
        if kind in ("EQ", "CR"):
            out[sym] = float(p["qty"])
    return out


def _order(sym, session):
    if "/" in sym:                            # crypto: the last ten minutes of the equity session
        close = cal.session_close(session)
        return OrderSpec(type="marketable_limit", not_before=close - 600, not_after=close + 1800)
    return OrderSpec(type="market", tif="cls")


class ApexSleeve(Sleeve):
    """an exposure sleeve: the feed's plan for its exec session -> frozen share targets, market-on-close."""
    CAPITAL = 100_000.0

    def __init__(self, sid, title, capital=None, schedule=SCHEDULE, cadence=CADENCE, feeds=("apex",)):
        row = ROWS.get(sid) or {}
        self.title = title
        self.CONFIG = SleeveConfig(
            sleeve_id=sid, family=row.get("family", "apex"), cadence_s=cadence, universe=("QQQ",),
            capital=float(capital or self.CAPITAL), needs={"feeds": list(feeds)}, schedule=schedule,
            params={"margin_rate": MARGIN_RATE, "signal_id": AF.SIGNAL_ID},
            source=dict(row.get("source") or {}, vendored="desk/vendor/apex"),
            state_schema={"plan": "dict|None"})
        self._st = None

    # -- the decision ------------------------------------------------------------------------------------------
    def _obs(self, view, what, meta=None, key=None):
        return Intent("signal", "QQQ", reason=("%s %s" % (self.CONFIG.sleeve_id, what))[:300], meta=meta or {},
                      signal_key=key or "%s:%s:%s" % (self.CONFIG.sleeve_id, view.session, short_hash(what, n=8)))

    def _refused(self, view, err):
        """OPT-03's alert: a blocker (desk/learn/health.py raises blocked:<reason> when every evaluation has one)."""
        return Intent("signal", "QQQ", reason=("blocker: OPTION_INPUTS: %s" % err)[:300],
                      meta={"blocker": "OPTION_INPUTS", "why": str(err)[:300], "sleeve": self.CONFIG.sleeve_id},
                      signal_key="blk:option_inputs:%s:%s" % (self.CONFIG.sleeve_id, view.session))

    def books(self, d, view):
        """[[fraction, plan, idle]] of this decision (the feed's plan on the whole book by default)."""
        if d.get("books"):
            return [list(b) + ["CASH"] for b in d["books"]]
        return [[1.0, d.get("plan") or {}, d.get("idle") or "CASH"]]

    def extra_targets(self, d, view, targets, feed):
        return targets

    def pre(self, view, feed):
        """intents due before this session's decision (E6's boost sale at the open). Returns (intents, wait)."""
        return [], False

    def signal(self, view):
        self._st = dict(view.state or {})
        return self._decide(view)

    def _decide(self, view):
        sid = self.CONFIG.sleeve_id
        st = self._st
        feed = view.extra.get("apex") or {}
        if feed.get("error"):
            return [self._obs(view, "no decision: %s" % feed["error"], {"error": feed["error"]})]
        d = (feed.get("sleeves") or {}).get(sid)
        if not d or d.get("error"):
            err = (d or {}).get("error") or "no decision"
            return [self._obs(view, "no decision: %s" % err, {"error": err})]
        out, wait = self.pre(view, feed)
        if wait:
            return out
        as_of, ex = feed["as_of"], feed["exec"]
        if ex != view.session:
            return out + [self._obs(view, "decision of %s executes on %s, not %s: waiting" % (as_of, ex, view.session),
                                    {"as_of": as_of, "exec": ex})]
        plan = st.get("plan") or {}
        if plan.get("as_of") != as_of:                     # one frozen set of targets per decision date
            try:
                targets = share_targets(allocate(self.books(d, view), view.equity), feed["px"])
                targets = self.extra_targets(d, view, targets, feed)
            except RuntimeError as e:
                return out + [self._obs(view, "no targets: %s" % e, {"error": str(e)})]
            plan = {"as_of": as_of, "exec": ex, "targets": targets, "equity": float(view.equity),
                    "decision": {k: v for k, v in d.items() if k != "obs"}, "obs": d.get("obs")}
            st["plan"] = plan
        return out + self.exposure_intents(view, plan, feed["px"], feed.get("signals"))

    def exposure_intents(self, view, plan, px, signals=None):
        """the frozen share targets against the book (market-on-close; Bitcoin in the last ten minutes) + one
        record of the decision."""
        sid, as_of, out = self.CONFIG.sleeve_id, plan["as_of"], []
        held = _held(view)
        for sym in sorted(set(plan["targets"]) | set(held)):
            q = float(plan["targets"].get(sym, 0.0))
            if abs(q - held.get(sym, 0.0)) < 1e-9:
                continue
            out.append(Intent("target", sym, side="long" if q >= 0 else "short",
                              asset="crypto" if "/" in sym else "equity", qty=abs(q), price_hint=px.get(sym),
                              order=_order(sym, view.session), signal_key="%s:%s:%s" % (sid, as_of, sym),
                              reason="%s %s: %s -> %s %g (decided %s)" % (sid, self.title, _plan_str(plan), sym, q,
                                                                          as_of)))
        out.append(Intent("signal", "QQQ", reason=("%s decision %s for %s: %s" % (sid, as_of, plan["exec"],
                                                                                 _plan_str(plan)))[:300],
                          meta={"as_of": as_of, "exec": plan["exec"], "decision": plan.get("decision"),
                                "obs": plan.get("obs"), "targets": plan["targets"], "signals": signals},
                          signal_key="%s:%s:decision" % (sid, as_of)))
        return out

    def update_state(self, view, intents):
        return self._st


def _plan_str(plan):
    d = plan.get("decision") or {}
    if d.get("books"):
        return "books " + "; ".join("%.3f x %s" % (b[0], ",".join("%s %.3f" % kv for kv in sorted((b[1] or {}).items())))
                                    for b in d["books"])
    p = ", ".join("%s %.3f" % kv for kv in sorted((d.get("plan") or {}).items())) or "flat"
    return p + (" idle %s" % d["idle"] if d.get("idle") else "")


class OvernightBoost(ApexSleeve):
    """E6: the base APEX-30 book market-on-close, plus +1x QQQ bought at that close and sold at the next open."""

    def __init__(self, sid, title):
        super().__init__(sid, title, schedule="rth&close-60:close-20,!open+0:open+10", cadence=CADENCE)

    def pre(self, view, feed):
        st = self._st
        b = st.get("boost") or {}
        if not b.get("qty") or b.get("exec", "") >= view.session:
            return [], False
        if b.get("sold") == view.session or cal.minutes_to_close(view.now) is None:
            return [], False
        held = _held(view).get("QQQ", 0.0)
        mins = cal.minutes_to_close(view.now) or 0
        if mins < 60:                                  # the close window: the target re-syncs QQQ instead
            st["boost"] = dict(b, qty=0.0)
            return [], False
        q = min(float(b["qty"]), held)
        st["boost"] = dict(b, sold=view.session)
        if q <= 0:
            return [], True
        return [Intent("exit", "QQQ", qty=q, order=OrderSpec(type="marketable_limit", window_s=1800),
                       signal_key="%s:%s:boost-out" % (self.CONFIG.sleeve_id, b["exec"]),
                       reason="E6 overnight boost out at the open: %g QQQ bought at the close of %s" % (q, b["exec"]))], True

    def extra_targets(self, d, view, targets, feed):
        q = 0.0
        if float(d.get("boost") or 0.0) == 1.0:
            q = float(math.floor(1.0 * view.equity / feed["px"]["QQQ"] + 1e-9))
            targets = dict(targets, QQQ=targets.get("QQQ", 0.0) + q)
        self._st["boost"] = {"exec": feed["exec"], "qty": q, "as_of": feed["as_of"]}
        return targets


# -- the live option adapter -------------------------------------------------------------------------------------
def make_live_book():
    from ...feedlib.apex_book import make_live_book as mk
    from ...vendor.apex import sim as VS
    return mk(VS)


def run_source(call, steps, listing=None, legs_live=None, frames=None):
    """run a source options strategy with the Book replaced by a LiveBook bound to `steps`; returns the book."""
    from ...vendor.apex import opt_strategies as O, round3 as C
    LB = make_live_book()
    cls = type("BoundLiveBook", (LB,), {"STATE": {"steps": steps, "listing": listing, "legs_live": legs_live or []},
                                        "INSTANCES": []})
    with AF._LOCK:
        saved = O.Book, C.Book
        O.Book = C.Book = cls
        try:
            if frames is not None:
                with AF.bound(frames):
                    call(O, C)
            else:
                call(O, C)
        finally:
            O.Book, C.Book = saved
    if not cls.INSTANCES:
        raise RuntimeError("the source strategy built no book")
    return cls.INSTANCES[-1]


def legs_of(view, tags=None):
    """the sleeve's held option contracts in the source's Leg terms (units = contracts x 100, signed)."""
    out = []
    for inst, p in view.positions.items():
        if not inst.startswith("OPT:"):
            continue
        occ = inst[4:]
        root, exp, cp, k = occ_parse(occ)
        meta = p.get("meta") or {}
        pm = meta.get("position_meta") or {}
        tag = pm.get("tag") or "?"
        if tags is not None and tag not in tags:
            continue
        from datetime import date
        e = date.fromisoformat(exp)
        tf = AF.third_friday(e.year, e.month).isoformat()
        mark = p.get("mark") if p.get("mark") is not None else p.get("avg")
        out.append({"occ": occ, "is_call": cp == "call", "K": k, "tf": tf, "exp": exp,
                    "units": float(p["qty"]) * 100.0, "tag": tag, "group": meta.get("group"),
                    "mark": p.get("mark"), "px": float(mark or 0.0)})
    return out


def option_value(view, tags=None):
    return sum(l["units"] * l["px"] for l in legs_of(view, tags))


def value_after(view, tags, ops, listing=None):
    """the options' value once this decision is done (the source's Book core is the NAV less it, its trades
    included): the held contracts at their marks, less those the decision closes, plus its adjustments at the held
    mark and its new contracts at the listed quote's mid (the source's model price without a two-sided quote)."""
    held = {l["occ"]: l for l in legs_of(view, tags)}
    v = sum(l["units"] * l["px"] for l in held.values())
    quotes = (listing or {}).get("quotes") or {}
    for o in ops or ():
        leg = held.get(o.get("occ"))
        if o["op"] == "close" and leg:
            v -= leg["units"] * leg["px"]
        elif o["op"] == "adjust" and leg:
            v += float(o["delta"]) * leg["px"]
        elif o["op"] == "open":
            px = float(o.get("px") or 0.0)
            bid, ask = quotes.get(o.get("occ"), (None, None))
            if bid and ask and float(ask) >= float(bid) > 0:
                px = (float(bid) + float(ask)) / 2.0
            v += float(o["units"]) * px
    return v


MULTI = ("vv", "chop", "fear", "rr")
RATE_BOUNDS = (0.0, 0.15)   # OPT-03: the annual T-bill rates an option decision may be priced at
DELTA_GAP = 0.25            # OPT-03: the most a chosen contract's chain delta may differ from the model's


class OptionRefusal(RuntimeError):
    """an option decision refused on impossible inputs (OPT-03): no option order, a blocker on the record, nothing
    frozen (the next pass in the window decides again on fresh inputs)."""


def rate_of(live):
    """the annual T-bill rate the decision prices at: build_inputs' r on today's row (^IRX / 100)."""
    r = getattr((live or {}).get("x"), "r", None)
    return float(r[-1]) if r is not None and len(r) else None


def impossible_inputs(r, ops=(), book=None, chain=None):
    """OPT-03 (Edge audit 2026-10-25): why an option decision's inputs are impossible, else None. 2026-10-16 the T-bill
    rate read 40.7% (Cboe's IRX, the yield x 10): O2 / O2b / O10 / O12's 0.80-delta LEAP was struck at 842 and they
    bought the 840 call, 0.28 delta at the market, at a 13.5%-wide quote ($44.2k of half-spread). Refused: a rate
    outside RATE_BOUNDS, or a contract the decision opens whose chain delta differs from the model's delta of that
    contract (the source Book's quote at the decision) by more than DELTA_GAP, when both deltas are present."""
    if r is None or not math.isfinite(r) or not RATE_BOUNDS[0] <= r <= RATE_BOUNDS[1]:
        return "the T-bill rate %s is outside [%g, %g]" % ("unknown" if r is None else "%.4f" % r, *RATE_BOUNDS)
    if book is None:
        return None
    market = {row.get("symbol"): row.get("delta") for row in chain or ()}
    t = len(book.dates) - 1
    for o in ops or ():
        m = market.get(o.get("occ")) if o.get("op") == "open" else None
        if m is None:
            continue
        model = float(book.quote(t, bool(o["is_call"]), float(o["K"]), int(o["exp_i"]))[1])
        if math.isfinite(model) and abs(model - float(m)) > DELTA_GAP:
            return "%s: chain delta %.2f against the model's %.2f (more than %.2f apart)" % (o["occ"], float(m), model,
                                                                                            DELTA_GAP)
    return None


def ops_to_intents(sid, view, book, ops, listing, why):
    """the recorded source trades -> engine intents: a structure opened in one decision (vv / chop / fear / rr) is
    one package; single contracts are marketable option orders; closes of a whole held structure are one package
    naming its legs."""
    out = []
    session = view.session
    close_at = cal.session_close(session)
    opens = [o for o in ops if o["op"] == "open"]
    by_tag = {}
    for o in opens:
        by_tag.setdefault(o["tag"], []).append(o)

    def occ_of(o):
        exp = book._exp_iso(o["exp_i"])
        typ = "call" if o["is_call"] else "put"
        return listing["occ"].get((exp, typ, o["K"])) or occ_symbol("QQQ", exp, typ, o["K"]), exp

    for tag, legs in by_tag.items():
        meta_base = {"tag": tag, "source_rule": why}
        if tag in MULTI and len(legs) > 1:
            n = int(abs(legs[0]["units"]) / 100.0 + 0.5)
            ls = []
            pm = []
            for o in legs:
                occ, exp = occ_of(o)
                side = "buy" if o["units"] > 0 else "sell"
                ls.append(Leg(occ, side, 1, "buy_to_open" if side == "buy" else "sell_to_open"))
                pm.append({"occ": occ, "K_model": o["K_model"], "units_model": o["units_model"], "expiry": exp})
            key = "%s:%s:%s:open" % (sid, session, tag)
            out.append(Intent("enter", "QQQ", asset="mleg", qty=float(n), legs=tuple(ls),
                              order=OrderSpec(type="marketable_limit", not_after=close_at), signal_key=key,
                              reason="%s %s: open %s (%d legs x %d)" % (sid, why, tag, len(ls), n),
                              meta={"group": "%s:%s:%s" % (sid, session, tag), "underlying": "QQQ",
                                    "position_meta": dict(meta_base, legs=pm)}))
        else:
            for o in legs:
                occ, exp = occ_of(o)
                n = int(abs(o["units"]) / 100.0 + 0.5)
                out.append(Intent("enter", occ, side="long" if o["units"] > 0 else "short", asset="option",
                                  qty=float(n), order=OrderSpec(type="marketable_limit", not_after=close_at),
                                  signal_key="%s:%s:open:%s" % (sid, session, occ),
                                  reason="%s %s: open %s %s x %d" % (sid, why, tag, occ, n),
                                  meta={"underlying": "QQQ", "position_meta": dict(meta_base, K_model=o["K_model"],
                                                                                   units_model=o["units_model"],
                                                                                   expiry=exp)}))
    closes = [o for o in ops if o["op"] == "close" and o.get("occ")]
    held = {l["occ"]: l for l in legs_of(view)}
    groups = {}
    for o in closes:
        g = (held.get(o["occ"]) or {}).get("group")
        groups.setdefault(g, []).append(o)
    for g, cs in groups.items():
        members = [l for l in held.values() if g and l["group"] == g]
        if g and len(cs) > 1 and len(members) == len(cs):
            n = min(int(abs(o["units"]) / 100.0 + 0.5) for o in cs)
            legs = tuple(Leg(o["occ"], "sell" if o["units"] > 0 else "buy", 1,
                             "sell_to_close" if o["units"] > 0 else "buy_to_close") for o in cs)
            out.append(Intent("exit", "QQQ", asset="mleg", qty=float(n), legs=legs,
                              order=OrderSpec(type="marketable_limit", not_after=close_at),
                              signal_key="%s:%s:close:%s" % (sid, session, short_hash(*sorted(o["occ"] for o in cs), n=8)),
                              reason="%s %s: close %s" % (sid, why, cs[0]["tag"]), meta={"group": g, "underlying": "QQQ"}))
        else:
            for o in cs:
                n = int(abs(o["units"]) / 100.0 + 0.5)
                out.append(Intent("exit", o["occ"], side="long" if o["units"] > 0 else "short", asset="option",
                                  qty=float(n), order=OrderSpec(type="marketable_limit", not_after=close_at),
                                  signal_key="%s:%s:close:%s" % (sid, session, o["occ"]),
                                  reason="%s %s: close %s %s" % (sid, why, o["tag"], o["occ"])))
    for o in ops:
        if o["op"] != "adjust" or not o.get("occ"):
            continue
        n = int(abs(o["delta"]) / 100.0 + 0.5)
        long_leg = o["units_before"] > 0
        add = (o["delta"] > 0) == long_leg
        side = "long" if long_leg else "short"
        out.append(Intent("enter" if add else "exit", o["occ"], side=side, asset="option", qty=float(n),
                          order=OrderSpec(type="marketable_limit", not_after=close_at),
                          signal_key="%s:%s:adjust:%s" % (sid, session, o["occ"]),
                          reason="%s %s: adjust %s %+d contracts" % (sid, why, o["occ"], int(o["delta"] / 100.0)),
                          meta={"underlying": "QQQ", "position_meta": {"tag": o["tag"]}}))
    return out


class ApexOptionSleeve(ApexSleeve):
    """a sleeve whose decision includes source option trades: the exposure books market-on-close (as ApexSleeve)
    and the source's options decide() on the live book, once per session (frozen), sent before the close."""
    CAPITAL = 1_000_000.0

    def __init__(self, sid, title, capital=None, feeds=("apex", "apex_live")):
        super().__init__(sid, title, capital=capital, schedule=OPTION_SCHEDULE, cadence=OPTION_CADENCE, feeds=feeds)
        self._ops, self._listing = [], None

    # subclasses: option_call(live) -> (call(O, C), nav_share, tags, why); core_books(view, live, d) -> books
    def option_call(self, view, live, d):
        raise NotImplementedError

    def decide_options(self, view, live, d):
        st = self._st
        frozen = st.get("options") or {}
        if frozen.get("session") == view.session:
            return frozen
        call, nav, why, frames = self.option_call(view, live, d)
        held = legs_of(view, self.TAGS)
        step = {"legs_live": held, "nav": nav, "o12": (st.get("o12") or {"fut": 0.0, "wait_month": False})
                if getattr(self, "O12", False) else None}
        book = run_source(call, [step], listing=live["listing"], legs_live=held, frames=frames)
        ops = book.steps_out[-1] if book.steps_out else []
        bad = impossible_inputs(rate_of(live), ops, book, live.get("chain"))
        if bad:                                         # OPT-03: refused before anything is frozen or kept
            raise OptionRefusal(bad)
        intents = ops_to_intents(self.CONFIG.sleeve_id, view, book, ops, live["listing"], why)
        frozen = {"session": view.session, "ops": ops, "nav": nav,
                  "intents": [_intent_dict(i) for i in intents]}
        if book.o12_after is not None:
            st["o12"] = book.o12_after
        st["options"] = frozen
        return frozen


def _intent_dict(i):
    return {"kind": i.kind, "symbol": i.symbol, "side": i.side, "asset": i.asset, "qty": i.qty,
            "legs": [[l.symbol, l.side, l.ratio, l.position_intent] for l in i.legs],
            "order": {k: getattr(i.order, k) for k in ("type", "limit_price", "tif", "not_after", "not_before")}
            if i.order else None, "signal_key": i.signal_key, "reason": i.reason, "meta": i.meta}


def _intent_of(d):
    o = d.get("order")
    return Intent(d["kind"], d["symbol"], side=d["side"], asset=d["asset"], qty=d["qty"],
                  legs=tuple(Leg(*l) for l in d.get("legs") or []),
                  order=OrderSpec(**{k: v for k, v in o.items() if v is not None}) if o else None,
                  signal_key=d["signal_key"], reason=d["reason"], meta=d.get("meta") or {})


class VVSleeve(ApexOptionSleeve):
    """N7 / C7 / the Council: exposure books from the daily decision + the Variance Value sleeve on a share of the
    book (round3.variance_value_cash for C7 / Council, the overlay of run_inventions for N7)."""
    TAGS = ("vv",)

    def option_call(self, view, live, d):
        """N7: the overlay of research/run_inventions.py (sleeves ("vv",)) on the whole book; C7 / the Council: the
        Variance Value rule on its share of the book (round3.variance_value_cash runs the same
        opt_strategies._variance_value decide on a T-bill core, which here is the sleeve's BIL)."""
        from ...vendor.apex import sim as VS
        share = float(d.get("vv_share") or 1.0)
        nav = share * float(view.equity)
        x, surf = live["x"], live["surface"]
        start = len(x.dates) - 1
        if self.CONFIG.sleeve_id == "apex_n7_omni":
            def call(O, C):
                O.overlay(x, surf, VS.OptionCosts(mult=1.0), start, ("vv",))
            return call, nav, "N7 OMNI variance value", None

        def call(O, C):
            O.o6_variance_value(x, surf, VS.OptionCosts(mult=1.0), start)
        return call, nav, "COUNCIL variance value", None

    def books(self, d, view):
        """the decision's books; the options' share keeps as T-bills what its options (after today's trades) do not
        hold (round3.variance_value_cash: the Variance Value book on a T-bill core)."""
        v = value_after(view, self.TAGS, self._ops, self._listing) / float(view.equity) if view.equity else 0.0
        if d.get("books"):
            bs = [list(b) + ["CASH"] for b in d["books"]]
            bs[-1][0] = float(bs[-1][0]) - v                 # the options sleeve's T-bills: its share less its options
            return bs
        return [[1.0 - v, d.get("plan") or {}, d.get("idle") or "CASH"]]

    def signal(self, view):
        """the options' decision first (frozen per session), then the exposure books sized after it."""
        sid = self.CONFIG.sleeve_id
        self._st = dict(view.state or {})
        self._ops, self._listing = [], None
        live = view.extra.get("apex_live") or {}
        feed = view.extra.get("apex") or {}
        d = (feed.get("sleeves") or {}).get(sid) or {}
        opt = []
        if not live or live.get("error") or feed.get("error") or d.get("error") or not d:
            err = live.get("error") if live else "no option context"
            opt = [self._obs(view, "options: %s" % (err or "no decision"), {"error": err})]
        elif live.get("session") == view.session:
            try:
                fr = self.decide_options(view, live, d)
                self._ops, self._listing = fr["ops"], live.get("listing")
                opt = [_intent_of(x) for x in fr["intents"]]
                if fr["ops"]:
                    opt.append(Intent("signal", "QQQ", reason=("%s options %s: %s" % (
                        sid, view.session, "; ".join("%s %s" % (o["op"], o.get("tag")) for o in fr["ops"])))[:300],
                        meta={"ops": fr["ops"]}, signal_key="%s:%s:options" % (sid, view.session)))
            except OptionRefusal as e:                       # OPT-03; the exposure books still run
                opt = [self._refused(view, e)]
            except Exception as e:                           # the exposure books still run
                opt = [self._obs(view, "options error: %s: %s" % (type(e).__name__, str(e)[:160]),
                                 {"error": str(e)[:200]})]
        return self._decide(view) + opt


TITLES = {
    "apex_trend_har_tiers": "APEX-50F (trend x HAR vol, the live tier)",
    "apex_benchmarks": "QQQ benchmark (core variants recorded)",
    "apex_v11_defensive_bond": "APEX v1.1 (APEX-50F, band 0.50, idle Treasuries)",
    "apex_e1_vix_term_gate": "E1 VIX term-structure gate",
    "apex_e2_double7_dip": "E2 Double-7 dip overlay",
    "apex_e3_defensive_treasuries": "E3 defensive Treasuries",
    "apex_e5_semis_rs_tilt": "E5 semis relative-strength tilt",
    "apex_e6_overnight_boost": "E6 overnight boost",
    "apex_e7_turn_of_month": "E7 turn-of-month boost",
    "apex_n1_duration_shield": "N1 Duration Shield",
    "apex_n2_silicon_switch": "N2 Silicon Switch",
    "apex_n3_prism_classic": "N3 PRISM Classic",
    "apex_n4_prism_paradigm": "N4 PRISM Paradigm",
    "apex_n5_gestalt": "N5 GESTALT",
    "apex_n6_gestalt_apex": "N6 GESTALT x APEX",
    "apex_n7_omni": "N7 OMNI",
    "apex_c1_aurelia_pair": "C1 AURELIA pair",
    "apex_c2_sector_kings": "C2 Sector Kings",
    "apex_c3_follow_through": "C3 Follow-through",
    "apex_c4_broken_hedge": "C4 Broken Hedge",
    "apex_c5_reflex": "C5 REFLEX",
    "apex_c6_slingshot": "C6 SLINGSHOT",
    "apex_c7_council": "C7 COUNCIL",
    "apex_council_btc": "Council with Bitcoin",
}
VV_ROWS = ("apex_n7_omni", "apex_c7_council", "apex_council_btc")


def sleeves():
    out = []
    for sid, title in TITLES.items():
        if sid == "apex_e6_overnight_boost":
            out.append(OvernightBoost(sid, title))
        elif sid in VV_ROWS:
            out.append(VVSleeve(sid, title))
        else:
            out.append(ApexSleeve(sid, title))
    return out


def _live(feeds, sleeve, now, arg=None):
    return AF.live_context(feeds, sleeve, now, arg)


def _job(engine):
    """after each close: the 29 daily histories and the 24 decisions of the session just finished, written where the
    "apex" feed reads them, so no pass waits on the fetches or the computation (the feed still computes them itself
    when the job has not run). Idempotent per finished session: a later run the same evening returns at once."""
    return AF.job(engine.hub, engine.clock())


FEEDS = {"apex": AF.feed, "apex_live": _live}
JOBS = {"apex_decisions": ("weekday:12345&et:16:20-23:59", 1800, _job)}
