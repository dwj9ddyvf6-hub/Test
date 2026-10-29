"""Sleeve conformance checker — static (AST) enforcement of spec section 3.

A sleeve module FAILS if it:
  * imports a broker/HTTP/subprocess module (requests, urllib, httpx,
    aiohttp, socket, subprocess, alpaca*, or core.broker in any form),
  * opens files (open(), io.open, os.open, pathlib write/read helpers),
  * reads the system clock (time.time/time_ns/monotonic/perf_counter,
    datetime.now/utcnow, date.today),
  * references Alpaca directly (any name/attribute/string mentioning
    alpaca or an Alpaca endpoint),
  * uses eval/exec/__import__ to smuggle any of the above past the scan,
  * lacks the contract shape (a CONFIG SleeveConfig and a signal callable).
"""
import ast

BANNED_IMPORT_ROOTS = {"requests", "urllib", "httpx", "aiohttp", "socket",
                       "subprocess", "alpaca", "alpaca_trade_api"}
BANNED_TIME_CALLS = {"time", "time_ns", "monotonic", "perf_counter", "clock"}
BANNED_CLOCK_METHODS = {"now", "utcnow", "today"}
BANNED_CALLS = {"open", "eval", "exec", "__import__"}
BANNED_ATTR_CALLS = {"open", "write_text", "write_bytes", "read_text", "read_bytes"}


def check_source(source, filename="<sleeve>"):
    """Return a list of violation strings; empty list == conforming."""
    violations = []
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        return [f"syntax_error: {e}"]

    def dotted(node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr); node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    has_config = has_signal = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            names = [mod] if mod else [a.name for a in node.names]
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            for name in names:
                root = (name or "").split(".")[0]
                if root in BANNED_IMPORT_ROOTS or name == "core.broker" or name.endswith(".broker"):
                    violations.append(f"banned_import: {name}")
                if "alpaca" in (name or "").lower():
                    violations.append(f"alpaca_reference: import {name}")
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "CONFIG":
                    has_config = True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "CONFIG":
            has_config = True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "signal":
                has_signal = True
            for dec in node.decorator_list:
                pass
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in BANNED_CALLS:
                violations.append(f"banned_call: {fn.id}()")
            path = dotted(fn)
            leaf = path.split(".")[-1] if path else ""
            root = path.split(".")[0] if path else ""
            if root == "time" and leaf in BANNED_TIME_CALLS:
                violations.append(f"clock_read: {path}() — use context.now")
            if leaf in BANNED_CLOCK_METHODS and root in ("datetime", "date"):
                violations.append(f"clock_read: {path}() — use context.now")
            if isinstance(fn, ast.Attribute) and fn.attr in BANNED_ATTR_CALLS and root in ("os", "io", "Path"):
                violations.append(f"file_access: {path}()")
        if isinstance(node, ast.Attribute) and "alpaca" in node.attr.lower():
            violations.append(f"alpaca_reference: .{node.attr}")
        if isinstance(node, ast.Name) and "alpaca" in node.id.lower():
            violations.append(f"alpaca_reference: {node.id}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "alpaca.markets" in node.value:
            violations.append("alpaca_reference: endpoint string")
    if not has_config:
        violations.append("missing_contract: no CONFIG block")
    if not has_signal:
        violations.append("missing_contract: no signal() defined")
    return violations


def check_file(path):
    with open(path) as f:  # the CHECKER may open files; sleeves may not
        return check_source(f.read(), filename=str(path))


def assert_conforming(path):
    v = check_file(path)
    if v:
        raise ValueError(f"sleeve conformance FAILED for {path}: {v}")
    return True
