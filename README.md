# MorningBrief

MorningBrief is a local CLI and read-only report browser for repeatable
Codex-based briefing workflows. It runs a configured prompt, saves the exact
final response as Markdown, and records an append-only history of every run.

Private prompts, notes, operational memory, Codex sessions, and generated
reports stay outside this repository.

## What's New in v2.1

- Complete fictional workflow through `mb doctor --demo`, `mb run --demo`, and
  `mb serve --demo`
- Bundled 12-file public vault with a generic structure unrelated to private
  user workspaces
- Isolated, Git-ignored demo runtime for operational memory, generated reports,
  and history
- Read-only demo diagnostics and automatic reader selection of generated runs
- Privacy regression coverage and clean public-only end-to-end validation

Version 2.0 established the reliable application foundation: exact Codex final
message capture, atomic writes, non-destructive reruns, portable configuration,
private state initialization, diagnostics, and rollback on failed runs. See the
[changelog](CHANGELOG.md) for release details.

## Features

- Generate a briefing with `mb run`
- Browse saved successful and failed runs with `mb serve`
- Preserve each run with a unique ID instead of replacing same-day reports
- Validate configuration without generating through `mb doctor`
- Initialize private operational state without overwriting through `mb init`

## Requirements

The public demo requires Python 3.9 or newer. Generating your own reports also
requires the Codex CLI on `PATH`, a prompt, and an input directory that Codex
may access.

## Installation

```bash
git clone https://github.com/WillGaoLab/MorningBrief.git
cd MorningBrief
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Conda is also supported:

```bash
conda create -n morningbrief python=3.12 -y
conda activate morningbrief
pip install -e .
```

## Try the Demo

The repository includes fictional sample data. To browse the pre-generated
sample, no Codex installation, private files, or configuration is needed:

```bash
mb serve --demo
```

To demonstrate the complete workflow with the Codex CLI installed:

```bash
mb doctor --demo
mb run --demo
mb serve --demo
```

The v2.1 full demo uses the bundled fictional prompt, 12-file Markdown vault, and
seed operational memory. It ignores `.env` and writes only under the Git-ignored
`MorningBriefDataDemo/runtime/` directory. After generation, `mb serve --demo`
automatically opens the generated runtime history. See the
[full demo guide](MorningBriefDataDemo/README.md) for its file layout.

Use **Close MorningBrief** in the sidebar to stop the local server. Browser
security may replace the tab with a blank page instead of closing it.

## Configure Your Workflow

Create private operational memory:

```bash
mb init --state-dir /path/to/your/morningbrief-state
```

Copy the example configuration and replace its placeholder paths:

```bash
cp .env.example .env
```

```dotenv
MB_CODEX_REPO=/path/to/your/codex-workspace
MB_PROMPT_FILE=/path/to/your/prompt.md
MB_VAULT_DIR=/path/to/your/input-notes
MB_STATE_DIR=/path/to/your/morningbrief-state
MB_DATA_ROOT=/path/to/your/output-data
MB_CODEX_BINARY=codex
```

Validate the setup, generate a report, and open the reader:

```bash
mb doctor
mb run
mb serve
```

`mb init` never replaces an existing `memory.md`.
`MB_AUTOMATION_MEMORY_DIR` remains supported as the legacy name for
`MB_STATE_DIR`.

## Commands

```text
mb run           Generate and save a new briefing
mb run --demo    Generate from bundled fictional inputs
mb serve         Browse reports from the configured output directory
mb serve --demo  Browse sample or generated fictional demo runs
mb doctor        Validate configuration without generating
mb doctor --demo Validate the full fictional demo workflow
mb init          Create private operational memory safely
```

Use an explicit configuration from any working directory:

```bash
mb --config /path/to/config.env doctor
mb --config /path/to/config.env run
```

Environment variables override file values. MorningBrief discovers
configuration in this order:

1. `--config /path/to/config.env`
2. `MORNINGBRIEF_CONFIG`
3. `.env` beside an editable source installation
4. the platform user-config location
5. `.env` in the current working directory

Platform user-config locations are:

- macOS: `~/Library/Application Support/MorningBrief/config.env`
- Linux: `${XDG_CONFIG_HOME:-~/.config}/morningbrief/config.env`
- Windows: `%APPDATA%\MorningBrief\config.env`

## Data and Reliability

MorningBrief writes only below `MB_DATA_ROOT`:

```text
MorningBriefData/
├── history.csv
└── reports/
    └── daily/
        ├── 20260719T080000-0400_a1b2c3d4.md
        └── 20260719T153000-0400_e5f6a7b8.md
```

Each run receives a unique ID. Reports and `history.csv` are written
atomically, and same-day reruns append instead of replacing earlier results.
Legacy `YYYY-MM-DD.md` reports and history rows remain readable.

Before running Codex, MorningBrief validates the configuration and snapshots
operational memory. If generation or extraction fails, it restores the
pre-run memory. Codex continues to own its session logs. MorningBrief captures
the report directly, then matches that exact final response in the fresh Codex
rollouts only to record `rollout_path` and `session_dir` metadata.

## Project Structure

```text
MorningBrief/
├── MorningBriefDataDemo/
│   ├── prompt.md
│   ├── seed/memory.md
│   ├── vault/
│   ├── history.csv
│   └── reports/daily/demo.md
├── src/morningbrief/
│   ├── cli.py
│   ├── config.py
│   ├── demo.py
│   ├── doctor.py
│   ├── history.py
│   ├── output.py
│   ├── reports.py
│   ├── runner.py
│   ├── state.py
│   ├── workflow.py
│   └── serve/
├── tests/
├── .env.example
├── CHANGELOG.md
├── pyproject.toml
└── README.md
```

## Tests

The test suite does not invoke Codex or read private data:

```bash
python -m unittest discover -s tests -v
```

## Privacy

Do not commit `.env`, operational `memory.md`, generated reports, Codex
sessions, private prompts, or input documents. The included
`MorningBriefDataDemo` contains fictional public sample content only.

Read [DISCLAIMER.md](DISCLAIMER.md) before publishing or redistributing
generated reports.

## Attribution

A **WillGaoLab** project, created and maintained by **William (Peidong) Gao**.

- Project website: <https://williampeidonggao.com>
- Brand: <https://github.com/WillGaoLab>
- Personal GitHub: <https://github.com/PeidongGao>

## Affiliation

MorningBrief is not affiliated with, endorsed by, or sponsored by OpenAI,
Codex, Streamlit, GitHub, or other referenced providers. See the
[affiliation disclaimer](DISCLAIMER.md#affiliation-disclaimer).

## License

Original code and documentation are licensed under the [MIT License](LICENSE)
© 2026 William Gao. Generated reports, private documents, third-party content,
API outputs, and model outputs are not covered by the repository license.
