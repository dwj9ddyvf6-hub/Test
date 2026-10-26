"""Lazarus — the 75 non-Midna lanes of lazarus-desk config/sleeves.json (commit a3319569, blob 7097760b), each a
sleeve with its own parameters, on the Lazarus runtime ported once.

Manifest families (by the lane's producer): tensor_tracker (1h 1d 1w: the canonical Tensor v698 tracker's
tradeable fires), desk_feed (1dc 1wa: desk_extra_fires_v1 from the lab_live books / tracker sc_tag), lab_live
(s_1dg s_1wlab s_1wsw s_rules_1d s_rules_1w: lab books routed natively by Lazarus), lazarus_feed (63 sleeve_feed
lanes: tracker ledger + alt-data tags, Q07 cells, WAIT / INDEX placeholders) and chartslector (s_cl_qm_small,
s_cl_vmr_qqq: the cl_live screens).

Vendored, hash-pinned, executed as is (desk/vendor/lazarus): signals.py (one signal function per lane:
resolve(), feed_lane / tracker_lane / lab_route, valid_fire), gate.py (capped_limit, size), cal.py (entry_bar,
time_exit_at, ...), data.py (load_feed, lab_books, tracker_log) and sleeves.json (the lane config these sleeves are
built from). desk/vendor/chartslector: cl_live_fires.py + cl_core.py, the ChartsLector producer, executed as is.

The wrapper carries out one Lazarus pass for its lane (desk.run_pass / decide / queue_pos, book.hold_exit /
exits), its decision code ported line for line into the pure functions below (parity: tools/parity/lazarus_*.py):
  * fires: resolve(lane)(inputs), deduplicated by key; invalid fires skipped; a key already decided skipped;
    lane cap: max_slots against the lane's open + working entries (an order takes a slot; a fire out of its
    window, waiting or skipped takes none: the source's own fix L-47, lazarus-desk BUG_LOG 2026-10-15, after the
    pinned a3319569 had every fire looked at take one and block the in-window fires behind it);
  * entry (gate-free path): a fire of a closed day waits; it triggers from the open of its research entry bar
    (cal.entry_bar of the lane kind: the next bar after the fire bar) for max_delay_minutes; a fire missing its
    close takes the fire session's daily close; capped DAY limit = live ref x (1 + limit_buffer_pct), capped at
    fire close x (1 + limit_band_pct) (gate.capped_limit); size class log_only -> logged, not traded; position
    $ = the size class's slot, else position_usd, else global_slot_usd; liquidity floor min_dv20_usd on the
    20-session dollar volume; gate.size (dv20 cap, whole shares, one-share rule, lane dollar budget shrink);
    qty never commits more dollars than reserved at the reference; an unknown live price waits (the source's
    order builder raised there);
  * exits: the time exit at the first pass at or after time_exit_at - 20 min (35 when it is a half-day close),
    time_exit_at = cal.time_exit_at(hold unit, entry bar, plan max_bars), recomputed from the fill session when
    the lane holds from the fill (the later of the two); the plan's own stop (stop_pct < 99) on the live ref;
    sells only in the session: one DAY limit at ref x (1 - 1%).

Removed (the cutover doctrine; not the lanes' own rules):
  * fear_day (74 lanes): QQQ < prior close AND stock <= prior close AND <= 1.02 x fire close, decided in the
    afternoon window (close-40 .. close-10) of sessions D+1..D+5, else skipped; one fear-day decision per session
    — the Galath doctrine of 2026-10-12 (a desk-wide red-day gate and buy delay). With it go its 1.02 x fire
    close no-chase cap and the D+1..D+5 re-queue window; the lane enters on Lazarus' own ungated path
    ("next_open": the research entry bar .. + max_delay_minutes).
  * qqq_red_1h (lz_1h): QQQ < prior close AND stock <= prior close at entry time (a market red-day gate).
  * held_by_account: one paper account never holding a symbol twice across lanes (a cross-sleeve overlap check);
    the lane's own one-position-per-symbol rule stays.
  * the shared account cash pool (MAIN cash / 0.9 x TEST Reg-T buying power: "insufficient cash"), a desk-wide
    exposure limit; the lane's budget_usd, max_slots, dv20 cap and liquidity floor stay.
  * monitor-only machinery: Tensor pin-drift and input-freshness alerts, broker reconciliation, ledger, publish.

Named divergences (plumbing / timing of the source runtime -> the strategy's intent here):
  1. producer hand-offs: Lazarus read the research box's files (<workspace>/galath-research shadow/live/
     latest_fires_v3.json + fires_log_v3.csv, desk_extra_fires_v1.json, paper_sleeve/live/sleeve_fires_v1.json,
     DESK_INTEGRATION/lab_live/out/latest/*.json) with the vendored readers (80 h freshness, 5-session window);
     here the same readers read the same relative layout under <root>/inputs/lazarus (cfg lazarus_inputs_dir),
     where the producers themselves now run as background jobs (desk/sleeves/families/galath_producers.py: the
     research box's tracker, lab_live, desk_feed, sleeve_feed and alt-data nightlies, vendored byte-exact).
  2. ChartsLector: s_cl_qm_small reads the real producer's output as Lazarus did: the sleeve_feed job runs
     cl_live_fires.py on the tracker's engine store (its whole canonical universe) with the PIT SEC band, then
     cl_merge.py into sleeve_fires_v1.json (signals.feed_lane). s_cl_vmr_qqq (unchanged): the vendored
     cl_live_fires.main runs on an engine store the desk writes from its Yahoo daily
     bars for QQQ (the source's store held the tracker's whole canonical universe; its day axis = the sessions
     most names printed, here QQQ's own sessions) and on the Cboe CSVs the desk downloads into its cache when
     they lack the last closed session (the source re-downloaded them at its 09:00 / 20:05 runs); the
     cl_merge.py hand-off (CL fires merged into sleeve_fires_v1.json, dropped unless generated today) becomes
     the producer's output read directly — its own fail-closed rules still apply (store > 4 days stale -> no
     fire; Cboe behind the last session -> no VMR fire).
  3. pass slots: Lazarus passed at 09:35 10:31 11:31 12:31 13:31 14:31 15:31 15:42 16:01 16:50 ET; these sleeves
     run every desk pass of the regular session: entries at the first pass inside the entry window, time exits
     at the first pass at or after time_exit_at - 20 min (Lazarus: its 15:42 / 12:31 slots).
  4. accounts: the lane's virtual book (capital = its budget_usd) replaces the shared MAIN / TEST_MWJW books:
     occupancy, budget use and the own-symbol rule read this lane's positions and working entries.
  5. reference price: the desk quote (Alpaca IEX snapshot when keyed, else Yahoo) under the source's rule — the
     last price when the quote is <= 10 min old, else a fresh mid with spread <= 2%, else unknown (wait); the
     source aged the IEX last trade and the IEX quote with two GETs of its own.
  6. orders: the source's client_order_id scheme and broker plumbing (submit / sync by client_order_id,
     re-queue of an unfilled entry inside its deadline, re-send of an unfilled exit) -> engine children keyed by
     the fire key: an entry is one DAY limit child alive until the close (the ungated path's deadline,
     entry bar + max_delay, always ends before the DAY order does, so the source never re-queued it); an exit is
     re-emitted at each due pass (the OMS's attempt n+1).
  7. cutover adoption (the old desks' queued entries, decided keys and mirrored book) is not carried: each lane
     starts flat.
  8. lanes the source left without a fire (Lazarus state dead; signals.resolve() -> None) run their intended
     rules (LIVE_RULES): an INDEX lane is the union of the cells it indexes (s_q07_wiki: the Q07 wiki families its
     sleeve_playbook.json row lists; s_q07_ins2: the s_q07w_*ins2* lanes), each fire re-keyed to the index lane;
     s_1wsw_stress reads sleeve_feed 1.0.4's own s_1wsw_stress fires (the w_swing feed producer now runs). The six WAIT
     placeholders run Research Lab's frozen lane specs (DESK_INTEGRATION/sleeve_specs/<lane>/README.md, vendored): their fires
     come from this desk's galath_wait_feed (shadow/paper_sleeve/live/wait_fires_v1.json, desk/sleeves/families/
     galath_wait_feed.py: rules and input divergences), each with its spec's entry kind and hold (WAIT_SPEC: Q14 W78 with
     the $5.00 entry cap, FLOW D+60, CHASE W52, OLX books H + 1 from the fill, R2 Daily Cyan 21 sessions, intraweek W52 from
     the fire week) and the paper-test sizing.

A lane whose producer is not on this desk would be wired here (all_sleeves()) and listed in BLOCKED with the missing piece
(also config/manifest/blocked.json); none is: sleeves() registers all 75. A lane an input of which comes from a producer
switched off in galath_producers.OFF cannot fire while it stays off (FEED-02: altdata_nightly, off since 2026-10-19, cuts 52
lanes): inputs_off derives them with the missing piece; they stay registered and run as before, and are recorded BLOCKED
(blocked_register = blocked.json's Lazarus rows, the lane's CONFIG.params["blocked"], one blocked_data observation a session,
not ready in desk health).

The record (FEED-01; observations, never orders: the decisions above are untouched): each fire key's outcome (intent, log_only,
skip_size, held, not_in_window, wait, cap, closed_day, blocked, shadow_only, invalid) is written when it changes, the lane's input
health (input_health: load_inputs' _health of its inputs, the producer's notes, feed codes and its own line) when it changes,
and a resolver exception is the lane's sleeve_error, once a session per error (beside its exits as an observation when an exit
goes out that pass), instead of an empty fire list."""
import contextlib
import hashlib
import io
import json
import math
import os

