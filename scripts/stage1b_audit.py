"""Run the Stage 1B cohort and temporal-confound audit without changing sources."""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import json
import os
import pathlib
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = pathlib.Path(__file__).resolve().parents[1]
YEARS = tuple(range(2021, 2027))
PRIMARY_YEARS = tuple(range(2021, 2026))
REPORT_QUARTERS = tuple(
    f"{year}Q{quarter}"
    for year in YEARS
    for quarter in range(1, 4 if year == 2026 else 5)
)
FLAG_JAN1 = "january_1_date_precision_unverified"
FLAG_SHORT = "short_abstract_review"
FLAG_LANGUAGE = "suspected_text_language_mismatch_review"
FLAG_VERSION = "preprint_published_date_review"
FLAG_2026 = "coverage_pending_stage_1B"
MODEL_COLUMNS = ["openalex_id", "title", "abstract", "publication_date"]
AUDIT_COLUMNS = [
    "openalex_id",
    "title",
    "abstract",
    "publication_date",
    "type",
    "primary_source_id",
    "primary_source_name",
    "quality_flags",
]


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quarter_for_date(value: str, year: int) -> str:
    try:
        parsed = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"invalid publication_date for {year}: {value!r}") from error
    if parsed.isoformat() != value or parsed.year != year:
        raise RuntimeError(f"publication_date outside yearly partition {year}: {value!r}")
    if year == 2026 and parsed > dt.date(2026, 9, 30):
        raise RuntimeError(f"2026 date outside the available Q1-Q3 window: {value!r}")
    return f"{year}Q{(parsed.month - 1) // 3 + 1}"


def suspected_text_language(title: str | None, abstract: str | None) -> bool:
    letters = [character for character in (title or "") + " " + (abstract or "") if character.isalpha()]
    return len(letters) >= 20 and sum(character.isascii() for character in letters) / len(letters) < 0.5


def read_json_list(value: str | None, work_id: str, field: str) -> set[str]:
    try:
        flags = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid {field} for {work_id}") from error
    if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
        raise RuntimeError(f"invalid {field} for {work_id}")
    return set(flags)


def source_integrity(manifest: dict) -> dict[str, dict]:
    result = {}
    for year in YEARS:
        year_info = manifest["years"][str(year)]
        for kind in ("raw", "processed"):
            expected = year_info["files"][kind]
            path = ROOT / expected["path"]
            if not path.is_file():
                raise RuntimeError(f"required source is missing: {path}")
            actual_size = path.stat().st_size
            actual_hash = sha256_file(path)
            parquet_rows = pq.ParquetFile(path).metadata.num_rows
            if actual_size != expected["size_bytes"] or actual_hash != expected["sha256"]:
                raise RuntimeError(f"source integrity mismatch: {path}")
            if parquet_rows != expected["rows"]:
                raise RuntimeError(f"source row-count mismatch: {path}")
            result[expected["path"]] = {
                "size_bytes": actual_size,
                "rows": parquet_rows,
                "sha256": actual_hash,
            }
    return result


def counter_from_audit(path: pathlib.Path, field: str) -> dict[str, int]:
    audit = json.loads(path.read_text())
    return {quarter: int(count) for quarter, count in audit[field].items()}


def check_quarter_crosschecks(year: int, raw_counts: collections.Counter, usable_counts: collections.Counter) -> None:
    audit_path = ROOT / "data" / "audits" / f"espef_audit_{year}.json"
    raw_audit = counter_from_audit(audit_path, "quarterly_raw")
    usable_audit = counter_from_audit(audit_path, "quarterly_processed")
    actual_raw = {key: value for key, value in raw_counts.items() if key.startswith(str(year))}
    actual_usable = {key: value for key, value in usable_counts.items() if key.startswith(str(year))}
    if actual_raw != raw_audit:
        raise RuntimeError(f"raw quarterly counts disagree with validated audit for {year}")
    if actual_usable != usable_audit:
        raise RuntimeError(f"usable quarterly counts disagree with validated audit for {year}")

    csv_path = ROOT / "data" / "audits" / f"espef_quarterly_{year}.csv"
    if csv_path.exists():
        with csv_path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                quarter = row["quarter"]
                if int(row["total_retrieved"]) != actual_raw.get(quarter, 0):
                    raise RuntimeError(f"raw quarterly CSV disagrees for {quarter}")
                if int(row["usable_works"]) != actual_usable.get(quarter, 0):
                    raise RuntimeError(f"usable quarterly CSV disagrees for {quarter}")


