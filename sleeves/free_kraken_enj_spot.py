"""FREE_KRAKEN_ENJ_SPOT — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_kraken_paper.py enj_spot(): ENJ has a Kraken
SPOT book only — no perpetual exists on the checked Kraken list.
enj_status() ports the old checks (empty -> BLOCKED_INPUT; crossed ->
BLOCKED_INPUT; else QUALIFIED/AWAITING SIGNAL).

UNFENCE-119 (owner ruling 2026-10-24 10:38 ET): the Decision #119
monitor-only fence is REVERSED for this sleeve in muse-desk-v2 —
CONFIG.monitor_only=False and the adapter routes signal() intents
to the dispatcher instead of journaling monitor_status.

DESIGNED-ORDER-LOGIC (DESIGNED-ORDER-LOGIC.md §3, owner ruling
2026-10-24 11:41 ET "Fix that defect"): no ENJ order logic existed
in any source to port, so the logic below was AUTHORED to the locked
design. These constants were authored under the owner's 2026-10-24
'Fix that defect' ruling: SPREAD_MAX_BPS = 50, IMBALANCE_RATIO = 2.0,
EXIT_SPREAD_BPS = 200, HOLD_HOURS = 24. Design: from extra["book"]
(Kraken ENJUSD Depth, produced at warm time by runtime/kraken_warm.py
and injected by the adapter with params precedence), take top-10
levels per side; depth = sum of size (row[1]) over those levels;
mid = (bid + ask) / 2; spread_bps = (ask - bid) / mid * 10000.
FLAT: enj_status QUALIFIED and spread_bps <= 50 and
bid_depth >= 2.0 * ask_depth and ask > 0 -> enter long ENJUSD,
qty_hint = floor(min(slice_equity, 10000) / ask) with slice_equity
from context.equity, min 1 else no intent, price_hint = ask.
LONG OPEN (sleeve_state qty > 0): exit full qty at the bid when
ask_depth >= 2.0 * bid_depth OR spread_bps > 200 OR held >= 24h
(entry time from sleeve_state entry_due_at/opened_at); every exit
requires a valid non-crossed book with bid > 0 — an empty book
means no priced exit exists, so hold. One open position at a time;
fail closed on missing, stale, crossed, or malformed inputs; never
raise. enj_status() is retained as a status helper.

VIRTUAL BOOK MAPPING: sizing goes through the existing slice
machinery (config slice capital_usd = 10000 for this sleeve).
"""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone

from desk3.contract import BaseSleeve, Intent, SleeveConfig

INSTRUMENT = "ENJUSD"
SPREAD_MAX_BPS = 50
IMBALANCE_RATIO = 2.0
EXIT_SPREAD_BPS = 200
HOLD_HOURS = 24
HOLD = timedelta(hours=HOLD_HOURS)
DEPTH_LEVELS = 10

CONFIG = SleeveConfig(
    sleeve_id="free_kraken_enj_spot", cadence_s=3600, universe=("ENJUSD",), monitor_only=False,
    state_schema={}, risk_pct=None)


