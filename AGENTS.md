# Repository Context

This is the Bingham Research Center checkout of WRF:

- Remote: `https://github.com/Bingham-Research-Center/WRF.git`
- Branch family: `john/*`
- Current upstream-style baseline: WRF `4.8.0`

This tree is large. Start narrow and local. Do not broad-scan WRF internals,
scratch trees, archives, or sibling repos unless a named file or `rg` result
points there.

## Cold Start

Keep this file as the AI router and safety contract, not a backlog.

Default start:

1. `git status --short --branch --untracked-files=no`
2. `sed -n '1,180p' AGENTS.md`
3. `sed -n '1,220p' doc/BRC_WRF_EXPERIMENT_TODO.md`

Then load only the task-specific owner doc:

- Detailed historical evidence: `doc/BRC_WRF_MICROTASK_HANDOFF.md`
- Build/WPS/WRF route: `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`
- Pelican review, source hot-swap, or comparison plots:
  `brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md` and
  `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md`
- Parked RAP-only details: `brc-docs/BRC-WRF-PELICAN-RAP-FEASIBILITY.md`
- Case manifests, validators, Slurm renderers, and quicklooks:
  `brc-cases/README.md`
- Input staging, manifests, contracts, source access:
  `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`,
  `../brc-tools/docs/WRF-INPUT-STAGING.md`, and
  `../brc-tools/WISHLIST-TASKS.md`
- CHPC node, storage, scheduler, proxy, and Slurm truth:
  `../brc-knowledge/scholarium/reference-base/resources/`
- Local automation: `.sane/wrf/README.md`
- CI: `.ci/tests/build.sh` and `.github/workflows/ci.yml`

Do not revive deleted June handoffs, chat-style notes, or stale priority files.
If a fact changes, update the owner doc and leave only short pointers elsewhere.

## Source Of Truth

| Truth | Canonical file |
| --- | --- |
| Current experiment todo across `brc-wrf` and `brc-tools` | `doc/BRC_WRF_EXPERIMENT_TODO.md` |
| Detailed evidence ledger | `doc/BRC_WRF_MICROTASK_HANDOFF.md` |
| End-to-end WRF/WPS route | `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` |
| Pelican conveyor, archive, and quicklook rules | `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md` |
| Pelican source/terrain verdicts and review prompts | `brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md` |
| First-case proof and run explanation | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| Printable state summary | `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` |
| Case helpers, static terrain helper, and WRF-output quicklook adapter | `brc-cases/README.md` |
| Input staging and downloader behavior | `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md` and `../brc-tools/docs/WRF-INPUT-STAGING.md` |
| CHPC infrastructure facts | `../brc-knowledge/scholarium/reference-base/resources/` |

## Ownership

- `brc-wrf`: WRF source, WPS/WRF-side docs, case manifests, validators, run
  templates, maintained wrappers, and WRF-output quicklook adaptation.
- `brc-tools`: input staging, manifests, contracts, token checks, NWP download
  logic, and reusable visualization helpers such as `brc_tools.visualize.grid`.
- `brc-knowledge`: canonical CHPC infrastructure facts and validated Slurm
  guidance.

Patch the repo that owns the behavior. Do not add downloader/staging logic to
`brc-wrf`. Do not put WRF/WPS execution wrappers in `brc-tools`.

## `brc-tools` Python Environment

For any command that runs sibling `../brc-tools` Python, Herbie, NWP source
planning, input staging, manifest verification, or `pytest`, force the
maintained environment:

```bash
conda run -n brc-tools-2026 python ...
conda run -n brc-tools-2026 pytest ...
```

The stricter equivalent is:

```bash
/uufs/chpc.utah.edu/common/home/u0737349/software/pkg/miniforge3/envs/brc-tools-2026/bin/python ...
```

Bare `python brc-cases/...` remains acceptable for this dependency-light
`brc-wrf` repo unless the task invokes `brc-tools`.

Exception: WRF-output quicklook rendering reads WRF NetCDF and imports plotting
helpers from `../brc-tools`. Source planning still belongs in
`brc-tools-2026`, but if that environment lacks the xarray NetCDF backend, use
a proven NetCDF-capable render environment with `PYTHONPATH` pointed at
`../brc-tools` and record the environment in the control/log evidence.

## Current Experiment Truth

- Validated Jan-2013 Basin proof: NAM-only, 12/4 km nested, WPS `Vtable.NAM`,
  `interval_seconds = 21600`; Gates 5-11 passed on 2026-06-18.
