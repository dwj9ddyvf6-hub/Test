"""Ausar confirmed-absorption books (ABSORPTION_ENJUSDT_4H, ABSORPTION_LINKUSDT_4H) on their own Binance tapes.

The frozen recurrence decides: the vendored, hash-pinned strategies/absorption/signals.py (blob 6b9feadb; the
rule file rules-v1.json, blob 73aa6b5d, sha256 cc56b957 = the runtime's RULE_SHA) — a prior native UTC 4h bar
with volume > 2 x its own-inclusive Decimal EMA20(volume), close < open and close < EMA50(close), then the very
next completed bar closing above its open and above the shock bar's (high + low) / 2. This wrapper carries out
the execution obligations of the source runtime (backend/absorption_runtime.py, blob 6d05c2cd: process_capture /
_execute / the BAR reducer), as the one-book-per-symbol state machine it is:

  * the EMAs are seeded at the first completed bar this book observes and carried across passes exactly (never
    re-seeded): the first pass seeds the 299 completed bars of the source's installation capture (klines limit
    300, the forming bar dropped); a confirmation is admissible from the 300th completed bar on (warmup);
  * every later pass stages the new completed bars in order; a gap, an out-of-order bar or a vendor correction
    to an already-seen bar quarantines the book's entries for good (rules-v1: no new entries on an invalid,
    corrected, missing, late or non-native prefix); owned exits continue;
  * a confirmation is admitted only when first seen < 300 s after its own completion, the book holds no
    position still due after that completion and has no opening order working; otherwise it is recorded with
    the source's reason (warmup / prefix_quarantined / missed_native_opening_window / owned_position_overlap /
    owned_opening_order);
  * the entry: the first observed quote strictly after the signal's receipt and before completion + 300 s, at
    the observed ask, size = 100% of book cash incl. the 10 bps fee, floored to the venue lot (native LOT_SIZE x
    MARKET_LOT_SIZE intersection, the vendored spot_market_constraints), capped by the venue maximum and by the
    displayed ask size; zero displayed size retries on the next fresh quote inside the window, a size below the
    venue minimum drops the signal; the unfilled remainder of a partial entry is cancelled (no pyramid); a pass
    whose acquisition failed (exchange metadata, bars, last trade missing or > 60 s before the quote) drops a
    pending signal; the contract must be current (5 min) and the quote on its tick;
  * the exit: from the original confirmation completion + 16 h (never reset), the first observed bid at or
    after it, the whole position capped by the accepted contract's maximum and the displayed bid size; the
    remainder continues on later distinct quotes; a quote body already consumed on that side is not reused
    and its displayed size is net of what was already taken; exits run before entries;
  * long spot only, no stop, no leverage, no pyramid; 10 bps per side (sim:binance's taker fee = the source FEE).

Removed (desk-wide plumbing, not this book's rules): the explicit operator enable/disable switch and its journal
(the book trades, as its installation enabled it), the sqlite journal / checkpoint / receipt-hash verification
and worker lease. No desk-wide gate existed in this runtime.

Named divergences:
  * pass clock: the source worker cycled every 20 s; this book runs every engine pass (schedule always). The bars,
    exchange metadata, last trade and book ticker are observed in that order inside one pass and the pass clock
    stands for every receipt (the quote counts as observed after the bars, as in the source's fetch order);
  * acknowledgement: the engine fills the decided quantity at the same observed quote in the same pass (sim
    venue, ask / bid, 10 bps) instead of the runtime's synchronous local fill; a fill the venue does not
    complete expires at completion + 300 s (entries) or is re-decided next pass (exits);
  * an exit and an entry never share a pass: the OMS would cross them internally at the mid; the entry is
    decided again on the next pass's fresh quote inside the same 300 s window;
  * bars come from the desk's Binance 4h cache (float-decoded klines re-read as decimal strings — exact for
    Binance's <= 15 significant digits); a cache that lacks the bar completed at the current 4h boundary counts
    as the source's bars_unavailable acquisition error;
  * the decided quantity is handed to the OMS on its 1e-6 fractional grid (a lot quantity whose binary value
    would floor below the lot is nudged up by ulps, never changed in decimal);
  * the book's cash is the desk book's (binary) cash, the source's was a Decimal journal."""
import math
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal, localcontext

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import binance_spot_obs
from ...vendor.ausar_ctx.backend.public_recipe_runtime import spot_market_constraints
from ...vendor.ausar_ctx.strategies.absorption import signals as sig

