"""Grade A (FACTORY.md §4; P2 grade A): which cells promoted in a first search replicate in a rerun on a second dataset.

The rule is the pre-registration of docs/research/forecast-search-rerun-2026-10-27.md, fixed before the rerun:
  untestable        the cell is under the minimum (status untested) or absent in the rerun: not counted against it
  A                 tested, the rerun's discovery sign equals run 1's, and the rerun's own verdict is promoted-B
  confirmed         not A, same sign, and the rerun holdout's block t, signed by RUN 1's sign, is >= HOLD_T (2.0)
  flipped           the rerun holdout's block t signed by run 1's sign is <= -HOLD_T
  not-replicated    tested, none of the above
rate = A / (A + confirmed + flipped + not-replicated). A forecaster x target passes when at least half of its tested
promoted cells are A or confirmed. The `all` cell of each forecaster x target is reported on its own.
Inputs are the slim report JSONs search_deep.write produces ({"rows": {"columns", "data"}})."""
import json

PROMOTED = "promoted-B"
HOLD_T = 2.0
GRADES = ("A", "confirmed", "flipped", "not-replicated", "untestable")


def rows_of(rep):
    r = rep["rows"]
    if isinstance(r, dict):
        cols = r["columns"]
        return [dict(zip(cols, x)) for x in r["data"]]
    return list(r)


def load(path):
    with open(path) as f:
        return json.load(f)


def index(rows):
    return {(r["forecaster"], r["target"], r["cell"]): r for r in rows}


def grade(r1, r2):
    """-> (grade, reason) for one run-1 promoted row against the rerun's row for the same cell (or None)"""
    if r2 is None or r2.get("status") != "tested":
        return "untestable", "absent or under the cell minimum in the rerun"
    s1, s2 = int(r1["sign"]), r2.get("sign")
    ht = r2.get("hold_t_signed")                       # signed by the rerun's own discovery sign
    t1 = None if ht is None or s2 is None else float(ht) * int(s2) * s1       # the same t signed by run 1's sign
    if t1 is not None and t1 <= -HOLD_T:
        return "flipped", f"rerun holdout t {t1:+.1f} against run 1's sign"
    if s2 is not None and int(s2) == s1 and r2.get("verdict") == PROMOTED:
        return "A", "promoted-B in the rerun"
    if s2 is not None and int(s2) == s1 and t1 is not None and t1 >= HOLD_T:
        return "confirmed", f"same sign, rerun holdout t {t1:+.1f}, rerun verdict {r2.get('verdict')}"
    why = "sign differs in the rerun's discovery" if s2 is None or int(s2) != s1 else f"rerun verdict {r2.get('verdict')}"
    return "not-replicated", why


def compare(rep1, rep2):
    """-> {cells, summary, by_ft, all_cells}; every run-1 promoted cell appears once with its grade"""
    r2 = index(rows_of(rep2))
    out = []
    for r1 in rows_of(rep1):
        if r1.get("verdict") != PROMOTED:
            continue
        key = (r1["forecaster"], r1["target"], r1["cell"])
        g, why = grade(r1, r2.get(key))
        x = r2.get(key) or {}
        out.append({"forecaster": key[0], "target": key[1], "cell": key[2], "sign1": int(r1["sign"]), "grade": g,
                    "why": why, "verdict2": x.get("verdict"), "sign2": x.get("sign"),
                    "disc2": x.get("disc_mean"), "hold2_signed": x.get("hold_signed"),
                    "hold2_t_signed": x.get("hold_t_signed"), "net2": x.get("execution_net"),
                    "hold1_signed": r1.get("hold_signed"), "hold1_t_signed": r1.get("hold_t_signed"),
                    "disc1": r1.get("disc_mean")})
    return {"cells": out, "summary": summarize(out), "by_ft": by_forecaster_target(out),
            "all_cells": [c for c in out if c["cell"] == "all"]}


def summarize(cells):
    n = {g: sum(1 for c in cells if c["grade"] == g) for g in GRADES}
    den = n["A"] + n["confirmed"] + n["flipped"] + n["not-replicated"]
    return {"promoted": len(cells), **n, "denominator": den,
            "rate_A": None if den == 0 else round(n["A"] / den, 4),
            "rate_A_or_confirmed": None if den == 0 else round((n["A"] + n["confirmed"]) / den, 4)}


