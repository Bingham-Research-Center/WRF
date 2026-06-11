# BRC Docs

This directory holds short BRC-facing guidance for this WRF fork. Keep these
files concise and route deeper operational records to `doc/`, `.sane/wrf/`, or
the adjacent `../brc-knowledge` checkout.

## Files

- `BRC-WRF-USAGE.md`: current CHPC usage posture for this fork: storage,
  login-node boundaries, build/install stance, and WRF run shape.
- `BRC-WRF-ROADMAP.md`: on-rails WRF workflow plan, dollar-sign skill ideas,
  and survey gaps before a supported BRC CHPC install.

## Style

- Prefer confirmed local facts over copied upstream WRF documentation.
- Keep high-level docs small enough for a cold-start agent to read cheaply.
- Move run records, large inventories, and time-stamped operational evidence to
  `../brc-knowledge` unless they must live with this fork.
