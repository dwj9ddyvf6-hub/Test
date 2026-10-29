"""Ausar R19 options: 30 independent option books (family ausar_options; the source's 6 unfunded monitor cards,
monitor_only with no capital and no order authority, were removed from the desk with their rows, the owner,
2026-10-26). The vendored, hash-pinned evaluator decides every entry, exit and size:
desk/vendor/ausar_r19/r19_options.py (agentic-trading-desk@1720157f, blob 3c7f3be9) reading its frozen book
definitions desk/vendor/strategies/r19/options_rules.json (blob 6e2aa298 — every book's config_sha256 equals the
Ausar registry receipt's). This wrapper only builds the evaluator's snapshot and book from this desk's data and the
sleeve's own virtual book, and carries out the package intents it returns — the obligations of the source runtime
(r19_cli / r19_option_data / r19_core):

  * one evaluation per 30 s pass in the regular session (the source worker's 30 s cycle);
  * snapshot = the source collector's shape (r19_data._calendar + r19_option_data.enrich_snapshot):
      calendar   NYSE sessions now-1700d .. now+390d, session / open / close / is_open, previous_session,
                 previous_session_by_date, option_close_by_date, first_session_of_week, weekly_PM_expiry;
      daily_bars completed native daily bars (raw = split-only adjusted closes) for the book's underlyings,
                 sessions strictly before today, usable at their session close;
      option_contracts / option_quotes  the desk's option chain (desk/data/options.py) for the underlyings the
                 book can enter, over the book's DTE window, and live quotes for every owned leg;
      underlying_quotes  the desk's equity quote (bid / ask) of each underlying;
      option_fees  the frozen R19 paper assumption $0.65 per contract per fill (r19_option_data
                 DEFAULT_PAPER_OPTION_FEES) — used by the evaluator's sizing and admission, as in the source;
  * book = the sleeve's own book: cash, NAV (cash + equities at the bid + packages at natural liquidation),
    package positions rebuilt from the held contracts (their position_meta is the source's package metadata
    from prepare_package at the decision), the frozen entry-attempt ledger (option_entry_attempts) and the
    filled-package outcomes that consume an event;
  * package intents -> engine intents at the evaluator's natural price: a one-leg package is a single option
    order (asset option) with a limit at the natural (ask to open, bid to close); a vertical is one mleg
    package (debit > 0 / credit < 0) with the natural net as its limit; the QQQ core of the two core_reserve
    books is an equity buy at the ask with the frozen 15 bps fee (cost_bps). Entries expire at the evaluator's
    own deadline (expires_at: 09:40 / 09:45 / 10:05 ET); unfilled children expire after 60 s and the next pass
    re-prices the same frozen attempt (the source re-ran prepare_package at each cycle's BBO).

Books (sleeve id = ausar_ + lower(id)):
  recovery (16) OPT_RSI2_* / OPT_VWAP20_*: IWM, QQQ, SPY in that order; previous session close > SMA200 and
     Wilder RSI2 < 10 (or close <= 98% of the 20-session VWAP); long 14-21 DTE .50-.60 delta call or +2% call
     vertical; .5% / 2% NAV risk, 5% initial-NAV outstanding cap; exit 15:55 of the 5th session, the
     15:45 pre-expiry guard, and (touch arms) a bid >= 1.02 x entry spot.
  core_reserve (2) OPT_QQQ95_RSI2_*: a 95% QQQ core bought once, then the RSI2 touch overlay from the rest.
  pead (4), xsp_pcs (4), opening_gamma (2), tensor_leaps (2): the same evaluator on event inputs the source
     runtime never produced (its books stayed blocked); each producer computes the research definition of the
     input (binding update 2026-10-16: no book stays BLOCKED for a missing producer):
       xsp_pcs       xsp_state: native XSP weekly bars (W-FRI weeks of the S&P 500 sessions / 10, 260 weeks), the
                     adjacent-put pair of the digital (this week's PM-expiry put nearest prior close - 1 ATR and
                     the next lower listed strike), prior-week digitals (the PCS research series, then the book's
                     own weekly readings); the index-inclusive fee schedule (N8); settlement by the engine (N6);
       opening_gamma opening_reversal_events: the prior afternoon's R5 events (recorded 20 minutes after each
                     close: last-two-hours return in the top quintile of its trailing 252 sessions, the R5 / R18
                     coverage definition and 41-symbol universe) + today's completed first 5-minute bar + the
                     observed price;
       pead          earnings_events + earnings_history from the PEAD producer (desk/feedlib/ausar_pead.py, job
                     ausar_pead): Nasdaq's earnings calendar (the research's source) observed ahead, surprises
                     resolved on the desk's daily bars, >= 200 prior-four-quarter events;
       tensor_leaps  tensor_G4_events / tensor_G4_exit_events: the source's own bridge (r19_tensor.attach_G4_events)
                     as published by the R19 tensor port's acquisition cycle (feed r19_tensor_snapshot).

Removed (desk-wide / runtime gates, not strategy rules): the runtime's book enable / pause_entries switch and
the global entry-quote denial throttle (r19_option_data._ENTRY_DENIALS). Kept: every rule of the evaluator.

Named divergences (plumbing of the source runtime, each counted in the parity receipt):
  N1 feed attestation: the evaluator requires OPRA option / SIP underlying quotes with market/receipt clocks
     (<= 10 s / 5 s, legs within 2 s), receipt hashes, provider contract ids, verified OCC deliverables,
     timestamped Greeks, a complete chain census and a verified dividend/exercise calendar. Here the desk's
     option chain (Alpaca indicative or CBOE delayed) and equity quote (Alpaca IEX) are the decision inputs,
     stamped with the decision clock; a contract is a standard 100-share deliverable when its OCC root is the
     underlying (adjusted series carry other roots and stay excluded by the evaluator's own root check); the
     chain is the desk's full chain (legacy complete_option_chains path); exercise_checks carry no assignment
     alert (the source had no producer either). Orders execute at the paper broker's live market.
  N2 displayed size: the desk's option rows carry no displayed size, so the evaluator's displayed-size cap and
     every-leg size check see an unbounded size (a row that does carry bid_size / ask_size is honoured).
  N3 execution: the source filled a package atomically at the natural BBO in its own ledger; here the engine
     routes the package (single option or mleg) with the natural as its limit, re-priced every pass.
  N4 accounting: proceeds settle immediately (the source's T+1 claim), option fees are the engine's
     per-contract schedule (the frozen $0.65 stays in the sizing), marks are the engine's mid marks.
  N5 calendar: the desk's NYSE rule calendar is always verified (the source's settlement table covered
     2022-2026 only, after which it would refuse every entry).
  N6 settlement: an expiring contract is settled by the engine (OCC auto-exercise / index cash settlement),
     not by the evaluator's 'settle' action (XSP is BLOCKED in any case).
  N7 in-flight entries: an entry still working at the broker is the book's one package in flight — a
     different package is not routed until it fills or expires (the source executed atomically, so it never
     had two in flight).
  N8 XSP fees: index_fee_included at $0.72 per contract per fill — the frozen $0.65 plus Cboe's customer XSP
     transaction fee $0.07 (Cboe Options Fees Schedule effective 2026-10-01; the $0.30 rebate on orders under
     10 contracts is not credited). The source's schedule excluded index fees and refused every XSP package.
  N9 XSP inputs: the weekly bars are the S&P 500 daily sessions / 10 (Yahoo ^GSPC; the source wanted a native
     XSP tape); the XSP spot is Cboe's delayed XSP index value; the prior-week digitals are the research series
     (SPXW (mid(K) - mid(K-5)) / 5 at the -1 ATR level, Monday <= 10:00, 2012-06 .. 2026-08-07, five nonpositive
     readings dropped) followed by the book's own first valid reading in each week's 10:00-10:05 window on XSP's
     adjacent $1 strikes — the weeks from 2026-08-14 to installation have no free source and are absent.
  N10 opening-gamma inputs: the R5 history is seeded from the R18 coverage lane's own 30-minute bars through
     2026-10-02 (derived/r5_last2h_seed.json, tools/ausar_r5_seed.py) and continued from the desk's 30-minute
     bars (Alpaca SIP adjustment=all when keyed, as the research; Yahoo otherwise); R5_received_at is the pass
     that recorded it after the close; the first 5-minute bar is Yahoo's (SIP is 15 minutes late on the free
     plan); the break is the mid of the desk's equity quote; the event clocks are the decision pass (N1).
  N11 PEAD inputs: announcement_at is the calendar bucket's bound (after-hours 16:00 ET of the event date, else
     00:00 ET), first_published_at the producer's first observation of the row (a backfilled history event:
     the bound); the universe is the calendar's 1-5 letter tickers that are active tradable Alpaca equities
     (keyless: the ticker test alone); the books receive the producer's pre-evaluated passing events (the same
     vendored build_pead_event / pead_signal on the same bars), so bars, quotes and chains are fetched for those.
  N12 G4 bridge: the events come from the R19 tensor port's cycle; its exit events cover the R19 tensor books'
     own positions (attach_G4_events(snapshot, books)), so these books exit on their saved original deadline or
     the 365-day checkpoint — the evaluator's own rules — while the feed is absent the books simply see no
     event.
  N13 XSP venue: Alpaca lists no index options, so XSP packages (entries and exits, single or multi-leg) are
     pinned to the labelled sim venue sim:options, filled on CBOE's delayed XSP chain in every desk mode."""
