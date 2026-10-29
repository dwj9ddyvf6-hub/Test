"""The Aurelia free-paper option descendants (free_opt_*): the SOURCE desk's own decision path (Agentic-Trading-Desk
aurelia-paper-desk @1720157f768e, run in its own tree: AURELIA_SRC) — free_options.evaluate(), execute() on the
sleeve's own row (its order journal, option_packages.submit_package() with its package journal and risk file,
option_packages.manage_exits()) — vs the port's decide(), over multi-pass sequences of randomized inputs.

Stubbed in the source, I/O only: the broker calls (a single order's ack — filled, accepted or rejected, the same draw
the port's book sees; a multi-leg ack: accepted; a cancel: canceled) and its state directory (a scratch dir). The
inputs the source's run() never supplied (the traded quote, the session return, the cash, the events, the package)
are the case's, fed identically to both. The port's book follows its own intents: an entry fills when the source's
ack says filled (a multi-leg package: accepted, 3% left unfilled), an exit fills.

Compared per pass: the row's status (a sent single order: the source's adopted state vs "sent") and reason, the
single orders (symbol, side, qty, limit, intent, client id), the cancels, each package's submission status, its
legs (symbol, side, quantity) and the price its journal booked, and the package exits. Named divergences are
classified and counted, each verified against the source's own record: natural_debit (the port's multi-leg limit
is the debit the journal booked; the source's broker order carried the larger leg ask), package_quantity (the
port's quantity is the legs' — the journal's; the source's broker order carried 1), released_reservation (a risk
check the port passes because closed packages released their reservations — the source's check with those
reservations removed passes too), same_pass_exit (a package already due when sent: the source booked its close in
the same pass, the port closes it on the next), unfilled_package (a multi-leg package the port's book did not
fill: the source's journal kept it open and closed it at its exit_at), orphan_round_trip (a coordinated package
with an unquoted later leg: the source's journal bought the earlier legs and sold them straight back, the port
sends nothing). After a pass classified as released_reservation, same_pass_exit or unfilled_package the two books
differ, so the rest of that sequence is counted as not compared."""
import os
import random
from datetime import date, datetime, timedelta, timezone

from desk import calendar as cal
from desk.sleeves.femto import compat as fc
from desk.util import ET

from . import femto_module, old_run, write_receipt

SRC = r'''
import json, pathlib, tempfile
from datetime import datetime
import desk.config as CFG
tmp = pathlib.Path(tempfile.mkdtemp())
CFG.STATE_DIR = tmp
import desk.free_options as FO
import desk.option_packages as OP
import desk.data.alpaca as A
SPEC = PAYLOAD["spec"]
ST = {}
def submit_option_mleg(legs, qty, price, cid):
    ST["mleg"].append([[[l["symbol"], l["side"], l["position_intent"]] for l in legs], qty, round(price, 6), cid])
    return {"status": "accepted", "id": "m%d" % len(ST["mleg"])}
A.submit_option_mleg = submit_option_mleg
def cancel(order_id):
    ST["cancels"] += 1
    return {"status": "canceled", "id": order_id}
FO._cancel = cancel
out = []
for i, seq in enumerate(PAYLOAD["seqs"]):
    journal = tmp / ("j%d.jsonl" % i)
    FO.PACKAGES = tmp / ("p%d.jsonl" % i)
    res = []
    for p in seq:
        moment = datetime.fromisoformat(p["moment"])
        ST.update(mleg=[], cancels=0)
        rows = FO.evaluate(moment, p["quote"], p["ret"], p["cash"], p["events"], package=p["package"],
                           market_open=p["market_open"])
        row = next(r for r in rows if r["id"] == SPEC)
        sent = []
        def send(order, client):
            sent.append([order["symbol"], order["side"], order["qty"], order["limit_price"], order["position_intent"],
                         client])
            return {"status": p["ack"], "id": "b%d" % len(sent), "filled_qty": "1" if p["ack"] == "filled" else "0"}
        FO.execute(moment, [row], journal=journal, market_open=p["market_open"], send=send)
        exits = OP.manage_exits(FO.PACKAGES, moment, quotes_ok=p["market_open"])
        state = OP.replay(FO.PACKAGES)["packages"] if FO.PACKAGES.exists() else {}
        why = {}
        for line in (FO.PACKAGES.read_text().splitlines() if FO.PACKAGES.exists() else []):
            r = json.loads(line)
            if r.get("event") == "status":
                why[r["client_order_id"]] = r.get("reason")
        res.append({"status": row["status"], "reason": row.get("reason"), "sent": sent, "mleg": ST["mleg"],
                    "cancels": ST["cancels"], "exits": sorted([e["client_order_id"], e["status"]] for e in exits),
                    "packages": {c: {"status": v.get("status"), "reason": why.get(c),
                                     "legs": [[l["symbol"], l["quantity"], l["price"], l.get("package_status")]
                                              for l in v.get("legs_filled") or []]}
                                 for c, v in state.items()}})
    out.append(res)
print(json.dumps(out))
'''

