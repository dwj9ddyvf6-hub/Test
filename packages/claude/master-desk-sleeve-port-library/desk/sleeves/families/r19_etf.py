"""R19 ETF books (26) — Ausar frozen R17/R18 ETF rules (vendored r19_etf.py + etf_rules.json, hash-pinned).

The vendored `select()` chooses the leader (LEADER1 / DRIFT1 / CORE25 / EXSMH1 / INTERVAL*); this wrapper
carries out the book rules exactly as the original adapter does, without its receipt plumbing:
  * signal = the previous month's last completed session; scores = log(close[-1]/close[-127]) over the
    last 252 total-return closes; funds whose inception is after the 252-session window are ineligible;
  * execution only 09:35-09:40 ET, origin = first session of the month, retries within the first five
    sessions; no backfill of a missed origin, no backdated signal before installation; a fixed-weight book's
    initial allocation runs on its installation clock (r19_etf_data.book_clock: origin = the installation session,
    retries in the five sessions from it inside its month, signal = the session before; closed after them);
  * target units = floor(weight * gross * NAV / ask), NAV = cash - debt + unsettled sale proceeds + units at the
    bid; DRIFT keeps the incumbent's units; fixed-weight MONTHLY books size from prior closes; BUY_HOLD books
    allocate once and hold; a target the book cannot fund in full stays pending until its window closes;
  * each cycle executes as the source's (vendored r19_etf.py _evaluate, then r19_core.py Ledger._execute): sells
    first, each min(excess, displayed bid size); buys only once no sale is needed, each min(deficit, displayed ask
    size, budget / (ask x (1 + fee)), exposure / gross unit), a fixed-weight book's deficits scaled together by
    min(1, budget / cash needed, exposure / gross needed); budget = settled cash (+ an M150 book's margin credit,
    (gross - 1) x NAV - debt), exposure = gross x NAV - held value; then the ledger's caps on the book as the
    cycle's earlier fills left it: a cash book never pays more than its settled cash, fee included; 15 bps per
    side; M150 books carry 10%/yr debit;
  * sale proceeds settle T+1 (desk.feedlib.r19_ledger: the vendored settlement_terms, released at the first XNYS
    opening on or after maturity) and only then fund a buy: a rotation's buys wait for them;
  * quotes: the R19 cycle's own (feed r19_etf_quotes: the vendored r19_data.Collector.refresh_quotes, IEX latest
    quotes with displayed sizes, each bound to the asset census's contract id), qualified by the vendored _quotes
    (2-second clock, 20 bp spread, iex/sip feed, whole sizes, an active tradable contract) for every fund the cycle
    needs; a refused quote holds the cycle (retried on the next).
INTERVAL policies use two providers (Alpaca total-return closes + Yahoo adjusted closes).

Named divergences: the R19 worker cycled every 30 s and refreshed quotes per book once a second had passed; here one
refresh per 30 s pass serves all 26 books. A decided order goes to the desk's venue (marketable, 120 s window)
instead of the ledger's local fill at the quote; a pass that finds a child of the book still working decides nothing
until the venue acknowledges it, and units the venue left unexecuted come off the sale's claim. The ledger's
per-quote depth accounting is not kept: one order per fund per cycle, and a quote older than 2 s never qualifies,
so it cannot bind. Margin interest stays the desk's daily carry on a negative cash balance (the ledger accrued on its
debt); the ledger's gross-above-2 maintenance, its owned-contract check and its corporate-action / receipt
qualification are not carried."""
import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import r19_ledger as L
from ...feedlib.r19_book import reconcile
from ...vendor.ausar_r19 import r19_etf as ve

RULES = json.load(open(os.path.join(os.path.dirname(ve.__file__), "..", "strategies", "r19", "etf_rules.json")))
SOURCE = {"repo": "codex-complete-archive", "ref": "artifacts/ausar-corrected-incomplete-2026-10-11",
          "commit": "9de774739ab1fd05a9a93f238d50425d4ceda487",
          "path": "digitalocean-pilot/2026-10-11/context/source/backend/r19_etf.py",
          "blob": "eeaf26d324b9df0920d59c2e259d865ceb746205"}
UTC = timezone.utc
ZERO = Decimal(0)
FEED = "r19_etf_quotes"
FUNDS = sorted({s for c in RULES["sleeves"] for s in c["symbols"]})
CHILD_WINDOW_S = 120


