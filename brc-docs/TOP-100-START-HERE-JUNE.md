# Top 100 Start Here June

This is a terse task menu for practical/science WRF tests and code auditing.
It is not approval to run DTN staging, WPS, `real.exe`, `wrf.exe`, Slurm jobs,
large downloads, or scaling sweeps.

Tags:

- `now`: safe no-run work.
- `gate`: needs explicit human approval before execution.
- `science`: needs meteorological judgment.
- `audit`: code, settings, or provenance review.
- `tools`: belongs mainly in `../brc-tools`.
- `knowledge`: belongs mainly in `../brc-knowledge`.

## 1. Start Clean

- [ ] 001 `now` Run `git status --short --branch --untracked-files=all`.
- [ ] 002 `now` Read `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md`.
- [ ] 003 `now` Read `brc-docs/BRC-WRF-FIRST-CASE.md`.
- [ ] 004 `now` Read `brc-cases/README.md`.
- [ ] 005 `now` Read `doc/BRC_WRF_MICROTASK_HANDOFF.md`.
- [ ] 006 `audit` Write the current branch, HEAD, and remote in the session notes.
- [ ] 007 `audit` List dirty files before editing anything.
- [ ] 008 `audit` Separate facts from guesses in every handoff.
- [ ] 009 `audit` Name the owner repo before changing a file.
- [ ] 010 `audit` End each work block with command, evidence, and stop point.

## 2. Case Manifest And Settings

- [ ] 011 `now` Read `brc-cases/jan2013_basin_nam.case.yaml`.
- [ ] 012 `audit` Mark proven facts versus editable experiment settings.
- [ ] 013 `now` Run `python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml`.
- [ ] 014 `now` Run strict validation against the current reconstructed contract.
- [ ] 015 `audit` Confirm `forcing.sources` is NAM-only for the proven path.
- [ ] 016 `audit` Confirm `forcing.wps_fg_name` is `NAM`.
- [ ] 017 `audit` Preserve the old proof nuance: WPS scratch used `FILE`.
- [ ] 018 `audit` Confirm `interval_seconds = 21600` for NAM-only.
- [ ] 019 `audit` Confirm `num_metgrid_levels = 40` for the proof.
- [ ] 020 `now` Render Slurm text and verify it is review-only.

## 3. Input Staging Contract

- [ ] 021 `now` Verify the existing proof manifest reports `28/28 OK`.
- [ ] 022 `tools` Read `../brc-tools/docs/WRF-INPUT-STAGING.md`.
- [ ] 023 `tools` Read `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`.
- [ ] 024 `tools` Confirm fresh staging emits `manifest_<case>.json`.
- [ ] 025 `tools` Confirm fresh staging emits `contract_<case>.json`.
- [ ] 026 `audit` Treat the contract sidecar as the WRF input handshake.
- [ ] 027 `audit` Do not derive NAM-only truth from mixed-source manifest rows.
- [ ] 028 `gate` Decide whether to refresh the NAM-only staged contract.
- [ ] 029 `gate` If fresh staging exists, validate a copied case YAML against it.
- [ ] 030 `audit` Retire the reconstructed fallback only after fresh strict validation.

## 4. NWP Source And WPS Proof

- [ ] 031 `science` Decide whether GEFS+NAM two-stream is needed now.
- [ ] 032 `tools` Read `../brc-tools/docs/WRF-GEFS-NAM-FIELD-MAP.md`.
- [ ] 033 `audit` List expected GEFS pressure-level fields.
- [ ] 034 `audit` List expected GEFS near-surface fields.
- [ ] 035 `audit` List NAM filler fields: landsea, skin temp, snow, soil.
- [ ] 036 `audit` Draft the `Vtable.GEFS` review checklist.
- [ ] 037 `audit` Draft separate GEFS and NAM ungrib stream names.
- [ ] 038 `audit` Draft metgrid `fg_name = 'GEFS','NAM'`.
- [ ] 039 `audit` Draft two-stream `interval_seconds = 10800`.
- [ ] 040 `gate` Stop after metgrid field evidence; do not run `real.exe`.

## 5. Domain And Meteorology QA

