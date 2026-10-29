"""Milkman v2 daily rules on the engine — dstrats.py with 12_run_daily.py's grids and the study's designated cell per
set and side (out/tab_primary.md: Milkman's own cell "(his)", else the study's plateau pick). One sleeve per rule;
each runs its lanes (set, side, cell). The rules in SPLIT run one sleeve per side (their sides net to zero).

Sets: "index" = the study's Yahoo index/futures set (SPY QQQ IWM DIA XLK XLF XLE SMH TLT GLD + ES=F NQ=F RTY=F YM=F;
Yahoo daily OHLC as downloaded with auto_adjust=False, full history); "univ" = its stock universe — the store_v1
survivors it was drawn from (desk/vendor/milkman/store_v1_1d_index.json, 1,822 names; >= 260 bars since 2016-01-01;
split-adjusted daily bars read cache-only, kept fresh by the genome job), liquidity-gated by the study's liq_gate.

The rule programs (rules.py) decide on daily bars as the study's engines do (tools/parity/milkman_daily.py replays them
against the study's own functions). This module carries their decisions to the engine by session phase:
  watch  (open .. close-16)   the first look runs the open phase (market-on-open exits / weekday and next-open
                              entries, levels gapped through at the open); every look then runs the touch phase on the
                              session range so far (the quote's day high / low / last): stop entries, voids, stops,
                              targets and touch exits, executed at once. Golden Gate periods are opened at the first
                              look of the day (their levels come from the prior period).
  close  (close-15 .. close-11)  the touch phase once more, then the close phase on the provisional bar (open / high /
                              low so far, the last price as the close, volume so far): close entries and exits, sent
                              market-on-close (tif cls).
  after  (after the close)    the completed bar: touches after the close look, a close phase the desk missed (its
                              entries are not taken late), the end phase (box locks, filters and stops for the next
                              bar, the follow-through machine, next-open signals). Its events execute next open.
Sizing (the study has none — it is per trade, equal weight, every signal taken): a fixed $10,000 per trade on a
$1,000,000 virtual book; each lane keeps its own trade ledger; the sleeve trades the net per symbol.
Gone under the cutover doctrine: nothing (the study has no desk-wide gates).
Named divergences:
  1. close decisions read the provisional bar 15 minutes before the close (the study decided on the final bar and
     filled at its close); the after pass records a "flip" when the final close differs;
  2. level events fill at the live market once a look sees the level reached (the study filled at the level, or at
     the open on a gap); a level reached between looks is caught from the session high / low; several new levels in
     one look resolve by the study's same-bar order (void before entry, stop before target);
  3. events the final bar reveals after the close look (late touches, a box locked by its episode's end, the
     next-open signals the study itself enters at the next open) execute at the next open;
  4. sizing rendering, as above;
  5. univ data: the desk's split-adjusted bars for the store_v1 survivors (the study read the store_v1 bars and
     included 1,152 since-delisted names; history is as deep as the genome cache — the Swing GG monthly ATR is seeded
     from it rather than from 2016-01); a univ provisional bar comes from the quote source (Alpaca's IEX snapshot
     when keyed: IEX range and volume);
  6. index futures: ES=F NQ=F RTY=F YM=F trade on the labelled sim venue sim:alpaca_equity, which quotes them from
     Yahoo on a desk without Alpaca keys; on a keyed (paper) desk that venue quotes from Alpaca, which does not list
     them, so there their lanes record their decisions as observations until a Yahoo-quoted sim venue exists;
  7. an entry on a Golden Gate period's last session that does not exit on that bar is closed at that session's
     close (the study's engine leaves it open and drops it);
  8. downtime: bars missed while the desk was down are replayed for state; their entries are not taken late and their
     exits execute at the next open."""
import os
from datetime import date, timedelta

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from . import MARGIN_RATE
from . import rules as R
from . import vendored as V

SOURCE = {"repo": "quant-research-critical", "ref": "main", "commit": "0be4c57569e363d052bd23564cf0664697439927",
          "path": "milkman-study/v2/code/dstrats.py", "blob": "c1845e96afc6e5b3c53244055f3a8497bf752d6c",
          "grid": "milkman-study/v2/code/12_run_daily.py@e895ae7d", "cells": "milkman-study/v2/out/tab_primary.md"}
