"""Author_paper: the Author paper desk's decision rules (Author-desk @652db7af src/lib/workdesk/paper-rules.ts
judgePaper / exitMath / bookMayEnter / paperShares / paperStop / paperTarget / inPocket / sameStoryCount /
paperEligible, tensor-edge.ts classifyEpisode / atr14 / chaseVerdict / impulseTarget / impulseExit / greenMayEnter,
exit.ts readExit / overheadFib / wave3Target / failed618 / railFlip / swingStop / swingTarget, select.ts weeklyBars,
cluster.ts clusterOf, timing.ts isBuyCode / isSellCode / capWatch; the SOURCE files and their import closure run
unmodified under Node 22) vs the port (desk/sleeves/Author/paper.py) on the same inputs.

Cases (deterministic, seeded):
  judge    random judgePaper tickets: buy (gold / Echo / Echo add / book / Tensor impulse) and sell (Tensor flatten,
           sell grace, card stop / target, impulse T1 / no progress / giveback / 5% target, swing readExit on daily
           bars), every input field randomly present, absent or at its edge (premarket, 15:45, caps, same story)
  exit     exitMath and readExit on random daily tapes shaped to reach each branch: overhead Fib rejections after
           runs, Fib break-retest-reject, weekly RSI stretch + daily bearish divergence, banked weeks, failed 0.618,
           50/200-day rail flips
  misc     the helpers above on random inputs
Compared exactly (JSON null = undefined).

    Author_DESK=<Author-desk @652db7af> PARITY_BLOBS=<dir with the voice/machine JSON blobs> \
        python3 -m tools.parity.run Author_paper"""
import json
import math
import random

from desk.sleeves.Author import paper as P

from . import write_receipt
from .node_pinned import cleanup, run as node_run, same, stage, transpile_ts

