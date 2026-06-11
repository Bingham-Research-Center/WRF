# `.sane/wrf` Local Automation Map

This directory holds BRC-local SANE automation for WRF builds, runs, and
regression-style checks. Treat it as workflow code, not upstream WRF source.

Do not run these actions casually. The build wrappers clean and compile WRF, the
run wrappers can remove or move run outputs, and the host configs target Derecho
PBS resources.

## File Map

| Path | Role | Cheap validation | Expensive boundary |
| --- | --- | --- | --- |
| `scripts/buildCMake.sh` | CMake build wrapper around `cleanCMake.sh`, `configure_new`, and `compile_new`. | `bash -n .sane/wrf/scripts/buildCMake.sh` | Cleans, configures, and compiles WRF. |
| `scripts/buildMake.sh` | Legacy build wrapper around `clean`, `configure`, and `compile`; can copy WRF to a build dir first. | `bash -n .sane/wrf/scripts/buildMake.sh` | Deletes/recreates build dirs and compiles WRF. |
| `scripts/run_init.sh` | Runs `ideal.exe`, `real.exe`, or another init executable in an existing run folder. | `bash -n .sane/wrf/scripts/run_init.sh` | Removes WRF outputs in the run folder, then launches the init executable. |
| `scripts/run_wrf.sh` | Runs `wrf.exe` in an existing run folder with optional MPI and OMP settings. | `bash -n .sane/wrf/scripts/run_wrf.sh` | Launches WRF and streams `rsl.out.*` output. |
| `scripts/run_wrf_restart.sh` | Runs restart comparison workflow using WRF and `diffwrf`. | `bash -n .sane/wrf/scripts/run_wrf_restart.sh` | Moves existing outputs, reruns WRF, and compares history files. |
| `scripts/compare_wrf.sh` | Compares WRF input/output files across folders with `diffwrf`. | `bash -n .sane/wrf/scripts/compare_wrf.sh` | Creates temp comparison dirs and invokes `diffwrf` on model outputs. |
| `custom_actions/run_wrf.py` | SANE action classes for staging/running WRF cases and wiring MPI/OMP options. | `python -m py_compile .sane/wrf/custom_actions/run_wrf.py` | Action execution may stage cases and launch WRF. |
| `tests/builds/builds.py` | SANE build-action generator for CMake and legacy compiler/build permutations. | `python -m py_compile .sane/wrf/tests/builds/builds.py` | Generates compile-scale action sets. |
| `tests/regtests/wrf_coop.py` | SANE WRF Coop regression action definitions and case matrix. | `python -m py_compile .sane/wrf/tests/regtests/wrf_coop.py` | Regression actions depend on built WRF and external case data. |
| `hosts/derecho.jsonc` | Derecho PBS host resources, local CPU limits, paths, and action resource patches. | Inspect with `sed` or JSONC-aware tools. | Targets Derecho queues/accounts and HPC resources. |
| `hosts/derecho_envs.jsonc` | Derecho compiler/module environment definitions. | Inspect with `sed` or JSONC-aware tools. | Loads Derecho modules during action execution. |

## Mutation Boundaries

- `buildCMake.sh` runs `cleanCMake.sh`, `configure_new`, and `compile_new`.
  Treat it as a clean/configure/compile action, not a probe.
- `buildMake.sh` runs legacy `clean`, `configure`, and `compile`. When given a
  non-default build directory, it removes that directory, recreates it, copies a
  WRF source subset into it, and builds there.
- `run_init.sh` changes into the run folder, may replace `namelist.input`, then
  removes prior `wrfinput_*`, `wrfbdy_*`, `wrfout_*`, `rsl*`, and related files
  before launching the init executable.
- `run_wrf.sh` changes into the run folder, may replace `namelist.input`, then
  launches WRF with optional MPI and OMP settings.
- `run_wrf_restart.sh` changes into the run folder, moves existing `wrfout_*`
  files to `.orig`, copies an `rsl.out.*` log, removes old `*.diff_log` files,
  reruns WRF, and compares restart output with `diffwrf`.
- `compare_wrf.sh` creates a temporary comparison directory, runs `diffwrf`
  across `wrfinput_*` and `wrfout_*` files, then removes the temp directory.
- `custom_actions/run_wrf.py` can remove and recreate run directories, symlink
  executables and met/input files, and launch the shell wrappers through SANE.
- `tests/builds/builds.py` generates compile-scale CMake and legacy build
  permutations.
- `tests/regtests/wrf_coop.py` generates init, run, compare, and sync actions
  that depend on built WRF plus external case and met data.

## Safe Inspection

- Prefer `sed`, `rg`, `bash -n`, and `python -m py_compile` before any action
  execution.
- Do not invoke wrappers, SANE actions, WRF binaries, compile paths, regression
  suites, or HPC submissions without explicit approval.

## Orientation Rules

- Inspect the relevant script or test definition before inferring build path,
  run mode, or resource usage.
- Prefer syntax checks and file reads before invoking any SANE action.
- Require explicit user approval before builds, WRF runs, regression suites, or
  real HPC submissions.
