"""Winner Confluence — lean-desk port.

EXTRACTED from the old desk's confluence_sleeve.py. Twin of the
Beaten-Down family machinery (same frozen HOLD9 set, same Decision
#92 gates, same _exit_due) with the confluence SELECTION law:
qualifiers firing >= SELECT_MIN_COUNT (2) of the 9 frozen holding
confluences are selected, ranked by count. The weekly qualifier/
feature pipeline arrives as a core Data product via context.extra.
See ports/confluence.md.

Hold 91 days (13 weeks); sleeve cap 30% of equity; max 10 positions;
cost model 25.5bp/side.

Inputs via context.extra:
  "qualifiers": [{"symbol","close","feat":{...}}]
  "vix": (close, prev, asof_iso, source) | None
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date",
                   "exit_due_date","qty"} | None}}
Bars: daily dicts (exit price hints only).
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
SELECT_MIN_COUNT = 2
MAX_POSITIONS = 10
HOLD_DAYS = 91
SLEEVE_CAP = 0.30
COST_BPS_SIDE = 0.00255
FOMC_2026 = [("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"),
             ("2026-04-28", "2026-04-29"), ("2026-06-16", "2026-06-17"),
             ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"),
             ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09")]

CONFIG = SleeveConfig(
    sleeve_id="confluence", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def score_rules(feat):
    """Names of the frozen HOLD9 confluences firing (verbatim)."""
    hits = []
    for j, rule in enumerate(HOLD9):
        if all(feat.get(k, False) for k in rule):
            hits.append(HOLD9_NAMES[j])
    return hits


def exit_due(pos, today):
    """Verbatim old _exit_due twin (missing due date = due).

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
    """Decision #92 gates, verbatim minus the core-owned desk halt."""
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


class Confluence(BaseSleeve):
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
                        reason="confluence 13-week time exit due"))
        if equity <= 0:
            return intents
        if new_buy_gates(today, extra.get("vix"),
                         extra.get("fomc_dates") or FOMC_2026):
            return intents
        _enh_on = _confluence_enh_enabled(extra)
        table = []
        for q in (extra.get("qualifiers") or []):
            if not isinstance(q, dict) or not q.get("symbol"):
                continue
            hits = score_rules(q.get("feat") or {})
            _raw = len(hits)
            _eff = effective_count(hits)
            _confluence_paired(extra, {
                "exp_id": EXP_ID_CONFLUENCE, "symbol": q["symbol"],
                "raw_count": _raw, "effective_count": _eff,
                "control_selected": _raw >= SELECT_MIN_COUNT,
                "treatment_selected": _eff >= SELECT_MIN_COUNT})
            table.append({"symbol": q["symbol"], "close": q.get("close"),
                          "count": _eff if _enh_on else _raw,
                          "rules": hits})
        selected = [r for r in table if r["count"] >= SELECT_MIN_COUNT]
        selected.sort(key=lambda r: (-r["count"], r["symbol"]))
        room = MAX_POSITIONS - len(book)
        per_name = equity * SLEEVE_CAP / MAX_POSITIONS
        for row in selected:
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
                reason="confluence: rules=%s count=%d >= %d"
                       % (",".join(row["rules"]), row["count"],
                          SELECT_MIN_COUNT)))
            room -= 1
        return intents


def signal(bars, slice_state, context):
    return Confluence().signal(bars, slice_state, context)


# --- ENH 2026-10-24 (Edge IMPROVE-confluence, Group A DEDUCED) ---------
# One counting change: the R5/R6 AVWAP_CAL pair contributes at most 1
# to the selection count (both names still appear in intent reasons).
# Switch: extra["confluence_improve"] {"avwap_pair_one": bool},
# default ON; OFF restores the raw count exactly. Paired records go to
# extra["confluence_exp_journal"]["records"] when served.
EXP_ID_CONFLUENCE = "ENH-CONFLUENCE-20261024"


def _confluence_enh_enabled(extra):
    ov = (extra or {}).get("confluence_improve")
    if isinstance(ov, dict) and "avwap_pair_one" in ov:
        return bool(ov["avwap_pair_one"])
    return True


def effective_count(hits):
    """Selection count with the R5/R6 AVWAP pair counted once."""
    n = len(hits)
    if "R5" in hits and "R6" in hits:
        n -= 1
    return n


def _confluence_paired(extra, record):
    j = (extra or {}).get("confluence_exp_journal")
    if isinstance(j, dict) and isinstance(j.get("records"), list):
        j["records"].append(record)
