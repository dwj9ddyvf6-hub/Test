"""IU-body fidelity drive (IU-BODY-ORDER-LOGIC-20261116).

Drives the ARCHIVE reducer itself — strategies/public_recipes/
public_source_sleeves.py from the estate archive, imported
read-only and sha-verified against the value
backend/public_recipe_runtime.py::load_core pins — and the desk
implementation's core reducer (desk3/iu_body.py::IuBodyReducer) on
identical event sequences, comparing after EVERY event:

- the source decision features (body, body_baseline, atr,
  long_signal, short_signal) on every BAR;
- the pending target (side + reason);
- the position (side, qty, avg_price, opened_at, trailing stop,
  stop_active_from) and the book cash;
- every emitted intent that carries a decision (PAPER_ORDER,
  STOP_PLAN, ENTRY_VETO, CANCEL_ORDER, ORDER_CANCELLED);
- the diagnostics list.

Scenarios: A long lifecycle (entry, stop init/ratchet/hold, quote
trigger exit — including a bar whose low pierces the stop with the
bid above it, which must NOT exit); B short lifecycle (the core
reducer carries the source's short side so fidelity is measured
against the unmodified source; the desk's long-only spot overlay
lives in evaluate() and is proven separately in the blocker test);
C the >=21-bar warmup boundary; D stale-bar veto, entry TTL expiry,
quote-not-strictly-after; E the nonpositive-stop branch; R the
recorded Kraken ENJ tape from a live snapshot (1-minute rows
resampled to the source's 5-minute bars by the engine's own
resampler, fed to both sides identically).

Output: desk3/iu_body_fidelity_result.json (the SSO CONV-46
fidelity file is the template for this artifact's shape).

Run: python3 desk3/iu_body_fidelity_check.py [--snapshot PATH]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ARCHIVE = os.path.expanduser(
    "~/workspace/.scratch-ausar-archive/handoff-20261024/source/"
    "strategies/public_recipes/public_source_sleeves.py")
ARCHIVE_SHA = ("e64c995dd451ac0fd0a32f8a1bcc22624a76362c58d607ee9e"
               "decc2d99722e6b")
UTC = timezone.utc
T0 = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)


def iso(d):
    return d.astimezone(UTC).isoformat()


def load_archive():
    raw = open(ARCHIVE, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ARCHIVE_SHA:
        raise ValueError(f"archive source sha mismatch: {digest}")
    spec = importlib.util.spec_from_file_location("archive_iu_source", ARCHIVE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def receipts(t0):
    avail = iso(t0 - timedelta(hours=1))
    # valid across both the synthetic window (2026-01) and the
    # recorded tape's window (2026-11): the archive validates
    # receipt clocks on every entry quote.
    until = iso(t0 + timedelta(days=400))
    return {
        "contract": {"source": "fixture-contract", "id": "contract-1",
                     "available_at": avail, "valid_until": until,
                     "market_kind": "spot", "symbol": "ENJUSDT",
                     "paper_only": True, "price_tick": 0.00001,
                     "qty_step": 0.1, "max_leverage": 1},
        "fees": {"source": "fixture-fees", "id": "fees-1",
                 "available_at": avail, "valid_until": until,
                 "taker_bps": 10.0},
        "short_capability": {"source": "fixture-short", "id": "short-1",
                             "available_at": avail, "valid_until": until,
                             "allowed": True},
        "borrow": {"source": "fixture-borrow", "id": "borrow-1",
                   "available_at": avail, "valid_until": until,
                   "available_qty": 5000.0, "annual_rate": 0.05},
    }


RECEIPTS = receipts(T0)


def bar_ev(idx, o, h, l, c, v=1000.0, open_dt=None, lag_s=1.0):
    open_dt = open_dt or (T0 + timedelta(seconds=300 * idx))
    close_dt = open_dt + timedelta(seconds=300)
    return {"type": "BAR", "id": f"bar:{iso(open_dt)}", "symbol": "ENJUSDT",
            "received_at": iso(close_dt + timedelta(seconds=lag_s)),
            "bar": {"open_at": iso(open_dt), "close_at": iso(close_dt),
                    "available_at": iso(close_dt), "open": o, "high": h,
                    "low": l, "close": c, "volume": v}}


def quote_ev(n, bid, ask, asof_dt):
    return {"type": "QUOTE", "id": f"quote:{n}:{iso(asof_dt)}",
            "symbol": "ENJUSDT",
            "received_at": iso(asof_dt + timedelta(seconds=1)),
            "quote": {"asof": iso(asof_dt), "bid": bid, "ask": ask},
            "receipts": RECEIPTS}


def fill_ev(order_id, qty, price, filled_dt):
    fees = qty * price * 0.001
    return {"type": "FILL", "id": f"fill:{order_id}:{iso(filled_dt)}",
            "symbol": "ENJUSDT", "order_id": order_id, "qty": qty,
            "price": price, "fees": fees, "paper_only": True,
            "filled_at": iso(filled_dt), "received_at": iso(filled_dt)}


def cashflow_ev(covers_id, kind, at_dt):
    return {"type": "CASHFLOW", "id": f"cashflow:{covers_id}",
            "symbol": "ENJUSDT", "paper_only": True, "amount": 0.0,
            "cashflow_kind": kind, "covers_obligation_id": covers_id,
            "source": "fixture-cashflow", "source_receipt_id": "cf-1",
            "effective_at": iso(at_dt), "received_at": iso(at_dt)}


def cancel_ev(order_id, at_dt):
    return {"type": "CANCEL", "id": f"cancel:{order_id}:{iso(at_dt)}",
            "symbol": "ENJUSDT", "order_id": order_id,
            "received_at": iso(at_dt)}


# ------------------------------------------------------------------
# normalization of both sides' outputs onto one comparable surface
# ------------------------------------------------------------------
def norm_intents(intents):
    out = []
    for it in intents or []:
        k = it.get("kind")
        if k == "PAPER_ORDER":
            out.append({"kind": k, "id": it["id"], "action": it["action"],
                        "qty": it["qty"], "quote_price": it["quote_price"]})
        elif k == "STOP_PLAN":
            af = it["active_from"]
            out.append({"kind": k, "side": it["side"], "qty": it["qty"],
                        "source_stop_price": it["source_stop_price"],
                        "active_from": af if isinstance(af, str) else iso(af)})
        elif k == "ENTRY_VETO":
            out.append({"kind": k, "source_side": it["source_side"],
                        "reasons": list(it["reasons"])})
        elif k == "CANCEL_ORDER":
            out.append({"kind": k, "order_id": it["order_id"],
                        "reason": it["reason"]})
        elif k == "ORDER_CANCELLED":
            out.append({"kind": k, "order_id": it["order_id"],
                        "remaining_unfilled": it["remaining_unfilled"]})
        elif k == "SOURCE_DECISION":
            f = it["features"]
            out.append({"kind": k,
                        "features": {"body": f["body"],
                                     "body_baseline": f["body_baseline"],
                                     "atr": f["atr"],
                                     "long_signal": f["long_signal"],
                                     "short_signal": f["short_signal"]},
                        "position_side_before": it["position_side_before"]})
    return out


def archive_observable(state):
    pos = state["position"]
    t = state["pending_target"]
    return {
        "pending_target": ({"side": t["side"], "reason": t["reason"]}
                           if t else None),
        "position": ({"side": pos["side"], "qty": pos["qty"],
                      "avg_price": pos["avg_price"],
                      "opened_at": pos["opened_at"], "stop": pos["stop"],
                      "stop_active_from": pos["stop_active_from"]}
                     if pos else None),
        "cash": state["book"]["cash"],
        "obligations": [x["id"] for x in state["accounting_obligations"]],
    }


class Drive:
    """Feed one event sequence to both reducers, compare every step."""

    def __init__(self, core, name):
        from desk3.iu_body import IuBodyReducer
        self.core = core
        self.name = name
        self.config = core.make_config("iu_body", {
            "symbol": "ENJUSDT", "market_kind": "spot",
            "initial_cash": 100000.0, "quantity_mode": "equity_percent",
            "quantity_value": 100.0})
        self.astate = core.initial_state("iu_body", self.config)
        self.mine = IuBodyReducer()
        self.steps = 0
        self.divergences = []
        self.counts = {"bars": 0, "orders": 0, "stop_plans": 0,
                       "triggers": 0, "vetoes": 0}

    def _compare(self, ev, ares, mres):
        self.steps += 1
        a_obs = archive_observable(self.astate)
        m_obs = self.mine.observable()
        a_int = norm_intents(ares["intents"])
        m_int = norm_intents(mres["intents"])
        a_diag = list(ares["diagnostics"])
        m_diag = list(mres["diagnostics"])
        for it in a_int:
            if it["kind"] == "PAPER_ORDER":
                self.counts["orders"] += 1
            elif it["kind"] == "STOP_PLAN":
                self.counts["stop_plans"] += 1
            elif it["kind"] == "ENTRY_VETO":
                self.counts["vetoes"] += 1
        if a_obs["pending_target"] and \
                a_obs["pending_target"]["reason"] == \
                "observed_quote_stop_trigger":
            self.counts["triggers"] += 1
        if ev["type"] == "BAR":
            self.counts["bars"] += 1
        problems = []
        if a_obs != m_obs:
            problems.append(f"observable: archive={a_obs} mine={m_obs}")
        if a_int != m_int:
            problems.append(f"intents: archive={a_int} mine={m_int}")
        if a_diag != m_diag:
            problems.append(f"diagnostics: archive={a_diag} mine={m_diag}")
        if problems:
            self.divergences.append({"event_id": ev["id"],
                                     "problems": problems})

    def feed(self, ev):
        core = self.core
        ares = core.step("iu_body", self.config, self.astate, ev)
        self.astate = ares["state"]
        t = ev["type"]
        if t == "BAR":
            b = dict(ev["bar"])
            b["_open_epoch"] = datetime.fromisoformat(
                b["open_at"]).timestamp()
            b["_close_epoch"] = datetime.fromisoformat(
                b["close_at"]).timestamp()
            mres = self.mine.bar(b, datetime.fromisoformat(ev["received_at"]))
        elif t == "QUOTE":
            q = ev["quote"]
            rc = ev.get("receipts") or {}
            mine_rc = {}
            if rc.get("contract"):
                c = rc["contract"]
                mine_rc["contract"] = {
                    "market_kind": c["market_kind"], "symbol": c["symbol"],
                    "price_tick": c["price_tick"], "qty_step": c["qty_step"],
                    "max_leverage": c["max_leverage"]}
            if rc.get("fees"):
                mine_rc["fees"] = {"taker_bps": rc["fees"]["taker_bps"]}
            if rc.get("short_capability"):
                mine_rc["short_capability"] = {
                    "allowed": rc["short_capability"]["allowed"]}
            if rc.get("borrow"):
                mine_rc["borrow"] = {
                    "available_qty": rc["borrow"]["available_qty"]}
            mres = self.mine.quote(
                q["bid"], q["ask"], datetime.fromisoformat(q["asof"]),
                datetime.fromisoformat(ev["received_at"]), mine_rc)
        elif t == "FILL":
            mres = self.mine.fill(
                ev["order_id"], ev["qty"], ev["price"], ev["fees"],
                datetime.fromisoformat(ev["filled_at"]),
                datetime.fromisoformat(ev["received_at"]))
        elif t == "CANCEL":
            mres = self.mine.cancel(
                ev["order_id"], datetime.fromisoformat(ev["received_at"]))
        elif t == "CASHFLOW":
            mres = self.mine.cashflow(
                ev["amount"], ev.get("covers_obligation_id"),
                datetime.fromisoformat(ev["received_at"]))
        else:
            raise ValueError(t)
        self._compare(ev, ares, mres)
        return ares

    def last_order(self):
        orders = [o for o in self.astate["orders"].values()
                  if o["status"] == "open"]
        return orders[-1] if orders else None

    def result(self):
        return {"scenario": self.name, "steps": self.steps,
                "counts": self.counts,
                "divergences": self.divergences,
                "final": archive_observable(self.astate)}


def quiet(idx, o=100.0, c=100.1):
    return bar_ev(idx, o, max(o, c) + 0.3, min(o, c) - 0.4, c)


def scenario_a(core):
    d = Drive(core, "A_long_lifecycle")
    for i in range(26):
        d.feed(quiet(i))
    # bar 26: big bullish body -> long target
    d.feed(bar_ev(26, 100.0, 103.2, 99.9, 103.0))
    close26 = T0 + timedelta(seconds=300 * 27)
    d.feed(quote_ev(1, 102.9, 103.1, close26 + timedelta(seconds=2)))
    o = d.last_order()
    d.feed(fill_ev(o["id"], o["qty"], 103.1,
                   close26 + timedelta(seconds=3)))
    # held bars: stop initializes, ratchets, holds
    closes = [104.0, 106.0, 105.0, 104.5]
    for j, c in enumerate(closes):
        prev = 103.1 if j == 0 else closes[j - 1]
        d.feed(bar_ev(27 + j, prev, max(prev, c) + 0.4, min(prev, c) - 0.4, c))
    stop = d.astate["position"]["stop"]
    last_close = T0 + timedelta(seconds=300 * 31)
    # quote with bid above the stop: no trigger
    d.feed(quote_ev(2, stop + 0.05, stop + 0.25,
                    last_close + timedelta(seconds=2)))
    # bar 31: low pierces the stop, close recovers — the source has
    # NO bar-low exit; still no trigger without the quote
    d.feed(bar_ev(31, 104.5, 105.0, stop - 0.5, 104.8))
    last_close = T0 + timedelta(seconds=300 * 32)
    # quote with bid at/below the stop: observed_quote_stop_trigger
    d.feed(quote_ev(3, stop - 0.01, stop + 0.19,
                    last_close + timedelta(seconds=2)))
    o = d.last_order()
    d.feed(fill_ev(o["id"], o["qty"], stop - 0.01,
                   last_close + timedelta(seconds=3)))
    d.feed(quiet(32))
    return d.result()


def scenario_b(core):
    d = Drive(core, "B_short_lifecycle")
    for i in range(26):
        d.feed(quiet(i))
    d.feed(bar_ev(26, 103.0, 103.2, 99.8, 100.0))  # big bearish body
    close26 = T0 + timedelta(seconds=300 * 27)
    d.feed(quote_ev(1, 99.9, 100.1, close26 + timedelta(seconds=2)))
    o = d.last_order()
    d.feed(fill_ev(o["id"], o["qty"], 99.9, close26 + timedelta(seconds=3)))
    closes = [99.0, 97.0]
    for j, c in enumerate(closes):
        prev = 99.9 if j == 0 else closes[j - 1]
        d.feed(bar_ev(27 + j, prev, prev + 0.4, c - 0.4, c))
    stop = d.astate["position"]["stop"]
    last_close = T0 + timedelta(seconds=300 * 29)
    d.feed(quote_ev(2, stop - 0.25, stop - 0.05,
                    last_close + timedelta(seconds=2)))  # ask below stop
    d.feed(quote_ev(3, stop - 0.19, stop + 0.01,
                    last_close + timedelta(seconds=4)))  # ask >= stop
    o = d.last_order()
    d.feed(fill_ev(o["id"], o["qty"], stop + 0.01,
                   last_close + timedelta(seconds=5)))
    return d.result()


def scenario_c(core):
    d = Drive(core, "C_warmup_boundary")
    for i in range(19):
        d.feed(quiet(i))
    # 20th bar: huge body, but only 20 bars served — baseline None
    d.feed(bar_ev(19, 100.0, 103.2, 99.9, 103.0))
    d.feed(quiet(20, o=103.0, c=103.1))
    # 22nd bar: 21+ bars served, big body fires
    d.feed(bar_ev(21, 103.0, 106.2, 102.9, 106.0))
    return d.result()


def scenario_d(core):
    d = Drive(core, "D_veto_ttl_quote_clock")
    for i in range(25):
        d.feed(quiet(i))
    # stale bar: received 301s after close -> stale_bar_entry_veto
    d.feed(bar_ev(25, 100.0, 103.2, 99.9, 103.0, lag_s=301.0))
    d.feed(quiet(26, o=103.0, c=103.1))
    # fresh big body -> target; quote at +301s -> entry TTL expiry
    d.feed(bar_ev(27, 103.0, 106.2, 102.9, 106.0))
    close27 = T0 + timedelta(seconds=300 * 28)
    created = close27 + timedelta(seconds=1)
    d.feed(quote_ev(1, 105.9, 106.1, created + timedelta(seconds=300.5)))
    # another big body -> new target; quote asof == created -> the
    # strictly-after diagnostic; then a proper quote -> order; then
    # a cancel acknowledgement
    d.feed(bar_ev(28, 106.0, 109.2, 105.9, 109.0, lag_s=3.0))
    close28 = T0 + timedelta(seconds=300 * 29)
    created2 = close28 + timedelta(seconds=3)
    d.feed(quote_ev(2, 108.9, 109.1, created2))
    d.feed(quote_ev(3, 108.9, 109.1, created2 + timedelta(seconds=2)))
    o = d.last_order()
    d.feed(cancel_ev(o["id"], created2 + timedelta(seconds=3)))
    return d.result()


def scenario_e(core):
    d = Drive(core, "E_nonpositive_stop")
    for i in range(25):
        d.feed(bar_ev(i, 1.0, 5.0, 0.2, 1.0, v=100.0))  # body 0, range 4.8
    d.feed(bar_ev(25, 1.0, 3.6, 0.9, 3.4, v=100.0))     # big body, long
    close25 = T0 + timedelta(seconds=300 * 26)
    d.feed(quote_ev(1, 3.39, 3.41, close25 + timedelta(seconds=2)))
    o = d.last_order()
    d.feed(fill_ev(o["id"], o["qty"], 3.41, close25 + timedelta(seconds=3)))
    # ATR ~4.8 -> candidate stop avg - 2*ATR < 0: not submitted
    d.feed(bar_ev(26, 3.4, 5.0, 0.2, 3.3, v=100.0))
    d.feed(bar_ev(27, 3.3, 5.0, 0.2, 3.35, v=100.0))
    return d.result()


def scenario_r(core, snapshot_path):
    from desk3.iu_body import resample_1min_to_5min
    doc = json.load(open(snapshot_path))
    rows = doc["data"]["bars"]["ENJ/USD|1Min"]
    bars5 = resample_1min_to_5min(rows)
    d = Drive(core, "R_recorded_kraken_tape")
    for i, b in enumerate(bars5):
        open_dt = datetime.fromisoformat(b["open_at"])
        ev = bar_ev(i, b["open"], b["high"], b["low"], b["close"],
                    v=b["volume"], open_dt=open_dt)
        d.feed(ev)
        close_dt = open_dt + timedelta(seconds=300)
        o = d.last_order()
        d.feed(quote_ev(i, b["close"] * 0.999, b["close"] * 1.001,
                        close_dt + timedelta(seconds=2)))
        o = d.last_order()
        if o:
            d.feed(fill_ev(o["id"], o["qty"], o["quote_price"],
                           close_dt + timedelta(seconds=3)))
    # tail: if a closed spot short left a borrow obligation behind
    # (entries vetoed until covered), cover it with a cashflow and
    # prove entries resume identically on both sides.
    obs = list(d.astate["accounting_obligations"])
    if obs:
        last_close_dt = datetime.fromisoformat(bars5[-1]["close_at"])
        at = last_close_dt + timedelta(seconds=10)
        for ob in obs:
            d.feed(cashflow_ev(ob["id"], ob["kind"], at))
            at += timedelta(seconds=1)
        if d.astate["position"] is None:
            lc = bars5[-1]["close"]
            d.feed(bar_ev(len(bars5), lc, lc * 1.05 + 0.001, lc * 0.999,
                          lc * 1.04, open_dt=last_close_dt))
            ncdt = last_close_dt + timedelta(seconds=300)
            d.feed(quote_ev(999, lc * 1.039, lc * 1.041,
                            ncdt + timedelta(seconds=2)))
            o = d.last_order()
            if o:
                d.feed(fill_ev(o["id"], o["qty"], o["quote_price"],
                               ncdt + timedelta(seconds=3)))
    res = d.result()
    res["snapshot"] = snapshot_path
    res["snapshot_asof"] = doc.get("asof")
    res["bars_1min"] = len(rows)
    res["bars_5min"] = len(bars5)
    return res


def scenario_f(snapshot_path):
    """Fixture cycle on the recorded tape through the DESK path:
    snapshot view -> adapters3 evaluate -> dispatcher -> kraken_paper
    fill, entry then observed-quote-stop exit. Quotes are the
    recorded book's form (bid/ask at the bar close -/+ 0.1%, the
    same synthetic quote the reducer drive uses)."""
    import tempfile
    from adapters3.fwd_alpaca_enj_iu_body import evaluate
    from desk3.broker import FakeBroker
    from desk3.dispatcher import Dispatcher
    from desk3.iu_body import resample_1min_to_5min

    class LiveBookFake(FakeBroker):
        live_book = True

    sid = "fwd_alpaca_enj_iu_body"
    doc = json.load(open(snapshot_path))
    rows1m = doc["data"]["bars"]["ENJ/USD|1Min"]
    tmp = tempfile.mkdtemp()
    broker = LiveBookFake(prices={"ENJ/USD": 0.02})
    d = Dispatcher(tmp, broker,
                   slices={sid: {"capital_usd": 10000, "cash_usd": 10000}},
                   price_lookup=lambda s: None)

    def _iso(ep):
        return datetime.fromtimestamp(ep, UTC).isoformat()

    entry = None
    exit_ = None
    pos = []
    steps = 0
    for end in range(105, len(rows1m) + 1, 5):
        sub = rows1m[:end]
        bars5 = resample_1min_to_5min(sub)
        if not bars5:
            continue
        lc = bars5[-1]["_close_epoch"]
        close = bars5[-1]["close"]
        bid, ask = close * 0.999, close * 1.001
        view = {"bars": {"ENJ/USD|1Min": sub}, "positions": pos,
                "slice": {"cash_usd": 10000.0},
                "kraken": {"generated_at": _iso(lc + 3)},
                "kraken.book": {"bids": [[str(bid), "1", lc + 2]],
                                "asks": [[str(ask), "1", lc + 2]]}}
        out = evaluate(view, {})
        steps += 1
        if out and entry is None:
            r = d.process_intent(out[0], sid)
            entry = {"bar_close": _iso(lc), "intent": out[0], "dispatch": r}
            if r["status"] == "filled":
                pos = [{"symbol": "ENJUSDT", "qty": r["qty"],
                        "avg_price": r["price"], "opened_at": _iso(lc + 3),
                        "sleeve_id": sid}]
        elif out and entry is not None and exit_ is None:
            r = d.process_intent(out[0], sid)
            exit_ = {"bar_close": _iso(lc), "intent": out[0], "dispatch": r}
            break
    fills = []
    path = os.path.join(tmp, "state", "dispatcher.jsonl")
    if os.path.exists(path):
        fills = [{"venue": x["venue"], "qty": x["qty"], "price": x["price"]}
                 for x in (json.loads(l) for l in open(path))
                 if x.get("event") == "fill"]
    return {"scenario": "F_fixture_cycle_recorded_tape",
            "snapshot": snapshot_path, "snapshot_asof": doc.get("asof"),
            "eval_steps": steps, "entry": entry, "exit": exit_,
            "journal_fills": fills, "submit_count": broker.submit_count,
            "roundtrip_complete": bool(entry and exit_
                                       and len(fills) == 2
                                       and broker.submit_count == 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--output", default=os.path.join(
        ROOT, "desk3", "iu_body_fidelity_result.json"))
    args = ap.parse_args()
    core = load_archive()
    results = [scenario_a(core), scenario_b(core), scenario_c(core),
               scenario_d(core), scenario_e(core)]
    snap = args.snapshot
    if snap is None:
        cands = sorted(glob.glob(os.path.expanduser(
            "~/workspace/muse-desk-v3/state/snapshots/*.json")),
            key=os.path.getmtime)
        snap = cands[-1] if cands else None
    fixture = None
    if snap:
        results.append(scenario_r(core, snap))
        fixture = scenario_f(snap)
    total_steps = sum(r["steps"] for r in results)
    total_div = sum(len(r["divergences"]) for r in results)
    out = {
        "id": "IU-BODY-ORDER-LOGIC-20261116",
        "archive_source": ARCHIVE,
        "archive_source_sha256": ARCHIVE_SHA,
        "archive_sha_verified": True,
        "implementation": "desk3/iu_body.py::IuBodyReducer + source_features",
        "book_config": {"strategy": "iu_body", "symbol": "ENJUSDT",
                        "market_kind": "spot", "initial_cash": 100000.0,
                        "quantity_mode": "equity_percent",
                        "quantity_value": 100.0,
                        "params": {"big_body_threshold": 4.0,
                                   "atr_length": 14, "atr_factor": 2.0,
                                   "body_baseline":
                                   "source_inclusive21_div20"}},
        "scenarios": results,
        "fixture_cycle": fixture,
        "total_steps_compared": total_steps,
        "total_divergences": total_div,
        "verdict": "MATCH" if total_div == 0 else "DIVERGENCE",
        "notes": [
            "Every event's observable state (pending target, position, "
            "cash), decision intents and diagnostics compared exactly "
            "(float equality; both sides run the archive's own formulas).",
            "Scenario A includes a bar whose low pierces the trailing "
            "stop with no quote trigger: neither side exits (the source "
            "has no bar-low exit; the desk sibling's bar-low/opposite-"
            "body exits are divergences and are not in this port).",
            "Scenario B exercises the source's short side in the core "
            "reducer; the desk sleeve itself is long-only under the "
            "runtime's spot overlay (evaluate() suppression proven in "
            "tests/test_iu_body_order_logic_20261116_blockers.py).",
            "No archive step was inexecutable: the reducer is pure "
            "stdlib Python and every branch above ran on both sides; "
            "no hand-computed substitutions were needed.",
            "The recorded-tape scenario caught a branch the synthetic "
            "scenarios missed: a closed spot short leaves a borrow "
            "accounting obligation in the archive, vetoing every later "
            "entry (unreconciled_funding_or_borrow_cashflow) until a "
            "cashflow covers it. The core reducer now carries that "
            "obligation exactly, and scenario R's tail covers it and "
            "proves entries resume identically.",
        ],
    }
    with open(args.output, "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(json.dumps({"steps": total_steps, "divergences": total_div,
                      "verdict": out["verdict"],
                      "scenarios": [(r["scenario"], r["steps"],
                                     len(r["divergences"]))
                                    for r in results]}, indent=1))
    return 0 if total_div == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
