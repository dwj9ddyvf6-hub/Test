"""Lazarus Q07 weekly lanes — shared fire-consumer engine (batch 4).

Source rule (catalog §4.1, SLEEVE-CATALOG-CONSOLIDATED-2026-10-23):
take the Tensor 1W signal of the named family (Green / Swing) in the
named cap band (SM = small, ML = mid/large), apply the named alt-data
filters, buy only on a QQQ-down day within 5 sessions of the signal,
exit on a 15% stop or at the time horizon in the name (52 / 78 weeks).
Standard sizing 1 slot at $1,000; exceptions in SPECS below.

Fires arrive via the desk's composer producer (CSV producer
"sleeve_feed composer (tracker ledger + alt-data tags)", fire file
shadow/paper_sleeve/live/sleeve_fires_v1.json — research-archive is
unreachable from this box, V3-SCOPE §3.4, so lanes consume the v3
snapshot's "fires" key, the research-lane ingest contract; no fresh
fires => fail closed, emit nothing).

Fire shape (flexible keys, tags under fire["tags"] or flat):
  {symbol, family ("green"|"w_green"|"swing"|"w_swing"), band
   ("small"|"sm"|"midlarge"|"ml"), signal_date, price,
   tags: {deep70: bool, wiki_cov: bool / wiki_views: int,
          wiki_low: bool, tier / tier_a, ats_z: float,
          mom6 / mom6_pct: float}}
Filter readings where the sources are thin (FIDELITY-LEDGER LAZ4):
  deep70  — explicit tag, else price <= 70% of trailing high in bars
  cheap5  — price < $5 (computed from the fire/bars price, no tag)
  wcov    — wiki_cov tag true, or wiki_views > 0
  wlow    — wiki_low tag true
  tierA   — tier == "A" or tier_a true
  ats_z1  — dark-pool ats_z >= 1.0
  mom6    — mom6_pct > 0, else 126-session return > 0 from bars
A filter with NO evidence (tag absent and not computable) fails
closed — the composer is the alt-data producer; missing tag = unfed.
"""
from __future__ import annotations
import datetime as _dt

