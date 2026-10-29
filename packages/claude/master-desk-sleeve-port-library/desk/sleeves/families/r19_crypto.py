"""R19 native-spot crypto books (54) — Ausar R17/R18 research variants. The vendored evaluator also registers 9
perpetual collectors (collector_only, initial capital 0: they record the market and never trade); they are not
sleeves here: removed from the desk with their rows (the owner, 2026-10-26: "anything that is not an actual trading
sleeve/strategy can just be removed altogether").

The vendored, hash-pinned evaluator (desk/vendor/ausar_r19/r19_crypto.py, blob b38e9d61) makes every decision;
this wrapper builds its snapshot from public Binance data exactly the way r19_crypto_data.py did:
  * contiguous completed native UTC 4h klines (data-api.binance.vision), with the persistent EMA recurrence
    (EMA20 volume, EMA50 close, seeded at the first bar) that defines absorption shocks/confirmations;
  * depth-snapshot quotes + native lot/tick/notional filters + last-trade clock;
  * USD-M funding from fapi.binance.com — HTTP 451 from US hosts: the funding-conditioned books then carry the
    original blocker FUNDING_SOURCE_HTTP_451 ("no alternate-venue substitution", crypto_rules.json).
Execution, as the R19 ledger's (r19_core.py Ledger._execute, desk.feedlib.r19_ledger): one order per signal and side,
each pass filling min(remaining, displayed size net of what this book already took from that depth snapshot) at the
ask (buy) / bid (sell) on the native lot grid; an entry completes on fresh snapshots inside its 300 s window after
due, an owned exit sells bid-size slices until the book is flat. Native USDT spot books in the sim venue on Binance
quotes, 10 bps per side. Pass clock: the 4h windows (utc_bar:240+0:330: signals, entries, owed-exit starts); while an
owned exit is due and units remain, every pass (the source worker cycled every 30 s): the sleeve sets its own
CONFIG.schedule, which the engine reads each pass, and bind() restores it from the record when a process starts. A
remainder the native filters refuse (below the minimum quantity or notional) stays owed, retried every pass as the
source retried it every cycle.
Named divergences: the ledger's runtime spread execution gate is not applied (desk.feedlib.r19_ledger); a decided
slice goes to the venue as a market order (120 s window) and units it leaves unexecuted return to the order; one
capture per symbol per pass serves its books."""
import dataclasses
import json
import os
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import r19_ledger as L
from ...feedlib.r19_book import reconcile
from ...vendor.ausar_r19 import r19_crypto as vc

SOURCE = {"repo": "codex-complete-archive", "ref": "artifacts/ausar-corrected-incomplete-2026-10-11",
          "commit": "9de774739ab1fd05a9a93f238d50425d4ceda487",
          "path": "digitalocean-pilot/2026-10-11/context/source/backend/r19_crypto.py",
          "blob": "b38e9d6157d40f7f789b0403ae68e6f52ed4e216"}


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def native_rows(klines, fetched_at):
    """klines -> evaluator rows with the persistent absorption recurrence (r19_crypto_data._store semantics)."""
    rows, ind = [], {"count": 0}
    for k in klines:
        c, v, o = Decimal(str(k["c"])), Decimal(str(k["v"])), Decimal(str(k["o"]))
        ema_v = v if ind["count"] == 0 else Decimal(2) / 21 * v + Decimal(19) / 21 * ind["ema_v"]
        ema_c = c if ind["count"] == 0 else Decimal(2) / 51 * c + Decimal(49) / 51 * ind["ema_c"]
        prev = ind.get("prev")
        confirmed = bool(prev and prev["shock"] and c > o and c > (prev["h"] + prev["l"]) / 2)
        shock = v > 2 * ema_v and c < o and c < ema_c
        ind.update(count=ind["count"] + 1, ema_v=ema_v, ema_c=ema_c,
                   prev={"shock": shock, "h": Decimal(str(k["h"])), "l": Decimal(str(k["l"]))})
        rows.append({"open_at": _iso(k["t"]), "close_at": _iso(k["t"] + 14400), "available_at": _iso(max(k["t"] + 14400, fetched_at)),
                     "open": str(k["o"]), "high": str(k["h"]), "low": str(k["l"]), "close": str(k["c"]), "volume": str(k["v"]),
                     "indicator_count": ind["count"], "confirmed_absorption": confirmed})
    return rows


