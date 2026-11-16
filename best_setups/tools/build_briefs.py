"""Build setup briefs + charts for a curator setups document
(2026-10-15; Addition 5 changes noted inline).

Reads a setups JSON produced by tools/build_setups.py, and for each
of its board setups composes the full brief (core/setup_brief.py,
including the holistic Desk read) and renders the marked-up chart.
Bars come through the desk's own doors (tools/run_live.py:
alpaca_daily_bars for the daily panel + geometry, alpaca_1h_bars
for the recent hourly panel). Read-only against the desk state;
every output path is the caller's choice.

Addition 5 wiring (MERGE_PLAN §11): briefs are built for EVERY
board setup by default (--all; the board is the curator's
`setups` list — every published name, score >= MIN_SCORE).
--top N remains for ad-hoc runs. Three Additions ride along:

* CHART RE-RENDER GUARD: rendering is the expensive step. A
  sidecar (<SYM>-<session>.inputs.json) records the hash of the
  inputs a chart was rendered from (bars + setup record + hourly
  bars). When the PNGs and the sidecar exist and the hash is
  unchanged, the render is skipped and the existing artifacts are
  re-attached — a publish cycle whose inputs did not change pays
  for text, not pixels.
* READ LEDGER: every brief build appends its Desk read to an
  append-only ledger (default: read_ledger.jsonl next to --out),
  one row per (session, symbol) — the FIRST build of a session is
  the recorded read, so a later same-session rebuild never
  rewrites the record the outcome scorer will grade.
* COMPLETED CARRY: names in the setups doc's `completed`
  section are NOT re-briefed. A completed name keeps the read
  that was generated while it was live: its brief is carried
  forward verbatim from the previous briefs document into
  `briefs_completed`.

Chart publication pattern (see MERGE_PLAN.md): charts are files,
named <SYMBOL>-<session>.png, published alongside the feed; the
brief carries the path relative to the terminal page
(setup-charts/<SYMBOL>-<session>.png by default).

Usage:
  python3 tools/build_briefs.py --setups state/live/setups_latest.json \
      --out state/live/setup_briefs.json --charts-dir /path/to/charts
"""
import argparse
import hashlib
import os
import json
import pathlib
import sys
import tarfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from core import refusal, setup_brief, setup_card, surface_seal  # noqa: E402
from core import visual_filing  # noqa: E402


