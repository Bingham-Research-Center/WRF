# TO-DO JUNE 17

This is the corrective control board after the failed 2026-06-17 Slurm
submission attempt. It is intentionally explicit about what is known, what is
not known, and where artifacts are allowed to live.

## Non-Negotiables

- Use John's WRF checkout: `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf`.
- Do not silently fall back to another user's build, including
  `lawson-group6/u6060939/wrf_build`.
- Do not submit a WPS/WRF run until John's `brc-wrf` checkout has a verified
  `real.exe` and `wrf.exe`, and a John-owned WPS root has verified WPS
  executables.
- Do not run practical checks on a login node. Manifest verification, strict
  file validation, NetCDF reads, quicklooks, WPS, `real.exe`, `wrf.exe`, and
  data-heavy inventories belong in an approved Slurm batch or interactive
  compute context.
- Do not put generated data, staged inputs, run directories, run-specific
  namelists, rendered one-off Slurm scripts, WRF/WPS logs, NetCDF, PNGs, or
  one-off option files in this repo.
- Keep only reusable source, docs, templates, case manifests, and validators in
  the repo. Put persistent run-control artifacts and logs under
  `lawson-group6`, outside `$HOME/gits`.

## Confirmed State

| Item | Current fact | Evidence |
| --- | --- | --- |
| Repo AGENTS files | Only one repo-local `AGENTS.md` exists. | `find . -path ./.git -prune -o -name AGENTS.md -print` returned `./AGENTS.md`. |
| WRF source checkout | `brc-wrf` exists at John's `~/gits` path. | `paths.wrf_src` and live cwd. |
| WRF executables in checkout | Not present yet. | Shallow executable scan found no `wrf.exe` or `real.exe` under the checkout. |
| WPS root | Not established for John. | The stale `jrlawson/wrf_build/WPS` root does not currently exist. |
| Failed job `13534966` | Started, verified the manifest, then exited before WPS. | Repo-local `.out` showed `verify: 28/28 OK` then missing `geogrid.exe`; logs were removed from the repo. |
| Practical WPS/WRF work | No WPS, `real.exe`, or `wrf.exe` ran in the failed job. | Failure occurred in `setup_wps`. |
| Current branch | Local `john/wrf` is ahead of `origin/john/wrf` by one commit before this cleanup. | `git status --short --branch`. |

## Storage Policy

| Artifact type | Allowed location | Repo status |
| --- | --- | --- |
| Source and reusable docs/templates | `~/gits/brc-wrf` | Track in git when stable. |
| WRF compile byproducts | Legacy WRF may build in `~/gits/brc-wrf` | Do not commit generated build products. |
| Build logs and module readbacks | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/<git-sha>/` | Never in repo. |
| John-owned WPS install | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS/` or another explicit John-owned group path | Never in repo. |
| Rendered per-run Slurm scripts | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_run_control/<case>/run_<UTC>/` | Never in repo. |
| Live WPS/WRF run I/O | `/scratch/general/vast/$USER/wrf_runs/<case>/...` | Never in repo. |
| Staged NWP input | `/scratch/general/vast/$USER/wrf_inputs/<case>/...` or a reviewed durable promotion path | Never in repo. |
| Durable outputs, logs, quicklooks | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/<case>/run_<UTC>/` | Never in repo. |

## Phase 1: Compile John's `brc-wrf`

Goal: make John's own checkout runnable, instead of using Michael's historical
group build or a nonexistent `jrlawson/wrf_build` path.

1. Prepare a Slurm build script as a reusable template or as a one-off rendered
   script under `lawson-group6/jrlawson/wrf_run_control/builds/`.
2. Run the build off-login. Do not compile on the login node.
3. Use the legacy path first unless a human explicitly chooses CMake:
   `./configure`, `./compile em_real`.
4. Use the CHPC module stack from `brc-docs/BRC-WRF-USAGE.md` and
   `brc-knowledge`, then record `module -t list`.
5. Save stdout/stderr and compile logs under:
   `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/<git-sha>/`.
6. After the build, verify on disk:
   `main/real.exe`, `main/wrf.exe`, and ideally matching `run/real.exe` /
   `run/wrf.exe` symlinks or executables.
7. Record the exact Git SHA, compiler choices, nesting choice, module list,
   executable paths, and final `git status --short --ignored`.

Template command body for the build job, to be reviewed before use:

```bash
module purge
module load intel-oneapi-compilers/2021.4.0
module load intel-oneapi-mpi/2021.1.1
module load hdf5/1.14.3
module load netcdf-c/4.9.2
module load netcdf-fortran/4.6.1

export NETCDF=$(nf-config --prefix)
export NETCDF_C=$(nc-config --prefix)
export JASPERLIB=/usr/lib64
export JASPERINC=/usr/include/jasper

cd /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf
git rev-parse HEAD
module -t list

# Review the correct configure choices before running.
# Historical CHPC guidance used Intel dmpar and basic nesting.
printf "15\n1\n" | ./configure
./compile em_real

test -x main/real.exe
test -x main/wrf.exe
```

