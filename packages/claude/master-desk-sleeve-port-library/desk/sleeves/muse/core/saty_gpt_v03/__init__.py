"""core.saty_gpt_v03 — Sol's Saty Adaptive Opportunity Engine
v0.3.0, ported faithfully per PORT-SPEC.md (workflow
saty-gpt-v03-20261023). reference/models/structure/strategies/
routing/awareness/data are the source files with only their
saty_reference import repointed at this package; risk_lots is
the one ADAPTED module (RiskConfig + lot math over desk fill
truth, no SQLite). His brokers/store/service/options layer does
not exist here — the desk dispatcher, Ink door and virtual
slices own execution and accounting."""
from core.saty_gpt_v03.models import VERSION

__all__ = ["VERSION"]
