"""Author_echo: the Echo Analysis lane's decision code vs its sources at Author-desk @652db7af under Node 22
(unmodified: classify.ts / gate.ts with types erased by the TypeScript compiler; echo-sidecar.mjs's stripHtml /
parseRss read verbatim out of the pinned script; the clock — new Date() — set per case, the only stub).

  classify  classifyEcho on generated posts: buys / starters / adds / holds / plans / recaps / old fills / never
            bought, $tickers and bare "I bought xyz", noise words, six-plus-ticker wraps, Unicode whitespace, BOMs
  gate      echoPaperGate (weekday, clock, BUY / ADD, first buy today, held, support / chase reads) at its edges
  rss       parseRss on generated Nitter feeds (CDATA, <br>, tags, reposts, foreign creators, status links,
            nitter.net -> x.com, #m anchors, missing pubDates)
Compared exactly (JSON null = undefined) — vs desk/sleeves/Author/echo.py.

    Author_DESK=<Author-desk @652db7af> python3 -m tools.parity.run Author_echo"""
import random

from desk.sleeves.Author import echo as E

from . import write_receipt
from .node_pinned import cleanup, run as node_run, same, stage, transpile_ts

COMMIT = "652db7afcc4312b6bd44d41547ca0f73981fe3ff"
TS = {"src/lib/echo/classify.ts": "04c85bb97b73ccea3faf6ccef45acda3976abd18",
      "src/lib/echo/gate.ts": "113bc6d59ec4b965a985a47de65aab563e1b0ceb"}
SCRIPTS = {"scripts/echo-sidecar.mjs": "7293ee38a37aa7ed7df572d1928e4658085f9b6c"}
N_CLASSIFY = 3000
N_GATE = 2000
N_RSS = 600
BATCH = 500

DRIVER = r"""
const RealDate = Date;
let NOW = 0;
class FakeDate extends RealDate {
  constructor(...a) { if (a.length === 0) super(NOW); else super(...a); }
  static now() { return NOW; }
}
globalThis.Date = FakeDate;
const { readFileSync } = require("node:fs");
const P = JSON.parse(readFileSync(0, "utf8"));
const C = require("./src/lib/echo/classify.js");
const G = require("./src/lib/echo/gate.js");
const SRC = readFileSync("./scripts/echo-sidecar.mjs", "utf8");
function extract(name) {
  const i = SRC.indexOf("function " + name + "(");
  let j = SRC.indexOf("{", SRC.indexOf(")", i));
  let depth = 0, k = j;
  for (; k < SRC.length; k++) {
    if (SRC[k] === "{") depth++;
    else if (SRC[k] === "}") { depth--; if (depth === 0) break; }
  }
  return SRC.slice(i, k + 1);
}
const HANDLE = /const HANDLE = "([^"]+)";/.exec(SRC)[1];
const R = new Function("HANDLE", [extract("stripHtml"), extract("parseRss")].join("\n") +
  "\nreturn { stripHtml, parseRss };")(HANDLE);
const out = P.cases.map((c) => {
  NOW = c.now || 0;
  if (c.part === "classify") return C.classifyEcho(c.text);
  if (c.part === "gate") return G.echoPaperGate(c.input);
  try { return { items: R.parseRss(c.xml) }; } catch (e) { return { error: String(e && e.name) }; }
});
console.log(JSON.stringify(out));
"""

WORDS = ["I bought", "i bought", "We bought", "publicly bought", "starter position in", "Starter here", "I added",
         "I've added", "I have added", "I'm adding", "adding to my position", "happy holding", "I am holding",
         "no concerns", "I will buy", "I'll buy", "plan to add", "I plan to buy", "don't rush", "staying patient",
         "buying opportunity", "buy zone", "I'm near a buy", "I never bought", "didn't buy", "did not buy",
         "hasn't gone to plan", "on Monday", "this week", "last week", "yesterday", "last 3 weeks",
         "another great week", "every buy posted", "up over 40%", "going into next week", "RT by @x:", "target",
         "support", "the 0.618 fib", "near the 200 DMA", "RSI", "ATR", "NFA", "", " ", "﻿", " ",
         "\u0085", "\u001c", "café", "I boughté", "&amp;", "<b>"]
TICKERS = ["$NVDA", "$TSLA", "$AMD", "$PLTR", "$RSI", "$EMA", "$TARGET", "$ABCDEF", "$ab", "$X", "$SOFI", "$HIMS",
           "$RKLB", "NVDA", "nvda", "$BRK.B", "$I", "$A"]


def classify_case(rnd):
    parts = []
    for _ in range(rnd.randint(0, 9)):
        parts.append(rnd.choice(WORDS) if rnd.random() < 0.6 else rnd.choice(TICKERS))
    sep = rnd.choice([" ", "  ", "\n", "  ", "\t"])
    text = sep.join(parts)
    if rnd.random() < 0.1:
        text = " " + text + rnd.choice([" ", "﻿", "　"])
    if rnd.random() < 0.08:
        text = "I bought " + rnd.choice(["nvda", "Tsla", "abcdef", "x1"]) + " today"
    return {"part": "classify", "text": text}


