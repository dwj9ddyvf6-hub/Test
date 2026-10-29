"""Unchanged helpers from frozen R14 source; venue execution extensions live separately."""
import math

def positive(value, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Finite numeric value required")
    if not math.isfinite(value) or value < 0 or (not allow_zero and value == 0):
        raise ValueError("Invalid positive numeric value")
    return float(value)

def features(rows):
    closes = [r["close"] for r in rows]
    output = []
    for i, row in enumerate(rows):
        if i < 199:
            output.append(None)
            continue
        sma = math.fsum(closes[i-199:i+1]) / 200
        output.append({"source_index": i, "signal_date": row["date"],
                       "signal_at": row["complete_at"], "close": closes[i],
                       "sma200": sma, "SMA200": closes[i] > sma,
                       "M7": closes[i] > closes[i-7],
                       "momentum7": closes[i]/closes[i-7]-1})
    return output

def rebalance(cash, quantities, prices, weights, fee):
    cash = positive(cash, True)
    fee = positive(fee, True)
    if fee >= 1 or len(quantities) != 2 or len(prices) != 2 or len(weights) != 2:
        raise ValueError("Invalid fee or dimensions")
    quantities = [positive(q, True) for q in quantities]
    prices = [positive(p) for p in prices]
    weights = [positive(w, True) for w in weights]
    if math.fsum(weights) > 1 + 1e-12:
        raise ValueError("Gross target exceeds funded capital")
    values = [q*p for q, p in zip(quantities, prices)]
    pre = cash + math.fsum(values)
    lo, hi = 0.0, pre
    for _ in range(70):
        nav = (lo + hi) / 2
        residual = nav + fee*math.fsum(abs(w*nav-v) for w,v in zip(weights, values)) - pre
        if residual > 0:
            hi = nav
        else:
            lo = nav
    post = (lo+hi)/2
    targets = [w*post for w in weights]
    dollars = [t-v for t,v in zip(targets,values)]
    gross = math.fsum(abs(d) for d in dollars)
    cost = fee*gross
    remainder = cash - math.fsum(dollars) - cost
    tolerance = max(1e-7, pre*1e-12)
    if remainder < -tolerance or abs(remainder-post*(1-math.fsum(weights))) > tolerance:
        raise ValueError("Funding invariant failed")
    return max(0.0,remainder), [v/p for v,p in zip(targets,prices)], {
        "pretrade_nav": pre, "postfee_open_nav": post,
        "gross_turnover_usd": gross, "fees_usd": cost,
        "trade_dollars": dollars, "target_weights": weights,
        "buys_usd": math.fsum(max(0,d) for d in dollars),
        "sells_usd": math.fsum(max(0,-d) for d in dollars)}
