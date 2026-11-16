"""Live runner (DEPLOY-1): loads config/sleeves.json, builds the Desk,
runs cycles forever. Modes: evaluate-only (FakeBroker, zero orders —
the launch posture) and --dispatch (PaperDoor, v3- client-order ids).

Credentials route = v2's: key ID from ALPACA_KEY_ID env else the
local-alpaca-paper skill config file; secret as the Secure Vault
hsurr:* surrogate via dynamic_credentials (custom.alpaca). Values are
held only in the door process env dict, never logged or journaled.

Producers (CURE3-1): `positions` is read back from the paper account
in dispatch mode as the canonical LIST of records via
get_positions_snapshot() ([] in evaluate-only — POS-SHAPE-20261026);
`bars` comes from the warm
producer (desk3/warm.py — real Alpaca SIP bars, cached in
state/warm_bars.json; on fetch failure the key is absent and dependent
sleeves are UNFED by name, never FED on an empty map). Batch-2 G4
producers (desk3/producers.py) add quotes (Alpaca SIP latest),
funding (Coinalyze current funding rate — R1 ruling 2026-10-25;
Binance premiumIndex is HTTP 451 geo-blocked from this box),
options/options_chain/
options_quotes (Alpaca contracts + OPRA snapshots) and the Tensor
bundle-file channel (tensor/tensor_fires/tensor_daily20), each
fail-closed. Sleeves declaring still-unproduced inputs are UNFED,
named in the terminal feed, never silently skipped.
State/heartbeat: state/runner.json rewritten every cycle."""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from desk3.broker import FakeBroker, PaperDoor  # noqa: E402
from desk3.cycle import Desk  # noqa: E402

_KEY_FILE = os.path.expanduser(
    "~/workspace/custom-skills/local-alpaca-paper/config/key_id")
for _d in ("/opt/muse/skills/custom-connector-setup/bin",
           "/opt/muse/skills/custom-connector-setup/templates/skill/bin"):
    if _d not in sys.path:
        sys.path.insert(0, _d)


def credential_env():
    kid = os.environ.get("ALPACA_KEY_ID", "").strip()
    if not kid and os.path.exists(_KEY_FILE):
        kid = open(_KEY_FILE).read().strip()
    from dynamic_credentials import dynamic_credential_entry
    entry = dynamic_credential_entry("custom.alpaca", "access_token")
    secret = str(entry.get("surrogate", "")).strip()
    if not kid or not secret.startswith("hsurr:"):
        raise RuntimeError("paper credentials route unavailable")
    return {"ALPACA_KEY_ID": kid, "ALPACA_SECRET_KEY": secret}


class ConfigWatcher:
    """G5 cure (HARDEN batch-1): the runner used to load sleeves.json
    ONCE at startup, so a roster landing (156 -> 311) left the live
    runner, health.json and the terminal roll serving the stale roster
    until a manual restart. The watcher hashes the config each cycle;
    on change the main loop rebuilds the Desk from the new config."""

    def __init__(self, root):
        self.path = os.path.join(root, "config", "sleeves.json")
        self._seen = self._digest()

    def _digest(self):
        import hashlib
        try:
            with open(self.path, "rb") as fh:
                return hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            return None

    def changed(self):
        return self._digest() != self._seen

    def mark_seen(self):
        self._seen = self._digest()


