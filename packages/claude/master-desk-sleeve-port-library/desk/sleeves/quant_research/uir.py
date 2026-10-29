"""qr_unpricedinformationrelay -- UIR, Unpriced Information Relay, on its executed free-data producer: R8's registered
fixed-relay ABSORPTION policy (quant-research-backup@d170596b research-archives/2026-10-08-ten-strategy-edge-research-r8/
uir/run_experiments.py, vendored byte-exact under desk/vendor/quant_research/r8/) over R3's SEC cash-flow filing
events (desk/sleeves/quant_research/relay.py).

The relay: a sender's quarterly filing (CAT, DE, MSFT) -> its fixed receivers (CAT->DE, DE->CAT, MSFT->AAPL / AMZN /
GOOGL / NVDA / AVGO / ORCL). Features (R8 rebuild): the six price features and the receiver one-hot, plus the seasonal
cash-flow surprise s, |s|, s x gap, s x absorption and max(s, 0) x max(-sender reaction, 0), with gap =
clip((sender - receiver reaction) / volatility, +-5) and absorption = clip(receiver reaction / volatility, +-5).
Model: the month's ridge (penalty 10) on matured horizon-20 rows (labels before the month's first session less 21,
>= 24 source filings). Admission: a prediction above 30 bp; the receiver stays active 20 sessions. Account: the R3 / R8
funded basket (relay.basket) traded at the open after the decision close, sells first.

Removed gates: none (the producer has no desk-wide gates).

Named divergences:
  1. the decision policy is R8's executed fixed-relay proxy -- the R10 repair kernel's canonical UIR gates
     (repair_kernel.evaluate_uir: dated supplier / customer graphs, NLP-classified unscheduled demand revisions, the
     response curve and absorption model with audited checkpoints) need native inputs no free source supplies; the
     R10 playbook's sizing (4% per name, 12% vol target) is the canonical design, the account here is the proxy's;
  2. history: R3's recorded event rows (its prices and SEC vintage) train the models; live events after R3's last
     decision come from the current SEC companyfacts / acceptance times (relay.run, job `qr_relay`) and the desk's
     all-adjusted daily bars;
  3. execution: the desk's quotes at the first pass after the decision close's next open (the proxy's next-open);
  4. acceptance clock: R2 / R3 stored EDGAR acceptance as the Eastern wall clock labelled UTC (4-5 hours early); live
     events use the true UTC acceptance, so a filing accepted after 16:00 ET decides at the next close (2 of R3's 84
     events would move a session; tools/parity/qr_relay_sec.py)."""
import numpy as np

from . import relay as R

SID = "qr_unpricedinformationrelay"
SOURCE = {"repo": "quant-research-backup", "ref": "main", "commit": "d170596b4d3f24712da933683ceb6d9ee95d6937",
          "path": "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/uir/repair_kernel.py",
          "blob_sha": "13c6d6fa924bc4ac296d2655e2727c72cf95ac64",
          "policy": "research-archives/2026-10-08-ten-strategy-edge-research-r8/uir/run_experiments.py (ABSORPTION)",
          "events": "research-archives/2026-10-08-alpha-extraction-r3/events/EXECUTED_CONTIGUOUS_GUARD_PRODUCER.py"}


def absorption(row, prior=None):
    """R8 rebuild's x_absorption from a row's x_price (6 price features + one-hot) and surprise."""
    p, oh = list(row["x_price"][:6]), list(row["x_price"][6:])
    s = float(row["financial_surprise"])
    sr, rr, vol = p[0], p[1], p[4]
    gap = float(np.clip((sr - rr) / max(vol, 1e-6), -5, 5))
    absorb = float(np.clip(rr / max(vol, 1e-6), -5, 5))
    return p + oh + [s, abs(s), s * gap, s * absorb, max(s, 0) * max(-sr, 0)]


class UIR(R.RelayBook):
    SID, FAMILY_ROWS, POLICY, SOURCE = SID, "UIR_fixed_relays", "ABSORPTION", SOURCE
    HORIZON, THRESHOLD, RIDGE = 20, 0.003, 10.0

    def features(self, row, prior):
        return absorption(row)


def sleeves():
    return [UIR()]
