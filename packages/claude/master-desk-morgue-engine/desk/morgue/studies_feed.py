"""Real inputs for the studies: the defect Muse's daily cycle left.

Silicon's studies_card.main() passed bars_by_symbol={} to every study, so wall validation could never grade, and the earnings,
squeeze and gap / opening-range studies had no loader at all: only fixtures ever produced a number, while the README called
the slice 'INTEGRATED'. Here every study is fed from data the desk holds, and a study whose input is missing says which:

  gap fill, opening range   SPY's regular-session 1-minute bars of the last 20 sessions (Alpaca through the desk's client;
                            the sessions already fetched are cached under cache/morgue/intraday/, so a night asks for the
                            new session only), the prior close from the daily bars
  earnings distributions    the 8-K Item 2.02 dates of the board's top names (the institutional crawl's records) against
                            the daily bars
  wall validation           the ledger's Map cards against the completed daily bars of SPY, QQQ and IWM
  squeeze                   the short-interest readings of the crawl (shares short over EDGAR shares outstanding) with the
                            daily bars and the FNQC short-volume ratio
  state vectors             SPY's (P, V, D, G, IV) of each session, appended to state/morgue/state_vectors.jsonl: price and
                            volatility from the bars, D from the FNQC history the Map job keeps, G from the Map card's net
                            gamma, IV from the 30-day IV history; the nearest-neighbour read waits for 126 accrued sessions
                            (Silicon named G and IV and computed neither)
Everything here is injectable and touches no network but through the Alpaca client it is handed."""
import json
import math
import os
from datetime import datetime, timezone

from .. import calendar as cal
from ..util import read_json, write_json_atomic
from . import cache_path, state_path, studies

INTRADAY_SESSIONS = 20
INTRADAY_KEEP = 60
FNQC_HISTORY = "fnqc_history.jsonl"
STATE_VECTORS = "state_vectors.jsonl"


# ---- gap fill and opening range: SPY's 1-minute sessions ----------------------------------------------------------------

def minute_of(ts_iso, day):
    """minutes after the 09:30 ET open of `day` for an RFC-3339 bar time, or None outside the regular session"""
    try:
        t = datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None
    m = int((t - cal.session_open(day)) // 60)
    return m if 0 <= m < (cal.close_minutes(day) - 570) else None


def sessions_from_bars(raw_bars, session_dates):
    """Alpaca's 1-minute bars -> {ISO date: [[minute, o, h, l, c, v]]} for the regular session of each date in
    `session_dates`; the bar of minute 0 is the 09:30 bar"""
    want = {d: cal._as_date(d) for d in session_dates}
    out = {d: [] for d in session_dates}
    for b in raw_bars or []:
        try:
            day = cal._as_date(datetime.fromisoformat(b["t"].replace("Z", "+00:00")).timestamp()).isoformat()
        except (KeyError, ValueError, AttributeError):
            continue
        if day not in want:
            continue
        m = minute_of(b["t"], want[day])
        if m is None:
            continue
        try:
            out[day].append([m, float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]), float(b.get("v") or 0)])
        except (KeyError, TypeError, ValueError):
            continue
    for rows in out.values():
        rows.sort()
    return {d: r for d, r in out.items() if r}


def intraday_path(root, symbol):
    return cache_path(root, "intraday", symbol + ".json")


def load_intraday(root, symbol):
    doc = read_json(intraday_path(root, symbol), {}) or {}
    return doc if isinstance(doc, dict) else {}


