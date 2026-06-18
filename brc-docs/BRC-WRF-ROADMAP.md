# BRC WRF End-To-End Roadmap

Purpose: give John or a cold-start AI session a concrete gate sequence for
getting `brc-wrf` compiled from John's checkout, paired with a John-owned WPS
root, running the proven NAM-only case on CHPC, archiving outputs, rendering
quicklooks, and then entering practical testing.

This is a roadmap, not approval. Compile-scale work, WPS, `real.exe`,
`wrf.exe`, Slurm submission, large staging, strict artifact reads, NetCDF
inspection, archive inventories, and quicklook rendering all require the
appropriate human-approved compute, batch, DTN, or interactive context.

## Gate Count

From the current state, expect 11 required gates before the system is genuinely
ready for practical testing, plus 3 optional or follow-on gates.

| Set | Gates | Meaning |
| --- | ---: | --- |
| Required baseline | 11 | John-owned WRF and WPS, NAM-only rerun, archive, quicklooks, and maintained test harness. |
| Optional science branch | 1 | GEFS+NAM WPS-only field proof if John chooses that path. |
| Practical testing branch | 2 | Scaling and memory sweeps after the baseline is repeatable. |

Current gate state as of 2026-06-18: Gates 0-4 have passed for John's owned
WRF/WPS build proof and metadata-only case-root review. The next required gate
is Gate 5, the fresh NAM-only input contract. Do not skip it by running WPS
against stale or assumed staging.

## Standing Rules

- Compile John's WRF from `~/gits/brc-wrf`; preserve branch, SHA, and dirty
  status as provenance.
- Use CHPC modules for compiler, MPI, HDF5, netCDF, Jasper, and related support
  only. Do not use a prebuilt CHPC WRF product.
- WPS must be John-owned too. Michael Davies' `lawson-group6/u6060939/wrf_build`
  tree is comparison evidence only.
- Read `../brc-knowledge` before selecting architecture, module stack, storage,
  Slurm flags, or run location.
- Keep `../brc-tools` as the input staging and contract owner.
- Put active WPS/WRF I/O under `/scratch/general/vast/$USER/wrf_runs/<case>/`.
- Put durable archives and quicklooks under
  `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/`.
- Keep generated logs, rendered one-off scripts, namelists, NetCDF, PNGs, and
  run artifacts out of this repo.

## Required Gates

| Gate | Name | Owner | Human approval needed to execute? | Done when |
| ---: | --- | --- | --- | --- |
| 0 | Live state freeze | `brc-wrf` | No | Branch, SHA, dirty files, remote, host, date, and current docs are recorded. |
| 1 | Build/run contract | `brc-wrf` + `brc-knowledge` | No for writing; yes before compile | A short contract names node, account, modules, WRF root, WPS root, build log root, scratch run root, archive root, configure choices, and stop points. |
| 2 | Approved WRF compile proof | `brc-wrf` | Yes | John's checkout configures and compiles `em_real`; `main/real.exe` and `main/wrf.exe` exist with logs and module evidence outside repo. |
| 3 | Approved John-owned WPS proof | John-owned WPS tree | Yes | WPS configures/builds or is verified under John's ownership; `geogrid.exe`, `ungrib.exe`, `metgrid.exe`, `link_grib.csh`, and `Vtable.NAM` exist; GRIB2 support is confirmed. |
| 4 | Case manifest root alignment | `brc-wrf` | No if metadata-only | `brc-cases` points to John-owned WRF/WPS roots and current scratch/archive paths; cheap validation and render-only review pass. |
| 5 | Fresh NAM-only input contract | `brc-tools` + `brc-wrf` | Yes if staging or artifact hashing is needed | Fresh `manifest_<case>.json` and `contract_<case>.json` exist on scratch; manifest verification and strict case validation pass off-login. |
| 6 | NAM-only WPS proof | WPS + `brc-wrf` | Yes | WPS runs with `Vtable.NAM`, paired prefix/`fg_name`, `interval_seconds = 21600`; `met_em` count, fields, levels, and warnings are recorded. |
| 7 | NAM-only `real.exe` proof | `brc-wrf` | Yes | John's `real.exe` reaches `SUCCESS COMPLETE REAL_EM INIT`; `wrfinput_d0*`, `wrfbdy_d01`, and `real.rsl.*` are preserved. |
| 8 | NAM-only `wrf.exe` proof | `brc-wrf` | Yes | John's `wrf.exe` runs on `notch392` with `srun --mpi=pmi2` and reaches `SUCCESS COMPLETE WRF`. |
| 9 | Archive proof | `brc-wrf` | Included in run approval | `wrfout`, namelists, WPS/WRF logs, debug files, and provenance records are copied to a timestamped `lawson-group6` archive. |
| 10 | Quicklook proof | `brc-wrf` | Yes if reading NetCDF/archive artifacts | Quicklook check/render runs from the new archive and writes PNGs plus summary stats under `<archive-run>/quicklooks/`. |
| 11 | Practical-test harness | `brc-wrf` | No for docs/templates; yes for submissions | Maintained wrapper, validation checklist, result tables, and approval prompts are ready for scaling/memory tests. |

