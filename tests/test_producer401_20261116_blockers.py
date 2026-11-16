"""PRODUCER-401-20261116 regression blockers.

Root cause: MilkmanChainProducer and PrzmTapeProducer read their
Alpaca credentials from os.environ, but the live runner process
carries NO ALPACA_KEY_ID / ALPACA_SECRET_KEY in its environment
(verified from /proc/<runner>/environ, names only). _auth() thus
built empty APCA headers and every authenticated call answered
HTTP 401 (paper-api: {"message": "unauthorized."}; data-api:
nginx 401) — both sleeves UNFED all session 2026-11-16.

Every working Alpaca producer on the desk (bars/WarmBars, quotes,
options, g4 xsp) instead receives the canonical route from
run_live.build_desk: env= or env_resolver=credential_env
(desk3/run_live.py: key id from ALPACA_KEY_ID env else the
local-alpaca-paper skill key_id file; secret as the Secure Vault
hsurr:* surrogate via dynamic_credentials). That same key id
(PKOXJJD4LMQFMLCSPY5WTJNX5E) returns HTTP 200 on BOTH failing
endpoints (probed 2026-11-16: SPX contracts 506 rows, SPY latest
trade 200) — not an entitlement wall, not a stale key.

These tests prove, without network: (1) both producers accept and
USE the injected env / env_resolver (never os.environ), (2)
register_batch3 forwards env/env_resolver to exactly those two
producers, (3) run_live wires register_batch3 with credential_env
exactly as it wires register_all / register_all_g4.
"""
import os
import sys
import unittest
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 11, 16, 14, 30, tzinfo=ET)  # Monday, in-window
SENTINEL = {"ALPACA_KEY_ID": "sentinel-kid",
            "ALPACA_SECRET_KEY": "sentinel-secret"}


def _synthetic_chain():
    import math
    from desk3.producers import _bs_call_price
    spot, expiry_close = 6000.0, NOW.replace(hour=16, minute=0)
    T = max((expiry_close - NOW).total_seconds(), 60.0) / (365.25 * 86400)
    contracts, snaps = [], {}
    for K in (5950.0, 6000.0, 6050.0):
        for right in ("call", "put"):
            c = _bs_call_price(spot, K, T, 0.04, 0.16)
            px = c if right == "call" else c - spot + K * math.exp(-0.04 * T)
            px = max(px, 0.05)
            sym = f"SPXW261116{'C' if right == 'call' else 'P'}{int(K * 1000):08d}"
            contracts.append({"symbol": sym, "type": right,
                              "strike_price": float(K),
                              "expiration_date": "2026-11-16"})
            snaps[sym] = {"latestQuote": {
                "bp": round(px - 0.05, 2), "ap": round(px + 0.05, 2),
                "t": "2026-11-16T19:30:00Z"}}
    return contracts, snaps


class TestMilkmanCredentialRoute(unittest.TestCase):
    def test_resolver_env_reaches_contracts_fetch_not_os_environ(self):
        from desk3 import producers3
        contracts, snaps = _synthetic_chain()
        seen = {}

        def fake_contracts(underlying, env, ref, max_dte=0):
            seen.setdefault("envs", []).append(env)
            return contracts if underlying == "SPX" else []

        def fake_snaps(occs, env):
            seen.setdefault("snap_envs", []).append(env)
            return snaps

        prod = producers3.MilkmanChainProducer(
            ROOT, env_resolver=lambda: SENTINEL)
        with mock.patch.dict(os.environ,
                             {"ALPACA_KEY_ID": "wrong-os-env",
                              "ALPACA_SECRET_KEY": "wrong-os-secret"}), \
                mock.patch("desk3.producers.fetch_option_contracts",
                           fake_contracts), \
                mock.patch("desk3.producers.fetch_option_snapshots",
                           fake_snaps):
            out = prod._run(NOW)
        self.assertIn("milkman_0dte_chain", out)
        self.assertTrue(seen["envs"], "contracts fetch never called")
        for env in seen["envs"] + seen["snap_envs"]:
            self.assertEqual(env, SENTINEL)

    def test_direct_env_kwarg_reaches_fetch(self):
        from desk3 import producers3
        contracts, snaps = _synthetic_chain()
        seen = {}

        def fake_contracts(underlying, env, ref, max_dte=0):
            seen["env"] = env
            return contracts if underlying == "SPX" else []

        prod = producers3.MilkmanChainProducer(ROOT, env=SENTINEL)
        with mock.patch("desk3.producers.fetch_option_contracts",
                        fake_contracts), \
                mock.patch("desk3.producers.fetch_option_snapshots",
                           lambda occs, env: snaps):
            out = prod._run(NOW)
        self.assertIn("milkman_0dte_chain", out)
        self.assertEqual(seen["env"], SENTINEL)


