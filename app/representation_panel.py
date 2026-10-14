"""Display only disclosure-controlled representation outputs."""
import pandas as pd
import streamlit as st


def representation_table(rows):
    return pd.DataFrame([{
        'Category': r['group'],
        'Comments': None if r['suppressed'] else r['count'],
        'Participation (%)': None if r['suppressed'] or r['participation_share'] is None else round(r['participation_share'] * 100, 2),
        'Reference (%)': None if r['reference_share'] is None else round(r['reference_share'] * 100, 2),
        'Gap (percentage points)': None if r['suppressed'] else r['gap_percentage_points'],
        'Representation ratio': None if r['suppressed'] else r['representation_ratio'],
        'Status': 'Suppressed' if r['suppressed'] else r['flag'].replace('_', ' ').capitalize(),
    } for r in rows])


def render_representation(result):
    st.header('Representation')
    gaps = result.get('gaps')
    if not gaps or not gaps.get('fields'):
        st.info('No subgroup fields were mapped. Select optional subgroup fields and validate the mapping to see participation summaries.')
        return
    st.caption('Counts describe comments after cleaning, not necessarily unique people. Categories are supplied, never inferred. Shares use rows with known values for each field.')
    st.caption('Counts and derived figures for small groups are hidden. Another group may also be hidden to prevent recovering a small count by subtraction. A dash means unavailable or suppressed, not zero.')
    for field in gaps['fields']:
        with st.container(border=True):
            st.text(field['field'].removeprefix('subgroup__'))
            st.caption(f"Known values: {field['known_rows']:,} | Missing values: {field['missing_rows']:,}")
            if field['reference_status'] != 'valid':
                st.info('No valid reference is available. This field shows counts and participation shares only; no representation comparison is made.')
            for notice in field.get('notices', []):
                st.info(notice)
            rows = [r for r in gaps['rows'] if r['field'] == field['field']]
            if rows:
                st.dataframe(representation_table(rows), hide_index=True, use_container_width=True)
            else:
                st.info('No known category values are available for this field.')
    st.caption('Underrepresented means a ratio below 0.75; overrepresented means above 1.25. These comparisons depend on the reference you supplied and do not explain why a difference exists.')