import csv
import hashlib
import json
import math
import os
from datetime import date, datetime, time as dtime, timedelta, timezone
from decimal import Decimal

from ... import calendar as cal
from ...contract import Intent, Leg, OrderSpec, Sleeve, SleeveConfig
from ...data.options import occ_parse, underlying_of
from ...feedlib import ausar_pead
from ...util import ET, et_date
from ...vendor.ausar_r19 import r19_options as vo

SOURCE = {"repo": "agentic-trading-desk", "ref": "aurelia-paper-desk", "commit": "1720157f768e63ebe76b148aa3d7d1a409ac9673",
          "path": "ausar-archive/ausar-receiver/original-payload/desk-source/backend/r19_options.py",
          "blob": "3c7f3be9579b93e0dd06b153e61df06fae4cf047",
          "rules_path": "ausar-archive/ausar-receiver/original-payload/desk-source/strategies/r19/options_rules.json",
          "rules_blob": "6e2aa298d8f6268a3b82f36f250255d9b045fc2c"}
# r19_option_data.DEFAULT_PAPER_OPTION_FEES (frozen R19 paper assumption)
OPTION_FEES = {"per_contract_per_fill": "0.65", "explicit_paper_assumption": True,
               "version": "R19_ETF_065_per_contract_side_v1", "index_fee_included": False}
UNBOUNDED_SIZE = 10 ** 9                  # N2: a row without a displayed size
ORDER_WINDOW_S = 60.0                     # N3: an unfilled child expires; the next pass re-prices the attempt
QUIET_BLOCKERS = ("outside_options_entry_window", "option_market_closed", "outside_XSP_weekly_entry_window")
UTC = timezone.utc
RESEARCH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                        "ausar_research")
# N8: XSP is an index option — the frozen $0.65 per contract per fill plus Cboe's customer XSP transaction fee
# ($0.07 per contract for orders of 10 contracts or more; the $0.30 rebate on smaller orders is not credited),
# Cboe Options Fees Schedule effective October 1, 2026 (cdn.cboe.com/resources/membership/Cboe_FeeSchedule.pdf,
# sha256 a5538f56...ff1c, "XSP, MRUT, DJX {CC} $0.07 >=10 contracts / {XC} ($0.30) <10 contracts").
XSP_FEES = {"per_contract_per_fill": "0.72", "explicit_paper_assumption": True,
            "version": "R19_ETF_065_plus_Cboe_XSP_customer_007_v1", "index_fee_included": True}
XSP_WEEKS = 260                           # weekly bars handed to the Wilder ATR14 (long warm-up, as the research)
SIM_INDEX_ROOTS = ("XSP",)                # N13: index options Alpaca does not list trade on the options sim venue
SIM_INDEX_VENUE = "sim:options"
DIGITALS_BLOB = "1b8eb4f39c162c903ea67e2d3d6565f5e9ea0cd4"


def iso(ts):
    return datetime.fromtimestamp(float(ts), tz=UTC).isoformat()


def _sha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def sleeve_id(cfg):
    return ("mon_" if cfg.get("monitor_only") else "ausar_") + cfg["id"].lower()


def entry_window(family):
    """the evaluator's own entry clock (r19_options._evaluate / evaluate)."""
    if family == "xsp_pcs":
        return (10, 0), (10, 5)
    return (9, 35), ((9, 45) if family == "opening_gamma" else (9, 40))


# -- the source collector's calendar block ------------------------------------------------------------
_CAL = {}