## Gate 0 - Live State Freeze

Goal: make the current source and handoff state unambiguous before any build or
run work.

Login-node-safe commands:

```bash
git status --short --branch --untracked-files=all
git rev-parse HEAD
git remote -v
hostname
date -u '+UTC %Y-%m-%d %H:%M:%S'
```

Evidence to leave:

| Field | Example |
| --- | --- |
| Repo | `~/gits/brc-wrf` |
| Branch and SHA | current branch plus full commit SHA |
| Dirty files | exact `git status` list |
| Host/time | login host and UTC timestamp |
| Stop point | "No compile, WPS, WRF, Slurm, artifact reads, or quicklooks." |

## Gate 1 - Build/Run Contract

Goal: choose the approved build and run shape before compiling.

Read first:

| Need | Source |
| --- | --- |
| CHPC node, account, storage, scheduler, modules | `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md` |
| WRF build/run details | `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md` |
| Repo boundaries | `AGENTS.md`, `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` |

Contract fields:

| Field | Default or expected value |
| --- | --- |
| Target node | `notch392` |
| Account/partition | `lawson-np` / `lawson-np` |
| Build host | approved compute/batch context, not login-node compile |
| WRF source | `~/gits/brc-wrf` |
| WRF configure path | legacy `./configure` + `./compile em_real` first |
| WRF configure choices | Intel `dmpar`, basic nesting |
| Toolchain | Intel oneAPI compilers, Intel MPI, HDF5, NetCDF-C, NetCDF-Fortran |
| Env vars | `NETCDF=$(nf-config --prefix)`, `NETCDF_C=$(nc-config --prefix)`, `JASPERLIB`, `JASPERINC` |
| WPS root | John-owned persistent WPS tree |
| Build logs | `lawson-group6/<namespace>/wrf_build_logs/...` |
| Active run root | `/scratch/general/vast/$USER/wrf_runs/<case>/` |
| Archive root | `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/` |

Done when: a human can approve or reject the exact build/run plan without
guessing paths, modules, ownership, or stop points.

## Gate 2 - Approved WRF Compile Proof

Goal: build John's WRF from John's checkout and stop at executable proof.

Approval boundary: compile-scale work. Do not start this gate without explicit
human approval and a written stop point.

Expected evidence:

| Evidence | Notes |
| --- | --- |
| Source state | branch, SHA, dirty files before configure |
| Module state | `module -t list` and key env vars |
| Configure transcript | prompt choices and `configure.wrf` path |
| Compile log | persistent log outside repo |
| Executables | `main/real.exe`, `main/wrf.exe`, timestamps, sizes |
| Stop point | "Compiled only; no WPS, real, WRF, or Slurm run." |

Failure stops:

- `netcdf.inc` missing.
- Configure choice differs from contract.
- Build writes logs/artifacts into the git checkout in a way that will be hard
  to separate from source.
- Any temptation to point wrappers at Michael-owned WRF.

## Gate 3 - Approved John-Owned WPS Proof

Goal: build or verify a John-owned WPS root paired with John's WRF build.

Approval boundary: WPS configure/compile is compile-scale work.

Current status: passed on 2026-06-18.

