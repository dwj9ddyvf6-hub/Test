"""The forward lab's six accounts — midna_d_cyan_gbm, midna_w_cyan_quiet_tape, midna_w_cyan_mid_vix, midna_d_green_band,
midna_w_green_calm_smh, midna_w_cyan_high_adx — Midna's src/lib/equity/forward.ts (@ cursor/paper-desk-f184 68315288,
blob 125bda69) advanceForward ported line for line, one $20,000 account per FORWARD_SPEC, over the scan
(desk/sleeves/midna/forward_scan.py, the forward-scan.ts port; producer desk/feedlib/midna_forward.py).

  rules     gbm-1d-cyan    daily cyan fire scored by the frozen v4 trees >= the training 90th percentile; hold 21
            w-cyan-breadth weekly cyan, log10 dollar volume <= 6.92, weekly slow state bullish (2), basket breadth up
                           >= 0.037 over 10 sessions; hold 126
            w-cyan-vix     weekly cyan, dv <= 7.36, 126-session return >= 0.441, VIX 13.71..26.38; hold 252
            d-green-band   daily green, price $10..20, dispersion 0.021..0.029, 32..252 sessions since a 4% gap on 2.5x
                           volume; hold 21
            w-green-smh    weekly green, 63-session skew -0.680..0.472, SMH - SPY 63-session return -0.049..0.097, no
                           FOMC decision within the next five sessions; hold 126
            w-cyan-adx     weekly cyan, dv <= 7.35, 126-session return >= 0.445, weekly ADX >= 25.8; hold 126
            (liquid filter: last close >= $5 and 20-session mean dollar volume >= $1M; at most 6 hits per account,
            best GBM score / alphabetical)
  staging   when the panel's session has been scanned, the account's staged list is replaced by its hits on names it
            does not hold, up to its free slots (6 - open)
  entry     regular hours from 10:00 ET on a fresh panel, on the session right after the signal session (a row older
            than that is dropped): a free slot, a fresh quote (<= 15 min, <= 1 min ahead), qty = floor((20,000 / 6) /
            (px x (1 + cost bps))) with px = the ask (else last on the cost schedule) to the cent, capped by the cash
  exit      the first such pass once the sessions after the entry day through the panel's session reach the hold

Removed (cutover doctrine): green.ts buyBlockReason (QQQ red + VIX up + the name red: a desk-wide red-day gate);
entryBlock — the desk halt, VIX > 32, VIX +25% on the day, SPY 20-session < -8% with VIX rising, Friday from 14:00 ET,
the last five sessions of the year, FOMC day and the day before ("shared volatility / calendar / halt gates"); the 40%
adverse circuit breaker that closed the name and halted the account (a circuit breaker and a kill switch).

Named divergences: fills are engine children at the source's paper price (it booked them instantly), a working order
counts as done (common.virtual_book); one scan per session is cached for all six accounts (desk/feedlib/midna_forward.py);
the panel and the engine run as described in desk/feedlib/midna_panel.py and forward_scan.py."""
import math

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import common as M
from .context import panel_stale
from .forward_scan import FORWARD_SLOTS, FORWARD_SPECS

FORWARD_NAV = 20_000.0
SOURCE = {"repo": "midna", "ref": "cursor/paper-desk-f184", "commit": "68315288cb7af1340ee1a44cf446c6a9bb3e65fa",
          "path": "src/lib/equity/forward.ts", "blob": "125bda690205551c2a0aa9859d27f76d9d4859b9",
          "scan": {"path": "src/lib/equity/forward-scan.ts", "blob": "005059c60f7a"},
          "model": {"path": "quant-research/strategies/tensor_gbm_v4_1D_cyan_full.json",
                    "blob": "cda5b9b101c16c2ea2c8663614acfaef1fc60387"},
          "engine": {"path": "scripts/tensor/engine.mjs + engine-extra.mjs", "blobs": ["4d02997a7807", "b7295399e20b"]}}
REMOVED = ["green.ts buyBlockReason: QQQ red + VIX up + the name red (desk-wide red-day gate)",
           "entryBlock: desk halt, VIX > 32, VIX +25% day, SPY 20d < -8% with VIX rising, Friday >= 14:00 ET, "
           "last five sessions of the year, FOMC day and the day before (shared volatility / calendar / halt gates)",
           "40% adverse circuit breaker + account halt"]
