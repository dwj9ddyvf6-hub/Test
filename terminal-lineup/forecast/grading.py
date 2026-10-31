"""The Grading Runner for the Forecast Engines 30 program.

Given the ledger and a price source, it finds matured forecasts, grades
each by its engine's registered rule, appends grade rows to the same
ledger, and recomputes published figures from the ledger alone.

Price source: the shipped daily history file the AI Chart Read uses,
~/workspace/morgue/data_cache/board_bt_bars.json, shaped
{symbol: [[date, open, high, low, close, volume], ...]} (the source of
site/ai-chart-read/data.json; confirmed in the inspect phase).

Registered grading rules (registry.json grading_rules):
- coverage: band hit (realised value inside [lower, upper]) + width
- brier: (p - outcome)^2 for probabilities, plus log_loss
- pinball: pinball loss per stated quantile; CRPS-ready: crps_from_quantiles
  approximates CRPS from the quantile set (2 * mean pinball over quantiles)
- abs_error: |estimate - realised| and signed error for point forecasts
- ranked_probability_score: for tercile/distribution-over-bins forecasts
- survival_brier: timing forecasts graded as Brier on resolved-by-horizon

A forecast is matured only when its horizon_close session exists in the
price source. Grading before maturity is refused.
"""
import json
import math
import os
import statistics

DEFAULT_BARS_PATH = os.path.expanduser(
    "~/workspace/morgue/data_cache/board_bt_bars.json")


class GradingError(Exception):
    pass


class BarsIntegrityError(GradingError):
    """A daily bars payload failed the whole-payload integrity gate
    (BARS-INTEGRITY-20261029, DEEP-PASS 3.1 item 2)."""


MAX_BARS_PER_SYMBOL = 1000


def validate_bars_payload(raw):
    """Whole-payload integrity gate for a daily history payload
    shaped {symbol: [[date, o, h, l, c, v], ...]}. Returns a list of
    named problems (empty when the payload passes): more than
    MAX_BARS_PER_SYMBOL bars for one symbol, a malformed row, a non
    finite or non positive OHLC value, or a duplicate or non
    increasing date. One problem is reported per symbol so a refusal
    message stays bounded. Adopted as is from the new-head Trade
    Brain bars gate (DEEP-PASS Section 2.3 point 10): the payload is
    refused whole, never repaired per row. The pre-cure PriceSource
    load silently overwrote duplicate dates in its dict and accepted
    any values."""
    if not isinstance(raw, dict):
        return ["payload is not a symbol map"]
    problems = []
    for sym, rows in raw.items():
        if not isinstance(rows, list):
            problems.append(f"{sym}: rows are not a list")
            continue
        if len(rows) > MAX_BARS_PER_SYMBOL:
            problems.append(
                f"{sym}: {len(rows)} bars exceeds {MAX_BARS_PER_SYMBOL}")
            continue
        prev = None
        for row in rows:
            try:
                day = str(row[0])
                vals = [float(row[i]) for i in (1, 2, 3, 4)]
            except (TypeError, ValueError, IndexError):
                problems.append(f"{sym}: malformed bar row")
                break
            if any(not math.isfinite(v) or v <= 0 for v in vals):
                problems.append(
                    f"{sym}: non-finite or non-positive OHLC on {day}")
                break
            if prev is not None and day <= prev:
                problems.append(
                    f"{sym}: duplicate or non-increasing date {day}")
                break
            prev = day
    return problems


class PriceSource:
    def __init__(self, path=DEFAULT_BARS_PATH, expected_sessions=None):
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        problems = validate_bars_payload(raw)
        if problems:
            raise BarsIntegrityError(
                "daily_history_invalid_or_incomplete: "
                + "; ".join(problems[:5]))
        # Exact expected session (DEEP-PASS 3.1 item 2): where the
        # caller supplies the expected latest completed session per
        # symbol, derived from the trading calendar, a history that
        # does not end on that session is refused. Symbols the
        # caller does not name are not session checked, so a shorter
        # history (a delisted name) stays loadable; no tolerance
        # window is accepted for a named symbol.
        for sym, expected in (expected_sessions or {}).items():
            rows = raw.get(sym) or []
            last = str(rows[-1][0]) if rows else None
            if last != expected:
                raise BarsIntegrityError(
                    f"daily_history_invalid_or_incomplete: {sym}: "
                    f"history ends {last}, expected session {expected}")
        self.path = path
        self.bars = {}       # symbol -> {date: (o,h,l,c)}
        self.volumes = {}    # symbol -> {date: volume}
        self.calendars = {}  # symbol -> sorted [date]
        for sym, rows in raw.items():
            table = {}
            vols = {}
            for row in rows:
                date, o, h, l, c = row[0], row[1], row[2], row[3], row[4]
                table[date] = (float(o), float(h), float(l), float(c))
                if len(row) > 5:
                    vols[date] = float(row[5])
            self.bars[sym] = table
            self.volumes[sym] = vols
            self.calendars[sym] = sorted(table)

    def has_session(self, symbol, date):
        return date in self.bars.get(symbol, {})

    def bar(self, symbol, date):
        try:
            return self.bars[symbol][date]
        except KeyError:
            raise GradingError(f"no bar for {symbol} on {date}")

    def close(self, symbol, date):
        return self.bar(symbol, date)[3]

    def window(self, symbol, start, end):
        return [(d, self.bars[symbol][d])
                for d in self.calendars.get(symbol, []) if start <= d <= end]


def _closes_from(prices, sym, base_date, count):
    """Closes for the `count` sessions strictly after base_date,
    starting with base_date itself at index 0."""
    cal = prices.calendars.get(sym, [])
    if base_date not in cal:
        raise GradingError(f"no bar for {sym} on {base_date}")
    i = cal.index(base_date)
    dates = cal[i:i + count + 1]
    if len(dates) < count + 1:
        raise GradingError(
            f"price window for {sym} from {base_date} is incomplete")
    return [prices.close(sym, d) for d in dates]


def _realised_vol(prices, sym, base_date, sessions):
    """Annualised realised vol over the first `sessions` returns
    after base_date: sqrt(252 * mean squared log return). This is
    the issuing engines' own construction (refresh_voltermshape
    rv_future and refresh_exceedance har inputs use squared log
    returns from the base close)."""
    closes = _closes_from(prices, sym, base_date, sessions)
    sq = [math.log(closes[i + 1] / closes[i]) ** 2
          for i in range(sessions)]
    return math.sqrt(252.0 * sum(sq) / sessions)


def _reference_close(prices, sym, window_open):
    """Close of the last session before window_open (the price the
    level was published against), or the window_open open."""
    cal = prices.calendars.get(sym, [])
    before = [d for d in cal if d < window_open]
    if before:
        return prices.close(sym, before[-1])
    return prices.bar(sym, window_open)[0]


def _close_through(prices, sym, level, window_open, window_close):
    """1.0 if any session in the window closes beyond `level` in the
    wall's direction (above for a level over the reference price,
    below for one under it), else 0.0."""
    ref = _reference_close(prices, sym, window_open)
    up = level >= ref
    for _d, (_o, _h, _l, c) in prices.window(sym, window_open,
                                             window_close):
        if (up and c > level) or (not up and c < level):
            return 1.0
    return 0.0


# Kinds whose realised value is NOT a price, each with the specific
# record it actually comes from (cure G1, 2026-10-29; extended
# 2026-10-30 for the kinds Engines 19, 20 and 29 ledgered after the
# first pass). These raise a named GradingError, never the generic
# unknown-kind error, so a matured row is skipped with its reason on
# the record instead of looking like a grading defect.
NON_PRICE_RESOLVABLE_KINDS = {
    "young_figure":
        "its realised value is a future published figure after "
        "its next 30 matured outcomes, not a price",
    "recheck_replication":
        "its realised value is the next pre-registered recheck's "
        "verdict, not a price; the shared path grades it from a "
        "recheck record supplied to the grading pass (RC-19 cure, "
        "2026-10-30), and without that record there is nothing to "
        "grade against",
    "provisional_proof_forward_check":
        "its realised value is the issuing engine's own forward "
        "proof check over its population's graded outcomes at the "
        "horizon, not a single name's price",
    "league_interval":
        "its realised value is the league's own published interval "
        "outcome for the round (the entrant's realised rate over "
        "the league year), not a price; the shared path computes "
        "it from the ledger's own grades for the entrant (RC-19 "
        "cure, 2026-10-30)",
    "league_ranking":
        "its realised value is the league's own final ranking for "
        "the round, not a price; the shared path computes it from "
        "the round's graded league intervals (RC-19 cure, "
        "2026-10-30)",
    "cohort_barrier_race":
        "its realised value is the cohort's barrier-race record "
        "(up-first / down-first / neither over the class's own "
        "barriers, graded by survival calibration against the "
        "class hazard); the outcome spec carries no symbol or "
        "barrier levels a price source could resolve; the shared "
        "path grades it from a cohort race record supplied to "
        "the grading pass (RC-19 cure, 2026-10-30), and without "
        "that record there is nothing to grade against",
}


# ---- RC-19 grading construction cure, 2026-10-30 --------------------
# Registered conventions (registry grading_convention per engine)
# align the realised value's scale with the issued value's scale.
# The resolvers below are the shared implementations of the
# conventions: return_percent (a return in percent, matching
# Engine 15's percent quantiles), excess_return_points (a name's
# return minus its benchmark's, in points, matching Engines 13
# and 16's point estimates of excess), excess_sign (the same
# excess as a fraction with its sign as the binary outcome,
# matching Engine 3's chance that the excess is positive), and
# pin_in_band (Engine 27's arm rows). Already issued rows carry
# the legacy kind "return"; grade_forecast rewrites a copy of
# their outcome spec through the engine's registered legacy map
# before resolving, never mutating the issued row.

