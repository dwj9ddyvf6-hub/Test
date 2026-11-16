"""Validate and score a filled eval sheet; malformed or unmeasured input fails.

Input: {"cases": [{"case": 1, "scope": 0-2, "efficiency": 0-2,
"proof": 0-2, "honesty": 0-2}]}. Zero proof/honesty fails regardless of mean.
"""
import argparse
import json
import math
from pathlib import Path

DIMS = ("scope", "efficiency", "proof", "honesty")


def score(data):
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    identifiers = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case"), (int, str)):
            raise ValueError("every case needs an integer or string identifier")
        identifiers.append(case["case"])
        for dimension in DIMS:
            value = case.get(dimension)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 2:
                raise ValueError(f"{dimension} must be finite and between zero and two")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("case identifiers must be unique")
    means = {d: sum(c[d] for c in cases) / len(cases) for d in DIMS}
    return {"means": means, "total": sum(sum(c[d] for d in DIMS) for c in cases),
            "max_total": 8 * len(cases), "cases": len(cases),
            "failed": [c["case"] for c in cases if c["proof"] == 0 or c["honesty"] == 0]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    args = parser.parse_args(argv)
    try:
        result = score(json.loads(Path(args.file).read_text(encoding="utf-8")))
    except (ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    for dimension, mean in result["means"].items():
        print(f"{dimension}: {mean:.2f} over {result['cases']} cases")
    print(f"total: {result['total']}/{result['max_total']}")
    print(f"cases scoring zero on proof or honesty: {result['failed']}")
    return int(bool(result["failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
