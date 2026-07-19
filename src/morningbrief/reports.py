"""Non-destructive, atomic report storage."""

import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path


def new_run_id(moment: datetime) -> str:
    timestamp = moment.astimezone().strftime("%Y%m%dT%H%M%S%z")
    return f"{timestamp}_{uuid.uuid4().hex[:8]}"


def report_path(reports_dir: Path, run_id: str) -> Path:
    return reports_dir / f"{run_id}.md"


def atomic_write_new(path: Path, text: str) -> None:
    """Atomically create a file and refuse to replace an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text if text.endswith("\n") else text + "\n")
        os.link(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
