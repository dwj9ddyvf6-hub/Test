"""FEED-05 and FEED-06 (AUDIT_FEED.md; exp1 item 7): the Lazarus lanes' fire population as the lab's shadow, from
fix1's FEED-01 record. Nothing here trades, routes, sizes or changes a lane.

  fires(rec)    the FEED-01 record (desk/sleeves/families/lazarus.py _outcome_notes): one signal observation per fire key
                each time its outcome changes, keyed lzo:<fire key>:<outcome>:<epoch> (outcomes: intent, cap, log_only,
                skip_size, held, not_in_window, wait, closed_day, blocked, shadow_only, invalid)
                -> {(lane, fire key): {"sym", "first_at", "timeline": [(pass time, outcome)]}}
  draws(fires)  FEED-05's seeded draw: at each pass where a lane filled slots (fires newly at outcome intent: its
                alphabetical K-fill), as many fires drawn at random (random.Random("feed05|<lane>|<pass>")) among the
                fires eligible as of that pass (outcome intent or cap) that the draw has not taken before. The draw
                fills the incumbent's slot count pass by pass, so the two sets differ only in which fires they hold
  rows          one per fire (arm "lazarus") in the session of its first record: its lane, key, symbol, outcomes,
                whether the incumbent gave it a slot (alphabetical) and whether the draw did (drawn), its price and
                dv20 at the decision, and the lab's outcomes for it as a zero-capital entry: nso_t20 (the next session's
                open, out at session 20: the 20-session return); an intraweek fire also FEED-06's pair, the next open
                after day k (iw_early) against the next week's first open (iw_monday), both out at session 20's open
Every fire is in the shadow population: log_only and capped fires included (FEED-05's "zero-capital shadow of all
fires")."""
import random

from .. import calendar as cal
from . import stats as S

OUTCOMES = ("intent", "cap", "log_only", "skip_size", "held", "not_in_window", "wait", "closed_day", "blocked",
            "shadow_only", "invalid")
INTRAWEEK = "lz_wait_intraweek"
IW_POLICIES = {"iw_early": ("nso", None, ("until", 20)), "iw_monday": ("nwk", None, ("until", 20))}
COVARIATES = ("price", "dv20", "ret20")

ARMS = {
    "feed05_seeded_draw": {
        "source": "AUDIT_FEED.md FEED-05 (EXPERIMENT, selection / sizing)",
        "changes": "where a lane's slots (K) bind, the slots go to a seeded random draw among the same pass's eligible "
                   "fires instead of the producer file's (alphabetical) order; and a zero-capital shadow holds every "
                   "fire, log_only and capped ones included",
        "kept": "the fires, K, the $1k slots and the lanes' mechanics; the draw fills the incumbent's slot count pass by "
                "pass; the incumbent is the lanes' own alphabetical fill",
        "expected": "if alphabetical order is harmless: no covariate or outcome difference between the drawn set, the "
                    "shadow population and the alphabetical set (intraweek took the first 20 of 31 fires, A-K)",
        "rival": "names early in the alphabet differ from the rest by chance only, and the 20-name, one-day sample "
                 "says little either way",
        "placebo": "none applies: the shadow population is itself the control (every fire, zero capital)",
        "rejection": "reject the random draw (keep the simpler incumbent) if, after at least 8 weekly cohorts, the "
                     "drawn set and the shadow population are indistinguishable from the alphabetical set in price, "
                     "dv20 and 20-session return (every cohort-clustered difference with |t| under 2); the shadow "
                     "stays as the lanes' evaluation population either way",
        "min_n": 8,
        "deviations": "the audit's fourth covariate, the band, is not in the record (the outcome observation carries "
                      "the fire's key and symbol only); eligible means outcome intent or cap as of the pass (a capped "
                      "fire was never decided, so a drawn one may not have qualified); outcomes before fix1's FEED-01 "
                      "deploy were never recorded",
    },
    "feed06_intraweek_timing": {
        "source": "AUDIT_FEED.md FEED-06 (EXPERIMENT, entry timing)",
        "changes": "on every lz_wait_intraweek fire, a paired shadow: entry at the next open after day k (the lane's "
                   "claim) against the next week's first open (the Monday open), both out at the same session",
        "kept": "every fire, its hold and capital; the lane itself is unchanged",
        "expected": "a positive mean paired advantage of the early entry (research holdout: early minus Monday open "
                    "+3.6 [+0.9, +6.8], n 453)",
        "rival": "the market's drift during the week",
        "placebo": "none built: the audit's control, same-week non-fire names, needs a draw the lane's record does "
                   "not support yet",
        "rejection": "reject (retire intraweek; enter confirmed fires on Monday) if after at least 8 weekly clusters "
                     "and 300 fires the cluster-robust mean advantage is at or below 0, or the vanished share x the "
                     "vanished loss exceeds the advantage",
        "min_n": 300, "min_clusters": 8,
        "deviations": "the vanished clause is UNVERIFIED here: whether a provisional marker was confirmed or "
                      "vanished is known only from the tracker's completed week, which the lab does not read; the "
                      "advantage is in R (the lab's ATR) at a common exit, the open of session 20 after the decision",
    },
}


