#!/usr/bin/env python3
"""Hub refresh: the hub page's producer (cure D-HUB, 2026-10-30).

The hub (site/index.html) was the one page in the terminal with no
producer: its lineup counts, status chips and as-of dates were typed
by hand when the page was rebuilt and aged from that day, while every
card points at a page whose own data moves daily. This refresher is
the minimum sufficient producer. It recomputes only the factual,
machine-checkable parts of the hub from each card page's own
published data file, and leaves the hand-written card prose (job
lines, headline figures, full notes) and the editorial status chips
untouched:

- Each card's "As of" date is rewritten from its page's data file,
  first field present wins, in the design's source order:
  as_of_session, session, as_of, recorded_on, published_at_utc,
  generated_at_utc.
- A card whose page is stale gets the Stale chip: headline session
  older than the latest completed session on a daily cadence (the
  audit's own definition). 13f-tracker is quarterly and exempt; the
  two calculator pages (greeks-sketch, payoff-sketch) publish no
  data file and keep their authored chip and date.
- A card that was Stale and whose page is current again gets back
  the chip it carried before it went stale: this refresher keeps
  one small producer state file (hub_chips.json, the last non-stale
  chip per slug, written only by this refresher) so a recovered
  page never has to be retyped by hand and this refresher never
  invents a Live chip for a page it has not seen live.
- The count line and the lineup meter are recomputed from the
  final chips on the cards, so the hub's headline numbers can
  never again disagree with its own cards.

It runs last in the tools chain (refresh_tools.py), after every
tool, engine, tape and stores page for the evening has refreshed,
and before the manifest rebuild and smoke check, so the manifest
and the smoke check see the hub's final state.

Usage: python3 refresh_hub.py
Exit 0 when the hub was rewritten (or already matched); exit 1 on
any card whose data file exists but does not parse, or when the
hub structure is not the expected card grid.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = Path(__file__).resolve().parent
HUB = HERE / "index.html"

DATE_FIELDS = ("as_of_session", "session", "as_of", "recorded_on",
               "published_at_utc", "generated_at_utc")
NO_DATA = {"greeks-sketch", "payoff-sketch"}
QUARTERLY = {"13f-tracker"}
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November",
          "December"]
CHIP_WORDS = {"live": "Live", "waiting": "Waiting",
              "ungraded": "Not yet graded", "stale": "Stale",
              "missing": "Missing"}


def plain_date(d: date) -> str:
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def parse_date(value):
    if not isinstance(value, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def headline_date(slug: str):
    """The page's own headline session from its data file, or None."""
    path = HERE / slug / "data.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return None
    for field in DATE_FIELDS:
        d = parse_date(data.get(field))
        if d is not None:
            return d
    return None


def latest_completed_session(today: date) -> date:
    d = today - timedelta(days=1)
    while d.weekday() >= 5:  # Sat, Sun
        d -= timedelta(days=1)
    return d


# --- Charts-IA restructure (2026-10-31): ruled section order --------
# The hub opens with a Visual Front, then Forecast Engines, Market
# Tools, Modules, The Record, and Desk last. This step is idempotent:
# it collects every card wherever it currently sits and rebuilds the
# sections in the ruled order, so hand drift cannot reorder the hub.
# Card prose, chips and dates are untouched here; the chip/date pass
# below still owns them. Membership sets are producer constants:
# ENGINES is the audited 30 forecast engines; MODULES is the seven
# composite surfaces ruled as Modules on 2026-10-31 (market-mood the
# psychology engine, regime-dial, morning-map, second-opinion,
# one-page-report, living-router, calibration-league). living-router
# and calibration-league are also registry engines: their hub home is
# Modules, so the Forecast Engines grid carries the other 28 engine
# cards and no card is duplicated. RECORD_SECTION carries
# The Record family. Everything else is a Market Tool (65 cards).
ENGINES = ["corrected-band", "touch-surface", "own-norm-depth",
           "stress-reversal", "honest-pop", "exceedance",
           "vol-term-shape", "intake-bias", "insider-divergence",
           "gamma-earnings-trap", "earnings-distribution",
           "wall-lifetime", "vol-clock", "self-analogue",
           "idio-liquidity", "capitulation-clock", "family-fracture",
           "living-router", "in-regime-oracle", "calibration-league",
           "streak-trap", "half-life-clock", "mortality-curve",
           "fear-day-triangulation", "sponsored-reset", "pin-or-escape",
           "silent-accumulation", "gap-destiny", "completion-clock",
           "abstention-signal"]
MODULES = ["market-mood", "regime-dial", "morning-map",
           "second-opinion", "one-page-report", "living-router",
           "calibration-league"]
RECORD_SECTION = ["record", "horizon-grades"]
VISUAL_FRONT = [
    ("market-mood", "Nine gauges of market mood in one reading."),
    ("corrected-band", "The published price ranges, drawn widening over the days ahead."),
    ("vol-term-shape", "How the expected size of moves changes with time."),
    ("capitulation-clock", "How close the market sits to a washout reading."),
    ("breadth-meter", "How many stocks are rising with the market."),
    ("regime-dial", "Six checks combined into one reading of the market kind."),
    ("sector-rotation", "Which parts of the market have been leading."),
    ("tape-heatmap", "Where the day's trading bunched up."),
]


