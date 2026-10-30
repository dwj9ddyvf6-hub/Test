# ausar_pb160: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test docs/ALL-SLEEVES.json, also docs/ALL-SLEEVES.md): canonical name "Saty Research v0.3 - SPY equity paper", type other, family saty_research. Algorithm grade PARTIAL, unresolved false. Accounting sources: ausar_map params/variant, md2 catalog entry/exit/strategy text. Recorded accounting gaps: sizing not recorded in any consulted source.
- Accounting home record: doc: dwj9ddyvf6-hub/Test docs/ALL-SLEEVES.json strategy entry "Saty Research v0.3 - SPY equity paper" (also docs/ALL-SLEEVES.md); no Test catalog entry in the accounting (test_entries empty); algorithm sources per accounting: ausar_map params/variant; md2 catalog entry/exit/strategy text; alias record sources: md2_ausar_map, md2_catalog
- Code search record: Searched, in order: dwj9ddyvf6-hub/Test (recursive tree, 4,430 entries, plus the file reads named in this package); dwj9ddyvf6-hub/Silicon (recursive tree, 21,337 entries); dwj9ddyvf6-hub/quant-research-backup (recursive tree, 47,379 entries); dwj9ddyvf6-hub/Midna (recursive tree, 7,855 entries).
- Code home: dwj9ddyvf6-hub/Test (code already in Test): desk3/aster_batch16.py (kind=saty) + sleeves/aster_saty_research.py + adapters3/aster_saty_research.py + integration/aster_saty_research_adapter.py; algorithm doc docs/ASTER_SATY_RESEARCH-ALGORITHM.md.

## What this strategy is

Saty Research v0.3 - SPY equity paper Type: other; family: saty_research. Universe: not recorded in consulted sources. Asset class: not recorded. Timeframe: not recorded. Creator / source: not recorded. Style evidence in the accounting: Classification 2026-10-30: other (config evidence): Accounting entry for ausar_pb160 read: it only ranks pre formed Saty family candidates by target room, context and age and never states what any family setup does, so the underlying mechanism cannot be read from the available source

## Full algorithm

Accounting record for ausar_pb160, in full as held: Entry: each family keeps its own setup state; eligible candidates are ranked by cost-adjusted target room relative to planned risk, market context, remaining entry room and setup age; the rank orders candidates, it is not a win probability; conflicting equal-ranked directions wait rather than being combined. Exit (truncated in the source record at 'Exits continue while new en...'): keep the structural stop attached to each filled lot; request 50% at the first target, then 25% stages where share size permits; trail the remaining shares by one ATR without loosening the stop; flatten ten minutes before the actual exchange close, including early closes. Sizing: not in the record (the accounting's recorded gap). Data: completed 10-minute SPY bars, separately built hourly context, QQQ and IWM for relative strength and breadth, prior completed daily references, and current two-sided SPY quotes (the accounting's filter text is truncated in the source record).

Identification: that accounting text is the meta-ranker implemented in Test as aster_saty_research (desk3/aster_batch16.py, kind saty; doc docs/ASTER_SATY_RESEARCH-ALGORITHM.md, derived from the code). The authored setup families are ABSENT from the archive (build map S4): the sleeve is a TSV-as-spec meta-ranker shell only, candidates arrive pre-formed via the saty_setups snapshot key, and no v3 producer emits that key, so the sleeve is visibly UNFED / monitor-only in production. Its code rules, in evaluation order:

