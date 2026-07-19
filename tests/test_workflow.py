import tempfile
import unittest
from pathlib import Path

from morningbrief.config import Settings
from morningbrief.workflow import build_command


class WorkflowTests(unittest.TestCase):
    def test_command_captures_exact_final_message(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = Settings(
                codex_workspace=root / "workspace",
                prompt_file=root / "prompt.md",
                input_dir=root / "input",
                state_dir=root / "state",
                data_root=root / "data",
                reports_dir=root / "data" / "reports" / "daily",
                history_csv=root / "data" / "history.csv",
                codex_binary="codex",
            )
            output_path = root / "final.md"

            command = build_command(settings, output_path)

            self.assertIn("--output-last-message", command)
            self.assertEqual(command[command.index("--output-last-message") + 1], str(output_path))
            self.assertNotIn("--json", command)


if __name__ == "__main__":
    unittest.main()