# sleeve_id -> spec. budget = total slice; slots = slot count;
# per-slot budget = budget / slots.
SPECS = {
    "s_q07w_g52_sm_deep70_wcov": dict(family="green", band="small", horizon_w=52,
        filters=("deep70", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g78_sm_tierA_wcov": dict(family="green", band="small", horizon_w=78,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g78_sm_deep70_wcov": dict(family="green", band="small", horizon_w=78,
        filters=("deep70", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g52_ml_tierA_wcov": dict(family="green", band="midlarge", horizon_w=52,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g78_ml_tierA_wcov": dict(family="green", band="midlarge", horizon_w=78,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g52_ml_ats_z1_mom6_wlow": dict(family="green", band="midlarge", horizon_w=52,
        filters=("ats_z1", "mom6", "wlow"), slots=1, budget=1000.0, parked=False),
    "s_q07w_s52_sm_cheap5_wcov": dict(family="swing", band="small", horizon_w=52,
        filters=("cheap5", "wcov"), slots=1, budget=1000.0, parked=True),
    "s_q07w_s52_sm_deep70_wcov": dict(family="swing", band="small", horizon_w=52,
        filters=("deep70", "wcov"), slots=1, budget=1000.0, parked=True),
    "s_q07w_s78_sm_cheap5_wcov": dict(family="swing", band="small", horizon_w=78,
        filters=("cheap5", "wcov"), slots=1, budget=1194.0, parked=True),
    "s_q07w_s78_sm_deep70_wcov": dict(family="swing", band="small", horizon_w=78,
        filters=("deep70", "wcov"), slots=2, budget=2265.0, parked=True),
    # --- batch 5 (LAZ-B5): swing ML parked + cyan/green ins2/vix20 lanes
    "s_q07w_s52_ml_deep70_wlow": dict(family="swing", band="midlarge", horizon_w=52,
        filters=("deep70", "wlow"), slots=1, budget=1000.0, parked=True),
    "s_q07w_s52_ml_deep70_vix20_wlow": dict(family="swing", band="midlarge", horizon_w=52,
        filters=("deep70", "vix20", "wlow"), slots=1, budget=1000.0, parked=True),
    "s_q07w_s78_ml_deep70_wcov": dict(family="swing", band="midlarge", horizon_w=78,
        filters=("deep70", "wcov"), slots=1, budget=1000.0, parked=True),
    "s_q07w_s78_ml_deep70_mom6_wlow": dict(family="swing", band="midlarge", horizon_w=78,
        filters=("deep70", "mom6", "wlow"), slots=1, budget=1000.0, parked=True),
    "s_q07w_c52_sm_cheap5_ins2_mom6": dict(family="cyan", band="small", horizon_w=52,
        filters=("cheap5", "ins2", "mom6"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_sm_deep70_ins2_vix20": dict(family="cyan", band="small", horizon_w=78,
        filters=("deep70", "ins2", "vix20"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_sm_ins2_mom6_vix20": dict(family="cyan", band="small", horizon_w=78,
        filters=("ins2", "mom6", "vix20"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g78_sm_deep70_ins2": dict(family="green", band="small", horizon_w=78,
        filters=("deep70", "ins2"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g52_sm_deep70_ins2_vix20": dict(family="green", band="small", horizon_w=52,
        filters=("deep70", "ins2", "vix20"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g78_sm_cheap5_ins2": dict(family="green", band="small", horizon_w=78,
        filters=("cheap5", "ins2"), slots=1, budget=1000.0, parked=False),
    # --- batch 3 (LAZ3-1): cyan tierA/wiki lanes + green small tierA/wcov
    "s_q07w_c78_sm_tierA_wcov": dict(family="cyan", band="small", horizon_w=78,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c52_ml_tierA_wcov": dict(family="cyan", band="midlarge", horizon_w=52,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c52_ml_tierA_wlow": dict(family="cyan", band="midlarge", horizon_w=52,
        filters=("tierA", "wlow"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c52_ml_mom6_tierA_wlow": dict(family="cyan", band="midlarge", horizon_w=52,
        filters=("mom6", "tierA", "wlow"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c52_ml_mom6_wspike2": dict(family="cyan", band="midlarge", horizon_w=52,
        filters=("mom6", "wspike2"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_ml_tierA_wcov": dict(family="cyan", band="midlarge", horizon_w=78,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_ml_tierA_wlow": dict(family="cyan", band="midlarge", horizon_w=78,
        filters=("tierA", "wlow"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_ml_mom6_tierA_wlow": dict(family="cyan", band="midlarge", horizon_w=78,
        filters=("mom6", "tierA", "wlow"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_ml_deep70_tierA_wlow": dict(family="cyan", band="midlarge", horizon_w=78,
        filters=("deep70", "tierA", "wlow"), slots=1, budget=1000.0, parked=False),
    "s_q07w_g52_sm_tierA_wcov": dict(family="green", band="small", horizon_w=52,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    # --- batch 2 (LAZ2-1): cyan small cheap5/deep70/tierA + c78 deep70, wcov
    "s_q07w_c52_sm_cheap5_wcov": dict(family="cyan", band="small", horizon_w=52,
        filters=("cheap5", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c52_sm_deep70_wcov": dict(family="cyan", band="small", horizon_w=52,
        filters=("deep70", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c52_sm_tierA_wcov": dict(family="cyan", band="small", horizon_w=52,
        filters=("tierA", "wcov"), slots=1, budget=1000.0, parked=False),
    "s_q07w_c78_sm_deep70_wcov": dict(family="cyan", band="small", horizon_w=78,
        filters=("deep70", "wcov"), slots=1, budget=1000.0, parked=False),
}
INPUTS = ("fires", "bars", "positions")
PRODUCERS = (
    {"name": "sleeve_feed_composer", "outputs": ("fires",), "freshness_sla_s": 604800},
    {"name": "bars", "outputs": ("bars",), "freshness_sla_s": 3600},
    {"name": "broker_readback", "outputs": ("positions",), "freshness_sla_s": 3600},
)
STOP_FRAC = 0.15
WINDOW_SESSIONS = 5

_BANDS = {"sm": "small", "small": "small", "ml": "midlarge",
          "midlarge": "midlarge", "mid_large": "midlarge", "mid/large": "midlarge"}
_FAMS = {"green": "green", "w_green": "green", "g": "green",
         "swing": "swing", "w_swing": "swing", "s": "swing",
         "cyan": "cyan", "w_cyan": "cyan", "c": "cyan"}


def _tags(fire):
    t = dict(fire.get("tags") or {})
    for k, v in fire.items():
        t.setdefault(k, v)
    return t


def _closes(bars_map, sym):
    rows = bars_map.get(sym) or bars_map.get(f"{sym}|1d") or []
    return [float(b["c"]) for b in rows if b.get("c") is not None]


def _last_price(fire, bars_map):
    if fire.get("price"):
        return float(fire["price"])
    cs = _closes(bars_map, fire.get("symbol") or "")
    return cs[-1] if cs else None


def _enh_exec_price(view, sleeve_id):
    """ENH-Q07EXEC-20261024 switch: extra.q07_enh[sid].exec_price,
    default ON; OFF restores the pre-change stale fire-price rule."""
    extra = view.get("extra") or {}
    pextra = ((view.get("params") or {}).get("extra") or {})
    for src in (extra.get("q07_enh"), pextra.get("q07_enh")):
        if isinstance(src, dict) and sleeve_id in src:
            v = src[sleeve_id]
            if isinstance(v, dict):
                return bool(v.get("exec_price", True))
            return bool(v)
    return True


def _enh_fresh_first(view, sleeve_id):
    """ENH-Q07FRESH-20261024 switch: extra.q07_enh[sid].fresh_first,
    default ON; OFF restores producer list order exactly."""
    extra = view.get("extra") or {}
    pextra = ((view.get("params") or {}).get("extra") or {})
    for src in (extra.get("q07_enh"), pextra.get("q07_enh")):
        if isinstance(src, dict) and sleeve_id in src:
            v = src[sleeve_id]
            if isinstance(v, dict):
                return bool(v.get("fresh_first", True))
            return bool(v)
    return True


def passes_filters(spec, fire, bars_map, price_override=None):
    """All named filters must have positive evidence (fail closed)."""
    tags = _tags(fire)
    price = price_override if price_override is not None else _last_price(fire, bars_map)
    for f in spec["filters"]:
        if f == "cheap5":
            if price is None or not price < 5.0:
                return False
        elif f == "deep70":
            if "deep70" in tags:
                if not tags["deep70"]:
                    return False
            elif tags.get("drawdown_from_high") is not None:
                if not float(tags["drawdown_from_high"]) >= 0.30:
                    return False
            elif tags.get("high_52w"):
                if price is None or not price <= 0.70 * float(tags["high_52w"]):
                    return False
            else:
                cs = _closes(bars_map, fire.get("symbol") or "")
                if not cs or price is None or not price <= 0.70 * max(cs):
                    return False
        elif f == "wcov":
            if "wiki_cov" in tags:
                if not tags["wiki_cov"]:
                    return False
            elif tags.get("wiki_views") is not None:
                if not float(tags["wiki_views"]) > 0:
                    return False
            elif tags.get("wiki_coverage") is not None:
                if not tags["wiki_coverage"]:
                    return False
            elif tags.get("wiki_attention") is not None:
                if tags["wiki_attention"] not in ("covered", "high", "spike"):
                    return False
            else:
                return False
        elif f == "wlow":
            if not (tags.get("wiki_low") or tags.get("wiki_attention") == "low"):
                return False
        elif f == "ins2":
            if tags.get("insider_buys") is not None:
                if not int(tags["insider_buys"]) >= 2:
                    return False
            elif not tags.get("ins2"):
                return False
        elif f == "vix20":
            v = tags.get("vix")
            if v is None:
                cs = _closes(bars_map, "VIX") or _closes(bars_map, "^VIX")
                v = cs[-1] if cs else None
            if v is None or not float(v) >= 20.0:
                return False
        elif f == "tierA":
            if tags.get("tier") is not None:
                if str(tags["tier"]).upper() != "A":
                    return False
            elif not tags.get("tier_a"):
                return False
        elif f == "wspike2":
            if tags.get("wiki_spike2") is not None:
                if not tags["wiki_spike2"]:
                    return False
            elif tags.get("wiki_spike") is not None:
                if not float(tags["wiki_spike"]) >= 2.0:
                    return False
            else:
                return False
        elif f == "ats_z1":
            if tags.get("ats_z") is None or not float(tags["ats_z"]) >= 1.0:
                return False
        elif f == "mom6":
            if tags.get("mom6_pct") is not None:
                if not float(tags["mom6_pct"]) > 0:
                    return False
            elif tags.get("mom6") is not None:
                m = tags["mom6"]
                if isinstance(m, bool):
                    if not m:
                        return False
                elif not float(m) > 0:
                    return False
            else:
                cs = _closes(bars_map, fire.get("symbol") or "")
                if len(cs) < 127 or not cs[-1] > cs[-127]:
                    return False
        else:  # unknown filter: fail closed, never guess
            return False
    return True


def _sessions_since(fire, session, bars_map):
    sd = (fire.get("signal_date") or fire.get("fired_at")
          or fire.get("fire_date") or fire.get("date"))
    if not sd:
        return None
    sd = str(sd)[:10]
    qqq = bars_map.get("QQQ") or bars_map.get("QQQ|1d") or []
    dates = sorted(str(b.get("date") or "")[:10] for b in qqq if b.get("date"))
    if dates and dates[0] <= sd <= session:
        n = sum(1 for d in dates if sd < d <= session)
        # bars may include the signal session itself; sessions elapsed
        # since the signal (signal day = 0) must be <= WINDOW_SESSIONS.
        return n
    try:
        delta = (_dt.date.fromisoformat(session) - _dt.date.fromisoformat(sd)).days
    except ValueError:
        return None
    return max(0, round(delta * 5 / 7)) if delta >= 0 else None


def _qqq_down(view, bars_map):
    extra = view.get("extra") or {}
    if isinstance(extra.get("qqq_red"), bool):
        return extra["qqq_red"]
    mkt = view.get("market") or {}
    if isinstance(mkt.get("qqq_red"), bool):
        return mkt["qqq_red"]
    cs = _closes(bars_map, "QQQ")
    return len(cs) >= 2 and cs[-1] < cs[-2]


def evaluate_sleeve(sleeve_id, view, ctx):
    spec = SPECS[sleeve_id]
    view = view or {}
    bars_map = view.get("bars") or {}
    positions = [p for p in (view.get("positions") or []) if p.get("symbol")]
    session = str(ctx.get("session") or "")[:10]
    stamp = str(ctx.get("now") or session).replace("-", "").replace(":", "").replace(" ", "")
    out, seq = [], 0

    def emit(kind, sym, side, qty, reason, stop=None):
        nonlocal seq
        seq += 1
        out.append({"intent_id": f"{sleeve_id}-{stamp}-{seq}", "kind": kind,
                    "symbol": sym, "side": side, "qty": int(qty),
                    "order_type": "market", "limit_price": None,
                    "stop_price": stop, "reason": reason,
                    "time_in_force": "day",
                    "position_intent": "buy_to_open" if kind == "entry" else "sell_to_close"})

    # Exits first (parked lanes still manage exits).
    held = {}
    for p in positions:
        sym = p["symbol"]
        held[sym] = p
        qty = int(float(p.get("qty") or 0))
        entry = float(p.get("avg_price") or 0)
        if qty <= 0 or entry <= 0:
            continue
        cs = _closes(bars_map, sym)
        price = cs[-1] if cs else (float(p["current_price"]) if p.get("current_price") else None)
        if price is not None and price <= entry * (1 - STOP_FRAC):
            emit("exit", sym, "sell", qty,
                 f"q07 exit: stop_15pct {sleeve_id} entry={entry:.2f} last={price:.2f}")
            continue
        opened = str(p.get("opened_at") or p.get("entry_date") or "")[:10]
        if opened and session:
            try:
                held_days = (_dt.date.fromisoformat(session)
                             - _dt.date.fromisoformat(opened)).days
            except ValueError:
                held_days = -1
            if held_days >= spec["horizon_w"] * 7:
                emit("exit", sym, "sell", qty,
                     f"q07 exit: horizon_{spec['horizon_w']}w {sleeve_id} opened={opened}")

    if spec["parked"]:
        return out  # CSV-off lane: entries refused, exits managed above

    # Entries: slots = distinct held symbols (exiting ones still count).
    open_slots = spec["slots"] - len(held)
    if open_slots <= 0 or not _qqq_down(view, bars_map):
        return out
    # ENH-Q07FRESH-20261024: single-slot lanes took whichever passing
    # fire the producer listed FIRST; a 5-session-old fire (edge decayed,
    # window about to expire) crowded out a same-day fire. ON (default):
    # allocate the slot freshest-signal-first (stable; age = sessions
    # since signal). OFF: producer list order exactly (pre-change).
    _fires_in = list(view.get("fires") or [])
    _fresh_on = _enh_fresh_first(view, sleeve_id)
    _cand = []
    for _f in _fires_in:
        if not isinstance(_f, dict) or not _f.get("symbol"):
            continue
        _fid = _f.get("sleeve_id") or _f.get("sleeve")
        if _fid is not None and _fid != sleeve_id:
            continue
        if _FAMS.get(str(_f.get("family") or "").lower()) != spec["family"]:
            continue
        if _BANDS.get(str(_f.get("band") or _f.get("cap_band") or "").lower()) != spec["band"]:
            continue
        if _f["symbol"] in held:
            continue
        _cand.append(_f)
    if len(_cand) >= 2:
        _ages = {id(_f): _sessions_since(_f, session, bars_map) for _f in _cand}
        _ordered = sorted(_cand, key=lambda _f: (
            _ages[id(_f)] is None,
            _ages[id(_f)] if _ages[id(_f)] is not None else 0))
        _jr = (view.get("extra") or {}).get("q07_exp_journal")
        if isinstance(_jr, dict) and isinstance(_jr.get("records"), list):
            _jr["records"].append({
                "exp_id": "ENH-Q07FRESH-20261024", "sleeve": sleeve_id,
                "control_first": _cand[0]["symbol"],
                "treatment_first": _ordered[0]["symbol"],
                "control_age": _ages[id(_cand[0])],
                "treatment_age": _ages[id(_ordered[0])]})
        _fires_iter = _ordered if _fresh_on else _fires_in
    elif _cand:
        _fires_iter = _cand if _fresh_on else _fires_in
    else:
        _fires_iter = _fires_in
    for fire in _fires_iter:
        if open_slots <= 0:
            break
        if not isinstance(fire, dict) or not fire.get("symbol"):
            continue
        fid = fire.get("sleeve_id") or fire.get("sleeve")
        if fid is not None and fid != sleeve_id:
            continue
        if _FAMS.get(str(fire.get("family") or "").lower()) != spec["family"]:
            continue
        if _BANDS.get(str(fire.get("band") or fire.get("cap_band") or "").lower()) != spec["band"]:
            continue
        sym = fire["symbol"]
        if sym in held:
            continue
        age = _sessions_since(fire, session, bars_map)
        if age is None or age > WINDOW_SESSIONS:
            continue
        # ENH-Q07EXEC-20261024: revalidate at the execution (latest bar)
        # price — filters, sizing and stop. The fire price is signal-time
        # (up to 5 sessions stale); a market entry fills at the current
        # price, so the stale price oversizes the slot and misplaces the
        # 15% stop. OFF = pre-change rule exactly (fire price throughout).
        stale_price = _last_price(fire, bars_map)
        _cs = _closes(bars_map, sym)
        current_price = _cs[-1] if _cs else None
        enh_on = _enh_exec_price(view, sleeve_id)
        treat_price = current_price if (enh_on and current_price) else stale_price
        ctrl_pass = passes_filters(spec, fire, bars_map)
        treat_pass = passes_filters(spec, fire, bars_map, price_override=treat_price)
        chosen_pass = treat_pass if enh_on else ctrl_pass
        journal = (view.get("extra") or {}).get("q07_exp_journal")
        if isinstance(journal, dict) and isinstance(journal.get("records"), list):
            journal["records"].append({
                "exp_id": "ENH-Q07EXEC-20261024", "sleeve": sleeve_id,
                "symbol": sym, "control_price": stale_price,
                "treatment_price": treat_price, "control_enter": ctrl_pass,
                "treatment_enter": treat_pass})
        if not chosen_pass:
            continue
        price = treat_price if enh_on else stale_price
        if price is None or price <= 0:
            continue
        qty = int((spec["budget"] / spec["slots"]) // price)
        if qty <= 0:
            continue
        emit("entry", sym, "buy", qty,
             f"q07 entry: {spec['family']} 1w {spec['band']} "
             f"filters={'+'.join(spec['filters'])} horizon={spec['horizon_w']}w "
             f"age_sessions={age} price={price:.2f} sleeve={sleeve_id}",
             stop=round(price * (1 - STOP_FRAC), 4))
        held[sym] = {"symbol": sym}
        open_slots -= 1
    return out


def register(registry):
    for name, outputs, sla in ((p["name"], p["outputs"], p["freshness_sla_s"]) for p in PRODUCERS):
        if name not in registry.producers:
            registry.register_producer(name, outputs, sla)
    for sid in SPECS:
        registry.register_sleeve(sid, INPUTS)
    return registry
