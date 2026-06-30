# BRC WRF Roadmap

Status: compact gate index. The active queue and approval state live in
`doc/BRC_WRF_MICROTASK_HANDOFF.md`.

This is not approval to compile, stage inputs, run WPS, run `real.exe` or
`wrf.exe`, submit Slurm jobs, inspect large artifacts, render quicklooks, or
run scaling/memory tests.

## Current State

Gates 0-11 passed on 2026-06-18 for the John-owned NAM-only baseline:
build/run contract, WRF compile proof, John-owned WPS proof, case manifest
alignment, fresh input contract, WPS, `real.exe`, `wrf.exe`, archive,
quicklooks, and maintained practical-test harness.

Practical testing has one approved passing row: `scaling_t028` job `13550110`.
Later `scaling_t016` attempts failed before WRF runtime evidence and are not
benchmark results.

Current alternate-forcing work is one source at a time through `brc-tools`
contracts, starting with RAP analysis for the Pelican 3/1/0.333 km baseline.
GEFS+NAM two-stream forcing is parked unless John explicitly revives it.

## Gate Index

| Gate | Name | Status | Canonical detail |
| ---: | --- | --- | --- |
| 0 | Live state freeze | Passed | `doc/BRC_WRF_MICROTASK_HANDOFF.md` |
| 1 | Build/run contract | Passed | `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` |
| 2 | John-owned WRF compile proof | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 3 | John-owned WPS proof | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 4 | Case manifest root alignment | Passed | `brc-cases/README.md` |
| 5 | Fresh NAM-only input contract | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 6 | NAM-only WPS proof | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 7 | NAM-only `real.exe` proof | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 8 | NAM-only `wrf.exe` proof | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 9 | Archive proof | Passed | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| 10 | Quicklook proof | Passed | `brc-cases/README.md` |
| 11 | Practical-test harness | Passed | `brc-cases/README.md` |

## Follow-On Lanes

| Lane | Default status | Stop point |
| --- | --- | --- |
| Pelican RAP alternate forcing | Active no-run review | Vtable candidate, field checklist, case manifest draft, rendered scripts, approval text. |
| Additional scaling row | Approval-gated | Render/check packet only until one row is explicitly approved. |
| Memory right-sizing | Approval-gated | Candidate table only until one row is explicitly approved. |
| GEFS+NAM two-stream | Parked legacy | Do not pursue unless John explicitly revives it. |
| Storage promotion | Human decision | No blind copy from scratch; prepare inventory/decision notes only. |

## Standing Rules

- Compile and run only John-owned WRF/WPS roots for production proof.
- Use Michael-owned paths only as comparison evidence.
- Keep NWP acquisition and staging contracts in `../brc-tools`.
- Keep CHPC scheduler/storage/module truth in `../brc-knowledge`.
- Put generated runs, namelists, logs, NetCDF, PNGs, inventories, and one-off
  Slurm scripts outside this repo.
- End each gate with command, host/context, owner repo, evidence path, result,
  what was not run, and next stop point.

## New-Session Prompt

```text
cwd=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf

Read AGENTS.md, then doc/BRC_WRF_MICROTASK_HANDOFF.md. Use this roadmap only as
a compact gate index. Gates 0-11 are passed unless live docs contradict that.

Pick exactly one follow-on lane. Do not run compile, staging, WPS, real.exe,
wrf.exe, sbatch, strict artifact reads, NetCDF/archive checks, quicklooks,
scaling, or memory tests without explicit approval for the exact command and
stop point.
```
