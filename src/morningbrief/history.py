"""Append-only history index with atomic CSV replacement."""

import csv
import os
import tempfile
from pathlib import Path
from typing import Dict, List


COLUMNS = [
    "run_id",
    "date",
    "report_path",
    "rollout_path",
    "session_dir",
    "scan_total_markdown",
    "scan_changed",
    "scan_need_attention",
    "status",
    "created_at",
]


def load_rows(history_csv: Path) -> List[Dict[str, str]]:
    if not history_csv.exists():
        return []
    with history_csv.open(newline="") as stream:
        return [
            {column: row.get(column, "") or "" for column in COLUMNS}
            for row in csv.DictReader(stream)
        ]


def _write_rows(history_csv: Path, rows: List[Dict[str, str]]) -> None:
    """Atomically replace history.csv without truncating a valid index."""
    history_csv.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        dir=history_csv.parent, prefix=f".{history_csv.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in COLUMNS})
        os.replace(temporary_path, history_csv)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def append_row(history_csv: Path, row: Dict[str, str]) -> None:
    """Append one immutable run record and reject duplicate run IDs."""
    run_id = row.get("run_id", "")
    if not run_id:
        raise ValueError("history row requires run_id")
    rows = load_rows(history_csv)
    if any(existing.get("run_id") == run_id for existing in rows):
        raise ValueError(f"history already contains run_id {run_id}")
    rows.append({column: row.get(column, "") for column in COLUMNS})
    rows.sort(key=lambda item: (item.get("created_at", ""), item.get("run_id", "")))
    _write_rows(history_csv, rows)


def record_failure(history_csv: Path, row: Dict[str, str]) -> bool:
    append_row(history_csv, row)
    return True
