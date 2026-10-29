"""Femto-lean family: the 60 vendored sleeves (desk/sleeves/femto/) on the master desk.

The femto contract is  signal(bars, slice_state, context) -> [femto Intent].  This module replaces the femto
dispatcher, which (a) submitted every entry as a BUY of intent.symbol — so put-spread, short and option
signals bought the underlying — and (b) supplied no feeds and no position state, so most sleeves sat inert.

Per sleeve, a SPEC row (femto_specs.py) states what the sleeve's own docstring names: universe, primary bars,
schedule, the context.extra keys and the ONE producer of each, which femto exit rules the engine executes,
capital and status. Every pass the adapter hands the sleeve:

  bars          completed bars of the primary series {SYM: [{"t","o","h","l","c","v"}, ...]}
  slice_state   {SYM: signed qty} of the sleeve's own virtual book
  context       now / session (ET date) / the sleeve's virtual equity / desk market / extra
  sleeve_state  rebuilt from the book every pass: {SYM: {"position": {qty, entry_px (average fill),
                entry_date (fill session), stop_px, exit_submitted, + the position_meta its entry declared},
                "pending_entry", "last_exit_date", + per-symbol private state}}

Intents become contract intents with structure as data (side, asset, venue, legs). The femto core executed
exactly one exit rule itself — the stop (a GTC disaster stop placed on fill); that stays an engine stop.
Targets, time and trailing exits stay inside the sleeve's own signal() unless its spec delegates them."""
import importlib
import inspect
import json
import math
import os

from ...contract import ExitRule, Intent, Leg, OrderSpec, Sleeve, SleeveConfig
from ...data.options import underlying_of
from ...feedlib.discovery import load_family_universe
from ... import calendar as cal
from ...util import ET, et_date, short_hash
from ...venues.sim import iex_near
from ..femto import compat as fc

HERE = os.path.dirname(os.path.abspath(__file__))
PROVENANCE = json.load(open(os.path.join(HERE, "..", "femto", "PROVENANCE.json")))
DEFAULT_RISK_PCT = 0.0025            # femto core/risk.py reference value
INTERVAL_H = {"1m": 1 / 60, "3m": 0.05, "5m": 1 / 12, "15m": 0.25, "30m": 0.5, "1h": 1.0, "4h": 4.0}


