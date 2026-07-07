# Pelican NWP Hot-Swap Handoff

This is the current paste-ready handoff for tracking Pelican 3/1/0.333 km,
75-level NWP forcing hot-swaps.

It supersedes older one-off context files. Keep this file as the active Pelican
source verdict and review prompt.

## Current Verdict

| Source family | Verdict | Next action |
| --- | --- | --- |
| NAM baseline | Complete. `pelican2013_nam_3_1_333m_75lev` is the comparison anchor. | Preserve as baseline. |
| NAM one-way feedback | Complete. `pelican2013_nam_3_1_333m_75lev_oneway` reused the NAM forcing/WPS artifacts and changed only `feedback = 1` to `feedback = 0` in `namelist.input`. | Review against the two-way NAM baseline quicklooks. |
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
pelican2013_nam_3_1_333m_75lev_oneway  # complete WRF feedback=0 sensitivity
pelican2013_nam_3_1_333m_75lev_oneway_hires_terrain  # complete overlay proof; HGT_M from topo_gmted2010_5m
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

Supplemental comparison quicklooks:

```text
job: 13792197, completed from log evidence on notch392
summary: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_gfs_compare/control/quicklooks_supplemental_20260702T082027Z/quicklook_supplemental_summary_13792197.tsv
NAM/GFS supplemental roots: same standardized_compare_20260630T214000Z/dXX/ domain roots, with nested {_600hPa,_4h}/ folders
NAM one-way supplemental root: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/full6h/run_20260702T053120Z/quicklooks/dXX/{_600hPa,_4h}/
```

NAM one-way feedback run and quicklooks:

```text
run job: 13788264, completed 0:0 in 02:12:32 on notch392
quicklook retry job: 13791045, completed 0:0 in 00:00:53
archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/full6h/run_20260702T053120Z/
control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/control/run_20260702T053120Z/
quicklooks: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/full6h/run_20260702T053120Z/quicklooks/dXX/
namelist diff: feedback = 1 -> feedback = 0 only; smooth_option retained at 0
```

The stamped folder above is historical. Future renders default to the simpler
`<archive-run>/quicklooks/dXX/` layout unless an explicit `--output-dir` is
needed to preserve a second render.

## Terrain-Fidelity Variant

Requested lane: repeat the successful NAM one-way feedback run shape, but
increase WPS terrain fidelity before `metgrid` and WRF. The reference run is
job `13788264`; its control packet reused the NAM baseline WPS/metgrid products
and changed only `feedback = 1` to `feedback = 0`. A terrain-fidelity rerun must
not reuse those old `met_em` files.

Initial local finding from 2026-07-07:

```text
namelist.wps baseline geog_data_res: 'default','default','default'
baseline WPS_GEOG: /uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/
installed HGT_M terrain: topo_gmted2010_30s only
GEOGRID.TBL default HGT_M path: topo_gmted2010_30s/
installed terrain-related VAR_SSO fields: varsso, varsso_10m, varsso_5m, varsso_2m
```

Resolution for the completed operator-proof run: avoid a full private GEOG copy.
The run-local GEOG overlay symlinks
the shared `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG` directories
and adds only `topo_gmted2010_5m`, exposed to WPS through the short scratch link
`/scratch/general/vast/u0737349/wps_geog_topo5m`. The run-local
`GEOGRID.TBL.ARW` adds `gmted2010_5m` only for `HGT_M`; other static fields
fall through to `default`. Important correction: WPS `5m` is 5 arc-minutes, not
5 metres, so this run is coarser than the installed `topo_gmted2010_30s`
terrain and should be treated as an overlay/control-path proof rather than the
real fine-terrain sensitivity.

Current execution packet:

