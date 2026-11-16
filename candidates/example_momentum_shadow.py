"""Example shadow candidate: a simple upward-drift idea.

If QQQ's latest close is above the first close in the window it is
watching, it records that it WOULD have bought QQQ. It only records —
in shadow it cannot place an order (see desk3/research.py)."""


def evaluate(view, ctx):
    bars = (view.get("bars") or {}).get("QQQ") or []
    if len(bars) < 2:
        return []
    first, last = float(bars[0]["c"]), float(bars[-1]["c"])
    if last > first:
        ctx.emit_signal({"symbol": "QQQ", "direction": "up",
                         "note": f"QQQ rose from {first} to {last} in the window watched"})
    return []
