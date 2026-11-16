# Trying out new strategy ideas

New ideas start here, in **shadow**: the idea reads the same market
information as the live strategies and writes down what it *would*
have done, in its own notebook under `state/research/<idea name>/`.
It cannot place an order — the notebook is all it can reach, and any
attempt to reach the order path is blocked and recorded in its
notebook as a blocked attempt.

## Adding an idea

1. Write one Python file here with `evaluate(view, ctx)`: read market
   data from `view`, record would-be trades with `ctx.emit_signal({...})`.
2. Add a row to `registry.json` with `"status": "shadow"`.
3. It is evaluated each time the research lane runs
   (`desk3.research.evaluate_candidates`).

## Promoting an idea to a real strategy

Promotion is always a deliberate, recorded move — never automatic:

1. Run `desk3.research.promote_candidate(registry_path, id, log_path)` —
   this flips the registry status to `promoted` and adds a dated line
   to `PROMOTIONS.md`.
2. Separately, by hand: add the strategy's row to the trading roster
   (`config/sleeves.json`) and its entrypoint, like any other strategy.
3. Commit the registry change, the promotions log, and the roster
   change together, saying that the idea was promoted.

Skipping step 2 leaves the idea promoted on paper but not trading;
skipping step 1 leaves it in shadow no matter what else changes.
