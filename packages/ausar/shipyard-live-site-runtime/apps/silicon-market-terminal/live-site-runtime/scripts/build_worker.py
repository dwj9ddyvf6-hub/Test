#!/usr/bin/env python3
"""Embed allowlisted terminal assets and assemble the read-only Site Worker."""
from __future__ import annotations

import base64
import json
import hashlib
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TEMPLATE = ROOT / "worker" / "index.js"
MANIFEST = ROOT / ".openai" / "hosting.json"
TARGET = DIST / "server" / "index.js"
PUBLIC_ASSETS = {
    "/index.html", "/app.js", "/app-bootstrap.mjs", "/styles.css",
    "/evidence-contract.mjs", "/research-adapters.mjs", "/market-overview.mjs", "/convergence-engine.mjs", "/vendor-coverage.json", "/favicon.svg",
}


def canonical_text_bytes(path: Path) -> bytes:
    """Return Git-stable UTF-8/LF bytes for a text asset on any checkout OS."""
    return path.read_text(encoding="utf-8").encode("utf-8")


def version_app_script(source: str, dist: Path) -> str:
    pattern = re.compile(r"app\.js\?v=(?:__APP_JS_VERSION__|[a-f0-9]{16})")
    if len(pattern.findall(source)) != 1:
        raise SystemExit("Expected one versioned app.js URL in app-bootstrap.mjs.")
    digest = hashlib.sha256(canonical_text_bytes(dist / "app.js")).hexdigest()[:16]
    return pattern.sub(f"app.js?v={digest}", source, count=1)


def version_app_data_urls(source: str, dist: Path) -> str:
    name = "vendor-coverage.json"
    digest = hashlib.sha256(canonical_text_bytes(dist / name)).hexdigest()[:16]
    pattern = re.compile(
        rf"(?P<quote>['\"])(?P<path>(?:\./)?{re.escape(name)})(?:\?v=[a-f0-9]+)?(?P=quote)"
    )
    def replace(match: re.Match[str]) -> str:
        return f"{match.group('quote')}{match.group('path')}?v={digest}{match.group('quote')}"

    source, replacements = pattern.subn(replace, source)
    if replacements != 1:
        raise SystemExit(f"Expected one application reference to {name}, found {replacements}.")
    return source


def version_module_imports(source: str, dist: Path, names: tuple[str, ...], owner: str) -> str:
    for name in names:
        digest = hashlib.sha256(canonical_text_bytes(dist / name)).hexdigest()[:16]
        pattern = re.compile(
            rf"(?P<quote>['\"])(?P<path>(?:\./)?{re.escape(name)})(?:\?v=[a-f0-9]+)?(?P=quote)"
        )
        def replace(match: re.Match[str]) -> str:
            return f"{match.group('quote')}{match.group('path')}?v={digest}{match.group('quote')}"

        source, replacements = pattern.subn(replace, source)
        if replacements != 1:
            raise SystemExit(f"Expected one {owner} import of {name}, found {replacements}.")
    return source


def version_asset_urls(html: str, dist: Path) -> str:
    for name in ("styles.css", "app-bootstrap.mjs", "favicon.svg"):
        digest = hashlib.sha256(canonical_text_bytes(dist / name)).hexdigest()[:16]
        pattern = re.compile(
            rf'(?P<attribute>\b(?:href|src)=)(?P<quote>["\'])(?P<path>(?:\./)?{re.escape(name)})(?:\?v=[a-f0-9]+)?(?P=quote)'
        )
        def replace(match: re.Match[str]) -> str:
            return f"{match.group('attribute')}{match.group('quote')}{match.group('path')}?v={digest}{match.group('quote')}"

        html, replacements = pattern.subn(replace, html)
        if replacements != 1:
            raise SystemExit(f"Expected one HTML reference to {name}, found {replacements}.")
    return html


