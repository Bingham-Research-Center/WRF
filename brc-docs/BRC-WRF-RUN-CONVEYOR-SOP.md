# BRC WRF Run Conveyor SOP

Use this for staged WRF runs that chain data staging, WPS, `real.exe`/`wrf.exe`,
CFL gates, archive, and quicklooks.

## Non-Negotiables

- Do not let generated Slurm stdout default to `slurm-%j.out` in the git
  checkout. Rendered WRF Slurm scripts should set `#SBATCH --chdir`,
  `#SBATCH --output`, and `#SBATCH --error` to the shared log root:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/
```

- Do not submit a Slurm job that depends on a control file under `/tmp`. Copy
  case YAML, generated Slurm wrappers, and gate/quicklook control files to:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/<case>/control/<run_id>/
```

- Keep active WPS/WRF I/O on scratch:

```text
/scratch/general/vast/$USER/wrf_runs/<case>/<run_id>/
/scratch/general/vast/$USER/wrf_inputs/<case>/
```

- Keep durable output under the group archive:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/<case>/
```

## Quicklook Control Files

`brc-cases/wrf_quicklook.py` validates the brc-tools manifest/contract. The
quicklook case YAML `case.name` must match the staged manifest/contract case
name. If WRF run variants use suffixes such as `_part6h` or `_full24h`, create a
quicklook-specific case YAML in the shared control directory that:

- uses the base staged `case.name`;
- points `paths.archive_root` at the intended variant archive, such as
  `full24h`;
- points `paths.wps_run`, `paths.wrf_run`, and namelist paths at the run used;
- is submitted from the shared control path, not `/tmp`.

Quicklook PNGs belong under:

```text
<archive-run>/quicklooks/
```

## CFL Gate Pattern

Run the short smoke job first, then a separate CFL gate, then the full job with
`afterok:<gate_jobid>`.

The CFL/error scan should be targeted. Avoid matching harmless text such as
`W-COURANT` damping setup lines or substrings inside words like
`provenance`. Use word-boundary matching for `nan`.

## `real.exe` Launch

If Intel MPI prints `PMI server not found` when `real.exe` is launched directly,
that is usually singleton MPI startup noise, not a data-server failure. A
cleaner future wrapper option is:

```bash
srun --mpi=pmi2 -n 1 ./real.exe
```

Keep the existing success checks: `SUCCESS COMPLETE REAL_EM INIT`, WRF success
marker, archive phases, Slurm accounting, and compact debug files are separate
facts.

## 2026-06-25 Pelican Evidence

Case: `pelican2013_nam_3_1km_75lev`

Run shape:

```text
d01: 3 km, 211 x 211
d02: 1 km, 151 x 151
e_vert: 75
time_step: 15 s parent, 5 s child effective
window: 2013-02-02_00:00:00 to 2013-02-03_00:00:00
```

Key jobs:

```text
stage:        13682055 completed 0:0 in 00:00:45
WPS/prep:     13682056 completed 0:0 in 00:01:41
6h smoke:     13682057 completed 0:0 in 00:31:50
CFL gate fix: 13682648 completed 0:0 in 00:00:08
24h WRF:      13682649 completed 0:0 in 02:10:06
quicklooks:   13694421 completed 0:0 in 00:00:43
```

Full archive:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1km_75lev/full24h/run_20260625T212123Z/
```

Control files:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1km_75lev/control/run_20260625T203215Z/
```

Quicklooks:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1km_75lev/full24h/run_20260625T212123Z/quicklooks/
```
