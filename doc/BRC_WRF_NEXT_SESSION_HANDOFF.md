# BRC WRF Next Session Handoff

Purpose: give the next Codex session a direct, evidence-driven path to resolve
the current `scaling_t016` blocker without drifting into visual inspection,
GEFS+NAM, memory sweeps, or broad WRF source work.

This is not approval to submit jobs or read heavy artifacts. It is a runbook for
what to verify, what to prepare only in an approved context, how to submit
exactly one row if approved, and what to document.

## Copy-Paste Prompt

```text
You are Codex in ~/gits/brc-wrf on branch john/wrf.

Goal: recover the next single practical benchmark gate, scaling_t016, from the
current setup failure. Stay scoped and evidence-driven.

First verify live state:
  git status --short --branch --untracked-files=all
  git branch -vv
  git rev-parse HEAD
  git rev-parse origin/john/wrf
  hostname
  date -u '+UTC %Y-%m-%d %H:%M:%S'

Read narrowly:
  AGENTS.md
  doc/BRC_WRF_NEXT_SESSION_HANDOFF.md
  doc/BRC_WRF_MICROTASK_HANDOFF.md
  brc-docs/BRC-WRF-ROADMAP.md Gate 11 and Optional Gates
  brc-cases/README.md
  brc-cases/jan2013_basin_nam.case.yaml

Known current truth to verify from disk/docs:
  HEAD/origin should be b68dab1efc7f760de28211503d4189bf1d08dabc or newer.
  Gates 0-11 are complete.
  scaling_t028 job 13550110 passed with John's WRF V4.8.0.
  scaling_t016 job 13550555 failed before WRF runtime because Slurm used
  node-local /tmp work/log paths.
  scaling_t016 job 13550909 fixed shared Slurm logging but failed before
  real.exe because the row-specific WRF_RUN lacked runtime physics/table files.
  Neither t016 attempt produced rsl.*, archive, debug, or benchmark evidence.

Cheap checks first:
  python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py brc-cases/test_wrf_case.py brc-cases/test_wrf_quicklook.py
  python brc-cases/test_wrf_case.py
  python brc-cases/test_wrf_quicklook.py
  python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
  python brc-cases/wrf_case.py render-no-run-report brc-cases/jan2013_basin_nam.case.yaml --memory-candidates 450G,600G
  git diff --check

Main lane:
  1. If approval is absent, stop at a precise approval request for preparing
     scaling_t016 WRF_RUN and submitting exactly scaling_t016.
  2. In approved batch/interactive context only, prepare the scaling_t016
     WRF_RUN from John's WRF build and the proven NAM-only run artifacts.
  3. Rerender a fresh packet after prep.
  4. Submit exactly scaling_t016.
  5. Monitor to completion/failure.
  6. Inspect only compact text evidence: Slurm state, shared batch stdout,
     rsl.out/error text, debug/run_debug_summary.txt,
     debug/run_phase_times.tsv, debug/run_file_inventory.tsv.
  7. Do not run quicklooks, NetCDF reads, manifest hashing, strict-files
     validation, WPS, or any second row.
  8. If t016 succeeds, update docs/results/approval packet, commit, push.
  9. If t016 fails, diagnose exact fatal, update docs, commit, push, stop.

Close out with branch/SHA/push state, Slurm job ID, shared log path, archive/debug
path or explicit absence, tests run, packet path, what was not run, and the next
single gate.
```

## Current State

Live state when this handoff was written:

| Field | Value |
| --- | --- |
| Branch | `john/wrf` |
| HEAD/origin | `b68dab1efc7f760de28211503d4189bf1d08dabc` |
| Date | `UTC 2026-06-19 02:21:23` |
| Worktree | Clean before this handoff edit |
| Host | `notchpeak1` |

Proof state:

