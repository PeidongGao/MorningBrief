"""Invoke the existing WillGaoLabCodex Morning Brief workflow via `codex exec`.

This module only launches the existing automation; it never modifies it.
"""

import subprocess

from . import config


def run_codex() -> int:
    """Run the Morning Brief generation. Returns the codex exit code.

    Codex output is inherited by the terminal so the user sees live progress.
    The prompt is piped via stdin (the trailing "-" argument), which is why no
    cd into the repo is needed.
    """
    cmd = [
        config.CODEX_BINARY,
        "exec",
        "--skip-git-repo-check",
        "--add-dir",
        str(config.VAULT_DIR),
        "--add-dir",
        str(config.AUTOMATION_MEMORY_DIR),
        "-C",
        str(config.CODEX_REPO),
        "-",
    ]
    with config.PROMPT_FILE.open("rb") as prompt:
        result = subprocess.run(cmd, stdin=prompt)
    return result.returncode