def _mini_types():
    """Hub mini-visual type per slug, from the audit's INFO-MAP.md."""
    types = {}
    info = (HERE.parents[1] / "research_notes" /
            "terminal-visual-expression-20261031" / "INFO-MAP.md")
    try:
        lines = info.read_text(encoding="utf-8").splitlines()
    except OSError:
        return types
    for line in lines:
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 8 or not re.match(r"^[a-z0-9-]+$", cells[1]):
            continue
        mini = cells[6].lower()
        for key, word in (("sparkline", "sparkline"),
                          ("heatmap", "heatmap"),
                          ("distribution", "distribution"),
                          ("gauge", "gauge"), ("donut", "donut"),
                          ("payoff", "sparkline"), ("band", "band"),
                          ("timeline", "timeline"), ("fan", "fan"),
                          ("line", "line")):
            if key in mini:
                types[cells[1]] = word
                break
        else:
            types[cells[1]] = "countbars"
    return types


def restructure(hub):
    """Rebuild the hub body in the ruled order. Returns new hub text."""
    cards = re.findall(r"<article class=\"hubcard\".*?</article>",
                       hub, re.S)
    by_slug, order = {}, []
    for card in cards:
        m = re.search(r'href="([a-z0-9-]+)/"', card)
        if not m:
            continue
        by_slug[m.group(1)] = card
        order.append(m.group(1))
    if len(by_slug) < 90:
        return hub
    types = _mini_types()
    for slug, card in list(by_slug.items()):
        if 'class="mini"' not in card:
            mini = (f'<div class="mini" data-mini="'
                    f'{types.get(slug, "countbars")}" '
                    f'data-slug="{slug}"></div>')
            card, n = re.subn(r'(<p class="figline">.*?</p>)',
                              r"\1\n" + mini, card, count=1, flags=re.S)
            if not n:
                card, n = re.subn(r'(<p class="jobline">.*?</p>)',
                                  r"\1\n" + mini, card, count=1,
                                  flags=re.S)
            if not n:
                card = re.sub(r'(<div class="cardfoot">)',
                              mini + r"\n\1", card, count=1)
            by_slug[slug] = card
    vf = hub.find('<section id="visual-front">')
    if vf >= 0:
        vf_end = hub.find("</section>", vf)
        if vf_end >= 0:
            hub = hub[:vf] + hub[vf_end + len("</section>\n"):]
    head_end = hub.find("<h2")
    script_at = hub.rfind("<script>", 0,
                          hub.find('getElementById("hubsearch")'))
    if head_end < 0 or script_at < 0:
        return hub
    prefix, suffix = hub[:head_end], hub[script_at:]
    names = {}
    for slug, card in by_slug.items():
        m = re.search(r"<h3><a[^>]*>([^<]+)</a></h3>", card)
        if m:
            names[slug] = m.group(1)

    def grid(slugs):
        body = "\n".join(by_slug[s] for s in slugs if s in by_slug)
        return f'<div class="hubgrid">\n{body}\n</div>\n'

    tiles = "\n".join(
        f'<div class="vftile" data-vf="{slug}"><h3>'
        f'<a href="{slug}/">{names.get(slug, slug)}</a></h3>'
        f'<div class="vfchart"></div>'
        f'<p class="vfsub">{sub}</p></div>'
        for slug, sub in VISUAL_FRONT if slug in by_slug)
    tools = [s for s in order if s not in ENGINES and s not in MODULES
             and s not in RECORD_SECTION]
    parts = [prefix]
    parts.append('<section id="visual-front">'
                 "<h2>Today, in pictures</h2>"
                 f'<div class="visualfront">\n{tiles}\n</div>'
                 "</section>\n")
    parts.append('<h2 id="forecast-engines">Forecast Engines</h2>\n'
                 + grid([s for s in ENGINES
                         if s in by_slug and s not in MODULES]))
    parts.append('<h2 id="ready-to-use">Market Tools</h2>\n'
                 + grid(tools))
    parts.append('<h2 id="modules">Modules</h2>\n'
                 + grid([s for s in MODULES if s in by_slug]))
    parts.append('<h2 id="the-record">The Record</h2>\n'
                 + grid([s for s in RECORD_SECTION if s in by_slug]))
    parts.append('<h2 id="desk">Desk</h2>\n'
                 '<div class="deskcard"><h3>'
                 '<a href="desk/">Your trading desk</a></h3>'
                 "<p>The paper trading desk: its positions, its "
                 "setups and the day's cycle, kept last by design. "
                 "The engines, tools and modules above come first."
                 "</p></div>\n")
    parts.append(suffix)
    return "".join(parts)