| Item | Status | Evidence |
| --- | --- | --- |
| Gates 0-11 | Complete | See `brc-docs/BRC-WRF-ROADMAP.md`. |
| NAM-only proof | Complete | Fresh 2026-06-18 path through WPS, `real.exe`, `wrf.exe`, archive, quicklooks. |
| WRF executable root | John-owned | `paths.wrf_build = /uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf`. |
| WPS root | John-owned | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS`. |
| Practical row `scaling_t028` | Passed | Job `13550110`, 28 tasks, `900G`, archive debug under `practical_tests/scaling_t028/run_20260618T230858Z/debug/`. |
| Practical row `scaling_t016` | Not benchmarked | Jobs `13550555` and `13550909` both failed before WRF runtime evidence. |

`scaling_t016` failure chain:

| Job | What happened | Meaning |
| --- | --- | --- |
| `13550555` | Failed in `00:00:04`, exit `2:0`, before WRF runtime. Slurm workdir/stdout/stderr pointed to node-local `/tmp`. | Submission/log-path setup failure; not a benchmark result. |
| `13550909` | Failed in `00:00:04`, exit `2:0`, before `real.exe`. Shared stdout showed missing `CAMtr_volume_mixing_ratio`; compact metadata showed all required runtime physics/table files absent from the row-specific `WRF_RUN`. | Scenario preparation failure; not a benchmark result. |

Visible `13550909` evidence:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wrf_jan2013_nam_t016_13550909.out
```

Archive/debug absence for `scaling_t016` is expected until a row reaches the
debug setup and archive code:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t016/
```

## Boundaries

Hard boundaries for the next session:

| Do not do | Why |
| --- | --- |
| Do not point wrappers at Michael-owned WRF/WPS roots. | Michael's path is comparison evidence only. |
| Do not add downloader/staging code to `brc-wrf`. | `brc-tools` owns staging and contracts. |
| Do not run quicklooks or NetCDF reads. | The next blocker is row preparation, not visual QA. |
| Do not run manifest hashing or `--strict-files` on login nodes. | Those read staged/archive artifacts. |
| Do not run WPS, `real.exe`, or `wrf.exe` outside the approved Slurm wrapper. | Preserve approval boundaries and evidence trail. |
| Do not submit `scaling_t056`, baseline, or memory rows by default. | One row, inspect, document, stop. |
| Do not overwrite `AGENTS.md` with detailed task state. | Keep `AGENTS.md` as a lean router. |

Allowed login-node work:

| Work | Commands |
| --- | --- |
| Live state | `git status`, `git branch -vv`, `git rev-parse`, `hostname`, `date`. |
| Python syntax/tests | `python -m py_compile ...`; focused unit tests. |
| Case metadata validation | `python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml`. |
| Packet render | `python brc-cases/wrf_case.py render-no-run-report ...`. |
| Shell syntax | `bash -n <rendered>.slurm`. |
| Diff hygiene | `git diff --check`. |

## First Verification Commands

Run these before making any edit:

```bash
git status --short --branch --untracked-files=all
git branch -vv
git rev-parse HEAD
git rev-parse origin/john/wrf
hostname
date -u '+UTC %Y-%m-%d %H:%M:%S'
```

Then the cheap check loop:

```bash
python -m py_compile \
  brc-cases/wrf_case.py \
  brc-cases/wrf_quicklook.py \
  brc-cases/test_wrf_case.py \
  brc-cases/test_wrf_quicklook.py

python brc-cases/test_wrf_case.py
python brc-cases/test_wrf_quicklook.py

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml

python brc-cases/wrf_case.py render-no-run-report \
  brc-cases/jan2013_basin_nam.case.yaml \
  --memory-candidates 450G,600G

git diff --check
```

The no-run report prints the fresh report path and Gate 11 packet path. Keep
those exact paths in the closeout. Do not reuse older `/tmp` packets.

## Approval Request To Use If Needed

If the user has not explicitly approved the next Slurm work, stop and ask for
this:

```text
Approve one bounded compute action?

