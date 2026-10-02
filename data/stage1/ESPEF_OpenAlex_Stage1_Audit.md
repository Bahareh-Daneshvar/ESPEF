# ESPEF OpenAlex Stage 1 audit

**Decision: stop before full extraction.** The confirmed scope has 908,358 matching Works and 703,996 abstract-present candidates. This exceeds the agreed 250,000–300,000 practical threshold. Temporal metadata and coverage discontinuities also need a decision before modelling. No full corpus, embeddings, model training, GitHub changes, or scope changes were performed.

## Scope and audit method

Date of audit: 1 October 2026 (UTC retrieval timestamps are preserved per request). Only OpenAlex supplied corpus metadata. Scope: primary AI subfield 1702; dates 2021-01-01 through 2026-09-30 inclusive; English metadata; article, conference-paper, preprint; no citation threshold. Subfield ID resolved live through `/subfields?search=Artificial Intelligence`, and types checked through `/work-types`.

Base filter:
```
primary_topic.subfield.id:1702,from_publication_date:2021-01-01,to_publication_date:2026-09-30,language:en,type:article|conference-paper|preprint
```
Candidate query adds `has_abstract:true,display_name:!null`. `display_name` is the title alias; the API rejects `title:!null` and `has_title:true`. The date-range filter requires an indexed publication date. The API default curated core was used; the expansion corpus was not added. This is a corpus-selector disclosure, not a change from primary to secondary-topic membership.

Quarter/type/year/topic counts are API aggregates, not extrapolated samples. The quarterly totals sum exactly to both whole-corpus counts. Non-null titles were verified by a separate aggregate query; zero base-query records have null titles. Exact corpus-wide usable-title and reconstructable-abstract counts cannot be certified from aggregate metadata alone. Whitespace titles, placeholder text, invalid indices, incorrect language labels and non-research misclassifications need record-level validation. **703,996 is an upper-bound candidate count, not a certified usable corpus.**

A seeded audit sample of 20 abstract-present Works per quarter (23 quarters, 460 Works; seed 20261001) was downloaded. Sampling is only for Stage 1 diagnostics and size estimation; it is not the proposed modelling corpus. A second seeded sample of 100 Works with an arXiv location and a published primary location (seed 20261002) examines version dates. These aggregate requests and limited samples do not constitute full extraction.

## Overall quality and abstract coverage

- Matching before abstract/title QC: **908,358**.
- Abstract present and non-null title: **703,996 (77.50%)**.
- Missing abstract: **204,362 (22.50%)**.
- All 460 quarter-sample indices reconstructed with unique nonnegative positions contiguous from zero; dates parsed and titles were nonempty.
- These structural checks do not establish scientific usefulness: median abstract length 169 whitespace tokens; range 1–682; 12/460 have fewer than 20 tokens and 22/460 fewer than 50. A non-Latin abstract can have few whitespace tokens without being short; thresholds are diagnostic only and were not adopted as exclusions.
- Examples of clearly problematic abstract text: `International audience` and `35.240.67`. Some records labelled `en` have visibly non-English title/abstract text. Thus OpenAlex language/type flags are not sufficient final screening.
- No repeated OpenAlex IDs, non-null DOIs, or casefolded punctuation-normalised titles in the 460 quarter-sample Works. Corpus-wide duplicate rates and unmerged version rates remain unmeasured; no records were deleted.

## Quarterly counts

| Quarter | Matching | Abstract-present candidates | Missing abstract % |
| --- | --- | --- | --- |
| 2021 Q1 | 48,757 | 32,126 | 34.11% |
| 2021 Q2 | 29,114 | 24,672 | 15.26% |
| 2021 Q3 | 28,029 | 23,552 | 15.97% |
| 2021 Q4 | 30,546 | 26,979 | 11.68% |
| 2022 Q1 | 46,805 | 31,561 | 32.57% |
| 2022 Q2 | 28,800 | 25,642 | 10.97% |
| 2022 Q3 | 27,512 | 23,761 | 13.63% |
| 2022 Q4 | 33,374 | 29,826 | 10.63% |
| 2023 Q1 | 55,544 | 37,206 | 33.02% |
| 2023 Q2 | 34,606 | 31,297 | 9.56% |
| 2023 Q3 | 32,541 | 28,332 | 12.93% |
| 2023 Q4 | 40,275 | 35,545 | 11.74% |
| 2024 Q1 | 64,534 | 44,649 | 30.81% |
| 2024 Q2 | 38,907 | 34,790 | 10.58% |
| 2024 Q3 | 36,582 | 31,640 | 13.51% |
| 2024 Q4 | 46,616 | 39,354 | 15.58% |
| 2025 Q1 | 68,905 | 46,150 | 33.02% |
| 2025 Q2 | 44,195 | 39,091 | 11.55% |
| 2025 Q3 | 36,078 | 29,304 | 18.78% |
| 2025 Q4 | 25,981 | 18,679 | 28.11% |
| 2026 Q1 | 46,558 | 26,955 | 42.10% |
| 2026 Q2 | 31,597 | 21,937 | 30.57% |
| 2026 Q3 | 32,502 | 20,948 | 35.55% |

