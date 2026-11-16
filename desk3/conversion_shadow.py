"""CONVERSION-SHADOW-20261115: forward shadow grader for the
Conversion Program's BLOCKED-ON-WIRING rows (armed by the desk lane,
2026-11-15, under the owner's order to turn the weekend's potential
edge into tradeable sleeves and strategies).

One instrument, ten arm kinds, driven entirely by
config/conversion_shadow_20261115.json:

  FWD_GRADE   a live stream's forward entries graded at registered
              forward horizons, excess vs QQQ (CONV-25, 26, 28;
              CONV-27 grades dispatcher entry intents as shadow
              entries, its stream's asset being unlisted at the
              broker, priced on the Kraken ENJ/USD tape).
  EXIT_PAIR   alternative exit profiles simulated as shadow arms
              beside the live profile on identical entries, paired
              deltas (CONV-29, 30, 31, 32, 33, 36).
  GATE_PAIR   a dropped entry gate reconstructed at the fire level
              from the archived lazarus fire drops, gated set vs
              gateless set on identical filters (CONV-35).
  ACTUAL_PAIR a shadow night-1 exit on each forward entry graded
              against the entry's own realized exit fill (CONV-37, 38).
  RACE        three forms of one sleeve graded side by side on
              identical forward fires (CONV-45).
  SPLIT_GRADE a FWD_GRADE whose entries split by a key computed at
              entry, each side graded separately at the decisive
              horizon (GOING-LIVE-GRADER-ARMS-20261115: CONV-61
              time-of-day, CONV-74 funding sign, CONV-101 warmup
              state, CONV-113 ATS z tercile, CONV-131 LINK basis
              tercile). FWD_GRADE itself gains a both-sides form
              (the inverted side on identical entries, borrow priced
              from the daily IB snapshot archive where it exists,
              gross with the borrow line named as accruing where it
              does not): CONV-94, CONV-99, CONV-143.
  PHASE_GRADE entries graded by hold-phase buckets, the fwd
              return decomposed into the registered spans
              (CONV-62 Aster, CONV-75 Fires live-record six).
  MEMBER_GRADE per-member grade counts inside a pooled family
              cell, the cell grade printed against a complement
              pool (CONV-76 widened Fires cell, CONV-93 absence
              cell).
  TWO_POOL    a family mean excess computed with a named subset
              included and excluded on identical fills (CONV-156).
  FORECAST_JOIN the CONV-86 (LS7) and CONV-87 (LS8) arms on the
              one nightly forecast-ledger plus bars join
              (desk3.nightly_join, NIGHTLY-JOIN-ARTIFACTS-20261116):
              the grader reads the join's desk-readable artifact
              (state/nightly_join/latest.json) and grades its
              resolved rows; no second join is built here.
  SEGMENT_GRADE stage 1 of CONV-80 (SEGMENT-CONSTRUCTION-
              20261116): held-session intraday segments
              (OPEN_DRIVE, MIDDAY, CLOSE_HOUR, OVERNIGHT) priced
              from the 1Min cache (cache/bars/<SYM>/1Min.jsonl,
              the DH3-widened cache) through the shared segment
              engine desk3/intraday_segments.py, on sessions the
              arm's Lazarus parents actually held, accruing to
              the registered 20 forward sessions. Stage 2 (the
              paired 10:30-exit / 15:00-re-entry avoidance arm)
              registers only after stage 1 passes, per the row.
  EXIT_PAIR profiles gain partial-target support (partial_pct:
              at the first target touch that fraction of the
              position realizes at the target and the remainder
              rides the same stop and horizon): CONV-150. EXIT_PAIR
              also carries the CONV-34 counterfactual arms (landed
              Lazarus profiles as base, pre-cure profiles as arms)
              and the CONV-161 per-host night-1 arms.

Semantics are the historical machinery's, copied in convention from
pass2/work/unblock2_grade.py (Book.path / Book.fwd): daily closes,
stop/target checked on closes, EXIT_COST inside every path return,
excess vs QQQ only where the benchmark has closes on both dates.
Entries count from 2026-11-16 (ET) forward only. Parents are never
modified: this module reads dispatcher journals, the ingest archive,
the bar caches and desk3.lazarus SPECS, and writes only under
state/conversion_shadow/.

Lazarus base profiles are asserted against the live SPECS at every
run; a drifted base reports SPEC_DRIFT and does not grade (the arm
grades the CURRENT live profile or none at all).

Run:  python3 -m desk3.conversion_shadow [--dry-run]
Writes state/conversion_shadow/latest.json and appends one summary
row per arm to state/conversion_shadow/ledger.jsonl (suppressed
under --dry-run). Prints the summary block either way.
"""
from __future__ import annotations

import bisect
import glob
import json
import math
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
EXIT_COST = 0.0006
BENCH = "QQQ"
DATA_END = 10 ** 6

# ENJ-FEED-CONV27-20261115: ENJUSDT mapped to None while no ENJ
# tape was served anywhere the grader reads; the warm layer now
# persists the Kraken spot tape as ENJ/USD|4Hour (desk3/warm.py
# KRAKEN_SPOT_FETCHES), so ENJ prices on that tape like ADA/LINK
# price on theirs. With the tape absent the series is still None
# (fail-closed: unpriceable, never fabricated).
SYMMAP = {"ADAUSDT": "ADA/USD", "LINKUSDT": "LINK/USD",
          "ENJUSDT": "ENJ/USD", "ADA/USD": "ADA/USD",
          "LINK/USD": "LINK/USD", "ENJ/USD": "ENJ/USD"}
CRYPTO_SYMBOLS = {"ADA/USD", "LINK/USD", "ENJ/USD", "BTC/USD",
                  "ETH/USD", "SOL/USD", "ADAUSDT", "LINKUSDT",
                  "ENJUSDT"}


# ---------------------------------------------------------------- stats
def stats_bp(vals):
    """vals are decimal returns; returns {n, mean_bp, t}."""
    if not vals:
        return {"n": 0, "mean_bp": None, "t": None}
    m = sum(vals) / len(vals)
    t = None
    if len(vals) > 1:
        var = sum((x - m) ** 2 for x in vals) / (len(vals) - 1)
        sd = math.sqrt(var)
        t = m / (sd / math.sqrt(len(vals))) if sd > 0 else None
    return {"n": len(vals), "mean_bp": round(10000 * m, 1),
            "t": round(t, 2) if t is not None else None}


# ---------------------------------------------------------------- bars
class SeriesBook:
    """Daily closes: equities from cache/bars/<SYM>/1Day.jsonl overlaid
    by the live warm cache (state/warm_bars.json, later dates win);
    crypto from the warm cache's served 4Hour tape resampled to
    UTC-date closes (the tape the live sleeves trade after
    F4-CRYPTO-BARKEY-20261114)."""

    def __init__(self, root):
        self.root = root
        self._warm = None
        self._cache = {}

    def _warm_bars(self):
        if self._warm is None:
            try:
                doc = json.load(open(os.path.join(
                    self.root, "state", "warm_bars.json")))
                self._warm = doc.get("bars") or {}
            except Exception:
                self._warm = {}
        return self._warm

    def _overlay(self, series, rows):
        for r in rows or []:
            t = str(r.get("t") or "")
            if len(t) >= 10 and r.get("c") is not None:
                series[t[:10]] = float(r["c"])
        return series

    def daily(self, symbol):
        sym = SYMMAP.get(symbol, symbol)
        if sym is None:
            return None
        if sym in self._cache:
            return self._cache[sym]
        series = {}
        if sym in CRYPTO_SYMBOLS:
            warm = self._warm_bars()
            by_date = {}
            for key in (f"{sym}|4Hour", f"{sym}|1Hour"):
                for r in warm.get(key) or []:
                    t = str(r.get("t") or "")
                    if len(t) >= 10 and r.get("c") is not None:
                        by_date[t[:10]] = (t, float(r["c"]))
            for d, (_t, c) in by_date.items():
                series[d] = c
        else:
            path = os.path.join(self.root, "cache", "bars", sym,
                                "1Day.jsonl")
            if os.path.exists(path):
                rows = []
                with open(path) as fh:
                    for line in fh:
                        line = line.strip()
                        if line:
                            rows.append(json.loads(line))
                self._overlay(series, rows)
            warm = self._warm_bars()
            for key in (f"{sym}|1Day", sym):
                if warm.get(key):
                    self._overlay(series, warm[key])
                    break
        if not series:
            self._cache[sym] = None
            return None
        dates = sorted(series)
        out = (dates, series)
        self._cache[sym] = out
        return out

    def bench(self):
        return self.daily(BENCH)


