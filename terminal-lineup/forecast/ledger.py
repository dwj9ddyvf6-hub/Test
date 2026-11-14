"""The Forecast Ledger: one append-only JSONL ledger for the Forecast
Engines 30 program (design: FORECAST-ENGINES-30.md, 'Shared machinery').

Discipline (N1, ledger before display):
- Rows are only ever appended. Nothing is rewritten; a correction is a
  new row of type "correction" that references the row it corrects.
- Every row carries a hash chain: row_hash = sha256(prev_hash + canonical
  JSON of the row without its hash fields). Any rewrite, deletion or
  reordering of a prior row breaks the chain and is detected by
  verify_chain() and refused by append operations.
- A forecast row carries: engine id, issued timestamp, horizon open and
  close (session dates), the exact forecast quantity and value, the data
  lineage (source artifacts with sha256, plus a five-clock envelope in
  the adopted evidence-contract form: event_time, publication_time,
  first_available_time, ingestion_time, decision_as_of, matching
  morgue/evidence.py CLOCK_FIELDS), and its evidence-family labels.
- Identical republications count once: dedupe key is
  engine + subject + horizon_open + horizon_close + sha256(forecast value).
  A duplicate append returns the existing row id and writes nothing.
- Grade rows append to the same ledger and reference the forecast row
  they grade (forecast_row_id).
- Label definitions are frozen (DEEP-PASS 3.2 item 3): a forecast row
  may carry a six field label context with its fingerprint plus a
  label transform id and hash; a grade for such a row must repeat
  that identity exactly or it is refused, and recompute_figures
  never pools scores across fingerprints.
- Every published figure must be recomputable from the ledger alone:
  see recompute_figures(), which reads only ledger rows.
"""
import hashlib
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:  # non-POSIX fallback: no inter-process lock
    fcntl = None

ROW_TYPES = ("genesis", "forecast", "grade", "correction")
CLOCK_FIELDS = ("event_time", "publication_time", "first_available_time",
                "ingestion_time", "decision_as_of")
ABSENCE_STATES = ("present", "no_data", "no_print", "not_yet_available",
                  "defect_abstention")

# ---- abstention reason codes (DEEP-PASS 3.1 item 6) -------------------
# The fixed vocabulary is taken whole from Ausar's forecast package
# (research/forecast_engines/engine.py, ForecastEngine.forecast, read
# in code 2026-10-29): per feature causes are stored as
# "<cause>:<feature>", global reasons stand alone, and the stored
# list is deduplicated and sorted, exactly as his _abstain emits
# abstain_reasons=tuple(sorted(set(reasons))). A reason outside this
# vocabulary is refused at append, so the record stays countable.
PER_FEATURE_REASON_CAUSES = (
    "missing", "invalid_observation", "non_finite", "unit_mismatch",
    "value_out_of_range", "future_or_late_data",
    "timestamp_order_invalid", "stale", "missing_provenance",
    "data_rights_not_approved", "unknown_evidence_kind",
    "missing_transform_provenance", "invalid_quality",
    "quality_below_floor")
GLOBAL_ABSTAIN_REASONS = (
    "invalid_as_of", "invalid_symbol", "invalid_feature_collection",
    "invalid_target_window_id", "incomplete_target_window_binding",
    "target_contract_not_labelable", "target_window_id_not_allowed",
    "invalid_target_window_end", "target_window_start_before_as_of",
    "target_window_end_not_after_start", "invalid_label_transform_id",
    "invalid_label_transform_hash",
    "incomplete_label_transform_binding",
    "label_transform_for_nonlabelable_target", "invalid_label_context",
    "missing_label_context", "label_context_for_nonlabelable_target",
    "as_of_in_future", "score_computation_failed")


def feature_reason(cause, feature):
    """Build one per feature reason code, validated against the
    fixed vocabulary."""
    if cause not in PER_FEATURE_REASON_CAUSES:
        raise LedgerError(f"unknown abstention cause {cause!r}")
    if not isinstance(feature, str) or not feature.strip() \
            or ":" in feature:
        raise LedgerError(f"invalid feature name {feature!r}")
    return f"{cause}:{feature}"


def normalize_abstain_reasons(reasons):
    """Validate, deduplicate and sort abstention reason codes.
    Every code is either a global reason from the fixed vocabulary
    or "<cause>:<feature>" with a cause from the vocabulary and a
    non-empty feature name. Anything else raises LedgerError."""
    if reasons is None:
        return []
    out = set()
    for reason in reasons:
        if not isinstance(reason, str) or not reason:
            raise LedgerError(f"invalid abstention reason {reason!r}")
        if reason in GLOBAL_ABSTAIN_REASONS:
            out.add(reason)
            continue
        cause, sep, feature = reason.partition(":")
        if not sep or cause not in PER_FEATURE_REASON_CAUSES \
                or not feature.strip():
            raise LedgerError(
                f"abstention reason {reason!r} is outside the fixed "
                f"vocabulary (a global reason, or "
                f"<cause>:<feature> with a known cause)")
        out.add(reason)
    return sorted(out)


# ---- scored zero convention (DEEP-PASS 3.1 item 7) --------------------
# From FE26 in Ausar's scorers.py, confirmed in code: a passed event
# returns a scored zero (drivers event_passed=1.0, time_weight=0.0),
# not an abstention and not silence. Here a scored zero is a taken
# (absence_state present) forecast row carrying a "scored_zero"
# marker whose drivers must record event_passed=1.0, so coverage
# audits can distinguish event over from engine broken.

def is_scored_zero(row):
    return isinstance(row.get("scored_zero"), dict)


def _validate_scored_zero(scored_zero):
    if not isinstance(scored_zero, dict):
        raise LedgerError("scored_zero must be a mapping with drivers")
    drivers = scored_zero.get("drivers")
    if not isinstance(drivers, dict) \
            or drivers.get("event_passed") != 1.0:
        raise LedgerError(
            "a scored zero must carry the event_passed=1.0 driver "
            "(the FE26 convention); without it the row is not "
            "distinguishable from an ordinary zero forecast")
    return {"drivers": dict(drivers),
            **{k: v for k, v in scored_zero.items() if k != "drivers"}}


# ---- label definition freezing (DEEP-PASS 3.2 item 3) ---------------
# Adapted from Ausar's label_context.py, target_provenance.py and
# target_contract.py (rows M06 to M08), imported as his ledger's two
# structural rules without his store:
#   1. an outcome append (here, a grade row) must repeat the label
#      identity frozen on the forecast row it grades, exactly, or it
#      is refused;
#   2. outcomes are never pooled across label fingerprints:
#      recompute_figures groups scores by fingerprint and publishes a
#      pooled mean only when an engine has exactly one group.
# The label context is six fields, all required: series, measurement
# basis, calendar, reference series, data vintage policy, corporate
# action policy. The label transform is named by an id and bound by
# the sha256 hash of its canonical spec. A forecast may carry the
# full identity or none of it (rows written before this freezing
# landed stay valid as one unfrozen legacy group); a partial
# identity is refused at append, because half a definition is how
# equal target names with different conventions get graded together.

