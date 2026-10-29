"""Ausar Daily20 — the frozen R11 daily twenty-bar forecasts as two independent paper books (family ausar_daily20):
ausar_daily20_price_volume (D20_PV / D20PV) and ausar_daily20_tensor (D20_TENSOR / D20TENSOR).

The vendored, hash-pinned source decides (agentic-trading-desk aurelia-paper-desk @1720157f, desk-source):
  backend/tensor_daily_models.py (blob e3471f49) — the C01 numerical tree models, their frozen assets
      (strategies/tensor_daily20/models: MANIFEST 9be2845e, both 100-tree models, the 1,817 canonical daily source
      anchors with each name's origin, endpoint ordinal and phase) and evaluate_daily20 / rank_daily20;
  backend/tensor_engine.py over the frozen Tensor v690 engine (strategies/tensor_state_repair/engine, SOURCE_MANIFEST
      5f38a63a, run under Node) — the full native feature rows the models read;
  strategies/enrollment-1d.json (the fixed 1,815-name R12 enrollment) and verified-ineligible-assets.json.
This module carries out the source runtime's D20 rules (backend/tensor_runtime.py: install config, _finish_symbol,
_finish_cycle census and ranking, _entry sizing, _exits):

  producer (job ausar_daily20, each weekday evening after the close): every enrolled name's canonical daily tape
      from its anchored first session (Yahoo daily — the installation's expected_bar_provider), identity-checked
      against its anchor (first timestamp and the original endpoint ordinal); a name whose newest ordinal is in its
      phase (ordinal % 20 = anchor phase) is computed by the engine and evaluated by both models; a selected decision
      becomes a candidate unless inside its cooldown (next eligible ordinal = selected ordinal + 20); the census
      (exclude_unavailable_with_census_receipts): every enrolled name assessed and >= 99% known
  books: in the next regular opening's window (300 s): owed exits first — 20 observed sessions from the entry
      session's opening -> sell the whole position at the next opening; while an exit is pending no entry is ranked;
      then the ranked candidates (prediction descending, symbol) while slots remain (10 including pending), each
      with a quote observed at/after the opening: shares = floor((min(10% equity, 1% of its 20-session dollar
      volume, cash) - $0 fee) / (price x (1 + max(10 bps, 10 bps slippage)))), market order (marketable limit).

Removed (runtime-wide, not the books' rules): the installation enable flag / operator pause, the storage and
transaction fences, the corporate-action probe service and its 'post-seed split' entry deferral (desk-wide action
verification), the receipt/outbox journal.

Named divergences (counted in docs/receipts/parity/ausar_daily20.json):
  D1 canonical tapes: today's Yahoo daily bars (split-adjusted as of the fetch) from each anchor's first session
     stand in for the runtime's seeded research tapes + forward Yahoo revisions; a vendor bar inside the frozen prefix
     at a session the name's pinned seed does not hold is quarantined, as the source's merge does
     (tensor_runtime._merge: "quarantined_vendor_backfill_inside_immutable_native_prefix", ordinals not shifted) --
     the sessions are in tensor_daily20/seed_sessions_1d.json, read from each name's R11 seed member (whose sha256 is
     the anchor's input_sha256); a name whose tape still does not match its anchor (origin or endpoint ordinal) is
     'failed' in the census, as in the source. Without the quarantine (to 2026-10-26) the vendor's 2026-09-22, which
     1,620 seeds lack (2021-05-05 two others), failed 1,623 of the 1,815 names every evening (known 0.1058).
  D2 off-phase names: a name whose newest ordinal is not in its phase (it cannot be selected that day) is assessed
     from its tape identity alone — the engine is run only for in-phase names (about 1 in 20 per day); it is
     labelled phase_not_selected where the source would name an earlier rule (price, liquidity, ATR, readiness):
     the same outcome, the same census status.
  D3 exit clock: the 20 observed bars are counted on the exchange calendar from the entry fill's session.
  D4 prices: the sizing price is the desk quote's last trade (its mid when absent); the order is a marketable limit
     at the ask held for the opening window, capped at the price the shares were sized on (sizing price x 1.001: the
     source's market order within its debit cap); the owed exit is the source's market order."""