class MinuteBook:
    """1Min rows from the ONE offline cache the weekend program
    widened (cache/bars/<SYM>/1Min.jsonl, DH3: 29 Focus names,
    53 sessions), grouped by ET session date. Segment pricing
    delegates to the shared engine (desk3/intraday_segments.py)
    so the grader and the live segment sleeves price segments
    identically. A symbol or session absent from the cache
    prices None (fail-closed, never fabricated)."""

    def __init__(self, root):
        self.root = root
        self._days = {}

    def _load(self, symbol):
        if symbol in self._days:
            return
        days = {}
        path = os.path.join(self.root, "cache", "bars", symbol,
                            "1Min.jsonl")
        if os.path.exists(path):
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    d = _et_date(r.get("t"))
                    if d is not None:
                        days.setdefault(d, []).append(r)
        self._days[symbol] = days

    def marks(self, symbol, date, prev_close=None):
        from desk3.intraday_segments import segment_marks
        self._load(symbol)
        rows = self._days[symbol].get(date) or []
        if not rows:
            return None
        return segment_marks(rows, date, prev_close)


def idx_of(series, date):
    if series is None:
        return None
    dates, _closes = series
    i = bisect.bisect_left(dates, date)
    return i if i < len(dates) else None


# ------------------------------------------------------- path machinery
def path_ret(series, bench, i, price, dir_, stop, target, horizon,
             min_age=0, partial_pct=None):
    """unblock2 Book.path semantics. Returns dict with ret (decimal,
    dir-adjusted, net of EXIT_COST), kind, resolved, exit_date; or
    None when the entry cannot be priced at all. horizon None means
    the data-end form (DROP_horizon): the return is marked at the
    latest close and counts resolved once the entry is at least
    min_age sessions old, the historical data-end convention.
    partial_pct (GOING-LIVE-GRADER-ARMS-20261115, CONV-150): when
    set alongside target, the first target touch realizes that
    fraction of the position at the target (net of EXIT_COST on
    that fraction) and the remainder rides the same stop and
    horizon to its own exit; the path return is the weighted sum.
    With partial_pct None the semantics are exactly the original."""
    if series is None or i is None or not price or price <= 0:
        return None
    dates, closes = series
    last = min(i + (horizon if horizon is not None else DATA_END),
               len(dates) - 1)
    if last <= i:
        return None
    partial_ret = None
    for k in range(i + 1, last + 1):
        r = dir_ * (closes[dates[k]] / price - 1)
        if stop is not None and r <= -stop:
            leg = -stop - EXIT_COST
            if partial_ret is None:
                return {"ret": leg, "kind": "stop", "resolved": True,
                        "exit_date": dates[k], "exit_idx": k}
            return {"ret": partial_pct * partial_ret
                    + (1 - partial_pct) * leg,
                    "kind": "partial_target_then_stop",
                    "resolved": True, "exit_date": dates[k],
                    "exit_idx": k}
        if target is not None and r >= target:
            if partial_pct is None:
                return {"ret": target - EXIT_COST, "kind": "target",
                        "resolved": True, "exit_date": dates[k],
                        "exit_idx": k}
            if partial_ret is None:
                partial_ret = target - EXIT_COST
    ret = dir_ * (closes[dates[last]] / price - 1) - EXIT_COST
    if horizon is not None:
        resolved = (i + horizon) <= (len(dates) - 1)
    else:
        resolved = (len(dates) - 1 - i) >= max(1, min_age)
    if partial_ret is not None:
        return {"ret": partial_pct * partial_ret
                + (1 - partial_pct) * ret,
                "kind": "partial_target_then_horizon",
                "resolved": resolved, "exit_date": dates[last],
                "exit_idx": last}
    return {"ret": ret, "kind": "horizon", "resolved": resolved,
            "exit_date": dates[last], "exit_idx": last}


def fwd_ret(series, bench, i, price, dir_, k):
    """unblock2 Book.fwd semantics: (raw, excess_or_None) at +k bars
    of the symbol's own series, or None when unpriceable."""
    if series is None or i is None or not price or price <= 0:
        return None
    dates, closes = series
    if i + k >= len(dates):
        return None
    raw = dir_ * (closes[dates[i + k]] / price - 1)
    exc = None
    if bench is not None:
        bd, bc = bench
        if dates[i] in bc and dates[i + k] in bc:
            exc = raw - (bc[dates[i + k]] / bc[dates[i]] - 1)
    return (raw, exc)


def bench_ret(bench, d0, d1):
    if bench is None:
        return None
    _bd, bc = bench
    if d0 in bc and d1 in bc:
        return bc[d1] / bc[d0] - 1
    return None


# ---------------------------------------------------------------- fills
def _et_date(ts):
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ET).date().isoformat()


def _utc_date(ts):
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


def load_fills(root, start_date):
    """Entry and exit fills from the dispatcher journal generations,
    oldest first, deduped by intent_id, from start_date (ET) forward.
    Entry date is the ET date for equity sleeves and the UTC date for
    crypto symbols (their tapes are UTC), matching each arm's
    registered calendar via entry['date_et'] / entry['date_utc']."""
    gens = [os.path.join(root, "state", f"dispatcher.jsonl.{n}")
            for n in (4, 3, 2, 1)]
    gens.append(os.path.join(root, "state", "dispatcher.jsonl"))
    seen = set()
    entries, exits = [], []
    for path in gens:
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("event") != "fill":
                    continue
                iid = r.get("intent_id")
                if iid is None or iid in seen:
                    continue
                seen.add(iid)
                ts = r.get("ts") or ""
                d_et = _et_date(ts)
                if d_et is None or d_et < start_date:
                    continue
                pi = r.get("position_intent") or ""
                rec = {"sleeve": r.get("sleeve"),
                       "symbol": r.get("symbol"),
                       "price": float(r.get("price") or 0),
                       "qty": abs(float(r.get("qty") or 0)),
                       "ts": ts, "intent_id": iid,
                       "date_et": d_et, "date_utc": _utc_date(ts)}
                if pi in ("buy_to_open", "sell_to_open"):
                    rec["dir"] = 1 if pi == "buy_to_open" else -1
                    entries.append(rec)
                elif pi in ("sell_to_close", "buy_to_close"):
                    exits.append(rec)
    entries.sort(key=lambda e: e["ts"])
    exits.sort(key=lambda e: e["ts"])
    return entries, exits


