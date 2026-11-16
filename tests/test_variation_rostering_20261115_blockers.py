"""VARIATION-ROSTERING-20261115 regression blockers.

The 19 F4 variations registered in config/f4_variations_20261115.json
(14 Q07 _vargd GATE_DROP, 2 Tensor C1 _varpx PARAM_EXTREME, 3 funding
_varsg SIGN_GATE_DROP) are rostered as first-class sleeves in
config/sleeves.json: roster 339 -> 358. Every variation inherits its
parent's engine/config with exactly the registered variation applied;
parents are byte-untouched (proven below against sha256 hashes of the
parents' roster rows, module files and engine SPECS entries, computed
on the pre-change tree at commit 1aa0220).

Covered:
- roster count exactly 359 (358 at this landing; amended
  2026-11-15 by CONVERSION-VARIATION-20261115, CONV-47); the 19
  variation ids present exactly once.
- each variation's roster row differs from its parent's row in
  exactly {id, module}.
- lazarus_q07 SPECS: variation == parent with filters replaced by
  the registered variation_filters; nothing else differs.
- q07_engine adapters: variation SPEC == parent SPEC except id and
  filters.
- aster_batch13: variation SPECS == parent + ret60_min=0; behavior:
  a ret60=15 fire is refused by the parent and admitted by the
  variation, a ret60=40 fire is admitted by both; the variations
  carry their parents' ENH11 fire-age membership.
- aster_b11_crypto: variation SPECS == parent + drop_funding_sign;
  behavior (absorption patched in): funding >= 0 refuses the parent
  and admits the variation, unobserved funding refuses both,
  funding < 0 admits both.
- aster_sleeves ADA _varsg: the variation module calls
  evaluate_crypto with drop_funding_sign=True; the parent module
  does not; the _common default stays False.
- registry: 19 variations, each marked rostered 2026-11-15, each
  carrying the uniform 20-fire falsifier.

Fail direction: proven on a git-archive copy of the pre-change tree
(commit 1aa0220) in /tmp: the roster/spec/behavior tests fail there
(the variation ids, SPECS entries and roster rows do not exist);
the parent-hash tests pass on both trees by design (they pin the
parents, which the change must not move).
"""
import hashlib
import importlib
import inspect
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.join(os.path.dirname(__file__), "..")

