# BRC WRF Michael Practical Test Packet

This is the short handout for John/Michael pair-programming on the current
WRF workflow. It is meant for a no-run walkthrough first, then for planning the
first approved practical tests.

It is not approval to run DTN staging, WPS, `real.exe`, `wrf.exe`, Slurm jobs,
large downloads, or scaling sweeps. Those steps need a named human approval,
scope, and stop point before they run.

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

## Repo Split

| Repo | Owns | Do not add there |
| --- | --- | --- |
| `brc-tools` | NWP download/staging, manifests, contracts, input quicklooks. | WPS, `real.exe`, `wrf.exe`, or Slurm run profiles. |
| `brc-wrf` | WRF source, WPS/WRF consumption docs, case manifests, validators, Slurm rendering, WRF-output quicklooks. | NWP downloader or GRIB staging logic. |
| `brc-knowledge` | Canonical CHPC node, storage, scheduler, proxy, and validated example-script facts. | Repo-local code or case manifests. |

## Read Before Pairing

Read these in order:

1. `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
2. `brc-docs/BRC-WRF-FIRST-CASE.md`
3. `brc-cases/README.md`
4. `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`

Keep `doc/BRC_WRF_MICROTASK_HANDOFF.md` open as the detailed task board.

## No-Run Walkthrough

Run these from `~/gits/brc-wrf`. They read metadata, verify existing files, or
render text/plots from existing proof artifacts. They do not submit work.

```bash
git status --short --branch --untracked-files=all

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml

python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml --strict-files

python brc-cases/wrf_quicklook.py check \
  brc-cases/jan2013_basin_nam.case.yaml

python brc-cases/wrf_case.py render-slurm \
  brc-cases/jan2013_basin_nam.case.yaml
```

Optional no-run visual output:

```bash
python brc-cases/wrf_quicklook.py render \
  brc-cases/jan2013_basin_nam.case.yaml
```

The optional render writes ignored PNGs under
`brc-cases/quicklooks/jan2013_basin_gefs/`.

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
| 1 | Fresh NAM-only contract validation | Proves a new `brc-tools` sidecar can replace the reconstructed legacy contract. | `wrf_case.py validate --strict-files` passes against fresh `contract_<case>.json`. |
| 2 | GEFS+NAM WPS-only field proof | Checks whether the two-stream forcing design has the needed fields. | Stop after `metgrid`; show `met_em` field list, `num_metgrid_levels`, and warnings. Do not run `real.exe`. |
| 3 | WRF scaling/memory benchmark | Finds whether 16, 28, or 56 tasks and a smaller memory request are enough. | Requires approved `sbatch`; record timing, memory evidence, WRF marker, and archive path. |

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
| Evidence to preserve | Command, log path, manifest/contract path, WPS/WRF markers, archive path |

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