def load_intent_entries(root, start_date, sleeves):
    """Shadow entries for arms whose stream cannot fill at the
    broker (ENJ-FEED-CONV27-20261115). ENJ/USD is unlisted at the
    broker (42210000 asset-not-found), so the ENJ sleeves' entries
    exist only as dispatcher entry intents that fail closed at the
    broker seam by name; there is no fill for load_fills to see,
    ever. The register's named step for CONV-27 arms the stream as
    shadow on the live Kraken ENJ/USD tape and grades its entries:
    an entry counts when the dispatcher record carries the intent's
    terminal broker verdict (broker_rejected_terminal, kind
    "entry") and the sleeve's own journal carries the intent's
    timestamp. Price is None at load: grade_fwd prices a shadow
    entry at its entry date's close on the arm's own series, the
    tape the sleeve trades. Entries are deduped by intent_id and
    filtered to start_date (ET) forward, the same accrual window
    as fills.

    INTENT-RECORDED-UNLISTED-20261116: since that cure the door
    records these entries locally as intent_recorded rows and
    never submits them, so the terminal evidence is the union of
    the historical broker_rejected_terminal rows and the
    intent_recorded rows; the population an arm grades (every
    entry intent of its sleeves that reached the door's terminal
    verdict) is unchanged.

    ENJ-PAPER-20261116: the ENJ class now fills in the free_kraken
    paper form at the door, so an ENJ entry's terminal evidence is
    its kraken_paper fill row (event "fill", venue "kraken_paper",
    an opening position_intent standing in for kind "entry"). The
    union grows to include those rows; the graded population (every
    entry intent of the arm's sleeves that reached a terminal
    verdict at the door) is unchanged, and the entry still prices
    at its entry date's close on the arm's own Kraken tape, exactly
    as the register's named step specifies."""
    gens = [os.path.join(root, "state", f"dispatcher.jsonl.{n}")
            for n in (4, 3, 2, 1)]
    gens.append(os.path.join(root, "state", "dispatcher.jsonl"))
    terminal = {}
    for path in gens:
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("event") in ("broker_rejected_terminal",
                                      "intent_recorded"):
                    if r.get("kind") != "entry":
                        continue
                elif r.get("event") == "fill" \
                        and r.get("venue") == "kraken_paper":
                    # ENJ-PAPER-20261116: a paper fill is the ENJ
                    # class's terminal verdict; its opening
                    # position_intent stands in for kind "entry".
                    if r.get("position_intent") not in (
                            "buy_to_open", "sell_to_open"):
                        continue
                else:
                    continue
                iid = r.get("intent_id")
                if iid is None or iid in terminal:
                    continue
                if r.get("sleeve") not in sleeves:
                    continue
                side = r.get("side")
                if side not in ("buy", "sell"):
                    continue
                terminal[iid] = {
                    "sleeve": r.get("sleeve"),
                    "symbol": r.get("symbol"),
                    "dir": 1 if side == "buy" else -1,
                    "qty": abs(float(r.get("qty") or 0))}
    entries = []
    seen = set()
    for sleeve in sorted(sleeves):
        jpath = os.path.join(root, "state", sleeve, "journal.jsonl")
        if not os.path.exists(jpath):
            continue
        with open(jpath) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("event") != "intent":
                    continue
                iid = r.get("intent_id")
                if iid is None or iid in seen or iid not in terminal:
                    continue
                seen.add(iid)
                ts = r.get("ts") or ""
                d_et = _et_date(ts)
                if d_et is None or d_et < start_date:
                    continue
                rec = dict(terminal[iid])
                rec.update({"price": None, "ts": ts,
                            "intent_id": iid, "date_et": d_et,
                            "date_utc": _utc_date(ts)})
                entries.append(rec)
    entries.sort(key=lambda e: e["ts"])
    return entries


def match_actuals(entries, exits):
    """FIFO-match exit fills to entry fills per (sleeve, symbol).
    Returns {intent_id: realized decimal return} for entries whose
    full quantity has closed; partial closes stay unresolved, the
    conservative paired convention."""
    open_q = {}
    for e in entries:
        open_q.setdefault((e["sleeve"], e["symbol"]), []).append(
            {"entry": e, "remaining": e["qty"], "exit_px_qty": 0.0,
             "exit_qty": 0.0})
    realized = {}
    for x in exits:
        lots = open_q.get((x["sleeve"], x["symbol"])) or []
        q = x["qty"]
        for lot in lots:
            if q <= 0:
                break
            if x["ts"] <= lot["entry"]["ts"]:
                continue
            take = min(q, lot["remaining"])
            lot["remaining"] -= take
            lot["exit_px_qty"] += take * x["price"]
            lot["exit_qty"] += take
            q -= take
            if lot["remaining"] <= 1e-9 and lot["exit_qty"] > 0:
                avg_exit = lot["exit_px_qty"] / lot["exit_qty"]
                realized[lot["entry"]["intent_id"]] = (
                    lot["entry"]["dir"]
                    * (avg_exit / lot["entry"]["price"] - 1)
                    - EXIT_COST)
    return realized


# ---------------------------------------------------------------- fires
def load_fires(root, start_date):
    """Lazarus fire drops: the dated ingest archive from start_date
    forward plus the current drop, deduped by (sleeve_id, symbol,
    fired_at)."""
    drops = []
    arch = os.path.join(root, "state", "ingest", "archive")
    if os.path.isdir(arch):
        for day in sorted(os.listdir(arch)):
            if day >= start_date:
                p = os.path.join(arch, day, "lazarus_fires.json")
                if os.path.exists(p):
                    drops.append(p)
    cur = os.path.join(root, "state", "ingest", "lazarus_fires.json")
    if os.path.exists(cur):
        drops.append(cur)
    seen = set()
    fires = []
    for path in drops:
        try:
            doc = json.load(open(path))
        except Exception:
            continue
        for f in doc.get("fires") or []:
            if not isinstance(f, dict) or not f.get("symbol"):
                continue
            ft = f.get("fired_at") or f.get("ts") or f.get("fire_date") \
                or f.get("signal_date")
            if ft is None:
                continue
            key = (f.get("sleeve_id"), f["symbol"], str(ft))
            if key in seen:
                continue
            seen.add(key)
            d = _et_date(ft) if "T" in str(ft) else str(ft)[:10]
            if d is None or d < start_date:
                continue
            px = f.get("price")
            try:
                px = float(px) if px else None
            except Exception:
                px = None
            if not px or px <= 0:
                continue
            qred = f.get("qqq_red", f.get("qqq_down"))
            fires.append({
                "sleeve_id": f.get("sleeve_id"), "symbol": f["symbol"],
                "date": d, "price": px, "dir": 1,
                "side": str(f.get("side", "buy")).lower(),
                "family": str(f.get("family") or f.get("color")
                              or "").lower(),
                "tf": str(f.get("tf") or f.get("timeframe") or ""),
                "cap_tier": str(f.get("cap_tier") or "").lower(),
                "signal_tier": str(f.get("signal_tier")
                                   or f.get("tier") or "").upper(),
                "ml_pick": f.get("ml_pick"), "qqq_red": qred,
                "fired_at": str(ft)})
    fires.sort(key=lambda f: f["fired_at"])
    return fires


def gate_sets(fires, sid, spec, bench):
    """Apply sleeve sid's recorded non-gate filters (the engine's own
    rules: enforced only when the fire carries the field) and split
    the survivors into the gated set (qqq_down gate applied) and the
    gateless set. Returns (gated_entries, gateless_entries), each a
    list of {symbol, date, price, dir} deduped by (symbol, date)."""
    gated, gateless = [], []
    seen_g, seen_x = set(), set()
    bd, bc = bench if bench else ([], {})
    for f in fires:
        if f["sleeve_id"] and f["sleeve_id"] != sid:
            continue
        if f["side"] not in ("buy", "long"):
            continue
        if spec.get("family") and f["family"] \
                and spec["family"] not in f["family"]:
            continue
        if spec.get("tf") and f.get("tf") \
                and spec["tf"] != f["tf"]:
            continue
        if spec.get("signal_tier") and f["signal_tier"] \
                and f["signal_tier"] != spec["signal_tier"]:
            continue
        allowed = spec.get("cap_tiers") or (
            (spec["cap_tier"],) if spec.get("cap_tier") else ())
        if f["cap_tier"] and allowed and f["cap_tier"] not in allowed:
            continue
        if spec.get("ml_pick") and f["ml_pick"] is False:
            continue
        if spec.get("max_price") is not None \
                and f["price"] >= spec["max_price"]:
            continue
        key = (f["symbol"], f["date"])
        ent = {"symbol": f["symbol"], "date": f["date"],
               "price": f["price"], "dir": 1}
        if key not in seen_x:
            seen_x.add(key)
            gateless.append(ent)
        qred = f["qqq_red"]
        if qred is None and bench is not None:
            i = idx_of(bench, f["date"])
            if i is not None and i >= 1:
                qred = bc[bd[i]] < bc[bd[i - 1]]
        if qred is True and key not in seen_g:
            seen_g.add(key)
            gated.append(ent)
    return gated, gateless


