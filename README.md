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
- `doc/README.cmake_build`: CMake build flow using `configure_new`,
  `compile_new`, and `cleanCMake.sh`.
- `doc/README.test_cases`: legacy idealized and real-data test-case overview.
- `.sane/wrf/`: BRC-local automation for build, run, and regression-style work.
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

## Wishlist / Todo

| Item | Feasibility | Likelihood | Craziness | Fundworthiness |
| --- | --- | --- | --- | --- |
| Add a short `.sane/wrf/README.md` that explains the local automation boundary. | High | High | Low | Medium |
| Document a cheap no-build validation path for common script and workflow edits. | High | High | Low | High |
| Map BRC-supported build paths by host, compiler, and intended use case. | Medium | Medium | Low | High |
| Add a small decision log for local WRF deviations from upstream. | Medium | Medium | Medium | Medium |
| Create a lightweight smoke-test harness that avoids full regression cost. | Medium | Medium | Medium | High |
| Build a cross-discipline "science intent to code path" index for common BRC work. | Medium | Low | Medium | High |
| Add provenance capture for local builds and runs that records source, config, and environment. | Medium | Medium | Medium | High |
| Create AI-assisted review checklists for physics, numerics, HPC, and documentation changes. | High | Medium | Low | Medium |

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
