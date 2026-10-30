"""Shared engine for Aster batch 5 (ADAUSDT spot sleeves, v3-native).

Faithful translations of the staged archive sources:
- R19 crypto families: source/backend/r19_crypto.py (evaluate/_signal/
  known_funding) + source/strategies/absorption/signals.py (Decimal
  EMA20-volume / EMA50-price absorption, confirmation on the bar after
  a bearish volume shock) + crypto_rules.json (native UTC 4h bars,
  entry_delay_hours_after_signal_close=4, entry_window_seconds=300,
  fee_bps_each_side=10, capacity arms fullcash / volume1pct).
- public_recipe RSI2: source/strategies/public_recipes/
  public_source_sleeves.py::source_features('tomazetti_rsi2') with the
  TSV-installed parameters (RSI2<10, close>SMA200, SMA4(RSI2)<30,
  exit close>SMA5, stop disabled, long only, 100% available cash).

v3 runtime translation (recorded in FIDELITY-LEDGER ASTER-B5): bars
arrive as completed snapshot bars {"SYM|4Hour"|"SYM|1Hour"}; the
archive's 4h entry delay is preserved in bar terms — the signal is
read on the second-to-last completed bar and the last completed bar
is the entry interval (its volume supplies the volume1pct cap, as in
the archive). Entry fires only inside the archive's 300s window
after the entry interval closes. Quote/spread/last-trade gates of the
archive transport layer are dispatcher/broker concerns in v3; the
sleeve fails closed on absent/stale bars and (for funding families)
absent funding — funding sleeves declare the `funding` producer
input, which no v3 producer serves yet, so they land UNFED live.
Quantities floor to whole ADA: the v3 intent contract admits
fractional qty only for fractional-symbol forms, and ADAUSDT is not
one (archive step_size flooring, conservative whole-unit reading).
"""
from __future__ import annotations
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext

SYMBOL = "ADAUSDT"
FEE = Decimal("0.001")  # 10 bps each side (crypto_rules.json)
HOLD = timedelta(hours=16)
STEP4 = timedelta(hours=4)
ENTRY_WINDOW_S = 300

# ENH-ABS-WINDOW-20261024 (Edge batch 1, IMPROVE): binding leak —
# the archive's 300s entry window was written for a dedicated
# process polling at the bar close; in v3 these sleeves evaluate on
# a 3600s cadence, so a designed signal is executable only when an
# evaluation happens to land within 300s after the entry bar closes
# (~8% of signals at arbitrary phase; measured on fixture: entry at
# lag 120s, NO entry at lag 1800s/3500s on identical bars). The
# sleeve decides correctly and never executes. Treatment (switch
# ON, default): the window extends to one full cadence (3600s) —
# the entry bar is still bars[-1] throughout that span (the next
# bar completes 4h later), so the designed signal bar, entry price
# reference and sizing inputs are unchanged; only the execution
# moment is repaired. Entries taken past the archive window carry
# the paired shadow record (control = no entry) on enhance_exp.
# OFF restores the exact 300s rule.
EXP_ID_ABS = "ENH-ABS-WINDOW-20261024"
TREATMENT_WINDOW_S = 3600  # = config cadence_s for all five sleeves
WINDOW_SIDS = frozenset({
    "aster_abs_base_ada_fullcash", "aster_abs_base_ada_vol1pct",
    "aster_abs_neg_ada_fullcash", "aster_abs_neg_ada_vol1pct",
    "aster_abs_nonneg_ada_fullcash"})


def _window_on(view, ctx, sid):
    if sid not in WINDOW_SIDS:
        return False  # sibling _common sleeves keep the archive
        # window until their own Edge batch dispositions them
    for src in ((ctx or {}).get("enhance"),
                ((view or {}).get("extra") or {}).get(f"{sid}_improve")):
        if isinstance(src, dict):
            per = src.get(sid) if isinstance(src.get(sid), dict) else src
            if isinstance(per, dict) and "entry_window_cadence" in per:
                return bool(per["entry_window_cadence"])
    return True


def _stamp(value):
    d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("timezone_required")
    return d.astimezone(timezone.utc)


def _now(view):
    return _stamp(view["now"])


