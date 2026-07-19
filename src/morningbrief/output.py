"""Parse a final Morning Brief written by ``codex exec``."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


SCAN_INTS_RE = re.compile(r"scan:\s*(\d+)\D+?(\d+)\D+?(\d+)", re.IGNORECASE)
_EMPHASIS_CHARS = "*_#`>-+ "


class OutputError(RuntimeError):
    """Raised when Codex does not produce a usable final response."""


@dataclass(frozen=True)
class ParsedOutput:
    text: str
    scan_line: Optional[str]
    scan_counts: Optional[Tuple[int, int, int]]


def find_scan_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.strip(_EMPHASIS_CHARS).lower().startswith("scan:"):
            return line.strip()
    return None


def parse_scan_counts(scan_line: str) -> Optional[Tuple[int, int, int]]:
    match = SCAN_INTS_RE.search(scan_line)
    if not match:
        return None
    return tuple(int(group) for group in match.groups())


def read_final_output(path: Path) -> ParsedOutput:
    if not path.is_file():
        raise OutputError(f"Codex did not write its final response to {path}")
    text = path.read_text().strip()
    if not text:
        raise OutputError(f"Codex wrote an empty final response to {path}")
    scan_line = find_scan_line(text)
    return ParsedOutput(
        text=text,
        scan_line=scan_line,
        scan_counts=parse_scan_counts(scan_line) if scan_line else None,
    )
