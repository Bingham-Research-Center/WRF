# BRC WRF Usage

This is a short BRC-facing guide for using this WRF fork on CHPC. It is not an
upstream WRF manual. It records what is confirmed locally and what is inherited
from the Lawson group CHPC guide.

## What Is Special Here

This checkout is an upstream-style WRF tree with BRC-local guidance layered on
top. The extensionless `README` is still the upstream WRF version, notice,
release-note, and documentation index. `README.md`, `AGENTS.md`, and
`brc-docs/` are BRC-facing routing documents.

Important local facts:

- Current observed WRF baseline: `4.8.0`.
- Current checkout path: `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf`.
- Current session host when this guide was drafted: `notchpeak1`, a CHPC login
  node.
- Local automation under `.sane/wrf/` is useful context, but its current host
  config targets NCAR Derecho/PBS, not CHPC Slurm.
- Canonical CHPC infrastructure facts live in:
  `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md`.
- WRF-specific CHPC build/run details are delegated from that inventory to:
  `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md`.
- NWP input download code belongs in the parallel `../brc-tools` repo, using
  its Herbie/SynopticPy patterns and emitted WPS/WRF case contract rather than
  adding downloader logic here.

The main BRC rule is simple: use this repo for source, documentation, and
validated wrappers; use CHPC scratch and group storage for heavy model work.

## Storage Layout

The WRF git checkout can stay in `$HOME`. That is the right place for source
code, small config files, docs, and Codex editing. Do not use `$HOME` as the
live run directory or as a dumping ground for `wrfout` files.

| Purpose | Recommended path | Notes |
| --- | --- | --- |
| WRF source checkout | `$HOME/gits/brc-wrf` | Good for git, Codex, docs, and small wrapper edits. |
| Per-user WRF/WPS build or install | WRF source/build: `$HOME/gits/brc-wrf`; WPS root: `/uufs/chpc.utah.edu/common/home/lawson-group6/<user-or-namespace>/wrf_build/WPS/` | John's WRF should be compiled from his `brc-wrf` checkout before any run. WPS is separate and should be a John-owned persistent install, not another user's build. |
| Active case runs | `/scratch/general/vast/$USER/wrf_runs/<case>/` | Fast active I/O; 60-day purge; clean after archiving. |
| Shared WPS geography | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/` | Existing group geog path from the CHPC WRF guide. |
| Durable outputs | `/uufs/chpc.utah.edu/common/home/lawson-group6/<user-or-namespace>/wrf_archive/<case>/run_<UTC>/` | Archive `wrfout`, namelists, and key logs. |

Observed from `notchpeak1` on 2026-06-11: `$HOME` is 74 percent used,
`/scratch/general/vast` is available, and `lawson-group6` is mounted with about
17 TB free. Treat these as live facts that should be rechecked before a large
run.

## Login Node Boundary

Codex and humans can do low-impact preparation on a login node:

- read local docs with `sed`, `rg`, and `rg --files`;
- edit docs, namelists, templates, and wrapper scripts;
- run `git status`, `git diff`, and similar metadata commands;
- run `bash -n <script>` and `python -m py_compile <file>`;
- run path-only unit tests that do not read staged files, archives, or NetCDF;
- inspect storage with `df -hT`;
- inspect modules with `module spider`;
- run scheduler queries such as `squeue`, `sinfo`, and `sacctmgr`.

Do not run compile-scale or model-scale work on a login node:

- no WRF compile;
- no WPS `geogrid.exe`, `ungrib.exe`, or `metgrid.exe`;
- no `real.exe` or `wrf.exe`;
- no manifest hashing, strict artifact validation, NetCDF/archive reads, or
  quicklook check/render;
- no SANE build/run action;
- no real `sbatch` unless the user explicitly approves submission.

For interactive setup that is heavier than a login-node probe, request a small
owned-node shell first:

```bash
salloc -A lawson-np -p lawson-np -N 1 -n 4 --mem=16G -t 4:00:00
```

For WRF execution, prefer batch scripts.

## Build And Install Posture

Two WRF build paths exist in this checkout:

- legacy WRF: `./configure`, `./compile`, `./clean`;
- CMake-oriented WRF: `./configure_new`, `./compile_new`, `./cleanCMake.sh`.

The first CHPC proof should follow the legacy WRF/WPS path because the current
CHPC WRF quickstart validates that setup. The CMake-oriented path still matters
for this fork, but it should be treated as a later comparison until it is
validated on CHPC with the same level of evidence.

For AI-led build/run progression, use `../doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`
as the routing map. It keeps CHPC architecture choices in `brc-knowledge`,
treats Michael's proven build/run path as a yardstick only, and requires John's
WRF executables to be compiled from this fork rather than loaded as a prebuilt
WRF product.

The CHPC WRF guide validated this module stack for WRF/WPS work on Notchpeak:

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
```

