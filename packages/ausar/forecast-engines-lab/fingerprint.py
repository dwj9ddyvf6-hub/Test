"""Deterministic fingerprint for the exact forecast contract and scoring path."""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

from .catalog import EngineSpec


_CODE_COMPONENTS = (
    "contracts.py",
    "engine.py",
    "catalog.py",
    "edge_cards.py",
    "scorers.py",
    "target_contract.py",
    "label_context.py",
    "fingerprint.py",
)


@lru_cache(maxsize=None)
def engine_model_fingerprint(spec: EngineSpec) -> str:
    """Bind a forecast to its spec, validators, scoring and card code, and Python runtime.

    Source line endings are normalized so the same checked-in code has the same
    fingerprint on Windows and Unix. The hash is cached for the process lifetime;
    restart the process after deploying code changes. Feature-building transforms have a separate
    per-observation fingerprint in FeatureObservation.
    """
    package_dir = Path(__file__).resolve().parent
    components: dict[str, str] = {}
    for name in _CODE_COMPONENTS:
        source = package_dir.joinpath(name).read_text(encoding="utf-8")
        normalized = source.replace("\r\n", "\n").replace("\r", "\n")
        components[name] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    envelope = {
        "fingerprint_schema": "forecast-model-v1",
        "engine_spec": asdict(spec),
        "code_components": components,
        "python_runtime": {
            "implementation": sys.implementation.name,
            "version": list(sys.version_info[:3]),
        },
    }
    canonical = json.dumps(envelope, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
