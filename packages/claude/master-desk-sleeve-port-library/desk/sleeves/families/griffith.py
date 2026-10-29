"""Griffith / Ledge three-strategy desk: Leaders Rest and Parallax, on the source's own decision and execution code.

The vendored, hash-pinned source modules (agentic-trading-desk main @4c8c179c, desk/vendor/griffith/) decide:
  strategy_system.py        LeadersRest.evaluate / Parallax.evaluate (the scanners);
  strategy_orchestrator.py  ThreeStrategyOrchestrator.evaluate: sector field sleeves, the Parallax regime and
                            cross-section benchmark returns, both versions of each scanner for every name;
  strategy_execution.py     ExecutionOverlays.build (LRX_1_0_0 / PXE_1_0_0 / PXE_1_1_0_AGGRESSIVE_PAPER plans) and
                            PortfolioAllocator.allocate (risk-per-trade sizing);
  config.json / universe.txt the runtime configuration and the frozen 552-name SCOPE universe.
This wrapper carries out agentic_runtime.run_three_strategies and drain_strategy_handoffs for one strategy:
  * Decision, once per trading day before the open (the source's premarket daily-discovery run): the orchestrator
    over the whole universe on the source's tape (feed griffith_iex_1d: Alpaca IEX raw daily bars, the last 550
    completed sessions). Plans for the strategy's champion version (LR_1_1_0_CORRECTED, PX_1_3_0_EXACT) and, for
    Parallax, the paper conditional-challenger lane (PX_1_3_0_CHALLENGER WAITs with engine COMPRESSION / DRIFT /
    RECLAIM / DISLOCATION and score >= 70, the 8 best per run, 0.5% risk, stop-limit above the market); in
    decision order (universe order, the source's), each plan is allocated and, with shares, armed as a handoff
    that expires with the plan (LR 5 days; PX 2 days, COMPRESSION 7; conditional 3, COMPRESSION 5).
  * Sizing = allocate(): min(risk fraction x equity [LR 0.5%, PX 0.35%, conditional 0.5%], the strategy cap 3% x
    equity - the strategy's open risk) / risk per share, and per order <= 35% of equity and <= 98% of buying power.
    Open risk is the source's: positions x (entry - stop) + working entries x (limit - stop) + armed handoffs'
    reserved risk + this run's earlier allocations. A held name is not added to.
  * Delivery, every regular-session pass (the 15-minute runtime cycle): a handoff is superseded when the name is
    held or the ask is at or below the plan stop, deferred while an entry is working on the name or no ask is
    quoted, else submitted: a GTC buy limit (stop-limit for COMPRESSION and the conditional lane) for the allocated
    shares, bracketed by the plan's stop-loss and take-profit.
Exits: the bracket only. The source's lifecycle plane (thesis break, 15-session non-positive time exit, breakeven,
trailing) is shadow except SHADOW_FULL_EXIT, and drain_lifecycle_exits defers that while any sell order reserves the
position — always, under a live bracket — so it never acts on these positions; it is not carried out here.

Gone under the cutover doctrine (per sleeve, both): the authoritative RiskGate on every entry (kill switch, the
SPY-only symbol allowlist that rejected every other name, $5,000 max order notional, buying-power check, $2,500
daily loss, 50% gross / 8% symbol exposure, signal age); the new-entry admission (operational SLO, command center,
database integrity, protection readiness); the desk allocator's portfolio terms (total risk 8%, symbol 2.5%,
sector 3%, gross notional 95%, the correlation multiplier, risk-truth admission, other strategies' ownership of a
name); the 30-position desk cap and its 8-slot Tensor reservation; the 12-claim hands budget per cycle.

Named divergences:
  * the tape is fetched once per session for the whole universe and the decision runs on the first pass of the
    trading day (premarket 07:00-09:25 ET, else the first session pass); the source's sharded run (4 x 138 names,
    one 30-minute cycle each) reached its decision about 90 minutes after its first premarket cycle — the same
    completed bars;
  * the planner's price input is the decision's reference close for every name (the source used it for every name
    outside its run's final shard; that shard's names carried their freshest IEX snapshot / 15-minute close);
  * buying power is the book's cash net of its working entries (the source read the shared Alpaca margin
    account's buying power);
  * the bracket legs are engine exit rules (stop / target on the mark, then a marketable exit) and a working GTC
    entry lives 90 days (Alpaca's GTC lifetime); positions, open risk and pending names are this sleeve's book."""