def fetch_intraday(client, root, symbol, daily, now, sessions=INTRADAY_SESSIONS):
    """the symbol's last `sessions` completed regular sessions of 1-minute bars, from the cache plus one fetch of the missing
    sessions -> ({date: rows}, note or None). `daily` is the dated daily bars (scorecards.dated): they name the completed
    sessions. A failed fetch returns what the cache holds, with the exact error as the note."""
    dates = [b["t"] for b in daily][-sessions:]
    cached = load_intraday(root, symbol)
    missing = [d for d in dates if d not in cached]
    note = None
    if missing and client is not None:
        try:
            start = datetime.fromtimestamp(cal.session_open(missing[0]), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            end = datetime.fromtimestamp(cal.session_close(missing[-1]) + 60, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            got = client.stock_bars([symbol], "1Min", start=start, end=end, feed="sip", adjustment="raw")
            fresh = sessions_from_bars(got.get(symbol) or [], missing)
            cached.update(fresh)
            if not fresh:
                note = f"the 1-minute read returned no regular-session bar for {len(missing)} session(s)"
        except Exception as e:                                       # noqa: BLE001
            note = f"{type(e).__name__}: {str(e)[:120]}"
    elif missing:
        note = "no Alpaca client with keys in this process"
    keep = sorted(cached)[-INTRADAY_KEEP:]
    cached = {d: cached[d] for d in keep}
    if cached:
        os.makedirs(os.path.dirname(intraday_path(root, symbol)), exist_ok=True)
        write_json_atomic(intraday_path(root, symbol), cached)
    return {d: cached[d] for d in dates if d in cached}, note


def days_for_studies(sessions, daily):
    """[{"date","prev_close","bars":[{"minute","o","h","l","c","v"}]}] for studies.gap_fill_study / orb_ib_study. The prior
    close is the previous session's daily close, unless it sits more than 2% from that session's last 1-minute close (a
    split between the two series), when the last 1-minute close stands in."""
    closes = {b["t"]: b["c"] for b in daily}
    order = [b["t"] for b in daily]
    out = []
    for i, d in enumerate(order):
        if d not in sessions or i == 0:
            continue
        prev = order[i - 1]
        pc = closes.get(prev)
        if prev in sessions and sessions[prev] and pc:
            last_min = sessions[prev][-1][4]
            if last_min and abs(pc / last_min - 1) > 0.02:
                pc = last_min
        if not pc:
            continue
        out.append({"date": d, "prev_close": pc,
                    "bars": [{"minute": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in sessions[d]]})
    return out


# ---- earnings ---------------------------------------------------------------------------------------------------------

def earnings_rows(records, bars_by_symbol, cap=12):
    """per-symbol earnings stats and the pooled moves from the crawl's records (8-K 2.02 dates) and the daily bars
    -> (rows, pooled_moves)"""
    rows, pooled = [], []
    for sym, rec in records.items():
        moves = studies.earnings_moves(rec.get("earnings_dates") or [], bars_by_symbol.get(sym) or [], cap)
        if not moves:
            continue
        pooled.extend(moves)
        st = studies.earnings_stats(moves)
        if st["state"] == "graded":
            rows.append({"symbol": sym, "n": st["n"], "mean": st["mean"], "median": st["median"], "std": st["std"],
                         "share_positive": st["share_positive"], "sharpe": st["sharpe"]})
    rows.sort(key=lambda r: (-r["n"], r["symbol"]))
    return rows, pooled


# ---- squeeze ----------------------------------------------------------------------------------------------------------

def squeeze_records(records, bars_by_symbol, short_volume, today):
    """the pane's inputs, one per name that has a short-interest row, shares outstanding and 21+ closes. si_pct_float is
    in percent over EDGAR shares outstanding (the float basis, declared). short_volume: {symbol: FNQC short ratio}."""
    out = []
    for sym, rec in records.items():
        si, so = (rec.get("si") or []), (rec.get("shares_outstanding") or {}).get("shares")
        bars = bars_by_symbol.get(sym) or []
        if not si or not so or len(bars) < 21:
            continue
        row = si[0]
        closes, vols = [b["c"] for b in bars], [b["v"] for b in bars]
        dollar = sorted(c * v for c, v in zip(closes[-20:], vols[-20:]))
        try:
            age = (today - datetime.fromisoformat(row["settlement_date"]).date()).days
        except ValueError:
            age = None
        prev = si[1]["si_shares"] if len(si) > 1 else None
        out.append({"symbol": sym, "si_pct_float": row["si_shares"] / so * 100.0, "si_shares": row["si_shares"],
                    "float_shares": so, "shares_outstanding": so, "close": closes[-1],
                    "adv20": sum(vols[-20:]) / 20.0, "median_dollar_vol": dollar[len(dollar) // 2],
                    "settlement_age_days": age, "closes": closes, "volumes": vols,
                    "si_change_pct": ((row["si_shares"] / prev - 1) * 100.0 if prev else None),
                    "short_volume_ratio": (short_volume or {}).get(sym)})
    return out


# ---- the state vector -------------------------------------------------------------------------------------------------

def fnqc_history_path(root):
    return state_path(root, FNQC_HISTORY)


def fnqc_append(root, file_date, ratios):
    """one line a FNQC file date: {"date","ratios":{symbol: ratio}} for the symbols the Map job tracks; a date already
    stored is not written again. Append-only."""
    p = fnqc_history_path(root)
    have = {r.get("date") for r in read_lines(p)}
    if file_date in have:
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"date": file_date, "ratios": ratios}) + "\n")
    return True


def read_lines(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def _fwd_p(closes_by_date, dates, i, k=21):
    if i + k >= len(dates):
        return None
    a, b = closes_by_date[dates[i]], closes_by_date[dates[i + k]]
    return math.log(b / a) if a > 0 and b > 0 else None


def state_vector_section(root, spy_daily, gex_net_b, iv30, now, history_min=126):
    """append today's raw (P, V, D, G, IV) of SPY and read the nearest-neighbour P_NN from what has accrued ->
    studies.p_nn's dict. Raw coordinates are stored; normalisation uses only the values before each row (point in time)."""
    closes = [b["c"] for b in spy_daily]
    dates = [b["t"] for b in spy_daily]
    if len(closes) < 22:
        return {"state": "insufficient_history", "history_sessions_accrued": 0, "p_nn": None,
                "reason": "SPY has fewer than 22 completed sessions"}
    today = dates[-1]
    by_day = {r["date"]: (r.get("ratios") or {}).get("SPY") for r in read_lines(fnqc_history_path(root))}
    d_series = [by_day.get(d) for d in dates[-7:]]                  # aligned to the sessions: None where no file was kept
    lagged = d_series[:-1][-5:]
    d_coord = studies.dix_coordinate(d_series) if sum(1 for v in lagged if v is not None) >= 3 else None
    raw = [studies.price_coordinate(closes), studies.vol_coordinate(closes), d_coord, gex_net_b, iv30]
    p = state_path(root, STATE_VECTORS)
    rows = read_lines(p)
    if today not in {r.get("date") for r in rows}:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"date": today, "raw": raw}) + "\n")
        rows.append({"date": today, "raw": raw})
    rows.sort(key=lambda r: r["date"])
    by_date = {b["t"]: b["c"] for b in spy_daily}
    hist = []
    for i, r in enumerate(rows):
        prior = rows[:i]
        vec = [studies.normalise(r["raw"][j], [q["raw"][j] for q in prior]) if r["raw"][j] is not None else None
               for j in range(5)]
        if r["date"] in by_date:
            k = dates.index(r["date"]) if r["date"] in dates else None
            mp = _fwd_p(by_date, dates, k) if k is not None else None
        else:
            mp = None
        hist.append({"vector": vec, "matured_p": mp, "date": r["date"]})
    cur = hist[-1]["vector"] if hist else [None] * 5
    out = studies.p_nn(cur, hist[:-1])
    out["history_sessions_accrued"] = len(rows)
    if out["state"] != "graded":
        out["reason"] = out.get("reason") or "waiting for 126 accrued sessions"
    return out
