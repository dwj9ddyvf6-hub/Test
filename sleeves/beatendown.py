"""Beaten-Down — lean-desk port.

EXTRACTED from the old desk's beatendown_sleeve.py. The frozen HOLD9
rule set, score_rules, is_beaten_down and the Decision #92
new_buy_gates are ported verbatim (the risk_gate desk-halt leg is core
Risk's now); the weekly qualifier/feature pipeline (M2 study outputs)
arrives as a core Data product via context.extra. See
ports/beatendown.md.

Selection law (frozen, pre-reg PRE_REG_BEATENDOWN_HOLDOUT.md): the
population = M2 qualifiers whose signal-week close <= 0.80 x trailing
52-week high (BEAT_LO52). There is NO rule-count minimum — the 9-rule
count is the ranker (timing signal). Hold 91 days (13 weeks); sleeve
cap 30% of equity; max 10 positions; cost model 25.5bp/side.
_exit_due ported verbatim: a position with a MISSING exit_due_date is
DUE (2026-10-12 fix — never held forever).

Inputs via context.extra:
  "qualifiers": [{"symbol","close","wcloses":[...],"feat":{...}}]
  "vix": (close, prev, asof_iso, source) | None
  "fomc_dates": optional override of FOMC_2026
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date",
                   "exit_due_date","qty"} | None}}
Bars: daily dicts (used for exit price hints only).
"""
from datetime import date, timedelta

from core.sleeve import BaseSleeve, ExitRule, Intent, SleeveConfig

