"""Upload, mapping and session-only analytical dashboard for Hearing Lens."""

from __future__ import annotations

import streamlit as st

from app.analysis_options import render_analysis_options, invalidate_options
from app.dashboard import analyze_dashboard, clear_workspace, render_dashboard, workspace_for
from pipeline.ingest import IngestError, list_excel_sheets, load_table, map_columns
from pipeline.redact import RedactionError, build_safe_display_frame
from pipeline.progress import STAGES
from app.runtime import AnalysisBusyError


st.set_page_config(page_title="Hearing Lens", layout="wide")
st.title("Hearing Lens")
st.write(
    "Upload a community-feedback or survey export, then identify the column "
    "that contains each response. Files are processed in memory for this session."
)
st.warning(
    "Development preview: use fictional test data. Automatic redaction can "
    "miss names and other identifiers; review the text before sharing it."
)

uploaded = st.file_uploader("Upload a CSV or XLSX file", type=["csv", "xlsx"])

if uploaded is None:
    clear_workspace()
else:
    selected_sheet = None
    if uploaded.name.lower().endswith(".xlsx"):
        try:
            sheets = list_excel_sheets(uploaded)
            selected_sheet = st.selectbox("Workbook sheet", sheets)
        except IngestError as exc:
            clear_workspace()
            st.error(str(exc))
            st.stop()

    try:
        loaded = load_table(uploaded, sheet_name=selected_sheet, preserve_text=True)
    except IngestError as exc:
        clear_workspace()
        st.error(str(exc))
        st.stop()

    for warning in loaded.warnings:
        st.warning(warning)

    columns = [str(column) for column in loaded.frame.columns]
    st.subheader("Map your columns")
    comment_column = st.selectbox(
        "Comment text",
        columns,
        index=columns.index("comment_text") if "comment_text" in columns else 0,
        help=(
            "Select the column containing each response. A column named exactly "
            "comment_text is selected initially when available; otherwise the "
            "first column is selected. You can change this selection."
        ),
    )

    optional_columns = ["Not provided", *columns]
    date_choice = st.selectbox("Date or hearing label", optional_columns)
    respondent_choice = st.selectbox("Respondent ID", optional_columns)

    already_selected = {comment_column, date_choice, respondent_choice}
    subgroup_options = [
        column
        for column in columns
        if column not in already_selected and not column.startswith("Unnamed:")
    ]
    subgroup_columns = st.multiselect(
        "Subgroup fields (optional)",
        subgroup_options,
        help="Examples include ward, ZIP, role, language, tenure, or school.",
    )

    mapping = dict(
        comment_column=comment_column,
        date_or_hearing_column=None if date_choice == "Not provided" else date_choice,
        respondent_id_column=None if respondent_choice == "Not provided" else respondent_choice,
        subgroup_columns=subgroup_columns,
    )
    workspace = workspace_for(uploaded, selected_sheet, mapping)
    if st.button("Validate mapping", type="primary"):
        clear_workspace()
        workspace = workspace_for(uploaded, selected_sheet, mapping)
        try:
            mapped = map_columns(loaded.frame, **mapping)
            with st.spinner("Checking comments for names and contact details..."):
                safe_preview = build_safe_display_frame(mapped.frame)
        except (IngestError, RedactionError) as exc:
            st.error(str(exc))
        else:
            workspace['mapped'] = mapped
            workspace['preview'] = safe_preview

    if workspace['mapped'] is not None:
        mapped, safe_preview = workspace['mapped'], workspace['preview']
        st.success(f"{len(mapped.frame):,} usable comments are ready for analysis.")
        if mapped.empty_comments_removed:
            st.info(f"Removed {mapped.empty_comments_removed:,} rows with empty comments.")
        if mapped.duplicate_respondents_removed:
            st.info(f"Removed {mapped.duplicate_respondents_removed:,} repeated respondent IDs.")
        redaction_total = sum(safe_preview.entity_counts.values())
        if redaction_total:
            st.info(f"Redacted {redaction_total:,} name, contact, or address matches across the usable comments.")
        st.caption("First 20 usable comments after automatic redaction. Respondent IDs and other mapped fields are excluded from this preview.")
        st.dataframe(safe_preview.frame.head(20), use_container_width=True)
        st.caption("Run analysis to view themes, sentiment, emotion, timelines, representation and question priorities. The first run may take longer while local models load.")
        references, response, option_signature, options_valid = render_analysis_options(mapped.frame)
        invalidate_options(workspace, option_signature)
        if st.button("Analyze comments", type="primary", disabled=not options_valid):
            workspace['result'] = None
            workspace.pop('brief_docx', None)
            workspace.pop('brief_pdf', None)
            workspace['revision'] += 1
            workspace['quote_revisions'] = {}
            for key in list(st.session_state):
                if key.startswith('hl_review_'):
                    del st.session_state[key]
            with st.status('Starting analysis...', expanded=False) as status:
                def show_stage(stage):
                    status.update(label=STAGES[stage] + '...')
                try:
                    workspace['result'] = analyze_dashboard(mapped.frame, references=references,
                                                           response=response, progress=show_stage)
                except AnalysisBusyError as exc:
                    status.update(label='Analysis not started: another run is still active', state='error')
                    st.info(str(exc))
                except Exception:
                    # Model exceptions can include source cells. Never display or log them.
                    status.update(label='Analysis could not finish', state='error')
                    st.error('Analysis could not finish. Check the analysis stage timings in the app logs before retrying. No partial results are shown.')
                else:
                    status.update(label='Analysis complete', state='complete')
        if workspace['result'] is not None:
            render_dashboard(workspace)
