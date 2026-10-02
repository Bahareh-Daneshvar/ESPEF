# ESPEF yearly OpenAlex corpus

Storage partitions do not change scientific scope or temporal resolution. Dates are preserved as supplied by OpenAlex. No embeddings, model training, clustering, or drift detection are run by these scripts.

## Download the dataset

The primary cleaned datasets are the six yearly `espef_corpus_YYYY.parquet` files. Each matching `.csv.gz` is a convenience export of the same cleaned rows and columns. `openalex_espef_YYYY.parquet` is raw provenance data: all matching Works before abstract and title exclusions, not the cleaned analysis dataset. File sizes below are the release asset sizes in decimal MB.

| Year | Cleaned rows / raw rows | Status | Primary cleaned Parquet | Equivalent CSV.gz | Raw provenance Parquet |
|---|---:|---|---|---|---|
| 2021 | 106,415 / 136,446 | Validated | [espef_corpus_2021.parquet (51.34 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2021.parquet) | [espef_corpus_2021.csv.gz (49.27 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2021.csv.gz) | [openalex_espef_2021.parquet (115.99 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/openalex_espef_2021.parquet) |
| 2022 | 110,212 / 136,491 | Validated | [espef_corpus_2022.parquet (54.88 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2022.parquet) | [espef_corpus_2022.csv.gz (52.54 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2022.csv.gz) | [openalex_espef_2022.parquet (120.56 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/openalex_espef_2022.parquet) |
| 2023 | 131,821 / 162,966 | Validated | [espef_corpus_2023.parquet (66.51 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2023.parquet) | [espef_corpus_2023.csv.gz (63.39 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2023.csv.gz) | [openalex_espef_2023.parquet (144.17 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/openalex_espef_2023.parquet) |
| 2024 | 150,191 / 186,964 | Validated | [espef_corpus_2024.parquet (79.17 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2024.parquet) | [espef_corpus_2024.csv.gz (75.21 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2024.csv.gz) | [openalex_espef_2024.parquet (168.78 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/openalex_espef_2024.parquet) |
| 2025 | 133,117 / 175,549 | Validated | [espef_corpus_2025.parquet (73.43 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2025.parquet) | [espef_corpus_2025.csv.gz (69.74 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2025.csv.gz) | [openalex_espef_2025.parquet (157.75 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/openalex_espef_2025.parquet) |
| 2026 | 70,057 / 111,148 | **Pending Stage 1B** | [espef_corpus_2026.parquet (38.52 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2026.parquet) | [espef_corpus_2026.csv.gz (40.37 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/espef_corpus_2026.csv.gz) | [openalex_espef_2026.parquet (87.01 MB)](https://github.com/Bahareh-Daneshvar/ESPEF/releases/download/espef-yearly-2026-10-02/openalex_espef_2026.parquet) |

Use the cleaned Parquet by default; it is typed and compact for analysis. CSV.gz has the same cleaned records and fields for tools that prefer CSV; it is not a separate sample or corpus. Raw Parquet preserves OpenAlex provenance and includes records that fail the cleaned-data rules. The `espef_quarterly_YYYY.csv` release assets are count reports only, not quarterly record-level datasets. GitHub's automatically offered “Source code” ZIP is a repository snapshot, not the dataset. Audits, reconciliation evidence, the manifest, and `SHA256SUMS` are available in the [release inventory](https://github.com/Bahareh-Daneshvar/ESPEF/releases/tag/espef-yearly-2026-10-02).

2026 covers 1 January through 30 September 2026. Its extracted snapshot passed structural validation, but Stage 1B remains pending and the year is not approved for modelling. The other counts are deterministic usable-row counts, not human certification of language, dates, or research content. No modelling has begun.

`data/espef_dataset_manifest.json` records yearly statuses, row counts, file sizes and full-data checksums. Annual audit JSONs and their release copies document exclusions and quality flags. The separate `data/sample_espef_corpus.csv` contains 25 cleaned records per 2021 quarter selected in stored order for format/QC demonstration; it is not representative and is not one of the downloadable yearly datasets.

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

## Data dictionary

The primary cleaned Parquet and equivalent CSV.gz share these fields:

| Field | Type | Meaning |
|---|---|---|
| `openalex_id` | string | OpenAlex Work identifier URL; deduplication key. |
| `doi` | string | DOI URL when present. |
| `title` | string | Work title. |
| `abstract` | string | Reconstructed abstract text. |
| `publication_date` | string | OpenAlex publication date, preserved as supplied. |
| `type` | string | OpenAlex work type. |
| `language` | string | OpenAlex metadata language. |
| `primary_topic_id` | string | OpenAlex primary-topic identifier. |
| `primary_topic_name` | string | Name of the primary topic. |
| `primary_source_id` | string | OpenAlex source identifier from the primary location, when present. |
| `primary_source_name` | string | Name of the source from the primary location, when present. |
| `quality_flags` | string | JSON-encoded list of review flags; an empty list means no emitted flags. |
| `publication_year` | integer | Calendar year of `publication_date`. |
| `abstract_word_count` | integer | Word count of the reconstructed abstract. |

Raw provenance Parquet uses the OpenAlex field names: `id`, `doi`, `title`, `abstract_inverted_index`, `publication_date`, `publication_year`, `type`, `language`, `primary_topic`, `topics`, `primary_location`, `locations`, `created_date`, and `updated_date`. Nested OpenAlex objects are stored as JSON strings; `abstract_inverted_index` retains the source inverted-index representation. Raw rows can lack titles or abstracts and are not filtered to the cleaned row count.

## Load a yearly dataset

Download one of the cleaned Parquets above, then read selected columns with PyArrow (included in the project requirements):

```python
import pyarrow.parquet as pq

table = pq.read_table(
    "espef_corpus_2024.parquet",
    columns=["openalex_id", "publication_date", "title", "abstract"],
)
print(table.num_rows)
```

For larger workflows, iterate in batches rather than loading the whole year:

```python
parquet = pq.ParquetFile("espef_corpus_2024.parquet")
for batch in parquet.iter_batches(
    batch_size=10_000,
    columns=["openalex_id", "publication_date", "abstract"],
):
    print(batch.num_rows)
```

To read the equivalent compressed CSV with Python's standard library:

```python
import csv
import gzip

with gzip.open("espef_corpus_2024.csv.gz", "rt", encoding="utf-8", newline="") as stream:
    for row in csv.DictReader(stream):
        print(row["openalex_id"], row["publication_date"])
        break
```

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

Tests exercise cross-year ID overlap rejection, index collisions/gaps, raw/processed count reconciliation, checksum corruption, crash recovery from an orphaned cached page, and the unresolved-2026 loader gate.

## GitHub and storage

Repository: https://github.com/Bahareh-Daneshvar/ESPEF. The yearly raw and processed Parquets, processed CSV.gz exports, audit files, manifest and `SHA256SUMS` are distributed as [release assets](https://github.com/Bahareh-Daneshvar/ESPEF/releases/tag/espef-yearly-2026-10-02). Full yearly Parquets and checkpoint page caches remain excluded from normal Git history; checkpoint caches are not release assets.

## Stage 1 concerns remain

Annual storage reduces peak processing memory; it does not remove missing abstracts, January-1 date imprecision, preprint/publication date ambiguity, source shifts or late-period indexing changes. No date redefinition or corpus narrowing is adopted.
