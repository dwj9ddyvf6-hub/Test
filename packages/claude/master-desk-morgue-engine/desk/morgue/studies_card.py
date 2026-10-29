"""The Studies card: gap fill (S1), opening range (S2), earnings (S3), wall validation (S4), squeeze (S5), state vectors (S6),
assembled ledger-first.

Ported from Silicon's studies_card.py with the defect fixed: the card is built from the inputs studies_feed.py loads, and a
study whose input is missing says which one (`state` unavailable or no_data with the reason), instead of the placeholder every
live run produced. build() is pure (inputs in, card out) so a test serves fixtures; cycle.py does the loading and the
ledger writes."""
from datetime import datetime, timezone

from . import ledger, no_data, squeeze as squeeze_mod, stamp, studies, wall_study

SOURCE = "the desk's studies over Alpaca bars, SEC filings and the Morgue ledger"
DELAY = "completed sessions only; built after the close"


def unavailable(reason, **kw):
    return {"state": "unavailable", "n": 0, "reason": reason, **kw}


def _st(state):
    """the contract's status of a study's finer state"""
    return "ok" if state == "graded" else "no_data"


def _wrap(body, as_of, reason_default):
    """a study's body with its stamp: status from `state`, the reason when not graded"""
    status = _st(body.get("state"))
    out = dict(body)
    out.update(status=status, as_of=as_of, source=SOURCE, delay=DELAY)
    if status != "ok":
        out["reason"] = body.get("reason") or body.get("line") or reason_default
    else:
        out.pop("reason", None)
    return out


def build(as_of, gap_days=None, orb_days=None, symbol="SPY", earnings=None, map_rows=None, bars_by_symbol=None,
          squeeze_recs=None, state_section=None, intraday_note=None, earnings_note=None, squeeze_note=None):
    """the studies card from loaded inputs -> the internal card (Silicon's shape, each study stamped)
    The wall study uses the ledger's Map cards and the completed daily bars; the others their loaded inputs. A missing
    input is the study's reason, with `*_note` carrying the loader's exact failure."""
    no_intra = unavailable(intraday_note or "no 1-minute bars loaded for the sessions", symbol=symbol)
    gap = studies.gap_fill_study(gap_days) if gap_days else dict(no_intra)
    gap["symbol"] = symbol
    orb = studies.orb_ib_study(orb_days) if orb_days else {str(w): dict(no_intra) for w in studies.WINDOWS}
    if earnings is None:
        earnings = unavailable(earnings_note or "no earnings events loaded", n_events=0)
    wall = wall_study.wall_validation(map_rows or [], bars_by_symbol or {})
    if squeeze_recs:
        sq = squeeze_mod.build_pane(squeeze_recs, as_of)
    else:
        sq = {"state": "unavailable", "as_of": as_of, "formula_version": squeeze_mod.FORMULA_VERSION, "rows": [],
              "excluded": {}, "reason": squeeze_note or "no short-interest readings loaded"}
    state = state_section if state_section is not None else {
        "state": "insufficient_history", "history_sessions_accrued": 0, "p_nn": None,
        "reason": "no accrued state history yet"}
    return {"as_of": as_of, "gap_fill": gap, "orb_ib": orb, "earnings_dist": earnings, "wall_validation": wall,
            "squeeze": sq, "state_vectors": state}


def log_all(root, card, now):
    """the ledger rows BEFORE the card is shown (design law): one per study -> {component: inputs_hash}"""
    hashes = {}
    for component, name, value in (
            ("study-gap-fill", "gap-fill", _brief(card["gap_fill"])),
            ("study-orb-ib", "orb-ib", {k: _brief(v) for k, v in card["orb_ib"].items()}),
            ("study-earnings-dist", "earnings", _brief(card["earnings_dist"])),
            ("wall-validation", "map-walls", {"state": card["wall_validation"]["state"],
                                              "cards_graded": card["wall_validation"]["cards_graded"],
                                              "cards_of_record": card["wall_validation"]["cards_of_record"]}),
            ("squeeze-pane", "squeeze", {"state": card["squeeze"]["state"], "gated_n": card["squeeze"].get("gated_n", 0)}),
            ("state-vectors", "state-vectors", _brief(card["state_vectors"]))):
        h = ledger.inputs_hash(value)
        ledger.append(root, {"layer": "studies", "component": component, "name": name, "value": value,
                             "inputs_hash": h, "grade": "pure scorers over loaded inputs; transforms declared per study"},
                      now)
        hashes[component] = h
    return hashes


