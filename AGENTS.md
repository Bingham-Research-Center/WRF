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
- `README.md`: BRC-facing landing page for humans. It may point to upstream WRF
  resources, CHPC references, and deeper local docs, but should stay short
  instead of becoming a full operating manual.

## First Reads

- `README`: version, public-domain notice, and index of WRF documentation files.
- `README.md`: BRC landing page, repository roles, local workflow pointers, and
  upstream WRF user, registration, citation, and public-notice links.
- `brc-docs/README.md`: concise BRC-facing docs index.
- `brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md`: terse change reel for the BRC fork
  layer.
- `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`: print-sized current state, reading
  packet, and maximum owned-node Slurm profile.
- `brc-docs/BRC-TOOLS-LINK-HANDOFF.md`: current brc-wrf -> brc-tools handoff
  for tightening the input-staging contract and stale-proof edge cases.
- `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`: current brc-tools -> brc-wrf
  run-side handoff after staging-contract updates.
- `brc-cases/README.md`: case manifest, cheap validator, and render-only Slurm
  checkpoint plus no-run quicklooks.
- `doc/BRC_WRF_MICROTASK_HANDOFF.md`: WRF-run-side control board for the
  remaining cross-repo microtasks, countdown, no-run prep, and parked
  human/approval batch.
- `brc-docs/BRC-WRF-USAGE.md`: CHPC usage posture, storage layout, login-node
  boundary, and standard WRF run shape.
- `brc-docs/BRC-WRF-FIRST-CASE.md`: current start-to-finish Jan-2013 Basin
  proof path connecting `brc-tools` staged input to WPS, WRF, and archive
  checks.
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

## Current Run Truth

- Validated proof: NAM-only, `Vtable.NAM`, `interval_seconds = 21600`,
  Jan-2013 Uinta Basin 12/4 km nested case. The input contract/source identity
  is NAM; the old proof scratch `namelist.wps` used the WPS default
  `ungrib` prefix `FILE` with `metgrid fg_name = 'FILE'`.
- The old proof scratch predates fresh `brc-tools` contract sidecars, so this
  repo carries `brc-cases/jan2013_basin_nam.contract.json` as a reconstructed
  NAM-only contract for strict validation. Fresh staging should still emit
  `contract_<case>.json` from `brc-tools`.
- No-run visual QA exists:
  `python brc-cases/wrf_quicklook.py render brc-cases/jan2013_basin_nam.case.yaml`
  writes PNGs beside the durable archive run, for example
  `<archive-run>/quicklooks/`; repo-local PNG output is refused. This is a
  practical NetCDF/archive read and must run off-login.
- Paramount CHPC rule after the 2026-06-17 retrospective: do not run practical
  WRF checks, Python test suites, manifest hashing, NetCDF reads, quicklook
  checks/renders, staging plans, WPS, `real.exe`, `wrf.exe`, or any data-heavy
  command on a login node. Login-node work is limited to reading/editing small
  docs, preparing scripts, and submitting or querying approved Slurm work.
- 2026-06-17 lesson learned: an earlier no-run validation pass was executed from
  `notchpeak1` login. It was fast because it reused existing artifacts, but this
  is now explicitly disallowed for future practical tests. Re-run from scratch
  in a Slurm allocation/session using the June 17 handoff.
- Current maximum owned-node Slurm profile is `owned_notch392_max`: `lawson-np`,
  `notch392`, one node, 56 tasks, `900G`, `srun --mpi=pmi2`.
- Not validated: GEFSv12 reforecast plus NAM two-stream forcing
  (`fg_name = 'GEFS','NAM'`, `interval_seconds = 10800`).
- `brc-tools` owns input staging and emits `manifest_<case>.json` plus
  `contract_<case>.json`; do not add NWP downloader code here.
- NWP downloads/staging should use `brc-tools`, Herbie-backed paths where
  available, and `notchpeak-dtn` for full transfer work; historical NAM analysis
  may use the direct NCEI path already owned by `brc-tools`.
- The latest `brc-tools` staging hygiene is additive for the run side: manifest
  schema v2 plus token preflight are merged upstream, and `brc-wrf` reads the
  contract sidecar rather than manifest `staged_files`.
- Latest reverse handoff from `brc-tools` is
  `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`; the most recent hygiene handoff
  reports brc-tools PRs #23 and #24 merged to `main`, with nothing to merge in
  this repo. WRF run profiles, WPS, `real.exe`, `wrf.exe`, scaling, and memory
  benchmarks stay owned by `brc-wrf`/`brc-knowledge`.
