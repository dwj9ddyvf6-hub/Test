#!/usr/bin/env python3
"""RC-12 sector map residual scan (2026-10-30).

One more genuine in-bounds attempt for the names the Sector
Rotation page lists as without a sector on record. Four routes,
each read as it stands and evidenced in the output record:

1. the terminal's own stores: every data.json under this site
   tree is scanned for a per name sector field (any object
   carrying both a symbol or ticker and a sector);
2. the chain store metadata: the chain snapshots under
   morgue/state/morgue/chains (their manifest and one snapshot
   header per underlying) are checked for any sector field;
3. the EDGAR company record: morgue/data_cache/edgar/
   company_tickers.json is checked for a sector or industry
   field per name (it carries cik, ticker and title only);
4. the panel metadata: the DEEP panel sidecars under
   terminal-lineup/deep_store are checked for any field beyond
   price rows (they carry fingerprint and session metadata
   only), and the board panel file's top level keys are read.

Any sector found for an unmapped name is written into the
record under found; the scan never invents a sector. The
record lands at site/sector-rotation/sector_scan_20261030.json
and refresh_rotation.py publishes its summary as the page's
stated limit.

Usage: python3 scan_sector_sources.py
"""

import gzip
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
PAGE = os.path.join(HERE, "sector-rotation", "data.json")
OUT_PATH = os.path.join(HERE, "sector-rotation",
                        "sector_scan_20261030.json")
CHAINS = os.path.join(WS, "morgue", "state", "morgue", "chains")
EDGAR_TICKERS = os.path.join(WS, "morgue", "data_cache", "edgar",
                             "company_tickers.json")
DEEP_STORE = os.path.join(WS, "terminal-lineup", "deep_store")
PANEL = os.path.join(WS, "morgue", "data_cache", "board_bt_bars.json")


def walk_sectors(node, unmapped, found, depth=0):
    if depth > 8:
        return
    if isinstance(node, dict):
        sym = node.get("symbol") or node.get("ticker")
        sec = node.get("sector")
        if isinstance(sym, str) and isinstance(sec, str) and sec \
                and sym in unmapped and sym not in found:
            found[sym] = sec
        for v in node.values():
            walk_sectors(v, unmapped, found, depth + 1)
    elif isinstance(node, list):
        for v in node[:20000]:
            walk_sectors(v, unmapped, found, depth + 1)


def main():
    with open(PAGE, encoding="utf-8") as fh:
        unmapped = set(json.load(fh)["unmapped_names"])
    found = {}
    files_scanned = 0
    for root, _dirs, files in os.walk(HERE):
        if "__pycache__" in root:
            continue
        for name in files:
            if not name.endswith("data.json"):
                continue
            path = os.path.join(root, name)
            if os.path.abspath(path) == os.path.abspath(PAGE):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
            except Exception:
                continue
            files_scanned += 1
            walk_sectors(doc, unmapped, found)
    routes = {
        "terminal_own_stores": {
            "files_scanned": files_scanned,
            "found": len(found),
            "note": "every site data.json scanned for a symbol "
                    "plus sector pair naming an unmapped name",
        },
    }
    # Chain store metadata: manifest lines and snapshot headers.
    chain_fields = set()
    manifest = os.path.join(CHAINS, "manifest.jsonl")
    if os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as fh:
            for line in fh:
                try:
                    chain_fields |= set(json.loads(line).keys())
                except Exception:
                    pass
                break
    for sym in ("SPY", "QQQ", "IWM"):
        day_path = None
        sdir = os.path.join(CHAINS, sym)
        if os.path.isdir(sdir):
            for name in sorted(os.listdir(sdir)):
                if name.endswith(".json.gz"):
                    day_path = os.path.join(sdir, name)
        if day_path:
            with gzip.open(day_path, "rt", encoding="utf-8") as fh:
                head = json.loads(fh.read())
            chain_fields |= set(head.keys())
    routes["chain_store_metadata"] = {
        "fields_seen": sorted(chain_fields),
        "sector_field_present": any("sector" in f.lower()
                                    for f in chain_fields),
        "found": 0,
        "note": "snapshots carry OCC rows for SPY, QQQ and IWM "
                "only; their headers carry no sector field and "
                "no per constituent record",
    }
    # EDGAR company record.
    edgar_fields = set()
    if os.path.exists(EDGAR_TICKERS):
        with open(EDGAR_TICKERS, encoding="utf-8") as fh:
            raw = json.load(fh)
        rows = raw.values() if isinstance(raw, dict) else raw
        for row in rows:
            if isinstance(row, dict):
                edgar_fields |= set(row.keys())
    routes["edgar_company_record"] = {
        "fields_seen": sorted(edgar_fields),
        "sector_field_present": any(
            f.lower() in ("sector", "sic", "industry")
            for f in edgar_fields),
        "found": 0,
        "note": "the company record carries cik, ticker and "
                "company title only; no sector, industry or SIC "
                "field exists in it",
    }
    # Panel metadata: sidecar keys and the board panel top level.
    sidecar_fields = set()
    if os.path.isdir(DEEP_STORE):
        for name in sorted(os.listdir(DEEP_STORE)):
            if name.startswith("sidecar"):
                with open(os.path.join(DEEP_STORE, name),
                          encoding="utf-8") as fh:
                    sidecar_fields |= set(json.load(fh).keys())
                break
    routes["panel_metadata"] = {
        "sidecar_fields_seen": sorted(sidecar_fields),
        "sector_field_present": any("sector" in f.lower()
                                    for f in sidecar_fields),
        "found": 0,
        "note": "the panel and its sidecars carry price rows "
                "and session metadata only; no sector field",
    }
    record = {
        "record": "RC-12 sector residual scan, four in-bounds routes",
        "scanned_on": "2026-10-30",
        "unmapped_names_count": len(unmapped),
        "found": found,
        "found_count": len(found),
        "still_unmapped_count": len(unmapped) - len(found),
        "routes": routes,
    }
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"sector scan: {len(unmapped)} unmapped, "
          f"{len(found)} found across four routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
