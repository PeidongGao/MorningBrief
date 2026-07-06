# MorningBrief

MorningBrief is a local CLI for running a Codex-based Morning Brief workflow and reading saved reports in a Streamlit interface.

It wraps an existing prompt workflow: `mb run` executes the configured prompt with Codex, extracts the generated brief, saves it as Markdown, and updates a CSV index. `mb serve` opens a read-only browser for previous reports.

## Features

- Run a configured Codex prompt workflow from the command line
- Save each generated brief as Markdown
- Maintain a `history.csv` index of generated reports
- Browse saved reports in a local Streamlit reader
- Keep local paths and private data outside the repository
- Configure paths with `.env` or environment variables

## Requirements

- Python 3.9+
- Codex CLI installed and available on `PATH`
- A local Codex workspace containing your Morning Brief prompt
- Local input directories that the prompt is allowed to read

## Installation

```bash
git clone https://github.com/<your-account>/MorningBrief.git
cd MorningBrief
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Conda works as well:

```bash
conda create -n morningbrief python=3.12 -y
conda activate morningbrief
pip install -e .
```

## Configuration

Copy the example configuration and edit it for your machine:

```bash
cp .env.example .env
```

Example `.env` values:

```bash
MB_CODEX_REPO=/path/to/your/codex-workspace
MB_PROMPT_FILE=/path/to/your/prompt.md
MB_VAULT_DIR=/path/to/your/input-notes
MB_AUTOMATION_MEMORY_DIR=/path/to/your/automation-memory
MB_SESSIONS_ROOT=~/.codex/sessions
MB_DATA_ROOT=/path/to/your/output-data
MB_CODEX_BINARY=codex
```

The `.env` file is ignored by Git. You can also set the same `MB_*` values as environment variables, or set `MORNINGBRIEF_CONFIG` to load a config file from a different location.

## Usage

Generate today's Morning Brief:

```bash
mb run
```

Launch the local reader:

```bash
mb serve
```

The reader opens a Streamlit app for the configured output directory. It displays saved reports, scan statistics, metadata, and file locations. It does not launch the workflow or write report data.

## Project Structure

```text
MorningBrief/
├── src/
│   └── morningbrief/
│       ├── cli.py
│       ├── config.py
│       ├── workflow.py
│       ├── rollout.py
│       ├── history.py
│       └── serve/
├── .env.example
├── pyproject.toml
└── README.md
```

## Output

MorningBrief writes generated files below `MB_DATA_ROOT`.

Typical output:

- `reports/daily/YYYY-MM-DD.md`
- `history.csv`

The output directory should not be committed.

## Privacy

This repository is intended to contain only reusable application code and public documentation. Keep these local resources outside version control:

- `.env`
- generated reports
- `history.csv`
- Codex sessions
- local notes or source material
- private workflow documentation

## License

Add an open-source license before publication.
