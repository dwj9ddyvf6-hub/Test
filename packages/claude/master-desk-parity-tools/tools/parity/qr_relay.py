"""qr_relay: the UIR and CRG rows' monthly models, admissions and funded basket vs R8's executed outputs.

SOURCE: quant-research-backup@d170596b research-archives/2026-10-08-ten-strategy-edge-research-r8:
  uir/PREDICTIONS.jsonl.gz (blob 89f90176): every policy's monthly-model prediction per relay row (ALPACA, no
      exclusion, no shift: PRICE_CONTROL, FINANCIAL, ABSORPTION, HALF_FINANCIAL, LOW_ABSORPTION_PRICE,
      POSITIVE_FINANCIAL_PRICE, REVERSED_ABSORPTION) and its admission (> 30 bp);
  uir/accounts/ALPACA__ABSORPTION__drop_NONE__shift0__C15__{development,outer_reused_discovery}.json.gz: the basket
      targets the ABSORPTION policy produced;
  crg/PREDICTIONS.json.gz (blob 144d2b73): all 24 candidates' predictions per own-stock row.
Inputs: R3 events/EVENT_ROWS.json (vendored). PORT: relay.fit / relay.predict with the sleeves' feature functions
(uir.absorption, crg.surprise_history; the other R8 policies' features restated alongside for coverage), the
month cutoffs from the desk's sessions, relay.basket over the admissions. Compared: predictions to 1e-12, admissions
exactly, basket targets exactly (1e-12)."""
import collections
import gzip
import json
import os

import numpy as np

from . import write_receipt

