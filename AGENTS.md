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
- `brc-docs/README.md`: concise BRC-facing docs index for CHPC usage and
  roadmap notes.
- `brc-docs/BRC-WRF-USAGE.md`: CHPC usage posture, storage layout, login-node
  boundary, and standard WRF run shape.
- `brc-docs/BRC-WRF-ROADMAP.md`: on-rails WRF workflow plan, skill ideas, and
  install gaps.
- `doc/BRC_FORK_GUIDE.md`: fork mental model, local-vs-upstream boundaries, and
  cheap-before-expensive orientation.
- `doc/README.cmake_build`: CMake-oriented build flow using `configure_new`,
  `compile_new`, and `cleanCMake.sh`.
- `doc/README.test_cases`: legacy test-case overview and idealized/real case
  orientation.
- `.sane/wrf/README.md`: map of local WRF automation, cheap validation, and
  expensive run boundaries.
- `.ci/tests/build.sh` and `.github/workflows/ci.yml`: CI build-test behavior.

## Task Routing

- Repo or fork-orientation task: start with `README.md`, `AGENTS.md`, and
  `doc/BRC_FORK_GUIDE.md`.
- Pending orientation backlog or handoff task: read `doc/BRC_WRF_HANDOFF.md`.
- Focused docs task: start with `README.md`, `AGENTS.md`, and the relevant
  `doc/README*` file.
- BRC CHPC usage or on-rails workflow task: start with `brc-docs/README.md`,
  then read either `brc-docs/BRC-WRF-USAGE.md` or
  `brc-docs/BRC-WRF-ROADMAP.md`.
- Local automation task: read `.sane/wrf/README.md`, then inspect the specific
  script, host config, or SANE test definition.
- CI task: inspect `.ci/tests/build.sh`, `.github/workflows/ci.yml`, and only
  then the called helper or workflow.
- Test-case task: read `doc/README.test_cases`, then narrow to the relevant
  `test/` case directory.
- Model-code task: use narrow `rg` searches before opening large source
  subtrees such as `dyn_*`, `phys`, `chem`, or `external`.

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
- `sed -n '1,140p' .sane/wrf/README.md`
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
- Write commit messages for future technical review: terse subject, detailed
  body with why the change was made, what evidence was checked, and any
  scientific or operational impact.
- When AI materially assists a change, include both coauthor trailers:
  `Co-authored-by: John Lawson <john.lawson@usu.edu>` and
  `Co-authored-by: Codex <codex@openai.com>`.
