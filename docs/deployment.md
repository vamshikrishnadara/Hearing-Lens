# Deploying the dashboard

## Streamlit Community Cloud

Use the free Community Cloud service with a GitHub account. The app does not
require a paid inference API or GPU. Free resource availability is not guaranteed:
measure the actual deployed app before relying on it for a session.

1. Sign in at https://share.streamlit.io/ and connect the GitHub repository.
2. Create an app from the branch containing these deployment files.
3. Set the entrypoint to `deployment/cloud_app.py` and select **Python 3.12** in
   Advanced settings. No app secrets are required for the public model downloads.
4. Deploy. The dependency file next to this entrypoint installs CPU-only PyTorch
   and the English redaction model. Initial startup downloads the three pinned
   analytical models; this may take several minutes.
5. Open the generated app URL and verify the workflow with fictional feedback.

The free deployment is a small-sample demo: at most **60 cleaned comments** and
**24,000 comment characters** per file. The row and text checks run after mapping
and before redaction/inference; a second check protects the analysis runtime.
An oversized upload gets a clear message before a job is started. Comments are
never sampled or silently discarded to meet these limits. These conservative
limits are not a latency guarantee: free hosting can still throttle small jobs.

For larger files, install the local requirements/models and run:

```sh
python -m scripts.start_local
```

This starts the full dashboard at `http://127.0.0.1:8501`, bound to the local
computer only. Keep the terminal open and press Ctrl+C to stop. Use `--port 8502`
if 8501 is occupied. The launcher explicitly selects local mode, retains the
pipeline's 5,000-row/text limits, and runs the same models, grouping and exports.
No paid service or upload to the public site is needed. Do not split a full file
just to bypass the demo cap: themes and representation comparisons would change.
The free demo does not support 2,000-comment analyses. Use the local dashboard
for that workload; local timings do not establish hosted capacity.

The normal local entrypoint remains `app/streamlit_app.py`; it expects models to
be installed already. To exercise the cloud entrypoint locally after installing
the root requirements and spaCy model, run:

```sh
python -m streamlit run deployment/cloud_app.py
```

`deployment/requirements.txt` targets Python 3.12 on Linux x86-64 CPU hosting.
PyTorch is installed from its official CPU wheel URL; other packages resolve
from PyPI. Do not add the PyTorch wheel server as a global extra index: uv
can select unrelated packages from that server and reject valid PyPI versions. Use the root requirements
for local macOS/Windows setup. Cloud dependency installation must be checked in
the hosting build logs; a local run is not a Linux build verification.

## Startup and resource controls

`scripts/model_setup.py` pins each analytical model to an immutable revision.
It checks provenance and required files, resumes incomplete downloads, and refuses
to silently replace a cache labeled with a different revision. Downloads happen
before the upload interface opens. Analysis reads local files and does not send
uploaded text to a model API. File presence checks are not cryptographic integrity
verification; use a fresh cache if model files may have been modified.

Models are shared within one process; analytical inputs and results are not
cached across sessions. Analysis requests run one at a time to avoid concurrent
model loading and multiplying inference memory. Waiting users see a queue
message for up to 30 seconds; if the lock remains occupied, the new request ends
without starting inference. This does not cancel or time-limit the active job.
Closing a browser tab does not reliably establish that active work stopped. This is suitable for a
small demonstration, not high-traffic service capacity.

The cloud entrypoint defaults to two CPU threads. `HEARING_LENS_THREADS` can
select 1–4 threads; the local entrypoint defaults to four. During analysis this
limit covers PyTorch and the loaded OpenMP/BLAS pools used by numerical libraries.
Pool limits are restored before releasing the shared analysis lock. This bounds
parallel numerical work; it is not a hosted speed or memory guarantee. Uploads are limited to
10 MB at the Streamlit boundary. The cloud entrypoint sets
`HEARING_LENS_DEPLOYMENT=community_cloud` to activate the demo admission limits;
the local launcher selects `local`. Existing pipeline row/text limits still apply.
CORS and XSRF protections remain enabled; usage telemetry is disabled. Source
watching is disabled to avoid scanning lazy model-library modules and importing
unrelated optional dependencies. Restart the local server after code changes;
Community Cloud redeploys from the configured GitHub branch.

Model preparation errors hide the upload controls and show a fixed message.
Check network access, dependency installation and storage if startup fails. An
inference failure hides partial results. Restarting a process discards in-memory
sessions. Hosting providers may independently retain infrastructure logs; do not
upload confidential material to this development preview.

The analysis status displays the current stage. The `hearing_lens.analysis`
logger emits fixed stage names and elapsed seconds, with a failure marker if a
run raises an exception. These messages contain no uploaded text, filenames,
IDs, subgroup labels or exception messages. An initial run can include model
loading and clustering-library compilation; use the timings to distinguish that
from inference or queue waiting. A slow hosted run is not diagnosed merely
because the same file runs quickly on a local computer.

Word and PDF export libraries are included in the root requirements. PDF uses
ReportLab's bundled fonts and needs no extra operating-system converter.

## Performance and workflow checks

Generate a reproducible 2,000-comment fictional CSV and exercise the real models:

```sh
python -m pip install -r requirements-dev.txt
python -m scripts.benchmark_dashboard \
  --entrypoint app/streamlit_app.py \
  --output ../local-analysis/dashboard-benchmark.json \
  --fixture-output ../local-analysis/fictional-2000.csv
```

The fixture uses 2,000 distinct authored text combinations with repeated phrases;
it measures software load, not model accuracy. The report records validation and
analysis-to-render times, sampled peak process RSS, model cache counters, five-panel
completion and exported row count. Model/package installation and first page load
are outside the timed validation-to-render interval. Run in a fresh process for
cold model loading. Machine load, architecture and host throttling affect results.

AppTest is not browser or hosted acceptance. Use the complete 2,000-row fixture
locally. The cloud entrypoint rejects it by design. For cloud startup testing,
pass `--entrypoint deployment/cloud_app.py --rows 60`; use at most 24,000 comment
characters. On the public URL, separately check:

- Upload a permitted small fictional CSV, map comments, dates, IDs and role, then validate.
- Time analysis through display of all five panels and record validation time separately.
- Upload an oversized fixture and confirm it is rejected before analysis starts.
- Download the labeled CSV and check row count and exclusion of identifiers.
- Try missing optional date/subgroup/reference/response inputs; inspect the
  explanatory states, then change uploads and confirm old results disappear.
- Open an independent browser session and confirm it cannot see the first
  session's input or results. Check resource limits with two active sessions.
- Check the complete upload-to-results and download flow against the user
  guide; record actual time and fix unclear instructions.

If the host runs out of memory or exceeds the performance target, the hosted
check has not passed. A local timing cannot establish free-host feasibility.

References: [Community Cloud dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
[resource limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#resource-limits),
[deployment steps](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
