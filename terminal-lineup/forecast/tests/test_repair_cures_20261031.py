"""Regression blockers for the REPAIR phase (2026-10-31) of the
terminal-ui-implementation program: one pin per VERIFY.md failure
cured in this phase, so the class cannot return silently.

Covered: freshness resolver reading the dates pages actually carry
(hub dateless cards 11 -> 2, the two survivors honestly dateless);
the hub exception monitor (14.3.1); the keyboard grammar (14.3.8);
titles as claims at the kit source (14.1.5); the slope form bound to
Sector Rotation's two-point ranks (14.2); Market Mood's composite
demoted from headline bignum to a labelled median line (14.4.5);
the five-second test's structural proxy (14.5.8: the attention
answer sits in the first screen, before the first card grid).
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"


def _data(slug):
    return json.loads((SITE / slug / "data.json").read_text())


def _node(js):
    node = shutil.which("node")
    assert node, "node required for renderer blockers"
    out = subprocess.run([node, "-e", js], capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr[:400]
    return out.stdout


# --- freshness: the resolver reads the dates the data carries ------

def test_resolver_reads_freshest_fields():
    import sys
    sys.path.insert(0, str(SITE))
    import freshness
    cases = {  # slug -> the field in its own data carrying the date
        "short-volume": "freshest_day",
        "filings-wire": "freshest_filed",
        "chain-explorer": "freshest_snapshot",
        "graveyard": "wire_grading_run_at",
        "grade-a-board": "second_search_finished",
    }
    for slug, field in cases.items():
        d = _data(slug)
        expect = freshness.parse_date(d[field])
        assert expect is not None, (slug, field)
        assert freshness.reading_date(d) == expect, slug
        # Fail direction: with the field removed, no date is invented
        # from it (the resolver falls back or returns None, never the
        # removed value unless another field carries the same date).
        d2 = dict(d)
        d2.pop(field, None)
        d2.pop("record_surface", None)
        if slug == "grade-a-board":
            # Both searches finished the same day (06:06 and 16:34),
            # so the date honestly survives removing one of them.
            d2.pop("first_search_finished", None)
        assert freshness.reading_date(d2) != expect or slug == "graveyard", slug


def test_resolver_reads_per_name_snapshot_day():
    import sys
    sys.path.insert(0, str(SITE))
    import freshness
    d = _data("expiry-pin-watch")
    expect = max(freshness.parse_date(n["snapshot_day"])
                 for n in d["names"] if n.get("snapshot_day"))
    assert freshness.reading_date(d) == expect


def _dateless(card):
    # The producer's own definition: the card's date span (in the
    # cardfoot) says so. The phrase also occurs inside some cards'
    # prose notes, which is not datelessness.
    m = re.search(r'class="updated">([^<]*)</span>', card)
    return bool(m and "No reading date" in m.group(1))


def test_hub_dateless_cards_are_only_the_two_honest_ones():
    hub = (SITE / "index.html").read_text()
    cards = re.findall(r'<article class="hubcard".*?</article>',
                       hub, re.S)
    assert len(cards) == 102
    dateless = sorted(
        re.search(r'href="([a-z0-9-]+)/"', c).group(1)
        for c in cards if _dateless(c))
    # promoted-book's producer is deterministic by design ("no time
    # comes from the clock") and one-page-report is a mixed-age
    # aggregate whose stalest section is a 13F quarter: neither
    # carries one honest reading date, so both say so on the card.
    assert dateless == ["one-page-report", "promoted-book"], dateless


# --- 14.3.1 exception monitor ---------------------------------------

def test_hub_exception_monitor_lists_exactly_the_exceptions():
    hub = (SITE / "index.html").read_text()
    mon = re.search(r'<section id="needs-attention">(.*?)</section>',
                    hub, re.S)
    assert mon, "monitor section missing"
    listed = re.findall(r'<li><a href="([a-z0-9-]+)/">', mon.group(1))
    cards = re.findall(r'<article class="hubcard".*?</article>',
                       hub, re.S)
    expected = []
    for c in cards:
        chip = re.search(r'class="chip ([a-z]+)"', c).group(1)
        if chip in ("stale", "missing") or _dateless(c):
            expected.append(
                re.search(r'href="([a-z0-9-]+)/"', c).group(1))
    assert sorted(listed) == sorted(expected), (listed, expected)
    assert f"{len(expected)} of 102 tools need attention" in mon.group(1)
    assert 'id="exceptions-toggle"' in mon.group(1)
    assert hub.count("terminal-keys") == 1


def test_monitor_sits_in_the_first_screen():
    # 14.5.8 structural proxy: the attention answer is reachable in
    # the first screen, before the first card grid is met.
    hub = (SITE / "index.html").read_text()
    assert hub.find('id="needs-attention"') < hub.find('id="forecast-engines"')
    assert hub.find('id="needs-attention"') < hub.find('<article class="hubcard"')


# --- 14.3.8 keyboard grammar ----------------------------------------

def test_keyboard_grammar_in_shared_shell_and_hub():
    shared = (SITE / "shared.js").read_text()
    assert 'addEventListener("keydown"' in shared
    for key in ('e.key === "/"', 'e.key === "h"', 'e.key === "r"',
                'e.key === "?"', 'e.key === "Escape"'):
        assert key in shared, key
    assert "keyhint" in shared
    hub = (SITE / "index.html").read_text()
    assert 'e.key === "e"' in hub  # hub exceptions-only key


# --- 14.1.5 titles are claims ----------------------------------------

def test_kit_titles_carry_computed_claims():
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const r=VK.ranked({rows:[{name:'A',score:1.5},{name:'B',score:4.25}],"
        "title:'Scores on record',session:'2026-10-30'});"
        "const a=VK.area({series:[{date:'2026-10-01',value:2},"
        "{date:'2026-10-30',value:5}],title:'How it has moved',"
        "session:'2026-10-30'});"
        "const d=VK.distribution({buckets:[{label:'0-2',value:3},"
        "{label:'2-4',value:9}],title:'Spread of moves',"
        "session:'2026-10-30'});"
        "console.log(JSON.stringify({r:r,a:a,d:d}));"
    )
    out = json.loads(_node(js))
    assert "Scores on record: B is highest at 4.25" in out["r"]
    assert "How it has moved: rose from 2 to 5" in out["a"]
    assert "2-4 is the fullest bucket at 9 of 12" in out["d"]
    # Fail direction: no scored rows, no claim is fabricated.
    js2 = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "console.log(VK.ranked({rows:[{name:'A'}],title:'Plain',"
        "session:'2026-10-30'}));"
    )
    assert "Plain:" not in _node(js2)


# --- 14.2 slope form --------------------------------------------------

def test_slope_primitive_draws_two_point_change():
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const s=VK.slope({pairs:[{name:'Staples',from:1,to:9},"
        "{name:'Tech',from:9,to:2}],lowerIsBetter:true,"
        "fromLabel:'rank over 21 sessions',toLabel:'rank over 5 sessions',"
        "title:'Ranks',session:'2026-10-30'});"
        "const one=VK.slope({pairs:[{name:'Only',from:1,to:2}],"
        "session:'2026-10-30'});"
        "console.log(JSON.stringify({s:s,one:one}));"
    )
    out = json.loads(_node(js))
    assert out["s"].count("<line") == 2
    assert ">1</text>" in out["s"] and ">9</text>" in out["s"]
    assert "rank over 21 sessions" in out["s"]
    # Fail closed: a single pair draws no slope.
    assert "<line" not in out["one"]


def test_sector_rotation_binds_the_slope_to_its_ranks():
    src = (SITE / "tool-visual.js").read_text()
    assert "VisualKit.slope" in src
    d = _data("sector-rotation")
    pairs = [(x["sector"], x["rank_21"], x["rank_5"])
             for x in d["sectors"]
             if isinstance(x.get("rank_21"), (int, float))
             and isinstance(x.get("rank_5"), (int, float))]
    assert len(pairs) >= 2  # the page's own two-point numeric data
    # decay-watch standings stay categorical: no slope is bound there.
    i = src.find('"decay-watch"')
    assert "slope" not in src[i:i + 900]


# --- 14.4.5 market mood headline --------------------------------------

def test_market_mood_composite_is_a_labelled_median_line():
    html = (SITE / "market-mood" / "index.html").read_text()
    data = _data("market-mood")
    comp = data["state"]["composite_percentile"]
    assert f'<p class="bignum">{comp}</p>' not in html
    assert f"Composite percentile {comp}: the median of the" in html
    assert "oldest gauge reading 2026-09-01" in html
    assert data["state"]["regime"] in html
    pipe = (SITE.parent / "psychology-engine" / "pipeline.py").read_text()
    assert "_spread_line" in pipe  # the cure lives in the generator