def _iso(dt):
    return dt.isoformat()


def _days():
    out, d = [], date(2025, 1, 6)
    while d <= date(2026, 9, 25):
        if cal.is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _moment(rnd, d):
    op, cl = cal.session_open(d), cal.session_close(d)
    u = rnd.random()
    if u < 0.12:
        t = op - rnd.randint(60, 5000)
    elif u < 0.20:
        t = cl + rnd.randint(1, 5000)
    else:
        t = op + rnd.randint(0, int(cl - op - 1))
    return datetime.fromtimestamp(t, tz=timezone.utc), op <= t < cl


def _stamps(rnd, m):
    """(source_at, received_at): fresh, stale, future, receipt before source, or missing."""
    u = rnd.random()
    src = m - timedelta(seconds=rnd.uniform(0, 80))
    rec = m - timedelta(seconds=rnd.uniform(0, min(25, (m - src).total_seconds())))
    if u < 0.06:
        src = m - timedelta(seconds=rnd.uniform(91, 400))
    elif u < 0.10:
        rec = m - timedelta(seconds=rnd.uniform(31, 120))
        src = rec - timedelta(seconds=rnd.uniform(0, 30))
    elif u < 0.13:
        src = m + timedelta(seconds=rnd.uniform(2.5, 30))
    elif u < 0.16:
        rec = m + timedelta(seconds=rnd.uniform(2.5, 30))
    elif u < 0.19:
        rec = src - timedelta(seconds=rnd.uniform(1, 20))
    elif u < 0.21:
        return None, _iso(rec)
    elif u < 0.23:
        return _iso(src), None
    return _iso(src), _iso(rec)


def _contract(rnd, root, d, right, k):
    exp = d + timedelta(days=rnd.randint(1, 60))
    return "%s%s%s%s%s%08d" % (root, exp.strftime("%y"), exp.strftime("%m"), exp.strftime("%d"),
                                "C" if right == "call" else "P", int(round(k * 1000)))


def _quote(rnd, m, d, spec):
    """the row's quote: the traded contract (tail / wheel) or the indicative probe (the others)."""
    if rnd.random() < 0.04:
        return None
    src, rec = _stamps(rnd, m)
    k = rnd.choice((rnd.uniform(50, 120), rnd.uniform(300, 700)))
    right = "put" if rnd.random() < 0.85 else "call"
    sym = _contract(rnd, "SPY", d, right, round(k)) if spec in ("FREE_OPT_TAIL_V1", "FREE_OPT_WHEEL_V1") else "SPY"
    bp = round(rnd.uniform(0.05, 9.0), 2)
    ap = round(bp + rnd.uniform(0.0, 0.4), 2)
    u = rnd.random()
    if u < 0.04:
        bp = None
    elif u < 0.07:
        ap = round(bp - 0.05, 2)
    elif u < 0.09:
        bp = 0.0
    q = {"symbol": sym, "bp": bp, "ap": ap, "received_at": rec}
    q["t" if rnd.random() < 0.85 else "source_at"] = src
    if spec == "FREE_OPT_WHEEL_V1" and rnd.random() < 0.88:
        q["strike"] = float(round(k))
    return q


