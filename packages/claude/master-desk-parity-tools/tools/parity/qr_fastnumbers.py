"""qr_fastnumbers: the six-strategy reconstruction's principal Fast Numbers ledger inputs vs
desk/sleeves/quant_research/fastnumbers.py's per-session decision.

SOURCE: quant-research-critical@0be4c575 research/2026-10-08-six-strategy-reconstruction/source.zip.parts, extracted
(SIXAI_X): fastnumbers/results/coverage-corrected/numeric_sue_canonical_raw_error-events.csv.gz (run_reconstruction
main(): every executed event -- a cohort event its price_events() priced -- with its CDF percentile, cohort count,
session and Appendix weight) and ...-full-cohort-N.csv.gz (each session's whole signal cohort before that price
filter: event id, p, N).
PORT: fastnumbers.decide(None, session) / decide_events() -- the production path on the vendored event history:
the snapshot's stored SUE inputs, run_reconstruction.cdf_scores / actual_session / weights executed from the vendored
copy -- once per session of the native cohort.
Compared, per session:
  every executed event (by event id): its symbol, weight and percentile (1e-12);
  the session's N and its cohort (the full-cohort file's event ids = the port's event ids);
  every cohort event the source's price filter rejected (cohort minus executed): the port's percentile vs the cohort
  file's, and the port's weight vs the source's weights() run on the cohort file's own row (p, N);
  the account's net per symbol: the port's decide() weight, less its events the source left unpriced, vs the executed
  ledger's per-symbol sum (two releases of one issuer can share a session).
The rejected tails are counted (unpriced_in_source_tails), not diffs: the port weights them exactly as the source does
before its price filter and trades one only when the desk quotes it (the module's named divergence 2)."""
import json
import os

import numpy as np
import pandas as pd

from . import write_receipt

SIXAI_X = os.environ.get("SIXAI_X", "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/dl/"
                                    "sixai/x")
EVENTS = "fastnumbers/results/coverage-corrected/numeric_sue_canonical_raw_error-events.csv.gz"
COHORT = "fastnumbers/results/coverage-corrected/numeric_sue_canonical_raw_error-full-cohort-N.csv.gz"
LIMIT = int(os.environ.get("FASTNUMBERS_PARITY_SESSIONS", 0))
TOL = 1e-12