# ------------------------------------------------------------- borrow
def load_borrow(root):
    """Daily IB snapshot archive for inverted-side borrow pricing:
    state/ib_borrow_archive.jsonl rows {date, symbol,
    fee_pct_per_year}. The archive accrues from 2026-11-16; where
    it does not exist yet the inverted side prints gross with the
    borrow line named as accruing, exactly as the both-sides rows
    register. Returns {symbol: [(date, fee_pct_per_year)]}."""
    path = os.path.join(root, "state", "ib_borrow_archive.jsonl")
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as fh:
        for line in fh:
            try:
                r = json.loads(line)
                fee = float(r["fee_pct_per_year"])
            except Exception:
                continue
            out.setdefault(r.get("symbol"), []).append(
                (str(r.get("date"))[:10], fee))
    for v in out.values():
        v.sort()
    return out


def borrow_fee(borrow, symbol, date):
    """The archive fee in force on date (latest snapshot on or
    before it), as a decimal per year, or None when the archive
    carries no snapshot for the symbol by then."""
    rows = borrow.get(symbol) or []
    fee = None
    for d, f in rows:
        if d <= date:
            fee = f
        else:
            break
    return fee / 100.0 if fee is not None else None


# ------------------------------------------------------------- profiles
def lazarus_base(sid):
    from desk3.lazarus import SPECS
    s = SPECS[sid]
    return {"stop_pct": s.get("stop_pct"),
            "target_pct": s.get("target_pct"),
            "horizon": s.get("horizon_sessions")}


def base_profile(arm_row):
    src = arm_row.get("base_source") or ""
    if src.startswith("lazarus:"):
        return lazarus_base(src.split(":", 1)[1])
    return arm_row.get("base")


def spec_drift(arm_row):
    src = arm_row.get("base_source") or ""
    if not src.startswith("lazarus:"):
        return False
    live = lazarus_base(src.split(":", 1)[1])
    reg = arm_row.get("base") or {}
    return any(live[k] != reg.get(k)
               for k in ("stop_pct", "target_pct", "horizon"))


# -------------------------------------------------------------- grading
def _entry_series(book, arm_row, entry):
    cal = arm_row.get("calendar", "et")
    if cal == "mixed":
        # Family pools spanning equity and crypto parents: crypto
        # entries price on their UTC tape dates, equity entries on
        # ET dates, the same per-stream convention the single-stream
        # arms apply uniformly.
        cal = "utc" if SYMMAP.get(entry["symbol"],
                                  entry["symbol"]) in CRYPTO_SYMBOLS \
            else "et"
    date = entry["date_utc"] if cal == "utc" else entry["date_et"]
    series = book.daily(entry["symbol"])
    return series, date, idx_of(series, date)


def grade_fwd(book, bench, arm_row, entries, intent_entries=None):
    pool = [e for e in entries if e["sleeve"] in arm_row["parents"]]
    if arm_row.get("entry_source") == "intents":
        # ENJ-FEED-CONV27-20261115: shadow entries from the
        # dispatcher intent record (load_intent_entries), pooled
        # beside any fills the parents ever produce.
        pool = pool + [e for e in (intent_entries or [])
                       if e["sleeve"] in arm_row["parents"]]
        pool.sort(key=lambda e: e["ts"])
    horizons = arm_row["horizons"]
    per_h = {h: [] for h in horizons}
    exc_h = {h: [] for h in horizons}
    both = bool(arm_row.get("both_sides"))
    inv_h = {h: [] for h in horizons}
    inv_exc_h = {h: [] for h in horizons}
    dec_dates = set()
    borrow = load_borrow(book.root) if both else {}
    for e in pool:
        series, date, i = _entry_series(book, arm_row, e)
        if i is None:
            continue
        price = e["price"]
        if not price:
            # Shadow intent entry (no fill exists): price at the
            # entry date's close on the arm's own series.
            if series is None:
                continue
            price = series[1].get(series[0][i])
            if not price:
                continue
        for h in horizons:
            f = fwd_ret(series, bench, i, price, e["dir"], h)
            if f is not None:
                per_h[h].append(f[0])
                if f[1] is not None:
                    exc_h[h].append(f[1])
                    if h in arm_row["decisive_horizons"]:
                        dec_dates.add(date)
                if both:
                    inv_raw = -f[0]
                    fee = borrow_fee(borrow, e["symbol"], date)
                    if fee is not None:
                        inv_raw -= fee / 252.0 * h
                    inv_h[h].append(inv_raw)
                    if f[1] is not None:
                        inv_exc_h[h].append(
                            inv_raw - (f[0] - f[1]))
    res = {"entries_seen": len(pool),
           "horizons": {str(h): {"raw": stats_bp(per_h[h]),
                                 "excess": stats_bp(exc_h[h])}
                        for h in horizons}}
    if both:
        res["inverted_horizons"] = {
            str(h): {"raw": stats_bp(inv_h[h]),
                     "excess": stats_bp(inv_exc_h[h])}
            for h in horizons}
        res["borrow"] = (
            "priced from the daily IB snapshot archive "
            "(state/ib_borrow_archive.jsonl)"
            if borrow else
            "accruing: the daily IB snapshot archive carries no "
            "history yet, so the inverted side is printed gross "
            "with the borrow line named as accruing")
        if arm_row.get("print_distinct_dates"):
            res["distinct_decisive_dates"] = len(dec_dates)
    dec = arm_row["decisive_horizons"]
    n_dec = min(len(exc_h[h]) for h in dec) if dec else 0
    res["resolved_decisive"] = n_dec
    if n_dec >= arm_row["grade_n"]:
        means = [stats_bp(exc_h[h])["mean_bp"] for h in dec]
        if both:
            inv_means = [stats_bp(inv_exc_h[h])["mean_bp"]
                         for h in dec]
            rule = arm_row.get("both_sides_positive",
                               "base_negative_and_inverted_positive")
            if rule == "inverted_positive":
                pos = all(m is not None and m > 0 for m in inv_means)
            else:
                pos = (all(m is not None and m < 0 for m in means)
                       and all(m is not None and m > 0
                               for m in inv_means))
            res["state"] = ("GRADED_POSITIVE" if pos
                            else "GRADED_NEGATIVE")
        else:
            res["state"] = ("GRADED_POSITIVE"
                            if all(m is not None and m > 0
                                   for m in means)
                            else "GRADED_NEGATIVE")
    else:
        res["state"] = "ACCRUING"
    folded = arm_row.get("folded_exit_pair")
    if folded:
        res["folded_exit_pair"] = grade_exit_pair(
            book, bench, dict(arm_row, base=folded["base"],
                              arms=[dict(folded["arm"],
                                         name=folded["arm_name"])],
                              grade_n=arm_row["grade_n"]), pool)
    return res


