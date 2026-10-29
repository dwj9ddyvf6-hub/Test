"""midna_opt_turtle_atm_call / midna_opt_reversal_call_spread / midna_opt_distance_pair — Midna's three listed-option
paper books (src/lib/equity/option-books.ts @ cursor/paper-desk-f184 68315288, blob c95db1d9: applyOptionBooks,
stopTurtle, expireAll, stepTurtle / buyCall, stepReversal / buySpread, stepPairs / buyPair, closeAt, liquidation,
openPackage; options-surface.ts pickExpiration / pickStrike / occSymbol), ported line for line, each its own $100,000
book, on the board / quantpedia signals (desk/feedlib/midna_signals.py) and the listed chains of the option-marks
producer (desk/feedlib/midna_options.py).

  act       on the regular session right after the signal session, from 10:00 ET (canAct), signals from the
            book's birth session on; a chain is fresh when it is today's and built <= 20 minutes ago
  turtle    one ATM call (the expiration nearest 30 days, 14..60; the strike nearest the chain's spot, the lower on a
            tie) on a 20- or 55-day breakout of the listed surface set (COMPARE_UNIVERSE), alphabetical, at most 4
            open; debit = ask x 100 (ask >= $0.20, a two-sided market no wider than 50% of mid); qty = floor(min(cash,
            1% of the book's equity) / debit); stop = the stock's last - 2 x ATR20: closed when the stock trades at
            or under it (regular hours), on the 10-day exit, at expiration; a winning call skips the next 20-day-only
            breakout of its name (skip20 / wonOn / skippedFor, as board.ts)
  reversal  a call spread (long ATM, short the listed strike nearest 5% above) on each of the five worst prior-month
            large caps while fewer than five are open: debit = long ask - short bid (>= $0.20); qty = floor(min(cash,
            equity / 5) / debit); closed when the name leaves the five but stays in the universe, at expiration
  pairs     a call on the cheap leg and a put on the rich leg (ATM each, a common expiration nearest 30 days) for a
            pair whose |z| >= 2 while fewer than five are open; closed when the pair is listed with |z| < 0.5, at
            expiration
  close     at the liquidation value (longs at the bid, shorts at the ask) on fresh chains of every leg, if the cash
            stays >= 0

Removed (cutover doctrine): green.ts buyBlockReason on every new package (QQQ red AND VIX up AND the call's
underlying red — the desk-wide red-day gate) and state.halted ("Entries are halted", the desk kill switch).

Named divergences: orders are engine children at the source's paper prices (a call / a pair leg: a DAY limit at the
ask, a spread: one multi-leg DAY limit at its net debit; closes at the bid / ask / net credit) — the source booked
each package at once; a working order counts as done (the package is open while its entry works, closed while its
close works) and the book's cash moves by the working orders' prices; the pairs package goes as two option orders
(two underlyings); an option still held at its expiry close settles by the engine's rule where the source closed it
at the chain's liquidation value on the expiration day (it does both: the close is sent that day); the chain file
hand-off is the producer job's cache; marks are recomputed from the chain each pass (the last known mark kept)."""
import math

from ...contract import Intent, Leg, OrderSpec, Sleeve, SleeveConfig
from ...feedlib.midna_options import SURFACE, contract_key, pick_expiration
from . import common as M

SOURCE = {"repo": "midna", "ref": "cursor/paper-desk-f184", "commit": "68315288cb7af1340ee1a44cf446c6a9bb3e65fa",
          "path": "src/lib/equity/option-books.ts", "blob": "c95db1d9af6f9afc01f8875a98631a4b97273932",
          "surface": {"path": "src/lib/equity/options-surface.ts", "blob": "f4713824fd1b"},
          "producer": {"path": "scripts/option-marks.ts", "blob": "3a592015033d"}}
