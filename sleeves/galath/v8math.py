"""V8's Math.log / Math.exp / Math.log1p / Math.pow (and `**`), bit for bit.

V8 (Node 22, V8 12.4) computes these with its own fdlibm ports (src/base/ieee754.cc); the C library Python's math
module calls (glibc) rounds differently in the last bit for a few percent of arguments (measured: log 3.8%, exp
9.8%, pow 8.9%, even x ** 2 0.7%). A line-by-line port of TypeScript that must reproduce the source's numbers
exactly uses these instead of math.log / math.exp / math.log1p / ** / math.pow. Proved against Node 22 on random
arguments in tests/test_v8math.py (and every galath parity harness that reaches them)."""
import math
import struct

_INF = float("inf")
_NAN = float("nan")


def _words(x):
    b = struct.unpack("<Q", struct.pack("<d", x))[0]
    hi = (b >> 32) & 0xFFFFFFFF
    lo = b & 0xFFFFFFFF
    return (hi - (1 << 32) if hi & 0x80000000 else hi), lo     # signed high word, unsigned low word


def _hi(x):
    return _words(x)[0]


def _from(hi, lo):
    return struct.unpack("<d", struct.pack("<Q", ((hi & 0xFFFFFFFF) << 32) | (lo & 0xFFFFFFFF)))[0]


def _set_hi(x, hi):
    return _from(hi, _words(x)[1])


def _set_lo(x, lo):
    return _from(_words(x)[0], lo)


def _i32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


# -- log --------------------------------------------------------------------------------------------------------------
_ln2_hi = 6.93147180369123816490e-01
_ln2_lo = 1.90821492927058770002e-10
_two54 = 1.80143985094819840000e+16
_Lg1 = 6.666666666666735130e-01
_Lg2 = 3.999999999940941908e-01
_Lg3 = 2.857142874366239149e-01
_Lg4 = 2.222219843214978396e-01
_Lg5 = 1.818357216161805012e-01
_Lg6 = 1.531383769920937332e-01
_Lg7 = 1.479819860511658591e-01


def log(x):
    x = float(x)
    hx, lx = _words(x)
    k = 0
    if hx < 0x00100000:
        if ((hx & 0x7FFFFFFF) | lx) == 0:
            return -_INF
        if hx < 0:
            return _NAN
        k -= 54
        x *= _two54
        hx = _hi(x)
    if hx >= 0x7FF00000:
        return x + x
    k += (hx >> 20) - 1023
    hx &= 0x000FFFFF
    i = (hx + 0x95F64) & 0x100000
    x = _set_hi(x, hx | (i ^ 0x3FF00000))
    k += (i >> 20)
    f = x - 1.0
    if (0x000FFFFF & (2 + hx)) < 3:
        if f == 0.0:
            if k == 0:
                return 0.0
            dk = float(k)
            return dk * _ln2_hi + dk * _ln2_lo
        R = f * f * (0.5 - 0.33333333333333333 * f)
        if k == 0:
            return f - R
        dk = float(k)
        return dk * _ln2_hi - ((R - dk * _ln2_lo) - f)
    s = f / (2.0 + f)
    dk = float(k)
    z = s * s
    i = hx - 0x6147A
    w = z * z
    j = 0x6B851 - hx
    t1 = w * (_Lg2 + w * (_Lg4 + w * _Lg6))
    t2 = z * (_Lg1 + w * (_Lg3 + w * (_Lg5 + w * _Lg7)))
    i |= j
    R = t2 + t1
    if i > 0:
        hfsq = 0.5 * f * f
        if k == 0:
            return f - (hfsq - s * (hfsq + R))
        return dk * _ln2_hi - ((hfsq - (s * (hfsq + R) + dk * _ln2_lo)) - f)
    if k == 0:
        return f - s * (f - R)
    return dk * _ln2_hi - ((s * (f - R) - dk * _ln2_lo) - f)