def raw_quarter_counts(year: int) -> collections.Counter:
    path = ROOT / "data" / "raw" / f"openalex_espef_{year}.parquet"
    counts: collections.Counter = collections.Counter()
    rows = 0
    for batch in pq.ParquetFile(path).iter_batches(columns=["publication_date"], batch_size=8192):
        for value in batch.column(0).to_pylist():
            quarter = quarter_for_date(value, year)
            counts[quarter] += 1
            rows += 1
    expected_quarters = 3 if year == 2026 else 4
    if len(counts) != expected_quarters or rows != pq.ParquetFile(path).metadata.num_rows:
        raise RuntimeError(f"raw rows do not map to all available quarters for {year}")
    return counts


def positive_version_ids(year: int) -> set[str]:
    """Reapply the extraction code's stored-location evidence rule exactly."""
    path = ROOT / "data" / "raw" / f"openalex_espef_{year}.parquet"
    positive = set()
    columns = ["id", "locations", "primary_location"]
    for batch in pq.ParquetFile(path).iter_batches(columns=columns, batch_size=4096):
        for work_id, locations_json, primary_json in zip(*(column.to_pylist() for column in batch.columns)):
            locations = json.loads(locations_json or "[]")
            primary = json.loads(primary_json or "{}")
            if (
                isinstance(locations, list)
                and any("arxiv" in json.dumps(location, ensure_ascii=False).casefold() for location in locations)
                and isinstance(primary, dict)
                and primary.get("is_published")
            ):
                positive.add(work_id)
    return positive


COHORT_SCHEMA = pa.schema(
    [
        ("openalex_id", pa.string()),
        ("publication_date", pa.string()),
        ("year", pa.int16()),
        ("quarter", pa.string()),
        ("period_role", pa.string()),
        ("cohort_p0", pa.bool_()),
        ("cohort_s1", pa.bool_()),
        ("cohort_s2", pa.bool_()),
        ("cohort_s3_known", pa.bool_()),
        ("january_1_date_precision_review", pa.bool_()),
        ("short_abstract_review", pa.bool_()),
        ("suspected_text_language_mismatch_review", pa.bool_()),
        ("preprint_published_version_review", pa.bool_()),
        ("version_history_state", pa.string()),
        ("stage1b_status", pa.string()),
    ]
)


def empty_quarter_stats() -> dict:
    return {
        "n_usable": 0,
        "january_1": 0,
        "short_abstract": 0,
        "language_mismatch": 0,
        "known_version": 0,
        "types": collections.Counter(),
        "missing_source": 0,
        "sources": collections.Counter(),
        "source_names": collections.defaultdict(collections.Counter),
    }


