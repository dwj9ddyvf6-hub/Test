#!/usr/bin/env python3
"""Regression blocker: HUB-ATOMIC-WRITE-RACE-20261110.

At 11:20 ET on 2026-11-10 the hourly lane failed with
FileNotFoundError renaming index.html.atomic-tmp ->
index.html. refresh_hub._atomic_write used a FIXED temp
name (path.name + ".atomic-tmp"), so two concurrent writer
processes shared one temp file: the first writer's
os.replace moved it away, and the second writer's rename
then found nothing (or the writers interleaved bytes in the
shared temp and corrupted the target).

The cure keeps the same-directory + os.replace design but
gives each process its own temp name,
"<name>.<pid>.atomic-tmp", which still ends with
".atomic-tmp" so sync_to_test.py's exclusion of that suffix
keeps working, and cleans the temp up on failure.

Concurrency here means concurrent PROCESSES (the incident
class: overlapping hourly-lane instances): threads inside
one process share a pid, so this blocker drives two child
processes, barrier-synchronised per round, writing
complete payloads to the same target. Each child also
delays its rename by a fixed pause (inside a wrapped
os.replace) so the exact live interleaving is reproduced
deterministically rather than by timing luck: writer 1's
temp is fully written and waiting to rename while writer
2 writes its own temp; writer 1 then renames, and writer
2's rename follows.

Fail-first: on the fixed-tmp code both children write the
SAME temp path, so writer 1's rename moves writer 2's
temp away and writer 2's rename raises FileNotFoundError
(the live 11:20 ET failure), in the first round. On the
cured code each child renames its own per-process temp,
both succeed every round, and the final file is one
writer's complete text.

Run standalone: python3 test_refresh_hub_atomic_write_20261110.py
(exit 0 = pass), or under pytest.
"""
import multiprocessing as mp
import os
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))

import refresh_hub as hub  # noqa: E402

ROUNDS = 8
SIZE = 65536


def _payload(char: str, rnd: int) -> str:
    return char * SIZE + f"<end-{char}-{rnd}>"


def _worker(target: str, char: str, barrier, queue) -> None:
    import time as _time
    real_replace = os.replace

    def slow_replace(src, dst):
        # Hold the written temp un-renamed briefly so the
        # other writer's write lands inside the window the
        # live incident hit (see the module docstring).
        _time.sleep(0.3)
        return real_replace(src, dst)

    hub.os.replace = slow_replace
    try:
        for rnd in range(ROUNDS):
            barrier.wait(timeout=30)
            hub._atomic_write(Path(target), _payload(char, rnd))
    except Exception as e:  # report, never die silently
        queue.put(f"{type(e).__name__}: {e}")
        try:
            barrier.abort()
        except Exception:
            pass
    else:
        queue.put(None)


def test_single_write_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "index.html"
        hub._atomic_write(target, "hello hub\n")
        assert target.read_text(encoding="utf-8") == "hello hub\n"
        assert list(Path(td).glob("*.atomic-tmp")) == []


def test_tmp_name_is_per_process_and_keeps_suffix():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "index.html"
        seen = []
        real_replace = os.replace

        def capturing_replace(src, dst):
            seen.append(Path(src).name)
            return real_replace(src, dst)

        orig = hub.os.replace
        hub.os.replace = capturing_replace
        try:
            hub._atomic_write(target, "x")
        finally:
            hub.os.replace = orig
        assert len(seen) == 1
        name = seen[0]
        assert name.endswith(".atomic-tmp"), name
        assert name != "index.html.atomic-tmp", name
        assert f".{os.getpid()}." in name, name


def test_concurrent_process_writes_both_succeed():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "index.html"
        target.write_text("seed\n", encoding="utf-8")
        ctx = mp.get_context("fork")
        barrier = ctx.Barrier(2)
        queue = ctx.Queue()
        procs = [ctx.Process(target=_worker,
                             args=(str(target), char, barrier, queue))
                 for char in ("A", "B")]
        for p in procs:
            p.start()
        results = [queue.get(timeout=300) for _ in procs]
        for p in procs:
            p.join(timeout=60)
        assert results == [None, None], results
        assert all(p.exitcode == 0 for p in procs), \
            [p.exitcode for p in procs]
        final = target.read_text(encoding="utf-8")
        assert final in (_payload("A", ROUNDS - 1),
                         _payload("B", ROUNDS - 1)), \
            f"final content is no writer's complete text: {final[:80]!r}... len={len(final)}"
        assert list(Path(td).glob("*.atomic-tmp")) == []


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
