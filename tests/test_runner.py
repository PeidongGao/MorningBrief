import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from morningbrief import history, runner, state, workflow
from morningbrief.config import Settings


class RunnerTests(unittest.TestCase):
    def settings(self, root: Path) -> Settings:
        workspace = root / "workspace"
        input_dir = root / "input"
        state_dir = root / "state"
        workspace.mkdir()
        input_dir.mkdir()
        state.initialize(state_dir, datetime(2026, 7, 19, tzinfo=timezone.utc))
        prompt = workspace / "prompt.md"
        prompt.write_text("Generate a brief")
        data_root = root / "data"
        return Settings(
            codex_workspace=workspace,
            prompt_file=prompt,
            input_dir=input_dir,
            state_dir=state_dir,
            data_root=data_root,
            reports_dir=data_root / "reports" / "daily",
            history_csv=data_root / "history.csv",
            codex_binary=sys.executable,
        )

    def test_two_same_day_runs_are_both_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self.settings(Path(directory))
            moment = datetime(2026, 7, 19, 8, 0, tzinfo=timezone.utc)

            def fake_run(_settings, output_path):
                output_path.write_text("Brief\nScan: 10 files | 2 changed | 1 need attention")
                return workflow.CodexRun(0, [], output_path)

            with patch("morningbrief.runner.workflow.run_codex", side_effect=fake_run):
                first = runner.run(settings, moment)
                second = runner.run(settings, moment)

            rows = history.load_rows(settings.history_csv)
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(first.run_id, second.run_id)
            self.assertTrue(first.report_path.is_file())
            self.assertTrue(second.report_path.is_file())

    def test_failed_codex_run_restores_memory_and_records_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self.settings(Path(directory))
            memory_path = settings.state_dir / "memory.md"
            original = memory_path.read_text()

            def fake_failure(_settings, output_path):
                memory_path.write_text("partial mutation")
                return workflow.CodexRun(1, [], output_path)

            with patch("morningbrief.runner.workflow.run_codex", side_effect=fake_failure):
                with self.assertRaises(runner.RunError):
                    runner.run(
                        settings,
                        datetime(2026, 7, 19, 8, 0, tzinfo=timezone.utc),
                    )

            self.assertEqual(memory_path.read_text(), original)
            rows = history.load_rows(settings.history_csv)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "generation_failed")

    def test_real_subprocess_writes_output_last_message(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = self.settings(root)
            fake_codex = root / "fake-codex"
            fake_codex.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "arguments = sys.argv[1:]\n"
                "output = pathlib.Path(arguments[arguments.index('--output-last-message') + 1])\n"
                "sys.stdin.buffer.read()\n"
                "output.write_text('Subprocess brief\\nScan: 4 files | 1 changed | 0 need attention')\n"
            )
            fake_codex.chmod(0o755)
            settings = Settings(
                codex_workspace=settings.codex_workspace,
                prompt_file=settings.prompt_file,
                input_dir=settings.input_dir,
                state_dir=settings.state_dir,
                data_root=settings.data_root,
                reports_dir=settings.reports_dir,
                history_csv=settings.history_csv,
                codex_binary=str(fake_codex),
            )

            result = runner.run(
                settings, datetime(2026, 7, 19, 8, 0, tzinfo=timezone.utc)
            )

            self.assertEqual(result.scan_counts, (4, 1, 0))
            self.assertEqual(result.report_path.read_text().splitlines()[0], "Subprocess brief")


if __name__ == "__main__":
    unittest.main()
