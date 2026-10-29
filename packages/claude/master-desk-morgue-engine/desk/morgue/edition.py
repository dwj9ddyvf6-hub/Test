"""The edition's `morgue` key: the Morgue Engine's cards, read from state/morgue/ (never the network), checked against the
ledger, stamped, and conformed to the public contract (docs/research/MORGUE_SCHEMA.md).

The terminal job calls block() while it builds an edition and write_sidecars() beside the publisher's other files; the page
(term-funnel's sections, term-gaps' GEX tiles) reads what is here and nothing else.

What this module guarantees, each proven in tests/test_morgue_edition.py:
  - log before show: a card whose inputs hash the ledger does not hold is shown as no_data ("not logged"), never as a number;
  - status: every section says ok, stale or no_data; stale once a newer session has opened, and a stale card keeps its
    numbers with the as-of date and the reason;
  - the contract: conform() drops any key the allow-list does not name (and the test fails if it had to), turns a
    non-finite number into null, and scrubs every string of an address, a host, a path, a token's shape and a currency sign
    (the page refuses an edition holding one);
  - nothing here raises into the edition: a section that cannot be read is no_data with the reason."""
import math
import os
import re
from datetime import datetime

from .. import calendar as cal
from ..util import ET
from . import ROOT_LAW, ledger, routes, state_path

SCHEMA = "morgue/1"
SIDECARS = ("morgue-board.json", "morgue-map.json")

