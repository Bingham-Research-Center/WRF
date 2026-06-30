# Repository Context

This is the Bingham Research Center checkout of WRF:

- Remote: `https://github.com/Bingham-Research-Center/WRF.git`
- Branch family: `john/*`
- Current upstream-style baseline: WRF `4.8.0`

This tree is large. Start narrow and local. Do not broad-scan WRF internals,
scratch trees, archives, or sibling repos unless a named file or `rg` result
points there.

## Source Of Truth

Keep this file as the AI router and safety contract, not a backlog.

| Truth | Canonical file |
| --- | --- |
| Current queue, active evidence, and remaining approvals | `doc/BRC_WRF_MICROTASK_HANDOFF.md` |
| End-to-end WRF/WPS route | `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` |
| Pelican conveyor, 333 m baseline, and quicklook rules | `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md` |
| Pelican alternate-forcing prompt, RAP feasibility, and approval boundary | `brc-docs/BRC-WRF-PELICAN-ALTERNATE-FORCING.md` |
| First-case proof and run explanation | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| Printable state summary | `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` |
| Case manifests, validators, Slurm renderers, WRF-output quicklook adapter | `brc-cases/README.md` |
| Input staging, manifests, contracts, downloader behavior | `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md` and `../brc-tools/docs/WRF-INPUT-STAGING.md` |
| CHPC node, storage, scheduler, proxy, and validated Slurm truth | `../brc-knowledge/scholarium/reference-base/resources/` |

If a fact changes, update the canonical file above and only leave short pointers
elsewhere. Do not revive deleted priority files or copy task matrices into this
router.

For to-dos and wishlists, start with `doc/BRC_WRF_MICROTASK_HANDOFF.md`.
Use `brc-docs/BRC-WRF-ROADMAP.md` only as a compact gate/follow-on index and
`brc-docs/BRC-WRF-STATE-PLAYBOOK.md` for human-readable next moves. Sibling
staging wishlists belong in `../brc-tools/docs/`, not this repo.

## Ownership

- `brc-wrf`: WRF source, WPS/WRF-side docs, case manifests, validators, run
  templates, maintained wrappers, and WRF-output quicklook adaptation.
- `brc-tools`: input staging, manifests, contracts, token checks, NWP download
  logic, and reusable visualization helpers such as `brc_tools.visualize.grid`.
- `brc-knowledge`: canonical CHPC infrastructure facts and validated Slurm
  guidance.

Patch the repo that owns the behavior. Do not add downloader/staging logic to
`brc-wrf`. Do not put WRF/WPS execution wrappers in `brc-tools`.

## Cold Start

Read only what the task needs. A cheap default start is:

1. `git status --short --branch --untracked-files=no`
2. `sed -n '1,180p' AGENTS.md`
3. `sed -n '1,220p' doc/BRC_WRF_MICROTASK_HANDOFF.md`
4. `sed -n '1,160p' brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
5. `sed -n '1,180p' brc-cases/README.md`
6. `sed -n '1,140p' ../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`

Task-specific adds:

- Local automation: `.sane/wrf/README.md`
- Build/WPS/WRF progression: `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`
- Pelican replay or comparison plots: `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md`
  and `brc-docs/BRC-WRF-PELICAN-ALTERNATE-FORCING.md`
- CI: `.ci/tests/build.sh` and `.github/workflows/ci.yml`

## Current Durable Truth

- Validated baseline: NAM-only Jan-2013 Uinta Basin, 12/4 km nested, WPS
  `Vtable.NAM`, `interval_seconds = 21600`.
- Fresh staging should emit `manifest_<case>.json` and
  `contract_<case>.json`; the tracked reconstructed Jan-2013 NAM contract is a
  fallback only.
- Roadmap Gates 5-11 passed on 2026-06-18 for the John-owned NAM-only proof:
  fresh contract, WPS, `real.exe`, `wrf.exe`, archive, quicklooks, and the
  maintained practical-test harness.
- John-owned WPS v4.6.0 proof passed on 2026-06-18 at
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS`.
- Current owned-node WRF default is `lawson-np` on `notch392`, one node,
  56 tasks, `900G`, and `srun --mpi=pmi2`.
- Practical testing has one approved passing row: `scaling_t028` job
  `13550110`. Later `scaling_t016` attempts failed before WRF runtime evidence
  and are not benchmark results; see `doc/BRC_WRF_MICROTASK_HANDOFF.md`.
- GEFSv12 plus NAM two-stream forcing is a parked optional path, not the
  current hot-swap route. Do not foreground it unless John explicitly revives
  that experiment.