OPT_NAV = 100_000.0
OPT_SLOTS = 5
TURTLE_MAX = 4
TURTLE_RISK = 0.01
CONTRACT = 100
MIN_DEBIT = 0.2
MAX_REL_SPREAD = 0.5
MAX_SPOT_GAP = 0.02
MARKS_FRESH_MS = 20 * 60_000
IDS = {"opt-turtle": "midna_opt_turtle_atm_call", "opt-reversal": "midna_opt_reversal_call_spread",
       "opt-pairs": "midna_opt_distance_pair"}
REMOVED = ["green.ts buyBlockReason on a new package: QQQ red + VIX up + the underlying red (desk-wide red-day gate)",
           "state.halted: 'Entries are halted' (desk kill switch)"]


def occ_symbol(root, expiration, right, strike):
    return f"{root}{expiration[2:4]}{expiration[5:7]}{expiration[8:10]}{right}{M.js_round(strike * 1000):08d}"


def pick_strike(strikes, spot, side):
    if not (spot > 0) or not strikes:
        return None
    if side == "atm":
        best = None
        for k in strikes:
            if best is None:
                best = k
                continue
            nxt, have = abs(k - spot), abs(best - spot)
            if nxt < have or (nxt == have and k < best):
                best = k
        return best
    target = spot * 0.95 if side == "put" else spot * 1.05
    pool = [k for k in strikes if (k < spot if side == "put" else k > spot)]
    best = None
    for k in pool:
        if best is None or abs(k - target) < abs(best - target):
            best = k
    return best


def can_act(now, as_of, born):
    if as_of < born:
        return False
    if M.trading_days_after(as_of, M.et_ymd(now)) != 1:
        return False
    if M.phase_at(now) != "rth":
        return False
    return M.et_parts(now)["minutes"] >= 10 * 60


def fresh_chain(name, marks, now):
    if not name or not marks or not ((name.get("spot") or 0) > 0) or name.get("day") != M.et_ymd(now):
        return False
    built = marks.get("builtAt")
    if built is None:
        return False
    return (now - built) * 1000 <= MARKS_FRESH_MS and now * 1000 >= built * 1000 - 60_000


def row_at(name, expiration, right, strike):
    row = (((name or {}).get("expirations") or {}).get(expiration) or {}).get("contracts", {}) \
        .get(contract_key(right, strike))
    if not row or not M.finite(row.get("bid")) or not M.finite(row.get("ask")):
        return None
    return row


def usable(row, strict):
    if row["ask"] < row["bid"] or row["bid"] < 0 or row["ask"] < 0:
        return False
    if not strict:
        return True
    if not (row["bid"] > 0) or not (row["ask"] > 0):
        return False
    mid = (row["bid"] + row["ask"]) / 2
    return mid > 0 and (row["ask"] - row["bid"]) / mid <= MAX_REL_SPREAD


def dollars(per_share):
    return M.round2(per_share * CONTRACT)


def liquidation(legs, expiration, marks):
    per = 0.0
    for leg in legs:
        row = row_at(((marks or {}).get("names") or {}).get(leg["root"]), expiration, leg["right"], leg["strike"])
        if not row or not usable(row, False):
            return None
        px = row["bid"] if leg["side"] == "long" else row["ask"]
        per += px if leg["side"] == "long" else -px
    return dollars(per)