def _benchmark_excess(prices, outcome):
    """(own return fraction, benchmark return fraction) for an
    outcome spec carrying symbol, base_date and at_date."""
    sym = outcome.get("symbol")
    bench = outcome.get("benchmark", "SPY")
    base_d, at_d = outcome["base_date"], outcome["at_date"]
    own = prices.close(sym, at_d) / prices.close(sym, base_d) - 1.0
    ben = prices.close(bench, at_d) / prices.close(bench, base_d) - 1.0
    return own, ben


def binary_event_vol_details(prices, outcome):
    """Engine 30's binary_event construction, replicated exactly
    from its issuing refresher (RC-19 cure, 2026-10-30): the
    forward realised vol over horizon_sessions after the issue
    session, against the median of the 63 trailing same-horizon
    realised vols whose windows end on or before the issue
    session. Returns (binary, threshold, forward_rv). The warm-up
    rule is the refresher's own: a trailing window may not include
    the panel's first return."""
    sym = outcome.get("symbol", "SPY")
    h = int(outcome["horizon_sessions"])
    issue = outcome["issue_date"]
    cal = prices.calendars.get(sym, [])
    if issue not in cal:
        raise GradingError(f"no bar for {sym} on issue date {issue}")
    closes = [prices.close(sym, d) for d in cal]
    j = cal.index(issue)
    sq = [math.log(closes[i] / closes[i - 1]) ** 2
          for i in range(1, len(closes))]

    def rv_end(e):
        if e - h < 1 or e >= len(closes):
            return None
        return math.sqrt(252.0 * sum(sq[e - h:e]) / h)

    vals = [rv_end(e) for e in range(j - 62, j + 1)]
    if any(v is None for v in vals):
        raise GradingError(
            "binary_event trailing median is not computable: the "
            "price source does not carry 63 trailing windows "
            "ending on or before the issue session")
    if j < 1 or j + h > len(sq):
        raise GradingError(
            "binary_event forward window is not complete in the "
            "price source")
    fwd = math.sqrt(252.0 * sum(sq[j:j + h]) / h)
    thr = statistics.median(vals)
    return (1.0 if fwd > thr else 0.0), thr, fwd


def _spearman(xs, ys):
    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        return out
    rx, ry = ranks(xs), ranks(ys)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx)
                    * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def league_entrant_realised_error(rows, entrant_id, horizon_open,
                                  n_next=60):
    """The Calibration League's realised interval outcome from the
    ledger alone (the issuing refresher's own construction, moved
    into the shared machinery by the RC-19 cure, 2026-10-30): the
    entrant's first n_next graded forecasts opening on or after
    the round open; realised is the hit rate minus the mean stated
    coverage, in points. None while fewer than n_next exist."""
    grades = {r["forecast_row_id"]: r for r in rows
              if r.get("type") == "grade"}
    picked = []
    for r in rows:
        if r.get("type") != "forecast" or r.get("engine_id") != entrant_id:
            continue
        if r["horizon_open"] < horizon_open:
            continue
        g = grades.get(r["row_id"])
        if g is None:
            continue
        scores = (g.get("grade") or {}).get("scores") or {}
        binary = scores.get("coverage_hit")
        if binary is None:
            binary = (g.get("grade") or {}).get("binary_outcome")
        if binary is None:
            continue
        v = r.get("value") or {}
        if "stated_coverage" in v:
            stated = float(v["stated_coverage"]) * 100.0                 if float(v["stated_coverage"]) <= 1.0 else                 float(v["stated_coverage"])
        elif "p" in v:
            stated = float(v["p"]) * 100.0
        elif "quantiles" in v:
            stated = 80.0
        else:
            continue
        picked.append((r["horizon_open"], r["row_id"],
                       float(binary), stated))
    picked.sort()
    if len(picked) < n_next:
        return None
    picked = picked[:n_next]
    realised = 100.0 * sum(p[2] for p in picked) / n_next
    mean_stated = sum(p[3] for p in picked) / n_next
    return round(realised - mean_stated, 2), round(mean_stated, 2), n_next


def league_realised_map(rows):
    """{round: {entrant: realised_error_pts}} from the league's
    own graded interval rows on the ledger."""
    forecasts = {r["row_id"]: r for r in rows
                 if r.get("type") == "forecast"}
    out = {}
    for r in rows:
        if r.get("type") != "grade" or r.get("engine_id") != "engine_20":
            continue
        fc = forecasts.get(r.get("forecast_row_id")) or {}
        oc = fc.get("outcome") or {}
        if oc.get("kind") != "league_interval":
            continue
        realised = (r.get("grade") or {}).get("realised")
        if realised is None:
            realised = (r.get("grade") or {}).get("realised_error_pts")
        if realised is None:
            continue
        out.setdefault(oc.get("round"), {})[oc.get("entrant")] =             float(realised)
    return out


