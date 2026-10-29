"""Roll call: every sleeve row on the record classified, each verdict with the record lines that prove it.

  FIRING   it evaluated in its window on its last expected session and it is acting: it holds a position, or its
           decision of record ordered an entry, exit, target or adjustment, and no planned exit is overdue.
  WAITING  it evaluated on schedule, is flat, and its decision of record saw no qualifying signal (an observation,
           a rule gate, or no intent at all). The row carries when it last traded ("never since <first_day>") and,
           where the notes know it, how rare its signal is.
  OFF      owner-disabled in the manifest, not loaded by the registry, parked, or a row that by design never trades.
  BLOCKED  it evaluates but cannot act: its decision of record is only input blockers, or a known missing input.
  BROKEN   a sleeve_error in its last session, a due pass it was not evaluated in, a window no pass ran in, an error
           its own state records, a planned exit overdue on an open position, or a demonstrated defect (notes).

Pure reads of a state directory (the host's state/, or a desk-state archive's state/), no network, no writes except
the outputs asked for:
  report.json        the corpus: one row a sleeve, with first_day (its fills and last_trade_at as of the report's
                     generated_at, which can be days old; the book and the ledger's book_fill records come first)
  desk.json          last_run per sleeve (set only when signal() returned), last_pass: the record's clock
  books.json         open positions and their planned exits, n_fills, closed trades
  sleeves/*.json     sleeve-private state (an error a sleeve keeps to itself)
  ledger             state/ledger.jsonl, or the record's segments state/ledger/ (manifest.json, seg-*.jsonl.gz,
                     open.jsonl): pass times, signals, observations, sleeve_error and book_fill records
and from the checkout: config/manifest/sleeves.jsonl under --root (status, disabled) and the sleeve configs of the
registry this module imports (schedule, cadence, status). The clock is the record's own last pass, never the wall
clock, so a replay of an old record gives the verdicts that record supported.

NOTES carries what the record cannot show by itself (a producer switched off, a defect an audit demonstrated, how
rare a rule's signal is), each with its source and the builder item that owns it. A note never hides the record:
the row keeps its record evidence, and a note that overrides the class says so in `evidence`.

  python -m desk.learn.rollcall --state STATE_DIR [--root CHECKOUT] [--json OUT] [--md OUT] [--csv OUT]
"""
import argparse
import bisect
import csv
import fnmatch
import gzip
import importlib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, time as dtime

from .. import calendar as cal
from ..schedule import _alt_open, anchor_due, is_open
from ..util import ET, UTC, read_json, write_json_atomic

CLASSES = ("FIRING", "WAITING", "OFF", "BLOCKED", "BROKEN")
ACTIONABLE = ("enter", "exit", "target", "adjust", "cancel")
DUST = 1e-6                      # a position smaller than this is a rounding remainder, not a holding
GAP_S = 45.0                     # pass gaps longer than this are searched for a window that opened and closed inside
GAP_STEP_S = 15.0
EXIT_GRACE_S = 6 * 3600          # a planned exit this far past due, on an open position, is overdue
# a sleeve that has never recorded an intent: its evaluation is on the record (desk.json last_run), its reason for
# standing aside is not (AUDIT_MAC MAC-04, a DEFECT no builder holds: no-decision records for silent sleeves)
SILENT = "evaluated on schedule; no intent at its last session (no abstention reason is recorded: MAC-04)"

# A blocker's reason says whether the rule declined (normal: WAITING) or an input is missing (BLOCKED). Matched on the
# intent's reason text, first list first; an unmatched "blocker:" or "BLOCKED" reason counts as an input blocker.
RULE_REASONS = (
    r"regular_session_closed", r"entry_window_closed", r"regime_skip", r"budget_exceeded",
    r"no_qualified_delta_DTE_contract", r"block qqq_down_on_the_week", r"market risk_off", r"AWAITING SIGNAL",
    r"pass=False", r"\bWATCH\b", r"NO_PROFILE_CLEARS_GATE", r"proxy-B red", r"short_not_explicitly_supported",
    r"MODEL_TEST_ONLY",
)
# a Lazarus lane's own record of its input (FEED-02, act1): "blocked_data: input missing: <file> (its source <job> is
# switched off ...)" or "blocked_data: input stale: <file> (<the composer's verdict>)", once a session; checked first, so a
# rule word inside the quoted verdict never reads as the rule's own decline ("blocked_data cleared: ..." is not one)
LANE_BLOCKED = r"^blocked_data: input (missing|stale)\b"
INPUT_REASONS = (
    LANE_BLOCKED, r"BLOCKED_INPUT", r"incomplete enrollment", r"cross_section_incomplete", r"enrollment_coverage_below",
    r"FUNDING_SOURCE_HTTP_451", r"INVALID_OR_WIDE_QUOTE", r"_required\b", r"\bBLOCKED: \d+ completed bars",
    r"^blocker: '[A-Z./]+'$", r"native_identity_or_actions_unqualified", r"\bstale\b", r"entry_last_trade_stale",
    r"ENTRY_WINDOW_EXPIRED",
)
_NOT_STALE = re.compile(r"""['"]stale['"]\s*:\s*(False|false|0)""")      # a health dict that reports stale = False
_BLOCKISH = re.compile(r"^blocker:|\bblocked:|\bBLOCKED\b|BLOCKED_INPUT|incomplete enrollment")


def reason_kind(reason):
    """'rule' (the rule declined), 'input' (an input is missing or stale) or None (not a blocker) of an intent reason"""
    r = _NOT_STALE.sub("", str(reason or ""))
    if re.search(LANE_BLOCKED, r):
        return "input"
    for p in RULE_REASONS:
        if re.search(p, r):
            return "rule"
    for p in INPUT_REASONS:
        if re.search(p, r):
            return "input"
    return "input" if _BLOCKISH.search(r) else None


# -- what the record cannot show by itself. Each entry: glob pattern(s) on the sleeve id -> fields:
#    cls      the class when the record alone would say otherwise (the evidence says "note")
#    cause    the root cause, with its source; owner: the builder and item that cover it ("" = none)
#    rarity   for WAITING rows: how rare the rule's signal is, from its rule or research row
#    only_if  apply the class only while the record still shows this state ("silent": no signals in the last
#             session; "flat": no open position); otherwise the note's cause is kept as context
_D1 = ("the FUNDING_SOURCE_HTTP_451 blocker was last logged 2026-10-17; since then the CoinGecko relay supplies "
       "Binance's own rate (96 of 96 settlements, AUDIT_CRY 0.1; keeping the relay is owner decision D1). The 451 "
       "itself is a legal block and stays as it is")