def session_calendar(now):
    """r19_data._calendar + r19_option_data.enrich_snapshot's calendar keys, on the desk's NYSE calendar (N5)."""
    nowdt = datetime.fromtimestamp(float(now), tz=UTC)
    day = nowdt.astimezone(ET).date()
    start, end = (nowdt - timedelta(days=1700)).date(), (nowdt + timedelta(days=390)).date()
    key = (day.isoformat(), start.isoformat(), end.isoformat())
    base = _CAL.get(key)
    if base is None:
        session = day if cal.is_trading_day(day) else cal.prev_trading_day(day)
        sessions, d = [], start
        while d <= end:
            if cal.is_trading_day(d):
                sessions.append(d.isoformat())
            d += timedelta(days=1)
        today = session.isoformat()
        week = session.isocalendar()[:2]
        week_sessions = [x for x in sessions if datetime.fromisoformat(x).date().isocalendar()[:2] == week]
        previous = [x for x in sessions if x < today]
        upcoming = cal.next_trading_day(day) if not cal.is_trading_day(day) else day
        base = {"session": today, "open": iso(cal.session_open(session)), "close": iso(cal.session_close(session)),
                "verified": True, "exchange": "XNYS", "next_session": upcoming.isoformat(),
                "all_sessions": sessions, "future_sessions": [x for x in sessions if x >= today],
                "previous_session": previous[-1] if previous else None,
                "previous_session_by_date": {x: sessions[n - 1] for n, x in enumerate(sessions) if n},
                "option_close_by_date": {x: iso(cal.session_close(x)) for x in sessions},
                "first_session_of_week": bool(week_sessions and today == week_sessions[0]),
                "weekly_PM_expiry": week_sessions[-1] if week_sessions else None,
                "_open_ts": cal.session_open(session), "_close_ts": cal.session_close(session)}
        _CAL.clear()
        _CAL[key] = base
    c = {k: v for k, v in base.items() if not k.startswith("_")}
    c["is_open"] = bool(base["_open_ts"] <= float(now) < base["_close_ts"])
    if c["is_open"] is False and float(now) >= base["_close_ts"] and c["next_session"] == c["session"]:
        c["next_session"] = cal.next_trading_day(c["session"]).isoformat()
    return c


def daily_rows(bars, today):
    """desk daily bars -> the source's daily_bars rows: completed native sessions strictly before `today`."""
    out, prev = [], None
    for b in bars or []:
        d = cal._as_date(float(b["t"]) + 12 * 3600)
        s = d.isoformat()
        if s >= today or not cal.is_trading_day(d) or (prev is not None and s <= prev):
            continue
        prev = s
        out.append({"session": s, "close": b["c"], "high": b["h"], "low": b["l"], "volume": b.get("v") or 0,
                    "usable_after": iso(cal.session_close(d)), "complete": True,
                    "source_sha256": _sha([s, b["o"], b["h"], b["l"], b["c"], b.get("v")])})
    return out


def _strike(k):
    v = float(k)
    return str(int(v)) if v == int(v) else repr(v)


def contract_of(row, stamp):
    """a desk chain row -> the evaluator's option contract (N1: standard deliverable when root == underlying)."""
    occ = row["symbol"]
    root, exp, cp, k = occ_parse(occ)
    under = row.get("underlying") or underlying_of(occ)
    european = root == "XSP" and under == "XSP"
    c = {"symbol": occ, "contract_id": "OCC:" + occ, "root": root, "underlying": under, "expiry": exp,
         "strike": _strike(k), "right": cp, "multiplier": 100, "status": "active", "tradable": True,
         "exercise_style": "european" if european else "american",
         "settlement": "cash_PM" if european else "physical",
         "deliverable": ({"shares": 0, "cash_settlement_multiplier": 100, "settlement_index": "XSP"} if european
                         else {"shares": 100, "cash": 0}),
         "deliverable_verified": True, "deliverable_source_sha256": _sha(["standard_deliverable", occ]),
         "delta": row.get("delta"), "greeks_market_at": stamp, "greeks_received_at": stamp}
    if european:
        c["deliverable_schema"] = "aster-option-deliverable-v1"
    return c


def option_quote(occ, q, stamp):
    """a desk option quote -> the evaluator's OPRA quote (N1 clocks / N2 sizes); None without a two-sided book."""
    if not q or q.get("bid") is None or q.get("ask") is None:
        return None
    return {"symbol": occ, "bid": q["bid"], "ask": q["ask"],
            "bid_size": int(q["bid_size"]) if q.get("bid_size") is not None else UNBOUNDED_SIZE,
            "ask_size": int(q["ask_size"]) if q.get("ask_size") is not None else UNBOUNDED_SIZE,
            "market_at": stamp, "received_at": stamp, "feed": "opra",
            "source_sha256": _sha([occ, q.get("bid"), q.get("ask"), q.get("t")])}


def underlying_quote(sym, q, stamp):
    """the desk's equity quote -> the evaluator's consolidated underlying quote (N1); None without bid / ask."""
    if not q or not q.get("bid") or not q.get("ask"):
        return None
    return {"symbol": sym, "bid": q["bid"], "ask": q["ask"],
            "bid_size": int(q["bid_size"]) if q.get("bid_size") is not None else UNBOUNDED_SIZE,
            "ask_size": int(q["ask_size"]) if q.get("ask_size") is not None else UNBOUNDED_SIZE,
            "market_at": stamp, "received_at": stamp, "feed": "official_index" if sym == "XSP" else "sip",
            "source_sha256": _sha([sym, q.get("bid"), q.get("ask"), q.get("t")]), "actions_verified": True}


def packages(view):
    """the sleeve's book -> (source positions {PKG: {quantity, metadata}} + equities, {PKG: [OCC legs]})."""
    held, eq = {}, {}
    for inst, p in (view.positions or {}).items():
        m = p.get("meta") or {}
        q = float(p["qty"])
        if inst.startswith("OPT:") and m.get("ausar_package"):
            e = held.setdefault(m["ausar_package"], {"meta": m.get("position_meta") or {}, "legs": {}})
            e["legs"][inst[4:]] = q
        elif inst.startswith("EQ:") and q > 0:
            eq[inst[3:]] = {"symbol": inst[3:], "quantity": str(q), "metadata": dict(m.get("position_meta") or {})}
    out, legs = dict(eq), {}
    for pkg, e in held.items():
        mlegs = e["meta"].get("legs") or []
        if not mlegs:
            continue
        n = min(abs(e["legs"].get(l["symbol"], 0.0)) / max(1, abs(int(l["ratio"]))) for l in mlegs)
        if n <= 1e-9:
            continue
        out[pkg] = {"symbol": pkg, "quantity": str(int(math.ceil(n - 1e-9))), "metadata": e["meta"]}
        legs[pkg] = [l["symbol"] for l in mlegs]
    return out, legs


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


# -- XSP producer (OPT_XSP_*) ----------------------------------------------------------------------------------------
_DIGITALS = []


def research_digitals():
    """the PCS research's weekly series (pcs-research code/sim_calm_filter.implied_digitals, vendored
    implied_digital_atr100.csv): each week's first-session ~10:00 ET implied digital P(settle < K) at the -1 ATR
    strike, (mid(K) - mid(K-5)) / 5 on SPXW, available from entry_d 10:00 ET. A reading outside (0, 1) is dropped:
    the evaluator rejects any, and the research's own hygiene note calls nonpositive digitals quote noise to reject
    live (5 of 658 rows)."""
    if not _DIGITALS:
        with open(os.path.join(RESEARCH, "implied_digital_atr100.csv")) as f:
            for r in csv.DictReader(f):
                if not Decimal(0) < Decimal(r["implied"]) < Decimal(1):
                    continue
                at = datetime.combine(date.fromisoformat(r["entry_d"]), dtime(10, 0), tzinfo=ET)
                _DIGITALS.append({"week_end": r["week_end"], "value": r["implied"], "available_at": at.isoformat(),
                                  "source_sha256": DIGITALS_BLOB, "origin": "research"})
    return [dict(x) for x in _DIGITALS]


