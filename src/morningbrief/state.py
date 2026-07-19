"""Safe initialization and rollback support for operational memory."""

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


MEMORY_FILENAME = "memory.md"


@dataclass(frozen=True)
class MemorySnapshot:
    path: Path
    existed: bool
    content: bytes


def initialize(state_dir: Path, moment: datetime) -> tuple:
    """Create starter memory exactly once. Returns ``(path, created)``."""
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / MEMORY_FILENAME
    content = (
        "# Morning Brief Operational Memory\n\n"
        "## State Initialization\n\n"
        f"- Initialized: {moment.astimezone().isoformat(timespec='seconds')}\n"
        "- Status: Fresh operational state\n"
        "- Historical reconstruction: None\n\n"
        "## Memory Rules\n\n"
        "- Preserve existing run-history entries.\n"
        "- Append new run records rather than deleting prior records.\n"
        "- Do not infer or fabricate unavailable historical state.\n\n"
        "## Run History\n\n"
        "- Operational memory initialized; awaiting the first successful run.\n"
    )
    try:
        with path.open("x") as stream:
            stream.write(content)
    except FileExistsError:
        return path, False
    return path, True


def snapshot(state_dir: Path) -> MemorySnapshot:
    path = state_dir / MEMORY_FILENAME
    return MemorySnapshot(path, path.exists(), path.read_bytes() if path.exists() else b"")


def restore(memory: MemorySnapshot) -> None:
    """Atomically restore the pre-run memory after an unsuccessful run."""
    if not memory.existed:
        memory.path.unlink(missing_ok=True)
        return
    memory.path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=memory.path.parent, prefix=f".{memory.path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(memory.content)
        os.replace(temporary_path, memory.path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
