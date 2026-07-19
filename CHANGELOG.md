# Changelog

Notable changes to MorningBrief are documented here.

## 2.1.0 — 2026-07-19

### Added

- Complete fictional demo generation with `mb run --demo`.
- Read-only demo validation with `mb doctor --demo`.
- Bundled 12-file fictional Markdown vault, prompt, and seed operational memory.
- Isolated `MorningBriefDataDemo/runtime/` storage for generated demo state,
  history, and reports.
- Automatic `mb serve --demo` selection of generated demo history when present.
- Privacy and generic-layout regression tests for public demo content.

### Changed

- Expanded the previous reader-only sample into an end-to-end demonstration.
- Replaced private-style taxonomy with the generic `notes`, `operations`,
  `organization`, `projects`, and `updates` layout.
- Updated public documentation for the complete demo workflow.

### Validation

- Verified generation from a public-only copy without `.env`, private files,
  existing runtime state, or Git metadata.
- Verified Streamlit health and rendering of the generated report and metrics.

## 2.0.0 — 2026-07-19

- Replaced Codex session discovery with exact final-message capture.
- Added atomic report/history writes and non-destructive same-day reruns.
- Added typed portable settings, `mb doctor`, and safe `mb init` state creation.
- Added operational-memory rollback after unsuccessful generation.
- Added the configuration-free pre-generated reader sample with
  `mb serve --demo`.
