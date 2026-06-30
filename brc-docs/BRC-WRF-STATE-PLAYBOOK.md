# BRC WRF State Playbook

Short print-oriented explanation for John/JRL and Michael. It describes where
the current `brc-wrf` fork fits, what is proven, and what should happen next.

## One-Sentence State

We have a BRC-local review layer around WRF 4.8.0, and one NAM-only Jan-2013
Basin case is proven through `brc-tools` input staging, WPS, `real.exe`,
`wrf.exe`, archive checks, no-run quicklooks, and a maintained practical-test
harness; the first practical 28-task row now passes after fixing executable
provenance and WRF runtime-file staging.

## Mental Model

| Layer | Owns | Does not own |
| --- | --- | --- |
| `brc-tools` | Downloading/staging WRF-ready GRIB files, manifests, contracts, input quicklooks. | WPS, `real.exe`, `wrf.exe`, Slurm run wrappers. |
| `brc-wrf` | WRF source, WPS/WRF consumption docs, case manifests, validators, Slurm rendering, WRF-output quicklooks. | NWP downloader logic. |
| `brc-knowledge` | Canonical CHPC hardware, storage, scheduler, and validated example Slurm scripts. | Repo-local code or case manifests. |

The AI tooling is useful because it keeps these contracts visible and checks
cheap facts before expensive runs. It is also another layer to audit, so every
AI-assisted step should leave a small, readable breadcrumb: command, evidence,
owner repo, and stop point.

## Collaboration Boundary

| Need | John-owned path | Michael/private path |
| --- | --- | --- |
| Production proof | `brc-wrf` consumes `brc-tools` contracts and runs John-owned WRF 4.8.0/WPS. | Comparison evidence and workflow review only. |
| Forcing experiments | One source at a time through `brc-tools`, then WRF-side Vtable/field review. | Review WPS/Vtable assumptions, field completeness, and gotchas. |
| Run safety | Approval-gated Slurm, archive, debug summaries, path refusal, byte-match checks. | Teaching examples and gotcha patterns that may be ported after review. |
| Scientific review | Baseline quicklooks, standardized comparison products, case manifests. | Pair review of domain, fields, physics plausibility, and failure modes. |

Do not use Michael-owned WRF/WPS roots for John production wrappers, WRF 4.8.0
proof, production archives, or `brc-tools` staging truth.

## Who Can Understand This Today?

| Audience | Current readiness | What still feels hard |
| --- | --- | --- |
| John/JRL | High enough to audit and steer science decisions. | Source hot-swapping should stay one forcing source at a time through `brc-tools` contracts; the old GEFS+NAM two-stream idea is parked. |
| Michael/new developer | Medium if starting from the reading packet below. | WRF requires both software-install knowledge and meteorological forcing knowledge; the repo split must be read first. |
| Future AI agent | High for no-run review tasks. | It must not confuse the maintained render harness with approval to run WPS/WRF/Slurm. |

## Where We Are

| Area | Status |
| --- | --- |
| Fork orientation | Usable. `README.md`, `AGENTS.md`, and `doc/BRC_FORK_GUIDE.md` explain the local layer. |
| CHPC posture | Usable. Canonical CHPC facts live in `brc-knowledge`; this repo points there. |
| First case | Proven NAM-only path for Jan 31-Feb 2 2013, d01/d02 Basin nest. |
| Case review | Usable. `brc-cases/wrf_case.py` validates metadata, renders Slurm text, and renders the Gate 11 practical-test packet only. |
| WRF/WPS build proof | Gates 2-3 passed. John's `main/real.exe` and `main/wrf.exe` exist, and John-owned WPS v4.6.0 is built at `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS`. |
| Visual QA | Usable off-login. `brc-cases/wrf_quicklook.py` checks existing artifacts and renders a standardized 10-PNG set per WRF domain; path-only unit tests are login-safe. |
| Practical-test harness | Usable. `wrf_case.py render-practical-harness` writes review packets outside the repo with approval-gated `prepare_<scenario>.sh` helpers, scaling/memory scripts, and blank result tables. |
| Practical testing | One 28-task row passed. Job `13550110` ran John's `~/gits/brc-wrf` WRF `V4.8.0`, passed `real.exe`/`wrf.exe`, and archived debug evidence under `practical_tests/scaling_t028/run_20260618T230858Z/`. Attempted `scaling_t016` jobs `13550555` and `13550909` failed before WRF runtime evidence: first from node-local `/tmp` Slurm paths, then from a `WRF_RUN` missing runtime files from John's `run/` directory. No `rsl.*`, archive, or debug evidence exists for `scaling_t016`. Memory rows remain unrun. |
| Gate 10 visual review | Preliminary PNG-only visual sanity passed; see `brc-docs/BRC-WRF-GATE10-QUICKLOOK-REVIEW.md`. John/Michael science acceptance is still the decision point. |
| Slurm profile | Aligned to max owned-node profile: `lawson-np`, `notch392`, 1 node, 56 tasks, `900G`, `srun --mpi=pmi2`. |
| Alternate forcing | Active direction is one-source-at-a-time hot-swapping through `brc-tools` staging contracts, starting with RAP feasibility. The older GEFS+NAM two-stream idea is parked, not a working production method. |