def size_by_risk(equity, entry, stop, risk_pct=DEFAULT_RISK_PCT):
    """femto core/risk.py size_by_risk, verbatim arithmetic (whole shares risked between entry and stop)."""
    per = float(entry) - float(stop)
    if per <= 0:
        raise ValueError("stop must be below entry for a long")
    return int((float(equity) * risk_pct) // per)


def _num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _whole(q):
    return int(q) if abs(q - round(q)) < 1e-9 else q


class FemtoSleeve(Sleeve):
    def __init__(self, name, spec):
        self.name = name
        self.spec = spec
        self.mod = importlib.import_module("desk.sleeves.femto." + name)
        self.fcfg = self.mod.CONFIG
        fcg = self.fcfg
        universe = tuple(spec.get("universe") or fcg.universe)
        needs = {"bars": [], "feeds": []}
        b = spec.get("bars")
        if b:
            needs["bars"].append({"source": b[0], "interval": b[1], "n": int(b[2]),
                                  **({"symbols": list(spec["data_symbols"])} if spec.get("data_symbols") else {}),
                                  **({"cache_only": True} if spec.get("cache_only") else {}),
                                  **({"symbols_for": spec["symbols_for"]} if spec.get("symbols_for") else {})})
        for key, eb in (spec.get("extra_bars") or {}).items():
            if not isinstance(eb, dict):                 # (source, interval, n[, symbols])
                eb = dict(zip(("source", "interval", "n", "symbols"), eb))
            row = {"source": eb["source"], "interval": eb["interval"], "n": int(eb["n"]), "key": key}
            if eb.get("symbols"):
                row["symbols"] = list(eb["symbols"])
            if eb.get("cache_only"):
                row["cache_only"] = True
            if eb.get("symbols_for"):
                row["symbols_for"] = eb["symbols_for"]
            needs["bars"].append(row)
        for prod in (spec.get("extra") or {}).values():
            if isinstance(prod, str) and prod.startswith("feed:"):
                needs["feeds"].append(prod[5:])
        if spec.get("quotes"):
            needs["quotes"] = spec["quotes"]
        prov = PROVENANCE["files"].get(name + ".py", {})
        self.CONFIG = SleeveConfig(
            sleeve_id="femto_" + name, family="femto", cadence_s=int(spec.get("cadence_s", fcg.cadence_s)),
            universe=universe, capital=float(spec.get("capital", 100_000.0)), needs=needs,
            schedule=spec.get("schedule", "always"), state_schema={},
            params={"femto_id": fcg.sleeve_id, "risk_pct": fcg.risk_pct, "parked": fcg.parked,
                    "cost_bps": spec.get("cost_bps"), "engine_rules": sorted(spec.get("engine_rules", ("stop",))),
                    **({"margin_rate": float(spec["margin_rate"])} if spec.get("margin_rate") else {})},
            source={"repo": PROVENANCE["repo"], "commit": PROVENANCE["commit"], "path": prov.get("source_path"),
                    "blob": prov.get("source_blob"), "vendored_blob": prov.get("vendored_blob"),
                    "transforms": prov.get("transforms"), "old_desk": spec.get("old_desk")},
            status=spec.get("status", "active"), venue_pref=spec.get("venue", ""))
        self._last = None
        self.cache_dir = None
        self.engine = None

    def bind(self, engine):
        self.cache_dir = os.path.join(engine.root, "cache")
        self.engine = engine

    def universe_now(self, now, book=None):
        """the static universe, or (spec "family") the old desk's weekly family watchlist with the static
        universe as its fallback; symbols the sleeve holds are always appended (a position is never
        stranded by a watchlist change — the old runner only managed symbols still in its universe)."""
        base = list(self.CONFIG.universe)
        fam = self.spec.get("family")
        if fam and self.cache_dir:
            base, self.universe_source = load_family_universe(os.path.join(self.cache_dir, "family_watchlists.json"),
                                                              fam, base, now)
        held = [self._femto_symbol(i, p.get("meta")) for i, p in ((book.positions.items()) if book else [])]
        dmap = self.spec.get("data_symbols") or {}
        return [dmap.get(x, x) for x in dict.fromkeys(base + [h for h in held if h not in base])]

    def _meta(self):
        if self.engine is None:
            return {}
        return (self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}).get("meta") or {}

    def bar_symbols(self, need, now, book=None):
        """the symbols of a declared need this pass (its "symbols_for"): "held" = the names the sleeve holds;
        "watch" = the names its meta lists for this session (meta.watch {date, symbols}); "held+watch";
        "screen" = the whole universe until the sleeve has screened this session (meta.screened), re-read no
        sooner than meta.screen_retry_at — a genome screen loads once, the session's passes load only what
        they trade."""
        mode = need.get("symbols_for")
        if mode == "screen":
            meta = self._meta()
            due = meta.get("screened") != et_date(now) and now >= float(meta.get("screen_retry_at") or 0)
            return list(self.universe_now(now, book)) if due else []
        if mode not in ("held", "watch", "held+watch"):
            return None
        held = [self._femto_symbol(i, p.get("meta")) for i, p in ((book.positions.items()) if book else [])]
        w = self._meta().get("watch") or {}
        watch = list(w.get("symbols") or []) if w.get("date") == et_date(now) else []
        syms = {"held": held, "watch": watch, "held+watch": held + watch}[mode]
        dmap = self.spec.get("data_symbols") or {}
        return [dmap.get(x, x) for x in dict.fromkeys(syms)]

    def quote_universe(self, now, book=None):
        """quotes only for what can trade this pass (spec quotes_for "pending": held names + the persisted
        pending buys/sells; "held" / "watch" / "held+watch" as bar_symbols) — a genome-scale sleeve never
        quotes its whole universe."""
        qf = self.spec.get("quotes_for")
        if qf in ("held", "watch", "held+watch"):
            return self.bar_symbols({"symbols_for": qf}, now, book)
        if qf != "pending":
            return self.universe_now(now, book)
        held = [self._femto_symbol(i, p.get("meta")) for i, p in ((book.positions.items()) if book else [])]
        st = {}
        if self.engine is not None:
            st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}
        pend = ((st.get("meta") or {}).get("pending") or {})
        return list(dict.fromkeys(held + list(pend.get("buys") or []) + list(pend.get("sells") or [])))

    # -- symbol / instrument mapping ---------------------------------------------------------------------
    def _asset(self):
        return self.spec.get("asset", "equity")

    def _trade_symbol(self, fsym):
        return (self.spec.get("trade_symbols") or {}).get(fsym, fsym)

    def _femto_symbol(self, inst, meta=None):
        meta = meta or {}
        if meta.get("femto_symbol"):
            return meta["femto_symbol"]
        kind, rest = inst.split(":", 1)
        sym = rest.split(":", 1)[0] if kind == "MLEG" else rest.split(":")[-1]   # MLEG:<underlying>:<group>
        if kind == "OPT":
            return underlying_of(sym)
        rev = {v: k for k, v in (self.spec.get("trade_symbols") or {}).items()}
        return rev.get(sym, sym)

    # -- inputs ---------------------------------------------------------------------------------------------
    def _primary_bars(self, view):
        b = self.spec.get("bars")
        if not b:
            return {}
        got = (view.bars.get(b[1]) or {})
        dmap = self.spec.get("data_symbols") or {}
        if dmap:
            rev = {v: k for k, v in dmap.items()}
            return {rev.get(s, s): bl for s, bl in got.items() if bl}
        return {s: bl for s, bl in got.items() if bl}

    def _by_symbol(self, view):
        out = {}
        for inst, p in view.positions.items():
            out.setdefault(self._femto_symbol(inst, p.get("meta")), []).append((inst, p))
        return out

    def _slice_state(self, view):
        out = {}
        for fsym, items in self._by_symbol(view).items():
            if len(items) == 1:
                out[fsym] = _whole(float(items[0][1]["qty"]))
            else:                                   # a spread: its unit count, signed by the first leg
                out[fsym] = _whole(self._group_units(items))
        return out

    @staticmethod
    def _group_units(items):
        for inst, p in items:
            r = float((p.get("meta") or {}).get("leg_ratio") or 1)
            return abs(float(p["qty"])) / r
        return 0.0

    def _sleeve_state(self, view, private):
        ss = {s: dict(v) for s, v in (private.get("symbols") or {}).items() if isinstance(v, dict)}
        pend = view.extra.get("pending_orders") or []
        for fsym, items in self._by_symbol(view).items():
            meta = dict(items[0][1].get("meta") or {})
            pm = dict(meta.get("position_meta") or {})
            if len(items) == 1:
                inst, p = items[0]
                q = float(p["qty"])
                pos = {"qty": _whole(q), "entry_px": float(p["avg"]),
                       "entry_date": et_date(float(p.get("opened_at") or view.now)), "stop_px": _stop_of(meta),
                       "target_px": meta.get("target"), "opened_at": float(p.get("opened_at") or view.now)}
                if inst.startswith("OPT:"):
                    pos["occ"] = inst.split(":", 1)[1]
                    pos["contracts"] = _whole(abs(q))
            else:
                units = self._group_units(items)
                net = sum(float(p["avg"]) * (1 if float(p["qty"]) > 0 else -1) *
                          float((p.get("meta") or {}).get("leg_ratio") or 1) for _, p in items)
                opened = min(float(p.get("opened_at") or view.now) for _, p in items)
                pos = {"qty": _whole(units), "entry_date": et_date(opened), "stop_px": None, "net_entry": net,
                       "opened_at": opened,
                       "legs": {inst.split(":", 1)[1]: _whole(float(p["qty"])) for inst, p in items}}
            for k, v in pm.items():
                pos.setdefault(k, v)
            for k, src in (self.spec.get("fill_fields") or {}).items():      # declared fields that are fills
                if src == "avg" and "entry_px" in pos:
                    pos[k] = pos["entry_px"]
                elif src == "net_debit" and "net_entry" in pos:
                    pos[k] = round(pos["net_entry"], 4)
                elif src == "net_credit" and "net_entry" in pos:
                    pos[k] = round(-pos["net_entry"], 4)
            insts = {i for i, _ in items}
            pos["exit_submitted"] = any(o["action"] in ("exit", "target") and (
                o["inst"] in insts or (o["inst"].startswith("MLEG:") and self._femto_symbol(o["inst"]) == fsym))
                for o in pend) or None                       # a package exit works on its underlying's legs
            st = ss.setdefault(fsym, {})
            pos.update(st.pop("pos", None) or {})            # the sleeve's own later position updates (e.g. tranche 2 done)
            st["position"] = pos
        for o in pend:                                   # entries in flight count as positions (old semantics)
            if o["action"] == "enter":
                fsym = self._femto_symbol(o["inst"])
                st = ss.setdefault(fsym, {})
                if not st.get("position"):
                    st["pending_entry"] = {"qty": o["vqty"], "filled": o["filled_v"], "key": o.get("signal_key"),
                                           "ref_px": o.get("ref")}
        for fsym, d in self._last_exits(view).items():
            st = ss.setdefault(fsym, {})
            if not st.get("position"):
                st["last_exit_date"] = max(d, str(st.get("last_exit_date") or ""))
        for fsym, st in ss.items():
            st.setdefault("position", None)
            if st["position"] is None:
                st.pop("pos", None)                          # overrides die with the position
        return ss

    def _last_exits(self, view):
        out = {}
        for t in view.extra.get("closed_trades") or []:
            fsym = self._femto_symbol(t["inst"])
            d = et_date(float(t["closed_at"]))
            if d > out.get(fsym, ""):
                out[fsym] = d
        return out

    def _extra(self, view, private, bars, ss):
        extra = {"sleeve_state": ss}
        u = list(self.CONFIG.universe)
        for key, prod in (self.spec.get("extra") or {}).items():
            if callable(prod):
                val = prod(self, view, private, bars)
            elif isinstance(prod, str) and prod.startswith("feed:"):
                val = view.extra.get(prod[5:])
            elif isinstance(prod, str) and prod.startswith("@"):
                val = self._builtin(prod[1:], view, private, u)
            else:
                val = prod
            if val is not None:
                extra[key] = val
        return extra

    def _builtin(self, what, view, private, universe):
        name, _, arg = what.partition(":")
        if name == "universe":
            dmap = {v: k for k, v in (self.spec.get("data_symbols") or {}).items()}
            return [dmap.get(x, x) for x in self.universe_now(view.now, _BookView(view))]
        if name == "meta":
            return private.get("meta") or {}
        if name == "state":
            return private.get(arg) if arg in private else (self.spec.get("state_defaults") or {}).get(arg)
        if name == "bars":
            got = view.extra.get("bars_" + arg) or {}
            eb = (self.spec.get("extra_bars") or {}).get(arg)
            if isinstance(eb, dict) and (eb.get("since_days") or eb.get("rth_grid")):
                got = {s: _trim(bl, view.now, eb.get("since_days"), eb.get("rth_grid")) for s, bl in got.items()}
            dmap = {v: k for k, v in (self.spec.get("data_symbols") or {}).items()}
            return {dmap.get(s, s): bl for s, bl in got.items()}
        if name == "quotes":                        # @quotes:near — a US equity priced as the engine marks it
            rows = {s: _quote_row(q) for s, q in (view.quotes or {}).items()}
            return {s: _near_row(r) for s, r in rows.items()} if arg == "near" else rows
        if name == "forming":                       # today's forming daily bar {o, c, v} (old SIP forming bar)
            # read per symbol on first access: a quote that carries the session's OHLCV (Alpaca snapshots) serves
            # it; otherwise the hub's full quote of that symbol is fetched then — so a sleeve that looks at three
            # names of a 48-name universe costs three requests, not 48 (the batched quotes carry no day OHLCV)
            from ...data.options import LazyMap
            hub = getattr(self.engine, "hub", None)
            src = hub.resolve((self.spec.get("quotes") or {}).get("source", "equity")) if hub is not None else None
            quotes = view.quotes or {}

            def one(sym):
                q = quotes.get(sym)
                if (not q or q.get("day_open") is None) and hub is not None:
                    try:
                        q = hub.quotes(src, [sym], full=True).get(sym) or q
                    except Exception:                # an unreachable source: no forming bar (fail closed)
                        pass
                return _forming_row(q, view.session)
            return LazyMap(one)
        if name == "marks":                         # fresh intraday marks (old: last 5-min close <= 30 min old)
            out = {}
            for sym, q in (view.quotes or {}).items():
                bid, ask, last = _num(q.get("bid")), _num(q.get("ask")), _num(q.get("last"))
                t = _num(q.get("t"))
                if t is not None and view.now - t > 1800:
                    continue
                if self._asset() == "equity" and bid and ask and not iex_near(bid, ask):
                    bid = ask = None                # a wide IEX book's mid is no price: its last print is (6aa70ba)
                px = (bid + ask) / 2 if bid and ask and ask >= bid else last
                if px:
                    out[sym] = px
            return out
        if name == "chain":                         # option chain rows: @chain:UNDERLYING[:DTEMIN-DTEMAX[:put|call]]
            parts = arg.split(":")
            lo = hi = typ = None
            if len(parts) > 1 and parts[1]:
                lo, hi = (int(x) for x in parts[1].split("-"))
            if len(parts) > 2 and parts[2]:
                typ = parts[2]
            opts = getattr(getattr(self.engine, "hub", None), "options", None)
            if opts is None:
                return None
            rows = opts.chain(parts[0], dte_min=lo, dte_max=hi, typ=typ, now=view.now)
            return {parts[0]: rows} if rows is not None else None
        if name == "chains":                        # lazy chains for any underlying: @chains:DTEMIN-DTEMAX[:put|call]
            parts = arg.split(":")
            lo, hi = (int(x) for x in parts[0].split("-")) if parts and parts[0] else (None, None)
            typ = parts[1] if len(parts) > 1 and parts[1] else None
            opts = getattr(getattr(self.engine, "hub", None), "options", None)
            if opts is None:
                return None
            from ...data.options import LazyMap
            now = view.now
            return LazyMap(lambda u: opts.chain(u, dte_min=lo, dte_max=hi, typ=typ, now=now))
        if name == "option_quotes":                 # live quotes for the sleeve's option legs (+ meta-named ones)
            opts = getattr(getattr(self.engine, "hub", None), "options", None)
            occs = [i.split(":", 1)[1] for i in view.positions if i.startswith("OPT:")]
            occs += [o for o in ((private.get("meta") or {}).get("watch_occs") or []) if o not in occs]
            return opts.quotes(occs) if (opts is not None and occs) else {}
        if name == "quote":
            sym = arg or (universe[0] if universe else None)
            q = (view.quotes or {}).get(sym)
            return _quote_row(q) if q else None
        if name == "broker_qty":                    # the sleeve's own virtual book is its broker view
            held = self._slice_state(view)
            return {s: held.get(s, 0) for s in universe}
        if name == "foreign_holders":
            return {}
        if name == "held_qty":
            sym = arg or (universe[0] if universe else None)
            return abs(float(self._slice_state(view).get(sym, 0) or 0))
        if name in ("cash", "buying_power"):
            return float(view.cash)
        if name == "equity":
            return float(view.equity)
        if name == "closed_trades":                  # the sleeve's own closed trades, with the exit's reason
            out = []
            for t in view.extra.get("closed_trades") or []:
                r = str(t.get("reason") or "")
                kind = "disaster_stop" if r.startswith("stop") else r.split(":")[0].strip() or "exit"
                out.append({"symbol": self._femto_symbol(t["inst"]), "pnl": t.get("pnl"), "ret": t.get("ret"),
                            "closed_at": t.get("closed_at"), "reason": kind, "detail": r[:120],
                            "signal_key": t.get("signal_key") or ""})
            return out
        raise ValueError(f"unknown femto builtin @{what}")

    # -- the pass -----------------------------------------------------------------------------------------
    def signal(self, view):
        private = view.state or {}
        bars = self._primary_bars(view)
        ss = self._sleeve_state(view, private)
        extra = self._extra(view, private, bars, ss)
        ctx = fc.Context(now=view.now, session=view.session, equity=float(view.equity), market=dict(view.market or {}),
                         extra=extra)
        out = list(self.mod.signal(bars, self._slice_state(view), ctx) or [])
        self._last = {"out": out, "bars": bars, "extra": extra, "ctx": ctx}
        intents = []
        for fi in out:
            intents += self._convert(fi, view, bars, ss)
        if hasattr(self.mod, "stop_levels"):        # a sleeve-computed trail: the engine holds it as the stop (ratchet)
            for sym, px in (self.mod.stop_levels(bars, self._slice_state(view), ctx) or {}).items():
                intents.append(Intent("adjust", self._trade_symbol(sym), asset=self._asset(), stop=float(px),
                                      reason=f"trail stop {float(px):.4f}", meta={"ratchet": True, "femto_symbol": sym}))
        if hasattr(self.mod, "exit_levels"):        # sleeve-moved engine stop/target (e.g. a refreshed take-profit)
            for sym, lv in (self.mod.exit_levels(bars, self._slice_state(view), ctx) or {}).items():
                stop, target = lv.get("stop"), lv.get("target")
                intents.append(Intent("adjust", self._trade_symbol(sym), asset=self._asset(),
                                      stop=None if stop is None else float(stop),
                                      target=None if target is None else float(target),
                                      reason=lv.get("reason") or "levels stop=%s target=%s" % (stop, target),
                                      meta={"ratchet": bool(lv.get("ratchet")), "femto_symbol": sym}))
        mon = self.spec.get("monitor")
        if mon is not None:
            for sym, reason, meta in mon(self.mod, bars, ctx) or []:
                intents.append(Intent("signal", sym, reason=reason[:300], meta=meta or {},
                                      signal_key=f"{sym}:{view.session}:{short_hash(reason, n=8)}"))
        return intents

    def update_state(self, view, intents):
        private = dict(view.state or {})
        last = self._last or {}
        syms = dict(private.get("symbols") or {})
        for fi in last.get("out") or []:
            if fi.state:
                syms[fi.symbol] = dict(syms.get(fi.symbol) or {}, **fi.state)
        held = set(self._by_symbol(view))
        for sym in list(syms):
            if "pos" in syms[sym] and sym not in held and not any(
                    fi.symbol == sym and fi.kind == "enter" for fi in last.get("out") or []):
                syms[sym] = {k: v for k, v in syms[sym].items() if k != "pos"}
        if syms:
            private["symbols"] = syms
        if hasattr(self.mod, "next_meta") and last.get("ctx") is not None:   # a sleeve's own sleeve-level stamps
            args = (last["bars"], self._slice_state(view), last["ctx"])
            if len(inspect.signature(self.mod.next_meta).parameters) >= 4:
                args += (last.get("out") or [],)
            private["meta"] = self.mod.next_meta(*args)
        if hasattr(self.mod, "next_symbol_state") and last.get("ctx") is not None:   # per-symbol bookkeeping
            upd = self.mod.next_symbol_state(last["bars"], self._slice_state(view), last["ctx"], last.get("out") or [])
            syms = dict(private.get("symbols") or {})
            for sym, d in (upd or {}).items():
                syms[sym] = dict(syms.get(sym) or {}, **d)
            private["symbols"] = syms
        hook = self.spec.get("state_hook")
        if hook is not None:
            private = hook(self, view, private, last) or private
        return private

    # -- femto intent -> contract intents ---------------------------------------------------------------
    def _rules(self, fi, interval):
        allow = set(self.spec.get("engine_rules", ("stop",)))
        out = []
        for r in fi.exit_rules:
            if r.kind not in allow:
                continue
            if r.kind in ("stop", "target"):
                out.append(ExitRule(r.kind, float(r.value)))
            elif r.kind == "trailing_pct" and r.value > 0:
                out.append(ExitRule("trailing_pct", float(r.value)))
            elif r.kind == "stop_dist" and r.value > 0:          # measured from the actual fill
                out.append(ExitRule("stop_dist", float(r.value)))
            elif r.kind == "time_bars" and r.value > 0:
                if interval in ("1d", None):
                    out.append(ExitRule("time_sessions", float(r.value)))
                elif interval == "1w":
                    out.append(ExitRule("time_sessions", float(r.value) * 5))
                else:
                    out.append(ExitRule("time_hours", float(r.value) * INTERVAL_H.get(interval, 1.0)))
        return tuple(out)

    def _order(self, fi, now=None):
        o = dict(self.spec.get("order") or {})
        o.update(fi.order or {})
        if fi.kind == "enter" and self.spec.get("entry_window") == "session" and now is not None \
                and "not_after" not in o:
            o["not_after"] = _fill_session_close(now)    # a daily decision waits for (only) its fill session
        if fi.net_price is not None and "limit_price" not in o:
            o["limit_price"] = float(fi.net_price)
            o["type"] = "limit"
        return OrderSpec(**o) if o else None

    def _convert(self, fi, view, bars, ss):
        out = self._convert1(fi, view, bars, ss)
        fn = self.spec.get("cost_bps_fn")
        if fn is not None:
            for it in out:
                px = it.price_hint or fi.price_hint
                if px and it.kind in ("enter", "exit"):
                    it.meta["cost_bps"] = float(fn(float(px)))
        return out

    def _convert1(self, fi, view, bars, ss):
        sid = self.CONFIG.sleeve_id
        interval = (self.spec.get("bars") or (None, None))[1]
        if fi.kind == "exit":
            return self._convert_exit(fi, view)
        if fi.kind == "cancel":                     # withdraw a working entry (e.g. a resting buy-stop)
            return [Intent("cancel", self._trade_symbol(fi.symbol), asset=fi.asset or self._asset(),
                           signal_key=fi.signal_key or "", reason=fi.reason, meta={"femto_symbol": fi.symbol})]
        if self.fcfg.parked:
            return [Intent("signal", fi.symbol, reason=("entry_parked: " + fi.reason)[:300],
                           signal_key=f"{fi.symbol}:{view.session}:parked")]
        asset = fi.asset or self._asset()
        side = fi.side or "long"
        meta = {"femto_symbol": fi.symbol, "position_meta": dict(fi.position_meta or {})}
        key = fi.signal_key or f"{fi.symbol}:{view.session}:enter"
        qty = fi.qty if fi.qty is not None else (float(fi.qty_hint) if fi.qty_hint else None)
        if qty is None:                             # femto core: the sleeve's referenced sizing formula
            px = fi.price_hint or (float(bars[fi.symbol][-1]["c"]) if bars.get(fi.symbol) else None)
            if not px:
                return [Intent("signal", fi.symbol, reason="entry_no_price: " + fi.reason[:280], signal_key=key)]
            ref_stop = fi.stop if fi.stop is not None else px * 0.95
            try:
                qty = float(size_by_risk(view.equity, px, ref_stop, self.fcfg.risk_pct or DEFAULT_RISK_PCT))
            except ValueError:
                qty = 0.0
            if qty <= 0:
                return [Intent("signal", fi.symbol, reason="entry_no_qty: " + fi.reason[:280], signal_key=key)]
        stop_px = fi.stop if fi.stop is not None else next((float(r.value) for r in fi.exit_rules if r.kind == "stop"), None)
        meta["position_meta"].setdefault("stop_px", stop_px)
        if asset == "mleg":
            legs = tuple(Leg(l["symbol"], l["side"], int(l.get("ratio", 1)), l.get("position_intent", ""))
                         for l in fi.legs)
            group = f"{sid}:{fi.symbol}:{short_hash(view.session, *[l.symbol for l in legs], n=10)}"
            meta.update(group=group, underlying=fi.symbol)
            return [Intent("enter", fi.symbol, side="long", asset="mleg", qty=qty, legs=legs, order=self._order(fi),
                           price_hint=fi.price_hint, signal_key=key, reason=fi.reason, meta=meta)]
        if asset == "option":
            occ = fi.legs[0]["symbol"] if fi.legs else fi.symbol
            opt_side = side
            if fi.legs:
                opt_side = "short" if fi.legs[0]["side"] == "sell" else "long"
            meta["underlying"] = underlying_of(occ)
            return [Intent("enter", occ, side=opt_side, asset="option", venue=fi.venue or "", qty=qty,
                           order=self._order(fi), price_hint=fi.price_hint if fi.symbol == occ else None,
                           signal_key=key, reason=fi.reason, meta=meta)]
        tsym = self._trade_symbol(fi.symbol)
        order = self._order(fi, view.now)
        rules = tuple(r for r in self._rules(fi, interval) if r.kind != "stop")
        stop = stop_px if "stop" in self.spec.get("engine_rules", ("stop",)) else None
        if self.spec.get("stop_pct") and stop is not None:      # disaster stop measured from the actual fill
            rules, stop = rules + (ExitRule("stop_pct", float(self.spec["stop_pct"])),), None
        target = fi.target if (fi.target is not None and "target" in self.spec.get("engine_rules", ("stop",))) else None
        if target is not None:                                  # an adjustable engine target (meta), never a static rule
            rules = tuple(r for r in rules if r.kind != "target")
        if self.spec.get("target_pct") and target is not None:  # a take-profit measured from the actual fill
            rules, target = rules + (ExitRule("target_pct", float(self.spec["target_pct"])),), None
        return [Intent("enter", tsym, side=side, asset=asset, venue=fi.venue or self.spec.get("venue", ""), qty=qty,
                       notional=fi.notional if qty is None else None, price_hint=fi.price_hint, stop=stop,
                       target=target, exit_rules=rules, order=order, signal_key=key, reason=fi.reason, meta=meta)]

    def _convert_exit(self, fi, view):
        items = self._by_symbol(view).get(fi.symbol) or []
        if fi.legs:                                 # close exactly these held contracts (several: one package)
            want = {"OPT:" + l["symbol"] for l in fi.legs}
            items = [it for it in items if it[0] in want]
        key = fi.signal_key or f"{fi.symbol}:{view.session}:exit"
        if not items:
            return []                               # femto core: exit_skipped (no slice qty)
        if len(items) > 1 or (items[0][1].get("meta") or {}).get("group"):
            meta0 = items[0][1].get("meta") or {}
            group = meta0.get("group")
            units = self._group_units(items)
            q = min(units, float(fi.qty_hint)) if fi.qty_hint else units
            legs = []
            for inst, p in items:
                r = int(float((p.get("meta") or {}).get("leg_ratio") or 1))
                long = float(p["qty"]) > 0
                legs.append(Leg(inst.split(":", 1)[1], "sell" if long else "buy", r,
                                "sell_to_close" if long else "buy_to_close"))
            if len(legs) == 1:                      # a one-leg group closes as a plain option order
                inst, p = items[0]
                long = float(p["qty"]) > 0
                return [Intent("exit", inst.split(":", 1)[1], side="long" if long else "short", asset="option",
                               qty=min(abs(float(p["qty"])), q), signal_key=key, reason=fi.reason,
                               meta={"femto_symbol": fi.symbol})]
            return [Intent("exit", meta0.get("underlying") or fi.symbol, asset="mleg", qty=q, legs=tuple(legs),
                           order=self._order(fi, view.now),
                           signal_key=key if group or not fi.legs else f"{key}:{short_hash(*sorted(l.symbol for l in legs), n=8)}",
                           reason=fi.reason,
                           meta={"group": group, "underlying": meta0.get("underlying"), "femto_symbol": fi.symbol})]
        inst, p = items[0]
        kind, rest = inst.split(":", 1)
        held = abs(float(p["qty"]))
        q = min(held, float(fi.qty if fi.qty is not None else (fi.qty_hint or held)))
        asset = {"EQ": "equity", "CR": "crypto", "OPT": "option", "PERP": "perp", "SPOT": "spot"}[kind]
        venue = fi.venue or ""                      # an exit may name its venue (a leg entered on a pinned sim venue)
        sym = rest
        if kind in ("PERP", "SPOT"):
            v, sym = rest.split(":", 1)
            venue = "sim:" + v.lower()
        return [Intent("exit", sym, side="long" if float(p["qty"]) > 0 else "short", asset=asset, venue=venue, qty=q,
                       order=self._order(fi, view.now), price_hint=fi.price_hint, signal_key=key, reason=fi.reason,
                       meta={"femto_symbol": fi.symbol})]


