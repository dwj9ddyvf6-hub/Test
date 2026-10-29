"""Auditable closed-trade samples and cashflow-aware benchmark comparisons."""
import hashlib
import json
import math
import statistics
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from .providers import exchange_calendar
from .strategy_contract import installed_strategies


UTC = timezone.utc
NY = ZoneInfo("America/New_York")
MIN_DAILY_RETURNS = 20  # Descriptive reporting gate, not statistical significance.
RAW_OHLC_BASES = {"raw", "raw ohlc", "raw alpaca iex ohlc"}
CLOSE_WINDOW = timedelta(minutes=5)


def timepoint(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be an ISO string")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Timestamp has no timezone")
    return stamp.astimezone(UTC)


def clean(row):
    return row.get("missing_marks") == 0 and row.get("stale_marks") == 0


def nav_curve(snapshots, flows):
    """Unitized clean NAV; deposits buy units at the adjacent pre-flow value.

    Keeping units, rather than multiplying ratios, preserves a loss to zero
    and later marks without dividing by a zero intermediate equity.
    """
    if len(snapshots) < 2 or not clean(snapshots[0]) or snapshots[0]["equity_cents"] <= 0:
        return None
    stamped_flows = [(timepoint(f["timestamp"]), f) for f in flows]
    flow_times = [stamp for stamp, _ in stamped_flows]
    if any(b < a for a, b in zip(flow_times, flow_times[1:])):
        return None
    units, curve = Decimal(snapshots[0]["equity_cents"]), [Decimal(1)]
    for prior, current in zip(snapshots, snapshots[1:]):
        if not clean(current):
            return None
        left, right = timepoint(prior["timestamp"]), timepoint(current["timestamp"])
        # A timestamp shared by a funding and a valuation cannot prove which
        # side of the cashflow that valuation represents.
        deposits = stamped_flows[bisect_left(flow_times, left):bisect_right(flow_times, right)]
        if right < left or any(stamp in (left, right) for stamp, _ in deposits):
            return None
        if any(stamp - left > timedelta(seconds=5)
               or right - stamp > timedelta(seconds=5) for stamp, _ in deposits):
            return None
        amount = sum((Decimal(f["amount_cents"]) for _, f in deposits), Decimal(0))
        if amount:
            if curve[-1] <= 0:
                return None  # A recapitalization at nonpositive NAV has no unit price.
            units += amount / curve[-1]
            if units <= 0:
                return None  # Fully redeemed units do not have a remaining NAV.
        curve.append(Decimal(current["equity_cents"]) / units)
    return curve


def flow_adjusted_return(snapshots, flows):
    """Clean unitized return, with deposits removed at their valued boundary."""
    curve = nav_curve(snapshots, flows)
    return float((curve[-1] - 1) * 100) if curve is not None else None


def finite_number(value):
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError, TypeError):
        return False


def metric(value, unit, samples, minimum, method, reason=None):
    if value is not None and not finite_number(value):
        value, reason = None, "Nonfinite result withheld"
    return {"value": value, "unit": unit, "samples": samples,
            "minimum_samples": minimum, "status": "available" if value is not None else "withheld",
            "reason": reason if value is None else None, "method": method}


def trade_metrics(samples, complete=True):
    pnl = [Decimal(e["net_pnl_cents"]) / 100 if "net_pnl_cents" in e
           else Decimal(str(e["net_pnl"])) for e in samples]
    wins, losses = [v for v in pnl if v > 0], [v for v in pnl if v < 0]
    reason = None if complete else "Broker opening inventory and fee completeness are not independently verified"
    def item(value, unit, count, method, empty):
        return metric(value if complete else None, unit, count, 1, method, reason or empty)
    return {
        "net_expectancy": item(float(sum(pnl) / len(pnl)) if pnl else None, "USD", len(pnl),
                               "Mean recorded net P/L per completed flat-to-flat episode, including flats", "No completed round trips"),
        "profit_factor": item(float(sum(wins) / abs(sum(losses))) if losses else None, "ratio", len(pnl),
                              "Sum positive net episode P/L divided by absolute sum negative net episode P/L",
                              "No losing completed round trips; finite profit factor is undefined" if pnl else "No completed round trips"),
        "average_net_win": item(float(sum(wins) / len(wins)) if wins else None, "USD", len(wins),
                                "Mean net P/L conditional on a positive completed episode", "No winning completed round trips"),
        "average_net_loss": item(float(sum(losses) / len(losses)) if losses else None, "USD", len(losses),
                                 "Mean signed net P/L conditional on a negative completed episode", "No losing completed round trips"),
    }


