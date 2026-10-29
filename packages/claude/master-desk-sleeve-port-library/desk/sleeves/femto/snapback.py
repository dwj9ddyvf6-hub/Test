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
"""
from bisect import bisect_left
from datetime import date, datetime, timedelta, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

BAND_FRAC = 0.10
HOLD_DAYS = 91
COST_BPS_SIDE = 0.015

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
    # master-desk: in symbol order. The old code iterated the set itself, whose order is the string hash's and so
    # changes with every process's PYTHONHASHSEED; the stable sorts below keep it among exact ties of the weekly
    # dollar volume (names that never traded, one history under two tickers), so the band edge, the terciles and
    # the flagged order there were a coin toss per run. Without such a tie the result is the same.
    for s in sorted(set(wk) & set(dly)):
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


# ---------------------------------------------------------------- master-desk: the old runtime, restored
from zoneinfo import ZoneInfo  # noqa: E402

from . import sleeve_core as core  # noqa: E402

ET = ZoneInfo("America/New_York")
MIN_FRESH = 0.5            # rank waits until most of the genome carries the rank day's bar (old: rank_wait)


def weekly_from_daily(daily):
    """Monday-bucketed weekly bars from daily bars (close = the week's last close, volume = the week's sum):
    what the old Alpaca 1Week bars carried for compute_flags."""
    out = {}
    for s, bl in (daily or {}).items():
        wk = {}
        for b in bl or ():
            m = monday_of(_bar_date(b))
            e = wk.get(m)
            if e is None:
                wk[m] = {"t": float(b["t"]), "c": float(b["c"]), "v": float(b.get("v") or 0)}
            else:
                e["c"] = float(b["c"])
                e["v"] += float(b.get("v") or 0)
        out[s] = [wk[m] for m in sorted(wk)]
    return out


def _now_et(context):
    return datetime.fromtimestamp(float(context.now), tz=ET)


def _phase(context):
    """rank: Friday after the close (old cron 16:35; here once the genome refresh landed); fill: Monday 10:35."""
    t = _now_et(context)
    if t.weekday() == 4 and (t.hour, t.minute) >= (16, 35):
        return "rank"
    if t.weekday() == 0 and (10, 35) <= (t.hour, t.minute) < (16, 0):
        return "fill"
    return None


def rank(bars, context, meta):
    """old mode_rank on completed bars: flagged names not held and not exited within 91 days, the capacity
    break, fill-Monday + 91 exit dates, positions due by today staged to sell, merged into the surviving
    pending (old buys first). None when the genome's bars are not yet the rank day's (rank waits)."""
    extra = context.extra or {}
    state = extra.get("sleeve_state") or {}
    today = context.session
    dated = sum(1 for bl in bars.values() if bl and _bar_date(bl[-1]).isoformat() == today)
    if not bars or dated < MIN_FRESH * len(bars):
        return None
    friday = date.fromisoformat(today)
    while friday.weekday() != 4:
        friday -= timedelta(days=1)
    flagged = compute_flags(weekly_from_daily(bars), bars, friday)
    book = core.book_of(state)
    old = dict(meta.get("pending") or {})
    prev_staged = set(old.get("buys") or [])
    buys = []
    for f in flagged:
        s = f["symbol"]
        if s in book:
            continue
        le = (state.get(s) or {}).get("last_exit_date")
        if le:
            try:
                if (date.fromisoformat(today) - date.fromisoformat(str(le)[:10])).days < HOLD_DAYS:
                    continue
            except ValueError:
                pass
        buys.append(s)
        if len(buys) + len(book) + len(prev_staged - set(book) - set(buys)) >= core.MAX_POSITIONS:
            break
    fill_monday = date.fromisoformat(today)
    while fill_monday.weekday() != 0:
        fill_monday += timedelta(days=1)
    exit_dates = {s: (fill_monday + timedelta(days=HOLD_DAYS)).isoformat() for s in buys}
    sells = [s for s, p in book.items() if p.get("exit_due_date") and str(p["exit_due_date"]) <= today]
    old_sells = list(old.get("sells") or [])
    merged_dates = dict(old.get("exit_dates") or {})
    merged_dates.update(exit_dates)
    return {"buys": core.merge_pending_buys(old.get("buys") or [], buys, len(book)),
            "sells": old_sells + [s for s in sells if s not in old_sells],
            "exit_dates": merged_dates, "rank_friday": friday.isoformat(), "flagged": len(flagged)}


class Snapback(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old two-phase runtime. Friday after the close the rank stages pending (next_meta);
        Monday 10:35 the old sleeve_core fill law executes it (30% sleeve budget split over the staged names,
        all-in at 150bp/side, max 10 names, exits on the 91-day due date)."""
        if _phase(context) != "fill":
            return []
        extra = context.extra or {}
        meta = extra.get("meta") or {}
        close_ts = _now_et(context).replace(hour=16, minute=0, second=0, microsecond=0).timestamp()
        intents, _left = core.fill_intents(Intent, extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                           float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                           context.session, float(context.now), "snapback", close_ts)
        return intents


def next_meta(bars, slice_state, context, intents=()):
    extra = context.extra or {}
    meta = dict(extra.get("meta") or {})
    ph = _phase(context)
    if ph == "rank":
        friday = date.fromisoformat(context.session)
        while friday.weekday() != 4:
            friday -= timedelta(days=1)
        if meta.get("rank_friday") != friday.isoformat():
            pend = rank(bars, context, meta)
            if pend is not None:
                meta["pending"] = {k: v for k, v in pend.items() if k not in ("rank_friday", "flagged")}
                meta["rank_friday"] = pend["rank_friday"]
                meta["last_flagged"] = pend["flagged"]
    elif ph == "fill":
        _s, _b, left = core.fill(extra.get("sleeve_state") or {}, meta.get("pending") or {},
                                 float(context.equity or 0.0), extra.get("quotes") or {}, COST_BPS_SIDE,
                                 context.session, float(context.now), "snapback")
        meta["pending"] = left
    return meta


def signal(bars, slice_state, context):
    return Snapback().signal(bars, slice_state, context)