def by_forecaster_target(cells):
    g = {}
    for c in cells:
        g.setdefault((c["forecaster"], c["target"]), []).append(c)
    out = []
    for (f, t), cs in sorted(g.items()):
        s = summarize(cs)
        tested = s["denominator"]
        ok = s["A"] + s["confirmed"]
        out.append({"forecaster": f, "target": t, **s, "passes": bool(tested and ok * 2 >= tested)})
    return out


def _f(x, nd=4):
    return "—" if x is None else f"{x:+.{nd}f}"


def markdown(cmp_, rep2):
    """the results sections of docs/research/forecast-search-rerun-*.md (appended after the pre-registration)"""
    s = cmp_["summary"]
    v = rep2["verdicts"]
    L = ["", "## 2. The rerun", "",
         f"Holdout opened once: key `{rep2['holdout']['key']}` at {rep2['holdout']['opened_at']} (discovery digest "
         f"`{rep2['holdout']['discovery_digest'][:16]}…`). Split {rep2['split']}, fold unit {rep2.get('wf_unit', 'year')}, "
         f"embargo >= {rep2['embargo_days_min']} days, BH q {rep2['q']}.",
         f"Data: {rep2['data']['names']:,} names, {rep2['data']['bars']:,} bars, {rep2['data']['window'][0]} to "
         f"{rep2['data']['window'][1]}; panel {rep2['panel']['rows']:,} rows; {rep2['panel']['xs_specs']} cross-sectional "
         f"and {rep2['panel']['market_specs']} market specs (the registry has grown since run 1's 109 + 14).",
         f"Cells {rep2['cells_total']:,}; tested {rep2['cells_tested']:,}; untested {rep2['cells_untested']:,}; passing BH "
         f"{rep2['bh_pass']:,}. Verdicts: " + ", ".join(f"{k} {n:,}" for k, n in sorted(v.items(), key=lambda kv: -kv[1])) + ".",
         "", "## 3. Replication of run 1's promoted cells", "",
         f"Run 1 promoted {s['promoted']:,} cells (grade B).", "",
         "| grade | cells |", "|---|---|"]
    for g in GRADES:
        L.append(f"| {g} | {s[g]:,} |")
    L += ["", f"Denominator (tested here, not untestable): {s['denominator']:,}. Replication rate: **A {s['rate_A']:.1%}**; "
          f"A or confirmed {s['rate_A_or_confirmed']:.1%}. Flipped (the rerun holdout significantly against run 1): "
          f"{s['flipped']}.", "",
          "## 4. By forecaster and target", "",
          "| forecaster | target | promoted | A | confirmed | flipped | not replicated | untestable | passes |",
          "|---|---|---|---|---|---|---|---|---|"]
    for x in sorted(cmp_["by_ft"], key=lambda x: (-x["A"], -x["confirmed"], x["forecaster"])):
        L.append(f"| {x['forecaster']} | {x['target']} | {x['promoted']} | {x['A']} | {x['confirmed']} | {x['flipped']} | "
                 f"{x['not-replicated']} | {x['untestable']} | {'yes' if x['passes'] else 'no'} |")
    L += ["", "## 5. The pooled (`all`) cell of each forecaster and target", "",
          "| forecaster | target | grade | rerun verdict | disc here | hold here (signed t) | hold run 1 (signed t) |",
          "|---|---|---|---|---|---|---|"]
    for c in cmp_["all_cells"]:
        L.append(f"| {c['forecaster']} | {c['target']} | {c['grade']} | {c['verdict2'] or '—'} | {_f(c['disc2'])} | "
                 f"{_f(c['hold2_signed'])} ({_f(c['hold2_t_signed'], 1)}) | {_f(c['hold1_signed'])} "
                 f"({_f(c['hold1_t_signed'], 1)}) |")
    a = [c for c in cmp_["cells"] if c["grade"] == "A"]
    L += ["", f"## 6. Cells graded A: {len(a)}", "",
          "| forecaster | target | cell | sign | disc here | hold here (signed t) | net/opp here | hold run 1 (signed t) |",
          "|---|---|---|---|---|---|---|---|"]
    for c in sorted(a, key=lambda c: (c["target"].startswith(("realized", "spy")), c["forecaster"], c["target"], c["cell"])):
        L.append(f"| {c['forecaster']} | {c['target']} | {c['cell']} | {c['sign1']:+d} | {_f(c['disc2'])} | "
                 f"{_f(c['hold2_signed'])} ({_f(c['hold2_t_signed'], 1)}) | {_f(c['net2'])} | {_f(c['hold1_signed'])} "
                 f"({_f(c['hold1_t_signed'], 1)}) |")
    return "\n".join(L) + "\n"
