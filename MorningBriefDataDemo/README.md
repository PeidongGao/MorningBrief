# MorningBrief 2.1 Full Demo

Introduced in MorningBrief 2.1.0, this directory contains a fictional public
workflow that demonstrates the same layers as a privately configured
MorningBrief installation:

```text
MorningBriefDataDemo/
├── prompt.md                 Demo briefing instructions
├── vault/                    Fictional Markdown input collection
├── seed/memory.md            Initial operational-memory template
├── history.csv               Pre-generated reader sample
├── reports/daily/demo.md     Pre-generated reader sample
└── runtime/                  Generated locally and ignored by Git
    ├── state/memory.md
    └── data/
        ├── history.csv
        └── reports/daily/
```

From an editable installation, validate and run the complete demo:

```bash
mb doctor --demo
mb run --demo
mb serve --demo
```

`mb run --demo` requires the Codex CLI. It reads only the bundled fictional
vault, uses a runtime copy of the demo operational memory, and writes generated
reports under `runtime/data`. It does not load `.env` or private user paths.
`mb doctor --demo` only inspects the public fixtures and does not create or
change runtime state.

Before a generated run exists, `mb serve --demo` displays the pre-generated
sample. After a successful or failed demo run is recorded, it displays the
runtime history instead.

All people, organizations, projects, decisions, and metrics in this directory
are fictional examples created solely for product demonstration.
