# BRC WRF Michael Practical Test Packet

This is the short handout for John/Michael pair-programming on the current
WRF workflow. It starts with a no-run walkthrough, then points at the first
practical-test attempt and the fix needed before resubmitting.

It is not blanket approval to run DTN staging, WPS, `real.exe`, `wrf.exe`,
Slurm jobs, large downloads, or new scaling sweeps. Those steps need a named
approval, scope, and stop point before they run.

## Goal For The First Session

By the end of the first session, Michael should be able to explain:

- which repo owns each layer of the workflow;
- where staged input, active runs, and durable archives live;
- which Jan-2013 Basin facts are proven;
- which commands are safe no-run checks;
- which settings are safe to edit in a case manifest; and
- where the first real WPS/WRF approval gate starts.

## Current Truth

| Topic | Current state |
| --- | --- |
| Proven case | Jan-2013 Uinta Basin, NAM-only, nested 12/4 km, 2013-01-31 12Z through 2013-02-02 00Z. |
| Proven model path | `brc-tools` staged inputs, WPS, `real.exe`, `wrf.exe`, archive, and no-run quicklooks. |
| Input identity | NAM-only, `Vtable.NAM`, `interval_seconds = 21600`. The old proof scratch used WPS default intermediate prefix `FILE`. |
| Not proven | GEFSv12 reforecast plus NAM two-stream forcing with `fg_name = 'GEFS','NAM'` and `interval_seconds = 10800`. |
| Current run profile | `owned_notch392_max`: `lawson-np`, `notch392`, one node, 56 tasks, `900G`, `srun --mpi=pmi2`. |
| Fresh staging contract | Fresh `brc-tools` staging should emit `manifest_<case>.json` and `contract_<case>.json`. This repo currently carries a reconstructed legacy NAM-only contract for strict validation. |
| Practical testing | Started but blocked. Prep `13548706` completed; `scaling_t028` job `13548709` failed in `wrf.exe`; downstream jobs were canceled. |

## Settings Readback Before Any Run

Use this terse table before starting an approved practical run.

| Setting | Current NAM-only baseline |
| --- | --- |
| Case window | Jan-2013 Uinta Basin, 2013-01-31 12Z through 2013-02-02 00Z. |
| Domains | Two nested domains. |
| Input stream | NAM analysis only, staged by `brc-tools`. |
| WPS cadence | 6-hourly, `interval_seconds = 21600`. |
| WPS naming | `Vtable.NAM`; keep ungrib `prefix` and metgrid `fg_name` paired. |
| WRF levels | `num_metgrid_levels = 40`; expected `met_em` count is 14. |
| Slurm shape | `lawson-np`, `notch392`, one node, 56 tasks, `900G`. |
| Launcher | `real.exe` direct; `wrf.exe` with `srun --mpi=pmi2`. |
| Storage | Scratch for live WPS/WRF I/O; `lawson-group6` for durable archive, debug logs, and quicklooks. |

## Five Gotchas

| Gotcha | Run habit |
| --- | --- |
| Login-node creep | Practical checks, manifests, NetCDF reads, archives, quicklooks, staging, WPS, and WRF run off-login only. |
| WPS stream mismatch | `prefix` and `fg_name` must match the intended stream, for example `FILE`/`FILE` or `NAM`/`NAM`. |
| Cadence mismatch | NAM-only is 6-hourly; GEFS+NAM is a separate, unproven 3-hourly path. |
| MPI launcher drift | Keep `srun --mpi=pmi2`; do not switch to bare `mpirun` or bare `srun -n`. |
| One status is not enough | Slurm state, `real.exe`, `wrf.exe`, archive completeness, and quicklooks are separate evidence. |

## Repo Split

| Repo | Owns | Do not add there |
| --- | --- | --- |
| `brc-tools` | NWP download/staging, manifests, contracts, input quicklooks. | WPS, `real.exe`, `wrf.exe`, or Slurm run profiles. |
| `brc-wrf` | WRF source, WPS/WRF consumption docs, case manifests, validators, Slurm rendering, WRF-output quicklooks. | NWP downloader or GRIB staging logic. |
| `brc-knowledge` | Canonical CHPC node, storage, scheduler, proxy, and validated example-script facts. | Repo-local code or case manifests. |

For downloads, use `brc-tools` with Herbie-backed paths where available. Full
NWP staging runs on `notchpeak-dtn`; `brc-wrf` only consumes the resulting
manifest and contract.

## Read Before Pairing