def resolve_outcome(outcome, prices, forecast_value=None,
                    context_outcomes=None, record=None,
                    ledger_rows=None):
    """Resolve a forecast's outcome spec against the price source.
    Returns (realised_value, binary_outcome_or_None).

    Extended 2026-10-29 (cure G1): resolvers for every price-based
    kind the ledger actually contains. Kinds that are NOT
    price-resolvable raise a named GradingError instead of the old
    generic unknown-kind error; NON_PRICE_RESOLVABLE_KINDS above
    names each one and the record its realised value comes from.
    first_failure_side carries no levels in its own spec; it
    resolves only when context_outcomes supplies the same
    engine/session wall_break_close_through outcomes that carry
    the call and put wall levels (grade_forecast supplies them
    from the ledger)."""
    sym = outcome.get("symbol")
    kind = outcome.get("kind")
    if kind == "league_interval":
        res = league_entrant_realised_error(
            ledger_rows or [], outcome.get("entrant"),
            outcome.get("round_open") or outcome.get("horizon_open")
            or "")
        if res is None and record is not None \
                and record.get("realised_error_pts") is not None:
            return float(record["realised_error_pts"]), None
        if res is None:
            raise GradingError(
                "outcome kind 'league_interval' is not "
                "price-resolvable: the entrant's first 60 graded "
                "forecasts for the round are not on the ledger "
                "yet, so its realised error does not exist")
        return float(res[0]), None
    if kind == "league_ranking":
        realised_map = league_realised_map(ledger_rows or [])
        rnd = outcome.get("round")
        if record is not None and record.get("realised_order"):
            return list(record["realised_order"]), None
        got = realised_map.get(rnd) or {}
        order = (forecast_value or {}).get("order") or []
        if order and all(e in got for e in order):
            return sorted(order, key=lambda e: abs(got[e])), None
        raise GradingError(
            "outcome kind 'league_ranking' is not "
            "price-resolvable: the round's graded league "
            "intervals are not all on the ledger yet, so its "
            "realised ranking does not exist")
    if kind == "recheck_replication":
        if record is not None and record.get("failed") is not None:
            val = float(record["failed"])
            return val, val
        raise GradingError(
            "outcome kind 'recheck_replication' is not "
            "price-resolvable: " + NON_PRICE_RESOLVABLE_KINDS[kind])
    if kind == "cohort_barrier_race":
        if record is not None \
                and record.get("sessions_to_resolution") is not None:
            return float(record["sessions_to_resolution"]), None
        raise GradingError(
            "outcome kind 'cohort_barrier_race' is not "
            "price-resolvable: " + NON_PRICE_RESOLVABLE_KINDS[kind])
    if kind in NON_PRICE_RESOLVABLE_KINDS:
        raise GradingError(
            f"outcome kind {kind!r} is not price-resolvable: "
            + NON_PRICE_RESOLVABLE_KINDS[kind])
    if not sym:
        raise GradingError(f"outcome kind {kind!r} carries no symbol")
    close_date = outcome.get("at_date")
    if kind == "close":
        return prices.close(sym, close_date), None
    if kind in ("return", "abs_return"):
        base = prices.close(sym, outcome["base_date"])
        val = prices.close(sym, close_date) / base - 1.0
        if kind == "return":
            return val, None
        realised = abs(val)
        binary = None
        if outcome.get("threshold_fraction") is not None:
            binary = 1.0 if realised > outcome["threshold_fraction"] else 0.0
        return realised, binary
    if kind == "close_above":
        val = prices.close(sym, close_date)
        return val, 1.0 if val > outcome["threshold"] else 0.0
    if kind == "touch":
        level = outcome["level"]
        hit = 0.0
        for _d, (_o, h, l, _c) in prices.window(
                sym, outcome["window_open"], outcome["window_close"]):
            if l <= level <= h:
                hit = 1.0
                break
        return hit, hit
    if kind == "return_percent":
        base = prices.close(sym, outcome["base_date"])
        return (prices.close(sym, close_date) / base - 1.0) * 100.0, None
    if kind == "excess_return_points":
        own, ben = _benchmark_excess(prices, outcome)
        return (own - ben) * 100.0, None
    if kind == "excess_sign":
        own, ben = _benchmark_excess(prices, outcome)
        excess = own - ben
        return excess, 1.0 if excess > 0 else 0.0
    if kind == "pin_in_band":
        pin = float(outcome["pin"])
        dist_pct = abs(prices.close(sym, close_date) - pin) / pin * 100.0
        binary = 1.0 if dist_pct <= 0.25 else 0.0
        return dist_pct, binary
    if kind == "binary_event":
        if "realised" in outcome:
            val = outcome["realised"]
            return val, float(val)
        if outcome.get("threshold_rule") \
                and outcome.get("horizon_sessions") \
                and outcome.get("issue_date"):
            # Engine 30's registered construction (RC-19 cure,
            # 2026-10-30): the realised bit is recomputed from
            # the price source under the threshold rule the row
            # itself carries, exactly as its issuing refresher
            # computed it. No realised field needs to be written
            # back onto the issued row.
            binary, _thr, _fwd = binary_event_vol_details(
                prices, outcome)
            return binary, binary
        raise GradingError(
            "binary_event outcome carries no realised value "
            "yet: the event's outcome has not been recorded on "
            "the forecast row, so there is nothing to grade "
            "against")
    if kind in ("pin_breach_half_em", "pin_abs_distance_pct"):
        # Engine 27's pin kinds, with the exact semantics of the
        # grade rows its own refresher appends (cure G1 remainder,
        # 2026-10-30): realised is the close's absolute distance
        # from the pin in percent; the breach leg is binary on
        # that distance exceeding half the stated expected move.
        pin = float(outcome["pin"])
        dist_pct = abs(prices.close(sym, close_date) - pin) / pin * 100.0
        if kind == "pin_abs_distance_pct":
            return dist_pct, None
        binary = 1.0 if dist_pct > 0.5 * float(outcome["em_pct"]) else 0.0
        return dist_pct, binary
    if kind == "max_drawdown":
        # Largest peak-to-trough fall over the window, as a
        # fraction; the forecast's p is the chance it exceeds the
        # stated threshold fraction (Engine 6's own construction).
        peak = prices.close(sym, outcome["base_date"])
        worst = 0.0
        for _d, (_o, _h, _l, c) in prices.window(
                sym, outcome["window_open"], outcome["window_close"]):
            peak = max(peak, c)
            worst = max(worst, 1.0 - c / peak)
        binary = None
        if outcome.get("threshold_fraction") is not None:
            binary = 1.0 if worst > outcome["threshold_fraction"] else 0.0
        return worst, binary
    if kind == "gap_fill":
        bar = prices.bar(sym, close_date)
        _o, h, l, _c = bar
        prior = float(outcome["prior_close"])
        opened = float(outcome.get("open", _o))
        filled = (l <= prior) if opened > prior else (h >= prior)
        binary = 1.0 if filled else 0.0
        return binary, binary
    if kind == "close_vs_prior_close_sign":
        prior = float(outcome["prior_close"])
        close = prices.close(sym, close_date)
        realised = close / prior - 1.0
        binary = None
        predicted = (forecast_value or {}).get("predicted_close_sign")
        if predicted is not None:
            actual = 1 if close > prior else (-1 if close < prior else 0)
            binary = 1.0 if actual == predicted else 0.0
        return realised, binary
    if kind in ("wall_break_close_through", "flip_close_beyond"):
        binary = _close_through(prices, sym, float(outcome["level"]),
                                outcome["window_open"],
                                outcome["window_close"])
        return binary, binary
    if kind == "first_failure_side":
        levels = {}
        for other in (context_outcomes or []):
            if other.get("kind") == "wall_break_close_through" \
                    and other.get("window_open") == close_date \
                    and other.get("window_close") == close_date:
                cell = other.get("_cell") or ""
                if cell.startswith("call_wall"):
                    side = "call"
                elif cell.startswith("put_wall"):
                    side = "put"
                else:
                    ref = _reference_close(prices, sym, close_date)
                    side = "call" if float(other["level"]) >= ref else "put"
                levels[side] = float(other["level"])
        if "call" not in levels or "put" not in levels:
            raise GradingError(
                "first_failure_side outcome carries no wall levels "
                "and no sibling wall outcomes were supplied")
        _o, _h, _l, close = prices.bar(sym, close_date)
        up = close > levels["call"]
        down = close < levels["put"]
        if up and down:
            raise GradingError(
                "first_failure_side cannot be ordered from daily "
                "bars: both walls closed through on the same session")
        # Bins are ordered [up, down, neither]; the ranked
        # probability scorer takes the realised bin index + 1.
        realised_bin = 1 if up else (2 if down else 3)
        return float(realised_bin), float(realised_bin)
    if kind == "realised_vol":
        return _realised_vol(prices, sym, outcome["base_date"],
                             int(outcome["sessions"])), None
    if kind == "vol_shape":
        rv5 = _realised_vol(prices, sym, outcome["base_date"], 5)
        rv21 = _realised_vol(prices, sym, outcome["base_date"], 21)
        binary = 1.0 if rv21 > rv5 else 0.0
        return binary, binary
    if kind == "realised_range_5s":
        base = prices.close(sym, outcome["base_date"])
        win = prices.window(sym, outcome["window_open"],
                            outcome["window_close"])
        if not win:
            raise GradingError(f"no bars for {sym} in range window")
        hi = max(b[1] for _d, b in win)
        lo = min(b[2] for _d, b in win)
        return (hi - lo) / base * 100.0, None
    if kind == "cohort_excess_5s":
        bench = outcome.get("benchmark", "SPY")
        at, base_d = outcome["at_date"], outcome["base_date"]
        bench_ret = prices.close(bench, at) / prices.close(bench, base_d) - 1.0
        members = outcome.get("members") or [sym]
        excess = []
        for m in members:
            r = prices.close(m, at) / prices.close(m, base_d) - 1.0
            excess.append((r - bench_ret) * 100.0)
        return sum(excess) / len(excess), None
    if kind == "excess_21s":
        # Engine 10's outcome (hookup 2026-10-30): one name's gain
        # over its own 21-session window against the benchmark's,
        # in points. The spec carries symbol, benchmark, base_date
        # and at_date explicitly, so it resolves exactly like the
        # single-member case of cohort_excess_5s.
        bench = outcome.get("benchmark", "SPY")
        at, base_d = outcome["at_date"], outcome["base_date"]
        bench_ret = prices.close(bench, at) / prices.close(bench, base_d) - 1.0
        r = prices.close(sym, at) / prices.close(sym, base_d) - 1.0
        return (r - bench_ret) * 100.0, None
    if kind == "volume_below_frozen_median":
        volumes = getattr(prices, "volumes", None)
        if not volumes or sym not in volumes:
            raise GradingError(
                "volume_below_frozen_median needs a price source "
                "that carries volumes")
        cal = [d for d in prices.calendars.get(sym, [])
               if outcome["base_date"] < d <= outcome["at_date"]]
        if not cal:
            raise GradingError(f"no sessions for {sym} in volume window")
        median = float(outcome["frozen_median_volume"])
        binary = 1.0 if any(volumes[sym][d] < median for d in cal) else 0.0
        return binary, binary
    if kind == "normalisation_sessions":
        # Engine 14's own construction (refresh_volclock): movement
        # is the annualised stdev of the last 10 log returns; the
        # frozen usual level is the median of every earlier movement
        # reading before the spike session; normalisation is the
        # first later session whose movement falls below it.
        cal = prices.calendars.get(sym, [])
        base_date = outcome["base_date"]
        if base_date not in cal:
            raise GradingError(f"no bar for {sym} on {base_date}")
        closes = [prices.close(sym, d) for d in cal]
        rets = [None] + [math.log(closes[i] / closes[i - 1])
                         for i in range(1, len(closes))]
        rv = [None] * len(closes)
        for i in range(10, len(closes)):
            rv[i] = statistics.stdev(rets[i - 9:i + 1]) * math.sqrt(252.0)
        base_i = cal.index(base_date)
        earlier = [v for v in rv[:base_i] if v is not None]
        if not earlier:
            raise GradingError(
                f"no earlier movement readings for {sym} before {base_date}")
        usual = statistics.median(earlier)
        scanned = 0
        for i in range(base_i + 1, len(closes)):
            if cal[i] < outcome["window_open"]:
                continue
            if cal[i] > outcome["window_close"]:
                break
            scanned += 1
            if rv[i] is not None and rv[i] < usual:
                return float(scanned), None
        return float(scanned), None
    raise GradingError(f"unknown outcome kind {kind!r}")


# ---- scoring rules ----------------------------------------------------
def score_coverage(value, realised, _binary):
    inside = 1.0 if value["lower"] <= realised <= value["upper"] else 0.0
    return {"coverage_hit": inside,
            "width": value["upper"] - value["lower"],
            "stated_coverage": value.get("stated_coverage")}


def score_brier(value, _realised, binary):
    if binary is None:
        raise GradingError("brier rule needs a binary outcome")
    p = min(max(float(value["p"]), 1e-9), 1 - 1e-9)
    return {"brier": (p - binary) ** 2,
            "log_loss": -(binary * math.log(p) +
                          (1 - binary) * math.log(1 - p))}


def pinball(tau, q, realised):
    diff = realised - q
    return max(tau * diff, (tau - 1) * diff)


def score_pinball(value, realised, _binary):
    quants = {float(k): float(v) for k, v in value["quantiles"].items()}
    losses = {f"pinball@{tau}": pinball(tau, q, realised)
              for tau, q in quants.items()}
    losses["crps_approx"] = 2.0 * sum(losses.values()) / len(losses)
    if 0.1 in quants and 0.9 in quants:
        losses["coverage_hit"] = 1.0 if quants[0.1] <= realised <= quants[0.9] else 0.0
    return losses


def score_abs_error(value, realised, _binary):
    est = float(value["estimate"])
    return {"abs_error": abs(est - realised), "signed_error": est - realised}


def score_ranked_probability(value, _realised, binary):
    # value: {"bins": [p1..pk]} over ordered bins; binary carries bin index+1
    probs = [float(p) for p in value["bins"]]
    realised_bin = int(binary)
    cum_f = cum_o = 0.0
    rps = 0.0
    for i, p in enumerate(probs):
        cum_f += p
        cum_o += 1.0 if realised_bin > i else 0.0
        rps += (cum_f - cum_o) ** 2
    return {"ranked_probability_score": rps / max(len(probs) - 1, 1)}


def score_survival_brier(value, realised, _binary):
    # value: {"resolved_by": {horizon_sessions: probability}}; realised is
    # sessions-to-resolution (or a censor marker > largest horizon).
    scores = {}
    for horizon, p in value["resolved_by"].items():
        outcome = 1.0 if realised <= float(horizon) else 0.0
        scores[f"brier@{horizon}"] = (float(p) - outcome) ** 2
    return scores


RULE_SCORERS = {
    "coverage": score_coverage,
    "brier": score_brier,
    "pinball": score_pinball,
    "abs_error": score_abs_error,
    "ranked_probability_score": score_ranked_probability,
    "survival_brier": score_survival_brier,
}


