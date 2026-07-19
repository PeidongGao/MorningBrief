import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from morningbrief import reports, state


class ReportAndStateTests(unittest.TestCase):
    def test_atomic_report_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            reports.atomic_write_new(path, "first")

            with self.assertRaises(FileExistsError):
                reports.atomic_write_new(path, "second")

            self.assertEqual(path.read_text(), "first\n")

    def test_init_never_overwrites_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "state"
            moment = datetime(2026, 7, 19, tzinfo=timezone.utc)
            path, created = state.initialize(state_dir, moment)
            original = path.read_text()
            path_two, created_two = state.initialize(state_dir, moment)

            self.assertTrue(created)
            self.assertFalse(created_two)
            self.assertEqual(path, path_two)
            self.assertEqual(path.read_text(), original)

    def test_snapshot_restore_recovers_previous_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            path = state_dir / "memory.md"
            path.write_text("before")
            snapshot = state.snapshot(state_dir)
            path.write_text("after")

            state.restore(snapshot)

            self.assertEqual(path.read_text(), "before")


if __name__ == "__main__":
    unittest.main()
