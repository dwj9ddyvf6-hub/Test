"""NYSE session calendar + hold arithmetic. Pure functions. Semantics copied from paper-desk 1.8.2 (desk.py next_td / entry_bar /
time_exit_at / red_window / prev_td) and the tracker calendar (addons_sources_st.nyse_holidays / close_minutes); every pass cross-checks
today against Alpaca GET /v2/calendar and halts on a mismatch."""
import pandas as pd
TZ = "America/New_York"

def _easter(y):
    a = y % 19; b, c = divmod(y, 100); d, e = divmod(b, 4); f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451; mo, dy = divmod(h + l - 7 * m + 114, 31)
    return pd.Timestamp(y, mo, dy + 1)
def _thanksgiving(y): d = pd.Timestamp(y, 11, 1); return d + pd.Timedelta(days=(3 - d.weekday()) % 7 + 21)
def holidays(y):
    def obs(d): return d - pd.Timedelta(days=1) if d.weekday() == 5 else d + pd.Timedelta(days=1) if d.weekday() == 6 else d
    def nth(mo, wd, n): d = pd.Timestamp(y, mo, 1); return d + pd.Timedelta(days=(wd - d.weekday()) % 7 + 7 * (n - 1))
    def last(mo, wd): d = pd.Timestamp(y, mo + 1, 1) - pd.Timedelta(days=1); return d - pd.Timedelta(days=(d.weekday() - wd) % 7)
    H = [obs(pd.Timestamp(y, 1, 1)), nth(1, 0, 3), nth(2, 0, 3), _easter(y) - pd.Timedelta(days=2), last(5, 0), obs(pd.Timestamp(y, 7, 4)),
         nth(9, 0, 1), _thanksgiving(y), obs(pd.Timestamp(y, 12, 25)), obs(pd.Timestamp(y, 6, 19))]
    return {d.date() for d in H if d.year == y}
def ts(x): t = pd.Timestamp(x); return t.tz_convert(TZ) if t.tzinfo else t.tz_localize(TZ)
def day0(t): return ts(t).normalize()
def is_td(d): d = pd.Timestamp(d); d = (d.tz_convert(TZ) if d.tzinfo else d).date(); return d.weekday() < 5 and d not in holidays(d.year)
def close_minutes(d):
    d = pd.Timestamp(d); d = d.tz_convert(TZ).tz_localize(None) if d.tzinfo else d
    early = (d.month == 7 and d.day == 3) or (d.month == 12 and d.day == 24) or d.normalize() == _thanksgiving(d.year) + pd.Timedelta(days=1)
    return 13 * 60 if early and is_td(d) else 16 * 60
def s_open(d): return day0(d) + pd.Timedelta(hours=9, minutes=30)
def s_close(d): d = day0(d); return d + pd.Timedelta(minutes=close_minutes(d))
def next_td(d, k=1):
    n = day0(d).tz_localize(None)   # naive stepping: DST-safe (old desk AF-08)
    while True:
        n += pd.Timedelta(days=1)
        if is_td(n): k -= 1
        if k == 0: return n.tz_localize(TZ)
def prev_td(d):
    n = day0(d).tz_localize(None)
    while True:
        n -= pd.Timedelta(days=1)
        if is_td(n): return n.tz_localize(TZ)
def hour_bars(d):
    o, c = s_open(d), s_close(d); out = []; s = o
    while s < c: out.append((s, min(s + pd.Timedelta(hours=1), c))); s += pd.Timedelta(hours=1)
    return out
def entry_bar(kind, fire_bar):
    """research entry = open of the next bar after the completed fire bar -> (entry bar start, entry session day)."""
    t = ts(fire_bar)
    if kind == "1h":
        for s, e in hour_bars(t):
            if s <= t < e:
                if e < s_close(t): return e, day0(t)
                break
        n = next_td(t); return s_open(n), n
    if kind == "1d": n = next_td(t); return s_open(n), n
    last = day0(t) - pd.Timedelta(days=day0(t).weekday()) + pd.Timedelta(days=4)   # 1W bar labelled at Friday; ends on the week's last session
    while not is_td(last): last -= pd.Timedelta(days=1)
    n = next_td(last); return s_open(n), n
def time_exit_at(kind, entry_start, max_bars):
    """close of the final bar of the hold, entry bar = bar 1 (research BT.sim exit at c[n-1])."""
    if kind == "1h":
        d = day0(entry_start); k = 0
        while True:
            if is_td(d):
                for s, e in hour_bars(d):
                    if s >= entry_start:
                        k += 1
                        if k == max_bars: return e
            d += pd.Timedelta(days=1)
    if kind == "1d":
        d = day0(entry_start); return s_close(d if max_bars == 1 else next_td(d, max_bars - 1))
    w0 = day0(entry_start).tz_localize(None); wk = (w0 - pd.Timedelta(days=w0.weekday()) + pd.Timedelta(weeks=max_bars - 1)).tz_localize(TZ)
    last = wk + pd.Timedelta(days=4)
    while not is_td(last): last -= pd.Timedelta(days=1)
    return s_close(last)
def red_window(kind, fire_bar, n):
    """fear-day window: sessions D+1..D+N after the fire session (1W: after the fire week's last session)."""
    _, eday = entry_bar(kind, fire_bar); w = [eday]
    while len(w) < n: w.append(next_td(w[-1]))
    return w
