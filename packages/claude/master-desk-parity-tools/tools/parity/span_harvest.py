"""span_harvest: the span_harvest_unified sleeve (desk/sleeves/families/prediction_markets.py) vs the source engine
itself (span_harvest_unified.py @649e71f1, vendored byte-exact, hash-pinned by tests/test_vendor.py) on the source's
own corpus — TimePortal's public clean_tapes release (the tapes the source's study replays) and its sport clocks.

  causal   for every corpus tape x every one of the 14 frozen profiles: the sleeve's live path — the state machine
           replayed on the tape so far at successive prints (each action carried out once, by key) — against
           simulate_profile on the complete tape. Every action the full replay takes before the end must appear,
           identically (print, rung / sleeve, reason, price, capital / shares), on the first prefix that holds its
           print; no prefix may take an action the full replay does not. The settlement (the end itself) is the one
           action only the resolved tape can carry.
  select   for every corpus tape after the replay's 30-match warm-up, in the replay's order: the sleeve's PZOE call
           (select() on the corpus matches that started before it) against replay_unified()'s decision for that
           tape — reason, profile and group.
  layout   counted, not compared: the live tape layout (the first print as the opening, the end at the first run of
           3 prints >= 99.9c / <= 0.1c) against the release's own fields (its opening on the trade + subtick basis,
           its verified ends) — named divergence 2.

    SPAN_CACHE=<dir with clean_tapes.json + game_time_by_sport.json, downloaded when missing>
    python3 -m tools.parity.run span_harvest"""
import hashlib
import json
import os
import random
import time
from dataclasses import replace

from desk.feedlib import polymarket as PM
from desk.sleeves.families import prediction_markets as P
from desk.vendor.span_harvest import span_harvest_unified as SH

from . import write_receipt

PREFIX_CUTS = 2


def _corpus():
    d = os.environ.get("SPAN_CACHE") or os.path.join(os.environ.get("TMPDIR", "/tmp"), "span_harvest_parity")
    tp, clock = PM.corpus(d, time.time())
    payload, tapes, rejected = SH.load_tapes(tp)
    return payload, tapes, rejected, SH.load_clock_reference(clock, tapes), tp


def _rows(tr):
    ents = [("e", r["i"], r["rung"], r["price"], r["capital"], r["limit"]) for r in tr.entries]
    exs = [("x", r["i"], r["sleeve"], r["reason"], r["price"], r["shares"]) for r in tr.exits]
    return ents, exs


def prefix(tape, k):
    """the tape as a live pass sees it after k prints: no end, no result, no settlement event yet."""
    return replace(tape, prices=tape.prices[:k], times=tape.times[:k], settlement_i=None, end_recorded=False,
                   result=None)


def causal_case(tape, profile, clock, rnd):
    full = SH.simulate_profile(tape, profile, clock)
    f_ent, f_exit = _rows(full)
    n = tape.last_tradable_i + 1
    marks = sorted({r[1] + 1 for r in f_ent + f_exit if r[1] + 1 <= n} | {n} |
                   {rnd.randint(1, n) for _ in range(PREFIX_CUTS)} if n >= 1 else set())
    seen = {}
    for k in marks:
        tr = SH.simulate_profile(prefix(tape, k), profile, clock)
        ents, exs = _rows(tr)
        for r in ents + exs:
            seen.setdefault(r, k)
            if r[1] >= k:
                return f"action at print {r[1]} on a {k}-print prefix: {r}"
    want = [r for r in f_ent + f_exit if not (r[0] == "x" and r[3] == "SETTLEMENT")]
    got = sorted(seen, key=lambda r: (r[1], r[0], str(r[2])))
    want_s = sorted(want, key=lambda r: (r[1], r[0], str(r[2])))
    extra = [r for r in got if r not in want]
    missing = [r for r in want_s if r not in seen]
    if extra or missing:
        return {"extra": extra[:3], "missing": missing[:3]}
    return None