def parse(key):
    """an outcome observation's key -> (fire key, outcome), or None"""
    k = str(key or "")
    if not k.startswith("lzo:"):
        return None
    parts = k[4:].rsplit(":", 2)
    if len(parts) != 3 or parts[1] not in OUTCOMES:
        return None
    return parts[0], parts[1]


def fires(rec):
    out = {}
    for at, lane, it in sorted(rec.lz_obs, key=lambda x: x[0]):
        got = parse(it.get("key"))
        if got is None:
            continue
        k, res = got
        f = out.setdefault((lane, k), {"sym": it.get("symbol"), "first_at": at, "timeline": []})
        f["timeline"].append((at, res))
    return out


def draws(fs):
    """{(lane, fire key): the pass at which the seeded draw gave it a slot}"""
    by_lane = {}
    for (lane, k), f in fs.items():
        for at, res in f["timeline"]:
            by_lane.setdefault(lane, {}).setdefault(at, []).append((k, res))
    drawn = {}
    for lane, passes in sorted(by_lane.items()):
        state = {}
        for at in sorted(passes):
            new = 0
            for k, res in sorted(passes[at]):
                if res == "intent" and state.get(k) != "intent":
                    new += 1
                state[k] = res
            if not new:
                continue
            pool = sorted(k for k, res in state.items() if res in ("intent", "cap") and (lane, k) not in drawn)
            rng = random.Random("feed05|%s|%d" % (lane, round(at)))
            for k in rng.sample(pool, min(new, len(pool))):
                drawn[(lane, k)] = at
    return drawn


def jobs(rec, live, version=1):
    """{symbol: [row]}: one zero-capital row per fire first recorded in a live session"""
    from .tape import session_for
    fs = fires(rec)
    drawn = draws(fs)
    out = {}
    for (lane, k), f in sorted(fs.items()):
        d = session_for(f["first_at"])
        sym = f["sym"]
        if d not in live or not sym:
            continue
        slot = next((at for at, res in f["timeline"] if res == "intent"), None)
        out.setdefault(sym, []).append({
            "v": version, "session": d, "arm": "lazarus", "sleeve": lane, "class": "lazarus", "symbol": sym,
            "side": "long", "fire_key": k, "decided_at": f["first_at"], "key": k,
            "outcome": f["timeline"][0][1], "timeline": [[round(a, 3), r] for a, r in f["timeline"]],
            "alphabetical": slot is not None, "alphabetical_at": slot, "drawn": (lane, k) in drawn,
            "drawn_at": drawn.get((lane, k)), "intraweek": lane == INTRAWEEK})
    return out


def row(tape, j, evaluate, base_policy):
    """the lab's outcomes for one fire as a zero-capital entry (desk/lab/policies.py evaluate)"""
    t0 = j["decided_at"]
    atr = tape.atr(t0)
    last = tape.last_close(t0)
    j["price"] = None if last is None else round(last[0], 6)
    j["dv20"] = tape.median_dv(j["session"])
    j["atr"] = None if atr is None else round(atr, 6)
    pols = dict(base_policy, **(IW_POLICIES if j["intraweek"] else {}))
    j["outcomes"] = evaluate(tape, t0, "long", j["price"], atr, False, tape.prev_close(t0), policies=pols)
    j["id"] = "%s:%s:%s" % (j["session"], j["sleeve"], j["fire_key"])
    return j


# -- the report -------------------------------------------------------------------------------------------------------