def gate_case(rnd):
    def maybe(lo, hi):
        return rnd.choice([None, round(rnd.uniform(lo, hi), 4), 0.02, -0.05, 0.04, 0.08, 0])
    return {"part": "gate", "input": {
        "weekday": rnd.random() < 0.85, "hour": rnd.randint(0, 23), "minute": rnd.choice([0, 30, 45, 46, 59]),
        "kind": rnd.choice(["BUY", "ADD", "WATCH"]), "boughtToday": rnd.random() < 0.3,
        "hasPosition": rnd.random() < 0.2, "price": rnd.choice([0, 10.0, round(rnd.uniform(1, 200), 2)]),
        "entry": rnd.choice([None, 0, 10.0, 9.95, round(rnd.uniform(1, 200), 2)]), "vs21": maybe(-0.1, 0.1),
        "ret5": maybe(-0.1, 0.15)}}


def _pub(rnd):
    t = 1_791_000_000 + rnd.randint(0, 3_000_000)
    from email.utils import formatdate
    return formatdate(t, usegmt=True)


def rss_case(rnd):
    items = []
    for _ in range(rnd.randint(0, 6)):
        sid = str(rnd.randint(10 ** 18, 10 ** 19))
        title = rnd.choice(["I bought $NVDA here", "RT by @EchoAnalysis: $TSLA", "rt by x", "Starter position $AMD",
                            "<![CDATA[I added $PLTR]]>", "", "plain note"])
        desc = rnd.choice(["", "<p>I bought $NVDA<br/>at the 0.618</p>", "<![CDATA[<a href='x'>$TSLA</a> starter "
                           "here]]>", "&amp; &lt;b&gt; I added $SOFI", "  \n "])
        creator = rnd.choice([None, "@EchoAnalysis", "EchoAnalysis", "@someoneelse", "@echoanalysis"])
        guid = rnd.choice([f"https://nitter.net/EchoAnalysis/status/{sid}#m", sid, "", f"  {sid}  "])
        link = rnd.choice([f"https://nitter.net/EchoAnalysis/status/{sid}#m", f"https://nitter.cz/x/status/{sid}",
                           "https://nitter.net/EchoAnalysis", ""])
        pub = rnd.choice([_pub(rnd), _pub(rnd), None])
        x = "<item>"
        x += f"<title>{title}</title>"
        if creator is not None:
            x += f"<dc:creator>{creator}</dc:creator>"
        x += f"<description>{desc}</description>"
        if guid:
            x += f"<guid isPermaLink=\"false\">{guid}</guid>"
        if link:
            x += f"<link>{link}</link>"
        if pub:
            x += f"<pubDate>{pub}</pubDate>"
        x += "</item>"
        items.append(x)
    head = "<?xml version=\"1.0\"?><rss><channel><title>Echo</title>"
    return {"part": "rss", "xml": head + "".join(items) + "</channel></rss>", "now": 1_792_000_000_000}


def port(c):
    if c["part"] == "classify":
        return E.classify_echo(c["text"])
    if c["part"] == "gate":
        return E.echo_paper_gate(**c["input"])
    try:
        return {"items": E.parse_rss(c["xml"], c["now"])}
    except ValueError:
        return {"error": "RangeError"}


def run():
    rnd = random.Random(20261018)
    cases = [classify_case(rnd) for _ in range(N_CLASSIFY)] + [gate_case(rnd) for _ in range(N_GATE)] + \
        [rss_case(rnd) for _ in range(N_RSS)]
    diffs, ident, stats = [], 0, {}
    tree = None
    try:
        tree = stage("Author_DESK", "/home/user/Author-desk", dict(TS, **SCRIPTS))
        transpile_ts(tree, list(TS))
        for i in range(0, len(cases), BATCH):
            chunk = cases[i:i + BATCH]
            theirs = node_run(tree, DRIVER, {"cases": chunk}, name="__driver.cjs")
            for j, (c, t) in enumerate(zip(chunk, theirs)):
                d = same(port(c), t)
                if d:
                    diffs.append({"part": c["part"], "case": i + j, "diff": [list(map(str, x)) for x in d[:5]]})
                else:
                    ident += 1
    finally:
        if tree:
            cleanup(tree)
    for c in cases:
        r = port(c)
        if c["part"] == "classify":
            key = "classify_" + r["kind"] + ("_paper" if r["paper"] else "")
        elif c["part"] == "gate":
            key = "gate_" + ("ok" if r["ok"] else "held")
        else:
            key = "rss_items" if "items" in r else "rss_error"
            stats["rss_posts"] = stats.get("rss_posts", 0) + len(r.get("items") or [])
        stats[key] = stats.get(key, 0) + 1
    res = {"sleeve": "Author_echo", "cases": len(cases), "identical": ident, "diffs": diffs[:40],
           "n_diffs": len(diffs), "stats": stats,
           "source": {"repo": "Author-desk", "commit": COMMIT, "files": dict(TS, **SCRIPTS)},
           "method": "source TypeScript (and echo-sidecar.mjs's stripHtml / parseRss, read verbatim) under Node 22 vs "
                     "desk/sleeves/Author/echo.py, exact JSON equality",
           "sleeves": ["Author_echo_swing"]}
    write_receipt("Author_echo", res)
    return res