## Annual counts

| Year | Matching | Abstract-present candidates | Missing abstract % |
| --- | --- | --- | --- |
| 2021 | 136,446 | 107,329 | 21.34% |
| 2022 | 136,491 | 110,790 | 18.83% |
| 2023 | 162,966 | 132,380 | 18.77% |
| 2024 | 186,639 | 150,433 | 19.40% |
| 2025 | 175,159 | 133,224 | 23.94% |
| 2026 (Q1–Q3) | 110,657 | 69,840 | 36.89% |

2026 covers nine months only. A calendar-complete quarter does not imply indexing completeness one day after its end.

## Work types

| Type | Matching | Abstract-present candidates | Abstract present % |
| --- | --- | --- | --- |
| article | 439,192 | 328,630 | 74.83% |
| conference-paper | 271,742 | 199,893 | 73.56% |
| preprint | 197,424 | 175,473 | 88.88% |

Counts follow current OpenAlex labels. Some conference material may be catalogued as book chapters or other labels, which are excluded under the confirmed scope. The vocabulary is being revised/backfilled; current type composition cannot establish historical indexing completeness.

## Top primary topics (abstract-present candidates)

| ID | Name | Count |
| --- | --- | --- |
| https://openalex.org/T10028 | Topic Modeling | 56,611 |
| https://openalex.org/T10181 | Natural Language Processing Techniques | 36,101 |
| https://openalex.org/T10764 | Privacy-Preserving Technologies in Data | 28,960 |
| https://openalex.org/T10682 | Quantum Computing Algorithms and Architecture | 28,510 |
| https://openalex.org/T10320 | Neural Networks and Applications | 25,363 |
| https://openalex.org/T11512 | Anomaly Detection Techniques and Applications | 24,634 |
| https://openalex.org/T11689 | Adversarial Robustness in Machine Learning | 22,648 |
| https://openalex.org/T10020 | Quantum Information and Cryptography | 22,185 |
| https://openalex.org/T10862 | AI in cancer detection | 21,951 |
| https://openalex.org/T12128 | AI in Service Interactions | 17,816 |

The classifier-defined AI subfield includes quantum computing, cryptography, and interdisciplinary topics. These were retained exactly as instructed. Their inclusion means the operational study domain should be described as OpenAlex primary subfield 1702, rather than implying a manually curated pure-ML corpus.

## Top primary sources (abstract-present candidates)

| ID | Name | Count |
| --- | --- | --- |
| https://openalex.org/S4306400194 | arXiv (Cornell University) | 137,697 |
| https://openalex.org/S4306400562 | Zenodo (CERN European Organization for Nuclear Research) | 32,182 |
| https://openalex.org/S2485537415 | IEEE Access | 7,753 |
| https://openalex.org/S4210191458 | Proceedings of the AAAI Conference on Artificial Intelligence | 6,344 |
| https://openalex.org/S196734849 | Scientific Reports | 4,309 |
| https://openalex.org/S4210205812 | Applied Sciences | 3,942 |
| https://openalex.org/S164566984 | Physical Review A | 3,662 |
| https://openalex.org/S4306402512 | HAL (Le Centre pour la Communication Scientifique Directe) | 3,444 |
| https://openalex.org/S4306525896 | Research Square | 2,926 |
| https://openalex.org/S4210202905 | Electronics | 2,711 |

These are primary source locations, including repositories, not necessarily original peer-reviewed venues. **158,454 candidates (22.51%) have a null primary source ID.** Source group responses retain the top 200 reported groups; the remainder is not zero. No full source-group enumeration was needed for top-source reporting.

## Language diagnostic

The confirmed corpus is 100% `language:en` by API label. A separate diagnostic query removed only that restriction, without adding its results to the corpus: 1,270,991 Works match the other base criteria, of which 908,358 (71.47%) are labelled English. The language CSV preserves reported groups; unreported/null language values must not be treated as English. Metadata language is automatically inferred and may differ from full-text language.

## Temporal balance and potential artificial drift

Abstract-present quarterly counts range **18,679–46,150**, a **2.47-fold** ratio; CV **23.39%**. There are no tiny quarters in the candidate counts, but the windows are not balanced. Adequate total N does not guarantee enough documents for every emerging-topic cluster.