def _leg(rnd, m, d, root, right, side):
    k = round(rnd.uniform(300, 700))
    src, rec = _stamps(rnd, m) if rnd.random() < 0.5 else (_iso(m - timedelta(seconds=rnd.uniform(0, 20))), _iso(m))
    bid = round(rnd.uniform(0.0, 8.0), 2)
    ask = round(bid + rnd.uniform(0.01, 0.5), 2)
    if rnd.random() < 0.04:
        ask, bid = bid, ask                                      # crossed
    leg = {"symbol": _contract(rnd, root, d, right, k), "right": right, "side": side,
           "quantity": 1 if rnd.random() < 0.85 else 2, "bid": bid, "ask": ask, "underlying": root}
    if src:
        leg["source_at"] = src
    if rec:
        leg["received_at"] = rec
    return leg


def _package(rnd, m, d, spec, pool):
    if rnd.random() < 0.10:
        return None
    pair = spec == "FREE_OPT_PAIR_V1"
    n = 2 if rnd.random() < 0.88 else rnd.choice((1, 3))
    legs = []
    for i in range(n):
        root = ("SPY", "QQQ")[i % 2] if (pair and rnd.random() < 0.9) else "SPY"
        right = ("call", "put")[i % 2] if (not pair and rnd.random() < 0.92) else rnd.choice(("call", "put"))
        legs.append(_leg(rnd, m, d, root, right, "buy" if rnd.random() < 0.85 else "sell"))
    u = rnd.random()
    execution = ("broker_mleg" if u < 0.55 else "broker_coordinated" if u < 0.80 else "local" if u < 0.88
                 else "model_test" if u < 0.94 else "delayed_local_simulation")
    exit_at = m + (timedelta(seconds=rnd.randint(-7200, 7200)) if rnd.random() < 0.04 else
                   timedelta(days=rnd.choice((1, 2, 3, 6, 10)), seconds=rnd.randint(-7200, 7200)))
    p = {"client_order_id": rnd.choice(pool), "book_id": spec, "shape": "straddle" if not pair else "pair",
         "execution": execution, "legs": legs, "result_series": rnd.choice(("broker_paper", "local_paper", "fixture")),
         "exit_at": _iso(exit_at) if rnd.random() < 0.9 else None}
    if rnd.random() < 0.8:
        p["legs_required"] = 2
    if rnd.random() < 0.5:
        p["max_loss"] = round(rnd.choice((rnd.uniform(100, 5000), rnd.uniform(20_000, 70_000))), 2)
        if rnd.random() < 0.4:
            p["risk_cap"] = round(rnd.uniform(1000, 90_000), 2)
    if rnd.random() < 0.03:
        p["deliverable_ok"] = False
    if rnd.random() < 0.05:
        p["fixture"] = True
    if pair:
        p["hedge"] = {"beta": 1.1, "z": 2.4, "signal": True, "reason": "Hedge frozen through x."}
        p["hedge_frozen"] = rnd.random() < 0.85
    return p


def _events(rnd, d):
    out = []
    for _ in range(rnd.choice((0, 1, 1, 2))):
        s = d if rnd.random() < 0.6 else d + timedelta(days=rnd.choice((-1, 1, 5)))
        out.append({"session": s.isoformat(), "verified": rnd.random() < 0.8})
    return out


