from pathlib import Path
import pandas as pd
import streamlit as st
from quality import load_csv, inspect, clean, safe_csv, report_json, validate_schema, STUDENT_SCHEMA

st.set_page_config(page_title='DataCheck | Quality Inspector', page_icon='🔎', layout='wide')
st.markdown('''<style>.stApp{background:#0b1120}h1,h2,h3{letter-spacing:-.035em}div[data-testid="stMetric"]{background:#131e33;border:1px solid #263553;padding:20px;border-radius:16px}.block-container{padding-top:2.5rem} </style>''', unsafe_allow_html=True)
st.caption('DATACHECK  /  BY BLESSING SEKERAMAVI')
st.title('Trust starts with better data.')
st.write('Inspect your CSV, understand the issues, and export a transparent quality report.')
with st.sidebar:
    st.header('Your data')
    st.caption('Created by Blessing Sekeramavi')
    schema_choice = st.selectbox('Validation schema', ['General CSV (no schema)', 'Student dataset'])
    upload = st.file_uploader('Upload CSV · up to 20 MB', type=['csv'])
    delimiter = st.selectbox('Separator', [',', ';', '\t', '|'], format_func=lambda x: 'Tab' if x=='\t' else x)
    encoding = st.selectbox('Encoding', ['utf-8-sig', 'utf-8', 'latin-1'])
    st.caption('Files are processed in server memory. This app has no file storage or external API calls. Use anonymized data on shared hosting; host infrastructure may retain operational logs.')
    st.markdown('**Checks:** blanks, exact duplicates, surrounding whitespace, category variants, mixed numeric values, infinities and potential outliers.')
if upload is None:
    st.info('Explore the synthetic education dataset below, or upload your own CSV.')
    sample_path = Path(__file__).resolve().parent/'data'/'sample_students.csv'
    if not sample_path.is_file():
        st.error('Sample data is missing. Upload a CSV in the sidebar to continue.'); st.stop()
    raw = sample_path.read_bytes()
    df = load_csv(raw)
else:
    if upload.size > 20*1024*1024:
        st.error('Choose a CSV smaller than 20 MB.'); st.stop()
    try:
        df = load_csv(upload.getvalue(), delimiter, encoding)
    except (ValueError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        st.error(f'Could not parse this file. Check the separator and encoding. {exc}'); st.stop()
if df.size > 2_000_000:
    st.error('This version supports up to two million cells. Use a smaller extract.'); st.stop()
report = inspect(df)
schema = STUDENT_SCHEMA if schema_choice == 'Student dataset' else None
report['schema_findings'] = validate_schema(df, schema) if schema is not None else []
s = report['summary']
a,b,c,d = st.columns(4)
a.metric('Rows inspected', f"{s['rows']:,}")
b.metric('Completeness', 'N/A' if s['completeness_pct'] is None else f"{s['completeness_pct']}%")
c.metric('Missing cells', s['missing_cells'])
d.metric('Duplicate rows', s['duplicate_rows'])
st.caption('Completeness reflects blank cells only. A complete dataset can still contain errors.')
overview, findings, preview, export = st.tabs(['Column health', 'Findings & methodology', 'Data preview', 'Clean & export'])
with overview:
    st.subheader('Where does your data need attention?')
    profile = pd.DataFrame(report['columns'])
    if not profile.empty:
        st.bar_chart(profile.set_index('column')[['missing', 'whitespace', 'potential_outliers']])
        st.dataframe(profile, width='stretch', hide_index=True)
with findings:
    st.subheader('Review before you change')
    st.write('Counts can overlap. Category variant counts refer to groups; other counts refer to cells. Duplicates refer to rows.')
    if report['issues']:
        st.dataframe(pd.DataFrame(report['issues']), width='stretch', hide_index=True)
    else:
        st.success('No issues detected by these checks. Domain validation may still be needed.')
    st.caption(report['methodology'])
    st.subheader('Schema validation')
    if schema is None:
        st.info('Choose Student dataset in the sidebar to validate required fields, unique IDs, numeric ranges and categories.')
    else:
        st.json(schema, expanded=False)
        if report['schema_findings']:
            st.dataframe(pd.DataFrame(report['schema_findings']), width='stretch', hide_index=True)
        else:
            st.success('All configured student schema checks passed.')
        st.caption('Exact column names and categories are required. Row positions start at 1 after the header. Numeric bounds describe the bundled demonstration schema, not every student dataset.')
with preview:
    st.caption('First 200 rows · identifiers and leading zeros are preserved. Literal NA and N/A are retained as text; only blanks count as missing.')
    st.dataframe(df.head(200), width='stretch', hide_index=True)
with export:
    st.subheader('Make deliberate changes')
    trim = st.checkbox('Trim surrounding whitespace')
    dedupe = st.checkbox('Remove exact duplicate rows (after trimming, if selected)')
    st.caption('No automatic imputation, category merging, outlier deletion or number conversion.')
    cleaned, log = clean(df, trim, dedupe)
    st.write(f'{len(cleaned):,} rows after selected changes')
    st.dataframe(cleaned.head(20), width='stretch', hide_index=True)
    st.caption('CSV exports prefix formula-like strings with an apostrophe for safer spreadsheet opening. This may affect numeric interpretation of negative strings; the input is unchanged.')
    st.download_button('Download cleaned CSV', safe_csv(cleaned), 'cleaned_data.csv', 'text/csv')
    after = inspect(cleaned)
    after['schema_findings'] = validate_schema(cleaned, schema) if schema is not None else []
    bundle = {'before': report, 'after': after, 'change_log': log,
              'export_note': 'Formula-like strings are prefixed with an apostrophe in CSV exports only.'}
    st.download_button('Download quality report + change log', report_json(bundle), 'quality_report.json', 'application/json')
    st.download_button('Download column profile', safe_csv(profile), 'column_profile.csv', 'text/csv')
st.divider()
st.caption('DataCheck · An explainable data quality project · Python / Pandas / Streamlit')
