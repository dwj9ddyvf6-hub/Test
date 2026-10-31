#!/usr/bin/env python3
"""Shared refresh-layer machinery for the terminal (adopted 2026-10-29
from the Shipyard live-terminal patterns; see
research_notes/codex-shipyard-live-terminal-20261029/LOOK.md section 4).

One source of truth for three contracts every refresh script shares:

1. QUOTE FRESHNESS GATE (fail-closed). Any figure derived from a live
   quote is checked at read time against QUOTE_MAX_AGE_SECONDS (90).
   A stale or missing quote yields an explicit stale / no_data state
   and the affected figures are withheld (set to None and named in
   ``figures_withheld``). An older cached value is NEVER substituted
   and presented as current.

2. FEED PROVENANCE. Every data.json written through this module's
   write path carries provenance fields: ``feed`` (source
   identifier), ``price_basis`` (for example sip, iex, delayed,
   indicative, close, snapshot, session_record),
   ``execution_pricing`` (False wherever figures are not executable
   prices, which is everywhere on this terminal), and a
   ``provenance`` block repeating the same facts. Values sourced from
   an indicative feed are renamed with the ``indicative_`` field-name
   prefix. Stamping only ADDS keys: existing fields keep their names
   and meanings, and consumers that do not read provenance are
   unaffected.

3. WRITE PATH. ``write_data_json`` stamps provenance and writes in
   the house style (indent=2, sort_keys, trailing newline). Refresh
   scripts wired to the stamp call ``stamp_for_script`` immediately
   before their own existing dump, so their file formatting and
   atomic-replace behaviour are unchanged.

Classification table: PROVENANCE_BY_SCRIPT maps each refresh script
to the feed its figures actually come from, derived from the inputs
that script reads (chain snapshot store, morgue feed, filed daily
bars, the forecast ledger, SEC/FINRA records). Scripts not in the
table fall back to filed_records / session_record, which is the true
state for a script whose inputs are dated files on disk.
"""

import json
import os
from datetime import datetime, timezone

QUOTE_MAX_AGE_SECONDS = 90
# Clock-skew tolerance for negative ages (CHAIN-SPOT-ANCHOR-20261031):
# a quote timestamped a few seconds AFTER the moment it is checked
# is a live quote from a clock running slightly ahead, not a stale
# one. Before this tolerance the freshness window was 0 <= age, so
# any capture whose quote landed seconds after the check instant
# was rejected as stale by construction (the chain collector lost
# 37 of 42 in-session captures on 2026-10-30 to exactly this). The
# tolerance is named and bounded: quotes more than this many
# seconds in the future are stale, fail-closed like old quotes.
QUOTE_CLOCK_SKEW_SECONDS = 30