# -- log1p ------------------------------------------------------------------------------------------------------------
def log1p(x):
    x = float(x)
    hx = _hi(x)
    ax = hx & 0x7FFFFFFF
    k = 1
    hu = 0
    c = 0.0
    f = 0.0
    if hx < 0x3FDA827A:
        if ax >= 0x3FF00000:
            if x == -1.0:
                return -_INF
            return _NAN
        if ax < 0x3E200000:
            if _two54 + x > 0.0 and ax < 0x3C900000:
                return x
            return x - x * x * 0.5
        if hx > 0 or hx <= _i32(0xBFD2BEC4):
            k = 0
            f = x
            hu = 1
    if hx >= 0x7FF00000:
        return x + x
    if k != 0:
        if hx < 0x43400000:
            u = 1.0 + x
            hu = _hi(u)
            k = (hu >> 20) - 1023
            c = (1.0 - (u - x)) if k > 0 else (x - (u - 1.0))
            c /= u
        else:
            u = x
            hu = _hi(u)
            k = (hu >> 20) - 1023
            c = 0.0
        hu &= 0x000FFFFF
        if hu < 0x6A09E:
            u = _set_hi(u, hu | 0x3FF00000)
        else:
            k += 1
            u = _set_hi(u, hu | 0x3FE00000)
            hu = (0x00100000 - hu) >> 2
        f = u - 1.0
    hfsq = 0.5 * f * f
    if hu == 0:
        if f == 0.0:
            if k == 0:
                return 0.0
            c += k * _ln2_lo
            return k * _ln2_hi + c
        R = hfsq * (1.0 - 0.66666666666666666 * f)
        if k == 0:
            return f - R
        return k * _ln2_hi - ((R - (k * _ln2_lo + c)) - f)
    s = f / (2.0 + f)
    z = s * s
    R = z * (_Lg1 + z * (_Lg2 + z * (_Lg3 + z * (_Lg4 + z * (_Lg5 + z * (_Lg6 + z * _Lg7))))))
    if k == 0:
        return f - (hfsq - s * (hfsq + R))
    return k * _ln2_hi - ((hfsq - (s * (hfsq + R) + (k * _ln2_lo + c))) - f)


# -- exp --------------------------------------------------------------------------------------------------------------
_halF = (0.5, -0.5)
_o_threshold = 7.09782712893383973096e+02
_u_threshold = -7.45133219101941108420e+02
_ln2HI = (6.93147180369123816490e-01, -6.93147180369123816490e-01)
_ln2LO = (1.90821492927058770002e-10, -1.90821492927058770002e-10)
_invln2 = 1.44269504088896338700e+00
_P1 = 1.66666666666666019037e-01
_P2 = -2.77777777770155933842e-03
_P3 = 6.61375632143793436117e-05
_P4 = -1.65339022054652515390e-06
_P5 = 4.13813679705723846039e-08
_E = 2.718281828459045
_huge = 1.0e+300
_twom1000 = 9.33263618503218878990e-302
_two1023 = 8.988465674311579539e307


def exp(x):
    x = float(x)
    hx = _hi(x) & 0xFFFFFFFF
    xsb = (hx >> 31) & 1
    hx &= 0x7FFFFFFF
    hi = lo = 0.0
    k = 0
    if hx >= 0x40862E42:
        if hx >= 0x7FF00000:
            lx = _words(x)[1]
            if ((hx & 0xFFFFF) | lx) != 0:
                return x + x
            return x if xsb == 0 else 0.0
        if x > _o_threshold:
            return _INF
        if x < _u_threshold:
            return 0.0
    if hx > 0x3FD62E42:
        if hx < 0x3FF0A2B2:
            if x == 1.0:
                return _E
            hi = x - _ln2HI[xsb]
            lo = _ln2LO[xsb]
            k = 1 - xsb - xsb
        else:
            k = int(_invln2 * x + _halF[xsb])        # C truncation toward zero
            t = float(k)
            hi = x - t * _ln2HI[0]
            lo = t * _ln2LO[0]
        x = hi - lo
    elif hx < 0x3E300000:
        if _huge + x > 1.0:
            return 1.0 + x
    else:
        k = 0
    t = x * x
    if k >= -1021:
        twopk = _from(0x3FF00000 + _i32((k & 0xFFFFFFFF) << 20), 0)
    else:
        twopk = _from(0x3FF00000 + ((((k + 1000) & 0xFFFFFFFF) << 20) & 0xFFFFFFFF), 0)
    c = x - t * (_P1 + t * (_P2 + t * (_P3 + t * (_P4 + t * _P5))))
    if k == 0:
        return 1.0 - ((x * c) / (c - 2.0) - x)
    y = 1.0 - ((lo - (x * c) / (2.0 - c)) - hi)
    if k >= -1021:
        if k == 1024:
            return y * 2.0 * _two1023
        return y * twopk
    return y * twopk * _twom1000


