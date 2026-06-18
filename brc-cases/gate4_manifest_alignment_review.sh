#!/usr/bin/env bash
# Gate 4: metadata-only case manifest root alignment review.
#
# This helper validates and renders the Jan-2013 case for review only. It does
# not use --strict-files, submit Slurm, run WPS, run real.exe, or run wrf.exe.

set -euo pipefail

CASE_FILE=${1:-brc-cases/jan2013_basin_nam.case.yaml}
STAMP=$(date -u '+%Y%m%dT%H%M%SZ')
REPORT=${BRC_GATE4_REPORT:-"/tmp/jan2013_basin_nam.gate4.${STAMP}.report.txt"}
RENDERED=${BRC_GATE4_RENDERED:-"/tmp/jan2013_basin_nam.gate4.${STAMP}.rendered.slurm"}

{
  echo "Gate/item: Roadmap Gate 4 - case manifest root alignment"
  echo "UTC: $(date -u '+%Y-%m-%d %H:%M:%S')"
  echo "Host: $(hostname)"
  echo "Case file: $CASE_FILE"
  echo "Report: $REPORT"
  echo "Rendered Slurm review: $RENDERED"
  echo
  echo "Validation:"
  python brc-cases/wrf_case.py validate "$CASE_FILE"
  echo
  echo "Rendered Slurm path:"
  python brc-cases/wrf_case.py render-slurm "$CASE_FILE" > "$RENDERED"
  echo "$RENDERED"
  echo
  echo "What was not run: strict file validation, sbatch, WPS, real.exe, wrf.exe, staging, NetCDF/archive reads, quicklooks."
} | tee "$REPORT"