import numpy as np
import pandas as pd

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...vendor.lazarus import cal, data, gate, signals
from . import galath_producers as G

VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor")
CONFIG = json.load(open(os.path.join(VENDOR, "lazarus", "sleeves.json")))
SOURCE = {"repo": "lazarus-desk", "ref": "main", "commit": "a3319569f5de475e3a655aae1f456f7dfe757776",
          "path": "config/sleeves.json", "blob": "7097760b1682098c5e85ae7ce2519e7d6272e0ee"}
CL_SOURCE = {"repo": "quant-research-critical", "ref": "main", "commit": "0be4c57569e363d052bd23564cf0664697439927",
             "path": "galath-research/shadow/paper_sleeve/chartslector/cl_live_fires.py",
             "blob": "dec0c0637680a23f1d23a058c35a5c9623c99e67"}
# config/lazarus.json @a3319569 (blob 5a0a4fed): the runtime constants the pass reads
FEED_MAX_AGE_HOURS = 80
FIRE_MAX_AGE_SESSIONS = 5
REF_MAX_AGE_MIN = 10
REF_MAX_SPREAD_PCT = 2.0
EXIT_BUFFER_PCT = 1.0
PRODUCER = {"tracker (canonical Tensor v698 engine)": "tensor_tracker",
            "desk_feed (lab_live books / tracker sc_tag)": "desk_feed",
            "lab_live books (native Lazarus routing)": "lab_live",
            "sleeve_feed composer (tracker ledger + alt-data tags)": "lazarus_feed",
            "cl_live (ChartsLector screens)": "chartslector"}
# producer files, relative to the research root (Lazarus config paths under <workspace>/galath-research)
INPUT_FILES = {"fires_main": "shadow/live/latest_fires_v3.json",
               "fires_main_extra": "shadow/live/desk_extra_fires_v1.json",
               "fires_sleeve": "shadow/paper_sleeve/live/sleeve_fires_v1.json",
               "fires_wait": "shadow/paper_sleeve/live/wait_fires_v1.json"}    # galath_wait_feed (the WAIT lanes' producer)
LAB_DIR = "DESK_INTEGRATION/lab_live/out/latest"
CL_BARS = 420


def sleeve_id(lane):
    return "lz_" + (lane[2:] if lane.startswith("s_") else lane)


def rows():
    """the 75 lanes this module runs: every config row but Midna's (s_mn_*, family midna_tensor) and the
    exit-only legacy stub."""
    return [r for r in CONFIG["sleeves"] if not r["id"].startswith("s_mn_") and r["id"] != "legacy_exit"]


def family_of(row):
    return PRODUCER[row["source"]["producer"]]


# ---------------------------------------------------------------- lanes the source left without a fire (state dead)
PLAYBOOK = json.load(open(os.path.join(VENDOR, "galath_research", "shadow", "paper_sleeve", "sleeve_playbook.json")))
LIVE_POSITION_USD = 1000.0                      # DESK_PLAN section 3: paper-test positions are $1k


def paper_test_k(hold_sessions):
    """DESK_PLAN section 3 (the paper-test families): concurrency K = min(20, ceil(20 x hold_sessions / 126))."""
    return min(20, math.ceil(20 * hold_sessions / 126))


