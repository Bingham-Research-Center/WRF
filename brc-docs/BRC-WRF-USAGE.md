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
- CHPC WRF practice currently lives in the adjacent knowledge checkout:
  `../brc-knowledge/scholarium/reference-base/resources/`.

The main BRC rule is simple: use this repo for source, documentation, and
validated wrappers; use CHPC scratch and group storage for heavy model work.

## Storage Layout

The WRF git checkout can stay in `$HOME`. That is the right place for source
code, small config files, docs, and Codex editing. Do not use `$HOME` as the
live run directory or as a dumping ground for `wrfout` files.

| Purpose | Recommended path | Notes |
| --- | --- | --- |
| WRF source checkout | `$HOME/gits/brc-wrf` | Good for git, Codex, docs, and small wrapper edits. |
| Per-user WRF/WPS build or install | `/uufs/chpc.utah.edu/common/home/lawson-group6/$USER/wrf_build/` | No purge; good for compiled artifacts and shared reproducibility. |
| Active case runs | `/scratch/general/vast/$USER/wrf_runs/<case>/` | Fast active I/O; 60-day purge; clean after archiving. |
| Shared WPS geography | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/` | Existing group geog path from the CHPC WRF guide. |
| Durable outputs | `/uufs/chpc.utah.edu/common/home/lawson-group6/$USER/wrf_archive/<case>/run_<UTC>/` | Archive `wrfout`, namelists, and key logs. |

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
- inspect storage with `df -hT`;
- inspect modules with `module spider`;
- run scheduler queries such as `squeue`, `sinfo`, and `sacctmgr`.

Do not run compile-scale or model-scale work on a login node:

- no WRF compile;
- no WPS `geogrid.exe`, `ungrib.exe`, or `metgrid.exe`;
- no `real.exe` or `wrf.exe`;
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

Do not assume either one is the BRC default until a CHPC build note says so. The
current CHPC WRF quickstart validates the legacy-style WRF/WPS setup, while this
repo also carries CMake-oriented documentation. The missing bridge is a
confirmed BRC CHPC recipe for this exact fork.

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

For this fork, the preferred installation shape should be out-of-source and
traceable:

```bash
export WRF_SRC=$HOME/gits/brc-wrf
export WRF_PREFIX=/uufs/chpc.utah.edu/common/home/lawson-group6/$USER/wrf_build/brc-wrf
export WRF_BUILD=$WRF_PREFIX/_build
export WRF_INSTALL=$WRF_PREFIX/install
```

Before making this an official recipe, validate the exact `configure_new` /
`compile_new` invocation on CHPC and record the Git SHA, module list, build path,
install path, and whether WPS is built beside it. Track that work in
`BRC-WRF-ROADMAP.md`.

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

Do not use bare `mpirun` for WRF on this Intel MPI stack. Do not use bare
`srun -n N ./wrf.exe` without `--mpi=pmi2`.

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

For ensembles, prefer job arrays with one run directory per member. Many smaller
single-node or partial-node runs are often better than one oversized WRF run,
because Basin-scale domains stop scaling efficiently after a few dozen ranks.

## Case Directory Shape

Use scratch for the active case:

```text
/scratch/general/vast/$USER/wrf_runs/<case>/
  grib_data/
  wps_run/
  wrf_run/
```

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
