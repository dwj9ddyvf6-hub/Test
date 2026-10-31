"""Regression blockers for the collapsed explanation block
(2026-10-31, final form).

The owner's rule, corrected three times: every module, engine and
tool carries a collapsed-by-default explanation, BUT there is no
heading, title or label on it, the phrase "What this is" never
appears, no canned text repeats across pages, and the collapsed
line is the page's own plain sentence stating what the thing is.

Covers: every hub page's data carries an explanation whose summary
is substantive and unique; the two pages with no data file are
covered by the renderer's own-page fallback; the renderer creates
exactly one block, closed by default, with no banned phrase; and
the banned phrase appears on zero pages anywhere on the site.
"""
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
NO_DATA = {"greeks-sketch", "payoff-sketch"}
BANNED = "What this is"


def _hub_slugs():
    hub = (SITE / "index.html").read_text()
    cards = re.findall(r'<article class="hubcard".*?</article>',
                       hub, re.S)
    slugs = []
    for card in cards:
        m = re.search(r'href="([a-z0-9-]+)/"', card)
        if m:
            slugs.append(m.group(1))
    return slugs


def test_every_hub_page_has_a_unique_substantive_explanation():
    slugs = _hub_slugs()
    assert len(slugs) == 102, len(slugs)
    summaries = {}
    for slug in slugs:
        if slug in NO_DATA:
            continue
        data = json.loads((SITE / slug / "data.json").read_text())
        block = data.get("explanation")
        assert block, f"{slug}: no explanation block"
        summary, body = block.get("summary", ""), block.get("body", "")
        assert len(summary) >= 40, f"{slug}: summary too thin"
        assert summary.endswith("."), f"{slug}: summary not a sentence"
        assert len(body) >= 60, f"{slug}: body too thin"
        assert BANNED not in summary and BANNED not in body
        assert slug not in summaries.values()
        assert summary not in summaries, f"{slug}: summary repeats"
        summaries[summary] = slug
    assert len(summaries) == 100, len(summaries)


def test_no_data_pages_covered_by_renderer_fallback():
    js = (SITE / "explanation.js").read_text()
    for slug in NO_DATA:
        assert f'"{slug}"' in js, slug
        page = (SITE / slug / "index.html").read_text()
        job = re.search(r'<p class="job">(.*?)</p>', page, re.S).group(1)
        job = re.sub(r"<[^>]+>", "", job).strip()
        assert job in js, f"{slug}: fallback is not the page's own job line"


def test_renderer_contract_one_block_closed_no_label():
    js = (SITE / "explanation.js").read_text()
    assert js.count('createElement("details")') == 1
    assert 'id = "explBlock"' in js or "explBlock" in js
    assert "setAttribute(\"open\"" not in js and ".open =" not in js
    assert BANNED not in js
    assert "What this is" not in (SITE / "explanation.py").read_text()
    shared = (SITE / "shared.js").read_text()
    assert "explanation.js" in shared


def test_banned_phrase_on_zero_pages():
    hits = []
    for path in SITE.rglob("*"):
        if path.is_file() and path.suffix in (".html", ".js", ".css",
                                              ".py", ".json"):
            if BANNED in path.read_text(errors="replace"):
                hits.append(str(path))
    assert hits == [], hits


def test_engine_bodies_carry_registry_facts():
    # Spot proof that engine bodies are built from the registry:
    # corrected-band is engine_01; its body must name its horizons
    # and its proving threshold words from forecast/registry.json.
    reg = json.loads((SITE.parent / "forecast" / "registry.json")
                     .read_text())
    entry = next(e for e in reg["engines"] if e["id"] == "engine_01")
    data = json.loads((SITE / "corrected-band" / "data.json").read_text())
    body = data["explanation"]["body"]
    assert entry["horizons"].split(";")[0] in body
    assert "120 live forecasts" in body
    assert "engine_01" not in body and "grading_rule_id" not in body
