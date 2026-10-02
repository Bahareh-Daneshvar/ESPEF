# ESPEF Stage 1B Modelling-Cohort and Temporal-Confound Audit

## Decision and scope

2021–2025 are the proposed primary modelling period. P0 is the usable cleaned cohort; S1 and S2 are sensitivity cohorts, and S3-known is a positive-evidence diagnostic subset, not a preprint-free cohort. 2026 Q1–Q3 is reported separately as recent/censored, remains pending_stage_1B, and is excluded from all primary cohorts.

This is a retrospective frozen OpenAlex snapshot ordered by stored publication_date, not a guaranteed reconstruction of first scholarly appearance.

No frozen corpus, source Parquet, query, or scientific inclusion rule was changed. This audit does not run embeddings, clustering, topic modelling, drift detection, or emergence scoring.

## Existing diagnostic definitions

- January 1: `january_1_date_precision_unverified` is set when the unchanged publication_date ends in `-01-01`; this is a potential date-precision review flag, not evidence of an erroneous or imputed date.
- Short abstract: `short_abstract_review` means fewer than 20 whitespace-separated tokens (`len(abstract.split()) < 20`). Short abstracts remain in P0.
- Text-language diagnostic: `suspected_text_language_mismatch_review` uses the existing heuristic: collect alphabetic characters from title plus abstract; flag only when there are at least 20 and fewer than half are ASCII. This is a diagnostic heuristic, not a validated language classifier.
- Positive version evidence: `preprint_published_date_review` is set only when a stored location contains the substring `arxiv` (case-insensitive) and the stored primary location has `is_published` true. An unflagged history is `unresolved/unknown`, never “no preprint.”
- 2026 records retain the extraction flag `coverage_pending_stage_1B` and are not eligible for P0/S1/S2/S3-known.

The runner checked each persisted quality flag against the existing implementation and raw location evidence; disagreements would stop output publication.

## Denominators and calculations

- `n_raw` comes from the raw yearly Parquet by unchanged publication_date. The counts were cross-checked against each validated yearly audit’s `quarterly_raw`; where available, quarterly CSVs were also checked. Any disagreement is fatal.
- `n_usable` is the processed cleaned-record count by publication_date quarter and is cross-checked against `quarterly_processed` in the validated audit.
- Usable rate is n_usable / n_raw. All flag rates, unresolved-version rates, work-type proportions, and missing-source rates use n_usable as denominator.
- Known-source shares and HHI use records with nonempty primary_source_id as denominator; missing source IDs are separately counted/rated among usable records. HHI is the sum of squared shares over all known source IDs, not only the leading five. Source IDs are grouping keys and display names are labels.
- Counts and rates in `stage1b_quarterly_qc.csv` cover all quarters 2021Q1–2025Q4 and 2026Q1–Q3. Rates are proportions from 0 to 1.

## Quantitative assessment

### Observations

- Primary-period raw quarterly counts range from 26,131 (2025Q4) to 68,976 (2025Q1), a 2.64× max/min ratio. Usable counts range from 18,703 (2025Q4) to 46,076 (2025Q1), a 2.46× ratio.
- From 2021 to 2025, article share changes from 42.17% to 52.39% (+10.22 percentage points); conference-paper share changes -10.79 points; preprint share changes +0.57 points.
- The 2021-to-2025 known-primary-source distributions have total-variation distance 0.4121; annual known-source HHI changes from 0.0781 to 0.0632. The leading source is arXiv (Cornell University) in 2021 (27.65% of known-source records) and arXiv (Cornell University) in 2025 (24.76%).
- January-1 flags total 81,491 of 631,756 P0 records (12.90%); 81,491 occur in Q1. Annual flag rates range from 11.60% to 14.89%.
- Primary-period missing-primary-source counts total 155,441 (24.60% of P0). Annual rates range from 15.78% to 30.39% of usable records.
- 2026 has 111,148 raw and 70,057 usable records in Q1–Q3 only; no Q4 is included. The frozen window ends 2026-09-30. Q1/Q2/Q3 usable counts are Q1 26,966, Q2 21,945, Q3 21,146.

### Flags, unknowns, and sensitivity assumptions

These are observed count and metadata-composition differences only. They do not demonstrate semantic drift, identify a causal mechanism, or establish ingestion incompleteness. The 2026 recent/censored window is not treated as a complete annual cohort, and no annual 2026 extrapolation is made.
January-1 dates are potential date-precision flags, not evidence of bad or imputed dates. A missing primary_source_id means source attribution is unavailable in the stored record; it does not establish that a work has no venue. Unflagged version histories remain unresolved/unknown.
S1 and S2 are sensitivity assumptions that remove only their named diagnostic flags. Their differences from P0 quantify sensitivity to those assumptions, not a corrected or preferred corpus. Short abstracts remain included.

## Cohort membership

- P0: 631,756 usable records from 2021–2025.
- S1: 550,265 P0 records excluding January-1 potential-precision flags only.
- S2: 628,228 P0 records excluding the existing suspected-text-language heuristic only.
- S3-known: 32,740 P0 records positively flagged by stored preprint/published-version location evidence. This is not a “preprint-free” comparison group.
- 2026 recent/censored: 70,057 usable Q1–Q3 records, all held outside the primary cohorts and labelled `pending_stage_1B`.
- No cohort excludes short abstracts or infers unobserved version history.

The compact cohort Parquet contains IDs, unchanged dates, quarter/period role, cohort membership, diagnostic flags, and explicit unresolved version-history states. It contains no titles or abstracts.

## Minimal modelling view

`scripts/load_stage1b_modelling.py` exposes a lazy, batch-based view of the processed yearly Parquets and is pinned to the `v2` cohort manifest. Its returned batches contain only `openalex_id`, `title`, `abstract`, and `publication_date`; the ID is traceability-only, title/abstract are semantic inputs, and publication_date is for temporal organization. The loader permits only 2021–2025 primary cohorts. Do not pass other metadata to semantic encoders or future modelling components.

## Source integrity

All 12 local yearly raw/processed Parquets matched their frozen-manifest SHA-256, byte-size, and row-count values before and after this audit. Before/after hashes are recorded in `stage1b_modelling_manifest.json`.

## Output files

- `data/stage1b/v2/stage1b_quarterly_qc.csv`
- `data/stage1b/v2/stage1b_modelling_cohorts.parquet`
- `data/stage1b/v2/stage1b_modelling_manifest.json`
- `data/stage1b/v2/ESPEF_Stage1B_Audit.md`
