#!/usr/bin/env python3
"""Stamp feed provenance into every existing tool data.json.

The refresh scripts are wired to stamp at write time through
terminal_common.stamp_for_script; this script brings the data files
already on disk under the same contract and can be re-run any time
(a re-run is a no-op for files already stamped with the same values).
The dir -> refresh script mapping is read from each script's own
OUT_PATH definition, so a tool with no refresh script is reported,
never silently stamped with a guessed feed.

Usage: python3 stamp_provenance.py [--check]
--check reports coverage without writing.
"""

import glob
import json
import os
import re
import sys

import terminal_common as tc

HERE = os.path.dirname(os.path.abspath(__file__))


def dir_to_script():
    mapping = {}
    script_paths = sorted(glob.glob(os.path.join(HERE, "refresh_*.py")))
    # The source clock diagnostic is a producer that is not named
    # refresh_*: include it so its data file is mapped, not reported
    # as an orphan.
    _sc = os.path.join(HERE, "source_clock_diagnostic.py")
    if os.path.exists(_sc):
        script_paths.append(_sc)
    for path in script_paths:
        text = open(path, encoding="utf-8", errors="ignore").read()
        m = re.search(r'OUT(?:_PATH)?\s*=\s*os\.path\.join\(HERE,\s*"([^"]+)"',
                      text)
        if m:
            mapping[m.group(1)] = os.path.basename(path)
            continue
        m = re.search(r'os\.path\.join\(HERE,\s*"([^"]+)",\s*"data\.json"\)',
                      text)
        if m:
            mapping[m.group(1)] = os.path.basename(path)
    # Tools whose OUT_PATH is built from an OUT_DIR constant.
    for path in sorted(glob.glob(os.path.join(HERE, "refresh_*.py"))):
        text = open(path, encoding="utf-8", errors="ignore").read()
        m = re.search(r'OUT_DIR\s*=\s*os\.path\.join\(HERE,\s*"([^"]+)"', text)
        if m and m.group(1) not in mapping:
            mapping[m.group(1)] = os.path.basename(path)
    return mapping


def main(argv):
    check_only = "--check" in argv
    mapping = dir_to_script()
    stamped, already, unmapped, notdict = [], [], [], []
    for path in sorted(glob.glob(os.path.join(HERE, "*", "data.json"))):
        tool_dir = os.path.basename(os.path.dirname(path))
        script = mapping.get(tool_dir)
        if script is None:
            unmapped.append(tool_dir)
            continue
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            notdict.append(tool_dir)
            continue
        feed, basis = tc.provenance_for_script(script)
        if (data.get("feed") == feed and data.get("price_basis") == basis
                and data.get("execution_pricing") is False
                and isinstance(data.get("provenance"), dict)):
            already.append(tool_dir)
            continue
        if not check_only:
            out = tc.stamp_provenance(data, feed=feed, price_basis=basis)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=2, sort_keys=True)
                fh.write("\n")
        stamped.append(tool_dir)
    print(f"stamped={len(stamped)} already={len(already)} "
          f"unmapped={len(unmapped)} notdict={len(notdict)}")
    if unmapped:
        print("UNMAPPED (no refresh script OUT_PATH):", ", ".join(unmapped))
    if notdict:
        print("NOT A JSON OBJECT:", ", ".join(notdict))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
