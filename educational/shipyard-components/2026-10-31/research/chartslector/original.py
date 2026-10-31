"""Execute a bounded allowlist of pinned original functions, without copying their math.
The three allowlisted indicator/source files loaded here remain unchanged. AST compilation omits machine-local imports and
Numba's optional accelerator decorator; function bodies execute verbatim in CPython.
No LoD/entry/sizing or order functions are loaded or invoked.
"""
from pathlib import Path
import ast
import hashlib
import json
import types
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "4985ae5989923731b5dbd1edb4c08ec1bd1424d9"

def verify_sources():
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    for row in manifest["files"]:
        content = (ROOT / row["path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if blob != row.get("export_git_blob_sha", row["git_blob_sha"]):
            raise ValueError("pinned_source_hash_mismatch:" + row["path"])
    return manifest

def functions(path, names, extra=None):
    source = ROOT / "archive_source" / path
    tree = ast.parse(source.read_text(), filename=str(source))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            node.decorator_list = []
            selected.append(node)
    if {x.name for x in selected} != set(names):
        raise ValueError("original_function_missing")
    scope = {"np": np, "pd": pd, "swv": swv, **(extra or {})}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), scope)
    return types.SimpleNamespace(**{name: scope[name] for name in names})

verify_sources()
I = functions("lib/ind.py", ["_df", "sma", "rstd", "rmax", "rmin", "rsum", "ema", "_rma", "rma", "lag", "tr", "atr", "consec"])
PT = functions("systems/pine_tools.py", ["rs1m", "stage"], {"I": I})
ROT = functions("systems/s04_rotation_core.py", ["_ema", "rrr"], {"I": I})
STAGE_NAMES = {1: "1A", 2: "1B", 3: "2A", 4: "2B", 5: "2C", 6: "2D", 7: "3A", 8: "3B", 9: "4A", 10: "4B", 11: "4C", 12: "NA"}

def calculate(bars, spy):
    """Same-date finite OHLCV rows, normalized to original panel float32 contract."""
    if len(bars) != len(spy) or len(bars) < 156:
        raise ValueError("insufficient_or_unaligned_history")
    O, H, L, C, V = (np.asarray([b[k] for b in bars], dtype=np.float32)[None] for k in ("open", "high", "low", "close", "volume"))
    ref = np.asarray([b["close"] for b in spy], dtype=np.float32)
    out = {}
    for n in (26, 78, 156):
        rank, streak, count = PT.rs1m(C, ref, N=n)
        out["rs" + str(n)] = rank[0]
        if n == 26:
            out["rs_run15"] = streak[0]
            out["rs_12of15"] = count[0]
    out["stage_code"] = PT.stage(O, H, L, C)[0]
    r, m = ROT.rrr(C, ref)
    out["rrr_ratio"], out["rrr_momentum"] = r[0], m[0]
    return out

def clean(value):
    if isinstance(value, np.ndarray):
        return [clean(x) for x in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value

