"""Maintain history.csv, the canonical index of generated Morning Briefs.

Rows are keyed by date: a successful run replaces any existing row for that
date (no duplicates); a failed run is recorded only when the date has no row
yet, so a failed re-run never clobbers an earlier success.
"""

import csv
import os
import tempfile
from pathlib import Path
from typing import Dict, List

COLUMNS = [
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
        return [dict(row) for row in csv.DictReader(stream)]


def _write_rows(history_csv: Path, rows: List[Dict[str, str]]) -> None:
    """Atomically replace history.csv via a temp file in the same directory,
    so an interrupted write can never truncate the canonical index."""
    history_csv.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=history_csv.parent, prefix=f".{history_csv.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=COLUMNS, extrasaction="ignore"
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, "") for col in COLUMNS})
        os.replace(tmp_path, history_csv)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def upsert_row(history_csv: Path, row: Dict[str, str]) -> None:
    """Insert the row, replacing any existing row with the same date."""
    rows = [r for r in load_rows(history_csv) if r.get("date") != row["date"]]
    rows.append(row)
    rows.sort(key=lambda r: r.get("date", ""))
    _write_rows(history_csv, rows)


def record_failure(history_csv: Path, row: Dict[str, str]) -> bool:
    """Record a failed run only if the date has no row yet. Returns True if
    the row was written."""
    if any(r.get("date") == row["date"] for r in load_rows(history_csv)):
        return False
    upsert_row(history_csv, row)
    return True
