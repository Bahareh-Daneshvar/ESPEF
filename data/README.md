# Dataset files

See the root README's [Download the dataset](../README.md#download-the-dataset) section for each yearly file, row counts, sizes, format guidance, data dictionary, and Python examples. The [public yearly release](https://github.com/Bahareh-Daneshvar/ESPEF/releases/tag/espef-yearly-2026-10-02) contains the six primary cleaned `espef_corpus_YYYY.parquet` files, equivalent CSV.gz convenience exports, and raw `openalex_espef_YYYY.parquet` provenance files. The master manifest records yearly counts, file sizes, and SHA-256 checksums. 2021–2025 are validated; 2026 remains pending Stage 1B and is not approved for modelling.

Annual audit JSONs are tracked in `data/audits/`. The release also includes count-only quarterly CSV reports, exclusion reports, reconciliation evidence, the manifest, and `SHA256SUMS`. Quarterly CSVs are not record-level data. GitHub's “Source code” ZIP is a repository snapshot, not a dataset. All raw data, cleaned data, audits, reconciliation evidence, manifests, checksums, and checkpoints are retained; checkpoint archives are not release assets.

The 100-row `data/sample_espef_corpus.csv` demonstrates the 2021 processed schema with 25 rows per quarter; it is not representative and is not a yearly corpus download. The `stage1` folder records the preceding aggregate audit across the entire date range; abstract-present candidate counts are not final usable counts.

Original OpenAlex publication dates are preserved, including dates flagged for unverified precision.

## Possible overlaps to review

These are review candidates only. No files have been removed, and path overlap does not prove byte-for-byte identity or that an archive has no independent restore value.

- `ESPEF_Checkpoints_2021.zip`, `ESPEF_Checkpoints_2022.zip`, and `ESPEF_Checkpoints_2023_PARTIAL.zip`: their 690, 721, and 665 file paths respectively also appear under `data/checkpoints/`. They may be snapshots of the same page caches, but could differ in content or checkpoint timing.
- `ESPEF_Review_Audit_2021_2026.zip`: all 42 archive member paths also exist as individual workspace files. It may be a redundant bundle, but could preserve a distinct point-in-time copy.
- `data/sample_espef_corpus.csv`: its selected 2021 records are a subset of the cleaned 2021 corpus, but the small file serves as a schema/QC example and is not interchangeable with a full-year download.
