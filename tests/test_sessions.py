import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from morningbrief import sessions


def write_rollout(path: Path, text: str, phase: str = "final_answer") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": phase,
                    "content": [{"type": "output_text", "text": text}],
                },
            }
        )
        + "\n"
    )


class SessionTests(unittest.TestCase):
    def test_matches_exact_final_response_and_ignores_unrelated_rollout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session_dir = root / "2026" / "07" / "20"
            unrelated = session_dir / "rollout-unrelated.jsonl"
            expected = session_dir / "rollout-morningbrief.jsonl"
            write_rollout(unrelated, "Another task")
            write_rollout(expected, "Morning brief\nScan: 4 | 1 | 0")

            result = sessions.find_matching_rollout(
                root,
                [date(2026, 7, 20)],
                0,
                "Morning brief\nScan: 4 | 1 | 0",
            )

            self.assertEqual(result.rollout_path, expected)
            self.assertEqual(result.session_dir, session_dir)

    def test_raises_when_no_rollout_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_rollout(
                root / "2026" / "07" / "20" / "rollout-other.jsonl",
                "Other final response",
            )

            with self.assertRaises(sessions.SessionLookupError):
                sessions.find_matching_rollout(
                    root, [date(2026, 7, 20)], 0, "Morning brief"
                )


if __name__ == "__main__":
    unittest.main()
