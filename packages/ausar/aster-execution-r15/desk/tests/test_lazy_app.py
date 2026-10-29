import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class LazyAppTests(unittest.TestCase):
    def test_importing_factory_never_initializes_default_operating_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'default.sqlite'
            environment = {**os.environ, 'ASTER_DB_PATH':str(path)}
            script = "from backend.app import create_app, app; import json; from pathlib import Path; import os; print(json.dumps({'exists':Path(os.environ['ASTER_DB_PATH']).exists(),'default_constructed':app._application is not None}))"
            result = subprocess.run([sys.executable,'-c',script], env=environment,
                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=20, check=True)
            self.assertEqual(json.loads(result.stdout), {'exists':False,'default_constructed':False})
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_lazy_default_remains_a_usable_asgi_app_without_funding(self):
        from fastapi.testclient import TestClient
        from backend.app import _LazyDefaultApp
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'ASTER_DB_PATH':str(Path(tmp)/'main.sqlite')}):
            app = _LazyDefaultApp()
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/strategies').json(), [])
                view = client.get('/api/prospective').json()
                self.assertFalse(view['native']['installed'])
                self.assertFalse(view['public_recipes']['installed'])
                self.assertFalse(view['original_research']['installed'])
                self.assertEqual(client.get('/api/desk').json()['account']['cash'], 0)


if __name__=='__main__':
    unittest.main()
