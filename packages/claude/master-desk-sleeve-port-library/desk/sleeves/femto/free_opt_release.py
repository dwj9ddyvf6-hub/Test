"""FREE_OPT_RELEASE — lean-desk port (Wave D, Decision #119 family).

master-desk: the Aurelia source desk's FREE_OPT_RELEASE_V1 descendant (preserves OPT_RELEASE_CONVEXITY) restored on
the engine (Agentic-Trading-Desk aurelia-paper-desk @1720157f768e: desk/free_options.py evaluate / execute and
desk/option_packages.py submit_package / manage_exits — the rules vendored as desk/vendor/aurelia/free_options.py,
the execution in free_opt_core). Buy the call AND the put (a straddle) only when a verified public event timestamp
is loaded for the session; a single put is never a straddle.

  entry .... evaluate(): the indicative probe fresh (source <= 90 s, receipt <= 30 s, 2 s future tolerance, bid > 0,
             ask >= bid), a verified event whose session is today's (the UTC date of the clock, as the source
             compared) and a package of exactly 2 legs, rights {call, put} -> submit_package() while the market is
             open: once per package id; not a model test, deliverable, both legs present, fresh and within 30 s of
             each other, its max loss inside its risk cap and the $100,000 pool; broker_mleg -> one multi-leg order
             at the price the package journal booked (the call's and the put's asks).
  exits .... the package's exit_at (the contract: the session after the event, or expiry) once passed while the
             market is open; at expiry the engine settles. Both legs close together.

  events ... produced on the desk (the source's run() always passed events=[]: no release calendar existed in its
             tree): desk/feedlib/release_calendar.py, cached by the release_calendar job from the official public
             schedules — CPI and the Employment Situation (08:30 ET) from FRED's release calendar, the FOMC statement
             (2:00 pm ET on each scheduled meeting's last day) from the Fed's meeting calendar; each event verified,
             with its source URL and page hash, dated to the last trading session that opens before it (an 08:30 ET
             release to the previous session, the FOMC statement to its own), so the straddle is held into it.
  package .. produced on the desk: desk/feedlib/free_options_inputs.release — on a session with a verified event,
             the ATM straddle on the nearest expiry after the session following the event's; 1 package, one per
             event session and one open at a time; max loss = the natural debit; exit_at 5 minutes after the open
             of the session after the event.

Gone under the cutover doctrine: the desk kill switch and the pre-trade clock-skew block (free_paper.run passed
send=False when either fired); the Femto fences of the old desk's copy (no snapshot fetch, sim packages); the
missing-producer block (status monitor).
Named divergences: the calendar (its releases: CPI, the Employment Situation and the FOMC statement — the source
named only "a verified public event timestamp"; FRED's mirror of the BLS schedule, bls.gov refusing automated
requests) and the package producer above (the contract rule, the exit 5 minutes after the next session's open);
the decision moment is the chain's receipt when the pass fetched it after its start; its own $100,000 book and pool
(the source's descendants shared one $100,000 pool); the package is
bought at the natural debit its journal booked (the source's multi-leg order carried the larger leg ask alone as
its limit, and quantity 1); a package that closes, or never opens, releases its risk reservation (the source never
released one); a due package closes through the OMS at its natural (the source booked the close at the entry
prices in a local journal and sent no order); a package whose exit_at has already passed when it is sent closes on
the next pass (the source booked both in one pass); a package the OMS never fills leaves the book and releases its
risk (the source's journal held it open from the broker's acknowledgement); a package with a leg that lacks its side
of the market sends nothing (the source's journal bought the legs before it at the ask and sold them back at the
bid); the probe is the desk's chain (received when the chain was fetched); a pass every 5 minutes of the session
(the source evaluated every ~20-second cycle).

Inputs via context.extra:
  "quote"        the indicative probe {"symbol","bp","ap","t","received_at"}
  "events"       [{"name","release_at","session": "YYYY-MM-DD","verified": True,"source","source_sha256"}] (feed
                 release_events: desk/feedlib/release_calendar.py)
  "package"      the straddle package (as free_opt_own_iv) (free_options_inputs.release)
  "release"      the producer's {"expiration","reason"}
  "market_open"  the clock's is_open
  "legs" / "pending"  the sleeve's option positions and working orders
  "meta"         {"packages": {client id: record}}
  "decided_at"   the chain's receipt when later than the pass's clock (free_opt_core.moment_of)
"""
from .compat import BaseSleeve, SleeveConfig
from . import free_opt_core as C

SPEC_ID = "FREE_OPT_RELEASE_V1"
ACCOUNT = "free_options"
BUDGET_USD = 100_000.0

CONFIG = SleeveConfig(
    sleeve_id="free_opt_release", cadence_s=300, universe=(),
    state_schema={"position": "dict|None"}, risk_pct=None)


def decide(bars, context):
    return C.decide_packages(SPEC_ID, context)


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_free_opt_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_free_opt_pass"] = memo
    return memo[1]


class FreeOptRelease(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return FreeOptRelease().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    meta = dict((context.extra or {}).get("meta") or {})
    meta["packages"] = _pass(bars, context)["packages"]
    return meta


def monitor(mod, bars, context):
    r = _pass(bars, context)["row"]
    why = ((context.extra or {}).get("release") or {}).get("reason")
    return [("SPY", "%s %s: %s%s" % (SPEC_ID, r["status"], r.get("reason") or "", " [%s]" % why if why else ""),
             {"status": r["status"]})]
