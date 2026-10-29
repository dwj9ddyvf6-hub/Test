import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.prospective_projection import prospective_snapshot


class ProspectiveProjectionTests(unittest.TestCase):
    def test_missing_companions_never_create_install_or_fund(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            result = prospective_snapshot(Path(tmp)/'main.sqlite')
            self.assertTrue(result['paper_only'])
            self.assertEqual(list(Path(tmp).iterdir()), [])
            for name in ('native','public_recipes','original_research'):
                self.assertEqual(result[name]['books'], [])
                self.assertFalse(result[name]['installed'])

    def test_corrupt_companion_is_unavailable_not_empty_or_healthy(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            path = Path(tmp)/'public-recipes.sqlite'
            path.write_bytes(b'corrupt journal')
            result = prospective_snapshot(Path(tmp)/'main.sqlite')
            self.assertEqual(result['public_recipes']['status'], 'unavailable')
            self.assertIsNone(result['public_recipes']['installed'])
            self.assertEqual(path.read_bytes(), b'corrupt journal')

    def test_explicit_paths_are_read_only_and_do_not_fall_into_main_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            external = Path(tmp)/'external.sqlite'
            with patch.dict(os.environ, {'ASTER_NATIVE_DB_PATH':str(external)}, clear=True):
                result = prospective_snapshot(Path(tmp)/'main.sqlite')
            self.assertFalse(result['native']['installed'])
            self.assertFalse(external.exists())


if __name__ == '__main__':
    unittest.main()