ALLOWED = {
    "morgue": {"schema", "as_of", "built_at", "law", "status", "reason", "map", "tape", "board", "institutional", "studies", "ledger", "flow", "chain", "lanes"},
    "morgue.map": {"status", "reason", "as_of", "source", "delay", "for_session", "label", "cards", "dix", "sidecar"},
    "morgue.map.cards.*": {"status", "reason", "as_of", "source", "delay", "spot", "spot_source", "net_gex_b", "regime", "call_wall", "put_wall", "flip", "flip_distance_pct", "flip_reason", "call_wall_pct", "put_wall_pct", "contracts_used", "chain_total", "coverage_pct", "oi_date", "expiries", "top_strikes", "by_expiry", "method", "inputs_hash"},
    "morgue.map.cards.*.top_strikes[]": {"strike", "gex_b"},
    "morgue.map.cards.*.by_expiry[]": {"expiry", "gex_b"},
    "morgue.map.dix": {"status", "reason", "as_of", "source", "delay", "file_date", "etf", "etf_avg", "index", "roster"},
    "morgue.map.dix.etf.*": {"ratio", "short_volume", "total_volume"},
    "morgue.map.dix.index": {"status", "reason", "as_of", "source", "delay", "value", "constituents_used", "constituents_total", "coverage", "weight_source", "construction", "not_the_same_as", "route"},
    "morgue.map.dix.roster": {"status", "reason", "as_of", "source", "delay", "value", "names_used", "names_total", "coverage", "weight_source", "construction", "not_the_same_as"},
    "morgue.tape": {"status", "reason", "as_of", "source", "delay", "for_session", "window", "labels", "cards"},
    "morgue.tape.cards.*": {"status", "reason", "as_of", "source", "delay", "spot", "prints", "signed_share", "cancelled_excluded", "multileg_prints", "total_premium_usd", "net_premium_usd", "call_net_premium_usd", "put_net_premium_usd", "golden_sweeps", "high_heat", "mean_heat", "mean_algo_all", "mean_algo_buys_only", "opening_prints", "closing_prints", "contracts_in_scope", "batches_capped", "week52_hi", "week52_lo", "week52_context", "alerts"},
    "morgue.tape.cards.*.alerts[]": {"ts", "contract", "kind", "strike", "expiry", "dte", "size", "price", "premium_usd", "heat", "algo", "side", "sentiment", "sweep", "golden_sweep", "unusual", "top_position", "opening", "size_oi"},
    "morgue.board": {"status", "reason", "as_of", "source", "delay", "for_session", "summary", "weights", "top", "qualified_symbols", "labels", "sidecar"},
    "morgue.board.summary": {"universe", "scored", "insufficient_data", "qualified", "market_context", "gate"},
    "morgue.board.summary.market_context": {"marketRegime", "marketBreadth", "indexAccDist", "breakoutFollowThrough", "riskAppetite", "sectorRotation", "macroEventRisk", "indexConfirmation"},
    "morgue.board.summary.gate": {"confirming_min", "conviction_min", "data_confidence_min", "coverage_floor"},
    "morgue.board.weights[]": {"category", "weight", "leaves"},
    "morgue.board.top[]": {"symbol", "sector", "close", "score", "confirming", "dc", "qualified", "gate_fails", "qualify_fails", "capacity_usd", "stage", "atr_pct", "support", "resistance", "ribbon", "triggers", "ladder", "categories", "leaves", "inst"},
    "morgue.board.top[].triggers[]": {"trigger", "level", "validated"},
    "morgue.board.top[].ladder": {"anchor", "atr", "trigger_up", "trigger_down"},
    "morgue.board.top[].categories.*": {"score", "state"},
    "morgue.board.top[].leaves.*": {"trendStructure", "baseQuality", "volContraction", "pullbackQuality", "technicalRespect", "stageDevelopment", "extension", "rsMarket", "rsGrowth", "rsSector", "peerRank", "rsLine", "downsideResilience", "longMomentum", "relVolume", "dollarVolTrend", "accDist", "volPriceAgreement", "pullbackVolume", "participationBreadth", "expansionReadiness", "emaPosition", "emaSlope", "dailyWeeklyAgreement", "stageAlignment", "htfLevelPosition", "weeklyAccExhaustion", "supportProximity", "roomToResistance", "levelSignificance", "srConversion", "tradeGeometry", "chasePenalty", "sectorStrength", "industryStrength", "capitalRotation", "stockLeadership", "peerConfirmation", "themeSympathy", "crowding", "instOwnership", "instActivity", "insiderActivity", "optionsPositioning", "dealerPositioning", "darkPool", "shortPositioning", "marketRegime", "marketBreadth", "indexAccDist", "breakoutFollowThrough", "riskAppetite", "sectorRotation", "macroEventRisk", "indexConfirmation"},
    "morgue.board.top[].inst.*": {"score", "status", "reason", "as_of", "source", "delay"},
    "morgue.institutional": {"status", "reason", "as_of", "source", "delay", "for_session", "coverage", "floor", "thirteen_f", "insider_buys", "short_interest", "routes"},
    "morgue.institutional.coverage[]": {"leaf", "names_with_value", "names_total", "pct", "status", "reason"},
    "morgue.institutional.floor": {"category_weight", "leaves_designed", "leaves_with_route", "share_with_route", "note"},
    "morgue.institutional.thirteen_f": {"status", "reason", "as_of", "source", "delay", "current_period", "prior_period", "cusip_coverage_pct", "names_wanted", "names_resolved", "vintage"},
    "morgue.institutional.insider_buys[]": {"symbol", "buy_value_usd", "sell_value_usd", "n_transactions", "latest_filing_date", "score"},
    "morgue.institutional.short_interest": {"status", "reason", "as_of", "source", "delay", "route", "rows"},
    "morgue.institutional.short_interest.rows[]": {"symbol", "settlement_date", "publication_date", "si_shares", "si_pct_shares_out", "days_to_cover", "score"},
    "morgue.institutional.routes[]": {"route", "status", "reason", "as_of"},
    "morgue.studies": {"status", "reason", "as_of", "source", "delay", "for_session", "gap_fill", "orb_ib", "earnings_dist", "wall_validation", "squeeze", "state_vectors"},
    "morgue.studies.gap_fill": {"status", "reason", "as_of", "source", "delay", "state", "symbol", "n", "fills", "frequency", "fill_pct", "by_band", "by_weekday"},
    "morgue.studies.gap_fill.by_band[]": {"band", "n", "fills", "frequency"},
    "morgue.studies.gap_fill.by_weekday[]": {"weekday", "n", "fills", "frequency"},
    "morgue.studies.orb_ib": {"status", "reason", "as_of", "source", "delay", "symbol", "windows"},
    "morgue.studies.orb_ib.windows[]": {"window_min", "status", "reason", "state", "n", "break_one_side", "break_both", "no_break", "break_one_side_rate", "break_both_rate", "no_break_rate", "extension_n", "ext_0_5", "ext_1_0", "ext_1_5"},
    "morgue.studies.earnings_dist": {"status", "reason", "as_of", "source", "delay", "state", "n_events", "symbols_used", "pooled", "rows"},
    "morgue.studies.earnings_dist.pooled": {"n", "mean", "median", "std", "share_positive", "sharpe"},
    "morgue.studies.earnings_dist.rows[]": {"symbol", "n", "mean", "median", "std", "share_positive", "sharpe"},
    "morgue.studies.wall_validation": {"status", "reason", "as_of", "source", "delay", "state", "cards_of_record", "cards_graded", "line", "windows", "by_underlying", "by_regime"},
    "morgue.studies.wall_validation.windows[]": {"window", "state", "n", "call_wall_held_rate", "put_wall_held_rate", "touched_and_held", "touched_and_held_rate", "blown_through", "blown_through_rate", "flip_respected_rate"},
    "morgue.studies.wall_validation.by_underlying[]": {"key", "state", "n", "call_wall_held_rate", "put_wall_held_rate", "touched_and_held", "touched_and_held_rate", "blown_through", "blown_through_rate", "flip_respected_rate"},
    "morgue.studies.wall_validation.by_regime[]": {"key", "state", "n", "call_wall_held_rate", "put_wall_held_rate", "touched_and_held", "touched_and_held_rate", "blown_through", "blown_through_rate", "flip_respected_rate"},
    "morgue.studies.squeeze": {"status", "reason", "as_of", "source", "delay", "state", "formula_version", "gated_n", "excluded_n", "rows", "note"},
    "morgue.studies.squeeze.rows[]": {"symbol", "score", "si_pct_float", "si_change_pct", "days_to_cover", "short_volume_ratio", "momentum_5d", "already_ran", "borrow_fee_state", "volatility_rms_ex_largest", "float_rotation_5d", "relative_volume_capped"},
    "morgue.studies.state_vectors": {"status", "reason", "as_of", "source", "delay", "state", "history_sessions_accrued", "p_nn", "neighbours", "n_neighbours", "p10", "p50", "p90", "nearest_distance"},
    "morgue.flow": {"status", "reason", "as_of", "source", "delay", "for_session", "labels", "net_drift", "repeat_sweeps", "premium_ratio", "flow_ratio", "hiro", "oi_change", "oi_confirm", "flow_gex"},
    "morgue.flow.net_drift.*": {"status", "reason", "as_of", "source", "delay", "bucket_min", "buckets"},
    "morgue.flow.net_drift.*.buckets[]": {"t", "call_net_premium_usd", "put_net_premium_usd", "net_premium_usd", "call_net_volume", "put_net_volume", "prints"},
    "morgue.flow.repeat_sweeps.*": {"status", "reason", "as_of", "source", "delay", "window_min", "min_count", "alerts"},
    "morgue.flow.repeat_sweeps.*.alerts[]": {"contract", "kind", "count", "premium_usd", "span_min", "tier", "first", "last"},
    "morgue.flow.premium_ratio": {"status", "reason", "as_of", "source", "delay", "names", "ignored"},
    "morgue.flow.premium_ratio.names.*": {"bullish_usd", "bearish_usd", "ratio", "prints", "reason"},
    "morgue.flow.flow_ratio.*": {"status", "reason", "as_of", "source", "delay", "call_premium_usd", "put_premium_usd", "ratio", "unusual_prints"},
    "morgue.flow.hiro.*": {"status", "reason", "as_of", "source", "delay", "series", "next_expiry", "skipped_no_delta", "bucket_min", "rolling_min"},
    "morgue.flow.hiro.*.series[]": {"t", "total", "call", "put", "next_expiry", "cumulative", "rolling"},
    "morgue.flow.oi_change.*": {"status", "reason", "as_of", "source", "delay", "prev_date", "rows"},
    "morgue.flow.oi_change.*.rows[]": {"contract", "kind", "strike", "expiry", "oi", "oi_prev", "change", "new"},
    "morgue.flow.oi_confirm.*": {"status", "reason", "as_of", "source", "delay", "alert_date", "counts", "rows"},
    "morgue.flow.oi_confirm.*.counts": {"opened", "closed", "unchanged", "unknown"},
    "morgue.flow.oi_confirm.*.rows[]": {"contract", "size", "oi_alert_day", "oi_next_day", "change", "result"},
    "morgue.flow.flow_gex.*": {"status", "reason", "as_of", "source", "delay", "weight", "net_gex_b", "oi_net_gex_b", "call_wall", "put_wall", "contracts_used", "label"},
    "morgue.chain": {"status", "reason", "as_of", "source", "delay", "for_session", "cards"},
    "morgue.chain.cards.*": {"status", "reason", "as_of", "source", "delay", "spot", "dex_b", "dex_balance", "vex_b", "charm_b_per_day", "max_pain", "max_pain_expiry", "key_gamma_strike", "anchor_strike", "key_delta_strike", "g_coord", "iv30", "iv60", "slope_30_60", "rr25", "strangle15", "butterfly25", "iv_rank", "iv_rank_n", "atm_by_expiry", "label"},
    "morgue.chain.cards.*.atm_by_expiry[]": {"days", "atm_iv"},
    "morgue.lanes": {"status", "reason", "as_of", "source", "delay", "for_session", "chain_archive", "short_volume", "sec_facts"},
    "morgue.lanes.chain_archive": {"status", "reason", "as_of", "source", "delay", "days", "first_date", "last_date", "bytes", "names"},
    "morgue.lanes.short_volume": {"status", "reason", "as_of", "source", "delay", "days", "first_date", "last_date", "bytes", "names"},
    "morgue.lanes.sec_facts": {"status", "reason", "as_of", "source", "delay", "days", "first_date", "last_date", "bytes", "names"},
    "morgue.ledger": {"status", "reason", "as_of", "source", "delay", "rows_total", "last_logged_at", "components", "scorecards", "counters", "rules"},
    "morgue.ledger.components[]": {"component", "n"},
    "morgue.ledger.scorecards": {"board", "map"},
    "morgue.ledger.scorecards.board.*": {"n_logged", "horizons"},
    "morgue.ledger.scorecards.board.*.horizons[]": {"horizon", "state", "n_mature", "hit_rate", "mean", "median", "expected", "line"},
    "morgue.ledger.scorecards.map": {"state", "cards_graded", "cards_pending", "call_wall_held_rate", "put_wall_held_rate", "touched_and_held", "flip_respected_rate", "line"},
    "morgue.ledger.counters": {"units_published", "board_rows_logged", "map_cards_of_record", "units_graded"},
}

