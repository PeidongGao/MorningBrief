"""End-to-end MorningBrief run orchestration."""

import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from . import doctor, history, output, reports, sessions, state, workflow
from .config import Settings


class RunError(RuntimeError):
    def __init__(self, message: str, warnings: Optional[List[str]] = None):
        super().__init__(message)
        self.warnings = warnings or []


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    report_path: Path
    final_text: str
    scan_line: Optional[str]
    scan_counts: Optional[Tuple[int, int, int]]
    created_at: str
    warnings: Tuple[str, ...] = ()


def _failure_row(run_id: str, moment: datetime, status: str) -> dict:
    return {
        "run_id": run_id,
        "date": moment.date().isoformat(),
        "report_path": "",
        "rollout_path": "",
        "session_dir": "",
        "scan_total_markdown": "",
        "scan_changed": "",
        "scan_need_attention": "",
        "status": status,
        "created_at": moment.isoformat(timespec="seconds"),
    }


def _record_failure(settings: Settings, row: dict) -> List[str]:
    try:
        history.record_failure(settings.history_csv, row)
        return []
    except (OSError, ValueError) as exc:
        return [f"could not record failed run in history: {exc}"]


def run(settings: Settings, moment: Optional[datetime] = None) -> RunOutcome:
    checks = doctor.inspect(settings)
    failures = doctor.errors(checks)
    if failures:
        raise RunError("preflight failed: " + "; ".join(check.detail for check in failures))

    started = (moment or datetime.now().astimezone()).astimezone()
    run_id = reports.new_run_id(started)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    memory = state.snapshot(settings.state_dir)

    metadata = None
    run_warnings = []
    with tempfile.TemporaryDirectory(prefix=".mb-run-", dir=settings.data_root) as directory:
        output_path = Path(directory) / "final.md"
        try:
            codex_run = workflow.run_codex(settings, output_path)
        except OSError as exc:
            state.restore(memory)
            warnings = _record_failure(
                settings, _failure_row(run_id, started, "generation_failed")
            )
            raise RunError(f"could not launch Codex: {exc}", warnings) from exc

        if codex_run.exit_code != 0:
            state.restore(memory)
            warnings = _record_failure(
                settings, _failure_row(run_id, started, "generation_failed")
            )
            raise RunError(f"codex exec exited with code {codex_run.exit_code}", warnings)

        try:
            parsed = output.read_final_output(output_path)
        except (OSError, output.OutputError) as exc:
            state.restore(memory)
            warnings = _record_failure(
                settings, _failure_row(run_id, started, "extraction_failed")
            )
            raise RunError(str(exc), warnings) from exc

        if settings.sessions_root is not None:
            finished = datetime.now().astimezone()
            run_dates = [started.date()]
            if finished.date() != started.date():
                run_dates.append(finished.date())
            try:
                metadata = sessions.find_matching_rollout(
                    settings.sessions_root,
                    run_dates,
                    started.timestamp(),
                    parsed.text,
                )
            except (OSError, sessions.SessionLookupError) as exc:
                run_warnings.append(f"could not record Codex session metadata: {exc}")

    destination = reports.report_path(settings.reports_dir, run_id)
    try:
        reports.atomic_write_new(destination, parsed.text)
    except OSError as exc:
        state.restore(memory)
        warnings = _record_failure(
            settings, _failure_row(run_id, started, "report_write_failed")
        )
        raise RunError(f"could not save report: {exc}", warnings) from exc

    total, changed, attention = parsed.scan_counts or ("", "", "")
    row = {
        "run_id": run_id,
        "date": started.date().isoformat(),
        "report_path": str(destination),
        "rollout_path": str(metadata.rollout_path) if metadata else "",
        "session_dir": str(metadata.session_dir) if metadata else "",
        "scan_total_markdown": str(total),
        "scan_changed": str(changed),
        "scan_need_attention": str(attention),
        "status": "success",
        "created_at": started.isoformat(timespec="seconds"),
    }
    try:
        history.append_row(settings.history_csv, row)
    except (OSError, ValueError) as exc:
        state.restore(memory)
        raise RunError(
            f"report was preserved at {destination}, but history update failed: {exc}"
        ) from exc

    return RunOutcome(
        run_id=run_id,
        report_path=destination,
        final_text=parsed.text,
        scan_line=parsed.scan_line,
        scan_counts=parsed.scan_counts,
        created_at=row["created_at"],
        warnings=tuple(run_warnings),
    )
