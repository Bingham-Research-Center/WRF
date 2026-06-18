# BRC WRF State Playbook

Short print-oriented explanation for John/JRL and Michael. It describes where
the current `brc-wrf` fork fits, what is proven, and what should happen next.

## One-Sentence State

We have a BRC-local review layer around WRF 4.8.0, and one NAM-only Jan-2013
Basin case is proven through `brc-tools` input staging, WPS, `real.exe`,
`wrf.exe`, archive checks, no-run quicklooks, and a maintained render-only
practical-test harness; the first practical scaling row exposed a WRF executable
or run-directory mismatch that must be fixed before more benchmarks.

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

## Who Can Understand This Today?

| Audience | Current readiness | What still feels hard |
| --- | --- | --- |
| John/JRL | High enough to audit and steer science decisions. | The GEFS+NAM two-stream path still needs WPS/`real.exe` proof before it is science-ready. |
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
| Visual QA | Usable off-login. `brc-cases/wrf_quicklook.py` checks/renders five PNGs from existing proof artifacts; path-only unit tests are login-safe. |
| Practical-test harness | Usable. `wrf_case.py render-practical-harness` writes review packets outside the repo with scaling/memory scripts and blank result tables. |
| Practical testing | Started but blocked. Prep `13548706` completed, `scaling_t028` `13548709` failed in `wrf.exe`, and downstream jobs were canceled. The failed log reports WRF `V4.7.1`; diagnose source-run/executable mismatch before resubmitting. |
| Slurm profile | Aligned to max owned-node profile: `lawson-np`, `notch392`, 1 node, 56 tasks, `900G`, `srun --mpi=pmi2`. |
| GEFS+NAM | Not proven. Treat as a design/proof task, not a working production method. |

## Where We Should Go Next

| Order | Next move | Stop point |
| --- | --- | --- |
| 1 | Diagnose the failed `scaling_t028` practical row. | Prove which `real.exe`/`wrf.exe`, `namelist.input`, and `met_em` source was used before resubmitting. |
| 2 | Patch the practical-test SOP/result record after diagnosis. | Make the approved preparation source explicit; do not rely on `/scratch/.../wrf_run` by memory. |
| 3 | Walk through Gate 10 quicklook PNGs with meteorological eyes. | Decide whether the NAM-only proof remains a physically useful baseline. |
| 4 | Decide whether GEFS+NAM is still needed for the next science question. | If yes, draft the two-stream WPS proof; if no, keep improving NAM-only repeatability. |

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
7. `../brc-tools/docs/walkthroughs/wrf-staging.md`
8. `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`
9. `brc-docs/BRC-TOOLS-LINK-HANDOFF.md` if opening a `brc-tools` session
10. `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md` sections 1-3 and Q1
11. `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md` sections 2, 3, and 8

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

Observed:

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
