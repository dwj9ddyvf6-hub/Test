"""Regression blockers for the charts-IA phase (2026-10-31).

Covers: the VisualKit INFO-MAP vocabulary renderers exist and draw to
scale; the shared nav is in the ruled order with Desk last; the hub
carries the ruled section order with truthful counts; the desk
publish copy matches its source byte for byte; Market Mood's gauges
are real SVG dials with unchanged values.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / "site"
WORKSPACE = SITE.parents[1]


def _node(expr):
    out = subprocess.run(["node", "-e", expr], capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_visualkit_vocabulary_and_scale():
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const need=['area','sparkline','fan','distribution','heatmap',"
        "'gaugeZones','timeline','countBars','donut','line','curve',"
        "'band','dial'];"
        "for (const n of need) if (typeof VK[n]!=='function') "
        "throw new Error('missing '+n);"
        "const g=VK.gaugeZones({value:50,low:0,high:100,"
        "zones:[{to:100,label:'x'}]});"
        "if (!g.includes('<svg')) throw new Error('gauge no svg');"
        "const d=VK.distribution({buckets:[{label:'a',value:0},"
        "{label:'b',value:10}]});"
        "if (!d.includes('<svg')) throw new Error('dist no svg');"
        "const dn=VK.donut({slices:[{label:'a',value:3},"
        "{label:'b',value:1}]});"
        "if (!dn.includes('75%')) throw new Error('donut share wrong');"
        "const e=VK.donut({slices:[]});"
        "if (e.includes('<svg')) throw new Error('empty donut drew');"
        "console.log('ok');"
    )
    assert "ok" in _node(js)


def test_nav_order_desk_last():
    shared = (SITE / "shared.js").read_text()
    nav = re.search(r'\[\["Forecast Engines".*?\]\]', shared, re.S)
    assert nav, "nav array not found"
    labels = re.findall(r'\["([A-Za-z ]+)", root', nav.group(0))
    assert labels == ["Forecast Engines", "Market Tools", "Modules",
                      "The Record", "Desk"], labels
    assert 'root + "desk/"' in shared


def test_hub_sections_and_counts():
    hub = (SITE / "index.html").read_text()
    order = [hub.find('id="visual-front"'),
             hub.find('id="forecast-engines"'),
             hub.find('id="ready-to-use"'),
             hub.find('id="modules"'),
             hub.find('id="the-record"'),
             hub.find('id="desk"')]
    assert all(x >= 0 for x in order), order
    assert order == sorted(order), order
    cards = re.findall(r'<article class="hubcard".*?</article>',
                       hub, re.S)
    assert len(cards) == 102
    assert len(re.findall(r'class="mini"', hub)) == 102
    assert len(re.findall(r'data-vf="', hub)) == 8
    chips = {}
    for c in re.findall(r'class="chip ([a-z]+)"', hub):
        chips[c] = chips.get(c, 0) + 1
    line = re.search(r'<p class="hubcount">([^<]*)</p>', hub).group(1)
    assert line.startswith(
        f"102 tools in the lineup: {chips.get('live', 0)} live, "
        f"{chips.get('waiting', 0)} waiting, "
        f"{chips.get('ungraded', 0)} not yet graded, "
        f"{chips.get('stale', 0)} stale"), line


DESK_WIRING = ('<link rel="stylesheet" href="../shared.css">\n'
               '<link rel="stylesheet" href="../visual.css">\n'
               '<script src="../shared.js" defer></script>\n')


def test_desk_publish_copy_matches_source():
    # The desk feed is live and moves on its own cycle, so the blocker
    # proves the producer: a fresh publish copies the feed byte for
    # byte, and the page byte for byte apart from the shared chart
    # wiring the producer adds to the published copy (desk subject
    # chart cure, 2026-10-31).
    out = subprocess.run(
        ["python3", str(SITE / "publish_desk.py")],
        capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    src = WORKSPACE / "muse-desk-v3" / "terminal"
    a = hashlib.sha256((src / "terminal_feed.json").read_bytes()).hexdigest()
    b = hashlib.sha256(
        (SITE / "desk" / "terminal_feed.json").read_bytes()).hexdigest()
    assert a == b, "terminal_feed.json"
    published = (SITE / "desk" / "index.html").read_text()
    assert DESK_WIRING in published, "chart wiring missing"
    assert published.replace(DESK_WIRING, "", 1) == \
        (src / "index.html").read_text(), "page content changed"


def _drawn_countbars(slug):
    """Render the page's counts through the real VisualKit countBars,
    exactly as page_charts.js does for its lead and record charts
    (rows from the top-level counts / live_accrual counts, positive
    values, plain names, sorted high to low)."""
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const fs=require('fs');"
        "const data=JSON.parse(fs.readFileSync("
        + json.dumps(str(SITE / slug / "data.json")) + ",'utf8'));"
        "const counts=(data.record_surface&&data.record_surface"
        ".live_accrual&&data.record_surface.live_accrual.counts)"
        "||data.counts||{};"
        "function plain(k){var s=String(k).replace(/_/g,' ');"
        "return s.charAt(0).toUpperCase()+s.slice(1);}"
        "const rows=Object.keys(counts)"
        ".filter(k=>typeof counts[k]==='number'&&counts[k]>0)"
        ".map(k=>({name:plain(k),score:counts[k]}))"
        ".sort((a,b)=>b.score-a.score);"
        "if(rows.length<2) throw new Error('too few chart rows');"
        "const html=VK.countBars({rows:rows,title:'The record, in "
        "counts'});"
        "if(!html.includes('<svg')) throw new Error('no svg drawn');"
        "if(!html.includes('<rect')) throw new Error('no bars drawn');"
        "for(const r of rows){"
        "if(!html.includes('>'+String(r.score)+'</text>')) "
        "throw new Error('value not plotted: '+r.score);}"
        "console.log('ok '+rows.length);"
    )
    return _node(js)


def test_agent_debate_record_chart_from_own_counts():
    data = json.loads((SITE / "agent-debate" / "data.json").read_text())
    expected = {}
    for fund in data["funds"]:
        sym = fund["symbol"].lower()
        expected[sym + "_readings_pointing_to_rising"] = \
            fund["count_rising"]
        expected[sym + "_readings_pointing_to_falling"] = \
            fund["count_falling"]
    assert data.get("counts") == expected, data.get("counts")
    accrual = (data.get("record_surface") or {}).get("live_accrual") or {}
    assert accrual.get("counts") == expected
    gen = (SITE / "refresh_agentdebate.py").read_text()
    assert '"counts": counts' in gen and "count_rising" in gen
    assert "ok" in _drawn_countbars("agent-debate")


def test_echo_board_record_chart_from_own_counts():
    data = json.loads((SITE / "echo-board" / "data.json").read_text())
    cov = data["coverage"]
    expected = {
        "names_covered_by_six_families": cov["six_families"],
        "names_covered_by_five_families": cov["five_families"],
        "names_covered_by_four_families": cov["four_families"],
        "names_covered_by_three_families": cov["three_families"],
        "names_covered_by_two_families": cov["two_families"],
        "names_covered_by_one_family": cov["one_family"],
        "names_covered_by_no_family": cov["no_family"],
    }
    assert data.get("counts") == expected, data.get("counts")
    accrual = (data.get("record_surface") or {}).get("live_accrual") or {}
    assert accrual.get("counts") == expected
    gen = (SITE / "refresh_echoboard.py").read_text()
    assert '"counts": chart_counts' in gen
    assert "ok" in _drawn_countbars("echo-board")


def test_second_opinion_record_chart_from_own_counts():
    data = json.loads(
        (SITE / "second-opinion" / "data.json").read_text())
    cov = data["coverage"]
    expected = {
        "names_covered_by_six_families": cov["six_families"],
        "names_covered_by_five_families": cov["five_families"],
        "names_covered_by_four_families": cov["four_families"],
        "names_covered_by_three_families": cov["three_families"],
        "names_covered_by_two_families": cov["two_families"],
        "names_covered_by_one_family": cov["one_family"],
        "names_covered_by_no_family": cov["no_family"],
    }
    assert data.get("counts") == expected, data.get("counts")
    accrual = (data.get("record_surface") or {}).get("live_accrual") or {}
    assert accrual.get("counts") == expected
    gen = (SITE / "refresh_second_opinion.py").read_text()
    assert '"names_covered_by_six_families": counts[6]' in gen
    assert "ok" in _drawn_countbars("second-opinion")


def test_market_mood_gauge_dials_values_unchanged():
    html = (SITE / "market-mood" / "index.html").read_text()
    data = json.loads((SITE / "market-mood" / "data.json").read_text())
    comp = data["state"]["composite_percentile"]
    assert html.count("Gauge reading") >= 5
    assert f'<p class="bignum">{comp}</p>' in html
    pipe = (WORKSPACE / "terminal-lineup" / "psychology-engine"
            / "pipeline.py").read_text()
    assert "def gauge_svg" in pipe


# --- Subject-chart cures, forecast engines (2026-10-31) -----------------
# One blocker per cured page. Each recomputes the expected subject
# series from the raw census fields in data.json (not from the
# subject_chart block), asserts the producer's series equals it and
# its source is not a counts dict, then renders lead and record
# through the real VisualKit and checks the plotted values.

def _subject_render(slug):
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const fs=require('fs');"
        "const data=JSON.parse(fs.readFileSync("
        + json.dumps(str(SITE / slug / "data.json")) + ",'utf8'));"
        "const sc=data.subject_chart||{};"
        "function render(c){if(!c)return '';"
        "if(c.kind==='ranked')return VK.ranked({rows:c.rows,title:c.title});"
        "if(c.kind==='curve')return VK.curve({points:c.points,title:c.title});"
        "if(c.kind==='band')return VK.band({items:c.items,title:c.title});"
        "if(c.kind==='distribution')return VK.distribution({buckets:c.buckets,title:c.title});"
        "return '';}"
        "const lead=render(sc.lead), rec=render(sc.record);"
        "console.log(JSON.stringify({lead:lead,record:rec}));"
    )
    return json.loads(_node(js))


def _fmt(v):
    return str(round(float(v) * 100) / 100).rstrip("0").rstrip(".") \
        if float(v) != int(float(v)) else str(int(float(v)))


def _check_subject(slug, lead_vals, record_vals):
    data = json.loads((SITE / slug / "data.json").read_text())
    sc = data.get("subject_chart")
    assert sc, f"{slug}: no subject_chart block"
    for slot, vals in (("lead", lead_vals), ("record", record_vals)):
        chart = sc.get(slot)
        if vals is None:
            assert chart is None, f"{slug} {slot}: expected no chart, got {chart}"
            continue
        assert chart, f"{slug} {slot}: missing chart"
        src = chart.get("source", "")
        assert "counts" not in src and "live_accrual" not in src, \
            f"{slug} {slot}: internal source {src}"
        if chart["kind"] == "ranked":
            got = [r["score"] for r in chart["rows"]]
        elif chart["kind"] == "distribution":
            got = [b["value"] for b in chart["buckets"]]
        elif chart["kind"] == "curve":
            got = [p["y"] for p in chart["points"]]
        elif chart["kind"] == "band":
            got = [(i["low"], i["high"]) for i in chart["items"]]
        assert got == vals, f"{slug} {slot}: {got} != {vals}"
    out = _subject_render(slug)
    for slot, vals in (("lead", lead_vals), ("record", record_vals)):
        if vals is None:
            assert out[slot] == "", f"{slug} {slot}: rendered a chart for None"
            continue
        html = out[slot]
        assert "<svg" in html or 'vk-ranked' in html, f"{slug} {slot}: no visual"
        chart = sc[slot]
        if chart["kind"] == "ranked":
            for v in vals:
                assert f">{_fmt(v)}</span>" in html or f">{_fmt(v)}</text>" in html \
                    or _fmt(v) in html, f"{slug} {slot}: value {v} not plotted"
        elif chart["kind"] == "band":
            for lo, hi in vals:
                assert f"{_fmt(lo)} to {_fmt(hi)}" in html, \
                    f"{slug} {slot}: band {lo}-{hi} not plotted"
        elif chart["kind"] == "distribution":
            for v in vals:
                assert _fmt(v) in html, f"{slug} {slot}: bucket {v} not plotted"
        elif chart["kind"] == "curve":
            assert f"{len(vals)} points drawn" in html, \
                f"{slug} {slot}: point count not in receipt"
    # wiring pins: lead and record both consume subject_chart
    assert "subject_chart.lead" in (SITE / "engine-visual.js").read_text()
    assert "subject_chart.record" in (SITE / "page_charts.js").read_text()
    gen = (SITE / "record_surface.py").read_text()
    assert "build_subject_chart" in gen


def _d(slug):
    return json.loads((SITE / slug / "data.json").read_text())


def test_subject_board_chart():
    d = _d("board"); names = d["groups"][0]["names"]
    buckets = {}
    for n in names:
        b = f"{int(n['score'] // 10) * 10}-{int(n['score'] // 10) * 10 + 9}"
        buckets[b] = buckets.get(b, 0) + 1
    _check_subject("board", [n["score"] for n in names[:12]],
                   [buckets[k] for k in sorted(buckets)])


def test_subject_calibration_league_chart():
    d = _d("calibration-league")
    _check_subject("calibration-league",
                   [e["error_pts"] for e in d["entrants"]
                    if e.get("error_pts") is not None],
                   [e["realised_pct"] for e in d["entrants"]
                    if e.get("realised_pct") is not None])


def test_subject_capitulation_clock_chart():
    d = _d("capitulation-clock")
    _check_subject("capitulation-clock",
                   [t["down_volume_times_line"] for t in d["today"]["triggers"][:12]],
                   [d["history"]["exhaustion_half"]["share_pct"],
                    d["history"]["return_half"]["median_points"]])


def test_subject_completion_clock_chart():
    d = _d("completion-clock")
    rec = [c["race"][-1]["up_first_pct"] for c in d["classes"] if c.get("race")]
    _check_subject("completion-clock", list(d["classes"][0]["hazard_pct"]), rec)


def test_subject_corrected_band_chart():
    d = _d("corrected-band"); n = d["live"]["names"][0]
    lead = [(b["lower"], b["upper"]) for b in n["horizons"][0]["bands"]]
    _check_subject("corrected-band", lead,
                   [c["coverage_pct"] for c in d["history"]["cells"][:12]])


def test_subject_earnings_distribution_chart():
    d = _d("earnings-distribution")
    vals = sorted(((n["exceedance"]["priced_move_pct"], n) for n in d["next"]["names"]
                   if isinstance(n.get("exceedance", {}).get("priced_move_pct"), (int, float))),
                  key=lambda t: -t[0])
    rec = [round(100 * s["hits"] / s["graded"], 2) for s in d["history"]["seasons"] if s.get("graded")]
    _check_subject("earnings-distribution", [v for v, _ in vals[:12]], rec)


def test_subject_exceedance_chart():
    d = _d("exceedance"); cells = d["history"]["cells"]
    _check_subject("exceedance", [c["realised_pct"] for c in cells[:8]],
                   [c["mean_forecast_pct"] for c in cells[:8]])


def test_subject_fear_day_triangulation_chart():
    d = _d("fear-day-triangulation")
    _check_subject("fear-day-triangulation",
                   [r["picked_mean_r"] for r in d["control_history"]["rows"]],
                   [x["spy_change_pct"] for x in d["fear_days_in_record"]["days"]])


def test_subject_gamma_earnings_trap_chart():
    d = _d("gamma-earnings-trap")
    _check_subject("gamma-earnings-trap",
                   [e["positioning_value_usd_per_1pct"] for e in d["window"]["events"][:10]],
                   [e["actual_move_pct"] for e in d["worked_example"]["events"]])


def test_subject_gap_destiny_chart():
    d = _d("gap-destiny")
    _check_subject("gap-destiny",
                   [b["index_fill_pct"] for b in d["history"]["bands"]],
                   [b["fill_pct"] for b in d["history"]["by_band_weekday_all"]
                    if b["weekday"] == "Mon"])


def test_subject_half_life_clock_chart():
    d = _d("half-life-clock")
    def sh(p, k):
        t = (p["confirmed"] or 0) + (p["not_replicated"] or 0)
        return round(100 * p[k] / t, 2) if t else None
    pairs = [p for p in d["pair_table"][:10]
             if (p["confirmed"] or 0) + (p["not_replicated"] or 0)]
    _check_subject("half-life-clock", [sh(p, "confirmed") for p in pairs],
                   [sh(p, "not_replicated") for p in pairs])


def test_subject_honest_pop_chart():
    d = _d("honest-pop")
    _check_subject("honest-pop",
                   [r["p_pct"] for r in d["surfaces"][0]["rows"]],
                   [r["p_pct"] for r in d["surfaces"][1]["rows"]])


def test_subject_idio_liquidity_chart():
    d = _d("idio-liquidity")
    _check_subject("idio-liquidity",
                   [n["own_move_pct"] for n in d["today"]["neither"][:12]],
                   [d["history"]["persist"]["median_points"],
                    d["history"]["reverse"]["median_points"]])


def test_subject_in_regime_oracle_chart():
    _check_subject("in-regime-oracle", None, None)


def test_subject_insider_divergence_chart():
    d = _d("insider-divergence"); elig = d["insider_legs"]["arm_b_eligible"]
    _check_subject("insider-divergence", [e["sells"] for e in elig[:12]],
                   [e["buys"] for e in elig[:12]])


def test_subject_intake_bias_chart():
    d = _d("intake-bias"); last = d["history"]["sessions"][-1]
    _check_subject("intake-bias", [n["gap"] for n in d["today"]["names"]],
                   [n["gap"] for n in last["names"]])


def test_subject_living_router_chart():
    _check_subject("living-router", None, None)


def test_subject_mortality_curve_chart():
    d = _d("mortality-curve")
    _check_subject("mortality-curve",
                   [r["fail_chance_pct"] for r in d["event_arm"]["ranked"][:10]],
                   [v["realised"] for v in d["backcast"]["classes"].values()])


def test_subject_own_norm_depth_chart():
    d = _d("own-norm-depth"); bins = d["curve"]["bins"]
    _check_subject("own-norm-depth",
                   [b["median_excess_points"] for b in bins],
                   [round(100 * b["p"], 2) for b in bins])


def test_subject_pin_or_escape_chart():
    d = _d("pin-or-escape"); funds = d["readings"]["funds"]
    _check_subject("pin-or-escape", [f["net_pull_billions"] for f in funds],
                   [round(f["next_expiry_pull_usd"] / 1e6, 2) for f in funds])


def test_subject_record_chart():
    d = _d("record"); coh = d["board"]["cohort"]; rows = []
    for hz in ("1d", "5d", "21d"):
        c = coh.get(hz) or {}
        if c.get("graded_count"):
            rows.append(round(100 * c["rose_count"] / c["graded_count"], 2))
    _check_subject("record", rows,
                   [c["score"] for c in d["board"]["groups"][0]["calls"][:12]])


def test_subject_self_analogue_chart():
    d = _d("self-analogue"); fc = d["live"]["forecasts"]
    top = sorted(fc, key=lambda f: -abs(f.get("middle_percent") or 0))[:12]
    _check_subject("self-analogue", [f["middle_percent"] for f in top],
                   [(f["low_percent"], f["high_percent"]) for f in top[:8]])


def test_subject_silent_accumulation_chart():
    d = _d("silent-accumulation"); ctx = d["readings"]["dark"]["combined_context"]
    _check_subject("silent-accumulation", [f["pct"] for f in ctx["funds"]],
                   [h["index_pct"] for h in ctx["history"]])


def test_subject_sponsored_reset_chart():
    d = _d("sponsored-reset")
    vals = [x["spy_change_pct"] for x in d["history"]["days"]]
    _check_subject("sponsored-reset", vals, vals)


def test_subject_streak_trap_chart():
    d = _d("streak-trap")
    _check_subject("streak-trap", [t["centre_pct"] for t in d["triggers"]],
                   [t["base_pct"] for t in d["triggers"]])


def test_subject_stress_reversal_chart():
    d = _d("stress-reversal"); h = d["history"]; med = h["stage_3_medians_pct"]
    _check_subject("stress-reversal",
                   [h["stage_1"]["rate_pct"], h["stage_2"]["rate_pct"]],
                   [med["plus_1"], med["plus_3"], med["plus_5"]])


def test_subject_touch_surface_chart():
    d = _d("touch-surface"); cells = d["live"]["names"][0]["cells"]
    seen, lead = set(), []
    for c in cells:
        k = (c["label"], c["side"])
        if k in seen:
            continue
        seen.add(k); lead.append(c["p_pct"])
    _check_subject("touch-surface", lead[:10],
                   [c["realised_pct"] for c in d["history"]["cells"][:10]])


def test_subject_vol_clock_chart():
    d = _d("vol-clock"); names = d["live"]["names"]
    _check_subject("vol-clock", [n["median_sessions"] for n in names[:12]],
                   [n["movement_pct"] for n in names[:12]])


def test_subject_vol_term_shape_chart():
    d = _d("vol-term-shape"); cells = d["history"]["cells"]
    lead = [c["coverage_pct"] for c in cells
            if c["symbol"] == "SPY" and c["horizon"] == 5]
    _check_subject("vol-term-shape", lead,
                   [c["coverage_pct"] for c in cells[:12]])


def test_subject_wall_lifetime_chart():
    d = _d("wall-lifetime"); agg = {}
    for e in d["history"]["episodes"]:
        k = f"{e['name']} {e['level']}"
        a = agg.setdefault(k, [0, 0]); a[1] += 1
        if e.get("touched_1"):
            a[0] += 1
    _check_subject("wall-lifetime",
                   [n["expected_move_price"] for n in d["live"]["names"]],
                   [round(100 * v[0] / v[1], 2) for _, v in sorted(agg.items()) if v[1]])


# ---------------------------------------------------------------------------
# Stated-information cure, MARKET TOOL batch (2026-10-31). One blocker per
# market-tool page: (a) the page's record chart series (record_surface
# .subject_charts, produced by record_surface.py at lane close) is the
# SUBJECT series named in the census, not internal counts; (b) the plotted
# values equal the subject values recomputed here from data.json's own
# subject fields. Lead-cured pages also pin the tool-visual.js adapter
# source: the internal-count form is gone and the subject field is read.
# ---------------------------------------------------------------------------

TOOL_SLUGS = """13f-tracker activity-profile alert-tape breakout-scanner
chain-explorer correlation-web dark-prints decay-watch earnings-calendar
earnings-drift echo-lens expected-move expiry-pin-watch fear-day
fear-day-forecaster filings-wire flow-board flow-engine flow-tape gap-fill
golden-sweep-wire grade-a-board grade-my-call graveyard holly-ideas
horizon-grades insider-wire iv-weather momentum-clock morning-map
odds-cards one-page-report portfolio-builder promoted-book proving-ground
pullback-norm receipts regime-dial replication-wire reversal-wire router
sector-rotation short-volume signal-feed skew-lens smart-money-tracker
squeeze-watch state-analogue static-gex strat-combos strat-scanner
survivors-wire unusual-volume wall-check week-ahead
watchlist-pulse""".split()


def _fmt(v):
    r = round(float(v) * 100) / 100
    if r == int(r) and abs(r) < 1e15:
        return str(int(r))
    return repr(r)


def _charts(slug):
    data = json.loads((SITE / slug / "data.json").read_text())
    rs = data.get("record_surface") or {}
    assert "subject_charts" in rs, \
        f"{slug}: no subject_charts block (record visual not cured)"
    return data, rs["subject_charts"]


def _rows_by_name(charts):
    out = {}
    for c in charts:
        for r in c.get("rows") or []:
            if isinstance(r.get("score"), (int, float)):
                out[r["name"]] = r["score"]
    return out


def _items_by_label(charts):
    out = {}
    for c in charts:
        for i in c.get("items") or []:
            if isinstance(i.get("value"), (int, float)):
                out[i["label"]] = i["value"]
    return out


def _series_values(charts):
    out = []
    for c in charts:
        for p in c.get("series") or []:
            out.append(p["value"])
    return out


def _grid_pairs(charts):
    out = set()
    for c in charts:
        for r in c.get("rows") or []:
            if r.get("status") is not None:
                out.add((r["name"], r["status"]))
    return out


def _expected_ranked(slug, d):
    """Subject values recomputed from the census-named fields."""
    n = _num = lambda v: v if isinstance(v, (int, float)) else None  # noqa
    if slug == "13f-tracker" or slug == "smart-money-tracker":
        out = {}
        for h in d["holders"]:
            prior = (h.get("change") or {}).get("prior_total_value") \
                or h.get("prior_total_value")
            if prior:
                out[h["holder"]] = round(
                    1000 * (h["total_value"] / prior - 1)) / 10
        return out
    if slug == "activity-profile":
        return {x["session"]: x["total_premium_usd"] for x in d["sessions"]}
    if slug in ("alert-tape", "flow-tape"):
        alerts = list(d.get("alerts") or [])
        for g in d.get("groups") or []:
            for a in g.get("alerts") or []:
                a = dict(a)
                a.setdefault("session", g.get("session"))
                alerts.append(a)
        out = {}
        for a in alerts:
            out[a["session"]] = out.get(a["session"], 0) + a["premium_usd"]
        return out
    if slug == "breakout-scanner":
        out = {}
        for sym, e in d["bars"].items():
            closes = [c for c in e[1] if isinstance(c, (int, float))]
            if len(closes) >= 10:
                hi = max(closes[-(d.get("high_window") or 252):])
                out[sym] = round(100 * closes[-1] / hi * 10) / 10
        return out
    if slug == "chain-explorer":
        out = {}
        u = d["underlyings"][0]
        for snap in u["snapshots"][-2:]:
            by = {}
            for ex in snap["expiries"]:
                for st in ex["strikes"]:
                    oi = sum((st[s] or {}).get("oi") or 0
                             for s in ("call", "put"))
                    if oi > 0:
                        by[st["strike"]] = by.get(st["strike"], 0) + oi
            for k, v in by.items():
                out[f"Strike {k}"] = v
        return out
    if slug == "correlation-web":
        return {f"{s} with {t[0]['symbol']}": t[0]["correlation"]
                for s, t in d["twins"].items() if t}
    if slug == "earnings-calendar":
        # Wave 2 cure: the record chart plots realised moves for
        # names whose report date has passed, never expected moves
        # for names that have not reported.
        return {f"{r['symbol']} {r['report_date']}":
                r["realised_move_pct"]
                for r in d.get("realised_moves") or []}
    if slug == "earnings-drift":
        # Wave 2 cure: per-event rows, one per earnings event.
        return {f"{r['symbol']} {r['report_date']}": r["drift_pct"]
                for r in d.get("event_rows") or []}
    if slug == "expiry-pin-watch":
        out = {}
        for nm in d["names"][:2]:
            for e in nm["expiries"]:
                out[f"{nm['symbol']} expiring {e['expiry']}"] = e["total_oi"]
        return out
    if slug == "fear-day":
        return {q["date"]: q["fear_gauge_change_pct"]
                for q in d["qualifying_days"]}
    if slug == "fear-day-forecaster":
        return {q["date"]: q["fear_gauge_change_pct"]
                for q in d["local_record"]["qualifying_days"]}
    if slug == "flow-board":
        out = {}
        for row in d["rows"][:2]:
            for cell in row["cells"]:
                out[f"{row['underlying']} calls {cell['session']}"] = \
                    cell["call_net_premium_usd"]
                out[f"{row['underlying']} puts {cell['session']}"] = \
                    cell["put_net_premium_usd"]
        return out
    if slug == "flow-engine":
        return {f"{e['underlying']} {e['contract_code']}": e["premium_usd"]
                for e in d["examples"]}
    if slug == "gap-fill":
        return {b["label"]: round(b["frequency"] * 1000) / 10
                for b in d["by_band"] if b.get("frequency") is not None}
    if slug == "golden-sweep-wire":
        return {p["contract_code"]: p["premium_usd"] for p in d["prints"]}
    if slug == "grade-a-board":
        return {(g["title"] or "")[:44]: g["cells"][0]["net_second"]
                for g in d["groups"] if g.get("cells")}
    if slug == "holly-ideas":
        return {i["symbol"]: i["score"] for i in d["ideas"][:12]}
    if slug == "horizon-grades":
        out = {}
        for h in d["horizons"]:
            for g in h["groups"]:
                if g.get("state") == "graded" and g.get("graded_count"):
                    out[f"{h['days']} day, {g['session']}"] = round(
                        100 * g["rose_count"] / g["graded_count"] * 10) / 10
        return out
    if slug == "insider-wire":
        out = {}
        for nm in d["names"]:
            s = nm.get("summary") or {}
            b = (s.get("buys") or {}).get("value_usd")
            se = (s.get("sells") or {}).get("value_usd")
            if b is not None and se is not None:
                out[nm["symbol"]] = round(b - se)
        return out
    if slug == "momentum-clock":
        out = {}
        for sym, e in d["bars"].items():
            closes = [c for c in e[1] if isinstance(c, (int, float))]
            if len(closes) > 21 and closes[-22]:
                out[sym] = round(1000 * (closes[-1] / closes[-22] - 1)) / 10
        return out
    if slug == "odds-cards":
        out = {}
        for f in d["families"]:
            for sec in (f.get("days") or []) + (f.get("regimes") or []):
                r = sec.get("rate")
                if isinstance(r, (int, float)):
                    out[f"{f['name']}: {sec.get('label')}"] = \
                        round(r * 1000) / 10 if r <= 1 else r
        return out
    if slug == "portfolio-builder":
        return {s["sector"]: s["share_pct"] for s in d["sector_mix"]}
    if slug == "promoted-book":
        out = {}
        for st in d["standings"]:
            for g in st["groups"]:
                for e in g["entries"]:
                    w = (e.get("windows") or [{}])[0]
                    if isinstance(w.get("gap_points"), (int, float)):
                        out[f"Grade {e['grade']} entry, "
                            f"{e['days_ahead']} days ahead"] = w["gap_points"]
        return out
    if slug == "pullback-norm":
        return {k.replace("_", " "): v["fwd20_mean_rel_pct"]
                for k, v in
                d["distribution"]["events_by_bucket"].items()
                if isinstance(v.get("fwd20_mean_rel_pct"), (int, float))}
    if slug == "sector-rotation":
        return {s["sector"]: s["avg_change_21_pct"] for s in d["sectors"]}
    if slug == "skew-lens":
        figs = d.get("modelled_figures") or d.get("figures") or []
        fresh = max((f.get("date") or "") for f in figs)
        out = {}
        for f in figs:
            if (f.get("date") or "") == fresh:
                out[f"{f['symbol']} put strike {f['put_strike']}"] = \
                    f["put_percent"]
                out[f"{f['symbol']} call strike {f['call_strike']}"] = \
                    f["call_percent"]
        return out
    if slug == "squeeze-watch":
        return {n["symbol"]: n["si_pct_of_float"] for n in d["names"]}
    if slug == "static-gex":
        f = d["funds"][0]
        return {f"Strike {x['strike']}": x["net_gex"]
                for x in f["strongest"]}
    raise KeyError(slug)


_RANKED_SLUGS = """13f-tracker activity-profile alert-tape breakout-scanner
chain-explorer correlation-web earnings-calendar earnings-drift expiry-pin-watch fear-day
fear-day-forecaster flow-board flow-engine flow-tape gap-fill
golden-sweep-wire grade-a-board holly-ideas horizon-grades insider-wire
momentum-clock odds-cards portfolio-builder promoted-book pullback-norm
sector-rotation skew-lens smart-money-tracker squeeze-watch
static-gex""".split()

_TILES_SLUGS = {
    "decay-watch": lambda d: {
        "Promoted, " + d["gradings"][-1]["date"]:
            round(100 * d["gradings"][-1]["promoted"]
                  / d["gradings"][-1]["total"] * 10) / 10,
        "On probation, " + d["gradings"][-1]["date"]:
            round(100 * d["gradings"][-1]["probation"]
                  / d["gradings"][-1]["total"] * 10) / 10},
    "iv-weather": lambda d: {
        n["symbol"]: n["iv_percent"]
        for g in d["groups"] for n in g["names"]
        if isinstance(n.get("iv_percent"), (int, float))},
    "state-analogue": lambda d: {
        r["name"]: d["today"]["values"][i]
        for i, r in enumerate(d["readings"])
        if i < len(d["today"]["values"])
        and isinstance(d["today"]["values"][i], (int, float))},
    "survivors-wire": lambda d: {
        k: v for r in d["per_record"] if r.get("tested")
        for k, v in
        [(f"{r['name']}: standing",
          round(100 * r["standing"] / r["tested"] * 10) / 10),
         (f"{r['name']}: partly standing",
          round(100 * r["partly"] / r["tested"] * 10) / 10)]},
    "unusual-volume": lambda d: {n["symbol"]: n["multiple"]
                                 for n in d["names"]},
    "watchlist-pulse": lambda d: {n["symbol"]: n["families_speaking"]
                                  for n in d["names"]},
}

_LINE_SLUGS = {
    "dark-prints": lambda d: [h["index_pct"] for h in d["history"]],
    "expected-move": lambda d: [
        round((c["upper"] - c["lower"]) * 100) / 100
        for n in d["names"][:1] for c in n["funded_curve"]],
    "filings-wire": lambda d: [
        r["value"] for c in d["companies"][:2]
        for f in c["figures"][:1] for r in f["readings"]],
    "grade-my-call": lambda d: [
        v for v in d["prices"]["SPY"][1]][-260:],
    "short-volume": lambda d: [
        x["short_share_pct"] for t in d["tickers"][:2] for x in t["days"]],
}

_GRID_SLUGS = {
    "echo-lens": lambda d: {(r["symbol"], r["verdict"])
                            for r in d["readings"][:24]},
    "graveyard": lambda d: {
        *((b["maker"][:44], b["verdict_words"]) for b in d["buried"][:8]),
        *((c["maker"][:44], c["verdict_words"] or "Held up")
          for c in (d["not_buried"].get("held") or [])[:4])},
    "proving-ground": lambda d: {(t["name"], t["state_words"])
                                 for t in d["tools"][:24]},
    "receipts": lambda d: {(r["tool"], r["grade"])
                           for r in d["receipts"][:24]},
    "regime-dial": lambda d: {(f"{h['session']}: {h['kind']}", h["kind"])
                              for h in d["reading_history"]},
    "replication-wire": lambda d: {(c["maker"][:44], c["verdict_words"])
                                   for c in d["claims"][:16]},
    "reversal-wire": lambda d: {(e["symbol"], e["label"])
                                for e in d["sessions"][0]["entries"][:24]},
    "router": lambda d: {(a["name"], "Avoid")
                         for a in
                         d["session_record"][0].get("avoid_names") or []},
    "strat-combos": lambda d: {
        (sym, max(d["groups"], key=lambda g: g.get("count") or 0)["name"])
        for sym in max(d["groups"],
                       key=lambda g: g.get("count") or 0)["names"][:24]},
    "strat-scanner": lambda d: {
        (n["symbol"], n.get("label") or g["name"])
        for g in d["groups"] for n in g["names"][:6] if isinstance(n, dict)},
    "wall-check": lambda d: {
        (f"{t['name']} {t['session']}",
         f"upper {t['upper_outcome']}, lower {t['lower_outcome']}")
        for s in d["sessions"] for t in s["tests"]},
}

_TAPE_SLUGS = ("signal-feed", "week-ahead")

_INTERNAL_TITLES = ("in counts", "by part", "on file, by gauge",
                    "sessions recorded", "names checked", "coverage")


def _check_page(slug):
    data, charts = _charts(slug)
    for c in charts:
        low = (c.get("title") or "").lower()
        for bad in _INTERNAL_TITLES:
            assert bad not in low, f"{slug}: internal title {c.get('title')}"
    counts = data.get("counts") or {}
    if slug == "promoted-book":
        # Entry names repeat (grade + horizon); compare as a multiset
        # of the 14 biggest-by-size charted rows.
        got_list = sorted((r["name"], r["score"]) for c in charts
                          for r in c.get("rows") or [])
        all_exp = [(f"Grade {e['grade']} entry, "
                    f"{e['days_ahead']} days ahead",
                    (e.get("windows") or [{}])[0]["gap_points"])
                   for st in data["standings"] for g in st["groups"]
                   for e in g["entries"]
                   if isinstance((e.get("windows") or [{}])[0]
                                 .get("gap_points"), (int, float))]
        all_exp.sort(key=lambda kv: -abs(kv[1]))
        assert got_list == sorted(all_exp[:14]), slug
        return
    if slug in _RANKED_SLUGS:
        got = _rows_by_name(charts)
        exp = _expected_ranked(slug, data)
        assert got, f"{slug}: no ranked subject rows charted"
        for name, val in got.items():
            assert name in exp and exp[name] == val, \
                f"{slug}: plotted {name}={val}, data says {exp.get(name)}"
        # Not the counts dict: no charted row may be a counts tally row.
        for k, v in counts.items():
            plain_k = k.replace("_", " ")
            assert not any(g.lower() == plain_k and gv == v
                           for g, gv in got.items()), \
                f"{slug}: charted row is the counts tally {k}"
    elif slug in _TILES_SLUGS:
        if slug == "iv-weather":
            # One name can carry a reading in several groups (different
            # expiries); compare the plotted tiles as a multiset.
            got_list = sorted((i["label"], i["value"]) for c in charts
                              for i in c.get("items") or [])
            exp_list = sorted([
                (n["symbol"], n["iv_percent"])
                for g in data["groups"] for n in g["names"]
                if isinstance(n.get("iv_percent"), (int, float))][:24])
            assert got_list == exp_list, slug
            return
        got = _items_by_label(charts)
        exp = _TILES_SLUGS[slug](data)
        assert got, f"{slug}: no subject tiles charted"
        for label, val in got.items():
            assert exp.get(label) == val, \
                f"{slug}: plotted {label}={val}, data says {exp.get(label)}"
    elif slug in _LINE_SLUGS:
        got = _series_values(charts)
        exp = _LINE_SLUGS[slug](data)
        assert got == exp, f"{slug}: line series differs from data fields"
    elif slug in _GRID_SLUGS:
        got = _grid_pairs(charts)
        exp = _GRID_SLUGS[slug](data)
        assert got and got <= exp, \
            f"{slug}: grid rows are not the page's own subject rows"
    elif slug in _TAPE_SLUGS:
        events = [e for c in charts for e in c.get("events") or []]
        assert events, f"{slug}: no tape events charted"
        src = data["entries"] if slug == "signal-feed" else data["events"]
        names = {e.get("name") for e in src}
        assert all(e["label"] in names for e in events), slug
    elif slug == "one-page-report":
        got = _items_by_label(charts)
        rec = data["names"][data["default_name"]]
        assert got.get(f"{data['default_name']} board score, out of 100") \
            == rec["scored"]["score"], slug
    elif slug == "morning-map":
        # Wave 3 cure (2026-10-31): past maps were not kept, so the
        # record chart is the current session's own levels ladder,
        # labelled as the session on record; values recomputed here
        # from the page's indexes block.
        bands = [c for c in charts if c.get("kind") == "band"]
        assert bands, "morning-map: no levels ladder charted"
        items = {i["label"]: i for i in bands[0].get("items") or []}
        assert items, "morning-map: ladder carries no index items"
        for ix in data["indexes"]:
            it = items.get(ix["symbol"])
            assert it is not None, \
                f"morning-map: {ix['symbol']} missing from the ladder"
            assert it["low"] == (ix.get("put_wall") or {}).get("value"), \
                f"morning-map: {ix['symbol']} put wall differs"
            assert it["high"] == (ix.get("call_wall") or {}).get("value"), \
                f"morning-map: {ix['symbol']} call wall differs"
            assert it["mid"] == (ix.get("flip") or {}).get("value"), \
                f"morning-map: {ix['symbol']} flip differs"
            assert it["current"] == ix.get("spot"), \
                f"morning-map: {ix['symbol']} spot differs"
    else:  # pragma: no cover
        raise AssertionError(f"no blocker spec for {slug}")


def _render_check(slug):
    """The real VisualKit draws the subject values: every ranked/tiles
    value in subject_charts appears as plotted text in the HTML."""
    data, charts = _charts(slug)
    js = (
        "const VK=require(" + json.dumps(str(SITE / "visual.js")) + ");"
        "const charts=" + json.dumps(charts) + ";"
        "let html='';"
        "for (const c of charts) {"
        " if (c.kind==='ranked') html+=VK.ranked({rows:c.rows,"
        "title:c.title,label:c.label});"
        " else if (c.kind==='tiles') html+=VK.tiles({items:c.items,"
        "title:c.title,label:c.label});"
        " else if (c.kind==='line') html+=VK.line({series:c.series,"
        "title:c.title,label:c.label});"
        " else if (c.kind==='band') html+=VK.band({items:c.items,"
        "title:c.title,label:c.label});"
        " else if (c.kind==='tape') html+=VK.tape({events:c.events,"
        "title:c.title,label:c.label});"
        "}"
        "console.log(html);"
    )
    out = _node(js)
    assert "vk-statewords" not in out or charts == [], \
        f"{slug}: renderer fell back to a state card"
    for c in charts:
        for r in c.get("rows") or []:
            if isinstance(r.get("score"), (int, float)):
                assert ">" + _fmt(r["score"]) + "</span>" in out, \
                    f"{slug}: value {r['score']} not plotted"
        for i in c.get("items") or []:
            if isinstance(i.get("value"), (int, float)):
                assert ">" + _fmt(i["value"]) + "</span>" in out, \
                    f"{slug}: tile value {i['value']} not plotted"


for _slug in TOOL_SLUGS:
    def _make(slug=_slug):
        def _test():
            _check_page(slug)
            _render_check(slug)
        return _test
    globals()[f"test_subject_record_{_slug.replace('-', '_')}"] = _make()


_LEAD_FORBIDDEN = {
    "alert-tape": ["hourStrip(d.alerts"],
    "decay-watch": ["current_counts", "in counts"],
    "earnings-calendar": ["groupCounts(d.names", 'mode: "calendar"'],
    "earnings-drift": ["Rose after reporting"],
    "echo-lens": ["groupCounts(d.readings"],
    "fear-day-forecaster": ["fear_gauge_readings", "Sessions checked"],
    "flow-engine": ["hourStrip(d.examples"],
    "flow-tape": ["hourStrip(all"],
    "golden-sweep-wire": ["prints_looked_at"],
    "grade-a-board": ["first_search.verdicts"],
    "graveyard": ['mode: "timeline"'],
    "horizon-grades": ["score: h.graded_count"],
    "one-page-report": ["coverage_distribution"],
    "promoted-book": ["score: g.count"],
    "proving-ground": ["groupCounts(d.tools"],
    "receipts": ['mode: "timeline"'],
    "replication-wire": ["groupCounts(d.claims"],
    "reversal-wire": ["groupCounts(entries"],
    "router": ["Names checked"],
    "signal-feed": ["groupCounts(d.entries"],
    "state-analogue": ["sessions_recorded"],
    "strat-combos": ["score: g.count"],
    "strat-scanner": ["score: g.count"],
    "survivors-wire": ["score: r.tested"],
    "week-ahead": ["groupCounts(d.events", 'mode: "calendar"'],
}
_LEAD_REQUIRED = {
    "alert-tape": "premium_usd", "decay-watch": "gradings",
    "earnings-calendar": "expected_move", "earnings-drift": "share_positive",
    "echo-lens": "d.readings", "fear-day-forecaster": "d.study",
    "flow-engine": "d.examples", "flow-tape": "premium_usd",
    "golden-sweep-wire": "d.prints", "grade-a-board": "d.groups",
    "graveyard": "d.buried", "horizon-grades": "average_pct",
    "one-page-report": "default_name", "promoted-book": "windows",
    "proving-ground": "d.tools", "receipts": "d.receipts",
    "replication-wire": "d.claims", "reversal-wire": "entries",
    "router": "avoid_names", "signal-feed": "d.entries",
    "state-analogue": "d.readings", "strat-combos": "g.names",
    "strat-scanner": "g.names", "survivors-wire": "per_record",
    "week-ahead": "d.events",
}


def _adapter_segment(src, slug):
    m = re.search(r'"' + re.escape(slug) + r'": function \(d, s\) \{'
                  r'(.*?)\n    \},', src, re.S)
    assert m, f"adapter not found for {slug}"
    return m.group(1)


for _slug in _LEAD_FORBIDDEN:
    def _make_lead(slug=_slug):
        def _test():
            src = (SITE / "tool-visual.js").read_text()
            seg = _adapter_segment(src, slug)
            for bad in _LEAD_FORBIDDEN[slug]:
                assert bad not in seg, \
                    f"{slug}: internal lead form still present: {bad}"
            assert _LEAD_REQUIRED[slug] in seg, \
                f"{slug}: subject field {_LEAD_REQUIRED[slug]} not read"
        return _test
    globals()[f"test_subject_lead_{_slug.replace('-', '_')}"] = _make_lead()


# --- Subject-chart cures, modules + record pages (2026-10-31) ----------
# One blocker per cured page. Each recomputes the expected subject
# series from the raw census fields in data.json (not from the
# subject_chart block), asserts the producer's series equals it and
# its source is not a counts dict, then renders lead and record
# through the real VisualKit and checks the plotted values. Wiring
# pin for this batch is page_charts.js (the generic lead path),
# not engine-visual.js.

def _check_module_subject(slug, lead_vals, record_vals):
    data = json.loads((SITE / slug / "data.json").read_text())
    sc = data.get("subject_chart")
    assert sc, f"{slug}: no subject_chart block"
    for slot, vals in (("lead", lead_vals), ("record", record_vals)):
        chart = sc.get(slot)
        if vals is None:
            assert chart is None, f"{slug} {slot}: expected no chart, got {chart}"
            continue
        assert chart, f"{slug} {slot}: missing chart"
        src = chart.get("source", "")
        assert "counts" not in src and "live_accrual" not in src, \
            f"{slug} {slot}: internal source {src}"
        if chart["kind"] == "ranked":
            got = [r["score"] for r in chart["rows"]]
        elif chart["kind"] == "distribution":
            got = [b["value"] for b in chart["buckets"]]
        elif chart["kind"] == "curve":
            got = [p["y"] for p in chart["points"]]
        elif chart["kind"] == "band":
            got = [(i["low"], i["high"]) for i in chart["items"]]
        assert got == vals, f"{slug} {slot}: {got} != {vals}"
    out = _subject_render(slug)
    for slot, vals in (("lead", lead_vals), ("record", record_vals)):
        if vals is None:
            assert out[slot] == "", f"{slug} {slot}: rendered a chart for None"
            continue
        html = out[slot]
        assert "<svg" in html or "vk-ranked" in html, f"{slug} {slot}: no visual"
        chart = sc[slot]
        if chart["kind"] == "ranked":
            for v in vals:
                assert _fmt(v) in html, f"{slug} {slot}: value {v} not plotted"
        elif chart["kind"] == "distribution":
            for v in vals:
                assert _fmt(v) in html, f"{slug} {slot}: bucket {v} not plotted"
        elif chart["kind"] == "curve":
            assert f"{len(vals)} points drawn" in html, \
                f"{slug} {slot}: point count not in receipt"
    pc = (SITE / "page_charts.js").read_text()
    assert "subject_chart.lead" in pc and "subject_chart.record" in pc
    gen = (SITE / "record_surface.py").read_text()
    assert "build_subject_chart" in gen


def test_subject_agent_debate_chart():
    d = _d("agent-debate")
    vals = [f["count_rising"] - f["count_falling"] for f in d["funds"]]
    _check_module_subject("agent-debate", vals, vals)


def test_subject_echo_board_chart():
    d = _d("echo-board")
    vals = [n["families_speaking"] for n in d["names"]]
    _check_module_subject("echo-board", vals, vals)


def test_subject_second_opinion_chart():
    d = _d("second-opinion")
    lead = sorted((n["families_speaking"] for n in d["names"]),
                  reverse=True)[:12]
    rec = [n["families_speaking"] for n in d["names"]
           if n["symbol"] in d["index_funds"]]
    _check_module_subject("second-opinion", lead, rec)


def test_subject_screener_chart():
    d = _d("screener")
    lead = sorted((n["score"] for n in d["names"]), reverse=True)[:12]
    buckets = {}
    for n in d["names"]:
        b = f"{int(n['score'] // 10) * 10}-{int(n['score'] // 10) * 10 + 9}"
        buckets[b] = buckets.get(b, 0) + 1
    _check_module_subject("screener", lead,
                          [buckets[k] for k in sorted(buckets)])


def test_subject_opening_range_chart():
    d = _d("opening-range")
    lead = [round(100 * w["break_both_frequency"], 2) for w in d["windows"]]
    head = next(w for w in d["windows"] if w.get("headline"))
    rec = [round(100 * e["frequency"], 2) for e in head["extensions"]]
    _check_module_subject("opening-range", lead, rec)


def test_subject_family_fracture_chart():
    d = _d("family-fracture")
    lead = [t["fracture_range_pct"] for t in d["today"]]
    rec = [v["multiplier"] for s in d["history"]["sessions"]
           for v in s["symbols"].values()]
    _check_module_subject("family-fracture", lead, rec)


def test_subject_gamma_ladder_chart():
    d = _d("gamma-ladder")
    vals = [r["pull"] for r in d["funds"][0]["rungs"]]
    _check_module_subject("gamma-ladder", vals, vals)


def test_subject_ai_chart_read_chart():
    d = _d("ai-chart-read")
    vals = d["bars"]["SPY"][1][-60:]
    _check_module_subject("ai-chart-read", vals, vals)


def test_subject_pattern_draw_chart():
    d = _d("pattern-draw")
    vals = d["bars"]["SPY"][1][-60:]
    _check_module_subject("pattern-draw", vals, vals)


def test_subject_breadth_meter_chart():
    d = _d("breadth-meter")
    _check_module_subject(
        "breadth-meter", None, [h["above_200_pct"] for h in d["history"]])


def test_subject_abstention_signal_chart():
    d = _d("abstention-signal")
    _check_module_subject(
        "abstention-signal", None,
        [round(100 * x["rate"], 2) for x in d["decision_days"]])


def test_subject_premium_meter_chart():
    d = _d("premium-meter")
    _check_module_subject(
        "premium-meter", None,
        [s["put_share_percent"] for s in d["names"][0]["sessions"]])


def test_subject_tape_heatmap_chart():
    d = _d("tape-heatmap")
    cells = [c["premium_usd"] for f in d["funds"]
             for side in ("calls", "puts") for c in f[side]["cells"]]
    _check_module_subject(
        "tape-heatmap", None, sorted(cells, reverse=True)[:12])


def test_subject_market_mood_chart():
    d = _d("market-mood")
    pts = sorted(
        ((e["date"], e["readings"]["G2"]["full_history_percentile"])
         for e in d["episodes"]
         if isinstance((e["readings"].get("G2") or {}).get(
             "full_history_percentile"), (int, float))))
    _check_module_subject("market-mood", None, [y for _, y in pts])


def test_no_chart_greeks_payoff():
    # No data.json is invented for these two pages and no internal
    # chart can be drawn: the two sketches lead with their authored
    # subject SVGs. (Desk left this class in the 2026-10-31 cure: it
    # now carries a data.json built from its own snapshot, blocked by
    # test_subject_desk_chart below.)
    for slug in ("greeks-sketch", "payoff-sketch"):
        assert not (SITE / slug / "data.json").exists()
        html = (SITE / slug / "index.html").read_text()
        assert "<svg" in html, f"{slug}: authored subject sketch missing"
    pc = (SITE / "page_charts.js").read_text()
    assert "if (!data) return" in pc


# --- Subject-chart cure, desk page (2026-10-31) -----------------------
# The desk page was the one hub page with no data.json and no chart.
# Its blocker recomputes both charts from the desk snapshot itself
# (the source feed publish_desk.py copies), never from the chart
# block: the lead is the open positions picture, named, aggregated
# from the per-strategy rows; the record is the two equity readings
# the snapshot carries (starting capital at the epoch start, equity
# at the latest cycle). A flat desk must yield a null lead, never a
# substitute chart, and a missing data.json must fail loudly here.

def _desk_expected(feed):
    agg = {}
    for strat in feed.get("strategies") or []:
        for pos in strat.get("open_positions") or []:
            sym, qty = pos.get("symbol"), pos.get("qty")
            if not sym or not isinstance(qty, (int, float)):
                continue
            agg[sym] = agg.get(sym, 0) + qty
    if not agg:
        for pos in feed.get("account_positions") or []:
            sym, qty = pos.get("symbol"), pos.get("qty")
            if not sym or not isinstance(qty, (int, float)):
                continue
            agg[sym] = agg.get(sym, 0) + qty
    lead_vals = [agg[s] for s in sorted(agg, key=lambda s: -abs(agg[s]))] \
        or None
    packet = feed.get("evidence_packet") or {}
    record_vals = [packet.get("starting_capital"),
                   (feed.get("account") or {}).get("equity")]
    return lead_vals, record_vals


def test_subject_desk_chart():
    feed_path = WORKSPACE / "muse-desk-v3" / "terminal" / \
        "terminal_feed.json"
    feed = json.loads(feed_path.read_text())
    lead_vals, record_vals = _desk_expected(feed)
    data_path = SITE / "desk" / "data.json"
    assert data_path.exists(), "desk: data.json missing, charts gone"
    data = json.loads(data_path.read_text())
    # the carried quantities themselves recompute from the feed
    assert [p["qty"] for p in data["positions"]] == \
        (lead_vals or []), "desk: positions block off the feed"
    assert data["epoch"]["starting_capital"] == record_vals[0]
    assert data["account"]["equity"] == record_vals[1]
    _check_subject("desk", lead_vals, record_vals)
    html = (SITE / "desk" / "index.html").read_text()
    assert "../shared.js" in html, "desk: shared chart wiring missing"
    assert "subject_chart.record" in (SITE / "page_charts.js").read_text()


def test_desk_positions_chart_from_synthetic_feed():
    # The live desk is flat at the time of the cure, so the positions
    # lead is also proven on a synthetic snapshot through the real
    # producer: named rows, quantities summed across strategies,
    # shorts kept signed, flat snapshots yielding no lead chart.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "publish_desk", SITE / "publish_desk.py")
    pub = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pub)
    feed = {
        "generated_at": "2026-10-31T20:01:37+00:00",
        "account": {"equity": 101250.5, "cash": 900.0,
                    "buying_power": 2000.0, "portfolio_value": 101250.5,
                    "last_equity": 101000.0, "status": "ACTIVE"},
        "evidence_packet": {
            "starting_capital": 100000.0,
            "period": {"start": "2026-10-26T20:14:30+00:00",
                       "end": "2026-10-31T20:01:37+00:00"}},
        "account_positions": [],
        "strategies": [
            {"name": "alpha", "open_positions": [
                {"symbol": "AAA", "qty": 40},
                {"symbol": "BBB", "qty": -15}]},
            {"name": "beta", "open_positions": [
                {"symbol": "AAA", "qty": 10}]},
        ],
    }
    data = pub.build_data(feed)
    lead = data["subject_chart"]["lead"]
    assert lead and lead["kind"] == "ranked", lead
    assert [(r["name"], r["score"]) for r in lead["rows"]] == \
        [("AAA", 50), ("BBB", -15)], lead["rows"]
    assert lead["rows"][0]["coverage"] == "held by alpha, beta"
    record = data["subject_chart"]["record"]
    assert [p["y"] for p in record["points"]] == [100000.0, 101250.5]
    flat = pub.build_data({**feed, "strategies": []})
    assert flat["subject_chart"]["lead"] is None
    assert flat["subject_chart"]["record"] is not None


# --- Wave 2 cures: earnings-drift per-event rows, earnings-calendar
# realised moves, decay-watch movements proof (2026-10-31) --------------
# Each blocker recomputes the charted values from the lane's own
# kept records and the DEEP panel closes, never from the chart block.

_DEEP_READER = None


def _deep_closes(symbol):
    global _DEEP_READER
    import sys
    if str(SITE) not in sys.path:
        sys.path.insert(0, str(SITE))
    if _DEEP_READER is None:
        from deep_panel_reader import DeepPanelReader
        _DEEP_READER = DeepPanelReader(
            str(WORKSPACE / "morgue" / "data_cache" / "deep_bars.json"),
            log=False)
    return {row[0]: row[4] for row in _DEEP_READER[symbol]}


def _move_on_or_after(closes, day):
    """The terminal's earnings convention, recomputed: the close of
    the first session on or after the report date against the close
    just before it, in percent, rounded the producer's way."""
    dates = sorted(closes)
    sess = [d for d in dates if d >= day]
    prior = [d for d in dates if d < day]
    assert sess and prior, f"no sessions around {day}"
    return round((closes[sess[0]] / closes[prior[-1]] - 1) * 100, 4), sess[0]


