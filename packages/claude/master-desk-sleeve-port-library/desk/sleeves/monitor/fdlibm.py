"""V8's Math.exp / Math.log / Math.log1p / Math.pow (and the ** operator), bit for bit.

V8 computes these with its ports of fdlibm (src/base/ieee754.cc, V8 12.4 as in node 22 — including V8's own
deviations: exp(1) returns E exactly; pow's final step divides by ((t1 - 2) - (w + z*w))); glibc's libm — what Python's math module calls —
is a different implementation and differs in the last bit for a few percent of arguments (measured: exp ~10%, log
~5%, pow(x, 1.5) ~7%; glibc pow(x, 2) even differs from x * x, which V8 returns exactly). A port that must
reproduce a JavaScript source's numbers uses these instead (desk/sleeves/monitor/js.py re-exports them).
Validated against node on random arguments by tests/test_fdlibm.py."""
import math
import struct

_pack, _unpack = struct.Struct("<d").pack, struct.Struct("<d").unpack
_q = struct.Struct("<Q")


def _words(x):
    b = _q.unpack(_pack(x))[0]
    return (b >> 32) & 0xFFFFFFFF, b & 0xFFFFFFFF


def _from_words(hi, lo):
    return _unpack(_q.pack(((hi & 0xFFFFFFFF) << 32) | (lo & 0xFFFFFFFF)))[0]


def _hi(x):
    h = _words(x)[0]
    return h - (1 << 32) if h & 0x80000000 else h        # signed high word


def _lo(x):
    return _words(x)[1]


def _set_hi(x, hi):
    return _from_words(hi, _words(x)[1])


def _set_lo(x, lo):
    return _from_words(_words(x)[0], lo)


INF = float("inf")
NAN = float("nan")


def _div(a, b):
    """IEEE division (x / 0 -> signed infinity, 0 / 0 -> NaN) where C relied on it."""
    if b == 0.0:
        if a != a or a == 0.0:
            return NAN
        return INF if (math.copysign(1.0, a) > 0) == (math.copysign(1.0, b) > 0) else -INF
    return a / b

# -- exp (e_exp.c) ------------------------------------------------------------------------------------------------
_HALF = (0.5, -0.5)
_HUGE = 1.0e+300
_TWOM1000 = 9.33263618503218878990e-302
_O_THRESHOLD = 7.09782712893383973096e+02
_U_THRESHOLD = -7.45133219101941108420e+02
_LN2HI = (6.93147180369123816490e-01, -6.93147180369123816490e-01)
_LN2LO = (1.90821492927058770002e-10, -1.90821492927058770002e-10)
_INVLN2 = 1.44269504088896338700e+00
_P1 = 1.66666666666666019037e-01
_P2 = -2.77777777770155933842e-03
_P3 = 6.61375632143793436117e-05
_P4 = -1.65339022054652515390e-06
_P5 = 4.13813679705723846039e-08


def exp(x):
    x = float(x)
    hx = _words(x)[0]
    xsb = (hx >> 31) & 1
    hx &= 0x7FFFFFFF
    if hx >= 0x40862E42:
        if hx >= 0x7FF00000:
            if ((hx & 0xFFFFF) | _lo(x)) != 0:
                return x + x
            return x if xsb == 0 else 0.0
        if x > _O_THRESHOLD:
            return INF
        if x < _U_THRESHOLD:
            return 0.0
    k = 0
    hi = lo = 0.0
    if hx > 0x3FD62E42:
        if hx < 0x3FF0A2B2:
            if x == 1.0:                      # V8: exp(1) is special-cased to return E exactly
                return 2.718281828459045
            hi = x - _LN2HI[xsb]
            lo = _LN2LO[xsb]
            k = 1 - xsb - xsb
        else:
            k = int(_INVLN2 * x + _HALF[xsb])
            t = float(k)
            hi = x - t * _LN2HI[0]
            lo = t * _LN2LO[0]
        x = hi - lo
    elif hx < 0x3E300000:
        if _HUGE + x > 1.0:
            return 1.0 + x
    else:
        k = 0
    t = x * x
    c = x - t * (_P1 + t * (_P2 + t * (_P3 + t * (_P4 + t * _P5))))
    if k == 0:
        return 1.0 - ((x * c) / (c - 2.0) - x)
    y = 1.0 - ((lo - (x * c) / (2.0 - c)) - hi)
    if k >= -1021:
        return _set_hi(y, _words(y)[0] + (k << 20))
    y = _set_hi(y, _words(y)[0] + ((k + 1000) << 20))
    return y * _TWOM1000


# -- log (e_log.c) --------------------------------------------------------------------------------------------------
_LN2_HI = 6.93147180369123816490e-01
_LN2_LO = 1.90821492927058770002e-10
_TWO54 = 1.80143985094819840000e+16
_LG1 = 6.666666666666735130e-01
_LG2 = 3.999999999940941908e-01
_LG3 = 2.857142874366239149e-01
_LG4 = 2.222219843214978396e-01
_LG5 = 1.818357216161805012e-01
_LG6 = 1.531383769920937332e-01
_LG7 = 1.479819860511658591e-01


