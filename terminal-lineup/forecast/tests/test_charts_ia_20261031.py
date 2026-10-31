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


def test_desk_publish_copy_matches_source():
    # The desk feed is live and moves on its own cycle, so the blocker
    # proves the producer: a fresh publish must be byte-identical.
    out = subprocess.run(
        ["python3", str(SITE / "publish_desk.py")],
        capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    src = WORKSPACE / "muse-desk-v3" / "terminal"
    for name in ("index.html", "terminal_feed.json"):
        a = hashlib.sha256((src / name).read_bytes()).hexdigest()
        b = hashlib.sha256(
            (SITE / "desk" / name).read_bytes()).hexdigest()
        assert a == b, name


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
    _check_subject("sponsored-reset",
                   [x["spy_change_pct"] for x in d["history"]["days"]], None)


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
        out = {}
        for nm in d["names"]:
            em = nm.get("expected_move")
            if isinstance(em, str) and em.endswith("%"):
                out[f"{nm['symbol']} {nm['date']}"] = float(em[:-1])
        return out
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
chain-explorer correlation-web earnings-calendar expiry-pin-watch fear-day
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
    "earnings-drift": lambda d: {
        "Average move after reporting": round(d["mean"] * 10000) / 100,
        "Middle move after reporting": round(d["median"] * 10000) / 100,
        "Share of reports that rose": round(d["share_positive"] * 1000) / 10},
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
        assert charts == [], \
            "morning-map: past maps are not kept; no record chart may " \
            "be drawn and no counts may be substituted"
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
    _check_module_subject(
        "agent-debate",
        [f["count_rising"] - f["count_falling"] for f in d["funds"]], None)


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
    _check_module_subject(
        "gamma-ladder", [r["pull"] for r in d["funds"][0]["rungs"]], None)


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


def test_no_chart_desk_greeks_payoff():
    # No data.json is invented for these pages and no internal chart
    # can be drawn: desk is a byte-for-byte publish copy with no chart
    # wiring; the two sketches lead with their authored subject SVGs.
    assert not (SITE / "desk" / "data.json").exists()
    desk_html = (SITE / "desk" / "index.html").read_text()
    assert "page_charts" not in desk_html and "shared.js" not in desk_html
    for slug in ("greeks-sketch", "payoff-sketch"):
        assert not (SITE / slug / "data.json").exists()
        html = (SITE / slug / "index.html").read_text()
        assert "<svg" in html, f"{slug}: authored subject sketch missing"
    pc = (SITE / "page_charts.js").read_text()
    assert "if (!data) return" in pc
