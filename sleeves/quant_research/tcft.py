"""qr_timecutflowtransport -- TCFT, Time-Cut Flow Transport (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/tcft: code/kernel.py and code/execution.py
vendored byte-exact under desk/vendor/quant_research/r10/tcft/ and executed; PRACTICAL_PLAYBOOK.md).

The account: held QQQ (the funded swap's donor) with at most 20% of NAV displaced into index-event stocks.

Formation (the 18:30 ET clock of session D, taken at the next session's first pass) over the registered index events
(cache/qr_tcft_registry.json: the announced constituent / float / weight change's original index target row, its
complete finite scenarios of owner lots -- DEMAND / SUPPLY shares, session slots, measurement kind, source hash --
with every registered allowance bounded, the security's price and ADV60, the binding endpoint session, the funded
net-advantage lower bound and the paired BASE increment, and the support counts):
  target_gate      execution.target_gate(target row, cutoff): original index target, clocks, identity, hash,
                   bounded allowances (any unbounded allowance is NO_TRADE);
  transport        kernel.finite_envelope(scenarios, cutoff): timed debt lower > 0 and time-cut gap lower > 0, then
                   price x gap_lower / ADV >= 0.1 and gap width / gap_upper <= 0.5;
  support          300 event clusters, 60 securities, 30 family calibration clusters, 5 training years;
  economics        the funded net lower bound >= 20 bp and the paired BASE increment > 0;
  breakers         no new entries after a 2% relative-to-QQQ or a 10% account drawdown.
Execution (the playbook's clock): D+1 09:45-10:00 the QQQ donor sale, D+2 09:45-10:00 the stock (marketable limit at
the ask + 3 bp, 15-minute timeout), sized min(4% NAV, 0.25% of ADV60 dollars, the remaining 20% budget); exit at the
binding endpoint's last ten-to-five minutes (15:50 ET); emergency exits on a 5% adverse bid (execution.risk_exit) or a
registered correction / vanished gap; QQQ restored at the next 09:45 window.

Removed gates: none beyond the playbook.

Named divergences:
  1. lots and allowances: the playbook's own audit finds no public source that bounds every intermediary allowance
     (PUBLIC_DATA_IDENTIFIABILITY_BOUNDS: a full bridge is always possible, so the public lower gap is zero); the
     scenarios are registered research inputs (the kernel's caller-supplied interface). With none registered the
     account holds QQQ -- the playbook's NO_TRADE_UNBOUNDED_MODEL_ALLOWANCE;
  2. support: registered counts plus this sleeve's own closed events;
  3. execution: the desk's quotes; the donor sale and the stock buy settle in the desk's paper book (no T+1 cash
     modelling), so the stock still waits for D+2 as the playbook orders.

Parity: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json (with the lane's 304 recorded
campaign cases replayed through the vendored kernel)."""
from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from . import r10

SID = "qr_timecutflowtransport"
SOURCE = r10.source("tcft", "code/kernel.py", "df9b493887c0be116ab3b9c7fddb4dbff706d9e7", 259)
REGISTRY = "qr_tcft_registry.json"
CORE = {"QQQ": 0.99}
NAME_CAP, ADV_CAP, BUDGET = 0.04, 0.0025, 0.20
GAP_ADV_MIN, WIDTH_MAX, NET_LCB_BP = 0.1, 0.5, 20.0
SUPPORT = {"clusters": 300, "securities": 60, "family_calibration": 30, "years": 5}
STOP, REL_DD, ACCT_DD = 0.05, 0.02, 0.10
WINDOW = ("09:45", "10:00")
EXIT_HM = "15:50"


def kernels():
    from ...vendor.quant_research.r10.tcft.code import execution as X
    from ...vendor.quant_research.r10.tcft.code import kernel as K
    return K, X


def scenarios_of(ev):
    K, _ = kernels()
    out = []
    for sc in ev.get("scenarios") or []:
        lots = tuple(K.Lot(l["lot_id"], l["owner_id"], l["security_id"], l["kind"], l["shares"], int(l["slot"]),
                           l["available_at"], l["measurement"], l["source_sha256"]) for l in sc["lots"])
        out.append(K.Scenario(sc["scenario_id"], lots, sc["model_allowances_complete"]))
    return tuple(out)


