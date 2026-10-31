#!/usr/bin/env python3
"""Read-only MCP surface for the terminal: exactly four tools.

Checked first (2026-10-29): this stack runs no MCP server of its own
and the Python ``mcp`` package is not installed, so this is a small
dependency-free MCP server over stdio (JSON-RPC: initialize,
tools/list, tools/call, ping), shaped on the Shipyard worker/mcp.js
pattern: tight input schemas, readOnlyHint annotations on every tool.

The four tools read the same files the pages read (site/*/data.json,
site/record/data.json, the forecast registry, and the chain store
manifest). This server is a second reader, never a second source:
it writes nothing, holds no credentials, and exposes no order,
account, or write tool of any kind.

Tools:
  terminal_catalog    the tool index: slug, name, state, data state
  terminal_tool_data  one tool page's current data.json
  forecast_record     the forecast Record: grades + abstention audit
  chain_store_status  chain snapshot store status (manifest tail)

Usage: python3 mcp_server.py   (stdio; one JSON-RPC message per line)
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.dirname(HERE)
CHAINS_DIR = os.path.expanduser("~/workspace/morgue/state/morgue/chains")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SERVER_INFO = {"name": "terminal-lineup-readonly", "version": "1.0.0"}
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "terminal_catalog",
        "description": "List the terminal's tools: slug, display name, "
                       "page state and whether its data file is present. "
                       "Read-only.",
        "inputSchema": {"type": "object", "properties": {},
                        "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "terminal_tool_data",
        "description": "Return one tool page's current data.json, the "
                       "same file the page itself reads. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"slug": {"type": "string",
                                    "description": "Tool slug, for "
                                                   "example chain-explorer"}},
            "required": ["slug"], "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "forecast_record",
        "description": "Return the forecast Record: published grades "
                       "(totals and board) and the abstention coverage "
                       "audit, from the Record page's own data file. "
                       "Read-only.",
        "inputSchema": {"type": "object", "properties": {},
                        "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "chain_store_status",
        "description": "Return chain snapshot store status: symbols on "
                       "record, snapshot days, and the tail of the "
                       "store manifest. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"tail": {"type": "integer", "minimum": 1,
                                    "maximum": 50,
                                    "description": "Manifest lines to "
                                                   "return (default 10)"}},
            "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
]
TOOL_NAMES = {t["name"] for t in TOOLS}


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def tool_slugs():
    return sorted(
        name for name in os.listdir(HERE)
        if os.path.isdir(os.path.join(HERE, name))
        and os.path.exists(os.path.join(HERE, name, "index.html")))


def call_terminal_catalog(_args):
    entries = []
    for slug in tool_slugs():
        data_path = os.path.join(HERE, slug, "data.json")
        entry = {"slug": slug, "has_data": os.path.exists(data_path)}
        if entry["has_data"]:
            try:
                data = load_json(data_path)
                entry["name"] = data.get("tool")
                entry["state"] = data.get("state")
                entry["feed"] = data.get("feed")
                entry["price_basis"] = data.get("price_basis")
            except (OSError, ValueError) as exc:
                entry["data_error"] = f"{type(exc).__name__}: {exc}"
        entries.append(entry)
    return {"count": len(entries), "tools": entries}


def call_terminal_tool_data(args):
    slug = (args or {}).get("slug", "")
    if not SLUG_RE.match(slug or ""):
        raise ValueError(f"invalid slug {slug!r}")
    data_path = os.path.join(HERE, slug, "data.json")
    if slug not in tool_slugs() or not os.path.exists(data_path):
        raise ValueError(f"no data file for tool {slug!r}")
    return {"slug": slug, "data": load_json(data_path)}


def call_forecast_record(_args):
    record = load_json(os.path.join(HERE, "record", "data.json"))
    out = {"generated_at_utc": record.get("generated_at_utc"),
           "totals": record.get("totals"),
           "abstention_audit": record.get("abstention_audit")}
    registry_path = os.path.join(LINEUP, "forecast", "registry.json")
    if os.path.exists(registry_path):
        registry = load_json(registry_path)
        engines = registry.get("engines") or registry
        out["registry_engines"] = (len(engines) if isinstance(
            engines, (list, dict)) else None)
    return out


def call_chain_store_status(args):
    tail_n = int((args or {}).get("tail", 10))
    tail_n = max(1, min(50, tail_n))
    out = {"store": CHAINS_DIR, "symbols": {}, "manifest_tail": []}
    if os.path.isdir(CHAINS_DIR):
        for symbol in sorted(os.listdir(CHAINS_DIR)):
            sub = os.path.join(CHAINS_DIR, symbol)
            if os.path.isdir(sub):
                days = sorted(f for f in os.listdir(sub)
                              if f.endswith(".json.gz"))
                out["symbols"][symbol] = {
                    "snapshots": len(days),
                    "latest_day": days[-1].removesuffix(".json.gz")
                    if days else None}
        manifest = os.path.join(CHAINS_DIR, "manifest.jsonl")
        if os.path.exists(manifest):
            with open(manifest, encoding="utf-8") as fh:
                lines = [ln for ln in fh if ln.strip()]
            for ln in lines[-tail_n:]:
                try:
                    out["manifest_tail"].append(json.loads(ln))
                except ValueError:
                    out["manifest_tail"].append({"unparsed": ln.strip()})
    return out


HANDLERS = {
    "terminal_catalog": call_terminal_catalog,
    "terminal_tool_data": call_terminal_tool_data,
    "forecast_record": call_forecast_record,
    "chain_store_status": call_chain_store_status,
}


def handle(request):
    method = request.get("method")
    rid = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        if name not in TOOL_NAMES:
            return {"jsonrpc": "2.0", "id": rid, "error": {
                "code": -32602, "message": f"unknown tool {name!r}"}}
        try:
            result = HANDLERS[name](params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text",
                             "text": json.dumps(result, default=str)}],
                "isError": False}}
        except (ValueError, OSError) as exc:
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text",
                             "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True}}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid, "error": {
            "code": -32601, "message": f"unknown method {method!r}"}}
    return None  # notification: no reply


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except ValueError:
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
