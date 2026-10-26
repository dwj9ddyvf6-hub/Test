"""qr_contractqueuerevaluation -- CQR, Contract Queue Revaluation (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/cqr: queue_delta_r10.py vendored byte-exact
under desk/vendor/quant_research/r10/cqr/ and executed; PRACTICAL_PLAYBOOK.md).

The account (section 9): $1m in cash and stocks, at most 5% per issuer, 25% per sector, 15% per program cluster and
20 issuers, at least 5% cash; unallocated cash stays cash.

Decision (sections 5-7), at the 16:15 ET cutoff over the registered contract packets (cache/qr_cqr_registry.json:
the issuer's documented order book before and after the award -- each order's quantity, avoidable contribution per
unit, resource use per unit, mandatory flag and documented shortfall remedy -- the qualified resource capacity, the
uncounted collectible settlement, the issuer's market value and its registered OOF excess forecast; the matured
cluster history):
  revaluation  queue_delta_r10.paired_delta(before, after, capacity, settlement): both books re-optimised under the
               same physical capacity (the kernel's certified one-period LP); delta_usd / market value must be > 0;
  support      100 mature contract clusters, 20 issuers, 24 origin months (and 30 older OOF calibration clusters);
  economics    the registered excess forecast above full costs (max(15 bp, measured) per side) + 50 bp.
Entry (section 8): the next regular session 09:35-10:05 ET on observed quotes, whole shares, expiring 10:05. Exits
(section 9): 63 observed sessions, an observed 8% position loss, an adverse operative revision (the packet's
`revoked` flag); a 20% account loss liquidates and pauses entries for 20 sessions.

Removed gates: none beyond the playbook.

Named divergences:
  1. contract packets: no free public source publishes executed incorporated contracts with resource-month books and
     qualified capacity (USAspending.gov carries obligations, not the queue); the packets are registered research
     inputs (the kernel's caller-supplied interface). With none registered the account stays in cash -- the
     playbook's own abstention ("unknown operative quantity, qualified monthly capacity ... blocks entry");
  2. support: the registry's matured-cluster history plus this sleeve's own closed episodes;
  3. execution: the desk's quotes and marketable limits inside the 09:35-10:05 window.

Parity: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json."""
from datetime import timedelta

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from . import r10

SID = "qr_contractqueuerevaluation"
SOURCE = r10.source("cqr", "queue_delta_r10.py", "d5bd3f351158be899b1e9c0c07c72da8c76df76a", 148)
REGISTRY = "qr_cqr_registry.json"
MAX_ISSUER, MAX_SECTOR, MAX_CLUSTER, MAX_ISSUERS, MIN_CASH = 0.05, 0.25, 0.15, 20, 0.05
SUPPORT = {"episodes": 100, "issuers": 20, "months": 24}
COST_FLOOR, BUFFER, STOP_LOSS, ACCOUNT_STOP, PAUSE = 0.0015, 0.005, 0.08, 0.20, 20
HOLD = 63
ENTRY_FROM, ENTRY_TO = "09:35", "10:05"


def kernel():
    from ...vendor.quant_research.r10.cqr import queue_delta_r10 as K
    return K


def orders_of(rows):
    K = kernel()
    return [K.Order(r["name"], r["quantity"], r["contribution_usd_per_unit"], tuple(r["resource_per_unit"]),
                    bool(r["mandatory"]), r.get("shortfall_penalty_usd_per_unit")) for r in rows]


def evaluate(packet, history):
    """(admitted, reason, detail) for one registered contract packet."""
    K = kernel()
    try:
        d = K.paired_delta(orders_of(packet["before"]), orders_of(packet["after"]), packet["capacity"],
                           packet.get("settlement_usd", 0.0))
    except (ValueError, RuntimeError, KeyError, TypeError) as e:
        return False, "UNSUPPORTED_QUEUE", {"error": str(e)[:120]}
    rel = d["delta_usd"] / float(packet["market_value"])
    if not rel > 0:
        return False, "NONPOSITIVE_REVALUATION", {"delta_usd": d["delta_usd"]}
    sup = r10.support(history)
    if any(sup[k] < v for k, v in SUPPORT.items()) or int(packet.get("oof_calibration_clusters", 0)) < 30:
        return False, "INSUFFICIENT_SUPPORT", {"support": sup}
    cost = 2 * max(COST_FLOOR, float(packet.get("side_cost", 0.0)))
    f = packet.get("forecast_excess")
    if f is None or f <= cost + BUFFER:
        return False, "BELOW_COST_BUFFER", {"forecast": f, "cost": cost}
    return True, "ADMITTED", {"delta_usd": d["delta_usd"], "relative": rel}


