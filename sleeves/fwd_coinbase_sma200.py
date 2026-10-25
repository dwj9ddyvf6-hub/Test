"""FWD Coinbase SMA200 — lean-desk port (Wave D, Decision #119).

EXTRACTED from aurelia_common's Coinbase daily schedule (coinbase_*)
+ aurelia_forward_sleeves.coinbase_forward(): a daily decision at
00:00-00:05 UTC only, on 200 CONSECUTIVE completed daily bars
(gap = not ready), with a fresh native quote (age <= 30s, not future);
one decision per (sleeve, product, day) — duplicates never re-fire.
Buy 0.01 BTC-USD, budget $100,000, max exposure 10%.

CANDOR (from the source closure): the integrated decide() checks
window/history/quote and the just-closed day's existence — the SMA200
comparison itself lived in the source's history preparation, outside
the closure Femto integrated. This port is faithful to the integrated
decision function; the 200 completed consecutive days it requires ARE
the SMA200 warmup. History arrives as context.extra["history"]
([{date, close, complete, forming}]), the quote as
context.extra["quote"] {"as_of","bid","ask"}, and prior decision ids
as context.extra["decisions"] (the book's recorded decisions).

PARKED 2026-10-16 (FINAL2) — UNPARKED 2026-10-24 by the wire-coinbase
program under owner delegation — RE-PARKED 2026-10-24 by owner ruling
11:09 ET ("Re-park coinbase until its strategy is defined"):
CONFIG.parked=True and the roster entry's parked=true, so the
scheduler skips it again. The D4 fractional-qty extension from the
unpark STAYS; only the park state flips back. History of the
park: no source in the chain (this port, aurelia_common.coinbase_decide,
the original desk/coinbase_schedule.py in Agentic-Trading-Desk) defines
the SMA200 comparison the name promises OR any exit; the ported
decide() is unchanged by the unpark — it still checks only the
00:00-00:05 UTC window, 200 consecutive completed daily bars, a fresh
native quote, and the just-closed day, and would buy 0.01 BTC on every
executable day. No strategy, sizing, or exit was invented or changed
here; the fractional 0.01 BTC qty is carried by the D4 platform
extension for Coinbase hyphen products in runtime/models.py.

STRATEGY DEFINED + UNPARKED (ENH apply pass, per
ENHANCE-DESIGN-fwd_coinbase_sma200.md sections 4-6, owner-approved
design): the SMA200 comparison and the symmetric exit now live in
signal()'s treatment path below — flat + just-closed close strictly
above the mean of prepare()'s proven 200 completed consecutive
closes enters 0.01 BTC; held + close strictly below exits the full
held qty; equality is a no-trade point on both sides. decide()
itself is unchanged. Switch extra["coinbase_sma200"]["strategy"]
default ON; OFF restores the pre-change executable-buys behaviour
exactly. The pre-change rule runs in shadow as the section-5
control (never emits), scored with the treatment's exit logic;
paired records are filed on last_evaluation and appended to
extra["coinbase_sma200_exp_journal"] when served. CONFIG.parked
and the roster row's parked flip to false in the same pass
(section 6 step 5).

VIRTUAL BOOK MAPPING: Ledger account "fwd_coinbase_sma200_v1",
BUDGET_USD = 100,000. Fractional BTC qty (0.01) rides the intent's
qty field — C-1 cured 2026-10-16 (before the cure it could ride only
in the reason and the sleeve could never enter: 0.01 floored to
entry_no_qty under the whole-units contract).
"""
import math
from datetime import datetime, timedelta, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

ACCOUNT = "fwd_coinbase_sma200_v1"
BUDGET_USD = 100_000.0
MAX_EXPOSURE = 0.10
VERSION = "coinbase-daily-v1"
PRODUCT = "BTC-USD"
WINDOW = timedelta(minutes=5)
QTY_BTC = 0.01

CONFIG = SleeveConfig(
    sleeve_id="fwd_coinbase_sma200", cadence_s=300, universe=(PRODUCT,),
    state_schema={"decisions": "dict"}, risk_pct=None, parked=False)


def decision_id(day):
    return f"{ACCOUNT}|{VERSION}|{PRODUCT}|{day}"


def prepare(history):
    """Verbatim coinbase_prepare: 200 completed, consecutive days."""
    completed = [row for row in history or []
                 if row.get("complete") is True and row.get("forming") is not True]
    if len(completed) < 200:
        return {"ready": False, "reason": f"{len(completed)} completed days; 200 required"}
    days = [row["date"] for row in completed[-200:]]
    for left, right in zip(days, days[1:]):
        if datetime.fromisoformat(right) - datetime.fromisoformat(left) != timedelta(days=1):
            return {"ready": False, "reason": f"missing interval between {left} and {right}"}
    return {"ready": True, "through": days[-1], "count": 200}


