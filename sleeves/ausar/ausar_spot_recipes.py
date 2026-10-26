"""Ausar public recipes on their own Binance spot tapes — PUBLIC_TOMAZETTI_RSI2_SPOT100 (ADAUSDT 1h),
PUBLIC_IU_BODY_SPOT100 (ENJUSDT 5m), PUBLIC_AI_VOLUME_SPOT100 (LINKUSDT 4h): the originals, each a 100k USDT book.

The vendored, hash-pinned reducer decides — strategies/public_recipes/public_source_sleeves.py (blob 834a60ab, sha256
e64c995d = the runtime's SOURCE_SHA): step() on BAR / QUOTE / FILL / CANCEL events, the frozen install configs
(make_config: equity_percent 100, the RSI2 window extended to 2030-12-30; their fhash = the inventory receipt's
config_sha256 c56723c6 / 29d4526f / 028dfd0a), with the runtime's exact chronological IndicatorStream (vendored
backend/public_recipe_runtime.py, blob 5c5f529b) standing in for source_features on every BAR, as the runtime did.
This wrapper is the runtime's process_capture, its receipt machinery left out:

  * every completed native bar of the capture (the 299 of a klines limit-300 read) is validated as a batch, then
    the new ones advance the stream and the reducer in order; a corrected or out-of-order bar, an invalid batch
    or a failed acquisition (exchange metadata, bars, last trade missing or > 60 s before the quote, a non-trading
    contract) blocks this capture's entries: a pending entry target is dropped (an opposite owned position is
    flattened instead), working opening orders are cancelled;
  * an entry target is good for 300 s from its bar's completion (and the reducer's own 300 s TTL); the QUOTE event
    sizes it from the reducer's book cash (100% incl. 10 bps) at the observed ask, floored to the venue lot (the
    native LOT_SIZE x MARKET_LOT_SIZE intersection) and capped by the venue maximum; venue minimum / notional
    refusals cancel it; each fill is bounded by the displayed size net of what earlier fills took from the same
    displayed book (identical body or the same receipt); an opening remainder is cancelled (no pyramid);
  * exits are the reducer's: TOMAZETTI close > SMA5, AI_VOLUME the 5-bar source counter or an opposite spike,
    IU_BODY the trailing 2 x ATR stop triggered by the observed bid; closing orders continue on later quotes;
  * long spot only (a short target is vetoed by the reducer: no short capability on spot).

Removed (plumbing, not the books' rules): the operator enable switch and its journal (the books trade as
installed), the sqlite event journal / checkpoints / receipt-body hashing and its replay verification, the worker
lease. No desk-wide gate existed in this runtime.

Named divergences:
  * pass clock: the source worker cycled every 20 s; these books run every engine pass. Inside a pass the bars,
    metadata, last trade and book ticker are observed in that order and stamped in that order (1 ms apart);
  * acknowledgement: the runtime's local paper fill is applied to the reducer at decision time exactly as the
    runtime did; the engine then books the same quantity at the same observed quote (sim:binance, ask / bid,
    10 bps) — the decided quantity handed to the OMS on its 1e-6 grid unchanged;
  * bars come from the desk's Binance cache (float-decoded klines, the same floats the runtime parsed); a cache
    missing the bar completed at the current boundary is the runtime's bars_unavailable."""
import copy
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from decimal import ROUND_DOWN, Decimal

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import binance_spot_obs
from ...vendor.ausar_ctx.backend import public_recipe_runtime as rt

SOURCE = {"repo": "codex-complete-archive", "ref": "artifacts/ausar-corrected-incomplete-2026-10-11",
          "commit": "9de774739ab1fd05a9a93f238d50425d4ceda487",
          "path": "digitalocean-pilot/2026-10-11/context/source/backend/public_recipe_runtime.py",
          "blob": "5c5f529beb0bff4ce2dcfdbe20881b05ba1a63e1",
          "reducer_blob": "834a60ab5a4ae25e39a5912a9391888f834a823e",
          "manifest_receipt": {"commit": "b2f71e710f05ab2dd9a24caf0548478ea4a4f595",
                               "path": "deployment/2026-10-14/operational-finish/receipts/current-sleeve-inventory.json",
                               "blob": "774beeede77841461a7c923d536ba401ccbcf725"}}
