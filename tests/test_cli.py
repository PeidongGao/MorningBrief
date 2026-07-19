import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from morningbrief import cli, config


class CliTests(unittest.TestCase):
    @patch("morningbrief.cli.serve_command", return_value=0)
    def test_serve_demo_uses_repository_sample_without_configuration(self, serve):
        with patch.dict("os.environ", {}, clear=True):
            result = cli.main(["serve", "--demo"])

        self.assertEqual(result, 0)
        settings = serve.call_args.args[0]
        self.assertEqual(
            settings.data_root, config.PROJECT_ROOT / "MorningBriefDataDemo"
        )

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