def _relay(feeds, symbol, now):
    from ...feedlib import binance_funding_relay as relay
    root = os.path.dirname(os.path.dirname(feeds.hub.cache.root)) if getattr(feeds.hub, "cache", None) is not None \
        else "."
    try:
        return relay.records(root, symbol, now)
    except Exception:
        return []


def capture(feeds, sleeve, now, symbol):
    """FEED r19_capture:<SYMBOL> — one native capture per symbol per pass (memoised by Feeds, shared by its books). Its reads
    come after the pass clock, so its clocks are theirs (r19_crypto_data.py collect_snapshot: "Captures happened after the
    caller's original clock; never stamp them with that earlier asof. Core must use the completion time"): the depth is read
    last, after the native filters and the last trade, as the source captured it, and the quote carries that read's receipt
    time; observed_at is the capture's completion, the clock its books evaluate at (R19Crypto.signal)."""
    hub = feeds.hub
    clock = getattr(feeds, "clock", None)               # the desk's Feeds always has one; without it, the pass clock
    at = lambda: max(float(now), float(clock())) if callable(clock) else float(now)
    if True:
        cap = {"bar_errors": [], "funding_errors": [], "funding": []}
        try:
            kl = hub.bars("binance", "4h", [symbol], 340).get(symbol) or []
            cap["bars"] = native_rows(kl, now)
        except Exception as e:
            cap["bars"] = []
            cap["bar_errors"].append("SPOT_CAPTURE_UNAVAILABLE:" + type(e).__name__)
        try:
            fr = hub.binance_futures.funding_history(symbol, limit=60)
            cap["funding"] = [{"symbol": symbol, "settled_at": _iso(x["t"]), "received_at": _iso(now), "rate": str(x["rate"]),
                               "observed_public_endpoint": True} for x in fr]
        except Exception as e:
            status = getattr(e, "status", None)
            # Binance refuses US hosts (HTTP 451): the same rate relayed by CoinGecko, sampled before each settlement
            # (desk/feedlib/binance_funding_relay.py, a named divergence); the source's blocker only without it
            relay = _relay(feeds, symbol, now)
            if relay:
                cap["funding"], cap["funding_source"] = relay, "coingecko_relay"
            else:
                cap["funding_errors"].append(f"FUNDING_SOURCE_HTTP_{status}" if status else "FUNDING_SOURCE_UNAVAILABLE:" + type(e).__name__)
        try:
            info = hub.binance.exchange_info(symbol)
            lt = hub.binance.last_trade(symbol)
            d = hub.binance.depth(symbol, 5)
            got = at()                                     # the depth snapshot's receipt
            if not d.get("bids") or not d.get("asks"):
                raise ValueError("empty_depth")
            cap["quote"] = {"symbol": symbol, "bid": d["bids"][0][0], "ask": d["asks"][0][0], "bid_size": d["bids"][0][1],
                            "ask_size": d["asks"][0][1], "market_at": _iso(got), "received_at": _iso(got),
                            "quote_clock_identity": "HTTP_observed_depth_snapshot_no_exchange_quote_time",
                            "quote_key": vc.digest([symbol, d.get("lastUpdateId"), d]), "currency": "USDT",
                            "asset_class": "crypto", "market_kind": "spot", "contract_id": f"BINANCE:SPOT:{symbol}",
                            "feed": "BINANCE_PRODUCTION_PUBLIC_SPOT",          # the source capture's feed identity
                            "contract_received_at": _iso(now - 1), "contract_valid_until": _iso(now + 3600),
                            "step_size": info["qty_step"], "price_tick": info["price_tick"], "minimum_qty": info["minimum_qty"],
                            "maximum_qty": info["maximum_qty"], "min_notional": info["minimum_notional"] or "0",
                            "last_trade_at": _iso(lt) if lt else None}
        except Exception as e:
            cap["bar_errors"].append("SPOT_QUOTE_UNAVAILABLE:" + type(e).__name__)
        cap["observed_at"] = _iso(at())                    # the capture's completion (the source capture's observed_at)
        return cap


FEEDS = {"r19_capture": capture}


def _relay_job(engine):
    from ...feedlib import binance_funding_relay as relay
    return relay.job(engine)