def xsp_weekly_bars(daily, session, weeks=XSP_WEEKS):
    """S&P 500 daily sessions (Yahoo ^GSPC, completed) / 10 -> native XSP weekly bars: W-FRI weeks (open first, high
    max, low min, close last), week_end = the week's last session, every week before `session`'s week, usable 15
    minutes after the week_end close (when its daily bar is final)."""
    this_week = date.fromisoformat(session).isocalendar()[:2]
    out = []
    for b in daily or []:
        d = cal._as_date(float(b["t"]) + 12 * 3600)
        s = d.isoformat()
        wk = d.isocalendar()[:2]
        if s >= session or wk >= this_week or not cal.is_trading_day(d):
            continue
        px = [Decimal(repr(float(b[k]))) / 10 for k in ("o", "h", "l", "c")]
        row = [s] + [str(x) for x in px]
        if out and out[-1]["_wk"] == wk:
            w = out[-1]
            if s <= w["week_end"]:
                continue
            w["high"], w["low"], w["close"], w["week_end"] = max(w["high"], px[1]), min(w["low"], px[2]), px[3], s
            w["_rows"].append(row)
        else:
            out.append({"_wk": wk, "open": px[0], "high": px[1], "low": px[2], "close": px[3], "week_end": s,
                        "_rows": [row]})
    return [{"week_end": w["week_end"], "open": str(w["open"]), "high": str(w["high"]), "low": str(w["low"]),
             "close": str(w["close"]), "complete": True,
             "usable_after": iso(cal.session_close(w["week_end"]) + 900), "source_sha256": _sha(w["_rows"])}
            for w in out[-weeks:]]


def xsp_state(snap, daily, recorded):
    """the evaluator's xsp_state: completed native weekly bars, the prior-week digital observations (the research
    series, then the book's own weekly readings) and the adjacent-put pair of the digital — the put of this week's
    PM expiry nearest the prior close - 1 ATR (the research's K) and the next lower listed strike."""
    c = snap["calendar"]
    bars = xsp_weekly_bars(daily, c["session"])
    research = research_digitals()
    weeks = {x["week_end"] for x in research}            # a research week keeps its research reading
    state = {"weekly_bars": bars, "prior_digitals": research + [dict(x) for x in recorded or [] if x["week_end"] not in weeks],
             "adjacent_put_symbols": [], "usable_after": max([b["usable_after"] for b in bars] or [iso(0)])}
    try:
        atr, prior = vo._weekly_atr14(bars, vo.stamp(snap["now"]), c["session"])
        target = prior - atr
        puts = [x for x in snap["option_contracts"] if x.get("underlying") == "XSP" and x.get("right") == "put"
                and x.get("expiry") == c["weekly_PM_expiry"]]
        k = min(puts, key=lambda x: (abs(Decimal(x["strike"]) - target), x["symbol"]))
        w = max((x for x in puts if Decimal(x["strike"]) < Decimal(k["strike"])), key=lambda x: Decimal(x["strike"]))
        state["adjacent_put_symbols"] = [w["symbol"], k["symbol"]]
    except (ValueError, KeyError, TypeError, ArithmeticError):
        pass
    state["source_sha256"] = _sha([[b["source_sha256"] for b in bars], state["adjacent_put_symbols"],
                                   [[x["week_end"], x["value"]] for x in state["prior_digitals"]]])
    return state


def xsp_reading(snap, state):
    """this week's executable digital (the evaluator's own _xsp_digital on the adjacent puts) as next weeks' prior
    observation; None when it cannot be computed or lies outside (0, 1)."""
    try:
        v = vo._xsp_digital(snap, state, vo.stamp(snap["now"]))
    except (ValueError, KeyError, TypeError, ArithmeticError):
        return None
    if not Decimal(0) < v < Decimal(1):
        return None
    qs = [snap["option_quotes"][s] for s in state["adjacent_put_symbols"]]
    return {"week_end": snap["calendar"]["weekly_PM_expiry"], "value": str(v), "available_at": snap["now"],
            "source_sha256": _sha([[q["symbol"], q["bid"], q["ask"]] for q in qs]), "origin": "desk"}


# -- opening-reversal producer (OPT_OPENING_GAMMA_*) ---------------------------------------------------------------
R5_MIN_OBS, R5_TRAIL, R5_PCT = 126, 252, 0.80    # run_r5_overnight_gap_long: MIN_OBS, TRAIL, top quintile
R5_DELAY_MIN = 20                                 # after the close: the 15:30 bar is final (SIP: 16 min delay)
_R5_SEED = {}


def r5_universe():
    """the R5 universe: every symbol of the stop-tolerance bar set (bars_manifest.json) but SIVEF, which R5 itself
    skips (a SEK listing without US bars)."""
    with open(os.path.join(RESEARCH, "r5_universe_bars_manifest.json")) as f:
        return sorted(s for s in json.load(f) if s != "SIVEF")


R5_UNIVERSE = r5_universe()


def r5_seed():
    """{symbol: [[session, last2h], ...]}: the R5 statistic of the R18 coverage lane's 30-minute bars (Alpaca SIP,
    adjustment=all) through 2026-10-02, last 300 sessions (derived/PROVENANCE.json, tools/ausar_r5_seed.py)."""
    if not _R5_SEED:
        with open(os.path.join(RESEARCH, "derived", "r5_last2h_seed.json")) as f:
            _R5_SEED.update(json.load(f))
    return _R5_SEED


def last2h_by_session(bars30):
    """run_r5_overnight_gap_long.last2h on 30-minute bars: close(15:30 bar) / close(13:30 bar) - 1 per ET session."""
    by = {}
    for b in bars30 or []:
        t = datetime.fromtimestamp(float(b["t"]), tz=ET)
        by[(t.date().isoformat(), t.strftime("%H:%M"))] = b
    out = {}
    for d in sorted({d for d, _ in by}):
        b16, b14 = by.get((d, "15:30")), by.get((d, "13:30"))
        if not b16 or not b14:
            continue
        c16, c14 = _num(b16.get("c")), _num(b14.get("c"))
        if not c16 or not c14 or c16 <= 0 or c14 <= 0:
            continue
        out[d] = c16 / c14 - 1
    return out


