"""Snapback — lean-desk port.

EXTRACTED from the old desk's snapback_sleeve.py. tercile_flags and
compute_flags ported verbatim in behavior (bar rows become dicts;
weekly-bar Monday bucketing identical); plumbing (sleeve_core state,
ledgers) is core-owned. See ports/snapback.md.

Strategy (old module; small-cap beaten-down replication family):
universe = bottom decile (BAND_FRAC 0.10, min 9 names) by trailing-52w
mean weekly dollar volume. Features per name: 20d mean daily spread
(h-l)/c, beat_run13 (13-week return <= -20%), near_low (distance above
the 52w low close). Flag = spread in the TOP tercile AND beat_run13
AND near_low NOT in the bottom tercile; ranked by spread desc.
Hold 91 days (13 weeks); 91-day rebuy de-overlap via last_exit.
Cost model 150bp/side (Decision D5) is a study parameter, kept as data.

Inputs via context.extra:
  "weekly": {SYM: [weekly bar dicts]} (bars arg carries the DAILY bars)
  "sleeve_state": {SYM: {"position": {...} | None}}
  "last_exit": {SYM: "YYYY-MM-DD"}
Bars: dicts {"t","o","h","l","c","v"} ascending.

ENH (IMPROVE-snapback, Edge program 2026-10-24): enforce the desk's
standard sleeve-local cap MAX_POSITIONS = 10 — count the open book
plus this pass's entries, taking flagged names in the existing
spread-descending order; further flagged names that week are not
taken. Snapback was the only 1%-notional sleeve in its family
without the cap. Switched by context.extra["snapback_enhance"]
["position_cap"] (default ON; OFF restores the pre-change rule
exactly — every flagged name taken). Paired records ride the
snapback_enh_journal (adopted from context.extra, filed on
self.last_evaluation); the control never emits intents.
"""
from bisect import bisect_left
from datetime import date, datetime, timedelta, timezone

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

BAND_FRAC = 0.10
HOLD_DAYS = 91
COST_BPS_SIDE = 0.015
MAX_POSITIONS = 10  # ENH: the desk's standard sleeve-local cap

# ------------------------------------------------------------ ENH
ENH_EXP_ID = "ENH-SNAPBACK-20261024"


def position_cap_enabled(extra):
    """ctx.extra['snapback_enhance']['position_cap'], default ON;
    non-dict override ignored (ENH2 idiom)."""
    ov = (extra or {}).get("snapback_enhance")
    if isinstance(ov, dict) and "position_cap" in ov:
        return bool(ov["position_cap"])
    return True


def _enh_journal(extra):
    raw = (extra or {}).get("snapback_enh_journal")
    if isinstance(raw, dict) and raw.get("exp_id") == ENH_EXP_ID \
            and isinstance(raw.get("records"), list):
        return raw
    return {"exp_id": ENH_EXP_ID, "records": []}

CONFIG = SleeveConfig(
    sleeve_id="snapback", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "last_exit": "dict"},
    risk_pct=None)


def _bar_date(b):
    return datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                  tz=timezone.utc).date()


def tercile_flags(pairs):
    """Verbatim: {key: 'lo'|'mid'|'hi'} by sorted value; {} if n < 3."""
    vals = sorted(pairs, key=lambda kv: kv[1])
    n = len(vals)
    if n < 3:
        return {}
    out = {}
    for i, (k, _) in enumerate(vals):
        out[k] = "lo" if i < n / 3 else ("hi" if i >= 2 * n / 3 else "mid")
    return out


def monday_of(d):
    return d - timedelta(days=d.weekday())


