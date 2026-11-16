"""BS-1 blockers: hash pins over the vendored Best Setups tree +
golden-diff behavioral identity vs the ORIGINAL system's outputs on
recorded matching inputs. Fail direction: any byte drift in a vendored
file, or any behavioral diff, fails this suite."""
import hashlib, json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BS = ROOT / "best_setups"
PINS = {
    "core/setups_curator.py": "a6a98dbe0bedb12d89d726f4182a3f685b13e861b3dc70c1dc20dab4e327e06c",
    "core/setup_card.py": "174541c28ea00ae4d91d50fb87626b3bd4794ed491b2216b9544aecf91863ba4",
    "core/setup_brief.py": "1796be7c60a8250ad46eb29b95b5d4b6aa486ca38d70b31a03ef761cd77fff53",
    "core/setup_call.py": "99b178105c0e5216d877f31618b28f57308a8ce4e6300cf2bb476911cc5dcc68",
    "core/setups_publish.py": "fde1c81ac9ac624977b8a0c6caea2b060af1f121528fe7681892e16a150c4e4c",
    "tools/build_setups.py": "9e7c7313dcb6d64eb4e9c20cd6112b0376f82e2ac5efb9e6e3142f12c9616f54",
    "tools/build_briefs.py": "e1eeb07e8c7898aa87e28ac47ba771a6adc98d2be6c8989875504b37a02f9868",
    "tools/build_market_charts.py": "786d725fced920a8468d362408bdcdd1018c0d3257ed0ca8eaf5b08ce07eb264",
}
GOLDEN_SHA = "0081d53af389e645a2c91ff2244464584cbd2bee6ea1d964ed8b772e3982bac1"


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TestHashPins(unittest.TestCase):
    def test_every_vendored_file_matches_pin(self):
        self.assertEqual(len(PINS), 8)
        for rel, pin in PINS.items():
            self.assertEqual(sha(BS / rel), pin, rel)

    def test_no_extra_python_in_vendored_core_tools(self):
        got = {str(p.relative_to(BS)) for d in ("core", "tools")
               for p in (BS / d).glob("*.py")}
        self.assertEqual(got, set(PINS))


class TestGoldenDiff(unittest.TestCase):
    def test_golden_output_byte_identical(self):
        golden = BS / "golden" / "golden_output.json"
        self.assertEqual(sha(golden), GOLDEN_SHA)
        r = subprocess.run([sys.executable, str(BS / "golden" / "run_golden.py"),
                            str(BS)], capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr.decode()[:400])
        self.assertEqual(r.stdout, golden.read_bytes())

    def test_golden_covers_calls_geo_and_merge(self):
        d = json.loads((BS / "golden" / "golden_output.json").read_text())
        self.assertEqual(len(d["calls"]), 11)
        self.assertEqual(len(d["geo"]), 11)
        self.assertIsNone(d.get("merged_error"))
        self.assertIn("setups", d["merged"])


class TestLaneIntegration(unittest.TestCase):
    def test_lane_produces_current_desk_terminal_keys(self):
        sys.path.insert(0, str(ROOT))
        from desk3.best_setups_lane import enrich_terminal_snapshot, TERMINAL_KEYS
        sd = json.loads((BS / "golden/inputs/setups_latest.json").read_text())
        bd = json.loads((BS / "golden/inputs/setup_briefs.json").read_text())
        out = enrich_terminal_snapshot({}, sd, bd)
        for k in TERMINAL_KEYS:
            self.assertIn(k, out)
        golden = json.loads((BS / "golden/golden_output.json").read_text())
        self.assertEqual(out, golden["merged"])


if __name__ == "__main__":
    unittest.main()
