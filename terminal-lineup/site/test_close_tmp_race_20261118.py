#!/usr/bin/env python3
"""Regression blocker: CLOSE-TMP-RACE-20261118.

On 2026-11-18 the hourly lane FAILED at 15:21Z, 17:21Z and
18:21Z and the intraday lane FAILED at 17:21Z and 18:21Z, always
in the close steps, always with the same signature:
FileNotFoundError renaming a FIXED temp name onto its target
(data.json.tmp -> data.json in record_surface/explanation via
enrich_all; asset-manifest.json.tmp -> asset-manifest.json in
terminal_common's manifest sync). The hourly lane (:21) and the
intraday lane (every 5 min) run the identical close()
concurrently; with one shared temp name per target, the first
writer's os.replace moves the temp away and the second writer's
rename finds nothing. A third symptom in the 18:21Z run, a desk
JSON parse error inside enrich_all, was the same concurrency
class from the other side: publish_desk wrote desk/data.json
with a truncating write_text while the other lane's enrich was
reading it.

The cure (2026-11-18): terminal_common.atomic_write_text writes
through a UNIQUE mkstemp temp in the target's directory, and
record_surface.enrich_file, explanation.enrich_file,
terminal_common.write_data_json, the manifest sync and
publish_desk's writes/copies all go through unique-temp atomic
writes (refresh_book_strip's per-process temp likewise).

Fail-first: on the pre-cure code terminal_common has no
atomic_write_text (the unit tests fail on the missing helper),
and the concurrent-process tests reproduce the live failure:
both children enrich/write the SAME target with a delayed
rename, the shared fixed temp is moved away by writer 1, and
writer 2 raises FileNotFoundError in the first round.

Run standalone: python3 test_close_tmp_race_20261118.py
(exit 0 = pass), or under pytest.
"""
import json
import multiprocessing as mp
import os
import shutil
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))
os.environ.setdefault("TERMINAL_NO_MANIFEST_SYNC", "1")

import terminal_common as tc  # noqa: E402

ROUNDS = 6
SIZE = 65536


def _payload(char: str, rnd: int) -> str:
    return char * SIZE + f"<end-{char}-{rnd}>"


def _slow_replace_factory(real_replace):
    import time as _time

    def slow_replace(src, dst):
        _time.sleep(0.3)
        return real_replace(src, dst)
    return slow_replace


def _write_worker(target: str, char: str, barrier, queue) -> None:
    tc.os.replace = _slow_replace_factory(os.replace)
    try:
        for rnd in range(ROUNDS):
            barrier.wait(timeout=30)
            tc.atomic_write_text(target, _payload(char, rnd))
    except Exception as e:
        queue.put(f"{type(e).__name__}: {e}")
        try:
            barrier.abort()
        except Exception:
            pass
    else:
        queue.put(None)


def _enrich_worker(target: str, seed_text: str, char: str,
                   barrier, queue) -> None:
    import explanation
    import record_surface
    slow = _slow_replace_factory(os.replace)
    # The rename delay must sit in whichever module performs the
    # replace: post-cure that is terminal_common (the shared
    # writer); pre-cure it was each enrich module itself.
    tc.os.replace = slow
    record_surface.os.replace = slow
    explanation.os.replace = slow
    path = Path(target)
    try:
        for rnd in range(ROUNDS):
            barrier.wait(timeout=30)
            # Reseed with round-unique content (via the cured
            # writer) so enrich has a real change to publish
            # every round instead of short-circuiting unchanged.
            data = json.loads(seed_text)
            data["race_round"] = f"{char}-{rnd}"
            tc.atomic_write_text(
                path, json.dumps(data, indent=2, sort_keys=True) + "\n")
            barrier.wait(timeout=30)
            record_surface.enrich_file(path)
            explanation.enrich_file(path)
    except Exception as e:
        queue.put(f"{type(e).__name__}: {e}")
        try:
            barrier.abort()
        except Exception:
            pass
    else:
        queue.put(None)


def _run_pair(worker, args_a, args_b):
    ctx = mp.get_context("fork")
    barrier = ctx.Barrier(2)
    queue = ctx.Queue()
    procs = [ctx.Process(target=worker, args=(*args, barrier, queue))
             for args in (args_a, args_b)]
    for p in procs:
        p.start()
    results = [queue.get(timeout=300) for _ in procs]
    for p in procs:
        p.join(timeout=60)
    assert results == [None, None], results
    assert all(p.exitcode == 0 for p in procs), [p.exitcode for p in procs]


