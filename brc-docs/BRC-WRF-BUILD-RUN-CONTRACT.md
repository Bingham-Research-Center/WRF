# BRC WRF Build/Run Contract

Gate: Roadmap Gate 1 - Build/run contract

Purpose: choose the John-owned build and run shape before compiling or running
anything. This is a planning artifact, not approval for compile-scale work,
WPS, `real.exe`, `wrf.exe`, Slurm submission, strict artifact reads, NetCDF
checks, archive inventories, or quicklook rendering.

Status update: Gates 2-11 have now passed. Keep this contract as the historical
build/run baseline, but do not resume at Gate 5 unless live evidence contradicts
the proof. The current lane is practical testing and post-run SOP/results docs.

Current operating branch:

| Field | Value |
| --- | --- |
| Branch | `john/wrf` |
| SHA | Check live with `git rev-parse HEAD`; do not trust this historical contract for current SHA. |
| Remote | `origin https://github.com/Bingham-Research-Center/WRF.git` |
| Practical chain | `scaling_t028` job `13550110` passed after executable-provenance and runtime-file staging fixes; other rows still need explicit approval |

## Historical Session Freeze

| Field | Value |
| --- | --- |
| Repo | `~/gits/brc-wrf` |
| Branch | `john/fix-end-to-end-workflow` |
| SHA | `48f2073d94df93482031cf5775bf1e6419a9321e` |
| Remote | `origin https://github.com/Bingham-Research-Center/WRF.git` |
| Host | `notchpeak1` |
| UTC time checked | `2026-06-18 04:11:31` |
| Dirty state | Existing modified docs plus new/untracked handoff docs; preserve before build. |
| Stop point | No compile, WPS, `real.exe`, `wrf.exe`, Slurm, strict artifact reads, NetCDF/archive checks, or quicklooks. |

This freeze records the pre-build decision point. Later proof evidence is below;
refresh live state before any new approval-gated execution.

## Source Evidence

| Decision area | Source |
| --- | --- |
| Repo boundaries and login-node limits | `AGENTS.md` |
| End-to-end gate map | `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` |
| Required gate order | `brc-docs/BRC-WRF-ROADMAP.md` |
| Current run-side queue | `doc/BRC_WRF_MICROTASK_HANDOFF.md` |
| Proven NAM-only case | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| Case validator and render behavior | `brc-cases/README.md` |
| CHPC node, partition, storage, module landscape | `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md` |
| WRF-specific build/run stack | `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md` |
| Input staging handoff | `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md` |
| Fresh manifest/contract expectations | `../brc-tools/docs/WRF-INPUT-STAGING.md` |

## Contract

| Field | Contract value |
| --- | --- |
| Target cluster/node | Notchpeak owned node `notch392`. |
| Account/partition | `lawson-np` / `lawson-np`. |
| Build host context | Approved compute/batch or interactive owned-node context; not a login-node compile. |
| WRF source root | `$HOME/gits/brc-wrf`. |
| WRF executable root | John's build from `$HOME/gits/brc-wrf`; Gate 2 proved `main/real.exe` and `main/wrf.exe`. |
| WRF configure path | Legacy `./configure` plus `./compile em_real` first. CMake stays a later comparison unless explicitly chosen. |
| WRF configure choices | Intel `dmpar`, basic nesting. Do not use `dm+sm` for this first proof. |
| Toolchain modules | `intel-oneapi-compilers/2021.4.0`, `intel-oneapi-mpi/2021.1.1`, `hdf5/1.14.3`, `netcdf-c/4.9.2`, `netcdf-fortran/4.6.1`. |
| Required env vars | `NETCDF=$(nf-config --prefix)`, `NETCDF_C=$(nc-config --prefix)`, `JASPERLIB=/usr/lib64`, `JASPERINC=/usr/include/jasper`. |
| WPS root | John-owned persistent WPS tree at `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS`. |
| WPS proof requirement | Gate 3 proved `geogrid.exe`, `ungrib.exe`, `metgrid.exe`, `link_grib.csh`, `ungrib/Variable_Tables/Vtable.NAM`, and GRIB2 flags in `configure.wps`. |
| Static geography | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/`. |
| Build log root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/`. |
| Active input root | `/scratch/general/vast/$USER/wrf_inputs/<case>/`, produced by `../brc-tools`. |
| Active run root | `/scratch/general/vast/$USER/wrf_runs/<case>/`. |
| Durable archive root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/<case>/run_<UTC>/`. |
| Proven first case | NAM-only Jan-2013 Uinta Basin, 12/4 km nest, `Vtable.NAM`, 6-hour cadence, `interval_seconds = 21600`. |
| Default run shape after build proof | One node, 56 tasks, `900G`, `srun --mpi=pmi2` for `wrf.exe`; `real.exe` direct. |
| Input contract | Fresh `brc-tools` staging should emit `manifest_<case>.json` and `contract_<case>.json`; the tracked reconstructed contract is fallback only. |

## Gate 2 Proof Evidence

Historical approval request that led to the successful proof:

```text
Approve compile-scale Gate 2 for John's brc-wrf checkout?

Plan:
1. Refresh branch, SHA, remote, dirty files, host, UTC time, and module state.
2. Use an approved owned-node compute/batch or interactive context, not the login node.
3. Load the validated Intel/HDF5/netCDF module stack and export NETCDF, NETCDF_C, JASPERLIB, and JASPERINC.
4. Configure WRF with the legacy path, Intel dmpar, and basic nesting.
5. Compile em_real from $HOME/gits/brc-wrf.
6. Write configure transcript, module list, compile log, and executable inventory under lawson-group6 build-log storage.

Expected evidence:
- configure.wrf with selected options.
- module list and key env vars.
- compile log outside the git checkout.
- main/real.exe and main/wrf.exe timestamps and sizes.

Stop point:
Compiled WRF proof only. No WPS, no real.exe, no wrf.exe, no sbatch run, no archive, and no quicklooks.
```

## Failure Stops

- Dirty source state cannot be explained before compile.
- The selected context is a login node.
- `NETCDF` resolves to the C prefix rather than the Fortran prefix.
- `netcdf.inc` is missing after configure.
- Configure choices differ from Intel `dmpar` plus basic nesting.
- Build logs or generated artifacts start accumulating as repo-local outputs.
- Any wrapper points at Michael Davies' WRF or WPS roots.

## Next Gate

Have John/Michael accept or reject
`brc-docs/BRC-WRF-GATE10-QUICKLOOK-REVIEW.md`, then approve exactly one next
benchmark row if the NAM-only visual baseline is good enough. The recommended
next row is still `scaling_t016`, but prepare that row's `WRF_RUN` with John's
executables and runtime files before rerendering the practical packet. Job
`13550555` failed before runtime evidence after using a node-local `/tmp`
packet; job `13550909` fixed Slurm logging but failed before `real.exe` because
runtime files were absent. Future staging, manifest hashing, strict artifact
reads, WPS execution, and new WRF submissions remain approval-gated.