def _exit_pair_counts(book, bench, arm_row, pool, base, arm_profiles):
    out = {}
    for ap in arm_profiles:
        pairs = []
        base_rets, arm_rets = [], []
        for e in pool:
            series, date, i = _entry_series(book, arm_row, e)
            if i is None:
                continue
            b = path_ret(series, bench, i, e["price"], e["dir"],
                         base["stop_pct"], base["target_pct"],
                         base["horizon"],
                         partial_pct=base.get("partial_pct"))
            a = path_ret(series, bench, i, e["price"], e["dir"],
                         ap["stop_pct"], ap["target_pct"],
                         ap["horizon"],
                         min_age=ap.get("min_age_sessions", 0),
                         partial_pct=ap.get("partial_pct"))
            if b and a and b["resolved"] and a["resolved"]:
                pairs.append(a["ret"] - b["ret"])
                base_rets.append(b["ret"])
                arm_rets.append(a["ret"])
        st = stats_bp(pairs)
        out[ap["name"]] = {
            "paired_n": len(pairs), "paired_delta": st,
            "base": stats_bp(base_rets), "arm": stats_bp(arm_rets),
            "state": ("GRADED_POSITIVE"
                      if len(pairs) >= arm_row["grade_n"]
                      and st["mean_bp"] is not None
                      and st["mean_bp"] > 0 else
                      "GRADED_NEGATIVE"
                      if len(pairs) >= arm_row["grade_n"] else
                      "ACCRUING")}
    return out


def grade_exit_pair(book, bench, arm_row, entries):
    pool = [e for e in entries if e["sleeve"] in arm_row["parents"]]
    base = base_profile(arm_row)
    res = {"entries_seen": len(pool), "base": base,
           "arms": _exit_pair_counts(book, bench, arm_row, pool, base,
                                     arm_row["arms"])}
    states = [a["state"] for a in res["arms"].values()]
    res["state"] = ("GRADED" if states and all(
        s != "ACCRUING" for s in states) else "ACCRUING")
    return res


def grade_gate_pair(book, bench, arm_row, fires):
    from desk3.lazarus import SPECS
    res = {"sleeves": {}}
    all_graded = True
    for sid in arm_row["parents"]:
        spec = SPECS[sid]
        base = {"stop_pct": spec.get("stop_pct"),
                "target_pct": spec.get("target_pct"),
                "horizon": spec.get("horizon_sessions")}
        gated, gateless = gate_sets(fires, sid, spec, bench)

        def _mean_path(ents):
            vals, f5 = [], []
            for e in ents:
                series = book.daily(e["symbol"])
                i = idx_of(series, e["date"])
                p = path_ret(series, bench, i, e["price"], e["dir"],
                             base["stop_pct"], base["target_pct"],
                             base["horizon"])
                if p and p["resolved"]:
                    vals.append(p["ret"])
                    f = fwd_ret(series, bench, i, e["price"],
                                e["dir"], 5)
                    if f is not None and f[1] is not None:
                        f5.append(f[1])
            return vals, f5

        window = gateless[:arm_row["grade_n"]]
        window_end = window[-1]["date"] if window else None
        gated_window = [e for e in gated
                        if window_end and e["date"] <= window_end]
        gx, gf5 = _mean_path(gated_window)
        xx, xf5 = _mean_path(gateless)
        wx, _wf5 = _mean_path(window)
        delta = None
        if wx and gx:
            delta = (sum(wx) / len(wx)) - (sum(gx) / len(gx))
        state = "ACCRUING"
        if len(wx) >= arm_row["grade_n"] and delta is not None:
            state = ("GRADED_POSITIVE" if delta > 0
                     else "GRADED_NEGATIVE")
        else:
            all_graded = False
        res["sleeves"][sid] = {
            "gated_fires": len(gated), "gateless_fires": len(gateless),
            "gated_fires_in_window": len(gated_window),
            "gated_path_window": stats_bp(gx),
            "gateless_path": stats_bp(xx),
            "gated_fwd5_excess": stats_bp(gf5),
            "gateless_fwd5_excess": stats_bp(xf5),
            "window_gateless_path": stats_bp(wx),
            "paired_delta_bp": (round(10000 * delta, 1)
                                if delta is not None else None),
            "state": state}
    res["state"] = "GRADED" if all_graded else "ACCRUING"
    return res


def grade_actual_pair(book, bench, arm_row, entries, exits):
    pool = [e for e in entries if e["sleeve"] in arm_row["parents"]]
    realized = match_actuals(pool, exits)
    n1 = arm_row["night1"]
    pairs = []
    sessions = set()
    for e in pool:
        if e["intent_id"] not in realized:
            continue
        series, date, i = _entry_series(book, arm_row, e)
        p = path_ret(series, bench, i, e["price"], e["dir"],
                     n1["stop_pct"], n1["target_pct"], n1["horizon"])
        if p and p["resolved"]:
            pairs.append(p["ret"] - realized[e["intent_id"]])
            sessions.add(date)
    st = stats_bp(pairs)
    unit = arm_row["grade_unit"]
    count = len(sessions) if "sessions" in unit else len(pairs)
    res = {"entries_seen": len(pool), "paired_n": len(pairs),
           "paired_sessions": len(sessions),
           "paired_delta": st,
           "state": ("GRADED_POSITIVE"
                     if count >= arm_row["grade_n"]
                     and st["mean_bp"] is not None
                     and st["mean_bp"] > 0 else
                     "GRADED_NEGATIVE"
                     if count >= arm_row["grade_n"] else "ACCRUING")}
    return res


def grade_race(book, bench, arm_row, entries):
    pool = [e for e in entries if e["sleeve"] in arm_row["parents"]]
    base = base_profile(arm_row)
    forms = {f: [] for f in arm_row["forms"]}
    n_all = 0
    for e in pool:
        series, date, i = _entry_series(book, arm_row, e)
        if i is None:
            continue
        b = path_ret(series, bench, i, e["price"], e["dir"],
                     base["stop_pct"], base["target_pct"],
                     base["horizon"])
        f5 = fwd_ret(series, bench, i, e["price"], e["dir"], 5)
        if not b or not b["resolved"] or f5 is None or f5[1] is None:
            continue
        br = bench_ret(bench, date, b["exit_date"])
        if br is None:
            continue
        n_all += 1
        forms["BASE"].append(b["ret"] - br)
        forms["FWD5_LONG"].append(f5[1])
        forms["FWD5_INV"].append(-f5[1])
    res = {"entries_seen": len(pool), "resolved_all_forms": n_all,
           "forms": {f: stats_bp(v) for f, v in forms.items()}}
    if n_all >= arm_row["grade_n"]:
        means = {f: (stats_bp(v)["mean_bp"] or float("-inf"))
                 for f, v in forms.items()}
        winner = max(means, key=means.get)
        res["winner"] = winner
        res["state"] = ("GRADED_WINNER_" + winner if winner != "BASE"
                        else "GRADED_NO_FORM_BEATS_BASE")
    else:
        res["state"] = "ACCRUING"
    return res


# ------------------------------------------------- split-grade keys
def _quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def _tercile_side(value, cuts):
    if value is None or cuts is None:
        return None
    lo, hi = cuts
    if value <= lo:
        return "T1_LOW"
    if value <= hi:
        return "T2_MID"
    return "T3_HIGH"


