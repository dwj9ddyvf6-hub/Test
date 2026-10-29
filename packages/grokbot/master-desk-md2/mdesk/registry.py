"""Single sleeve registry + unified catalog (every sleeve from every desk, with status and dedupe/merge map)."""
import json, os, collections
from .engines import ausar, lazarus, muse, ausar_genuine, kz_sweep, cci_corr
ROOT = "/workspace/desk2"

def load_all():
    a, ca = ausar.load(); l, cl = lazarus.load(); m, cm = muse.load()
    ca, replaced = ausar_genuine.apply(ca)
    for s in a:   # retired reimplementations: no new entries; kept loaded exit-only so any open sim lot is run off by its own exit rule
        if s.sid in replaced: s.exit_only = True
    k, ck = kz_sweep.load(); cc, ccc = cci_corr.load()
    native = a + l + k + cc
    return native, m, ca + cl + cm + ck + ccc

# cross-desk duplicates (same strategy, same instrument/universe, same rules) -> one running copy
MERGE = {   # catalog sid -> running sid
}

def catalog(write=True):
    native, m, cat = load_all()
    running = {s.sid for s in native} | {s.sid for s in m if s.status == "installed"}
    for r in cat:
        if r["status"] == "installed" and r["source"] not in ("ausar-r19", "ausar-genuine") and r["sid"] not in running: r["status"], r["reason"] = "blocked", r["reason"] or "failed to load"
    # Lazarus vs muse name-level overlaps are recorded, not merged: they read different producers (Lazarus: Tensor tracker
    # fires; muse: its own port of the same rule on its own bars) and size/exit differently -> genuinely distinct books.
    for r in cat:   # known vendored-sleeve defect observed on live inputs (isolated; alert raised each pass; not modified here)
        if r["sid"] == "iron_condor": r["reason"] = "runs, but muse-desk-v2's own iron_condor raised TypeError float(tuple) on the 2026-10-24 option chain - upstream defect, isolated by md2"
    by = collections.Counter((r["source"], r["status"]) for r in cat)
    summary = dict(total_rows=len(cat), installed=sum(1 for r in cat if r["status"] == "installed"),
                   by_source_status={f"{k[0]}:{k[1]}": v for k, v in sorted(by.items())})
    doc = dict(summary=summary, sleeves=cat)
    if write:
        os.makedirs(f"{ROOT}/catalog", exist_ok=True); json.dump(doc, open(f"{ROOT}/catalog/catalog.json", "w"), indent=1)
        with open(f"{ROOT}/catalog/CATALOG.md", "w") as f:
            f.write(f"# md2 unified sleeve catalog\n\n{json.dumps(summary, indent=1)}\n\n| sid | source | family | status | strategy | reason / merged into | origin |\n|---|---|---|---|---|---|---|\n")
            for r in cat:
                f.write(f"| {r['sid']} | {r['source']} | {r['family']} | {r['status']} | {str(r['strategy'])[:70].replace('|','/')} | {(r.get('merged_into') or r['reason'] or '')[:110].replace('|','/')} | {r['origin'][:80]} |\n")
    return doc