class Account:
    """the OptionAccount during one pass (open packages in book order; closes / opens recorded as orders)."""

    def __init__(self, ident, cash, positions, born, skip20=None, skipped_for=None, won_on=None, told=None):
        self.id = ident
        self.cash = cash
        self.positions = positions
        self.born = born
        self.skip20 = dict(skip20 or {})
        self.skipped_for = dict(skipped_for or {})
        self.won_on = dict(won_on or {})
        self.just_won = {}
        self.pending_signal = None
        self.told = dict(told or {})
        self.orders = []

    def equity(self):
        return self.cash + M.js_sum(p["qty"] * (p["mark"] if M.finite(p.get("mark")) else p["entryAvg"])
                                    for p in self.positions)

    def mark_open(self, marks):
        for p in self.positions:
            v = liquidation(p["legs"], p["expiration"], marks)
            if v is not None:
                p["mark"] = v

    def close_at(self, p, now, marks, reason):
        value = liquidation(p["legs"], p["expiration"], marks)
        ready = all(fresh_chain(((marks or {}).get("names") or {}).get(l["root"]), marks, now) for l in p["legs"])
        if value is None or not ready:
            return False
        proceeds = M.round2(p["qty"] * value)
        if M.round2(self.cash + proceeds) < 0:
            return False
        pnl = M.round2((value - p["entryAvg"]) * p["qty"])
        self.cash = M.round2(self.cash + proceeds)
        self.positions.remove(p)
        self.orders.append({"action": "close", "pos": p, "value": value, "reason": reason, "marks": marks})
        if self.id == "opt-turtle":
            self.skip20[p["root"]] = pnl > 0
            if pnl > 0:
                self.won_on[p["root"]] = self.pending_signal or ""
                self.just_won[p["root"]] = True
        return True

    def open_package(self, root, pair_key, qty, debit, mark, expiration, legs, stop, now, sym, prices):
        self.cash = M.round2(self.cash - qty * debit)
        p = {"key": f"{self.id}:{pair_key or root}:{M.et_ymd(now)}", "sym": sym, "root": root, "pairKey": pair_key,
             "qty": qty, "entryAvg": debit, "mark": mark, "entryDay": M.et_ymd(now), "expiration": expiration,
             "legs": legs, "stop": stop}
        self.positions.append(p)
        self.orders.append({"action": "open", "pos": p, "prices": prices})


def stop_turtle(acc, now, quotes, marks):
    for p in list(acc.positions):
        q = quotes.get(p["root"])
        if not q or not (q["last"] > 0) or p["stop"] is None:
            continue
        if q["last"] > p["stop"]:
            continue
        acc.close_at(p, now, marks, "Turtle 2N stop")


def expire_all(acc, now, marks):
    today = M.et_ymd(now)
    for p in list(acc.positions):
        if p["expiration"] > today:
            continue
        acc.close_at(p, now, marks, "Expiration")


def buy_call(acc, root, atr, now, quotes, chain, marks):
    q = quotes.get(root)
    if not q or not (atr > 0):
        return "skip"
    if abs(chain["spot"] - q["last"]) / q["last"] > MAX_SPOT_GAP:
        return "wait"
    exp = pick_expiration(M.et_ymd(now), list(chain["expirations"]))
    book = chain["expirations"].get(exp) if exp else None
    if not exp or not book:
        return "wait"
    strike = pick_strike(book["strikes"], chain["spot"], "atm")
    if strike is None:
        return "wait"
    row = row_at(chain, exp, "C", strike)
    if not row or not usable(row, True):
        return "wait"
    debit = dollars(row["ask"])
    if not (debit > 0) or row["ask"] < MIN_DEBIT:
        return "skip"
    budget = min(acc.cash, acc.equity() * TURTLE_RISK)
    qty = math.floor(budget / debit)
    if qty < 1:
        return "skip"
    legs = [{"occ": occ_symbol(root, exp, "C", strike), "root": root, "right": "C", "strike": strike, "side": "long"}]
    acc.open_package(root, None, qty, debit, dollars(row["bid"]), exp, legs, q["last"] - 2 * atr, now,
                     f"{root} {M.js_num(strike)} call", {legs[0]["occ"]: row["ask"]})
    if marks:
        acc.mark_open(marks)
    return "filled"