I will prepare only the scaling_t016 WRF_RUN in an approved batch/interactive
context using John's ~/gits/brc-wrf main/{real.exe,wrf.exe} and runtime files
from John's run/ directory, plus namelist.input and met_em files from the proven
NAM-only run artifacts. Then I will rerender the Gate 11 packet and submit
exactly scaling_t016. I will inspect only compact text evidence and stop on
success or first failure. I will not run quicklooks, NetCDF reads, WPS, strict
validation, manifest hashing, t056, baseline, or memory rows.
```

## Approved Preparation Plan

Run this only in an approved batch, DTN, or interactive compute context. It is
not login-node work because it copies and checks WRF run artifacts.

Scenario:

| Variable | Value |
| --- | --- |
| `SCENARIO` | `scaling_t016` |
| `JOHN_WRF_BUILD` | `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf` |
| `WRF_RUN` | `/scratch/general/vast/u0737349/wrf_runs/jan2013_basin_gefs/practical_tests/scaling_t016/wrf_run` |
| `ARCHIVE_ROOT` | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t016` |
| `PROVEN_WRF_RUN` | proven NAM-only run directory that supplied Gate 7/8 `namelist.input` and `met_em.d0*.nc` files |

Use the current proven run path from docs or disk. The default candidate named
in the case manifest is:

```text
/scratch/general/vast/u0737349/wrf_runs/jan2013_basin_gefs/wrf_run
```

Preparation template:

```bash
set -euo pipefail

JOHN_WRF_BUILD=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf
PROVEN_WRF_RUN=/scratch/general/vast/u0737349/wrf_runs/jan2013_basin_gefs/wrf_run
WRF_RUN=/scratch/general/vast/u0737349/wrf_runs/jan2013_basin_gefs/practical_tests/scaling_t016/wrf_run

test -x "$JOHN_WRF_BUILD/main/real.exe"
test -x "$JOHN_WRF_BUILD/main/wrf.exe"
test -d "$JOHN_WRF_BUILD/run"
test -f "$PROVEN_WRF_RUN/namelist.input"
compgen -G "$PROVEN_WRF_RUN/met_em.d0*.nc" >/dev/null

mkdir -p "$WRF_RUN"
rsync -av "$JOHN_WRF_BUILD"/main/real.exe "$WRF_RUN"/
rsync -av "$JOHN_WRF_BUILD"/main/wrf.exe "$WRF_RUN"/
rsync -av --exclude="*.exe" "$JOHN_WRF_BUILD"/run/ "$WRF_RUN"/
rsync -av "$PROVEN_WRF_RUN"/namelist.input "$WRF_RUN"/
rsync -av "$PROVEN_WRF_RUN"/met_em.d0*.nc "$WRF_RUN"/

cmp -s "$JOHN_WRF_BUILD/main/real.exe" "$WRF_RUN/real.exe"
cmp -s "$JOHN_WRF_BUILD/main/wrf.exe" "$WRF_RUN/wrf.exe"
test -f "$WRF_RUN/namelist.input"
compgen -G "$WRF_RUN/met_em.d0*.nc" >/dev/null

for runtime_file in \
  CAMtr_volume_mixing_ratio \
  RRTMG_LW_DATA \
  RRTMG_SW_DATA \
  ozone.formatted \
  ozone_lat.formatted \
  ozone_plev.formatted \
  GENPARM.TBL \
  LANDUSE.TBL \
  SOILPARM.TBL \
  VEGPARM.TBL
do
  test -f "$JOHN_WRF_BUILD/run/$runtime_file"
  test -f "$WRF_RUN/$runtime_file"
  cmp -s "$JOHN_WRF_BUILD/run/$runtime_file" "$WRF_RUN/$runtime_file"
done
```

If any check fails, do not submit. Record the exact missing path and stop.

## Rerender And Submit Exactly One Row

After preparation passes, return to `~/gits/brc-wrf` and rerender:

```bash
python brc-cases/wrf_case.py render-no-run-report \
  brc-cases/jan2013_basin_nam.case.yaml \
  --memory-candidates 450G,600G
```

Inspect the printed packet path. The `scaling_t016.slurm` file must include:

| Setting | Expected |
| --- | --- |
| Job name | `wrf_jan2013_nam_t016` |
| Account/partition | `lawson-np` / `lawson-np` |
| Node | `notch392` |
| Nodes/tasks | `1` node, `16` tasks |
| Memory/time | `900G`, `06:00:00` |
| Launcher | `srun --mpi=pmi2 -n "$SLURM_NTASKS" ./wrf.exe` |
| WRF source/build | `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf` |
| WRF run | `/scratch/general/vast/u0737349/wrf_runs/jan2013_basin_gefs/practical_tests/scaling_t016/wrf_run` |
| Archive root | `lawson-group6/.../wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t016` |
| Slurm chdir/output/error | shared `/uufs/.../wrf_build_logs/brc-wrf` path |

Check shell syntax:

```bash
bash -n /tmp/<fresh_packet>/prepare_scaling_t016.sh /tmp/<fresh_packet>/scaling_t016.slurm
```

The packet also includes `prepare_scaling_t016.sh`. Treat it as the preferred
approved-context copy/check helper after review. It requires
`BRC_PREP_APPROVED=YES`, refuses Michael-owned comparison paths, stages John's
`main/{real.exe,wrf.exe}` plus `run/` runtime files, copies only
`namelist.input`/`met_em` from the proven run artifacts, and does not submit
Slurm or execute WRF.

Submit only this row:

```bash
sbatch /tmp/<fresh_packet>/scaling_t016.slurm
```

Do not submit `scaling_t028`, `scaling_t056`, baseline, or memory rows in the
same pass.

## Monitoring And Evidence

Poll:

```bash
squeue -j <jobid> -h -o "%i|%T|%j|%M|%l|%D|%R"
```

When it leaves the queue:

```bash
sacct -j <jobid> --format=JobIDRaw,JobName,State,ExitCode,Elapsed,Nodelist,Start,End -P
```

If `sacct` fails from sandbox restrictions, rerun with escalation and explain it
is only Slurm accounting.

Inspect only compact text evidence:

| Evidence | Path or command |
| --- | --- |
| Shared batch log | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/wrf_jan2013_nam_t016_<jobid>.out` |
| WRF text logs | `rsl.out.0000`, `rsl.error.0000`, `real.rsl.out.0000`, `real.rsl.error.0000` in the row `WRF_RUN` or archive. |
| Debug summary | `<archive-run>/debug/run_debug_summary.txt` if archive/debug exists. |
| Phase times | `<archive-run>/debug/run_phase_times.tsv` if archive/debug exists. |
| File inventory | `<archive-run>/debug/run_file_inventory.tsv` if archive/debug exists. |
| Slurm state | `sacct` output. |

Do not read NetCDF files. Do not render quicklooks. Do not run archive-wide
inventories beyond the generated compact text files.

## Success Criteria

Treat `scaling_t016` as a benchmark row only if all of these exist:

| Required evidence | Why |
| --- | --- |
| Slurm state is `COMPLETED` or WRF success is separately proven if archive work fails. | Slurm success alone can hide post-run archive failures. |
| `real.exe` marker `SUCCESS COMPLETE REAL_EM INIT`. | Confirms initialization reached success. |
| `wrf.exe` marker `SUCCESS COMPLETE WRF`. | Confirms integration reached success. |
| `debug/run_phase_times.tsv`. | Records `real.exe`, marker checks, `wrf.exe`, and archive phase timings. |
| `debug/run_file_inventory.tsv`. | Provides compact file-count/byte evidence without broad archive inspection. |
| Archive path under `practical_tests/scaling_t016/run_<UTC>`. | Keeps row evidence durable. |
| Same source SHA, WRF/WPS roots, input contract, namelist, and forcing identity as the proven baseline. | Keeps comparison with `scaling_t028` meaningful. |

If `wrf.exe` succeeds but archive work fails, record those as separate facts.
Do not erase the WRF result.

## Failure Handling

If the row fails before `real.exe`:

1. Record the exact preflight missing path from shared stdout/stderr.
2. Record Slurm state, exit code, elapsed time, and node.
3. Check whether `rsl.*`, `brc_run_debug`, archive, or debug path exists.
4. Update the docs/approval packet with "not benchmark evidence".
5. Stop before any rerun unless the user explicitly approves the trivial fix
   and retry.

If `real.exe` fails:

1. Inspect `real.rsl.*` or `rsl.*` text only.
2. Record the first fatal/error block and phase table if created.
3. Do not run `wrf.exe`.
4. Update docs and stop.

If `wrf.exe` fails:

1. Inspect `rsl.out.0000`, `rsl.error.0000`, Slurm state, and phase table.
2. Record whether `SUCCESS COMPLETE WRF` is absent.
3. Do not submit another scaling/memory row.
4. Update docs and stop.

If archive work fails after WRF succeeds:

1. Preserve WRF success as a separate fact.
2. Record the archive phase failure.
3. Do not call the benchmark complete until durable evidence is repaired or
   explicitly accepted.

## Docs To Update After The Row

Update only files that carry practical-test truth:

| File | Update |
| --- | --- |
| `doc/BRC_WRF_MICROTASK_HANDOFF.md` | Practical-test status and next gate. |
| `brc-docs/BRC-WRF-ROADMAP.md` | Optional Gate B table and current practical evidence. |
| `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` | One-line current state and next move. |
| `brc-docs/BRC-WRF-FIRST-CASE.md` | First-case summary and next tests. |
| `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md` | John/Michael approval evidence. |
| Generated `APPROVAL_PACKET.md` | Fill exact row evidence if the packet is being handed off outside repo. |

Keep `AGENTS.md` lean. Touch it only if the router truth changes, not for row
tables or detailed task counts.

## Commit And Push

Run the cheap checks again:

```bash
python -m py_compile \
  brc-cases/wrf_case.py \
  brc-cases/wrf_quicklook.py \
  brc-cases/test_wrf_case.py \
  brc-cases/test_wrf_quicklook.py

