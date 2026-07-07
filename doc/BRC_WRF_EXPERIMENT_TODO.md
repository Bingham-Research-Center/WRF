# BRC WRF Experiment To-Do

This is the short active task router for running and reviewing WRF
experiments across `brc-wrf` and sibling `brc-tools`.

Use this before the longer evidence files. It should stay small enough for an
AI cold start.

## Current Aim

Use the completed Pelican 3/1/0.333 km, 75-level runs as a poor-man's ensemble:

- NAM two-way baseline: complete.
- GFS analysis hot-swap: complete.
- NAM one-way feedback sensitivity: complete.
- Standard and supplemental quicklooks: complete.

Current human-selected lane: rerun the NAM one-way terrain test using
successful job `13788264` as the Slurm/WRF reference, but with genuinely finer
terrain. The completed `topo_gmted2010_5m` run proved the overlay/control path,
but `5m` is 5 arc-minutes, not 5 metres, so it is coarser than the installed
`topo_gmted2010_30s` default. Job `13847980` completed `0:0` in `02:17:41` on
`notch392`; quicklook job `13848733` completed `0:0` and wrote 42 PNGs. The
custom `3s` `HGT_M` static terrain source is built and cached. Next target:
geogrid-only proof that WPS uses `topo_brc_custom_3s` for `HGT_M`.

## Next Tasks

| Order | Repo | Task | Stop point |
| ---: | --- | --- | --- |
| 1 | `brc-wrf` | Run geogrid-only proof with `topo_brc_custom_3s` as the `HGT_M` overlay and shared `WPS_GEOG` for all other fields. | `geogrid.log` says custom `3s` source was used; archive `geo_em.d0*.nc`, `namelist.wps`, `GEOGRID.TBL.ARW`, and a terrain-difference preview against the `30s`/`5m` runs. |
| 2 | `brc-wrf` | If the `3s` geogrid proof is clean, rerun the same NAM one-way WPS/WRF conveyor as job `13847980`, changing only the terrain source and case/run names. | `real.exe`, `wrf.exe`, archive, standard quicklooks, and supplemental quicklooks; compare against job `13788264` and the `topo_gmted2010_5m` operator-proof run. |
| 3 | `brc-wrf` | Review the completed Pelican quicklooks, including standard 10-product sets plus `_600hPa` and `_4h` supplemental folders. | Short science packet: similarities, differences, suspicious fields, and whether another source or `1s` terrain is worth trying. |
| 4 | `brc-wrf` | Decide the next experiment lane from the review. | Pick one: `1s` terrain follow-up, FNL/GFS-family source, corrected RAP/filler design, ERA5 access work, scaling row, memory row, or stop. |
| 5 | `brc-tools` | If another forcing source is chosen, do source feasibility first: source access, fields, cadence, Vtable implications, manifest/contract plan. | No WPS/WRF; hand back a staged or clearly blocked contract path. |
| 6 | `brc-wrf` | Consume only a verified `brc-tools` contract: case YAML, WPS/Vtable review, WPS-only field proof if field adequacy is uncertain. | Stop before `real.exe` unless explicitly approved after field review. |
| 7 | `brc-wrf` | Run the WRF conveyor only after approval: WPS, `real.exe`, `wrf.exe`, archive, quicklooks. | Leave job IDs, logs, archive path, quicklook path, and failure/success markers. |

## Current Evidence Pointers

| Need | File |
| --- | --- |
| Geogrid-only terrain/domain preview | `brc-docs/BRC-WRF-DOMAIN-PREVIEW-SOP.md` |
| Custom WPS `HGT_M` static tile preparation | `brc-cases/wps_hgt_static.py` and `brc-cases/README.md` |
| Pelican source verdicts, terrain state, and quicklook roots | `brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md` |
| Conveyor rules, archive layout, quicklook layout | `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md` |
| First Jan-2013 proof and gate evidence | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| Detailed historical evidence ledger | `doc/BRC_WRF_MICROTASK_HANDOFF.md` |
| Build/WPS/WRF end-to-end route | `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` |
| Case helpers and quicklook adapter | `brc-cases/README.md` |
| WRF staging state in `brc-tools` | `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md` |
| WRF staging implementation details in `brc-tools` | `../brc-tools/docs/WRF-INPUT-STAGING.md` |
| Broader `brc-tools` backlog | `../brc-tools/WISHLIST-TASKS.md` |

## Source Choices

| Source path | Current status | Owner |
| --- | --- | --- |
| NAM baseline | Complete; comparison anchor. | `brc-wrf` review only |
| GFS analysis | Complete; WRF run and quicklooks rendered. | `brc-wrf` review only |
| NAM one-way feedback | Complete; feedback sensitivity, not a new forcing source. | `brc-wrf` review only |
| RAP-only | Blocked before `real.exe`: hybrid RAP lacks usable 3D atmosphere; pressure RAP lacks layered soil temperature/moisture. | `brc-tools` source fix or explicit filler design |
| ERA5 | Locally blocked: no `brc-tools` source support, CDS tooling, or CDS credentials. | `brc-tools` access/tooling first |
| FNL | Optional independent third source; not current default. | `brc-tools` feasibility first |
| GEFSv12+NAM two-stream | Parked legacy path. | revive only by explicit human decision |

## Approval Boundaries

Login-safe:

- read/edit docs;
- run `git status`;
- run path-only quicklook tests;
- run `python -m py_compile` on `brc-cases` helpers;
- render terrain Slurm packets without submitting them.

Off-login or approval-gated:

- terrain DEM metadata/download/cache/build jobs;
- strict manifest/contract checks that hash staged inputs;
- NetCDF/archive reads;
- quicklook rendering;
- DTN staging;
- WPS, `real.exe`, `wrf.exe`;
- Slurm submissions, scaling, memory benchmarks;
- durable promotion from scratch.

## Repo Boundary

- `brc-tools`: downloads, source access, GRIB staging, manifests, contracts,
  token/source checks, input quicklooks.
- `brc-wrf`: WRF source, WPS/WRF consumption, case YAML, validators, run
  wrappers, WRF-output quicklooks, archive evidence.
- `brc-knowledge`: CHPC node, storage, scheduler, proxy, and validated Slurm
  truth.

Patch the repo that owns the behavior. If this file and a sibling `brc-tools`
doc disagree, refresh the owner doc and leave a short pointer here.