def _week(t):
    y, w, _ = cal._as_date(float(t)).isocalendar()
    return "%d-W%02d" % (y, w)


def _ret20(r):
    o = (r.get("outcomes") or {}).get("nso_t20") or {}
    return float(o["ret_pct"]) if o.get("state") == "done" and o.get("filled") else None


def _cov(r, name):
    if name == "ret20":
        return _ret20(r)
    v = r.get(name)
    return None if v is None else float(v)


def _diff(cohorts, a, b, name):
    """the cohort-clustered difference of a covariate's means: set a minus set b, one observation per cohort"""
    obs = []
    for c, rs in sorted(cohorts.items()):
        xa = [x for x in (_cov(r, name) for r in rs if a(r)) if x is not None]
        xb = [x for x in (_cov(r, name) for r in rs if b(r)) if x is not None]
        if xa and xb:
            obs.append((c, sum(xa) / len(xa) - sum(xb) / len(xb)))
    st = S.paired([(c, x) for c, x in obs])          # each cohort its own cluster
    return st


def feed05_report(rows):
    c = ARMS["feed05_seeded_draw"]
    lz = [r for r in rows if r.get("arm") == "lazarus"]
    cohorts = {}
    for r in lz:
        t = r.get("alphabetical_at") or r.get("drawn_at") or r["decided_at"]
        cohorts.setdefault(_week(t), []).append(r)
    out = {"contract": dict(c), "fires": len(lz), "alphabetical": sum(1 for r in lz if r.get("alphabetical")),
           "drawn": sum(1 for r in lz if r.get("drawn")), "cohorts": len(cohorts),
           "outcomes": {}, "by_lane": {}, "drawn_vs_alphabetical": {}, "population_vs_alphabetical": {}}
    for r in lz:
        out["outcomes"][r["outcome"]] = out["outcomes"].get(r["outcome"], 0) + 1
        b = out["by_lane"].setdefault(r["sleeve"], {"fires": 0, "alphabetical": 0, "drawn": 0})
        b["fires"] += 1
        b["alphabetical"] += bool(r.get("alphabetical"))
        b["drawn"] += bool(r.get("drawn"))
    alpha = (lambda r: r.get("alphabetical"))
    for name in COVARIATES:
        out["drawn_vs_alphabetical"][name] = _diff(cohorts, lambda r: r.get("drawn"), alpha, name)
        out["population_vs_alphabetical"][name] = _diff(cohorts, lambda r: True, alpha, name)
    if len(cohorts) < c["min_n"]:
        out["status"] = "descriptive"
        out["note"] = "descriptive until %d weekly cohorts (%d so far); no rule is applied before" % (c["min_n"],
                                                                                                   len(cohorts))
    else:
        ts = [abs(st["t"]) for g in ("drawn_vs_alphabetical", "population_vs_alphabetical")
              for st in out[g].values() if st.get("t") is not None]
        out["status"] = "rejected" if all(t < 2.0 for t in ts) else "not_rejected"
    return out


def _r(r, p):
    o = (r.get("outcomes") or {}).get(p) or {}
    if o.get("state") != "done":
        return None
    return float(o["r"]) if o.get("filled") else 0.0


def feed06_report(rows):
    c = ARMS["feed06_intraweek_timing"]
    iw = [r for r in rows if r.get("arm") == "lazarus" and r.get("intraweek")]
    obs = []
    for r in iw:
        a, b = _r(r, "iw_early"), _r(r, "iw_monday")
        if a is not None and b is not None:
            obs.append((_week(r["decided_at"]), a - b))
    st = S.paired(obs)
    out = {"contract": dict(c), "fires": len(iw), "paired": len(obs), "advantage_r": st,
           "vanished_clause": "UNVERIFIED: the tracker's completed-week marker is not read by the lab"}
    if st["n"] < c["min_n"] or st["sessions"] < c["min_clusters"]:
        out["status"] = "descriptive"
        out["note"] = "descriptive until %d fires over %d weekly clusters (%d over %d so far); no rule is applied " \
                      "before" % (c["min_n"], c["min_clusters"], st["n"], st["sessions"])
    else:
        out["status"] = "rejected" if (st["mean"] or 0.0) <= 0 else "not_rejected (the vanished clause unverified)"
    return out


def report(rows):
    return {"feed05_seeded_draw": feed05_report(rows), "feed06_intraweek_timing": feed06_report(rows)}