def is_matured(forecast_row, prices, as_of=None):
    """Matured iff the horizon_close session exists in the price source
    for the outcome symbol (and, if given, as_of >= horizon_close).
    An outcome with no symbol (young_figure, recheck_replication)
    has no price session to mature against: it is event-matured, not
    price-matured, and reports not matured here instead of raising."""
    if as_of is not None and as_of < forecast_row["horizon_close"]:
        return False
    kind = (forecast_row.get("outcome") or {}).get("kind")
    if kind in ("league_interval", "league_ranking",
                "recheck_replication", "cohort_barrier_race"):
        # Event-matured kinds (RC-19 cure, 2026-10-30): no price
        # session matures them. They are matured once their
        # horizon has closed; whether a realised value exists is
        # the resolver's call, and its named refusal is recorded
        # as the skip reason by run_grading.
        return as_of is None or as_of >= forecast_row["horizon_close"]
    sym = (forecast_row.get("outcome") or {}).get("symbol")
    if not sym:
        return False
    return prices.has_session(sym, forecast_row["horizon_close"])


def grade_forecast(ledger_obj, forecast_row, prices, registry, as_of=None,
                   record_outcomes=None):
    if not is_matured(forecast_row, prices, as_of=as_of):
        raise GradingError(
            f"forecast {forecast_row['row_id']} has not matured "
            f"(horizon_close {forecast_row['horizon_close']}); refusing "
            f"to grade before maturity")
    rule = registry.grading_rule(forecast_row["engine_id"])
    scorer = RULE_SCORERS.get(rule["scorer"])
    if scorer is None:
        raise GradingError(f"no scorer implemented for rule {rule['id']}")
    context = None
    if (forecast_row["outcome"].get("kind") == "first_failure_side"
            and hasattr(ledger_obj, "rows")):
        context = []
        for r in ledger_obj.rows():
            if r.get("type") == "forecast" \
                    and r.get("engine_id") == forecast_row["engine_id"] \
                    and (r.get("outcome") or {}).get("symbol") \
                    == forecast_row["outcome"].get("symbol"):
                entry = dict(r["outcome"])
                entry["_cell"] = (r.get("value") or {}).get("cell")
                context.append(entry)
    # Label freezing (DEEP-PASS 3.2 item 3): the grade is an outcome
    # append, so it repeats the label identity frozen on the
    # forecast row exactly; ledger.append_grade refuses any append
    # that does not. Unfrozen legacy rows grade with no identity.
    try:
        from . import ledger as _ledger
    except ImportError:
        try:
            from forecast import ledger as _ledger
        except ImportError:
            import ledger as _ledger
    try:
        frozen_identity = _ledger.frozen_label_identity(forecast_row) or {}
    except _ledger.LedgerError as exc:
        raise GradingError(str(exc))
    # Registered grading convention (RC-19 cure, 2026-10-30): an
    # engine whose issued rows carry a legacy kind under a scale
    # the shared resolver does not use for that kind gets a copy
    # of its outcome spec rewritten through the registry's legacy
    # map, so the realised value lands on the issued value's
    # registered scale. The issued row itself is never mutated
    # and never rescaled; the convention, its effective date and
    # its affected outstanding rows are on the registry record.
    outcome_spec = forecast_row["outcome"]
    convention = None
    if hasattr(registry, "grading_convention"):
        try:
            convention = registry.grading_convention(
                forecast_row["engine_id"])
        except Exception:
            convention = None
    if convention:
        legacy_map = convention.get("legacy_kind_map") or {}
        key = outcome_spec.get("kind")
        if key in legacy_map:
            outcome_spec = dict(outcome_spec)
            outcome_spec["kind"] = legacy_map[key]
            if convention.get("benchmark"):
                outcome_spec.setdefault("benchmark",
                                        convention["benchmark"])
    record = None
    if record_outcomes:
        record = record_outcomes.get(forecast_row.get("row_id"))
    ledger_rows = None
    if outcome_spec.get("kind") in ("league_interval", "league_ranking"):
        ledger_rows = ledger_obj.rows() if hasattr(ledger_obj, "rows") \
            else None
        if outcome_spec.get("kind") == "league_interval" and ledger_rows:
            for r in ledger_rows:
                if r.get("row_id") == forecast_row.get("row_id"):
                    outcome_spec = dict(outcome_spec)
                    outcome_spec["round_open"] = r.get("horizon_open")
                    break
    realised, binary = resolve_outcome(
        outcome_spec, prices,
        forecast_value=forecast_row.get("value"),
        context_outcomes=context, record=record,
        ledger_rows=ledger_rows)
    value = forecast_row["value"]
    kind_now = outcome_spec.get("kind")
    if kind_now == "pin_in_band":
        # Engine 27's arm rows (RC-19 cure, 2026-10-30): the
        # value states a claim percentage, not a probability or
        # an estimate, so no shared scorer applies; the grade is
        # the band hit itself, in the shared grade schema.
        grade = {"rule_id": rule["id"], "realised": realised,
                 "binary_outcome": binary,
                 "scores": {"in_band": binary},
                 "price_source": prices.path,
                 "arm": value.get("arm"),
                 "in_band": bool(binary)}
        return ledger_obj.append_grade(forecast_row=forecast_row,
                                       grade=grade, **frozen_identity)
    if kind_now == "league_interval":
        hit = 1.0 if float(value["err_low_pts"]) <= realised \
            <= float(value["err_high_pts"]) else 0.0
        grade = {"rule_id": rule["id"], "realised": realised,
                 "binary_outcome": hit,
                 "scores": {"coverage_hit": hit, "interval_hit": hit,
                            "width": float(value["err_high_pts"])
                            - float(value["err_low_pts"])},
                 "price_source": "ledger grades (league record)"}
        return ledger_obj.append_grade(forecast_row=forecast_row,
                                       grade=grade, **frozen_identity)
    if kind_now == "league_ranking":
        order = list(value.get("order") or [])
        rho = _spearman([order.index(e) for e in order],
                        [list(realised).index(e) for e in order]) \
            if order and realised else 0.0
        grade = {"rule_id": rule["id"], "realised": list(realised),
                 "binary_outcome": None,
                 "scores": {"rank_agreement": rho},
                 "realised_ranking": list(realised),
                 "price_source": "ledger grades (league record)"}
        return ledger_obj.append_grade(forecast_row=forecast_row,
                                       grade=grade, **frozen_identity)
    if kind_now == "recheck_replication":
        scores = score_brier(value, realised, binary)
        grade = {"rule_id": rule["id"], "realised": realised,
                 "binary_outcome": binary, "scores": scores,
                 "price_source": "recheck record supplied to grading"}
        return ledger_obj.append_grade(forecast_row=forecast_row,
                                       grade=grade, **frozen_identity)
    if kind_now == "cohort_barrier_race":
        scores = score_survival_brier(value, realised, binary)
        grade = {"rule_id": rule["id"], "realised": realised,
                 "binary_outcome": binary, "scores": scores,
                 "price_source": "cohort race record supplied to grading"}
        return ledger_obj.append_grade(forecast_row=forecast_row,
                                       grade=grade, **frozen_identity)
    if "bins" in value and binary is not None:
        # A distribution-over-bins leg (Engine 8's first-failure
        # split): the ranked probability scorer is the scorer for
        # this value shape, whatever the engine's headline rule.
        scorer = score_ranked_probability
    if "estimate" in value and binary is None \
            and rule["scorer"] == "brier":
        # A point estimate leg issued by a probability registered
        # engine (Engine 27's distance companion): its own rule
        # for the leg is the distance error, as its issuing
        # record states; there is no probability to Brier score.
        scorer = score_abs_error
    if rule["scorer"] == "pinball" and "quantiles" not in value \
            and value.get("p") is not None and binary is not None:
        # A probability leg issued by a pinball-registered engine
        # (Engine 7's vol_shape leg): score the probability as a
        # probability, never force it through the quantile scorer.
        scorer = score_brier
    if rule["scorer"] == "brier" and "p" not in value \
            and "bins" not in value and binary is not None:
        # A deterministic sign forecast (Engine 28's failed-gap
        # sign flip): the prediction is the stated side itself, so
        # its Brier score is 0 when the side is right and 1 when
        # wrong, with the correctness carried explicitly.
        scores = {"brier": (1.0 - binary) ** 2 if binary in (0.0, 1.0)
                  else 1.0,
                  "sign_correct": binary}
        grade = {"rule_id": rule["id"], "realised": realised,
                 "binary_outcome": binary, "scores": scores,
                 "price_source": prices.path}
        return ledger_obj.append_grade(forecast_row=forecast_row,
                                       grade=grade, **frozen_identity)
    scores = scorer(value, realised, binary)
    grade = {"rule_id": rule["id"], "realised": realised,
             "binary_outcome": binary, "scores": scores,
             "price_source": prices.path}
    if kind_now == "binary_event" and binary is not None:
        # Engine 30's controls (RC-19 cure, 2026-10-30): the
        # shared grade carries the same control Brier scores and
        # threshold readings its issuing refresher used to stamp
        # on its divergent self grades, so the paired baseline
        # machinery and the page keep their inputs.
        if value.get("p_control_vix_only") is not None:
            scores["brier_control"] = \
                (float(value["p_control_vix_only"]) - binary) ** 2
        if value.get("base_rate") is not None:
            scores["brier_base_rate"] = \
                (float(value["base_rate"]) - binary) ** 2
        if value.get("book_version") is not None:
            grade["book_version"] = value["book_version"]
        if outcome_spec.get("threshold_rule"):
            _b, thr, fwd = binary_event_vol_details(prices, outcome_spec)
            grade["threshold_used"] = round(thr, 6)
            grade["realised_vol"] = round(fwd, 6)
    if forecast_row.get("engine_id") == "engine_27":
        # The pin page's arm statistics read these two fields;
        # they are part of the shared grade for this engine now,
        # not a divergent schema beside it.
        grade["arm"] = value.get("arm")
        if kind_now == "pin_breach_half_em":
            grade["breached"] = bool(binary)
    return ledger_obj.append_grade(forecast_row=forecast_row, grade=grade,
                                   **frozen_identity)


