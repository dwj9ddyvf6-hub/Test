"""Best Setups GENERATION from v3 state (CURE3-2, A8 end-to-end half).

The vendored Best Setups files are byte-identical and never modified;
their generator (tools/build_setups.py) wires the desk SIP door +
Yahoo ^VIX into the pure curator, but its door module lives in the
femto-lean tree (outside the §4 vendor list). So generation runs the
ORIGINAL tree's generator read-only (PYTHONDONTWRITEBYTECODE=1,
--out into v3 state) against a curator-shaped state dir translated
from v3's own journals:

  v3 state/dispatcher.jsonl + state/<sleeve>/journal.jsonl
    -> <curator_state>/ledger.jsonl   (session/kind/sleeve/symbol rows)
    -> <curator_state>/live/sleeves/<sleeve>.json (journal positions)
    -> <curator_state>/live/terminal_snapshot.json (v3 terminal.json)
    -> <curator_state>/live/slices.json (config slices)

The output lands at state/setups_latest.json with a provenance sidecar
state/setups_generation.json; the next desk cycle then merges it via
the vendored publish merge with setups_source=state/setups_latest.json
(CURE2-4). An empty v3 ledger generates an honest doc (0 setups,
market context from real bars) — generation is proven, candidacy is
whatever v3 actually traded.
"""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime, timezone

FEMTO_ROOT = os.path.expanduser("~/workspace/femto-lean")


def _read_jsonl(path):
    rows = []
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    return rows


def build_curator_state(v3_root, out_dir):
    """Translate v3 state -> curator load_state layout. Returns counts."""
    state = os.path.join(v3_root, "state")
    os.makedirs(os.path.join(out_dir, "live", "sleeves"), exist_ok=True)
    ledger = []
    # Dispatcher journal: the fill record of the desk. Its rows carry
    # no ts; the session falls back to the journal file's mtime date.
    dpath = os.path.join(state, "dispatcher.jsonl")
    dsession = ""
    if os.path.exists(dpath):
        dsession = datetime.fromtimestamp(
            os.path.getmtime(dpath), timezone.utc).strftime("%Y-%m-%d")
    for row in _read_jsonl(dpath):
        ts = row.get("ts") or row.get("timestamp") or dsession
        ev = row.get("event") or row.get("status") or ""
        kind = "fill" if "fill" in str(ev) else (
            "signal_intent" if "intent" in str(ev) else None)
        if kind and row.get("symbol"):
            ledger.append({"session": str(ts)[:10], "kind": kind,
                           "sleeve": row.get("sleeve_id") or row.get("sleeve"),
                           "symbol": row.get("symbol")})
    # Per-sleeve journals: intent events carry the session + symbol when
    # the dispatcher journal is absent (pre-first-dispatch desk).
    positions = {}
    if os.path.isdir(state):
        for sid in sorted(os.listdir(state)):
            jpath = os.path.join(state, sid, "journal.jsonl")
            if not os.path.isfile(jpath):
                continue
            pos = {}
            for row in _read_jsonl(jpath):
                if row.get("event") == "intent" and row.get("symbol"):
                    ledger.append(
                        {"session": str(row.get("ts", ""))[:10],
                         "kind": "signal_intent", "sleeve": sid,
                         "symbol": row.get("symbol")})
                if row.get("event") == "fill" and row.get("symbol"):
                    pos[row["symbol"]] = {
                        "position": {"entry_date": str(row.get("ts", ""))[:10],
                                     "qty": row.get("qty")}}
            if pos:
                positions[sid] = pos
                with open(os.path.join(out_dir, "live", "sleeves",
                                       f"{sid}.json"), "w") as fh:
                    json.dump(pos, fh, sort_keys=True)
    with open(os.path.join(out_dir, "ledger.jsonl"), "w") as fh:
        for row in ledger:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    term = os.path.join(state, "terminal.json")
    if os.path.exists(term):
        with open(os.path.join(out_dir, "live",
                               "terminal_snapshot.json"), "w") as fh:
            fh.write(open(term).read())
    cfg = os.path.join(v3_root, "config", "sleeves.json")
    slices = {}
    if os.path.exists(cfg):
        for row in json.load(open(cfg)).get("sleeves", []):
            slices[row["id"]] = row.get("slice", {})
    with open(os.path.join(out_dir, "live", "slices.json"), "w") as fh:
        json.dump(slices, fh, sort_keys=True)
    return {"ledger_rows": len(ledger), "sleeves_with_positions": len(positions)}


def generate(v3_root, femto_root=None, runner=None, session=None):
    """Run the original generator against translated v3 state.
    Returns the provenance dict; raises on generator failure."""
    femto_root = femto_root or FEMTO_ROOT
    curator_dir = os.path.join(v3_root, "state", "curator_input")
    counts = build_curator_state(v3_root, curator_dir)
    out_path = os.path.join(v3_root, "state", "setups_latest.json")
    cmd = [sys.executable, os.path.join(femto_root, "tools", "build_setups.py"),
           "--state-dir", curator_dir, "--out", out_path]
    if session:
        cmd += ["--session", session]
    if runner is None:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run(cmd, cwd=femto_root, capture_output=True,
                           text=True, timeout=900, env=env)
        if r.returncode != 0:
            raise RuntimeError(f"build_setups failed: {r.stderr[-600:]}")
        stdout = r.stdout
    else:
        stdout = runner(cmd)
    doc = json.load(open(out_path))
    prov = {"generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "v3_state_via_original_build_setups",
            "curator_input": counts,
            "setups": len(doc.get("setups") or []),
            "as_of": doc.get("as_of"),
            "generator_stdout_head": (stdout or "")[:300]}
    with open(os.path.join(v3_root, "state", "setups_generation.json"),
              "w") as fh:
        json.dump(prov, fh, sort_keys=True, indent=1)
    return prov


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(json.dumps(generate(root), indent=1))