def _trim(bars, now, since_days=None, rth_grid=False):
    """old sleeve_core 1H conventions: bars since (today - since_days) 00:00Z, and the RTH grid = bar starts at
    09..15 ET (rth_1h_bars)."""
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    out = bars or []
    if since_days:
        d0 = _dt.fromtimestamp(now, tz=ET).date() - _td(days=int(since_days))
        start = _dt(d0.year, d0.month, d0.day, tzinfo=_tz.utc).timestamp()
        out = [b for b in out if float(b["t"]) >= start]
    if rth_grid:
        out = [b for b in out if 9 <= _dt.fromtimestamp(float(b["t"]), tz=ET).hour <= 15]
    return out


def _fill_session_close(now):
    """the close of the session an order placed now can still fill in: today's if before today's close on a
    trading day, else the next trading day's."""
    d = cal._as_date(now)
    if cal.is_trading_day(d) and now < cal.session_close(d):
        return cal.session_close(d)
    return cal.session_close(cal.next_trading_day(d))


class _BookView:
    """positions of a View in the shape universe_now() reads."""

    def __init__(self, view):
        self.positions = view.positions


def _stop_of(meta):
    if meta.get("stop") is not None:
        return meta["stop"]
    for kind, val in meta.get("exit_rules") or []:
        if kind == "stop":
            return val
    return (meta.get("position_meta") or {}).get("stop_px")


