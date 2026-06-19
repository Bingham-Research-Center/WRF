# Gate 10 Quicklook Visual Review

Purpose: record the first visual pass over the existing Gate 10 PNG quicklooks
for the Jan-2013 NAM-only Basin proof. This is a review note, not a new
quicklook render and not final scientific approval.

## Scope

| Field | Value |
| --- | --- |
| Review date | 2026-06-19 UTC |
| Reviewer | Codex visual pass for John/Michael review |
| Case | `jan2013_basin_gefs`, NAM-only forcing |
| Source archive | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_gate8_20260618T062439Z_13540006/` |
| Quicklook directory | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_gate8_20260618T062439Z_13540006/quicklooks/` |
| Gate 10 job evidence | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate10_20260618T065224Z_13540365/` |
| What was inspected | Existing PNG files only |
| What was not run | No NetCDF reads, quicklook check/render, WPS, `real.exe`, `wrf.exe`, `sbatch`, strict validation, manifest hashing, archive copy, or benchmark submission |

The fresh Gate 8 archive quicklooks and the older `run_20260613T044846Z`
quicklooks have matching filenames and byte sizes. The fresh Gate 8 archive is
the review target.

## File Inventory

| File | Size | Visual finding |
| --- | ---: | --- |
| `wps_domain_terrain.png` | 146545 bytes | Nonblank, framed terrain plot. The d02 outline is inside d01 and centered over the intended Intermountain/Basin terrain corridor. Terrain range and colorbar are plausible. |
| `wps_d02_landmask.png` | 40343 bytes | Nonblank d02 land/water mask. The domain is nearly all land, with the Great Salt Lake visible; no obvious shifted-grid signal. |
| `wps_d02_skintemp_snow.png` | 335911 bytes | Nonblank WPS skin-temperature field with snow contours. Temperatures span roughly `-21` to `0` C and spatial structure follows terrain and snow/cold-pool patterns expected for late January. |
| `wrf_d02_t2_10m_wind.png` | 517208 bytes | Nonblank WRF near-surface field. T2 spans roughly `-14` to `+3` C; 10 m wind vectors are coherent and not obviously unit-broken or exploded. |
| `wrf_d02_snow_depth.png` | 415433 bytes | Nonblank WRF snow-depth field. Snow depth reaches roughly `0.5` m, is spatially varied, and is terrain-related; it is neither all-zero nor uniformly saturated. |

## Review Result

Preliminary visual sanity: pass.

No inspected PNG showed a blank panel, all-missing field, obvious domain shift,
implausible colorbar unit, exploded wind vector field, or all-zero snow field.
The quicklooks are suitable for a John/Michael meteorological review of whether
the NAM-only proof is good enough as the baseline for practical tuning.

This review does not compare against station observations, snow analyses, or an
independent meteorological truth dataset. It also does not approve additional
WRF runs. The next decision should be one of:

1. John/Michael accepts the NAM-only visual baseline and approves exactly one
   additional benchmark row.
2. John/Michael asks for a targeted quicklook improvement such as Basin/point
   overlays before more benchmarks.
3. John/Michael parks scaling and chooses the GEFS+NAM WPS-only design path.

## Recommended Next Benchmark If Approved

If the visual baseline is acceptable and John wants one more benchmark row, the
next most useful row is `scaling_t016` with the same WRF/WPS roots, input
contract, namelist, archive pattern, and `900G` memory request used for the
successful `scaling_t028` row. That tests whether the cheaper lower-task shape
is viable before spending another row on `scaling_t056` or memory
right-sizing.

Approval must name the exact row and stop point before `sbatch`. A suitable
scope is:

```text
Approve exactly one Slurm submission: scaling_t016 from the current Gate 11
packet, using John's ~/gits/brc-wrf WRF 4.8.0 build, John-owned WPS artifacts,
NAM-only Jan-2013 case inputs, 16 tasks, 900G, and stop after real.exe/wrf.exe,
archive, and compact debug evidence succeed or fail. Do not submit scaling_t056
or memory rows.
```
