"""CONV123-REVIVAL-20261116: desk producers serving the three
Graveyard revival accrual ledgers (CONV-123).

The revival rule is frozen (Conversion Register CONV-123;
Graveyard Book registration, 2026-11-15): a leg is declared
REVIVED only if its forward read, at 250 further active days
(or 100 further events for PEAD), shows its published-direction
mean positive with t at or above 2 in the forward window alone.
Accrual counts from Mon 2026-11-16.

Until this landing the three accruals (research-lane crons
w7-tom-accrual-daily, w7-pairs-accrual-daily,
w7-pead-accrual-daily) appended to research-lane ledgers beside
their scripts, which no desk producer served into the snapshot,
so no desk evaluator could ever read a family's accrual state
(BUGLOG_2026-11-15.md, GOING-LIVE-VARIATIONS-20261115, Lane B).

ONE source of truth: these producers READ the research lane's
canonical ledgers in place
(research_notes/decisions-api-leverage-20261114/keepgoing2/
wave7/w7d_*_shadow.jsonl). They never write to them, never copy
them, and never fork the data; the research crons keep
appending and the desk serves whatever the ledger holds at
cycle time. A missing or genesis-less ledger fails closed
({}), leaving dependent sleeves UNFED by name, exactly like
every other batch producer.

Each producer serves one snapshot key (revival_tom,
revival_pairs, revival_pead) carrying the family's accrual
state, and also stamps the same state to
state/revival_<leg>.json on every call, so the accrual state
is readable from desk state without a snapshot.

The revival read is FROZEN AT THE COUNT, per the registration's
own wording ("its forward read, AT 250 further active days"):
the frozen mean and t are computed over the first 250 active
days (TOM, PAIRS) or the first 100 matured events (PEAD) in
ledger order, and the revival_state is decided on that frozen
read alone. Running stats over every accrued row are served
beside the frozen read and decide nothing.

Statistics replicate the accrual scripts' own formulas:
TOM/PAIRS mean and t over the active-day ret_bp series
(mean / (stdev / sqrt(n)), sample stdev); PEAD's
published-direction mean is the foundry leg (mean +21-session
drift of the top surprise tercile minus the bottom tercile,
over matured events) with a Welch two-sample t between the
terciles.
"""
from __future__ import annotations

import json
import math
import os
import statistics

ACCRUAL_START = "2026-11-16"
LEDGER_DIR = os.path.expanduser(
    "~/workspace/research_notes/decisions-api-leverage-20261114/"
    "keepgoing2/wave7")

# Freshness: the research crons append on weekdays only, so a
# ledger can legitimately be ~4 days old across a holiday
# weekend; the state it carries (an accrual count) cannot go
# stale in the direction of harm, it can only lag a day.
REVIVAL_SLA_S = 400000


def _write_json_atomic(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, sort_keys=True)
    os.replace(tmp, path)


def mean_t_bp(vals_bp):
    """(n, mean_bp, t) with the accrual scripts' formula."""
    vals = [float(v) for v in vals_bp]
    n = len(vals)
    if n == 0:
        return 0, None, None
    mean = statistics.mean(vals)
    if n < 2:
        return n, round(mean, 4), None
    sd = statistics.stdev(vals)
    t = mean / (sd / math.sqrt(n)) if sd > 0 else None
    return n, round(mean, 4), (round(t, 3) if t is not None else None)


def _read_ledger(path):
    """(genesis, rows) or (None, []) when the ledger is absent,
    unreadable, or carries no genesis row (fail closed)."""
    try:
        with open(path) as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None, []
    genesis, rows = None, []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get("record_type") == "genesis":
            genesis = row
        else:
            rows.append(row)
    if genesis is None:
        return None, []
    return genesis, rows


def _revival_state(count, threshold, mean_bp, t):
    if count < threshold:
        return "accruing"
    if mean_bp is not None and mean_bp > 0 and t is not None \
            and t >= 2:
        return "REVIVED"
    return "REBURIED"