python brc-cases/test_wrf_case.py
python brc-cases/test_wrf_quicklook.py
python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
git diff --check
```

Commit message shape:

```text
<subject about t016 result>

Record scaling_t016 job <jobid> as <success/failure> with Slurm state, exit
code, elapsed time, node, shared log path, archive/debug path, and exact
recommendation.

Tests: <commands>

Co-authored-by: John Lawson <john.lawson@usu.edu>
Co-authored-by: Codex <codex@openai.com>
```

Push `john/wrf` and re-check:

```bash
git push origin john/wrf
git status --short --branch --untracked-files=all
git rev-parse HEAD
git rev-parse origin/john/wrf
date -u '+UTC %Y-%m-%d %H:%M:%S'
```

## Closeout Template

Use this exact structure in the final response:

```text
Branch/SHA/push:
  john/wrf at <sha>; origin/john/wrf <matches/diverges>; worktree <clean/dirty>.

Slurm:
  submitted exactly <scenario>; job <jobid>; state <state>; exit <exit>;
  elapsed <time>; node <node>.

Evidence:
  shared log: <path>
  archive/debug: <path or absent>
  key fatal or success marker: <one line>

Tests:
  <commands run>

Report/packet:
  <fresh report path>
  <fresh Gate 11 packet path>

Not run:
  no quicklooks, NetCDF reads, manifest hashing, strict-files validation, WPS,
  extra rows, memory rows, or GEFS+NAM work.

Next single gate:
  <one concrete next step>
```

## If There Is No Approval

The best no-approval work is:

1. Render a fresh no-run report and packet.
2. Confirm generated `scaling_t016.slurm` has shared Slurm log paths and full
   preflight checks.
3. Draft the exact approval request above.
4. Optionally improve docs/tests if they would prevent a repeat misread.
5. Stop before file-copy prep, `sbatch`, WPS, `real.exe`, `wrf.exe`, strict
   validation, quicklook, NetCDF, or manifest-hash work.

Do not fill time by pursuing `scaling_t056`, memory right-sizing, or GEFS+NAM
unless the user explicitly changes the scope.
