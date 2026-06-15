# BRC Docs

This directory holds short BRC-facing guidance for this WRF fork. Keep these
files concise and route deeper operational records to `doc/`, `brc-cases/`,
`.sane/wrf/`, or the adjacent `../brc-knowledge` checkout.

## Files

- `BRC-WRF-FORK-HIGHLIGHTS.md`: terse milestone/highlight reel for the BRC
  fork layer since it diverged from upstream WRF 4.8.0.
- `BRC-WRF-STATE-PLAYBOOK.md`: printable plain-language state of play, next
  steps, reading packet, and maximum owned-node Slurm profile.
- `BRC-TOOLS-LINK-HANDOFF.md`: current handoff to `../brc-tools` for tightening
  the WRF input-staging contract and stale-proof edge cases.
- `BRC-WRF-USAGE.md`: current CHPC usage posture for this fork: storage,
  login-node boundaries, build/install stance, and WRF run shape.
- `BRC-WRF-FIRST-CASE.md`: current start-to-finish Jan-2013 Basin proof path
  connecting `brc-tools` staged inputs to WPS, `real.exe`, `wrf.exe`, and
  archive checks.
- `BRC-WRF-ROADMAP.md`: on-rails WRF workflow plan, dollar-sign skill ideas,
  and survey gaps before a supported BRC CHPC install.
- `../brc-cases/README.md`: BRC case manifest, cheap validator, and render-only
  Slurm checkpoint.

## Style

- Prefer confirmed local facts over copied upstream WRF documentation.
- Keep high-level docs small enough for a cold-start agent to read cheaply.
- Move run records, large inventories, and time-stamped operational evidence to
  `../brc-knowledge` unless they must live with this fork.
