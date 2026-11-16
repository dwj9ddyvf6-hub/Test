"""core.saty_gpt_v02 — Sol's Saty Research System v0.2.0,
ported faithfully per PORT-SPEC.md (workflow
saty-gpt-v02-20261023). reference/models/structure/strategies/
data are the source files with only their saty_reference
import repointed at this package (data.py also drops the
AlpacaReadOnlyData transport tail — the desk's shared data
door is the only feed path); risk_lots is the one ADAPTED
module (RiskConfig + lot math over desk fill truth, no
SQLite). His brokers/store/service/options layer does not
exist here — the desk dispatcher, Ink door and virtual slices
own execution and accounting."""
from core.saty_gpt_v02.models import VERSION
from core.saty_gpt_v02.data import (
    normalize_alpaca_daily as normalize_daily_bars)
from core.saty_gpt_v02.data import (
    normalize_alpaca_intraday as normalize_intraday_bars)

__all__ = ["VERSION", "normalize_daily_bars",
           "normalize_intraday_bars"]
