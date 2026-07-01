# BRC WRF Handoff

This file is intentionally slim; the active WRF-run-side control board is
`doc/BRC_WRF_MICROTASK_HANDOFF.md`.

For any cold-start session, read `AGENTS.md` first, then
`doc/BRC_WRF_MICROTASK_HANDOFF.md`. That pair is the current AI routing stack.

The current stated next goal is to inspect the completed Pelican NAM/GFS
quicklook pair and summarize forcing sensitivity. After the control board, read
`brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md` and
`brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md`.

For the end-to-end AI route toward compiling John's fork, pairing it with a
John-owned WPS root, and proving a repeatable CHPC run, read
`doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`.

For the full gate-by-gate roadmap to compiled WRF, John-owned WPS, a NAM-only
rerun, archive, quicklooks, and practical-test readiness, read
`brc-docs/BRC-WRF-ROADMAP.md`.

For current proof state and the human-facing overview, read
`brc-docs/BRC-WRF-STATE-PLAYBOOK.md`, `brc-docs/BRC-WRF-FIRST-CASE.md`, and
`brc-cases/README.md`.

For Pelican conveyor, comparison quicklooks, or domain-review work, read
`brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md`,
`brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md`, and, only for parked RAP-only details,
`brc-docs/BRC-WRF-PELICAN-RAP-FEASIBILITY.md`.

For `brc-tools` staging context, read
`../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md` and
`../brc-tools/docs/WRF-INPUT-STAGING.md`; force
`conda run -n brc-tools-2026 ...` for sibling Python/Herbie commands, and do
not run DTN staging, WPS,
`real.exe`, `wrf.exe`, Slurm, scaling sweeps, or large downloads without
explicit approval.