def test_subject_earnings_drift_per_event_rows():
    d = _d("earnings-drift")
    rows = d.get("event_rows") or []
    assert rows, "earnings-drift: no per-event rows carried"
    assert len(rows) == d["events"], (len(rows), d["events"])
    for r in rows:
        expect, sess = _move_on_or_after(
            _deep_closes(r["symbol"]), r["report_date"])
        assert r["drift_pct"] == expect, r
        assert r["session_date"] == sess, r
    # The pooled figures the page has always carried recompute from
    # the per-event rows (annotation, not a substitute chart).
    vals = [r["drift_pct"] for r in rows]
    assert abs(sum(vals) / len(vals) - d["mean"] * 100) < 0.01
    assert sum(1 for v in vals if v > 0) == d["positive"]
    # The record chart plots every event, named, with its own move.
    _, charts = _charts("earnings-drift")
    got = _rows_by_name(charts)
    assert got == {f"{r['symbol']} {r['report_date']}": r["drift_pct"]
                   for r in rows}, "record chart is not the per-event rows"
    gen = (SITE / "refresh_earningsdrift.py").read_text()
    assert "event_rows" in gen and "DeepPanelReader" in gen
    seg = _adapter_segment((SITE / "tool-visual.js").read_text(),
                           "earnings-drift")
    assert "event_rows" in seg and "share_positive" in seg


