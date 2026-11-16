#!/usr/bin/env python3
"""Regression blocker: MEMORY-INDEX-ROOTS-20261113.

Failure class: the local BM25 recall index omitted
~/workspace/COMMITMENTS.md from its roots. COMMITMENTS is a primary
shared register, so a fresh session could read the file directly but
could not recall its rows through the estate search tool.

Cure pinned here: the commitments register is an explicit index root,
is yielded by the file iterator, and is present in the built index.
"""
import os
import sqlite3
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import memory_search as ms  # noqa: E402


COMMITMENTS = os.path.join(HERE, "..", "COMMITMENTS.md")
COMMITMENTS = os.path.abspath(COMMITMENTS)


class MemoryIndexRoots(unittest.TestCase):
    def test_commitments_register_is_an_index_root(self):
        self.assertIn(COMMITMENTS, [os.path.abspath(p) for p in ms.ROOTS])

    def test_commitments_register_is_iterated(self):
        paths = [os.path.abspath(p) for p in ms.iter_files()]
        self.assertIn(COMMITMENTS, paths)

    def test_commitments_register_is_in_built_index(self):
        db = os.path.join(HERE, "memory_index.db")
        self.assertTrue(os.path.exists(db), "memory index has not been built")
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            row = con.execute(
                "select count(*) from chunks where path = ?",
                (COMMITMENTS,),
            ).fetchone()
        finally:
            con.close()
        self.assertGreater(row[0], 0)


if __name__ == "__main__":
    unittest.main()