_URL = re.compile(r"https?://\S+", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_HOST = re.compile(r"\b(?:[a-z0-9-]+\.)+(?:com|org|gov|net|io|co|us|edu)\b", re.I)
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_PATH = re.compile(r"(?<![\w/])(?:/[\w.-]+){2,}")
_CUR = re.compile("[$¢£¥€]")
STR_MAX = 400


def scrub(text):
    """a string the public page may carry: no address, host, IP, path, token shape or currency sign (the page refuses an
    edition with a currency sign, the publisher blocks the rest)"""
    from ..terminal.publish import SECRET_SHAPES
    s = _URL.sub("a public source", text)
    s = _EMAIL.sub("an address", s)
    for p in SECRET_SHAPES:
        s = p.sub("", s)
    s = _HOST.sub("a public source", s)
    s = _IP.sub("", s)
    s = _PATH.sub("", s)
    s = _CUR.sub("USD ", s)
    s = " ".join(s.split())
    return s if len(s) <= STR_MAX else s[:STR_MAX - 1].rstrip() + "…"


def conform(obj, path, dropped):
    """`obj` cut to the allow-list at `path` (the keys it names, nothing else), numbers finite, strings scrubbed; the paths
    of what was dropped are appended to `dropped` (a test fails on any: the builder must not make what the contract refuses)"""
    if isinstance(obj, dict):
        if path in ALLOWED:
            allowed, out = ALLOWED[path], {}
            for k, v in obj.items():
                if k not in allowed:
                    dropped.append(f"{path}.{k}")
                    continue
                out[k] = conform(v, f"{path}.{k}", dropped)
            return out
        if path + ".*" in ALLOWED:
            return {k: conform(v, path + ".*", dropped) for k, v in obj.items()}
        dropped.append(path)
        return None
    if isinstance(obj, list):
        return [conform(x, path + "[]", dropped) for x in obj]
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, str):
        return scrub(obj)
    if isinstance(obj, (bool, int)) or obj is None:
        return obj
    dropped.append(f"{path} (type {type(obj).__name__})")
    return None


