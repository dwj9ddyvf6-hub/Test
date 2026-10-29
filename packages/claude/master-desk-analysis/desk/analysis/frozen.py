"""The frozen inputs, pinned by content: the spec and the reference scorer exactly as the validator froze them
(FROZEN.md 2026-10-25 23:09 UTC; out2/ENGINE_FINAL.md lists the same hashes). A file whose sha256 differs from its
pin is refused, so the screen never runs on anything else."""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_PATH = os.path.join(HERE, "spec", "engine_spec.json")
SPEC_SHA256 = "2af2c353a07e5c59c11a652cde161c35624cb8840b54f7139762dd4783641110"
SPEC_VERSION = "deep2-engine-secv-1.0.0-final"
SCORER_PATH = os.path.join(HERE, "engine_score_ref.py")
SCORER_SHA256 = "686eb27e2be673721bf8ffcd01c50cf0702a841152bd3f9e49d0bce33c2cab4c"
# the validator's test vectors (40 veto rows, 10 HAR rows), vendored as tests/fixtures/analysis/engine_vectors.csv
VECTORS_SHA256 = "875f652996f4105983b5eb215846f57d37a638eb050b8752f80089fc3cbe0445"
NEEDED = ("veto", "ow", "har", "tier", "universe")      # the sections the screen reads


class SpecError(RuntimeError):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_spec(path=SPEC_PATH, sha256=SPEC_SHA256):
    """(spec, its sha256) when the file is the pinned one; SpecError otherwise (missing, changed, unreadable)"""
    if not sha256:
        raise SpecError("no sha256 pin for the spec")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        raise SpecError("spec unreadable: %s" % e)
    got = hashlib.sha256(raw).hexdigest()
    if got != sha256:
        raise SpecError("spec sha256 %s is not the pinned %s" % (got, sha256))
    try:
        spec = json.loads(raw)
    except ValueError as e:
        raise SpecError("spec is not JSON: %s" % e)
    missing = [k for k in NEEDED if k not in spec]
    if missing:
        raise SpecError("spec lacks %s" % ", ".join(missing))
    return spec, got


def check_scorer(path=SCORER_PATH, sha256=SCORER_SHA256):
    """the vendored reference scorer's sha256, when it is the pinned file; SpecError otherwise"""
    got = sha256_file(path)
    if got != sha256:
        raise SpecError("scorer sha256 %s is not the pinned %s" % (got, sha256))
    return got