def in_window(moment):
    start = moment.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return start <= moment.astimezone(timezone.utc) < start + WINDOW


def decide(moment, history, quote, decided_ids):
    """Verbatim coinbase_decide outcomes, as a status dict."""
    day = moment.astimezone(timezone.utc).date().isoformat()
    ident = decision_id(day)
    record = {"id": ident, "sleeve": ACCOUNT, "version": VERSION,
              "product": PRODUCT, "day": day}
    if ident in (decided_ids or set()):
        return {**record, "status": "duplicate"}
    prepared = prepare(history)
    if not in_window(moment):
        record.update(status="outside-window",
                      reason="Decision window is 00:00-00:05 UTC.")
    elif not prepared["ready"]:
        record.update(status="blocked", reason=prepared["reason"])
    elif not quote or quote.get("as_of") is None:
        record.update(status="blocked", reason="Fresh native quote is missing.")
    else:
        quoted_at = datetime.fromisoformat(str(quote["as_of"]).replace("Z", "+00:00"))
        if quoted_at.tzinfo is None:
            record.update(status="blocked", reason="Native quote timestamp has no timezone.")
            return record
        age = moment - quoted_at
        if age > timedelta(seconds=30) or age.total_seconds() < 0:
            record.update(status="blocked", reason="Native quote is stale or future.")
        else:
            # The just-closed day is the day before `day` — not any prior
            # day (P3 audit 2026-10-15: a history ending weeks earlier
            # passed the old any-prior-day check and executed on stale
            # closes). Mirror prepare(): a forming row is not completed,
            # even if it also claims complete.
            just_closed = (datetime.fromisoformat(day)
                           - timedelta(days=1)).date().isoformat()
            closed = sorted(
                (row for row in history
                 if row.get("complete") is True
                 and row.get("forming") is not True and row["date"] < day),
                key=lambda r: r["date"])
            fresh = bool(closed) and closed[-1]["date"] == just_closed
            record.update(status="executable" if fresh else "blocked",
                          reason=None if fresh else "Just-closed day is missing.",
                          close=closed[-1]["close"] if fresh else None)
    return record


# --- ENH 2026-10-24 (ENHANCE-DESIGN-fwd_coinbase_sma200 sections 4-5) --
# The strategy the name promises, added at the point decide() returns
# "executable" — every existing gate preserved verbatim. SMA200 is the
# mean of exactly the 200 completed consecutive closes prepare()
# proves; the comparison price is the last of them (the just-closed
# close). Partition (design section 4): flat & close > SMA200 -> enter
# QTY_BTC; flat & close <= SMA200 -> nothing; held & close < SMA200 ->
# exit the held qty exactly; held & close >= SMA200 -> hold. Equality
# is a no-trade point on both sides. No other rule exists.
# Switch: extra["coinbase_sma200"]["strategy"], default ON; OFF
# restores the pre-change executable-buys behaviour exactly.
# Control (design section 5): the pre-change rule evaluated in shadow
# on the same executable days, never emitting; its virtual position is
# scored with the treatment's exit logic (control_scored) and also
# tracked unscored as raw accumulation (control_raw buys QTY_BTC on
# every executable day and never sells). Paired records are filed on
# last_evaluation["enhance_exp"] and appended to
# extra["coinbase_sma200_exp_journal"]["records"] when served.
EXP_ID_COINBASE = "ENH-COINBASE-SMA200-20261024"


def _strategy_on(extra):
    ov = (extra or {}).get("coinbase_sma200")
    if isinstance(ov, dict) and "strategy" in ov:
        v = ov["strategy"]
        if isinstance(v, str):
            return v.strip().lower() not in ("off", "false", "control", "0", "")
        return bool(v)
    return True


def _valid_price(v):
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(float(v)) and float(v) > 0)


def _held_claim(extra):
    """(claimed, qty): whether the served held state claims a BTC-USD
    position, and its raw qty (validated by the caller). sleeve_state_flat
    for BTC-USD wins; the generic held_qty anchor is the fallback."""
    flat_map = (extra or {}).get("sleeve_state_flat")
    if isinstance(flat_map, dict) and PRODUCT in flat_map:
        row = flat_map[PRODUCT]
        return True, (row.get("qty") if isinstance(row, dict) else None)
    if "held_qty" in (extra or {}):
        return True, extra.get("held_qty")
    return False, None


def _entry_intent(quote, record):
    """The pre-change entry intent, byte-for-byte."""
    return Intent(
        "enter", PRODUCT, qty=QTY_BTC,
        price_hint=round(float(quote["ask"]), 2),
        reason="fwd_coinbase_sma200 buy qty_btc=%.2f decision=%s "
               "close=%s (account=%s max_exposure=%.2f)"
               % (QTY_BTC, record["id"], record.get("close"),
                  ACCOUNT, MAX_EXPOSURE))


