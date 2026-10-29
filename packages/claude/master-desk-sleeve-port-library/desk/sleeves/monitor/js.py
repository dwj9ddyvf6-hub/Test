"""JavaScript number semantics the TypeScript/JavaScript sources rely on, reproduced exactly so a port computes
the same values and the same text: Number.prototype.toFixed, String(number), Math.round, Math.max / Math.min
(NaN-propagating, empty = -/+Infinity), IEEE division / sqrt / log (Infinity / NaN, never an exception),
truthiness, Number.isFinite, Array.prototype.sort with a comparator (stable) and the ASCII subset of
String.prototype.localeCompare that ticker symbols use."""
import functools
import math
from decimal import ROUND_HALF_UP, Decimal

from . import fdlibm as _F

NAN = float("nan")
INF = float("inf")


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def finite(x):
    """Number.isFinite: a number that is neither NaN nor +/-Infinity (null / strings / booleans: false)."""
    return is_num(x) and math.isfinite(x)


def truthy(x):
    if x is None or x is False:
        return False
    if x is True:
        return True
    if is_num(x):
        return x == x and x != 0
    if isinstance(x, str):
        return x != ""
    return True


def num(x):
    """Number(x) for the values ports see: null -> 0, undefined (None passed as 'undef') -> NaN, bool -> 0/1."""
    if x is None:
        return 0.0
    if x is True:
        return 1.0
    if x is False:
        return 0.0
    if is_num(x):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if s == "":
            return 0.0
        try:
            return float(s)
        except ValueError:
            return NAN
    return NAN


def div(a, b):
    """a / b with IEEE semantics (x/0 -> +/-Infinity, 0/0 -> NaN)."""
    a, b = float(a), float(b)
    if b == 0.0:
        if a != a or a == 0.0:
            return NAN
        neg = (a < 0) != (math.copysign(1.0, b) < 0)
        return -INF if neg else INF
    return a / b


def sqrt(x):
    x = float(x)
    if x != x or x < 0:
        return NAN
    return math.sqrt(x)


def log(x):
    """Math.log (V8's fdlibm port: bit-identical to node; glibc differs in the last bit for ~5% of arguments)."""
    return _F.log(float(x))


def exp(x):
    """Math.exp (V8's fdlibm port)."""
    return _F.exp(float(x))


def log1p(x):
    """Math.log1p (V8's fdlibm port)."""
    return _F.log1p(float(x))


def pow(x, y):
    """Math.pow and the ** operator (V8's fdlibm port; x ** 2 is exactly x * x in V8, not glibc's pow)."""
    return _F.pow(float(x), float(y))


def js_round(x):
    """Math.round: nearest integer, ties toward +Infinity (Math.round(-2.5) = -2, Math.round(2.5) = 3)."""
    x = float(x)
    if x != x or math.isinf(x):
        return x
    r = math.floor(x)
    return float(r + 1) if x - r >= 0.5 else float(r)


def js_floor(x):
    """Math.floor (Infinity / NaN pass through)."""
    x = float(x)
    if x != x or math.isinf(x):
        return x
    return float(math.floor(x))


def js_max(*vals):
    if len(vals) == 1 and isinstance(vals[0], (list, tuple)):
        vals = tuple(vals[0])
    out = -INF
    for v in vals:
        v = num(v)
        if v != v:
            return NAN
        if v > out or (v == 0 and out == 0 and math.copysign(1.0, out) < 0):
            out = v
    return out


def js_min(*vals):
    if len(vals) == 1 and isinstance(vals[0], (list, tuple)):
        vals = tuple(vals[0])
    out = INF
    for v in vals:
        v = num(v)
        if v != v:
            return NAN
        if v < out or (v == 0 and out == 0 and math.copysign(1.0, v) < 0):
            out = v
    return out