def _parse(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _now_dt(now):
    if isinstance(now, datetime):
        return now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromtimestamp(float(now), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _levels(rows):
    out = []
    for row in (rows or [])[:DEPTH_LEVELS]:
        try:
            price = float(row[0]); size = float(row[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        out.append((price, size))
    return out


def _book_metrics(book):
    """Return dict or None-ish metrics; fail closed on malformed."""
    if not isinstance(book, dict):
        return {"ok": False, "reason": "book_missing"}
    bids_raw, asks_raw = book.get("bids") or [], book.get("asks") or []
    if not bids_raw or not asks_raw:
        return {"ok": False, "reason": "empty"}
    bids, asks = _levels(bids_raw), _levels(asks_raw)
    if not bids or not asks:
        return {"ok": False, "reason": "malformed"}
    bid, ask = bids[0][0], asks[0][0]
    if bid <= 0 or ask <= 0 or ask < bid:
        return {"ok": False, "reason": "crossed", "bid": bid, "ask": ask}
    mid = (bid + ask) / 2.0
    if mid <= 0:
        return {"ok": False, "reason": "crossed", "bid": bid, "ask": ask}
    spread_bps = (ask - bid) / mid * 10000.0
    bid_depth = sum(s for _, s in bids)
    ask_depth = sum(s for _, s in asks)
    ratio = (bid_depth / ask_depth) if ask_depth > 0 else float("inf")
    return {"ok": True, "bid": bid, "ask": ask, "mid": mid,
            "spread_bps": spread_bps, "bid_depth": bid_depth,
            "ask_depth": ask_depth, "depth_ratio": ratio}


def _event_id(metrics):
    payload = json.dumps(
        {"instrument": INSTRUMENT, "bid": metrics.get("bid"),
         "ask": metrics.get("ask"),
         "spread_bps": round(float(metrics.get("spread_bps") or 0), 6),
         "bid_depth": metrics.get("bid_depth"),
         "ask_depth": metrics.get("ask_depth")},
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def enj_status(book, now_iso=""):
    """book: {"bids": [[price, ...], ...], "asks": [[price, ...], ...]}."""
    m = _book_metrics(book)
    if not m["ok"]:
        if m["reason"] == "crossed":
            return {"id": "FREE_KRAKEN_ENJ_SPOT_V1", "status": "BLOCKED_INPUT",
                    "reason": "Kraken ENJ/USD book is crossed."}
        return {"id": "FREE_KRAKEN_ENJ_SPOT_V1", "status": "BLOCKED_INPUT",
                "reason": "Kraken ENJ/USD book is empty."}
    return {"id": "FREE_KRAKEN_ENJ_SPOT_V1", "status": "QUALIFIED/AWAITING SIGNAL",
            "feed": "kraken_spot_ENJUSD", "bid": m["bid"], "ask": m["ask"],
            "reason": "Spot book is live. Designed spot logic armed: long ENJUSD when spread <= 50bps and bid depth >= 2.0x ask depth (top-10); exit on depth flip, spread > 200bps, or 24h hold. No perpetual exists for ENJ on the checked Kraken list, so no basis or funding order is created.",
            "asof": now_iso}


def enj_decision(book, now):
    """Designed ENJ decision (family style of
    sleeves/free_kraken_ada_breakdown.py): decision dict with
    status/reason from the top-10 depth book."""
    n = _now_dt(now)
    m = _book_metrics(book)
    if not m["ok"]:
        return {"status": "BLOCKED_INPUT",
                "reason": "Kraken ENJ/USD book is empty." if m["reason"] != "crossed" else "Kraken ENJ/USD book is crossed.",
                "spread_bps": None, "bid_depth": None, "ask_depth": None,
                "bid": m.get("bid"), "ask": m.get("ask")}
    base = {"bid": m["bid"], "ask": m["ask"], "mid": m["mid"],
            "spread_bps": m["spread_bps"], "bid_depth": m["bid_depth"],
            "ask_depth": m["ask_depth"], "depth_ratio": m["depth_ratio"],
            "event_id": _event_id(m),
            "decision_at": n.isoformat() if n else None}
    if m["spread_bps"] <= SPREAD_MAX_BPS and m["bid_depth"] >= IMBALANCE_RATIO * m["ask_depth"]:
        return {**base, "status": "entry_ready", "side": "buy",
                "reason": "Bid-heavy tight book: spread %.2fbps <= %d and bid/ask depth ratio %.2f >= %.1f." % (m["spread_bps"], SPREAD_MAX_BPS, m["depth_ratio"], IMBALANCE_RATIO)}
    return {**base, "status": "QUALIFIED/AWAITING SIGNAL",
            "reason": "Book qualified but entry not met: spread %.2fbps (max %d), bid/ask depth ratio %.2f (need >= %.1f)." % (m["spread_bps"], SPREAD_MAX_BPS, m["depth_ratio"], IMBALANCE_RATIO)}


def _position(extra, slice_state):
    candidates = []
    for source in (extra.get("sleeve_state") or {}, extra.get("sleeve_state_flat") or {}):
        if isinstance(source, dict) and INSTRUMENT in source:
            candidates.append(source[INSTRUMENT])
    if isinstance(slice_state, dict) and INSTRUMENT in slice_state:
        candidates.append(slice_state[INSTRUMENT])
    for pos in candidates:
        if isinstance(pos, dict) and isinstance(pos.get("position"), dict):
            pos = pos["position"]
        if isinstance(pos, (int, float)):
            return float(pos), None
        if not isinstance(pos, dict):
            continue
        try:
            qty = float(pos.get("qty") or 0)
        except (TypeError, ValueError):
            continue
        entry_time = None
        for key in ("entry_due_at", "opened_at", "entry_time", "entry_at"):
            if pos.get(key):
                try:
                    entry_time = _parse(pos[key])
                except Exception:
                    entry_time = None
                break
        return qty, entry_time
    return 0.0, None


class FreeKrakenEnjSpot(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        try:
            now = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        except (TypeError, ValueError):
            return []
        book = extra.get("book") or {}
        m = _book_metrics(book)
        qty, entry_time = _position(extra, slice_state)
        if qty > 0:
            # LONG OPEN: exit requires valid non-crossed book, bid>0
            if not m["ok"]:
                return []
            flip = m["ask_depth"] >= IMBALANCE_RATIO * m["bid_depth"]
            blowout = m["spread_bps"] > EXIT_SPREAD_BPS
            held = entry_time is not None and now >= entry_time + HOLD
            if not (flip or blowout or held):
                return []
            if flip:
                why = "depth flip ask_depth %.2f >= %.1f x bid_depth %.2f" % (m["ask_depth"], IMBALANCE_RATIO, m["bid_depth"])
            elif blowout:
                why = "spread blowout %.2fbps > %dbps" % (m["spread_bps"], EXIT_SPREAD_BPS)
            else:
                why = "24h hold elapsed since %s" % entry_time.isoformat()
            qty_hint = int(qty) if float(qty) == int(float(qty)) else float(qty)
            return [Intent("exit", INSTRUMENT, qty_hint=qty_hint,
                           price_hint=round(float(m["bid"]), 6),
                           reason="free_kraken_enj_spot EXIT long ENJUSD at live bid; %s; spread_bps=%.2f depth_ratio=%.2f event=%s" % (why, m["spread_bps"], m["depth_ratio"], _event_id(m)))]
        if qty < 0:
            return []
        # FLAT
        status = enj_status(book, now.isoformat())
        if status.get("status") != "QUALIFIED/AWAITING SIGNAL":
            return []
        decision = enj_decision(book, now)
        if decision.get("status") != "entry_ready":
            return []
        ask = m["ask"]
        if not (ask > 0):
            return []
        try:
            equity = float(context.equity or 0)
        except (TypeError, ValueError):
            return []
        qty_calc = math.floor(min(equity, 10000.0) / ask) if ask > 0 else 0
        if qty_calc < 1:
            return []
        return [Intent("enter", INSTRUMENT, qty_hint=int(qty_calc),
                       price_hint=round(float(ask), 6),
                       reason="free_kraken_enj_spot LONG ENJUSD at live ask; spread_bps=%.2f <= %d depth_ratio=%.2f >= %.1f event=%s" % (m["spread_bps"], SPREAD_MAX_BPS, m["depth_ratio"], IMBALANCE_RATIO, decision["event_id"]))]


def signal(bars, slice_state, context):
    return FreeKrakenEnjSpot().signal(bars, slice_state, context)
