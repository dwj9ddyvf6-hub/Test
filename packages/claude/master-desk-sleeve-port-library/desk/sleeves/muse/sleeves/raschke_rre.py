"""raschke_rre — Astra's RRE Adaptive Desk v0.2.0 as a desk
sleeve (2026-10-23), built per PORT-SPEC.md (workflow
raschke-rre-20261023). Source: Silicon dwj9ddyvf6-hub/Silicon,
research/linda_raschke/v02/, commit 59b11df1a3ff, package
"RRE Adaptive Desk v0.2.0" (RRE = Raschke Research Engine).

LINEAGE. The underlying methods are Linda Raschke's; the engine
design is Astra's. Not Sol, not ChatGPT, not Grok. Grok's
raschke_pf3 sleeve is a different design from a different
author; the PF3 overlap is convergence of subject matter and
the two sleeves are never merged or deduplicated.

THE PORT IN ONE PARAGRAPH. His canonical brain ports verbatim
into core/raschke_rre/ (raschke_core, raschke_engine,
awareness, router — byte-identical except pyflakes-proven
unused-import removals, the Saty ports' import-line delta).
His SPY-linear admission decision ports adapted into
core/raschke_rre/admission.py. This file is a thin desk
wrapper with NO strategy math: it builds his Session /
PriorSessionReference / Bar objects from the shared SIP bar
door, restores his AdaptiveRouter from the production journal
(producer key rre_journal, served by tools/run_live.py's
_rre_session_data through core/bars_universe.py's raschke_rre
branch), feeds each accepted bar exactly once, and maps his
routed candidates onto desk Intents. His broker / SQLite desk
/ service layers do not exist here — the desk dispatcher, the
Ink filing door and virtual slices own execution and
accounting. RRE3 / options / ES / MES are NOT ported.

PROFILES (spec section 5). Both lanes advance on every bar.
Only a routed RRE2 candidate may become a desk entry Intent
(FIRST_CROSS / FAILED_BREAK). A routed RRE1 candidate is
journaled BASELINE_ONLY — the preserved in-port baseline his
edge contract's comparison requires — and never trades.

EVENT SEAM (spec section 7). The desk has NO authenticated
point-in-time event-calendar feed. The wrapper therefore
supplies his ContextGates honestly — event_coverage_known=
False, events_clear=False, evidence_id naming the absence —
so his context book reports DATA_BLOCK on every pass, his
router vetoes routing (candidates preserved and consumed),
and the sleeve evaluates, journals and ABSTAINS. It does not
trade until a real compatible event source is integrated
through this same seam. No waiver, no invented all-clear.

WARMUP (spec section 6.4). blocked_warmup is stamped only for
his REQUIRED elements: a complete frozen prior-session
reference, and core feature readiness (Features exist with a
known previous state; PF3 arm gate at generation bar_count
>= 27). The 20-session same-slot baseline is OPTIONAL context:
ratios stay None, baseline_count is stamped, COMPRESSION is
unreachable, and nothing blocks on it. Exits are never
trapped behind warmup, the event block, or any entry gate:
position management runs first in every pass.

EXIT LAW (spec section 6.6). Per pass, in his precedence:
quote-triggered stop, quote-triggered target, the 1,800 s
hold deadline from first actual fill (the desk position
record's fill_t; the entry Intent's creation time is the
conservative provisional fallback, journaled
hold_clock_provisional), and flatten at session close
- 300 s. A due exit with no fresh executable quote is
journaled exit_due_unpriced and never priced synthetically.
Named cadence difference: his service layer evaluates exits
on a <=250 ms timer; this desk evaluates on the sleeve's
60 s scan cadence.

SESSION LAW (spec section 6.7). One S&P thesis at a time,
sleeve-scoped: the journal's active_thesis holds the slot
from entry-Intent emission until terminal flat
reconciliation; expiry of an unfilled intent releases it.
Cooldown is 900 wall-clock seconds after TERMINAL FLAT
RECONCILIATION (first pass whose served position/fill
records prove flat) — requests and ACKs never start it.

ADMISSION PINS (spec section 3.4, caller-required; desk
sources named in ports/raschke_rre.md): the virtual slice's
equity is the single capital bound (every RiskSnapshot
remainder is the slice equity); max_risk_age 60 s (the pass
cadence); spread caps 0.10 / 0.01, depth participation 0.5,
adverse-gap 0.2 x ATR, crossing caps $20 / 0.2, costs
(.01, .01, .01, 2) — his demo/test EXAMPLE values adopted as
named desk paper pins; allowed feeds ("sip", "iex") — the
desk quote door is the IEX latest-quote door (SIP is the bar
door); the wrapper stamps the quote's true door lineage and
never relabels it. Quote sizes 0/0 from the door mean depth
UNKNOWN (spec 6.5): the wrapper substitutes a non-binding
depth record (size 1 with depth terms neutralized via
depth_units_remaining bound by slice equity) and journals
quote_depth_unknown; when the door carries a real size, his
depth math applies exactly. Shorts fail closed: the desk has
no borrow-verification door, so borrow_verified is False and
his admission rejects SHORT_NOT_EXPRESSIBLE.

FORWARD TESTING ONLY. His own framing stands: an integration
package, not a deployed desk; the June replay proved candidate
generation and determinism, no fills or returns. This port
claims mechanical fidelity, never edge.
"""
import hashlib
import json
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.early_close import EARLY_CLOSES as _SHARED_EARLY_CLOSES
from core.sleeve import BaseSleeve, Intent, SleeveConfig
from core.raschke_rre import admission as adm
from core.raschke_rre.awareness import ContextConfig, ContextGates
from core.raschke_rre.raschke_core import Bar, Session
from core.raschke_rre.raschke_engine import PriorSessionReference
from core.raschke_rre.router import AdaptiveRouter, RankedIntent
from core.raschke_rre.router import RouterConfig

