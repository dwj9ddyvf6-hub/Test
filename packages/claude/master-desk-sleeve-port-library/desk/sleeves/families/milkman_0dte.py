"""Milkman 0DTE SPX (family "milkman_0dte"): the Milkman SPY intraday setups expressed the way the owner trades them,
with same-day-expiry SPX options and his daily stop (DEC-02, 2026-10-27: the agent's decision, recorded in
docs/OWNER_RULINGS.md). One forward paper book, mk_zerodte_spx; the existing mk_* sleeves are untouched.

Signals: the study's own detection (desk/sleeves/milkman/intraday.py lane_trades over the same SPY panel, the
designated cell per side of every setup except ESMON, an extended-hours clock, and OPX4, a ten-session hold). A long
lane buys a same-day call, a short lane buys a same-day put (long premium only: the risk of a trade is its premium); a
lane's exit bar sells that contract. The setups still read SPY's 1-minute bars; SPY is the signal's tape, never the
instrument traded.
Contract: today's expiry only, SPXW or SPX as the probe recorded (desk/data/spx_probe.py), the contract whose |delta| is
nearest 0.40 with a two-sided quote at most 20% wide (spread / ask) and fresher than 3 minutes, bought at the quoted
ask (a limit at the ask), sold at a marketable limit under the quoted bid. No Black-Scholes price is ever used.
Sizing: a $1,000,000 virtual book; PREMIUM_PER_TRADE ($2,500) of premium a trade in whole contracts (one contract if it
costs up to 1.5 times that), at most MAX_OPEN (4) open at once, so every contract in the book can lose its whole premium
and the book still sits at the stop, not beyond it.
Daily stop (a sleeve-level risk rule; no OMS or global change): the book's realised plus open P&L since the session's
first pass (equity now less equity then, the books' own marks) reaching DAILY_STOP (-$10,000) flattens everything at
once and no entry follows for the rest of the session; every later pass cancels working entries and re-sends exits for
any option still held, until flat.
Close: no entry in the last 30 minutes; at 15 minutes before the close everything is flattened with marketable
limits (options have no market-on-close). A contract still held at the expiry (downtime, a refused exit) settles in the
engine at the official SPX close, in cash at intrinsic value (desk/engine.py _settle_options; SPXW is PM-settled);
the sleeve's ledger drops it on the next session's first pass as "expired".
INERT until the SPX 0DTE chain is proven: with no complete spx_chain_probe record saying SPX (or SPXW) lists today's
expiry with fresh two-sided quotes, the sleeve enters nothing and names the reason "SPX 0DTE chain not available"
(abstention); it never falls back to SPY options or to a model. Exits and the stop run whether it is inert or not.
Named divergences from the study: its fills at the signal level and its SPY shares are replaced by option quotes; its
$10,000 notional a trade by the premium budget; the study has no daily stop."""
import math

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...data import spx_probe
from ...data.options import _alpaca_row
from ..milkman import intraday as I

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
LATE = I.LATE
EXCLUDED = ("ESMON", "OPX4")
ROOTS = ("SPXW", "SPX")
FEED = "milkman_0dte_chain"
INERT = "SPX 0DTE chain not available"
SOURCE = dict(I.SOURCE, family="Milkman 0DTE SPX", decision="DEC-02 2026-10-27")


# ----------------------------------------------------------------------------------------------- the chain feed
class Chain:
    """today's SPX/SPXW chain, read only when the sleeve asks (an entry or an exit price), once a pass."""

    def __init__(self, opts, now):
        self.opts, self.now, self._rows = opts, now, {}

    def rows(self, under, expiry):
        if (under, expiry) not in self._rows:
            try:
                snaps = self.opts._snapshots(under, (expiry, expiry)) or {}
                self._rows[(under, expiry)] = [_alpaca_row(under, occ, sn, self.now) for occ, sn in snaps.items()]
            except Exception:
                self._rows[(under, expiry)] = None
        return self._rows[(under, expiry)]

    def quotes(self, occs):
        try:
            return self.opts.quotes(list(occs)) or {}
        except Exception:
            return {}


def feed_chain(f, s, now, arg):
    opts = getattr(getattr(f, "hub", None), "options", None)
    return Chain(opts, now) if opts is not None else None


FEEDS = {FEED: feed_chain}


