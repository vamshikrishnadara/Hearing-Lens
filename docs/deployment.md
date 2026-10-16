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

The normal local entrypoint remains `app/streamlit_app.py`; it expects models to
be installed already. To exercise the cloud entrypoint locally after installing
the root requirements and spaCy model, run:

```sh
python -m streamlit run deployment/cloud_app.py
```

`deployment/requirements.txt` targets Linux CPU hosting. Use the root requirements
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
model loading and multiplying inference memory. Waiting users will see the
analysis spinner until the preceding request finishes. This is suitable for a
small demonstration, not high-traffic service capacity.

The cloud entrypoint defaults to two PyTorch CPU threads. `HEARING_LENS_THREADS` can
select 1–4 threads; the local entrypoint defaults to four. Uploads are limited to
10 MB at the Streamlit boundary. Existing pipeline row/text limits still apply.
CORS and XSRF protections remain enabled; usage telemetry is disabled.

Model preparation errors hide the upload controls and show a fixed message.
Check network access, dependency installation and storage if startup fails. An
inference failure hides partial results. Restarting a process discards in-memory
sessions. Hosting providers may independently retain infrastructure logs; do not
upload confidential material to this development preview.

## Performance and workflow checks

Generate a reproducible 2,000-comment fictional CSV and exercise the real models:

```sh
python -m pip install -r requirements-dev.txt
python -m scripts.benchmark_dashboard \
  --entrypoint deployment/cloud_app.py \
  --output ../local-analysis/dashboard-benchmark.json \
  --fixture-output ../local-analysis/fictional-2000.csv
```

The fixture uses 2,000 distinct authored text combinations with repeated phrases;
it measures software load, not model accuracy. The report records validation and
analysis-to-render times, sampled peak process RSS, model cache counters, five-panel
completion and exported row count. Model/package installation and first page load
are outside the timed validation-to-render interval. Run in a fresh process for
cold model loading. Machine load, architecture and host throttling affect results.

AppTest is not browser or hosted acceptance. On the public URL, separately check:

- Upload the generated CSV, map comments, dates, IDs and role, then validate.
- Time analysis through display of all five panels; target under three minutes
  for 2,000 comments after startup. Also record validation time separately.
- Download the labeled CSV and check row count and exclusion of identifiers.
- Try missing optional date/subgroup/reference/response inputs; inspect the
  explanatory states, then change uploads and confirm old results disappear.
- Open an independent browser session and confirm it cannot see the first
  session's input or results. Check resource limits with two active sessions.
- Ask someone unfamiliar with the interface to complete upload-to-results and
  download without coaching; record actual time and fix confusing steps.

If the host runs out of memory or exceeds the performance target, the hosted
check has not passed. A local timing cannot establish free-host feasibility.

References: [Community Cloud dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies),
[resource limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#resource-limits),
[deployment steps](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
