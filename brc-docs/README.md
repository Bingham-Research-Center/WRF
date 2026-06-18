# BRC Docs

This directory holds short BRC-facing guidance for this WRF fork. Keep these
files concise and route deeper operational records to `doc/`, `brc-cases/`,
`.sane/wrf/`, or the adjacent `../brc-knowledge` checkout.

## Files

- `BRC-WRF-FORK-HIGHLIGHTS.md`: terse milestone/highlight reel for the BRC
  fork layer since it diverged from upstream WRF 4.8.0.
- `BRC-WRF-STATE-PLAYBOOK.md`: printable plain-language state of play, next
  steps, practical-chain result, reading packet, and maximum owned-node Slurm profile. This is the
  WRF-side companion to `../brc-tools/docs/walkthroughs/wrf-staging.md`.
- `BRC-WRF-PLAN-MODE-RUN-HANDOFF.md`: comprehensive Plan Mode handoff and
  walkthrough for low-hanging no-run work, manual quicklook/data inspection,
  directory checks, and a gated from-scratch NAM-only run.
- `BRC-WRF-MICHAEL-PRACTICAL-PACKET.md`: short John/Michael pair-programming
  handout with no-run walkthrough commands, editable settings, approval gates,
  and blank result tables.
- `../doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`: AI-facing pointer map for the
  end-to-end build/WPS/WRF goal, using Michael's proven path as a yardstick but
  keeping John's fork/build ownership separate.
- `TOP-100-START-HERE-JUNE.md`: terse 100-item microtask menu for practical
  WRF tests, science checks, and code/provenance auditing.
- `BRC-TOOLS-LINK-HANDOFF.md`: current handoff to `../brc-tools` for tightening
  the WRF input-staging contract and stale-proof edge cases.
- `BRC-WRF-USAGE.md`: current CHPC usage posture for this fork: storage,
  login-node boundaries, build/install stance, and WRF run shape.
- `BRC-WRF-FIRST-CASE.md`: current start-to-finish Jan-2013 Basin proof path
  connecting `brc-tools` staged inputs to WPS, `real.exe`, `wrf.exe`, and
  archive checks.
- `BRC-WRF-ROADMAP.md`: on-rails WRF workflow plan, dollar-sign skill ideas,
  current practical-testing status, and follow-on science/scaling gates.
- `../brc-cases/README.md`: BRC case manifest, cheap validator, and render-only
  Slurm checkpoint.
- `handouts/`: rendered PDF copies for live review. Treat these as derivatives
  of the Markdown sources above.

## Style

- Prefer confirmed local facts over copied upstream WRF documentation.
- Keep high-level docs small enough for a cold-start agent to read cheaply.
- Keep beginner walkthroughs split by execution context: login-safe metadata
  checks, approved off-login artifact reads, and approved WRF execution.
- Move run records, large inventories, and time-stamped operational evidence to
  `../brc-knowledge` unless they must live with this fork.