# script filename -> (feed, price_basis). Derived from the inputs each
# script reads; see stamp_provenance.py for the derivation audit.
PROVENANCE_BY_SCRIPT = {
    "refresh_13ftracker.py": ("filed_records", "session_record"),
    "refresh_abstentionsignal.py": ("forecast_ledger", "close"),
    "refresh_activity.py": ("forecast_ledger", "close"),
    "refresh_agentdebate.py": ("filed_records", "session_record"),
    "refresh_aichartread.py": ("morgue_feed", "close"),
    "refresh_alerttape.py": ("filed_records", "session_record"),
    "refresh_analogue.py": ("forecast_ledger", "close"),
    "refresh_board.py": ("forecast_ledger", "close"),
    "refresh_breadth.py": ("morgue_feed", "close"),
    "refresh_breakoutscanner.py": ("morgue_feed", "close"),
    "refresh_calibrationleague.py": ("forecast_ledger", "close"),
    "refresh_capitulationclock.py": ("forecast_ledger", "close"),
    "refresh_chain.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_staticgex.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_completionclock.py": ("forecast_ledger", "close"),
    "refresh_correctedband.py": ("forecast_ledger", "close"),
    "refresh_correlation.py": ("morgue_feed", "close"),
    "refresh_darkprints.py": ("forecast_ledger", "close"),
    "refresh_decaywatch.py": ("filed_records", "session_record"),
    "refresh_earningscal.py": ("filed_records", "session_record"),
    "refresh_earningsdistribution.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_earningsdrift.py": ("forecast_ledger", "close"),
    "refresh_echoboard.py": ("filed_records", "session_record"),
    "refresh_echolens.py": ("filed_records", "session_record"),
    "refresh_exceedance.py": ("forecast_ledger", "close"),
    "refresh_expected_move.py": ("forecast_ledger", "close"),
    "refresh_familyfracture.py": ("forecast_ledger", "close"),
    "refresh_fearday.py": ("forecast_ledger", "close"),
    "refresh_feardayforecaster.py": ("filed_records", "session_record"),
    "refresh_feardaytriangulation.py": ("forecast_ledger", "close"),
    "refresh_filings.py": ("morgue_feed", "close"),
    "refresh_flow_tape.py": ("forecast_ledger", "close"),
    "refresh_flowboard.py": ("filed_records", "session_record"),
    "refresh_flowengine.py": ("filed_records", "session_record"),
    "refresh_gammaearningstrap.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_gammaladder.py": ("filed_records", "session_record"),
    "refresh_gapdestiny.py": ("forecast_ledger", "close"),
    "refresh_gapfill.py": ("forecast_ledger", "close"),
    "refresh_gradeaboard.py": ("forecast_ledger", "close"),
    "refresh_grademycall.py": ("morgue_feed", "close"),
    "refresh_graveyard.py": ("filed_records", "session_record"),
    "refresh_halflifeclock.py": ("forecast_ledger", "close"),
    "refresh_hollyideas.py": ("filed_records", "session_record"),
    "refresh_honestpop.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_horizongrades.py": ("filed_records", "session_record"),
    "refresh_idioliquidity.py": ("forecast_ledger", "close"),
    "refresh_inregimeoracle.py": ("forecast_ledger", "close"),
    "refresh_insider.py": ("morgue_feed", "close"),
    "refresh_insiderdivergence.py": ("forecast_ledger", "close"),
    "refresh_intakebias.py": ("forecast_ledger", "close"),
    "refresh_ivweather.py": ("filed_records", "session_record"),
    "refresh_livingrouter.py": ("forecast_ledger", "close"),
    "refresh_momentumclock.py": ("morgue_feed", "close"),
    "refresh_morning_map.py": ("morgue_feed", "close"),
    "refresh_mortalitycurve.py": ("forecast_ledger", "close"),
    "refresh_oddscards.py": ("filed_records", "session_record"),
    "refresh_onepagereport.py": ("filed_records", "session_record"),
    "refresh_openingrange.py": ("forecast_ledger", "close"),
    "refresh_ownnormdepth.py": ("forecast_ledger", "close"),
    "refresh_patterndraw.py": ("filed_records", "session_record"),
    "refresh_pinorescape.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_pinwatch.py": ("tastytrade_chain_snapshot", "snapshot"),
    "refresh_portfolio.py": ("forecast_ledger", "close"),
    "refresh_premiummeter.py": ("forecast_ledger", "close"),
    "refresh_proofgate.py": ("morgue_feed", "close"),
    "refresh_promotedbook.py": ("filed_records", "session_record"),
    "refresh_provingground.py": ("filed_records", "session_record"),
    "refresh_pullback.py": ("forecast_ledger", "close"),
    "refresh_receipts.py": ("forecast_ledger", "close"),
    "refresh_record.py": ("forecast_ledger_and_published_grades", "close"),
    "refresh_regime.py": ("filed_records", "session_record"),
    "refresh_replicationwire.py": ("morgue_feed", "close"),
    "refresh_reversalwire.py": ("filed_records", "session_record"),
    "refresh_rotation.py": ("morgue_feed", "close"),
    "refresh_router.py": ("filed_records", "session_record"),
    "refresh_screener.py": ("forecast_ledger", "close"),
    "refresh_second_opinion.py": ("forecast_ledger", "close"),
    "refresh_selfanalogue.py": ("forecast_ledger", "close"),
    "refresh_shortvol.py": ("morgue_feed", "close"),
    "refresh_signalfeed.py": ("finra_records", "session_record"),
    "refresh_silentaccumulation.py": ("forecast_ledger", "close"),
    "refresh_skewlens.py": ("filed_records", "session_record"),
    "refresh_smartmoney.py": ("filed_records", "session_record"),
    "refresh_sponsoredreset.py": ("forecast_ledger", "close"),
    "refresh_squeeze.py": ("forecast_ledger", "close"),
    "refresh_stratcombos.py": ("filed_records", "session_record"),
    "refresh_stratscanner.py": ("filed_records", "session_record"),
    "refresh_streaktrap.py": ("forecast_ledger", "close"),
    "refresh_stressreversal.py": ("forecast_ledger", "close"),
    "refresh_survivorswire.py": ("filed_records", "session_record"),
    "refresh_sweep_wire.py": ("forecast_ledger", "close"),
    "refresh_tapeheatmap.py": ("filed_records", "session_record"),
    "refresh_touchsurface.py": ("forecast_ledger", "close"),
    "refresh_unusualvolume.py": ("filed_records", "session_record"),
    "refresh_volclock.py": ("forecast_ledger", "close"),
    "refresh_voltermshape.py": ("forecast_ledger", "close"),
    "refresh_wallcheck.py": ("forecast_ledger", "close"),
    "refresh_walllifetime.py": ("forecast_ledger", "close"),
    "refresh_watchlistpulse.py": ("filed_records", "session_record"),
    "refresh_weekahead.py": ("filed_records", "session_record"),
    # The two daily runners (R-09 cure, 2026-10-30): they publish no
    # page of their own; their run summaries are stamped from the
    # filed records they orchestrate, like every other refresher.
    "refresh_engines.py": ("filed_records", "session_record"),
    "refresh_tools.py": ("filed_records", "session_record"),
    # The hub refresher (R-09 residual cure, 2026-10-30): it
    # publishes index.html, not a data.json; its run summary is
    # stamped from the filed records it reads (each card page's
    # own data file), like the two runners above.
    "refresh_hub.py": ("filed_records", "session_record"),
}

