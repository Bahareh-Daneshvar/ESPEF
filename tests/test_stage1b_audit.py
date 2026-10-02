import collections
import unittest

from scripts.load_stage1b_modelling import iter_modelling_batches
from scripts.stage1b_audit import (
    REPORT_QUARTERS,
    empty_quarter_stats,
    make_qc_rows,
    quarter_for_date,
    suspected_text_language,
)


class Stage1BAuditTests(unittest.TestCase):
    def test_quarter_boundaries_preserve_year_partition(self):
        self.assertEqual(quarter_for_date("2021-03-31", 2021), "2021Q1")
        self.assertEqual(quarter_for_date("2021-04-01", 2021), "2021Q2")
        self.assertEqual(quarter_for_date("2026-09-30", 2026), "2026Q3")
        with self.assertRaises(RuntimeError):
            quarter_for_date("2026-10-01", 2026)
        with self.assertRaises(RuntimeError):
            quarter_for_date("2024-02-30", 2024)

    def test_language_flag_matches_ascii_letter_heuristic(self):
        self.assertFalse(suspected_text_language("English paper title", "ASCII abstract content"))
        self.assertTrue(suspected_text_language("Научная статья", "Исследование показывает результаты"))
        self.assertFalse(suspected_text_language("短い", "短文"))

    def test_qc_uses_known_source_denominator_for_shares_and_hhi(self):
        raw = collections.Counter({quarter: 1 for quarter in REPORT_QUARTERS})
        usable = collections.Counter({quarter: 1 for quarter in REPORT_QUARTERS})
        stats = {quarter: empty_quarter_stats() for quarter in REPORT_QUARTERS}
        for quarter in REPORT_QUARTERS:
            stats[quarter]["n_usable"] = 1
        first = stats["2021Q1"]
        first.update(
            n_usable=4,
            january_1=1,
            short_abstract=1,
            language_mismatch=1,
            known_version=2,
            missing_source=1,
        )
        raw["2021Q1"] = 5
        first["types"].update({"article": 2, "conference-paper": 1, "preprint": 1})
        first["sources"].update({"S1": 3})
        first["sources"].update({"S2": 1})
        first["source_names"]["S1"]["Venue One"] = 3
        first["source_names"]["S2"]["Venue Two"] = 1
        usable["2021Q1"] = 4

        row = make_qc_rows(raw, usable, stats)[0]
        self.assertEqual(row["usable_rate"], 0.8)
        self.assertEqual(row["january_1_flag_rate_usable_denominator"], 0.25)
        self.assertEqual(row["missing_primary_source_rate_usable_denominator"], 0.25)
        self.assertEqual(row["known_primary_source_denominator"], 4)
        self.assertEqual(row["source_hhi_known_primary_source_denominator"], 0.625)
        self.assertEqual(row["leading_source_1_id"], "S1")
        self.assertEqual(row["leading_source_1_share_known_source_denominator"], 0.75)

    def test_modelling_loader_rejects_2026_and_unknown_cohorts(self):
        with self.assertRaises(ValueError):
            next(iter_modelling_batches(2026))
        with self.assertRaises(ValueError):
            next(iter_modelling_batches(2021, "not-a-cohort"))


if __name__ == "__main__":
    unittest.main()