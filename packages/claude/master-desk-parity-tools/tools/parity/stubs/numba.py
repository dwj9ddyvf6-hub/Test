"""Harness stand-in for numba (found only when numba is not installed): @njit is a compiler decorator, so the source's
engines run as the same Python code. Not I/O, not a decision."""


def njit(*a, **k):
    if a and callable(a[0]) and not k:
        return a[0]
    return lambda f: f
