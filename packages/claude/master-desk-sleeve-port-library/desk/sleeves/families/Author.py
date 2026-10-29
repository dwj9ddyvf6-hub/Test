"""Author / GrokBot desk (Author-desk) — its paper sleeves, screens and printers on the desk engine. The decision code is
ported line by line from the TypeScript (desk/sleeves/Author/*.py) and proved against the source under Node 22
(tools/parity/Author_{tensor,paper,screens,book}.py receipts).

Rows (manifest family Author):
  Author_komar_momentum          Komar public-proxy momentum screen (@a4fc436c komar/*): hard gates, proxy-B market
                                 colour, A/B tiers; a ready tight / large-base breakout (near the 20-day pivot, fewer
                                 than three up days) buys a stop at the pivot next session; planTicket sizing (0.5%
                                 risk to the 10-day base low, 35% cap); its own 5% open-risk budget
  Author_anna_seven_vote_printer the seven-vote Anna printer (@7683c7dd anna-replica.ts, the last version before
                                 Tensor 2.0) on the Tensor dashboard's default watchlist, daily bars: hold while the
                                 printer's signal is buy (CYAN / GREEN), flat when it turns sell (RED / MAGENTA or the
                                 200-day lost); markers count once 200 bars back them (AUTHORITY_BARS)
  Author_next_support_plan       the admit-ticker v1.1 next-support plan (buy the next support under last, stop under
                                 the 12-day low clamped 2.5-3.5%, the 5R / 6-18% target) for the desk's name list,
                                 papered through the book lane
  Author_washout_ppc_coil        washout v1.2 (washout under the 50-day at a Fib / the 12-day shelf / the 21-day) and
                                 the PPC coil over the desk universe; levels from the admission planner (admitTicker),
                                 papered through the book lane
  Author_scanner_book_swing      the scanner book (desk-scan.mjs + desk-autopilot.mjs runCycle): the Signal Prism scan
                                 of the universe (SPY the bench), buy-desk distillBuys (doctrine, select, curl, the
                                 bottom screen and sector tape, admit-ticker v1.1 plans, the 20-name ceiling),
                                 keepAfterCurl; each cycle orderBook -> filterBookForCurl -> (morning / catch-up
                                 windows) the session-tape rebase and keepNearBuy -> the desk book (else the last
                                 book, else the roster's); maybeBookPaper each pass on live quotes; the swing exits; the
                                 roster (curateRoster) kept as the source kept it
  Author_sector_first_bottom     the bottom screen v1.0 (bottom-screen.ts: the sleeves vs SPY first, then quality x
                                 cheap x turn, the fund overlay), routed as the buy desk routes it (admit-ticker v1.1
                                 plans, admission, the ceiling), on the same cycle and paper lane
  (the three Tensor wire lanes, Author_tensor_gold_diamond, Author_tensor_5m_impulse and
  Author_tensor_1m_bracket, traded 1m / 5m bars: removed from the desk with their code, the owner,
  2026-10-26: "any tensor strategy that requires 1m or 5m bars" is removed altogether)
  Author_echo_swing              the Echo sidecar (scripts/echo-sidecar.mjs runEchoSweep): each new @EchoAnalysis post
                                 classified (echo/classify.ts); a filled buy or add, the first time it is read ->
                                 paperEcho (echoPaperGate on the live mark with vs21 / ret5) -> an Echo ticket
                                 (paperStop / paperTarget) -> the swing manager (trims, rail-flip adds, stops)

The book lane (paper-wire.ts maybeBookPaper -> runPaperTicket -> judgePaper bookTicket, paperShares "swing"; then
runPaperExits each pass): 09:35-15:45 ET, no same-day revenge, six swings / ten open / sixteen new a day / two of a
story per sleeve, price within +-3% of the buy and between stop and target, 1.5% equity risk to the card stop capped
at 8% notional; a bracket (card stop, card target) held by the engine; the swing manager's trims (20% at the first
overhead Fib rejection, half after a 50% week or a stretched weekly RSI), its 50/200-day rail-flip adds (an Echo add
ticket), $75 crumbs flattened, and the sell confirmation exactly as the source runs it (runPaperExits re-judges a
sell without the daily bars or the impulse flag, so only a print through the stop confirms; the card target is the
bracket's).

Removed under the cutover doctrine (desk-wide gates of the Author paper wire, named per sleeve):
  every book-lane sleeve: applyDayGuard (a 3% paper day loss parked the whole wire — a drawdown brake),
    ALPACA_HALTED (operator kill switch), scannerOff() (the scanner was cancelled 22 Aug 2026 — a kill switch), the
    Skyvern PM overlay (a cross-agent context gate that could skip / exit a book name), the account-wide counts
    (open names, swings, impulses, new buys and same-story names counted across every lane of the one Alpaca account
    — here each sleeve counts its own book).
  Author_komar_momentum: KOMAR_STATUS "No paper. No live" / quantity 0 (an undeployed-research staging gate: the
    planned shares trade here).
  Author_scanner_book_swing / Author_sector_first_bottom: honorTodaysList (the operator's posted Typefully list
    replaced the scanned book — a manual context override), applyAnalystToBook (scanners the paper record rated cold
    dropped off the book — a performance kill switch), scannerOff() (above).

Named divergences:
  1. cadence: the wire swept every 2.5 s and at each minute close; here one pass a minute (book lanes), the daily
     sleeves once after the close and at the next session's first pass.
  2. books: each sleeve keeps its own paper ledger (the source's one ledger mixed every lane; the fills-derived
     counts, same-day checks, trims and adds read the sleeve's own rows, retained as vault.ts retainFills does).
  3. orders: placePaperBuy's bracket = engine-held stop / target exit rules (checked against the mark each pass);
     market orders in the regular session, a resting GTC limit at the buy before 09:30 (the source's own split).
  4. the swing manager's daily tape: the completed daily bars plus today's developing bar from the live quote (the
     source read the last scan's cached completed bars for names in that scan, else Yahoo's daily chart with the
     forming bar).
  5. book-lane screens: the setups are built once a session before the open from the last completed session (the
     source rebuilt the book at its publishing windows); a screen sleeve's own setup is decorated as distillBuys
     decorates every admitted name (antiChase, atSupport, curlOk = MACD not falling).
  6. Author_next_support_plan's names: the desk's own list at the pinned commit (folio-list.ts FOLIO_TICKERS, 30
     names — the planner planned whatever names were supplied); Author_washout_ppc_coil's: the desk universe
     (universe.ts signal-prism-us-413.v1) without its two crypto pairs.
  7. Author_komar_momentum (the code had no order or exit manager; the rules are its law and the Komar research
     bundle's — foliotend-tensor-release archive-2026-09-19 bundle-016 "Julian Komar: Trading-System Reverse
     Engineering", stages 6-10): entry a buy stop at the 20-day pivot the next session; the initial stop the 10-day
     base low; half sold on a close back under the pivot; out on a close under the 21-day EMA (the normal swing
     trend's moving average) or after 10 sessions without progress (close <= entry); the market colour from ^IXIC
     daily bars (effective at the next open, as colorHistory computes it).
  8. Author_anna_seven_vote_printer: the dashboard's default watchlist (desk-store.ts DEFAULT_WATCH at the gospel
     backup, 13 names), daily bars (Anna's calls were daily); the printer has no sizing — each name holds an equal
     1/13 slot; a decision on a completed session trades at the next session's first pass.
  9. the scan: a job (Authordesk_scan) once per completed session over the hub's split-adjusted daily bars (502
     sessions, Yahoo's 2y chart), written to cache/Author/scan.json; the source's worker rescanned at every cycle
     from a disk cache / Yahoo, whose completed bars change once a session.
  10. the session tape: the hub's 5-minute extended-hours bars plus the forming bar from the live quote (the source's
     5m chart carried the forming bar).
  11. the scan universe: universe.ts without its two crypto pairs (no daily equity bars), SPY, the regime and sector
     ETFs (desk-scan.mjs order).
  12. book cycles on trading days 04:00-20:00 ET (the source also cycled overnight, when nothing could trade).
  13. Author_sector_first_bottom: the bottom lane on its own (mergeBottomBook's names through distillBuys' admission
     and ceiling), without the Prism candidates ranked in front of it.
  14, 15. (the removed Tensor wire lanes' tape and episode memory)
  16. Author_echo_swing's feed: a job (Authordesk_echo) sweeps every three minutes (the sidecar's POLL_MS) the
     three Nitter RSS mirrors, then the two more fetch-x.ts lists (nitter.poast.org, xcancel.com); a post read in a
     sweep is judged at the sleeve's next pass, with the name's live quote and daily tape (completed + developing
     bar; the source fetched Yahoo's quote and daily chart for the name at once).
  17. (the removed one-minute bracket's watch)
Source behaviour kept, noted: the fund overlay is inert — Yahoo's quoteSummary refuses unauthenticated calls and
fund-io's SEC read looks for companyfacts' `us_gaap` (SEC keys it `us-gaap`), so every name's evidence is unknown and
applyFundOverlay changes nothing, exactly as in the source.
"""
import math
import os
import re

