#!/usr/bin/env python3
"""Report-only grounding verifier for compiled research pages. ADOPT A2.

For each compiled research page, extracts a frozen candidate set (direct
quotes of 15+ characters, ISO dates, high-signal numbers), strips fenced and
inline code, links, metadata headers and Status blocks before extraction, and
verifies each candidate appears verbatim in the body (metadata header
excluded) of the source files named in the page's Sources or Raw field,
resolving those files through the A1 manifest where one exists.

Report sections only: fidelity suspects (misses; suspects, never verdicts),
evidence errors, unreferenced sources. Also flags malformed Status blocks.
Writes nothing; exit code carries no verdict (0 on a completed run).
Stdlib only: re, sys, pathlib, dataclasses, json.
"""
import json, re, sys
from dataclasses import dataclass, field
from pathlib import Path

QUOTE_RE = re.compile(r'"([^"\n]{15,})"')
DATE_RE = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')
NUM_PATTERNS = [
    re.compile(r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b'),          # thousands-grouped
    re.compile(r'\b\d+\.\d+\b'),                              # dotted
    re.compile(r'\b\d+(?:\.\d+)?[KMB]\b'),                    # suffixed K/M/B
    re.compile(r'\b\d+(?:\.\d+)?%'),                          # percent
    re.compile(r'\b\d{4,}\b'),                                # 4+ digits
]
SOURCE_FIELD_RE = re.compile(r'^\s*(?:[-*]\s*)?(?:Sources?|Raw)\s*:\s*(.+)$', re.M)
PATH_RE = re.compile(r'[\w./~+-]+\.(?:md|txt|json|csv|html)\b')
STATUS_RE = re.compile(r'^>\s*\*\*Status:\s*(Outdated|Disputed)\*\*\s*(.*)$', re.M)


@dataclass
class PageReport:
    page: str
    suspects: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    malformed_status: list = field(default_factory=list)


def strip_metadata(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            return text[nl + 1:] if nl != -1 else ""
    return text


def strip_for_extraction(text: str) -> str:
    text = re.sub(r'```.*?```', '', text, flags=re.S)          # fenced code
    text = re.sub(r'`[^`\n]*`', '', text)                      # inline code
    text = re.sub(r'\[[^\]]*\]\([^)]*\)', '', text)            # links
    text = re.sub(r'^>.*$', '', text, flags=re.M)              # Status blocks / quotes
    return text


def extract_candidates(text: str) -> list:
    body = strip_for_extraction(strip_metadata(text))
    found = []
    for m in QUOTE_RE.finditer(body):
        found.append(m.group(1))
    for m in DATE_RE.finditer(body):
        found.append(m.group(0))
    for pat in NUM_PATTERNS:
        for m in pat.finditer(body):
            found.append(m.group(0))
    # De-duplicate, preserve order; dates inside quotes are their own candidates.
    seen, out = set(), []
    for c in found:
        if c not in seen:
            seen.add(c); out.append(c)
    return out


def check_status_blocks(text: str) -> list:
    bad = []
    for m in STATUS_RE.finditer(text):
        kind, rest = m.group(1), m.group(2).strip()
        if kind == "Outdated" and not DATE_RE.search(rest):
            bad.append(f"Status: Outdated block missing its date: {m.group(0)[:80]}")
        if not rest or (kind == "Outdated" and rest.strip("() ").isdigit()):
            bad.append(f"Status block missing its explanation: {m.group(0)[:80]}")
    # Any Status-looking block that does not match the format at all.
    for line in text.splitlines():
        if line.startswith("> **Status:") and not STATUS_RE.match(line):
            bad.append(f"Malformed Status block: {line[:80]}")
    return bad


def resolve_sources(page: Path, program: Path, manifest_entries: list) -> tuple:
    text = page.read_text(encoding="utf-8", errors="replace")
    fields = SOURCE_FIELD_RE.findall(text)
    sources, errors = [], []
    if not fields:
        errors.append("page has no Sources or Raw field")
        return sources, errors, text
    by_raw_path = {e.get("raw_path"): e for e in manifest_entries}
    named = []
    for f in fields:
        named.extend(PATH_RE.findall(f))
    if not named:
        errors.append("Sources or Raw field names no resolvable file")
    sources_root = (program / "sources").resolve()
    for name in named:
        candidates = [page.parent / name, program / name, Path(name).expanduser()]
        hit = next((c for c in candidates if c.is_file()), None)
        if hit is None and name in by_raw_path:
            hit = program / name
        if hit is None:
            errors.append(f"source link does not resolve: {name}")
            continue
        resolved = hit.resolve()
        in_sources = False
        try:
            in_sources = resolved.is_relative_to(sources_root)
        except AttributeError:
            in_sources = str(resolved).startswith(str(sources_root))
        if not in_sources:
            errors.append(f"source path escapes the program's sources/ tree: {name}")
            continue
        sources.append(resolved)
    return sources, errors, text


def load_manifest(program: Path) -> list:
    mp = program / "sources" / "MANIFEST.json"
    if mp.is_file():
        try:
            return json.loads(mp.read_text(encoding="utf-8")).get("entries", [])
        except Exception:
            return []
    return []


def no_material_raw_paths(program: Path) -> set:
    out = set()
    log = program / "INGEST-LOG.md"
    if log.is_file():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r'## \[\d{4}-\d{2}-\d{2}\] ingest \| No material: (.+)$', line.strip())
            if m:
                out.add(m.group(1).strip())
    return out


def check_page(page: Path, program: Path, manifest_entries: list) -> PageReport:
    rep = PageReport(page=str(page))
    sources, errors, text = resolve_sources(page, program, manifest_entries)
    rep.errors.extend(errors)
    rep.malformed_status.extend(check_status_blocks(text))
    if sources:
        bodies = []
        for s in sources:
            bodies.append(strip_metadata(s.read_text(encoding="utf-8", errors="replace")))
        joined = "\n".join(bodies)
        for cand in extract_candidates(text):
            if cand not in joined:
                rep.suspects.append(cand)
    return rep


def is_archived_answer(text: str) -> bool:
    return "[Archived]" in text[:400] or "Archived date:" in text[:2000]


def run(program: Path) -> dict:
    program = Path(program)
    manifest_entries = load_manifest(program)
    pages = sorted(p for p in program.glob("*.md")
                   if p.name not in ("INGEST-LOG.md",))
    reports, referenced = [], set()
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        if is_archived_answer(text):
            continue  # archived-answer class is exempt from A2 verification
        rep = check_page(page, program, manifest_entries)
        reports.append(rep)
        srcs, _, _ = resolve_sources(page, program, manifest_entries)
        for s in srcs:
            try:
                referenced.add(s.relative_to(program.resolve()).as_posix())
            except Exception:
                pass
    exempt = no_material_raw_paths(program)
    unreferenced = []
    for e in manifest_entries:
        rp = e.get("raw_path")
        if rp and rp not in referenced and rp not in exempt:
            unreferenced.append(rp)
    return {"program": str(program), "pages": reports, "unreferenced": unreferenced}


def format_report(result: dict) -> str:
    lines = [f"check_evidence report: {result['program']}"]
    total_suspects = 0
    lines.append("== Fidelity suspects (misses; suspects, never verdicts) ==")
    for rep in result["pages"]:
        for s in rep.suspects:
            total_suspects += 1
            lines.append(f"{rep.page}: {s}")
    if total_suspects == 0:
        lines.append("(none)")
    lines.append("== Evidence errors ==")
    n_err = 0
    for rep in result["pages"]:
        for e in rep.errors:
            n_err += 1; lines.append(f"{rep.page}: {e}")
        for mb in rep.malformed_status:
            n_err += 1; lines.append(f"{rep.page}: malformed Status block: {mb}")
    if n_err == 0:
        lines.append("(none)")
    lines.append("== Unreferenced sources ==")
    if result["unreferenced"]:
        lines.extend(result["unreferenced"])
    else:
        lines.append("(none)")
    lines.append(f"counts: pages={len(result['pages'])} suspects={total_suspects} "
                 f"evidence_errors={n_err} unreferenced={len(result['unreferenced'])}")
    return "\n".join(lines)


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__); print("usage: check_evidence.py <program_folder>")
        return 2
    result = run(Path(argv[1]))
    print(format_report(result))
    return 0  # exit code carries no verdict


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
