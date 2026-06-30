# Pelican Alternate Forcing

Use this when the goal is to rerun the completed Pelican 3/1/0.333 km triple
nest with a different IC/LBC forcing source.

Status: no-run routing and RAP feasibility review. This is not approval to
stage GRIBs, run WPS, submit Slurm, run `real.exe` or `wrf.exe`, inspect
NetCDF-heavy artifacts, or render new forcing quicklooks.

## Prompt

```text
cwd=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf

Goal: rerun the completed Pelican 3/1/0.333 km triple-nest setup one forcing
source at a time, keeping domain, physics, vertical levels, run length,
archive/quicklook products, and comparison workflow as identical as possible.
Do not run anything until I explicitly approve the first source.

First read:
1. AGENTS.md
2. README.md
3. brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md
4. brc-docs/BRC-WRF-PELICAN-ALTERNATE-FORCING.md
5. brc-cases/README.md
6. ../brc-tools/docs/WRF-INPUT-STAGING.md
7. ../brc-tools/docs/HANDOFF-TO-BRC-WRF.md

Use the same target setup:
- Case family: Pelican 2013 triple nest
- Domains: 3 km / 1 km / 0.333 km
- Vertical levels: 75
- Window: 2013-02-02_12:00:00 to 2013-02-02_18:00:00 UTC
- Init: 2013-02-02_12:00:00 UTC where supported
- Keep WRF physics/time-step choices matching the prior successful 333 m run
  unless stability forces a documented change.
- Quicklooks: standardized 10 PNGs per available domain under
  <archive-run>/quicklooks/<stamp>/dXX/.

Baseline to compare against:
- Case: pelican2013_nam_3_1_333m_75lev
- Full archive:
  /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/
- Current standardized baseline quicklooks:
  /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/quicklooks/standardized_20260629T020921Z/
- Control files:
  /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/control/run_20260626T144836Z/

Run sources in this priority order, one at a time:
1. RAP analysis
2. ERA5
3. GEFSv12 reforecast members as their own source, not the parked GEFS+NAM
   two-stream filler design
4. GFS/FNL
5. CFSv2
6. NARR

For each source:
1. Do a no-run feasibility check first: data availability for
   2013-02-02 12-18Z, cadence, WPS Vtable availability, required WRF fields,
   soil/snow/skin-temperature coverage, and brc-tools staging support.
2. If unsupported in brc-tools, do not add staging or downloader logic to
   brc-wrf. Propose the smallest brc-tools change instead.
3. Draft or update a case manifest with a source-specific case name, such as
   pelican2013_rap_3_1_333m_75lev.
4. Render/review WPS and Slurm scripts only.
5. Stop and ask for approval before DTN staging, WPS, real.exe, wrf.exe,
   sbatch, NetCDF-heavy checks, or quicklook rendering.
6. After each approved run, compare against the NAM 333 m baseline using the
   same quicklook products and archive layout.
7. Do not proceed to the next forcing source until the current source is
   complete, blocked with evidence, or explicitly skipped.

Scientific constraint:
Treat this as changing the IC/LBC forcing source, not only swapping wrfinput.
WRF initial conditions and lateral boundaries should remain internally
consistent unless I explicitly ask for a controlled perturbation experiment.

First task only:
Start with RAP analysis. Use the feasibility memo in this file, then continue
the no-run WRF-side review: Vtable candidate, field-risk checklist,
source-specific case manifest, rendered scripts, and exact approval request for
the smallest next staging/WPS proof. Do not submit, stage, run WPS/WRF, or
render new forcing quicklooks yet.
```

## RAP Feasibility

The adjacent `brc-tools` branch `feat/wrf-rap-source` now adds `rap_analysis`
as a whole-file hourly analysis source, derives `interval_seconds = 3600` and
`wps_fg_name = ["RAP"]`, and records live NCEI availability evidence for all
seven 2013-02-02 12-18Z RAP cycles. That proves source discovery and contract
shape; it does not prove a WRF run.

Target window:

```text
2013-02-02_12:00:00 to 2013-02-02_18:00:00 UTC
domains: 3 km / 1 km / 0.333 km
vertical levels: 75
baseline case: pelican2013_nam_3_1_333m_75lev
```

Local support:

```text
brc-tools WRF staging sources found: nam_analysis, gefs_reforecast, rap_analysis
RAP staging source found: yes, on branch feat/wrf-rap-source
RAP manifest/contract schema proof found: yes, offline tests in tests/test_wrf_staging.py
RAP WPS Vtable decision found: partial candidates only
RAP soil/snow/skin-temperature field proof found: no
```

WPS Vtable candidates in the John-owned WPS root:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS

Generic Vtable.RAP: missing
Candidate RAP tables present:
- Vtable.RAP.hybrid.ncep
- Vtable.RAP.pressure.ncep
- Vtable.RAP.sigma.gsd
- Vtable.raphrrr
```

Inference: for 2013-02-02 12-18Z, the simplest staged candidate is hourly RAP
13 km analysis `f000` files from NCEI through the deterministic URL template
encoded in `brc-tools`. The exact Vtable and field adequacy remain WRF-side
review items before WPS approval.

## Completed `brc-tools` Step

Do not route RAP through the older GEFS reforecast staging path. That path
assumes per-variable forecast-bucket files, integer ensemble members, and
GEFS-specific remote URLs. RAP analysis should instead follow the NAM analysis
shape: one whole GRIB per analysis cycle, staged under:

```text
<output_root>/<case>/rap_analysis/rap_130_<YYYYMMDD_HHMM>_000.grb2
```

Implemented in `../brc-tools` on `feat/wrf-rap-source`:

1. Added `[models.rap_analysis]` to `brc_tools/nwp/lookups.toml` with hourly
   cadence, product/source metadata for 13 km NCEI RAP analysis, and a
   deterministic filename/URL template.
2. Generalized the NAM whole-file analysis staging path so
   `--source rap_analysis --plan` can enumerate 2013-02-02 12Z through 18Z
   files offline.
3. Made `build_contract()` derive `interval_seconds = 3600` and
   `wps_fg_name = ["RAP"]` from source metadata instead of stamping non-NAM
   sources as GEFS.
4. Added mocked unit tests for lookup parsing, offline plan shape, contract
   shape, and no-network staging behavior.

That branch completed the live availability preflight and stopped before DTN
staging, WPS, or WRF execution.

## Next Approval Boundary

The next no-run `brc-wrf` batch can proceed without execution approval:

```text
Repo: brc-wrf
Work: choose/review RAP Vtable candidate, define field-adequacy checklist,
      draft pelican2013_rap_3_1_333m_75lev case manifest, render/review scripts
No: GRIB download, DTN staging, WPS, real.exe, wrf.exe, sbatch run conveyor,
    NetCDF-heavy reads, or RAP quicklook rendering
Stop point: report case manifest diff, contract expectations, Vtable candidate,
            field-risk checklist, and exact approval text for staging/WPS
```

Minimum facts still needed before approved staging or WPS:

- WPS Vtable and `fg_name`/prefix choice.
- Required WRF fields, especially land-sea mask, soil levels, snow depth, snow
  water, SST/skin temperature, pressure, humidity, and winds.
- Whether RAP alone is internally complete, or whether a second filler stream is
  scientifically intended.