from ... import calendar as cal
from ...contract import ExitRule, Intent, OrderSpec, Sleeve, SleeveConfig
from ...util import et_date, read_json, write_json_atomic
from ..jsport import js_round, lsum
from ..Author import anna as A
from ..Author import book as B
from ..Author import echo as EC
from ..Author import komar as K
from ..Author import levels as L
from ..Author import paper as P
from ..Author import prism as PR
from ..Author import tensor as T
from ..Author import wire as W

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "..", "..", "vendor", "Author")
SOURCE = {"repo": "Author-desk", "ref": "main", "commit": "652db7afcc4312b6bd44d41547ca0f73981fe3ff"}


def _ts_block(path, start, end):
    src = open(os.path.join(VENDOR, path), encoding="utf-8").read()
    i = src.index(start)
    return src[i:src.index(end, i)]


# universe.ts read as rebuild-komar.mjs read it
UNIVERSE = tuple(m.group(1) for m in re.finditer(r'"([A-Z][A-Z0-9.-]{0,7})"',
                                                 _ts_block("universe.ts", "export const UNIVERSE = [", "] as const;")))
STOCKS = tuple(s for s in UNIVERSE if s not in ("BTC-USD", "ETH-USD"))
FOLIO_TICKERS = tuple(m.group(1) for m in re.finditer(r'"([A-Z][A-Z0-9.-]{0,7})"',
                                                      _ts_block("folio-list.ts", "export const FOLIO_TICKERS = [",
                                                                "] as const;")))
DEFAULT_WATCH = tuple(m.group(1) for m in re.finditer(r'"([A-Z][A-Z0-9.-]{0,7})"',
                                                      _ts_block("desk-store.ts", "const DEFAULT_WATCH",
                                                                "].map(")))


# -- bars ----------------------------------------------------------------------------------------------------------------
def gbars(rows):
    """hub bars (t in epoch seconds) -> the sources' bars (t in epoch ms)."""
    return [{"t": int(round(float(b["t"]) * 1000)), "o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
             "c": float(b["c"]), "v": float(b.get("v") or 0)} for b in (rows or [])]


def live_day_bar(daily, quote, now):
    """the completed daily bars plus today's developing bar from the live quote (named divergence 4)."""
    out = list(daily)
    q = quote or {}
    day = et_date(now)
    last = q.get("last")
    if not (last and last > 0) or q.get("day_date") not in (None, day):
        return out
    if out and et_date(out[-1]["t"] / 1000) == day:
        return out
    o = q.get("day_open") or last
    h = max(q.get("day_high") or last, last, o)
    lo = min(q.get("day_low") or last, last, o)
    out.append({"t": int(cal.session_open(day) * 1000), "o": float(o), "h": float(h), "l": float(lo),
                "c": float(last), "v": float(q.get("day_volume") or 0)})
    return out


def _held(view):
    out = {}
    for inst, p in (view.positions or {}).items():
        if inst.startswith("EQ:") and abs(float(p.get("qty") or 0)) > 1e-12:
            out[inst.split(":", 1)[1]] = {"qty": float(p["qty"]), "avg": float(p.get("avg") or 0),
                                         "opened_at": float(p.get("opened_at") or 0), "meta": p.get("meta") or {}}
    return out


def _book_syms(book):
    return sorted(i.split(":", 1)[1] for i in ((book.positions if book is not None else {}) or {}) if i.startswith("EQ:"))


