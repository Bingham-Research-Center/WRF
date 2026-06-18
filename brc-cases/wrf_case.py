#!/usr/bin/env python3
"""Validate and render BRC WRF case manifests without running WRF.

This is deliberately small and dependency-free. It accepts only the constrained
case-YAML subset documented in ``brc-cases/README.md``.
"""

from __future__ import annotations

import argparse
import ast
import copy
import glob
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DATE_FORMAT = "%Y-%m-%d_%H:%M:%S"
CASE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULT_PRACTICAL_TASKS = (16, 28, 56)

REQUIRED_SECTIONS = {
    "case": ("name", "start", "end", "domains"),
    "forcing": (
        "sources",
        "wps_fg_name",
        "interval_seconds",
        "num_metgrid_levels",
        "manifest_path",
        "contract_path",
    ),
    "paths": (
        "wrf_src",
        "wrf_build",
        "wps_root",
        "input_root",
        "run_root",
        "wps_run",
        "wrf_run",
        "geog_data_path",
        "archive_root",
    ),
    "slurm": (
        "job_name",
        "account",
        "partition",
        "nodes",
        "ntasks",
        "time",
        "memory",
        "mpi_launcher",
    ),
}


@dataclass
class Finding:
    severity: str
    message: str


def parse_value(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith(('"', "'", "[", "{")):
        return ast.literal_eval(raw)
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if re.fullmatch(r"[-+]?\d+", raw):
        return int(raw)
    return raw


def load_case(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    current_name: str | None = None

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        body = line.split("#", 1)[0].rstrip()
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        if indent == 0:
            if ":" not in body:
                raise ValueError(f"{path}:{line_no}: expected 'key:'")
            key, raw = body.split(":", 1)
            key = key.strip()
            raw = raw.strip()
            if raw:
                data[key] = parse_value(raw)
                current = None
                current_name = None
            else:
                section: dict[str, Any] = {}
                data[key] = section
                current = section
                current_name = key
            continue
        if indent != 2 or current is None or current_name is None:
            raise ValueError(
                f"{path}:{line_no}: only two-space section keys are supported"
            )
        if ":" not in body.lstrip(" "):
            raise ValueError(f"{path}:{line_no}: expected 'key: value'")
        key, raw = body.lstrip(" ").split(":", 1)
        current[key.strip()] = parse_value(raw)
    return data


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def as_path(value: Any) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(value))))


def path_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def add_path_finding(
    findings: list[Finding],
    path: Path,
    label: str,
    *,
    strict_files: bool,
    must_be_dir: bool | None = None,
) -> None:
    if not path.exists():
        severity = "ERROR" if strict_files else "WARN"
        findings.append(Finding(severity, f"{label} does not exist: {path}"))
        return
    if must_be_dir is True and not path.is_dir():
        findings.append(Finding("ERROR", f"{label} is not a directory: {path}"))
    if must_be_dir is False and not path.is_file():
        findings.append(Finding("ERROR", f"{label} is not a file: {path}"))


def add_executable_root_findings(
    findings: list[Finding],
    root: Path,
    label: str,
    *,
    strict_files: bool,
    executables: tuple[str, ...],
    subdirs: tuple[str, ...] = (),
    files: tuple[str, ...] = (),
) -> None:
    add_path_finding(
        findings,
        root,
        label,
        strict_files=strict_files,
        must_be_dir=True,
    )
    if not root.exists() or not root.is_dir():
        return

    severity = "ERROR" if strict_files else "WARN"
    for exe in executables:
        candidates = [
            root / exe,
            root / "run" / exe,
            root / "main" / exe,
            root / "geogrid" / exe,
            root / "ungrib" / exe,
            root / "metgrid" / exe,
            root / "geogrid" / "src" / exe,
            root / "ungrib" / "src" / exe,
            root / "metgrid" / "src" / exe,
        ]
        if not any(path.exists() and os.access(path, os.X_OK) for path in candidates):
            findings.append(
                Finding(severity, f"{label} missing executable {exe} under {root}")
            )

    for subdir in subdirs:
        path = root / subdir
        if not path.is_dir():
            findings.append(Finding(severity, f"{label} missing directory {subdir}: {path}"))

    for file_name in files:
        path = root / file_name
        if not path.is_file():
            findings.append(Finding(severity, f"{label} missing file {file_name}: {path}"))


def add_storage_policy_findings(
    findings: list[Finding],
    data: dict[str, Any],
    *,
    strict_files: bool,
) -> None:
    paths = data["paths"]
    repo_root = as_path(paths["wrf_src"])
    for key in ("input_root", "grib_data", "run_root", "wps_run", "wrf_run", "archive_root"):
        if key not in paths:
            continue
        path = as_path(paths[key])
        if path_under(path, repo_root):
            findings.append(
                Finding(
                    "ERROR",
                    f"paths.{key} must not be inside the brc-wrf checkout: {path}",
                )
            )

    archive_root = as_path(paths["archive_root"])
    archive_text = str(archive_root)
    if archive_text.startswith("/scratch/"):
        findings.append(
            Finding("ERROR", f"paths.archive_root must be durable, not scratch: {archive_root}")
        )
    elif "lawson-group6" not in archive_text:
        severity = "ERROR" if strict_files else "WARN"
        findings.append(
            Finding(
                severity,
                "paths.archive_root should be under durable lawson-group6 storage: "
                f"{archive_root}",
            )
        )


