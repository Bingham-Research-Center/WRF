#!/usr/bin/env python3
"""Render approval-gated WRF physics-treatment packets without running WRF."""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import namelist_diff
import wrf_case


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ID_RE = re.compile(r"^run_[0-9]{8}T[0-9]{6}Z$")
SET_PREFIX = "set."
RENDER_ENV = "BRC_TREATMENT_WRF_APPROVED"
PREP_ENV = "BRC_TREATMENT_PREP_APPROVED"
QUICKLOOK_ENV = "BRC_TREATMENT_QUICKLOOK_APPROVED"
QUICKLOOK_PYTHON = Path(
    "/uufs/chpc.utah.edu/common/home/u0737349/software/pkg/miniforge3/"
    "envs/clyfar-nov2025/bin/python"
)
BRC_TOOLS = Path("/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-tools")
LOG_ROOT = Path(
    "/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/"
    "wrf_build_logs/brc-wrf"
)


def utc_run_id() -> str:
    return time.strftime("run_%Y%m%dT%H%M%SZ", time.gmtime())


def shell_quote(value: Any) -> str:
    return wrf_case.shell_quote(value)


def treatment_changes(data: dict[str, Any]) -> dict[tuple[str, str], tuple[str, ...]]:
    treatment = data.get("treatment")
    if not isinstance(treatment, dict):
        raise ValueError("case manifest requires a treatment section")
    changes: dict[tuple[str, str], tuple[str, ...]] = {}
    for raw_key, raw_value in treatment.items():
        if not raw_key.startswith(SET_PREFIX):
            continue
        dotted = raw_key[len(SET_PREFIX) :]
        if dotted.count(".") != 1:
            raise ValueError(f"treatment key must be set.SECTION.KEY: {raw_key}")
        section, key = (part.strip().lower() for part in dotted.split(".", 1))
        values = tuple(str(value).strip() for value in wrf_case.as_list(raw_value))
        if not section or not key or not values or any(not value for value in values):
            raise ValueError(f"invalid treatment assignment: {raw_key}={raw_value!r}")
        changes[(section, key)] = values
    if not changes:
        raise ValueError("treatment section has no set.SECTION.KEY assignments")
    return changes


def _section_bounds(lines: list[str], section: str) -> tuple[int, int]:
    start = None
    for index, line in enumerate(lines):
        match = re.match(r"^\s*&([A-Za-z][A-Za-z0-9_]*)\b", line)
        if match and match.group(1).lower() == section:
            start = index
            break
    if start is None:
        raise ValueError(f"namelist section not found: {section}")
    for index in range(start + 1, len(lines)):
        if re.match(r"^\s*/", lines[index]):
            return start, index
    raise ValueError(f"namelist section is not terminated: {section}")


def _replace_assignment(
    lines: list[str], section: str, key: str, values: tuple[str, ...]
) -> None:
    start, end = _section_bounds(lines, section)
    assignment = re.compile(rf"^\s*{re.escape(key)}\s*=", re.IGNORECASE)
    starts = [index for index in range(start + 1, end) if assignment.match(lines[index])]
    if len(starts) > 1:
        raise ValueError(f"duplicate namelist assignment: {section}.{key}")
    rendered = f"{key:<25} = {', '.join(values)},"
    if not starts:
        lines.insert(end, rendered)
        return

    first = starts[0]
    last = first + 1
    next_assignment = re.compile(r"^\s*[A-Za-z][A-Za-z0-9_]*\s*=")
    while last < end and not next_assignment.match(lines[last]):
        if re.match(r"^\s*/", lines[last]):
            break
        last += 1
    lines[first:last] = [rendered]