| Field | Value |
| --- | --- |
| WPS source | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_sources/WPS-v4.6.0` |
| WPS root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS` |
| Evidence | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate3_20260618T054456Z_13539773/` |
| Slurm job | `13539773` on `notch392` |
| Configure choice | WPS v4.6.0 option `23`: Linux x86_64 Intel Classic compilers, `dmpar` |
| CHPC fix | Pin Intel MPI wrappers in `configure.wps`: `DM_FC = mpif90 -f90=$(SFC)`, `DM_CC = mpicc -cc=$(SCC)` |

Required WPS proof:

| Required item | Evidence |
| --- | --- |
| `geogrid.exe` | path, owner, timestamp, target if symlink |
| `ungrib.exe` | path, owner, timestamp, target if symlink |
| `metgrid.exe` | path, owner, timestamp, target if symlink |
| `link_grib.csh` | path |
| `Vtable.NAM` | path, normally under `ungrib/Variable_Tables/` |
| GRIB2 support | `configure.wps` includes JPEG2000/PNG support flags |
| Static geog | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/` reachable in the chosen context |

Failure stops:

- `JASPER*` was not exported before configure.
- `configure.wps` lacks GRIB2 support.
- The WPS root is Michael-owned or otherwise not John's operational root.

## Gate 4 - Case Manifest Root Alignment

Goal: make the `brc-cases` manifest point at the new John-owned executable
roots and current storage targets before any WPS/WRF run.

Current status: passed as a metadata-only review on 2026-06-18.

| Field | Value |
| --- | --- |
| Report | `/tmp/jan2013_basin_nam.gate4.20260618T054655Z.report.txt` |
| Rendered Slurm review | `/tmp/jan2013_basin_nam.gate4.20260618T054655Z.rendered.slurm` |
| Validation | `OK: no findings` |
| Submitted? | No. Rendered text only. |

Login-node-safe checks:

```bash
python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
python brc-cases/wrf_case.py render-slurm brc-cases/jan2013_basin_nam.case.yaml
```

Do not use strict validation on a login node if it reads staged inputs,
archives, WPS/WRF files, NetCDF, or generated artifacts.

Done when:

- The case manifest names John-owned WRF and WPS roots.
- Rendered Slurm text still uses `lawson-np`, `notch392`, 56 tasks, `900G`, and
  `srun --mpi=pmi2`.
- Active run and archive paths are outside the repo.
- The rendered wrapper keeps debug files:
  `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, and
  `debug/run_file_inventory.tsv`.

## Gate 5 - Fresh NAM-Only Input Contract

Goal: retire dependence on the reconstructed legacy fallback only after a fresh
`brc-tools` contract proves clean.

Owner split:

| Repo | Owns |
| --- | --- |
| `brc-tools` | GRIB staging, manifest, contract, token checks, DTN staging job |
| `brc-wrf` | consuming the contract, case validation, WPS/WRF run side |

Approval boundary: large staging, DTN submission, manifest hashing, strict file
validation, and artifact reads.

Expected off-login sequence after fresh staging exists:

```bash
python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/<case>/manifest_<case>.json

python brc-cases/wrf_case.py validate <review-case>.yaml --strict-files
```

Done when:

- The fresh `contract_<case>.json` records NAM-only cadence and WPS settings.
- Manifest verification passes.
- `wrf_case.py validate --strict-files` passes against the fresh contract.
- Any decision to retire `brc-cases/jan2013_basin_nam.contract.json` is explicit.

## Gate 6 - NAM-Only WPS Proof

Goal: rerun WPS using John-owned WPS against the proven NAM-only input lane.

Approval boundary: WPS execution.

Expected settings:

| Item | Expected |
| --- | --- |
| Stream | NAM-only |
| Vtable | `Vtable.NAM` |
| WPS prefix/`fg_name` | paired values, either `FILE`/`FILE` or `NAM`/`NAM` |
| Cadence | 6 hours |
| `interval_seconds` | `21600` |
| `geog_data_path` | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/` |

Evidence:

- `geogrid.log`, `ungrib.log`, `metgrid.log`.
- `met_em.d0*` count for both domains and expected time window.
- `num_metgrid_levels`.
- Required field list including land/soil/skin/snow fields.
- Warnings and whether they are fatal.

Stop point: stop before `real.exe` unless the approval explicitly included
`real.exe`.

