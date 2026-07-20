"""Locate the Codex rollout that produced an already captured final response."""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional


class SessionLookupError(RuntimeError):
    """Raised when a matching Codex rollout cannot be identified."""


@dataclass(frozen=True)
class SessionMetadata:
    rollout_path: Path
    session_dir: Path


def _message_text(payload: dict) -> str:
    if (
        payload.get("type") != "message"
        or payload.get("role") != "assistant"
        or payload.get("phase") != "final_answer"
    ):
        return ""
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        item["text"]
        for item in content
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    )


def _final_response(path: Path) -> Optional[str]:
    final = None
    with path.open() as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = _message_text(item.get("payload", {}))
            if text:
                final = text
    return final


def find_matching_rollout(
    sessions_root: Path,
    dates: Iterable[date],
    start_time: float,
    final_text: str,
) -> SessionMetadata:
    """Find a fresh rollout whose final answer exactly matches ``final_text``."""
    directories = []
    for run_date in dates:
        directory = sessions_root / run_date.strftime("%Y/%m/%d")
        if directory not in directories:
            directories.append(directory)

    candidates = []
    for directory in directories:
        if directory.is_dir():
            candidates.extend(directory.glob("rollout-*.jsonl"))
    fresh = [path for path in candidates if path.stat().st_mtime >= start_time - 2]
    fresh.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    expected = final_text.strip()
    for path in fresh:
        try:
            actual = _final_response(path)
        except OSError:
            continue
        if actual is not None and actual.strip() == expected:
            return SessionMetadata(rollout_path=path, session_dir=path.parent)

    searched = ", ".join(str(path) for path in directories)
    raise SessionLookupError(
        f"no fresh rollout with the captured final response was found in: {searched}"
    )
