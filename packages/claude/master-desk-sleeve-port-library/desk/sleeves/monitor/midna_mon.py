"""midna — three monitors over the midna desk's own code (midna@43f08f96), vendored byte-exact under
desk/vendor/midna_mon and executed under Node by desk/feedlib/node/midna.mjs; never reimplemented.

  mon_midna_3tf_vwap_pullback       src/lib/vwap/strategy.ts liveRead, as the equity journal's readVwap runs it:
                                    each COMPARE_UNIVERSE name's completed 15m regular-session tape (journal.ts
                                    sessionBars) -> signal / pullback / trend (below: no state)
  mon_midna_weekly_8_20_50_pullback src/lib/felipe/pullback.ts lastWeekState, as readFelipe runs it: each
                                    FELIPE_ETFS daily tape -> completed weeks, EMA 8 > 20 > 50 stack, the weekly
                                    pullback signal; QQQ's qldState (the QLD trend) travels in every read
  mon_midna_tsmom_forms             scripts/tsmom-forms.ts FORMS (12-1 / 6 / 6-and-12 sign, rate of change,
                                    Donchian 20, golden cross, year high) over the DIVERSIFIED panel aligned to
                                    SPY's sessions, at the newest session

Named divergences:
  * cadence: the journal read its data files when it wrote the day log, the forms ran as a study; here the VWAP read
    every 15 minutes in the session, the weekly pullback and the forms after each close;
  * tapes: the desk's Yahoo bars (15m regular session; daily — Nasdaq while Yahoo refuses this host) stand in for
    the midna producers' files (vwap-15m.json, the equity-desk daily series, the backtest bar cache); the forms'
    adjusted close is Yahoo's adjclose, the close itself when the provider gives none (Nasdaq);
  * the forms study's stock registry panel (quant-research/registry/names.csv, liquidity-filtered) is not part of
    the monitor: the in-script DIVERSIFIED panel is.
Removed gates: none (reads only; the journal's "Reading only")."""
import os
import re
from datetime import datetime

from ...feedlib import node_source as NS
from ...util import ET
from .base import MonitorSpec, Obs

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "midna_mon")
REPO = {"repo": "midna", "ref": "entire", "commit": "43f08f96fce33ee67521002e09f8bc7534cfe264"}


def _list(rel, pattern):
    src = open(os.path.join(VENDOR, rel), encoding="utf-8").read()
    return tuple(re.findall(r'"([^"]+)"', re.search(pattern, src, re.S).group(1)))


COMPARE_UNIVERSE = _list("src/lib/equity/options-surface.ts", r"export const COMPARE_UNIVERSE = \[(.*?)\]")
FELIPE_ETFS = _list("src/lib/felipe/pullback.ts", r"export const FELIPE_ETFS = \[(.*?)\]")
DIVERSIFIED = _list("scripts/tsmom-forms.ts", r"const DIVERSIFIED = \[(.*?)\]")


def _date(t):
    return datetime.fromtimestamp(float(t), tz=ET).strftime("%Y-%m-%d")


def _days(rows):
    return [{"date": _date(b["t"]), "open": b.get("o") or 0, "high": b.get("h") or 0, "low": b.get("l") or 0,
             "close": b.get("c") or 0} for b in rows or [] if b.get("c") is not None]


def run(payload):
    NS.verify("midna_mon/", 7)
    return NS.run("midna.mjs", payload, timeout=300)


def eval_vwap(view, mon):
    rows = (view.bars.get("15m") or {})
    reqs = [{"symbol": s, "rows": [{"t": float(b["t"]), "open": b.get("o") or 0, "high": b.get("h") or 0,
                                    "low": b.get("l") or 0, "close": b.get("c") or 0, "volume": b.get("v") or 0}
                                   for b in rows.get(s) or []]}
            for s in mon.CONFIG.universe if rows.get(s)]
    if not reqs:
        return {}
    res = run({"now": int(view.now * 1000), "vwap": reqs})["vwap"]
    out = {}
    for s, r in res.items():
        if not r:
            continue
        if r["state"] == "below":
            out[s] = None
            continue
        bar_t = datetime.strptime(r["date"], "%Y-%m-%d").replace(tzinfo=ET).timestamp() + r["minute"] * 60
        out[s] = Obs(r["state"], "3TF VWAP %s: close %s vs session VWAP %s, hour VWAP %s, prior-day VWAP %s, RSI %s"
                     % (r["state"], r["close"], r["sessionVwap"], r["hourVwap"], r["dailyVwap"], r["rsi"]),
                     bar_t, r, r["close"])
    return out