# -- pow --------------------------------------------------------------------------------------------------------------
_bp = (1.0, 1.5)
_dp_h = (0.0, 5.84962487220764160156e-01)
_dp_l = (0.0, 1.35003920212974897128e-08)
_two53 = 9007199254740992.0
_tiny = 1.0e-300
_L1 = 5.99999999999994648725e-01
_L2 = 4.28571428578550184252e-01
_L3 = 3.33333329818377432918e-01
_L4 = 2.72728123808534006489e-01
_L5 = 2.30660745775561754067e-01
_L6 = 2.06975017800338417784e-01
_lg2 = 6.93147180559945286227e-01
_lg2_h = 6.93147182464599609375e-01
_lg2_l = -1.90465429995776804525e-09
_ovt = 8.0085662595372944372e-0017
_cp = 9.61796693925975554329e-01
_cp_h = 9.61796700954437255859e-01
_cp_l = -7.02846165095275826516e-09
_ivln2 = 1.44269504088896338700e+00
_ivln2_h = 1.44269502162933349609e+00
_ivln2_l = 1.92596299112661746887e-08


def _div(a, b):
    """base::Divide: IEEE division (x / 0 = +-inf or NaN, not an exception)."""
    try:
        return a / b
    except ZeroDivisionError:
        if a != a or a == 0:
            return _NAN
        neg = (math.copysign(1.0, a) < 0) != (math.copysign(1.0, b) < 0)
        return -_INF if neg else _INF


def _mul(*xs):
    """left-to-right product with IEEE overflow to +-inf (Python floats raise nothing on overflow in *)."""
    r = xs[0]
    for v in xs[1:]:
        r = r * v
    return r


