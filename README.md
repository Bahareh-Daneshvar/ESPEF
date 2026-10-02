# ESPEF yearly OpenAlex corpus

Storage partitions do not change scientific scope or temporal resolution. Dates are preserved as supplied by OpenAlex. No embeddings, model training, clustering, or drift detection are run by these scripts.

## Current extraction status

2021: 136,446 retrieved Works; 106,415 pass the documented quality rules. Extracted on 1 October 2026 UTC. 2022: 62,600 checkpointed records, incomplete. 2023–2026: not started. OpenAlex returned HTTP 429 and extraction is paused. No modelling has begun. These counts describe rule-based validation, not human certification of language, dates or research content.

`data/espef_dataset_manifest.json` records these statuses and full-data checksums. `data/audits/espef_audit_2021.json` is a compact summary; the complete source distributions and duplicate groups are preserved in `espef_audit_2021_full.json.gz`. The CSV sample contains 25 processed records per 2021 quarter selected in stored order, for format/QC demonstration only; it is not a representative scientific sample or a reduced modelling corpus.

## Frozen corpus definition

- OpenAlex API default curated core, explicitly `corpus=core`.
- `primary_topic.subfield.id:1702` only; secondary-topic membership is not used.
- Metadata language `en`; types `article|conference-paper|preprint`.
- 2021-01-01 through 2026-09-30 inclusive; no citation filtering or citation inputs.
- Raw files retain all matching Works, including missing abstracts, so exclusions can be audited.
- Processed files require a nonempty title, valid date inside the year, and a deterministically reconstructable abstract. Empty, exact metadata-placeholder and numeric-only abstract text is unusable. No minimum word count is imposed. Very short text and suspected language-label errors are flagged for review. Text-language flags do not silently replace the confirmed OpenAlex language rule.
- OpenAlex ID is the deduplication key. Repeated DOIs and normalized titles are indicators for review, not automatic deletions. Cross-year ID overlap blocks completion.

All years share the same configuration and quality rules. Annual dates are the only changing scope parameter. Quarter requests are disjoint subdivisions inside the current annual range, use cursor pagination, and never run across multiple years concurrently.

## Outputs

```
data/raw/openalex_espef_2021.parquet          # ... through 2026
data/processed/espef_corpus_2021.parquet     # ... through 2026
data/audits/espef_audit_2021.json            # ... through 2026
data/audits/espef_quarterly_2021.csv         # ... through 2026
data/audits/espef_exclusions_2021.json       # ... through 2026
data/espef_dataset_manifest.json
data/checkpoints/2021/Q1/                   # cursor states and immutable page caches
```

Nested raw metadata is retained losslessly as JSON strings in Parquet columns, including abstract inverted indices and version/source locations. Processed files contain reconstructed text and flattened primary-topic/source identifiers.

Missing, invalid and placeholder abstracts are distinguished in yearly audits. Audits retain work-type/source distributions, quarter counts, January-1 concentration, duplicate groups, language-label mismatches and text-language review flags, file sizes, checksums and extraction timestamps. `usable_works` means passes the documented deterministic rules; it is not a guarantee of historical text availability or a human-certified scientific corpus.

## Install and run

```bash
python -m pip install -r requirements.txt
python scripts/download_openalex.py
```

Run from any directory; the script resolves this project from its own location. Years complete in ascending order. To stop after 2021:

```bash
python scripts/download_openalex.py --years 2021
python scripts/validate_dataset.py --year 2021
```

The normal command is also the resume command. Completed yearly Parquets are SHA-256 verified and skipped. Partial quarters resume from cursor states. A committed page with an uncommitted state is reused without another API download. Partial `.tmp` Parquets are rebuilt from cached pages, never presented as completed years. A year must pass count reconciliation, reconstruction rules, ID checks and Parquet validation before the next starts.

A free OpenAlex API key can be supplied through `OPENALEX_API_KEY` using your environment or secret manager. Never paste it into source, reports or Git. The API also accepts unauthenticated requests; daily/rate limits pause extraction with checkpoints. The script does not acquire keys, spend beyond an account's API controls, schedule itself, or bypass limits. `--request-budget` controls the maximum request attempts for a run without changing the corpus or completed-file fingerprints.

A live API is not a frozen snapshot. If counts change during a year, reconciliation fails and the next year is blocked. Preserved responses and timestamps identify the actual extraction. Do not silently merge a fresh query with completed files from a changed configuration.

## Load one temporal window

```python
from scripts.load_temporal_partition import scan_window
for batch in scan_window('2023-04-01', '2023-06-30',
                         columns=['openalex_id', 'title', 'abstract', 'publication_date']):
    # Audit/process the batch; modelling still needs explicit approval.
    pass
```

The loader selects only required yearly files and pushes the exact date range into a streaming Parquet scanner. It does not combine yearly files or load the corpus into RAM. Quarterly, semi-annual and annual windows use the unchanged publication dates.

2026 remains `pending_stage_1B`. The default loader refuses windows touching 2026; `allow_unresolved_2026=True` is an explicit audit-only override. Successful extraction of 2026 is not evidence that its indexing is complete. All years remain unapproved for modelling until the final data audit is reviewed.

## Verification

```bash
python -m unittest discover -s tests -v
```

Tests exercise index collisions/gaps, raw/processed count reconciliation, checksum corruption, crash recovery from an orphaned cached page, and the unresolved-2026 loader gate.

## GitHub and storage

Repository: https://github.com/Bahareh-Daneshvar/ESPEF. This repository stores reproducibility materials and a small audit sample; full yearly Parquets and resume page caches are distributed separately to the project owner. They are not yet deposited in a public research data archive.

Code, config, queries, audits, manifest and a small sample can be stored in normal Git. Full yearly Parquets and checkpoint page caches are excluded by `.gitignore`; annual partitioning does not itself make large files suitable for normal Git history. Full-data storage must be chosen after actual file sizes are known.

## Stage 1 concerns remain

Annual storage reduces peak processing memory; it does not remove missing abstracts, January-1 date imprecision, preprint/publication date ambiguity, source shifts or late-period indexing changes. No date redefinition or corpus narrowing is adopted.
