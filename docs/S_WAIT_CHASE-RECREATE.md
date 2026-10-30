# s_wait_chase - Recreation Package

Status: UNRESOLVED in the ALL-SLEEVES accounting; this package holds the best evidence on file and does not claim a complete algorithm.

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "s_wait_chase", type other, algorithm grade FULL from the lz_engine config (entry/exit/sizing), and UNRESOLVED: "singleton with no Test entry and no recorded strategy description; would be settled by the sleeve module docstring or a catalog description". The accounting's universe, asset class, timeframe and creator fields are "not recorded in consulted sources". Status history: dead (md2_lz_engine). Classification evidence on the accounting entry: "Classification 2026-10-30: other (config evidence): lz_engine config in accounting shows only a fear_day capped-limit execution policy; the upstream sleeve feed fire that it waits on is not recorded"
- Config record found in Test: `packages/grokbot/rl64/lz_engine/config/sleeves.json` row id `s_wait_chase`, label "CHASE (WAIT)", kind 1w, enabled False, state dead, account TEST, broker_account TEST_MWJW. Status text: "WAIT placeholder" (a WAIT placeholder in the source config). Flags: ["placeholder/index: WAIT placeholder"] Research on the entry: ["DESK_INTEGRATION/DESK_PLAN.md section 6 WAIT: conflicts with the live near-52w-high avoid"]
- The same config row is also present in `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and in `sleeves/lazarus/vendor/lazarus/sleeves.json` (in the vendor copy the exit rule text reads "no stop / time exit" where the rl64 copy reads "15% disaster stop (L-130) / time exit"; the executable WAIT_SPEC rule below, which is the code that runs this lane in this repo, records no stop).
- Executable code found in Test (read and confirmed to carry this exact lane id): `sleeves/lazarus/lazarus.py` (WAIT_SPEC entry for `s_wait_chase`, the wait_lane resolver, LIVE_RULES and live_row) and the WAIT feed producer module in `sleeves/lazarus/` whose filename carries a token excluded under the repo rule and is therefore not reproduced here (its header states it is the producer of the six WAIT lanes, on the rules the Research Lab froze for them, vendored specs under DESK_INTEGRATION/sleeve_specs). Its per-lane rule text is quoted in the Full algorithm section.
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree plus content reads of the files above); dwj9ddyvf6-hub/Silicon (recursive tree; no path named for this id); dwj9ddyvf6-hub/quant-research-backup (recursive tree; no path named for this id); dwj9ddyvf6-hub/Midna (recursive tree; no path named for this id).

## What this strategy is

One of the six Lazarus WAIT lanes: a placeholder row in the original sleeve_feed config (enabled false, state dead, budget 0, max_slots 0) that this repo's Lazarus runtime port runs on its intended frozen Research Lab spec instead. Label: "CHASE (WAIT)". Research note on the config entry: "DESK_PLAN.md section 6 WAIT: conflicts with the live near-52w-high avoid". Accounting description: "No strategy description recorded in consulted sources."

## Full algorithm

In evaluation order, from the code in this repo:

1. Fire production (the WAIT feed producer, `sleeves/lazarus/`): the lane's rule is: a tracker 1W Cyan fire whose mom126 rank at t (the last session <= the fire Friday) against the liquid cross-section LQ is >= 0.90 (mom126 = Cf[t]/Cf[t-126]-1, searchsorted right / n, >= 50 LQ names; LQ = bar present, dv20 >= $0.5M (UC rule), SIC operating company and not an ETF, close >= $5, dv20 >= $1M; params and lists from paper_families_v1_frozen.json) and Cf[t] / max(Cf over the last 63 sessions, min 40 periods) - 1 > -0.05.
2. Fire file: the producer writes `shadow/paper_sleeve/live/wait_fires_v1.json` in the sleeve_fires_v1 fire schema. A lane whose input is missing in a run keeps its fires of the previous file when the fire day is inside the 5-session window and the evidence is at most 80 hours old (carry-forward, stamped carried_from), and the lane's status reads "input missing" with what is missing; a lane whose input is present is recomputed.
3. Lane resolution (`sleeves/lazarus/lazarus.py`): LIVE_RULES maps `s_wait_chase` to wait_lane, which takes the wait feed's fires for this lane that are tradeable, normalises them, and attaches each fire's own entry price cap (limit_cap).
4. WAIT_SPEC for this lane in that module: kind="1w", unit="1w", hold_from="plan", H=52*5 sessions; rule text: exit W52 from the 1W fire week; no stop; entry at the next open.
5. live_row sizing: the source row is sized at zero (budget_usd 0, max_slots 0), so the lane takes the paper-test sizing: K = min(20, ceil(20 x H / 126)) = 20 positions of $1,000, i.e. budget_usd 20000, max_slots 20, position_usd 1000, global_slot_usd 1000. The config row's other sizing values stand: cap_pct_of_dv20 1.0, min_slot_fraction 0.9, min_dv20_usd 100000.
6. Entry mechanics of the runtime port (the module's header, which governs all its lanes): fires are deduplicated by key and a key already decided is skipped; the lane cap counts open plus working entries; a fire of a closed day waits; entry triggers from the open of its research entry bar for max_delay_minutes (65 in the config entry); the capped DAY limit is live reference x (1 + limit_buffer_pct 1.0%), capped at fire close x (1 + limit_band_pct 5.0%); size is the slot dollars subject to the dv20 cap, whole shares and the min_dv20_usd floor on 20-session dollar volume; an unknown live price waits. Named removal in the port: the source config's fear_day desk-wide gate (QQQ and stock red, D+1..D+5 afternoon window, 1.02x no-chase cap) was removed at cutover as a desk-wide doctrine, not this lane's own rule; the lane enters on the ungated next-open path. Both readings are recorded here: the config entry's entry policy (fear_day, max_delay_minutes 65, limit_band_pct 5.0, limit_buffer_pct 1.0, window_sessions 5, no_chase_mult 1.02, stock_red true, qqq_red true, order capped_limit_day) is the source record; the in-repo port's mechanics in this step are the code that runs in this repo.
7. Exit mechanics of the runtime port: the time exit fires at the first pass at or after time_exit_at - 20 minutes (35 minutes on a half-day close), time_exit_at recomputed from the fill session when the lane holds from the fill; a plan stop below 99% sells on the live reference (this lane's plan records no stop, so none fires); exits are one DAY limit at reference x (1 - 1%). For this lane the plan exit is: exit W52 from the 1W fire week; no stop.

## Files in this repo

- This package: `docs/S_WAIT_CHASE-RECREATE.md`
- Code (already in Test; nothing vendored): `sleeves/lazarus/lazarus.py` (WAIT_SPEC, wait_lane, LIVE_RULES, live_row, and the lane pass mechanics), the WAIT feed producer module in `sleeves/lazarus/` (filename not reproduced: it carries a token excluded under the repo rule; it is the 36 KB module beside lazarus.py whose header names the six s_wait_* lanes), and `sleeves/lazarus/vendor/lazarus/` (vendored lane package: signals.py, gate.py, cal.py, data.py and sleeves.json).
- Config (already in Test): `packages/grokbot/rl64/lz_engine/config/sleeves.json`, `packages/grokbot/q07-1w-swing-lz/lz_engine/config/sleeves.json` and `sleeves/lazarus/vendor/lazarus/sleeves.json`, each with a row for this id.
- Related recreation packages in Test: `docs/LZ_WAIT_INTRAWEEK-RECREATE.md` and `docs/LZ_WAIT_R2_DCYAN-RECREATE.md` cover the merged catalog forms of two of the six WAIT lanes (different canonical entries in the accounting).
- Tests in Test: the producer module's header names its rule tests as the desk's WAIT feed test file (tests for the producer's pure rule functions); the Lazarus parity tools are named in the lazarus.py header.
- Accounting: `docs/ALL-SLEEVES.json` / `docs/ALL-SLEEVES.md`, UNRESOLVED section entry for this canonical id.

## Configuration

Full lz_engine config row for `s_wait_chase` in `packages/grokbot/rl64/lz_engine/config/sleeves.json` (verbatim; the source placeholder row, before live_row applies the WAIT_SPEC kind/hold and the paper-test sizing in the Full algorithm section):

```json
{
 "id": "s_wait_chase",
 "account": "TEST",
 "broker_account": "TEST_MWJW",
 "kind": "1w",
 "label": "CHASE (WAIT)",
 "enabled": false,
 "state": "dead",
 "status_text": "WAIT placeholder",
 "source": {
  "producer": "sleeve_feed composer (tracker ledger + alt-data tags)",
  "file": "shadow/paper_sleeve/live/sleeve_fires_v1.json",
  "lane": "s_wait_chase"
 },
 "entry": {
  "policy": "fear_day",
  "max_delay_minutes": 65,
  "limit_band_pct": 5.0,
  "limit_buffer_pct": 1.0,
  "window_sessions": 5,
  "no_chase_mult": 1.02,
  "stock_red": true,
  "qqq_red": true,
  "order": "capped_limit_day"
 },
 "exit": {
  "rule": "the sleeve feed fire's plan (15% disaster stop (L-130) / time exit; hold = n/a)",
  "hold_from": "plan",
  "hold_unit_kind": "1w",
  "stop_pct": null,
  "max_bars": null,
  "rest": null,
  "plan_overrides": []
 },
 "sizing": {
  "budget_usd": 0,
  "max_slots": 0,
  "position_usd": 1000,
  "position_usd_by_class": {},
  "one_share_max_usd": null,
  "cap_pct_of_dv20": 1.0,
  "min_slot_fraction": 0.9,
  "global_slot_usd": 1000,
  "min_dv20_usd": 100000
 },
 "research": [
  "DESK_INTEGRATION/DESK_PLAN.md section 6 WAIT: conflicts with the live near-52w-high avoid"
 ],
 "flags": [
  "placeholder/index: WAIT placeholder"
 ]
}
```

- WAIT_SPEC (code): kind="1w", unit="1w", hold_from="plan", H=52*5 sessions.
- Effective sizing under live_row: max_slots 20, budget_usd 20000, position_usd 1000, global_slot_usd 1000.
- Account TEST (paper), broker_account TEST_MWJW per the config entry. Source row enabled false, state dead; the in-repo port runs the lane live on its intended rule (LIVE_RULES).

## Data inputs

- Wait fires: `shadow/paper_sleeve/live/wait_fires_v1.json` from the WAIT feed producer, lane `s_wait_chase`.
- The producer's upstream inputs for this lane, per its header: the research producers' live outputs under the research root (tracker ledger and, per lane, the engine daily store, the OLX or R2 lab output, or the intraweek detector output).
- Daily bars and live reference prices for entry caps, the dv20 floor and the time exit, per the lazarus.py header.

## Install and run

1. Clone this repository (Test) and check out the main branch; keep the repo directory layout unchanged.
2. Read this doc and the UNRESOLVED accounting entry for `s_wait_chase` in `docs/ALL-SLEEVES.json`.
3. Open `sleeves/lazarus/lazarus.py` and confirm the WAIT_SPEC entry, wait_lane resolver and live_row sizing for `s_wait_chase` match the Full algorithm and Configuration sections.
4. Run the WAIT feed producer so `wait_fires_v1.json` carries this lane's fires, and wire the Lazarus inputs layout the module header describes.
5. Run the Lazarus pass for lane `s_wait_chase`; verify against the Verification section before treating any recreation as faithful.

## Verification

- WAIT_SPEC in `sleeves/lazarus/lazarus.py` contains `s_wait_chase` with the kind, hold and rule in Configuration, LIVE_RULES maps it to wait_lane, and live_row yields max_slots 20 and budget_usd 20000 for its zero-sized source row.
- Behaviour checklist from the recorded algorithm: a fire is produced only when this lane's rule in step 1 holds exactly (every threshold as written); a missing upstream input produces carry-forward inside the 5-session / 80-hour bounds and an "input missing" lane status, never a fabricated fire; entries follow step 6 and exits step 7, with no stop exit for this lane.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