def stale_why(for_session, now):
    """why a card built for `for_session` is stale at `now`, or None: stale once a later session has opened"""
    try:
        d0 = datetime.fromisoformat(str(for_session)[:10]).date()
    except ValueError:
        return "its session is not dated"
    today = cal._as_date(float(now))
    d = d0
    while True:
        d = cal.next_trading_day(d)
        if d > today:
            return None
        if cal.session_open(d) <= now:
            return f"built for {d0.isoformat()}; the {d.isoformat()} session has opened"


def _doc(root, name):
    from ..util import read_json as rj
    try:
        doc = rj(state_path(root, name), None)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _gone(why, source=None, delay=None, as_of=None):
    return {"status": "no_data", "reason": why, "as_of": as_of, "source": source, "delay": delay}


def _roll(parts):
    """(status, reason) of a section from its parts' statuses: ok if any part is ok, else stale if any is stale (its reason
    first), else no_data"""
    sts = [p.get("status") for p in parts if isinstance(p, dict)]
    if "ok" in sts:
        return "ok", None
    want = "stale" if "stale" in sts else "no_data"
    why = next((p.get("reason") for p in parts if isinstance(p, dict) and p.get("status") == want and p.get("reason")),
               "no part carries a reading")
    return want, why


def _aged(card, why):
    """an ok card shown past its session: stale, numbers kept, the reason said"""
    if card.get("status") == "ok" and why:
        return {**card, "status": "stale", "reason": why}
    return card


