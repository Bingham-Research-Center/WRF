# BRC WRF Plan Mode Run Handoff

Purpose: give a fresh Codex Plan Mode session and John a practical, low-risk
route for improving the current BRC WRF workflow, inspecting existing proof
artifacts, and preparing a from-scratch NAM-only WRF rerun without losing the
approval boundaries.

This is a handoff and walkthrough, not approval. Do not run DTN staging, WPS,
`real.exe`, `wrf.exe`, Slurm submissions, strict artifact reads, NetCDF/archive
reads, quicklook rendering, scaling sweeps, or memory benchmarks until John has
explicitly approved the exact row and stop point.

## Copy-Paste Prompt For Plan Mode

```text
You are Codex in /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf on branch
john/wrf. Work in Plan Mode first.

Goal: choose the lowest-risk next WRF task, improve tests/docs/render-only
harnesses where possible, and prepare John for either manual inspection or an
approved from-scratch NAM-only WRF rerun. Do not run WPS, real.exe, wrf.exe,
sbatch, strict artifact reads, NetCDF/archive reads, quicklooks, staging, scaling,
or memory benchmarks unless John explicitly approves the exact action.

Start by verifying:
  git status --short --branch --untracked-files=all
  git rev-parse HEAD
  git rev-parse origin/john/wrf
  hostname
  date -u '+UTC %Y-%m-%d %H:%M:%S'

Read in order:
1. AGENTS.md
2. brc-docs/BRC-WRF-PLAN-MODE-RUN-HANDOFF.md
3. brc-docs/BRC-WRF-FIRST-CASE.md
4. brc-docs/BRC-WRF-ROADMAP.md, Gate 11 and Optional Gates
5. doc/BRC_WRF_MICROTASK_HANDOFF.md
6. brc-cases/README.md
7. brc-cases/wrf_case.py
8. brc-cases/wrf_quicklook.py only if planning quicklook inspection
9. ../brc-tools/docs/HANDOFF-TO-BRC-WRF.md
10. ../brc-tools/docs/WRF-INPUT-STAGING.md only if planning staging work

In Plan Mode, ask John to choose one lane:
A. low-hanging no-run tests/docs;
B. manual quicklook/data inspection walkthrough;
C. render/check Gate 11 practical-test packet and choose approval rows;
D. prepare a from-scratch NAM-only rerun command packet;
E. no-run GEFS+NAM two-stream design.

Keep repo boundaries explicit: brc-tools owns staging and contracts; brc-wrf owns
case manifests, validators, WRF run wrappers, WRF quicklooks, and practical
harnesses; brc-knowledge owns canonical CHPC scheduler/storage guidance.
```

## Current Truth To Preserve

Live state when this document was written:

| Field | Value |
| --- | --- |
| Branch | `john/wrf` |
| HEAD and origin | `1244fb3a943b1af5ee45ee31c052741161ff5433` |
| Host/time | `notchpeak1`, `UTC 2026-06-18 21:30:08` |
| Tracked state | Clean at that commit |
| Untracked state | Clean in `brc-wrf` at this freeze. |

Proven state:

| Topic | Current truth |
| --- | --- |
| Baseline case | NAM-only Jan-2013 Uinta Basin, 12/4 km nested, `2013-01-31_12:00:00` to `2013-02-02_00:00:00`. |
| Input cadence | `Vtable.NAM`, `interval_seconds = 21600`, fresh `brc-tools` NAM-only sidecars verified on 2026-06-18. |
| WRF/WPS ownership | John-owned WRF build and John-owned WPS v4.6.0; do not point wrappers at Michael-owned roots. |
| Run target | `lawson-np`, `notch392`, one node, 56 tasks, `900G`, `srun --mpi=pmi2`. |
| Gates | Roadmap Gates 0-11 passed; scaling/memory and GEFS+NAM are not proven. |
| Gate 11 | `render-practical-harness` writes review packet, baseline/scaling/memory scripts, `PREPARE_CHECKLIST.md`, and `APPROVAL_PACKET.md` outside the repo. |
| Practical testing | Started but blocked. Prep `13548706` completed; `scaling_t028` `13548709` failed in `wrf.exe`; downstream rows were canceled. |

## Directory Truth

Use this table when checking whether data is in the right place.

