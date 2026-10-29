"""Best setups: the desk's entry signals distilled into at most five evidence-ranked, agreement-counted setups.

  Candidates  entry intents (ledger `signals`, kind enter) on US stocks and ETFs, from the passes since the previous
              session's open: one candidate per (symbol, side)
  Eligible    a manifest row of kind trading that is not disabled, never killed_* (research-killed formulations: the
              controls the board must beat), ro_* (research-only proposals) or mon_*
  Gates       liquidity (20-session median dollar volume >= $20M, last close >= $5); freshness (the latest price is not
              more than 1 ATR(14) past the signal price in the setup's direction); conflict (an eligible engine signalled
              the other side). Prices come from the desk's own bar caches and are never published.
  Grade       A paper-proven (the scorecard's evidence: luck excluded); B researched (config/terminal/evidence.json,
              each row cited); C rule-based. A record of 20+ returns with a negative shrunk Sharpe lowers it one step.
  Agreement   distinct engines among the eligible sleeves: the manifest `type`, every Tensor type one engine, at most 3
  Listing     A and B with agreement >= 1, C with agreement >= 2; the board is never padded
  Rank        grade, agreement, the best shrunk Sharpe, dollar volume, the freshest signal, the ticker (no fitted weights)
  Board       at most 5, at most 2 per primary engine; a listed name stays while it passes and ranks within 10
The research behind each rule: docs/research/2026-10-18-terminal/ (research-ranking.md, extract-setups-ranking.md)."""
import json
import os
import re
import statistics
from datetime import datetime

from .. import calendar as cal
from ..util import ET

PLAIN = re.compile(r"^[A-Z]{1,5}([.-][A-Z]{1,2})?$")      # a US stock or ETF ticker; never an option or a pair
EXCLUDED_PREFIXES = ("killed_", "ro_", "mon_")
MAX_BOARD, MAX_PER_ENGINE, KEEP_WITHIN = 5, 2, 10
MIN_DOLLAR_VOLUME, MIN_PRICE, MAX_ATR_RUN = 20e6, 5.0, 1.0
MIN_RETURNS = 20
GRADE_TEXT = {"A": "Paper record: the desk's own forward record, beyond what luck explains",
              "B": "Researched: measured out of sample, or a published and replicated rule; research can be wrong, "
                   "and the desk's forward record is its test",
              "C": "Rule-based: no measured edge yet"}
_GRADE_ORDER = {"A": 0, "B": 1, "C": 2}


def engine_of(row):
    t = (row or {}).get("type") or (row or {}).get("family") or "Other"
    return "Tensor engine" if "tensor" in t.lower() else t


def eligible(sid, row):
    return bool(row) and row.get("status") != "disabled" and row.get("kind", "trading") == "trading" \
        and not sid.startswith(EXCLUDED_PREFIXES)


def _ts(x):
    try:
        return datetime.fromisoformat(str(x)).timestamp()
    except (TypeError, ValueError):
        return None


def _loads(b):
    try:
        return json.loads(b)
    except ValueError:
        return None


def ledger_signals(path, t_cut, chunk=1 << 22, max_bytes=128 << 20):
    """[(pass_at, signals_record)] for the passes that started at or after t_cut. The file is read backwards in chunks
    until a pass_start before t_cut, so the cost follows the window, not the ledger's length; the bytes after the last
    newline are not a record yet (as Ledger.read)."""
    if not os.path.exists(path):
        return []
    kept, stop = [], False
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        look = min(size, 1 << 20)
        f.seek(size - look)
        cut = f.read(look).rfind(b"\n")
        if cut < 0:
            return []
        end = pos = size - look + cut + 1
        carry = b""
        while pos > 0 and not stop and end - pos < max_bytes:
            step = min(chunk, pos)
            pos -= step
            f.seek(pos)
            lines = (f.read(step) + carry).split(b"\n")
            carry = lines.pop(0) if pos > 0 else b""
            for ln in reversed(lines):
                if b'"kind": "pass_start"' in ln:
                    at = _ts((_loads(ln) or {}).get("at"))
                    if at is not None and at < t_cut:
                        stop = True
                        break
                    kept.append((True, at))
                elif b'"kind": "signals"' in ln:
                    r = _loads(ln)
                    if r:
                        kept.append((False, r))
    out, at = [], None
    for is_pass, v in reversed(kept):
        if is_pass:
            at = v
        elif at is not None:
            out.append((at, v))
    return out