class SplitContext:
    """Entry-time split keys for SPLIT_GRADE arms, loaded lazily
    per key family from the desk's own persisted records. A key
    that cannot be computed for an entry leaves the entry
    unstamped (excluded from every side, counted as unstamped);
    nothing is fabricated."""

    def __init__(self, root):
        self.root = root
        self._funding = None
        self._ats = {}
        self._basis = {}

    def funding_sign(self, entry):
        if self._funding is None:
            self._funding = {}
            path = os.path.join(self.root, "state",
                                "okx_funding_history.json")
            try:
                doc = json.load(open(path))
                for sym, rows in (doc.get("history") or {}).items():
                    self._funding[sym] = sorted(
                        (int(r["ts_ms"]), float(r["rate"]))
                        for r in rows)
            except Exception:
                pass
        sym = SYMMAP.get(entry["symbol"], entry["symbol"])
        key = sym.split("/")[0] + "USDT" if "/" in sym else sym
        rows = self._funding.get(key) or []
        if not rows:
            return None
        try:
            ts_ms = int(datetime.fromisoformat(
                str(entry["ts"]).replace("Z", "+00:00")
            ).timestamp() * 1000)
        except Exception:
            return None
        rate = None
        for t, r in rows:
            if t <= ts_ms:
                rate = r
            else:
                break
        if rate is None:
            return None
        return "NONNEG" if rate >= 0 else "NEG"

    def _ats_series(self, arm_row):
        path = arm_row.get("series_path") or ""
        if path in self._ats:
            return self._ats[path]
        out = {"z": {}, "cuts": None}
        try:
            doc = json.load(open(path))
        except Exception:
            self._ats[path] = out
            return out
        pooled = []
        for sym, cell in (doc.get("per_symbol_series")
                          or {}).items():
            weeks = cell.get("weeks") or []
            zs = []
            for j, w in enumerate(weeks):
                prior = [float(x["ats_share_qty"])
                         for x in weeks[max(0, j - 26):j]]
                if len(prior) < 7:
                    zs.append(None)
                    continue
                mean = sum(prior) / len(prior)
                var = sum((x - mean) ** 2 for x in prior) \
                    / len(prior)
                sd = math.sqrt(var)
                z = None if sd <= 0 else (
                    float(w["ats_share_qty"]) - mean) / sd
                zs.append(z)
                if z is not None:
                    pooled.append(z)
            out["z"][sym] = [(str(w["week_start"]), z)
                             for w, z in zip(weeks, zs)]
        pooled.sort()
        if len(pooled) >= 3:
            out["cuts"] = (_quantile(pooled, 1 / 3),
                           _quantile(pooled, 2 / 3))
        self._ats[path] = out
        return out

    def ats_z_tercile(self, arm_row, entry, date):
        ser = self._ats_series(arm_row)
        rows = ser["z"].get(entry["symbol"]) or []
        z = None
        for wk, zv in rows:
            if wk <= date:
                z = zv
            else:
                break
        return _tercile_side(z, ser["cuts"])

    def _basis_series(self, arm_row):
        path = arm_row.get("series_path") or ""
        if path in self._basis:
            return self._basis[path]
        out = {"rows": [], "cuts": None}
        try:
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        r = json.loads(line)
                        out["rows"].append(
                            (str(r["date_utc"])[:10],
                             float(r["basis_bps"])))
        except Exception:
            pass
        out["rows"].sort()
        vals = sorted(v for _d, v in out["rows"])
        if len(vals) >= 3:
            out["cuts"] = (_quantile(vals, 1 / 3),
                           _quantile(vals, 2 / 3))
        self._basis[path] = out
        return out

    def link_basis_tercile(self, arm_row, entry, date):
        ser = self._basis_series(arm_row)
        val = None
        for d, v in ser["rows"]:
            if d <= date:
                val = v
            else:
                break
        return _tercile_side(val, ser["cuts"])

    def key(self, arm_row, entry, date):
        kind = arm_row.get("split_key")
        if kind == "tod_ampm":
            try:
                dt = datetime.fromisoformat(
                    str(entry["ts"]).replace("Z", "+00:00"))
            except Exception:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return "AM" if dt.astimezone(ET).hour < 12 else "PM"
        if kind == "funding_sign":
            return self.funding_sign(entry)
        if kind == "ats_z_tercile":
            return self.ats_z_tercile(arm_row, entry, date)
        if kind == "link_basis_tercile":
            return self.link_basis_tercile(arm_row, entry, date)
        if kind == "warmup_state":
            for side, sleeves in (arm_row.get("split_groups")
                                  or {}).items():
                if entry["sleeve"] in sleeves:
                    return side
            return None
        return None


def _pool_entries(arm_row, entries, intent_entries):
    pool = [e for e in entries if e["sleeve"] in arm_row["parents"]]
    if arm_row.get("entry_source") == "intents":
        pool = pool + [e for e in (intent_entries or [])
                       if e["sleeve"] in arm_row["parents"]]
        pool.sort(key=lambda e: e["ts"])
    return pool


def _priced_fwd(book, bench, arm_row, e):
    """(date, {horizon: (raw, excess)}) for one entry, or None."""
    series, date, i = _entry_series(book, arm_row, e)
    if i is None or series is None:
        return None
    price = e["price"]
    if not price:
        price = series[1].get(series[0][i])
        if not price:
            return None
    out = {}
    for h in arm_row["horizons"]:
        f = fwd_ret(series, bench, i, price, e["dir"], h)
        if f is not None:
            out[h] = f
    return date, out


def grade_split(book, bench, arm_row, entries, intent_entries=None,
                split_ctx=None):
    pool = _pool_entries(arm_row, entries, intent_entries)
    sides = {}
    unstamped = 0
    pooled_dec = []
    for e in pool:
        got = _priced_fwd(book, bench, arm_row, e)
        if got is None:
            continue
        date, fwd = got
        side = split_ctx.key(arm_row, e, date) if split_ctx else None
        if side is None:
            unstamped += 1
            continue
        cell = sides.setdefault(
            side, {h: {"raw": [], "excess": []}
                   for h in arm_row["horizons"]})
        for h, f in fwd.items():
            cell[h]["raw"].append(f[0])
            if f[1] is not None:
                cell[h]["excess"].append(f[1])
        dec = arm_row["decisive_horizons"]
        if all(h in fwd and fwd[h][1] is not None for h in dec):
            pooled_dec.append(
                sum(fwd[h][1] for h in dec) / len(dec))
    dec = arm_row["decisive_horizons"]
    res = {"entries_seen": len(pool), "unstamped": unstamped,
           "sides": {}}
    side_dec_mean = {}
    for side, cell in sides.items():
        res["sides"][side] = {
            str(h): {"raw": stats_bp(cell[h]["raw"]),
                     "excess": stats_bp(cell[h]["excess"])}
            for h in arm_row["horizons"]}
        vals = [x for h in dec for x in cell[h]["excess"]]
        side_dec_mean[side] = (stats_bp(vals)["mean_bp"], len(vals))
    res["side_decisive"] = {
        s: {"mean_excess_bp": m, "n": n}
        for s, (m, n) in side_dec_mean.items()}
    res["pooled_decisive"] = stats_bp(pooled_dec)
    mode = arm_row.get("grade_mode", "per_side")
    if mode == "per_side":
        graded = bool(side_dec_mean) and all(
            n >= arm_row["grade_n"]
            for _m, n in side_dec_mean.values()) \
            and len(side_dec_mean) >= 2
    else:
        graded = len(pooled_dec) >= arm_row["grade_n"] and all(
            side_dec_mean.get(s, (None, 0))[1] >= n
            for s, n in (arm_row.get("min_side") or {}).items()) \
            and all(n > 0 for _m, n in side_dec_mean.values()) \
            and len(side_dec_mean) >= 2
    if not graded:
        res["state"] = "ACCRUING"
        return res
    a, b = (arm_row.get("spread_sides") or [None, None])[:2]
    ma = side_dec_mean.get(a, (None, 0))[0]
    mb = side_dec_mean.get(b, (None, 0))[0] if b else None
    rule = arm_row.get("positive_rule", "a_positive_and_above_b")
    if rule == "a_above_b":
        pos = ma is not None and mb is not None and ma > mb
    elif rule == "a_differs_from_pooled":
        pooled_mean = stats_bp(pooled_dec)["mean_bp"]
        pos = (ma is not None and pooled_mean is not None
               and abs(ma - pooled_mean)
               >= arm_row.get("spread_bp", 100))
    else:
        pos = (ma is not None and mb is not None and ma > 0
               and ma > mb)
    res["state"] = "GRADED_POSITIVE" if pos else "GRADED_NEGATIVE"
    return res


