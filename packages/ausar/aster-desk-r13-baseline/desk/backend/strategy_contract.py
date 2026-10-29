"""Read-only installed-strategy metadata and the timestamped evaluation contract."""
import hashlib
import json
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CandidateManifest:
    identity: str
    version: str
    source_hash: str
    research_registration_id: str
    dataset_manifest_hash: str
    training_end: str
    holdout_end: str
    execution_cost_model: str
    benchmark: tuple[str, ...] = ("QQQ", "SPY")


class FutureStrategy(Protocol):
    """Contract for explicitly installed deterministic implementations.

    Future candidates must consume timestamped data from a frozen as-of view,
    declare their hold/exit rules, and supply versioned order intentions to the
    existing execution engine. Research is isolated from funded books; success
    requires out-of-sample, cost-adjusted and forward-paper evidence. Available
    code is distinct from installation; new databases have no installed rules.
    """
    manifest: CandidateManifest

    def evaluate(self, as_of_snapshot: dict) -> tuple[dict, ...]: ...


def installed_strategies(store=None, con=None):
    """Project actual durable installations without gaining execution authority.

    Older/manual-only databases legitimately have no installation table. Read
    inside the caller's snapshot when provided, and never construct a runtime or
    install a rule just to answer a metadata request. Arbitrary config fields,
    source text and environment credentials are excluded from this projection.
    A malformed config remains visible as an installed but invalid record.
    """
    if con is None:
        if store is None:
            return ()
        reader = store.connect()
        try:
            reader.execute("BEGIN")
            return installed_strategies(con=reader)
        finally:
            reader.close()
    registry = []
    source_rows = []
    for family, table in (("tensor", "a_tensor_installations"), ("trader", "a_trader_installations")):
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
            continue
        cursor = con.execute(f"SELECT id,sleeve,book_id,enabled,config,config_sha256,created_at,updated_at FROM {table} ORDER BY id")
        columns = [value[0] for value in cursor.description]
        source_rows.extend((family, dict(zip(columns, row))) for row in cursor)
    for family, record in source_rows:
        record["family"] = family
        raw_config = record.pop("config")
        record["enabled"] = bool(record["enabled"])
        record["execution_scope"] = "dedicated local paper book"
        try:
            config = json.loads(raw_config)
            if not isinstance(config, dict):
                raise ValueError()
            serialized = json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)
            record["config_status"] = "verified" if hashlib.sha256(serialized.encode()).hexdigest() == record["config_sha256"] else "identity_mismatch"
            for field in ("frame", "rule_id", "rules_sha256", "hold_native_bars", "maximum_slots", "entry_cap_equity", "entry_cap_native_dv"):
                if field in config:
                    record[field] = config[field]
            symbols = config.get("symbols")
            record["enrollment_count"] = len(symbols) if isinstance(symbols, list) else None
        except (ValueError, TypeError):
            record["config_status"] = "invalid"
        registry.append(record)
    return tuple(sorted(registry, key=lambda row: (row["id"], row["family"])))
