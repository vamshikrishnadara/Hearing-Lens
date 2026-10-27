"""Upload, mapping and session-only analytical dashboard for Hearing Lens."""

from __future__ import annotations

import streamlit as st

from app.analysis_options import render_analysis_options, invalidate_options
from app.dashboard import analyze_dashboard, clear_workspace, render_dashboard, workspace_for
from pipeline.ingest import IngestError, list_excel_sheets, load_table, map_columns
from pipeline.redact import RedactionError, build_safe_display_frame
from pipeline.progress import STAGES
from app.runtime import AnalysisBusyError
from app.limits import AnalysisLimitError, check_analysis_size, is_cloud_demo


st.set_page_config(page_title="Hearing Lens", layout="wide")
view = st.sidebar.radio('View', ['Analyze feedback', 'Methodology and limitations'], key='hl_view')
if view == 'Methodology and limitations':
    from app.pages.methodology import render_methodology
    render_methodology()
    st.stop()

st.title("Hearing Lens")
st.write(
    "Upload a community-feedback or survey export, then identify the column "
    "that contains each response. Files are processed in memory for this session."
)
st.warning(
    "Development preview: use fictional test data. Automatic redaction can "
    "miss names and other identifiers; review the text before sharing it."
)

if is_cloud_demo():
    st.info("Free demo: up to 60 cleaned comments and 24,000 comment characters. "
            "For larger files, use the local dashboard with the same analysis and downloads. "
            "Small runs can still slow down when the free host is busy.")

with st.expander("How to use Hearing Lens"):
    st.markdown(
        "1. Start with a small fictional CSV or Excel file. Select the column containing comments. "
        "Dates, IDs and subgroup fields are optional.\n"
        "2. Select **Validate mapping** and check the usable count and redacted preview.\n"
        "3. Select **Analyze comments** once. The status shows the current step; avoid starting repeated runs while it is busy.\n"
        "4. Explore the five result tabs and check the quotes and any warnings.\n"
        "5. Download labeled CSV, or select **Prepare Word brief** or **Prepare PDF brief** below the results, then download."
    )
    st.caption("Counts describe comments, not necessarily people. Model labels and possible response matches need checking. Changing inputs clears earlier results and downloads.")

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
            check_analysis_size(mapped.frame)
            with st.spinner("Checking comments for names and contact details..."):
                safe_preview = build_safe_display_frame(mapped.frame)
        except (IngestError, RedactionError, AnalysisLimitError) as exc:
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
                except AnalysisLimitError as exc:
                    status.update(label='File exceeds the free demo limit', state='error')
                    st.info(str(exc))
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