def parse_case_datetime(value: Any, field: str, findings: list[Finding]) -> datetime | None:
    text = str(value)
    for fmt in (DATE_FORMAT, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    findings.append(Finding("ERROR", f"case.{field} has unsupported date format: {text}"))
    return None


def parse_namelist_values(path: Path) -> dict[str, list[str]]:
    wanted = {
        "start_date",
        "end_date",
        "interval_seconds",
        "fg_name",
        "geog_data_path",
        "num_metgrid_levels",
    }
    values: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        body = line.split("!", 1)[0]
        if "=" not in body:
            continue
        key, raw = body.split("=", 1)
        key = key.strip()
        if key not in wanted:
            continue
        quoted = re.findall(r"'([^']*)'|\"([^\"]*)\"", raw)
        if quoted:
            values[key] = [a or b for a, b in quoted]
        else:
            values[key] = [v.strip().strip(",") for v in raw.split(",") if v.strip()]
    return values


def parse_memory_gib(value: Any) -> float | None:
    text = str(value).strip().upper()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([GMTP]?)(?:I?B)?", text)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2) or "M"
    if unit == "T":
        return amount * 1024
    if unit == "G":
        return amount
    if unit == "M":
        return amount / 1024
    if unit == "P":
        return amount * 1024 * 1024
    return None


def validate_manifest(
    findings: list[Finding],
    path: Path,
    case_name: str,
    sources: list[str],
    strict_files: bool,
) -> None:
    if not path.exists():
        add_path_finding(findings, path, "forcing.manifest_path", strict_files=strict_files)
        return
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(Finding("ERROR", f"manifest JSON is invalid: {path}: {exc}"))
        return
    if manifest.get("manifest_kind") != "wrf_input_staging":
        findings.append(Finding("ERROR", f"manifest_kind is not wrf_input_staging: {path}"))
    manifest_case = manifest.get("case", {})
    if manifest_case.get("name") != case_name:
        findings.append(
            Finding(
                "WARN",
                f"manifest case name {manifest_case.get('name')!r} != case.name {case_name!r}",
            )
        )
    manifest_sources = set(as_list(manifest_case.get("sources")))
    missing = set(sources) - manifest_sources
    if missing:
        findings.append(Finding("WARN", f"manifest missing requested sources: {sorted(missing)}"))


def validate_contract(
    findings: list[Finding],
    path: Path,
    case_name: str,
    wps_fg_name: list[str],
    interval_seconds: int,
    strict_files: bool,
) -> None:
    if not path.exists():
        add_path_finding(findings, path, "forcing.contract_path", strict_files=strict_files)
        return
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(Finding("ERROR", f"contract JSON is invalid: {path}: {exc}"))
        return
    if contract.get("contract_kind") != "wps_wrf_case_contract":
        findings.append(Finding("ERROR", f"contract_kind is not wps_wrf_case_contract: {path}"))
    if contract.get("case") != case_name:
        findings.append(
            Finding("ERROR", f"contract case {contract.get('case')!r} != {case_name!r}")
        )
    if as_list(contract.get("wps_fg_name")) != wps_fg_name:
        findings.append(
            Finding(
                "ERROR",
                f"contract wps_fg_name {contract.get('wps_fg_name')!r} != {wps_fg_name!r}",
            )
        )
    if contract.get("interval_seconds") != interval_seconds:
        findings.append(
            Finding(
                "ERROR",
                f"contract interval_seconds {contract.get('interval_seconds')!r} != {interval_seconds!r}",
            )
        )


def validate_namelists(
    findings: list[Finding],
    data: dict[str, Any],
    *,
    strict_files: bool,
) -> None:
    namelists = data.get("namelists", {})
    forcing = data["forcing"]
    paths = data["paths"]
    case = data["case"]
    wps = data.get("wps", {})
    start = str(case["start"])
    end = str(case["end"])

    for key in ("namelist_wps", "namelist_input"):
        if key not in namelists:
            continue
        path = as_path(namelists[key])
        if not path.exists():
            add_path_finding(findings, path, key, strict_files=strict_files)
            continue
        values = parse_namelist_values(path)
        if key == "namelist_wps":
            interval = values.get("interval_seconds", [None])[0]
            if interval is not None and int(interval) != int(forcing["interval_seconds"]):
                findings.append(
                    Finding("ERROR", f"{key} interval_seconds {interval} != case value")
                )
            fg_name = values.get("fg_name")
            expected_fg_name = as_list(wps.get("namelist_fg_name", forcing["wps_fg_name"]))
            if fg_name and fg_name != expected_fg_name:
                findings.append(
                    Finding("ERROR", f"{key} fg_name {fg_name!r} != expected {expected_fg_name!r}")
                )
            geog = values.get("geog_data_path", [None])[0]
            if geog and as_path(geog) != as_path(paths["geog_data_path"]):
                findings.append(Finding("ERROR", f"{key} geog_data_path differs from case"))
            starts = values.get("start_date", [])
            ends = values.get("end_date", [])
            if starts and any(v != start for v in starts):
                findings.append(Finding("WARN", f"{key} start_date does not match {start}"))
            if ends and any(v != end for v in ends):
                findings.append(Finding("WARN", f"{key} end_date does not match {end}"))
        if key == "namelist_input":
            levels = values.get("num_metgrid_levels", [None])[0]
            if levels is not None and int(levels) != int(forcing["num_metgrid_levels"]):
                findings.append(
                    Finding("ERROR", f"{key} num_metgrid_levels {levels} != case value")
                )


def validate_case(data: dict[str, Any], *, strict_files: bool) -> list[Finding]:
    findings: list[Finding] = []

    for section, keys in REQUIRED_SECTIONS.items():
        if section not in data or not isinstance(data[section], dict):
            findings.append(Finding("ERROR", f"missing section: {section}"))
            continue
        for key in keys:
            if key not in data[section]:
                findings.append(Finding("ERROR", f"missing required key: {section}.{key}"))
    if any(f.severity == "ERROR" for f in findings):
        return findings

    case = data["case"]
    forcing = data["forcing"]
    paths = data["paths"]
    slurm = data["slurm"]

    case_name = str(case["name"])
    if not CASE_NAME_RE.match(case_name):
        findings.append(Finding("ERROR", f"case.name is not path-safe: {case_name!r}"))

    start = parse_case_datetime(case["start"], "start", findings)
    end = parse_case_datetime(case["end"], "end", findings)
    if start and end and start >= end:
        findings.append(Finding("ERROR", "case.start must be before case.end"))

    domains = int(case["domains"])
    if domains < 1:
        findings.append(Finding("ERROR", "case.domains must be >= 1"))

    sources = [str(v) for v in as_list(forcing["sources"])]
    wps_fg_name = [str(v) for v in as_list(forcing["wps_fg_name"])]
    interval_seconds = int(forcing["interval_seconds"])
    num_metgrid_levels = int(forcing["num_metgrid_levels"])

    if sources == ["nam_analysis"] and wps_fg_name != ["NAM"]:
        findings.append(Finding("ERROR", "NAM-only source should use wps_fg_name ['NAM']"))
    if sources == ["nam_analysis"] and interval_seconds != 21600:
        findings.append(Finding("ERROR", "NAM-only source should use interval_seconds 21600"))
    if "gefs_reforecast" in sources and interval_seconds != 10800:
        findings.append(Finding("WARN", "GEFS reforecast stream normally uses 10800 seconds"))
    if "gefs_reforecast" in sources and wps_fg_name != ["GEFS", "NAM"]:
        findings.append(Finding("WARN", "two-stream GEFS+NAM should use fg_name ['GEFS', 'NAM']"))
    if num_metgrid_levels <= 0:
        findings.append(Finding("ERROR", "num_metgrid_levels must be positive"))

    add_path_finding(
        findings, as_path(paths["wrf_src"]), "paths.wrf_src",
        strict_files=True, must_be_dir=True,
    )
    add_executable_root_findings(
        findings,
        as_path(paths["wrf_build"]),
        "paths.wrf_build",
        strict_files=strict_files,
        executables=("real.exe", "wrf.exe"),
        subdirs=("run",),
    )
    add_executable_root_findings(
        findings,
        as_path(paths["wps_root"]),
        "paths.wps_root",
        strict_files=strict_files,
        executables=("geogrid.exe", "ungrib.exe", "metgrid.exe"),
        subdirs=("geogrid", "metgrid", "ungrib"),
        files=("link_grib.csh", "ungrib/Variable_Tables/Vtable.NAM"),
    )
    add_path_finding(
        findings, as_path(paths["geog_data_path"]), "paths.geog_data_path",
        strict_files=strict_files, must_be_dir=True,
    )
    for key in ("input_root", "run_root", "wps_run", "wrf_run", "archive_root"):
        add_path_finding(
            findings, as_path(paths[key]), f"paths.{key}",
            strict_files=strict_files, must_be_dir=True,
        )
    if "grib_data" in paths:
        add_path_finding(
            findings, as_path(paths["grib_data"]), "paths.grib_data",
            strict_files=strict_files, must_be_dir=True,
        )
    add_storage_policy_findings(findings, data, strict_files=strict_files)

    validate_manifest(
        findings,
        as_path(forcing["manifest_path"]),
        case_name,
        sources,
        strict_files,
    )
    validate_contract(
        findings,
        as_path(forcing["contract_path"]),
        case_name,
        wps_fg_name,
        interval_seconds,
        strict_files,
    )
    validate_namelists(findings, data, strict_files=strict_files)

    wrf_run = as_path(paths["wrf_run"])
    stale_met_em = []
    for item in sorted(glob.glob(str(wrf_run / "met_em.d0*.nc"))):
        path = Path(item)
        if path.is_symlink():
            try:
                if path.resolve().parent == as_path(paths["wps_run"]).resolve():
                    continue
            except OSError:
                pass
        stale_met_em.append(item)
    if stale_met_em:
        severity = "ERROR" if strict_files else "WARN"
        findings.append(
            Finding(severity, f"wrf_run contains stale met_em files: {len(stale_met_em)}")
        )

    wps_run = as_path(paths["wps_run"])
    met_em = sorted(glob.glob(str(wps_run / "met_em.d0*.nc")))
    expected_met_em = forcing.get("expected_met_em_count")
    if met_em and expected_met_em is not None and len(met_em) != int(expected_met_em):
        findings.append(
            Finding(
                "WARN",
                f"wps_run has {len(met_em)} met_em files, expected {expected_met_em}",
            )
        )

    if int(slurm["nodes"]) != 1:
        findings.append(Finding("WARN", "validated Basin proof uses one Slurm node"))
    if int(slurm["ntasks"]) <= 0:
        findings.append(Finding("ERROR", "slurm.ntasks must be positive"))
    if str(slurm["account"]) != "lawson-np" or str(slurm["partition"]) != "lawson-np":
        findings.append(Finding("WARN", "default validated target is lawson-np"))
    if "srun --mpi=pmi2" not in str(slurm["mpi_launcher"]):
        findings.append(Finding("ERROR", "slurm.mpi_launcher must include 'srun --mpi=pmi2'"))
    if slurm.get("profile") == "owned_notch392_max":
        if str(slurm["account"]) != "lawson-np" or str(slurm["partition"]) != "lawson-np":
            findings.append(Finding("ERROR", "owned_notch392_max requires lawson-np account/partition"))
        if str(slurm.get("nodelist")) != "notch392":
            findings.append(Finding("ERROR", "owned_notch392_max requires nodelist notch392"))
        if int(slurm["nodes"]) != 1 or int(slurm["ntasks"]) != 56:
            findings.append(Finding("ERROR", "owned_notch392_max requires nodes=1 and ntasks=56"))
        memory_gib = parse_memory_gib(slurm["memory"])
        if memory_gib is None:
            findings.append(Finding("ERROR", f"could not parse slurm.memory: {slurm['memory']}"))
        elif memory_gib < 900:
            findings.append(Finding("WARN", "owned_notch392_max should request at least 900G"))

    archive = data.get("archive", {})
    if archive.get("colon_safe_wrfout_source") != "./wrfout_d0*":
        findings.append(Finding("WARN", "archive should use ./wrfout_d0* for colon-safe rsync"))

    return findings


def shell_quote(value: Any) -> str:
    return shlex.quote(str(value))


def text_value(value: Any) -> str:
    values = as_list(value)
    if not values:
        return ""
    return ", ".join(str(v) for v in values)


def render_slurm(data: dict[str, Any], case_file: Path) -> str:
    case = data["case"]
    forcing = data["forcing"]
    paths = data["paths"]
    wps = data.get("wps", {})
    slurm = data["slurm"]

    job_name = str(slurm["job_name"])
    archive_root = as_path(paths["archive_root"])
    wrf_run = as_path(paths["wrf_run"])
    mpi_launcher = str(slurm["mpi_launcher"])
    wps_prefix = wps.get("ungrib_prefix", "unset")
    namelist_fg_name = text_value(wps.get("namelist_fg_name", forcing["wps_fg_name"]))

    lines = [
        "#!/bin/bash",
        f"# Rendered by brc-cases/wrf_case.py from {case_file}",
        "# Review only. Do not submit without explicit human approval.",
        f"#SBATCH --job-name={job_name}",
        f"#SBATCH --account={slurm['account']}",
        f"#SBATCH --partition={slurm['partition']}",
        f"#SBATCH --nodes={slurm['nodes']}",
        f"#SBATCH --ntasks={slurm['ntasks']}",
        f"#SBATCH --mem={slurm['memory']}",
        f"#SBATCH --time={slurm['time']}",
    ]
    if slurm.get("nodelist"):
        lines.append(f"#SBATCH --nodelist={slurm['nodelist']}")
    lines.extend(
        [
            "",
            "set -euo pipefail",
            "",
            f"CASE_NAME={shell_quote(case['name'])}",
            f"WRF_RUN={shell_quote(wrf_run)}",
            f"ARCHIVE_ROOT={shell_quote(archive_root)}",
            'ARCHIVE_DIR="${ARCHIVE_ROOT}/run_$(date -u +%Y%m%dT%H%M%SZ)"',
            'DEBUG_DIR="${WRF_RUN}/brc_run_debug"',
            'SUMMARY_LOG="${DEBUG_DIR}/run_debug_summary.txt"',
            'PHASE_LOG="${DEBUG_DIR}/run_phase_times.tsv"',
            'INVENTORY_LOG="${DEBUG_DIR}/run_file_inventory.tsv"',
            "",
            'utc_now() { date -u +%Y-%m-%dT%H:%M:%SZ; }',
            'epoch_now() { date -u +%s; }',
            'fail() { printf "ERROR: %s\\n" "$*" >&2; exit 2; }',
            'require_file() { [[ -f "$1" ]] || fail "missing required file: $1"; }',
            'require_executable() { [[ -x "$1" ]] || fail "missing required executable: $1"; }',
            'require_glob() { compgen -G "$1" >/dev/null || fail "missing required files matching: $1"; }',
            "",
            "run_phase() {",
            "  local phase=\"$1\"",
            "  shift",
            "  local start_utc start_epoch end_utc end_epoch rc",
            "  start_utc=$(utc_now)",
            "  start_epoch=$(epoch_now)",
            "  set +e",
            "  \"$@\"",
            "  rc=$?",
            "  set -e",
            "  end_utc=$(utc_now)",
            "  end_epoch=$(epoch_now)",
            "  printf \"%s\\t%s\\t%s\\t%s\\t%s\\n\" \\",
            "    \"$phase\" \"$start_utc\" \"$end_utc\" \"$((end_epoch - start_epoch))\" \"$rc\" >> \"$PHASE_LOG\"",
            "  return \"$rc\"",
            "}",
            "",
            "write_inventory() {",
            "  local pattern count bytes newest",
            "  {",
            "    printf \"pattern\\tcount\\tbytes\\tnewest_epoch\\n\"",
            "    for pattern in met_em.d0*.nc wrfinput_d0* wrfbdy_d01 wrfout_d0* rsl.out.* rsl.error.* real.rsl.out.* real.rsl.error.*; do",
            "      count=$(find . -maxdepth 1 -name \"$pattern\" -type f | wc -l)",
            "      bytes=$(find . -maxdepth 1 -name \"$pattern\" -type f -printf '%s\\n' | awk '{s+=$1} END{print s+0}')",
            "      newest=$(find . -maxdepth 1 -name \"$pattern\" -type f -printf '%T@\\n' | sort -nr | head -n 1)",
            "      newest=${newest:-NA}",
            "      printf \"%s\\t%s\\t%s\\t%s\\n\" \"$pattern\" \"$count\" \"$bytes\" \"$newest\"",
            "    done",
            "  } > \"$INVENTORY_LOG\"",
            "}",
            "",
            "write_summary_preamble() {",
            "  {",
            "    printf \"BRC WRF run debug summary\\n\"",
            "    printf \"generated_utc\\t%s\\n\" \"$(utc_now)\"",
            "    printf \"case\\t%s\\n\" \"$CASE_NAME\"",
            "    printf \"job_id\\t%s\\n\" \"${SLURM_JOB_ID:-none}\"",
            "    printf \"host\\t%s\\n\" \"$(hostname)\"",
            "    printf \"submit_dir\\t%s\\n\" \"${SLURM_SUBMIT_DIR:-unset}\"",
            "    printf \"wrf_run\\t%s\\n\" \"$WRF_RUN\"",
            "    printf \"archive_dir\\t%s\\n\" \"$ARCHIVE_DIR\"",
            "    printf \"wrf_commit\\t%s\\n\" \"$(git -C " + shell_quote(paths["wrf_src"]) + " rev-parse --short HEAD 2>/dev/null || printf unknown)\"",
            f"    printf \"manifest_path\\t%s\\n\" {shell_quote(forcing['manifest_path'])}",
            f"    printf \"contract_path\\t%s\\n\" {shell_quote(forcing['contract_path'])}",
            "    printf \"\\nSettings\\n\"",
            "    printf \"| Item | Value |\\n\"",
            "    printf \"| --- | --- |\\n\"",
            f"    printf \"| Case window | %s to %s |\\n\" {shell_quote(case['start'])} {shell_quote(case['end'])}",
            f"    printf \"| Domains | %s |\\n\" {shell_quote(case['domains'])}",
            f"    printf \"| Forcing | %s |\\n\" {shell_quote(text_value(forcing['sources']))}",
            f"    printf \"| WPS cadence | interval_seconds = %s |\\n\" {shell_quote(forcing['interval_seconds'])}",
            f"    printf \"| WPS Vtable | %s |\\n\" {shell_quote(wps.get('vtable', 'unset'))}",
            f"    printf \"| WPS prefix / fg_name | %s / %s |\\n\" {shell_quote(wps_prefix)} {shell_quote(namelist_fg_name)}",
            f"    printf \"| met_em count / levels | %s files / %s levels |\\n\" {shell_quote(forcing.get('expected_met_em_count', 'unset'))} {shell_quote(forcing['num_metgrid_levels'])}",
            f"    printf \"| Slurm shape | %s node(s), %s task(s), %s, %s |\\n\" {shell_quote(slurm['nodes'])} {shell_quote(slurm['ntasks'])} {shell_quote(slurm['memory'])} {shell_quote(slurm['time'])}",
            f"    printf \"| Launcher | %s |\\n\" {shell_quote(mpi_launcher)}",
            "    printf \"\\nGotchas\\n\"",
            "    printf \"1. Do not run practical checks from login nodes; this script belongs in approved Slurm/compute context.\\n\"",
            "    printf \"2. Keep ungrib prefix and metgrid fg_name paired.\\n\"",
            "    printf \"3. NAM-only cadence is 21600 seconds; GEFS+NAM would be a separate 10800-second proof.\\n\"",
            "    printf \"4. Use srun --mpi=pmi2 for wrf.exe on this Intel MPI stack.\\n\"",
            "    printf \"5. Check real.exe, wrf.exe, archive completeness, and Slurm state as separate facts.\\n\"",
            "    printf \"\\nModules\\n\"",
            "    module -t list 2>&1 || true",
            "  } > \"$SUMMARY_LOG\"",
            "}",
            "",
            "finalize_debug() {",
            "  local rc=$?",
            "  set +e",
            "  printf \"final_status\\t%s\\n\" \"$rc\" >> \"$SUMMARY_LOG\"",
            "  printf \"finished_utc\\t%s\\n\" \"$(utc_now)\" >> \"$SUMMARY_LOG\"",
            "  write_inventory",
            "  mkdir -p \"$ARCHIVE_DIR/debug\"",
            "  rsync -av \"$DEBUG_DIR\"/ \"$ARCHIVE_DIR/debug/\" >/dev/null 2>&1",
            "  exit \"$rc\"",
            "}",
            "",
            '[[ -d "$WRF_RUN" ]] || fail "WRF run directory is not prepared: $WRF_RUN"',
            'require_executable "$WRF_RUN/real.exe"',
            'require_executable "$WRF_RUN/wrf.exe"',
            'require_file "$WRF_RUN/namelist.input"',
            'require_glob "$WRF_RUN/met_em.d0*.nc"',
            "",
            'mkdir -p "$DEBUG_DIR"',
            "printf \"phase\\tstart_utc\\tend_utc\\telapsed_seconds\\texit_code\\n\" > \"$PHASE_LOG\"",
            "trap finalize_debug EXIT",
            "",
            "module purge",
            "module load intel-oneapi-compilers/2021.4.0",
            "module load intel-oneapi-mpi/2021.1.1",
            "module load hdf5/1.14.3",
            "module load netcdf-c/4.9.2",
            "module load netcdf-fortran/4.6.1",
            "",
            "export NETCDF=$(nf-config --prefix)",
            "export NETCDF_C=$(nc-config --prefix)",
            "export JASPERLIB=/usr/lib64",
            "export JASPERINC=/usr/include/jasper",
            "",
            'cd "$WRF_RUN"',
            "write_summary_preamble",
            "",
            "run_phase real.exe ./real.exe",
            'run_phase real_success_marker grep -q "SUCCESS COMPLETE REAL_EM INIT" rsl.out.0000',
            "mv rsl.out.0000 real.rsl.out.0000",
            "mv rsl.error.0000 real.rsl.error.0000",
            "write_inventory",
            "",
            f"run_phase wrf.exe {mpi_launcher} -n \"$SLURM_NTASKS\" ./wrf.exe",
            'run_phase wrf_success_marker grep -q "SUCCESS COMPLETE WRF" rsl.out.0000',
            "write_inventory",
            "",
            'mkdir -p "$ARCHIVE_DIR"',
            'run_phase archive_wrfout rsync -av ./wrfout_d0* "$ARCHIVE_DIR/"',
            "run_phase archive_logs rsync -av namelist.input rsl.out.0000 rsl.error.0000 \\",
            '  real.rsl.out.0000 real.rsl.error.0000 "$ARCHIVE_DIR/"',
            "",
            'printf "case=%s archive=%s\\n" "$CASE_NAME" "$ARCHIVE_DIR"',
        ]
    )
    return "\n".join(lines) + "\n"


def safe_name(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_") or "item"


def parse_csv_ints(raw: str) -> list[int]:
    values: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        value = int(item)
        if value <= 0:
            raise ValueError(f"task counts must be positive: {raw}")
        values.append(value)
    if not values:
        raise ValueError("at least one task count is required")
    return values


def parse_csv_strings(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def practical_variant(
    data: dict[str, Any],
    *,
    scenario: str,
    job_suffix: str,
    ntasks: int | None = None,
    memory: str | None = None,
) -> dict[str, Any]:
    variant = copy.deepcopy(data)
    slurm = variant["slurm"]
    paths = variant["paths"]
    archive_root = as_path(paths["archive_root"])
    run_root = as_path(paths["run_root"])

    slurm["profile"] = "gate11_practical_review"
    slurm["job_name"] = f"{slurm['job_name']}_{job_suffix}"
    if ntasks is not None:
        slurm["ntasks"] = ntasks
    if memory is not None:
        slurm["memory"] = memory

    scenario_name = safe_name(scenario)
    paths["wrf_run"] = str(run_root / "practical_tests" / scenario_name / "wrf_run")
    paths["archive_root"] = str(archive_root / "practical_tests" / scenario_name)
    return variant


def render_practical_packet(
    data: dict[str, Any],
    case_file: Path,
    *,
    output_dir: Path,
    tasks: list[int],
    memory_candidates: list[str],
    scripts: list[tuple[str, str]],
) -> str:
    case = data["case"]
    forcing = data["forcing"]
    paths = data["paths"]
    slurm = data["slurm"]
    case_name = str(case["name"])

    lines = [
        f"# Gate 11 Practical-Test Harness: {case_name}",
        "",
        "Rendered from the tracked case manifest. This packet is review-only; it",
        "does not submit Slurm, run WPS, run `real.exe`, run `wrf.exe`, read",
        "NetCDF/archive artifacts, hash staged inputs, or render quicklooks.",
        "",
        "## Case Contract",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Case file | `{case_file}` |",
        f"| Render output | `{output_dir}` |",
        f"| Window | `{case['start']}` to `{case['end']}` |",
        f"| Domains | `{case['domains']}` |",
        f"| Forcing | `{text_value(forcing['sources'])}` |",
        f"| WPS cadence | `{forcing['interval_seconds']}` seconds |",
        f"| WPS fg_name | `{text_value(forcing['wps_fg_name'])}` |",
        f"| Manifest | `{forcing['manifest_path']}` |",
        f"| Contract | `{forcing['contract_path']}` |",
        f"| WRF source | `{paths['wrf_src']}` |",
        f"| WPS root | `{paths['wps_root']}` |",
        f"| Scratch run root | `{paths['run_root']}` |",
        f"| Archive root | `{paths['archive_root']}` |",
        f"| Default Slurm | `{slurm['account']}` / `{slurm['partition']}`, `{slurm.get('nodelist', 'any')}`, `{slurm['nodes']}` node, `{slurm['ntasks']}` tasks, `{slurm['memory']}` |",
        f"| Launcher | `{slurm['mpi_launcher']}` |",
        "",
        "## Rendered Scripts",
        "",
        "| Script | Scenario | Approval boundary |",
        "| --- | --- | --- |",
    ]
    for script, scenario in scripts:
        lines.append(
            f"| `{script}` | {scenario} | Human approval before `sbatch`; run only in approved Slurm/compute context. |"
        )

    lines.extend(
        [
            "",
            "Each script preserves the maintained wrapper behavior from",
            "`brc-cases/wrf_case.py render-slurm`: settings readback, module",
            "record, phase timings, file inventory, `real.exe` and `wrf.exe`",
            "success-marker checks, colon-safe `wrfout` archive copy, and debug",
            "archive under `debug/`.",
            "",
            "The scaling variants use per-scenario scratch and archive roots under",
            "`practical_tests/<scenario>/` so benchmark results do not collide",
            "with the proof archive or with each other.",
            "",
            "Before approved submission, each per-scenario `WRF_RUN` must be",
            "prepared with `real.exe`, `wrf.exe`, `namelist.input`, and `met_em`",
            "files. The rendered scripts fail fast if those inputs are missing.",
            "",
            "## Login-Safe Checks",
            "",
            "Run these before requesting approval. They are metadata/render checks",
            "only when `--strict-files` is omitted.",
            "",
            "```bash",
            f"python brc-cases/wrf_case.py validate {case_file}",
            f"python brc-cases/wrf_case.py render-practical-harness {case_file} --output-dir {shell_quote(output_dir)}",
            f"bash -n {shell_quote(output_dir)}/*.slurm",
            "```",
            "",
            "## Off-Login Checks",
            "",
            "Use only inside an approved batch, DTN, or interactive compute context",
            "when the command reads staged inputs, manifests, WPS/WRF files,",
            "NetCDF, archives, or quicklook outputs.",
            "",
            "```bash",
            f"python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest {forcing['manifest_path']}",
            f"python brc-cases/wrf_case.py validate {case_file} --strict-files",
            f"python brc-cases/wrf_quicklook.py check {case_file}",
            f"python brc-cases/wrf_quicklook.py render {case_file}",
            "```",
            "",
            "## Scaling Result Table",
            "",
            "| Tasks | Memory request | Job ID | Wall time | Sim hours | Wall time per sim hour | WRF marker | Archive path | Recommendation |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for task_count in tasks:
        memory = str(slurm["memory"])
        lines.append(f"| {task_count} | `{memory}` | TBD | TBD | TBD | TBD | TBD | TBD | TBD |")

    lines.extend(
        [
            "",
            "## Memory Result Table",
            "",
            "| Run | Memory request | Job ID | Peak memory evidence | WRF marker | Archive path | Recommendation |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
            f"| Baseline | `{slurm['memory']}` | TBD | TBD | TBD | TBD | TBD |",
        ]
    )
    if memory_candidates:
        for memory in memory_candidates:
            lines.append(f"| Candidate | `{memory}` | TBD | TBD | TBD | TBD | TBD |")
    else:
        lines.append("| Candidate | TBD | TBD | TBD | TBD | TBD | TBD |")

    lines.extend(
        [
            "",
            "## Closeout Record",
            "",
            "| Field | Value |",
            "| --- | --- |",
            "| Gate/item | Gate 11 practical-test harness or approved benchmark row |",
            "| Commands run | Exact render/check commands and any approved `sbatch` |",
            "| Host/context | Login render, DTN, interactive compute, or Slurm job ID |",
            "| Approval status | Who approved WPS/WRF/Slurm, or `not approved/not run` |",
            "| Evidence paths | Render packet, Slurm logs, manifest, contract, archive, quicklooks |",
            "| Owner repo | `brc-wrf` for wrapper/run; `brc-tools` for staging; `brc-knowledge` for CHPC truth |",
            "| Result | Passed, failed, parked, or not run |",
            "| What was not run | Explicit skipped compute/artifact reads |",
            "| Dirty state | `git status --short --branch --untracked-files=all` |",
            "| Commit/push status | SHA and remote branch when applicable |",
            "| Next suggested item | Next approval row or design task |",
            "",
            "Do not treat a successful render as approval to submit. Practical",
            "benchmark `sbatch`, WPS, `real.exe`, `wrf.exe`, strict artifact reads,",
            "and quicklooks remain approval-gated.",
            "",
        ]
    )
    return "\n".join(lines)


def print_findings(findings: list[Finding]) -> None:
    if not findings:
        print("OK: no findings")
        return
    for finding in findings:
        print(f"{finding.severity}: {finding.message}")


def cmd_validate(args: argparse.Namespace) -> int:
    case_file = Path(args.case_file)
    data = load_case(case_file)
    findings = validate_case(data, strict_files=args.strict_files)
    print_findings(findings)
    return 1 if any(f.severity == "ERROR" for f in findings) else 0


def cmd_render_slurm(args: argparse.Namespace) -> int:
    case_file = Path(args.case_file)
    data = load_case(case_file)
    findings = validate_case(data, strict_files=False)
    errors = [f for f in findings if f.severity == "ERROR"]
    if errors:
        print_findings(errors)
        return 1
    text = render_slurm(data, case_file)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


def cmd_render_practical_harness(args: argparse.Namespace) -> int:
    case_file = Path(args.case_file)
    output_dir = Path(args.output_dir)
    data = load_case(case_file)
    findings = validate_case(data, strict_files=False)
    errors = [f for f in findings if f.severity == "ERROR"]
    if errors:
        print_findings(errors)
        return 1

    repo_root = as_path(data["paths"]["wrf_src"])
    if path_under(output_dir, repo_root):
        print(
            "ERROR: practical harness output must stay outside the brc-wrf checkout: "
            f"{output_dir}",
            file=sys.stderr,
        )
        return 1

    tasks = parse_csv_ints(args.tasks)
    memory_candidates = parse_csv_strings(args.memory_candidates)
    output_dir.mkdir(parents=True, exist_ok=True)

    scripts: list[tuple[str, str]] = []
    baseline = practical_variant(
        data,
        scenario="baseline",
        job_suffix="baseline",
    )
    baseline_name = "baseline.slurm"
    (output_dir / baseline_name).write_text(render_slurm(baseline, case_file), encoding="utf-8")
    scripts.append((baseline_name, "baseline current case profile"))

    for task_count in tasks:
        scenario = f"scaling_t{task_count:03d}"
        script_name = f"{scenario}.slurm"
        variant = practical_variant(
            data,
            scenario=scenario,
            job_suffix=f"t{task_count:03d}",
            ntasks=task_count,
        )
        (output_dir / script_name).write_text(render_slurm(variant, case_file), encoding="utf-8")
        scripts.append((script_name, f"scaling candidate: {task_count} tasks"))

    for memory in memory_candidates:
        scenario = f"memory_{safe_name(memory)}"
        script_name = f"{scenario}.slurm"
        variant = practical_variant(
            data,
            scenario=scenario,
            job_suffix=f"mem{safe_name(memory)}",
            memory=memory,
        )
        (output_dir / script_name).write_text(render_slurm(variant, case_file), encoding="utf-8")
        scripts.append((script_name, f"memory candidate: {memory}"))

    packet = render_practical_packet(
        data,
        case_file,
        output_dir=output_dir,
        tasks=tasks,
        memory_candidates=memory_candidates,
        scripts=scripts,
    )
    packet_name = "README.md"
    (output_dir / packet_name).write_text(packet, encoding="utf-8")
    print(f"Wrote Gate 11 practical-test harness packet: {output_dir}")
    for name, _scenario in scripts:
        print(f"  {output_dir / name}")
    print(f"  {output_dir / packet_name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and render BRC WRF case manifests without running WRF."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="check a case manifest")
    validate.add_argument("case_file")
    validate.add_argument(
        "--strict-files",
        action="store_true",
        help="treat missing external files/directories as errors",
    )
    validate.set_defaults(func=cmd_validate)

    render = subparsers.add_parser(
        "render-slurm",
        help="render a Slurm script to stdout or --output; never submits",
    )
    render.add_argument("case_file")
    render.add_argument("--output", help="write rendered script to this path")
    render.set_defaults(func=cmd_render_slurm)

    practical = subparsers.add_parser(
        "render-practical-harness",
        help="render a Gate 11 review packet and benchmark Slurm scripts; never submits",
    )
    practical.add_argument("case_file")
    practical.add_argument(
        "--output-dir",
        required=True,
        help="write the packet outside the brc-wrf checkout, for example under /tmp",
    )
    practical.add_argument(
        "--tasks",
        default=",".join(str(value) for value in DEFAULT_PRACTICAL_TASKS),
        help="comma-separated scaling task counts to render",
    )
    practical.add_argument(
        "--memory-candidates",
        help="optional comma-separated memory requests to render as candidate scripts",
    )
    practical.set_defaults(func=cmd_render_practical_harness)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