def _brief(body):
    return {k: v for k, v in body.items() if k not in ("partitions", "rows", "excluded", "grades")}


GAP_KEYS = ("state", "symbol", "n", "fills", "frequency", "fill_pct", "by_band", "by_weekday", "reason")
ORB_KEYS = ("state", "n", "break_one_side", "break_both", "no_break", "break_one_side_rate", "break_both_rate",
            "no_break_rate", "extension_n", "reason")
EARN_KEYS = ("state", "n_events", "symbols_used", "pooled", "rows", "reason")
WALL_KEYS = ("state", "cards_of_record", "cards_graded", "line", "reason")
RATE_KEYS = ("state", "n", "call_wall_held_rate", "put_wall_held_rate", "touched_and_held", "touched_and_held_rate",
             "blown_through", "blown_through_rate", "flip_respected_rate")
SQ_KEYS = ("state", "formula_version", "gated_n", "rows", "note", "reason")
SQ_ROW = ("symbol", "score", "si_pct_float", "si_change_pct", "days_to_cover", "short_volume_ratio", "momentum_5d",
          "already_ran", "borrow_fee_state", "volatility_rms_ex_largest", "float_rotation_5d", "relative_volume_capped")
SV_KEYS = ("state", "history_sessions_accrued", "p_nn", "neighbours", "n_neighbours", "p10", "p50", "p90", "nearest_distance",
           "reason")


def _pick(d, keys):
    return {k: d[k] for k in keys if k in d}


def contract(card):
    """the contract's morgue.studies (docs/research/MORGUE_SCHEMA.md) from the internal card: every study stamped, its detail
    cut to the keys the contract names (the dicts keyed by window or underlying become lists)"""
    as_of = card["as_of"]
    g = _wrap(_pick(card["gap_fill"], GAP_KEYS) | _flat(card["gap_fill"]), as_of, "no gapped session in the sample")
    orb = {"symbol": card["gap_fill"].get("symbol"), "windows": []}
    for w, body in card["orb_ib"].items():
        ext = body.get("extension_rates") or {}
        b = _pick(body, ORB_KEYS)
        b.update(window_min=int(w), status=_st(body.get("state")), ext_0_5=ext.get("0.5"), ext_1_0=ext.get("1.0"),
                 ext_1_5=ext.get("1.5"))
        if b["status"] != "ok":
            b["reason"] = body.get("reason") or "no completed session with an opening range"
        orb["windows"].append(b)
    ed = _wrap(_pick(card["earnings_dist"], EARN_KEYS), as_of, "no earnings events")
    wv = card["wall_validation"]
    wall = _pick(wv, WALL_KEYS)
    wall["windows"] = [{"window": k, **_pick(v, RATE_KEYS)} for k, v in (wv.get("windows") or {}).items()]
    wall["by_underlying"] = [{"key": k, **_pick(v, RATE_KEYS)} for k, v in (wv.get("by_underlying") or {}).items()]
    wall["by_regime"] = [{"key": k, **_pick(v, RATE_KEYS)} for k, v in (wv.get("by_regime") or {}).items()]
    wall = _wrap(wall, as_of, "not yet graded")
    sqz = card["squeeze"]
    sqb = _pick(sqz, SQ_KEYS)
    sqb["rows"] = [_pick(r, SQ_ROW) for r in (sqz.get("rows") or [])[:15]]
    sqb["excluded_n"] = len(sqz.get("excluded") or {})
    sqb["note"] = ((sqz.get("note") or "").rstrip(". ") + ". " if sqz.get("note") else "") + (
        "The published formula's gate and filters are the pane's own; the vendor's calibration figures are not reproduced here.")
    sq_ = _wrap(sqb, as_of, "no names pass the published gate")
    st = _wrap(_pick(card["state_vectors"], SV_KEYS), as_of, "waiting for 126 accrued sessions")
    return {"gap_fill": g, "orb_ib": orb, "earnings_dist": ed, "wall_validation": wall, "squeeze": sq_, "state_vectors": st}


def _flat(gap):
    """by_band and by_weekday as lists, from Silicon's partitions"""
    p = gap.get("partitions") or {}
    return {"by_band": [{"band": k, **v} for k, v in (p.get("by_band") or {}).items()],
            "by_weekday": [{"weekday": k, **v} for k, v in (p.get("by_weekday") or {}).items()]} if p else {}


def now_iso(now):
    return datetime.fromtimestamp(float(now), tz=timezone.utc).isoformat()


__all__ = ["build", "log_all", "contract", "unavailable", "stamp", "no_data"]