def index_cells():
    """{INDEX lane: its cell lanes}: s_q07_wiki = the Q07 wiki families its sleeve_playbook.json row lists, each traded as an
    s_q07w_* lane; s_q07_ins2 = the s_q07w_*ins2* lanes (its playbook status: "the cells trade as s_q07w_*ins2* lanes")."""
    L = PLAYBOOK["lanes"]
    by_cell = {v["q07_cell"]: k for k, v in L.items() if v.get("q07_cell") and k.startswith("s_q07w_")}
    return {"s_q07_wiki": sorted(by_cell[c] for c in L["s_q07_wiki"]["eligibility"]["families"] if c in by_cell),
            "s_q07_ins2": sorted(k for k in L if k.startswith("s_q07w_") and "ins2" in k)}


def index_lane(lane, cells):
    """an INDEX lane: the union of its cells' fires in the composed sleeve file, each re-keyed to the index lane."""
    cells = set(cells)

    def fn(I):
        o = I.get("fires_sleeve")
        if o is None:
            return []
        return [dict(signals._norm_feed(f, False, "fires_sleeve"), key=f"{f['key']}|{lane}", lane=lane)
                for f in o.get("fires", []) if f.get("lane") in cells and f.get("tradeable", True)]
    fn.__name__ = f"index_lane[{lane}]"
    return fn


# the WAIT lanes on Research Lab's frozen lane specs (DESK_INTEGRATION/sleeve_specs/<lane>/README.md, vendored): their fires come from
# galath_wait_feed (shadow/paper_sleeve/live/wait_fires_v1.json); entry kind, hold unit and the K rule's hold per spec.
WAIT_SPEC = {
    "s_wait_q14": dict(kind="1w", unit="1w", hold_from="plan", H=78 * 5, rule="W78 from the 1W fire week, no stop (Q14 pxcap5)"),
    "s_wait_flow": dict(kind="1d", unit="1d", hold_from="plan", H=60, rule="D+1 open .. close of D+60, no stop (FLOW svr5 cell)"),
    "s_wait_chase": dict(kind="1w", unit="1w", hold_from="plan", H=52 * 5, rule="W52 from the 1W fire week, no stop (CHASE)"),
    "s_wait_olx_books": dict(kind="1d", unit="1d", hold_from="fill", H=126, rule="entry + H sessions (H + 1 from the fill), no stop "
                                                                                 "(OLX frozen rules, the s_rules mechanics)"),
    "s_wait_r2_dcyan": dict(kind="1d", unit="1d", hold_from="fill", H=21, rule="21 sessions from the fill, no stop (lab 1D horizon)"),
    "s_wait_intraweek": dict(kind="1d", unit="1w", hold_from="plan", H=52 * 5, rule="next open after day k .. close of the fire Friday "
                                                                                    "+ 52 weeks, no stop (intraweek early entry)"),
}


def wait_lane(lane):
    """a WAIT lane: its fires in the wait feed (signals.feed_lane's normalisation + the fire's own entry price cap, Q14's $5.00)."""
    def fn(I):
        o = I.get("fires_wait")
        if o is None:
            return []
        return [dict(signals._norm_feed(f, False, "fires_wait"), limit_cap=f.get("limit_cap"))
                for f in o.get("fires", []) if f.get("lane") == lane and f.get("tradeable", True)]
    fn.__name__ = f"wait_lane[{lane}]"
    return fn


LIVE_RULES = {lane: index_lane(lane, cells) for lane, cells in index_cells().items()}
LIVE_RULES["s_1wsw_stress"] = signals.feed_lane("s_1wsw_stress", "fires_sleeve")
LIVE_RULES.update({lane: wait_lane(lane) for lane in WAIT_SPEC})
LIVE_HOLD = dict({"s_q07_wiki": 52 * 5, "s_q07_ins2": 52 * 5, "s_1wsw_stress": 52 * 5},   # sessions (W52 / W78 cells -> K 20)
                 **{lane: w["H"] for lane, w in WAIT_SPEC.items()})


def live_row(row):
    """a dead row run on its intended rule: state live; a row the source sized at zero (max_slots 0, budget 0) takes the
    paper-test sizing (K = min(20, ceil(20 x H / 126)) positions of $1k); a WAIT row takes its spec's entry kind and hold."""
    if row["id"] not in LIVE_RULES:
        return row
    row = json.loads(json.dumps(row))
    row["state"] = "live"
    w = WAIT_SPEC.get(row["id"])
    if w:
        row["kind"] = w["kind"]
        row["exit"].update(hold_unit_kind=w["unit"], hold_from=w["hold_from"], rule=f"the wait feed fire's plan: {w['rule']}")
    z = row["sizing"]
    if not z.get("max_slots"):
        k = paper_test_k(LIVE_HOLD[row["id"]])
        z.update(max_slots=k, budget_usd=k * LIVE_POSITION_USD, position_usd=LIVE_POSITION_USD,
                 global_slot_usd=LIVE_POSITION_USD)
    return row


# ---------------------------------------------------------------------------------------------- blocked lanes
def _blocked():
    """lanes wired here whose producer is not on this desk: none (every lane's producer runs: galath_producers, galath_wait)."""
    return {sleeve_id(r["id"]): f"no fire source: Lazarus state {r['state']} and no live rule on this desk"
            for r in rows() if r["id"] not in LIVE_RULES and signals.resolve(r) is None}


BLOCKED = _blocked()

# the alt-data inputs a lane cannot decide without, research-relative: a Q07 cell's tags (the cell id's "+" terms, as
# shadow/paper_sleeve/sleeve_q07.py parse), each read from its feed's file in the source's feed registry (sleeve_feeds.py
# REGISTRY: wiki, insider2, finra_ats, options_market), and the 1W Swing fire source of the w_swing cells and s_1wsw_stress
# (sleeve_swing.py); which producer writes each is galath_producers.OUTPUTS'
WIKI_INPUT = "WIKI_LIVE/out/wiki_features_latest.parquet"
TAG_INPUT = {"wiki_cov": WIKI_INPUT, "wiki_low": WIKI_INPUT, "wiki_spike2": WIKI_INPUT,
             "insider2": "ALTDATA_LIVE/out/insider2_latest.parquet", "ats_z1": "ALTDATA_LIVE/out/finra_ats_events.parquet",
             "gamma_low": "ALTDATA_LIVE/out/options_market_latest.parquet"}
SWING_INPUT = "DESK_INTEGRATION/w_swing_live/out/w_swing_fires_latest.json"


