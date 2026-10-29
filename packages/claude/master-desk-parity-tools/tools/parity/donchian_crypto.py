"""donchian_crypto: old donchian_crypto_sleeve.scan_pass, pass by pass, vs the restored port on the same tapes.

Random SOL-like 15m tapes (trend / chop / crash regimes, jumps, zero-volume bars). Every closed bar is one pass
(the old cron ran every 15 minutes, one minute after the close). The OLD pass runs its own scan_pass with the
broker simulated: market orders submitted in pass i fill before pass i+1 at bar i+1's open, list_orders and the
broker position reflect them, equity is fixed; the desk-wide gates (kill switch, Decision #75, 150% cap,
exposure ledger) proceed — the cutover doctrine. The port runs signal + next_symbol_state with the adapter's
state semantics (position_meta trail, the persisted "pos" override, the held / entry cleanup). Compared per
pass: the entry (qty, initial trail), the exit (reason, qty) and the ratcheted trail carried after the pass."""
import os
import random
from datetime import datetime, timezone

from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, write_receipt

F = femto_module("donchian_crypto")
N_TAPES = 14

OLD = r'''
import sys, types
import desk as _pkg
import donchian_crypto_sleeve as O


def mod(name, **fns):
    m = types.ModuleType("desk." + name)
    for k, v in fns.items():
        setattr(m, k, v)
    sys.modules["desk." + name] = m
    setattr(_pkg, name, m)


mod("desk_exposure", read_exposure=lambda: {}, holders_of=lambda *a, **k: [],
    clamp_exit_qty=lambda sym, q, sleeve=None: (q, ""), add_position=lambda *a, **k: None,
    remove_position=lambda *a, **k: None, assert_cap_or_block=lambda *a, **k: (True, 0.0, 0.0, ""))
mod("decision75", pre_buy=lambda *a, **k: "proceed", sweep_releases=lambda *a, **k: [])
O.check_kill_switch = lambda sym: True
O._cap_gate_entry = lambda sym, notional, equity: True
O.replay_chart_gate_releases = lambda state, now_utc, equity=None: None
O.adopt_working_orders = lambda state, now_utc: None
from datetime import datetime, timezone
out = []
for tape in PAYLOAD["tapes"]:
    bars = tape["bars"]
    STATE = {}
    LOG = []
    ORDERS = []
    BROKER = {"qty": 0.0}
    O.load_state = lambda STATE=STATE: STATE
    O.save_state = lambda s: None
    O.log = lambda e, LOG=LOG: LOG.append(dict(e))
    O.get_equity = lambda tape=tape: tape["equity"]
    O.broker_position_qty = lambda sym, BROKER=BROKER: BROKER["qty"]
    I = [0]

    def run_cli(script, args, timeout=None, ORDERS=ORDERS):
        if script == "alpaca_list_orders.py":
            return [] if "open" in args else list(ORDERS)
        raise RuntimeError(script)
    O.desk.run_cli = run_cli

    def submit(args, timeout=120, ORDERS=ORDERS):
        a = dict(zip(args[0::2], args[1::2]))
        ORDERS.append({"client_order_id": a["--client-order-id"], "side": a["--side"], "qty": float(a["--qty"]),
                       "status": "new", "filled_qty": 0, "filled_avg_price": None})
        return {"id": "o%d" % len(ORDERS), "status": "accepted"}
    O.submit = submit
    O.fetch_15m_bars = lambda limit=120, bars=bars, I=I: [dict(b) for b in bars[max(0, I[0] + 1 - limit):I[0] + 1]]
    passes = []
    for i in range(tape["first"], len(bars)):
        I[0] = i
        n0 = len(LOG)
        k0 = len(ORDERS)
        O.scan_pass(datetime.fromtimestamp(datetime.fromisoformat(bars[i]["t"]).timestamp() + 960, tz=timezone.utc))
        ev = [e for e in LOG[n0:] if e.get("event") in ("entry_submitted", "exit_submitted")]
        st = STATE.get("SOLUSD") or {}
        pend = st.get("pending_entry") or {}
        pos = st.get("position") or {}
        passes.append({"i": i, "entry": [[e["qty"], pend.get("trail_init")] for e in ev if e["event"] == "entry_submitted"],
                       "exit": [[e["reason"], e["qty"]] for e in ev if e["event"] == "exit_submitted"],
                       "trail": pos.get("trail")})
        # the broker fills this pass's market orders at the next bar's open
        nxt = bars[i + 1]["o"] if i + 1 < len(bars) else bars[i]["c"]
        for o in ORDERS[k0:]:
            o.update(status="filled", filled_qty=o["qty"], filled_avg_price=nxt)
            BROKER["qty"] += o["qty"] if o["side"] == "buy" else -o["qty"]
    out.append(passes)
print(json.dumps(out))
'''


