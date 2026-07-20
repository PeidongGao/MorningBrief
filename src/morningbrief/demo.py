"""Self-contained public demo configuration and runtime initialization."""

from datetime import datetime
from pathlib import Path

from . import config, state


DEMO_ROOT = config.PROJECT_ROOT / "MorningBriefDataDemo"
RUNTIME_DIRECTORY = "runtime"


def _settings(root: Path, state_dir: Path) -> config.Settings:
    data_root = root / RUNTIME_DIRECTORY / "data"
    return config.Settings(
        codex_workspace=root,
        prompt_file=root / "prompt.md",
        input_dir=root / "vault",
        state_dir=state_dir,
        data_root=data_root,
        reports_dir=data_root / "reports" / "daily",
        history_csv=data_root / "history.csv",
        codex_binary="codex",
        sessions_root=None,
    )


def doctor_settings(root: Path = DEMO_ROOT) -> config.Settings:
    """Return read-only validation settings backed by the public seed state."""
    root = root.resolve()
    return _settings(root, root / "seed")


def prepare_settings(root: Path = DEMO_ROOT) -> config.Settings:
    """Create private-like demo runtime state without touching the seed fixtures."""
    root = root.resolve()
    runtime_root = root / RUNTIME_DIRECTORY
    state_dir = runtime_root / "state"
    memory_path = state_dir / state.MEMORY_FILENAME
    state_dir.mkdir(parents=True, exist_ok=True)

    if not memory_path.exists():
        seed_memory = root / "seed" / state.MEMORY_FILENAME
        if seed_memory.is_file():
            try:
                with memory_path.open("xb") as stream:
                    stream.write(seed_memory.read_bytes())
            except FileExistsError:
                pass
        else:
            state.initialize(state_dir, datetime.now().astimezone())

    return _settings(root, state_dir)


def demo_reader_settings(root: Path = DEMO_ROOT) -> config.ReaderSettings:
    """Read generated demo runs when present, otherwise show the seed report."""
    generated_root = root.resolve() / RUNTIME_DIRECTORY / "data"
    if (generated_root / "history.csv").is_file():
        return config.reader_settings(generated_root)
    return config.reader_settings(root.resolve())