Read these in order:

1. `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
2. `brc-docs/BRC-WRF-FIRST-CASE.md`
3. `brc-cases/README.md`
4. `../brc-tools/docs/walkthroughs/wrf-staging.md`
5. `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`

Keep `doc/BRC_WRF_MICROTASK_HANDOFF.md` open as the detailed task board.

## No-Run Walkthrough

Start with login-safe checks. They read local metadata or render text only; they
do not hash staged files, open NetCDF, read archives, render quicklooks, or
submit work.

```bash
git status --short --branch --untracked-files=all

python -m py_compile \
  brc-cases/wrf_case.py \
  brc-cases/wrf_quicklook.py \
  brc-cases/test_wrf_case.py \
  brc-cases/test_wrf_quicklook.py

python brc-cases/test_wrf_case.py

python brc-cases/test_wrf_quicklook.py

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml

python brc-cases/wrf_case.py render-slurm \
  brc-cases/jan2013_basin_nam.case.yaml
```

Run these only in an approved compute/batch context or the appropriate transfer
node. They read staged files, archive files, or NetCDF-backed quicklook inputs.

```bash
python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml --strict-files

python brc-cases/wrf_quicklook.py check \
  brc-cases/jan2013_basin_nam.case.yaml
```

Optional no-run visual output, still off-login only:

```bash
python brc-cases/wrf_quicklook.py render \
  brc-cases/jan2013_basin_nam.case.yaml
```

The optional render writes PNGs beside the durable archive run under
`lawson-group6`, for example `<archive-run>/quicklooks/`. Repo-local PNG output
is refused.

For approved Slurm runs, the rendered wrapper adds compact debug files beside
WRF's `rsl.*` logs:

| Debug file | Why it exists |
| --- | --- |
| `debug/run_debug_summary.txt` | Settings readback, gotchas, host/job/commit, paths, modules, final status. |
| `debug/run_phase_times.tsv` | Phase timings and exit codes for `real.exe`, marker checks, `wrf.exe`, and archive copies. |
| `debug/run_file_inventory.tsv` | Counts, bytes, and newest mtimes for key WPS/WRF outputs and logs. |

### Latest Walkthrough Result

The 2026-06-17 walkthrough was run from `notchpeak1` login, not Slurm. That is
now recorded as a process mistake: do not repeat practical checks on a login
node. Future walkthroughs should run inside an approved compute allocation or
batch job.

It was fast because it reused existing artifacts:

- staged GRIB files under `/scratch/general/vast/$USER/wrf_inputs/`;
- existing WPS/WRF run files under `/scratch/general/vast/$USER/wrf_runs/`;
- the durable proof archive under `lawson-group6/jrlawson/wrf_archive/`; and
- quicklook PNG output that now belongs beside the durable archive run, not in
  the repo checkout.

The pass confirmed `28/28 OK` manifest verification, clean case validation, and
five nonblank quicklook PNGs. It did not prove any new WPS/WRF configuration.

## Settings To Inspect Or Change

Use `brc-cases/jan2013_basin_nam.case.yaml` as the first settings map.

| Setting group | Keys or files | Safe no-run action |
| --- | --- | --- |
| NWP source | `forcing.sources`, `forcing.wps_fg_name`, `forcing.interval_seconds`, `forcing.contract_path` | Inspect or draft a copied case manifest. Do not claim GEFS+NAM works until WPS evidence exists. |
| Input destination | `paths.input_root`, `paths.grib_data` | Confirm the scratch input path. New staging belongs in `brc-tools` and may need DTN approval. |
| Run destination | `paths.run_root`, `paths.wps_run`, `paths.wrf_run` | Confirm the active scratch layout. Do not run WPS/WRF from the git checkout. |
| Archive destination | `paths.archive_root`, `archive.required_patterns`, `archive.colon_safe_wrfout_source` | Confirm durable output target and colon-safe `wrfout` handling. |
| WPS details | `wps.vtable`, `wps.ungrib_prefix`, `wps.namelist_fg_name`, `paths.geog_data_path` | Check consistency. WPS execution is a separate approval gate. |
| WRF runtime | `slurm.profile`, `slurm.ntasks`, `slurm.memory`, `slurm.nodelist`, `slurm.mpi_launcher` | Render and review Slurm text only. No `sbatch` without explicit approval. |

## First Practical Tests

| Order | Test | Why first | Stop point |
| ---: | --- | --- | --- |
| 1 | Practical-source diagnosis | The first benchmark used an incompatible WRF/run setup; log reports WRF `V4.7.1` and missing `CAMtr_volume_mixing_ratio`. | Prove source `wrf_run`, `real.exe`, `wrf.exe`, `namelist.input`, and `met_em` provenance before any resubmit. |
| 2 | WRF scaling/memory benchmark | Finds whether 16, 28, or 56 tasks and a smaller memory request are enough. | Resubmit only after source diagnosis; record timing, memory evidence, WRF marker, and archive path. |
| 3 | GEFS+NAM WPS-only field proof | Checks whether the two-stream forcing design has the needed fields. | Stop after `metgrid`; show `met_em` field list, `num_metgrid_levels`, and warnings. Do not run `real.exe`. |
| 4 | Fresh NAM-only contract retirement decision | Fresh Gate 5 sidecars passed, but retiring the tracked fallback is still a policy decision. | Do not delete `brc-cases/jan2013_basin_nam.contract.json` without explicit approval. |

Current practical packet:

```text
/tmp/brc_gate11_jan2013_basin_gefs_20260618T2118Z/
```

Failure evidence:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t028/run_20260618T213126Z/debug/
```

