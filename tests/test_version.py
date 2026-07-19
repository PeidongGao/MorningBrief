import unittest
from pathlib import Path

import morningbrief


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_package_and_project_versions_match_release(self):
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()

        self.assertEqual(morningbrief.__version__, "2.1.0")
        self.assertIn('version = "2.1.0"', pyproject)


if __name__ == "__main__":
    unittest.main()