def step_turtle(acc, now, quotes, board, marks):
    if not board or not board.get("asOf") or not board.get("bars"):
        acc.just_won = {}
        return
    if not can_act(now, board["asOf"], acc.born):
        acc.just_won = {}
        return
    by_sym = {b["sym"]: b for b in board["bars"]}
    for p in list(acc.positions):
        bar = by_sym.get(p["root"])
        if not bar or not bar.get("exit10"):
            continue
        acc.close_at(p, now, marks, "Turtle 10-day exit")
    seen, won = acc.skipped_for, acc.just_won
    wanted = sorted([b for b in board["bars"] if (b.get("enter20") or b.get("enter55")) and b["sym"] in SURFACE],
                    key=lambda b: M.locale_key(b["sym"]))
    for bar in wanted:
        if len(acc.positions) >= TURTLE_MAX:
            break
        if any(p["root"] == bar["sym"] for p in acc.positions):
            continue
        if bar.get("enter20") and not bar.get("enter55") and (won.get(bar["sym"]) or acc.skip20.get(bar["sym"]) or
                                                              seen.get(bar["sym"]) == board["asOf"]):
            if not won.get(bar["sym"]) and seen.get(bar["sym"]) != board["asOf"]:
                seen[bar["sym"]] = board["asOf"]
                if board["asOf"] > (acc.won_on.get(bar["sym"]) or ""):
                    acc.skip20[bar["sym"]] = False
            continue
        chain = ((marks or {}).get("names") or {}).get(bar["sym"])
        if not fresh_chain(chain, marks, now):
            continue
        buy_call(acc, bar["sym"], bar.get("atr20") or 0, now, quotes, chain, marks)
    acc.just_won = {}


def buy_spread(acc, root, now, quotes, chain):
    q = quotes.get(root)
    if not q:
        return "skip"
    if not (q["last"] > 0) or abs(chain["spot"] - q["last"]) / q["last"] > MAX_SPOT_GAP:
        return "wait"
    exp = pick_expiration(M.et_ymd(now), list(chain["expirations"]))
    book = chain["expirations"].get(exp) if exp else None
    if not exp or not book:
        return "wait"
    lk = pick_strike(book["strikes"], chain["spot"], "atm")
    sk = pick_strike(book["strikes"], chain["spot"], "call")
    if lk is None or sk is None or sk <= lk:
        return "wait"
    long, short = row_at(chain, exp, "C", lk), row_at(chain, exp, "C", sk)
    if not long or not short or not usable(long, True) or not usable(short, True):
        return "wait"
    per = long["ask"] - short["bid"]
    if per < MIN_DEBIT:
        return "skip"
    debit = dollars(per)
    budget = min(acc.cash, acc.equity() / OPT_SLOTS)
    qty = math.floor(budget / debit)
    if qty < 1:
        return "skip"
    legs = [{"occ": occ_symbol(root, exp, "C", lk), "root": root, "right": "C", "strike": lk, "side": "long"},
            {"occ": occ_symbol(root, exp, "C", sk), "root": root, "right": "C", "strike": sk, "side": "short"}]
    acc.open_package(root, None, qty, debit, dollars(long["bid"] - short["ask"]), exp, legs, None, now,
                     f"{root} {M.js_num(lk)}/{M.js_num(sk)} call spread", {"net": per})
    return "filled"


def step_reversal(acc, now, quotes, qp, marks):
    if not qp or not qp.get("asOf"):
        return
    universe = {r["sym"] for r in qp["reversal"]}
    targets = [r["sym"] for r in sorted(qp["reversal"], key=lambda r: r["ret"])[:OPT_SLOTS]]
    if not can_act(now, qp["asOf"], acc.born):
        return
    for p in list(acc.positions):
        if p["root"] not in universe or p["root"] in targets:
            continue
        acc.close_at(p, now, marks, "Left the loser set")
    for root in targets:
        if len(acc.positions) >= OPT_SLOTS:
            break
        if any(p["root"] == root for p in acc.positions):
            continue
        chain = ((marks or {}).get("names") or {}).get(root)
        if not fresh_chain(chain, marks, now):
            continue
        buy_spread(acc, root, now, quotes, chain)


def pair_key(a, b):
    return "|".join(sorted([a, b]))