1. **January date concentration:** January 1 alone accounts for 16,026 candidates in 2021, 14,162 in 2022, 16,956 in 2023, 17,508 in 2024, 17,421 in 2025, and 8,880 in 2026. Overall 90,953/703,996 (12.92%) candidates lie on January 1. These represent about 33–50% of their year's Q1 candidates. This is consistent with coarse/year-only dates or defaults, but this audit cannot prove which individual dates were imputed. Do not assume precise dates merely because the field uses YYYY-MM-DD.
2. **Seasonal missingness:** Q1 abstract coverage is usually only 66–69% through 2025, whereas many other quarters are 84–90%; 2026 Q1 is 57.90%. This changes which publications reach the detector.
3. **Late-period source discontinuity:** primary-source arXiv counts are 34,657 in 2024, 25,794 in 2025, but only 1,096 across 2026 Q1–Q3. Quarterly arXiv falls from 6,712 in 2025 Q3 to 2,262 in Q4 and then 395, 387, 314 in 2026. In contrast, Zenodo rises from 174 in 2024 to 2,828 in 2025 and 24,142 in 2026 Q1–Q3 (34.57% of 2026 candidates). Independent source-filtered yearly aggregate queries reproduced these totals.
4. **Type discontinuity:** candidate conference papers fall from 11,048 in 2025 Q2 to 5,649 in Q3, 2,147 in Q4, then 3,473, 1,596, and 317 in 2026. In 2026 Q3 only 1.51% of candidates are conference papers, versus about 28–39% in many earlier quarters.
5. **Recent-quarter censoring:** 2025 Q4 and 2026 have lower counts and poorer abstract coverage. Backlogs, source harvest changes, revised classification, date defaults, and source substitution are plausible explanations; no cause was proven. Current created/updated timestamps cannot reconstruct historical availability, and updated_date also changes with citation updates.

These are substantial confounders. Drift in this corpus cannot automatically be attributed to scientific topic emergence. There is no historical snapshot comparison in this audit, so exact ingestion dates, missingness causes, and coverage completeness remain unresolved.

## Preprints, published versions, and early-detection validity

OpenAlex's documented data model groups matched publisher, preprint, and repository copies as locations of one Work. The primary location generally selects the version of record. Documentation states publication_date usually uses the earliest electronic-publication date **for the primary-location version**; other locations can be earlier. Therefore this field is not guaranteed to mean earliest scholarly appearance.

Live query: confirmed base scope plus `has_abstract:true,locations.source.id:S4306400194,primary_location.is_published:true` finds **37,545 Works** with both an arXiv location and a published primary location (24,126 article; 13,006 conference-paper; 413 preprint). The last category is a label/version inconsistency requiring later inspection. This proves that merged representations occur substantially; it does not measure the fraction of all real-world preprint–publication pairs that were successfully merged. Unmerged pairs are not captured by this denominator. We cannot defensibly claim a corpus-wide “usually merged” percentage from Stage 1.

In the selected 100-Work merged cohort, arXiv identifier YYMM was earlier than Work publication month in **74**, the same month in **5**, and later in **21**. This is a month-level diagnostic, not independently validated first-posting dates. Some later identifiers represent genuine post-publication deposits, others may expose coarse dates; we cannot distinguish them here. Submitted-version flags alone are insufficient evidence of a preprint, because institutional repository copies can carry them too; the explicit arXiv source filter is why this cohort was used.

| OpenAlex Work | Title | Work publication date | Earliest arXiv identifier month |
| --- | --- | --- | --- |
| https://openalex.org/W3205701968 | A scalable and fast artificial neural network syndrome decoder for surface codes | 2023-07-12 | 2021-10 |
| https://openalex.org/W4380136196 | Solving Novel Program Synthesis Problems with Genetic Programming using Parametric Polymorphism | 2023-07-12 | 2023-06 |
| https://openalex.org/W3094947935 | Semi-Supervised Speech Recognition Via Graph-Based Temporal Classification | 2021-05-13 | 2020-10 |
| https://openalex.org/W3196261868 | Graph Attention Multi-Layer Perceptron | 2022-08-12 | 2022-06 |
| https://openalex.org/W4416307670 | The Double-edged Sword of LLM-based Data Reconstruction: Understanding and Mitigating Contextual Vulnerability in Word-level Differential Privacy Text Sanitization | 2025-10-13 | 2025-08 |

Concrete quarter-sample evidence: “Proof Automation in the Theory of Finite Sets and Finite Set Relation Algebra”, W3122440787, has publisher DOI 10.1093/comjnl/bxab030, Work date 2021-03-17, and both arXiv 2101.07700 and its DOI location in the same Work. “Incremental and Modular Context-sensitive Analysis”, W3115796600, has Work date 2021-01-19 but an arXiv 1804.01839 location. The latter demonstrates that a publication dated inside the study window may have circulated before 2021.