def log(x):
    x = float(x)
    hx = _hi(x)
    lx = _lo(x)
    k = 0
    if hx < 0x00100000:
        if ((hx & 0x7FFFFFFF) | lx) == 0:
            return -INF
        if hx < 0:
            return NAN
        k -= 54
        x *= _TWO54
        hx = _hi(x)
    if hx >= 0x7FF00000:
        return x + x
    k += (hx >> 20) - 1023
    hx &= 0x000FFFFF
    i = (hx + 0x95F64) & 0x100000
    x = _set_hi(x, hx | (i ^ 0x3FF00000))
    k += i >> 20
    f = x - 1.0
    if (0x000FFFFF & (2 + hx)) < 3:
        if f == 0.0:
            if k == 0:
                return 0.0
            dk = float(k)
            return dk * _LN2_HI + dk * _LN2_LO
        R = f * f * (0.5 - 0.33333333333333333 * f)
        if k == 0:
            return f - R
        dk = float(k)
        return dk * _LN2_HI - ((R - dk * _LN2_LO) - f)
    s = f / (2.0 + f)
    dk = float(k)
    z = s * s
    i = hx - 0x6147A
    w = z * z
    j = 0x6B851 - hx
    t1 = w * (_LG2 + w * (_LG4 + w * _LG6))
    t2 = z * (_LG1 + w * (_LG3 + w * (_LG5 + w * _LG7)))
    i |= j
    R = t2 + t1
    if i > 0:
        hfsq = 0.5 * f * f
        if k == 0:
            return f - (hfsq - s * (hfsq + R))
        return dk * _LN2_HI - ((hfsq - (s * (hfsq + R) + dk * _LN2_LO)) - f)
    if k == 0:
        return f - s * (f - R)
    return dk * _LN2_HI - ((s * (f - R) - dk * _LN2_LO) - f)


# -- log1p (s_log1p.c) ----------------------------------------------------------------------------------------------
_TWO54b = 1.80143985094819840000e+16
_Lp1 = 6.666666666666735130e-01
_Lp2 = 3.999999999940941908e-01
_Lp3 = 2.857142874366239149e-01
_Lp4 = 2.222219843214978396e-01
_Lp5 = 1.818357216161805012e-01
_Lp6 = 1.531383769920937332e-01
_Lp7 = 1.479819860511658591e-01


def log1p(x):
    x = float(x)
    hx = _hi(x)
    ax = hx & 0x7FFFFFFF
    k = 1
    f = c = 0.0
    hu = 0
    if hx < 0x3FDA827A:                       # 1+x < sqrt(2)+
        if ax >= 0x3FF00000:                  # x <= -1.0
            if x == -1.0:
                return -INF
            return NAN
        if ax < 0x3E200000:                   # |x| < 2**-29
            if _TWO54b + x > 0.0 and ax < 0x3C900000:
                return x
            return x - x * x * 0.5
        if hx > 0 or hx <= -1076707644:       # (int) 0xbfd2bec4: sqrt(2)/2- <= 1+x < sqrt(2)+
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
    if hu == 0:                               # |f| < 2**-20
        if f == 0.0:
            if k == 0:
                return 0.0
            c += k * _LN2_LO
            return k * _LN2_HI + c
        R = hfsq * (1.0 - 0.66666666666666666 * f)
        if k == 0:
            return f - R
        return k * _LN2_HI - ((R - (k * _LN2_LO + c)) - f)
    s = f / (2.0 + f)
    z = s * s
    R = z * (_Lp1 + z * (_Lp2 + z * (_Lp3 + z * (_Lp4 + z * (_Lp5 + z * (_Lp6 + z * _Lp7))))))
    if k == 0:
        return f - (hfsq - s * (hfsq + R))
    return k * _LN2_HI - ((hfsq - (s * (hfsq + R) + (k * _LN2_LO + c))) - f)


# -- pow (e_pow.c) ----------------------------------------------------------------------------------------------------
_BP = (1.0, 1.5)
_DP_H = (0.0, 5.84962487220764160156e-01)
_DP_L = (0.0, 1.35003920212974897128e-08)
_TWO53 = 9007199254740992.0
_L1 = 5.99999999999994648725e-01
_L2 = 4.28571428578550184252e-01
_L3 = 3.33333329818377432918e-01
_L4 = 2.72728123808534006489e-01
_L5 = 2.30660745775561754067e-01
_L6 = 2.06975017800338417784e-01
_PP1 = 1.66666666666666019037e-01
_PP2 = -2.77777777770155933842e-03
_PP3 = 6.61375632143793436117e-05
_PP4 = -1.65339022054652515390e-06
_PP5 = 4.13813679705723846039e-08
_PLG2 = 6.93147180559945286227e-01
_PLG2_H = 6.93147182464599609375e-01
_PLG2_L = -1.90465429995776804525e-09
_OVT = 8.0085662595372944372e-17
_CP = 9.61796693925975554329e-01
_CP_H = 9.61796700954437255859e-01
_CP_L = -7.02846165095275826516e-09
_IVLN2 = 1.44269504088896338700e+00
_IVLN2_H = 1.44269502162933349609e+00
_IVLN2_L = 1.92596299112661746887e-08
_HUGEP = 1.0e300
_TINY = 1.0e-300