- Pelican NAM 3/1/0.333 km 75-level six-hour baseline completed on 2026-06-26:
  `pelican2013_nam_3_1_333m_75lev`, full job `13695261`, archive
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/`.
- Adjacent `brc-tools` branch `feat/wrf-rap-source` has `rap_analysis`
  planning/contract support and live NCEI availability evidence for the
  2013-02-02 12-18Z Pelican RAP window. `brc-wrf` still owns the WPS Vtable,
  field-adequacy, case-manifest, render, and run-approval review before any
  RAP staging or WPS/WRF execution.
- Standardized WRF-output quicklooks render 10 PNGs per available domain under
  `<archive-run>/quicklooks/<stamp>/dXX/` using reusable `brc-tools` plotting
  helpers and a `brc-wrf` WRF-file adapter. Pelican forcing comparisons should
  reuse the NAM 333 m baseline products.
- Michael Davies' working WRF/WPS path under `lawson-group6/u6060939/` is
  comparison evidence only. Do not point John's wrappers at Michael-owned WRF
  or WPS roots.

## Login-Safe Versus Off-Login

Login-node-safe examples when kept small:

- `git status --short --branch --untracked-files=no`
- `sed -n '1,180p' <named-doc>`
- `rg -n '<specific-pattern>' <narrow-paths>`
- `python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py`
- `PYTHONPATH=brc-cases python brc-cases/test_wrf_quicklook.py`
- `python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml`

Run only in approved Slurm batch or interactive compute context:

- `python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest ...`
- `python brc-cases/wrf_case.py validate ... --strict-files` when it reads
  staged inputs, manifests, WPS/WRF files, or archives
- `python brc-cases/wrf_quicklook.py check ...`
- `python brc-cases/wrf_quicklook.py render ...`
- WPS, `real.exe`, `wrf.exe`, NetCDF inspection, manifest hashing, archive
  inventories, staging plans, and data-heavy filesystem searches

Never run full builds, WPS, WRF, Slurm submissions, scaling sweeps, or large
downloads without explicit approval.

## Storage And Artifacts

- Staged forcing: `/scratch/general/vast/$USER/wrf_inputs/<case>/`
- Active WPS/WRF I/O: `/scratch/general/vast/$USER/wrf_runs/<case>/`
- Durable run artifacts:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/`
- Durable logs:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/`

Generated runs, staged inputs, run-local namelists, rendered one-off Slurm
scripts, logs, NetCDF, PNGs, and inventories do not belong in this repo.

## WRF Workflow Gotchas

- Build truth must be checked from disk. A fresh checkout has no `real.exe` or
  `wrf.exe` until compiled.
- WPS is separate from this checkout. A real submission needs a John-owned WRF
  executable root and a WPS root containing `geogrid.exe`, `ungrib.exe`,
  `metgrid.exe`, `link_grib.csh`, and `Vtable.NAM`.
- Gate 11 practical wrappers byte-match scenario `real.exe`/`wrf.exe` against
  John's `paths.wrf_build/main/` and runtime physics/table files against
  John's `paths.wrf_build/run/` before `real.exe`.
- Generated `prepare_<scenario>.sh` helpers require `BRC_PREP_APPROVED=YES`,
  refuse Michael-owned comparison paths, copy/check files only, and must be run
  only in an approved off-login context.
- WRF filenames contain colons. Archive with local-style sources such as
  `rsync -av ./wrfout_d0* ...`.
- A Slurm wrapper can fail after successful WRF execution if archive work fails.
  Treat `real.exe`, `wrf.exe`, archive completeness, Slurm state, and
  quicklooks as separate evidence.
- Avoid `srun --jobid` probes inside a fully occupied WRF allocation.
- Prefer structured artifacts over large logs: `debug/run_debug_summary.txt`,
  `debug/run_phase_times.tsv`, `debug/run_file_inventory.tsv`, `sacct`, and
  targeted `rg` success/error patterns. Keep tails tightly bounded.

## Build And Test Caution

Both build paths exist:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct. Read the relevant local doc or script first.

## Change SOP

- Keep changes lean, logical, and scientifically grounded.
- Update the canonical doc in the same commit when workflow truth changes.
- Keep detailed task counts in `doc/BRC_WRF_MICROTASK_HANDOFF.md`, not here.
- Stage only relevant files; leave unrelated sibling-repo dirt alone.
- Write concise commit subjects and detailed bodies with motivation, evidence,
  validation, and operational impact.
- When AI materially assists a change, include both coauthor trailers:
  `Co-authored-by: John Lawson <john.lawson@usu.edu>` and
  `Co-authored-by: Codex <codex@openai.com>`.