def _quotes(view):
    return {s: q for s, q in (view.quotes or {}).items()}


# -- the book lane -------------------------------------------------------------------------------------------------------
class BookLane(Sleeve):
    """A sleeve that papers its own daily setups through the Author paper wire (maybeBookPaper + runPaperExits)."""
    SCREEN = ()

    def __init__(self, sleeve_id, title, screen, source, universe=None):
        self.screen_names = tuple(universe or screen)
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="Author", cadence_s=60, universe=self.screen_names, schedule="ext",
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": 300, "symbols_for": "daily"}],
                   "quotes": {"source": "equity"}},
            params={"title": title}, source=source)

    # what the engine fetches
    def bar_symbols(self, need, now, book=None):
        held = _book_syms(book)
        st = getattr(self, "_last_state", {}) or {}
        built = (st.get("book") or {}).get("dateEt") == et_date(now)
        return sorted(set(held) | (set() if built else set(self.screen_names)))

    def quote_universe(self, now, book=None):
        """today's setups and the held names; when this process has not yet seen today's book (its first pass: a new
        process, or the session's first pass, which builds the book), every name the book can hold, as bar_symbols
        does, so no ticket is judged on its setup's completed close for want of a quote (2026-10-16 15:45 ET: the
        first pass after a deploy quoted none, GRND bought at 14.07 under its 14.35 card stop on a 15.10 close)."""
        st = getattr(self, "_last_state", {}) or {}
        b = st.get("book") or {}
        names = [s["symbol"] for s in b.get("setups") or []] if b.get("dateEt") == et_date(now) else self.screen_names
        return sorted(set(names) | set(_book_syms(book)))

    def setups(self, daily, now_ms):
        raise NotImplementedError

    def signal(self, view):
        st = dict(view.state or {})
        self._last_state = st
        ms = int(view.now * 1000)
        kind = T.classify_session(ms)
        parts = W.et_parts(view.now)
        if parts["weekday"] in ("Sat", "Sun") or not T.is_signal_session(kind):
            return []
        daily = {s: gbars(rows) for s, rows in ((view.bars or {}).get("1d") or {}).items()}
        intents = []
        book = st.get("book") or {}
        if book.get("dateEt") != parts["dateEt"]:
            book = {"dateEt": parts["dateEt"], "window": "morning",
                    "setups": self.setups({s: b for s, b in daily.items() if s in self.screen_names}, ms)}
            st["book"] = book
            intents.append(Intent("signal", "Author", reason=f"{self.CONFIG.sleeve_id}: book {parts['dateEt']} — "
                                  f"{', '.join(s['symbol'] for s in book['setups'][:12]) or 'empty'}",
                                  signal_key=f"{self.CONFIG.sleeve_id}:book:{parts['dateEt']}",
                                  meta={"setups": [{k: s[k] for k in ("symbol", "plan", "tier", "size")}
                                                   for s in book["setups"][:40]]}))
        quotes = _quotes(view)
        held = _held(view)
        wire = W.Wire(self.CONFIG.sleeve_id, st, view.now, view.equity, held, quotes,
                      trades=(view.extra or {}).get("closed_trades"))

        def tape(sym):
            return live_day_bar(daily.get(sym) or [], quotes.get(sym), view.now)
        wire.exits(parts["dateEt"], parts["hour"], parts["minute"], ms, tape)
        W.book_paper(wire, book, parts["dateEt"], parts["hour"], parts["minute"])
        st.update(wire.state())
        self._st = st
        return intents + wire.intents

    def update_state(self, view, intents):
        st = getattr(self, "_st", None)
        self._st = None
        return st if st is not None else dict(view.state or {})


def _admitted(symbol, daily, last, t, tier, size, coil=None):
    """distillBuys' decoration of an admitted name (named divergence 5)."""
    risk = max(t["buy"] - t["stop"], t["buy"] * 0.01)
    return {"symbol": symbol, "tier": tier, "size": size, "close": last,
            "plan": {"buy": t["buy"], "stop": t["stop"], "target": t["target"],
                     "rr": P.js_round(((t["target"] - t["buy"]) / risk) * 10) / 10},
            "antiChase": True, "atSupport": True, "curlOk": t["macdUp"] is not False, "coilOk": coil,
            "completedBarAt": daily[-1]["t"] if daily else None, "why": t["why"]}


class NextSupportPlan(BookLane):
    def __init__(self):
        super().__init__("Author_next_support_plan", "Next-support plan generator", FOLIO_TICKERS,
                         dict(SOURCE, path="src/lib/workdesk/admit-ticker.ts",
                              blob_sha="2ba2130f275a125af190a396ed71337c8768181a"))

    def setups(self, daily, now_ms):
        out = []
        for sym in self.screen_names:
            bars = daily.get(sym) or []
            if not bars:
                continue
            last = bars[-1]["c"]
            t = L.admit_ticker(sym, bars, last, now_ms)
            if t["tag"] != "BUY" or not t["live"] or None in (t["buy"], t["stop"], t["target"]):
                continue
            out.append(_admitted(sym, bars, last, t, "A", t["size"]))
        return out


class WashoutCoil(BookLane):
    def __init__(self):
        super().__init__("Author_washout_ppc_coil", "Washout and PPC coil screens", STOCKS,
                         dict(SOURCE, path="src/lib/workdesk/washout.ts",
                              blob_sha="d6d55212acc6206cb8cb9da94c0bbb67045c308b"))

    def setups(self, daily, now_ms):
        out = []
        for sym in self.screen_names:
            bars = daily.get(sym) or []
            if len(bars) < 50:
                continue
            last = bars[-1]["c"]
            w = L.washout_buy(bars, last, now_ms)
            if not w:
                continue
            t = L.admit_ticker(sym, bars, last, now_ms)
            if t["tag"] != "BUY" or not t["live"] or None in (t["buy"], t["stop"], t["target"]):
                continue
            s = _admitted(sym, bars, last, t, "S" if w["coil"] else "A", "Full size" if w["coil"] else "Half size",
                          coil=bool(w["coil"]))
            s["why"] = w["why"]
            out.append(s)
        return out


