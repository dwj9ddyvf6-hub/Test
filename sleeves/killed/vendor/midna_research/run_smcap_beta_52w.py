#!/usr/bin/env python3
"""Stage-1 discovery for PRE_REG_SMCAP_BETA_52W (frozen 2026-10-03).

Question: with low market cap + high beta, does the beaten-down enrichment
beat random stocks over 52 weeks?

Frozen design (see PRE_REG_SMCAP_BETA_52W.md):
- Stage 1: M2 qualifier-weeks, signal weeks 2019-11-01 -> 2021-12-31
  (qualifiers_dev.jsonl; the "2016-2021" bar window admits qualifiers only
  once >=200 weekly bars exist, hence the 2019-11 start).
- BEAT = BEAT_LO52 (close <= 0.80 x trailing-52wk high) union BEAT_RUN13
  (13wk trailing <= -20%).
- SMALL = bottom tercile of trailing-52wk mean weekly dollar volume among
  that week's M2 qualifiers. FALLBACK definition (pre-registered): no
  historical shares-outstanding source exists anywhere in the desk/research
  tree (grepped 2026-10-03), so market-cap proper is unavailable for the
  full window. Documented as a liquidity-size proxy, not cap.
- HIBETA = 52wk weekly beta vs SPY > 1.2, OLS on weekly log returns,
  min 40 paired weeks.
- Primary set: BEAT & SMALL & HIBETA. Endpoint: 52-week net forward return
  (Friday-close to Friday-close, 51bp round-trip). Control: same-week
  random symbols from the admitted universe (admitted, non-M2-qualifier),
  k = filtered count, md5("20261003|bh52|week").
- Decision: PASSES iff paired t > 2.0 AND mean net > 0.
- 52-week forwards need bars past 2022-07-01: merge weekly_bars_dev.json +
  weekly_2022plus.json for forwards ONLY (signal weeks unchanged).
- Stage 2 (2023+ holdout) runs ONLY on a Stage-1 pass (not implemented
  here; separate pre-reg + worker).
"""
import json
import math
import hashlib
import random
import statistics
from collections import defaultdict

BASE = "<workspace>/alpaca-swing-desk/desk/research/weekly-phenotypes/"
HOLD = "<workspace>/alpaca-swing-desk/desk/research/winner-confluence/holdout/"
COST = 0.0051  # 51bp round-trip, desk convention


def load_merged_bars():
    dev = json.load(open(BASE + "weekly_bars_dev.json"))
    plus = json.load(open(HOLD + "weekly_2022plus.json"))
    merged, dev_idx_map = {}, {}
    for sym in set(dev) | set(plus):
        seen = {}
        for b in dev.get(sym, []):
            seen[b["t"]] = b
        for b in plus.get(sym, []):
            seen[b["t"]] = b
        s = sorted(seen.values(), key=lambda b: b["t"])
        merged[sym] = s
        if sym in dev:
            # dev idx -> merged idx via timestamp (2022plus only appends)
            t2i = {b["t"]: i for i, b in enumerate(s)}
            dev_idx_map[sym] = {i: t2i[b["t"]] for i, b in enumerate(dev[sym])}
    return merged, dev_idx_map


def logrets(closes):
    return [math.log(closes[j] / closes[j - 1]) for j in range(1, len(closes))
            if closes[j] > 0 and closes[j - 1] > 0]


def ols_beta(ry, rx):
    n = len(rx)
    mx = sum(rx) / n
    my = sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    var = sum((a - mx) ** 2 for a in rx)
    if var <= 0:
        return None
    return cov / var


def paired_t(diffs):
    n = len(diffs)
    m = sum(diffs) / n
    sd = math.sqrt(sum((d - m) ** 2 for d in diffs) / (n - 1)) if n > 1 else 0.0
    t = m / (sd / math.sqrt(n)) if sd > 0 else 0.0
    return m, t


