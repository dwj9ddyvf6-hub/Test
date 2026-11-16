#!/usr/bin/env python3
"""lenses.py — desk strategy lenses for unified stock analysis.

For each Femto sleeve, reports the strategy's OWN verdict on a symbol by
reading its ledger and universe. NEVER reimplements sleeve rules — extreme
rigor means reading the strategy's state, not vibing it.

Edge statuses come from the desk's strategic audit (2026-10-07):
  VALIDATED    sealed holdout / edge-lab grade
  WATCH        edge partial, eroded, or trails a naive alternative
  CONTESTED    validation disputed by a clean rerun (unresolved)
  EXPERIMENTAL live paper, no sealed validation cited
  CORE         desk flagship (Tensor 1H swing, v625 hash-pinned)
Sleeves that FAILED validation (5 GBM rule sleeves + daily_cyan_gbm,
timing null t=+0.49) and morning_dip (killed 2026-10-07) are EXCLUDED —
they never appear as lenses.

Usage: python3 lenses.py --symbol PLTR
Output: JSON.
"""
import argparse, json
from pathlib import Path

DESK = Path.home() / "workspace/alpaca-swing-desk"

def tensor_universe():
    # basket.json "symbols" is a list of dicts ({"symbol": "AEHR", ...}),
    # not plain strings — set(b["symbols"]) raised TypeError on the
    # unhashable dicts, the bare except swallowed it, and the lens
    # reported EVERY symbol as "not in tensor basket" (bug 2026-10-12).
    try:
        b = json.loads((DESK / "basket.json").read_text())
        out = set()
        for e in b["symbols"]:
            s = e.get("symbol") if isinstance(e, dict) else e
            if s:
                out.add(str(s).upper())
        return out
    except Exception:
        return set()

def phase_universe():
    try:
        return {l.strip().upper() for l in
                (DESK / "desk" / "phase_universe.txt").read_text().splitlines()
                if l.strip() and not l.startswith("#")}
    except Exception:
        return set()

SLEEVES = [
    {"key": "tensor", "ledger": "ledger.jsonl", "edge": "CORE",
     "edge_note": "Desk flagship 1H-swing strategy, v625 hash-pinned; timing authority",
     "universe": ("tensor basket (41)", lambda s, u: s in u),
     "universe_data": tensor_universe},
    {"key": "phase", "ledger": "phase_ledger.jsonl", "edge": "EXPERIMENTAL",
     "edge_note": "Milkman's Daily Bilbo port; live paper, no sealed holdout cited",
     "universe": ("phase proxy universe (24)", lambda s, u: s in u),
     "universe_data": phase_universe},
    {"key": "phoenix", "ledger": "phoenix_ledger.jsonl", "edge": "EXPERIMENTAL",
     "edge_note": "Live 7th sleeve; judgments #39-49 frozen",
     "universe": None, "universe_data": None},
    {"key": "bilbo_options", "ledger": "bilbo_options_ledger.jsonl", "edge": "EXPERIMENTAL",
     "edge_note": "Live 5th sleeve; 273/273 software tests are not edge validation",
     "universe": None, "universe_data": None},
    {"key": "momentum", "ledger": "momentum_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "Edge-lab grade B; holdout Sharpe 1.06 (audit 2026-10-07)",
     "universe": None, "universe_data": None},
    {"key": "confluence", "ledger": "confluence_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "Sealed 2023+ holdout (audit 2026-10-07)",
     "universe": None, "universe_data": None},
    {"key": "beatendown", "ledger": "beatendown_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "Sealed holdout 18.6% vs 8.9%, p=1e-13",
     "universe": None, "universe_data": None},
    {"key": "snapback", "ledger": "snapback_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "T10 study; small-cap mean reversion",
     "universe": None, "universe_data": None},
    {"key": "blowoff_d", "ledger": "blowoff_d_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "R4 full-universe; daily blowoff, down-regime",
     "universe": None, "universe_data": None},
    {"key": "gate_1h", "ledger": "gate_1h_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "R7 gated continuation, 1H",
     "universe": None, "universe_data": None},
    {"key": "leader_d", "ledger": "leader_d_ledger.jsonl", "edge": "VALIDATED",
     "edge_note": "R6 leader-1d, down-regime",
     "universe": None, "universe_data": None},
    {"key": "blowoff_1h", "ledger": "blowoff_1h_ledger.jsonl", "edge": "WATCH",
     "edge_note": "Edge exists (t=+5.28) but trails naive breakout",
     "universe": None, "universe_data": None},
    {"key": "leader_sc", "ledger": "leader_sc_ledger.jsonl", "edge": "WATCH",
     "edge_note": "Universe changed from validated spec",
     "universe": None, "universe_data": None},
    {"key": "ts_momentum", "ledger": "ts_momentum_decile_ledger.jsonl", "edge": "CONTESTED",
     "edge_note": "GO t=2.10 vs clean rerun PARK t=0.68 — unresolved, do not lean on",
     "universe": None, "universe_data": None},
    {"key": "legends_ema", "ledger": "legends_ema_ledger.jsonl", "edge": "EXPERIMENTAL",
     "edge_note": "QQQ paper only",
     "universe": ("QQQ only", lambda s, u: s == "QQQ"),
     "universe_data": lambda: set()},
]

EXCLUDED = ("rule_1d_cyan_smallcap, rule_1d_green_tom, rule_1h_cyan_raw, "
            "rule_1w_cyan_mom_adx, rule_1w_swing_beta_wt, daily_cyan_gbm "
            "(GBM timing null t=+0.49 — audit verdict KILL), "
            "morning_dip (killed 2026-10-07)")

KEY_FIELDS = ("ts", "episode", "decision", "event", "confidence", "phenotype",
              "action", "signal", "side", "reason", "note")

def latest_signal(ledger_path, symbol):
    """Latest ledger entry for the symbol (by ts), trimmed to key fields."""
    best, best_ts = None, ""
    try:
        with open(ledger_path) as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if str(e.get("symbol", "")).upper() != symbol:
                    continue
                ts = str(e.get("ts", ""))
                if ts >= best_ts:
                    best, best_ts = e, ts
    except FileNotFoundError:
        return None
    if not best:
        return None
    return {k: best.get(k) for k in KEY_FIELDS if best.get(k) is not None}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbol", required=True)
    sym = ap.parse_args().symbol.upper()
    lenses = []
    for s in SLEEVES:
        lens = {"sleeve": s["key"], "edge": s["edge"], "edge_note": s["edge_note"]}
        # applicability
        if s["universe"]:
            name, check = s["universe"]
            uni = s["universe_data"]()
            ok = check(sym, uni)
            lens["applies"] = ok
            lens["applicability"] = (f"in {name}" if ok
                                     else f"not in {name} — lens does not apply")
            if not ok:
                lenses.append(lens); continue
        else:
            lens["applies"] = True
            lens["applicability"] = "no universe gate"
        sig = latest_signal(DESK / s["ledger"], sym)
        lens["signal"] = sig if sig else "no signal on record"
        lenses.append(lens)
    print(json.dumps({"symbol": sym, "excluded_sleeves": EXCLUDED,
                      "lenses": lenses}, indent=1))

if __name__ == "__main__":
    main()
