"""Load Alpaca paper keys from the same env files Lazarus uses. Values never logged, printed or persisted by md2."""
import os, re
FILES = {"MAIN": "/home/box/.main_alpaca_env", "TEST_MWJW": "/home/box/.sleeve_alpaca_env"}
def _parse(p):
    out = {}
    try:
        for ln in open(p):
            m = re.match(r"\s*(?:export\s+)?([A-Z0-9_]+)=(.*)", ln)
            if m: out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    except OSError: pass
    return out
def keys(account="TEST_MWJW"):
    e = _parse(FILES[account])
    if account == "MAIN": return e.get("ALPACA_API_KEY_ID"), e.get("ALPACA_API_SECRET_KEY")
    return e.get("ALPACA_SLEEVE_API_KEY_ID"), e.get("ALPACA_SLEEVE_API_SECRET_KEY")
def headers(account="TEST_MWJW"):
    k, s = keys(account)
    if not (k and s): raise RuntimeError(f"no keys for {account}")
    return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s}
