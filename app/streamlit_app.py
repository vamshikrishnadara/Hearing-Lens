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
from app.local_guidance import render_local_guidance
from app.presentation import apply_style, render_sidebar, render_intro, render_steps, render_empty_state


st.set_page_config(page_title="Hearing Lens", page_icon="◉", layout="wide")
apply_style()
view = render_sidebar(is_cloud_demo())
if view == 'Methodology and limitations':
    from app.pages.methodology import render_methodology
    render_methodology()
    st.stop()

render_intro()
render_steps()

with st.expander("How to use Hearing Lens"):
    st.markdown(
        "1. **Upload** a CSV or Excel file containing feedback or survey responses and choose your comment column.\n"
        "2. **Check** the redacted preview, then select **Analyze comments** once.\n"
        "3. **Explore** themes, tone, timeline, representation and questions.\n"
        "4. **Download** labeled comments or prepare a Word or PDF brief."
    )
    st.caption("Dates, IDs and subgroup fields are optional. Counts describe comments, not necessarily people. Changing inputs clears earlier results and downloads.")

st.subheader("1. Add your feedback")
st.caption("One response per row. CSV or Excel · up to 10 MB per file.")
if is_cloud_demo():
    st.info("Free demo: up to 60 cleaned comments and 24,000 comment characters. Use the local dashboard for larger files.")
uploaded = st.file_uploader("Upload a CSV or XLSX file", type=["csv", "xlsx"])

if uploaded is None:
    clear_workspace()
    render_empty_state()
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
    st.subheader("2. Choose your columns")
    st.caption("Select the text to analyze. Add optional details only when you need comparisons.")
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
    date_col, respondent_col = st.columns(2)
    with date_col:
        date_choice = st.selectbox("Date or hearing label", optional_columns)
    with respondent_col:
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
        except AnalysisLimitError as exc:
            st.warning(str(exc))
            render_local_guidance()
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
        with st.expander("Preview cleaned comments", expanded=workspace['result'] is None):
            st.caption("First 20 usable comments after automatic redaction. Respondent IDs and other mapped fields are excluded from this preview.")
            st.dataframe(safe_preview.frame.head(20), use_container_width=True, hide_index=True)
        st.subheader("3. Explore your feedback")
        st.caption("Analyze once, then explore all five views. The first run may take longer while models load.")
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
                    st.warning(str(exc))
                    render_local_guidance()
                except AnalysisBusyError as exc:
                    status.update(label='Analysis not started: another run is still active', state='error')
                    st.info(str(exc))
                except Exception:
                    # Model exceptions can include source cells. Never display or log them.
                    status.update(label='Analysis could not finish', state='error')
                    st.error('Analysis could not finish. Try again once, or use the local dashboard if the problem continues. No partial results are shown.')
                else:
                    status.update(label='Analysis complete', state='complete')
        if workspace['result'] is not None:
            render_dashboard(workspace)