def patch_namelist(
    original: str, changes: dict[tuple[str, str], tuple[str, ...]]
) -> str:
    lines = original.splitlines()
    for (section, key), values in changes.items():
        _replace_assignment(lines, section, key, values)
    updated = "\n".join(lines) + "\n"

    before = namelist_diff.parse_namelist_text(original)
    after = namelist_diff.parse_namelist_text(updated)
    actual_changed = {
        key for key in set(before) | set(after) if before.get(key) != after.get(key)
    }
    expected_changed = set(changes)
    if actual_changed != expected_changed:
        raise ValueError(
            "namelist patch changed an unexpected key set: "
            f"expected={sorted(expected_changed)} actual={sorted(actual_changed)}"
        )
    for key, expected in changes.items():
        actual = after.get(key)
        normalized_expected = tuple(namelist_diff.normalize_value(value) for value in expected)
        if actual != normalized_expected:
            raise ValueError(f"namelist patch verification failed for {key}: {actual}")
    return updated


def yaml_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value)


def dump_case(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {yaml_value(child_value)}")
        else:
            lines.append(f"{key}: {yaml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _inject_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one {label} insertion point, found {count}")
    return text.replace(old, new, 1)


def render_run_script(
    data: dict[str, Any], generated_case: Path, *, run_id: str, archive_run: Path
) -> str:
    script = wrf_case.render_slurm(data, generated_case)
    script = _inject_once(
        script,
        "set -euo pipefail\n",
        "set -euo pipefail\n\n"
        f'[[ "${{{RENDER_ENV}:-NO}}" == "YES" ]] || '
        f'{{ echo "set {RENDER_ENV}=YES only after treatment preparation approval" >&2; exit 2; }}\n',
        "WRF approval guard",
    )
    archive_assignment = 'ARCHIVE_DIR="${ARCHIVE_ROOT}/run_$(date -u +%Y%m%dT%H%M%SZ)"'
    script = _inject_once(
        script,
        archive_assignment,
        f"ARCHIVE_DIR={shell_quote(archive_run)}",
        "fixed archive path",
    )
    marker = 'run_phase wrf_success_marker grep -q "SUCCESS COMPLETE WRF" rsl.out.0000\n'
    script = _inject_once(
        script,
        marker,
        marker
        + "grep -Ein 'fatal|segmentation fault|floating invalid|cfl|nan' rsl.out.* rsl.error.* "
        + '> "$DEBUG_DIR/wrf_error_marker_scan.txt" || true\n',
        "WRF marker scan",
    )
    final_archive = (
        'run_phase archive_logs rsync -av namelist.input rsl.out.0000 rsl.error.0000 \\\n'
        '  real.rsl.out.0000 real.rsl.error.0000 "$ARCHIVE_DIR/"\n'
    )
    replacement = final_archive + (
        'run_phase archive_real_outputs rsync -av wrfinput_d0* wrfbdy_d01 "$ARCHIVE_DIR/"\n'
        'wrfout_count=$(find "$ARCHIVE_DIR" -maxdepth 1 -type f -name "wrfout_d0*" | wc -l)\n'
        '[[ "$wrfout_count" -eq 21 ]] || fail "expected 21 archived wrfout files, found $wrfout_count"\n'
    )
    script = _inject_once(script, final_archive, replacement, "real-output archive")
    return script


def render_prepare_script(
    data: dict[str, Any], generated_case: Path, namelist_path: Path, *, run_id: str
) -> str:
    treatment = data["treatment"]
    paths = data["paths"]
    wrf_build = wrf_case.as_path(paths["wrf_build"])
    wrf_run = wrf_case.as_path(paths["wrf_run"])
    source_wrf_run = wrf_case.as_path(treatment["source_wrf_run"])
    required_runtime = " ".join(wrf_case.REQUIRED_WRF_RUNTIME_FILES)
    return f"""#!/bin/bash
# Approved batch or interactive compute context only. Does not submit Slurm or run WRF.
set -euo pipefail

[[ "${{{PREP_ENV}:-NO}}" == "YES" ]] || {{ echo "set {PREP_ENV}=YES only in an approved off-login context" >&2; exit 2; }}
CASE_FILE={shell_quote(generated_case)}
RUN_ID={shell_quote(run_id)}
WRF_BUILD={shell_quote(wrf_build)}
SOURCE_WRF_RUN={shell_quote(source_wrf_run)}
WRF_RUN={shell_quote(wrf_run)}
NAMELIST={shell_quote(namelist_path)}

case "$SOURCE_WRF_RUN" in *"/u6060939/"*) echo "refusing Michael-owned source path" >&2; exit 2 ;; esac
[[ "$WRF_RUN/" != "$WRF_BUILD/"* ]] || {{ echo "WRF_RUN must stay outside the checkout" >&2; exit 2; }}
test -x "$WRF_BUILD/main/real.exe"
test -x "$WRF_BUILD/main/wrf.exe"
test -f "$NAMELIST"
test -d "$SOURCE_WRF_RUN"
met_count=$(find -L "$SOURCE_WRF_RUN" -maxdepth 1 -type f -name 'met_em.d0*.nc' | wc -l)
[[ "$met_count" -eq 6 ]] || {{ echo "expected 6 source met_em files, found $met_count" >&2; exit 2; }}
for runtime_file in {required_runtime}; do test -f "$WRF_BUILD/run/$runtime_file"; done

mkdir -p "$WRF_RUN"
rsync -a "$WRF_BUILD/main/real.exe" "$WRF_RUN/"
rsync -a "$WRF_BUILD/main/wrf.exe" "$WRF_RUN/"
rsync -a --exclude='*.exe' "$WRF_BUILD/run/" "$WRF_RUN/"
rsync -aL "$SOURCE_WRF_RUN"/met_em.d0*.nc "$WRF_RUN/"
rsync -a "$NAMELIST" "$WRF_RUN/namelist.input"

cmp -s "$WRF_BUILD/main/real.exe" "$WRF_RUN/real.exe"
cmp -s "$WRF_BUILD/main/wrf.exe" "$WRF_RUN/wrf.exe"
cmp -s "$NAMELIST" "$WRF_RUN/namelist.input"
prepared_met_count=$(find "$WRF_RUN" -maxdepth 1 -type f -name 'met_em.d0*.nc' | wc -l)
[[ "$prepared_met_count" -eq 6 ]] || {{ echo "expected 6 prepared met_em files, found $prepared_met_count" >&2; exit 2; }}
for runtime_file in {required_runtime}; do cmp -s "$WRF_BUILD/run/$runtime_file" "$WRF_RUN/$runtime_file"; done

{{
  printf 'key\tvalue\n'
  printf 'run_id\t%s\n' "$RUN_ID"
  printf 'case_file\t%s\n' "$CASE_FILE"
  printf 'source_wrf_run\t%s\n' "$SOURCE_WRF_RUN"
  printf 'wrf_run\t%s\n' "$WRF_RUN"
  printf 'met_em_count\t%s\n' "$prepared_met_count"
  printf 'namelist_sha256\t%s\n' "$(sha256sum "$WRF_RUN/namelist.input" | awk '{{print $1}}')"
  printf 'prepared_utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}} > "$WRF_RUN/brc_treatment_prepare_summary.tsv"
printf 'prepared treatment run at %s\n' "$WRF_RUN"
"""


def render_quicklook_script(
    data: dict[str, Any], generated_case: Path, output_dir: Path, archive_run: Path
) -> str:
    case_name = wrf_case.safe_name(data["case"]["name"])
    return f"""#!/bin/bash
# Review only. Submit after WRF/archive acceptance and explicit approval.
#SBATCH --job-name=ql_{case_name[-24:]}
#SBATCH --account=lawson-np
#SBATCH --partition=lawson-np
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --nodelist=notch392
#SBATCH --chdir={LOG_ROOT}
#SBATCH --output={LOG_ROOT}/quicklook_{case_name}_%j.out
#SBATCH --error={LOG_ROOT}/quicklook_{case_name}_%j.out

set -euo pipefail
[[ "${{{QUICKLOOK_ENV}:-NO}}" == "YES" ]] || {{ echo "set {QUICKLOOK_ENV}=YES only after WRF/archive proof" >&2; exit 2; }}
REPO={REPO_ROOT}
BRC_TOOLS={BRC_TOOLS}
PY={QUICKLOOK_PYTHON}
CASE_FILE={shell_quote(generated_case)}
ARCHIVE_RUN={shell_quote(archive_run)}
CONTROL={shell_quote(output_dir)}
export PYTHONPATH="${{BRC_TOOLS}}:${{PYTHONPATH:-}}"
export MPLCONFIGDIR=/tmp/brc-wrf-matplotlib-${{USER}}-${{SLURM_JOB_ID:-manual}}
export XDG_CACHE_HOME=/tmp/brc-wrf-cache-${{USER}}-${{SLURM_JOB_ID:-manual}}
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME/fontconfig"
cd "$REPO"
"$PY" brc-cases/wrf_quicklook.py check "$CASE_FILE" --archive-run "$ARCHIVE_RUN"
"$PY" brc-cases/wrf_quicklook.py render "$CASE_FILE" --archive-run "$ARCHIVE_RUN"
"$PY" brc-cases/wrf_quicklook.py render-supplemental "$CASE_FILE" --archive-run "$ARCHIVE_RUN"
"$PY" brc-cases/wrf_quicklook.py render-surface-energy "$CASE_FILE" --archive-run "$ARCHIVE_RUN"
summary="$CONTROL/quicklook_summary_${{SLURM_JOB_ID:-manual}}.tsv"
find "$ARCHIVE_RUN/quicklooks" -type f -name '*.png' -printf '%P\t%s bytes\n' | sort | tee "$summary"
count=$(wc -l < "$summary")
[[ "$count" -eq 54 ]] || {{ echo "expected 54 quicklook PNGs, found $count" >&2; exit 3; }}
printf 'quicklook_count=%s summary=%s\n' "$count" "$summary"
"""


def render_readme(
    data: dict[str, Any], source_case: Path, output_dir: Path, run_id: str, archive_run: Path
) -> str:
    treatment = data["treatment"]
    changes = treatment_changes(data)
    rows = [
        f"| `{section}.{key}` | `{', '.join(values)}` |"
        for (section, key), values in changes.items()
    ]
    return "\n".join(
        [
            f"# WRF Treatment Control: {data['case']['name']}",
            "",
            "This is a render-only, approval-gated control packet. It reuses the accepted",
            "comparison parent's meteorological inputs and does not run WPS.",
            "",
            f"- source manifest: `{source_case}`",
            f"- run id: `{run_id}`",
            f"- comparison parent: `{treatment['comparison_parent']}`",
            f"- source WRF run: `{treatment['source_wrf_run']}`",
            f"- target archive: `{archive_run}`",
            "- FDDA: disabled (empty inherited `&fdda` block)",
            "",
            "## Intended Namelist Delta",
            "",
            "| Setting | Treatment value |",
            "| --- | --- |",
            *rows,
            "",
            "The normalized and raw control-to-treatment diffs are under `namelist_diff/`.",
            "No other normalized namelist key may change.",
            "",
            "## Approval Gates",
            "",
            "Preparation must run off-login in an approved batch or interactive context:",
            "",
            "```bash",
            f"{PREP_ENV}=YES {output_dir / 'prepare_treatment.sh'}",
            "```",
            "",
            "After preparation evidence is reviewed, submit WRF only with explicit approval:",
            "",
            "```bash",
            f"{RENDER_ENV}=YES sbatch {output_dir / 'run_wrf.slurm'}",
            "```",
            "",
            "After WRF success, 21-file archive proof, and error-scan review:",
            "",
            "```bash",
            f"{QUICKLOOK_ENV}=YES sbatch {output_dir / 'render_quicklooks.slurm'}",
            "```",
            "",
            "Do not infer multi-day cold-pool skill from this six-hour bridge run.",
            "",
        ]
    )


def render_packet(case_file: Path, output_dir: Path, run_id: str) -> list[Path]:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"run id must match {RUN_ID_RE.pattern}: {run_id}")
    data = wrf_case.load_case(case_file)
    findings = wrf_case.validate_case(data, strict_files=False)
    findings.extend(wrf_case.run_readiness_findings(data))
    errors = [finding for finding in findings if finding.severity == "ERROR"]
    if errors:
        wrf_case.print_findings(errors)
        raise ValueError("case manifest validation failed")
    wrf_case.require_outside_repo(output_dir, REPO_ROOT, "treatment packet output")

    treatment = data.get("treatment", {})
    required = ("baseline_namelist", "source_wrf_run", "comparison_parent")
    missing = [key for key in required if not treatment.get(key)]
    if missing:
        raise ValueError(f"treatment section missing: {', '.join(missing)}")
    baseline_path = wrf_case.as_path(treatment["baseline_namelist"])
    original = baseline_path.read_text(encoding="utf-8")
    updated = patch_namelist(original, treatment_changes(data))

    generated = copy.deepcopy(data)
    generated["paths"]["wrf_run"] = str(
        wrf_case.as_path(data["paths"]["run_root"]) / run_id / "wrf_run_full6h"
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    namelist_path = output_dir / "namelist.input"
    namelist_path.write_text(updated, encoding="utf-8")
    generated.setdefault("namelists", {})["namelist_input"] = str(namelist_path)
    generated_case = output_dir / f"{data['case']['name']}.case.yaml"
    generated_case.write_text(dump_case(generated), encoding="utf-8")

    archive_run = wrf_case.as_path(generated["paths"]["archive_root"]) / run_id
    prep = output_dir / "prepare_treatment.sh"
    run = output_dir / "run_wrf.slurm"
    quicklook = output_dir / "render_quicklooks.slurm"
    prep.write_text(
        render_prepare_script(generated, generated_case, namelist_path, run_id=run_id),
        encoding="utf-8",
    )
    run.write_text(
        render_run_script(generated, generated_case, run_id=run_id, archive_run=archive_run),
        encoding="utf-8",
    )
    quicklook.write_text(
        render_quicklook_script(generated, generated_case, output_dir, archive_run),
        encoding="utf-8",
    )
    prep.chmod(0o750)

    diff_dir = output_dir / "namelist_diff"
    namelist_diff.write_report(
        [
            namelist_diff.load_case(str(treatment["comparison_parent"]), baseline_path),
            namelist_diff.load_case(data["case"]["name"], namelist_path),
        ],
        diff_dir,
    )
    readme = output_dir / "README.md"
    readme.write_text(
        render_readme(generated, case_file, output_dir, run_id, archive_run),
        encoding="utf-8",
    )
    manifest = output_dir / "control_manifest.tsv"
    paths = [readme, generated_case, namelist_path, prep, run, quicklook, manifest]
    manifest.write_text(
        "path\trole\n"
        + "\n".join(
            [
                f"{readme}\treview and approval notes",
                f"{generated_case}\trendered treatment/quicklook case",
                f"{namelist_path}\tverified treatment namelist",
                f"{prep}\tapproval-gated off-login preparation",
                f"{run}\tapproval-gated real.exe/wrf.exe/archive job",
                f"{quicklook}\tapproval-gated standard and supplemental quicklooks",
                f"{diff_dir}\tcontrol-to-treatment namelist diff evidence",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    check = subprocess.run(
        ["bash", "-n", str(prep), str(run), str(quicklook)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check.returncode:
        raise ValueError(f"rendered shell syntax failed: {check.stderr.strip()}")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a no-run WRF physics-treatment packet outside the checkout."
    )
    parser.add_argument("case_file", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", default=utc_run_id())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = render_packet(args.case_file, args.output_dir, args.run_id)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote treatment packet: {args.output_dir}")
    for path in paths:
        print(f"  {path}")
    print("Stop point: rendered and syntax-checked; no files staged and no jobs submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
