"""Read-only configuration and environment diagnostics."""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .config import Settings
from .state import MEMORY_FILENAME


@dataclass(frozen=True)
class Check:
    level: str
    label: str
    detail: str


def _directory(path: Path, label: str, writable: bool = False) -> Check:
    if not path.exists():
        return Check("error", label, f"directory not found: {path}")
    if not path.is_dir():
        return Check("error", label, f"not a directory: {path}")
    mode = os.R_OK | (os.W_OK if writable else 0)
    if not os.access(path, mode):
        requirement = "read/write" if writable else "read"
        return Check("error", label, f"directory is not {requirement} accessible: {path}")
    return Check("ok", label, str(path))


def _file(path: Path, label: str) -> Check:
    if not path.is_file():
        return Check("error", label, f"file not found: {path}")
    if not os.access(path, os.R_OK):
        return Check("error", label, f"file is not readable: {path}")
    return Check("ok", label, str(path))


def _output_root(path: Path) -> Check:
    if path.exists():
        return _directory(path, "Output data", writable=True)
    parent = path.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if parent.is_dir() and os.access(parent, os.W_OK):
        return Check("ok", "Output data", f"will be created under writable {parent}")
    return Check("error", "Output data", f"cannot create output directory: {path}")


def inspect(settings: Settings) -> List[Check]:
    binary = shutil.which(settings.codex_binary)
    checks = [
        Check("ok" if binary else "error", "Codex CLI", binary or f"not found: {settings.codex_binary}"),
        _directory(settings.codex_workspace, "Codex workspace"),
        _file(settings.prompt_file, "Prompt"),
        _directory(settings.input_dir, "Input directory"),
        _directory(settings.state_dir, "State directory", writable=True),
        _file(settings.state_dir / MEMORY_FILENAME, "Operational memory"),
        _output_root(settings.data_root),
    ]
    if settings.config_file:
        checks.insert(0, Check("ok", "Configuration", str(settings.config_file)))
    else:
        checks.insert(0, Check("ok", "Configuration", "environment variables"))
    return checks


def errors(checks: List[Check]) -> List[Check]:
    return [check for check in checks if check.level == "error"]
