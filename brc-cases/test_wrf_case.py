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
    def write_case(
        self,
        workdir: Path,
        case_name: str = "unit_case",
        wrf_build: str = "/tmp/brc_wrf_unit_missing_wrf_build",
        wps_root: str = "/tmp/brc_wrf_unit_missing_wps",
    ) -> Path:
        manifest = workdir / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "manifest_kind": "wrf_input_staging",
                    "case": {"name": case_name, "sources": ["nam_analysis"]},
                }
            ),
            encoding="utf-8",
        )
        contract = workdir / "contract.json"
        contract.write_text(
            json.dumps(
                {
                    "contract_kind": "wps_wrf_case_contract",
                    "case": case_name,
                    "wps_fg_name": ["NAM"],
                    "interval_seconds": 21600,
                }
            ),
            encoding="utf-8",
        )
        case_file = workdir / f"{case_name}.case.yaml"
        case_file.write_text(
            f"""
schema_version: 1

case:
  name: {case_name}
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
  wrf_build: "{wrf_build}"
  wps_root: "{wps_root}"
  input_root: "/scratch/general/vast/${{USER}}/wrf_inputs/{case_name}"
  run_root: "/scratch/general/vast/${{USER}}/wrf_runs/{case_name}"
  wps_run: "/scratch/general/vast/${{USER}}/wrf_runs/{case_name}/wps_run"
  wrf_run: "/scratch/general/vast/${{USER}}/wrf_runs/{case_name}/wrf_run"
  geog_data_path: "/tmp/brc_wrf_unit_missing_geog"
  archive_root: "/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/{case_name}"

slurm:
  profile: owned_notch392_max
  job_name: wrf_{case_name}
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

    def run_report(self, case_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "render-no-run-report",
                str(case_file),
                *args,
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_validate(self, case_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "validate",
                *args,
                str(case_file),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_render_slurm(self, case_file: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "render-slurm",
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

    def test_validate_wrf_build_requires_main_executables_and_runtime_sources(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            wrf_build = workdir / "fake_wrf_build"
            run_dir = wrf_build / "run"
            run_dir.mkdir(parents=True)
            for name in ("real.exe", "wrf.exe"):
                path = run_dir / name
                path.write_text("#!/bin/sh\n", encoding="utf-8")
                path.chmod(0o755)
            case_file = self.write_case(workdir, wrf_build=str(wrf_build))

            result = self.run_validate(case_file)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARN: paths.wrf_build missing executable main/real.exe", result.stdout)
            self.assertIn("WARN: paths.wrf_build missing executable main/wrf.exe", result.stdout)
            self.assertIn(
                "WARN: paths.wrf_build missing runtime file run/CAMtr_volume_mixing_ratio",
                result.stdout,
            )

    def test_render_slurm_defaults_to_shared_slurm_logs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            case_file = self.write_case(Path(raw))

            result = self.run_render_slurm(case_file)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "#SBATCH --chdir=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf",
                result.stdout,
            )
            self.assertIn(
                "#SBATCH --output=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wrf_unit_case_%j.out",
                result.stdout,
            )
            self.assertIn(
                "#SBATCH --error=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wrf_unit_case_%j.out",
                result.stdout,
            )

    def test_validate_wps_root_requires_top_level_executables(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            wps_root = workdir / "fake_wps"
            for subdir, exe in (
                ("geogrid", "geogrid.exe"),
                ("ungrib", "ungrib.exe"),
                ("metgrid", "metgrid.exe"),
            ):
                path = wps_root / subdir / exe
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("#!/bin/sh\n", encoding="utf-8")
                path.chmod(0o755)
            (wps_root / "link_grib.csh").write_text("#!/bin/csh\n", encoding="utf-8")
            vtable = wps_root / "ungrib" / "Variable_Tables" / "Vtable.NAM"
            vtable.parent.mkdir(parents=True, exist_ok=True)
            vtable.write_text("# NAM\n", encoding="utf-8")
            case_file = self.write_case(workdir, wps_root=str(wps_root))

            result = self.run_validate(case_file)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "WARN: paths.wps_root missing top-level executable geogrid.exe",
                result.stdout,
            )
            self.assertIn(
                "WARN: paths.wps_root missing top-level executable ungrib.exe",
                result.stdout,
            )
            self.assertIn(
                "WARN: paths.wps_root missing top-level executable metgrid.exe",
                result.stdout,
            )

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
                "prepare_baseline.sh",
                "prepare_scaling_t016.sh",
                "prepare_scaling_t028.sh",
                "prepare_scaling_t056.sh",
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
            self.assertIn("JOHN_WRF_BUILD=/tmp/brc_wrf_unit_missing_wrf_build", prepare)
            self.assertIn('rsync -av "$JOHN_WRF_BUILD"/main/wrf.exe "$WRF_RUN"/', prepare)
            self.assertIn('rsync -av --exclude="*.exe" "$JOHN_WRF_BUILD"/run/ "$WRF_RUN"/', prepare)
            self.assertIn('cmp -s "$JOHN_WRF_BUILD/main/wrf.exe" "$WRF_RUN/wrf.exe"', prepare)
            self.assertIn('test -f "$JOHN_WRF_BUILD/run/$runtime_file"', prepare)
            self.assertIn('cmp -s "$JOHN_WRF_BUILD/run/$runtime_file" "$WRF_RUN/$runtime_file"', prepare)
            self.assertIn("CAMtr_volume_mixing_ratio", prepare)

            prepare_script = (output_dir / "prepare_scaling_t016.sh").read_text(encoding="utf-8")
            self.assertIn('[[ "${BRC_PREP_APPROVED:-NO}" == "YES" ]]', prepare_script)
            self.assertIn("SCENARIO=scaling_t016", prepare_script)
            self.assertIn("practical_tests/scaling_t016/wrf_run", prepare_script)
            self.assertIn("PROVEN_WRF_RUN=", prepare_script)
            self.assertIn('case "$JOHN_WRF_BUILD" in *"/u6060939/"*)', prepare_script)
            self.assertIn('rsync -av "$JOHN_WRF_BUILD"/main/wrf.exe "$WRF_RUN"/', prepare_script)
            self.assertIn('rsync -av --exclude="*.exe" "$JOHN_WRF_BUILD"/run/ "$WRF_RUN"/', prepare_script)
            self.assertIn('cmp -s "$JOHN_WRF_BUILD/run/$runtime_file" "$WRF_RUN/$runtime_file"', prepare_script)
            self.assertIn("brc_prepare_summary.tsv", prepare_script)
            self.assertNotIn("sbatch", prepare_script)
            self.assertNotIn("./real.exe", prepare_script)
            self.assertNotIn("./wrf.exe", prepare_script)

            approval = (output_dir / "APPROVAL_PACKET.md").read_text(encoding="utf-8")
            self.assertIn("Job ID | Slurm state | WRF marker", approval)
            self.assertIn("Peak memory evidence | Archive path | Debug path", approval)

            scaling = (output_dir / "scaling_t016.slurm").read_text(encoding="utf-8")
            self.assertIn("#SBATCH --ntasks=16", scaling)
            self.assertIn(
                "#SBATCH --chdir=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf",
                scaling,
            )
            self.assertIn(
                "#SBATCH --output=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wrf_unit_case_t016_%j.out",
                scaling,
            )
            self.assertIn(
                "#SBATCH --error=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wrf_unit_case_t016_%j.out",
                scaling,
            )
            self.assertIn("practical_tests/scaling_t016/wrf_run", scaling)
            self.assertIn('check_executable "$WRF_RUN/real.exe"', scaling)
            self.assertIn("WRF_BUILD=/tmp/brc_wrf_unit_missing_wrf_build", scaling)
            self.assertIn("EXPECTED_WRF=/tmp/brc_wrf_unit_missing_wrf_build/main/wrf.exe", scaling)
            self.assertIn('require_matching_executable "$EXPECTED_WRF" "$WRF_RUN/wrf.exe" "wrf.exe"', scaling)
            self.assertIn("does not match John-owned WRF build", scaling)
            self.assertIn("for runtime_file in CAMtr_volume_mixing_ratio", scaling)
            self.assertIn('check_file "$WRF_BUILD/run/$runtime_file"', scaling)
            self.assertIn('check_file "$WRF_RUN/$runtime_file"', scaling)
            self.assertIn(
                'require_matching_file "$WRF_BUILD/run/$runtime_file" "$WRF_RUN/$runtime_file" "$runtime_file"',
                scaling,
            )
            self.assertIn("does not match John-owned WRF run directory", scaling)
            self.assertIn("preflight failed; prepare WRF_RUN before resubmitting", scaling)

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
                "prepare_scaling_t004.sh",
                "prepare_scaling_t012.sh",
                "prepare_memory_450G.sh",
                "prepare_memory_600G.sh",
            ):
                self.assertTrue((output_dir / name).is_file(), name)
            self.assertFalse((output_dir / "scaling_t016.slurm").exists())
            self.assertFalse((output_dir / "prepare_scaling_t016.sh").exists())

            approval = (output_dir / "APPROVAL_PACKET.md").read_text(encoding="utf-8")
            self.assertIn("| scaling_t004 | `scaling_t004.slurm` | 4 | `900G` |", approval)
            self.assertIn("| scaling_t012 | `scaling_t012.slurm` | 12 | `900G` |", approval)
            self.assertIn("| memory_450G | `memory_450G.slurm` | 56 | `450G` |", approval)
            self.assertIn("| memory_600G | `memory_600G.slurm` | 56 | `600G` |", approval)

            memory_script = (output_dir / "memory_450G.slurm").read_text(encoding="utf-8")
            self.assertIn("#SBATCH --mem=450G", memory_script)
            self.assertIn("practical_tests/memory_450G/wrf_run", memory_script)

    def test_jan2013_approval_packet_records_completed_t028(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            case_file = self.write_case(workdir, case_name="jan2013_basin_gefs")
            output_dir = workdir / "packet"

            result = self.run_harness(case_file, "--output-dir", str(output_dir))

            self.assertEqual(result.returncode, 0, result.stderr)
            approval = (output_dir / "APPROVAL_PACKET.md").read_text(encoding="utf-8")
            self.assertIn("## Current Practical Evidence", approval)
            self.assertIn("`scaling_t028` | Completed with John's WRF `V4.8.0`", approval)
            self.assertIn("`scaling_t016` | Job `13550555` failed before WRF runtime evidence", approval)
            self.assertIn("Rerendered scripts now use shared Slurm `--chdir` and stdout/stderr", approval)
            self.assertIn("Job `13550909` used the shared log path and failed before `real.exe`", approval)
            self.assertIn("wrf_jan2013_nam_t016_13550909.out", approval)
            self.assertIn("Prepare that scenario `WRF_RUN` before any retry", approval)
            self.assertIn("Do not rerun `scaling_t028` by default", approval)

    def test_no_run_report_writes_report_packet_and_slurm_syntax_check(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            case_file = self.write_case(workdir)
            report = workdir / "no_run_report.md"
            packet = workdir / "packet"
            slurm = workdir / "render.slurm"

            result = self.run_report(
                case_file,
                "--output",
                str(report),
                "--packet-dir",
                str(packet),
                "--slurm-output",
                str(slurm),
                "--memory-candidates",
                "450G,600G",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(report.is_file())
            self.assertTrue((packet / "APPROVAL_PACKET.md").is_file())
            self.assertTrue((packet / "prepare_scaling_t016.sh").is_file())
            self.assertTrue((packet / "memory_450G.slurm").is_file())
            self.assertTrue((packet / "prepare_memory_450G.sh").is_file())
            self.assertTrue(slurm.is_file())

            text = report.read_text(encoding="utf-8")
            self.assertIn("BRC WRF No-Run Report: unit_case", text)
            self.assertIn("| Case metadata validation | `PASS` |", text)
            self.assertIn("| Rendered shell syntax | `PASS` |", text)
            self.assertIn("prepare_scaling_t016.sh", text)
            self.assertIn("memory_450G.slurm", text)
            self.assertIn("Not run: `--strict-files`, manifest hashing", text)
            self.assertIn("single row remains `scaling_t016`", text)

    def test_no_run_report_refuses_repo_local_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            case_file = self.write_case(Path(raw))
            output = REPO_ROOT / "brc-cases" / f"_unit_no_run_report_{Path(raw).name}.md"

            result = self.run_report(case_file, "--output", str(output))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("outside the brc-wrf checkout", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
