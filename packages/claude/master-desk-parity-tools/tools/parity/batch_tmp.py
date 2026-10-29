"""A parity batch's temp root, owned by the harness process.

The source side of a batch runs in a child process (tools.parity.old_run). Its sqlite journals, per-case temp
directories and any Node scratch land under TMPDIR, which points at a directory created and removed here. The
harness process removes it in a finally block, so nothing is left behind when a case raises, the child times out,
or the child is killed (a killed child never reaches its own finally)."""
import contextlib
import os
import shutil
import tempfile


@contextlib.contextmanager
def batch_tmp(prefix):
    tempfile.gettempdir()          # this process keeps its own temp root; only the child's TMPDIR moves
    d = tempfile.mkdtemp(prefix=prefix)
    old = os.environ.get("TMPDIR")
    os.environ["TMPDIR"] = d
    try:
        yield d
    finally:
        if old is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = old
        shutil.rmtree(d, ignore_errors=True)


@contextlib.contextmanager
def case_tmp():
    """one in-process case's temp directory, removed when the case ends however it ends."""
    d = tempfile.mkdtemp()
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)