class FwdCoinbaseSma200(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        moment = datetime.fromtimestamp(float(context.now), tz=timezone.utc)
        record = decide(moment, extra.get("history") or [], extra.get("quote"),
                        set(extra.get("decisions") or {}))
        if record.get("status") != "executable":
            return []
        quote = extra["quote"]
        if not _strategy_on(extra):
            self._paired(extra, record, record.get("close"), None, None,
                         "enter", None, switch="off")
            return [_entry_intent(quote, record)]
        return self._treatment(extra, record, quote)

    def _treatment(self, extra, record, quote):
        history = extra.get("history") or []
        completed = [row for row in history
                     if row.get("complete") is True
                     and row.get("forming") is not True]
        closes = []
        for row in completed[-200:]:
            c = row.get("close")
            if not _valid_price(c):
                self._paired(extra, record, None, None, None, "blocked",
                             "invalid_close_in_window")
                return []
            closes.append(float(c))
        sma200 = sum(closes) / 200.0
        close = closes[-1]
        claimed, held_raw = _held_claim(extra)
        held_qty = None
        if claimed:
            if not _valid_price(held_raw):
                self._paired(extra, record, close, sma200, None, "blocked",
                             "held_qty_invalid")
                return []
            held_qty = float(held_raw)
        if held_qty is None:
            if close <= sma200:
                self._paired(extra, record, close, sma200, None, "none",
                             "close_not_above_sma200")
                return []
            ask = quote.get("ask")
            if not _valid_price(ask):
                self._paired(extra, record, close, sma200, None, "blocked",
                             "quote_ask_invalid")
                return []
            if QTY_BTC * float(ask) > MAX_EXPOSURE * BUDGET_USD:
                self._paired(extra, record, close, sma200, None, "blocked",
                             "exposure_cap_exceeded")
                return []
            self._paired(extra, record, close, sma200, None, "enter", None)
            return [_entry_intent(quote, record)]
        if close >= sma200:
            self._paired(extra, record, close, sma200, held_qty, "hold", None)
            return []
        bid = quote.get("bid")
        if not _valid_price(bid):
            self._paired(extra, record, close, sma200, held_qty, "blocked",
                         "quote_bid_invalid")
            return []
        self._paired(extra, record, close, sma200, held_qty, "exit", None)
        return [Intent(
            "exit", PRODUCT, qty=held_qty,
            price_hint=round(float(bid), 2),
            reason="fwd_coinbase_sma200 exit qty_btc=%s decision=%s "
                   "close=%s sma200=%.2f (account=%s)"
                   % (held_qty, record["id"], record.get("close"),
                      sma200, ACCOUNT))]

    def _paired(self, extra, record, close, sma200, held_qty, action,
                reason, switch="on"):
        """Design section 5 paired record + shadow control scoring.
        The control never emits; it is scored only inside the served
        experiment journal (state must persist across decision days)."""
        journal = (extra or {}).get("coinbase_sma200_exp_journal")
        control_action = "none"
        if isinstance(journal, dict):
            scored = journal.setdefault("control_scored", {
                "qty": 0.0, "entry_price": None, "realized_pnl": 0.0,
                "round_trips": 0})
            raw = journal.setdefault("control_raw", {
                "buys": 0, "qty": 0.0, "last_close": None})
            quote = (extra or {}).get("quote") or {}
            raw["buys"] += 1
            raw["qty"] += QTY_BTC
            raw["last_close"] = close
            if scored["qty"] > 0 and sma200 is not None and close is not None \
                    and close < sma200 and _valid_price(quote.get("bid")):
                scored["realized_pnl"] += (float(quote["bid"])
                                            - scored["entry_price"]) * scored["qty"]
                scored["round_trips"] += 1
                scored["qty"] = 0.0
                scored["entry_price"] = None
                control_action = "exit"
            elif scored["qty"] <= 0 and _valid_price(quote.get("ask")):
                scored["qty"] = QTY_BTC
                scored["entry_price"] = float(quote["ask"])
                control_action = "enter"
            elif scored["qty"] > 0:
                control_action = "hold"
        rec = {"exp_id": EXP_ID_COINBASE, "day": record.get("day"),
               "decision_id": record.get("id"), "close": close,
               "sma200": sma200, "held_qty": held_qty,
               "treatment_action": action, "treatment_reason": reason,
               "control_action": control_action, "switch": switch}
        if isinstance(journal, dict):
            journal.setdefault("records", []).append(rec)
        stamp = {"enhance_exp": rec}
        if isinstance(journal, dict):
            stamp["coinbase_sma200_exp_journal"] = journal
        self.last_evaluation = stamp
        return rec


def signal(bars, slice_state, context):
    return FwdCoinbaseSma200().signal(bars, slice_state, context)
