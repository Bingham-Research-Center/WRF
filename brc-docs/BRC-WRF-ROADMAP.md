# BRC WRF Roadmap

This roadmap holds forward-looking work for making BRC WRF runs repeatable on
CHPC. Keep operational facts in `BRC-WRF-USAGE.md`; keep larger run records in
`../brc-knowledge`.

## On-Rails Natural-Language Runs

The long-term goal should not be a skill that turns free text directly into
`sbatch`. It should be a gated workflow:

1. `$wrf-plan-case`: turn natural language into a case manifest containing
   dates, domains, forcing source, intended build, run path, archive path, and
   Slurm target.
2. `$wrf-prepare-case`: create the scratch directory layout, copy or symlink
   templates, and write namelist drafts.
3. `$wrf-validate-case`: perform cheap checks only. Confirm paths, modules,
   geog, forcing files, namelist consistency, stale-file hazards, and Slurm
   account/partition/QOS.
4. `$wrf-render-slurm`: write the sbatch script but do not submit.
5. `$wrf-submit-case --allow-sbatch`: submit only after explicit human approval.
6. `$wrf-monitor-archive`: check `squeue`, logs, WRF success markers, and archive
   outputs to `lawson-group6`.

Each step should leave a short provenance record: Git SHA, module list, WRF/WPS
paths, forcing URLs or files, geog path, namelists, Slurm job id, and archive
location.

## Guardrails

- Natural language may choose a template, dates, and case intent, but not bypass
  validation.
- A rendered Slurm script is not a submission. Submission requires explicit
  human approval and an `--allow-sbatch`-style flag.
- The default run target should be owned Notchpeak (`lawson-np`) unless a case
  manifest explains why a preemptible or cross-cluster target is needed.
- Login-node work must stay limited to file reads, edits, syntax checks, path
  checks, module inspection, and scheduler queries.
- The workflow should reject missing `WPS_GEOG`, missing forcing files, stale
  `met_em.*` in a run directory, and a WRF launch without `srun --mpi=pmi2`.

## Survey Gaps Before First Supported Install

These are the gaps to close before treating this fork as fully on rails on CHPC:

- Decide whether BRC's first supported build path is legacy, CMake, or both.
- Validate the exact build/install command sequence for this fork on CHPC.
- Decide the canonical group build layout under `lawson-group6`.
- Document how WPS is obtained, built, versioned, and paired with this WRF fork.
- Add a CHPC Slurm host profile or wrapper; current `.sane/wrf` host config is
  Derecho/PBS-oriented.
- Create a template case manifest and namelist template set for Basin runs.
- Define a cheap smoke-test ladder: syntax checks, path checks, WPS metadata
  checks, `real.exe` in an allocation, then WRF batch.
- Add restart and requeue policy for preemptible Granite or longer production
  runs.
- Record any confirmed BRC source changes from upstream WRF in a local deviation
  log.

## Candidate First Milestones

1. Create a `case.yaml` schema for one Uinta Basin real-data case.
2. Render a Slurm script from the schema without submitting it.
3. Add a validator that checks only local paths, namelist consistency, WPS geog,
   and Slurm target metadata.
4. Validate the build path for this fork on CHPC and record exact evidence.
5. Promote one known-good case into a reusable example only after a successful
   run and archive.
