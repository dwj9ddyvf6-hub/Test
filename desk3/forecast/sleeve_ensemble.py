"""PORT-ADAPT (2026-10-27, ensemble port): Sleeve ensemble report tool,
vendored from Femto-lean `tools/sleeve_ensemble.py` (branch factory-p3,
sha256 9a8d80dde58ecc65d934ce96b5ef8b4c8cfdfe44a7d1f9b8549dc72c02719f38
in the program MANIFEST), adapted to muse-desk-v3:

  - imports `desk3.forecast.ensemble` instead of `desk.forecast.ensemble`;
  - the source's `--ref` git mode is dropped (muse-desk-v3 has no
    desk-state branch; its state lives on disk under `state/`);
  - the "record is short" page section is worded from the report's own
    low-confidence flags instead of asserting shortness unconditionally
    (the source page was written for one known 7-session record);
  - a `--v3-state` probe mode reads muse-desk-v3's actual forward record
    (state/capital_epoch.json + the dispatcher journal's `fill` events,
    epoch-scoped exactly as desk3/reconcile.py scopes them) and reports
    honestly whether that record can feed the ensemble. muse-desk-v3
    keeps NO per-sleeve equity curves (no books.json) and no segmented
    ledger, so the probe's verdict names the missing inputs instead of
    fabricating curves from fills.

Read-only and advisory: no sleeve runs, no backtest, no decision, size
or order changes. Writes only <out>.json and <out>.md.

  python3 -m desk3.forecast.sleeve_ensemble --root <dir holding state/> --out <path>
  python3 -m desk3.forecast.sleeve_ensemble --v3-state <muse-desk-v3 state dir> --out <path>
"""
import argparse
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from desk3.forecast import VERSION as FORECAST_VERSION  # noqa: E402
from desk3.forecast import ensemble as EN  # noqa: E402

ET = ZoneInfo("America/New_York")


class Source:
    def __init__(self, root=None):
        self.root = root

    def read(self, path):
        with open(os.path.join(self.root, path), "rb") as f:
            return f.read()


def load(src):
    """Femto-format record: state/books.json + state/ledger/manifest.json,
    every segment sha256-checked against the manifest; fails closed on a
    mismatch (source behavior, unchanged)."""
    books = json.loads(src.read("state/books.json"))
    man = json.loads(src.read("state/ledger/manifest.json"))
    fills, receipt = [], {"segments": 0, "open_rows": 0}
    blobs = []
    for s in man.get("segments") or ():
        raw = gzip.decompress(src.read("state/ledger/" + s["name"]))
        if hashlib.sha256(raw).hexdigest() != s["sha256"]:
            raise SystemExit(f"ledger segment {s['name']} does not match its manifest sha256")
        blobs.append(raw)
        receipt["segments"] += 1
    op = man.get("open") or {}
    raw = src.read("state/ledger/" + op.get("name", "open.jsonl"))
    if op.get("sha256") and hashlib.sha256(raw).hexdigest() != op["sha256"]:
        raise SystemExit("ledger open.jsonl does not match its manifest sha256")
    blobs.append(raw)
    for raw in blobs:
        for line in raw.splitlines():
            if b'"book_fill"' not in line:
                continue
            r = json.loads(line)
            if r.get("kind") == "book_fill":
                fills.append({k: r.get(k) for k in ("sleeve", "inst", "side", "qty", "at")})
    receipt["book_fills"] = len(fills)
    receipt["manifest_sha256"] = hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest()
    return books, fills, receipt


def _evidence_packet(period_start, period_end, starting_capital,
                     engine_version, trade_count, trade_count_scope,
                     self_check, failures, benchmarks=None,
                     period_basis=None):
    """EVIDENCE-PACKET-20261031: the packet that must travel with
    every published number (period, starting capital, engine
    version, trade count, self-check flags; failures visible even
    when they fail). Fields the record does not hold are None and
    named in failures, never filled with an invented figure. No
    number is computed here; the packet only joins material the
    report already produced."""
    return {"period": {"start": period_start, "end": period_end,
                       "basis": period_basis},
            "starting_capital": starting_capital,
            "benchmarks": list(benchmarks or []),
            "engine_version": engine_version,
            "trade_count": trade_count,
            "trade_count_scope": trade_count_scope,
            "self_check": self_check,
            "failures": list(failures)}