def layout_case(rec):
    """the release record laid out the live way (named divergence 2): (same opening, same end) counts."""
    m = {"event_id": str(rec.get("id")), "sport": str(rec.get("sport", "unknown")).lower(),
         "start_ts": rec.get("start_ts") or rec["t"][0], "result": rec.get("result") if rec.get("end_recorded") else None,
         "prints": [[t, p] for t, p in zip(rec["t"], rec["p"])]}
    if m["result"] == "won" and rec.get("settlement_i") is not None:
        i = int(rec["settlement_i"])
        m["prints"] = m["prints"][:i] + m["prints"][i + 1:]
    live = SH.Tape.from_record(P.live_record(m))
    src = SH.Tape.from_record(rec)
    if live is None or src is None:
        return None
    return {"same_open": live.opening == src.opening,
            "same_end": live.last_tradable_i == src.last_tradable_i and live.terminal_price == src.terminal_price}


def run():
    payload, tapes, rejected, clock, tp_path = _corpus()
    sha = hashlib.sha256(open(tp_path, "rb").read()).hexdigest()
    rnd = random.Random(20261016)
    diffs, n, same = [], 0, 0
    stats = {"tapes": len(tapes), "profiles": len(P.PROFILES), "actions": {"entries": 0, "exits": 0},
             "selection_reasons": {}, "layout": {"records": 0, "same_open": 0, "same_end": 0}}
    for tape in tapes:
        for profile in P.PROFILES:
            d = causal_case(tape, profile, clock, rnd)
            n += 1
            if d is None:
                same += 1
            else:
                diffs.append({"kind": "causal", "match": tape.match_id, "profile": profile.profile_id, "diff": d})
            if profile.profile_id == "apzi_base":
                tr = SH.simulate_profile(tape, profile, clock)
                stats["actions"]["entries"] += len(tr.entries)
                stats["actions"]["exits"] += len(tr.exits)
    n_causal, same_causal = n, same
    rep = SH.replay_unified(tapes, clock)
    ordered = sorted(tapes, key=lambda t: (t.start_ts, t.match_id))
    for i, (tape, dec) in enumerate(zip(ordered, rep["decisions"])):
        if i < SH.Gate().warmup_matches:
            continue
        prof, sel = P.select(tape, ordered, clock)
        ours = {"reason": sel["reason"], "profile": prof.profile_id if prof else None,
                "group": list(sel.get("group") or []) or None}
        src_sel = dec.get("selection") or {}
        theirs = {"reason": src_sel.get("reason", dec.get("reason")), "profile": dec.get("profile_id"),
                  "group": list(src_sel.get("group") or []) or None}
        n += 1
        stats["selection_reasons"][ours["reason"]] = stats["selection_reasons"].get(ours["reason"], 0) + 1
        if ours == theirs:
            same += 1
        else:
            diffs.append({"kind": "select", "match": tape.match_id, "ours": ours, "theirs": theirs})
    for rec in payload.get("matches") or []:
        if not isinstance(rec, dict) or rec.get("omitted") or not rec.get("p"):
            continue
        r = layout_case(rec)
        if r is None:
            continue
        stats["layout"]["records"] += 1
        stats["layout"]["same_open"] += int(r["same_open"])
        stats["layout"]["same_end"] += int(r["same_end"])
    res = {"sleeve": "span_harvest", "cases": n, "identical": same, "diffs": diffs[:40], "n_diffs": len(diffs),
           "stats": dict(stats, causal_cases=n_causal, causal_identical=same_causal,
                         select_cases=n - n_causal, select_identical=same - same_causal,
                         replay_summary={k: rep["summary"].get(k) for k in ("matches", "filled", "resolved_filled",
                                                                             "net", "mean_net_per_match")}),
           "method": "the sleeve's prefix-by-prefix state-machine path and its PZOE call vs simulate_profile / "
                     "replay_unified of span_harvest_unified.py (blob 6ab429a4) on TimePortal's public release",
           "corpus": {"release_id": payload.get("release_id"), "generated_utc": payload.get("generated_utc"),
                      "sha256": sha, "loaded_tapes": len(tapes), "rejected_or_omitted": rejected},
           "named_divergences": 5, "sleeves": ["span_harvest_unified"]}
    write_receipt("span_harvest", res)
    return res
