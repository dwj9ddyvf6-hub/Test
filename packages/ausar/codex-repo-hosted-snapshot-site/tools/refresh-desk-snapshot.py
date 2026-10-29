#!/usr/bin/env python3
"""Export a public-safe Ausar paper snapshot from the local R24 read-only API.

The API has legacy Aster labels and contains account identifiers. This exporter
verifies the release README's Ausar identity, then emits a strict field allowlist
with stable public book aliases. It never writes account IDs, broker account
names, user names, credentials, orders, or free-form model output.

The public page serves a static snapshot. This script refreshes the local artifact
only; commit and push the new artifact to publish the updated observation.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist" / "data" / "desk-snapshot.json"
DEFAULT_RELEASE = Path("/workspace/ausar-r24b-release-2026-10-10")
MARKET_INSTRUMENTS = [
    {"symbol": "AMEX:SPY", "label": "S&P 500 ETF"},
    {"symbol": "NASDAQ:QQQ", "label": "Nasdaq-100 ETF"},
    {"symbol": "COINBASE:BTCUSD", "label": "Bitcoin spot USD"},
    {"symbol": "COINBASE:ETHUSD", "label": "Ether spot USD"},
]
ACCOUNT_FIELDS = (
    "equity", "cash", "market_value", "gross_exposure", "reserved_cash",
    "available_cash", "realized_pnl", "unrealized_pnl", "fees",
)
METRIC_FIELDS = (
    "net_expectancy", "profit_factor", "average_net_win", "average_net_loss",
    "daily_volatility_percent", "annualized_volatility_percent", "sharpe_ratio",
    "max_drawdown_percent", "beta_spy", "beta_qqq",
)
BENCHMARK_SYMBOLS = {"SPY", "QQQ"}


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def safe_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def safe_currency(value: Any) -> str:
    if isinstance(value, str) and re.fullmatch(r"[A-Z]{3,6}", value):
        return value
    return "UNK"


def get_json(port: int, path: str) -> dict | None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        headers={"Accept": "application/json", "Cache-Control": "no-store"},
    )
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            if response.status != 200:
                return None
            data = json.load(response)
            return data if isinstance(data, dict) else None
    except (OSError, urllib.error.URLError, ValueError, TimeoutError):
        return None


def metric_record(metrics: Any) -> dict[str, dict[str, Any]]:
    metrics = metrics if isinstance(metrics, dict) else {}
    result: dict[str, dict[str, Any]] = {}
    for name in METRIC_FIELDS:
        item = metrics.get(name)
        if not isinstance(item, dict):
            result[name] = {"value": None, "samples": None, "minimum_samples": None, "status": "unavailable"}
            continue
        status = item.get("status")
        result[name] = {
            "value": finite_number(item.get("value")),
            "samples": safe_int(item.get("samples")),
            "minimum_samples": safe_int(item.get("minimum_samples")),
            "status": status if isinstance(status, str) and re.fullmatch(r"[a-z_]{1,32}", status) else "unavailable",
        }
    return result


def safe_benchmarks(value: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return result
    for item in value:
        if not isinstance(item, dict):
            continue
        symbol = item.get("symbol", item.get("benchmark"))
        if symbol not in BENCHMARK_SYMBOLS:
            continue
        result.append({
            "symbol": symbol,
            "portfolio_return_percent": finite_number(item.get("portfolio_return_percent")),
            "benchmark_return_percent": finite_number(item.get("benchmark_return_percent")),
            "excess_return_percent": finite_number(item.get("excess_return_percent", item.get("excess_percent"))),
        })
    return result


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".desk-snapshot-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def blank_snapshot(reason: str) -> dict:
    return {
        "schema": "AUSAR_PUBLIC_TERMINAL_SNAPSHOT_V1",
        "data_status": "unobserved",
        "observed_at_utc": None,
        "unavailable_reason": reason,
        "public_scope": "Paper portfolio, positions, and account performance only. Private account identifiers, broker account names, user names, credentials, orders, and free-form AI output are omitted.",
        "desk": {"name": "Ausar", "mode": "paper", "strategy_count": None},
        "books": [],
        "positions": [],
        "currency_totals": {},
        "performance_summary": {"closed_roundtrips": None, "wins": None, "losses": None},
        "benchmark_note": "Benchmark-relative returns have not been observed.",
        "services": {"main": {"observed": False}, "wave": {"observed": False}, "scheduled_briefs": {"enabled": False}},
        "market_data": {"ticker_widget": "TradingView", "refresh_mode": "Vendor and exchange delays apply.", "instruments": MARKET_INSTRUMENTS},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--release-dir", type=Path, default=Path(os.environ.get("AUSAR_RELEASE_DIR", str(DEFAULT_RELEASE))))
    args = parser.parse_args()

    release_readme = args.release_dir / "README.md"
    identity_proof = "Ausar is the current name of the desk formerly called Aster."
    if not release_readme.is_file() or identity_proof not in release_readme.read_text(encoding="utf-8", errors="replace"):
        snapshot = blank_snapshot("The configured local release did not prove Ausar desk identity.")
        write_json(args.output.resolve(), snapshot)
        print(json.dumps({"data_status": "unobserved", "reason": "Ausar source identity check failed"}))
        return 2

    desk = get_json(8787, "/api/public/desk")
    health = get_json(8787, "/api/health")
    wave_health = get_json(8791, "/api/health")
    if not isinstance(desk, dict) or desk.get("mode") != "paper" or desk.get("read_only") is not True:
        snapshot = blank_snapshot("The local Ausar paper read-only projection is unavailable.")
        write_json(args.output.resolve(), snapshot)
        print(json.dumps({"data_status": "unobserved", "reason": "paper read-only projection unavailable"}))
        return 2

    raw_performance = desk.get("performance")
    raw_book_rows = raw_performance.get("books") if isinstance(raw_performance, dict) else None
    raw_book_rows = raw_book_rows if isinstance(raw_book_rows, list) else []
    id_values = sorted({row.get("book_id") for row in raw_book_rows if isinstance(row, dict) and isinstance(row.get("book_id"), str)})
    aliases = {book_id: f"Paper book {index:02d}" for index, book_id in enumerate(id_values, start=1)}

    books: list[dict[str, Any]] = []
    currency_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {field: 0.0 for field in ACCOUNT_FIELDS} | {"book_count": 0})
    summary = {"closed_roundtrips": 0, "wins": 0, "losses": 0}
    benchmark_observed = False
    for row in raw_book_rows:
        if not isinstance(row, dict):
            continue
        raw_account = row.get("account") if isinstance(row.get("account"), dict) else {}
        currency = safe_currency(raw_account.get("currency"))
        alias = aliases.get(row.get("book_id"), f"Paper book {len(books) + 1:02d}")
        account = {field: finite_number(raw_account.get(field)) for field in ACCOUNT_FIELDS}
        totals = currency_totals[currency]
        totals["book_count"] += 1
        for field, value in account.items():
            if value is not None:
                totals[field] += value

        trades = safe_int(row.get("closed_roundtrips"))
        wins = safe_int(row.get("wins"))
        losses = safe_int(row.get("losses"))
        if trades is not None:
            summary["closed_roundtrips"] += trades
        if wins is not None:
            summary["wins"] += wins
        if losses is not None:
            summary["losses"] += losses
        benchmarks = safe_benchmarks(row.get("benchmarks"))
        benchmark_observed = benchmark_observed or bool(benchmarks)
        metrics = metric_record(row.get("metrics"))
        max_dd = metrics["max_drawdown_percent"]["value"]

        books.append({
            "label": alias,
            "currency": currency,
            **account,
            "closed_roundtrips": trades,
            "wins": wins,
            "losses": losses,
            "win_rate_percent": finite_number(row.get("win_rate_percent")),
            "closed_trade_net_pnl": finite_number(row.get("closed_trade_net_pnl")),
            "return_percent": finite_number(row.get("return_percent")),
            "max_drawdown_percent": max_dd,
            "metrics": metrics,
            "benchmarks": benchmarks,
        })

    for totals in currency_totals.values():
        for field in ACCOUNT_FIELDS:
            totals[field] = round(totals[field], 8)
    summary["win_rate_percent"] = (summary["wins"] / (summary["wins"] + summary["losses"]) * 100) if summary["wins"] + summary["losses"] else None

    positions: list[dict[str, Any]] = []
    for position in desk.get("positions", []):
        if not isinstance(position, dict):
            continue
        symbol = position.get("symbol")
        symbol = symbol if isinstance(symbol, str) and re.fullmatch(r"[A-Za-z0-9./:_-]{1,32}", symbol) else "Unknown"
        book_id = position.get("book_id")
        alias = aliases.get(book_id, "Unassigned paper book")
        book = next((item for item in books if item["label"] == alias), None)
        positions.append({
            "book_label": alias,
            "currency": book.get("currency", "UNK") if book else "UNK",
            "symbol": symbol.upper(),
            "quantity": finite_number(position.get("quantity")),
            "mark_price": finite_number(position.get("mark_price")),
            "market_value": finite_number(position.get("market_value")),
            "unrealized_pnl": finite_number(position.get("unrealized_pnl")),
            "quote_fresh": position.get("quote_fresh") if isinstance(position.get("quote_fresh"), bool) else None,
        })
    positions.sort(key=lambda row: (row["book_label"], row["symbol"]))

    main_worker = ((health or {}).get("autonomy") or {}) if isinstance(health, dict) else {}
    wave_worker = ((wave_health or {}).get("autonomy") or {}) if isinstance(wave_health, dict) else {}
    market_data = (health or {}).get("market_data") or {} if isinstance(health, dict) else {}
    reasoning = (health or {}).get("reasoning") or {} if isinstance(health, dict) else {}
    now = datetime.now(timezone.utc).isoformat()
    snapshot = {
        "schema": "AUSAR_PUBLIC_TERMINAL_SNAPSHOT_V1",
        "data_status": "connected",
        "observed_at_utc": now,
        "public_scope": "Paper positions, account-level performance, and health only. No personal identifiers, internal book IDs, broker account names, credentials, orders, strategy rules, or free-form AI output.",
        "desk": {"name": "Ausar", "mode": "paper", "strategy_count": safe_int(raw_performance.get("strategy_count")) if isinstance(raw_performance, dict) else safe_int(desk.get("strategy_count"))},
        "books": books,
        "positions": positions,
        "currency_totals": dict(currency_totals),
        "performance_summary": summary,
        "benchmark_note": "No QQQ/SPY relative return is shown unless the book has aligned, distribution-aware benchmark evidence." if not benchmark_observed else "Benchmark observations are shown per paper book; they are not pooled across currencies.",
        "services": {
            "observed_at_utc": now,
            "main": {
                "observed": isinstance(health, dict),
                "healthy": bool(main_worker.get("healthy")) if isinstance(health, dict) else False,
                "heartbeat_at": main_worker.get("heartbeat_at") if isinstance(main_worker.get("heartbeat_at"), str) else None,
                "market_data_last_success_at": market_data.get("last_success_at") if isinstance(market_data, dict) and isinstance(market_data.get("last_success_at"), str) else None,
                "ai_last_success_at": reasoning.get("last_success_at") if isinstance(reasoning, dict) and isinstance(reasoning.get("last_success_at"), str) else None,
            },
            "wave": {
                "observed": isinstance(wave_health, dict),
                "healthy": bool(wave_worker.get("healthy")) if isinstance(wave_health, dict) else False,
                "heartbeat_at": wave_worker.get("heartbeat_at") if isinstance(wave_worker.get("heartbeat_at"), str) else None,
                "books_evaluated": safe_int((wave_health or {}).get("observed_book_count")) if isinstance(wave_health, dict) else None,
            },
            "scheduled_briefs": {"enabled": True, "interval_seconds": 3600},
        },
        "market_data": {
            "ticker_widget": "TradingView",
            "refresh_mode": "Public embedded widgets. Vendor and exchange timing, delays, and coverage apply.",
            "instruments": MARKET_INSTRUMENTS,
        },
    }
    write_json(args.output.resolve(), snapshot)
    print(json.dumps({
        "data_status": snapshot["data_status"],
        "snapshot_path": str(args.output.resolve()),
        "observed_at_utc": now,
        "paper_books": len(books),
        "open_positions": len(positions),
        "currencies": sorted(currency_totals.keys()),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
