"""python -m desk.ai <tool> [--args JSON] [--offline] [--root DIR]   (python -m desk.ai list: every tool)

Prints one contract envelope as JSON and appends it to the session log state/ai/session-<snapshot_id>.jsonl, which
the grounding gate reads (`python -m desk.ai ground --args '{"text": "...", "session": true}'`).
"""
import argparse
import json
import os
import sys

from . import dumps, names, run
from .source import Source, ai_dir


def _log(root, env):
    if not env.get("snapshot_id"):
        return
    d = ai_dir(root)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"session-{env['snapshot_id']}.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(env, ensure_ascii=False) + "\n")


def _session(root):
    from . import snapshot_id
    ed, _, _ = Source(root=root).edition()
    p = os.path.join(ai_dir(root), f"session-{snapshot_id(ed)}.jsonl") if ed else None
    if not p or not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m desk.ai")
    ap.add_argument("tool")
    ap.add_argument("--args", default="{}")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    if a.tool == "list":
        print("\n".join(names()))
        return 0
    try:
        args = json.loads(a.args)
    except ValueError as e:
        print(json.dumps({"status": "no_data", "reason": f"--args is not JSON: {e}"}))
        return 2
    root = a.root or os.environ.get("DESK_ROOT") or os.getcwd()
    if a.tool == "ground" and args.pop("session", False):
        args["outputs"] = _session(root)
    env = run(a.tool, args, source=Source(root=root, offline=a.offline or None))
    if a.tool != "ground":
        _log(root, env)
    print(dumps(env))
    return 0 if env["status"] != "no_data" else 1


if __name__ == "__main__":
    sys.exit(main())
