"""Q07 alt-data confluence engine (Lazarus batch 6).

Faithful reading of the consolidated catalog section 4.1 family rule for
the Research Lab Q07 weekly lanes: take the Tensor 1W signal of the named
family (Green / Swing) in the named cap band, apply the named alt-data
filters, buy only on a QQQ-down day within 5 sessions of the signal, and
exit on a 15% stop or at the time horizon in the name (52 or 78 weeks).
Standard sizing: 1 slot at $1,000.

Signal source: the CSV declares the feed as the sleeve_feed composer
(tracker ledger + alt-data tags) publishing sleeve_fires_v1.json. In v3
that is the producer key "sleeve_fires" in the cycle snapshot (view
"extra"), one fire row per sleeve: {sleeve, symbol, signal_date,
cap_band, insider_buys, wiki_views_30d}. Price-derived filters (cheap5,
deep70, mom6) are computed from snapshot daily bars; vix20 from the
snapshot "vix" value; the QQQ-down gate from QQQ daily bars.

Filter-token readings (underspecified in the sources; recorded in
FIDELITY-LEDGER.md): deep70 = close at or below 70% of the trailing
252-session high (>=30% drawdown); wcov = Wikipedia coverage present
(wiki_views_30d > 0); wlow = low Wikipedia attention
(0 <= wiki_views_30d < 1000); mom6 = positive 6-month momentum
(close vs close 126 sessions ago > 0); ins2 = insider_buys >= 2;
cheap5 = last close < $5; vix20 = VIX >= 20.
"""
from __future__ import annotations
from datetime import datetime, timezone

from desk3.contract import ExitRule, Intent

SLOT_USD = 1000.0
STOP_PCT = 0.15
MAX_SIGNAL_AGE_SESSIONS = 5
WIKI_LOW_MAX_VIEWS = 1000
MOM6_SESSIONS = 126
DEEP70_HIGH_SESSIONS = 252

CAP_BANDS_USD = {"mi": (0.0, 300_000_000.0),
                 "sm": (300_000_000.0, 2_000_000_000.0),
                 "ml": (2_000_000_000.0, float("inf"))}


def _bars(view, symbol):
    rows = (view.get("bars") or {}).get(f"{symbol}|1day") or []
    return sorted(rows, key=lambda r: str(r.get("t")))


def _today(view, ctx):
    now = view.get("now") or (ctx or {}).get("now")
    dt = (now if isinstance(now, datetime)
          else datetime.fromisoformat(str(now).replace("Z", "+00:00")))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.date()


def _sessions_between(qqq_bars, start, end):
    """Trading sessions in (start, end] per QQQ bar dates."""
    n = 0
    for r in qqq_bars:
        d = str(r.get("t"))[:10]
        if start < d <= end:
            n += 1
    return n


def _filters_pass(spec, fire, bars, vix, wlow_evidence=True):
    px = float(bars[-1]["c"]) if bars else None
    if "ins2" in spec["filters"]:
        if int(fire.get("insider_buys") or 0) < 2:
            return False, "ins2"
    if "cheap5" in spec["filters"]:
        if px is None or not px < 5.0:
            return False, "cheap5"
    if "deep70" in spec["filters"]:
        if px is None or len(bars) < 20:
            return False, "deep70"
        hi = max(float(r["h"]) for r in bars[-DEEP70_HIGH_SESSIONS:])
        if not px <= 0.70 * hi:
            return False, "deep70"
    if "wcov" in spec["filters"]:
        if not float(fire.get("wiki_views_30d") or 0) > 0:
            return False, "wcov"
    if "wlow" in spec["filters"]:
        # ENH-Q07WLOW-20261024: missing wiki evidence must fail closed
        # (every other filter in this engine does); pre-change a fire
        # with NO wiki data defaulted to 0 views and passed as "low".
        if wlow_evidence:
            if fire.get("wiki_low") is True:
                pass
            elif fire.get("wiki_views_30d") is not None:
                if not float(fire["wiki_views_30d"]) < WIKI_LOW_MAX_VIEWS:
                    return False, "wlow"
            else:
                return False, "wlow_unfed"
        elif not float(fire.get("wiki_views_30d") or 0) < WIKI_LOW_MAX_VIEWS:
            return False, "wlow"
    if "mom6" in spec["filters"]:
        if px is None or len(bars) <= MOM6_SESSIONS:
            return False, "mom6"
        if not px > float(bars[-1 - MOM6_SESSIONS]["c"]):
            return False, "mom6"
    if "vix20" in spec["filters"]:
        if vix is None or not float(vix) >= 20.0:
            return False, "vix20"
    return True, ""


