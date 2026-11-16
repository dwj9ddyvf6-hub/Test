"""Aster ETF sleeves — batch 10 (TSV-as-spec; staged archive absent on this box at build time, see FIDELITY-LEDGER ASTER-B10).
Spec source: sleeve-catalog.tsv education_* fields + ASTER-BUILD-MAP.md §6 etf rows.
Common rules (all 10): entry/rebalance only 09:35-09:40 ET; whole shares floor(gross*equity/price);
sells before buys; no price stop/target; cost_bps 15 is source-book accounting, not an order field.
Monthly sleeves act on initial allocation (flat) or when a holding's entry month != session month
(documented reading of 'monthly'); buy-and-hold sleeves held fixed shares with no exit until
BUYHOLD-REBALANCE-EXIT-20261116 (owner ruling 2026-11-16): a held buy-hold position whose
current weight drifts beyond the drift band above its fixed target weight emits a sell-only
rebalance exit of the excess back toward target (see BUYHOLD_DRIFT_BAND below).
LEADER1: rank basket by 126-session log return log(close[-1]/close[-127])
(source r19_etf._scores, HARDEN batch-1 fidelity cure), ties alphabetical.
Eligibility is source-exact: _scores requires the full 252-session history
window — a symbol with <252 bars is ineligible (pre-inception) or the
evaluation is unqualified; it is never ranked on a shorter history.
Inputs must come from v3 producers (bars/positions/quotes) — absent bars => no intents (UNFED upstream)."""
from __future__ import annotations
import json, os
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# --- ENH-ETWIN (Edge pass batch 4, 2026-10-24): binding leak = the
# execution window was read off the raw clock hour. The desk cycle
# stamps view["now"] in UTC (desk3/cycle.py: datetime.now(timezone.utc)),
# so the 09:35-09:40 window fired 05:35-05:40 ET premarket and NEVER
# during RTH — all batch-10/11 ETF sleeves were dead in live cycles
# (fixture tests used naive ET stamps, masking it). Cure: aware stamps
# are converted to America/New_York before the window check (the exact
# reading the archive/b9 engine already uses); naive stamps read as ET.
# Switch: extra["aster_etf_enh"] {"et_window": bool}, default ON; OFF
# restores the pre-change raw-hour rule exactly. Shadow control: the
# legacy raw-hour gate is evaluated on every call (never emits) and a
# paired record is appended to extra["aster_etf_exp_journal"]["records"]
# when served. Exp: ENH-ETWIN-20261024, proof/enhance/<sleeve>.json.
EXP_ID_ETWIN = "ENH-ETWIN-20261024"

# --- WEIGHT-LAG-20261031 (quants-mechanisms steal, mechanism 1)
# + WEIGHT-LAG-ACTIVE-20261031 (owner rulings 2026-10-31 10:39 ET
# and 2026-10-31 11:44 ET): the stolen form shifts target weights
# forward by 1 day at the engine layer to prevent look-ahead bias.
# The owner ruled the one-bar lag ON for the live books, accepting
# that entries and rebalances fire one evaluation later than the
# closed-bar signal that produced the weights. The lag lives at
# this book's consumption point: evaluate() computes target-share
# counts from the last CLOSED bar (producers serve closed bars
# only: core/data.py SIP recency clamp, core/saty_bars.py
# closed-bars-only contract), stores them as the pending targets,
# and diffs the PREVIOUS evaluation's pending targets against the
# current positions to produce intents. The first evaluation after
# activation therefore emits nothing for newly computed weights.
# An evaluation that computes no weights (window/month gates above
# return before this point) does not advance the lag. Pending
# targets are module state (this book's evaluate() has no state_dir
# channel); they are pinned by
# tests/test_weight_lag_20261031_blockers.py. evaluate() still
# appends an observer record to an opt-in extra["weight_lag_journal"]
# when served.
WEIGHT_LAG_POLICY = {
    "mechanism": "weight-lag",
    "lag_bars": 1,
    "applied": True,
    "basis": "closed_bar_gating_only",
    "status": "ACTIVE",
    "reason": ("Shift weights forward by 1 day to prevent look-ahead "
               "bias (the engine-layer form). Applied here as a "
               "one-evaluation lag at the consumption point: targets "
               "computed from the last CLOSED bar at one evaluation "
               "are diffed against positions and acted on at the "
               "next evaluation."),
    "ruling_needed": ("None: owner ruling 2026-10-31 10:39 ET "
                      "authorized the one-bar weight lag on the live "
                      "books and ruling 2026-10-31 11:44 ET authorized "
                      "landing it; entries and rebalances fire one "
                      "evaluation later by design."),
}

