#!/usr/bin/env python3
"""T474U-CRYPTO-PORT-20261116 fidelity check: the desk port
(desk3/t474u_crypto.py) against GrokBot's recorded evidence for the
t474u crypto filter twins.

Inputs (this directory, provenance in desk3/t474u_crypto.py's
docstring):
  bars_<SYM>-USDT.json    the build-time OKX 4h series, 399 completed
                          bars, t in [1788940800, 1794672000] for
                          every symbol — re-fetched from OKX public
                          history-candles 2026-11-16; endpoints and
                          counts match sweeps.json's series table.
  historical_fires.json   md2's recorded replay fires (n_fires,
                          last_t per sleeve), cos2-estate
                          research/x_t473u @ 31f90a01187b.
  sweeps_expected.json    the chosen-param records of md2's
                          evidence/calibrations/t474u/sweeps.json
                          (IS/OOS x 1x/2x/4x/5x fee-stress metrics).
  original_code_fires.json  fire bar indices/timestamps produced by
                          GrokBot's ORIGINAL numpy code (ind.py +
                          t474u_indicators.py @ c2de069) over the
                          same bars, backtest sweep definition.

Checks, per sleeve (the 9 ported sleeves + the 3 BTC twins as
controls, computed by the same ported signal code on BTC bars):
  FIRES   ported fires_series count and last fire timestamp equal
          the recorded historical_fires values exactly, AND the
          ported fire timestamp list equals the original code's
          list exactly (trade-for-trade on entries).
  TRADES  ported simulate_trades metrics equal the recorded sweeps
          metrics field-for-field (n, win, net, avg, maxdd, pf,
          npdd at every stress level, IS and OOS) — trade-for-trade
          on the simulated ledger (entries at next open, 16h hold).

Writes t474u_fidelity_result.json beside this script and exits 0
only on a full PASS.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from desk3 import t474u_crypto as T  # noqa: E402

SYMS = {"BTCUSDT": "BTC-USDT", "ADAUSDT": "ADA-USDT",
        "ENJUSDT": "ENJ-USDT", "LINKUSDT": "LINK-USDT"}
KIND_FAM = {"bratr": "bar_range_atr", "mfi": "mfi_gate",
            "stdev": "btc_stdev"}
PORTED = {f"crypto_{k}_{b.lower()}"
          for k in ("bratr", "mfi", "stdev") for b in ("ADA", "ENJ", "LINK")}


def load_bars(inst):
    raw = json.load(open(os.path.join(HERE, f"bars_{inst}.json")))
    return [{"t": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4],
             "v": r[5]} for r in raw]


def main():
    fires_ref = json.load(open(os.path.join(HERE, "historical_fires.json")))
    sweeps = json.load(open(os.path.join(HERE, "sweeps_expected.json")))
    orig = json.load(open(os.path.join(HERE, "original_code_fires.json")))
    result = {"check": "T474U-CRYPTO-PORT-20261116",
              "source_engine": "md2 mdesk/engines/t474u_x.py @ master-desk c2de06921bac7c902b19daa572dcbf8f831fe60f",
              "sleeves": {}, "pass": True}
    for sym, inst in SYMS.items():
        bars = load_bars(inst)
        series_meta = sweeps["series"][sym]
        assert len(bars) == series_meta["n"] == 399, (sym, len(bars))
        assert bars[0]["t"] == series_meta["t0"], sym
        assert bars[-1]["t"] == series_meta["t1"], sym
        for kind in ("bratr", "mfi", "stdev"):
            sid = f"crypto_{kind}_{sym[:-4].lower()}"
            ref = fires_ref[sid]
            idx = T.fires_series(kind, bars)
            got = {"n_fires": len(idx),
                   "last_t": float(bars[idx[-1]]["t"]) if idx else None,
                   "fires": [{"t": float(bars[i]["t"]),
                              "close": bars[i]["c"]} for i in idx]}
            fires_ok = (got["n_fires"] == ref["n_fires"]
                        and got["last_t"] == ref["last_t"])
            orig_ts = orig["sleeves"][sid]["timestamps"]
            orig_ok = ([f["t"] for f in got["fires"]] == orig_ts
                       and idx == orig["sleeves"][sid]["indices"])
            mine = T.simulate_trades(kind, bars)
            exp = sweeps["families"][KIND_FAM[kind]][sym]
            exp_rec = {"IS": exp["IS"], "OOS": exp["OOS"]}
            trades_ok = mine == exp_rec
            ok = fires_ok and orig_ok and trades_ok
            result["pass"] = result["pass"] and ok
            result["sleeves"][sid] = {
                "ported": sid in PORTED,
                "fires": {"recorded": {"n_fires": ref["n_fires"],
                                       "last_t": ref["last_t"]},
                          "ported": got, "match": fires_ok},
                "original_code_fires_match": orig_ok,
                "trades": {"recorded": exp_rec, "ported": mine,
                           "match": trades_ok},
                "verdict": "PASS" if ok else "FAIL"}
    out = os.path.join(HERE, "t474u_fidelity_result.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=1)
    n_pass = sum(1 for s in result["sleeves"].values()
                 if s["verdict"] == "PASS")
    print(f"fidelity: {n_pass}/{len(result['sleeves'])} sleeves PASS "
          f"-> {out}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