def etf_quotes(feeds, sleeve, now, arg):
    """FEED r19_etf_quotes — the R19 cycle's equity quote refresh for its ETF books (r19_cli._cycle): the vendored
    r19_data.Collector.refresh_quotes over the ETF configs' funds (IEX latest quotes with displayed sizes), each
    bound to the asset census's native contract id (the collector's 6-hour census cache, shared with the timing
    books); one request per pass serves all 26 books."""
    from ...feedlib import r19_source as RS
    from .r19_timing import source_dir
    client = getattr(getattr(feeds.hub, "alpaca", None), "c", None)
    if client is None:
        return {"blocked": "R19_IEX_SOURCE_UNAVAILABLE: no Alpaca market-data client (credentials) on this desk"}
    m = RS.bind_clock(feeds.clock)
    col = RS.collector(source_dir(), client, feeds.clock)
    snap = {"asof": m["r19_core"].iso(), "quotes": {}, "provider_receipts": {}, "acquisition_errors": []}
    try:
        census = col._assets(m["r19_core"].stamp(snap["asof"]))["value"]
        snap["assets"] = {s: census[s] for s in FUNDS if s in census}
        snap["etf"] = {"asset_identities": {s: {"contract_id": a["id"]} for s, a in snap["assets"].items()
                                            if a.get("class") == "us_equity" and a.get("symbol") == s and a.get("id")}}
        col.refresh_quotes(snap, FUNDS)
    except Exception as exc:
        snap["acquisition_errors"].append(f"equity_quotes:{type(exc).__name__}:{exc}"[:300])
    return snap


FEEDS = {FEED: etf_quotes}


def month_sessions(d):
    """trading sessions of d's calendar month."""
    from datetime import date, timedelta
    d = cal._as_date(d)
    x = date(d.year, d.month, 1)
    out = []
    while x.month == d.month:
        if cal.is_trading_day(x):
            out.append(x.isoformat())
        x += timedelta(days=1)
    return out


def install_window(origin, n):
    """r19_etf_data.book_clock for an initial fixed allocation: n sessions from the installation session (the first
    session at or after it), cut at its month's end (no retry crosses a month)."""
    d = cal._as_date(origin)
    if not cal.is_trading_day(d):
        d = cal.next_trading_day(d)
    out = []
    while len(out) < n:
        out.append(d.isoformat())
        d = cal.next_trading_day(d)
    return [x for x in out if x[:7] == out[0][:7]]


def closes_tr(bars, before_session):
    """[(session, total-return close)] for bars of sessions strictly before `before_session`."""
    out = []
    for b in bars:
        s = cal._as_date(b["t"] + 6 * 3600).isoformat()
        if s < before_session:
            out.append((s, float(b.get("ac") or b["c"])))
    return out


