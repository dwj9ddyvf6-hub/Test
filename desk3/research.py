"""Research lane (RES-1): new strategy ideas are tried out in shadow —
they read the same market information as the live strategies and record
what they WOULD have done, but they are built so they cannot place an
order. Isolation is by construction:

* a candidate receives a ShadowContext exposing only a frozen view of
  the market data and emit_signal(); there is no route to the order
  path — touching dispatch/broker/submit attributes raises
  ShadowBoundaryError, and the attempt is written to the candidate's
  own journal as blocked_order_attempt;
* emitted signals are stamped can_be_ordered=False and shadow=True;
* candidates write only under state/research/<candidate id>/;
* evaluation NEVER changes the registry or the trading roster.
  Promotion is an explicit move: promote_candidate() flips the
  registry status and logs it in candidates/PROMOTIONS.md; joining
  the trading roster is then a separate, manual roster edit + commit
  (see candidates/README.md). Nothing promotes automatically."""
from __future__ import annotations
import importlib.util, json, os
from datetime import datetime, timezone
from .journal import append_line
from .snapshot import _freeze

_BLOCKED = ("dispatch", "dispatcher", "broker", "door", "submit",
            "submit_order", "place_order", "order", "buy", "sell")


class ShadowBoundaryError(Exception):
    pass


class ShadowContext:
    def __init__(self, candidate_id):
        object.__setattr__(self, "_candidate_id", candidate_id)
        object.__setattr__(self, "_signals", [])

    def emit_signal(self, signal):
        row = dict(signal)
        row.update({"candidate": self._candidate_id, "shadow": True,
                    "can_be_ordered": False})
        self._signals.append(row)
        return row

    @property
    def signals(self):
        return list(self._signals)

    def __getattr__(self, name):
        if name in _BLOCKED or name.startswith("dispatch") or name.startswith("submit"):
            raise ShadowBoundaryError(
                f"shadow candidate cannot reach {name!r}: no order path exists here")
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in _BLOCKED:
            raise ShadowBoundaryError(f"shadow candidate cannot set {name!r}")
        object.__setattr__(self, name, value)


def _journal_path(state_root, candidate_id):
    base = os.path.join(os.path.abspath(state_root), "research")
    path = os.path.join(base, candidate_id, "journal.jsonl")
    if os.path.commonpath([base, os.path.abspath(path)]) != base or candidate_id in ("", ".", ".."):
        raise ShadowBoundaryError(f"journal path escapes the research space: {candidate_id!r}")
    return path


def load_registry(registry_path):
    with open(registry_path) as fh:
        return json.load(fh)


def _load_module(candidates_dir, module_name):
    path = os.path.join(candidates_dir, module_name + ".py")
    spec = importlib.util.spec_from_file_location(f"candidate_{module_name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evaluate_candidates(snapshot_data, registry_path, state_root, candidates_dir):
    """Run every shadow candidate once against the market view. Returns
    {candidate_id: {status, signals}}. Writes only each candidate's own
    journal. The registry file and the trading roster are never touched."""
    doc = load_registry(registry_path)
    view = _freeze(dict(snapshot_data))
    results = {}
    for cand in doc.get("candidates", []):
        cid = cand["id"]
        if cand.get("status") != "shadow":
            results[cid] = {"status": "skipped_not_shadow", "signals": 0}
            continue
        journal = _journal_path(state_root, cid)
        ctx = ShadowContext(cid)
        ts = datetime.now(timezone.utc).isoformat()
        try:
            mod = _load_module(candidates_dir, cand["module"])
            returned = mod.evaluate(view, ctx) or []
            signals = ctx.signals + [dict(s, candidate=cid, shadow=True,
                                          can_be_ordered=False)
                                     for s in returned if isinstance(s, dict)
                                     and "candidate" not in s]
            for sig in signals:
                append_line(journal, {"event": "shadow_signal", "ts": ts, **sig})
            append_line(journal, {"event": "evaluation", "ts": ts,
                                  "status": "ok", "signals": len(signals)})
            results[cid] = {"status": "ok", "signals": len(signals)}
        except ShadowBoundaryError as e:
            append_line(journal, {"event": "blocked_order_attempt", "ts": ts,
                                  "detail": str(e)})
            results[cid] = {"status": "blocked_order_attempt", "signals": 0}
        except Exception as e:  # a broken idea is recorded, never fatal
            append_line(journal, {"event": "evaluation", "ts": ts,
                                  "status": "error",
                                  "detail": f"{type(e).__name__}: {e}"})
            results[cid] = {"status": "error", "signals": 0}
    return results


def promote_candidate(registry_path, candidate_id, log_path):
    """The ONLY promotion route: an explicit registry move + a line in
    the promotions log. Deliberately does not touch the trading roster —
    adding the strategy there is a separate manual edit and commit."""
    doc = load_registry(registry_path)
    hit = None
    for cand in doc.get("candidates", []):
        if cand["id"] == candidate_id:
            hit = cand
    if hit is None:
        raise KeyError(f"unknown candidate: {candidate_id}")
    if hit.get("status") != "shadow":
        raise ValueError(f"candidate {candidate_id} is not in shadow (status={hit.get('status')})")
    ts = datetime.now(timezone.utc).isoformat()
    hit["status"] = "promoted"
    hit["promoted_at"] = ts
    tmp = registry_path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    os.replace(tmp, registry_path)
    with open(log_path, "a") as fh:
        fh.write(f"- {ts} — {candidate_id} promoted from shadow. "
                 f"Next step (manual): add its row to the trading roster "
                 f"and commit both changes together.\n")
    return hit
