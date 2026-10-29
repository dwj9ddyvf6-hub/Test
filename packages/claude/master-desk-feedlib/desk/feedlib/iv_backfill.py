"""Iron condor IV-store backfill: the sleeve's own measurement (iron_condor.atm_iv — the nearest 30-45 DTE expiry's
call with the strike nearest the spot, Black-Scholes inverted at r = 4%) recomputed for each past session from
Alpaca's historical option bars (OPRA history from 2024-02), so the TRUE IV rank has its 60-observation history on the
first day instead of after 60 sessions.

    run(client, universe, sessions, closes) -> {SYM: [[session, iv], ...]}

Per name and session d: the spot is d's daily close; the calls whose expiry is 30-45 days after d (active or expired
contracts); the nearest such expiry and the strike nearest the spot; that contract's daily bar on d, its close as the
option price (the sleeve inverts the live mid; history has no quote, so the session close stands in for it — a named
divergence of the backfill). A session without the bar, or an inversion outside (0, 500%], records nothing (the
sleeve's own fail-closed rule). Writes <root>/cache/iv_backfill/iron_condor.json; the sleeve merges it under its own
observations (its own measurement wins a session). Needs Alpaca credentials; without them the job reports so."""
import json
import os
from datetime import date, timedelta

DTE_MIN, DTE_MAX = 30, 45


def _sessions_of(closes):
    return sorted(closes)


def contract_for(contracts, session, spot):
    """the old measurement's contract on a session: the nearest expiry 30-45 days out, the strike nearest the spot."""
    d = date.fromisoformat(session)
    calls = []
    for c in contracts or []:
        try:
            if str(c.get("type", "call")) != "call":
                continue
            exp = date.fromisoformat(str(c["expiration_date"])[:10])
            k = float(c["strike_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if DTE_MIN <= (exp - d).days <= DTE_MAX:
            calls.append((exp, k, c["symbol"]))
    if not calls or not spot or spot <= 0:
        return None
    exp = min(e for e, _, _ in calls)
    e, k, occ = min(((e, k, o) for e, k, o in calls if e == exp), key=lambda x: abs(x[1] - spot))
    return {"occ": occ, "expiry": e.isoformat(), "strike": k, "dte": (e - d).days}


def run(client, universe, closes_by_sym, sessions=260):
    """closes_by_sym: {SYM: {session_iso: close}} (the desk's daily bars). Returns {SYM: [[session, iv], ...]}."""
    from ..sleeves.femto import iron_condor as IC
    out = {}
    for sym in universe:
        closes = closes_by_sym.get(sym) or {}
        days = _sessions_of(closes)[-sessions:]
        if not days:
            continue
        first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
        contracts = client.option_contracts_any(sym, expiration_gte=(first + timedelta(days=DTE_MIN)).isoformat(),
                                                expiration_lte=(last + timedelta(days=DTE_MAX)).isoformat(),
                                                typ="call")
        picks = {d: contract_for(contracts, d, closes[d]) for d in days}
        need = sorted({p["occ"] for p in picks.values() if p})
        bars = {}
        for i in range(0, len(need), 100):
            got = client.option_bars(need[i:i + 100], "1Day", start=days[0], end=days[-1])
            for occ, bl in (got or {}).items():
                for b in bl:
                    bars.setdefault(occ, {})[str(b["t"])[:10]] = float(b["c"])
        obs = []
        for d in days:
            p = picks[d]
            px = (bars.get(p["occ"]) or {}).get(d) if p else None
            if not px or px <= 0:
                continue
            iv = IC.implied_vol(px, closes[d], p["strike"], max(p["dte"], 1) / 365.0, IC.RISK_FREE, "call")
            if iv is None or iv <= 0 or iv > 5:
                continue
            obs.append([d, round(float(iv), 6)])
        out[sym] = obs
    return out


def path(root):
    return os.path.join(root, "cache", "iv_backfill", "iron_condor.json")


def write(root, store, now):
    p = path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"at": now, "iv": store}, f)
    os.replace(tmp, p)


def load(root):
    try:
        with open(path(root)) as f:
            return (json.load(f) or {}).get("iv") or {}
    except (OSError, ValueError):
        return {}


def merge(own, backfill, cap=400):
    """the sleeve's store with the backfill under it: one observation per session, its own measurement wins."""
    out = {}
    for sym in set(own or {}) | set(backfill or {}):
        by = {s: v for s, v in (backfill or {}).get(sym) or []}
        by.update({s: v for s, v in (own or {}).get(sym) or []})
        out[sym] = [[s, by[s]] for s in sorted(by)][-cap:]
    return out