def size(cfg, held, target, quotes, cash, debt, unsettled, nav, refused=()):
    """one cycle's orders -> ([(symbol, side, quantity, price)], [decided orders on refused funds]), as the source
    decided and then executed them. Decided (vendored r19_etf.py _evaluate): sells first, each min(excess, displayed
    bid size); buys only when no sale is needed, each min(deficit, displayed ask size, budget / (ask x (1 + fee)),
    exposure / gross unit), a fixed-weight book's deficits scaled together by min(1, budget / cash needed, exposure /
    gross needed); budget = settled cash (+ the margin credit (gross - 1) x NAV - debt of a gross > 1 book), exposure =
    gross x NAV - held value, both spent down by each decided buy. Executed (r19_core.py Ledger._execute): each buy
    also capped by the ledger book as the cycle's earlier fills left it (re-marked at the bid): settled cash (+ the
    margin credit of a margin book) at price x (1 + fee), and gross capacity; a decided order on a `refused` fund (the
    ledger's execution clock) does not fill. quotes: {fund: (bid, ask, bid size, ask size)}; cash / debt / unsettled /
    nav: Decimal."""
    gross, fee = Decimal(str(cfg["gross_target"])), Decimal(str(cfg["cost_bps_per_side"])) / 10000
    needed = sorted(set(held) | set(target))
    held_value = sum((Decimal(q) * quotes[s][0] for s, q in held.items()), ZERO)
    out, skipped = [], []
    for s in needed:
        q = min(max(0, held.get(s, 0) - target.get(s, 0)), quotes[s][2])
        if q:
            (skipped if s in refused else out).append((s, "sell", q, quotes[s][0]))
    if any(held.get(s, 0) > target.get(s, 0) for s in needed):
        return out, skipped
    budget = max(ZERO, cash)
    if gross > 1:
        budget += max(ZERO, nav * (gross - 1) - debt)          # the ledger book's margin_credit_remaining
    exposure = max(ZERO, gross * nav - held_value)
    scaled = None
    if cfg["fixed_weights"]:
        deficits = {s: min(max(0, target.get(s, 0) - held.get(s, 0)), quotes[s][3]) for s in needed}
        cash_needed = sum((Decimal(q) * quotes[s][1] * (1 + fee) for s, q in deficits.items()), ZERO)
        gross_needed = sum((Decimal(q) * (gross * quotes[s][1] + (1 - gross) * quotes[s][0] + gross * fee * quotes[s][1])
                            for s, q in deficits.items()), ZERO)
        scale = min(Decimal(1), budget / cash_needed if cash_needed else Decimal(1),
                    exposure / gross_needed if gross_needed else Decimal(1))
        scaled = {s: ve._floor(Decimal(q) * scale) for s, q in deficits.items()}
    margin = bool((cfg.get("margin") or {}).get("enabled"))
    g = gross if margin else min(Decimal(1), gross)
    lcash, ldebt, lheld = cash, debt, dict(held)
    for s in needed:
        bid, ask, _, ask_size = quotes[s]
        unit = gross * ask + (1 - gross) * bid + gross * fee * ask
        q = min(scaled[s] if scaled is not None else max(0, target.get(s, 0) - held.get(s, 0)), ask_size,
                max(0, ve._floor(budget / (ask * (1 + fee)))), max(0, ve._floor(exposure / unit)))
        if not q:
            continue
        budget -= q * ask * (1 + fee)
        exposure -= q * unit
        if s in refused:
            skipped.append((s, "buy", q, ask))
            continue
        value = sum((Decimal(n) * quotes[x][0] for x, n in lheld.items()), ZERO)
        lnav = lcash - ldebt + unsettled + value
        afford = max(ZERO, lcash) + (max(ZERO, (g - 1) * lnav - ldebt) if margin else ZERO)
        q = min(q, ve._floor(afford / (ask * (1 + fee))),
                ve._floor(max(ZERO, g * lnav - value) / (g * ask + (1 - g) * bid + g * ask * fee)))
        if q <= 0:
            continue
        cost = q * ask + q * ask * fee
        spend = min(max(ZERO, lcash), cost)
        lcash, ldebt = lcash - spend, ldebt + cost - spend
        lheld[s] = lheld.get(s, 0) + q
        out.append((s, "buy", q, ask))
    return out, skipped