IDS = {"gbm-1d-cyan": "midna_d_cyan_gbm", "w-cyan-breadth": "midna_w_cyan_quiet_tape", "w-cyan-vix": "midna_w_cyan_mid_vix",
       "d-green-band": "midna_d_green_band", "w-green-smh": "midna_w_green_calm_smh", "w-cyan-adx": "midna_w_cyan_high_adx"}


def stage(spec, hits, held, as_of):
    """advanceForward's staging for one account: its hits on names it does not hold, up to its free slots."""
    room = max(0, FORWARD_SLOTS - len(held))
    mine = sorted([h for h in hits if h["accountId"] == spec["id"] and h["sym"] not in held],
                  key=lambda h: (-(h["score"]) if h["score"] is not None else math.inf, h["sym"]))[:room]
    return [{"sym": h["sym"], "signalDay": as_of, "score": h["score"], "flag": h["flag"]} for h in mine]


def desired_qty(nav0, sym, px, schedule):
    dollars = nav0 / FORWARD_SLOTS
    if not dollars > 0 or not px > 0:
        return 0
    bps = M.context_cost_bps(sym, px) / 10_000 if schedule else 0
    return math.floor(dollars / (px * (1 + bps)))


def step(spec, account, now, quotes, panel, hits, nav0=FORWARD_NAV):
    """advanceForward for one account without the removed gates. account = {"cash", "positions": [{sym, qty, entryDay,
    holdSessions}] (open), "staged": [...], "scanned"}; mutated in place; returns the orders
    [{"side", "sym", "qty", "px", "reason"}]."""
    orders = []
    parts = M.et_parts(now)
    stale = panel_stale(panel, now)
    fill_ok = M.phase_at(now) == "rth" and parts["minutes"] >= 10 * 60
    can_price = fill_ok and not stale
    if panel and hits is not None and not stale:
        account["scanned"] = panel["asOf"]
        account["staged"] = stage(spec, hits, {p["sym"] for p in account["positions"]}, panel["asOf"])
    if can_price and panel:
        account["staged"] = [r for r in account["staged"] if M.trading_gap(r["signalDay"], parts["ymd"]) <= 1]
        still = []
        for row in account["staged"]:
            open_syms = {p["sym"] for p in account["positions"]}
            if M.trading_gap(row["signalDay"], parts["ymd"]) != 1 or row["sym"] in open_syms or \
                    len(account["positions"]) >= FORWARD_SLOTS:
                still.append(row)
                continue
            q = quotes.get(row["sym"])
            if not M.quote_is_fresh(q, now):
                still.append(row)
                continue
            px, schedule = M.priced(q, "buy")
            qty = desired_qty(nav0, row["sym"], px, schedule)
            if qty < 1:
                still.append(row)
                continue
            bps = M.context_cost_bps(row["sym"], px) / 10_000 if schedule else 0
            affordable = math.floor(account["cash"] / (px * (1 + bps)))
            if affordable < qty:
                qty = max(0, affordable)
            if qty <= 0:
                still.append(row)
                continue
            account["cash"] = M.round2(account["cash"] - qty * px - qty * px * bps)
            account["positions"].append({"sym": row["sym"], "qty": qty, "entryDay": parts["ymd"],
                                         "holdSessions": spec["holdSessions"], "signalDay": row["signalDay"],
                                         "score": row["score"], "flag": row["flag"], "schedule": schedule})
            orders.append({"side": "buy", "sym": row["sym"], "qty": qty, "px": px, "signalDay": row["signalDay"],
                           "flag": row["flag"], "score": row["score"]})
        account["staged"] = still
        for p in list(account["positions"]):
            q = quotes.get(p["sym"])
            if not M.quote_is_fresh(q, now):
                continue
            if M.sessions_after(p["entryDay"], panel["asOf"]) >= p["holdSessions"]:
                px, schedule = M.priced(q, "sell")
                bps = M.context_cost_bps(p["sym"], px) / 10_000 if schedule else 0
                account["cash"] = M.round2(account["cash"] + p["qty"] * px - p["qty"] * px * bps)
                account["positions"].remove(p)
                orders.append({"side": "sell", "sym": p["sym"], "qty": p["qty"], "px": px,
                               "reason": f"{p['holdSessions']}-session hold"})
    return orders