import json
import os
import time
from datetime import timezone
from decimal import ROUND_FLOOR, Decimal

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...util import read_json, write_json_atomic
from ...vendor.ausar_tensor import tensor_daily_models as TD
from ...vendor.ausar_tensor import tensor_engine as TE

SOURCE = {"repo": "agentic-trading-desk", "ref": "aurelia-paper-desk", "commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
          "path": "ausar-archive/ausar-receiver/original-payload/desk-source/backend/tensor_daily_models.py",
          "blob": "e3471f490d39d9fa033966d5507c97bd7c97676d",
          "runtime": "ausar-archive/ausar-receiver/original-payload/desk-source/backend/tensor_runtime.py"}
BOOKS = (("ausar_daily20_price_volume", "D20_PV", "price_volume"),
         ("ausar_daily20_tensor", "D20_TENSOR", "price_volume_plus_tensor"))
STRATEGIES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                          "strategies")
HOLD_BARS, MAX_SLOTS, CAP_EQUITY, CAP_DV, SLIPPAGE, FEE = 20, 10, Decimal(".10"), Decimal(".01"), Decimal(".001"), Decimal(0)
WINDOW_S = 300
KNOWN_FRACTION = 0.99
FEED = "ausar_daily20"
UTC = timezone.utc


def out_dir(root):
    return os.path.join(root, "cache", "ausar_daily20")


def enrollment():
    return list(json.load(open(os.path.join(STRATEGIES, "enrollment-1d.json")))["symbols"])


def verified_ineligible():
    doc = json.load(open(os.path.join(STRATEGIES, "verified-ineligible-assets.json")))
    return {r["asset"]["symbol"] for r in doc.get("records") or []}


SEED_SESSIONS = os.path.join(STRATEGIES, "tensor_daily20", "seed_sessions_1d.json")
_SEEDS = {}


def seed_sessions():
    """{symbol: {"seed_sha256", "non_seed_sessions"}} -- the XNYS sessions inside each name's frozen prefix that its
    pinned R11 research seed does not hold (D1)."""
    if not _SEEDS:
        _SEEDS.update(json.load(open(SEED_SESSIONS))["names"])
    return _SEEDS


def non_seed_sessions(symbol):
    return frozenset((seed_sessions().get(symbol) or {}).get("non_seed_sessions") or ())


def tape(bars, anchor):
    """the canonical tape: completed daily bars from the anchor's first session, less the vendor's bars inside the
    frozen prefix at sessions the pinned seed does not hold (D1: the source quarantines them); (bars, None) or
    (None, reason)."""
    opens = [cal.session_open(d) for d in sorted(non_seed_sessions(anchor.symbol))]
    rows = [b for b in bars or [] if int(b["t"]) >= anchor.first_timestamp
            and not (int(b["t"]) <= anchor.last_timestamp and any(abs(float(b["t"]) - o) < 43200 for o in opens))]
    if not rows or int(rows[0]["t"]) != anchor.first_timestamp:
        return None, "canonical_origin_differs"
    if int(rows[-1]["t"]) >= anchor.last_timestamp:
        if len(rows) < anchor.original_rows or int(rows[anchor.original_rows - 1]["t"]) != anchor.last_timestamp:
            return None, "canonical_endpoint_ordinal_differs"
    return rows, None


def native_bars(rows, fetched_ms):
    out = []
    for b in rows:
        t = int(b["t"])
        d = cal._as_date(t)
        done = int(cal.session_close(d) * 1000)
        out.append(TE.NativeBar(timestamp_ms=t * 1000, completed_at_ms=done, usable_at_ms=max(done, fetched_ms),
                                open=float(b["o"]), high=float(b["h"]), low=float(b["l"]), close=float(b["c"]),
                                volume=float(b.get("v") or 0.0), executable_at_ms=int(cal.session_open(d) * 1000)))
    return out


