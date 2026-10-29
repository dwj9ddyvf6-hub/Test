"""qr_catalystresolutiongap -- CRG, Catalyst Resolution Gap, on its executed free-data producer: R8's registered
surprise-history policy SURPRISE_HISTORY__H20__L1, its development-frozen selection for the surprise-history variant
(quant-research-backup@d170596b research-archives/2026-10-08-ten-strategy-edge-research-r8/crg/run_tests.py and
FROZEN_DEVELOPMENT_SELECTION.json, vendored byte-exact under desk/vendor/quant_research/r8/) over R3's SEC cash-flow
filing events of CAT, DE and MSFT (desk/sleeves/quant_research/relay.py), own stock.

Features: the 15-coordinate x_price (six price features + the issuer one-hot) and the current seasonal CFO - capex
surprise s, the issuer's previous surprise p (strictly earlier decision), s x p and the prior-four mean. Model: the
month's ridge (penalty 1) on matured horizon-20 own-stock rows (labels before the month's first session less 21,
>= 24 source filings). Admission: a prediction above 30 bp; the issuer stays active 20 sessions. Account: the R3 / R8
funded basket (relay.basket) traded at the open after the decision close, sells first.

Removed gates: none (the producer has no desk-wide gates).

Named divergences:
  1. the decision policy is R8's executed own-stock proxy -- the R10 repair kernel's canonical CRG gates
     (repair_kernel.evaluate_crg: frozen quarter heads with joint residual draws, typed operating drivers, 30-peer
     multiples, 200 bootstrap return fits) need inputs no free source supplies; the account is the proxy's, not the
     R10 playbook's min(.05, .0025 / max(ES, .08)) sizing;
  2. history: R3's recorded event rows; live events from the current SEC companyfacts / acceptance times (job
     `qr_relay`) and the desk's all-adjusted daily bars;
  3. execution: the desk's quotes at the first pass of the session after the decision close;
  4. acceptance clock: live events use the true UTC EDGAR acceptance (R2 / R3 stored the Eastern wall clock labelled
     UTC); a filing accepted after 16:00 ET decides at the next close (tools/parity/qr_relay_sec.py)."""
import numpy as np

from . import relay as R

SID = "qr_catalystresolutiongap"
SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
          "path": "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/crg/repair_kernel.py",
          "blob_sha": "3e659c8bd69f0aa5afd604ddc840df5ae0f1062e",
          "policy": "research-archives/2026-10-08-ten-strategy-edge-research-r8/crg/run_tests.py (SURPRISE_HISTORY__H20__L1)",
          "events": "research-archives/2026-10-08-alpha-extraction-r3/events/EXECUTED_CONTIGUOUS_GUARD_PRODUCER.py"}


def surprise_history(row, prior):
    """R8's SURPRISE_HISTORY: base + [s, p, s*p, m]; p = the issuer's previous surprise (0 without one), m = the mean
    of its last four (0 without any)."""
    s = float(row["financial_surprise"])
    p = float(prior[-1]) if prior else 0.
    m = float(np.mean(prior[-4:])) if prior else 0.
    return list(row["x_price"]) + [s, p, s * p, m]


class CRG(R.RelayBook):
    SID, FAMILY_ROWS, POLICY, SOURCE = SID, "CRG_own_stock", "SURPRISE_HISTORY__H20__L1", SOURCE
    HORIZON, THRESHOLD, RIDGE = 20, 0.003, 1.0

    def features(self, row, prior):
        return surprise_history(row, prior)


def sleeves():
    return [CRG()]
