"""Independent stdlib reference math for NEW FE01_DAILY_TREND_PRIOR252_V1.
Offline synthetic/parity verification only; no acquisition or original scorer changes.
"""
import json
import math
import sys


def compute(closes):
    if not isinstance(closes, list) or len(closes) != 505 or any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or p <= 0 for p in closes):
        raise ValueError('invalid_close_history')
    logs = [math.log(p) for p in closes]
    def standardize(current, prior, label):
        mean = sum(prior) / len(prior)
        sd = math.sqrt(sum((x-mean)**2 for x in prior) / len(prior))
        if not all(math.isfinite(x) for x in (current, mean, sd)) or sd <= 1e-12:
            raise ValueError('degenerate_' + label + '_normalizer')
        return (current-mean) / sd
    features = {}
    for h in (21, 63, 252):
        features[f'ret_{h}d_z'] = standardize(logs[504]-logs[504-h], [logs[u]-logs[u-h] for u in range(252,504)], f'ret_{h}d')
    returns = [0] + [logs[u]-logs[u-1] for u in range(1,505)]
    path = sum(abs(x) for x in returns[484:505])
    if path <= 1e-12:
        raise ValueError('degenerate_efficiency_path')
    efficiency = abs(logs[504]-logs[483]) / path
    if not math.isfinite(efficiency) or efficiency > 1 + 1e-12:
        raise ValueError('invalid_efficiency_ratio')
    features['trend_efficiency'] = min(1, efficiency)
    def rv(u):
        return math.sqrt(sum(r*r for r in returns[u-20:u+1])/21)
    features['vol_regime'] = standardize(rv(504), [rv(u) for u in range(252,504)], 'vol_regime')
    if not all(math.isfinite(x) for x in features.values()):
        raise ValueError('nonfinite_feature')
    return features


if __name__ == '__main__':
    data = sys.stdin.read(65537)
    if len(data) > 65536:
        raise ValueError('input_bound_exceeded')
    try:
        print(json.dumps({'features': compute(json.loads(data))}, allow_nan=False))
    except ValueError as error:
        print(json.dumps({'error': str(error)}))
