"""Genuine Ausar hosting (posted R25 source, quant-research-backup 1692d555).
Every TSV book whose posted code exists is hosted by that code; md2's own reimplementation is retired (status 'replaced')."""
import json, sqlite3, os
ROOT = "/workspace/desk2"
ORIG = {  # TSV book -> (genuine desk, genuine book id)
    "ausar_pb1": ("trader_cli", "trader_rsi2_public_v1"), "ausar_pb2": ("trader_cli", "trader_squeeze20_public_v1"),
    "ausar_pb157": ("trader_cli", "trader_donchian55_public_v1"),
    "ausar_pb5": ("absorption_runtime", "ABSORPTION_ENJUSDT_4H"), "ausar_pb6": ("absorption_runtime", "ABSORPTION_LINKUSDT_4H"),
    "ausar_pb7": ("prospective_native", "ETH_SMA200"), "ausar_pb8": ("prospective_native", "BTC_ETH_SMA200"),
}
FUNCTIONAL_WAITS = {"option_market_closed", "OUTSIDE_0935_0940_EXECUTION_WINDOW", "regular_session_closed"}

def r19_health():
    db = sqlite3.connect(f"file:{ROOT}/state/ausar/r19.sqlite3?mode=ro", uri=True); out = {}
    for k, p in db.execute("select key,payload_json from r19_health where key like 'book:%'"):
        b = json.loads(p).get("blockers") or []
        out[k[5:]] = [x if isinstance(x, str) else x.get("reason", json.dumps(x)) for x in b]
    db.close(); return out

def apply(cat):
    amap = {m["pb"]: m for m in json.load(open(f"{ROOT}/catalog/ausar_map.json"))}
    H = r19_health(); replaced = set(); new = []
    for r in cat:
        if r["source"] != "ausar": continue
        m = amap.get(r["sid"], {}); r19 = m.get("r19") or []
        if r["sid"] in ORIG:
            desk, bid = ORIG[r["sid"]]
            if r["status"] == "installed": replaced.add(r["sid"])
            r["status"], r["merged_into"] = "replaced", f"ausar-genuine:{bid}"
            r["reason"] = f"md2 reimplementation retired; hosted by posted Ausar {desk} ({bid}), rules match the TSV entry/exit text"
            new.append(dict(sid=f"ausar_g_{bid}", source="ausar-genuine", family=r["family"], strategy=r["strategy"], entry=r["entry"], exit=r["exit"],
                            data="posted Ausar runtime inputs", status="installed", reason=f"genuine {desk}, local paper ledger state/ausar_orig", merged_into=None,
                            origin=f"quant-research-backup@1692d555 backend/{desk}.py"))
        elif len(r19) == 1:
            bid = r19[0]; bl = H.get(bid)
            if r["status"] == "installed": replaced.add(r["sid"])
            r["status"], r["merged_into"], r["reason"] = "replaced", f"ausar-r19:{bid}", "md2 reimplementation retired; hosted by the posted r19 engine"
            if bl is None: st, why = "blocked", "not in r19 worker health"
            else:
                hard = [b for b in bl if b not in FUNCTIONAL_WAITS]
                st = "blocked" if hard else "installed"
                why = ("; ".join(hard) if hard else ("waiting: " + ", ".join(bl) if bl else "functional"))
                if "FUNDING_SOURCE_HTTP_451" in hard: why += " (Binance USDT-perp funding geoblocked; OKX substitute rejected: evidence/funding_substitute_check.json)"
                if "enrollment_coverage_below_99pct" in hard: why += " (census warm-up: r19 enrolls 20 names/pass of ~1843; see EVIDENCE)"
            new.append(dict(sid=f"ausar_r19_{bid}", source="ausar-r19", family=r["family"], strategy=r["strategy"], entry=r["entry"], exit=r["exit"],
                            data="posted r19 data adapters", status=st, reason=why, merged_into=None, origin="quant-research-backup@1692d555 backend/r19_*"))
        elif r["sid"] in ("ausar_pb44", "ausar_pb45", "ausar_pb46"):
            r["reason"] += "; posted public_recipe_runtime also hosts it (state/ausar_orig), counted once"
    return cat + new, replaced