def _bars(view, tf):
    rows = (view.get("bars") or {}).get(f"{SYMBOL}|{tf}") or []
    return sorted(rows, key=lambda r: str(r["t"]))


def _positions(view, sid):
    out = []
    for p in view.get("positions") or []:
        if p.get("sleeve_id") not in (None, sid):
            continue
        if p.get("symbol") != SYMBOL:
            continue
        if float(p.get("qty") or 0) != 0:
            out.append(p)
    return out


def _cash(view):
    sl = view.get("slice") or {}
    return float(sl.get("cash_usd", sl.get("capital_usd", 10000.0)))


def _intent(sid, kind, qty, price, reason, tag):
    side = "buy" if kind == "entry" else "sell"
    q = int(qty) if float(qty) == int(float(qty)) else float(qty)
    return {"intent_id": f"{sid}-{SYMBOL}-{tag}-{kind}",
            "kind": kind, "symbol": SYMBOL, "side": side, "qty": q,
            "order_type": "market", "time_in_force": "gtc",
            "price_hint": float(price), "reason": reason}


# ------------------------------------------------------------ funding
def _funding_records(view):
    f = view.get("funding")
    if f is None:
        return None
    if isinstance(f, dict):
        rows = f.get(SYMBOL, f if "rate" in f else None)
        if isinstance(rows, dict):
            return [rows]
        return rows
    return f


def known_funding_rate(view, close_at, now):
    """Archive known_funding: latest eligible receipt; settlement and
    genuine receipt must precede the decision, settlement within 12h
    of the signal close. A simple {'rate': x} observation (no clocks)
    is accepted as an already-qualified receipt."""
    rows = _funding_records(view)
    if not rows:
        return None
    eligible = []
    for r in rows:
        if r.get("observed_public_endpoint") is False:
            continue
        if "settled_at" not in r or "received_at" not in r:
            eligible.append(r)
            continue
        settled, received = _stamp(r["settled_at"]), _stamp(r["received_at"])
        if settled <= close_at and settled <= received <= now:
            eligible.append(r)
    if not eligible:
        return None
    def key(r):
        return _stamp(r["settled_at"]) if "settled_at" in r else close_at
    item = max(eligible, key=key)
    if "settled_at" in item and close_at - key(item) > timedelta(hours=12):
        return None
    try:
        return float(item["rate"])
    except (KeyError, TypeError, ValueError):
        return None


# ------------------------------------------------------- absorption
def _absorption_flags(bars):
    """Port of absorption/signals.py advance(): EMA recurrence
    (vol k=2/21, price k=2/51) seeded on the first bar; a bar is a
    bearish shock when volume > 2x volume-EMA, close < open and
    close < price-EMA; the NEXT bar confirms when it closes bullish
    above the shock bar's midpoint. Returns [(confirmed, count)]."""
    out = []
    count = 0
    vol_ema = price_ema = None
    prev = None  # (bar, shock)
    with localcontext() as ctx:
        ctx.prec = 34
        for b in bars:
            v, c = Decimal(str(b["v"])), Decimal(str(b["c"]))
            o, h, l = (Decimal(str(b["o"])), Decimal(str(b["h"])),
                       Decimal(str(b["l"])))
            vol_ema = v if vol_ema is None else \
                (Decimal(2) * v + Decimal(19) * vol_ema) / Decimal(21)
            price_ema = c if price_ema is None else \
                (Decimal(2) * c + Decimal(49) * price_ema) / Decimal(51)
            shock = bool(v > Decimal(2) * vol_ema and c < o
                         and c < price_ema)
            confirmed = bool(prev and prev[1] and c > o
                             and c > (prev[0]["h"] + prev[0]["l"]) / Decimal(2))
            count += 1
            out.append((confirmed, count))
            prev = ({"h": h, "l": l}, shock)
    return out


# ------------------------------------------------------------ crypto
# ENH edge-batch2 (2026-10-24): per-sleeve switch + paired shadow records.
def _enh_on(view, ctx, sid, key):
    for src in ((ctx or {}), (view or {}).get("extra") or {}):
        if isinstance(src, dict):
            ov = src.get(f"{sid}_enhance")
            if isinstance(ov, dict) and key in ov:
                return bool(ov[key])
    return True


