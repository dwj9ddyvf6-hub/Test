"""qr_auctionimpulseresponsetrading -- AIRT, Auction-Impulse Response Trading (quant-research-backup@d170596b
research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/airt: code/coordinator.py, the paper-research
coordinator, and code/vendor/airt_r1.py, its decision kernels, vendored byte-exact under
desk/vendor/quant_research/r10/airt/; airt_r1 executed; PRACTICAL_PLAYBOOK.md).

No core: the account is cash plus at most 4 positions, 40% stock gross, 25% per sector, 10% per initial name.

Each session, from the registered morning episodes (cache/qr_airt_registry.json: per symbol and session the frozen
09:35 detector inputs -- the opening displacement x0 (factor residual, bp), the volume and auction ratios v0 / a0,
the residual scale -- the two dose probes' paths x1 / x2, signed-flow fractions q1 / q2, impacts eta1 / eta2, VWAPs,
the spreads, the midpoint, the 20-day ADV and last-60-second dollars, the 1-minute sigma, the matured policy-label
records of the episode's cell):
  route       airt_r1.route(...): continuation or recovery (v0 >= 2, a0 >= 1.25, |x0| >= max(20 bp, 1.5 sigma0),
              second-probe spread <= 8 bp and <= 70% of the first, the route's flow / impulse / VWAP conditions);
  support     airt_r1.calibration(records of the cell): >= 200 earlier events over >= 60 session dates, the
              day-cluster mean and SE of the exact policy label;
  admission   airt_r1.expectancy_admitted: mean - 1.645 SE > 2 x round trip + 10 bp;
  size        airt_r1.size_shares (0.1% equity / d, 10% equity, 0.1% ADV, 2% of the last minute's dollars) inside
              airt_r1.portfolio_capacity (4 names, 40% gross, 25% sector, 10% name; no entry after a 0.5% session
              loss or a 5% peak drawdown), d = airt_r1.stop_distance(D, sigma1m).
Entry: a marketable limit capped at the decision ask + 2 bp, 90 seconds, one attempt per symbol and session, by the
09:50 probe deadline. Exits: airt_r1.exit_reason -- stop at entry x (1 - d), target at entry x (1 + 2d), the recovery
thesis when the residual reaches zero, 30 minutes after the first fill, flat by 15:45.

Removed gates: none beyond the playbook.

Named divergences:
  1. the detector's inputs need the official opening cross (price / shares / exchange receipts), SIP NBBO quotes with
     a source-unit contract and condition-coded trades for signing -- none has a free live source (the desk sees L1
     quotes and IEX-derived minute bars); the morning episodes are registered research inputs (the coordinator's own
     "source declarations are explicit research inputs"). With none registered the sleeve stays in cash;
  2. the recovery thesis exit reads the residual from the episode's registered betas and reference prices against
     the desk's live quotes (residual_bp);
  3. execution: the desk's quotes; the 90-second IOC refresh is a 90-second window on a capped limit.

Parity: tools/parity/qr_r10_kernels.py -> docs/receipts/parity/qr_r10_kernels.json."""
from datetime import datetime

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as C
from . import r10

SID = "qr_auctionimpulseresponsetrading"
SOURCE = r10.source("airt", "code/coordinator.py", "f49a25951d07597b08681d07ecd4e51f8d08794d", 658)
REGISTRY = "qr_airt_registry.json"
DEADLINE, FLAT = "09:50", "15:45"
CAP_BP, WINDOW_S = 2.0, 90


def kernel():
    from ...vendor.quant_research.r10.airt.code.vendor import airt_r1 as K
    return K


ROUTE_KEYS = ("x0", "x1", "x2", "v0", "a0", "scale", "spread0", "spread2", "q1", "q2", "eta1", "eta2", "midpoint",
              "vwap1", "vwap2")


def evaluate(ep, now):
    """(route, cell, detail) or (None, reason, {}) for one registered episode."""
    K = kernel()
    try:
        name = K.route(**{k: float(ep[k]) for k in ROUTE_KEYS})
        if name is None:
            return None, "NO_ROUTE", {}
        D = abs(float(ep["x0"]))
        c = K.cell(name, float(ep["v0"]), D, float(ep["scale"]))
        mean, se = K.calibration(ep.get("records") or [], now, ep.get("policy_sha"), c)
        rt = float(ep["expected_round_trip_bp"])
        if not K.expectancy_admitted(mean, se, rt):
            return None, "EXPECTANCY", {"mean": mean, "se": se}
        d = K.stop_distance(D, float(ep["sigma1m"]))
    except (K.EvidenceUnavailable, KeyError, TypeError, ValueError) as e:
        return None, "ABSTAIN: " + str(e)[:80], {}
    return name, c, {"d": d, "mean": mean, "se": se}


