"""Shadow recorder for Binance USDT-perp funding as redistributed by CoinGecko's free public derivatives API (no key; their
'Binance (Futures)' tickers carry Binance's current funding rate, in percent, rounded to 0.001%). Lawful from the US box: no
binance.com/fapi, VPN or proxy. Shadow only: it feeds NO book. A sample is kept with its genuine receipt time so a later validator
can compare the last pre-settlement sample against Binance's own settled series (data.binance.vision archive)."""
import json, os, time, urllib.request
URL = "https://api.coingecko.com/api/v3/derivatives/exchanges/binance_futures?include_tickers=unexpired"
SYMS = ("ADAUSDT", "LINKUSDT", "ENJUSDT")

def parse(doc, received_at, syms=SYMS):
    rows = []
    for t in doc.get("tickers") or []:
        if t.get("symbol") in syms and t.get("contract_type") == "perpetual" and t.get("funding_rate") is not None:
            rows.append(dict(symbol=t["symbol"], rate=float(t["funding_rate"]) / 100.0, rate_pct_rounded=float(t["funding_rate"]),
                             last_traded=t.get("last_traded"), received_at=received_at, source="coingecko:binance_futures"))
    return rows

def record(path, fetch=None):
    t0 = time.time()
    raw = fetch() if fetch else urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "md2", "Accept": "application/json"}), timeout=15).read()
    rows = parse(json.loads(raw), round(time.time(), 3))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for r in rows: f.write(json.dumps(r, sort_keys=True) + "\n")
    return dict(rows=len(rows), ms=round((time.time() - t0) * 1e3))

# ---- Coinalyze (free key from env COINALYZE_API_KEY only; never logged/stored). Binance USDT perps = <SYM>_PERP.A.
# Validated exactly vs the Binance archive (evidence/coinalyze_check.json): settled rate appears ~0-15 min after settlement.
CA = "https://api.coinalyze.net/v1/"
def parse_coinalyze(settled, predicted, received_at):
    rows = []
    for kind, doc in (("settled", settled), ("predicted", predicted)):
        for x in doc or []:
            sym = x["symbol"].split("_PERP")[0]
            if sym in SYMS: rows.append(dict(symbol=sym, rate=float(x["value"]) / 100.0, kind=kind, update_ms=x.get("update"), received_at=received_at, source="coinalyze:binance"))
    return rows

def record_coinalyze(path, fetch=None):
    key = os.environ.get("COINALYZE_API_KEY")
    if not key and fetch is None: return dict(rows=0, skipped="no key in env")
    q = "?symbols=" + ",".join(s + "_PERP.A" for s in SYMS)
    def _get(ep): return json.loads(urllib.request.urlopen(urllib.request.Request(CA + ep + q, headers={"api_key": key, "User-Agent": "md2"}), timeout=15).read())
    get = fetch or _get
    try: rows = parse_coinalyze(get("funding-rate"), get("predicted-funding-rate"), round(time.time(), 3))
    except Exception as e: raise RuntimeError(f"coinalyze {type(e).__name__}") from None   # never surface request headers
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        for r in rows: f.write(json.dumps(r, sort_keys=True) + "\n")
    return dict(rows=len(rows))