COMMIT = "652db7afcc4312b6bd44d41547ca0f73981fe3ff"
TS = {
    "src/lib/prism/kernel.ts": "ef279262e81a4bd71a8e96b43234dbf103590ea6",
    "src/lib/tensor/doctrine.ts": "84065db763d67a752527e32f4a3b0c0016f0f498",
    "src/lib/tensor/indicators.ts": "04d1402b4e3c6db28c0b2447ec1fdb498a725fee",
    "src/lib/tensor/math.ts": "4add3a71847a6b9a7322b69e2a914ad290247e4a",
    "src/lib/tensor/session.ts": "7e6799c3bc18cbe1c5c7ecd9d3dbf1bdeb1b467b",
    "src/lib/voice/identities.ts": "789a704a4575c33ebc2478573765d620e92a5ea1",
    "src/lib/voice/retrieve.ts": "c323f20ace8709a586cf16dba8d8c73e9469a94c",
    "src/lib/workdesk/admit-ticker.ts": "2ba2130f275a125af190a396ed71337c8768181a",
    "src/lib/workdesk/after-hours.ts": "9366faf281fcb28b6f319060017a16e2b85114ff",
    "src/lib/workdesk/bottom-screen.ts": "a929d9f2a3615250fedbcd9d49f9f23d1b19f760",
    "src/lib/workdesk/buy-desk.ts": "b55128ddff2ca45e22d6ab35dd0956d6d3761295",
    "src/lib/workdesk/cluster.ts": "c0677336bd094fcddde96e0fd189c99f9a0ab051",
    "src/lib/workdesk/copy.ts": "2e0db8fb459e98bca01fecda2ced360a2b3a53d0",
    "src/lib/workdesk/curl.ts": "4ea3154b4918a28fbd86cc4611ec85ecb2e02b6e",
    "src/lib/workdesk/desk-post.ts": "f8ba5256a866685a0014c2fffcd66973b2b17ee8",
    "src/lib/workdesk/doctrine.ts": "59cf28537f2bd48fe5cc42fc82659de620afaaf0",
    "src/lib/workdesk/engage.ts": "10ecf44a4900b09ff389b8e6713e4c102cd8669d",
    "src/lib/workdesk/exit.ts": "9e496477d7b780f3b09da90f1ceba16f0d352ca2",
    "src/lib/workdesk/folio-novelty.ts": "efa996caea403313d72ff5f33a2d194c648294bb",
    "src/lib/workdesk/folio-voice.ts": "4b66fc0b575911e6d94afd92274a35eb42d53c6f",
    "src/lib/workdesk/fund-overlay.ts": "9eaff1c4700edf83e4708ce28b6b2d8f8d6c4076",
    "src/lib/workdesk/language-editor.ts": "0778b4b3beb69cc8ca7f54ccde820fe86dfcca46",
    "src/lib/workdesk/location-law.ts": "9b63af7b2d2a4f8c7959201917b85c33c6d96970",
    "src/lib/workdesk/paper-rules.ts": "e3bcb77c310acb557b6adb5fcdafd58ff3c8805d",
    "src/lib/workdesk/public-doctrine.ts": "ec91ee8f131d6c36b875eb36bd54f3317534fac7",
    "src/lib/workdesk/scanner-prompt.ts": "ceca8d80f6208e0265738607700657a6ba0ab403",
    "src/lib/workdesk/sector-copy.ts": "4add373d414e018ae09586a912dfde0e999aa499",
    "src/lib/workdesk/sector-map.ts": "5f4d89903bef4fc6c7d3f4f1f55055101945d5d3",
    "src/lib/workdesk/sector-tape.ts": "5693b6d68c98177ecf276b8d8ac6796ce5c48713",
    "src/lib/workdesk/select.ts": "a5078c1d87b8a2dc0e1cd9e5a062126a4f038e1f",
    "src/lib/workdesk/tape-levels.ts": "5f214698eaf64a4a0ddd207f774d6efafa02ac19",
    "src/lib/workdesk/tensor-edge.ts": "f54056b8c09bfe6a1f669beb47ae531d743d7b1f",
    "src/lib/workdesk/timing.ts": "1ae3325e2dae995c8ea38ca7c728dfd96e7d651e",
    "src/lib/workdesk/washout.ts": "d6d55212acc6206cb8cb9da94c0bbb67045c308b",
    "src/lib/workdesk/weekend-desk.ts": "9b4967d334534a67693df6061eeb2f82551d1dc6",
    "src/lib/workdesk/x-feedback.ts": "3d8de400843f9c8603f3bcaac93e1ea9dd72d92b",
}
DATA = {   # JSON the import closure loads at module time (fetched by blob into $PARITY_BLOBS when not checked out)
    "src/lib/voice/machine/situations.json": "e9fbbecd6c9191e25c4e84bf0e2f9f3b43c937bb",
    "src/lib/voice/machine/scanner-identities.lock.json": "871e0001b957894a70907e26069a889c8e76228c",
    "src/lib/voice/machine/manifest.json": "a9b92842b14ef40b5d8dde1c164a9f209044bf8e",
    "src/lib/voice/machine/contract.json": "ffd7e61fa18206ae95b1175e4fc47445a51c7144",
}
N_JUDGE = 4000
N_EXIT = 2500
N_MISC = 2500
BATCH = 500
SYMS = ["NVDA", "AMD", "TSM", "PLTR", "CRM", "TSLA", "RIVN", "ASTS", "XLE", "LLY", "SPY", "QQQ", "AAPL", "SOFI", "MU",
        "nvda", " amd ", "HOOD", "RKLB", "DVN"]
CODES = ["GREEN_BUY", "CYAN_BUY", "GREEN_BUY_HOLD", "TENSOR_BUY", "RED_SELL", "MAGENTA_SELL", "SELL", "VECTOR_SELL",
         "BOOK_BUY", "ECHO_ADD", "GOLD", "DCB_GREEN_BUY", "STOP", "TARGET", "VECTOR_BUY"]

