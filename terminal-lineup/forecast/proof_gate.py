"""Aperture per name historical proof gate, hardened (DEEP-PASS
3.2 item 2, source analysis at Section 2.8).

The mechanism, adopted from Ausar's Aperture scanner: a name
earns a proof state from its own episode history. Episodes are
the engine's own entry conditions found in the name's daily
history, taken non overlapping, scored on their forward return
net of a friction allowance, and split chronologically into a
train and a holdout part. The raw states are SUPPORTED, MIXED
and OBSERVING under the thresholds frozen in the registry.

Three hardenings over the source, which are the whole point of
this module:

1. PROVISIONAL state language. Every state this gate prints is
   provisional: it is manufactured from the name's own in sample
   history at scan time, not accrued forward. The result dict
   carries provisional True and a display string of the form
   "PROVISIONAL SUPPORTED"; no surface may print the bare state
   as if it were a proven record.

2. Benjamini-Hochberg correction across the scanned universe.
   Scanning a universe with a per name episode minimum
   guarantees some names pass by chance. Before any name may
   print SUPPORTED, its one sided binomial p-value (episode hit
   rate against 0.5) is BH adjusted across every name in the
   scan (the grading module's benjamini_hochberg, the one
   correction implementation in this package), and only a name
   whose q-value clears the frozen alpha keeps SUPPORTED. A
   name that passes the raw thresholds but not BH is downgraded
   to MIXED with the reason recorded.

3. A forward ledger record. record_forward_records appends one
   forecast row per scanned name under the ledger engine named
   in the frozen rule, carrying the provisional state, so the
   state is later checked against what the name actually did:
   grade_forward_record grades that row from the realised
   forward return once the horizon has actually traded. The in
   sample proof thereby becomes the first chapter of a real
   record instead of a permanent claim.

The episode rule is NOT a parameter of a scan. It is frozen per
engine in forecast/registry.json (proof_gate_rule on Engines 19
and 20, validated by registry.py); callers load it from the
registry and pass it in. Changing the rule means changing the
registry, in the open.

Entry condition as frozen (aperture_episode_rule_v1): Wilder
RSI(14) curling up and at most 58, MACD (12, 26, 9) histogram
curling up, and the close within 2 percent of EMA(20). An
episode scores its 10 session forward return minus a flat
35 bp friction allowance; a hit is a net return above zero.
Episodes are non overlapping and at least 10 sessions apart.

This module is pure apart from the two ledger helpers: absent
history stays absent (a name with too little history is
OBSERVING with its episode count printed, never filled in).
"""
import math
import statistics

from grading import benjamini_hochberg

PROOF_STATES = ("SUPPORTED", "MIXED", "OBSERVING")
FORWARD_QUANTITY = "provisional_proof_state_forward_return_10s"


# ---- indicators ---------------------------------------------------

def ema_series(values, period):
    """EMA seeded at the first value, recursive thereafter.
    Deterministic and stated here because the source terminal
    carries more than one EMA convention; this gate uses only
    this one."""
    if not values:
        return []
    k = 2.0 / (period + 1.0)
    out = [float(values[0])]
    for v in values[1:]:
        out.append(out[-1] + k * (float(v) - out[-1]))
    return out


def rsi_wilder(closes, period=14):
    """Wilder smoothed RSI. Entries before the first full period
    are None."""
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    gains, losses = [], []
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    def _rsi(ag, al):
        if al == 0:
            return 100.0 if ag > 0 else 50.0
        return 100.0 - 100.0 / (1.0 + ag / al)

    out[period] = _rsi(avg_gain, avg_loss)
    for i in range(period + 1, n):
        d = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(d, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-d, 0.0)) / period
        out[i] = _rsi(avg_gain, avg_loss)
    return out


def macd_histogram(closes, fast=12, slow=26, signal=9):
    """MACD histogram: (EMA fast minus EMA slow) minus its own
    EMA signal line, all under ema_series above."""
    if not closes:
        return []
    ef = ema_series(closes, fast)
    es = ema_series(closes, slow)
    macd = [a - b for a, b in zip(ef, es)]
    sig = ema_series(macd, signal)
    return [m - s for m, s in zip(macd, sig)]


# ---- episodes -------------------------------------------------------