# WEIGHT-LAG-ACTIVE-20261031: pending target-share counts per sleeve,
# computed at one evaluation and consumed at the next. Module state:
# this book's evaluate() signature carries no state_dir.
_PENDING_TARGETS = {}

# CR-1 (2026-11-11): the lag's pending targets now also persist to
# the sleeve's state directory (ctx["state_dir"], which the live
# cycle has always passed) as weight_lag_pending.json. The in-memory
# semantics are unchanged; the disk copy only survives a runner
# restart, which previously restarted the lag from zero and, with
# the single 09:35 evaluation window, silently ate flat sleeves'
# initial allocations for sessions at a time (DIAGNOSIS.md S1).
# Without a state_dir (fixture drives) behaviour is exactly the
# pre-cure in-memory behaviour.


def _pending_path(state_dir):
    return (os.path.join(state_dir, "weight_lag_pending.json")
            if state_dir else None)


def _load_pending(state_dir, sleeve_id):
    path = _pending_path(state_dir)
    if not path:
        return None
    try:
        with open(path) as fh:
            doc = json.load(fh)
        targets = doc["targets"]
        if doc.get("sleeve") != sleeve_id or \
                not isinstance(targets, dict):
            return None
        return {str(k): int(v) for k, v in targets.items()}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _save_pending(state_dir, sleeve_id, targets, sess):
    path = _pending_path(state_dir)
    if not path:
        return
    try:
        os.makedirs(state_dir, exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"sleeve": sleeve_id, "session": sess,
                       "targets": dict(targets)}, fh)
    except OSError:
        pass