class R19Etf(Sleeve):
    def __init__(self, cfg):
        self.rule = cfg
        sid = cfg["id"].lower()
        two = cfg["secondary_provider"] is not None
        bars = [{"source": "equity", "interval": "1d", "n": 300, "symbols": list(cfg["symbols"])}]
        if two:
            bars.append({"source": "yahoo", "interval": "1d", "n": 300, "symbols": list(cfg["symbols"]), "key": "yahoo"})
        self.CONFIG = SleeveConfig(
            sleeve_id=sid, family="r19_etf", cadence_s=30, universe=tuple(cfg["symbols"]),
            capital=float(cfg["initial_capital"]), schedule="open+5:open+10",
            needs={"bars": bars, "feeds": [FEED]},
            params={"cost_bps": cfg["cost_bps_per_side"], "margin_rate": cfg["margin"]["annual_interest"],
                    "gross": cfg["gross_target"], "policy": cfg["policy"]},
            source=dict(SOURCE, config_id=cfg["id"]),
            state_schema={"pending": "dict|None", "incumbent": "str|None", "last_completed_signal": "str|None",
                          "initial_done": "bool", "ledger": "dict", "inflight": "dict"})

    def _scores(self, bars_by_sym, signal_session, before):
        funds = RULES["funds"]
        out = {}
        for sym in self.rule["symbols"]:
            rows = closes_tr(bars_by_sym.get(sym) or [], before)
            if not rows or rows[-1][0] != signal_session:
                continue                                   # history must end exactly at the signal session
            tail = rows[-252:]
            if len(tail) < 252:
                if funds.get(sym, {}).get("inception", "0000") > rows[0][0]:
                    continue                               # post-inception funds legitimately ineligible
                continue
            if funds.get(sym, {}).get("inception", "0000") > tail[0][0]:
                continue
            c = [x[1] for x in tail]
            if any(v <= 0 for v in c):
                continue
            out[sym] = math.log(c[-1] / c[-127])
        return out

    def _note(self, reason, key, **meta):
        return Intent("signal", self.CONFIG.universe[0], reason=reason[:200], meta=meta, signal_key=key[:80])

    def signal(self, view):
        cfg = self.rule
        st = dict(view.state or {})
        st.setdefault("initial_done", False)
        model = st["ledger"] = st.get("ledger") or L.fresh()
        inflight = st["inflight"] = st.get("inflight") or {}
        self._st = st
        held = {i.split(":", 1)[1]: int(round(float(p["qty"]))) for i, p in view.positions.items()
                if i.startswith("EQ:") and float(p["qty"]) > 0}
        working = {p["inst"].split(":", 1)[1]: p for p in view.extra.get("pending_orders") or []}
        reconcile(model, inflight, {s: {"quantity": str(q)} for s, q in held.items()}, working)
        L.release(model, view.now)                          # matured sale proceeds become settled cash
        session = view.session
        sessions = month_sessions(session)
        allowed = sessions[:int(cfg["max_pending_sessions"])]
        fixed = cfg["fixed_weights"]
        pending = st.get("pending")
        if pending and session > pending["allowed"][-1]:
            st["last_completed_signal"] = pending["signal"]
            st["pending"] = pending = None
            st["initial_done"] = True
        if cfg["frequency"] == "BUY_HOLD" and st["initial_done"] and not pending:
            return []
        signal_session = cal.prev_trading_day(sessions[0]).isoformat()
        selected, weights, initial_fixed = None, {}, False
        if not pending:
            initial_fixed = bool(fixed) and not st["initial_done"]
            if not initial_fixed:
                if session != allowed[0] or st.get("last_completed_signal") == signal_session:
                    return []                                 # no backfill of a missed monthly origin
                if st.get("installed_at") and st["installed_at"] >= signal_session:
                    return []                                 # no backdated pre-install signal
            else:                                             # the installation clock (book_clock): its own window
                allowed = install_window(st.get("installed_at") or session, int(cfg["max_pending_sessions"]))
                signal_session = cal.prev_trading_day(allowed[0]).isoformat()
                if session > allowed[-1]:                     # the window elapsed without a target: closed
                    st["initial_done"] = True
                    return []
                if session != allowed[0]:                     # its origin passed without a target: no backfill
                    return []
            if fixed:
                weights = {s: Decimal(str(w)) for s, w in fixed.items()}
            else:
                daily = view.bars.get("1d") or {}
                own = self._scores(daily, signal_session, sessions[0])
                other = self._scores(view.extra.get("bars_yahoo") or {}, signal_session, sessions[0]) \
                    if cfg["secondary_provider"] else None
                try:
                    selected, _ = ve.select(cfg["policy"], own, other, st.get("incumbent"))
                except ValueError as e:
                    return [Intent("signal", "QQQ", reason=f"blocked: {e}", meta={"blocker": str(e)})]
                weights = {selected: Decimal(1)}
                if cfg["policy"].endswith("CORE25"):
                    weights = {selected: Decimal(".25")}
                    weights["QQQ"] = weights.get("QQQ", ZERO) + Decimal(".75")
        snap = view.extra.get(FEED) or {}
        if snap.get("blocked"):
            return [self._note(snap["blocked"], "blk:" + snap["blocked"][:40], blocker=snap["blocked"])]
        if working or not snap.get("asof"):
            return []                                         # the venue acknowledges this book's last decision first
        now = ve._utc(snap["asof"])
        opened = cal.session_open(session)
        if not opened + 300 <= now.timestamp() < opened + 600:
            return []                                         # r19_etf._calendar: the 09:35-09:40 execution window
        needed = sorted(set(held) | set(weights) | set((pending or {}).get("target") or {}))
        try:                                                  # every fund the cycle needs, as the source qualified it
            quotes, _ = ve._quotes(snap, None, needed, now, (snap.get("etf") or {}).get("asset_identities") or {}, cfg)
        except (KeyError, ValueError, TypeError, ArithmeticError) as e:
            b = str(e)
            return [self._note(f"blocker: {b}", f"blk:{b[:40]}:{session}", blocker=b[:300])]
        unsettled = L.unsettled(model)
        settled = Decimal(repr(float(view.cash))) - unsettled
        cash, debt = max(ZERO, settled), max(ZERO, -settled)
        nav = settled + unsettled + sum((Decimal(q) * quotes[s][0] for s, q in held.items()), ZERO)
        if nav <= 0:
            return [self._note("blocker: NONPOSITIVE_NAV", f"blk:nav:{session}", blocker="NONPOSITIVE_NAV")]
        gross = Decimal(str(cfg["gross_target"]))
        if not pending:
            retain = cfg["policy"] in ("DRIFT1", "INTERVAL_DRIFT1") and selected == st.get("incumbent") and \
                held.get(selected, 0) > 0 and st["initial_done"]
            if fixed and cfg["frequency"] == "MONTHLY" and not initial_fixed:
                daily = view.bars.get("1d") or {}
                prior = {s: (closes_tr(daily.get(s) or [], sessions[0]) or [(None, None)])[-1][1] for s in needed}
                if any(not prior.get(s) for s in needed):
                    return []
                prior = {s: Decimal(str(p)) for s, p in prior.items()}
                pnav = settled + unsettled + sum((Decimal(q) * prior[s] for s, q in held.items()), ZERO)
                desired = {s: ve._floor(weights.get(s, ZERO) * gross * pnav / prior[s]) for s in needed}
            else:
                desired = {s: held.get(s, 0) if retain else ve._floor(weights.get(s, ZERO) * gross * nav / quotes[s][1])
                           for s in needed}
            pending = st["pending"] = {"signal": signal_session, "allowed": allowed, "selected": selected,
                                       "target": desired}
            st["incumbent"] = selected
        target = {s: int(t) for s, t in pending["target"].items()}
        if all(held.get(s, 0) == target.get(s, 0) for s in set(held) | set(target)):
            st.update(pending=None, initial_done=True, last_completed_signal=pending["signal"])
            return []
        actual = now.timestamp() + 0.001                     # the ledger's acknowledgement, after the snapshot
        late = {s for s in needed if actual - ve._utc(snap["quotes"][s]["market_at"]).timestamp() >
                float(cfg["max_quote_age_seconds"])}         # Ledger._execute: snapshot replay forbidden
        sid = ve.digest({"book": cfg["id"], "signal": pending["signal"], "target": target, "asof": snap["asof"]})
        decided, skipped = size(cfg, held, target, quotes, cash, debt, unsettled, nav, refused=late)
        intents = [self._note(f"{s}: {side} {q}: Actual execution clock exceeds fresh quote; snapshot replay forbidden",
                              f"gate:{s}:late:{session}", gate="late_quote") for s, side, q, _ in skipped]
        for s, side, q, px in decided:
            oid = L.order_id(cfg["id"], cfg, sid, s, side)
            release = None
            if side == "sell":
                try:
                    terms = L.settlement_terms(datetime.fromtimestamp(actual, tz=UTC))
                except ValueError as e:
                    intents.append(self._note(f"{s}: {e}", f"gate:{s}:settlement", gate=str(e)[:200]))
                    continue
                release = ve._utc(terms["cash_release_at"]).timestamp()
                fee = q * px * Decimal(str(cfg["cost_bps_per_side"])) / 10000
                model["unsettled"].append({"amount": str(q * px - fee), "release_at": release, "order": oid,
                                           "qty": str(q)})
            inflight.setdefault(s, []).append({"symbol": s, "side": side, "quantity": str(q),
                                               "before": str(held.get(s, 0)), "order_id": oid, "depth_key": None,
                                               "release_at": release})
            meta = {"cost_bps": float(cfg["cost_bps_per_side"]), "signal_id": sid, "decided_qty": str(q),
                    "order_id": oid}
            why = f"{cfg['id']} {cfg['policy']}: {side} {q} at the {'ask' if side == 'buy' else 'bid'} {px} " \
                  f"(target {target.get(s, 0)}, selected {pending['selected']})"
            intents.append(Intent("enter" if side == "buy" else "exit", s, qty=float(q), price_hint=float(px),
                                  signal_key=f"{s}:{pending['signal']}:{side}:{view.now}", reason=why[:300],
                                  order=OrderSpec(window_s=CHILD_WINDOW_S), meta=meta))
        L.trim(model)
        return intents

    def update_state(self, view, intents):
        st = getattr(self, "_st", None) or dict(view.state or {})
        st.setdefault("installed_at", view.session)
        return st


def sleeves():
    return [R19Etf(c) for c in RULES["sleeves"]]