LABEL_CONTEXT_FIELDS = ("series", "measurement_basis", "calendar",
                        "reference_series", "data_vintage_policy",
                        "corporate_action_policy")
UNFROZEN_GROUP = "unfrozen_legacy"
_HEX = set("0123456789abcdef")


def _is_hash64(value):
    return isinstance(value, str) and len(value) == 64 \
        and all(c in _HEX for c in value)


def normalize_label_context(context):
    """Validate and normalise a six field label context. Every one
    of LABEL_CONTEXT_FIELDS must be present as a non-empty string,
    and no other field is allowed. Returns the normalised dict."""
    if not isinstance(context, dict):
        raise LedgerError("label context must be a mapping of the six "
                          "label context fields")
    extra = sorted(set(context) - set(LABEL_CONTEXT_FIELDS))
    if extra:
        raise LedgerError(
            f"label context carries fields outside the six field "
            f"definition: {extra}")
    out = {}
    for field in LABEL_CONTEXT_FIELDS:
        val = context.get(field)
        if not isinstance(val, str) or not val.strip():
            raise LedgerError(
                f"label context field {field!r} is missing or empty; "
                f"all six fields are required for the fingerprint")
        out[field] = " ".join(val.split())
    return out


def label_context_fingerprint(context):
    """sha256 over the canonical normalised six field context."""
    return hashlib.sha256(
        _canonical(normalize_label_context(context)).encode()).hexdigest()


def label_transform_hash_for(transform_id, transform_spec):
    """The hash that binds a label transform: sha256 over the
    canonical {id, spec} pair, so the same id with a changed spec
    hashes differently."""
    if not isinstance(transform_id, str) or not transform_id.strip():
        raise LedgerError("label transform id must be a non-empty string")
    return hashlib.sha256(_canonical(
        {"id": transform_id, "spec": transform_spec}).encode()).hexdigest()


def default_label_identity(*, subject, quantity, outcome):
    """The shared label identity every issuing refresher declares at
    issue time (RC-21 cure, 2026-10-30). One mechanism, in this shared
    ledger path, not per refresher copies: when a refresher issues
    through append_forecast_declared, the label definition is
    derived deterministically from the forecast's own subject,
    quantity and outcome spec, so the frozen context and the
    transform binding describe exactly the label being issued. The
    transform spec is the outcome spec itself, hashed, so any change
    to how the label resolves changes the fingerprint and the old
    and new definitions are never pooled. Rows already on the ledger
    without an identity stay in the unfrozen_legacy group; nothing
    here rewrites history."""
    outcome = outcome or {}
    kind = outcome.get("kind") or "unspecified"
    # The context names the label definition, never the forecast's
    # subject: the same definition applied to another name is the
    # same label, so subjects and per issue dates stay out of both
    # the context and the transform spec (they already live in the
    # row's subject and horizon fields). Including them would
    # fragment every fingerprint group to a single row.
    context = {
        "series": "subject daily bars (panel record)",
        "measurement_basis": (
            f"quantity {quantity!r} resolved as outcome kind "
            f"{kind!r} over the horizon sessions"),
        "calendar": "NYSE sessions",
        "reference_series": "the forecast subject's own daily bar series",
        "data_vintage_policy": (
            "point in time as first available (five clock lineage "
            "envelope)"),
        "corporate_action_policy": (
            "split adjusted daily bars, dividends excluded"),
    }
    transform_id = f"outcome_{kind}_v1"
    spec_outcome = {k: v for k, v in outcome.items()
                    if k not in ("symbol", "subject", "at_date", "date")}
    transform_spec = {"quantity": quantity, "outcome": spec_outcome}
    return {"label_context": context,
            "label_transform_id": transform_id,
            "label_transform_hash": label_transform_hash_for(
                transform_id, transform_spec)}


def _validate_label_identity(label_context, label_transform_id,
                             label_transform_hash):
    """All-or-none validation of a forecast's frozen label identity.
    Returns the stored identity dict, or None when nothing was
    supplied (an unfrozen legacy row)."""
    supplied = [label_context is not None, label_transform_id is not None,
                label_transform_hash is not None]
    if not any(supplied):
        return None
    if not all(supplied):
        raise LedgerError(
            "incomplete label identity: label_context, "
            "label_transform_id and label_transform_hash must be "
            "supplied together or not at all (a partial binding "
            "cannot be frozen)")
    context = normalize_label_context(label_context)
    if not isinstance(label_transform_id, str) \
            or not label_transform_id.strip():
        raise LedgerError("label transform id must be a non-empty string")
    if not _is_hash64(label_transform_hash):
        raise LedgerError(
            "label transform hash must be a 64 character lowercase "
            "hex sha256 (see label_transform_hash_for)")
    return {"label_context": context,
            "label_context_fingerprint": label_context_fingerprint(context),
            "label_transform_id": label_transform_id,
            "label_transform_hash": label_transform_hash}


def frozen_label_identity(row):
    """The identity an outcome append must repeat for `row`: the
    three binding fields, or None when the row carries no frozen
    identity. A row carrying only part of an identity is malformed
    and raises LedgerError rather than grading quietly."""
    fields = ("label_context_fingerprint", "label_transform_id",
              "label_transform_hash")
    present = [f for f in fields if row.get(f) is not None]
    if not present:
        return None
    if len(present) != len(fields):
        raise LedgerError(
            f"row {row.get('row_id')} carries a partial label identity "
            f"({present}); refusing to treat it as frozen or unfrozen")
    return {f: row[f] for f in fields}


