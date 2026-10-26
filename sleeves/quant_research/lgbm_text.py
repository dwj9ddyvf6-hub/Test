"""LightGBM text-model inference without lightgbm (not installed): parses a saved model.txt (version v4, regression,
numerical splits) and predicts exactly as LightGBM's Tree::Predict does -- per tree from the root, a numerical node
compares the feature (as double; NaN -> 0 unless the node's missing type is NaN; zero-as-missing for missing type
Zero) with its threshold (<= goes left) and sends missing values to the default side; the prediction is the sum of
the leaf values over all saved trees (a model saved after early stopping holds its best iteration's trees)."""
import numpy as np


class Tree:
    __slots__ = ("feat", "thr", "dtype", "left", "right", "leaf", "num_leaves")

    def __init__(self, d):
        self.num_leaves = int(d["num_leaves"])
        if self.num_leaves > 1:
            self.feat = np.array(d["split_feature"].split(), dtype=np.int64)
            self.thr = np.array(d["threshold"].split(), dtype=np.float64)
            self.dtype = np.array(d["decision_type"].split(), dtype=np.int64)
            self.left = np.array(d["left_child"].split(), dtype=np.int64)
            self.right = np.array(d["right_child"].split(), dtype=np.int64)
            if (self.dtype & 1).any():
                raise ValueError("categorical splits are not supported")
        self.leaf = np.array(d["leaf_value"].split(), dtype=np.float64)

    def predict(self, X):
        n = X.shape[0]
        if self.num_leaves == 1:
            return np.full(n, self.leaf[0])
        node = np.zeros(n, dtype=np.int64)
        active = np.ones(n, dtype=bool)
        out = np.empty(n)
        rows = np.arange(n)
        while active.any():
            idx = rows[active]
            k = node[idx]
            f = self.feat[k]
            x = X[idx, f].astype(np.float64)
            dt = self.dtype[k]
            missing_type = (dt >> 2) & 3
            default_left = (dt & 2) != 0
            nan = np.isnan(x)
            x = np.where(nan & (missing_type != 2), 0.0, x)
            is_missing = ((missing_type == 1) & (np.abs(x) <= 1e-35)) | ((missing_type == 2) & np.isnan(x))
            go_left = np.where(is_missing, default_left, x <= self.thr[k])
            nxt = np.where(go_left, self.left[k], self.right[k])
            leaf = nxt < 0
            out[idx[leaf]] = self.leaf[~nxt[leaf]]
            active[idx[leaf]] = False
            node[idx[~leaf]] = nxt[~leaf]
        return out


class Model:
    def __init__(self, text):
        blocks = text.split("\nTree=")
        head = dict(line.split("=", 1) for line in blocks[0].splitlines() if "=" in line)
        if head.get("version") != "v4" or head.get("objective", "").split()[0] != "regression":
            raise ValueError("only v4 regression models are supported")
        self.feature_names = head["feature_names"].split()
        self.trees = []
        for b in blocks[1:]:
            body = b.split("\nend of trees")[0]
            d = dict(line.split("=", 1) for line in body.splitlines()[1:] if "=" in line)
            self.trees.append(Tree(d))

    @classmethod
    def load(cls, path):
        return cls(open(path).read())

    def predict(self, X):
        X = np.asarray(X)
        total = np.zeros(X.shape[0])
        for t in self.trees:
            total = total + t.predict(X)
        return total