class _RevivalLedgerProducer:
    """Base: read one w7 shadow ledger, serve its accrual state."""

    LEG = None          # "TOM" | "PAIRS" | "PEAD"
    FAMILY = None       # snapshot family name
    OUTPUT = None       # snapshot key
    LEDGER_NAME = None  # file under LEDGER_DIR
    THRESHOLD = None

    def __init__(self, root, ledger_path=None):
        self.root = root
        self.ledger_path = ledger_path or os.path.join(
            LEDGER_DIR, self.LEDGER_NAME)
        self.state_path = os.path.join(
            root, "state", f"revival_{self.FAMILY}.json")

    def _state(self, genesis, rows):
        raise NotImplementedError

    def __call__(self, pctx):
        genesis, rows = _read_ledger(self.ledger_path)
        if genesis is None:
            return {}
        state = self._state(genesis, rows)
        try:
            _write_json_atomic(self.state_path, state)
        except OSError:
            pass
        return {self.OUTPUT: state}


class RevivalTomProducer(_RevivalLedgerProducer):
    """TOM: one ledger row per forward active (turn-of-month)
    day; the count is active days, the threshold 250."""

    LEG = "TOM"
    FAMILY = "tom"
    OUTPUT = "revival_tom"
    LEDGER_NAME = "w7d_tom_shadow.jsonl"
    THRESHOLD = 250

    def _state(self, genesis, rows):
        days = [r for r in rows
                if r.get("record_type") == "active_day"
                and r.get("ret_bp") is not None]
        days.sort(key=lambda r: r.get("date") or "")
        vals = [r["ret_bp"] for r in days]
        n, mean, t = mean_t_bp(vals)
        fn, fmean, ft = mean_t_bp(vals[:self.THRESHOLD])
        return {
            "leg": self.LEG, "family": self.FAMILY,
            "registered": genesis.get("registered"),
            "accrual_start": ACCRUAL_START,
            "ledger": self.ledger_path,
            "construction": genesis.get("construction"),
            "revival_rule": genesis.get("revival_rule"),
            "threshold": self.THRESHOLD,
            "threshold_kind": "active_days",
            "active_days": n,
            "mean_bp": mean, "t": t,
            "frozen_count": fn, "frozen_mean_bp": fmean,
            "frozen_t": ft,
            "revival_state": _revival_state(
                fn, self.THRESHOLD, fmean, ft),
            "last_date": (days[-1].get("date") if days else None),
            "status": genesis.get("status") if n == 0 else "accruing",
        }


class RevivalPairsProducer(_RevivalLedgerProducer):
    """PAIRS: one ledger row per forward active day (a day any
    pair carries pnl); the count is active days, threshold 250."""

    LEG = "PAIRS"
    FAMILY = "pairs"
    OUTPUT = "revival_pairs"
    LEDGER_NAME = "w7d_pairs_shadow.jsonl"
    THRESHOLD = 250

    def _state(self, genesis, rows):
        days = [r for r in rows
                if r.get("record_type") == "active_day"
                and r.get("ret_bp") is not None]
        days.sort(key=lambda r: r.get("date") or "")
        vals = [r["ret_bp"] for r in days]
        n, mean, t = mean_t_bp(vals)
        fn, fmean, ft = mean_t_bp(vals[:self.THRESHOLD])
        return {
            "leg": self.LEG, "family": self.FAMILY,
            "registered": genesis.get("registered"),
            "accrual_start": ACCRUAL_START,
            "ledger": self.ledger_path,
            "construction": genesis.get("construction"),
            "revival_rule": genesis.get("revival_rule"),
            "threshold": self.THRESHOLD,
            "threshold_kind": "active_days",
            "active_days": n,
            "mean_bp": mean, "t": t,
            "frozen_count": fn, "frozen_mean_bp": fmean,
            "frozen_t": ft,
            "revival_state": _revival_state(
                fn, self.THRESHOLD, fmean, ft),
            "last_date": (days[-1].get("date") if days else None),
            "status": genesis.get("status") if n == 0 else "accruing",
        }


