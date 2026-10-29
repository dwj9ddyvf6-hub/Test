"""The Morgue Engine's daily rhythm (Silicon's daily_cycle.py, as functions the host jobs call).

  preopen   about 08:46 ET   the Map (gamma and DIX), the Board, the scorecards; outputs written under state/morgue/
  postclose about 16:46 ET   the Tape, the scorecards (today's close matures the 1-day horizons), the studies
  inst      evenings         the institutional crawl and the 13F bundle (the board reads what it left)

Silicon's cycle ran scripts, collected their exit codes and pushed two JSON files to a GitHub mirror. Here the steps are
functions with the engine's hub and Alpaca client handed in (a test hands in fixtures), a step's failure is reported and
never stops the next, and nothing is pushed from here: the terminal job builds the edition from state/morgue/ and the
publisher ships it (edition.py, desk/terminal/publish.py). Every card is written to the ledger first.

Bars come from the desk's own split-adjusted daily cache (`hub.bars(..., cache_only=True)`), which the genome job keeps
fresh; the cycle fetches no second copy of the roster's history."""
import time
from datetime import datetime

from .. import calendar as cal
from ..terminal import optnews as on
from ..util import ET, write_json_atomic
from . import (FUNDS, board, board_card, cache_path, fetch, flow, flow_card, inst_bundle, ledger, map_dix, map_gex, routes,
               scorecards, state_path, studies_card, studies_feed, tape_card)
from .lanes import finra_shortvol

DAILY_BARS = 1300


def _iso(now):
    return datetime.fromtimestamp(float(now), tz=ET).isoformat(timespec="seconds")


def _hot_gate(clock):
    return lambda: on.hot(clock()) is None


def write_state(root, name, doc):
    write_json_atomic(state_path(root, name), doc)


def load_state(root, name):
    from ..util import read_json
    try:
        doc = read_json(state_path(root, name), None)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def roster():
    from ..sleeves.families.femto_specs import GENOME
    return list(GENOME)


def cached_daily(hub, symbols, n, batch=200):
    """{symbol: the hub's cached daily bars} (cache only: no fetch), in batches"""
    out = {}
    if hub is None:
        return out
    for i in range(0, len(symbols), batch):
        out.update(hub.bars("equity_split", "1d", symbols[i:i + batch], n, cache_only=True) or {})
    return out


# ---- the Map ---------------------------------------------------------------------------------------------------------

def map_row(card, today, underlying):
    """the ledger row of an ok Map card, in the shape scorecards.py grades (component gex_static_v1)"""
    row = {"layer": "map", "component": "gex_static_v1", "underlying": underlying, "as_of": today.isoformat(),
           "spot": card["spot"], "net_gex_usd_per_1pct": card["net_gex_b"] * 1e9, "call_wall": card["call_wall"],
           "put_wall": card["put_wall"], "zero_gamma": card["flip"], "flip_distance_pct": card["flip_distance_pct"],
           "contracts_used": card["contracts_used"], "chain_total": card["chain_total"], "label": map_gex.LABEL}
    row["inputs_hash"] = ledger.inputs_hash({k: row[k] for k in ("underlying", "as_of", "spot", "net_gex_usd_per_1pct",
                                                                 "call_wall", "put_wall", "zero_gamma",
                                                                 "contracts_used")})
    return row


