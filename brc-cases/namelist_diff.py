#!/usr/bin/env python3
"""Compare archived WRF namelist.input files without reading model output."""

from __future__ import annotations

import argparse
import difflib
import itertools
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_ROOT = Path(
    "/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/"
    "namelist_diff_reports"
)

IMPORTANT_KEYS = [
    ("time_control", "run_days"),
    ("time_control", "run_hours"),
    ("time_control", "start_year"),
    ("time_control", "start_month"),
    ("time_control", "start_day"),
    ("time_control", "start_hour"),
    ("time_control", "end_year"),
    ("time_control", "end_month"),
    ("time_control", "end_day"),
    ("time_control", "end_hour"),
    ("time_control", "interval_seconds"),
    ("time_control", "history_interval"),
    ("domains", "time_step"),
    ("domains", "max_dom"),
    ("domains", "e_we"),
    ("domains", "e_sn"),
    ("domains", "e_vert"),
    ("domains", "dx"),
    ("domains", "dy"),
    ("domains", "parent_grid_ratio"),
    ("domains", "parent_time_step_ratio"),
    ("domains", "feedback"),
    ("domains", "smooth_option"),
    ("domains", "use_adaptive_time_step"),
    ("domains", "target_cfl"),
    ("domains", "num_metgrid_levels"),
    ("domains", "num_metgrid_soil_levels"),
    ("domains", "p_top_requested"),
    ("physics", "mp_physics"),
    ("physics", "ra_lw_physics"),
    ("physics", "ra_sw_physics"),
    ("physics", "radt"),
    ("physics", "sf_sfclay_physics"),
    ("physics", "sf_surface_physics"),
    ("physics", "bl_pbl_physics"),
    ("physics", "bldt"),
    ("physics", "cu_physics"),
    ("physics", "cudt"),
    ("physics", "slope_rad"),
    ("physics", "topo_shading"),
    ("physics", "shadlen"),
    ("physics", "num_soil_layers"),
    ("physics", "num_land_cat"),
    ("dynamics", "hybrid_opt"),
    ("dynamics", "w_damping"),
    ("dynamics", "diff_opt"),
    ("dynamics", "km_opt"),
    ("dynamics", "diff_6th_opt"),
    ("dynamics", "diff_6th_factor"),
    ("dynamics", "damp_opt"),
    ("dynamics", "zdamp"),
    ("dynamics", "dampcoef"),
]


@dataclass(frozen=True)
class NamelistCase:
    label: str
    path: Path
    text: str
    values: dict[tuple[str, str], tuple[str, ...]]


def utc_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def path_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def require_outside_repo(path: Path) -> None:
    if path_under(path, REPO_ROOT):
        raise ValueError(f"output directory must stay outside the brc-wrf checkout: {path}")


def safe_label(value: str) -> str:
    label = re.sub(r"[^A-Za-z0-9._+-]+", "_", value.strip()).strip("._-")
    if not label:
        raise ValueError("case label must contain at least one safe filename character")
    return label


def strip_inline_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    out: list[str] = []
    for char in line:
        if quote:
            out.append(char)
            if char == quote and not escaped:
                quote = None
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
            continue
        if char in ("'", '"'):
            quote = char
            out.append(char)
            continue
        if char == "!":
            break
        out.append(char)
    return "".join(out).rstrip()


def split_fortran_values(raw: str) -> tuple[str, ...]:
    values: list[str] = []
    quote: str | None = None
    current: list[str] = []
    for char in raw:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
            continue
        if char == ",":
            token = normalize_value("".join(current))
            if token:
                values.append(token)
            current = []
            continue
        current.append(char)
    token = normalize_value("".join(current))
    if token:
        values.append(token)
    return tuple(values)


def normalize_value(raw: str) -> str:
    value = raw.strip().strip(",")
    if not value:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    if value.lower() in {".true.", ".false.", "true", "false"}:
        return value.lower()
    return re.sub(r"\s+", " ", value)


def parse_namelist_text(text: str) -> dict[tuple[str, str], tuple[str, ...]]:
    values: dict[tuple[str, str], tuple[str, ...]] = {}
    section: str | None = None
    pending_key: str | None = None
    pending_value: list[str] = []

    def flush_pending() -> None:
        nonlocal pending_key, pending_value
        if section and pending_key:
            joined = " ".join(part for part in pending_value if part.strip())
            values[(section, pending_key)] = split_fortran_values(joined)
        pending_key = None
        pending_value = []

    for raw_line in text.splitlines():
        line = strip_inline_comment(raw_line)
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("&"):
            flush_pending()
            section = stripped[1:].split()[0].lower()
            continue
        if stripped == "/" or stripped.startswith("/"):
            flush_pending()
            section = None
            continue
        if section is None:
            continue
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if match:
            flush_pending()
            pending_key = match.group(1).lower()
            pending_value = [match.group(2).strip()]
        elif pending_key:
            pending_value.append(stripped)
    flush_pending()
    return values


def resolve_namelist_path(path: Path) -> Path:
    if path.is_dir():
        candidate = path / "namelist.input"
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"directory does not contain namelist.input: {path}")
    if path.exists():
        return path
    raise FileNotFoundError(f"namelist path does not exist: {path}")


def load_case(label: str, path: Path) -> NamelistCase:
    actual = resolve_namelist_path(path)
    text = actual.read_text(encoding="utf-8", errors="replace")
    return NamelistCase(
        label=safe_label(label),
        path=actual,
        text=text,
        values=parse_namelist_text(text),
    )


