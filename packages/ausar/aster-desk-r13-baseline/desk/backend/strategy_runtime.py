"""Compose independently owned Tensor and public-rule paper runtimes.

No strategy is installed or funded here. The original Tensor implementation and
its source/configuration pins remain untouched. Each manager owns its own state,
while every intent crosses the existing strategy-owned paper execution boundary.
"""
from __future__ import annotations

import importlib
import json

from .providers import utc_clock
from .store import DeskError
from .tensor_runtime import TensorRuntimeManager


class _EmptyTraderRuntime:
    """Schema-neutral read projection while public-rule code is unavailable."""

    actions = None

    def snapshot(self):
        return {"installations": [], "decisions": [], "definitions": [], "strategy_count": 0,
                "enabled": False, "status": "empty"}

    def install(self, config):
        raise DeskError("Public-rule runtime is not available in this build", 409)

    def set_enabled(self, installation_id, enabled):
        raise DeskError("Public-rule installation not found", 404)

    def run_once(self, **kwargs):
        return {"status": "empty", "acquired": 0, "entries": 0, "exits": 0, "errors": []}

    def service_exits(self, **kwargs):
        return {"status": "empty", "exits": 0, "observed_periods": 0, "errors": []}

    def prepare_fills(self, **kwargs):
        return {"status": "empty", "cancelled": 0, "fills_safe": True, "errors": []}


class _GuardedExecutionBroker:
    def __init__(self, broker, fence):
        self._broker, self._fence = broker, fence

    def __getattr__(self, name):
        value = getattr(self._broker, name)
        if name in {"submit", "cancel"}:
            def guarded(*args, **kwargs):
                self._fence()
                return value(*args, **kwargs)
            return guarded
        return value


class _GuardedExecutionProviders:
    """Retain per-fill and pre-transport fences even for a raw provider input."""

    def __init__(self, provider, store, transaction_guard):
        self._provider, self._store = provider, store
        self._guards = []
        for guard in (transaction_guard, getattr(provider, "execution_fence", None)):
            if callable(guard) and not any(guard is old for old in self._guards):
                self._guards.append(guard)
        self.execution_fence = self._fence
        broker = getattr(provider, "broker", None)
        self.broker = _GuardedExecutionBroker(broker, self._fence) if broker is not None else None
        self.brokers = {name: _GuardedExecutionBroker(broker, self._fence)
                        for name, broker in getattr(provider, "brokers", {}).items()}

    def _fence(self, con=None):
        try:
            if con is None:
                with self._store.transaction() as writer:
                    self._fence(writer)
            else:
                for guard in self._guards:
                    guard(con)
        except Exception as exc:
            setattr(exc, "trader_fence_failure", True)
            raise

    def broker_for(self, connection_id="default"):
        if hasattr(self._provider, "broker_for"):
            broker = self._provider.broker_for(connection_id)
            return _GuardedExecutionBroker(broker, self._fence) if broker is not None else None
        return self.broker if connection_id == "default" else None

    def __getattr__(self, name):
        return getattr(self._provider, name)


