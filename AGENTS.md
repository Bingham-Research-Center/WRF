# Repository Context

This is the Bingham Research Center checkout of WRF:

- Remote: `https://github.com/Bingham-Research-Center/WRF.git`
- Branch family: `john/*`
- Current upstream-style baseline: WRF `4.8.0`

This tree is large. Start narrow and local before broad source scans or expensive
commands.

## README Roles

- `README`: upstream WRF version, public-domain notice, release notes, and doc
  index.
- `README.md`: short BRC-facing entry point for humans.
- `AGENTS.md`: short AI router and safety guide. Keep detailed task boards out of
  this file.

## Core Ownership

- `brc-wrf`: WRF source, WPS/WRF-side docs, case manifests, validators, run
  templates, and maintained wrappers.
- `brc-tools`: input staging, manifests, contracts, token checks, and NWP
  download logic. Do not add downloader/staging code here.
- `brc-knowledge`: canonical CHPC node, storage, scheduler, and validated Slurm
  guidance.

## Start Here

Read only what the task needs:

1. `README.md`
2. `doc/BRC_FORK_GUIDE.md`
3. `doc/BRC_WRF_MICROTASK_HANDOFF.md`
4. `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`
5. `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
6. `brc-docs/BRC-WRF-FIRST-CASE.md`
7. `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`
8. `brc-cases/README.md`

If the task is about local automation, also read `.sane/wrf/README.md`. If it is
about CI, read `.ci/tests/build.sh` and `.github/workflows/ci.yml`.

## Current Run Truth

- The validated proof is NAM-only, Jan-2013 Uinta Basin, 12/4 km nested, with
  `Vtable.NAM` and `interval_seconds = 21600`.
- The old proof scratch used WPS `FILE`/`FILE` naming for ungrib prefix and
  `metgrid fg_name`.
- The old proof predates fresh `brc-tools` contract sidecars, so this repo keeps
  `brc-cases/jan2013_basin_nam.contract.json` as a reconstructed fallback for
  strict validation. Fresh staging should emit `contract_<case>.json`.
- Practical checks must not run on login nodes. That includes manifest hashing,
  strict validation when it reads staged/archive artifacts, NetCDF reads,
  quicklooks, WPS, `real.exe`, `wrf.exe`, and data-heavy inventories.
- Current owned-node default for real WRF work is `lawson-np` on `notch392`,
  one node, 56 tasks, `900G`, and `srun --mpi=pmi2`.
- GEFSv12 plus NAM two-stream forcing is not yet validated.
- Build truth must be checked from disk. A fresh checkout has no `real.exe` or
  `wrf.exe` until it is compiled.
- WPS is separate from this checkout. A real submission needs both a John-owned
  WRF executable root and a WPS root with `geogrid.exe`, `ungrib.exe`,
  `metgrid.exe`, `link_grib.csh`, and `Vtable.NAM`.
- Roadmap Gate 3 passed on 2026-06-18: John-owned WPS v4.6.0 was built at
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS` from
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_sources/WPS-v4.6.0`.
  Evidence:
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate3_20260618T054456Z_13539773/`.
  WPS configure option `23` selected Intel Classic `dmpar`; `configure.wps`
  required CHPC MPI wrapper pinning to `mpif90 -f90=$(SFC)` and
  `mpicc -cc=$(SCC)`.
- Roadmap Gate 4 metadata review passed on 2026-06-18:
  `/tmp/jan2013_basin_nam.gate4.20260618T054655Z.report.txt`; rendered Slurm
  review only:
  `/tmp/jan2013_basin_nam.gate4.20260618T054655Z.rendered.slurm`.
- Roadmap Gates 5-11 passed on 2026-06-18: fresh NAM-only contract,
  NAM-only WPS/`real.exe`/`wrf.exe`, archive, quicklooks, and maintained
  practical-test harness are complete. Do not redo those gates unless live disk
  evidence contradicts the docs.
- Practical testing has one approved scaling row complete. The first chain
  exposed two setup bugs: job `13548709` used Michael-owned WRF `V4.7.1`
  binaries through scratch symlinks and failed with
  `CLWRF: 'CAMtr_volume_mixing_ratio' does not exist`; follow-up job `13550021`
  used John's WRF `V4.8.0` binaries but the clean scenario run directory lacked
  runtime physics files from John's `run/` directory. After wrapper provenance
  guards and runtime-file staging, prep job `13550104` and `scaling_t028` job
  `13550110` passed with John's `~/gits/brc-wrf` at `34710497`, 28 tasks,
  `900G`, and archive/debug evidence under
  `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t028/run_20260618T230858Z/debug/`.
  No other scaling or memory rows are approved by this evidence.
