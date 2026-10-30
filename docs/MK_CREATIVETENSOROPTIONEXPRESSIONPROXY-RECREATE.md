# mk-creativetensoroptionexpressionproxy: Recreation Package

## Provenance

- ALL-SLEEVES accounting (Test `docs/ALL-SLEEVES.json`, also `docs/ALL-SLEEVES.md`): canonical name "Tensor fires as calls", type options directional, family milkman, style "Tensor signal, options", universe "1,822 US stocks (the store_v1 survivors), their listed calls", asset class equity options, timeframe 1w, creator recorded as the TENSOR_CREATIVE option study research lab (the creator string itself is not reproduced in this doc: it carries a token the public-write gate forbids in new files). Algorithm grade PARTIAL in the accounting, with recorded gaps: entry/signal rule, exit rule and sizing not recorded in any consulted source. Alias `mk_creativetensoroptionexpressionproxy` (test_catalog status: entry status_counts={'live': 1}).
- Test catalog entry `mk-creativetensoroptionexpressionproxy` (`docs/CATALOG.json`): status live, card `strategies/milkman/mk-creativetensoroptionexpressionproxy.md`, code list naming the files in Files below.
- The rules the accounting lacked are held in the Test strategy card and in the code in this repo (named in Files); nothing beyond the card and that code is claimed. The card's own note stands: the Tensor engine these lanes run is not published in this repo, so the fire producer itself cannot be recreated from Test alone; the sleeve code that consumes the fires and trades the calls is in Test in full.

## What this strategy is

Tier-A weekly Tensor Cyan / Green fires on the 1,822 store_v1 survivor names, expressed with listed calls instead of stock: one-year at-the-money calls, $1,000 of premium per fire, sold after 52 weeks. Book $1,000,000. In Test it runs as the `OptionExpression` class (SID `mk_creativetensoroptionexpressionproxy`) in the milkman family module under `sleeves/milkman/` named in the card's Code row (a 47,897-byte module; its filename is not spelled in this doc for the gate reason given in Provenance).

## Full algorithm

From the card and the `OptionExpression` / `FireBook` code in that module (class constants: CAPITAL 1,000,000, PREMIUM 1,000.0, PMIN 0.02, WEEKS 52; FLOOR = 100,000 dollar-volume floor):

