# BRC WRF

This is the Bingham Research Center checkout of WRF 4.8.0 with BRC-local
case tooling, CHPC run practices, and AI routing layered on top.

The extensionless `README` is the upstream WRF notice/release/documentation
file. This `README.md` is the local BRC entry point. Keep it terse and route
details to the owning docs.

## Start Here

Read in this order for a cold start:

1. `AGENTS.md` - repo ownership, safety boundaries, current durable truth.
2. `doc/BRC_WRF_MICROTASK_HANDOFF.md` - active queue, approvals, and evidence.
3. `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` - compact human-facing state summary.
4. `brc-cases/README.md` - case manifests, validators, Slurm renderers,
   practical harness, and WRF-output quicklook adapter.
5. `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` - build/WPS/WRF progression route.
6. `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md` - staged WRF conveyor, archive, and
   quicklook placement rules.
7. `brc-docs/BRC-WRF-PELICAN-ALTERNATE-FORCING.md` - Pelican alternate
   forcing prompt, RAP feasibility, and approval boundary.
8. `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md` - input-staging handoff when the
   task touches manifests, contracts, or forcing.
9. `../brc-knowledge/scholarium/reference-base/resources/` - CHPC node,
   storage, scheduler, proxy, and validated Slurm truth.

For a print-sized milestone overview, use
`brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md` and
`brc-docs/BRC-WRF-STATE-PLAYBOOK.md`.

## Current Posture

Validated baseline: NAM-only Jan-2013 Uinta Basin, 12/4 km nested, WPS
`Vtable.NAM`, `interval_seconds = 21600`.

Roadmap Gates 5-11 passed on 2026-06-18 for the John-owned NAM-only proof:
fresh contract, WPS, `real.exe`, `wrf.exe`, archive, quicklooks, and the
maintained practical-test harness. The first approved practical row,
`scaling_t028` job `13550110`, passed. Later `scaling_t016` attempts failed
before WRF runtime evidence and are not benchmark results.

Current Pelican baseline: NAM 3/1/0.333 km, 75 levels, six-hour run
`pelican2013_nam_3_1_333m_75lev`, full job `13695261`, archived under
`lawson-group6/jrlawson/wrf_archive/`. New forcing experiments should hot-swap
one source at a time through `brc-tools` staging contracts, starting with RAP
analysis. The older GEFS+NAM two-stream idea is parked unless explicitly
revived.

## To-Dos And Wishlists

Current work is intentionally split by ownership:

- Active queue, next default task, remaining approvals, and parked work:
  `doc/BRC_WRF_MICROTASK_HANDOFF.md`.
- Compact gate/follow-on index: `brc-docs/BRC-WRF-ROADMAP.md`.
- Human-readable next moves: `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`.
- Case-helper and practical-harness work: `brc-cases/README.md`.
- Input-staging wishlists and source support: `../brc-tools/docs/`.

Do not revive deleted June to-do, handoff, or chat-style files. Update the
canonical owner above and leave only short pointers elsewhere.

## Boundaries

- `brc-wrf`: WRF source, WPS/WRF-side docs, case manifests, validators, run
  templates, maintained wrappers, and WRF-output quicklook adaptation.
- `brc-tools`: input staging, manifests, contracts, token checks, NWP download
  logic, and reusable plotting helpers.
- `brc-knowledge`: canonical CHPC infrastructure facts and validated Slurm
  guidance.

Do not add downloader/staging logic to `brc-wrf`. Do not put WRF/WPS execution
wrappers in `brc-tools`. Do not point John's wrappers at Michael-owned WRF/WPS
roots.

## Build And Run

Both WRF build paths exist:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct for a task. Read the relevant local doc or
script first. Full builds, WPS, `real.exe`, `wrf.exe`, Slurm jobs, large
downloads, strict artifact reads, NetCDF-heavy checks, archive inventories, and
quicklooks need explicit approval and the correct off-login context.

## Change Style

Keep edits lean, scoped, and scientifically motivated. Update the canonical doc
that owns the fact, then leave short pointers elsewhere. Stage only relevant
files, leave sibling-repo dirt alone, and preserve command/evidence/stop-point
details in commit bodies when workflow truth changes.

When AI materially assists a change, include:

```text
Co-authored-by: John Lawson <john.lawson@usu.edu>
Co-authored-by: Codex <codex@openai.com>
```

## Upstream WRF Resources

WRF registration, documentation, support, citation, and public notice links are
listed in the upstream `README`.