def test_subject_earnings_calendar_realised_moves():
    d = _d("earnings-calendar")
    rows = d.get("realised_moves") or []
    assert rows, "earnings-calendar: no realised moves carried"
    priced = {}
    pp = SITE / "earnings-record" / "priced_moves.json"
    if pp.exists():
        priced = {k: v["priced_move_pct"] for k, v in
                  json.loads(pp.read_text())["names"].items()}
    for r in rows:
        assert r["report_date"] < d["recorded_on"], r
        expect, sess = _move_on_or_after(
            _deep_closes(r["symbol"]), r["report_date"])
        assert r["realised_move_pct"] == expect, r
        assert r["session_date"] == sess, r
        if r.get("expected_move_pct") is not None:
            # An expected value may only be the priced record's own
            # figure for that same name; never another name's.
            assert priced.get(r["symbol"]) == r["expected_move_pct"], r
    # No name that has not yet reported appears among realised rows.
    future = {n["symbol"] for n in d["names"]
              if n["date"] >= d["recorded_on"]}
    assert not ({r["symbol"] for r in rows} & future
                and any(r["report_date"] >= d["recorded_on"]
                        for r in rows))
    store = json.loads(
        (SITE / "earnings-calendar" / "realised_moves.json").read_text())
    assert store["rows"] == rows, "accrual store and page disagree"
    _, charts = _charts("earnings-calendar")
    got = _rows_by_name(charts)
    assert got == {f"{r['symbol']} {r['report_date']}":
                   r["realised_move_pct"] for r in rows}, \
        "record chart is not the realised moves"
    gen = (SITE / "refresh_earningscal.py").read_text()
    assert "realised_moves" in gen and "DeepPanelReader" in gen