def lane_inputs(lane):
    """the alt-data files a lane cannot decide without ([] for a lane that needs none)."""
    if lane == "s_1wsw_stress":
        return [SWING_INPUT]
    cell = (PLAYBOOK["lanes"].get(lane) or {}).get("q07_cell")
    if not cell:
        return []
    _, kind, _, _, tags = cell.split("-", 4)          # Q07-<lane>-H<h>-<band>-<tag+tag...>
    return sorted({TAG_INPUT[t] for t in tags.split("+") if t in TAG_INPUT} | ({SWING_INPUT} if kind == "w_swing" else set()))


def inputs_off(off=None):
    """FEED-02: {sleeve id: the missing piece} of the lanes an input of which comes from a producer switched off in
    galath_producers.OFF (off: that table), and of an INDEX lane whose every cell is one. Without the switch: none."""
    off = G.OFF if off is None else off
    writer = {rel: p for p, rels in G.OUTPUTS.items() for rel in rels}
    stopped = {G.PRODUCER_OF[j]: j for j in off if j in G.PRODUCER_OF}
    out = {}
    for r in rows():
        gone = [rel for rel in lane_inputs(r["id"]) if writer.get(rel) in stopped]
        if gone:
            jobs = ", ".join(sorted({stopped[writer[rel]] for rel in gone}))
            out[r["id"]] = f"input missing: {', '.join(gone)} (its source {jobs} is switched off in galath_producers.OFF)"
    for lane, cells in index_cells().items():
        if cells and all(c in out for c in cells):
            out[lane] = f"input missing: the alt-data inputs of all {len(cells)} cells it indexes (their source is switched " \
                        f"off in galath_producers.OFF: {', '.join(sorted(off))})"
    return {sleeve_id(k): v for k, v in sorted(out.items())}


INPUT_OFF = inputs_off()


def blocked_register(off=None):
    """config/manifest/blocked.json's Lazarus rows: the lanes not wired here (BLOCKED) and those whose input is switched off."""
    return dict(_blocked(), **inputs_off(off))


# ---------------------------------------------------------------------------------------- pure decision code
def ts(epoch):
    return cal.ts(pd.Timestamp(float(epoch), unit="s", tz="UTC"))


def oldest_fire_day(now, n):
    """desk.oldest_fire_day: the earliest of the last n trading sessions up to now (ET date string)."""
    d = cal.day0(now)
    sess = []
    while len(sess) < n:
        if cal.is_td(d) and d <= cal.day0(now):
            sess.append(d)
        d -= pd.Timedelta(days=1)
    return str(sess[-1].date())


def ref_price(q, now_epoch):
    """the source's ref quote on a desk quote: last when the quote is <= 10 min old, else a fresh tight mid."""
    q = q or {}
    t = q.get("t")
    fresh = t is None or (float(now_epoch) - float(t)) / 60.0 <= REF_MAX_AGE_MIN
    if not fresh:
        return None
    last = q.get("last")
    if last and float(last) > 0:
        return float(last)
    bp, ap = q.get("bid"), q.get("ask")
    if bp and ap and float(bp) > 0 and float(ap) >= float(bp):
        bp, ap = float(bp), float(ap)
        if (ap - bp) / ((ap + bp) / 2) * 100 <= REF_MAX_SPREAD_PCT:
            return round((ap + bp) / 2, 4)
    return None


def removed_gates(row):
    """what the cutover doctrine removed from this lane (the lane's own rules stay)."""
    pol = row["entry"]["policy"]
    first = {"fear_day": "fear_day: QQQ < prior close AND stock <= prior close AND <= 1.02 x fire close, decided in "
                         "the afternoon window of sessions D+1..D+5 (one decision per session), else skipped",
             "qqq_red_1h": "qqq_red_1h: QQQ < prior close AND stock <= prior close at entry time"}.get(pol, pol)
    return [first, "held_by_account: one paper account never holding a symbol twice across lanes",
            "account cash pool: the shared MAIN cash / TEST 0.9 x Reg-T buying power ('insufficient cash')"]


def entry_kind(row):
    return row["kind"] if row["kind"] in ("1h", "1d", "1w") else "1d"


def hold_kind(row):
    """book.exit_kind: the lane's hold unit."""
    return row.get("exit", {}).get("hold_unit_kind") or row.get("kind") or row["id"][:2]


def entry_window(row, fire_bar):
    """the gate-free entry window: [open of the research entry bar, + max_delay_minutes]."""
    eb, _ = cal.entry_bar(entry_kind(row), fire_bar)
    return eb, eb + pd.Timedelta(minutes=row["entry"]["max_delay_minutes"] or 30)


