# Handoff To Run New June 17

This is the cold-start prompt for a future session whose job is to re-run the
WRF practical pipeline from scratch. Do not execute this in the current session.

## Hard Rules

- Never run practical tests on a login node. No manifest hashing, NetCDF reads,
  quicklook rendering, staging plans, WPS, `real.exe`, `wrf.exe`, Python test
  suites, or data-heavy commands from `notchpeak1`/login shells.
- Use login nodes only to read/edit small docs, prepare scripts, submit approved
  Slurm work, and run scheduler queries.
- All NWP download/staging work stays in `../brc-tools`. Use Herbie-backed
  paths where that repo supports them, respect the direct NCEI path for
  historical NAM analysis, and run full transfers on `notchpeak-dtn`.
- Quicklook PNGs must not go into the repo checkout. Write them beside the
  durable archive run, for example
  `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/quicklooks/`.
- Keep repo roles separate: `brc-tools` stages GRIBs and emits manifests and
  contracts; `brc-wrf` consumes them through WPS/WRF and renders WRF-side
  evidence; `brc-knowledge` owns canonical CHPC settings.

## Lessons From The 2026-06-17 No-Run Pass

That pass was useful scientifically but wrong operationally because it ran from
`notchpeak1` login. It was fast because it reused existing artifacts rather than
testing the pipeline from scratch:

- no fresh DTN staging;
- no fresh `contract_<case>.json` validation from current staging output;
- no WPS/ungrib/metgrid execution;
- no `real.exe` or `wrf.exe`;
- PNGs were written into the repo-local ignored quicklook directory.

Those PNGs were later copied to:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_20260613T044846Z/quicklooks/
```

and the repo-local copies were removed.

Do not treat that pass as a full pipeline proof. Treat it as evidence that the
existing artifacts can be read and visualized.

## Goal For The New Session

Run a from-scratch practical pipeline test with explicit approval gates:

1. Start from clean repo states in `brc-tools`, `brc-wrf`, and `brc-knowledge`.
2. Allocate or submit work so all practical commands run off the login node.
3. Fresh-stage NAM-only inputs through `brc-tools` and produce current
   `manifest_<case>.json` and `contract_<case>.json`.
4. Validate the fresh contract from `brc-wrf` without using the reconstructed
   legacy fallback.
5. Run WPS for NAM-only, then stop and inspect `met_em` fields before any WRF
   integration.
6. If approved, run `real.exe`, then `wrf.exe`, archive to `lawson-group6`, and
   render quicklooks into the durable archive's `quicklooks/` directory.
7. Record command, Slurm job ID, host, repo commit, manifest path, contract
   path, WPS/WRF success markers, archive path, and PNG paths.
8. Preserve the rendered wrapper's compact debug artifacts:
   `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, and
   `debug/run_file_inventory.tsv`.

## Settings Snapshot To Read Back Before Running

| Setting | Current NAM-only baseline |
| --- | --- |
| Case | Jan-2013 Uinta Basin NAM-only baseline. |
| Window | 2013-01-31 12Z through 2013-02-02 00Z. |
| Domains | Two nested domains. |
| Forcing | NAM analysis only; fresh stage should come from `brc-tools`. |
| WPS cadence | 6-hourly, `interval_seconds = 21600`. |
| WPS stream | `Vtable.NAM`; current proof used WPS `FILE`/`FILE` prefix and `fg_name`. |
| Expected WPS output | 14 `met_em` files and `num_metgrid_levels = 40`. |
| Run profile | `lawson-np`, `notch392`, one node, 56 tasks, `900G`, `srun --mpi=pmi2`. |
| Storage | Scratch for live WPS/WRF I/O; `lawson-group6` for durable archive and quicklooks. |

## Five Gotchas To Say Out Loud