Five attempts to resolve preprint DOI aliases as singleton Work URLs returned 404 despite those aliases appearing as locations. This does not establish separate Works or disprove merging; the Work location evidence is retained and alias resolution was not used for deduplication.

**Implication:** counting such a Work at its current publication date can delay a signal relative to its initial preprint appearance. Current metadata/abstracts can also reflect later versions, so backdating a final-version abstract without historical text would risk hindsight leakage. Do not substitute location `ingested_at` or Work `created_date` for scholarly appearance. No date definition was changed. Decide explicitly whether the study measures retrospective publication-date evolution or historical first-appearance detection before full extraction.

## Approximate full-data sizes

Sample-based extrapolation, decimal GB; not actual full files:

| Product | Central estimate | Planning range |
| --- | --- | --- |
| Modelling CSV with title, abstract and selected metadata | 1.04 GB | 0.8–1.5 GB |
| Modelling Parquet, Zstandard | 0.41 GB | 0.3–0.7 GB |
| Raw selected-metadata Parquet incl. inverted indices and locations | 0.82 GB | 0.6–1.3 GB |
| Selected raw metadata as uncompressed JSON equivalent | 3.78 GB | 3–5 GB |

CSV estimates weight the 20-Work quarterly samples by actual quarterly candidate counts. Parquet estimates extrapolate the two actual 460-row compressed files; small-sample dictionary/footer overhead and corpus redundancy make these estimates approximate. Raw Parquet sample serializes nested metadata to JSON strings; nested-struct storage could differ. No full CSV or Parquet was produced.

## Computational assessment and recommendation

- One 768-dimensional float32 embedding matrix for 703,996 candidates: **2.16 GB (2.01 GiB)**. SciBERT plus SPECTER2 matrices: **4.33 GB**, before IDs, batches and model memory.
- Embedding is technically feasible with batched GPU inference and disk-backed storage. Illustrative 5–100 documents/s means about 39.1–2.0 hours per model; this is arithmetic, not a hardware benchmark. Token truncation/chunking and SPECTER2 adapter choice remain later decisions.
- Largest quarter has 46,150 candidates. A 46,150 × 46,150 float32 dense transport-cost matrix alone is **8.52 GB (7.93 GiB)**, before solver/gradient/buffering overhead. SciBERT/SPECTER2 embedding feasibility does not make repeated exact high-dimensional OT automatically practical. A full-corpus square matrix would be about 1.98 TB.
- Full-data clustering and topic tracking require benchmarks and scalable algorithms. Sliced/regularized/approximate transport options would be methodological choices needing documented validation, not silent substitutes.
- Therefore the full corpus is **not manageable under the agreed initial rule**, even though storage and GPU embedding are technically possible. Full extraction must remain stopped.

No narrowing is adopted in this audit. First resolve date semantics, coarse dates and late-period coverage; source/type anomalies should be diagnosed before considering a date reduction. If all-source primary-subfield AI must remain fixed, computational resources or the initial size limit would need an explicit revised decision. A date-only sensitivity option illustrates the tradeoff: 2023–2024 has 282,813 candidates, whereas 2021–2024 has 500,932. The shorter interval loses recent emergence evidence and is not a recommendation to silently change the approved range. No citation filtering, random corpus reduction, or famous-paper selection was applied.

## Reproducibility and limitations

The accompanying ZIP contains the live aggregate JSON responses with exact request URLs/timestamps, CSV audits, two small diagnostic sample Parquets, a reconstructed sample CSV, version-date sample, scripts, query text, summary and checksums. These are Stage 1 materials only. Seeds make sample requests reproducible against a database state; a changing live index can change results later, so preserved responses are the audit evidence. No credentials are embedded.

Exact final usable count, corpus-wide duplicates, verified earliest appearance dates, historical abstracts, coverage completeness and actual GPU throughput remain unmeasured. These limits do not affect the decision to stop: the candidate volume exceeds the threshold by a large margin and multiple serious temporal confounders are directly observed.

## Current official references

- https://help.openalex.org/data/subfields/
- https://help.openalex.org/data/work-types/
- https://help.openalex.org/data/works/attributes/
- https://help.openalex.org/data/works/
- https://help.openalex.org/data/locations/
- https://help.openalex.org/api/filtering/
- https://help.openalex.org/api/grouping/
- https://help.openalex.org/api/llm-quick-reference/

Counts and sample observations are from the attached live OpenAlex API responses, not from these documentation pages.
