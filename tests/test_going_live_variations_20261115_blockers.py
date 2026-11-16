"""GOING-LIVE-VARIATIONS-20261115 regression blockers.

Owner ruling 2026-11-15 22:35 ET: no shadow sleeves, they have to
be live. 15 registered conversion variations rostered live beside
their parents under GUTTING AS VARIATION (CONV-29 x3, CONV-30 x4,
CONV-31, CONV-32 x2, CONV-33, CONV-35 x2, CONV-36, CONV-37): each is
a NEW sleeve id whose roster row differs from its parent's in
exactly {id, module}; each carries its registered arm profile in
its engine's SPECS layer under its own id; the Lazarus and Midna
variations consume the parent's own fire stream re-addressed by
desk3/var_fires.py. Parents are byte-untouched, proven below
against sha256 pins computed on the pre-change tree at commit
a0a481f (roster rows, adapter module files, engine SPECS entries).

Fail direction: proven on a git-archive copy of the pre-change
tree (commit a0a481f) in /tmp: the roster, SPECS, registry and
behavior tests fail there (the variation ids, SPECS entries,
adapters and registry entries do not exist); the parent-hash tests
pass on both trees by design (they pin the parents, which the
change must not move).
"""
import hashlib
import importlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.join(os.path.dirname(__file__), "..")

VARIATIONS = [('aster_abs_link_4h_varhx2', 'aster_abs_link_4h', 'CONV-29'), ('aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2', 'aster_r19_linkusdt_absorption_base_fixed16_fullcash', 'CONV-29'), ('aster_r19_linkusdt_absorption_base_fixed16_volume1pct_varhx2', 'aster_r19_linkusdt_absorption_base_fixed16_volume1pct', 'CONV-29'), ('1d_varjx2', '1d', 'CONV-30'), ('1d_vardh', '1d', 'CONV-30'), ('1d_varhx4', '1d', 'CONV-30'), ('1d_vardt', '1d', 'CONV-30'), ('s_1dg_vardh', 's_1dg', 'CONV-31'), ('s_rules_1d_vardh', 's_rules_1d', 'CONV-32'), ('s_rules_1d_varhx4', 's_rules_1d', 'CONV-32'), ('s_1wc_ml_vards', 's_1wc_ml', 'CONV-33'), ('1w_vargd', '1w', 'CONV-35'), ('1wa_vargd', '1wa', 'CONV-35'), ('s_rules_1w_varhx2', 's_rules_1w', 'CONV-36'), ('s_mn_hourly_1w_varn1', 's_mn_hourly_1w', 'CONV-37')]

VARIATION_MODULES = ['adapters3/aster_abs_link_4h_varhx2.py', 'adapters3/aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2.py', 'adapters3/aster_r19_linkusdt_absorption_base_fixed16_volume1pct_varhx2.py', 'adapters3/laz_1d_varjx2.py', 'adapters3/laz_1d_vardh.py', 'adapters3/laz_1d_varhx4.py', 'adapters3/laz_1d_vardt.py', 'adapters3/laz_s_1dg_vardh.py', 'adapters3/laz_s_rules_1d_vardh.py', 'adapters3/laz_s_rules_1d_varhx4.py', 'adapters3/laz_s_1wc_ml_vards.py', 'adapters3/laz_1w_vargd.py', 'adapters3/laz_1wa_vargd.py', 'adapters3/laz_s_rules_1w_varhx2.py', 'adapters3/s_mn_hourly_1w_varn1.py']

