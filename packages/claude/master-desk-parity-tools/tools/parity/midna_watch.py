"""Midna's hourly watch (the producer of midna_qqq_flip5_tza, midna_w_cyan_moonshot and the 1H fire inbox): the
original scripts/tensor-watch.mjs (lector-desk fd0e0a07) run unmodified under Node in a scratch layout of its pinned
files vs desk/feedlib/midna_watch.py, on real Yahoo chart payloads cut at random clocks.

Data: Yahoo's public chart endpoint (60m range 730d and 1wk range 10y for a sample of the swing basket, 1d range 2y
for QQQ and TZA), fetched once into a scratch directory (MIDNA_WATCH_DATA) and never written into the repository.
Each case takes one to three basket names (WATCH_SYMBOLS, so the source prints its per-name history line), a clock
(about half of them one to three hours after one of the name's 1H fires, so the inbox path runs; the rest anywhere in
the last 400 sessions, inside and outside regular hours), every payload cut at that clock (Yahoo returns the bars that
opened by then), a seen map (random prior keys, sometimes the fire's own key) and, for one fetch in ten, a scripted
status sequence (500 then 200, 422 then the period1/period2 retry, four failures, 404s). Random clocks rarely land
where the QQQ block's flip5 or a moonshot is live, so a targeted shard (`<n> <seed> <checkpoint> targeted`) places
every clock there: shortly after a QQQ slow-state flip, or within the 10 days after a cheap, deep weekly buy-cyan bar
(found on the full payloads by the port's replica; both sides still run on the payloads cut at the clock).

The source runs with a preload that (a) answers fetch from the case's payloads and statuses, recording each URL,
(b) fixes Date.now / new Date() at the case's clock and (c) adds the desk calendar's closes outside 2026 to
market-calendar.mjs's HOLIDAYS / EARLY_CLOSE (the calendar is common.py's named divergence). Compared, exactly: the
inbox files (every field), watch-seen.json, shadow-feed.json (generatedAt, the QQQ block, the moonshots, the errors),
whether watch-stamp.json was written, each name's history line (closed bars, session bars, fires, the last fire) and
the URLs requested. When a case scripts a retry, the source's two-worker pool may finish names out of order (its
sleep is real time), so the moonshot and error lists of those cases are compared as sorted lists."""
import atexit
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

from desk.feedlib import midna_watch as W

from . import write_receipt
from .midna_common import LEAN_ENV, check_pin, desk_closes

N_CASES = 1000
DATA = os.environ.get("MIDNA_WATCH_DATA",
                      "/tmp/claude-0/-home-user/68100f50-a551-5c19-83c9-96beaaccdaac/scratchpad/watchdata")
FILES = ["scripts/tensor-watch.mjs", "scripts/market-calendar.mjs",
         "quant-research/Author-research/real_engine/lib/anna-replica.mjs",
         "quant-research/Author-research/real_engine/lib/anna-epochs.mjs",
         "quant-research/Author-research/real_engine/lib/tensor-chart-window.mjs",
         "quant-research/Author-research/real_engine/lib/tensor-date-format.mjs",
         "quant-research/Author-research/real_engine/lib/tensor-enrichment-signals.mjs",
         "quant-research/Author-research/real_engine/app/lib/tensor-context.mjs",
         "quant-research/Author-research/shadow/swing_basket_v1.json"]

PRELOAD = r'''
import fs from "node:fs"
const CFG = JSON.parse(fs.readFileSync(process.env.WATCH_STUB, "utf8"))
const FAKE = CFG.nowMs
const RealDate = Date
class FakeDate extends RealDate {
  constructor(...a) { if (a.length === 0) super(FAKE); else super(...a) }
  static now() { return FAKE }
}
globalThis.Date = FakeDate
const cal = await import(CFG.calendar)
for (const d of CFG.holidays) cal.HOLIDAYS.add(d)
for (const d of CFG.early) cal.EARLY_CLOSE.add(d)
const calls = []
const tries = {}
globalThis.fetch = async (url) => {
  calls.push(String(url))
  const u = new URL(url)
  const sym = decodeURIComponent(u.pathname.split("/").pop())
  const key = sym + "|" + u.searchParams.get("interval")
  const n = tries[key] = (tries[key] || 0) + 1
  const plan = CFG.status[key] || []
  const status = plan[n - 1] ?? 200
  const file = CFG.payloads[key]
  if (status !== 200 || !file) return { ok: false, status: file ? status : 404, json: async () => ({}) }
  return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(file, "utf8")) }
}
process.on("exit", () => fs.writeFileSync(CFG.callsOut, JSON.stringify(calls)))
'''