def grade_phase(book, bench, arm_row, entries, intent_entries=None,
                split_ctx=None):
    pool = _pool_entries(arm_row, entries, intent_entries)
    buckets = arm_row["phase_buckets"]
    vals = {b["name"]: [] for b in buckets}
    sessions = set()
    for e in pool:
        series, date, i = _entry_series(book, arm_row, e)
        if i is None or series is None:
            continue
        dates, closes = series
        price = e["price"] or closes.get(dates[i])
        if not price:
            continue
        sessions.add(date)
        bd, bc = bench if bench else ([], {})
        for b in buckets:
            start = i + b["from"] - 1
            if start < i or start >= len(dates):
                continue
            if b["to"] is None:
                if len(dates) - 1 < i + b["from"]:
                    continue
                end = len(dates) - 1
            else:
                if i + b["to"] >= len(dates):
                    continue
                end = i + b["to"]
            raw = e["dir"] * (closes[dates[end]]
                              / closes[dates[start]] - 1)
            exc = None
            if dates[start] in bc and dates[end] in bc:
                exc = raw - (bc[dates[end]] / bc[dates[start]] - 1)
            if exc is not None:
                vals[b["name"]].append(exc)
    res = {"entries_seen": len(pool),
           "entry_sessions": len(sessions),
           "phases": {n: stats_bp(v) for n, v in vals.items()}}
    count = len(sessions) if "sessions" in arm_row["grade_unit"] \
        else len(pool)
    res["grade_count"] = count
    n23 = stats_bp(vals.get("N2-3", []))
    n1 = stats_bp(vals.get("N1", []))
    if count >= arm_row["grade_n"] and n23["n"] > 0:
        if arm_row.get("phase_positive") \
                == "n23_positive_and_above_n1":
            pos = (n23["mean_bp"] is not None and n23["mean_bp"] > 0
                   and n1["mean_bp"] is not None
                   and n23["mean_bp"] > n1["mean_bp"])
        else:
            pos = n23["mean_bp"] is not None and n23["mean_bp"] > 0
        res["state"] = "GRADED_POSITIVE" if pos else "GRADED_NEGATIVE"
    else:
        res["state"] = "ACCRUING"
    return res


def _decisive_excess(book, bench, arm_row, entries):
    """{sleeve: [decisive excess values]} plus pooled list."""
    per = {}
    pooled = []
    dec = arm_row["decisive_horizons"]
    for e in entries:
        got = _priced_fwd(book, bench, arm_row, e)
        if got is None:
            continue
        _date, fwd = got
        if all(h in fwd and fwd[h][1] is not None for h in dec):
            v = sum(fwd[h][1] for h in dec) / len(dec)
            per.setdefault(e["sleeve"], []).append(v)
            pooled.append(v)
    return per, pooled


def grade_member(book, bench, arm_row, entries, intent_entries=None,
                 split_ctx=None, roster_ids=None):
    pool = _pool_entries(arm_row, entries, intent_entries)
    per, pooled = _decisive_excess(book, bench, arm_row, pool)
    comp_ids = arm_row.get("complement_parents")
    if arm_row.get("complement") == "ALL_OTHER_ROSTER":
        comp_ids = [s for s in (roster_ids or [])
                    if s not in arm_row["parents"]]
    comp_pool = [e for e in entries if e["sleeve"] in (comp_ids or [])]
    _cper, comp = _decisive_excess(book, bench, arm_row, comp_pool)
    res = {"entries_seen": len(pool),
           "per_member_decisive_n": {
               s: len(per.get(s, [])) for s in arm_row["parents"]},
           "cell_decisive": stats_bp(pooled),
           "complement_decisive": stats_bp(comp),
           "complement_entries_seen": len(comp_pool)}
    graded = all(len(per.get(s, [])) >= arm_row["grade_n"]
                 for s in arm_row["parents"])
    if not graded:
        res["state"] = "ACCRUING"
        return res
    cell_mean = stats_bp(pooled)["mean_bp"]
    pos = cell_mean is not None and cell_mean > 0
    if pos and arm_row.get("must_beat_complement"):
        comp_mean = stats_bp(comp)["mean_bp"]
        pos = comp_mean is not None and cell_mean > comp_mean
    res["state"] = "GRADED_POSITIVE" if pos else "GRADED_NEGATIVE"
    return res


def grade_two_pool(book, bench, arm_row, entries,
                   intent_entries=None, split_ctx=None):
    pool = _pool_entries(arm_row, entries, intent_entries)
    excl = set(arm_row.get("excluded") or [])
    incl_pool = pool
    excl_pool = [e for e in pool if e["sleeve"] not in excl]
    var_pool = [e for e in pool if e["sleeve"] in excl]
    _pi, incl = _decisive_excess(book, bench, arm_row, incl_pool)
    _pe, without = _decisive_excess(book, bench, arm_row, excl_pool)
    per_var, var = _decisive_excess(book, bench, arm_row, var_pool)
    res = {"entries_seen": len(pool),
           "per_variant_decisive_n": {
               s: len(per_var.get(s, [])) for s in sorted(excl)},
           "family_incl_decisive": stats_bp(incl),
           "family_excl_decisive": stats_bp(without),
           "variant_decisive": stats_bp(var)}
    graded = all(len(per_var.get(s, [])) >= arm_row["grade_n"]
                 for s in excl)
    if not graded:
        res["state"] = "ACCRUING"
        return res
    var_mean = stats_bp(var)["mean_bp"]
    res["state"] = ("GRADED_POSITIVE"
                    if var_mean is not None and var_mean > 0
                    else "GRADED_NEGATIVE")
    return res


def grade_forecast_join(book, bench, arm_row, entries):
    """FORECAST_JOIN (NIGHTLY-JOIN-ARTIFACTS-20261116): CONV-86
    (LS7) and CONV-87 (LS8) grade on the one nightly forecast-
    ledger plus bars join (desk3.nightly_join), whose artifact
    the desk reads at state/nightly_join/latest.json. No second
    join exists: this grader only reads that artifact. A missing
    artifact is an ACCRUING arm with the absence named, never a
    fabricated zero (the join's first nightly run writes it).
    CONV-86: resolved qualifying oversold joint-below calls,
    decisive at grade_n on mean next-night overnight net of the
    registered 5bp friction. CONV-87: resolved bar-carrying
    calls split by window, decisive at grade_n on the macro
    minus quiet next-night overnight difference."""
    res = {"entries_seen": 0, "resolved_decisive": 0,
           "state": "ACCRUING"}
    path = os.path.join(book.root, "state", "nightly_join",
                        "latest.json")
    if not os.path.exists(path):
        res["detail"] = ("nightly join artifact absent "
                         "(state/nightly_join/latest.json); the "
                         "join runs nightly before this grade")
        return res
    doc = json.load(open(path))
    rows = [r for r in doc.get("rows") or []
            if r.get("state") == "RESOLVED"]
    if arm_row.get("join_arm") == "LS7":
        qual = [r for r in rows if r.get("qualifying_ls7")]
        res["entries_seen"] = len(doc.get("qualifying") or [])
        res["resolved_decisive"] = len(qual)
        if qual:
            res["ls7"] = stats_bp([r["next_on"] for r in qual])
            res["mean_net_bp"] = round(
                res["ls7"]["mean_bp"] - 5.0, 2)
        if len(qual) >= arm_row["grade_n"]:
            res["state"] = ("GRADED_POSITIVE"
                            if res["mean_net_bp"] > 0
                            else "GRADED_NEGATIVE")
        return res
    macro = [r["next_on"] for r in rows if r.get("window") == "macro"]
    quiet = [r["next_on"] for r in rows if r.get("window") == "quiet"]
    res["entries_seen"] = len(rows)
    res["resolved_decisive"] = len(macro) + len(quiet)
    res["macro"] = stats_bp(macro)
    res["quiet"] = stats_bp(quiet)
    if macro and quiet:
        res["split_bp"] = round(
            (sum(macro) / len(macro)
             - sum(quiet) / len(quiet)) * 1e4, 2)
    if len(macro) + len(quiet) >= arm_row["grade_n"]:
        res["state"] = ("GRADED_POSITIVE"
                        if res.get("split_bp") is not None
                        and res["split_bp"] > 0
                        else "GRADED_NEGATIVE")
    return res