def main() -> int:
    original = HUB.read_text(encoding="utf-8")
    hub = restructure(original)
    try:
        import publish_desk as _pd
        _pd.publish()
    except Exception as _exc:  # desk copy is a soft step, named loudly
        print(f"desk publish step failed: {_exc}")
    cards = re.findall(r"<article class=\"hubcard\".*?</article>",
                       hub, re.S)
    if len(cards) < 90:
        print(f"FAIL: expected the 100 card grid, found {len(cards)} cards")
        return 1
    today = datetime.now().date()
    latest = latest_completed_session(today)
    state_path = HERE / "hub_chips.json"
    saved_chips = {}
    if state_path.exists():
        try:
            saved_chips = json.loads(
                state_path.read_text(encoding="utf-8"))
        except Exception:
            saved_chips = {}
    failures = []
    stale_slugs = []
    counts = {"live": 0, "waiting": 0, "ungraded": 0, "stale": 0,
              "missing": 0}
    out = hub
    for card in cards:
        m = re.search(r'href="([a-z0-9-]+)/"', card)
        if not m:
            failures.append("card without a page link")
            continue
        slug = m.group(1)
        new_card = card
        if slug not in NO_DATA:
            try:
                d = headline_date(slug)
            except Exception as e:  # data file does not parse: loud
                failures.append(f"{slug}: data file does not parse: {e}")
                continue
            if d is not None:
                cur = re.search(r'class="chip ([a-z]+)"', new_card)
                if cur and cur.group(1) != "stale":
                    saved_chips[slug] = cur.group(1)
                if slug not in QUARTERLY and d < latest:
                    stale_slugs.append(slug)
                    new_card = re.sub(
                        r'<span class="chip [a-z]+">[^<]*</span>',
                        '<span class="chip stale">Stale</span>',
                        new_card, count=1)
                elif cur and cur.group(1) == "stale":
                    back = saved_chips.get(slug, "ungraded")
                    new_card = re.sub(
                        r'<span class="chip [a-z]+">[^<]*</span>',
                        f'<span class="chip {back}">'
                        f'{CHIP_WORDS[back]}</span>',
                        new_card, count=1)
                new_card = re.sub(
                    r'(<span class="updated">As of )[^<]*(</span>)',
                    lambda mm: mm.group(1) + plain_date(d) + mm.group(2),
                    new_card, count=1)
        chip = re.search(r'class="chip ([a-z]+)"', new_card)
        if chip and chip.group(1) in counts:
            counts[chip.group(1)] += 1
        if new_card != card:
            out = out.replace(card, new_card, 1)
    total = sum(counts.values())
    count_line = (
        f"{total} tools in the lineup: {counts['live']} live, "
        f"{counts['waiting']} waiting, {counts['ungraded']} not yet "
        f"graded, {counts['stale']} stale. Status and dates come "
        f"from each tool's own latest note, shown in full on its card.")
    out, n = re.subn(r'<p class="hubcount">[^<]*</p>',
                     f'<p class="hubcount">{count_line}</p>', out,
                     count=1)
    if n != 1:
        failures.append("hub count line not found")
    pct = round(100 * counts["live"] / total) if total else 0
    out = re.sub(
        r'(<div class="fill" style="width:)\d+(%"></div>)',
        lambda mm: mm.group(1) + str(pct) + mm.group(2),
        out, count=1)
    out = re.sub(
        r'(<span class="mvalue">)\d+ of \d+( tools live today</span>)',
        lambda mm: mm.group(1) + str(counts["live"]) + " of " + str(total) + mm.group(2),
        out, count=1)
    out = re.sub(
        r'(<span>Full lineup: )\d+(</span>)',
        lambda mm: mm.group(1) + str(total) + mm.group(2),
        out, count=1)
    if failures:
        print("FAILURES: " + "; ".join(failures))
        return 1
    if out != original:
        HUB.write_text(out, encoding="utf-8")
    state_path.write_text(json.dumps(saved_chips, indent=1,
                                     sort_keys=True) + "\n",
                          encoding="utf-8")
    print(f"hub refreshed: {total} cards; live {counts['live']}, "
          f"waiting {counts['waiting']}, not yet graded "
          f"{counts['ungraded']}, stale {counts['stale']}"
          + (f" ({', '.join(sorted(stale_slugs))})"
             if stale_slugs else "")
          + f"; latest completed session {latest.isoformat()}")
    # Provenance stamp (R-09 residual cure, 2026-10-30): this
    # refresher publishes index.html, not a data.json, so its run
    # summary is the record it stamps, the same shipyard stamp
    # every refresher carries, exactly as the two daily runners
    # (refresh_engines.py, refresh_tools.py) stamp theirs.
    summary = {"runner": "refresh_hub.py", "cards": total,
               "live": counts["live"], "waiting": counts["waiting"],
               "not_yet_graded": counts["ungraded"],
               "stale": counts["stale"],
               "stale_slugs": sorted(stale_slugs),
               "latest_completed_session": latest.isoformat()}
    summary = _tc.stamp_for_script(summary, __file__) \
        if _tc is not None else summary
    print(f"run provenance: feed={summary.get('feed')} "
          f"price_basis={summary.get('price_basis')} "
          f"execution_pricing={summary.get('execution_pricing')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
