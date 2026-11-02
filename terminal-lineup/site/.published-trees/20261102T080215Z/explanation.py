#!/usr/bin/env python3
"""Collapsed explanation producer (2026-10-31, final form).

Adds ONE new block, ``explanation``, to a page's data.json:

- ``summary``: the collapsed line. It is the page's OWN plain sentence
  stating what the thing is: the job line printed in the page's own
  index.html (``<p class="job">``), with the "One job:" lead-in removed.
  Market Mood prints no job line; its summary is the intro sentence its
  own page carries ("Nine gauges of market mood in one reading: ...").
  Every summary is therefore different on every page by construction.
- ``body``: the fuller explanation, still in plain words and built only
  from the page's record. For the 30 forecast engines it comes from
  forecast/registry.json: what form the forecast takes, its horizons,
  how it is graded (the grading rule's own description), what would end
  it (its kill criterion) and what counts as proven (its proving
  threshold). For tools and modules it comes from the page's own
  record_surface block: when the current reading is from, how much
  study record is on file, the live counts where they exist, and the
  line naming what is missing and when it arrives.

No heading or label is produced here or in the renderer, and no text
template repeats across pages except the short connective phrases that
carry each page's own values. Nothing is invented: a field that is not
on record contributes no sentence. No raw internal field names, engine
ids or grading rule ids appear in the text.
"""
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

MARKET_MOOD_SUMMARY = (
    "Nine gauges of market mood in one reading: what people say, how "
    "the slow climate sits, where money sits, what protection costs, "
    "and more.")


def _clean_html_text(fragment):
    text = re.sub(r"<[^>]+>", "", fragment)
    text = (text.replace("&amp;", "&").replace("&lt;", "<")
            .replace("&gt;", ">").replace("&quot;", '"')
            .replace("&#39;", "'"))
    return re.sub(r"\s+", " ", text).strip()


def jobline_for(slug):
    """The page's own job sentence from its index.html, or None."""
    page = HERE / slug / "index.html"
    if not page.exists():
        return None
    html = page.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<p class="job">(.*?)</p>', html, re.S)
    if not m:
        return None
    text = _clean_html_text(m.group(1))
    text = re.sub(r"^One job:\s*", "", text)
    if text:
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."
    return text or None


# Plain-word renderings of the registry's own grading rule
# descriptions (forecast/registry.json grading_rules). The registry
# text itself carries scoring jargon; these say the same thing in
# plain words and are the only grading text used.
PLAIN_GRADING = {
    "coverage": ("how often its stated ranges contain what actually "
                 "happens, checked against the width of those ranges"),
    "brier": ("a score that rewards probabilities that land close to "
              "what actually happens"),
    "pinball": ("a loss score on each of its stated percentile lines, "
                "where lower is better"),
    "abs_error": ("the size and direction of the gap between its "
                  "forecast and what actually happens"),
    "ranked_probability_score": (
        "a score that rewards putting the most weight on the band "
        "of outcomes that actually happens"),
    "survival_brier": (
        "whether its timing calls resolve by each stated horizon, "
        "with unresolved cases still counted"),
}


def _registry():
    path = ROOT / "forecast" / "registry.json"
    reg = json.loads(path.read_text())
    rules = {r["id"]: PLAIN_GRADING.get(r["id"], r["description"])
             for r in reg.get("grading_rules", [])}
    return reg.get("engines", []), rules


def _engine_for(slug):
    import record_surface
    return record_surface.engine_for_slug(slug, {})


def _sentence(text):
    text = re.sub(r"\s+", " ", str(text)).strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _lower_first(text):
    return text[0].lower() + text[1:] if text else text


def engine_body(entry, rules, summary):
    parts = []
    form = entry.get("forecast_form")
    horizons = entry.get("horizons")
    if form and horizons:
        parts.append(_sentence(
            f"Its forecast takes this form: {form}, over {horizons}"))
    elif form:
        parts.append(_sentence(f"Its forecast takes this form: {form}"))
    elif horizons:
        parts.append(_sentence(f"It forecasts over {horizons}"))
    rule = rules.get(entry.get("grading_rule_id"))
    if rule:
        parts.append(_sentence(f"It is graded on { _lower_first(rule.rstrip('.')) }"))
    kill = entry.get("kill_criterion")
    if kill:
        parts.append(_sentence(
            f"It would be ended if {_lower_first(str(kill).rstrip('.'))}"))
    proving = entry.get("proving_threshold")
    if proving:
        parts.append(_sentence(
            f"It counts as proven at {_lower_first(str(proving).rstrip('.'))}"))
    return " ".join(parts)


def tool_body(slug, data, summary):
    rs = data.get("record_surface") or {}
    parts = []
    reading = rs.get("current_reading") or {}
    if reading.get("as_of"):
        parts.append(_sentence(
            f"Its current reading is from {str(reading['as_of'])[:10]}"))
    study = rs.get("study_record") or {}
    total = study.get("total_items_counted")
    if isinstance(total, (int, float)) and total:
        parts.append(_sentence(
            f"Its study record, the history it was built and checked on, "
            f"holds {int(total)} counted items on file"))
    accrual = rs.get("live_accrual") or {}
    counts = accrual.get("counts")
    if isinstance(counts, dict):
        named = [f"{int(v)} {_plain_count_key(k)}"
                 for k, v in counts.items()
                 if isinstance(v, (int, float)) and v]
        if named:
            parts.append(_sentence(
                "On its live record it counts " + ", ".join(named[:4])))
    elif isinstance(accrual.get("forecasts"), (int, float)):
        parts.append(_sentence(
            f"On its live record it has {int(accrual['forecasts'])} "
            f"forecasts on file and {int(accrual.get('grades') or 0)} "
            f"graded so far"))
    gauge_files = (rs.get("gauge_history") or {}).get("files")
    if isinstance(gauge_files, dict) and gauge_files:
        parts.append(_sentence(
            f"Its gauge history on file holds "
            f"{sum(int(v) for v in gauge_files.values())} past readings "
            f"across {len(gauge_files)} gauges"))
    missing = (rs.get("missing") or {}).get("what_and_when")
    if missing:
        parts.append(_sentence(missing))
    return " ".join(parts)


def _plain_count_key(key):
    return str(key).replace("_", " ")


def build_explanation(slug, data):
    if slug == "market-mood":
        summary = MARKET_MOOD_SUMMARY
    else:
        summary = jobline_for(slug)
    if not summary:
        return None
    engines, rules = _registry()
    eng_id = _engine_for(slug)
    entry = next((e for e in engines if e.get("id") == eng_id), None)
    if entry is not None:
        body = engine_body(entry, rules, summary)
    else:
        body = tool_body(slug, data, summary)
    if not body:
        return None
    return {"summary": summary, "body": body}


def enrich_file(path):
    path = Path(path)
    slug = path.parent.name
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        return False
    block = build_explanation(slug, data)
    if block is None:
        return False
    data["explanation"] = block
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)
    return True


def enrich_slug(slug):
    path = HERE / slug / "data.json"
    if path.exists():
        return enrich_file(path)
    return False


if __name__ == "__main__":
    import sys
    for slug in sys.argv[1:]:
        print(slug, enrich_slug(slug))
