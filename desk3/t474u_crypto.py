"""t474u crypto filter twins — faithful desk port (T474U-CRYPTO-PORT-20261116).

SOURCE (provenance, verified 2026-11-16 by ghapi blob read):
  GrokBot md2, repo dwj9ddyvf6-hub/master-desk @
  c2de06921bac7c902b19daa572dcbf8f831fe60f:
    mdesk/engines/t474u_x.py        blob e9b08e1ba15f78ad9eacfca472d25c4bbc6e6b34
    mdesk/t474u_indicators.py       blob daba61293d7f233f14c9ab488a89bb69df209089
    mdesk/ind.py                    blob ef7ad0df9fa05fd999682bdc3dddff1c0f142df7
    mdesk/t474u_params.json         blob 376c01e44d66810b1cbcf00c2d5816f7a2cb2a6e
    tools/t474u_backtest.py         blob 5452c9e113f547fe9de6d28f9666a343d7824c5c
  Fidelity records, repo dwj9ddyvf6-hub/cos2-estate @
  31f90a01187bdead91afe3d7652f9007c5bee691 (copies also in master-desk
  evidence/calibrations/t474u/ at the same commit):
    research/x_t473u/historical_fires.json  blob 15c87bb2d8bf78ee2dfb4cb5e375d26cb67f3668
    evidence sweeps.json                    blob 68007f3b14159e8220dde746d2a819d3452f3711

SCOPE: exactly the 9 book-blocked sleeves of the GROKBOT-T474U-INTAKE-
20261114 intake (midna-book/GROKBOT-T474U-SLEEVES-ADDED-20261114.md):
the CryptoFilterTwin class on ADA/ENJ/LINK for the three filter
families (bar_range_atr, mfi_gate, btc_stdev). The BTC twins and the
other t474u families are NOT ported here: the BTC sleeves already
trade on the book side via IBIT options expressions, and the equity /
feature families were never blocked. Nothing in the source engine is
edited; this is a port, and every rule below names its source line.

SOURCE RULES (CryptoFilterTwin, t474u_x.py):
  host: 4h 10-bar breakout — close above the max high of the prior
    `lookback` bars (lookback=10 from the frozen params; the engine
    reads lookback_crypto for mfi, both are 10).
  bratr: (H-L)/ATR(14) at the signal bar > k, k=2.0 (bar_range_atr).
  mfi:   100*(MFI(14)/SMA(30,MFI) - 1) > theta, theta=15 (mfi_gate).
  stdev: |C - SMA(C,20)| / STDEV(C,20) > k, k=0.5 (btc_stdev; the
    source's stated definition of the close-vs-MA stdev filter).
  warm-up: scan refuses a served series shorter than MIN_4H=300 bars.
  sizing on md2: principal 10_000, pos_frac 0.25, slots 1.
  exit: fixed16h — exit_reason returns "fixed16h" once the position's
    age from confirm_t (signal bar t + 4h) reaches 16 hours.
  venue on md2: shadow-crypto, paper/sim only. These desk rows are
    paper too (the desk is a paper desk).

FIDELITY (proof/t474u/t474u_fidelity_result.json, harness
proof/t474u/t474u_fidelity_check.py): historical_fires.json records
the BACKTEST replay's fires (tools/t474u_backtest.py
sweep_breakout_filter signal arrays over the full 399-bar OKX series),
not live-scan counts — the live scan's 300-bar gate undercounts them
(measured: scan-prefix replay matches last_t on 12/12 but counts on
0/12; the array replay matches counts AND last_t on 12/12). The port
therefore proves fidelity on the recorded definition: the ported
signal function, run over the exact build-time OKX window (399 bars,
t0=1788940800, t1=1794672000 for all four symbols, re-fetched from
OKX public history-candles on 2026-11-16 and endpoint-verified
against sweeps.json's own series table), reproduces every recorded
fire (bar timestamp + signal close) for the 9 sleeves and the 3 BTC
controls, and the ported trade simulation (fill next open, 16h =
4-bar hold, non-overlapping, fee 10bp one-way at 1x/2x/4x/5x stress)
reproduces sweeps.json's IS/OOS metrics at the frozen params.
The LIVE evaluate() below gates identically to the source scan
(>=300 served bars, signal on the last completed bar only).

VEHICLES (from the desk's own records, never invented):
  ADA, LINK: Alpaca spot ADA/USD and LINK/USD — the desk's served
    spot tape (warm CRYPTO_FETCHES ADA/USD|4Hour and LINK/USD|4Hour,
    ~540 bars) and its broker door; intents carry the slash form with
    time_in_force gtc, the proven crypto wire shape.
  ENJ: ENJ/USD is unlisted at Alpaca (42210000 asset-not-found,
    proven 2026-10-30/31); the execution form is the desk's
    kraken_paper class (ENJ-PAPER-20261116, desk3/dispatcher.py):
    the dispatcher fills these sleeves' ENJ/USD intents against the
    Kraken public spot tape (warm KRAKEN_SPOT_FETCHES ENJ/USD|4Hour)
    and journals venue="kraken_paper"; the sleeves read their own
    journal-derived book (own_book_view). The 3 ENJ ids are added to
    the dispatcher's ENJ_PAPER_SLEEVES class by this landing.
  Feed note, named: the source engine reads OKX 4h candles; the desk
    serves the same underlyings' spot 4h tape from Alpaca (ADA, LINK)
    and Kraken (ENJ). The signal math is venue-agnostic bar math;
    the feed substitution is the desk's standing F4 resolver form
    (desk3/crypto_bars.py) and is recorded here, not hidden.

FORWARD FALSIFIER (the intake's own, unchanged): at 20 resolved
forward fires per family on md2 terms — here, per family across its
3 sleeves' live desk trades — a family whose net after the source
fee model (10bp one-way) is at or below zero is closed and reported
at B5 with the counts (midna-book intake, 2026-11-14). All three
families are calibration-pending in the frozen params; they fire
anyway (t460u: no paused sleeves).
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone

# ------------------------------------------------------------------
# Frozen params — byte-faithful copy of the VALUES in
# mdesk/t474u_params.json @ c2de069 (families bar_range_atr /
# mfi_gate / btc_stdev only; the other families are out of scope).
# ------------------------------------------------------------------
PARAMS = {
    "bar_range_atr": {"k": 2.0, "atr_n": 14, "lookback": 10,
                      "calibration_pending": True},
    "mfi_gate": {"theta": 15.0, "mfi_n": 14, "sma_n": 30,
                 "lookback_crypto": 10, "lookback_equity": 20,
                 "calibration_pending": True,
                 "crypto_mfi_calibration_pending": True},
    "btc_stdev": {"k": 0.5, "n": 20, "lookback": 10,
                  "calibration_pending": True},
}
FEE_1X_CRYPTO = 0.001  # params file fee_1x_crypto; backtest FEE_CRYPTO
MIN_4H = 300           # t474u_x.MIN_4H (scan warm-up gate)
H4_S = 4 * 3600
POS_FRAC = 0.25        # CryptoFilterTwin.pos_frac
PRINCIPAL = 10_000.0   # CryptoFilterTwin principal via _Base
HOLD_H = 16            # exit_reason: "fixed16h" at age >= 16 hours

_KIND_FAM = {"bratr": "bar_range_atr", "mfi": "mfi_gate",
             "stdev": "btc_stdev"}
_BASES = ("ADA", "ENJ", "LINK")
SPECS = {}
for _kind in ("bratr", "mfi", "stdev"):
    for _base in _BASES:
        _sid = f"crypto_{_kind}_{_base.lower()}"
        SPECS[_sid] = dict(
            kind=_kind, fam=_KIND_FAM[_kind], base=_base,
            inst=f"{_base}-USDT",            # source DataHub instId form
            archive_sym=f"{_base}USDT",      # source sleeve symbol form
            trade_sym=f"{_base}/USD",        # desk broker/tape form
            cadence_s=14400, session="24h")
INPUTS = ("bars", "positions")
PRODUCERS = (
    {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 900},
    {"name": "broker_readback", "outputs": ("positions",),
     "freshness_sla_s": 900},
)

NAN = float("nan")


# ------------------------------------------------------------------
# Indicator math — function-for-function port of mdesk/ind.py and
# mdesk/t474u_indicators.py (numpy originals; the desk runs stdlib
# only, so the same recursions/windows are written in pure Python —
# sma/ema/atr/mfi are sequential recursions or window sums whose
# float results agree with the numpy forms to <1e-9 on the fidelity
# window, measured in proof/t474u/t474u_fidelity_result.json).
# ------------------------------------------------------------------

def _sma(x, n):
    out = [NAN] * len(x)
    if len(x) >= n:
        run = math.fsum(x[:n])
        out[n - 1] = run / n
        for i in range(n, len(x)):
            run += x[i] - x[i - n]
            out[i] = run / n
    return out


def _stdev(x, n):
    """Population stdev (numpy np.std default ddof=0), windowed."""
    out = [NAN] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        m = math.fsum(w) / n
        out[i] = math.sqrt(math.fsum((v - m) ** 2 for v in w) / n)
    return out


def _atr(h, l, c, n=14):
    out = [NAN] * len(c)
    if not len(c):
        return out
    tr = [0.0] * len(c)
    tr[0] = h[0] - l[0]
    for i in range(1, len(c)):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]),
                    abs(l[i] - c[i - 1]))
    if len(c) >= n:
        out[n - 1] = math.fsum(tr[:n]) / n
        for i in range(n, len(c)):
            out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def bar_range_atr(h, l, c, atr_n=14):
    a = _atr(h, l, c, atr_n)
    out = [NAN] * len(c)
    for i in range(len(c)):
        if a[i] == a[i] and a[i] > 0:
            out[i] = (h[i] - l[i]) / a[i]
    return out


def _mfi(h, l, c, v, n=14):
    tp = [(h[i] + l[i] + c[i]) / 3.0 for i in range(len(c))]
    raw = [tp[i] * v[i] for i in range(len(c))]
    out = [NAN] * len(c)
    if len(c) <= n:
        return out
    pos = [0.0] * (len(c) - 1)
    neg = [0.0] * (len(c) - 1)
    for j in range(len(c) - 1):
        d = tp[j + 1] - tp[j]
        if d > 0:
            pos[j] = raw[j + 1]
        elif d < 0:
            neg[j] = raw[j + 1]
    cpos = [0.0]
    cneg = [0.0]
    for j in range(len(c) - 1):
        cpos.append(cpos[-1] + pos[j])
        cneg.append(cneg[-1] + neg[j])
    for i in range(n, len(c)):
        a = cpos[i] - cpos[i - n]
        b = cneg[i] - cneg[i - n]
        if b <= 0 and a > 0:
            out[i] = 100.0
        elif a <= 0 and b <= 0:
            out[i] = 50.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + a / b)
    return out


def mfi_gate(h, l, c, v, n=14, sma_n=30):
    m = _mfi(h, l, c, v, n)
    out = [NAN] * len(c)
    if len(m) < n + sma_n:
        return out
    for i in range(n + sma_n - 1, len(m)):
        w = m[i - sma_n + 1:i + 1]
        if not all(vv == vv for vv in w):
            continue
        s = math.fsum(w) / sma_n
        if s == 0:
            continue
        out[i] = 100.0 * (m[i] / s - 1.0)
    return out


def close_ma_stdev_z(c, n=20):
    s = _sma(c, n)
    d = _stdev(c, n)
    out = [NAN] * len(c)
    for i in range(len(c)):
        if s[i] == s[i] and d[i] == d[i] and d[i] > 0:
            out[i] = abs(c[i] - s[i]) / d[i]
    return out


def is_breakout(h, c, lookback, i):
    if i < 0:
        i = len(h) + i
    if i < lookback:
        return False
    return float(c[i]) > float(max(h[i - lookback:i]))


def filter_series(kind, h, l, c, v):
    """The family's filter array, source defaults wired to the
    frozen params exactly as CryptoFilterTwin.scan reads them."""
    p = PARAMS[_KIND_FAM[kind]]
    if kind == "bratr":
        return bar_range_atr(h, l, c, int(p.get("atr_n", 14)))
    if kind == "mfi":
        return mfi_gate(h, l, c, v, int(p.get("mfi_n", 14)),
                        int(p.get("sma_n", 30)))
    return close_ma_stdev_z(c, int(p.get("n", 20)))


def threshold(kind):
    p = PARAMS[_KIND_FAM[kind]]
    if kind == "mfi":
        return float(p.get("theta", 5.0))
    return float(p.get("k", 1.2 if kind == "bratr" else 1.0))


def lookback(kind):
    p = PARAMS[_KIND_FAM[kind]]
    return int(p.get("lookback", p.get("lookback_crypto", 10)))


def signal_at(kind, h, l, c, v, i):
    """Source scan's entry test at bar i (t474u_x.CryptoFilterTwin.
    scan with the bar as the last bar): breakout host, then the
    family filter strictly above its frozen threshold; a NaN filter
    value never fires."""
    if not is_breakout(h, c, lookback(kind), i):
        return False
    val = filter_series(kind, h, l, c, v)[i]
    return val == val and val > threshold(kind)


def fires_series(kind, bars):
    """Every bar index at which the source signal test fires over
    the series — the backtest replay's fire definition, the one
    historical_fires.json records. bars: list of {t,o,h,l,c,v}."""
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    c = [b["c"] for b in bars]
    v = [b["v"] for b in bars]
    ratio = filter_series(kind, h, l, c, v)
    th = threshold(kind)
    lb = lookback(kind)
    out = []
    for i in range(len(bars)):
        if not is_breakout(h, c, lb, i):
            continue
        val = ratio[i]
        if val == val and val > th:
            out.append(i)
    return out


def simulate_trades(kind, bars, fee=FEE_1X_CRYPTO, stress=(1, 2, 4, 5),
                    hold_bars=4, is_frac=0.7):
    """Port of tools/t474u_backtest.py _simulate + _metrics for one
    breakout-filter family at its frozen param (the backtest's
    sweep_breakout_filter record shape): signal on completed bar i
    fills at bar i+1 open, fixed hold of `hold_bars` bars (16h = 4
    bars of 4h), exit fill at the following open, no overlapping
    lot per series; IS/OOS split at int(n * is_frac) bars, trades
    assigned to the window their signal bar falls in."""
    n = len(bars)
    o = [b["o"] for b in bars]
    fires = set(fires_series(kind, bars))
    split = max(1, int(n * is_frac))

    def run(a, bnd):
        rets = {s: [] for s in stress}
        i = 0
        while i < n - 2:
            if i not in fires or not (a <= i < bnd):
                i += 1
                continue
            entry_i = i + 1
            if entry_i >= n:
                break
            fill_exit = min(n - 1, entry_i + hold_bars)
            if fill_exit <= entry_i:
                i += 1
                continue
            px_in, px_out = float(o[entry_i]), float(o[fill_exit])
            if px_in <= 0:
                i = fill_exit
                continue
            raw = px_out / px_in - 1.0
            for s in stress:
                rets[s].append(raw - 2.0 * fee * s)
            i = fill_exit
        return rets

    def metrics(rets):
        r = list(rets)
        if not r:
            return dict(n=0, win=None, net=0.0, avg=None, maxdd=0.0,
                        pf=None, npdd=None)
        eq = []
        run_eq = 0.0
        for x in r:
            run_eq += x
            eq.append(run_eq)
        peak = eq[0]
        maxdd = 0.0
        for x in eq:
            peak = max(peak, x)
            maxdd = max(maxdd, peak - x)
        wins = [x for x in r if x > 0]
        losses = [x for x in r if x < 0]
        gp = math.fsum(wins) if wins else 0.0
        gl = -math.fsum(losses) if losses else 0.0
        pf = (gp / gl) if gl > 0 else (None if gp == 0 else float("inf"))
        net = math.fsum(r)
        # Source _metrics: npdd divides the UNROUNDED net by the
        # UNROUNDED maxdd (the round() calls in its return dict do
        # not rebind the locals) — reproduced exactly; rounding
        # maxdd first moves npdd in the 4th decimal on 6 of 12
        # sleeves (measured in the fidelity run).
        return dict(
            n=len(r), win=round(sum(1 for x in r if x > 0) / len(r), 4),
            net=round(net, 6),
            avg=round(math.fsum(r) / len(r), 6),
            maxdd=round(maxdd, 6),
            pf=None if pf is None else (round(pf, 4)
                                         if pf != float("inf") else "inf"),
            npdd=None if maxdd <= 0 else round(net / maxdd, 4))

    out = {}
    for name, a, bnd in (("IS", 0, split), ("OOS", split, n)):
        rets = run(a, bnd)
        out[name] = {f"{s}x": metrics(rets[s]) for s in stress}
    return out


# ------------------------------------------------------------------
# Live evaluation (desk3 contract: evaluate(sid, view, ctx) -> the
# aster-family plain-dict intents).
# ------------------------------------------------------------------

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


def _bars(view, spec):
    m = (view or {}).get("bars") or {}
    rows = None
    for k in (f"{spec['archive_sym']}|4Hour", f"{spec['trade_sym']}|4Hour"):
        if m.get(k):
            rows = list(m[k])
            break
    if rows is None:
        # F4 resolver: archive USDT keys resolve to the served spot
        # forms (ADA/USD, LINK/USD Alpaca spot; ENJ/USD Kraken spot).
        from .crypto_bars import resolve_bars
        rows = resolve_bars(m, spec["archive_sym"], ("4Hour",))
    out = []
    for r in rows or []:
        g = r.get
        try:
            out.append({"t": g("t", g("timestamp_ms", g("timestamp"))),
                        "o": float(g("o", g("open"))),
                        "h": float(g("h", g("high"))),
                        "l": float(g("l", g("low"))),
                        "c": float(g("c", g("close"))),
                        "v": float(g("v", g("volume", 0.0)))})
        except (TypeError, ValueError, AttributeError):
            continue
    out.sort(key=lambda b: _ts(b["t"]) or datetime.min.replace(
        tzinfo=timezone.utc))
    return out


def _position(view, spec):
    base = spec["base"]
    for p in (view or {}).get("positions") or []:
        sym = str(p.get("symbol") or "")
        norm = sym.replace("/", "").replace("-", "").upper()
        if norm in (f"{base}USD", f"{base}USDT"):
            try:
                q = float(p.get("qty") or 0)
            except (TypeError, ValueError):
                continue
            if q != 0:
                return p
    return None


def _state(ctx, sid):
    sd = (ctx or {}).get("state_dir")
    if not sd:
        return {}, None
    path = os.path.join(sd, f"t474u_{sid}.json")
    try:
        return (json.load(open(path)) if os.path.exists(path)
                else {}), path
    except Exception:
        return {}, path


def _save_state(path, st):
    if path:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(st, fh, sort_keys=True)


def _intent(sid, kind, spec, side, qty, reason, price=None):
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    d = {"intent_id": f"{sid}-{stamp}-1-{spec['archive_sym']}",
         "kind": kind, "symbol": spec["trade_sym"], "side": side,
         "qty": qty, "order_type": "market", "limit_price": None,
         "stop_price": None, "reason": reason,
         # proven crypto wire shape (aster family): gtc, never day.
         "time_in_force": "gtc"}
    if price is not None:
        d["price_hint"] = float(price)
    if kind == "exit":
        d["position_intent"] = "sell_to_close"
    return d


def evaluate(sid, view, ctx=None):
    spec = SPECS[sid]
    kind = spec["kind"]
    view = view or {}
    now = (ctx or {}).get("now")
    now = _ts(now) if now is not None else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    bars = _bars(view, spec)
    state, spath = _state(ctx, sid)
    pos = _position(view, spec)
    if pos is not None and float(pos.get("qty") or 0) > 0:
        # Source exit_reason: age from confirm_t (the entry signal
        # bar's t + 4h, stored at entry) >= 16h -> "fixed16h".
        # Fallback anchor, the aster absorption family's own form:
        # the position's opened_at + 16h when no state was kept.
        anchor = None
        ct = state.get("confirm_t")
        if ct:
            anchor = _ts(ct)
        if anchor is None:
            opened = _ts(pos.get("opened_at") or pos.get("entry_time"))
            if opened is not None:
                anchor = opened
        if anchor is None:
            return []  # fail closed: no anchor, no guessed exit
        age_h = (now - anchor).total_seconds() / 3600.0
        if age_h < HOLD_H:
            return []
        price = bars[-1]["c"] if bars else None
        out = [_intent(sid, "exit", spec, "sell",
                       abs(float(pos["qty"])),
                       f"{sid}:fixed16h age_h={age_h:.2f}", price=price)]
        state.pop("confirm_t", None)
        _save_state(spath, state)
        return out
    if pos is not None:
        return []
    # Source scan: series shorter than MIN_4H cannot evaluate.
    if len(bars) < MIN_4H:
        return []
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    c = [b["c"] for b in bars]
    v = [b["v"] for b in bars]
    i = len(bars) - 1
    if not is_breakout(h, c, lookback(kind), i):
        return []
    val = filter_series(kind, h, l, c, v)[i]
    if not (val == val) or val <= threshold(kind):
        return []
    price = float(c[i])
    if price <= 0:
        return []
    cash = float((view.get("slice") or {}).get("cash_usd")
                 or PRINCIPAL)
    qty = POS_FRAC * cash / price
    if qty <= 0:
        return []
    bar_t = _ts(bars[i]["t"])
    confirm_t = (bar_t.timestamp() + H4_S) if bar_t is not None else None
    if confirm_t is not None:
        state["confirm_t"] = datetime.fromtimestamp(
            confirm_t, timezone.utc).isoformat()
        _save_state(spath, state)
    meta_name = {"bratr": "ratio", "mfi": "mfi_gate",
                 "stdev": "z"}[kind]
    return [_intent(
        sid, "entry", spec, "buy", qty,
        f"{sid}:4h_breakout10 {meta_name}={val:.4f} "
        f"thr={threshold(kind)} close={price} "
        f"calibration_pending", price=price)]


def config_rows():
    rows = []
    for sid, spec in SPECS.items():
        enj = spec["base"] == "ENJ"
        row = {
            "id": sid, "module": f"adapters3.{sid}",
            "cadence_s": spec["cadence_s"], "session": spec["session"],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "bp_buffer_frac": 0.02, "flat_by_close": False,
            "flatten_time_et": None,
            "params": {"t474u_family": spec["fam"],
                       "t474u_kind": spec["kind"],
                       "calibration_pending": True,
                       "source": "md2 mdesk/engines/t474u_x.py @ "
                                 "master-desk c2de06921bac"},
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
            "inputs": ["bars", "positions"],
            "parked": False,
        }
        if enj:
            # ENJ-PAPER-20261116 form, identical to the other 22
            # kraken_paper rows: journal-derived own book, fills at
            # the dispatcher against the Kraken spot tape.
            row["own_book_view"] = True
            row["params"]["parked_reason"] = (
                "T474U-CRYPTO-PORT-20261116: faithful desk port of "
                "md2 t474u_x CryptoFilterTwin on ENJ. Fed from Kraken "
                "public spot (ENJ/USD bars served by desk3 "
                "KrakenProducer). ENJ-PAPER-20261116: execution form "
                "is the free_kraken paper form: entries and exits "
                "fill at the dispatcher against the Kraken public "
                "spot feed, journaled as fill rows with venue "
                "kraken_paper; ENJ is never dispatched to Alpaca "
                "(ENJ/USD unlisted, broker 42210000). The sleeve "
                "reads its own journal-derived book (own_book_view).")
        rows.append(row)
    return rows