def test_atomic_write_roundtrip_and_unique_temps():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "data.json"
        seen = []
        real_replace = os.replace

        def capturing_replace(src, dst):
            seen.append(Path(src).name)
            return real_replace(src, dst)

        orig = tc.os.replace
        tc.os.replace = capturing_replace
        try:
            tc.atomic_write_text(target, "one\n")
            tc.atomic_write_text(target, "two\n")
        finally:
            tc.os.replace = orig
        assert target.read_text(encoding="utf-8") == "two\n"
        assert len(seen) == 2 and seen[0] != seen[1], seen
        assert all(n.endswith(".tmp") for n in seen), seen
        assert all(n != "data.json.tmp" for n in seen), seen
        assert list(Path(td).glob("*.tmp")) == []


def test_write_data_json_uses_unique_tmp():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "data.json"
        seen = []
        real_replace = os.replace

        def capturing_replace(src, dst):
            seen.append(Path(src).name)
            return real_replace(src, dst)

        orig = tc.os.replace
        tc.os.replace = capturing_replace
        try:
            tc.write_data_json(target, {"a": 1},
                               feed="filed_records",
                               price_basis="session_record")
        finally:
            tc.os.replace = orig
        assert json.loads(target.read_text())["a"] == 1
        assert len(seen) == 1 and seen[0] != "data.json.tmp", seen


def test_source_has_no_fixed_tmp_in_close_writers():
    rs = (SITE / "record_surface.py").read_text()
    ex = (SITE / "explanation.py").read_text()
    assert 'with_suffix(".json.tmp")' not in rs
    assert 'with_suffix(".json.tmp")' not in ex
    common = (SITE / "terminal_common.py").read_text()
    assert '_MANIFEST_PATH + ".tmp"' not in common
    assert 'str(path) + ".tmp"' not in common
    desk = (SITE / "publish_desk.py").read_text()
    assert '(dest / "data.json").write_text(' not in desk


def test_concurrent_atomic_writes_both_succeed():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "data.json"
        target.write_text("seed\n", encoding="utf-8")
        _run_pair(_write_worker, (str(target), "A"), (str(target), "B"))
        final = target.read_text(encoding="utf-8")
        assert final in (_payload("A", ROUNDS - 1),
                         _payload("B", ROUNDS - 1)), \
            f"final content is no writer's complete text: {final[:80]!r}"
        assert list(Path(td).glob("*.tmp")) == []


def test_concurrent_enrich_both_succeed():
    seed = (SITE / "desk" / "data.json").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        page_dir = Path(td) / "desk"
        page_dir.mkdir()
        target = page_dir / "data.json"
        target.write_text(seed, encoding="utf-8")
        _run_pair(_enrich_worker,
                  (str(target), seed, "A"), (str(target), seed, "B"))
        final = json.loads(target.read_text(encoding="utf-8"))
        assert "record_surface" in final, \
            "enriched record_surface block missing from final file"
        assert list(page_dir.glob("*.tmp")) == []
        assert list(page_dir.glob(".*.tmp")) == []


def test_publish_desk_writes_are_atomic():
    src = (SITE / "publish_desk.py").read_text()
    assert "_atomic_write_text" in src and "_copy_atomic" in src
    assert "shutil.copyfile(src, out)" not in src
    # The desk page copy in a temp tree publishes complete files.
    import publish_desk as pd
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "desk"
        dest.mkdir()
        fsrc = Path(td) / "terminal_feed.json"
        feed = {"account": {"equity": 1.0}, "strategies": [],
                "generated_at": "2026-11-18T00:00:00Z",
                "evidence_packet": {}}
        fsrc.write_text(json.dumps(feed), encoding="utf-8")
        out = dest / "terminal_feed.json"
        pd._copy_atomic(fsrc, out)
        assert json.loads(out.read_text()) == feed
        pd._atomic_write_text(dest / "data.json", "{}\n")
        assert (dest / "data.json").read_text() == "{}\n"
        assert list(dest.glob("*.tmp")) == []
        assert list(dest.glob(".*.tmp")) == []


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