- `brc-knowledge` owns canonical CHPC reference material and the validated
  example Slurm script.
- Current CHPC guidance rechecked against `brc-knowledge` on 2026-06-17:
  default WRF run posture is still single-node `notch392` on `lawson-np`,
  `srun --mpi=pmi2`, scratch for live WRF I/O, and `lawson-group6` for durable
  archives. See `../brc-knowledge/scholarium/reference-base/resources/`.
- `brc-wrf` owns source, WRF-side docs, templates, validators, and any maintained
  WPS/WRF consumption wrapper.
- Build/install truth must be checked from disk before submission. The
  `~/gits/brc-wrf` checkout is John's source tree and intended WRF build root,
  but a fresh clone has no `real.exe` or `wrf.exe` until it is compiled. Do not
  silently fall back to another user's group build such as `u6060939`, and do
  not trust stale `jrlawson/wrf_build` paths unless the executable files exist.
- WPS is a separate install/root from this WRF source checkout. A real WPS/WRF
  submission needs both a valid John-owned WRF executable root and a valid
  WPS root with `geogrid.exe`, `ungrib.exe`, `metgrid.exe`, `link_grib.csh`,
  and `Vtable.NAM`.
- Generated data, staged inputs, run directories, run-specific namelists,
  rendered per-run Slurm scripts, model logs, NetCDF, PNGs, and one-off option
  files must not be written into this repo. Keep only reusable templates and
  source-controlled docs/code here. Live WPS/WRF I/O belongs on scratch; durable
  artifacts belong under `lawson-group6/<namespace>/...` outside the checkout
  and outside `$HOME/gits`.
- Remaining microtask routing, countdown, WRF-side no-run prep, and parked
  approval-gated work live in `doc/BRC_WRF_MICROTASK_HANDOFF.md`; keep that
  detailed control board current instead of expanding this router.

## Doc Currency (caretaker)

When any of these change, update the named file in the same commit:

- `brc-tools` contract/manifest fields or staging flags -> "Current Run Truth"
  here.
- A proof state flips, for example GEFS+NAM two-stream proven -> "Current Run
  Truth" here plus `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` and
  `brc-docs/BRC-WRF-FIRST-CASE.md`.
- Any `../brc-tools` path is renamed -> run the cross-repo link-check and fix
  references.

`README.md` is for humans; `AGENTS.md` is for agents. Do not duplicate run logic
into `README.md`.

## Routing

- Repo or fork-orientation task: start with `README.md`, `AGENTS.md`, and
  `doc/BRC_FORK_GUIDE.md`.
- Priority or next-task question: read `doc/BRC_WRF_MICROTASK_HANDOFF.md`; use
  `doc/BRC_WRF_HANDOFF.md` only as a slim pointer.
- Remaining microtask split, countdown, or "what can Codex do next" question:
  read `doc/BRC_WRF_MICROTASK_HANDOFF.md`, then stay in the repo lane named by
  the relevant table.
- Current milestone/state or printable handoff question: read
  `brc-docs/BRC-WRF-STATE-PLAYBOOK.md`, then
  `brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md`.
- Task for an outside AI starting in `brc-tools`: read
  `brc-docs/BRC-TOOLS-LINK-HANDOFF.md`, then
  `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`.
- Task handed back from `brc-tools` into `brc-wrf`: read
  `../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`, then follow its listed read packet
  in order. Run only its cheap manifest and strict-validator checks unless a
  human explicitly approves DTN staging, WPS, WRF, or Slurm work.
- First-case proof or run explanation: read `brc-docs/BRC-WRF-FIRST-CASE.md`,
  then `brc-docs/BRC-WRF-USAGE.md`.
- Focused docs task: start with `README.md`, `AGENTS.md`, and the relevant
  `doc/README*` file.
- BRC CHPC usage or on-rails workflow task: start with `brc-docs/README.md`,
  then read either `brc-docs/BRC-WRF-USAGE.md` or
  `brc-docs/BRC-WRF-ROADMAP.md`.
- Case manifest, validator, or Slurm-render task: start with
  `brc-cases/README.md`, then inspect the relevant `*.case.yaml` file and
  `brc-cases/wrf_case.py`.