HOLD9 = [
    ("E_WEEK_BIGRANGE", "X_SECT_LEAD", "Q_LAM_HIGH"),
    ("E_ENR_EXTENSION", "X_DOLLAR_WEAK", "Q_LAM_HIGH"),
    ("X_SECT_LEAD", "M_DAILY_RANGE_HI", "Q_LAM_HIGH"),
    ("E_FAST_BULL", "X_SECT_LEAD", "Q_LAM_HIGH"),
    ("E_AVWAP_CAL_ABOVE", "X_SECT_LEAD", "Q_LAM_HIGH"),
    ("E_AVWAP_CAL_FAR", "X_SECT_LEAD", "Q_LAM_HIGH"),
    ("E_WEEK_BIGRANGE", "X_DOLLAR_WEAK", "Q_LAM_HIGH"),
    ("E_VOTES_NET_HIGH", "X_SECT_LEAD", "Q_LAM_HIGH"),
    ("X_SECT_LEAD", "P_IND_TREND", "Q_LAM_HIGH"),
]
HOLD9_NAMES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"]
CUT_LAM = 0.17647058823529413
BEAT_LO52_CUT = 0.80
MAX_POSITIONS = 10
HOLD_DAYS = 91
SLEEVE_CAP = 0.30
COST_BPS_SIDE = 0.00255
FOMC_2026 = [("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"),
             ("2026-04-28", "2026-04-29"), ("2026-06-16", "2026-06-17"),
             ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"),
             ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09")]

CONFIG = SleeveConfig(
    sleeve_id="beatendown", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def score_rules(feat):
    """Names of the frozen HOLD9 confluences firing on a feature dict."""
    hits = []
    for j, rule in enumerate(HOLD9):
        if all(feat.get(k, False) for k in rule):
            hits.append(HOLD9_NAMES[j])
    return hits


def is_beaten_down(q):
    """Verbatim: close <= 0.80 x trailing 52-week high on the
    qualifier's weekly closes; fail-closed on short/bad data."""
    try:
        closes = [c for c in (q.get("wcloses") or []) if c]
        if len(closes) < 52:
            return False
        hi52 = max(closes[-52:])
        px = q.get("close") or closes[-1]
        return hi52 > 0 and px <= BEAT_LO52_CUT * hi52
    except Exception:
        return False


def exit_due(pos, today):
    """Verbatim old _exit_due (missing due date = due; non-string due
    date on a truthy value = not due, the BC14E-7 guard).

    XT-1 (2026-10-16): the old desk BOOKED exit_due_date at fill
    (entry + HOLD_DAYS calendar days); the lean core never writes the
    field, so every lean fill read as due and exited on the next
    pass. When the stored field is absent, derive the date the old
    booker would have written from the record's entry_date — the
    stored-first, derive-when-missing pattern sleeves/phoenix.py
    uses. A record with neither field keeps the verbatim law."""
    if not isinstance(pos, dict):
        return False
    due = pos.get("exit_due_date")
    if not due and pos.get("entry_date"):
        try:
            due = (date.fromisoformat(str(pos["entry_date"])[:10])
                   + timedelta(days=HOLD_DAYS)).isoformat()
        except (TypeError, ValueError):
            due = None
    if due and not isinstance(due, str):
        return False
    return (not due) or due <= today


def new_buy_gates(today_iso, vix, fomc=FOMC_2026):
    """Decision #92 gates (desk conventions only; panic gates removed
    by ruling; desk halt is core Risk's). Returns [(gate, detail)]."""
    blocks = []
    today = date.fromisoformat(today_iso)
    dec_weekdays = []
    d = date(today.year, 12, 1)
    while d.month == 12:
        if d.weekday() < 5:
            dec_weekdays.append(d.isoformat())
        d += timedelta(days=1)
    if today_iso in dec_weekdays[-5:]:
        blocks.append(("year_end", "last 5 sessions of the year"))
    for d1s, d2s in fomc:
        d1 = date.fromisoformat(d1s)
        prev = d1 - timedelta(days=1)
        while prev.weekday() >= 5:
            prev -= timedelta(days=1)
        if today_iso in (prev.isoformat(), d1s, d2s):
            blocks.append(("fomc", "FOMC blackout %s/%s/%s"
                           % (prev.isoformat(), d1s, d2s)))
            break
    if not vix:
        blocks.append(("vix_unknown", "VIX unavailable; buys wait"))
        return blocks
    vclose, _vprev, vasof, vsrc = vix
    if vclose is None:
        blocks.append(("vix_unknown", "VIX unavailable (%s); buys wait" % vsrc))
    else:
        stale = False
        try:
            asof = date.fromisoformat(str(vasof)[:10])
            if (today - asof).days > 4:
                stale = True
        except (TypeError, ValueError):
            stale = True
        if stale:
            blocks.append(("vix_stale", "VIX as-of %s is stale (%s); buys wait"
                           % (vasof, vsrc)))
    return blocks


class BeatenDown(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        equity = float(context.equity or 0.0)
        today = context.session
        intents = []
        book = {s: (state.get(s) or {}).get("position")
                for s in state if (state.get(s) or {}).get("position")}
        for sym, p in book.items():
            if exit_due(p, today):
                qty = int(float(p.get("qty") or 0))
                if qty > 0:
                    bl = bars.get(sym) or []
                    px = round(float(bl[-1]["c"]), 2) if bl else None
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty, price_hint=px,
                        reason="beatendown 13-week time exit due"))
        if equity <= 0:
            return intents
        if new_buy_gates(today, extra.get("vix"),
                         extra.get("fomc_dates") or FOMC_2026):
            return intents
        quals = [q for q in (extra.get("qualifiers") or [])
                 if isinstance(q, dict) and q.get("symbol")]
        table = []
        _enh_on = _beatendown_enh_enabled(extra)
        for q in quals:
            if not is_beaten_down(q):
                continue
            hits = score_rules(q.get("feat") or {})
            _beatendown_paired(extra, {
                "exp_id": EXP_ID_BEATENDOWN, "symbol": q["symbol"],
                "hold9_count": len(hits),
                "control": "candidate",
                "treatment": ("refused_hold9_zero"
                              if _enh_on and len(hits) == 0 else "candidate")})
            if _enh_on and len(hits) == 0:
                continue  # ENH: zero-evidence candidates never rank
            table.append({"symbol": q["symbol"], "close": q.get("close"),
                          "count": len(hits), "rules": hits})
        table.sort(key=lambda r: (-r["count"], r["symbol"]))
        room = MAX_POSITIONS - len(book)
        per_name = equity * SLEEVE_CAP / MAX_POSITIONS
        for row in table:
            if room <= 0:
                break
            sym = row["symbol"]
            if sym in book:
                continue
            px = row["close"]
            if not px or px <= 0:
                bl = bars.get(sym) or []
                if not bl:
                    continue
                px = float(bl[-1]["c"])
            qty = int(per_name // px)
            if qty < 1:
                # OBS-1 (ruling 2026-10-22): the sleeve's own
                # sizing is the law — a budget that buys
                # nothing takes no position. No forced floor.
                continue
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(float(px), 2),
                exit_rules=(ExitRule("time_bars", float(HOLD_DAYS)),),
                reason="beatendown: rules=%s count=%d (ranker, no minimum)"
                       % (",".join(row["rules"]) or "-", row["count"])))
            room -= 1
        return intents


def signal(bars, slice_state, context):
    return BeatenDown().signal(bars, slice_state, context)


# --- ENH 2026-10-24 (Edge IMPROVE-beatendown, Group B LEAP) -------------
# One added refusal: skip any candidate whose HOLD9 count is 0 (no
# confirming confluence at all). Switch: extra["beatendown_improve"]
# {"hold9_min_one": bool}, default ON; OFF restores the pre-change rule
# exactly (count-0 candidates rank as before). Control (pre-change)
# decisions are shadow-scored on every qualifier and appended as paired
# records to extra["beatendown_exp_journal"]["records"] when served.
EXP_ID_BEATENDOWN = "ENH-BEATENDOWN-20261024"


def _beatendown_enh_enabled(extra):
    ov = (extra or {}).get("beatendown_improve")
    if isinstance(ov, dict) and "hold9_min_one" in ov:
        return bool(ov["hold9_min_one"])
    return True


def _beatendown_paired(extra, record):
    j = (extra or {}).get("beatendown_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)