# --- REBALANCE-POLICY-20261031 (quants-mechanisms steal, mechanism
# 6) + REBALANCE-ENFORCE-20261031 (owner ruling 2026-10-31):
# rebalance policy as a first-class object, ENFORCED for exactly
# the dimensions this book declares concrete values for. This
# book's SPECS state frequency per sleeve (MONTHLY / BUY_HOLD, in
# SPECS below and in each config/sleeves.json row's
# rebalance_policy block) and evaluate() enforces it in-path:
# BUY_HOLD sleeves with positions return no intents except the
# drift-band rebalance exit of BUYHOLD-REBALANCE-EXIT-20261116
# (owner ruling 2026-11-16, declared in the nested
# "buyhold_rebalance_exit" block of REBALANCE_POLICY below;
# the book-level drift_threshold stays None because the band is
# scoped to the BUY_HOLD subset only — the MONTHLY sleeves in
# this book carry no band), MONTHLY
# sleeves whose holdings entered in the current month return no
# intents (so an intra-month signal change cannot rebalance the
# book: signal_change_rebalance False, enforced by the same
# gates), and trading is delta-only (buy target-held, sell
# held-target), the declared partial_rebalance. There is no
# drift band, no tracking-error trigger and no turnover budget
# declared on this book (explicit Nones), so those dimensions
# stay declared_not_enforced and are named in ruling_needed; no
# value was invented for them. The dispatcher never reads this
# object; it is pinned by
# tests/test_rebalance_policy_20261031_blockers.py. The contract
# object is desk3.contract.RebalancePolicy (frequency "per_spec"
# here because SPECS carries two frequencies).
REBALANCE_POLICY = {
    "mechanism": "rebalance-policy",
    "frequency": "per_spec",
    "drift_threshold": None,
    "drift_type": None,
    "partial_rebalance": True,
    "tracking_error_threshold": None,
    "tracking_error_window_days": None,
    "max_annual_turnover": None,
    "signal_change_rebalance": False,
    "execution_timing": "on_evaluation",
    "enforcement": "enforced_for_declared_dimensions",
    "status": "ACTIVE_DECLARED_DIMENSIONS_ONLY",
    "enforced_dimensions": ["frequency", "partial_rebalance",
                            "signal_change_rebalance"],
    "declared_only_dimensions": ["drift_threshold",
                                 "tracking_error_threshold",
                                 "max_annual_turnover"],
    "ruling_needed": ("A declared value for a drift band, a "
                      "tracking-error trigger, or a turnover "
                      "budget on the live books: none is declared "
                      "today (all explicit Nones), so those "
                      "dimensions cannot be enforced until a "
                      "value is declared by ruling."),
    # BUYHOLD-REBALANCE-EXIT-20261116 (owner ruling 2026-11-16,
    # "Make it work"): the drift band for the BUY_HOLD subset
    # only, declared and enforced in evaluate() below. The value
    # is ADOPTED, not invented: the estate's sole genuine
    # weight-deviation tolerance is the ENH-B5 no-trade deadband
    # in desk3/aster_batch1.py (comment at lines 1010-1015:
    # "drift adjustments within 0.5% of book value are refused";
    # code at lines 1137-1146: abs(drift) <= 0.005 * book). The
    # other leads carry no band: aster_batch8/b9 DRIFT1 is
    # incumbent-share retention, and this book's drift_threshold
    # above is an explicit None. Book-level drift_threshold
    # therefore stays None (no book-wide band exists); this
    # nested block is the per-spec (BUY_HOLD-only) declaration.
    "buyhold_rebalance_exit": {
        "drift_threshold": 0.005,
        "drift_type": "absolute",
        "scope": "BUY_HOLD sleeves only (the six aster buy-hold "
                 "ETF sleeves); MONTHLY sleeves unchanged",
        "source": "desk3/aster_batch1.py ENH-B5 deadband: 0.5% "
                  "of book value (comment lines 1010-1015, code "
                  "lines 1137-1146, constant 0.005)",
        "enforcement": "enforced_in_evaluate_sell_only",
        "status": "ACTIVE",
    },
}

# BUYHOLD-REBALANCE-EXIT-20261116: drift band for the six
# BUY_HOLD ETF sleeves (aster_etf_qld_buy_hold,
# aster_etf_qqq_buy_hold, aster_etf_qqq_qld_buy_hold,
# aster_etf_smh_hold_c098, aster_etf_smh_hold_m150 in SPECS
# below, aster_etf_spy_buy_hold registered by
# desk3/aster_batch11 — the only BUY_HOLD specs this engine
# serves). ADOPTED from the estate's existing deadband
# convention, desk3/aster_batch1.py lines 1010-1015 + 1137-1146
# (0.5% of book value, constant 0.005), read here in the
# contract's terms (desk3/contract.py REBALANCE_DRIFT_TYPES) as
# an "absolute" band: a held position's current weight —
# held value over the sleeve's sizing equity, the same base
# evaluate() sizes targets from — minus its target weight
# (gross * fixed weight). Beyond the band, the excess over the
# fixed target share count is sold back toward target.
BUYHOLD_DRIFT_BAND = 0.005
BUYHOLD_DRIFT_BAND_TYPE = "absolute"