- Local automation task: read `.sane/wrf/README.md`, then inspect the specific
  script, host config, or SANE test definition.
- CI task: inspect `.ci/tests/build.sh`, `.github/workflows/ci.yml`, and only
  then the called helper or workflow.
- Test-case task: read `doc/README.test_cases`, then narrow to the relevant
  `test/` case directory.
- Model-code task: use narrow `rg` searches before opening large source
  subtrees such as `dyn_*`, `phys`, `chem`, or `external`.

## Build And Test Caution

Never use a login node for practical test execution in this workflow. If a
check reads staged GRIBs, WPS/WRF NetCDF files, manifests, or archive outputs,
run it in an approved interactive/batch compute context or do not run it.

Both build paths exist:

- Legacy: `./configure`, `./compile`, `./clean`
- CMake-oriented: `./configure_new`, `./compile_new`, `./cleanCMake.sh`

Do not assume one path is correct for a task. Inspect the relevant docs,
workflow, or script before choosing.

Do not run full builds, regression tests, Slurm jobs, or other HPC workflows
without explicit user approval. WRF builds and tests can be expensive.

## Login-Node-Safe First Commands

Use these read-only commands for an initial orientation when relevant. They
should not read staged GRIBs, WPS/WRF NetCDF, archives, or manifests.

- `git status --short`
- `sed -n '1,120p' README.md`
- `sed -n '1,80p' README`
- `sed -n '1,140p' brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
- `sed -n '1,140p' brc-docs/BRC-TOOLS-LINK-HANDOFF.md`
- `sed -n '1,160p' doc/README.cmake_build`
- `sed -n '1,140p' .sane/wrf/README.md`
- `sed -n '1,160p' .ci/tests/build.sh`
- `python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py`
- `find . -path ./.git -prune -o -name AGENTS.md -print`
- `find . -maxdepth 3 \( -name wrf.exe -o -name real.exe -o -name geogrid.exe -o -name ungrib.exe -o -name metgrid.exe \) -print`

If a task concerns tests, read `doc/README.test_cases`; note that this checkout
uses the dotted filename even though some upstream-oriented references may use a
different spelling.

## Off-Login Practical Checks

Run these only inside an approved Slurm batch or interactive compute context,
never on a login node:

- `python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest ...`
- `python brc-cases/wrf_case.py validate ... --strict-files` when it reads
  scratch inputs, manifests, WPS/WRF files, or archive paths.
- `python brc-cases/wrf_quicklook.py check ...`
- `python brc-cases/wrf_quicklook.py render ...`
- WPS, `real.exe`, `wrf.exe`, NetCDF field inspection, and any staging plan or
  data-heavy filesystem inventory.

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

## WRF Run Gotchas Confirmed

- Use `/scratch/general/vast/$USER/wrf_inputs/<case>/` for staged forcing and
  `/scratch/general/vast/$USER/wrf_runs/<case>/` for active WPS/WRF case I/O.
  These are scratch paths, not durable archives; promote important outputs to
  `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/`.
- No-run quicklooks are review artifacts beside the durable archive run, for
  example `lawson-group6/<namespace>/wrf_archive/<case>/run_<UTC>/quicklooks/`.
  They must not be written into the repo checkout and are not a substitute for
  a new WPS/WRF run.
- Rendered WRF run wrappers should preserve compact debug artifacts beside WRF's
  native logs: `debug/run_debug_summary.txt`, `debug/run_phase_times.tsv`, and
  `debug/run_file_inventory.tsv`.
- Recheck `df -h` and quota/storage tooling before large runs. Filesystem-wide
  free space is not the same thing as a user or group quota.
- If staging/download behavior changes, patch `brc-tools`, not this WRF tree.
- WRF filenames contain colons, for example `wrfout_d01_YYYY-MM-DD_HH:MM:SS`.
  When using `rsync`, prefix local sources with `./wrfout...` or rsync may treat
  them as remote-style paths.
- A Slurm batch wrapper can be marked failed even when `wrf.exe` completed
  successfully, if a post-WRF archive step fails. Check the WRF step, the
  `SUCCESS COMPLETE WRF` marker, and archived artifacts separately.
- Avoid `srun --jobid` probe commands inside a fully occupied WRF allocation;
  they can leave a pending step waiting for resources.
- Slurm accounting can fail from this environment even when jobs are healthy.
  Fall back to exact logs, success markers, `squeue`, and on-disk artifacts.

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
