"""sleeve_midna — the Midna port's fire producer of the Lazarus Test desk (quant-research-backup main ce5ccbcd, blob 49c0524b,
Author-research/shadow/paper_sleeve/sleeve_midna.py 1.0.14), for the midna_tensor Lazarus lanes it feeds, ported
line for line (_fire, forward_fires) and, for the lane the producer emitted nothing for, built from the lane's
written rule:

  s_mn_w_cyan_breadth  forward_fires: every row the Midna forward account w-cyan-breadth has staged (its scan hits
                       on names it does not hold, for the session after the signal) -> a fire keyed
                       SYM:s_mn_w_cyan_breadth:x:<signal day>, fire bar the signal day 09:30 ET, plan "time exit 126
                       sessions" (the account's holdSessions), size class test; the staged rows are the account
                       midna_w_cyan_quiet_tape's (desk/sleeves/midna/forward.py) — the source read Midna's state.json
                       forward.accounts[...].staged, the same rows
  s_mn_nostop          no producer code: sleeve_midna 1.0.14 declares the lane (SLEEVES: "Midna Nostop", kind 1h,
                       "60 bars no stop", "same Midna buyBlockReason as Hourly (shadow twin)", source "Midna shadow.ts
                       markNostop") and the Lazarus config gives its rule ("Midna plan: no stop / time exit 60 bars",
                       hold unit 1h) but build_midna_fires emits no s_mn_nostop fire. Built from that rule: the Midna
                       Hourly book's 1H fires (the hourly watch's inbox — the 1H basket fires midna_hourly_playbook
                       trades), each as an s_mn_nostop fire keyed SYM:s_mn_nostop:<fire key>, fire bar the 1H bar's
                       ET start, close the fire close, plan no stop / time exit 60 bars
  s_mn_hourly_1d       hourly_fires (lanes 1d / 1w; its 1h lane is midna_hourly_playbook's watch inbox): the
  s_mn_hourly_1w       canonical Tensor v698 tracker's fires of the lane — Author-research shadow/live/
                       latest_fires_v3.json with the tracker ledger shadow/log/ledger.jsonl (tradeable, bar_source,
                       cal_plans, meta decile / score) under the Lazarus inputs root that the tracker job writes —
                       tradeable Yahoo-sourced fires with an active unit, ranked by decile x 1e6 + score, each keyed
                       SYM:<lane>:<tracker key> on rules.ts planForNewEntry's plan (calibrated stop / max bars, default
                       40 sessions for 1D and 52 weeks for 1W); verbatim (parity tools/parity/midna_fires.py against
                       the vendored sleeve_midna.hourly_fires)

Removed: the plan stop of 40% on the forward fires ("40% adverse circuit", FORWARD_RUIN_PCT — Midna's forward
circuit breaker, removed from the forward accounts too) and the local / Midna forward halts (forward_lane_halted, a
kill switch): the fires carry stop 99 (none).

Named divergences: the producer file (shadow/paper_sleeve/live/midna/midna_fires_v1.json, synced from Midna's
signal files by `gh api`) is this feed, computed in-pass; the tracker engine's Yahoo canonical close of the signal
day (_engine_close) is the lane's own close of the fire day from the desk's daily bars (desk.run_pass fills a fire
without a close that way); the alt-data tag columns (all None for Midna fires) are not carried."""
import json
import os
from datetime import datetime

from ..util import ET

SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "ce5ccbcd3634f79358eb096b6e43271989bb27d0",
          "blob": "49c0524b74e95d80bcfccf6c2633f0db1ea48c60",
          "path": "Author-research/shadow/paper_sleeve/sleeve_midna.py", "version": "1.0.14"}
FORWARD_LANES = {"w-cyan-breadth": ("s_mn_w_cyan_breadth", "midna_w_cyan_quiet_tape")}
NOSTOP_PLAN = {"scheme": "no stop / time exit 60 bars", "stop_pct": 99.0, "first_target_pct": None,
               "sell_fraction": 1.0, "rest": "time", "max_bars": 60, "exit_on_engine_sell": False}


