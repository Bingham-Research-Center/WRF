# BRC WRF Domain Preview SOP

Use this when the next decision is domain geometry, not forcing or model
physics. The goal is a cheap review PNG from WPS `geogrid.exe`, then a hard stop
before any NAM staging, `ungrib`, `metgrid`, `real.exe`, or `wrf.exe`.

## Boundary

This is approved off-login WPS work only when a human explicitly asks to see the
domain. It may read WPS geography and write `geo_em.d0*.nc` on scratch. It must
not download GRIB, hash manifests, inspect NetCDF archives, run quicklooks from
WRF output, run `real.exe`, run `wrf.exe`, or submit a full WRF wrapper.

Keep generated Slurm scripts, WPS run directories, PNGs, logs, and `geo_em`
files out of the git checkout.

## Storage

Use scratch for active WPS files:

```text
/scratch/general/vast/$USER/wrf_runs/<case>/domain_preview/wps_run/
```

Use durable group storage for the review packet:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/<case>/domain_review/geogrid_<UTC>_<jobid>/
```

The durable packet should contain at least:

| File | Purpose |
| --- | --- |
| `domain_preview.png` | Terrain map with nested-domain footprint. |
| `namelist.wps` | Exact domain geometry and case window used by `geogrid.exe`. |
| `geogrid.log` | WPS completion and optional-field messages. |
| `domain_preview_summary.tsv` | Host, job id, source SHA, paths, and stop point. |
| `file_inventory.tsv` | Small inventory of scratch preview outputs. |

## Current Reviewed Seed

The first approved preview used the original NAM-only 12/4 km nested Basin
geometry with the shortened requested window:

```text
case: feb2013_basin_nam_12_4km
start: 2013-02-01_12:00:00
end:   2013-02-03_00:00:00
```

The geogrid settings were seeded from the validated Jan-2013 Basin proof:

```text
max_dom = 2
parent_grid_ratio = 1, 3
i_parent_start = 1, 50
j_parent_start = 1, 40
e_we = 150, 151
e_sn = 120, 121
dx = 12000
dy = 12000
ref_lat = 40.45
ref_lon = -109.50
stand_lon = -109.50
geog_data_path = /uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/
```

For the later NAM WPS stage, keep `prefix = 'NAM'` and `fg_name = 'NAM'`
paired. The old proof scratch used `FILE`/`FILE`; that remains historical
context, not a requirement for fresh NAM-only staging.

## 2026-06-25 Preview Evidence

Job `13679937` ran on `notch392` and completed `0:0` in `00:01:02`. It ran
`geogrid.exe`, rendered a PNG, archived the review packet, and stopped before
`ungrib`, `metgrid`, `real.exe`, and `wrf.exe`.

Durable packet:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/feb2013_basin_nam_12_4km/domain_review/geogrid_20260625T181644Z_13679937/
```

PNG:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/feb2013_basin_nam_12_4km/domain_review/geogrid_20260625T181644Z_13679937/domain_preview.png
```

Observed footprint: d01 terrain background with a d02 4 km nest covering the
Uinta Basin core around Duchesne, Roosevelt, and Vernal. This is the review
point for chopping `e_we`/`e_sn` or shifting `i_parent_start`/`j_parent_start`
before spending time on NAM staging and model execution.

## Edit Loop

For a domain-size adjustment:

1. Edit only the domain geometry in `namelist.wps`.
2. Re-run only `geogrid.exe`.
3. Regenerate only `domain_preview.png`.
4. Compare footprints and stop for review.

Do not advance to `ungrib` or `metgrid` until the footprint is accepted.
