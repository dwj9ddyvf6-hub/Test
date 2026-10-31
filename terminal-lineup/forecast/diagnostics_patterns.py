"""Diagnostics and audit patterns adopted 2026-10-29 (DEEP-PASS 3.2 items 8, 9, 12).

Three patterns, none of them a market forecast:

1. Source clock (3.2.8, M12): a data arrival diagnostic over refresh
   history. It estimates, per source, how often a refresh arrived on
   time, as a Laplace smoothed frequency with a Wilson interval,
   pooled exact source first, then source family, then refused.
   Flaw fixed on import: his version returned a Wilson interval even
   in the insufficient history state, so a consumer could quote an
   interval for an estimate the function itself refused to make.
   Here, when the estimate is refused, the interval is suppressed
   (None) with the estimate. Labelled diagnostic only, never a
   market forecast and never ledgered as one.

2. Boundary map sweeps (3.2.9, M10 and M15): the parity standard for
   any scorer mirror and the pre publication check for any new
   multiplicative scorer. Sweeps run one feature corners, pairwise
   corners and the joint corner through the scorer directly. An
   abstained baseline produces no map at all. Parity proven by one
   benign synthetic vector does not count.

3. Confluence renormalisation discipline (3.2.12, L01): any composite
   that renormalises over present inputs must carry coverage beside
   the score in the same visual weight, and coverage floors are
   computed on weight, not count. His candidate passed its 60 percent
   floor on metric count, so many light metrics could pass it while
   its heaviest metric was blank, and a score on 3 of 8 categories
   could still print in the 90s. Here the floor is on weight.
"""
import math
import re

Z = 1.96
AGE_BANDS = ((0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0),
             (4.0, 8.0), (8.0, None))


def wilson_interval(successes, n, z=Z):
    if n <= 0:
        return None
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def age_band(age_ratio):
    """Six bands by age to horizon ratio, to 8x (M12 banding)."""
    if age_ratio is None or not math.isfinite(float(age_ratio)) or age_ratio < 0:
        return None
    for i, (lo, hi) in enumerate(AGE_BANDS):
        if age_ratio >= lo and (hi is None or age_ratio < hi):
            return i
    return len(AGE_BANDS) - 1


def _validate_history(rows):
    for r in rows:
        horizon = r.get("horizon_seconds")
        start, end = r.get("label_start"), r.get("label_end")
        if horizon is not None and start is not None and end is not None:
            if float(end) - float(start) > float(horizon) + 1e-9:
                raise ValueError(
                    "label timing contradicts declared horizon for "
                    f"source {r.get('source')!r}: label span exceeds horizon")


def estimate_source_clock(history, source, family=None, min_samples=30):
    """Refresh hazard estimate for one source.

    history rows: {source, family, on_time: bool, horizon_seconds,
    label_start, label_end, age_ratio}. Strict eligibility: a row
    whose label timing contradicts its declared horizon raises and
    kills the whole estimate (fail closed, M12), never per row
    exclusion. Returns a dict with state exact, family or
    insufficient_history. On insufficient_history both estimate and
    interval are None: the interval is suppressed whenever the
    estimate itself is refused.
    """
    if min_samples < 2:
        raise ValueError("min_samples must be at least 2")
    _validate_history(history)
    for level, pool in (
            ("exact", [r for r in history if r.get("source") == source]),
            ("family", [r for r in history
                        if family is not None and r.get("family") == family])):
        if len(pool) >= min_samples:
            s = sum(1 for r in pool if r.get("on_time"))
            est = (s + 1) / (len(pool) + 2)
            return {"source": source, "state": level,
                    "pool": level, "n": len(pool), "successes": s,
                    "estimate": est,
                    "wilson_interval": wilson_interval(s, len(pool)),
                    "kind": "data_arrival_diagnostic_not_a_forecast"}
    return {"source": source, "state": "insufficient_history",
            "pool": None, "n": sum(1 for r in history
                                   if r.get("source") == source),
            "successes": None, "estimate": None,
            "wilson_interval": None,
            "kind": "data_arrival_diagnostic_not_a_forecast"}


_DONE_RE = re.compile(r"^done\s+(?P<source>\S+)\s+in\s+\d+s\s+exit\s+(?P<exit>\d+)")


def parse_refresh_proof_log(text, family="terminal_refresh"):
    """Parse refresh runner logs (start/done lines) into history rows.

    A done line with exit 0 is an on time arrival; any other exit is
    not. Sources with only a start line produce no row: absence is
    not a failure count and not a success.
    """
    rows = []
    for line in text.splitlines():
        m = _DONE_RE.match(line.strip())
        if m:
            rows.append({"source": m.group("source"), "family": family,
                         "on_time": m.group("exit") == "0"})
    return rows


def diagnostic_over_refresh_logs(log_texts, min_samples=30):
    """Per source diagnostic over one or more refresh log texts."""
    history = []
    for text in log_texts:
        history.extend(parse_refresh_proof_log(text))
    sources = sorted({r["source"] for r in history})
    return {"kind": "data_arrival_diagnostic_not_a_forecast",
            "label": "Data arrival diagnostic. Not a market forecast.",
            "min_samples": min_samples,
            "sources": [estimate_source_clock(
                history, s, family="terminal_refresh",
                min_samples=min_samples) for s in sources]}


