#!/usr/bin/env python3
"""Login-safe tests for WPS static HGT_M helper text transforms."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import wps_hgt_static as hgt


class WpsHgtStaticTests(unittest.TestCase):
    def test_tiles_for_pelican_bounds_include_utah_longitudes(self) -> None:
        tiles = hgt.tiles_for_bounds((-112.0, 40.0, -111.0, 41.0))
        self.assertTrue(tiles)
        left, north, right, south = hgt.tile_projwin(tiles[0])
        self.assertLessEqual(left, -112.0)
        self.assertGreaterEqual(right, -111.0)
        self.assertLessEqual(south, 40.0)
        self.assertGreaterEqual(north, 41.0)

    def test_patch_geogrid_table_text_adds_only_hgt_token(self) -> None:
        source = """name = HGT_M
        interp_option = gmted2010_30s:four_pt
        rel_path = gmted2010_30s:topo_gmted2010_30s/
===============================
name=LANDUSEF
        interp_option = default:nearest_neighbor
        rel_path = default:modis/
"""
        patched = hgt.patch_geogrid_table_text(source, token="terrain3s", rel_path="topo_terrain3s")
        self.assertIn("interp_option = terrain3s:average_gcell", patched)
        self.assertIn("rel_path = terrain3s:topo_terrain3s/", patched)
        self.assertEqual(patched.count("interp_option = terrain3s:"), 1)
        self.assertEqual(patched.count("rel_path = terrain3s:"), 1)

    def test_render_namelist_text_replaces_geog_fields(self) -> None:
        source = """&geogrid
 geog_data_res     = 'default','default','default',
 geog_data_path = '/old/path/'
/
"""
        rendered = hgt.render_namelist_text(
            source,
            token="terrain3s",
            geog_data_path=Path("/scratch/general/vast/u0737349/wps_geog_terrain3s"),
        )
        self.assertIn("terrain3s+default", rendered)
        self.assertIn("/scratch/general/vast/u0737349/wps_geog_terrain3s/", rendered)

    def test_index_text_has_wps_continuous_metadata(self) -> None:
        text = hgt.index_text()
        self.assertIn("type = continuous", text)
        self.assertIn("projection = regular_ll", text)
        self.assertIn("filename_digits = 6", text)
        self.assertIn("tile_bdr=3", text)

    def test_index_text_preserves_five_digit_names_for_30s_grid(self) -> None:
        text = hgt.index_text(dx_deg=30.0 / 3600.0)
        self.assertIn("filename_digits = 5", text)

    def test_tile_name_uses_selected_filename_width(self) -> None:
        tile = hgt.Tile(1, 1200, 1201, 2400)
        self.assertEqual(hgt.tile_name(tile, filename_digits=5), "00001-01200.01201-02400")
        self.assertEqual(hgt.tile_name(tile, filename_digits=6), "000001-001200.001201-002400")

    def test_manifest_round_trip_and_inventory_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = root / "manifest.tsv"
            rows = [
                hgt.ManifestRow(
                    url="https://example.invalid/path/demo one.tif",
                    filename="demo one.tif",
                    bytes_expected=12,
                    sha256_expected="abc",
                    title="Demo",
                )
            ]
            hgt.write_manifest(manifest, rows)
            loaded = hgt.read_manifest(manifest)
            self.assertEqual(loaded[0].filename, "demo_one.tif")
            self.assertEqual(loaded[0].bytes_expected, 12)

            inventory = root / "inventory.tsv"
            inventory.write_text(
                "status\tpath\tbytes\tsha256\turl\terror\n"
                f"cached\t{root / 'demo.tif'}\t12\tabc\thttps://example.invalid/demo.tif\t\n",
                encoding="utf-8",
            )
            self.assertEqual(hgt.paths_from_inventory(inventory), [root / "demo.tif"])

    def test_render_slurm_packet_writes_review_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            packet_dir = Path(raw) / "packet"
            args = type(
                "Args",
                (),
                {
                    "packet_dir": packet_dir,
                    "case_name": "unit terrain",
                    "run_id": "unit_run",
                    "bounds": (-114.0, 37.0, -105.0, 44.0),
                    "geog_data_path": Path("/scratch/general/vast/u0737349/wps_geog_static/unit"),
                    "static_output_dir": None,
                    "download_dir": Path("/scratch/general/vast/u0737349/wrf_inputs/unit/dem_cache"),
                    "rel_path": "topo_unit_3s",
                    "token": "unit_3s",
                    "source_manifest": None,
                    "usgs_dataset": hgt.DEFAULT_USGS_DATASET,
                    "usgs_format": "GeoTIFF",
                    "max_products": 10,
                    "timeout": 120,
                    "retries": 2,
                    "min_free_gb": 1.0,
                    "download_account": "",
                    "download_partition": "notchpeak-dtn",
                    "download_qos": "notchpeak-dtn",
                    "download_mem": "1G",
                    "download_time": "00:10:00",
                    "build_account": "lawson-np",
                    "build_partition": "lawson-np",
                    "build_qos": "",
                    "build_mem": "2G",
                    "build_time": "00:20:00",
                    "log_root": Path("/tmp/brc-wrf-test-logs"),
                    "description": "Unit test 3s terrain",
                },
            )()
            hgt.render_slurm_packet(args)
            self.assertTrue((packet_dir / "terrain_download.slurm").exists())
            self.assertTrue((packet_dir / "terrain_build.slurm").exists())
            self.assertIn("query-usgs", (packet_dir / "terrain_download.slurm").read_text(encoding="utf-8"))
            self.assertIn("build-from-inventory", (packet_dir / "terrain_build.slurm").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
