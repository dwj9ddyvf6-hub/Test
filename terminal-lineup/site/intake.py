#!/usr/bin/env python3
"""CSV intake contracts for the terminal (adopted 2026-10-29 from the
Codex terminal deep pass, DEEP-PASS.md Sections 2.0 point 4, 2.4 and
3.1 items 4 and 5).

Two contracts live here, one source of truth for both:

1. ANTI FIXTURE SOURCE REJECTION (3.1 item 4). Any row whose source
   field reads synthetic, sample or fixture is refused as market
   input. The check keys on the self declared source label (a column
   named source, data source, source name, side source or provenance,
   in any casing or punctuation), tokenised on non alphanumeric
   characters, so "synthetic", "SYNTHETIC SAMPLE" and "fixture_v2"
   all trip it while a real source name that merely contains those
   letters inside a longer word does not. This is a labelling guard,
   not a provenance proof, and it is stated that way wherever it is
   used. Generic CSV intakes raise on a fixture row (the whole intake
   fails, as the Bullflow importer does); the evidence contract below
   rejects fixture rows per row with a named reason instead, because
   its output contract is per row accounting.

2. EVIDENCE CSV INTAKE CONTRACT (3.1 item 5), a port of the
   parseEvidenceCsv semantics. Hard caps: 10 MiB of input, 50,000
   data rows, 8,192 characters per field; exceeding a file level cap
   refuses the whole file. Fixed three clock schema: required
   ObservedAt, Entity, Source, Metric, Value; optional PublicAt,
   ReceivedAt, Unit, Method, Confidence, EventType, SourceURL.
   Header names are normalised (case and punctuation insensitive)
   and an unknown or duplicate column refuses the whole file.
   Rows are never repaired and never silently dropped: every data
   row is either accepted or returned in the rejected list with its
   1 based line number (header is line 1) and a named reason.
   Accepted rows carry absent optional fields as None, never as an
   invented value.

No network, no fabricated data: this module only judges text a
person or a loader already holds.
"""

import csv
import io
import re
from datetime import datetime
from urllib.parse import urlparse

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50000
MAX_FIELD_CHARS = 8192

FIXTURE_TOKENS = frozenset({"synthetic", "sample", "fixture"})
FIXTURE_MESSAGE = ("synthetic, sample, and fixture records are not "
                   "accepted as market input")

_SOURCE_FIELD_NAMES = frozenset({
    "source", "datasource", "sourcename", "sidesource",
    "sideprovenance", "provenance",
})

EVIDENCE_REQUIRED = ("ObservedAt", "Entity", "Source", "Metric", "Value")
EVIDENCE_OPTIONAL = ("PublicAt", "ReceivedAt", "Unit", "Method",
                     "Confidence", "EventType", "SourceURL")
EVIDENCE_COLUMNS = EVIDENCE_REQUIRED + EVIDENCE_OPTIONAL

_CLOCK_COLUMNS = ("ObservedAt", "PublicAt", "ReceivedAt")


class IntakeError(ValueError):
    """A whole intake is refused (file level cap, bad header, or a
    fixture row in a generic market intake)."""


def _norm(name):
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def is_fixture_source(value):
    """True when a self declared source label names a fixture: any
    alphanumeric token of the label is synthetic, sample or fixture."""
    if value is None:
        return False
    tokens = re.split(r"[^a-z0-9]+", str(value).strip().lower())
    return any(tok in FIXTURE_TOKENS for tok in tokens if tok)


def source_field_names(fieldnames):
    """The subset of a header that declares a source, by normalised
    name. Empty when the intake carries no source column at all."""
    return [f for f in (fieldnames or []) if _norm(f) in _SOURCE_FIELD_NAMES]


def check_fixture_rows(rows, fieldnames=None):
    """Raise IntakeError naming the first fixture row (line numbers
    count the header as line 1, so the first data row is line 2).
    Returns the row count checked. A header with no source column
    checks nothing and passes, stated plainly in the docstring."""
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    fields = source_field_names(fieldnames)
    for i, row in enumerate(rows):
        for field in fields:
            if is_fixture_source(row.get(field)):
                raise IntakeError(
                    f"row {i + 2}: {FIXTURE_MESSAGE} "
                    f"(source field {field!r} reads {row.get(field)!r})")
    return len(rows)