```text
case: pelican2013_nam_3_1_333m_75lev_oneway_hires_terrain
run_id: run_20260707T182414Z
WPS proof job: 13847970; geogrid/ungrib/metgrid all completed, batch failed only in a post-summary Python block
WRF job: 13847980; completed 0:0 in 02:17:41 on notch392
quicklook job: 13848733; completed 0:0 in 00:01:06
control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_hires_terrain/control/run_20260707T182414Z/
WPS archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_hires_terrain/wps_run_run_20260707T182414Z_13847970/
WRF archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_hires_terrain/full6h/run_20260707T182414Z/
quicklooks: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_hires_terrain/full6h/run_20260707T182414Z/quicklooks/dXX/
geogrid proof: "Using gmted2010_5m data source for HGT_M."
namelist carry-forward: feedback = 0; smooth_option = 0
WRF proof: SUCCESS COMPLETE WRF; 21 archived wrfout files; no fatal/CFL/NaN markers seen during monitoring
quicklook proof: 30 standard PNGs plus 12 supplemental PNGs; summary quicklook_hires_terrain_summary_13848733.tsv
```

Next terrain run handoff:

```text
standard WPS topography present/advertised: topo_gmted2010_30s and topo_gmted2010_5m
15s/3s/1s HGT_M status: custom WPS static terrain build required
recommended terrain source: custom 3 arc-second HGT_M
why not 15s first: only modestly finer than 30s and still near/coarser than d03 grid scale
why not 1s first: much larger download/tiling/geogrid cost; likely little added value before proving 3s matters on 333 m d03
approx Utah spacing at 40N: 15s ~463 m N-S / 355 m E-W; 3s ~93 m / 71 m; 1s ~31 m / 24 m
case name suggestion: pelican2013_nam_3_1_333m_75lev_oneway_terrain3s
control-path rule: copy the 13847980 control shape, but replace only the HGT_M terrain source, case names, run ids, and archive roots
stop rule: run geogrid-only first; do not submit WRF until geogrid.log and geo_em metadata prove custom 3s HGT_M was used
comparison anchors: NAM one-way job 13788264, operator-proof topo5m job 13847980, and quicklooks from job 13848733
```

Resolution choice tradeoff:

| HGT_M target | Effective spacing near Utah | Pros | Cons | Recommendation |
| --- | ---: | --- | --- | --- |
| `15s` | ~463 m N-S / ~355 m E-W | Smallest custom-data and geogrid cost; simple smoke test. | Barely finer than d03 `333 m`, only 2x better than `30s` east-west and still coarse north-south. | Skip unless toolchain risk is the main concern. |
| `3s` | ~93 m N-S / ~71 m E-W | Several DEM samples per d03 grid cell; strong enough to test terrain sensitivity without `1s` overhead. | Requires custom WPS terrain build; larger than `15s`. | First real science run. |
| `1s` | ~31 m N-S / ~24 m E-W | Best raw terrain fidelity; useful if 3s shows a meaningful terrain signal. | Most download/storage/tiling cost; WPS will still aggregate to 333 m. | Defer until 3s proves terrain matters. |

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

Goal: review the completed NAM, GFS, and NAM one-way Pelican 3/1/0.333 km,
75-level WRF runs using the rendered standard and supplemental quicklooks,
without rerunning blocked RAP-only or reviving GEFS+NAM unless explicitly
asked.

First read:
1. AGENTS.md
2. doc/BRC_WRF_EXPERIMENT_TODO.md
3. brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md
4. brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md
5. brc-cases/README.md
6. ../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md
7. ../brc-tools/docs/WRF-INPUT-STAGING.md
8. ../brc-tools/docs/nwp/NWP-SOURCE-MATRIX.md

Use doc/BRC_WRF_MICROTASK_HANDOFF.md only when detailed historical evidence is
needed.

Current source verdicts:
- NAM baseline is complete: pelican2013_nam_3_1_333m_75lev.
- NAM one-way feedback is complete: pelican2013_nam_3_1_333m_75lev_oneway,
  job 13788264, feedback=0 only, 30 quicklook PNGs from retry job 13791045.
- GFS analysis is complete: pelican2013_gfs_3_1_333m_75lev, job 13753673,
  NUM_METGRID_SOIL_LEVELS = 4, SUCCESS COMPLETE WRF.
- NAM/GFS standardized quicklooks are complete: job 13755401, 30 PNGs per
  forcing, 10 per d01/d02/d03, stamp standardized_compare_20260630T214000Z.
- Supplemental quicklooks are complete: job 13792197 added `_600hPa` and `_4h`
  folders under each domain root for NAM, GFS, and NAM one-way.
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
7. ../brc-wrf/doc/BRC_WRF_EXPERIMENT_TODO.md

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