# OBV-CLASS-20261116 re-pin (2026-11-16): fourteen roster_row_sha256
# values below were re-based because OBV-CLASS-20261116 added
# own_book_view: true to those parents' roster rows (the s_q07w_*
# parents). Verified: each amended row differs from its pre-OBV row
# by exactly that one key; module and spec pins are untouched.
PARENT_HASHES = {'s_q07w_c52_ml_mom6_tierA_wlow': {'roster_row_sha256': '6cfdd7c94e0ec7e36f9d6661cb85f787821daa41c0946b4420c53c55824c6003', 'module_path': 'adapters3/s_q07w_c52_ml_mom6_tierA_wlow.py', 'module_sha256': 'a9c8e16e667aafd391981ba3d15ad13e43df6255afd40879338c8e8a39bf0575', 'spec_where': 'lazarus_q07', 'spec_sha256': 'bcd77ad2769caab5afd7fcb3d9fe0b8b93061bcf1a90cfa9673fe82556b3dfd6'}, 's_q07w_c52_ml_mom6_wspike2': {'roster_row_sha256': '6fc7228d6ee32027edb6e145059be609f6e562d5756539ac190dd7d94a9d3b9a', 'module_path': 'adapters3/s_q07w_c52_ml_mom6_wspike2.py', 'module_sha256': 'f3087f2497bafba499496928c7414f09c33953f887eac7c76a2d1d5e69c56973', 'spec_where': 'lazarus_q07', 'spec_sha256': '7fd71715026d8752d6b1fabbcb3d2bccb9d130b7b731e9476db6f896d5094cf3'}, 's_q07w_c52_ml_tierA_wcov': {'roster_row_sha256': '4178e619bbaf25f769ec5f74fea33dc829fdfc1374bd56f56770c6b02b5b126d', 'module_path': 'adapters3/s_q07w_c52_ml_tierA_wcov.py', 'module_sha256': '527e929578a8b5ccf7f348bf1b03ed94ace3460f50d0e400685c874b4d7a76bd', 'spec_where': 'lazarus_q07', 'spec_sha256': '90b6a35e51158c8ff1a0c3c7d40166d6b1ebab1acfd06b00a10fdf30b196c6fa'}, 's_q07w_c52_ml_tierA_wlow': {'roster_row_sha256': 'd0535999f6a36ef78f644c3c717340bda6462ebae7467da193d04f20d6191fb1', 'module_path': 'adapters3/s_q07w_c52_ml_tierA_wlow.py', 'module_sha256': '2934de07c12cc113ee5733e32a93864f417b6ea55dfc0c3c32e9034bfde94a3d', 'spec_where': 'lazarus_q07', 'spec_sha256': '4f8c43d92405310c09c3e2f0cfe37f2856fbdb1ca7635c80fb79bfe3355a6884'}, 's_q07w_c78_ml_deep70_tierA_wlow': {'roster_row_sha256': 'cbf9ae19ee99eebb4a306f2889f433c39c8a14a4d53e3e7f52c68e256b7fd176', 'module_path': 'adapters3/s_q07w_c78_ml_deep70_tierA_wlow.py', 'module_sha256': 'a304d232dba7b28d3bc1acdc04aec4f7f678b00fed9ce186f4a596b5a9c2f863', 'spec_where': 'lazarus_q07', 'spec_sha256': 'b47c89f0332c4a923bc7f6481920ffd537dac8d3e373c53eb32bfbc5aed61f28'}, 's_q07w_c78_ml_mom6_tierA_wlow': {'roster_row_sha256': '13a006df5a08391852b871ca19fdad36222022609735d536304f6f57a4288f16', 'module_path': 'adapters3/s_q07w_c78_ml_mom6_tierA_wlow.py', 'module_sha256': 'd40c50b0b6e0c589bf447035d739dc3d57b7654f9c5d15f1a2b9364c43b66458', 'spec_where': 'lazarus_q07', 'spec_sha256': '2e93c3722bf1918a678d3de1a1c73143f5f3f47aa9ec0c6a68e7264f7738ae66'}, 's_q07w_c78_ml_tierA_wcov': {'roster_row_sha256': '5189cd32f3a0eba5ed154d3f76cb815be087f932e5188d718b64095221108797', 'module_path': 'adapters3/s_q07w_c78_ml_tierA_wcov.py', 'module_sha256': 'f19aeed9dfb3fc24e7802eeb08354bb1dc75a443339203b2c2cf94e5016fd20b', 'spec_where': 'lazarus_q07', 'spec_sha256': '9743a5d6af1052e2df939b18c99c29573b67071f755da632adff9d022f8e2cd7'}, 's_q07w_c78_ml_tierA_wlow': {'roster_row_sha256': 'a23b2112eebaef8d5a8f07e21614a9c2d1e2c0f538e5dbd017935f57479179b3', 'module_path': 'adapters3/s_q07w_c78_ml_tierA_wlow.py', 'module_sha256': '43b32216f2421d6a3bd9d6b3bcc7d7099921f22c5d21a82b5ae9d23bdcace2ac', 'spec_where': 'lazarus_q07', 'spec_sha256': 'a785a97f1e88b69d06df86c9d945300d941f61bc5ac2a325bcf90442e8b15bb0'}, 's_q07w_g52_ml_ats_z1_mom6_wlow': {'roster_row_sha256': 'b5ce46d77f4649c92e1efffa8dacf76e2f97f4341840254458766deca3f064f6', 'module_path': 'adapters3/s_q07w_g52_ml_ats_z1_mom6_wlow.py', 'module_sha256': '1061ad3488422d1d8136634dce527799bb7a6c482f1f8b13592ef4b8f721a311', 'spec_where': 'lazarus_q07', 'spec_sha256': '148a4935735b5f395ebaf3f5a5d9ec9999b150daf283dfba36626ae8bc882c01'}, 's_q07w_g52_ml_ins2_wlow': {'roster_row_sha256': '2b3b977e8a9c7358280e15a0479b88d2a1d80f93eb9d937f6d60a728c199421f', 'module_path': 'adapters3/s_q07w_g52_ml_ins2_wlow.py', 'module_sha256': '1acea800d00b1604e0a6539e68fc2a20cb4571efe6a974cb417b6fe6219b55c3', 'spec_where': None, 'spec_sha256': None}, 's_q07w_g52_ml_tierA_wcov': {'roster_row_sha256': '81c29067ce7838e06e728fb4437962150a114c07ba27671207c72da81d708e76', 'module_path': 'adapters3/s_q07w_g52_ml_tierA_wcov.py', 'module_sha256': '4f7b100f821573f22c9ee8cce67e63ba6b4fec9a2b61d1b8c60490e231075647', 'spec_where': 'lazarus_q07', 'spec_sha256': '25e7055a4949b418da7f8935727eb06fe6e222ad4e82390e3420166d61002fc4'}, 's_q07w_g78_ml_tierA_wcov': {'roster_row_sha256': '1567f44484599fd90e38637bd9799ba353db8bec01da05087244352d2e251149', 'module_path': 'adapters3/s_q07w_g78_ml_tierA_wcov.py', 'module_sha256': '9da7d6d34296ff87745ed318536ceacb6766dc476acedfe23c45b780c52142c2', 'spec_where': 'lazarus_q07', 'spec_sha256': 'a6f547ebd7554adbe8b725edd2d90ba2dc2211142a38793b30c2d4e7fbcadd3f'}, 's_q07w_s52_ml_deep70_ins2_vix20': {'roster_row_sha256': '060bd96ae6a37db0971fb8c65788179835345ec5c42cdd334c3f69ab272d230c', 'module_path': 'adapters3/s_q07w_s52_ml_deep70_ins2_vix20.py', 'module_sha256': '29fb3eb12000b9b401877c97445f526f79abd30cad3eaa63727e4cff5bfa9966', 'spec_where': None, 'spec_sha256': None}, 's_q07w_s78_ml_deep70_ins2_vix20': {'roster_row_sha256': '171ba2d790abcfa43e07fe0b3e62ece769244bfd6377a0ebb47b1471e7c75473', 'module_path': 'adapters3/s_q07w_s78_ml_deep70_ins2_vix20.py', 'module_sha256': '869a19c57f0ae770e86a3db19fb092da435169b8d84961d664008b2799674b93', 'spec_where': None, 'spec_sha256': None}, 'aster_tensor_c1_cash_all_25': {'roster_row_sha256': '43fbcb97b6b8474e4a69424d914dc4d7f0bcf73913a53e936d3654b3cc7a09c1', 'module_path': 'adapters3/aster_tensor_c1_cash_all_25.py', 'module_sha256': '95f060543e068bdfd6fcd3bb4a3e657ab18cb271bd8db7c57b7705770e4c5922', 'spec_where': 'aster_batch13', 'spec_sha256': '77c8021f6a2aede44007d5e6613485b0b8117a9d7bb1b9f948737e778b68a486'}, 'aster_tensor_c1_cash_hot_25': {'roster_row_sha256': 'e8cf8b6446fef4a7621652d2467bf3b2914de9432fee7b19dcf791be49346e45', 'module_path': 'adapters3/aster_tensor_c1_cash_hot_25.py', 'module_sha256': 'c25e5f4310ed1dfecd62733001ccae02af68a4075cd7d4fc88c2065070803788', 'spec_where': 'aster_batch13', 'spec_sha256': '20da37a747c065ea6298bf86476afe43a38d0e5ba2de5794a352c2cd3d3fb382'}, 'aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash': {'roster_row_sha256': 'b743e095602f3c05a9183844eccefbc3b522573745d8e9d620dc124c81ab7753', 'module_path': 'adapters3/aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash.py', 'module_sha256': '0804b27c1656366a23918e1511ae608156223102353f4ee38d1944a895112798', 'spec_where': 'aster_b11', 'spec_sha256': 'd99c3ba9abf4692464cb3e0de13aa7dd95330c1d95699c504ac851bc00723be1'}, 'aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct': {'roster_row_sha256': '13457a0b9490a78a64bf660ec690c3b016deabe2f2c2e159f500bcc539d60a9b', 'module_path': 'adapters3/aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct.py', 'module_sha256': '35d516f7ba9b305a61c835c1caf3a856d56dd6b497aa589bdb6a064feee18e32', 'spec_where': 'aster_b11', 'spec_sha256': 'c6ca4b1b343451d724b014545baba662dab59934bfcc3e9a30713704bb930fd4'}, 'aster_abs_neg_ada_vol1pct': {'roster_row_sha256': 'fe73a41fc490fa892bb2379457c91856d123ac8105d32aad100fe32aede76b85', 'module_path': 'aster_sleeves/aster_abs_neg_ada_vol1pct.py', 'module_sha256': '32122f67316f85b8c9f34239caefa9954efd502efea03a8354657a4948cb516c', 'spec_where': None, 'spec_sha256': None}}

