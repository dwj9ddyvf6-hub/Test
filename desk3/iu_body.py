"""IU-body order logic for fwd_alpaca_enj_iu_body — faithful desk-side
implementation of the archive public-recipe reducer (IU-BODY-ORDER-
LOGIC-20261116, Mon 2026-11-16 total audit).

WHY THIS FILE EXISTS. The sleeve's byte-pinned vendored strategy
(desk3/vendor/sleeves/fwd_alpaca_enj_iu_body.py, sha256 171f5f79...)
returns [] from signal() by source design: the v2 source it preserves
(PUBLIC_IU_BODY_SPOT100) carried no order logic, so the sleeve could
evaluate on the real Kraken ENJ tape and sit in the dispatcher's ENJ
paper class (ENJ-PAPER-20261116) yet never emit an intent. The
escalations lane found the exact order-logic spec in the estate
archive; this module is the desk-side implementation the roster row
now uses. The vendored file is untouched and stays byte-identical.

SOURCE OF RECORD (read before changing anything here):
- ~/workspace/.scratch-ausar-archive/handoff-20261024/source/
  strategies/public_recipes/public_source_sleeves.py
  (sha256 e64c995dd451ac0fd0a32f8a1bcc22624a76362c58d607ee9edecc2
  d99722e6b, verified by backend/public_recipe_runtime.py::load_core)
  ::source_features('iu_body') and ::step('iu_body') — the reducer.
- .../strategies/public_recipes/sources/IU_BIG_BODY_BAR.pine — the
  Pine original the reducer preserves.
- .../source/backend/public_recipe_runtime.py — the runtime overlay:
  market ENJUSDT 5m bars (300000 ms); book PUBLIC_IU_BODY_SPOT100:
  spot, quantity_mode equity_percent, quantity_value 100; spot is
  LONG-ONLY (read_status: "spot long only; short research decisions
  visible but opening unsupported"); entry TTL 300s; bar max
  decision lag 300s; quote max age 10s.

THE LOGIC (no behavior exists here that the source does not have):
- Params: big_body_threshold 4.0, atr_length 14, atr_factor 2.0,
  body_baseline 'source_inclusive21_div20'.
- bodies = |close-open|; baseline = sum of the last 21 bodies / 20
  (needs >= 21 bars, else None and no signal); strong = last body
  > 4.0 * baseline; long_signal = strong and close > open;
  short_signal = strong and close < open; ATR14 by Wilder RMA.
- Reducer: flat + long_signal -> target long (source_body_impulse);
  flat + short_signal -> target short; held long: trailing stop =
  max(prior stop, close - 2*ATR14), initialized at avg entry -
  2*ATR14, never loosens; held short mirrored. A computed stop
  <= 0 is NOT submitted (source diagnostic
  source_stop_nonpositive_not_submitted; the prior stop stands).
- Exit ONLY on the observed quote trigger: long exits when
  bid <= stop (short mirrored on ask) on a quote observed strictly
  after the stop became active -> target flat
  (observed_quote_stop_trigger). NO opposite-body exit exists in
  the source reducer. The desk's live sibling
  desk3/aster_b4.py::evaluate_enj_iu_body adds one
  (source_opposite_body_exit) and triggers its stop on bar lows —
  both are DIVERGENCES of that sibling and are deliberately NOT
  copied here.

DESK WIRING (coordinator decisions, from the estate's precedents):
- Venue: the desk's ENJ kraken_paper class (landing 8096eed). This
  sleeve was already registered in dispatcher.ENJ_PAPER_SLEEVES and
  its roster row already carries own_book_view + the ENJ-PAPER
  stamp; intents it emits in ENJ/USD fill at the dispatcher at the
  Kraken feed price, journaled venue=kraken_paper. This module only
  had to produce the intents.
- Bars: the Kraken ENJ tape the desk already serves
  (bars:ENJ/USD:1Min / bars["ENJ/USD|1Min"] from KrakenProducer),
  resampled to the source's 5-minute bars by resample_1min_to_5min
  below (complete UTC buckets only; the crypto_bars.resample_1h_to_4h
  pattern). No second tape is forked.
- Sizing: the sleeve's standard $10,000 slice through the
  dispatcher's slice check. The source book's quantity_value 100
  (100% of its own book, equity_percent) maps to the slice: entry
  qty = the slice's available cash expressed in whole ENJ units at
  the observed ask (last close when no fresh quote), rounded down,
  exactly the aster spot family's _frac_qty/int form.
- Long-only: per the runtime's spot read_status, a short signal
  while flat produces NO entry intent (the core reducer below keeps
  the source's short target so fidelity is measured against the
  unmodified source; the suppression is this desk overlay, applied
  in evaluate() only, and named here).
- Session: the roster row moves rth -> 24h, the source market's own
  clock and the aster_pub_enj_iu_body sibling's session; cadence
  stays 300s, the source's bar length and entry TTL.

LIVE TRANSLATION (named, the desk's universal serving form): the
archive reducer is an event machine (BAR / QUOTE / FILL events with
receipts). The desk evaluates per cycle from a snapshot, so
evaluate() reconstructs the reducer's observable state from the
served bars plus the sleeve's own-book position (qty, avg_price,
opened_at — the journal-derived row cycle.own_book_positions
serves): the trailing stop is replayed deterministically over the
bars after entry with the archive's own update rule (the same
reconstruction the aster sibling uses for its stop, minus its
divergences), and the observed quote is the snapshot's kraken.book
top of book (best bid/ask with their Kraken level epochs; capture
clock = the kraken payload's generated_at). Entry lag, entry TTL
and quote age are enforced against those clocks with the source's
own bounds (300s / 300s / 10s). Indicators compute over the served
window, as everywhere on this desk.

FIDELITY: desk3/iu_body_fidelity_check.py drives the ARCHIVE
reducer itself (imported read-only, sha-verified) and this module's
core reducer on identical synthetic + recorded event sequences;
desk3/iu_body_fidelity_result.json is the published result.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

SLEEVE_ID = "fwd_alpaca_enj_iu_body"
SYMBOL = "ENJ/USD"
ARCHIVE_SYMBOL = "ENJUSDT"
SOURCE_SHA256 = ("e64c995dd451ac0fd0a32f8a1bcc22624a76362c58d607ee9e"
                 "decc2d99722e6b")
PARAMS = {"big_body_threshold": 4.0, "atr_length": 14,
          "atr_factor": 2.0, "body_baseline": "source_inclusive21_div20"}
BAR_MS = 300000
ENTRY_TTL_S = 300.0
BAR_MAX_DECISION_LAG_S = 300.0
QUOTE_MAX_AGE_S = 10.0
SLICE_USD = 10000.0


# ------------------------------------------------------------------
# indicators — the archive's own recurrences, verbatim formulas
# (public_source_sleeves.py::rma / ::atr / ::source_features iu_body)
# ------------------------------------------------------------------
def rma(xs, n):
    out = []
    seed = []
    old = None
    for x in xs:
        if x is None:
            out.append(None)
            continue
        if old is None:
            seed.append(x)
            if len(seed) < n:
                out.append(None)
                continue
            old = sum(seed[-n:]) / n
        else:
            old = (old * (n - 1) + x) / n
        out.append(old)
    return out


def atr_series(bars, n):
    """Wilder ATR over archive-shaped bars ({open, high, low, close})."""
    tr = []
    for i, b in enumerate(bars):
        if i == 0:
            tr.append(b["high"] - b["low"])
        else:
            pc = bars[i - 1]["close"]
            tr.append(max(b["high"] - b["low"], abs(b["high"] - pc),
                          abs(b["low"] - pc)))
    return rma(tr, n)


def source_features(bars, params=PARAMS):
    """Exact port of the archive source_features 'iu_body' branch.
    `bars` are archive-shaped dicts with open/high/low/close keys."""
    if not bars:
        return {}
    bodies = [abs(b["close"] - b["open"]) for b in bars]
    if params["body_baseline"] == "source_inclusive21_div20":
        base = sum(bodies[-21:]) / 20 if len(bodies) >= 21 else None
    elif params["body_baseline"] == "declared_corrected_prior20":
        base = sum(bodies[-21:-1]) / 20 if len(bodies) >= 21 else None
    else:
        raise ValueError("unknown declared body baseline")
    b = bars[-1]
    strong = base is not None and bodies[-1] > base * params["big_body_threshold"]
    return {"body": bodies[-1], "body_baseline": base,
            "atr": atr_series(bars, params["atr_length"])[-1],
            "long_signal": strong and b["close"] > b["open"],
            "short_signal": strong and b["close"] < b["open"]}


# ------------------------------------------------------------------
# core reducer — the archive step() for strategy 'iu_body' under the
# book of record's configuration (spot, equity_percent 100, the
# runtime overlay bounds). Cash is tracked because the archive's
# order quantity derives from it. Event/receipt validation that
# cannot change a decision (id dedupe, clock monotonicity) is not
# reproduced; every branch that CAN change a target, a stop, an
# order or a position is.
# ------------------------------------------------------------------
class IuBodyReducer:
    def __init__(self, initial_cash=100000.0, quantity_value=100.0):
        self.cash = float(initial_cash)
        self.quantity_value = float(quantity_value)
        self.bars = []
        self.position = None          # {side, qty, avg_price, opened_at, stop, stop_active_from}
        self.pending_target = None    # {side, reason, created_at, source_bar_open_at}
        self.orders = {}              # id -> order dict
        self.next_order = 1
        self.obligations = []         # archive accounting_obligations ids

    # -- archive target() -------------------------------------------
    def _target(self, side, reason, at):
        intents, diagnostics = [], []
        if side != "flat" and self.bars and (
                at - datetime.fromtimestamp(self.bars[-1]["_close_epoch"],
                                            timezone.utc)).total_seconds() \
                > BAR_MAX_DECISION_LAG_S:
            diagnostics.append("stale_bar_entry_veto")
            intents.append({"kind": "ENTRY_VETO", "source_side": side,
                            "reasons": ["stale_bar_entry_veto"]})
            return intents, diagnostics
        old = self.pending_target
        if old and old["side"] != side:
            for oid, o in self.orders.items():
                if o["action"].startswith("OPEN_") and o["status"] == "open":
                    o["status"] = "cancel_requested"
                    intents.append({"kind": "CANCEL_ORDER", "order_id": oid,
                                    "reason": "source_target_changed"})
        self.pending_target = {
            "side": side, "reason": reason, "created_at": at,
            "source_bar_open_at": self.bars[-1]["open_at"] if self.bars else None}
        return intents, diagnostics

    def _expire_entries(self, at):
        intents, diagnostics = [], []
        t = self.pending_target
        if t and t["side"] != "flat" and (
                at - t["created_at"]).total_seconds() >= ENTRY_TTL_S:
            for oid, o in self.orders.items():
                if o["action"].startswith("OPEN_") and o["status"] == "open":
                    o["status"] = "cancel_requested"
                    intents.append({"kind": "CANCEL_ORDER", "order_id": oid,
                                    "reason": "entry_deadline_expired"})
            self.pending_target = None
            diagnostics.append("entry_deadline_expired")
        return intents, diagnostics

    # -- events ------------------------------------------------------
    def bar(self, bar, received_at):
        """Archive BAR branch. `bar` is archive-shaped plus
        _open_epoch/_close_epoch (epoch seconds, float)."""
        intents, diagnostics = [], []
        ei, ed = self._expire_entries(received_at)
        intents += ei
        diagnostics += ed
        self.bars.append(bar)
        f = source_features(self.bars)
        pos = self.position
        decision = {"bar_open_at": bar["open_at"],
                    "bar_close_at": bar["close_at"], "features": f,
                    "position_side_before": pos["side"] if pos else None}
        if pos is None:
            if f["long_signal"]:
                ti, td = self._target("long", "source_body_impulse", received_at)
                intents += ti
                diagnostics += td
            elif f["short_signal"]:
                ti, td = self._target("short", "source_body_impulse", received_at)
                intents += ti
                diagnostics += td
        elif f["atr"] is not None and bar["_close_epoch"] > pos["_opened_epoch"]:
            dist = f["atr"] * PARAMS["atr_factor"]
            old = pos.get("stop")
            new = pos["avg_price"] - dist if pos["side"] == "long" \
                else pos["avg_price"] + dist
            if old is not None:
                new = max(old, bar["close"] - dist) if pos["side"] == "long" \
                    else min(old, bar["close"] + dist)
            if new <= 0:
                diagnostics.append("source_stop_nonpositive_not_submitted")
            else:
                if old is None or new != old:
                    pos["stop_active_from"] = received_at
                pos["stop"] = new
                intents.append({"kind": "STOP_PLAN", "side": pos["side"],
                                "qty": pos["qty"], "source_stop_price": new,
                                "active_from": pos["stop_active_from"]})
        elif pos:
            diagnostics.append("prefill_completed_bar_stop_update_skipped")
        intents.append({"kind": "SOURCE_DECISION", **decision})
        return {"intents": intents, "diagnostics": diagnostics}

    def quote(self, bid, ask, asof, received_at, receipts=None):
        """Archive QUOTE branch (spot). `receipts` carries the entry
        capability receipts the archive validates (contract, fees,
        and for shorts short_capability + borrow); the drive and the
        fidelity check supply valid ones, so a veto here means the
        caller's receipts failed the archive's own checks."""
        intents, diagnostics = [], []
        ei, ed = self._expire_entries(received_at)
        intents += ei
        diagnostics += ed
        pos = self.position
        if pos and pos.get("stop") is not None and \
                asof > pos["stop_active_from"]:
            triggered = bid <= pos["stop"] if pos["side"] == "long" \
                else ask >= pos["stop"]
            if triggered:
                ti, td = self._target("flat", "observed_quote_stop_trigger",
                                      received_at)
                intents += ti
                diagnostics += td
        t = self.pending_target
        if not t:
            return {"intents": intents, "diagnostics": diagnostics}
        if (pos is None or t["side"] == pos["side"]) and asof <= t["created_at"]:
            diagnostics.append("entry_quote_not_strictly_after_source_decision")
            return {"intents": intents, "diagnostics": diagnostics}
        action = None
        qty = None
        if pos and (t["side"] == "flat" or t["side"] != pos["side"]):
            action = "CLOSE_" + pos["side"].upper()
            qty = pos["qty"]
        elif pos and t["side"] == pos["side"]:
            self.pending_target = None
        elif t["side"] == "flat":
            for oid, o in self.orders.items():
                if o["action"].startswith("OPEN_") and o["status"] == "open":
                    o["status"] = "cancel_requested"
                    intents.append({"kind": "CANCEL_ORDER", "order_id": oid,
                                    "reason": "flat_source_target"})
            self.pending_target = None
        else:
            receipts = receipts or {}
            fails = []
            if self.obligations:
                fails.append("unreconciled_funding_or_borrow_cashflow")
            contract = receipts.get("contract") or {}
            fees_r = receipts.get("fees") or {}
            if not contract:
                fails.append("contract_receipt_missing")
            if not fees_r:
                fails.append("fees_receipt_missing")
            if contract and contract.get("market_kind") != "spot":
                fails.append("market_kind_receipt_mismatch")
            if contract and contract.get("symbol") != ARCHIVE_SYMBOL:
                fails.append("contract_symbol_mismatch")
            if t["side"] == "short":
                short = receipts.get("short_capability") or {}
                if short.get("allowed") is not True:
                    fails.append("short_not_explicitly_supported")
                borrow = receipts.get("borrow") or {}
                if not borrow or not borrow.get("available_qty"):
                    fails.append("borrow_quantity_and_rate_missing")
            if fails:
                diagnostics.extend(fails)
                intents.append({"kind": "ENTRY_VETO", "source_side": t["side"],
                                "reasons": fails})
                return {"intents": intents, "diagnostics": diagnostics}
            tick = float(contract["price_tick"])
            lot = float(contract["qty_step"])
            maxlev = float(contract["max_leverage"])
            if tick <= 0 or lot <= 0:
                raise ValueError("positive tick/lot required")
            fb = float(fees_r["taker_bps"]) / 10000
            px = ask if t["side"] == "long" else bid
            nav = self.cash
            wanted = (nav * self.quantity_value / 100) / (px * (1 + fb))
            maximum = (nav * maxlev) / (px * (1 + fb))
            if t["side"] == "long":  # spot long cap, archive verbatim
                maximum = nav / (px * (1 + fb))
            desired = min(wanted, maximum)
            if t["side"] == "short":
                desired = min(desired, float(receipts["borrow"]["available_qty"]))
            qty = float((Decimal(str(desired)) / Decimal(str(lot)))
                        .to_integral_value(rounding=ROUND_DOWN)
                        * Decimal(str(lot)))
            if qty <= 0:
                diagnostics.append("size_rounds_to_zero")
                return {"intents": intents, "diagnostics": diagnostics}
            action = "OPEN_" + t["side"].upper()
        if action:
            active = [o for o in self.orders.values()
                      if o["status"] in ("open", "cancel_requested")]
            if active:
                diagnostics.append("await_existing_order_acknowledgement")
                return {"intents": intents, "diagnostics": diagnostics}
            oid = f"iu_body:{ARCHIVE_SYMBOL}:{self.next_order}"
            self.next_order += 1
            o = {"id": oid, "action": action, "qty": qty, "remaining": qty,
                 "status": "open", "submitted_at": received_at,
                 "quote_asof": asof,
                 "source_target_created_at": t["created_at"],
                 "quote_price": ask if action in ("OPEN_LONG", "CLOSE_SHORT")
                 else bid}
            self.orders[oid] = o
            intents.append({"kind": "PAPER_ORDER", **o})
        return {"intents": intents, "diagnostics": diagnostics}

    def fill(self, order_id, qty, price, fees, filled_at, received_at=None):
        """Archive FILL branch (spot accounting)."""
        intents = []
        if received_at is not None:
            ei, _ed = self._expire_entries(received_at)
            intents += ei
        o = self.orders.get(order_id)
        if not o or o["status"] not in ("open", "cancel_requested"):
            raise ValueError("fill must acknowledge own outstanding order")
        action = o["action"]
        side = "long" if action.endswith("LONG") else "short"
        d = 1 if side == "long" else -1
        pos = self.position
        cash = self.cash
        if action.startswith("OPEN_"):
            if pos and pos["side"] != side:
                raise ValueError("open fill cannot silently cross old position")
            if pos is None:
                pos = {"side": side, "qty": qty, "avg_price": price,
                       "opened_at": filled_at, "_opened_epoch":
                       filled_at.timestamp(), "stop": None,
                       "stop_active_from": None}
                self.position = pos
            else:
                pos["avg_price"] = (pos["avg_price"] * pos["qty"]
                                    + price * qty) / (pos["qty"] + qty)
                pos["qty"] += qty
            cash -= fees
            cash -= d * qty * price
            if qty < o["remaining"] - 1e-10:
                o["status"] = "cancel_requested"
                intents.append({"kind": "CANCEL_ORDER", "order_id": order_id,
                                "reason": "partial_fill_remainder_policy"})
        else:
            if not pos or pos["side"] != side or qty > pos["qty"] + 1e-10:
                raise ValueError("exit fill exceeds owned position")
            if side == "short":  # spot borrow obligation, archive verbatim
                opened_iso = pos["opened_at"].isoformat() \
                    if isinstance(pos["opened_at"], datetime) \
                    else pos["opened_at"]
                self.obligations.append(
                    f"borrow:{opened_iso}:{filled_at.isoformat()}")
            cash += d * qty * price - fees
            pos["qty"] -= qty
            if pos["qty"] <= 1e-10:
                self.position = None
                if self.pending_target and \
                        self.pending_target["side"] == "flat":
                    self.pending_target = None
        self.cash = cash
        o["remaining"] = max(0, o["remaining"] - qty)
        if o["remaining"] <= 1e-10:
            o["status"] = "filled"
        if action.startswith("OPEN_") and o["status"] == "filled" and \
                self.pending_target and \
                self.pending_target["side"] == side:
            self.pending_target = None
        return {"intents": intents, "diagnostics": []}

    def cancel(self, order_id, received_at=None):
        intents = []
        if received_at is not None:
            ei, _ed = self._expire_entries(received_at)
            intents += ei
        o = self.orders.get(order_id)
        if not o or o["status"] not in ("open", "cancel_requested"):
            raise ValueError("cancel must acknowledge own outstanding order")
        o["status"] = "cancelled"
        intents.append({"kind": "ORDER_CANCELLED", "order_id": order_id,
                        "remaining_unfilled": o["remaining"]})
        return {"intents": intents, "diagnostics": []}

    def cashflow(self, amount, covers_id=None, received_at=None):
        """Archive CASHFLOW branch (obligation coverage only; funding
        schedule advancement is perpetual-only and out of this book)."""
        intents = []
        if received_at is not None:
            ei, _ed = self._expire_entries(received_at)
            intents += ei
        if covers_id is not None:
            if covers_id not in self.obligations:
                raise ValueError("cashflow must cover known obligation")
            self.obligations = [x for x in self.obligations
                                if x != covers_id]
        self.cash += float(amount)
        return {"intents": intents, "diagnostics": []}

    def observable(self):
        """The decision surface the fidelity check compares."""
        pos = self.position
        return {
            "pending_target": ({"side": self.pending_target["side"],
                                "reason": self.pending_target["reason"]}
                               if self.pending_target else None),
            "position": ({"side": pos["side"], "qty": pos["qty"],
                          "avg_price": pos["avg_price"],
                          "opened_at": pos["opened_at"].isoformat()
                          if isinstance(pos["opened_at"], datetime)
                          else pos["opened_at"],
                          "stop": pos["stop"],
                          "stop_active_from": pos["stop_active_from"].isoformat()
                          if isinstance(pos["stop_active_from"], datetime)
                          else pos["stop_active_from"]}
                         if pos else None),
            "cash": self.cash,
            "obligations": list(self.obligations),
        }


# ------------------------------------------------------------------
# desk serving form: 1-minute Kraken rows -> the source's 5m bars
# ------------------------------------------------------------------
def _epoch(t):
    if isinstance(t, (int, float)):
        return float(t)
    d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.timestamp()


def _iso(epoch_s):
    return datetime.fromtimestamp(epoch_s, timezone.utc).isoformat()


def resample_1min_to_5min(rows):
    """Aggregate the desk's served ENJ/USD 1-minute rows into the
    source's 5-minute bars. Complete UTC 5-minute buckets only
    (exactly 5 one-minute bars; a trailing partial bucket is a
    forming bar and is dropped, as the archive runtime admits only
    completed bars) — the crypto_bars.resample_1h_to_4h pattern on
    the same tape, never a second source. Output rows are
    archive-shaped: {open_at, close_at, open, high, low, close,
    volume, _open_epoch, _close_epoch}."""
    buckets = {}
    for r in rows or []:
        try:
            ep = _epoch(r.get("t"))
        except (TypeError, ValueError):
            continue
        start = int(ep // 300) * 300
        buckets.setdefault(start, []).append((ep, r))
    out = []
    for start in sorted(buckets):
        mins = sorted(buckets[start], key=lambda x: x[0])
        if len(mins) != 5:
            continue
        rs = [r for _, r in mins]
        try:
            out.append({
                "open_at": _iso(start), "close_at": _iso(start + 300),
                "open": float(rs[0]["o"]), "high": max(float(r["h"]) for r in rs),
                "low": min(float(r["l"]) for r in rs),
                "close": float(rs[-1]["c"]),
                "volume": sum(float(r["v"]) for r in rs),
                "_open_epoch": float(start), "_close_epoch": float(start + 300)})
        except (TypeError, ValueError, KeyError):
            continue
    return out


def reconstruct_stop(bars, avg_price, opened_epoch, side="long"):
    """Replay the archive's BAR-branch stop update over the served
    bars after entry. Returns (stop, stop_active_from_epoch) or
    (None, None) when the source submitted no stop. Deterministic
    in (bars, avg_price, opened_at): the archive's stop depends on
    nothing else."""
    atrs = atr_series(bars, PARAMS["atr_length"])
    stop = None
    active_from = None
    for i, b in enumerate(bars):
        if b["_close_epoch"] <= opened_epoch:
            continue
        atr = atrs[i]
        if atr is None:
            continue
        dist = atr * PARAMS["atr_factor"]
        if stop is None:
            new = avg_price - dist if side == "long" else avg_price + dist
        else:
            cand = b["close"] - dist if side == "long" else b["close"] + dist
            new = max(stop, cand) if side == "long" else min(stop, cand)
        if new <= 0:
            continue  # source_stop_nonpositive_not_submitted: prior stands
        if stop is None or new != stop:
            active_from = b["_close_epoch"]
        stop = new
    return stop, active_from


# ------------------------------------------------------------------
# desk evaluation (the roster module's evaluate path)
# ------------------------------------------------------------------
def _frac_qty(dollars, per_unit):
    """The desk spot family's sizing form (aster_b4._frac_qty,
    WS4-FRACTIONAL-20261114): budget expressed fractionally, floored
    to 6dp, never past the budget."""
    if dollars <= 0 or per_unit <= 0:
        return 0.0
    return math.floor((dollars / per_unit) * 1_000_000) / 1_000_000


def _slice_cash(view):
    sl = (view or {}).get("slice") or {}
    if isinstance(sl, dict) and sl.get("cash_usd") is not None:
        return float(sl["cash_usd"])
    return SLICE_USD


def _enj_1min_rows(view):
    bars = (view or {}).get("bars") or {}
    rows = bars.get("ENJ/USD|1Min") or bars.get("ENJUSD|1Min")
    if rows:
        return rows
    return (view or {}).get("bars:ENJ/USD:1Min") or []


def _position(view, sid):
    for p in (view or {}).get("positions") or []:
        if p.get("sleeve_id") not in (None, sid):
            continue
        if p.get("symbol") in ("ENJ/USD", "ENJUSDT", "ENJUSD") and \
                float(p.get("qty") or 0) != 0:
            return p
    return None


def _book_quote(view):
    """Observed quote: the snapshot's kraken.book top of book.
    Returns (bid, ask, asof_epoch) or None. Level epochs are the
    Kraken stamps the producer serves ([price, qty, epoch])."""
    book = (view or {}).get("kraken.book") or {}
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return None
    try:
        bid = float(bids[0][0])
        ask = float(asks[0][0])
    except (TypeError, ValueError, IndexError):
        return None
    if not 0 < bid <= ask:
        return None
    stamps = []
    for lvl in (bids[0], asks[0]):
        try:
            stamps.append(float(lvl[2]))
        except (TypeError, ValueError, IndexError):
            pass
    return bid, ask, (max(stamps) if stamps else None)


def _capture_epoch(view, fallback):
    payload = (view or {}).get("kraken") or {}
    gen = payload.get("generated_at")
    if gen:
        try:
            return _epoch(gen)
        except (TypeError, ValueError):
            pass
    return fallback


def _intent(sid, kind, qty, price, reason, tag):
    return {"intent_id": f"{sid}-ENJ/USD-{tag}", "kind": kind,
            "symbol": SYMBOL,
            "side": "buy" if kind == "entry" else "sell", "qty": int(qty),
            "order_type": "market", "limit_price": None, "stop_price": None,
            "reason": f"{sid} {kind}: {reason}", "time_in_force": "gtc",
            "position_intent": "buy_to_open" if kind == "entry"
            else "sell_to_close",
            "price_hint": float(price)}


def evaluate(view, ctx=None, sid=SLEEVE_ID):
    view = view or {}
    bars = resample_1min_to_5min(_enj_1min_rows(view))
    if len(bars) < 21:
        return []
    f = source_features(bars)
    last_close_epoch = bars[-1]["_close_epoch"]
    quote = _book_quote(view)
    clock = _capture_epoch(view, quote[2] if quote and quote[2]
                           else last_close_epoch)
    pos = _position(view, sid)
    if pos is not None:
        qty = float(pos["qty"])
        if qty < 0:
            return []  # this sleeve never opens shorts (long-only spot)
        opened = pos.get("opened_at")
        if opened is None:
            return []  # no entry anchor: the stop cannot be reconstructed
        try:
            opened_epoch = _epoch(opened)
        except (TypeError, ValueError):
            return []
        stop, active_from = reconstruct_stop(
            bars, float(pos.get("avg_price") or 0.0), opened_epoch, "long")
        if stop is None or quote is None:
            return []
        bid, _ask, qa = quote
        if qa is None:
            qa = clock
        # observed_quote_stop_trigger, the source's own conditions:
        # a real stop, a quote observed strictly after the stop
        # became active, not stale at the capture clock, bid <= stop.
        if qa > active_from and (clock - qa) <= QUOTE_MAX_AGE_S \
                and bid <= stop:
            return [_intent(sid, "exit", abs(qty), bid,
                            f"observed_quote_stop_trigger stop={stop:.10g}",
                            "exit-quote-stop")]
        return []
    # flat: the source's target decision on the newest completed bar
    if f["short_signal"]:
        return []  # spot long-only overlay: short opening unsupported
    if not f["long_signal"]:
        return []
    if clock - last_close_epoch > BAR_MAX_DECISION_LAG_S:
        return []  # stale_bar_entry_veto bound, source's own 300s
    px = bars[-1]["close"]
    if quote is not None:
        _bid, ask, qa = quote
        if qa is None or (clock - qa) <= QUOTE_MAX_AGE_S:
            px = ask  # the archive sizes a long entry at the ask
    qty = int(_frac_qty(_slice_cash(view), px))
    if qty <= 0:
        return []
    return [_intent(sid, "entry", qty, px, "source_body_impulse",
                    "entry")]
