"""Muse week family ("muse_week"): the owner's install set of 2026-10-25 ("I want you to add the new 12 sleeves"),
all twelve, vendored byte for byte in desk/sleeves/muse/ (PROVENANCE.json). Ten come from the muse-desk-v3 roster
(dwj9ddyvf6-hub/Silicon muse-desk-v3 @0fc22aaa, config/sleeves.json), shen_fade from Femto-lean
stopped-checkout-20261024 @5b93f313 (in no roster), trullas_divergence (owner 2026-10-27, DEC-01 "Install Trullas")
from dwj9ddyvf6-hub/Test @fe6b8123 (in no roster; its build report names slice $10,000, RTH, 60 s). raschke_pf3 and
raschke_rre are two different systems.

Contract. Each strategy is the femto-lean contract  signal(bars, slice_state, context) -> [core.sleeve.Intent]  of
its own vendored core (desk/sleeves/muse/core/sleeve.py). Every pass this adapter hands a sleeve exactly the
context.extra keys its own file reads, from the desk's doors:

  bars_5m_long / bars_1m / bars_1m_long / bars_daily   Alpaca SIP bars (alpaca_split: split-adjusted, otherwise
              raw; intraday volume is SIP's), all hours as the hub stores them; "rth" rows are cut to the regular
              session (09:30 to the close), from the window's first whole session: saty_gpt_v03 labels every
              observation "regular" and raschke_rre needs a complete 09:30-close grid for its prior-session
              reference (both refuse extended-hours bars); saty_gpt_v02's own normalizer drops every bar outside
              the session, so the cut hands it the same observations (it reads its bar step off its first two rows,
              hence the whole first session). The free-plan SIP door ends 16 minutes before now
              (desk/data/providers.py).
  trullas_state (trullas_divergence only) the sleeve's own state (pending setup, plan, day counters) as it stamped
              it on the instance last pass: carried in the sleeve's private journal, a deep copy handed in each pass.
              Its bars arrive as the `bars` argument ({"QQQ": 1-minute rows}, the source adapter's shape; the strategy
              cuts the regular session itself), its position as {"QQQ": signed qty}, from the first row of the
              third-latest ET date on (ANCHORED): the strategy keeps bar INDEXES in its state (pivot pairs, the
              30-bar expiry), so a window that slid by a bar each minute would shift them; this one moves only at
              the session boundary, where the strategy's own state resets with the day.
  vix_series  [(date, close)] of completed ^VIX sessions (Yahoo daily: the one Yahoo use the data law allows)
  latest_quote {SYM: {bp, ap, t, received_at}}: IEX top of book read at the sleeve's own turn (at most
              QUOTE_MAX_AGE_S old), t = the quote's own time (the sleeves' freshness gates judge it)
  chains / fresh_quotes / quotes   the desk's option chain (desk/data/options.py: Alpaca indicative, else CBOE
              delayed), at most CHAIN_MAX_AGE_S old: rows, {OCC: {bp, ap, t, received_at}} with each row's own
              quote time, {OCC: {bid, ask}} for the chain and the held contracts
  oi_by_strike (em_1587, filed context only) per-strike open interest within 35 days, when the chain carries it
  session_fills  this sleeve's own fills of the session (OMS children), as {position_intent, qty, price, symbol,
              side, ts}
  sleeve_state {SYM: {"position": {...}}} from the sleeve's own book (qty signed; occ for a contract, keyed by its
              underlying; entry_px; fill_t; signal_date)
  <journal>   the durable journal the sleeve stamped on last_evaluation last pass (sol_journal, sol0_journal,
              gpt_v02_journal, gpt_v03_journal, gpf3_journal, rre_journal; shen_fade's state_out as shen_state),
              persisted in the sleeve's private state

Intents. The sleeves name an option contract either as the intent symbol (shen_fade) or, as their docstrings say,
as "occ=<OCC>" in the reason with the underlying as the symbol (the femto-lean options door, bilbo_options C-1b): the
contract is read from there with a strict OCC pattern and must belong to the intent's underlying; an option intent
without a resolvable contract is recorded as a signal, never sent. buy_to_open / sell_to_close are long-option
orders, buy_to_open / sell_to_open / *_to_close equity orders. Quantities are the sleeves' own (an intent without
one is recorded, never defaulted). limit_price -> a DAY limit (an entry works until the session's close, the
sleeves' DAY-order semantics; shen_fade's ladder until its own 180 s cancel); none -> marketable (equities) / market
(options). One order slot per sleeve symbol and action (_convert_all): a changed exit instruction replaces the
working exit in the same pass; an entry re-sent for the same contract, side and quantity is the working order; one
for another contract withdraws the working entry and is sent once the slot is free (never two working entries).
Intent.stop / Intent.target are never engine stops: every one of these
sleeves evaluates its own stops in its own code (raschke_pf3 GP-5, raschke_rre's quote-triggered exits, the saty
family's close rules); they ride the child's meta. Roster rows with flat_by_close (saty_day, saty_sol_0dte,
po10_qqq: flatten_time_et 15:55) get an engine expire_at rule on every entry (15:55 ET; the close - 5 minutes on an
early close) and no new entry from then on. Each change of a sleeve's stamped state (state / stood_down) is
recorded once as an observation, so a blocked sleeve says why on the ledger.

The slice, as v3 ran it. Sizing equity is the roster row's fixed slice capital (v3 desk3/bridge.py:111 hands
context.equity = slice capital_usd), never the book's compounding equity. Entries pass v3's per-slice buying-power
gate (desk3/dispatcher.py:75-90, _bp_gate): cost = (limit_price or price_hint or the newest bar close the sleeve was
handed for that symbol) x qty; an entry whose cost exceeds the slice's cash (the sleeve's own book cash) less its
open reservations is recorded as not sent, "insufficient_slice_bp", one with no price as "no_price_for_bp"; an
accepted entry reserves cost x (1 + bp_buffer_frac, 0.02) until its order fills or ends (while it works, only its
unfilled part stays reserved: the filled part has left the book's cash). As in v3 (line 75), exits and sell-side
entries (sell_to_open) are not checked. The one divergence: an option's cost is its real notional (premium x qty x
100); v3 multiplied premium by contracts only.

Named divergences: the pass clock (view.now, the pass's start) is every sleeve's decision clock; a pass that takes
longer than 60 s evaluates each sleeve once per pass. v3 rebuilt its slices every cycle (desk3/cycle.py:161-164:
cash = the slice capital, no reservation carried over); here the slice's cash is the book's and a reservation lasts
until its order fills or ends. v3's desk-layer entry filters (desk3/enhance14) are not part of the strategy files and
are not applied."""
import copy
import json
import math
import os
import re
from datetime import datetime, time as dtime, timezone

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...data.options import occ_parse, underlying_of
from ...util import ET, et_date, short_hash
from .. import muse as M