# -- Komar --------------------------------------------------------------------------------------------------------------
KOMAR_SOURCE = {"repo": "Author-desk", "ref": "main", "commit": "a4fc436cc2daa3b5853820550fdeac8a1e4956c7",
                "path": "src/lib/komar/screen.ts", "blob_sha": "52023d6effe7315e73773248e15e37b35ee80ef5"}
PORTFOLIO_RISK_CAP = 0.05
TIME_STOP_SESSIONS = 10


class KomarMomentum(Sleeve):
    def __init__(self, universe=None):
        self.names = tuple(universe or STOCKS)
        self.CONFIG = SleeveConfig(
            sleeve_id="Author_komar_momentum", family="Author", cadence_s=60, universe=self.names,
            schedule="rth,after_close+20:after_close+240",
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": 504, "symbols_for": "screen"},
                            {"source": "yahoo", "interval": "1d", "n": 504, "symbols": ["^IXIC"], "key": "ixic"}],
                   "quotes": {"source": "equity"}},
            params={"title": "Komar public-proxy momentum screen"}, source=KOMAR_SOURCE)

    def bar_symbols(self, need, now, book=None):
        """the screen's universe after the close until the session is screened (then, and in the session, the held
        names): every pass after a screen had re-read 504 bars of each name for nothing (2 s a pass, 2026-10-16)."""
        names = sorted(set(self.names) | {"QQQ"})
        day = et_date(now)
        screened = (getattr(self, "_last_state", None) or {}).get("screened") == day
        return names if now >= cal.session_close(day) and not screened else _book_syms(book)

    def quote_universe(self, now, book=None):
        st = getattr(self, "_last_state", {}) or {}
        plans = (st.get("plans") or {}).get("rows") or []
        return sorted(set(_book_syms(book)) | {p["symbol"] for p in plans})

    def screen(self, daily, ixic, equity):
        qqq = daily.get("QQQ") or []
        qqq_ret20 = qqq[-1]["c"] / qqq[len(qqq) - 21]["c"] - 1 if len(qqq) > 20 else None
        colors = K.color_history(ixic) if len(ixic) >= 2 else []
        eff = colors[-1]["effectiveB"] if colors else None
        out = []
        for sym in self.names:
            bars = daily.get(sym)
            if not bars:
                continue
            c = K.classify_tier(K.inspect_name(sym, bars, qqq_ret20), eff)
            out.append(c)
        return K.rank(out), eff

    def signal(self, view):
        st = dict(view.state or {})
        self._last_state = st
        day = et_date(view.now)
        if not cal.is_trading_day(day):
            return []
        held = _held(view)
        intents = []
        pos = st.setdefault("pos", {})
        for s in list(pos):
            if s not in held:
                pos.pop(s)
        if view.now >= cal.session_close(day):
            if st.get("screened") == day:
                return []
            daily = {s: [dict(b, date=et_date(b["t"] / 1000)) for b in gbars(r)]
                     for s, r in ((view.bars or {}).get("1d") or {}).items()}
            ixic = [dict(b, date=et_date(b["t"] / 1000)) for b in gbars(((view.extra or {}).get("bars_ixic") or {}).get("^IXIC"))]
            if ixic and et_date(ixic[-1]["t"] / 1000) != day:
                return []                                    # the session's ^IXIC bar is not final yet
            ranked, eff = self.screen(daily, ixic, view.equity)
            nxt = cal.next_trading_day(day).isoformat()
            rows = []
            for c in ranked:
                if c["tier"] not in ("S", "A", "B") or c["setup"] == "none" or not c["triggerReady"]:
                    continue
                if c["symbol"] in held:
                    continue
                plan = K.plan_ticket(c["symbol"], c["tier"], c["close"], c["stopPct"], view.equity, True)
                if plan["shares"] <= 0:
                    continue
                rows.append({"symbol": c["symbol"], "tier": c["tier"], "setup": c["setup"], "pivot": c["pivot"],
                             "stop": c["baseLow"], "shares": plan["shares"], "score": c["score"], "close": c["close"]})
            st["plans"] = {"for": nxt, "rows": rows, "effectiveB": eff}
            for s, h in held.items():                          # the exits decided on the completed session
                bars = daily.get(s) or []
                rec = pos.setdefault(s, {})
                if not bars:
                    continue
                close = bars[-1]["c"]
                e21 = K.ema([b["c"] for b in bars], 21)[-1]
                entry_day = rec.get("entry_day") or et_date(h["opened_at"] or view.now)
                held_sessions = cal.trading_days_between(entry_day, day)
                why = None
                if e21 is not None and close < e21:
                    why = "close under the 21-day EMA"
                elif held_sessions >= TIME_STOP_SESSIONS and close <= h["avg"]:
                    why = f"no progress after {TIME_STOP_SESSIONS} sessions"
                elif rec.get("pivot") and close < rec["pivot"] and not rec.get("halved"):
                    rec["exit_half"] = nxt
                if why:
                    rec["exit"] = {"for": nxt, "why": why}
            st["screened"] = day
            intents.append(Intent("signal", "KOMAR", reason=f"komar screen {day}: proxy-B {eff}; "
                                  f"{len(rows)} ready", signal_key=f"komar:{day}",
                                  meta={"effectiveB": eff, "ready": [r["symbol"] for r in rows[:20]]}))
            self._st = st
            return intents
        if not cal.is_rth(view.now):
            return []
        for s, rec in pos.items():
            if s not in held:
                continue
            if (rec.get("exit") or {}).get("for") == day and rec.get("exit_sent") != day:
                intents.append(Intent("exit", s, signal_key=f"komar:{s}:{day}:exit", reason=f"komar: {rec['exit']['why']}"))
                rec["exit_sent"] = day           # the session it was sent for: an unfilled one goes again next decision
            elif rec.get("exit_half") == day and not rec.get("halved"):
                q = math.floor(held[s]["qty"] / 2)
                if q > 0:
                    intents.append(Intent("exit", s, qty=float(q), signal_key=f"komar:{s}:{day}:half",
                                          reason="komar: closed back under the breakout — half"))
                rec["halved"] = True
        plans = st.get("plans") or {}
        if plans.get("for") == day:
            risk_open = sum(max(0.0, h["avg"] - float((pos.get(s) or {}).get("stop") or h["avg"])) * h["qty"]
                            for s, h in held.items())
            for r in plans.get("rows") or []:
                if r["symbol"] in held or r.get("sent"):
                    continue
                risk = max(0.0, r["pivot"] - r["stop"]) * r["shares"]
                if risk_open + risk > PORTFOLIO_RISK_CAP * view.equity:
                    continue
                risk_open += risk
                intents.append(Intent("enter", r["symbol"], qty=float(r["shares"]), price_hint=r["pivot"],
                                      exit_rules=(ExitRule("stop", float(r["stop"])),),
                                      order=OrderSpec(stop_price=float(r["pivot"]), tif="day"),
                                      signal_key=f"komar:{r['symbol']}:{day}:buy",
                                      reason=f"komar {r['tier']} {r['setup']}: buy stop at the pivot {r['pivot']}",
                                      meta={"position_meta": {"pivot": r["pivot"], "stop": r["stop"]}}))
                r["sent"] = True
                pos[r["symbol"]] = {"pivot": r["pivot"], "stop": r["stop"], "entry_day": day}
        self._st = st
        return intents

    def update_state(self, view, intents):
        st = getattr(self, "_st", None)
        self._st = None
        return st if st is not None else dict(view.state or {})