INDEX_ETF = ("SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "SMH", "TLT", "GLD")
INDEX_FUT = ("ES=F", "NQ=F", "RTY=F", "YM=F")
NOTIONAL = 10_000.0
CAPITAL = 1_000_000.0
UNIV_START = "2016-01-01"
H, L = 1, -1
HIS = {
    "D7": ("mk_connorsdouble7", "N=7;ma=200"),
    "LBD": ("mk_legendsbuydaydailyproxy", "k=3;exact=True"),
    "DOW": ("mk_weekdayopentocloseproxy", "dow=0"),
    "DBB": ("mk_dailybilbobox", "boxlen=5;exitm=ema50"),
    "SGG": ("mk_swinggoldengatemonthly", "freq=M;entry_lvl=0.618;ema_gate=with;stop=pivot"),
    "MDGG": ("mk_multidaygoldengateweekly",
             "freq=W;entry_lvl=0.382;tgt_lvl=0.618;stop=pivot;ema_gate=off;po_filter=True;min_left=1"),
    "RIB": ("mk_pivotribbon1348cross", "exitm=opposite"),
    "BIG": ("mk_bigdowndayresponse", "thr=-2.0;H=10"),
    "FTD": ("mk_oneilfollowthroughdayrace", "corr=10.0;gain=1.25"),
}
PLATEAU = {
    "E21": ("mk_ema21deviationreversion", {("univ", H): "k=2.0;H=10", ("index", L): "k=4.0;H=10",
                                            ("univ", L): "k=4.0;H=20", ("index", H): "k=3.5;H=28"}),
    "PO": ("mk_phaseoscillatorzoneexit", {("univ", L): "kind=extreme;H=20", ("univ", H): "kind=accum;H=20",
                                           ("index", L): "kind=accum;H=10", ("index", H): "kind=extreme;H=20"}),
    "CEX": ("mk_dailycompressionexpansion", {("index", H): "minbars=10;H=5", ("univ", H): "minbars=10;H=5",
                                              ("index", L): "minbars=3;H=10", ("univ", L): "minbars=5;H=20"}),
}
SETS = {"D7": ("univ", "index"), "LBD": ("univ", "index"), "DOW": ("index",), "DBB": ("univ", "index"),
        "SGG": ("univ", "index"), "MDGG": ("univ", "index"), "RIB": ("univ", "index"), "BIG": ("index",),
        "FTD": ("index",), "E21": ("univ", "index"), "PO": ("univ", "index"), "CEX": ("univ", "index")}
PROGRAM = {"SGG": "GG", "MDGG": "GG"}
CLOSE_ENTRY = {"D7", "LBD", "E21", "PO", "RIB", "BIG", "FTD"}       # rules whose entries happen at the close
END_ALL = {"DBB", "CEX", "FTD", "LBDD"}                             # rules whose end phase concerns every symbol
ORDER = ("D7", "LBD", "DOW", "DBB", "SGG", "MDGG", "E21", "PO", "RIB", "CEX", "BIG", "FTD")


def parse_cell(s):
    out = {}
    for kv in s.split(";"):
        k, v = kv.split("=")
        if v in ("True", "False"):
            out[k] = v == "True"
            continue
        for cast in (int, float):
            try:
                out[k] = cast(v)
                break
            except ValueError:
                continue
        else:
            out[k] = v
    return out


def lane(lid, setname, side, rule, text, syms):
    return {"id": lid, "set": setname, "side": side, "cell": parse_cell(text), "cell_text": text, "rule": rule,
            "prog": R.RULES[PROGRAM.get(rule, rule)], "syms": tuple(syms), "symset": frozenset(syms)}


def lanes_of(rule, sides=(H, L)):
    out = []
    for st in SETS[rule]:
        syms = INDEX_ETF + INDEX_FUT if st == "index" else V.univ_symbols()
        for side in sides:
            text = HIS[rule][1] if rule in HIS else PLATEAU[rule][1][(st, side)]
            out.append(lane(f"{st}:{'L' if side > 0 else 'S'}", st, side, rule, text, syms))
    return out


# 50_crypto.py: every coded daily strategy's primary cell, both sides, on the crypto-linked stock universe
# (Author-research/CRYPTO_STOCKS/out/crypto_universe.csv, the first *universe* file it reads) within the study's
# stock panel
CRYPTO_PRIM = (("D7", "N=7;ma=200"), ("LBD", "k=3;exact=True"), ("DBB", "boxlen=5;exitm=ema50"),
               ("SGG", "freq=M;entry_lvl=0.618;ema_gate=with;stop=pivot"),
               ("MDGG", "freq=W;entry_lvl=0.382;tgt_lvl=0.618;stop=pivot;ema_gate=off;po_filter=True;min_left=1"),
               ("E21", "k=2.0;H=10"), ("PO", "kind=accum;H=20"), ("RIB", "exitm=opposite"), ("CEX", "minbars=10;H=5"))
CRYPTO_SOURCE = {"repo": "quant-research-critical", "ref": "main", "commit": "0be4c57569e363d052bd23564cf0664697439927",
                 "path": "milkman-study/v2/code/50_crypto.py", "blob": "31361c6c3d9bbe8844ddf9fda060ae77449877aa",
                 "universe": "quant-research-backup@d170596b Author-research/CRYPTO_STOCKS/out/crypto_universe.csv "
                             "(blob bbb45e42)"}


def crypto_symbols():
    """the crypto universe file's symbols (sorted, deduplicated, as 50_crypto reads them) that are in the study's stock
    panel; on this desk that is the store_v1 survivors (the study's panel also held since-delisted names)."""
    import csv
    rows = list(csv.DictReader(open(os.path.join(V.VENDOR, "crypto_universe.csv"))))
    syms = sorted({str(r["sym"]) for r in rows})
    univ = set(V.univ_symbols())
    return tuple(s for s in syms if s in univ)


def crypto_sleeve():
    syms = crypto_symbols()
    lanes = [lane(f"{rule}:{'L' if side > 0 else 'S'}", "univ", side, rule, text, syms)
             for rule, text in CRYPTO_PRIM for side in (H, L)]
    return MilkmanDaily("CRYPTO", lanes=lanes, sid="mk_milkmancryptolinkedstockvariant", source=CRYPTO_SOURCE)


# Legend's Buy Day, the day leg (milkmantrades.com/legends-buy-day.html section 8): his package's LEG 2, long only,
# on SPY standing in for ES; quant-research-critical keeps his package as he published it
LBDD_SOURCE = {"repo": "quant-research-critical", "ref": "main", "commit": "0be4c57569e363d052bd23564cf0664697439927",
               "path": "milkman-study/v2/packages/legends-buy-day-package/02_buyday_backtest.py",
               "blob": "8c8a41f122e2a1c98411e61e7256afcb9662be6f", "lines": "11-15",
               "page": "https://milkmantrades.com/legends-buy-day.html"}


def legends_day_sleeve():
    """the day leg on SPY. Named divergence: SPY's regular-session daily bars stand in for ES's full sessions, so the
    ATR (his: the mean of the prior 20 full-session ranges) and the stop (his: one tick under the prior full-session
    low) read regular-session ranges and lows; the overnight move is the open against the prior close, as his."""
    lanes = [lane("index:L", "index", H, "LBDD", "k=4;gate=0.15;atrn=20;tick=0.01", ("SPY",))]
    return MilkmanDaily("LBDD", lanes=lanes, sid="mk_legendsbuydaydayleg", source=LBDD_SOURCE, prime=True)


def sleeve_id(rule):
    return (HIS.get(rule) or PLATEAU.get(rule))[0]


# The owner's split (2026-10-19). These rules' long and short lanes enter and exit on the same bars: one entry signal,
# and FTD's long target is its short stop and the other way round. Netted in one sleeve they were always zero, so the
# sleeve could never hold a position. Each side runs as its own sleeve, as the study tested them (one row per set and
# side): the long side under the rule's id, the short side under <id>_short. desk/migrations moved the short lanes'
# records once.
SPLIT = ("DOW", "BIG", "FTD")


def side_sleeves(rule):
    return [MilkmanDaily(rule, lanes=lanes_of(rule, (H,))),
            MilkmanDaily(rule, lanes=lanes_of(rule, (L,)), sid=sleeve_id(rule) + "_short")]


# --------------------------------------------------------------------------------------------- data
def session_of(t):
    return cal._as_date(float(t) + 6 * 3600).isoformat()


def ctx_for(setname, sym, bars, prov=None):
    """the study's arrays for one symbol from the desk's daily bars (+ today's provisional bar)."""
    rows = []
    for b in bars or ():
        d = session_of(b["t"])
        if setname == "univ" and d < UNIV_START:
            continue
        o, h, l, c = (b.get(k) for k in ("o", "h", "l", "c"))
        if None in (o, h, l, c):
            continue
        if setname == "index" and not (o > 0 and h >= l):          # load_index: dropna, o > 0, h >= l
            continue
        rows.append((d, float(o), float(h), float(l), float(c), float(b.get("v") or 0.0)))
    if prov:
        rows = [r for r in rows if r[0] < prov["date"]]
        rows.append((prov["date"], prov["o"], prov["h"], prov["l"], prov["c"], prov["v"]))
    if len(rows) < (260 if setname == "univ" else 2):                 # load_universe: >= 260 bars
        return None
    kind = "stock" if setname == "univ" else ("fut" if sym.endswith("=F") else "etf")
    a = list(zip(*rows))
    return R.Ctx(a[0], a[1], a[2], a[3], a[4], a[5], kind)


def provisional(q, session):
    """today's bar so far from a quote: the session's open / high / low / volume and the last price as the close."""
    if not q or (q.get("day_date") or q.get("session")) != session:
        return None
    o, hi, lo = q.get("day_open"), q.get("day_high"), q.get("day_low")
    last = q.get("last") or q.get("day_close")
    if not (o and hi and lo and last):
        return None
    return {"date": session, "o": float(o), "h": float(max(hi, last, o)), "l": float(min(lo, last, o)),
            "c": float(last), "v": float(q.get("day_volume") or 0.0)}


def period_last(session, freq):
    """the last trading session of the study's period containing `session` (pandas Period M, or W = W-SUN)."""
    d = cal._as_date(session)
    if freq == "M":
        end = date(d.year + (d.month == 12), d.month % 12 + 1, 1) - timedelta(days=1)
    else:
        end = d + timedelta(days=6 - d.weekday())
    while not cal.is_trading_day(end):
        end -= timedelta(days=1)
    return end.isoformat()


def phase(now):
    d = cal._as_date(now)
    if not cal.is_trading_day(d):
        return None
    o, c = cal.session_open(d), cal.session_close(d)
    if o <= now < c - 15 * 60:
        return "watch"
    if c - 15 * 60 <= now <= c - 11 * 60:
        return "close"
    if now >= c + 25 * 60:
        return "after"
    return None


# --------------------------------------------------------------------------------------------- the sleeve
class MilkmanDaily(Sleeve):
    """one Milkman daily rule (or, for the crypto variant, several) as lanes; each lane carries its rule program,
    cell, side, data set (index / univ) and symbols."""

    def __init__(self, rule, lanes=None, sid=None, source=None, prime=False):
        self.rule = rule
        self.prime = prime                      # a first pass arms from the last completed bar (see _prime)
        self.lanes = lanes or lanes_of(rule)
        self.sets = tuple(dict.fromkeys(l["set"] for l in self.lanes))
        self.spec = {"cache_only": "univ" in self.sets}           # the genome job keeps the univ bars fresh
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=sid or sleeve_id(rule), family="milkman", cadence_s=60, universe=(), capital=CAPITAL,
            schedule="rth,after_close+25:after_close+330",
            needs={"feeds": [f"milkman_bars:{s}" for s in self.sets] + ["milkman_quotes"]},
            params={"rule": rule, "notional": NOTIONAL, "margin_rate": MARGIN_RATE,
                    "lanes": [{"id": l["id"], "rule": l["rule"], "cell": l["cell_text"]} for l in self.lanes]},
            source=source or dict(SOURCE, rule=rule),
            state_schema={"lanes": "dict", "today": "dict", "pending": "list", "ledger": "dict", "flips": "list",
                          "done": "dict"})

    def bind(self, engine):
        self.engine = engine

    # -- what the feeds / the genome job ask --------------------------------------------------------------------
    def futures_live(self):
        """futures lanes route to sim:alpaca_equity only where that venue quotes them (a desk without Alpaca keys)."""
        hub = getattr(self.engine, "hub", None)
        return hub is not None and getattr(hub, "alpaca", None) is None

    def universe_now(self, now, book=None):
        return tuple(sorted({s for l in self.lanes if l["set"] == "univ" for s in l["syms"]}))

    def _persisted(self):
        try:
            return (self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}) if self.engine is not None else {}
        except Exception:
            return {}

    def quote_plan(self, now):
        """{set: [symbols]} this pass needs quotes for."""
        ph = phase(now)
        if ph not in ("watch", "close"):
            return {}
        st = self._persisted()
        session = cal._as_date(now).isoformat()
        out = {}
        for l in self.lanes:
            syms = set()
            whole = (ph == "close" and l["rule"] in CLOSE_ENTRY) or \
                (l["rule"] == "DOW" and cal._as_date(now).weekday() == int(l["cell"]["dow"])) or \
                (l["prog"].name == "GG" and not (st.get("today") or {}).get("begun", {}).get(l["id"]) == session)
            if whole:
                syms |= set(l["syms"])
            for sym, S in ((st.get("lanes") or {}).get(l["id"]) or {}).items():
                if _active(S):
                    syms.add(sym)
            for p in st.get("pending") or []:
                if p.get("lane") == l["id"]:
                    syms.add(p["sym"])
            for x in (st.get("ledger") or {}).values():
                if x.get("lane") == l["id"]:
                    syms.add(x["sym"])
            out.setdefault(l["set"], set()).update(syms)
        return {k: sorted(v) for k, v in out.items()}

    # -- the pass -----------------------------------------------------------------------------------------------
    def signal(self, view):
        now, session = float(view.now), view.session
        ph = phase(now)
        st = dict(view.state or {})
        for k, v in (("lanes", {}), ("today", {}), ("pending", []), ("ledger", {}), ("flips", []), ("done", {})):
            st.setdefault(k, v)
        own = {l["id"] for l in self.lanes}        # a lane this sleeve does not run (the side split) is not its trade
        st["ledger"] = {k: x for k, x in st["ledger"].items() if x.get("lane") in own}
        st["pending"] = [p for p in st["pending"] if p.get("lane") in own]
        if st["today"].get("date") != session:
            st["today"] = {"date": session, "begun": {}, "obs": {}}
        self._st = st
        if ph is None:
            return []
        bars = {s: (view.extra.get(f"milkman_bars:{s}") or {}) for s in self.sets}
        quotes = view.extra.get("milkman_quotes") or {}
        if self.prime and not st.get("primed"):
            if ph != "after":                                          # the after pass arms from today's bar itself
                self._prime(st, session, bars)
            st["primed"] = session
        if ph == "after":
            st["pending"] += self._after(st, session, bars)
            return []
        events = []
        if st["done"].get("open") != session:                         # decided after the last close: execute now
            events += [dict(e, exec="now") for e in st["pending"]]
            st["pending"] = []
            st["done"]["open"] = session
        events += self._watch(st, session, bars, quotes, ph)
        if ph == "close":
            events += self._close(st, session, bars, quotes)
        return self._intents(view, st, events, session, quotes)

    def _prime(self, st, session, bars):
        """a sleeve that starts with no record (a first deploy, a reset) runs its rules' end phase on the last bar
        completed before this session, as that session's after pass would have, so a setup that bar armed is not
        lost. Completed bars only; what it arms still waits for the next open."""
        for lane in self.lanes:
            for sym in lane["syms"]:
                bl = [b for b in (bars.get(lane["set"], {}).get(sym) or []) if session_of(b["t"]) < session]
                X = ctx_for(lane["set"], sym, bl)
                if X is None:
                    continue
                S = self._S(st, lane, sym)
                if S.get("last") is not None:
                    continue
                t = X.n - 1
                lane["prog"].end(S, X, t, lane["side"], lane["cell"])
                S["last"] = X.dates[t]

    def _S(self, st, lane, sym):
        return R._fresh(st["lanes"].setdefault(lane["id"], {}).setdefault(sym, {}))

    def _obs(self, st, lane, sym):
        return st["today"]["obs"].setdefault(lane["id"], {}).setdefault(sym, {})

    @staticmethod
    def _seen(st, lane, sym):
        return (st["today"]["obs"].get(lane["id"]) or {}).get(sym) or {}

    def _lanes_by_set(self):
        out = {}
        for l in self.lanes:
            out.setdefault(l["set"], []).append(l)
        return out

    def _watch(self, st, session, bars, quotes, ph):
        """the open (first look) and touch phases from quotes; Golden Gate periods opened at the day's first look."""
        out = []
        for setname, lanes in self._lanes_by_set().items():
            qs = quotes.get(setname) or {}
            todo = [l for l in lanes if l["prog"].name == "GG" and st["today"]["begun"].get(l["id"]) != session]
            if todo:
                for sym in sorted({s for l in todo for s in l["syms"]}):
                    prov = provisional(qs.get(sym), session)
                    if prov is None:
                        continue
                    X = ctx_for(setname, sym, bars.get(setname, {}).get(sym), prov)
                    if X is None or X.dates[-1] != session:
                        continue
                    t = X.n - 1
                    for lane in todo:
                        if sym not in lane["symset"]:
                            continue
                        S = self._S(st, lane, sym)
                        out += self._catch_up(S, X, t, lane, sym)
                        pl = period_last(session, lane["cell"]["freq"])
                        lane["prog"].begin(S, X, t, lane["side"], lane["cell"], period_last=pl,
                                           left=cal.trading_days_between(session, pl))
                        self._obs(st, lane, sym)["begun"] = True
                for lane in todo:
                    st["today"]["begun"][lane["id"]] = session
            for lane in lanes:
                side, cell, prog = lane["side"], lane["cell"], lane["prog"]
                names = set(lane["syms"]) if lane["rule"] == "DOW" else set()
                names |= {s for s, S in (st["lanes"].get(lane["id"]) or {}).items() if _active(S)}
                for sym in sorted(names):
                    prov = provisional(qs.get(sym), session)
                    if prov is None:
                        continue
                    S = self._S(st, lane, sym)
                    ob = self._obs(st, lane, sym)
                    day = R.Day(session, prov["o"], "stock" if setname == "univ" else "etf")
                    evs = []
                    if not ob.get("seen"):
                        evs += prog.open(S, day, 0, side, cell)
                        evs += prog.touch(S, day, 0, side, cell, prov["l"], prov["h"], True)
                        ob["seen"] = [prov["l"], prov["h"]]
                    elif prov["l"] < ob["seen"][0] or prov["h"] > ob["seen"][1]:
                        evs += prog.touch(S, day, 0, side, cell, prov["l"], prov["h"], False)
                        ob["seen"] = [min(prov["l"], ob["seen"][0]), max(prov["h"], ob["seen"][1])]
                    for e in evs:
                        e.update(lane=lane["id"], sym=sym, side=side, exec="moc" if ph == "close" else "now")
                    out += evs
        return out

    def _close(self, st, session, bars, quotes):
        """the close phase on the provisional bar, market-on-close."""
        out = []
        for setname, lanes in self._lanes_by_set().items():
            qs = quotes.get(setname) or {}
            names = set()
            for lane in lanes:
                if lane["rule"] in CLOSE_ENTRY:
                    names |= set(lane["syms"])
                names |= {s for s, S in (st["lanes"].get(lane["id"]) or {}).items() if S.get("open")}
            for sym in sorted(names):
                todo = [l for l in lanes if sym in l["symset"] and not self._seen(st, l, sym).get("closed") and
                        (l["rule"] in CLOSE_ENTRY or ((st["lanes"].get(l["id"]) or {}).get(sym) or {}).get("open"))]
                if not todo:
                    continue
                prov = provisional(qs.get(sym), session)
                if prov is None:
                    continue
                X = ctx_for(setname, sym, bars.get(setname, {}).get(sym), prov)
                if X is None or X.dates[-1] != session:
                    continue
                t = X.n - 1
                for lane in todo:
                    S = self._S(st, lane, sym)
                    out += self._catch_up(S, X, t, lane, sym)
                    evs = lane["prog"].close(S, X, t, lane["side"], lane["cell"])
                    ob = self._obs(st, lane, sym)
                    ob["closed"], ob["prov_close"] = True, prov["c"]
                    if evs:
                        ob["ev"] = True
                    for e in evs:
                        e.update(lane=lane["id"], sym=sym, side=lane["side"], exec="moc")
                    out += evs
                    if not _active(S) and S.get("busy") is None and not S.get("episode") and not S.get("ftd") and \
                            not _period_decided(S, session):
                        st["lanes"][lane["id"]].pop(sym, None)     # nothing to carry: no state, no after work
                        if not evs:
                            st["today"]["obs"].get(lane["id"], {}).pop(sym, None)
        return out

    def _after(self, st, session, bars):
        """the completed session bar for every symbol whose bar is in: late touches, a missed close (exits only),
        the end phase. Events execute at the next open. Each (lane, symbol) is evaluated once a session (today's
        "after" marks): one whose state the evaluation leaves inactive is dropped from the lanes, and re-evaluating it
        on every later pass, to the same nothing, held passes at 65 s (mk_dailycompressionexpansion and
        mk_dailybilbobox, END_ALL over their universes: 15-16 s of CPU each a pass, 2026-10-16)."""
        out = []
        done = st["today"].setdefault("after", {})
        for setname, lanes in self._lanes_by_set().items():
            names = set()
            for lane in lanes:
                if lane["rule"] in END_ALL:
                    names |= set(lane["syms"])
                names |= set(st["lanes"].get(lane["id"]) or {})
                names |= {s for s, ob in (st["today"]["obs"].get(lane["id"]) or {}).items()
                          if ob.get("ev") or ob.get("seen")}
            for sym in sorted(names):
                todo = [l for l in lanes if sym in l["symset"] and sym not in (done.get(l["id"]) or {}) and
                        ((st["lanes"].get(l["id"]) or {}).get(sym) or {}).get("last") != session and
                        (l["rule"] in END_ALL or sym in (st["lanes"].get(l["id"]) or {}) or
                         sym in (st["today"]["obs"].get(l["id"]) or {}))]
                if not todo:
                    continue
                bl = bars.get(setname, {}).get(sym)
                if not bl or session_of(bl[-1]["t"]) != session:
                    continue                                        # the completed bar is not in yet
                X = ctx_for(setname, sym, bl)
                if X is None or X.dates[-1] != session:
                    continue
                t = X.n - 1
                for lane in todo:
                    out += self._after_one(st, session, lane, sym, X, t)
                    done.setdefault(lane["id"], {})[sym] = 1
        return out

    def _after_one(self, st, session, lane, sym, X, t):
        side, cell, prog = lane["side"], lane["cell"], lane["prog"]
        lanes = st["lanes"].setdefault(lane["id"], {})
        S = self._S(st, lane, sym)
        evs = self._catch_up(S, X, t, lane, sym)
        ob = (st["today"]["obs"].get(lane["id"]) or {}).get(sym) or {}
        if prog.name == "GG" and not ob.get("begun"):
            pl = period_last(session, cell["freq"])
            prog.begin(S, X, t, side, cell, period_last=pl, left=cal.trading_days_between(session, pl))
        late = []
        if not ob.get("seen"):
            late += prog.open(S, X, t, side, cell)
            late += prog.touch(S, X, t, side, cell, X.l[t], X.h[t], True)
        elif X.l[t] < ob["seen"][0] or X.h[t] > ob["seen"][1]:
            late += prog.touch(S, X, t, side, cell, X.l[t], X.h[t], False)
        if not ob.get("closed"):
            for e in prog.close(S, X, t, side, cell):
                if e["kind"] == "enter":                            # a close entry is not taken after the close
                    S["open"] = [x for x in S["open"] if x["tid"] != e["tid"]]
                else:
                    late.append(e)
        else:
            new = {e["tid"] for e in late if e["kind"] == "enter"}
            if new and prog.name in ("DBB", "GG"):                  # entries reached after the close look still owe
                keep = [x for x in S["open"] if x["tid"] not in new]  # their entry bar's close rule
                tmp = dict(S, open=[x for x in S["open"] if x["tid"] in new])
                late += prog.close(tmp, X, t, side, cell)
                S["open"], S["busy"] = keep + tmp["open"], tmp.get("busy")
            if ob.get("ev") and abs(float(ob.get("prov_close") or 0.0) - float(X.c[t])) > 1e-9:
                st["flips"] = (st["flips"] + [{"date": session, "lane": lane["id"], "sym": sym,
                                               "provisional": ob["prov_close"], "close": float(X.c[t])}])[-300:]
        late += prog.end(S, X, t, side, cell)
        S["last"] = session
        for e in evs + late:
            e.update(lane=lane["id"], sym=sym, side=side, exec="next_open")
        if S.get("busy") is not None and S["busy"] < session:
            S["busy"] = None
        if not _active(S) and not S.get("episode") and not S.get("ftd") and S.get("busy") is None and \
                not _period_decided(S, session):
            lanes.pop(sym, None)
        return evs + late

    def _catch_up(self, S, X, t, lane, sym):
        """bars between the last committed bar and bar t (desk downtime) replayed for state; their entries are not
        taken late, their exits execute next (named divergence 8)."""
        out = []
        last = S.get("last")
        if last is None:
            S["last"] = X.dates[t - 1] if t >= 1 else None
            return out
        i = X.i(last)
        if i is None:
            return out
        side, cell, prog = lane["side"], lane["cell"], lane["prog"]
        for k in range(i + 1, t):
            if prog.name == "GG":
                pl = period_last(X.dates[k], cell["freq"])
                prog.begin(S, X, k, side, cell, period_last=pl, left=cal.trading_days_between(X.dates[k], pl))
            evs = prog.open(S, X, k, side, cell) + prog.touch(S, X, k, side, cell, X.l[k], X.h[k], True) + \
                prog.close(S, X, k, side, cell) + prog.end(S, X, k, side, cell)
            for e in evs:
                if e["kind"] == "enter":
                    S["open"] = [x for x in S["open"] if x["tid"] != e["tid"]]
                else:
                    e.update(lane=lane["id"], sym=sym, side=side, exec="now", missed=True)
                    out.append(e)
            S["last"] = X.dates[k]
        return out

    # -- execution: the lanes' ledger, netted per symbol ---------------------------------------------------------
    def _set_of(self, lane_id):
        for l in self.lanes:
            if l["id"] == lane_id:
                return l["set"]
        return lane_id.split(":")[0]

    def _intents(self, view, st, events, session, quotes):
        if not events:
            return []
        ledger = st["ledger"]
        touched, refs = {}, {}
        for e in events:
            q = (quotes.get(self._set_of(e["lane"])) or {}).get(e["sym"]) or {}
            ref = q.get("last") or q.get("ask") or q.get("bid") or e["px"]
            refs.setdefault(e["sym"], ref)
            key = f"{e['lane']}|{e['sym']}|{e['tid']}"
            if e["kind"] == "enter":
                ledger[key] = {"sym": e["sym"], "qty": NOTIONAL / float(ref) * (1 if e["side"] > 0 else -1),
                               "lane": e["lane"], "entered": session, "px": e["px"]}
            elif key in ledger:
                ledger.pop(key)
            else:
                continue                                           # an exit of a trade never taken (downtime)
            touched.setdefault(e["sym"], set()).add(e["exec"])
        out = []
        fut_ok = self.futures_live()
        for sym, how in sorted(touched.items()):
            net = sum(x["qty"] for x in ledger.values() if x["sym"] == sym)
            moc = "moc" in how
            fut = sym in INDEX_FUT
            why = f"milkman {self.rule} net {net:+.6f} on {sym}"
            if fut and not fut_ok:
                out.append(Intent("signal", sym, reason=why + " (futures lane: no quoted futures venue on this desk)",
                                  signal_key=f"{sym}:{session}:{round(net, 6)}", meta={"net": net}))
                continue
            out.append(Intent("target", sym, side="long" if net >= 0 else "short", qty=abs(net),
                              price_hint=float(refs[sym]),
                              signal_key=f"{sym}:{session}:{'moc' if moc else 'mkt'}:{round(net, 6)}", reason=why,
                              order=OrderSpec(type="market", tif="cls") if moc else OrderSpec(window_s=900),
                              venue="sim:alpaca_equity" if fut else ""))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def _active(S):
    per = S.get("period") or {}
    return bool(S.get("open") or S.get("boxes") or S.get("next_open") or
                (per.get("finite") and not per.get("decided")) or (per.get("armed") and not per.get("entered")))


