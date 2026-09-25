# CFPB public development sample

Source checked September 25, 2026. This is a small, historical development corpus
for testing varied open text. It is not resident input, a Chicago hearing sample,
or an estimate of consumer experience in the population.

## Source and usage basis

- [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/): the Bureau explicitly permits using, analyzing, and building on its published complaint data. It cautions that complaints are not a representative statistical sample of all consumers.
- [Official narrative archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/): lists downloadable historical records, including December 2011 through April 2018. This archive was used, not a third-party mirror or a restricted portal.
- [CFPB legal notices](https://www.consumerfinance.gov/privacy/website-privacy-policy/#legal-notices): Bureau-created information is public domain, with attribution encouraged; third-party material can carry separate rights. We record the database's express reuse permission rather than assigning a new open-source license to consumer-written narratives.

Keep the downloaded archive, selected narratives, public complaint identifiers,
and detailed review reports local. Commit scripts, fictional tests, source notes,
and aggregate results. Attribution does not imply CFPB endorsement. The published
text already contains masking, but our redaction still runs before review output.

## Fixed selection

- Archive: `CCDB_Export_1_December_2011_through_April_2018.zip`.
- Eligible: nonempty narratives with a date received in calendar year 2017.
- Draw: 100 distinct complaint IDs by reservoir sampling, seed `20260925`, in archive row order; output sorted by numeric complaint ID.
- No product, company, length, or quality filter. Repeated IDs are skipped after their first eligible occurrence; distinct complaints with identical wording are retained.
- Fields retained locally: `complaint_id`, `comment_text`, `date_received`, `product`, and `issue`. Company, location, tags, and response metadata are omitted.
- Only `comment_text` enters theme analysis. Product/issue are not ground-truth themes, so no accuracy or ARI score is calculated for this corpus.

The source has 1,031,863 rows; 115,311 unique records meet the selection criteria.
No duplicate eligible IDs were encountered. Archive SHA-256:
`9d4fabeb5db925ce4303e81ab448f44531303a995aec1a935abc09156f2fc533`.
Selected CSV SHA-256:
`e7faa7957fe104113c2e145b7c65b36100025d6a4550cf31eb0ebcae6b362318`.

The manifest records source URLs, hashes, archive member, seed, counts, creation
time, and selected public IDs. Same bytes and seed reproduce the sample; an
upstream replacement may change it, so compare hashes. Hashes verify file
consistency, not authenticity or anonymity.

## Reproduce locally

These are explicit offline development utilities. They do not change the
application's in-memory upload processing. The archive download is about 135 MB;
its CSV is read as a stream without extracting it to disk.

```sh
mkdir -p data/public_samples
curl -fL 'https://files.consumerfinance.gov/f/documents/CCDB_Export_1_December_2011_through_April_2018.zip' -o data/public_samples/cfpb_archive.zip
python -m scripts.prepare_cfpb_sample --archive data/public_samples/cfpb_archive.zip --output-dir data/public_samples/cfpb_2017
```

`data/public_samples/` is ignored by Git. Preparation refuses to overwrite an
existing sample or manifest. No network request occurs inside the Python utility.
It copies public source narrative text as supplied, apart from trimming outer
whitespace; redaction is applied during validation, not silently to the archive.
For today's run, the sample and manifest were saved outside the repository in
`daily-evidence/2026-09-25/public-sample/`.