def to_fixed(x, digits=0):
    """Number.prototype.toFixed: exact binary value rounded half-up on the magnitude; |x| >= 1e21 -> String(x)."""
    x = float(x)
    if x != x:
        return "NaN"
    if abs(x) >= 1e21 or math.isinf(x):
        return num_str(x)
    neg = x < 0
    d = Decimal(abs(x)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    s = format(d, "f")
    if digits > 0 and "." not in s:
        s += "." + "0" * digits
    return ("-" + s) if neg else s


def num_str(x):
    """String(number) / template-literal interpolation of a number (ECMAScript Number::toString)."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        x = float(x)
    if x != x:
        return "NaN"
    if math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    if x == 0:
        return "0"
    neg = x < 0
    t = Decimal(repr(abs(x))).normalize().as_tuple()
    digits = "".join(str(d) for d in t.digits)
    k = len(digits)
    n = t.exponent + k                      # value = 0.digits x 10^n
    if k <= n <= 21:
        s = digits + "0" * (n - k)
    elif 0 < n <= 21:
        s = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        s = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        s = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return ("-" + s) if neg else s


def tstr(x):
    """`${x}` for the value kinds the sources interpolate (numbers, strings, null, booleans)."""
    if x is None:
        return "null"
    if isinstance(x, str):
        return x
    return num_str(x)


def sort(items, cmp):
    """Array.prototype.sort(comparator): stable; comparator result coerced like V8 (NaN / 0 = equal)."""
    def c(a, b):
        r = cmp(a, b)
        r = num(r)
        if r != r or r == 0:
            return 0
        return -1 if r < 0 else 1
    return sorted(items, key=functools.cmp_to_key(c))


_PUNCT = "_-,;:!?.'\"()[]{}@*/\\&#%`^+<=>|~$"


def _lc_key(ch):
    if ch.isdigit():
        return (2, ord(ch), 0)
    if ch.isalpha():
        return (3, ord(ch.lower()), 0 if ch.islower() else 1)
    i = _PUNCT.find(ch)
    return (1, i if i >= 0 else 100 + ord(ch), 0)


def locale_compare(a, b):
    """String.prototype.localeCompare (ICU root collation) on the ASCII strings the sources compare (tickers):
    punctuation < digits < letters, letters case-insensitive at the primary level, lower case first on a tie."""
    pa = [_lc_key(c)[:2] for c in a]
    pb = [_lc_key(c)[:2] for c in b]
    if pa != pb:
        return -1 if pa < pb else 1
    ta = [_lc_key(c)[2] for c in a]
    tb = [_lc_key(c)[2] for c in b]
    if ta != tb:
        return -1 if ta < tb else 1
    return 0


def json_str(s):
    """JSON.stringify(string)."""
    import json
    return json.dumps(s, ensure_ascii=False)


def stringify(v):
    """JSON.stringify for the plain data the sources hash (null / bool / number / string / array / object in
    insertion order; non-finite numbers -> null)."""
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if is_num(v):
        return num_str(v) if math.isfinite(v) else "null"
    if isinstance(v, str):
        return json_str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(stringify(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(json_str(k) + ":" + stringify(x) for k, x in v.items()) + "}"
    raise TypeError(type(v))


def stable_normalize(v):
    """stable-hash.ts normalize: object keys ordered by localeCompare, non-finite numbers -> null."""
    if isinstance(v, (list, tuple)):
        return [stable_normalize(x) for x in v]
    if isinstance(v, dict):
        keys = sort(list(v.keys()), locale_compare)
        return {k: stable_normalize(v[k]) for k in keys}
    if is_num(v) and not math.isfinite(v):
        return None
    return v


def stable_hash(v):
    """stable-hash.ts stableHash: sha256 hex of JSON.stringify(normalize(value))."""
    import hashlib
    return hashlib.sha256(stringify(stable_normalize(v)).encode("utf-8")).hexdigest()


def iso_ms(ms):
    """new Date(ms).toISOString()."""
    from datetime import datetime, timezone
    ms = int(ms)
    d = datetime.fromtimestamp(ms // 1000, tz=timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S") + ".%03dZ" % (ms % 1000)


def parse_iso_ms(s):
    """Date.parse of an ISO-8601 'Z' timestamp -> epoch ms (NaN when unparseable)."""
    from datetime import datetime
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp() * 1000.0
    except (TypeError, ValueError):
        return NAN


def jsum(vals, start=0.0):
    """values.reduce((s, v) => s + v, start): naive left-to-right addition. Python >= 3.12 sum() compensates
    float rounding (Neumaier) and would not reproduce JavaScript's result bit for bit."""
    s = start
    for v in vals:
        s = s + v
    return s


def mean(vals):
    return jsum(vals) / len(vals) if vals else NAN
