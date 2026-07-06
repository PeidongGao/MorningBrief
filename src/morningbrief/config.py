"""Configuration for MorningBrief.

All machine-specific paths live in a `.env` file at the project root — copy
`.env.example` to `.env` and fill in your paths. The file is git-ignored so
personal paths never enter version control.

Lookup order for each MB_* key: OS environment variable, then the `.env`
file, then the built-in default (required keys have no default). Values
support a leading `~`. Set MORNINGBRIEF_CONFIG to use a config file at a
different location.

Settings are loaded lazily on first attribute access (config.CODEX_REPO,
config.HISTORY_CSV, ...), so importing this module — e.g. for `mb --help` —
never requires a config file.
"""

import os
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when the config file is missing or incomplete."""


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_FILE = PROJECT_ROOT / ".env"
EXAMPLE_CONFIG_FILE = PROJECT_ROOT / ".env.example"


def config_file_path() -> Path:
    override = os.environ.get("MORNINGBRIEF_CONFIG")
    return Path(override).expanduser() if override else DEFAULT_CONFIG_FILE


def _parse_env_file(path: Path) -> dict:
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _load() -> dict:
    path = config_file_path()
    if not path.is_file():
        raise ConfigError(
            f"config file not found: {path} — copy "
            f"{EXAMPLE_CONFIG_FILE} to {DEFAULT_CONFIG_FILE} and fill in "
            "your paths (or set MORNINGBRIEF_CONFIG to a config file)"
        )
    file_values = _parse_env_file(path)

    def raw(key, default=None):
        value = os.environ.get(key)
        if value is None:
            value = file_values.get(key)
        if value is None or value == "":
            value = default
        return value

    def path_value(key, default=None):
        value = raw(key, default)
        if value is None:
            raise ConfigError(f"required key {key} is not set in {path}")
        return Path(value).expanduser()

    codex_repo = path_value("MB_CODEX_REPO")
    data_root = path_value("MB_DATA_ROOT", "~/Documents/MorningBriefData")
    return {
        # existing automation (wrapped, never modified)
        "CODEX_REPO": codex_repo,
        "PROMPT_FILE": path_value(
            "MB_PROMPT_FILE",
            str(codex_repo / "prompts" / "reusable" / "morning-brief-prompt.md"),
        ),
        "VAULT_DIR": path_value("MB_VAULT_DIR"),
        "AUTOMATION_MEMORY_DIR": path_value("MB_AUTOMATION_MEMORY_DIR"),
        "SESSIONS_ROOT": path_value("MB_SESSIONS_ROOT", "~/.codex/sessions"),
        # generated data (owned by MorningBrief; layout below the root is fixed)
        "DATA_ROOT": data_root,
        "REPORTS_DIR": data_root / "reports" / "daily",
        "HISTORY_CSV": data_root / "history.csv",
        "CODEX_BINARY": raw("MB_CODEX_BINARY", "codex"),
    }


def __getattr__(name):
    settings = _load()
    if name in settings:
        globals().update(settings)  # cache: later access skips re-reading .env
        return settings[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