def _paired(view, ctx, rec):
    if isinstance(ctx, dict):
        ctx.setdefault("enhance_paired", []).append(rec)
    ex = (view or {}).get("extra")
    if isinstance(ex, dict):
        ex.setdefault("enhance_paired", []).append(rec)


def evaluate_crypto(view, ctx, sid, family, capacity):
    now = _now(view)
    held = _positions(view, sid)
    out = []
    for p in held:
        due_raw = p.get("exit_due_at")
        if due_raw:
            due = _stamp(due_raw)
        elif p.get("opened_at"):
            due = _stamp(p["opened_at"]) + HOLD
        else:
            continue  # no saved deadline on record: never invent one
        if now >= due:
            out.append(_intent(sid, "exit", abs(float(p["qty"])),
                               float(p.get("avg_price") or 0) or 1.0,
                               f"aster_{family}_fixed16_deadline",
                               str(p.get("opened_at") or due.date())))
    if held:
        return out
    bars = _bars(view, "4Hour")
    if len(bars) < 22:
        return []
    entry_bar, signal_bar = bars[-1], bars[-2]
    entry_close = _stamp(entry_bar["t"]) + STEP4
    lag = now - entry_close
    window_s = max(ENTRY_WINDOW_S, TREATMENT_WINDOW_S) \
        if _window_on(view, ctx, sid) else ENTRY_WINDOW_S
    if not timedelta(0) <= lag <= timedelta(seconds=window_s):
        return []  # outside the entry window / stale
    win_rec = None
    if lag.total_seconds() > ENTRY_WINDOW_S:
        win_rec = {"exp_id": EXP_ID_ABS, "sleeve": sid,
                   "lag_s": lag.total_seconds(),
                   "control": "no_entry_outside_300s_window",
                   "treatment": "entry_at_first_cadence_evaluation"}
    signal_close = _stamp(signal_bar["t"]) + STEP4
    if signal_close != entry_close - STEP4:
        return []  # native-bar gap: fail closed
    rate = None
    if family not in ("breakout_base", "absorption_base"):
        rate = known_funding_rate(view, signal_close, now)
        if rate is None:
            return []  # funding unobserved: never assumed
    boundary = None
    if family in ("breakout_base", "negative_funding_squeeze"):
        i = len(bars) - 2
        boundary = max(float(r["h"]) for r in bars[i - 20:i])
        triggered = float(signal_bar["c"]) > boundary
    else:
        flags = _absorption_flags(bars)
        confirmed, count = flags[len(bars) - 2]
        triggered = bool(confirmed and count >= 300)
    if family in ("negative_funding_squeeze",
                  "absorption_negative_funding"):
        triggered = triggered and rate is not None and rate < 0
    elif family == "absorption_nonnegative_funding":
        triggered = triggered and rate is not None and rate >= 0
    if not triggered:
        return []
    # ENH: revalidate the 4h-old signal on the entry bar itself.
    if family == "breakout_base" and boundary is not None and \
            _enh_on(view, ctx, sid, "entry_revalidation"):
        held_up = float(entry_bar["c"]) > boundary
        _paired(view, ctx, {"exp_id": "ENH-EDGE-B2-" + sid, "sleeve": sid,
                            "control": "enter", "treatment": "enter" if held_up else "refuse_stale_breakout",
                            "entry_close": float(entry_bar["c"]), "boundary": boundary,
                            "enhance_switch": True})
        if not held_up:
            return []  # breakout already lost on the entry bar: do not chase a dead signal
    if family == "absorption_nonnegative_funding" and \
            _enh_on(view, ctx, sid, "funding_revalidation"):
        rate_entry = known_funding_rate(view, entry_close, now)
        ok = rate_entry is not None and rate_entry >= 0
        _paired(view, ctx, {"exp_id": "ENH-EDGE-B2-" + sid, "sleeve": sid,
                            "control": "enter", "treatment": "enter" if ok else "refuse_funding_flipped",
                            "funding_at_signal": rate, "funding_at_entry": rate_entry,
                            "enhance_switch": True})
        if not ok:
            return []  # defining funding condition flipped during the 4h delay
    # ENH batch 11 (aster_squeeze_ada_fullcash ONLY): the same stale-
    # funding leak on the negative side — the squeeze's defining input
    # (funding < 0) was read at the signal bar, 4h before the entry
    # bar; if funding normalized in between, the squeeze premise is
    # gone but the sleeve still deployed full cash. Treatment:
    # revalidate funding at the entry bar; control = signal-time rule.
    if sid == "aster_squeeze_ada_fullcash" and \
            family == "negative_funding_squeeze" and \
            _enh_on(view, ctx, sid, "funding_revalidation"):
        rate_entry = known_funding_rate(view, entry_close, now)
        ok = rate_entry is not None and rate_entry < 0
        _paired(view, ctx, {"exp_id": "ENH-B11-" + sid, "sleeve": sid,
                            "control": "enter", "treatment": "enter" if ok else "refuse_funding_normalized",
                            "funding_at_signal": rate, "funding_at_entry": rate_entry,
                            "enhance_switch": True})
        if not ok:
            return []  # funding normalized during the 4h delay: premise gone
    price = float(entry_bar["c"])
    if price <= 0:
        return []
    with localcontext() as ctx2:
        ctx2.prec = 34
        target = Decimal(str(_cash(view))) / \
            (Decimal(str(price)) * (1 + FEE))
        if capacity == "volume1pct":
            target = min(target, Decimal(str(entry_bar["v"]))
                         * Decimal("0.01"))
    qty = math.floor(float(target))
    if qty <= 0:
        return []
    ent = _intent(sid, "entry", qty, price,
                  f"aster_{family}_{capacity}",
                  str(signal_bar["t"])[:13])
    if win_rec:
        win_rec["qty"] = qty
        ent["enhance_exp"] = {"exp_id": EXP_ID_ABS, "records": [win_rec]}
    return [ent]