DRIVER = r"""
const { readFileSync } = require("node:fs");
const PR = require("./src/lib/workdesk/paper-rules.js");
const TE = require("./src/lib/workdesk/tensor-edge.js");
const EX = require("./src/lib/workdesk/exit.js");
const SE = require("./src/lib/workdesk/select.js");
const CL = require("./src/lib/workdesk/cluster.js");
const TI = require("./src/lib/workdesk/timing.js");
const P = JSON.parse(readFileSync(0, "utf8"));
const out = P.cases.map((c) => {
  const a = c.args;
  switch (c.kind) {
    case "judge": return PR.judgePaper(a);
    case "exitMath": return PR.exitMath(a);
    case "readExit": return EX.readExit(a);
    case "shares": return PR.paperShares(a);
    case "stopTarget": return [PR.paperStop(a.entry, a.card), PR.paperTarget(a.entry), EX.swingStop(a.entry, a.card),
      EX.swingTarget(a.entry, a.cardT), PR.inPocket(a.price, a.buy, a.stop), TE.impulseTarget(a.entry, a.atr)];
    case "book": return PR.bookMayEnter(a);
    case "eligible": return PR.paperEligible(a.member);
    case "episode": return TE.classifyEpisode(a.last, a.next);
    case "chase": return [TE.chaseVerdict(a.price, a.signal, a.atr), TE.chaseLine(a.signal, a.atr2)];
    case "atr": return TE.atr14(a.bars);
    case "impulse": return TE.impulseExit(a);
    case "green": return TE.greenMayEnter(a.kind, a.chase);
    case "weekly": return SE.weeklyBars(a.bars);
    case "levels": return [EX.overheadFib(a.bars, a.buy), EX.wave3Target(a.bars, a.buy, a.risk), EX.failed618(a.bars, a.last),
      EX.railFlip(a.bars, a.last)];
    case "story": return [CL.clusterOf(a.symbol), PR.sameStoryCount(a.symbol, a.open), TI.capWatch(a.watch)];
    case "codes": return a.codes.map((x) => [TI.isBuyCode(x), TI.isSellCode(x)]);
  }
  return null;
});
console.log(JSON.stringify(out));
"""