def scan_processed_year(year: int, version_ids: set[str], writer: pq.ParquetWriter):
    path = ROOT / "data" / "processed" / f"espef_corpus_{year}.parquet"
    counts: collections.Counter = collections.Counter()
    stats = {quarter: empty_quarter_stats() for quarter in REPORT_QUARTERS if quarter.startswith(str(year))}
    for batch in pq.ParquetFile(path).iter_batches(columns=AUDIT_COLUMNS, batch_size=4096):
        cohort_rows = []
        for row in batch.to_pylist():
            work_id = row["openalex_id"]
            if not work_id:
                raise RuntimeError(f"missing openalex_id in usable source: {year}")
            date = row["publication_date"]
            quarter = quarter_for_date(date, year)
            if quarter not in stats:
                raise RuntimeError(f"date outside audit quarters: {date}")
            counts[quarter] += 1
            flags = read_json_list(row["quality_flags"], work_id, "quality_flags")
            january = date.endswith("-01-01")
            short = len((row["abstract"] or "").split()) < 20
            language = suspected_text_language(row["title"], row["abstract"])
            version = work_id in version_ids
            if (FLAG_JAN1 in flags) != january:
                raise RuntimeError(f"January-1 flag disagrees with unchanged date for {work_id}")
            if (FLAG_SHORT in flags) != short:
                raise RuntimeError(f"short-abstract flag differs from fewer-than-20 tokens for {work_id}")
            if (FLAG_LANGUAGE in flags) != language:
                raise RuntimeError(f"stored language heuristic flag disagrees for {work_id}")
            if (FLAG_VERSION in flags) != version:
                raise RuntimeError(f"stored version flag disagrees with raw location evidence for {work_id}")
            if (year == 2026) != (FLAG_2026 in flags):
                raise RuntimeError(f"2026 pending-stage flag disagrees for {work_id}")

            current = stats[quarter]
            current["n_usable"] += 1
            current["january_1"] += january
            current["short_abstract"] += short
            current["language_mismatch"] += language
            current["known_version"] += version
            current["types"][row["type"]] += 1
            source_id = row["primary_source_id"]
            source_name = row["primary_source_name"]
            if not source_id:
                current["missing_source"] += 1
            else:
                current["sources"][source_id] += 1
                current["source_names"][source_id][source_name or "UNKNOWN"] += 1

            primary = year in PRIMARY_YEARS
            cohort_rows.append(
                {
                    "openalex_id": work_id,
                    "publication_date": date,
                    "year": year,
                    "quarter": quarter,
                    "period_role": "primary_candidate_2021_2025" if primary else "recent_censored_2026_q1_q3",
                    "cohort_p0": primary,
                    "cohort_s1": primary and not january,
                    "cohort_s2": primary and not language,
                    "cohort_s3_known": primary and version,
                    "january_1_date_precision_review": january,
                    "short_abstract_review": short,
                    "suspected_text_language_mismatch_review": language,
                    "preprint_published_version_review": version,
                    "version_history_state": "positively_identified_preprint_published_version" if version else "unresolved_unknown",
                    "stage1b_status": "pending_stage_1B" if year == 2026 else "validated_year_pending_cohort_review",
                }
            )
        if cohort_rows:
            writer.write_table(pa.Table.from_pylist(cohort_rows, schema=COHORT_SCHEMA))
    return counts, stats


def rate(count: int, denominator: int) -> float | None:
    return round(count / denominator, 8) if denominator else None


def make_qc_rows(raw_counts: collections.Counter, usable_counts: collections.Counter, stats_by_quarter: dict) -> list[dict]:
    rows = []
    for quarter in REPORT_QUARTERS:
        year = int(quarter[:4])
        current = stats_by_quarter[quarter]
        n_raw = raw_counts[quarter]
        n_usable = current["n_usable"]
        known_denominator = sum(current["sources"].values())
        role = "primary_candidate_2021_2025" if year in PRIMARY_YEARS else "pending_stage_1B_recent_censored_excluded"
        row = {
            "year": year,
            "quarter": quarter[-2:],
            "period_role": role,
            "n_raw": n_raw,
            "n_usable": n_usable,
            "usable_rate": rate(n_usable, n_raw),
            "january_1_flag_count": current["january_1"],
            "january_1_flag_rate_usable_denominator": rate(current["january_1"], n_usable),
            "short_abstract_review_count": current["short_abstract"],
            "short_abstract_review_rate_usable_denominator": rate(current["short_abstract"], n_usable),
            "suspected_text_language_mismatch_review_count": current["language_mismatch"],
            "suspected_text_language_mismatch_review_rate_usable_denominator": rate(current["language_mismatch"], n_usable),
            "preprint_published_version_review_count": current["known_version"],
            "preprint_published_version_review_rate_usable_denominator": rate(current["known_version"], n_usable),
            "version_history_unresolved_unknown_count": n_usable - current["known_version"],
            "version_history_unresolved_unknown_rate_usable_denominator": rate(n_usable - current["known_version"], n_usable),
            "article_count": current["types"]["article"],
            "article_proportion_usable_denominator": rate(current["types"]["article"], n_usable),
            "conference_paper_count": current["types"]["conference-paper"],
            "conference_paper_proportion_usable_denominator": rate(current["types"]["conference-paper"], n_usable),
            "preprint_count": current["types"]["preprint"],
            "preprint_proportion_usable_denominator": rate(current["types"]["preprint"], n_usable),
            "missing_primary_source_count": current["missing_source"],
            "missing_primary_source_rate_usable_denominator": rate(current["missing_source"], n_usable),
            "known_primary_source_denominator": known_denominator,
            "source_hhi_known_primary_source_denominator": round(
                sum((count / known_denominator) ** 2 for count in current["sources"].values()), 8
            ) if known_denominator else None,
        }
        ordered_sources = sorted(current["sources"].items(), key=lambda item: (-item[1], item[0]))[:5]
        for index in range(5):
            suffix = index + 1
            if index < len(ordered_sources):
                source_id, count = ordered_sources[index]
                names = current["source_names"][source_id]
                source_name = sorted(names.items(), key=lambda item: (-item[1], item[0]))[0][0]
                row[f"leading_source_{suffix}_id"] = source_id
                row[f"leading_source_{suffix}_name"] = source_name
                row[f"leading_source_{suffix}_count"] = count
                row[f"leading_source_{suffix}_share_known_source_denominator"] = rate(count, known_denominator)
            else:
                row[f"leading_source_{suffix}_id"] = ""
                row[f"leading_source_{suffix}_name"] = ""
                row[f"leading_source_{suffix}_count"] = 0
                row[f"leading_source_{suffix}_share_known_source_denominator"] = None
        if n_usable != usable_counts[quarter]:
            raise RuntimeError(f"usable count accounting mismatch in {quarter}")
        rows.append(row)
    return rows


