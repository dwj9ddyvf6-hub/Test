"""Shared by the Lazarus runtime harnesses (lazarus_entry, lazarus_exit): the SOURCE tree (lazarus-desk at commit
a3319569, every imported file checked against its pinned blob) and the deterministic case generators.

LAZARUS_SRC = a directory holding lazarus-desk at a3319569 (e.g. `git -C lazarus-desk worktree add <dir> a3319569`
or a `git archive` of it): its lazarus/ package runs in its own process, never imported here."""
import hashlib
import os
import random
from datetime import date, datetime, timedelta

import pandas as pd

from desk import calendar as cal
from desk.sleeves.families import lazarus as L
from desk.util import ET

COMMIT = "a3319569f5de475e3a655aae1f456f7dfe757776"
PINS = {"lazarus/__init__.py": "eecc3f525b2451db3f7383e22a145bc93ce5d173",
        "lazarus/cal.py": "462a707e66493fb0e9f6b7e3a1168e13851a0134",
        "lazarus/data.py": "1ec29ef5be01411a4afb4087a96357e135b6945b",
        "lazarus/desk.py": "60f0f5b8a62a3bc9004a1319c7b50b40f3edd3b6",
        "lazarus/gate.py": "d6c39afe1675c10f787b2a9ea8a88aa687edfa59",
        "lazarus/signals.py": "b00c68adf0c0aa1a7f4bbda1b49f30decd10d323",
        "lazarus/book.py": "81568f36f62ace175b993d9dd8cfe32936ceec5a",
        "lazarus/execution.py": "d9e58e04dd3efa4618e72d1440a769d076bb7a26",
        "lazarus/ledger.py": "825894e2de3a440edbc0ecbd80d3684e6283552c",
        "lazarus/state.py": "fc3c68a0e54549e07bc5066f82d1324082442ff8",
        "config/sleeves.json": "7097760b1682098c5e85ae7ce2519e7d6272e0ee"}
HALF_DAYS = (date(2024, 7, 3), date(2024, 11, 29), date(2024, 12, 24), date(2025, 7, 3), date(2025, 11, 28),
             date(2025, 12, 24), date(2026, 11, 27), date(2026, 12, 24))


def source_tree():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"          # never write __pycache__ into a source tree
    d = os.environ.get("LAZARUS_SRC")
    if not d or not os.path.isdir(d):
        raise SystemExit("set LAZARUS_SRC to a lazarus-desk tree at commit " + COMMIT)
    for rel, want in PINS.items():
        b = open(os.path.join(d, rel), "rb").read()
        got = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
        if got != want:
            raise SystemExit(f"{rel} in {d} is blob {got[:12]}, not the pinned {want[:12]} (commit {COMMIT[:8]})")
    return d


def et(d, hh=0, mm=0):
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET)


def rand_session(rnd, lo=date(2024, 1, 2), span=1000):
    d = lo + timedelta(days=rnd.randrange(span))
    if rnd.random() < 0.25:                               # near a half day / holiday
        d = rnd.choice(HALF_DAYS) + timedelta(days=rnd.randint(-8, 3))
    while not cal.is_trading_day(d):
        d -= timedelta(days=1)
    return d


def fire_bar(rnd, kind, d):
    """a fire bar as the producers write them: daily = the session at 09:30 ET; hourly = an RTH bar start;
    weekly = the Monday-labelled weekly bar (tracker), the week's last session (lab books) or a weekday."""
    if kind == "1h":
        close = cal.session_close(d)
        starts = [et(d, 9, 30) + timedelta(hours=k) for k in range(7)]
        starts = [s for s in starts if s.timestamp() < close]
        if cal.close_minutes(d) < 16 * 60 and rnd.random() < 0.5:
            starts.append(et(d, 13, 0))
        return str(pd.Timestamp(rnd.choice(starts)))
    if kind == "1d":
        return str(pd.Timestamp(et(d, 9, 30)))
    u = rnd.random()
    mon = d - timedelta(days=d.weekday())
    if u < 0.4:
        return str(pd.Timestamp(et(mon)))
    if u < 0.8:
        last = mon + timedelta(days=4)
        while not cal.is_trading_day(last):
            last -= timedelta(days=1)
        return last.isoformat()
    return (mon + timedelta(days=rnd.randrange(5))).isoformat()


def plan(rnd, kind):
    mb = {"1h": rnd.randint(1, 120), "1d": rnd.randint(1, 260), "1w": rnd.randint(1, 80)}[kind]
    if rnd.random() < 0.05:
        mb = None
    st = 99.0 if rnd.random() < 0.7 else round(rnd.uniform(4, 30), 1)
    return {"scheme": f"plan {mb}", "stop_pct": st, "max_bars": mb, "rest": "time", "first_target_pct": None}


def daily_bars(rnd, upto, n, px, now_bar):
    """closed daily bars (engine-store rows) for the n sessions before `upto` (+ upto's own when now_bar)."""
    days, d = [], upto - timedelta(days=1)
    while len(days) < n:
        if cal.is_trading_day(d):
            days.append(d)
        d -= timedelta(days=1)
    days = days[::-1] + ([upto] if now_bar and cal.is_trading_day(upto) else [])
    rows = []
    for x in days:
        c = round(max(0.5, px * (1 + rnd.gauss(0, 0.03))), 2)
        rows.append({"t": int(et(x, 9, 30).timestamp()), "o": c, "h": round(c * 1.01, 2), "l": round(c * 0.99, 2),
                     "c": c, "v": float(rnd.choice((rnd.randrange(1000, 40000), rnd.randrange(40000, 3_000_000))))})
        px = c
    return rows


def write_bars(eng, sym, rows):
    L.write_store(eng, sym, rows)


def rows_by_kind():
    out = {}
    for r in L.rows():
        out.setdefault(L.entry_kind(r), []).append(r)
    return out


def pick_row(rnd):
    by = rows_by_kind()
    k = rnd.choices(("1h", "1d", "1w"), weights=(2, 3, 4))[0]
    return dict(rnd.choice(by[k]))


def seed_rng(name, i):
    return random.Random(f"{name}:{i}")
