"""The desk AI's tool layer: deterministic desk tools behind one contract, so a Claude session on the host can act as
the desk's analyst without ever typing a number of its own (docs/AI.md).

Every tool returns the same envelope (CONTRACT): what was asked, the snapshot it was answered from, when the data is
from, whether the bars behind it are closed, its sources, the data's age, a status (ok / stale / no_data) with a named
reason, and the result. A tool that cannot answer says no_data and why; it never guesses (study I, failure taxonomy).

Slots name tools that sibling builds provide (odds, catalysts, the market strip, the record line). Each resolves by
import name when its module lands; until then it answers no_data, reason "not built yet".
"""
import hashlib
import importlib
import json
import time

CONTRACT = ("tool", "args", "snapshot_id", "as_of", "bar_closed", "sources", "data_age_s", "status", "reason", "result")
STATUSES = ("ok", "stale", "no_data")
STALE_S = 36 * 3600            # an edition older than a day and a half is stale (a weekend's edition is not)

TOOLS = {}
# slot name -> candidate (module, function) pairs, tried in order; the first importable one answers
SLOTS = {}          # a sibling build may still register a tool by import name here: name -> [(module, function)]


def tool(name):
    def wrap(fn):
        TOOLS[name] = fn
        return fn
    return wrap


def envelope(name, args, snap, status="ok", reason="", result=None, sources=(), as_of=None, bar_closed=True,
             data_age_s=None):
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if status != "ok" and not reason:
        raise ValueError("a status other than ok needs a named reason")
    return {"tool": name, "args": args or {}, "snapshot_id": snap, "as_of": as_of, "bar_closed": bool(bar_closed),
            "sources": list(sources), "data_age_s": data_age_s, "status": status, "reason": reason,
            "result": result}


def snapshot_id(edition):
    """one immutable id per edition: every tool answer carries the snapshot it was read from"""
    key = "|".join(str((edition or {}).get(k)) for k in ("schema", "seq", "edition", "generated_at"))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def resolve_slot(name):
    for mod, fn in SLOTS.get(name, []):
        try:
            f = getattr(importlib.import_module(mod), fn, None)
        except ImportError:
            continue
        if callable(f):
            return f
    return None


def names():
    from . import tools  # noqa: F401
    return sorted(set(TOOLS) | set(SLOTS))


def run(name, args=None, source=None, now=None):
    """answer one tool call in the contract; never raises for a desk-side failure (it becomes no_data + reason)"""
    from . import source as srcmod, tools  # noqa: F401  (tools registers itself)
    args = dict(args or {})
    src = source or srcmod.Source()
    now = time.time() if now is None else float(now)
    ed, where, err = src.edition()
    snap = snapshot_id(ed) if ed else None
    if args.get("snapshot_id") and snap and args["snapshot_id"] != snap:
        return envelope(name, args, snap, "stale", f"snapshot moved: asked {args['snapshot_id']}, now {snap}")
    if name in TOOLS:
        fn = TOOLS[name]
    elif name in SLOTS:
        f = resolve_slot(name)
        if f is None:
            return envelope(name, args, snap, "no_data", "not built yet")
        fn = lambda a, ctx: tools.slot_call(f, a, ctx)                       # noqa: E731
    else:
        return envelope(name, args, snap, "no_data", f"unknown tool; known: {', '.join(names())}")
    if ed is None and name not in ("risk_gate", "consistency_gate", "ground"):
        return envelope(name, args, None, "no_data", f"no edition: {err}")
    ctx = {"edition": ed, "where": where, "source": src, "now": now, "snapshot_id": snap}
    try:
        out = fn(args, ctx)
    except (KeyError, ValueError, TypeError, OSError) as e:
        return envelope(name, args, snap, "no_data", f"{type(e).__name__}: {e}"[:300])
    env = envelope(name, args, snap, out.get("status", "ok"), out.get("reason", ""), out.get("result"),
                   out.get("sources") or [where], out.get("as_of") or (ed or {}).get("market", {}).get("as_of"),
                   out.get("bar_closed", True), _age(ed, now))
    if env["status"] == "ok" and env["data_age_s"] is not None and env["data_age_s"] > STALE_S \
            and not out.get("timeless"):
        env["status"], env["reason"] = "stale", f"edition is {int(env['data_age_s'] // 3600)} h old"
    return env


def _age(ed, now):
    from datetime import datetime
    try:
        return round(now - datetime.fromisoformat(ed["generated_at"]).timestamp())
    except (KeyError, TypeError, ValueError):
        return None


def dumps(env):
    return json.dumps(env, ensure_ascii=False, indent=1, sort_keys=False)