The validated legacy WRF choices were Intel `dmpar` and basic nesting. WPS needs
the same module stack plus the `JASPER*` exports before configure so GRIB2
support is enabled.

For John's first proof, compile the WRF executable from his checked-out
`brc-wrf` source tree and keep build logs in persistent group storage:

```bash
export WRF_SRC=$HOME/gits/brc-wrf
export WRF_BUILD=$HOME/gits/brc-wrf
export BRC_WRF_BUILD_LOG_ROOT=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf
```

Before making this an official recipe, validate the exact legacy WRF/WPS
configure and compile sequence for this fork on CHPC and record the Git SHA,
module list, build path, compile logs, executables, and the separate WPS root.
Track any later CMake comparison separately in `BRC-WRF-ROADMAP.md`.

## Standard Run Pattern

For typical Uinta Basin WRF cases, the current group guidance is single-node
Notchpeak first:

- account and partition: `lawson-np`;
- preferred node for one production run: `notch392`;
- common size: `--nodes=1`, `--ntasks=56`;
- memory: often 180 GB is enough for documented 12/4 km cases, while 900 to
  950 GB reserves most of the large-memory node;
- launcher: `real.exe` directly, then `srun --mpi=pmi2 -n "$SLURM_NTASKS"
  ./wrf.exe`.

The current Jan-2013 case manifest uses the high-powered owned-node profile
(`profile: owned_notch392_max`): `notch392`, 56 tasks, and `900G`. This matches
the current `brc-knowledge` WRF quickstart for a non-preemptible single run.

Do not use bare `mpirun` for WRF on this Intel MPI stack. Do not use bare
`srun -n N ./wrf.exe` without `--mpi=pmi2`.

Before an approved run starts, read back the case settings in plain language:
case window, domains, forcing stream, WPS cadence, Vtable/prefix/`fg_name`,
expected `met_em`/levels, Slurm shape, launcher, live scratch path, and durable
archive path.

Minimum batch body:

```bash
set -euo pipefail

module purge
module load intel-oneapi-compilers/2021.4.0
module load intel-oneapi-mpi/2021.1.1
module load hdf5/1.14.3
module load netcdf-c/4.9.2
module load netcdf-fortran/4.6.1

export NETCDF=$(nf-config --prefix)
export NETCDF_C=$(nc-config --prefix)

cd "$SLURM_SUBMIT_DIR"

./real.exe
grep -q "SUCCESS COMPLETE REAL_EM INIT" rsl.out.0000
mv rsl.out.0000 real.rsl.out.0000
mv rsl.error.0000 real.rsl.error.0000

srun --mpi=pmi2 -n "$SLURM_NTASKS" ./wrf.exe
grep -q "SUCCESS COMPLETE WRF" rsl.out.0000
```

The maintained BRC run wrapper should also write compact debug artifacts beside
WRF's native logs and copy them to `<archive-run>/debug/`:

| File | Contents |
| --- | --- |
| `run_debug_summary.txt` | Settings readback, five gotchas, host, job ID, commit, paths, modules, final status. |
| `run_phase_times.tsv` | Start/end/elapsed/exit code for `real.exe`, marker checks, `wrf.exe`, and archive copies. |
| `run_file_inventory.tsv` | Counts, bytes, and newest mtimes for key output and log patterns. |

