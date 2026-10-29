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

Master-desk restoration (the femto port ranked on every call, sized 3% per
name off the qualifier close, held 91 SESSIONS via time_bars and dropped
the fill law): the old weekly runtime in m2_core.py — the Friday rank over
the M2 weekly job's qualifier file (desk/feedlib/m2.py: the vendored
qualify_week.mjs + the verbatim feature blocks), the Monday fill pass with
the old budget / capacity / fresh-quote law and the 91-calendar-day exit.

Inputs via context.extra:
  "m2": the weekly qualifier file for the rank day (None until written)
  "meta": the sleeve's stamps (pending, last_rank_date, last_fill_date)
  "quotes": {SYM: {"bid","ask","t"}} for held and staged names
  "vix": (close, prev, asof_iso, source) | None
  "fear_ok": the desk fear composite >= FEAR (beatendown's buy gate)
  "sleeve_state": {SYM: {"position": {...}, "pending_entry": {...}}}
"""
from datetime import date, timedelta

from . import m2_core
from .compat import BaseSleeve, Intent, SleeveConfig

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
    """Verbatim old _exit_due twin (missing due date = due)."""
    if not isinstance(pos, dict):
        return False
    due = pos.get("exit_due_date")
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


def row(q):
    """old mode_rank's table row: the HOLD9 count on the rank's own feature set (daily bars before the rank
    day), selected = count >= 2."""
    hits = score_rules(q.get("feat_cf") or q.get("feat") or {})
    return {"count": len(hits), "rules": hits, "selected": len(hits) >= SELECT_MIN_COUNT,
            "bucket": (q.get("feat_cf") or q.get("feat") or {}).get("_bucket")}


RANK_HM, FILL_HM = (16, 5), (10, 0)      # old crons: rank Fri 16:5, fill Mon 10:0 ET


class Confluence(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        """master-desk: the old weekly runtime (desk/sleeves/femto/m2_core.py) — Friday's rank stages the book,
        the Monday fill pass executes it."""
        meta = (context.extra or {}).get("meta") or {}
        if m2_core.phase(context, RANK_HM, FILL_HM) != "fill" or meta.get("last_fill_date") == context.session:
            return []
        return m2_core.intents(Intent, context, meta, exit_due, new_buy_gates, "confluence", fear_gate=False,
                               free_sold_slots=True)


def next_meta(bars, slice_state, context, intents=()):
    return m2_core.next_meta(context, (context.extra or {}).get("meta") or {}, RANK_HM, FILL_HM, row, exit_due,
                             new_buy_gates, fear_gate=False, free_sold_slots=True)


def signal(bars, slice_state, context):
    return Confluence().signal(bars, slice_state, context)