# Binance's funding relay: one read in the last 4.5 minutes before each UTC 4-hour boundary (every settlement of the
# books' symbols falls on one); the full-precision relay is ~10 MB a read
JOBS = {"binance_funding_relay": ("utc_bar:240+14100:14370", 300, _relay_job)}


WINDOW = "utc_bar:240+0:330"          # every rule acts here: signals, entries (due .. due + 300 s), owed-exit starts
OWED = "always"                       # while an owned exit is due and units remain (the source cycled every 30 s)
CHILD_WINDOW_S = 120                  # a decided slice the venue leaves unfilled lapses and returns to its order


def _native(qty, step):
    """the book's units on the native lot grid (the desk book sums fills in floats)."""
    d = Decimal(repr(float(qty or 0)))
    if step and Decimal(str(step)) > 0:
        s = Decimal(str(step))
        d = (d / s).to_integral_value(rounding=ROUND_HALF_EVEN) * s
    return d if d > 0 else Decimal(0)


def _owed(st, sym, now):
    """the held position's owned exit is due (the evaluator's fixed deadline or its scheduled structural exit)."""
    meta = (st.get("metadata") or {}).get(sym) or st.get("position_metadata") or {}
    if not meta.get("exit_due_at"):
        return False
    due = vc.stamp(meta["exit_due_at"])
    tr = st.get("exit_trigger")
    if tr and tr.get("signal_id") == meta.get("signal_id"):
        due = min(due, vc.stamp(tr["execute_at"]))
    return float(now) >= due.timestamp()


