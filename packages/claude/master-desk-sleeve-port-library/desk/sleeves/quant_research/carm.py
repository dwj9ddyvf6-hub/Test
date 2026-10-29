"""qr_commitmentadjustedrecoverymemory -- CARM, Commitment-Adjusted Recovery Memory (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/carm: code/reference_kernel.py vendored
byte-exact under desk/vendor/quant_research/r10/carm/ and executed; PRACTICAL_PLAYBOOK.md).

The account (Capital): a declared 90% QQQ core, rebalanced monthly only while the sleeve is flat (drift retained
otherwise); the sleeve at most 10% of equity, 2 positions, 5% per name and per sector; settled cash only.

Episodes (Information / Features / Selection / Net Edge), from the registered shock-recovery episodes
(cache/qr_carm_registry.json: per episode the native lifecycle summaries of the frozen bid and ask bands -- added,
executed, cancelled, live and mature-live shares from first-received canonical order-ID events -- the anchors, and
the fitted lower / upper estimates: G_L, O_U, C_U, H, the paired increment, CPDW, plus the support counts):
  memory     reference_kernel.cohort_memory over the episode's events when supplied (else its summaries):
             commitment M = (E - C + L20) / A per side;
  admission  reference_kernel.admit(gross_lower, qqq_upper, incremental_lower, cost_upper >= 15 bp, overhead)
             -- both inequalities -- and CPDW > 5 bp, inside the 10:02-14:40 ET entry window, spread <= 4 bp;
  support    >= 500 training episodes over 100 dates and 60 calibration dates.
Execution: a marketable limit at the ask + one tick, 10-second life, size min(5% equity, the sleeve's room).
Exits, first of: the bid 40 bp under the average entry, the bid 60 bp over it, 30 minutes after the first fill, the
session close - 10 minutes; a 1% account daily loss blocks entries and liquidates the sleeve; 30-minute cooldown.

Removed gates: none beyond the playbook.

Named divergences:
  1. native Nasdaq order-ID data (full unfiltered ITCH-grade lifecycles with authenticated initial books and
     calibrated receipt clocks) has no free public source; the lifecycles and the fitted estimates are registered
     research inputs (the kernel's own caller-supplied interface). With none registered the account holds its QQQ
     core -- the playbook's abstention ("missing authentic initial book, full stream ...");
  2. execution: the desk's quotes; the 10-second IOC is a 10-second window on a marketable limit.

Parity: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json."""
from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from . import r10

SID = "qr_commitmentadjustedrecoverymemory"
SOURCE = r10.source("carm", "code/reference_kernel.py", "3a482c62bc79d92aac0d24bff1017f33d75cb11e", 213)
REGISTRY = "qr_carm_registry.json"
CORE = {"QQQ": 0.90}
SLEEVE_MAX, POSITIONS, NAME_MAX = 0.10, 2, 0.05
STOP_BP, TARGET_BP, HOLD_S, CLOSE_BUFFER_S, DAILY_LOSS, COOLDOWN_S = 40, 60, 30 * 60, 10 * 60, 0.01, 30 * 60
SPREAD_BP, CPDW_BP, COST_FLOOR_BP = 4.0, 5.0, 15.0
SUPPORT = {"train_episodes": 500, "train_dates": 100, "calibration_dates": 60}
WINDOW = ("10:02", "14:40")


def kernel():
    from ...vendor.quant_research.r10.carm.code import reference_kernel as K
    return K


def memory(ep):
    """the episode's bid-minus-ask commitment: the kernel's replay when its events are supplied, else the
    summaries' M = (E - C + L20) / A."""
    K = kernel()
    if ep.get("events"):
        r = K.cohort_memory(ep["events"], **ep["anchors"])
        return r["bid_minus_ask_commitment"]
    out = {}
    for side in ("B", "A"):
        s = ep["summary"][side]
        A = s["added"]
        out[side] = (s["executed"] - s["cancelled"] + s["mature_live"]) / A if A else None
    return out["B"] - out["A"] if out["B"] is not None and out["A"] is not None else None


def evaluate(ep, quote):
    """(admitted, reason) for one registered episode."""
    K = kernel()
    sup = ep.get("support") or {}
    if any(float(sup.get(k, 0)) < v for k, v in SUPPORT.items()):
        return False, "INSUFFICIENT_SUPPORT"
    try:
        m = memory(ep)
        e = ep["estimates"]
        ok = K.admit(gross_lower_bp=e["gross_lower_bp"], qqq_upper_bp=e["qqq_upper_bp"],
                     incremental_lower_bp=e["incremental_lower_bp"],
                     cost_upper_bp=max(COST_FLOOR_BP, e["cost_upper_bp"]), overhead_bp=e["overhead_bp"])
    except (ValueError, KeyError, TypeError, AssertionError) as exc:
        return False, "INVALID_INPUT: " + str(exc)[:80]
    if m is None:
        return False, "UNSUPPORTED_MEMORY"
    if not ok or float(ep["estimates"].get("cpdw_bp", 0)) <= CPDW_BP:
        return False, "NET_EDGE"
    b, a = quote.get("bid"), quote.get("ask")
    if not b or not a or (a - b) / ((a + b) / 2) * 1e4 > SPREAD_BP:
        return False, "SPREAD"
    return True, "ADMITTED"