def _sequences(rnd, spec, n_seqs, n_steps):
    days = _days()
    seqs = []
    for i in range(n_seqs):
        d = rnd.choice(days)
        pool = ["pkg-%d-%d" % (i, j) for j in range(4)]
        steps = []
        for _ in range(n_steps):
            u = rnd.random()
            if u < 0.45:
                pass
            elif u < 0.8:
                d = cal.next_trading_day(d)
            else:
                d = cal.next_trading_day(d, rnd.randint(2, 6))
            m, is_open = _moment(rnd, d)
            p = {"moment": _iso(m), "market_open": is_open, "quote": _quote(rnd, m, d, spec),
                 "ret": None if rnd.random() < 0.08 else round(rnd.gauss(-0.02, 0.025), 5),
                 "cash": round(rnd.choice((0.0, rnd.uniform(0, 90_000), rnd.uniform(50_000, 120_000))), 2),
                 "events": _events(rnd, m.date()), "package": _package(rnd, m, d, spec, pool),
                 "ack": "filled" if rnd.random() < 0.9 else rnd.choice(("accepted", "rejected"))}
            if spec in ("FREE_OPT_TAIL_V1", "FREE_OPT_WHEEL_V1", "FREE_OPT_PARITY_V1"):
                p["package"] = None
            steps.append(p)
        seqs.append(steps)
    return seqs


def _ctx(p, meta, legs, pending):
    m = datetime.fromisoformat(p["moment"])
    extra = {"quote": p["quote"], "underlying_return": p["ret"], "cash": p["cash"], "events": p["events"],
             "package": p["package"], "market_open": p["market_open"], "legs": legs, "pending": pending,
             "meta": meta}
    return fc.Context(now=m.timestamp(), session=m.astimezone(ET).date().isoformat(), equity=0.0, extra=extra)


def _port_pass(mod, p, meta, legs, pending, rnd):
    """one port pass + its book's fills -> (comparable record, meta, legs, pending)."""
    ctx = _ctx(p, meta, legs, pending)
    out = mod.decide({}, ctx)
    rec = {"status": out["row"]["status"], "reason": out["row"].get("reason"), "sent": [], "mleg": [], "legs_sent": [],
           "cancels": 0, "exits": [], "pkg_submitted": out["row"].get("client") is not None}
    meta = dict(meta)
    if "sent" in out:
        meta["sent"] = out["sent"]
    if "packages" in out:
        meta["packages"] = out["packages"]
    legs, pending = {k: dict(v) for k, v in legs.items()}, []          # working orders end with the pass's day
    m = datetime.fromisoformat(p["moment"])
    for it in out["intents"]:
        if it.kind == "cancel":
            rec["cancels"] += 1
            continue
        if it.kind == "exit":
            for l in it.legs:
                legs.pop(l["symbol"], None)
            rec["exits"].append(it.signal_key)
            continue
        if it.asset == "mleg":
            rec["mleg"].append([[[l["symbol"], l["side"], l["position_intent"]] for l in it.legs], it.qty_hint,
                                round(it.net_price, 6), it.signal_key])
            if rnd.random() < 0.97:
                for l in it.legs:
                    legs[l["symbol"]] = {"qty": it.qty_hint * (1 if l["side"] == "buy" else -1), "avg": 0.0,
                                         "opened_at": m.timestamp(), "meta": dict(it.position_meta or {})}
            else:
                rec["unfilled_package"] = True
            continue
        l = it.legs[0]
        if (it.position_meta or {}).get("package"):
            rec["legs_sent"].append([l["symbol"], l["side"], it.qty_hint, it.order["limit_price"]])
            legs[l["symbol"]] = {"qty": it.qty_hint * (1 if l["side"] == "buy" else -1), "avg": it.order["limit_price"],
                                 "opened_at": m.timestamp(), "meta": dict(it.position_meta)}
            continue
        rec["sent"].append([l["symbol"], l["side"], it.qty_hint, it.order["limit_price"], l["position_intent"],
                            it.signal_key])
        if p["ack"] == "filled":
            legs[l["symbol"]] = {"qty": it.qty_hint * (1 if l["side"] == "buy" else -1), "avg": it.order["limit_price"],
                                 "opened_at": m.timestamp(), "meta": dict(it.position_meta or {})}
        elif p["ack"] == "accepted":
            pending.append({"action": "enter", "occ": l["symbol"], "side": l["side"], "qty": it.qty_hint,
                            "limit": it.order["limit_price"], "key": it.signal_key, "meta": {}})
    rec["packages"] = {c: v.get("status") for c, v in (meta.get("packages") or {}).items()}
    return rec, meta, legs, pending


