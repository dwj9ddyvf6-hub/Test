"""Public-recipe feature engine — recovered and ported (EA2b, 2026-10-15).

PROVENANCE (User's 2026-10-15 10:44 order authorizing the archive
search): the recipe engine the fwd_alpaca_* sleeves were fenced on
(ports/fwd_alpaca_*.md M1, BUGLOG AURELIA-4) was found in the Ausar
archive payload on GitHub — dwj9ddyvf6-hub/Agentic-Trading-Desk branch
aurelia-paper-desk, path
ausar-archive/ausar-receiver/original-payload/desk-source/strategies/
public_recipes/public_source_sleeves.py (sha256
e64c995dd451ac0fd0a32f8a1bcc22624a76362c58d607ee9edecc2d99722e6b),
backed by the Pine sources in the same directory (TOMAZETTI_RSI2.pine
sha256 b8d8e844…, AI_Volume_Strategy.pine sha256 d83e7f59…). The old
desk's own _features (desk/aurelia_alpaca_forward.py, mirrored source
desk/alpaca_forward.py sha256 5b8e9e86…) called exactly:
  core.make_config(strategy, {symbol, market_kind: spot, paper_only,
  params: spec.params}) -> core.source_features(strategy, bars, params)
where `core` is that file (sleeve_history._recipes()).

Ported VERBATIM below: the indicator helpers (sma/ema/rma/rsi/atr),
DEFAULTS, source_features, and the parameter merge of make_config
(unknown params rejected; lengths positive ints). The runtime/state
machine in the same file (step/run_payload, funding, journals) is NOT
ported — the lean sleeves carry their own ported decide() and only
consume {long_signal, long_close_signal, ...} feature dicts.

Bars for source_features are the source shape: dicts with
open_at/close_at (ISO), open/high/low/close/volume — exactly what the
sleeves' own completed_bars() produces from lean bar dicts.
"""
from copy import deepcopy
from datetime import datetime, timezone

STRATEGIES = ('ai_volume', 'iu_body', 'tomazetti_rsi2')
DEFAULTS = {
 'ai_volume': {'volume_ema_length': 20, 'volume_multiplier': 2.,
               'price_ema_length': 50, 'exit_bars': 5},
 'iu_body': {'big_body_threshold': 4., 'atr_length': 14, 'atr_factor': 2.,
             'body_baseline': 'source_inclusive21_div20'},
 'tomazetti_rsi2': {'rsi_length': 2, 'rsi_threshold': 10.,
                    'short_ma_length': 5, 'long_ma_length': 200,
                    'rsi_ma_filter': True, 'rsi_ma_length': 4,
                    'rsi_ma_threshold': 30., 'stop_enabled': False,
                    'stop_percent': 10.,
                    'window_start': '2009-01-02T00:00:00+00:00',
                    'window_end': '2020-12-30T00:00:00+00:00',
                    'source_timezone': 'UTC'}
}


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be explicit ISO string')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError('timestamp needs timezone')
    return d.astimezone(timezone.utc)


def sma(xs, n):
    out = []
    for i in range(len(xs)):
        w = xs[max(0, i - n + 1):i + 1]
        out.append(sum(w) / n if len(w) == n and all(x is not None for x in w) else None)
    return out


def ema(xs, n):
    out = []
    old = None
    a = 2 / (n + 1)
    for x in xs:
        old = x if old is None else a * x + (1 - a) * old
        out.append(old)
    return out


def rma(xs, n):
    out = []
    seed = []
    old = None
    for x in xs:
        if x is None:
            out.append(None)
            continue
        if old is None:
            seed.append(x)
            if len(seed) < n:
                out.append(None)
                continue
            old = sum(seed[-n:]) / n
        else:
            old = (old * (n - 1) + x) / n
        out.append(old)
    return out


