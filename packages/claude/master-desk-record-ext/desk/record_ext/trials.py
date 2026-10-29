"""V-tradingkit-2 - best-of-N label discipline: a rate taken from the best of N trials prints only with N."""


def stamp(row, n_trials, n_markets=None):
    """-> a copy of the registry row / tile with the search's trial count (and market count) written on it"""
    if not isinstance(n_trials, int) or n_trials < 1:
        raise ValueError("n_trials must be a positive integer")
    out = dict(row)
    out["n_trials"] = n_trials
    if n_markets is not None:
        out["n_markets"] = n_markets
    return out


def label_rate(row, key="rate"):
    """the line a card prints for a search winner's rate: the rate, N trials, M markets. A row without n_trials has no
    printable rate (None)."""
    n = row.get("n_trials")
    if not isinstance(n, int) or n < 1 or row.get(key) is None:
        return None
    m = row.get("n_markets")
    return f"{row[key]:.1%} best of {n} trials" + (f" across {m} markets" if m else "")