def assess(symbol, bars, now_ms, ineligible=frozenset(), engine=None):
    """one enrolled name -> (status, reason, {sleeve: decision dict}) as the runtime's _finish_symbol records it."""
    try:
        anchor = TD.anchor_for(symbol)
    except TD.DailyModelInputError as e:
        return "failed", str(e), {}
    rows, why = tape(bars, anchor)
    if rows is None:
        return "failed", why, {}
    i = len(rows) - 1
    if symbol in TD.EXCLUDED_SYMBOLS:
        return "ineligible", "excluded_symbol", {}
    if symbol in ineligible:
        return "ineligible", "verified_ineligible_asset", {}
    if len(rows) < 234:
        return "ineligible", "native_history_warming", {}
    if i % 20 != anchor.phase:                                  # D2: it cannot be selected at this ordinal
        return "ready", "phase_not_selected", {}
    try:
        hist = (engine or TE.extract_native_feature_rows)(symbol, "1d", native_bars(rows, now_ms), as_of_ms=now_ms)
        decisions = TD.evaluate_daily20(symbol, list(hist.rows), as_of_ms=now_ms)
    except (TE.TensorEngineError, TD.DailyModelInputError, ValueError, KeyError) as e:
        return "failed", f"{type(e).__name__}: {str(e)[:160]}", {}
    out = {}
    for d in decisions:
        out[d.sleeve_id] = {"symbol": symbol, "bar_index": d.bar_index, "score": d.score, "selected": d.selected,
                            "reason": d.reason, "threshold": d.threshold, "close": d.close,
                            "dollar_volume20": d.dollar_volume20, "decision_at_ms": d.decision_at_ms}
    return "ready", "evaluated", out


def run(root, hub, clock=time.time, engine=None, symbols=None, bars=None):
    """the producer cycle after a session's close: census + ranked candidates per book -> decisions.json."""
    now = clock()
    d = cal._as_date(now)
    if not (cal.is_trading_day(d) and now >= cal.session_close(d) + 900):
        d = cal.prev_trading_day(d)
    origin = d.isoformat()
    names = symbols or enrollment()
    inel = verified_ineligible()
    got = bars if bars is not None else hub.bars("yahoo", "1d", names, 2800)
    now_ms = int(now) * 1000                                  # whole seconds: the native clocks are second-aligned
    cool_path = os.path.join(out_dir(root), "cooldowns.json")
    cool = read_json(cool_path, {}) or {}
    reads, cands = {}, {sid: [] for _, sid, _ in BOOKS}
    for sym in names:
        bl = [b for b in got.get(sym) or [] if cal._as_date(float(b["t"])) <= d]
        status, reason, dec = assess(sym, bl, now_ms, inel, engine)
        reads[sym] = {"status": status, "reason": reason}
        for _, sid, _ in BOOKS:
            x = dec.get(sid)
            if not x or not x["selected"]:
                continue
            prior = (cool.get(sid) or {}).get(sym)
            if prior and prior["origin"] != origin and x["bar_index"] < prior["next"]:
                continue                                        # inside its 20-bar cooldown
            cool.setdefault(sid, {})[sym] = {"next": x["bar_index"] + HOLD_BARS, "origin": origin}
            cands[sid].append(x)
    bad = sorted(s for s, r in reads.items() if r["status"] == "failed")
    known = (len(reads) - len(bad)) / len(names) if names else 0.0
    census = {"enrollment_count": len(names), "assessed_count": len(reads), "known_valid_or_ineligible": len(reads) - len(bad),
              "known_fraction": known, "minimum_forward_known_fraction": KNOWN_FRACTION,
              "unknown_entry_blocked_symbols": bad[:200], "unknown_count": len(bad),
              "entries_admissible": len(reads) == len(names) and (not bad or known >= KNOWN_FRACTION)}
    nxt_open = cal.session_open(cal.next_trading_day(d))
    doc = {"origin": origin, "computed_at": now, "next_open": nxt_open, "expires": nxt_open + WINDOW_S,
           "census": census, "candidates": {sid: sorted(c, key=lambda x: (-x["score"], x["symbol"]))
                                            for sid, c in cands.items()},
           "in_phase": sum(1 for r in reads.values() if r["reason"] == "evaluated")}
    write_json_atomic(cool_path, cool)
    write_json_atomic(os.path.join(out_dir(root), "decisions.json"), doc)
    return {"origin": origin, "assessed": len(reads), "failed": len(bad), "in_phase": doc["in_phase"],
            "candidates": {k: len(v) for k, v in cands.items()}, "admissible": census["entries_admissible"]}