class CQR(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=(), capital=1_000_000.0,
            schedule="rth", needs={"quotes": {"source": "equity"}},
            params={"max_issuer": MAX_ISSUER, "max_sector": MAX_SECTOR, "max_cluster": MAX_CLUSTER,
                    "max_issuers": MAX_ISSUERS, "min_cash": MIN_CASH, "support": SUPPORT, "hold": HOLD,
                    "stop_loss": STOP_LOSS, "account_stop": ACCOUNT_STOP, "entry": [ENTRY_FROM, ENTRY_TO]},
            source=SOURCE, state_schema={"episodes": "dict", "admitted": "dict", "matured": "list", "peak": "float",
                                         "pause_until": "str", "decided": "str", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _registry(self):
        return r10.read_registry(getattr(self.engine, "root", None), REGISTRY)

    def quote_universe(self, now, book):
        names = {p["symbol"] for p in self._registry().get("packets") or [] if p.get("symbol")}
        held = {i.split(":", 1)[1] for i in (book.positions or {}) if i.startswith("EQ:")}
        return sorted(names | held)

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("episodes", {}), ("admitted", {}), ("matured", []), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not r10.in_session(now, day):
            return []
        reg = self._registry()
        packets = {p["packet_id"]: p for p in reg.get("packets") or []}
        held = C.held(view)
        nav = C.nav(view)
        st["peak"] = max(float(st.get("peak") or 0.0), nav)
        out = []
        if st["peak"] and nav <= (1 - ACCOUNT_STOP) * st["peak"]:          # account loss: liquidate, pause entries
            st["pause_until"] = C.sessions_between(day, (cal._as_date(day) + timedelta(days=60)).isoformat())[PAUSE]
            st["peak"] = nav
            for s in held:
                out.append(Intent("exit", s, signal_key=f"cqr:{day}:{s}:account", reason=f"{SID} 20% account loss",
                                  order=OrderSpec(type="market", window_s=1800)))
            return out
        last = C.prev_session(day)
        if st.get("decided") != last and packets:
            history = list(reg.get("history") or []) + st["matured"]
            for pid, p in packets.items():
                if pid in st["admitted"] or any(e.get("packet_id") == pid for e in st["episodes"].values()):
                    continue
                ok, why, det = evaluate(p, history)
                st["log"] = (st["log"] + [{"at": last, "packet": pid, "decision": why}])[-100:]
                if ok:
                    st["admitted"][pid] = {"day": last}
        st["decided"] = last
        hm = r10.hm(now)
        for eid, ep in list(st["episodes"].items()):
            sym, q = ep["symbol"], held.get(ep["symbol"], 0.0)
            if ep["status"] == "entering":
                if q > 0:
                    ep.update(status="open", filled=day, qty=q)
                elif day > ep["since"] or hm >= ENTRY_TO:
                    ep["status"] = "lapsed"
            if ep["status"] == "open":
                bid = ((view.quotes or {}).get(sym) or {}).get("bid")
                p = packets.get(ep["packet_id"]) or {}
                why = ("63 sessions" if r10.sessions_since(ep["filled"], day) >= HOLD else
                       "8% loss" if bid and bid <= (1 - STOP_LOSS) * ep["avg"] else
                       "adverse revision" if p.get("revoked") else None)
                if why:
                    ep.update(status="exiting", why=why)
            if ep["status"] == "exiting":
                if q <= 1e-9:
                    ep["status"] = "closed"
                    st["matured"].append({"issuer": ep.get("issuer"), "group": ep.get("cluster"), "exit_session": day,
                                          "label": 0.0})
                else:
                    out.append(Intent("exit", sym, signal_key=f"cqr:{eid}:exit", reason=f"{SID} {ep['why']}",
                                      order=OrderSpec(type="market", window_s=1800)))
        for eid in [e for e, ep in st["episodes"].items() if ep["status"] in ("closed", "lapsed")]:
            st["episodes"].pop(eid)
        if ENTRY_FROM <= hm < ENTRY_TO and day >= (st.get("pause_until") or ""):
            live = [e for e in st["episodes"].values() if e["status"] in ("entering", "open")]
            for pid, adm in sorted(st["admitted"].items()):
                p = packets.get(pid)
                if not p or adm["day"] != last:
                    st["admitted"].pop(pid, None)                    # entry is the next session only
                    continue
                w_sector = sum(e["w"] for e in live if e.get("sector") == p.get("sector"))
                w_cluster = sum(e["w"] for e in live if e.get("cluster") == p.get("cluster"))
                w_all = sum(e["w"] for e in live)
                w = min(MAX_ISSUER, MAX_SECTOR - w_sector, MAX_CLUSTER - w_cluster, 1 - MIN_CASH - w_all)
                ask = ((view.quotes or {}).get(p["symbol"]) or {}).get("ask")
                if len(live) >= MAX_ISSUERS or w <= 0 or not ask:
                    continue
                qty = int(w * nav / float(ask))                           # whole shares
                if qty < 1:
                    continue
                eid = f"{pid}@{day}"
                st["episodes"][eid] = {"packet_id": pid, "symbol": p["symbol"], "issuer": p.get("issuer"),
                                       "sector": p.get("sector"), "cluster": p.get("cluster"), "w": w,
                                       "status": "entering", "since": day, "qty": qty, "avg": float(ask)}
                live.append(st["episodes"][eid])
                st["admitted"].pop(pid)
                out.append(Intent("enter", p["symbol"], side="long", qty=float(qty), price_hint=float(ask),
                                  signal_key=f"cqr:{eid}:enter", reason=f"{SID} queue revaluation {pid}",
                                  order=OrderSpec(window_s=max(60.0, cal.session_open(day) + 35 * 60 - now))))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [CQR()]