## Gate 7 - NAM-Only `real.exe` Proof

Goal: prove John's compiled `real.exe` consumes the new WPS output.

Approval boundary: model preprocessing execution.

Evidence:

| Evidence | Required |
| --- | --- |
| Executable | John's WRF build path, not Michael-owned |
| Input | WPS `met_em` paths and count |
| Marker | `SUCCESS COMPLETE REAL_EM INIT` |
| Outputs | `wrfinput_d01`, `wrfinput_d02`, `wrfbdy_d01` |
| Logs | `real.rsl.out.0000`, `real.rsl.error.0000`, warnings |

Stop point: stop before `wrf.exe` unless the approval explicitly included WRF.

## Gate 8 - NAM-Only `wrf.exe` Proof

Goal: run John's compiled WRF on the proven NAM-only case.

Approval boundary: WRF model execution and Slurm submission.

Required run facts:

| Fact | Expected |
| --- | --- |
| Account/partition | `lawson-np` / `lawson-np` |
| Node | `notch392` |
| Shape | one node, 56 tasks, `900G` first |
| Launcher | `srun --mpi=pmi2 -n "$SLURM_NTASKS" ./wrf.exe` |
| Success marker | `SUCCESS COMPLETE WRF` in `rsl.out.0000` |

Evidence to keep separate:

- Slurm batch state.
- WRF step state.
- `real.exe` success marker.
- `wrf.exe` success marker.
- Archive success or failure.

Do not collapse a post-run archive failure into a model failure without checking
the WRF logs and output files.

## Gate 9 - Archive Proof

Goal: preserve the new run in durable storage with enough provenance to audit it.

Archive root:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/
```

Minimum archive contents:

| Category | Examples |
| --- | --- |
| Model output | `wrfout_d0*` |
| WRF logs | `rsl.out.0000`, `rsl.error.0000`, rank logs if kept |
| Real logs | `real.rsl.out.0000`, `real.rsl.error.0000` |
| Namelists | `namelist.input`, `namelist.wps` |
| Debug | `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, `debug/run_file_inventory.tsv` |
| Build/run provenance | branch, SHA, module list, WRF root, WPS root, manifest, contract |

WRF filenames contain colons. Archive local paths as local paths, for example:

```bash
rsync -av ./wrfout_d0* "$ARCHIVE_DIR/"
```

## Gate 10 - Quicklook Proof

Goal: prove the new archive can produce quicklooks suitable for scientific
review and practical testing triage.

Approval boundary: quicklook checks/renders read NetCDF and archive artifacts,
so run in approved compute/batch/interactive context, not on a login node.

Expected commands after the case manifest points at the new archive:

```bash
python brc-cases/wrf_quicklook.py check brc-cases/jan2013_basin_nam.case.yaml
python brc-cases/wrf_quicklook.py render brc-cases/jan2013_basin_nam.case.yaml
```

Done when:

- Quicklook check passes.
- PNGs are written under `<archive-run>/quicklooks/`, not the repo.
- A small summary stats table exists beside the PNGs or in the run record.
- Any blank, unit-broken, or physically suspicious image is called out before
  practical testing begins.

Useful improvement before practical testing: add Basin/domain overlays and
observation overlays only if the data path is already available or explicitly
approved.

## Gate 11 - Practical-Test Harness

Goal: turn the successful one-off proof into a repeatable launch and review
surface for practical testing.

Required pieces:

| Piece | Done when |
| --- | --- |
| Maintained Slurm wrapper | It renders from the case manifest and does not require hand-editing one-off paths. |
| Settings readback | Run logs show case window, forcing, WPS cadence, Vtable/prefix/`fg_name`, Slurm shape, launcher, scratch path, archive path. |
| Debug artifacts | Summary, phase timing, and file inventory are created for every run. |
| Validation checklist | Cheap metadata checks are separate from strict off-login artifact checks. |
| Result tables | Scaling and memory tables are ready but empty until approved runs happen. |
| Closeout prompt | A next AI session can pick up from exact commands, job IDs, archive paths, and stop points. |

Ready-for-practical-testing means: John can approve a scaling or memory run by
choosing a row in a table, not by reconstructing the entire WRF/WPS path from
memory.

