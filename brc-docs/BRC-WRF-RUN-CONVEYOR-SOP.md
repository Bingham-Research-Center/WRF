# BRC WRF Run Conveyor SOP

Use this for staged WRF runs that chain data staging, WPS, `real.exe`/`wrf.exe`,
CFL gates, archive, and quicklooks.

## Non-Negotiables

- Any command that invokes sibling `../brc-tools` Python, Herbie, source
  planning, staging, manifest verification, or tests must force the maintained
  environment:

```bash
conda run -n brc-tools-2026 python ...
conda run -n brc-tools-2026 pytest ...
```

  Do not use bare `python`/`pytest` for `brc-tools` from a Codex shell; the
  inherited env may be unrelated to WRF staging.

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
<archive-run>/quicklooks/dXX/
```

That simple path is the default because the archive run already identifies the
case and timestamp. Use `--output-dir` only when you intentionally need to
preserve an alternate render. Older stamped folders such as
`quicklooks/standardized_compare_20260630T214000Z/` remain valid historical
evidence; do not move them just to rename them.

## Source-Agnostic Conveyor

NAM and GFS Pelican runs should follow the same WRF-side conveyor. The forcing
contract decides the source token, cadence, and Vtable; the domain geometry,
physics, archive, quicklook product list, and success checks stay parallel.

| Step | NAM | GFS |
| --- | --- | --- |
| Staged source | `nam_analysis` contract in `../brc-tools` | `gfs_analysis` contract in `../brc-tools` |
| WPS Vtable | `Vtable.NAM` | `Vtable.GFS` |
| `ungrib` prefix / `metgrid fg_name` | `NAM` / `NAM` | `GFS` / `GFS` |
| Pelican interval | `21600` seconds | `21600` seconds |
| Required metgrid proof | positive `num_metgrid_levels`, soil levels present | positive `num_metgrid_levels`, `NUM_METGRID_SOIL_LEVELS > 0` |
| WRF proof | `SUCCESS COMPLETE REAL_EM INIT`, then `SUCCESS COMPLETE WRF` | same |
| Quicklook default | `<archive-run>/quicklooks/dXX/` | same |

Do not hard-code NAM into the WRF-side conveyor. Read `forcing.sources`,
`forcing.wps_fg_name`, `forcing.interval_seconds`, and `wps.vtable` from the
case/contract. Reuse NAM namelists for a like-for-like GFS sensitivity only
when the source contract has the same window and cadence, as the 2026-06-30 GFS
run did.

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

## 2026-06-26 Pelican 333 m Baseline Evidence

Case: `pelican2013_nam_3_1_333m_75lev`

Run shape:

```text
d01: 3 km
d02: 1 km
d03: 0.333 km
e_vert: 75
window: 2013-02-02_12:00:00 to 2013-02-02_18:00:00
forcing: NAM analysis, Vtable.NAM, prefix NAM, fg_name NAM
```

Key jobs:

```text
stage:     13695257
WPS/prep:  13695258
smoke6h:   13695259
CFL gate:  13695260
full6h:    13695261, wrf.exe elapsed 6342 s
```

Full archive:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/
```

Control files:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/control/run_20260626T144836Z/
```

Quicklooks:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/quicklooks/
```

Standardized quicklooks should be regenerated with `brc-cases/wrf_quicklook.py`
from approved compute/batch context and should land under:

```text
<archive-run>/quicklooks/dXX/
```

Historical standardized render:

```text
job: 13729327, completed 0:0 in 00:00:55 on notch392
manifest check: 2/2 OK
products: 30 PNGs, 10 per d01/d02/d03
path: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/quicklooks/standardized_20260629T020921Z/
log: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/quicklook_pelican333_13729327.out
```

## 2026-07-02 Pelican 333 m NAM One-Way Feedback Evidence

Case: `pelican2013_nam_3_1_333m_75lev_oneway`

Run shape:

```text
d01: 3 km
d02: 1 km
d03: 0.333 km
e_vert: 75
window: 2013-02-02_12:00:00 to 2013-02-02_18:00:00
forcing: NAM analysis, Vtable.NAM, prefix NAM, fg_name NAM
nesting sensitivity: feedback = 0; smooth_option = 0
only namelist.input change from the NAM baseline: feedback = 1 -> feedback = 0
```

Key jobs:

```text
full6h: 13788264, completed 0:0 in 02:12:32 on notch392
wrf.exe step: 02:11:26
quicklook first attempt: 13791008, failed 1:0 because brc-tools-2026 lacked the xarray NetCDF backend
quicklook retry: 13791045, completed 0:0 in 00:00:53 using clyfar-nov2025 for NetCDF rendering
```

Full archive:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/full6h/run_20260702T053120Z/
```

Control files:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/control/run_20260702T053120Z/
```

Quicklooks:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev_oneway/full6h/run_20260702T053120Z/quicklooks/dXX/
```

Acceptance:

```text
SUCCESS COMPLETE REAL_EM INIT
SUCCESS COMPLETE WRF
archive phases exited 0
21 archived wrfout files, d01/d02/d03 hourly 12Z through 18Z
30 quicklook PNGs, 10 per d01/d02/d03
```

## 2026-06-30 Pelican 333 m GFS Evidence

Case: `pelican2013_gfs_3_1_333m_75lev`

Run shape:

```text
d01: 3 km
d02: 1 km
d03: 0.333 km
e_vert: 75
window: 2013-02-02_12:00:00 to 2013-02-02_18:00:00
forcing: GFS analysis, Vtable.GFS, prefix GFS, fg_name GFS
interval_seconds: 21600
metgrid: num_metgrid_levels = 27, NUM_METGRID_SOIL_LEVELS = 4
```

Key job:

```text
full6h: 13753673, completed 0:0 in 01:42:51 on notch392
wrf.exe step: 01:41:14
```

Full archive:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_gfs_3_1_333m_75lev/full6h/run_20260630T181555Z/
```

Control files:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_gfs_3_1_333m_75lev/control/run_20260630T181555Z/
```

Acceptance:

```text
SUCCESS COMPLETE REAL_EM INIT
SUCCESS COMPLETE WRF
archive phases exited 0
21 archived wrfout files, d01/d02/d03 hourly 12Z through 18Z
```

## 2026-06-30 Pelican 333 m NAM/GFS Comparison Quicklooks

These are the like-for-like products for the completed NAM and GFS WRF runs.
Both use the same six-hour window, 3/1/0.333 km nest, 75 vertical levels, and
standardized product names. They predate the simplified default quicklook path
and therefore live under a stamped historical subdirectory.

```text
job: 13755401, completed 0:0 in 00:01:38 on notch392
manifest checks: NAM 2/2 OK, GFS 2/2 OK
products: NAM 30 PNGs, GFS 30 PNGs; 10 per d01/d02/d03
stamp: standardized_compare_20260630T214000Z
summary: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_gfs_compare/control/quicklooks_20260630T214000Z/quicklook_summary_13755401.tsv
log: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/quicklook_pelican333_compare_13755401.out
```

NAM quicklooks:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1_333m_75lev/full6h/run_20260626T163737Z/quicklooks/standardized_compare_20260630T214000Z/
```

GFS quicklooks:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_gfs_3_1_333m_75lev/full6h/run_20260630T181555Z/quicklooks/standardized_compare_20260630T214000Z/
```