def window_start(now):
    """a signal lives through the session after it: before and during a session the window opens at the previous
    session's open (Friday's after-close signals are on Monday's board, and a weekend shows Friday's); after a
    session's close it opens at that session's open (its after-close signals are for the next one)"""
    d = cal._as_date(now)
    if cal.is_trading_day(d) and now >= cal.session_close(d):
        return cal.session_open(d)
    return cal.session_open(cal.prev_trading_day(d))


def load_evidence(path):
    """config/terminal/evidence.json -> [(match, row)]: `match` is a sleeve id, or a prefix ending in '*'"""
    try:
        doc = json.load(open(path))
    except (OSError, ValueError):
        return []
    return [(r["match"], r) for r in doc.get("grades") or [] if r.get("match") and r.get("grade") in ("A", "B")]


def researched(sid, ev_rows):
    for m, r in ev_rows:
        if sid == m or (m.endswith("*") and sid.startswith(m[:-1])):
            return r
    return None


def sleeve_grade(sid, card, ev_rows):
    """(grade, why, shrunk Sharpe or None) for one sleeve"""
    e = (card or {}).get("evidence") or {}
    shrunk = e.get("shrunk_sharpe_ann")
    if e.get("luck_excluded"):
        g, why = "A", GRADE_TEXT["A"]
    else:
        r = researched(sid, ev_rows)
        g, why = ("B", r.get("why") or GRADE_TEXT["B"]) if r else ("C", GRADE_TEXT["C"])
    if (e.get("returns") or 0) >= MIN_RETURNS and shrunk is not None and shrunk < 0:
        g = {"A": "B", "B": "C", "C": None}[g]               # a record that disagrees lowers the grade one step
        why = (why + "; lowered: its paper record is negative after shrinkage") if g else why
    return g, why, shrunk


def _stats(bars):
    """(last close, 20-session median dollar volume, ATR(14)) from ascending daily bars, or None"""
    if len(bars) < 15:
        return None
    dv = [float(b["c"]) * float(b.get("v") or 0) for b in bars[-20:]]
    trs = [max(float(b["h"]) - float(b["l"]), abs(float(b["h"]) - float(p["c"])), abs(float(b["l"]) - float(p["c"])))
           for p, b in zip(bars[-15:-1], bars[-14:])]
    return float(bars[-1]["c"]), statistics.median(dv), sum(trs) / len(trs)


def _latest(daily, hourly):
    """the most recent close the desk's caches hold: an hourly bar's close when it is newer than the daily close"""
    best_t, best = None, None
    if daily:
        d = cal._as_date(float(daily[-1]["t"]))
        best_t, best = cal.session_close(d), float(daily[-1]["c"])
    if hourly:
        t = float(hourly[-1]["t"]) + 3600
        if best_t is None or t > best_t:
            best_t, best = t, float(hourly[-1]["c"])
    return best


class Candidate:
    def __init__(self, symbol, side):
        self.symbol, self.side = symbol, side
        self.sleeves = {}          # sid -> {"at", "price", "reason"} (latest signal of that sleeve)
        self.first_at = None

    def add(self, sid, at, it):
        self.sleeves[sid] = {"at": at, "price": it.get("price"), "reason": it.get("reason") or ""}
        self.first_at = at if self.first_at is None else min(self.first_at, at)

    @property
    def last_at(self):
        return max(v["at"] for v in self.sleeves.values())


def candidates(signal_recs):
    """{(symbol, side): Candidate} and the count of entry signals seen"""
    out, n = {}, 0
    for at, r in signal_recs:
        sid = r.get("sleeve")
        for it in r.get("intents") or []:
            if it.get("kind") != "enter" or it.get("asset") != "equity":
                continue
            sym, side = str(it.get("symbol") or ""), it.get("side")
            if not PLAIN.match(sym) or side not in ("long", "short"):
                continue
            n += 1
            out.setdefault((sym, side), Candidate(sym, side)).add(sid, at, it)
    return out, n


