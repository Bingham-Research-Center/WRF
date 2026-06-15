#!/usr/bin/env python3
"""Validate and render BRC WRF case manifests without running WRF.

This is deliberately small and dependency-free. It accepts only the constrained
case-YAML subset documented in ``brc-cases/README.md``.
"""

from __future__ import annotations

import argparse
import ast
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
    add_path_finding(
        findings, as_path(paths["geog_data_path"]), "paths.geog_data_path",
        strict_files=strict_files, must_be_dir=True,
    )
    for key in ("input_root", "run_root", "wps_run", "wrf_run", "archive_root"):
        add_path_finding(
            findings, as_path(paths[key]), f"paths.{key}",
            strict_files=strict_files, must_be_dir=True,
        )

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


def render_slurm(data: dict[str, Any], case_file: Path) -> str:
    case = data["case"]
    paths = data["paths"]
    slurm = data["slurm"]

    job_name = str(slurm["job_name"])
    archive_root = as_path(paths["archive_root"])
    wrf_run = as_path(paths["wrf_run"])
    mpi_launcher = str(slurm["mpi_launcher"])

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
            "",
            "./real.exe",
            'grep -q "SUCCESS COMPLETE REAL_EM INIT" rsl.out.0000',
            "mv rsl.out.0000 real.rsl.out.0000",
            "mv rsl.error.0000 real.rsl.error.0000",
            "",
            f"{mpi_launcher} -n \"$SLURM_NTASKS\" ./wrf.exe",
            'grep -q "SUCCESS COMPLETE WRF" rsl.out.0000',
            "",
            'mkdir -p "$ARCHIVE_DIR"',
            'rsync -av ./wrfout_d0* "$ARCHIVE_DIR/"',
            "rsync -av namelist.input rsl.out.0000 rsl.error.0000 \\",
            '  real.rsl.out.0000 real.rsl.error.0000 "$ARCHIVE_DIR/"',
            "",
            'printf "case=%s archive=%s\\n" "$CASE_NAME" "$ARCHIVE_DIR"',
        ]
    )
    return "\n".join(lines) + "\n"


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
