# BRC WRF First Case Runbook

This is the current start-to-finish proof path that connects `../brc-tools`
input staging to WPS, `real.exe`, `wrf.exe`, and archive checks for this
`brc-wrf` checkout.

It is a runbook, not an approval to submit jobs. DTN staging jobs, WPS work,
`real.exe`, `wrf.exe`, scaling sweeps, and Slurm submissions still need explicit
human approval before they run.

Beginner rule: keep three contexts separate. Metadata validation and path-only
unit tests are login-safe; manifest hashing, strict artifact checks, NetCDF
reads, and quicklook rendering are approved off-login checks; WPS and WRF
execution require explicit run approval.

## Current Status

- Validated path: NAM-only, single WPS stream, `Vtable.NAM`,
  `interval_seconds = 21600`.
- Validated case: known Jan-2013 Uinta Basin 12/4 km nested domain,
  `2013-01-31_12:00:00` through `2013-02-02_00:00:00`.
- Validated runtime target: `notch392`, `lawson-np`, one node, 56 tasks,
  Intel MPI launched with `srun --mpi=pmi2`.
- John-owned WPS executable root is now proven at
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS`.
  Gate 3 evidence:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate3_20260618T054456Z_13539773/`.
- Fresh 2026-06-18 NAM-only proof passed through input contract, WPS,
  `real.exe`, `wrf.exe`, archive, and quicklooks. The new archive is
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_gate8_20260618T062439Z_13540006`,
  with quicklooks in its `quicklooks/` subdirectory.
- Practical testing has one completed `scaling_t028` row. The first attempt
  exposed wrong executable provenance and missing runtime physics files, but
  retry job `13550110` ran John's WRF `V4.8.0` from `~/gits/brc-wrf`, passed
  `real.exe`/`wrf.exe`, and archived debug evidence under
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t028/run_20260618T230858Z/debug/`.
  Other practical rows still need explicit approval.
- Not yet validated: GEFSv12 reforecast plus NAM two-stream forcing
  (`fg_name = 'GEFS','NAM'`, `interval_seconds = 10800`).

Do not describe this proof as a fresh standalone 4 km case or as a completed
GEFS+NAM two-stream run.

The input contract/source identity for the proof is NAM. The old proof scratch
`namelist.wps` used the WPS default intermediate prefix, so its live values are
`ungrib prefix = 'FILE'` and `metgrid fg_name = 'FILE'`. Future NAM-only runs may
use `prefix = 'NAM'` and `fg_name = 'NAM'` if those names are kept paired.

## Ownership

| Step | Owner | Node class | Main output |
| --- | --- | --- | --- |
| Plan and stage GRIB input | `../brc-tools` | DTN | `/scratch/general/vast/$USER/wrf_inputs/<case>/` |
| Validate staged input | `../brc-tools` | approved compute/batch or DTN | `manifest_<case>.json` check results |
| WPS setup and run | WPS plus this runbook | allocation or batch | `met_em.d0*` |
| `real.exe` and `wrf.exe` | `brc-wrf` build/run tree | `notch392` batch | `wrfinput_d0*`, `wrfbdy_d01`, `wrfout_d0*` |
| Archive and explain result | `brc-wrf` wrapper | end of batch | `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/` |

## brc-tools Input Contract

Read `../brc-tools/docs/WRF-INPUT-STAGING.md` before consuming staged inputs.
Fresh `brc-tools` staging writes both:

```text
/scratch/general/vast/$USER/wrf_inputs/<case>/manifest_<case>.json
/scratch/general/vast/$USER/wrf_inputs/<case>/contract_<case>.json
```

Use the contract as the input handshake. It records the staged source counts,
cadence, valid window, suggested WPS `fg_name`, and `interval_seconds`.

For the validated NAM-only path, the WPS-side constants are:

| Fact | Value |
| --- | --- |
| `wps_fg_name` | `NAM` |
| observed proof `namelist.wps` `fg_name` | `FILE` |
| `interval_seconds` | `21600` |
| `num_metgrid_levels` | `40` |
| `met_em` count | 14 files, d01 and d02 at 6-hour cadence |
| Required fields observed | `LANDSEA`, `SOILHGT`, `SKINTEMP`, `SEAICE`, `SNOW`, `SNOWH`, four soil-temperature layers, four soil-moisture layers |

The old proof scratch set was staged before the contract sidecar existed, so it
may have only the manifest. This `brc-wrf` checkout carries
`brc-cases/jan2013_basin_nam.contract.json`, a reconstructed NAM-only contract
for the validated consumption path, so the case validator has a durable
handshake to read. Do not treat the missing old scratch sidecar as evidence that
fresh `brc-tools` staging lacks the contract feature.

Login-safe planning plus off-login verification:

```bash
cd ~/gits/brc-tools
python scripts/stage_wrf_inputs.py --plan --case jan2013_basin_gefs \
  --init-time "2013-01-31 12Z" --source nam_analysis

# Off-login only: this hashes existing staged GRIB files.
python scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json
```

The `--plan` command is metadata planning. Manifest verification reads scratch
artifacts and should run only in an approved compute/batch context or on the
appropriate transfer node.

Current checked evidence: fresh NAM-only Gate 5 sidecars exist on scratch and
the manifest verifies `7/7 OK`:

```text
/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json
/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/contract_jan2013_basin_gefs.json
```

The previous mixed scratch manifest that verified `28/28 OK` is historical
context. The fresh 2026-06-18 rerun consumed the NAM stream only.

## WPS Handoff

Stage active case I/O under scratch:

```text
/scratch/general/vast/$USER/wrf_runs/<case>/
  grib_data/
  wps_run/
  wrf_run/
```

For the validated path:

- Link or copy `wrf_inputs/<case>/nam_analysis/` into `grib_data/`.
- Use `Vtable.NAM`.
- Keep the WPS intermediate prefix and metgrid `fg_name` paired. The checked
  proof scratch used `prefix = 'FILE'` and `fg_name = 'FILE'`; a cleaned-up
  NAM-named stream should use `prefix = 'NAM'` and `fg_name = 'NAM'`.
- Set WPS/WRF interval to 6 hours (`interval_seconds = 21600`).
- Keep `geog_data_path = /uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/`.

After WPS, check that `met_em` exists for both domains and that the resulting
WRF namelist uses `num_metgrid_levels = 40`.

## WRF Run Wrapper

Use the CHPC-validated wrapper as the starting point:

```text
../brc-knowledge/scholarium/reference-base/resources/run_wrf_feb05.slurm
```

For maintained BRC-side practical-test renders, use the case manifest entrypoint:

```bash
python brc-cases/wrf_case.py render-practical-harness \
  brc-cases/jan2013_basin_nam.case.yaml \
  --output-dir /tmp/brc_gate11_jan2013_basin_gefs
```

That command writes a review packet, per-scenario prepare/check checklist,
approval packet, baseline wrapper, scaling wrappers, blank result tables,
approval boundaries, and closeout template outside the repo. It does not submit
jobs or read staged/archive artifacts; generated wrappers still need prepared
per-scenario `wrf_run` directories and explicit approval before `sbatch`.

For login-safe guardrails around quicklook paths, run:

```bash
python brc-cases/test_wrf_quicklook.py
```

Those tests exercise output-path refusal and archive-run selection only. They do
not verify manifests, open NetCDF files, read archives, or render PNGs.

The wrapper must keep these CHPC-specific details:

- reload the validated Intel/HDF5/netCDF module stack inside the batch job;
- write a plain settings readback before model execution, including case
  window, forcing stream, WPS cadence, Vtable/prefix/`fg_name`, Slurm shape,
  launcher, and storage paths;
