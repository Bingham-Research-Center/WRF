#!/bin/bash
# Gate 3: approved John-owned WPS proof.
#
# Submit only after explicit human approval for compile-scale Gate 3 work.
# This job configures/builds or verifies WPS only. It never runs geogrid.exe,
# ungrib.exe, metgrid.exe, real.exe, wrf.exe, staging, quicklooks, or NetCDF
# inspection.
#
# Fewest-click submit pattern:
#   BRC_GATE3_APPROVED=YES \
#   BRC_WPS_SOURCE=/path/to/WPS-source-or-WPS.tar.gz \
#   BRC_WPS_CONFIGURE_OPTION=<wps-configure-menu-number> \
#   sbatch brc-cases/gate3_wps_proof.slurm
#
# Verification-only pattern for an already built John-owned WPS root:
#   BRC_GATE3_APPROVED=YES BRC_GATE3_MODE=verify \
#   sbatch brc-cases/gate3_wps_proof.slurm

#SBATCH --job-name=brc_gate3_wps
#SBATCH --account=lawson-np
#SBATCH --partition=lawson-np
#SBATCH --nodelist=notch392
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate3_submit_%j.out
#SBATCH --error=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate3_submit_%j.err
#SBATCH --export=ALL

set -euo pipefail

fail() {
  echo "ERROR: $*" >&2
  exit 2
}

require_file() {
  local path=$1
  [[ -e "$path" ]] || fail "missing required Gate 3 file: $path"
}

copy_wps_source() {
  local source=$1
  local target=$2
  local extract_dir
  local top

  [[ ! -e "$target" ]] || fail "refusing to overwrite existing WPS root: $target"
  mkdir -p "$(dirname "$target")"

  if [[ -d "$source" ]]; then
    cp -a "$source" "$target"
    return
  fi

  [[ -f "$source" ]] || fail "BRC_WPS_SOURCE is neither a directory nor a tar file: $source"
  extract_dir=$(mktemp -d "${TMPDIR:-/tmp}/brc_gate3_wps.XXXXXX")
  tar -xf "$source" -C "$extract_dir"
  top=$(find "$extract_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)
  [[ -n "$top" ]] || fail "could not find top-level WPS directory after extracting $source"
  cp -a "$top" "$target"
}

record_inventory() {
  local evidence_dir=$1
  local wps_root=$2

  {
    echo "Gate 3 WPS executable inventory"
    echo "UTC: $(date -u '+%Y-%m-%d %H:%M:%S')"
    echo "WPS_ROOT=$wps_root"
    echo
    for path in \
      "$wps_root/geogrid.exe" \
      "$wps_root/ungrib.exe" \
      "$wps_root/metgrid.exe" \
      "$wps_root/link_grib.csh" \
      "$wps_root/ungrib/Variable_Tables/Vtable.NAM" \
      "$wps_root/configure.wps"; do
      if [[ -e "$path" ]]; then
        ls -lh --time-style=long-iso "$path"
        if [[ -L "$path" ]]; then
          printf '  symlink target: '
          readlink "$path"
        fi
      else
        echo "MISSING $path"
      fi
    done
  } > "$evidence_dir/executable_inventory.txt"
}

verify_gate3() {
  local evidence_dir=$1
  local wps_root=$2

  require_file "$wps_root/geogrid.exe"
  require_file "$wps_root/ungrib.exe"
  require_file "$wps_root/metgrid.exe"
  require_file "$wps_root/link_grib.csh"
  require_file "$wps_root/ungrib/Variable_Tables/Vtable.NAM"
  require_file "$wps_root/configure.wps"

  grep -q -- "-DUSE_JPEG2000" "$wps_root/configure.wps" \
    || fail "configure.wps does not include -DUSE_JPEG2000"
  grep -q -- "-DUSE_PNG" "$wps_root/configure.wps" \
    || fail "configure.wps does not include -DUSE_PNG"

  cp "$wps_root/configure.wps" "$evidence_dir/configure.wps"
  record_inventory "$evidence_dir" "$wps_root"
}

pin_intel_classic_mpi_wrappers() {
  local config=$1
  local transcript=$2

  grep -Eq '^SFC[[:space:]]*=[[:space:]]*ifort([[:space:]]*)?$' "$config" || return
  grep -Eq '^SCC[[:space:]]*=[[:space:]]*icc([[:space:]]*)?$' "$config" || return

  sed -i \
    -e 's/^DM_FC[[:space:]]*=.*/DM_FC               = mpif90 -f90=$(SFC)/' \
    -e 's/^DM_CC[[:space:]]*=.*/DM_CC               = mpicc -cc=$(SCC)/' \
    "$config"

  {
    echo
    echo "Applied CHPC Intel Classic MPI wrapper pinning:"
    grep -E '^(SFC|SCC|DM_FC|DM_CC)[[:space:]]*=' "$config"
  } >> "$transcript"
}

[[ "${BRC_GATE3_APPROVED:-}" == "YES" ]] \
  || fail "set BRC_GATE3_APPROVED=YES only after explicit human approval for Gate 3 compile-scale WPS work"

MODE=${BRC_GATE3_MODE:-auto}
WRF_SRC=${BRC_WRF_SRC:-"$HOME/gits/brc-wrf"}
WPS_ROOT=${BRC_WPS_ROOT:-/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS}
BUILD_LOG_ROOT=${BRC_WRF_BUILD_LOG_ROOT:-/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf}
STATIC_GEOG=${BRC_WPS_GEOG:-/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG}
UTC_STAMP=$(date -u '+%Y%m%dT%H%M%SZ')
JOB_ID=${SLURM_JOB_ID:-manual}
EVIDENCE_DIR="$BUILD_LOG_ROOT/gate3_${UTC_STAMP}_${JOB_ID}"

case "$WPS_ROOT" in
  *"/u6060939/"*) fail "refusing Michael-owned WPS path: $WPS_ROOT" ;;
