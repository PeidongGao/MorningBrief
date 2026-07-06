"""Locate the completed Morning Brief rollout and extract the final report.

Native port of the locator logic used by the external Morning Brief automation
(which stays untouched as the reference implementation), with two hardenings:

* mtime cutoff — only rollouts written at/after this run's start time are
  eligible, so a stale rollout from an earlier session is never re-reported.
* tolerant Scan-line parsing — the Scan line is LLM-generated text; matching
  strips markdown emphasis and does not depend on the exact wording between
  the three numbers.
"""

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

SCAN_INTS_RE = re.compile(r"scan:\s*(\d+)\D+?(\d+)\D+?(\d+)", re.IGNORECASE)
_EMPHASIS_CHARS = "*_#`> "


class RolloutError(RuntimeError):
    """Raised when no completed Morning Brief rollout can be found/parsed."""


@dataclass
class CompletedRollout:
    session_dir: Path
    rollout_path: Path
    final_text: str
    scan_line: str
    scan_counts: Optional[Tuple[int, int, int]]  # None if Scan line unparseable


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for item in content:
        if isinstance(item, dict) and item.get("text"):
            parts.append(item["text"])
    return "\n".join(parts)


def extract_final_answer(rollout_path: Path) -> Optional[str]:
    """Return the last assistant final_answer text in the rollout, or None."""
    final = None
    with rollout_path.open() as stream:
        for line in stream:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate a partially written trailing line
            payload = obj.get("payload", {})
            if (
                payload.get("type") == "message"
                and payload.get("role") == "assistant"
                and payload.get("phase") == "final_answer"
            ):
                final = _content_text(payload.get("content"))
    return final


def find_scan_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.strip(_EMPHASIS_CHARS).lower().startswith("scan:"):
            return line.strip()
    return None


def parse_scan_counts(scan_line: str) -> Optional[Tuple[int, int, int]]:
    match = SCAN_INTS_RE.search(scan_line)
    if not match:
        return None
    return tuple(int(g) for g in match.groups())


def _session_dirs(sessions_root: Path, dates: Iterable[date]) -> List[Path]:
    dirs = []
    for d in dates:
        candidate = sessions_root / d.strftime("%Y/%m/%d")
        if candidate not in dirs:
            dirs.append(candidate)
    return dirs


def find_completed_rollout(
    sessions_root: Path, dates: Iterable[date], start_time: float
) -> CompletedRollout:
    """Find the newest rollout created by this run that contains a completed
    Morning Brief (an assistant final_answer with a Scan line).

    `dates` should cover the local dates at run start and finish, so a run
    crossing midnight is still found. `start_time` is the epoch time recorded
    just before codex was launched; a 2-second slack absorbs filesystem
    timestamp granularity.
    """
    session_dirs = _session_dirs(sessions_root, dates)
    candidates = []
    for session_dir in session_dirs:
        if session_dir.is_dir():
            candidates.extend(session_dir.glob("rollout-*.jsonl"))

    if not candidates:
        raise RolloutError(
            "No rollout files found in: "
            + ", ".join(str(d) for d in session_dirs)
        )

    fresh = [p for p in candidates if p.stat().st_mtime >= start_time - 2]
    if not fresh:
        raise RolloutError(
            f"Found {len(candidates)} rollout file(s), but none newer than this "
            "run's start time — the codex run may not have produced a session. "
            "Searched: " + ", ".join(str(d) for d in session_dirs)
        )

    fresh.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    for rollout_path in fresh:
        final = extract_final_answer(rollout_path)
        if not final:
            continue
        scan_line = find_scan_line(final)
        if not scan_line:
            continue
        return CompletedRollout(
            session_dir=rollout_path.parent,
            rollout_path=rollout_path,
            final_text=final,
            scan_line=scan_line,
            scan_counts=parse_scan_counts(scan_line),
        )

    raise RolloutError(
        "No completed Morning Brief found: none of the "
        f"{len(fresh)} rollout(s) from this run contains an assistant "
        "final_answer with a Scan line. Newest candidate: " + str(fresh[0])
    )