def build_desk(root, dispatch=False, env=None):
    cfg = json.load(open(os.path.join(root, "config", "sleeves.json")))
    rows = cfg["sleeves"]
    if dispatch:
        broker = PaperDoor(env=env if env is not None else credential_env())
    else:
        broker = FakeBroker()
    desk = Desk(root, broker=broker, sleeve_path=root, timeout_s=30.0,
                # DSK-7: live stage timings land in the state sink,
                # one record per cycle, in the Scheduler's shape.
                stage_sink=os.path.join(root, "state",
                                        "stage_timings.jsonl"))
    # A15 reconcile only in dispatch mode (CURE3-4): the baseline is a
    # PaperDoor artifact (the legacy paper book); an evaluate-only
    # FakeBroker starts empty, so reconciling it against that baseline
    # fabricates discrepancies and halts sleeves on phantom state.
    desk.reconcile_enabled = bool(dispatch)
    if dispatch:
        # POS-SHAPE-20261026: the snapshot positions contract is a
        # LIST of canonical records; broker.get_positions() is the
        # reconcile dict shape and must never be served here.
        desk.add_producer(
            "account",
            lambda c: {"positions": broker.get_positions_snapshot()},
            ["positions"], 3600)
    else:
        desk.add_producer("account", lambda c: {"positions": []},
                          ["positions"], 3600)
    from desk3.warm import WarmBars
    if env is not None:
        desk.add_producer("bars", WarmBars(root, env), ["bars"], 3600)
    else:
        desk.add_producer("bars", WarmBars(root, env_resolver=credential_env),
                          ["bars"], 3600)
    # G4 batch-2 producers (desk3/producers.py): quotes, funding,
    # options/options_chain/options_quotes, tensor, tensor_fires,
    # tensor_daily20. Each fails closed ({}), so a down source leaves
    # only its dependents UNFED by name.
    from desk3.producers import register_all
    if env is not None:
        register_all(desk, root, env=env)
    else:
        register_all(desk, root, env_resolver=credential_env)
    # G4 batch-4 producers (desk3/producers_g4.py): bars timeframe
    # projections, vix, bars_secondary, calendar, xsp_state,
    # saty_setups, and the file-served qulla / buyback_scan channels.
    # Same fail-closed contract.
    from desk3.producers_g4 import register_all_g4
    if env is not None:
        register_all_g4(desk, root, env=env)
    else:
        register_all_g4(desk, root, env_resolver=credential_env)
    # G4 batch-3 producers (desk3/producers3.py): kraken (+ perp bars),
    # earnings, earnings_events, session_fills, fire/rule/timing
    # ingest. Public/internal sources need no credentials — EXCEPT
    # przm_tape and milkman_chain (PRODUCER-401-20261116), which are
    # authenticated Alpaca producers and receive the canonical
    # credential route here, exactly as register_all above; without
    # it they read an empty process environment and 401 all session.
    # Each fails closed ({}), leaving only its dependents UNFED.
    from desk3.producers3 import register_batch3
    if env is not None:
        register_batch3(desk, root, env=env)
    else:
        register_batch3(desk, root, env_resolver=credential_env)
    # CONV123-REVIVAL-20261116: the three Graveyard revival
    # accrual ledger producers (revival_tom / revival_pairs /
    # revival_pead), reading the research lane's w7 shadow
    # ledgers in place — one source of truth, fail-closed.
    from desk3.revival_producers import register_revival
    register_revival(desk, root)
    # COINALYZE-1: funding-rate HISTORY producer (funding_history key;
    # the same loader backfills kraken.funding inside the kraken
    # producer — one merged series per symbol, no parallel key).
    # Fail-closed: missing/invalid key or stale data => {} (UNFED).
    from desk3.producers3 import CoinalyzeFundingProducer
    desk.add_producer("coinalyze_funding", CoinalyzeFundingProducer(root),
                      ["funding_history"], 3600)
    for row in rows:
        module = row["module"]
        # AUDIT-CURE 2026-10-25 (B4): rows carrying adapter_dir declare
        # a bare module name resolved INSIDE that directory. Passing
        # the bare name to the worker imported the strategy module in
        # sleeves/ (no evaluate attribute) instead of the adapter in
        # desk_sleeves/ — red_day_reversal and rsi_meanrev were FED
        # but errored every cycle, and 8 more rows carried the same
        # latent defect behind UNFED states. Qualify at the source.
        adapter_dir = row.get("adapter_dir")
        if adapter_dir and "." not in module:
            module = f"{adapter_dir}.{module}"
        _params = row.get("params") or {}
        desk.add_sleeve(row["id"], module, row.get("inputs", []),
                        row.get("cadence_s", 300),
                        float(row["slice"]["capital_usd"]),
                        parked=bool(row.get("parked", False)),
                        session=row.get("session"),
                        symbol=_params.get("symbol"),
                        declared_family=_params.get("family"),
                        parked_reason=_params.get("parked_reason"),
                        # TENSOR-DAILY20-SERVE-20261031: the two D20
                        # sleeves resolve the daily20 store reference
                        # from disk (full-basket scoring, ~106
                        # CPU-seconds for the pair); the 30s default
                        # worker budget cannot hold that evaluation.
                        # Budget only — no strategy parameter changes.
                        # SATY-V02-TIMEOUT-20261116: saty_gpt_v02's
                        # live evaluation cost is ~33s (EFF-1 pool
                        # record, the desk's slowest) against the
                        # same 30s default, so it wedged at 11:27Z
                        # and 11:44Z on 2026-11-16. Cause: desk3/
                        # warm.py CR-6 widened the shared SPY 5Min
                        # window 60 -> 300 days for v03, growing
                        # v02's input ~5x (39,946 bars on the
                        # 2026-11-16 13:46Z snapshot); the
                        # aggregation cache is process-local and
                        # defeated by snapshot hash churn. 120.0s
                        # is ~3.6x the 33s live cost (timed fixture
                        # on that snapshot in isolation: 6.46s/
                        # 6.56s cold, 4.26s/4.50s warm — the live
                        # pool's CPU contention is what pushes it
                        # to ~33s, and the budget must hold the
                        # live cost). saty_gpt_v03 measured 0.79s/
                        # 0.81s on the same snapshot with zero
                        # wedged journal rows, so it gets no
                        # override. Budget only — no strategy
                        # parameter changes.
                        timeout_s=(600.0 if row["id"] in
                                   ("aster_tensor_d20_pv",
                                    "aster_tensor_d20_tensor") else
                                   120.0 if row["id"] in
                                   ("saty_gpt_v02",) else None),
                        # CLEAR-THE-BOARD-20261114 (CR-S3): rows
                        # flagged own_book_view are served their own
                        # journal-derived positions at evaluation
                        # (desk3.cycle.own_book_positions).
                        own_book_view=bool(row.get("own_book_view",
                                                   False)))
    return desk, rows