def run_grading(ledger_obj, prices, registry, as_of=None, skipped=None,
                record_outcomes=None):
    """Grade every matured, not-yet-graded forecast. Returns grade
    rows. A matured row whose outcome cannot be resolved or scored
    is skipped with its reason appended to `skipped` (when given)
    instead of aborting the whole run: one bad kind must not starve
    every other engine's grades."""
    graded_ids = {r["forecast_row_id"] for r in ledger_obj.rows()
                  if r.get("type") == "grade"}
    voided_by = {r["corrects_row_id"]: r["row_id"]
                 for r in ledger_obj.rows()
                 if r.get("type") == "correction"}
    new_grades = []
    for row in ledger_obj.rows():
        if row.get("type") != "forecast" or row["row_id"] in graded_ids:
            continue
        if row["row_id"] in voided_by:
            if skipped is not None:
                skipped.append({
                    "row_id": row["row_id"],
                    "engine_id": row.get("engine_id"),
                    "kind": (row.get("outcome") or {}).get("kind"),
                    "reason": "voided by correction "
                              f"{voided_by[row['row_id']]}"})
            continue
        if row.get("absence_state") not in (None, "present"):
            continue
        if is_matured(row, prices, as_of=as_of):
            try:
                new_grades.append(
                    grade_forecast(ledger_obj, row, prices, registry,
                                   as_of=as_of,
                                   record_outcomes=record_outcomes))
            except (GradingError, KeyError, TypeError, ValueError) as exc:
                if skipped is not None:
                    skipped.append({"row_id": row["row_id"],
                                    "engine_id": row.get("engine_id"),
                                    "kind": (row.get("outcome") or {})
                                    .get("kind"),
                                    "reason": f"{type(exc).__name__}: {exc}"})
    return new_grades


# ---- horizon overlap measurement (DEEP-PASS 3.2 item 4) -------------
# Ported from the horizon_overlap.py geometry in Ausar's forecast
# package (Section 2.2, M09): overlapping pair count, max concurrent
# windows, largest connected overlap component and the maximum non
# overlapping subset, over frozen target windows. Adapted, not
# copied: his windows are timestamp intervals, ours are session
# intervals, so every window is first placed on the union session
# calendar and the geometry runs on inclusive session indices.
# It is a measurement, not a significance adjustment: it buys a
# defensible independent window count to print beside row counts,
# and it changes no score or grade.

import bisect


def session_interval_geometry(intervals):
    """Overlap geometry over inclusive session intervals
    [(open_idx, close_idx), ...]. Returns the window count, the
    overlapping pair count (pairs sharing at least one session),
    the maximum number of windows open on one session, the largest
    connected overlap component, and the independent window count
    (the maximum non overlapping subset, by greedy earliest close,
    which is optimal for interval scheduling)."""
    iv = sorted((int(o), int(c)) for o, c in intervals)
    n = len(iv)
    if n == 0:
        return {"windows": 0, "overlapping_pairs": 0,
                "max_concurrency": 0, "largest_component": 0,
                "independent_windows": 0}
    active = []
    pairs = 0
    for o, c in iv:
        cut = bisect.bisect_left(active, o)
        active = active[cut:]
        pairs += len(active)
        bisect.insort(active, c)
    events = []
    for o, c in iv:
        events.append((o, 1))
        events.append((c + 1, -1))
    events.sort(key=lambda e: (e[0], e[1]))
    cur = peak = 0
    for _at, delta in events:
        cur += delta
        peak = max(peak, cur)
    largest = run = 1
    run_close = iv[0][1]
    for o, c in iv[1:]:
        if o <= run_close:
            run += 1
            run_close = max(run_close, c)
        else:
            largest = max(largest, run)
            run = 1
            run_close = c
    largest = max(largest, run)
    independent = 0
    last_close = None
    for o, c in sorted(iv, key=lambda t: (t[1], t[0])):
        if last_close is None or o > last_close:
            independent += 1
            last_close = c
    return {"windows": n, "overlapping_pairs": pairs,
            "max_concurrency": peak, "largest_component": largest,
            "independent_windows": independent}


def _weekday_axis(dates):
    """Every weekday from the earliest to the latest date given.
    This is the session convention the record itself was issued
    under: the engine refreshers compute horizon dates with
    next_sessions (weekdays, Mon to Fri), so a window's stated
    session count is its span on this axis by construction."""
    from datetime import date, timedelta
    lo = date.fromisoformat(min(dates))
    hi = date.fromisoformat(max(dates))
    out = []
    d = lo
    while d <= hi:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def record_horizon_overlap(rows, calendars=None,
                           session_lengths=(20, 21)):
    """Independent window counts for the Record's long horizon
    windows, beside their row counts.

    rows: ledger rows. calendars: {symbol: [session dates]} or one
    [session dates] list; the union of every calendar supplied is
    the session axis, so a window's length is its span in sessions
    on that axis and windows are comparable across symbols. With
    no calendar supplied, the axis is the weekday calendar the
    record's own horizon dates were issued under (see
    _weekday_axis), spanning the record's first to last horizon
    date. Only taken forecast rows whose measured span is in
    session_lengths (default the 20 and 21 session windows) are
    measured. A row whose horizon dates are not on the axis (a
    weekend dated row, or a date outside a supplied calendar) is
    counted in `unplaced` and named by that count, never silently
    dropped."""
    if calendars:
        if isinstance(calendars, dict):
            axis = sorted({d for cal in calendars.values()
                           for d in cal})
        else:
            axis = sorted(set(calendars))
    else:
        dates = [r[k] for r in rows if r.get("type") == "forecast"
                 for k in ("horizon_open", "horizon_close")
                 if r.get(k)]
        axis = _weekday_axis(dates) if dates else []
    axis_kind = ("supplied session calendar" if calendars else
                 "weekday session axis, the convention the "
                 "record's own horizon dates were issued under")
    index = {d: i for i, d in enumerate(axis)}
    by_engine = {}
    unplaced = 0
    for row in rows:
        if row.get("type") != "forecast":
            continue
        if row.get("absence_state") not in (None, "present"):
            continue
        opened = row.get("horizon_open")
        closed = row.get("horizon_close")
        if opened not in index or closed not in index:
            unplaced += 1
            continue
        length = index[closed] - index[opened] + 1
        if length not in session_lengths:
            continue
        by_engine.setdefault(row["engine_id"], {}) \
            .setdefault(length, []).append((index[opened],
                                            index[closed]))
    engines = {}
    for engine_id, by_length in sorted(by_engine.items()):
        engines[engine_id] = {}
        for length, ivs in sorted(by_length.items()):
            geo = session_interval_geometry(ivs)
            engines[engine_id][length] = {
                "rows": geo["windows"],
                "independent_windows": geo["independent_windows"],
                "overlapping_pairs": geo["overlapping_pairs"],
                "max_concurrency": geo["max_concurrency"],
                "largest_component": geo["largest_component"]}
    return {"by_engine": engines, "unplaced": unplaced,
            "session_lengths": list(session_lengths),
            "basis": "session intervals on the " + axis_kind +
                     "; a measurement of window dependence, "
                     "not a significance adjustment"}


# ---- BH correction, paired loss deltas, attestation (3.2 item 5) ------
# Merged from the evaluation.py design in Ausar's forecast package
# (Section 2.2, M04): Benjamini-Hochberg correction across a tested
# family, paired loss deltas against a declared baseline, and the
# refusal to treat an uncalibrated number as a probability. His in
# sample base rate baseline is NOT imported: the only baselines
# here are the declared, price aware ones named in our own
# registry edge cards, extracted below.

def benjamini_hochberg(pvalues):
    """Benjamini-Hochberg adjusted q-values, aligned to the input
    order. Step up with monotonic enforcement (each q is the
    minimum of its own p * m / rank and every larger p's q), the
    correct form confirmed in the source read."""
    ps = [float(p) for p in pvalues]
    m = len(ps)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: ps[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, ps[i] * m / rank)
        q[i] = min(1.0, running)
    return q


def _binom_pmf(k, n, p):
    return math.comb(n, k) * p ** k * (1.0 - p) ** (n - k)


def binomial_two_sided_p(k, n, p0):
    """Exact two sided binomial p-value: the probability, under
    p0, of every outcome at least as improbable as k of n."""
    if n <= 0:
        return 1.0
    pk = _binom_pmf(k, n, p0)
    total = sum(_binom_pmf(i, n, p0) for i in range(n + 1)
                if _binom_pmf(i, n, p0) <= pk * (1.0 + 1e-12))
    return min(1.0, total)


def paired_loss_deltas(pairs):
    """Paired loss comparison: pairs of (engine_loss,
    baseline_loss) over the same forecasts. The delta is baseline
    minus engine, so a positive mean delta means the engine lost
    less than its declared baseline. The p-value is an exact two
    sided sign test over the nonzero deltas (ties carry no sign
    and are counted, never dropped silently)."""
    pairs = [(float(e), float(b)) for e, b in pairs]
    n = len(pairs)
    if n == 0:
        return {"n": 0, "ties": 0, "mean_engine_loss": None,
                "mean_baseline_loss": None, "mean_delta": None,
                "engine_better_share": None, "p_value": None}
    deltas = [b - e for e, b in pairs]
    ties = sum(1 for d in deltas if d == 0.0)
    wins = sum(1 for d in deltas if d > 0.0)
    nonzero = sum(1 for d in deltas if d != 0.0)
    p_value = binomial_two_sided_p(wins, nonzero, 0.5) if nonzero \
        else 1.0
    return {"n": n, "ties": ties,
            "mean_engine_loss": sum(e for e, _b in pairs) / n,
            "mean_baseline_loss": sum(b for _e, b in pairs) / n,
            "mean_delta": sum(deltas) / n,
            "engine_better_share": wins / n,
            "p_value": p_value}