def eval_felipe(view, mon):
    daily = view.bars.get("1d") or {}
    reqs = [{"symbol": s, "days": _days(daily.get(s))} for s in mon.CONFIG.universe if daily.get(s)]
    if not reqs:
        return {}
    res = run({"now": int(view.now * 1000), "felipe": reqs, "qqq": _days(daily.get("QQQ"))})
    qld = res.get("qld")
    out = {}
    for s, r in res["felipe"].items():
        if not r:
            continue
        state = "signal" if r["signal"] else "stacked" if r["stacked"] else None
        if state is None:
            out[s] = None
            continue
        bar_t = datetime.strptime(r["date"], "%Y-%m-%d").replace(tzinfo=ET).timestamp()
        out[s] = Obs(state, "weekly 8/20/50 %s: week %s close %s low %s RSI %s" % (state, r["date"], r["close"],
                                                                                 r["low"], r["rsi"]),
                     bar_t, dict(r, qld=qld), r["close"])
    return out


def eval_tsmom(view, mon):
    daily = view.bars.get("1d") or {}
    reqs = []
    for s in mon.CONFIG.universe:
        bl = daily.get(s) or []
        if not bl:
            continue
        reqs.append({"symbol": s, "rows": [[_date(b["t"]), b.get("ac") or b.get("c"), b.get("c"), b.get("h") or 0,
                                            b.get("l") or 0, b.get("v") or 0] for b in bl if b.get("c")]})
    if not reqs:
        return {}
    res = run({"now": int(view.now * 1000), "tsmom": reqs})["tsmom"]
    out = {}
    for s, r in res.items():
        if not r["forms"]:
            out[s] = None
            continue
        bar_t = datetime.strptime(r["date"], "%Y-%m-%d").replace(tzinfo=ET).timestamp()
        out[s] = Obs("+".join(r["forms"]), "TSMOM forms on: %s (12m %s, 6m %s)" % (", ".join(r["forms"]),
                                                                              r["ret252"], r["ret126"]),
                     bar_t, r)
    return out


SPECS = [
    MonitorSpec(sleeve_id="mon_midna_3tf_vwap_pullback", title="Three-timeframe VWAP pullback",
                source=dict(REPO, path="src/lib/vwap/strategy.ts", blob_sha="bb656bff24ed00e32a2eea368b770957458d51b6",
                            line_start=1, line_end=386),
                evaluate=eval_vwap, universe=COMPARE_UNIVERSE,
                needs={"bars": [{"source": "yahoo", "interval": "15m", "n": 600}]},
                schedule="rth,!close+0:close+25", cadence_s=900, mode="state", params={"executed": "midna_mon"}),
    MonitorSpec(sleeve_id="mon_midna_weekly_8_20_50_pullback", title="Weekly 8/20/50 price pullback",
                source=dict(REPO, path="src/lib/felipe/pullback.ts", blob_sha="da620bd787610653ccb4b3b46ba46e828a3b6944",
                            line_start=1, line_end=674),
                evaluate=eval_felipe, universe=FELIPE_ETFS,
                needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 1600},
                                {"source": "yahoo", "interval": "1d", "n": 1600, "symbols": ["QQQ"]}]},
                schedule="after_close+20:after_close+300", cadence_s=1800, mode="state",
                params={"executed": "midna_mon"}),
    MonitorSpec(sleeve_id="mon_midna_tsmom_forms", title="Time-series momentum forms",
                source=dict(REPO, path="src/lib/research/tsmom.ts", blob_sha="53b332900fc42556a7063b0161532e089e9a9297",
                            line_start=1, line_end=409),
                evaluate=eval_tsmom, universe=DIVERSIFIED,
                needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 1600}]},
                schedule="after_close+20:after_close+300", cadence_s=1800, mode="state",
                params={"executed": "midna_mon"}),
]
