import tempfile
import unittest
from pathlib import Path

from morningbrief import output


class OutputTests(unittest.TestCase):
    def test_accepts_markdown_emphasis_before_scan(self):
        line = output.find_scan_line(
            "Brief\n- **Scan: 59 markdown files | 2 changed | 3 need attention**"
        )

        self.assertIsNotNone(line)
        self.assertEqual(output.parse_scan_counts(line), (59, 2, 3))

    def test_reads_exact_final_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "final.md"
            path.write_text("Brief\nScan: 3 files | 1 changed | 0 need attention\n")

            parsed = output.read_final_output(path)

            self.assertEqual(parsed.text, "Brief\nScan: 3 files | 1 changed | 0 need attention")
            self.assertEqual(parsed.scan_counts, (3, 1, 0))

    def test_scan_line_is_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "final.md"
            path.write_text("A useful brief without metrics")

            parsed = output.read_final_output(path)

            self.assertIsNone(parsed.scan_line)
            self.assertIsNone(parsed.scan_counts)


if __name__ == "__main__":
    unittest.main()