## Optional Gate A - GEFS+NAM WPS-Only Field Proof

This is not on the default path to a repeatable NAM-only baseline.

Use it only if John chooses GEFS+NAM as the science path now.

Approval boundary: science branch plus WPS execution.

Stop point: after `metgrid`. Do not run `real.exe` until the field list and
warnings are reviewed.

Required evidence:

| Item | Evidence |
| --- | --- |
| Field map | `../brc-tools/docs/WRF-GEFS-NAM-FIELD-MAP.md` reviewed or patched |
| GEFS Vtable | selected or built with pressure split and specific-humidity reality reflected |
| Stream settings | separate ungrib streams and `fg_name = 'GEFS','NAM'` |
| Cadence | 3 hours, `interval_seconds = 10800` |
| `met_em` review | field list, levels, missing-field warnings, and decision before `real.exe` |

## Optional Gate B - Scaling Sweep

Goal: find the task-count knee for the proven case.

Approval boundary: Slurm and WRF execution.

Candidate table:

| Tasks | Memory | Expected use | Evidence |
| ---: | ---: | --- | --- |
| 16 | TBD | slower but cheaper baseline | wall time, sim hours, marker, archive |
| 28 | TBD | likely middle point | wall time, sim hours, marker, archive |
| 56 | `900G` first | high-power default | wall time, sim hours, marker, archive |

Do not compare runs unless source SHA, WRF/WPS roots, input contract, namelists,
and archive completeness are the same.

## Optional Gate C - Memory Right-Sizing

Goal: replace `900G` with an evidence-backed request for the proven case.

Approval boundary: Slurm and WRF execution.

Evidence:

| Run | Memory request | Peak memory evidence | WRF marker | Archive | Recommendation |
| --- | ---: | --- | --- | --- | --- |
| Baseline | `900G` | TBD | TBD | TBD | TBD |
| Candidate | TBD | TBD | TBD | TBD | TBD |

Stop if a lower-memory candidate changes model behavior, fails for non-memory
reasons that cannot be separated, or loses debug/archive evidence.

## AI Handoff Prompt

Paste this into a new AI session when the next step is end-to-end WRF progress:

```text
You are Codex in ~/gits/brc-wrf. Goal: advance John's end-to-end BRC WRF
workflow toward a compiled John-owned WRF, John-owned WPS, NAM-only rerun,
archive, quicklooks, and practical-test readiness.

First verify live state:
  git status --short --branch --untracked-files=all
  git rev-parse HEAD
  hostname
  date -u '+UTC %Y-%m-%d %H:%M:%S'

Read, in order:
1. AGENTS.md
2. doc/BRC_WRF_END_TO_END_AI_HANDOFF.md
3. brc-docs/BRC-WRF-ROADMAP.md
4. doc/BRC_WRF_MICROTASK_HANDOFF.md
5. brc-docs/BRC-WRF-FIRST-CASE.md
6. brc-cases/README.md
7. ../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md
8. ../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md
9. ../brc-tools/docs/HANDOFF-TO-BRC-WRF.md
10. ../brc-tools/docs/WRF-INPUT-STAGING.md

Pick exactly one gate from brc-docs/BRC-WRF-ROADMAP.md. Default next gate is
Gate 1, the build/run contract, unless a current handoff proves it is already
complete.

Hard boundaries:
- No compile, WPS, real.exe, wrf.exe, sbatch, large staging, strict artifact
  reads, NetCDF/archive practical checks, or quicklooks without explicit human
  approval.
- Do not point John's wrappers at Michael-owned WRF or WPS roots.
- Do not add downloader/staging logic to brc-wrf; that belongs in brc-tools.

Leave breadcrumbs: command, host/context, evidence path, owner repo, artifact
path, stop point, and the next gate.
```

## Closeout Format

End every gate with this compact record:

| Field | Value |
| --- | --- |
| Gate | number and name |
| Command(s) | exact command or "docs-only" |
| Host/context | login, DTN, interactive compute, or batch job ID |
| Source | repo, branch, SHA, dirty status |
| Evidence | log path, manifest, contract, archive, quicklooks, or doc path |
| Result | passed, failed, blocked, or parked |
| Stop point | what was deliberately not run |
| Next gate | one numbered gate and why |