# ----------------------------------------------------------------------------------------------- contract choice
def pick_contract(rows, side, expiry, now):
    """the call (side > 0) or put (side < 0) expiring `expiry` with |delta| nearest TARGET_DELTA among the quoted,
    fresh, tight contracts -> (row, None) or (None, why). Rows without a delta are not chosen from."""
    cp = "call" if side > 0 else "put"
    mine = [r for r in rows or () if r.get("expiration") == expiry and r.get("type") == cp and r.get("root") in ROOTS]
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
    return min(ok, key=lambda r: (abs(abs(float(r["delta"])) - TARGET_DELTA), r["symbol"])), None


def contracts_for(ask):
    """whole contracts for the premium budget; one if it costs up to 1.5 budgets; else 0."""
    n = int(PREMIUM_PER_TRADE // (ask * 100.0))
    if n >= 1:
        return n
    return 1 if ask * 100.0 <= 1.5 * PREMIUM_PER_TRADE else 0


class Milkman0DTE(Sleeve):
    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="milkman_0dte", cadence_s=60, universe=("SPX",), capital=CAPITAL, schedule="rth",
            needs={"feeds": ["milkman_spy", FEED]},
            params={"daily_stop": DAILY_STOP, "premium_per_trade": PREMIUM_PER_TRADE, "max_open": MAX_OPEN,
                    "target_delta": TARGET_DELTA, "hard_exit_s": HARD_EXIT_S, "no_entry_s": NO_ENTRY_S,
                    "setups": [k for k in I.SETUPS if k not in EXCLUDED]},
            source=SOURCE,
            state_schema={"day": "str", "start_equity": "float", "stopped": "dict", "open": "dict", "seen": "dict",
                          "log": "list", "seq": "int", "inert": "str"})
        self._why = None

    def bind(self, engine):
        self.engine = engine

    def abstention(self, view):
        return self._why

    # -- helpers -----------------------------------------------------------------------------------------
    def _log(self, st, **kw):
        st["log"] = (st["log"] + [kw])[-200:]

    def _exit(self, chain, inst, qty, pos, now, why, session, tag):
        occ = inst[4:]
        px = None
        if chain is not None:
            q = chain.quotes([occ]).get(occ) or {}
            if q.get("bid"):
                px = float(q["bid"])
        if px is None and (pos or {}).get("mark"):
            px = float(pos["mark"])
        return Intent("exit", occ, side="long", qty=float(qty), asset="option", price_hint=px,
                      order=OrderSpec(type="marketable_limit", buffer_bps=1000.0, window_s=120),
                      signal_key=f"{SID}:{session}:{tag}:{occ}:{int(now // 300)}", reason=f"{SID} {why}")

    # -- the pass ----------------------------------------------------------------------------------------
    def signal(self, view):
        now, session = float(view.now), view.session
        st = dict(view.state or {})
        for k, v in (("day", ""), ("start_equity", None), ("stopped", {}), ("open", {}), ("seen", {}), ("log", []),
                     ("seq", 0), ("inert", "")):
            st.setdefault(k, v)
        self._st, self._why = st, None
        if st["day"] != session:
            for key, x in list(st["open"].items()):          # held past its expiry: the engine settled it in cash
                self._log(st, key=key, why="expired: settled by the engine at the official SPX close", at=x.get("session"))
            st.update(day=session, start_equity=float(view.equity), stopped={}, open={}, seen={})
        if not cal.is_rth(now):
            return []
        chain = view.extra.get(FEED)
        held = {i: p for i, p in view.positions.items()
                if i.startswith("OPT:") and abs(float(p.get("qty") or 0)) > 1e-9}
        pending = [p for p in (view.extra.get("pending_orders") or []) if str(p.get("inst", "")).startswith("OPT:")]
        out = []
        day_pnl = float(view.equity) - float(st["start_equity"])
        if not st["stopped"] and day_pnl <= DAILY_STOP:
            st["stopped"] = {"at": now, "pnl": round(day_pnl, 2)}
            self._log(st, why="daily stop", pnl=round(day_pnl, 2), at=now)
        close = cal.session_close(session)
        flat = bool(st["stopped"]) or now >= close - HARD_EXIT_S
        if flat:
            for p in pending:                                # working entries are withdrawn
                if p.get("action") == "enter" or p.get("side") == "buy":
                    out.append(Intent("cancel", p["inst"][4:], asset="option",
                                      reason=f"{SID} {'daily stop' if st['stopped'] else 'close'}: withdraw"))
            tag = "stop" if st["stopped"] else "close"
            for inst, p in held.items():
                out.append(self._exit(chain, inst, abs(float(p["qty"])), p, now,
                                      "daily stop %.0f: flatten" % DAILY_STOP if st["stopped"] else
                                      "hard exit before the close", session, tag))
            for key in list(st["open"]):
                if ("OPT:" + st["open"][key]["occ"]) not in held:
                    st["open"].pop(key)
            self._why = ("daily stop hit (%.0f): flat, no entry for the session" % st["stopped"]["pnl"]
                         if st["stopped"] else "inside the last %d minutes: flat" % (HARD_EXIT_S // 60))
            return out
        under, inert = spx_probe.availability(getattr(self.engine, "root", None) or "", session)
        for key, x in list(st["open"].items()):              # entries that never filled
            inst = "OPT:" + x["occ"]
            if inst not in held and not any(p.get("inst") == inst for p in pending) and now - x["at"] > 240:
                st["open"].pop(key)
                self._log(st, key=key, why="entry did not fill", at=now)
        P = view.extra.get("milkman_spy")
        live = P is not None and P.today == session and P.live_di is not None and I.full_day(session)
        sigs = []
        if live:
            for setup in I.SETUPS:
                if setup in EXCLUDED:
                    continue
                for sd, cell in I.SETUPS[setup][1]:
                    lane = f"{setup}:{'L' if sd > 0 else 'S'}"
                    for t in I.lane_trades(setup, P, P.live_di, cell, sd):
                        sigs.append((f"{lane}|{session}|{t['key']}", sd, t))
        jmax = int(P.E0[P.live_di]) if live else 0
        for key, sd, t in sigs:                              # exits of the lanes' own trades
            x, ex = st["open"].get(key), t.get("exit")
            if x is not None and ex is not None:
                inst = "OPT:" + x["occ"]
                if inst in held:
                    out.append(self._exit(chain, inst, abs(float(held[inst]["qty"])), held[inst], now,
                                          f"exit bar {ex[0]} of {key}", session, "sig"))
                st["open"].pop(key)
                st["seen"][key] = "done"
                self._log(st, key=key, why="signal exit", at=now)
        if inert:
            self._why = inert
            st["inert"] = inert
            return out
        st["inert"] = ""
        if now >= close - NO_ENTRY_S:
            return out
        for key, sd, t in sigs:
            if key in st["open"] or key in st["seen"]:
                continue
            ex = t.get("exit")
            if ex is not None and ex[0] <= t["decide"]:
                st["seen"][key] = "same_bar"
            elif t["decide"] < jmax - LATE or ex is not None:
                st["seen"][key] = "missed"
            elif len(st["open"]) >= MAX_OPEN:
                st["seen"][key] = "skipped: %d open" % MAX_OPEN
            else:
                rows = chain.rows(under, session) if chain is not None else None
                row, why = pick_contract(rows, sd, session, now) if rows else (None, "no chain rows read")
                n = contracts_for(float(row["ask"])) if row else 0
                if row is not None and n < 1:
                    row, why = None, "one contract over budget"
                if row is None:
                    st["seen"][key] = "skipped: " + why
                    self._log(st, key=key, why="no entry: " + why, at=now)
                    continue
                st["seen"][key] = "open"
                st["open"][key] = {"occ": row["symbol"], "side": sd, "qty": n, "ask": row["ask"], "at": now,
                                   "session": session}
                out.append(Intent("enter", row["symbol"], side="long", qty=float(n), asset="option",
                                  price_hint=float(row["ask"]),
                                  order=OrderSpec(type="limit", limit_price=round(float(row["ask"]), 2), window_s=120),
                                  signal_key=f"{SID}:{key}",
                                  reason=f"{SID} {key}: {'call' if sd > 0 else 'put'} {row['symbol']} "
                                         f"x{n} at the ask {row['ask']:.2f} (bid {row['bid']:.2f})",
                                  meta={"setup_key": key, "bid": row["bid"], "delta": row["delta"],
                                        "quote_t": row["t"]}))
        if len(st["seen"]) > 1500:
            st["seen"] = {}
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [Milkman0DTE()]
