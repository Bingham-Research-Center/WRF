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
pelican2013_nam_3_1_333m_75lev_oneway_terrain5m  # complete overlay proof; HGT_M from topo_gmted2010_5m
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
case: pelican2013_nam_3_1_333m_75lev_oneway_terrain5m
run_id: run_20260707T182414Z
WPS proof job: 13847970; geogrid/ungrib/metgrid all completed, batch failed only in a post-summary Python block
WRF job: 13847980; completed 0:0 in 02:17:41 on notch392
quicklook job: 13848733; completed 0:0 in 00:01:06
control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain5m/control/run_20260707T182414Z/
WPS archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain5m/wps_run_run_20260707T182414Z_13847970/
WRF archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain5m/full6h/run_20260707T182414Z/
quicklooks: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain5m/full6h/run_20260707T182414Z/quicklooks/dXX/
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
control-path rule: copy the 13847980 control shape, but render fresh terrain3s wrappers; do not copy literal terrain5m script path strings because archived wrapper internals still carry topo5m/hires_terrain labels
stop rule: run geogrid-only first; do not submit WRF until geogrid.log and geo_em metadata prove custom 3s HGT_M was used
comparison anchors: NAM one-way job 13788264, operator-proof topo5m job 13847980, and quicklooks from job 13848733
```

Current helper surface: `brc-cases/wps_hgt_static.py` can plan 3s WPS tile
coverage, query USGS terrain metadata, de-duplicate a URL manifest, cache DEMs
from a Slurm/DTN job, build WPS-format `topo_brc_custom_3s/`, and render the
run-local `GEOGRID.TBL` and `namelist.wps` edits. For 3 arc-second global-style
tiles it must emit WPS `filename_digits = 6` in the static `index` so geogrid
looks for six-digit tile names such as `295201-296400.152401-153600`. It does
not submit Slurm, run WPS/geogrid, or write generated data inside the checkout.

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
status: source selection, static-terrain build, and geogrid-only proof are
  complete; next work is the WRF conveyor only after explicit approval.
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
index proof: type=continuous, projection=regular_ll, dx=dy=0.000833333333333333, wordsize=2, filename_digits=6, tile_bdr=3, units="meters MSL"
```

Geogrid-only proof evidence from 2026-07-07:

```text
first proof job: 13849698 completed geogrid but produced all-zero HGT_M; cause was missing filename_digits=6 in the custom static index, so WPS used the brc_custom_3s token but looked for five-digit tile names and filled HGT_M with fill_missing=0
corrected proof job: 13849737 on notch392; geogrid phase exit 0 in 10 s
control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s/control/geogrid_20260707T230301Z/
archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s/domain_review/geogrid_20260707T230301Z_13849737/
scratch WPS run: /scratch/general/vast/u0737349/wrf_runs/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s/geogrid_20260707T230301Z/wps_run/
source proof: geogrid.log says "Using brc_custom_3s data source for HGT_M." for d01, d02, and d03
HGT_M summary: d01 min/mean/max = 1113.251/2122.432/3879.707 m; d02 = 1417.477/2084.941/3823.632 m; d03 = 1414.842/1558.500/2148.225 m
terrain comparison: d03 terrain3s minus 30s mean_abs = 5.103 m, range -36.682 to 68.782 m; d03 terrain3s minus topo5m mean_abs = 27.531 m, range -122.784 to 235.096 m
preview: terrain3s_hgt_and_diffs.png in the corrected archive, comparing HGT_M and differences against installed 30s and topo5m
historical stop point: geogrid only; the later full conveyor is recorded below
```

Terrain3s conveyor completion and current physics-bridge controls:

