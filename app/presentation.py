"""Static presentation for the dashboard; never interpolates uploaded content."""
import streamlit as st


STYLE = '''<style>
/* Scope custom presentation to the app; keep native controls and focus behavior. */
[data-testid="stMainBlockContainer"] {max-width: 1240px; padding-top: 4.5rem; padding-bottom: 4rem;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(135, 166, 188, .22);}
h1, h2, h3 {letter-spacing: -.025em;}
h2 {font-size: 1.65rem !important;}
h3 {font-size: 1.2rem !important;}
[data-testid="stFileUploader"] {border: 1px dashed #608a96; border-radius: 16px; padding: 1.1rem; background: rgba(63, 145, 143, .06);}
[data-testid="stMetric"] {border: 1px solid rgba(135, 166, 188, .25); border-radius: 14px; padding: 1rem; background: rgba(63, 145, 143, .06);}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 16px;}
[data-baseweb="tab-list"] {gap: .3rem; border-bottom: 1px solid rgba(135, 166, 188, .25);}
[data-baseweb="tab"] {padding: .65rem 1rem; border-radius: 8px 8px 0 0;}
[data-baseweb="tab"][aria-selected="true"] {background: rgba(64, 140, 148, .14);}
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {border-radius: 9px; min-height: 2.7rem; font-weight: 600;}
.hl-brand {font-weight: 750; font-size: 1.4rem; color: inherit; letter-spacing: -.04em; margin-bottom: .25rem;}
.hl-brand span {color: #72dfc5; margin-right: .4rem;}
.hl-tagline {font-size: .86rem; color: inherit; opacity: .85; margin: 0 0 1.7rem;}
.hl-hero {display: grid; grid-template-columns: 1fr 230px; align-items: center; gap: 2rem; background: radial-gradient(ellipse at top right, #184c51 0%, transparent 65%), linear-gradient(135deg, #102337, #122d3c); border: 1px solid #315366; border-radius: 22px; padding: 2.6rem 2.8rem; margin-bottom: 1.1rem; color: #fff; overflow: hidden; box-shadow: 0 18px 50px rgba(0, 0, 0, .14);}
.hl-eyebrow {font-size: .72rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: #a9ded7; margin-bottom: .8rem;}
.hl-hero h1 {color: #fff; font-size: clamp(2rem, 3.5vw, 3.2rem); line-height: 1.12; font-weight: 700; margin: 0 0 1rem; padding: 0; letter-spacing: -.045em;}
.hl-hero p {color: #d5e4eb; font-size: 1rem; line-height: 1.65; max-width: 570px; margin: 0;}
.hl-art {position: relative; height: 170px; display: flex; align-items: center; justify-content: center; gap: 9px; border: 1px solid #315366; border-radius: 50%;}
.hl-art::after {content: ''; position: absolute; inset: 16px -15px; border: 1px solid #315366; border-radius: 50%; transform: rotate(-24deg);}
.hl-art i {display: block; width: 12px; border-radius: 12px; background: #80cec2; z-index: 1;}
.hl-art i:nth-child(1), .hl-art i:nth-child(7) {height: 26px;}
.hl-art i:nth-child(2), .hl-art i:nth-child(6) {height: 54px;}
.hl-art i:nth-child(3), .hl-art i:nth-child(5) {height: 92px;}
.hl-art i:nth-child(4) {height: 126px; background: #e5f5ef;}
.hl-steps {display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; margin: .2rem 0 .6rem;}
.hl-step {display: flex; gap: .7rem; align-items: center; padding: 1rem .7rem; border: 1px solid rgba(135, 166, 188, .2); border-radius: 12px;}
.hl-step b {display: inline-flex; flex-shrink: 0; width: 30px; height: 30px; justify-content: center; align-items: center; border: 1px solid #608a96; border-radius: 50%; color: inherit; font-size: .8rem;}
.hl-step strong {display: block; color: inherit; font-size: .9rem;}
.hl-step small {display: block; color: inherit; opacity: .85; font-size: .8rem;}
.hl-empty {padding: 1.2rem 0 .4rem; color: inherit; opacity: .85; font-size: .9rem;}
@media (max-width: 700px) {
 [data-testid="stMainBlockContainer"] {padding-top: 4rem; padding-left: 1rem; padding-right: 1rem;}
 .hl-hero {grid-template-columns: 1fr; padding: 1.8rem 1.4rem; border-radius: 16px;}
 .hl-art {display: none;}
 .hl-steps {gap: .3rem;}
 .hl-step {align-items: flex-start; gap: .4rem; padding: .7rem .4rem;}
 .hl-step small {display: none;}
 .hl-step strong {font-size: .8rem; padding-top: .3rem;}
 [data-baseweb="tab"] {padding: .5rem .65rem;}
}
</style>'''