## Approval Gates

Before any approved run, write down:

| Item | Value |
| --- | --- |
| Approved by | TBD |
| Approval date/time | TBD |
| Repo and command scope | TBD |
| Data source | `NAM-only` or `GEFS+NAM` |
| Input destination | `/scratch/general/vast/$USER/wrf_inputs/<case>/` |
| Run destination | `/scratch/general/vast/$USER/wrf_runs/<case>/` |
| Archive destination | `/uufs/chpc.utah.edu/common/home/lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/` |
| Stop point | `fresh contract validation`, `metgrid only`, `real.exe only`, or `full WRF` |
| Evidence to preserve | Command, log path, manifest/contract path, WPS/WRF markers, archive path, debug TSV/text files |

## Result Table

Use this table during the no-run walkthrough.

| Check | Command or file | Expected result | Observed result | Follow-up |
| --- | --- | --- | --- | --- |
| Git state | `git status --short --branch --untracked-files=all` | Clean or intentionally dirty | TBD | TBD |
| Case metadata | `wrf_case.py validate` | Pass | TBD | TBD |
| Input manifest | `stage_wrf_inputs.py --verify-manifest` | Existing proof manifest verifies | TBD | TBD |
| Strict case files | `wrf_case.py validate --strict-files` | Pass against current reconstructed contract | TBD | TBD |
| Quicklook check | `wrf_quicklook.py check` | Finds required existing proof artifacts | TBD | TBD |
| Slurm render | `wrf_case.py render-slurm` | Text only, no submission | TBD | TBD |

Use this table before changing settings.

| Setting | Current value | Proposed value | File to edit | Proof needed before use |
| --- | --- | --- | --- | --- |
| NWP source | `nam_analysis` | TBD | `*.case.yaml` and `brc-tools` staging config | Fresh manifest/contract and WPS field evidence |
| WPS `fg_name` | `NAM` intent, old proof scratch used `FILE` | TBD | `*.case.yaml`, `namelist.wps` draft | Paired ungrib prefix and metgrid output |
| `interval_seconds` | `21600` | TBD | `*.case.yaml`, WPS/WRF namelists | Cadence matches staged inputs |
| Tasks | `56` | TBD | Slurm profile/template | Approved benchmark |
| Memory | `900G` | TBD | Slurm profile/template | Approved benchmark and peak memory evidence |

## What To Hand Around

Use these Markdown sources and rendered PDFs as the handout set:

- `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md`
- `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
- `brc-docs/BRC-WRF-FIRST-CASE.md`
- `brc-cases/README.md`

Recommended PDF output directory:

```text
brc-docs/handouts/
```

Render with the local Markdown-to-PDF wrapper:

```bash
md2pdf brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md \
  -o brc-docs/handouts/BRC-WRF-MICHAEL-PRACTICAL-PACKET.pdf
md2pdf brc-docs/BRC-WRF-STATE-PLAYBOOK.md \
  -o brc-docs/handouts/BRC-WRF-STATE-PLAYBOOK.pdf
md2pdf brc-docs/BRC-WRF-FIRST-CASE.md \
  -o brc-docs/handouts/BRC-WRF-FIRST-CASE.pdf
md2pdf brc-cases/README.md \
  -o brc-docs/handouts/BRC-WRF-CASE-SCAFFOLDS.pdf
```