def unavailable_risk(reason):
    return {key: metric(None, unit, 0, minimum, method, reason) for key, unit, minimum, method in (
        ("daily_volatility_percent", "percent", 2, "Sample standard deviation of contiguous session observation returns"),
        ("annualized_volatility_percent", "percent", MIN_DAILY_RETURNS, "Daily sample standard deviation times sqrt(252); descriptive scaling"),
        ("sharpe_ratio", "ratio", MIN_DAILY_RETURNS, "Mean daily excess return / sample standard deviation times sqrt(252); explicit annual risk-free rate zero"),
        ("max_drawdown_percent", "percent", 2, "Peak-to-trough loss of recorded clean cashflow-adjusted NAV; excludes unobserved intraday extrema"),
        ("beta_spy", "ratio", MIN_DAILY_RETURNS, "Sample covariance(book, SPY) / sample variance(SPY), same contiguous session pairs"),
        ("beta_qqq", "ratio", MIN_DAILY_RETURNS, "Sample covariance(book, QQQ) / sample variance(QQQ), same contiguous session pairs"),
    )}


def risk_metrics(daily, benchmark_daily, curve, gap=False, daily_reason=None):
    count = len(daily)
    metrics = unavailable_risk("Insufficient clean daily observations")
    reason = daily_reason or ("Missing exchange sessions; multi-session returns are not treated as daily" if gap else None)
    enough = count >= 2 and reason is None
    sd = statistics.stdev(daily) if enough else None
    metrics["daily_volatility_percent"] = metric(sd * 100 if sd is not None else None, "percent", count, 2,
        metrics["daily_volatility_percent"]["method"], reason or "At least two contiguous daily returns required")
    for key in ("annualized_volatility_percent", "sharpe_ratio"):
        value = None
        why = reason or f"At least {MIN_DAILY_RETURNS} contiguous daily returns required; this is a descriptive display gate"
        if enough and count >= MIN_DAILY_RETURNS:
            if key == "annualized_volatility_percent":
                value = sd * math.sqrt(252) * 100
            elif sd > 0:
                value = statistics.mean(daily) / sd * math.sqrt(252)
            else:
                why = "Zero daily variance; Sharpe denominator is zero"
        metrics[key] = metric(value, metrics[key]["unit"], count, MIN_DAILY_RETURNS, metrics[key]["method"], why)
    if curve is not None:
        peak, worst = Decimal(1), Decimal(0)
        for nav in curve:
            peak = max(peak, nav)
            worst = max(worst, (peak - nav) / peak)
        metrics["max_drawdown_percent"] = metric(float(worst * 100), "percent", len(curve), 2,
            metrics["max_drawdown_percent"]["method"])
    for sym in ("SPY", "QQQ"):
        values = benchmark_daily.get(sym, [])
        value, why = None, reason or f"At least {MIN_DAILY_RETURNS} matching contiguous daily return pairs required"
        if reason is None and len(values) == count and count >= MIN_DAILY_RETURNS:
            try:
                variance = statistics.variance(values)
            except (OverflowError, ValueError):
                variance = None
            if variance is None or not finite_number(variance):
                why = "Nonfinite benchmark variance; beta withheld"
            elif variance > 0:
                x, y = statistics.mean(daily), statistics.mean(values)
                covariance = sum((a - x) * (b - y) for a, b in zip(daily, values)) / (count - 1)
                value = covariance / variance
            else:
                why = "Benchmark daily variance is zero; beta is undefined"
        key = "beta_" + sym.lower()
        metrics[key] = metric(value, "ratio", min(count, len(values)), MIN_DAILY_RETURNS, metrics[key]["method"], why)
    return metrics


