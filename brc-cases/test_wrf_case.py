#!/usr/bin/env python3
"""Focused tests for the BRC-local WRF case renderer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).with_name("wrf_case.py")


class RenderPracticalHarnessTests(unittest.TestCase):
    def write_case(self, workdir: Path) -> Path:
        manifest = workdir / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "manifest_kind": "wrf_input_staging",
                    "case": {"name": "unit_case", "sources": ["nam_analysis"]},
                }
            ),
            encoding="utf-8",
        )
        contract = workdir / "contract.json"
        contract.write_text(
            json.dumps(
                {
                    "contract_kind": "wps_wrf_case_contract",
                    "case": "unit_case",
                    "wps_fg_name": ["NAM"],
                    "interval_seconds": 21600,
                }
            ),
            encoding="utf-8",
        )
        case_file = workdir / "unit.case.yaml"
        case_file.write_text(
            f"""
schema_version: 1

case:
  name: unit_case
  start: "2013-01-31_12:00:00"
  end: "2013-02-02_00:00:00"
  domains: 2

forcing:
  sources: ["nam_analysis"]
  wps_fg_name: ["NAM"]
  interval_seconds: 21600
  num_metgrid_levels: 40
  expected_met_em_count: 14
  manifest_path: "{manifest}"
  contract_path: "{contract}"

paths:
  wrf_src: "{REPO_ROOT}"
  wrf_build: "/tmp/brc_wrf_unit_missing_wrf_build"
  wps_root: "/tmp/brc_wrf_unit_missing_wps"
  input_root: "/scratch/general/vast/${{USER}}/wrf_inputs/unit_case"
  run_root: "/scratch/general/vast/${{USER}}/wrf_runs/unit_case"
  wps_run: "/scratch/general/vast/${{USER}}/wrf_runs/unit_case/wps_run"
  wrf_run: "/scratch/general/vast/${{USER}}/wrf_runs/unit_case/wrf_run"
  geog_data_path: "/tmp/brc_wrf_unit_missing_geog"
  archive_root: "/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/unit_case"

slurm:
  profile: owned_notch392_max
  job_name: wrf_unit_case
  account: lawson-np
  partition: lawson-np
  nodelist: notch392
  nodes: 1
  ntasks: 56
  memory: "900G"
  time: "06:00:00"
  mpi_launcher: "srun --mpi=pmi2"

archive:
  colon_safe_wrfout_source: "./wrfout_d0*"
""".lstrip(),
            encoding="utf-8",
        )
        return case_file

    def run_harness(self, case_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "render-practical-harness",
                str(case_file),
                *args,
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_refuses_repo_local_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            case_file = self.write_case(Path(raw))
            output_dir = REPO_ROOT / "brc-cases" / f"_unit_practical_harness_{Path(raw).name}"

            result = self.run_harness(case_file, "--output-dir", str(output_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside the brc-wrf checkout", result.stderr)
            self.assertFalse(output_dir.exists())

    def test_default_packet_names_and_key_settings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            case_file = self.write_case(workdir)
            output_dir = workdir / "packet"

            result = self.run_harness(case_file, "--output-dir", str(output_dir))

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in (
                "README.md",
                "PREPARE_CHECKLIST.md",
                "APPROVAL_PACKET.md",
                "baseline.slurm",
                "scaling_t016.slurm",
                "scaling_t028.slurm",
                "scaling_t056.slurm",
            ):
                self.assertTrue((output_dir / name).is_file(), name)

            readme = (output_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("PREPARE_CHECKLIST.md", readme)
            self.assertIn("APPROVAL_PACKET.md", readme)
            self.assertIn("Peak memory evidence", readme)

            prepare = (output_dir / "PREPARE_CHECKLIST.md").read_text(encoding="utf-8")
            self.assertIn("practical_tests/baseline/wrf_run", prepare)
            self.assertIn("practical_tests/scaling_t016/wrf_run", prepare)
            self.assertIn("Approved batch, DTN, or interactive compute context only", prepare)

            approval = (output_dir / "APPROVAL_PACKET.md").read_text(encoding="utf-8")
            self.assertIn("Job ID | Slurm state | WRF marker", approval)
            self.assertIn("Peak memory evidence | Archive path | Debug path", approval)

            scaling = (output_dir / "scaling_t016.slurm").read_text(encoding="utf-8")
            self.assertIn("#SBATCH --ntasks=16", scaling)
            self.assertIn("practical_tests/scaling_t016/wrf_run", scaling)
            self.assertIn('require_executable "$WRF_RUN/real.exe"', scaling)

    def test_custom_tasks_and_memory_candidates_render(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            case_file = self.write_case(workdir)
            output_dir = workdir / "packet"

            result = self.run_harness(
                case_file,
                "--output-dir",
                str(output_dir),
                "--tasks",
                "4,12",
                "--memory-candidates",
                "450G,600G",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in (
                "scaling_t004.slurm",
                "scaling_t012.slurm",
                "memory_450G.slurm",
                "memory_600G.slurm",
            ):
                self.assertTrue((output_dir / name).is_file(), name)
            self.assertFalse((output_dir / "scaling_t016.slurm").exists())

            approval = (output_dir / "APPROVAL_PACKET.md").read_text(encoding="utf-8")
            self.assertIn("| scaling_t004 | `scaling_t004.slurm` | 4 | `900G` |", approval)
            self.assertIn("| scaling_t012 | `scaling_t012.slurm` | 12 | `900G` |", approval)
            self.assertIn("| memory_450G | `memory_450G.slurm` | 56 | `450G` |", approval)
            self.assertIn("| memory_600G | `memory_600G.slurm` | 56 | `600G` |", approval)

            memory_script = (output_dir / "memory_450G.slurm").read_text(encoding="utf-8")
            self.assertIn("#SBATCH --mem=450G", memory_script)
            self.assertIn("practical_tests/memory_450G/wrf_run", memory_script)


if __name__ == "__main__":
    unittest.main()