class R19Crypto(Sleeve):
    def __init__(self, cfg):
        self.rule = cfg
        sid = cfg["id"].lower()
        self.INST = f"SPOT:BINANCE:{cfg['symbol']}"
        self.CONFIG = SleeveConfig(
            sleeve_id=sid, family="r19_crypto",
            cadence_s=30, universe=(cfg["symbol"],), capital=float(cfg["initial_capital"] or 1.0),
            schedule=WINDOW, status="active", venue_pref="sim:binance",
            needs={"feeds": [f"r19_capture:{cfg['symbol']}"]},
            params={"cost_bps": cfg.get("fee_bps", 10), "family": cfg["family"], "exit_policy": cfg.get("exit_policy"),
                    "capacity": cfg.get("capacity"), "currency": "USDT"},
            source=dict(SOURCE, config_id=cfg["id"]),
            state_schema={"consumed_signals": "list", "candidate": "dict|None", "position_metadata": "dict|None",
                          "ledger": "dict", "inflight": "dict", "metadata": "dict"})

    def _clock(self, owed):
        """the pass clock: the 4h windows, or every pass while an owned exit is due and units remain."""
        want = OWED if owed else WINDOW
        if self.CONFIG.schedule != want:
            self.CONFIG = dataclasses.replace(self.CONFIG, schedule=want)

    def bind(self, engine):
        """a process that starts while an owned exit is due resumes its slices at once (the clock is the record's)."""
        try:
            st = engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}
            book = engine.books.books.get(self.CONFIG.sleeve_id)
            p = (book.positions if book is not None else {}).get(self.INST)
            self._clock(bool(p and float(p["qty"]) > 0) and _owed(st, self.rule["symbol"], engine.clock()))
        except Exception:
            pass

    def signal(self, view):
        cfg = self.rule
        sym = cfg["symbol"]
        cap = view.extra.get(f"r19_capture:{sym}")
        if not cap:
            return []
        st = dict(view.state or {})
        model, inflight, metadata = st.pop("ledger", None) or L.fresh(), st.pop("inflight", None) or {}, \
            st.pop("metadata", None) or {}
        q = cap.get("quote") or {}
        pos = view.positions.get(self.INST)
        owned = held = _native(pos["qty"] if pos else 0, q.get("step_size"))
        working = {p["inst"].rsplit(":", 1)[-1]: p for p in view.extra.get("pending_orders") or []}
        reconcile(model, inflight, {sym: {"quantity": str(owned)}} if owned > 0 else {}, working)
        meta = metadata.get(sym) or st.get("position_metadata")      # the ledger's position metadata, else the
        positions = {sym: {"quantity": str(owned), "metadata": meta}} if owned > 0 else {}    # evaluator's own copy
        # the evaluation clock: the capture's completion, whose reads came after the pass clock (r19_crypto_data.py: "never
        # stamp them with that earlier asof"), as coinbase_sma200.market_of acknowledges a quote at max(pass clock, receipt)
        asof = max(float(view.now), vc.stamp(cap["observed_at"]).timestamp()) if cap.get("observed_at") else float(view.now)
        snapshot = {"asof": _iso(asof), "quotes": {sym: q} if q else {}, "crypto": {sym: cap}}
        book = {"config": cfg, "state": st, "positions": positions, "cash": str(max(0.0, view.cash)), "debt": 0,
                "enabled": True, "activated_at": st.get("activated_at") or _iso(view.now)}
        out = vc.evaluate(snapshot, book)
        state = dict(out["state"], activated_at=book["activated_at"])
        intents = []
        for b in out.get("blockers", []):
            intents.append(Intent("signal", sym, reason=f"blocker: {b}", meta={"blocker": b}, signal_key=f"blk:{b}:{int(view.now//14400)}"))
        # the R19 ledger's execution (r19_core.py Ledger._execute, desk.feedlib.r19_ledger): one order per signal and
        # side, each pass's fill min(remaining, displayed size net of what this book took from that snapshot)
        cash, nav = Decimal(repr(float(view.cash))), Decimal(repr(float(view.equity)))
        held_value, actual = nav - cash, asof + 0.001
        for it in out["intents"]:
            if sym in working:
                continue                                      # the decided remainder is still at the venue
            contract = ((meta or {}).get("contract_id") or q.get("contract_id")) if owned > 0 else None
            fill, why = L.execute(model, cfg["id"], cfg, it, snapshot, owned, cash, nav, held_value, actual,
                                  owned_contract=contract)
            if fill is None:
                if why not in ("target_satisfied", "idempotent"):
                    sid = str(it.get("signal_id"))
                    intents.append(Intent("signal", sym, reason=f"{sid[:12]}: {why}"[:200], meta={"gate": why},
                                          signal_key=f"gate:{sid[:16]}:{why[:40]}"))
                continue
            qty, px = fill["quantity"], fill["price"]
            m = {"cost_bps": float(L.fee_rule(cfg, sym, px)), "signal_id": it["signal_id"], "decided_qty": str(qty),
                 "order_id": fill["order_id"]}
            inflight.setdefault(sym, []).append({"symbol": sym, "side": fill["side"], "quantity": str(qty),
                                                 "before": str(owned), "order_id": fill["order_id"],
                                                 "depth_key": fill["depth_key"], "release_at": None})
            why = f"{cfg['family']}/{cfg.get('exit_policy')}: {it['reason']}: {fill['side']} {qty} at {px}"[:300]
            spec = OrderSpec(type="market", window_s=CHILD_WINDOW_S)
            if fill["side"] == "buy":                         # the ledger's position metadata: the first fill's intent
                pm = dict(meta) if owned > 0 and meta else dict(it.get("metadata") or {})      # metadata, then the
                pm.update(contract_id=fill["contract_id"], asset_class="crypto", last_fill_at=_iso(actual))   # fill's
                meta = metadata[sym] = m["position_meta"] = pm
                cash -= qty * px + fill["fee"]
                owned += qty
                intents.append(Intent("enter", sym, asset="spot", venue="sim:binance", qty=float(qty), price_hint=float(px),
                                      signal_key=f"{it['signal_id']}:buy:{view.now}", reason=why, order=spec, meta=m))
            else:
                owned -= qty                                   # the last slice closes the book's own units exactly
                intents.append(Intent("exit", sym, asset="spot", venue="sim:binance",
                                      qty=float(qty) if owned > 0 else None, price_hint=float(px),
                                      signal_key=f"{it['signal_id']}:sell:{view.now}", reason=why, order=spec, meta=m))
        L.trim(model)
        live = ({sym} if owned > 0 else set()) | set(working) | set(inflight)
        state.update(ledger=model, inflight=inflight, metadata={k: v for k, v in metadata.items() if k in live})
        self._st = state
        self._clock(held > 0 and _owed(state, sym, view.now))
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [R19Crypto(c) for c in vc.register() if not c.get("collector_only")]