def find_episodes(closes, rule):
    """Episode start indices under the frozen entry condition,
    non overlapping and at least the frozen separation apart.
    An episode is only taken when its full forward window
    exists in the history supplied: a partial forward window
    is not an episode, never a shortened score."""
    entry = rule["entry_condition"]
    horizon = int(rule["episode"]["forward_sessions"])
    separation = int(rule["episode"]["min_separation_sessions"])
    rsi = rsi_wilder(closes, int(entry["rsi_period"]))
    hist = macd_histogram(closes)
    ema = ema_series(closes, int(entry["ema_period"]))
    near = float(entry["near_ema_pct"])
    rsi_max = float(entry["rsi_max"])
    starts = []
    i = 1
    while i + horizon < len(closes):
        if starts and i < starts[-1] + separation:
            i += 1
            continue
        if rsi[i] is None or rsi[i - 1] is None:
            i += 1
            continue
        if rsi[i] <= rsi[i - 1] or rsi[i] > rsi_max:
            i += 1
            continue
        if hist[i] <= hist[i - 1]:
            i += 1
            continue
        if ema[i] == 0 or abs(closes[i] - ema[i]) > near * abs(ema[i]):
            i += 1
            continue
        starts.append(i)
        i += separation
    return starts


def episode_returns(closes, starts, rule):
    """Net forward return per episode: the frozen horizon's
    return minus the frozen friction allowance."""
    horizon = int(rule["episode"]["forward_sessions"])
    friction = float(rule["episode"]["friction"])
    return [closes[s + horizon] / closes[s] - 1.0 - friction
            for s in starts]


def _split(rets, train_fraction):
    """Chronological split: the first train_fraction of the
    episodes are train, the rest holdout. With at least one
    episode the holdout keeps at least one when n is 2 or more;
    a single episode is train only and can never support."""
    n = len(rets)
    if n == 0:
        return [], []
    if n == 1:
        return list(rets), []
    n_train = int(round(n * float(train_fraction)))
    n_train = min(max(n_train, 1), n - 1)
    return list(rets[:n_train]), list(rets[n_train:])


def _stats(rets):
    if not rets:
        return {"episodes": 0, "hit_rate": None, "median": None,
                "hits": 0}
    hits = sum(1 for r in rets if r > 0)
    return {"episodes": len(rets), "hit_rate": hits / len(rets),
            "median": statistics.median(rets), "hits": hits}


def binomial_one_sided_p(hits, n):
    """P(X at least hits) for X Binomial(n, 0.5): the chance a
    coin would produce a hit record this good, which is the
    null the BH correction across the universe tests."""
    if n <= 0:
        return 1.0
    return min(1.0, sum(math.comb(n, k) for k in range(hits, n + 1))
               * 0.5 ** n)


def raw_proof_state(train, holdout, thresholds):
    """The source thresholds, unchanged: SUPPORTED needs the
    full episode count and both splits over their bars; MIXED
    needs the mixed episode floor; otherwise OBSERVING."""
    total = train["episodes"] + holdout["episodes"]
    if total >= int(thresholds["supported_min_episodes"]) \
            and train["hit_rate"] is not None \
            and train["hit_rate"] >= float(thresholds["train_hit_rate_min"]) \
            and train["median"] is not None \
            and train["median"] >= float(thresholds["train_median_min"]) \
            and holdout["hit_rate"] is not None \
            and holdout["hit_rate"] >= float(thresholds["holdout_hit_rate_min"]) \
            and holdout["median"] is not None \
            and holdout["median"] >= float(thresholds["holdout_median_min"]):
        return "SUPPORTED"
    if total >= int(thresholds["mixed_min_episodes"]):
        return "MIXED"
    return "OBSERVING"


def compute_name_proof(symbol, closes, rule):
    """One name's provisional proof, before universe correction.
    closes is a plain close series in session order."""
    closes = [float(c) for c in closes]
    starts = find_episodes(closes, rule)
    rets = episode_returns(closes, starts, rule)
    train_rets, holdout_rets = _split(
        rets, rule["split"]["train_fraction"])
    train, holdout = _stats(train_rets), _stats(holdout_rets)
    all_stats = _stats(rets)
    state = raw_proof_state(train, holdout, rule["thresholds"])
    return {
        "symbol": symbol, "rule_id": rule["id"],
        "provisional": True, "proof_state": state,
        "display_state": f"PROVISIONAL {state}",
        "episodes": all_stats["episodes"], "hits": all_stats["hits"],
        "episode_starts": starts,
        "train": train, "holdout": holdout,
        "p_value": binomial_one_sided_p(all_stats["hits"],
                                        all_stats["episodes"]),
        "bh_q_value": None, "bh_significant": False,
        "bh_applied": False, "downgrade_reason": None,
    }


