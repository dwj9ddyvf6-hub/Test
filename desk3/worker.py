"""Pool worker process. Long-lived; reads JSON-line tasks on stdin, writes
JSON-line results on stdout. Receives ONLY a snapshot file path + hash and
a ctx (cycle id, sleeve id, own state dir). Sleeve modules expose
evaluate(view, ctx) -> list[intent]. The snapshot is loaded once per hash
and reused — no per-sleeve cache files, no network needed at eval time.
The worker's environment is stripped by the pool (no credentials)."""
from __future__ import annotations
import dataclasses, importlib, json, os, sys


def _intent_dict(raw, sleeve_id, cycle_id, seq):
    """WORKER-EOF-20261026: normalize one evaluate() return value to
    the dispatcher's intent-dict contract. Dict intents pass through
    untouched (the overwhelmingly common shape). A dataclass Intent
    (desk3.contract.Intent — returned by desk3/aster_crypto, whose
    unit tests pin that object shape) is converted here, at the one
    boundary where the JSON contract is enforced: kind enter->entry,
    qty falls back to qty_hint, side falls back to the
    position_intent/kind default, and a deterministic per-cycle
    intent_id is stamped when the object carries none. Anything else
    raises, and the caller reports it as a sleeve error — the worker
    itself must never die on a result it cannot serialize."""
    if isinstance(raw, dict):
        return raw
    if dataclasses.is_dataclass(raw) and not isinstance(raw, type):
        d = dataclasses.asdict(raw)
        kind = {"enter": "entry", "entry": "entry",
                "exit": "exit"}.get(d.get("kind"))
        if kind is None or not d.get("symbol"):
            raise TypeError(f"unserializable_intent:{type(raw).__name__}")
        qty = d.get("qty") if d.get("qty") is not None else d.get("qty_hint")
        side = d.get("side") or {
            "buy_to_open": "buy", "buy_to_close": "buy",
            "sell_to_open": "sell", "sell_to_close": "sell"}.get(
                d.get("position_intent")) or ("sell" if kind == "exit"
                                              else "buy")
        out = {"intent_id": f"{sleeve_id}-{cycle_id}-{seq}",
               "kind": kind, "symbol": d["symbol"], "side": side,
               "qty": qty,
               "order_type": d.get("order_type") or (
                   "limit" if d.get("limit_price") else "market"),
               "limit_price": d.get("limit_price"),
               "stop_price": d.get("stop"),
               "reason": (d.get("reason") or kind)[:500],
               "time_in_force": d.get("time_in_force") or "day",
               "price_hint": d.get("price_hint")}
        if d.get("position_intent"):
            out["position_intent"] = d["position_intent"]
        # OVERNIGHT-AUCTION-20261116: the auction deadline rides
        # only when the sleeve declares it; no other sleeve's dict
        # gains the key.
        if d.get("auction_deadline_et"):
            out["auction_deadline_et"] = d["auction_deadline_et"]
        return out
    raise TypeError(f"unserializable_intent:{type(raw).__name__}")


def _normalize_intents(intents, sleeve_id, cycle_id):
    return [_intent_dict(r, sleeve_id, cycle_id, i + 1)
            for i, r in enumerate(intents)]


def _view_for_task(data, task):
    """CLEAR-THE-BOARD-20261114 (CR-S3): a task may carry a
    positions_override — the sleeve's OWN journal-derived positions,
    computed by the cycle (desk3.cycle.own_book_positions) for
    sleeves flagged own_book_view. The override is applied to a
    shallow copy: the cached snapshot data is shared by every sleeve
    in the pool and is never mutated, and a task without the key
    receives the snapshot itself, byte-identical to pre-cure."""
    override = task.get("positions_override")
    if override is None:
        return data
    view = dict(data)
    view["positions"] = override
    return view


def main():
    cache = {"hash": None, "data": None}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        task = json.loads(line)
        try:
            if cache["hash"] != task["snapshot_hash"]:
                with open(task["snapshot_path"]) as fh:
                    doc = json.load(fh)
                if doc["hash"] != task["snapshot_hash"]:
                    raise ValueError("snapshot_hash_mismatch")
                cache = {"hash": task["snapshot_hash"], "data": doc["data"]}
            mod = importlib.import_module(task["module"])
            ctx = dict(task["ctx"])
            os.makedirs(ctx["state_dir"], exist_ok=True)
            intents = mod.evaluate(_view_for_task(cache["data"], task),
                                   ctx) or []
            result = {"sleeve_id": task["sleeve_id"], "status": "ok",
                      "intents": _normalize_intents(
                          intents, task["sleeve_id"],
                          ctx.get("cycle_id") or "cycle")}
        except Exception as e:  # sleeve error: report, never kill the worker
            result = {"sleeve_id": task.get("sleeve_id"), "status": "error",
                      "error": f"{type(e).__name__}: {e}", "intents": []}
        # WORKER-EOF-20261026: serialization stays INSIDE the guard —
        # a result that still cannot be serialized degrades to a
        # named sleeve error, never a dead worker (the pool used to
        # see bare EOF and report 'worker_eof' with the cause lost).
        try:
            line_out = json.dumps(result)
        except Exception as e:
            line_out = json.dumps(
                {"sleeve_id": task.get("sleeve_id"), "status": "error",
                 "error": f"result_unserializable:{type(e).__name__}: {e}",
                 "intents": []})
        sys.stdout.write(line_out + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
