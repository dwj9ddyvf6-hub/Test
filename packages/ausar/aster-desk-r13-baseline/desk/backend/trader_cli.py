"""Explicitly install and operate three public-rule local paper sleeves."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path

from .providers import Providers
from .autonomy import AutonomyRuntime
from .reasoning import Reasoning
from .store import DeskError, Store, cents
from .tensor_actions import TensorActions
from .trader_runtime import TraderRuntimeManager
from .trading import TradingDesk, decimal

ROOT = Path(__file__).resolve().parents[1]


def components(db_path):
    store = Store(db_path)
    trading = TradingDesk(store)
    providers = Providers(store)
    manager = TraderRuntimeManager(store, trading, providers)
    manager.actions = TensorActions(store, trading, providers)
    return store, trading, providers, manager


def install_all(store, trading, manager, *, enabled=False, virtual_capital=100000):
    """Explicit operation only; no construction or app import calls this helper."""
    manager.verify_rule_assets()
    if type(enabled) is not bool:
        raise DeskError("enabled must be a boolean", 422)
    if virtual_capital is not None:
        amount = decimal(virtual_capital, "virtual_capital")
        if amount != Decimal(cents(amount)) / 100:
            raise DeskError("Virtual capital requires positive whole cents", 422)
    installed = []
    for rule_id, definition in manager.definitions().items():
        with store.connect() as con:
            saved = con.execute("SELECT * FROM a_trader_installations WHERE id=?", (rule_id,)).fetchone()
            named = con.execute("SELECT id FROM p_books WHERE name=?", (definition["name"],)).fetchone()
        if saved:
            config = json.loads(saved["config"])
        else:
            book_id = named[0] if named else trading.create_book({"name": definition["name"], "kind": "forward", "broker": "local",
                                     "description": "Frozen public-rule adaptation; separate virtual paper capital; no broker orders"})["id"]
            trading.set_book(book_id, {"policy": {"allow_short": False, "fees_per_order": 0, "slippage_bps": 10}})
            config = {"id": rule_id, "rule_id": rule_id, "book_id": book_id, "enabled": enabled}
        # Source and immutable rule checks precede idempotent virtual funding.
        row = manager.install(config)
        if virtual_capital is not None:
            trading.fund_book(row["book_id"], virtual_capital, "trader-public-v1-opening-capital")
        installed.append(row)
    # The application worker consumes the generic strategies schedule. Explicit
    # installation creates it; constructors still install/fund no strategies.
    autonomy = AutonomyRuntime(store, trading, None, Reasoning(), manager.providers)
    autonomy.strategies = manager
    autonomy.ensure_strategy_schedule()
    return {"installed": len(installed), "virtual_capital_per_book": virtual_capital, "broker_orders": 0,
            "sleeves": [{key: row[key] for key in ("id", "sleeve", "book_id", "enabled", "config_sha256")} for row in installed]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("ASTER_DB_PATH", str(ROOT / "data/aster.sqlite"))))
    commands = parser.add_subparsers(dest="command", required=True)
    installer = commands.add_parser("install", help="Explicitly create three independent public-rule local paper books")
    installer.add_argument("--enable", action="store_true")
    installer.add_argument("--virtual-capital", type=float, default=100000)
    installer.add_argument("--no-funding", action="store_true")
    commands.add_parser("status")
    commands.add_parser("run", help="Evaluate one cycle; running the desk's worker provides continuing execution")
    args = parser.parse_args()
    store, trading, providers, manager = components(args.db)
    if args.command == "install":
        result = install_all(store, trading, manager, enabled=args.enable,
                             virtual_capital=None if args.no_funding else args.virtual_capital)
    elif args.command == "run":
        cycle = manager.run_once()
        prepared = manager.prepare_fills()
        if not prepared["fills_safe"]:
            raise DeskError("Public rule ownership is uncertain; local fill processing is withheld")
        result = {"cycle": cycle, "fill_preflight": prepared, "fills": trading.process(providers), "state": manager.snapshot()}
    else:
        result = manager.snapshot()
    print(json.dumps(result, indent=2, default=str, allow_nan=False))


if __name__ == "__main__":
    main()
