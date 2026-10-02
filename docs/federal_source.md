# Federal development sample

The third corpus is now available locally. The direct Regulations.gov demo-key
request returned HTTP 429, so the completed sample uses the publicly accessible
[Mirrulations archive](https://registry.opendata.aws/mirrulations/), managed by
Moravian University. This is an archive of Regulations.gov records, not a direct
agency download or a new agency API key. No quota was bypassed.

Parent: [FAA-2018-1084-0001, External Marking Requirement for Small Unmanned Aircraft](https://www.regulations.gov/document/FAA-2018-1084-0001).
The archive listed 418 comment records. The fixed main benchmark contains the
first 300 nonempty, unrestricted, non-withdrawn inline comments for that parent,
in archive-key order. The earlier 100-row sample is retained separately. Selection
uses source metadata and text availability, not model scores, quote length, or
whether a result passes. Attachments are excluded. This convenience sample is
not representative of Chicago participation, all federal comments, or public opinion.

```sh
python -m scripts.prepare_federal_mirror --rows 300 --output-dir data/public_samples/federal_mirror_300
```

Each response is saved locally with its source URL and SHA-256. The output manifest
records selected public record IDs, the parent/docket, retrieval time, source
hashes, selection rules, and the CSV checksum. Import verifies parent membership
and excludes withdrawn/restricted records. A later archive revision can change
the sample, so compare hashes before claiming reproduction.

Main CSV SHA-256:
`c49045c8e56baf08f27c6f8926604c1dc35aea8d3656efd70d2b1dce877dc219`.

The AWS registry lists the archive with a Public Domain Mark. That listing does
not resolve every submitter's rights or mean identifying information is safe to
republish. Raw responses, narratives, identifiers, manifests, and detailed review
packets remain in ignored local development folders. Only preparation code,
source notes, and aggregate results are committed. Public samples are never
preloaded production inputs, and the application never calls an agency API.

The original direct API utility remains available for a later independently
configured key. The mirrored sample removes the development-data access blocker;
it does not imply a human quality review has occurred.