def build_map(root, client, hub, getter, now, today, funds=FUNDS, clock=None, universe=None):
    """the Map card of each fund and the DIX block -> the map.json document (the cards logged first). The gate that keeps the
    reads out of the desk's hot windows asks `clock` (the real clock in a job)."""
    go = _hot_gate(clock or time.time)
    closes = {s: (b[-1]["c"] if b else None) for s, b in cached_daily(hub, list(funds), 5).items()}
    cards, sidecar, ext_chain, ext_flow = {}, {}, {}, {}
    for f in funds:
        if client is None:
            cards[f] = _no_client(today)
            continue
        card, side, extra = map_gex.build_card(client, f, today, now, closes.get(f), go)
        if card["status"] == "ok":
            ext = flow_card.after_map(root, f, extra, today, now)              # chain analytics, flow-GEX, OI reads, the archive
            ext_chain[f] = ext["chain"]
            for name, blk in ext["flow"].items():
                ext_flow.setdefault(name, {})[f] = blk
            row = map_row(card, today, f)
            ledger.append(root, row, now)                             # logged BEFORE it is shown
            card["inputs_hash"] = row["inputs_hash"]
            sidecar[f] = side
        cards[f] = card
    dix, dix_hash = build_dix(root, hub, getter, now, today, funds, roster_names=universe)
    if ext_chain:
        try:
            flow_card.put(root, "chain", {"cards": ext_chain}, today, now)
            flow_card.put(root, "flow", {"blocks": ext_flow}, today, now)
        except Exception:                                                  # noqa: BLE001  (the extended reads never fail the Map)
            pass
    if client is not None and not any(c["status"] == "ok" for c in cards.values()):
        write_state(root, "map.json", {"for_session": today.isoformat(), "as_of": today.isoformat(), "built_at": _iso(now),
                                       "label": map_gex.LABEL, "cards": cards, "dix": dix, "dix_hash": dix_hash,
                                       "sidecar": {"cards": {}}})
        raise RuntimeError("no Map card could be built: " + "; ".join(f"{k}: {c.get('reason')}" for k, c in cards.items()))
    doc = {"for_session": today.isoformat(), "as_of": today.isoformat(), "built_at": _iso(now), "label": map_gex.LABEL,
           "cards": cards, "dix": dix, "dix_hash": dix_hash, "sidecar": {"as_of": today.isoformat(), "cards": sidecar}}
    write_state(root, "map.json", doc)
    return doc


def _no_client(today):
    from . import no_data
    return no_data("no Alpaca client with keys in this process", today.isoformat(), map_gex.SOURCE, map_gex.DELAY)


def sp500_names(root, today, getter):
    """(tickers, route or None, errors): the S&P 500 constituent list, cached for a week"""
    from ..util import read_json
    p = cache_path(root, "sp500.json")
    doc = read_json(p, {}) or {}
    if doc.get("names") and doc.get("day") and (today - datetime.fromisoformat(doc["day"]).date()).days < 7:
        return doc["names"], doc.get("route"), []
    errors = []
    names, route = map_dix.sp500_constituents(getter, errors)
    if names:
        write_json_atomic(p, {"day": today.isoformat(), "route": route, "names": names})
        return names, route, errors
    return (doc.get("names") or []), (doc.get("route") if doc.get("names") else None), errors


def build_dix(root, hub, getter, now, today, funds=FUNDS, roster_names=None):
    """the contract's morgue.map.dix block and the hash it was logged under"""
    try:
        file_date, body, tried = fetch.fnqc_latest(today, getter)
    except Exception as e:                                            # noqa: BLE001
        routes.record(root, "FINRA FNQC short-volume file", "no_data", f"{type(e).__name__}: {str(e)[:100]}", today.isoformat())
        blk = map_dix.dix_block(None, {}, funds, {}, {}, f"{type(e).__name__}: {str(e)[:100]}")
        return blk, None
    if not body:
        why = f"no FNQC file for the last {len(tried)} days (FINRA answers 403 for a file not posted)"
        routes.record(root, "FINRA FNQC short-volume file", "no_data", why, today.isoformat())
        return map_dix.dix_block(None, {}, funds, {}, {}, why), None
    routes.record(root, "FINRA FNQC short-volume file", "ok", None, file_date)
    data = map_dix.parse_fnqc(body)
    etf, avg = map_dix.etf_ratios(data, funds)
    studies_feed.fnqc_append(root, file_date, {k: v["ratio"] for k, v in etf.items()})
    try:
        finra_shortvol.store_day(root, file_date, data)                    # B52: every name's pair, kept for the per-name history
    except OSError:
        pass
    names, route, errors = sp500_names(root, today, getter)
    roster_names = roster_names if roster_names is not None else roster()
    syms = sorted(set(names) | set(roster_names))
    weights = map_dix.dollar_weights(cached_daily(hub, syms, 3)) if hub is not None else {}
    routes.record(root, "S&P 500 constituent list", "ok" if names else "no_data",
                  None if names else ("; ".join(errors) or "no route answered"), today.isoformat())
    index = map_dix.index_block(file_date, data, names, weights, route or "none",
                                weights_error=None if weights else "no cached daily bars")
    rost = map_dix.roster_block(file_date, data, roster_names, weights)
    blk = map_dix.dix_block(file_date, data, funds, index, rost)
    value = {"file_date": file_date, "etf": {k: v["ratio"] for k, v in etf.items()}, "etf_avg": avg,
             "index": index.get("value"), "roster": rost.get("value")}
    h = ledger.inputs_hash(value)
    ledger.append(root, {"layer": "map", "component": "dix", "name": "dix", "value": value, "inputs_hash": h,
                         "grade": "FNQC short volume over total volume; the desk's dollar weights"}, now)
    return blk, h