| Data class | Correct location | Wrong location |
| --- | --- | --- |
| Source checkout | `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf` | Scratch or generated run directories. |
| Input staging | `/scratch/general/vast/$USER/wrf_inputs/<case>/` | `brc-wrf` source tree. |
| Fresh manifest/contract | `/scratch/general/vast/$USER/wrf_inputs/<case>/manifest_<case>.json` and `contract_<case>.json` | Hand-edited repo-local substitutes, except the tracked reconstructed fallback contract already in `brc-cases/`. |
| Active WPS/WRF I/O | `/scratch/general/vast/$USER/wrf_runs/<case>/` | `$HOME/gits`, durable archive roots, or Michael-owned paths. |
| WPS run dir | `/scratch/general/vast/$USER/wrf_runs/<case>/wps_run/` | `WPS` source/build root. |
| WRF run dir | `/scratch/general/vast/$USER/wrf_runs/<case>/wrf_run/` or `practical_tests/<scenario>/wrf_run/` | Repo checkout or archive. |
| Durable archive | `/uufs/chpc.utah.edu/common/home/lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>.../` | Scratch-only storage. |
| Debug archive | `<archive-run>/debug/run_debug_summary.txt`, `run_phase_times.tsv`, `run_file_inventory.tsv` | Only in transient `wrf_run` after the job ends. |
| Quicklooks | `<archive-run>/quicklooks/*.png` | Repo-local PNG output. |
| Rendered review packets | `/tmp/brc_gate11_*` or another outside-repo review directory | Inside `brc-wrf`. |

Do not use login-node `find`, manifest hashing, NetCDF tools, quicklook helpers,
or archive inventories as a practical check. Those are approved-context tasks.

## Lowest-Hanging Fruit

These are good next tasks for Codex before asking John to spend allocation time.

| Priority | Task | Why | Stop point |
| ---: | --- | --- | --- |
| Done | Add tests for quicklook output path refusal and archive-run selection. | `brc-cases/test_wrf_quicklook.py` covers path-level behavior without opening NetCDF. | Keep actual quicklook checks/renders off-login. |
| 1 | Walk through existing Gate 10 quicklooks with John/Michael. | Lowest compute next step after path guardrails; it answers whether the NAM-only baseline is physically useful. | Visual/science decision only; no new WPS/WRF run. |
| Done | Add a one-command no-run report wrapper. | Captures host, SHA, case validate, render packet path, shell syntax, and status in one text report. | Report only; no strict files or artifact reads. |
| In progress | Diagnose the failed `scaling_t028` row. | It exposed the first real practical-test blocker. | Prove executable/source-run provenance before resubmitting dependent rows. |
| 3 | Write the practical-test SOP/result record. | The packet is now the approval surface for practical tests. | Include the failed-row lesson and resubmit guardrails. |
| 4 | Draft a GEFS+NAM two-stream design table. | Keeps science branch ready without WPS execution. | Stop before WPS and before `real.exe`. |
| 5 | Draft storage-retention decision notes. | Scratch purges; staged inputs and proof runs may need promotion. | No copy or inventory unless approved. |
| 6 | Add quicklook summary-stat output in `wrf_quicklook.py`. | Helps manual visual QA catch blank/unit-broken plots. | Only implement code/tests locally; run against NetCDF only in approved context. |
| 7 | Review docs for fallback-contract retirement wording. | Fresh Gate 5 sidecar passed, but retirement is a decision. | Do not delete `brc-cases/jan2013_basin_nam.contract.json` without explicit approval. |

## Cheap Local Tests

These are login-node-safe because they do not read staged GRIBs, WPS NetCDF,
archives, or quicklook PNGs.

```bash
python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py brc-cases/test_wrf_case.py brc-cases/test_wrf_quicklook.py

python brc-cases/test_wrf_case.py

python brc-cases/test_wrf_quicklook.py

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml

python brc-cases/wrf_case.py render-practical-harness \
  brc-cases/jan2013_basin_nam.case.yaml \
  --output-dir /tmp/brc_gate11_jan2013_basin_gefs_default

bash -n /tmp/brc_gate11_jan2013_basin_gefs_default/*.slurm

python brc-cases/wrf_case.py render-no-run-report \
  brc-cases/jan2013_basin_nam.case.yaml \
  --output /tmp/brc_wrf_no_run_report.md \
  --packet-dir /tmp/brc_wrf_no_run_report_gate11_packet \
  --slurm-output /tmp/brc_wrf_no_run_report_render.slurm

python brc-cases/wrf_case.py render-slurm \
  brc-cases/jan2013_basin_nam.case.yaml \
  --output /tmp/brc_gate11_baseline_render.slurm

bash -n /tmp/brc_gate11_baseline_render.slurm

git diff --check
```

