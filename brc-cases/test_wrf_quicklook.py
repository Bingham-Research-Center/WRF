#!/usr/bin/env python3
"""Path-only tests for the BRC WRF quicklook helper."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import wrf_quicklook


REPO_ROOT = Path(__file__).resolve().parents[1]


class QuicklookPathTests(unittest.TestCase):
    def test_refuses_repo_local_output(self) -> None:
        output_dir = REPO_ROOT / "brc-cases" / "_unit_quicklooks"

        with self.assertRaisesRegex(ValueError, "inside the brc-wrf checkout"):
            wrf_quicklook._validate_output_dir(output_dir)

    def test_default_output_dir_is_archive_quicklooks(self) -> None:
        archive_run = Path("/tmp/brc_wrf_quicklook_unit/run_20260618T000000Z")
        ctx = wrf_quicklook.QuicklookContext(
            case_file=Path("unit.case.yaml"),
            data={},
            case_name="unit_case",
            case_start="2013-01-31_12:00:00",
            domains=(1, 2),
            manifest_path=Path("/tmp/manifest.json"),
            wps_run=Path("/tmp/wps_run"),
            archive_run=archive_run,
            met_by_domain={
                1: Path("/tmp/met_em.d01.nc"),
                2: Path("/tmp/met_em.d02.nc"),
            },
            wrf_by_domain={
                1: Path("/tmp/wrfout_d01"),
                2: Path("/tmp/wrfout_d02"),
            },
        )

        self.assertEqual(
            wrf_quicklook._default_output_dir(ctx),
            archive_run / "quicklooks",
        )

    def test_latest_archive_run_uses_newest_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            archive_root = Path(raw)
            (archive_root / "run_20260618T010000Z").mkdir()
            expected = archive_root / "run_20260618T030000Z"
            expected.mkdir()
            (archive_root / "not_a_run_20260618T040000Z").mkdir()
            (archive_root / "run_20260618T020000Z.txt").write_text("not a directory", encoding="utf-8")

            self.assertEqual(wrf_quicklook._latest_archive_run(archive_root), expected)

    def test_latest_archive_run_errors_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            archive_root = Path(raw)

            with self.assertRaisesRegex(FileNotFoundError, "no run_\\* archive directories"):
                wrf_quicklook._latest_archive_run(archive_root)

    def test_explicit_archive_run_bypasses_latest_scan(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            archive_root = Path(raw)
            explicit = archive_root / "manual_run"

            self.assertEqual(
                wrf_quicklook._resolve_archive_run(archive_root, str(explicit)),
                explicit,
            )


if __name__ == "__main__":
    unittest.main()
