"""Regression blockers for the 2026-10-29 G17 refresh-pipeline cures
(cure stream A: G1/G2/G15/G17).

Fail directions, each proven against the pre-cure code:
- grading.grade_forecast did a bare `import ledger`, which resolves
  to the wrong module (or none) whenever grading is imported as
  forecast.grading from a process whose script directory is not
  forecast/ (Engine 15's refresh died with "module 'ledger' has no
  attribute 'LedgerError'"). The subprocess test below imports it
  exactly that way and grades a scratch forecast.
- refresh_record attached the cohort grade block to the first
  day-group only, so once a second day matured no group carried
  grades while the totals published 66; its map cards_waiting was
  published as None and crashed Horizon Grades (int + NoneType).
  Source assertions pin the per-group reconciliation and the
  waiting-count derivation.
- refresh_horizongrades refused a record with grades on more than
  one day-group and bound the graded-so-far total to the Board
  block alone. Source assertions pin the aggregation.
- refresh_voltermshape hard-pinned the panel at 399 sessions, so
  the G2 panel advance froze it. Source assertion pins the
  panel-derived count.
- morgue/studies_card.main never fetched daily bars for its wall
  validation, so wall_validation.json graded 0 cards on every live
  run while the scorecard graded 9. Source assertion pins the fetch.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LINEUP = os.path.expanduser("~/workspace/terminal-lineup")
SITE = os.path.join(LINEUP, "site")


def _src(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as fh:
        return fh.read()


def test_grading_importable_as_package_from_site_cwd(tmp_path):
    code = (
        "import sys, os, json, tempfile\n"
        f"sys.path.insert(0, {LINEUP!r})\n"
        "from forecast import grading, ledger as L, registry as R\n"
        "reg = R.load()\n"
        "tmp = tempfile.mkdtemp()\n"
        "led = L.Ledger(os.path.join(tmp, 'l.jsonl'), registry=reg)\n"
        "led.append_genesis('t')\n"
        "clocks = {c: '2026-10-20T13:00:00Z' for c in L.CLOCK_FIELDS}\n"
        "lin = {'source_artifacts': [{'path': 'f.json', 'sha256': 'ab'*32}], 'clocks': clocks}\n"
        "row, _ = led.append_forecast(engine_id='engine_02', issued_ts='2026-10-20T13:00:00Z', subject='TEST', quantity='touch_probability', value={'p': 0.8}, horizon_open='2026-10-21', horizon_close='2026-10-23', lineage=lin, families=['price'], outcome={'symbol': 'TEST', 'kind': 'touch', 'level': 106.0, 'window_open': '2026-10-21', 'window_close': '2026-10-23', 'at_date': '2026-10-23'})\n"
        "class P:\n"
        "    path = 'fixture'\n"
        "    bars = {'TEST': {'2026-10-21': (100.0, 107.0, 99.0, 101.0), '2026-10-23': (101.0, 103.0, 100.0, 102.0)}}\n"
        "    calendars = {'TEST': ['2026-10-21', '2026-10-23']}\n"
        "    volumes = {'TEST': {}}\n"
        "    def has_session(self, s, d): return d in self.bars.get(s, {})\n"
        "    def bar(self, s, d): return self.bars[s][d]\n"
        "    def close(self, s, d): return self.bars[s][d][3]\n"
        "    def window(self, s, a, b): return [(d, self.bars[s][d]) for d in self.calendars[s] if a <= d <= b]\n"
        "grades = grading.run_grading(led, P(), reg)\n"
        "assert len(grades) == 1, grades\n"
        "print('GRADED_OK')\n")
    r = subprocess.run([sys.executable, "-c", code], cwd=SITE,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "GRADED_OK" in r.stdout


def test_record_per_group_reconciliation_present():
    src = _src("refresh_record.py")
    assert "group_returns" in src
    assert "do not reconcile" in src
    assert 'g is groups[0]' not in src


def test_record_cards_waiting_never_none():
    src = _src("refresh_record.py")
    assert "cards_pending" in src and "n_map - " in src


def test_horizongrades_aggregates_groups():
    src = _src("refresh_horizongrades.py")
    assert "more than one day-group" not in src
    assert 'record["map"]["cards_graded"]' in src


def test_voltermshape_panel_derived_count():
    src = _src("refresh_voltermshape.py")
    assert "expected_sessions = len(panel.get(\"SPY\")" in src
    assert "expected 399" not in src


def test_studies_card_fetches_wall_bars():
    with open(os.path.expanduser("~/workspace/morgue/studies_card.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert "sc.fetch_daily(" in src


def test_record_groups_reconcile_on_final_data():
    with open(os.path.join(SITE, "record", "data.json"),
              encoding="utf-8") as fh:
        rec = json.load(fh)
    graded = sum(g["grades"]["1d"].get("graded_count", 0)
                 for g in rec["board"]["groups"])
    rose = sum(g["grades"]["1d"].get("rose_count", 0)
               for g in rec["board"]["groups"])
    assert graded == rec["totals"]["outcomes_so_far"]["graded_count"]
    assert rose == rec["totals"]["outcomes_so_far"]["rose_count"]
    assert rec["map"]["cards_waiting"] is not None
    assert rec["map"]["cards_graded"] + rec["map"]["cards_waiting"] \
        == rec["totals"]["map_calls"]