def main():
    bars, dev_idx_map = load_merged_bars()
    spy_t2c = {b["t"]: b["c"] for b in bars["SPY"]}

    # ---- M2 qualifier-weeks (same set as the model comparison: 2,587) ----
    quals = []  # (friday, symbol, dev_idx)
    week_rows = defaultdict(list)  # friday -> rows (for admitted universe)
    for line in open(BASE + "qualifiers_dev.jsonl"):
        r = json.loads(line)
        week_rows[r["friday"]].append(r)
        if r["m2"] and not r["m23_inadm"]:
            quals.append((r["friday"], r["symbol"], r["idx"]))
    print(f"M2 qualifier-weeks: {len(quals)}")

    # ---- per-qualifier features ----
    feats = []  # dicts with friday, symbol, i, beat, dvol52, hibeta, fwd_net
    no_fwd = 0
    for friday, sym, didx in quals:
        i = dev_idx_map[sym][didx]
        s = bars[sym]
        if i + 52 >= len(s):
            no_fwd += 1
            continue
        closes = [b["c"] for b in s]
        vols = [b["v"] for b in s]
        c = closes[i]
        hi52 = max(closes[i - 51:i + 1])
        beat_lo52 = c <= 0.80 * hi52
        beat_run13 = (c / closes[i - 13] - 1) <= -0.20
        beat = beat_lo52 or beat_run13
        dvol52 = sum(closes[j] * vols[j] for j in range(i - 51, i + 1)) / 52.0
        # beta vs SPY, 52 weekly log returns aligned by timestamp
        ts = [b["t"] for b in s[i - 52:i + 1]]  # 53 closes -> 52 returns
        sc = [closes[i - 52 + k] for k in range(53)]
        ok = [k for k in range(1, 53)
              if sc[k] > 0 and sc[k - 1] > 0 and
              spy_t2c.get(ts[k]) and spy_t2c.get(ts[k - 1])]
        rx_all = [math.log(sc[k] / sc[k - 1]) for k in ok]
        ry_all = [math.log(spy_t2c[ts[k]] / spy_t2c[ts[k - 1]]) for k in ok]
        beta = ols_beta(ry_all, rx_all) if len(rx_all) >= 40 else None
        hibeta = beta is not None and beta > 1.2
        fwd_net = closes[i + 52] / c - 1 - COST
        feats.append({"friday": friday, "symbol": sym, "i": i,
                      "beat": beat, "beat_lo52": beat_lo52,
                      "beat_run13": beat_run13, "dvol52": dvol52,
                      "beta": beta, "hibeta": hibeta, "fwd_net": fwd_net})
    print(f"qualifiers with 52w forward: {len(feats)} (dropped {no_fwd})")

    # ---- SMALL: bottom tercile of trailing-52wk mean $vol among that week's
    # ---- M2 qualifiers (pre-registered FALLBACK definition) ----
    by_week = defaultdict(list)
    for f in feats:
        by_week[f["friday"]].append(f)
    for friday, fs in by_week.items():
        dvols = sorted(f["dvol52"] for f in fs)
        cut = statistics.quantiles(dvols, n=3, method="inclusive")[0]
        for f in fs:
            f["small"] = f["dvol52"] <= cut

    def run_set(name, pred):
        sel = [f for f in feats if pred(f)]
        # control: per week, k = filtered count, admitted non-qualifier pool
        diffs, qrets, crets = [], [], []
        dropped_pairs = 0
        for friday in sorted(by_week):
            fs = [f for f in sel if f["friday"] == friday]
            if not fs:
                continue
            pool = [(r["symbol"], r["idx"]) for r in week_rows[friday]
                    if not r["m23_inadm"] and not r["m2"]]
            rng = random.Random(
                hashlib.md5(f"20261003|bh52|{friday}".encode()).hexdigest())
            rng.shuffle(pool)
            used = 0
            for sym_c, didx_c in pool:
                if used >= len(fs):
                    break
                s = bars[sym_c]
                i_c = dev_idx_map[sym_c][didx_c]
                if i_c + 52 >= len(s):
                    continue
                cc = [b["c"] for b in s]
                fwd_c = cc[i_c + 52] / cc[i_c] - 1 - COST
                q = fs[used]
                diffs.append(q["fwd_net"] - fwd_c)
                qrets.append(q["fwd_net"])
                crets.append(fwd_c)
                used += 1
            dropped_pairs += len(fs) - used
        n = len(diffs)
        mean_q = sum(qrets) / n if n else 0.0
        mean_c = sum(crets) / n if n else 0.0
        mt, t = paired_t(diffs) if n > 1 else (0.0, 0.0)
        return {"name": name, "n": n, "mean_net_qual": mean_q,
                "mean_net_ctrl": mean_c, "paired_t": t,
                "dropped_pairs": dropped_pairs}

    primary = run_set("BEAT&SMALL&HIBETA",
                      lambda f: f["beat"] and f["small"] and f["hibeta"])
    d_beat = run_set("BEAT", lambda f: f["beat"])
    d_bs = run_set("BEAT&SMALL", lambda f: f["beat"] and f["small"])
    d_bh = run_set("BEAT&HIBETA", lambda f: f["beat"] and f["hibeta"])

    # descriptives on filter composition
    n_beat = sum(1 for f in feats if f["beat"])
    n_small = sum(1 for f in feats if f["small"])
    n_hibeta = sum(1 for f in feats if f["hibeta"])
    n_run13 = sum(1 for f in feats if f["beat_run13"])

    passes = primary["paired_t"] > 2.0 and primary["mean_net_qual"] > 0
    underpowered = primary["n"] < 100
    stats = {
        "primary": primary,
        "descriptives": [d_beat, d_bs, d_bh],
        "composition": {"n_qualifiers": len(feats),
                        "n_beat": n_beat, "n_small": n_small,
                        "n_hibeta": n_hibeta, "n_beat_run13": n_run13},
        "small_definition": ("FALLBACK: bottom tercile of trailing-52wk "
                             "mean weekly dollar volume among that week's "
                             "M2 qualifiers (no historical shares-outstanding "
                             "source exists in the desk/research tree)"),
        "decision": "PASS" if passes else "FAIL",
        "underpowered": underpowered,
        "stage2_triggered": passes,
    }
    json.dump(stats, open(BASE + "smcap_beta_52w_stats.json", "w"), indent=1)
    print(json.dumps(stats, indent=1))
    return stats


if __name__ == "__main__":
    main()
