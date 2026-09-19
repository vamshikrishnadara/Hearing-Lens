"""Week 1 upload and column-mapping interface for Hearing Lens."""

from __future__ import annotations

import streamlit as st

from pipeline.ingest import IngestError, list_excel_sheets, load_table, map_columns
from pipeline.redact import RedactionError, build_safe_display_frame


st.set_page_config(page_title="Hearing Lens", layout="wide")
st.title("Hearing Lens")
st.write(
    "Upload a public-comment or community-survey export, then identify the column "
    "that contains each response. Files are processed in memory for this session."
)
st.warning(
    "Development preview: use fictional test data. Automatic redaction can "
    "miss names and other identifiers; review the text before sharing it."
)

uploaded = st.file_uploader("Upload a CSV or XLSX file", type=["csv", "xlsx"])

if uploaded is not None:
    selected_sheet = None
    if uploaded.name.lower().endswith(".xlsx"):
        try:
            sheets = list_excel_sheets(uploaded)
            selected_sheet = st.selectbox("Workbook sheet", sheets)
        except IngestError as exc:
            st.error(str(exc))
            st.stop()

    try:
        loaded = load_table(uploaded, sheet_name=selected_sheet)
    except IngestError as exc:
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

    if st.button("Validate mapping", type="primary"):
        try:
            mapped = map_columns(
                loaded.frame,
                comment_column=comment_column,
                date_or_hearing_column=(
                    None if date_choice == "Not provided" else date_choice
                ),
                respondent_id_column=(
                    None if respondent_choice == "Not provided" else respondent_choice
                ),
                subgroup_columns=subgroup_columns,
            )
            with st.spinner("Checking comments for names and contact details..."):
                safe_preview = build_safe_display_frame(mapped.frame)
        except (IngestError, RedactionError) as exc:
            st.error(str(exc))
        else:
            st.success(f"{len(mapped.frame):,} usable comments are ready for analysis.")
            if mapped.empty_comments_removed:
                st.info(
                    f"Removed {mapped.empty_comments_removed:,} rows with empty comments."
                )
            if mapped.duplicate_respondents_removed:
                st.info(
                    "Removed "
                    f"{mapped.duplicate_respondents_removed:,} repeated respondent IDs."
                )
            redaction_total = sum(safe_preview.entity_counts.values())
            if redaction_total:
                st.info(
                    f"Redacted {redaction_total:,} name, contact, or address matches "
                    "across the usable comments."
                )
            st.caption(
                "First 20 usable comments after automatic redaction. Respondent IDs "
                "and other mapped fields are excluded from this preview."
            )
            st.dataframe(safe_preview.frame.head(20), use_container_width=True)