def apply_style():
    st.markdown(STYLE, unsafe_allow_html=True)


def render_sidebar(cloud):
    with st.sidebar:
        st.markdown('<div class="hl-brand"><span>◉</span> Hearing Lens</div><p class="hl-tagline">Make room for every perspective.</p>', unsafe_allow_html=True)
        view = st.radio('View', ['Analyze feedback', 'Methodology and limitations'], key='hl_view')
        st.divider()
        st.caption('YOUR WORKSPACE')
        if cloud:
            st.markdown('**Free online demo**')
            st.caption('Up to 60 cleaned comments · 24,000 comment characters.')
            with st.expander('Working with a larger file?'):
                st.markdown('Use the [local installation guide](https://github.com/vamshikrishnadara/Hearing-Lens#install-and-run) to analyze your complete file on your computer, with the same views and downloads.')
                st.caption('Separate sample reports should not be combined into a full-file analysis.')
            st.caption('The free host can slow down when busy. Start one analysis and let it finish.')
        else:
            st.markdown('**Local workspace**')
            st.caption('Analyze larger files on your computer. Capacity depends on your hardware.')
        st.divider()
        st.caption('Uploads and results stay in memory for this session. Download what you need before leaving.')
    return view


def render_intro():
    st.markdown('''<section class="hl-hero" aria-label="Hearing Lens introduction">
<div><div class="hl-eyebrow">Hearing Lens · Community feedback</div>
<h1>From many voices.<br>To a clearer picture.</h1>
<p>Find the themes, understand the tone, and bring the important questions into focus.</p></div>
<div class="hl-art" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
</section>''', unsafe_allow_html=True)
    st.caption('Upload community feedback or survey responses you have permission to use. Remove sensitive information before uploading; automatic redaction can miss identifiers. Review results before sharing.')


def render_steps():
    st.markdown('''<div class="hl-steps" aria-label="Three steps to your results">
<div class="hl-step"><b>01</b><div><strong>Add feedback</strong><small>Upload a CSV or Excel file</small></div></div>
<div class="hl-step"><b>02</b><div><strong>Find the patterns</strong><small>Check your columns and analyze</small></div></div>
<div class="hl-step"><b>03</b><div><strong>Share the findings</strong><small>Explore and download your results</small></div></div>
</div>''', unsafe_allow_html=True)


def render_empty_state():
    st.markdown('<div class="hl-empty">Your results will appear here after analysis. Start with a file containing a column of written feedback.</div>', unsafe_allow_html=True)
    with st.expander('Need a sample file?'):
        st.caption('Six fictional comments about a community library. Download, then upload above to explore the workflow.')
        sample = ('comment_text\n'
                  '"The library staff helped me find books for my evening class and explained how to reserve them."\n'
                  '"The library closes too early for people who work late and cannot attend daytime sessions."\n'
                  '"When will the library publish the schedule for the next reading group so families can plan ahead?"\n'
                  '"I appreciate the quiet study area and the clear signs that help me find the right shelves."\n'
                  '"The reading room is noisy and I am disappointed that the broken door has not been repaired."\n'
                  '"Could the library offer more weekend workshops for families who cannot visit during the working week?"\n')
        st.download_button('Download sample CSV', data=sample.encode(), file_name='hearing_lens_sample.csv', mime='text/csv', on_click='ignore')
