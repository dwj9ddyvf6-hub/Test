"""Desk terminal feed (TERM-1): one plain-language JSON feed per cycle,
written atomically for the static page in terminal/. Reader prose only —
statuses are words a person uses, never desk shorthand. Machine fields
(generated_at, cycle_id) ride alongside so freshness is provable by
read-back: generated_at and cycle_id advance every cycle."""
from __future__ import annotations
import json, os

_STATUS = {"FED_ok": "Ready", "UNFED": "Waiting for data",
           "PARKED": "Paused"}

# EVIDENCE-PACKET-20261031: the engine that builds every number on
# this feed. Published on the feed itself (top-level engine_version
# and inside the evidence packet) so a reader can always name the
# provenance of a figure, never a blanket claim.
ENGINE_VERSION = "desk3-terminal-1"


def build_evidence_packet(roll, total_orders, account=None,
                          account_error=None, capital_epoch=None,
                          capital_epoch_error=None,
                          engine_version=None,
                          trade_count_scope=
                          "orders_placed_in_reported_cycle"):
    """The packet that must travel with every published number
    (quants.md evidence-packet form): period, starting capital,
    engine version, trade count and self-check flags, with failures
    visible even when they fail. Fields the desk does not hold are
    None and flagged absent in self_check/failures, never filled
    with a carried or invented figure. No number is computed here:
    the packet only joins material other code already produced
    (the roll's own counts, the broker account read, and
    state/capital_epoch.json as read by the cycle)."""
    epoch = capital_epoch if isinstance(capital_epoch, dict) else None
    producer_errors = roll.get("producer_errors") or {}
    failures = []
    if epoch is None:
        failures.append("capital_epoch_missing: period start and "
                        "starting capital are not published")
    if capital_epoch_error:
        failures.append(f"capital_epoch_read_failed:{capital_epoch_error}")
    if account_error:
        failures.append(f"account_read_failed:{account_error}")
    for name in sorted(producer_errors):
        failures.append(f"producer_error:{name}:{producer_errors[name]}")
    if not roll.get("snapshot_hash"):
        failures.append("snapshot_hash_missing")
    start_equity = epoch.get("start_equity") if epoch else None
    return {
        "period": {"start": epoch.get("epoch_start_utc") if epoch else None,
                   "end": roll.get("generated_at"),
                   "basis": "capital_epoch_start_to_feed_generation"},
        "starting_capital": (float(start_equity)
                             if isinstance(start_equity, (int, float))
                             else None),
        "benchmarks": list(epoch.get("benchmarks") or []) if epoch else [],
        "engine_version": engine_version or ENGINE_VERSION,
        "trade_count": int(total_orders),
        "trade_count_scope": trade_count_scope,
        "self_check": {
            "capital_epoch_present": epoch is not None,
            "starting_capital_present": isinstance(
                start_equity, (int, float)),
            "period_start_present": bool(
                epoch and epoch.get("epoch_start_utc")),
            "snapshot_hash_present": bool(roll.get("snapshot_hash")),
            "snapshot_hash": roll.get("snapshot_hash"),
            "producer_errors": dict(producer_errors),
            "producer_errors_present": bool(producer_errors),
            "account_present": account is not None,
            "account_error": account_error,
            "account_read_failed": bool(account_error),
        },
        "failures": failures,
    }


def sleeve_family(sleeve_id):
    """Derived grouping (SLEEVE-SURFACE-20261031): config declares no
    book/family per sleeve, so the group is the deterministic first
    token of the id, labelled derived wherever it is shown."""
    return str(sleeve_id).split("_", 1)[0] or str(sleeve_id)


def cadence_label(cadence_s):
    try:
        s = int(cadence_s)
    except (TypeError, ValueError):
        return None
    if s % 86400 == 0:
        return "daily" if s == 86400 else f"every {s // 86400} days"
    if s % 3600 == 0:
        return "hourly" if s == 3600 else f"every {s // 3600} hours"
    if s % 60 == 0:
        return "every minute" if s == 60 else f"every {s // 60} minutes"
    return f"every {s} seconds"


def declared_instrument(inputs, symbol=None):
    """Only a declared instrument: params.symbol, else an explicit
    bars:<SYM>:<TF> input (wildcard bars:* is not an instrument)."""
    if symbol:
        return str(symbol)
    for item in inputs or []:
        parts = str(item).split(":")
        if len(parts) == 3 and parts[0] == "bars" and parts[1] not in ("", "*"):
            return f"{parts[1]} ({parts[2]})"
    return None


def _status_for(entry, parked):
    if parked:
        return "Paused"
    if entry.get("state") == "UNFED":
        return "Waiting for data"
    if entry.get("status") in ("error", "wedged") or entry.get("verdict") == "wedged":
        return "Needs attention"
    return "Ready"


def _last_action(entry, status):
    if status == "Paused":
        return "Paused — not trading right now"
    if status == "Waiting for data":
        missing = ", ".join(entry.get("missing") or entry.get("stale") or [])
        return "Waiting for fresh market information" + (f" ({missing})" if missing else "")
    if status == "Needs attention":
        return "Hit a problem on its last check — see the desk log"
    if entry.get("orders_placed"):
        return "Placed an order on its last check"
    return "Checked the market — no trade"


