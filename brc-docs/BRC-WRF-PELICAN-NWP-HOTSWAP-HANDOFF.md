# Pelican NWP Hot-Swap Handoff

This is the current paste-ready handoff for tracking Pelican 3/1/0.333 km,
75-level NWP forcing hot-swaps.

It supersedes older one-off context files. Keep this file as the active Pelican
source verdict and review prompt.

## Current Verdict

| Source family | Verdict | Next action |
| --- | --- | --- |
| NAM baseline | Complete. `pelican2013_nam_3_1_333m_75lev` is the comparison anchor. | Preserve as baseline. |
| RAP-only | Blocked before `real.exe`. Hybrid RAP lacked a real-ready 3D atmosphere; pressure RAP had 38 atmospheric levels but no layered soil temperature/moisture. | Park unchanged RAP-only reruns. Revisit only with a corrected RAP product or explicit filler-stream design. |
| ERA5 | Locally blocked for immediate staging. `brc-tools` has no ERA5 WRF source, `brc-tools-2026` lacks `cdsapi`/`ecmwfapi`, and CDS credentials were not configured. WPS-side support is plausible via `Vtable.ECMWF`. | Defer until CDS tooling/credentials and pressure-level plus surface/land request support exist. |
| GFS analysis | Complete. `pelican2013_gfs_3_1_333m_75lev` ran through WPS, `real.exe`, `wrf.exe`, and archive on 2026-06-30. `NUM_METGRID_SOIL_LEVELS = 4`, clearing the RAP failure mode. | Review with the rendered NAM/GFS standardized quicklooks. |
| FNL | Not tried in this WRF staging lane. | Optional third-source work in `brc-tools`, after the NAM/GFS comparison need is clear. |
| GEFS+NAM two-stream | Parked legacy filler/ensemble idea. | Do not revive unless John explicitly asks. |

## Fixed Run Geometry

Use the successful Pelican baseline as the comparison anchor:

```text
baseline case: pelican2013_nam_3_1_333m_75lev
window: 2013-02-02_12:00:00 to 2013-02-02_18:00:00 UTC
domains: 3 km / 1 km / 0.333 km
vertical levels: 75
baseline archive:
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/
```

Completed and optional case names:

```text
pelican2013_gfs_3_1_333m_75lev  # complete
pelican2013_fnl_3_1_333m_75lev
```

GFS archive:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_gfs_3_1_333m_75lev/full6h/run_20260630T181555Z/
```

Comparison quicklooks:

```text
job: 13755401, completed 0:0 in 00:01:38 on notch392
summary: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_gfs_compare/control/quicklooks_20260630T214000Z/quicklook_summary_13755401.tsv
NAM: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/quicklooks/standardized_compare_20260630T214000Z/
GFS: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_gfs_3_1_333m_75lev/full6h/run_20260630T181555Z/quicklooks/standardized_compare_20260630T214000Z/
```

The stamped folder above is historical. Future renders default to the simpler
`<archive-run>/quicklooks/dXX/` layout unless an explicit `--output-dir` is
needed to preserve a second render.

## GFS Source Facts

The consumed `brc-tools` GFS contract staged two NCEI GFS grid-004 analysis
files for 2013-02-02 12Z and 18Z. It matched the NAM comparison window and
cadence:

```text
source: gfs_analysis
files: gfsanl_4_20130202_1200_000.grb2, gfsanl_4_20130202_1800_000.grb2
cadence: 6 hours
interval_seconds: 21600
wps_fg_name: GFS
Vtable: Vtable.GFS
```

The field reason GFS cleared the RAP blocker: grid-004 carries a real-ready
pressure-level atmosphere and four soil temperature/moisture layers. The WRF
acceptance evidence confirmed `num_metgrid_levels = 27` and
`NUM_METGRID_SOIL_LEVELS = 4`.

## Ownership

| Repo | Owns | Do not do there |
| --- | --- | --- |
| `brc-tools` | NWP source access, Herbie/NCEI/RDA/CDS decisions, downloads, staging, manifests, contracts, source-matrix tests. | WPS, `real.exe`, `wrf.exe`, WRF Slurm wrappers, WRF case manifests. |
| `brc-wrf` | Case manifests, WPS Vtable review, WPS field-proof packet rendering, WRF run conveyor, archives, WRF-output quicklooks. | Downloader or GRIB-staging logic. |

For any `brc-tools` Python, Herbie, source-planning, staging, manifest
verification, or pytest command, force the maintained environment:

```bash
conda run -n brc-tools-2026 python ...
conda run -n brc-tools-2026 pytest ...
```

Do not trust an inherited shell environment. Current local verification showed:

```text
python: /uufs/chpc.utah.edu/common/home/u0737349/software/pkg/miniforge3/envs/brc-tools-2026/bin/python
herbie: 2026.3.0
cdsapi: absent
ecmwfapi: absent
```

## Prompt A: Codex In `brc-wrf`

Use this when the session starts in `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf`.

```text
cwd=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf

Goal: review the completed NAM and GFS Pelican 3/1/0.333 km, 75-level WRF runs
using the rendered standardized quicklooks, without rerunning blocked RAP-only
or reviving GEFS+NAM unless explicitly asked.

First read:
1. AGENTS.md
2. doc/BRC_WRF_MICROTASK_HANDOFF.md
3. brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md
4. brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md
5. brc-cases/README.md
6. ../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md
7. ../brc-tools/docs/WRF-INPUT-STAGING.md
8. ../brc-tools/docs/nwp/NWP-SOURCE-MATRIX.md

Current source verdicts:
- NAM baseline is complete: pelican2013_nam_3_1_333m_75lev.
- GFS analysis is complete: pelican2013_gfs_3_1_333m_75lev, job 13753673,
  NUM_METGRID_SOIL_LEVELS = 4, SUCCESS COMPLETE WRF.
- NAM/GFS standardized quicklooks are complete: job 13755401, 30 PNGs per
  forcing, 10 per d01/d02/d03, stamp standardized_compare_20260630T214000Z.
- RAP-only is blocked before real.exe; do not rerun unchanged.
- ERA5 is blocked locally by missing brc-tools source support, CDS Python
  tooling, and CDS credentials; WPS has a plausible Vtable.ECMWF.
- FNL has not been tried and is optional third-source work.

If no newer human instruction exists, inspect the paired NAM/GFS quicklooks and
prepare a concise science-review packet. Do not add downloader/staging logic
here.

Hard stop: do not run downloads, staging, WPS, real.exe, wrf.exe, sbatch,
NetCDF-heavy reads, archive inventories, or quicklooks without explicit
approval for that exact action.
```

## Prompt B: Optional Third Source In `brc-tools`

Use this when opening `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-tools`.

```text
cwd=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-tools

Goal: only if John explicitly asks for a third Pelican NWP source, implement
the smallest no-run FNL source-support pass. GFS analysis is already staged and
completed through WRF in brc-wrf; do not redo it.

First read:
1. git status --short --branch --untracked-files=no
2. docs/WRF-STAGING-STATE-PLAYBOOK.md
3. docs/WRF-INPUT-STAGING.md
4. docs/nwp/NWP-SOURCE-MATRIX.md
5. docs/walkthroughs/wrf-staging.md
6. ../brc-wrf/brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md
7. ../brc-wrf/doc/BRC_WRF_MICROTASK_HANDOFF.md

Environment guardrail:
- Use conda run -n brc-tools-2026 python ...
- Use conda run -n brc-tools-2026 pytest ...
- Do not use bare python/pytest or an inherited shell env.

Task:
1. Preserve existing RAP and GFS proof changes and unrelated local dirt.
2. Do a no-download FNL feasibility pass for 2013-02-02 12-18Z:
   source access path, Herbie/NCEI/RDA support, cadence, likely WPS Vtable,
   and whether pressure, humidity, winds, temperature, land/sea mask,
   soil temperature/moisture, snow/ice, and skin/surface fields are available.
3. If source support is missing, patch only brc-tools with the smallest
   source/staging support step: metadata/source matrix/offline plan/tests.
4. Stop before live downloads, staging, DTN work, manifest hashing of large
   files, WPS, real.exe, wrf.exe, Slurm, NetCDF-heavy reads, and quicklooks.

Return to brc-wrf with:
- feasibility verdict,
- proposed case name,
- manifest/contract shape or exact blocker,
- likely WPS Vtable,
- exact approval text for the next stage.
```

## Next Review Prompt

```text
Inspect the completed NAM/GFS standardized quicklooks for the Pelican 2013
12-18Z, 3/1/0.333 km, 75-level hot-swap lane and summarize the forcing
sensitivity.

Use the paired quicklook roots under standardized_compare_20260630T214000Z.
Do not rerun downloads, staging, WPS, real.exe, wrf.exe, source-family
experiments, or unbounded archive searches unless explicitly approved.
```