```text
terrain3s WPS job: 13851884, completed 0:0
terrain3s WRF job: 13852034, completed 0:0 with 21 hourly wrfout files
terrain3s quicklook job: 13852773, completed with 42 PNGs
terrain3s archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s/full6h/run_20260708T021809Z/

terrain3s two-way control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_twoway_terrain3s/control/run_20260710T084413Z/
terrain3s two-way normalized diff: feedback 0 -> 1 only; smooth_option remains 0; slope/shading and MYJ/Eta remain off
terrain3s two-way preparation job: 13880432, completed 0:0 in 00:00:12 with six met_em files
terrain3s two-way WRF job: 13880435, completed 0:0 in 01:44:43; real.exe 28 s; wrf.exe 6214 s
terrain3s two-way WRF proof: 21 hourly wrfout files, SUCCESS COMPLETE WRF, all executable/runtime provenance checks PASS, empty archived error-marker scan
terrain3s two-way archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_twoway_terrain3s/full6h/run_20260710T084413Z/
terrain3s two-way quicklook job: 13881153, completed 0:0 in 00:01:30
terrain3s two-way quicklook proof: 54 PNGs = 30 standard + 12 supplemental + 12 _4h_energy; manifest verification 2/2 OK
terrain3s two-way quicklook summary: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_twoway_terrain3s/control/run_20260710T084413Z/quicklook_summary_13881153.tsv
terrain3s paired diagnostic job: 13881198, completed 0:0 in 00:00:50 with 189 field/time/domain rows, zero nonfinite values, and 12 figures
terrain3s paired diagnostic artifact: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_twoway_terrain3s/control/run_20260710T084413Z/review_oneway_vs_twoway_13881198/
terrain3s d03 late response: at 16/17/18Z, two-way minus one-way mean T2 = +0.037/-0.003/-0.023 K, mean PBLH = +1.36/+0.47/+0.91 m, and mean 10 m wind speed = -0.016/-0.015/+0.007 m s-1
terrain3s d03 locality/noise: local T2, PBLH, and wind responses are non-null and often more than 10 cells from the outer boundary, but adjacent-cell p99 roughness remains comparable between one-way and two-way
terrain3s d03 shortwave response: cells exceeding |20 W m-2| = 462/960/1658 of 22500 at 16/17/18Z (2.1/4.3/7.4%), mostly more than 10 cells from the outer boundary
terrain3s feedback science stop: human figure review and a parent-nest-footprint mask remain; mechanical completion and descriptive diagnostics are not yet a manuscript verdict

slope treatment control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope/control/run_20260710T003606Z/
slope+MYJ treatment control: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope_myj/control/run_20260710T003606Z/
slope preparation job: 13876527, completed 0:0 in 00:00:18
slope WRF job: 13876534, completed 0:0 in 01:45:09; real.exe 30 s; wrf.exe 6233 s
slope WRF proof: 21 hourly wrfout files, SUCCESS COMPLETE WRF, empty archived error-marker scan
slope archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope/full6h/run_20260710T003606Z/
slope quicklook job: 13877355, completed 0:0 in 00:01:26
slope quicklook proof: 54 PNGs = 30 standard + 12 supplemental + 12 _4h_energy
slope quicklook summary: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope/control/run_20260710T003606Z/quicklook_summary_13877355.tsv
quicklook environment: clyfar-nov2025 with PYTHONPATH pointed at ../brc-tools
quicklook check note: manifest verification 2/2 OK; nonfatal warning reported the six retained met_em files in the prepared scratch run as stale
review diagnostic job: 13877599, completed 0:0 in 00:00:38 on notch392
review artifact: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope/control/run_20260710T003606Z/review_control_vs_slope_13877599/
review proof: 189 field/time/domain rows; zero nonfinite values; paired surface, time-series, vertical-section, and Horsepool-profile figures
review recommendation: GO for slope+MYJ/Eta, with lateral-boundary surface outliers retained as an analysis caveat

slope+MYJ incremental diff: bl_pbl_physics 1 -> 2 and sf_sfclay_physics 1 -> 2 only; Noah sf_surface_physics remains 2
slope+MYJ preparation job: 13879078, completed 0:0 in 00:00:15
slope+MYJ WRF job: 13879100, completed 0:0 in 01:41:53; real.exe 28 s; wrf.exe 6047 s
slope+MYJ WRF proof: 21 hourly wrfout files, SUCCESS COMPLETE WRF, all provenance checks PASS, empty error-marker scan
slope+MYJ archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope_myj/full6h/run_20260710T003606Z/
slope+MYJ quicklook job: 13879973, completed 0:0 in 00:01:15
slope+MYJ quicklook proof: 54 PNGs = 30 standard + 12 supplemental + 12 _4h_energy
slope+MYJ quicklook summary: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope_myj/control/run_20260710T003606Z/quicklook_summary_13879973.tsv
slope+MYJ publication generator: 13879669, completed 0:0 in 00:11:53; 604 tasks and no per-figure errors
slope+MYJ publication convergence: 13880154, completed 0:0 in 00:00:19; every seven-case task up to date
slope+MYJ publication inventory: 63 PNGs per case x 7 = 441 per-case PNGs; cross-case root = 184 PNGs; total = 625 PNGs
slope+MYJ paired diagnostic job: 13880122, completed 0:0 in 00:00:40; 189 field/time/domain rows, zero nonfinite values, 12 figures
slope+MYJ paired diagnostic artifact: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway_terrain3s_slope_myj/control/run_20260710T003606Z/review_slope_vs_myj_13880122/
slope+MYJ preliminary response: coherent, non-null low-level physics sensitivity; MYJ lowers d03 mean PBLH by 33-75 m from 16-18Z and makes PBLH substantially patchier
current stop point: human science review of the completed physics suite and terrain3s feedback pair; no additional WRF treatment is authorized

publication figure job: 13877404, TIMEOUT with exit 0:0 after 02:00:13 on notch392
publication figure end: 2026-07-09 23:29:03 MDT; stderr records cancellation due to the Slurm time limit
publication figure logs: /scratch/general/vast/u0737349/pelican_figures_13877404.{out,err}
publication figure stdout proof: start line only; no completion line or Python traceback
publication figure partial slope output: 23 PNGs = 6 sections + 6 upperair + 11 surface
publication figure partial cross-case output: 4 PNGs = 1 profile + 1 heat-deficit + 2 Horsepool skew-Ts
publication figure last progress: theta2m_nam_terrain3s_slope_multidomain_14z.png at 2026-07-09 21:32:32 MDT
publication figure initial verdict: failed partial batch, not an accepted complete figure set
publication recovery job: 13878948, cancelled after a second reproducible long-process stall in 00:06:14; 87 newly completed PNGs were preserved
publication isolated proof: 13878999 completed 0:0 in 00:00:17; the previously blocked 12Z slope/control difference rendered successfully
publication bounded completion: 13879006 and 13879007 completed 0:0 in 00:00:21 and 00:00:22, filling the remaining slope/control differences through 18Z
publication convergence check: 13879016 completed 0:0 in 00:00:29 with every selected six-case product up to date
publication final inventory: 63 PNGs per completed case x 6 cases = 378 per-case PNGs; cross-case compare root = 156 PNGs; total = 534 PNGs
publication final verdict: complete for GFS, NAM, NAM one-way, terrain5m, terrain3s, and slope/shading; slope+MYJ/Eta was excluded because it was still unrun during that publication recovery, and its later completion is recorded above
```

