"""mb — the MorningBrief CLI.

Commands:

    mb run     Generate today's Morning Brief via the configured Codex
               workflow, save it into the data directory, and update history.csv.
    mb serve   Launch the read-only Streamlit reader for saved reports.
"""

import argparse
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

from . import config, history, rollout, workflow


def _err(message: str) -> None:
    print(f"mb: error: {message}", file=sys.stderr)


def _preflight() -> bool:
    """Verify required paths and the codex binary; create data directories."""
    ok = True
    required = [
        (config.CODEX_REPO, "Codex workflow repository"),
        (config.PROMPT_FILE, "Morning Brief prompt file"),
        (config.VAULT_DIR, "Obsidian vault"),
        (config.AUTOMATION_MEMORY_DIR, "codex automation memory directory"),
    ]
    for path, label in required:
        if not path.exists():
            _err(f"{label} not found: {path}")
            ok = False
    if shutil.which(config.CODEX_BINARY) is None:
        _err(
            f"'{config.CODEX_BINARY}' binary not found on PATH — "
            "is the codex CLI installed in this environment?"
        )
        ok = False
    if ok:
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return ok


def _failure_row(run_date: date, status: str, session_dir: Path = None) -> dict:
    return {
        "date": run_date.isoformat(),
        "report_path": "",
        "rollout_path": "",
        "session_dir": str(session_dir) if session_dir else "",
        "scan_total_markdown": "",
        "scan_changed": "",
        "scan_need_attention": "",
        "status": status,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def run_command() -> int:
    if not _preflight():
        return 2

    start_time = time.time()
    start_date = date.today()

    print("=== mb run: generating Morning Brief via configured Codex workflow ===")
    print(f"Prompt: {config.PROMPT_FILE}")
    print()

    exit_code = workflow.run_codex()

    end_date = date.today()
    run_dates = [start_date] if start_date == end_date else [start_date, end_date]

    if exit_code != 0:
        history.record_failure(
            config.HISTORY_CSV, _failure_row(end_date, "generation_failed")
        )
        _err(
            f"codex exec exited with code {exit_code} — no report saved. "
            f"Check the codex output above and {config.SESSIONS_ROOT}"
        )
        return 1

    try:
        completed = rollout.find_completed_rollout(
            config.SESSIONS_ROOT, run_dates, start_time
        )
    except rollout.RolloutError as exc:
        history.record_failure(
            config.HISTORY_CSV, _failure_row(end_date, "extraction_failed")
        )
        _err(str(exc))
        return 1

    report_path = config.REPORTS_DIR / f"{end_date.isoformat()}.md"
    text = completed.final_text
    report_path.write_text(text if text.endswith("\n") else text + "\n")

    if completed.scan_counts is None:
        print(
            "mb: warning: Scan line found but its counts could not be parsed: "
            f"{completed.scan_line!r}",
            file=sys.stderr,
        )
        total, changed, attention = "", "", ""
    else:
        total, changed, attention = completed.scan_counts

    history.upsert_row(
        config.HISTORY_CSV,
        {
            "date": end_date.isoformat(),
            "report_path": str(report_path),
            "rollout_path": str(completed.rollout_path),
            "session_dir": str(completed.session_dir),
            "scan_total_markdown": str(total),
            "scan_changed": str(changed),
            "scan_need_attention": str(attention),
            "status": "success",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )

    print()
    print("=== Final Morning Brief ===")
    print(completed.final_text)
    print()
    print("=== Saved ===")
    print(f"Report:      {report_path}")
    print(f"Rollout:     {completed.rollout_path}")
    print(f"History:     {config.HISTORY_CSV}")
    return 0


def serve_command() -> int:
    """Launch the read-only Streamlit reader. Never generates reports."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        _err(
            "streamlit is not installed in this environment — reinstall the "
            f"package to pull it in: pip install -e {config.PROJECT_ROOT}"
        )
        return 2

    app_path = Path(__file__).parent / "serve" / "app.py"
    if not app_path.exists():
        _err(f"Streamlit app not found: {app_path}")
        return 2

    print(f"=== mb serve: launching Morning Brief reader (read-only) ===")
    print(f"Data: {config.DATA_ROOT}")
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)]
    )
    return result.returncode


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mb",
        description="MorningBrief — wrapper around a local Codex Morning Brief "
        "workflow.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "run",
        help="Generate today's Morning Brief, save it, and update history.csv",
    )
    subparsers.add_parser(
        "serve",
        help="Launch the read-only local reader interface (Streamlit)",
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            return run_command()
        if args.command == "serve":
            return serve_command()
    except KeyboardInterrupt:
        print(f"\nmb: {args.command} interrupted", file=sys.stderr)
        return 130
    except config.ConfigError as exc:
        _err(str(exc))
        return 2
    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