# -- generators ---------------------------------------------------------------------------------------------------------
def daily_bars(rnd, n=None):
    n = rnd.choice([0, 3, 9, 15, 25, 40, 80, 150, 250, 400]) if n is None else n
    t = 1_700_000_000_000 + rnd.randint(0, 400) * 86_400_000
    t -= t % 86_400_000
    t += rnd.choice([13 * 3600_000 + 30 * 60_000, 4 * 3600_000, 5 * 3600_000])
    px = rnd.uniform(2, 300)
    drift = rnd.choice([0.0, 0.002, -0.002, 0.006, 0.012, -0.008])
    vol = rnd.uniform(0.008, 0.05)
    out = []
    for _ in range(n):
        while ((t // 86_400_000) + 4) % 7 in (5, 6):      # skip weekends (1970-01-01 was a Thursday)
            t += 86_400_000
        o = px * (1 + rnd.gauss(0, vol / 3))
        c = max(0.2, px * (1 + rnd.gauss(drift, vol)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, vol / 2)))
        lo = min(o, c) * (1 - abs(rnd.gauss(0, vol / 2)))
        out.append({"t": t, "o": round(o, 4), "h": round(h, 4), "l": round(lo, 4), "c": round(c, 4),
                    "v": float(rnd.randint(1000, 9_000_000))})
        px = c
        t += 86_400_000
    return out


def shape_last(rnd, bars, buy):
    """bend the last bar onto a level the exit rules read."""
    if not bars:
        return bars
    b = dict(bars[-1])
    x = rnd.random()
    if x < 0.3:
        lvl = P.overhead_fib(bars, buy)
        if lvl:
            b["h"] = lvl * rnd.uniform(0.985, 1.035)
            b["o"] = lvl * rnd.uniform(0.97, 0.999)
            b["c"] = b["o"] * rnd.uniform(0.95, 0.999)
            b["l"] = min(b["c"], b["o"]) * rnd.uniform(0.97, 1.0)
    elif x < 0.45 and buy > 0:
        b["o"] = buy * rnd.uniform(0.99, 1.02)
        b["c"] = min(b["o"], buy * rnd.uniform(0.985, 1.0))
        b["h"] = max(b["o"], b["c"]) * 1.01
        b["l"] = min(b["o"], b["c"]) * 0.99
    elif x < 0.6 and len(bars) >= 25:
        rail = P._ema_now(bars, rnd.choice([50, 200])) or b["c"]
        b["c"] = rail * rnd.uniform(0.99, 1.02)
        b["h"] = max(b["h"], b["c"])
        b["l"] = min(b["l"], b["c"])
    for k in ("o", "h", "l", "c"):
        b[k] = round(b[k], 4)
    b["h"] = max(b["h"], b["o"], b["c"])
    b["l"] = min(b["l"], b["o"], b["c"])
    return bars[:-1] + [b]


def maybe(rnd, v, p=0.25):
    return v if rnd.random() > p else rnd.choice([None, "__absent__"])


def put(d, k, v):
    if v != "__absent__":
        d[k] = v


def judge_case(rnd):
    side = rnd.choice(["buy", "buy", "sell"])
    px = round(rnd.uniform(1, 400), 2)
    buy = rnd.choice([px, round(px * rnd.uniform(0.9, 1.1), 2), 0])
    stop = rnd.choice([round(buy * rnd.uniform(0.85, 0.995), 2), 0, round(buy * 1.01, 2)])
    target = rnd.choice([round(buy * rnd.uniform(1.01, 1.4), 2), 0, round(buy * 0.99, 2), round(px * 1.05, 2)])
    price = rnd.choice([px, round(buy * rnd.uniform(0.95, 1.06), 2), round(stop * rnd.uniform(0.98, 1.0), 2), 0,
                        round(target * rnd.uniform(0.99, 1.01), 2)])
    bar_at = 1_790_000_000_000 + rnd.randint(0, 10_000) * 60_000
    a = {"side": side, "code": rnd.choice(CODES), "price": price, "buy": buy, "stop": stop, "target": target,
         "hour": rnd.choice([4, 8, 9, 9, 10, 12, 15, 15, 16]), "minute": rnd.choice([0, 15, 34, 35, 36, 44, 45, 46, 59]),
         "openCount": rnd.choice([0, 1, 3, 5, 6, 9, 10, 11]), "buysToday": rnd.choice([0, 2, 15, 16, 17]),
         "lastBuyAt": rnd.choice([None, bar_at - rnd.choice([0, 30_000, 69_999, 70_000, 600_000])]), "barAt": bar_at,
         "hasPosition": rnd.random() < (0.85 if side == "sell" else 0.2)}
    put(a, "symbol", rnd.choice(SYMS + ["__absent__"]))
    put(a, "entry", maybe(rnd, rnd.choice([price, round(buy * rnd.uniform(0.9, 1.1), 2), 0])))
    put(a, "barUp", maybe(rnd, rnd.random() < 0.7))
    put(a, "sameDay", maybe(rnd, rnd.random() < 0.2))
    put(a, "clusterOpen", maybe(rnd, rnd.choice([0, 1, 2, 3])))
    put(a, "eligible", maybe(rnd, rnd.random() < 0.7))
    put(a, "folioFlatten", maybe(rnd, rnd.random() < 0.1, 0.6))
    put(a, "tensorFlatten", maybe(rnd, rnd.random() < 0.3, 0.4))
    kind = rnd.choice(["gold", "echo", "echoAdd", "book", "tensor", "tensor"])
    put(a, "goldTicket", kind == "gold" or (rnd.random() < 0.05))
    put(a, "echoTicket", kind in ("echo", "echoAdd"))
    put(a, "echoAdd", kind == "echoAdd" or "__absent__")
    put(a, "bookTicket", kind == "book")
    put(a, "weekend", maybe(rnd, rnd.random() < 0.15))
    put(a, "alreadyTrimmed", maybe(rnd, rnd.random() < 0.3))
    put(a, "alreadyAdded", maybe(rnd, rnd.random() < 0.3))
    if rnd.random() < 0.5:
        bars = daily_bars(rnd)
        a["bars"] = shape_last(rnd, bars, a.get("entry") or buy)
    put(a, "episodeKind", rnd.choice(["FRESH", "REINFORCED", "REPEATED", "REVERSAL", "STALE", "__absent__"]))
    put(a, "chaseKind", rnd.choice(["OK", "WAIT", "AVOID", "__absent__"]))
    put(a, "impulse", maybe(rnd, rnd.random() < 0.5))
    put(a, "openedAt", maybe(rnd, bar_at - rnd.choice([0, 60_000, 1_799_999, 1_800_000, 3 * 86_400_000,
                                                      9 * 86_400_000])))
    put(a, "now", maybe(rnd, bar_at + rnd.choice([0, 60_000]), 0.5))
    put(a, "atr", maybe(rnd, round(px * rnd.uniform(0.001, 0.03), 4)))
    put(a, "mfe", maybe(rnd, round(px * rnd.uniform(0.98, 1.1), 2)))
    put(a, "impulseOpen", maybe(rnd, rnd.choice([0, 3, 4, 5]), 0.4))
    put(a, "swingOpen", maybe(rnd, rnd.choice([0, 5, 6, 7]), 0.4))
    put(a, "closedSwing", maybe(rnd, rnd.choice([0, 5, 19, 20, 21, 40])))
    put(a, "antiChase", maybe(rnd, rnd.random() < 0.8))
    put(a, "atSupport", maybe(rnd, rnd.random() < 0.6))
    put(a, "curlOk", maybe(rnd, rnd.random() < 0.6))
    put(a, "coilOk", maybe(rnd, rnd.random() < 0.3))
    put(a, "context", rnd.choice(["adverse", "supportive", "neutral", "__absent__"]))
    return {"kind": "judge", "args": a}


def exit_cases(rnd):
    bars = daily_bars(rnd, rnd.choice([0, 9, 30, 60, 120, 200, 300]))
    last_c = bars[-1]["c"] if bars else rnd.uniform(5, 100)
    buy = round(last_c * rnd.choice([rnd.uniform(0.4, 0.7), rnd.uniform(0.9, 1.1), rnd.uniform(0.98, 1.02)]), 2)
    bars = shape_last(rnd, bars, buy)
    last = bars[-1]["c"] if bars and rnd.random() < 0.8 else round(last_c * rnd.uniform(0.9, 1.1), 2)
    stop = rnd.choice([0, round(buy * rnd.uniform(0.85, 0.99), 2), round(last * 1.01, 2)])
    now = bars[-1]["t"] + 3600_000 if bars else 1_790_000_000_000
    opened = rnd.choice([None, now - rnd.randint(1, 20) * 86_400_000, now + 1, 0])
    a = {"bars": bars, "last": last, "buy": buy, "stop": stop}
    put(a, "alreadyTrimmed", maybe(rnd, rnd.random() < 0.3))
    put(a, "alreadyAdded", maybe(rnd, rnd.random() < 0.3))
    if opened is not None:
        a["openedAt"] = opened
    put(a, "now", maybe(rnd, now, 0.2))
    out = [{"kind": "readExit", "args": a}]
    m = {"price": last, "entry": rnd.choice([buy, 0]), "stop": stop, "bars": bars, "target": rnd.choice(
        [0, round(buy * 1.2, 2), round(last * 0.99, 2)]), "impulse": rnd.random() < 0.35}
    put(m, "openedAt", maybe(rnd, now - rnd.choice([60_000, 1_800_000, 2 * 86_400_000])))
    m["now"] = now                      # runPaperExits always passes now (barAt); absent it reads the wall clock
    put(m, "atr", maybe(rnd, round(last * rnd.uniform(0.002, 0.03), 4)))
    put(m, "mfe", maybe(rnd, round(last * rnd.uniform(0.98, 1.1), 2)))
    put(m, "alreadyTrimmed", maybe(rnd, rnd.random() < 0.3))
    put(m, "alreadyAdded", maybe(rnd, rnd.random() < 0.3))
    out.append({"kind": "exitMath", "args": m})
    return out


def misc_cases(rnd):
    px = round(rnd.uniform(0.3, 500), 4)
    out = [{"kind": "shares", "args": {"equity": rnd.choice([0, 1000, 100_000.0, rnd.uniform(5e3, 5e6)]),
                                       "buy": rnd.choice([0, px]), "stop": rnd.choice([None, 0, px * 0.97, px * 1.01]),
                                       "sleeve": rnd.choice(["impulse", "gold", "echo", "swing"]),
                                       "premarket": rnd.random() < 0.5}},
           {"kind": "stopTarget", "args": {"entry": rnd.choice([0, px, 0.5, 0.98]), "card": rnd.choice([0, px * 0.9, px * 0.99, px * 1.1]),
                                           "cardT": rnd.choice([0, px * 1.1, px * 0.9]), "price": rnd.choice([0, px, px * 1.01]),
                                           "buy": px, "stop": rnd.choice([px * 0.97, px * 1.01]),
                                           "atr": rnd.choice([None, 0, px * 0.01])}},
           {"kind": "book", "args": {k: v for k, v in {
               "price": rnd.choice([0, px, px * 1.02, px * 1.04, px * 0.96, px * 0.95]), "buy": px,
               "stop": rnd.choice([px * 0.95, 0, px * 1.01]), "target": rnd.choice([px * 1.2, px * 0.99, 0]),
               "antiChase": rnd.choice([True, False, None, "__absent__"]),
               "atSupport": rnd.choice([True, False, None, "__absent__"]),
               "curlOk": rnd.choice([True, False, "__absent__"]), "coilOk": rnd.choice([True, False, "__absent__"]),
               "context": rnd.choice(["adverse", "neutral", "__absent__"])}.items() if v != "__absent__"}},
           {"kind": "eligible", "args": {"member": rnd.choice([None, {k: v for k, v in {
               "status": rnd.choice(["LIVE", "DROPPED", "__absent__"]), "call": rnd.choice(["BUY", "HALF", "__absent__"]),
               "demoted": rnd.choice([True, False, "__absent__"]), "buy": rnd.choice([px, "__absent__", None]),
               "stop": rnd.choice([px * 0.95, "__absent__"]), "target": rnd.choice([px * 1.1, px * 0.9, "__absent__"])
           }.items() if v != "__absent__"}])}}]
    t0 = 1_790_000_000_000 + rnd.randint(0, 999) * 300_000
    last = None if rnd.random() < 0.2 else {"symbol": "X", "interval": "5m", "side": rnd.choice(["buy", "sell"]),
                                            "barAt": t0, "eventKey": rnd.choice(["k1", "k2"]),
                                            "expiresAt": t0 + 6 * 300_000}
    nxt = {"symbol": "X", "interval": "5m", "side": rnd.choice(["buy", "sell"]),
           "barAt": t0 + rnd.choice([0, 300_000, 1_800_000, 1_800_001, 3_600_000, -300_000]),
           "eventKey": rnd.choice(["k1", "k2", "k3"])}
    if rnd.random() < 0.5:
        nxt["now"] = nxt["barAt"] + rnd.choice([0, 1_800_000, 1_800_001, 7_200_000])
    out.append({"kind": "episode", "args": {"last": last, "next": nxt}})
    sig = rnd.choice([0, px])
    out.append({"kind": "chase", "args": {"price": rnd.choice([0, px * rnd.uniform(0.98, 1.08)]), "signal": sig,
                                          "atr": rnd.choice([None, 0, px * rnd.uniform(0.002, 0.04)]),
                                          "atr2": rnd.choice([0, px * 0.01, px * 0.2])}})
    ib = [{"h": b["h"], "l": b["l"], "c": b["c"]} for b in daily_bars(rnd, rnd.choice([0, 10, 15, 16, 17, 40]))]
    out.append({"kind": "atr", "args": {"bars": ib if rnd.random() > 0.05 else None}})
    entry = rnd.choice([0, px])
    out.append({"kind": "impulse", "args": {k: v for k, v in {
        "price": rnd.choice([0, px * rnd.uniform(0.97, 1.06)]), "entry": entry, "openedAt": t0,
        "now": t0 + rnd.choice([0, 1_799_999, 1_800_000, 3_600_000]),
        "atr": rnd.choice([None, 0, px * rnd.uniform(0.002, 0.03), "__absent__"]),
        "mfe": rnd.choice([None, px * rnd.uniform(0.99, 1.08), "__absent__"])}.items() if v != "__absent__"}})
    out.append({"kind": "green", "args": {"kind": rnd.choice(["FRESH", "REPEATED", "REINFORCED", "STALE", "REVERSAL", None]),
                                          "chase": rnd.choice(["OK", "WAIT", "AVOID", None])}})
    wb = daily_bars(rnd)
    out.append({"kind": "weekly", "args": {"bars": wb}})
    lb = daily_bars(rnd, rnd.choice([5, 10, 19, 20, 30, 90, 250]))
    lc = lb[-1]["c"] if lb else px
    out.append({"kind": "levels", "args": {"bars": lb, "buy": rnd.choice([0, lc * rnd.uniform(0.5, 1.1)]),
                                           "risk": rnd.choice([0, lc * 0.05]),
                                           "last": rnd.choice([0, lc, lc * rnd.uniform(0.95, 1.03)])}})
    out.append({"kind": "story", "args": {"symbol": rnd.choice(SYMS), "open": rnd.sample(SYMS, rnd.randint(0, 8)),
                                          "watch": [rnd.choice(SYMS + ["", "  ", "Abc"]) for _ in range(rnd.randint(0, 60))]}})
    out.append({"kind": "codes", "args": {"codes": rnd.sample(CODES, 5)}})
    return out


# -- the port side -----------------------------------------------------------------------------------------------------
def port(c):
    a = c["args"]
    k = c["kind"]
    if k == "judge":
        return P.judge_paper(**a)
    if k == "exitMath":
        return P.exit_math(**a)
    if k == "readExit":
        return P.read_exit(**a)
    if k == "shares":
        return P.paper_shares(**a)
    if k == "stopTarget":
        return [P.paper_stop(a["entry"], a["card"]), P.paper_target(a["entry"]), P.swing_stop(a["entry"], a["card"]),
                P.swing_target(a["entry"], a["cardT"]), P.in_pocket(a["price"], a["buy"], a["stop"]),
                P.impulse_target(a["entry"], a["atr"])]
    if k == "book":
        return P.book_may_enter(**a)
    if k == "eligible":
        return P.paper_eligible(a["member"])
    if k == "episode":
        return P.classify_episode(a["last"], a["next"])
    if k == "chase":
        return [P.chase_verdict(a["price"], a["signal"], a["atr"]), P.chase_line(a["signal"], a["atr2"])]
    if k == "atr":
        return P.atr14(a["bars"])
    if k == "impulse":
        return P.impulse_exit(**a)
    if k == "green":
        return P.green_may_enter(a["kind"], a["chase"])
    if k == "weekly":
        return P.weekly_bars(a["bars"])
    if k == "levels":
        return [P.overhead_fib(a["bars"], a["buy"]), P.wave3_target(a["bars"], a["buy"], a["risk"]),
                P.failed618(a["bars"], a["last"]), P.rail_flip(a["bars"], a["last"])]
    if k == "story":
        return [P.cluster_of(a["symbol"]), P.same_story_count(a["symbol"], a["open"]), P.cap_watch(a["watch"])]
    if k == "codes":
        return [[P.is_buy_code(x), P.is_sell_code(x)] for x in a["codes"]]
    raise ValueError(k)


def _clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    return x


def corpus():
    rnd = random.Random(20261016)
    cases = [judge_case(rnd) for _ in range(N_JUDGE)]
    for _ in range(N_EXIT // 2):
        cases += exit_cases(rnd)
    for _ in range(N_MISC // 12):
        cases += misc_cases(rnd)
    return cases


def run():
    tree = stage("Author_DESK", "/home/user/Author-desk", dict(TS, **DATA))
    try:
        transpile_ts(tree, list(TS))
        cases = corpus()
        diffs, ident, kinds, actions = [], 0, {}, {}
        for i in range(0, len(cases), BATCH):
            chunk = cases[i:i + BATCH]
            theirs = node_run(tree, DRIVER, {"cases": chunk}, name="__driver.cjs")
            for j, (c, t) in enumerate(zip(chunk, theirs)):
                o = _clean(port(c))
                d = same(o, t)
                kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
                if c["kind"] in ("judge", "exitMath", "readExit") and isinstance(t, dict):
                    key = f"{c['kind']}:{t.get('action')}:{t.get('reason') or t.get('why')}"
                    actions[key] = actions.get(key, 0) + 1
                if d:
                    diffs.append({"case": i + j, "kind": c["kind"], "diff": [list(map(str, x)) for x in d[:5]],
                                  "args": json.dumps(c["args"])[:600]})
                else:
                    ident += 1
        res = {"sleeve": "Author_paper", "cases": len(cases), "identical": ident, "diffs": diffs[:40],
               "n_diffs": len(diffs), "stats": {"kinds": kinds, "verdicts": dict(sorted(actions.items()))},
               "source": {"repo": "Author-desk", "commit": COMMIT, "files": dict(TS, **DATA)},
               "method": "source TypeScript (and its import closure) under Node 22 vs desk/sleeves/Author/paper.py, "
                         "exact JSON equality",
               "sleeves": ["Author_tensor_gold_diamond", "Author_tensor_5m_impulse", "Author_echo_swing",
                           "Author_scanner_book_swing", "Author_tensor_1m_bracket"]}
        write_receipt("Author_paper", res)
        return res
    finally:
        cleanup(tree)
