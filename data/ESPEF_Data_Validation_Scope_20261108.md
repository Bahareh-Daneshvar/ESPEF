# ESPEF dataset validation and intended scope (8 November 2026)

## Dataset release decision

The six OpenAlex yearly extracts released under [`espef-yearly-2026-10-02`](https://github.com/Bahareh-Daneshvar/ESPEF/releases/tag/espef-yearly-2026-10-02) are **validated for structural integrity, deterministic cleaning, documented row-count reconciliation, and release distribution**. They may be downloaded and used for research analyses with the temporal and metadata limitations below.

This statement approves **the documented dataset release**, not every downstream modelling or publication claim. It does **not** certify topical ground truth, first appearance of a research topic, or numerical results reported in an associated manuscript.

| Partition | Date interval in frozen extract | Raw works | Cleaned usable works | Data-release validation |
|---|---|---:|---:|---|
| 2021 | 2021-01-01 to 2021-12-31 | 136,446 | 106,415 | Validated |
| 2022 | 2022-01-01 to 2022-12-31 | 136,491 | 110,212 | Validated |
| 2023 | 2023-01-01 to 2023-12-31 | 162,966 | 131,821 | Validated |
| 2024 | 2024-01-01 to 2024-12-31 | 186,964 | 150,191 | Validated |
| 2025 | 2025-01-01 to 2025-12-31 | 175,549 | 133,117 | Validated |
| 2026 | 2026-01-01 to **2026-09-30** | 111,148 | 70,057 | **Validated partial-year snapshot (Q1–Q3)** |

## Basis of validation

- The frozen master [`espef_dataset_manifest.json`](espef_dataset_manifest.json) records `status: validated` for **each** year and `all_years_validated: true`, together with counts, byte sizes, SHA-256 fingerprints and audit paths. Its original metadata is preserved rather than rewritten after the frozen release.
- The independent [Stage 1B v2 audit](stage1b/v2/ESPEF_Stage1B_Audit.md) reports that all 12 raw/processed Parquet source files matched their frozen-manifest SHA-256 checksums, byte sizes and row counts **before and after** its audit. The corresponding [`stage1b_modelling_manifest.json`](stage1b/v2/stage1b_modelling_manifest.json) records the verification evidence, originally checked on **2 October 2026**. This statement records that previously performed validation; it does not claim a fresh full-file download or byte-level recheck on 8 November.
- The Stage 1B quarterly QC records 2026 usable counts of **26,966** (Q1), **21,945** (Q2), and **21,146** (Q3), summing to **70,057**. No fourth-quarter records are present.
- Cleaned records satisfy the existing deterministic rules for a non-empty title, reconstructable abstract and valid in-partition date. The stored `quality_flags` document additional potential concerns; they are **not** all human-reviewed or corrected.

## Important scope limitations

1. **Partial year and right censoring.** The 2026 snapshot covers January–September only. It is not a complete 2026 annual population, and OpenAlex indexing may be delayed. No annual 2026 extrapolation or comparison of full-year totals should be inferred from these data.
2. **Marked source-composition shift.** In the frozen Stage 1B QC, Zenodo represents **25.03%**, **39.16%**, and **45.50%** of *known-source* records in 2026 Q1, Q2 and Q3, respectively, while the corresponding arXiv shares are **1.52%**, **1.86%**, and **1.55%**. These are descriptive source shares, not errors proven by this audit; they materially limit unqualified cross-period modelling comparisons. Publication type and usable-rate composition also vary.
3. **Publication metadata is not ground truth.** Recorded OpenAlex publication dates may have precision and preprint-versus-published-version ambiguities. The primary-topic assignment and metadata language do not establish human-adjudicated scientific-topic labels. Short abstracts and suspected text-language mismatches are flagged for review rather than silently removed.
4. **Dataset validation is separate from experimental evidence.** The Stage 1B v2 **primary modelling cohort** remains the frozen 2021–2025 selection (631,756 cleaned works), and its loader intentionally excludes 2026. This is a modelling-protocol choice, **not** a failure of the released 2026 Parquet's structural validation. An explicitly revised cohort can include 2026 Q1–Q3, but must document its partial-year handling and sensitivity to changing sources; existing results are not automatically updated or endorsed.

## What has and has not changed

This record clarifies the dataset-release validation status and scope. It does **not** modify, regenerate, or relabel the released raw/processed Parquets; their manifest hashes; the frozen Stage 1B v2 membership file; the model inputs; or the manuscript's experimental tables. The original `modelling_approved: false` field remains a separate, historical protocol gate and must not be mistaken for an assertion that the downloadable dataset files failed structural validation.