def main() -> None:
    # Content-address every browser script and static dependency so a publish
    # cannot combine code from different releases through a browser or edge cache.
    app_path = DIST / "app.js"
    app = version_app_data_urls(app_path.read_text(encoding="utf-8"), DIST)
    app_path.write_text(app, encoding="utf-8", newline="\n")

    adapters_path = DIST / "research-adapters.mjs"
    adapters = version_module_imports(
        adapters_path.read_text(encoding="utf-8"), DIST, ("evidence-contract.mjs",), "research-adapters"
    )
    adapters_path.write_text(adapters, encoding="utf-8", newline="\n")

    bootstrap_path = DIST / "app-bootstrap.mjs"
    bootstrap = version_module_imports(
        bootstrap_path.read_text(encoding="utf-8"),
        DIST,
        ("evidence-contract.mjs", "research-adapters.mjs", "market-overview.mjs", "convergence-engine.mjs"),
        "bootstrap",
    )
    bootstrap = version_app_script(bootstrap, DIST)
    bootstrap_path.write_text(bootstrap, encoding="utf-8", newline="\n")

    # HTML is revalidated; content-addressed URLs prevent mixed release assets.
    html_path = DIST / "index.html"
    html = html_path.read_text(encoding="utf-8")
    html = version_asset_urls(html, DIST)
    html_path.write_text(html, encoding="utf-8", newline="\n")
    assets: dict[str, str] = {}
    for path in sorted(DIST.rglob("*")):
        # Publish only reviewed UI and research-contract assets. Prior desk
        # snapshots, exports, and generated archives are excluded by default.
        if not path.is_file() or path == TARGET or ".openai" in path.relative_to(DIST).parts or "server" in path.relative_to(DIST).parts:
            continue
        relative = "/" + path.relative_to(DIST).as_posix()
        if relative not in PUBLIC_ASSETS:
            continue
        assets[relative] = base64.b64encode(canonical_text_bytes(path)).decode("ascii")
    required = {"/index.html", "/app.js", "/styles.css", "/app-bootstrap.mjs", "/evidence-contract.mjs", "/research-adapters.mjs", "/market-overview.mjs", "/convergence-engine.mjs", "/vendor-coverage.json"}
    if not required.issubset(assets):
        raise SystemExit("Terminal build is missing its public HTML, JS, or CSS asset.")
    template = TEMPLATE.read_text(encoding="utf-8").replace("// __TERMINAL__", (ROOT / "worker" / "terminal.js").read_text())
    template = template.replace("// __ALPACA__", (ROOT / "worker" / "alpaca.js").read_text())
    morgue_metadata = json.loads((ROOT / "worker" / "morgue-snapshot-metadata.json").read_text(encoding="utf-8"))
    morgue_adapter = (ROOT / "worker" / "morgue.js").read_text(encoding="utf-8").replace("__MORGUE_SNAPSHOT_METADATA__", json.dumps(morgue_metadata, separators=(",", ":")))
    template = template.replace("// __MORGUE__", morgue_adapter)
    template = template.replace("// __MCP__", (ROOT / "worker" / "mcp.js").read_text())
    marker = "__AUSAR_STATIC_ASSETS__"
    if template.count(marker) != 1:
        raise SystemExit("Worker template must contain exactly one static asset marker.")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(template.replace(marker, json.dumps(assets, separators=(",", ":"))), encoding="utf-8", newline="\n")
    # All Worker modules are concatenated above and use only platform APIs.
    # Keep the deployment entrypoint as plain ESM; no bundler is required.
    out_manifest = DIST / ".openai" / "hosting.json"
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    out_manifest.write_bytes(MANIFEST.read_bytes())
    migration_source = ROOT / "drizzle"
    migration_output = DIST / ".openai" / "drizzle"
    if migration_output.exists():
        shutil.rmtree(migration_output)
    if migration_source.is_dir():
        shutil.copytree(migration_source, migration_output)
    print(json.dumps({"worker": str(TARGET), "embedded_assets": len(assets), "embedded_bytes": sum(len(value) * 3 // 4 for value in assets.values())}))


if __name__ == "__main__":
    main()
