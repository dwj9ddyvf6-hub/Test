"""The extended reads' blocks and store (REA work packages 3 and 5): glue between the pure functions (flow.py, opt_ext.py, the
lanes) and the cycle. Every block is stamped (status ok / no_data with the reason, as_of, source, delay).

State: state/morgue/ext.json holds three sections, `flow` (built after the close from the Tape's prints), `chain` (built before the
open from the Map's chain) and `lanes` (what each data lane holds). A section is replaced when a new session writes it and
accumulates per underlying within a session. Each write is logged to the ledger first (a section's hash; the edition shows a
section only when the ledger holds it). iv_history.jsonl starts the IV history (one row an underlying and session)."""
import json
import os
from datetime import datetime, timedelta, timezone

from .. import calendar as cal
from ..util import ET, read_json, write_json_atomic
from . import flow, ledger, map_gex, no_data, opt_ext, stamp, state_path
from .lanes import chain_archive, finra_shortvol

EXT = "ext.json"
IV_HISTORY = "iv_history.jsonl"
NAMES_CAP = 8                      # board names whose prints the premium ratio reads (the request budget is shared)
LABELS_FLOW = [
    "net drift: each five-minute bucket stands alone (net single-leg premium and volume by direction), never a running total",
    "repeat sweeps: the same contract swept three or more times inside ten minutes; the tier names are by the run's own span",
    "HIRO: side x delta x size x 100 x spot per signed print, SPY, QQQ and IWM only; the vendor's retail-only and hedged-flow filters are not built",
    "premium ratio: the board's top names only, from the prints the shared request budget allowed",
    "open interest changes and the next-day confirmation need the archived chain of the earlier session",
]
LABEL_FLOW_GEX = ("flow-GEX: each contract weighted by the latest daily volume in the snapshot (the previous session's before the "
                  "open), beside the open-interest form; same signs")
LABEL_ASSUME = "convention-signed: calls positive, puts negative; prior-close open interest"


def _ok(as_of, **kw):
    return stamp("ok", as_of, flow.SOURCE, flow.DELAY, **kw)


def _no(why, as_of, **kw):
    return no_data(why, as_of, flow.SOURCE, flow.DELAY, **kw)


def _r(x, k=4):
    return None if x is None else round(float(x), k)


# ---- postclose: the Tape's prints ---------------------------------------------------------------------------------------------

def tape_blocks(und, info, as_of):
    """{block name: block} for one fund from build_card's info ({"signed","deltas"}); no_data blocks say why"""
    sp = (info or {}).get("signed") or []
    if not sp:
        why = "no scoreable print in the window"
        return {k: _no(why, as_of) for k in ("net_drift", "repeat_sweeps", "flow_ratio", "hiro")}
    out = {"net_drift": _ok(as_of, bucket_min=flow.BUCKET_MIN, buckets=flow.net_drift(sp)),
           "repeat_sweeps": _ok(as_of, window_min=flow.SWEEP_WINDOW_MIN, min_count=flow.SWEEP_MIN_COUNT,
                                alerts=flow.repeat_sweeps(sp))}
    fr = flow.flow_ratio(sp)
    out["flow_ratio"] = (_ok(as_of, **{k: v for k, v in fr.items() if k != "reason"}) if fr["ratio"] is not None
                         else _no(fr["reason"], as_of, **{k: v for k, v in fr.items() if k != "reason"}))
    spot = info.get("spot")
    h = flow.hiro(sp, info.get("deltas") or {}, spot, und) if spot else {"status": "no_data", "reason": "no spot"}
    out["hiro"] = (_ok(as_of, **{k: v for k, v in h.items() if k not in ("status", "reason")}) if h["status"] == "ok"
                   else _no(h["reason"], as_of))
    return out


def names_block(by_name, allowed, as_of, capped=0):
    """the premium ratio of the board and watching names only"""
    if not allowed:
        return _no("no board or watching names to read", as_of)
    r = flow.premium_ratio(by_name, allowed)
    if not r["names"]:
        return _no("none of the roster's names printed an option", as_of)
    return _ok(as_of, names=r["names"], ignored=r["ignored"] + capped)


# ---- preopen: the Map's chain ------------------------------------------------------------------------------------------------

def iv_history(root, underlying, before):
    out = []
    try:
        with open(state_path(root, IV_HISTORY), encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if r.get("und") == underlying and r.get("date") < before and r.get("iv30") is not None:
                    out.append(r["iv30"])
    except OSError:
        pass
    return out


def iv_append(root, underlying, day, summary):
    p = state_path(root, IV_HISTORY)
    seen = set()
    try:
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                    seen.add((r.get("und"), r.get("date")))
                except ValueError:
                    pass
    except OSError:
        pass
    if (underlying, day) in seen:
        return False
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"und": underlying, "date": day, **{k: summary.get(k) for k in ("iv30", "iv60", "slope_30_60", "rr25",
                                                                                        "strangle15", "butterfly25")}}) + "\n")
    return True