For ensembles, prefer job arrays with one run directory per member. Many smaller
single-node or partial-node runs are often better than one oversized WRF run,
because Basin-scale domains stop scaling efficiently after a few dozen ranks.

## Case Directory Shape

Use scratch for the active case:

```text
/scratch/general/vast/$USER/wrf_runs/<case>/
  grib_data/ -> /scratch/general/vast/$USER/wrf_inputs/<case>/<source>/
  wps_run/
  wrf_run/
```

Populate the separate scratch input directory from `../brc-tools` staging
scripts, for example:

```text
/scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/nam_analysis/
/scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json
/scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/contract_jan2013_basin_gefs.json
```

Read `contract_<case>.json` before WPS. It is the canonical input handshake from
`brc-tools`: staged source counts, cadence, valid window, suggested WPS
`fg_name`, and `interval_seconds`. The validated NAM-only path uses
`fg_name = 'NAM'` and `interval_seconds = 21600`. A fresh two-stream
GEFS+NAM stage should advertise `fg_name = 'GEFS','NAM'` and
`interval_seconds = 10800`, but that path still needs WPS/`real.exe` proof.

Then link or copy the relevant source directory into the case's `grib_data/`
path when staging WPS. This keeps the downloaded NWP inputs easy to keep, reuse,
or discard independently of the WRF run directory. It is scratch, not a durable
archive: anything important should be promoted later by an explicit archive
decision.

`brc-tools` already owns WRF-facing input staging and manifest verification. Do
not add an ad hoc downloader in this WRF tree. Use its Herbie-backed paths where
available, respect its direct NCEI path for historical NAM analysis, and run
full NWP transfer work on `notchpeak-dtn`. If WPS input behavior needs to
change, update `brc-tools` and keep this repo focused on the WPS/WRF
consumption contract.

In `wps_run/`, link the WPS executables, `link_grib.csh`, `Vtable`, and the
literal `geogrid` and `metgrid` directories. The names matter: `geogrid.exe`
looks for `geogrid/GEOGRID.TBL`, not `geogrid_dir/GEOGRID.TBL`.

Set `geog_data_path` in `namelist.wps` to:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/
```

In `wrf_run/`, symlink WRF run files and executables from the build, remove any
stale `met_em.*` inherited from the build run directory, then link the
case-specific `met_em.*` from `../wps_run/`.

Before `wrf.exe`, verify:

- `namelist.input` dates match `namelist.wps`;
- `num_metgrid_levels` matches the actual `met_em` files;
- `wrfinput_d0*` and `wrfbdy_d01` exist after `real.exe`;
- the Slurm script uses the right account, partition, node count, task count,
  memory, and `srun --mpi=pmi2`.

## Reference Files

- `README.md` and `AGENTS.md`: BRC repo routing and safety boundaries.
- `doc/BRC_FORK_GUIDE.md`: fork mental model and local-vs-upstream boundary.
- `doc/README.cmake_build`: CMake-oriented WRF build flow.
- `.sane/wrf/README.md`: local automation map and expensive-action boundaries.
- `brc-docs/BRC-WRF-FIRST-CASE.md`: current end-to-end Jan-2013 Basin proof
  path and evidence.
- `../brc-tools/docs/WRF-INPUT-STAGING.md`: WPS/WRF input staging contract,
  manifest verification, and two-stream backlog.
- `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md`:
  current WRF-on-CHPC operating guide.
- `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md`:
  canonical CHPC hardware, scheduler, and storage facts.
- `../brc-knowledge/scholarium/reference-base/resources/chpc-slurm-job-examples.md`:
  group Slurm examples and WRF ensemble advice.
- `../brc-knowledge/archive/runs/may2026_spillover/README.md`: frozen
  operational record for a recent WRF/WPS case.
- `../MICHAEL-WRF.md`: scratch note that seeded the BRC WRF path, storage, GFS,
  and guardrailed-script questions.
