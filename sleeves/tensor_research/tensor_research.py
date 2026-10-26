"""Tensor research family: the FolioTend / Griffith Tensor phenotype, genome and Swing research lanes as forward-test
books on the desk's pinned production Tensor engine (v698; desk/feedlib/tensor.py pins), never a re-port of it.

Data (desk/feedlib/tensor_research.py): background jobs build, for the 1,838-name canonical research roster (the
genome universe = the Griffith market-wide union, identical sets), the FolioTend production chart inputs (Yahoo 60m
RTH range 1y via the canonical feed; Yahoo 1d range 2y and 1wk range 10y, the production parse), run the engine and
the vendored research sources over them, run each row's detector (below) and publish events; the sleeves read the
events cache-only and trade them. Every event is a lot of one equal slot (capital / (roster x timeframes the row
trades), split equally among the event's sub-lots); a lot enters at the open of the bar after the event bar
(1d / 1wk: a market order at the next session open; 1h: at once while the next bar is still open) and exits per
its row's rule (a fixed-bar exit closes at the close of bar i+h: market-on-close when that bar ends the session, else
a market order when the bar ends). A lot is skipped when the book has no cash for its slot.

Rows (source -> rule):
  genome_coiled_spring / genome_comeback / genome_leader      FolioTend v619 research sidecar (foliotend-research-
      sidecar.ts, executed) Genome rows on 1h / 1d / 1wk, visible only on a bar with a buy marker or a phenotype; the
      genome response study's trade: next-bar open, close of bar 20, 51 bp round trip (25.5 bp/side).
  genome_daily_green_base_expansion, ro_weekly_cyan_accumulation, ro_weekly_cyan_transition,
  ro_weekly_green_recovery    the same sidecar's phenotypes (DAILY_GREEN_BASE_EXPANSION 1d; WEEKLY_CYAN_ACCUMULATION_
      RECOVERY, WEEKLY_CYAN_EARLY_MARKUP_TRANSITION, WEEKLY_GREEN_EARLY_MARKUP_RECOVERY 1wk); same trade.
  ro_tensor_1h_swing_v615     FolioTend v615 buildTensorSwingSignal (executed): a confirmed 1H Swing, one episode per
      production notification eventKey; the full-universe study's trade (next 1H open, close of bar 20, 25.5 bp/side).
  ro_winner_census_10_20_30   the same deduplicated v615 Swing episodes under the corrected winner-census contract:
      three equal sub-lots closing at bars 10 / 20 / 30.
  ro_swing_transition_1h_v1   v698 Swing Transition (tensor-swing-transition.mjs, the frozen ST classifier) on the
      replica decorated by the production native structural engine; eligible = the frozen primary basket (8 names);
      next 1H open, close of bar 20 (ST core window shared with the parent study's primary), 25.5 bp/side.
  ro_hourly_transition_core_burst  the hourly transition proposal's Core and Burst branches as coded in its mining
      script (winner-basket-mine.mjs): a v615 black-square -> consensus confirmation with daily buy-cyan context and
      Core (hourly ATR 1-2%, nearest EMA21/50/200 0.5-1.0 ATR) or Burst (hourly ATR 2-4%, daily supply/range
      breakout), no sell-red/magenta on the confirmation bar; frozen target / invalidation (the decorated Swing's),
      exit on a later 1H sell-red/magenta (next bar) or bar 20.
  griffith_htf_conditional_h1_h8  TENSOR_HTF_CONDITIONAL_HOLDOUT_1_0_0: labels() of the conditional discovery on a
      fresh 1d / 1wk signal; one sub-lot per matched candidate; close of bar 20 (1d) / 12 (1wk); 100 bp round trip.
  griffith_weekly_cyan_confirmation  CY01-CY18 (tensor_htf_weekly_cyan_study.context / HYPOTHESES) on a fresh weekly
      buy-cyan; 84-day per-hypothesis symbol purge; close of week 12; 100 bp round trip.
  griffith_weekly_green_cyan_deep_confirmation / griffith_weekly_color_forward_shadow  the atoms() conditions of the
      WG/WC and FG/FC candidates on a fresh weekly buy-green / buy-cyan (84-day purge for the deep confirmation);
      close of week 12; 100 bp round trip.
  griffith_htf_relay          TENSOR_HTF_RELAY_1_0_0 arms T1-T7 (the preregistration in TENSOR_DAILY_WEEKLY_STRATEGY_
      AND_CHART_STUDY): entry next session open; exit next open after a completed daily or weekly sell-red /
      sell-magenta.
  griffith_tensor_edge_v01    griffith-tensor-edge/0.1.0 G1 / G2 / C1 (X1 = the REJECT variant): the signal-bar high
      break during the next bar, structural stop at the signal bar's low, exit on the frame's sell-red / sell-magenta.
  griffith_frozen_phenotypes_v4  tensor-frozen-phenotype-specifications/4.0.0 (evaluate_specs over the market scan's
      tail_features on the agentic 420-daily / 260-weekly windows): NEXT_OPEN entry, H4 / H13 / H26_CLOSE sub-lots,
      15 bp/side (the ledger's BASE cost scenario).
  griffith_tensor_phenotype_experiment  TENSOR_EXPERIMENTAL_1_1_0: those predictions -> decision_from_prediction ->
      the three-strategy desk's TENSORX overlay, allocator, handoff and bracket (desk/sleeves/families/griffith.py).
  ro_leaders_rest_v11         work/run-deep-reset-leaders-rest.py: each fresh daily buy-green name through
      LeadersRest.evaluate(corrected=True, is_etf, active_event=False) (LR_1_1_0_CORRECTED) on its Yahoo daily history
      (SPY the benchmark); a SETUP trades through the LRX overlay and the same desk path; the Doorway Deep Reset lens
      (prepare-current-doorway-inputs.py, vendored) rides along as evidence.
  ro_deep_reset_cross_scan    work/run-cross-scan-deep-reset-2026-09-21.py: the dailyGreen / weeklyGreen / weeklyCyan
      groups while the daily EMA21-extension flag is false, Deep Reset recomputed on the group's timeframe (2 years);
      drReset names enter at the next session open and close at the close of session 15 (the lane's horizon).
  qr_tensor_rejection_memory  quant-research-critical tensor_rejection_memory_v1 (MID21): nightly after the SIP
      finality the frozen basket's full all-adjusted daily history -> native rows (engine extract recipe) -> the frozen
      acceptance module (executed); make_plan's laws on the book: time exit at the open of entry + 20 sessions, entries
      at the open, whole shares, limit 1.03 x the session's raw close (tick-rounded down), ticket min(12.5% equity,
      cash) / (limit x 1.001), 8 slots, symbol order, no stop, entries only on a complete basket scan and while no time
      exit is overdue.
  qr_tensor_residual_accumulation  TRACE r10 (trace_r10.py, executed) at the daily scale on the genome tape: the
      playbook universe (operating companies, price >= 10, 60-session median dollar volume >= $50M, 252 daily / 72
      weekly observations), frozen 20-session box, 20-session residual path on factors fit over the 60 sessions before
      it (SPY + the Griffith orchestrator's sector ETF), phase_transition's PRICE_ACCEPTED gate; next session 09:35-09:45
      a limit at cutoff close + 0.5 ATR, shares min(.25% NAV / 1.5 ATR, 8% NAV / P, .5% ADV, 25% sector, gross, cash)
      >= $1,000, 15 names; first-fill barriers P0 - 1.5 ATR / P0 + 3 ATR, renewal failure or 20 sessions (next
      morning), 20-session cooldown, no pyramiding.
  sable_edge_paper_hands      autopilot-desk scout-hands.mjs planEdgeHands (executed) with the paper hands armed, per
      named lineage (lineage.mjs, ten sub-books of capital / 10) over bridge.ts reads of the defaultMandate watchlist's
      completed one-hour Tensor bars (the canonical 1H series; analyzeVectorReplicaBars signalOnly, v698) and
      quote-core.mjs quotes of the same bars; the plan applied as scout-cycle.ts applyEdgePlan does on the Sable
      desk: paper_buy -> proposeBuy (canEnter under defaultMandate: 6 names, no ETF entries, anti-chase extension
      1.85 ATR / RSI 72, swingSizeShares, the applyFill bracket), paper_sell / paper_trim / park / stand_aside /
      size_down / review_stop; each bar the desk's applyStopsAndTargets and the 2% daily-loss park.

Gone under the cutover doctrine: the research authority boundaries (automaticInfluence / strategyAuthority /
brokerAuthority false, SHADOW / RESEARCH_ONLY states, promotion and qualification gates), and for the experiment
the T4 / logic qualification (the source config already authorized unqualified paper) and the desk-wide gates the
griffith family removes; MID21's broker / account / OPG-capability / ledger-reconciliation blocks and its
source-verification flag; TRACE's RESEARCH_ONLY_CANONICAL_INPUT_BLOCKED status and DEPLOYMENT_APPROVED / native
qualification flags; the Edge policy's hands switch (off by default; armed here, the lane being the paper hands).

Named divergences (rows below the event books): the experiment takes the 25 oldest unseen predictions per cycle (the
source's ORDER BY created_at LIMIT 25 only ever planned the first 25), admits each prediction's own bars at the
cycle's clock and skips one that fails admission (the source admitted the scope evidence inside
decision_from_prediction and an admission error ended its cycle); MID21 orders are opening limits for 10 minutes
from the open (no OPG auction order) on the desk's equity daily source; TRACE arms on the phase gate alone - the B+8
ridge arming (CONTINUE - FAIL >= .15, conservative value > .0025) needs a model fit on mature canonical first-fill
episodes that do not exist - renewal failure uses the daily path's contrast and pressure (not hourly), ADV is the
20-session mean volume, a name outside the sector map uses SPY as its sector factor and carries no sector cap,
the 20% forecast-volatility scaling and the minute-volume / spread capacity checks are not applied; Sable's Edge
brief (scout research: headlines / filings / calendar and the location-first scan snapshot) is not built, so the
hands plan on an empty brief (no brief-driven parks, pauses or extension tags), the bars are the canonical 1H series
(tensor_swing's; the owner's 1H decision, 2026-10-18 - the source read completed five-minute bars), so the scout
runs once per completed hour, 2-11 minutes after it closes (the 15:30 stub at the next open), and the quote, the
anti-chase and RSI checks and the stops and targets are taken on those hours, the regime / earnings-window flags
are never raised, orders are market orders for 10 minutes, and each lineage sub-book is a virtual ledger inside
the sleeve's book (a fill's price = the book's cost basis net of the lineages' earlier lots; exits credited at the
bar close); the forward-shadow spec names no primary horizon or cost (horizons 1-52 weeks are observed), so its
book trades the parent confirmation spec's 12 weeks and 100 bp round trip.

Named divergences (all rows): the engine is v698 (the desk's pin), not the row's research-era engine (v615/v619
anna-replica bb73871b; the agentic tensor_canonical; MID21's canonical 597433d5; Sable's Grok Tensor clone package
1b52adb); the bars are Yahoo's (production FolioTend input) where the
Griffith HTF studies used Alpaca all-adjusted daily history with ISO-week aggregates over their full span; entry at
the next bar's open is a market order on the first desk pass at or after it (no opening-auction order; 1h: the job
publishes minutes after the bar closes, so the fill is the price then); a study's close-to-close event return
(entry at the event close) is traded from the next open; research sizing is per event, the book's is one slot."""
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...venues.sim import iex_near
from ...feedlib import tensor_features as tf
from ...feedlib import tensor_research as plane

FAMILY = "tensor_research"
FEED = "tensor_research_events"
ARCHIVE = {"repo": "foliotend-research-operations-archive", "ref": "main",
           "commit": "1a6a8ca208b71e8fbd70efa0c5cfe4496d7ddf65"}
AGENTIC = {"repo": "agentic-trading-desk", "ref": "main", "commit": "4c8c179c5988d6e603c1f3c5f28f93e2344ca225"}
V619 = dict(ARCHIVE, path="outputs/foliotend-daily-weekly-signal-winner-study-2026-09-25/production-source-v619.tar.gz",
            blob="787356f885efa9d9f256d36bacb00eb8be24105b", member="app/lib/foliotend-research-sidecar.ts")
GENOMES = {"genome_coiled_spring": "COILED_SPRING", "genome_comeback": "COMEBACK", "genome_leader": "LEADER"}
PHENOTYPES = {"genome_daily_green_base_expansion": ("1d", "DAILY_GREEN_BASE_EXPANSION"),
              "ro_weekly_cyan_accumulation": ("1wk", "WEEKLY_CYAN_ACCUMULATION_RECOVERY"),
              "ro_weekly_cyan_transition": ("1wk", "WEEKLY_CYAN_EARLY_MARKUP_TRANSITION"),
              "ro_weekly_green_recovery": ("1wk", "WEEKLY_GREEN_EARLY_MARKUP_RECOVERY")}
ST_PRIMARY = ("AG", "CMG", "CRDO", "FLY", "LTBR", "UAMY", "VRT", "XPEV")
ST_SECONDARY = ("WYFI", "BLDP", "CLS", "CRML", "ERIE", "EXK", "OKLO", "REMX", "SMG", "URA", "WT", "AEHR", "NBIS", "ASAN",
                "FIVN", "GTLB", "LITE", "SOXL")
STUDY_SIDE_BPS = 25.5                    # 25 bp slippage + 0.5 bp fee per side (51 bp round trip)
SELLS = ("sell-red", "sell-magenta")
HORIZON = 20
SPECS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                         "griffith")


def spec_json(name):
    with open(os.path.join(SPECS_DIR, name)) as f:
        return json.load(f)


# -- frames ---------------------------------------------------------------------------------------------------------
def ids_of(row):
    """tensor_htf_chart_factory.signal_ids over a runner row (primary markers, dcb-<marker>, enrichment ids)."""
    out = list(row.get("primaryMarkers") or [])
    if row.get("dcbMarker"):
        out.append(f"dcb-{row['dcbMarker']}")
    out.extend(row.get("enrichmentIds") or [])
    return out


