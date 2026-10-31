# PROVENANCE — Codex option-model stack, adopted as independent oracle

Adopted 2026-10-28 under the owner's adoption order, from the evaluation in
`~/workspace/peer-commit-read-20261027/codex-review/05-EVALUATION.md`
section 2 item 1 (the strongest code in Codex's tree) and section 7
item 3. Purpose: an independent oracle for our Payoff Sketch (tool 6,
`~/workspace/terminal-lineup/site/payoff-sketch/`). The models disagree
with ours only if one side is wrong; agreement is evidence, not proof
of vendor parity.

## Source

- Repo: `dwj9ddyvf6-hub/Silicon` (private), branch `main`.
- Fetched read-only via `~/workspace/.scratch-femto-mirror/ghapi.py`
  (`api_ok`, GET Contents API only). No GitHub writes were made.
- Fetch commit (main head at fetch time):
  `f65f62ad32a5438730a99badca71b4e5cc357702`
  ("Reconcile REA scope and restore Morgue evidence gates",
  2026-10-28T12:38:03Z).
- Review snapshot in 03-BUILDS-REVIEW.md was head `7d435a524a`;
  the `app.js` blob below is byte-identical to the reviewed blob, so
  the reviewed option stack is exactly what was fetched.

## Files in this directory (read-only reference copies, mode 444)

| Local copy | Source path in Silicon | Git blob sha | SHA-256 | Bytes |
|---|---|---|---|---|
| `codex_app.js` | `apps/silicon-market-terminal/app.js` | `5c78c6b32c0f88fb3591a3e708455ce46b499db5` | `a3e24bce14c8ac7524a58c48e52c6447c0c830ad17e78aa46cdb49d2e675822b` | 327403 |
| `codex_candidate-calculation-fixtures.mjs` | `apps/silicon-market-terminal/candidate-calculation-fixtures.mjs` | `4b5343e807151ea5b80085aefa87255b84ec0615` | `096650e3da186fd84b2f40f7df103fd6fc6eb066dccd10ad78503157cab9d9f2` | 44679 |

Blob shas were verified locally with `git hash-object` against the
downloaded bytes, not merely copied from the API response.

Note on the fixtures blob: 03-BUILDS-REVIEW.md recorded blob
`e5c56188` at its snapshot head. The fixtures file has since changed
on main (current blob above). The crosscheck does not rely on his
fixtures file: it calls the option functions in `codex_app.js`
directly, and that blob is unchanged from the reviewed snapshot.

## The adopted stack (functions in `codex_app.js`)

Identified from 03-BUILDS-REVIEW.md sections 2.5 and 3.1-3.3:

- Expiration payoff (03 section 2.5, grade A):
  `optionStrategyPnlAt` (line 2030), `optionStrategyStats` (line 2038).
- European Black-Scholes (03 section 3.1, grade A):
  `blackScholesEuropean` (line 2093), with `standardNormalCdf`
  (line 2084).
- American CRR (03 section 3.2, grade A-):
  `crrAmericanOption` (line 2120), `americanCrrGreeks` (line 2163),
  routed per leg by `optionScenarioModel` (line 2202).
- Sensitivity grid (03 section 3.3, grade A-):
  `buildOptionStrategyModel` (line 2211),
  `buildOptionStrategySensitivity` (line 2231).

Explicitly NOT adopted: `blackScholesGamma` (line 1224), the static
GEX lab's gamma, which 03 section 2.6 proved defective off-ATM. The
gamma crosscheck in `crosscheck_payoff.py` uses the European model's
gamma, not the GEX lab's.

## Licence posture

This is our own program's code: written by Codex (Ausar), the owner's own
AI agent, inside the owner's own Silicon repository, for this same
terminal program. The models are clean-room implementations of
textbook Black-Scholes and Cox-Ross-Rubinstein formulas (Hull;
Cox, Ross and Rubinstein 1979), built from the OptionStrat teardown
with no vendor code, data, or outputs used. No vendor parity is
claimed for them, by their author or by us. They are kept here as
read-only reference copies; our own code is not edited to match them,
and any disagreement found by the crosscheck is reported, not
smoothed.