_RUNNER_LOCK_FH = None


def acquire_runner_lock(state):
    """Single-instance lock (AUDIT-CURE 2026-10-25, A-01): exactly one
    desk3.run_live may exist. A second process starting for ANY reason
    (watchdog misjudgement, hand launch, unit restart) exits instead
    of racing the first on state/snapshot/dispatcher files. Returns
    the held lock file handle, or None when another runner holds it."""
    import fcntl
    fh = open(os.path.join(state, "runner.lock"), "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    fh.seek(0); fh.truncate(); fh.write(str(os.getpid())); fh.flush()
    return fh


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dispatch = "--dispatch" in argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state = os.path.join(root, "state")
    os.makedirs(state, exist_ok=True)
    global _RUNNER_LOCK_FH
    _RUNNER_LOCK_FH = acquire_runner_lock(state)
    if _RUNNER_LOCK_FH is None:
        print("runner already running: single-instance lock held; "
              "exiting (A-01 duplicate guard)")
        return 3
    desk, rows = build_desk(root, dispatch=dispatch)
    watcher = ConfigWatcher(root)
    state = os.path.join(root, "state")
    os.makedirs(state, exist_ok=True)
    n = 0
    while True:
        n += 1
        if watcher.changed():  # G5: roster/config landed -> rebuild
            try:
                desk.close()
            except Exception:
                pass
            desk, rows = build_desk(root, dispatch=dispatch)
            watcher.mark_seen()
        try:
            roll = desk.run_cycle()
            status = roll["status"]
            dispatched = roll["dispatched"]
        except Exception as e:  # cycle failure: record, keep the loop alive
            status, dispatched = f"error:{type(e).__name__}:{e}", 0
        hb = {"pid": os.getpid(), "cycle": n, "mode":
              "dispatch" if dispatch else "evaluate-only",
              "roster": len(rows), "last_status": status,
              "last_dispatched": dispatched,
              "ts": datetime.now(timezone.utc).isoformat()}
        tmp = os.path.join(state, "runner.json.tmp")
        with open(tmp, "w") as fh:
            json.dump(hb, fh, sort_keys=True)
        os.replace(tmp, os.path.join(state, "runner.json"))
        time.sleep(60)


if __name__ == "__main__":
    main()