def write_qc(path: pathlib.Path, rows: list[dict]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_report(qc_rows: list[dict], cohort_counts: dict) -> str:
    sums = collections.Counter()
    for row in qc_rows:
        if row["year"] in PRIMARY_YEARS:
            sums["p0"] += row["n_usable"]
            sums["s1"] += row["n_usable"] - row["january_1_flag_count"]
            sums["s2"] += row["n_usable"] - row["suspected_text_language_mismatch_review_count"]
            sums["s3_known"] += row["preprint_published_version_review_count"]
        else:
            sums["recent_2026"] += row["n_usable"]
    lines = [
        "# ESPEF Stage 1B Modelling-Cohort and Temporal-Confound Audit",
        "",
        "## Decision and scope",
        "",
        "2021–2025 are the proposed primary modelling period. P0 is the usable cleaned cohort; S1 and S2 are sensitivity cohorts, and S3-known is a positive-evidence diagnostic subset, not a preprint-free cohort. 2026 Q1–Q3 is reported separately as recent/censored, remains pending_stage_1B, and is excluded from all primary cohorts.",
        "",
        "No frozen corpus, source Parquet, query, or scientific inclusion rule was changed. This audit does not run embeddings, clustering, topic modelling, drift detection, or emergence scoring.",
        "",
        "## Existing diagnostic definitions",
        "",
        f"- January 1: `{FLAG_JAN1}` is set when the unchanged publication_date ends in `-01-01`; this is a potential date-precision review flag, not evidence of an erroneous or imputed date.",
        f"- Short abstract: `{FLAG_SHORT}` means fewer than 20 whitespace-separated tokens (`len(abstract.split()) < 20`). Short abstracts remain in P0.",
        f"- Text-language diagnostic: `{FLAG_LANGUAGE}` uses the existing heuristic: collect alphabetic characters from title plus abstract; flag only when there are at least 20 and fewer than half are ASCII. This is a diagnostic heuristic, not a validated language classifier.",
        f"- Positive version evidence: `{FLAG_VERSION}` is set only when a stored location contains the substring `arxiv` (case-insensitive) and the stored primary location has `is_published` true. An unflagged history is `unresolved/unknown`, never “no preprint.”",
        "- 2026 records retain the extraction flag `coverage_pending_stage_1B` and are not eligible for P0/S1/S2/S3-known.",
        "",
        "The runner checked each persisted quality flag against the existing implementation and raw location evidence; disagreements would stop output publication.",
        "",
        "## Denominators and calculations",
        "",
        "- `n_raw` comes from the raw yearly Parquet by unchanged publication_date. The counts were cross-checked against each validated yearly audit’s `quarterly_raw`; where available, quarterly CSVs were also checked. Any disagreement is fatal.",
        "- `n_usable` is the processed cleaned-record count by publication_date quarter and is cross-checked against `quarterly_processed` in the validated audit.",
        "- Usable rate is n_usable / n_raw. All flag rates, unresolved-version rates, work-type proportions, and missing-source rates use n_usable as denominator.",
        "- Known-source shares and HHI use records with nonempty primary_source_id as denominator; missing source IDs are separately counted/rated among usable records. HHI is the sum of squared shares over all known source IDs, not only the leading five. Source IDs are grouping keys and display names are labels.",
        "- Counts and rates in `stage1b_quarterly_qc.csv` cover all quarters 2021Q1–2025Q4 and 2026Q1–Q3. Rates are proportions from 0 to 1.",
        "",
        "## Cohort membership",
        "",
        f"- P0: {sums['p0']:,} usable records from 2021–2025.",
        f"- S1: {sums['s1']:,} P0 records excluding January-1 potential-precision flags only.",
        f"- S2: {sums['s2']:,} P0 records excluding the existing suspected-text-language heuristic only.",
        f"- S3-known: {sums['s3_known']:,} P0 records positively flagged by stored preprint/published-version location evidence. This is not a “preprint-free” comparison group.",
        f"- 2026 recent/censored: {sums['recent_2026']:,} usable Q1–Q3 records, all held outside the primary cohorts and labelled `pending_stage_1B`.",
        "- No cohort excludes short abstracts or infers unobserved version history.",
        "",
        "The compact cohort Parquet contains IDs, unchanged dates, quarter/period role, cohort membership, diagnostic flags, and explicit unresolved version-history states. It contains no titles or abstracts.",
        "",
        "## Minimal modelling view",
        "",
        "`scripts/load_stage1b_modelling.py` exposes a lazy, batch-based view of the processed yearly Parquets. Its returned batches contain only `openalex_id`, `title`, `abstract`, and `publication_date`; the ID is traceability-only, title/abstract are semantic inputs, and publication_date is for temporal organization. The loader permits only 2021–2025 primary cohorts. Do not pass other metadata to semantic encoders or future modelling components.",
        "",
        "## Source integrity",
        "",
        "All 12 local yearly raw/processed Parquets matched their frozen-manifest SHA-256, byte-size, and row-count values before and after this audit. Before/after hashes are recorded in `stage1b_modelling_manifest.json`.",
        "",
        "## Output files",
        "",
        "- `data/stage1b/stage1b_quarterly_qc.csv`",
        "- `data/stage1b/stage1b_modelling_cohorts.parquet`",
        "- `data/stage1b/stage1b_modelling_manifest.json`",
        "- `data/stage1b/ESPEF_Stage1B_Audit.md`",
        "",
    ]
    return "\n".join(lines)


def run() -> None:
    output_dir = ROOT / "data" / "stage1b"
    output_dir.mkdir(parents=True, exist_ok=True)
    names = [
        "stage1b_quarterly_qc.csv",
        "stage1b_modelling_cohorts.parquet",
        "stage1b_modelling_manifest.json",
        "ESPEF_Stage1B_Audit.md",
    ]
    existing = [name for name in names if (output_dir / name).exists()]
    if existing:
        raise RuntimeError(f"refusing to overwrite Stage 1B output(s): {', '.join(existing)}")

    frozen = json.loads((ROOT / "data" / "espef_dataset_manifest.json").read_text())
    before = source_integrity(frozen)
    raw_counts: collections.Counter = collections.Counter()
    usable_counts: collections.Counter = collections.Counter()
    stats_by_quarter = {quarter: empty_quarter_stats() for quarter in REPORT_QUARTERS}
    with tempfile.TemporaryDirectory(prefix=".stage1b-", dir=output_dir) as temporary:
        temporary_dir = pathlib.Path(temporary)
        cohort_temp = temporary_dir / names[1]
        cohort_writer = pq.ParquetWriter(cohort_temp, COHORT_SCHEMA, compression="zstd")
        try:
            for year in YEARS:
                print(f"Auditing {year}", flush=True)
                year_raw = raw_quarter_counts(year)
                version_ids = positive_version_ids(year)
                year_usable, year_stats = scan_processed_year(year, version_ids, cohort_writer)
                for quarter, count in year_raw.items():
                    raw_counts[quarter] = count
                for quarter, count in year_usable.items():
                    usable_counts[quarter] = count
                stats_by_quarter.update(year_stats)
                check_quarter_crosschecks(year, raw_counts, usable_counts)
        finally:
            cohort_writer.close()

        if set(raw_counts) != set(REPORT_QUARTERS) or set(usable_counts) != set(REPORT_QUARTERS):
            raise RuntimeError("quarter coverage is incomplete for the requested audit periods")
        qc_rows = make_qc_rows(raw_counts, usable_counts, stats_by_quarter)
        qc_temp = temporary_dir / names[0]
        write_qc(qc_temp, qc_rows)

        after = source_integrity(frozen)
        if before != after:
            raise RuntimeError("one or more source Parquets changed during the audit")

        cohort_totals = {
            "P0": sum(row["n_usable"] for row in qc_rows if row["year"] in PRIMARY_YEARS),
            "S1": sum(row["n_usable"] - row["january_1_flag_count"] for row in qc_rows if row["year"] in PRIMARY_YEARS),
            "S2": sum(row["n_usable"] - row["suspected_text_language_mismatch_review_count"] for row in qc_rows if row["year"] in PRIMARY_YEARS),
            "S3-known": sum(row["preprint_published_version_review_count"] for row in qc_rows if row["year"] in PRIMARY_YEARS),
            "recent_censored_2026_q1_q3": sum(row["n_usable"] for row in qc_rows if row["year"] == 2026),
        }
        report_temp = temporary_dir / names[3]
        report_temp.write_text(build_report(qc_rows, cohort_totals), encoding="utf-8")
        outputs = {
            "quarterly_qc": {"path": "data/stage1b/stage1b_quarterly_qc.csv", "sha256": sha256_file(qc_temp)},
            "cohort_membership": {"path": "data/stage1b/stage1b_modelling_cohorts.parquet", "sha256": sha256_file(cohort_temp)},
            "audit_report": {"path": "data/stage1b/ESPEF_Stage1B_Audit.md", "sha256": sha256_file(report_temp)},
        }
        output_manifest = {
            "project": "ESPEF",
            "audit": "Stage 1B Modelling-Cohort and Temporal-Confound Audit",
            "release_tag": "espef-yearly-2026-10-02",
            "release_metadata_hash_check": "passed for frozen manifest, SHA256SUMS, and all 12 dataset assets before download",
            "source_hashes_before_audit": before,
            "source_hashes_after_audit": after,
            "source_files_unchanged": before == after,
            "periods": {
                "primary_candidate": "2021-01-01 through 2025-12-31",
                "recent_censored": "2026-01-01 through 2026-09-30; pending_stage_1B; excluded from primary cohorts",
            },
            "cohorts": cohort_totals,
            "flags": {
                FLAG_JAN1: "publication_date ends in -01-01; potential precision flag, not proof of erroneous or imputed date",
                FLAG_SHORT: "fewer than 20 whitespace-separated abstract tokens; review only; no exclusion",
                FLAG_LANGUAGE: "at least 20 alphabetic title+abstract characters and ASCII-letter proportion below 0.5; heuristic, not validated language classifier",
                FLAG_VERSION: "at least one raw stored location contains arxiv case-insensitively and raw primary_location.is_published is true",
                "unflagged_version_history": "unresolved/unknown; never interpreted as no preprint",
            },
            "denominators": {
                "n_raw": "raw Parquet records grouped by unchanged publication_date; cross-checked with validated yearly audit and available quarterly CSV",
                "n_usable": "processed Parquet records; diagnostic rates and work-type proportions use this denominator",
                "known_source_shares_and_hhi": "records with nonempty primary_source_id; missing source count/rate separately uses n_usable",
            },
            "modelling_view": {
                "loader": "scripts/load_stage1b_modelling.py",
                "columns": MODEL_COLUMNS,
                "traceability_only": ["openalex_id"],
                "semantic_inputs": ["title", "abstract"],
                "temporal_organization": ["publication_date"],
                "metadata_prohibited_as_semantic_input": True,
            },
            "outputs": outputs,
            "modelling_approved": False,
            "embeddings_or_clustering_run": False,
        }
        manifest_temp = temporary_dir / names[2]
        manifest_temp.write_text(json.dumps(output_manifest, indent=2) + "\n", encoding="utf-8")
        for name in names:
            os.replace(temporary_dir / name, output_dir / name)
    print(json.dumps({"cohorts": cohort_totals, "quarters": len(qc_rows), "source_files_unchanged": True}, indent=2))


if __name__ == "__main__":
    run()