# ---- sections ---------------------------------------------------------------------------------------------------------

def map_section(root, now, held):
    doc = _doc(root, "map.json")
    src, dly = "Alpaca option chains and FINRA FNQC short volume", "prior-close open interest; FNQC posts after the close"
    if not doc:
        return _gone("the preopen job has not written a Map yet", src, dly)
    why = stale_why(doc.get("for_session"), now)
    cards = {}
    for sym, c in (doc.get("cards") or {}).items():
        if not isinstance(c, dict):
            continue
        if c.get("status") == "ok" and not ledger.logged(root, c.get("inputs_hash"), held):
            c = _gone("not logged: the ledger holds no row for this card's inputs", c.get("source"), c.get("delay"),
                      c.get("as_of"))
        cards[sym] = _aged(c, why)
    dix = doc.get("dix") if isinstance(doc.get("dix"), dict) else _gone("no DIX block", map_dix_source())
    if dix.get("status") == "ok" and not ledger.logged(root, doc.get("dix_hash"), held):
        dix = _gone("not logged: the ledger holds no row for this DIX", dix.get("source"), dix.get("delay"), dix.get("as_of"))
    dix = _dix_aged(dix, now)
    st, reason = _roll(list(cards.values()) or [dix])           # the gamma cards are the Map; the DIX block carries its own status
    out = {"status": st, "as_of": doc.get("as_of"), "source": src, "delay": dly, "for_session": doc.get("for_session"),
           "label": doc.get("label"), "cards": cards, "dix": dix,
           "sidecar": "morgue-map.json" if (doc.get("sidecar") or {}).get("cards") else None}
    if reason:
        out["reason"] = reason
    return out


def gex_card(root, fund, now):
    """one fund's Map card as the edition would show it (stamped, checked against the ledger, aged), or None without one:
    the single reader the strip's fallback and the Market tab's GEX tiles share"""
    try:
        return (map_section(root, now, ledger.hashes(root)).get("cards") or {}).get(fund)
    except Exception:                                    # noqa: BLE001  (a tile never fails the edition)
        return None


def map_dix_source():
    from . import map_dix
    return map_dix.SOURCE


def _dix_aged(dix, now):
    """a DIX older than the last completed session's file by more than one session is stale"""
    if dix.get("status") != "ok" or not dix.get("file_date"):
        return dix
    try:
        fd = datetime.fromisoformat(dix["file_date"]).date()
    except ValueError:
        return dix
    today = cal._as_date(float(now))
    last = today if (cal.is_trading_day(today) and now >= cal.session_close(today)) else cal.prev_trading_day(today)
    lag = cal.trading_days_between(fd, last)
    if lag > 1:
        return {**dix, "status": "stale", "reason": f"the newest file is {lag} sessions behind the last completed session"}
    return dix


