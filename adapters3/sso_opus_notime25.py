"""v3 sleeve sso_opus_notime25 — CONV-46 variation beside sso_opus
(Conversion Program, SSO-PORT-CONV46-20261115): the identical
ported engine with the TIME_25 exit class removed and nothing
else changed (GUTTING AS VARIATION; the parent is never edited
into the variation). Engine: desk3/sso_opus.py
(drop_time25=True). See config/conversion_variations_20261115.json
for the registered variation, its falsifier and its kill rule."""
from desk3.sso_opus import evaluate as _ev, INPUTS, PRODUCERS
SLEEVE_ID = "sso_opus_notime25"
def evaluate(view, ctx=None):
    return _ev(SLEEVE_ID, view, ctx)