def decide(row, f, now, px, held, used_usd, dv20):
    """desk.decide() for one fire on Lazarus' ungated path (fear_day / qqq_red_1h removed; held = this lane's
    own symbols; the account cash pool removed). -> dict(result, why, qty, limit)."""
    e, z = row["entry"], row["sizing"]
    d = dict(lane=row["id"], key=f["key"], sym=f["sym"])
    if row["state"] != "live" or f.get("shadow"):
        return dict(d, result="shadow_only")
    if f["sym"] in held:
        return dict(d, result="held")
    if not cal.is_td(now):
        return dict(d, result="closed_day")
    eb, dl = entry_window(row, f["fire_bar"])
    if not (eb <= now <= dl):
        return dict(d, result="not_in_window")
    lim = gate.capped_limit(ref=px, buffer_pct=e["limit_buffer_pct"], fire_close=f["close"],
                           band_pct=e["limit_band_pct"] or 0, no_chase_max=None)
    if lim and f.get("limit_cap"):                # the lane's own entry price cap (Q14: the fill must be <= $5.00)
        lim = min(lim, float(f["limit_cap"]))
    if f.get("size_class") == "log_only":
        return dict(d, result="log_only", why="size_class log_only (tested weak in this bucket; logged, not traded)")
    pos_usd = float((z.get("position_usd_by_class") or {}).get(f.get("size_class")) or z["position_usd"]
                    or z["global_slot_usd"])
    if not (f.get("ref_price") or f["close"] or px):
        return dict(d, result="wait", why="no reference price (the source raised here)")
    ref0 = float(f.get("ref_price") or f["close"] or px)
    flo = z.get("min_dv20_usd")
    if flo and (dv20 is None or dv20 < flo):
        return dict(d, result="skip_size", why=f"illiquid: dv20 {'unavailable' if dv20 is None else f'${dv20:,.0f}'} "
                                               f"< ${flo:,.0f} floor")
    qty, why2, blocked = gate.size(position_usd=pos_usd, ref=ref0, avail=math.inf, dv20=dv20,
                                   cap_pct_dv20=z["cap_pct_of_dv20"], min_fraction=z["min_slot_fraction"],
                                   global_slot_usd=z["global_slot_usd"], lane_used_usd=used_usd,
                                   budget_usd=z["budget_usd"], one_share_max_usd=z.get("one_share_max_usd"))
    if not qty:
        return dict(d, result="blocked" if blocked else "skip_size", why=why2)
    if lim and ref0 and lim > ref0:
        qty = max(1, min(qty, int(qty * ref0 // lim)))
    if not lim:                                   # unknown live price: the source's order builder raised here
        return dict(d, result="wait", why="no live reference price")
    return dict(d, result="intent", qty=int(qty), limit=lim, ref0=ref0)


def time_exit_at(row, fire_bar, plan):
    """queue_pos: the planned time exit from the research entry bar (None without max_bars)."""
    mb = (plan or {}).get("max_bars")
    if not mb:
        return None
    k = hold_kind(row)
    eb, _ = cal.entry_bar(entry_kind(row), fire_bar)
    return cal.time_exit_at(k if k in ("1h", "1d", "1w") else "1d", eb, int(mb))


def hold_exit(row, plan, te0, fill_at):
    """book.hold_exit: a lane holding from the fill counts its 1d / 1w hold from the fill session (the later)."""
    k, mb = hold_kind(row), (plan or {}).get("max_bars")
    if row["exit"]["hold_from"] != "fill" or k not in ("1d", "1w") or not mb or te0 is None:
        return te0
    fd = cal.day0(fill_at)
    new = cal.time_exit_at(k, cal.s_open(fd), int(mb)) if cal.is_td(fd) else None
    return new if new is not None and new > te0 else te0


def exit_decision(te, plan, avg, now, px):
    """book.exits for one open position -> None (hold) | dict(why, limit) | dict(why, limit=None) (no price)."""
    why = None
    if te is not None:
        lead = 35 if cal.close_minutes(te) != 960 and te == cal.s_close(te) else 20
        if now >= te - pd.Timedelta(minutes=lead):
            why = f"time exit {te}"
    st = float((plan or {}).get("stop_pct") or 99)
    if not why and st < 99 and px and avg and px <= float(avg) * (1 - st / 100):
        why = f"stop {st}% (last {px} vs entry {avg})"
    if not why:
        return None
    if not (cal.is_td(now) and cal.s_open(now) <= now < cal.s_close(now)):
        return None
    if not px:
        return dict(why=why, limit=None)
    return dict(why=why, limit=round(px * (1 - EXIT_BUFFER_PCT / 100), 2 if px >= 1 else 4))


def dv20(bars, now):
    """data.dv20 on desk daily bars: mean close x volume of the last 20 completed sessions up to `now` (numpy
    pairwise sum / 20, as pandas' Series.mean)."""
    day = cal.day0(now)
    b = [x for x in bars if _sess(x["t"]) <= day]
    if len(b) < 20:
        return None
    return float(np.asarray([float(x["c"]) * float(x.get("v") or 0) for x in b[-20:]], dtype=float).sum() / 20)


def close_on(bars, day):
    """the fire session's daily close (desk.run_pass fills a fire's missing close from the engine bars)."""
    want = cal.day0(day)
    hit = [float(x["c"]) for x in bars if _sess(x["t"]) == want]
    return hit[-1] if hit else None


def _sess(t):
    return cal.day0(ts(float(t)))


# ------------------------------------------------------------------------------------------------------ feeds
def _root(feeds, sleeve):
    eng = getattr(sleeve, "engine", None)
    if eng is not None:
        return eng.root
    return os.path.dirname(feeds.hub.cache.root)


def inputs_dir(feeds, sleeve):
    eng = getattr(sleeve, "engine", None)
    d = (eng.cfg.get("lazarus_inputs_dir") if eng is not None else None)
    return d or os.path.join(_root(feeds, sleeve), "inputs", "lazarus")


def load_inputs(base, now_epoch):
    """desk.load_inputs on files under `base` (the research root's layout): the producer files with the vendored
    80 h freshness rule, the lab books, the 5-session window and the tracker fire log inside it."""
    now = ts(now_epoch)
    C = {"paths": dict({k: os.path.join(base, v) for k, v in INPUT_FILES.items()},
                       lab_books=os.path.join(base, LAB_DIR), research=base),
         "feed_max_age_hours": FEED_MAX_AGE_HOURS, "fire_max_age_sessions": FIRE_MAX_AGE_SESSIONS}
    inp, health = {}, {}
    for k in INPUT_FILES:
        inp[k], health[k] = data.load_feed(C["paths"][k], FEED_MAX_AGE_HOURS, now)
    inp["lab_books"] = data.lab_books(C)
    inp["oldest_fire_day"] = oldest_fire_day(now, FIRE_MAX_AGE_SESSIONS)
    inp["fires_main_log"] = data.tracker_log(C, inp["oldest_fire_day"])
    health["lab_books"] = dict(ok=bool(inp["lab_books"]), n=len(inp["lab_books"]))
    health["fires_main_log"] = dict(ok=True, n=len(inp["fires_main_log"]))
    inp["_health"] = health
    return inp


def feed_inputs(feeds, sleeve, now, arg=None):
    return load_inputs(inputs_dir(feeds, sleeve), now)


CBOE_FILES = {"VIX": "VIX_History.csv", "VIX3M": "VIX3M_History.csv", "VVIX": "VVIX_History.csv",
              "SKEW": "SKEW_History.csv"}
CBOE_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{}"
CBOE_GET = None            # optional fetch hook (url -> bytes|str); None = desk.data.http.get
_CBOE_TRY = {}
_CL_MEMO = {}


def _cboe_last(path):
    try:
        with open(path) as f:
            lines = [x for x in f.read().splitlines() if x.strip()]
        return pd.Timestamp(lines[-1].split(",")[0]).normalize() if len(lines) > 1 else None
    except (OSError, ValueError):
        return None


def refresh_cboe(d, now_epoch, last_session, getter=None):
    """keep the four Cboe daily CSVs current: (re)download one whose cache lacks the last closed session (at
    most every 10 minutes) or is older than 12 hours; the source's validation (payload must start with DATE,
    else the cache is kept)."""
    os.makedirs(d, exist_ok=True)
    notes = []
    for k, fn in CBOE_FILES.items():
        p = os.path.join(d, fn)
        last = _cboe_last(p)
        age = now_epoch - os.path.getmtime(p) if os.path.exists(p) else None
        behind = last is None or (last_session is not None and last < last_session)
        if not (behind or age is None or age > 12 * 3600) or now_epoch - _CBOE_TRY.get(p, 0) < 600:
            continue
        _CBOE_TRY[p] = now_epoch
        try:
            getter = getter or CBOE_GET
            if getter is not None:
                b = getter(CBOE_URL.format(fn))
            else:
                from ...data.http import get
                b = get(CBOE_URL.format(fn), as_text=True, timeout=60)
            b = b.encode() if isinstance(b, str) else b
            if b[:4].upper().startswith(b"DATE"):
                with open(p + ".tmp", "wb") as f:
                    f.write(b)
                os.replace(p + ".tmp", p)
            else:
                notes.append(f"cboe {k}: unexpected payload, kept cache")
        except Exception as ex:
            notes.append(f"cboe {k}: fetch failed ({str(ex)[:60]}), using cache")
    return notes


def write_store(eng_dir, sym, bars):
    """an engine-store CSV (the tracker engine's 1d export columns) from desk daily bars (closed sessions)."""
    os.makedirs(os.path.join(eng_dir, "1d"), exist_ok=True)
    lines = ["timestamp,open,high,low,close,volume,barFinality"]
    for b in bars:
        lines.append("%d,%r,%r,%r,%r,%r,closed" % (int(b["t"]), float(b["o"]), float(b["h"]), float(b["l"]),
                                                   float(b["c"]), float(b.get("v") or 0)))
    tmp = os.path.join(eng_dir, "1d", sym + ".csv.tmp")
    with open(tmp, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, os.path.join(eng_dir, "1d", sym + ".csv"))


def run_cl(work, qqq_bars, cboe_dir, today):
    """the vendored ChartsLector producer over QQQ's daily bars and the cached Cboe CSVs -> its output JSON."""
    import importlib
    import sys
    here = os.path.join(VENDOR, "chartslector")
    if here not in sys.path:
        sys.path.insert(0, here)
    cl = importlib.import_module("cl_live_fires")
    eng = os.path.join(work, "engine")
    write_store(eng, "QQQ", qqq_bars)
    out = os.path.join(work, "cl_fires_v1.json")
    with contextlib.redirect_stdout(io.StringIO()):
        cl.main(["--eng", eng, "--out", out, "--cboe-dir", cboe_dir, "--no-net", "--no-sec", "--today", today,
                 "--bars", str(CL_BARS)])
    with open(out) as f:
        return json.load(f)


def feed_cl(feeds, sleeve, now, arg=None):
    """the ChartsLector lanes' input: {"fires_sleeve": {"fires": cl fires}, "cl": freshness / notes}."""
    root = _root(feeds, sleeve)
    work = os.path.join(root, "cache", "lazarus_cl")
    cboe = os.path.join(root, "cache", "cboe_daily")
    bars = (feeds.hub.bars("yahoo", "1d", ["QQQ"], CL_BARS + 40).get("QQQ") or [])
    nts = ts(now)
    last = _sess(bars[-1]["t"]).tz_localize(None) if bars else None
    notes = refresh_cboe(cboe, now, last)
    today = str(cal.day0(nts).date())
    sig = (today, int(bars[-1]["t"]) if bars else None, len(bars),
           tuple((os.path.getmtime(os.path.join(cboe, f)) if os.path.exists(os.path.join(cboe, f)) else None)
                 for f in CBOE_FILES.values()))
    if _CL_MEMO.get(work, (None,))[0] != sig:
        J = run_cl(work, bars, cboe, today) if bars else {"fires": [], "notes": ["no QQQ daily bars"]}
        _CL_MEMO[work] = (sig, J)
    J = _CL_MEMO[work][1]
    return {"fires_sleeve": {"fires": J.get("fires") or []}, "oldest_fire_day": oldest_fire_day(nts, 5),
            "cl": {"freshness": J.get("freshness"), "notes": (J.get("notes") or [])[-6:] + notes}}


FEEDS = {"lazarus_inputs": feed_inputs, "lazarus_cl": feed_cl}


# ------------------------------------------------------------------------------------------------------ the record
def input_keys(row):
    """the producer inputs a lane's fires come from (signals.resolve's routing, LIVE_RULES, the lazarus_cl feed's own)."""
    lid = row["id"]
    if lid == "s_cl_vmr_qqq":
        return ("cl",)
    if lid in WAIT_SPEC:
        return ("fires_wait",)
    if lid in LIVE_RULES:
        return ("fires_sleeve",)
    if row["state"] == "dead":
        return ()
    if row["account"] == "MAIN":
        return ("fires_main", "fires_main_log") if lid in ("1h", "1d", "1w") else ("fires_main_extra",)
    return ("lab_books",) if lid in signals.LAB_LANES else ("fires_sleeve",)


def input_health(I, keys, lane):
    """FEED-01: a lane's inputs as its pass read them: load_inputs' _health of each (ok, the producer file's generated, the
    error's kind, n), the producer's notes and feed codes, and the producer's own line on this lane where it writes one (a Q07
    cell's missing reasons, a WAIT lane's status); the ChartsLector lane's own freshness and notes."""
    I = I or {}
    H = I.get("_health") or {}
    out = {}
    for k in keys:
        o = I.get(k)
        if k == "cl":
            o = o or {}
            out[k] = {"freshness": o.get("freshness"), "notes": [str(x)[:160] for x in list(o.get("notes") or [])[-4:]]}
            continue
        h = H.get(k) or {}
        e = h.get("error")
        rec = {"ok": h.get("ok"), "generated": h.get("generated"), "error": str(e).split(" (")[0][:80] if e else None}
        if "n" in h:
            rec["n"] = h["n"]
        if k.startswith("fires_") and isinstance(o, dict):
            if o.get("notes"):
                rec["notes"] = [str(x)[:160] for x in list(o["notes"])[:4]]
            if isinstance(o.get("feeds"), dict):
                rec["codes"] = {f: v.get("code") for f, v in sorted(o["feeds"].items()) if isinstance(v, dict) and v.get("code")}
            mine = (o.get("q07_cells") or {}).get(lane) or (o.get("lanes") or {}).get(lane)
            if isinstance(mine, dict):
                line = {x: mine[x] for x in ("status", "missing", "carried", "evaluated", "fires") if x in mine}
                if isinstance(line.get("missing"), dict):
                    top = sorted(line["missing"].items(), key=lambda kv: -kv[1] if isinstance(kv[1], (int, float)) else 0)
                    line["missing"] = {str(r)[:160]: n for r, n in top[:3]}
                rec["lane"] = line
        out[k] = rec
    return out


def _health_line(h):
    parts = []
    for k, r in h.items():
        if k == "cl":
            parts.append(f"cl {r.get('freshness')}")
            continue
        s = f"{k} {'ok' if r.get('ok') else (r.get('error') or 'absent')}"
        if r.get("generated"):
            s += f" (generated {r['generated']})"
        bad = [f"{f} {c}" for f, c in (r.get("codes") or {}).items() if c != "OK"]
        parts.append("; ".join([s] + list(r.get("notes") or [])[:1] + ([", ".join(bad)] if bad else [])))
    return " | ".join(parts) or "no input"


# ------------------------------------------------------------------------------------------------------ sleeve
class LazarusLane(Sleeve):
    RECORD = True               # FEED-01's record and FEED-02's note (a subclass that keeps the record as it was: False)
    blocked, inputs, _err = None, (), None

    def __init__(self, row):
        row = live_row(row)
        self.row = row
        self.family = family_of(row)
        self.feed = "lazarus_cl" if row["id"] == "s_cl_vmr_qqq" else "lazarus_inputs"
        self.fn = LIVE_RULES.get(row["id"]) or signals.resolve(row)
        self.blocked = INPUT_OFF.get(sleeve_id(row["id"]))      # FEED-02: an input switched off (the missing piece), else None
        self.inputs = input_keys(row)                           # FEED-01: the inputs its fires come from
        self._err = None                                        # the resolver error last recorded ("<session>|<error>")
        z = row["sizing"]
        capital = float(z.get("budget_usd") or z.get("global_slot_usd") or z.get("position_usd") or 1000.0)
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id(row["id"]), family=self.family, cadence_s=60, universe=(), capital=capital,
            needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 30, "symbols_for": "lazarus"}],
                   "quotes": {"source": "equity"}, "feeds": [self.feed]},
            schedule="rth", status="active",
            params=dict({"lane": row["id"], "account": row["broker_account"], "kind": row["kind"], "state": row["state"],
                         "entry": row["entry"], "exit": row["exit"], "sizing": row["sizing"], "label": row["label"],
                         "removed_gates": removed_gates(row)}, **({"blocked": self.blocked} if self.blocked else {})),
            source=dict(SOURCE, lane=row["id"], producer=row["source"]["producer"], file=row["source"]["file"],
                        **({"producer_source": CL_SOURCE} if self.family == "chartslector" else {})),
            state_schema={"seen": "dict", "pending": "dict", "blocked_on": "str|None", "outcomes": "dict",
                          "health": "str|None", "resolver_error": "str|None"})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    # -- inputs ---------------------------------------------------------------------------------------------
    def _inputs(self, now):
        if self.engine is None or self.engine.feeds is None:
            return {}
        return self.engine.feeds.get(self.feed, self, now) or {}

    def fires(self, inputs):
        """the lane's fires for the pass's data plan (bars, quotes): a resolver exception gives none here, and signal() records
        it (resolve)."""
        return self.resolve(inputs)[0]

    def resolve(self, inputs):
        """(fires deduplicated by key, the resolver's exception or None)."""
        if self.fn is None or not inputs:
            return [], None
        try:
            out = self.fn(inputs)
        except Exception as e:
            return [], e
        return list({f["key"]: f for f in out}.values()), None

    def _held(self, book):
        return [i.split(":", 1)[1] for i, p in (book.positions.items() if book else []) if i.startswith("EQ:")]

    def bar_symbols(self, need, now, book=None):
        syms = [f["sym"] for f in self.fires(self._inputs(now))] + self._held(book)
        return list(dict.fromkeys(syms))

    def quote_universe(self, now, book=None):
        return self.bar_symbols(None, now, book)

    # -- the pass ---------------------------------------------------------------------------------------------
    def signal(self, view):
        row, z = self.row, self.row["sizing"]
        st = dict(view.state or {})
        seen, pending = dict(st.get("seen") or {}), dict(st.get("pending") or {})
        now = ts(view.now)
        daily = (view.bars or {}).get("1d") or {}
        held_pos = {i.split(":", 1)[1]: p for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"]) > 0}
        live = {p.get("signal_key"): p for p in view.extra.get("pending_orders", [])}
        working_exit = {p["inst"].split(":", 1)[1] for p in view.extra.get("pending_orders", []) if p["action"] == "exit"}
        for k in list(pending):                  # an entry leaves `pending` once its child is no longer working
            if k + ":EN" not in live:
                pending.pop(k)
        held = set(held_pos) | {v["sym"] for v in pending.values()}
        used = sum(float(p["avg"]) * float(p["qty"]) for p in held_pos.values()) + \
            sum(float(v["ref_price"]) * int(v["qty"]) for v in pending.values() if v["sym"] not in held_pos)
        occ = len(held)
        cap = z.get("max_slots")
        intents, outcome = [], {}                              # outcome: fire key -> (result, why, symbol) this pass
        inputs = view.extra.get(self.feed)
        inputs = inputs if inputs is not None else self._inputs(view.now)
        fires, err = self.resolve(inputs)
        for f in fires:
            if not signals.valid_fire(f):
                if f.get("key") is not None:
                    outcome[f["key"]] = ("invalid", "not a valid fire (key, sym, lane, fire_bar, D, plan with max_bars)",
                                         f.get("sym"))
                continue
            if f["key"] in seen:
                continue
            if cap is not None and occ >= cap and row["state"] == "live":
                outcome[f["key"]] = ("cap", f"lane cap: {occ} of {cap} slots taken", f["sym"])
                continue                                       # lane cap (retried while the fire is in window)
            f = dict(f)
            bl = daily.get(f["sym"]) or []
            if f["close"] is None:
                f["close"] = close_on(bl, f["D"])
            q = view.quotes.get(f["sym"])
            px = ref_price(q, view.now)
            dec = decide(row, f, now, px, held, used, dv20(bl, now))
            outcome[f["key"]] = (dec["result"], dec.get("why"), f["sym"])
            if dec["result"] in ("log_only", "skip_size"):
                seen[f["key"]] = str(now)
            if dec["result"] != "intent":
                continue
            occ += 1                                           # only an order takes a slot (lazarus-desk L-47)
            seen[f["key"]] = str(now)
            qty, lim = dec["qty"], dec["limit"]
            te0 = time_exit_at(row, f["fire_bar"], f["plan"])
            eb, dl = entry_window(row, f["fire_bar"])
            pm = {"lz_key": f["key"], "lane": row["id"], "fire_bar": str(f["fire_bar"]), "D": f["D"],
                  "fire_close": f["close"], "plan": f["plan"], "unit": hold_kind(row), "entry_bar": str(eb),
                  "entry_deadline": str(dl), "time_exit_at": str(te0) if te0 is not None else None,
                  "hold_from": row["exit"]["hold_from"], "ref_price": dec["ref0"], "qty_req": qty, "limit": lim,
                  "strategy": f.get("strategy"), "size_class": f.get("size_class"), "source": f.get("source")}
            close = cal.s_close(now)
            intents.append(Intent("enter", f["sym"], qty=float(qty), price_hint=px,
                                  order=OrderSpec(type="limit", limit_price=lim, tif="day",
                                                  window_s=max(60.0, (close - now).total_seconds())),
                                  signal_key=f["key"] + ":EN",
                                  reason=f"{row['id']} {f.get('strategy') or ''} fire {f['D']} close {f['close']}: "
                                         f"entry {qty} @ <= {lim}",
                                  meta={"position_meta": pm, "timeframe": row["kind"]}))
            pending[f["key"]] = {"sym": f["sym"], "qty": qty, "ref_price": dec["ref0"], "limit": lim}
            held.add(f["sym"])
            used += qty * lim
        for sym, p in held_pos.items():
            if sym in working_exit:
                continue
            pm = (p.get("meta") or {}).get("position_meta") or {}
            te0 = cal.ts(pm["time_exit_at"]) if pm.get("time_exit_at") else None
            te = hold_exit(row, pm.get("plan"), te0, ts(p["opened_at"])) if p.get("opened_at") else te0
            px = ref_price(view.quotes.get(sym), view.now)
            ex = exit_decision(te, pm.get("plan"), p["avg"], now, px)
            if not ex or ex["limit"] is None:
                continue
            close = cal.s_close(now)
            intents.append(Intent("exit", sym, order=OrderSpec(type="limit", limit_price=ex["limit"], tif="day",
                                                               window_s=max(60.0, (close - now).total_seconds())),
                                  signal_key=(pm.get("lz_key") or sym) + ":TX", reason=f"{row['id']} {ex['why']}"))
        if not self.RECORD:                                    # as before: a resolver exception gave no fires, nothing recorded
            self._st = {"seen": seen, "pending": pending}
            return intents
        notes = []                                             # the record: observations after the orders, never in their place
        blocked_on = self._blocked_note(notes, st.get("blocked_on"), now)
        done = self._outcome_notes(notes, st.get("outcomes"), outcome, fires, view.now) if err is None else \
            dict(st.get("outcomes") or {})
        health = self._health_note(notes, st.get("health"), inputs)
        resolver_error = self._error_note(notes, st.get("resolver_error"), err, now, bool(intents))
        self._st = {"seen": seen, "pending": pending, "blocked_on": blocked_on, "outcomes": done, "health": health,
                    "resolver_error": resolver_error}
        return intents + notes

    def _blocked_note(self, notes, last, now):
        """FEED-02: a lane whose input is switched off says so once a session (a blocked_data observation with the missing
        piece), and once when the block ends; its decisions are untouched. -> the state's blocked_on ("<session>|<why>")."""
        day = str(cal.day0(now).date())
        if self.blocked:
            on = f"{day}|{self.blocked}"
            if last != on:
                notes.append(Intent("signal", self.row["id"], reason=f"blocked_data: {self.blocked}"[:300],
                                    meta={"blocked": self.blocked}, signal_key=f"lzb:{self.row['id']}:{day}"))
            return on
        if last:
            notes.append(Intent("signal", self.row["id"], reason="blocked_data cleared: its inputs are no longer switched off",
                                meta={"blocked": None, "was": last.split("|", 1)[-1]}, signal_key=f"lzb:{self.row['id']}:{day}:end"))
        return None

    def _outcome_notes(self, notes, last, outcome, fires, now_epoch):
        """FEED-01: one observation for each fire key whose outcome changed this pass. -> {key: outcome} of the fires the
        producer still lists (so the record is bounded by fires x transitions)."""
        last = dict(last or {})
        for k, (res, why, sym) in outcome.items():
            if last.get(k) == res:
                continue
            last[k] = res
            notes.append(Intent("signal", sym or self.row["id"],
                                reason=(f"{self.row['id']} fire {k}: {res}" + (f" ({why})" if why else ""))[:300],
                                meta={"lz_key": k, "outcome": res, "why": why}, signal_key=f"lzo:{k}:{res}:{int(now_epoch)}"))
        keys = {f.get("key") for f in fires}
        return {k: v for k, v in last.items() if k in keys}

    def _health_note(self, notes, last, inputs):
        """FEED-01: the lane's input health (input_health), one observation whenever it changes. -> its fingerprint."""
        h = input_health(inputs, self.inputs, self.row["id"])
        fp = hashlib.sha256(json.dumps(h, sort_keys=True, default=str).encode()).hexdigest()[:16]
        if fp != last:
            notes.append(Intent("signal", self.row["id"], reason=f"{self.row['id']} input health: {_health_line(h)}"[:300],
                                meta={"input_health": h}, signal_key=f"lzh:{self.row['id']}:{fp}"))
        return fp

    def _error_note(self, notes, last, err, now, orders):
        """FEED-01: a resolver exception, once a session per error: raised as the lane's sleeve_error (the engine records it,
        with its trace) when no order rides on this pass, else an observation beside its exits; then its recovery once.
        -> the state's resolver_error ("<session>|<error>")."""
        day = str(cal.day0(now).date())
        if err is None:
            was = last or self._err
            if was:
                notes.append(Intent("signal", self.row["id"], reason=f"{self.row['id']} resolver recovered",
                                    meta={"sleeve_error": None, "was": was.split("|", 1)[-1]},
                                    signal_key=f"lze:{self.row['id']}:{day}:ok"))
            self._err = None
            return None
        on = f"{day}|{type(err).__name__}: {str(err)[:160]}"
        if on in (last, self._err):
            return on
        self._err = on
        what = f"{self.row['id']} resolver {getattr(self.fn, '__name__', 'fn')}: {on.split('|', 1)[1]}"
        if not orders:
            raise RuntimeError(what) from err
        notes.append(Intent("signal", self.row["id"], reason=f"sleeve_error: {what}"[:300], meta={"sleeve_error": on.split("|", 1)[1]},
                            signal_key=f"lze:{self.row['id']}:{day}"))
        return on

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


def all_sleeves():
    """every lane, BLOCKED ones included (their wiring is exercised by the tests on fixture producer files)."""
    return [LazarusLane(r) for r in rows()]


def sleeves():
    return [s for s in all_sleeves() if s.CONFIG.sleeve_id not in BLOCKED]