def completed_episodes(fills):
    """Count full long/short round trips; a partial exit is not a closed trade."""
    active, complete = {}, []
    for fill in fills:
        key = (fill["book_id"], fill["symbol"])
        quantity = Decimal(str(fill["quantity"])) * (1 if fill["side"] == "buy" else -1)
        fill_at = timepoint(fill["timestamp"] or fill["observed_at"])
        episode = active.get(key)
        if episode is None:
            active[key] = {"book_id": key[0], "symbol": key[1], "quantity": quantity, "direction": "long" if quantity > 0 else "short", "opened_at": fill["timestamp"] or fill["observed_at"], "gross_realized_cents": fill["realized_cents"], "fees_cents": fill["fee_cents"], "fill_ids": [fill["id"]]}
            active[key]["last_fill_at"], active[key]["execution_times_monotonic"] = fill_at, True
            continue
        episode["execution_times_monotonic"] &= fill_at >= episode["last_fill_at"]
        episode["last_fill_at"] = fill_at
        prior = episode["quantity"]
        total = prior + quantity
        crossed = prior * total < 0
        closing_fee = int((Decimal(fill["fee_cents"]) * abs(prior / quantity)).quantize(Decimal(1), rounding=ROUND_HALF_UP)) if crossed else fill["fee_cents"]
        episode["gross_realized_cents"] += fill["realized_cents"]
        episode["fees_cents"] += closing_fee
        episode["fill_ids"].append(fill["id"])
        if total == 0 or crossed:
            episode["closed_at"] = fill["timestamp"] or fill["observed_at"]
            gross_cents, fee_cents = episode.pop("gross_realized_cents"), episode.pop("fees_cents")
            episode["net_pnl_cents"] = gross_cents - fee_cents
            episode["gross_pnl"] = gross_cents / 100
            episode["fees"] = fee_cents / 100
            episode["net_pnl"] = episode["net_pnl_cents"] / 100
            episode["duration_seconds"] = (timepoint(episode["closed_at"]) - timepoint(episode["opened_at"])).total_seconds() if episode["execution_times_monotonic"] else None
            episode.pop("last_fill_at")
            episode.pop("quantity")
            complete.append(episode)
            active.pop(key)
            if crossed:
                active[key] = {"book_id": key[0], "symbol": key[1], "quantity": total, "direction": "long" if total > 0 else "short", "opened_at": fill["timestamp"] or fill["observed_at"], "gross_realized_cents": 0, "fees_cents": fill["fee_cents"] - closing_fee, "fill_ids": [fill["id"]]}
                active[key]["last_fill_at"], active[key]["execution_times_monotonic"] = fill_at, True
        else:
            episode["quantity"] = total
    return complete