def compute_flags(weekly, daily, friday):
    """Verbatim port of the old compute_flags. weekly/daily: {sym: bars};
    friday: date of the signal week's Friday."""
    M = monday_of(friday)
    miso = M.isoformat()
    wk = {}
    for s, bl in weekly.items():
        seen = {}
        for b in bl:
            m = monday_of(_bar_date(b))
            seen[m] = (float(b["c"]), float(b["v"] or 0))
        mons_s = sorted(seen)
        wk[s] = (mons_s, [seen[m][0] for m in mons_s],
                 [seen[m][1] for m in mons_s])
    dly = {}
    for s, bl in daily.items():
        dly[s] = ([_bar_date(b).isoformat() for b in bl], bl)
    cands = []
    for s in set(wk) & set(dly):
        mons, closes, vols = wk[s]
        widx = bisect_left(mons, M) - 1
        if widx < 51:
            continue
        wsum = sum((closes[j] or 0) * (vols[j] or 0)
                   for j in range(widx - 51, widx + 1))
        cands.append((s, wsum / 52, widx))
    if not cands:
        return []
    cands.sort(key=lambda x: x[1])
    n_band = max(9, int(len(cands) * BAND_FRAC))
    band = cands[:n_band]
    feats = {}
    for s, wkvol, widx in band:
        mons, closes, vols = wk[s]
        ei = bisect_left(mons, M)
        if ei >= len(mons) or mons[ei] != M:
            continue
        c0 = closes[ei]
        if not c0 or c0 <= 0:
            continue
        c = closes[widx]
        if not c or c <= 0:
            continue
        ret13 = (c / closes[widx - 13] - 1
                 if closes[widx - 13] and closes[widx - 13] > 0 else None)
        win52 = [x for x in closes[widx - 51:widx + 1] if x]
        if not win52:
            continue
        lo52 = min(win52)
        near_low = (c - lo52) / lo52 if lo52 else None
        ddates, dbars = dly[s]
        didx = bisect_left(ddates, miso) - 1
        if didx < 20:
            continue
        win20 = dbars[didx - 19:didx + 1]
        sp = [(float(b["h"]) - float(b["l"])) / float(b["c"])
              for b in win20 if b["c"]]
        if not sp:
            continue
        feats[s] = {"spread": sum(sp) / len(sp),
                    "beat_run13": bool(ret13 is not None and ret13 <= -0.20),
                    "near_low": near_low, "close": c0, "ret13": ret13,
                    "wkvol": wkvol}
    sp_terc = tercile_flags([(s, f["spread"]) for s, f in feats.items()])
    nl_terc = tercile_flags([(s, f["near_low"]) for s, f in feats.items()
                             if f["near_low"] is not None])
    flagged = []
    for s, f in feats.items():
        if s not in sp_terc or s not in nl_terc:
            continue
        if sp_terc[s] == "hi" and f["beat_run13"] and nl_terc[s] != "lo":
            flagged.append({"symbol": s, "close": round(f["close"], 2),
                            "spread": round(f["spread"], 4),
                            "ret13": (round(f["ret13"], 4)
                                      if f["ret13"] is not None else None),
                            "near_low": (round(f["near_low"], 4)
                                         if f["near_low"] is not None else None),
                            "wkvol": round(f["wkvol"], 0)})
    flagged.sort(key=lambda r: r["spread"], reverse=True)
    return flagged


class Snapback(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        weekly = extra.get("weekly") or {}
        state = extra.get("sleeve_state") or {}
        last_exit = extra.get("last_exit") or {}
        equity = float(context.equity or 0.0)
        today = date.fromisoformat(context.session)
        enh_on = position_cap_enabled(extra)
        journal = _enh_journal(extra)
        intents = []
        # time exits: 91 calendar days held (old bookkeeping is date-based)
        for sym, st in state.items():
            p = (st or {}).get("position")
            if not p or not p.get("entry_date"):
                continue
            try:
                held = (today - date.fromisoformat(str(p["entry_date"])[:10])).days
            except ValueError:
                continue
            qty = int(float(p.get("qty") or 0))
            if held >= HOLD_DAYS and qty > 0:
                bl = bars.get(sym) or []
                px = round(float(bl[-1]["c"]), 2) if bl else None
                intents.append(Intent(
                    "exit", sym, qty_hint=qty, price_hint=px,
                    reason="snapback time exit: held %dd >= %d" % (held, HOLD_DAYS)))
        if equity <= 0 or not weekly:
            self.last_evaluation = {"snapback_enh_journal": journal}
            return intents
        # signal week = the week ending the most recent Friday <= today
        friday = today - timedelta(days=(today.weekday() - 4) % 7)
        held_syms = {s for s, st in state.items() if (st or {}).get("position")}
        open_n = len(held_syms)
        for row in compute_flags(weekly, bars, friday):
            sym = row["symbol"]
            if sym in held_syms:
                continue
            if enh_on and open_n >= MAX_POSITIONS:
                journal["records"].append({
                    "symbol": sym, "session": context.session,
                    "control": "enter", "treatment": "refuse_cap",
                    "open_before": open_n, "cap": MAX_POSITIONS,
                    "enhance_switch": enh_on})
                continue
            le = last_exit.get(sym)
            if le:
                try:
                    if (today - date.fromisoformat(str(le)[:10])).days < HOLD_DAYS:
                        continue  # 91-day rebuy de-overlap
                except ValueError:
                    pass
            px = row["close"]
            if px <= 0:
                continue
            qty = int((equity * 0.01) // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            journal["records"].append({
                "symbol": sym, "session": context.session,
                "control": "enter", "treatment": "enter",
                "open_before": open_n, "cap": MAX_POSITIONS,
                "enhance_switch": enh_on})
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=px,
                exit_rules=(ExitRule("time_bars", float(HOLD_DAYS)),),
                reason="snapback flag: spread=%.4f ret13=%s near_low=%s wkvol=%.0f"
                       % (row["spread"], row["ret13"], row["near_low"],
                          row["wkvol"])))
            open_n += 1
        self.last_evaluation = {"snapback_enh_journal": journal}
        return intents


def signal(bars, slice_state, context):
    return Snapback().signal(bars, slice_state, context)