SOURCE = {"repo": "codex-complete-archive", "ref": "artifacts/ausar-corrected-incomplete-2026-10-11",
          "commit": "9de774739ab1fd05a9a93f238d50425d4ceda487",
          "path": "digitalocean-pilot/2026-10-11/context/source/backend/absorption_runtime.py",
          "blob": "6d05c2cdd13c1c0990bd2ef44743b8689259ca73",
          "signal_blob": "6b9feadba910e10c514f43c141fbe175b9bc6c64",
          "rules_blob": "73aa6b5d3c94e34937e28d73d12d53f9228deedd",
          "manifest_receipt": {"commit": "b2f71e710f05ab2dd9a24caf0548478ea4a4f595",
                               "path": "deployment/2026-10-14/operational-finish/receipts/current-sleeve-inventory.json",
                               "blob": "774beeede77841461a7c923d536ba401ccbcf725"}}
MARKETS = ("ENJUSDT", "LINKUSDT")
D = Decimal
FEE = D("0.001")
STEP = 14400
WINDOW = 300                    # rules-v1 entry_seconds
EXIT_AFTER = 57600              # rules-v1 exit_seconds_after_confirmation_completion (16 h)
WARMUP = 300                    # rules-v1 warmup_completed_bars
SEED = 299                      # completed bars in the installation capture (klines limit 300, forming bar dropped)
QUOTE_MAX_AGE = 10              # rules-v1 quote_max_age_seconds
TRADE_MAX_AGE = 60
CONTRACT_VALID = 300            # the capture's contract: valid 5 minutes from its metadata receipt
KEEP_SEEN = 320
BASE = "https://data-api.binance.vision/api/v3/"


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def ts_of(s):
    return sig.stamp(s).timestamp()


def dec(x):
    """a float observation (the desk's decoded kline / ticker) back to its decimal string."""
    return D(repr(float(x))) if not isinstance(x, (str, D)) else D(str(x))


def lot_floor(value, step):
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def oms_qty(q):
    """the decimal lot quantity as the float the OMS keeps on its 1e-6 grid unchanged."""
    f = float(q)
    while math.floor(f * 1e6) / 1e6 < float(q):
        f = math.nextafter(f, math.inf)
    return f


def source_bar(b):
    """a desk 4h kline -> the source's completed native bar (normalized decimal strings)."""
    raw = {"open_at": iso(b["t"]), "close_at": iso(b["t"] + STEP), "available_at": iso(b["t"] + STEP),
           **{k: format(dec(b[s]), "f") for k, s in (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"),
                                                      ("volume", "v"))}}
    out = sig.normalized_bar(raw, raw["available_at"])
    for key in ("open", "high", "low", "close", "volume"):           # completed_bar(): scale-free content identity
        value = D(out[key])
        text = format(value, "f")
        out[key] = "0" if value == 0 else text.rstrip("0").rstrip(".") if "." in text else text
    return out


def content_key(b):
    return "|".join(b[k] for k in ("open", "high", "low", "close", "volume"))


def contract_from(item, fetched_at, symbol):
    """the capture's accepted spot contract (BinancePublicSpotFeed.capture + AbsorptionPublicFeed.capture)."""
    if not item or item.get("status") != "TRADING" or item.get("isSpotTradingAllowed") is not True or \
            item.get("quoteAsset") != "USDT" or item.get("baseAsset") != symbol[:-4]:
        return None, "production_spot_contract_unavailable"
    try:
        native = spot_market_constraints(item)
    except (ValueError, KeyError, TypeError, IndexError, ArithmeticError):
        return None, "metadata_invalid_contract"
    return dict(native, symbol=symbol, available_at=fetched_at, valid_until=fetched_at + CONTRACT_VALID), None


def raw_exchange_info(symbol):
    from ...data.http import get
    return get(BASE + "exchangeInfo", {"symbol": symbol})


