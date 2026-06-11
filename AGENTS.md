# Repository Context

This is the Bingham Research Center checkout of WRF:

- Remote: `https://github.com/Bingham-Research-Center/WRF.git`
- Current observed branch: `john/wrf`
- Current observed baseline: WRF Model Version `4.8.0`

This is a large upstream-style WRF source tree. Keep first-pass context gathering
small and local before broad scans or expensive commands.

## First Places To Read

- `README`: version, public-domain notice, and index of WRF documentation files.
- `README.md`: upstream WRF user, registration, citation, and public-notice links.
- `doc/README.cmake_build`: CMake-oriented build flow using `configure_new`,
  `compile_new`, and `cleanCMake.sh`.
- `doc/README.test_cases`: legacy test-case overview and idealized/real case
  orientation.
- `.sane/wrf/`: local WRF automation for builds, runs, and regression-style work.
- `.ci/tests/build.sh` and `.github/workflows/ci.yml`: CI build-test behavior.

## Build And Test Caution

Both build paths exist:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct for a task. Inspect the relevant docs,
workflow, or script before choosing.

Do not run full builds, regression tests, Slurm jobs, or other HPC workflows
without explicit user approval. WRF builds and tests can be expensive.

## Orientation Style

- Prefer `rg`, `rg --files`, and shallow `find` commands for initial bearings.
- Avoid broad recursive scans unless a narrow search fails.
- Use local documentation and code-linked references before online lookup.
- Do not browse online WRF documentation unless the user explicitly asks for it.
- Treat this file as an initial context entry; extend it gradually as local
  conventions and BRC-specific workflows are confirmed.

## Change SOP

- Commit changes in logical, scientifically driven batches.
- Keep commit subjects low-verbosity and specific.
- Use detailed commit bodies that preserve the reasoning, evidence, and
  scientific or operational impact behind each batch.
- Treat human and AI contributors as coauthors when AI materially assisted the
  change; include an appropriate `Co-authored-by:` trailer.
