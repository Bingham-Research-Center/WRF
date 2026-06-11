# Repository Context

This is the Bingham Research Center checkout of WRF:

- Remote: `https://github.com/Bingham-Research-Center/WRF.git`
- Current observed branch: `john/wrf`
- Current observed baseline: WRF Model Version `4.8.0`

This is a large upstream-style WRF source tree. Keep first-pass context gathering
small and local before broad scans or expensive commands.

## README Roles

- `README`: preserve as the upstream-style WRF version, public-domain notice,
  release-note, and documentation-index file.
- `README.md`: BRC-facing landing page for humans and AI agents. It may point to
  upstream WRF resources, but should stay short and route readers to deeper
  local docs instead of becoming a full operating manual.

## First Places To Read

- `README`: version, public-domain notice, and index of WRF documentation files.
- `README.md`: BRC landing page, repository roles, local workflow pointers, and
  upstream WRF user, registration, citation, and public-notice links.
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

## Cheap First Commands

Use these read-only commands for an initial orientation when relevant:

- `git status --short`
- `sed -n '1,120p' README.md`
- `sed -n '1,80p' README`
- `sed -n '1,160p' doc/README.cmake_build`
- `find .sane/wrf -maxdepth 2 -type f | sort`
- `sed -n '1,160p' .ci/tests/build.sh`

If a task concerns tests, read `doc/README.test_cases`; note that this checkout
uses the dotted filename even though some upstream-oriented references may use a
different spelling.

## Orientation Style

- Prefer `rg`, `rg --files`, and shallow `find` commands for initial bearings.
- Avoid broad recursive scans unless a narrow search fails.
- Use local documentation and code-linked references before online lookup.
- Do not browse online WRF documentation unless the user explicitly asks for it.
- Do not start in large source subtrees such as `dyn_*`, `phys`, `chem`, or
  `external` unless the user request or a local document points there.
- Treat `.sane/wrf/` as BRC-local automation until proven otherwise; inspect the
  relevant script before assuming whether it uses legacy, CMake, CI, or HPC
  behavior.
- Treat this file as an initial context entry; extend it gradually as local
  conventions and BRC-specific workflows are confirmed.

## Cheap Validation

- Syntax and metadata checks are preferred before any compile-scale work.
- For shell changes, use `bash -n <script>` when appropriate.
- For Python changes, use `python -m py_compile <file>` or focused tests if they
  exist.
- For workflow or HPC changes, inspect the command path and dry-run behavior
  first; require explicit approval before real submission, full regression, or
  expensive build work.

## Change SOP

- Commit changes in logical, scientifically driven batches.
- Keep commit subjects low-verbosity and specific.
- Use detailed commit bodies that preserve the reasoning, evidence, and
  scientific or operational impact behind each batch.
- Treat human and AI contributors as coauthors when AI materially assisted the
  change; include an appropriate `Co-authored-by:` trailer.