R8 = os.environ.get("R8_DIR", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/dl/r8")


def uir_feats(r, policy):
    from desk.sleeves.quant_research import uir as U
    p, oh, s = list(r["x_price"][:6]), list(r["x_price"][6:]), float(r["financial_surprise"])
    sr, rr, vol = p[0], p[1], p[4]
    gap = float(np.clip((sr - rr) / max(vol, 1e-6), -5, 5))
    absorb = float(np.clip(rr / max(vol, 1e-6), -5, 5))
    if policy == "x_price":
        return p + oh
    if policy == "x_financial":
        return p + oh + [s, abs(s), max(s, 0) * max(-sr, 0), s * (sr - rr)]
    if policy == "x_absorption":
        return U.absorption(r)
    return p + oh + [-s, abs(s), -s * gap, -s * absorb, max(-s, 0) * max(-sr, 0)]      # reversed absorption


def run():
    from desk.sleeves.quant_research import crg as G
    from desk.sleeves.quant_research import relay as R
    st = {"uir": {"cases": 0, "bad": 0}, "uir_basket": {"cases": 0, "bad": 0}, "crg": {"cases": 0, "bad": 0}}
    diffs = []
    # ---------------------------------------------------------------- UIR
    rows = [r for r in R.history_rows("UIR_fixed_relays") if r["horizon"] == 20]
    days, ix = R.sessions()
    preds = [json.loads(l) for l in gzip.open(os.path.join(R8, "uir", "PREDICTIONS.jsonl.gz"), "rt")]
    preds = [p for p in preds if p["provider"] == "ALPACA" and p["exclude"] is None and p["shift"] == 0]
    by_row = {r["row_id"]: r for r in rows}
    fits = {}
    for month in sorted({p["decision_date"][:7] for p in preds}):
        cutoff = R.month_cutoff(month)
        train = [r for r in rows if r["label_exit_index"] < cutoff - 21]
        for key in ("x_price", "x_financial", "x_absorption"):
            fits[month, key] = R.fit(train, None, 10.0, feats=lambda r, k=key: uir_feats(r, k))
    for p in preds:
        r = by_row[p["row_id"]]
        m = p["decision_date"][:7]
        pc = R.predict(fits[m, "x_price"], uir_feats(r, "x_price"))
        f = R.predict(fits[m, "x_financial"], uir_feats(r, "x_financial"))
        a = R.predict(fits[m, "x_absorption"], uir_feats(r, "x_absorption"))
        rev = R.predict(fits[m, "x_absorption"], uir_feats(r, "rev"))
        sr, rr = r["x_price"][:2]
        vals = {"PRICE_CONTROL": pc, "FINANCIAL": f, "ABSORPTION": a, "HALF_FINANCIAL": (pc + f) / 2,
                "LOW_ABSORPTION_PRICE": pc if sr > 0 and rr < 0.5 * sr else None,
                "POSITIVE_FINANCIAL_PRICE": pc if r["financial_surprise"] > 0 else None, "REVERSED_ABSORPTION": rev}
        got = vals[p["policy"]]
        st["uir"]["cases"] += 1
        ok = (got is None and p["prediction"] is None) or (got is not None and p["prediction"] is not None
                                                           and abs(got - p["prediction"]) <= 1e-12)
        ok = ok and ((got is not None and got > .003) == bool(p["admitted"]))
        if not ok:
            st["uir"]["bad"] += 1
            diffs.append({"part": "uir", "row": p["row_id"][:12], "policy": p["policy"], "port": got,
                          "r8": p["prediction"]})
    # the ABSORPTION basket over the R8 split windows
    adm = collections.defaultdict(list)
    for p in preds:
        if p["policy"] == "ABSORPTION":
            adm[p["decision_date"]].append(p)
    for split, name in (("development", "ABSORPTION_development.json.gz"), ("outer", "ABSORPTION_outer.json.gz")):
        path = os.path.join(R8, "uir", name)
        if not os.path.exists(path):
            continue
        want = json.load(gzip.open(path, "rt"))["targets"]
        start, end = (("2022-01-03", "2023-12-29") if split == "development" else ("2024-01-02", "2026-10-07"))
        got, active, last = {days[ix[start] - 1]: {"SPY": .475, "QQQ": .475}}, {}, {"SPY": .475, "QQQ": .475}
        for d in days[ix[start]:ix[end] + 1]:
            j = ix[d]
            active = {s: v for s, v in active.items() if v > j}
            for p in sorted(adm.get(d, []), key=lambda x: (by_row[x["row_id"]]["receiver"], x["source_id"])):
                if p["admitted"]:
                    active[by_row[p["row_id"]]["receiver"]] = j + 20
            w = R.basket(active)
            if w != last:
                got[d] = w
                last = w
        for d in sorted(set(want) | set(got)):
            st["uir_basket"]["cases"] += 1
            a, b = want.get(d), got.get(d)
            if a is None or b is None or set(a) != set(b) or any(abs(a[k] - b[k]) > 1e-12 for k in a):
                st["uir_basket"]["bad"] += 1
                diffs.append({"part": "uir_basket", "split": split, "date": d, "r8": a, "port": b})
    # ---------------------------------------------------------------- CRG
    crows = R.history_rows("CRG_own_stock")
    cp = json.load(gzip.open(os.path.join(R8, "crg", "PREDICTIONS.json.gz"), "rt"))
    pri = R.priors(crows, [])

    def before(r):
        return [v for d, v in pri.get(r["sender"], []) if d < r["decision_date"]]

    def feats(r, variant):
        base = list(r["x_price"])
        s, prior = float(r["financial_surprise"]), before(r)
        p = float(prior[-1]) if prior else 0.
        m = float(np.mean(prior[-4:])) if prior else 0.
        t, tp, tm = float(np.tanh(s)), float(np.tanh(p)), float(np.tanh(m))
        reaction, vol = base[0], max(base[4], 1e-6)
        return {"BASE": base, "ORIGINAL_FINANCIAL": r["x_financial"], "SURPRISE_HISTORY": G.surprise_history(r, prior),
                "ROBUST_HISTORY": base + [t, tp, t * tp, tm],
                "ABSORPTION_HISTORY": base + [t, tp, t * tp, tm, t * np.sign(reaction), t * abs(reaction) / vol],
                "PRIOR_ONLY_PLACEBO": base + [tp, tm, float(p > 0)]}[variant]
    by_src = {(r["source_id"], r["horizon"]): r for r in crows}
    cfits = {}
    for p in cp:
        variant, h, lam = p["candidate_id"].split("__")
        h, lam = int(h[1:]), float(lam[1:])
        month = p["decision_date"][:7]
        key = (month, p["candidate_id"])
        if key not in cfits:
            cutoff = R.month_cutoff(month)
            train = [r for r in crows if r["horizon"] == h and r["label_exit_index"] < cutoff - 21]
            cfits[key] = R.fit(train, None, lam, feats=lambda r, v=variant: feats(r, v))
        r = by_src[p["source_id"], h]
        got = R.predict(cfits[key], feats(r, variant))
        st["crg"]["cases"] += 1
        if abs(got - p["prediction"]) > 1e-12:
            st["crg"]["bad"] += 1
            diffs.append({"part": "crg", "candidate": p["candidate_id"], "date": p["decision_date"], "port": got,
                          "r8": p["prediction"]})
    cases = sum(v["cases"] for v in st.values())
    bad = sum(v["bad"] for v in st.values())
    out = {"family": "quant_research", "sleeves": ["qr_unpricedinformationrelay", "qr_catalystresolutiongap"],
           "cases": cases, "identical": cases - bad, "n_diffs": bad, "detail": st, "diffs": diffs[:50],
           "source": {"repo": "quant-research-backup", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
                      "r8": "research-archives/2026-10-08-ten-strategy-edge-research-r8/{uir,crg}",
                      "rows": "research-archives/2026-10-08-alpha-extraction-r3/events/EVENT_ROWS.json"},
           "method": "R8's own monthly predictions / admissions / ABSORPTION basket targets vs the port's fit, predict, "
                     "features and basket on R3's rows",
           "not_in_this_comparison": ["live SEC events (divergence 2: see tools/parity/qr_relay_sec.py)",
                                      "execution (3)"]}
    write_receipt("qr_relay", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["detail"]))
    for d in r["diffs"][:10]:
        print(d)
