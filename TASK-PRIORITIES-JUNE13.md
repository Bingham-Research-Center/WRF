# BRC WRF Task Priorities - June 13

Purpose: keep the next WRF/WPS work small, explainable, and split cleanly
between `brc-wrf`, `brc-tools`, and `brc-knowledge`.

## Current Truth

- `brc-tools` owns WRF input staging. `brc-wrf` consumes its
  `manifest_<case>.json` and `contract_<case>.json`; do not add downloader code
  here.
- Validated proof: NAM-only source contract, `Vtable.NAM`,
  `interval_seconds = 21600`, Jan-2013 Uinta Basin 12/4 km nested case,
  `2013-01-31_12:00:00` to `2013-02-02_00:00:00`. The old proof scratch
  `namelist.wps` used `ungrib prefix = 'FILE'` and `metgrid fg_name = 'FILE'`;
  future NAM-named WPS streams should keep `prefix = 'NAM'` paired with
  `fg_name = 'NAM'`.
- Proof evidence checked: brc-tools manifest `28/28 OK`; archived run has
  `SUCCESS COMPLETE REAL_EM INIT`, `SUCCESS COMPLETE WRF`, 194 files, 74
  `wrfout_d0*`, 2.2G.
- Not proven: GEFSv12 reforecast plus NAM two-stream forcing. Do not call it
  production-ready until WPS and `real.exe` pass with `fg_name = 'GEFS','NAM'`.
- Archive wrapper bug fixed in `brc-knowledge`: use `./wrfout_d0*` for rsync
  because WRF filenames contain colons.

## P0 - Preserve The Baseline

- Keep `brc-docs/BRC-WRF-FIRST-CASE.md` as the single short runbook for the
  validated proof path.
- Keep `brc-docs/BRC-WRF-USAGE.md` for operating posture, not detailed run
  logs.
- Keep `doc/BRC_WRF_HANDOFF.md` as backlog and next-session state, not a manual.
- Do not submit Slurm, run WPS, run `real.exe`, or run `wrf.exe` without explicit
  approval.

## P1 - GEFS+NAM Two-Stream Proof

Microtasks:

1. Read `../brc-tools/docs/WRF-INPUT-STAGING.md` contract section and
   `lookups.toml` source layout before WPS work.
2. Build or select a GEFSv12 reforecast Vtable:
   - include pressure split fields: `_pres` and `_pres_abv700mb`;
   - use specific humidity, not relative humidity;
   - handle 10 m winds as height-level fields;
   - expect NAM to fill missing land/skin/snow fields.
3. Ungrib GEFS and NAM into separate intermediate streams.
4. Run metgrid with `fg_name = 'GEFS','NAM'`.
5. Check `met_em` field coverage and `num_metgrid_levels`.
6. Run `real.exe` only after approval and document IC/LBC source split.

Acceptance: `real.exe` reaches `SUCCESS COMPLETE REAL_EM INIT` with no missing
mandatory fields, and the docs say exactly which fields came from GEFS vs NAM.

## P1 - Scaling Benchmark

Microtasks:

1. Start from
   `../brc-knowledge/scholarium/reference-base/resources/run_wrf_feb05.slurm`.
2. Create one run copy per task count: 16, 28, 56.
3. Keep `--nodes=1`, `--nodelist=notch392`, `lawson-np`,
   `srun --mpi=pmi2`.
4. Record wall time per simulated hour, WRF success marker, archive path, and
   peak memory if available.
5. Compare against quickstart scaling guidance and pick the knee.

Acceptance: one table with tasks, wall time, memory, status, archive, and
recommendation for single case vs ensemble arrays.

## P1 - Wrapper Robustness

Microtasks:

1. Turn the validated Slurm wrapper into a brc-wrf-side template only after the
   build/WPS/run directory contract is stable.
2. Keep WRF success independent of Slurm batch state:
   - WRF marker: `SUCCESS COMPLETE WRF`;
   - real marker: `SUCCESS COMPLETE REAL_EM INIT`;
   - archive completeness: `wrfout*`, namelists, key `rsl.*`;
   - Slurm state: useful but not authoritative alone.
3. Never use `srun --jobid` probes inside a full WRF allocation.
4. Keep archive commands colon-safe: `rsync -av ./wrfout_d0* ...`.

Acceptance: a successful WRF run with successful archive does not become a
false failed batch because of post-run file handling.

## P2 - Repeatable Case Template

Microtasks:

Initial checkpoint: `brc-cases/` now holds a constrained case manifest, cheap
validator, and render-only Slurm command for the Jan-2013 NAM proof. Continue
to treat this as a review gate, not as approval to submit.

Microtasks:

1. Define a small `case.yaml` schema:
   case name, dates, domains, source contract path, WPS path, WRF path,
   archive path, account, partition, node, tasks. Initial version exists in
   `brc-cases/jan2013_basin_nam.case.yaml`.
2. Add a cheap validator:
   paths, geog, contract, namelist dates, `interval_seconds`,
   `num_metgrid_levels`, stale `met_em`, Slurm metadata. Initial version exists
   in `brc-cases/wrf_case.py`.
3. Render Slurm without submission. Initial command:
   `python brc-cases/wrf_case.py render-slurm brc-cases/jan2013_basin_nam.case.yaml`.
4. Require explicit `--allow-sbatch` or equivalent before real submission.

Acceptance: a new run can be reviewed as files and commands before any compute
work starts.

## Repo Accounting

- `brc-wrf`: commit docs/runbook/router changes and this priority file.
- `brc-knowledge`: commit the colon-safe rsync fix in the validated run script
  and quickstart snippet.
- `brc-tools`: no changes needed from this pass; it remains the staging owner.
- Existing scratch handoffs may stay untracked unless a human asks to promote
  them.
