"""v3 sleeve sso_opus — the SSO Opus swing baseline (Conversion
Program CONV-46, SSO-PORT-CONV46-20261115): the 2026-11-03
research engine ported to desk3/sso_opus.py with fidelity proven
against the research trade ledgers (265/265 primary, 282/282
cost case, 0 divergences). See
config/conversion_variations_20261115.json for the registered
variation beside it and desk3/sso_opus.py for the port."""
from desk3.sso_opus import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "sso_opus"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