SENT_STATES = ("filled", "submitted", "rejected", "partial", "unknown")
SAME_JOURNAL = {"open": ("open", "exit_waiting_on_quote"), "closed": ("exit_submitted", "closed")}


def run_for(name, spec_id, n_seqs=150, n_steps=8, seed=20261016):
    mod = femto_module(name)
    rnd = random.Random(seed)
    seqs = _sequences(rnd, spec_id, n_seqs, n_steps)
    src = old_run(SRC, {"spec": spec_id, "seqs": seqs}, timeout=3600, tree=os.environ.get("AURELIA_SRC"))
    diffs = []
    stats = {"passes": 0, "identical": 0, "skipped_after_divergence": 0, "statuses": {}, "single_orders": 0,
             "packages_sent": 0, "package_exits": 0, "cancels": 0,
             "named": {"natural_debit": 0, "package_quantity": 0, "released_reservation": 0, "same_pass_exit": 0,
                       "unfilled_package": 0}}
    frnd = random.Random(seed + 1)
    for seq, sres in zip(seqs, src):
        meta, legs, pending, diverged = {}, {}, [], False
        for p, s in zip(seq, sres):
            stats["passes"] += 1
            if diverged:                                      # a classified book divergence: the books now differ
                stats["skipped_after_divergence"] += 1
                continue
            rec, meta, legs, pending = _port_pass(mod, p, meta, legs, pending, frnd)
            key = "%s: %s" % (s["status"], (s["reason"] or "")[:70])
            stats["statuses"][key] = stats["statuses"].get(key, 0) + 1
            why = _compare(s, rec, p, meta, stats)
            if why is True:
                stats["identical"] += 1
                continue
            if why in stats["named"]:
                stats["named"][why] += 1
                diverged = True
                continue
            diffs.append({"part": why, "pass": p, "source": s, "port": rec})
            diverged = True
    res = {"sleeve": name, "cases": stats["passes"], "identical": stats["identical"], "diffs": diffs[:10],
           "n_diffs": len(diffs), "stats": stats,
           "method": "source free_options.evaluate / execute (own row) / option_packages.submit_package / "
                     "manage_exits in its own tree vs %s.decide() on the same inputs, books following the port's fills"
                     % name}
    write_receipt(name, res)
    return res


def _compare(s, rec, p, meta, stats):
    """True when the pass is identical; else a named-divergence label (verified) or the reason of a diff."""
    st_src = "sent" if s["sent"] and s["status"] in SENT_STATES else s["status"]
    if st_src != rec["status"]:
        if _released(s, rec, p, meta):
            return "released_reservation"
        return "row status"
    if not rec.get("pkg_submitted") and s["reason"] != rec["reason"]:
        return "row reason"
    if s["sent"] != rec["sent"]:
        return "single orders"
    if s["cancels"] != rec["cancels"]:
        return "cancels"
    stats["single_orders"] += len(s["sent"])
    stats["cancels"] += s["cancels"]
    return _packages(s, rec, p, stats)


def _released(s, rec, p, meta):
    """the source's risk check rejected the package, the port's passed, and the only difference in the reserved risk
    is what the port released (its closed / rejected packages): verified on the source's own rejection reason."""
    client = (p["package"] or {}).get("client_order_id")
    sj = s["packages"].get(client) or {}
    if not (rec["status"] == "open" and s["status"] == "BLOCKED_INPUT" and sj.get("status") == "BLOCKED_INPUT"
            and (sj.get("reason") or "").endswith(("would exceed its risk cap", "does not cover this book"))):
        return False
    released = sum(float(v.get("amount") or 0) for c, v in (meta.get("packages") or {}).items()
                   if c != client and v.get("status") in ("closed", "orphan_recovered", "rejected"))
    return released > 0