1. Fires: the producer runs the vendored Tensor engine over Yahoo payloads (1wk and 1d, last 10 years) for the store_v1 survivors and writes the weekly fires file the sleeve's fires feed reads (the code's needs dict names that feed plus its chains feed). A weekly fire is a closed weekly Tensor bar with a buy-cyan or buy-green marker, bar index >= 60. Sleeve evaluations run in RTH only, cadence 300 s.
2. Exits are processed before entries (FireBook.signal): a ledger row whose exit session is past exits at once; on its exit session an option row exits with a marketable order that session (window 1800 s; not market-on-close, which is the equity-row treatment). Exit session for a call row = min(the last session of the week 52 weeks after the fire week, the call expiry's last session).
3. Candidates: weekly fires with a close and 20-day dollar volume >= $100,000 (FLOOR), passing the tier-A proxy (`tier_a_proxy` in the same module): at least 2 of (close <= $14.94; close <= $14.94 AND 60-day return >= 31%; at least 70% below the 252-day high, read as dd252 >= 70 in the code; sector SMH), and sector not in (XLF, XLB, XLRE, XLU); and, when a 60-day realised volatility value is carried, 5 <= rv <= 400 (percent).
4. Entry timing: a fire enters on the session after its fire week (entry_on = the session after the fire's last session); the shared FireBook machinery enters only in the first 90 minutes of a session, marks a fire seen on its entry session, and treats a fire first seen more than 1 session late as missed (logged when at most 5 sessions late). If no chain is available for the name this pass, the fire is retried on a later pass instead of being marked seen.
5. Call selection (`pick_call`): among two-sided listed calls (bid and ask present), keep expiries at least 75% of 52 weeks out (dte >= 273 days against the 364-day target); pick the expiry nearest 52 weeks (364 days) from the entry session, then the strike nearest the fire close (spot).
6. Premium gate and sizing: if the ask is below 2% of spot, skip (logged "premium under 2% of spot"). Contracts n = floor(1000 / (ask x 100)); if n < 1, buy 1 contract unless one contract costs over $2,000 (ask x 100 > 2 x PREMIUM), in which case skip (logged).
7. Entry intent: a long option entry for n contracts of the picked call symbol, limit price round(ask x 1.02, 2), window 3600 s (one hour), with the underlying recorded in the intent meta; the ledger row records symbol, quantity, ask as reference price, asset option and the exit session from step 2.
8. Named divergences recorded in the module header: the study priced calls by Black-Scholes on realised volatility, the desk buys real listed calls; tier A is the study's own labelled proxy, not the META-boosted tier; META / responsiveness / genome flags are not computed (missing-value convention: no veto); entries are sized on the live quote path of the shared machinery where applicable, and the universe is the 1,822 store_v1 survivors.

## Files in this repo

- This doc: `docs/MK_CREATIVETENSOROPTIONEXPRESSIONPROXY-RECREATE.md`
- Strategy card: `strategies/milkman/mk-creativetensoroptionexpressionproxy.md`; catalog: `docs/CATALOG.json` (entry mk-creativetensoroptionexpressionproxy); rule lines: `docs/verify/milkman.md`.
- Sleeve code (already in Test): the milkman family module under `sleeves/milkman/` named in the card's Code row (47,897 bytes in the fresh tree; contains the OptionExpression class, FireBook, tier_a_proxy and pick_call), plus `sleeves/milkman/vendored.py` (the loader for the vendored study code) and `sleeves/milkman/vendor/milkman/dstrats.py` (vendored study code), with `sleeves/milkman/vendor/milkman/store_v1_1d_index.json` (the survivor universe index) and `sleeves/milkman/__init__.py`.
- Accounting: `docs/ALL-SLEEVES.json`, `docs/ALL-SLEEVES.md`.
- Not in this repo (card's own note): the Tensor engine that produces the fires (the desk's vendor engine directory) is not published in Test; a recreation must supply weekly Cyan / Green fires in the feed file format the code reads, or reuse a fire file produced elsewhere.
- Code search: Silicon, quant-research-backup and Midna trees were searched for this sleeve id; the running sleeve code was found in Test only.

## Configuration

- Sleeve id: `mk_creativetensoroptionexpressionproxy`; family milkman; capital $1,000,000; cadence 300 seconds; schedule rth.
- Needs: the weekly-fires feed and its chains feed (call chains 250-800 days out for candidate names, per `feed_chains` in the module).
- Params (from the class `params()`): tier "A (c_eng.tierA_proxy)", strike "spot (k = 1.0)", expiry "nearest 52 weeks", premium_usd 1000, pmin 0.02, hold_weeks 52, floor_dv20 100000; margin_rate from the milkman package init.
- State schema: ledger, seen, log, extra (FireBook).

## Data inputs

- Yahoo daily bars (10 years) of the 1,822 names, built into Friday weeks; the vendored Tensor engine runs after each close (daily lanes) and each weekend (weekly lanes) to produce the fires (card).
- The desk's call chains, 250-800 days out, for candidate names; live quotes where the shared machinery prices an entry.

## Install and run

1. Clone the Test repo.
2. Place the `sleeves/milkman/` package files above at their repo paths, preserving the package layout (the module imports the package init for MARGIN_RATE and the calendar / contract modules by relative path).
3. Register the sleeve from the module's `sleeves()` list (class OptionExpression) with capital $1,000,000, cadence 300 s, schedule rth and the needs above.
4. Supply the fires feed: a weekly fires file in the format the code reads (fires with lane, sym, t, friday, last_session, close, dv20, d_ret60, dd252, sector, rvol60d), produced by the Tensor engine described in Files (not in Test), plus call chains for candidate names.
5. Call the sleeve's `signal(view)` on cadence in RTH; exits are processed before entries, entries only in the first 90 minutes.
6. Verify against the Verification checklist before any live use.

## Verification

No dedicated test file for this sleeve was found in the fresh Test tree. Behaviour checklist from the algorithm above:

- A fire that fails the tier-A proxy, the $100,000 dv20 floor, or the 5-400% realised-volatility band produces no entry; a fire from a non-Cyan / non-Green weekly lane produces no entry.
- The picked call is the two-sided call at the expiry nearest 364 days (and at least 273 days out) with the strike nearest the fire close; an ask below 2% of spot is skipped, and sizing is floor(1000 / (ask x 100)) contracts with the single-contract exception exactly as stated.
- The entry order is a limit at round(ask x 1.02, 2) good for one hour, on the session after the fire week (or the one-late-session allowance), and the position exits on the earlier of the week-52 session and the expiry's last session.
- With no chain available for a candidate this pass, no entry is emitted and the fire is not consumed.
