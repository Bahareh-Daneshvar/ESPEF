"""Lazy, metadata-free projection for approved Stage 1B primary cohorts."""
from __future__ import annotations

import pathlib
from collections.abc import Iterator

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = pathlib.Path(__file__).resolve().parents[1]
COHORT_PATH = ROOT / "data" / "stage1b" / "stage1b_modelling_cohorts.parquet"
MODEL_COLUMNS = ["openalex_id", "title", "abstract", "publication_date"]
COHORT_COLUMN = {
    "P0": "cohort_p0",
    "S1": "cohort_s1",
    "S2": "cohort_s2",
    "S3-known": "cohort_s3_known",
}


def iter_modelling_batches(
    year: int,
    cohort: str = "P0",
    batch_size: int = 1024,
) -> Iterator[pa.RecordBatch]:
    """Yield only ID, title, abstract, and date for one primary-cohort year.

    The ID is retained only for traceability. This function deliberately rejects
    2026 and never reads source, work type, citation, topic, or quality metadata
    from the processed Parquet.
    """
    if year not in range(2021, 2026):
        raise ValueError("Stage 1B modelling cohorts are limited to 2021-2025")
    if cohort not in COHORT_COLUMN:
        raise ValueError(f"unknown primary cohort: {cohort}")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if not COHORT_PATH.is_file():
        raise FileNotFoundError(f"cohort membership manifest is missing: {COHORT_PATH}")

    selected_ids = set()
    cohort_column = COHORT_COLUMN[cohort]
    for batch in pq.ParquetFile(COHORT_PATH).iter_batches(
        columns=["openalex_id", "year", cohort_column], batch_size=16384
    ):
        ids = batch.column(0).to_pylist()
        years = batch.column(1).to_pylist()
        included = batch.column(2).to_pylist()
        selected_ids.update(
            work_id
            for work_id, record_year, is_included in zip(ids, years, included)
            if record_year == year and is_included
        )

    source = ROOT / "data" / "processed" / f"espef_corpus_{year}.parquet"
    for batch in pq.ParquetFile(source).iter_batches(columns=MODEL_COLUMNS, batch_size=batch_size):
        mask = pa.array([work_id in selected_ids for work_id in batch.column(0).to_pylist()])
        selected = batch.filter(mask)
        if selected.num_rows:
            yield selected