def _packet_lines(pkt):
    """Render one packet as plain report lines (failures included)."""
    L = []
    a = L.append
    a("## Evidence packet")
    a("")
    a(f"- Period: {pkt['period']['start']} → {pkt['period']['end']} "
      f"({pkt['period']['basis']})")
    a(f"- Starting capital: {pkt['starting_capital']}")
    a(f"- Engine version: {pkt['engine_version']}")
    a(f"- Trade count: {pkt['trade_count']} ({pkt['trade_count_scope']})")
    a(f"- Self-check: {json.dumps(pkt['self_check'], sort_keys=True, default=str)}")
    if pkt["failures"]:
        a("- Failures (visible, not hidden):")
        for f_ in pkt["failures"]:
            a(f"  - {f_}")
    else:
        a("- Failures: none")
    a("")
    return L


def _f(x, n=3, pct=False):
    if x is None:
        return "–"
    return f"{100 * x:.{n}f}" if pct else f"{x:.{n}f}"


def render(rep, receipt, source_label):
    c, b, p = rep["counts"], rep["bets"], rep["portfolio"]
    rows = rep["sleeves"]
    L = []
    a = L.append
    a(f"# Sleeve ensemble: owner decision page ({rep['calendar']['last'] or 'n/a'})")
    a("")
    a("Status: **proposals only.** Nothing here changes a sleeve's decisions, sizes or orders. Built by "
      "`desk3.forecast.sleeve_ensemble` (desk3/forecast/ensemble.py) from the existing forward record only: "
      f"{source_label} books.json and {receipt['segments']} ledger segments + open.jsonl "
      f"({receipt['book_fills']} book_fill rows, each segment sha256-checked against the manifest). No backtest.")
    a("")
    pkt = rep.get("evidence_packet")
    if pkt:
        L.extend(_packet_lines(pkt))
    short = all(r["low_confidence"] for r in rows) if rows else True
    if short:
        a("## Read this first: the record is short")
        a("")
        a(f"- Calendar: {rep['calendar']['sessions']} NYSE session returns, {rep['calendar']['first']} → "
          f"{rep['calendar']['last']}. A 24/7 book's weekend move is folded into the next session.")
        a(f"- **Every sleeve has fewer than {rep['params']['min_record']} forward sessions**, the FACTORY §9 bar. So every "
          "final label is `unproven`; the labels below are *provisional* and every row is low-confidence.")
    else:
        a("## Read this first: confidence")
        a("")
        a(f"- Calendar: {rep['calendar']['sessions']} NYSE session returns, {rep['calendar']['first']} → "
          f"{rep['calendar']['last']}. A 24/7 book's weekend move is folded into the next session.")
        a(f"- Rows whose sleeve has fewer than {rep['params']['min_record']} forward sessions are marked "
          "`unproven` / low-confidence; only the rest carry a final label.")
    a(f"- Correlations use pairs with ≥ {rep['params']['min_overlap']} overlapping sessions (exploratory; the "
      f"confident gate is {rep['params']['min_record']}). With T sessions a sample correlation matrix has rank ≤ T−1, "
      f"so the raw sample matrix carries at most {b['record_bound']} independent directions; the shrunk matrix's "
      "participation ratio is larger only because the shrinkage target is the identity. Read the effective-bet "
      "numbers as ranges, not counts.")
    a(f"- Ledoit-Wolf shrinkage intensity: {_f(rep['shrinkage']['lw_delta_sleeves'])} on sleeves, "
      f"{_f(rep['shrinkage']['lw_delta_clusters'])} on clusters (1 = all identity).")
    a("")
    a("## Headline")
    a("")
    a("| | |\n|---|---|")
    a(f"| Books in the record | {c['books']} |")
    a(f"| Sleeves with a record (fills, ≥ 2 sessions, non-flat) | {c['with_record']} |")
    a(f"| Identical-fill groups (hashed fill sequences) | {c['identical_fill_groups']} groups, "
      f"{c['identical_fill_sleeves']} sleeves |")
    a(f"| Clusters after merging identical fills and ρ ≥ {rep['params']['twin_rho']} twins (one bet each) | "
      f"{c['clusters']} ({c['multi_member_clusters']} with ≥ 2 members) |")
    a(f"| Exact-copy fill groups (raw quantities) | {c['exact_fill_groups']} groups, {c['exact_fill_sleeves']} sleeves |")
    qq = rep["qqq_twins"]
    a(f"| Long-QQQ exposure twins (ρ ≥ 0.95 to one of {len(qq['references'])} QQQ-only books, incl. them) | "
      f"{len(qq['twins'])} |")
    a(f"| Average-linkage clusters cut at ρ = 0.6 | {b['linkage_clusters_rho_0_6']} |")
    a(f"| Effective bets: participation ratio of the shrunk cluster correlation | "
      f"{_f(b['participation_ratio'], 1)} |")
    a(f"| Effective bets without de-duplication (sleeve level) | {_f(b['participation_ratio_sleeves_no_dedup'], 1)} |")
    a(f"| Breadth (Σq)²/qᵀCq over clusters with q > 0 | {_f(b.get('breadth_q'), 1)} |")
    a(f"| Equal-risk desk portfolio: Sharpe (annualised) / max drawdown | {_f(p['sr_ann'], 2)} / "
      f"{_f(p['mdd_pct'], 2)}% |")
    a("")
    a("On a short record, ρ ≥ 0.95 to a long-QQQ book cannot separate a QQQ copy from any long equity-beta book, so the "
      "QQQ-twin count is an upper bound. Clusters below use complete linkage (every pair ≥ 0.95), which is stricter.")
    a("")
    a("## Top redundant clusters")
    a("")
    a("Each cluster is one bet. Proposal: let one representative (highest shrunk forward quality) carry the bet and "
      "review whether the copies add anything.")
    a("")
    a("| # | size | why | min ρ | representative | members (first 8) |\n|---|---|---|---|---|---|")
    for cl in [x for x in rep["clusters"] if x["size"] > 1][:15]:
        mem = ", ".join(cl["members"][:8]) + (f" … (+{cl['size'] - 8})" if cl["size"] > 8 else "")
        a(f"| {cl['id']} | {cl['size']} | {cl['why']} | {_f(cl['min_rho'], 3)} | {cl['representative']} | {mem} |")
    a("")
    a("## Sleeves that hurt the portfolio (largest negative leave-one-out ΔSharpe)")
    a("")
    a("ΔSR = annualised Sharpe of the equal-risk desk with the sleeve − without it; ΔDD (basis points) > 0 means the "
      "sleeve deepens the desk's max drawdown. CI: bootstrap over days. ρ desk = correlation with the desk without "
      "the sleeve.")
    a("")
    hdr = ("| sleeve | sessions | P&L $ | ΔSR ann. [95% CI] | ΔDD bp | DSR | ρ desk | max |ρ| | cluster | label (prov.) |\n"
           "|---|---|---|---|---|---|---|---|---|---|")
    k = 252 ** 0.5

    def sc(x, m):
        return None if x is None else x * m

    def line(r):
        ci = r["mc_sr_ci"]
        return (f"| {r['sleeve']} | {r['sessions_alive']} | {r['pnl_usd']:,.0f} | {_f(sc(r['mc_sr'], k), 3)} "
                f"[{_f(sc(ci[0], k), 3)}, {_f(sc(ci[1], k), 3)}] | {_f(sc(r['mc_dd'], 1e4), 2)} | {_f(r['dsr'], 2)} | "
                f"{_f(r['rho_desk'], 2)} | {_f(r['max_abs_rho'], 2)} | {r['cluster']} ({r['cluster_size']}) | "
                f"{r['provisional_label']} |")
    drags = sorted((r for r in rows if r["mc_sr"] is not None), key=lambda r: r["mc_sr"])[:15]
    a(hdr)
    for r in drags:
        a(line(r))
    a("")
    a("## Sleeves that diversify it (positive ΔSharpe, ρ to the rest of the desk < 0.5)")
    a("")
    divs = sorted((r for r in rows if r["mc_sr"] is not None and r["mc_sr"] > 0
                   and r["rho_desk"] is not None and r["rho_desk"] < rep["params"]["diversifier_rho"]),
                  key=lambda r: -r["mc_sr"])[:15]
    a(hdr)
    for r in divs:
        a(line(r))
    a("")
    a("## Allocation proposal (independence weights w ∝ C⁻¹q over clusters)")
    a("")
    a("q = the empirical-Bayes shrunk forward Sharpe (the evidence module's formula), C = the Ledoit-Wolf shrunk "
      "correlation of the cluster series. Weights are clipped at 0 and sum to 1; the band is the 5–95% range over a "
      f"day bootstrap. Rows under {rep['params']['min_record']} sessions are low-confidence. **Proposal only.**")
    a("")
    a("| cluster | representative | size | q | w % | band % |\n|---|---|---|---|---|---|")
    top = sorted((x for x in rep["clusters"] if (x["weight"] or 0) > 0), key=lambda x: -x["weight"])[:25]
    for x in top:
        a(f"| {x['id']} | {x['representative']} | {x['size']} | {_f(x['q'], 3)} | {_f(x['weight'], 2, True)} | "
          f"{_f(x['weight_band'][0], 1, True)}–{_f(x['weight_band'][1], 1, True)} |")
    a(f"\n{sum(1 for x in rep['clusters'] if (x['weight'] or 0) > 0)} of {len(rep['clusters'])} clusters receive "
      "a positive weight.")
    a("")
    a("## Proposals for the owner")
    a("")
    a("1. *Proposal:* treat each redundant cluster above as one bet when reading the desk's breadth, and consider "
      "keeping its representative as the bet's carrier; the copies stay running until you decide.")
    a("2. *Proposal:* put the drag list on watch, not off: no drag's CI is based on ≥ 20 sessions unless its row "
      "carries a final (non-provisional) label. Re-run this report when the record reaches 20 sessions "
      "(FACTORY §9 gate) before any sleeve decision.")
    a("3. *Proposal:* the diversifiers are the cheapest source of breadth; they are candidates for more attention "
      "in the Execution Lab, never for a size change without your decision.")
    a("4. *Proposal:* use the independence weights only as a reading of where independent forward quality sits today; "
      "the bands are wide.")
    a("")
    a("## Method and gaps")
    a("")
    a("- Daily P&L: last book mark per ET date, carried to each NYSE session; alive from first to last mark. "
      "Each sleeve is scaled to 1% daily risk (σ floored at 1 bp) for the equal-risk portfolio; the drawdown is on the "
      "additive cumulative path.")
    a("- Identical fills: ledger book_fill rows summed per (ET date, instrument, side), quantity divided by the "
      "sleeve's largest such sum, sha256 of the sequence. Books' n_fills does not equal the ledger's book_fill count "
      "for every sleeve (books carry migrations and resets); the hash uses the ledger.")
    a("- PSR/DSR: desk3/forecast/evidence.psr and expected_max_sr over the sleeves with a record.")
    a("- Not done: any wiring into the desk. This tool is advisory report generation only.")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- v3 record probe
