"""The AlphaQCM / alphagen expression grammar (ZhuZhouFan/AlphaQCM@dffc695f alphagen/data/expression.py) evaluated in
numpy float32, with the reconstruction's day normalisation (alphagen/utils/pytorch_utils.normalize_by_day) and its
causal mask (alphaqcm/train_native.py CachedCalculator).

Semantics follow the torch originals operator by operator: features are the panel's float32 open / close / high /
low / volume / vwap; rolling operators read the window (t-W, t]; Var / Std are unbiased; Med is torch.median's lower
median and is NaN when the window holds a NaN; Max / Min / Greater / Less propagate NaN; WMA weights arange(n) / sum;
EMA alpha = 1 - 2 / (1 + n) with powers n..1; Corr guards variance sums under 1e-6 as the original. The arithmetic is
numpy's: reductions can differ from torch's in the last float32 bit (named in the calling module)."""
import ast

import numpy as np

FEATURES = ("open", "close", "high", "low", "volume", "vwap")
F32 = np.float32


class Node:
    __slots__ = ("op", "args", "dt", "value", "feature")

    def __init__(self, op, args=(), dt=None, value=None, feature=None):
        self.op, self.args, self.dt, self.value, self.feature = op, tuple(args), dt, value, feature

    def __str__(self):
        if self.op == "Feature":
            return "$" + self.feature
        if self.op == "Constant":
            return f"Constant({self.value})"
        inner = ",".join(str(a) for a in self.args)
        return f"{self.op}({inner}{',' + str(self.dt) if self.dt is not None else ''})"

    def backtrack(self):
        """rows of history this expression needs before the first evaluated row."""
        if self.op in ("Feature", "Constant"):
            return 0
        b = max((a.backtrack() for a in self.args), default=0)
        if self.op in ROLLING or self.op in PAIR:
            return b + self.dt - 1
        if self.op in ("Ref", "Delta"):
            return b + self.dt
        return b


UNARY = {"Abs", "Sign", "Log", "CSRank"}
BINARY = {"Add", "Sub", "Mul", "Div", "Pow", "Greater", "Less"}
ROLLING = {"Mean", "Sum", "Std", "Var", "Skew", "Kurt", "Max", "Min", "Med", "Mad", "Rank", "WMA", "EMA"}
PAIR = {"Cov", "Corr"}
SHIFT = {"Ref", "Delta"}


def parse(text):
    """the public native grammar only (train_native.parse_native_expression's whitelist): calls, names, numbers."""
    tree = ast.parse(text.replace("$", ""), mode="eval")

    def conv(n):
        if isinstance(n, ast.Expression):
            return conv(n.body)
        if isinstance(n, ast.Name):
            if n.id not in FEATURES:
                raise ValueError(f"unknown feature {n.id}")
            return Node("Feature", feature=n.id)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            name = n.func.id
            if name == "Constant":
                (a,) = n.args
                return Node("Constant", value=float(_num(a)))
            args = list(n.args)
            if name in UNARY:
                return Node(name, [_operand(conv, args[0])])
            if name in BINARY:
                return Node(name, [_operand(conv, args[0]), _operand(conv, args[1])])
            if name in ROLLING or name in SHIFT:
                return Node(name, [_operand(conv, args[0])], dt=int(_num(args[1])))
            if name in PAIR:
                return Node(name, [_operand(conv, args[0]), _operand(conv, args[1])], dt=int(_num(args[2])))
        raise ValueError(f"unsupported grammar: {ast.dump(n)[:120]}")
    return conv(tree)


def _num(a):
    if isinstance(a, ast.Constant) and isinstance(a.value, (int, float)) and not isinstance(a.value, bool):
        return a.value
    if isinstance(a, ast.UnaryOp) and isinstance(a.op, ast.USub):
        return -_num(a.operand)
    raise ValueError("number expected")


def _operand(conv, a):
    if isinstance(a, (ast.Constant, ast.UnaryOp)):
        return Node("Constant", value=float(_num(a)))
    return conv(a)


def _windows(v, w):
    """(L+W-1, S) -> (L, S, W) like torch.Tensor.unfold(0, W, 1)."""
    return np.lib.stride_tricks.sliding_window_view(v, w, axis=0)


