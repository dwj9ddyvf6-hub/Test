"""JavaScript number semantics for line-by-line ports of the users' TypeScript / .mjs sources.

Python floats and JS numbers are the same IEEE-754 doubles, so a port that performs the same operations in the
same order reproduces the source bit for bit. What differs is the library surface; these helpers carry the JS
meaning: Math.round (half toward +infinity, not Python's half-even), Number() coercion, Math.min/max over an
empty list (+/-Infinity), Array.prototype.at, Number.prototype.toFixed (round-half-up on the exact binary value,
like V8)."""
import math
from decimal import ROUND_HALF_UP, Decimal

INF = float("inf")


def js_round(x):
    """Math.round: the integer closest to x, ties toward +infinity (Math.round(-2.5) == -2)."""
    if x is None or not math.isfinite(x):
        return x
    f = math.floor(x)
    return float(f + 1 if x - f >= 0.5 else f)


def num(v):
    """Number(v) when finite, else None (the sources' `num()` helper). None stands for undefined."""
    n = number(v)
    return n if math.isfinite(n) else None


def number(v):
    """Number(v): NaN for undefined (None) / non-numeric strings, 1/0 for booleans."""
    if v is None:
        return float("nan")
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return 0.0
        try:
            return float(s)
        except ValueError:
            return float("nan")
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def truthy(x):
    """JS truthiness for the values our ports see (None = null/undefined)."""
    if x is None or x is False:
        return False
    if isinstance(x, float):
        return not (x != x or x == 0)
    if isinstance(x, (int, str, list, dict, tuple)) and not isinstance(x, bool):
        return x != 0 if isinstance(x, int) else (len(x) > 0 if isinstance(x, str) else True)
    return bool(x)


def jor(x, default):
    """x || default."""
    return x if truthy(x) else default


def gt(a, b):
    """a > b with JS null/undefined/NaN semantics for our ports: None (undefined) compares false."""
    return a is not None and b is not None and a > b


def lsum(xs, start=0):
    """Array.prototype.reduce((a, b) => a + b, start): a plain left fold. Python's sum() of floats compensates
    rounding (Neumaier, 3.12+) and can differ from JavaScript in the last bit."""
    acc = start
    for x in xs:
        acc = acc + x
    return acc


def jmin(xs):
    xs = list(xs)
    return min(xs) if xs else INF


def jmax(xs):
    xs = list(xs)
    return max(xs) if xs else -INF


def at(xs, i):
    """Array.prototype.at: None (undefined) when out of range."""
    n = len(xs)
    j = i + n if i < 0 else i
    return xs[j] if 0 <= j < n else None


def to_fixed(x, digits=2):
    """Number.prototype.toFixed: decimal rounding of the exact binary value, half away from zero."""
    d = Decimal(x).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    s = format(d, "f")
    return s


def js_str(x):
    """String(x) for numbers (template-literal interpolation): integral values print without '.0', exponents
    like JS (1e+21, 1e-7)."""
    if x is None:
        return "undefined"
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, str):
        return x
    x = float(x)
    if x != x:
        return "NaN"
    if x in (INF, -INF):
        return "Infinity" if x > 0 else "-Infinity"
    if x == 0:
        return "0"
    if x.is_integer() and abs(x) < 1e21:
        return str(int(x))
    r = repr(x)
    if "e" in r:
        mant, exp = r.split("e")
        e = int(exp)
        if -7 < e < 21:
            from decimal import Decimal as _D
            return format(_D(r), "f")
        return f"{mant}e{'+' if e > 0 else '-'}{abs(e)}"
    return r


def round2(x):
    """Math.round(x * 100) / 100."""
    return js_round(x * 100) / 100