# OBV-CLASS-20261116 re-pin (2026-11-16): eight roster_row_sha256
# values below were re-based because OBV-CLASS-20261116 added
# own_book_view: true to those parents' roster rows (1d, s_1dg,
# s_rules_1d, s_1wc_ml, 1w, 1wa, s_rules_1w, s_mn_hourly_1w).
# Verified: each amended row differs from its pre-OBV row by
# exactly that one key; module_sha256 pins are untouched.
PARENT_PINS = {'aster_abs_link_4h': {'roster_row_sha256': 'b0c20e23076c1140e51a11c88a6c8525ba044983a2188593ed6c5f68f1da954b', 'module_path': 'adapters3/aster_abs_link_4h.py', 'module_sha256': '122f58048cb037e30c89667ccb6bf3818582d25cc78873304b9f76de2a2d0061'}, 'aster_r19_linkusdt_absorption_base_fixed16_fullcash': {'roster_row_sha256': '465472f2169ec926a2d35983e918d404ed2723ee875125a4cffc7a6e599338ab', 'module_path': 'adapters3/aster_r19_linkusdt_absorption_base_fixed16_fullcash.py', 'module_sha256': '54d33cdfa1d9d6c7a70bc24d225f20b1774d8d71ffa5fa0be00d0d5eb1b2a3f0'}, 'aster_r19_linkusdt_absorption_base_fixed16_volume1pct': {'roster_row_sha256': 'a4942fce23e0cfcde97e0dc74aa95972e797e6635605c02bb8b7ab7d0d178c51', 'module_path': 'adapters3/aster_r19_linkusdt_absorption_base_fixed16_volume1pct.py', 'module_sha256': '6ed1896fda62329a4efe4216dc02f3c8b38d1c0629183b503535518aba06bf0a'}, '1d': {'roster_row_sha256': '46dd695592d01958faf6af70f9162e1dc6eaf66abd1a1dd8dff45a7fa06b2f1c', 'module_path': 'adapters3/laz_1d.py', 'module_sha256': 'a7f861bb3f25dc33b60410ec0b7c3820af1c09600328b395da85ddceea8d8874'}, 's_1dg': {'roster_row_sha256': 'b71147b4650bb61b480e8e6de828cd90080d1590236b00b630f52f46c68a87fe', 'module_path': 'adapters3/laz_s_1dg.py', 'module_sha256': '09d24d769e5a6167e5991b7d22761fc08fdf22550e7f4dab25846c5f167212c9'}, 's_rules_1d': {'roster_row_sha256': '5a88676d5feb0216ce09cbef558b626e8d08b7cba47607faf16197721f6af641', 'module_path': 'adapters3/s_rules_1d.py', 'module_sha256': '8b482c454bd5a0411cb50c97f3a731c38e06933ce7fb269459ab5ea57cc6580b'}, 's_1wc_ml': {'roster_row_sha256': '4cd2717b7235f339225f1385d12cb28ad58467f7763ff5b3d8814918aef52d3c', 'module_path': 'adapters3/laz_s_1wc_ml.py', 'module_sha256': '701c5ce0d7ee97395448389eafda245d2a038504cc7250a7f4ec65d41a186335'}, '1w': {'roster_row_sha256': '5a4e4c160ca9b9f6869cc27d639e8a281de52f8c589eb5aa92bfe4173a86e037', 'module_path': 'adapters3/laz_1w.py', 'module_sha256': '60de11ca81f99a11a1f5d3bd58cdcfbd4d36038e8e58063e12a88f30b0dd0de1'}, '1wa': {'roster_row_sha256': '913464465c74e5d52ab6f4fc9add022d4204cd9f92cb265152e9ee4596f52c39', 'module_path': 'adapters3/laz_1wa.py', 'module_sha256': 'e0c1c7f090b7c8e99c2ff7f5578f33ed69672090a64be28f301d423bd41d4f15'}, 's_rules_1w': {'roster_row_sha256': 'e6ac857b35d25fb2fd35b03d34c11551359ea46d8e580319644e29d003ab1440', 'module_path': 'adapters3/s_rules_1w.py', 'module_sha256': 'ce53a94d39e60d5e6e73ef96b3ae52de998ead5fea1e7e30926d085dc95e1e1c'}, 's_mn_hourly_1w': {'roster_row_sha256': '42fbdfa10e1dbdc09ebb2c686a37c6f344d0a5f2efa64df1d9910f04cb32e0f4', 'module_path': 'adapters3/s_mn_hourly_1w.py', 'module_sha256': 'f50439b01007d219651afcab7485eb04e1da417a8775e25fe67ff1dc1c3a8966'}}

