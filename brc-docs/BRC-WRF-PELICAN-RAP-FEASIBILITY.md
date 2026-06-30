# Pelican RAP Feasibility

Use this memo for the first Pelican 3/1/0.333 km alternate-forcing source:
RAP analysis for 2013-02-02 12-18Z. It is a WRF-side consumption review and
proof record, not standing approval to run WPS, `real.exe`, `wrf.exe`, Slurm,
NetCDF-heavy checks, or new quicklooks.

## Current State

The `brc-tools` side has staged and verified the RAP input bundle on scratch:

```text
/scratch/general/vast/$USER/wrf_inputs/pelican2013_rap_3_1_333m_75lev/
```

Observed sidecar facts from the staged contract generated at
`2026-06-30T02:39:11Z`:

| Item | Value |
| --- | --- |
| Case | `pelican2013_rap_3_1_333m_75lev` |
| Source | `rap_analysis` |
| Files | 7 hourly RAP-130 analysis files |
| Window | `2013-02-02T12:00:00Z` to `2013-02-02T18:00:00Z` |
| WPS `fg_name` | `RAP` |
| `interval_seconds` | `3600` |
| Manifest | `/scratch/general/vast/$USER/wrf_inputs/pelican2013_rap_3_1_333m_75lev/manifest_pelican2013_rap_3_1_333m_75lev.json` |
| Contract | `/scratch/general/vast/$USER/wrf_inputs/pelican2013_rap_3_1_333m_75lev/contract_pelican2013_rap_3_1_333m_75lev.json` |

The matching `brc-wrf` case manifest is:

```text
brc-cases/pelican2013_rap_3_1_333m_75lev.case.yaml
```

It intentionally marks `num_metgrid_levels` and `expected_met_em_count` as
`field_adequacy_pending` because those are metgrid/real proof facts, not
`brc-tools` contract facts.

The WPS-only approval packet is rendered from that manifest:

```bash
python brc-cases/wrf_case.py render-wps-field-proof \
  brc-cases/pelican2013_rap_3_1_333m_75lev.case.yaml \
  --output-dir /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_rap_3_1_333m_75lev/control/wps_field_proof_<UTC>
```

The generated Slurm wrapper requires `BRC_WPS_FIELD_PROOF_APPROVED=YES`, runs
only `ungrib.exe` and `metgrid.exe`, extracts the `met_em` field list and
`num_metgrid_levels`, and refuses to run `real.exe`, `wrf.exe`, quicklooks, or
the full conveyor.

Current external dependency: the packet reuses the NAM 333 m baseline
`geo_em.d0*.nc` files from
`/scratch/general/vast/$USER/wrf_runs/pelican2013_nam_3_1_333m_75lev/run_20260626T144836Z/wps_run/`.
If that scratch source disappears, restore those domain files or explicitly
approve a geogrid rerun before continuing the RAP proof.

## 2026-06-30 WPS Proof Results

John approved the RAP sensitivity attempt through Slurm on 2026-06-30, with the
condition that the workflow stop before unsafe WRF startup. Two WPS-only proofs
were submitted on `notch392`; neither ran `real.exe`, `wrf.exe`, quicklooks, or
the full run conveyor.

| Job | Vtable | WPS result | Field-adequacy result |
| --- | --- | --- | --- |
| `13744756` | `Vtable.RAP.hybrid.ncep` | `ungrib.exe` and `metgrid.exe` completed; 21 `met_em` files were written. | Failed: sample `met_em` header had no `num_metgrid_levels` dimension and no real-ready 3D atmospheric stack. |
| `13745030` | `Vtable.RAP.pressure.ncep` | `ungrib.exe` and `metgrid.exe` completed; 21 `met_em` files were written. | Partially passed: `num_metgrid_levels = 38` and 3D `PRES`, `GHT`, `RH`, `UU`, `VV`, and `TT` are present. Failed for WRF startup because layered soil temperature/moisture fields are absent and `NUM_METGRID_SOIL_LEVELS = 0`. |

Evidence paths:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wps_pelican2013_rap_3_1_333m_75lev_13744756.out
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wps_pelican2013_rap_3_1_333m_75lev_13745030.out
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_rap_3_1_333m_75lev/wps_field_proof/wps_field_proof_13744756_20260630T054317Z/debug/
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_rap_3_1_333m_75lev/wps_field_proof/wps_field_proof_13745030_20260630T054748Z/debug/
```

The staged bundle contains seven hourly NCEI `rap_130` GRIB2 files. With the
available WPS Vtables, that single stream is not enough to produce complete
WRF-ready `met_em` files for this case. Treat this as a source-product or
explicit filler-stream design problem before any `real.exe` approval.

## Vtable Choice

John's WPS root has no generic `Vtable.RAP`. The RAP candidates present under
`/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS/ungrib/Variable_Tables/`
are:

```text
Vtable.RAP.hybrid.ncep
Vtable.RAP.pressure.ncep
Vtable.RAP.sigma.gsd
Vtable.raphrrr
```

The 2026-06-30 proofs show that neither RAP Vtable is sufficient for the
currently staged single `rap_130` stream:

- `Vtable.RAP.hybrid.ncep` maps the desired surface/land fields, but against
  the staged files it did not produce a real-ready atmospheric vertical stack.
- `Vtable.RAP.pressure.ncep` produced the real-ready atmospheric stack, but its
  own comments say soil fields are in the hybrid-coordinate files; the proof
  confirmed no layered soil temperature/moisture output.

Use `RAP` as both the ungrib prefix and metgrid `fg_name` for single-stream RAP
proofs. Do not run `real.exe` until a corrected source product or explicit
filler design produces complete land-state/soil layers.

## Field-Adequacy Gate

The contract proves source identity and cadence. It does not prove that the
staged RAP files decode through WPS into all fields WRF needs. The first two
WPS-only proofs have failed this gate for RAP-only startup.

Minimum field checklist:

| Need | Fields or proof |
| --- | --- |
| 3D mass/wind/thermo | `HGT`, `PRESSURE`, `TT`, humidity, `UU`, `VV` on the expected vertical coordinate |
| Near-surface forcing | 2 m temperature/humidity, 10 m winds, surface pressure, sea-level pressure |
| Static/source terrain | `LANDSEA`, `SOILHGT` |
| Land state | soil temperature and soil moisture levels accepted by WPS/WRF |
| Snow and ice | `SNOW`, `SNOWH`, `SEAICE` |
| Surface temperature | `SKINTEMP` or an explicitly reviewed equivalent |
| WRF handoff | `met_em` field list, `num_metgrid_levels`, metgrid warnings, and file count for d01/d02/d03 |

Current RAP-only disposition: blocked. Do not silently revive the parked
GEFS+NAM path; ask whether John wants a NAM or other filler stream for this RAP
experiment, and label that experiment as RAP-plus-filler rather than RAP-only.

## Next Approval Request

The next approval should not be for `real.exe`. Choose one path first:

1. `brc-tools` source-product fix: stage RAP products that supply both pressure
   atmospheric fields and layered soil temperature/moisture fields, then rerun
   the WPS-only field proof.
2. RAP-plus-filler design: explicitly combine RAP atmospheric IC/LBCs with NAM
   or another land-state filler, document the science compromise, then rerun a
   WPS-only field proof.

Do not run `real.exe`, `wrf.exe`, a full run conveyor, or RAP quicklooks until
the new WPS proof produces complete `met_em` files and the field proof is
accepted.