def buy_pair(acc, cheap, rich, key, now, quotes, call_chain, put_chain):
    q = quotes.get(cheap)
    if not q:
        return "skip"
    if not (q["last"] > 0) or abs(call_chain["spot"] - q["last"]) / q["last"] > MAX_SPOT_GAP:
        return "wait"
    rq = quotes.get(rich)
    if not rq or not (rq["last"] > 0) or abs(put_chain["spot"] - rq["last"]) / rq["last"] > MAX_SPOT_GAP:
        return "wait"
    exp = pick_expiration(M.et_ymd(now), [e for e in call_chain["expirations"] if put_chain["expirations"].get(e)])
    if not exp:
        return "wait"
    ck = pick_strike(call_chain["expirations"][exp]["strikes"], call_chain["spot"], "atm")
    pk = pick_strike(put_chain["expirations"][exp]["strikes"], put_chain["spot"], "atm")
    if ck is None or pk is None:
        return "wait"
    call, put = row_at(call_chain, exp, "C", ck), row_at(put_chain, exp, "P", pk)
    if not call or not put or not usable(call, True) or not usable(put, True):
        return "wait"
    per = call["ask"] + put["ask"]
    if per < MIN_DEBIT:
        return "skip"
    debit = dollars(per)
    budget = min(acc.cash, acc.equity() / OPT_SLOTS)
    qty = math.floor(budget / debit)
    if qty < 1:
        return "skip"
    legs = [{"occ": occ_symbol(cheap, exp, "C", ck), "root": cheap, "right": "C", "strike": ck, "side": "long"},
            {"occ": occ_symbol(rich, exp, "P", pk), "root": rich, "right": "P", "strike": pk, "side": "long"}]
    acc.open_package(cheap, key, qty, debit, dollars(call["bid"] + put["bid"]), exp, legs, None, now,
                     f"{cheap} call / {rich} put", {legs[0]["occ"]: call["ask"], legs[1]["occ"]: put["ask"]})
    return "filled"


def step_pairs(acc, now, quotes, qp, marks):
    if not qp or not qp.get("asOf"):
        return
    by_key = {pair_key(r["a"], r["b"]): r for r in qp["pairs"]}
    if not can_act(now, qp["asOf"], acc.born):
        return
    for p in list(acc.positions):
        if not p.get("pairKey") or p["pairKey"] not in by_key:
            continue
        row = by_key[p["pairKey"]]
        if row and abs(row["z"]) >= 0.5:
            continue
        acc.close_at(p, now, marks, "Pair spread reverted")
    for row in qp["pairs"]:
        if not row.get("long") or abs(row["z"]) < 2:
            continue
        if len(acc.positions) >= OPT_SLOTS:
            break
        key = pair_key(row["a"], row["b"])
        if any(p.get("pairKey") == key for p in acc.positions):
            continue
        rich = row["b"] if row["long"] == row["a"] else row["a"]
        names = (marks or {}).get("names") or {}
        cc, pc = names.get(row["long"]), names.get(rich)
        if not fresh_chain(cc, marks, now) or not fresh_chain(pc, marks, now):
            continue
        buy_pair(acc, row["long"], rich, key, now, quotes, cc, pc)


def step(acc, now, quotes, board, qp, marks):
    """applyOptionBooks for one account (mark, the regular-hours stop / expiration closes, then its step)."""
    if acc.id == "opt-turtle":
        acc.pending_signal = (board or {}).get("asOf")
    acc.mark_open(marks)
    if M.phase_at(now) == "rth":
        if acc.id == "opt-turtle":
            stop_turtle(acc, now, quotes, marks)
        expire_all(acc, now, marks)
    if acc.id == "opt-turtle":
        step_turtle(acc, now, quotes, board, marks)
    elif acc.id == "opt-reversal":
        step_reversal(acc, now, quotes, qp, marks)
    else:
        step_pairs(acc, now, quotes, qp, marks)