# ---- the Board -------------------------------------------------------------------------------------------------------

def sectors_from_records(root, symbols):
    """{symbol: {"sector","sub_industry"}} from the crawl's SIC codes"""
    from . import sectors
    out = {}
    for s in symbols:
        rec = inst_bundle.load_record(root, s)
        if rec and rec.get("sic") is not None:
            c = sectors.classify(rec["sic"], rec.get("sic_desc"))
            if c:
                out[s] = c
    return out


def board_bars(hub, symbols, today, now, batch=200):
    """{symbol: the board's bars} read from the hub's cache a batch at a time and converted at once, so the hub's own lists
    (a dict a bar, 1,838 names of 420 sessions) are never all held together"""
    out = {}
    if hub is None:
        return out
    for i in range(0, len(symbols), batch):
        got = hub.bars("equity_split", "1d", symbols[i:i + batch], board_card.BARS, cache_only=True) or {}
        for s, b in got.items():
            out[s] = board_card.to_bars(b, today, now)
        del got
    return out


def build_board(root, hub, now, today, universe=None, bars_by_symbol=None):
    """the Board over the roster from the cached bars -> the board.json document; the rows are logged first and the full
    ranked list is written beside it (board_full.json)"""
    universe = list(dict.fromkeys(universe if universe is not None else roster()))
    if bars_by_symbol is not None:
        bars = {s: board_card.to_bars(b, today, now) for s, b in bars_by_symbol.items()}
    else:
        bars = board_bars(hub, sorted(set(universe) | set(board_card.BENCH)), today, now)
    tape_doc = load_state(root, "tape.json") or {}
    bundle = (load_state(root, "inst_bundle.json") or {}).get("bundle") or {}
    rows, insufficient, market, as_of = board_card.compute(bars, universe, sectors_from_records(root, universe),
                                                           board_card.tape_positioning(tape_doc.get("cards")), bundle)
    n_q = sum(1 for r in rows if r["qualified"])
    summary = {"universe": len(universe), "scored": len(rows), "insufficient_data": len(insufficient), "qualified": n_q,
               "market_context": {k: (None if v is None else round(v, 1)) for k, v in market.items()},
               "gate": {"confirming_min": board.CONFIRM_COUNT, "conviction_min": board.CONVICTION_MIN,
                        "data_confidence_min": board.DC_MIN, "coverage_floor": board.COVERAGE_FLOOR}}
    top = [board_card.public_row(r, as_of) for r in rows[:board_card.TOP]]
    h_summary = ledger.inputs_hash({"as_of_session": as_of, **summary})
    ledger.append(root, {"layer": "board", "component": "board-summary", "name": "genome",
                         "value": {"as_of_session": as_of, **summary}, "inputs_hash": h_summary,
                         "grade": "confluence8 configuration as shipped; the desk's leaf transforms"}, now)
    for r in top:
        v = {"symbol": r["symbol"], "close": r["close"], "score": r["score"], "qualified": r["qualified"]}
        ledger.append(root, {"layer": "board", "component": "board-row", "name": r["symbol"], "value": v,
                             "inputs_hash": ledger.inputs_hash({"as_of": as_of, **v}),
                             "grade": "confluence8 configuration as shipped; the desk's leaf transforms"}, now)
    card_hash = ledger.inputs_hash({"as_of": as_of, "summary": summary, "top": [(r["symbol"], r["score"]) for r in top]})
    ledger.append(root, {"layer": "board", "component": "board-card", "name": "genome",
                         "value": {"as_of": as_of, "top": len(top)}, "inputs_hash": card_hash, "grade": "card of record"}, now)
    doc = {"for_session": today.isoformat(), "as_of": as_of, "built_at": _iso(now), "summary": summary,
           "weights": [{"category": c, "weight": w, "leaves": len(s)} for c, (w, s) in board.CONFIG.items()],
           "top": top, "qualified_symbols": [r["symbol"] for r in rows if r["qualified"]],
           "labels": board_card.LABELS, "inputs_hash": card_hash}
    write_state(root, "board.json", doc)
    write_state(root, "board_full.json", {"as_of": as_of, "columns": board_card.FULL_COLUMNS,
                                         "rows": [board_card.full_row(r) for r in rows], "insufficient": insufficient})
    return doc