# -- the Anna printer ---------------------------------------------------------------------------------------------------
ANNA_SOURCE = {"repo": "Author-desk", "ref": "main", "commit": "7683c7dd5a",
               "path": "src/lib/tensor/anna-replica.ts", "blob_sha": "a769d404b30279286a8e7bc7f1884943f62e7734"}


class AnnaPrinter(Sleeve):
    CONFIG = SleeveConfig(
        sleeve_id="Author_anna_seven_vote_printer", family="Author", cadence_s=60, universe=DEFAULT_WATCH,
        schedule="rth,after_close+20:after_close+240",
        needs={"bars": [{"source": "equity_split", "interval": "1d", "n": 500}], "quotes": {"source": "equity"}},
        params={"title": "Historical Author seven-vote Anna printer"}, source=ANNA_SOURCE)

    def signal(self, view):
        st = dict(view.state or {})
        day = et_date(view.now)
        if not cal.is_trading_day(day):
            return []
        held = _held(view)
        intents = []
        if view.now >= cal.session_close(day):
            if st.get("printed") == day:
                return []
            daily = {s: gbars(r) for s, r in ((view.bars or {}).get("1d") or {}).items()}
            todo = {}
            reads = {}
            for s in DEFAULT_WATCH:
                bars = daily.get(s) or []
                if not bars or et_date(bars[-1]["t"] / 1000) != day:
                    continue                                   # the session's bar is not final yet
                rep = A.build_anna_replica(bars)
                if len(bars) < A.AUTHORITY_BARS or not rep:
                    continue
                cur = rep[-1]
                reads[s] = {"signal": cur["signal"], "marker": cur["marker"], "location": cur["location"]}
                if cur["signal"] == "buy" and s not in held:
                    todo[s] = {"side": "buy", "why": f"printer signal buy ({cur['marker'] or 'held buy'})"}
                elif cur["signal"] == "sell" and s in held:
                    todo[s] = {"side": "sell", "why": f"printer signal sell ({cur['marker'] or '200-day lost'})"}
            st["todo"] = {"for": cal.next_trading_day(day).isoformat(), "rows": todo}
            st["printed"] = day
            intents.append(Intent("signal", "ANNA", reason=f"anna printer {day}: " + ", ".join(
                f"{s} {r['signal']}" for s, r in sorted(reads.items())), signal_key=f"anna:{day}", meta=reads))
            self._st = st
            return intents
        if not cal.is_rth(view.now):
            return []
        todo = st.get("todo") or {}
        if todo.get("for") != day:
            return []
        slot = view.equity / len(DEFAULT_WATCH)
        for s, r in sorted((todo.get("rows") or {}).items()):
            if r.get("sent"):
                continue
            px = float(((view.quotes or {}).get(s) or {}).get("last") or 0)
            if r["side"] == "buy" and s not in held:
                if not (px > 0):
                    continue
                intents.append(Intent("enter", s, notional=float(slot), price_hint=px,
                                      signal_key=f"anna:{s}:{day}:buy", reason=f"anna: {r['why']}"))
            elif r["side"] == "sell" and s in held:
                intents.append(Intent("exit", s, signal_key=f"anna:{s}:{day}:sell", reason=f"anna: {r['why']}"))
            r["sent"] = True
        self._st = st
        return intents

    def quote_universe(self, now, book=None):
        return list(DEFAULT_WATCH)

    def update_state(self, view, intents):
        st = getattr(self, "_st", None)
        self._st = None
        return st if st is not None else dict(view.state or {})


# -- the scanner book: desk-scan.mjs (the killable scan worker) + desk-autopilot.mjs runCycle --------------------------
SCAN_N = 502                     # the scan's daily history: Yahoo's 1d chart, range 2y (~502 sessions)
SCAN_ORDER = tuple(dict.fromkeys(("SPY",) + B.REGIME_EXTRA + B.SECTOR_ETFS + STOCKS))
CYCLE_STALE_S = 600              # tickWindows: a cycle when the window changes or the last scan is >10 minutes old


def completed_session(now):
    d = cal._as_date(now)
    if not (cal.is_trading_day(d) and now >= cal.session_close(d) + 900):
        d = cal.prev_trading_day(d)
    return d


def scan_path(root):
    return os.path.join(root, "cache", "Author", "scan.json")


