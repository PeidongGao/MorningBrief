import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from morningbrief import config


class ConfigTests(unittest.TestCase):
    def write_config(self, directory: str, state_key: str = "MB_STATE_DIR") -> Path:
        root = Path(directory)
        path = root / "config.env"
        path.write_text(
            "\n".join(
                [
                    f"MB_CODEX_REPO={root / 'workspace'}",
                    f"MB_VAULT_DIR={root / 'input'}",
                    f"{state_key}={root / 'state'}",
                    f"MB_DATA_ROOT={root / 'data'}",
                ]
            )
        )
        return path

    def test_loads_typed_settings_from_explicit_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {}, clear=True
        ):
            path = self.write_config(directory)

            settings = config.load_settings(path)

            self.assertIsInstance(settings, config.Settings)
            self.assertEqual(settings.state_dir, Path(directory) / "state")
            self.assertEqual(settings.sessions_root, Path.home() / ".codex" / "sessions")
            self.assertEqual(settings.config_file, path)

    def test_environment_overrides_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(directory)
            override = Path(directory) / "override-state"
            with patch.dict(os.environ, {"MB_STATE_DIR": str(override)}, clear=False):
                settings = config.load_settings(path)

            self.assertEqual(settings.state_dir, override)

    def test_legacy_memory_key_remains_supported(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {}, clear=True
        ):
            path = self.write_config(directory, "MB_AUTOMATION_MEMORY_DIR")

            settings = config.load_settings(path)

            self.assertEqual(settings.state_dir, Path(directory) / "state")


if __name__ == "__main__":
    unittest.main()