def chain_card(root, und, extra, today, now):
    """the chain analytics card of one fund from map_gex.build_card's extra (the rows it was built from)"""
    as_of = today.isoformat()
    when = datetime.fromtimestamp(float(now), tz=timezone.utc)
    spot = extra["spot"]
    rows = opt_ext.rows_of(extra["chain"], extra["snaps"], spot, und, when)
    if not rows:
        return no_data("no contract carried a gamma", as_of, map_gex.SOURCE, map_gex.DELAY, spot=_r(spot, 2))
    dex, vex, chm = opt_ext.dex_profile(rows, spot), opt_ext.vex_profile(rows, spot), opt_ext.charm_profile(rows, spot)
    mp, ks = opt_ext.max_pain(rows), opt_ext.key_strikes(rows, spot)
    surf = opt_ext.iv_surface_summary(rows, spot)
    rank = opt_ext.iv_rank(iv_history(root, und, as_of), surf["iv30"])
    iv_append(root, und, as_of, surf)
    b = lambda x: None if x is None else round(x / 1e9, 4)
    return stamp("ok", as_of, map_gex.SOURCE, map_gex.DELAY, spot=_r(spot, 2), dex_b=b(dex["net"]),
                 dex_balance=_r(dex["balance"], 2), vex_b=b(vex["net"]), charm_b_per_day=b(chm["net"]),
                 max_pain=(mp or {}).get("strike"), max_pain_expiry=(mp or {}).get("expiry"),
                 key_gamma_strike=ks["key_gamma"], anchor_strike=ks["anchor"], key_delta_strike=ks["key_delta"],
                 g_coord=_r(opt_ext.g_coordinate(rows), 4), iv30=_r(surf["iv30"]), iv60=_r(surf["iv60"]),
                 slope_30_60=_r(surf["slope_30_60"]), rr25=_r(surf["rr25"]), strangle15=_r(surf["strangle15"]),
                 butterfly25=_r(surf["butterfly25"]), iv_rank=_r(rank["rank"], 1), iv_rank_n=rank["n"],
                 atm_by_expiry=[{"days": x["days"], "atm_iv": _r(x["atm_iv"])} for x in surf["atm_by_expiry"]][:12],
                 label=LABEL_ASSUME)


def flow_gex_block(und, extra, today, now):
    as_of = today.isoformat()
    when = datetime.fromtimestamp(float(now), tz=timezone.utc)
    vols = extra.get("volumes") or {}
    if not vols:
        return _no("the snapshots carry no daily volume", as_of)
    spot = extra["spot"]
    v = map_gex.gex_profile(extra["chain"], extra["snaps"], spot, und, when, weight="volume", volumes=vols)
    o = extra.get("profile") or map_gex.gex_profile(extra["chain"], extra["snaps"], spot, und, when)
    if not v["contracts_used"]:
        return _no("no contract had both a gamma and a volume", as_of)
    return _ok(as_of, weight="volume", net_gex_b=_r(v["net_gex"] / 1e9, 3), oi_net_gex_b=_r(o["net_gex"] / 1e9, 3),
               call_wall=v["call_wall"], put_wall=v["put_wall"], contracts_used=v["contracts_used"], label=LABEL_FLOW_GEX)


def oi_blocks(root, und, extra, today):
    """(oi_change, oi_confirm) blocks: today's chain against the previous archived day, and the previous session's alerts against
    today's open interest. Both need the archive: the first archived day has nothing to compare."""
    as_of = today.isoformat()
    chain = extra["chain"]
    prev_day = chain_archive.previous_day(root, und, as_of)
    prev = chain_archive.read_day(root, und, prev_day) if prev_day else None
    if not prev:
        no = "no earlier archived chain to compare with (the archive starts with this session)"
        return _no(no, as_of), _no(no, as_of)
    prev_oi = {k: v["oi"] for k, v in prev["contracts"].items() if v.get("oi") is not None}
    top = flow.oi_change_top(chain, prev_oi)
    change = _ok(as_of, prev_date=prev_day, rows=top) if top else _no("no contract's open interest changed", as_of)
    alerts = _prev_alerts(root, und, today)
    if alerts is None:
        return change, _no("the Tape's alerts of the previous session are not on file", as_of)
    if not alerts:
        return change, _no("the previous session raised no alert on this fund", as_of)
    c = flow.oi_confirm(alerts, prev_oi, {c["symbol"]: c["oi"] for c in chain})
    return change, _ok(as_of, alert_date=prev_day, counts=c["counts"], rows=c["rows"][:25])


def _prev_alerts(root, und, today):
    """the alerts of the previous session's Tape card for `und`, or None when the Tape on file is not that session's"""
    doc = read_json(state_path(root, "tape.json"), None)
    prev = cal.prev_trading_day(today).isoformat()
    if not isinstance(doc, dict) or doc.get("for_session") != prev:
        return None
    card = (doc.get("cards") or {}).get(und) or {}
    return [a for a in card.get("alerts") or [] if a.get("contract") and a.get("size")] if card.get("status") == "ok" else []


