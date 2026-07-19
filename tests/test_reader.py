import os
import signal
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from morningbrief import history
from morningbrief import config
from morningbrief.config import Settings
from morningbrief.serve.app import (
    CLOSE_PAGE_HTML,
    load_history_rows,
    perform_confirmed_close,
    request_browser_close,
    request_server_shutdown,
    resolve_report_path,
    row_label,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA_ROOT = PROJECT_ROOT / "MorningBriefDataDemo"


class ReaderTests(unittest.TestCase):
    def test_demo_report_resolves_from_data_root_outside_clone_working_directory(self):
        settings = config.reader_settings(DEMO_DATA_ROOT)

        with tempfile.TemporaryDirectory() as directory:
            previous_directory = Path.cwd()
            try:
                os.chdir(directory)
                self.assertFalse(Path("reports/daily/demo.md").is_file())
                rows = load_history_rows(settings)
                path = resolve_report_path(
                    rows[0]["report_path"], settings.data_root
                )
            finally:
                os.chdir(previous_directory)

        self.assertEqual(
            path, DEMO_DATA_ROOT / "reports" / "daily" / "demo.md"
        )
        self.assertTrue(path.is_file())
        self.assertIn("# Morning Brief", path.read_text())
        self.assertEqual(rows[0]["run_id"], "demo_00000000")
        self.assertEqual(rows[0]["scan_total_markdown"], "12")

    def test_absolute_report_path_is_unchanged(self):
        absolute = DEMO_DATA_ROOT / "reports" / "daily" / "demo.md"

        self.assertEqual(resolve_report_path(absolute, Path("/elsewhere")), absolute)

    @patch("morningbrief.serve.app.request_server_shutdown")
    @patch("morningbrief.serve.app.request_browser_close")
    def test_confirmed_close_closes_page_then_server(self, browser_close, shutdown):
        perform_confirmed_close()

        browser_close.assert_called_once_with()
        shutdown.assert_called_once_with(delay_seconds=1.5)

    @patch("morningbrief.serve.app.components.html")
    def test_browser_close_requests_tab_close_with_blank_fallback(self, html):
        request_browser_close()

        html.assert_called_once_with(CLOSE_PAGE_HTML, height=80)
        self.assertIn("page.close()", CLOSE_PAGE_HTML)
        self.assertIn('page.location.replace("about:blank")', CLOSE_PAGE_HTML)

    @patch("morningbrief.serve.app.threading.Timer")
    @patch("morningbrief.serve.app.os.getpid", return_value=4321)
    def test_shutdown_schedules_sigint_for_streamlit_process(self, _getpid, timer):
        scheduled = timer.return_value

        request_server_shutdown(delay_seconds=0.25)

        timer.assert_called_once_with(
            0.25, os.kill, args=(4321, signal.SIGINT)
        )
        self.assertTrue(scheduled.daemon)
        scheduled.start.assert_called_once_with()

    def test_reader_distinguishes_legacy_and_new_same_day_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history_path = root / "history.csv"
            history_path.write_text(
                "date,report_path,status,created_at\n"
                "2026-07-19,/legacy.md,success,2026-07-19T08:00:00\n"
            )
            history.append_row(
                history_path,
                {
                    "run_id": "20260719T090000-0400_a1b2c3d4",
                    "date": "2026-07-19",
                    "report_path": "/new.md",
                    "status": "success",
                    "created_at": "2026-07-19T09:00:00-04:00",
                },
            )
            settings = Settings(
                codex_workspace=root,
                prompt_file=root / "prompt.md",
                input_dir=root,
                state_dir=root,
                data_root=root,
                reports_dir=root / "reports",
                history_csv=history_path,
                codex_binary="codex",
            )

            rows = load_history_rows(settings)

            self.assertEqual(len(rows), 2)
            self.assertIn("a1b2c3d4", row_label(rows[0]))
            self.assertIn("legacy", row_label(rows[1]))


if __name__ == "__main__":
    unittest.main()
