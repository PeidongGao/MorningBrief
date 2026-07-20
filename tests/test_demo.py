import re
import tempfile
import unittest
from pathlib import Path

from morningbrief import demo


class DemoTests(unittest.TestCase):
    def test_public_vault_uses_generic_layout(self):
        vault = demo.DEMO_ROOT / "vault"
        files = list(vault.rglob("*.md"))

        self.assertEqual(len(files), 12)
        self.assertEqual(
            {path.relative_to(vault).parts[0] for path in files},
            {"notes", "operations", "organization", "projects", "updates"},
        )

    def test_public_demo_contains_no_private_structure_or_paths(self):
        blocked = re.compile(
            r"/Users/|/home/|[A-Z]:\\Users\\|\.codex/",
            re.IGNORECASE,
        )
        public_files = [
            path
            for path in demo.DEMO_ROOT.rglob("*")
            if path.is_file()
            and "runtime" not in path.relative_to(demo.DEMO_ROOT).parts
            and path.name != ".DS_Store"
        ]

        findings = [
            str(path.relative_to(demo.DEMO_ROOT))
            for path in public_files
            if blocked.search(path.read_text())
        ]
        self.assertEqual(findings, [])

    def test_doctor_settings_do_not_create_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            settings = demo.doctor_settings(root)

            self.assertEqual(settings.state_dir, root.resolve() / "seed")
            self.assertIsNone(settings.sessions_root)
            self.assertFalse((root / "runtime").exists())

    def test_prepare_settings_seeds_runtime_memory_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "seed").mkdir()
            (root / "seed" / "memory.md").write_text("seed memory\n")
            (root / "prompt.md").write_text("prompt\n")
            (root / "vault").mkdir()

            settings = demo.prepare_settings(root)
            memory = settings.state_dir / "memory.md"
            self.assertEqual(memory.read_text(), "seed memory\n")
            self.assertIsNone(settings.sessions_root)

            memory.write_text("updated by a run\n")
            demo.prepare_settings(root)
            self.assertEqual(memory.read_text(), "updated by a run\n")

    def test_reader_prefers_generated_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_settings = demo.demo_reader_settings(root)
            self.assertEqual(seed_settings.data_root, root.resolve())

            generated = root / "runtime" / "data"
            generated.mkdir(parents=True)
            (generated / "history.csv").write_text("run_id\n")

            generated_settings = demo.demo_reader_settings(root)
            self.assertEqual(generated_settings.data_root, generated.resolve())


if __name__ == "__main__":
    unittest.main()