FAMILY = "muse_week"
PROVENANCE = json.load(open(os.path.join(M.HERE, "PROVENANCE.json")))
OCC_RE = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
OCC_IN_REASON = re.compile(r"occ=([A-Z]{1,6}\d{6}[CP]\d{8})(?![0-9A-Z])")
QUOTE_MAX_AGE_S = 2.0          # the underlying quote is read at the sleeve's own turn (saty_gpt_v02/v03 gate at 5 s)
CHAIN_MAX_AGE_S = 20.0         # the options sleeves gate contract quotes at 60 s of their own time
BAR_SOURCE = "alpaca_split"    # Alpaca SIP, split-adjusted (= raw for SPY / QQQ / IWM in these windows)
OI_DTE = 35                    # em_1587 DC-7: the OI window (expiries within 35 days)
BP_BUFFER_FRAC = 0.02          # v3 desk3/dispatcher.py:24 default (every roster row carries 0.02)
OPTION_MULTIPLIER = 100.0      # an option's cost is premium x contracts x 100 (v3: premium x contracts)
ALL, RTH, ANCHORED = "all", "rth", "anchored"
ANCHOR_DATES = 3                # ANCHORED: today and the two sessions before it

# the v3 roster rows of record (config/sleeves.json @0fc22aaa), verbatim; shen_fade has none
V3 = {"repo": "dwj9ddyvf6-hub/Silicon", "ref": "muse-desk-v3", "commit": "0fc22aaaf1009385d736148b45776f6abc471939",
      "path": "config/sleeves.json", "blob": "03db72662220c501c67f86a5efa821b201549caf",
      "sha256": "ddfd5850c939cb943b16787e9242adfdab0f21c3e206391444724e4d70579527"}


def _row(module, capital, flat, inputs, **kw):
    r = {"module": module, "cadence_s": 60, "session": "rth",
         "slice": {"capital_usd": float(capital), "cash_usd": float(capital)}, "bp_buffer_frac": 0.02,
         "flat_by_close": bool(flat), "flatten_time_et": "15:55" if flat else None, "params": {},
         "inputs": list(inputs), "parked": False}
    r.update(kw)
    return r


ROSTER = {
    "saty_day": _row("saty_day", 10_000, True, ["bars_5min", "bars_1min", "positions", "options_chains",
                                                "options_quotes", "session_fills"], timeout_s=None,
                     adapter_dir="desk_sleeves"),
    "saty_sol": _row("adapters3.saty_sol", 10_000, False, ["bars", "quotes", "options", "session_fills"],
                     timeout_s=None),
    "saty_sol_0dte": _row("adapters3.saty_sol_0dte", 10_000, True, ["bars", "quotes", "options", "session_fills"],
                          timeout_s=None),
    "po10_qqq": _row("desk3.port_b5.po10_qqq", 100_000, True, ["bars", "positions", "quotes", "session_fills"]),
    "em_1587": _row("adapters3.em_1587", 10_000, False, ["bars", "positions", "options", "extra"]),
    "saty_magnum": _row("adapters3.saty_magnum", 10_000, False, ["bars", "quotes", "options", "session_fills"],
                        timeout_s=None),
    "saty_gpt_v03": _row("adapters3.saty_gpt_v03", 10_000, False, ["bars", "quotes", "options", "session_fills"],
                         timeout_s=None),
    "saty_gpt_v02": _row("adapters3.saty_gpt_v02", 10_000, False, ["bars", "quotes", "options", "session_fills"],
                         timeout_s=None),
    "raschke_pf3": _row("desk3.port_b5.raschke_pf3", 10_000, False, ["bars", "positions", "journal"]),
    "raschke_rre": _row("raschke_rre", 10_000, False, ["bars_5min", "positions", "session_fills", "latest_quotes"],
                        timeout_s=None, adapter_dir="desk_sleeves"),
}