ET = ZoneInfo("America/New_York")
SYM = "SPY"
SERIES_ID = "SPY-5m-RTH-SIP-v1"
CALENDAR_VERSION = "desk-rth-earlyclose-v1"
EVENT_ABSENT_ID = "no-desk-event-source"
MAX_QUOTE_AGE_S = 5.0
COOLDOWN_S = 900
HOLD_S = 1800
PRIOR_FEED_SESSIONS = 40

_ROUTER_CFG = RouterConfig(0.01, SERIES_ID, CALENDAR_VERSION, 0.02)
_CTX_CFG = ContextConfig(SERIES_ID, CALENDAR_VERSION)
_LIMITS = adm.canonical_limits(
    max_risk_age_seconds=60.0, max_spread_price=0.10,
    max_spread_fraction=0.01, depth_participation=0.5,
    adverse_gap_atr_multiple=0.2, max_crossing_cost_dollars=20.0,
    max_crossing_cost_fraction=0.2,
    allowed_linear_feeds=("sip", "iex"))
_COSTS = adm.Costs(0.01, 0.01, 0.01, 2.0)
# The section-7 event seam, as data: (event_coverage_known,
# events_clear) for admission. Production value is (False,
# False) — ABSENT, blocking, per the spec pin. Labeled
# synthetic test fixtures may monkeypatch this module
# constant to exercise the admission path; no configuration
# surface reads it, and the trap blocker pins this literal.
_EVENT_GATES = (False, False)
_FINGERPRINT = hashlib.sha256(json.dumps({
    "version": "0.2.0", "router": str(sorted(
        vars(_ROUTER_CFG).items())),
    "context": str(sorted(vars(_CTX_CFG).items())),
    "limits": str(sorted(vars(_LIMITS).items())),
    "costs": str(sorted(vars(_COSTS).items())),
}, sort_keys=True, default=str).encode()).hexdigest()[:28]

CONFIG = SleeveConfig(
    sleeve_id="raschke_rre",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"position": "dict|None"},
)


