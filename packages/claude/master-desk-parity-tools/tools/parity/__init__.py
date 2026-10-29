"""Old-desk vs femto-port parity harnesses. Each harness imports the OLD sleeve module read-only from
OLD_DESK (the alpaca-swing-desk tree, e.g. midna@main/workspace/alpaca-swing-desk) and the vendored femto
sleeve, drives both over a deterministic case corpus, and writes a receipt to docs/receipts/parity/.

    OLD_DESK=/path/to/alpaca-swing-desk python3 -m tools.parity.run donchian [...]"""
import json
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECEIPTS = os.path.join(ROOT, "docs", "receipts", "parity")


def old_desk():
    od = os.environ.get("OLD_DESK")
    if not od or not os.path.isdir(od):
        raise SystemExit("set OLD_DESK to the alpaca-swing-desk tree")
    return od


def old_run(script, payload, timeout=900, tree=None):
    """run `script` (python source) against the OLD desk in a separate process — the old tree has its own
    `desk` package, so it never shares an interpreter with this one. The script reads JSON `payload` from
    stdin as PAYLOAD and must print one JSON document (the last stdout line). `tree`: another source tree
    (e.g. the Aurelia source desk) in place of OLD_DESK."""
    import subprocess
    od = tree or old_desk()
    stubs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs")
    prelude = ("import json, sys\nsys.path.insert(0, %r)\nsys.path.append(%r)\nPAYLOAD = json.load(sys.stdin)\n"
               % (od, stubs))
    r = subprocess.run([sys.executable, "-c", prelude + script], input=json.dumps(payload), capture_output=True,
                       text=True, timeout=timeout, cwd=od, env=dict(os.environ, DRY_RUN="1"))
    if r.returncode != 0:
        raise RuntimeError("old-desk harness failed: " + r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def trading_dates(start, n):
    out, d = [], date.fromisoformat(start)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def walk(seed, n, start_px=50.0, vol=0.025, drift=0.0005, jumps=0.02, start="2025-01-02"):
    """deterministic OHLCV daily path with occasional jumps (to exercise breakouts and breakdowns)."""
    rnd = random.Random(seed)
    dates = trading_dates(start, n)
    px, rows = start_px, []
    for d in dates:
        r = rnd.gauss(drift, vol) + (rnd.choice((-1, 1)) * rnd.uniform(0.04, 0.12) if rnd.random() < jumps else 0)
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.5, px * (1 + r))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        v = 0.0 if rnd.random() < 0.01 else float(int(rnd.uniform(2e5, 5e6)))
        rows.append({"d": d, "o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4), "v": v})
        px = c
    return rows


def as_epoch(rows):
    """femto bar dicts: t = 04:00 UTC of the session date (Alpaca stamp; +4h shift dates it correctly)."""
    return [{"t": datetime.fromisoformat(r["d"]).replace(hour=4, tzinfo=timezone.utc).timestamp(),
             "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows]


def as_iso(rows):
    return [{"t": r["d"], "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]} for r in rows]


def write_receipt(name, payload):
    os.makedirs(RECEIPTS, exist_ok=True)
    payload = dict(payload, sleeve=name, generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   old_desk=os.environ.get("OLD_DESK"))
    path = os.path.join(RECEIPTS, name + ".json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    return path


def femto_module(name):
    """the vendored femto sleeve; with FEMTO_REF=<git ref> the version at that ref (e.g. the unpatched
    vendoring commit) — used to record how far the original port diverged from the old desk."""
    import importlib
    import subprocess
    import types
    ref = os.environ.get("FEMTO_REF")
    if not ref:
        return importlib.import_module("desk.sleeves.femto." + name)
    src = subprocess.run(["git", "-C", ROOT, "show", f"{ref}:desk/sleeves/femto/{name}.py"], capture_output=True,
                         text=True, check=True).stdout
    mod = types.ModuleType(f"desk.sleeves.femto._ref_{name}")
    mod.__package__ = "desk.sleeves.femto"
    exec(compile(src, f"{ref}:{name}.py", "exec"), mod.__dict__)
    return mod
