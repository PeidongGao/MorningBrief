import tempfile
import unittest
from pathlib import Path

from morningbrief import history


def row(run_id: str, date: str = "2026-07-19", status: str = "success") -> dict:
    return {
        "run_id": run_id,
        "date": date,
        "report_path": f"/reports/{run_id}.md",
        "rollout_path": "",
        "session_dir": "",
        "scan_total_markdown": "10",
        "scan_changed": "2",
        "scan_need_attention": "1",
        "status": status,
        "created_at": f"{date}T08:00:00-04:00",
    }


class HistoryTests(unittest.TestCase):
    def test_append_preserves_multiple_runs_on_same_date(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.csv"
            history.append_row(path, row("run-one"))
            history.append_row(path, row("run-two"))

            rows = history.load_rows(path)

            self.assertEqual([item["run_id"] for item in rows], ["run-one", "run-two"])

    def test_duplicate_run_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.csv"
            history.append_row(path, row("same"))

            with self.assertRaises(ValueError):
                history.append_row(path, row("same"))

    def test_old_schema_loads_with_empty_run_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.csv"
            path.write_text("date,status,created_at\n2026-07-18,success,2026-07-18T08:00:00\n")

            rows = history.load_rows(path)

            self.assertEqual(rows[0]["run_id"], "")
            self.assertEqual(rows[0]["status"], "success")


if __name__ == "__main__":
    unittest.main()
