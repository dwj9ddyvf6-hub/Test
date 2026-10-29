import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_worker", ROOT / "scripts" / "build_worker.py")
BUILD_WORKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_WORKER)


class AssetVersionTests(unittest.TestCase):
    def test_line_endings_do_not_change_asset_version_or_packaged_bytes(self):
        css = b"body {\n  color: #fff;\n}\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            linux_checkout = root / "linux"
            windows_checkout = root / "windows"
            linux_checkout.mkdir()
            windows_checkout.mkdir()
            (linux_checkout / "styles.css").write_bytes(css)
            (windows_checkout / "styles.css").write_bytes(css.replace(b"\n", b"\r\n"))
            bootstrap = b"export {};\n"
            (linux_checkout / "app-bootstrap.mjs").write_bytes(bootstrap)
            (windows_checkout / "app-bootstrap.mjs").write_bytes(bootstrap.replace(b"\n", b"\r\n"))

            html = '<link href="styles.css?v=6666c0fd" /><script src="./app-bootstrap.mjs"></script>'
            linux_html = BUILD_WORKER.version_asset_urls(html, linux_checkout)
            windows_html = BUILD_WORKER.version_asset_urls(html, windows_checkout)

            self.assertEqual(windows_html, linux_html)
            self.assertIn(hashlib.sha256(css).hexdigest()[:16], windows_html)
            self.assertEqual(BUILD_WORKER.canonical_text_bytes(windows_checkout / "styles.css"), css)

    def test_asset_versioning_requires_one_reference_per_versioned_asset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "styles.css").write_text("body {}\n", encoding="utf-8")
            (root / "app-bootstrap.mjs").write_text("export {};\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                BUILD_WORKER.version_asset_urls("<html></html>", root)


if __name__ == "__main__":
    unittest.main()