def session_close_dt(session_iso):
    d = date.fromisoformat(session_iso)
    t = _SHARED_EARLY_CLOSES.get(session_iso, dtime(16, 0))
    return datetime.combine(d, t, tzinfo=ET)


def _session_obj(d, previous_id):
    iso = d.isoformat()
    return Session(iso,
                   datetime.combine(d, dtime(9, 30), tzinfo=ET),
                   session_close_dt(iso), previous_id)


def _shape(raw):
    """Desk bars ({t epoch, o/h/l/c/v}) -> sorted tuples."""
    out = []
    for b in raw or []:
        try:
            out.append((float(b["t"]), float(b["o"]), float(b["h"]),
                        float(b["l"]), float(b["c"]),
                        float(b.get("v") or 0.0)))
        except (KeyError, TypeError, ValueError):
            continue
    out.sort(key=lambda x: x[0])
    return out


def _fresh_journal():
    return {"fingerprint": _FINGERPRINT, "version": "0.2.0",
            "router_snapshot": None, "session": None,
            "reference": None, "pending": [],
            "dispositions": {}, "active_thesis": None,
            "cooldown_until": None, "last_bar_end": None,
            "warmup_sessions_fed": [],
            "pass_counters": {"bars_fed": 0, "data_vetoes": 0,
                              "shock_vetoes": 0, "baseline": 0,
                              "admitted": 0, "denied": 0}}


def _journal(extra, slice_state):
    raw = None
    if isinstance(extra.get("rre_journal"), dict):
        raw = extra["rre_journal"]
    elif isinstance(slice_state, dict) \
            and isinstance(slice_state.get("rre_journal"), dict):
        raw = slice_state["rre_journal"]
    if raw and raw.get("fingerprint") == _FINGERPRINT \
            and raw.get("version") == "0.2.0":
        j = _fresh_journal()
        j.update({k: raw[k] for k in j if k in raw})
        return j, False
    return _fresh_journal(), bool(raw)


def _intent_from_dict(row):
    from core.raschke_rre.raschke_engine import Intent as RIntent
    return RIntent(**row)


def _ranked_from_dict(row):
    return RankedIntent(_intent_from_dict(row["intent"]),
                        tuple(row["rank"]), row["context_id"],
                        row["context_state"], tuple(row["reasons"]))


