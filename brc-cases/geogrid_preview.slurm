#!/bin/bash
# Gate-B geogrid-only domain preview for a five-domain WRF case (default:
# ashley2026_seiche). Self-contained runner for the BRC WRF Domain Preview SOP.
#
# It (1) builds the custom 1-arc-second HGT_M static set from cached USGS DEM
# tiles, (2) assembles geog_data_path (default WPS_GEOG symlinks + reuse of the
# 3s custom set for d04 + the new 1s set for d05), (3) writes a run-local patched
# GEOGRID.TBL carrying both custom tokens, (4) runs geogrid.exe over all domains,
# (5) verifies each custom token was actually used (no silent default fallback),
# and (6) renders domain_preview.png. It STOPS before ungrib/metgrid/real/wrf.
#
# Submit from a login shell (owned node), review-approved:
#   sbatch brc-cases/geogrid_preview.slurm
# Override any VAR=... before sbatch via --export, e.g.
#   sbatch --export=ALL,PREVIEW_BOUNDS="-109.75 40.27 -109.30 40.63" brc-cases/geogrid_preview.slurm

#SBATCH --job-name=geogrid_preview_ashley
#SBATCH --account=lawson-np
#SBATCH --partition=lawson-np
#SBATCH --nodelist=notch392
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem=48G
#SBATCH --time=00:40:00
#SBATCH --output=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/geogrid_preview_%j.out
#SBATCH --error=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/geogrid_preview_%j.out
#SBATCH --export=ALL

set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 2; }

# ---- configuration (env-overridable; defaults target ashley2026_seiche) ----
USER_NAME="${USER:-u0737349}"
CASE="${PREVIEW_CASE:-ashley2026_seiche}"
WRF_SRC="${PREVIEW_WRF_SRC:-/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf}"
WPS_ROOT="${PREVIEW_WPS_ROOT:-/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS}"
GEOG_SRC="${PREVIEW_GEOG_SRC:-/scratch/general/vast/${USER_NAME}/wps_geog_terrain3s}"
GEOG_DST="${PREVIEW_GEOG_DST:-/scratch/general/vast/${USER_NAME}/wps_geog_ashley_1s}"
DEM_DIR="${PREVIEW_DEM_DIR:-/scratch/general/vast/${USER_NAME}/wrf_inputs/pelican2013_terrain3s/usgs_3dep_1arcsec}"
DEM_TILES=("${DEM_DIR}"/USGS_1_n40w109_*.tif "${DEM_DIR}"/USGS_1_n40w110_*.tif \
           "${DEM_DIR}"/USGS_1_n41w109_*.tif "${DEM_DIR}"/USGS_1_n41w110_*.tif)
PREVIEW_BOUNDS="${PREVIEW_BOUNDS:--109.75 40.27 -109.30 40.63}"
ONE_S_DXDEG="${PREVIEW_ONE_S_DXDEG:-0.0002777777777777778}"
RUN_ROOT="${PREVIEW_RUN_ROOT:-/scratch/general/vast/${USER_NAME}/wrf_runs/${CASE}}"
WPS_RUN="${PREVIEW_WPS_RUN:-${RUN_ROOT}/wps_run}"
NAMELIST_TEMPLATE="${PREVIEW_NAMELIST:-/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/${CASE}/control/draft/namelist.wps}"
ARCHIVE_ROOT="${PREVIEW_ARCHIVE_ROOT:-/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/${CASE}}"
FIG_KEEP="${PREVIEW_FIG_KEEP:-/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/ub-wx-figures/20260222-ashley-seiche-wrf}"
CONDA_PY="${PREVIEW_CONDA_PY:-/uufs/chpc.utah.edu/common/home/u0737349/software/pkg/miniforge3/envs/brc-tools-2026/bin/python}"

