"""The forward-lab scan producer: Midna's scanForward (desk/sleeves/midna/forward_scan.py) over the daily panel, with the
Midna engine executed by desk/feedlib/midna_forward_runner.mjs.

The source scanned once per completed session — the first desk pass with a fresh panel whose session it had not
scanned (forward.scannedAsOf; a blocked or failed scan was retried on the next pass). Here the scan runs in the
midna_tensor family job `midna_forward_scan` (its own process, after the close and before the open, every 15 minutes
until the fresh panel's session is scanned) and is kept in cache/midna/forward_scan.json (per asOf, scan version 3);
the feed only reads that file, so the Node engine never runs inside the pass loop. A blocked scan is not kept
(retried by the next job run)."""
import json
import os
import subprocess

from ..sleeves.midna import forward_scan as F
from ..sleeves.midna.context import panel_stale
from ..util import read_json, write_json_atomic

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "midna_forward_runner.mjs")
SCAN_VERSION = 3
_MEMO = {}


class ScanError(RuntimeError):
    pass


def run_engine(names, timeout=900):
    """the runner over [{sym, day, o, h, l, c, v}] -> {sym: {n, d, w, wlast}}."""
    if not names:
        return {}
    try:
        p = subprocess.run(["node", "--max-old-space-size=1024", RUNNER], input=json.dumps({"names": names}),
                           capture_output=True, text=True, timeout=timeout,
                           env=dict(os.environ, UV_THREADPOOL_SIZE="1", MALLOC_ARENA_MAX="2"))
    except FileNotFoundError as e:
        raise ScanError("node is not available") from e
    except subprocess.TimeoutExpired as e:
        raise ScanError("engine runner timed out") from e
    if p.returncode != 0:
        raise ScanError("engine runner failed: " + p.stderr[-600:])
    return json.loads(p.stdout)["out"]


def blocked_before_engine(panel):
    """scan_forward's blocks that do not depend on the engine's output (the session index, the probe's open and low,
    SPY's valid bars reaching asOf), checked before the engine runs: a blocked session is retried every 15 minutes
    and each engine run took 3-17 minutes of a job slot (2026-10-16). None when the engine must decide."""
    as_of, clock = panel["asOf"], panel["clock"]
    if (clock.index(as_of) if as_of in clock else -1) < 80:
        return "Not enough sessions."
    sample = panel["series"].get(panel["universe"][0] if panel["universe"] else "SPY") or []
    probe = next((p for p in sample if p["close"] > 0), None)
    if not probe or not probe.get("open") or not probe.get("low"):
        return "Open and low are missing."
    spy = F.valid_bars(clock, panel["series"].get("SPY"))
    if len(spy) < 60 or spy[-1]["day"] != as_of:
        return "SPY bars are short."
    return None


def scan(panel):
    why = blocked_before_engine(panel)
    if why:
        return {"hits": [], "blocked": True, "cyan": 0, "green": 0, "why": why}
    engine_out = run_engine(F.runner_input(panel))
    res = F.scan_forward(panel, engine_out)
    res.pop("rows", None)
    return res


def cached_scan(root, panel):
    """{asOf, blocked, hits, cyan, green} for the panel's session, scanned once (job side: runs the scan when the
    session has none yet)."""
    if not panel:
        return None
    rec = stored_scan(root, panel["asOf"])
    if rec is not None:
        return rec
    res = scan(panel)
    rec = dict(res, asOf=panel["asOf"], version=SCAN_VERSION)
    if not res.get("blocked"):
        path = os.path.join(root, "cache", "midna", "forward_scan.json")
        doc = read_json(path, {}) or {}
        key = (root, panel["asOf"], SCAN_VERSION)
        scans = dict(doc.get("scans") or {})
        scans[panel["asOf"]] = rec
        for old in sorted(scans)[:-30]:
            scans.pop(old)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_json_atomic(path, {"scans": scans})
        _MEMO[key] = rec
    return rec


def stored_scan(root, as_of):
    key = (root, as_of, SCAN_VERSION)
    if key in _MEMO:
        return _MEMO[key]
    doc = read_json(os.path.join(root, "cache", "midna", "forward_scan.json"), {}) or {}
    rec = (doc.get("scans") or {}).get(as_of)
    if rec and rec.get("version") == SCAN_VERSION:
        _MEMO[key] = rec
        return rec
    return None


def job(engine):
    """the family job: scan the fresh panel's session once (Node runs here, in the job's process)."""
    from . import midna_panel
    now = engine.clock()
    panel = midna_panel.build(engine.hub, now)
    if not panel or panel_stale(panel, now):
        return {"scanned": False, "why": "panel not fresh", "asOf": (panel or {}).get("asOf")}
    if stored_scan(engine.root, panel["asOf"]) is not None:
        return {"scanned": False, "why": "already scanned", "asOf": panel["asOf"]}
    rec = cached_scan(engine.root, panel)
    out = {"scanned": True, "asOf": panel["asOf"], "blocked": bool(rec.get("blocked")),
           "hits": len(rec.get("hits") or [])}
    if rec.get("blocked"):
        out["why"] = rec.get("why")
    return out


def feed_scan(feeds, sleeve, now, arg=None):
    """the job's scan of the panel's session; None while the panel is stale (the source scanned only a fresh panel)
    or until the job has scanned it."""
    panel = feeds.get("midna_panel", sleeve, now)
    if not panel or panel_stale(panel, now):
        return None
    eng = getattr(sleeve, "engine", None)
    root = eng.root if eng is not None else os.path.dirname(os.path.dirname(feeds.hub.cache.root))
    return stored_scan(root, panel["asOf"])
