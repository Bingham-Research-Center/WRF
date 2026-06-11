# BRC WRF

This is the Bingham Research Center checkout of the Weather Research and
Forecasting model. It is an upstream-style WRF source tree with BRC-local
automation and development practices layered on top.

The extensionless `README` is kept as the upstream WRF version, public-domain,
release-note, and documentation-index file. This `README.md` is the BRC-facing
entry point for human and AI contributors.

## Start Here

- `README`: upstream WRF version, public-domain notice, release notes, and
  documentation index.
- `AGENTS.md`: cold-start routing, safety boundaries, and change expectations
  for AI-assisted work.
- `doc/BRC_FORK_GUIDE.md`: fork mental model, local-vs-upstream boundaries, and
  cheap-before-expensive orientation.
- `doc/BRC_WRF_HANDOFF.md`: current handoff, cold-start order, and next
  orientation work queue.
- `brc-docs/`: concise BRC-facing usage and roadmap notes for CHPC work.
- `doc/README.cmake_build`: CMake build flow using `configure_new`,
  `compile_new`, and `cleanCMake.sh`.
- `doc/README.test_cases`: legacy idealized and real-data test-case overview.
- `.sane/wrf/README.md`: BRC-local automation map for build, run, and
  regression-style work.
- `.ci/tests/build.sh` and `.github/workflows/ci.yml`: CI compilation behavior.

This is a large source tree. Start with narrow local reads before searching WRF
internals broadly.

## Build And Test Posture

Both WRF build paths exist here:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct for a task. Inspect the relevant local doc,
workflow, or script before choosing.

Full builds, regression suites, Slurm jobs, and other HPC workflows can be
expensive. Do not run them without explicit approval.

## Change Style

Keep edits lean, scoped, and scientifically motivated. Prefer small logical
batches with clear commit bodies that preserve the reasoning, evidence, and
operational impact behind the change.

When AI materially assists a change, include an appropriate `Co-authored-by:`
trailer.

## Current Gaps

- BRC-supported build paths still need a host/compiler/use-case matrix.
- BRC CHPC usage and on-rails workflow gaps are tracked in `brc-docs/`.
- Local WRF deviations from upstream should be captured as they are confirmed.
- Cheap smoke tests should be documented before any full regression workflow is
  treated as routine.

## Upstream WRF Resources

New WRF users are requested to register:
[WRF registration](https://www2.mmm.ucar.edu/wrf/users/download/wrf-regist.php).

For downloads, user support, documentation, publications, and additional
resources, see the
[WRF Model Users' Web Site](https://www2.mmm.ucar.edu/wrf/users/).

WRF citation information, including DOI guidance, is available at
[citing WRF](https://www2.mmm.ucar.edu/wrf/users/citing_wrf.html).

WRF is public-domain open-source code. The name "WRF" is a registered trademark
of the University Corporation for Atmospheric Research. Public-domain notice and
related information are available at
[WRF public notice](https://www2.mmm.ucar.edu/wrf/users/public.html).