_DOC = {}


def load(root):
    p = os.path.join(out_dir(root), "decisions.json")
    try:
        m = os.path.getmtime(p)
    except OSError:
        return None
    if _DOC.get("path") != p or _DOC.get("mtime") != m:
        _DOC.update(path=p, mtime=m, doc=read_json(p, None))
    return _DOC.get("doc")


def _feed(feeds, sleeve, now, arg):
    """FEED ausar_daily20: the producer's latest census + ranked candidates."""
    root = getattr(getattr(sleeve, "engine", None), "root", None)
    return load(root) if root else None


def _job(engine):
    """once per completed session: a later launch in the same evening finds its decisions written and returns."""
    now = engine.clock()
    d = cal._as_date(now)
    if not (cal.is_trading_day(d) and now >= cal.session_close(d) + 900):
        d = cal.prev_trading_day(d)
    have = load(engine.root) or {}
    if have.get("origin") == d.isoformat():
        return {"origin": have["origin"], "skipped": "decisions already written for this session"}
    return run(engine.root, engine.hub, clock=engine.clock)


def exit_session(entry_session):
    """D3: the opening that follows the 20th observed session counted from the entry session (entry + 20)."""
    return cal.next_trading_day(entry_session, HOLD_BARS).isoformat()


def _price(q):
    last = q.get("last")
    if last:
        return float(last)
    if q.get("bid") and q.get("ask"):
        return (float(q["bid"]) + float(q["ask"])) / 2
    return None


