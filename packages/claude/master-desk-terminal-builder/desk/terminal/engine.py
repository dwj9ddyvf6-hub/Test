"""The analysis engine on the cards (docs/research/2026-10-25-engine/DESIGN.md; the UI review's section 5): the
engine's forward screen read beside the desk's read. It is context and never a vote (PROGRAM2.md Addendum 2-19b): no
take, conviction, plan or board place moves on it, except that its momentum rank breaks an exact tie in the board's
order (board.rank_key, 2-19b's TILT).

  latest(root, on_or_before)  the newest screen the engine wrote for a session on or before the given one, through the
                              engine's own reader (desk/analysis/store): {"as_of", "rows": {symbol: row}}, the rows
                              ranked (ranks); None when there is none or it cannot be read
  ranks(rows)                 each scored row's momentum rank, mom (mom6_pct, its share at or below within session x
                              tier, as 0-100), and loser-risk rank, risk (the share of its tier's scored names whose P
                              is at or under its own, as 0-100: higher is riskier)
  block(screen, sym, as_of, sessions, by)
                              setups[] and watching[] engine = {as_of, mom, risk, em, em_by, status} and, when the
                              screen is from an earlier session than the read, note = "engine as of <day>":
                                em      the typical move in % over the plan's own horizon, 100 x 0.9 x sigma_mean x
                                        sqrt(sessions) (sigma_mean: the screen's HAR forecast of the daily volatility of
                                        the next 20 sessions); em_by the plan's horizon date
                                status  the forward test's week (FB2 counts from 2026-10-27)
                              None for a name the screen does not score, or a screen more than STALE sessions older
  vetoed(screen, sym, as_of)  the tier of a name the screen vetoes where the veto is in force (veto_applied: small,
                              micro and nano), when the card's engine line shows (block's rule); else None: the card's
                              caution (cautions.veto)
  at_listing(screen, sym, pub)
                              what a call keeps when its card is listed: the card's engine line with the screen's tier
                              and veto (veto_applied), so the forward record can split calls by them; None without a line
  doc(screen, prev)           engine.json, published beside the edition: {as_of, n, cols, rows}, one row per scored
                              name [sym, mom, risk, em, dmom, drisk, tier, veto]: em over the screen's own 20-session
                              horizon, dmom and drisk against the screen before it (None without one), tier liquid,
                              small, micro or nano, veto true only where the veto is in force (veto_applied: small,
                              micro and nano; a liquid name's P is recorded, never applied)
Nothing here reads the network or writes a file the engine owns; a screen that cannot be read costs the cards their
engine line, never the edition."""
import json
import math
import os

from .. import calendar as cal
from ..data.hub import alpaca_stock_symbol
from .read import words as W

STALE = 5                     # a screen more than five sessions older than the read is not shown
HAR_STOP = 0.9                # a range or stop taken from the HAR volatility uses HAR x0.9 (graded finding, EVIDENCE.md)
HORIZON = 20                  # sigma_mean's own horizon: engine.json's typical move
COLS = ["sym", "mom", "risk", "em", "dmom", "drisk", "tier", "veto"]
TIERS = ("liquid", "small", "micro", "nano")
ALLOWED = {"": {"as_of", "n", "cols", "rows"}}
BLOCK = {"as_of", "mom", "risk", "em", "em_by", "status", "note"}


def ranks(rows):
    """{symbol: row with "mom" and "risk"} for every scored row of one screen"""
    from ..analysis import engine_score_ref as ref          # the screen's own share rule (and the job's process only)
    scored = [r for r in rows if r.get("scored") and r.get("tier")]
    risk = {}
    for t in ref.TIERS:
        risk.update(ref.share_at_or_below({r["sym"]: r.get("p") for r in scored if r["tier"] == t}))
    out = {}
    for r in scored:
        m, k = r.get("mom6_pct"), risk.get(r["sym"])
        out[r["sym"]] = dict(r, mom=None if m is None else round(100 * m), risk=None if k is None else round(100 * k))
    return out


_SEEN = {}                    # (root, session) -> the ranked screen: a screen is written once and never changes


def latest(root, on_or_before):
    """the newest screen of a session on or before `on_or_before` (ISO), ranked, or None"""
    from ..analysis import store
    try:
        sessions = sorted(s for s in store.written(root) if s <= str(on_or_before))
        if not sessions:
            return None
        key = (os.path.abspath(root), sessions[-1])
        if key not in _SEEN:
            doc = store.read(root, sessions[-1])
            _SEEN.clear()                                    # one screen kept: the job reads the newest each time
            _SEEN[key] = {"as_of": doc.get("session") or sessions[-1], "rows": ranks(doc.get("rows") or ())}
        return _SEEN[key]
    except (OSError, ValueError, EOFError):
        return None


def previous(root, screen):
    """the screen of the session before `screen`'s, ranked, or None"""
    if not screen:
        return None
    d = cal.prev_trading_day(cal._as_date(screen["as_of"])).isoformat()
    return latest(root, d)


def _key(sym):
    return alpaca_stock_symbol(str(sym or "").strip().upper())


def mom_of(screen, sym):
    """a name's momentum rank on the screen, or None"""
    row = (screen or {}).get("rows", {}).get(_key(sym)) if screen else None
    return row["mom"] if row else None


