# 🔎 DataCheck — Data Quality Inspector

<p align="center"><a href="https://wruj3msd9wtshpkozw4lvd.streamlit.app/"><img src="./assets/datacheck-cover-v2.jpg" alt="DataCheck — Data Quality Inspector" width="100%"></a></p>

[View the full-resolution cover](./assets/datacheck-cover-v2.jpg)

[**Open the public Streamlit app**](https://wruj3msd9wtshpkozw4lvd.streamlit.app/)

*AI-generated product illustration; the dashboard artwork is not an exact screenshot.*

**Turn an unfamiliar CSV into an explainable data quality report.**

Built by **Blessing Sekeramavi** with Python, Pandas and Streamlit.

DataCheck helps analysts inspect data before reporting or modeling. It surfaces reviewable findings, explains its assumptions and keeps cleaning decisions explicit.

## Features

- Optional student schema: required columns/values, unique student IDs, finite numeric values, study hours 0–168, final scores 0–100, and exact allowed categories.

- CSV upload with delimiter and encoding controls, plus Excel `.xlsx` and `.xls` uploads with a worksheet selector.
- Completeness metrics and column health chart.
- Blank cells, exact duplicate rows and surrounding whitespace checks.
- Case/whitespace category variants and mixed numeric values.
- Infinite values and potential outliers using the 1.5 × IQR rule.
- Opt-in whitespace trimming and duplicate removal with before/after reports.
- Downloadable cleaned CSV, column profile and JSON report with a change log.
- Synthetic education dataset with intentionally introduced issues.

## Run locally

Use Python 3.11 or 3.12. From the project folder:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`.

Open the local address printed by Streamlit. Without an upload, the sample data loads automatically.

## Example workflow

1. Explore the included sample or upload a CSV.
2. Review column health and read the findings.
3. Inspect suspicious values in the preview or original dataset.
4. Select cleaning actions, review the preview and download the results.
5. Keep the JSON report alongside your analysis for a transparent record.

## Excel uploads

Upload an unencrypted `.xlsx` or `.xls` workbook, then select its worksheet in the sidebar. The first row supplies column headers. Analysis and cleaning apply only to the selected sheet. CSV exports and JSON reports work the same as for CSV uploads.

Text identifiers retain leading zeros. Numeric Excel formatting such as a `0000` display mask is not retained. Formula cells use saved results; formulas are not recalculated. Recalculate and save the workbook in Excel first if necessary. Blank cells and literal `NA` categories follow the CSV rules. The application does not preserve workbook formatting or export cleaned workbooks. Compressed `.xlsx` files are limited to 100 MB expanded contents, in addition to the 20 MB upload and two-million-cell analysis caps.

## Methodology and limitations

| Check | Definition |
|---|---|
| Missing | Empty, whitespace-only or null cells. Literal `NA` and `N/A` are retained. |
| Completeness | 100 × (1 − blank cells / total cells). Undefined for zero cells. This is not an overall quality score. |
| Duplicate rows | Exact repeated rows after the first occurrence. Duplicate IDs require domain-specific checks. |
| Category variants | Number of groups whose values differ only by case or surrounding whitespace. |
| Numeric-like | At least 80% of nonblank values parse numerically. Remaining values are flagged for review. |
| Potential outliers | Finite numeric values outside Q1 − 1.5×IQR and Q3 + 1.5×IQR. Skipped with fewer than four finite values or zero IQR. |

Counts may overlap. Numeric identifiers can be classified as numeric-like, but remain strings. Leading zeros are preserved. Outliers and category variants are suggestions for review, not proof of errors. The app does not validate real-world accuracy, email addresses, dates, foreign keys or domain-specific ranges. It does not impute missing values or silently delete outliers.

CSV exports prefix formula-like strings (`=`, `+`, `-`, `@`, tabs and carriage returns, including after surrounding whitespace) with an apostrophe. This mitigates spreadsheet formula execution but can affect numeric interpretation of negative strings. Original data and JSON metrics are unchanged. Review exports before using them in another pipeline.

Files are processed in server memory; the application contains no persistence or outbound API calls. Shared hosting infrastructure may retain operational logs. Use anonymized data for public demos. Upload cap: 20 MB; analysis cap: two million cells. Larger files may require substantial memory before the cell cap is checked. Duplicate CSV column names are normalized by Pandas during parsing.

## Validation

```bash
python -m unittest discover -s tests -v
```

Tests cover identifier preservation, missing values, mixed numeric data, infinities, outliers, category variants, empty data, constant data, non-destructive cleaning and formula escaping. GitHub Actions runs these tests on pushes and pull requests.

## Repository structure

```text
app.py                       Streamlit dashboard
quality.py                   Analysis, cleaning and export functions
data/sample_students.csv     Synthetic demonstration data
data/example_report.json     Reproducible sample findings
tests/test_quality.py        Core behavioral tests
.streamlit/config.toml       Dashboard theme and upload limit
.github/workflows/tests.yml  Continuous integration
```

## Optional Google Colab launcher (temporary sharing)

Open `DataCheck_Colab.ipynb` through File → Upload notebook in Google Colab. Run the first two code cells in order. The notebook embeds the project source, creates every required file, installs dependencies and runs the tests before starting the server. No archive upload or hardcoded external file path is needed.

The second cell starts Streamlit in the background on port 8501, waits for its health endpoint, installs localtunnel and prints a `https://…loca.lt` sharing URL. If the tunnel prompts for a password, use the value printed by the notebook. Share only anonymized sample data. Keep the Colab runtime connected; the URL stops working when either process or the runtime stops. Logs are saved under `/content/datacheck_*.log`. The final cell stops notebook-owned processes. The notebook launcher has been syntax checked here; a live Colab tunnel has not been verified from this environment.

## Permanent deployment options

### Streamlit Community Cloud

Use `app.py` as entry point, Python 3.12 and the provided `requirements.txt`. This is suitable for a portfolio URL, but inactive apps sleep, so it is not guaranteed continuous uptime.

### Render

The included `render.yaml` requests a **paid Starter web service**; deploying it may incur charges. Connect your GitHub repository in Render and create a Blueprint from this file after reviewing the plan and price. The service binds to Render's injected `$PORT` and exposes `/_stcore/health`. No deployment or purchase has been performed.

### Hugging Face Docker Space

The Dockerfile runs as a non-root user on port 7860. Create a Docker Space and upload the project files. Add the following YAML front matter at the beginning of that Space's README (not in a fenced code block):

```yaml
---
title: DataCheck
emoji: 🔎
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---
```

Check the host's current account and hardware requirements before deploying; continuous availability depends on the selected hardware and sleep policy.

## Publish a live demo

Push these files to a GitHub repository named `DataCheck`. In Streamlit Community Cloud, select that repository and `app.py` as the entry point. Add the resulting app URL to the repository's About section. The public Streamlit app is live at https://wruj3msd9wtshpkozw4lvd.streamlit.app/

## Portfolio description

> Built an interactive CSV quality inspector using Python, Pandas and Streamlit, with explainable checks, non-destructive cleaning, downloadable audit reports and automated tests.

## Future work

Schema-based validation, configurable missing tokens, date checks, business rules and scalable processing for larger datasets.

## Deployment status and sources

The app has been tested directly in the workspace, including a successful HTTP health check. The Python application is deployed publicly on Streamlit Community Cloud: https://wruj3msd9wtshpkozw4lvd.streamlit.app/ . It runs independently of your laptop or this chat. Free hosting may sleep after inactivity; continuous uptime is not guaranteed.

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- https://huggingface.co/docs/hub/spaces-sdks-docker
- https://github.com/localtunnel/localtunnel