class Daily20Book(Sleeve):
    def __init__(self, sleeve_id, sid, model):
        self.sid, self.model = sid, model
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="ausar_daily20", cadence_s=30, universe=(), capital=100000.0,
            needs={"quotes": {"source": "equity"}, "feeds": [FEED]}, schedule="open+0:open+5",
            params={"sleeve": sid, "model": model, "hold_native_bars": HOLD_BARS, "maximum_slots": MAX_SLOTS,
                    "entry_cap_equity": 0.10, "entry_cap_native_dv": 0.01, "opening_window_seconds": WINDOW_S,
                    "missing_data_policy": "exclude_unavailable_with_census_receipts", "slippage_bps": 10,
                    "fees_per_order": 0},
            source=dict(SOURCE), state_schema={"entries": "dict"})
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def _doc(self):
        root = getattr(self.engine, "root", None)
        return load(root) if root else None

    def quote_universe(self, now, book=None):
        syms = [i.split(":", 1)[1] for i in (getattr(book, "positions", None) or {}) if i.startswith("EQ:")]
        doc = self._doc()
        if doc and doc.get("next_open") and doc["next_open"] <= now < doc["expires"]:
            syms += [c["symbol"] for c in (doc.get("candidates") or {}).get(self.sid, [])[:32] if c["symbol"] not in syms]
        return syms

    def signal(self, view):
        st = dict(view.state or {})
        entries = dict(st.get("entries") or {})
        now = view.now
        d = cal._as_date(now)
        out = []
        held = {i.split(":", 1)[1]: p for i, p in (view.positions or {}).items() if i.startswith("EQ:") and p["qty"] > 0}
        for sym in list(entries):
            if sym not in held:
                entries.pop(sym)
        for sym, p in held.items():
            e = entries.setdefault(sym, {"entry_session": cal._as_date(float(p.get("opened_at") or now)).isoformat()})
            if not cal.is_trading_day(d) or d.isoformat() < exit_session(e["entry_session"]):
                continue
            if not cal.session_open(d) <= now < cal.session_open(d) + WINDOW_S:
                continue                                         # an owed exit waits for an opening window
            q = (view.quotes or {}).get(sym) or {}
            if not q.get("bid"):
                continue                                         # quote acquisition retries in the window
            # the source's exit is a market order for the opening window (tensor_runtime._exits order_type "market"):
            # a limit pinned at IEX's bid rests unfilled on a sim touch wider than IEX's book, at every opening
            out.append(Intent("exit", sym, qty=None, order=OrderSpec(type="market", window_s=WINDOW_S,
                                                                     not_after=cal.session_open(d) + WINDOW_S),
                              price_hint=float(q["bid"]), signal_key=f"{self.sid}:{sym}:{e['entry_session']}:exit",
                              reason=f"{self.sid} exit: 20 observed native bars from the entry session"))
        pending = view.extra.get("pending_orders") or []
        doc = view.extra.get(FEED) or self._doc()
        if out or any(p.get("action") == "exit" for p in pending):
            self._st = dict(st, entries=entries)
            return out                                           # risk-reducing exits first, then a fresh ranking
        if not doc or not (doc["next_open"] <= now < doc["expires"]):
            self._st = dict(st, entries=entries)
            return out
        census = doc.get("census") or {}
        if not census.get("entries_admissible"):
            out.append(Intent("signal", self.sid, reason=f"{self.sid}: incomplete enrollment cycle "
                              f"(known {census.get('known_fraction', 0):.4f})", signal_key=f"{doc['origin']}:census"))
            self._st = dict(st, entries=entries)
            return out
        busy = set(held) | {p["inst"].split(":", 1)[1] for p in pending if p.get("action") == "enter"}
        equity, cash = Decimal(repr(view.equity)), Decimal(repr(view.cash))
        for c in (doc.get("candidates") or {}).get(self.sid, []):
            sym = c["symbol"]
            if sym in busy:
                continue
            if len(busy) >= MAX_SLOTS:
                break
            q = (view.quotes or {}).get(sym) or {}
            px = _price(q)
            if not px or not q.get("ask") or float(q.get("t") or now) < doc["next_open"]:
                continue                                         # a quote at/after the opening is required
            price = Decimal(repr(px))
            effective = price * (1 + max(Decimal(".001"), SLIPPAGE))
            cap = min(equity * CAP_EQUITY, Decimal(repr(c["dollar_volume20"])) * CAP_DV, cash)
            budget = cap - FEE
            shares = int((budget / effective).to_integral_value(rounding=ROUND_FLOOR)) if budget > 0 else 0
            if shares < 1:
                continue
            cash -= shares * effective
            busy.add(sym)
            # D4: a marketable limit (the OMS's, from the ask) whose cost stays within the price the shares were sized
            # on; a limit pinned at IEX's ask was refused by a sim touch wider than IEX's book at an unchanged quote
            out.append(Intent("enter", sym, side="long", qty=float(shares), price_hint=float(q["ask"]),
                              order=OrderSpec(type="marketable_limit", cap_price=float(effective), window_s=WINDOW_S,
                                              not_after=doc["expires"]),
                              signal_key=f"{self.sid}:{sym}:{doc['origin']}",
                              reason=f"{self.sid}: ranked funded opportunity score={c['score']:.5f} "
                                     f"(threshold {c['threshold']:.5f}, ordinal {c['bar_index']})",
                              meta={"daily20": {k: c[k] for k in ("score", "bar_index", "threshold", "dollar_volume20")}}))
        self._st = dict(st, entries=entries)
        return out

    def update_state(self, view, intents):
        return self._st


def sleeves():
    return [Daily20Book(sleeve_id, sid, model) for sleeve_id, sid, model in BOOKS]


FEEDS = {FEED: _feed}
JOBS = {"ausar_daily20": ("weekday:12345&et:16:20-23:59", 1800, _job)}