MARKETS = rt.MARKETS                 # strategy -> (symbol, interval, step_ms)
IDS = {s: f"ausar_public_{s}_spot100" for s in MARKETS}
CONFIG_SHA = {"tomazetti_rsi2": "c56723c6d03c6015b03eeb8650406035df7be5e445567c09fdc017da7e5cc7cc",
              "iu_body": "29d4526fd0f505ec6eab5783aeb5f620cf3447edc4996fe5c1e5256c3b49e56f",
              "ai_volume": "028dfd0a1a3a6e7e63992250dd19bb9572b0a17a01637dd545d16427ab57a068"}
TRADE_MAX_AGE = 60
CONTRACT_VALID = 300
KEEP_SEEN = 320
BASE = "https://data-api.binance.vision/api/v3/"
_CORE = None


def core():
    """the reducer exactly as the runtime loads it (sha256-checked, its own module instance)."""
    global _CORE
    if _CORE is None:
        _CORE = rt.load_core()
    return _CORE


def install_config(strategy):
    symbol = MARKETS[strategy][0]
    return core().make_config(strategy, {"symbol": symbol, "market_kind": "spot", "initial_cash": 100000.,
                                         "quantity_mode": "equity_percent", "quantity_value": 100.,
                                         "params": {"window_end": "2030-12-30T00:00:00+00:00"}
                                         if strategy == "tomazetti_rsi2" else {}})


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def sha(x):
    return rt.sha(x)


def oms_qty(q):
    f = float(q)
    while math.floor(f * 1e6) / 1e6 < float(q):
        f = math.nextafter(f, math.inf)
    return f


def raw_exchange_info(symbol):
    from ...data.http import get
    return get(BASE + "exchangeInfo", {"symbol": symbol})