def evaluate_q07(spec, view, ctx):
    view = view or {}
    extra = dict(view.get("extra") or {})
    pextra = ((view.get("params") or {}).get("extra") or {})
    for k, v in pextra.items():
        extra.setdefault(k, v)
    fires = extra.get("sleeve_fires") or []
    vix = extra.get("vix")
    today = _today(view, ctx)
    qqq = _bars(view, "QQQ")
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) > 0]
    held = {p["symbol"]: p for p in positions}
    intents = []

    # ---- exits: 15% stop or horizon expiry (family rule) ----
    for sym, pos in held.items():
        avg = float(pos.get("avg_price") or 0)
        bars = _bars(view, sym)
        px = float(bars[-1]["c"]) if bars else None
        reason = None
        if avg > 0 and px is not None and px <= avg * (1.0 - STOP_PCT):
            reason = "q07_stop15"
        opened = str(pos.get("opened_at") or "")[:10]
        if reason is None and opened:
            try:
                from datetime import date as _date
                age_wk = (_date.fromisoformat(today.isoformat())
                          - _date.fromisoformat(opened)).days / 7.0
                if age_wk >= spec["horizon_wk"]:
                    reason = "q07_horizon_exit"
            except ValueError:
                pass
        if reason:
            intents.append(Intent(
                kind="exit", symbol=sym, qty=float(pos["qty"]),
                price_hint=px, reason=reason,
                side="sell", position_intent="sell_to_close"))

    # ---- entries ----
    if held:
        return intents  # 1 slot: occupied
    if len(qqq) < 2:
        return intents
    qqq_down = float(qqq[-1]["c"]) < float(qqq[-2]["c"])
    if not qqq_down:
        return intents
    # ENH-Q07FRESH-20261024: the 1-slot lane took whichever eligible
    # fire the producer listed FIRST; a 5-session-old fire crowded out
    # a same-day fire. ON (default): freshest-signal-first. OFF:
    # producer list order exactly. Switch extra.q07_enh[sid].fresh_first.
    _elig = []
    for fire in fires:
        if fire.get("sleeve") != spec["id"]:
            continue
        sym = fire.get("symbol")
        if not sym or sym in held:
            continue
        band = fire.get("cap_band")
        if band is not None and band != spec["band"]:
            continue
        mcap = fire.get("mcap_usd")
        if mcap is not None:
            lo, hi = CAP_BANDS_USD[spec["band"]]
            if not (lo <= float(mcap) < hi):
                continue
        sig = str(fire.get("signal_date") or "")[:10]
        if not sig:
            continue
        age = _sessions_between(qqq, sig, today.isoformat())
        if age < 0 or age > MAX_SIGNAL_AGE_SESSIONS:
            continue
        bars = _bars(view, sym)
        if not bars:
            continue
        # ENH25-Q07-STALEBARS-20261024: bar staleness of the SYMBOL —
        # filters/sizing ran on bars[-1] however old it was; a halted
        # or delisted name whose last bar predates the 5-session
        # signal window still entered at that ancient close.
        _lastd = str(bars[-1].get("t") or "")[:10]
        _stale = bool(_lastd) and _sessions_between(
            qqq, _lastd, today.isoformat()) > MAX_SIGNAL_AGE_SESSIONS
        _elig.append((age, fire, sym, sig, bars, _stale))
    _svf = (extra.get("q07_enh") or {}).get(spec["id"])
    _fresh_on = bool(_svf.get("fresh_first", True)) if isinstance(_svf, dict) else True
    _ordered = sorted(_elig, key=lambda e: e[0]) if _fresh_on else _elig
    if len(_elig) >= 2:
        _jr = extra.get("q07_exp_journal")
        if isinstance(_jr, dict) and isinstance(_jr.get("records"), list):
            _jr["records"].append({
                "exp_id": "ENH-Q07FRESH-20261024", "sleeve": spec["id"],
                "control_first": _elig[0][1].get("symbol"),
                "treatment_first": sorted(_elig, key=lambda e: e[0])[0][1].get("symbol"),
                "control_age": _elig[0][0],
                "treatment_age": min(e[0] for e in _elig)})
    for age, fire, sym, sig, bars, _stale in _ordered:
        # ENH25-Q07-STALEBARS-20261024: ON (default): refuse the entry
        # on stale symbol bars (paired journal record; the OFF control
        # enters on the stale close exactly as pre-change).
        _svb = (extra.get("q07_enh") or {}).get(spec["id"])
        _stale_on = bool(_svb.get("fresh_bars", True)) if isinstance(_svb, dict) else True
        if _stale:
            _jr2 = extra.get("q07_exp_journal")
            if isinstance(_jr2, dict) and isinstance(_jr2.get("records"), list):
                _jr2["records"].append({
                    "exp_id": "ENH25-Q07-STALEBARS-20261024",
                    "sleeve": spec["id"], "symbol": sym,
                    "control_enter": True, "treatment_enter": not _stale_on,
                    "last_bar": str(bars[-1].get("t") or "")[:10]})
            if _stale_on:
                continue
        _enh = extra.get("q07_enh") or {}
        _sv = _enh.get(spec["id"]) if isinstance(_enh, dict) else None
        enh_on = bool(_sv.get("wlow_evidence", True)) if isinstance(_sv, dict) else True
        ctrl_ok, _ = _filters_pass(spec, fire, bars, vix, wlow_evidence=False)
        treat_ok, _why = _filters_pass(spec, fire, bars, vix, wlow_evidence=True)
        journal = extra.get("q07_exp_journal")
        if isinstance(journal, dict) and isinstance(journal.get("records"), list):
            journal["records"].append({
                "exp_id": "ENH-Q07WLOW-20261024", "sleeve": spec["id"],
                "symbol": sym, "control_enter": ctrl_ok,
                "treatment_enter": treat_ok})
        ok = treat_ok if enh_on else ctrl_ok
        if not ok:
            continue
        px = float(bars[-1]["c"])
        qty = int(SLOT_USD // px)
        if qty < 1:
            continue
        horizon_bars = spec["horizon_wk"] * 5
        intents.append(Intent(
            kind="enter", symbol=sym, qty=qty, price_hint=px,
            stop=round(px * (1.0 - STOP_PCT), 4),
            exit_rules=(ExitRule("stop", round(px * (1.0 - STOP_PCT), 4)),
                        ExitRule("time_bars", float(horizon_bars))),
            reason=(f"q07_{spec['family']}_tensor1w_{spec['band']} "
                    f"filters={'+'.join(spec['filters'])} "
                    f"signal={sig} age_sessions={age}"),
            side="buy", position_intent="buy_to_open",
            signal_date=sig))
        break  # 1 slot at $1,000
    return intents