SPEC_PINS = {'1d': '9df16314b0a8c046f8f9a3d32ac3f5803e0bbf41ff3baa955e53afd25f48e173', 's_1dg': '4b8332306eeb45454c82d95c93f55d6f6eb9f79ef059a37931a6e01900dd20f2', 's_rules_1d': '1057c691bf9cb9129e7a8cbae912ba017ec2ae367dd528b484f54f90499637ee', 's_1wc_ml': '06ea02f2f71ee9965c9e91a63fd8d78c06da99f34e8089ce8f1b736fe48e0612', '1w': '9cc6e7aa8d80a21d0aed120159dc815e8b6fa05bc74388e6e00e31f55267c25f', '1wa': 'ee50892a1d3faecd0d0c778258f47c0b991ce4f254c24796217e3102d1047214', 's_rules_1w': 'ebb4de86b1c0f55f74272f6c887ca2dbafc4e2dacf40f19f1d03e6bd21aa056d', 's_mn_hourly_1w': '2a5689f8caf24f758fb91fad35bbcac330fa027ae53733f8a6b08810551cdb12', 'aster_abs_link_4h': 'd98550ad5a36a966d05c8f428dcdae29cd7c37ff5f917811f98d86bf074f0ea4', 'aster_r19_linkusdt_absorption_base_fixed16_fullcash': 'c450a82467e97eb83c623795ab9251f81aec871b979c0ae35dd0d8f0663d3b6f', 'aster_r19_linkusdt_absorption_base_fixed16_volume1pct': '830a99674c0a9e6d18e32f9cd9acf7349783856a5a3fc45fec3d4b17402e6a06'}

FALSIFIERS = {'aster_abs_link_4h_varhx2': ('First grade at 15 resolved shadow exits.', 'Paired delta not positive at the grade retires the variation.'), 'aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2': ('First grade at 15 resolved shadow exits.', 'Paired delta not positive at the grade retires the variation.'), 'aster_r19_linkusdt_absorption_base_fixed16_volume1pct_varhx2': ('First grade at 15 resolved shadow exits.', 'Paired delta not positive at the grade retires the variation.'), '1d_varjx2': ('First grade at 20 resolved shadow exits per arm, paired against the base profile on the same entries.', 'An arm whose paired delta is not positive at its grade retires.'), '1d_vardh': ('First grade at 20 resolved shadow exits per arm, paired against the base profile on the same entries.', 'An arm whose paired delta is not positive at its grade retires.'), '1d_varhx4': ('First grade at 20 resolved shadow exits per arm, paired against the base profile on the same entries.', 'An arm whose paired delta is not positive at its grade retires.'), '1d_vardt': ('First grade at 20 resolved shadow exits per arm, paired against the base profile on the same entries.', 'An arm whose paired delta is not positive at its grade retires.'), 's_1dg_vardh': ('First grade at 20 resolved shadow exits (F1 check).', 'Paired delta not positive retires the arm.'), 's_rules_1d_vardh': ('First grade at 20 resolved shadow exits per arm (F1 check).', 'An arm whose paired delta is not positive retires.'), 's_rules_1d_varhx4': ('First grade at 20 resolved shadow exits per arm (F1 check).', 'An arm whose paired delta is not positive retires.'), 's_1wc_ml_vards': ('First grade at 20 resolved shadow exits (F1 check).', 'Paired delta not positive retires the arm.'), '1w_vargd': ('20 paired forward fires per sleeve.', 'Paired delta not positive retires the gateless form for that sleeve.'), '1wa_vargd': ('20 paired forward fires per sleeve.', 'Paired delta not positive retires the gateless form for that sleeve.'), 's_rules_1w_varhx2': ('First grade at 15 resolved shadow exits.', 'Paired delta not positive against the current live profile retires it.'), 's_mn_hourly_1w_varn1': ('20 paired forward fires.', 'Night-1 arm not beating the own-exit arm retires the form.')}


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _load(name):
    return json.load(open(os.path.join(ROOT, name)))


class RosterAndRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = _load("config/sleeves.json")
        cls.rows = cls.cfg["sleeves"]
        cls.by_id = {}
        for r in cls.rows:
            cls.by_id.setdefault(r["id"], []).append(r)
        cls.reg = _load("config/conversion_variations_20261115.json")

    def test_variation_ids_present_exactly_once(self):
        for vid, _, _ in VARIATIONS:
            self.assertEqual(len(self.by_id.get(vid, [])), 1, vid)

    def test_variation_row_differs_from_parent_only_in_id_module(self):
        for vid, parent, _ in VARIATIONS:
            a = dict(self.by_id[parent][0]); b = dict(self.by_id[vid][0])
            self.assertEqual({k for k in set(a) | set(b) if a.get(k) != b.get(k)},
                             {"id", "module"}, vid)
            mod = importlib.import_module(b["module"])
            self.assertEqual(mod.SLEEVE_ID, vid)

    def test_parents_byte_untouched(self):
        for pid, pin in PARENT_PINS.items():
            row = self.by_id[pid][0]
            self.assertEqual(_sha(json.dumps(row, sort_keys=True).encode()),
                             pin["roster_row_sha256"], pid)
            with open(os.path.join(ROOT, pin["module_path"]), "rb") as fh:
                self.assertEqual(_sha(fh.read()), pin["module_sha256"], pid)

    def test_parent_specs_byte_untouched(self):
        from desk3 import lazarus, lazarus_midna, aster_batch1, aster_b11_crypto
        src = {}
        for pid in ("1d", "s_1dg", "s_rules_1d", "s_1wc_ml", "1w", "1wa", "s_rules_1w"):
            src[pid] = lazarus.SPECS[pid]
        src["s_mn_hourly_1w"] = lazarus_midna.SPECS["s_mn_hourly_1w"]
        src["aster_abs_link_4h"] = aster_batch1.SPECS["aster_abs_link_4h"]
        for pid in ("aster_r19_linkusdt_absorption_base_fixed16_fullcash",
                    "aster_r19_linkusdt_absorption_base_fixed16_volume1pct"):
            src[pid] = aster_b11_crypto.SPECS[pid]
        for pid, want in SPEC_PINS.items():
            got = _sha(json.dumps(src[pid], sort_keys=True, default=str).encode())
            self.assertEqual(got, want, pid)

    def test_variation_module_files_load_with_matching_sleeve_id(self):
        for path in VARIATION_MODULES:
            name = path[:-3].replace("/", ".")
            mod = importlib.import_module(name)
            self.assertTrue(any(mod.SLEEVE_ID == vid for vid, _, _ in VARIATIONS), path)

    def test_registry_entries_carry_register_falsifiers(self):
        by_id = {v["id"]: v for v in self.reg["variations"]}
        for vid, parent, conv in VARIATIONS:
            v = by_id[vid]
            self.assertEqual(v["parent"], parent, vid)
            self.assertEqual(v["conv"], conv, vid)
            self.assertEqual(v["falsifier"], FALSIFIERS[vid][0], vid)
            self.assertEqual(v["kill_rule"], FALSIFIERS[vid][1], vid)
            self.assertIn("GOING-LIVE-VARIATIONS-20261115", v["status"], vid)


class SpecProfiles(unittest.TestCase):
    def test_lazarus_variation_profiles_exact(self):
        from desk3 import lazarus
        S = lazarus.SPECS
        self.assertEqual((S["1d_varjx2"]["horizon_sessions"], S["1d_varjx2"]["stop_pct"], S["1d_varjx2"]["target_pct"]), (80, 0.15, 0.20))
        self.assertEqual((S["1d_vardh"]["horizon_sessions"], S["1d_vardh"]["stop_pct"], S["1d_vardh"]["target_pct"]), (None, 0.15, 0.20))
        self.assertEqual((S["1d_varhx4"]["horizon_sessions"], S["1d_varhx4"]["stop_pct"], S["1d_varhx4"]["target_pct"]), (160, 0.15, 0.20))
        self.assertEqual((S["1d_vardt"]["horizon_sessions"], S["1d_vardt"]["stop_pct"], S["1d_vardt"]["target_pct"]), (40, 0.15, None))
        for vid in ("1d_varjx2", "1d_vardh", "1d_varhx4", "1d_vardt"):
            self.assertNotIn("partial_pct", S[vid], vid)
            self.assertTrue(S[vid]["force_spec_horizon"], vid)
            self.assertEqual(S[vid]["slots"], S["1d"]["slots"], vid)
            self.assertEqual(S[vid]["capital"], S["1d"]["capital"], vid)
        self.assertIsNone(S["s_1dg_vardh"]["horizon_sessions"])
        self.assertIsNone(S["s_rules_1d_vardh"]["horizon_sessions"])
        self.assertEqual(S["s_rules_1d_varhx4"]["horizon_sessions"], 88)
        for vid in ("s_rules_1d_vardh", "s_rules_1d_varhx4"):
            self.assertNotIn("horizon_from_fire", S[vid], vid)
            self.assertNotIn("horizon_plus_one", S[vid], vid)
        self.assertIsNone(S["s_1wc_ml_vards"]["stop_pct"])
        self.assertEqual(S["s_1wc_ml_vards"]["horizon_sessions"], 252)
        self.assertNotIn("qqq_down", S["1w_vargd"])
        self.assertNotIn("qqq_down", S["1wa_vargd"])
        self.assertTrue(S["1w"]["qqq_down"] and S["1wa"]["qqq_down"])
        self.assertEqual((S["s_rules_1w_varhx2"]["horizon_sessions"], S["s_rules_1w_varhx2"]["stop_pct"]), (108, 0.15))
        self.assertTrue(S["s_rules_1w_varhx2"]["qqq_down"])

    def test_midna_and_aster_profiles_exact(self):
        from desk3 import lazarus_midna, aster_batch1, aster_b11_crypto
        v = lazarus_midna.SPECS["s_mn_hourly_1w_varn1"]
        self.assertEqual((v["hold_sessions"], v["stop"], v["budget"]), (1, None, 1000.0))
        self.assertEqual(aster_batch1.SPECS["aster_abs_link_4h_varhx2"]["hold_h"], 32)
        self.assertNotIn("hold_h", aster_batch1.SPECS["aster_abs_link_4h"])
        for vid in ("aster_r19_linkusdt_absorption_base_fixed16_fullcash_varhx2",
                    "aster_r19_linkusdt_absorption_base_fixed16_volume1pct_varhx2"):
            parent = vid[:-len("_varhx2")]
            want = dict(aster_b11_crypto.SPECS[parent]); want["hold_h"] = 32
            self.assertEqual(aster_b11_crypto.SPECS[vid], want, vid)