# what each strategy file reads (its own code), and from which door. bars rows: (interval, symbols, n, session, key)
SPECS = {
    "saty_day": {"trades": "SPY options, same-day expiry", "kind": "option",
                 "bars": [("5m", ("SPY", "QQQ"), 22000, ALL, "bars_5m_long"),     # ATR Levels warm at 100 sessions
                          ("1m", ("SPY", "QQQ"), 1200, ALL, "bars_1m")],
                 "quotes": ("SPY", "QQQ"), "options": ("SPY", 0, 0)},
    "saty_sol": {"trades": "SPY options, 2-4 calendar days to expiry", "kind": "option",
                 "bars": [("5m", ("SPY",), 22000, ALL, "bars_5m_long"), ("1m", ("SPY",), 1200, ALL, "bars_1m")],
                 "quotes": ("SPY",), "options": ("SPY", 0, 7), "journal": "sol_journal"},
    "saty_sol_0dte": {"trades": "SPY options, same-day expiry", "kind": "option",
                      "bars": [("5m", ("SPY",), 22000, ALL, "bars_5m_long"), ("1m", ("SPY",), 1200, ALL, "bars_1m")],
                      "quotes": ("SPY",), "options": ("SPY", 0, 0), "journal": "sol0_journal"},
    "po10_qqq": {"trades": "QQQ shares, long and short", "kind": "equity",
                 "bars": [("5m", ("QQQ",), 4000, ALL, "bars_5m_long")], "quotes": ("QQQ",)},
    "em_1587": {"trades": "SPY options, same-day expiry", "kind": "option",
                "bars": [("5m", ("SPY", "QQQ"), 4000, ALL, "bars_5m_long")], "quotes": ("SPY",),
                "options": ("SPY", 0, 0), "vix": True, "oi": True},
    "saty_magnum": {"trades": "SPY shares, long and short", "kind": "equity",
                    "bars": [("5m", ("SPY",), 52000, ALL, "bars_5m_long"),       # the daily Pro ribbon warms at 250
                             ("1m", ("SPY",), 1200, ALL, "bars_1m")],
                    "quotes": ("SPY",), "vix": True},
    "shen_fade": {"trades": "SPY options, same-day expiry", "kind": "option", "capital": 10_000.0,
                  "bars": [("1m", ("SPY",), 2400, ALL, "bars_1m_long")], "options": ("SPY", 0, 0),
                  "state_key": "shen_state", "ladder_s": 180.0},
    "saty_gpt_v03": {"trades": "SPY shares, long and short", "kind": "equity",
                     "bars": [("5m", ("SPY", "QQQ", "IWM"), 34000, RTH, "bars_5m_long"),   # 1000 1H bars: ~170 sessions
                              ("1d", ("SPY",), 200, ALL, "bars_daily")],
                     "quotes": ("SPY",), "journal": "gpt_v03_journal", "daily_arg": True},
    "saty_gpt_v02": {"trades": "SPY shares, long and short", "kind": "equity",
                     "bars": [("5m", ("SPY",), 34000, RTH, "bars_5m_long"), ("1d", ("SPY",), 200, ALL, "bars_daily")],
                     "quotes": ("SPY",), "journal": "gpt_v02_journal", "daily_arg": True},
    "raschke_pf3": {"trades": "SPY shares, long and short", "kind": "equity",
                    "bars": [("5m", ("SPY",), 4000, ALL, "bars_5m_long")], "journal": "gpf3_journal"},
    "raschke_rre": {"trades": "SPY shares (long; its admission refuses shorts)", "kind": "equity",
                    "bars": [("5m", ("SPY",), 5000, RTH, "bars_5m_long")], "quotes": ("SPY",),
                    "journal": "rre_journal"},
    # Test @fe6b8123, in no roster: slice $10,000 (its build report TRULLAS-SLEEVE-BUILD), RTH, 60 s, parked=False.
    # The source sizes itself whole (units x 0.25% x equity / stop distance, 25% notional cap), so no default is used.
    "trullas_divergence": {"trades": "QQQ shares, long and short", "kind": "equity", "capital": 10_000.0,
                           "bars": [("1m", ("QQQ",), 6000, ANCHORED, "bars_1m_long")],
                           "journal": "trullas_state", "journal_attr": "trullas_state",
                           "bars_arg": ("QQQ", "bars_1m_long"), "qty_state": True},
}
NOT_INSTALLED = {}             # the owner's twelve are all installed