def _bar_session_date(t, hourly):
    """The session date a bar belongs to, for the hash pin:
    daily bars carry their session as the UTC date (the
    disk layer's 04:00Z convention); hourly bars carry a
    UTC instant whose ET date is the session."""
    if not t:
        return None
    ts = str(t)
    if not hourly:
        return ts[:10]
    try:
        import datetime as _dt
        from zoneinfo import ZoneInfo
        dt = _dt.datetime.fromisoformat(
            ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        return dt.astimezone(
            ZoneInfo("America/New_York")).date().isoformat()
    except Exception:
        return ts[:10]


def _inputs_hash(setup, daily_bars, hourly_bars):
    # R2526 BG1 (§64 A-54): the hash binds only the pinned
    # session's bars. The doors were pinned one at a time
    # (AF0 hourly, §43 daily), but this hash — the one a
    # counted visual read files against — hashed whatever
    # bar lists the caller handed it verbatim, so a later
    # session's forming bar or a post-as_of hourly bar from
    # an unpinned route churned it between two builds of
    # the same as_of and stranded the reads (rounds 23-26,
    # every round in some form). Bars dated after the
    # setup's own as_of session are not hash inputs, exactly
    # as §43 BG2 already bars them from derivations. Bars
    # ON the session still bind, in full.
    pin = str((setup or {}).get("as_of") or "")[:10]
    daily = [b for b in (daily_bars or [])
             if not pin or (_bar_session_date(
                 b.get("t"), hourly=False) or "") <= pin]
    hourly = [b for b in (hourly_bars or [])
              if not pin or (_bar_session_date(
                  b.get("t"), hourly=True) or "") <= pin]
    h = hashlib.sha256()
    h.update(json.dumps(setup, sort_keys=True, default=str).encode())
    h.update(json.dumps(daily, default=str).encode())
    h.update(json.dumps(hourly, default=str).encode())
    return h.hexdigest()


def _card_digest(brief, inputs_digest):
    """THE CARD's own cache key (Amendment A-2 (§12)): the shared
    inputs hash PLUS the brief material the card actually prints
    — the call, the plan, the levels, the instrument. A change
    in the call's words alone re-renders the card image even
    when bars and setup are unchanged, so the image and the
    post text can never drift (the frozen-manifest lesson from
    the Hypedesk corpus)."""
    h = hashlib.sha256()
    h.update(inputs_digest.encode())
    h.update(json.dumps({
        "the_call": brief.get("the_call"),
        "plan": brief.get("plan"),
        "levels": brief.get("levels"),
        "instrument": brief.get("instrument"),
        "elliott_headline": (brief.get("elliott") or {})
        .get("headline"),
        "score": brief.get("score"), "tier": brief.get("tier"),
        "status": brief.get("status"),
    }, sort_keys=True, default=str).encode())
    return h.hexdigest()


_PRIOR_DOCS_CACHE = {}
_PRIOR_DOCS_CACHE_MAX = 8


def _stat_row(p):
    try:
        st = p.stat()
        return (True, st.st_size, st.st_mtime_ns)
    except Exception:
        return (False, None, None)


def _prior_docs_fingerprint(out_path, bdir, tars):
    """The true-input fingerprint of one _prior_brief_docs scan:
    the resolved backup dir, each scanned tar's (name, size,
    mtime) plus its sidecar's and manifest's (exists, size,
    mtime), and the out document's (exists, size, mtime). Any
    change to an archive, a sidecar, a manifest, or the prior
    document changes the fingerprint, so a cached result can
    never serve stale docs for changed inputs."""
    rows = []
    for tar in tars[:8]:
        stem = tar.name[:-len(".tar.gz")]
        rows.append((
            tar.name, _stat_row(tar),
            _stat_row(tar.with_name(stem + ".setup_briefs.json")),
            _stat_row(tar.with_name(stem + ".manifest.json"))))
    out_row = None
    if out_path is not None:
        out_row = (str(out_path), _stat_row(pathlib.Path(out_path)))
    return (str(bdir), tuple(rows), out_row)


def _scan_prior_brief_docs(out_path, bdir, tars):
    docs = []
    if out_path is not None and out_path.exists():
        try:
            docs.append(json.loads(out_path.read_text()))
        except Exception:
            pass
    for tar in tars[:8]:
        stem = tar.name[:-len(".tar.gz")]
        sidecar = tar.with_name(stem + ".setup_briefs.json")
        try:
            if sidecar.exists():
                docs.append(json.loads(sidecar.read_text()))
                continue
        except Exception:
            pass
        # GESTALT-SUITE-BUDGET-20261024: a tarball with no
        # manifest is an INCOMPLETE artifact — core/backup.py
        # writes the manifest only after the artifact verifies
        # (and publishes the sidecar in the same step), so a
        # manifest-less, sidecar-less tar is an in-flight or
        # truncated write. Opening one re-pays a full gzip scan
        # to its EOF failure on EVERY build (the truncated
        # 2026-10-24 artifact cost ~60 s per call and could
        # never backfill, the exception path swallowing the
        # failure per-tar). It is never opened; fail-soft
        # semantics are preserved — the history simply
        # shortens, exactly as for an unreadable snapshot.
        if not tar.with_name(stem + ".manifest.json").exists():
            continue
        try:
            with tarfile.open(tar) as tf:
                fh = tf.extractfile(
                    "state/live/setup_briefs.json")
                if fh is not None:
                    raw = fh.read()
                    docs.append(json.loads(raw))
                    # Lazy backfill: the next build reads the
                    # sidecar, never this tarball again.
                    try:
                        tmp = sidecar.with_name(
                            "." + sidecar.name + ".tmp")
                        tmp.write_bytes(raw)
                        tmp.replace(sidecar)
                    except Exception:
                        pass
        except Exception:
            continue
    return docs


def _prior_brief_docs(out_path):
    """The desk's retained brief history, newest first: the
    briefs document this build is about to replace (the prior
    cycle), then the daily backup snapshots (core/backup.py's
    area), each carrying its own state/live/setup_briefs.json.
    Read-only and fail-soft — a missing or unreadable snapshot
    only shortens the history, and a shorter history can cost
    the post's serial line its date, never invent one. Feeds
    setup_card.unchanged_call_fact (the "Still no changes"
    line, X Chart Study addendum §5).

    PERF-1 (2026-10-19): each snapshot's member is read from the
    sidecar core/backup.py publishes beside the tar
    (femto-lean-backup-<stamp>.setup_briefs.json). The tar itself
    is opened only for a snapshot with no sidecar, and that read
    lazily backfills the sidecar — re-scanning a whole tarball
    per build cost ~87 s once artifacts reached 97 MB.

    GESTALT-SUITE-BUDGET-20261024: results are memoized in
    process on the true-input fingerprint (see
    _prior_docs_fingerprint), NEGATIVE results included — a
    scan that paid a truncated tar's EOF failure once never
    pays it again while its inputs stand. Callers receive a
    deep copy, so the cached docs can never be mutated through
    a returned list."""
    import copy as _copy
    try:
        from core import backup as _backup_mod
        # EXEC-20261021-3: the backup-history door is isolable —
        # FEMTO_BACKUP_DIR (the FEMTO_TEST_TIMEOUT_S precedent)
        # points the scan at a caller-owned area; hermetic builds
        # and tests must never scan (or backfill-write into) the
        # shared workspace corpus, whose growth otherwise taxes
        # every build and couples fixtures to production state.
        _bdir = (pathlib.Path(os.environ["FEMTO_BACKUP_DIR"])
                 if os.environ.get("FEMTO_BACKUP_DIR")
                 else _backup_mod.DEFAULT_BACKUP_DIR)
        tars = sorted(
            _bdir.glob(
                "femto-lean-backup-*.tar.gz"),
            reverse=True)
    except Exception:
        _bdir, tars = None, []
    if _bdir is None:
        # The history door itself failed to resolve: the prior
        # document (when readable) is the whole history.
        docs = []
        if out_path is not None and out_path.exists():
            try:
                docs.append(json.loads(out_path.read_text()))
            except Exception:
                pass
        return docs
    try:
        fp = _prior_docs_fingerprint(out_path, _bdir, tars)
    except Exception:
        fp = None
    if fp is not None and fp in _PRIOR_DOCS_CACHE:
        return _copy.deepcopy(_PRIOR_DOCS_CACHE[fp])
    docs = _scan_prior_brief_docs(out_path, _bdir, tars)
    if fp is not None:
        if len(_PRIOR_DOCS_CACHE) >= _PRIOR_DOCS_CACHE_MAX:
            _PRIOR_DOCS_CACHE.pop(
                next(iter(_PRIOR_DOCS_CACHE)), None)
        _PRIOR_DOCS_CACHE[fp] = _copy.deepcopy(docs)
    return docs


def _append_read_ledger(ledger_path, briefs, as_of):
    """Append Desk-read rows for board briefs, one per
    (session, symbol) — first build of the session stands."""
    if ledger_path is None:
        return 0
    seen = set()
    if ledger_path.exists():
        for line in ledger_path.read_text().splitlines():
            try:
                row = json.loads(line)
                seen.add((row.get("session"), row.get("symbol")))
            except Exception:
                continue
    rows = []
    for sym, brief in briefs.items():
        if (as_of, sym) in seen:
            continue
        rows.append(setup_brief.read_ledger_row(brief, as_of=as_of))
    if rows:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("a") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
    return len(rows)


_VISUAL_VERDICTS = {"supports", "opposes", "no view"}
_VISUAL_CONFIDENCE = {"LOW", "MED"}


def _load_visual_read(visual_dir, sym, as_of, inputs_hash):
    """GESTALT Phase 2 (§19): load the Pass B visual read for
    one name from the reader's sidecar
    ({visual_dir}/{SYM}-{session}.json). The sidecar is a
    model-vision artifact recorded by the orchestrating agent
    after viewing the rendered charts (tools/build_briefs.py
    writes the request manifest naming the exact charts +
    Pass A summary). Fail-closed to None — the brief then
    prints the named absence — on: no dir, no file, malformed
    JSON, wrong symbol/session, a STALE inputs hash (the read
    was taken over different bars than this build's), or a
    read record outside the schema (status read/abstain; a
    read carries a verdict in {supports, opposes, no view}
    and a confidence in {LOW, MED} — never HIGH, per the
    skill's Pass B rules)."""
    if not visual_dir:
        return None
    try:
        doc = json.loads((pathlib.Path(visual_dir)
                          / f"{sym}-{as_of}.json").read_text())
    except Exception:
        return None
    if not isinstance(doc, dict):
        return None
    if doc.get("symbol") not in (None, sym):
        return None
    if str(doc.get("session") or "") != str(as_of):
        return None
    if doc.get("inputs_hash") != inputs_hash:
        return None
    status = doc.get("status") or "read"
    if status not in ("read", "abstain"):
        return None
    if status == "read":
        if doc.get("verdict") not in _VISUAL_VERDICTS:
            return None
        if doc.get("confidence") not in _VISUAL_CONFIDENCE:
            return None
        # ROUND-7 ADJUST N4 (§23 A-13), the load-side
        # fence: the verdict judges the STAGED direction
        # (pinned in the schema and on every filing the
        # helper writes). A sidecar whose verdict
        # contradicts its own scenario lean — GEN/ES/O
        # filed "supports" for an against lean — fails
        # closed here too, so an ambiguous token is never
        # weighed however the file arrived.
        # ROUND-11 ADJUST S1 (§27 A-17): the fence reads
        # the filing's own frame — on a contrary frame the
        # branch the verdict supports is the contrary one.
        if not visual_filing.verdict_lean_consistent(
                doc.get("verdict"), doc.get("lean_target"),
                contrary_frame=visual_filing.frame_contrary(
                    doc.get("verdict_vs_call"))):
            return None
    doc = dict(doc)
    doc["status"] = status
    if status == "read":
        # §27 A-17 (S1): the stance the weighing consumes
        # is DERIVED here, once — the verdict's sign
        # relative to the plan object, flipped exactly
        # when the filing's recorded frame was a contrary
        # call. The brief builder reads plan_stance and
        # never re-derives from the raw verdict.
        doc["plan_stance"] = visual_filing.derive_plan_stance(
            doc)
    if status == "read":
        # THE COURTROOM (Stage 4): the fixed view set. Every
        # frame the reader claims to have viewed must belong
        # to the set the build renders — a claimed frame
        # outside the set is a schema violation and the read
        # fails closed (the name prints the absence instead).
        canon = set()
        for f in doc.get("frames_viewed") or []:
            fl = str(f).lower()
            got = set()
            if "week" in fl:
                got.add("weekly")
            if "annotated" in fl:
                got.update(("daily", "hourly"))
            elif "daily" in fl:
                got.add("daily")
            if "hour" in fl or "1h" in fl:
                got.add("hourly")
            if "plan" in fl:
                got.add("plan")
            if "card" in fl:
                got.add("card")
            if "mobile" in fl or "phone" in fl:
                got.add("mobile")
            if not got:
                return None
            canon |= got
        doc["frames_canonical"] = sorted(canon)
    return doc


# The visual expert's fixed view set (Stage 4): the frames the
# build renders for every name, declared on every request.
VIEW_SET = ["weekly", "daily", "hourly", "plan", "card", "mobile"]


def _companyfacts(sib, cik, _fetch=None):
    """GESTALT G3 (2026-10-17): the EDGAR companyfacts doc for
    one CIK. The producer (tools/run_live.edgar_float_frames)
    caches under state/live/mcap_facts/ as CIK{cik}.json; the
    reader here used to look for the bare {cik:010d}.json, a
    name no producer ever wrote — the §13 fundamentals slice
    resolved for 0 of 115 audited briefs while hundreds of
    cache files sat on disk. Read the producer's name first
    (the legacy name stays as fallback); a missing or
    older-than-7-days cache (the producer's own TTL) refreshes
    through the same door (data.sec.gov, the desk's UA) and is
    written back in the producer's format — gated on a live
    product area existing beside the setups doc, so hermetic
    builds never fetch. Fail-soft: on any failure the stale
    cache, when one exists, still serves; otherwise None.

    W-1/E-1 cure (2026-10-19): the producer's format is now the
    extracted PROJECTION (core/edgar_projection — the consumed
    series only, KBs per CIK), and this reader returns the doc
    shape rebuilt from it, values byte-equal to the raw path.
    Legacy raw-document cache files still serve and migrate
    to the projection on read, mtime (the TTL clock)
    preserved."""
    import time as _t
    from core import edgar_projection as _ep
    d = pathlib.Path(sib) / "mcap_facts"
    raw, fresh = None, False
    for p in (d / f"CIK{cik}.json", d / f"{int(cik):010d}.json"):
        try:
            cached = json.loads(p.read_text())
            doc = _ep.doc_from_cached(cached)
            if doc is None:
                continue
            raw = doc
            fresh = (_t.time() - p.stat().st_mtime) < 7 * 86400
            if not _ep.is_projection(cached):
                _ep.migrate_cache_file(p, cached, cik=cik)
            break
        except Exception:
            continue
    live_area = (pathlib.Path(sib) / "mcap_facts").is_dir() \
        or (pathlib.Path(sib) / "gap_products").is_dir()
    if (raw is None or not fresh) and live_area:
        try:
            if _fetch is not None:
                doc = _fetch(int(cik))
            else:
                import urllib.request as _u
                req = _u.Request(
                    "https://data.sec.gov/api/xbrl/companyfacts/"
                    f"CIK{int(cik):010d}.json",
                    headers={"User-Agent":
                             "FemtoDesk/1.0 (quant research)",
                             "Accept": "application/json"})
                with _u.urlopen(req, timeout=30) as r:
                    doc = json.loads(
                        r.read().decode("utf-8", "replace"))
            if doc:
                try:
                    d.mkdir(parents=True, exist_ok=True)
                    (d / f"CIK{cik}.json").write_text(json.dumps(
                        _ep.extract_projection(
                            doc, cik=cik, fetched_at=_t.time())))
                except Exception:
                    pass
                raw = doc
        except Exception:
            pass  # a stale cache, when one exists, still serves
    return raw


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--setups", required=True,
                    help="curator setups JSON (tools/build_setups.py output)")
    ap.add_argument("--out", default=None,
                    help="write the briefs JSON here (default: stdout)")
    ap.add_argument("--charts-dir", default=None,
                    help="directory to write chart PNGs into "
                         "(default: no charts rendered)")
    ap.add_argument("--chart-prefix", default="setup-charts",
                    help="path prefix stored in each brief "
                         "(relative to the terminal page)")
    ap.add_argument("--top", type=int, default=None,
                    help="briefs for the top N setups (default: "
                         "ALL board setups — Addition 5 wiring)")
    ap.add_argument("--symbols", default=None,
                    help="comma-separated symbols to brief instead "
                         "of the top N")
    ap.add_argument("--market-measurements", default=None,
                    help="Phase 3.5 market-measurements JSON "
                         "(default: market_measurements.json next "
                         "to the setups file, when it exists)")
    ap.add_argument("--read-ledger", default=None,
                    help="append Desk reads to this JSONL ledger "
                         "(default: read_ledger.jsonl next to "
                         "--out; 'none' disables)")
    ap.add_argument("--no-gap-ensure", action="store_true",
                    help="skip the on-boarding gap-product build "
                         "(GESTALT G1): by default, when a "
                         "gap_products area exists beside the "
                         "setups doc, products are built for any "
                         "briefed name missing from them")
    ap.add_argument("--visual-dir", default=None,
                    help="directory holding Pass B visual-read "
                         "sidecars ({SYM}-{session}.json, §19); "
                         "default: a 'visual_reads' directory "
                         "beside the setups doc when one exists; "
                         "'none' disables the visual voice")
    args = ap.parse_args(argv)

    doc = json.loads(pathlib.Path(args.setups).read_text())
    as_of = doc.get("as_of")
    mc = doc.get("market_context")
    notes = doc.get("notes") or []
    wanted = ([s.strip().upper() for s in args.symbols.split(",")]
              if args.symbols else None)
    setups = doc.get("setups") or []
    if wanted:
        setups = [s for s in setups if s.get("symbol") in wanted]
    elif args.top:
        setups = setups[:args.top]
    # DA-1 (Cure Program 2, Stage 2): entered names are positions,
    # not board setups — but their plans are how the positions are
    # managed, so they are briefed too and published under the
    # feed's entered_setups section (positions surface).
    entered_rows = doc.get("entered") or []
    if wanted:
        entered_rows = [s for s in entered_rows
                        if s.get("symbol") in wanted]
    setups = setups + entered_rows

    mm = None
    mm_path = args.market_measurements or str(
        pathlib.Path(args.setups).parent / "market_measurements.json")
    if mm_path and pathlib.Path(mm_path).exists():
        try:
            mm = json.loads(pathlib.Path(mm_path).read_text())
        except Exception:
            mm = None
    # THE COURTROOM (Stage 5): the GEX state doc rides the
    # market measurements to the context expert's voice.
    _gex_path = pathlib.Path(args.setups).parent / "gex_state.json"
    _gex_doc_gw3 = None
    if _gex_path.exists():
        try:
            _gex_doc = json.loads(_gex_path.read_text())
            _gex_doc_gw3 = _gex_doc
            mm = dict(mm or {})
            mm["gex"] = _gex_doc
        except Exception:
            pass
    # THE COURTROOM (Stage 6): the leash state rides along —
    # the arbiter caps leashed voices out of the decisive band.
    _leash_path = (pathlib.Path(args.setups).parent
                   / "calibration" / "leash_state.json")
    if _leash_path.exists():
        try:
            _leash_doc = json.loads(_leash_path.read_text())
            mm = dict(mm or {})
            mm["leash"] = _leash_doc
        except Exception:
            pass

    # EXEC-20261021-2 (GW-3 remainder): this consumer asserts the
    # freshness contract on the products it rides — the market
    # measurements and the GEX state — and the lector ranks below.
    # Staleness is a NAMED finding in the briefs document, never
    # silence; context products are stance 0 and never decisive,
    # so a stale one degrades by name, never blocks the build.
    from core import gateway as _gw3
    freshness_rows = _gw3.consumer_freshness(
        {"market_context": mm, "gex_state": _gex_doc_gw3})
    for _r in freshness_rows:
        print(f"  freshness finding: {_r['product']}: {_r['reason']}")

    briefs = {}
    if setups:
        from tools.run_live import alpaca_1h_bars, alpaca_daily_bars
        from core import chart_read
        from core import m2_features as _m2
        syms = [s["symbol"] for s in setups]
        # §13 (Amendment A-3): the consideration record's external
        # inputs ride the SAME doors the brief already uses — the
        # benchmarks and sector proxies through the bars door, the
        # lector ranks / tensor memo / EDGAR facts as sibling
        # files of the setups doc (the market_measurements
        # pattern), the earnings + macro calendars through
        # core/event_feeds.py's own paths and freshness law.
        _bench_syms = (["SPY", "UUP"]
                       + sorted(set(_m2.DESK_SECTOR_ETF.values()))
                       + sorted(_m2.SECTORS))
        # GESTALT G2 (2026-10-17): sector resolution for ANY
        # name — the desk bucket first, else the GICS map
        # (core/sector_map.py). Assignments resolve BEFORE the
        # bars fetch so the peer symbols and the 11 SPDRs ride
        # the same door as everything else.
        from core import sector_map as _smap
        _assignments = {s: _smap.assignment(s) for s in syms}
        _gics_peers = sorted({p for a in _assignments.values()
                              if a for p in a["peers"]})
        _bench_syms = list(dict.fromkeys(
            _bench_syms + list(_smap.SPDRS) + _gics_peers))
        _fetch_syms = list(dict.fromkeys(syms + _bench_syms))
        # SA-10: the chart pipeline reads SPLIT-ADJUSTED bars.
        # Raw bars print a recorded split as a one-day cliff
        # (CVNA's 5-for-1 of 2026-05-08 read as -80.5%) and every
        # average/pattern fitted across it is an artifact.
        daily_full = alpaca_daily_bars(_fetch_syms, session=as_of,
                                       adjustment="split")
        # The door returns full history; the brief needs the recent
        # window (chart ~6 months + geometry lookback + the chart
        # read's 200-day average and dominant swing). The name's
        # FULL history rides along for the consideration record's
        # own-history facts (seasonality, the stretch rank).
        daily = {s: (b or [])[-320:]
                 for s, b in daily_full.items()}
        bench = {s: daily.get(s) for s in _bench_syms}
        _sib = pathlib.Path(args.setups).parent
        lector_rows = {}
        try:
            _lr = json.loads((_sib / "lector" / "ranks_top15.json")
                             .read_text())
            lector_rows = {r["symbol"]: r
                           for r in _lr.get("ranks") or []}
            freshness_rows += _gw3.consumer_freshness(
                {"lector": _lr})
        except Exception:
            lector_rows = {}
        tensor_rows = {}
        # GESTALT G4 (2026-10-17): the memo's per-name
        # diagnostics snapshots ride beside the signal rows —
        # the tensor_timeframes item states the canonical
        # series' newest diagnostics state for every evaluated
        # name, signal or not (core/tensor_feeds.py writes the
        # "diag" field; memos written before the cure simply
        # lack it and the item names that).
        tensor_diags = {}
        try:
            _tm = json.loads((_sib / "tensor_signals_memo.json")
                             .read_text())
            tensor_rows = {s: (v or {}).get("row")
                           for s, v in
                           (_tm.get("rows") or {}).items()}
            tensor_diags = {s: (v or {}).get("diag")
                            for s, v in
                            (_tm.get("rows") or {}).items()}
        except Exception:
            tensor_rows = {}
            tensor_diags = {}
        earnings_by_sym = {}
        macro_doc = None
        try:
            from core import event_feeds as _ef
            import time as _time
            _edoc = json.loads(
                pathlib.Path(_ef.EARNINGS_JSON).read_text())
            _dates, _fresh = _ef.earnings_from_doc(
                _edoc, _time.time())
            earnings_by_sym = {
                s: {"date": d, "stale": not _fresh,
                    "updated": _edoc.get("updated_ts")}
                for s, d in _dates.items()}
            if not _fresh:
                for _v in earnings_by_sym.values():
                    _v["stale"] = True
            earnings_by_sym["__stale__"] = not _fresh
            earnings_by_sym["__updated__"] = _edoc.get("updated_ts")
            macro_doc = json.loads(
                pathlib.Path(_ef.MACRO_EVENTS).read_text())
        except Exception:
            earnings_by_sym, macro_doc = {}, None
        cik_map = {}
        try:
            from core import event_feeds as _ef2
            cik_map = json.loads(
                pathlib.Path(_ef2.CIK_MAP).read_text())
        except Exception:
            cik_map = {}
        # Stage 5 (2026-10-16): the gap products — EDGAR, shorts,
        # news, attention, options (core/gap_products.py) — ride
        # to the consideration record as stamped slices. TTLs
        # follow each product's cadence (options 30 min, news 6 h
        # build / daily full, EDGAR + attention daily); a product
        # past its TTL reaches the record STALE and states no
        # values — the earnings freshness law, generalized.
        import time as _gtime
        import datetime as _gdt
        _gap_docs = {}
        for _fam in ("options", "edgar", "shorts", "news",
                     "attention"):
            try:
                _gap_docs[_fam] = json.loads(
                    (_sib / "gap_products" / f"{_fam}.json")
                    .read_text())
            except Exception:
                _gap_docs[_fam] = {}
        _gap_ttl = {"options": 3 * 3600, "news": 24 * 3600,
                    "edgar": 48 * 3600, "attention": 72 * 3600}
        _iv_hist = {}
        try:
            for _ln in (_sib / "gap_products"
                        / "iv_history.jsonl").read_text() \
                    .splitlines():
                _r = json.loads(_ln)
                _iv_hist.setdefault(_r.get("symbol"), []).append(
                    {"session": _r.get("session"),
                     "iv_pct": _r.get("iv_pct")})
        except Exception:
            _iv_hist = {}
        _family_doc = None
        try:
            _family_doc = json.loads(
                (_sib / "family_record.json").read_text())
        except Exception:
            _family_doc = None

        # GESTALT G1 (2026-10-17): the gap wing builds ON
        # BOARDING. The nightly product build covers the board
        # as it stood then; a name boarding today used to reach
        # its brief with the whole wing UNAVAILABLE until the
        # next nightly run. Ensure products for the names THIS
        # build is briefing (merge-preserving: entries already
        # in a product keep their true ages), then re-read the
        # docs + IV history so the fresh entries serve. Gated
        # on the live product area existing beside the setups
        # doc — hermetic builds without one behave exactly as
        # before. Fail-soft: any failure leaves the existing
        # products standing and the build proceeds.
        if not args.no_gap_ensure \
                and (_sib / "gap_products").is_dir():
            try:
                from core import gap_products as _gp2
                _spots = {}
                for _r in setups:
                    _lc = _r.get("last_close")
                    if isinstance(_lc, (int, float)):
                        _spots[_r["symbol"]] = _lc
                _ens = _gp2.build_missing(
                    _sib, list(dict.fromkeys(syms)),
                    _gdt.date.fromisoformat(as_of[:10]),
                    spots=_spots, cik_map=cik_map)
                _att = {k: v.get("attempted")
                        for k, v in _ens.items()
                        if isinstance(v, dict)}
                if any(_att.values()):
                    print(f"  gap ensure (built on boarding): "
                          f"{_att}")
                _gap_docs = {}
                for _fam in ("options", "edgar", "shorts",
                             "news", "attention"):
                    try:
                        _gap_docs[_fam] = json.loads(
                            (_sib / "gap_products"
                             / f"{_fam}.json").read_text())
                    except Exception:
                        _gap_docs[_fam] = {}
                _iv_hist = {}
                try:
                    for _ln in (_sib / "gap_products"
                                / "iv_history.jsonl").read_text() \
                            .splitlines():
                        _r2 = json.loads(_ln)
                        _iv_hist.setdefault(
                            _r2.get("symbol"), []).append(
                            {"session": _r2.get("session"),
                             "iv_pct": _r2.get("iv_pct")})
                except Exception:
                    _iv_hist = {}
            except Exception as _e:
                print(f"  gap ensure failed (existing products "
                      f"stand): {type(_e).__name__}: {_e}")

        def _gap_slice_for(fam, sym):
            doc = _gap_docs.get(fam) or {}
            entry = (doc.get("symbols") or {}).get(sym)
            if entry is None:
                return None
            # GESTALT G1: an entry built on boarding carries
            # its OWN built_at — the doc stamp is the LAST
            # build's, not this entry's.
            built = entry.get("built_at") or doc.get("built_at")
            if fam == "shorts":
                try:
                    _rd = _gdt.date.fromisoformat(
                        entry.get("regsho_date") or "")
                    _ao = _gdt.date.fromisoformat(as_of[:10])
                    stale = (_ao - _rd).days > 7
                except Exception:
                    stale = True
                return {"data": entry, "stale": stale,
                        "built_at": built}
            stale = True
            try:
                _ts = _gdt.datetime.fromisoformat(
                    str(built)).timestamp()
                stale = (_gtime.time() - _ts) > _gap_ttl[fam]
            except Exception:
                stale = True
            return {"data": entry, "stale": stale,
                    "built_at": built}

        def _mcap_for(sym):
            cik = cik_map.get(sym) or cik_map.get(sym.upper())
            if not cik:
                return None
            # GESTALT G3: the facts doc comes from
            # _companyfacts (producer-format cache + on-demand
            # refresh); the parse below is the item's original.
            f = _companyfacts(_sib, cik)
            if not f:
                return None
            try:
                units = ((f.get("facts") or {}).get("dei") or {}) \
                    .get("EntityCommonStockSharesOutstanding") or {}
                series = None
                for _u, rows in (units.get("units") or {}).items():
                    if rows:
                        series = rows
                        break
                if not series:
                    return None
                latest = max(series, key=lambda r: r.get("end") or "")
                return {"shares": float(latest["val"]),
                        "entity": f.get("entityName"),
                        "as_of": latest.get("end")}
            except Exception:
                return None

        _all_rows = list(doc.get("setups") or []) \
            + list(doc.get("entered") or [])

        def _consideration_inputs(s):
            sym = s["symbol"]
            holders = [{"sleeve": r.get("plan_sleeve")
                        or r.get("primary_sleeve"),
                        "status": r.get("status")}
                       for r in _all_rows
                       if r.get("symbol") == sym and r is not s
                       and (r.get("entered")
                            or r.get("status") == "entered")]
            # GESTALT G2: peers ride the resolved assignment
            # (desk bucket or GICS group); the desk-dict path
            # stays as the fallback for direct callers.
            _asg = _assignments.get(sym)
            peer_bars = {}
            if _asg:
                for psym in _asg["peers"]:
                    if daily_full.get(psym):
                        peer_bars[psym] = daily_full[psym]
            else:
                bucket = _m2.SECTORS.get(sym)
                if bucket:
                    for psym, pb in _m2.SECTORS.items():
                        if pb == bucket and psym != sym \
                                and daily_full.get(psym):
                            peer_bars[psym] = daily_full[psym]
            # THE COURTROOM (Stage 5): the calendar product
            # (dividends from EDGAR; lockups/index no-route in
            # the product itself), when it reached the build.
            _cal_doc = None
            try:
                _cal_doc = json.loads(
                    (_sib / "calendar_products"
                     / f"{sym}.json").read_text())
            except Exception:
                _cal_doc = None
            edoc = dict(earnings_by_sym.get(sym) or {})
            if earnings_by_sym.get("__stale__"):
                edoc = {"stale": True,
                        "updated": earnings_by_sym.get("__updated__")}
            elif sym in earnings_by_sym:
                edoc.setdefault("updated",
                                earnings_by_sym.get("__updated__"))
            from core import gap_products as _gp
            return {"bench": bench,
                    "lector_row": lector_rows.get(sym),
                    "calendar_product": _cal_doc,
                    "earnings": edoc,
                    "macro_events": macro_doc,
                    "book": {"holders": holders},
                    "tensor_row": tensor_rows.get(sym),
                    "tensor_diag": tensor_diags.get(sym),
                    "sector_assignment": _assignments.get(sym),
                    "full_bars": daily_full.get(sym),
                    "peer_bars": peer_bars,
                    "mcap": _mcap_for(sym),
                    "gap_options": _gap_slice_for("options", sym),
                    "gap_edgar": _gap_slice_for("edgar", sym),
                    "gap_shorts": _gap_slice_for("shorts", sym),
                    "gap_news": _gap_slice_for("news", sym),
                    "gap_attention": _gap_slice_for("attention",
                                                    sym),
                    "iv_history": _iv_hist.get(sym) or [],
                    "desk_history": _gp.desk_history_rollup(
                        _family_doc, sym)}
        tas = {s: chart_read.read_chart(s, daily.get(s))
               for s in syms}
        # SA-10 gate: a series that fails integrity is never
        # annotated — read_chart already refuses it (tas is None);
        # here the refusal gets its own published reason, distinct
        # from bars being unavailable, and the render below is
        # skipped even when a cached chart exists.
        gaps = {}
        for s in syms:
            v = chart_read.series_integrity_violations(
                daily.get(s), symbol=s)
            if v:
                gaps[s] = ("Chart withheld — price history under "
                           "review: " + v[0] + ". The rest of this "
                           "brief stands on the desk's records; no "
                           "chart was drawn from a price history "
                           "that does not check out.")
                print(f"  GATE {s}: chart withheld — {'; '.join(v)}")
        try:
            hourly = alpaca_1h_bars(syms, session=as_of)
        except Exception:
            hourly = {}
    else:
        daily, hourly, tas, gaps = {}, {}, {}, {}

    charts_dir = pathlib.Path(args.charts_dir) if args.charts_dir else None
    if charts_dir:
        charts_dir.mkdir(parents=True, exist_ok=True)

    skipped_renders = 0
    # GESTALT Phase 2 (§19): the Pass B visual-read sidecars.
    # The reader (the orchestrating agent, following the
    # local-chart-read protocol over the charts a build pass
    # renders) records one structured read per name; a later
    # pass consumes the read whose inputs hash matches THIS
    # build's inputs. Default location: a visual_reads/
    # directory beside the setups doc, when one exists.
    if args.visual_dir == "none":
        visual_dir = None
    elif args.visual_dir:
        visual_dir = pathlib.Path(args.visual_dir)
    else:
        _vd = pathlib.Path(args.setups).parent / "visual_reads"
        visual_dir = _vd if _vd.is_dir() else None
    visual_requests = []
    # The retained brief history is read BEFORE the loop —
    # the loop's own build replaces the document it reads.
    prior_docs = _prior_brief_docs(
        pathlib.Path(args.out) if args.out else None)
    for s in setups:
        sym = s["symbol"]
        digest = _inputs_hash(s, daily.get(sym), hourly.get(sym))
        _vr = _load_visual_read(visual_dir, sym, as_of, digest)
        brief = setup_brief.build_brief(
            s, market_context=mc, notes=notes,
            daily_bars=daily.get(sym), as_of=as_of,
            ta_read=tas.get(sym), market_measurements=mm,
            consideration_inputs=_consideration_inputs(s),
            visual_read=_vr, hourly_bars=hourly.get(sym))
        rel = None
        mobile_rel = None
        plan_rel = None
        card_rel = None
        panels = []
        # THE CARD (Amendment A-2 (§12)): the post text is
        # composed from the finished brief on every pass (pure
        # text, no pixels); the card PNG joins the cached
        # render set under its own digest.
        card_post = setup_card.compose_post(
            brief, market_context=mc,
            prior_call=setup_card.unchanged_call_fact(
                brief, prior_docs, as_of=as_of))
        render_skipped = False
        if charts_dir and sym not in gaps:
            name = f"{sym}-{as_of}.png"
            mname = f"{sym}-{as_of}-m.png"
            pname = f"{sym}-{as_of}-plan.png"
            cname = f"{sym}-{as_of}-card.png"
            sidecar = charts_dir / f"{sym}-{as_of}.inputs.json"
            card_digest = _card_digest(brief, digest)
            cached = None
            if sidecar.exists() and (charts_dir / name).exists() \
                    and (charts_dir / mname).exists() \
                    and (charts_dir / pname).exists():
                try:
                    cached = json.loads(sidecar.read_text())
                except Exception:
                    cached = None
            if cached and cached.get("hash") == digest \
                    and cached.get("plan"):
                rel = f"{args.chart_prefix}/{name}"
                mobile_rel = f"{args.chart_prefix}/{mname}"
                plan_rel = f"{args.chart_prefix}/{pname}"
                panels = cached.get("panels") or []
                skipped_renders += 1
                render_skipped = True
                if cached.get("card_digest") == card_digest \
                        and (charts_dir / cname).exists():
                    card_rel = f"{args.chart_prefix}/{cname}"
                else:
                    cpath, _cp, _cd = setup_card.render_card(
                        brief, daily.get(sym),
                        charts_dir / cname, as_of=as_of)
                    if cpath:
                        card_rel = f"{args.chart_prefix}/{cname}"
                        cached["card_digest"] = card_digest
                        sidecar.write_text(
                            json.dumps(cached) + "\n")
            else:
                path, panels, _lines = setup_brief.render_chart(
                    s, daily.get(sym), hourly.get(sym),
                    charts_dir / name, as_of=as_of,
                    ta_read=tas.get(sym),
                    plan_invalidation=(
                        brief.get("plan") or {}).get(
                            "invalidation"))
                if path:
                    rel = f"{args.chart_prefix}/{name}"
                    # The phone variant of the same read — rendered
                    # from the same chart read, so the two charts can
                    # never disagree.
                    mpath, _mp, _ml = setup_brief.render_chart(
                        s, daily.get(sym), None,
                        charts_dir / mname, as_of=as_of,
                        ta_read=tas.get(sym), variant="mobile",
                        plan_invalidation=(
                            brief.get("plan") or {}).get(
                                "invalidation"))
                    if mpath:
                        mobile_rel = f"{args.chart_prefix}/{mname}"
                    # The plan chart (PRODUCT REDESIGN §11):
                    # the plan and nothing else, rendered from
                    # the finished brief so it can only draw the
                    # numbers the brief itself states.
                    ppath, _pp, _pl = \
                        setup_brief.render_plan_chart(
                            brief, daily.get(sym),
                            charts_dir / pname, as_of=as_of)
                    if ppath:
                        plan_rel = f"{args.chart_prefix}/{pname}"
                    # THE CARD image (Amendment A-2 (§12)):
                    # rendered from the finished brief, like
                    # the plan chart, so it can only print the
                    # numbers the brief itself states.
                    cpath, _cp, _cd = setup_card.render_card(
                        brief, daily.get(sym),
                        charts_dir / cname, as_of=as_of)
                    if cpath:
                        card_rel = f"{args.chart_prefix}/{cname}"
                    sidecar.write_text(json.dumps(
                        {"hash": digest, "panels": panels,
                         "plan": bool(plan_rel),
                         "card_digest": card_digest,
                         "session": as_of, "symbol": sym}) + "\n")
        setup_brief.attach_chart(brief, rel, panels,
                                 mobile_rel=mobile_rel,
                                 gap=gaps.get(sym),
                                 plan_rel=plan_rel)
        setup_card.attach_card(brief, card_rel, card_post)
        # THE COURTROOM (Stage 4): the weekly render joins the
        # visual expert's fixed view set.
        weekly_rel = None
        if charts_dir and sym not in gaps:
            _wname = f"{sym}-{as_of}-w.png"
            # GESTALT-SUITE-BUDGET-20261024: the weekly frame
            # joins the chart re-render guard. The weekly chart
            # is a pure function of the same guarded inputs
            # (setup + daily bars — exactly what the sidecar
            # hash binds), so when the guard hits and the
            # weekly PNG is on disk, it is re-attached, never
            # re-rendered: a two-pass build used to pay the
            # weekly render on BOTH passes.
            if render_skipped and (charts_dir / _wname).exists():
                weekly_rel = f"{args.chart_prefix}/{_wname}"
            else:
                try:
                    _wpath, _wp, _wl = \
                        setup_brief.render_weekly_chart(
                            s, daily.get(sym), charts_dir / _wname,
                            as_of=as_of)
                except Exception:
                    _wpath = None
                if _wpath:
                    weekly_rel = f"{args.chart_prefix}/{_wname}"
        brief["chart_weekly"] = weekly_rel
        # THE COURTROOM (Stage 3): the refusal spine + the
        # surface seal. A brief whose docket failed verification
        # or whose chart was withheld does not publish; a post
        # that disagrees with the sealed brief does not publish
        # either. The name publishes the held state instead —
        # "held — [plain reason]" on the board, no call, no
        # card, no post. Publication only; never a trade veto.
        if refusal.apply(brief) is None:
            _seal_problems = surface_seal.seal_surfaces(brief)
            brief.setdefault("seals", {})["surface"] = \
                _seal_problems
            if _seal_problems:
                refusal.hold_for_surface(brief, _seal_problems)
        briefs[sym] = brief
        # §19: the visual-read request for this name — the
        # exact charts the reader must view, the Pass A public
        # summary (the brief's own chart_read section), the
        # setup's direction, and where the sidecar goes. A name
        # whose charts were withheld (integrity gate) gets no
        # request: there is nothing honest to read.
        if sym not in gaps:
            # ROUND-11 ADJUST S1 (§27 A-17): the request
            # carries the staged CALL explicitly — the
            # frame the reader judges and the filing tool
            # pins. When this build consumed a read, the
            # frame of record is the one the consumed
            # filing was judged against (it rides the
            # sidecar); otherwise it is the call THIS build
            # just composed, testimony-free by construction
            # on a first pass — the pass-1 call the next
            # filing will judge.
            _call = brief.get("the_call") or {}
            _frame = (_vr or {}).get("verdict_vs_call") \
                if _vr else None
            if _frame:
                _staged_call = {
                    "direction": _frame.get("call_direction"),
                    "plan_direction":
                        _frame.get("plan_direction"),
                    "invalidation":
                        _frame.get("call_invalidation"),
                    "contrary": bool(
                        _frame.get("contrary")),
                    "state": "call"}
            else:
                _c_dir = _call.get("direction")
                if _c_dir not in ("long", "short"):
                    _c_dir = _call.get("sleeve_direction") \
                        or "long"
                _c_inv = ((_call.get(
                    "contrary_invalidation") or {}).get(
                        "price") if _call.get("contrary")
                    else ((brief.get("plan") or {}).get(
                        "invalidation") or {}).get("price"))
                _staged_call = {
                    "direction": _c_dir,
                    "plan_direction":
                        _call.get("sleeve_direction")
                        or _c_dir,
                    "invalidation": _c_inv,
                    "contrary": bool(_call.get("contrary")),
                    "state": ("no_call" if _call.get(
                        "no_call") and not _call.get(
                            "conditional")
                        else "conditional" if _call.get(
                            "conditional") else "call")}
            visual_requests.append({
                "symbol": sym, "session": as_of,
                "inputs_hash": digest,
                "status": "read" if _vr else "absent",
                "staged_call": _staged_call,
                "sidecar": (str(visual_dir
                                / f"{sym}-{as_of}.json")
                            if visual_dir else None),
                "charts": {"chart": rel, "plan": plan_rel,
                           "card": card_rel,
                           "mobile": mobile_rel,
                           "weekly": weekly_rel},
                "view_set": VIEW_SET,
                "setup": {"status": s.get("status"),
                          "side": s.get("side"),
                          "entry": s.get("entry"),
                          "stop": s.get("stop"),
                          "target": s.get("target"),
                          "last_close":
                              brief["levels"].get("last_close")},
                "pass_a": brief.get("chart_read"),
            })
        # ROUND-20 ADJUST AD1 (§38 A-28): the log line
        # reports the brief's FINAL card state, read after
        # the refusal spine and the surface seal have run —
        # the pre-cure line printed the local card_rel
        # (the pre-seal render), so AZO's pass-2 log showed
        # a card path on a brief the seal had just held
        # and stripped: the log claimed a surface the
        # shipped brief did not carry.
        print(f"  brief {sym:<6} score={brief['score']} "
              f"card={brief.get('card') or 'NONE'} "
              f"chart={rel or 'NONE'} panels={panels} "
              f"pattern={(tas.get(sym) or {}).get('pattern', {}).get('name')} "
              f"desk_read={(brief.get('desk_read') or {}).get('call')}")

    # §13: the 6-month-momentum book rank is an assembly-time
    # fact (a percentile needs the whole book) — applied to every
    # brief's consideration ledger before anything is written.
    if briefs:
        from core import consideration as _consideration
        _consideration.apply_momentum_book_ranks(
            list(briefs.values()))

    # Completed names: carry the live read forward, never rebuild.
    # LANDING (2026-10-16): the landed curator emits this list under
    # the key "completed" (core/setups_curator.py; live setups doc
    # verified on disk) — "setups_completed" is the FEED key the
    # merge writes, not the setups-doc key. Reading only the feed
    # key here would leave the carry permanently inert on the live
    # pipeline; the fallback keeps the build-era shape readable.
    briefs_completed = {}
    completed = doc.get("completed") or doc.get("setups_completed") or []
    if completed and args.out and pathlib.Path(args.out).exists():
        try:
            prev = json.loads(pathlib.Path(args.out).read_text())
        except Exception:
            prev = {}
        prev_briefs = dict(prev.get("briefs") or {})
        prev_briefs.update(prev.get("briefs_completed") or {})
        for entry in completed:
            csym = entry.get("symbol") if isinstance(entry, dict) \
                else None
            if csym and csym in prev_briefs and csym not in briefs:
                briefs_completed[csym] = prev_briefs[csym]
        if briefs_completed:
            print(f"  carried {len(briefs_completed)} completed "
                  f"brief(s) forward (not regenerated)")

    out_doc = {"as_of": as_of, "briefs": briefs}
    if freshness_rows:
        out_doc["freshness_findings"] = freshness_rows
    if briefs_completed:
        out_doc["briefs_completed"] = briefs_completed
    text = json.dumps(out_doc, indent=1)

    # §19: the visual-read request manifest — written beside
    # the charts it names, every build, so the orchestrating
    # reader always works from the CURRENT inputs hashes.
    # Names marked "absent" are the reads still owed.
    if charts_dir and visual_requests:
        (charts_dir / "visual_requests.json").write_text(
            json.dumps({
                "session": as_of,
                "protocol": ("local-chart-read Pass B: view the "
                             "named charts at full resolution, "
                             "whole then parts; transcribe "
                             "before interpreting; record the "
                             "structured read at the sidecar "
                             "path, bound to inputs_hash"),
                "filing": ("file reads with tools/"
                           "file_visual_read.py --requests "
                           "<this file> --symbol SYM "
                           "--content <content.json>: the "
                           "helper copies symbol, session and "
                           "inputs_hash from the request of "
                           "record (a hash is never typed) "
                           "and validates the filing before "
                           "writing — N4, §23 A-13"),
                "sidecar_schema": {
                    "_contract": ("ONE schema, stated once in "
                                  "core/visual_filing.py "
                                  "(READ_CONTENT_REQUIRED, "
                                  "§25 A-15): every field "
                                  "below is required at "
                                  "filing, top-level — a "
                                  "filing missing one is "
                                  "refused by the helper "
                                  "with the field named"),
                    "symbol": "SYM", "session": as_of,
                    "inputs_hash": "from the request",
                    "status": "read | abstain",
                    "frames_viewed": ["what was actually "
                                      "viewed"],
                    "reference_class": "the setup family, or "
                                       "not established here",
                    "structure_verdict": "regime / stage / "
                                         "rhythm in plain "
                                         "words",
                    "pattern_quality": "clean | forced | none "
                                       "+ the judgment",
                    "the_tell": "the volume verdict",
                    "still_going_up": "the first question, "
                                      "kept separate — filed "
                                      "as a TOP-LEVEL field",
                    "safe_to_buy_here": "the second "
                                        "question, kept "
                                        "separate — filed "
                                        "as a TOP-LEVEL "
                                        "field (the helper "
                                        "writes the nested "
                                        "two_questions "
                                        "mirror itself)",
                    "verdict": "supports | opposes | no view"
                               " — judged against the "
                               "STAGED CALL (the call the "
                               "build staged, named on this "
                               "request's staged_call block), "
                               "never the desk read's lean "
                               "and never the sleeve plan "
                               "object (§27 A-17)",
                    "call_direction": "long | short — the "
                                      "staged call the "
                                      "reader judged, stated "
                                      "in the filing and "
                                      "checked against the "
                                      "request's staged_call "
                                      "block; a disagreement "
                                      "is refused at filing "
                                      "(§27 A-17)",
                    "verdict_reference": "staged_call "
                                         "(written by the "
                                         "filing helper, with "
                                         "the verdict_vs_call "
                                         "frame copied from "
                                         "the request)",
                    "confidence": "LOW | MED",
                    "scenario_lean": "which branch the eye "
                                     "leans to, and the "
                                     "terminus it draws",
                    "lean_target": "staged_plan | contrary "
                                   "| neither — the branch "
                                   "of scenario_lean, in the "
                                   "verdict's own reference; "
                                   "filing refuses a verdict "
                                   "inconsistent with it",
                    "expectancy": "what the eye expects, in "
                                  "plain words — required "
                                  "since §25 A-15 (the "
                                  "docket's gate always "
                                  "required it; filing now "
                                  "asks for it too)",
                    "premortem": "how this read is wrong in "
                                 "two weeks",
                    "self_critique": "the strongest case "
                                     "against the read's "
                                     "own lean",
                    "disagreements": [{
                        "fact": "the material fact",
                        "pass_a": "what the geometry records",
                        "visual": "what the eye records"}],
                    "abstain_reason": "when status is abstain"},
                "requests": visual_requests}, indent=1) + "\n")

    ledger_path = None
    if args.read_ledger != "none" and args.out:
        ledger_path = pathlib.Path(args.read_ledger) if \
            args.read_ledger else \
            pathlib.Path(args.out).parent / "read_ledger.jsonl"
    n_rows = _append_read_ledger(ledger_path, briefs, as_of)
    if ledger_path:
        print(f"  read ledger: +{n_rows} row(s) -> {ledger_path}")

    if args.out:
        pathlib.Path(args.out).write_text(text + "\n")
        print(f"wrote {args.out}: {len(briefs)} briefs, "
              f"session={as_of}, chart renders skipped "
              f"(unchanged inputs): {skipped_renders}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