def evaluate(node, data, lo, hi):
    """rows [lo, hi) of the expression over data (rows, 6 features, stocks) float32."""
    op = node.op
    if lo < 0:
        raise IndexError("out of data range")
    if op == "Feature":
        return data[lo:hi, FEATURES.index(node.feature), :]
    if op == "Constant":
        return np.full((hi - lo, data.shape[2]), node.value, dtype=F32)
    if op in UNARY:
        x = evaluate(node.args[0], data, lo, hi)
        with np.errstate(all="ignore"):
            if op == "Abs":
                return np.abs(x)
            if op == "Sign":
                return np.sign(x)
            if op == "Log":
                return np.log(x)
            if op == "CSRank":
                nan = np.isnan(x)
                n = (~nan).sum(axis=1, keepdims=True)
                r = np.argsort(np.argsort(x, axis=1, kind="stable"), axis=1, kind="stable").astype(F32) / n
                r[nan] = np.nan
                return r.astype(F32)
    if op in BINARY:
        a, b = evaluate(node.args[0], data, lo, hi), evaluate(node.args[1], data, lo, hi)
        with np.errstate(all="ignore"):
            return {"Add": np.add, "Sub": np.subtract, "Mul": np.multiply, "Div": np.divide, "Pow": np.power,
                    "Greater": np.maximum, "Less": np.minimum}[op](a, b).astype(F32, copy=False)
    if op == "Ref":
        return evaluate(node.args[0], data, lo - node.dt, hi - node.dt)
    if op == "Delta":
        v = evaluate(node.args[0], data, lo - node.dt, hi)
        return (v[node.dt:] - v[:-node.dt]).astype(F32, copy=False)
    if op in ROLLING:
        w = node.dt
        x = _windows(evaluate(node.args[0], data, lo - w + 1, hi), w)
        with np.errstate(all="ignore"):
            return _rolling(op, x, w)
    if op in PAIR:
        w = node.dt
        a = _windows(evaluate(node.args[0], data, lo - w + 1, hi), w)
        b = _windows(evaluate(node.args[1], data, lo - w + 1, hi), w)
        with np.errstate(all="ignore"):
            ca = a - a.mean(axis=-1, keepdims=True, dtype=F32)
            cb = b - b.mean(axis=-1, keepdims=True, dtype=F32)
            if op == "Cov":
                return ((ca * cb).sum(axis=-1, dtype=F32) / F32(w - 1)).astype(F32)
            ncov = (ca * cb).sum(axis=-1, dtype=F32)
            nl = (ca ** 2).sum(axis=-1, dtype=F32)
            nr = (cb ** 2).sum(axis=-1, dtype=F32)
            sm = np.sqrt(nl * nr)
            sm[(nl < 1e-6) | (nr < 1e-6)] = 1
            return (ncov / sm).astype(F32)
    raise ValueError(op)


def _rolling(op, x, n):
    if op == "Mean":
        return x.mean(axis=-1, dtype=F32)
    if op == "Sum":
        return x.sum(axis=-1, dtype=F32)
    if op in ("Var", "Std"):
        v = np.var(x.astype(np.float64), axis=-1, ddof=1)
        return (np.sqrt(v) if op == "Std" else v).astype(F32)
    if op == "Skew":
        c = x - x.mean(axis=-1, keepdims=True, dtype=F32)
        return ((c ** 3).mean(axis=-1, dtype=F32) / (c ** 2).mean(axis=-1, dtype=F32) ** F32(1.5)).astype(F32)
    if op == "Kurt":
        c = x - x.mean(axis=-1, keepdims=True, dtype=F32)
        var = np.var(x.astype(np.float64), axis=-1, ddof=1).astype(F32)
        return ((c ** 4).mean(axis=-1, dtype=F32) / var ** 2 - F32(3)).astype(F32)
    if op == "Max":
        return x.max(axis=-1)
    if op == "Min":
        return x.min(axis=-1)
    if op == "Med":
        s = np.sort(x, axis=-1)
        out = s[..., (n - 1) // 2].copy()
        out[np.isnan(x).any(axis=-1)] = np.nan
        return out
    if op == "Mad":
        c = x - x.mean(axis=-1, keepdims=True, dtype=F32)
        return np.abs(c).mean(axis=-1, dtype=F32)
    if op == "Rank":
        last = x[..., -1:]
        left = (last < x).sum(axis=-1)
        right = (last <= x).sum(axis=-1)
        return ((right + left + (right > left)) / (2 * n)).astype(F32)
    if op == "WMA":
        w = np.arange(n, dtype=F32)
        w /= w.sum(dtype=F32)
        return (w * x).sum(axis=-1, dtype=F32)
    if op == "EMA":
        alpha = 1 - 2 / (1 + n)
        w = (F32(alpha) ** np.arange(n, 0, -1, dtype=F32)).astype(F32)
        w /= w.sum(dtype=F32)
        return (w * x).sum(axis=-1, dtype=F32)
    raise ValueError(op)


def normalize_by_day(v):
    """alphagen normalize_by_day: per row, NaN-masked population mean / std; NaN -> 0 after scaling."""
    v = v.astype(F32, copy=True)
    mask = np.isnan(v)
    n = (~mask).sum(axis=1).astype(F32)
    x = v.copy()
    x[mask] = 0
    with np.errstate(all="ignore"):
        mean = x.sum(axis=1, dtype=F32) / n
        std = np.sqrt((((x - mean[:, None]) * ~mask) ** 2).sum(axis=1, dtype=F32) / n)
        out = (v - mean[:, None]) / std[:, None]
    out[np.isnan(out)] = 0
    return out.astype(F32)


def ensemble(nodes, weights, data, eligible, lo, hi):
    """train_native's frozen causal daily score for rows [lo, hi): each factor masked by eligibility (and to NaN where
    non-finite) before normalisation, weighted sum in pool order; ineligible -> NaN."""
    total = 0
    for node, w in zip(nodes, weights):
        v = evaluate(node, data, lo, hi).astype(F32, copy=True)
        v[~eligible[lo:hi]] = np.nan
        v[~np.isfinite(v)] = np.nan
        total = total + normalize_by_day(v) * F32(w) if not isinstance(total, int) else normalize_by_day(v) * F32(w)
    score = np.asarray(total, dtype=F32).copy()
    score[~eligible[lo:hi]] = np.nan
    return score