class LedgerError(Exception):
    pass


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def value_hash(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dedupe_key(engine_id, subject, horizon_open, horizon_close, vhash):
    return "|".join([engine_id, subject, horizon_open, horizon_close, vhash])


class Ledger:
    def __init__(self, path, registry=None):
        self.path = path
        self.registry = registry  # optional registry.Registry for family checks
        # Append-path cache (cure 2026-10-29): _append used to
        # re-read and re-verify the whole ledger on every append,
        # which made bulk grading O(n^2) (about 9s per grade at
        # 9k rows). The cache is keyed on the file's (mtime_ns,
        # size): any external rewrite or another process's append
        # changes the stat and forces a full reload and re-verify,
        # so the rewrite protection is unchanged.
        self._cache_stat = None
        self._cache_rows = None
        self._verified_stat = None
        # Dedupe offset index (LEDGER-DEDUPE-INDEX-20261113):
        # {dedupe_key: byte offset of the first forecast row
        # carrying it}, built by one raw scan and refreshed by
        # scanning only the bytes appended since the last scan
        # (the ledger is append-only, so earlier offsets never
        # move). See _dedupe_offsets.
        self._dedupe_index = None
        self._dedupe_index_stat = None
        self._dedupe_index_size = 0
        self._lock_depth = 0

    @contextmanager
    def _append_lock(self):
        """Serialize the short write critical section against
        other estate processes (cure LEDGER-APPEND-RACE-20261113).
        The lock is held only for a delta verification plus one
        row's write, never for a full pass, so a long reader
        never blocks the evening's appenders; it is reentrant
        per Ledger instance so the streaming append path can
        hold it across its extend-and-write step while the write
        helper takes it again. On a platform without fcntl the
        lock degrades to the instance guard only."""
        if self._lock_depth > 0:
            self._lock_depth += 1
            try:
                yield
            finally:
                self._lock_depth -= 1
            return
        if fcntl is None:
            self._lock_depth = 1
            try:
                yield
            finally:
                self._lock_depth = 0
            return
        lock_path = self.path + ".lock"
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o666)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            self._lock_depth = 1
            try:
                yield
            finally:
                self._lock_depth = 0
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def _stat(self):
        try:
            st = os.stat(self.path)
        except OSError:
            return None
        return (st.st_mtime_ns, st.st_size)

    # ---- reading -----------------------------------------------------
    def rows(self):
        stat = self._stat()
        if stat is None:
            return []
        if self._cache_rows is not None and self._cache_stat == stat:
            return list(self._cache_rows)
        out = []
        with open(self.path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise LedgerError(
                        f"ledger line {i} is not valid JSON (possible "
                        f"rewrite/corruption): {exc}")
        self._cache_stat = stat
        self._cache_rows = out
        return list(out)

    def iter_rows(self):
        """Stream the ledger's rows one at a time
        (GRADING-STREAM-20261106): the same parse and the same
        LedgerError on an invalid line as rows(), but nothing is
        retained and the parsed-rows cache is neither read nor
        populated, so a caller walking a ledger of any size holds
        one parsed row of resident memory. Rows appended to the
        file while a stream is open may or may not be seen by
        that stream; callers that append as they go (the grading
        driver) only ever append row types their own scan
        filters out."""
        if self._stat() is None:
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerError(
                        f"ledger line {i} is not valid JSON (possible "
                        f"rewrite/corruption): {exc}")

    def verify_chain(self, rows=None):
        """Return True iff every row's hash chain link is intact."""
        rows = self.rows() if rows is None else rows
        prev = ""
        for row in rows:
            body = {k: v for k, v in row.items()
                    if k not in ("row_hash", "prev_hash", "row_id")}
            expect = hashlib.sha256(
                (prev + _canonical(body)).encode()).hexdigest()
            if row.get("prev_hash") != prev or row.get("row_hash") != expect:
                return False
            prev = row["row_hash"]
        return True

    def verify_chain_streaming(self):
        """verify_chain() with bounded memory
        (PROOFGATE-STREAM-20261104): the file is read one line
        at a time and only the previous row's hash is held, so
        verifying a ledger of any size costs one parsed row of
        resident memory instead of the whole parsed ledger.
        Same verdicts as verify_chain() on the same file: a
        missing file verifies as an empty ledger, an invalid
        JSON line raises LedgerError, and any broken link
        returns False. Callers that verify before appending in
        a memory-tight process use this form; the append path's
        own re-verification is unchanged."""
        if self._stat() is None:
            return True
        prev = ""
        with open(self.path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerError(
                        f"ledger line {i} is not valid JSON "
                        f"(possible rewrite/corruption): {exc}")
                body = {k: v for k, v in row.items()
                        if k not in ("row_hash", "prev_hash",
                                     "row_id")}
                expect = hashlib.sha256(
                    (prev + _canonical(body)).encode()).hexdigest()
                if row.get("prev_hash") != prev \
                        or row.get("row_hash") != expect:
                    return False
                prev = row["row_hash"]
        return True

    # Outcome kinds whose grading needs ledger context beyond the
    # row itself (grade_forecast's context scans). The streaming
    # grading state pre-collects exactly these rows: 28 exist in
    # the 253,163-row ledger of 2026-11-06.
    GRADING_CONTEXT_KINDS = ("first_failure_side", "league_interval",
                             "league_ranking")

    def grading_stream_state(self):
        """One streaming pass over the ledger collecting the
        grading append state (GRADING-STREAM-20261106): the hash
        chain is verified exactly as _stream_pass verifies it (an
        unparseable line or a broken link raises LedgerError,
        because the append path refuses rather than reports), and
        the working set collected is only the tail hash, the ids
        of already-graded forecasts, the void map, the grade
        count, and the few context rows grade_forecast scans for.
        Nothing else is retained and the parsed-rows cache is
        neither read nor populated: the resident set is the id
        sets, not the parsed ledger. A pass whose file moves
        under it is retried; a file that will not sit still is
        refused. The returned dict carries the stream-state keys
        _append_streaming consumes (stat, tail_hash, seen), so
        grade appends route through it unchanged."""
        for _attempt in range(3):
            stat0 = self._stat()
            graded_ids = set()
            voided_by = {}
            context_rows = []
            grade_count = 0
            prev = ""
            if stat0 is not None:
                with open(self.path, "r", encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise LedgerError(
                                f"ledger line {i} is not valid JSON "
                                f"(possible rewrite/corruption): {exc}")
                        body = {k: v for k, v in row.items()
                                if k not in ("row_hash", "prev_hash",
                                             "row_id")}
                        expect = hashlib.sha256(
                            (prev + _canonical(body)).encode()
                        ).hexdigest()
                        if row.get("prev_hash") != prev \
                                or row.get("row_hash") != expect:
                            raise LedgerError(
                                "ledger hash chain is broken; "
                                "refusing to append to a ledger whose "
                                "history does not verify (rewrite "
                                "detected)")
                        prev = row["row_hash"]
                        rtype = row.get("type")
                        if rtype == "grade":
                            grade_count += 1
                            if row.get("forecast_row_id"):
                                graded_ids.add(row["forecast_row_id"])
                        elif rtype == "correction":
                            if row.get("corrects_row_id"):
                                voided_by[row["corrects_row_id"]] = \
                                    row["row_id"]
                        elif rtype == "forecast":
                            if (row.get("outcome") or {}).get("kind") \
                                    in self.GRADING_CONTEXT_KINDS:
                                context_rows.append(row)
            if self._stat() == stat0:
                return {"engine_id": None, "issued_ts": None,
                        "stat": stat0, "tail_hash": prev, "seen": set(),
                        "graded_ids": graded_ids,
                        "voided_by": voided_by,
                        "grade_count": grade_count,
                        "context_rows": context_rows}
        raise LedgerError(
            "ledger changed repeatedly during the streaming "
            "grading pass; refusing to append")

    def _tail_hash(self):
        """The last row's hash, read from the file's tail at
        bounded memory (LEDGER-APPEND-TAIL-20261109): lines are
        walked backwards in blocks until the last non-empty
        line is whole, and only that line is parsed. _append
        needs the tail and nothing else; the pre-cure code
        parsed the entire ledger for it, so every classic
        append on the grown 660 MB ledger cost a full parse
        (measured: four appends in one refresher, each after
        a cache invalidation, at about 2.3 GB peak apiece)."""
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return ""
        if size == 0:
            return ""
        block = 1 << 16
        data = b""
        pos = size
        with open(self.path, "rb") as fh:
            while pos > 0:
                step = min(block, pos)
                pos -= step
                fh.seek(pos)
                data = fh.read(step) + data
                lines = [ln for ln in data.split(b"\n") if ln.strip()]
                if len(lines) >= 2 or pos == 0:
                    if not lines:
                        return ""
                    try:
                        return json.loads(
                            lines[-1].decode("utf-8"))["row_hash"]
                    except (ValueError, KeyError, UnicodeDecodeError) as exc:
                        raise LedgerError(
                            "the ledger's last line is not a valid "
                            f"row (possible rewrite/corruption): {exc}")
        return ""

    def _append(self, row):
        stat = self._stat()
        if self._verified_stat != stat:
            # Verification streams (LEDGER-APPEND-TAIL-20261109):
            # the same chain verdict as verify_chain(rows), at
            # one parsed row of resident memory; the pre-cure
            # code parsed the whole ledger to reach it.
            if stat is not None and not self.verify_chain_streaming():
                raise LedgerError(
                    "ledger hash chain is broken; refusing to append to a "
                    "ledger whose history does not verify (rewrite detected)")
            self._verified_stat = self._stat()
            stat = self._verified_stat
        # If another writer appended between our read and this
        # write, our prev link would be stale: re-check the stat
        # and start over with the fresh tail when it moved. The
        # re-check, the tail read and the write now sit inside
        # the append lock (cure LEDGER-APPEND-RACE-20261113), so
        # the window between the tail read and the write, where
        # two lanes could both link onto the same tail, is
        # closed; a stat that moved before the lock was taken
        # still restarts the append exactly as before.
        with self._append_lock():
            if self._stat() == stat:
                return self._append_locked(row, stat)
        return self._append(row)

    def _append_locked(self, row, stat):
        prev = self._tail_hash()
        row = dict(row)
        row["prev_hash"] = prev
        body = {k: v for k, v in row.items()
                if k not in ("row_hash", "prev_hash", "row_id")}
        row["row_hash"] = hashlib.sha256(
            (prev + _canonical(body)).encode()).hexdigest()
        row["row_id"] = row["row_hash"][:16]
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(_canonical(row) + "\n")
        self._write_provenance(row)
        new_stat = self._stat()
        # The parsed-rows cache cannot be extended without the
        # parse this cure exists to avoid; drop it, exactly as
        # _append_streaming does, so no later rows() call in
        # this process reads a stale copy. Callers that held
        # the cache as their working set re-read on demand.
        self._cache_rows = None
        self._cache_stat = None
        self._verified_stat = new_stat
        return row

    def _write_provenance(self, row):
        # Append provenance (cure D-R1-01, 2026-10-31): every
        # append, from any path (the refresh runner, grading, or a
        # standalone refresher run by hand), writes one line to the
        # sidecar ledger_provenance.log beside the ledger, so the
        # ledger's growth always carries run-level provenance.
        # Before this cure the ledger advanced ~19,700 rows with
        # no proof-log entry because only refresh_engines.py runs
        # wrote refresh_proof.log. The sidecar is an audit record
        # only: it is not part of the hash chain, and a sidecar
        # write failure never blocks or alters an append.
        try:
            prov_path = os.path.join(
                os.path.dirname(os.path.abspath(self.path)),
                "ledger_provenance.log")
            prov = {"ts_utc": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"),
                    "type": row.get("type"),
                    "engine_id": row.get("engine_id"),
                    "row_id": row["row_id"],
                    "pid": os.getpid()}
            with open(prov_path, "a", encoding="utf-8") as fh:
                fh.write(_canonical(prov) + "\n")
        except Exception:
            pass

    # ---- streaming append (PROOFGATE-APPEND-STREAM-20261105) ------
    def _stream_pass(self, engine_id, issued_ts):
        """One streaming pass over the ledger file, the append
        state's only read: the hash chain is verified exactly as
        verify_chain_streaming verifies it (an unparseable line
        raises LedgerError; a broken link raises LedgerError,
        because the append path refuses rather than reports),
        and the working set collected is only the tail row's hash
        and the dedupe keys of the forecast rows of the one
        (engine_id, issued_ts) batch. Nothing else is retained:
        the resident set is the batch's key set, not the ledger.

        Snapshot form (cure LEDGER-APPEND-RACE-20261113): the
        pass reads exactly the bytes the file held when the pass
        opened (stat0's size) and verifies that prefix. The
        ledger is append-only, so a prefix is itself a complete
        valid chain, and rows another lane appends during the
        pass are not a defect: they are picked up afterwards by
        _extend_stream_state under the append lock, which
        verifies the delta before anything links onto it. The
        pre-cure pass demanded the file sit still for the whole
        read and retried only three times, so on an evening when
        another lane appended during the proof gate's pass over
        the grown ledger, all three attempts moved and the lane
        died on "ledger changed repeatedly during the streaming
        append pass" (the 2026-11-12 tools run). Verification is
        not weakened: every row the state is built from, in the
        snapshot and in every delta, is hash-verified before the
        state's tail is trusted. A file that shrinks under the
        pass (a rewrite, never an append) or whose snapshot
        boundary falls mid-line on every attempt is refused
        exactly as before."""
        for _attempt in range(3):
            stat0 = self._stat()
            if stat0 is None:
                return {"engine_id": engine_id,
                        "issued_ts": issued_ts, "stat": None,
                        "size": 0, "tail_hash": "", "seen": set()}
            size0 = stat0[1]
            seen = set()
            prev = ""
            consumed = 0
            boundary_ok = True
            with open(self.path, "rb") as fh:
                i = 0
                while consumed < size0:
                    raw = fh.readline()
                    if not raw:
                        boundary_ok = False  # shrank: a rewrite
                        break
                    if consumed + len(raw) > size0:
                        boundary_ok = False  # boundary mid-line
                        break
                    consumed += len(raw)
                    i += 1
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise LedgerError(
                            f"ledger line {i} is not valid JSON "
                            f"(possible rewrite/corruption): {exc}")
                    body = {k: v for k, v in row.items()
                            if k not in ("row_hash", "prev_hash",
                                         "row_id")}
                    expect = hashlib.sha256(
                        (prev + _canonical(body)).encode()
                    ).hexdigest()
                    if row.get("prev_hash") != prev \
                            or row.get("row_hash") != expect:
                        raise LedgerError(
                            "ledger hash chain is broken; "
                            "refusing to append to a ledger whose "
                            "history does not verify (rewrite "
                            "detected)")
                    prev = row["row_hash"]
                    if row.get("type") == "forecast" \
                            and row.get("engine_id") == engine_id \
                            and row.get("issued_ts") == issued_ts \
                            and row.get("dedupe_key"):
                        seen.add(row["dedupe_key"])
            if not boundary_ok or consumed != size0:
                continue
            return {"engine_id": engine_id,
                    "issued_ts": issued_ts, "stat": stat0,
                    "size": size0, "tail_hash": prev, "seen": seen}
        raise LedgerError(
            "ledger changed repeatedly during the streaming "
            "append pass; refusing to append")

    def _extend_stream_state(self, state):
        """Bring a streaming append state current under the
        append lock (cure LEDGER-APPEND-RACE-20261113): read
        only the bytes appended since the state's snapshot,
        verify the delta's chain links onto the state's tail
        hash exactly as a full pass verifies them, and extend
        the state's tail, dedupe set, stat and size. A file
        that shrank (a rewrite) or a delta that does not chain
        is refused. The caller must hold _append_lock, so no
        estate writer can be mid-line inside the delta: every
        estate append writes its whole row inside the lock."""
        cur = self._stat()
        if cur == state["stat"]:
            return
        if cur is None or cur[1] < state["size"]:
            raise LedgerError(
                "ledger shrank under a streaming append state; "
                "refusing to append (rewrite detected)")
        prev = state["tail_hash"]
        consumed = state["size"]
        with open(self.path, "rb") as fh:
            fh.seek(state["size"])
            while consumed < cur[1]:
                raw = fh.readline()
                if not raw or consumed + len(raw) > cur[1]:
                    raise LedgerError(
                        "ledger delta under a streaming append "
                        "is not a whole number of rows; refusing "
                        "to append")
                consumed += len(raw)
                line = raw.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerError(
                        f"ledger delta line is not valid JSON "
                        f"(possible rewrite/corruption): {exc}")
                body = {k: v for k, v in row.items()
                        if k not in ("row_hash", "prev_hash",
                                         "row_id")}
                expect = hashlib.sha256(
                    (prev + _canonical(body)).encode()).hexdigest()
                if row.get("prev_hash") != prev \
                        or row.get("row_hash") != expect:
                    raise LedgerError(
                        "ledger hash chain is broken in the "
                        "delta past a streaming snapshot; "
                        "refusing to append")
                prev = row["row_hash"]
                if row.get("type") == "forecast" \
                        and row.get("engine_id") == state["engine_id"] \
                        and row.get("issued_ts") == state["issued_ts"] \
                        and row.get("dedupe_key"):
                    state["seen"].add(row["dedupe_key"])
        state["tail_hash"] = prev
        state["stat"] = cur
        state["size"] = cur[1]

    def append_stream_state(self, engine_id, issued_ts):
        """Open a streaming append state for one (engine,
        issuance) batch: see _stream_pass and
        append_forecast_streaming."""
        return self._stream_pass(engine_id, issued_ts)

    def _refresh_stream_state(self, state):
        state.update(self._stream_pass(state["engine_id"],
                                       state["issued_ts"]))

    def _append_streaming(self, row, state):
        """_append's streaming form: the caller guarantees the
        stream state's stat is current (append_forecast_streaming
        extends it under the append lock; the grading path
        refreshes its own state), so the chain link comes from
        the state's tail hash instead of a re-read of the whole
        ledger. The hash, the write, the provenance sidecar and
        the cache discipline are _append's own. The write itself
        takes the append lock (cure LEDGER-APPEND-RACE-20261113)
        so two lanes can never link onto the same tail in the
        same instant; the lock is reentrant per instance, so a
        caller already holding it (the streaming forecast path)
        passes straight through."""
        with self._append_lock():
            return self._append_streaming_locked(row, state)

    def _append_streaming_locked(self, row, state):
        row = dict(row)
        row["prev_hash"] = state["tail_hash"]
        body = {k: v for k, v in row.items()
                if k not in ("row_hash", "prev_hash", "row_id")}
        row["row_hash"] = hashlib.sha256(
            (state["tail_hash"] + _canonical(body)).encode()
        ).hexdigest()
        row["row_id"] = row["row_hash"][:16]
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(_canonical(row) + "\n")
        self._write_provenance(row)
        new_stat = self._stat()
        state["stat"] = new_stat
        if new_stat is not None:
            state["size"] = new_stat[1]
        state["tail_hash"] = row["row_hash"]
        if row.get("type") == "forecast" and row.get("dedupe_key"):
            state["seen"].add(row["dedupe_key"])
        # The parsed-rows cache cannot be extended without
        # holding it; drop it so no later rows() call in this
        # process reads a stale copy, and record the verified
        # stat the stream pass established.
        self._cache_rows = None
        self._cache_stat = None
        self._verified_stat = new_stat
        return row

    # ---- writing -----------------------------------------------------
    def append_genesis(self, note=""):
        if self._stat() is not None:
            raise LedgerError("genesis row already exists")
        return self._append({"type": "genesis", "program": "forecast-engines-30",
                             "note": note})

    def _forecast_body(self, *, engine_id, issued_ts, subject, quantity,
                       value, horizon_open, horizon_close, lineage,
                       families, outcome, absence_state="present",
                       abstain_reasons=None, scored_zero=None,
                       label_context=None, label_transform_id=None,
                       label_transform_hash=None):
        """Validation and body assembly for a forecast row: the
        one source of truth both append forms (append_forecast
        and append_forecast_streaming) build through, so the two
        paths can never drift in what they validate or store.
        Returns (body, dedupe_key)."""
        if absence_state not in ABSENCE_STATES:
            raise LedgerError(f"unknown absence_state {absence_state!r}")
        reasons_norm = None
        if abstain_reasons is not None:
            reasons_norm = normalize_abstain_reasons(abstain_reasons)
        if absence_state == "present" and reasons_norm:
            raise LedgerError(
                "a taken forecast cannot carry abstention reasons")
        zero_norm = None
        if scored_zero is not None:
            if absence_state != "present":
                raise LedgerError(
                    "a scored zero is a taken row, not an abstention")
            zero_norm = _validate_scored_zero(scored_zero)
        clocks = (lineage or {}).get("clocks") or {}
        missing = [c for c in CLOCK_FIELDS if c not in clocks]
        if missing:
            raise LedgerError(
                f"lineage five-clock envelope is missing clocks: {missing}")
        for art in (lineage or {}).get("source_artifacts") or []:
            if not art.get("path") or not art.get("sha256"):
                raise LedgerError(
                    "every lineage source artifact needs path and sha256")
        if self.registry is not None:
            self.registry.validate_engine(engine_id)
            for fam in families:
                self.registry.validate_family(fam)
        if horizon_close < horizon_open:
            raise LedgerError("horizon_close precedes horizon_open")
        identity = _validate_label_identity(
            label_context, label_transform_id, label_transform_hash)
        vhash = value_hash(value)
        key = dedupe_key(engine_id, subject, horizon_open, horizon_close,
                         vhash)
        if identity is not None:
            key = key + "|label:" + identity["label_context_fingerprint"] \
                + ":" + identity["label_transform_hash"]
        body = {
            "type": "forecast", "engine_id": engine_id,
            "issued_ts": issued_ts, "subject": subject, "quantity": quantity,
            "value": value, "value_hash": vhash,
            "horizon_open": horizon_open, "horizon_close": horizon_close,
            "lineage": lineage, "families": list(families),
            "outcome": outcome, "absence_state": absence_state,
            "dedupe_key": key}
        if absence_state != "present":
            body["abstain_reasons"] = reasons_norm or []
        elif reasons_norm is not None:
            body["abstain_reasons"] = reasons_norm
        if zero_norm is not None:
            body["scored_zero"] = zero_norm
        if identity is not None:
            body.update(identity)
        return body, key

    # ---- dedupe offset index (LEDGER-DEDUPE-INDEX-20261113) ------
    _DEDUPE_MARKER = b'"dedupe_key":"'

    def _dedupe_offsets(self):
        """{dedupe_key: byte offset of its first forecast row}.

        Why: the classic append paths proved a republication by
        streaming the whole ledger and parsing every row's JSON
        (about 9s at 400k rows / 800 MB), and they did it once
        per append, twice over (append_forecast_declared's
        legacy scan, then append_forecast's own). A bulk caller
        recording dozens of forecasts in one run therefore paid
        minutes of re-parsing per run (insider divergence's
        appends landed 20 to 50 seconds apart on 2026-11-13 and
        the leg never finished). The ledger is append-only, so
        a row's byte offset never changes: this index is built
        by ONE raw scan that reads each forecast row's stored
        dedupe key out of the raw line without parsing it, and
        later calls rescan only the bytes appended since the
        indexed size. A file that shrank, or whose size stands
        still while its mtime moved (an in-place rewrite),
        forces a full rebuild. The index only ever LOCATES a
        candidate row; the caller parses that one line and
        applies the exact checks the full scan applied, so the
        dedupe verdicts are the scan's own."""
        stat = self._stat()
        if stat is None:
            return {}
        if self._dedupe_index is not None \
                and self._dedupe_index_stat == stat:
            return self._dedupe_index
        index = self._dedupe_index
        start = 0
        if index is not None and stat[1] > self._dedupe_index_size:
            start = self._dedupe_index_size  # pure growth: rescan
            # only the appended suffix; earlier offsets stand.
        else:
            index = {}
        marker = self._DEDUPE_MARKER
        with open(self.path, "rb") as fh:
            fh.seek(start)
            offset = start
            for raw in fh:
                i = raw.find(marker)
                if i >= 0:
                    j = raw.find(b'"', i + len(marker))
                    if j > i:
                        key = raw[i + len(marker):j].decode(
                            "utf-8", "replace")
                        if key not in index:
                            index[key] = offset
                offset += len(raw)
        self._dedupe_index = index
        self._dedupe_index_size = offset
        self._dedupe_index_stat = self._stat()
        return index

    def _find_forecast_row(self, key):
        """The first forecast row stored under dedupe key `key`,
        or None: the offset index locates the candidate line and
        only that line is parsed, with the same invalid-JSON
        refusal rows() raises."""
        offset = self._dedupe_offsets().get(key)
        if offset is None:
            return None
        with open(self.path, "r", encoding="utf-8") as fh:
            fh.seek(offset)
            line = fh.readline().strip()
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(
                f"ledger line at byte {offset} is not valid JSON "
                f"(possible rewrite/corruption): {exc}")
        if row.get("type") != "forecast" \
                or row.get("dedupe_key") != key:
            return None
        return row

    def append_forecast(self, *, engine_id, issued_ts, subject, quantity,
                        value, horizon_open, horizon_close, lineage,
                        families, outcome, absence_state="present",
                        abstain_reasons=None, scored_zero=None,
                        label_context=None, label_transform_id=None,
                        label_transform_hash=None):
        """Append a forecast row. Returns (row, created). A duplicate
        republication returns (existing_row, False) and writes nothing.

        An abstention row (absence_state other than present) may carry
        abstain_reasons in the fixed vocabulary (see
        normalize_abstain_reasons); they are stored sorted and
        deduplicated. An abstention appended without reasons stores
        an empty list, so reasonless refusals stay countable in the
        coverage audit rather than invisible. A taken row must not
        carry abstention reasons.

        A passed event is ledgered as a scored zero (scored_zero
        marker, see _validate_scored_zero): a taken row, never an
        abstention.

        Label freezing (DEEP-PASS 3.2 item 3): label_context (the
        six field context), label_transform_id and
        label_transform_hash freeze what this forecast's label
        means. Supply all three or none; the row stores the context,
        its fingerprint and the transform binding, the dedupe key
        separates the same value issued under a different label
        definition, and any later grade must repeat the identity
        exactly (see append_grade)."""
        body, key = self._forecast_body(
            engine_id=engine_id, issued_ts=issued_ts, subject=subject,
            quantity=quantity, value=value,
            horizon_open=horizon_open, horizon_close=horizon_close,
            lineage=lineage, families=families, outcome=outcome,
            absence_state=absence_state,
            abstain_reasons=abstain_reasons, scored_zero=scored_zero,
            label_context=label_context,
            label_transform_id=label_transform_id,
            label_transform_hash=label_transform_hash)
        # Dedupe via the offset index (LEDGER-DEDUPE-INDEX-
        # 20261113): the same first forecast row the iter_rows
        # scan returned, located without re-parsing the ledger.
        existing = self._find_forecast_row(key)
        if existing is not None:
            return existing, False
        row = self._append(body)
        return row, True

    def append_forecast_declared(self, **kwargs):
        """Append a forecast with its label identity declared at
        issue time through the one shared mechanism (RC-21 cure,
        2026-10-30): every issuing refresher calls this instead of
        append_forecast, and the identity is the derived one from
        default_label_identity (the forecast's own subject, quantity
        and outcome spec), never a per refresher copy. An explicit
        identity in kwargs is respected as supplied. A republication
        of a forecast already on the ledger as an unfrozen legacy
        row returns that row: history is never rewritten, and a
        cured refresher does not double its own record on its first
        re-run; genuinely new issues carry the frozen identity."""
        if kwargs.get("label_context") is None \
                and kwargs.get("label_transform_id") is None \
                and kwargs.get("label_transform_hash") is None:
            plain = dedupe_key(
                kwargs["engine_id"], kwargs["subject"],
                kwargs["horizon_open"], kwargs["horizon_close"],
                value_hash(kwargs["value"]))
            # The legacy-row check via the offset index
            # (LEDGER-DEDUPE-INDEX-20261113): a stored key equal
            # to the plain key can only sit on an unfrozen row
            # (a frozen row's stored key carries the label
            # suffix), and the parsed candidate still goes
            # through frozen_label_identity exactly as the
            # streaming scan did.
            legacy = self._find_forecast_row(plain)
            if legacy is not None \
                    and frozen_label_identity(legacy) is None:
                return legacy, False
            kwargs.update(default_label_identity(
                subject=kwargs["subject"], quantity=kwargs["quantity"],
                outcome=kwargs.get("outcome")))
        return self.append_forecast(**kwargs)

    def append_forecast_streaming(self, state, **kwargs):
        """append_forecast_declared's streaming form
        (PROOFGATE-APPEND-STREAM-20261105), for a bulk batch of
        one (engine, issuance) whose horizon_open is the
        issuance session itself (the proof gate's forward
        records): under that convention a duplicate of a batch
        row can only live inside the batch, so the batch's own
        dedupe keys, collected by append_stream_state, are the
        whole dedupe universe and the parsed ledger is never
        loaded. Validation and body assembly are the shared
        _forecast_body; the append is _append_streaming.

        Returns (row, True) for a new issue and (None, False)
        for a republication: the existing row is never loaded,
        so it cannot be returned; callers that need it use the
        classic path. A state opened for a different (engine,
        issuance), or a call whose horizon_open is not its
        issued_ts, is refused rather than silently mis-scoped."""
        if state["engine_id"] != kwargs.get("engine_id") \
                or state["issued_ts"] != kwargs.get("issued_ts"):
            raise LedgerError(
                "streaming append state is for a different "
                "(engine, issuance) batch than the append")
        if kwargs.get("horizon_open") != kwargs.get("issued_ts"):
            raise LedgerError(
                "streaming append requires horizon_open == "
                "issued_ts (the batch convention its dedupe "
                "scope rests on)")
        if kwargs.get("label_context") is None \
                and kwargs.get("label_transform_id") is None \
                and kwargs.get("label_transform_hash") is None:
            plain = dedupe_key(
                kwargs["engine_id"], kwargs["subject"],
                kwargs["horizon_open"], kwargs["horizon_close"],
                value_hash(kwargs["value"]))
            if plain in state["seen"]:
                return None, False
            kwargs.update(default_label_identity(
                subject=kwargs["subject"],
                quantity=kwargs["quantity"],
                outcome=kwargs.get("outcome")))
        call = {"absence_state": "present", "abstain_reasons": None,
                "scored_zero": None, "label_context": None,
                "label_transform_id": None,
                "label_transform_hash": None}
        call.update(kwargs)
        body, key = self._forecast_body(**call)
        if key in state["seen"]:
            return None, False
        # Extend-and-write under the append lock (cure
        # LEDGER-APPEND-RACE-20261113): the state is brought
        # current over just the delta appended since its
        # snapshot (each delta row hash-verified onto the
        # state's tail), the dedupe check runs against the
        # extended set, and the write itself is serialized, so
        # another lane's appends during the batch are absorbed
        # one delta at a time instead of refusing the batch.
        with self._append_lock():
            self._extend_stream_state(state)
            if key in state["seen"]:
                return None, False
            return self._append_streaming(body, state), True

    def append_grade(self, *, forecast_row, grade,
                     label_context_fingerprint=None,
                     label_transform_id=None, label_transform_hash=None,
                     stream_state=None):
        """Append a grade row referencing the forecast row it grades.
        Refuses to grade a forecast twice (a re-grade is a correction).

        Label freezing (DEEP-PASS 3.2 item 3, structural rule 1):
        when the forecast row carries a frozen label identity, this
        outcome append must repeat it exactly (all three binding
        fields, equal values) or it is refused; the repeated
        identity is stored on the grade row. When the forecast
        carries none, supplying one is refused: an identity cannot
        be invented at outcome time."""
        frozen = frozen_label_identity(forecast_row)
        supplied = {"label_context_fingerprint": label_context_fingerprint,
                    "label_transform_id": label_transform_id,
                    "label_transform_hash": label_transform_hash}
        if frozen is None:
            if any(v is not None for v in supplied.values()):
                raise LedgerError(
                    "grade supplies a label identity but the forecast "
                    "row froze none; an outcome cannot invent the "
                    "label definition it is graded under")
        else:
            if any(v is None for v in supplied.values()):
                raise LedgerError(
                    "outcome append does not repeat the frozen label "
                    "identity (label_context_fingerprint, "
                    "label_transform_id, label_transform_hash are all "
                    "required); refusing to grade under an unstated "
                    "label definition")
            if supplied != frozen:
                raise LedgerError(
                    "outcome append label identity does not match the "
                    "identity frozen on the forecast row; refusing "
                    "to grade a label under a different definition "
                    "than the one it was issued under")
        if stream_state is not None:
            # Streaming form (GRADING-STREAM-20261106): the refusal
            # checks consult the grading stream state's id sets
            # instead of a rows() scan, and the append goes through
            # _append_streaming, so grading a ledger of any size
            # never parses it. The checks, the messages and the
            # appended body are the classic path's own; if the file
            # moved under the state (another writer appended), the
            # state is rebuilt once and the checks run again
            # against the fresh sets.
            for _attempt in range(2):
                if forecast_row["row_id"] in \
                        stream_state["voided_by"]:
                    raise LedgerError(
                        "forecast voided by correction "
                        f"{stream_state['voided_by'][forecast_row['row_id']]}; "
                        "refusing to grade a voided forecast "
                        "(grade rows on voided forecasts cure, "
                        "2026-10-30, defect 8)")
                if forecast_row["row_id"] in \
                        stream_state["graded_ids"]:
                    raise LedgerError(
                        "forecast already graded; append a correction "
                        "row instead of a second grade")
                body = {
                    "type": "grade",
                    "engine_id": forecast_row["engine_id"],
                    "forecast_row_id": forecast_row["row_id"],
                    "subject": forecast_row["subject"],
                    "horizon_close": forecast_row["horizon_close"],
                    "grade": grade}
                if frozen is not None:
                    body.update(frozen)
                if self._stat() == stream_state["stat"]:
                    appended = self._append_streaming(body,
                                                      stream_state)
                    stream_state["graded_ids"].add(
                        forecast_row["row_id"])
                    stream_state["grade_count"] += 1
                    return appended
                stream_state.update(self.grading_stream_state())
            raise LedgerError(
                "ledger changed repeatedly during streaming grade "
                "appends; refusing to append")
        # The refusal checks stream (LEDGER-APPEND-TAIL-20261109):
        # same two checks, same messages, one parsed row held.
        for row in self.iter_rows():
            if row.get("type") == "correction" and \
                    row.get("corrects_row_id") == forecast_row["row_id"]:
                raise LedgerError(
                    "forecast voided by correction "
                    f"{row['row_id']}; refusing to grade a voided "
                    "forecast (grade rows on voided forecasts cure, "
                    "2026-10-30, defect 8)")
            if row.get("type") == "grade" and \
                    row.get("forecast_row_id") == forecast_row["row_id"]:
                raise LedgerError(
                    "forecast already graded; append a correction row "
                    "instead of a second grade")
        body = {
            "type": "grade", "engine_id": forecast_row["engine_id"],
            "forecast_row_id": forecast_row["row_id"],
            "subject": forecast_row["subject"],
            "horizon_close": forecast_row["horizon_close"],
            "grade": grade}
        if frozen is not None:
            body.update(frozen)
        return self._append(body)

    def append_correction(self, *, corrects_row_id, note, payload=None):
        ids = {r["row_id"] for r in self.iter_rows()}
        if corrects_row_id not in ids:
            raise LedgerError(f"correction targets unknown row {corrects_row_id}")
        return self._append({"type": "correction",
                             "corrects_row_id": corrects_row_id,
                             "note": note, "payload": payload or {}})


def recompute_figures(rows):
    """Recompute every published figure from ledger rows alone.
    Returns per-engine counts and mean scores by grading rule.

    `rows` may be any iterable of parsed rows, including a
    one-shot generator (LEDGER-STREAM-FIGURES-20261109): it is
    consumed exactly once. The forecast and correction rows
    stream into the two collections the grade pass needs
    (forecast rows by id, voided ids), and the grade rows
    stream through the counting loop directly; the old form
    walked its argument three times, which on a list was
    merely wasteful and on a one-shot stream would have
    silently produced empty figures. Callers holding a Ledger
    can pass ledger.iter_rows() instead of the parsed whole;
    the verdicts are identical on the same file and resident
    memory stays at one parsed row plus the forecast rows
    themselves, which the grade pass must look up by id in
    any implementation.

    Void exclusion (defect 8 cure, 2026-10-30): a forecast voided
    by a correction row is counted in forecasts_voided and its
    valid remainder in forecasts_valid; grades on voided forecasts
    are counted only in grades_on_voided and graded_raw, never in
    graded or in any mean score.

    Label freezing (DEEP-PASS 3.2 item 3, structural rule 2): scores
    are grouped by the label fingerprint frozen on the forecast row
    each grade grades (grades of unfrozen rows form the single
    UNFROZEN_GROUP). The per group means live under
    by_label_fingerprint; the top level mean_scores is that single
    group's means when the engine has exactly one group, and empty
    when it has more than one, because pooling outcomes across
    fingerprints is refused, never averaged over."""
    forecasts = {}
    corrects = []
    grade_rows = []
    for r in rows:
        kind = r.get("type")
        if kind == "forecast":
            forecasts[r["row_id"]] = r
        elif kind == "correction":
            corrects.append(r.get("corrects_row_id"))
        elif kind == "grade":
            grade_rows.append(r)
    voided_ids = {c for c in corrects if c in forecasts}
    figures = {}
    groups = {}  # engine_id -> group key -> {"scores": {}, ...}

    def _engine(engine_id):
        return figures.setdefault(engine_id, {
            "forecasts": 0, "graded": 0, "scored_zero": 0,
            "forecasts_voided": 0, "forecasts_valid": 0,
            "grades_on_voided": 0, "graded_raw": 0})

    def _group(engine_id, forecast_row):
        identity = frozen_label_identity(forecast_row) \
            if forecast_row else None
        key = identity["label_context_fingerprint"] if identity \
            else UNFROZEN_GROUP
        grp = groups.setdefault(engine_id, {}).setdefault(key, {
            "forecasts": 0, "graded": 0, "scores": {},
            "label_transform_id":
                identity["label_transform_id"] if identity else None,
            "label_transform_hash":
                identity["label_transform_hash"] if identity else None})
        return grp

    for row in forecasts.values():
        eng = _engine(row["engine_id"])
        eng["forecasts"] += 1
        if row["row_id"] in voided_ids:
            eng["forecasts_voided"] += 1
        else:
            eng["forecasts_valid"] += 1
        _group(row["engine_id"], row)["forecasts"] += 1
        if is_scored_zero(row):
            _engine(row["engine_id"])["scored_zero"] += 1
    for row in grade_rows:
        eng = _engine(row["engine_id"])
        eng["graded_raw"] += 1
        if row.get("forecast_row_id") in voided_ids:
            # Grades of voided forecasts stay in the ledger
            # (append-only) and stay named in grades_on_voided, but
            # they leave the graded counts and every mean: the
            # forecast was withdrawn, so its score is not a result
            # (defect 8 cure, 2026-10-30).
            eng["grades_on_voided"] += 1
            continue
        eng["graded"] += 1
        grp = _group(row["engine_id"], forecasts.get(row["forecast_row_id"]))
        grp["graded"] += 1
        for name, val in (row["grade"].get("scores") or {}).items():
            if isinstance(val, (int, float)):
                grp["scores"].setdefault(name, []).append(val)
    for engine_id, eng in figures.items():
        by_group = {}
        for key, grp in groups.get(engine_id, {}).items():
            by_group[key] = {
                "forecasts": grp["forecasts"], "graded": grp["graded"],
                "label_transform_id": grp["label_transform_id"],
                "label_transform_hash": grp["label_transform_hash"],
                "mean_scores": {
                    name: sum(vals) / len(vals)
                    for name, vals in grp["scores"].items() if vals}}
        eng["by_label_fingerprint"] = by_group
        if len(by_group) == 1:
            eng["mean_scores"] = next(iter(by_group.values()))["mean_scores"]
        else:
            eng["mean_scores"] = {}
    return figures
