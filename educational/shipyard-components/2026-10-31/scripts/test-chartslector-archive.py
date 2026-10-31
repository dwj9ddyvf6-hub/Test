#!/usr/bin/env python3
"""Run synthetic checks for selected owner-supplied ChartsLector archive references."""
from pathlib import Path
import sys, unittest
root=Path(__file__).resolve().parent.parent
suite=unittest.defaultTestLoader.discover(str(root/"tests"), pattern="test_chartslector_archive_reference.py")
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