DEFAULT_PROVENANCE = ("filed_records", "session_record")


def provenance_for_script(script_path):
    name = os.path.basename(str(script_path))
    return PROVENANCE_BY_SCRIPT.get(name, DEFAULT_PROVENANCE)


def parse_ts(value):
    """Parse an ISO timestamp, epoch seconds, or YYYY-MM-DD date into
    an aware UTC datetime. Returns None when unparseable or missing."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except ValueError:
        pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def quote_freshness(quote_ts, now=None, max_age_seconds=QUOTE_MAX_AGE_SECONDS,
                    clock_skew_seconds=QUOTE_CLOCK_SKEW_SECONDS):
    """Freshness verdict for one live quote. Fail-closed: a missing or
    unparseable timestamp is no_data, never fresh. A quote is fresh
    when its age at the check moment lies in
    [-clock_skew_seconds, max_age_seconds]: the negative end is the
    named clock-skew tolerance (QUOTE_CLOCK_SKEW_SECONDS), so a
    live quote stamped seconds after the check instant passes,
    while a genuinely old quote, or one implausibly far in the
    future, is stale. Callers must pass ``now`` as the moment the
    quote was fetched, never an earlier run-start time."""
    now = now or datetime.now(timezone.utc)
    ts = parse_ts(quote_ts)
    if ts is None:
        return {"state": "no_data", "age_seconds": None,
                "max_age_seconds": max_age_seconds,
                "clock_skew_seconds": clock_skew_seconds,
                "quote_ts": None if quote_ts is None else str(quote_ts)}
    age = (now - ts).total_seconds()
    return {"state": "fresh" if -clock_skew_seconds <= age <= max_age_seconds
            else "stale",
            "age_seconds": round(age, 3),
            "max_age_seconds": max_age_seconds,
            "clock_skew_seconds": clock_skew_seconds,
            "quote_ts": ts.isoformat()}


def gate_figures(data, figure_keys, quote_ts, now=None,
                 max_age_seconds=QUOTE_MAX_AGE_SECONDS):
    """Apply the freshness gate to a record dict. Returns a copy. When
    the quote is fresh the figures pass through untouched. When it is
    stale or missing, every named figure that carried a value is
    withheld (None) and named in ``figures_withheld``; the record
    gains an explicit ``quote_freshness`` block and ``quote_state``.
    No older value is ever substituted."""
    out = dict(data)
    fresh = quote_freshness(quote_ts, now=now, max_age_seconds=max_age_seconds)
    out["quote_freshness"] = fresh
    out["quote_state"] = fresh["state"]
    if fresh["state"] == "fresh":
        out["figures_withheld"] = []
        return out
    withheld = []
    for key in figure_keys:
        if out.get(key) is not None:
            out[key] = None
            withheld.append(key)
    out["figures_withheld"] = withheld
    return out


def stamp_provenance(data, feed, price_basis, execution_pricing=False,
                     indicative_keys=()):
    """Return a copy of ``data`` with provenance fields added and any
    ``indicative_keys`` renamed to the ``indicative_`` prefix. Existing
    fields keep their names and meanings; a pre-existing top-level
    ``feed``/``price_basis`` value is preserved in the provenance
    block's ``declared_*`` slots rather than overwritten silently."""
    out = dict(data)
    for key in indicative_keys:
        if key in out and not key.startswith("indicative_"):
            out["indicative_" + key] = out.pop(key)
    prov = {"feed": feed, "price_basis": price_basis,
            "execution_pricing": bool(execution_pricing),
            "stamped_by": "terminal_common.stamp_provenance"}
    if "feed" in out and out["feed"] != feed:
        prov["declared_feed"] = out["feed"]
    if "price_basis" in out and out["price_basis"] != price_basis:
        prov["declared_price_basis"] = out["price_basis"]
    out["feed"] = feed
    out["price_basis"] = price_basis
    out["execution_pricing"] = bool(execution_pricing)
    out["provenance"] = prov
    return out


