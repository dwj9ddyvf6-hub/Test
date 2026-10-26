"""CCI Correction Pullback Strategy (long-only, daily bars).
Core filter: Lowest(CCI(27), 18) < -100. No performance claims; backtest() is untested on real data."""
from dataclasses import dataclass
import numpy as np, pandas as pd

@dataclass
class P:
    cci_len: int = 27; look: int = 18; cci_thr: float = -100.0; cci_trig: float = -100.0
    sma_fast: int = 50; sma_slow: int = 200; atr_len: int = 14
    stop_atr: float = 2.0; trail_atr: float = 3.0; target_r: float = 3.0; max_bars: int = 20
    risk_pct: float = 0.005; max_pos: int = 10; max_pos_pct: float = 0.15
    min_price: float = 5.0; min_dollar_vol: float = 20e6; vix_max: float = 30.0

def cci(df, n):
    tp = (df.high + df.low + df.close) / 3
    sma = tp.rolling(n).mean()
    mad = tp.rolling(n).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma) / (0.015 * mad.replace(0, np.nan))

def atr(df, n):
    pc = df.close.shift()
    tr = pd.concat([df.high-df.low, (df.high-pc).abs(), (df.low-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def signals(df, p=P(), spy=None, vix=None):
    d = df.copy()
    d["cci"] = cci(d, p.cci_len); d["atr"] = atr(d, p.atr_len)
    d["sma_f"] = d.close.rolling(p.sma_fast).mean(); d["sma_s"] = d.close.rolling(p.sma_slow).mean()
    d["dvol"] = (d.close*d.volume).rolling(20).mean()
    correction = d.cci.rolling(p.look).min() < p.cci_thr
    trend = (d.close > d.sma_s) & (d.sma_f > d.sma_s)
    liquid = (d.close >= p.min_price) & (d.dvol >= p.min_dollar_vol)
    trigger = (d.cci > p.cci_trig) & (d.cci.shift() <= p.cci_trig) | \
              ((d.close > d.high.shift()) & (d.cci > d.cci.shift()) & (d.cci < 0))
    regime = pd.Series(True, index=d.index)
    if spy is not None:
        regime &= (spy.close > spy.close.rolling(200).mean()).reindex(d.index).fillna(False)
    if vix is not None:
        regime &= (vix.reindex(d.index).ffill() < p.vix_max).fillna(False)
    d["entry"] = correction & trend & liquid & trigger & regime
    return d

def size(equity, entry, stop, p=P()):
    risk = entry - stop
    if risk <= 0: return 0
    return int(max(0, min(equity*p.risk_pct/risk, equity*p.max_pos_pct/entry)))

def backtest(data: dict, p=P(), equity=100_000.0, spy=None, vix=None, cost_bps=5.0):
    """Signal on close t, fill at open t+1. Stop/target intrabar, trail on close, time stop."""
    sig = {k: signals(v, p, spy, vix) for k, v in data.items()}
    dates = sorted(set().union(*[s.index for s in sig.values()]))
    pos, trades, curve, pending = {}, [], [], []
    c = cost_bps/1e4
    for t in dates:
        for k in pending:  # fills at open
            s = sig[k]
            if t not in s.index or k in pos or len(pos) >= p.max_pos: continue
            r = s.loc[t]; a = s.atr.shift().loc[t]
            if not np.isfinite(a): continue
            stop = r.open - p.stop_atr*a; q = size(equity, r.open, stop, p)
            if q and q*r.open*(1+c) <= equity:
                equity -= q*r.open*(1+c)
                pos[k] = dict(q=q, e=r.open, stop=stop, tgt=r.open+p.target_r*(r.open-stop), hi=r.open, n=0, d=t)
        pending = []
        for k in list(pos):
            s = sig[k]
            if t not in s.index: continue
            r, x = s.loc[t], pos[k]; x["n"] += 1; px = None
            if r.low <= x["stop"]: px = min(r.open, x["stop"])
            elif r.high >= x["tgt"]: px = max(r.open, x["tgt"])
            elif x["n"] >= p.max_bars or r.close < r.sma_s: px = r.close
            if px is not None:
                equity += x["q"]*px*(1-c); trades.append((k, x["d"], t, x["e"], px, x["q"])); del pos[k]; continue
            x["hi"] = max(x["hi"], r.close); x["stop"] = max(x["stop"], x["hi"]-p.trail_atr*r.atr)
        mtm = equity + sum(x["q"]*sig[k].close.get(t, x["e"]) for k, x in pos.items())
        curve.append((t, mtm))
        cands = [(k, sig[k].loc[t, "cci"]) for k in sig if t in sig[k].index and sig[k].loc[t, "entry"] and k not in pos]
        pending = [k for k, _ in sorted(cands, key=lambda z: z[1])][:max(0, p.max_pos-len(pos))]
    return pd.DataFrame(trades, columns="sym entry_date exit_date entry exit qty".split()), pd.Series(dict(curve))

if __name__ == "__main__":  # smoke test on synthetic data only
    rng = np.random.default_rng(0); idx = pd.bdate_range("2020-01-01", periods=600)
    def fake(seed):
        r = np.random.default_rng(seed); cl = 50*np.exp(np.cumsum(r.normal(.0005, .02, 600)))
        op = cl*(1+r.normal(0, .005, 600))
        return pd.DataFrame(dict(open=op, high=np.maximum(op, cl)*1.01, low=np.minimum(op, cl)*.99, close=cl, volume=1e6), idx)
    tr, eq = backtest({f"S{i}": fake(i) for i in range(5)})
    print("smoke ok:", len(tr), "trades,", len(eq), "bars")
