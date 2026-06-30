# BRC Docs

This directory holds short BRC-facing guidance for this WRF fork. Keep these
files concise and route deeper operational records to `doc/`, `brc-cases/`,
`.sane/wrf/`, or the adjacent `../brc-knowledge` checkout.

## Files

- `BRC-WRF-FORK-HIGHLIGHTS.md`: terse milestone/highlight reel for the BRC
  fork layer since it diverged from upstream WRF 4.8.0.
- `BRC-WRF-STATE-PLAYBOOK.md`: printable plain-language state of play, next
  steps, practical-chain result, reading packet, and maximum owned-node Slurm
  profile. This is the WRF-side companion to
  `../brc-tools/docs/walkthroughs/wrf-staging.md`.
- `BRC-WRF-MULTISCALE-ROADMAP.md`: terse task-size and time-horizon map for
  the Pelican hot-swap lane, from RAP field proof through source campaign.
- `BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md`: current paste-ready handoff for
  parallel `brc-wrf`/`brc-tools` work to find one additional working NWP source
  after RAP-only and ERA5 were blocked.
- `BRC-WRF-PLAN-MODE-RUN-HANDOFF.md`: short legacy Plan Mode pointer. Use only
  when John explicitly asks for planning before implementation.
- `BRC-WRF-DOMAIN-PREVIEW-SOP.md`: geogrid-only domain-preview workflow,
  storage rules, and review-packet expectations.
- `BRC-WRF-RUN-CONVEYOR-SOP.md`: staged WRF conveyor rules for shared control
  files, Slurm logs, CFL gates, archives, and quicklooks.
- `BRC-WRF-PELICAN-ALTERNATE-FORCING.md`: historical Pelican alternate-forcing
  background, RAP feasibility memo, and RAP WPS proof evidence. Use
  `BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md` for the active prompt.
- `BRC-WRF-PELICAN-RAP-FEASIBILITY.md`: RAP staged-contract consumption memo,
  selected WPS Vtable candidate, field-adequacy checklist, and WPS-only stop
  point.
- `BRC-WRF-MICHAEL-PRACTICAL-PACKET.md`: short John/Michael pair-programming
  handout with no-run walkthrough commands, editable settings, approval gates,
  and blank result tables.
- `../doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`: AI-facing pointer map for the
  end-to-end build/WPS/WRF goal, using Michael's proven path as a yardstick but
  keeping John's fork/build ownership separate.
- `BRC-WRF-USAGE.md`: current CHPC usage posture for this fork: storage,
  login-node boundaries, build/install stance, and WRF run shape.
- `BRC-WRF-FIRST-CASE.md`: current start-to-finish Jan-2013 Basin proof path
  connecting `brc-tools` staged inputs to WPS, `real.exe`, `wrf.exe`, and
  archive checks.
- `BRC-WRF-ROADMAP.md`: compact gate index. The active queue and approval
  state live in `../doc/BRC_WRF_MICROTASK_HANDOFF.md`.
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