class StrategyRuntimeManager:
    """One API projection, separate deterministic rule and position ownership."""

    def __init__(self, store, trading, providers, *, tensor=None, trader=None):
        self.store, self.trading, self.providers = store, trading, providers
        self.tensor = tensor if tensor is not None else TensorRuntimeManager(store, trading, providers)
        if trader is None:
            try:
                module = importlib.import_module(".trader_runtime", __package__)
            except ModuleNotFoundError as exc:
                if exc.name != __package__ + ".trader_runtime":
                    raise
                trader = _EmptyTraderRuntime()
            else:
                trader = module.TraderRuntimeManager(store, trading, providers)
        self.trader = trader
        self._actions = None

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, actions):
        self._actions = actions
        self.tensor.actions = actions
        self.trader.actions = actions

    def bind_actions(self, actions):
        self.actions = actions

    def install(self, config):
        if not isinstance(config, dict):
            raise DeskError("Strategy installation must be an object", 422)
        family = config.get("family", "tensor")
        if not isinstance(family, str) or family not in {"tensor", "trader"}:
            raise DeskError("Select the explicit tensor or trader strategy family", 422)
        supplied = dict(config)
        supplied.pop("family", None)
        rid = supplied.get("id", supplied.get("installation_id"))
        if rid is not None and not isinstance(rid, str):
            raise DeskError("Installation identity must be text", 422)
        if supplied.get("book_id") is not None and not isinstance(supplied["book_id"], str):
            raise DeskError("Paper book identity must be text", 422)
        other_table = "a_trader_installations" if family == "tensor" else "a_tensor_installations"
        with self.store.connect() as con:
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (other_table,)).fetchone():
                if rid and con.execute(f"SELECT 1 FROM {other_table} WHERE id=?", (rid,)).fetchone():
                    raise DeskError("Installation identity already belongs to another strategy family", 409)
                if supplied.get("book_id") and con.execute(f"SELECT 1 FROM {other_table} WHERE book_id=?", (supplied["book_id"],)).fetchone():
                    raise DeskError("Paper book already belongs to another strategy family", 409)
        manager = self.tensor if family == "tensor" else self.trader
        result = manager.install(supplied)
        return {**result, "family": family}

    def _owner_family(self, installation_id):
        matches = []
        with self.store.connect() as con:
            for family, table in (("tensor", "a_tensor_installations"), ("trader", "a_trader_installations")):
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                    if con.execute(f"SELECT 1 FROM {table} WHERE id=?", (installation_id,)).fetchone():
                        matches.append(family)
        if len(matches) > 1:
            raise DeskError("Installation identity is ambiguous across strategy families", 409)
        if not matches:
            raise DeskError("Strategy installation not found", 404)
        return matches[0]

    def set_enabled(self, installation_id, enabled):
        if type(enabled) is not bool:
            raise DeskError("enabled must be a boolean", 422)
        family = self._owner_family(installation_id)
        manager = self.tensor if family == "tensor" else self.trader
        return {**manager.set_enabled(installation_id, enabled), "family": family}

    def snapshot(self):
        components = {"tensor": self.tensor.snapshot(), "trader": self.trader.snapshot()}
        merged = {}
        for key in ("installations", "decisions", "definitions"):
            merged[key] = [{**row, "family": family} for family, component in components.items()
                           for row in component.get(key, [])]
        merged["installations"].sort(key=lambda row: row["id"])
        merged["decisions"].sort(key=lambda row: (row.get("created_at", ""), row.get("id", "")), reverse=True)
        merged["decisions"] = merged["decisions"][:200]
        merged["registry"] = merged["installations"]
        merged["strategy_count"] = len(merged["installations"])
        merged["enabled"] = any(row.get("enabled", False) for row in merged["installations"])
        merged["status"] = "installed" if merged["installations"] else "empty"
        merged["scope"] = "Separate deterministic sleeves with independent local paper books"
        merged["execution"] = "Local quote-paper fills; no external broker order submission"
        merged["entry_timing"] = "Completed observed source periods and each sleeve's explicit execution window"
        merged["exit_timing"] = "Each frozen rule's owned exit obligations survive entry pause"
        merged["components"] = components
        return merged

    def _tensor_opening_priority(self, clock):
        """Keep new broad data acquisition outside the existing H1 entry budget."""
        with self.store.connect() as con:
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='a_tensor_installations'").fetchone():
                return False
            installs = [dict(row) for row in con.execute("SELECT * FROM a_tensor_installations ORDER BY id")]
        hourly = []
        for row in installs:
            row["settings"] = json.loads(row["config"])
            if row["settings"].get("frame") == "1h":
                hourly.append(row)
        return bool(hourly and self.tensor._h1_window_priority(hourly, utc_clock(clock)))

    @staticmethod
    def _result(components):
        result = {"components": components, "acquired": 0, "entries": 0, "exits": 0,
                  "observed_periods": 0, "errors": []}
        for family, component in components.items():
            for key in ("acquired", "entries", "exits", "observed_periods"):
                result[key] += component.get(key, 0)
            for error in component.get("errors", []):
                result["errors"].append({"family": family, "error": error})
        states = {component.get("status", "ok") for component in components.values()}
        result["status"] = ("data_blocked" if result["errors"] or "data_blocked" in states
                            else "degraded" if "degraded" in states
                            else "collecting" if "collecting" in states
                            else "busy" if "busy" in states
                            else "empty" if states == {"empty"} else "ok")
        return result

    @staticmethod
    def _call_component(family, manager, operation, **kwargs):
        """A data fault in one book family must not strand the other's exits."""
        try:
            return getattr(manager, operation)(**kwargs)
        except Exception as exc:
            if any(getattr(exc, flag, False) for flag in
                   ("tensor_fence_failure", "trader_fence_failure", "paused")):
                raise
            # Transport errors can contain signed URLs or credentials. Keep
            # the public failure useful without echoing exception text.
            return {"status": "data_blocked", "acquired": 0, "entries": 0, "exits": 0,
                    "observed_periods": 0, "errors": [{"family": family, "operation": operation,
                    "reason": "Component unavailable: " + type(exc).__name__}]}

    def _process_between_families(self, providers, clock, transaction_guard):
        if self.trading is None:
            return {"status": "unavailable", "processed": 0, "fills": 0, "submitted": 0, "errors": []}
        recovery = self.prepare_fills(clock=clock, transaction_guard=transaction_guard)
        provider = providers or self.providers
        if callable(transaction_guard) or callable(getattr(provider, "execution_fence", None)):
            provider = _GuardedExecutionProviders(provider, self.store, transaction_guard)
        try:
            # This is the same public engine the supervisor calls. Its actual
            # clock, expiry, price, cash, action and cap checks remain intact.
            result = self.trading.process(provider, clock)
        except Exception as exc:
            if any(getattr(exc, flag, False) for flag in
                   ("tensor_fence_failure", "trader_fence_failure", "paused")):
                raise
            result = {"status": "data_blocked", "processed": 0, "fills": 0, "submitted": 0,
                      "errors": [{"operation": "process_between_families",
                                  "reason": "Paper execution unavailable: " + type(exc).__name__}]}
        result["trader_fill_recovery"] = recovery
        return result

    def prepare_fills(self, clock=None, transaction_guard=None):
        """No-network safety barrier before any subsequent shared fill pass.

        Managed invalid-book errors may be isolated only when the runtime
        explicitly attests that its unsafe entry remainders are quarantined.
        A failed recovery aborts the supervisor job, including its later outer
        process call, instead of silently allowing another partial fill.
        """
        try:
            result = self.trader.prepare_fills(clock=clock, transaction_guard=transaction_guard)
        except Exception as exc:
            if any(getattr(exc, flag, False) for flag in
                   ("tensor_fence_failure", "trader_fence_failure", "paused")):
                raise
            raise DeskError("Public-rule fill recovery unavailable; financial execution deferred", 503) from None
        if not isinstance(result, dict):
            raise DeskError("Public-rule fill recovery has no valid receipt; financial execution deferred", 503)
        safe = result.get("fills_safe", not result.get("errors") and result.get("status") in {"ok", "empty"})
        if safe is not True:
            failure = DeskError("Public-rule entry recovery is unverified; financial execution deferred", 503)
            failure.receipt = result
            raise failure
        return result

    @staticmethod
    def _with_process(result, process):
        result["process_between_families"] = process
        if process.get("errors"):
            result["errors"].extend({"operation": "process_between_families", "error": error}
                                    for error in process["errors"])
            result["status"] = "data_blocked"
        for error in process.get("trader_fill_recovery", {}).get("errors", []):
            result["errors"].append({"operation": "prepare_fills", "error": error})
            result["status"] = "data_blocked"
        return result

    @staticmethod
    def _with_recovery(result, recovery):
        result["trader_fill_recovery_after_component"] = recovery
        for error in recovery.get("errors", []):
            result["errors"].append({"operation": "prepare_fills", "error": error})
            result["status"] = "data_blocked"
        return result

    def service_exits(self, clock=None, transaction_guard=None, providers=None, *, acquire_native_clocks=True):
        kwargs = {"clock": clock, "transaction_guard": transaction_guard, "providers": providers,
                  "acquire_native_clocks": acquire_native_clocks}
        # Both families service owed risk before the supervisor's fill boundary.
        tensor_result = self._call_component("tensor", self.tensor, "service_exits", **kwargs)
        process = self._process_between_families(providers, clock, transaction_guard)
        trader_result = self._call_component("trader", self.trader, "service_exits", **kwargs)
        recovery = self.prepare_fills(clock=clock, transaction_guard=transaction_guard)
        return self._with_recovery(self._with_process(self._result({"tensor": tensor_result, "trader": trader_result}), process), recovery)

    def run_once(self, clock=None, transaction_guard=None, providers=None):
        kwargs = {"clock": clock, "transaction_guard": transaction_guard, "providers": providers}
        # Post-Tensor clock matters: its full census may itself cross a boundary.
        tensor_result = self._call_component("tensor", self.tensor, "run_once", **kwargs)
        process = self._process_between_families(providers, clock, transaction_guard)
        priority_error = None
        try:
            priority = self._tensor_opening_priority(clock)
        except Exception as exc:
            if any(getattr(exc, flag, False) for flag in
                   ("tensor_fence_failure", "trader_fence_failure", "paused")):
                raise
            priority = True
            priority_error = {"operation": "h1_priority", "reason": "Priority unavailable: " + type(exc).__name__}
        trader_result = self._call_component("trader", self.trader, "run_once", **kwargs, allow_acquisition=not priority)
        recovery = self.prepare_fills(clock=clock, transaction_guard=transaction_guard)
        if priority_error:
            trader_result = {**trader_result, "status": "data_blocked",
                             "errors": [*trader_result.get("errors", []), priority_error]}
        result = self._with_process(self._result({"tensor": tensor_result, "trader": trader_result}), process)
        self._with_recovery(result, recovery)
        result["trader_broad_acquisition_deferred_for_tensor_h1"] = priority
        return result
