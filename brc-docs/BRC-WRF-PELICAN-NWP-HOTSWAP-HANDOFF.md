# Pelican NWP Hot-Swap State

This is the canonical Pelican 3/1/0.333 km, 75-level NWP forcing and terrain
state note.

It supersedes older one-off context files. Keep durable verdicts and run facts
here; keep copy-paste prompts and disposable next-session handoffs in
`.local-handoffs/`, `scratch-handoffs/`, or `/tmp`, then migrate only durable
facts back into the owner docs.

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

Current helper surface: `brc-cases/wps_hgt_static.py` can plan 3s WPS tile
coverage, query USGS terrain metadata, de-duplicate a URL manifest, cache DEMs
from a Slurm/DTN job, build WPS-format `topo_brc_custom_3s/`, and render the
run-local `GEOGRID.TBL` and `namelist.wps` edits. It does not submit Slurm, run
WPS/geogrid, or write generated data inside the checkout.

Dataset search verdict from 2026-07-07:

```text
local search: no usable DEM rasters found under bounded scratch input searches;
  shared WPS_GEOG exposes topo_gmted2010_30s; the archived topo_gmted2010_5m
  overlay remains only an operator-proof/control-path artifact.
helper plan: bounds -114 37 -105 44 require 63 WPS 3s HGT_M output tiles.
preferred source: USGS NED/3DEP 1 arc-second DEM GeoTIFF from The National Map;
  API dataset token is "National Elevation Dataset (NED) 1 arc-second".
  The expanded WPS-border query de-duplicates to 99 one-degree source tiles,
  about 4.53 GiB from metadata for the current Pelican broad box. Confirm
  vertical datum and meters from downloaded tile metadata before build.
fallback source: NASADEM_HGT or SRTMGL1 1 arc-second HGT from NASA LP DAAC;
  expect Earthdata/cloud access and a one-degree-tile cache of similar order.
smallest fallback: SRTMGL3 3 arc-second HGT; native target spacing, about
  60 MB compressed / 180 MB unpacked for 63 tiles, but lower source fidelity
  than 1 arc-second terrain resampled to 3s.
not preferred: Copernicus GLO-30/GLO-90 because it is a DSM including
  vegetation/buildings and carries registration plus attribution obligations.
next step: submit the rendered static-terrain Slurm packet; stop after source
  manifest, download inventory/checksums, size evidence, and
  topo_brc_custom_3s index verification. Geogrid is a separate step.
```

Static terrain packet evidence from 2026-07-07:

```text
case target: pelican2013_nam_3_1_333m_75lev_oneway_terrain3s
control packet: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s/control/terrain_static_20260707T222250Z/
download job: 13849489, completed 0:0 in 00:02:04 on dtn05
build job: 13849490, completed 0:0 in 00:03:01 on notch137
source manifest: 99 de-duplicated USGS NED 1 arc-second GeoTIFF rows
download inventory: 36 cached + 63 downloaded rows; 4 nonfatal TNM metadata size warnings
DEM cache: /scratch/general/vast/u0737349/wrf_inputs/pelican2013_terrain3s/usgs_3dep_1arcsec/ = 4.6G
WPS static output: /scratch/general/vast/u0737349/wps_geog_terrain3s/topo_brc_custom_3s/ = 350M
WPS output files: 64 top-level files, meaning 63 WPS tiles plus index
index proof: type=continuous, projection=regular_ll, dx=dy=0.000833333333333333, wordsize=2, tile_bdr=3, units="meters MSL"
important caveat: no geogrid.exe has run against this source yet
next stop: geogrid-only proof that WPS uses brc_custom_3s/topo_brc_custom_3s for HGT_M
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