def r5_events(bars30_by_symbol, session):
    """the R5 events of `session` (research: an event iff the day's last2h >= the linear 80th percentile of the
    trailing 252 prior values, with at least 126 of them): seed history + the desk's 30-minute bars after it."""
    seed = r5_seed()
    out = []
    for sym in R5_UNIVERSE:
        hist = [list(x) for x in seed.get(sym) or []]
        last = hist[-1][0] if hist else ""
        live = last2h_by_session((bars30_by_symbol or {}).get(sym))
        hist += [[d, v] for d, v in sorted(live.items()) if d > last]
        prior = [v for d, v in hist if d < session]
        today = next((v for d, v in hist if d == session), None)
        if today is None or len(prior) < R5_MIN_OBS:
            continue
        p80 = float(vo._quantile(prior[-R5_TRAIL:], R5_PCT))
        if today >= p80:
            out.append({"symbol": sym, "value": repr(today), "p80": repr(p80), "n_hist": len(prior),
                        "signal_at": iso(cal.session_close(session))})
    return out


def opening_events(view, snap, r5):
    """the evaluator's opening_reversal_events: each prior-afternoon R5 event with today's completed first 5-minute
    bar (09:30-09:35 ET) and the live observed price (mid of the desk's quote), lexical order."""
    c = snap["calendar"]
    if not r5 or r5.get("session") != c.get("previous_session"):
        return []
    opened = cal.session_open(c["session"])
    bars5 = view.extra.get("bars_open5") or {}
    out = []
    for e in sorted(r5.get("events") or [], key=lambda x: x["symbol"]):
        sym = e["symbol"]
        bar = next((b for b in bars5.get(sym) or [] if abs(float(b["t"]) - opened) < 1), None)
        q = (view.quotes or {}).get(sym) or {}
        o, lo, cl = (_num((bar or {}).get(k)) for k in ("o", "l", "c"))
        bid, ask = _num(q.get("bid")), _num(q.get("ask"))
        if not (o and lo and cl and bid and ask) or o <= 0:
            continue
        ev = {"event_id": f"{sym}:{r5['session']}:R5", "symbol": sym, "session": c["session"],
              "prior_afternoon_session": r5["session"], "first_5min_start_at": iso(opened),
              "first_5min_end_at": iso(opened + 300), "first_5min_received_at": snap["now"],
              "first_5min_complete": True, "first_5min_return": repr(cl / o - 1), "first_5min_low": repr(lo),
              "observed_break_price": repr((bid + ask) / 2), "break_market_at": snap["now"],
              "break_received_at": snap["now"], "R5_signal_at": e["signal_at"], "R5_received_at": r5["received_at"],
              "causal_R5_prior_afternoon": True, "R5_value": e["value"], "R5_p80": e["p80"]}
        ev["source_sha256"] = _sha([ev, [bar.get(k) for k in ("t", "o", "h", "l", "c")], [bid, ask]])
        out.append(ev)
    return out


def opening_triggered(ev):
    return float(ev["first_5min_return"]) < 0 and float(ev["observed_break_price"]) < float(ev["first_5min_low"])


# -- PEAD producer (OPT_PEAD_*): desk/feedlib/ausar_pead.py (job ausar_pead, feed ausar_pead) ----------------------
PEAD_FEED = "ausar_pead"
PEAD_KEYS = ("event_id", "symbol", "event_date", "first_published_at", "announcement_at", "source_sha256")


def pead_doc(root):
    return ausar_pead.load(root) if root else None


def pead_today(doc, session):
    """today's entries (event + 3 sessions) the producer pre-evaluated as passing (vendored build/pead_signal)."""
    return sorted((c for c in (doc or {}).get("candidates") or []
                   if c.get("entry_session") == session and c.get("pre_pass") is True),
                  key=lambda c: (c["entry_session"], c["symbol"]))


def pead_inputs(view, snap, doc):
    snap["earnings_events"] = [{k: c[k] for k in PEAD_KEYS} for c in pead_today(doc, snap["calendar"]["session"])]
    snap["earnings_history"] = list((doc or {}).get("history") or [])


def _pead_feed(feeds, sleeve, now, arg):
    """FEED ausar_pead: the producer's latest pead.json (history + pre-evaluated candidates)."""
    return pead_doc(getattr(getattr(sleeve, "engine", None), "root", None))


def _pead_job(engine):
    tradable = None
    broker = getattr(engine, "broker", None)
    if broker is not None and getattr(broker, "available", False):
        try:
            tradable = {str(a["symbol"]).upper() for a in broker.assets() or []
                        if a.get("tradable") and a.get("status") == "active"}
        except Exception:
            tradable = None
    return ausar_pead.run(engine.root, engine.hub, clock=engine.clock, tradable=tradable)


# -- Tensor G4 bridge (OPT_TENSOR_LEAPS_*) -------------------------------------------------------------------------
# The source's own bridge, r19_tensor.attach_G4_events (qualified Author v615 G4 offers of the R19 tensor cycle,
# each with its entry session and original 52-week exit deadline), is produced on this desk by the R19 tensor
# port's acquisition cycle and published in its feed; the option books read its tensor_G4_events /
# tensor_G4_exit_events exactly as the source's options evaluator read them from the shared R19 snapshot.
G4_FEED = "r19_tensor_snapshot"


def record_g4(view, st):
    snap = view.extra.get(G4_FEED)
    if isinstance(snap, dict) and ("tensor_G4_events" in snap or "tensor_G4_exit_events" in snap):
        st["g4"] = {"at": iso(view.now), "events": list(snap.get("tensor_G4_events") or [])[-200:],
                    "exit_events": list(snap.get("tensor_G4_exit_events") or [])[-200:]}


def g4_candidates(st, session):
    return sorted({e["symbol"] for e in (st.get("g4") or {}).get("events") or []
                   if e.get("entry_session") == session and e.get("qualified_native_G4") is True and e.get("symbol")})


def g4_quote_symbols(st, now):
    d = cal._as_date(now)
    et = datetime.fromtimestamp(now, tz=ET)
    if not cal.is_trading_day(d) or not (9, 35) <= (et.hour, et.minute) < (9, 40):
        return []
    return g4_candidates(st, d.isoformat())


def g4_inputs(view, snap, st):
    """the source's per-book scoping (r19_cli.bounded_snapshot): today's entry events, exit events of owned events."""
    g4 = st.get("g4") or {}
    today = snap["calendar"]["session"]
    owned = {((p.get("meta") or {}).get("position_meta") or {}).get("G4_event_id")
             for p in (view.positions or {}).values()}
    snap["tensor_G4_events"] = [e for e in g4.get("events") or [] if e.get("entry_session") == today]
    snap["tensor_G4_exit_events"] = [e for e in g4.get("exit_events") or [] if e.get("event_id") in owned]


