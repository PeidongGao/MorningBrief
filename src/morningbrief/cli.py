"""Command-line interface for MorningBrief."""

import argparse
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import config, demo, doctor, runner, state


def _err(message: str) -> None:
    print(f"mb: error: {message}", file=sys.stderr)


def _settings(config_path: Optional[Path]) -> config.Settings:
    return config.load_settings(config_path)


def run_command(settings: config.Settings) -> int:
    print("=== mb run: generating Morning Brief via configured Codex workflow ===")
    print(f"Prompt: {settings.prompt_file}")
    print()
    try:
        result = runner.run(settings)
    except runner.RunError as exc:
        _err(str(exc))
        for warning in exc.warnings:
            print(f"mb: warning: {warning}", file=sys.stderr)
        return 1

    if result.scan_line is None:
        print("mb: warning: final response has no Scan line", file=sys.stderr)
    elif result.scan_counts is None:
        print(
            f"mb: warning: Scan counts could not be parsed: {result.scan_line!r}",
            file=sys.stderr,
        )

    print()
    print("=== Final Morning Brief ===")
    print(result.final_text)
    print()
    print("=== Saved ===")
    print(f"Run ID:      {result.run_id}")
    print(f"Report:      {result.report_path}")
    print(f"History:     {settings.history_csv}")
    return 0


def doctor_command(settings: config.Settings) -> int:
    checks = doctor.inspect(settings)
    for check in checks:
        marker = "OK" if check.level == "ok" else "ERROR"
        print(f"[{marker}] {check.label}: {check.detail}")
    failures = doctor.errors(checks)
    if failures:
        print(f"\nDoctor found {len(failures)} problem(s).")
        return 2
    print("\nMorningBrief is ready.")
    return 0


def init_command(state_dir: Path) -> int:
    path, created = state.initialize(state_dir, datetime.now().astimezone())
    if created:
        print(f"Created operational memory: {path}")
    else:
        print(f"Operational memory already exists; left unchanged: {path}")
    print("Configure MB_STATE_DIR with this directory:")
    print(state_dir)
    return 0


def serve_command(settings) -> int:
    try:
        import streamlit  # noqa: F401
    except ImportError:
        _err("streamlit is not installed in this environment")
        return 2

    app_path = Path(__file__).parent / "serve" / "app.py"
    if not app_path.exists():
        _err(f"Streamlit app not found: {app_path}")
        return 2

    environment = os.environ.copy()
    environment["MORNINGBRIEF_READER_DATA_ROOT"] = str(settings.data_root)
    if settings.config_file:
        environment["MORNINGBRIEF_CONFIG"] = str(settings.config_file)
    print("=== mb serve: launching Morning Brief reader (read-only) ===")
    print(f"Data: {settings.data_root}")
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        env=environment,
    )
    if result.returncode in (-signal.SIGINT, 130):
        print("MorningBrief reader closed.")
        return 0
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mb",
        description="MorningBrief — run and browse a local Codex briefing workflow.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a MorningBrief environment-style configuration file",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser(
        "run", help="Generate and save a new Morning Brief"
    )
    run_parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate from bundled fictional inputs without private configuration",
    )
    doctor_parser = subparsers.add_parser(
        "doctor", help="Validate configuration without generating"
    )
    doctor_parser.add_argument(
        "--demo",
        action="store_true",
        help="Validate the self-contained fictional demo workflow",
    )
    init_parser = subparsers.add_parser(
        "init", help="Safely create operational memory without overwriting it"
    )
    init_parser.add_argument(
        "--state-dir", type=Path, help="Operational state directory to initialize"
    )
    serve_parser = subparsers.add_parser(
        "serve", help="Launch the read-only local reader"
    )
    serve_parser.add_argument(
        "--demo",
        action="store_true",
        help="Browse the public sample data without configuration",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            state_dir = config.resolve_state_dir(args.state_dir, args.config)
            return init_command(state_dir)
        if getattr(args, "demo", False):
            if args.command == "serve":
                return serve_command(demo.demo_reader_settings())
            settings = (
                demo.doctor_settings()
                if args.command == "doctor"
                else demo.prepare_settings()
            )
        else:
            settings = _settings(args.config)
        if args.command == "run":
            return run_command(settings)
        if args.command == "doctor":
            return doctor_command(settings)
        if args.command == "serve":
            return serve_command(settings)
    except KeyboardInterrupt:
        print(f"\nmb: {args.command} interrupted", file=sys.stderr)
        return 130
    except (config.ConfigError, OSError) as exc:
        _err(str(exc))
        return 2
    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