def compute_proof_universe(closes_by_symbol, rule):
    """A full scan: per name proof, then BH correction across
    the scanned universe before any name may print SUPPORTED.
    Returns {symbol: result} with q-values stamped and the
    downgrade applied."""
    results = {sym: compute_name_proof(sym, closes, rule)
               for sym, closes in sorted(closes_by_symbol.items())}
    alpha = float(rule["multiple_testing"]["alpha"])
    # The correction family is the whole scanned universe, as
    # the frozen rule states: a name with no episodes carries
    # p 1.0 and still counts in the family size, so adding
    # names to a scan can only make SUPPORTED harder to print.
    tested = list(results.values())
    qs = benjamini_hochberg([r["p_value"] for r in tested])
    for result, q in zip(tested, qs):
        result["bh_q_value"] = q
        result["bh_applied"] = True
        result["bh_significant"] = bool(q <= alpha)
        if result["proof_state"] == "SUPPORTED" and q > alpha:
            result["proof_state"] = "MIXED"
            result["display_state"] = "PROVISIONAL MIXED"
            result["downgrade_reason"] = (
                "raw thresholds passed but the BH adjusted q-value "
                f"{q:.4f} exceeds the frozen alpha {alpha} across "
                "the scanned universe; SUPPORTED is refused until "
                "the name's own record clears the correction")
    return results


def display_state(result):
    """The only string a surface may print for a proof result:
    the state with its provisional marker, never bare."""
    return result["display_state"]


# ---- the forward record ----------------------------------------------

def forward_return(closes, start_idx, rule):
    """The realised net forward return from a bar index, or
    None when the frozen horizon has not fully traded yet:
    an unmatured check stays ungraded, never estimated."""
    horizon = int(rule["episode"]["forward_sessions"])
    friction = float(rule["episode"]["friction"])
    if start_idx is None or start_idx + horizon >= len(closes):
        return None
    return closes[start_idx + horizon] / closes[start_idx] - 1.0 - friction


def record_forward_records(ledger, *, results, issued_ts,
                           horizon_open, horizon_close, lineage,
                           engine_id=None, rule=None):
    """Append one forward ledger record per scanned name, so
    each provisional state is later checked against what the
    name actually did. The engine is the frozen rule's ledger
    engine unless the caller names another consuming engine
    that carries the same frozen rule. Dedupe is the ledger's
    own: a republication of the same scan writes nothing.
    Returns (created, duplicates)."""
    if engine_id is None:
        engine_id = rule["forward_check"]["ledger_engine_id"]
    created = duplicates = 0
    for symbol, result in sorted(results.items()):
        value = {
            "proof_state": result["proof_state"],
            "provisional": True,
            "display_state": result["display_state"],
            "rule_id": result["rule_id"],
            "episodes": result["episodes"], "hits": result["hits"],
            "train": {k: result["train"][k]
                      for k in ("episodes", "hit_rate", "median")},
            "holdout": {k: result["holdout"][k]
                        for k in ("episodes", "hit_rate", "median")},
            "p_value": result["p_value"],
            "bh_q_value": result["bh_q_value"],
            "bh_significant": result["bh_significant"],
            "downgrade_reason": result["downgrade_reason"],
        }
        _row, made = ledger.append_forecast_declared(
            engine_id=engine_id, issued_ts=issued_ts, subject=symbol,
            quantity=FORWARD_QUANTITY, value=value,
            horizon_open=horizon_open, horizon_close=horizon_close,
            lineage=lineage, families=["price"],
            outcome={"kind": "provisional_proof_forward_check",
                     "symbol": symbol,
                     "horizon_sessions": int(
                         rule["forward_check"]["horizon_sessions"])})
        if made:
            created += 1
        else:
            duplicates += 1
    return created, duplicates


def grade_forward_record(ledger, forecast_row, realised_net_return):
    """Grade one forward record from the realised net forward
    return over its frozen horizon. A SUPPORTED name is checked
    on whether its forward return actually cleared the friction
    allowance; every state's realised return is on the grade, so
    the SUPPORTED population can be compared with OBSERVING."""
    hit = 1.0 if realised_net_return > 0 else 0.0
    # Repeat the row's frozen label identity when it carries one
    # (RC-21: forward rows now issue through the declared path, so
    # their grades must repeat the identity, per ledger.append_grade).
    frozen = {f: forecast_row[f] for f in (
        "label_context_fingerprint", "label_transform_id",
        "label_transform_hash") if forecast_row.get(f) is not None}
    return ledger.append_grade(forecast_row=forecast_row, **frozen, grade={
        "rule_id": "abs_error",
        "realised_net_return": realised_net_return,
        "proof_state_at_issue": (forecast_row.get("value") or {})
            .get("proof_state"),
        "scores": {"forward_hit": hit,
                   "forward_return_net": realised_net_return}})
