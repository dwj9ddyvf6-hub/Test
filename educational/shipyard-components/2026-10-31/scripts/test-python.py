from pathlib import Path
import sys, unittest
root = Path(__file__).resolve().parent.parent
component = root / "deploy" / "python-research-service"
sys.path.insert(0, str(component))
suite = unittest.defaultTestLoader.discover(str(component / "tests"))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