def evaluate(ev, cutoff):
    """(admitted, reason, detail) for one registered event at the formation cutoff (ISO, aware)."""
    K, X = kernels()
    g = X.target_gate(ev.get("target") or {}, cutoff)
    if g != "INPUT_SCHEMA_VALID_NOT_TRADE_AUTHORIZATION":
        return False, g, {}
    try:
        env = K.finite_envelope(scenarios_of(ev), cutoff, int(ev.get("max_carry_slots", 5)))
    except (ValueError, ArithmeticError, KeyError, TypeError) as e:
        return False, "INVALID_GRAPH", {"error": str(e)[:120]}
    if env["status"] != "MODEL_ENVELOPE_COMPUTED":
        return False, env["status"], {}
    sec = (env["securities"] or {}).get(ev["security_id"])
    if not sec or not sec["structural_candidate"]:
        return False, "NO_STRUCTURAL_GAP", {"security": sec}
    lo, hi = sec["time_cut_gap_lower_shares"], sec["time_cut_gap_upper_shares"]
    if float(ev["price"]) * lo / float(ev["adv60_dollars"]) < GAP_ADV_MIN or (hi - lo) / hi > WIDTH_MAX:
        return False, "GAP_TOO_SMALL_OR_WIDE", {"gap": [lo, hi]}
    sup = ev.get("support") or {}
    if any(float(sup.get(k, 0)) < v for k, v in SUPPORT.items()):
        return False, "INSUFFICIENT_SUPPORT", {"support": sup}
    if float(ev.get("net_lcb_bp", -1e9)) < NET_LCB_BP or float(ev.get("paired_base_lcb", -1)) <= 0:
        return False, "NET_OR_PAIRED_BOUND", {}
    return True, "ADMITTED", {"gap": [lo, hi]}


