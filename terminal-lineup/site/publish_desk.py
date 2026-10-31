#!/usr/bin/env python3
"""Publish the desk terminal surface inside the tools site root.

The desk page lives on the desk side (muse-desk-v3/terminal/: its
index.html plus the terminal_feed.json it fetches). The tools site is
served from this folder, so the shared navigation's Desk tab (last,
by the 2026-10-31 ruling) can only link truthfully to a copy served
from the same root. This producer makes that copy: both files are
copied byte for byte into site/desk/, and the copy is verified by
hash before this prints success. The desk side stays the source;
this folder is a publish copy, refreshed by refresh_hub.py.

Desk subject charts (cure 2026-10-31): the desk page was the one hub
page with no data.json and no chart. This producer now also builds
site/desk/data.json from the copied snapshot, carrying the subject
quantities the snapshot itself holds (the account readings, the open
positions aggregated from the per-strategy rows, and the capital
epoch the snapshot's evidence packet declares) plus the subject
charts record_surface.build_subject_chart builds from them. The
published index.html keeps the desk page's own content byte for byte
and gains only the shared chart wiring every other page carries
(shared.css, visual.css, shared.js, which loads the chart layer).
Both additions are rebuilt here on every publish, so they survive
republication; nothing is hand-edited into site/desk/.

Usage: python3 publish_desk.py
Exit 0 when both files are in place and hash-verified, the wiring
is in the published page, and data.json is written.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "muse-desk-v3" / "terminal"
FILES = ("index.html", "terminal_feed.json")

# The shared chart wiring, exactly as the authored pages carry it.
# Added to the published copy only; the desk source is untouched.
WIRING = ('<link rel="stylesheet" href="../shared.css">\n'
          '<link rel="stylesheet" href="../visual.css">\n'
          '<script src="../shared.js" defer></script>\n')


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) \
        else None


def aggregate_positions(feed):
    """Open positions from the snapshot, aggregated by symbol.

    The snapshot carries positions per strategy as {symbol, qty}
    rows (the desk page itself renders those). Quantities for the
    same symbol across strategies are summed and the holding
    strategies named. If no strategy row exists, account_positions
    rows are used when they carry the same two fields. No other
    position field (no market value, no unrealised profit or loss)
    exists in the snapshot, so none is carried or invented.
    """
    agg = {}
    for strat in feed.get("strategies") or []:
        for pos in strat.get("open_positions") or []:
            sym, qty = pos.get("symbol"), _num(pos.get("qty"))
            if not sym or qty is None:
                continue
            row = agg.setdefault(sym, {"symbol": sym, "qty": 0,
                                       "strategies": []})
            row["qty"] += qty
            name = strat.get("name")
            if name and name not in row["strategies"]:
                row["strategies"].append(name)
    if not agg:
        for pos in feed.get("account_positions") or []:
            sym, qty = pos.get("symbol"), _num(pos.get("qty"))
            if not sym or qty is None:
                continue
            row = agg.setdefault(sym, {"symbol": sym, "qty": 0,
                                       "strategies": []})
            row["qty"] += qty
    return sorted(agg.values(), key=lambda r: -abs(r["qty"]))


def build_data(feed):
    """The desk page's data.json, from its own snapshot only."""
    account = feed.get("account") or {}
    packet = feed.get("evidence_packet") or {}
    period = packet.get("period") or {}
    generated = feed.get("generated_at") or ""
    data = {
        "tool": "desk",
        "session": generated[:10],
        "published_at_utc": generated,
        "source": "desk snapshot terminal_feed.json, copied read-only "
                  "by publish_desk.py from muse-desk-v3/terminal/",
        "account": {k: account.get(k) for k in (
            "equity", "cash", "buying_power", "portfolio_value",
            "last_equity", "status")},
        "positions": aggregate_positions(feed),
        "positions_source": "strategies[].open_positions "
                            "(symbol, qty), aggregated by symbol",
        "epoch": {"starting_capital": packet.get("starting_capital"),
                  "start": period.get("start"),
                  "end": period.get("end")},
    }
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import record_surface
    data["subject_chart"] = record_surface.build_subject_chart(
        "desk", data)
    return data


def publish():
    dest = HERE / "desk"
    dest.mkdir(exist_ok=True)
    copied = []
    for name in FILES:
        src = SOURCE / name
        if not src.exists():
            print(f"FAIL: desk source missing: {src}")
            return 1
        out = dest / name
        shutil.copyfile(src, out)
        if _sha(src) != _sha(out):
            print(f"FAIL: desk copy does not match source: {name}")
            return 1
        copied.append(name)
    # Shared chart wiring on the published copy only, added after
    # the byte-for-byte copy above is hash-verified.
    page_path = dest / "index.html"
    page = page_path.read_text(encoding="utf-8")
    if "../shared.js" not in page:
        if "</head>" not in page:
            print("FAIL: desk page has no </head> to wire charts into")
            return 1
        page_path.write_text(page.replace(
            "</head>", WIRING + "</head>", 1), encoding="utf-8")
    feed = json.loads((dest / "terminal_feed.json").read_text(
        encoding="utf-8"))
    data = build_data(feed)
    (dest / "data.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    # Self-enrich tail (cure 2026-10-31, Wave 2): every other hub
    # page carries its record_surface block from enrich_all, but a
    # bare republication of the desk page must not strip it. The
    # enrich rebuilds the same subject charts from the same data
    # through the one builder, so the block and the charts agree.
    try:
        import record_surface as _rs
        if not _rs.enrich_file(dest / "data.json"):
            print("FAIL: desk data.json could not be enriched")
            return 1
    except Exception as exc:
        print(f"FAIL: desk self-enrich failed: {exc}")
        return 1
    print(f"desk published: site/desk/ ({', '.join(copied)}), "
          "hash-verified against muse-desk-v3/terminal/; "
          "chart wiring and data.json (subject charts) built from "
          "the copied snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(publish())
