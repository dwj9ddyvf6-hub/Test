"""Opening-gamma in-window scan loop (GAMMA-WINDOW-20261116).

Lane E (desk full audit 2026-11-16, defect 1a): aster_open_gamma_a
and aster_open_gamma_b evaluate only inside 09:35-09:45 ET and
consume an opening-event row only while its break is <=5s old
(desk3/aster_batch1.py _eval_gamma). The desk cycle that feeds
them runs 691-1671s + 60s at an unanchored phase and stamps its
snapshot with the cycle-START instant, so no evaluation could
ever land in the window with a fresh break: on 2026-11-16 the
pair evaluated at 09:34:14 ET (46s before the window) and
09:51:24 ET (6m24s after it closed).

Cure shape (the desk's own precedents, no new machinery class):
the pair joins a named WINDOW roster in the ADA-WINDOW shape
(WINDOW_SIDS here, switch default ON, OFF restores the pre-cure
main-cycle-only behaviour exactly), and OpeningGammaWarmer
(desk3/producers_g4.py, the QullaScanWarmer shape) launches this
loop DETACHED on the first cycle touching 09:30-09:35 ET. The
loop polls at <=5s through the window for the two roster
sleeves only: fresh OpeningEventsProducer read -> the engine's
own evaluate() -> Dispatcher.process_intent. The strategy's
window, freshness gate and signal rules are untouched — the
route changes, the signal stays.

Every poll that sees an event row journals its outcome to
state/opening_gamma_window/journal.jsonl: gamma_window_eval for
an evaluation (with its intents and dispatch results) and
gamma_window_abstain, with a reason, when an event was seen but
no intent reached the door. An event a sleeve has already taken
to the door is consumed for that sleeve (keyed by symbol +
break_market_at) and never re-dispatched on a later poll.

Run as a module for the detached live form:
    python3 -m desk3.opening_gamma_scan <desk_root>
which builds the live dispatcher (PaperDoor via the runner's
credential route, slices seeded from the dispatcher journal,
the cycle's own seed_slices) lazily, only if an intent appears.
"""
from __future__ import annotations
import json, os
from datetime import datetime, time as _time, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# GAMMA-WINDOW-20261116: the WINDOW roster, ADA-WINDOW shape —
# exactly the pair whose designed window the fleet cycle cannot
# land in. No other sleeve joins the in-window scan.
WINDOW_SIDS = frozenset({"aster_open_gamma_a", "aster_open_gamma_b"})
WINDOW_START = _time(9, 35)
WINDOW_END = _time(9, 45)
LAUNCH_START = _time(9, 30)   # warmer launch band opens
POLL_S = 2.0                  # <= the strategy's 5s freshness gate


def window_scan_on(ctx=None):
    """Switch, ADA-WINDOW shape: default ON; an explicit
    gamma_window_scan=False in the call context turns the scan
    off, restoring the pre-cure main-cycle-only behaviour."""
    for src in (ctx, (ctx or {}).get("extra"),
                (ctx or {}).get("enhance")):
        if isinstance(src, dict) and "gamma_window_scan" in src:
            return bool(src["gamma_window_scan"])
    return True


def _in_window(now_et):
    return WINDOW_START <= now_et.time() < WINDOW_END


def _event_key(ev):
    return (ev.get("symbol"), ev.get("break_market_at"))


def _default_events(root):
    from .producers3 import OpeningEventsProducer
    prod = OpeningEventsProducer(root)

    def events(now):
        return (prod({"now": now}) or {}).get("opening_events") or []
    return events


def _default_view(root):
    snap_dir = os.path.join(root, "state", "snapshots")

    def view(now, rows):
        base = {}
        try:
            names = [n for n in os.listdir(snap_dir)
                     if n.endswith(".json")]
            if names:
                newest = max(
                    (os.path.join(snap_dir, n) for n in names),
                    key=lambda p: os.path.getmtime(p))
                from .snapshot import load_snapshot
                base = dict(load_snapshot(newest).plain)
        except Exception:
            base = {}  # no servable snapshot: the minimal view
            # below evaluates to a journaled abstention, never a
            # fabricated feed
        base["now"] = now.isoformat()
        base["opening_events"] = rows
        base.setdefault("positions", [])
        return base
    return view


def _default_evaluate(sid, view, ctx):
    from .aster_batch1 import evaluate
    return evaluate(sid, view, ctx)


class _LiveDispatch:
    """The loop's door: a real Dispatcher over the live book,
    built lazily on the first intent (PaperDoor via the runner's
    credential route; slices seeded from the dispatcher journal
    by the cycle's own seed_slices, so the loop's buying-power
    view is the desk's)."""

    def __init__(self, root):
        self.root = root
        self._disp = None
        self._view = None

    def _build(self, view):
        from .broker import PaperDoor
        from .cycle import seed_slices
        from .dispatcher import Dispatcher
        from .run_live import credential_env
        cfg = json.load(open(os.path.join(
            self.root, "config", "sleeves.json")))
        sleeves = {}
        for row in cfg["sleeves"]:
            if row["id"] in WINDOW_SIDS:
                sleeves[row["id"]] = {
                    "slice_usd": float(row["slice"]["capital_usd"])}
        try:
            slices = seed_slices(
                sleeves, os.path.join(self.root, "state",
                                      "dispatcher.jsonl"))
        except Exception:
            slices = {sid: {"capital_usd": s["slice_usd"],
                            "cash_usd": s["slice_usd"]}
                      for sid, s in sleeves.items()}
        self._disp = Dispatcher(
            self.root, PaperDoor(env=credential_env()), slices=slices,
            price_lookup=lambda sym: _price_from_view(view, sym))
        return self._disp

    def __call__(self, intent, sid, view=None):
        if self._disp is None:
            self._build(view or {})
        return self._disp.process_intent(intent, sid)