class AIRT(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=60, universe=(), capital=1_000_000.0,
            schedule="rth", needs={"quotes": {"source": "equity"}},
            params={"positions": 4, "gross": 0.4, "sector": 0.25, "name": 0.10, "deadline": DEADLINE,
                    "flat": FLAT, "cap_bp": CAP_BP, "window_s": WINDOW_S},
            source=SOURCE, state_schema={"positions": "dict", "attempts": "list", "day": "str", "day_nav": "float",
                                         "peak": "float", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def _registry(self):
        return r10.read_registry(getattr(self.engine, "root", None), REGISTRY)

    def quote_universe(self, now, book):
        day = cal._as_date(now).isoformat()
        names = {e["symbol"] for e in self._registry().get("episodes") or [] if e.get("session") == day}
        held = {i.split(":", 1)[1] for i in (book.positions or {}) if i.startswith("EQ:")}
        return sorted(names | held | {"SPY"})

    def signal(self, view):
        K = kernel()
        st = dict(view.state or {})
        for k, v in (("positions", {}), ("attempts", []), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not r10.in_session(now, day):
            return []
        nav = C.nav(view)
        if st.get("day") != day:
            st.update(day=day, day_nav=nav, attempts=[a for a in st["attempts"] if a.endswith(day)])
        st["peak"] = max(float(st.get("peak") or 0.0), nav)
        held = C.held(view)
        hm = r10.hm(now)
        flat_at = datetime.combine(cal._as_date(day), datetime.strptime(FLAT, "%H:%M").time(), r10.ET).timestamp()
        out = []
        for sym, p in list(st["positions"].items()):
            q = held.get(sym, 0.0)
            qt = (view.quotes or {}).get(sym) or {}
            if p["status"] == "entering":
                if q > 0:
                    p.update(status="open", first_fill=now, qty=q)
                elif now - p["since"] > WINDOW_S:
                    st["positions"].pop(sym)
                    continue
            if p["status"] == "open":
                bid = qt.get("bid")
                x = 0.0
                if p["route"] == "recovery" and p.get("ref"):
                    spy = ((view.quotes or {}).get("SPY") or {}).get("bid")
                    try:
                        x = K.residual_bp(bid / p["ref"]["stock"], spy / p["ref"]["market"], 1.0,
                                          p["ref"]["beta_market"], 0.0) if bid and spy else -1.0
                    except K.EvidenceUnavailable:
                        x = -1.0
                if bid:
                    why = K.exit_reason(bid, p["avg"], p["d"], now, p["first_fill"], p["route"],
                                        x if p["route"] == "recovery" else 0.0, flatten_at=flat_at)
                    if why:
                        p.update(status="exiting", why=why)
            if p["status"] == "exiting":
                if q <= 1e-9:
                    st["positions"].pop(sym)
                else:
                    out.append(Intent("exit", sym, signal_key=f"airt:{day}:{sym}:exit", reason=f"{SID} {p['why']}",
                                      order=OrderSpec(type="market", window_s=600)))
        if hm < DEADLINE:
            sectors = {}
            gross = 0.0
            for sym, p in st["positions"].items():
                gross += p["qty"] * p["avg"]
                sectors[p["sector"]] = sectors.get(p["sector"], 0.0) + p["qty"] * p["avg"]
            for ep in self._registry().get("episodes") or []:
                sym = ep.get("symbol")
                key = f"{sym}@{day}"
                if ep.get("session") != day or key in st["attempts"] or sym in st["positions"]:
                    continue
                qt = (view.quotes or {}).get(sym) or {}
                if not qt.get("ask"):
                    continue
                st["attempts"].append(key)                       # one attempt per symbol and session
                name, c, det = evaluate(ep, now)
                st["log"] = (st["log"] + [{"at": day, "symbol": sym, "decision": name or c}])[-100:]
                if not name:
                    continue
                cap = float(qt["ask"]) * (1 + CAP_BP / 1e4)
                try:
                    want = K.size_shares(nav, det["d"], float(ep["adv20"]), float(ep["observed_last60_dollars"]),
                                         float(qt["ask"]))
                    sec = ep.get("sector") or sym
                    sec_map = dict(sectors)
                    sec_map.setdefault(sec, 0.0)
                    qty = K.portfolio_capacity(equity=nav, available_cash=float(view.cash), gross_with_reservations=gross,
                                               sector_with_reservations=sec_map, occupied_names=len(st["positions"]),
                                               sector=sec, proposed_shares=int(want), price_cap=cap,
                                               session_return=nav / float(st["day_nav"]) - 1,
                                               peak_drawdown=1 - nav / float(st["peak"]))
                except K.EvidenceUnavailable as e:
                    st["log"] = (st["log"] + [{"at": day, "symbol": sym, "decision": "size: " + str(e)[:60]}])[-100:]
                    continue
                if qty < 1:
                    continue
                st["positions"][sym] = {"status": "entering", "since": now, "qty": qty, "avg": float(qt["ask"]),
                                        "route": name, "d": det["d"], "sector": sec, "ref": ep.get("reference")}
                gross += qty * cap
                sectors[sec] = sectors.get(sec, 0.0) + qty * cap
                out.append(Intent("enter", sym, side="long", qty=float(qty), price_hint=float(qt["ask"]),
                                  signal_key=f"airt:{key}:enter", reason=f"{SID} {name} cell {list(c)}",
                                  order=OrderSpec(type="limit", limit_price=round(cap, 4), cap_price=round(cap, 4),
                                                  window_s=WINDOW_S)))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [AIRT()]