Good result:

| Check | Expected |
| --- | --- |
| `py_compile` | exit `0` |
| `test_wrf_case.py` | 3 tests pass or more if expanded |
| metadata `validate` | `OK: no findings` |
| practical harness render | writes `README.md`, `PREPARE_CHECKLIST.md`, `APPROVAL_PACKET.md`, `baseline.slurm`, `scaling_t016.slurm`, `scaling_t028.slurm`, `scaling_t056.slurm` |
| `bash -n` | exit `0` |
| no-run report | writes a Markdown report, Gate 11 packet, standalone Slurm render, and explicit "not run" boundary under `/tmp` |
| `git diff --check` | no output |

## Approved-Context Practical Checks

Run these only inside approved batch, DTN, or interactive compute context.

```bash
# brc-tools owns this check; it hashes staged files.
python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json

# brc-wrf strict validation reads declared roots and artifacts.
python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml --strict-files

# Quicklook checks read manifest, WPS met_em, and archived WRF output.
python brc-cases/wrf_quicklook.py check \
  brc-cases/jan2013_basin_nam.case.yaml \
  --archive-run /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_gate8_20260618T062439Z_13540006

python brc-cases/wrf_quicklook.py render \
  brc-cases/jan2013_basin_nam.case.yaml \
  --archive-run /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_gate8_20260618T062439Z_13540006
```

Expected quicklook files:

| File | Inspect for |
| --- | --- |
| `wps_domain_terrain.png` | Nonblank terrain, d02 footprint inside d01, Basin domain in the intended place. |
| `wps_d02_landmask.png` | Plausible land/water mask and terrain contours; no shifted grid. |
| `wps_d02_skintemp_snow.png` | Physically plausible skin temperature and snow contour pattern for late January Basin conditions. |
| `wrf_d02_t2_10m_wind.png` | Plausible 2 m temperature, coherent 10 m wind vectors, no huge vector or unit artifact. |
| `wrf_d02_snow_depth.png` | Snow-depth field nonblank and terrain-related; no all-zero or all-missing pattern unless scientifically expected. |

## Manual Inspection Walkthrough

Use this as the human review checklist after an approved quicklook/check batch.

| Layer | What John should inspect | Pass signal | Red flag |
| --- | --- | --- | --- |
| Staging | Manifest and contract paths under `/scratch/general/vast/$USER/wrf_inputs/<case>/`. | Expected source count and `verify: OK`. | Manifest points to mixed or stale streams unintentionally. |
| WPS | `geogrid.log`, `ungrib.log`, `metgrid.log`, `met_em.d0*.nc` count. | 14 `met_em` files for d01/d02 at 6-hour cadence; `num_metgrid_levels = 40`. | Missing land/soil/skin/snow fields or fatal metgrid warnings. |
| `real.exe` | `real.rsl.out.0000`, `real.rsl.error.0000`, `wrfinput_d0*`, `wrfbdy_d01`. | `SUCCESS COMPLETE REAL_EM INIT`. | Missing boundary/input files, fatal soil/vertical-level errors. |
| `wrf.exe` | `rsl.out.0000`, `rsl.error.0000`, Slurm state. | `SUCCESS COMPLETE WRF`; 74 `wrfout_d0*` for the current proof. | WRF success missing, or Slurm failure confused with archive failure. |
| Archive | `<archive-run>/` plus `<archive-run>/debug/`. | `wrfout`, namelists, logs, debug summary, phase table, and inventory are present. | WRF succeeded but archive phases failed; record both separately. |
| Quicklooks | Five PNGs under `<archive-run>/quicklooks/`. | Nonblank, framed, coherent terrain/landmask/temperature/wind/snow. | Blank panels, extreme units, shifted domains, all-missing variables. |

Questions for John/Michael during visual review:

| Question | Why it matters |
| --- | --- |
| Does the nest cover the intended Uinta Basin area and surroundings? | Domain geometry is a human/science decision. |
| Are snow, landmask, terrain, and skin temperature plausible for Jan 31-Feb 2 2013? | Confirms WPS fields are meteorologically credible. |
| Are near-surface winds and temperatures plausible enough to use as a tuning baseline? | Determines whether practical tests should proceed. |
| Is NAM-only sufficient for the next science question, or is GEFS+NAM needed now? | Avoids spending WPS/WRF time on the wrong forcing path. |
| Should scratch staged inputs or run artifacts be promoted to durable group storage? | Prevents silent loss to scratch purge. |

