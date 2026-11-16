"""SSO Opus swing (15-minute) as a desk sleeve family:
SSO-PORT-CONV46-20261115.

Source of truth: the 2026-11-03 research engines at
research_notes/trendspider-sso-opus-test-20261103/harness.py
(run_sim, trail_from="close", the frozen primary form) and its
saved ledgers trades_primary.csv (265 trades, cost 0) and
trades_cost_5bp.csv (282 trades, cost 5bp). This module is a
line-faithful stdlib port of that simulator: same indicators
(SMA50/SMA200 on closes, Wilder ADX(10), Wilder RSI(14), SMA20
of volume, per-day VWAP on typical price, range high = max of
the prior 14 bars' highs), same entry gate (i >= 200, trend and
ADX filters, Setup A range breakout at 2.0x volume, Setup B
same-day VWAP cross at 1.5x volume with RSI > 50, A wins the
label), same fills (entry at next bar open, exit at next bar
open, last-bar exits at the close with _AT_CLOSE_END), and the
same exit priority on every held bar: STOP_LOSS (pnl <= -3.5%),
TRAILING_STOP (close <= 0.93 x running max close), TAKE_PROFIT
(pnl >= +15%), TIME_25 (held >= 25 and pnl < 0), TIME_60
(held >= 60 and pnl < +1%).

Fidelity is proven, not asserted: the port's simulate()
reproduces both research ledgers trade-for-trade (entry/exit
times, prices, returns, reasons, setups, bars held) at 1e-9
relative tolerance, and passes the harness's own synthetic
known-answer series. The proof script and its output are saved
with the Conversion Register update for CONV-46; the gate
blocker (tests/test_conv46_sso_port_20261115_blockers.py)
carries the synthetic test and the rule pins so a regression
cannot silently move the form.

Two sleeves share this engine:
- sso_opus: the research baseline, byte-for-byte in behavior.
- sso_opus_notime25: the CONV-46 variation (GUTTING AS
  VARIATION): the identical engine with drop_time25=True, which
  removes exactly the TIME_25 exit class and nothing else (a bar
  that would have exited TIME_25 falls through to the TIME_60
  check, as the elif chain dictates). The baseline is never
  edited into the variation; the variation is registered in
  config/conversion_variations_20261115.json with its own
  falsifier and kill rule.

Live translation (named, the only place the sim and the sleeve
differ): the sim decides on bar i and fills at bar i+1's open;
the sleeve evaluates the served SSO 15Min tape (RTH-filtered to
bar starts 09:30-15:45 ET, the research frame's own filter) and
emits the intent at the signal bar, with the sleeve's costs
carrying fill_timing next_bar, so the fill lands at the next
bar's open exactly as in the sim. A held position is anchored
by the position record's opened_at (the bar at whose open the
fill landed) and its avg_price when the book carries one, else
that bar's open (the sim's own fill convention); exits evaluate
the same priority chain on the latest served bar. Indicators
compute over the served window (30 days, about 780 RTH bars,
above the 200-bar warmup), the desk's universal serving form.
A position whose entry bar cannot be located in the served
window fails closed (no exit intent) rather than guessing an
anchor. Costs are 0 in the live sleeve: the baseline identity
is the 0bp primary ledger, and the desk's costs block models
execution separately.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .contract import Intent

SYMBOL = "SSO"
BASE_ID = "sso_opus"
VARIATION_ID = "sso_opus_notime25"

SPECS = {
    BASE_ID: dict(drop_time25=False),
    VARIATION_ID: dict(drop_time25=True),
}

INPUTS = ("bars", "bars:SSO:15Min", "positions")
PRODUCERS = ({"name": "bars", "outputs": ("bars",),
              "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",),
              "freshness_sla_s": 900})

# Rule constants, pinned from the research harness (run_sim).
STOP_LOSS_PNL = -0.035
TRAIL_FRACTION = 0.93
TAKE_PROFIT_PNL = 0.15
TIME_25_HELD = 25
TIME_60_HELD = 60
TIME_60_PNL = 0.01
ADX_MIN = 20.0
WARMUP_BARS = 200
SETUP_A_VOL_MULT = 2.0
SETUP_B_VOL_MULT = 1.5
SETUP_B_RSI_MIN = 50.0

_ET = ZoneInfo("America/New_York")
_NAN = float("nan")


# ---------------- indicators (line-faithful ports) ----------------

def _sma(vals, n):
    out = [_NAN] * len(vals)
    run = 0.0
    for i, v in enumerate(vals):
        run += v
        if i >= n:
            run -= vals[i - n]
        if i >= n - 1:
            out[i] = run / n
    return out


def _wilder_rsi(close, n=14):
    m = len(close)
    rsi = [_NAN] * m
    if m <= n:
        return rsi
    gain = [0.0] * (m - 1)
    loss = [0.0] * (m - 1)
    for i in range(m - 1):
        d = close[i + 1] - close[i]
        if d > 0:
            gain[i] = d
        elif d < 0:
            loss[i] = -d
    ag = sum(gain[:n]) / n
    al = sum(loss[:n]) / n
    for k in range(n, m - 1):
        if k > n:
            ag = (ag * (n - 1) + gain[k]) / n
            al = (al * (n - 1) + loss[k]) / n
        rsi[k + 1] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return rsi


def _wilder_adx(high, low, close, n=10):
    m = len(close)
    tr = [0.0] * m
    pdm = [0.0] * m
    mdm = [0.0] * m
    for i in range(1, m):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]),
                    abs(low[i] - close[i - 1]))
        up = high[i] - high[i - 1]
        dn = low[i - 1] - low[i]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        mdm[i] = dn if (dn > up and dn > 0) else 0.0

    def smooth(x):
        out = [_NAN] * m
        if m <= n:
            return out
        s = sum(x[1:n + 1])
        out[n] = s
        for i in range(n + 1, m):
            s = s - s / n + x[i]
            out[i] = s
        return out

    str_ = smooth(tr)
    spdm = smooth(pdm)
    smdm = smooth(mdm)
    dx = [_NAN] * m
    for i in range(n, m):
        if not math.isnan(str_[i]) and str_[i] > 0:
            pdi = 100.0 * spdm[i] / str_[i]
            mdi = 100.0 * smdm[i] / str_[i]
            dx[i] = 0.0 if (pdi + mdi) == 0 else \
                100.0 * abs(pdi - mdi) / (pdi + mdi)
    adx = [_NAN] * m
    first = next((i for i in range(m) if not math.isnan(dx[i])), None)
    if first is None:
        return adx
    seed_end = first + n - 1
    if seed_end >= m:
        return adx
    seed = [x for x in dx[first:seed_end + 1] if not math.isnan(x)]
    val = sum(seed) / len(seed) if seed else _NAN
    adx[seed_end] = val
    for i in range(seed_end + 1, m):
        if not math.isnan(dx[i]):
            val = (val * (n - 1) + dx[i]) / n
            adx[i] = val
    return adx


def _day_vwap(bars):
    out = [_NAN] * len(bars)
    pv = {}
    cv = {}
    for i, b in enumerate(bars):
        d = b["date"]
        tp = (float(b["h"]) + float(b["l"]) + float(b["c"])) / 3.0
        pv[d] = pv.get(d, 0.0) + tp * float(b["v"])
        cv[d] = cv.get(d, 0.0) + float(b["v"])
        out[i] = pv[d] / cv[d] if cv[d] else _NAN
    return out


def _range_high(high):
    m = len(high)
    out = [_NAN] * m
    for i in range(14, m):
        out[i] = max(high[i - 14:i])
    return out


def _indicators(bars):
    o = [float(b["o"]) for b in bars]
    h = [float(b["h"]) for b in bars]
    low = [float(b["l"]) for b in bars]
    c = [float(b["c"]) for b in bars]
    v = [float(b["v"]) for b in bars]
    return {
        "o": o, "h": h, "l": low, "c": c, "v": v,
        "sma50": _sma(c, 50), "sma200": _sma(c, 200),
        "adx": _wilder_adx(h, low, c, 10), "rsi": _wilder_rsi(c, 14),
        "volsma": _sma(v, 20), "vwap": _day_vwap(bars),
        "range_high": _range_high(h),
    }


def _exit_reason(pnl, close, hi_close, held, drop_time25):
    """The exit priority chain, shared by simulate() and the live
    evaluator so the two can never drift apart."""
    if pnl <= STOP_LOSS_PNL:
        return "STOP_LOSS"
    if close <= TRAIL_FRACTION * hi_close:
        return "TRAILING_STOP"
    if pnl >= TAKE_PROFIT_PNL:
        return "TAKE_PROFIT"
    if not drop_time25 and held >= TIME_25_HELD and pnl < 0:
        return "TIME_25"
    if held >= TIME_60_HELD and pnl < TIME_60_PNL:
        return "TIME_60"
    return None


def _entry_setup(ind, dates, i):
    """Setup label ("A"/"B") when bar i is an entry signal under
    the registered gate, else None. Mirrors run_sim exactly."""
    if math.isnan(ind["sma50"][i]) or math.isnan(ind["sma200"][i]) \
            or math.isnan(ind["adx"][i]) or math.isnan(ind["rsi"][i]) \
            or math.isnan(ind["volsma"][i]) \
            or math.isnan(ind["range_high"][i]):
        return None
    if not (ind["sma50"][i] > ind["sma200"][i]
            and ind["adx"][i] > ADX_MIN):
        return None
    c = ind["c"]
    v = ind["v"]
    setup_a = bool(c[i] > ind["range_high"][i]
                   and v[i] >= SETUP_A_VOL_MULT * ind["volsma"][i])
    setup_b = bool(i > 0 and dates[i] == dates[i - 1]
                   and c[i - 1] <= ind["vwap"][i - 1]
                   and c[i] > ind["vwap"][i]
                   and ind["rsi"][i] > SETUP_B_RSI_MIN
                   and v[i] >= SETUP_B_VOL_MULT * ind["volsma"][i])
    if setup_a:
        return "A"
    if setup_b:
        return "B"
    return None


# ---------------- the simulator (fidelity surface) ----------------

def simulate(bars, drop_time25=False, cost_bp=0.0):
    """Line-faithful port of the research run_sim (trail_from=
    "close"). bars: ordered RTH frame rows {t, o, h, l, c, v,
    date}. Returns the trade list in the harness's own fields."""
    ind = _indicators(bars)
    o, c = ind["o"], ind["c"]
    dates = [b["date"] for b in bars]
    times = [b["t"] for b in bars]
    n = len(bars)
    cost = cost_bp / 10000.0
    equity = 1.0
    trades = []
    pos = None
    for i in range(n):
        exited_this_bar = False
        if pos is not None:
            pos["hi_close"] = max(pos["hi_close"], c[i])
            pos["hi_high"] = max(pos["hi_high"], ind["h"][i])
            pnl = c[i] / pos["entry_price"] - 1.0
            held = i - pos["entry_idx"]
            reason = _exit_reason(pnl, c[i], pos["hi_close"], held,
                                  drop_time25)
            if reason is not None:
                exited_this_bar = True
                if i + 1 < n:
                    exit_price = o[i + 1] * (1 - cost)
                    exit_idx = i + 1
                else:
                    exit_price = c[i] * (1 - cost)
                    exit_idx = i
                    reason = reason + "_AT_CLOSE_END"
                ret = exit_price / pos["entry_price"] - 1.0
                eq_before = equity
                equity = equity * (1 + ret)
                trades.append({
                    "entry_time": pos["entry_time"],
                    "exit_time": times[exit_idx],
                    "entry_idx": pos["entry_idx"],
                    "exit_idx": exit_idx,
                    "entry_price": pos["entry_price"],
                    "exit_price": exit_price,
                    "return": ret, "exit_reason": reason,
                    "setup": pos["setup"],
                    "bars_held": exit_idx - pos["entry_idx"],
                    "equity_before": eq_before,
                    "equity_after": equity,
                })
                pos = None
        if pos is None and not exited_this_bar and i >= WARMUP_BARS \
                and i + 1 < n:
            setup = _entry_setup(ind, dates, i)
            if setup is not None:
                pos = {
                    "entry_idx": i + 1, "entry_time": times[i + 1],
                    "entry_price": o[i + 1] * (1 + cost),
                    "setup": setup,
                    "hi_close": float("-inf"),
                    "hi_high": float("-inf"),
                }
    if pos is not None:
        i = n - 1
        exit_price = c[i] * (1 - cost)
        ret = exit_price / pos["entry_price"] - 1.0
        eq_before = equity
        equity = equity * (1 + ret)
        trades.append({
            "entry_time": pos["entry_time"], "exit_time": times[i],
            "entry_idx": pos["entry_idx"], "exit_idx": i,
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "return": ret, "exit_reason": "END_OF_DATA",
            "setup": pos["setup"],
            "bars_held": i - pos["entry_idx"],
            "equity_before": eq_before, "equity_after": equity,
        })
    return trades


