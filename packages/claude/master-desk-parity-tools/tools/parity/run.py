"""python3 -m tools.parity.run <sleeve> [<sleeve> ...]  — run parity harnesses, write receipts, exit 1 on any diff."""
import importlib
import json
import sys


def main(argv):
    bad = 0
    for name in argv or []:
        mod = importlib.import_module("tools.parity." + name)
        res = mod.run()
        print(json.dumps({k: res[k] for k in ("sleeve", "cases", "identical", "diffs")}, default=str)[:2000])
        bad += 1 if res["diffs"] else 0
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