def _read_table(source):
    """Decode and split a CSV source under the file level caps.
    Returns the raw table (header row first). Raises IntakeError on
    a cap breach, undecodable bytes, or malformed CSV."""
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
        if len(raw) > MAX_BYTES:
            raise IntakeError(
                f"CSV input is {len(raw)} bytes, over the "
                f"{MAX_BYTES} byte (10 MiB) cap")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise IntakeError(f"CSV input is not UTF-8: {exc}") from exc
    else:
        text = str(source)
        if len(text.encode("utf-8")) > MAX_BYTES:
            raise IntakeError("CSV input is over the 10 MiB cap")
        if text.startswith("\ufeff"):
            text = text[1:]
    try:
        table = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise IntakeError(f"CSV input does not parse: {exc}") from exc
    table = [row for row in table if any(c.strip() for c in row)]
    if not table:
        raise IntakeError("CSV input carries no header row")
    if len(table) - 1 > MAX_ROWS:
        raise IntakeError(
            f"CSV input carries {len(table) - 1} data rows, over the "
            f"{MAX_ROWS} row cap")
    for row in table:
        for cell in row:
            if len(cell) > MAX_FIELD_CHARS:
                raise IntakeError(
                    f"CSV input carries a field over the "
                    f"{MAX_FIELD_CHARS} character cap")
    return table


def read_csv_dicts_guarded(source):
    """Generic guarded CSV intake for market data loaders: caps,
    plus the anti fixture source rejection applied to every row.
    Returns a list of dicts keyed by the header exactly as written.
    Raises IntakeError on any refusal; nothing is silently dropped."""
    table = _read_table(source)
    header = [h.strip() for h in table[0]]
    rows = []
    for cells in table[1:]:
        if len(cells) != len(header):
            raise IntakeError(
                f"row carries {len(cells)} fields against a "
                f"{len(header)} column header; rows are not repaired")
        rows.append(dict(zip(header, cells)))
    check_fixture_rows(rows, header)
    return rows


def _parse_timestamp(value):
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


_EVIDENCE_BY_NORM = {_norm(c): c for c in EVIDENCE_COLUMNS}


def parse_evidence_csv(source):
    """The evidence CSV intake contract. Returns a dict with
    accepted (list of row dicts keyed by the canonical column names,
    absent optional fields as None, plus a _line entry), rejected
    (list of {line, reason, row} with the row keyed canonically
    where the header allowed), and the two counts. File level
    problems (caps, unknown or duplicate or missing header columns)
    raise IntakeError instead, because no per row accounting is
    meaningful without a known schema."""
    table = _read_table(source)
    header_raw = table[0]
    canonical = []
    seen = set()
    for name in header_raw:
        col = _EVIDENCE_BY_NORM.get(_norm(name))
        if col is None:
            raise IntakeError(
                f"unknown evidence column {name!r}; allowed columns "
                f"are {', '.join(EVIDENCE_COLUMNS)}")
        if col in seen:
            raise IntakeError(f"duplicate evidence column {name!r}")
        seen.add(col)
        canonical.append(col)
    missing = [c for c in EVIDENCE_REQUIRED if c not in seen]
    if missing:
        raise IntakeError(
            f"evidence CSV is missing required columns: "
            f"{', '.join(missing)}")

    accepted, rejected = [], []

    def reject(line, reason, row):
        rejected.append({"line": line, "reason": reason, "row": row})

    for idx, cells in enumerate(table[1:]):
        line = idx + 2
        if len(cells) != len(canonical):
            reject(line, "wrong_field_count", None)
            continue
        row = {col: (cells[canonical.index(col)].strip()
                     if col in seen else None)
               for col in EVIDENCE_COLUMNS}
        reason = None
        for col in EVIDENCE_COLUMNS:
            value = row[col]
            if value is not None and len(value) > MAX_FIELD_CHARS:
                reason = f"field_too_long:{col}"
                break
        if reason is None:
            for col in EVIDENCE_REQUIRED:
                if not row[col]:
                    reason = f"missing_required:{col}"
                    break
        if reason is None and is_fixture_source(row["Source"]):
            reason = "fixture_source"
        if reason is None:
            for col in _CLOCK_COLUMNS:
                if row[col] and _parse_timestamp(row[col]) is None:
                    reason = f"invalid_timestamp:{col}"
                    break
        if reason is None and row["Confidence"]:
            try:
                conf = float(row["Confidence"])
                if not (0.0 <= conf <= 1.0):
                    reason = "invalid_confidence"
            except ValueError:
                reason = "invalid_confidence"
        if reason is None and row["SourceURL"]:
            parsed = urlparse(row["SourceURL"])
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                reason = "invalid_source_url"
        if reason is not None:
            reject(line, reason, row)
            continue
        row["_line"] = line
        accepted.append(row)
    return {"accepted": accepted, "rejected": rejected,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected)}