class AusarOptionBook(Sleeve):
    def __init__(self, cfg):
        self.rule = cfg
        fam = cfg["family"]
        under = list(cfg.get("universe") or [])
        if fam == "core_reserve" and "QQQ" not in under:
            under.append("QQQ")
        needs, schedule = {}, "rth"
        if fam in ("recovery", "core_reserve"):
            needs = {"bars": [{"source": "equity_split", "interval": "1d", "n": 450, "symbols": list(under)}],
                     "quotes": {"source": "equity", "symbols": list(under)}}
        elif fam == "xsp_pcs":             # the S&P 500 sessions of the weekly XSP bars, read in the entry window
            needs = {"bars": [{"source": "yahoo", "interval": "1d", "n": 5 * XSP_WEEKS + 30,
                               "symbols_for": "xsp_index", "key": "index"}]}
        elif fam == "opening_gamma":       # R5 after each close (30-minute bars), the first 5-minute bar at the open
            under = list(R5_UNIVERSE)
            needs = {"bars": [{"source": "yahoo", "interval": "5m", "n": 6, "symbols_for": "r5_open", "key": "open5"}],
                     "quotes": {"source": "equity"}}
            schedule = f"rth,after_close+{R5_DELAY_MIN}:after_close+300"
        elif fam == "pead":
            under = ["SPY"]
            needs = {"bars": [{"source": "equity_split", "interval": "1d", "n": 60, "symbols_for": "pead_events"}],
                     "quotes": {"source": "equity"}, "feeds": [PEAD_FEED]}
        elif fam == "tensor_leaps":
            under = []
            needs = {"quotes": {"source": "equity"}, "feeds": [G4_FEED]}
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id(cfg), family="ausar_options", cadence_s=30, universe=tuple(under),
            capital=float(cfg["initial_capital"]), needs=needs, schedule=schedule,
            params={"rule_id": cfg["id"], "family": fam, "structure": cfg.get("structure"),
                    "config_sha256": vo.digest(cfg)},
            source=dict(SOURCE, config_id=cfg["id"]),
            state_schema={"installed_at": "str", "option_entry_attempts": "dict", "filled_packages": "list"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def _state_now(self):
        store = getattr(self.engine, "store", None)
        if store is not None:
            try:
                return store.sleeve_get(self.CONFIG.sleeve_id) or {}
            except Exception:
                pass
        return self._st or {}

    def _r5_candidates(self, now, st):
        """the prior-afternoon R5 symbols, inside the opening-gamma entry window."""
        d = cal._as_date(now)
        et = datetime.fromtimestamp(now, tz=ET)
        r5 = st.get("r5") or {}
        if not cal.is_trading_day(d) or not (9, 35) <= (et.hour, et.minute) < (9, 45):
            return []
        if r5.get("session") != cal.prev_trading_day(d).isoformat():
            return []
        return sorted({e["symbol"] for e in r5.get("events") or []})

    def bar_symbols(self, spec, now, book=None):
        """per-pass symbols of the producer bar needs (none outside the moment a producer reads them)."""
        tag, d = spec.get("symbols_for"), cal._as_date(now)
        if not cal.is_trading_day(d):
            return []
        et = datetime.fromtimestamp(now, tz=ET)
        if tag == "xsp_index":
            c = session_calendar(now)
            return ["^GSPC"] if c["first_session_of_week"] and (10, 0) <= (et.hour, et.minute) < (10, 5) else []
        st = self._state_now()
        if tag == "r5_open":
            return self._r5_candidates(now, st)
        if tag == "pead_events":
            syms = self._pead_symbols(now)
            return ["SPY"] + syms if syms else []
        return []

    def _pead_symbols(self, now):
        """today's pre-evaluated PEAD entries, inside the 09:35-09:40 entry window."""
        d = cal._as_date(now)
        et = datetime.fromtimestamp(now, tz=ET)
        if not cal.is_trading_day(d) or not (9, 35) <= (et.hour, et.minute) < (9, 40):
            return []
        return [c["symbol"] for c in pead_today(pead_doc(getattr(self.engine, "root", None)), d.isoformat())]

    def quote_universe(self, now, book=None):
        syms = list(self.CONFIG.universe) if self.rule["family"] in ("recovery", "core_reserve") else []
        fam = self.rule["family"]
        if fam == "opening_gamma":
            syms += self._r5_candidates(now, self._state_now())
        elif fam == "pead":
            syms += self._pead_symbols(now)
        elif fam == "tensor_leaps":
            syms += g4_quote_symbols(self._state_now(), now)
        for p in (getattr(book, "positions", None) or {}).values():
            u = ((p.get("meta") or {}).get("underlying"))
            if u and u not in syms and u != "XSP":
                syms.append(u)
        return syms

    def _options(self):
        hub = getattr(self.engine, "hub", None)
        return getattr(hub, "options", None)

    # -- snapshot / book -----------------------------------------------------------------------------------
    def snapshot(self, view, owned_legs, chains):
        """the evaluator's snapshot from the View (+ chain rows {underlying: rows} and owned-leg quotes)."""
        stamp = iso(view.now)
        c = session_calendar(view.now)
        s = {"now": stamp, "asof": stamp, "calendar": c, "market_open": c["is_open"], "option_fees": dict(OPTION_FEES),
             "option_cash_release_at": iso(cal.session_open(cal.next_trading_day(c["session"]))),
             "option_settlement_calendar_verified": True, "complete_option_chains": [], "option_contracts": [],
             "option_quotes": {}, "underlying_quotes": {}, "exercise_checks": {}, "daily_bars": {}}
        for sym, bl in ((view.bars or {}).get("1d") or {}).items():
            s["daily_bars"][sym] = daily_rows(bl, c["session"])
        for sym, q in (view.quotes or {}).items():
            uq = underlying_quote(sym, q, stamp)
            if uq:
                s["underlying_quotes"][sym] = uq
        far = (datetime.fromisoformat(c["session"]) + timedelta(days=3650)).date().isoformat()
        for under, rows in chains.items():
            if rows is None:
                continue
            s["complete_option_chains"].append(under)
            s["exercise_checks"][under] = {"verified": True, "source_sha256": _sha(["exercise_checks", under]),
                                           "received_at": stamp, "valid_through": far, "assignment_alert": False}
            for r in rows:
                try:
                    s["option_contracts"].append(contract_of(r, stamp))
                except (ValueError, IndexError, KeyError):
                    continue
                oq = option_quote(r["symbol"], r, stamp)
                if oq:
                    s["option_quotes"][r["symbol"]] = oq
        for occ, q in owned_legs.items():
            oq = option_quote(occ, q, stamp)
            if oq:
                s["option_quotes"][occ] = oq
            u = underlying_of(occ)
            s["exercise_checks"].setdefault(u, {"verified": True, "source_sha256": _sha(["exercise_checks", u]),
                                                "received_at": stamp, "valid_through": far, "assignment_alert": False})
        return s

    def book(self, view, positions, state):
        nav = float(view.cash)
        for sym, p in positions.items():
            if "legs" in p["metadata"]:
                continue
            q = (view.quotes or {}).get(sym) or {}
            px = _num(q.get("bid")) or _num((view.positions.get("EQ:" + sym) or {}).get("mark")) or \
                _num((view.positions.get("EQ:" + sym) or {}).get("avg"))
            nav += float(p["quantity"]) * (px or 0.0)
        for inst, p in (view.positions or {}).items():
            if inst.startswith("OPT:"):
                nav += float(p["qty"]) * 100.0 * float(p.get("mark") or p.get("avg") or 0.0)
        coll = sum(float(p["metadata"].get("collateral_per_package") or 0) * float(p["quantity"])
                   for p in positions.values() if "legs" in p["metadata"])
        filled = list(state.get("filled_packages") or [])
        return {"id": self.rule["id"], "strategy_id": self.rule["id"], "config": self.rule,
                "initial_capital": self.rule["initial_capital"], "nav": repr(round(nav, 6)),
                "cash": repr(round(float(view.cash), 6)), "collateral": repr(round(coll, 6)), "enabled": True,
                "installed_at": state["installed_at"], "positions": positions,
                "state": {"option_entry_attempts": state.get("option_entry_attempts") or {},
                          "last_evaluation": {"outcomes": [{"symbol": p, "action": "open", "status": "filled"}
                                                           for p in filled]}}}

    # -- the pass --------------------------------------------------------------------------------------------
    def signal(self, view):
        cfg = self.rule
        st = dict(view.state or {})
        st.setdefault("installed_at", iso(view.now))
        positions, pkg_legs = packages(view)
        owned = [p for p in positions.values() if "legs" in p["metadata"]]
        filled = list(st.get("filled_packages") or [])
        for pkg in pkg_legs:                      # an owned package consumes its event (evaluate's filled outcome)
            if pkg not in filled:
                filled.append(pkg)
        st["filled_packages"] = filled[-200:]
        et = datetime.fromtimestamp(view.now, tz=ET)
        lo, hi = entry_window(cfg["family"])
        in_window = lo <= (et.hour, et.minute) < hi
        pending = [p for p in view.extra.get("pending_orders") or [] if p.get("action") == "enter"]
        self._st = st
        if cfg["family"] == "opening_gamma":
            self._record_r5(view, st)             # after each close: that session's R5 events, for the next open
        if cfg["family"] == "tensor_leaps":
            self._record_g4(view, st)
        if not owned and not in_window:
            return []                             # the evaluator proposes nothing outside its window when flat
        opts = self._options()
        occs = [o for legs in pkg_legs.values() for o in legs]
        owned_q = (opts.quotes(occs) if (opts is not None and occs) else {})
        pre = {}
        chains = self._chains(view, st, opts, pre) if (in_window and not owned and opts is not None) else {}
        snap = self.snapshot(view, owned_q, chains)
        self._inputs(view, snap, st, opts, in_window and not owned, pre)
        book = self.book(view, positions, st)
        out = vo.evaluate(snap, book)
        if (out.get("state") or {}).get("option_entry_attempts") is not None:
            st["option_entry_attempts"] = out["state"]["option_entry_attempts"]
        intents = self.intents(view, snap, book, out, pending)
        self._st = st
        return intents

    # -- producers --------------------------------------------------------------------------------------------
    def _chains(self, view, st, opts, pre):
        """{underlying: chain rows} the evaluator may select from this pass (flat, inside the entry window)."""
        cfg, fam = self.rule, self.rule["family"]
        lo_d, hi_d = cfg.get("dte") or (None, None)

        def chain(u):
            return opts.chain(u, dte_min=(lo_d - 1) if lo_d is not None else None,
                              dte_max=(hi_d + 1) if hi_d is not None else None, now=view.now)
        out = {}
        if fam in ("recovery", "core_reserve"):
            for u in cfg.get("universe") or []:
                out[u] = chain(u)
        elif fam == "xsp_pcs":
            if session_calendar(view.now)["first_session_of_week"]:
                out["XSP"] = opts.chain("XSP", dte_min=0, dte_max=7, typ="put", now=view.now)
        elif fam == "opening_gamma":
            pre["opening"] = opening_events(view, {"calendar": session_calendar(view.now), "now": iso(view.now)},
                                            st.get("r5"))
            for e in pre["opening"]:
                if opening_triggered(e) and e["symbol"] not in out:
                    out[e["symbol"]] = chain(e["symbol"])
        elif fam == "pead":
            for sym in self._pead_symbols(view.now):
                out.setdefault(sym, chain(sym))
        elif fam == "tensor_leaps":
            for sym in g4_candidates(st, view.session):
                out.setdefault(sym, chain(sym))
        return out

    def _inputs(self, view, snap, st, opts, flat_window, pre):
        """the family's event / state inputs on the snapshot (the producers the source runtime lacked)."""
        fam, c = self.rule["family"], snap["calendar"]
        if fam == "xsp_pcs":
            snap["option_fees"] = dict(XSP_FEES)                                  # N8
            if flat_window and c["first_session_of_week"]:
                spot = opts.spot("XSP") if opts is not None else None
                if spot:
                    snap["underlying_quotes"]["XSP"] = underlying_quote("XSP", {"bid": spot, "ask": spot}, snap["now"])
                state = xsp_state(snap, (view.extra.get("bars_index") or {}).get("^GSPC"), st.get("xsp_digitals"))
                snap["xsp_state"] = state
                rd = xsp_reading(snap, state)
                have = list(st.get("xsp_digitals") or [])
                if rd and not any(x["week_end"] == rd["week_end"] for x in have):
                    st["xsp_digitals"] = (have + [rd])[-520:]
        elif fam == "opening_gamma":
            if flat_window:
                snap["opening_reversal_events"] = pre["opening"] if "opening" in pre else \
                    opening_events(view, snap, st.get("r5"))
        elif fam == "pead":
            if flat_window:
                doc = view.extra.get(PEAD_FEED) or pead_doc(getattr(self.engine, "root", None))
                pead_inputs(view, snap, doc)
        elif fam == "tensor_leaps":
            g4_inputs(view, snap, st)

    def _record_r5(self, view, st):
        """after a session's close (+20 min): its R5 events, received now — the next open's prior-afternoon input."""
        d = cal._as_date(view.now)
        if not cal.is_trading_day(d) or view.now < cal.session_close(d) + R5_DELAY_MIN * 60:
            return
        session = d.isoformat()
        if (st.get("r5") or {}).get("session") == session:
            return
        bars30 = view.extra.get("bars_r5")
        if bars30 is None:                        # the 30-minute bars since the seed's end, once per evening
            hub = getattr(self.engine, "hub", None)
            if hub is None:
                return
            last = max(v[-1][0] for v in r5_seed().values() if v)
            n = 13 * min(280, cal.trading_days_between(last, d) + 3)
            try:
                bars30 = hub.bars("equity", "30m", list(R5_UNIVERSE), n) or {}
            except Exception:
                return
        traded = [s for s in R5_UNIVERSE if any(et_date(float(b["t"])) == session for b in (bars30.get(s) or [])[-20:])]
        done = [s for s in traded if session in last2h_by_session((bars30.get(s) or [])[-20:])]
        if not traded or (len(done) < len(traded) and view.now < cal.session_close(d) + 3600):
            return                                # the session's 15:30 bars are not all in yet
        st["r5"] = {"session": session, "received_at": iso(view.now), "events": r5_events(bars30, session),
                    "symbols_with_session": len(done)}

    def _record_g4(self, view, st):
        record_g4(view, st)

    def intents(self, view, snap, book, out, pending):
        cfg, sid, session = self.rule, self.CONFIG.sleeve_id, view.session
        res = []
        live_keys = {p.get("signal_key") for p in pending}
        for it in out.get("intents") or []:
            if it.get("type") != "option_package":           # the QQQ core purchase (core_reserve)
                uq = snap["underlying_quotes"].get(it["symbol"]) or {}
                res.append(Intent("enter", it["symbol"], qty=float(it["quantity"]), price_hint=_num(uq.get("ask")),
                                  order=OrderSpec(type="limit", limit_price=float(uq["ask"]), window_s=ORDER_WINDOW_S,
                                                  not_after=vo.stamp(it["expires_at"]).timestamp()),
                                  signal_key=it["signal_id"], reason=f"{cfg['id']}: {it.get('reason')}",
                                  meta={"cost_bps": float(cfg.get("fee_bps", 15)),
                                        "position_meta": dict(it.get("metadata") or {})}))
                continue
            action = it["action"]
            if action == "settle":                           # N6: the engine settles expiring contracts
                continue
            legs = it["legs"]
            qs = [snap["option_quotes"][l["symbol"]] for l in legs]
            under = legs[0]["underlying"]
            venue = SIM_INDEX_VENUE if under in SIM_INDEX_ROOTS else ""   # N13: index options Alpaca does not list
            if action == "open":
                if pending and it["signal_id"] not in live_keys:      # N7: one package in flight
                    res.append(Intent("signal", under, reason=f"{cfg['id']}: entry {it['signal_id']} waits — "
                                      f"package in flight", signal_key=f"{session}:inflight:{it['signal_id']}"))
                    continue
                pp = vo.prepare_package(it, snap, book)
                pm = dict(pp["position_metadata"])
                deadline = vo.stamp(it["expires_at"]).timestamp()
                meta = {"ausar_package": it["symbol"], "position_meta": pm, "underlying": under}
                if len(legs) == 1:
                    res.append(Intent("enter", legs[0]["symbol"], side="long", asset="option", qty=float(it["quantity"]),
                                      price_hint=float(qs[0]["ask"]), venue=venue,
                                      order=OrderSpec(type="limit", limit_price=float(qs[0]["ask"]),
                                                      window_s=ORDER_WINDOW_S, not_after=deadline),
                                      signal_key=it["signal_id"], reason=f"{cfg['id']}: {it['reason']}", meta=meta))
                else:
                    net = round(sum((float(q["ask"]) if int(l["ratio"]) > 0 else -float(q["bid"])) * abs(int(l["ratio"]))
                                    for l, q in zip(legs, qs)), 4)
                    meta["group"] = f"{sid}:{it['symbol']}"
                    eleg = tuple(Leg(l["symbol"], "buy" if int(l["ratio"]) > 0 else "sell", abs(int(l["ratio"])),
                                     "buy_to_open" if int(l["ratio"]) > 0 else "sell_to_open") for l in legs)
                    res.append(Intent("enter", under, side="long", asset="mleg", qty=float(it["quantity"]), legs=eleg,
                                      venue=venue, price_hint=net, order=OrderSpec(type="limit", limit_price=net,
                                                                      window_s=ORDER_WINDOW_S, not_after=deadline),
                                      signal_key=it["signal_id"], reason=f"{cfg['id']}: {it['reason']}", meta=meta))
                continue
            # close: the whole owned package at the natural liquidation
            if len(legs) == 1:
                bid = float(qs[0]["bid"])
                order = OrderSpec(type="limit", limit_price=bid, window_s=ORDER_WINDOW_S) if bid > 0 else \
                    OrderSpec(window_s=ORDER_WINDOW_S)
                res.append(Intent("exit", legs[0]["symbol"], side="long", asset="option", qty=None, order=order,
                                  venue=venue, price_hint=bid or None, signal_key=it["signal_id"],
                                  reason=f"{cfg['id']} exit: {it['reason']}", meta={"ausar_package": it["symbol"]}))
            else:
                net = round(sum((float(q["ask"]) if int(l["ratio"]) < 0 else -float(q["bid"])) * abs(int(l["ratio"]))
                                for l, q in zip(legs, qs)), 4)
                eleg = tuple(Leg(l["symbol"], "sell" if int(l["ratio"]) > 0 else "buy", abs(int(l["ratio"])),
                                 "sell_to_close" if int(l["ratio"]) > 0 else "buy_to_close") for l in legs)
                res.append(Intent("exit", under, asset="mleg", qty=None, legs=eleg, price_hint=net, venue=venue,
                                  order=OrderSpec(type="limit", limit_price=net, window_s=ORDER_WINDOW_S),
                                  signal_key=it["signal_id"], reason=f"{cfg['id']} exit: {it['reason']}",
                                  meta={"group": f"{sid}:{it['symbol']}", "underlying": under,
                                        "ausar_package": it["symbol"]}))
        for b in out.get("blockers") or []:
            r = str(b.get("reason") or "")
            if not r or r in QUIET_BLOCKERS:
                continue
            sym = b.get("symbol") or (cfg.get("universe") or [cfg["id"]])[0]
            if str(sym).startswith("PKG:"):
                sym = (book["positions"].get(sym, {}).get("metadata", {}).get("legs") or [{}])[0].get("underlying") or sym
            res.append(Intent("signal", str(sym), reason=f"{cfg['id']} blocked: {r}"[:300], meta={"blocker": b},
                              signal_key=f"{session}:blk:{_sha([sym, r])[:16]}"))
        for o in out.get("observations") or []:
            if "pass" in o and o.get("symbol"):
                res.append(Intent("signal", o["symbol"], reason=(
                    f"{cfg['id']} {o.get('method', 'signal')} {o['symbol']} value={_fmt(o.get('value'))} "
                    f"sma200={_fmt(o.get('sma200'))} pass={o['pass']} ({o.get('signal_session')})")[:300],
                    meta={"observation": _jsonable(o)}, signal_key=f"{session}:obs:{o['symbol']}"))
        return res

    def update_state(self, view, intents):
        return self._st


def _fmt(v):
    return f"{v:.4f}" if isinstance(v, float) else str(v)


def _jsonable(o):
    return json.loads(json.dumps(o, default=str))


def sleeves():
    out = []
    for cfg in vo.register():
        if not cfg.get("monitor_only"):
            out.append(AusarOptionBook(cfg))
    return out


FEEDS = {PEAD_FEED: _pead_feed}
# the PEAD producer each weekday evening after the close (the calendar ahead, the resolved history, next entries)
JOBS = {"ausar_pead": ("weekday:12345&et:16:40-23:30", 6 * 3600, _pead_job)}