def assess(cands, rows, cards, ev_rows, daily, hourly):
    """every candidate with eligible sleeves, assessed: [{key, symbol, side, grade, ..., passed, why_not}]"""
    out = []
    by_symbol = {}
    for (sym, side), c in cands.items():
        el = {sid: v for sid, v in c.sleeves.items() if eligible(sid, rows.get(sid))}
        if el:
            by_symbol.setdefault(sym, set()).add(side)
    for (sym, side), c in cands.items():
        el = {sid: v for sid, v in c.sleeves.items() if eligible(sid, rows.get(sid))}
        if not el:
            continue
        graded = {sid: sleeve_grade(sid, cards.get(sid), ev_rows) for sid in el}
        graded = {sid: g for sid, g in graded.items() if g[0] is not None}
        a = {"key": f"{sym}:{side}", "symbol": sym, "side": side, "sleeves": el, "graded": graded,
             "engines": sorted({engine_of(rows.get(sid)) for sid in graded}), "first_at": c.first_at,
             "last_at": max(v["at"] for v in el.values()), "passed": False, "why_not": None}
        out.append(a)
        if not graded:
            a["why_not"] = "Every agreeing strategy's paper record is negative"
            continue
        best = min(graded, key=lambda s: (_GRADE_ORDER[graded[s][0]], -(graded[s][2] or -1e9), s))
        a.update(grade=graded[best][0], grade_why=graded[best][1], best=best, shrunk=graded[best][2],
                 agreement=min(3, len(a["engines"])), primary_engine=engine_of(rows.get(best)))
        if len(by_symbol.get(sym, ())) > 1:
            a["why_not"] = "Conflicted: another engine signalled the other side"
            continue
        st = _stats(daily.get(sym) or [])
        if st is None:
            a["why_not"] = "Not enough price history in the desk's cache"
            continue
        close, dv, atr = st
        a["dollar_volume"] = dv
        if close < MIN_PRICE or dv < MIN_DOLLAR_VOLUME:
            a["why_not"] = "Below the liquidity bar"
            continue
        last = _latest(daily.get(sym), hourly.get(sym))
        ref = el[best].get("price")
        a["_last"], a["_atr"] = last, atr          # internal: never published
        if ref and last and atr > 0:
            run = (last - float(ref)) / atr * (1 if side == "long" else -1)
            if run > MAX_ATR_RUN:
                a["why_not"] = "Ran more than 1 ATR past its signal"
                continue
        if a["grade"] == "C" and a["agreement"] < 2:
            a["why_not"] = "Rule-based with one engine: listed only when independent engines agree"
            continue
        a["passed"] = True
    return out


def rank_key(a):
    return (_GRADE_ORDER[a["grade"]], -a["agreement"], -(a["shrunk"] if a.get("shrunk") is not None else -1e9),
            -(a.get("dollar_volume") or 0), -(a.get("last_at") or 0), a["symbol"])


def board(assessed, prev_keys):
    """(listed, ranked): the ranked passing candidates and the board. A name already listed stays while it passes and
    ranks within KEEP_WITHIN; new names fill the remaining places in rank order; at most MAX_PER_ENGINE per primary
    engine and MAX_BOARD in all"""
    ranked = sorted((a for a in assessed if a["passed"]), key=rank_key)
    for i, a in enumerate(ranked, 1):
        a["rank"] = i
    keep = [a for a in ranked if a["key"] in prev_keys and a["rank"] <= KEEP_WITHIN]
    listed, per_engine = [], {}
    for a in keep + [a for a in ranked if a not in keep]:
        if len(listed) >= MAX_BOARD:
            break
        if per_engine.get(a["primary_engine"], 0) >= MAX_PER_ENGINE:
            continue
        listed.append(a)
        per_engine[a["primary_engine"]] = per_engine.get(a["primary_engine"], 0) + 1
    listed.sort(key=rank_key)
    return listed, ranked


_TOKENS = [(re.compile(r"\bwilder_rsi(\d+)\b"), r"RSI(\1)"), (re.compile(r"\brsi_?(\d+)\b"), r"RSI(\1)"),
           (re.compile(r"\bsma_?(\d+)\b"), r"\1-day average"), (re.compile(r"\bema_?(\d+)\b"), r"\1-day EMA"),
           (re.compile(r"<="), "≤"), (re.compile(r">="), "≥"), (re.compile(r"\bclose\s*>\s*(?=\d+-day)"), "close above the "),
           (re.compile(r"\bclose\s*<\s*(?=\d+-day)"), "close below the "), (re.compile(r"\s>\s"), " above "),
           (re.compile(r"\s<\s"), " below "), (re.compile(r"\s+"), " ")]


def plain_reason(reason):
    """a sleeve's entry reason in plain words: its rule after the title, with indicator tokens spelled out"""
    r = str(reason or "")
    r = r.split(":", 1)[1] if ":" in r[:80] else r
    for pat, rep in _TOKENS:
        r = pat.sub(rep, r)
    r = r.strip(" .;")
    return (r[:157] + "...") if len(r) > 160 else r


