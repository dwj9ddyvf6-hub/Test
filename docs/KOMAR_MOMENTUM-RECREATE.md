# komar-momentum recreation package

## Provenance

- Sanitized id: komar-momentum. Canonical id: recorded in the owner's private recreation index (see the disclosure below).
- Accounting: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md in this repo, strategy entry "Komar momentum breakout". Algorithm grade in the accounting: PARTIAL. The accounting entry lists its entry, exit and sizing arrays as empty and names those rules as gaps; the Test catalog card for this strategy, which the accounting itself cites as its source (Test catalog entry and variants), does record them, and the Full algorithm below is taken from that card and checked against the code constants in komar.py.
- Catalog status in the card: waiting.
- Code search, in order: Test (found, see Files in this repo), Silicon (no path matching komar, next-support or scanner-book fragments), quant-research-backup (no matching filename; it does hold the older originating desk tree, which is not the code home cited by the card), Midna (no matching filename; same older desk tree copy). Desk source on disk was also checked and holds no komar file.
- Filed under a sanitized filename per the owner's ruling of 2026-10-30. The canonical strategy name in the ALL-SLEEVES accounting carries the originating research family name, which this repo's privacy gate does not allow in file paths or new content. The canonical name and this file's mapping are recorded in the owner's private recreation index. 15 mention(s) of that name in source material were replaced with a neutral placeholder or omitted; no rule, parameter, or code content was changed. The count is the mentions in the ALL-SLEEVES accounting entry plus the Test catalog card for this strategy.

## What this strategy is

Komar momentum breakout. Type: breakout. Style: momentum breakout. Asset class: US equities. Timeframe: 1d. Universe: the 411-stock universe described in the card as Signal Prism US 413 without its two crypto pairs. Creator as recorded: Julian Komar's momentum method, implemented as a public-proxy screen by the originating research desk. In one line from the card: it buys a liquid, trending leader on a stop order at its 20-day high the session after a tight or large-base setup, and sells under the 21-day EMA.

## Full algorithm

Evaluation order, with the strategy's own parameter values:

1. Screen, after the close, requiring at least 80 sessions of bars: close above $5; 50-day dollar volume at least $20M; 20-day ADR at least 4%; at least 70% above the 52-week low; close above the 65-day EMA; the 8-day EMA above the 21-day EMA.
2. Setup, within 18% of the 52-week high. Tight breakout: 10-day range at most 55% of the 40-day range, 5-day volume at most 80% of the 50-day volume, within 6% of the 20-day high. Large base: 10-day range at most 70% of the 40-day range, within 10% of the 20-day high. Ready when within 2% of the 20-day high after fewer than 3 straight up days. In the code these read as: tightness = clamp01(1 - range10 / range40), dry = clamp01(1 - vol5 / vol50), near = clamp01(1 - (high20 - close) / high20); a setup is none when distance from the 52-week high exceeds 0.18, tight_breakout when tightness is at least 0.45 and dry is at least 0.2 and near is at least 0.94, and large_base when tightness is at least 0.3 and near is at least 0.9; trigger ready when near is at least 0.98 and consecutive up days are under 3.
3. Market gate: Nasdaq Composite proxy B from the prior session. Proxy B is green when the 8-day EMA is over the 21-day EMA with both rising over 5 sessions, red when under with both falling, otherwise yellow (code: slope lookback 5). Red blocks entries. Tiering in the code: a candidate with any hard-gate reject stays reject; red proxy B makes it reject with a red-market reason; green proxy B with strong reads is tier A (strong means technical part at least 0.55, setup part at least 0.45, risk part at least 0.5, and stop percent at most 0.07); the rest that pass are tier B. Both A and B trade. Score parts in the code are weighted technical 0.25, setup 0.25, fundamental 0.15, story 0.15, trigger 0.1, risk 0.1, with fundamental and story parts at 0 in the public-proxy screen.
4. Entry: the next session, a day buy-stop at the 20-day high; skipped when open risk would pass 5% of equity.
5. Exit, engine-held stop at the 10-day low. A close under the 21-day EMA sells at the next session. After 10 sessions, a close at or under the entry price sells at the next session. A close back under the 20-day-high pivot sells half at the next session, once.
6. Sizing: 0.5% of equity at risk to the 10-day low, capped at 35% of equity, whole shares. Code constants: MIN_ADR 0.04, MIN_ABOVE_52W_LOW 0.7, MIN_DOLLAR_VOLUME 20,000,000, RISK_FRAC 0.005 with ceiling 0.01, MAX_POSITION_PCT 0.35, SLOPE_LOOKBACK 5; the ticket planner falls back to a 5% stop percent when none is supplied and floors share counts.