def _tape(rnd, n, start="2026-03-02T00:00:00+00:00"):
    t0 = datetime.fromisoformat(start).timestamp()
    px = rnd.uniform(60, 240)
    rows = []
    regime, left = 0.0, 0
    for i in range(n):
        if left <= 0:
            regime = rnd.choice((0.0018, 0.0010, 0.0, 0.0, -0.0010, -0.0025))
            left = rnd.randint(20, 160)
        left -= 1
        sd = rnd.choice((0.003, 0.005, 0.008))
        o = px * (1 + rnd.gauss(0, sd / 4))
        c = max(1.0, px * (1 + rnd.gauss(regime, sd) + (rnd.choice((-1, 1)) * rnd.uniform(0.02, 0.06)
                                                       if rnd.random() < 0.006 else 0)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, sd / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, sd / 2)))
        v = 0.0 if rnd.random() < 0.01 else round(rnd.uniform(50, 5000), 3)
        t = datetime.fromtimestamp(t0 + i * 900, tz=timezone.utc).isoformat()
        rows.append({"t": t, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4), "v": v})
        px = c
    return rows


def _new_side(tape):
    """the port under the adapter's state semantics, fills at the next bar's open."""
    bars = [dict(b, t=datetime.fromisoformat(b["t"]).timestamp()) for b in tape["bars"]]
    pos, syms, passes = None, {}, []
    for i in range(tape["first"], len(bars)):
        bl = bars[max(0, i + 1 - 120):i + 1]
        st = {k: v for k, v in syms.get("SOLUSD", {}).items()}
        view_pos = None
        if pos is not None:
            view_pos = dict(pos["meta"])
            view_pos.update(qty=pos["qty"], entry_px=pos["entry_px"], exit_submitted=None)
            view_pos.update(st.pop("pos", None) or {})
        else:
            st.pop("pos", None)
        ctx = fc.Context(now=bars[i]["t"] + 960, session="", equity=tape["equity"],
                         extra={"sleeve_state": {"SOLUSD": dict(st, position=view_pos)}})
        out = F.signal({"SOLUSD": bl}, {}, ctx)
        held = pos is not None
        if "pos" in syms.get("SOLUSD", {}) and not held and not any(x.kind == "enter" for x in out):
            syms["SOLUSD"] = {k: v for k, v in syms["SOLUSD"].items() if k != "pos"}
        nss = getattr(F, "next_symbol_state", None)          # absent in the as-vendored femto port
        for sym, d in ((nss({"SOLUSD": bl}, {}, ctx, out) if nss else None) or {}).items():
            syms[sym] = dict(syms.get(sym) or {}, **d)
        rec = {"i": i, "entry": [], "exit": [], "trail": None}
        nxt = bars[i + 1]["o"] if i + 1 < len(bars) else bars[i]["c"]
        for x in out:
            if x.kind == "enter":
                rec["entry"].append([x.qty, (x.position_meta or {}).get("trail")])
            elif x.kind == "exit":
                rec["exit"].append([x.reason.split(": ", 1)[1].split(" ", 1)[0], x.qty])
        if held:
            rec["trail"] = ((syms.get("SOLUSD") or {}).get("pos") or {}).get("trail")
        passes.append(rec)
        for x in out:
            if x.kind == "enter":
                pos = {"qty": x.qty, "entry_px": nxt, "meta": dict(x.position_meta or {})}
            elif x.kind == "exit":
                pos = None
    return passes


def run():
    rnd = random.Random(15)
    tapes = []
    for k in range(N_TAPES):
        n = rnd.randint(700, 1400)
        tapes.append({"bars": _tape(rnd, n), "first": rnd.randint(30, 130),
                      "equity": rnd.choice((2_000.0, 25_000.0, 100_000.0, 1_000_000.0))})
    old = old_run(OLD, {"tapes": tapes}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"passes": 0, "entries": 0, "exits": {}}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ti, (tape, o) in enumerate(zip(tapes, old)):
        new = _new_side(tape)
        cmp("n_passes", ti, len(o), len(new))
        for po, pn in zip(o, new):
            ref = [ti, po["i"]]
            cmp("entry", ref, po["entry"], pn["entry"])
            cmp("exit", ref, po["exit"], pn["exit"])
            cmp("trail", ref, po["trail"], pn["trail"])
            counts["passes"] += 1
            counts["entries"] += len(po["entry"])
            for r, _q in po["exit"]:
                counts["exits"][r] = counts["exits"].get(r, 0) + 1
    res = {"sleeve": "donchian_crypto", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("donchian_crypto" + ("@" + os.environ["FEMTO_REF"] if os.environ.get("FEMTO_REF") else ""), res)
    return res