def pow(x, y):
    x, y = float(x), float(y)
    hx, lx = _words(x)
    hy, ly = _words(y)
    ix = hx & 0x7FFFFFFF
    iy = hy & 0x7FFFFFFF
    if (iy | ly) == 0:
        return 1.0
    if ix > 0x7FF00000 or (ix == 0x7FF00000 and lx != 0) or iy > 0x7FF00000 or (iy == 0x7FF00000 and ly != 0):
        return x + y
    yisint = 0
    if hx < 0:
        if iy >= 0x43400000:
            yisint = 2
        elif iy >= 0x3FF00000:
            k = (iy >> 20) - 0x3FF
            if k > 20:
                j = ly >> (52 - k)
                if ((j << (52 - k)) & 0xFFFFFFFF) == ly:
                    yisint = 2 - (j & 1)
            elif ly == 0:
                j = iy >> (20 - k)
                if (j << (20 - k)) == iy:
                    yisint = 2 - (j & 1)
    if ly == 0:
        if iy == 0x7FF00000:
            if ((ix - 0x3FF00000) | lx) == 0:
                return y - y
            if ix >= 0x3FF00000:
                return y if hy >= 0 else 0.0
            return -y if hy < 0 else 0.0
        if iy == 0x3FF00000:
            if hy < 0:
                return _div(1.0, x)
            return x
        if hy == 0x40000000:
            return x * x
        if hy == 0x3FE00000:
            if hx >= 0:
                return math.sqrt(x)
    ax = abs(x)
    if lx == 0:
        if ix == 0x7FF00000 or ix == 0 or ix == 0x3FF00000:
            z = ax
            if hy < 0:
                z = _div(1.0, z)
            if hx < 0:
                if ((ix - 0x3FF00000) | yisint) == 0:
                    z = _NAN
                elif yisint == 1:
                    z = -z
            return z
    n = (hx >> 31) + 1        # arithmetic shift of the signed high word: -1 for x < 0, so n = 0 / 1
    if (n | yisint) == 0:
        return _NAN
    s = 1.0
    if (n | (yisint - 1)) == 0:
        s = -1.0
    if iy > 0x41E00000:
        if iy > 0x43F00000:
            if ix <= 0x3FEFFFFF:
                return _INF if hy < 0 else 0.0
            if ix >= 0x3FF00000:
                return _INF if hy > 0 else 0.0
        if ix < 0x3FEFFFFF:
            return s * _INF if hy < 0 else s * 0.0
        if ix > 0x3FF00000:
            return s * _INF if hy > 0 else s * 0.0
        t = ax - 1.0
        w = (t * t) * (0.5 - t * (0.3333333333333333333333 - t * 0.25))
        u = _ivln2_h * t
        v = t * _ivln2_l - w * _ivln2
        t1 = _set_lo(u + v, 0)
        t2 = v - (t1 - u)
    else:
        n = 0
        if ix < 0x00100000:
            ax *= _two53
            n -= 53
            ix = _hi(ax)
        n += (ix >> 20) - 0x3FF
        j = ix & 0x000FFFFF
        ix = j | 0x3FF00000
        if j <= 0x3988E:
            k = 0
        elif j < 0xBB67A:
            k = 1
        else:
            k = 0
            n += 1
            ix -= 0x00100000
        ax = _set_hi(ax, ix)
        u = ax - _bp[k]
        v = _div(1.0, ax + _bp[k])
        ss = u * v
        s_h = _set_lo(ss, 0)
        t_h = _set_hi(0.0, ((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18))
        t_l = ax - (t_h - _bp[k])
        s_l = v * ((u - s_h * t_h) - s_h * t_l)
        s2 = ss * ss
        r = s2 * s2 * (_L1 + s2 * (_L2 + s2 * (_L3 + s2 * (_L4 + s2 * (_L5 + s2 * _L6)))))
        r += s_l * (s_h + ss)
        s2 = s_h * s_h
        t_h = _set_lo(3.0 + s2 + r, 0)
        t_l = r - ((t_h - 3.0) - s2)
        u = s_h * t_h
        v = s_l * t_h + t_l * ss
        p_h = _set_lo(u + v, 0)
        p_l = v - (p_h - u)
        z_h = _cp_h * p_h
        z_l = _cp_l * p_h + p_l * _cp + _dp_l[k]
        t = float(n)
        t1 = _set_lo((((z_h + z_l) + _dp_h[k]) + t), 0)
        t2 = z_l - (((t1 - t) - _dp_h[k]) - z_h)
    y1 = _set_lo(y, 0)
    p_l = (y - y1) * t1 + y * t2
    p_h = y1 * t1
    z = p_l + p_h
    j, i = _words(z)
    if j >= 0x40900000:
        if ((j - 0x40900000) | i) != 0:
            return s * _INF
        if p_l + _ovt > z - p_h:
            return s * _INF
    elif (j & 0x7FFFFFFF) >= 0x4090CC00:
        if (_i32(j - _i32(0xC090CC00)) | i) != 0:
            return s * 0.0
        if p_l <= z - p_h:
            return s * 0.0
    i = j & 0x7FFFFFFF
    k = (i >> 20) - 0x3FF
    n = 0
    if i > 0x3FE00000:
        n = j + (0x00100000 >> (k + 1))
        k = ((n & 0x7FFFFFFF) >> 20) - 0x3FF
        t = _set_hi(0.0, n & ~(0x000FFFFF >> k))
        n = ((n & 0x000FFFFF) | 0x00100000) >> (20 - k)
        if j < 0:
            n = -n
        p_h -= t
    t = _set_lo(p_l + p_h, 0)
    u = t * _lg2_h
    v = (p_l - (t - p_h)) * _lg2 + t * _lg2_l
    z = u + v
    w = v - (z - u)
    t = z * z
    t1 = z - t * (_P1 + t * (_P2 + t * (_P3 + t * (_P4 + t * _P5))))
    r = _div(z * t1, (t1 - 2.0) - (w + z * w))
    z = 1.0 - (r - z)
    j = _hi(z)
    j = _i32(j + ((n & 0xFFFFFFFF) << 20))
    if (j >> 20) <= 0:
        z = math.ldexp(z, n)           # scalbn: subnormal output
    else:
        z = _set_hi(z, _i32(_hi(z) + ((n & 0xFFFFFFFF) << 20)))
    return s * z