def capture(feeds, sleeve, now, symbol):
    """FEED absorption_capture:<SYMBOL> — one observation per pass: completed 4h bars, exchange metadata, last
    trade, then the book ticker (bid/ask with displayed sizes), with the source's acquisition errors."""
    hub = feeds.hub
    cap = {"errors": [], "bars": [], "contract": None, "last_trade_at": None, "quote": None}
    o = binance_spot_obs.observe(feeds, symbol, now, raw_exchange_info)     # one observation a symbol a pass
    try:
        if "info_error" in o:
            raise o["info_error"]
        info = o["info"]
        item = next((s for s in (info or {}).get("symbols", []) if s.get("symbol") == symbol), None)
        cap["contract"], why = contract_from(item, now, symbol)
        if why:
            cap["errors"].append(why)
    except Exception:
        cap["errors"].append("metadata_unavailable")
    try:
        bl = hub.bars("binance", "4h", [symbol], 300).get(symbol) or []
        cap["bars"] = [b for b in bl if b["t"] + STEP <= now]
        if not cap["bars"] or cap["bars"][-1]["t"] + STEP < (int(now) // STEP) * STEP:
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
    if not q:                                   # the source's separately observed fallback quote: entries blocked
        q = hub.quotes("binance", [symbol], max_age=0).get(symbol)
        cap.update(bars=[], contract=None, last_trade_at=None, errors=["source_capture_failed"])
    if q and q.get("bid") is not None and q.get("ask") is not None:
        cap["quote"] = {"bid": q["bid"], "ask": q["ask"], "bid_qty": q.get("bid_size"), "ask_qty": q.get("ask_size"),
                        "t": float(q.get("t") or now)}
        lt = cap["last_trade_at"]
        if "source_capture_failed" in cap["errors"]:
            pass
        elif lt:
            age = cap["quote"]["t"] - float(lt)
            if not 0 <= age <= TRADE_MAX_AGE:
                cap["errors"].append("last_trade_stale_or_future")
        elif "last_trade_unavailable" not in cap["errors"]:
            cap["errors"].append("last_trade_missing")
    return cap


FEEDS = {"absorption_capture": capture}


def fresh_state():
    return {"indicators": sig.initial_indicators(), "seen": {}, "quarantined": False, "quarantine_reason": None,
            "pending_target": None, "exit_order": None, "last_buy_quote": None, "last_sell_quote": None,
            "last_buy_quote_at": None, "last_sell_quote_at": None, "consumed": {"buy": {}, "sell": {}},
            "signal_count": 0, "last_signal": None, "passes": 0}


def quote_key(q):
    return "|".join(repr(float(q[k])) for k in ("bid", "ask", "bid_qty", "ask_qty"))


def step(st, obs, symbol, defer_entry_after_exit=True):
    """One source capture cycle (process_capture -> exit _execute -> entry _execute) on one observation.

    obs: now, bars (desk 4h klines, completed), quote {bid, ask, bid_qty, ask_qty, t} | None, contract | None,
    last_trade_at, errors, cash, position {qty, meta} | None (the desk book), working (a child of this book
    still working). Returns (state, actions, notes); actions: ("buy"|"sell", qty Decimal, px Decimal, meta).
    defer_entry_after_exit=False lets an entry follow an exit in the same cycle, as the source did (parity only)."""
    with localcontext() as ctx:
        ctx.prec = 34
        return _step(dict(st or fresh_state()), obs, symbol, defer_entry_after_exit)


def _held(position, step_):
    """the desk book quantity on the lot grid (the OMS keeps quantities on a 1e-6 grid)."""
    if not position or float(position.get("qty") or 0) <= 0:
        return D(0)
    q = dec(position["qty"])
    n = (q / step_).to_integral_value()
    return n * step_ if abs(q - n * step_) <= D("0.000002") else lot_floor(q, step_)


def _step(s, obs, symbol, defer):
    import copy
    s = copy.deepcopy(s)
    now = float(obs["now"])
    notes, actions = [], []
    q = obs.get("quote")
    if not q or q.get("bid") is None or q.get("ask") is None or q.get("bid_qty") is None or q.get("ask_qty") is None:
        return s, actions, ["no_observed_quote"]
    quote_at = float(q.get("t") or now)
    at = max(now, quote_at)                 # the acknowledgement clock: the quote is observed after the bars
    bid, ask = dec(q["bid"]), dec(q["ask"])
    if not (bid > 0 and ask > 0) or bid > ask or not 0 <= at - quote_at <= QUOTE_MAX_AGE:
        return s, actions, ["quote_invalid_or_stale"]
    first_pass = s["indicators"]["previous"] is None and not s["seen"]
    # -- bars: the whole offered prefix is validated before any recurrence advances --------------------------
    offered = (obs.get("bars") or [])[-SEED:]
    staged, problem = [], None
    prev = s["indicators"]["previous"]
    last_open = ts_of(prev["open_at"]) if prev else None
    for k in offered:
        try:
            b = source_bar(k)
        except (ValueError, ArithmeticError, KeyError, TypeError) as e:
            problem = str(e)
            break
        old = s["seen"].get(b["open_at"])
        if old is not None:
            if old != content_key(b):
                problem = "vendor correction to immutable completed prefix"
                break
            continue
        op = ts_of(b["open_at"])
        if last_open is not None and op != last_open + STEP:
            problem = "missing/late/out-of-order completed prefix"
            break
        staged.append(b)
        last_open = op
    if problem:
        if not s["quarantined"]:
            s.update(quarantined=True, quarantine_reason=problem, pending_target=None)
            notes.append("prefix_quarantined:" + problem)
        staged = []
    pos = obs.get("position")
    pmeta = ((pos or {}).get("meta") or {}).get("position_meta") or {}
    for b in staged:
        s["indicators"], feature = sig.advance(s["indicators"], b)
        s["seen"][b["open_at"]] = content_key(b)
        if feature["confirmed_absorption"]:
            s["signal_count"] += 1
            origin = ts_of(b["close_at"])
            working_open = obs.get("working") == "enter"
            reason = ("warmup" if feature["completed_count"] < WARMUP else
                      "prefix_quarantined" if s["quarantined"] else
                      "missed_native_opening_window" if now >= origin + WINDOW else
                      "owned_position_overlap" if pos and float(pos.get("qty") or 0) > 0 and
                      float(pmeta.get("exit_due_at", 0)) > origin else
                      "owned_opening_order" if working_open else None)
            cand = {"id": "signal:" + symbol + ":" + b["close_at"], "origin": origin, "first_seen": now,
                    "exit_due_at": origin + EXIT_AFTER}
            s["last_signal"] = dict(cand, admission=reason or "pending_observed_quote")
            if not first_pass:
                notes.append(("signal", cand["id"], reason or "pending_observed_quote"))
            if reason is None:
                s["pending_target"] = cand
    if len(s["seen"]) > KEEP_SEEN:
        for k in sorted(s["seen"])[:len(s["seen"]) - KEEP_SEEN]:
            s["seen"].pop(k)
    errors = list(obs.get("errors") or [])
    blocked = errors + (["prefix_quarantined:" + str(s["quarantine_reason"])] if s["quarantined"] else [])
    t = s["pending_target"]
    if t:
        reason = "acquisition_entry_block" if blocked else \
            "missed_native_opening_window" if at >= t["origin"] + WINDOW else None
        if reason:
            s["pending_target"] = None
            s["last_signal"] = dict(s.get("last_signal") or {}, execution_skip_reason=reason)
            notes.append(("skip", t["id"], reason))
    qk = quote_key(q)
    exited = _exit(s, obs, q, qk, quote_at, at, bid, actions, notes)
    if exited and defer:
        if s["pending_target"]:
            notes.append("entry_deferred_after_exit")
    else:
        if exited:                                      # the source's book after this exit fill: units and cash
            _, q_out, px_out, _ = actions[-1]
            obs = dict(obs, position=_after_exit(obs.get("position"), q_out),
                       cash=str(dec(obs.get("cash") or 0) + q_out * px_out - q_out * px_out * FEE))
        _entry(s, obs, q, qk, quote_at, at, ask, blocked, actions, notes, symbol)
    s["passes"] = int(s.get("passes", 0)) + 1
    return s, actions, notes


def _after_exit(pos, qty):
    left = dec(pos["qty"]) - qty
    return None if left <= D("0.000002") else dict(pos, qty=float(left))


def _dup(s, side, qk, quote_at):
    return s["last_" + side + "_quote"] == qk or (s["last_" + side + "_quote_at"] is not None and
                                                    quote_at <= float(s["last_" + side + "_quote_at"]))


def _consume(s, side, qk, qty, quote_at):
    c = s["consumed"][side]
    c[qk] = str(D(c.get(qk, "0")) + qty)
    if len(c) > 64:
        for k in list(c)[:len(c) - 64]:
            c.pop(k)
    s["last_" + side + "_quote"] = qk
    s["last_" + side + "_quote_at"] = quote_at


def _exit(s, obs, q, qk, quote_at, now, bid, actions, notes):
    pos = obs.get("position")
    pmeta = ((pos or {}).get("meta") or {}).get("position_meta") or {}
    if not pos or float(pos.get("qty") or 0) <= 0 or not pmeta:
        s["exit_order"] = None
        return False
    if _dup(s, "sell", qk, quote_at):
        notes.append("duplicate_sell_quote_depth_ignored")
        return False
    due = float(pmeta["exit_due_at"])
    if now < due or quote_at < due:
        return False
    if obs.get("working") == "exit":
        return False                                    # the decided remainder is still working at the venue
    c = pmeta["contract"]
    lot, tick = D(c["qty_step"]), D(c["price_tick"])
    held = _held(pos, lot)
    qty = lot_floor(min(held, D(c["maximum_qty"])), lot)
    if lot_floor(bid, tick) != bid:
        notes.append("owned_exit_quote_off_accepted_tick_unfilled")
        return False
    if qty <= 0 or qty < D(c["minimum_qty"]) or qty * bid < D(c["minimum_notional"]):
        notes.append("owned_exit_below_accepted_venue_minimum_unfilled")
        return False
    order = s.get("exit_order")
    if not order or order.get("entry_id") != pmeta.get("entry_id"):
        order = s["exit_order"] = {"entry_id": pmeta.get("entry_id"), "qty": str(qty), "remaining": str(qty)}
    depth = max(D(0), dec(q["bid_qty"]) - D(s["consumed"]["sell"].get(qk, "0")))
    fill = lot_floor(min(D(order["remaining"]), depth, D(c["maximum_qty"])), lot)
    if fill <= 0:
        notes.append("zero_executable_displayed_depth")
        return False
    if fill < D(c["minimum_qty"]) or fill * bid < D(c["minimum_notional"]):
        notes.append("owned_exit_depth_below_accepted_venue_minimum_unfilled")
        return False
    order["remaining"] = str(D(order["remaining"]) - fill)
    if D(order["remaining"]) == 0:
        s["exit_order"] = None
    _consume(s, "sell", qk, fill, quote_at)
    actions.append(("sell", fill, bid, {"entry_id": pmeta.get("entry_id"), "quote": qk}))
    return True


def _entry(s, obs, q, qk, quote_at, now, ask, blocked, actions, notes, symbol):
    if _dup(s, "buy", qk, quote_at):
        notes.append("duplicate_buy_quote_depth_ignored")
        return
    t = s["pending_target"]
    pos = obs.get("position")
    if not t or (pos and float(pos.get("qty") or 0) > 0) or obs.get("working") or s["quarantined"] or blocked:
        return
    if not (t["first_seen"] <= quote_at <= now < t["origin"] + WINDOW):
        s["pending_target"] = None
        notes.append(("skip", t["id"], "acknowledgement_origin_window_or_source_clock_guard"))
        return
    c = obs.get("contract")
    try:
        if not c or not float(c["available_at"]) <= now <= float(c["valid_until"]):
            raise ValueError("contract unavailable/stale at acknowledgement")
        for k in ("price_tick", "qty_step", "maximum_qty"):
            if not D(c[k]) > 0:
                raise ValueError("finite positive/nonnegative observation required")
        lt = obs.get("last_trade_at")
        if lt is None or not 0 <= quote_at - float(lt) <= TRADE_MAX_AGE:
            raise ValueError("raw last-trade clock stale or unavailable")
        tick = D(c["price_tick"])
        if any(lot_floor(dec(q[k]), tick) != dec(q[k]) for k in ("bid", "ask")):
            raise ValueError("observed quote violates current venue price tick")
    except (ValueError, KeyError, TypeError, ArithmeticError) as e:
        s["pending_target"] = None
        notes.append(("skip", t["id"], "contract_guard:" + str(e)))
        return
    lot, mx = D(c["qty_step"]), D(c["maximum_qty"])
    cash = dec(obs.get("cash") or 0)
    intended = cash / (ask * (D(1) + FEE))
    qty = lot_floor(min(intended, mx), lot)
    if qty < D(c["minimum_qty"]) or qty * ask < D(c["minimum_notional"]) or qty <= 0:
        s["pending_target"] = None
        notes.append(("skip", t["id"], "cash_or_venue_minimum"))
        return
    depth = max(D(0), dec(q["ask_qty"]) - D(s["consumed"]["buy"].get(qk, "0")))
    fill = lot_floor(min(qty, depth, mx), lot)
    if fill <= 0:
        notes.append(("retry", t["id"], "observed_zero_executable_depth"))   # the candidate stays for a fresh quote
        return
    if fill < D(c["minimum_qty"]) or fill * ask < D(c["minimum_notional"]):
        s["pending_target"] = None
        notes.append(("drop", t["id"], "observed_depth_below_venue_minimum"))
        return
    s["pending_target"] = None
    _consume(s, "buy", qk, fill, quote_at)
    if fill < qty:
        notes.append(("drop", t["id"], "opening_partial_remainder_cancelled_no_pyramid"))
    contract = {k: str(c[k]) for k in ("price_tick", "qty_step", "minimum_qty", "maximum_qty", "minimum_notional")}
    actions.append(("buy", fill, ask, {"entry_id": t["id"], "origin": t["origin"], "exit_due_at": t["exit_due_at"],
                                       "intended": str(intended), "contract": contract}))


class Absorption(Sleeve):
    def __init__(self, symbol):
        self.symbol = symbol
        self.inst = "SPOT:BINANCE:" + symbol
        self.CONFIG = SleeveConfig(
            sleeve_id=f"ausar_absorption_{symbol.lower()}_4h", family="absorption", cadence_s=20,
            universe=(symbol,), capital=100_000.0, schedule="always", venue_pref="sim:binance",
            needs={"feeds": [f"absorption_capture:{symbol}"]},
            params={"cost_bps": 10, "currency": "USDT", "timeframe": "4h", "warmup": WARMUP, "entry_seconds": WINDOW,
                    "exit_seconds": EXIT_AFTER, "rule_sha256": "cc56b9572a8a3f1c2e8370c92961ad7238fcde5d65c3a08568c6decc182b0659"},
            source=dict(SOURCE, book="ABSORPTION_" + symbol + "_4H"),
            state_schema={"indicators": "dict", "seen": "dict", "pending_target": "dict|None", "exit_order": "dict|None"})

    def observe(self, view):
        cap = view.extra.get(f"absorption_capture:{self.symbol}") or {}
        pos = view.positions.get(self.inst)
        working = None
        for p in view.extra.get("pending_orders") or []:
            if p["inst"] == self.inst:
                working = "exit" if p["action"] == "exit" else "enter"
        return {"now": view.now, "bars": cap.get("bars") or [], "quote": cap.get("quote"), "contract": cap.get("contract"),
                "last_trade_at": cap.get("last_trade_at"), "errors": cap.get("errors") or [], "cash": view.cash,
                "position": pos, "working": working}

    def signal(self, view):
        if not view.extra.get(f"absorption_capture:{self.symbol}"):
            self._st = None
            return []
        st, actions, notes = step(view.state or None, self.observe(view), self.symbol)
        self._st = st
        out = []
        for n in notes:
            if isinstance(n, tuple):
                kind, sid, why = n
                if kind not in ("signal", "skip"):
                    continue
                out.append(Intent("signal", self.symbol, reason=f"confirmed absorption {sid}: {why}" if kind == "signal"
                                  else f"entry skipped {sid}: {why}", signal_key=f"{kind}:{sid}",
                                  meta={"signal_id": sid, "admission" if kind == "signal" else "skip": why}))
        for side, qty, px, m in actions:
            if side == "buy":
                out.append(Intent("enter", self.symbol, asset="spot", venue="sim:binance", qty=oms_qty(qty),
                                  price_hint=float(px), signal_key=m["entry_id"] + ":entry",
                                  reason=f"confirmed absorption {m['entry_id']}: buy {qty} at the observed ask {px}",
                                  order=OrderSpec(type="market", not_after=m["origin"] + WINDOW, window_s=WINDOW),
                                  meta={"position_meta": {"entry_id": m["entry_id"], "exit_due_at": m["exit_due_at"],
                                                          "origin": m["origin"], "contract": m["contract"],
                                                          "qty": str(qty)}, "decided_qty": str(qty)}))
            else:
                out.append(Intent("exit", self.symbol, asset="spot", venue="sim:binance", qty=oms_qty(qty),
                                  price_hint=float(px), signal_key=f"{m['entry_id']}:exit:{m['quote']}",
                                  reason=f"16h exit of {m['entry_id']}: sell {qty} at the observed bid {px}",
                                  order=OrderSpec(type="market", window_s=60), meta={"decided_qty": str(qty)}))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [Absorption(s) for s in MARKETS]