def parse_case_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError(f"--case must be LABEL=PATH, got: {raw}")
    label, path = raw.split("=", 1)
    label = safe_label(label)
    if not path.strip():
        raise ValueError(f"--case {label} has an empty path")
    return label, Path(path).expanduser()


def format_value(values: tuple[str, ...] | None, *, limit: int = 120) -> str:
    if values is None:
        return "(missing)"
    text = ", ".join(values)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def all_keys(cases: list[NamelistCase]) -> list[tuple[str, str]]:
    keys = set().union(*(case.values.keys() for case in cases))
    important = [key for key in IMPORTANT_KEYS if key in keys]
    remaining = sorted(keys.difference(important))
    return important + remaining


def changed_keys(cases: list[NamelistCase]) -> list[tuple[str, str]]:
    changed: list[tuple[str, str]] = []
    for key in all_keys(cases):
        variants = {case.values.get(key) for case in cases}
        if len(variants) > 1:
            changed.append(key)
    return changed


def write_matrix(cases: list[NamelistCase], output_dir: Path) -> Path:
    path = output_dir / "namelist_diff_matrix.tsv"
    labels = [case.label for case in cases]
    lines = ["section\tkey\tchanged\t" + "\t".join(labels)]
    for section, key in all_keys(cases):
        variants = {case.values.get((section, key)) for case in cases}
        row = [
            section,
            key,
            "yes" if len(variants) > 1 else "no",
            *[format_value(case.values.get((section, key)), limit=10000) for case in cases],
        ]
        lines.append("\t".join(cell.replace("\t", " ") for cell in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_pair_diffs(cases: list[NamelistCase], output_dir: Path) -> list[Path]:
    diff_paths: list[Path] = []
    for left, right in itertools.combinations(cases, 2):
        diff_lines = list(
            difflib.unified_diff(
                left.text.splitlines(),
                right.text.splitlines(),
                fromfile=f"{left.label}: {left.path}",
                tofile=f"{right.label}: {right.path}",
            )
        )
        diff_text = "\n".join(diff_lines) + "\n" if diff_lines else "(no raw text differences)\n"
        path = output_dir / f"{left.label}__vs__{right.label}.diff"
        path.write_text(diff_text, encoding="utf-8")
        diff_paths.append(path)
    return diff_paths


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        escaped = [cell.replace("|", "\\|").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(escaped) + " |")
    return lines


def write_summary(cases: list[NamelistCase], diff_paths: list[Path], output_dir: Path) -> Path:
    changed = changed_keys(cases)
    important_changed = [key for key in IMPORTANT_KEYS if key in changed]
    other_changed = [key for key in changed if key not in important_changed]

    lines = [
        "# WRF namelist.input Diff Summary",
        "",
        f"Generated UTC: `{utc_id()}`",
        "",
        "This report compares existing text namelist artifacts only. It does not run WPS, "
        "WRF, Slurm, NetCDF reads, quicklooks, or archive promotion.",
        "",
        "## Cases",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Label", "Path"],
            [[case.label, str(case.path)] for case in cases],
        )
    )
    lines.extend(["", "## High-Signal Differences", ""])
    if important_changed:
        rows = []
        for section, key in important_changed:
            rows.append(
                [
                    f"{section}.{key}",
                    *[format_value(case.values.get((section, key))) for case in cases],
                ]
            )
        lines.extend(markdown_table(["Setting", *[case.label for case in cases]], rows))
    else:
        lines.append("No high-signal setting differences were found.")

    lines.extend(["", "## Other Changed Settings", ""])
    if other_changed:
        rows = []
        for section, key in other_changed:
            rows.append(
                [
                    f"{section}.{key}",
                    *[format_value(case.values.get((section, key))) for case in cases],
                ]
            )
        lines.extend(markdown_table(["Setting", *[case.label for case in cases]], rows))
    else:
        lines.append("No other normalized setting differences were found.")

    lines.extend(["", "## Raw Unified Diffs", ""])
    for path in diff_paths:
        lines.append(f"- `{path.name}`")
    lines.extend(["", "## Matrix", "", "- `namelist_diff_matrix.tsv`"])

    path = output_dir / "namelist_diff_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_report(cases: list[NamelistCase], output_dir: Path) -> tuple[Path, Path, list[Path]]:
    if len(cases) < 2:
        raise ValueError("at least two --case entries are required")
    require_outside_repo(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    matrix = write_matrix(cases, output_dir)
    diff_paths = write_pair_diffs(cases, output_dir)
    summary = write_summary(cases, diff_paths, output_dir)
    return summary, matrix, diff_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare existing WRF namelist.input text files and write a report."
    )
    parser.add_argument(
        "--case",
        action="append",
        required=True,
        metavar="LABEL=PATH",
        help="comparison input; PATH may be namelist.input or a directory containing it",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_REPORT_ROOT / utc_id(),
        help="report directory; must be outside this checkout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        cases = [load_case(label, path) for label, path in map(parse_case_arg, args.case)]
        labels = [case.label for case in cases]
        if len(labels) != len(set(labels)):
            raise ValueError("case labels must be unique")
        summary, matrix, diff_paths = write_report(cases, args.output_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"summary: {summary}")
    print(f"matrix: {matrix}")
    print(f"raw diffs: {len(diff_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
