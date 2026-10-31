"""Regression blockers for the Shipyard adoptions (2026-10-29):
quote freshness gate, feed provenance stamps, content-addressed
asset manifest + smoke check, and the read-only MCP surface.

Run in the existing forecast test setup:
    python3 -m pytest tests/ -q        (from forecast/)
"""

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(SITE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tc = _load("terminal_common", "terminal_common.py")
cc = _load("collect_chains", "collect_chains.py")
sc = _load("smoke_check", "smoke_check.py")

NOW = datetime(2026, 10, 29, 15, 0, 0, tzinfo=timezone.utc)


# ---- (1) quote freshness gate, fail-closed ---------------------------

def test_gate_fresh_quote_passes_figures_through():
    ts = (NOW - timedelta(seconds=30)).isoformat()
    out = tc.gate_figures({"bid": 1.2, "ask": 1.3}, ["bid", "ask"], ts,
                          now=NOW)
    assert out["quote_state"] == "fresh"
    assert out["bid"] == 1.2 and out["ask"] == 1.3
    assert out["figures_withheld"] == []


def test_gate_stale_quote_withholds_and_never_substitutes():
    ts = (NOW - timedelta(seconds=91)).isoformat()
    out = tc.gate_figures({"bid": 1.2, "ask": 1.3}, ["bid", "ask"], ts,
                          now=NOW)
    assert out["quote_state"] == "stale"
    assert out["bid"] is None and out["ask"] is None
    assert out["figures_withheld"] == ["bid", "ask"]
    assert out["quote_freshness"]["age_seconds"] > 90


def test_gate_missing_quote_is_no_data_and_withholds():
    out = tc.gate_figures({"bid": 1.2}, ["bid"], None, now=NOW)
    assert out["quote_state"] == "no_data"
    assert out["bid"] is None
    out2 = tc.gate_figures({"bid": 1.2}, ["bid"], "not-a-time", now=NOW)
    assert out2["quote_state"] == "no_data" and out2["bid"] is None


def test_gate_boundary_exactly_90_seconds_is_fresh():
    ts = (NOW - timedelta(seconds=90)).isoformat()
    assert tc.quote_freshness(ts, now=NOW)["state"] == "fresh"
    ts = (NOW - timedelta(seconds=90, milliseconds=1)).isoformat()
    assert tc.quote_freshness(ts, now=NOW)["state"] == "stale"


def test_collector_fetch_spot_gates_on_quote_timestamp(monkeypatch):
    fresh_meta = {"regularMarketPrice": 100.0,
                  "regularMarketTime": int(NOW.timestamp()) - 10}
    stale_meta = {"regularMarketPrice": 100.0,
                  "regularMarketTime": int(NOW.timestamp()) - 3600}
    doc = {"chart": {"result": [{"meta": fresh_meta}]}}
    monkeypatch.setattr(cc, "curl_json", lambda args, timeout=60: doc)
    price, _src, qts, state = cc.fetch_spot("SPY", now=NOW)
    assert price == 100.0 and state == "fresh" and qts is not None
    doc["chart"]["result"][0]["meta"] = stale_meta
    _p, _s, _q, state = cc.fetch_spot("SPY", now=NOW)
    assert state == "stale"
    doc["chart"]["result"][0]["meta"] = {"regularMarketPrice": 100.0}
    _p, _s, _q, state = cc.fetch_spot("SPY", now=NOW)
    assert state == "no_data"


def test_snapshot_doc_carries_spot_freshness_fields():
    doc = cc.build_snapshot_doc("SPY", "2026-10-29", 1.0, "src", [],
                                "u", "e", spot_quote_ts="t",
                                spot_freshness="fresh")
    assert doc["spot_freshness"] == "fresh" and doc["spot_quote_ts"] == "t"
    legacy = cc.build_snapshot_doc("SPY", "2026-10-29", 1.0, "src", [],
                                   "u", "e")
    assert legacy["spot_freshness"] is None  # old callers unaffected


# ---- (2) feed provenance stamps --------------------------------------

def test_stamp_adds_provenance_and_preserves_existing_fields():
    data = {"tool": "X", "state": "published", "source": "prose",
            "figure": 3}
    out = tc.stamp_provenance(data, feed="iex", price_basis="close")
    assert out["feed"] == "iex" and out["price_basis"] == "close"
    assert out["execution_pricing"] is False
    assert out["provenance"]["feed"] == "iex"
    assert out["tool"] == "X" and out["figure"] == 3
    assert "feed" not in data  # caller's dict untouched


def test_stamp_indicative_prefix_and_declared_feed_kept():
    out = tc.stamp_provenance({"mid": 5, "feed": "other"},
                              feed="indicative", price_basis="indicative",
                              indicative_keys=("mid",))
    assert out["indicative_mid"] == 5 and "mid" not in out
    assert out["provenance"]["declared_feed"] == "other"
    assert out["feed"] == "indicative"


def test_every_refresh_script_is_wired_to_stamp():
    import glob
    unwired = []
    for path in sorted(glob.glob(os.path.join(SITE, "refresh_*.py"))):
        if "stamp_for_script" not in open(path, encoding="utf-8").read():
            unwired.append(os.path.basename(path))
    assert unwired == [], f"refresh scripts not stamping: {unwired}"


def test_every_data_json_on_disk_carries_provenance():
    import glob
    missing = []
    for path in sorted(glob.glob(os.path.join(SITE, "*", "data.json"))):
        data = json.load(open(path, encoding="utf-8"))
        if not (data.get("feed") and data.get("price_basis")
                and data.get("execution_pricing") is False
                and isinstance(data.get("provenance"), dict)):
            missing.append(os.path.relpath(path, SITE))
    assert missing == [], f"data.json without provenance: {missing}"


# ---- (3) content-addressed manifest + smoke check --------------------

def test_manifest_roundtrip_and_tamper_fails_loudly(tmp_path):
    (tmp_path / "index.html").write_text("<html>hub</html>")
    tool = tmp_path / "tool-a"
    tool.mkdir()
    (tool / "index.html").write_text("<html>a</html>")
    (tool / "data.json").write_text('{"x": 1}\n')
    manifest = sc.build_manifest(str(tmp_path))
    assert set(manifest["files"]) == {
        "index.html", "tool-a/index.html", "tool-a/data.json"}
    assert sc.verify_tree(str(tmp_path), manifest) == []
    (tool / "data.json").write_text('{"x": 2}\n')
    problems = sc.verify_tree(str(tmp_path), manifest)
    assert any("MISMATCH" in p and "tool-a/data.json" in p
               for p in problems)


def test_real_tree_matches_committed_manifest():
    manifest = sc.load_manifest()
    assert sc.verify_tree(SITE, manifest) == []


# ---- (4) read-only MCP surface ----------------------------------------

def _mcp_session(messages):
    proc = subprocess.run(
        [sys.executable, os.path.join(SITE, "mcp_server.py")],
        input="".join(json.dumps(m) + "\n" for m in messages),
        capture_output=True, text=True, timeout=120)
    return [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]


def test_mcp_exposes_exactly_four_readonly_tools():
    replies = _mcp_session([
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ])
    tools = replies[1]["result"]["tools"]
    assert [t["name"] for t in tools] == [
        "terminal_catalog", "terminal_tool_data", "forecast_record",
        "chain_store_status"]
    assert all(t["annotations"]["readOnlyHint"] is True for t in tools)


def test_mcp_tools_read_the_pages_own_files():
    replies = _mcp_session([
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "terminal_catalog", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "forecast_record", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "chain_store_status",
                    "arguments": {"tail": 3}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "no_such_tool", "arguments": {}}},
    ])
    catalog = json.loads(replies[0]["result"]["content"][0]["text"])
    assert catalog["count"] >= 100
    assert all(e["has_data"] for e in catalog["tools"]
               if e["slug"] != "greeks-sketch"
               and e["slug"] != "payoff-sketch")
    record = json.loads(replies[1]["result"]["content"][0]["text"])
    assert "abstention_audit" in record and "totals" in record
    chains = json.loads(replies[2]["result"]["content"][0]["text"])
    assert "SPY" in chains["symbols"] and len(chains["manifest_tail"]) <= 3
    assert "error" in replies[3]  # unknown tool refused, no fifth tool