def tape_section(root, now, held):
    doc = _doc(root, "tape.json")
    src = "Alpaca option trades and quotes"
    dly = "the session's prints to the run; the side is signed against the latest quote"
    if not doc:
        return _gone("the postclose job has not written a Tape yet", src, dly)
    why = stale_why(doc.get("for_session"), now)
    hashes = doc.get("hashes") or {}
    cards = {}
    for sym, c in (doc.get("cards") or {}).items():
        if not isinstance(c, dict):
            continue
        if c.get("status") == "ok" and not ledger.logged(root, hashes.get(sym), held):
            c = _gone("not logged: the ledger holds no row for this card's inputs", c.get("source"), c.get("delay"),
                      c.get("as_of"))
        cards[sym] = _aged(c, why)
    st, reason = _roll(list(cards.values()))
    out = {"status": st, "as_of": doc.get("as_of"), "source": src, "delay": dly, "for_session": doc.get("for_session"),
           "window": doc.get("window"), "labels": doc.get("labels") or [], "cards": cards}
    if reason:
        out["reason"] = reason
    return out


def board_section(root, now, held):
    doc = _doc(root, "board.json")
    from . import board_card
    src, dly = board_card.SOURCE, board_card.DELAY
    if not doc:
        return _gone("the preopen job has not written a Board yet", src, dly)
    if not ledger.logged(root, doc.get("inputs_hash"), held):
        return _gone("not logged: the ledger holds no row for this board's inputs", src, dly, doc.get("as_of"))
    why = stale_why(doc.get("for_session"), now)
    out = {"status": "stale" if why else "ok", "as_of": doc.get("as_of"), "source": src, "delay": dly,
           "for_session": doc.get("for_session"), "summary": doc.get("summary"), "weights": doc.get("weights"),
           "top": doc.get("top") or [], "qualified_symbols": doc.get("qualified_symbols") or [],
           "labels": doc.get("labels") or [], "sidecar": "morgue-board.json"}
    if why:
        out["reason"] = why
    return out


def inst_section(root, now, held):
    doc = _doc(root, "inst.json")
    from . import inst_bundle
    src, dly = "SEC EDGAR, SEC 13F data sets and Nasdaq short interest", "public filings; each leaf states its own delay"
    if not doc:
        return _gone("the institutional crawl has not run yet", src, dly)
    if not ledger.logged(root, doc.get("inputs_hash"), held):
        return _gone("not logged: the ledger holds no row for this summary's inputs", src, dly, doc.get("as_of"))
    today = cal._as_date(float(now))
    try:
        age = (today - datetime.fromisoformat(doc["as_of"]).date()).days
    except (KeyError, ValueError):
        age = 99
    stale = f"last assembled {age} days ago" if age > 3 else None
    th, si = doc.get("thirteen_f") or {}, doc.get("short_interest") or {}
    out = {"status": "stale" if stale else "ok", "as_of": doc.get("as_of"), "source": src, "delay": dly,
           "for_session": doc.get("for_session"), "coverage": doc.get("coverage") or [], "floor": doc.get("floor"),
           "thirteen_f": _aged(th, stale) if th else _gone("no 13F data set cached yet", inst_bundle.SRC_13F),
           "insider_buys": doc.get("insider_buys") or [], "short_interest": _aged(si, stale) if si else
           _gone("no short-interest reading cached yet", inst_bundle.SRC_SI),
           "routes": routes.listing(root)}
    if stale:
        out["reason"] = stale
    return out


def studies_section(root, now, held):
    doc = _doc(root, "studies.json")
    src, dly = ("the desk's studies over Alpaca bars, SEC filings and the Morgue ledger",
                "completed sessions only; built after the close")
    if not doc:
        return _gone("the postclose job has not written the studies yet", src, dly)
    why = stale_why(doc.get("for_session"), now)
    hashes = doc.get("hashes") or {}
    comp = {"gap_fill": "study-gap-fill", "orb_ib": "study-orb-ib", "earnings_dist": "study-earnings-dist",
            "wall_validation": "wall-validation", "squeeze": "squeeze-pane", "state_vectors": "state-vectors"}
    body = {}
    for k, c in comp.items():
        s = (doc.get("studies") or {}).get(k)
        if not isinstance(s, dict):
            continue
        if not ledger.logged(root, hashes.get(c), held):
            s = {**_gone("not logged: the ledger holds no row for this study's inputs", src, dly, s.get("as_of")),
                 "state": "unavailable"}
        body[k] = _aged(s, why)
    st, reason = _roll(list(body.values()))
    out = {"status": st, "as_of": doc.get("as_of"), "source": src, "delay": dly, "for_session": doc.get("for_session"),
           **body}
    if reason:
        out["reason"] = reason
    return out