- John-owned WPS v4.6.0 lives at
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS`.
  John's WRF executable path must come from rendered control evidence and be
  checked on disk.
- Current owned-node WRF profile: `lawson-np` on `notch392`, one node,
  56 tasks, `900G`, `srun --mpi=pmi2`.
- Fresh `brc-tools` staging emits `manifest_<case>.json` and
  `contract_<case>.json`; `brc-wrf` consumes those sidecars.
- Pelican completed WRF-side runs: NAM two-way baseline job `13695261`, GFS
  analysis job `13753673`, and NAM one-way feedback sensitivity job `13788264`.
- The matched default-terrain GFS one-way leg is complete through post-processing:
  preparation `13894268`, WRF `13894282`, and quicklooks `13896648`; exact
  paths and cross-repo analysis/figure evidence are in `doc/BRC_WRF_EXPERIMENT_TODO.md`.
- The custom `3s` NAM one-way terrain run is complete: WPS `13851884`, WRF
  `13852034`, and quicklooks `13852773`. Its clean two-way feedback companion
  is complete in preparation `13880432`, WRF `13880435`, and quicklooks
  `13881153`; the only normalized namelist change was `feedback = 0 -> 1`, and
  it produced 21 hourly outputs plus 54 review PNGs. Paired diagnostic job
  `13881198` completed with 189 finite field/time/domain rows and found small
  d03 domain-mean but non-null localized feedback response without broad
  adjacent-cell roughness growth. The six-hour
  slope/shading treatment is complete in preparation `13876527`, WRF
  `13876534`, and quicklooks
  `13877355`; its slope+MYJ/Eta increment is complete in preparation
  `13879078`, WRF `13879100`, and quicklooks `13879973`. Each treatment has
  21 hourly outputs and 54 review PNGs. The paired publication and diagnostic
  figure suites are also complete; current stop is human science review,
  including a dedicated one-way-versus-two-way terrain3s comparison. Do not
  submit another WRF treatment without a new explicit approval.
- Current static-terrain evidence: download job `13849489` on `dtn05` and build
  job `13849490` on `notch137` completed `0:0`; 99 USGS 1 arc-second GeoTIFFs
  cached at 4.6G; `topo_brc_custom_3s` built at 350M with 63 tiles plus index;
  corrected geogrid-only job `13849737` proved nonzero custom 3s `HGT_M`.
- RAP-only remains blocked before `real.exe`; ERA5 is locally blocked by source
  support, CDS tooling, and CDS credentials; FNL is optional; GEFSv12+NAM is
  parked unless explicitly revived.

## Login-Safe Versus Off-Login

Login-node-safe examples when kept small:

- `git status --short --branch --untracked-files=no`
- `sed -n '1,180p' <named-doc>`
- `rg -n '<specific-pattern>' <narrow-paths>`
- `python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py`
- `python -m py_compile brc-cases/wps_hgt_static.py`
- `PYTHONPATH=brc-cases python brc-cases/test_wrf_quicklook.py`
- `PYTHONPATH=brc-cases python brc-cases/test_wps_hgt_static.py`
- `python brc-cases/wps_hgt_static.py render-slurm-packet ...`
- `python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml`

Run only in approved Slurm batch or interactive compute context:

- `python brc-cases/wps_hgt_static.py query-usgs ...`
- `python brc-cases/wps_hgt_static.py download-manifest ...`
- `python brc-cases/wps_hgt_static.py build-from-inventory ...`
- `conda run -n brc-tools-2026 python -m brc_tools.nwp.wrf_staging --verify-manifest ...`
- strict validators that read staged inputs, manifests, WPS/WRF files, or archives
- `python brc-cases/wrf_quicklook.py check ...`
- `python brc-cases/wrf_quicklook.py render ...`
- WPS, `real.exe`, `wrf.exe`, NetCDF inspection, manifest hashing, archive
  inventories, staging plans, scaling sweeps, memory tests, and large downloads

Never run full builds, WPS, WRF, Slurm submissions, scaling sweeps, or large
downloads without explicit approval.

## Storage And Artifacts

- Staged forcing: `/scratch/general/vast/$USER/wrf_inputs/<case>/`
- Static terrain DEM cache: `/scratch/general/vast/$USER/wrf_inputs/<case>/terrain_dem_cache/`
- Static WPS geography overlays: `/scratch/general/vast/$USER/wps_geog_<purpose>/`
- Active WPS/WRF I/O: `/scratch/general/vast/$USER/wrf_runs/<case>/`
- Durable run artifacts:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/`
- Durable logs:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/`

Generated runs, staged inputs, run-local namelists, rendered Slurm scripts,
logs, NetCDF, PNGs, and inventories do not belong in this repo.

## Workflow Gotchas

- Build truth must be checked from disk; a fresh checkout has no `real.exe` or
  `wrf.exe` until compiled.
- WPS is separate from this checkout. Production wrappers must use John-owned
  WRF/WPS roots, not Michael-owned comparison paths.
- Gate 11 practical wrappers byte-match scenario executables and runtime tables
  against John's build before `real.exe`.
- WRF filenames contain colons; archive with local-style sources such as
  `rsync -av ./wrfout_d0* ...`.
- Treat `real.exe`, `wrf.exe`, archive completeness, Slurm state, and
  quicklooks as separate evidence.
- Prefer structured artifacts over large logs:
  `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`,
  `debug/run_file_inventory.tsv`, `sacct`, and targeted `rg` patterns.

## Build And Test Caution

Both build paths exist:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct. Read the relevant local doc or script first.

## Change SOP

- Keep changes lean, logical, and scientifically grounded.
- Update the canonical owner doc when workflow truth changes.
- Stage only relevant files; leave unrelated sibling-repo dirt alone.
- Write concise commit subjects and detailed bodies with motivation, evidence,
  validation, and operational impact.
- When AI materially assists a change, include both coauthor trailers:
  `Co-authored-by: John Lawson <john.lawson@usu.edu>` and
  `Co-authored-by: Codex <codex@openai.com>`.