def _i32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def pow(x, y):
    """V8 Math.pow / **: ES semantics on special values (y NaN -> NaN, |x| = 1 with infinite y -> NaN), fdlibm
    e_pow otherwise."""
    x, y = float(x), float(y)
    if y != y:
        return NAN
    if y == 0.0:
        return 1.0
    if x != x:
        return NAN
    if math.isinf(y) and abs(x) == 1.0:
        return NAN
    hx, lx = _hi(x), _lo(x)
    hy, ly = _hi(y), _lo(y)
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
                j = (ly >> (52 - k)) & 0xFFFFFFFF
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
            return _div(1.0, x) if hy < 0 else x
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
                    z = NAN
                elif yisint == 1:
                    z = -z
            return z
    n = ((hx >> 31) & 0xFFFFFFFF) + 1
    n = _i32(n)
    if (n | yisint) == 0:
        return NAN
    s = 1.0
    if (n | (yisint - 1)) == 0:
        s = -1.0
    if iy > 0x41E00000:
        if iy > 0x43F00000:
            if ix <= 0x3FEFFFFF:
                return _HUGEP * _HUGEP if hy < 0 else _TINY * _TINY
            if ix >= 0x3FF00000:
                return _HUGEP * _HUGEP if hy > 0 else _TINY * _TINY
        if ix < 0x3FEFFFFF:
            return s * _HUGEP * _HUGEP if hy < 0 else s * _TINY * _TINY
        if ix > 0x3FF00000:
            return s * _HUGEP * _HUGEP if hy > 0 else s * _TINY * _TINY
        t = ax - 1.0
        w = (t * t) * (0.5 - t * (0.3333333333333333333333 - t * 0.25))
        u = _IVLN2_H * t
        v = t * _IVLN2_L - w * _IVLN2
        t1 = _set_lo(u + v, 0)
        t2 = v - (t1 - u)
    else:
        n = 0
        if ix < 0x00100000:
            ax *= _TWO53
            n -= 53
            ix = _hi(ax)
        n += ((ix) >> 20) - 0x3FF
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
        u = ax - _BP[k]
        v = 1.0 / (ax + _BP[k])
        ss = u * v
        s_h = _set_lo(ss, 0)
        t_h = _from_words(((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18), 0)
        t_l = ax - (t_h - _BP[k])
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
        z_h = _CP_H * p_h
        z_l = _CP_L * p_h + p_l * _CP + _DP_L[k]
        t = float(n)
        t1 = _set_lo(((z_h + z_l) + _DP_H[k]) + t, 0)
        t2 = z_l - (((t1 - t) - _DP_H[k]) - z_h)
    y1 = _set_lo(y, 0)
    p_l = (y - y1) * t1 + y * t2
    p_h = y1 * t1
    z = p_l + p_h
    j, i = _hi(z), _lo(z)
    if j >= 0x40900000:
        if ((j - 0x40900000) | i) != 0:
            return s * _HUGEP * _HUGEP
        if p_l + _OVT > z - p_h:
            return s * _HUGEP * _HUGEP
    elif (j & 0x7FFFFFFF) >= 0x4090CC00:
        if ((j - _i32(0xC090CC00)) | i) != 0:
            return s * _TINY * _TINY
        if p_l <= z - p_h:
            return s * _TINY * _TINY
    i = j & 0x7FFFFFFF
    k = (i >> 20) - 0x3FF
    n = 0
    if i > 0x3FE00000:
        n = j + (0x00100000 >> (k + 1))
        k = ((n & 0x7FFFFFFF) >> 20) - 0x3FF
        t = _from_words(n & ~(0x000FFFFF >> k), 0)
        n = ((n & 0x000FFFFF) | 0x00100000) >> (20 - k)
        if j < 0:
            n = -n
        p_h -= t
    t = _set_lo(p_l + p_h, 0)
    u = t * _PLG2_H
    v = (p_l - (t - p_h)) * _PLG2 + t * _PLG2_L
    z = u + v
    w = v - (z - u)
    t = z * z
    t1 = z - t * (_PP1 + t * (_PP2 + t * (_PP3 + t * (_PP4 + t * _PP5))))
    r = _div(z * t1, (t1 - 2.0) - (w + z * w))      # V8's grouping (fdlibm: (z*t1)/(t1-2) - (w+z*w))
    z = 1.0 - (r - z)
    j = _hi(z)
    j += (n << 20)
    if (j >> 20) <= 0:
        z = _scalbn(z, n)
    else:
        z = _set_hi(z, j)
    return s * z


def _scalbn(x, n):
    return math.ldexp(x, n)