- [ ] 041 `science` Review domain bounds against the Uinta Basin question.
- [ ] 042 `knowledge` Confirm the intended `WPS_GEOG` path.
- [ ] 043 `science` Inspect terrain quicklook.
- [ ] 044 `science` Inspect d02 landmask quicklook.
- [ ] 045 `science` Inspect skin temperature and snow quicklook.
- [ ] 046 `science` Inspect d02 2 m temperature quicklook.
- [ ] 047 `science` Inspect d02 10 m wind quicklook.
- [ ] 048 `science` Inspect snow-depth quicklook.
- [ ] 049 `science` Record whether the NAM-only baseline is plausible.
- [ ] 050 `science` Record whether the soil warning changes trust in the proof.

## 6. WRF Wrapper And Slurm Safety

- [ ] 051 `knowledge` Compare rendered Slurm with the CHPC WRF quickstart.
- [ ] 052 `audit` Confirm account and partition are `lawson-np`.
- [ ] 053 `audit` Confirm node is `notch392`.
- [ ] 054 `audit` Confirm launcher is `srun --mpi=pmi2`.
- [ ] 055 `audit` Confirm `real.exe` success marker is required.
- [ ] 056 `audit` Confirm `wrf.exe` success marker is required.
- [ ] 057 `audit` Keep `real.exe` logs separate from WRF logs.
- [ ] 058 `audit` Archive `wrfout` files with colon-safe local paths.
- [ ] 059 `audit` Treat Slurm state, WRF state, and archive state separately.
- [ ] 060 `gate` Do not submit `sbatch` from a render-only review.

## 7. Scaling And Memory Tests

- [ ] 061 `gate` Approve benchmark scope before any WRF run.
- [ ] 062 `audit` Define the fixed case, dates, domains, and forcing.
- [ ] 063 `audit` Use 56 tasks as the current max-node baseline.
- [ ] 064 `audit` Add 28 tasks as the middle comparison.
- [ ] 065 `audit` Add 16 tasks as the low comparison.
- [ ] 066 `audit` Start memory evidence from the known `900G` profile.
- [ ] 067 `audit` Pick one smaller memory candidate at a time.
- [ ] 068 `audit` Record wall time per simulated hour.
- [ ] 069 `audit` Record peak memory evidence source.
- [ ] 070 `science` Pick the default profile only after timing and output checks.

## 8. Output, Archive, And Reproducibility

- [ ] 071 `now` Inventory the existing archive run path.
- [ ] 072 `audit` Count archived `wrfout_d01_*` files.
- [ ] 073 `audit` Count archived `wrfout_d02_*` files.
- [ ] 074 `audit` Confirm archived `namelist.input`.
- [ ] 075 `audit` Confirm archived `rsl.out.0000`.
- [ ] 076 `audit` Confirm archived `real.rsl.out.0000`.
- [ ] 077 `audit` Record archive size and file count.
- [ ] 078 `audit` Link quicklooks to the archive they came from.
- [ ] 079 `gate` Decide whether scratch inputs should be promoted.
- [ ] 080 `audit` Update runbook only from checked logs or artifacts.

## 9. Code Audit Targets

- [ ] 081 `audit` Review `brc-cases/wrf_case.py` parser limits.
- [ ] 082 `audit` Review invalid YAML failure behavior.
- [ ] 083 `audit` Review missing manifest failure behavior.
- [ ] 084 `audit` Review missing contract failure behavior.
- [ ] 085 `audit` Review inconsistent `fg_name` failure behavior.
- [ ] 086 `audit` Review bad Slurm profile failure behavior.
- [ ] 087 `audit` Verify render-slurm cannot submit jobs.
- [ ] 088 `audit` Review `wrf_quicklook.py` dependency errors.
- [ ] 089 `audit` Review archive path and colon filename handling.
- [ ] 090 `now` Run `python -m py_compile` on changed Python files.

## 10. Pair-Programming Workflow

- [ ] 091 `now` Start Michael with the practical packet, not the full WRF tree.
- [ ] 092 `now` Fill the no-run result table live.
- [ ] 093 `now` Compare proposed settings against the case YAML.
- [ ] 094 `science` Ask what weather question the next test answers.
- [ ] 095 `gate` Write the exact approval scope before any compute step.
- [ ] 096 `tools` Open a separate `brc-tools` session for staging changes.
- [ ] 097 `knowledge` Open a separate `brc-knowledge` session for CHPC truth.
- [ ] 098 `audit` Keep WRF code changes separate from docs-only changes.
- [ ] 099 `now` Render any handout PDFs with `md2pdf`.
- [ ] 100 `audit` Close with `git status`, commit hash, push state, and next gate.
