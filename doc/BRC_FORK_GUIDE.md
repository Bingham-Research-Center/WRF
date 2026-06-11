# BRC WRF Fork Guide

This guide is a fork-orientation layer for this BRC WRF checkout. It is not a
replacement for upstream WRF docs or local workflow scripts.

## Mental Model

This repository is still mostly an upstream-style WRF source tree. Large
directories such as `dyn_*`, `phys`, `chem`, `external`, `frame`, `share`, and
`test` should be approached as WRF model source unless local evidence says
otherwise.

BRC-local work is layered around that source tree:

- repo-facing docs such as `README.md`, `AGENTS.md`, and selected `doc/` files;
- local automation and host-specific workflow code under `.sane/wrf/`;
- CI and workflow glue under `.ci/` and `.github/workflows/`;
- confirmed local source patches, when they have been identified and recorded.

Do not assume every unusual file is a BRC change. This tree carries upstream WRF
structure, older documentation conventions, generated build products, and local
automation side by side. Confirm provenance before labeling something local.

## Where To Change What

- For first-contact repo orientation, update `README.md`, `AGENTS.md`, or a
  focused guide in `doc/`.
- For upstream WRF version, public-domain notice, release notes, or the broad
  upstream documentation index, leave extensionless `README` as the source of
  truth unless explicitly asked to update upstream-facing metadata.
- For local build, run, or regression automation, start in `.sane/wrf/README.md`
  and then inspect the specific script, host config, or SANE test definition.
- For CI compile behavior, start with `.ci/tests/build.sh` and
  `.github/workflows/ci.yml` before following helper calls.
- For test-case behavior, read `doc/README.test_cases`, then narrow to the
  relevant `test/` case directory.
- For WRF model behavior, use narrow `rg` searches first, then open the relevant
  source subtree only after the symbol, namelist option, registry entry, or
  module is identified.

BRC-facing docs and automation do not need to mimic upstream WRF layout when a
short local guide or wrapper makes the fork easier to operate.

## Build/Install Reality

Both build paths exist here:

- legacy WRF: `./configure`, `./compile`, and `./clean`;
- CMake-oriented WRF: `./configure_new`, `./compile_new`, and
  `./cleanCMake.sh`.

Do not choose between them by habit. Inspect the relevant doc, CI path, SANE
script, or user request first.

"Install" can mean different things in this checkout:

- a CMake install tree such as `install/`;
- a copied or isolated legacy build directory;
- a test-case run directory under `test/` or an install tree;
- a staged case directory created by local automation;
- an HPC workflow output location.

Before changing install behavior, identify which meaning is in play and which
script or documentation currently owns it.

## Cheap Before Expensive

Prefer small, local checks before compile-scale work:

- `git status --short --untracked-files=all`;
- `sed -n` reads of `README.md`, `AGENTS.md`, and the relevant `doc/README*`;
- `rg` for specific symbols, options, scripts, or paths;
- `bash -n <script>` for shell changes;
- `python -m py_compile <file>` for Python changes;
- dry-run or read-only inspection for workflow and HPC paths.

Do not run full builds, WRF cases, regression suites, SANE actions, Slurm/PBS
jobs, or other HPC workflows without explicit approval. If a command might
compile, clean, move outputs, submit work, or consume allocation time, stop and
inspect the command path first.

## Confirmed Unknowns

- The BRC-supported host, compiler, dependency, and use-case matrix still needs
  to be mapped from actual workflow use.
- Local deviations from upstream WRF should be recorded only after they are
  confirmed from code, git history, or operational evidence.
- A cheap smoke-test path is not yet documented well enough to treat as routine.