## Where We Should Go Next

| Order | Next move | Stop point |
| --- | --- | --- |
| 1 | Have John/Michael accept or reject the Gate 10 quicklook review. | Decide whether the NAM-only proof remains a physically useful baseline. |
| 2 | Decide whether to reapprove exactly one practical benchmark row. | Recommended next row is still `scaling_t016`; use the generated `prepare_scaling_t016.sh` in an approved off-login context, then submit exactly one row and stop on its result. |
| 3 | Continue alternate-forcing hot-swap work only through a concrete source contract. | `brc-tools` now has RAP source planning/contract support on `feat/wrf-rap-source`; keep the next step in `brc-wrf` to RAP Vtable, field-adequacy, case-manifest, and render review. Do not revive GEFS+NAM unless John explicitly asks for that experiment. |

## Reading Packet

Read these in order for a milestone review:

1. `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md` for a pair-programming
   walkthrough.
2. `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` for an AI-led build/WPS/WRF
   progression map.
3. `brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md`
4. `brc-docs/BRC-WRF-FIRST-CASE.md`
5. `brc-cases/README.md`
6. `brc-docs/BRC-WRF-USAGE.md`
7. `brc-docs/BRC-WRF-GATE10-QUICKLOOK-REVIEW.md`
8. `../brc-tools/docs/walkthroughs/wrf-staging.md`
9. `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`
10. `brc-docs/BRC-TOOLS-LINK-HANDOFF.md` if opening a `brc-tools` session
11. `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md` sections 1-3 and Q1
12. `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md` sections 2, 3, and 8

For Michael, start with items 1, 4, 5, 7, and 8 before the full CHPC resource
inventory. For John, start with items 2, 3, 4, 7, 8, 10, and 11; add item 9 when
the next task is in `brc-tools`.

## Maximum Owned-Node WRF Profile

Use this when the goal is a high-powered, non-preemptible single WRF run on the
team-reserved node:

| Slurm setting | Value | Source |
| --- | --- | --- |
| account | `lawson-np` | `brc-knowledge` resource inventory |
| partition | `lawson-np` | `brc-knowledge` resource inventory |
| node | `notch392` | preferred WRF workhorse |
| nodes | `1` | avoids asymmetric two-node WRF costs |
| tasks | `56` | all Slurm cores on `notch392` |
| memory | `900G` | reserves most of the ~996 GiB node |
| launcher | `srun --mpi=pmi2` | validated Intel MPI fix |
| preemptible? | no | owned partition |

Do not move to preemptible Granite or multi-node Notchpeak until the case needs
more than one `notch392` can provide.

## Practical Chain Result

Packet:

```text
/tmp/brc_gate11_jan2013_basin_gefs_20260618T2118Z/
```

Final status check:

```bash
sacct -j 13548706,13548709,13548711,13548714,13548717,13548719,13548747 \
  --format=JobID,JobName%30,State,ExitCode,Elapsed,MaxRSS,NodeList
```

Observed original failed chain:

| Job | Result |
| --- | --- |
| `13548706` prep | `COMPLETED`, `0:0` |
| `13548709` `scaling_t028` | `FAILED`, batch `9:0`; `wrf.exe` step canceled after fatal |
| `13548711`, `13548714`, `13548717`, `13548719`, `13548747` | canceled after the failed dependency |

Failure evidence:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t028/run_20260618T213126Z/debug/
```

Key fact: `real.exe` passed, then `wrf.exe` failed with:

```text
CLWRF: 'CAMtr_volume_mixing_ratio' does not exist
```

The WRF log reports WRF `V4.7.1`. The next SOP must require a checked
John-owned WRF 4.8.0 executable/run source before resubmitting benchmarks.
Live diagnosis on 2026-06-18 found the practical `real.exe` and `wrf.exe`
were symlinks through the base scratch run directory to Michael Davies'
`lawson-group6/u6060939/wrf_build/WRF/main/` binaries, not John's
`~/gits/brc-wrf/main/` binaries. Future practical wrappers now need an
executable byte-match check against John's `paths.wrf_build/main` before model
execution.
Follow-up job `13550021` used John's WRF `V4.8.0` binaries and passed the
executable provenance checks, but still failed because the clean scenario
`WRF_RUN` did not contain WRF runtime physics files from John's `run/`
directory. With `ghg_input=1` by default and RRTMG radiation enabled, WRF needs
`CAMtr_volume_mixing_ratio` in the run directory.
Current wrappers now byte-match required runtime files against John's
`paths.wrf_build/run/`, and generated `prepare_<scenario>.sh` helpers require
`BRC_PREP_APPROVED=YES` before any off-login copy/check.

Successful rerun:

| Job | Result |
| --- | --- |
| `13550104` prep | completed runtime-file fixed `scaling_t028` setup |
| `13550110` `scaling_t028` | completed with John's WRF `V4.8.0`, 28 tasks, `900G`; `wrf.exe` elapsed 2296 s; archive and debug summary exited `0` |

Successful evidence:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/jan2013_basin_gefs/practical_tests/scaling_t028/run_20260618T230858Z/debug/
```
