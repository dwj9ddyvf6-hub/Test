"""Regression blockers for the reader-copy cures (COPY class,
terminal-ui-implementation 2026-10-31; owner's Absolute 2 and
spec 14.5.5).

Old behaviours blocked:
- Any disclaimer-style copy on a reader surface (hub, pages,
  shared JS/CSS, or any string inside a page's data.json):
  the banned set below must return zero hits across all of them.
- Programming/null words leaking into reader prose: a published
  state line reading "Fragility: insufficient history (G4
  percentile None)" on Market Mood (page, data file and the
  psychology engine's live state), and drift-state prose in the
  13F Tracker / Dark Prints generators that led with the status
  token "undefined:" instead of a plain factual phrase.
- The psychology compiler emitting a null word in any state
  line it builds (compile_state run unpublished, numbers and
  lines only).

Factual state is not banned: dates, coverage and no-data states
stay, phrased plainly ("not computed: ...", "no percentile yet").
"""
import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
PSYCH = Path(__file__).resolve().parents[2] / "psychology-engine"

BANNED = [
    "not financial advice", "not investment advice",
    "for informational purposes", "for information purposes",
    "for educational purposes", "past performance",
    "do your own research", "not a recommendation",
    "disclaimer", "does not constitute", "seek professional advice",
    "no guarantee", "at your own risk", "information only",
    "should not be relied", "not intended as advice",
    "hypothetical performance",
]

NULL_LEAK = re.compile(r"percentile None\b|\(None\)|: None\b|=\s*None\b")


def _data_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _data_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _data_strings(v)
    elif isinstance(obj, str):
        yield obj


def _reader_texts():
    """(name, text) for every reader surface: HTML, shared JS/CSS,
    and every string value in every page data.json."""
    out = []
    for fp in sorted(SITE.glob("index.html")) + sorted(
            SITE.glob("*/index.html")):
        out.append((str(fp), fp.read_text(errors="ignore")))
    for name in ("visual.js", "visual.css", "shared.js", "shared.css",
                 "page_charts.js", "engine-visual.js", "tool-visual.js",
                 "live.js", "explanation.js"):
        fp = SITE / name
        if fp.exists():
            out.append((str(fp), fp.read_text(errors="ignore")))
    for fp in sorted(SITE.glob("*/data.json")):
        try:
            data = json.loads(fp.read_text())
        except Exception:
            continue
        for s in _data_strings(data):
            out.append((str(fp), s))
    return out


def test_no_disclaimer_copy_on_any_reader_surface():
    hits = []
    for name, text in _reader_texts():
        low = text.lower()
        for phrase in BANNED:
            if phrase in low:
                hits.append((name, phrase))
    assert hits == [], hits[:10]


def test_banned_set_actually_catches_a_disclaimer():
    # The sweep is only a blocker if its patterns bite.
    sample = "This page is not financial advice and is for " \
             "informational purposes only. Past performance ..."
    low = sample.lower()
    assert any(p in low for p in BANNED)


def test_no_null_word_leaks_into_reader_prose():
    hits = []
    for name, text in _reader_texts():
        for m in NULL_LEAK.finditer(text):
            ctx = text[max(0, m.start() - 40):m.end() + 20]
            if "fetch(" in ctx or "=== null" in ctx or \
                    "== null" in ctx or "!= null" in ctx or \
                    "!== null" in ctx or "|| null" in ctx:
                continue  # code comparisons, not prose
            hits.append((name, ctx))
    assert hits == [], hits[:10]


def test_drift_state_prose_is_plain_in_generators_and_data():
    for gen in ("refresh_13ftracker.py", "refresh_darkprints.py"):
        src = (SITE / gen).read_text()
        assert '"undefined:' not in src and "'undefined:" not in src, gen
        assert "not computed:" in src, gen
    for slug in ("13f-tracker", "dark-prints"):
        data = json.loads((SITE / slug / "data.json").read_text())
        for s in _data_strings(data):
            assert not s.startswith("undefined"), (slug, s[:80])


def test_market_mood_published_lines_carry_no_null_word():
    data = json.loads((SITE / "market-mood" / "data.json").read_text())
    line = (data.get("state") or {}).get("fragility_line", "")
    assert "None" not in line, line
    assert "no percentile yet" in line or "percentile" not in line, line
    page = (SITE / "market-mood" / "index.html").read_text()
    assert "percentile None" not in page
    state = json.loads((PSYCH / "live" / "state" / "2026-10-31.json")
                       .read_text())
    assert "None" not in state.get("fragility_line", "")


def test_psychology_compiler_lines_carry_no_null_word():
    sys.path.insert(0, str(PSYCH))
    import pipeline
    state = pipeline.compile_state(publish=False)
    for key in ("slow_climate_line", "fragility_line", "disagreement"):
        assert "None" not in str(state.get(key)), (key, state.get(key))
