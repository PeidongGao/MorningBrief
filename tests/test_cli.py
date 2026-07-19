import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from morningbrief import cli, config


class CliTests(unittest.TestCase):
    @patch("morningbrief.cli.serve_command", return_value=0)
    @patch("morningbrief.cli.demo.demo_reader_settings")
    def test_serve_demo_uses_repository_sample_without_configuration(
        self, demo_reader, serve
    ):
        demo_reader.return_value = config.reader_settings(
            config.PROJECT_ROOT / "MorningBriefDataDemo"
        )
        with patch.dict("os.environ", {}, clear=True):
            result = cli.main(["serve", "--demo"])

        self.assertEqual(result, 0)
        demo_reader.assert_called_once_with()
        settings = serve.call_args.args[0]
        self.assertEqual(
            settings.data_root, config.PROJECT_ROOT / "MorningBriefDataDemo"
        )

    @patch("morningbrief.cli.runner.run")
    @patch("morningbrief.cli.demo.prepare_settings")
    def test_run_demo_uses_public_settings_without_configuration(self, prepare, run):
        with tempfile.TemporaryDirectory() as directory:
            settings = config.Settings(
                codex_workspace=Path(directory),
                prompt_file=Path(directory) / "prompt.md",
                input_dir=Path(directory) / "vault",
                state_dir=Path(directory) / "state",
                data_root=Path(directory) / "data",
                reports_dir=Path(directory) / "data" / "reports" / "daily",
                history_csv=Path(directory) / "data" / "history.csv",
                codex_binary="codex",
            )
            prepare.return_value = settings
            run.return_value.run_id = "demo-run"
            run.return_value.report_path = settings.reports_dir / "demo-run.md"
            run.return_value.final_text = "Demo brief"
            run.return_value.scan_line = (
                "Scan: 12 markdown files | 3 changed | 2 need attention"
            )
            run.return_value.scan_counts = (12, 3, 2)

            with patch.dict("os.environ", {}, clear=True):
                result = cli.main(["run", "--demo"])

        self.assertEqual(result, 0)
        prepare.assert_called_once_with()
        run.assert_called_once_with(settings)

    @patch("morningbrief.cli.doctor_command", return_value=0)
    @patch("morningbrief.cli.demo.doctor_settings")
    def test_doctor_demo_uses_read_only_seed_settings(self, demo_settings, doctor):
        with tempfile.TemporaryDirectory() as directory:
            settings = config.Settings(
                codex_workspace=Path(directory),
                prompt_file=Path(directory) / "prompt.md",
                input_dir=Path(directory) / "vault",
                state_dir=Path(directory) / "seed",
                data_root=Path(directory) / "runtime" / "data",
                reports_dir=Path(directory) / "runtime" / "data" / "reports",
                history_csv=Path(directory) / "runtime" / "data" / "history.csv",
                codex_binary="codex",
            )
            demo_settings.return_value = settings

            result = cli.main(["doctor", "--demo"])

        self.assertEqual(result, 0)
        demo_settings.assert_called_once_with()
        doctor.assert_called_once_with(settings)

    @patch("morningbrief.cli.subprocess.run")
    def test_serve_passes_reader_data_root_to_streamlit(self, run):
        run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as directory:
            settings = config.reader_settings(Path(directory))

            result = cli.serve_command(settings)

        self.assertEqual(result, 0)
        environment = run.call_args.kwargs["env"]
        self.assertEqual(
            environment["MORNINGBRIEF_READER_DATA_ROOT"], str(settings.data_root)
        )


if __name__ == "__main__":
    unittest.main()