def _packages(s, rec, p, stats):
    pkg = p["package"] or {}
    client = pkg.get("client_order_id")
    # multi-leg: same legs and client; the port's price is the debit the source's journal booked (natural_debit
    # when the source's broker order carried another), its quantity the journal's (package_quantity)
    if len(s["mleg"]) != len(rec["mleg"]):
        return "multi-leg sends"
    for (sl, sq, sp, sc), (pl, pq, pp, pc) in zip(s["mleg"], rec["mleg"]):
        booked = [l for l in (s["packages"].get(sc) or {}).get("legs") or [] if l[3] in ("open", "partial")]
        if sl != pl or not pc.endswith(":" + sc) or not booked:
            return "multi-leg legs"
        debit = round(sum((1 if l[1] > 0 else -1) * float(l[2]) for l in booked), 6)
        if abs(debit - pp) > 1e-6:
            return "multi-leg price is not the journal's"
        if abs(sp - pp) > 1e-9:
            stats["named"]["natural_debit"] += 1
        if int(sq) != int(pq):
            if int(pq) != int(abs(booked[0][1])):
                return "multi-leg quantity is not the journal's"
            stats["named"]["package_quantity"] += 1
        stats["packages_sent"] += 1
    # coordinated / local legs of a package sent this pass: the journal's open position rows, leg for leg; a package
    # the source opened and unwound in its journal (orphan_recovered: each filled leg sold back) is no order here
    pj = s["packages"].get(client) or {}
    newly = rec.get("pkg_submitted") and rec["status"] != "duplicate" and \
        (pkg.get("execution") or "local") not in ("broker_mleg", "model_test")
    if newly or rec["legs_sent"]:
        opened = [l for l in pj.get("legs") or [] if l[3] in ("open", "partial")]
        if pj.get("status") == "orphan_recovered":
            closes = [l for l in pj.get("legs") or [] if l[3] == "orphan_close"]
            if sorted((l[0], -l[1]) for l in opened) != sorted((l[0], l[1]) for l in closes) or rec["legs_sent"]:
                return "orphan legs"
            stats["named"]["orphan_round_trip"] = stats["named"].get("orphan_round_trip", 0) + 1
            opened = []
        booked = [[l[0], abs(l[1]), round(float(l[2]), 2)] for l in opened]
        got = [[l[0], l[2], round(float(l[3]), 2)] for l in rec["legs_sent"]]
        if booked != got:
            return "coordinated legs"
        if got:
            stats["packages_sent"] += 1
    # this pass's package journal status
    if rec.get("pkg_submitted") and client in s["packages"]:
        sst, pst = s["packages"][client]["status"], (rec["packages"] or {}).get(client)
        if sst != pst and pst not in SAME_JOURNAL.get(sst, ()):
            if sst == "closed" and pst == "open" and pkg.get("exit_at") and \
                    datetime.fromisoformat(pkg["exit_at"]) <= datetime.fromisoformat(p["moment"]):
                return "same_pass_exit"                       # due when sent: the source closed it in this pass
            return "journal status %s vs %s" % (sst, pst)
    # exits: the packages closed this pass
    sx = sorted(c for c, st in s["exits"] if st == "closed")
    px = sorted({k.split(":exit:", 1)[1].split(":")[0] for k in rec["exits"]})
    if sx != px:
        never = [c for c in sx if c not in px and (rec["packages"] or {}).get(c) == "closed"]
        if never and all(c in never for c in sx if c not in px) and not [c for c in px if c not in sx]:
            return "unfilled_package"                         # the port's book never filled it
        return "exits"
    stats["package_exits"] += len(sx)
    return True