class Frame:
    """one symbol's runner output for one interval, with the lazily computed research features."""

    def __init__(self, symbol, interval, now, result, job, spy=None):
        self.symbol, self.interval, self.now = symbol, interval, now
        views = result.get("views") or {}
        fd = views.get("fd") or {}
        self.fd = [r for r in fd.get("bars") or [] if r.get("barFinality") == "closed"]
        self.ag = [r for r in (views.get("ag") or {}).get("bars") or [] if r.get("barFinality") == "closed"]
        self.decorated = bool(fd.get("decorated"))
        self.input = [{"time": int(r[0]), "open": float(r[1]), "high": float(r[2]), "low": float(r[3]),
                       "close": float(r[4]), "volume": float(r[5])} for r in fd.get("input") or []]
        self.series = job.get("bars") or []
        self.spy = spy
        self._cache = {}

    @property
    def last(self):
        return self.fd[-1] if self.fd else None

    def active(self, k=-1):
        return set(ids_of(self.fd[k])) if len(self.fd) >= -k else set()

    def fresh(self, k=-1):
        if len(self.fd) < 1 - k:
            return set(ids_of(self.fd[k])) if self.fd else set()
        return set(ids_of(self.fd[k])) - set(ids_of(self.fd[k - 1]))

    def ages(self, k=-1):
        """signalAges as the HTF ledger computes them at the event bar: bars since the last earlier bar on which
        each signal was active (over the tail the runner returned)."""
        last = {}
        end = len(self.fd) + k
        for i in range(end):
            for s in ids_of(self.fd[i]):
                last[s] = i
        return {s: end - i for s, i in last.items()}

    def ledger_features(self):
        """the HTF event-ledger features of the newest bar: feature_tape + the replica fields + ages + fresh."""
        if "ledger" not in self._cache:
            if len(self.input) < 2 or not self.fd:
                self._cache["ledger"] = None
            else:
                bar = self.fd[-1]
                f = dict(tf.feature_tape(self.input, only_latest=True)[-1])
                f.update({k: bar.get(k) for k in ("bullishVotes", "bearishVotes", "totalVotes", "fastState", "slowState",
                                                  "activeCall", "callLifecycle", "candleRegime", "rvol", "bbUpper",
                                                  "bbLower", "macdHistogram", "tensorContext")})
                f["signalAges"] = self.ages()
                f["freshSignals"] = sorted(self.fresh())
                self._cache["ledger"] = f
        return self._cache["ledger"]

    def spy_by_date(self):
        return {tf._day(b["time"]): float(b["close"]) for b in (self.spy or {}).get("input") or []}

    def advanced_features(self):
        """the weekly advanced-feature row (tensor_htf_advanced_features.build): ledger features + technical_tape +
        the same-date SPY regime."""
        if "advanced" not in self._cache:
            base = self.ledger_features()
            if base is None or not self.spy:
                self._cache["advanced"] = None
            else:
                adv = tf.technical_tape(self.input, self.spy_by_date(), only_latest=True)[-1]
                f = {**base, **adv}
                f["spyRegime"] = (self.spy.get("regime_by_date") or {}).get(tf._day(self.input[-1]["time"]))
                self._cache["advanced"] = f
        return self._cache["advanced"]

    def market_context(self, window):
        """the market scan's frame context on the agentic window: {barCutoff, featureVersion, features}."""
        key = ("scan", window)
        if key not in self._cache:
            bars = self.input[-window:] if self.input else []
            spy = (self.spy or {}).get("input") or []
            if len(bars) < 200 or not self.ag:
                self._cache[key] = None
            else:
                tail = [dict(r, time=int(r["timestamp"]),
                             enrichment={"signals": [{"id": i} for i in r.get("enrichmentIds") or []]})
                        for r in self.ag]
                feats = tf.tail_features(bars, {"researchTail": tail}, spy[-window:] if spy else None, self.interval)
                self._cache[key] = {"symbol": self.symbol, "timeframe": self.interval, "barCutoff": int(bars[-1]["time"]),
                                    "featureVersion": tf.FEATURE_VERSION, "features": feats}
        return self._cache[key]


# -- event construction ---------------------------------------------------------------------------------------------
def event(sid, frame, tags, horizons=(HORIZON,), **extra):
    row = frame.last
    t = int(row["timestamp"])
    return dict({"key": f"{sid}|{frame.symbol}|{frame.interval}|{t}|{'+'.join(sorted(tags))}", "sid": sid,
                 "symbol": frame.symbol, "interval": frame.interval, "t": t, "tags": sorted(tags),
                 "horizons": list(horizons), "close": row.get("close"), "high": row.get("high"),
                 "low": row.get("low")}, **extra)


def detect_genome(sid, gid):
    def run(frame, col):
        side = (frame.last or {}).get("sidecar") or {}
        if any(g.get("id") == gid for g in side.get("genomes") or []):
            return [event(sid, frame, [gid])]
        return []
    return run


def detect_phenotype(sid, pid):
    def run(frame, col):
        side = (frame.last or {}).get("sidecar") or {}
        if pid in (side.get("phenotypes") or []):
            return [event(sid, frame, [pid])]
        return []
    return run


def detect_swing615(sid, horizons):
    def run(frame, col):
        sw = (frame.last or {}).get("swing615") or {}
        if sw.get("confirmed") and sw.get("eventKey"):
            ev = event(sid, frame, ["SWING_V615"], horizons, episode=sw["eventKey"])
            ev["key"] = f"{sid}|{sw['eventKey']}"
            return [ev]
        return []
    return run


def detect_st(frame, col):
    sw = (frame.last or {}).get("swing698") or {}
    tr = sw.get("transition") or {}
    if sw.get("confirmed") and tr.get("qualifies") and tr.get("eligible") and frame.symbol in ST_PRIMARY:
        ev = event("ro_swing_transition_1h_v1", frame, ["SWING_TRANSITION_1H_V1"])
        ev["key"] = f"ro_swing_transition_1h_v1|{frame.symbol}:1h:swing:{sw.get('setupBarTimestamp')}:confirmed"
        ev["factors"] = tr.get("factors") or []
        return [ev]
    return []


def ema_last(values, period):
    a, cur = 2 / (period + 1), values[0]
    for v in values[1:]:
        cur = a * v + (1 - a) * cur
    return cur


def detect_core_burst(frame, col):
    """the proposal's Core / Burst on a v615 confirmation (winner-basket-mine.mjs predicates)."""
    row = frame.last or {}
    sw = row.get("swing615") or {}
    if not (sw.get("confirmed") and sw.get("eventKey")):
        return []
    daily = (col.ctx_in.get("daily") or {}).get(frame.symbol) or {}
    if "buy-cyan" not in (daily.get("markers") or []):
        return []
    if set(row.get("primaryMarkers") or []) & set(SELLS):
        return []
    loc = row.get("vectorStructuralLocation") or {}
    close = float(row["close"])
    atr = loc.get("atr")
    if not frame.decorated or not atr or not close:
        return []
    atr_pct = float(atr) / close * 100
    closes = [float(b["c"]) for b in frame.series] or [close]
    dists = [abs((close / ema_last(closes, p) - 1) * 100) / atr_pct for p in (21, 50, 200)]
    nearest = min(dists)
    tags = []
    if 1 <= atr_pct < 2 and 0.5 <= nearest < 1:
        tags.append("CORE")
    if 2 <= atr_pct < 4 and daily.get("trigger") in ("supply-breakout", "range-breakout"):
        tags.append("BURST")
    if not tags:
        return []
    ev = event("ro_hourly_transition_core_burst", frame, tags, stop=sw.get("invalidation"), target=sw.get("target"),
               exit_on_sell=True, atr_pct=round(atr_pct, 4), nearest_ema_atr=round(nearest, 4))
    ev["key"] = f"ro_hourly_transition_core_burst|{sw['eventKey']}"
    return [ev]


# -- Griffith HTF (agentic) detectors --------------------------------------------------------------------------------
HOLDOUT = None
CYAN_SPEC = None
COLOR_SPEC = None
FORWARD_SPEC = None
REGISTRY = None


def _specs():
    global HOLDOUT, CYAN_SPEC, COLOR_SPEC, FORWARD_SPEC, REGISTRY
    if HOLDOUT is None:
        HOLDOUT = spec_json("tensor_htf_holdout_spec.json")
        CYAN_SPEC = spec_json("tensor_htf_weekly_cyan_spec.json")
        COLOR_SPEC = spec_json("tensor_htf_weekly_color_spec.json")
        FORWARD_SPEC = spec_json("tensor_htf_weekly_color_forward_spec.json")
        REGISTRY = spec_json("tensor_phenotype_registry.json")


def operating(col, symbol):
    """the HTF ledger universe: OPERATING_COMPANY_CANDIDATE_CURRENT_METADATA (tensor_htf_asset_classification)."""
    return (col.assets.get(symbol) or {}).get("classification") == "OPERATING_COMPANY_CANDIDATE_CURRENT_METADATA"


def detect_holdout(frame, col):
    _specs()
    if not operating(col, frame.symbol):
        return []
    f = frame.ledger_features()
    fresh = frame.fresh()
    if f is None or not fresh:
        return []
    found = tf.labels(frame.active(), fresh, f)
    tags = [c["id"] for c in HOLDOUT["candidates"] if c["timeframe"] == frame.interval and c["label"] in found]
    if not tags:
        return []
    h = int(HOLDOUT["primaryHorizon"][frame.interval])
    return [event("griffith_htf_conditional_h1_h8", frame, tags, (h,))]


def detect_cyan(frame, col):
    _specs()
    active, fresh = frame.active(), frame.fresh()
    if not operating(col, frame.symbol) or "buy-cyan" not in active or "buy-cyan" not in fresh:
        return []
    f = frame.ledger_features()
    if f is None:
        return []
    ctx = tf.cyan_context(f, active)
    tags = [hid for hid, pred in tf.CYAN_HYPOTHESES if hid in CYAN_SPEC["hypotheses"] and pred(ctx)]
    if not tags:
        return []
    return [event("griffith_weekly_cyan_confirmation", frame, tags, (int(CYAN_SPEC["primaryHorizonWeeks"]),),
                  purge_days=int(CYAN_SPEC["purgeDays"]))]


def _atoms(frame):
    f = frame.advanced_features()
    if f is None:
        return None
    return tf.atoms(f, frame.active(), {})


def detect_color(sid, spec_name, purge):
    def run(frame, col):
        _specs()
        spec = COLOR_SPEC if spec_name == "color" else FORWARD_SPEC
        fresh = frame.fresh()
        if not operating(col, frame.symbol) or not fresh & {"buy-green", "buy-cyan"}:
            return []
        atoms = _atoms(frame)
        if atoms is None:
            return []
        tags = [c["id"] for c in spec["candidates"] if c["color"] in fresh and set(c["conditions"]) <= atoms]
        if not tags:
            return []
        h = int(spec.get("primaryHorizonWeeks") or COLOR_SPEC["primaryHorizonWeeks"])
        extra = {"purge_days": int(spec["purgeDays"])} if purge else {}
        return [event(sid, frame, tags, (h,), **extra)]
    return run


def weekly_episode(rows):
    """an active bullish weekly episode at the newest bar: the latest fresh buy-green / buy-cyan not followed by a
    weekly sell-red / sell-magenta -> its bar time, else None."""
    start = None
    prev = set()
    for r in rows:
        ids = set(ids_of(r))
        fresh = ids - prev
        if fresh & {"buy-green", "buy-cyan"}:
            start = int(r["timestamp"])
        if ids & set(SELLS):
            start = None
        prev = ids
    return start


def detect_relay(frame, col):
    fresh = frame.fresh()
    tags = []
    extra = {}
    if frame.interval == "1d":
        episode = ((col.ctx_in.get("episodes") or {}).get(frame.symbol))
        if "buy-green" in fresh:
            tags.append("T1_DAILY_GREEN")
            if episode:
                tags.append("T4_DAILY_GREEN_IN_WEEKLY_BULL_EPISODE")
                if frame.active() & {"consensus-buy", "state-p"}:
                    tags.append("T5_T4_PLUS_CONSENSUS_BUY_OR_LIFECYCLE_P")
                extra["episode"] = episode
        if "dcb-buy" in fresh and episode:
            tags.append("T6_GREEN_STAR_IN_WEEKLY_BULL_EPISODE")
            extra["episode"] = episode
    else:
        if "buy-green" in fresh:
            tags.append("T2_WEEKLY_GREEN")
        if "buy-cyan" in fresh:
            tags.append("T3_WEEKLY_CYAN")
    if not tags:
        return []
    return [event("griffith_htf_relay", frame, tags, (), exit_on_sell="1d+1wk", **extra)]


def detect_edge(frame, col):
    """griffith-tensor-edge/0.1.0: G1 (1d), G2 / C1 (1wk); X1 exhaustion rejects C1 (its REJECT variant)."""
    f = frame.advanced_features()
    fresh = frame.fresh()
    if f is None or not fresh & {"buy-green", "buy-cyan"}:
        return []
    num = tf.num
    tags = []
    up = num(f.get("upVolumeShare13"))
    constructive = (up is not None and up >= 0.50) or (num(f.get("obvSlope13")) or 0) > 0 \
        or (num(f.get("adlSlope13")) or 0) > 0
    ema21 = num(f.get("ema21Distance"))
    rsi14 = num(f.get("rsi14"))
    r13 = num(f.get("return13"))
    rs13, rs26 = num(f.get("relativeStrength13")), num(f.get("relativeStrength26"))
    comp = num(f.get("compression20To60"))
    if frame.interval == "1d" and "buy-green" in fresh:
        if f.get("regime") == "above rising EMA200" and comp is not None and comp <= 0.75 \
                and f.get("breakout20") is True and ema21 is not None and ema21 < 0.15 and constructive:
            tags.append("G1_DAILY_GREEN_IGNITION")
    if frame.interval == "1wk" and "buy-green" in fresh:
        long_base = comp is not None and comp <= 0.75 or (num(f.get("drawdown52")) or 0) <= -0.30
        rs_ok = (rs13 is not None and rs13 > 0) or (rs26 is not None and rs13 is not None and rs13 > rs26)
        expanding = (num(f.get("volume4To20")) or 0) >= 1.0
        if long_base and rs_ok and expanding and ema21 is not None and ema21 < 0.15:
            tags.append("G2_WEEKLY_GREEN_EMERGENCE")
    if frame.interval == "1wk" and "buy-cyan" in fresh:
        exhausted = (rsi14 is not None and rsi14 >= 75) or (r13 is not None and r13 >= 1.0) \
            or "extension-warning" in frame.active()
        if exhausted:
            tags.append("X1_CYAN_EXHAUSTION_HARVEST:REJECT")
        elif rs13 is not None and rs13 > 0 and rs26 is not None and rs26 > 0 and r13 is not None \
                and 0.25 <= r13 <= 0.60 and rsi14 is not None and 55 <= rsi14 <= 72 and up is not None and up >= 0.55 \
                and (num(f.get("range4To13")) or 1) <= 0.75:
            tags.append("C1_WEEKLY_CYAN_REACCELERATION")
    tradable = [t for t in tags if not t.endswith(":REJECT")]
    if not tags:
        return []
    row = frame.last
    return [event("griffith_tensor_edge_v01", frame, tags, (), trade=bool(tradable), exit_on_sell=frame.interval,
                  stop=row.get("low"), trigger=row.get("high"))]