def after_map(root, und, extra, today, now):
    """all the chain-side blocks of one fund -> {"chain": card, "flow": {name: block}}; the chain is archived last. Never raises."""
    as_of = today.isoformat()
    out = {"chain": None, "flow": {}}
    try:
        out["chain"] = chain_card(root, und, extra, today, now)
    except Exception as e:                                            # noqa: BLE001
        out["chain"] = _no(f"{type(e).__name__}: {str(e)[:100]}", as_of)
    try:
        out["flow"]["flow_gex"] = flow_gex_block(und, extra, today, now)
    except Exception as e:                                            # noqa: BLE001
        out["flow"]["flow_gex"] = _no(f"{type(e).__name__}: {str(e)[:100]}", as_of)
    try:
        out["flow"]["oi_change"], out["flow"]["oi_confirm"] = oi_blocks(root, und, extra, today)
    except Exception as e:                                            # noqa: BLE001
        out["flow"]["oi_change"] = out["flow"]["oi_confirm"] = _no(f"{type(e).__name__}: {str(e)[:100]}", as_of)
    try:
        vols = extra.get("volumes") or {}
        rows = [{**c, "volume": vols.get(c["symbol"]), "iv": (extra["snaps"].get(c["symbol"]) or {}).get("iv"),
                 "gamma": (extra["snaps"].get(c["symbol"]) or {}).get("gamma")} for c in extra["chain"]]
        chain_archive.archive_chain(root, und, as_of, rows, extra["spot"], extra.get("oi_date"))
    except Exception:                                                 # noqa: BLE001  (the archive is a lane: its failure costs only it)
        pass
    return out


# ---- the lanes' status ---------------------------------------------------------------------------------------------------------

def lanes_section(root, today, now):
    as_of = today.isoformat()
    lanes = {}
    for und in ("SPY", "QQQ", "IWM"):
        st = chain_archive.status(root, und)
        lanes.setdefault("chain_archive", {"funds": {}})["funds"][und] = st
    ca = lanes["chain_archive"]["funds"]
    n = max(v["days"] for v in ca.values())
    lanes["chain_archive"] = (stamp("ok", as_of, "the desk's own Map reads", "one file a session; kept 400 sessions", days=n,
                                    first_date=min((v["first_date"] for v in ca.values() if v["first_date"]), default=None),
                                    last_date=max((v["last_date"] for v in ca.values() if v["last_date"]), default=None),
                                    bytes=sum(v["bytes"] for v in ca.values())) if n else
                              no_data("no chain archived yet", as_of, "the desk's own Map reads", "one file a session"))
    ds = finra_shortvol.days(root)
    lanes["short_volume"] = (stamp("ok", as_of, finra_shortvol.SOURCE, finra_shortvol.DELAY, days=len(ds), first_date=ds[0],
                                   last_date=ds[-1]) if ds else
                             no_data("no FINRA day stored yet", as_of, finra_shortvol.SOURCE, finra_shortvol.DELAY))
    from .lanes import sec_facts
    try:
        names = len([n for n in os.listdir(state_path(root, sec_facts.DIR)) if n.endswith(".json.gz")])
    except OSError:
        names = 0
    lanes["sec_facts"] = (stamp("ok", as_of, sec_facts.SOURCE, sec_facts.DELAY, names=names) if names else
                          no_data("no company's facts stored yet", as_of, sec_facts.SOURCE, sec_facts.DELAY))
    return lanes


# ---- the store -------------------------------------------------------------------------------------------------------------------

def put(root, section, patch, today, now, labels=None):
    """merge `patch` into section `section` of ext.json for the session `today` and log it -> the section.
    patch: {"blocks": {name: {key: block}}} for flow, {"cards": {und: card}} for chain, {"lanes": {name: block}} for lanes, or
    {"blocks": {name: block}} for a block that is not per underlying (premium_ratio)."""
    doc = read_json(state_path(root, EXT), None)
    doc = doc if isinstance(doc, dict) else {}
    sec = doc.get(section) if isinstance(doc.get(section), dict) and doc[section].get("for_session") == today.isoformat() else {}
    sec = {**sec, "for_session": today.isoformat(), "as_of": today.isoformat(),
           "built_at": datetime.fromtimestamp(float(now), tz=ET).isoformat(timespec="seconds")}
    if labels:
        sec["labels"] = labels
    for group, items in patch.items():
        cur = dict(sec.get(group) or {})
        for k, v in items.items():
            if isinstance(v, dict) and group == "blocks" and not v.get("status"):
                cur[k] = {**(cur.get(k) or {}), **v}                   # per-underlying blocks: merge by key
            else:
                cur[k] = v
        sec[group] = cur
    sec.pop("inputs_hash", None)
    h = ledger.inputs_hash(sec)
    sec["inputs_hash"] = h
    ledger.append(root, {"layer": "ext", "component": f"{section}-ext", "name": section, "inputs_hash": h,
                         "value": {"for_session": sec["for_session"], "keys": sorted(k for g in patch.values() for k in g)},
                         "grade": "derived from the Map's chain and the Tape's prints; the formulas are the vendors' published ones"},
                  now)
    doc[section] = sec
    write_json_atomic(state_path(root, EXT), doc)
    return sec
