"""Ausar public recipes (RSI2 pullback, Donchian 55 trend, BB/KC squeeze) — the vendored, hash-pinned
evaluator (desk/vendor/ausar/trader_signals.py, blob 1445d646) decides; this wrapper only carries out the
execution-manager obligations of the original Ausar trader runtime:

  * signals from completed daily bars (Yahoo, the frozen expected provider); entries and signal exits
    at the next regular opening, within 300 s (schedule open+0:open+5);
  * size = floor((min(equity*0.10, dv20*0.01, cash) - fee) / (quote*(1+10bps))), and for stop rules
    min(that, floor(equity*0.005/stop_distance)); whole shares; at most 10 names incl. pending;
  * initial stop = actual fill - 2*ATR14 (observed quote, regular session) -> ExitRule stop_dist;
  * time exit after max_hold_bars observed sessions -> ExitRule time_sessions (next open);
  * signal exits are owed (trader_runtime _rule_exits -> _owe_exit -> _exits): every completed bar while a name is
    held is assessed once, and an exit it raises is sold at each opening window until the position is flat, so a
    missed or slow opening window defers it to the next opening and never drops it."""
import math

from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...calendar import session_open
from ...util import et_date
from ...vendor.ausar import trader_signals as ts

SOURCE = {"repo": "agentic-trading-desk", "ref": "aurelia-paper-desk", "commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
          "path": "ausar-archive/ausar-receiver/original-payload/desk-source/backend/trader_signals.py",
          "blob": "1445d64653345204513b9d792a45f6f9fb0d4783"}
IDS = {ts.RSI2: "ausar_public_rsi2", ts.DONCHIAN: "ausar_public_donchian55", ts.SQUEEZE: "ausar_public_squeeze20"}


def _rows(bars):
    return [{"timestamp_ms": int(b["t"] * 1000), "open": float(b["o"]), "high": float(b["h"]), "low": float(b["l"]),
             "close": float(b["c"]), "volume": float(b["v"] or 0)} for b in bars]


class PublicRecipe(Sleeve):
    def __init__(self, rule_id):
        self.rule_id = rule_id
        cfg = ts._RULES[rule_id]
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[rule_id], family="ausar_public_recipe", cadence_s=60, universe=ts.UNIVERSE,
            needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 400}], "quotes": {"source": "equity"}},
            schedule="open+0:open+5", params={"rule_id": rule_id, "config_sha256": ts.CONFIG_SHA256[rule_id]},
            source=dict(SOURCE, catalog=cfg["name"]), state_schema={"owed": "dict", "exit_seen": "dict"})

    def owed_exits(self, view, bars, held, st):
        """{symbol: {reason, bar_ms}} owed, {symbol: last assessed bar_ms}: each completed bar from the entry session's
        on is assessed once while the name is held (the evaluator on the series up to that bar, as the source's held
        assessment saw it when that bar was the newest); an owed exit stays until the name is flat."""
        owed = {s: o for s, o in (st.get("owed") or {}).items() if s in held}
        seen = {s: t for s, t in (st.get("exit_seen") or {}).items() if s in held}
        for sym in sorted(held):
            rows = bars.get(sym) or []
            if not rows:
                continue
            entry_day = et_date(float((view.positions.get("EQ:" + sym) or {}).get("opened_at") or view.now))
            last = seen.get(sym)
            for i, r in enumerate(rows):
                if sym in owed:
                    break
                if et_date(r["timestamp_ms"] / 1000.0) < entry_day or (last is not None and r["timestamp_ms"] <= last):
                    continue
                ex = ts.evaluate(self.rule_id, {sym: rows[:i + 1]}, held_symbols={sym})["exits"]
                if ex:
                    owed[sym] = {"reason": ex[0]["reason"], "bar_ms": r["timestamp_ms"]}
            seen[sym] = rows[-1]["timestamp_ms"]
        return owed, seen

    def update_state(self, view, intents):
        return getattr(self, "_st", None)

    def signal(self, view):
        cfg = ts._RULES[self.rule_id]
        daily = view.bars.get("1d") or {}
        today_open = session_open(view.session)
        # only bars completed before today's open are causal for today's opening decision
        bars = {s: _rows([b for b in bl if b["t"] < today_open - 3600]) for s, bl in daily.items() if bl}
        held = {inst.split(":", 1)[1] for inst, p in view.positions.items() if float(p["qty"]) > 0}
        pending = {p["inst"].split(":", 1)[1] for p in view.extra.get("pending_orders", []) if p["action"] == "enter"}
        out = ts.evaluate(self.rule_id, bars, held_symbols=held)
        st = dict(view.state or {})
        owed, seen = self.owed_exits(view, bars, held, st)
        self._st = dict(st, owed=owed, exit_seen=seen)
        intents = []
        for sym in sorted(owed):
            intents.append(Intent("exit", sym, reason=f"{self.rule_id} exit: {owed[sym]['reason']}",
                                  signal_key=f"{sym}:{view.session}:exit",
                                  order=OrderSpec(window_s=300 + 60)))
        slots = len(held | pending)
        equity, cash = view.equity, view.cash
        for c in out["candidates"]:
            if slots >= cfg["max_positions"]:
                break
            sym = c["symbol"]
            q = view.quotes.get(sym) or {}
            px = q.get("ask") or q.get("last")
            if not px:
                continue
            cap = min(equity * 0.10, c["dollar_volume20"] * 0.01, max(0.0, cash))
            shares = int(cap / (float(px) * 1.001)) if cap > 0 else 0
            rules = [ExitRule("time_sessions", float(cfg["max_hold_bars"]))]
            if c["stop_distance"] is not None:
                shares = min(shares, int(equity * 0.005 / c["stop_distance"]))
                rules.append(ExitRule("stop_dist", float(c["stop_distance"])))
            if shares < 1:
                continue
            intents.append(Intent("enter", sym, qty=float(shares), price_hint=float(px), exit_rules=tuple(rules),
                                  signal_key=f"{sym}:{view.session}:entry", reason=f"{cfg['name']}: {c['reason']}",
                                  order=OrderSpec(window_s=300), meta={"rank_key": c["rank_key"], "score": c["score"]}))
            slots += 1
        return intents


def sleeves():
    return [PublicRecipe(r) for r in (ts.RSI2, ts.DONCHIAN, ts.SQUEEZE)]