def _load(sym, interval):
    p = os.path.join(DATA, f"{sym}_{interval}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def cut(payload, now):
    """the payload as Yahoo would have served it at `now`: the bars that opened by then."""
    if not payload:
        return payload
    res = json.loads(json.dumps(payload))
    r = res["chart"]["result"][0]
    ts = r.get("timestamp") or []
    keep = [i for i, t in enumerate(ts) if t <= now]
    r["timestamp"] = [ts[i] for i in keep]
    for q in r["indicators"].get("quote") or []:
        for k, v in list(q.items()):
            if isinstance(v, list):
                q[k] = [v[i] for i in keep]
    for q in r["indicators"].get("adjclose") or []:
        for k, v in list(q.items()):
            if isinstance(v, list):
                q[k] = [v[i] for i in keep]
    r.pop("events", None)
    return res


def available():
    syms = sorted({f.rsplit("_", 1)[0] for f in os.listdir(DATA) if f.endswith("_60m.json")}) if os.path.isdir(DATA) else []
    return [s for s in syms if os.path.exists(os.path.join(DATA, f"{s}_1wk.json"))]


def full_fires(syms):
    """each name's 1H fires over the whole fetched history (the port's replica; only used to place clocks)."""
    out = {}
    for s in syms:
        p = _load(s, "60m")
        ts = p["chart"]["result"][0].get("timestamp") or []
        if not ts:
            out[s] = []
            continue
        now = ts[-1] + 5 * 86400
        rows = W.run_engine([{"key": s, "interval": "1h", "payload": p, "now": now}]).get(s)
        out[s] = [f for f in W.hourly_fires(s, rows) if f["gap20"]] if isinstance(rows, list) else []
    return out


def targets(syms):
    """clocks where the watch's rare outputs are live, found on the full payloads with the port's replica (only used to
    place clocks; each case still runs both sides on payloads cut at its clock): the session closes after each QQQ
    slow-state flip (flip5) and the bars of each cheap, deep weekly buy-cyan close (moonshot)."""
    out = {"flip": [], "moon": []}
    q = _load("QQQ", "1d")
    end = q["chart"]["result"][0]["timestamp"][-1] + 8 * 86400
    rows = W.run_engine([{"key": "QQQ", "interval": "1d", "payload": q, "now": end}]).get("QQQ")
    prev = False
    for r in rows if isinstance(rows, list) else []:
        bear = bool(r[3])
        if bear and not prev:
            out["flip"].append(int(r[0]))
        prev = bear
    jobs = []
    for s in syms:
        p = _load(s, "1wk")
        ts = p["chart"]["result"][0].get("timestamp") or []
        if ts:
            jobs.append({"key": s, "interval": "1wk", "payload": p, "now": ts[-1] + 8 * 86400})
    got = W.run_engine(jobs)
    for s in syms:
        rows = got.get(s)
        if not isinstance(rows, list):
            continue
        for i in range(59, len(rows)):
            d = W.depth60(rows, i)
            if rows[i][4] and float(rows[i][1]) <= W.CHEAP_MAX and d is not None and d >= W.DEPTH60_MIN:
                out["moon"].append([s, int(rows[i][0])])
    return out


def gen_targeted(rnd, syms, tg):
    """a case at a flip5 or moonshot clock: half after a QQQ flip (6.6 h to 8 days after the flip bar's open), half
    4.3 to 10 days after a moonshot bar's open (the source reports a moonshot while it is <= 10 days old), the
    moonshot's name plus up to two others; one moonshot case in five has the moonshot's key in the seen map."""
    seen = {}
    if tg["moon"] and (not tg["flip"] or rnd.random() < 0.5):
        sym, w = rnd.choice(tg["moon"])
        names = [sym] + rnd.sample([s for s in syms if s != sym], rnd.randint(0, 2))
        now = w + rnd.randint(int(4.3 * 86400), 10 * 86400)
        if rnd.random() < 0.2:
            seen[f"{sym}:1w:cyan:{w}:moonshot"] = "2026-01-01T00:00:00.000Z"
    else:
        names = rnd.sample(syms, rnd.randint(1, 3))
        now = rnd.choice(tg["flip"]) + rnd.randint(int(6.6 * 3600), 8 * 86400)
    status = {}
    for key in [f"{s}|60m" for s in names] + [f"{s}|1wk" for s in names] + ["QQQ|1d", "TZA|1d"]:
        if rnd.random() < 0.05:
            status[key] = rnd.choice([[500], [422], [404, 404, 404, 404], [429, 200]])
    return {"names": names, "now": int(now), "seen": seen, "status": status}


def gen_case(rnd, syms, fires, last_ts):
    names = rnd.sample(syms, rnd.randint(1, 3))
    pool = [f for s in names for f in fires.get(s) or []]
    if pool and rnd.random() < 0.5:
        f = rnd.choice(pool)
        now = f["fireTs"] + rnd.randint(3600, 3 * 3600)
    else:
        now = last_ts - rnd.randint(0, 400) * 86400 - rnd.randint(0, 86400)
    seen = {}
    for f in pool:
        if rnd.random() < 0.15:
            seen[f"{f['sym']}:1h:swing:{f['setupTs']}:confirmed"] = "2026-01-01T00:00:00.000Z"
    for _ in range(rnd.randint(0, 3)):
        seen[f"ZZZ:1h:swing:{rnd.randint(1, 10**9)}:confirmed"] = "2026-01-01T00:00:00.000Z"
    status = {}
    for key in [f"{s}|60m" for s in names] + [f"{s}|1wk" for s in names] + ["QQQ|1d", "TZA|1d"]:
        if rnd.random() < 0.1:
            status[key] = rnd.choice([[500], [500, 500], [422], [422, 500], [500, 500, 500, 500], [404, 404, 404, 404],
                                      [429, 200]])
    return {"names": names, "now": int(now), "seen": seen, "status": status}


def run_source(work, case, layout):
    data = os.path.join(layout, "data", "equity-desk")
    shutil.rmtree(data, ignore_errors=True)
    os.makedirs(data)
    with open(os.path.join(data, "watch-seen.json"), "w") as f:
        json.dump(case["seen"], f)
    payloads = {}
    for s in case["names"]:
        for iv in ("60m", "1wk"):
            p = os.path.join(work, f"{s}_{iv}.json")
            json.dump(cut(_load(s, iv), case["now"]), open(p, "w"))
            payloads[f"{s}|{iv}"] = p
    for s in ("QQQ", "TZA"):
        p = os.path.join(work, f"{s}_1d.json")
        json.dump(cut(_load(s, "1d"), case["now"]), open(p, "w"))
        payloads[f"{s}|1d"] = p
    full, early = desk_closes()
    cfg = {"nowMs": case["now"] * 1000, "calendar": "file://" + os.path.join(layout, "scripts", "market-calendar.mjs"),
           "holidays": full, "early": early, "status": case["status"], "payloads": payloads,
           "callsOut": os.path.join(work, "calls.json")}
    with open(os.path.join(work, "stub.json"), "w") as f:
        json.dump(cfg, f)
    r = subprocess.run(["node", "--max-old-space-size=1024", "--import", "file://" + os.path.join(work, "preload.mjs"),
                        os.path.join(layout, "scripts", "tensor-watch.mjs")], cwd=layout, capture_output=True,
                       text=True, timeout=1200,
                       env=dict(os.environ, TZ="UTC", WATCH_SYMBOLS=",".join(case["names"]),
                                WATCH_STUB=os.path.join(work, "stub.json"), **LEAN_ENV))
    inbox_dir = os.path.join(data, "inbox")
    inbox = sorted((json.load(open(os.path.join(inbox_dir, f))) for f in os.listdir(inbox_dir)),
                   key=lambda x: x["key"]) if os.path.isdir(inbox_dir) else []
    feed = json.load(open(os.path.join(data, "shadow-feed.json"))) if os.path.exists(os.path.join(data, "shadow-feed.json")) else None
    lines = [ln for ln in r.stdout.splitlines() if " closed=" in ln]
    return {"inbox": inbox, "seen": json.load(open(os.path.join(data, "watch-seen.json"))), "feed": feed,
            "stamp": os.path.exists(os.path.join(data, "watch-stamp.json")), "lines": lines,
            "calls": json.load(open(cfg["callsOut"])) if os.path.exists(cfg["callsOut"]) else [], "code": r.returncode,
            "stderr": r.stderr[-400:]}


def run_port(case):
    calls, tries = [], {}
    payloads = {}
    for s in case["names"]:
        for iv in ("60m", "1wk"):
            payloads[f"{s}|{iv}"] = cut(_load(s, iv), case["now"])
    for s in ("QQQ", "TZA"):
        payloads[f"{s}|1d"] = cut(_load(s, "1d"), case["now"])

    def getter(url, params):
        from urllib.parse import unquote, urlencode
        calls.append(url + "?" + urlencode(params))
        sym = unquote(url.rsplit("/", 1)[-1])
        key = f"{sym}|{params['interval']}"
        tries[key] = tries.get(key, 0) + 1
        plan = case["status"].get(key) or []
        status = plan[tries[key] - 1] if tries[key] - 1 < len(plan) else 200
        if status != 200 or payloads.get(key) is None:
            raise W.YahooStatus(status if payloads.get(key) is not None else 404)
        return json.loads(json.dumps(payloads[key]))

    res, seen = W.watch(case["now"], dict(case["seen"]), case["names"], getter)
    lines = []
    for s in case["names"]:
        try:
            payload = W.yahoo(s, "60m", "730d", case["now"], lambda u, p, s=s: json.loads(json.dumps(payloads[f"{s}|60m"])))
        except Exception:                          # noqa: BLE001
            continue
        rows = W.run_engine([{"key": s, "interval": "1h", "payload": payload, "now": case["now"]}]).get(s)
        if not isinstance(rows, list):
            continue
        fires = W.hourly_fires(s, rows)
        last = W.iso_ms(fires[-1]["fireTs"]) if fires else "none"
        sess = sum(1 for r in rows if W.in_regular_session(r[0]))
        lines.append((s, f"{s} closed={len(rows)} session={sess} setups={len(fires)} last={last}"))
    return {"res": res, "seen": seen, "lines": lines, "calls": calls}


def compare(case, src, prt):
    bad = []
    res = prt["res"]
    if src["inbox"] != sorted(res["inbox"], key=lambda x: x["key"]):
        bad.append("inbox")
    if src["seen"] != prt["seen"]:
        bad.append("seen")
    feed = src["feed"] or {}
    if feed.get("generatedAt") != res["generatedAt"]:
        bad.append("generatedAt")
    if feed.get("qqq") != res["qqq"]:
        bad.append("qqq")
    retry = bool(case["status"])
    sm, pm = feed.get("moonshots") or [], res["moonshots"]
    se, pe = feed.get("errors") or [], res["errors"]
    if retry:
        sm, pm = sorted(sm, key=lambda x: x["key"]), sorted(pm, key=lambda x: x["key"])
        se, pe = sorted(se), sorted(pe)
    if json.dumps(sm, sort_keys=True) != json.dumps(pm, sort_keys=True):
        bad.append("moonshots")
    if se != pe:
        bad.append("errors")
    if src["stamp"] != res["stamp"]:
        bad.append("stamp")
    # the history line is printed for the names whose hourly job succeeded
    src_lines = sorted(src["lines"])
    ok_names = {s for s in case["names"] if not any(e.startswith(f"{s} 1h:") for e in res["errors"])}
    prt_lines = sorted(line for s, line in prt["lines"] if s in ok_names)
    if src_lines != prt_lines:
        bad.append("history")
    if sorted(map(_url, src["calls"])) != sorted(map(_url, prt["calls"])):
        bad.append("calls")
    return bad


def _url(u):
    """a request as (path, query pairs): the source writes events=div,splits unencoded, urlencode writes %2C."""
    from urllib.parse import parse_qsl, urlsplit
    p = urlsplit(u)
    return [p.scheme, p.netloc, p.path, sorted(parse_qsl(p.query))]


def run(n=N_CASES, seed=20261016, progress=None, targeted=False):
    syms = available()
    if not syms:
        raise SystemExit(f"no watch data under {DATA} (fetch the Yahoo payloads first)")
    rnd = random.Random(seed)
    work = tempfile.mkdtemp(prefix="midna_watch_")
    atexit.register(shutil.rmtree, work, True)
    layout = os.path.join(work, "layout")
    for rel in FILES:
        dst = os.path.join(layout, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(check_pin("lector", rel), dst)
    with open(os.path.join(work, "preload.mjs"), "w") as f:
        f.write(PRELOAD)
    fires = None if targeted else full_fires(syms)
    tg = targets(syms) if targeted else None
    last_ts = max(_load(s, "60m")["chart"]["result"][0]["timestamp"][-1] for s in syms)
    diffs, stats = [], {"names": 0, "inbox": 0, "moonshots": 0, "qqq_blocks": 0, "flip5": 0, "errors": 0,
                        "retry_cases": 0, "history_fires": 0, "no_stamp": 0}
    for k in range(n):
        case = gen_targeted(rnd, syms, tg) if targeted else gen_case(rnd, syms, fires, last_ts)
        src = run_source(work, case, layout)
        prt = run_port(case)
        bad = compare(case, src, prt)
        stats["names"] += len(case["names"])
        stats["inbox"] += len(src["inbox"])
        stats["moonshots"] += len((src["feed"] or {}).get("moonshots") or [])
        stats["qqq_blocks"] += bool((src["feed"] or {}).get("qqq"))
        stats["flip5"] += bool(((src["feed"] or {}).get("qqq") or {}).get("flip5"))
        stats["errors"] += len((src["feed"] or {}).get("errors") or [])
        stats["retry_cases"] += bool(case["status"])
        stats["no_stamp"] += not src["stamp"]
        stats["history_fires"] += sum(int(ln.split("setups=")[1].split()[0]) for ln in src["lines"])
        if (k + 1) % 10 == 0:
            print(f"case {k + 1}/{n} diffs={len(diffs) + bool(bad)}", file=sys.stderr, flush=True)
        if progress:                                   # a shard's checkpoint (merge() folds shards into the receipt)
            with open(progress, "w") as f:
                json.dump({"seed": seed, "targeted": bool(targeted), "cases": k + 1,
                           "targets": {k2: len(v) for k2, v in tg.items()} if tg else None,
                           "n_diffs": len(diffs) + bool(bad), "stats": stats,
                           "diffs": (diffs + ([{"case": k, "names": case["names"], "now": case["now"], "bad": bad}]
                                              if bad else []))[:10], "names_sampled": syms}, f)
        if bad:
            diffs.append({"case": k, "names": case["names"], "now": case["now"], "bad": bad,
                          "src": {"inbox": src["inbox"][:2], "feed": src["feed"], "lines": src["lines"],
                                  "stderr": src["stderr"]},
                          "port": {"inbox": prt["res"]["inbox"][:2], "qqq": prt["res"]["qqq"],
                                   "moonshots": prt["res"]["moonshots"], "errors": prt["res"]["errors"],
                                   "lines": prt["lines"]}})
    shutil.rmtree(work, ignore_errors=True)
    res = {"cases": n, "identical": n - len(diffs), "diffs": diffs[:10], "n_diffs": len(diffs), "stats": stats,
           "names_sampled": syms,
           "sleeves": ["midna_qqq_flip5_tza", "midna_w_cyan_moonshot", "midna_hourly_playbook (inbox)"],
           "method": "tensor-watch.mjs run unmodified under Node (fetch / clock stubbed by a preload; the source "
                     "holiday table extended with the desk calendar outside 2026) vs midna_watch.watch on the same "
                     "real Yahoo payloads cut at the case clock; exact (moonshot / error lists sorted in retry cases)"}
    write_receipt("midna_watch", res)
    return dict(res, sleeve="midna_watch")


METHOD = ("tensor-watch.mjs run unmodified under Node (fetch / clock stubbed by a preload; the source holiday table "
          "extended with the desk calendar outside 2026) vs midna_watch.watch on the same real Yahoo payloads cut at "
          "the case clock; exact (moonshot / error lists sorted in retry cases)")


def merge(paths):
    """fold shard checkpoints (each its own seed) into the receipt."""
    shards = [json.load(open(p)) for p in paths]
    stats = {}
    for sh in shards:
        for k, v in sh["stats"].items():
            stats[k] = stats.get(k, 0) + v
    n = sum(sh["cases"] for sh in shards)
    nd = sum(sh["n_diffs"] for sh in shards)
    res = {"cases": n, "identical": n - nd, "n_diffs": nd, "stats": stats,
           "diffs": [dict(d, seed=sh["seed"]) for sh in shards for d in sh["diffs"]][:10],
           "shards": [{"seed": sh["seed"], "cases": sh["cases"], "n_diffs": sh["n_diffs"],
                       "targeted": bool(sh.get("targeted")), "targets": sh.get("targets"),
                       "flip5": sh["stats"].get("flip5"), "moonshots": sh["stats"].get("moonshots")}
                      for sh in shards],
           "names_sampled": shards[0]["names_sampled"] if shards else [],
           "sleeves": ["midna_qqq_flip5_tza", "midna_w_cyan_moonshot", "midna_hourly_playbook (inbox)"],
           "method": METHOD + "; run as seeded shards, each case independent"}
    write_receipt("midna_watch", res)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "merge":
        r = merge(sys.argv[2:])
    elif len(sys.argv) > 1:
        r = run(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None,
                len(sys.argv) > 4 and sys.argv[4] == "targeted")
    else:
        r = run()
    print(json.dumps({k: r[k] for k in ("cases", "identical", "n_diffs", "stats")}))
