import ast
import json
import unittest
from pathlib import Path


def load_privacy_gate():
    source_path = Path(__file__).with_name("sync_to_test.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "DESK_PRIVATE_KEYS"
            for target in node.targets
        ):
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in {
            "_json_keys",
            "desk_privacy_reason",
        }:
            selected.append(node)
    namespace = {"json": json, "Path": Path}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace


class DeskPrivacySurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_privacy_gate()
        cls.private_key = sorted(cls.gate["DESK_PRIVATE_KEYS"])[0]
        cls.payload = json.dumps({"fixture_only": [{cls.private_key: "synthetic-only"}]}).encode()

    def test_denylist_does_not_shrink(self):
        self.assertGreaterEqual(len(self.gate["DESK_PRIVATE_KEYS"]), 40)

    def test_blocks_active_temporary_and_archived_json(self):
        cases = (
            ("active", "terminal-lineup/site/desk/data.json"),
            ("temporary", "terminal-lineup/site/desk/data.json.tmp"),
            ("archived", "terminal-lineup/site/.published-trees/20300102/desk/data.json"),
        )
        for label, rel in cases:
            with self.subTest(route=label):
                self.assertTrue(self.gate["desk_privacy_reason"](rel, self.payload))

    def test_malformed_temporary_json_fails_closed(self):
        reason = self.gate["desk_privacy_reason"](
            "terminal-lineup/site/desk/data.json.tmp", b"synthetic-invalid-json"
        )
        self.assertTrue(reason)

    def test_clean_safe_feed_remains_allowed(self):
        raw = json.dumps(
            {
                "schema": "PEER_BREADTH_PUBLIC_DESK_FEED_V2",
                "generated_at": "2030-01-02T03:04:05Z",
                "cycle_id": "synthetic-cycle",
            }
        ).encode()
        self.assertIsNone(
            self.gate["desk_privacy_reason"](
                "terminal-lineup/site/desk/data.json", raw
            )
        )


if __name__ == "__main__":
    unittest.main()