def capture(feeds, sleeve, now, strategy):
    """FEED recipe_capture:<strategy> — one observation per pass in the runtime's capture order: exchange metadata,
    completed native bars, last trade, book ticker; the runtime's acquisition errors."""
    symbol, interval, step_ms = MARKETS[strategy]
    step = step_ms // 1000
    hub = feeds.hub
    cap = {"errors": [], "bars": [], "contract": None, "last_trade_at": None, "quote": None, "metadata_at": now}
    o = binance_spot_obs.observe(feeds, symbol, now, raw_exchange_info)     # one observation a symbol a pass
    try:
        if "info_error" in o:
            raise o["info_error"]
        info = o["info"]
        item = next((s for s in (info or {}).get("symbols", []) if s.get("symbol") == symbol), None)
        if not item or item.get("status") != "TRADING" or item.get("isSpotTradingAllowed") is not True or \
                item.get("quoteAsset") != "USDT" or item.get("baseAsset") != symbol[:-4]:
            cap["errors"].append("production_spot_contract_unavailable")
        else:
            try:
                native = rt.spot_market_constraints(item)
                cap["contract"] = {"id": "binance:exchangeInfo:" + symbol + ":" + str(int(now)),
                                   "source": BASE + "exchangeInfo?symbol=" + symbol, "available_at": iso(now),
                                   "valid_until": iso(now + CONTRACT_VALID), "symbol": symbol, "paper_only": True,
                                   "market_kind": "spot", "max_leverage": 1, "quote_asset": item["quoteAsset"],
                                   **{k: float(v) for k, v in native.items()}, "native_filter_values": native,
                                   "filter_policy": "lot_and_market_intersection_v1"}
            except (ValueError, KeyError, TypeError, IndexError, ArithmeticError):
                cap["errors"].append("metadata_invalid_contract")
    except Exception:
        cap["errors"].append("metadata_unavailable")
        cap["errors"].append("production_spot_contract_unavailable")
    try:
        bl = hub.bars("binance", interval, [symbol], 300).get(symbol) or []
        cap["bars"] = [b for b in bl if b["t"] + step <= now][-299:]
        if not cap["bars"] or cap["bars"][-1]["t"] + step < (int(now) // step) * step:
            cap["errors"].append("bars_unavailable")
    except Exception:
        cap["bars"] = []
        cap["errors"].append("bars_unavailable")
    try:
        if "last_trade_error" in o:
            raise o["last_trade_error"]
        cap["last_trade_at"] = o["last_trade"]
    except Exception:
        cap["errors"].append("last_trade_unavailable")
    if "quote_error" in o:
        raise o["quote_error"]
    q = o["quote"]
    if q and q.get("bid") is not None and q.get("ask") is not None:
        cap["quote"] = {"bid": float(q["bid"]), "ask": float(q["ask"]), "bid_qty": float(q.get("bid_size") or 0.0),
                        "ask_qty": float(q.get("ask_size") or 0.0), "t": float(q.get("t") or now)}
        lt = cap["last_trade_at"]
        if lt:
            if not 0 <= cap["quote"]["t"] - float(lt) <= TRADE_MAX_AGE:
                cap["errors"].append("last_trade_stale_or_future")
        else:
            cap["errors"].append("last_trade_missing")
    return cap


FEEDS = {"recipe_capture": capture}


def fresh_row(strategy):
    c = install_config(strategy)
    st = core().initial_state(strategy, c)
    return {"strategy": strategy, "config": c, "state": st, "indicators": rt.IndicatorStream().state, "seen": {},
            "used": {}, "checkpoint": sha(st), "enabled": True}


class _Pass:
    """one capture: a monotone receipt clock (1 ms per reading, from the pass clock)."""

    def __init__(self, now):
        self.t = float(now)

    def clock(self):
        self.t += 0.001
        return self.t


def _event(row, event, stream=None):
    """PublicRecipeDesk._event without the journal: reducer step + the runtime's owned-order overlay."""
    strategy = row["strategy"]
    state, config = row["state"], row["config"]
    m = core()
    original = m.source_features
    if event["type"] == "BAR":
        feature = stream.push(strategy, config["params"], event["bar"])
        m.source_features = lambda strategy, bars, params: feature
    try:
        result = m.step(strategy, config, state, event)
    finally:
        m.source_features = original
    state = result["state"]
    t = state.get("pending_target")
    if t and t["side"] != "flat" and not t.get("origin_completed_at"):
        origin = next((b for b in state["bars"] if b["open_at"] == t.get("source_bar_open_at")), None)
        if not origin:
            raise ValueError("source target lacks its own origin completion")
        t["origin_completed_at"] = origin["close_at"]
    for intent in result["intents"]:
        if intent["kind"] == "PAPER_ORDER":
            owned = state["orders"][intent["id"]]
            contract = owned["quote_receipts"].get("contract") or (state.get("position") or {}).get("accepted_contract")
            if contract:
                cap, lot = contract["maximum_qty"], contract["qty_step"]
                legal = float((Decimal(str(min(owned["qty"], cap))) / Decimal(str(lot))).to_integral_value(
                    rounding=ROUND_DOWN) * Decimal(str(lot)))
                owned["source_allocation_intended_qty"] = owned["qty"]
                owned["qty"] = legal
                owned["remaining"] = legal
                intent.update(source_allocation_intended_qty=owned["source_allocation_intended_qty"], qty=legal,
                              remaining=legal)
            if intent["action"].startswith("OPEN_"):
                if not t or not t.get("origin_completed_at"):
                    raise ValueError("opening order missing origin completion")
                owned["origin_completed_at"] = t["origin_completed_at"]
                intent["origin_completed_at"] = t["origin_completed_at"]
    if event["type"] == "FILL" and state.get("position"):
        order = state["orders"][event["order_id"]]
        if order["action"] == "OPEN_LONG":
            state["position"]["accepted_contract"] = copy.deepcopy(order["quote_receipts"]["contract"])
            state["position"]["accepted_entry_order_id"] = order["id"]
    state["bars"] = state["bars"][-200:]
    state["source_decisions"] = state["source_decisions"][-5:]
    state["seen_events"] = state["seen_events"][-32:]
    state["event_fingerprints"] = {k: state["event_fingerprints"][k] for k in state["seen_events"]}
    state["fill_ledger"] = state["fill_ledger"][-32:]
    state["cashflow_ledger"] = state["cashflow_ledger"][-32:]
    state["orders"] = {k: v for k, v in state["orders"].items() if v["status"] in ("open", "cancel_requested")}
    if not row["enabled"] and state.get("pending_target") and state["pending_target"]["side"] != "flat":
        if state.get("position") and state["position"]["side"] != state["pending_target"]["side"]:
            state["pending_target"] = {**state["pending_target"], "side": "flat",
                                       "reason": "disabled_entry_preserve_owned_flatten"}
        else:
            state["pending_target"] = None
        result["diagnostics"].append("operator_entry_disabled")
    row["state"] = state
    if stream:
        row["indicators"] = stream.state
    row["checkpoint"] = sha(state)
    return result


def _native(b, step, received_at):
    return {"open_at": iso(b["t"]), "close_at": iso(b["t"] + step), "available_at": received_at,
            "open": float(b["o"]), "high": float(b["h"]), "low": float(b["l"]), "close": float(b["c"]),
            "volume": float(b["v"])}


def process(row, cap, now):
    """PublicRecipeDesk.process_capture on one observation -> (row, fills, notes); fills: (side, qty, price).
    Raises like the runtime (the caller keeps the previous row: the runtime's transaction rolled back)."""
    row = copy.deepcopy(row)
    strategy = row["strategy"]
    symbol, _, step_ms = MARKETS[strategy]
    step = step_ms / 1000
    clk = _Pass(now)
    bars_at = clk.clock()
    q0 = cap.get("quote")
    if not q0:
        raise ValueError("public feed quote unavailable")
    quote_at = max(float(q0.get("t") or now), clk.clock())
    clk.t = quote_at
    qr_id = "bookTicker:" + iso(quote_at)
    stream = rt.IndicatorStream(row["indicators"])
    outputs, fills, notes = [], [], []
    blocked = bool(cap.get("errors"))
    last = row["state"]["bars"]
    last_open = last[-1]["open_at"] if last else None
    offered = [_native(b, step, iso(bars_at)) for b in cap.get("bars") or []]
    m = core()
    try:
        previous_end = None
        received = m.stamp(iso(bars_at))
        for bar in offered:
            op, end, available = m.stamp(bar["open_at"]), m.stamp(bar["close_at"]), m.stamp(bar["available_at"])
            if op.microsecond or int(op.timestamp()) % int(step) or (end - op).total_seconds() != step or \
                    not end <= available <= received or (previous_end is not None and op != previous_end):
                raise ValueError("invalid native completed bar clock")
            values = {k: m.finite(bar[k], k, 0) for k in ("open", "high", "low", "close", "volume")}
            if not 0 < values["low"] <= min(values["open"], values["close"]) <= max(values["open"], values["close"]) \
                    <= values["high"]:
                raise ValueError("invalid native OHLC")
            previous_end = end
    except (ValueError, KeyError, TypeError, ArithmeticError):
        offered = []
        blocked = True
        notes.append("invalid_native_bar_batch_entries_blocked_owned_quote_exits_preserved")
    for bar in offered:
        contents = {k: bar[k] for k in ("open_at", "close_at", "open", "high", "low", "close", "volume")}
        existing = row["seen"].get(bar["open_at"])
        if existing:
            if existing != sha(contents):
                blocked = True
            continue
        if last_open and bar["open_at"] < last_open:
            blocked = True
            continue
        if last_open and (datetime.fromisoformat(bar["open_at"]) - datetime.fromisoformat(last_open)).total_seconds() \
                != step:
            blocked = True
            break
        ev = {"type": "BAR", "id": "bar:" + bar["open_at"], "received_at": iso(bars_at), "symbol": symbol, "bar": bar,
              "source_receipt": {"url": BASE + "klines", "http_body_sha256": None, "native_raw_row": None}}
        outputs.append(_event(row, ev, stream))
        row["seen"][bar["open_at"]] = sha(contents)
        last_open = bar["open_at"]
    if len(row["seen"]) > KEEP_SEEN:
        for k in sorted(row["seen"])[:len(row["seen"]) - KEEP_SEEN]:
            row["seen"].pop(k)
    q = {"asof": iso(quote_at), "bid": q0["bid"], "ask": q0["ask"], "bid_qty": q0["bid_qty"], "ask_qty": q0["ask_qty"]}
    at = datetime.fromisoformat(q["asof"])
    observed_t = clk.clock()
    observed = datetime.fromisoformat(iso(observed_t))
    if not all(isinstance(q[k], (int, float)) and not isinstance(q[k], bool) and math.isfinite(q[k])
               for k in ("bid", "ask")) or not 0 < q["bid"] <= q["ask"]:
        raise ValueError("quote values/actual observation identity invalid")
    if observed < at or (observed - at).total_seconds() > 10:
        raise ValueError("capture quote stale/future at actual processing clock")
    fee = {"id": "paper-cost-model-v1", "source": "Explicit hypothetical10bps each-side fee debit plus actual bid/ask "
           "spread; account-specific fee unavailable", "available_at": iso(cap.get("metadata_at", now)),
           "valid_until": (at + timedelta(minutes=5)).isoformat(), "taker_bps": 10.}
    if blocked or not row["enabled"]:
        s = row["state"]
        t = s.get("pending_target")
        if t and t["side"] != "flat":
            if s.get("position") and s["position"]["side"] != t["side"]:
                s["pending_target"] = {**t, "side": "flat", "reason": "acquisition_entry_block_preserve_owned_flatten"}
            else:
                s["pending_target"] = None
    s = row["state"]
    t = s.get("pending_target")
    window_veto = False
    if t and t["side"] != "flat" and (not t.get("origin_completed_at") or max(at, observed) >=
                                       datetime.fromisoformat(t["origin_completed_at"]) + timedelta(seconds=300)):
        window_veto = True
        if s.get("position") and s["position"]["side"] != t["side"]:
            s["pending_target"] = {**t, "side": "flat", "reason": "missed_opening_preserve_owned_flatten"}
        else:
            s["pending_target"] = None
    for order in list(row["state"]["orders"].values()):
        if order["action"].startswith("OPEN_") and order["status"] in ("open", "cancel_requested") and \
                (blocked or not row["enabled"] or not order.get("origin_completed_at") or
                 observed >= datetime.fromisoformat(order["origin_completed_at"]) + timedelta(seconds=300)):
            cancel = {"type": "CANCEL", "id": "opening-guard-cancel:" + order["id"], "order_id": order["id"],
                      "received_at": iso(clk.clock()), "reason": "acquisition_or_operator_entry_block"
                      if blocked or not row["enabled"] else "original_native_signal_completion_window_expired"}
            outputs.append(_event(row, cancel))
            notes.append(("cancel", order["id"], cancel["reason"]))
            window_veto = True
            observed = datetime.fromisoformat(iso(clk.t))
    ev = {"type": "QUOTE", "id": "quote:" + q["asof"] + ":" + qr_id, "received_at": observed.isoformat(),
          "symbol": symbol, "quote": q, "receipts": {"contract": cap.get("contract"), "fees": fee}}
    s = row["state"]
    p = s.get("position")
    stop_trigger = bool(p and p.get("stop") is not None and datetime.fromisoformat(q["asof"]) >
                        datetime.fromisoformat(p["stop_active_from"]) and q["bid"] <= p["stop"])
    active = any(o["status"] in ("open", "cancel_requested") for o in s["orders"].values())
    local_state_changed = sha(s) != row["checkpoint"]
    if s.get("pending_target") or stop_trigger or active or local_state_changed:
        out = _event(row, ev)
        outputs.append(out)
    else:
        out = {"intents": [], "diagnostics": ["observed_quote_no_financial_obligation"]}
    existing_close = [o for o in row["state"]["orders"].values() if o["status"] == "open"]
    new_ids = {i.get("id") for i in out["intents"] if i["kind"] == "PAPER_ORDER"}
    executable = out["intents"] + [{"kind": "PAPER_ORDER", **o} for o in existing_close if o["id"] not in new_ids]
    for i in out["intents"]:
        if i["kind"] == "ENTRY_VETO":
            notes.append(("veto", i.get("source_side"), ",".join(i.get("reasons") or [])))
    for intent in executable:
        if intent["kind"] == "CANCEL_ORDER":
            cancel = {"type": "CANCEL", "id": "cancel:" + intent["order_id"] + ":" + qr_id, "order_id": intent["order_id"],
                      "received_at": iso(clk.clock())}
            outputs.append(_event(row, cancel))
            notes.append(("cancel", intent["order_id"], "source_cancel"))
            continue
        if intent["kind"] != "PAPER_ORDER":
            continue
        order = intent
        position = row["state"].get("position")
        contract = cap.get("contract") or (position or {}).get("accepted_contract")
        opening = order["action"].startswith("OPEN_")
        if contract is None:
            raise ValueError("owned order lacks accepted contract identity")
        if opening and (order["qty"] < contract["minimum_qty"] or order["qty"] > contract["maximum_qty"] or
                        order["qty"] * order["quote_price"] < contract["minimum_notional"]):
            cancel = {"type": "CANCEL", "id": "filter-veto:" + order["id"], "order_id": order["id"],
                      "received_at": iso(clk.clock())}
            outputs.append(_event(row, cancel))
            notes.append(("cancel", order["id"], "filter-veto"))
            continue
        buy = order["action"] in ("OPEN_LONG", "CLOSE_SHORT")
        px = q["ask"] if buy else q["bid"]
        display = q.get("ask_qty" if buy else "bid_qty")
        if not isinstance(display, (int, float)) or isinstance(display, bool) or not math.isfinite(display) or display < 0:
            raise ValueError("actual displayed quote quantity required for paper fill")
        depth_identity = sha({k: q[k] for k in ("bid", "ask", "bid_qty", "ask_qty")})
        side = "buy" if buy else "sell"
        # every earlier fill against the same displayed book (identical parsed body) on this side; the source also
        # matched its receipt id, the hash of those same body bytes
        used = Decimal(row["used"].get(depth_identity + ":" + side, "0"))
        display = max(Decimal(0), Decimal(str(display)) - used)
        lot = contract["qty_step"]
        qty = float((min(Decimal(str(order.get("remaining", order["qty"]))), display) / Decimal(str(lot)))
                    .to_integral_value(rounding=ROUND_DOWN) * Decimal(str(lot)))
        if qty <= 0:
            continue
        if qty < contract["minimum_qty"] or qty * px < contract["minimum_notional"]:
            if opening:
                cancel = {"type": "CANCEL", "id": "depth-filter-veto:" + order["id"], "order_id": order["id"],
                          "received_at": iso(clk.clock())}
                outputs.append(_event(row, cancel))
                notes.append(("cancel", order["id"], "depth-filter-veto"))
            else:
                notes.append("owned_exit_depth_below_accepted_venue_minimum_unfilled")
            continue
        fill_at = iso(clk.clock())
        fill_clock = datetime.fromisoformat(fill_at)
        if fill_clock - datetime.fromisoformat(q["asof"]) > timedelta(seconds=10):
            if opening:
                cancel = {"type": "CANCEL", "id": "quote-expired:" + order["id"], "order_id": order["id"],
                          "received_at": fill_at, "reason": "observed_quote_expired_before_actual_acknowledgement"}
                outputs.append(_event(row, cancel))
            continue
        if opening:
            origin = datetime.fromisoformat(order["origin_completed_at"])
            valid_clock = all(datetime.fromisoformat(r["available_at"]) <= fill_clock <=
                              datetime.fromisoformat(r["valid_until"]) for r in (cap["contract"], fee))
            if fill_clock >= origin + timedelta(seconds=300) or not valid_clock or \
                    qty * px * 1.001 > row["state"]["book"]["cash"] + 1e-8:
                cancel = {"type": "CANCEL", "id": "actual-fill-veto:" + order["id"], "order_id": order["id"],
                          "received_at": fill_at, "reason": "actual_acknowledgement_origin_receipt_or_cash_guard"}
                outputs.append(_event(row, cancel))
                notes.append(("cancel", order["id"], "actual-fill-veto"))
                window_veto = True
                continue
        fill = {"type": "FILL", "id": "fill:" + order["id"] + ":" + q["asof"], "order_id": order["id"], "qty": qty,
                "price": px, "fees": qty * px * .001, "filled_at": fill_at, "received_at": fill_at, "paper_only": True,
                "actual_quote_receipt_id": qr_id, "displayed_depth_identity": depth_identity,
                "liquidity_side": side, "fill_identity": "Local paper acknowledgement bounded by actual observed "
                "displayed quantity; repeated identical depth is not replenishment evidence"}
        filled = _event(row, fill)
        outputs.append(filled)
        k = depth_identity + ":" + side
        row["used"][k] = str(Decimal(row["used"].get(k, "0")) + Decimal(str(qty)))
        if len(row["used"]) > 128:
            for k in list(row["used"])[:len(row["used"]) - 128]:
                row["used"].pop(k)
        fills.append((side, qty, px, order["id"], order["action"]))
        for follow in filled["intents"]:
            if follow["kind"] == "CANCEL_ORDER":
                cancel = {"type": "CANCEL", "id": "partial-remainder-cancel:" + follow["order_id"] + ":" + qr_id,
                          "order_id": follow["order_id"], "received_at": iso(clk.clock())}
                outputs.append(_event(row, cancel))
                notes.append(("cancel", follow["order_id"], "partial-remainder"))
    if window_veto:
        notes.append("missed_native_opening_window")
    for o in outputs:
        for d in o["diagnostics"]:
            if d in ("stale_bar_entry_veto", "entry_deadline_expired"):
                notes.append(d)
    return row, fills, notes


class SpotRecipe(Sleeve):
    def __init__(self, strategy):
        self.strategy = strategy
        self.symbol, interval, _ = MARKETS[strategy]
        self.inst = "SPOT:BINANCE:" + self.symbol
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[strategy], family="ausar_spot_recipes", cadence_s=20, universe=(self.symbol,),
            capital=100_000.0, schedule="always", venue_pref="sim:binance",
            needs={"feeds": [f"recipe_capture:{strategy}"]},
            params={"cost_bps": 10, "currency": "USDT", "timeframe": interval, "strategy": strategy,
                    "config_sha256": CONFIG_SHA[strategy]},
            source=dict(SOURCE, book="PUBLIC_" + strategy.upper() + "_SPOT100"),
            state_schema={"state": "dict", "indicators": "dict", "seen": "dict", "used": "dict"})

    def signal(self, view):
        cap = view.extra.get(f"recipe_capture:{self.strategy}")
        row = view.state if (view.state and view.state.get("state")) else fresh_row(self.strategy)
        self._st = row
        if not cap or not cap.get("quote"):
            return []
        try:
            row, fills, notes = process(row, cap, view.now)
        except (ValueError, KeyError, TypeError, ArithmeticError) as e:
            return [Intent("signal", self.symbol, reason=f"capture refused: {e}"[:200],
                           signal_key="refused:" + str(e)[:60], meta={"error": str(e)[:200]})]
        self._st = row
        out = []
        held = float((view.positions.get(self.inst) or {}).get("qty") or 0.0)
        mine = (row["state"].get("position") or {}).get("qty") or 0.0
        for side, qty, px, oid, action in fills:
            if side == "buy":
                out.append(Intent("enter", self.symbol, asset="spot", venue="sim:binance", qty=oms_qty(Decimal(str(qty))),
                                  price_hint=px, signal_key=f"{oid}:fill:{view.now}", reason=f"{action} {qty} at the "
                                  f"observed ask {px} ({oid})", order=OrderSpec(type="market", window_s=60),
                                  meta={"order_id": oid, "decided_qty": qty}))
            else:
                out.append(Intent("exit", self.symbol, asset="spot", venue="sim:binance", qty=oms_qty(Decimal(str(qty))),
                                  price_hint=px, signal_key=f"{oid}:fill:{view.now}", reason=f"{action} {qty} at the "
                                  f"observed bid {px} ({oid})", order=OrderSpec(type="market", window_s=60),
                                  meta={"order_id": oid, "decided_qty": qty}))
                held -= qty
        for n in notes:
            if isinstance(n, tuple) and n[0] == "veto":
                out.append(Intent("signal", self.symbol, reason=f"entry veto ({n[1]}): {n[2]}", signal_key=f"veto:{n[2]}",
                                  meta={"veto": n[2]}))
        if not fills and abs(held - float(mine)) > 1e-6:
            out.append(Intent("signal", self.symbol, reason=f"book {held} differs from the reducer's position {mine}",
                              signal_key=f"mismatch:{held}:{mine}", meta={"book_qty": held, "reducer_qty": mine}))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [SpotRecipe(s) for s in ("tomazetti_rsi2", "iu_body", "ai_volume")]
