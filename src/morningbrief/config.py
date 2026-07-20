"""Typed, portable configuration for MorningBrief."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


class ConfigError(RuntimeError):
    """Raised when configuration is missing or invalid."""


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    codex_workspace: Path
    prompt_file: Path
    input_dir: Path
    state_dir: Path
    data_root: Path
    reports_dir: Path
    history_csv: Path
    codex_binary: str
    sessions_root: Optional[Path] = None
    config_file: Optional[Path] = None


@dataclass(frozen=True)
class ReaderSettings:
    data_root: Path
    history_csv: Path
    config_file: Optional[Path] = None


def reader_settings(data_root: Path) -> ReaderSettings:
    root = data_root.expanduser()
    return ReaderSettings(data_root=root, history_csv=root / "history.csv")


def user_config_file() -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
        return root / "MorningBrief" / "config.env"
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "MorningBrief" / "config.env"
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "morningbrief" / "config.env"


def user_state_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "MorningBrief" / "state"
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / "MorningBrief" / "state"
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "morningbrief"


def _parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def config_candidates() -> List[Path]:
    candidates = [PROJECT_ROOT / ".env", user_config_file(), Path.cwd() / ".env"]
    unique: List[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def config_file_path(explicit: Optional[Path] = None) -> Optional[Path]:
    requested = explicit
    if requested is None:
        override = os.environ.get("MORNINGBRIEF_CONFIG")
        requested = Path(override) if override else None
    if requested is not None:
        path = requested.expanduser()
        if not path.is_file():
            raise ConfigError(f"config file not found: {path}")
        return path
    return next((path for path in config_candidates() if path.is_file()), None)


def _source_values(config_path: Optional[Path] = None) -> tuple:
    source = config_file_path(config_path)
    return source, _parse_env_file(source) if source else {}


def load_settings(config_path: Optional[Path] = None) -> Settings:
    source, file_values = _source_values(config_path)

    def raw(key: str, default: Optional[str] = None) -> Optional[str]:
        value = os.environ.get(key)
        if value is None:
            value = file_values.get(key)
        return default if value is None or value == "" else value

    def required(key: str) -> str:
        value = raw(key)
        if value is None:
            location = str(source) if source else "environment or configuration file"
            raise ConfigError(f"required key {key} is not set in {location}")
        return value

    def path_value(key: str, default: Optional[str] = None) -> Path:
        value = raw(key, default)
        if value is None:
            raise ConfigError(f"required key {key} is not set")
        return Path(value).expanduser()

    workspace = Path(required("MB_CODEX_REPO")).expanduser()
    state_value = raw("MB_STATE_DIR") or raw("MB_AUTOMATION_MEMORY_DIR")
    if state_value is None:
        raise ConfigError(
            "required key MB_STATE_DIR is not set "
            "(MB_AUTOMATION_MEMORY_DIR remains supported for compatibility)"
        )
    data_root = path_value("MB_DATA_ROOT", "~/Documents/MorningBriefData")
    return Settings(
        codex_workspace=workspace,
        prompt_file=path_value(
            "MB_PROMPT_FILE",
            str(workspace / "prompts" / "reusable" / "morning-brief-prompt.md"),
        ),
        input_dir=Path(required("MB_VAULT_DIR")).expanduser(),
        state_dir=Path(state_value).expanduser(),
        data_root=data_root,
        reports_dir=data_root / "reports" / "daily",
        history_csv=data_root / "history.csv",
        codex_binary=raw("MB_CODEX_BINARY", "codex") or "codex",
        sessions_root=path_value("MB_SESSIONS_ROOT", "~/.codex/sessions").resolve(),
        config_file=source,
    )


def resolve_state_dir(
    requested: Optional[Path] = None, config_path: Optional[Path] = None
) -> Path:
    if requested is not None:
        return requested.expanduser()
    _, file_values = _source_values(config_path)
    for key in ("MB_STATE_DIR", "MB_AUTOMATION_MEMORY_DIR"):
        value = os.environ.get(key) or file_values.get(key)
        if value:
            return Path(value).expanduser()
    return user_state_dir()