def stamp_for_script(data, script_path, **kwargs):
    feed, basis = provenance_for_script(script_path)
    return stamp_provenance(data, feed=feed, price_basis=basis, **kwargs)


def write_data_json(path, data, feed, price_basis, **kwargs):
    """Stamp provenance and write ``data`` as the tool's data.json in
    the house style. Returns the stamped dict."""
    stamped = stamp_provenance(data, feed=feed, price_basis=price_basis,
                               **kwargs)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(stamped, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return stamped


# ------------------------------------------------------------------
# MANIFEST SYNC (MANIFEST-SHARED-WRITE-20261031)
#
# Every refresh script in this tree imports this module, so it is
# the one write path they all share. Before this cure the asset
# manifest was rebuilt only by verify_terminal.sh at the end of
# the scheduled chains and by the opt-in republish_one.sh wrapper:
# a standalone refresher run (the exact exercise that proved the
# defect in two audit rounds) wrote its data file and left
# asset-manifest.json stale, so smoke_check.py failed on the
# delivered tree. The cure puts the rebuild here: importing this
# module snapshots the served files (the hub, every tool page and
# every data.json, the same set smoke_check.py serves); at process
# exit, if any served file changed during the process and the
# manifest no longer matches the tree, the manifest is rebuilt
# and written atomically. A read-only import changes nothing and
# writes nothing. The hook never fails the host process: a sync
# problem is named on stderr and the chains still end with
# verify_terminal.sh, which fails loudly as before.
# Set TERMINAL_NO_MANIFEST_SYNC=1 to disable (blocker tests use
# this to prove the fail direction on the pre-cure behaviour).

import atexit as _atexit
import sys as _sys

_SITE_DIR = os.path.dirname(os.path.abspath(__file__))
_MANIFEST_PATH = os.path.join(_SITE_DIR, "asset-manifest.json")


def _served_snapshot():
    snap = {}
    hub = os.path.join(_SITE_DIR, "index.html")
    if os.path.exists(hub):
        st = os.stat(hub)
        snap["index.html"] = (st.st_size, st.st_mtime_ns)
    for name in sorted(os.listdir(_SITE_DIR)):
        sub = os.path.join(_SITE_DIR, name)
        if not os.path.isdir(sub):
            continue
        for fname in ("index.html", "data.json"):
            p = os.path.join(sub, fname)
            if os.path.exists(p):
                st = os.stat(p)
                snap[f"{name}/{fname}"] = (st.st_size, st.st_mtime_ns)
    return snap


def _sync_manifest_on_exit():
    try:
        if _MANIFEST_SNAPSHOT is None:
            return
        if _served_snapshot() == _MANIFEST_SNAPSHOT:
            return  # this process wrote no served file
        import smoke_check
        manifest = smoke_check.build_manifest()
        try:
            with open(_MANIFEST_PATH, encoding="utf-8") as fh:
                current = json.load(fh)
        except (OSError, ValueError):
            current = None
        if current == manifest:
            return
        tmp = _MANIFEST_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, _MANIFEST_PATH)
    except Exception as exc:  # noqa: BLE001 - never fail the host
        print(f"terminal_common: manifest sync failed: {exc}",
              file=_sys.stderr)


_MANIFEST_SNAPSHOT = None
if (not os.environ.get("TERMINAL_NO_MANIFEST_SYNC")
        and os.path.exists(_MANIFEST_PATH)
        and os.path.exists(os.path.join(_SITE_DIR, "smoke_check.py"))):
    try:
        _MANIFEST_SNAPSHOT = _served_snapshot()
        _atexit.register(_sync_manifest_on_exit)
    except Exception:  # noqa: BLE001 - import must never break
        _MANIFEST_SNAPSHOT = None
