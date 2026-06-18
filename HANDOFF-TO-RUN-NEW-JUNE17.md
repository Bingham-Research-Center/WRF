# Handoff To Run New June 17

This scratch handoff has been collapsed into the canonical docs below so the
repo stays lean. Do not expand it into a parallel run plan again.

## Use These Instead

1. `AGENTS.md` for the short repo router and hard boundaries.
2. `doc/BRC_WRF_MICROTASK_HANDOFF.md` for the detailed queue and approval gates.
3. `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md` for the John/Michael no-run
   checklist and settings tables.
4. `brc-docs/BRC-WRF-FIRST-CASE.md` for the current NAM-only proof path.
5. `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md` for the latest reverse handoff from
   `brc-tools`.

## Hard Boundaries

- No practical tests on a login node.
- Keep quicklooks in the durable archive, not the repo checkout.
- Stop before DTN staging, WPS, `real.exe`, `wrf.exe`, or benchmark sweeps
  unless a human explicitly approves them.