## Phase 2: Establish John's WPS Root

WRF alone is not enough for a from-scratch practical run. WPS is separate from
this checkout.

1. Choose or create a John-owned persistent WPS source/install root, for
   example:
   `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS/`.
2. Do not use `lawson-group6/u6060939/wrf_build/WPS` except as historical
   comparison material.
3. Configure WPS against John's compiled WRF checkout:
   `WRF_DIR=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf`.
4. Verify these exist before any WPS submission:
   `geogrid.exe`, `ungrib.exe`, `metgrid.exe`, `link_grib.csh`,
   `geogrid/`, `metgrid/`, `ungrib/`, and
   `ungrib/Variable_Tables/Vtable.NAM`.
5. Keep WPS compile logs in `lawson-group6`, not the repo.

## Phase 3: Fix Case Manifest Only After Roots Exist

The case manifest now points `paths.wrf_build` at John's `brc-wrf` checkout.
That is the intended root, but it is not runnable until compile artifacts exist.

1. Keep `paths.wrf_build` as John's checkout if the legacy build is in-tree.
2. Set `paths.wps_root` only to an actual John-owned WPS root.
3. Use strict validation only in a compute/batch context if it reads scratch,
   manifests, NetCDF, or archive files.
4. Confirm the validator catches:
   missing WRF root, missing `real.exe`, missing `wrf.exe`, missing WPS root,
   missing WPS executables, repo-local run/data paths, and non-durable archive
   roots.

## Phase 4: Render Scripts Outside The Repo

1. Keep reusable Slurm template logic in repo only if it is a true template.
2. Render one-off scripts to:
   `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_run_control/<case>/run_<UTC>/`.
3. A rendered script must read back:
   WRF root, WPS root, executable paths, case window, input root, scratch run
   root, archive root, Slurm account/partition/node/tasks/memory, and launcher.
4. It must fail before WPS if any declared executable root is missing.

## Phase 5: Fresh Input/Contract Work

1. Keep input staging in `../brc-tools`.
2. Stage or refresh NAM-only inputs through approved DTN/batch work, not from
   the login node.
3. Produce a fresh `manifest_<case>.json` and `contract_<case>.json`.
4. Do not retire `brc-cases/jan2013_basin_nam.contract.json` until a fresh
   contract validates cleanly from a compute/batch context.

## Phase 6: WPS, `real.exe`, `wrf.exe`

1. WPS setup must use John's WPS root and John's compiled WRF root.
2. WPS writes to scratch, not the repo.
3. Stop after WPS if the field list or `num_metgrid_levels` is wrong.
4. Run `real.exe` directly and require `SUCCESS COMPLETE REAL_EM INIT`.
5. Run `wrf.exe` with `srun --mpi=pmi2 -n "$SLURM_NTASKS" ./wrf.exe`.
6. Treat Slurm state, WPS success, `real.exe`, `wrf.exe`, archive, and
   quicklooks as separate facts.

## Phase 7: Archive And Review

1. Archive `wrfout_d0*`, `namelist.input`, `namelist.wps`, `rsl.out.0000`,
   `rsl.error.0000`, `real.rsl.out.0000`, and `real.rsl.error.0000`.
2. Preserve debug files:
   `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, and
   `debug/run_file_inventory.tsv`.
3. Put quicklooks under `<archive-run>/quicklooks/`.
4. Never copy PNGs, NetCDF, WPS intermediate files, or run logs into the repo.

## Catches Added Or Required

| Catch | Status |
| --- | --- |
| `wrf_case.py` requires `paths.wrf_build` and `paths.wps_root` keys. | Added. |
| Strict validation reports missing `real.exe` and `wrf.exe`. | Added. |
| Strict validation reports missing WPS executables and `Vtable.NAM`. | Added. |
| Validation rejects repo-local data/run/archive roots. | Added. |
| Validation rejects scratch archive roots. | Added. |
| Validation warns if archive root is not under `lawson-group6`. | Added. |
| Rendered one-off scripts kept outside repo. | Still to implement as workflow, not yet automated. |
| Dedicated build template for John's WRF checkout. | Still to implement. |
| Dedicated WPS install/build template. | Still to implement. |

## Cleanup Completed In This Batch

- Removed failed repo-local Slurm artifacts from `brc-cases/slurm/`.
- Removed the empty `brc-cases/slurm/` directory.
- Corrected `AGENTS.md` so login-node-safe commands no longer include manifest
  verification, strict file validation, or quicklook checks.
- Changed the case manifest WRF build root to John's `brc-wrf` checkout.
- Left WPS explicitly unresolved until a John-owned WPS root exists.

## Do Not Do Next

- Do not resubmit the failed June 17 Slurm script.
- Do not point the run at `u6060939` executables.
- Do not put generated run scripts or logs under `brc-cases/`.
- Do not perform a practical validator/quicklook/manifest run on the login node
  just to make the docs look green.