def pead_leg_stats(events):
    """The foundry PEAD leg over matured events (drift21_bp
    present), all values in bp: terciles by surprise_bp, leg21 =
    mean top-tercile drift21 minus mean bottom-tercile drift21,
    leg5 the same at +5 sessions, and the Welch two-sample t of
    the +21 leg. Returns a dict with n == 0 when no event has
    matured."""
    matured = [e for e in events
               if e.get("drift21_bp") is not None
               and e.get("surprise_bp") is not None]
    matured.sort(key=lambda e: e["surprise_bp"])
    n = len(matured)
    out = {"n": n, "leg21_bp": None, "leg5_bp": None,
           "welch_t21": None, "bottom21_bp": None, "top21_bp": None}
    if n < 3:
        return out
    k = n // 3
    bottom, top = matured[:k], matured[-k:]
    b21 = [float(e["drift21_bp"]) for e in bottom]
    t21 = [float(e["drift21_bp"]) for e in top]
    out["bottom21_bp"] = round(statistics.mean(b21), 4)
    out["top21_bp"] = round(statistics.mean(t21), 4)
    out["leg21_bp"] = round(statistics.mean(t21)
                            - statistics.mean(b21), 4)
    b5 = [float(e["drift5_bp"]) for e in bottom
          if e.get("drift5_bp") is not None]
    t5 = [float(e["drift5_bp"]) for e in top
          if e.get("drift5_bp") is not None]
    if b5 and t5:
        out["leg5_bp"] = round(statistics.mean(t5)
                               - statistics.mean(b5), 4)
    if k >= 2:
        vb = statistics.variance(b21)
        vt = statistics.variance(t21)
        denom = math.sqrt(vt / k + vb / k)
        if denom > 0:
            out["welch_t21"] = round(
                (statistics.mean(t21) - statistics.mean(b21))
                / denom, 3)
    return out


class RevivalPeadProducer(_RevivalLedgerProducer):
    """PEAD: one ledger row per forward Item 2.02 event; the
    count is MATURED events (drift21 priced), the threshold 100.
    The full event list is served with the state: it is the
    evaluator's trade-form input (no second join exists)."""

    LEG = "PEAD"
    FAMILY = "pead"
    OUTPUT = "revival_pead"
    LEDGER_NAME = "w7d_pead_shadow.jsonl"
    THRESHOLD = 100

    def _state(self, genesis, rows):
        events = [r for r in rows if r.get("record_type") == "event"]
        events.sort(key=lambda r: r.get("acceptance_utc") or "")
        served = [{
            "symbol": e.get("symbol"),
            "acceptance_utc": e.get("acceptance_utc"),
            "event_date": e.get("event_date"),
            "surprise_bp": e.get("surprise_bp"),
            "drift5_bp": e.get("drift5_bp"),
            "drift21_bp": e.get("drift21_bp"),
            "status": e.get("status"),
        } for e in events]
        running = pead_leg_stats(served)
        # The frozen read is over the first 100 MATURED events in
        # ledger order (pead_leg_stats re-sorts its input by
        # surprise for the terciles, which is the foundry form).
        matured = [e for e in served
                   if e.get("drift21_bp") is not None]
        frozen = pead_leg_stats(matured[:self.THRESHOLD])
        return {
            "leg": self.LEG, "family": self.FAMILY,
            "registered": genesis.get("registered"),
            "accrual_start": ACCRUAL_START,
            "ledger": self.ledger_path,
            "construction": genesis.get("construction"),
            "revival_rule": genesis.get("revival_rule"),
            "threshold": self.THRESHOLD,
            "threshold_kind": "events",
            "events_total": len(served),
            "events_matured": running["n"],
            "leg21_bp": running["leg21_bp"],
            "leg5_bp": running["leg5_bp"],
            "welch_t21": running["welch_t21"],
            "frozen_count": frozen["n"],
            "frozen_mean_bp": frozen["leg21_bp"],
            "frozen_t": frozen["welch_t21"],
            "revival_state": _revival_state(
                frozen["n"], self.THRESHOLD,
                frozen["leg21_bp"], frozen["welch_t21"]),
            "excluded_by_construction":
                genesis.get("excluded_by_construction"),
            "events": served,
            "status": genesis.get("status") if not served
                      else "accruing",
        }


REVIVAL_PRODUCERS = (
    ("revival_tom", RevivalTomProducer, RevivalTomProducer.OUTPUT),
    ("revival_pairs", RevivalPairsProducer,
     RevivalPairsProducer.OUTPUT),
    ("revival_pead", RevivalPeadProducer, RevivalPeadProducer.OUTPUT),
)


def register_revival(desk, root):
    """Register the three revival ledger producers on a Desk
    (live runner wiring, beside register_batch3)."""
    for name, cls, output in REVIVAL_PRODUCERS:
        desk.add_producer(name, cls(root), [output], REVIVAL_SLA_S)
    return desk