- write compact debug artifacts beside WRF logs:
  `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, and
  `debug/run_file_inventory.tsv`;
- run `real.exe` directly and require `SUCCESS COMPLETE REAL_EM INIT`;
- move `real.exe` `rsl.*` files aside before `wrf.exe`;
- launch WRF with `srun --mpi=pmi2 -n "$SLURM_NTASKS" ./wrf.exe`;
- require `SUCCESS COMPLETE WRF` in `rsl.out.0000`.

WRF output filenames contain colons, so archive commands must prefix local
sources or use absolute paths:

```bash
rsync -av ./wrfout_d0* "$ARCHIVE_DIR/"
rsync -av namelist.input rsl.out.0000 rsl.error.0000 \
  real.rsl.out.0000 real.rsl.error.0000 "$ARCHIVE_DIR/"
```

Treat Slurm batch state, the WRF `.0` step state, WRF success markers, and
archive completeness as separate facts. A post-WRF archive failure can mark the
batch failed even when WRF completed successfully.

For fresh NWP downloads, stay in `brc-tools`: use Herbie-backed paths where
available, respect its direct NCEI path for historical NAM analysis, and run
full transfer work on `notchpeak-dtn`. This repo consumes the resulting
manifest and contract sidecars.

## Proof Evidence

Fresh evidence checked on 2026-06-18:

| Gate | Evidence |
| --- | --- |
| Gate 5 fresh contract | `/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/gate5_nam_contract_13539969.out`; `verify: 7/7 OK`; strict validation log `/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/gate5_validate_13539980.out`. |
| Gate 6 WPS | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate6_20260618T061731Z_13539991/`; 14 `met_em` files, `num_metgrid_levels = 40`. |
| Gate 7 `real.exe` | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate7_20260618T062118Z_13540001/`; `SUCCESS COMPLETE REAL_EM INIT`. |
| Gate 8/9 `wrf.exe` and archive | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate8_20260618T062439Z_13540006/`; `SUCCESS COMPLETE WRF`; 74 `wrfout` files archived. |
| Gate 10 quicklooks | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate10_20260618T065224Z_13540365/`; five PNGs under the Gate 8 archive `quicklooks/` directory. |
| Gate 10 visual review | `brc-docs/BRC-WRF-GATE10-QUICKLOOK-REVIEW.md`; PNG-only sanity pass, pending John/Michael science acceptance. |

Evidence checked on 2026-06-13 without submitting a new job:

- `brc-tools` manifest verification:
  `/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json`
  verified `28/28 OK`.
- Archive:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_20260613T044846Z`
  contains 194 files, including 74 `wrfout_d0*` files, and is 2.2G.
- `real.rsl.out.0000` contains
  `d01 2013-02-02_00:00:00 real_em: SUCCESS COMPLETE REAL_EM INIT`.
- `rsl.out.0000` contains
  `d01 2013-02-02_00:00:00 wrf: SUCCESS COMPLETE WRF`.

The non-fatal `real.exe` soil message observed for the proof was:
`forcing artificial silty clay loam at 2 points, out of 18000`.

## Next Tests

1. Have John/Michael accept or reject the Gate 10 quicklook review in
   `brc-docs/BRC-WRF-GATE10-QUICKLOOK-REVIEW.md`.
2. Choose whether to approve exactly one additional practical benchmark row.
   The recommended next row is `scaling_t016`; `scaling_t028` has already
   passed after the wrapper sourced executables from John's build, byte-checked
   them, and staged runtime physics files from John's `~/gits/brc-wrf/run/`.
3. GEFS+NAM two-stream WPS/real path: build or select a GEFSv12 reforecast
   Vtable, ungrib GEFS and NAM separately, run metgrid with
   `fg_name = 'GEFS','NAM'`, then prove `real.exe`.
4. Use `brc-cases/` to review the case manifest, validate cheap metadata, and
   render Slurm text before any submitted run.
5. Keep generated run packets, logs, NetCDF, PNGs, and one-off Slurm files out
   of the repo; durable evidence belongs under `lawson-group6`.