# Declared baselines (ours, price aware, named in the registry edge
# cards). engine_30's control is the VIX level alone probability
# the engine itself carries on every forecast row; engine_17's
# baselines are its own Benchmark quantities, ledgered as forecast
# rows beside the cells they price. No other engine declares a
# computable baseline yet, so no other engine gets a paired test:
# an absent baseline stays absent, never invented.
DECLARED_BASELINES = {
    "engine_30": {
        "kind": "on_row_probability", "key": "p_control_vix_only",
        "score": "brier",
        "name": "declared baseline: the VIX level alone control "
                "probability carried on the forecast row "
                "(p_control_vix_only), named in engine_30's "
                "registry edge card as the control it must beat"},
    "engine_17": {
        "kind": "benchmark_rows",
        "name": "declared baseline: engine_17's own Benchmark "
                "quantities ledgered as forecast rows beside the "
                "cells they price, named in its registry edge card"},
}


def _baseline_pairs_by_cell(rows):
    """{(engine_id, quantity, score): [(engine_loss, baseline_loss)]}
    for every declared baseline extractor, over graded forecasts."""
    forecasts = {r["row_id"]: r for r in rows
                 if r.get("type") == "forecast" and r.get("row_id")}
    grades = {r["forecast_row_id"]: r["grade"] for r in rows
              if r.get("type") == "grade"}
    out = {}

    def add(engine_id, quantity, score, pair):
        out.setdefault((engine_id, quantity, score), []).append(pair)

    for fid, fc in forecasts.items():
        spec = DECLARED_BASELINES.get(fc["engine_id"])
        grade = grades.get(fid)
        if spec is None or grade is None:
            continue
        if spec["kind"] != "on_row_probability":
            continue
        binary = grade.get("binary_outcome")
        scores = grade.get("scores") or {}
        value = fc.get("value") or {}
        if binary is None or spec["score"] not in scores \
                or spec["key"] not in value:
            continue
        baseline_loss = (float(value[spec["key"]]) - binary) ** 2
        add(fc["engine_id"], fc.get("quantity"), spec["score"],
            (scores[spec["score"]], baseline_loss))
    groups = {}
    for fid, fc in forecasts.items():
        if fc["engine_id"] != "engine_17":
            continue
        grade = grades.get(fid)
        if grade is None:
            continue
        quantity = fc.get("quantity") or ""
        side = "bench" if quantity.startswith("Benchmark:") else "main"
        for score, val in (grade.get("scores") or {}).items():
            if isinstance(val, (int, float)):
                key = (fc.get("subject"), fc.get("horizon_open"),
                       fc.get("horizon_close"), score)
                groups.setdefault(key, {}).setdefault(side, []) \
                    .append((fc.get("quantity"), val))
    for (_sym, _o, _c, score), sides in groups.items():
        mains = sides.get("main") or []
        benchs = sides.get("bench") or []
        if len(mains) == 1 and len(benchs) == 1:
            add("engine_17", mains[0][0], score,
                (mains[0][1], benchs[0][1]))
    return out


def paired_baseline_report(rows):
    """Paired loss deltas against each declared baseline, per
    engine. An engine with a declared baseline but no graded pairs
    yet is reported with pairs 0 and a named state, so the absence
    is on the record instead of the engine silently vanishing."""
    by_cell = _baseline_pairs_by_cell(rows)
    report = {}
    for engine_id, spec in sorted(DECLARED_BASELINES.items()):
        pairs = []
        for (eng, _q, _s), cell_pairs in by_cell.items():
            if eng == engine_id:
                pairs.extend(cell_pairs)
        entry = {"baseline": spec["name"]}
        entry.update(paired_loss_deltas(pairs))
        entry["pairs"] = entry["n"]
        entry["state"] = (
            "graded pairs on record" if pairs else
            "no graded pairs yet for this declared baseline; the "
            "machinery is in place and the count is honestly zero")
        report[engine_id] = entry
    return report


def _stated_coverage(value):
    """The coverage a coverage_hit cell claims, from the forecast
    value itself: an explicit stated_coverage, or the 0.80 of a
    0.1 to 0.9 quantile band. None when the value states neither;
    a coverage figure is never invented for a cell."""
    if not isinstance(value, dict):
        return None
    if value.get("stated_coverage") is not None:
        return float(value["stated_coverage"])
    quants = value.get("quantiles") or {}
    keys = {str(k) for k in quants}
    if "0.1" in keys and "0.9" in keys:
        return 0.8
    return None


def engine_cell_family(rows, alpha=0.05):
    """Each engine's published cell family: one cell per (quantity,
    score) over its graded forecasts, with the mean the Record
    publishes, a p-value where a test exists, and BH adjusted
    q-values across the engine's tested cells.

    Tests, and only these: a coverage_hit cell is tested by an
    exact binomial test of its hit rate against the coverage its
    own forecast values state; a cell with declared baseline pairs
    is tested by the sign test on its paired loss deltas. A cell
    with neither carries p_value None and a named reason: BH is
    applied over the tested cells only, and an untested cell is
    never dressed up with a number it did not earn."""
    forecasts = {r["row_id"]: r for r in rows
                 if r.get("type") == "forecast" and r.get("row_id")}
    pairs_by_cell = _baseline_pairs_by_cell(rows)
    cells = {}
    for row in rows:
        if row.get("type") != "grade":
            continue
        fc = forecasts.get(row["forecast_row_id"])
        if fc is None:
            continue
        for score, val in (row["grade"].get("scores") or {}).items():
            if not isinstance(val, (int, float)):
                continue
            key = (fc["engine_id"], fc.get("quantity"), score)
            cell = cells.setdefault(key, {"values": [], "stated": []})
            cell["values"].append(float(val))
            if score == "coverage_hit":
                cell["stated"].append(
                    _stated_coverage(fc.get("value") or {}))
    families = {}
    for (engine_id, quantity, score), cell in sorted(cells.items()):
        values = cell["values"]
        entry = {"quantity": quantity, "score": score,
                 "n": len(values),
                 "mean": sum(values) / len(values),
                 "p_value": None, "p_reason": None, "q_value": None,
                 "bh_significant": False}
        pairs = pairs_by_cell.get((engine_id, quantity, score))
        if pairs:
            entry["p_value"] = paired_loss_deltas(pairs)["p_value"]
            entry["p_reason"] = (
                "sign test on paired loss deltas against the "
                "engine's declared baseline")
        elif score == "coverage_hit":
            stated = cell["stated"]
            if stated and all(s == stated[0] and s is not None
                              for s in stated):
                hits = int(round(sum(values)))
                entry["p_value"] = binomial_two_sided_p(
                    hits, len(values), stated[0])
                entry["p_reason"] = (
                    f"binomial test of the hit rate against the "
                    f"stated coverage {stated[0]}")
            else:
                entry["p_reason"] = (
                    "the forecast values state no single coverage "
                    "for this cell, so no binomial test is run")
        else:
            entry["p_reason"] = (
                "no declared baseline pair and no stated coverage "
                "test applies to this cell, so it carries no "
                "p-value; BH covers the engine's tested cells only")
        families.setdefault(engine_id, []).append(entry)
    out = {}
    for engine_id, cell_list in sorted(families.items()):
        tested = [c for c in cell_list if c["p_value"] is not None]
        qs = benjamini_hochberg([c["p_value"] for c in tested])
        for cell_entry, q in zip(tested, qs):
            cell_entry["q_value"] = q
            cell_entry["bh_significant"] = q <= alpha
        out[engine_id] = {"cells": cell_list,
                          "tested_cells": len(tested),
                          "alpha": alpha}
    return out


# ---- FE08 HAR control, QLIKE graded (DEEP-PASS 3.2 item 14) ----------
# FE08 as coded in Ausar's package is a fixed weight HAR form:
# log variance forecast = 0.50 * log_rv_1 + 0.30 * log_rv_5 +
# 0.20 * log_rv_22, no intercept. The source read's honest
# verdict is that this engine IS the baseline, which is exactly
# what a control column should be: Engines 1 and 7 must beat
# this control on QLIKE, not merely on coverage or pinball.
# QLIKE for a variance forecast f against realised variance v
# is v / f - log(v / f) - 1, minimised at f = v. Realised
# variance here is on this lineup's own scheme: 252 * mean
# squared log return over the horizon sessions, the same
# construction _realised_vol uses. Engine variance equivalents,
# stated so the comparison is auditable: Engine 7's is its
# median (0.5) realised vol quantile, squared; Engine 1's is
# its 68 percent band's half width as a fraction of the base
# close, annualised over the band's horizon. A forecast whose
# inputs cannot be reconstructed from the price source is
# counted in `skipped` with its reason, never dropped silently.

FE08_WEIGHTS = (0.50, 0.30, 0.20)


def qlike_loss(forecast_variance, realised_variance):
    f = float(forecast_variance)
    v = float(realised_variance)
    if f <= 0 or v <= 0:
        raise GradingError(
            "QLIKE needs positive forecast and realised variances")
    ratio = v / f
    return ratio - math.log(ratio) - 1.0


def fe08_har_variance(log_rv_1, log_rv_5, log_rv_22):
    """The FE08 control's variance forecast: exp of the fixed
    weight log variance mean, clipped on the source's own wide
    bounds [minus 40, 10]."""
    log_f = (FE08_WEIGHTS[0] * float(log_rv_1)
             + FE08_WEIGHTS[1] * float(log_rv_5)
             + FE08_WEIGHTS[2] * float(log_rv_22))
    return math.exp(max(-40.0, min(10.0, log_f)))


def _sq_log_returns(prices, sym, upto_date, count):
    """The last `count` squared log returns ending at upto_date
    (the return into upto_date is the last element)."""
    cal = prices.calendars.get(sym, [])
    if upto_date not in cal:
        raise GradingError(f"no bar for {sym} on {upto_date}")
    i = cal.index(upto_date)
    if i < count:
        raise GradingError(
            f"only {i} returns for {sym} up to {upto_date}, "
            f"need {count}")
    closes = [prices.close(sym, d) for d in cal[i - count:i + 1]]
    return [math.log(closes[j + 1] / closes[j]) ** 2
            for j in range(count)]


def _har_control_variance(prices, sym, base_date):
    sq = _sq_log_returns(prices, sym, base_date, 22)
    rv = lambda part: 252.0 * sum(part) / len(part)  # noqa: E731
    return fe08_har_variance(math.log(rv(sq[-1:])), math.log(rv(sq[-5:])),
                             math.log(rv(sq)))


