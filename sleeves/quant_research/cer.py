"""qr_conjunctiveentitlementrepricing -- CER, Conjunctive Entitlement Repricing (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/cer: reference_kernel_r10.py vendored
byte-exact under desk/vendor/quant_research/r10/cer/ and executed; PRACTICAL_PLAYBOOK.md).

The account (playbook section 7): $1m reference capital, QQQ 49% / SPY 49% / cash 2%; each episode displaces 1% of
each index for a 2% stock position; at most 4 issuers, 8% of the sleeve in stocks, 4% per operator / buyer / region
cluster. No shorting, derivatives or borrowing.

Decision (section 5), at 16:15 ET each session over the registered projects (cache/qr_cer_registry.json: each
project's frozen AND graph of 1..8 required predicates, its horizon H in {21, 63}, the after / before equity-cash value
intervals and the dated equity value; the proofs with their publication / receipt / extraction / verification /
effective clocks; the matured-episode history):
  closure   reference_kernel_r10.closure(graph, proofs, prior 16:15, this 16:15): every required predicate TRUE now,
            not all TRUE at the prior snapshot, and a new usable TRUE proof in between;
  economics robust_conversion_screen(after, before, equity value) > 0 (None = unsupported economics: abstain);
  support   at least 100 matured episodes, 40 issuers, 10 operator-region groups and 36 months of labels;
  forecast  the registered net dual-index forecast above the 50 bp buffer.
Entry (section 6): the next session from 09:45 ET, the donor sale (1% QQQ, 1% SPY) and a limit buy at most 25 bp above
the offer; an admission expires after five sessions, an unfilled order after one session. Exits (section 8), first
trigger: H sessions from the first fill, a revoked required condition (a usable FALSE / conflicting proof), a 12%
loss on the observed bid; the donor is restored with the proceeds.

Removed gates: none beyond the playbook (no desk-wide gate applies).

Named divergences:
  1. proofs and project economics: no free public feed publishes adjudicated entitlement proofs or project
     equity-cash values; they are registered research inputs (the kernel's own interface: caller-supplied values) in
     the registry file. With none registered the account holds its funded core -- the playbook's own abstention
     ("all eight current discovery records remain blocked");
  2. support: the matured-episode history is the registry's plus this sleeve's own closed episodes;
  3. execution: the desk's quotes and marketable limits; the donor restoration rebuys the shares sold for the episode.

Parity: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json."""
from datetime import datetime, timedelta

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from . import r10

SID = "qr_conjunctiveentitlementrepricing"
SOURCE = r10.source("cer", "reference_kernel_r10.py", "c418bd076c972f986a3571cae2b1ff2348e86d39", 175)
REGISTRY = "qr_cer_registry.json"
CORE = {"QQQ": 0.49, "SPY": 0.49}
DONOR = {"QQQ": 0.01, "SPY": 0.01}
STOCK_W, MAX_ISSUERS, MAX_STOCKS, MAX_CLUSTER = 0.02, 4, 0.08, 0.04
SUPPORT = {"episodes": 100, "issuers": 40, "groups": 10, "months": 36}
BUFFER, STOP_LOSS, LIMIT_BPS = 0.005, 0.12, 25
DECIDE_HM, ENTRY_HM = "16:15", "09:45"
ADMISSION_SESSIONS = 5


def kernel():
    from ...vendor.quant_research.r10.cer import reference_kernel_r10 as K
    return K


