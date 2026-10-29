"""Milkman 0DTE SPX — v3-native expression of the authored sleeve.

Authored source: Femto-lean branch milkman-0dte,
desk/sleeves/families/milkman_0dte.py, vendored BYTE-EXACT at
desk3/milkman_0dte/milkman_0dte.py (sha256 202841b379c96120b6e859a4a576d76fde8b4b24f7653b57a56ce7d04be106ee;
provenance in desk3/milkman_0dte/PROVENANCE.md). This module is the
same rules on the core/sleeve.py contract, following the
trullas_divergence install pattern: pick_contract / contracts_for are
logic-identical ports of the vendored pure functions, and the pass
logic mirrors the vendored signal() decision for decision.

Rules as authored (never retuned here):
  * SPX 0DTE only: today's expiry, root SPXW or SPX, the contract
    whose |delta| is nearest 0.40 among fresh (<=180 s) two-sided
    quotes at most 20% wide; bought at the quoted ask (a limit at
    the ask), sold at the quoted bid. No model price anywhere.
  * Long premium only: a long lane buys a call, a short lane buys a
    put. $2,500 premium per trade in whole contracts (one contract if
    it costs up to 1.5 budgets), at most 4 open at once.
  * Daily stop: the book's P&L for the session reaching -$10,000
    (Milkman's own figure) flattens everything and blocks entries for
    the rest of the session.
  * No entry in the last 30 minutes; hard flat 15 minutes before the
    close. A contract held past expiry is dropped on the next
    session's first pass, logged "expired".
  * ESMON and OPX4 are not expressed.
  * INERT until the SPX 0DTE chain is proven by the probe record
    (desk3/milkman_0dte/spx_probe.py): no record, no entry, and the
    abstention names the reason "SPX 0DTE chain not available". Never
    a fallback to SPY options or to a model.

Channels (ctx.extra, built by adapters/milkman_0dte.py):
  milkman_state  the sleeve's own state dict (round-tripped)
  spx_probe      {"available", "underlying", "why"} from the probe
                 record's availability() verdict
  chain_rows     today's chain rows {symbol, root, expiration, type,
                 strike, bid, ask, delta, t} or None
  quotes         {OCC: {"bid", "ask"}} latest quotes for exits
  lane_signals   authored lane trades [{key, side}] for entries
  lane_exits     lane keys whose exit bar has fired
  book_pnl       the book's session P&L (the stop's input; the
                 authored sleeve reads it as equity-now less
                 equity-at-first-pass of its own book)

PARKED + UNFED at install (PROVENANCE gaps 1-2): the adapter leaves
lane_signals empty because the Milkman intraday study
(desk/sleeves/milkman/intraday.py) is not ported, and this account
tier's chain carries no delta, so pick_contract names "no delta" on
every live row. The strategy is pure: clock only via Context.now, no
files, no broker.
"""
from __future__ import annotations

import re
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")

SID = "mk_zerodte_spx"
CAPITAL = 1_000_000.0
DAILY_STOP = -10_000.0
PREMIUM_PER_TRADE = 2_500.0
MAX_OPEN = 4
TARGET_DELTA = 0.40
MAX_SPREAD = 0.20
QUOTE_MAX_AGE_S = 180.0
NO_ENTRY_S = 30 * 60
HARD_EXIT_S = 15 * 60
EXCLUDED = ("ESMON", "OPX4")
ROOTS = ("SPXW", "SPX")
INERT = "SPX 0DTE chain not available"

_OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")

CONFIG = SleeveConfig(
    sleeve_id=SID, cadence_s=60, universe=("SPX",),
    state_schema={"milkman_state": "dict"},
    risk_pct=None, parked=True)


def _root(symbol):
    m = _OCC.match(symbol or "")
    return m.group(1) if m else None


# ------------------------------------------------------------ contract choice
def pick_contract(rows, side, expiry, now):
    """The call (side > 0) or put (side < 0) expiring `expiry` with
    |delta| nearest TARGET_DELTA among the quoted, fresh, tight
    contracts -> (row, None) or (None, why). Rows without a delta are
    not chosen from. Logic-identical to the vendored source."""
    cp = "call" if side > 0 else "put"
    mine = [r for r in rows or () if r.get("expiration") == expiry
            and r.get("type") == cp and r.get("root") in ROOTS]
    if not mine:
        return None, "no %s listed for %s" % (cp, expiry)
    ok, why = [], "no two-sided quote"
    for r in mine:
        bid, ask = r.get("bid"), r.get("ask")
        if not (bid and ask and bid > 0 and ask >= bid):
            continue
        if now - float(r.get("t") or 0) > QUOTE_MAX_AGE_S:
            why = "quotes older than %d s" % QUOTE_MAX_AGE_S
            continue
        if (ask - bid) / ask > MAX_SPREAD:
            why = "spread over %d%%" % (MAX_SPREAD * 100)
            continue
        if r.get("delta") is None:
            why = "no delta"
            continue
        ok.append(r)
    if not ok:
        return None, why
    return min(ok, key=lambda r: (abs(abs(float(r["delta"])) - TARGET_DELTA),
                                  r["symbol"])), None