def fire_bar_0930(day):
    """str(pd.Timestamp(f"{day} 09:30").tz_localize("America/New_York")) — e.g. 2026-10-15 09:30:00-04:00."""
    t = datetime.fromisoformat(f"{day}T09:30:00").replace(tzinfo=ET)
    off = t.utcoffset()
    sign = "-" if off.total_seconds() < 0 else "+"
    m = int(abs(off.total_seconds()) // 60)
    return f"{day} 09:30:00{sign}{m // 60:02d}:{m % 60:02d}"


def et_string(epoch):
    t = datetime.fromtimestamp(float(epoch), tz=ET)
    off = t.utcoffset()
    sign = "-" if off.total_seconds() < 0 else "+"
    m = int(abs(off.total_seconds()) // 60)
    return t.strftime("%Y-%m-%d %H:%M:%S") + f"{sign}{m // 60:02d}:{m % 60:02d}"


def make_fire(sym, lane, day, unit, plan, strategy, strategies, close=None, extra=None, fire_bar=None):
    """sleeve_midna._fire (the fields the lane reads)."""
    d = {"key": f"{sym}:{lane}:x:{day}", "sym": sym, "lane": lane, "fire_bar": fire_bar or fire_bar_0930(day),
         "close": close, "tradeable": True, "cal_units": [unit], "cal_units_paused": [], "cal_plans": {unit: plan},
         "bar_source": "yahoo:midna-signal-file", "midna_signal_close": close, "strategy": strategy,
         "strategies": strategies, "size_class": "test", "D": day, "midna_port": True, "midna_start_flat": True,
         "feed": "sleeve_midna", "cal_priority": 0, "paper_families": ["midna"]}
    if extra:
        d.update(extra)
    return d


def forward_fires(state_of):
    """forward_fires() for the forward lanes this desk runs; state_of(sleeve_id) -> that forward account's state."""
    out = []
    for mid, (lane, sid) in FORWARD_LANES.items():
        st = state_of(sid) or {}
        hs = 126
        for row in st.get("staged") or []:
            if not row.get("sym") or not row.get("signalDay"):
                continue
            plan = {"scheme": f"time exit {hs} sessions", "stop_pct": 99.0, "first_target_pct": None,
                    "sell_fraction": 1.0, "rest": "time", "max_bars": hs, "exit_on_engine_sell": False}
            out.append(make_fire(row["sym"], lane, row["signalDay"], "s-" + lane[2:].replace("_", "-"), plan,
                                 f"Midna forward {mid} (Midna port)", [f"Midna forward {mid}"],
                                 extra={"midna_flag": row.get("flag"), "midna_score": row.get("score")}))
    return out


def nostop_fires(watch_doc):
    """the s_mn_nostop lane: the Hourly book's 1H basket fires (the watch inbox) on the no-stop / 60-bar plan."""
    from ..sleeves.midna.hourly import ms_of
    out = []
    for raw in (watch_doc or {}).get("inbox") or []:
        if raw.get("lane") != "1h" or raw.get("tradeable") is not True:
            continue
        t = ms_of(raw.get("fireBar"))
        if t is None or not raw.get("sym"):
            continue
        fb = et_string(t)
        f = make_fire(raw["sym"], "s_mn_nostop", fb[:10], "s-mn-nostop", dict(NOSTOP_PLAN),
                      "Midna Nostop (Midna port)", ["Midna shadow.ts markNostop", "Midna rules.ts Hourly 1h"],
                      close=raw.get("fireClose"),
                      extra={"key": f"{raw['sym']}:s_mn_nostop:{raw['key']}", "fire_bar": fb, "midna_tf": "1h",
                             "bar_source": raw.get("barSource") or "yahoo:canonical", "gap20": raw.get("gap20"),
                             "first_of_setup": raw.get("firstOfSetup"), "inbox_key": raw["key"]})
        out.append(f)
    return out


# -- the Hourly book's 1D / 1W lanes: sleeve_midna.hourly_fires on the canonical tracker's files -------------------
HOURLY_LANE_MAP = {"1d": ("s_mn_hourly_1d", "s-mn-hourly-1d"), "1w": ("s_mn_hourly_1w", "s-mn-hourly-1w")}
_LEDGER = {}      # ledger path -> {"tag", "end", "tail", "at": {key: (offset, length) of its last fire record}}
_TAIL = 64


def _scan(f, start, at):
    """index the fire records from byte `start`: each key's last fire-record line by offset (the records themselves
    are parsed again on lookup, so the pass loop never holds the ledger). Returns the end of the last complete line;
    a final line still being written is indexed when it parses and scanned again next time."""
    f.seek(start)
    pos = end = start
    for raw in f:
        n = len(raw)
        if b'"type":"fire"' in raw or b'"type": "fire"' in raw:
            try:
                r = json.loads(raw)
            except ValueError:
                r = None
            if isinstance(r, dict) and r.get("type") == "fire":
                at[r.get("key")] = (pos, n)
        pos += n
        if raw.endswith(b"\n"):
            end = pos
    return end


def tracker_index(ledger_path, keys):
    """sleeve_midna._tracker_index: the ledger's fire records by key, the last record of a key winning. The index
    holds line offsets only and follows the append-only ledger incrementally (a ledger that shrank or whose bytes
    before the indexed end changed is indexed again from the start)."""
    if not keys or not os.path.exists(ledger_path):
        return {}
    st = os.stat(ledger_path)
    tag = (st.st_size, st.st_mtime_ns)
    with open(ledger_path, "rb") as f:
        memo = _LEDGER.get(ledger_path)
        if memo is None or memo["tag"] != tag:
            if memo is not None:
                same = st.st_size >= memo["end"]
                if same:
                    f.seek(max(0, memo["end"] - _TAIL))
                    same = f.read(min(_TAIL, memo["end"])) == memo["tail"]
                if not same:
                    memo = None
            if memo is None:
                memo = {"end": 0, "tail": b"", "at": {}}
            memo["end"] = _scan(f, memo["end"], memo["at"])
            f.seek(max(0, memo["end"] - _TAIL))
            memo["tail"] = f.read(min(_TAIL, memo["end"]))
            memo["tag"] = tag
            _LEDGER[ledger_path] = memo
        out = {}
        for k in keys:
            if k in memo["at"]:
                off, n = memo["at"][k]
                f.seek(off)
                out[k] = json.loads(f.read(n))
        return out


def plan_for_new_entry(lane, unit, stop_pct, max_bars):
    """rules.ts planForNewEntry (sleeve_midna.plan_for_new_entry): 1h-basket -> no stop / 60 bars; else calibrated
    stop / max bars (default 40, 1w 52)."""
    if lane == "1h" and unit == "1h-basket":
        return ("no stop / time exit 60 bars", 99.0, 60)
    mb = max_bars if max_bars else (52 if lane == "1w" else 40)
    return (f"calibrated stop {stop_pct}% / {mb} bars" if stop_pct is not None and stop_pct < 99 else "calibrated plan",
            float(stop_pct) if stop_pct is not None else 99.0, int(mb))


def hourly_fires(shadow_dir):
    """sleeve_midna.hourly_fires for the 1D and 1W lanes: the tracker's tradeable Yahoo-sourced fires of the lane,
    ranked by the ledger's decile x 1e6 + score (else priority), each on rules.ts planForNewEntry's plan."""
    lf = os.path.join(shadow_dir, "live", "latest_fires_v3.json")
    if not os.path.exists(lf):
        return []
    with open(lf) as f:
        all_rows = json.load(f).get("fires") or []
    out = []
    for tf, (lane_id, unit_name) in HOURLY_LANE_MAP.items():
        rows = [r for r in all_rows if r.get("lane") == tf]
        idx = tracker_index(os.path.join(shadow_dir, "log", "ledger.jsonl"), {r.get("key") for r in rows})
        cand = []
        for r in rows:
            led = idx.get(r.get("key")) or {}
            unit = str(r.get("active_units") or "").split(",")[0].strip()
            if not unit or not (led.get("tradeable", r.get("tradeable")) is True):
                continue
            if not str(led.get("bar_source") or r.get("bar_source") or "").startswith("yahoo"):
                continue
            pl = (led.get("cal_plans") or {}).get(unit) or {}
            meta = led.get("meta") or {}
            dec = meta.get("decile") if isinstance(meta.get("decile"), (int, float)) else 5.5
            sc = meta.get("score") if isinstance(meta.get("score"), (int, float)) else (r.get("priority") or 0)
            cand.append((dec * 1_000_000 + sc, r, unit, pl, led))
        cand.sort(key=lambda c: (-c[0], c[1].get("symbol") or ""))
        for rank, r, unit, pl, led in cand:
            scheme, stop, mb = plan_for_new_entry(tf, unit, pl.get("stop_pct", r.get("stop_pct")),
                                                  pl.get("max_bars", r.get("max_hold_bars")))
            fb = str(r.get("time_et"))
            sym = r.get("symbol")
            out.append(make_fire(sym, lane_id, fb[:10], unit_name,
                                 {"scheme": scheme, "stop_pct": stop, "first_target_pct": None, "sell_fraction": 1.0,
                                  "rest": "time", "max_bars": mb, "exit_on_engine_sell": False},
                                 f"Midna Hourly {tf.upper()} (Midna port)", [f"Midna rules.ts Hourly {tf}"],
                                 close=r.get("entry_ref"),
                                 extra={"fire_bar": fb, "close": r.get("entry_ref"),
                                        "bar_source": r.get("bar_source") or "yahoo:canonical",
                                        "key": f"{sym}:{lane_id}:{r.get('key')}", "midna_rank": rank,
                                        "tracker_key": r.get("key"), "midna_tf": tf, "gap20": None,
                                        "first_of_setup": None}))
    return out


def feed_fires(feeds, sleeve, now, arg=None):
    """{"fires_midna": {"fires": [...]}, "oldest_fire_day": ...} — the lanes' pass inputs."""
    from ..sleeves.families.lazarus import inputs_dir, oldest_fire_day, ts
    eng = getattr(sleeve, "engine", None)
    store = getattr(eng, "store", None)
    fires = forward_fires(lambda sid: store.sleeve_get(sid) if store is not None else {})
    fires += nostop_fires(feeds.get("midna_watch", sleeve, now))
    fires += hourly_fires(os.path.join(inputs_dir(feeds, sleeve), "shadow"))
    return {"fires_midna": {"fires": fires}, "oldest_fire_day": oldest_fire_day(ts(now), 5)}