# ---- the scorecards --------------------------------------------------------------------------------------------------

def build_scorecards(root, hub, now):
    rows = ledger.read(root)
    syms = scorecards.symbols_needed(rows)
    raw = cached_daily(hub, syms, 90)
    card = scorecards.run(root, raw, now)
    write_state(root, "scorecard.json", card)
    return card


# ---- the Tape --------------------------------------------------------------------------------------------------------

def build_tape(root, client, hub, now, today, funds=FUNDS, clock=None):
    """the Tape card of each fund -> the tape.json document (aggregates and alerts logged first)"""
    go = _hot_gate(clock or time.time)
    daily = cached_daily(hub, list(funds), 300)
    cards, hashes, budget = {}, {}, [tape_card.MAX_REQUESTS]
    ext_flow = {}
    for f in funds:
        bars = daily.get(f) or []
        if client is None:
            cards[f] = _no_client(today)
            continue
        spot, src = map_gex.read_spot(client, f, bars[-1]["c"] if bars else None)
        if spot is None:
            from . import no_data
            cards[f] = no_data(src, today.isoformat(), tape_card.SOURCE, tape_card.DELAY)
            continue
        hi, lo = tape_card.range52(bars)
        card, info = tape_card.build_card(client, f, today, now, spot, hi, lo, go, budget)
        try:
            for name, blk in flow_card.tape_blocks(f, info, today.isoformat()).items():
                ext_flow.setdefault(name, {})[f] = blk
        except Exception as e:                                             # noqa: BLE001  (the flow reads never fail the Tape)
            ext_flow.setdefault("net_drift", {})[f] = no_data_block(f"{type(e).__name__}: {str(e)[:100]}", today)
        if card["status"] == "ok":
            h = ledger.inputs_hash({k: v for k, v in card.items() if k != "alerts"} | {"as_of": today.isoformat()})
            ledger.append(root, {"layer": "tape", "component": "tape-aggregate", "name": f, "value": card,
                                 "inputs_hash": h, "grade": "tape scores as published by the vendors; the side join and "
                                                            "baselines are the desk's, labelled"}, now)
            for a in card["alerts"]:
                ledger.append(root, {"layer": "tape", "component": "tape-alert", "name": f, "value": a,
                                     "inputs_hash": ledger.inputs_hash(a), "grade": "tape scores as published"}, now)
            hashes[f] = h
        cards[f] = card
    doc = {"for_session": today.isoformat(), "as_of": today.isoformat(), "built_at": _iso(now),
           "window": f"{tape_card.session_start_iso(today)} to the run", "labels": tape_card.LABELS, "cards": cards,
           "hashes": hashes}
    write_state(root, "tape.json", doc)
    if client is not None and ext_flow:
        try:
            ext_flow["premium_ratio"] = build_names_ratio(root, client, now, today, go, budget)
            flow_card.put(root, "flow", {"blocks": ext_flow}, today, now, labels=flow_card.LABELS_FLOW)
        except Exception:                                                  # noqa: BLE001
            pass
    if client is not None and not hashes:
        raise RuntimeError("no Tape card could be built: " + "; ".join(f"{k}: {c.get('reason')}" for k, c in cards.items()))
    return doc