def build_feed(roll, sleeve_meta, positions=None, account=None,
               account_error=None, capital_epoch=None,
               capital_epoch_error=None, engine_version=None):
    """sleeve_meta: {id: {slice_usd, parked}}; positions: either the
    per-sleeve dict {id: [pos,...]} or the canonical snapshot shape
    (POS-SHAPE-20261026): a flat LIST of {symbol, qty, avg_price}
    account-level records with no sleeve attribution. The list shape
    is counted and carried as account_positions — never fabricated
    into per-sleeve attribution (TERMINAL-POSITIONS-SHAPE-20261027:
    the list used to be discarded upstream, so the live feed
    reported 0 open positions every cycle)."""
    account_positions = []
    if isinstance(positions, list):
        account_positions = list(positions)
        positions = {}
    positions = positions or {}
    rows, counts = [], {"Ready": 0, "Waiting for data": 0, "Paused": 0,
                        "Needs attention": 0}
    total_positions = len(account_positions)
    total_orders = 0
    _session_orders, _session_seen = 0, False
    for sid in sorted(roll.get("sleeves", {})):
        entry = roll["sleeves"][sid]
        meta = sleeve_meta.get(sid, {})
        status = _status_for(entry, bool(meta.get("parked")))
        counts[status] += 1
        pos = list(positions.get(sid, []))
        total_positions += len(pos)
        total_orders += int(entry.get("orders_placed", 0))
        # HEALTH-ORDERS-PLACED-20261116: the session-cumulative
        # figure rides the feed beside the per-cycle one when the
        # roll carries it (additive; a roll without it keeps the
        # pre-cure feed shape exactly).
        if "orders_placed_session" in entry:
            _session_orders += int(entry.get("orders_placed_session")
                                   or 0)
            _session_seen = True
        row = {"name": sid, "status": status,
               "money_assigned": float(meta.get("slice_usd", 0.0)),
               "open_positions": pos,
               "last_action": _last_action(entry, status),
               # SLEEVE-SURFACE-20261031: per-sleeve expression.
               "family": sleeve_family(sid),
               "family_source": "derived_from_id",
               "feed_state": {"FED": "Data arriving",
                              "UNFED": "Data missing",
                              "PARKED": "Paused"}.get(entry.get("state")),
               "missing": list(entry.get("missing") or []),
               "stale": list(entry.get("stale") or []),
               "orders_placed": int(entry.get("orders_placed", 0))}
        if "orders_placed_session" in entry:
            row["orders_placed_session"] = int(
                entry.get("orders_placed_session") or 0)
        if meta.get("cadence_s") is not None:
            row["cadence_s"] = int(meta["cadence_s"])
            label = cadence_label(meta["cadence_s"])
            if label:
                row["cadence_label"] = label
        if meta.get("session"):
            row["session"] = meta["session"]
        if meta.get("inputs"):
            row["inputs"] = list(meta["inputs"])
        instrument = declared_instrument(meta.get("inputs"),
                                         meta.get("symbol"))
        if instrument:
            row["instrument"] = instrument
        if meta.get("declared_family"):
            row["declared_family"] = meta["declared_family"]
        if meta.get("parked_reason"):
            row["parked_reason"] = meta["parked_reason"]
        rows.append(row)
    total = len(rows)
    groups = {}
    for r in rows:
        g = groups.setdefault(r["family"], {"family": r["family"],
            "total": 0, "ready": 0, "waiting_for_data": 0, "paused": 0,
            "needs_attention": 0})
        g["total"] += 1
        key = {"Ready": "ready", "Waiting for data": "waiting_for_data",
               "Paused": "paused",
               "Needs attention": "needs_attention"}[r["status"]]
        g[key] += 1
    sleeve_groups = [groups[k] for k in sorted(groups)]
    summary = {"strategies_total": total, "ready": counts["Ready"],
               "waiting_for_data": counts["Waiting for data"],
               "paused": counts["Paused"],
               "needs_attention": counts["Needs attention"],
               "orders_placed": total_orders,
               "open_positions": total_positions,
               "money_assigned_total": round(sum(r["money_assigned"] for r in rows), 2)}
    if _session_seen:
        summary["orders_placed_session"] = _session_orders
    headline = (f"{counts['Ready']} of {total} strategies are ready. "
                f"{total_orders} order(s) placed on the last check, "
                f"{total_positions} position(s) open.")
    if counts["Waiting for data"]:
        headline += f" {counts['Waiting for data']} waiting for data."
    if counts["Needs attention"]:
        headline += f" {counts['Needs attention']} need attention."
    # FEED-EQUITY-20261031: the account block carries the broker
    # account record the cycle read (equity, cash, buying power,
    # last equity, status), so a consumer such as Friday grading
    # can certify the desk week from the feed alone. When the
    # cycle could not read the account, the block is None and the
    # failure is named in account_error: absent equity is an
    # honest gap, never a carried or invented figure.
    # EVIDENCE-PACKET-20261031: every published number on this feed
    # ships with its packet (period, starting capital, engine
    # version, trade count, self-check flags; failures visible).
    # HEALTH-ORDERS-PLACED-20261116: when the roll carries the
    # session figure, the packet's trade count is the session's
    # orders placed and its scope says so; a roll without it
    # keeps the pre-cure per-cycle count and scope exactly.
    packet = build_evidence_packet(
        roll, _session_orders if _session_seen else total_orders,
        account=account,
        account_error=account_error, capital_epoch=capital_epoch,
        capital_epoch_error=capital_epoch_error,
        engine_version=engine_version,
        trade_count_scope=("orders_placed_session_in_reported_session"
                           if _session_seen else
                           "orders_placed_in_reported_cycle"))
    feed = {"generated_at": roll.get("generated_at"),
            "cycle_id": roll.get("cycle_id"), "headline": headline,
            "summary": summary, "strategies": rows,
            "sleeve_groups": sleeve_groups,
            "account_positions": account_positions,
            "account": account,
            "engine_version": packet["engine_version"],
            "evidence_packet": packet}
    if account_error:
        feed["account_error"] = account_error
    return feed


def write_feed(feed, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(feed, fh, sort_keys=True, indent=1)
    os.replace(tmp, path)
    return path


def read_feed(path):
    with open(path) as fh:
        return json.load(fh)