class TestPrzmCredentialRoute(unittest.TestCase):
    def test_resolver_env_reaches_spot_and_contracts_not_os_environ(self):
        from desk3 import producers3
        seen = {"headers": [], "envs": []}

        def fake_get_json(url, headers=None, timeout=30):
            seen["headers"].append(headers)
            if "trades/latest" in url:
                return {"trade": {"p": 100.0}}
            return {}  # v1beta1 options trades: none

        def fake_contracts(underlying, env, ref, max_dte=1):
            seen["envs"].append(env)
            return [{"symbol": "SPY261116C00100000",
                     "strike_price": "100"}]

        prod = producers3.PrzmTapeProducer(
            ROOT, env_resolver=lambda: SENTINEL)
        with mock.patch.dict(os.environ,
                             {"ALPACA_KEY_ID": "wrong-os-env",
                              "ALPACA_SECRET_KEY": "wrong-os-secret"}), \
                mock.patch("desk3.producers._get_json", fake_get_json), \
                mock.patch("desk3.producers.fetch_option_contracts",
                           fake_contracts), \
                mock.patch("desk3.producers.fetch_option_snapshots",
                           lambda occs, env: {}):
            out = prod._run(NOW)
        self.assertIn("przm_prints", out)
        self.assertIsNone(prod.last_error)
        self.assertTrue(seen["headers"], "spot fetch never called")
        for h in seen["headers"]:
            self.assertEqual(h.get("APCA-API-KEY-ID"), "sentinel-kid")
            self.assertEqual(h.get("APCA-API-SECRET-KEY"),
                             "sentinel-secret")
        for env in seen["envs"]:
            self.assertEqual(env, SENTINEL)


class TestWiring(unittest.TestCase):
    def test_register_batch3_forwards_resolver_to_both_producers(self):
        from desk3 import producers3

        class FakeDesk:
            def __init__(self):
                self.prods = {}

            def add_producer(self, name, fn, outputs, sla):
                self.prods[name] = fn

        desk = FakeDesk()
        producers3.register_batch3(desk, ROOT,
                                   env_resolver=lambda: SENTINEL)
        for name in ("milkman_chain", "przm_tape"):
            prod = desk.prods[name]
            self.assertIsNotNone(getattr(prod, "env_resolver", None),
                                 name)
            self.assertEqual(prod.env_resolver(), SENTINEL, name)

    def test_run_live_wires_batch3_with_credential_env(self):
        src = open(os.path.join(ROOT, "desk3", "run_live.py")).read()
        self.assertIn("register_batch3(desk, root, env=env)", src)
        self.assertIn(
            "register_batch3(desk, root, env_resolver=credential_env)",
            src)

    def test_no_os_environ_credential_read_in_either_producer(self):
        src = open(os.path.join(ROOT, "desk3", "producers3.py")).read()
        milk = src[src.index("class MilkmanChainProducer"):
                   src.index("class PrzmTapeProducer")]
        przm = src[src.index("class PrzmTapeProducer"):
                   src.index("# ------------------------------------------------------------------ wiring")]
        for chunk, name in ((milk, "milkman"), (przm, "przm")):
            self.assertNotIn("os.environ", chunk, name)


if __name__ == "__main__":
    unittest.main()