import importlib
import json
import math
import os
import sys
import types
from datetime import datetime, timezone

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import griffith as tape
from ...util import et_date

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "griffith")
VENDOR_NAMES = ("strategy_system", "validation_factory", "strategy_orchestrator", "strategy_execution",
                "r4_parallel_strategy_lab", "strategy_tournament")
SOURCE = {"repo": "agentic-trading-desk", "ref": "main", "commit": "4c8c179c5988d6e603c1f3c5f28f93e2344ca225"}
SOURCES = {
    "LEADERS_REST": dict(SOURCE, path="strategy_system.py", blob="4ab6c0aa939c26f88c7e34d9f8d2d86ac941cc92",
                         lines="126-176"),
    "PARALLAX": dict(SOURCE, path="strategy_system.py", blob="4ab6c0aa939c26f88c7e34d9f8d2d86ac941cc92",
                     lines="237-294")}
FEED = "griffith_iex_1d"
GTC_S = 90 * 86400
NEUTRAL = 1e12                       # a removed desk-wide allocator term never binds
PREFIX = {"PARALLAX": "px", "LEADERS_REST": "lr", "foliotend-location-first-swing": "lf",
          "TENSOR_PHENOTYPE_EXPERIMENTAL": "tx"}       # agentic_runtime drain_strategy_handoffs' client-id prefixes
KEEP_DONE_S = 10 * 86400
DECISION_KEYS = ("decisionId", "symbol", "scannerVersion", "status", "engine", "score", "asOf", "evidenceHash",
                 "entryReference")
_V = None


def vendored():
    """the pinned source modules. Each file's bare `from strategy_system import ...` resolves to the pin while the
    set loads; the bare names are not left behind in sys.modules."""
    global _V
    if _V is None:
        saved = {n: sys.modules.get(n) for n in VENDOR_NAMES}
        mods = {}
        try:
            for n in VENDOR_NAMES:
                mods[n] = importlib.import_module("desk.vendor.griffith." + n)
                sys.modules[n] = mods[n]
        finally:
            for n, m in saved.items():
                if m is None:
                    sys.modules.pop(n, None)
                else:
                    sys.modules[n] = m
        _V = types.SimpleNamespace(**mods)
    return _V


def source_config():
    return json.load(open(os.path.join(VENDOR, "config.json")))


def utc_iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def ts_of(iso_text):
    return datetime.fromisoformat(str(iso_text).replace("Z", "+00:00")).timestamp()


def stop_of(meta):
    for k, v in (meta or {}).get("exit_rules") or []:
        if k == "stop":
            return float(v)
    s = (meta or {}).get("stop")
    return float(s) if s is not None else None


def two(x):
    """the source's payload rendering f"{x:.2f}" back to a number."""
    return float(f"{float(x):.2f}")


def tensorx_price(item, quotes):
    """the price a TENSORX decision plans on (the owner's decision Q51, 2026-10-26). The live ask (or last) when this
    pass has one, as the source does for its SCOPE shard; else just under the trigger, so the plan waits for the break
    (a stop-limit at the event high, capped at the ceiling). The entry ceiling given as the price read every plan as
    already crossed: a limit at the ceiling that bought at once below the event high (HOPE and PFS on 2026-10-23)."""
    q = (quotes or {}).get(item.symbol) or {}
    live = float(q.get("ask") or q.get("last") or 0)
    if live > 0:
        return live
    trigger = float((item.metrics or {}).get("triggerPrice") or 0)
    return math.nextafter(trigger, 0.0) if trigger > 0 else float(item.entryReference or 0)


