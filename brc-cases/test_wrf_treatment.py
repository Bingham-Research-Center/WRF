#!/usr/bin/env python3
"""Login-safe tests for WRF physics-treatment packet rendering."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import namelist_diff
import wrf_treatment


BASE = """&physics
mp_physics               = 8, 8, 8,
sf_sfclay_physics        = 1, 1, 1,
sf_surface_physics       = 2, 2, 2,
bl_pbl_physics           = 1, 1, 1,
cu_physics               = 0, 0, 0,
/

&fdda
/
"""


class WrfTreatmentTests(unittest.TestCase):
    def test_patch_adds_radiation_keys_and_changes_only_requested_settings(self) -> None:
        changes = {
            ("physics", "slope_rad"): ("1", "1", "1"),
            ("physics", "topo_shading"): ("1", "1", "1"),
            ("physics", "shadlen"): ("25000.",),
        }
        updated = wrf_treatment.patch_namelist(BASE, changes)
        before = namelist_diff.parse_namelist_text(BASE)
        after = namelist_diff.parse_namelist_text(updated)

        self.assertEqual(after[("physics", "slope_rad")], ("1", "1", "1"))
        self.assertEqual(after[("physics", "topo_shading")], ("1", "1", "1"))
        self.assertEqual(after[("physics", "shadlen")], ("25000.",))
        self.assertEqual(before[("physics", "bl_pbl_physics")], after[("physics", "bl_pbl_physics")])

    def test_patch_replaces_existing_scheme_assignments(self) -> None:
        updated = wrf_treatment.patch_namelist(
            BASE,
            {
                ("physics", "sf_sfclay_physics"): ("2", "2", "2"),
                ("physics", "bl_pbl_physics"): ("2", "2", "2"),
            },
        )
        values = namelist_diff.parse_namelist_text(updated)
        self.assertEqual(values[("physics", "sf_sfclay_physics")], ("2", "2", "2"))
        self.assertEqual(values[("physics", "bl_pbl_physics")], ("2", "2", "2"))
        self.assertEqual(values[("physics", "sf_surface_physics")], ("2", "2", "2"))

    def test_patch_rejects_missing_section(self) -> None:
        with self.assertRaisesRegex(ValueError, "section not found"):
            wrf_treatment.patch_namelist(BASE, {("domains", "feedback"): ("0",)})

    def test_dump_case_round_trips_supported_shape(self) -> None:
        data = {
            "schema_version": 1,
            "case": {"name": "unit", "domains": 3},
            "treatment": {"set.physics.slope_rad": ["1", "1", "1"]},
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "case.yaml"
            path.write_text(wrf_treatment.dump_case(data), encoding="utf-8")
            import wrf_case

            self.assertEqual(wrf_case.load_case(path), data)


if __name__ == "__main__":
    unittest.main()