def ledger_section(root, now, rows=None):
    rows = ledger.read(root) if rows is None else rows
    src, dly = "the Morgue ledger (append-only)", "written before each card is shown"
    if not rows:
        return _gone("the ledger holds no row yet", src, dly)
    counts = {}
    for r in rows:
        c = r.get("component") or "unknown"
        counts[c] = counts.get(c, 0) + 1
    sc = _doc(root, "scorecard.json") or {}
    scorecards = None
    if sc:
        mp = dict(sc.get("map") or {})
        mp.pop("grades", None)
        hz = {}
        for cohort, v in (sc.get("board") or {}).items():
            hs = v.get("horizons") or {}
            hz[cohort] = {"n_logged": v.get("n_logged"),
                          "horizons": [{"horizon": h, **{k: hs[h].get(k) for k in ("state", "n_mature", "hit_rate", "mean", "median",
                                                                                   "line")}, "expected": hs[h].get("expected")}
                                       for h in ("1d", "5d", "21d") if h in hs]}
        scorecards = {"board": hz, "map": mp}
    last = rows[-1].get("ts_utc")
    today_iso = cal._as_date(float(now)).isoformat()
    return {"status": "ok", "as_of": (last or "")[:10] or today_iso, "source": src, "delay": dly, "rows_total": len(rows),
            "last_logged_at": last, "components": [{"component": k, "n": v} for k, v in sorted(counts.items())],
            "scorecards": scorecards or {"board": {}, "map": {"state": "not_yet_graded", "line": "no scorecard yet"}},
            "counters": sc.get("counters") or {},
            "rules": ["every card is written to the ledger before it is shown",
                      "outcomes are forward returns at fixed horizons of 1, 5 and 21 sessions, close to close",
                      "an immature horizon says so, with the date its first grade lands",
                      "restatement is a new row, never an edit"]}


_EXT_SRC = {"flow": ("Alpaca option trades and chain snapshots, the Morgue's archived chains",
                     "the session's prints to the run; open interest posts the next morning"),
            "chain": ("Alpaca option contracts and indicative snapshots", "prior-close open interest; snapshot greeks as of the run"),
            "lanes": ("the Morgue's data lanes: archived chains, FINRA per-name short volume, SEC companyfacts",
                      "one file a session; FINRA posts after the close")}
_EXT_GROUP = {"flow": "blocks", "chain": "cards", "lanes": "lanes"}


def _leaf_blocks(node):
    """every stamped block (a dict with a status) under a section group, however it is keyed"""
    if isinstance(node, dict):
        if "status" in node:
            yield node
        else:
            for v in node.values():
                yield from _leaf_blocks(v)


def ext_section(root, name, now, held):
    """one of the extended sections (flow, chain, lanes) from ext.json: logged before shown, stale once a newer session opened,
    each block keeping its own status"""
    src, dly = _EXT_SRC[name]
    doc = (_doc(root, "ext.json") or {}).get(name)
    if not isinstance(doc, dict):
        return _gone({"flow": "the Tape and the Map have written no flow read yet", "chain": "the preopen job has written no chain "
                      "analytics yet", "lanes": "the postclose job has not reported the data lanes yet"}[name], src, dly)
    if not ledger.logged(root, doc.get("inputs_hash"), held):
        return _gone("not logged: the ledger holds no row for this section's inputs", src, dly, doc.get("as_of"))
    why = stale_why(doc.get("for_session"), now)
    group = _EXT_GROUP[name]
    body = doc.get(group) or {}
    leaves = list(_leaf_blocks(body))
    st, reason = _roll(leaves) if leaves else ("no_data", "no block was written")
    if st == "ok" and why:
        st, reason = "stale", why
    out = {"status": st, "as_of": doc.get("as_of"), "source": src, "delay": dly, "for_session": doc.get("for_session")}
    if reason:
        out["reason"] = reason
    if name == "flow":
        out["labels"] = doc.get("labels") or []
        out.update({k: _aged_tree(v, why) for k, v in body.items()})
    elif name == "chain":
        out["cards"] = {k: _aged(v, why) for k, v in body.items() if isinstance(v, dict)}
    else:
        out.update({k: _aged(v, why) for k, v in body.items() if isinstance(v, dict)})
    return out