def _dt(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def proofs_of(doc):
    K = kernel()
    out = []
    for p in doc.get("proofs") or []:
        out.append(K.Proof(p["project_id"], p["predicate_id"], p["origin_family"], p["body_sha256"], K.State(p["state"]),
                           _dt(p["published"]), _dt(p["received"]), _dt(p["extracted"]), _dt(p["verified"]),
                           _dt(p["effective_from"]), _dt(p["effective_until"]) if p.get("effective_until") else None))
    return tuple(out)


def graph_of(p):
    K = kernel()
    return K.Graph(p["project_id"], tuple(p["required"]), _dt(p["frozen_at"]), p["contract_sha256"])


def decision_time(day):
    return datetime.combine(cal._as_date(day), datetime.strptime(DECIDE_HM, "%H:%M").time(), r10.ET)


def evaluate(project, proofs, prior, cutoff, history):
    """(admitted, reason, detail) for one registered project at the cutoff."""
    K = kernel()
    try:
        g = graph_of(project)
        if not K.closure(g, proofs, prior, cutoff):
            return False, "NO_CLOSURE", {}
        after = K.Interval(*project["after"]) if project.get("after") else None
        before = K.Interval(*project["before"]) if project.get("before") else None
        screen = K.robust_conversion_screen(after, before, project["equity_value"])
    except (ValueError, KeyError, TypeError) as e:
        return False, "INVALID_INPUT", {"error": str(e)[:120]}
    if screen is None or screen <= 0:
        return False, "UNSUPPORTED_OR_NONPOSITIVE_ECONOMICS", {"screen": screen}
    sup = r10.support(history)
    if any(sup[k] < v for k, v in SUPPORT.items()):
        return False, "INSUFFICIENT_SUPPORT", {"support": sup}
    f = project.get("forecast_net")
    if f is None or f <= BUFFER:
        return False, "FORECAST_BELOW_BUFFER", {"forecast": f}
    return True, "ADMITTED", {"screen": screen, "support": sup}


def revoked(project, proofs, now_dt):
    K = kernel()
    try:
        snap = K.snapshot(graph_of(project), proofs, now_dt)
    except (ValueError, KeyError, TypeError):
        return False
    return any(v in (K.State.FALSE, K.State.CONFLICT) for v in snap.values())


class CER(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=("QQQ", "SPY"), capital=1_000_000.0,
            schedule="rth", needs={"quotes": {"source": "equity"}},
            params={"core": CORE, "donor": DONOR, "stock_weight": STOCK_W, "max_issuers": MAX_ISSUERS,
                    "max_stocks": MAX_STOCKS, "max_cluster": MAX_CLUSTER, "support": SUPPORT, "buffer": BUFFER,
                    "stop_loss": STOP_LOSS, "limit_bps": LIMIT_BPS, "decide": DECIDE_HM, "entry": ENTRY_HM},
            source=SOURCE, state_schema={"core": "dict", "episodes": "dict", "admitted": "dict", "matured": "list",
                                         "decided": "str", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _registry(self):
        return r10.read_registry(getattr(self.engine, "root", None), REGISTRY)

    def quote_universe(self, now, book):
        reg = self._registry()
        names = {p["symbol"] for p in reg.get("projects") or [] if p.get("symbol")}
        held = {i.split(":", 1)[1] for i in (book.positions or {}) if i.startswith("EQ:")}
        return sorted({"QQQ", "SPY"} | names | held)

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("admitted", {}), ("matured", []), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not r10.in_session(now, day):
            return []
        core = r10.CoreBook(st, CORE)
        if not core.seed(view):
            return []
        reg = self._registry()
        projects = {p["project_id"]: p for p in reg.get("projects") or []}
        proofs = proofs_of(reg) if reg else ()
        held = C.held(view)
        hm = r10.hm(now)
        out = []
        # the 16:15 decision (the regular session ends 16:00: the first pass after it is the next session's, which
        # decides for the prior session's 16:15 clock before anything else)
        last = C.prev_session(day)
        if st.get("decided") != last and projects:
            prior, cutoff = decision_time(C.prev_session(last)), decision_time(last)
            history = list(reg.get("history") or []) + st["matured"]
            for pid, p in projects.items():
                if pid in st["admitted"] or any(e.get("project_id") == pid for e in st["episodes"].values()):
                    continue
                ok, why, det = evaluate(p, proofs, prior, cutoff, history)
                st["log"] = (st["log"] + [{"at": last, "project": pid, "decision": why}])[-100:]
                if ok:
                    st["admitted"][pid] = {"day": last, "symbol": p["symbol"]}
        st["decided"] = last
        # episodes: fills, exits
        for eid, ep in list(st["episodes"].items()):
            sym = ep["symbol"]
            q = held.get(sym, 0.0)
            if ep["status"] == "entering":
                if q > 0:
                    ep.update(status="open", qty=q, filled=day)
                elif day > ep["since"]:                            # an unfilled order lapses after one session
                    core.restore(ep.get("donor"))
                    ep["status"] = "lapsed"
            if ep["status"] == "open":
                p = projects.get(ep["project_id"]) or {}
                bid = ((view.quotes or {}).get(sym) or {}).get("bid")
                why = None
                if r10.sessions_since(ep["filled"], day) >= int(ep["H"]):
                    why = f"H {ep['H']} sessions"
                elif bid and ep.get("avg") and bid <= (1 - STOP_LOSS) * ep["avg"]:
                    why = "12% loss"
                elif p and revoked(p, proofs, decision_time(day)):
                    why = "revoked condition"
                if why and hm >= ENTRY_HM:
                    ep.update(status="exiting", why=why)
            if ep["status"] == "exiting":
                if q <= 1e-9:
                    core.restore(ep.get("donor"))
                    ep["status"] = "closed"
                    st["matured"].append({"issuer": ep.get("issuer"), "group": ep.get("group"), "exit_session": day,
                                          "label": ep.get("label", 0.0)})
                else:
                    out.append(Intent("exit", sym, signal_key=f"cer:{eid}:exit", reason=f"{SID} {ep['why']}",
                                      order=OrderSpec(type="market", window_s=1800)))
        for eid in [e for e, ep in st["episodes"].items() if ep["status"] in ("closed", "lapsed")]:
            st["episodes"].pop(eid)
        # entries from 09:45 on the admitted projects (admission lives five sessions)
        if hm >= ENTRY_HM:
            open_eps = [e for e in st["episodes"].values() if e["status"] in ("entering", "open")]
            for pid, adm in sorted(st["admitted"].items()):
                p = projects.get(pid)
                if not p or r10.sessions_since(adm["day"], day) > ADMISSION_SESSIONS:
                    st["admitted"].pop(pid)
                    continue
                cluster_w = sum(STOCK_W for e in open_eps if e.get("group") == p.get("group"))
                if (len(open_eps) >= MAX_ISSUERS or STOCK_W * (len(open_eps) + 1) > MAX_STOCKS + 1e-12
                        or cluster_w + STOCK_W > MAX_CLUSTER + 1e-12):
                    continue
                qt = (view.quotes or {}).get(p["symbol"]) or {}
                ask = qt.get("ask")
                if not ask:
                    continue
                donor = core.displace(view, DONOR)
                if donor is None:
                    continue
                qty = STOCK_W * C.nav(view) / float(ask)
                eid = f"{pid}@{day}"
                st["episodes"][eid] = {"project_id": pid, "symbol": p["symbol"], "issuer": p.get("issuer"),
                                       "group": p.get("group"), "H": int(p.get("H", 21)), "status": "entering",
                                       "since": day, "qty": qty, "donor": donor, "avg": float(ask)}
                st["admitted"].pop(pid)
                open_eps.append(st["episodes"][eid])
                out.append(Intent("enter", p["symbol"], side="long", qty=round(qty, 6), price_hint=float(ask),
                                  signal_key=f"cer:{eid}:enter", reason=f"{SID} entitlement closure {pid}",
                                  order=OrderSpec(type="limit", limit_price=round(float(ask) * (1 + LIMIT_BPS / 1e4), 4),
                                                  window_s=max(60.0, cal.session_close(day) - now))))
        tgt = core.targets()
        for e in st["episodes"].values():                       # the episodes' own stock legs ride their intents
            if e["status"] in ("entering", "exiting"):
                tgt.pop(e["symbol"], None)
        busy = {i.symbol for i in out} | {e["symbol"] for e in st["episodes"].values()
                                           if e["status"] in ("entering", "exiting")}
        reb, _ = C.rebalance(view, tgt, f"cer:{day}", f"{SID} core")
        return out + [i for i in reb if i.symbol not in busy]

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [CER()]