def test_subject_decay_watch_movements_proof():
    import importlib.util
    d = _d("decay-watch")
    # The proof the empty movements list is correct: exactly one
    # grading exists, in the producer's own source records.
    assert d["gradings_count"] == 1 and len(d["gradings"]) == 1
    assert d["movements"] == []
    assert all(v == 0 for v in d["movement_counts"].values())
    frozen = WORKSPACE / "peer-execute-20261027" / "sources" / \
        "a_factory" / "desk" / "forecast" / "frozen"
    versions = sorted(p.name for p in frozen.glob("promoted-book-*.json"))
    assert versions == ["promoted-book-1.json"], versions
    book = json.loads((frozen / "promoted-book-1.json").read_text())
    assert len(book["entries"]) == d["current_counts"]["total"]
    for e in book["entries"]:
        # No entry carries a second standing or any history field:
        # no transition is provable from the kept record.
        assert "history" not in e and "previous" not in e
    # The forward recording layer: one standings snapshot, matching
    # the book entry by entry.
    hist = json.loads(
        (SITE / "decay-watch" / "standings-history.json").read_text())
    assert len(hist["snapshots"]) == 1
    snap = hist["snapshots"][0]
    assert snap["grading_date"] == d["gradings"][0]["date"]
    assert snap["standings"] == {e["id"]: e["status"]
                                 for e in book["entries"]}
    # The producer's transition function, exercised on synthetic
    # standings: promotion, demotion, probation entry and exit.
    spec = importlib.util.spec_from_file_location(
        "refresh_decaywatch", SITE / "refresh_decaywatch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    moves = mod.compute_movements(
        {"A": "probation", "B": "promoted", "C": "probation"},
        {"A": "promoted", "B": "probation", "D": "probation"},
        "2026-10-27", "2026-11-03")
    by_name = {m["name"]: m for m in moves}
    assert by_name["A"]["from"] == "probation"
    assert by_name["A"]["to"] == "promoted"
    assert by_name["B"]["to"] == "probation"
    assert by_name["C"]["to"] == "left the book"
    assert by_name["D"]["from"] == "not in the book"
    assert all(m["date"] == "2026-11-03" for m in moves)
    # The chart is labelled with the proven state, not a fallback.
    _, charts = _charts("decay-watch")
    text = " ".join((c.get("title") or "") + " " + (c.get("label") or "")
                    for c in charts)
    assert "graded once" in text and "no movement" in text
    gen = (SITE / "refresh_decaywatch.py").read_text()
    assert "standings-history" in gen and "compute_movements" in gen