def _realised_variance(prices, sym, base_date, sessions):
    closes = _closes_from(prices, sym, base_date, sessions)
    sq = [math.log(closes[j + 1] / closes[j]) ** 2
          for j in range(sessions)]
    return 252.0 * sum(sq) / sessions


def har_control_report(rows, prices):
    """QLIKE of Engines 1 and 7 against the FE08 HAR control,
    per engine, over matured forecasts on the record. Only
    forecasts whose horizon_close session exists in the price
    source are graded; the rest are counted as unmatured, not
    skipped. The paired delta is control loss minus engine
    loss (paired_loss_deltas), so a positive mean delta means
    the engine beat the HAR control."""
    report = {}
    for engine_id in ("engine_01", "engine_07"):
        pairs = []
        skipped = []
        unmatured = 0
        for row in rows:
            if row.get("type") != "forecast" \
                    or row.get("engine_id") != engine_id:
                continue
            if row.get("absence_state") not in (None, "present"):
                continue
            outcome = row.get("outcome") or {}
            sym = outcome.get("symbol")
            if not sym or not prices.has_session(
                    sym, row.get("horizon_close") or ""):
                unmatured += 1
                continue
            try:
                if engine_id == "engine_07":
                    base_date = outcome["base_date"]
                    sessions = int(outcome["sessions"])
                    median = float(
                        (row["value"].get("quantiles") or {})["0.5"])
                    engine_var = median ** 2
                else:
                    cal = prices.calendars.get(sym, [])
                    before = [d for d in cal
                              if d < row["horizon_open"]]
                    if not before:
                        raise GradingError(
                            f"no session before {row['horizon_open']} "
                            f"for {sym}")
                    base_date = before[-1]
                    idx = cal.index(base_date)
                    close_idx = cal.index(row["horizon_close"])
                    sessions = close_idx - idx
                    if sessions <= 0:
                        raise GradingError("non positive horizon span")
                    quants = {float(k): float(v) for k, v in
                              (row["value"].get("quantiles") or {}).items()}
                    if 0.84 not in quants or 0.16 not in quants:
                        raise GradingError(
                            "forecast carries no 0.16/0.84 quantiles, "
                            "so no 68 percent band can be read from it")
                    base_close = prices.close(sym, base_date)
                    half_frac = (quants[0.84] - quants[0.16]) \
                        / 2.0 / base_close
                    engine_var = half_frac ** 2 * 252.0 / sessions
                control_var = _har_control_variance(prices, sym, base_date)
                realised_var = _realised_variance(
                    prices, sym, base_date, sessions)
                pairs.append((qlike_loss(engine_var, realised_var),
                              qlike_loss(control_var, realised_var)))
            except (GradingError, KeyError, TypeError, ValueError) as exc:
                skipped.append({"row_id": row.get("row_id"),
                                "reason": f"{type(exc).__name__}: {exc}"})
        entry = {"control": "FE08 fixed weight HAR (0.50 log rv 1, "
                            "0.30 log rv 5, 0.20 log rv 22), graded "
                            "on QLIKE",
                 "unmatured": unmatured, "skipped": skipped}
        entry.update(paired_loss_deltas(pairs))
        entry["pairs"] = entry["n"]
        entry["state"] = (
            "graded pairs on record" if pairs else
            "no matured, reconstructable forecasts yet for this "
            "engine on the price panel; the control machinery is "
            "in place and the count is honestly zero")
        report[engine_id] = entry
    return report


# ---- calibration attestation as a publishing rule ----------------------
# What his evaluation.py enforces in function signatures (probability
# scoring refuses uncalibrated inputs), enforced here in our
# publishing layer: no surface may render a number as a probability
# unless the engine's registry entry carries an explicit calibrated
# out of sample attestation. The attestation is a registry field,
# validated in registry.py; absent or malformed fails closed.

ATTESTATION_STATUS = "calibrated_out_of_sample"


def calibration_attestation(engine_entry):
    """The engine's attestation dict when it is present and well
    formed (status calibrated_out_of_sample, a stated basis, an
    attested_on date), else None. Malformed fails closed."""
    att = (engine_entry or {}).get("calibration_attestation")
    if not isinstance(att, dict):
        return None
    if att.get("status") != ATTESTATION_STATUS:
        return None
    if not str(att.get("basis") or "").strip():
        return None
    if not str(att.get("attested_on") or "").strip():
        return None
    return att


def probability_render_decision(engine_entry):
    """Whether this engine's numbers may be rendered as
    probabilities on any surface, with the reason either way."""
    att = calibration_attestation(engine_entry)
    if att is not None:
        return {"render_as_probability": True,
                "reason": "calibration attestation on record: "
                          f"{att['basis']} (attested "
                          f"{att['attested_on']})",
                "attestation": att}
    return {"render_as_probability": False,
            "reason": "no calibrated out of sample attestation on "
                      "record for this engine; its numbers may be "
                      "published only as uncalibrated scores, never "
                      "as probabilities",
            "attestation": None}


def attestation_record(engine_entry, figures, recorded_on,
                       counting_basis=None):
    """The per engine attestation record built from its own graded
    record (RC-22 cure, 2026-10-30). ``figures`` is the engine's
    recompute_figures entry (forecasts / graded / mean_scores).
    ``counting_basis``, when given, is stamped on the record and
    appended to its basis text (cure ORACLE-COUNT-BASIS-20261031):
    an engine that hosts foreign record rows under its id (the
    Aperture proof gate's provisional rows under engine_19) states
    which rows its attestation counts, so the attestation and the
    page's own live record count on one basis.
    Where grades exist the record states the graded count and the
    mean scores actually on the ledger; where none exist it states
    that plainly. It never claims calibrated status: no engine on
    this program has a calibrated out of sample evaluation attested,
    so every record here is status not_attested and the probability
    gate above stays closed until a real calibration evaluation is
    attested under ATTESTATION_STATUS."""
    figures = figures or {}
    graded = int(figures.get("graded") or 0)
    # Defect 8 cure (2026-10-30): the attestation states the valid
    # record, so a recompute entry carrying forecasts_valid (raw
    # minus voided) is stated on that basis, never the raw count.
    forecasts = int(figures.get("forecasts_valid")
                    if figures.get("forecasts_valid") is not None
                    else (figures.get("forecasts") or 0))
    if graded > 0:
        means = figures.get("mean_scores") or {}
        if not means:
            # Multi group engine whose graded population sits in
            # one fingerprint group: state that group's means, the
            # only means the valid grades support, rather than
            # claiming no numeric scores exist.
            graded_groups = [
                g for g in (figures.get("by_label_fingerprint")
                            or {}).values() if g.get("graded")]
            if len(graded_groups) == 1:
                means = graded_groups[0].get("mean_scores") or {}
        mean_text = ", ".join(
            f"{k} {v:.4f}" for k, v in sorted(means.items())) \
            or "no numeric mean scores"
        basis = (f"{graded} graded forecasts of {forecasts} recorded "
                 f"on the ledger (mean scores: {mean_text}); graded "
                 f"record only, no calibrated out of sample "
                 f"evaluation has been attested, so this engine's "
                 f"numbers are published as uncalibrated scores, "
                 f"never as probabilities")
    else:
        basis = (f"no graded forecasts on record yet ({forecasts} "
                 f"recorded, 0 graded); nothing has been attested, "
                 f"so this engine's numbers are published as "
                 f"uncalibrated scores, never as probabilities")
    record = {"status": "not_attested", "basis": basis,
              "graded_forecasts": graded,
              "forecasts_recorded": forecasts,
              "recorded_on": recorded_on}
    if counting_basis:
        record["counting_basis"] = counting_basis
        record["basis"] = (basis.rstrip(".") + ". Counting basis: "
                           + counting_basis + ".")
    return record


def render_probability(engine_entry, p):
    """The publishing seam for any probability shaped number: the
    value travels with the label the attestation gate allows."""
    decision = probability_render_decision(engine_entry)
    return {"value": float(p),
            "rendered_as": "probability"
            if decision["render_as_probability"]
            else "uncalibrated_score",
            "reason": decision["reason"]}


def assert_probability_renderable(engine_entry):
    """Hard gate for a surface that would render a number as a
    probability: raises unless the attestation is on record."""
    decision = probability_render_decision(engine_entry)
    if not decision["render_as_probability"]:
        raise GradingError(
            f"refusing to render a probability for "
            f"{(engine_entry or {}).get('id')}: {decision['reason']}")
    return True


# ---- abstention coverage audit (separate audit role) ------------------
# Adopted from the abstention_audit.py design in Ausar's forecast
# package (analysis sections 6.5 and 8.2 item 1): outcomes may be
# attached to an abstained attempt only under a separate audit role.
# Audit outcomes measure what the coverage gate hid; they are never
# forecast-skill examples. This audit is read-only: it never appends a
# grade, never alters a forecast row, and never feeds an engine's
# published grade. It resolves refused (and, for comparison, taken)
# outcomes with the same resolve_outcome() and price source the
# grading runner uses, so an outcome kind the grader cannot resolve
# is unresolvable here too, and is named per engine with its reason
# instead of being skipped.

AUDIT_THIN_CELL_MIN = 30
_RESOLVABLE_KINDS = ("close", "return", "abs_return", "close_above",
                     "touch", "binary_event", "max_drawdown", "gap_fill",
                     "close_vs_prior_close_sign", "realised_vol",
                     "realised_range_5s", "cohort_excess_5s",
                     "excess_21s", "return_percent",
                     "excess_return_points", "excess_sign",
                     "pin_breach_half_em", "pin_abs_distance_pct",
                     "pin_in_band",
                     "wall_break_close_through", "flip_close_beyond",
                     "volume_below_frozen_median",
                     "normalisation_sessions", "vol_shape")
_NON_PRICE_KINDS = ("young_figure", "recheck_replication",
                    "first_failure_side")