def _iso(ts):
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def _num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _rth(bars):
    """the bars of the regular session (start in [09:30, the close) ET of a trading day), from the first session open
    in the window on: a window cut inside a session would start the series on a partial session (saty_gpt_v02 reads
    its bar step off the first two rows)"""
    out = []
    for b in bars or []:
        t = float(b["t"])
        d = cal._as_date(t)
        if cal.is_trading_day(d) and cal.session_open(d) <= t < cal.session_close(d):
            out.append(b)
    for i, b in enumerate(out):
        if float(b["t"]) == cal.session_open(cal._as_date(float(b["t"]))):
            return out[i:]
    return []


def flatten_at(session):
    """flatten_time_et 15:55 of a flat_by_close row: 15:55 ET on a full session, the close - 5 minutes on an early
    close (15:55 lies after a 13:00 close)."""
    d = cal._as_date(session)
    full = datetime.combine(d, dtime(15, 55), ET).timestamp()
    return min(full, cal.session_close(d) - 300)


def _anchored(bars, dates=ANCHOR_DATES):
    """the rows from the first row of the `dates`-th latest ET date on: a window that starts on a session boundary and
    moves only when a new session begins (trullas_divergence keeps bar indexes in its state)"""
    days = sorted({et_date(float(b["t"])) for b in bars or []})
    if len(days) <= dates:
        return list(bars or [])
    first = days[-dates]
    return [b for b in bars if et_date(float(b["t"])) >= first]


def _jsonable(x):
    try:
        return json.loads(json.dumps(x, allow_nan=False))
    except (TypeError, ValueError):
        return None