class OptionBook(Sleeve):
    def __init__(self, ident):
        self.ident = ident
        feeds = ["midna_option_marks"] + (["midna_board_signals"] if ident == "opt-turtle" else ["midna_qp_signals"])
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[ident], family="midna", cadence_s=300, capital=OPT_NAV, universe=(), schedule="always",
            needs={"quotes": {"source": "equity"}, "feeds": feeds},
            params={"book": ident, "slots": TURTLE_MAX if ident == "opt-turtle" else OPT_SLOTS,
                    "removed_gates": REMOVED}, source=dict(SOURCE, book=ident),
            state_schema={"born": "str", "pkgs": "dict", "skip20": "dict", "skippedFor": "dict", "wonOn": "dict"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book=None):
        st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) if self.engine is not None else {}
        roots = [r for p in ((st or {}).get("pkgs") or {}).values() for r in {l["root"] for l in p["legs"]}]
        sig = None
        if self.engine is not None and self.engine.feeds is not None:
            sig = self.engine.feeds.get("midna_board_signals" if self.ident == "opt-turtle" else "midna_qp_signals",
                                        self, now)
        if self.ident == "opt-turtle":
            roots += [b["sym"] for b in (sig or {}).get("bars") or [] if (b.get("enter20") or b.get("enter55"))
                      and b["sym"] in SURFACE]
        elif self.ident == "opt-reversal":
            roots += [r["sym"] for r in sorted((sig or {}).get("reversal") or [], key=lambda r: r["ret"])[:OPT_SLOTS]]
        else:
            roots += [s for r in (sig or {}).get("pairs") or [] if abs(r["z"]) >= 2 for s in (r["a"], r["b"])]
        return list(dict.fromkeys(roots))

    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("born", view.session)
        marks = view.extra.get("midna_option_marks")
        board = view.extra.get("midna_board_signals")
        qp = view.extra.get("midna_qp_signals")
        pkgs, cash = packages(view, dict(st.get("pkgs") or {}))
        acc = Account(self.ident, cash, [dict(p) for p in pkgs.values() if p["status"] == "open"], st["born"],
                      st.get("skip20"), st.get("skippedFor"), st.get("wonOn"), st.get("told"))
        quotes = {}
        for sym in {l["root"] for p in acc.positions for l in p["legs"]} | set(self.quote_universe(view.now)) | \
                {"QQQ", "^VIX"}:
            q = M.mq(view.quotes.get(sym))
            if q:
                quotes[sym] = q
        step(acc, view.now, quotes, board, qp, marks)
        close = M.et_to_epoch(view.session, 0, 0) + M.session_close_minutes(view.session) * 60
        window = max(60.0, close - view.now)
        out = []
        for o in acc.orders:
            p = o["pos"]
            if o["action"] == "open":
                pkgs[p["key"]] = dict(p, status="open", sent=view.now, open_px=o["prices"])
                out += open_intents(self.ident, p, o["prices"], window)
            else:
                rec = pkgs.get(p["key"]) or dict(p)
                rec.update(status="closing", close_reason=o["reason"], close_value=o["value"])
                pkgs[p["key"]] = rec
                out += close_intents(self.ident, p, o["marks"], view.session, window)
        for p in acc.positions:                              # marks carried
            if p["key"] in pkgs:
                pkgs[p["key"]]["mark"] = p["mark"]
        st.update(pkgs=pkgs, skip20=acc.skip20, skippedFor=acc.skipped_for, wonOn=acc.won_on, told=acc.told)
        self._st = st
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def open_intents(ident, p, prices, window):
    if len(p["legs"]) == 2 and ident == "opt-reversal":
        lg, sh = p["legs"]
        return [Intent("enter", p["root"], side="long", asset="mleg", qty=float(p["qty"]),
                       legs=(Leg(lg["occ"], "buy", 1, "buy_to_open"), Leg(sh["occ"], "sell", 1, "sell_to_open")),
                       order=OrderSpec(type="limit", limit_price=round(prices["net"], 2), tif="day", window_s=window),
                       signal_key=f"{p['key']}:open", reason=f"{ident}: {p['sym']} x{p['qty']}",
                       meta={"group": p["key"], "underlying": p["root"], "position_meta": {"pkg": p["key"]}})]
    out = []
    for leg in p["legs"]:
        px = prices[leg["occ"]]
        out.append(Intent("enter", leg["occ"], side="long", asset="option", qty=float(p["qty"]), price_hint=px,
                          order=OrderSpec(type="limit", limit_price=round(px, 2), tif="day", window_s=window),
                          signal_key=f"{p['key']}:open:{leg['occ']}", reason=f"{ident}: {p['sym']} x{p['qty']}",
                          meta={"underlying": leg["root"], "position_meta": {"pkg": p["key"]}}))
    return out