CTX = {"session": "2026-10-24", "now": "2026-10-24T15:00:00"}

# The 19 variation module files, named explicitly: each is loaded
# by path in RosterShape.test_variation_module_files_load_with_
# matching_sleeve_id below (this is also the coverage the blocker
# ratchet counts: a module named in a gate-wired blocker).
VARIATION_MODULES = [
    "adapters3/s_q07w_c52_ml_mom6_tierA_wlow_vargd.py",
    "adapters3/s_q07w_c52_ml_mom6_wspike2_vargd.py",
    "adapters3/s_q07w_c52_ml_tierA_wcov_vargd.py",
    "adapters3/s_q07w_c52_ml_tierA_wlow_vargd.py",
    "adapters3/s_q07w_c78_ml_deep70_tierA_wlow_vargd.py",
    "adapters3/s_q07w_c78_ml_mom6_tierA_wlow_vargd.py",
    "adapters3/s_q07w_c78_ml_tierA_wcov_vargd.py",
    "adapters3/s_q07w_c78_ml_tierA_wlow_vargd.py",
    "adapters3/s_q07w_g52_ml_ats_z1_mom6_wlow_vargd.py",
    "adapters3/s_q07w_g52_ml_ins2_wlow_vargd.py",
    "adapters3/s_q07w_g52_ml_tierA_wcov_vargd.py",
    "adapters3/s_q07w_g78_ml_tierA_wcov_vargd.py",
    "adapters3/s_q07w_s52_ml_deep70_ins2_vix20_vargd.py",
    "adapters3/s_q07w_s78_ml_deep70_ins2_vix20_vargd.py",
    "adapters3/aster_tensor_c1_cash_all_25_varpx.py",
    "adapters3/aster_tensor_c1_cash_hot_25_varpx.py",
    "adapters3/aster_r19_linkusdt_absorption_negative_funding_fixed16_fullcash_varsg.py",
    "adapters3/aster_r19_linkusdt_absorption_negative_funding_fixed16_volume1pct_varsg.py",
    "aster_sleeves/aster_abs_neg_ada_vol1pct_varsg.py",
]


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _load(name):
    return json.load(open(os.path.join(ROOT, name)))


class RosterShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = _load("config/sleeves.json")
        cls.rows = cls.cfg["sleeves"]
        cls.by_id = {}
        for r in cls.rows:
            cls.by_id.setdefault(r["id"], []).append(r)
        cls.reg = _load("config/f4_variations_20261115.json")
        cls.variations = cls.reg["variations"]

    def test_roster_count_exactly_359(self):
        # VARIATION-ROSTERING-20261115 (2026-11-15): 339 + the 19
        # rostered F4 variations = 358; amended to 359 the same day
        # by CONVERSION-VARIATION-20261115 (CONV-47 turtle2010).
        # Any other drift still fails here.
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366 (the five overnight basket sleeves rostered live).
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(self.rows), 400)
        # SSO-PORT-CONV46-20261115: roster count 359 -> 361 (sso_opus, sso_opus_notime25 rostered).
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(self.by_id), 400)

    def test_variation_ids_present_exactly_once(self):
        self.assertEqual(len(self.variations), 19)
        for v in self.variations:
            self.assertEqual(len(self.by_id.get(v["id"], [])), 1, v["id"])

    def test_variation_row_differs_from_parent_only_in_id_module(self):
        for v in self.variations:
            a = dict(self.by_id[v["parent"]][0])
            b = dict(self.by_id[v["id"]][0])
            self.assertEqual(set(a), set(b), v["id"])
            diff = {k for k in a if a[k] != b[k]}
            self.assertEqual(diff, {"id", "module"}, v["id"])
            if v["id"] == "aster_abs_neg_ada_vol1pct_varsg":
                self.assertEqual(
                    b["module"],
                    "aster_sleeves.aster_abs_neg_ada_vol1pct_varsg")
            else:
                self.assertEqual(b["module"], f"adapters3.{v['id']}")

    def test_variation_modules_import_with_matching_sleeve_id(self):
        for v in self.variations:
            row = self.by_id[v["id"]][0]
            m = importlib.import_module(row["module"])
            self.assertEqual(m.SLEEVE_ID, v["id"], v["id"])
            self.assertTrue(callable(m.evaluate), v["id"])

    def test_variation_module_files_load_with_matching_sleeve_id(self):
        import importlib.util
        self.assertEqual(len(VARIATION_MODULES), 19)
        for rel in VARIATION_MODULES:
            path = os.path.join(ROOT, rel)
            self.assertTrue(os.path.exists(path), rel)
            stem = os.path.splitext(os.path.basename(rel))[0]
            spec = importlib.util.spec_from_file_location(
                f"_varmod_{stem}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.assertEqual(mod.SLEEVE_ID, stem, rel)
            self.assertTrue(callable(mod.evaluate), rel)

    def test_registry_marks_all_rostered_with_uniform_falsifier(self):
        for v in self.variations:
            self.assertIn("rostered 2026-11-15", v["status"], v["id"])
            self.assertTrue(v["falsifier"].startswith(
                "Retire if, over its first 20 resolved forward fires"),
                v["id"])


class ParentsUntouched(unittest.TestCase):
    def test_parent_roster_rows_and_modules_byte_identical(self):
        cfg = _load("config/sleeves.json")
        rows = {r["id"]: r for r in cfg["sleeves"]}
        for pid, info in PARENT_HASHES.items():
            row = rows[pid]
            self.assertEqual(
                _sha(json.dumps(row, sort_keys=True).encode()),
                info["roster_row_sha256"], pid)
            with open(os.path.join(ROOT, info["module_path"]), "rb") as fh:
                self.assertEqual(_sha(fh.read()), info["module_sha256"], pid)

    def test_parent_engine_specs_byte_identical(self):
        from desk3.aster_b11_crypto import SPECS as B11
        from desk3.aster_batch13 import SPECS as B13
        from desk3.lazarus_q07 import SPECS as LZ
        tables = {"lazarus_q07": LZ, "aster_batch13": B13,
                  "aster_b11": B11}
        for pid, info in PARENT_HASHES.items():
            where = info.get("spec_where")
            if not where:
                continue
            spec = tables[where][pid]
            self.assertEqual(
                _sha(repr(sorted(spec.items())).encode()),
                info["spec_sha256"], pid)


class LazarusGateDrop(unittest.TestCase):
    def test_specs_differ_only_in_filters(self):
        from desk3.lazarus_q07 import SPECS
        reg = _load("config/f4_variations_20261115.json")
        n = 0
        for v in reg["variations"]:
            if v["parent"] not in SPECS or v["id"] not in SPECS:
                continue
            n += 1
            a, b = dict(SPECS[v["parent"]]), dict(SPECS[v["id"]])
            self.assertEqual(list(a["filters"]), v["parent_filters"],
                             v["id"])
            self.assertEqual(list(b["filters"]), v["variation_filters"],
                             v["id"])
            a["filters"] = b["filters"]
            self.assertEqual(a, b, v["id"])
        self.assertEqual(n, 11)


class Q07EngineGateDrop(unittest.TestCase):
    def test_adapter_specs_differ_only_in_id_and_filters(self):
        reg = _load("config/f4_variations_20261115.json")
        n = 0
        for v in reg["variations"]:
            if not v["id"].endswith("_vargd"):
                continue
            pm = importlib.import_module(f"adapters3.{v['parent']}")
            if not hasattr(pm, "SPEC") or "horizon_wk" not in pm.SPEC:
                continue
            n += 1
            vm = importlib.import_module(f"adapters3.{v['id']}")
            a, b = dict(pm.SPEC), dict(vm.SPEC)
            self.assertEqual(list(a["filters"]), v["parent_filters"],
                             v["id"])
            self.assertEqual(list(b["filters"]), v["variation_filters"],
                             v["id"])
            a["filters"] = b["filters"]
            a["id"] = b["id"]
            self.assertEqual(a, b, v["id"])
        self.assertEqual(n, 3)


def _fire(sid, ret60, atr=0.5):
    return {"sleeve_id": sid, "symbol": "AAA", "signal": "buy-cyan",
            "date": "2026-10-23", "price": 4.0, "ret60": ret60,
            "vol20": 0.1, "adv_usd": 3000000, "atr_ratio": atr}


def _tview(sid, fires):
    return {"now": CTX["now"], "tensor": {"fires": fires}, "bars": {},
            "positions": [], "extra": {}}


class TensorParamExtreme(unittest.TestCase):
    PAIRS = [("aster_tensor_c1_cash_all_25", 0.5),
             ("aster_tensor_c1_cash_hot_25", 2.0)]

    def test_specs_differ_only_in_ret60_min(self):
        from desk3.aster_batch13 import SPECS
        for pid, _atr in self.PAIRS:
            self.assertNotIn("ret60_min", SPECS[pid], pid)
            self.assertEqual(SPECS[pid + "_varpx"],
                             {**SPECS[pid], "ret60_min": 0}, pid)

    def test_ret60_floor_behavior(self):
        for pid, atr in self.PAIRS:
            vid = pid + "_varpx"
            pm = importlib.import_module(f"adapters3.{pid}")
            vm = importlib.import_module(f"adapters3.{vid}")
            self.assertEqual(
                pm.evaluate(_tview(pid, [_fire(pid, 15, atr)]),
                            dict(CTX)), [], pid)
            self.assertEqual(
                len(vm.evaluate(_tview(vid, [_fire(vid, 15, atr)]),
                                dict(CTX))), 1, vid)
            self.assertEqual(
                len(pm.evaluate(_tview(pid, [_fire(pid, 40, atr)]),
                                dict(CTX))), 1, pid)
            self.assertEqual(
                len(vm.evaluate(_tview(vid, [_fire(vid, 40, atr)]),
                                dict(CTX))), 1, vid)

    def test_enh11_membership_inherited(self):
        from desk3.aster_batch13 import ENH11_TENSOR
        for pid, _atr in self.PAIRS:
            self.assertIn(pid, ENH11_TENSOR)
            self.assertIn(pid + "_varpx", ENH11_TENSOR)


class LinkSignGateDrop(unittest.TestCase):
    P = "aster_r19_linkusdt_absorption_negative_funding_fixed16_"

    def test_specs_differ_only_in_drop_flag(self):
        from desk3.aster_b11_crypto import SPECS
        for cap in ("fullcash", "volume1pct"):
            pid, vid = self.P + cap, self.P + cap + "_varsg"
            self.assertNotIn("drop_funding_sign", SPECS[pid], pid)
            self.assertEqual(SPECS[vid],
                             {**SPECS[pid], "drop_funding_sign": True},
                             vid)

    def test_sign_gate_behavior(self):
        from desk3 import aster_b11_crypto as b11
        orig_abs, orig_stale = b11._absorption, b11._stale_blocked
        b11._absorption = lambda brs, mult=2.0: True
        b11._stale_blocked = lambda view, sid, brs, now: False
        bars = [{"t": "h0", "o": 10, "h": 10.5, "l": 9.5, "c": 10,
                 "v": 100000.0},
                {"t": "h1", "o": 10, "h": 10.5, "l": 9.5, "c": 10,
                 "v": 100000.0}]
        try:
            for cap in ("fullcash", "volume1pct"):
                pid, vid = self.P + cap, self.P + cap + "_varsg"

                def view(fund):
                    f = {} if fund is None else {"LINKUSDT": fund}
                    return {"now": CTX["now"],
                            "bars": {"LINKUSDT": bars}, "funding": f,
                            "positions": [], "extra": {},
                            "slice": {"cash_usd": 10000.0}}
                self.assertEqual(b11.evaluate(pid, view(0.5), {}), [],
                                 pid)
                self.assertEqual(len(b11.evaluate(vid, view(0.5), {})), 1,
                                 vid)
                self.assertEqual(b11.evaluate(pid, view(None), {}), [])
                self.assertEqual(b11.evaluate(vid, view(None), {}), [])
                self.assertEqual(len(b11.evaluate(pid, view(-0.5), {})), 1,
                                 pid)
                self.assertEqual(len(b11.evaluate(vid, view(-0.5), {})), 1,
                                 vid)
        finally:
            b11._absorption, b11._stale_blocked = orig_abs, orig_stale


class AdaSignGateDrop(unittest.TestCase):
    def test_variation_module_passes_drop_flag_parent_does_not(self):
        import aster_sleeves.aster_abs_neg_ada_vol1pct as parent_mod
        import aster_sleeves.aster_abs_neg_ada_vol1pct_varsg as var_mod
        calls = []

        def recorder(view, ctx, sid, family, capacity, **kw):
            calls.append(kw)
            return []
        orig_p, orig_v = parent_mod.evaluate_crypto, var_mod.evaluate_crypto
        parent_mod.evaluate_crypto = recorder
        var_mod.evaluate_crypto = recorder
        try:
            parent_mod.evaluate({}, {})
            var_mod.evaluate({}, {})
        finally:
            parent_mod.evaluate_crypto = orig_p
            var_mod.evaluate_crypto = orig_v
        self.assertEqual(calls[0].get("drop_funding_sign", False), False)
        self.assertEqual(calls[1].get("drop_funding_sign"), True)

    def test_common_default_keeps_sign_leg(self):
        from aster_sleeves._common import evaluate_crypto
        sig = inspect.signature(evaluate_crypto)
        self.assertEqual(
            sig.parameters["drop_funding_sign"].default, False)


if __name__ == "__main__":
    unittest.main()