def no_data_block(why, today):
    return flow_card._no(why, today.isoformat())


def build_lanes(root, now, today, getter=None, max_new=20):
    """grow the FINRA per-name short-volume history a few files a run (older days, at the host's pace), then say what each data lane
    holds (the `lanes` section). A refusal is the step's failure and the section still reports what is stored."""
    res = finra_shortvol.backfill(root, today, getter, want=260, max_new=max_new)
    flow_card.put(root, "lanes", {"lanes": flow_card.lanes_section(root, today, now)}, today, now)
    if res.get("error"):
        raise RuntimeError("FINRA backfill stopped: " + res["error"])
    return res


def board_names(root, cap=flow_card.NAMES_CAP):
    """the board's top symbols from the card on file (the roster the premium ratio may read; the universe is never read)"""
    doc = load_state(root, "board.json") or {}
    top = doc.get("top") or []
    return [r["symbol"] for r in top if isinstance(r, dict) and r.get("symbol")][:cap]


def build_names_ratio(root, client, now, today, go, budget):
    """the premium ratio of the board's top names (A58): their option prints read through the same request budget as the funds'
    (what the three funds left is all the names get), then flow.premium_ratio over the roster"""
    names = board_names(root)
    as_of = today.isoformat()
    if not names:
        return flow_card.names_block({}, [], as_of)
    by_name, capped = {}, 0
    for sym in names:
        try:
            spot, _src = map_gex.read_spot(client, sym, None)
            if spot is None:
                continue
            _card, info = tape_card.build_card(client, sym, today, now, spot, None, None, go, budget)
            capped += (info or {}).get("capped") or 0
            by_name[sym] = (info or {}).get("signed") or []
        except Exception:                                                  # noqa: BLE001  (one name never stops the rest)
            continue
    return flow_card.names_block(by_name, names, as_of, capped)


# ---- the Studies -----------------------------------------------------------------------------------------------------

def build_studies(root, client, hub, now, today, getter=None, top_names=None):
    """load every study's real inputs, build, log, write -> the studies.json document"""
    daily_raw = cached_daily(hub, list(FUNDS), 300)
    spy = scorecards.dated(daily_raw.get("SPY"), now)
    sessions, intra_note = ({}, "SPY has no cached daily bars")
    if spy:
        sessions, intra_note = studies_feed.fetch_intraday(client, root, "SPY", spy, now)
    days = studies_feed.days_for_studies(sessions, spy) if sessions else []
    ledger_rows = ledger.read(root)
    map_rows = [r for r in ledger_rows if r.get("component") == "gex_static_v1"]
    wall_bars = {s: scorecards.dated(b, now) for s, b in daily_raw.items()}
    # earnings: the board's top names with a crawl record
    board_doc = load_state(root, "board.json") or {}
    names = top_names if top_names is not None else [r["symbol"] for r in (board_doc.get("top") or [])]
    recs = {s: inst_bundle.load_record(root, s) for s in names}
    recs = {s: r for s, r in recs.items() if r and r.get("earnings_dates")}
    earn, earn_note = None, ("no crawl record with 8-K Item 2.02 dates for the board's top names yet" if not recs else None)
    if recs:
        bars = {s: scorecards.dated(b, now) for s, b in cached_daily(hub, sorted(recs), 800).items()}
        rows, pooled = studies_feed.earnings_rows(recs, bars)
        pooled_stats = studies_card.studies.earnings_stats(pooled)
        if pooled_stats["state"] == "graded":
            earn = {"state": "graded", "n_events": len(pooled), "symbols_used": len(rows),
                    "pooled": {k: pooled_stats[k] for k in ("n", "mean", "median", "std", "share_positive", "sharpe")},
                    "rows": rows[:15]}
        else:
            earn_note = pooled_stats.get("reason")
    # squeeze: every crawl record with a short-interest row
    sq_recs, sq_note = [], None
    all_syms = sorted(r for r in names_with_si(root))
    if all_syms:
        sbars = {s: scorecards.dated(b, now) for s, b in cached_daily(hub, all_syms, 40).items()}
        fq = studies_feed.read_lines(studies_feed.fnqc_history_path(root))
        sv = (fq[-1].get("ratios") if fq else {}) or {}
        sq_recs = studies_feed.squeeze_records({s: inst_bundle.load_record(root, s) for s in all_syms}, sbars, sv, today)
    else:
        sq_note = "no short-interest readings cached yet (the institutional crawl has not read any name)"
    map_doc = load_state(root, "map.json") or {}
    gex_b = ((map_doc.get("cards") or {}).get("SPY") or {}).get("net_gex_b")
    iv = _spy_iv(root)
    state_section = studies_feed.state_vector_section(root, spy, gex_b, iv, now) if spy else None
    card = studies_card.build(today.isoformat(), days, days, "SPY", earn, map_rows, wall_bars, sq_recs, state_section,
                              intra_note, earn_note, sq_note)
    hashes = studies_card.log_all(root, card, now)
    doc = {"for_session": today.isoformat(), "as_of": today.isoformat(), "built_at": _iso(now),
           "studies": studies_card.contract(card), "hashes": hashes}
    write_state(root, "studies.json", doc)
    return doc