def _aged_tree(node, why):
    if isinstance(node, dict) and "status" in node:
        return _aged(node, why)
    if isinstance(node, dict):
        return {k: _aged_tree(v, why) for k, v in node.items()}
    return node


# ---- the block and the sidecars -----------------------------------------------------------------------------------------

def raw_block(root, now):
    """the block before it is conformed to the contract: what the sections hold, stamped and checked against the ledger"""
    rows = ledger.read(root)
    held = {r.get("inputs_hash") for r in rows if r.get("inputs_hash")}
    secs = {"map": map_section(root, now, held), "tape": tape_section(root, now, held),
            "board": board_section(root, now, held), "institutional": inst_section(root, now, held),
            "studies": studies_section(root, now, held), "ledger": ledger_section(root, now, rows),
            "flow": ext_section(root, "flow", now, held), "chain": ext_section(root, "chain", now, held),
            "lanes": ext_section(root, "lanes", now, held)}
    sts = [s.get("status") for s in secs.values()]
    root_st = "ok" if "ok" in sts else ("stale" if "stale" in sts else "no_data")
    out = {"schema": SCHEMA, "as_of": cal._as_date(float(now)).isoformat(),
           "built_at": datetime.fromtimestamp(float(now), tz=ET).isoformat(timespec="seconds"), "law": ROOT_LAW,
           "status": root_st, **secs}
    if root_st != "ok":
        out["reason"] = next((s.get("reason") for s in secs.values() if s.get("reason")), "no section carries a reading")
    return out


def block(root, now):
    """edition["morgue"], or None when the engine has written nothing yet (the key is then left off); never raises"""
    try:
        if not any(os.path.exists(state_path(root, n)) for n in ("map.json", "tape.json", "board.json", "inst.json",
                                                                 "studies.json", "ext.json", ledger.LEDGER)):
            return None
        return conform(raw_block(root, now), "morgue", [])
    except Exception as e:                                            # noqa: BLE001  (never into the edition)
        return {"schema": SCHEMA, "as_of": cal._as_date(float(now)).isoformat(),
                "built_at": datetime.fromtimestamp(float(now), tz=ET).isoformat(timespec="seconds"), "law": ROOT_LAW,
                "status": "no_data", "reason": scrub(f"the block could not be built: {type(e).__name__}")}


def sidecars(root, now):
    """{file name: document} for the two sidecars, each only when its card is logged and its file is readable"""
    held = ledger.hashes(root)
    out = {}
    board_doc, full = _doc(root, "board.json"), _doc(root, "board_full.json")
    if board_doc and full and ledger.logged(root, board_doc.get("inputs_hash"), held) and full.get("as_of") == board_doc.get("as_of"):
        out["morgue-board.json"] = _plain(full)
    mp = _doc(root, "map.json")
    if mp and (mp.get("sidecar") or {}).get("cards"):
        ok = all(ledger.logged(root, (c or {}).get("inputs_hash"), held) for c in (mp.get("cards") or {}).values()
                 if isinstance(c, dict) and c.get("status") == "ok")
        if ok:
            out["morgue-map.json"] = _plain(mp["sidecar"])
    return out


def _plain(obj):
    """a sidecar document with finite numbers and scrubbed strings (its own shape, not the edition's allow-list)"""
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_plain(x) for x in obj]
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, str):
        return scrub(obj)
    return obj


def write_sidecars(root, directory, now):
    """write the sidecars into `directory` (cache/terminal/morgue), removing one whose card is not logged -> the names
    written. Never raises."""
    import json
    import os
    try:
        os.makedirs(directory, exist_ok=True)
        docs = sidecars(root, now)
        for name in SIDECARS:
            p = os.path.join(directory, name)
            if name in docs:
                tmp = p + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    json.dump(docs[name], fh, ensure_ascii=False, separators=(",", ":"))
                os.replace(tmp, p)
            elif os.path.exists(p):
                os.remove(p)
        return sorted(docs)
    except OSError:
        return []
