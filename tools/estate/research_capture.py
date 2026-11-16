#!/usr/bin/env python3
"""Content-addressed research source capture. ADOPT A1, Obsidian sweep 2026-11-02.

Takes a local file and a research program folder; computes SHA-256; copies the
file create-only into <program>/sources/raw/; creates or updates
<program>/sources/MANIFEST.json in the same operation. An identical hash
already present is a no-op reported as already captured. The same slug with
different content creates a new dated capture and never overwrites.
No network, no execution of the captured file, no writes outside the named
program folder. Stdlib only.
"""
import hashlib, json, re, shutil, sys
from datetime import date
from pathlib import Path


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(name: str) -> str:
    stem = Path(name).stem
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-").lower()
    return slug or "source"


def load_manifest(manifest_path: Path) -> dict:
    if manifest_path.is_file():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"entries": []}


def capture(src: Path, program: Path, locator: str = "", captured: str = "") -> dict:
    src = Path(src); program = Path(program)
    if not src.is_file():
        raise FileNotFoundError(f"source file not found: {src}")
    digest = sha256_of(src)
    size = src.stat().st_size
    captured = captured or date.today().isoformat()
    raw_dir = program / "sources" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = program / "sources" / "MANIFEST.json"
    manifest = load_manifest(manifest_path)
    entries = manifest.setdefault("entries", [])
    for e in entries:
        if e.get("sha256") == digest:
            return {"status": "already_captured", "sha256": digest,
                    "raw_path": e.get("raw_path"), "manifest": str(manifest_path)}
    slug = slugify(src.name)
    ext = src.suffix
    candidate = raw_dir / f"{slug}{ext}"
    if candidate.exists():
        # Same slug, different content (identical content returned above):
        # new dated capture, never overwrite.
        candidate = raw_dir / f"{slug}-{captured}-{digest[:8]}{ext}"
        n = 2
        while candidate.exists():
            candidate = raw_dir / f"{slug}-{captured}-{digest[:8]}-{n}{ext}"
            n += 1
    # Create-only copy: exclusive create via hardlink-free byte copy.
    with open(src, "rb") as fin, open(candidate, "xb") as fout:
        shutil.copyfileobj(fin, fout)
    if sha256_of(candidate) != digest:
        candidate.unlink()
        raise IOError("captured copy hash mismatch; capture aborted")
    rel = candidate.relative_to(program).as_posix()
    entry = {"sha256": digest, "captured": captured,
             "original_filename": src.name, "byte_size": size,
             "raw_path": rel}
    if locator:
        entry["locator"] = locator
    entries.append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    return {"status": "captured", "sha256": digest, "raw_path": rel,
            "manifest": str(manifest_path)}


def main(argv) -> int:
    if len(argv) < 3:
        print(__doc__); print("usage: research_capture.py <file> <program_folder> [--locator URL] [--date YYYY-MM-DD]")
        return 2
    src, program = argv[1], argv[2]
    locator, captured = "", ""
    i = 3
    while i < len(argv):
        if argv[i] == "--locator" and i + 1 < len(argv):
            locator = argv[i + 1]; i += 2
        elif argv[i] == "--date" and i + 1 < len(argv):
            captured = argv[i + 1]; i += 2
        else:
            print(f"unknown argument: {argv[i]}"); return 2
    result = capture(Path(src), Path(program), locator=locator, captured=captured)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