TOKEN_3S="brc_custom_3s";  REL_3S="topo_brc_custom_3s"
TOKEN_1S="brc_custom_1s";  REL_1S="topo_brc_custom_1s"
HELPER="${WRF_SRC}/brc-cases/wps_hgt_static.py"
PLOT="${WRF_SRC}/brc-cases/geogrid_preview_plot.py"
GEOGRID_TBL_BASE="${WPS_ROOT}/geogrid/GEOGRID.TBL.ARW"
GEOGRID_EXE="${WPS_ROOT}/geogrid.exe"
UTC="$(date -u +%Y%m%dT%H%M%SZ)"
JOBID="${SLURM_JOB_ID:-manual}"
PACKET="${ARCHIVE_ROOT}/domain_review/geogrid_${UTC}_${JOBID}"

echo "geogrid preview start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) job=${JOBID}"
echo "  case=${CASE} wps_run=${WPS_RUN} geog_dst=${GEOG_DST}"

# Clean module state so the system GDAL CLI used by the 1s build links its own
# libraries (the geogrid stack is loaded later, just before geogrid.exe).
module purge 2>/dev/null || true

# ---- preflight -------------------------------------------------------------
[[ -x "${GEOGRID_EXE}" ]] || fail "geogrid.exe not executable: ${GEOGRID_EXE}"
[[ -f "${GEOGRID_TBL_BASE}" ]] || fail "missing GEOGRID.TBL.ARW: ${GEOGRID_TBL_BASE}"
[[ -f "${NAMELIST_TEMPLATE}" ]] || fail "missing namelist template: ${NAMELIST_TEMPLATE}"
[[ -f "${HELPER}" ]] || fail "missing helper: ${HELPER}"
[[ -f "${PLOT}" ]] || fail "missing plot script: ${PLOT}"
[[ -d "${GEOG_SRC}" ]] || fail "missing geog source (default symlinks + 3s reuse): ${GEOG_SRC}"
[[ -d "${GEOG_SRC}/${REL_3S}" ]] || fail "missing 3s custom set to reuse: ${GEOG_SRC}/${REL_3S}"
for t in "${DEM_TILES[@]}"; do [[ -f "$t" ]] || fail "missing cached DEM tile: $t"; done
command -v gdalwarp >/dev/null 2>&1 || fail "gdalwarp not on PATH (need system/module GDAL for the 1s build)"

mkdir -p "${WPS_RUN}" "${GEOG_DST}" "${PACKET}"

# ---- step 1: build the 1-arc-second custom HGT_M set (GDAL) -----------------
# Clean environment for system GDAL CLI; the helper shells out to gdal* tools.
echo "[1/6] building ${REL_1S} from cached 1s DEM tiles into ${GEOG_DST}/${REL_1S}"
"${CONDA_PY}" -B "${HELPER}" build \
    --source-dem "${DEM_TILES[@]}" \
    --output-dir "${GEOG_DST}/${REL_1S}" \
    --bounds ${PREVIEW_BOUNDS} \
    --dx-deg "${ONE_S_DXDEG}" \
    --filename-digits 6 \
    --resampling bilinear \
    --description "Custom 1-arc-second topography height for BRC WRF"
[[ -f "${GEOG_DST}/${REL_1S}/index" ]] || fail "1s build produced no index file"
n_1s_tiles=$(find "${GEOG_DST}/${REL_1S}" -maxdepth 1 -type f ! -name index | wc -l)
echo "      ${REL_1S}: ${n_1s_tiles} tile(s)"
[[ "${n_1s_tiles}" -ge 1 ]] || fail "1s build produced no tiles"