## Files in this repo

- This doc: docs/KOMAR_MOMENTUM-RECREATE.md.
- Accounting entry: docs/ALL-SLEEVES.json and docs/ALL-SLEEVES.md (entry under the canonical name, which is withheld here per the disclosure).
- Catalog entry: docs/CATALOG.json (entry under the canonical id, withheld here) and the catalog card in the strategies directory under the canonical id (its path carries the blocked token, so it is not written here; it is recorded in the private recreation index).
- Code, already in Test, no vendoring needed: the dedicated module komar.py (11,266 bytes in the tree) in the master-desk sleeve directory for this family (the directory segment and the main sleeve module basename both carry the blocked token, so neither is written here), plus that main sleeve module. The card also points to a rule-lines verify doc under docs/verify/ whose filename carries the blocked token.
- Vendored in this package: none. The code was already present in Test, so nothing was copied into engines/universe/komar-momentum/.

## Configuration

- No separate configuration file is recorded for this strategy. Configuration is the code constants listed in the Full algorithm (ADR floor, dollar-volume floor, above-low floor, risk fraction and ceiling, position cap, slope lookback) plus the catalog status, waiting.
- Anything else about configuration: not in the record.

## Data inputs

- Split-adjusted daily bars, 504 sessions as recorded on the card (the screen itself requires at least 80 sessions and uses 252 sessions for the 52-week range in the code).
- Nasdaq Composite daily bars, for proxy B.
- Live quotes.

## Install and run

1. Clone this repository (Test) and check out the main branch, keeping the directory layout unchanged.
2. Read this doc, the accounting entry in docs/ALL-SLEEVES.json, and the catalog card for this strategy (path in the private recreation index).
3. Locate the code named in Files in this repo: the dedicated komar.py module and the main sleeve module in the same sleeve directory.
4. Wire split-adjusted daily bars and Nasdaq Composite daily bars plus live quotes in the bar shape the module expects (dicts with date, o, h, l, c, v).
5. Run the screen after the close to produce ranked, tiered candidates, then place the next-session day buy-stop entries and the engine-held exits exactly as the Full algorithm states.
6. Verify against the Verification section before treating a recreation as faithful.

## Verification

Behaviour spec (no per-strategy test file for this exact id is recorded in this repo; this spec is the testable form of the rules above):

- A symbol with fewer than 80 bars, a close at or under $5, 50-day dollar volume under $20M, ADR under 4%, less than 70% above its 52-week low, a close at or under its 65-day EMA, or its 8-day EMA at or under its 21-day EMA is rejected and produces no entry.
- A name more than 18% below its 52-week high has setup none and produces no entry.
- Red proxy B from the prior session blocks every entry that session; green proxy B with the strong reads in step 3 tiers A, other passing candidates tier B.
- An entry, when it fires, is a day buy-stop at the 20-day high on the session after the setup, and is skipped if open risk would pass 5% of equity.
- Position size never exceeds 35% of equity and targets 0.5% of equity at risk to the 10-day low, in whole shares.
- A close under the 21-day EMA exits at the next session; the half exit on a close back under the pivot fires only once.
- Read-back check: this doc was written through the PII gate and read back from Test; the sha256 recorded in the batch results file matches the read-back bytes.
