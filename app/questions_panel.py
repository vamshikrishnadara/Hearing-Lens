"""Question candidates and supplied-response matches, without answer claims."""
import pandas as pd
import streamlit as st

MATCH_LABELS = {'not_checked': 'Not checked - no usable response',
                'possible_match': 'Possible response match - review needed',
                'partial_match': 'Partial response match - review needed',
                'no_match': 'No matching passage found'}


def question_summary(groups):
    return pd.DataFrame([{'Rank': g['rank'], 'Question group': g['question_group_id'],
                          'Supporting comments': g['comment_count'], 'Question sentences': g['sentence_count'],
                          'Distinct wordings': g['unique_wordings'],
                          'Response comparison': MATCH_LABELS[g['response_match_status']]} for g in groups])


def render_questions(result):
    st.header('Questions')
    questions = result.get('questions')
    if not questions:
        st.info('No question analysis is available for this run.')
        return
    if not questions.get('groups'):
        st.info('No question candidates were detected. This does not prove that the comments contain no requests or concerns.')
        return
    st.caption('English question candidates grouped by similar wording. Frequency counts supporting comments, not unique people. Check the wording and possible response matches before sharing.')
    if questions['response_status'] != 'available':
        st.info('No usable response text was supplied. These are unverified follow-up priorities, not confirmed unanswered questions.')
    else:
        st.caption('Similarity can identify related text without proving it answers the question. Partial and missing matches remain follow-up candidates.')
    priority_ids = set(questions['top_unanswered'])
    st.subheader('Suggested follow-up priorities')
    if not priority_ids:
        st.info('Every detected group has a possible response match. Review the passages before deciding whether any question is answered.')
    for group in questions['groups']:
        if group['question_group_id'] in priority_ids:
            st.text(f"{group['question_group_id']}: {group['representative']['text']}")
    st.subheader('All question groups')
    st.dataframe(question_summary(questions['groups']), hide_index=True, use_container_width=True)
    for group in questions['groups']:
        with st.expander(f"{group['question_group_id']} - {group['comment_count']} supporting comments"):
            st.text(group['representative']['text'])
            st.caption(MATCH_LABELS[group['response_match_status']])
            spread = group.get('subgroup_spread')
            if spread is None:
                st.caption('Subgroup spread is unavailable because no usable subgroup values were supplied.')
            else:
                st.caption(f'Visible field/category pairs: {spread}. Counts include only categories meeting the minimum size in this question group; they are not a count of unique people.')
                if group.get('spread_is_lower_bound'):
                    st.caption('Small or missing categories mean this is a lower bound.')
            for match in group.get('response_matches', []):
                st.text('Question wording: ' + match['question_text'])
                if match['response'] is not None:
                    st.text('Possible response passage: ' + match['response']['text'])
                    st.caption(f"Similarity: {match['similarity']:.2f}. Review relevance, completeness and contradictions.")
                else:
                    st.caption('No response passage met the matching threshold for this wording.')
