"""v3 sleeve crypto_stdev_link — GrokBot t474u CryptoFilterTwin (stdev filter on
LINK) faithful port, T474U-CRYPTO-PORT-20261116. Engine:
desk3/t474u_crypto.py (source md2 mdesk/engines/t474u_x.py @
master-desk c2de06921bac; fidelity proof
proof/t474u/t474u_fidelity_result.json)."""
from desk3.t474u_crypto import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "crypto_stdev_link"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