- Spec: inputs (saty_setups, quotes, bars, positions), cadence_s=600, session rth, slice capital $10,000, paper only, SPY only. Risk per entry 0.25% of the slice ($25 = 1R; halved for mean-reversion families); round-trip cost estimate $0.02 per share; at most 3 entries per day; daily loss limit 2R; open risk limit 2R with a 1R correlated cap (single-instrument book); quote maximum age 5 seconds; entry deadline 15:40 ET; final exit 15:50 ET.
- Exits first; if any exit is emitted the evaluation returns with no entry. No entry at or after 15:40 ET, after 3 entries today, or when the day's realised result is at or below -2R. A fresh two-sided SPY quote is required (timestamp within 5 seconds of now, not in the future) or the evaluation fails closed; price is the quote mid, else the last 10-minute bar close.
- Open risk is summed as qty x |avg_price - invalidation|; a new entry is refused when open risk plus the new 1R would exceed the 1R correlated cap. A candidate must be a dict for SPY, SPY not held, with positive net room at both its planned entry and the current price: net room = (distance to first target - $0.02 per share) / (distance to invalidation), direction-aware.
- Ranking: net room at the current price descending, then context descending, then age_min ascending, then family name. If the best two candidates have opposite directions and equal top rank (within 1e-9), no entry is emitted.
- Sizing: risk $25 (halved for mean-reversion families); executable-risk sizing (ENH switch default ON) qty = int(risk_usd // |current price - invalidation|), with the switch OFF the planned entry price is used; qty < 1 emits nothing; one entry per evaluation. Entries are market, day intents on SPY (buy for long, sell_to_open for short) with family, direction, net room, risk, invalidation and targets in the reason.
- Exits in code: structural invalidation (price at/past the position's invalidation) closes the full position; at or after 15:50 ET any held position is closed in full; an unscaled position reaching its first target is half closed (the full quantity when halving would give 0); a scaled position whose price returns to its entry reference is closed in full (trail to breakeven after scale).

Divergence named, not hidden: the accounting's exit text (50% at the first target, then 25% stages, trail by one ATR) is fuller than the v3 code's exit set above (half at target 1, then breakeven trail, 15:50 flatten, which is ten minutes before a 16:00 close). Where they differ, the code is the truth for the v3 implementation and the accounting text is preserved above as the record of the original book.

## Files in this repo

- This package: docs/AUSAR_PB160-RECREATE.md
- Accounting: docs/ALL-SLEEVES.json, docs/ALL-SLEEVES.md
- Code home (see Provenance): dwj9ddyvf6-hub/Test (code already in Test): desk3/aster_batch16.py (kind=saty) + sleeves/aster_saty_research.py + adapters3/aster_saty_research.py + integration/aster_saty_research_adapter.py; algorithm doc docs/ASTER_SATY_RESEARCH-ALGORITHM.md

## Configuration

SPY only (single-instrument book); slice $10,000; cadence 600 s; session rth; paper only. Risk 0.25% of slice per entry (halved for mean-reversion families); at most 3 entries per day; daily loss limit 2R; open risk limit 2R, correlated cap 1R. Accounting status: blocked (md2_catalog), present in roster (md2_ausar_map). Universe, asset class and timeframe beyond SPY / 10-minute bars are not in the record in the accounting entry itself.

## Data inputs

Declared inputs: saty_setups, quotes, bars, positions. Producers named in desk3/aster_batch16.py: saty_setup_families (60 s freshness, outputs saty_setups), quotes (60 s), bars (900 s), broker_readback (900 s, positions). The batch-16 note states run_live registers only bars and broker_readback today, so saty_setups and quotes have no live producer yet and the sleeve is visibly UNFED rather than fake-fed. Accounting data note: completed 10-minute SPY bars, separately built hourly context, QQQ and IWM for relative strength and breadth, prior completed daily references, current two-sided SPY quotes.

## Install and run

1. Clone the Test repo.
2. Place every file named under Files in this repo at its stated repo path (all are already in Test for a built package; for an INCOMPLETE-CODE package there is no code to place).
3. Wire the producers so the inputs named under Data inputs arrive in the shapes the Full algorithm describes, with the configuration under Configuration.
4. Run the sleeve's entry point named in the code (its sleeves() factory or evaluate(view, ctx) wrapper) on a fixture snapshot that satisfies the entry conditions and confirm the expected intent before any live use.
5. Verify against the Verification section before treating the recreation as faithful.

## Verification

- No entry at/after 15:40 ET, after 3 entries today, at/below -2R for the day, without a two-sided SPY quote within 5 seconds, or when SPY is already held.
- A candidate with non-positive net room at its planned entry or at the current price is refused; equal top-ranked opposite directions produce no entry.
- qty = int($25 // |current price - invalidation|) with the ENH switch ON ($12.50 risk for mean-reversion families); qty < 1 emits nothing; one entry per evaluation.
- Exits: invalidation closes in full, target 1 halves an unscaled position, a scaled position returning to its entry reference closes in full, and everything is flat at/after 15:50 ET; an evaluation emitting an exit emits no entry.