| Gotcha | What to do |
| --- | --- |
| Login-node creep | Anything that reads staged GRIBs, manifests, NetCDF, archives, or renders plots runs off-login. |
| WPS stream mismatch | Keep ungrib `prefix` and metgrid `fg_name` paired, for example `FILE`/`FILE` or `NAM`/`NAM`. |
| Cadence mismatch | NAM-only is 6-hourly; GEFS+NAM would be a separate 3-hourly proof. |
| MPI launcher | Use `srun --mpi=pmi2`; do not switch to bare `mpirun` or bare `srun -n`. |
| False single-status thinking | Check Slurm state, `real.exe`, `wrf.exe`, archive completeness, and quicklooks separately. |

## CHPC Defaults To Use Unless Rechecked

Re-check these against `../brc-knowledge/scholarium/reference-base/resources/`
before submission:

- WRF default: single-node `notch392` on `lawson-np`.
- Slurm: `--account=lawson-np`, `--partition=lawson-np`, `--nodelist=notch392`,
  `--nodes=1`, `--ntasks=56`, `--mem=900G`.
- Launcher: `real.exe` directly; `wrf.exe` with `srun --mpi=pmi2 -n
  "$SLURM_NTASKS" ./wrf.exe`.
- Live run I/O: `/scratch/general/vast/$USER/wrf_runs/<case>/`.
- Staged forcing: `/scratch/general/vast/$USER/wrf_inputs/<case>/`.
- Durable archive: `/uufs/chpc.utah.edu/common/home/lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/`.

The existing `brc-cases/wrf_case.py render-slurm` output was statically checked
against these settings after the June 17 retrospective. Its account, partition,
node, task count, memory, module stack, `real.exe`/`wrf.exe` sequence,
`srun --mpi=pmi2`, scratch run root, `lawson-group6` archive root, and
colon-safe `./wrfout_d0*` archive copy align with the current CHPC guidance.
The next session should still render a fresh script and compare it with
`wrf-on-chpc-quickstart.md` before submission.

## Stop Gates

| Gate | Stop until approved |
| --- | --- |
| DTN or network staging | Before any multi-GB download or transfer. |
| WPS | Before ungrib/metgrid if the source mix or Vtable differs from NAM-only. |
| `real.exe` | After WPS field inspection. |
| `wrf.exe` | After `real.exe` reaches `SUCCESS COMPLETE REAL_EM INIT`. |
| Benchmark sweep | Before changing task count, memory, or running multiple configurations. |
| GEFS+NAM | Keep separate from the NAM-only baseline; stop after metgrid field evidence unless explicitly approved. |

## Acceptance Evidence

- `brc-tools` fresh manifest verifies cleanly.
- `brc-wrf` strict validation passes against the fresh contract sidecar.
- WPS emits the expected `met_em` files and field set.
- `real.exe` log contains `SUCCESS COMPLETE REAL_EM INIT`.
- `wrf.exe` log contains `SUCCESS COMPLETE WRF`.
- Archive contains `wrfout_d0*`, `namelist.input`, `rsl.out.0000`,
  `rsl.error.0000`, `real.rsl.out.0000`, and `real.rsl.error.0000`.
- Archive contains `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`,
  and `debug/run_file_inventory.tsv`.
- Quicklooks are in the durable archive, not the repo.

## First Prompt For The Next Agent

```text
You are in ~/gits/brc-wrf. Read AGENTS.md, HANDOFF-TO-RUN-NEW-JUNE17.md,
doc/BRC_WRF_MICROTASK_HANDOFF.md, brc-cases/README.md, and the three CHPC
reference docs in ../brc-knowledge/scholarium/reference-base/resources/.

Goal: plan and then run a from-scratch NAM-only practical WRF pipeline test,
but never execute practical checks on a login node. Use Slurm/interactive
compute context for any command that reads staged data, WPS/WRF outputs, or
renders quicklooks. Keep quicklook PNGs in the durable lawson-group6 archive.

Start by rendering/reviewing the Slurm commands and asking for approval before
DTN staging, WPS, real.exe, wrf.exe, or benchmark sweeps.
```