def tier(screen, sym, bars=None):
    """a name's tier, liquid, small, micro or nano: the screen's when it scored the name, else the spec's own rule
    (engine_score_ref.tier_of) on the read's bars (dv20, the median of close x volume over 20 sessions, which the split
    adjustment leaves as it was; the close, the raw close since the name's last split); None below the rule's floor
    or with fewer than 20 bars"""
    row = (screen or {}).get("rows", {}).get(_key(sym)) if screen else None
    if row and row.get("tier") in TIERS:
        return row["tier"]
    bars = [b for b in bars or () if b.get("c") is not None][-20:]
    if len(bars) < 20:
        return None
    from ..analysis import engine_score_ref as ref
    closes, vols = [float(b["c"]) for b in bars], [float(b.get("v") or 0) for b in bars]
    return ref.tier_of(closes[-1], ref.dollar_volume_20(closes, vols))


def status(as_of):
    """the forward test's week at a screen's session, in a few words"""
    from ..analysis import FB2_START
    if as_of < FB2_START:
        return "forward test from " + W.short_day(FB2_START)
    return f"forward test · week {cal.trading_days_between(FB2_START, as_of) // 5 + 1}"


def _row(screen, sym, as_of):
    """(the screen's row of a name, how many sessions the screen is older than the read of session as_of), or None:
    no screen or row, a screen from after the read, or one more than STALE sessions older"""
    if not screen or not as_of:
        return None
    row = screen["rows"].get(_key(sym))
    if not row or screen["as_of"] > as_of:
        return None
    lag = cal.trading_days_between(screen["as_of"], as_of)
    return None if lag > STALE else (row, lag)


def block(screen, sym, as_of, sessions=None, by=None):
    """the card's engine line (the module docstring), or None"""
    got = _row(screen, sym, as_of)
    if not got:
        return None
    row, lag = got
    out = {"as_of": screen["as_of"], "mom": row["mom"], "risk": row["risk"], "status": status(screen["as_of"])}
    sigma = row.get("sigma_mean")
    if sigma and sessions:
        out.update(em=round(100.0 * HAR_STOP * sigma * math.sqrt(sessions), 1), em_by=by)
    if lag:
        out["note"] = "engine as of " + W.short_day(screen["as_of"])
    return out


def vetoed(screen, sym, as_of):
    """the tier of a vetoed name where the veto is in force, when its engine line shows (the module docstring)"""
    got = _row(screen, sym, as_of)
    return got[0].get("tier") if got and got[0].get("veto_applied") else None


def at_listing(screen, sym, pub):
    """what the call of a newly listed card keeps of the engine (the module docstring), or None"""
    pl = pub.get("plan") or {}
    line = block(screen, sym, pub.get("as_of"), pl.get("sessions"), pl.get("by"))
    if not line:
        return None
    row = _row(screen, sym, pub["as_of"])[0]
    return dict(line, tier=row.get("tier"), veto=bool(row.get("veto_applied")))


def doc(screen, prev=None):
    """engine.json (the module docstring), or None without a screen"""
    if not screen:
        return None
    before = (prev or {}).get("rows") or {}
    rows = []
    for sym, r in screen["rows"].items():
        p = before.get(sym) or {}
        d = (lambda k: None if r.get(k) is None or p.get(k) is None else r[k] - p[k])  # noqa: E731
        em = round(100.0 * HAR_STOP * r["sigma_mean"] * math.sqrt(HORIZON), 1) if r.get("sigma_mean") else None
        rows.append([sym, r["mom"], r["risk"], em, d("mom"), d("risk"), r["tier"], bool(r.get("veto_applied"))])
    rows.sort(key=lambda x: (x[1] is None, -(x[1] or 0), x[0]))
    return validate({"as_of": screen["as_of"], "n": len(rows), "cols": list(COLS), "rows": rows})


def published(root, now, last_session=None):
    """engine.json for the edition at `now`: the newest screen of a session on or before it, when it is no more than
    STALE sessions older than the latest session the desk's prices hold (last_session, the market read's as_of);
    else None"""
    scr = latest(root, cal._as_date(now).isoformat())
    if not scr or (last_session and cal.trading_days_between(scr["as_of"], last_session) > STALE):
        return None
    return doc(scr, previous(root, scr))


def path(root):
    """engine.json's place in the desk's cache, from where the publisher copies it beside the edition"""
    return os.path.join(root, "cache", "terminal", "engine.json")


def save(root, d):
    """write engine.json (validated), or remove it without a screen to show: a stale file is never published"""
    p = path(root)
    if d is None:
        if os.path.exists(p):
            os.remove(p)
        return None
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:              # compact, as the edition is published
        json.dump(validate(d), f, separators=(",", ":"))
    os.replace(tmp, p)
    return p


def validate(d):
    """raise ValueError unless d is engine.json's shape exactly: its four keys, its columns, and rows of a symbol, five
    numbers or nulls, a tier and a true or false"""
    if not isinstance(d, dict) or set(d) != ALLOWED[""]:
        raise ValueError("engine.json: keys")
    if d["cols"] != COLS or not isinstance(d["rows"], list) or d["n"] != len(d["rows"]):
        raise ValueError("engine.json: columns or count")
    for r in d["rows"]:
        if not (isinstance(r, list) and len(r) == len(COLS) and isinstance(r[0], str) and
                all(v is None or (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v))
                    for v in r[1:6]) and r[6] in TIERS and isinstance(r[7], bool)):
            raise ValueError(f"engine.json: row {r!r:.80}")
    return d