def build_scan(hub, now, names=SCAN_ORDER):
    """desk-scan.mjs on the last completed session: scanPrismSymbol over the universe (SPY the bench), distillBuys,
    keepAfterCurl; the bottom lane on its own (B.distill_bottom); the sector tape; the book names' bars."""
    d = completed_session(now).isoformat()
    ms = int(now * 1000)
    got = hub.bars("equity_split", "1d", list(names), SCAN_N)
    bars_by = {}
    for s in names:
        bl = [b for b in gbars(got.get(s)) if et_date(b["t"] / 1000) <= d]
        if bl:
            bars_by[s] = bl
    bench = bars_by.get("SPY") or []
    rows = []
    for s in names:
        bars = bars_by.get(s)
        rows.append(PR.scan_prism_symbol(s, bars, bench) if bars else
                    {"symbol": s, "coverage": "quarantined", "reason": "no bars", "barCount": 0, "completedBarAt": None,
                     "close": None, "episodes": []})
    dist = B.distill_buys(rows, bars_by, {}, ms)
    rejected = dist["rejected"]

    def curl_cut(setups, rej):
        out = []
        for s in setups:
            kept = B.keep_after_curl(s, bars_by.get(s["symbol"]))
            if not kept["keep"]:
                rej.append({"symbol": s["symbol"], "reason": kept["why"], "close": s["close"], "status": "LATE",
                            "scanner": s["primaryScanner"], "eventClass": s["eventClass"]})
                continue
            out.append(dict(s, fundStatus="unknown"))     # fund-io: Yahoo refuses, the SEC read finds no us_gaap
        return out
    buys = curl_cut(dist["buys"], rejected)
    bot = B.distill_bottom(bars_by, {}, ms)
    bottom = curl_cut(bot["buys"], bot["rejected"])
    keep = {s["symbol"] for s in buys + bottom} | {"SPY", "IWM"} | set(B.SECTOR_ETFS) | set(B.REGIME_EXTRA)
    return {"origin": d, "at": W.iso(now), "scanned": len(rows), "usable": dist["usable"], "buys": buys,
            "bottom": bottom, "rejected": rejected[:600], "bottomRejected": bot["rejected"][:200],
            "tape": B.read_sector_tape(bars_by, ms), "bars": {s: bars_by[s][-500:] for s in sorted(keep) if s in bars_by}}


def scan_job(engine):
    """the family's job: once per completed session (a later launch finds the scan written and returns)."""
    now = engine.clock()
    d = completed_session(now).isoformat()
    path = scan_path(engine.root)
    have = read_json(path, None) or {}
    if have.get("origin") == d:
        return {"origin": d, "skipped": "scan already written for this session"}
    doc = build_scan(engine.hub, now)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_json_atomic(path, doc)
    return {"origin": d, "scanned": doc["scanned"], "usable": doc["usable"], "buys": len(doc["buys"]),
            "bottom": len(doc["bottom"])}


_SCAN = {}


def load_scan(root):
    p = scan_path(root)
    try:
        m = os.path.getmtime(p)
    except OSError:
        return None
    if _SCAN.get("path") != p or _SCAN.get("mtime") != m:
        _SCAN.update(path=p, mtime=m, doc=read_json(p, None))
    return _SCAN.get("doc")


def current_window(now):
    """autopilot.ts currentWindow."""
    p = W.et_parts(now)
    if p["weekday"] in ("Sat", "Sun"):
        return None
    hm = p["hour"] * 60 + p["minute"]
    if 8 * 60 + 10 <= hm < 10 * 60 + 50:
        return "morning"
    if 11 * 60 + 25 <= hm < 11 * 60 + 55:
        return "midday"
    if 14 * 60 + 10 <= hm < 14 * 60 + 50:
        return "afternoon"
    return None


def five_with_quote(five, quote, now):
    """the session tape's 5-minute bars: the hub's extended-hours bars plus the forming bar from the live quote
    (loadYahooBars' 5m chart carries the forming bar)."""
    out = list(five)
    q = quote or {}
    last = q.get("last")
    if not (last and last > 0):
        return out
    t = int(math.floor(now / 300) * 300 * 1000)
    if out and out[-1]["t"] >= t:
        return out
    px = float(last)
    out.append({"t": t, "o": px, "h": px, "l": px, "c": px, "v": 0.0})
    return out


class DeskCycle:
    """runCycle's book assembly on a sleeve's own state: the scan's list (or the last booked book, or the roster's)
    -> orderBook -> filterBookForCurl -> (morning / catch-up windows) the session tape and keepNearBuy -> the desk
    book, lastBook and the roster (curateRoster on the scan's closes)."""
    KEY = "buys"

    def bind(self, engine):
        self.engine = engine

    def scan_doc(self):
        eng = getattr(self, "engine", None)
        return load_scan(eng.root) if eng is not None else None

    @staticmethod
    def cycle_due(st, now):
        win = current_window(now)
        return (win is not None and st.get("lastWindow") != win) or now - float(st.get("lastScanAt") or 0) > CYCLE_STALE_S

    def cycle_names(self, st, now):
        """the names a cycle due now stamps with the session tape (none outside the morning / catch-up windows)."""
        if not self.cycle_due(st, now) or (current_window(now) or "catchup") not in ("morning", "catchup"):
            return []
        doc = self.scan_doc() or {}
        names = [s["symbol"] for s in doc.get(self.KEY) or []]
        names += [s["symbol"] for s in (st.get("deskBook") or {}).get("setups") or []]
        names += [m["symbol"] for m in (st.get("roster") or {}).get("members") or [] if m.get("status") == "LIVE"]
        return sorted(set(names))

    def run_cycle(self, st, doc, five, quotes, now):
        win = current_window(now) or "catchup"
        ms = int(now * 1000)
        date_et = W.et_parts(now)["dateEt"]
        bars_map = (doc or {}).get("bars") or {}

        def stamp(s):
            sym = s["symbol"]
            tape = B.session_tape(five_with_quote(five.get(sym) or [], quotes.get(sym), now), ms)
            daily = live_day_bar(bars_map.get(sym) or [], quotes.get(sym), now)
            return B.apply_session_tape(s, tape, ms, daily or None)["setup"]

        def assemble(setups):
            book = B.filter_book_for_curl(B.order_book(setups), bars_map)
            if win in ("morning", "catchup"):
                book = B.keep_near_buy([stamp(s) for s in book])
            return book
        book = assemble((doc or {}).get(self.KEY) or [])
        if not book:
            book = assemble((st.get("deskBook") or {}).get("setups") or B.book_from_roster(st.get("roster"), ms))
        st["lastScanAt"] = now
        st["lastWindow"] = win
        if not book:
            return None
        st["deskBook"] = {"dateEt": date_et, "at": W.iso(now), "window": win, "setups": book}
        st["lastBook"] = [s["symbol"] for s in book]
        closes = {s: float(b[-1]["c"]) for s, b in bars_map.items() if b and b[-1].get("c")}
        seeds = [{"symbol": s["symbol"], "buy": s["plan"]["buy"], "stop": s["plan"]["stop"],
                  "target": s["plan"]["target"], "rr": s["plan"]["rr"], "close": s["close"], "call": B.buy_call(s),
                  "scanner": s.get("primaryScanner")} for s in book]
        st["roster"] = B.curate_roster(st.get("roster") or B.empty_roster(date_et), seeds, closes, date_et, ms)
        return book