class Analytics:
    def __init__(self, store, trading):
        self.store, self.trading = store, trading

    def snapshot(self):
        reports = []
        with self.store.connect() as con:
            con.execute("BEGIN")
            registry = installed_strategies(con=con)
            # Financial mutations are causal in append order, even if the
            # system clock reverses between two committed fills.
            all_fills = [dict(r) for r in con.execute("SELECT * FROM p_fills ORDER BY rowid")]
            episodes = completed_episodes(all_fills)
            fill_map = {f["id"]: f for f in all_fills}
            for episode in episodes:
                episode["excursion"] = self._excursion(con, episode, fill_map)
            for row in con.execute("SELECT * FROM p_books ORDER BY created_at"):
                book = dict(row)
                bid = book["id"]
                account = self.trading._account(con, row, datetime.now(UTC))[0]
                samples = [e for e in episodes if e["book_id"] == bid]
                returns = [dict(r) for r in con.execute("SELECT * FROM p_equity WHERE book_id=? ORDER BY rowid", (bid,))]
                flows = [dict(r) for r in con.execute("SELECT * FROM p_fundings WHERE book_id=? ORDER BY rowid", (bid,))]
                book_fills = [f for f in all_fills if f["book_id"] == bid]
                fill_times = [(timepoint(f["observed_at"]), timepoint(f["timestamp"] or f["observed_at"])) for f in book_fills]
                clock_coverage = {"fill_timestamps_monotonic": all(b[0] >= a[0] and b[1] >= a[1] for a, b in zip(fill_times, fill_times[1:])),
                    **{label: all(b >= a for a, b in zip(values, values[1:])) for label, values in (
                        ("equity_timestamps_monotonic", [timepoint(r["timestamp"]) for r in returns]),
                        ("funding_timestamps_monotonic", [timepoint(f["timestamp"]) for f in flows]))}}
                clock_valid = all(clock_coverage.values())
                reason = "Awaiting clean end-of-session valuations and matching benchmark bars"
                report = {"book_id": bid, "book_name": book["name"], "account": account,
                          "closed_roundtrips": len(samples), "wins": sum(e["net_pnl_cents"] > 0 for e in samples),
                          "losses": sum(e["net_pnl_cents"] < 0 for e in samples),
                          "win_rate_percent": sum(e["net_pnl_cents"] > 0 for e in samples) * 100 / len(samples) if samples else None,
                          "closed_trade_net_pnl": sum(e["net_pnl_cents"] for e in samples) / 100,
                          "return_percent": None, "benchmarks": [], "coverage": reason, "profitability_claim": False,
                          "metrics": {**trade_metrics(samples, book["broker"] == "local"), **unavailable_risk(reason)},
                          "trade_accounting_coverage": {"status": "recorded_local_fees" if book["broker"] == "local" else "unverified_broker_basis_and_fees",
                              "scope": "Local completed episodes include all recorded fees; broker starting inventory and fee completeness must be independently established"},
                          "clock_coverage": {**clock_coverage, "scope": "Normalized timestamps in immutable ledger append order"},
                          "risk_assumptions": {"risk_free_annual_rate": 0, "sessions_per_year": 252,
                              "minimum_daily_returns": MIN_DAILY_RETURNS,
                              "scope": "Descriptive close-window observations; the sample gate is not a significance test or claim of future profitability",
                              "annualization_assumption": "Conventional sqrt(252) scaling assumes stable daily second moments and negligible serial covariance; no autocorrelation correction is inferred"}}
                if book["broker"] == "local":
                    strategy_owned = any(r["book_id"] == bid for r in registry)
                    aligned = self._aligned(con, returns, flows, require_adjusted=strategy_owned) if clock_valid else {
                        "coverage": "Recorded ledger timestamps moved backwards; chronological return and risk performance withheld",
                        "metrics": unavailable_risk("Recorded ledger timestamps moved backwards; chronological return and risk performance withheld")}
                    report["metrics"].update(aligned.pop("metrics"))
                    report.update(aligned)
                else:
                    report["coverage"] = "Broker cashflow, initial inventory and fee coverage are incomplete; account returns and net trade statistics are withheld"
                    for key in ("closed_roundtrips", "wins", "losses", "win_rate_percent", "closed_trade_net_pnl"):
                        report[key] = None
                    report["recorded_flattening_sequences"] = len(samples)
                    report["metrics"].update(unavailable_risk(report["coverage"]))
                action_affected = self._has_table(con, "a_strategy_actions") and con.execute(
                    "SELECT 1 FROM a_strategy_actions WHERE book_id=? AND status<>'not_entitled' LIMIT 1", (bid,)).fetchone() is not None
                if action_affected:
                    # Raw buy/sell quantities use different units across a
                    # split; raw fill P/L also excludes accrued dividends.
                    # NAV includes those action assets, but the episode tape
                    # must be normalized before claiming net trade statistics.
                    reason = "Corporate actions require an action-normalized episode tape; raw fill profit statistics withheld"
                    report["trade_accounting_coverage"] = {"status": "withheld", "reason": reason,
                        "scope": "Book NAV separately includes recorded corporate-action assets; raw fill episodes do not"}
                    for key in ("closed_roundtrips", "wins", "losses", "win_rate_percent", "closed_trade_net_pnl"):
                        report[key] = None
                    unavailable = trade_metrics([], False)
                    for item in unavailable.values():
                        item["reason"] = reason
                    report["metrics"].update(unavailable)
                for episode in samples:
                    episode["accounting_status"] = report["trade_accounting_coverage"]["status"]
                    if not clock_valid:
                        episode["duration_seconds"] = None
                        episode["excursion"] = {"mfe_percent": None, "mae_percent": None, "status": "withheld",
                            "reason": "Recorded ledger timestamps moved backwards; actual holding-time extrema cannot be established",
                            "scope": "Time-based statistics require monotonic recorded ledger timestamps"}
                    if book["broker"] != "local" or action_affected:
                        # A broker delta stream can start with a closing fill
                        # against unknown inventory; it cannot establish a
                        # round trip or a complete net P/L sample.
                        for key in ("gross_pnl", "fees", "net_pnl", "net_pnl_cents"):
                            episode[key] = None
                        episode["excursion"] = {"mfe_percent": None, "mae_percent": None, "status": "withheld",
                            "reason": "Corporate-action units require a normalized tape" if action_affected else "Broker opening inventory is unverified; recorded fill sequences do not establish a complete fixed-size holding interval",
                            "scope": "Recorded broker deltas, with no inferred opening-position or holding-period extrema"}
                reports.append(report)
        return {"books": reports, "completed_trades": episodes[-1000:],
                "benchmark_definitions": {"QQQ": "Nasdaq-100 ETF", "SPY": "S&P 500 ETF proxy"},
                "return_method": "Chain of clean valued cashflow-adjusted subperiod returns between common session-close-window baselines; deposits require adjacent pre/post valuations",
                "strategy_count": len(registry), "scope": "Measured evidence; outperformance is not a prediction or proof of durable edge"}

    @staticmethod
    def _has_table(con, name):
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

    @staticmethod
    def _verified_revision(revision):
        """Read archive content only after its identity, metadata and bars agree."""
        try:
            data = json.loads(revision["data"])
            if not isinstance(data, dict) or not isinstance(data.get("bars"), list):
                return None
            digest = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            if digest != revision["id"] or digest != revision["content_sha256"]:
                return None
            if any(not isinstance(data.get(key), str) or data[key] != revision[key]
                   for key in ("symbol", "range", "interval", "provider", "source", "adjustment")):
                return None
            observed, fetched = timepoint(revision["observed_at"]), timepoint(revision["fetched_at"])
            if observed > fetched:
                return None
            stamps = []
            for bar in data["bars"]:
                stamps.append(timepoint(bar["timestamp"]))
                values = {key: Decimal(str(bar[key])) for key in ("open", "high", "low", "close")}
                if any(not v.is_finite() or v <= 0 for v in values.values()):
                    return None
                if not values["low"] <= min(values["open"], values["close"]) <= max(values["open"], values["close"]) <= values["high"]:
                    return None
                adjusted = bar.get("adjusted_close")
                if adjusted is not None and (not Decimal(str(adjusted)).is_finite() or Decimal(str(adjusted)) <= 0):
                    return None
                volume = bar.get("volume")
                if volume is not None and (not Decimal(str(volume)).is_finite() or Decimal(str(volume)) < 0):
                    return None
            if any(b <= a for a, b in zip(stamps, stamps[1:])):
                return None
            asof = timepoint(revision["provider_asof"]) if revision["provider_asof"] else None
            if asof != (stamps[-1] if stamps else None) or (stamps and stamps[-1] > observed + timedelta(seconds=5)):
                return None
            return data
        except (ValueError, TypeError, KeyError, InvalidOperation, OverflowError):
            return None

    def _aligned(self, con, snapshots, flows, require_adjusted=False):
        def withheld(reason):
            return {"coverage": reason, "metrics": unavailable_risk(reason)}
        days, calendars = {}, {}
        stamped_rows = [(timepoint(row["timestamp"]), row) for row in snapshots]
        row_times = [stamp for stamp, _ in stamped_rows]
        if any(b < a for a, b in zip(row_times, row_times[1:])):
            return withheld("Recorded equity timestamps moved backwards; chronological performance withheld")
        snapshots = [row for _, row in stamped_rows]
        for stamp, row in stamped_rows:
            date = stamp.astimezone(NY).date().isoformat()
            if date not in calendars:
                calendars[date] = exchange_calendar(datetime.fromisoformat(date).replace(hour=12, tzinfo=NY))
            calendar = calendars[date]
            close = timepoint(calendar["close_at"]) if calendar.get("close_at") else None
            # First recorded valuation in a bounded close window; never an overnight mark.
            if close and close <= stamp <= close + CLOSE_WINDOW and calendar["session_date"] == date:
                days.setdefault(date, row)
        if not self._has_table(con, "a_bar_cache") or not self._has_table(con, "a_bar_revisions"):
            return withheld("No archived daily benchmark history")
        candidates = {}
        for sym in ("QQQ", "SPY"):
            caches = con.execute("SELECT * FROM a_bar_cache WHERE symbol=? AND interval='1d' ORDER BY fetched_at DESC", (sym,)).fetchall()
            if not caches:
                return withheld("Missing archived daily history for " + sym)
            candidates[sym], rejected = [], set()
            for cached in caches:
                try:
                    receipt = json.loads(cached["data"])
                    if not isinstance(receipt, dict):
                        rejected.add("integrity")
                        continue
                    revision = con.execute("SELECT * FROM a_bar_revisions WHERE id=?", (receipt.get("revision_id"),)).fetchone()
                    data = self._verified_revision(revision) if revision else None
                    if (data is None or data["symbol"] != sym or data["range"] != cached["range"]
                            or data["interval"] != "1d" or receipt.get("content_sha256") != revision["content_sha256"]
                            or any(receipt.get(key) != value for key, value in data.items())
                            or receipt.get("fetched_at") != cached["fetched_at"]):
                        rejected.add("integrity")
                        continue
                    if data.get("truncated"):
                        rejected.add("truncated")
                        continue
                    bars, fetched = {}, timepoint(cached["fetched_at"])
                    for bar in data["bars"]:
                        stamp = timepoint(bar["timestamp"])
                        # Some vendors encode a session-date label as UTC midnight.
                        date = stamp.date().isoformat() if stamp.time().replace(tzinfo=None).isoformat() == "00:00:00" else stamp.astimezone(NY).date().isoformat()
                        if date not in days:
                            # Max vendor history can predate the bundled
                            # calendar. Only recorded desk dates can align.
                            continue
                        session = calendars[date]
                        if session["is_session"] and timepoint(session["close_at"]) <= fetched:
                            if date in bars:
                                raise ValueError("Multiple daily bars for one exchange session")
                            bars[date] = bar
                    candidates[sym].append(({**data, "revision_id": revision["id"]}, bars, fetched))
                except (ValueError, TypeError, KeyError, OverflowError):
                    rejected.add("integrity")
            if not candidates[sym]:
                return withheld(("Truncated " + sym + " history; complete aligned sampling is not verified") if rejected == {"truncated"}
                                else "Unverified " + sym + " archive integrity or daily-bar coverage; comparison withheld")
        eligible = sorted(days)
        # Exclude initial genuinely unfunded zero days; retain losses to zero after funding.
        while eligible and days[eligible[0]]["equity_cents"] == 0 and not any(timepoint(f["timestamp"]) <= timepoint(days[eligible[0]]["timestamp"]) for f in flows):
            eligible.pop(0)
        # Reading a shorter chart must not erase an intact longer baseline.
        # Select whole immutable revisions, maximizing common recorded coverage;
        # choose the newest receipts only when coverage is tied.
        chosen = max(((qqq, spy, sorted(set(eligible).intersection(qqq[1], spy[1])))
                      for qqq in candidates["QQQ"] for spy in candidates["SPY"]),
                     key=lambda pair: (len(pair[2]), min(pair[0][2], pair[1][2]), max(pair[0][2], pair[1][2])))
        common = chosen[2]
        histories = {"QQQ": chosen[0][:2], "SPY": chosen[1][:2]}
        if len(common) < 2:
            return withheld("At least two matching close-window valuations and completed benchmark sessions required")
        start, end = days[common[0]], days[common[-1]]
        left, right = timepoint(start["timestamp"]), timepoint(end["timestamp"])
        rows = snapshots[bisect_left(row_times, left):bisect_right(row_times, right)]
        curve = nav_curve(rows, flows)
        if curve is None:
            return withheld("Stale/missing marks, nonpositive opening NAV or funding without adjacent clean pre/post valuations; comparison withheld")
        value = float((curve[-1] - 1) * 100)
        if not finite_number(value):
            return withheld("Nonfinite cashflow-adjusted return; comparison withheld")
        daily, benchmark_daily, benchmarks, daily_reason = [], {}, [], None
        gap = any(calendars[b]["previous_session"] != a for a, b in zip(common, common[1:]))
        for a, b in zip(common, common[1:]):
            t0, t1 = timepoint(days[a]["timestamp"]), timepoint(days[b]["timestamp"])
            part = snapshots[bisect_left(row_times, t0):bisect_right(row_times, t1)]
            result = flow_adjusted_return(part, flows)
            if result is None:
                daily_reason = "Nonpositive daily opening NAV or incomplete daily flow coverage; percentage daily risk statistics withheld"
            else:
                daily.append(result / 100)
        for sym, (data, bars) in histories.items():
            adjusted = all(bars[d].get("adjusted_close") is not None for d in common)
            if require_adjusted and not adjusted:
                return withheld("Strategy total-return NAV requires adjusted QQQ and SPY benchmarks; raw-close comparison withheld")
            field = "adjusted_close" if adjusted else "close"
            prices = [Decimal(str(bars[d][field])) for d in common]
            if any(not price.is_finite() or price <= 0 for price in prices):
                return withheld("Invalid benchmark prices; comparison withheld")
            benchmark_daily[sym] = [float(b / a - 1) for a, b in zip(prices, prices[1:])]
            bench = float((prices[-1] / prices[0] - 1) * 100)
            if not all(finite_number(v) for v in [bench, value - bench, *benchmark_daily[sym]]):
                return withheld("Nonfinite benchmark return after price-ratio calculation; comparison withheld")
            benchmarks.append({"symbol": sym, "return_percent": bench, "excess_return_points": value - bench,
                               "scope": "Vendor adjusted-close return" if adjusted else "Raw close price return; dividend adjustments unavailable",
                               "source": data.get("source"), "revision_id": data.get("revision_id"),
                               "baseline_date": common[0], "through_date": common[-1]})
        return {"return_percent": value, "benchmarks": benchmarks, "coverage": "Aligned clean observations within five minutes after session close; exact exchange-close marks are not inferred",
                "baseline_at": start["timestamp"], "through_at": end["timestamp"], "matched_sessions": len(common),
                "daily_return_coverage": {"returns": len(daily), "contiguous_sessions": not gap, "reason": daily_reason,
                    "baseline_date": common[0], "through_date": common[-1], "close_window_seconds": int(CLOSE_WINDOW.total_seconds())},
                "metrics": risk_metrics(daily, benchmark_daily, curve, gap, daily_reason)}

    def _excursion(self, con, episode, fill_map):
        scope = "Gross vendor-observed instrument price excursion from actual fixed-size entry; timestamp-complete raw regular-session OHLC interval, not certified consolidated-market extrema; excludes fees"
        def withheld(reason):
            return {"mfe_percent": None, "mae_percent": None, "status": "withheld", "reason": reason, "scope": scope}
        fills = [fill_map[fid] for fid in episode["fill_ids"]]
        if len(fills) != 2 or any(not f.get("timestamp") for f in fills):
            return withheld("Changing position size or imprecise execution times; exact fixed-size holding interval unavailable")
        if Decimal(str(fills[0]["quantity"])) != Decimal(str(fills[1]["quantity"])):
            return withheld("Position flip or unequal opening/closing quantities; fixed-size excursion not inferred")
        opened, closed = timepoint(episode["opened_at"]), timepoint(episode["closed_at"])
        session = exchange_calendar(opened)
        if not session["is_session"] or closed <= opened or opened < timepoint(session["open_at"]) or closed > timepoint(session["close_at"]):
            return withheld("Holding interval is not wholly within one regular exchange session")
        if not self._has_table(con, "a_bar_revisions"):
            return withheld("No archived complete intraday bars; sparse quotes cannot establish interval extrema")
        durations = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "60m": 3600}
        archived = con.execute("SELECT * FROM a_bar_revisions WHERE symbol=? ORDER BY observed_at DESC LIMIT 200", (episode["symbol"],)).fetchall()
        nonfinite_excursion = False
        for revision in archived:
            seconds = durations.get(revision["interval"])
            if seconds is None:
                continue
            data = self._verified_revision(revision)
            if data is None:
                continue
            if data.get("truncated") or revision["adjustment"].strip().lower() not in RAW_OHLC_BASES:
                # Adjusted OHLC may not share the actual execution-price basis.
                continue
            bars = sorted(data.get("bars", []), key=lambda b: timepoint(b["timestamp"]))
            inside = [b for b in bars if opened <= timepoint(b["timestamp"]) < closed]
            if not inside or timepoint(inside[0]["timestamp"]) != opened or timepoint(inside[-1]["timestamp"]) + timedelta(seconds=seconds) != closed:
                continue
            if any(timepoint(b["timestamp"]) - timepoint(a["timestamp"]) != timedelta(seconds=seconds) for a, b in zip(inside, inside[1:])):
                continue
            if timepoint(revision["observed_at"]) < closed:
                continue
            prices = [Decimal(str(b[field])) for b in inside for field in ("low", "high")]
            entry, exit_price = Decimal(str(fills[0]["price"])), Decimal(str(fills[1]["price"]))
            if entry <= 0 or any(not v.is_finite() or v <= 0 for v in prices) or any(Decimal(str(b["low"])) > Decimal(str(b["high"])) for b in inside):
                continue
            low, high = min(prices + [entry, exit_price]), max(prices + [entry, exit_price])
            favorable, adverse = (high - entry, entry - low) if episode["direction"] == "long" else (entry - low, high - entry)
            mfe, mae = float(favorable / entry * 100), float(adverse / entry * 100)
            if not finite_number(mfe) or not finite_number(mae):
                nonfinite_excursion = True
                continue
            return {"mfe_percent": mfe, "mae_percent": mae,
                    "status": "available", "reason": None, "scope": scope, "bar_count": len(inside),
                    "interval": revision["interval"], "revision_id": revision["id"], "source": revision["source"],
                    "observed_at": revision["observed_at"], "opened_at": episode["opened_at"], "closed_at": episode["closed_at"],
                    "provider": revision["provider"], "finality": data.get("finality", "provisional_vendor_observation"),
                    "completeness": data.get("completeness", {"status": "timestamp_complete_holding_interval", "exchange_coverage": "not independently certified"}),
                    "feed_scope": "Alpaca IEX observations" if revision["provider"] == "alpaca" else revision["source"]}
        return withheld("Nonfinite vendor price-excursion ratio withheld" if nonfinite_excursion else "No complete explicitly raw intraday-bar revision exactly covers the holding interval; sparse quotes, daily ranges, overlapping bars and unknown adjustment bases are insufficient")


def analytics_router(analytics):
    router = APIRouter()

    @router.get("/api/reports")
    def reports():
        return analytics.snapshot()

    @router.get("/api/public/desk")
    def projection():
        state = analytics.trading.snapshot()
        performance = analytics.snapshot()
        return {"name": "Aster Desk", "mode": "paper", "strategy_count": performance["strategy_count"], "read_only": True, "books": [{"id": b["id"], "name": b["name"], "kind": b["kind"], "broker": b["broker"], "account": b["account"], "updated_at": b["updated_at"]} for b in state["books"]], "positions": [{k: p.get(k) for k in ("book_id", "symbol", "quantity", "mark_price", "market_value", "unrealized_pnl", "quote_fresh")} for p in state["positions"]], "performance": performance, "scope": "Read-only projection with no order, policy, instructions or credential fields"}

    return router