def held_sessions(entries, exits, book):
    """(entry, ET date) pairs for every session a position was
    held, FIFO on (sleeve, symbol) like match_actuals: a lot is
    held on its entry session and every later session up to (not
    including) its exit session; a same-session round trip counts
    its entry session; an unclosed lot is held through the latest
    session on the symbol's daily series. Sessions are the
    symbol's own daily-series dates, so weekends and holidays
    never appear."""
    lots = {}
    for e in entries:
        lots.setdefault((e["sleeve"], e["symbol"]), []).append(
            {"entry": e, "remaining": e["qty"], "exit_date": None})
    for x in exits:
        q = x["qty"]
        for lot in lots.get((x["sleeve"], x["symbol"])) or []:
            if q <= 0:
                break
            if x["ts"] <= lot["entry"]["ts"]:
                continue
            take = min(q, lot["remaining"])
            lot["remaining"] -= take
            q -= take
            if lot["remaining"] <= 1e-9:
                lot["exit_date"] = x["date_et"]
    out = []
    for key in sorted(lots):
        for lot in lots[key]:
            e = lot["entry"]
            series = book.daily(e["symbol"])
            if series is None:
                continue
            dates, _closes = series
            for d in dates:
                if d < e["date_et"]:
                    continue
                if lot["exit_date"] is not None \
                        and d > lot["exit_date"]:
                    break
                if lot["exit_date"] is not None \
                        and d == lot["exit_date"] \
                        and lot["exit_date"] != e["date_et"]:
                    continue
                out.append((e, d))
    return out


def grade_segment(book, bench, arm_row, entries, exits,
                  minute_book):
    """CONV-80 stage 1 (SEGMENT_GRADE): segment means on the
    arm's parents' held sessions only, priced from the 1Min
    cache through the shared segment engine. The grade counts
    distinct forward sessions carrying at least one priced held
    session, against the registered grade_n (20); the claim
    survives only if the forward MIDDAY mean is negative (the
    register's falsifier, carried on the arm row)."""
    pool = [e for e in entries if e["sleeve"] in arm_row["parents"]]
    seg_vals = {s: [] for s in ("OPEN_DRIVE", "MIDDAY",
                                "CLOSE_HOUR", "OVERNIGHT")}
    sessions = set()
    held_n = 0
    unpriced = 0
    for e, date in held_sessions(pool, exits, book):
        series = book.daily(e["symbol"])
        prev = None
        if series is not None:
            dates, closes = series
            i = idx_of(series, date)
            if i is not None and i > 0:
                prev = closes[dates[i - 1]]
        marks = minute_book.marks(e["symbol"], date, prev)
        if marks is None:
            unpriced += 1
            continue
        held_n += 1
        sessions.add(date)
        for name, v in marks.items():
            seg_vals[name].append(e["dir"] * v)
    res = {"entries_seen": len(pool),
           "held_sessions_priced": held_n,
           "held_sessions_unpriced": unpriced,
           "forward_sessions": len(sessions),
           "segments": {s: stats_bp(v) for s, v in seg_vals.items()}}
    if len(sessions) >= arm_row["grade_n"]:
        mid = stats_bp(seg_vals["MIDDAY"])["mean_bp"]
        res["state"] = ("GRADED_POSITIVE"
                        if mid is not None and mid < 0
                        else "GRADED_NEGATIVE")
    else:
        res["state"] = "ACCRUING"
    return res


GRADERS = {"FWD_GRADE": grade_fwd, "EXIT_PAIR": grade_exit_pair,
           "ACTUAL_PAIR": grade_actual_pair, "RACE": grade_race,
           "SPLIT_GRADE": grade_split, "PHASE_GRADE": grade_phase,
           "MEMBER_GRADE": grade_member, "TWO_POOL": grade_two_pool,
           "FORECAST_JOIN": grade_forecast_join}


def run(root, dry_run=False):
    reg_path = os.path.join(root, "config",
                            "conversion_shadow_20261115.json")
    reg = json.load(open(reg_path))
    start = reg["start_date_et"]
    book = SeriesBook(root)
    bench = book.bench()
    entries, exits = load_fills(root, start)
    intent_entries = None
    fires = None
    split_ctx = None
    roster_ids = None
    minute_book = None
    results = []
    for arm_row in reg["arms"]:
        row = {"conv": arm_row["conv"], "kind": arm_row["kind"],
               "parents": arm_row["parents"],
               "falsifier": arm_row["falsifier"],
               "kill_rule": arm_row["kill_rule"],
               "grade_n": arm_row["grade_n"],
               "grade_unit": arm_row["grade_unit"]}
        if spec_drift(arm_row):
            row["state"] = "SPEC_DRIFT"
            row["detail"] = ("registered base profile no longer "
                             "matches the live lazarus SPECS; not "
                             "graded")
            results.append(row)
            continue
        kind = arm_row["kind"]
        if kind == "GATE_PAIR":
            if fires is None:
                fires = load_fires(root, start)
            row.update(grade_gate_pair(book, bench, arm_row, fires))
            row["entries_seen"] = len(fires)
        elif kind == "ACTUAL_PAIR":
            row.update(GRADERS[kind](book, bench, arm_row, entries,
                                     exits))
        elif kind == "SEGMENT_GRADE":
            if minute_book is None:
                minute_book = MinuteBook(root)
            row.update(grade_segment(book, bench, arm_row, entries,
                                     exits, minute_book))
        elif kind == "FWD_GRADE" and arm_row.get(
                "entry_source") == "intents":
            if intent_entries is None:
                intent_entries = load_intent_entries(
                    root, start,
                    {p for a in reg["arms"] for p in a["parents"]})
            row.update(grade_fwd(book, bench, arm_row, entries,
                                 intent_entries))
        elif kind in ("SPLIT_GRADE", "PHASE_GRADE", "MEMBER_GRADE",
                      "TWO_POOL"):
            if arm_row.get("entry_source") == "intents" \
                    and intent_entries is None:
                intent_entries = load_intent_entries(
                    root, start,
                    {p for a in reg["arms"] for p in a["parents"]})
            if split_ctx is None:
                split_ctx = SplitContext(root)
            if kind == "MEMBER_GRADE" and roster_ids is None:
                try:
                    roster_ids = [r["id"] for r in json.load(open(
                        os.path.join(root, "config",
                                     "sleeves.json")))["sleeves"]]
                except Exception:
                    roster_ids = []
            row.update(GRADERS[kind](book, bench, arm_row, entries,
                                     intent_entries, split_ctx,
                                     roster_ids)
                       if kind == "MEMBER_GRADE" else
                       GRADERS[kind](book, bench, arm_row, entries,
                                     intent_entries, split_ctx))
        else:
            row.update(GRADERS[kind](book, bench, arm_row, entries))
        results.append(row)
    out_dir = os.path.join(root, "state", "conversion_shadow")
    ts = datetime.now(timezone.utc).isoformat()
    if not dry_run:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "latest.json"), "w") as fh:
            json.dump({"generated_at": ts, "registry": reg["registry"],
                       "start_date_et": start, "arms": results},
                      fh, indent=1, sort_keys=True)
        with open(os.path.join(out_dir, "ledger.jsonl"), "a") as fh:
            for row in results:
                fh.write(json.dumps(
                    {"ts": ts, "conv": row["conv"],
                     "state": row.get("state"),
                     "entries_seen": row.get("entries_seen")},
                    sort_keys=True) + "\n")
    lines = [f"CONVERSION-SHADOW-20261115 grade run {ts} "
             f"(entries from {start} ET forward)"]
    for row in results:
        lines.append(f"  {row['conv']} {row['kind']} "
                     f"state={row.get('state')} "
                     f"entries_seen={row.get('entries_seen')} "
                     f"grade_at={row['grade_n']} "
                     f"({row['grade_unit']})")
    return "\n".join(lines), results


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    text, _results = run(root, dry_run="--dry-run" in argv)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
