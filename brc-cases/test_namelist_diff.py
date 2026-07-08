#!/usr/bin/env python3
"""Login-safe tests for archived WRF namelist.input comparison."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import namelist_diff as nd


BASE_NAMELIST = """&time_control
 run_days                 = 0,
 run_hours                = 6,
 start_year               = 2013, 2013, 2013,
 start_month              = 02,   02,   02,
 start_day                = 02,   02,   02,
 start_hour               = 12,   12,   12,
 end_year                 = 2013, 2013, 2013,
 end_month                = 02,   02,   02,
 end_day                  = 02,   02,   02,
 end_hour                 = 18,   18,   18,
 interval_seconds         = 21600,
/

&domains
 max_dom                  = 3,
 e_vert                   = 75,   75,   75,
 eta_levels               = 1.00000, 0.99000,
                            0.97000, 0.00000,
 dx                       = 3000, 1000, 333.333,
 dy                       = 3000, 1000, 333.333,
 feedback                 = 1,  ! two-way
 smooth_option            = 0,
 num_metgrid_levels       = 40,
 num_metgrid_soil_levels  = 4,
/

&physics
 mp_physics               = 8,    8,    8,
 cu_physics               = 0,    0,    0,
/
"""


class NamelistDiffTests(unittest.TestCase):
    def test_parse_namelist_text_handles_vectors_comments_and_continuations(self) -> None:
        values = nd.parse_namelist_text(BASE_NAMELIST)

        self.assertEqual(values[("time_control", "interval_seconds")], ("21600",))
        self.assertEqual(values[("domains", "feedback")], ("1",))
        self.assertEqual(values[("domains", "eta_levels")], ("1.00000", "0.99000", "0.97000", "0.00000"))
        self.assertEqual(values[("physics", "cu_physics")], ("0", "0", "0"))

    def test_parse_namelist_text_normalizes_quotes_and_logicals(self) -> None:
        text = """&share
 fg_name = 'NAM', "GFS", ! comment
 active_grid = .TRUE., .false.,
 path_name = '/scratch/demo!literal',
/
"""
        values = nd.parse_namelist_text(text)

        self.assertEqual(values[("share", "fg_name")], ("NAM", "GFS"))
        self.assertEqual(values[("share", "active_grid")], (".true.", ".false."))
        self.assertEqual(values[("share", "path_name")], ("/scratch/demo!literal",))

    def test_resolve_namelist_path_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            namelist = root / "namelist.input"
            namelist.write_text(BASE_NAMELIST, encoding="utf-8")

            self.assertEqual(nd.resolve_namelist_path(root), namelist)

    def test_report_refuses_repo_local_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first.input"
            second = root / "second.input"
            first.write_text(BASE_NAMELIST, encoding="utf-8")
            second.write_text(BASE_NAMELIST.replace("feedback                 = 1", "feedback                 = 0"), encoding="utf-8")
            cases = [nd.load_case("first", first), nd.load_case("second", second)]

            with self.assertRaises(ValueError):
                nd.write_report(cases, nd.REPO_ROOT / "namelist_diff_unit")

    def test_write_report_creates_summary_matrix_and_raw_diff(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = root / "first.input"
            second = root / "second.input"
            first.write_text(BASE_NAMELIST, encoding="utf-8")
            second.write_text(
                BASE_NAMELIST
                .replace("feedback                 = 1", "feedback                 = 0")
                .replace("num_metgrid_levels       = 40", "num_metgrid_levels       = 27"),
                encoding="utf-8",
            )
            output_dir = root / "report"

            summary, matrix, diff_paths = nd.write_report(
                [nd.load_case("john_base", first), nd.load_case("john_oneway", second)],
                output_dir,
            )

            self.assertTrue(summary.exists())
            self.assertTrue(matrix.exists())
            self.assertEqual(len(diff_paths), 1)
            summary_text = summary.read_text(encoding="utf-8")
            matrix_text = matrix.read_text(encoding="utf-8")
            raw_diff = diff_paths[0].read_text(encoding="utf-8")
            self.assertIn("domains.feedback", summary_text)
            self.assertIn("domains\tnum_metgrid_levels\tyes", matrix_text)
            self.assertIn("- feedback                 = 1", raw_diff)
            self.assertIn("+ feedback                 = 0", raw_diff)


if __name__ == "__main__":
    unittest.main()
