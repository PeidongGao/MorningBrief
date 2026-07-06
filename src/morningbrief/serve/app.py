"""Read-only Streamlit reader for Morning Brief reports.

Launched via `mb serve`. Consumes history.csv and the daily report files in
the configured data directory. It never generates reports and never writes
anything.
"""

from pathlib import Path

import streamlit as st

from morningbrief import config, history


def load_history_rows():
    """History rows sorted newest-first."""
    rows = history.load_rows(config.HISTORY_CSV)
    rows.sort(key=lambda r: r.get("date", ""), reverse=True)
    return rows


def render_metadata(row):
    def metric_value(column):
        value = row.get(column, "")
        return value if value != "" else "—"

    cols = st.columns(3)
    cols[0].metric("Markdown files scanned", metric_value("scan_total_markdown"))
    cols[1].metric("Changed", metric_value("scan_changed"))
    cols[2].metric("Need attention", metric_value("scan_need_attention"))

    st.caption(
        f"Status: **{row.get('status', '') or 'unknown'}** · "
        f"Generated: {row.get('created_at', '') or 'unknown'}"
    )
    with st.expander("Paths", expanded=False):
        st.markdown(f"**Report:** `{row.get('report_path', '') or '—'}`")
        st.markdown(f"**Rollout:** `{row.get('rollout_path', '') or '—'}`")
        st.markdown(f"**Session dir:** `{row.get('session_dir', '') or '—'}`")
        st.markdown(f"**History:** `{config.HISTORY_CSV}`")


def render_report(row):
    report_path = row.get("report_path", "")
    if not report_path:
        st.error(
            f"No report file is recorded for {row.get('date', 'this date')} "
            f"(status: {row.get('status', '') or 'unknown'}). "
            "Run `mb run` to generate it."
        )
        return
    path = Path(report_path)
    if not path.exists():
        st.error(
            f"Report file listed in history.csv is missing:\n\n`{path}`\n\n"
            "It may have been moved or deleted. Re-run `mb run` to regenerate "
            "today's report."
        )
        return
    st.markdown(path.read_text())


def main():
    st.set_page_config(page_title="Morning Brief", page_icon="☀️")
    st.title("Morning Brief")

    if not config.HISTORY_CSV.exists():
        st.warning(
            f"No history file found at `{config.HISTORY_CSV}`.\n\n"
            "Generate your first Morning Brief with:\n\n"
            "```\nconda activate morningbrief\nmb run\n```"
        )
        return

    rows = load_history_rows()
    if not rows:
        st.warning(
            f"`{config.HISTORY_CSV}` exists but contains no reports yet. "
            "Run `mb run` to generate one."
        )
        return

    dates = [row.get("date", "") for row in rows]
    selected_date = st.sidebar.selectbox("Report date", dates, index=0)
    st.sidebar.caption(f"{len(rows)} report(s) indexed in history.csv")

    row = next(r for r in rows if r.get("date", "") == selected_date)

    heading = selected_date
    if selected_date == dates[0]:
        heading += " (latest)"
    st.subheader(heading)

    render_metadata(row)
    st.divider()
    render_report(row)


main()