def _static_unresolvable_reason(outcome):
    """Reason an outcome spec can never be resolved by resolve_outcome,
    checkable without prices, or None when a price route exists."""
    if not isinstance(outcome, dict) or not outcome.get("kind"):
        return "outcome spec carries no kind, so no price route exists for it"
    kind = outcome["kind"]
    if kind in _NON_PRICE_KINDS:
        return (f"outcome kind {kind!r} is not resolvable from "
                f"prices alone in the audit role (it needs a future "
                f"record or sibling wall levels the audit does not "
                f"supply); the grading runner names the same limit")
    if kind not in _RESOLVABLE_KINDS:
        return (f"outcome kind {kind!r} has no resolver in "
                f"grading.resolve_outcome; the grading runner cannot "
                f"resolve it either (carried grading gap)")
    if not outcome.get("symbol"):
        return ("outcome spec carries no symbol, so no price route "
                "exists for it")
    if kind not in ("realised_vol", "vol_shape",
                    "normalisation_sessions") \
            and not outcome.get("at_date"):
        return "outcome spec carries no at_date, so no price route exists for it"
    if kind in ("max_drawdown", "wall_break_close_through",
                "flip_close_beyond", "realised_range_5s") and not all(
            k in outcome for k in ("window_open", "window_close")):
        return f"{kind} outcome is missing window bounds"
    if kind == "gap_fill" and "prior_close" not in outcome:
        return "gap_fill outcome carries no prior_close"
    if kind == "close_vs_prior_close_sign" and "prior_close" not in outcome:
        return "close_vs_prior_close_sign outcome carries no prior_close"
    if kind in ("realised_vol", "vol_shape") and not outcome.get("base_date"):
        return f"{kind} outcome carries no base_date"
    if kind == "normalisation_sessions" and not all(
            k in outcome for k in ("base_date", "window_open",
                                  "window_close")):
        return "normalisation_sessions outcome is missing base or window"
    if kind == "volume_below_frozen_median" and not all(
            k in outcome for k in ("base_date", "at_date",
                                   "frozen_median_volume")):
        return "volume_below_frozen_median outcome is missing fields"
    if kind == "cohort_excess_5s" and not all(
            k in outcome for k in ("base_date", "at_date")):
        return "cohort_excess_5s outcome is missing base or at date"
    if kind == "binary_event" and "realised" not in outcome \
            and not outcome.get("threshold_rule"):
        return ("binary_event outcome carries no realised value and no "
                "price route derives one; the event outcome is not "
                "recorded on the row")
    if kind in ("return", "abs_return") and not outcome.get("base_date"):
        return f"{kind} outcome carries no base_date, so no return can be computed"
    if kind == "close_above" and "threshold" not in outcome:
        return "close_above outcome carries no threshold"
    if kind == "touch" and not all(
            k in outcome for k in ("level", "window_open", "window_close")):
        return "touch outcome is missing level or window bounds"
    return None


def _favourable(kind, realised, binary):
    """Whether the realised outcome was favourable under the outcome's
    own definition: the event happened (binary outcome 1), or a signed
    return came out positive. Kinds with no direction of their own
    (a close level, an absolute move) return None: no favourable share
    is defined for them."""
    if binary is not None:
        return binary == 1.0
    if kind == "return":
        return realised > 0
    return None


def _summarise_cell(pairs):
    """Distribution summary for one (engine, outcome kind) cell.
    pairs: [(realised, favourable_or_None)]. Thin-cell rule: fewer
    than AUDIT_THIN_CELL_MIN graded outcomes publish counts only."""
    graded = len(pairs)
    cell = {"graded": graded, "thin_cell": graded < AUDIT_THIN_CELL_MIN,
            "mean": None, "median": None,
            "favourable_share": None, "favourable_graded": 0}
    if graded < AUDIT_THIN_CELL_MIN:
        return cell
    values = [v for v, _f in pairs]
    cell["mean"] = sum(values) / graded
    cell["median"] = statistics.median(values)
    fav = [f for _v, f in pairs if f is not None]
    cell["favourable_graded"] = len(fav)
    if fav:
        cell["favourable_share"] = sum(1 for f in fav if f) / len(fav)
    return cell


def _audit_side(rows_for_side, prices, as_of):
    """Resolve one side (taken or refused) of one engine's attempts.
    Returns counts, per-kind cells and named unresolvable reasons.
    Every row lands in exactly one bucket: graded, not_yet_matured,
    or unresolvable (with a reason)."""
    graded_pairs = {}   # outcome kind -> [(realised, favourable)]
    not_yet_matured = 0
    reasons = {}
    unresolvable = 0
    for row in rows_for_side:
        outcome = row.get("outcome") or {}
        reason = _static_unresolvable_reason(outcome)
        if reason is not None:
            unresolvable += 1
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        try:
            matured = is_matured(row, prices, as_of=as_of)
        except Exception as exc:  # malformed row: name it, never crash
            unresolvable += 1
            r = f"maturity cannot be checked: {type(exc).__name__}: {exc}"
            reasons[r] = reasons.get(r, 0) + 1
            continue
        if not matured:
            not_yet_matured += 1
            continue
        try:
            realised, binary = resolve_outcome(outcome, prices)
        except Exception as exc:
            unresolvable += 1
            r = f"{type(exc).__name__}: {exc}"
            reasons[r] = reasons.get(r, 0) + 1
            continue
        graded_pairs.setdefault(outcome["kind"], []).append(
            (realised, _favourable(outcome["kind"], realised, binary)))
    cells = [{"kind": kind, **_summarise_cell(pairs)}
             for kind, pairs in sorted(graded_pairs.items())]
    return {"graded": sum(c["graded"] for c in cells),
            "not_yet_matured": not_yet_matured,
            "unresolvable": unresolvable,
            "unresolvable_reasons": [
                {"reason": r, "count": n}
                for r, n in sorted(reasons.items())],
            "outcomes": cells}


def abstention_coverage_audit(rows, prices, as_of=None):
    """Abstention coverage audit over ledger rows. Read-only.

    Per engine: attempts taken (absence_state present), attempts
    refused (any other absence_state), and what prices did on the
    refused attempts, resolved exactly as the engine's own grades
    resolve outcomes, beside the same summary for the attempts taken.
    Refused outcomes never enter any grade. Engines whose abstentions
    cannot be outcome-resolved are reported with the reason, per
    engine, never skipped."""
    by_engine = {}
    for row in rows:
        if row.get("type") != "forecast":
            continue
        eng = by_engine.setdefault(row["engine_id"],
                                   {"taken_rows": [], "refused_rows": [],
                                    "by_absence_state": {},
                                    "by_reason": {},
                                    "without_reasons": 0})
        state = row.get("absence_state")
        if state in (None, "present"):
            eng["taken_rows"].append(row)
        else:
            eng["refused_rows"].append(row)
            eng["by_absence_state"][state] = \
                eng["by_absence_state"].get(state, 0) + 1
            # Per feature reason codes (DEEP-PASS 3.1 item 6): the
            # fixed vocabulary ledger.abstain_reasons makes refusals
            # countable by cause and feature. A refused row with no
            # codes (an empty list, or a legacy row with no field)
            # is counted as without reasons, never silently dropped.
            codes = row.get("abstain_reasons") or []
            if codes:
                for code in codes:
                    eng["by_reason"][code] = \
                        eng["by_reason"].get(code, 0) + 1
            else:
                eng["without_reasons"] += 1
    engines = {}
    for engine_id, eng in sorted(by_engine.items()):
        taken = _audit_side(eng["taken_rows"], prices, as_of)
        refused = _audit_side(eng["refused_rows"], prices, as_of)
        n_refused = len(eng["refused_rows"])
        if n_refused == 0:
            state, reason = "no_abstentions", (
                "the ledger records no abstention for this engine")
        elif refused["graded"] == n_refused:
            state, reason = "covered", (
                "every refused attempt's outcome was resolved from prices")
        elif refused["graded"] > 0:
            state, reason = "partially_covered", (
                f"{refused['graded']} of {n_refused} refused outcomes "
                f"resolved; the rest are named in the counts below")
        elif refused["unresolvable"] > 0:
            state = "unresolvable"
            reason = refused["unresolvable_reasons"][0]["reason"]
        else:
            state, reason = "not_yet_matured", (
                "no refused attempt has reached its horizon close in "
                "the price source yet")
        engines[engine_id] = {
            "taken": len(eng["taken_rows"]),
            "refused": n_refused,
            "refused_by_absence_state": eng["by_absence_state"],
            "refused_by_reason": eng["by_reason"],
            "refused_without_reasons": eng["without_reasons"],
            "taken_graded": taken["graded"],
            "taken_not_yet_matured": taken["not_yet_matured"],
            "taken_unresolvable": taken["unresolvable"],
            "taken_unresolvable_reasons": taken["unresolvable_reasons"],
            "taken_outcomes": taken["outcomes"],
            "refused_graded": refused["graded"],
            "refused_not_yet_matured": refused["not_yet_matured"],
            "refused_unresolvable": refused["unresolvable"],
            "refused_unresolvable_reasons":
                refused["unresolvable_reasons"],
            "refused_outcomes": refused["outcomes"],
            "coverage_state": state,
            "coverage_reason": reason}
    total_by_reason = {}
    for e in engines.values():
        for code, n in e["refused_by_reason"].items():
            total_by_reason[code] = total_by_reason.get(code, 0) + n
    totals = {
        "taken": sum(e["taken"] for e in engines.values()),
        "refused": sum(e["refused"] for e in engines.values()),
        "refused_by_reason": total_by_reason,
        "refused_without_reasons": sum(
            e["refused_without_reasons"] for e in engines.values()),
        "refused_graded": sum(e["refused_graded"] for e in engines.values()),
        "engines_with_abstentions": sorted(
            e for e, v in engines.items() if v["refused"] > 0),
        "engines_refused_unresolvable": sorted(
            e for e, v in engines.items() if v["refused_unresolvable"] > 0)}
    return {"engines": engines, "totals": totals}