class RaschkeRre(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # inputs
    # ------------------------------------------------------------
    def _position(self, extra, slice_state):
        state = extra.get("sleeve_state") or {}
        pos = (state.get(SYM) or {}).get("position")
        if not isinstance(pos, dict) and isinstance(slice_state, dict):
            pos = slice_state.get("position")
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0:
            return pos
        return None

    def _quote(self, extra, now_epoch):
        """(bid, ask, bid_size, ask_size, event_dt, feed) from
        the desk quote door when two-sided and <= 5 s old; sizes
        0 when the door carries none (unknown, never invented).
        Feed is the door's own lineage stamp when carried, else
        the IEX latest-quote door's name — never relabeled."""
        q = (extra.get("latest_quote") or {}).get(SYM)
        if not isinstance(q, dict) or not q.get("t"):
            return None
        try:
            t_dt = datetime.fromisoformat(
                str(q["t"]).replace("Z", "+00:00"))
            bp, ap = float(q["bp"]), float(q["ap"])
            bs = int(q.get("bs") or 0)
            asz = int(q.get("as") or 0)
        except (KeyError, TypeError, ValueError):
            return None
        if now_epoch - t_dt.timestamp() > MAX_QUOTE_AGE_S \
                or bp <= 0 or ap < bp:
            return None
        return bp, ap, bs, asz, t_dt, str(q.get("feed") or "iex")

    def _fills(self, extra):
        fills = extra.get("session_fills")
        if fills is None:
            return None
        out = []
        for f in fills:
            try:
                out.append({
                    "position_intent": f.get("position_intent"),
                    "qty": abs(float(f.get("qty") or 0)),
                    "price": float(f.get("price") or 0),
                    "ts": f.get("ts")})
            except (TypeError, ValueError):
                continue
        return out

    # ------------------------------------------------------------
    # exit management — runs FIRST, never trapped (spec 6.6)
    # ------------------------------------------------------------
    def _exit_intent(self, qty_signed, rule, quote, ctx):
        d = 1 if qty_signed > 0 else -1
        kw = {}
        if quote is not None:
            limit = quote[0] if d > 0 else quote[1]
            kw["limit_price"] = round(limit, 2)
            kw["price_hint"] = round(limit, 2)
        return Intent(
            "exit", SYM, qty=abs(int(qty_signed)),
            side="sell" if d > 0 else "buy",
            position_intent="sell_to_close" if d > 0
            else "buy_to_close",
            reason=f"raschke_rre exit: {rule}",
            signal_date=ctx.session, **kw)

    def _manage(self, pos, journal, extra, ctx, stamp):
        qty_signed = float(pos.get("qty") or 0)
        d = 1 if qty_signed > 0 else -1
        thesis = journal.get("active_thesis") or {}
        stamp["position"] = {"qty": qty_signed, "direction": d,
                             "source_id": thesis.get("source_id")}
        quote = self._quote(extra, ctx.now)
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        close_dt = session_close_dt(ctx.session)
        due = None
        if thesis:
            stop = thesis.get("stop")
            target = thesis.get("target")
            if quote is not None and stop is not None:
                exec_px = quote[0] if d > 0 else quote[1]
                if (d > 0 and exec_px <= float(stop)) or \
                        (d < 0 and exec_px >= float(stop)):
                    due = "stop"
                elif target is not None and (
                        (d > 0 and exec_px >= float(target)) or
                        (d < 0 and exec_px <= float(target))):
                    due = "target"
            if due is None:
                first_fill = thesis.get("first_fill_at")
                if first_fill is None:
                    first_fill = thesis.get("emitted_at")
                    stamp["hold_clock_provisional"] = True
                if first_fill is not None and \
                        ctx.now >= float(first_fill) + HOLD_S:
                    due = "hold_deadline"
            if due is None and \
                    now_dt >= close_dt - timedelta(seconds=300):
                due = "flatten"
        elif now_dt >= close_dt - timedelta(seconds=300):
            due = "flatten"
        if due is None:
            return []
        stamp["decision"] = f"exit_{due}"
        if quote is None:
            stamp["exit_due_unpriced"] = due
            return []
        return [self._exit_intent(qty_signed, due, quote, ctx)]

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "raschke_rre", "session": ctx.session,
                 "state": "armed", "decision": None,
                 "event_state": "event_absent_strict_block",
                 "event_coverage_known": False,
                 "baseline_count": 0, "context_state": None,
                 "warmup": {}}
        self.last_evaluation = stamp
        extra = ctx.extra or {}
        journal, rejected = _journal(extra, slice_state)
        stamp["rre_journal"] = journal
        if rejected:
            stamp["journal_rejected"] = "fingerprint_mismatch"
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)

        # thesis flat reconciliation + cooldown (spec 6.7):
        # proven only by the served position/fill records.
        pos = self._position(extra, slice_state)
        thesis = journal.get("active_thesis")
        if thesis is not None:
            fills = self._fills(extra)
            if pos is not None and not thesis.get("first_fill_at"):
                fill_t = pos.get("fill_t") or pos.get("entry_t")
                if fill_t:
                    thesis["first_fill_at"] = float(fill_t)
                    thesis["state"] = "open"
                elif fills:
                    thesis["state"] = "open"
            if pos is None and thesis.get("state") in (
                    "open", "exit_pending", "emitted"):
                if thesis.get("state") == "emitted" and fills:
                    pass  # fills exist: not proven flat
                elif thesis.get("state") == "emitted" and \
                        thesis.get("expires_at") and \
                        ctx.now >= float(thesis["expires_at"]):
                    journal["dispositions"][thesis["source_id"]] = {
                        "status": "EXPIRED", "reason": "intent_expired",
                        "at": now_dt.isoformat()}
                    journal["active_thesis"] = None
                    stamp["decision"] = "thesis_expired"
                elif thesis.get("state") in ("open", "exit_pending"):
                    journal["cooldown_until"] = ctx.now + COOLDOWN_S
                    journal["dispositions"][thesis["source_id"]] = {
                        "status": "FLAT", "reason": "proven_flat",
                        "at": now_dt.isoformat()}
                    journal["active_thesis"] = None
                    stamp["cooldown_until"] = \
                        journal["cooldown_until"]

        # 1. exits first — always, in every state (spec 6.6)
        pos = self._position(extra, slice_state)
        if pos is not None:
            exits = self._manage(pos, journal, extra, ctx, stamp)
            if exits:
                th = journal.get("active_thesis")
                if th is not None:
                    th["state"] = "exit_pending"
                return exits

        # 2. calendar
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []

        # 3. bar bundle: current + prior sessions from the door
        raw = []
        if isinstance(extra.get("bars_5m_long"), dict):
            raw = _shape(extra["bars_5m_long"].get(SYM))
        if not raw and isinstance(bars, dict):
            raw = _shape(bars.get(SYM))
        if not raw:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: no 5m bars"
            return []
        by_day = {}
        for r in raw:
            d = datetime.fromtimestamp(r[0], tz=ET).date()
            by_day.setdefault(d, []).append(r)
        days = sorted(d for d in by_day if is_trading_day(d))
        if session_d not in by_day and session_d not in days:
            stamp["state"] = "blocked_data"
            stamp["decision"] = "blocked_data: session unregistered"
            return []

        # sessions + frozen prior-session references (spec 6.3)
        sess_objs = {}
        prev = None
        for d in days:
            sess_objs[d.isoformat()] = _session_obj(
                d, prev.isoformat() if prev else None)
            prev = d
        if ctx.session not in sess_objs:
            sess_objs[ctx.session] = _session_obj(
                session_d,
                days[-1].isoformat() if days and
                days[-1] < session_d else
                (days[-2].isoformat() if len(days) > 1 else None))
        refs = {}
        day_list = sorted(sess_objs)
        for i, iso in enumerate(day_list):
            if i == 0:
                continue
            pd = date.fromisoformat(day_list[i - 1])
            rows = by_day.get(pd) or []
            if not rows:
                continue
            p_sess = sess_objs[day_list[i - 1]]
            grid = int((p_sess.close - p_sess.open).total_seconds()
                       // 300)
            complete = len(rows) >= grid and \
                abs(rows[0][0] - p_sess.open.timestamp()) < 1 and \
                abs(rows[-1][0] + 300 - p_sess.close.timestamp()) < 1
            refs[iso] = PriorSessionReference(
                SYM, iso, p_sess, p_sess.close,
                max(r[2] for r in rows), min(r[3] for r in rows),
                rows[-1][4], SERIES_ID, CALENDAR_VERSION, complete)

        # 4. restore or build the router (spec 8)
        router = None
        snap = journal.get("router_snapshot")
        if snap and journal.get("session") == ctx.session:
            try:
                router = AdaptiveRouter.from_snapshot(snap)
            except Exception:
                router = None
                stamp["journal_rejected"] = "snapshot_invalid"
        if router is None:
            router = AdaptiveRouter(_ROUTER_CFG, _CTX_CFG)
            journal["router_snapshot"] = None
            journal["last_bar_end"] = None
            journal["warmup_sessions_fed"] = []
            # feed prior sessions (bounded) so the context
            # book's history/baseline and the core carry are
            # built by his own machinery, never synthesized
            feed_days = [d for d in days if d < session_d]
            feed_days = feed_days[-PRIOR_FEED_SESSIONS:]
            for d in feed_days:
                iso = d.isoformat()
                ref = refs.get(iso)
                if ref is None or not ref.complete:
                    continue
                self._feed(router, by_day[d], sess_objs[iso], ref,
                           journal, stamp)
                journal["warmup_sessions_fed"].append(iso)
            journal["session"] = ctx.session

        # current session: frozen reference rides the journal
        ref = refs.get(ctx.session)
        if journal.get("reference") and \
                journal.get("session") == ctx.session:
            try:
                ref = PriorSessionReference.from_dict(
                    journal["reference"])
            except Exception:
                ref = refs.get(ctx.session)
        if ref is not None:
            journal["reference"] = ref.to_dict()
        stamp["reference"] = {
            "complete": bool(ref and ref.complete),
            "reference_id": ref.reference_id if ref else None}

        # gates: honest absence (spec section 7)
        sess = sess_objs[ctx.session]
        gates = ContextGates(
            EVENT_ABSENT_ID, ctx.session, sess.open,
            sess.close + timedelta(days=1),
            True, False, False, True, True)

        # 5. feed this session's new bars exactly once,
        # harvesting routed AND vetoed candidates per bar
        routed_now = []
        if ref is not None and ref.complete:
            rows = [r for r in (by_day.get(session_d) or [])
                    if r[0] + 300 <= ctx.now]
            watermark = journal.get("last_bar_end")
            for r in rows:
                end_iso = datetime.fromtimestamp(
                    r[0] + 300, tz=ET).isoformat()
                if watermark and end_iso <= watermark:
                    continue
                got = self._feed_one(
                    router, r, sess, ref, gates, journal, stamp)
                if got is None:
                    stamp["state"] = "blocked_data"
                    stamp["decision"] = \
                        "blocked_data: bar rejected (fail closed)"
                    journal["router_snapshot"] = router.dump_state()
                    return []
                routed_now.extend(got[0])
                # candidates the context book vetoed on this
                # bar are consumed by his router: journal them
                # VETOED at harvest — preserved for audit,
                # never offered to admission (spec 2.4/5)
                if got[2] in ("DATA_BLOCK", "SHOCK_PAUSE"):
                    for item in got[1]:
                        sid = item.intent.source_id
                        if sid not in journal["dispositions"]:
                            journal["dispositions"][sid] = {
                                "status": "VETOED",
                                "reason": got[2],
                                "at": end_iso,
                                "intent": item.intent.to_dict(),
                                "context_id": item.context_id}
                            key = "data_vetoes" \
                                if got[2] == "DATA_BLOCK" \
                                else "shock_vetoes"
                            journal["pass_counters"][key] += 1
                journal["last_bar_end"] = end_iso
                watermark = end_iso
        journal["router_snapshot"] = router.dump_state()

        # context + warmup stamps (spec 6.4)
        snap_ctx = router.context.last_snapshot
        features = router.lanes["RRE2"]._previous
        bar_count = features.bar_count if features else 0
        if snap_ctx is not None:
            stamp["context_state"] = snap_ctx.state
            stamp["context_id"] = snap_ctx.context_id
            stamp["baseline_count"] = int(
                snap_ctx.quality.get("baseline_count") or 0)
            stamp["range_ratio"] = \
                snap_ctx.observed.get("range_ratio")
        stamp["warmup"] = {
            "prior_reference": bool(ref and ref.complete),
            "core_features": int(bar_count or 0),
            "baseline_count": stamp["baseline_count"]}
        warm_block = None
        if ref is None or not ref.complete:
            warm_block = "prior_reference"
        elif features is None or (bar_count or 0) < 27:
            warm_block = "core_features"
        if warm_block:
            stamp["state"] = "blocked_warmup"
            stamp["decision"] = f"blocked_warmup: {warm_block} " \
                f"core_features {int(bar_count or 0)}/27 " \
                f"baseline_count {stamp['baseline_count']}/20"
            self._dispose_pending(journal, router, ctx, stamp,
                                  entries_allowed=False)
            return []

        # 6. new routed candidates join pending (non-destructive)
        seen = {p["intent"]["source_id"]
                for p in journal["pending"]}
        for item in routed_now:
            sid = item.intent.source_id
            if sid not in seen and \
                    sid not in journal["dispositions"]:
                journal["pending"].append(item.to_dict())
                seen.add(sid)
        # 7. disposition maintenance + admission (spec 5/6.5/6.7)
        intents = self._dispose_pending(
            journal, router, ctx, stamp, entries_allowed=True)
        journal["router_snapshot"] = router.dump_state()
        return intents

    # ------------------------------------------------------------
    # bar feeding
    # ------------------------------------------------------------
    def _feed(self, router, rows, sess, ref, journal, stamp):
        gates = ContextGates(
            EVENT_ABSENT_ID, sess.id, sess.open,
            sess.close + timedelta(days=1),
            True, False, False, True, True)
        for r in rows:
            end_epoch = r[0] + 300
            if end_epoch > sess.close.timestamp():
                continue
            self._feed_one(router, r, sess, ref, gates, journal,
                           stamp)

    def _feed_one(self, router, r, sess, ref, gates, journal,
                  stamp):
        start = datetime.fromtimestamp(r[0], tz=ET)
        end = start + timedelta(minutes=5)
        bar = Bar(SYM, start, end, end, sess.id,
                  r[1], r[2], r[3], r[4], r[5])
        try:
            routed = router.update(bar, sess, ref, end, gates)
        except ValueError:
            return None
        journal["pass_counters"]["bars_fed"] += 1
        # vetoed candidates live in last_candidates for THIS
        # bar only (the router overwrites it next bar): the
        # caller harvests them per bar or they are lost.
        ctx_state = router.context.last_snapshot.state \
            if router.context.last_snapshot else None
        return list(routed), list(router.last_candidates), ctx_state

    # ------------------------------------------------------------
    # pending disposition + admission (spec 2.6 / 5 / 6.5 / 6.7)
    # ------------------------------------------------------------
    def _dispose_pending(self, journal, router, ctx, stamp,
                         entries_allowed):
        out = []
        if not journal["pending"]:
            return out
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        remaining = []
        for row in journal["pending"]:
            try:
                item = _ranked_from_dict(row)
            except Exception:
                continue
            intent = item.intent
            sid = intent.source_id
            if sid in journal["dispositions"]:
                continue
            if now_dt >= intent.expires_at:
                journal["dispositions"][sid] = {
                    "status": "EXPIRED", "reason": "intent_expired",
                    "at": now_dt.isoformat()}
                continue
            if intent.variant == "RRE1":
                journal["dispositions"][sid] = {
                    "status": "BASELINE_ONLY",
                    "reason": "rre1_baseline_lane",
                    "at": now_dt.isoformat(),
                    "intent": intent.to_dict(),
                    "rank": list(item.rank),
                    "context_id": item.context_id}
                journal["pass_counters"]["baseline"] += 1
                continue
            if not entries_allowed:
                remaining.append(row)
                continue
            # one-thesis slot + cooldown (spec 6.7)
            if journal.get("active_thesis") is not None:
                remaining.append(row)
                continue
            if journal.get("cooldown_until") and \
                    ctx.now < float(journal["cooldown_until"]):
                stamp["cooldown_active"] = True
                remaining.append(row)
                continue
            admitted = self._admit(journal, intent, item, ctx,
                                   stamp)
            if admitted is None:
                remaining.append(row)  # no quote yet: stays
                continue            # pending inside its TTL
            adm_rec, desk_intent = admitted
            if adm_rec.allowed and desk_intent is not None:
                journal["dispositions"][sid] = {
                    "status": "RESERVED", "reason": "admitted",
                    "at": now_dt.isoformat(),
                    "units": adm_rec.units,
                    "entry_limit": adm_rec.entry_limit,
                    "net_rr": adm_rec.underlying_net_rr}
                journal["active_thesis"] = {
                    "source_id": sid,
                    "setup": intent.setup,
                    "direction": intent.direction,
                    "stop": intent.stop, "target": intent.target,
                    "emitted_at": ctx.now,
                    "expires_at": intent.expires_at.timestamp(),
                    "first_fill_at": None, "state": "emitted"}
                journal["pass_counters"]["admitted"] += 1
                stamp["decision"] = f"enter {intent.setup}"
                out.append(desk_intent)
            else:
                journal["dispositions"][sid] = {
                    "status": "REJECTED", "reason": adm_rec.reason,
                    "at": now_dt.isoformat()}
                journal["pass_counters"]["denied"] += 1
        journal["pending"] = remaining
        return out

    def _admit(self, journal, intent, item, ctx, stamp):
        """His admit_linear against the virtual slice (spec
        6.5). Returns None when no fresh quote exists yet (the
        candidate stays pending inside its TTL), else
        (Admission, desk Intent | None)."""
        extra = ctx.extra or {}
        quote = self._quote(extra, ctx.now)
        if quote is None:
            return None
        bp, ap, bs, asz, q_dt, feed = quote
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        sess = _session_obj(date.fromisoformat(ctx.session), None)
        # prior-session chain for the Session object is not
        # part of admission; identity is by id/close only.
        equity = float(ctx.equity or 0.0)
        risk = adm.RiskSnapshot(
            f"slice-{ctx.session}-{int(ctx.now)}", now_dt,
            now_dt + timedelta(seconds=60),
            equity, equity, equity, equity, equity,
            10000, 10000, 0.0, 0)
        gates = adm.Gates(True, True, _EVENT_GATES[0],
                          _EVENT_GATES[1], True, False, False)
        # event gates are False by the section-7 seam: his
        # _common rejects EVENT_COVERAGE_UNKNOWN before any
        # quote/geometry term runs. The synthetic all-clear
        # path exists only in labeled test fixtures, which
        # call admit_linear directly.
        depth_unknown = (bs == 0 and asz == 0)
        if depth_unknown:
            stamp["quote_depth_unknown"] = True
            bs = asz = 1  # non-binding record; the binding
            # capacity terms are the slice-equity remainders
        q = adm.Quote(
            f"desk-{ctx.session}-{int(q_dt.timestamp())}", SYM,
            bp, ap, bs, asz, q_dt, q_dt, feed, ctx.session,
            "shares", True, True, True)
        exec_px = ap if intent.direction > 0 else bp
        instrument = adm.LinearInstrument(
            SYM, "SPY", 1, 0.01, exec_px, sess.open, sess.close,
            sess.close, True, True)
        rec = adm.admit_linear(intent, q, instrument, _COSTS,
                               risk, gates, _LIMITS, sess, now_dt)
        if not rec.allowed:
            return rec, None
        d = intent.direction
        desk = Intent(
            "enter", SYM, qty=int(rec.units),
            limit_price=round(float(rec.entry_limit), 2),
            price_hint=round(intent.entry_reference, 2),
            stop=round(intent.stop, 2),
            target=round(intent.target, 2),
            side="buy" if d > 0 else "sell",
            position_intent="buy_to_open" if d > 0
            else "sell_to_open",
            reason=(f"raschke_rre/RRE2 {intent.setup} "
                    f"{'long' if d > 0 else 'short'} "
                    f"source_id={intent.source_id} "
                    f"episode_id={intent.episode_id} "
                    f"context={item.context_state} "
                    f"context_id={item.context_id} "
                    f"rank={list(item.rank)} "
                    f"net_rr={rec.underlying_net_rr} "
                    f"event_state=event_absent_strict_block"),
            signal_date=ctx.session)
        return rec, desk


def signal(bars, slice_state, ctx):
    return RaschkeRre().signal(bars, slice_state, ctx)