- Michael Davies has a separate working end-to-end WRF/WPS reference path under
  `lawson-group6/u6060939/wrf_build/`, documented in `brc-knowledge`. Treat it
  as evidence and comparison context only; do not point John's run wrappers at
  Michael-owned WRF or WPS roots.
- Generated runs, staged inputs, run-local namelists, rendered one-off Slurm
  scripts, logs, NetCDF, PNGs, and other ephemeral artifacts do not belong in
  this repo. Active I/O goes to scratch; durable artifacts go under
  `lawson-group6/...` outside `$HOME/gits`.

## Routing

- Repo or fork orientation: `README.md`, `AGENTS.md`, `doc/BRC_FORK_GUIDE.md`
- Current queue, countdown, or next-task routing:
  `doc/BRC_WRF_MICROTASK_HANDOFF.md`
- End-to-end build/WPS/WRF progression:
  `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`
- Slim handoff pointer: `doc/BRC_WRF_HANDOFF.md`
- Current milestone or printable state:
  `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`, then
  `brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md`
- First-case proof or run explanation:
  `brc-docs/BRC-WRF-FIRST-CASE.md`, then `brc-docs/BRC-WRF-USAGE.md`
- John/Michael no-run review packet:
  `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md`
- `brc-tools` to `brc-wrf` handoff:
  `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`
- `brc-wrf` to `brc-tools` staging-contract handoff:
  `brc-docs/BRC-TOOLS-LINK-HANDOFF.md`
- Case/validator/Slurm-render work:
  `brc-cases/README.md`, the relevant `*.case.yaml`, and
  `brc-cases/wrf_case.py`

## Login-Node-Safe First Commands

These are safe first-pass orientation commands when they stay small and local:

- `git status --short --branch`
- `sed -n '1,140p' README.md`
- `sed -n '1,180p' AGENTS.md`
- `sed -n '1,220p' doc/BRC_WRF_MICROTASK_HANDOFF.md`
- `sed -n '1,160p' brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
- `sed -n '1,180p' brc-docs/BRC-WRF-FIRST-CASE.md`
- `sed -n '1,160p' brc-cases/README.md`
- `python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py`
- `find . -path ./.git -prune -o -name AGENTS.md -print`
- `find . -maxdepth 3 \( -name wrf.exe -o -name real.exe -o -name geogrid.exe -o -name ungrib.exe -o -name metgrid.exe \) -print`

## Off-Login Practical Checks

Run these only inside approved Slurm batch or interactive compute context:

- `python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest ...`
- `python brc-cases/wrf_case.py validate ... --strict-files` when it reads
  staged inputs, manifests, WPS/WRF files, or archive paths
- `python brc-cases/wrf_quicklook.py check ...`
- `python brc-cases/wrf_quicklook.py render ...`
- WPS, `real.exe`, `wrf.exe`, NetCDF inspection, staging plans, and data-heavy
  inventories

## Build And Test Caution

- Both build paths exist:
  - Legacy: `./configure`, `./compile`, `./clean`
  - CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`
- Do not assume one path is correct for a task. Read the relevant local doc or
  script first.
- Do not run full builds, regression suites, Slurm jobs, or other HPC workflows
  without explicit approval.

## Cheap Validation

- Prefer syntax and metadata checks before compile-scale work.
- For shell changes, use `bash -n`.
- For Python changes, use `python -m py_compile <file>` or the smallest existing
  focused test.
- For workflow changes, inspect paths, dry-run behavior, and storage targets
  before any practical run.

## WRF Workflow Gotchas

- Use `/scratch/general/vast/$USER/wrf_inputs/<case>/` for staged forcing and
  `/scratch/general/vast/$USER/wrf_runs/<case>/` for active WPS/WRF I/O.
- Durable runs and quicklooks belong under
  `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/`.
- Rendered run wrappers should preserve compact debug artifacts beside WRF logs:
  `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, and
  `debug/run_file_inventory.tsv`.
- If staging behavior changes, patch `brc-tools`, not this WRF tree.
- WRF filenames contain colons. When archiving with `rsync`, use local-style
  sources such as `./wrfout_d0*`.
- A Slurm wrapper can fail after a successful `wrf.exe` step if post-run archive
  work fails. Check WRF success markers, Slurm state, and archived artifacts
  separately.
- Avoid `srun --jobid` probes inside a fully occupied WRF allocation.

## Change SOP

- Keep changes lean, logical, and scientifically grounded.
- Update the canonical doc in the same commit when workflow truth changes.
- Keep detailed task counts in `doc/BRC_WRF_MICROTASK_HANDOFF.md`, not here.
- Write concise commit subjects and detailed bodies when committing.
- When AI materially assists a change, include both coauthor trailers:
  `Co-authored-by: John Lawson <john.lawson@usu.edu>` and
  `Co-authored-by: Codex <codex@openai.com>`.