class ForwardAccount(Sleeve):
    def __init__(self, spec):
        self.spec = spec
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[spec["id"]], family="midna_tensor", cadence_s=300, capital=FORWARD_NAV, universe=(),
            schedule="always", needs={"quotes": {"source": "equity"}, "feeds": ["midna_panel", "midna_forward_scan"]},
            params={"account": spec["id"], "rule_id": spec["ruleId"], "hold_sessions": spec["holdSessions"],
                    "slots": FORWARD_SLOTS, "removed_gates": REMOVED},
            source=dict(SOURCE, account=spec["id"]),
            state_schema={"scanned": "str|None", "staged": "list", "pos": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book=None):
        held = [i[3:] for i in (book.positions if book else {}) if i.startswith("EQ:")]
        st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) if self.engine is not None else {}
        syms = held + [r["sym"] for r in (st or {}).get("staged") or []]
        if self.engine is not None and self.engine.feeds is not None:
            scan = self.engine.feeds.get("midna_forward_scan", self, now)
            syms += [h["sym"] for h in (scan or {}).get("hits") or [] if h["accountId"] == self.spec["id"]]
        return list(dict.fromkeys(syms))

    def signal(self, view):
        st = dict(view.state or {})
        panel = view.extra.get("midna_panel")
        scan = view.extra.get("midna_forward_scan")
        hits = None
        if scan and not scan.get("blocked") and panel and scan.get("asOf") == panel.get("asOf") and \
                st.get("scanned") != scan["asOf"]:
            hits = scan.get("hits") or []
        book, cash = M.virtual_book(view)
        rec = dict(st.get("pos") or {})
        positions = []
        for sym, p in book.items():
            r = rec.get(sym) or p["meta"] or {}
            positions.append({"sym": sym, "qty": p["qty"], "entryDay": r.get("entryDay") or M.et_ymd(view.now),
                              "holdSessions": int(r.get("holdSessions") or self.spec["holdSessions"]),
                              "signalDay": r.get("signalDay"), "score": r.get("score"), "flag": r.get("flag")})
        account = {"cash": cash, "positions": positions, "staged": list(st.get("staged") or []),
                   "scanned": st.get("scanned")}
        quotes = {}
        for sym in set(book) | {r["sym"] for r in account["staged"]} | {h["sym"] for h in (hits or [])}:
            q = M.mq(view.quotes.get(sym))
            if q:
                quotes[sym] = q
        orders = step(self.spec, account, view.now, quotes, panel, hits)
        out = []
        close = M.et_to_epoch(view.session, 0, 0) + M.session_close_minutes(view.session) * 60
        window = max(60.0, close - view.now)
        for o in orders:
            if o["side"] == "buy":
                pm = {"entryDay": M.et_ymd(view.now), "holdSessions": self.spec["holdSessions"],
                      "signalDay": o["signalDay"], "score": o["score"], "flag": o["flag"]}
                out.append(Intent("enter", o["sym"], qty=float(o["qty"]), price_hint=o["px"],
                                  signal_key=f"{self.spec['id']}:{o['sym']}:{o['signalDay']}:entry",
                                  reason=f"{self.spec['ruleId']} entry ({o['flag']})", order=OrderSpec(window_s=window),
                                  meta={"position_meta": pm}))
            else:
                out.append(Intent("exit", o["sym"], price_hint=o["px"], reason=o["reason"],
                                  signal_key=f"{self.spec['id']}:{o['sym']}:{view.session}:exit",
                                  order=OrderSpec(window_s=window)))
        keep = {p["sym"]: {k: p.get(k) for k in ("entryDay", "holdSessions", "signalDay", "score", "flag")}
                for p in account["positions"]}
        for sym in M.equity_positions(view):
            if sym not in keep and sym in rec:
                keep[sym] = rec[sym]
        st.update(scanned=account["scanned"], staged=account["staged"], pos=keep)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def sleeves():
    return [ForwardAccount(s) for s in FORWARD_SPECS]
