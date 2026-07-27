#!/usr/bin/env python3
"""HRRR soil rules: the configuration gate C proved, and the one it disproved.

ashley2026_seiche gate C established that public HRRR GRIB (nat+sfc) carries ZERO
soil-temperature messages, so single-stream HRRR gives num_metgrid_soil_levels=0 and
real.exe cannot initialise Noah. The fix is a two-stream metgrid: HRRR for the
atmosphere with a soil-stripped Vtable, GFS 0.25 f000 for soil.

Before this module existed, wrf_case.py *enforced* the broken single-stream shape --
so the manifest validated cleanly precisely because it still recorded the disproven
configuration, and correcting it to what actually ran would have been rejected.
These tests exist so that cannot happen again.
"""

from __future__ import annotations

import unittest

import wrf_case


def _case(sources, wps_fg_name, namelist_fg_name, vtable, prefix="HRRR"):
    """A minimal case dict exercising only the source rules."""
    return {
        "case": {"name": "unit_case", "start": "2025-01-28_18:00:00",
                 "end": "2025-01-29_00:00:00", "domains": 3},
        "forcing": {
            "sources": sources,
            "wps_fg_name": wps_fg_name,
            "interval_seconds": 3600,
            "num_metgrid_levels": 51,
            "expected_met_em_count": 7,
            "manifest_path": "/scratch/unit/manifest.json",
            "contract_path": "/scratch/unit/contract.json",
        },
        "wps": {
            "vtable": vtable,
            "ungrib_prefix": prefix,
            "namelist_fg_name": namelist_fg_name,
            "namelist_template": "/scratch/unit/namelist.wps",
            "geogrid_source": "/scratch/unit/wps_run",
        },
        # Present only so validate_case reaches the source rules; not under test.
        "paths": {
            "wrf_src": "/scratch/unit/src",
            "wrf_build": "/scratch/unit/build",
            "wps_root": "/scratch/unit/wps",
            "input_root": "/scratch/unit/inputs",
            "grib_data": "/scratch/unit/grib",
            "run_root": "/scratch/unit/run",
            "wps_run": "/scratch/unit/run/wps_run",
            "wrf_run": "/scratch/unit/run/wrf_run",
            "geog_data_path": "/scratch/unit/geog",
            "archive_root": "/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/unit",
        },
        "slurm": {
            "profile": "owned_notch392_max",
            "job_name": "unit",
            "account": "lawson-np",
            "partition": "lawson-np",
            "nodes": 1,
            "ntasks": 56,
            "memory": "900G",
            "time": "01:00:00",
            "mpi_launcher": "srun --mpi=pmi2",
        },
    }


def _messages(data, level="ERROR"):
    return [f.message for f in wrf_case.validate_case(data, strict_files=False)
            if f.severity == level]


class HrrrSoilRuleTests(unittest.TestCase):
    def test_single_stream_hrrr_warns_it_cannot_initialise_noah(self):
        data = _case(["hrrr"], ["HRRR"], ["HRRR"], "Vtable.raphrrr")
        warns = " ".join(_messages(data, "WARN"))
        self.assertIn("soil", warns.lower())
        self.assertIn("hrrr", warns.lower())

    def test_two_stream_hrrr_gfs_is_accepted(self):
        """The configuration that actually ran must not be rejected."""
        data = _case(["hrrr", "gfs"], ["HRRR", "GFSSOIL"],
                     ["HRRR", "GFSSOIL"], "Vtable.raphrrr.nosoil")
        self.assertEqual(
            [m for m in _messages(data) if "fg_name" in m or "vtable" in m.lower()],
            [],
        )

    def test_two_stream_order_matters(self):
        """metgrid takes fg_name in priority order: HRRR must win the atmosphere."""
        data = _case(["hrrr", "gfs"], ["GFSSOIL", "HRRR"],
                     ["GFSSOIL", "HRRR"], "Vtable.raphrrr.nosoil")
        self.assertTrue(any("fg_name" in m for m in _messages(data)))

    def test_two_stream_rejects_the_unstripped_vtable(self):
        """Plain Vtable.raphrrr reinstates HRRR's degenerate 0/0.01 m soil layers."""
        data = _case(["hrrr", "gfs"], ["HRRR", "GFSSOIL"],
                     ["HRRR", "GFSSOIL"], "Vtable.raphrrr")
        self.assertTrue(any("nosoil" in m for m in _messages(data)))

    def test_hrrr_interval_is_hourly_in_both_shapes(self):
        for sources, fg in ((["hrrr"], ["HRRR"]),
                            (["hrrr", "gfs"], ["HRRR", "GFSSOIL"])):
            data = _case(sources, fg, fg,
                         "Vtable.raphrrr" if sources == ["hrrr"] else "Vtable.raphrrr.nosoil")
            data["forcing"]["interval_seconds"] = 10800
            self.assertTrue(any("interval_seconds" in m for m in _messages(data)),
                            f"no interval finding for {sources}")


if __name__ == "__main__":
    unittest.main()