def probe_v3_state(state_dir):
    """Read muse-desk-v3's actual forward record (read-only) and decide
    whether it can feed the ensemble. Epoch scoping follows
    desk3/reconcile.py exactly: only fills with a parseable ts at or
    after capital_epoch.epoch_start_utc count; a fill with no (or an
    unparseable) ts is pre-epoch and excluded."""
    epoch_path = os.path.join(state_dir, "capital_epoch.json")
    epoch = json.loads(open(epoch_path).read()) if os.path.exists(epoch_path) else {}
    epoch_start = epoch.get("epoch_start_utc")
    books_present = os.path.exists(os.path.join(state_dir, "books.json"))
    ledger_manifest_present = os.path.exists(os.path.join(state_dir, "ledger", "manifest.json"))
    fills, pre_epoch, unparseable = [], 0, 0
    for name in ("dispatcher.jsonl.1", "dispatcher.jsonl"):
        path = os.path.join(state_dir, name)
        if not os.path.exists(path):
            continue
        for line in open(path, errors="ignore"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("event") != "fill":
                continue
            ts = r.get("ts")
            if epoch_start:
                if not ts:
                    unparseable += 1
                    continue
                if ts < epoch_start:      # ISO-8601 UTC strings compare chronologically
                    pre_epoch += 1
                    continue
            fills.append(r)
    sessions = sorted({datetime.fromisoformat(f["ts"]).astimezone(ET).date().isoformat()
                       for f in fills if f.get("ts")})
    sleeves = sorted({f.get("sleeve") for f in fills if f.get("sleeve")})
    missing = []
    if not books_present:
        missing.append("per-sleeve equity curves (state/books.json): muse-desk-v3 keeps no book "
                       "documents, so there is no daily per-sleeve P&L series to correlate")
    if not ledger_manifest_present:
        missing.append("segmented ledger (state/ledger/manifest.json + book_fill rows): fills exist "
                       "only as dispatcher journal `fill` events")
    if len(sessions) < 2:
        missing.append(f"session count: {len(sessions)} session(s) with fills in the current capital "
                       "epoch; the ensemble needs >= 2 sessions per sleeve for even one return, and "
                       f"{EN.MIN_RECORD} before any label is more than provisional")
    verdict = "CANNOT_FEED_HONESTLY" if missing else "FEEDABLE"
    start_equity = epoch.get("start_equity")
    packet = _evidence_packet(
        epoch_start, sessions[-1] if sessions else None,
        float(start_equity) if isinstance(start_equity, (int, float))
        else None,
        FORECAST_VERSION, len(fills), "fills_in_epoch (dispatcher fill events)",
        {"books_json_present": books_present,
         "ledger_manifest_present": ledger_manifest_present,
         "sessions_counted": len(sessions),
         "min_record_for_nonprovisional": EN.MIN_RECORD,
         "verdict": verdict},
        list(missing) if missing else [],
        benchmarks=epoch.get("benchmarks"),
        period_basis="capital_epoch_start_to_last_session_with_fills")
    return {"mode": "v3-state-probe", "verdict": verdict,
            "engine_version": FORECAST_VERSION,
            "evidence_packet": packet,
            "account": epoch.get("account"), "epoch_start_utc": epoch_start,
            "books_json_present": books_present,
            "ledger_manifest_present": ledger_manifest_present,
            "fills_in_epoch": len(fills), "fills_pre_epoch_excluded": pre_epoch,
            "fills_no_ts_excluded": unparseable,
            "sessions_with_fills": sessions, "sessions_counted": len(sessions),
            "sleeves_with_fills": sleeves, "sleeves_counted": len(sleeves),
            "min_record_for_nonprovisional": EN.MIN_RECORD,
            "missing_inputs": missing}


def render_probe(probe):
    L = []
    a = L.append
    a("# Sleeve ensemble run over the muse-desk-v3 forward record (2026-10-27)")
    a("")
    a(f"Verdict: **{probe['verdict']}**. The ensemble was NOT run over this record, because "
      "running it would require fabricating the inputs it reads. This page is the run's "
      "evidence: what the record actually holds, counted read-only from the final state.")
    a("")
    pkt = probe.get("evidence_packet")
    if pkt:
        L.extend(_packet_lines(pkt))
    a("## The record, counted")
    a("")
    a(f"- Capital epoch: {probe['epoch_start_utc']} (account {probe['account']}, per "
      "state/capital_epoch.json). Fills before the epoch belong to the prior account and are "
      "excluded, exactly as desk3/reconcile.py excludes them.")
    a(f"- Sessions counted (ET dates with in-epoch fills): **{probe['sessions_counted']}** "
      f"({', '.join(probe['sessions_with_fills']) or 'none'}).")
    a(f"- In-epoch fills: {probe['fills_in_epoch']}, across {probe['sleeves_counted']} sleeves "
      f"({', '.join(probe['sleeves_with_fills'])}).")
    a(f"- Excluded: {probe['fills_pre_epoch_excluded']} pre-epoch fills, "
      f"{probe['fills_no_ts_excluded']} fills with no timestamp.")
    a(f"- state/books.json present: {probe['books_json_present']}; segmented ledger manifest "
      f"present: {probe['ledger_manifest_present']}.")
    a("")
    a("## Why it cannot feed honestly")
    a("")
    for m in probe["missing_inputs"]:
        a(f"- {m}")
    a("")
    a("## What stands instead")
    a("")
    a("- The tool itself is landed and fixture-proven: `desk3/forecast/ensemble.py` + "
      "`desk3/forecast/sleeve_ensemble.py` + `desk3/forecast/evidence.py`, with gate-wired "
      "blockers in tests/test_sleeve_ensemble_20261027_blockers.py (identical-fill twins merge "
      "into one bet, leave-one-out matches the hand calculation, the tool fails closed on a "
      "corrupt ledger segment and writes only its report).")
    a(f"- Every label the ensemble would emit on a record this short is provisional by its own "
      f"rule (FACTORY §9: {probe['min_record_for_nonprovisional']} forward sessions). On this "
      "record there is not yet one return per sleeve, so there are no labels at all, provisional "
      "or otherwise.")
    a("- Named gap (OPEN): muse-desk-v3 has no per-sleeve daily equity/P&L record. Until the desk "
      "keeps one (a books.json-style curve per sleeve, marked daily), no ensemble, correlation, "
      "or leave-one-out reading of the v3 forward record is possible from any tool.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root")
    ap.add_argument("--v3-state")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-overlap", type=int, default=EN.MIN_OVERLAP)
    ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args(argv)
    if bool(a.root) == bool(a.v3_state):
        ap.error("exactly one of --root or --v3-state is required")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.v3_state:
        probe = probe_v3_state(a.v3_state)
        with open(a.out + ".json", "w") as f:
            json.dump(probe, f, indent=1, sort_keys=True)
        with open(a.out + ".md", "w") as f:
            f.write(render_probe(probe))
        print(json.dumps({"verdict": probe["verdict"], "sessions_counted": probe["sessions_counted"],
                          "fills_in_epoch": probe["fills_in_epoch"],
                          "sleeves_counted": probe["sleeves_counted"]}, indent=1))
        return 0
    src = Source(root=a.root)
    books, fills, receipt = load(src)
    rep = EN.build(books, fills, min_overlap=a.min_overlap, n_boot=a.boot)
    rep["source"] = {"root": a.root, **receipt}
    # EVIDENCE-PACKET-20261031: the report's numbers ship with their
    # packet. Starting capital is per-dashboard material: a single
    # figure only when every book in the record agrees on it,
    # otherwise None with the disagreement named (the teardown
    # refuted a blanket per-run capital claim in exactly this way).
    capitals = sorted({float(b.get("capital"))
                       for b in books.values()
                       if isinstance(b.get("capital"), (int, float))})
    one_capital = capitals[0] if len(capitals) == 1 else None
    packet_failures = []
    if one_capital is None:
        packet_failures.append(
            f"starting_capital_varies_across_books:{capitals}")
    if rep.get("fill_pnl_conflicts"):
        packet_failures.append(
            f"fill_pnl_conflicts:{len(rep['fill_pnl_conflicts'])}")
    rep["evidence_packet"] = _evidence_packet(
        rep["calendar"]["first"], rep["calendar"]["last"], one_capital,
        rep.get("version"), receipt.get("book_fills"),
        "ledger_book_fill_rows",
        {"ledger_segments_sha256_checked": receipt.get("segments", 0),
         "ledger_manifest_sha256_present": bool(
             receipt.get("manifest_sha256")),
         "book_fill_rows": receipt.get("book_fills"),
         "all_sleeves_low_confidence": all(
             r["low_confidence"] for r in rep["sleeves"])
         if rep["sleeves"] else True},
        packet_failures,
        period_basis="record_calendar_first_to_last_session")
    rep["engine_version"] = rep.get("version")
    with open(a.out + ".json", "w") as f:
        json.dump(rep, f, indent=1, sort_keys=True)
    with open(a.out + ".md", "w") as f:
        f.write(render(rep, receipt, "local"))
    print(json.dumps({"counts": rep["counts"], "bets": rep["bets"], "portfolio": rep["portfolio"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