class CARM(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=60, universe=("QQQ",), capital=1_000_000.0,
            schedule="rth", needs={"quotes": {"source": "equity"}},
            params={"core": CORE, "sleeve_max": SLEEVE_MAX, "positions": POSITIONS, "name_max": NAME_MAX,
                    "stop_bp": STOP_BP, "target_bp": TARGET_BP, "hold_s": HOLD_S, "support": SUPPORT,
                    "window": WINDOW, "spread_bp": SPREAD_BP},
            source=SOURCE, state_schema={"core": "dict", "episodes": "dict", "seen": "list", "day": "str",
                                         "day_nav": "float", "rebalanced": "str", "cooldown": "dict", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _registry(self):
        return r10.read_registry(getattr(self.engine, "root", None), REGISTRY)

    def quote_universe(self, now, book):
        names = {e["symbol"] for e in self._registry().get("episodes") or [] if e.get("symbol")}
        held = {i.split(":", 1)[1] for i in (book.positions or {}) if i.startswith("EQ:")}
        return sorted({"QQQ"} | names | held)

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("episodes", {}), ("seen", []), ("cooldown", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not r10.in_session(now, day):
            return []
        nav = C.nav(view)
        if st.get("day") != day:
            st.update(day=day, day_nav=nav)
        held = C.held(view)
        sleeve_open = [e for e in st["episodes"].values() if e["status"] in ("entering", "open")]
        month = day[:7]
        if not st.get("core") or (st.get("rebalanced", "")[:7] != month and not sleeve_open):
            q = ((view.quotes or {}).get("QQQ") or {}).get("ask")
            if q:                                              # the monthly core rebalance, sleeve flat
                st["core"] = {"QQQ": CORE["QQQ"] * nav / float(q)}
                st["rebalanced"] = day
        out = []
        loss = nav <= (1 - DAILY_LOSS) * float(st["day_nav"])
        hm = r10.hm(now)
        close = cal.session_close(day)
        for key, ep in list(st["episodes"].items()):
            sym = ep["symbol"]
            q = held.get(sym, 0.0)
            qt = (view.quotes or {}).get(sym) or {}
            if ep["status"] == "entering":
                if q > 0:
                    ep.update(status="open", qty=q, filled_at=now)
                elif now - ep["since"] > 10:
                    ep["status"] = "done"
            if ep["status"] == "open":
                bid = qt.get("bid")
                why = ("daily loss" if loss else
                       "stop -40bp" if bid and bid <= ep["avg"] * (1 - STOP_BP / 1e4) else
                       "target +60bp" if bid and bid >= ep["avg"] * (1 + TARGET_BP / 1e4) else
                       "30 minutes" if now - ep["filled_at"] >= HOLD_S else
                       "close - 10m" if now >= close - CLOSE_BUFFER_S else None)
                if why:
                    ep.update(status="exiting", why=why)
            if ep["status"] == "exiting":
                if q <= 1e-9:
                    ep["status"] = "done"
                    st["cooldown"][sym] = now
                else:
                    out.append(Intent("exit", sym, signal_key=f"carm:{key}:exit", reason=f"{SID} {ep['why']}",
                                      order=OrderSpec(type="market", window_s=600)))
        for key in [k for k, e in st["episodes"].items() if e["status"] == "done"]:
            st["episodes"].pop(key)
        reg = self._registry()
        if not loss and WINDOW[0] <= hm < WINDOW[1]:
            live = [e for e in st["episodes"].values() if e["status"] in ("entering", "open")]
            for ep in reg.get("episodes") or []:
                eid, sym = ep.get("episode_id"), ep.get("symbol")
                if not eid or eid in st["seen"] or len(live) >= POSITIONS:
                    continue
                if now - float(st["cooldown"].get(sym, 0)) < COOLDOWN_S or any(e["symbol"] == sym for e in live):
                    continue
                st["seen"] = (st["seen"] + [eid])[-500:]
                qt = (view.quotes or {}).get(sym) or {}
                ok, why = evaluate(ep, qt)
                st["log"] = (st["log"] + [{"at": day, "episode": eid, "decision": why}])[-100:]
                if not ok:
                    continue
                room = SLEEVE_MAX * nav - sum(e["qty"] * e["avg"] for e in live)
                notional = min(NAME_MAX * nav, room)
                if notional <= 0:
                    continue
                ask = float(qt["ask"])
                qty = notional / ask
                k = f"{eid}"
                st["episodes"][k] = {"symbol": sym, "status": "entering", "since": now, "qty": qty, "avg": ask}
                live.append(st["episodes"][k])
                out.append(Intent("enter", sym, side="long", qty=round(qty, 6), price_hint=ask,
                                  signal_key=f"carm:{k}:enter", reason=f"{SID} recovery memory {eid}",
                                  order=OrderSpec(type="limit", limit_price=round(ask + 0.01, 2), window_s=10)))
        tgt = {s: q for s, q in (st.get("core") or {}).items()}
        for e in st["episodes"].values():
            if e["status"] == "open":
                tgt[e["symbol"]] = e["qty"]
        busy = {i.symbol for i in out} | {e["symbol"] for e in st["episodes"].values()
                                         if e["status"] in ("entering", "exiting")}
        reb, _ = C.rebalance(view, tgt, f"carm:{st.get('rebalanced')}", f"{SID} QQQ core")
        return out + [i for i in reb if i.symbol not in busy]

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [CARM()]