def run():
    import hashlib
    from desk.sleeves.quant_research import fastnumbers as F
    rr, _ = F.source()
    ev = pd.read_csv(os.path.join(SIXAI_X, EVENTS), low_memory=False,
                     usecols=["event_id", "symbol", "session_date", "session_N", "cdf_percentile", "weight"])
    co = pd.read_csv(os.path.join(SIXAI_X, COHORT), low_memory=False)
    co = rr.weights(co, F.SIGNAL)                      # the source's weights() on the cohort file's own p and N
    sessions = sorted(set(co.session_date))
    if LIMIT:
        rng = np.random.default_rng(7)
        sessions = sorted(str(s) for s in rng.choice(sessions, LIMIT, replace=False))
    by_ev = {d: g for d, g in ev.groupby("session_date")}
    by_co = {d: g for d, g in co.groupby("session_date")}
    st = {"sessions": 0, "events": 0, "weights_bad": 0, "p_bad": 0, "n_bad": 0, "cohort_bad": 0, "tails": 0,
          "rejected": 0, "rejected_bad": 0, "unpriced_in_source_tails": 0, "net_checks": 0, "net_bad": 0}
    diffs = []
    for d in sessions:
        F._MEMO.clear()
        w, n, p = F.decide(None, d)
        evs = F.decide_events(None, d)
        g, c = by_ev.get(d), by_co[d]
        executed = set(g.event_id) if g is not None else set()
        st["sessions"] += 1
        if n != int(c.session_N.iloc[0]):
            st["n_bad"] += 1
            diffs.append({"session": d, "N_port": n, "N_native": int(c.session_N.iloc[0])})
        if set(evs) != set(c.event_id):
            st["cohort_bad"] += 1
            diffs.append({"session": d, "cohort_only_port": sorted(set(evs) - set(c.event_id))[:5],
                          "cohort_only_native": sorted(set(c.event_id) - set(evs))[:5]})
        for r in (g.itertuples() if g is not None else ()):
            st["events"] += 1
            st["tails"] += bool(r.weight)
            sym, pp, ww = evs.get(r.event_id, (None, -1.0, 0.0))
            if abs(ww - r.weight) > TOL or sym != r.symbol:
                st["weights_bad"] += 1
                diffs.append({"session": d, "event": r.event_id, "w_port": ww, "w_native": r.weight})
            if abs(pp - r.cdf_percentile) > TOL:
                st["p_bad"] += 1
                diffs.append({"session": d, "event": r.event_id, "p_port": pp, "p_native": r.cdf_percentile})
        for r in c.itertuples():                       # the cohort events the source's price filter rejected
            if r.event_id in executed:
                continue
            st["rejected"] += 1
            st["unpriced_in_source_tails"] += bool(r.weight)
            sym, pp, ww = evs.get(r.event_id, (None, -1.0, None))
            if sym != r.symbol or abs(pp - r.cdf_percentile) > TOL or ww is None or abs(ww - r.weight) > TOL:
                st["rejected_bad"] += 1
                diffs.append({"session": d, "rejected_event": r.event_id, "p_port": pp, "p_native": r.cdf_percentile,
                              "w_port": ww, "w_source_weights": r.weight})
        unpriced = {}
        for eid, (sym, pp, ww) in evs.items():
            if eid not in executed:
                unpriced[sym] = unpriced.get(sym, 0.0) + ww
        native = g.groupby("symbol").weight.sum() if g is not None else pd.Series(dtype=float)
        for s_ in sorted(set(native.index) | {s for s, v in w.items() if v}):
            st["net_checks"] += 1                      # the account's net per symbol over the events the source priced
            port = w.get(s_, 0.0) - unpriced.get(s_, 0.0)
            nat = float(native.get(s_, 0.0))
            if abs(port - nat) > TOL:
                st["net_bad"] += 1
                diffs.append({"session": d, "symbol": s_, "net_port_priced": port, "net_native": nat})
        if st["sessions"] % 50 == 0:
            print(d, json.dumps(st), flush=True)
    cases = st["events"] + 2 * st["sessions"] + st["rejected"] + st["net_checks"]
    bad = st["weights_bad"] + st["p_bad"] + st["n_bad"] + st["cohort_bad"] + st["rejected_bad"] + st["net_bad"]
    out = {"family": "quant_research", "sleeves": [F.SID], "cases": cases, "identical": cases - bad, "n_diffs": bad,
           "detail": st, "diffs": diffs[:50],
           "source": {"archive": "quant-research-critical@0be4c57569e363d052bd23564cf0664697439927 research/"
                                 "2026-10-08-six-strategy-reconstruction/source.zip.parts",
                      "events_sha256": hashlib.sha256(open(os.path.join(SIXAI_X, EVENTS), "rb").read()).hexdigest(),
                      "cohort_sha256": hashlib.sha256(open(os.path.join(SIXAI_X, COHORT), "rb").read()).hexdigest()},
           "method": "per native session: fastnumbers.decide() / decide_events() on the vendored history vs the native "
                     "executed events (symbol, weight, percentile), the session's N and full signal cohort (event "
                     "ids), every cohort event the source's price filter rejected (percentile; weight vs the source's "
                     "weights() on the cohort row) and the account's net per symbol over the events the source priced",
           "named_divergence_counts": {
               "unpriced_in_source_tails": "cohort tails the source's price_events() rejected (no price in its "
                                           "daily panel / raw1Day extension): weighted identically here, traded "
                                           "only when the desk quotes them (divergence 2)"},
           "not_in_this_comparison": ["live Nasdaq events (divergence 1)", "execution and the close (2)",
                                      "whole-share shorts (3)", "NAV (4)", "post-snapshot SUE (5)"]}
    write_receipt("qr_fastnumbers", out)
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs")}), json.dumps(r["detail"]))