def names_with_si(root):
    import os
    d = cache_path(root, "inst")
    try:
        files = os.listdir(d)
    except OSError:
        return []
    out = []
    for f in files:
        if not f.endswith(".json"):
            continue
        rec = inst_bundle.load_record(root, f[:-5])
        if rec and rec.get("si") and rec.get("shares_outstanding"):
            out.append(rec["symbol"])
    return out


def _spy_iv(root):
    from ..util import read_json
    from ..terminal import optnews
    try:
        h = (read_json(f"{root}/{optnews.IV_PATH}", {}) or {}).get("names", {}).get("SPY") or []
        return float(h[-1][1]) if h else None
    except (OSError, ValueError, TypeError, IndexError):
        return None


# ---- the institutional crawl -------------------------------------------------------------------------------------------

def crawl_order(root, universe):
    """the roster with the board's ranked names first, the qualified before the rest"""
    top = [r["symbol"] for r in ((load_state(root, "board.json") or {}).get("top") or [])]
    seen = set()
    out = []
    for s in top + list(universe):
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def run_inst(root, hub, now, getter=None, budget_s=1500.0, universe=None, free_mb=None, only=("edgar", "si")):
    """the crawl, the 13F sets, the assembly -> the info dict; inst_bundle.json and inst.json are written"""
    today = cal._as_date(now)
    uni = crawl_order(root, universe if universe is not None else roster())
    stats = inst_bundle.crawl(root, uni, now, budget_s, getter, only=only)
    thirteen, notes13 = ([], [])
    try:
        thirteen, notes13 = inst_bundle.ensure_13f(root, today, getter, free_mb)
    except Exception as e:                                            # noqa: BLE001  (the other leaves stand)
        notes13 = [f"{type(e).__name__}: {str(e)[:120]}"]
    routes.record(root, "SEC Form 13F data sets", "ok" if thirteen else "no_data",
                  None if thirteen else ("; ".join(notes13) or "no data set cached"), today.isoformat())
    adv = {}
    cik = {}
    try:
        cik = inst_bundle.load_cik_map(root, today, getter)
    except Exception:                                                 # noqa: BLE001
        cik = {}
    bundle, detail, notes = inst_bundle.assemble(root, uni, now, adv, thirteen or None,
                                                 inst_bundle.wanted_names(cik, uni))
    write_state(root, "inst_bundle.json", {"as_of": today.isoformat(), "built_at": _iso(now), "bundle": bundle})
    doc = inst_summary(root, uni, bundle, detail, notes, notes13, thirteen, now, today)
    write_state(root, "inst.json", doc)
    return {"ok": True, "crawl": stats, "names": len(uni), "thirteen_f": len(thirteen), "notes13": notes13,
            "coverage": {c["leaf"]: c["names_with_value"] for c in doc["coverage"]}}


