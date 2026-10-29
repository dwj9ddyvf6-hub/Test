"""src/lib/tensor/math.ts (Author-desk@652db7af, blob 4add3a71847a6b9a7322b69e2a914ad290247e4a): ema (SMA seed of the
first `length` finite values, a missing print never updates), sma, stdev, wilder, slope, linregEndpoint,
highest / lowest (an index outside the series is a missing value, as JavaScript's undefined), lastFinite, clamp,
nz."""
from .. import js


def _at(values, i):
    return values[i] if 0 <= i < len(values) else None


def ema(values, length):
    out = [None] * len(values)
    if not (length > 0) or len(values) < length:
        return out
    k = 2 / (length + 1)
    prev = None
    seed = 0.0
    count = 0
    for i, v in enumerate(values):
        if v is None or not js.finite(v):
            continue
        if prev is None:
            seed += v
            count += 1
            if count == length:
                prev = seed / length
                out[i] = prev
        else:
            prev = v * k + prev * (1 - k)
            out[i] = prev
    return out


def sma(values, length):
    out = [None] * len(values)
    s = 0.0
    n = 0
    window = []
    for i, v in enumerate(values):
        window.append(v)
        if v is not None:
            s += v
            n += 1
        if len(window) > length:
            old = window.pop(0)
            if old is not None:
                s -= old
                n -= 1
        if len(window) == length and n == length:
            out[i] = s / length
    return out


def stdev(values, length):
    out = [None] * len(values)
    for i in range(length - 1, len(values)):
        s = 0.0
        n = 0
        for j in range(i - length + 1, i + 1):
            v = _at(values, j)
            if v is None:
                n = -1
                break
            s += v
            n += 1
        if n != length:
            continue
        mean = s / length
        acc = 0.0
        for j in range(i - length + 1, i + 1):
            d = values[j] - mean
            acc += d * d
        out[i] = js.sqrt(acc / length)
    return out


def wilder(values, length):
    out = [None] * len(values)
    prev = None
    seed = 0.0
    count = 0
    for i, v in enumerate(values):
        if v is None:
            continue
        if prev is None:
            seed += v
            count += 1
            if count == length:
                prev = seed / length
                out[i] = prev
        else:
            prev = (prev * (length - 1) + v) / length
            out[i] = prev
    return out


def slope(values, lookback, i):
    a = _at(values, i)
    b = _at(values, i - lookback)
    if a is None or b is None:
        return None
    return a - b


def linreg_endpoint(values, length):
    out = [None] * len(values)
    for i in range(length - 1, len(values)):
        sx = sy = sxy = sxx = 0.0
        ok = True
        x0 = (length - 1) / 2
        for k in range(length):
            y = _at(values, i - length + 1 + k)
            if y is None:
                ok = False
                break
            x = k - x0
            sx += x
            sy += y
            sxy += x * y
            sxx += x * x
        if not ok:
            continue
        mean_y = sy / length
        cov = sxy / length
        var_x = sxx / length
        beta = 0 if var_x == 0 else cov / var_x
        out[i] = mean_y + beta * ((length - 1) / 2)
    return out


def highest(values, length, i):
    m = -js.INF
    for j in range(i - length + 1, i + 1):
        v = _at(values, j)
        if v is None:
            return None
        if v > m:
            m = v
    return m if js.finite(m) else None


def lowest(values, length, i):
    m = js.INF
    for j in range(i - length + 1, i + 1):
        v = _at(values, j)
        if v is None:
            return None
        if v < m:
            m = v
    return m if js.finite(m) else None


def last_finite(values):
    for v in reversed(values):
        if v is not None and js.finite(v):
            return v
    return None


def clamp(n, a, b):
    return js.js_min(b, js.js_max(a, n))


def nz(v, fallback=0):
    return fallback if (v is None or not js.finite(v)) else v