## Gate 11 Practical-Test Walkthrough

Render the no-run packet:

```bash
python brc-cases/wrf_case.py render-practical-harness \
  brc-cases/jan2013_basin_nam.case.yaml \
  --output-dir /tmp/brc_gate11_jan2013_basin_gefs_default
```

Read in this order:

1. `/tmp/brc_gate11_jan2013_basin_gefs_default/README.md`
2. `/tmp/brc_gate11_jan2013_basin_gefs_default/PREPARE_CHECKLIST.md`
3. `/tmp/brc_gate11_jan2013_basin_gefs_default/APPROVAL_PACKET.md`
4. `baseline.slurm`, then `scaling_t016.slurm`, `scaling_t028.slurm`,
   `scaling_t056.slurm`

What to inspect:

| File | Inspect |
| --- | --- |
| `PREPARE_CHECKLIST.md` | Per-scenario `WRF_RUN` directories under `/scratch/general/vast/$USER/wrf_runs/<case>/practical_tests/<scenario>/wrf_run`. |
| `APPROVAL_PACKET.md` | Approval rows with job ID, Slurm state, WRF marker, wall time, sim hours, peak memory evidence, archive path, debug path, recommendation. |
| `*.slurm` | `#SBATCH` account/partition/node/tasks/memory/time, `srun --mpi=pmi2`, fail-fast checks, archive root under `lawson-group6`. |

Do not submit just because the scripts render. John must choose a row and approve
the exact scenario.

## From-Scratch NAM-Only Run Guide

This is the current best shape for John to run a fresh NAM-only proof. It is
written as a sequence of approval gates. A Plan Mode session should turn this
into an exact reviewed command packet before execution.

### 0. Choose The Case

Default first rerun:

| Field | Value |
| --- | --- |
| Case | `jan2013_basin_gefs` manifest, NAM-only proof identity |
| Case file | `brc-cases/jan2013_basin_nam.case.yaml` |
| Time window | `2013-01-31_12:00:00` to `2013-02-02_00:00:00` |
| Domains | 2, 12/4 km Basin nest |
| Forcing | `nam_analysis` |
| WPS cadence | `21600` seconds |
| Stop if | You are tempted to call this GEFS+NAM. It is NAM-only. |

### 1. Freeze Source State

Login-safe:

```bash
cd /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf
git status --short --branch --untracked-files=all
git rev-parse HEAD
git rev-parse origin/john/wrf
hostname
date -u '+UTC %Y-%m-%d %H:%M:%S'
python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
```

Record the branch, SHA, host, time, and dirty state in the run notes.

### 2. Stage Or Reuse NAM Inputs

Planning is login-safe:

```bash
cd /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-tools
python scripts/stage_wrf_inputs.py --plan --case jan2013_basin_gefs \
  --init-time "2013-01-31 12Z" --source nam_analysis
```

Actual staging or manifest verification is not login-safe. It belongs on DTN or
approved compute/batch context. The fresh known sidecars are:

```text
/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json
/scratch/general/vast/u0737349/wrf_inputs/jan2013_basin_gefs/contract_jan2013_basin_gefs.json
```

After approved staging/verification, return to `brc-wrf` and run strict
validation only in approved off-login context:

```bash
cd /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf
python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml --strict-files
```

### 3. Prepare WPS Run

Use approved batch/interactive compute context. Do not run this on a login node.

Required roots:

| Name | Path |
| --- | --- |
| WPS root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS` |
| Static geog | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/` |
| Input root | `/scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs` |
| Run root | `/scratch/general/vast/$USER/wrf_runs/jan2013_basin_gefs` |
| WPS run | `/scratch/general/vast/$USER/wrf_runs/jan2013_basin_gefs/wps_run` |

Preparation shape:

```bash
CASE=jan2013_basin_gefs
INPUT_ROOT=/scratch/general/vast/$USER/wrf_inputs/$CASE
RUN_ROOT=/scratch/general/vast/$USER/wrf_runs/$CASE
WPS_ROOT=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS
WPS_RUN=$RUN_ROOT/wps_run

mkdir -p "$RUN_ROOT/grib_data" "$WPS_RUN"
cd "$WPS_RUN"

# Use John-owned WPS only.
test -x "$WPS_ROOT/geogrid.exe"
test -x "$WPS_ROOT/ungrib.exe"
test -x "$WPS_ROOT/metgrid.exe"
test -f "$WPS_ROOT/link_grib.csh"
test -f "$WPS_ROOT/ungrib/Variable_Tables/Vtable.NAM"
```