def inst_summary(root, universe, bundle, detail, notes, notes13, thirteen, now, today):
    """the contract's morgue.institutional from the assembled bundle (stamped, logged first)"""
    from . import stamp
    n = len(universe)
    cov = []
    for leaf in ("instOwnership", "instActivity", "insiderActivity", "shortPositioning"):
        have = sum(1 for s in universe if (bundle.get(s) or {}).get(leaf, {}).get("score") is not None)
        row = {"leaf": leaf, "names_with_value": have, "names_total": n, "pct": round(have / n * 100.0, 1) if n else 0.0,
               "status": "ok" if have else "no_data"}
        if not have:
            row["reason"] = "no name carries a reading yet"
        cov.append(row)
    tape_doc = load_state(root, "tape.json") or {}
    tape_have = sum(1 for c in (tape_doc.get("cards") or {}).values() if isinstance(c, dict) and c.get("status") == "ok")
    cov.append({"leaf": "optionsPositioning", "names_with_value": tape_have, "names_total": n,
                "pct": round(tape_have / n * 100.0, 1) if n else 0.0, "status": "ok" if tape_have else "no_data",
                **({} if tape_have else {"reason": "no tape card yet; the index funds only"})})
    st = notes.get("cusip_stats") or {}
    cur = thirteen[0] if thirteen else None
    th = (stamp("ok", notes.get("as_of"), inst_bundle.SRC_13F, inst_bundle.DELAY_13F, current_period=notes.get("cur"),
                prior_period=notes.get("prev"), cusip_coverage_pct=round(
                    st.get("names_resolved", 0) / max(st.get("names_wanted", 1), 1) * 100.0, 1),
                names_wanted=st.get("names_wanted", 0), names_resolved=st.get("names_resolved", 0),
                vintage="13F data sets: " + (cur[0] if cur else "none") + " (current)"
                        + (f" against {thirteen[1][0]}" if len(thirteen) > 1 else ""))
          if cur else
          {"status": "no_data", "reason": "; ".join(notes13) or "no 13F data set cached yet", "as_of": None,
           "source": inst_bundle.SRC_13F, "delay": inst_bundle.DELAY_13F, "current_period": None, "prior_period": None,
           "cusip_coverage_pct": None, "names_wanted": 0, "names_resolved": 0, "vintage": None})
    buys = sorted(detail["insider"], key=lambda r: -(r["buy_value_usd"] - r["sell_value_usd"]))
    buys = [b for b in buys if b["buy_value_usd"] > b["sell_value_usd"]][:15]
    si_rows = sorted(detail["short"], key=lambda r: -r["si_pct_shares_out"])[:15]
    si_dates = [r["settlement_date"] for r in detail["short"]]
    si = (stamp("ok", max(si_dates), inst_bundle.SRC_SI, inst_bundle.DELAY_SI, route="Nasdaq republication of FINRA short interest",
                rows=si_rows) if si_rows else
          {"status": "no_data", "reason": "no short-interest reading cached yet", "as_of": None,
           "source": inst_bundle.SRC_SI, "delay": inst_bundle.DELAY_SI, "route": "Nasdaq republication of FINRA short interest",
           "rows": []})
    floor = {"category_weight": board.CONFIG["institutionalPositioning"][0],
             "leaves_designed": len(board.CONFIG["institutionalPositioning"][1]), "leaves_with_route": 5,
             "share_with_route": round(5 / 7, 3),
             "note": "dealer positioning and dark pool have no free route for single stocks; the category scores from "
                     "whichever of its leaves carry a reading and shows how many (no coverage floor)"}
    doc = {"for_session": today.isoformat(), "as_of": today.isoformat(), "built_at": _iso(now), "coverage": cov,
           "floor": floor, "thirteen_f": th, "insider_buys": buys, "short_interest": si}
    doc["inputs_hash"] = ledger.inputs_hash({"as_of": doc["as_of"], "coverage": cov, "buys": [b["symbol"] for b in buys]})
    ledger.append(root, {"layer": "institutional", "component": "inst-summary", "name": "roster",
                         "value": {"coverage": cov}, "inputs_hash": doc["inputs_hash"],
                         "grade": "SEC and Nasdaq public routes; the desk's leaf transforms"}, now)
    return doc