def contracts_for(ask):
    """Whole contracts for the premium budget; one if it costs up to
    1.5 budgets; else 0. Logic-identical to the vendored source."""
    n = int(PREMIUM_PER_TRADE // (ask * 100.0))
    if n >= 1:
        return n
    return 1 if ask * 100.0 <= 1.5 * PREMIUM_PER_TRADE else 0


class Milkman0DTESleeve(BaseSleeve):
    CONFIG = CONFIG

    def _log(self, st, **kw):
        st["log"] = (st["log"] + [kw])[-200:]

    def _exit(self, occ, qty, price_hint, why):
        return Intent("exit", occ, qty=float(abs(qty)),
                      price_hint=price_hint, side="sell",
                      position_intent="sell_to_close",
                      reason=f"{SID} {why}")

    def signal(self, bars, slice_state, ctx):
        now, session = float(ctx.now), ctx.session
        extra = ctx.extra or {}
        st = dict(extra.get("milkman_state") or {})
        for k, v in (("day", ""), ("start_equity", None), ("stopped", {}),
                     ("open", {}), ("seen", {}), ("log", []), ("seq", 0),
                     ("inert", "")):
            st.setdefault(k, v)
        self.milkman_state = st
        self.last_evaluation = {"sleeve": SID, "session": session,
                                "state": "scanning", "inert": ""}
        if st["day"] != session:
            for key, x in list(st["open"].items()):
                self._log(st, key=key,
                          why="expired: settled at the official SPX close",
                          at=x.get("session"))
            st.update(day=session, start_equity=float(ctx.equity or 0.0),
                      stopped={}, open={}, seen={})
        now_dt = datetime.fromtimestamp(now, tz=ET)
        if now_dt.weekday() >= 5 or not (dtime(9, 30) <= now_dt.time()
                                         < dtime(16, 0)):
            self.last_evaluation["state"] = "outside_rth"
            return []
        close_ts = datetime.combine(now_dt.date(), dtime(16, 0),
                                    tzinfo=ET).timestamp()
        secs_to_close = close_ts - now
        held = {sym: float(q) for sym, q in (slice_state or {}).items()
                if _root(sym) in ROOTS and float(q or 0) != 0}
        quotes = extra.get("quotes") or {}
        out = []

        book_pnl = extra.get("book_pnl")
        if not st["stopped"] and book_pnl is not None \
                and float(book_pnl) <= DAILY_STOP:
            st["stopped"] = {"at": now, "pnl": round(float(book_pnl), 2)}
            self._log(st, why="daily stop", pnl=round(float(book_pnl), 2),
                      at=now)

        flat = bool(st["stopped"]) or secs_to_close <= HARD_EXIT_S
        if flat:
            tag = "daily stop %.0f: flatten" % DAILY_STOP if st["stopped"] \
                else "hard exit before the close"
            for sym, q in held.items():
                bid = (quotes.get(sym) or {}).get("bid")
                out.append(self._exit(sym, q,
                                      float(bid) if bid else None, tag))
            for key in list(st["open"]):
                if st["open"][key]["occ"] not in held:
                    st["open"].pop(key)
            self.last_evaluation["state"] = "stopped" if st["stopped"] \
                else "hard_exit"
            self.last_evaluation["inert"] = (
                "daily stop hit (%.0f): flat, no entry for the session"
                % st["stopped"]["pnl"] if st["stopped"] else "")
            return out

        probe = extra.get("spx_probe") or {}
        available = probe.get("available") is True and probe.get("underlying")
        chain_rows = extra.get("chain_rows")

        for key in extra.get("lane_exits") or []:
            x = st["open"].get(key)
            if x is None:
                continue
            occ = x["occ"]
            if occ in held:
                bid = (quotes.get(occ) or {}).get("bid")
                out.append(self._exit(occ, held[occ],
                                      float(bid) if bid else None,
                                      f"exit bar of {key}"))
            st["open"].pop(key)
            st["seen"][key] = "done"
            self._log(st, key=key, why="signal exit", at=now)

        if not available:
            why = INERT + ": " + str(
                probe.get("why")
                or "the spx_chain_probe job has not recorded a result")
            self.last_evaluation["inert"] = why
            self.last_evaluation["state"] = "inert"
            st["inert"] = why
            return out
        st["inert"] = ""

        if secs_to_close <= NO_ENTRY_S:
            self.last_evaluation["state"] = "no_entry_window"
            return out

        for lane in extra.get("lane_signals") or []:
            key, sd = lane.get("key"), lane.get("side")
            if not key or sd not in (1, -1):
                continue
            if key.split(":")[0] in EXCLUDED:
                continue
            if key in st["open"] or key in st["seen"]:
                continue
            if len(st["open"]) >= MAX_OPEN:
                st["seen"][key] = "skipped: %d open" % MAX_OPEN
                continue
            row, why = pick_contract(chain_rows, sd, session, now) \
                if chain_rows else (None, "no chain rows read")
            n = contracts_for(float(row["ask"])) if row else 0
            if row is not None and n < 1:
                row, why = None, "one contract over budget"
            if row is None:
                st["seen"][key] = "skipped: " + why
                self._log(st, key=key, why="no entry: " + why, at=now)
                continue
            st["seen"][key] = "open"
            st["open"][key] = {"occ": row["symbol"], "side": sd, "qty": n,
                               "ask": row["ask"], "at": now,
                               "session": session}
            out.append(Intent(
                "enter", row["symbol"], qty=float(n),
                limit_price=round(float(row["ask"]), 2),
                price_hint=float(row["ask"]), side="buy",
                position_intent="buy_to_open",
                reason=f"{SID} {key}: {'call' if sd > 0 else 'put'} "
                       f"{row['symbol']} x{n} at the ask "
                       f"{row['ask']:.2f} (bid {row['bid']:.2f})"))
        if len(st["seen"]) > 1500:
            st["seen"] = {}
        return out


_INSTANCE = Milkman0DTESleeve()


def signal(bars, slice_state, context):
    out = _INSTANCE.signal(bars, slice_state, context)
    signal.last_evaluation = _INSTANCE.last_evaluation
    signal.milkman_state = _INSTANCE.milkman_state
    return out