def close_intents(ident, p, marks, session, window):
    names = (marks or {}).get("names") or {}
    rows = [row_at(names.get(l["root"]), p["expiration"], l["right"], l["strike"]) for l in p["legs"]]
    if len(p["legs"]) == 2 and ident == "opt-reversal":
        lg, sh = p["legs"]
        net = rows[0]["bid"] - rows[1]["ask"]
        return [Intent("exit", p["root"], asset="mleg", qty=float(p["qty"]),
                       legs=(Leg(lg["occ"], "sell", 1, "sell_to_close"), Leg(sh["occ"], "buy", 1, "buy_to_close")),
                       order=OrderSpec(type="limit", limit_price=round(net, 2), tif="day", window_s=window),
                       signal_key=f"{p['key']}:close:{session}", reason=f"{ident}: close {p['sym']}",
                       meta={"group": p["key"], "underlying": p["root"]})]
    out = []
    for leg, row in zip(p["legs"], rows):
        px = row["bid"]
        out.append(Intent("exit", leg["occ"], side="long", asset="option", qty=float(p["qty"]), price_hint=px,
                          order=OrderSpec(type="limit", limit_price=round(px, 2), tif="day", window_s=window),
                          signal_key=f"{p['key']}:close:{session}:{leg['occ']}", reason=f"{ident}: close {p['sym']}"))
    return out


def packages(view, pkgs):
    """the book's packages as the source's instant-fill book holds them: a recorded package is open while one of
    its legs is held or its entry works, gone while its close works (or once nothing is held and nothing works);
    the cash moves by the working orders at the prices sent."""
    held = {inst[4:]: float(p["qty"]) for inst, p in view.positions.items() if inst.startswith("OPT:")}
    working = {}
    for ch in view.extra.get("pending_orders", []) or []:
        rem = float(ch.get("vqty") or 0.0) - float(ch.get("filled_v") or 0.0)
        if rem > 1e-9 and ch.get("signal_key"):
            working[ch["signal_key"]] = rem
    cash = float(view.cash)
    out = {}
    for key, p in pkgs.items():
        opens = [k for k in working if k.startswith(f"{key}:open")]
        closes = [k for k in working if k.startswith(f"{key}:close")]
        any_held = any(abs(held.get(l["occ"], 0.0)) > 1e-9 for l in p["legs"])
        if closes:                                          # a working close: the package is gone, its proceeds
            frac = sum(working[k] for k in closes) / (float(p["qty"]) * len(closes))   # count (the unfilled part)
            cash += min(1.0, frac) * float(p["qty"]) * float(p.get("close_value") or 0.0)
            out[key] = dict(p, status="closing")
            continue
        if opens:                                           # a working entry: the package is open, its debit paid
            for k in opens:
                px = (p.get("open_px") or {}).get("net")
                if px is None:
                    px = (p.get("open_px") or {}).get(k.rsplit(":", 1)[-1], 0.0)
                cash -= working[k] * px * CONTRACT
            out[key] = dict(p, status="open")
            continue
        if any_held:                                        # held (a close that did not fill is managed again)
            out[key] = dict(p, status="open")
    return out, cash
