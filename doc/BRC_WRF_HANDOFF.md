# BRC WRF Handoff

This handoff is for a fresh human or Codex session continuing the work of making
the BRC WRF fork less opaque without loading the full WRF source tree.

## Current State

- Repo: `/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf`
- Branch: `john/wrf`
- Remote: `https://github.com/Bingham-Research-Center/WRF.git`
- Baseline observed in `README`: WRF Model Version `4.8.0`
- Latest orientation commits:
  - `170ef2e0` `Document fork orientation`
  - `f52b0c4b` `Document SANE boundaries`
  - `f5ee2fc0` `Document WRF proof priorities`

The expected starting state after this handoff is a clean branch tracking
`origin/john/wrf`.

## Goal

Build a thin, reliable orientation layer around a large upstream-style WRF tree.
The goal is not to rewrite WRF documentation or infer BRC policy from guesses.
Document only confirmed local behavior, keep routing files lean, and move detail
into focused docs near the workflow they describe.

## Cold Start Order

Start with these local reads before broad scans:

1. `git status --short --branch --untracked-files=all`
2. `sed -n '1,120p' README.md`
3. `sed -n '1,170p' AGENTS.md`
4. `sed -n '1,120p' doc/BRC_FORK_GUIDE.md`
5. `sed -n '1,180p' .sane/wrf/README.md`

Then narrow by task:

- case manifest or render-only Slurm: `brc-cases/README.md`, then the relevant
  `*.case.yaml` and `brc-cases/wrf_case.py`
- CMake build path: `doc/README.cmake_build`
- test-case orientation: `doc/README.test_cases`
- CI compile behavior: `.ci/tests/build.sh` and `.github/workflows/ci.yml`
- local automation: the specific `.sane/wrf` script, host config, or SANE test
  definition
- model source: narrow `rg` first, then the relevant WRF subtree

## Do Not Run Without Approval

Do not run full builds, WRF cases, SANE actions, regression tests, Slurm/PBS
jobs, or other HPC workflows without explicit approval. Commands that can clean,
compile, remove outputs, stage run directories, launch WRF, compare model files,
or consume allocation time are not cold-start probes.

Cheap inspection remains appropriate: `sed`, `rg`, `git diff --check`,
`bash -n <script>`, and `python -m py_compile <file>`.

## Next Work Items

0. Current Jan-2013 proof path
   - Read `brc-docs/BRC-WRF-FIRST-CASE.md` before making new run claims.
   - NAM-only staging from `../brc-tools` has been validated through WPS,
     `real.exe`, `wrf.exe`, and archive checks for a known 12/4 km nested Basin
     case.
   - GEFS+NAM two-stream forcing remains open; do not describe it as proven.
   - The referenced CHPC run script now uses `rsync -av ./wrfout_d0*` so WRF
     colon filenames are archived as local paths.
   - `brc-cases/` now provides the initial review gate for this case:
     `python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml`
     and `python brc-cases/wrf_case.py render-slurm brc-cases/jan2013_basin_nam.case.yaml`.
     Non-strict validation warns that the old proof scratch lacks the newer
     `contract_<case>.json` sidecar; strict validation correctly fails until a
     fresh contract exists.

1. Cheap smoke-test doctrine
   - Suggested file: `doc/BRC_CHEAP_VALIDATION.md`
   - Define what can be validated without building WRF: markdown readback,
     `git diff --check`, shell syntax checks, Python compile checks, CI/workflow
     dry inspection, config-path sanity, and explicit stop points.
   - Keep it practical and command-oriented. Do not invent a full test harness
     until real cheap checks are confirmed.

2. Local-deviation log
   - Suggested file: `doc/BRC_LOCAL_CHANGES.md`
   - Record only confirmed deviations from upstream WRF source or workflow.
   - Each entry should include evidence: file path, commit or diff context when
     available, why it matters scientifically or operationally, and open
     questions.
   - If no source deviations are confirmed yet, start with that statement.

3. Build/install meanings
   - Suggested file: `doc/BRC_BUILD_INSTALL_NOTES.md`
   - Separate meanings of "build" and "install": legacy build tree, CMake
     install tree, copied build directory, test-case run directory, SANE staging
     directory, and HPC output location.
   - Ground this in `doc/README.cmake_build`, `.ci/tests/build.sh`,
     `.sane/wrf/scripts/buildCMake.sh`, and `.sane/wrf/scripts/buildMake.sh`.

4. Future handoff refresh
   - Update this file after each orientation batch that changes the cold-start
     path, latest commits, or recommended next work.
   - Do not use this file as a dumping ground for all WRF knowledge. Move stable
     doctrine into the focused docs above.

## Commit And Push Protocol

- Keep each batch logical and reviewable.
- Use a terse subject and a detailed body with why, evidence checked, and
  scientific or operational impact.
- Include both trailers when AI materially assists:
  - `Co-authored-by: John Lawson <john.lawson@usu.edu>`
  - `Co-authored-by: Codex <codex@openai.com>`
- Push `john/wrf` after each completed batch when asked to implement.

## Acceptance Criteria

- The repo stays clean after each pushed batch.
- `AGENTS.md` remains a short router, not a manual.
- `README.md` remains a landing page, not an operations guide.
- New docs are evidence-backed and point to local files rather than online WRF
  docs unless the user explicitly asks for web lookup.
- Validation is recorded in commit messages, including the fact that no
  build/run/regression/HPC command was used.