def _weight_lag_paired(extra, record):
    j = (extra or {}).get("weight_lag_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)


def _etwin_enabled(extra):
    ov = (extra or {}).get("aster_etf_enh")
    if isinstance(ov, dict) and "et_window" in ov:
        return bool(ov["et_window"])
    return True


def _etwin_paired(extra, record):
    j = (extra or {}).get("aster_etf_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)

# --- ENH-B5-CATCHUP (Edge pass batch 5, 2026-10-24) — SECOND look at
# the monthly sleeves (first look: ENH-ETWIN above). Binding leak: the
# rebalance window is 5 minutes wide and the sleeve cadence is 300s,
# so exactly ONE evaluation per month can ever fire; a wedged, late,
# or unfed 09:35 cycle loses the entire month's rebalance (the desk's
# own history is 21 watchdog kills in a day). Treatment: a MONTHLY
# sleeve whose rebalance is due may still execute the SAME targets
# later the same session (09:40-15:55 ET) — the monthly horizon makes
# the intraday delay immaterial vs a month of wrong exposure.
# Switch: extra["aster_etf_enh"] {"catchup": bool}, default ON; OFF
# restores the window-only rule exactly. Shadow control: the legacy
# window gate is evaluated on every call (never emits) and paired
# records are appended when the catch-up path serves.
EXP_ID_CATCHUP = "ENH-B5-ETF-CATCHUP-20261024"


def _catchup_enabled(extra):
    ov = (extra or {}).get("aster_etf_enh")
    if isinstance(ov, dict) and "catchup" in ov:
        return bool(ov["catchup"])
    return True


def _in_catchup(now, legacy=False):
    if now is None: return False
    if not legacy and now.tzinfo is not None:
        now = now.astimezone(ET)
    mins = now.hour * 60 + now.minute
    return 9 * 60 + 40 <= mins < 15 * 60 + 55

BASKET=["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]
SPECS={
 "aster_etf_leader1_m150": dict(policy="LEADER1", freq="MONTHLY", gross=1.5, weights=None),
 "aster_etf_qld_buy_hold": dict(policy="QLD_ONLY_BUY_HOLD", freq="BUY_HOLD", gross=1.0, weights={"QLD":1.0}),
 "aster_etf_qld_monthly": dict(policy="QLD_ONLY_MONTHLY", freq="MONTHLY", gross=1.0, weights={"QLD":1.0}),
 "aster_etf_qqq_buy_hold": dict(policy="QQQ_HOLD_FULL", freq="BUY_HOLD", gross=1.0, weights={"QQQ":1.0}),
 "aster_etf_qqq_monthly_c098": dict(policy="QQQ_MONTHLY", freq="MONTHLY", gross=0.98, weights={"QQQ":1.0}),
 "aster_etf_qqq_monthly_m150": dict(policy="QQQ_MONTHLY", freq="MONTHLY", gross=1.5, weights={"QQQ":1.0}),
 "aster_etf_qqq_qld_buy_hold": dict(policy="QQQ_QLD_50_50_BUY_HOLD", freq="BUY_HOLD", gross=1.0, weights={"QQQ":0.5,"QLD":0.5}),
 "aster_etf_qqq_qld_monthly": dict(policy="QQQ_QLD_50_50_MONTHLY", freq="MONTHLY", gross=1.0, weights={"QQQ":0.5,"QLD":0.5}),
 "aster_etf_qld_monthly_inv": dict(policy="QLD_ONLY_MONTHLY", freq="MONTHLY", gross=1.0, weights={"QLD":1.0}, direction=-1),
 "aster_etf_qqq_qld_monthly_inv": dict(policy="QQQ_QLD_50_50_MONTHLY", freq="MONTHLY", gross=1.0, weights={"QQQ":0.5,"QLD":0.5}, direction=-1),
 "aster_etf_smh_hold_c098": dict(policy="SMH_HOLD", freq="BUY_HOLD", gross=0.98, weights={"SMH":1.0}),
 "aster_etf_smh_hold_m150": dict(policy="SMH_HOLD", freq="BUY_HOLD", gross=1.5, weights={"SMH":1.0}),
}
# --- CONV21-INVERT-20261116 (Conversion Register CONV-21, QLD monthly
# inversion): the inverted evaluator the going-live pass named as the
# missing construction. The two _inv SPECS above carry direction=-1:
# their targets are the base sleeves' targets negated, expressed at
# the door as sell_to_open entries and buy_to_close covers (the
# dispatcher's buy-to-cover form; desk3.contract POSITION_INTENTS).
# Equity sell_to_open is expressible on this desk (the contract admits
# it, the dispatcher treats it as an entry facing the slice
# buying-power gate at price x qty, and live equity sleeves already
# short single names, e.g. bta_onebar_qqq on QQQ). Base SPECS carry no
# direction key and evaluate exactly as before this cure.
# Borrow is priced in-path: every sell_to_open intent the inverted
# evaluator emits carries a borrow record at the DH2 snapshot fee
# (DH2-BORROW-SERIES.jsonl, IB snapshot 2026-11-15: QLD 0.7690 percent
# per year, QQQ 0.26 percent per year), accrued per day on the
# intent's own notional; the daily IB snapshot archive accruing from
# 2026-11-16 supersedes the snapshot for grading, per the register.
CONV21_BORROW_FEE_PCT_PER_YEAR = {"QLD": 0.7690, "QQQ": 0.26}
CONV21_BORROW_SOURCE = "DH2-BORROW-SERIES-2026-11-15"
# The register row's falsifier and kill rule, byte-identical to
# CONVERSION-REGISTER-2026-11-15.md CONV-21; the both-sides
# FWD_GRADE arm in config/conversion_shadow_20261115.json carries
# the same texts and grades the base sleeves' forward fires.
CONV21_FALSIFIER = "The inversion dies if forward fwd5 excess of the long (base) side is not negative over the next 10 forward fires; symmetrically, the inverted form promotes only if its own forward fwd5 excess is positive over the same fires."
CONV21_KILL_RULE = "Base-side forward fwd5 excess not negative over those fires kills the inversion."
INPUTS=("bars","positions","quotes")
PRODUCERS=({"name":"bars","outputs":("bars",),"freshness_sla_s":900},
 {"name":"broker_readback","outputs":("positions",),"freshness_sla_s":900},
 {"name":"quotes","outputs":("quotes",),"freshness_sla_s":60})

def _bars(view,sym):
    m=view.get("bars") or {}
    for k in (f"{sym}|1Day",f"{sym}|1D",sym):
        if m.get(k): return m[k]
    return []
def _close(bars): return float(bars[-1]["c"]) if bars else 0.0
def _now(view,ctx):
    n=view.get("now") or (ctx or {}).get("now") or (ctx or {}).get("session") or ""
    if isinstance(n,datetime): return n
    try: return datetime.fromisoformat(str(n).replace("Z","+00:00"))
    except Exception: return None
def _in_window(now, legacy=False):
    if now is None: return False
    if not legacy and now.tzinfo is not None:
        now = now.astimezone(ET)
    mins=now.hour*60+now.minute
    return 9*60+35 <= mins < 9*60+40

def evaluate(sleeve_id, view, ctx=None):
    view=view or {}; ctx=ctx or {}
    spec=SPECS[sleeve_id]; now=_now(view,ctx)
    _extra0={}; _extra0.update(ctx.get("extra") or {} if isinstance(ctx,dict) else {}); _extra0.update(view.get("extra") or {})
    _enh=_etwin_enabled(_extra0)
    _control_in=_in_window(now, legacy=True)  # shadow: pre-change gate, never emits
    # CR-1 (2026-11-11): the same-session catch-up treatment extends
    # to flat BUY_HOLD initial allocations — a flat buy-hold sleeve's
    # first in-window evaluation only stores its lagged targets, so
    # without catch-up its allocation could never emit the same
    # session even with the persistence cure above.
    _flat_top=not any(float(p.get("qty") or 0)!=0
                      for p in (view.get("positions") or []))
    _catch=((spec["freq"]=="MONTHLY"
             or (spec["freq"]=="BUY_HOLD" and _flat_top))
            and _catchup_enabled(_extra0)
            and not _in_window(now, legacy=not _enh)
            and _in_catchup(now, legacy=not _enh))
    if not _in_window(now, legacy=not _enh) and not _catch: return []
    _etwin_paired(_extra0, {"exp_id": EXP_ID_ETWIN, "sleeve": sleeve_id,
        "treatment": "et_window" if _enh else "legacy_raw_hour",
        "treatment_window_open": True, "control_window_open": _control_in})
    sess=now.date().isoformat(); stamp=now.strftime("%Y%m%dT%H%M%S")
    extra={}; extra.update(ctx.get("extra") or {} if isinstance(ctx,dict) else {}); extra.update(view.get("extra") or {})
    sl=(ctx.get("slice") or {}) if isinstance(ctx,dict) else {}
    equity=float(extra.get("account_value") or extra.get("net_value") or sl.get("capital_usd") or 10000.0)
    positions={p["symbol"]:p for p in (view.get("positions") or []) if float(p.get("qty") or 0)!=0}
    # BUY_HOLD (BUYHOLD-REBALANCE-EXIT-20261116, owner ruling
    # 2026-11-16): once allocated, the sleeve's only exit is the
    # drift-band rebalance below — a held sleeve falls through to
    # the fixed-target computation (bypassing the weight lag, see
    # the lag block below) and in the intent section is SELL-ONLY:
    # no buys (entries stay exactly the flat-allocation path), no
    # sale of non-target symbols, and a sale only where the held
    # weight has drifted beyond BUYHOLD_DRIFT_BAND above target.
    _buyhold_held=(spec["freq"]=="BUY_HOLD" and bool(positions))
    # MONTHLY: only on initial allocation or a new month vs holdings' entry month
    if spec["freq"]=="MONTHLY" and positions and not extra.get("rebalance_due"):
        months={str(p.get("entry_date") or p.get("opened_at") or "")[:7] for p in positions.values()}
        if months=={sess[:7]}: return []
    # targets
    if spec["policy"]=="LEADER1":
        import math
        scored=[]
        for sym in BASKET:
            b=_bars(view,sym)
            if len(b)>=252:  # source _scores 252-session eligibility window
                scored.append((-math.log(_close(b)/float(b[-127]["c"])), sym))
        if not scored: return []
        scored.sort()  # highest return first; ties alphabetical (sym asc within equal score via tuple on -ret? use stable)
        # sort by return desc, ticker asc:
        scored=sorted(scored, key=lambda x:(x[0], x[1]))
        leader=scored[0][1]; weights={leader:1.0}
    else:
        weights=spec["weights"]
    targets={}
    for sym,w in weights.items():
        b=_bars(view,sym); px=_close(b)
        if px<=0: return []  # missing price for a target leg: refuse whole rebalance
        targets[sym]=int(spec["gross"]*equity*w//px)
    if spec.get("direction", 1) < 0:
        # CONV21-INVERT-20261116: negative targets — the inverted
        # form holds the mirror (short) position of the base sleeve.
        targets={sym: -qty for sym, qty in targets.items()}
    # WEIGHT-LAG-ACTIVE-20261031: act on the PREVIOUS evaluation's
    # pending targets; this evaluation's targets become pending.
    # Reaching this point means weights were computed, so the lag
    # advances exactly here and nowhere earlier. No pending state
    # (first evaluation after activation) emits nothing at all:
    # there is no previous computation to act on.
    _sd=(ctx.get("state_dir") if isinstance(ctx,dict) else None)
    if _buyhold_held:
        # BUYHOLD-REBALANCE-EXIT-20261116: the held buy-hold
        # rebalance does NOT consume or advance the weight lag.
        # The lag guards signal-derived target weights against
        # look-ahead; a buy-hold sleeve's target weights are
        # fixed constants in SPECS and the band is measured on
        # the current closed-bar price (producers serve closed
        # bars only, per the WEIGHT-LAG header), so there is no
        # computed signal to lag. The pre-cure held path also
        # never touched the pending state, and that invariant is
        # pinned (a held evaluation must not prime a later flat
        # entry: tests/test_aster_batch11_blockers.py refusals).
        pass
    elif sleeve_id not in _PENDING_TARGETS:
        # CR-1: after a runner restart the in-memory pending set is
        # empty but the persisted one survives — act on it exactly as
        # if the process had never died.
        _persisted=_load_pending(_sd, sleeve_id)
        if _persisted is not None:
            _PENDING_TARGETS[sleeve_id]=_persisted
        else:
            _PENDING_TARGETS[sleeve_id]=dict(targets)
            _save_pending(_sd, sleeve_id, targets, sess)
            _weight_lag_paired(_extra0, {"mechanism": "weight-lag",
                "sleeve": sleeve_id, "lag_bars": WEIGHT_LAG_POLICY["lag_bars"],
                "basis": WEIGHT_LAG_POLICY["basis"],
                "status": WEIGHT_LAG_POLICY["status"], "intents": 0})
            return []
    if not _buyhold_held:
        _lagged_targets=_PENDING_TARGETS[sleeve_id]
        _PENDING_TARGETS[sleeve_id]=dict(targets)
    if not _buyhold_held:
        _save_pending(_sd, sleeve_id, targets, sess)
        targets=_lagged_targets
    out=[]; n=0
    def intent(kind,sym,side,qty,reason,price,position_intent=None):
        nonlocal n; n+=1
        return {"intent_id":f"{sleeve_id}-{stamp}-{n}","kind":kind,"symbol":sym,"side":side,"qty":int(qty),"order_type":"market","limit_price":None,"stop_price":None,"reason":reason,"time_in_force":"day","position_intent":position_intent or ("buy_to_open" if kind=="entry" else "sell_to_close"),"price_hint":float(price)}
    if spec.get("direction", 1) < 0:
        # CONV21-INVERT-20261116: sign-aware diff for the inverted
        # form. Sells before buys, as the base path. A sell first
        # closes any long held (sell_to_close), then opens or adds
        # the short (sell_to_open, borrow priced in-path on the
        # intent). A buy first covers the short (buy_to_close, the
        # buy-to-cover form), then opens any long remainder
        # (buy_to_open). Kinds are the door's vocabulary only
        # (entry/exit, desk3/models.py bad_kind): every close or
        # cover intent is kind exit, full or partial, with the
        # partial case named rebalance in its reason prose. (The
        # base path's kind="rebalance" emission was cured the
        # same day by REBALANCE-KIND-20261116.)
        _sells=[]; _buys=[]
        for sym in sorted(set(positions) | set(targets)):
            held=int(float(positions.get(sym,{}).get("qty") or 0)); tgt=targets.get(sym,0)
            delta=tgt-held
            if delta==0: continue
            px=_close(_bars(view,sym)) or float(positions.get(sym,{}).get("avg_price") or 0)
            if delta<0:
                q=-delta; close_q=min(max(held,0),q)
                if close_q:
                    _word="exit" if close_q==held else "rebalance"
                    _sells.append(intent("exit",sym,"sell",close_q,f"{sleeve_id} {_word}: monthly target {tgt} vs held {held} policy={spec['policy']} inverted",px,position_intent="sell_to_close"))
                open_q=q-close_q
                if open_q:
                    _o=intent("entry",sym,"sell",open_q,f"{sleeve_id} entry: monthly target {tgt} gross={spec['gross']} policy={spec['policy']} inverted sell_to_open",px,position_intent="sell_to_open")
                    _fee=CONV21_BORROW_FEE_PCT_PER_YEAR.get(sym)
                    if _fee is not None:
                        _o["borrow"]={"fee_rate_pct_per_year":_fee,"borrow_cost_per_day_usd":round(open_q*px*_fee/100.0/365.0,4),"source":CONV21_BORROW_SOURCE}
                    _sells.append(_o)
            else:
                q=delta; cover_q=min(max(-held,0),q)
                if cover_q:
                    _word="exit" if cover_q==-held else "rebalance"
                    _buys.append(intent("exit",sym,"buy",cover_q,f"{sleeve_id} {_word}: monthly target {tgt} vs held {held} policy={spec['policy']} inverted buy_to_cover",px,position_intent="buy_to_close"))
                open_q=q-cover_q
                if open_q:
                    _buys.append(intent("entry",sym,"buy",open_q,f"{sleeve_id} entry: monthly target {tgt} gross={spec['gross']} policy={spec['policy']} inverted",px,position_intent="buy_to_open"))
        out=_sells+_buys
    # sells first: non-target symbols fully; over-target reduced
    for sym in sorted(positions) if spec.get("direction", 1) >= 0 else []:
        held=int(float(positions[sym]["qty"])); tgt=targets.get(sym,0)
        if _buyhold_held:
            # BUYHOLD-REBALANCE-EXIT-20261116: sell-only drift-band
            # rebalance. Only fixed-target symbols are this sleeve's
            # to trim (a foreign symbol in the served book is not a
            # buy-hold holding); only whole-share excess over the
            # fixed target is sold, and only when the held weight
            # (held value / sizing equity) exceeds the target
            # weight (gross * fixed weight) by more than the band.
            if sym not in (spec["weights"] or {}): continue
            if held<=tgt: continue
            px=_close(_bars(view,sym)) or float(positions[sym].get("avg_price") or 0)
            if px<=0: continue  # drift unmeasured: refuse the trim
            drift=(held*px-spec["gross"]*equity*spec["weights"][sym])/equity
            if drift<=BUYHOLD_DRIFT_BAND: continue
            out.append(intent("exit",sym,"sell",held-tgt,f"{sleeve_id} exit: buyhold drift-band rebalance drift={drift:.4f} band={BUYHOLD_DRIFT_BAND} target {tgt} vs held {held} policy={spec['policy']}",px))
            continue
        if held>tgt:
            px=_close(_bars(view,sym)) or float(positions[sym].get("avg_price") or 0)
            # REBALANCE-KIND-20261116: a partial reduction is a
            # partial exit in the door's vocabulary (entry/exit
            # only; desk3/models.py raises bad_kind otherwise).
            # kind="rebalance" was rejected at the door (5 live
            # rejects, 2026-11-13) and the decided reduction
            # silently never executed. The kind is exit; the
            # partial case stays named rebalance in the reason
            # prose, as the CONV-21 inverted branch above does.
            kind="exit"
            _word="exit" if tgt==0 else "rebalance"
            out.append(intent(kind,sym,"sell",held-tgt,f"{sleeve_id} {_word}: monthly target {tgt} vs held {held} policy={spec['policy']}",px))
    if _buyhold_held:
        # A held buy-hold sleeve never buys: under-target legs are
        # held untouched and entries remain the flat path only.
        targets={}
    for sym in sorted(targets) if spec.get("direction", 1) >= 0 else []:
        held=int(float(positions.get(sym,{}).get("qty") or 0)); tgt=targets[sym]
        if tgt>held:
            out.append(intent("entry",sym,"buy",tgt-held,f"{sleeve_id} entry: monthly target {tgt} gross={spec['gross']} policy={spec['policy']}",_close(_bars(view,sym))))
    if _catch and out:
        rec={"exp_id": EXP_ID_CATCHUP, "sleeve": sleeve_id,
             "treatment": "same_session_catchup", "control_intents": 0,
             "treatment_intents": len(out), "control_window_open": False}
        _etwin_paired(_extra0, rec)
        for o in out:
            o["reason"] += f" enh:{EXP_ID_CATCHUP} catchup_after_missed_window"
            o["enhance_exp"] = rec
    # WEIGHT-LAG-20261031 observer: journal-only, never alters intents.
    _weight_lag_paired(_extra0, {"mechanism": "weight-lag",
        "sleeve": sleeve_id, "lag_bars": WEIGHT_LAG_POLICY["lag_bars"],
        "basis": WEIGHT_LAG_POLICY["basis"],
        "status": WEIGHT_LAG_POLICY["status"], "intents": len(out)})
    return out