The first treatment adds only `slope_rad`, `topo_shading`, and `shadlen`.
The second retains those settings and changes YSU/revised-MM5 to MYJ/Eta.
Both reuse the accepted terrain3s `met_em` inputs and keep FDDA off. The paper
text does not document the three terrain-radiation namelist values, so call
these Tran-inspired bridge treatments, not reproductions.

The completed control-versus-slope review found the following:

- From 16-18Z, d03 mean `SWDOWN` changes were `-0.010`, `-0.117`, and
  `-0.250 W m-2`; only 7, 4, and 34 of 22,500 cells respectively exceeded
  `|20 W m-2|`. The visually darkest absolute cells were already dark in the
  control (for example `87.18` versus `87.02 W m-2` at 16Z), while the actual
  treatment response formed small terrain-aligned 1-5-cell components.
- D03 `GLW`, `HFX`, and `LH` differences followed the shortwave terrain
  pattern without domain-wide energy collapse. At 18Z their mean changes were
  `+0.212`, `+0.339`, and `+0.036 W m-2` respectively.
- D03 T2 mean absolute differences were `0.065`, `0.031`, and `0.033 K` at
  16-18Z; 2 m theta was similar. The roughly `-6 K` minima were confined to
  the outermost one-cell lateral boundary strip by 17-18Z. The largest d02 T2
  response (`-8.86 K`) was also one cell from its boundary.
- D03 PBLH mean absolute differences stayed at `1.36-1.77 m` from 16-18Z and
  10 m wind at `0.017-0.023 m s-1`. Local tails followed terrain/boundary
  features; no d03 wind difference reached `1 m s-1`.
- Across all 75 d03 levels, theta mean absolute differences were
  `0.0021-0.0048 K` from 16-18Z. Central EW/NS sections were about
  `+/-0.04 K`, the Horsepool 16/18Z profiles differed by less than about
  `0.02 K`, and no d03 value exceeded `1 K`.
- Adjacent-cell p99 jumps remained comparable between control and treatment.
  The extreme surface-temperature/PBLH tails at parent and nest boundaries are
  real review caveats, but they do not propagate into the basin-interior
  thermal column or constitute a pathological domain collapse.

The user approved treatment 2 after this review, and the slope+MYJ/Eta run and
base quicklooks completed as recorded above. The next owner is the paired
science/figure workflow; this completion is not approval for another WRF run.

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