class ThreeStrategySleeve(Sleeve):
    """one strategy of the three-strategy desk (LEADERS_REST or PARALLAX) on its own book."""

    def __init__(self, sleeve_id, strategy):
        self.strategy = strategy
        cfg = source_config()
        self.three = cfg["three_strategy"]
        self.aggr = self.three.get("paper_aggressive_execution") or {}
        profile = dict(cfg["risk"]["paper_aggressive_profile"])
        profile.update(total_risk_fraction=NEUTRAL, symbol_risk_fraction=NEUTRAL, sector_risk_fraction=NEUTRAL,
                       gross_notional_fraction=NEUTRAL)
        self.profile = profile
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="griffith", cadence_s=int(cfg["agentic"]["cycle_seconds"]),
            universe=tuple(s for s in tape.universe() if s not in tape.ACCOUNTING_ONLY),
            needs={"feeds": [FEED], "quotes": {"source": "equity"}}, schedule="premarket,rth",
            params={"strategy": strategy, "champion": self.three["version_policy"]["champion_versions"][strategy],
                    "strategy_cap": self.profile["strategy_caps"][strategy],
                    "per_order_notional_fraction": self.profile["per_order_notional_fraction"]},
            source=SOURCES[strategy],
            state_schema={"decided": "str|None", "handoffs": "dict", "submitted": "dict"})

    # -- engine hooks --------------------------------------------------------------------------------------
    def bind(self, engine):
        self.engine = engine

    def _stored(self):
        if self.engine is None:
            return {}
        return self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}

    def wants_tape(self, now):
        """the tape loads only for the day's decision pass."""
        d = et_date(now)
        return cal.is_trading_day(d) and self._stored().get("decided") != d

    def quote_universe(self, now, book):
        st = self._stored()
        names = [i.split(":", 1)[1] for i, p in book.positions.items() if i.startswith("EQ:")]
        names += [h["symbol"] for h in (st.get("handoffs") or {}).values() if h.get("state") == "ARMED"]
        names += [r["symbol"] for r in (st.get("submitted") or {}).values()]
        return sorted(set(names))

    # -- decision ------------------------------------------------------------------------------------------
    @staticmethod
    def decisions(bars):
        """the orchestrator's decisions over the eligible universe (the source's evaluate call; Location-First,
        which needs 15-minute evidence, is not one of these sleeves)."""
        V = vendored()
        daily = {s: tape.raw_rows(bl) for s, bl in bars.items() if bl}
        eligible = [s for s in tape.universe() if s in daily and s not in tape.ACCOUNTING_ONLY]
        return V.strategy_orchestrator.ThreeStrategyOrchestrator().evaluate(eligible, daily, {}, {},
                                                                             location_symbols=set())

    @classmethod
    def tape_decisions(cls, t):
        """decisions memoised on the shared tape object (one orchestrator run serves both strategies)."""
        if t.get("_decisions") is None:
            t["_decisions"] = cls.decisions(t["bars"])
        return t["_decisions"]

    def open_risk(self, view, handoffs, submitted, now):
        """this strategy's open + reserved risk (portfolio_risk.calculate's byStrategy, on this book)."""
        risk = 0.0
        for inst, p in view.positions.items():
            q = float(p["qty"])
            stop = stop_of(p.get("meta"))
            if inst.startswith("EQ:") and q > 0 and stop:
                risk += q * max(0.0, float(p["avg"]) - stop)
        for po in view.extra.get("pending_orders") or []:
            rec = submitted.get(po.get("signal_key") or "")
            if rec and po.get("action") == "enter":
                risk += max(0.0, float(po["vqty"]) - float(po["filled_v"])) * (rec["limit"] - rec["stop"])
        for h in handoffs.values():
            if h["state"] == "ARMED" and h["expires_at"] > now:
                risk += float(h["allocation"]["reservedRisk"])
        return risk

    def buying_power(self, view, submitted):
        working = 0.0
        for po in view.extra.get("pending_orders") or []:
            rec = submitted.get(po.get("signal_key") or "")
            if rec and po.get("action") == "enter":
                working += max(0.0, float(po["vqty"]) - float(po["filled_v"])) * rec["limit"]
        return max(0.0, float(view.cash) - working)

    def plan_run(self, decisions, equity, buying_power, strategy_risk, held, now, quotes=None):
        """run_three_strategies' plan -> allocation -> handoff loop for this strategy: [(decision, plan, alloc)].
        quotes: this pass's live quotes, read by TENSORX decisions (tensorx_price)."""
        from dataclasses import asdict
        V = vendored()
        overlays = V.strategy_execution.ExecutionOverlays()
        allocator = V.strategy_execution.PortfolioAllocator(self.profile)
        clock = datetime.fromtimestamp(float(now), tz=timezone.utc)
        aggressive = bool(self.aggr.get("enabled", False))
        engines = {str(e).upper() for e in (self.aggr.get("conditional_engines") or [])}
        versions = {str(v) for v in (self.aggr.get("conditional_versions") or [])}
        min_score = float(self.aggr.get("conditional_min_score", 70))
        risk_fraction = float(self.aggr.get("conditional_risk_fraction", 0.005))
        max_plans = max(0, int(self.aggr.get("max_conditional_plans_per_cycle", 8)))
        candidates = [d for d in decisions if d.strategyId == "PARALLAX" and d.status == "WAIT"
                      and d.scannerVersion in versions and str(d.engine or "") in engines
                      and float(d.score or 0) >= min_score]
        allowed = {d.decisionId for d in sorted(candidates, key=lambda c: (-float(c.score or 0), c.symbol,
                                                                           c.decisionId))[:max_plans]} \
            if aggressive else set()
        champions = set((self.three.get("version_policy") or {}).get("champion_versions", {}).values())
        active = set(self.three.get("active_versions", []))
        out = []
        for item in decisions:
            if item.strategyId != self.strategy or item.scannerVersion not in active:
                continue
            quote = float(item.entryReference or 0)
            if item.strategyId == "TENSOR_PHENOTYPE_EXPERIMENTAL":
                quote = tensorx_price(item, quotes)
            plan = overlays.build(item, quote, equity, clock=clock,
                                  allow_conditional_wait=aggressive and item.decisionId in allowed,
                                  conditional_min_score=min_score, conditional_engines=engines,
                                  conditional_versions=versions, conditional_risk_fraction=risk_fraction)
            if not plan:
                continue
            conditional = "AUTHORIZED_PAPER_CONDITIONAL_WAIT" in plan.reasonCodes
            if champions and item.scannerVersion not in champions and not conditional:
                continue
            alloc = allocator.allocate(plan, equity, buying_power, open_risk=0.0, strategy_risk=strategy_risk,
                                       symbol_risk=0.0, sector_risk=0.0, gross_notional=0.0,
                                       existing_owner=None if item.symbol not in held else "EXTERNAL",
                                       max_order_notional=None, admission_allowed=True, correlation_multiplier=1.0)
            if alloc.authorizedQuantity > 0:
                strategy_risk += alloc.reservedRisk
                out.append((asdict(item), asdict(plan), asdict(alloc)))
        return out

    # -- delivery ------------------------------------------------------------------------------------------
    def entry_intent(self, h):
        d, plan, alloc = h["decision"], h["plan"], h["allocation"]
        sym = plan["symbol"]
        limit = two(plan["limitPrice"])
        trigger = two(plan["triggerPrice"]) if plan["orderType"] == "stop_limit" else None
        rules = [ExitRule("stop", two(plan["stopPrice"]))]
        if plan.get("targetPrice") is not None:
            rules.append(ExitRule("target", two(plan["targetPrice"])))
        cid = h["client_id"]
        return Intent("enter", sym, qty=float(int(alloc["authorizedQuantity"])), price_hint=limit,
                      order=OrderSpec(type="limit", limit_price=limit, stop_price=trigger, tif="gtc", window_s=GTC_S),
                      exit_rules=tuple(rules), signal_key=cid,
                      reason=f"{plan['overlayVersion']} {d['scannerVersion']} {d['status']} {sym} "
                             f"({','.join(plan['reasonCodes'])})",
                      meta={"plan": plan["planId"], "allocation": alloc["allocationId"], "decision": d["decisionId"],
                            "overlay": plan["overlayVersion"], "scanner": d["scannerVersion"],
                            "engine": d.get("engine"), "score": d.get("score")})

    def arm(self, triples, handoffs, now):
        """arm_handoff: one durable handoff per allocation (an allocation already known is ignored)."""
        created = utc_iso(now)
        for d, plan, alloc in triples:
            aid = alloc["allocationId"]
            if aid in handoffs:
                continue
            src_date = str(d.get("asOf") or created)[:10]
            handoffs[aid] = {"symbol": d["symbol"], "state": "ARMED", "created_at": created,
                             "expires_at": ts_of(plan["expiresAt"]), "plan": plan, "allocation": alloc,
                             "decision": {k: d.get(k) for k in DECISION_KEYS}, "reason": None,
                             "client_id": f"{PREFIX[self.strategy]}-{src_date}-{d['symbol']}-"
                                          f"{str(d['evidenceHash'])[:10]}-1"}
        return handoffs

    def deliver(self, view, handoffs, submitted, held, now):
        """drain_strategy_handoffs for this strategy's armed handoffs (creation order, then allocation id)."""
        intents = []
        pending = {po["inst"].split(":", 1)[1] for po in view.extra.get("pending_orders") or []
                   if po.get("action") == "enter" and po["inst"].startswith("EQ:")}
        for aid, h in sorted(handoffs.items(), key=lambda kv: (kv[1]["created_at"], kv[0])):
            if h["state"] != "ARMED":
                continue
            if h["expires_at"] <= now:
                h.update(state="EXPIRED", reason="PLAN_EXPIRED", at=now)
                continue
            sym = h["symbol"]
            if sym in held:
                h.update(state="SUPERSEDED", reason="POSITION_ALREADY_HELD", at=now)
                continue
            if sym in pending:
                h["reason"] = "BROKER_ORDER_ALREADY_PENDING"
                continue
            q = view.quotes.get(sym) or {}
            ask = float(q.get("ask") or q.get("last") or 0)
            if ask <= 0:
                h["reason"] = "FRESH_PRICE_UNAVAILABLE"
                continue
            if ask <= float(h["plan"]["stopPrice"]):
                h.update(state="SUPERSEDED", reason="INVALIDATED_BEFORE_ENTRY", at=now)
                continue
            if h["client_id"] in submitted:
                h.update(state="SUBMITTED", reason="EXISTING_LOCAL_ORDER_WITNESS", at=now)
                continue
            intents.append(self.entry_intent(h))
            submitted[h["client_id"]] = {"symbol": sym, "limit": two(h["plan"]["limitPrice"]),
                                         "stop": two(h["plan"]["stopPrice"]), "at": now}
            h.update(state="SUBMITTED", reason="BROKER_ACKNOWLEDGED", at=now)
            pending.add(sym)
        return intents

    def signal(self, view):
        st = dict(view.state or {})
        handoffs = {k: dict(v) for k, v in (st.get("handoffs") or {}).items()}
        now, session = float(view.now), view.session
        held = {i.split(":", 1)[1] for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"]) > 0}
        live = {po.get("signal_key") for po in view.extra.get("pending_orders") or []}
        submitted = {k: r for k, r in (st.get("submitted") or {}).items() if k in live or now - r["at"] < 3600}
        if cal.is_trading_day(session) and st.get("decided") != session:
            t = view.extra.get(FEED)
            bars = t.get("bars") if isinstance(t, dict) else None
            if bars:
                risk = self.open_risk(view, handoffs, submitted, now)
                triples = self.plan_run(self.tape_decisions(t), float(view.equity),
                                        self.buying_power(view, submitted), risk, held, now)
                self.arm(triples, handoffs, now)
                st["decided"] = session
                st["tape"] = {"session": t.get("session"), "names": len(bars), "missing": len(t.get("missing") or []),
                              "armed": len(triples)}
            elif isinstance(t, dict) and not t.get("skipped"):
                st["tape"] = {"error": "no bars", "session": session}
        intents = self.deliver(view, handoffs, submitted, held, now) if cal.is_rth(now) else []
        st["handoffs"] = {k: h for k, h in handoffs.items()
                          if h["state"] == "ARMED" or now - float(h.get("at") or now) < KEEP_DONE_S}
        st["submitted"] = submitted
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [ThreeStrategySleeve("griffith_leaders_rest", "LEADERS_REST"),
            ThreeStrategySleeve("griffith_parallax", "PARALLAX")]


# per asking sleeve: the feed answers each Griffith sleeve by its own wants_tape (the tape itself still loads once per
# final session, memoised on the hub). Memoised once per pass for every asker, the first asker's skip reached the whole
# pass: from 2026-10-20 the daily candidates and momentum-PEAD never saw the tape (roll call 2026-10-26).
FEEDS = {FEED: (tape.feed, {"per_sleeve": True})}