def detect_frozen(frame, col):
    """the frozen v4 registry over the market scan context: predictions (shared with the experiment)."""
    _specs()
    window = plane.AG_WINDOW[frame.interval]
    ctx = frame.market_context(window)
    if ctx is None:
        return []
    specs = [s for s in REGISTRY["phenotypes"] if s.get("enabled")]
    matches = tf.evaluate_specs({"symbol": frame.symbol, "frames": {frame.interval: ctx}}, specs)
    out = []
    for m in matches:
        spec = next(s for s in specs if s["id"] == m["phenotypeId"])
        frames_ = {str(r.get("path")).split(".")[1] for r in spec["required"] if str(r.get("path")).startswith("frames.")}
        if frames_ != {frame.interval}:
            continue
        cutoff = int(ctx["barCutoff"])
        obs = tf.digest({"symbol": frame.symbol, "frame": frame.interval, "cutoff": cutoff, "features": ctx["features"]})
        pid = "tfpred:" + tf.digest({"spec": spec["id"], "version": spec["version"], "symbol": frame.symbol,
                                     "timeframe": frame.interval, "cutoff": cutoff})[:32]
        bars = frame.input[-window:]
        ev = event("griffith_frozen_phenotypes_v4", frame, [spec["id"]], (4, 13, 26), prediction={
            "prediction_id": pid, "observation_hash": obs, "specification_id": spec["id"], "symbol": frame.symbol,
            "timeframe": frame.interval, "event_cutoff": cutoff,
            "bars": [{"t": datetime.fromtimestamp(b["time"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"], "v": b["volume"]}
                     for b in bars]})
        out.append(ev)
    return out


DETECTORS = {
    "1h": [*[(sid, detect_genome(sid, gid)) for sid, gid in GENOMES.items()],
           ("ro_tensor_1h_swing_v615", detect_swing615("ro_tensor_1h_swing_v615", (HORIZON,))),
           ("ro_winner_census_10_20_30", detect_swing615("ro_winner_census_10_20_30", (10, 20, 30))),
           ("ro_swing_transition_1h_v1", detect_st),
           ("ro_hourly_transition_core_burst", detect_core_burst)],
    "1d": [*[(sid, detect_genome(sid, gid)) for sid, gid in GENOMES.items()],
           ("genome_daily_green_base_expansion", detect_phenotype("genome_daily_green_base_expansion",
                                                                  "DAILY_GREEN_BASE_EXPANSION")),
           ("griffith_htf_conditional_h1_h8", detect_holdout),
           ("griffith_htf_relay", detect_relay),
           ("griffith_tensor_edge_v01", detect_edge),
           ("griffith_frozen_phenotypes_v4", detect_frozen)],
    "1wk": [*[(sid, detect_genome(sid, gid)) for sid, gid in GENOMES.items()],
            *[(sid, detect_phenotype(sid, pid)) for sid, (iv, pid) in PHENOTYPES.items() if iv == "1wk"],
            ("griffith_htf_conditional_h1_h8", detect_holdout),
            ("griffith_weekly_cyan_confirmation", detect_cyan),
            ("griffith_weekly_green_cyan_deep_confirmation",
             detect_color("griffith_weekly_green_cyan_deep_confirmation", "color", True)),
            ("griffith_weekly_color_forward_shadow", detect_color("griffith_weekly_color_forward_shadow", "forward",
                                                                  False)),
            ("griffith_htf_relay", detect_relay),
            ("griffith_tensor_edge_v01", detect_edge),
            ("griffith_frozen_phenotypes_v4", detect_frozen)],
}
EXTRA_DETECTORS = {"1h": [], "1d": [], "1wk": []}      # rows defined further below register here


def views(interval, symbol=None):
    """the runner views each interval's detectors need."""
    if interval == "1h":
        return [{"name": "fd", "tail": 3, "sidecar": True, "swing615": True,
                 "swing698": symbol in ST_PRIMARY + ST_SECONDARY, "decorate": "on_confirmed"}]
    window = plane.AG_WINDOW[interval]
    return [{"name": "fd", "tail": 40, "sidecar": True, "input": True,
             "decorate": "on_marker:buy-cyan" if interval == "1d" else "never"},
            {"name": "ag", "window": window, "tail": 2}]


class Collector:
    """runs the interval's detectors over each frame as the runner returns it and gathers the events, the context the
    other jobs / sleeves read (daily markers and locations, sells, weekly episodes) and the per-symbol errors."""

    def __init__(self, interval, now, context=None, root=None, day=None):
        self.interval, self.now = interval, now
        self.ctx_in = context or {}
        self.root = root
        self.day = day
        self.events = defaultdict(list)
        self.context = {"daily": {}, "sells": {}, "episodes": {}}
        self.errors = {}
        self.n_frames = self.n_events = self.n_fresh = 0
        self.spy = None
        self.assets = plane.load_assets(root) if root else {}

    def fresh_enough(self, t):
        if self.interval == "1h":
            return plane.hour_end(t) >= self.now - 2 * 3600
        if self.interval == "1d":
            return self.day is None or plane.session_of(t) == self.day
        return self.day is None or plane.week_monday(t) == self.day - timedelta(days=self.day.weekday())

    def add(self, job, res):
        sym = job["symbol"].upper()
        if not res.get("ok"):
            self.errors[sym] = res.get("error") or "runner error"
            return
        for name, v in (res.get("views") or {}).items():
            if isinstance(v, dict) and v.get("error"):
                self.errors[sym] = f"{name}: {v['error']}"
        frame = Frame(sym, self.interval, self.now, res, job, spy=self.spy)
        if sym == "SPY" and self.interval != "1h" and frame.input:
            struct = tf.feature_tape(frame.input)
            self.spy = {"input": frame.input,
                        "regime_by_date": {tf._day(b["time"]): s["regime"] for b, s in zip(frame.input, struct)}}
            frame.spy = self.spy
        if not frame.last:
            return
        self.n_frames += 1
        row = frame.last
        t = int(row["timestamp"])
        if set(row.get("primaryMarkers") or []) & set(SELLS):
            self.context["sells"][sym] = t
        if self.interval == "1d":
            loc = row.get("vectorStructuralLocation") or {}
            self.context["daily"][sym] = {"t": t, "markers": list(row.get("primaryMarkers") or []),
                                          "trigger": loc.get("trigger")}
        if self.interval == "1wk":
            ep = weekly_episode(frame.fd)
            if ep:
                self.context["episodes"][sym] = ep
        if not self.fresh_enough(t):
            return
        self.n_fresh += 1
        for sid, fn in DETECTORS.get(self.interval, []) + EXTRA_DETECTORS.get(self.interval, []):
            try:
                for ev in fn(frame, self) or []:
                    self.events[sid].append(ev)
                    self.n_events += 1
            except Exception as e:                     # one detector's failure never blocks the others
                self.errors[f"{sym}:{sid}"] = f"{type(e).__name__}: {str(e)[:160]}"

    def finish(self):
        return self

    def result(self):
        return {"events": dict(self.events), "context": self.context}


# -- the event book -------------------------------------------------------------------------------------------------
def _px(q):
    """an entry's sizing price: the ask, unless IEX's two-sided book is too wide to be near the NBBO (the sim's own rule,
    desk/venues/sim.py iex_near), then the last print. AWR's IEX book [70.21, 94.57] against an 83.46 NBBO on
    2026-10-16 sized the genome lots at 94.57, 12% short of their slot."""
    q = q or {}
    if q.get("last") and q.get("bid") and q.get("ask") and not iex_near(q["bid"], q["ask"]):
        return float(q["last"])
    for k in ("ask", "last", "bid"):
        v = q.get(k)
        if v:
            return float(v)
    return None


STUDY_COST = object()                    # EventBook default: the row's study cost (COST_BPS); None = the engine's fees


class EventBook(Sleeve):
    """a research row's forward-test book: events -> lots (entry at the next bar's open, the row's exits)."""
    INTERVALS = ("1d",)
    SLOT_TIMEFRAMES = 1
    COST_BPS = STUDY_SIDE_BPS
    SOURCE = {}
    UNIVERSE = None
    TITLE = ""

    def __init__(self, sleeve_id, intervals=None, cost_bps=STUDY_COST, source=None, slots=None, title=""):
        self.sid = sleeve_id
        self.intervals = tuple(intervals or self.INTERVALS)
        c = self.COST_BPS if cost_bps is STUDY_COST else cost_bps
        self.cost_bps = None if c is None else float(c)      # None: no cost model in the source -> engine fees
        self.slots = int(slots or len(plane.roster()) * len(self.intervals))
        self.engine = None
        params = {"intervals": list(self.intervals), "slots": self.slots}
        if self.cost_bps is not None:
            params["cost_bps"] = self.cost_bps
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family=FAMILY, cadence_s=300, universe=tuple(self.UNIVERSE or ()),
            needs={"feeds": [FEED], "quotes": {"source": "equity"}}, schedule="rth",
            params=params, source=dict(source or self.SOURCE), state_schema={"lots": "dict", "seen": "dict"})
        self.title = title

    def _cost(self, meta=None):
        out = dict(meta or {})
        if self.cost_bps is not None:
            out["cost_bps"] = self.cost_bps
        return out

    def bind(self, engine):
        self.engine = engine

    def _stored(self):
        if self.engine is None:
            return {}
        return self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}

    def quote_universe(self, now, book):
        """held names, open lots, and the names of events not yet taken (their lots may enter on this pass)."""
        st = self._stored()
        names = {i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:")}
        names |= {lot["symbol"] for lot in (st.get("lots") or {}).values() if lot.get("state") in ("pending", "working")}
        seen = st.get("seen") or {}
        root = getattr(self.engine, "root", None)
        for iv in self.intervals if root else ():
            p = plane.events_path(root, iv)
            try:
                m = os.stat(p).st_mtime_ns
            except OSError:
                continue
            memo = self.__dict__.setdefault("_doc_memo", {})
            if memo.get(iv, (None,))[0] != m:
                memo[iv] = (m, plane.load_events(root, iv) or {})
            names |= {ev["symbol"] for ev in (memo[iv][1].get("events") or {}).get(self.sid, [])
                      if ev["key"] not in seen}
        return sorted(names)

    # -- lots ----------------------------------------------------------------------------------------------------
    def make_lots(self, ev, now):
        """the event's lots: one per (tag, horizon) splitting the event slot (row hook)."""
        tags = ev.get("tags") or ["EVENT"]
        horizons = ev.get("horizons") or [None]
        n = len(tags) * len(horizons)
        iv, t = ev["interval"], int(ev["t"])
        entry_at = plane.entry_open(iv, t)
        lots = []
        for tag in tags:
            for h in horizons:
                exit_at, moc = plane.exit_close(iv, t, int(h)) if h else (None, False)
                lots.append({"key": f"{ev['key']}|{tag}|h{h}", "event": ev["key"], "symbol": ev["symbol"], "interval": iv,
                             "t": t, "tag": tag, "h": h, "frac": 1.0 / n, "entry_at": entry_at,
                             "entry_until": self.entry_deadline(iv, entry_at), "exit_at": exit_at, "moc": moc,
                             "stop": ev.get("stop"), "target": ev.get("target"),
                             "exit_on_sell": ev.get("exit_on_sell"), "state": "pending", "created": now})
        return lots

    @staticmethod
    def entry_deadline(iv, entry_at):
        """a lot enters during the entry bar (1h) / the entry session (1d, 1wk)."""
        if iv == "1h":
            return plane.hour_end(entry_at)
        return cal.session_close(cal._as_date(entry_at))

    def admit(self, ev, st, now):
        """row hook: False skips the event (e.g. a purge rule); default admits every event."""
        return True

    def ingest(self, docs, st, now):
        seen = st.setdefault("seen", {})
        lots = st.setdefault("lots", {})
        for iv in self.intervals:
            doc = docs.get(iv) or {}
            for ev in (doc.get("events") or {}).get(self.sid, []):
                if ev["key"] in seen:
                    continue
                seen[ev["key"]] = now
                if not self.admit(ev, st, now):
                    continue
                for lot in self.make_lots(ev, now):
                    lots[lot["key"]] = lot
        for k in [k for k, v in seen.items() if now - float(v) > 120 * 86400]:
            seen.pop(k)

    def sells(self, docs, lot, now):
        """True once a completed sell-red / sell-magenta printed on the lot's exit frame(s) after its entry bar."""
        which = lot.get("exit_on_sell")
        if not which:
            return False
        ivs = ("1d", "1wk") if which == "1d+1wk" else (lot["interval"],) if which is True else tuple(str(which).split("+"))
        for iv in ivs:
            t = ((docs.get(iv) or {}).get("context") or {}).get("sells", {}).get(lot["symbol"])
            if t and int(t) > int(lot["t"]) and plane.bar_end(iv, int(t)) > float(lot.get("filled_at") or lot["entry_at"]) - 1:
                return True
        return False

    def signal(self, view):
        st = dict(view.state or {})
        st["lots"] = {k: dict(v) for k, v in (st.get("lots") or {}).items()}
        now = float(view.now)
        docs = view.extra.get(FEED) or {}
        self.ingest(docs, st, now)
        lots = st["lots"]
        pending_keys = {po.get("signal_key") for po in view.extra.get("pending_orders") or []
                        if float(po.get("filled_v") or 0) < float(po.get("vqty") or 0) * (1 - 1e-6) - 1e-9}
        held = {i.split(":", 1)[1]: float(p["qty"]) for i, p in view.positions.items() if i.startswith("EQ:")}
        self.reconcile(lots, held, pending_keys, now)
        intents = []
        intents += self.exits(view, docs, lots, held, pending_keys, now)
        intents += self.entries(view, lots, pending_keys, now)
        for k in [k for k, v in lots.items() if v["state"] in ("done", "skipped", "failed")
                  and now - float(v.get("closed_at") or v.get("created") or now) > 30 * 86400]:
            lots.pop(k)
        self._st = st
        return intents

    def reconcile(self, lots, held, pending_keys, now):
        """working entries whose order is gone are open when the position carries them, else failed; a closing lot
        whose exit order is gone is done, unless the position still holds shares beyond the other lots' claims (its
        exit ended unfilled): those it keeps, open again, so its exit is sent again; open lots shrink (newest first)
        when the position holds less than they claim."""
        by_sym = defaultdict(list)
        for lot in lots.values():
            by_sym[lot["symbol"]].append(lot)
        for sym, group in by_sym.items():
            pos = held.get(sym, 0.0)
            claimed = sum(float(l["qty"]) for l in group if l["state"] in ("open", "closing"))
            for l in sorted((l for l in group if l["state"] == "working" and l["key"] not in pending_keys),
                            key=lambda x: x["created"]):
                if pos >= claimed + float(l["qty"]) * (1 - 1e-6) - 1e-9:
                    l["state"] = "open"
                    l["filled_at"] = now
                    claimed += float(l["qty"])
                else:
                    l.update(state="failed", closed_at=now, reason="entry not filled")
            gone = sorted((l for l in group if l["state"] == "closing" and l.get("exit_key") not in pending_keys),
                          key=lambda x: x["created"])
            left = pos - sum(float(l["qty"]) for l in group if l["state"] == "open" or (l["state"] == "closing"
                                                                                          and l not in gone))
            for l in gone:
                keep = min(float(l["qty"]), max(0.0, left))
                if keep > max(1e-6, 1e-6 * float(l["qty"])):
                    left -= keep
                    l.update(state="open", qty=keep)
                else:
                    l.update(state="done", closed_at=now)
            open_ = [l for l in group if l["state"] in ("open", "closing")]
            claimed = sum(float(l["qty"]) for l in open_)
            for l in sorted(open_, key=lambda x: x["created"], reverse=True):
                if claimed <= pos + 1e-9:
                    break
                cut = min(float(l["qty"]), claimed - pos)
                l["qty"] = float(l["qty"]) - cut
                claimed -= cut
                if l["qty"] <= 1e-9:
                    l.update(state="done", closed_at=now, reason="position closed elsewhere")

    def entries(self, view, lots, pending_keys, now):
        out = []
        cash = float(view.cash)
        working = sum(float(l["qty"]) * float(l.get("px") or 0) for l in lots.values() if l["state"] == "working")
        cash -= working
        slot = float(self.CONFIG.capital) / self.slots
        for lot in sorted((l for l in lots.values() if l["state"] == "pending"), key=lambda x: (x["entry_at"], x["key"])):
            if now < float(lot["entry_at"]):
                continue
            if now >= float(lot["entry_until"]):
                lot.update(state="skipped", closed_at=now, reason="entry bar passed")
                continue
            if not cal.is_rth(now):
                continue
            px = _px(view.quotes.get(lot["symbol"]))
            if not px:
                continue
            notional = slot * float(lot["frac"])
            if notional > cash:
                lot.update(state="skipped", closed_at=now, reason="no cash for the slot")
                continue
            qty = notional / px
            cash -= notional
            lot.update(state="working", qty=qty, px=px, entered=now)
            out.append(Intent("enter", lot["symbol"], qty=qty, price_hint=px, signal_key=lot["key"],
                              order=OrderSpec(type="market", window_s=max(60.0, float(lot["entry_until"]) - now)),
                              reason=f"{self.sid} {lot['tag']} {lot['interval']} event {lot['t']}: next-bar open",
                              meta=self._cost({"tag": lot["tag"], "event": lot["event"]})))
        return out

    def exit_due(self, lot, view, docs, now):
        """(reason, OrderSpec) when the lot exits now, else None."""
        if lot.get("exit_at"):
            at = float(lot["exit_at"])
            if lot.get("moc"):
                mtc = cal.minutes_to_close(now)
                if (cal._as_date(now) == cal._as_date(at - 1) and mtc is not None and mtc <= 25) or now >= at:
                    return f"bar {lot['h']} close", OrderSpec(type="market", tif="cls", window_s=3600)
            elif now >= at:
                return f"bar {lot['h']} close", OrderSpec(type="market", window_s=1800)
        q = view.quotes.get(lot["symbol"]) or {}
        mark = q.get("bid") or q.get("last")
        if mark and lot.get("stop") and float(mark) <= float(lot["stop"]):
            return "stop", OrderSpec(type="market", window_s=1800)
        if mark and lot.get("target") and float(mark) >= float(lot["target"]):
            return "target", OrderSpec(type="market", window_s=1800)
        if self.sells(docs, lot, now):
            return "Tensor sell", OrderSpec(type="market", window_s=1800)
        return None

    def exits(self, view, docs, lots, held, pending_keys, now):
        out = []
        if not cal.is_rth(now):
            return out
        left = dict(held)
        for lot in sorted((l for l in lots.values() if l["state"] == "open"), key=lambda x: x["created"]):
            due = self.exit_due(lot, view, docs, now)
            if not due:
                continue
            reason, spec = due
            qty = min(float(lot["qty"]), left.get(lot["symbol"], 0.0))
            if qty <= 1e-9:
                lot.update(state="done", closed_at=now, reason="nothing held")
                continue
            rest = left[lot["symbol"]] - qty
            full = rest <= max(1e-6, 1e-6 * qty)         # the last lot closes the whole position (no dust)
            left[lot["symbol"]] = 0.0 if full else rest
            key = lot["key"] + ":x"
            lot.update(state="closing", exit_key=key, exit_reason=reason)
            out.append(Intent("exit", lot["symbol"], qty=None if full else qty, signal_key=key, order=spec,
                              reason=f"{self.sid} {lot['tag']}: {reason}", meta=self._cost()))
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


class PurgedBook(EventBook):
    """a book whose events obey a per-(tag, symbol) spacing rule (the cyan / color confirmation purge)."""

    def admit(self, ev, st, now):
        days = ev.get("purge_days")
        if not days:
            return True
        last = st.setdefault("purge", {})
        stamp = datetime.fromtimestamp(int(ev["t"]), tz=timezone.utc).date().isoformat()
        keep = []
        for tag in ev.get("tags") or []:
            k = f"{tag}|{ev['symbol']}"
            if tf.purge_ok(last.get(k), stamp, int(days)):
                keep.append(tag)
                last[k] = stamp
        ev["tags"] = keep
        return bool(keep)


class RelayBook(EventBook):
    """TENSOR_HTF_RELAY_1_0_0: positions run until a completed daily or weekly sell; T7 = the first daily green of a
    weekly episode (tracked here)."""

    def admit(self, ev, st, now):
        ep = ev.get("episode")
        if ep and "T4_DAILY_GREEN_IN_WEEKLY_BULL_EPISODE" in (ev.get("tags") or []):
            used = st.setdefault("t7", {})
            k = f"{ev['symbol']}|{ep}"
            if k not in used:
                used[k] = int(ev["t"])
                ev["tags"] = list(ev["tags"]) + ["T7_WEEKLY_BUY_THEN_DAILY_GREEN_LATENCY"]
        return True

    def make_lots(self, ev, now):
        lots = super().make_lots(dict(ev, horizons=[None]), now)
        for lot in lots:
            lot["exit_on_sell"] = "1d+1wk"
        return lots

    def sells(self, docs, lot, now):
        """exit at the next session open after the first completed daily or weekly sell after the entry bar."""
        for iv in ("1d", "1wk"):
            t = ((docs.get(iv) or {}).get("context") or {}).get("sells", {}).get(lot["symbol"])
            if t and int(t) > int(lot["t"]) and now >= cal.session_open(cal.next_trading_day(
                    cal._as_date(plane.bar_end(iv, int(t)) - 1))):
                return True
        return False


class EdgeBook(EventBook):
    """griffith-tensor-edge/0.1.0: a buy-stop at the signal bar's high during the next bar (the NEXT_SESSION /
    NEXT_WEEK_SIGNAL_HIGH_BREAK variants), the structural stop at the signal bar's low, exit on the frame's
    completed sell-red / sell-magenta (next open)."""

    def admit(self, ev, st, now):
        ev["tags"] = [t for t in ev.get("tags") or [] if not t.endswith(":REJECT")]
        return bool(ev["tags"]) and bool(ev.get("trade", True))

    def make_lots(self, ev, now):
        lots = super().make_lots(dict(ev, horizons=[None]), now)
        for lot in lots:
            lot.update(trigger=ev.get("trigger"), exit_on_sell=ev["interval"],
                       entry_until=plane.bar_end(ev["interval"], plane.entry_open(ev["interval"], int(ev["t"]))))
        return lots

    def entries(self, view, lots, pending_keys, now):
        """the break: a buy-stop at the signal bar's high, resting through the entry bar (the engine routes it once the
        ask trades through the trigger; an unbroken stop expires with the bar)."""
        out = []
        cash = float(view.cash) - sum(float(l["qty"]) * float(l.get("px") or 0) for l in lots.values()
                                      if l["state"] == "working")
        slot = float(self.CONFIG.capital) / self.slots
        for lot in sorted((l for l in lots.values() if l["state"] == "pending"), key=lambda x: (x["entry_at"], x["key"])):
            if now < float(lot["entry_at"]):
                continue
            if now >= float(lot["entry_until"]):
                lot.update(state="skipped", closed_at=now, reason="entry bar passed")
                continue
            if not cal.is_rth(now) or not lot.get("trigger"):
                continue
            trig = float(lot["trigger"])
            notional = slot * float(lot["frac"])
            if notional > cash:
                lot.update(state="skipped", closed_at=now, reason="no cash for the slot")
                continue
            cash -= notional
            qty = notional / trig
            lot.update(state="working", qty=qty, px=trig, entered=now)
            out.append(Intent("enter", lot["symbol"], qty=qty, price_hint=trig, signal_key=lot["key"],
                              order=OrderSpec(type="market", stop_price=trig, not_after=float(lot["entry_until"]),
                                              window_s=max(60.0, float(lot["entry_until"]) - now)),
                              reason=f"{self.sid} {lot['tag']} {lot['interval']} event {lot['t']}: signal-high break "
                                     f"{trig:.2f}",
                              meta=self._cost({"tag": lot["tag"], "event": lot["event"], "stop": lot.get("stop")})))
        return out

    def sells(self, docs, lot, now):
        t = ((docs.get(lot["interval"]) or {}).get("context") or {}).get("sells", {}).get(lot["symbol"])
        return bool(t and int(t) > int(lot["t"]) and now >= cal.session_open(cal.next_trading_day(
            cal._as_date(plane.bar_end(lot["interval"], int(t)) - 1))))


class HourlySellBook(EventBook):
    """the hourly Core/Burst exits: a later 1H sell-red / sell-magenta exits at the next bar."""

    def sells(self, docs, lot, now):
        t = ((docs.get("1h") or {}).get("context") or {}).get("sells", {}).get(lot["symbol"])
        return bool(t and int(t) > int(lot["t"]) and now >= plane.hour_end(int(t)))


def research_sleeves():
    out = []
    for sid, gid in GENOMES.items():
        out.append(EventBook(sid, intervals=("1h", "1d", "1wk"), source=V619, title=f"{gid} genome"))
    for sid, (iv, pid) in PHENOTYPES.items():
        out.append(EventBook(sid, intervals=(iv,), source=V619, title=pid))
    v615 = dict(ARCHIVE, path="outputs/foliotend-tensor-swing-full-universe-2026-09-24/production-source-v615/lib/"
                              "tensor-swing-signals.mjs", blob="c25d029df4830c44dad5fbe446fd9cd147aff7bb", lines="81-134")
    out.append(EventBook("ro_tensor_1h_swing_v615", intervals=("1h",), source=v615))
    out.append(EventBook("ro_winner_census_10_20_30", intervals=("1h",), source=dict(
        ARCHIVE, ref="research/tensor-1h-phenotype-genome-2026-09-28", commit="f9a611637fb66cb3158c704a38ba504e61e1f2f8",
        path="outputs/tensor-swing-context-incremental-study-2026-09-29/winner-focus-recovery-plan-2026-09-29.md",
        blob="3f139f067e40ebaa91a4f54fbe771613a061654c", lines="67-193")))
    out.append(EventBook("ro_swing_transition_1h_v1", intervals=("1h",), slots=len(ST_PRIMARY), source=dict(
        ARCHIVE, path="outputs/tensor-stock-selection-v2-2026-09-30/deployed-st-classifier.mjs",
        blob="18cf2bf802aaecfcca8f008881a10595f298d889")))
    out.append(HourlySellBook("ro_hourly_transition_core_burst", intervals=("1h",), source=dict(
        ARCHIVE, path="outputs/foliotend-enhanced-genome-phenotype-response-study-2026-09-25/prior-research-source/"
                      "hourly-signal-study/hourly_transition_genome_proposal.md",
        blob="4c57404000cf2f18ba84197e9f671a8c64a2e957")))
    out.append(EventBook("griffith_htf_conditional_h1_h8", intervals=("1d", "1wk"), cost_bps=50.0, source=dict(
        AGENTIC, path="tensor_htf_holdout_spec.json", blob="d6a11f5d2dcc00c942e99f33e806e36fc549b018")))
    out.append(PurgedBook("griffith_weekly_cyan_confirmation", intervals=("1wk",), cost_bps=50.0, source=dict(
        AGENTIC, path="tensor_htf_weekly_cyan_spec.json", blob="69982d9b8f573b07bfa74efc602dc83072037341")))
    out.append(PurgedBook("griffith_weekly_green_cyan_deep_confirmation", intervals=("1wk",), cost_bps=50.0,
                          source=dict(AGENTIC, path="tensor_htf_weekly_color_spec.json",
                                      blob="d1d4e8a24e3e1cd3d114e24fcefff46792844484")))
    out.append(EventBook("griffith_weekly_color_forward_shadow", intervals=("1wk",), cost_bps=50.0, source=dict(
        AGENTIC, path="tensor_htf_weekly_color_forward_spec.json", blob="845e3259339e9377f0a3b2b2c36410940ade03b5")))
    out.append(RelayBook("griffith_htf_relay", intervals=("1d", "1wk"), cost_bps=None, source=dict(
        AGENTIC, path="tensor_htf_strategy_spec.json", blob="728e1d4e46655933717b23510c562d034b450002")))
    out.append(EdgeBook("griffith_tensor_edge_v01", intervals=("1d", "1wk"), cost_bps=None, source=dict(
        AGENTIC, path="tensor_edge_strategy_spec.json", blob="d8218e26942a2cb44efa839321606ed338f809f8")))
    out.append(EventBook("griffith_frozen_phenotypes_v4", intervals=("1d", "1wk"), cost_bps=15.0, source=dict(
        AGENTIC, path="tensor_phenotype_registry.json", blob="753011229bb946ddc154aba45a35ecf69ca4f4d8")))
    return out


# == the three-strategy desk path for research decisions (the experiment; Leaders Rest v1.1) =========================
from . import griffith as G  # noqa: E402  (after the event-book section: griffith is a sibling family module)

VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor")
EXPERIMENT_MAX_PER_CYCLE = 25          # tensor_experimental_paper.max_predictions_per_cycle


def _decision(fields):
    V = G.vendored()
    f = dict(fields)
    f["reasonCodes"] = tuple(f.get("reasonCodes") or ())
    f["metrics"] = dict(f.get("metrics") or {})
    return V.strategy_system.StrategyDecision(**f)


class HandoffBook(G.ThreeStrategySleeve):
    """research decisions through the Griffith desk's ExecutionOverlays plan, PortfolioAllocator sizing, armed
    handoff and bracketed GTC entry (the griffith family's port of run_three_strategies / drain_strategy_handoffs,
    with its removed desk-wide gates and named divergences)."""

    def __init__(self, sleeve_id, strategy, source):
        self.strategy = strategy
        cfg = G.source_config()
        self.three = cfg["three_strategy"]
        self.aggr = self.three.get("paper_aggressive_execution") or {}
        profile = dict(cfg["risk"]["paper_aggressive_profile"])
        profile.update(total_risk_fraction=G.NEUTRAL, symbol_risk_fraction=G.NEUTRAL, sector_risk_fraction=G.NEUTRAL,
                       gross_notional_fraction=G.NEUTRAL)
        self.profile = profile
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family=FAMILY, cadence_s=int(cfg["agentic"]["cycle_seconds"]),
            needs={"feeds": [FEED], "quotes": {"source": "equity"}}, schedule="premarket,rth",
            params={"strategy": strategy, "champion": self.three["version_policy"]["champion_versions"][strategy],
                    "strategy_cap": profile["strategy_caps"][strategy]},
            source=dict(source), state_schema={"seen": "dict", "handoffs": "dict", "submitted": "dict"})

    def wants_tape(self, now):
        return False

    def decisions_from(self, docs, st, now):
        raise NotImplementedError

    def signal(self, view):
        st = dict(view.state or {})
        handoffs = {k: dict(v) for k, v in (st.get("handoffs") or {}).items()}
        now = float(view.now)
        held = {i.split(":", 1)[1] for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"]) > 0}
        live = {po.get("signal_key") for po in view.extra.get("pending_orders") or []}
        submitted = {k: r for k, r in (st.get("submitted") or {}).items() if k in live or now - r["at"] < 3600}
        decisions = self.decisions_from(view.extra.get(FEED) or {}, st, now)
        if decisions:
            risk = self.open_risk(view, handoffs, submitted, now)
            triples = self.plan_run(decisions, float(view.equity), self.buying_power(view, submitted), risk, held, now,
                                    quotes=view.quotes)
            self.arm(triples, handoffs, now)
            st["last_run"] = {"at": now, "decisions": len(decisions), "armed": len(triples)}
        intents = self.deliver(view, handoffs, submitted, held, now) if cal.is_rth(now) else []
        st["handoffs"] = {k: h for k, h in handoffs.items()
                          if h["state"] == "ARMED" or now - float(h.get("at") or now) < G.KEEP_DONE_S}
        st["submitted"] = submitted
        seen = st.get("seen") or {}
        st["seen"] = {k: v for k, v in seen.items() if now - float(v) < 120 * 86400}
        self._st = st
        return intents


class ExperimentBook(HandoffBook):
    """TENSOR_EXPERIMENTAL_1_1_0 (tensor_experimental_strategy.py): each frozen-registry prediction ->
    decision_from_prediction on its admitted completed bars (HIGH_BREAK_4: trigger = event high, ceiling = trigger +
    0.10 ATR14, stop = close - 2 ATR14, target = ceiling x 1.10 daily / 1.25 weekly, horizon 26 / 130 sessions,
    entry window 7 / 28 days) under the source config's authorized unqualified paper experiment, then the TENSORX
    overlay and the desk path. At most 25 predictions are taken per cycle, oldest first."""

    def __init__(self):
        super().__init__("griffith_tensor_phenotype_experiment", tf.EXPERIMENT_STRATEGY_ID, dict(
            AGENTIC, path="tensor_experimental_strategy.py", blob="a98c7cc3b6a458441a83216947109187e9c5b23f",
            lines="1-162"))

    def decisions_from(self, docs, st, now):
        seen = st.setdefault("seen", {})
        queue = []
        for iv in ("1d", "1wk"):
            for ev in ((docs.get(iv) or {}).get("events") or {}).get("griffith_frozen_phenotypes_v4", []):
                p = ev.get("prediction")
                if p and p["prediction_id"] not in seen:
                    queue.append((float((docs.get(iv) or {}).get("asof") or 0), p["prediction_id"], p))
        out = []
        clock = datetime.fromtimestamp(now, tz=timezone.utc)
        for _, pid, p in sorted(queue, key=lambda x: (x[0], x[1]))[:EXPERIMENT_MAX_PER_CYCLE]:
            seen[pid] = now
            try:
                completed, _ = tf.admit_completed(p["bars"], p["timeframe"], clock)
            except tf.TensorAdmissionError:
                continue
            fields = tf.decision_from_prediction(p, completed, "AUTHORIZED_PAPER_EXPERIMENT")
            if fields is None:
                continue
            # the source's authorized-unqualified replace(): paperExperimentAuthorized + the reason prefix
            fields["metrics"] = dict(fields["metrics"], paperExperimentAuthorized=True)
            fields["reasonCodes"] = ("AUTHORIZED_UNQUALIFIED_PAPER", *fields["reasonCodes"])
            out.append(_decision(fields))
        return out


class LeadersRestV11Book(HandoffBook):
    """the Deep Reset / Leaders Rest wrapper (work/run-deep-reset-leaders-rest.py): every session's fresh daily
    buy-green names (the scan's dailyGreen group) through LeadersRest.evaluate(corrected=True, is_etf, active_event=
    False) = LR_1_1_0_CORRECTED on the names' Yahoo daily history; a SETUP trades through the LRX overlay and the desk
    path; the Doorway Deep Reset lens rides along as evidence."""

    def __init__(self):
        super().__init__("ro_leaders_rest_v11", "LEADERS_REST", dict(
            ARCHIVE, path="work/run-deep-reset-leaders-rest.py", blob="4644f106d44ceed9455cdf8977a36b08e32e460f",
            lines="1-155"))

    def decisions_from(self, docs, st, now):
        seen = st.setdefault("seen", {})
        out = []
        for ev in ((docs.get("1d") or {}).get("events") or {}).get("ro_leaders_rest_v11", []):
            if ev["key"] in seen:
                continue
            seen[ev["key"]] = now
            out.append(_decision(ev["decision"]))
        return out


_DOORWAY = None


def doorway():
    """the vendored Doorway helper (prepare-current-doorway-inputs.py, FolioTend production v622 scripts)."""
    global _DOORWAY
    if _DOORWAY is None:
        import importlib
        _DOORWAY = importlib.import_module("desk.vendor.foliotend_research.doorway.prepare_current_doorway_inputs")
    return _DOORWAY


def raw_rows(bars):
    return [{"t": datetime.fromtimestamp(b["time"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": b["open"],
             "h": b["high"], "l": b["low"], "c": b["close"], "v": b["volume"]} for b in bars]


def ema21_extended(bars):
    """the market scan's winnerGenome ema21_extended: the ready bar (the one before the cutoff) close over its EMA21
    (seeded at the window's first close) - 1 >= .08."""
    closes = [float(b["close"]) for b in bars[:-1]]
    return len(closes) >= 2 and closes[-1] / ema_last(closes, 21) - 1 >= 0.08


def detect_lr11(frame, col):
    if "buy-green" not in frame.fresh() or not frame.input or not col.spy:
        return []
    V = G.vendored()
    fund = (col.assets.get(frame.symbol) or {}).get("classification") == "FUND_OR_ETP_EXCLUDED_FROM_STOCK_CROSS_SECTION"
    raw = raw_rows(frame.input)
    d = V.strategy_system.LeadersRest().evaluate(frame.symbol, raw, raw_rows(col.spy["input"]), corrected=True,
                                                 is_etf=fund, active_event=False)
    from dataclasses import asdict
    dr = doorway().completed_bar_reset_screen(raw, V.strategy_system)
    return [event("ro_leaders_rest_v11", frame, [d.status], (), decision=asdict(d), deep_reset=dr)]


DEEP_RESET_SESSIONS = 15               # strategy_system LocationFirst / LeadersRest horizon (the Deep Reset lane)


def detect_deep_reset(frame, col):
    """the cross-scan wrapper (work/run-cross-scan-deep-reset-2026-09-21.py): the scan's dailyGreen / weeklyGreen /
    weeklyCyan groups, eligible while the daily Tensor EMA21 extension flag is false, Deep Reset recomputed on the
    group's native timeframe (2 years of bars); a name whose lens reads drReset (score >= 60) is traded."""
    fresh = frame.fresh()
    if frame.interval == "1d":
        group = "dailyGreen" if "buy-green" in fresh else None
        extended = ema21_extended(frame.input[-plane.AG_WINDOW["1d"]:]) if frame.input else None
        col.context.setdefault("ext", {})[frame.symbol] = extended
    else:
        group = "weeklyGreen" if "buy-green" in fresh else "weeklyCyan" if "buy-cyan" in fresh else None
        extended = (col.ctx_in.get("ext") or {}).get(frame.symbol)
    if not group or extended is None or extended or not frame.input:
        return []
    last = frame.input[-1]["time"]
    bars = [b for b in frame.input if b["time"] >= last - 2 * 366 * 86400]
    dr = doorway().completed_bar_reset_screen(raw_rows(bars), G.vendored().strategy_system)
    if not dr.get("drReset"):
        return []
    return [event("ro_deep_reset_cross_scan", frame, [group], (DEEP_RESET_SESSIONS,), deep_reset=dr,
                  rvol=(frame.last or {}).get("rvol"))]


class DeepResetBook(EventBook):
    """a Deep Reset lot enters at the next session open and closes at the close of its 15th session (weekly groups
    count sessions from the week's last session)."""

    def make_lots(self, ev, now):
        ev = dict(ev)
        if ev["interval"] == "1wk":
            last = cal.week_last_session(plane.week_monday(int(ev["t"])))
            ev["interval"] = "1d"
            ev["t"] = int(cal.session_open(last))
        lots = super().make_lots(ev, now)
        return lots


EXTRA_DETECTORS["1d"] += [("ro_leaders_rest_v11", detect_lr11), ("ro_deep_reset_cross_scan", detect_deep_reset)]
EXTRA_DETECTORS["1wk"] += [("ro_deep_reset_cross_scan", detect_deep_reset)]


def handoff_and_reset_sleeves():
    return [ExperimentBook(), LeadersRestV11Book(),
            DeepResetBook("ro_deep_reset_cross_scan", intervals=("1d", "1wk"), cost_bps=None, source=dict(
                ARCHIVE, path="work/run-cross-scan-deep-reset-2026-09-21.py",
                blob="414252cc9c4dd2e182a1f3a3ec145693dcae375b", lines="1-198"))]


# == qr_tensor_rejection_memory: the frozen MID21 daily rejection-memory desk =========================================
import importlib  # noqa: E402
from decimal import Decimal  # noqa: E402

RM_SOURCE = {"repo": "quant-research-critical", "ref": "strategies/tensor-rejection-memory-v1-20261009",
             "commit": "be562a86e60ec33d6a565b461d43f8e6a6271ea6"}
RM_SEED = "2015-01-01"                 # data.py SEED_SESSION: SIP all-adjusted history from 2015
RM_MIN_INDEX = 200                     # native.py MINIMUM_DECISION_INDEX
RM_HOLD = 20                           # strategy.exit_session: entry session + 20 sessions
RM_TICKET = 0.125                      # ticket_fraction
RM_MAX = 8                             # max_positions
RM_COLUMNS = ("timestamp", "close", "high", "ema48", "ema200", "emaRibbon_4", "emaRibbon_5", "emaRibbon_6",
              "emaRibbon_7", "native_atr", "marker_buy_green", "marker_buy_cyan", "swing_confirmed", "barFinality")


def rm_modules():
    s = importlib.import_module("desk.vendor.foliotend_research.rejection_memory.strategy")
    a = importlib.import_module("desk.vendor.foliotend_research.rejection_memory.acceptance_features")
    return s, a


def rm_path(root):
    return os.path.join(plane.cache_dir(root), "rejection_memory.json")


def rm_completed_session(now):
    """the last session whose SIP daily bar is final (20:15 New York, data.py / the scan's finality rule)."""
    d = cal._as_date(now)
    t = datetime.fromtimestamp(now, tz=plane.ET)
    if cal.is_trading_day(d) and (t.hour, t.minute) >= (20, 15):
        return d
    return cal.prev_trading_day(d)


def rm_signals(native_rows_by_symbol):
    """native.calculate_signals over the runner's projected rows: the frozen acceptance module on every row, the
    latest row per symbol with decision_index / warmup / entry_eligible / native_trigger."""
    import pandas as pd
    _, A = rm_modules()
    rows = []
    for sym, native in native_rows_by_symbol.items():
        for r in native:
            d = dict(zip(RM_COLUMNS, r))
            d["symbol"] = sym
            rows.append(d)
    if not rows:
        return {}
    panel = pd.DataFrame(rows)
    acc = A.calculate(panel)
    out = {}
    counts = defaultdict(int)
    for i, d in enumerate(rows):
        idx = counts[d["symbol"]]
        counts[d["symbol"]] += 1
        rec = {k: (None if (isinstance(v, float) and not math.isfinite(v)) else (v.item() if hasattr(v, "item") else v))
               for k, v in acc.iloc[i].items()}
        rec.update({k: d[k] for k in ("timestamp", "close", "marker_buy_green", "marker_buy_cyan", "swing_confirmed",
                                      "barFinality")})
        rec["decision_index"] = idx
        rec["warmup_complete"] = idx >= RM_MIN_INDEX
        rec["native_trigger"] = bool(d["marker_buy_green"] or d["marker_buy_cyan"] or d["swing_confirmed"])
        rec["entry_eligible"] = bool(rec["warmup_complete"] and rec.get("acceptance_release"))
        for name in ("anchor_kind", "anchor_level", "anchor_atr", "episode_age", "failed_attempt_count"):
            rec[name] = rec.get("acceptance_" + name)
        out[d["symbol"]] = rec
    return out


def job_rejection_memory(engine, now=None, bars=None, raw=None):
    """nightly after the SIP finality (20:15 ET): the basket's full SIP all-adjusted daily history (Alpaca; the
    desk's equity source) -> the native rows (engine v698) -> the frozen acceptance module -> the latest signal row
    per basket name, with the completed session's unadjusted close as its decision close (cli._scan's raw daily
    reference: the executable limit is 1.03 x that close). A name whose history is stale or short, or whose raw
    reference bar is missing, is a failure (and the scan is incomplete), never substituted."""
    S, _ = rm_modules()
    now = now or engine.clock()
    completed = rm_completed_session(now)
    from ...util import read_json, write_json_atomic
    done = read_json(rm_path(engine.root), None) or {}
    if done.get("completed_session") == completed.isoformat() and not done.get("failures"):
        return {"skipped": "already published", "completed_session": completed.isoformat()}
    if bars is None:
        bars = engine.hub.bars("equity", "1d", list(S.BASKET), 3000)
    seed = datetime.fromisoformat(RM_SEED + "T00:00:00+00:00").timestamp()
    jobs, failures = [], {}
    for sym in S.BASKET:
        bl = [b for b in bars.get(sym) or [] if float(b["t"]) >= seed and plane.session_of(b["t"]) <= completed]
        if not bl or plane.session_of(bl[-1]["t"]) != completed:
            failures[sym] = "stale or missing history for %s" % completed
            continue
        if len(bl) <= RM_MIN_INDEX:
            failures[sym] = "at least %d completed bars required" % (RM_MIN_INDEX + 1)
            continue
        jobs.append({"symbol": sym, "interval": "1d", "bars": [{"t": int(b["t"]), "o": b["o"], "h": b["h"],
                                                                 "l": b["l"], "c": b["c"], "v": b.get("v") or 0}
                                                                for b in bl],
                     "views": [{"name": "rm", "nativeFull": True}]})
    native = {}

    def take(job, res):
        v = ((res.get("views") or {}).get("rm") or {}) if res.get("ok") else {}
        if v.get("native"):
            native[job["symbol"]] = v["native"]
        else:
            failures[job["symbol"]] = res.get("error") or v.get("error") or "native extraction failed"
    plane.frames(jobs, take, chunk=7)
    signals = rm_signals(native)
    if raw is None:                        # the split-adjusted tape's completed bar = that session's raw close
        raw = engine.hub.bars("equity_split", "1d", list(S.BASKET), 5)
    for sym, sig in signals.items():
        ref = [b for b in raw.get(sym) or [] if plane.session_of(b["t"]) == completed]
        if ref:
            sig["decision_close"] = float(ref[-1]["c"])
        else:
            failures[sym] = "raw daily reference bar missing for %s" % completed
    doc = {"asof": now, "completed_session": completed.isoformat(), "signals": signals, "failures": failures}
    write_json_atomic(rm_path(engine.root), doc)
    info = {"completed_session": completed.isoformat(), "signals": len(signals), "failures": len(failures),
            "eligible": sorted(s for s, r in signals.items() if rm_eligible(r))}
    if failures:                           # make_plan's incomplete_frozen_basket_scan: retried until complete
        raise plane.IncompleteRun(f"rejection memory: {len(failures)} of {len(S.BASKET)} basket names failed "
                                  f"({', '.join(sorted(failures)[:5])})")
    return info


def rm_eligible(s):
    """make_plan's entry law: Tensor authority (green / cyan / confirmed swing) with the stored rejection-memory
    release, the 200-bar admission, >= 2 failed attempts and an episode 5-60 bars old."""
    authority = bool(s.get("marker_buy_green") or s.get("marker_buy_cyan") or s.get("swing_confirmed"))
    release = bool(s.get("acceptance_release"))
    if not (authority and release and s.get("warmup_complete") and s.get("entry_eligible")):
        return False
    try:
        return int(s.get("failed_attempt_count") or 0) >= 2 and 5 <= int(s.get("episode_age") or 0) <= 60
    except (TypeError, ValueError):
        return False


class RejectionMemoryBook(Sleeve):
    """make_plan (strategy.py) on this book: before each session's open, the holdings due (entry session + 20) sell
    at the open and each eligible basket name (symbol order, while slots remain of 8) buys whole shares at the open
    with a limit of 1.03 x the decision close (rounded down to the tick), ticket min(12.5% of equity, cash) /
    (limit x 1.001). No stop."""

    def __init__(self):
        S, _ = rm_modules()
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id="qr_tensor_rejection_memory", family=FAMILY, cadence_s=120, universe=tuple(S.BASKET),
            needs={"feeds": [FEED], "quotes": {"source": "equity"}}, schedule="et:07:00-16:00",
            params={"max_positions": RM_MAX, "ticket_fraction": RM_TICKET, "hold_sessions": RM_HOLD},
            source=dict(RM_SOURCE, path="strategies/tensor_rejection_memory_v1/tensor_strategy/strategy.py",
                        blob="36a02c51490f9ba99b8584bc3612a022b22acb8f", lines="1-292"),
            state_schema={"holdings": "dict", "working": "dict", "planned": "str|None"})

    def bind(self, engine):
        self.engine = engine

    def signal(self, view):
        S, _ = rm_modules()
        st = dict(view.state or {})
        now, today = float(view.now), cal._as_date(view.now)
        holdings = {k: dict(v) for k, v in (st.get("holdings") or {}).items()}
        working = {k: dict(v) for k, v in (st.get("working") or {}).items()}
        pend = {po.get("signal_key") for po in view.extra.get("pending_orders") or []}
        held = {i.split(":", 1)[1]: float(p["qty"]) for i, p in view.positions.items() if i.startswith("EQ:")}
        # fills: a working entry whose order is gone becomes a holding when the position carries it
        for key, w in list(working.items()):
            if key in pend:
                continue
            sym = w["symbol"]
            if held.get(sym, 0) > 0 and sym not in holdings:
                entry_day = cal._as_date(w["routed"])
                holdings[sym] = {"entry_session": entry_day.isoformat(),
                                 "exit_session": cal.next_trading_day(entry_day, RM_HOLD).isoformat(),
                                 "signal_session": w["signal_session"], "qty": held[sym], "client": key}
            working.pop(key)
        for sym in list(holdings):
            if held.get(sym, 0) <= 0 and not any(k.startswith(holdings[sym]["client"] + ":x") for k in pend):
                holdings.pop(sym)
        intents = []
        if cal.is_trading_day(today) and st.get("planned") != today.isoformat():
            open_ = cal.session_open(today)
            for sym, h in sorted(holdings.items()):
                if h["exit_session"] <= today.isoformat() and held.get(sym, 0) > 0:
                    late = h["exit_session"] < today.isoformat()
                    intents.append(Intent("exit", sym, qty=float(int(held[sym])), signal_key=f"{h['client']}:x{today}",
                                          order=OrderSpec(type="market", not_before=open_, not_after=open_ + 3600,
                                                          window_s=max(60.0, open_ + 3600 - now)),
                                          reason=f"MID21 {'late_' if late else ''}time_exit_20 (entry {h['entry_session']})"))
            doc = (view.extra.get(FEED) or {}).get("rm") or {}
            expected = cal.prev_trading_day(today).isoformat()
            # make_plan's own entry laws: the complete frozen basket scan of the completed session, and no new
            # entries while a time exit is overdue (late_time_exit_new_entries_paused)
            complete = not doc.get("failures") and set(doc.get("signals") or {}) == set(S.BASKET)
            overdue = any(h["exit_session"] < today.isoformat() for h in holdings.values())
            if now < open_ and doc.get("completed_session") == expected and complete and not overdue:
                slots = RM_MAX - len(holdings) - len(working)
                cash = float(view.cash) - sum(float(w["qty"]) * float(w["limit"]) * 1.001 for w in working.values())
                equity = float(view.equity)
                pending = {w["symbol"] for w in working.values()}
                for sym in sorted(doc.get("signals") or {}):
                    s = doc["signals"][sym]
                    if not rm_eligible(s) or sym in holdings or sym in held or sym in pending or slots <= 0:
                        continue                # already_held_or_pending; capacity_rejection_consumes_this_episode
                    dlimit = S.price_limit(s.get("decision_close", s["close"]))
                    limit = float(dlimit)
                    budget = min(equity * RM_TICKET, max(0.0, cash))
                    qty = int(Decimal(str(budget)) / (dlimit * Decimal("1.001")))
                    if qty < 1:
                        continue
                    key = S.order_id(sym, expected, "buy")
                    cash -= qty * limit * 1.001
                    slots -= 1
                    working[key] = {"symbol": sym, "qty": qty, "limit": limit, "routed": open_, "signal_session": expected}
                    intents.append(Intent("enter", sym, qty=float(qty), price_hint=limit, signal_key=key,
                                          order=OrderSpec(type="limit", limit_price=limit, not_before=open_,
                                                          not_after=open_ + 600, window_s=max(60.0, open_ + 600 - now)),
                                          reason=f"MID21 Tensor_trigger_and_stored_rejection_acceptance "
                                                 f"({s.get('anchor_kind')}, {s.get('failed_attempt_count')} failed, "
                                                 f"age {s.get('episode_age')})",
                                          meta={"anchor_level": s.get("anchor_level"), "anchor_atr": s.get("anchor_atr")}))
            if now >= open_ or doc.get("completed_session") == expected:
                st["planned"] = today.isoformat()
        st["holdings"], st["working"] = holdings, working
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


# == qr_tensor_residual_accumulation: TRACE r10 at the daily scale ====================================================
TRACE_SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
                "path": "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/trace/repair/trace_r10.py",
                "blob": "6306d548248d174261b73e843a6b4bb2ac312f91", "lines": "1-658"}
TRACE_BOX, TRACE_PATH, TRACE_FIT = 20, 20, 60
TRACE_MAX_NAMES, TRACE_NAME_CAP, TRACE_RISK, TRACE_MIN_NOTIONAL = 15, 0.08, 0.0025, 1000.0
TRACE_HOLD, TRACE_COOLDOWN = 20, 20


def trace_module():
    return importlib.import_module("desk.vendor.foliotend_research.trace.trace_r10")


def trace_path(root):
    return os.path.join(plane.cache_dir(root), "trace.json")


def _atr14(bars, i):
    vals = [max(bars[k]["h"] - bars[k]["l"], abs(bars[k]["h"] - bars[k - 1]["c"]), abs(bars[k]["l"] - bars[k - 1]["c"]))
            for k in range(max(1, i - 13), i + 1)]
    return sum(vals) / len(vals) if vals else None


def trace_evaluate(sym, bl, spy, sector, T):
    """the playbook's selection at one daily cutoff: the frozen 20-session box, the 20-session residual path
    (factors fit on the 60 sessions before its origin: stock ~ duration + SPY + sector), pressure over the
    pre-window same-slot volume medians, and phase_transition; plus the renewal-failure state."""
    from datetime import datetime as _dt

    def when(t, h, m):
        d = plane.session_of(t)
        return _dt(d.year, d.month, d.day, h, m, tzinfo=plane.ET)

    n = len(bl)
    if n < TRACE_FIT + TRACE_BOX + TRACE_PATH + 1:
        return None
    by_t = {plane.session_of(b["t"]): b for b in bl}

    def rets(series, idx):
        out = []
        for i in idx:
            a, b = series[i - 1], series[i]
            out.append(b["c"] / a["c"] - 1)
        return out

    def aligned(ref, idx):
        rd = {plane.session_of(b["t"]): b for b in ref}
        out = []
        for i in idx:
            d0, d1 = plane.session_of(bl[i - 1]["t"]), plane.session_of(bl[i]["t"])
            a, b = rd.get(d0), rd.get(d1)
            if not a or not b:
                return None
            out.append(b["c"] / a["c"] - 1)
        return out
    del by_t
    w0 = n - TRACE_PATH
    fit_idx = list(range(w0 - TRACE_FIT, w0))
    win_idx = list(range(w0, n))
    y, m, s = rets(bl, fit_idx), aligned(spy, fit_idx), aligned(sector, fit_idx)
    yw, mw, sw = rets(bl, win_idx), aligned(spy, win_idx), aligned(sector, win_idx)
    if None in (m, s, mw, sw):
        return None
    known = when(bl[w0 - 1]["t"], 16, 15)
    fit = T.fit_factors(y, m, s, [1.0] * len(y), known, maximum_input_end=when(bl[w0 - 1]["t"], 16, 0),
                        maximum_received_at=known)

    def bar(b, origin=None):
        return T.Bar(end=when(b["t"], 16, 0), available_at=when(b["t"], 16, 10), received_at=when(b["t"], 16, 5),
                     open=float(b["o"]), high=float(b["h"]), low=float(b["l"]), close=float(b["c"]),
                     volume=float(b.get("v") or 0), duration=1.0, slot="daily", origin=origin)
    origin = when(bl[w0]["t"], 9, 30)
    window = [bar(bl[i], origin if i == w0 else None) for i in win_idx]
    pre = [bar(bl[i]) for i in range(w0 - 20, w0)]
    medians = T.volume_medians(pre, window)
    path = T.residual_path(window, yw, mw, sw, medians, fit)
    box = bl[w0 - TRACE_BOX:w0]
    low, high = min(b["l"] for b in box), max(b["h"] for b in box)
    closes = [bl[i]["c"] for i in win_idx]
    phase = T.phase_transition(closes, path["q"], path["p"], low, high)
    prior_high = max(closes[:-3]) if len(closes) > 3 else None
    renewal = bool(prior_high and T.renewal_failure(closes[-3:], prior_high, path["contrast"], list(path["u"][-3:])))
    return {"symbol": sym, "t": int(bl[-1]["t"]), "close": float(bl[-1]["c"]), "atr": _atr14(bl, n - 1),
            "state": phase.state, "gate": bool(phase.entry_gate), "renewal_failure": renewal,
            "contrast": float(path["contrast"]), "area": float(path["area"]), "box": [low, high]}


def job_trace(engine, now=None, bars=None, assets=None):
    """after the genome job (its cache is this lane's daily tape): every eligible roster name at the cutoff."""
    T = trace_module()
    from ...util import read_json, write_json_atomic
    now = now or engine.clock()
    day = cal._as_date(now)
    if not cal.is_trading_day(day) or now < cal.session_close(day) + 10 * 60:
        day = cal.prev_trading_day(day)
    done = read_json(trace_path(engine.root), None) or {}
    if done.get("session") == day.isoformat():
        return {"skipped": "already published", "session": day.isoformat()}
    assets = assets if assets is not None else plane.load_assets(engine.root)
    V = G.vendored()
    names = [s for s in plane.roster()
             if (assets.get(s) or {}).get("classification") == "OPERATING_COMPANY_CANDIDATE_CURRENT_METADATA"]
    proxies = sorted(set(V.strategy_orchestrator.PROXIES))
    if bars is None:
        bars = {}
        for i in range(0, len(names), 200):
            bars.update(engine.hub.bars("equity_split", "1d", names[i:i + 200], 600, cache_only=True))
        bars.update(engine.hub.bars("equity_split", "1d", proxies, 600))      # SPY + the sector ETFs
    spy = bars.get("SPY") or []
    have = [s for s in names if bars.get(s)]
    reached = sum(1 for s in have if plane.session_of(bars[s][-1]["t"]) >= day)
    if not spy or plane.session_of(spy[-1]["t"]) < day or (have and reached < plane.MIN_COVERAGE * len(have)):
        raise plane.IncompleteRun(f"TRACE: the genome tape has {reached} of {len(have)} names (SPY "
                                  f"{plane.session_of(spy[-1]['t']) if spy else None}) at {day}")
    out, renewal, errors = [], {}, {}
    for sym in names:
        bl = [b for b in bars.get(sym) or [] if plane.session_of(b["t"]) <= day]
        if len(bl) < 252 or plane.session_of(bl[-1]["t"]) != day:
            continue
        weeks = {plane.week_monday(b["t"]) for b in bl} - {plane.week_monday(bl[-1]["t"])}
        if len(weeks) < 72:                            # 252 daily and 72 completed weekly observations
            continue
        dv = sorted(b["c"] * (b.get("v") or 0) for b in bl[-61:-1])
        if bl[-1]["c"] < 10 or (dv[len(dv) // 2] if dv else 0) < 50e6:
            continue
        sector_etf = V.strategy_orchestrator.SECTOR_FOR.get(sym)
        sector = bars.get(sector_etf) if sector_etf else spy
        if not sector:
            errors[sym] = f"no {sector_etf} history"
            continue
        try:
            r = trace_evaluate(sym, bl, spy, sector, T)
        except Exception as e:                         # the source's ContractError = abstention for that name
            errors[sym] = f"{type(e).__name__}: {str(e)[:100]}"
            continue
        if r is None:
            continue
        renewal[sym] = r["renewal_failure"]
        if r["gate"]:
            r["adv_shares"] = sum(float(b.get("v") or 0) for b in bl[-20:]) / 20.0
            r["sector"] = sector_etf or f"name:{sym}"
            out.append(r)
    doc = {"asof": now, "session": day.isoformat(), "candidates": out, "renewal": renewal, "errors": errors}
    write_json_atomic(trace_path(engine.root), doc)
    return {"session": day.isoformat(), "candidates": len(out), "evaluated": len(renewal), "errors": len(errors)}


class TraceBook(Sleeve):
    """TRACE's playbook execution on its daily-scale candidates: the next session 09:35-09:45 a whole-share buy
    limit at cutoff close + 0.5 ATR, shares = min(.25% NAV / 1.5 ATR, 8% NAV / price) (>= $1,000 planned), at most
    15 names, no pyramiding, a 20-session cooldown; exits on the first fill's barriers (P0 - 1.5 ATR / P0 + 3 ATR),
    renewal failure or 20 sessions (next morning)."""

    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id="qr_tensor_residual_accumulation", family=FAMILY, cadence_s=120, universe=(),
            needs={"feeds": [FEED], "quotes": {"source": "equity"}}, schedule="rth",
            params={"max_names": TRACE_MAX_NAMES, "risk_fraction": TRACE_RISK, "name_cap": TRACE_NAME_CAP},
            source=dict(TRACE_SOURCE), state_schema={"lots": "dict", "cooldown": "dict", "planned": "str|None"})

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book):
        st = (self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}) if self.engine else {}
        return sorted({i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:")}
                      | {k for k, v in (st.get("lots") or {}).items()})

    def signal(self, view):
        st = dict(view.state or {})
        lots = {k: dict(v) for k, v in (st.get("lots") or {}).items()}
        cool = dict(st.get("cooldown") or {})
        now, today = float(view.now), cal._as_date(view.now)
        held = {i.split(":", 1)[1]: (float(p["qty"]), float(p["avg"])) for i, p in view.positions.items()
                if i.startswith("EQ:")}
        pend = {po.get("signal_key") for po in view.extra.get("pending_orders") or []}
        doc = (view.extra.get(FEED) or {}).get("trace") or {}
        intents = []
        for sym, lot in list(lots.items()):
            q = held.get(sym)
            if lot["state"] == "working" and lot["key"] not in pend:
                if q and q[0] > 0:
                    lot.update(state="open", p0=q[1], entry_session=today.isoformat())
                else:
                    lots.pop(sym)
                    continue
            if lot["state"] == "closing" and lot.get("xkey") not in pend:
                if not q or q[0] <= 0:
                    lots.pop(sym)                # ReceiptAccount.plan: 20 completed post-exit sessions before the next
                    cool[sym] = cal.next_trading_day(today, TRACE_COOLDOWN + 1).isoformat()
                    continue
                lot["state"] = "open"
            if lot["state"] != "open" or not q or q[0] <= 0:
                continue
            quote = view.quotes.get(sym) or {}
            mark = quote.get("bid") or quote.get("last")
            atr = float(lot["atr"])
            reason = None
            if mark and float(mark) <= lot["p0"] - 1.5 * atr:
                reason = "stop P0 - 1.5 ATR"
            elif mark and float(mark) >= lot["p0"] + 3 * atr:
                reason = "target P0 + 3 ATR"
            elif cal.trading_days_between(cal._as_date(lot["entry_session"]), today) >= TRACE_HOLD \
                    and self._morning(now):
                reason = "20-session expiry"
            elif (doc.get("renewal") or {}).get(sym) and doc.get("session", "") > lot["entry_session"] \
                    and self._morning(now):
                reason = "renewal failure"
            if reason:
                key = f"{lot['key']}:x"
                lot.update(state="closing", xkey=key)
                intents.append(Intent("exit", sym, qty=None, signal_key=key,
                                      order=OrderSpec(type="market", window_s=1800), reason=f"TRACE {reason}"))
        if doc.get("session") == cal.prev_trading_day(today).isoformat() and st.get("planned") != today.isoformat() \
                and self._morning(now):
            st["planned"] = today.isoformat()
            nav = float(view.equity)
            cash = float(view.cash)

            def mark(s):
                q = view.quotes.get(s) or {}
                return float(q.get("last") or q.get("bid") or (held.get(s) or (0, 0))[1] or 0)
            sector_value, gross = defaultdict(float), 0.0
            for s, lot in lots.items():
                v = (held[s][0] * mark(s)) if s in held else float(lot.get("shares") or 0) * float(lot.get("limit") or 0)
                sector_value[lot.get("sector") or f"name:{s}"] += v
                gross += v
            for c in sorted(doc.get("candidates") or [], key=lambda r: r["symbol"]):
                sym = c["symbol"]
                if len(lots) >= TRACE_MAX_NAMES:
                    break
                if sym in lots or sym in held or cool.get(sym, "") > today.isoformat() or not c.get("atr"):
                    continue
                price, atr, sec = float(c["close"]), float(c["atr"]), c.get("sector") or f"name:{sym}"
                # ReceiptAccount.plan / portfolio_order_shares: risk, 8% name, .5% ADV, 25% sector, gross, cash
                shares = math.floor(min(TRACE_RISK * nav / (1.5 * atr), TRACE_NAME_CAP * nav / price,
                                        0.005 * float(c.get("adv_shares") or 0),
                                        max(0.0, 0.25 * nav - sector_value[sec]) / price,
                                        max(0.0, nav - gross) / price, max(0.0, cash) / price))
                if shares < 1 or shares * price < TRACE_MIN_NOTIONAL:
                    continue
                limit = round(price + 0.5 * atr, 2)
                cash -= shares * limit
                sector_value[sec] += shares * price
                gross += shares * price
                key = f"trace:{sym}:{doc['session']}"
                lots[sym] = {"key": key, "state": "working", "atr": atr, "limit": limit, "cutoff": doc["session"],
                             "shares": shares, "sector": sec}
                deadline = datetime(today.year, today.month, today.day, 9, 45, tzinfo=plane.ET).timestamp()
                intents.append(Intent("enter", sym, qty=float(shares), price_hint=limit, signal_key=key,
                                      order=OrderSpec(type="limit", limit_price=limit,
                                                      window_s=max(60.0, deadline - now)),
                                      reason=f"TRACE PRICE_ACCEPTED after pressure inside the 20-session box "
                                             f"(cutoff {doc['session']})"))
        st["lots"], st["cooldown"] = lots, {k: v for k, v in cool.items() if v > today.isoformat()}
        self._st = st
        return intents

    @staticmethod
    def _morning(now):
        t = datetime.fromtimestamp(now, tz=plane.ET)
        return cal.is_trading_day(cal._as_date(now)) and (9, 35) <= (t.hour, t.minute) < (9, 45)

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


# == sable_edge_paper_hands: the Sable / Autopilot Edge paper hands under each named lineage ==========================
HANDS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "feedlib",
                     "tensor_research_hands.mjs")
SABLE_WATCHLIST = ("SPY", "QQQ", "IWM", "SMH", "AAPL", "MSFT", "NVDA", "AMZN", "JPM", "XOM")   # defaultMandate()
SABLE_ETFS = frozenset({"SPY", "QQQ", "IWM", "SMH"})          # universe.ts kind "etf" among the watchlist
SABLE_LINEAGES = ("livermore", "ptj", "druckenmiller", "minervini", "qullamaggie", "kell", "turtle", "raschke", "cohen",
                  "simons")
SABLE_MAX_POSITIONS, SABLE_MAX_DAILY_LOSS_PCT = 6, 2.0         # defaultMandate maxPositions / maxDailyLossPct
SABLE_FEED = "tensor_research_sable"


def _round2(x):
    """JavaScript Math.round(x * 100) / 100."""
    return math.floor(float(x) * 100 + 0.5) / 100


def immediate_buy_marker(markers):
    """notification-policy.ts immediateBuyMarker: exactly one literal buy-green / buy-gold marker."""
    if len(markers) != 1:
        return None
    return markers[0] if markers[0] in ("buy-green", "buy-gold") else None


def interpret(ticker, analysis):
    """bridge.ts interpret: the desk read of one completed-bar analysis."""
    status = (analysis or {}).get("status") or "unavailable"
    cur = (analysis or {}).get("current")
    markers = [m for m in (cur or {}).get("primaryMarkers") or [] if m]
    buy = immediate_buy_marker(markers) if cur else None
    gd = (cur or {}).get("goldDiamond") or {}
    gold = bool(buy == "buy-gold" or (gd.get("qualifies") is True and gd.get("baseGreen") is True))
    paper_buy = status == "ready" and (cur or {}).get("state") == "VECTOR_BUY" and buy is not None
    paper_sell = status == "ready" and (cur or {}).get("state") == "VECTOR_SELL" and len(markers) == 1 \
        and markers[0] in ("sell-red", "sell-magenta")
    return {"ticker": ticker, "status": status, "state": (cur or {}).get("state"), "markers": markers, "gold": gold,
            "paperBuy": paper_buy, "paperSell": paper_sell,
            "completedBarAt": (cur["time"] * 1000) if cur and cur.get("time") else None,
            "close": (cur or {}).get("close")}


def sable_quote(symbol, bars):
    """quote-core.mjs quoteFromCompletedBars over the completed bars ({t, o, h, l, c, v}): the canonical hours."""
    if not bars:
        return None
    last, prev = bars[-1], bars[-2] if len(bars) > 1 else bars[-1]
    close = float(last["c"])
    if close <= 0:
        return None

    def swing(rows, key, lookback, fn):
        vals = [float(r[key]) for r in rows[-lookback:]]
        return fn(vals) if vals else None
    window = bars[-48:]
    sl = bars[-15:]
    ranges = [max(sl[i]["h"] - sl[i]["l"], abs(sl[i]["h"] - sl[i - 1]["c"]), abs(sl[i]["l"] - sl[i - 1]["c"]))
              for i in range(1, len(sl))]
    atr = sum(ranges) / len(ranges) if ranges else None
    support, resistance = swing(bars, "l", 64, min), swing(bars, "h", 64, max)
    closes = [float(b["c"]) for b in bars]
    rsi = None
    if len(closes) >= 15:
        gain = loss = 0.0
        for i in range(len(closes) - 14, len(closes)):
            d = closes[i] - closes[i - 1]
            if d >= 0:
                gain += d
            else:
                loss -= d
        rsi = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    macd = None
    if len(closes) >= 26:
        def ema(p):
            k, v = 2 / (p + 1), closes[0]
            for c in closes[1:]:
                v = c * k + v * (1 - k)
            return v
        macd = ema(12) - ema(26)
    if atr is None or support is None or resistance is None or last.get("v") is None:
        return None
    return {"ticker": symbol, "kind": "etf" if symbol in SABLE_ETFS else "stock", "price": close,
            "prevClose": float(prev["c"]), "high": swing(window, "h", 36, max), "low": swing(window, "l", 36, min),
            "volume": float(last.get("v") or 0), "avgVolume": sum(float(b.get("v") or 0) for b in window) / len(window),
            "support": support, "resistance": resistance, "rsi": rsi, "macdHist": macd, "atr": atr,
            "extensionAtr": (close - support) / max(atr, 0.01), "completedBarAt": int(last["t"]) * 1000}


def swing_atr(atr, px):
    """ledger-core.mjs swingAtr: the quote ATR floored at 1.5% of price."""
    floor_, a = float(px) * 0.015, float(atr) if atr is not None else float("nan")
    if math.isfinite(a) and a >= floor_:
        return a
    if floor_ > 0:
        return floor_
    return a if math.isfinite(a) and a > 0 else 0.0


def swing_size_shares(equity, cash, price, atr, size_down=False):
    """ledger-core.mjs swingSizeShares: min(0.5% (0.25%) equity / 1.6 ATR, 15% (8%) equity / price, 98% cash / price)."""
    px = float(price)
    stop_dist = swing_atr(atr, px) * 1.6
    eq = float(equity) if float(equity) > 0 else float(cash)
    if not (px > 0 and stop_dist > 0 and eq > 0 and float(cash) > 0):
        return 0
    risk, notional = (0.0025, 0.08) if size_down else (0.005, 0.15)
    return max(0, min(math.floor(eq * risk / stop_dist), math.floor(eq * notional / px), math.floor(float(cash) * 0.98 / px)))


def _js_num(x):
    """JavaScript Number(x) for a stored level: null -> 0."""
    return 0.0 if x is None else float(x)


def _js_str(x):
    """JavaScript String(number) for the reason text (an integral value prints without '.0')."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def swing_bracket_check(pos, q):
    """unattended-core.mjs applyStopsAndTargets for one position: the swing floors (stop <= avg - 1.6 ATR, target >=
    avg + 2.8 ATR), the break-even trail after +1R, then the hit -> (reason) or None (JavaScript comparison
    semantics on a missing level)."""
    avg, atr, price = float(pos["avg"]), q.get("atr"), float(q["price"])
    a = swing_atr(atr, avg)
    if avg > 0 and a > 0:
        floor_stop, floor_target = _round2(avg - a * 1.6), _round2(avg + a * 2.8)
        if not (_js_num(pos.get("stop")) <= floor_stop):
            pos["stop"] = floor_stop
        if not (_js_num(pos.get("target")) >= floor_target):
            pos["target"] = floor_target
        if price >= avg + a * 1.6:                     # swingTrailStop: break-even once 1R is in hand
            be = _round2(avg)
            pos["stop"] = max(_js_num(pos.get("stop")) or be, be)
    if pos.get("stop") is not None and price <= float(pos["stop"]):
        return f"Invalidation at {_js_str(pos['stop'])} was reached."
    if pos.get("target") is not None and price >= float(pos["target"]):
        return f"Target plan at {_js_str(pos['target'])} was reached."
    return None


def can_enter(lb, sym, q, now):
    """engine.ts canEnter + ledger-core.mjs canEnterUnderMandate under defaultMandate() (autopilot)."""
    if lb.get("run") != "running":
        return "Desk is paused."
    if (lb.get("edge") or {}).get("block"):
        return "Edge is standing aside. New risk is blocked."
    if sym in (lb.get("parked") or []):
        return "Edge parked this name."
    if sym in lb["pos"]:
        return "Already holding."
    if len(lb["pos"]) + len(lb["working"]) >= SABLE_MAX_POSITIONS:
        return "Position cap reached."
    if not q:
        return "No quote."
    if lb_size(lb, q) < 1:
        return "Insufficient cash."
    if not cal.is_rth(now):
        return "Session is closed to new paper risk."
    if any(w["symbol"] == sym for w in lb["working"].values()):
        return "Working paper order already exists."
    if q.get("kind") == "etf":
        return "ETF is context. Stock book first."
    if float(q.get("extensionAtr") or 0) > 1.85:
        return "Price is extended — anti-chase."
    if q.get("rsi") is not None and float(q["rsi"]) > 72:
        return "Momentum is stretched."
    return None


def lb_cash(lb):
    return float(lb["cash"]) - sum(float(w["qty"]) * float(w["px"]) for w in lb["working"].values())


def lb_equity(lb, quotes):
    return float(lb["cash"]) + sum(float(p["qty"]) * float((quotes.get(s) or {}).get("price") or p["avg"])
                                   for s, p in lb["pos"].items())


def lb_size(lb, q):
    return swing_size_shares(lb.get("equity") or lb["cash"], lb_cash(lb), q["price"], q.get("atr"),
                             bool((lb.get("edge") or {}).get("down")))


def sable_feed(feeds, sleeve, now, arg=None):
    """the canonical 1H series of the watchlist and the held names (desk/feedlib/canonical.py, tensor_swing's cache:
    Yahoo 60m regular session, range 1y, completed hours only) -> per name the bridge.ts Tensor read (v698
    analyzeVectorReplicaBars, signalOnly, interval 1h) and the quote-core quote; memoised per completed hour once
    every name's series reaches it."""
    from ...feedlib.canonical import Canonical, latest_completed_open
    st = (sleeve.engine.store.sleeve_get(sleeve.CONFIG.sleeve_id) or {}) if getattr(sleeve, "engine", None) else {}
    held = {s for lb in (st.get("books") or {}).values() for s in (lb.get("pos") or {})}
    syms = sorted(set(SABLE_WATCHLIST) | held)
    bar = latest_completed_open(now)
    memo = feeds.__dict__.setdefault("_sable_reads", {})
    if memo.get("bar") == bar and memo.get("syms") == syms:
        return memo["doc"]
    can = Canonical(os.path.dirname(feeds.hub.cache.root)) if feeds.hub is not None else None
    jobs, quotes, current = [], {}, True
    for s in syms:
        bl = can.bars(s, now) if can is not None else []
        current = current and bool(bl) and int(bl[-1]["t"]) == bar
        if not bl:
            continue
        q = sable_quote(s, bl)
        if q:
            quotes[s] = q
        jobs.append({"symbol": s, "interval": "1h", "bars": [{"t": int(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"],
                                                               "c": b["c"], "v": b.get("v") or 0} for b in bl],
                     "views": [{"name": "read", "vectorRead": True}]})
    reads = {}

    def take(job, res):
        v = ((res.get("views") or {}).get("read") or {}) if res.get("ok") else {}
        reads[job["symbol"]] = interpret(job["symbol"], v.get("read"))
    plane.frames(jobs, take, chunk=max(1, (len(jobs) + 1) // 2), workers=2)
    doc = {"asof": now, "reads": reads, "quotes": quotes}
    if current:
        memo.update(bar=bar, syms=syms, doc=doc)
    return doc


def run_hands(books):
    import subprocess
    p = subprocess.run(["node", "--no-warnings", HANDS], input=json.dumps({"books": books}), capture_output=True,
                       text=True, timeout=120)
    return json.loads((p.stdout or "").strip().splitlines()[-1])


class SableHandsBook(Sleeve):
    """planEdgeHands (autopilot-desk scout-hands.mjs, executed) with the paper hands armed, once per completed
    canonical hour, for each named lineage on its own sub-book (capital / 10), its plan applied as scout-cycle.ts
    applyEdgePlan applies it to the Sable desk: park / stand_aside (no new risk) / size_down / review_stop (tighten
    to support x 0.992) / paper_sell / paper_trim (half) / paper_buy -> proposeBuy (canEnter, swingSizeShares, the
    applyFill bracket avg - 1.6 ATR / avg + 2.8 ATR); every bar the desk's applyStopsAndTargets (swing floors,
    break-even trail after +1R) and the 2% daily-loss park (cleared at the next session)."""

    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            # one pass per completed canonical hour, 2-11 minutes after it closes (tensor_swing's schedule)
            sleeve_id="sable_edge_paper_hands", family=FAMILY, cadence_s=1200, universe=SABLE_WATCHLIST,
            needs={"feeds": [SABLE_FEED], "quotes": {"source": "equity"}}, schedule="rth&minute:32-41",
            params={"lineages": list(SABLE_LINEAGES), "max_positions": SABLE_MAX_POSITIONS,
                    "max_daily_loss_pct": SABLE_MAX_DAILY_LOSS_PCT},
            source={"repo": "autopilot-desk", "ref": "main", "commit": "48e8f90f5d9def28363eb4013dac4dd8d78f74bf",
                    "path": "src/lib/scanner/scout-hands.mjs", "blob": "8f8b9f7ab542b29303f448cbecf15f93e5a44ac8",
                    "lines": "6-126"},
            state_schema={"books": "dict", "bar": "int|None"})

    def bind(self, engine):
        self.engine = engine

    def quote_universe(self, now, book):
        return sorted(set(SABLE_WATCHLIST) | {i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:")})

    def _books(self, st):
        sub = float(self.CONFIG.capital) / len(SABLE_LINEAGES)
        books = {}
        for lin in SABLE_LINEAGES:
            lb = dict((st.get("books") or {}).get(lin) or {})
            lb.setdefault("cash", sub)
            lb["pos"] = {k: dict(v) for k, v in (lb.get("pos") or {}).items()}
            lb["working"] = {k: dict(v) for k, v in (lb.get("working") or {}).items()}
            lb["selling"] = {k: dict(v) for k, v in (lb.get("selling") or {}).items()}
            lb["parked"] = list(lb.get("parked") or [])
            lb["edge"] = dict(lb.get("edge") or {})
            lb.setdefault("run", "running")
            books[lin] = lb
        return books

    def _reconcile(self, books, held, avg, pend, now):
        """fills: a working buy whose order is gone opens the lineage's position when the book carries it; a sell
        whose order is gone closes what the book no longer holds."""
        claimed = defaultdict(float)
        for lb in books.values():
            for s, p in lb["pos"].items():
                claimed[s] += float(p["qty"])
        for lin, lb in books.items():
            for k, s in list(lb["selling"].items()):
                if k in pend:
                    continue
                lb["selling"].pop(k)
                p = lb["pos"].get(s["symbol"])
                if not p:
                    continue
                gone = min(float(s["qty"]), max(0.0, claimed[s["symbol"]] - held.get(s["symbol"], 0.0)))
                if gone <= 1e-9:
                    continue
                claimed[s["symbol"]] -= gone
                p["qty"] = float(p["qty"]) - gone
                lb["cash"] = float(lb["cash"]) + gone * float(s["px"])
                if p["qty"] <= 1e-9:
                    lb["pos"].pop(s["symbol"])
        done = defaultdict(list)
        for lin, lb in books.items():
            for k, w in sorted(lb["working"].items(), key=lambda kv: kv[1]["at"]):
                if k not in pend:
                    lb["working"].pop(k)
                    done[w["symbol"]].append((lin, k, w))
        for sym, new in done.items():
            room = held.get(sym, 0.0) - claimed[sym]
            got = []
            for lin, k, w in sorted(new, key=lambda x: x[2]["at"]):
                if room + 1e-6 >= float(w["qty"]):         # the book carries it: filled (else it expired unfilled)
                    got.append((lin, k, w))
                    room -= float(w["qty"])
            if not got:
                continue
            # the new shares' average fill: the book's cost basis less the lineages' earlier lots
            prior = sum(float(p["qty"]) * float(p["avg"]) for lb in books.values() for s, p in lb["pos"].items()
                        if s == sym)
            fresh = held.get(sym, 0.0) - claimed[sym]
            px_book = (float(avg[sym]) * held[sym] - prior) / fresh if avg.get(sym) and fresh > 1e-9 else None
            for lin, k, w in got:
                lb = books[lin]
                px = px_book if px_book is not None and px_book > 0 and math.isfinite(px_book) else float(w["px"])
                a = max(float(w.get("atr") or 0), px * 0.015)  # applyFill's bracket
                claimed[sym] += float(w["qty"])
                lb["cash"] = float(lb["cash"]) - float(w["qty"]) * px
                lb["pos"][sym] = {"qty": float(w["qty"]), "avg": px, "stop": _round2(px - a * 1.6),
                                  "target": _round2(px + a * 2.8), "opened": now, "key": k}

    def _exit(self, lin, lb, sym, qty, why, quotes, intents, bar, tag):
        p = lb["pos"].get(sym)
        if not p:
            return
        qty = min(float(p["qty"]), float(qty))
        working = sum(float(s["qty"]) for s in lb["selling"].values() if s["symbol"] == sym)
        if qty < 1 or working >= qty:
            return
        key = f"{p['key']}:{tag}{bar}"
        px = float((quotes.get(sym) or {}).get("price") or p["avg"])
        lb["selling"][key] = {"symbol": sym, "qty": qty, "px": px}
        intents.append(Intent("exit", sym, qty=qty, signal_key=key, order=OrderSpec(type="market", window_s=600),
                              reason=f"Edge hands {lin}: {why}"))

    def signal(self, view):
        st = dict(view.state or {})
        books = self._books(st)
        now = float(view.now)
        doc = view.extra.get(SABLE_FEED) or {}
        reads = list((doc.get("reads") or {}).values())
        quotes = doc.get("quotes") or {}
        held = {i.split(":", 1)[1]: float(p["qty"]) for i, p in view.positions.items() if i.startswith("EQ:")}
        avg = {i.split(":", 1)[1]: float(p["avg"]) for i, p in view.positions.items() if i.startswith("EQ:")}
        pend = {po.get("signal_key") for po in view.extra.get("pending_orders") or []}
        self._reconcile(books, held, avg, pend, now)
        bar = max([int(r.get("completedBarAt") or 0) for r in reads] or [0])
        intents = []
        if not cal.is_rth(now) or not reads or bar == st.get("bar"):
            st["books"] = books
            self._st = st
            return intents
        st["bar"] = bar
        day = cal._as_date(now).isoformat()
        requests = []
        for lin, lb in books.items():
            equity = lb_equity(lb, quotes)
            lb["equity"] = equity
            if lb.get("session") != day:                       # applySessionRollover: new day start, park cleared
                lb["session"], lb["day_start"], lb["run"] = day, equity, "running"
            for sym in sorted(lb["pos"]):                       # applyStopsAndTargets
                q = quotes.get(sym)
                if q:
                    hit = swing_bracket_check(lb["pos"][sym], q)
                    if hit:
                        self._exit(lin, lb, sym, lb["pos"][sym]["qty"], hit, quotes, intents, bar, "b")
            start = float(lb.get("day_start") or 0)
            if start > 0 and (equity - start) / start * 100 <= -SABLE_MAX_DAILY_LOSS_PCT and lb["run"] == "running":
                lb["run"] = "parked"                            # evaluateDailyLoss: new entries parked
            requests.append({"lineage": lin, "parked": lb["parked"], "brief": {"items": [], "management": []},
                             "candidates": [],
                             "desk": {"positions": [{"ticker": s, "qty": p["qty"], "avgPrice": p["avg"],
                                                     "stop": p.get("stop")} for s, p in lb["pos"].items()],
                                      "quotes": quotes, "mandate": {"autonomy": "autopilot"}, "equity": equity,
                                      "dayStartEquity": lb.get("day_start")},
                             "tensorReads": [{"ticker": r["ticker"], "paperBuy": r["paperBuy"],
                                              "paperSell": r["paperSell"], "gold": r["gold"],
                                              "completedBarAt": r["completedBarAt"]} for r in reads]})
        try:
            res = run_hands(requests)
        except Exception as e:
            st.update(books=books, error=f"{type(e).__name__}: {str(e)[:160]}")
            self._st = st
            return intents
        for r in res.get("results") or []:
            lin = r["lineage"]
            lb = books.get(lin)
            plan = r.get("plan") or {}
            if lb is None or plan.get("hands") != "paper":
                continue
            edge = lb["edge"]
            acts = plan.get("intents") or []
            for a in acts:                                      # scout-cycle.ts applyEdgePlan, in order
                sym = (a.get("symbol") or "").upper()
                kind = a.get("type")
                if kind == "park" and sym and sym not in lb["parked"]:
                    lb["parked"].append(sym)
                elif kind == "stand_aside":
                    edge["block"] = True
                elif kind == "size_down":
                    edge["down"] = True
                elif kind == "review_stop" and sym in lb["pos"]:
                    q, p = quotes.get(sym) or {}, lb["pos"][sym]
                    if q.get("support") is not None and p.get("stop") is not None:
                        tighter = _round2(float(q["support"]) * 0.992)
                        if float(p["stop"]) < tighter < float(q["price"]):
                            p["stop"] = tighter
                elif kind == "paper_sell" and sym:
                    self._exit(lin, lb, sym, (lb["pos"].get(sym) or {}).get("qty", 0), a.get("why") or "Tensor SELL.",
                               quotes, intents, bar, "s")
                elif kind == "paper_trim" and sym in lb["pos"]:
                    self._exit(lin, lb, sym, max(1, math.floor(float(lb["pos"][sym]["qty"]) / 2)),
                               a.get("why") or "Sell into strength.", quotes, intents, bar, "t")
                elif kind == "risk_pct" and a.get("stopRiskPct"):
                    edge["risk_pct"] = float(a["stopRiskPct"])
                elif kind == "paper_buy" and sym:
                    q = quotes.get(sym)
                    if can_enter(lb, sym, q, now):
                        continue
                    qty = lb_size(lb, q)
                    key = f"hands:{lin}:{sym}:{a.get('completedBarAt') or bar}"
                    lb["working"][key] = {"symbol": sym, "qty": float(qty), "px": float(q["price"]),
                                          "atr": q.get("atr"), "at": now}
                    intents.append(Intent("enter", sym, qty=float(qty), price_hint=float(q["price"]), signal_key=key,
                                          order=OrderSpec(type="market", window_s=600),
                                          reason=f"Edge hands {lin}: {a.get('why')}", meta={"lineage": lin}))
            if not any(a.get("type") == "stand_aside" for a in acts):
                edge["block"] = False
            if not any(a.get("type") == "size_down" for a in acts):
                edge["down"] = False
        st["books"] = books
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def extra_sleeves():
    return [RejectionMemoryBook(), TraceBook(), SableHandsBook()]


def sleeves():
    return research_sleeves() + handoff_and_reset_sleeves() + extra_sleeves()


def feed(feeds, sleeve, now, arg=None):
    """the published documents (cache-only; memoised on each file's mtime): {"1h" | "1d" | "1wk": the event
    documents, "rm": the rejection-memory signals, "trace": the TRACE candidates}."""
    from ...util import read_json
    root = getattr(getattr(sleeve, "engine", None), "root", None)
    memo = feeds.__dict__.setdefault("_tensor_research_docs", {})
    out = {}
    if not root:
        return out
    paths = {iv: plane.events_path(root, iv) for iv in ("1h", "1d", "1wk")}
    paths.update(rm=rm_path(root), trace=trace_path(root))
    for name, p in paths.items():
        try:
            m = os.stat(p).st_mtime_ns
        except OSError:
            continue
        if memo.get(p, (None,))[0] != m:
            memo[p] = (m, read_json(p, None))
        if memo[p][1] is not None:
            out[name] = memo[p][1]
    return out


FEEDS = {FEED: feed, SABLE_FEED: sable_feed}
