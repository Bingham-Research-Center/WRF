# Pelican Alternate Forcing

Use this when the goal is to rerun the completed Pelican 3/1/0.333 km triple
nest with a different IC/LBC forcing source.

Status: RAP contract staged and consumed by a `brc-wrf` review case; two
approved WPS-only RAP proofs ran on 2026-06-30 and blocked before `real.exe`
because RAP-only field adequacy failed. This is not approval to run WPS, submit
Slurm, run `real.exe` or `wrf.exe`, inspect NetCDF-heavy artifacts, or render
new forcing quicklooks.

## Active Prompt Moved

Do not use an older RAP-first prompt for new work. The current paste-ready
handoff is `brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md`.

This file preserves the Pelican alternate-forcing background, RAP feasibility
memo, RAP WPS proof evidence, and ERA5/GFS/FNL notes only.

## RAP Feasibility

The adjacent `brc-tools` repo now has `rap_analysis` as a whole-file hourly
analysis source, derives `interval_seconds = 3600` and
`wps_fg_name = ["RAP"]`, and staged the seven 2013-02-02 12-18Z RAP cycles on
scratch with manifest verification evidence. That proves source discovery,
staging, and contract shape; it does not prove WPS field adequacy or a WRF run.

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
RAP staged contract found: yes, /scratch/general/vast/$USER/wrf_inputs/pelican2013_rap_3_1_333m_75lev/
RAP manifest/contract proof found: yes, 7 hourly RAP-130 files; contract says wps_fg_name ["RAP"] and interval_seconds 3600
RAP WPS Vtable proof found: yes, hybrid job 13744756 and pressure job 13745030
RAP soil/snow/skin-temperature field proof found: failed for RAP-only; pressure output has NUM_METGRID_SOIL_LEVELS = 0
```

WPS Vtable candidates in the John-owned WPS root:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS

Generic Vtable.RAP: missing
Tested candidate:
- Vtable.RAP.hybrid.ncep
Other tested/fallback candidate:
- Vtable.RAP.pressure.ncep
Other RAP tables present:
- Vtable.RAP.sigma.gsd
- Vtable.raphrrr
```

Inference: for 2013-02-02 12-18Z, the simplest staged candidate is hourly RAP
13 km analysis `f000` files from NCEI through the deterministic URL template
encoded in `brc-tools`. That single `rap_130` stream is not complete WRF input
as currently staged. The hybrid table did not produce a real-ready 3D
atmosphere, while the pressure table produced 38 atmospheric levels but no
layered soil temperature/moisture fields.

## Completed `brc-tools` Step

Do not route RAP through the older GEFS reforecast staging path. That path
assumes per-variable forecast-bucket files, integer ensemble members, and
GEFS-specific remote URLs. RAP analysis should instead follow the NAM analysis
shape: one whole GRIB per analysis cycle, staged under:

```text
<output_root>/<case>/rap_analysis/rap_130_<YYYYMMDD_HHMM>_000.grb2
```

Implemented in `../brc-tools`:

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

That work completed source support, live availability preflight, staging, and
manifest/contract verification, then stopped before WPS or WRF execution.

## ERA5 And Fast Fallback

No local ERA5 staging support is ready yet. The sibling `brc-tools` source
registry currently has `nam_analysis`, `gefs_reforecast`, and `rap_analysis`
for WRF staging, but no `era5` key. `brc-tools-2026` can run Herbie 2026.3.0,
but it still lacks `cdsapi`/`ecmwfapi`, and no CDS credentials are configured
in the inherited environment or `~/.cdsapirc`.

WRF-side ERA5 support is plausible: John's WPS root has `Vtable.ECMWF`, which
maps pressure-level atmosphere plus land mask, skin/SST, sea ice, snow, and
four soil temperature/moisture layers when the ERA5 request includes both
pressure-level and surface/land products. The blocker is access/tooling and
source support in `brc-tools`, not the WPS table itself.

GFS analysis is no longer hypothetical. The staged GFS contract ran through
WPS, `real.exe`, `wrf.exe`, archive, and paired NAM/GFS standardized quicklooks
on 2026-06-30. FNL remains optional third-source work if John wants another
independent forcing after reviewing the NAM/GFS pair.

## Next Approval Boundary

The no-run `brc-wrf` consumption batch has a case manifest and RAP field memo,
plus a renderer for reproducible WPS-only proof packets:

```bash
python brc-cases/wrf_case.py render-wps-field-proof \
  brc-cases/pelican2013_rap_3_1_333m_75lev.case.yaml \
  --output-dir /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_rap_3_1_333m_75lev/control/wps_field_proof_<UTC>
```

The next RAP-specific executed step is not `real.exe`. It needs an explicit
source/design decision first:

```text
Repo: brc-wrf
Work: choose one corrected RAP source product or one explicit RAP-plus-filler
      design, then run one WPS-only field-adequacy proof
No: real.exe, wrf.exe, full run conveyor, or RAP quicklook rendering
Stop point: report met_em field list, num_metgrid_levels, layered soil fields,
            metgrid warnings, and whether the corrected design satisfies the
            field checklist
```

Minimum facts still needed before approved `real.exe`:

- Required WRF fields, especially layered soil temperature/moisture, snow/ice
  treatment, land mask, pressure, humidity, and winds.
- Whether RAP alone can be staged as internally complete, or whether a second
  filler stream is scientifically intended.
