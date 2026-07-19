"""Invoke Codex and capture the exact final response for this run."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .config import Settings


@dataclass(frozen=True)
class CodexRun:
    exit_code: int
    command: List[str]
    output_path: Path


def build_command(settings: Settings, output_path: Path) -> List[str]:
    return [
        settings.codex_binary,
        "exec",
        "--skip-git-repo-check",
        "--add-dir",
        str(settings.input_dir),
        "--add-dir",
        str(settings.state_dir),
        "--output-last-message",
        str(output_path),
        "-C",
        str(settings.codex_workspace),
        "-",
    ]


def run_codex(settings: Settings, output_path: Path) -> CodexRun:
    command = build_command(settings, output_path)
    with settings.prompt_file.open("rb") as prompt:
        result = subprocess.run(command, stdin=prompt)
    return CodexRun(result.returncode, command, output_path)