class MuseSleeve(Sleeve):
    def __init__(self, name, spec):
        self.name = name
        self.spec = spec
        self.mod = M.strategy_module(name)
        self.cls = next(v for v in vars(self.mod).values()
                        if isinstance(v, type) and v.__module__ == self.mod.__name__ and hasattr(v, "signal"))
        roster = ROSTER.get(name)
        capital = float(roster["slice"]["capital_usd"]) if roster else float(spec["capital"])
        path = "sleeves/%s.py" % name
        prov = PROVENANCE["files"][path]
        needs = {"bars": [{"source": BAR_SOURCE, "interval": iv, "n": int(n), "symbols": list(syms)}
                          for iv, syms, n, _s, _k in spec["bars"]], "feeds": []}
        if spec.get("vix"):
            needs["bars"].append({"source": "yahoo", "interval": "1d", "n": 40, "symbols": ["^VIX"], "key": "vix"})
        self.CONFIG = SleeveConfig(
            sleeve_id="muse_" + name, family=FAMILY, cadence_s=int(roster["cadence_s"] if roster else
                                                                 self.mod.CONFIG.cadence_s),
            universe=tuple(dict.fromkeys(s for _iv, syms, _n, _s, _k in spec["bars"] for s in syms)),
            capital=capital, needs=needs, schedule="rth",
            params={"strategy_id": self.mod.CONFIG.sleeve_id, "trades": spec["trades"], "kind": spec["kind"],
                    "flatten_time_et": (roster or {}).get("flatten_time_et"),
                    "flat_by_close": bool((roster or {}).get("flat_by_close")),
                    "journal": spec.get("journal") or spec.get("state_key"),
                    "options": list(spec["options"]) if spec.get("options") else None,
                    "quotes": list(spec.get("quotes") or ()), "roster_row": roster},
            source={"repo": prov["repo"], "ref": prov["ref"], "commit": prov["commit"], "path": path,
                    "blob": prov["git_blob"], "sha256": prov["sha256"], "roster": V3 if roster else None},
            status="active")
        self.engine = None
        self._last = None

    def bind(self, engine):
        self.engine = engine

    # -- doors ------------------------------------------------------------------------------------------------
    def _hub(self):
        return getattr(self.engine, "hub", None)

    def _bars_extra(self, view):
        extra, daily = {}, None
        for iv, syms, n, sess, key in self.spec["bars"]:
            got = (view.bars or {}).get(iv) or {}
            rows = {}
            for s in syms:
                bl = list(got.get(s) or [])[-int(n):]
                if sess == RTH:
                    bl = _rth(bl)
                elif sess == ANCHORED:
                    bl = _anchored(bl)
                if bl:
                    rows[s] = bl
            extra[key] = rows
            if iv == "1d":
                daily = rows
        if self.spec.get("vix"):
            series = []
            for b in (view.extra.get("bars_vix") or {}).get("^VIX") or []:
                c = _num(b.get("c"))
                if c is not None:
                    series.append((et_date(float(b["t"])), c))
            extra["vix_series"] = series
        return extra, daily

    def _latest_quotes(self, view):
        syms = list(self.spec.get("quotes") or ())
        hub = self._hub()
        if not syms or hub is None:
            return {}
        try:
            got = hub.quotes("alpaca", syms, max_age=QUOTE_MAX_AGE_S) or {}
        except Exception:
            return {}
        out = {}
        for s in syms:
            q = got.get(s) or {}
            bid, ask, t = _num(q.get("bid")), _num(q.get("ask")), _num(q.get("t"))
            if bid and ask and t:
                out[s] = {"symbol": s, "bp": bid, "ap": ask, "t": _iso(t),
                          "received_at": _iso(q.get("_at") or t), "last": _num(q.get("last"))}
        return out

    def _options(self, view, held_occs):
        und, lo, hi = self.spec["options"]
        opts = getattr(self._hub(), "options", None)
        out = {"chains": {und: []}, "fresh_quotes": {}, "quotes": {}}
        if opts is None:
            return out
        try:
            rows = opts.chain(und, dte_min=lo, dte_max=hi, now=view.now, max_age=CHAIN_MAX_AGE_S) or []
        except Exception:
            rows = []
        at = opts.received_at(und) if hasattr(opts, "received_at") else None
        for r in rows:
            occ = r.get("symbol")
            if not occ:
                continue
            out["chains"][und].append({k: r.get(k) for k in ("symbol", "underlying", "expiration", "type", "strike",
                                                             "bid", "ask", "last", "delta", "iv", "t", "source")})
            bid, ask = _num(r.get("bid")), _num(r.get("ask"))
            if bid is not None and ask is not None:
                out["quotes"][occ] = {"bid": bid, "ask": ask}
                if r.get("t"):
                    out["fresh_quotes"][occ] = {"symbol": occ, "bp": bid, "ap": ask, "t": _iso(r["t"]),
                                                "received_at": _iso(at or r["t"]), "source": r.get("source")}
        missing = [o for o in held_occs if o not in out["quotes"]]
        if missing:
            try:
                for occ, q in (opts.quotes(missing) or {}).items():
                    bid, ask = _num(q.get("bid")), _num(q.get("ask"))
                    if bid is not None and ask is not None:
                        out["quotes"][occ] = {"bid": bid, "ask": ask}
                        if q.get("t"):
                            out["fresh_quotes"][occ] = {"symbol": occ, "bp": bid, "ap": ask, "t": _iso(q["t"]),
                                                        "received_at": _iso(q["t"]), "source": q.get("source")}
            except Exception:
                pass
        if self.spec.get("oi"):
            try:
                oi_rows = opts.chain(und, dte_min=0, dte_max=OI_DTE, now=view.now, max_age=CHAIN_MAX_AGE_S) or []
            except Exception:
                oi_rows = []
            oi = {}
            for r in oi_rows:
                v = _num(r.get("oi"))
                if v is None:
                    continue
                k = oi.setdefault(float(r["strike"]), {"call": 0.0, "put": 0.0, "total": 0.0})
                k["call" if r.get("type") == "call" else "put"] += v
                k["total"] += v
            if oi:
                out["oi_by_strike"] = oi
        return out

    def _session_fills(self, view):
        """this sleeve's own fills of the session, from its OMS children (None without an engine: unverifiable)"""
        oms = getattr(self.engine, "oms", None)
        if oms is None:
            return None
        out = []
        for c in (oms.s.get("children") or {}).values():
            if c.get("sleeve") != self.CONFIG.sleeve_id:
                continue
            kind, sym = c["inst"].split(":", 1)
            opening = c.get("action") != "exit"
            buy = c.get("side") == "buy"
            pi = ("buy_to_open" if buy else "sell_to_open") if opening else ("buy_to_close" if buy else "sell_to_close")
            if c.get("action") == "target":          # a target child is opening when it moves away from flat
                pi = "buy_to_open" if buy else "sell_to_close"
            for ts, dv, px, *_rest in c.get("fills") or []:
                if et_date(float(ts)) != view.session:
                    continue
                out.append({"position_intent": pi, "qty": float(dv), "price": float(px), "symbol": sym,
                            "submit_symbol": sym, "side": c.get("side"), "ts": datetime.fromtimestamp(
                                float(ts), tz=ET).isoformat(), "inst": c["inst"]})
        out.sort(key=lambda f: f["ts"])
        return out

    def _sleeve_state(self, view):
        st = {}
        for inst, p in sorted((view.positions or {}).items()):
            kind, sym = inst.split(":", 1)
            q = float(p.get("qty") or 0.0)
            if not q:
                continue
            opened = float(p.get("opened_at") or view.now)
            pm = dict((p.get("meta") or {}).get("position_meta") or {})
            pos = {"symbol": sym, "qty": q, "entry_px": float(p["avg"]), "avg_price": float(p["avg"]),
                   "fill_t": opened, "entry_t": opened, "entry_date": et_date(opened),
                   "signal_date": pm.get("signal_date") or et_date(opened),
                   "opened_at": datetime.fromtimestamp(opened, tz=ET).isoformat()}
            if kind == "OPT":
                pos.update(occ=sym, entry_premium=float(p["avg"]))
                st.setdefault(underlying_of(sym), {"position": pos})
            st[sym] = {"position": pos}
        return st

    # -- the pass -----------------------------------------------------------------------------------------------
    def signal(self, view):
        private = view.state or {}
        extra, daily = self._bars_extra(view)
        held_occs = [i.split(":", 1)[1] for i in (view.positions or {}) if i.startswith("OPT:")]
        lq = self._latest_quotes(view)
        if self.spec.get("quotes"):
            extra["latest_quote"] = lq
        if self.spec.get("options"):
            extra.update(self._options(view, held_occs))
        fills = self._session_fills(view)
        extra["session_fills"] = fills
        sstate = self._sleeve_state(view)
        extra["sleeve_state"] = sstate
        jkey = self.spec.get("journal") or self.spec.get("state_key")
        if jkey and isinstance(private.get("journal"), dict):
            extra[jkey] = (copy.deepcopy(private["journal"]) if self.spec.get("journal_attr")
                           else private["journal"])           # a strategy that edits its state in place keeps ours
        CS = M.core_module("sleeve")
        ctx = CS.Context(now=float(view.now), session=view.session, equity=float(self.CONFIG.capital),
                         market=dict(view.market or {}), extra=extra)     # v3: the fixed slice capital
        inst = self.cls()
        bars = {"SPY": (daily or {}).get("SPY") or []} if self.spec.get("daily_arg") else {}
        if self.spec.get("bars_arg"):                         # trullas_divergence: the strategy reads the bars itself
            sym, key = self.spec["bars_arg"]
            bars = {sym: list(extra[key].get(sym) or [])}
        if self.spec.get("qty_state"):                        # ... and its position as {symbol: signed qty}
            sstate = {s: v["position"]["qty"] for s, v in sstate.items()}
        out = list(inst.signal(bars, sstate, ctx) or [])
        stamp = getattr(inst, "last_evaluation", None) or {}
        if self.spec.get("journal_attr"):                     # the state lives on the instance, not in the stamp
            stamp = dict(stamp, **{jkey: _jsonable(getattr(inst, self.spec["journal_attr"], None))})
        bp = self._bp_open(private, view)
        intents, slots, notes = self._convert_all(out, view, private, stamp, bp)
        intents += self._observe(stamp, view)
        self._last = {"stamp": stamp, "slots": slots, "notes": notes, "jkey": jkey, "out": out, "bp": bp}
        return intents

    def _observe(self, stamp, view):
        """one observation per change of the stamped state (the engine records a signal key once per 6 h)"""
        state = str(stamp.get("state") or "")
        why = str(stamp.get("stood_down") or "")
        if not state and not why:
            return []
        sym = self.CONFIG.universe[0]
        reason = "%s state=%s%s%s" % (self.name, state or "-", (" stood_down=" + why) if why else "",
                                      (" decision=" + str(stamp.get("decision"))[:160]) if stamp.get("decision") else "")
        return [Intent("signal", sym, reason=reason[:300], signal_key=f"{sym}:{view.session}:state:"
                       f"{short_hash(state, why, n=10)}", meta={"muse_state": state, "stood_down": why})]

    def update_state(self, view, intents):
        last = self._last or {}
        private = dict(view.state or {})
        stamp = last.get("stamp") or {}
        jkey = last.get("jkey")
        if jkey:
            src = stamp.get("state_out") if jkey == "shen_state" else stamp.get(jkey)
            if isinstance(src, dict):
                j = _jsonable(src)
                if j is None:
                    private["journal_error"] = {"at": view.now, "why": "journal is not JSON (kept the previous one)"}
                else:
                    private["journal"] = j
                    private.pop("journal_error", None)
        private["slots"] = last.get("slots") or {}
        if "bp" in last:
            private["bp"] = last["bp"]
        private["last"] = {"session": view.session, "at": view.now, "state": stamp.get("state"),
                           "stood_down": stamp.get("stood_down"), "decision": _jsonable(stamp.get("decision")),
                           "notes": last.get("notes") or []}
        return private

    # -- intents ------------------------------------------------------------------------------------------------
    def _refused(self, view, why, reason, detail=""):
        sym = self.CONFIG.universe[0]
        text = "not sent: %s%s | %s" % (why, " (%s)" % detail if detail else "", reason)
        return Intent("signal", sym, reason=text[:300],
                      signal_key=f"{sym}:{view.session}:refused:{short_hash(why, reason, n=10)}")

    # -- the slice's buying power (v3 desk3/dispatcher.py:75-90) -------------------------------------------------
    def _bp_open(self, private, view):
        """the slice's reservations still open: an accepted entry's reservation lasts while its order works in the OMS
        (pending_orders), less the part that has filled (it has left the book's cash), and is released when the order
        fills or ends (filled, expired, cancelled, or never placed)"""
        live = {(o.get("inst"), o.get("signal_key")): o for o in ((view.extra or {}).get("pending_orders") or [])}
        held = {}
        for key, r in ((private.get("bp") or {}).get("reserved") or {}).items():
            o = live.get((r.get("inst"), key))
            vq = float((o or {}).get("vqty") or 0.0)
            left = max(0.0, vq - float(o.get("filled_v") or 0.0)) / vq if o is not None and vq > 0 else 0.0
            if left > 0:
                held[key] = dict(r, hold=round(float(r["full"]) * left, 6))
        return {"reserved": held}

    def _price_lookup(self, symbol, view):
        """v3's price lookup (desk3/cycle.py:277 _price_from: the symbol's last bar close): the newest bar close the
        sleeve was handed for the symbol; None for a symbol without bars (an option contract, as on v3)"""
        best = None
        tapes = list((view.bars or {}).values()) + [v for k, v in (view.extra or {}).items()
                                                    if k.startswith("bars_") and isinstance(v, dict)]
        for by_sym in tapes:
            bl = by_sym.get(symbol) or []
            if bl and (best is None or float(bl[-1]["t"]) > float(best["t"])):
                best = bl[-1]
        return _num(best.get("c")) if best else None

    def _bp_gate(self, it, conv, view, bp):
        """v3's slice check of an entry -> (refusal or None, detail, reservation or None): a sell is checked as an exit
        (line 75: never refused, nothing reserved); price = limit_price or price_hint or the lookup (no price:
        no_price_for_bp); cost = price x qty (x 100 for an option: real notional, the one divergence from v3);
        refused when cost > the slice's cash less its open reservations (insufficient_slice_bp); else reserved at
        cost x (1 + bp_buffer_frac)"""
        if conv.asset == "equity" and conv.side == "short":
            return None, "", None
        price = _num(it.limit_price) or _num(it.price_hint) or self._price_lookup(conv.symbol, view)
        if price is None:
            return "no_price_for_bp", "", None
        cost = price * float(conv.qty) * (OPTION_MULTIPLIER if conv.asset == "option" else 1.0)
        available = float(view.cash or 0.0) - sum(float(r["hold"]) for r in bp["reserved"].values())
        if cost > available:
            return "insufficient_slice_bp", "cost %.2f > available %.2f" % (cost, available), None
        full = cost * (1.0 + float((ROSTER.get(self.name) or {}).get("bp_buffer_frac", BP_BUFFER_FRAC)))
        inst = ("OPT:" if conv.asset == "option" else "EQ:") + conv.symbol
        return None, "", {"inst": inst, "cost": round(cost, 6), "full": round(full, 6), "hold": round(full, 6),
                          "qty": float(conv.qty), "at": float(view.now), "session": view.session}

    def _convert_all(self, out, view, private, stamp=None, bp=None):
        """the sleeve's intents as contract intents, one order slot per (action, sleeve symbol):
          exit   a changed instruction (contract, quantity, limit or reason) cancels the working exit and places the
                 new one in the same pass (an exit never closes more than the book holds: OMS _fit_exit);
          enter  while the slot's entry still works, the same contract / side / quantity keeps that order (its first
                 limit works as a DAY order, the sleeves' own order model); another contract / side / quantity cancels
                 it and is placed on a later pass once the slot is free (never two working entries: a resting entry
                 can fill at the cycle's sync in the very pass a replacement is sent); an entry to be placed passes
                 the slice's buying-power gate first (_bp_gate; bp: the open reservations, which it extends)."""
        bp = self._bp_open(private, view) if bp is None else bp
        slots = {k: v for k, v in (private.get("slots") or {}).items() if v.get("session") == view.session}
        live = {(o.get("inst"), o.get("signal_key")) for o in (view.extra.get("pending_orders") or [])}
        roster = ROSTER.get(self.name) or {}
        flat_t = flatten_at(view.session) if roster.get("flat_by_close") else None
        res, notes = [], []
        for it in out:
            conv, why = self._convert(it, view, flat_t, stamp or {})
            if conv is None:
                notes.append(why)
                res.append(self._refused(view, why, it.reason))
                continue
            slot = f"{it.kind}:{it.symbol}"
            lim = conv.order.limit_price if conv.order else None
            same = short_hash(conv.symbol, conv.side, conv.qty, n=16)
            sig = short_hash(same, lim, conv.order.type if conv.order else None, it.reason, n=16)
            prev = slots.get(slot)
            prev_inst = None
            if prev:
                prev_inst = ("OPT:" if prev["asset"] == "option" else "EQ:") + prev["symbol"]
            prev_live = bool(prev) and (prev_inst, prev["key"]) in live
            key = f"{conv.symbol}:{view.session}:{it.kind}:{sig}"
            if it.kind == "enter" and prev_live:
                if prev.get("same") == same:
                    continue                                  # the working entry is this instruction's order
                res.append(Intent("cancel", prev["symbol"], asset=prev["asset"], signal_key=prev["key"],
                                  reason=f"{self.name}: the sleeve now names another entry; this one is withdrawn"))
                notes.append("entry deferred until the withdrawn order is gone")
                res.append(self._refused(view, "deferred one pass: the slot's working entry is withdrawn first",
                                         it.reason))
                continue
            if prev and prev.get("sig") == sig:
                key = prev["key"]
            elif prev and it.kind == "exit":
                res.append(Intent("cancel", prev["symbol"], asset=prev["asset"], signal_key=prev["key"],
                                  reason=f"{self.name}: replaced by the sleeve's new exit instruction"))
            if it.kind == "enter":
                why, detail, hold = self._bp_gate(it, conv, view, bp)
                if why:
                    notes.append(why)
                    res.append(self._refused(view, why, it.reason, detail))
                    continue
                if hold is not None:
                    bp["reserved"][key] = hold
            slots[slot] = {"session": view.session, "symbol": conv.symbol, "asset": conv.asset, "key": key,
                           "sig": sig, "same": same}
            res.append(Intent(conv.kind, conv.symbol, side=conv.side, asset=conv.asset, qty=conv.qty,
                              price_hint=conv.price_hint, exit_rules=conv.exit_rules, order=conv.order,
                              signal_key=key, reason=conv.reason, meta=conv.meta))
        return res, slots, notes

    def _contract(self, it):
        """(OCC or None, why): the contract an option intent names"""
        if OCC_RE.match(it.symbol or ""):
            return it.symbol, None
        m = OCC_IN_REASON.findall(it.reason or "")
        if not m:
            return None, None
        if len(set(m)) > 1:
            return None, "two contracts named in one intent"
        occ = m[0]
        try:
            if underlying_of(occ) != it.symbol:
                return None, f"contract {occ} is not on {it.symbol}"
            occ_parse(occ)
        except (ValueError, IndexError):
            return None, f"unparseable contract {occ}"
        return occ, None

    def _entry_deadline(self, it, occ, stamp, close):
        """when an entry stops working: the session's close (a DAY order), or a sleeve's own cancel time (shen_fade
        R-12: its working ladder is cancelled 180 s after the first limit)"""
        if self.spec.get("ladder_s"):
            w = ((stamp.get("state_out") or {}).get("working") or {})
            if w.get("occ") == occ and _num(w.get("since_ts")) is not None:
                end = float(w["since_ts"]) + float(self.spec["ladder_s"])
                return min(end, close) if close else end
        return close

    def _convert(self, it, view, flat_t, stamp):
        """(contract Intent, None) or (None, why it is not sent)"""
        qty = it.qty if it.qty is not None else it.qty_hint
        if qty is None or not float(qty) > 0:
            return None, "no quantity"
        if it.legs:
            return None, "multi-leg intents are not part of these sleeves' contract"
        occ, bad = self._contract(it)
        if bad:
            return None, bad
        pi = it.position_intent or ""
        lp = _num(it.limit_price)
        meta = {"muse": {"strategy": self.name, "position_intent": pi or None, "sleeve_stop": it.stop,
                         "sleeve_target": it.target, "sleeve_price_hint": it.price_hint},
                "position_meta": {"signal_date": it.signal_date or view.session}}
        close = cal.session_close(view.session) if cal.is_trading_day(view.session) else None
        if it.kind == "enter":
            if flat_t is not None and float(view.now) >= flat_t:
                return None, "entry at/after the row's flatten time 15:55 ET"
            rules = (ExitRule("expire_at", float(flat_t)),) if flat_t is not None else ()
            if occ is not None or self.spec["kind"] == "option":
                if occ is None:
                    return None, "option entry without a contract"
                if pi and pi != "buy_to_open":
                    return None, f"option entry {pi} is not a long-option open"
                meta["underlying"] = underlying_of(occ)
                until = self._entry_deadline(it, occ, stamp, close)
                order = OrderSpec(type="limit", limit_price=lp, tif="day", not_after=until) if lp \
                    else OrderSpec(type="market", tif="day", not_after=until)
                return Intent("enter", occ, side="long", asset="option", qty=float(qty), price_hint=lp,
                              exit_rules=rules, order=order, reason=it.reason[:300], meta=meta), None
            side = "short" if (pi == "sell_to_open" or (not pi and it.side == "sell")) else "long"
            order = OrderSpec(type="limit", limit_price=lp, tif="day", not_after=close) if lp \
                else OrderSpec(type="marketable_limit", tif="day", not_after=close)
            return Intent("enter", it.symbol, side=side, asset="equity", qty=float(qty),
                          price_hint=_num(it.price_hint) or lp, exit_rules=rules, order=order, reason=it.reason[:300],
                          meta=meta), None
        # exit
        inst = ("OPT:" + occ) if occ else ("EQ:" + it.symbol)
        held = float(((view.positions or {}).get(inst) or {}).get("qty") or 0.0)
        if not held:
            return None, f"exit of {inst.split(':', 1)[1]}, which this book does not hold"
        if occ is not None:
            meta["underlying"] = underlying_of(occ)
            order = OrderSpec(type="limit", limit_price=lp, tif="day", not_after=close) if lp \
                else OrderSpec(type="market", tif="day")
            return Intent("exit", occ, side="long" if held > 0 else "short", asset="option",
                          qty=min(float(qty), abs(held)), price_hint=lp, order=order, reason=it.reason[:300],
                          meta=meta), None
        order = OrderSpec(type="limit", limit_price=lp, tif="day", not_after=close) if lp \
            else OrderSpec(type="marketable_limit", tif="day", not_after=close)
        return Intent("exit", it.symbol, side="long" if held > 0 else "short", asset="equity",
                      qty=min(float(qty), abs(held)), price_hint=_num(it.price_hint) or lp, order=order,
                      reason=it.reason[:300], meta=meta), None


def sleeves():
    return [MuseSleeve(name, spec) for name, spec in SPECS.items()]