# --- Wave 3 cures (2026-10-31) ---------------------------------------
# Item E: ai-chart-read and pattern-draw records carry the page's own
# reads drawn on the closes (labels at their sessions), distinct from
# the bare lead curve. Item F: agent-debate, gamma-ladder,
# morning-map and sponsored-reset records chart the current session's
# subject picture today, and each page's producer keeps a dated
# session snapshot from this run forward (append-only store); once
# more than one session is kept, the record plots the kept sessions.
# ---------------------------------------------------------------------

import importlib.util  # noqa: E402


def _load_site_module(name):
    spec = importlib.util.spec_from_file_location(
        name, SITE / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _check_labelled_record(slug):
    d = _d(slug)
    sc = d.get("subject_chart") or {}
    lead, record = sc.get("lead"), sc.get("record")
    assert record and record["kind"] == "curve", \
        f"{slug}: record is not a curve"
    assert "labels" in (record.get("source") or ""), \
        f"{slug}: record source does not name the labels"
    seq = ((d.get("labels") or {}).get("SPY") or {}).get("sequence") or []
    notes = {s["date"]: s["label"] for s in seq
             if s.get("date") and s.get("label")}
    assert notes, f"{slug}: no SPY label sequence on record"
    # The lead stays the bare curve: no point carries a note.
    assert all("note" not in p for p in lead["points"]), \
        f"{slug}: lead carries label notes"
    # Record points are the same closes as the lead, recomputed from
    # bars and dates, with a note exactly at each labelled session.
    closes = d["bars"]["SPY"][1]
    dates = d["dates"]
    assert [p["y"] for p in record["points"]] == \
        [p["y"] for p in lead["points"]], \
        f"{slug}: record closes differ from the lead closes"
    got = {}
    for p in record["points"]:
        assert p["y"] == closes[dates.index(p["x"])], \
            f"{slug}: record close at {p['x']} differs from bars"
        if p.get("note"):
            got[p["x"]] = p["note"]
    assert got == notes, \
        f"{slug}: drawn labels {got} != label sequence {notes}"
    assert record != lead, f"{slug}: record is still the bare curve"
    # The real VisualKit draws the label text on the record curve.
    out = _subject_render(slug)
    for label in set(notes.values()):
        assert f">{label}</text>" in out["record"], \
            f"{slug}: label {label} not drawn on the record curve"
    for label in set(notes.values()):
        assert f">{label}</text>" not in out["lead"], \
            f"{slug}: label {label} drawn on the lead curve"


def test_subject_ai_chart_read_record_labels():
    _check_labelled_record("ai-chart-read")


def test_subject_pattern_draw_record_labels():
    _check_labelled_record("pattern-draw")


def test_session_keeping_appends_not_overwrites(tmp_path):
    sh = _load_site_module("session_history")
    store = tmp_path / "session-history.json"
    v1 = [{"symbol": "SPY", "rising": 1, "falling": 5}]
    v2 = [{"symbol": "SPY", "rising": 2, "falling": 4}]
    out1 = sh.append_session(str(store), "2026-10-30", v1)
    assert out1 == [{"session": "2026-10-30", "values": v1}]
    out2 = sh.append_session(str(store), "2026-11-02", v2)
    assert len(out2) == 2, "second dated run overwrote the first"
    assert out2[0] == {"session": "2026-10-30", "values": v1}, \
        "the first kept session changed when the second was appended"
    assert out2[1] == {"session": "2026-11-02", "values": v2}
    # An identical repeat of the latest entry (a chained re-run inside
    # one lane pass) must not duplicate the session.
    out3 = sh.append_session(str(store), "2026-11-02", v2)
    assert len(out3) == 2
    on_disk = json.loads(store.read_text())
    assert on_disk["sessions"] == out3


def test_agent_debate_session_kept():
    d = _d("agent-debate")
    kept = d.get("session_history") or []
    assert kept, "agent-debate: no session kept on the page data"
    last = kept[-1]
    assert last["session"] == d["session"]
    exp = {f["symbol"]: (f["count_rising"], f["count_falling"])
           for f in d["funds"]}
    got = {v["symbol"]: (v["rising"], v["falling"])
           for v in last["values"]}
    assert got == exp, "agent-debate: kept values differ from funds"
    store = json.loads(
        (SITE / "agent-debate" / "session-history.json").read_text())
    assert store["sessions"] == kept
    gen = (SITE / "refresh_agentdebate.py").read_text()
    assert "append_session" in gen and "session_history" in gen


def test_gamma_ladder_session_kept():
    d = _d("gamma-ladder")
    kept = d.get("session_history") or []
    assert kept, "gamma-ladder: no session kept on the page data"
    last = kept[-1]
    assert last["session"] == d["session"]
    f0 = d["funds"][0]
    assert last["values"]["symbol"] == f0["symbol"]
    exp = [(r["strike"], r["pull"]) for r in f0["rungs"]]
    got = [(r["strike"], r["pull"]) for r in last["values"]["rungs"]]
    assert got == exp, "gamma-ladder: kept rungs differ from funds[0]"
    store = json.loads(
        (SITE / "gamma-ladder" / "session-history.json").read_text())
    assert store["sessions"] == kept
    gen = (SITE / "refresh_gammaladder.py").read_text()
    assert "append_session" in gen and "session_history" in gen


def test_morning_map_session_kept():
    d = _d("morning-map")
    kept = d.get("session_history") or []
    assert kept, "morning-map: no session kept on the page data"
    last = kept[-1]
    assert last["session"] == d["session"]
    exp = {ix["symbol"]: (ix.get("spot"),
                           (ix.get("put_wall") or {}).get("value"),
                           (ix.get("flip") or {}).get("value"),
                           (ix.get("call_wall") or {}).get("value"))
           for ix in d["indexes"]}
    got = {v["symbol"]: (v["spot"], v["put_wall"], v["flip"],
                         v["call_wall"]) for v in last["values"]}
    assert got == exp, "morning-map: kept levels differ from indexes"
    store = json.loads(
        (SITE / "morning-map" / "session-history.json").read_text())
    assert store["sessions"] == kept
    gen = (SITE / "refresh_morning_map.py").read_text()
    assert "append_session" in gen and "session_history" in gen


def test_sponsored_reset_session_kept():
    d = _d("sponsored-reset")
    kept = d.get("session_history") or []
    assert kept, "sponsored-reset: no session kept on the page data"
    last = kept[-1]
    assert last["session"] == (d["live"].get("freshest_session")
                               or d.get("as_of"))
    exp = [(x["date"], x["spy_change_pct"]) for x in d["history"]["days"]]
    got = [(x["date"], x["spy_change_pct"])
           for x in last["values"]["days"]]
    assert got == exp, \
        "sponsored-reset: kept days differ from history.days"
    store = json.loads(
        (SITE / "sponsored-reset" / "session-history.json").read_text())
    assert store["sessions"] == kept
    gen = (SITE / "refresh_sponsoredreset.py").read_text()
    assert "append_session" in gen and "session_history" in gen


def test_agent_debate_record_plots_kept_sessions():
    rs = _load_site_module("record_surface")
    data = {
        "funds": [{"symbol": "SPY", "count_rising": 3,
                   "count_falling": 1},
                  {"symbol": "QQQ", "count_rising": 2,
                   "count_falling": 2}],
        "session_history": [
            {"session": "2026-10-29",
             "values": [{"symbol": "SPY", "rising": 0, "falling": 2},
                        {"symbol": "QQQ", "rising": 1, "falling": 1}]},
            {"session": "2026-10-30",
             "values": [{"symbol": "SPY", "rising": 3, "falling": 1},
                        {"symbol": "QQQ", "rising": 2, "falling": 2}]},
        ],
    }
    sc = rs.build_subject_chart("agent-debate", data)
    rows = {r["name"]: r["score"] for r in sc["record"]["rows"]}
    assert rows == {"2026-10-29 SPY": -2, "2026-10-29 QQQ": 0,
                    "2026-10-30 SPY": 2, "2026-10-30 QQQ": 0}, rows


def test_gamma_ladder_record_plots_kept_sessions():
    rs = _load_site_module("record_surface")
    data = {
        "funds": [{"symbol": "SPY",
                   "rungs": [{"strike": 750.0, "pull": -5.0}]}],
        "session_history": [
            {"session": "2026-10-29",
             "values": {"symbol": "SPY",
                        "rungs": [{"strike": 740.0, "pull": -3.0}]}},
            {"session": "2026-10-30",
             "values": {"symbol": "SPY",
                        "rungs": [{"strike": 750.0, "pull": -5.0}]}},
        ],
    }
    sc = rs.build_subject_chart("gamma-ladder", data)
    rows = {r["name"]: r["score"] for r in sc["record"]["rows"]}
    assert rows == {"2026-10-29 strike 740.0": -3.0,
                    "2026-10-30 strike 750.0": -5.0}, rows


def test_morning_map_record_plots_kept_sessions():
    rs = _load_site_module("record_surface")
    ix = {"symbol": "SPY", "spot": 755.72,
          "put_wall": {"value": 750.0}, "flip": {"value": 768.8},
          "call_wall": {"value": 800.0}}
    data = {
        "indexes": [ix],
        "session_history": [
            {"session": "2026-10-29",
             "values": [{"symbol": "SPY", "spot": 750.0,
                         "put_wall": 745.0, "flip": 760.0,
                         "call_wall": 790.0}]},
            {"session": "2026-10-30",
             "values": [{"symbol": "SPY", "spot": 755.72,
                         "put_wall": 750.0, "flip": 768.8,
                         "call_wall": 800.0}]},
        ],
    }
    charts = rs.subject_charts_for("morning-map", data)
    lines = [c for c in charts if c.get("kind") == "line"]
    assert lines, "morning-map: kept sessions not plotted"
    series = lines[0]["series"]
    assert [(p["date"], p["value"]) for p in series] == \
        [("2026-10-29", 760.0), ("2026-10-30", 768.8)], series