def plan_from(rules, avg, side):
    """{text, stop_pct, target_pct, sessions} from a position's exit_rules ([[kind, value], ...]); absolute levels are
    turned into % from the entry price, which is never published"""
    stop = target = sessions = None
    sign = 1 if side == "long" else -1
    for k, v in rules or []:
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if k == "stop_pct":
            stop = -sign * abs(v)
        elif k == "target_pct":
            target = sign * abs(v)
        elif k in ("time_sessions", "time_sessions_close"):
            sessions = int(v)
        elif k == "stop" and avg:
            stop = (v / avg - 1) * 100
        elif k == "target" and avg:
            target = (v / avg - 1) * 100
        elif k == "stop_dist" and avg:
            stop = -sign * abs(v) / avg * 100
    r = round(abs(target) / abs(stop), 1) if stop and target is not None else None
    parts = []
    if stop is not None:
        parts.append(f"Stop {_pct(stop)}")
    if target is not None:
        parts.append(f"Target {_pct(target)}" + (f" ({_num(r)}R)" if r is not None else ""))
    if sessions:
        parts.append(f"up to {sessions} session{'s' if sessions != 1 else ''}")
    text = " · ".join(parts) if parts else "Exits on its own signal"
    if parts and stop is None and target is None:
        text = "Exits on its own signal, or after " + parts[0][len("up to "):]
    return {"text": text, "stop_pct": None if stop is None else round(stop, 1),
            "target_pct": None if target is None else round(target, 1), "sessions": sessions, "r": r}


def entry(ref, last, atr, side):
    """{entry_pct, now_pct}: the band a listed setup can still be entered in (the board's MAX_ATR_RUN past the signal
    price, in %: + above for a long, - below for a short) and where the latest close sits against the signal price, in
    %; None without a signal price, a close or an ATR. Neither price is published"""
    try:
        ref, last, atr = float(ref), float(last), float(atr)
    except (TypeError, ValueError):
        return None
    if ref <= 0 or atr <= 0:
        return None
    band = MAX_ATR_RUN * atr / ref * 100
    return {"entry_pct": round(band if side == "long" else -band, 1), "now_pct": round((last / ref - 1) * 100, 1)}


def plan_words(plan, ent, until, side):
    """(line, sentence): the card's plan line and the plan in one sentence, in % and ATR only. until: the call's last
    session (desk/terminal/calls.py: the plan's sessions, else 5)"""
    day = until.strftime("%a %b ") + str(until.day)
    long_ = side == "long"
    buy = None
    if ent:
        buy = (f"Buy up to {_pct(ent['entry_pct'])} above the signal" if long_ else
               f"Short down to {_pct(ent['entry_pct'])} below the signal")
    line = " · ".join(([buy, "now " + _pct(ent["now_pct"])] if ent else []) + [("through " if ent else "Through ") + day])
    st, tg, n = plan.get("stop_pct"), plan.get("target_pct"), plan.get("sessions")
    parts = [buy] if buy else []
    if tg is not None:
        parts.append(f"target {_pct(tg)}" + (f" ({_num(plan['r'])}R)" if plan.get("r") is not None else "") + f" by {day}")
    if st is not None:
        atr_pct = abs(ent["entry_pct"]) / MAX_ATR_RUN if ent else None
        parts.append(f"out at {_pct(st)}" + (f" ({_num(round(abs(st) / atr_pct, 1))} ATR)" if atr_pct else ""))
    if st is None and tg is None:
        parts.append("the strategy exits on its own signal" +
                     (f" or after {n} session{'s' if n != 1 else ''}" if n else ""))
    if tg is None:
        parts.append(f"this call is scored through {day}")
    sentence = "; ".join(parts) + "."
    return line, sentence[0].upper() + sentence[1:]


def _num(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def _pct(x):
    return ("+" if x > 0 else "−" if x < 0 else "") + f"{abs(x):.1f}%".replace(".0%", "%")


def lower_first(name):
    """'Mean reversion and pullback' -> 'mean reversion and pullback'; an acronym ('ETF and ...') stays"""
    return name if len(name) < 2 or name[1].isupper() else name[0].lower() + name[1:]


def et_iso(ts):
    return datetime.fromtimestamp(float(ts), tz=ET).isoformat(timespec="seconds")
