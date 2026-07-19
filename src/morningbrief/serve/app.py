"""Read-only Streamlit reader for saved Morning Brief reports."""

import os
import signal
import threading
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from morningbrief import config, history


CLOSE_PAGE_HTML = """
<div style="font-family: sans-serif; padding: 0.75rem; text-align: center;">
  MorningBrief is closed. This page may now be dismissed.
</div>
<script>
(() => {
  const page = window.top;
  setTimeout(() => {
    try {
      page.open("", "_self");
      page.close();
    } catch (_) {}

    setTimeout(() => {
      try {
        if (!page.closed) {
          page.location.replace("about:blank");
        }
      } catch (_) {}
    }, 250);
  }, 100);
})();
</script>
"""


def request_server_shutdown(delay_seconds=0.5):
    """Stop this local Streamlit process shortly after the UI acknowledges it."""
    timer = threading.Timer(
        delay_seconds,
        os.kill,
        args=(os.getpid(), signal.SIGINT),
    )
    timer.daemon = True
    timer.start()


def request_browser_close():
    """Ask the browser to close this tab, with a blank-page fallback."""
    components.html(CLOSE_PAGE_HTML, height=80)


def perform_confirmed_close():
    """Close the browser view and then stop the local reader server."""
    request_browser_close()
    request_server_shutdown(delay_seconds=1.5)


@st.dialog("Close MorningBrief?")
def show_close_confirmation():
    st.write("This will close the MorningBrief page and stop the local server.")
    cancel_column, close_column = st.columns(2)
    if cancel_column.button("Cancel", use_container_width=True):
        st.rerun()
    if close_column.button(
        "Close MorningBrief", type="primary", use_container_width=True
    ):
        perform_confirmed_close()
        st.stop()


def load_history_rows(settings):
    rows = history.load_rows(settings.history_csv)
    rows.sort(
        key=lambda row: (row.get("created_at", ""), row.get("run_id", "")),
        reverse=True,
    )
    return rows


def render_metadata(row, settings):
    def metric_value(column):
        value = row.get(column, "")
        return value if value != "" else "—"

    columns = st.columns(3)
    columns[0].metric("Markdown files scanned", metric_value("scan_total_markdown"))
    columns[1].metric("Changed", metric_value("scan_changed"))
    columns[2].metric("Need attention", metric_value("scan_need_attention"))
    st.caption(
        f"Status: **{row.get('status', '') or 'unknown'}** · "
        f"Generated: {row.get('created_at', '') or 'unknown'}"
    )
    with st.expander("Paths", expanded=False):
        st.markdown(f"**Run ID:** `{row.get('run_id', '') or 'legacy'}`")
        st.markdown(f"**Report:** `{row.get('report_path', '') or '—'}`")
        st.markdown(f"**Rollout:** `{row.get('rollout_path', '') or '—'}`")
        st.markdown(f"**Session dir:** `{row.get('session_dir', '') or '—'}`")
        st.markdown(f"**History:** `{settings.history_csv}`")


def resolve_report_path(report_path, data_root):
    """Resolve history paths relative to the configured data root."""
    path = Path(report_path).expanduser()
    return path if path.is_absolute() else Path(data_root) / path


def render_report(row, settings):
    report_path = row.get("report_path", "")
    if not report_path:
        st.error(
            f"No report is recorded for this run (status: "
            f"{row.get('status', '') or 'unknown'})."
        )
        return
    path = resolve_report_path(report_path, settings.data_root)
    if not path.is_file():
        st.error(f"Report file listed in history.csv is missing:\n\n`{path}`")
        return
    st.markdown(path.read_text())


def row_label(row):
    created = row.get("created_at", "") or row.get("date", "") or "unknown date"
    status = row.get("status", "") or "unknown"
    run_id = row.get("run_id", "")
    suffix = run_id[-8:] if run_id else "legacy"
    return f"{created} · {status} · {suffix}"


def main():
    st.set_page_config(page_title="Morning Brief", page_icon="☀️")
    st.title("Morning Brief")
    try:
        reader_root = os.environ.get("MORNINGBRIEF_READER_DATA_ROOT")
        settings = (
            config.reader_settings(Path(reader_root))
            if reader_root
            else config.load_settings()
        )
    except config.ConfigError as exc:
        st.error(str(exc))
        return

    if not settings.history_csv.exists():
        st.warning(
            f"No history file found at `{settings.history_csv}`.\n\n"
            "Validate configuration with `mb doctor`, then generate with `mb run`."
        )
        return

    rows = load_history_rows(settings)
    if not rows:
        st.warning("history.csv contains no runs. Run `mb run` to generate one.")
        return

    selected_index = st.sidebar.selectbox(
        "Briefing run",
        range(len(rows)),
        format_func=lambda index: row_label(rows[index]),
    )
    st.sidebar.caption(f"{len(rows)} run(s) indexed in history.csv")
    if st.sidebar.button("Close MorningBrief", use_container_width=True):
        show_close_confirmation()
    row = rows[selected_index]

    heading = row.get("date", "") or "Morning Brief"
    if selected_index == 0:
        heading += " (latest)"
    st.subheader(heading)
    render_metadata(row, settings)
    st.divider()
    render_report(row, settings)


if __name__ == "__main__":
    main()