Then prepare `namelist.wps` from the proven settings:

| Setting | Value |
| --- | --- |
| `start_date` | `2013-01-31_12:00:00` for both domains |
| `end_date` | `2013-02-02_00:00:00` for both domains |
| `interval_seconds` | `21600` |
| `geog_data_path` | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG/` |
| Vtable | `Vtable.NAM` |
| `prefix` and `fg_name` | Keep paired: either `NAM`/`NAM` or `FILE`/`FILE`. The fresh 2026-06-18 proof used `NAM`/`NAM`; older proof scratch used `FILE`/`FILE`. |

WPS execution, only after approval:

```bash
cd "$WPS_RUN"
ln -sf "$WPS_ROOT/geogrid.exe" .
ln -sf "$WPS_ROOT/ungrib.exe" .
ln -sf "$WPS_ROOT/metgrid.exe" .
ln -sf "$WPS_ROOT/link_grib.csh" .
ln -sf "$WPS_ROOT/ungrib/Variable_Tables/Vtable.NAM" Vtable

# Link staged NAM GRIB files from the approved input root.
./link_grib.csh "$INPUT_ROOT"/nam_analysis/*

./geogrid.exe
./ungrib.exe
./metgrid.exe
```

WPS pass criteria:

| Evidence | Expected |
| --- | --- |
| Logs | `geogrid.log`, `ungrib.log`, `metgrid.log` exist and have no fatal error. |
| `met_em` | 14 files for d01/d02 across the 6-hour cadence window. |
| Levels | `num_metgrid_levels = 40` in the downstream WRF namelist. |
| Required fields | Land/soil/skin/snow fields present. |
| Stop | Stop before `real.exe` unless approval includes `real.exe`. |

### 4. Prepare WRF Run

Use approved batch/interactive compute context.

Required roots:

| Name | Path |
| --- | --- |
| WRF source/build | `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf` |
| WRF run | `/scratch/general/vast/$USER/wrf_runs/jan2013_basin_gefs/wrf_run` |
| Archive root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs` |

Preparation shape:

```bash
WRF_SRC=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf
RUN_ROOT=/scratch/general/vast/$USER/wrf_runs/jan2013_basin_gefs
WPS_RUN=$RUN_ROOT/wps_run
WRF_RUN=$RUN_ROOT/wrf_run

mkdir -p "$WRF_RUN"
cd "$WRF_RUN"

# Use John's WRF build from this checkout, not Michael-owned roots.
test -x "$WRF_SRC/main/real.exe" || test -x "$WRF_SRC/run/real.exe" || test -x "$WRF_SRC/real.exe"
test -x "$WRF_SRC/main/wrf.exe" || test -x "$WRF_SRC/run/wrf.exe" || test -x "$WRF_SRC/wrf.exe"

# Copy or symlink executables according to the approved packet.
# Copy or create namelist.input from the proven settings.
# Link/copy WPS outputs only in approved context.
ln -sf "$WPS_RUN"/met_em.d0*.nc .
```

Before running, render and inspect the maintained wrapper:

```bash
cd /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf
python brc-cases/wrf_case.py render-slurm \
  brc-cases/jan2013_basin_nam.case.yaml \
  --output /tmp/jan2013_basin_nam.approved_review.slurm

bash -n /tmp/jan2013_basin_nam.approved_review.slurm
```

Inspect the rendered script for:

| Setting | Expected |
| --- | --- |
| Account/partition | `lawson-np` / `lawson-np` |
| Node | `notch392` |
| Tasks/memory | 56 tasks, `900G` for high-power default |
| Launcher | `srun --mpi=pmi2 -n "$SLURM_NTASKS" ./wrf.exe` |
| Debug files | `run_debug_summary.txt`, `run_phase_times.tsv`, `run_file_inventory.tsv` |
| Archive | `lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/run_<UTC>/` |
| Fail-fast checks | `real.exe`, `wrf.exe`, `namelist.input`, `met_em.d0*.nc` |

Submit only after John approves the rendered script and stop point:

```bash
sbatch /tmp/jan2013_basin_nam.approved_review.slurm
```

### 5. After The Job

Check these separately:

| Fact | Evidence |
| --- | --- |
| Slurm state | `sacct`/Slurm output or batch log, if available. |
| `real.exe` success | `SUCCESS COMPLETE REAL_EM INIT` in `real.rsl.out.0000`. |
| `wrf.exe` success | `SUCCESS COMPLETE WRF` in `rsl.out.0000`. |
| Archive success | Archive phases exit `0` in `debug/run_phase_times.tsv`; expected files in archive. |
| Debug summary | `<archive-run>/debug/run_debug_summary.txt`. |
| Inventory | `<archive-run>/debug/run_file_inventory.tsv`, including `wrfout_d0*` count. |

If WRF succeeds but archive copy fails, record WRF success and archive failure as
separate facts.

### 6. Quicklook The New Archive

Only in approved compute/batch/interactive context:

```bash
python brc-cases/wrf_quicklook.py check \
  brc-cases/jan2013_basin_nam.case.yaml \
  --archive-run <new-archive-run>

python brc-cases/wrf_quicklook.py render \
  brc-cases/jan2013_basin_nam.case.yaml \
  --archive-run <new-archive-run>
```

Expected output directory:

```text
<new-archive-run>/quicklooks/
```

Then John should inspect the five PNGs using the visual checklist above.

## Decision Points For John

| Decision | Default if unsure |
| --- | --- |
| Do we approve a from-scratch NAM-only rerun now? | No; render/check packets and inspect current quicklooks first. |
| Do we approve practical scaling at 16/28/56 tasks? | No; choose one row from `APPROVAL_PACKET.md` only after visual baseline review. |
| Do we test lower memory candidates? | Render candidates first, for example `--memory-candidates 450G,600G`, then approve one row. |
| Do we pursue GEFS+NAM now? | No unless the science question needs it; keep it as WPS-only field proof with stop after `metgrid`. |
| Do we retire the tracked reconstructed fallback contract? | No until compatibility and fresh sidecar policy are explicitly accepted. |
| Do we promote scratch inputs/artifacts to durable storage? | Decide after inventory and storage review; no blind copy from login. |

## Next-Session Prompt

Use this when the next session should stay low-compute and decide the next
science/benchmark step.

```text
You are Codex in /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf on
branch john/wrf.

Goal: diagnose the failed practical `scaling_t028` row, then walk John/Michael
through the Gate 10 quicklooks and practical-test evidence before choosing any
next lane.

First verify live state:
  git status --short --branch --untracked-files=all
  git rev-parse HEAD
  hostname
  date -u '+UTC %Y-%m-%d %H:%M:%S'

Read:
1. AGENTS.md
2. brc-docs/BRC-WRF-STATE-PLAYBOOK.md
3. brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md
4. brc-docs/BRC-WRF-FIRST-CASE.md
5. brc-cases/README.md
6. ../brc-tools/docs/walkthroughs/wrf-staging.md

Boundaries:
- Login-safe: syntax/tests, metadata validate, render-only Slurm or Gate 11 packet.
- Off-login approval required: manifest verification, strict artifact reads,
  NetCDF/archive reads, and quicklook check/render.
- Explicit run approval required: staging jobs, WPS, real.exe, wrf.exe, sbatch,
  scaling, or memory benchmarks.
- Do not point John's wrappers at Michael-owned WRF/WPS roots.

Default recommendation: start from job `13548709`. `real.exe` passed, then
`wrf.exe` failed with `CLWRF: 'CAMtr_volume_mixing_ratio' does not exist`; the
log reports WRF `V4.7.1`. Live diagnosis found the scenario `real.exe` and
`wrf.exe` symlinked through scratch to Michael Davies'
`lawson-group6/u6060939/wrf_build/WRF/main/` binaries. Source executables from
John's `~/gits/brc-wrf/main`, use approved proven artifacts only for
`namelist.input`/`met_em`, and verify byte-match before rerunning anything.
```

## Closeout Template

Every follow-up session should end with this table.

| Field | Value |
| --- | --- |
| Gate/item |  |
| Commands run |  |
| Host/context | login, DTN, interactive compute, or Slurm job ID |
| Source | branch, SHA, dirty status |
| Approval status | approved by whom, or not approved/not run |
| Evidence paths | render packet, Slurm logs, manifest, contract, archive, quicklooks |
| Owner repo | `brc-wrf`, `brc-tools`, or `brc-knowledge` |
| Result | passed, failed, parked, or not run |
| What was not run | explicit skipped compute/artifact reads |
| Dirty state | `git status --short --branch --untracked-files=all` |
| Commit/push status | SHA and remote branch |
| Next suggested item | one next lane |