# -------------------------------------------------------------- RSI2
def _rma(xs, n):
    out, seed, old = [], [], None
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


def _rsi(closes, n=2):
    gains = [None] + [max(closes[i] - closes[i - 1], 0.0)
                      for i in range(1, len(closes))]
    losses = [None] + [max(closes[i - 1] - closes[i], 0.0)
                       for i in range(1, len(closes))]
    g, l = _rma(gains, n), _rma(losses, n)
    out = []
    for a, b in zip(g, l):
        if a is None or b is None or (a == 0 and b == 0):
            out.append(None)
        elif b == 0:
            out.append(100.0)
        elif a == 0:
            out.append(0.0)
        else:
            out.append(100 - 100 / (1 + a / b))
    return out


def _sma(xs, n):
    if len(xs) < n or any(x is None for x in xs[-n:]):
        return None
    return sum(xs[-n:]) / n


# TSV-installed window (education_parameters_json, Paper book 46).
_WINDOW_START = _stamp("2009-01-01T19:00:00-05:00")
_WINDOW_END = _stamp("2030-12-29T19:00:00-05:00")


def evaluate_rsi2(view, ctx, sid):
    now = _now(view)
    bars = _bars(view, "1Hour")
    held = _positions(view, sid)
    closes = [float(b["c"]) for b in bars]
    if held:
        sma5 = _sma(closes, 5) if len(closes) >= 5 else None
        if sma5 is not None and closes[-1] > sma5:
            p = held[0]
            return [_intent(sid, "exit", abs(float(p["qty"])),
                            closes[-1], "aster_rsi2_close_above_sma5",
                            str(p.get("opened_at") or now.date()))]
        return []
    if len(bars) < 200:
        return []
    last_close_dt = _stamp(bars[-1]["t"]) + timedelta(hours=1)
    if not timedelta(0) <= now - last_close_dt <= timedelta(
            seconds=ENTRY_WINDOW_S):
        return []  # decision window: 300s after the completed bar
    if not (_WINDOW_START <= _stamp(bars[-1]["t"]) <= _WINDOW_END):
        return []
    rsi = _rsi(closes, 2)
    sma200, sma4rsi = _sma(closes, 200), _sma(rsi, 4)
    if rsi[-1] is None or sma200 is None or sma4rsi is None:
        return []
    if not (rsi[-1] < 10 and closes[-1] > sma200 and sma4rsi < 30):
        return []
    qty = math.floor(_cash(view) / closes[-1])
    if qty <= 0:
        return []
    return [_intent(sid, "entry", qty, closes[-1],
                    "aster_public_rsi2_filtered",
                    str(bars[-1]["t"])[:13])]
