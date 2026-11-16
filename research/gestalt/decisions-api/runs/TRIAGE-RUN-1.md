# NON-FIRING TRIAGE, RUN 1 (Sat 2026-11-14)

Program: Execute Both Brainstorms (W3; Decisions brainstorm item 2,
top-three A). Population: the board's 148 ARMED-PROVEN sleeves (fed
and evaluating; quiet on the most recent completed session, Fri
2026-11-13). Method: numbers-only packs (board trigger shape,
sessions live, lifetime orders/fills/own closes, cadence) posed to
the frozen nonfiring-triage-bank v1 through the GA harness (Luna 6),
3 chunked batched requests, prompt_cache_key nonfiring-triage-bank-v1.
Spend: $0.00529 (budget file: day total 31 requests, $0.008356 after
this run). Labels: runs/triage_labels.json; ledger runs/triage_ledger.jsonl.
SHADOW-ONLY: no gate loosened, no state changed, on any label.

## Results (148 classified)
- insufficient_evidence: 93
- never_approached: 47
- quiet_by_design: 4 (aster_pead_long_b, coffin_rebuilt,
  momentum_rotation, s_q07w_s52_ml_ins2_mom6_wlow — matches their
  monthly/rotation designs)
- data_shaped: 4 (s_mn_d_green_band, s_mn_w_cyan_breadth,
  s_mn_w_cyan_vix, s_mn_w_green_smh — breadth/VIX/SMH-shaped inputs)
- near_miss: 0

## The honest headline
The dominant class is insufficient_evidence (93 of 148): the packs do
not carry gate-distance or eval-reason data, so no judge, typed or
human, can distinguish a strict gate from an absent pattern for most
quiet sleeves. That is an instrumentation finding, not a modeling
failure, and it drafts the program's first triage hypothesis below.

## Drafted calibration hypotheses (for the calibration owners at B5;
none landed by this run)
- H-TRIAGE-1 (instrumentation, 93 sleeves): before any strictness
  judgment, each armed sleeve's evaluation must record its gate
  distance (the binding condition and its measured margin) per eval.
  Falsifier: with gate-distance logging live for 5 sessions, the
  insufficient_evidence share of a re-run must fall below 25%, or
  the packs' missing field is something else and gets named.
- H-TRIAGE-2 (never_approached, 47): replay-count each trigger over
  the trailing 60 sessions. Sleeves at >=1 qualifying day/week in
  replay but 0 live approaches point at the eval path, not the gate;
  sleeves below that are strictness-round candidates under the
  standing falsifier discipline (old/new threshold, replay counts,
  forward falsifier, rollback line).
- H-TRIAGE-3 (data_shaped, 4): name each sleeve's coarse field and
  its producer; fixture-drive with shaped data before any gate
  judgment (the F4 key-normalization cure is the shape of this fix).
- quiet_by_design (4): no action; re-check at each sleeve's cadence
  horizon (coffin_rebuilt's first signal is the 2026-11-30 month-end).
Cadence registered: nonfiring-triage-nightly (weekdays), whose packs
gain the gate-distance fields as H-TRIAGE-1 lands.
STATUS: GREEN for run 1 as scoped. EVIDENCE: runs/triage_ledger.jsonl,
runs/triage_labels.json, tools/build_triage.py, tools/run_triage.py.