def _period_decided(S, session):
    """a Golden Gate period its first gate touch has decided, running past `session`: the study decides a period once
    and enters it once (dstrats.gg_trade's done_period), so its record stays to the period's last session; dropped,
    the next session's first look would open the same period again"""
    per = S.get("period") or {}
    return bool(per.get("decided") and per.get("last") and per["last"] > session)


# --------------------------------------------------------------------------------------------- feeds
def feed_bars(f, s, now, arg):
    """daily bars per set, shared by the milkman daily sleeves in a pass."""
    if arg == "index":
        return f.hub.bars("yahoo", "1d", list(INDEX_ETF + INDEX_FUT), 9000)
    return f.hub.bars("equity_split", "1d", list(V.univ_symbols()), 1000, cache_only=True)


def feed_quotes(f, s, now, arg):
    """the quotes this sleeve's pass needs: Yahoo for the index set (consolidated day high / low / volume: the full
    per-symbol quote, as Yahoo's batched quote carries no day OHLCV), the desk's equity source for the univ set."""
    plan = s.quote_plan(now) if hasattr(s, "quote_plan") else {}
    out = {}
    if plan.get("index"):
        out["index"] = f.hub.quotes("yahoo", plan["index"], full=True)
    if plan.get("univ"):
        out["univ"] = f.hub.quotes(f.hub.resolve("equity"), plan["univ"])
    return out


def sleeves():
    return [s for r in ORDER for s in (side_sleeves(r) if r in SPLIT else [MilkmanDaily(r)])] + \
        [crypto_sleeve(), legends_day_sleeve()]