class ScanBookLane(DeskCycle, Sleeve):
    """The scanner book on the paper wire: the cycle every ten minutes (and at each window), maybeBookPaper each pass
    with live quotes, runPaperExits on the sleeve's positions."""

    def __init__(self, sleeve_id, title, key, source):
        self.KEY = key
        self.engine = None
        self._last_state = None
        self._st = None
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="Author", cadence_s=60, universe=(), schedule="ext",
            needs={"bars": [{"source": "yahoo_ext", "interval": "5m", "n": 400, "symbols_for": "five"},
                            {"source": "equity_split", "interval": "1d", "n": 300, "symbols_for": "held"}],
                   "quotes": {"source": "equity"}},
            params={"title": title, "list": key}, source=source)

    def bar_symbols(self, need, now, book=None):
        if need.get("symbols_for") == "held":
            return _book_syms(book)
        return self.cycle_names(self._last_state or {}, now)

    def quote_universe(self, now, book=None):
        st = self._last_state or {}
        names = set(_book_syms(book)) | {s["symbol"] for s in (st.get("deskBook") or {}).get("setups") or []}
        names |= {s["symbol"] for s in (self.scan_doc() or {}).get(self.KEY) or []}
        return sorted(names)

    def signal(self, view):
        st = dict(view.state or {})
        self._last_state = st
        parts = W.et_parts(view.now)
        if parts["weekday"] in ("Sat", "Sun"):
            return []
        quotes = _quotes(view)
        intents = []
        doc = self.scan_doc()
        if self.cycle_due(st, view.now):
            five = {s: gbars(r) for s, r in ((view.bars or {}).get("5m") or {}).items()}
            book = self.run_cycle(st, doc, five, quotes, view.now)
            names = [s["symbol"] for s in book or []]
            key = f"{parts['dateEt']}:{','.join(names)}"
            if book and st.get("bookKey") != key:
                st["bookKey"] = key
                intents.append(Intent("signal", "Author", reason=f"{self.CONFIG.sleeve_id}: book "
                                      f"{st['deskBook']['window']} {parts['dateEt']} — {', '.join(names[:12])}",
                                      signal_key=f"{self.CONFIG.sleeve_id}:book:{key}"[:200],
                                      meta={"origin": (doc or {}).get("origin"),
                                            "setups": [{k: s.get(k) for k in ("symbol", "plan", "tier", "size",
                                                                              "primaryScanner")} for s in book]}))
        ms = int(view.now * 1000)
        if not T.is_signal_session(T.classify_session(ms)):
            self._st = st
            return intents
        held = _held(view)
        wire = W.Wire(self.CONFIG.sleeve_id, st, view.now, view.equity, held, quotes,
                      trades=(view.extra or {}).get("closed_trades"))
        daily = {s: gbars(rows) for s, rows in ((view.bars or {}).get("1d") or {}).items()}
        bars_map = (doc or {}).get("bars") or {}

        def tape(sym):
            return live_day_bar(daily.get(sym) or bars_map.get(sym) or [], quotes.get(sym), view.now)
        wire.exits(parts["dateEt"], parts["hour"], parts["minute"], ms, tape)
        W.book_paper(wire, st.get("deskBook") or {}, parts["dateEt"], parts["hour"], parts["minute"])
        st.update(wire.state())
        self._st = st
        return intents + wire.intents

    def update_state(self, view, intents):
        st = getattr(self, "_st", None)
        self._st = None
        return st if st is not None else dict(view.state or {})


# -- Echo: scripts/echo-sidecar.mjs (the @EchoAnalysis posts) ------------------------------------------------------------
ECHO_SOURCE = dict(SOURCE, path="scripts/echo-sidecar.mjs", blob_sha="7293ee38a37aa7ed7df572d1928e4658085f9b6c")
ECHO_FEEDS = EC.FEEDS + ("https://nitter.poast.org/EchoAnalysis/rss", "https://xcancel.com/EchoAnalysis/rss")
ECHO_POLL_S = 180                # the sidecar's POLL_MS
ECHO_PAPER_KEEP = 80


def echo_path(root):
    return os.path.join(root, "cache", "Author", "echo_feed.json")


def fetch_echo_feed(now, get=None):
    """fetchFeed: each mirror in order, the first whose RSS carries posts wins (a challenge page carries none). A
    malformed pubDate throws out of parseRss, failing the sweep as it did in the source."""
    if get is None:
        from ...data import http

        def get(url):
            return http.get(url, tries=1, timeout=15, as_text=True, headers={"User-Agent": "Mozilla/5.0",
                                                                             "Accept": "application/rss+xml, */*"})
    for url in ECHO_FEEDS:
        try:
            xml = get(url) or ""
        except Exception:
            xml = ""
        items = EC.parse_rss(xml, int(now * 1000)) if xml else []
        if items:
            return {"source": url, "items": items}
    return {"source": None, "items": []}


