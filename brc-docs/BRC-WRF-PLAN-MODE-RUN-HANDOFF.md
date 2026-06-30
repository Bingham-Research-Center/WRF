# BRC WRF Plan Mode Pointer

Status: legacy pointer. This file is no longer the active handoff or task
board.

Use it only when John explicitly asks for a Plan Mode planning session rather
than direct implementation. Otherwise start from:

1. `AGENTS.md`
2. `doc/BRC_WRF_MICROTASK_HANDOFF.md`
3. `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
4. `brc-cases/README.md`

## Prompt

```text
cwd=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf

Work in Plan Mode first. Verify live git/host/date state, then read AGENTS.md
and doc/BRC_WRF_MICROTASK_HANDOFF.md. Choose exactly one lane and stop at its
approval boundary.

Lanes:
A. login-safe docs/tests/render-only cleanup;
B. manual science review of existing quicklooks and evidence;
C. render/check the Gate 11 practical-test packet;
D. no-run Pelican alternate-forcing consumer review;
E. from-scratch NAM-only rerun packet preparation;
F. parked GEFS+NAM two-stream design only if John explicitly revives it.

Do not run DTN staging, WPS, real.exe, wrf.exe, sbatch, strict artifact reads,
NetCDF/archive reads, quicklooks, scaling, or memory benchmarks without explicit
approval for the exact command and stop point.
```

## Current Routing

- Active task board: `doc/BRC_WRF_MICROTASK_HANDOFF.md`
- End-to-end WRF/WPS route: `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`
- Case tooling: `brc-cases/README.md`
- Pelican conveyor: `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md`
- Pelican alternate forcing: `brc-docs/BRC-WRF-PELICAN-ALTERNATE-FORCING.md`

## Closeout Shape

End with branch/SHA, dirty state, commands run, host/context, evidence paths,
what was not run, owner repo, result, and one next approval or no-run action.