# ---- step 2: assemble geog_data_path ---------------------------------------
# default WPS_GEOG datasets + the reused 3s set become resolved symlinks; the
# freshly built 1s set stays a real directory.
echo "[2/6] assembling ${GEOG_DST} (default symlinks + ${REL_3S} reuse + ${REL_1S})"
for entry in "${GEOG_SRC}"/*; do
    name="$(basename "${entry}")"
    [[ "${name}" == "${REL_1S}" ]] && continue
    ln -sfn "$(readlink -f "${entry}")" "${GEOG_DST}/${name}"
done
[[ -e "${GEOG_DST}/${REL_3S}/index" ]] || fail "reused ${REL_3S} not resolvable under ${GEOG_DST}"
[[ -e "${GEOG_DST}/${REL_1S}/index" ]] || fail "built ${REL_1S} missing under ${GEOG_DST}"
[[ -e "${GEOG_DST}/topo_gmted2010_30s" ]] || fail "default topo (topo_gmted2010_30s) missing under ${GEOG_DST}"

# ---- step 3: run-local patched GEOGRID.TBL with BOTH custom tokens ----------
echo "[3/6] patching GEOGRID.TBL with ${TOKEN_3S} and ${TOKEN_1S}"
# Never write into a symlinked default geogrid/ dir (would clobber the shared build).
if [[ -L "${WPS_RUN}/geogrid" ]]; then rm -f "${WPS_RUN}/geogrid"; fi
mkdir -p "${WPS_RUN}/geogrid"
TBL="${WPS_RUN}/geogrid/GEOGRID.TBL"
"${CONDA_PY}" -B "${HELPER}" patch-geogrid-table --base "${GEOGRID_TBL_BASE}" \
    --output "${TBL}" --token "${TOKEN_3S}" --rel-path "${REL_3S}"
"${CONDA_PY}" -B "${HELPER}" patch-geogrid-table --base "${TBL}" \
    --output "${TBL}" --token "${TOKEN_1S}" --rel-path "${REL_1S}"
grep -q "${TOKEN_3S}:" "${TBL}" || fail "patched table missing ${TOKEN_3S} token"
grep -q "${TOKEN_1S}:" "${TBL}" || fail "patched table missing ${TOKEN_1S} token"

# ---- step 4: stage namelist.wps + geogrid.exe, run geogrid -----------------
echo "[4/6] staging + running geogrid.exe in ${WPS_RUN}"
cp -f "${NAMELIST_TEMPLATE}" "${WPS_RUN}/namelist.wps"
ln -sfn "${GEOGRID_EXE}" "${WPS_RUN}/geogrid.exe"
# sanity: the staged namelist must point geog_data_path at GEOG_DST
grep -q "$(basename "${GEOG_DST}")" "${WPS_RUN}/namelist.wps" || \
    fail "staged namelist.wps geog_data_path does not reference ${GEOG_DST}"
rm -f "${WPS_RUN}"/geo_em.d0*.nc "${WPS_RUN}/geogrid.log"

module purge
module load intel-oneapi-compilers/2021.4.0
module load intel-oneapi-mpi/2021.1.1
module load hdf5/1.14.3
module load netcdf-c/4.9.2
module load netcdf-fortran/4.6.1

cd "${WPS_RUN}"
t0=$(date -u +%s)
srun --mpi=pmi2 -n 1 ./geogrid.exe || fail "geogrid.exe failed (see ${WPS_RUN}/geogrid.log)"
t1=$(date -u +%s)
grep -q "Successful completion of program geogrid.exe" geogrid.log || fail "geogrid.log has no success marker"

# ---- step 5: verify each domain used the intended terrain source ------------
echo "[5/6] verifying HGT_M source per domain (guarding silent default fallback)"
ndom=$(ls -1 geo_em.d0*.nc 2>/dev/null | wc -l)
[[ "${ndom}" -ge 5 ]] || fail "expected 5 geo_em files, found ${ndom}"
hgt_src() { grep -A3 "Processing domain $1 of ${ndom}" geogrid.log \
    | grep -m1 "data source for HGT_M" || true; }
grep -n "data source for HGT_M" geogrid.log > "${PACKET}/geogrid_hgt_source_grep.txt" || true
d4src="$(hgt_src 4)"; d5src="$(hgt_src 5)"
echo "      d04: ${d4src}"
echo "      d05: ${d5src}"
echo "${d4src}" | grep -q "${TOKEN_3S}" || fail "d04 did NOT use ${TOKEN_3S} (silent fallback): ${d4src}"
echo "${d5src}" | grep -q "${TOKEN_1S}" || fail "d05 did NOT use ${TOKEN_1S} (silent fallback): ${d5src}"

# ---- step 6: render preview + summary (conda python; module-free) ----------
echo "[6/6] rendering domain_preview.png"
module purge
"${CONDA_PY}" -B "${PLOT}" \
    --wps-run "${WPS_RUN}" \
    --out-png "${WPS_RUN}/domain_preview.png" \
    --summary-tsv "${WPS_RUN}/geogrid_geo_em_summary.tsv" \
    --title "${CASE} 5-domain geogrid preview (d05 37 m, 1-arc-second terrain)"
[[ -f "${WPS_RUN}/domain_preview.png" ]] || fail "plot did not produce domain_preview.png"

# ---- archive review packet + curated figure copy ---------------------------
printf "geogrid\t%s\t%s\n" "$((t1 - t0))" "0" > "${WPS_RUN}/geogrid_phase_times.tsv"
{
  printf "case\t%s\n" "${CASE}"
  printf "tag\tgeogrid_%s\n" "${UTC}"
  printf "job_id\t%s\n" "${JOBID}"
  printf "host\t%s\n" "$(hostname)"
  printf "finish_utc\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf "wrf_commit\t%s\n" "$(git -C "${WRF_SRC}" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  printf "wps_root\t%s\n" "${WPS_ROOT}"
  printf "geog_root\t%s\n" "${GEOG_DST}"
  printf "geog_data_res\td01-03 default; d04 %s+default; d05 %s+default\n" "${TOKEN_3S}" "${TOKEN_1S}"
  printf "hgt_m_source_d04\t%s\n" "${d4src}"
  printf "hgt_m_source_d05\t%s\n" "${d5src}"
  printf "one_arcsec_bounds\t%s\n" "${PREVIEW_BOUNDS}"
  printf "one_arcsec_tiles\t%s\n" "${n_1s_tiles}"
  printf "wps_run\t%s\n" "${WPS_RUN}"
  printf "archive\t%s\n" "${PACKET}"
  printf "stop_point\tgeogrid-only preview; did not run ungrib, metgrid, real.exe, wrf.exe, or quicklooks\n"
} > "${WPS_RUN}/domain_preview_summary.tsv"

cp -f "${WPS_RUN}/domain_preview.png" "${WPS_RUN}/geogrid_geo_em_summary.tsv" \
      "${WPS_RUN}/domain_preview_summary.tsv" "${WPS_RUN}/geogrid_phase_times.tsv" \
      "${WPS_RUN}/namelist.wps" "${WPS_RUN}/geogrid.log" "${TBL}" \
      "${GEOG_DST}/${REL_1S}/index" "${PACKET}/" 2>/dev/null || true
cp -f "${GEOG_DST}/${REL_1S}/index" "${PACKET}/topo_brc_custom_1s.index" 2>/dev/null || true
cp -f "${WPS_RUN}"/geo_em.d0*.nc "${PACKET}/" 2>/dev/null || true
{ ls -l "${WPS_RUN}" ; echo "---" ; ls -l "${PACKET}" ; } > "${PACKET}/file_inventory.tsv" 2>/dev/null || true

mkdir -p "${FIG_KEEP}"
cp -f "${WPS_RUN}/domain_preview.png" "${FIG_KEEP}/domain_preview.png"
cp -f "${WPS_RUN}/domain_preview_summary.tsv" "${FIG_KEEP}/domain_preview_summary.tsv" 2>/dev/null || true

echo "geogrid preview OK: packet=${PACKET}"
echo "  domain_preview.png -> ${FIG_KEEP}/domain_preview.png"
echo "geogrid preview stop $(date -u +%Y-%m-%dT%H:%M:%SZ)"