esac

mkdir -p "$EVIDENCE_DIR"
exec > >(tee "$EVIDENCE_DIR/gate3_wps_proof.log") 2>&1

echo "Gate 3 John-owned WPS proof"
echo "UTC: $(date -u '+%Y-%m-%d %H:%M:%S')"
echo "Host: $(hostname)"
echo "Job: $JOB_ID"
echo "Mode: $MODE"
echo "WRF_SRC=$WRF_SRC"
echo "WPS_ROOT=$WPS_ROOT"
echo "STATIC_GEOG=$STATIC_GEOG"
echo "EVIDENCE_DIR=$EVIDENCE_DIR"
echo

[[ -d "$WRF_SRC" ]] || fail "WRF source root is missing: $WRF_SRC"
require_file "$WRF_SRC/main/real.exe"
require_file "$WRF_SRC/main/wrf.exe"
[[ -d "$STATIC_GEOG" ]] || fail "static WPS geography path is missing: $STATIC_GEOG"

{
  echo "Source state"
  echo "WRF_SRC=$WRF_SRC"
  git -C "$WRF_SRC" status --short --branch --untracked-files=all
  git -C "$WRF_SRC" rev-parse HEAD
  git -C "$WRF_SRC" remote -v
  echo
  ls -lh --time-style=long-iso "$WRF_SRC/main/real.exe" "$WRF_SRC/main/wrf.exe"
} > "$EVIDENCE_DIR/source_state.txt"

if ! type module >/dev/null 2>&1 && [[ -f /etc/profile.d/modules.sh ]]; then
  # shellcheck source=/dev/null
  source /etc/profile.d/modules.sh
fi

type module >/dev/null 2>&1 || fail "environment modules are not available"

module purge
module load intel-oneapi-compilers/2021.4.0
module load intel-oneapi-mpi/2021.1.1
module load hdf5/1.14.3
module load netcdf-c/4.9.2
module load netcdf-fortran/4.6.1

export NETCDF
NETCDF=$(nf-config --prefix)
export NETCDF_C
NETCDF_C=$(nc-config --prefix)
export JASPERLIB=${JASPERLIB:-/usr/lib64}
export JASPERINC=${JASPERINC:-/usr/include/jasper}
export WRF_DIR=${WRF_DIR:-$WRF_SRC}

module -t list > "$EVIDENCE_DIR/modules_loaded.txt" 2>&1
{
  echo "NETCDF=$NETCDF"
  echo "NETCDF_C=$NETCDF_C"
  echo "JASPERLIB=$JASPERLIB"
  echo "JASPERINC=$JASPERINC"
  echo "WRF_DIR=$WRF_DIR"
  command -v nf-config
  command -v nc-config
  nf-config --all
  nc-config --all
} > "$EVIDENCE_DIR/build_env.txt"

if [[ "$MODE" == "verify" ]]; then
  verify_gate3 "$EVIDENCE_DIR" "$WPS_ROOT"
elif [[ "$MODE" == "auto" || "$MODE" == "build" ]]; then
  if [[ ! -e "$WPS_ROOT" ]]; then
    [[ -n "${BRC_WPS_SOURCE:-}" ]] \
      || fail "WPS_ROOT is absent and BRC_WPS_SOURCE was not set"
    copy_wps_source "$BRC_WPS_SOURCE" "$WPS_ROOT"
  fi

  [[ -d "$WPS_ROOT" ]] || fail "WPS root is not a directory: $WPS_ROOT"
  cd "$WPS_ROOT"

  if [[ ! -f configure.wps || "${BRC_WPS_FORCE_CONFIGURE:-NO}" == "YES" ]]; then
    [[ -n "${BRC_WPS_CONFIGURE_OPTION:-}" ]] \
      || fail "set BRC_WPS_CONFIGURE_OPTION to the WPS configure menu number; this script will not guess it"
    printf '%s\n' "$BRC_WPS_CONFIGURE_OPTION" \
      | ./configure > "$EVIDENCE_DIR/configure_transcript.txt" 2>&1
  else
    echo "Using existing configure.wps in $WPS_ROOT" \
      > "$EVIDENCE_DIR/configure_transcript.txt"
  fi

  pin_intel_classic_mpi_wrappers configure.wps "$EVIDENCE_DIR/configure_transcript.txt"

  cp configure.wps "$EVIDENCE_DIR/configure.wps"
  grep -q -- "-DUSE_JPEG2000" configure.wps \
    || fail "configure.wps does not include -DUSE_JPEG2000"
  grep -q -- "-DUSE_PNG" configure.wps \
    || fail "configure.wps does not include -DUSE_PNG"

  ./compile > "$EVIDENCE_DIR/compile_wps.log" 2>&1
  verify_gate3 "$EVIDENCE_DIR" "$WPS_ROOT"
else
  fail "unknown BRC_GATE3_MODE: $MODE"
fi

{
  echo "Gate/item: Roadmap Gate 3 - Approved John-owned WPS proof"
  echo "Result: PASS"
  echo "Evidence path: $EVIDENCE_DIR"
  echo "WPS root: $WPS_ROOT"
  echo "What was not run: geogrid.exe, ungrib.exe, metgrid.exe, real.exe, wrf.exe, staging, strict artifact reads, NetCDF/archive checks, quicklooks, scaling, memory benchmarks."
  echo "Next suggested item: Roadmap Gate 4 - case manifest root alignment."
} > "$EVIDENCE_DIR/closeout.txt"

cat "$EVIDENCE_DIR/closeout.txt"