_MILKMAN_OOS = "milkman study v2 out/tab_primary.md, SPY intraday OOS 2013-2026-04 (about 3,350 sessions)"
NOTES = [
    # -- Lazarus lanes (lazarus.py, Author_wait*.py: fix1) -----------------------------------------------------
    (("lz_q07w_*", "lz_q07_wiki", "lz_q07_ins2", "lz_1wsw_stress"),
     {"cls": "BLOCKED", "only_if": ("silent", "unrecorded"),
      "reason": "its inputs come from the alt-data producer the owner's OFF switch holds since 2026-10-19",
      "cause": "every input these lanes need (wiki, insider2, FINRA ATS, gamma, the w_swing feed) comes from "
               "altdata_nightly, switched off 2026-10-19 (Author_producers.OFF, commit 7e9f0673) after its run was "
               "killed at the 4 h limit (jobs.json Author_altdata_nightly ok=false); the sleeve_feed reports those "
               "feeds stale (AUDIT_FEED 1.2(1))",
      "owner": "fix1 FEED-02 (30fed390) and act1 (cf1748c4: one switch per source, stale inputs named): a lane records "
               "its own block (a blocked_data observation a session, its state's blocked_on), and from its first pass "
               "on that code the record decides, not this note; the sources: owner decision D3 / D28"}),
    ("lz_wait_chase",
     {"cls": "BROKEN", "only_if": "silent", "until": "2026-10-27T04:00:00Z",
      "reason": "the 08:50 WAIT compose erased its in-window fires",
      "cause": "the 2026-10-19 08:50 Author_wait_compose overwrote its 9 fires with 'no engine daily bars' at status "
               "ok, 40 minutes before their only window (AUDIT_FEED 1.2(3)); 7 new CHASE fires wait for the "
               "2026-10-26 09:30-10:35 window",
      "owner": "fix1 FEED-03 (e3acc604, merged to master-desk in 5dcbb7bb); its proof is the next CHASE window"}),
    ("lz_wait_flow",
     {"cls": "BROKEN", "only_if": ("silent", "unrecorded"), "reason": "every fire reaches the wait file after its window",
      "cause": "its dv20 comes only from the fire's lc2/ue tag, which the tracker writes after the next day's 16:45 "
               "run; all 6 FLOW fires in the record arrived after their D+1 09:30-10:35 window (AUDIT_FEED 1.2(4))",
      "owner": "fix1 FEED-04a (39349691: no FINRA fetch while the sources are OFF); act1 FEED-04b (42948524: dv20 from "
               "the engine store at D) and daf9f162 (recorded BLOCKED while its short-volume source is off); once the "
               "lane records its own block the record decides, not this note"}),
    ("lz_wait_q14", {"rarity": "tier-A 1W fires closing at or under $5.00: 0 of 89-101 1W fires per run in the record "
                               "(nearest miss BMBL at $5.93; AUDIT_FEED 1.2(5)); the playbook states no rate"}),
    (("lz_1wc_micro", "lz_1wc_ml", "lz_1wg_small"),
     {"rarity": "tier-A weekly cells: no qualifying tier-A row in the record's 2 weekly cycles (140 tracker sc_tags; "
                "AUDIT_FEED 1.2(2)); the playbook states no rate"}),
    ("lz_1wsw", {"rarity": "1W-swing-covered search fires: none in the record's 2 weekly cycles (AUDIT_FEED 7)"}),
    ("lz_cl_vmr_qqq", {"rarity": "VIX Mood Ring composite at or under 35, then QQQ for 5 days: 7 out-of-sample events "
                                 "in its source (UNPROVEN there); the last read was 57.4 (AUDIT_FEED 7)"}),
    # -- r19 crypto (r19_crypto.py: fix1) -------------------------------------------------------------------------
    (("r19_linkusdt_negative_funding_squeeze_*", "r19_linkusdt_absorption_negative_funding_*",
      "r19_linkusdt_breakout_base_*", "r19_linkusdt_absorption_base_*"),
     {"cls": "BROKEN", "only_if": "flat", "reason": "its LINK entries fail the capture clock (CRY-D1)",
      "cause": "the evaluator refuses an entry unless the last trade printed 0-60 s before its clock; the wrapper set "
               "that clock to the pass start while its Binance reads came 5.8-22 s later, so LINK's latest trade lay "
               "'in the future' (entry_last_trade_stale, then ENTRY_WINDOW_EXPIRED): 0 of 20 due passes entered in "
               "LINK's two signal windows (AUDIT_CRY 0.2)",
      "owner": "fix1 CRY-D1 (64bef51b + cfb81ba8, r19 parity 300/300 identical)"}),
    (("r19_enjusdt_negative_funding_squeeze_*", "r19_enjusdt_absorption_negative_funding_*"),
     {"rarity": "needs a negative settled funding rate at the signal: ENJ funding was +5.0e-05 at both ENJ signals of "
                "the record (10-21 breakout, 10-24 absorption), so the rule stood aside (AUDIT_CRY 0.1)",
      "cause": _D1}),
    (("r19_adausdt_absorption_nonnegative_funding_*", "r19_linkusdt_absorption_nonnegative_funding_*"),
     {"rarity": "needs funding >= 0 at an absorption signal: ADA's (10-24 20:00Z) was -9.7e-06 and LINK's -3.03e-05, so "
                "the rule stood aside (AUDIT_CRY 0.1); absorption signals: about 1 per symbol per 9 days",
      "cause": _D1}),
    ("r19_*usdt_*", {"cause": _D1}),
    # -- r19 ETF / tensor ----------------------------------------------------------------------------------------
    (("r19_etf_core25_*", "r19_etf_drift1_*", "r19_etf_exsmh1_*", "r19_etf_interval*", "r19_etf_leader1_*"),
     {"rarity": "the rotation books trade only at a month's first session, 09:35-09:40 ET, and never backfill a "
                "missed origin; installed 2026-10-19, their first origin is 2026-11-02 (AUDIT_MAC 3.4, AUDIT_FEED H-4)"}),
    ("r19_tensor_beta_m2_52w_25", {"owner": "fix2 EQ-09 (bf64fcfe: records the coverage and the names BETA_M2 "
                                            "cannot read)"}),
    ("r19_tensor_*", {"rarity": "weekly Tensor G4 / C1 turns, 52-week holds; the enrollment blocker last cleared "
                                "2026-10-21 08:24Z and no blocker or entry has been recorded since; the record holds "
                                "no coverage receipt, so 'no event' and 'not eligible' are not told apart yet",
                      "owner": "fix2 EQ-09 (bf64fcfe) adds the coverage receipt"}),
    # -- ausar ------------------------------------------------------------------------------------------------------
    ("ausar_daily20_*", {"owner": "owner decision D2 (Tensor on daily bars, CRY-O5), then the census repair CRY-D2; "
                                  "no builder item",
                         "cause": "the census knows 10.58% of the 1,815 enrolled names against its 99% entry gate on "
                                  "every session (AUDIT_CRY 2.5)"}),
    ("ausar_opt_tensor_leaps_*",
     {"cls": "BLOCKED", "reason": "its input, the r19_tensor G4 bridge, has carried no qualified G4 event",
      "cause": "the vendored evaluator raises qualified_native_G4_event_bridge_required while the r19_tensor snapshot "
               "carries no G4 event (r19_options.py); r19_tensor's G4 books have recorded no event since 2026-10-21",
      "owner": "upstream: fix2 EQ-09 (r19_tensor coverage); no item of its own"}),
    (("ausar_opt_rsi2_*_b", "ausar_opt_vwap20_*_b", "ausar_opt_pead_long_b"),
     {"rarity": "the B books are near-silent by construction: a $500 risk budget is less than one 0.55-delta 14-21 DTE "
                "QQQ or SPY call (about $1,100-1,550) and the premium and debit caps reject the typical contract, so "
                "they can realistically trade IWM verticals only (AUDIT_OPT 3.4); recovery signals: 1 in the record",
      "owner": "owner decision OPT-13 (keep B as the paired control, or retire it)"}),
    ("ausar_opt_opening_gamma_*", {"rarity": "an opening reversal after a prior-afternoon spike, on a 0-2 DTE contract "
                                             "that qualifies by delta: no qualified contract on the record's signal "
                                             "days (AUDIT_OPT 3.3)"}),
    ("ausar_opt_xsp_calm_*", {"rarity": "the prior-week XSP digital decides each Monday: the 10-19 decision was a "
                                        "regime skip (XSP_conditional_regime_skip)"}),
    ("ausar_public_ai_volume_spot100", {"rarity": "its LINKUSDT 4h signals in the record were short, and this spot "
                                                  "book cannot short (entry veto): not a blocked input (CRY-D3)"}),
    ("ausar_public_squeeze20", {"rarity": "a Bollinger/Keltner squeeze breakout on the sector ETFs: no signal in its "
                                          "daily decisions of the record (AUDIT_CRY 2.3)"}),
    ("ausar_public_tomazetti_rsi2_spot100", {"rarity": "ADAUSDT 1h: RSI(2) under 10, its 4-bar average under 30, the "
                                                       "close above the 200-bar average: no signal in the record"}),
    ("ausar_wstate", {"rarity": "weekly state-repair qualifiers at the weekly bar; no qualifier in the record's weekly "
                                "cycles (its ledger observations: 0 held, 0 fills)"}),
    # -- femto ------------------------------------------------------------------------------------------------------
    ("femto_momentum",
     {"cls": "BROKEN", "only_if": "flat", "reason": "its one review ran in the 10-16 data outage and bought nothing",
      "cause": "its 63-session review ran at the 2026-10-16 14:07:41Z pass, while the pass's data health read alpaca "
               "'no credentials' and Yahoo quotes HTTP 429; it emitted no buy and still stamped "
               "meta.last_review_spy_date = 2026-10-15; with no holdings, every later pass targets the empty book, so "
               "it cannot buy before the next review, 63 SPY sessions on (the 63rd after 10-15 is 2027-01-15)",
      "owner": "roll1 f3208a3a (a review stays due until its buys are sent; the outage's stamp is due again); "
               "FOMC blackout 10-26..10-28 holds its buys until 10-29"}),
    ("femto_leaps_momentum",
     {"cls": "BLOCKED", "only_if": "silent", "reason": "its input, femto_momentum's book, is empty",
      "cause": "it carries femto_momentum's holdings in LEAPS; that book is empty because femto_momentum's only "
               "review bought nothing (see femto_momentum)",
      "owner": "roll1 f3208a3a, with femto_momentum"}),
    ("femto_tensor_swing",
     {"cls": "BROKEN", "only_if": "flat", "reason": "its canonical 1H input arrives a session old",
      "cause": "most of its decisions are demoted as stale at 18-22 clock-hours old, never under 6 h (the last on "
               "2026-10-23 14:33Z), so its 1H series ends at the prior session during regular hours (AUDIT_EQ 3.1)",
      "owner": "fix2 EQ-05 (4e806b72 + 0598a07b: records what the canonical 1H feed served on each pass)"}),
    ("femto_free_opt_tail",
     {"cause": "269 of its 406 evaluations fail the clock rule (250 'receipt is earlier than the source timestamp', "
               "19 'source timestamp is beyond the 2-second clock tolerance'): the options hub stamps a chain's receipt "
               "at the start of its fetch (desk/data/options.py _load passes the pre-fetch clock as the chain's "
               "'at'), while the Alpaca quotes inside carry later times",
      "owner": "roll1 0e3929c4 (the tail and the wheel read the chain's completion; parity's economic path, owner "
               "decision FEED-12a, and the muse_week adapter keep the start)"}),
    ("femto_free_opt_wheel", {"cause": "158 of its 406 evaluations failed the same clock rule as femto_free_opt_tail "
                                       "(see there)", "owner": "roll1 0e3929c4"}),
    ("femto_free_opt_parity", {"owner": "owner decision FEED-12a (retire the economic path); FEED-12b only if kept",
                               "rarity": "its indicative path is MODEL_TEST_ONLY by rule (recorded, never traded); its "
                                         "economic path found 0 packages in the 49 of 406 evaluations the clock rule "
                                         "let through (AUDIT_FEED 3(b))"}),
    (("femto_fwd_alpaca_ada_rsi2", "femto_fwd_alpaca_link_ai_volume"),
     {"rarity": "its warm-up blocker (0 completed bars) was last recorded 2026-10-17; its monitor records only sends "
                "and blocks, so a waiting pass leaves no record: an RSI(2) / volume-impulse rule on 1h / 4h bars"}),
    ("femto_beatendown", {"rarity": "weekly: ranked Friday, bought Monday 10:20-10:35 ET; meta.pending holds 5 buys "
                                    "(BAH, BL, BSY, TRUP, ZS) for 2026-10-26"}),
    ("femto_confluence", {"rarity": "weekly: qualifiers firing at least 2 of the 9 frozen confluences; the 10-23 rank "
                                    "selected none (meta.pending.selected_detail empty)"}),
    (("femto_blowoff_d", "femto_leader_d"), {"rarity": "fires only in a SPY down regime (trailing-60 return <= 0): "
                                                       "meta.spy_down_regime = false at the 10-23 rank"}),
    ("femto_gate_1h", {"rarity": "a gated Leader-1d daily event, then the first RTH 1H bar after it: its last scan "
                                 "(10-23 19:58Z) found 0 (meta.last_signals 0)"}),
    (("femto_rule_1d_cyan_smallcap", "femto_rule_1d_green_tom", "femto_rule_1w_swing_beta_wt", "femto_rule_1h_cyan_raw"),
     {"rarity": "a GBM / rule-scorer fire passing exact thresholds; the 10-23 rank produced none (meta.last_signals "
                "empty, meta.pending.buys empty)"}),
    (("femto_capitulation", "femto_capitulation_options"),
     {"rarity": "the 5-part 1H capitulation signature (RSI(14) under 20, a climax bar over 2x volume, its low within 2% "
                "of the daily EMA200, daily ATR/close over 5%, then a green bar): rare by design"}),
    ("femto_earnings_buyback", {"rarity": "an 8-K buyback of at least 5% of the shares 15-30 days before earnings: the "
                                          "edgar_buyback job's 10-23 scan found 0 in its 73-name universe"}),
    ("femto_iron_condor", {"rarity": "IV rank >= 50 on its own stored IV history (60 observations first), VIX <= 35, no "
                                     "earnings within 45 days"}),
    ("femto_legends_ema", {"rarity": "QQQ trend day with no touch of the 15m EMA20 the prior session: the LEMA setup, "
                                     "about 1 in 21 sessions on SPY (" + _MILKMAN_OOS + ")"}),
    ("femto_phoenix", {"rarity": "a strict 20-day closing high while SPY's trailing 60-session return is <= 0, then a "
                                 "red day within 5 sessions"}),
    ("femto_qullamaggie_paper", {"rarity": "gated off while the QQQ 10/20 market state is risk_off (meta.watch "
                                           "market_state risk_off on 10-23)"}),
    ("femto_rsi_meanrev_options", {"rarity": "RSI(2) under 10 above the 200-day SMA on the basket, as a 14-30 DTE call "
                                             "spread"}),
    ("femto_vix_hedge", {"rarity": "buys only while VIX is complacent (under 16 or its 30-day percentile under 25); "
                                   "its 10-16 VXX call (VIX 15.91) expired unfilled"}),
    ("femto_donchian", {"rarity": "a 20-day Donchian breakout on the basket; its 10-20 ANF entry expired unfilled in "
                                  "the Alpaca outage"}),
    # -- midna --------------------------------------------------------------------------------------------------------
    (("midna_d_cyan_gbm", "midna_d_green_band", "midna_w_cyan_high_adx", "midna_w_cyan_mid_vix",
      "midna_w_cyan_quiet_tape", "midna_w_green_calm_smh"),
     {"rarity": "a forward-lab account over the forward scan: the 10-23 scan staged nothing for its rule (state "
                "scanned 2026-10-23, staged [])"}),
    ("midna_w_cyan_moonshot", {"rarity": "the hourly watch's weekly cyan moonshots: the midna_watch job of 10-23 found "
                                         "0 moonshots"}),
    ("midna_w_cyan_breadth", {"rarity": "fires only on rows staged by midna_w_cyan_quiet_tape, which staged nothing "
                                        "(AUDIT_FEED 7)"}),
    (("midna_ema4_vwap", "midna_macd_cci"),
     {"rarity": "a MACD(12,26) cross with CCI(20) over 100 / an EMA(4) cross over a rising 20-session VWAP, from the "
                "board signals that fed midna_turtle_s1's entries; none since the books' birth (10-16)"}),
    ("midna_opt_turtle_atm_call", {"rarity": "a Turtle breakout of the listed surface set with a two-sided ATM call no "
                                             "wider than 50% of mid: none since its birth (10-16)"}),
    ("midna_qqq_csp_ladder", {"rarity": "a new layer once per ISO week, only on a day QQQ is not down and VIX not up, "
                                        "on a chain built within 20 minutes: none added (addedWeek null)"}),
    ("midna_qqq_flip5_tza", {"rarity": "the QQQ flip-5 signal turned on 10-23: a pending BUY waits for the 2026-10-26 "
                                       "session (state pending BUY, pending_from 2026-10-23)"}),
    ("midna_hourly_playbook", {"owner": "playbook 1.0.0 stays as it is (InfinityBlade); its capacity skips are its own "
                                        "rule"}),
    # -- milkman (rarity from the study's OOS trade counts) ---------------------------------------------------------
    ("mk_esmondayclockonspyproxy",
     {"cls": "OFF", "reason": "by design an observation: the ES-Monday clock trades outside the desk's session",
      "cause": "its 06:00 ET entry is recorded as an observation (the desk routes equities only in the regular "
               "session) and its long and short lanes net flat in any case (desk/sleeves/milkman/intraday.py, named "
               "divergence 5)"}),
    ("mk_bilbogoldengate", {"rarity": "BGG: 38 trades long + short (" + _MILKMAN_OOS + "): about 1 in 90 sessions"}),
    ("mk_directionaltriggerbox", {"rarity": "TBOX: 121 trades (" + _MILKMAN_OOS + "): about 1 in 28 sessions"}),
    ("mk_legendsemaintradayproxy", {"rarity": "LEMA: 162 trades (" + _MILKMAN_OOS + "): about 1 in 21 sessions"}),
    ("mk_premarketathmorningfade", {"rarity": "PMATH: 201 trades (" + _MILKMAN_OOS + "): about 1 in 17 sessions, only "
                                                                                    "after a premarket all-time high"}),
    ("mk_fourhourpoopexrollover", {"rarity": "OPX4: 9 trades (" + _MILKMAN_OOS + "): under 1 a year, OpEx weeks only"}),
    ("mk_gapupprenooncontinuation", {"rarity": "GUPN: 405 trades (" + _MILKMAN_OOS + "): about 1 in 8 sessions"}),
    (("mk_oneilfollowthroughdayrace", "mk_oneilfollowthroughdayrace_short"),
     {"rarity": "FTD on the index set: 424 pooled OOS trades since 2013 over 14 instruments (SPY 21, QQQ 33): about 2-3 "
                "a year per instrument (milkman study REPORT.md)"}),
    ("mk_legendsbuydaydayleg", {"rarity": "the Legends buy-day day leg on SPY (k=4, gate 0.15): an index-set event; none "
                                          "in the record"}),
    # -- quant_research ---------------------------------------------------------------------------------------------
    (("qr_conjunctiveentitlementrepricing", "qr_timecutflowtransport", "qr_commitmentadjustedrecoverymemory"),
     {"cls": "BLOCKED", "reason": "its signal's input has no free source; it holds its playbook's funded index core",
      "cause": "cer needs adjudicated entitlement proofs, tcft bounded lot allowances (its own audit: 'the public lower "
               "gap is zero'), carm ITCH-grade order-ID lifecycles: none has a free source, so the row holds its SPY/QQQ "
               "core indefinitely and its decision of record is the core of 10-19 (named divergence 1 of "
               "desk/sleeves/quant_research/cer.py, tcft.py, carm.py; AUDIT_MAC R10 cores)",
      "owner": "owner decision MAC-08 / D9 (hold the idle core in T-bills, or pause cer, tcft and carm)"}),
    ("qr_bracketedoptionlawtransport",
     {"cls": "BLOCKED", "reason": "its event snapshots are blocked, and its first tilt needs 144 FOMC/CPI events",
      "cause": "its snapshots for the 2026-10-28 FOMC (taken 10-21) are BLOCKED for NDX and SPX, 'no feasible law or "
               "solver failure; quotes are not repaired' (state snaps; log 10-22 NO_FEATURES), and it needs 80 "
               "training, 40 calibration and 24 development FOMC/CPI events before its first tilt, about 7 years at "
               "about 20 a year (desk/sleeves/quant_research/bolt.py docstring; AUDIT_MAC R10 cores); it holds its "
               "50 / 50 SPY/QQQ core meanwhile",
      "owner": "owner decision MAC-08 / D9 (the core); the quotes it refuses to repair are its source's rule"}),
    (("qr_auctionimpulseresponsetrading", "qr_capitalreleasedynamics", "qr_contractqueuerevaluation"),
     {"rarity": "cash abstention until its event input qualifies (AUDIT_MAC 3.2); none in the record"}),
    ("qr_newsconditioned121leadership", {"rarity": "acts on a monthly snapshot taken after a month's last session: none "
                                                   "yet (state log 'no monthly snapshot yet'); the next is due after the "
                                                   "2026-10-30 close"}),
    ("qr_spectral_echo_drift",
     {"cause": "every tape read overruns the IEX quote stream's 50 pages of 10,000 quotes (a reloaded tape refills 40 "
               "minutes of raw updates in one read; the open's catch-up windows cover two minutes of 20 mega-caps), so "
               "the tape never moves and it decides nothing (ops1's 20c813b4 analysis)",
      "owner": "ops1 (20c813b4, merged to master-desk in 53dc84b7) stops the repeated paging only: the sleeve still "
               "decides nothing until its reads are smaller, which ops1 left to the owner"}),
    # -- tensor_research / sable / Author / killed / griffith -------------------------------------------------------
    (("ro_weekly_*", "griffith_weekly_*"),
     {"rarity": "a weekly event book: one weekly publication per week (10-16, 10-23) and no event of its row"}),
    (("ro_swing_transition_1h_v1", "ro_hourly_transition_core_burst"),
     {"rarity": "an hourly event book on its frozen basket: no event of its row in the record"}),
    ("qr_tensor_residual_accumulation", {"rarity": "TRACE daily candidates: planned 2026-10-23, no lot taken"}),
    ("sable_edge_paper_hands", {"rarity": "the paper hands' buy plan per lineage, once per completed hour: no buy "
                                          "planned in the record"}),
    ("Author_echo_swing", {"rarity": "Echo's buy posts trade only when read 04:00-15:45 ET on a weekday (the sidecar's "
                                     "own paper gate): the record's 4 posts came after hours or on a weekend (state "
                                     "echo.papers, status held); the source papers each post once, when first read, "
                                     "and holds it for good outside the window (Author-desk@652db7af "
                                     "scripts/echo-sidecar.mjs runEchoSweep / paperEcho): its rule"}),
    (("Author_scanner_book_swing", "Author_sector_first_bottom"),
     {"rarity": "the scanner book's buys / bottom list on the paper wire: nothing booked (state fills [])",
      "owner": "MAC-04 (no-decision record): unassigned"}),
    ("killed_leader1d_short", {"rarity": "Leader-1d events inside its 41-name basket only (its long twin reads the "
                                         "1,838-name genome): none in the record"}),
    ("killed_smcap_beta_52w", {"rarity": "the week's M2 qualifiers that are beaten-down, small and high-beta at once: "
                                         "none taken (tranches [])"}),
    ("griffith_orb20", {"rarity": "a 09:30-09:50 range breakout with first-20-minute volume at least 2x its 20-session "
                                  "median: none qualified (state qualified {} on 10-23)"}),
    (("griffith_simple_daily_trend", "griffith_liquid_momentum_trend", "griffith_momentum_pead"),
     {"cause": "the shared feed griffith_iex_1d is memoised once per pass for every sleeve, but its producer answers "
               "{skipped: true} to an asker that does not want the tape (desk/feedlib/griffith.py feed, "
               "wants_tape): since 10-20 the first asker of each RTH pass, griffith_xs_mom_12_1, has its month "
               "decided, so every later Griffith sleeve of that pass gets the skip and its daily step returns early",
      "owner": "roll1 4ca1b77f (the feed is produced per asking sleeve)"}),
    (("griffith_leaders_rest", "griffith_parallax"),
     {"cause": "its 10-22 tape missed 16 of 534 names (state tape.missing 16); resting entries are its design"}),
    # -- rows whose decision of record already names the reason: the rate behind it -------------------------------
    ("ausar_absorption_*_4h", {"rarity": "a 4h volume shock (over 2x EMA20, a down bar under EMA50) then a confirming "
                                         "bar: about 1 signal per symbol per 9 days in the record (AUDIT_CRY 2.1)"}),
    (("femto_free_kraken_ada_basis", "femto_free_kraken_link_basis"),
     {"rarity": "a perp/spot basis above its 180-bar mean + 2 sd with positive funding: no qualifying 4h candle of the "
                "56 in the record (AUDIT_FEED 3)"}),
    (("femto_free_opt_own_iv", "femto_free_opt_pair", "femto_free_opt_release"),
     {"rarity": "an SPY option rule that waits on its own read (a HAR forecast 2 points over the straddle's IV, a pair "
                "residual |z| past its band, a verified public event): none in the record (its decision of record "
                "names the missing condition)",
      "cause": "73 of its 406 evaluations were refused by the clock rule through its indicative probe and legs (the "
               "receipt stamped at the fetch's start, see femto_free_opt_tail)",
      "owner": "roll1 3e452eec (the probe, legs and decision moment read the chain's completion)"}),
    ("femto_qqq_put_ladder", {"rarity": "adds a layer only while QQQ is not down on the week: blocked by that rule on "
                                        "every decision of the record"}),
    ("Author_komar_momentum", {"rarity": "screens only while the proxy-B market colour is not red: red on every screen "
                                         "of the record"}),
    (("qm_episodic_pivot", "qm_leader_breakout_pass3", "qm_parabolic_short"),
     {"rarity": "screens only while the QQQ 10/20-day market gate is open: risk_off on every screen of the record "
                "(AUDIT_EQ 3.7)"}),
    ("mk_calltoputputtocallreversal", {"rarity": "C2P: 494 trades long + short (" + _MILKMAN_OOS + "): about 1 in 7 "
                                                 "sessions; its lanes net on SPY"}),
    ("mk_threeminutetriggerconfirmation", {"rarity": "CT3: 1,787 trades long + short (" + _MILKMAN_OOS + "): about 1 a "
                                                     "session, mirror lanes that net on SPY; its one net order of "
                                                     "10-20 fell in the Alpaca outage"}),
    ("qr_tensor_rejection_memory", {"rarity": "a Tensor trigger with a stored rejection accepted: 1 entry decided in "
                                              "the record (BILL, 10-22 07:00 ET), not filled"}),
    (("r19_timing_cloud_base", "r19_timing_cloud_aggressive"),
     {"rarity": "an EMA5/12 10-minute cloud signal inside 09:50-15:30 ET: none on the qualified names; the source's own "
                "per-name qualification keeps ASPI, HIVE, SIVEF out (issuer identity / actions unqualified) and CVNA, "
                "MU short of history"}),
    ("span_harvest_unified", {"rarity": "trades a match only when a replay profile clears its PZOE gate (5 fills, 85% "
                                        "coverage, positive lower bounds): 133 selections in the record, every one "
                                        "NO_PROFILE_CLEARS_GATE; its source study rejected the rule (AUDIT_CRY 2.6)"}),
    # -- firing rows with an open item that bites on a known day (context; the class stays the record's) -----------
    ("apex_o*", {"owner": "OPT-01 live since 0c010a49 (Monday 10-26 is its first Monday); OPT-02 / OPT-03 with fix2 "
                          "(8c950cef, f9c0ed11)"}),
    (("griffith_xs_mom_*", "griffith_52w_high_rs", "griffith_etf_*"),
     {"owner": "fix2 EQ-02 (the coverage gate before the 2026-11-02 rebalance)"}),
    ("ausar_opt_qqq95_*", {"owner": "ops1 OPT-05 (entry deadlines on the route's clock, 8ffee956)"}),
    # milkman intraday setups that have traded: the study's own rates (milkman-study/v2/out/tab_primary.md, OOS long
    # + short trades). Their decisions' "net +0.000000" is the flattening order after an exit: in the record only
    # mk_vomyivomy ever held opposite lanes at once (10-20)
    ("mk_atrlevelcascade", {"rarity": "CASCADE: 9,548 trades (" + _MILKMAN_OOS + "): about 3 a session",
                            "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    ("mk_daygoldengate", {"rarity": "DGG: 2,131 trades (" + _MILKMAN_OOS + "): about 2 in 3 sessions",
                          "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    ("mk_gapfademomentummirror", {"rarity": "GAP: 1,530 trades (" + _MILKMAN_OOS + "): about 1 in 2 sessions",
                                  "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    ("mk_openingrangebreakout", {"rarity": "ORB: 2,704 trades (" + _MILKMAN_OOS + "): about 4 in 5 sessions",
                                 "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    ("mk_tenminutecompressionrelease", {"rarity": "COMP10: 2,572 trades (" + _MILKMAN_OOS + "): about 3 in 4 sessions",
                                        "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    ("mk_threeminutecompressiondrift", {"rarity": "CDC: 3,594 trades (" + _MILKMAN_OOS + "): about 1 a session",
                                        "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    (("mk_vomyivomy", "mk_vomyivomy_short"),
     {"rarity": "VOMY: 8,235 trades long + short (" + _MILKMAN_OOS + "): about 2.5 a session; one book per side since "
                "roll1 78fd79e5 (its lanes netted on one book on 10-20)",
      "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    (("mk_weekdayopentocloseproxy", "mk_weekdayopentocloseproxy_short"),
     {"rarity": "DOW: Monday's open to close on the index set (8,856 OOS trades a side over 14 instruments since 2013): "
                "every Monday it is quoted; one book per side since the owner's split of 2026-10-19",
      "owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
    ("mk_*", {"owner": "fix2 MAC-10 (f7e7b37e: debit balances carry the desk's margin rate)"}),
]


def note_for(sid, notes=None):
    for pats, n in (NOTES if notes is None else notes):
        for p in (pats if isinstance(pats, (list, tuple)) else (pats,)):
            if fnmatch.fnmatchcase(sid, p):
                return n
    return None


# -- reading the record ------------------------------------------------------------------------------------------
def ledger_records(state_dir):
    """every record of the ledger: state/ledger.jsonl when present (the host), else the record's segments"""
    whole = os.path.join(state_dir, "ledger.jsonl")
    paths = []
    if os.path.exists(whole):
        paths = [whole]
    else:
        seg = os.path.join(state_dir, "ledger")
        man = read_json(os.path.join(seg, "manifest.json"), {}) or {}
        paths = [os.path.join(seg, s["name"]) for s in man.get("segments") or ()]
        if man.get("open"):
            paths.append(os.path.join(seg, man["open"]["name"]))
    for p in paths:
        if not os.path.exists(p):
            continue
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue                      # a torn last line: the records before it stand


def _ts(text):
    try:
        return datetime.fromisoformat(str(text)).timestamp()
    except (TypeError, ValueError):
        return None


def _intents(r, n=40):
    return [{k: i.get(k) for k in ("kind", "symbol", "side", "reason")} for i in (r.get("intents") or [])[:n]]


def scan(records):
    """one pass over the ledger -> pass times and per-sleeve facts (the last signals record, the last one that ordered
    something, the last observation, every sleeve_error with its pass time, the book fills and the last one's time)"""
    passes = []                                   # pass clock (pass_end.summary.at), ascending
    sig_last, act_last, obs_last, fill_last = {}, {}, {}, {}
    sig_n, obs_n, fill_n = Counter(), Counter(), Counter()
    errors = defaultdict(list)                    # sid -> [(at, error, seq)]
    at = None
    n = 0
    for r in records:
        n += 1
        k = r.get("kind")
        if k == "pass_start":
            at = _ts(r.get("at"))
            continue
        if k == "pass_end":
            t = _ts((r.get("summary") or {}).get("at"))
            if t is not None:
                passes.append(t)
            continue
        sid = r.get("sleeve")
        if k == "signals" and sid:
            sig_n[sid] += 1
            rec = {"at": at, "seq": r.get("seq"), "n": r.get("n"), "intents": _intents(r)}
            sig_last[sid] = rec
            if any(i.get("kind") in ACTIONABLE for i in r.get("intents") or ()):
                act_last[sid] = rec
        elif k == "observation" and sid:
            obs_n[sid] += 1
            obs_last[sid] = {"at": at, "seq": r.get("seq"), "symbol": r.get("symbol"),
                             "reason": str(r.get("reason") or "")[:300]}
        elif k == "sleeve_error" and sid:
            errors[sid].append((at, str(r.get("error") or "")[:300], r.get("seq")))
        elif k == "book_fill" and sid:
            fill_n[sid] += 1
            t = r.get("at") if isinstance(r.get("at"), (int, float)) else at
            if t is not None and t >= fill_last.get(sid, (0.0,))[0]:
                fill_last[sid] = (float(t), r.get("seq"))
    passes.sort()
    return {"records": n, "passes": passes, "sig_last": sig_last, "act_last": act_last, "obs_last": obs_last,
            "sig_n": sig_n, "obs_n": obs_n, "errors": errors, "fill_n": fill_n, "fill_last": fill_last}


def manifest_rows(root):
    rows, line_no = {}, {}
    p = os.path.join(root, "config", "manifest", "sleeves.jsonl")
    if os.path.exists(p):
        with open(p) as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    r = json.loads(line)
                    rows[r["sleeve_id"]] = r
                    line_no[r["sleeve_id"]] = i
    return rows, line_no


def registry_configs():
    """{sleeve_id: {schedule, cadence_s, status, module}} of every sleeve the registry's families define (disabled rows
    too), and "__errors__": {family: error} for a family that cannot load; importing a family reads code and pinned
    files only"""
    from .. import registry
    out = {}
    for mod in registry.FAMILIES:
        try:
            m = importlib.import_module(mod)
            for s in m.sleeves():
                c = s.CONFIG
                out[c.sleeve_id] = {"schedule": c.schedule, "cadence_s": float(c.cadence_s), "status": c.status,
                                    "module": mod.rsplit(".", 1)[-1]}
        except Exception as e:                    # a family that cannot load: its rows say so
            out.setdefault("__errors__", {})[mod] = f"{type(e).__name__}: {str(e)[:160]}"
    return out


# -- schedule facts ----------------------------------------------------------------------------------------------
def first_missed_due(schedule, cadence, last, passes):
    """the first pass after `last` at which the engine's due rule (cadence elapsed and window open, or an anchor) held:
    the sleeve should have been evaluated there and was not (last_run moves only when signal() returns)"""
    i = bisect.bisect_right(passes, last + 1e-6)
    anchored = "!" in (schedule or "")
    for t in passes[i:]:
        if (t - last >= cadence and is_open(schedule, t)) or (anchored and anchor_due(schedule, last, t)):
            return t
    return None


def windows_without_pass(schedule, cadence, last, passes, end):
    """[(first, last) sampled second] of window occurrences that opened and closed between two consecutive passes
    after `last` (closed at both passes, open between them) while the sleeve was due by cadence, and of anchored
    windows likewise whatever the cadence: a window no pass ran in. A window the sleeve was evaluated in earlier, whose
    last seconds had no pass, is not one: the sleeve ran in that occurrence."""
    out = []
    i = bisect.bisect_right(passes, last + 1e-6)
    seq = [last] + passes[i:]
    if seq[-1] < end:
        seq.append(end)
    alts = [a.strip() for a in (schedule or "always").split(",")]
    anchors = [a for a in alts if a.startswith("!")]
    for a, b in zip(seq, seq[1:]):
        if b - a <= GAP_S:
            continue
        whole = not is_open(schedule, a) and not is_open(schedule, b)
        shut = [alt for alt in anchors if not _alt_open(alt, a) and not _alt_open(alt, b)]
        if not whole and not shut:
            continue
        hit = None
        t = a + GAP_STEP_S
        while t < b:
            if (whole and t - last >= cadence and is_open(schedule, t)) or any(_alt_open(x, t) for x in shut):
                hit = (hit[0], t) if hit else (t, t)
            t += GAP_STEP_S
        if hit:
            out.append(hit)
    return out


# -- positions -----------------------------------------------------------------------------------------------------
def open_positions(book):
    return {i: p for i, p in ((book or {}).get("positions") or {}).items() if abs(float(p.get("qty") or 0.0)) > DUST}


def _when(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        x = float(v)
        return x / 1000.0 if x > 1e12 else x
    s = str(v).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):            # a session date: due by that session's close
        d = datetime.fromisoformat(s).date()
        return datetime.combine(d, dtime(16, 0), ET).timestamp()
    t = _ts(s.replace("Z", "+00:00"))
    if t is None:
        return None
    if datetime.fromisoformat(s.replace("Z", "+00:00")).tzinfo is None:
        return None                                      # a naive time names no instant
    return t


def overdue_exits(book, now):
    """[(inst, field, due)] of open positions whose planned exit (time_exit_at, exit_at, exit_due_date in the
    position's meta) passed more than EXIT_GRACE_S ago and more than one session ago"""
    out = []
    for inst, p in open_positions(book).items():
        pm = ((p.get("meta") or {}).get("position_meta") or {})
        if not isinstance(pm, dict):
            continue
        for k in ("time_exit_at", "exit_at", "exit_due_date"):
            due = _when(pm.get(k))
            if due is not None and now - due > EXIT_GRACE_S and _sessions_between(due, now) >= 1:
                out.append((inst, k, pm.get(k)))
    return out


def _sessions_since(first_day, t):
    """NYSE sessions from first_day through the ET date of t"""
    try:
        d = datetime.fromisoformat(str(first_day)).date()
    except ValueError:
        return None
    n, end = 0, cal._as_date(float(t))
    while d <= end:
        n += cal.is_trading_day(d)
        d = d.fromordinal(d.toordinal() + 1)
    return n


def _sessions_between(a, b):
    """NYSE sessions that opened after a and closed at or before b"""
    n = 0
    d = cal._as_date(a)
    end = cal._as_date(b)
    while d <= end:
        if cal.is_trading_day(d) and cal.session_open(d) > a and cal.session_close(d) <= b:
            n += 1
        d = d.fromordinal(d.toordinal() + 1)
    return n


def state_error(state, since=None):
    """the error a sleeve keeps in its own state: its log's last entry carries one. With `since` (epoch seconds), an
    entry stamped before it is history, not the sleeve's present: qr_spectral_echo_drift's log ended in a 10-23 error and
    the sleeve has read its tape every pass since, yet the row stayed BROKEN on a four-day-old line"""
    log = (state or {}).get("log") if isinstance(state, dict) else None
    if isinstance(log, list) and log and isinstance(log[-1], dict) and log[-1].get("error"):
        e = log[-1]
        at = e.get("at")
        at = at if isinstance(at, (int, float)) else _ts(at)
        if since is not None and at is not None and at < since:
            return None
        return {"at": e.get("at"), "decision": e.get("decision"), "error": str(e.get("error"))[:200],
                "n_last": sum(1 for x in log if isinstance(x, dict) and x.get("error")), "of": len(log)}
    return None


# the sleeve-private stamps that name the last session a daily decision step ran (top level or under "meta"); a
# stamp sessions behind the sleeve's last evaluated session means its decision step returned early on every pass
# since, without a record (2026-10-20..23: griffith_simple_daily_trend "observed", griffith_momentum_pead "day")
DAILY_STAMPS = ("observed", "scanned", "last_rank_date", "funnel_session", "day")
STAMP_LAG_SESSIONS = 2
STAMP_STEP_S = 300.0


def _window_passed(schedule, d, until):
    """the sleeve's schedule opened on the ET day d, and, when `until` falls inside d, closed again before it: a
    session whose decision step should have stamped it by `until`"""
    t = datetime.combine(d, dtime(0, 0), ET).timestamp()
    end = t + 86400
    whole = end <= until
    opened = False
    while t < min(end, until):
        if is_open(schedule, t):
            if whole:
                return True
            opened = True
        elif opened:
            return True
        t += STAMP_STEP_S
    return False


def stale_daily_stamp(state, last_eval, schedule=None):
    """(key, stamp, sessions behind) of a daily stamp at least STAMP_LAG_SESSIONS sessions behind the sleeve's last
    evaluation, counting the NYSE sessions after the stamp on which its schedule's window opened (and, on the day of
    the evaluation, closed again before it): a weekly ranker's Friday stamp is not behind on Wednesday, nor an
    after-close step's stamp before the close. None when every stamp is current or there is none."""
    if not isinstance(state, dict) or not last_eval:
        return None
    until = float(last_eval)
    sess = cal._as_date(until)
    places = [state] + ([state["meta"]] if isinstance(state.get("meta"), dict) else [])
    for doc in places:
        for k in DAILY_STAMPS:
            v = doc.get(k)
            if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                continue
            x = datetime.fromisoformat(v).date()
            behind = 0
            while x < sess:
                x = x.fromordinal(x.toordinal() + 1)
                if cal.is_trading_day(x) and (schedule is None or _window_passed(schedule, x, until)):
                    behind += 1
            if behind >= STAMP_LAG_SESSIONS:
                return k, v, behind
    return None


# -- classification ------------------------------------------------------------------------------------------------
def _iso(t):
    return datetime.fromtimestamp(float(t), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def _session_start(t):
    """00:00 ET of the ET date of t"""
    d = datetime.fromtimestamp(float(t), tz=ET).date()
    return datetime.combine(d, dtime(0, 0), ET).timestamp()


def _decision_text(rec, n=3):
    if not rec:
        return None
    parts = []
    for i in rec["intents"][:n]:
        side = f" {i.get('side')}" if i.get("side") else ""
        parts.append(f"{i.get('kind')} {i.get('symbol')}{side}: {str(i.get('reason') or '')[:140]}")
    more = len(rec["intents"]) - n
    return "; ".join(parts) + (f"; (+{more} more)" if more > 0 else "")


def classify_row(sid, ctx, notes=None):
    """one report row -> {class, reason, evidence[], ...}; ctx holds the record's documents and the ledger scan"""
    man, lines = ctx["manifest"], ctx["manifest_lines"]
    cfgs, rep, desk, books, sc = ctx["configs"], ctx["report"], ctx["desk"], ctx["books"], ctx["scan"]
    T = float(desk.get("last_pass") or 0)
    row = rep.get(sid) or {}
    m = man.get(sid) or {}
    c = cfgs.get(sid)
    last = float((desk.get("last_run") or {}).get(sid) or 0)
    book = (books or {}).get(sid) or {}
    pos = open_positions(book)
    n = note_for(sid, notes)
    ev = []
    # when it last traded: the ledger's last book_fill, the book's closed trades, the report's last_trade_at (the
    # report can be days old: 2026-10-26 its rows were of 10-23 20:45Z while the crypto books traded all weekend)
    filled = sc["fill_last"].get(sid)
    closed = [float(t["closed_at"]) for t in book.get("trades") or () if t.get("closed_at")]
    when = [x for x in [filled[0] if filled else None, row.get("last_trade_at")] + closed if x]
    fills = int(book["n_fills"]) if isinstance(book.get("n_fills"), (int, float)) else int(row.get("fills") or 0)
    out = {"sleeve_id": sid, "family": m.get("family") or row.get("family") or sid.split("_")[0],
           "module": (c or {}).get("module"), "kind": m.get("kind"), "schedule": (c or {}).get("schedule"),
           "cadence_s": (c or {}).get("cadence_s"), "last_eval": _iso(last), "fills": fills,
           "trades": len(book["trades"]) if isinstance(book.get("trades"), list) else int(row.get("trades") or 0),
           "open_positions": len(pos), "first_day": row.get("first_day"),
           "last_trade": _iso(max(when)) if when else f"never since {row.get('first_day') or 'install'}",
           "owner": "", "cause": "", "rarity": ""}
    sig = sc["sig_last"].get(sid)
    act = sc["act_last"].get(sid)
    obs = sc["obs_last"].get(sid)
    out["last_decision_at"] = _iso(sig["at"]) if sig else None
    out["last_decision"] = _decision_text(sig) if sig else "no intent recorded in the ledger"
    out["signals_records"] = int(sc["sig_n"].get(sid, 0))
    out["observations"] = int(sc["obs_n"].get(sid, 0))

    def done(cls, reason):
        out["class"], out["reason"], out["evidence"] = cls, reason, ev
        if n:
            out["owner"] = out["owner"] or n.get("owner", "")
            out["cause"] = out["cause"] or n.get("cause", "")
            out["rarity"] = out["rarity"] or n.get("rarity", "")
        if cls == "WAITING" and not out["rarity"]:          # no rule or research rate: its own forward record's
            out["rarity"] = (f"its own forward record: {out['trades']} closed trades, {out['fills']} fills in "
                             f"{_sessions_since(row.get('first_day'), T)} sessions since {row.get('first_day')}")
        return out

    # OFF: the owner's manifest decision, or nothing the registry loads
    if m.get("status") == "disabled":
        d = m.get("disabled") or {}
        ev.append(f"config/manifest/sleeves.jsonl:{lines.get(sid)} status disabled by {d.get('by')} on {d.get('on')}: "
                  f"{str(d.get('why') or '')[:160]}")
        return done("OFF", f"owner-disabled {d.get('on')}: {str(d.get('why') or d.get('rule') or '')[:120]}")
    if c is None:
        ev.append("registry: no family defines this sleeve id (not loaded)")
        return done("OFF", "not loaded by the registry")
    if c.get("status") == "parked":
        ev.append(f"registry config status parked ({c.get('module')})")
        return done("OFF", "parked in its config")
    if n and n.get("cls") == "OFF":
        ev.append(f"note: {n.get('cause')}")
        if last:
            ev.append(f"state/desk.json last_run[{sid}] = {_iso(last)}")
        return done("OFF", n.get("reason") or "by design it never trades")

    # evaluation: when it last ran, whether a due pass or a whole window went without it
    if not last:
        ev.append(f"state/desk.json: no last_run for {sid}")
        return done("BROKEN", "never evaluated")
    ev.append(f"state/desk.json last_run[{sid}] = {_iso(last)} (record clock {_iso(T)})")
    missed = first_missed_due(c["schedule"], c["cadence_s"], last, sc["passes"])
    errs = sc["errors"].get(sid) or []
    since = min(_session_start(last), last - 86400)
    recent = [e for e in errs if e[0] is not None and e[0] >= since]
    if missed is not None:
        after = [e for e in errs if e[0] is not None and e[0] >= missed]
        if after:
            ev.append(f"ledger seq {after[-1][2]} sleeve_error at {_iso(after[-1][0])}: {after[-1][1][:160]}")
            ev.append(f"{len(after)} sleeve_error records since the due pass at {_iso(missed)}")
            return done("BROKEN", f"errors on every due pass since {_iso(missed)}: {after[-1][1][:100]}")
        ev.append(f"ledger: pass at {_iso(missed)} had it due ({c['schedule']}, cadence {c['cadence_s']:.0f} s) "
                  f"and it was not evaluated")
        return done("BROKEN", f"due at {_iso(missed)} and not evaluated")
    gaps = windows_without_pass(c["schedule"], c["cadence_s"], last, sc["passes"], T)
    if gaps:
        g = gaps[-1]
        ev.append(f"ledger pass times: no pass between {_iso(g[0])} and {_iso(g[1])} while its window was open "
                  f"({c['schedule']})")
        return done("BROKEN", f"a window no pass ran in ({_iso(g[0])})")
    if recent:
        e = recent[-1]
        ev.append(f"ledger seq {e[2]} sleeve_error at {_iso(e[0])}: {e[1][:160]} ({len(recent)} in its last session)")
        return done("BROKEN", f"sleeve_error in its last session: {e[1][:100]}")
    se = state_error(ctx["states"].get(sid), min(_session_start(last), last - 86400))
    if se:
        ev.append(f"state/sleeves/{sid}.json log[-1] {se['decision']}: {se['error']} ({se['n_last']} of {se['of']} "
                  f"log entries carry an error)")
        return done("BROKEN", f"its state records an error: {se['error'][:100]}")
    stamp = stale_daily_stamp(ctx["states"].get(sid), last, c.get("schedule"))
    if stamp:
        k, v, behind = stamp
        ev.append(f"state/sleeves/{sid}.json {k} = {v}: {behind} sessions behind its last evaluation {_iso(last)}")
        return done("BROKEN", f"its daily step has not run since {v} ({k}; {behind} sessions skipped silently)")
    od = overdue_exits(book, T)
    if od:
        inst, k, due = od[0]
        ev.append(f"state/books.json {sid}.positions[{inst}].meta.position_meta.{k} = {due}, still open at {_iso(T)}")
        return done("BROKEN", f"planned exit overdue: {inst} {k} {due}")

    # its decision of record: the last signals record, when it belongs to the sleeve's last evaluated session
    cur = sig is not None and sig["at"] is not None and sig["at"] >= min(_session_start(last), last - 86400)
    if sig:
        ev.append(f"ledger seq {sig['seq']} signals at {_iso(sig['at'])}: {_decision_text(sig, 2)[:300]}")
    if obs and (not sig or (obs["at"] or 0) > (sig["at"] or 0)):
        ev.append(f"ledger seq {obs['seq']} observation at {_iso(obs['at'])}: {obs['reason'][:200]}")
    lb = _lane_block(ctx["states"].get(sid), last)
    if lb and not pos:                                    # its own record of its block outranks any note
        ev.append(f"state/sleeves/{sid}.json blocked_on = {lb[0][:220]}")
        out["cause"] = f"input blocker: {lb[1][:160]}"
        return done("BLOCKED", f"its own record names its missing input: {lb[1][:100]}")
    st_ = ctx["states"].get(sid)
    if n and n.get("cls") == "BROKEN" and _note_applies(n, sig, cur, pos, st_, T):
        ev.append(f"note: {n.get('cause')}")
        return done("BROKEN", n.get("reason") or n.get("cause", "")[:120])
    kinds = Counter(i.get("kind") for i in (sig or {}).get("intents") or ())
    acting_now = cur and any(kinds.get(k) for k in ACTIONABLE)
    blockers = [(reason_kind(i.get("reason")), i) for i in (sig or {}).get("intents") or () if i.get("kind") == "signal"]
    inputs = [i for k, i in blockers if k == "input"]
    if cur and not acting_now and inputs and len(inputs) == len([1 for k, _ in blockers if k]) and not pos:
        first = str(inputs[0].get("reason"))
        if not (n and n.get("cls") == "WAITING" and _note_applies(n, sig, cur, pos, st_, T)):
            out["cause"] = f"input blocker: {first[:160]}"
            return done("BLOCKED", f"its decision of record is an input blocker: {first[:100]}")
    if n and n.get("cls") == "BLOCKED" and _note_applies(n, sig, cur, pos, st_, T):
        ev.append(f"note: {n.get('cause')}")
        return done("BLOCKED", n.get("reason") or n.get("cause", "")[:120])

    # acting or waiting (a contract that expired into its settlement is not a trade the sleeve decided)
    traded = [float(t["closed_at"]) for t in book.get("trades") or () if t.get("closed_at")
              and not str(t.get("reason") or "").startswith("expired ")]
    fills_today = bool(traded) and max(traded) >= _session_start(last)
    if pos or acting_now or fills_today:
        bits = []
        if pos:
            bits.append(f"holds {len(pos)} position(s)")
            first = sorted(pos)[0]
            ev.append(f"state/books.json {sid}.positions: {len(pos)} open, e.g. {first} qty "
                      f"{float(pos[first].get('qty') or 0):g}")
        if acting_now:
            bits.append(f"decided {', '.join(f'{v} {k}' for k, v in sorted(kinds.items()) if k in ACTIONABLE)}")
        if fills_today:
            bits.append(f"closed a trade {_iso(max(traded))}")
            ev.append(f"state/books.json {sid}.trades: last closed {_iso(max(traded))}")
        return done("FIRING", "; ".join(bits))
    if act:
        ev.append(f"ledger seq {act['seq']} last order-bearing decision at {_iso(act['at'])}: "
                  f"{_decision_text(act, 1)[:200]}")
    ev.append(f"state/books.json {sid}.n_fills {out['fills']}; last trade {out['last_trade']}"
              + (f" (ledger seq {filled[1]} book_fill)" if filled and _iso(filled[0]) == out["last_trade"] else ""))
    # the engine's own record of an evaluation that decided nothing (desk.json `waiting`, MAC-04), when it has one
    wt = (desk.get("waiting") or {}).get(sid) if isinstance(desk.get("waiting"), dict) else None
    if isinstance(wt, dict) and wt.get("at"):
        miss = str(wt.get("miss") or "")
        ev.append(f"state/desk.json waiting[{sid}]: {wt.get('why')} at {_iso(wt['at'])}"
                  + (f"; its nearest miss: {miss[:200]}" if miss else ""))
    else:
        wt, miss = None, ""
    if cur and sig:
        return done("WAITING", f"evaluated on schedule; its decision of record declined: "
                               f"{str(sig['intents'][0].get('reason') if sig['intents'] else '')[:100]}")
    if wt and float(wt["at"]) >= float((sig or {}).get("at") or 0):
        return done("WAITING", f"evaluated on schedule; {wt.get('why')} at {_iso(wt['at'])}"
                               + (f" (its nearest miss: {miss[:100]})" if miss else ""))
    return done("WAITING", SILENT if not sig else "evaluated on schedule; flat, no intent since its last decision")


def _note_applies(n, sig, cur, pos, state=None, T=None):
    """a note's class applies while the record still shows what it was written for: only_if "silent" (no decision in
    its last session), "flat" (no open position), "unrecorded" (the sleeve's state does not record its own block yet:
    no blocked_on key), any of them listed together; "until" (ISO time): only on a record whose clock is before it"""
    until = _ts(str(n.get("until") or "").replace("Z", "+00:00")) if n.get("until") else None
    if until is not None and T is not None and float(T) >= until:
        return False
    only = n.get("only_if")
    for cond in ((only,) if isinstance(only, str) else tuple(only or ())):
        if cond == "silent" and cur:
            return False
        if cond == "flat" and pos:
            return False
        if cond == "unrecorded" and isinstance(state, dict) and "blocked_on" in state:
            return False
    return True


def _lane_block(state, last):
    """(blocked_on, the missing piece) when the sleeve's state records its own block (Lazarus FEED-02: blocked_on =
    "<session>|<why>", written each pass) in the ET session of its last evaluation and the piece is an input; else None"""
    bo = state.get("blocked_on") if isinstance(state, dict) else None
    if not isinstance(bo, str) or "|" not in bo or not last:
        return None
    day, why = bo.split("|", 1)
    if day != cal._as_date(float(last)).isoformat() or reason_kind("blocked_data: " + why) != "input":
        return None
    return bo, why


def build(state_dir, root, configs=None, notes=None, records=None):
    """the roll call of the record in state_dir against the checkout at root -> the rollcall document"""
    rep = (read_json(os.path.join(state_dir, "report.json"), {}) or {}).get("sleeves") or {}
    desk = read_json(os.path.join(state_dir, "desk.json"), {}) or {}
    books = read_json(os.path.join(state_dir, "books.json"), {}) or {}
    books = books.get("books", books) if isinstance(books, dict) else {}
    states = {}
    sd = os.path.join(state_dir, "sleeves")
    if os.path.isdir(sd):
        for f in os.listdir(sd):
            if f.endswith(".json"):
                try:
                    states[f[:-5]] = read_json(os.path.join(sd, f), {})
                except ValueError:
                    states[f[:-5]] = {}
    man, lines = manifest_rows(root)
    cfgs = registry_configs() if configs is None else configs
    sc = scan(ledger_records(state_dir) if records is None else records)
    ctx = {"manifest": man, "manifest_lines": lines, "configs": cfgs, "report": rep, "desk": desk, "books": books,
           "states": states, "scan": sc}
    rows = [classify_row(sid, ctx, notes) for sid in sorted(rep)]
    T = float(desk.get("last_pass") or 0)
    counts = Counter(r["class"] for r in rows)
    fam = defaultdict(Counter)
    for r in rows:
        fam[r["family"]][r["class"]] += 1
    hb = read_json(os.path.join(state_dir, "heartbeat.json"), {}) or {}
    not_on = [{"sleeve_id": s, "status": r.get("status"), "family": r.get("family"),
               "loaded": s in cfgs, "schedule": (cfgs.get(s) or {}).get("schedule")}
              for s, r in sorted(man.items()) if s not in rep]
    return {"at": _iso(T), "record": {"last_pass": _iso(T), "passes": desk.get("passes"),
                                      "code": (hb.get("code") or {}).get("commit"),
                                      "report_generated_at": (read_json(os.path.join(state_dir, "report.json"), {})
                                                              or {}).get("generated_at"),
                                      "ledger_records": sc["records"]},
            "corpus": {"report_rows": len(rep), "manifest_rows": len(man), "not_on_record": not_on},
            "counts": {k: counts.get(k, 0) for k in CLASSES},
            "by_family": {f: {k: v.get(k, 0) for k in CLASSES} for f, v in sorted(fam.items())},
            "registry_errors": (cfgs or {}).get("__errors__", {}), "rows": rows}


# -- outputs -------------------------------------------------------------------------------------------------------
CSV_FIELDS = ("sleeve_id", "family", "module", "class", "reason", "cause", "owner", "rarity", "last_eval",
              "last_decision_at", "last_decision", "last_trade", "fills", "open_positions", "schedule", "evidence")


def to_csv(doc):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore")
    w.writeheader()
    for r in doc["rows"]:
        w.writerow(dict(r, evidence=" | ".join(r.get("evidence") or ())))
    return buf.getvalue()


def to_markdown(doc, limit_waiting=None):
    c = doc["counts"]
    lines = [f"# Roll call, record of {doc['at']}", "",
             f"{doc['corpus']['report_rows']} sleeve rows on the record (state/report.json); code "
             f"{doc['record'].get('code')}; {doc['record'].get('ledger_records')} ledger records read.", "",
             "| class | rows |", "|---|---:|"]
    lines += [f"| {k} | {c.get(k, 0)} |" for k in CLASSES]
    lines += ["", "## By family", "", "| family | " + " | ".join(CLASSES) + " |",
              "|---|" + "---:|" * len(CLASSES)]
    for f, v in doc["by_family"].items():
        lines.append(f"| {f} | " + " | ".join(str(v.get(k, 0)) for k in CLASSES) + " |")
    for cls in ("BROKEN", "BLOCKED"):
        rows = [r for r in doc["rows"] if r["class"] == cls]
        lines += ["", f"## {cls} ({len(rows)})", "", "| sleeve | reason | cause | owner |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['sleeve_id']} | {_md(r['reason'])} | {_md(r.get('cause'))} | {_md(r.get('owner'))} |")
    rows = [r for r in doc["rows"] if r["class"] == "WAITING"]
    lines += ["", f"## WAITING ({len(rows)})", "", "| sleeve | last eval | last trade | rarity / reason |",
              "|---|---|---|---|"]
    for r in rows[:limit_waiting]:
        lines.append(f"| {r['sleeve_id']} | {r['last_eval']} | {r['last_trade']} | "
                     f"{_md(r.get('rarity') or r['reason'])} |")
    if doc["corpus"]["not_on_record"]:
        lines += ["", "## Manifest rows not on the record", ""]
        for x in doc["corpus"]["not_on_record"]:
            lines.append(f"- {x['sleeve_id']} ({x['status']}, {x['family']}, schedule {x.get('schedule')})")
    return "\n".join(lines) + "\n"


def _md(s):
    return str(s or "").replace("|", "/").replace("\n", " ")[:220]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--state", required=True, help="a state directory (the host's state/ or a record's)")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    help="the checkout whose config/manifest/sleeves.jsonl is read (default: this one)")
    ap.add_argument("--json", help="write the rollcall document here (default: <state>/rollcall.json)")
    ap.add_argument("--md", help="write the Markdown summary here (default: <state>/rollcall.md)")
    ap.add_argument("--csv", help="write one CSV row a sleeve here")
    a = ap.parse_args(argv)
    doc = build(a.state, a.root)
    write_json_atomic(a.json or os.path.join(a.state, "rollcall.json"), doc, indent=1)
    with open(a.md or os.path.join(a.state, "rollcall.md"), "w") as f:
        f.write(to_markdown(doc))
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            f.write(to_csv(doc))
    print(json.dumps({"at": doc["at"], "counts": doc["counts"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
