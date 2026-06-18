# BRC WRF

This is the Bingham Research Center checkout of the Weather Research and
Forecasting model. It is an upstream-style WRF source tree with BRC-local
automation and development practices layered on top.

The extensionless `README` is kept as the upstream WRF version, public-domain,
release-note, and documentation-index file. This `README.md` is the BRC-facing
entry point for human contributors; AI-assisted routing lives in `AGENTS.md`.

## Start Here

- `README`: upstream WRF version, public-domain notice, release notes, and
  documentation index.
- `AGENTS.md`: cold-start routing, safety boundaries, and change expectations
  for AI-assisted work.
- `doc/BRC_FORK_GUIDE.md`: fork mental model, local-vs-upstream boundaries, and
  cheap-before-expensive orientation.
- `doc/BRC_WRF_HANDOFF.md`: slim pointer to the current WRF-run-side control
  board.
- `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`: AI-optimized pointer map for building
  John's fork, pairing it with a John-owned WPS root, and progressing toward a
  repeatable CHPC WRF run.
- `brc-docs/`: concise BRC-facing usage and roadmap notes for CHPC work.
  Start with `brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md` and
  `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` for a print-sized milestone overview.
- `brc-cases/README.md`: BRC case manifest, cheap validator, and render-only
  Slurm checkpoint.
- `doc/README.cmake_build`: CMake build flow using `configure_new`,
  `compile_new`, and `cleanCMake.sh`.
- `doc/README.test_cases`: legacy idealized and real-data test-case overview.
- `.sane/wrf/README.md`: BRC-local automation map for build, run, and
  regression-style work.
- `.ci/tests/build.sh` and `.github/workflows/ci.yml`: CI compilation behavior.

This is a large source tree. Start with narrow local reads before searching WRF
internals broadly.

## Human Resource List

- BRC docs index: `brc-docs/README.md`.
- Current WRF-run-side control board:
  `doc/BRC_WRF_MICROTASK_HANDOFF.md`.
- End-to-end AI handoff:
  `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md`.
- Current first-case runbook: `brc-docs/BRC-WRF-FIRST-CASE.md`.
- CHPC infrastructure truth:
  `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md`.
- CHPC WRF quickstart:
  `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md`.
- `brc-tools` input-staging contract:
  `../brc-tools/docs/WRF-INPUT-STAGING.md`.
- Upstream WRF registration, user guide, citation, and public notice links are
  listed below.

## Build And Test Posture

Both WRF build paths exist here:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct for a task. Inspect the relevant local doc,
workflow, or script before choosing.

Full builds, regression suites, Slurm jobs, and other HPC workflows can be
expensive. Do not run them without explicit approval.

## Near-Term BRC Roadmap

The immediate aim is a real-life proof of concept: install/build this checkout
with WPS, run one Uinta Basin case, preserve enough logs to debug without
guesswork, then grow toward repeatable ensembles.

| Order | Goal | Why It Comes Next | Mini To-Dos |
| --- | --- | --- | --- |
| 1 | Confirm CHPC authority | Prevents cargo-cult modules, paths, and Slurm flags. | Treat `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md` as canonical infrastructure truth; use its delegated WRF quickstart for WRF-specific build/run details. |
| 2 | Prove the install recipe | This is the first proof of concept for the fork, compilers, modules, and WPS pairing. | Use `doc/BRC_WRF_END_TO_END_AI_HANDOFF.md` as the AI routing map. Use the legacy WRF/WPS path first because the CHPC WRF quickstart has validated it; keep CMake as a later comparison. Compile John's `~/gits/brc-wrf` checkout, keep build logs in persistent `lawson-group6` storage outside the repo, and record Git SHA, module list, build path, and executables. |
| 3 | Run one submitted real-data case | Batch precedent beats login-node calamity and leaves pollable evidence. | Render and submit a guarded Slurm job; collect stdout, stderr, `rsl.*`, scheduler metadata, and success markers. |
| 4 | Target the first Basin weather case | A small real case teaches more than a toy run once installation is proven. | Use the validated NAM-only Jan-2013 12/4 km nested Basin proof as the first run record. Keep GEFS+NAM reforecast forcing as the next unproven path. |
| 5 | Make the outputs worth looking at | Build success is not the same as a useful simulation. | Archive namelists, `wrfout*`, WPS/WRF logs, provenance, and quick visual checks against expected snowy-weather behavior. Preserve `brc-tools` input manifests and contracts. |
| 6 | Turn the case into a template | The second run should be boring in the best way. | Start from `brc-cases/`: a case manifest, cheap validator, render-only Slurm path, scratch/archive layout, and stable handoff to `../brc-tools` for staged input. |
| 7 | Run 2+ ensemble members | Monte Carlo workflow pressure-tests paths, storage, logging, and reproducibility. | Use separate run directories per GEFS member; compare logs, timing, outputs, and archive records. |
| 8 | Change nesting only after the baseline is solid | Nesting multiplies failure modes and should not hide install problems. | Treat the validated 12/4 km nest as the current baseline; introduce any new nesting pattern only after WPS, `real.exe`, `wrf.exe`, and archive behavior are routine. |
| 9 | Explore stochastic schemes such as SKEB | This is a science extension, not an install prerequisite. | Record the baseline first; then test stochastic options as explicit experiments with comparable provenance. |

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