def rsi(xs, n):
    gains = [None] + [max(xs[i] - xs[i - 1], 0) for i in range(1, len(xs))]
    losses = [None] + [max(xs[i - 1] - xs[i], 0) for i in range(1, len(xs))]
    g, l = rma(gains, n), rma(losses, n)
    out = []
    for a, b in zip(g, l):
        if a is None or b is None or (a == 0 and b == 0):
            out.append(None)
        elif b == 0:
            out.append(100.)
        elif a == 0:
            out.append(0.)
        else:
            out.append(100 - 100 / (1 + a / b))
    return out


def atr(bars, n):
    tr = []
    for i, b in enumerate(bars):
        tr.append(b['high'] - b['low'] if i == 0 else max(
            b['high'] - b['low'], abs(b['high'] - bars[i - 1]['close']),
            abs(b['low'] - bars[i - 1]['close'])))
    return rma(tr, n)


def source_features(strategy, bars, params):
    """Verbatim from public_source_sleeves.source_features."""
    if not bars:
        return {}
    close = [b['close'] for b in bars]
    b = bars[-1]
    if strategy == 'ai_volume':
        v = ema([b['volume'] for b in bars], params['volume_ema_length'])[-1]
        m = ema(close, params['price_ema_length'])[-1]
        spike = b['volume'] > v * params['volume_multiplier']
        return {'volume_ema': v, 'price_ema': m, 'volume_spike': spike,
                'long_signal': spike and b['close'] > m and b['close'] > b['open'],
                'short_signal': spike and b['close'] < m and b['close'] < b['open']}
    if strategy == 'iu_body':
        bodies = [abs(b['close'] - b['open']) for b in bars]
        if params['body_baseline'] == 'source_inclusive21_div20':
            base = sum(bodies[-21:]) / 20 if len(bodies) >= 21 else None
        elif params['body_baseline'] == 'declared_corrected_prior20':
            base = sum(bodies[-21:-1]) / 20 if len(bodies) >= 21 else None
        else:
            raise ValueError('unknown declared body baseline')
        strong = base is not None and bodies[-1] > base * params['big_body_threshold']
        return {'body': bodies[-1], 'body_baseline': base,
                'atr': atr(bars, params['atr_length'])[-1],
                'long_signal': strong and b['close'] > b['open'],
                'short_signal': strong and b['close'] < b['open']}
    rs = rsi(close, params['rsi_length'])
    short = sma(close, params['short_ma_length'])[-1]
    long = sma(close, params['long_ma_length'])[-1]
    mr = sma(rs, params['rsi_ma_length'])[-1]
    in_window = stamp(params['window_start']) <= stamp(b['open_at']) <= stamp(params['window_end'])
    enter = (in_window and rs[-1] is not None and long is not None
             and rs[-1] < params['rsi_threshold'] and b['close'] > long
             and (not params['rsi_ma_filter']
                  or (mr is not None and mr < params['rsi_ma_threshold'])))
    return {'rsi': rs[-1], 'rsi_average': mr, 'short_ma': short,
            'long_ma': long,
            'source_window_allows_all_strategy_block': in_window,
            'long_signal': enter, 'short_signal': False,
            'long_close_signal': in_window and rs[-1] is not None
            and short is not None and b['close'] > short}


def make_params(strategy, spec_params=None):
    """The parameter half of the source's make_config: DEFAULTS merged
    with the book's declared params; unknown params rejected verbatim."""
    if strategy not in STRATEGIES:
        raise ValueError('unknown strategy')
    params = deepcopy(DEFAULTS[strategy])
    for k, v in (spec_params or {}).items():
        if k not in DEFAULTS[strategy]:
            raise ValueError('unknown source params ' + str(k))
        params[k] = v
    return params


# The two fwd_alpaca books' declared params (source BOOKS in
# desk/alpaca_forward.py, mirrored in the lean sleeves' SPECs).
BOOK_PARAMS = {
    "fwd_alpaca_ada_rsi2": ("tomazetti_rsi2", {
        "window_start": "2023-12-01T00:00:00+00:00",
        "window_end": "2099-01-01T00:00:00+00:00"}),
    "fwd_alpaca_link_ai_volume": ("ai_volume", {}),
}
