# Hearing Lens

Hearing Lens analyzes community feedback and survey responses to identify recurring
themes, sentiment, participation patterns and questions that may need follow-up.
It accepts CSV and Excel files and runs natural-language processing models locally.

## Features

- CSV/XLSX upload with column mapping, empty-row cleaning and optional ID deduplication.
- Theme grouping with keyword labels, comment counts and supporting quotes.
- Local sentiment and emotion classification with date or hearing-level summaries.
- Representation-gap calculations using supplied categories and reference values.
- Question detection, grouping, prioritization and optional response matching.
- Five Streamlit panels: Themes, Sentiment and emotion, Timeline, Representation, and Questions.
- Optional reference shares and response text, plus a redacted labeled CSV download.
- One-page Word and PDF briefs with selected quotes and concise findings.
- A command-line workflow that exports structured JSON and offline timeline charts.

## Pipeline

```text
CSV / XLSX
    -> Column mapping and cleaning
    -> Redaction and local text analysis
    -> Themes | Sentiment & emotion | Timeline | Representation | Questions
    -> Streamlit views, labeled CSV, Word / PDF briefs
    -> Optional command-line JSON / HTML exports
```

Theme analysis uses MiniLM embeddings, BERTopic for larger inputs and K-means for
smaller inputs. KeyBERT generates keyword labels. Sentiment and emotion use local
transformer models. Representation metrics use provided data; demographic
characteristics are never inferred from names or comment text.

## Requirements

- Python 3.12 recommended (the cloud deployment requires Python 3.12)
- Python packages in `requirements.txt`
- Local spaCy, embedding, sentiment and emotion model files
- Internet access for initial package and model installation

Main libraries: pandas, Streamlit, spaCy, sentence-transformers, BERTopic,
KeyBERT, scikit-learn, PyTorch and Plotly.

## Install and run

From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m scripts.setup_theme_model
python -m scripts.setup_affect_models
python -m scripts.start_local
```

On Windows, activate the environment with `.venv\Scripts\activate`.
In the app, upload a file, map the comment column, validate the mapping and choose
**Analyze comments**. Explore the five result tabs and use **Download labeled CSV**
for comment-level labels. Below the panels, choose **Prepare Word brief** or
**Prepare PDF brief**, then use the corresponding download button. Optional reference shares and response text can be supplied
after validating the mapping. Choose **Methodology and limitations** in the
sidebar for model details and measured validation. The command below exports
combined analytical outputs.

## Hosting

A Streamlit Community Cloud entrypoint prepares pinned models at startup and uses
CPU-only dependencies. The free demo accepts at most 60 cleaned comments and
24,000 comment characters. For larger files, run `python -m scripts.start_local`
on your computer; the same dashboard processes the complete file within the
pipeline limits (up to 5,000 rows), without sampling. This binds only to your
computer at `127.0.0.1`, not your network. Keep the terminal open while using it.
If port 8501 is occupied, choose another with `--port 8502`. See [deployment instructions](docs/deployment.md) for setup,
resource limits and browser checks. Use fictional data for the development preview.

## Run the complete pipeline

```sh
python run_all.py data/samples/synthetic_theme_benchmark.csv \
  --comment-column comment_text \
  --date-column hearing_date \
  --id-column respondent_id \
  --subgroup role \
  --output-dir ../local-analysis/example-01
```

Choose a new output directory for each run. The input needs a comment column;
dates, respondent IDs and subgroup fields are optional. Run `python run_all.py
--help` for reference distributions, supplied response text and other options.
Included fictional samples can be used to try the workflow.

## Data handling

The app processes uploads in session memory. The command-line tool writes only
the exports requested by the user. Model files are installed during setup;
analysis does not send comments to an external inference service.

Automatic redaction and model predictions can be imperfect. Check quotes before
sharing them. Sentiment and emotion models target English text; unsupported
language and missing-data states are reported explicitly.

## Project structure

```text
app/             Streamlit interface and session controls
pipeline/        Ingestion, redaction and analytical modules
scripts/         Model setup, sample generation and validation utilities
data/samples/    Fictional development data
notebooks/       Reproducible technical experiments
tests/           Automated tests
docs/            Technical documentation
run_all.py       Complete local analysis command
```

## Tests

```sh
python -m pytest -q
```

## Technical documentation

- [Input schema](docs/schema.md)
- [Methodology](docs/methods.md)
- [Validation and measured limitations](docs/validation.md)
- [Word and PDF briefs](docs/community_brief.md)
- [App usage](docs/user_guide.md)
- [Command-line reference](docs/full_pipeline.md)
- [Troubleshooting](docs/troubleshooting.md)