# ---------------- live evaluation ----------------

def _ts(raw):
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), timezone.utc)
    try:
        d = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except Exception:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _frame(view):
    """The served SSO 15Min tape, RTH-filtered to the research
    frame's own window (bar starts 09:30-15:45 ET), with ET date
    stamps, in served order."""
    rows = (view.get("bars") or {}).get("SSO|15Min") or []
    out = []
    for r in rows:
        t = _ts(r.get("t"))
        if t is None:
            continue
        et = t.astimezone(_ET)
        mins = et.hour * 60 + et.minute
        if not (570 <= mins <= 945):
            continue
        out.append({"t": r["t"], "o": float(r["o"]),
                    "h": float(r["h"]), "l": float(r["l"]),
                    "c": float(r["c"]), "v": float(r["v"]),
                    "date": et.date().isoformat()})
    return out


def evaluate(sid, view, ctx=None):
    view = view or {}
    drop = SPECS[sid]["drop_time25"]
    bars = _frame(view)
    if not bars:
        return []
    poss = [p for p in (view.get("positions") or [])
            if p.get("symbol", SYMBOL) == SYMBOL
            and float(p.get("qty") or 0) != 0]
    if poss:
        p = poss[0]
        opened = _ts(p.get("opened_at") or p.get("entry_time"))
        if opened is None:
            return []  # fail closed: no anchor, no guessed exit
        entry_idx = None
        for j, b in enumerate(bars):
            bt = _ts(b["t"])
            if bt is not None and bt <= opened:
                entry_idx = j
            if bt is not None and bt > opened:
                break
        if entry_idx is None:
            return []  # position predates the served window
        avg = float(p.get("avg_price") or 0)
        entry_price = avg if avg > 0 else float(bars[entry_idx]["o"])
        if entry_price <= 0:
            return []
        last = len(bars) - 1
        closes = [float(b["c"]) for b in bars]
        hi_close = max(closes[entry_idx:last + 1])
        held = last - entry_idx
        pnl = closes[last] / entry_price - 1.0
        reason = _exit_reason(pnl, closes[last], hi_close, held, drop)
        if reason is None:
            return []
        return [Intent(
            kind="exit", symbol=SYMBOL, qty=abs(float(p["qty"])),
            price_hint=closes[last],
            reason=f"{sid} exit: {reason} held={held} "
                   f"pnl={pnl:.4f} entry={entry_price}",
            side="sell", position_intent="sell_to_close")]
    i = len(bars) - 1
    if i < WARMUP_BARS:
        return []
    ind = _indicators(bars)
    dates = [b["date"] for b in bars]
    setup = _entry_setup(ind, dates, i)
    if setup is None:
        return []
    price = ind["c"][i]
    cash = float((view.get("slice") or {}).get("cash_usd") or 10000.0)
    qty = cash / price
    if qty <= 0:
        return []
    return [Intent(
        kind="enter", symbol=SYMBOL, qty=round(qty, 8),
        price_hint=price,
        reason=f"{sid} entry: setup {setup} close={price} "
               f"adx={ind['adx'][i]:.1f}",
        side="buy", position_intent="buy_to_open")]


def config_rows():
    rows = []
    for sid in (BASE_ID, VARIATION_ID):
        rows.append({
            "id": sid, "module": f"adapters3.{sid}",
            "cadence_s": 300, "session": "rth",
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None, "params": {},
            "costs": {"fill_timing": "next_bar",
                      "commission_per_share": 0.0,
                      "commission_bps": 0.0,
                      "min_commission_per_order": 0.0,
                      "slippage_model": "forecast_per_name",
                      "slippage_bps": None},
            "rebalance_policy": {
                "frequency": "signal_driven", "drift_threshold": None,
                "drift_type": None, "partial_rebalance": False,
                "tracking_error_threshold": None,
                "tracking_error_window_days": None,
                "max_annual_turnover": None,
                "signal_change_rebalance": True,
                "execution_timing": "on_evaluation",
                "enforcement": "declared_not_enforced",
                "status": "ESCALATED_FOR_RULING",
                "enforced_dimensions": []},
            "inputs": list(INPUTS), "parked": False,
        })
    return rows