def echo_job(engine):
    """the family's job: one sweep of the feed every three minutes, written where the Echo sleeve reads it."""
    now = engine.clock()
    try:
        feed = fetch_echo_feed(now)
    except ValueError as e:
        feed = {"source": None, "items": [], "error": str(e)}
    path = echo_path(engine.root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_json_atomic(path, dict(feed, at=now))
    return {"source": feed["source"], "items": len(feed["items"]), "error": feed.get("error")}


def echo_reads(daily):
    """paperEcho's vs21 / ret5 on the daily closes."""
    closes = [float(b["c"]) for b in daily if float(b["c"]) > 0]
    vs21 = ret5 = None
    if len(closes) >= 6:
        last, prev5 = closes[-1], closes[-6]
        if last and prev5:
            ret5 = (last - prev5) / prev5
        if len(closes) >= 21:
            k = 2 / 22
            ema = lsum(closes[:21], 0) / 21
            for c in closes[21:]:
                ema = c * k + ema * (1 - k)
            vs21 = (last - ema) / ema
    return vs21, ret5


class EchoSwing(Sleeve):
    """runEchoSweep: each new post classified (classifyEcho); a filled buy / add the first time it is read ->
    paperEcho (echoPaperGate on the live mark, vs21 and ret5) -> an Echo ticket (paperStop / paperTarget, the swing
    manager after); runPaperExits on the sleeve's positions."""
    CONFIG = SleeveConfig(
        sleeve_id="Author_echo_swing", family="Author", cadence_s=60, universe=(), schedule="always",
        needs={"bars": [{"source": "equity_split", "interval": "1d", "n": 300, "symbols_for": "names"}],
               "quotes": {"source": "equity"}},
        params={"title": "Echo post-derived buy/add swing", "feeds": list(ECHO_FEEDS)}, source=ECHO_SOURCE)

    def __init__(self):
        self.engine = None
        self._last_state = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def feed(self):
        if self.engine is None:
            return None
        return read_json(echo_path(self.engine.root), None)

    def _names(self, book):
        st = self._last_state or {}
        return sorted(set(_book_syms(book)) | {p["call"]["symbols"][0] for p in st.get("pending") or []})

    def bar_symbols(self, need, now, book=None):
        return self._names(book)

    def quote_universe(self, now, book=None):
        return self._names(book)

    def signal(self, view):
        st = dict(view.state or {})
        self._last_state = st
        feed = self.feed()
        ledger = st.get("echo")
        if feed and feed.get("at") != st.get("feedAt"):
            st["feedAt"] = feed.get("at")
            backfill = ledger is None                          # the sidecar's first sweep: once(true)
            ledger = dict(ledger or {"seen": {}, "papers": []})
            seen = dict(ledger["seen"])
            pending = list(st.get("pending") or [])
            for item in feed.get("items") or []:
                if item["id"] in seen:
                    continue
                call = EC.classify_echo(item["text"])
                seen[item["id"]] = item["at"]
                if not backfill and call["paper"]:
                    pending.append({"id": item["id"], "at": item["at"], "call": call, "text": item["text"][:280],
                                    "readAt": view.now})
            ledger["seen"] = dict(list(seen.items())[-2000:])
            st["echo"] = ledger
            st["pending"] = pending
            self._last_state = st
        parts = W.et_parts(view.now)
        weekday = parts["weekday"] not in ("Sat", "Sun")
        quotes = _quotes(view)
        held = _held(view)
        wire = W.Wire(self.CONFIG.sleeve_id, st, view.now, view.equity, held, quotes,
                      trades=(view.extra or {}).get("closed_trades"))
        daily = {s: gbars(r) for s, r in ((view.bars or {}).get("1d") or {}).items()}
        papers = list((st.get("echo") or {}).get("papers") or [])
        on_disk = list(papers)                    # paperEcho reads the ledger as the last sweep wrote it
        left = []
        for p in st.get("pending") or []:
            sym = p["call"]["symbols"][0]
            q = quotes.get(sym)
            if q is None and view.now - p["readAt"] < 180:
                left.append(p)                                  # the name's quote arrives on the next pass
                continue
            row = self.paper_echo(wire, p, sym, q, daily.get(sym) or [], weekday, parts, on_disk, view.now)
            papers.insert(0, {"id": p["id"], "symbol": sym, "kind": p["call"]["kind"],
                              "status": (row or {}).get("status") or "held", "reason": (row or {}).get("reason") or "",
                              "dateEt": parts["dateEt"], "at": W.iso(view.now)})
        if "echo" in st:
            st["echo"] = dict(st["echo"], papers=papers[:ECHO_PAPER_KEEP])
        st["pending"] = left
        if weekday and T.is_signal_session(T.classify_session(int(view.now * 1000))):
            def tape(sym):
                return live_day_bar(daily.get(sym) or [], quotes.get(sym), view.now)
            wire.exits(parts["dateEt"], parts["hour"], parts["minute"], int(view.now * 1000), tape)
        st.update(wire.state())
        self._st = st
        return wire.intents

    @staticmethod
    def paper_echo(wire, post, symbol, quote, daily, weekday, parts, papers, now):
        if not weekday:
            return {"status": "held", "reason": "weekend — no Echo paper", "symbol": symbol}
        px = float((quote or {}).get("last") or 0)
        if not (px > 0):
            return {"status": "held", "reason": "no quote", "symbol": symbol}
        bought_today = any(p["symbol"] == symbol and p["status"] == "sent" and p["dateEt"] == parts["dateEt"]
                           for p in papers)
        vs21, ret5 = echo_reads(live_day_bar(daily, quote, now))
        kind = post["call"]["kind"]
        gate = EC.echo_paper_gate(weekday, parts["hour"], parts["minute"], kind, bought_today, False, px, vs21=vs21,
                                  ret5=ret5)
        if not gate["ok"]:
            return {"status": "held", "reason": gate["reason"], "symbol": symbol}
        bar_at = B._parse_iso_ms(post["at"]) or int(now * 1000)
        return wire.ticket(symbol, "buy", "ECHO_ADD" if kind == "ADD" else "ECHO_BUY", px, px, P.paper_stop(px, 0),
                           P.paper_target(px), "BUY", bar_at, parts["dateEt"], parts["hour"], parts["minute"],
                           eligible=True, echoTicket=True, echoAdd=kind == "ADD", weekend=not weekday)

    def update_state(self, view, intents):
        st = getattr(self, "_st", None)
        self._st = None
        return st if st is not None else dict(view.state or {})


def sleeves():
    return [KomarMomentum(), AnnaPrinter(), NextSupportPlan(), WashoutCoil(), EchoSwing(),
            ScanBookLane("Author_scanner_book_swing", "Scanner-book structural swing", "buys",
                         dict(SOURCE, path="src/lib/workdesk/buy-desk.ts",
                              blob_sha="b55128ddff2ca45e22d6ab35dd0956d6d3761295")),
            ScanBookLane("Author_sector_first_bottom", "Sector-first bottom recovery", "bottom",
                         dict(SOURCE, path="src/lib/workdesk/bottom-screen.ts",
                              blob_sha="a929d9f2a3615250fedbcd9d49f9f23d1b19f760"))]


# named Authordesk_* (the Author-desk repo): the Author_* job names are the Author_producers family's Lazarus slots
JOBS = {"Authordesk_scan": ("always", 1800, scan_job), "Authordesk_echo": ("always", ECHO_POLL_S, echo_job)}