class TCFT(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=("QQQ",), capital=1_000_000.0,
            schedule="rth", needs={"quotes": {"source": "equity"}},
            params={"core": CORE, "caps": [NAME_CAP, ADV_CAP, BUDGET], "gap_adv_min": GAP_ADV_MIN,
                    "width_max": WIDTH_MAX, "net_lcb_bp": NET_LCB_BP, "support": SUPPORT, "stop": STOP,
                    "breakers": [REL_DD, ACCT_DD], "window": WINDOW, "exit": EXIT_HM},
            source=SOURCE, state_schema={"core": "dict", "episodes": "dict", "decided": "str", "peak": "float",
                                         "qqq0": "float", "nav0": "float", "rel_peak": "float", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _registry(self):
        return r10.read_registry(getattr(self.engine, "root", None), REGISTRY)

    def quote_universe(self, now, book):
        names = {e["symbol"] for e in self._registry().get("events") or [] if e.get("symbol")}
        held = {i.split(":", 1)[1] for i in (book.positions or {}) if i.startswith("EQ:")}
        return sorted({"QQQ"} | names | held)

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("episodes", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not r10.in_session(now, day):
            return []
        core = r10.CoreBook(st, CORE)
        if not core.seed(view):
            return []
        nav = C.nav(view)
        qqq = ((view.quotes or {}).get("QQQ") or {}).get("bid")
        st.setdefault("nav0", nav)
        if qqq:
            st.setdefault("qqq0", float(qqq))
        st["peak"] = max(float(st.get("peak") or 0.0), nav)
        rel = (nav / st["nav0"]) / (float(qqq) / st["qqq0"]) if qqq and st.get("qqq0") else 1.0
        st["rel_peak"] = max(float(st.get("rel_peak") or 0.0), rel)
        breaker = nav <= (1 - ACCT_DD) * st["peak"] or rel <= (1 - REL_DD) * st["rel_peak"]
        reg = self._registry()
        events = {e["event_id"]: e for e in reg.get("events") or []}
        last = C.prev_session(day)
        if st.get("decided") != last and events and not breaker:
            cutoff = r10.datetime.combine(cal._as_date(last), r10.datetime.strptime("18:30", "%H:%M").time(),
                                          r10.ET).isoformat()
            for eid, e in events.items():
                if any(ep["event_id"] == eid for ep in st["episodes"].values()):
                    continue
                ok, why, det = evaluate(e, cutoff)
                st["log"] = (st["log"] + [{"at": last, "event": eid, "decision": why}])[-100:]
                if ok:
                    st["episodes"][f"{eid}@{last}"] = {"event_id": eid, "symbol": e["symbol"], "status": "admitted",
                                                       "D": last, "endpoint": e["endpoint_session"]}
        st["decided"] = last
        hm = r10.hm(now)
        held = C.held(view)
        out = []
        _, X = kernels()
        in_window = WINDOW[0] <= hm < WINDOW[1]
        used = sum(float(ep.get("notional", 0.0)) for ep in st["episodes"].values()
                   if ep["status"] in ("funded", "entering", "open"))
        for key, ep in list(st["episodes"].items()):
            e = events.get(ep["event_id"]) or {}
            sym = ep["symbol"]
            if ep["status"] == "admitted":
                if r10.sessions_since(ep["D"], day) > 1:
                    ep["status"] = "lapsed"
                elif r10.sessions_since(ep["D"], day) == 1 and in_window:
                    px = ((view.quotes or {}).get(sym) or {}).get("ask") or e.get("price")
                    n = min(NAME_CAP * nav, ADV_CAP * float(e.get("adv60_dollars", 0.0)), BUDGET * nav - used)
                    if n > 0 and px:
                        donor = core.displace(view, {"QQQ": n / nav})
                        if donor is not None:
                            ep.update(status="funded", donor=donor, notional=n)
                            used += n
            elif ep["status"] == "funded" and r10.sessions_since(ep["D"], day) >= 2:
                ask = ((view.quotes or {}).get(sym) or {}).get("ask")
                if in_window and ask:
                    qty = ep["notional"] / float(ask)
                    ep.update(status="entering", qty=qty, avg=float(ask), since=day)
                    out.append(Intent("enter", sym, side="long", qty=round(qty, 6), price_hint=float(ask),
                                      signal_key=f"tcft:{key}:enter", reason=f"{SID} time-cut gap {ep['event_id']}",
                                      order=OrderSpec(type="limit", limit_price=round(float(ask) * 1.0003, 4),
                                                      window_s=900)))
                elif hm >= WINDOW[1]:
                    ep["status"] = "restoring"                    # no stock fill: restore the donor
            elif ep["status"] == "entering":
                if held.get(sym, 0.0) > 0:
                    ep.update(status="open", qty=held[sym])
                elif hm >= WINDOW[1] or day > ep["since"]:
                    ep["status"] = "restoring"
            if ep["status"] == "open":
                bid = ((view.quotes or {}).get(sym) or {}).get("bid")
                risk = X.risk_exit(ep["avg"], bid, missing=bid is None)
                why = ("endpoint" if (day > ep["endpoint"] or (day == ep["endpoint"] and hm >= EXIT_HM)) else
                       "5% adverse" if risk["action"] == "REQUEST_NEXT_OBTAINABLE_EXIT" else
                       "correction" if e.get("corrected") or e.get("gap_vanished") else None)
                if why:
                    ep.update(status="exiting", why=why)
            if ep["status"] == "exiting":
                if held.get(sym, 0.0) <= 1e-9:
                    ep["status"] = "restoring"
                else:
                    out.append(Intent("exit", sym, signal_key=f"tcft:{key}:exit", reason=f"{SID} {ep['why']}",
                                      order=OrderSpec(type="market", window_s=600)))
            if ep["status"] == "restoring" and hm >= WINDOW[0]:
                core.restore(ep.get("donor"))
                ep["status"] = "closed"
        for key in [k for k, ep in st["episodes"].items() if ep["status"] in ("closed", "lapsed")]:
            st["episodes"].pop(key)
        busy = {i.symbol for i in out} | {ep["symbol"] for ep in st["episodes"].values()
                                         if ep["status"] in ("entering", "exiting")}
        tgt = core.targets()
        for ep in st["episodes"].values():
            if ep["status"] == "open":
                tgt[ep["symbol"]] = float(ep["qty"])
        reb, _ = C.rebalance(view, tgt, f"tcft:{day}", f"{SID} QQQ core")
        return out + [i for i in reb if i.symbol not in busy]

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [TCFT()]
