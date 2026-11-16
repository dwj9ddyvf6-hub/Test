"""v3 sleeve fwd_alpaca_enj_iu_body — IU-body order logic
(IU-BODY-ORDER-LOGIC-20261116). Engine: desk3/iu_body.py, a faithful
desk-side implementation of the archive public-recipe reducer
(public_source_sleeves.py 'iu_body', sha256 e64c995d...) under the
PUBLIC_IU_BODY_SPOT100 runtime overlay (ENJ 5m, spot long-only).

This adapter replaces the port-batch4 adapter
(desk3/sleeves/fwd_alpaca_enj_iu_body.py) as the roster row's module:
that adapter delegates to the byte-pinned vendored strategy whose
signal() returns [] by source design, so the sleeve could never
fire. The vendored file and the old adapter stay untouched (the
port_batch4 pin test still passes on them); the roster row keeps
its id and its ENJ paper class registration (dispatcher
ENJ_PAPER_SLEEVES, own_book_view, ENJ-PAPER-20261116 stamp) and now
points here. Inputs are the desk's existing ENJ serving forms: the
Kraken 1-minute tape (resampled to the source's 5-minute bars in
the engine), the Kraken depth book (the observed quote), and the
sleeve's own-book positions."""
from desk3.iu_body import evaluate as _f

SLEEVE_ID = "fwd_alpaca_enj_iu_body"
INPUTS = ("bars:ENJ/USD:1Min", "kraken.book", "positions")
PRODUCERS = ({"name": "kraken", "outputs": ("bars:ENJ/USD:1Min",
                                            "kraken.book"),
              "freshness_sla_s": 3600},
             {"name": "account", "outputs": ("positions",),
              "freshness_sla_s": 3600})


def evaluate(view, ctx=None):
    return _f(view, ctx, SLEEVE_ID)