# --- Boundary map sweeps (3.2.9) -------------------------------------

def _call(scorer, point):
    out = scorer(dict(point))
    if out is None:
        return None
    if isinstance(out, dict) and out.get("abstain"):
        return None
    return out


def boundary_sweep(scorer, baseline, ranges, max_dims=8):
    """Corner map for a scorer.

    scorer takes a dict and returns a score, or None / {abstain: True}
    for an abstention. ranges maps name to (low, high) and each range
    must lie inside the scorer domain and contain the baseline value.
    An abstained baseline produces no map at all:
    status unavailable_baseline_abstained.
    """
    if len(ranges) > max_dims:
        raise ValueError(f"at most {max_dims} stress dimensions")
    for name, (lo, hi) in ranges.items():
        if name not in baseline:
            raise ValueError(f"range for undeclared input {name!r}")
        if not (lo <= baseline[name] <= hi):
            raise ValueError(f"baseline {name} outside its stress range")
    base = _call(scorer, baseline)
    if base is None:
        return {"status": "unavailable_baseline_abstained", "baseline": None,
                "cases": []}
    cases = []

    def add(kind, point):
        cases.append({"kind": kind, "point": dict(point),
                      "score": _call(scorer, point)})

    names = list(ranges)
    for name in names:
        for edge in ranges[name]:
            p = dict(baseline); p[name] = edge; add("one_feature", p)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for ea in ranges[a]:
                for eb in ranges[b]:
                    p = dict(baseline); p[a] = ea; p[b] = eb
                    add("pairwise", p)
    if names:
        for pick in (0, 1):
            p = dict(baseline)
            for name in names:
                p[name] = ranges[name][pick]
            add("joint_corner", p)
    numeric = [c["score"] for c in cases if isinstance(c["score"], (int, float))]
    return {"status": "ok", "baseline": base, "cases": cases,
            "score_min": min(numeric) if numeric else None,
            "score_max": max(numeric) if numeric else None,
            "abstained_cases": sum(1 for c in cases if c["score"] is None)}


def parity_sweep(scorer_a, scorer_b, baseline, ranges, tol=1e-9):
    """Parity between two implementations proven over boundary sweeps,
    never over one synthetic vector. Returns mismatches by case."""
    ma = boundary_sweep(scorer_a, baseline, ranges)
    mb = boundary_sweep(scorer_b, baseline, ranges)
    if ma["status"] != mb["status"]:
        return {"status": "mismatch", "reason": "baseline state differs",
                "a": ma["status"], "b": mb["status"]}
    if ma["status"] != "ok":
        return {"status": ma["status"], "mismatches": []}
    mismatches = []
    for ca, cb in zip(ma["cases"], mb["cases"]):
        sa, sb = ca["score"], cb["score"]
        if (sa is None) != (sb is None):
            mismatches.append({"point": ca["point"], "a": sa, "b": sb})
        elif isinstance(sa, (int, float)) and abs(sa - sb) > tol:
            mismatches.append({"point": ca["point"], "a": sa, "b": sb})
    return {"status": "ok" if not mismatches else "mismatch",
            "cases_checked": len(ma["cases"]), "mismatches": mismatches}


# --- Confluence renormalisation discipline (3.2.12) ------------------

def renormalised_composite(items, floor=0.60):
    """Weighted composite renormalised over present inputs only.

    items: [{value, weight, present}]. Coverage is computed on weight
    (present weight over total weight), not on count. The floor is a
    weight floor. The result always carries coverage_weight and
    coverage_count beside the score, at the same prominence in any
    rendering (see format_score_with_coverage).
    """
    total_w = sum(float(i["weight"]) for i in items)
    if total_w <= 0:
        return {"score": None, "coverage_weight": 0.0,
                "coverage_count": 0.0, "passes_weight_floor": False,
                "present_weight": 0.0, "total_weight": 0.0}
    present = [i for i in items if i.get("present") and i.get("value") is not None]
    present_w = sum(float(i["weight"]) for i in present)
    cov_w = present_w / total_w
    cov_c = len(present) / len(items) if items else 0.0
    score = None
    if present_w > 0:
        score = sum(float(i["value"]) * float(i["weight"])
                    for i in present) / present_w
    return {"score": score, "coverage_weight": cov_w,
            "coverage_count": cov_c,
            "passes_weight_floor": cov_w >= floor - 1e-9,
            "floor": floor, "present_weight": present_w,
            "total_weight": total_w}


def format_score_with_coverage(result):
    """Score and coverage in the same visual weight: one string, both
    bolded by callers as a unit, neither subordinated."""
    if result.get("score") is None:
        return "Score: no score. Coverage: {:.0f}% of weight.".format(
            100 * result.get("coverage_weight", 0.0))
    return "Score: {:.1f}. Coverage: {:.0f}% of weight.".format(
        float(result["score"]), 100 * result["coverage_weight"])