def _price_from_view(view, sym):
    q = ((view or {}).get("quotes") or {}).get(sym) or {}
    if q.get("bid") and q.get("ask"):
        return (float(q["bid"]) + float(q["ask"])) / 2
    bars = ((view or {}).get("bars") or {}).get(sym)
    if bars:
        return float(bars[-1]["c"])
    return None


def run_window_scan(root, now_fn=None, sleep_fn=None, events_fn=None,
                    view_fn=None, evaluate_fn=None, dispatch_fn=None,
                    journal_path=None, poll_s=POLL_S, enabled=True,
                    max_polls=None):
    """Poll the window for the WINDOW_SIDS pair. All seams are
    injectable so blockers drive the loop on a fixture clock with
    no network, broker or credentials. Returns a summary dict."""
    import time as _time_mod
    now_fn = now_fn or (lambda: datetime.now(timezone.utc))
    sleep_fn = sleep_fn or _time_mod.sleep
    if not enabled:
        return {"polls": 0, "evaluations": 0, "dispatched": 0,
                "abstentions": 0, "reason": "switch_off"}
    events_fn = events_fn or _default_events(root)
    view_fn = view_fn or _default_view(root)
    evaluate_fn = evaluate_fn or _default_evaluate
    live_dispatch = None
    if dispatch_fn is None:
        live_dispatch = _LiveDispatch(root)

        def dispatch_fn(intent, sid, _view=None):
            return live_dispatch(intent, sid, view=_view)
    journal_path = journal_path or os.path.join(
        root, "state", "opening_gamma_window", "journal.jsonl")
    summary = {"polls": 0, "evaluations": 0, "dispatched": 0,
               "abstentions": 0}
    consumed = set()    # (sid, symbol, break_market_at) taken to door
    abstained = set()   # (sid, symbol, break_market_at) already named

    def journal(row):
        try:
            os.makedirs(os.path.dirname(
                os.path.abspath(journal_path)), exist_ok=True)
            with open(journal_path, "a") as fh:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        except OSError:
            pass  # the summary still carries the count

    while True:
        now = now_fn()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        now_et = now.astimezone(ET)
        if now_et.time() >= WINDOW_END:
            break
        if max_polls is not None and summary["polls"] >= max_polls:
            break
        summary["polls"] += 1
        if _in_window(now_et):
            try:
                rows = events_fn(now) or []
            except Exception as e:  # named in the summary, loop lives
                summary["events_error"] = f"{type(e).__name__}:{e}"
                rows = []
            if rows:
                view = view_fn(now, rows)
                for sid in sorted(WINDOW_SIDS):
                    fresh = [ev for ev in rows
                             if (sid,) + _event_key(ev) not in consumed]
                    if not fresh:
                        continue
                    ctx = {"sleeve_id": sid,
                           "state_dir": os.path.join(
                               root, "state", sid),
                           "gamma_window_scan": True}
                    sview = dict(view)
                    sview["opening_events"] = fresh
                    try:
                        intents = evaluate_fn(sid, sview, ctx) or []
                    except TypeError:
                        intents = evaluate_fn(sid, sview) or []
                    summary["evaluations"] += 1
                    if intents:
                        results = []
                        for intent in intents:
                            try:
                                r = dispatch_fn(intent, sid, view)
                            except TypeError:
                                r = dispatch_fn(intent, sid)
                            results.append(
                                {"intent_id": intent.get("intent_id"),
                                 "status": (r or {}).get("status")})
                            summary["dispatched"] += 1
                        for ev in fresh:
                            consumed.add((sid,) + _event_key(ev))
                        journal({"event": "gamma_window_eval",
                                 "sleeve": sid, "ts": now.isoformat(),
                                 "symbols": [ev.get("symbol")
                                             for ev in fresh],
                                 "intents": len(intents),
                                 "results": results})
                    else:
                        new_abstain = [
                            ev for ev in fresh
                            if (sid,) + _event_key(ev) not in abstained]
                        if new_abstain:
                            for ev in new_abstain:
                                abstained.add((sid,) + _event_key(ev))
                            summary["abstentions"] += 1
                            journal({
                                "event": "gamma_window_abstain",
                                "sleeve": sid, "ts": now.isoformat(),
                                "symbols": [ev.get("symbol")
                                            for ev in new_abstain],
                                "reason": "event_seen_no_intent:"
                                          "the engine returned no "
                                          "intent for a fresh in-"
                                          "window event (its causal, "
                                          "chain or sizing gates "
                                          "refused on the served "
                                          "view)"})
        sleep_fn(poll_s)
    summary["window_sids"] = sorted(WINDOW_SIDS)
    return summary


def main(argv=None):
    import sys, time as _time_mod
    argv = list(sys.argv[1:] if argv is None else argv)
    root = os.path.abspath(argv[0]) if argv else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    summary = run_window_scan(
        root, sleep_fn=_time_mod.sleep)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
