"""HTTP boundary and production frontend hosting for Aster Desk."""
import json
import threading
import base64
import math
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response

from .models import Funding, Order, Quote, Runtime, Settings, Task, Watch
from .autonomy import AutonomyRuntime
from .analytics import Analytics, analytics_router
from .lab import Lab, lab_router
from .notifications import NotificationDispatcher, notification_router
from .providers import ProviderError
from .prospective_projection import prospective_snapshot
from .reasoning import Reasoning
from .research import Research, research_router
from .store import DeskError, Store
from .trading import TradingDesk
from .strategy_runtime import StrategyRuntimeManager
from .tensor_actions import TensorActions
from .worker import Worker


ROOT = Path(__file__).resolve().parent.parent


def create_app(db_path=None, start_worker=True):
    store = Store(db_path or os.environ.get("ASTER_DB_PATH") or ROOT / "data" / "aster.sqlite")
    reasoning = Reasoning()
    worker = Worker(store, reasoning)
    trading = TradingDesk(store)
    lab = Lab(store)
    autonomy = AutonomyRuntime(store, trading, lab, reasoning)
    tensor_strategies = StrategyRuntimeManager(store, trading, autonomy.providers)
    corporate_actions = TensorActions(store, trading, autonomy.providers)
    autonomy.strategies = tensor_strategies
    autonomy.actions = corporate_actions
    tensor_strategies.actions = corporate_actions
    research = Research(store, providers=autonomy.providers)
    lab.bind(trading, research)
    analytics = Analytics(store, trading)
    notifications = NotificationDispatcher(store, lab)
    autonomy.bind_notifications(notifications)
    worker.trading, worker.lab, worker.research, worker.providers = trading, lab, research, autonomy.providers

    @asynccontextmanager
    async def lifespan(application):
        try:
            if start_worker:
                worker.start()
                autonomy.start()
            yield
        finally:
            if start_worker:
                try:
                    autonomy.stop()
                finally:
                    worker.stop()

    application = FastAPI(title="Aster Desk", version="1.0.0", lifespan=lifespan)
    application.state.store = store
    application.state.worker = worker
    application.state.reasoning = reasoning
    application.state.trading = trading
    application.state.lab = lab
    application.state.autonomy = autonomy
    application.state.strategies = tensor_strategies
    application.state.corporate_actions = corporate_actions
    application.state.research = research
    application.state.analytics = analytics
    application.state.notifications = notifications
    application.include_router(lab_router(lab))
    application.include_router(research_router(research))
    application.include_router(analytics_router(analytics))
    application.include_router(notification_router(notifications))

    @application.exception_handler(DeskError)
    async def desk_error(request: Request, exc: DeskError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail})

    @application.exception_handler(ProviderError)
    async def provider_error(request: Request, exc: ProviderError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # JSON parsers can accept nonstandard NaN/Infinity tokens. Reject them
        # with a useful 422 rather than failing while encoding the error itself.
        def safe(value):
            if isinstance(value, float) and not math.isfinite(value):
                return str(value)
            if isinstance(value, dict):
                return {key: safe(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [safe(item) for item in value]
            if isinstance(value, Exception):
                return str(value)
            return jsonable_encoder(value)
        return JSONResponse(status_code=422, content={"detail": safe(exc.errors())})

    @application.get("/api/desk")
    def desk():
        return store.snapshot(reasoning.status())

    @application.get("/api/autonomy")
    def autonomous_snapshot():
        return {"trading": trading.snapshot(), "runtime": autonomy.snapshot(), "strategies": tensor_strategies.snapshot(), "prospective": prospective_snapshot(store.path), "lab": lab.snapshot(), "research": research.snapshot(), "reports": analytics.snapshot(), "notifications": notifications.snapshot()}

    @application.get("/api/prospective")
    def prospective_status():
        return prospective_snapshot(store.path)

    @application.post("/api/books")
    def create_book(payload: dict):
        return trading.create_book(payload)

    @application.post("/api/books/{book_id}/funding")
    def fund_book(book_id: str, body: Funding):
        return trading.fund_book(book_id, body.amount, body.client_id)

    @application.patch("/api/books/{book_id}")
    def set_book(book_id: str, payload: dict):
        expected = payload.get("expected_hash")
        if expected is not None and not isinstance(expected, str):
            raise DeskError("expected_hash must be a policy hash", 422)
        changes = {key: value for key, value in payload.items() if key != "expected_hash"}
        if "policy" in changes and set(changes) != {"policy"}:
            raise DeskError("Policy envelope accepts only policy and expected_hash", 422)
        return trading.set_book(book_id, changes, expected_hash=expected)

    @application.patch("/api/portfolio-policy")
    def set_portfolio_policy(payload: dict):
        return trading.set_portfolio_policy(payload)

    @application.post("/api/intents")
    def submit_intent(payload: dict):
        return trading.submit_intent(payload)

    @application.post("/api/intents/{rid}/cancel")
    def cancel_intent(rid: str):
        return trading.cancel_intent(rid)

    @application.post("/api/reconciliation")
    def reconcile():
        return trading.reconcile(autonomy.providers)

    @application.post("/api/autonomy/runtime")
    def autonomous_runtime(payload: dict):
        return autonomy.configure(payload)

    @application.post("/api/autonomy/cycle")
    def autonomous_cycle():
        return autonomy.run_once(force=True)

    @application.post("/api/schedules")
    def schedule(payload: dict):
        return autonomy.schedule(payload)

    @application.post("/api/jobs/{rid}/retry")
    def retry_job(rid: str):
        return autonomy.retry_job(rid)

    @application.get("/api/market/calendar")
    def market_calendar():
        return autonomy.providers.calendar()

    @application.get("/api/market/bars/{sym}")
    def market_bars(sym: str, range: str = "1mo", interval: str = "1d"):
        return autonomy.providers.bars(sym, range=range, interval=interval)

    @application.get("/api/market/revisions/{revision_id}/manifest")
    def market_revision_manifest(revision_id: str):
        return autonomy.providers.bar_manifest(revision_id)

    @application.get("/api/market/revisions/{revision_id}/bars")
    def market_revision_page(revision_id: str, cursor: str | None = None, limit: int = 500):
        return autonomy.providers.bar_page(revision_id, cursor=cursor, limit=limit)

    @application.post("/api/market/revisions/{revision_id}/continue")
    def market_revision_continue(revision_id: str):
        return autonomy.providers.continue_bars(revision_id)

    @application.post("/api/account/funding")
    def funding(body: Funding):
        return store.fund(body.amount, body.client_id)

    @application.post("/api/watchlist")
    def watch(body: Watch):
        return store.add_watch(body.symbol)

    @application.delete("/api/watchlist/{sym}")
    def unwatch(sym: str):
        return store.remove_watch(sym)

    @application.post("/api/quotes")
    def quote(body: Quote):
        return store.ingest_quote(body.symbol, body.price, body.as_of, body.source)

    @application.post("/api/orders")
    def order(body: Order):
        return store.create_order(body.symbol, body.side, body.quantity, body.client_id, body.type)

    @application.post("/api/orders/{rid}/approve")
    def approve(rid: str):
        return store.approve_order(rid)

    @application.post("/api/orders/{rid}/cancel")
    def cancel_order(rid: str):
        return store.cancel_order(rid)

    @application.post("/api/tasks")
    def task(body: Task):
        return store.enqueue(body.kind, body.title, body.instructions, body.symbol)

    @application.post("/api/tasks/{rid}/cancel")
    def cancel_task(rid: str):
        return store.cancel_task(rid)

    @application.post("/api/runtime/cycle")
    def cycle():
        return store.enqueue("operational_cycle")

    @application.post("/api/runtime")
    def runtime(body: Runtime):
        return store.runtime(body.running)

    @application.patch("/api/settings")
    def settings(body: Settings):
        return store.update_settings(body.model_dump(exclude_none=True))

    @application.get("/api/strategies")
    def strategies():
        return tensor_strategies.snapshot()["installations"]

    @application.get("/api/strategies/catalogue")
    def strategy_catalogue():
        return tensor_strategies.snapshot()

    @application.post("/api/strategies/install")
    def strategy_install(payload: dict):
        installed = tensor_strategies.install(payload)
        autonomy.ensure_strategy_schedule()
        return installed

    @application.patch("/api/strategies/{installation_id}")
    def strategy_enable(installation_id: str, payload: dict):
        if set(payload) != {"enabled"}:
            raise DeskError("Supply only the enabled boolean", 422)
        return tensor_strategies.set_enabled(installation_id, payload["enabled"])

    @application.post("/api/strategies/run", status_code=202)
    def strategy_run():
        if not tensor_strategies.snapshot()["installations"]:
            raise DeskError("Install a strategy sleeve before requesting a cycle", 409)
        autonomy.ensure_strategy_schedule()
        with store.transaction() as con:
            con.execute("UPDATE a_schedules SET next_due=0 WHERE id='tensor-strategies'")
            store.event(con, "tensor_cycle_requested", "operator", "Queued a fenced strategy cycle", {"schedule_id": "tensor-strategies"})
        return {"queued": True, "schedule_id": "tensor-strategies", "runtime_running": autonomy.status()["running"]}

    @application.get("/api/health")
    def health(deep: bool = False):
        health = worker.health()
        provider_status = autonomy.providers.status()
        integrity = store.verify_ledger() if deep else store.ledger_status()
        return {**health, "manual_ledger": {"market_data": health["market_data"], "broker": health["broker"]}, "market_data": provider_status["market_data"], "broker": provider_status["broker"], "autonomy": autonomy.status(), "journal_integrity": integrity}

    @application.get("/api/market/history/{sym}")
    def market_history(sym: str, as_of: str | None = None, limit: int = 100):
        return autonomy.providers.observations(sym, as_of=as_of, limit=limit)

    @application.get("/api/export")
    def export():
        exported = store.export(reasoning.status())
        manual_names = tuple(name for name in exported["tables"] if not name.startswith(("a_", "p_")))
        lab_names = ("lab_messages", "lab_cursors", "lab_alerts", "lab_studies", "lab_study_results", "lab_artifacts", "lab_incidents", "lab_proposals", "lab_decisions")
        research_names = ("research_receipts", "research_collection", "research_workflows", "research_runs", "research_nodes", "research_node_receipts")
        with store.connect() as con:
            con.execute("BEGIN")
            names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND (name GLOB 'p_*' OR name GLOB 'a_*' OR (name GLOB 'n_*' AND name NOT IN ('n_subscriptions','n_media')))")]
            def rows(table_names):
                def encode(row):
                    return {key: {"encoding": "base64", "data": base64.b64encode(value).decode("ascii"), "bytes": len(value)}
                            if isinstance(value, bytes) else value for key, value in dict(row).items()}
                return {name: [encode(row) for row in con.execute('SELECT * FROM "' + name + '"')] for name in table_names}
            exported["tables"] = rows(manual_names)
            exported["autonomous_tables"] = rows(names)
            exported["lab"] = rows(lab_names)
            exported["research"] = rows(research_names)
        trading_view = trading.snapshot()
        exported.update({"trading": trading_view, "runtime": autonomy.snapshot(), "strategies": tensor_strategies.snapshot(), "reports": analytics.snapshot(), "notifications": notifications.snapshot(),
                         "binary_encoding": "SQLite BLOB values use {encoding:base64,data:<RFC4648 string>,bytes:<decoded size>}; decode before SQLite restoration",
                         "accounting_coverage": {"broker": trading_view["broker_accounting_coverage"],
                                                "raw_realized_cents": {"tables": ["p_books", "p_positions", "p_fills"], "local_books": "Exact local signed average-cost ledger values", "broker_books": "Internal reconstruction estimates from cumulative order receipts; not verified realized P/L or an ordered execution tape", "public_coverage": "Use trading.books[].account.realized_pnl_coverage, trading.positions[].realized_pnl_coverage and trading.fills[].realized_pnl_coverage"},
                                                "raw_position_basis": "Broker p_positions.cost_cents can be a reconstruction estimate. Use trading.positions[].cost_basis_coverage and nullable average_cost/cost_basis/unrealized_pnl to determine verified source basis.",
                                                "raw_broker_fee_cents": "Cumulative broker order responses do not establish complete execution fees; zero stored fees are not proof of zero broker costs"},
                         "consistency": {"raw_tables": "One SQLite read transaction across tables, autonomous_tables, lab and research", "derived_views": "Component views observed after the raw evidence snapshot"}})
        content = json.dumps(exported, indent=2)
        return Response(content=content, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="aster-desk-export.json"'})

    @application.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path == "api" or path.startswith("api/"):
            raise DeskError("API route not found", 404)
        dist = ROOT / "frontend" / "dist"
        target = (dist / path).resolve()
        if target.is_relative_to(dist.resolve()) and target.is_file():
            return FileResponse(target)
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html")
        return JSONResponse(status_code=503, content={"detail": "Frontend has not been built. Run the project launcher or use the Vite development server."})

    return application


class _LazyDefaultApp:
    """ASGI default constructed on use, never by importing a test factory.

    Uvicorn retains its existing backend.app:app entry. An explicit factory
    import cannot initialize a different operating database as a side effect.
    """
    def __init__(self):
        self._application = None
        self._lock = threading.Lock()

    def _get(self):
        with self._lock:
            if self._application is None:
                self._application = create_app()
            return self._application

    async def __call__(self, scope, receive, send):
        await self._get()(scope, receive, send)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self._get(), name)


app = _LazyDefaultApp()
