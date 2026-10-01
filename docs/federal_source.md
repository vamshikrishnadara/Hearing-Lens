# Federal development sample - October 1, 2026

The required third corpus is not prepared yet. The official Regulations.gov API
was reachable and returned document metadata/comment counts, but the download
attempt hit HTTP 429 using its public DEMO_KEY. Do not repeatedly retry a rate
limit or mark the corpus validated without a complete sample.

Selected parent document:
[FAA-2018-1084-0001, External Marking Requirement for Small Unmanned Aircraft](https://www.regulations.gov/document/FAA-2018-1084-0001).
This is a single federal docket with public inline comments, a development source
rather than a Chicago participation sample. Its API listing reported 418 comments
at the metadata check. It is chosen for reproducible access to inline comment text,
not to optimize model outcomes. Attached-only comments are outside this initial
sample and must be disclosed as a selection limitation.

The development-only downloader uses the [official GSA API](https://open.gsa.gov/api/regulationsgov/).
It selects the first 20 nonempty inline comments in posted-date order, strips HTML,
preserves a source manifest/checksum locally, and verifies the docket. Ties use
the API's returned order; later API updates can change the draw. The saved hash
and IDs identify the exact sample actually tested, not a claim of representativeness.

```sh
python -m scripts.prepare_federal_sample --document-id FAA-2018-1084-0001 --rows 20
```

The script uses `REGULATIONS_API_KEY` if configured, otherwise the documented
public demo key. Never put a private key in a command, file tracked by Git, or
chat message. A downloaded export is another possible input after provenance
and schema checks. The current script checkpoints successful API responses in
its ignored output folder, enabling a later retry without losing progress.

Default output is `data/public_samples/federal/`, ignored by Git. Public comment
authors can retain rights; public visibility does not automatically make their
writing public domain. Keep narratives, identifiers, manifests, and review
packets local. Publish preparation code and aggregate findings only. No federal
comment is a preloaded production input, and no agency API is called by the app.
