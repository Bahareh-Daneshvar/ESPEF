# Dataset files

Full data is stored as separate yearly raw and processed Parquets, with processed CSV.gz exports, in the [public yearly release](https://github.com/Bahareh-Daneshvar/ESPEF/releases/tag/espef-yearly-2026-10-02). The master manifest records yearly counts, file sizes and SHA-256 checksums. 2021–2025 are validated; 2026 remains pending Stage 1B and is not approved for modelling.

Annual audit JSONs are tracked in `data/audits/`. The release also includes quarterly summaries, exclusion reports, reconciliation audits and `SHA256SUMS`. Gzip files are reports or processed-corpus exports, not raw corpora. Checkpoint page caches and checkpoint archives are not release assets.

The 100-row CSV demonstrates the 2021 processed schema with 25 rows per quarter; it is not intended as a representative sample for analysis. The `stage1` folder records the preceding aggregate audit across the entire date range; abstract-present candidate counts are not final usable counts.

Original OpenAlex publication dates are preserved, including dates flagged for unverified precision.