def _laz_ctx(sd):
    return {"state_dir": sd, "now": "2026-11-16T15:00:00+00:00"}


def _laz_view(fires, positions=None, bars=None):
    return {"now": "2026-11-16T15:00:00+00:00", "lazarus_fires": fires,
            "positions": positions or [],
            "bars": bars or {"QQQ": [{"t": "2026-11-13", "c": 100.0},
                                     {"t": "2026-11-16", "c": 101.0}],
                             "AAA": [{"t": "2026-11-16", "c": 10.0}]}}


class Behavior(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _sd(self, name):
        d = os.path.join(self.tmp, name); os.makedirs(d); return d

    def test_clone_readdresses_without_mutating(self):
        from desk3.var_fires import clone_view_for_parent
        fires = [{"sleeve_id": "1d", "symbol": "AAA"}, {"sleeve_id": "1w", "symbol": "BBB"}]
        view = {"lazarus_fires": fires, "bars": {}}
        out = clone_view_for_parent(view, "1d", "1d_varjx2")
        self.assertEqual(out["lazarus_fires"][0]["sleeve_id"], "1d_varjx2")
        self.assertEqual(out["lazarus_fires"][1]["sleeve_id"], "1w")
        self.assertEqual(fires[0]["sleeve_id"], "1d")

    def test_1d_varjx2_entry_stores_horizon_80(self):
        from adapters3 import laz_1d_varjx2
        sd = self._sd("jx2")
        fire = [{"sleeve_id": "1d", "symbol": "AAA",
                 "fired_at": "2026-11-16T14:00:00+00:00", "price": 10.0,
                 "qqq_red": True}]
        out = laz_1d_varjx2.evaluate(_laz_view(fire), _laz_ctx(sd))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["stop_price"], 8.5)
        st = json.load(open(os.path.join(sd, "laz_state.json")))
        self.assertEqual(st["AAA"]["horizon_sessions"], 80)

    def test_1d_vardh_no_time_exit_but_stop_exit_lives(self):
        from adapters3 import laz_1d_vardh
        sd = self._sd("dh")
        fire = [{"sleeve_id": "1d", "symbol": "AAA",
                 "fired_at": "2026-11-16T14:00:00+00:00", "price": 10.0,
                 "qqq_red": True}]
        self.assertEqual(len(laz_1d_vardh.evaluate(_laz_view(fire), _laz_ctx(sd))), 1)
        pos = [{"symbol": "AAA", "qty": 172, "avg_price": 10.0,
                "opened_at": "2026-08-01T15:00:00+00:00"}]
        bars = {"AAA": [{"t": "2026-11-16", "c": 10.5}],
                "SPY": [{"t": d, "c": 100.0} for d in
                        ("2026-08-03", "2026-09-01", "2026-10-01",
                         "2026-11-02", "2026-11-16")]}
        # aged past the parent's 40 and the x2's 80 alike on a
        # business-day fallback count: no time exit under DROP_horizon
        self.assertEqual(laz_1d_vardh.evaluate(_laz_view([], pos, bars), _laz_ctx(sd)), [])
        bars["AAA"] = [{"t": "2026-11-16", "c": 8.0}]  # below the 15% stop
        out = laz_1d_vardh.evaluate(_laz_view([], pos, bars), _laz_ctx(sd))
        self.assertEqual(len(out), 1)
        self.assertIn("stop15", out[0]["reason"])

    def test_gate_drop_enters_where_parent_refuses(self):
        from adapters3 import laz_1w, laz_1w_vargd
        fire = [{"sleeve_id": "1w", "symbol": "AAA",
                 "fired_at": "2026-11-16T14:00:00+00:00", "price": 10.0,
                 "qqq_red": False}]
        self.assertEqual(laz_1w.evaluate(_laz_view(fire), _laz_ctx(self._sd("w"))), [])
        out = laz_1w_vargd.evaluate(_laz_view(fire), _laz_ctx(self._sd("wg")))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "AAA")

    def test_rules_1w_varhx2_forces_horizon_108(self):
        from adapters3 import laz_s_rules_1w_varhx2
        sd = self._sd("r1w")
        fire = [{"sleeve_id": "s_rules_1w", "symbol": "AAA",
                 "fired_at": "2026-11-16T14:00:00+00:00", "price": 10.0,
                 "qqq_red": True, "horizon_sessions": 54}]
        out = laz_s_rules_1w_varhx2.evaluate(_laz_view(fire), _laz_ctx(sd))
        self.assertEqual(len(out), 1)
        st = json.load(open(os.path.join(sd, "laz_state.json")))
        self.assertEqual(st["AAA"]["horizon_sessions"], 108)

    def test_1wc_ml_vards_entry_has_no_stop(self):
        from adapters3 import laz_s_1wc_ml, laz_s_1wc_ml_vards
        fire = [{"sleeve_id": "s_1wc_ml", "symbol": "AAA",
                 "fired_at": "2026-11-16T14:00:00+00:00", "price": 10.0,
                 "cap_tier": "mid", "signal_tier": "A", "family": "cyan"}]
        p = laz_s_1wc_ml.evaluate(_laz_view(fire), _laz_ctx(self._sd("mlp")))
        v = laz_s_1wc_ml_vards.evaluate(_laz_view(fire), _laz_ctx(self._sd("mlv")))
        self.assertEqual(len(p), 1); self.assertEqual(len(v), 1)
        self.assertEqual(p[0]["stop_price"], 8.5)
        self.assertIsNone(v[0]["stop_price"])

    def test_abs_link_varhx2_deadline_doubled(self):
        from desk3 import aster_batch1
        now = aster_batch1._parse_ts("2026-11-16T12:00:00+00:00") \
            if hasattr(aster_batch1, "_parse_ts") else None
        from datetime import datetime, timezone, timedelta
        now = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
        confirm = (now - timedelta(hours=20)).isoformat()
        pos = [{"symbol": "LINKUSDT", "qty": 5.0, "avg_price": 10.0,
                "confirm_close_at": confirm,
                "opened_at": (now - timedelta(hours=20)).isoformat()}]
        view = {"now": now.isoformat(), "positions": pos, "bars": {},
                "quotes": {}, "cash": 10000.0}
        ctx = {"state_dir": self._sd("abs")}
        parent_out = aster_batch1.evaluate("aster_abs_link_4h", view, ctx)
        var_out = aster_batch1.evaluate("aster_abs_link_4h_varhx2", view, ctx)
        self.assertEqual(len(parent_out), 1)   # 16h deadline passed
        self.assertEqual(var_out, [])          # 32h deadline not reached

    def test_midna_varn1_exits_after_night_1(self):
        from adapters3 import s_mn_hourly_1w_varn1
        bars = {"AAA": [{"t": "2026-11-13", "c": 10.0},
                        {"t": "2026-11-16", "c": 10.5}]}
        pos = [{"symbol": "AAA", "qty": 10, "avg_price": 10.0,
                "entry_date": "2026-11-13"}]
        view = {"now": "2026-11-16T15:00:00+00:00", "positions": pos,
                "bars": bars, "fires": []}
        ctx = {"session": "2026-11-16", "now": "2026-11-16T15:00:00+00:00"}
        out = s_mn_hourly_1w_varn1.evaluate(view, ctx)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")


if __name__ == "__main__":
    unittest.main()
