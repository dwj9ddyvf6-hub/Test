# DESIGN: THE SECOND-ORDER BOOK (Invention 2)

Status: DESIGN ONLY, Sat 2026-11-14. No build today. Registration:
midna-book/strategy-candidates/2026-11-14-invention-second-order-book.md.

## Mechanism

A meta-model whose subject is not stocks but sleeves. The estate
has generated millions of labeled evaluation rows: every sleeve
evaluation knows its features, its gate distances, and (for fires)
its outcome. Train a model P(fire pays | sleeve gate geometry,
tape state) and use it as the fleet's selection function: which
sleeves' fires to trust today, which families are in season. This
is Ledger vs. Surface generalized from one family to the fleet:
there, our ledger's calibrated dispersion was set against the
market's implied; here, the fleet's own history is set against
each new fire.

The discipline from the research report (section 1.1) is adopted
by name: the meta-model is a META-LABEL, never a side prediction.
Primary sleeves decide side; the meta-model only filters and
sizes (trade if p_hat clears a frozen threshold; the AFML
evidence is that meta-labeling improves precision at the cost of
recall and cannot rescue a negative-expectancy primary, it can
only refine a real one). Labels are triple-barrier labels on the
primary fires (profit-take and stop at the fire's own geometry,
vertical barrier at the family's median holding horizon),
computed on distinct events, never on overlapping state-machine
round trips.

## Data contracts (against the attribution ledger)

Reads: runs/attribution_ledger_v1.json per sleeve (expectancy_usd,
win_rate, avg_hold_days, own_closes, klass, flags) as the label
sanity layer: the meta-model's training labels must reconcile to
the ledger's settled closes for every sleeve where both exist;
mismatches are defects, not features. Feature rows come from the
gate-distance instrumentation (improvement lane's build) joined
to warm bars for tape state; settlement labels come from the
harvester (fires resolved at target/stop/horizon). The NETTED
flag excludes a sleeve's closes from training until the fleet
flip (Mon 2026-11-16 census) clears it, exactly as the Internal
Market design treats the same flag.
Writes: its own feature/label store and model artifacts in the
research lane; predictions appended per fire, frozen at fire
time, graded by the harvester. Never writes to desk state.

## Build order

1. Label factory: triple-barrier labels for every historical fire
   with a recorded entry/stop/target (Ghost Book population
   first, then the intent-journal fires as capture improves).
2. Baseline model: logistic regression on a small frozen feature
   list (gate distance, vol regime, trend state, spread, hour,
   family recent hit rate), purged and embargoed splits (CPCV
   N=10, k=2 per the admission exam) because labels overlap.
3. Twin run: filtered versus unfiltered twins on the three
   highest-volume primary families, forward, per the report's
   section 1.1 falsification form (>= 100 primary fires).
4. Only on twin success: fleet-wide scoring as a shadow selection
   function beside the attribution leaderboard.

## Falsifier

Restated from the registration: the meta-model's top-decile
sleeve picks do not outperform the fleet median forward. Interim
kill, from the report: after >= 100 primary fires in the twin
run, filtered expectancy per trade (net of the spread haircut)
<= unfiltered, or the model's out-of-sample Brier is no better
than the base win-rate constant; either kills it before stage 4.
