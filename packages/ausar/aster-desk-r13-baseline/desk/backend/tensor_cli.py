"""Explicit installation and operation of the four independent paper sleeves."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from .autonomy import AutonomyRuntime
from .providers import Providers
from .reasoning import Reasoning
from .store import DeskError, Store
from .tensor_daily_models import verify_model_assets
from .tensor_engine import source_manifest_sha256
from .tensor_runtime import TensorRuntimeManager
from .tensor_actions import TensorActions
from .trading import TradingDesk

ROOT = Path(__file__).resolve().parents[1]
SLEEVES = (
    ("tensor_state_repair_1h_r12", "H1STATE", "1h", "Tensor hourly state repair"),
    ("tensor_state_repair_1wk_r12", "WSTATE", "1wk", "Tensor weekly state repair"),
    ("daily20_price_volume_r12", "D20PV", "1d", "Daily20 price and volume"),
    ("daily20_tensor_r12", "D20TENSOR", "1d", "Daily20 Tensor augmented"),
)


def components(db_path):
    store = Store(db_path)
    trading = TradingDesk(store)
    providers = Providers(store)
    runtime = AutonomyRuntime(store, trading, None, Reasoning(), providers)
    strategies = TensorRuntimeManager(store, trading, providers)
    actions = TensorActions(store, trading, providers)
    runtime.strategies = strategies
    runtime.actions = actions
    strategies.actions = actions
    return store, trading, runtime, strategies


def verify_seed(directory):
    manifest_path = ROOT / "strategies/research-input-manifest.json"
    encoded = manifest_path.read_bytes()
    manifest = json.loads(encoded)
    verified = 0
    total_bytes = 0
    for source in manifest["sources"]:
        for group in source["groups"]:
            if group["interval"] not in {"1h", "1d", "1wk"} or group.get("identity_quarantined") or group["symbol"] in {"SPY", "QQQ", "B", "GOLD"}:
                continue
            relative = Path(group["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise DeskError("Invalid pinned seed member")
            path = directory / relative
            if not path.is_file():
                raise DeskError("Restore the complete research seed before installing the sleeves")
            raw = path.read_bytes()
            if len(raw) != group["bytes"] or hashlib.sha256(raw).hexdigest() != group["sha256"]:
                raise DeskError("A research seed member differs from its pinned identity")
            verified += 1
            total_bytes += len(raw)
    return {"members_verified": verified, "bytes_verified": total_bytes,
            "manifest_sha256": hashlib.sha256(encoded).hexdigest()}


def install_all(store, trading, runtime, manager, *, seed_directory, enabled=False):
    """Idempotent named installation; virtual funding never touches a broker."""
    directory = Path(seed_directory).resolve()
    seed_receipt = verify_seed(directory)
    verify_model_assets()
    engine_hash = source_manifest_sha256()
    created = []
    for rid, sleeve, frame, name in SLEEVES:
        with store.connect() as con:
            existing = con.execute("SELECT book_id FROM a_tensor_installations WHERE id=?", (rid,)).fetchone()
            book = con.execute("SELECT id FROM p_books WHERE name=?", (name,)).fetchone()
        if existing:
            book_id = existing["book_id"]
        else:
            book_id = book["id"] if book else trading.create_book({"name": name, "kind": "forward", "broker": "local", "description": "R12 frozen independent strategy; virtual paper capital only"})["id"]
            trading.set_book(book_id, {"policy": {"allow_short": False, "fees_per_order": 0, "slippage_bps": 10}})
        trading.fund_book(book_id, 100000, "r12-opening-capital-" + sleeve)
        universe_path = ROOT / f"strategies/enrollment-{frame}.json"
        config = {"id": rid, "sleeve": sleeve, "book_id": book_id,
                  "universe_file": str(universe_path.relative_to(ROOT)),
                  "universe_sha256": hashlib.sha256(universe_path.read_bytes()).hexdigest(),
                  "enabled": enabled, "max_fetch_per_run": 256,
                  "opening_window_seconds": 300,
                  "missing_data_policy": "exclude_unavailable_with_census_receipts",
                  "forward_revision_policy": "retain_frozen_prefix_audit_minor",
                  "expected_bar_provider": "yahoo",
                  "seed_directory": str(directory),
                  "seed_manifest_file": "strategies/research-input-manifest.json",
                  "seed_manifest_sha256": seed_receipt["manifest_sha256"],
                  "engine_source_manifest_sha256": engine_hash,
                  "research_commit": "4b08cfddcc67d6542e7cb583223874f839cd8f2b"}
        eligibility = ROOT / "strategies/verified-ineligible-assets.json"
        if eligibility.is_file():
            config.update({"verified_ineligible_file": str(eligibility.relative_to(ROOT)),
                           "verified_ineligible_sha256": hashlib.sha256(eligibility.read_bytes()).hexdigest()})
        # Repeated install respects the original immutable enabled flag;
        # later pause/resume changes remain operational state, not a refit.
        if existing:
            with store.connect() as con:
                saved = json.loads(con.execute("SELECT config FROM a_tensor_installations WHERE id=?", (rid,)).fetchone()[0])
            config["enabled"] = saved["enabled"]
        created.append(manager.install(config))
    runtime.ensure_strategy_schedule()
    return {"installed": len(created), "virtual_capital_per_book": 100000,
            "broker_orders": 0, "seed_verification": seed_receipt,
            "sleeves": [{"id": v["id"], "sleeve": v["sleeve"], "book_id": v["book_id"], "enabled": v["enabled"], "readiness": v["readiness"]} for v in created]}


def status(trading, manager, runtime):
    books = {b["id"]: b for b in trading.snapshot()["books"]}
    snapshot = manager.snapshot()
    return {"strategy_count": snapshot["strategy_count"], "runtime_running": runtime.status()["running"],
            "worker_alive": runtime.status()["worker_alive"],
            "sleeves": [{"id": s["id"], "sleeve": s["sleeve"], "enabled": s["enabled"],
                         "book_id": s["book_id"], "account": books[s["book_id"]]["account"],
                         "readiness": s["readiness"], "pending_intents": s["pending_intents"],
                         "owned_positions": s["owned_positions"]} for s in snapshot["installations"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("ASTER_DB_PATH", str(ROOT / "data/aster.sqlite"))))
    sub = parser.add_subparsers(dest="command", required=True)
    installer = sub.add_parser("install", help="Install and virtually fund all four local paper sleeves")
    installer.add_argument("--seed-directory", type=Path, default=ROOT / "data/research-seed-r11/native-inputs")
    installer.add_argument("--enable", action="store_true", help="Enable entry evaluation; data readiness is still required")
    sub.add_parser("status", help="Show actual books, coverage, decisions and runtime status")
    sub.add_parser("run", help="Run one fenced supervisor cycle; serving the desk keeps cycles autonomous")
    args = parser.parse_args()
    store, trading, runtime, manager = components(args.db)
    if args.command == "install":
        result = install_all(store, trading, runtime, manager, seed_directory=args.seed_directory, enabled=args.enable)
    elif args.command == "run":
        if not manager.snapshot()["installations"]:
            parser.error("Install the sleeves first")
        runtime.ensure_strategy_schedule()
        with store.transaction() as con:
            con.execute("UPDATE a_schedules SET next_due=0 WHERE id='tensor-strategies'")
        result = {"completed_work": runtime.run_once(force=True), "state": status(trading, manager, runtime)}
    else:
        result = status(trading, manager, runtime)
    print(json.dumps(result, indent=2, default=str, allow_nan=False))


if __name__ == "__main__":
    main()