# ---- the two cycles ------------------------------------------------------------------------------------------------------

def _step(name, fn, out):
    t0 = time.time()
    try:
        fn()
        out[name] = {"ok": True, "s": round(time.time() - t0, 1)}
    except Exception as e:                                            # noqa: BLE001  (a step's failure never stops the next)
        out[name] = {"ok": False, "s": round(time.time() - t0, 1), "error": f"{type(e).__name__}: {str(e)[:160]}"}


def preopen(root, hub, client, now, getter=None, universe=None, bars_by_symbol=None, clock=None):
    """map, board, scorecards -> {"ok", "steps"}; skipped on a day without a session"""
    today = cal._as_date(now)
    if not cal.is_trading_day(today):
        return {"ok": True, "skipped": "no session today"}
    steps = {}
    _step("map", lambda: build_map(root, client, hub, getter, now, today, clock=clock, universe=universe), steps)
    _step("board", lambda: build_board(root, hub, now, today, universe, bars_by_symbol), steps)
    _step("scorecards", lambda: build_scorecards(root, hub, now), steps)
    return _finish(root, "preopen", steps, now)


def postclose(root, hub, client, now, getter=None, clock=None):
    """tape, scorecards, studies -> {"ok", "steps"}"""
    today = cal._as_date(now)
    if not cal.is_trading_day(today):
        return {"ok": True, "skipped": "no session today"}
    steps = {}
    _step("tape", lambda: build_tape(root, client, hub, now, today, clock=clock), steps)
    _step("scorecards", lambda: build_scorecards(root, hub, now), steps)
    _step("studies", lambda: build_studies(root, client, hub, now, today, getter), steps)
    _step("lanes", lambda: build_lanes(root, now, today, getter), steps)
    return _finish(root, "postclose", steps, now)


def _finish(root, mode, steps, now):
    ok = all(s["ok"] for s in steps.values())
    doc = load_state(root, "cycle.json") or {}
    doc[mode] = {"at": _iso(now), "ok": ok, "steps": steps}
    write_state(root, "cycle.json", doc)
    return {"ok": ok, "steps": steps}


# ---- the jobs (desk/jobs.py) -------------------------------------------------------------------------------------------

def _client(engine):
    """the desk's Alpaca market-data client when this process holds keys, else None (the Map and the Tape then say so)"""
    return on._client(engine)


def job_preopen(engine, now=None):
    """job `morgue_preopen`: the Map, the Board and the scorecards, about 08:46 ET"""
    now = float(engine.clock() if now is None else now)
    res = preopen(engine.root, engine.hub, _client(engine), now)
    res["client"] = _client(engine) is not None
    return res


def job_postclose(engine, now=None):
    """job `morgue_postclose`: the Tape, the scorecards and the studies, about 16:46 ET"""
    now = float(engine.clock() if now is None else now)
    res = postclose(engine.root, engine.hub, _client(engine), now)
    res["client"] = _client(engine) is not None
    return res


def job_inst(engine, now=None):
    """job `morgue_inst`: the institutional crawl under a time budget (longer at weekends), resumable"""
    from .. import jobs
    now = float(engine.clock() if now is None else now)
    weekend = datetime.fromtimestamp(now, tz=ET).isoweekday() >= 6
    info = run_inst(engine.root, engine.hub, now, budget_s=7200.0 if weekend else 2400.0,
                    free_mb=jobs.disk_free_mb(engine.root))
    return info