def _forming_row(q, session):
    """a quote with the session's OHLCV -> the forming daily bar {o, h, l, c, v}; None off-session or unknown."""
    if not q or str(q.get("day_date") or q.get("session") or "")[:10] != session:
        return None
    o, c, v = _num(q.get("day_open")), _num(q.get("last") or q.get("day_close")), _num(q.get("day_volume"))
    if not (o and c):
        return None
    h, lo = _num(q.get("day_high")), _num(q.get("day_low"))
    return {"o": o, "c": c, "v": v or 0.0, "h": max(x for x in (h, o, c) if x is not None),
            "l": min(x for x in (lo, o, c) if x is not None)}


def _quote_row(q):
    """hub quote -> the femto quote shape (both spellings the ports read)."""
    if not q:
        return None
    bid, ask = _num(q.get("bid")), _num(q.get("ask"))
    return {"bid": bid, "ask": ask, "bp": bid, "ap": ask, "last": _num(q.get("last")), "t": q.get("t"),
            "as_of": q.get("t"), "received_at": q.get("_at")}


def _near_row(r):
    """a US equity quote row as the engine marks it (Engine._mark, 6aa70ba): IEX's book (Alpaca's free feed) only when
    it is near the NBBO (desk/venues/sim.py iex_near), else no bid / ask, so the last print, a real trade, is the
    price. 2026-10-16: femto_tensor_red_dip sold SKYQ for its -8% stop on a 2.24 mid while the touch read 2.41 / 2.44."""
    if r and r.get("bid") and r.get("ask") and not iex_near(r["bid"], r["ask"]):
        return dict(r, bid=None, ask=None, bp=None, ap=None, wide_book=[r["bid"], r["ask"]])
    return r


def sleeves():
    return [FemtoSleeve(name, spec) for name, spec in SPECS.items() if not spec.get("disabled")]


from .femto_specs import FEEDS, JOBS, SPECS  # noqa: E402,F401  (specs are data + producers; they never import this module)
