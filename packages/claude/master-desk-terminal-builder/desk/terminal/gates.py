"""The gate rail and the market gate as pure functions (owner, 2026-10-26: "Execute all", PLAN.md Phase 0/1).

REUSABLE for the new Best Setups picker (owner, 2026-10-27: the old board is retired and nothing here is wired into it):
evaluate(setup, badge, banner, today) needs only a setup dict with form, status, now_pct, close, as_of, avgs, plan
{zone_lo, zone_hi, trigger, out, t1, r}, optional earnings/fear/lens; record_label(closed, hits) is the small-n words.

Every Best Setups card carries `gates`: each condition of the trade as one sentence with its value, a check (True,
False, or None when the data is missing: a missing value never passes) and a tag. The card says Buy only when every
required condition passes; otherwise Watch only, with the first missing condition and, where a price completes it,
that price (as a % from the card's close, formatted on the page by the order-tick rules). A card whose levels do not
add up (coherence.problems) reads No trade.

Market gate (owner's defaults, 2026-10-26):
  Risk-on                          the market check passes; size Full size
  Mixed                            passes; a pullback Full size, anything else Smaller
  Risk-off                         fails, unless the setup is fear-qualified: a pullback or a buy-in-zone ('now') in
                                   an uptrend whose fear day came (fear.status 'came') or on a broad fear day today
                                   (QQQ and SPY red: the edition's banner); then it passes, size Smaller
  no market read                   not required; size Smaller (an unknown market is never Full size)
The record is untouched: a card's `action` and its call stay the record's; `gates` is the face's instruction."""
from . import coherence

R_MIN = coherence.R_MIN
STAGES = ("Qualify", "Conviction", "Trigger", "Validate")      # read/lenses.py, Leadr's four stages
SIZES = ("Full size", "Smaller", "Watch only", "No trade")
PUBLIC = {"verdict", "size", "missing", "need", "rail", "stage"}
RAIL_KEYS = {"tag", "sentence", "value", "pass", "need"}
NEED_KEYS = {"pct", "role", "words"}
STAGE_KEYS = {"at", "n", "word", "c8"}


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _pct(v):
    return f"{v:+.1f}%".replace("-", "−")


def _row(tag, text, ok, need=True, value=None):
    """one check: {tag, sentence, value, pass, need}: the generic shape web/terminal/gates.js renders"""
    return {"tag": tag, "sentence": text, "value": value, "pass": ok, "need": need}


def record_label(closed, hits):
    """the record's headline in words, honest about a small sample: under 30 closed calls it says so"""
    if not closed:
        return "No closed calls yet"
    if closed < 30:
        return f"{hits} of {closed} won · too few to judge; first read at 30"
    return f"{round(100 * hits / closed)}% won of {closed}"


def _trend(s):
    a, c = s.get("avgs") or {}, s.get("close")
    m50, m200 = a.get("sma50"), a.get("sma200")
    if not (_num(c) and _num(m50) and _num(m200)) or m50 <= 0:
        return _row("Trend", "Trend: no 50- and 200-day averages to check", None), False
    up = c > m50 and m50 > m200
    return _row("Trend", f"Price {_pct((c / m50 - 1) * 100)} vs its 50-day; 50-day "
                         f"{'above' if m50 > m200 else 'below'} the 200-day", up), up


def _entry(s):
    """(row, need): the entry condition, and the price that completes it when it fails"""
    p, now = s.get("plan") or {}, s.get("now_pct")
    if s.get("status") not in (None, "waiting"):
        return _row("Trigger", "Bought: the entry is filled", True), None
    now = now if _num(now) else 0.0
    trig = p.get("trigger")
    if _num(trig):
        ok = now >= trig
        return _row("Trigger", f"Daily close above {_pct(trig)} (now {_pct(now)})", ok), \
            None if ok else {"pct": trig, "role": 1, "words": "Close above"}
    lo, hi = p.get("zone_lo"), p.get("zone_hi")
    if not (_num(lo) and _num(hi)):
        return _row("Pullback", "Buy range: missing an end", None), None
    ok = now <= hi
    return _row("Pullback", f"Price {_pct(now)} vs buy range {_pct(lo)} to {_pct(hi)}", ok), \
        None if ok else {"pct": hi, "role": -1, "words": "Pull back to"}


def evaluate(s, badge, banner, today):
    """{verdict, size, missing, need, rail, stage} for one setup card"""
    p = s.get("plan") or {}
    rail = []
    trend_row, up = _trend(s)
    rail.append(trend_row)
    entry_row, need = _entry(s)
    rail.append(entry_row)
    r = p.get("r")
    rail.append(_row("Risk", f"Reward to risk {r:.1f} to 1 (at least {R_MIN:.1f})" if _num(r)
                     else "Reward to risk: not measured", (r >= R_MIN) if _num(r) else None))
    e = s.get("earnings")
    rail.append(_row("Risk", f"Earnings {e} inside the plan" if e else "No earnings report inside the plan", not e))
    f = s.get("fear") or {}
    fear_today = bool(banner and banner.get("both") and banner.get("date") and banner["date"] == s.get("as_of"))
    pullback = s.get("form") in ("pullback", "now")
    fear_ok = pullback and up and (f.get("state") == "came" or fear_today)
    word = (badge or {}).get("word")
    if word == "Risk-off":
        rail.append(_row("Market", "Market Risk-off, but a fear-day pullback qualifies" if fear_ok else
                         f"Market Risk-off: {(badge or {}).get('line') or 'its checks fail'}; "
                         "only a fear-day pullback buys", fear_ok))
        rail.append(_row("Fear", "Broad fear day today: QQQ and SPY red" if fear_today else
                         (f.get("label") or "No fear-day status"), f.get("state") == "came" or fear_today, need=False))
    elif word in ("Risk-on", "Mixed"):
        if f:
            rail.append(_row("Fear", f.get("label") or "Fear day", f.get("state") == "came", need=False))
        rail.append(_row("Market", f"Market {word}", True))
    else:
        rail.append(_row("Market", "Market read unavailable", None, need=False))
    bad = coherence.problems(s, today, "setup")
    if bad:
        verdict, missing, need = "No trade", "; ".join(bad), None
    else:
        fail = next((x for x in rail if x["need"] and x["pass"] is not True), None)
        if fail:
            verdict, missing = "Watch only", fail["sentence"]
            if fail is not entry_row:
                need = None
        else:
            verdict, missing, need = "Buy", None, None
    if verdict != "Buy":
        size = verdict
    elif word == "Risk-on":
        size = "Full size"
    elif word == "Mixed" and s.get("form") == "pullback":
        size = "Full size"
    else:
        size = "Smaller"
    L = s.get("lens") or {}
    stage = {"at": STAGES.index(L["stage"]), "n": L.get("n"), "word": L.get("word"), "c8": L.get("c8")} \
        if L.get("stage") in STAGES else None
    return {"verdict": verdict, "size": size, "missing": missing, "need": need, "rail": rail, "stage": stage}


def apply(edition, today):
    """every setup card gets its gates (in place); returns the edition"""
    badge = (edition.get("market") or {}).get("badge")
    for s in edition.get("setups") or []:
        s["gates"] = evaluate(s, badge, edition.get("fear"), today)
    return edition
