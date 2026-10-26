"""qr_alphamemosourcepreservingfactorrecon and qr_quantaalphadeterministicproposalreco -- the six-strategy
reconstruction's AlphaMemo (jarrettyu/AlphaMemo@412fee13) and QuantaAlpha (QuantaAlpha/QuantaAlpha@b7ceb27b) factor
models, traded as the reconstruction registers them (results/portfolios/alphamemo-residual and quantaalpha-rounds5:
TopkDropout, top 50, drop 5, minimum hold 1 session, risk degree 0.95, its participation and affordability rules).

Signals (desk/sleeves/quant_research/scores.py, job `qr_scores` after each close): the frozen pools and LightGBM
models vendored byte-exact under desk/vendor/quant_research/{alphamemo,quantaalpha}/ -- AlphaMemo's principal
`residual` run (15 admitted sspm formulas + the four baseline features, per-date z-score, a 7-tree model) and
QuantaAlpha's main five-round run (`rounds5`, its native parser and function library, per-date CSRankNorm, the saved
model) -- on the frozen 640-name panel roster with build_panel's causal eligibility; the model's prediction after
the close of session t is traded from session t+1 (dropout_book.py).

Named divergences:
  1. data: the desk's Alpaca split-adjusted daily bars (the reconstruction's provider and adjustment) for the 640
     roster columns; validity checks the split-adjusted bar only; a column the provider no longer serves is unobserved
     (as the panel's inactive names after their last bar);
  2. inference: LightGBM is not installed -- desk/sleeves/quant_research/lgbm_text.py evaluates the saved text models
     with LightGBM's own decision rule; QuantaAlpha's function library imports joblib (absent), replaced by a
     sequential stand-in used by none of the frozen expressions;
  3. rolling statistics restart at the window's first row (320 sessions): pandas' running sums can differ from the
     full-history panel in the last bits (QuantaAlpha); and the desk's runtime (pandas 3 / numpy 2.5) computes
     rolling second moments differently in the last bits from the source's (pandas 2.2.2 / numpy 2.3.5), which can
     move a cross-sectional rank by a position: under the source's runtime the port's scores are identical (the
     receipt replays every differing session there and counts it as `runtime_numerics`);
  4. execution: market orders from the first pass of session t+1, sells before buys, sized on the live bid / ask
     (the reconstruction filled at the session's open); the quotes of the candidates arrive with the next pass;
  5. budget costs: the registrations' native cost pairs (AlphaMemo buy 0 / sell 5 bp, QuantaAlpha 5 / 15 bp) size the
     affordable buys; the desk charges its own fees."""
from . import common as C
from .dropout_book import DropoutBook

SIX = C.SIXAI


class AlphaMemo(DropoutBook):
    SID = "qr_alphamemosourcepreservingfactorrecon"
    NAME = "alphamemo"
    STUDY = "alphamemo residual frozen pool + LightGBM (results/portfolios/alphamemo-residual)"
    BUY_BPS, SELL_BPS = 0.0, 5.0
    SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT, "path": SIX + "alphamemo/reconstruct.py",
              "upstream": "jarrettyu/AlphaMemo@412fee13d905bf5a25f0958aa572b7c668ccb925",
              "registration": "results/portfolios/alphamemo-residual/registration.json"}


class QuantaAlpha(DropoutBook):
    SID = "qr_quantaalphadeterministicproposalreco"
    NAME = "quantaalpha"
    STUDY = "quantaalpha rounds5 frozen pool + LightGBM (results/portfolios/quantaalpha-rounds5)"
    BUY_BPS, SELL_BPS = 5.0, 15.0
    SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT,
              "path": SIX + "quantaalpha/reconstruct.py",
              "upstream": "QuantaAlpha/QuantaAlpha@b7ceb27b1001261d7a95b209a963664ae1f8ab23",
              "registration": "results/portfolios/quantaalpha-rounds5/registration.json"}


def sleeves():
    return [AlphaMemo(), QuantaAlpha()]
