# Pelican 333 m Next-Iteration Handoff

Use this to start the next Codex iteration for a short, comparable Pelican Lake
WRF replay with a 333 m inner nest.

## Paste-Ready Prompt

```text
cwd=/uufs/chpc.utah.edu/common/home/u0737349/gits/brc-wrf

Read AGENTS.md first. Then read:
- brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md
- brc-docs/BRC-WRF-DOMAIN-PREVIEW-SOP.md
- brc-docs/BRC-WRF-PELICAN-333M-HANDOFF.md

Goal: run the next Pelican Lake WRF conveyor using the recommended
3 km -> 1 km -> 0.333 km nested setup. Keep the run otherwise close to the
completed Pelican 3/1 km 75-level NAM-only case so output can be compared.

Requested replay window: 2013-02-02_12:00:00 to 2013-02-02_18:00:00
UTC, initialized at 1200 UTC.

Before submitting anything, verify that the staged NAM-analysis inputs cover
the 1200 UTC initialization and 1800 UTC boundary time. This window is on the
normal 00/06/12/18 UTC NAM-analysis cadence; do not silently shift the window
or use a different forcing interpretation.

If the forcing decision is acceptable, build the staged conveyor:
1. geogrid/domain preview for d01/d02/d03 and archive the PNG;
2. stage inputs using brc-tools on DTN;
3. WPS plus WRF_RUN preparation;
4. short WRF smoke run with CFL gate;
5. full six-hour WRF run only after the gate passes;
6. quicklook render from shared archive control files.

Use shared control files under the case archive. Do not depend on /tmp inside
Slurm jobs. Do not allow Slurm stdout/stderr to land in the git checkout.
Keep polling conservative and inspect structured debug artifacts before logs.
```

## Current On-Rails Docs

`AGENTS.md` points to both refreshed SOPs from this session:

- `brc-docs/BRC-WRF-DOMAIN-PREVIEW-SOP.md`
- `brc-docs/BRC-WRF-RUN-CONVEYOR-SOP.md`

The run conveyor SOP captures the fixes from the successful Pelican run:

- normal rendered WRF Slurm scripts use shared `--chdir`, `--output`, and
  `--error`;
- Slurm control files must live in shared archive storage, not `/tmp`;
- quicklook case YAML must match the brc-tools manifest/contract base case name;
- CFL scan patterns must avoid false positives from harmless `W-COURANT` and
  substring matches;
- quicklook PNGs belong under `<archive-run>/quicklooks/`.

## Reference Run To Compare Against

Completed case: `pelican2013_nam_3_1km_75lev`

```text
window: 2013-02-02_00:00:00 to 2013-02-03_00:00:00
d01: 3 km, 211 x 211
d02: 1 km, 151 x 151
e_vert: 75
time_step: 15 s parent, 5 s child effective
forcing: NAM analysis, Vtable.NAM, prefix NAM, fg_name NAM
physics: keep as baseline unless there is a clear stability reason
full WRF job: 13682649, completed 0:0 in 02:10:06
wrf.exe: 02:08:35
archive: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1km_75lev/full24h/run_20260625T212123Z/
quicklooks: /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_nam_3_1km_75lev/full24h/run_20260625T212123Z/quicklooks/
```

## Proposed 333 m Geometry

Start from the same parent footprint and add one compact inner nest:

```text
max_dom = 3
dx/dy = 3000, 1000, 333.333
parent_grid_ratio = 1, 3, 3
parent_time_step_ratio = 1, 3, 3
d01 e_we/e_sn = 211, 211
d02 e_we/e_sn = 151, 151
d03 e_we/e_sn = 151, 151
d02 i_parent_start/j_parent_start = 81, 81
d03 i_parent_start/j_parent_start = 51, 51
ref_lat = 40.25
ref_lon = -109.65
stand_lon = -109.65
```

This puts a roughly 50 km inner nest inside the 150 km 1 km nest. Review the
domain PNG before WPS.

## Vertical And Time Step

Use the same 75-level eta stack as the completed Pelican run unless there is a
reason to back off.

For the first 333 m attempt, prefer:

```text
time_step = 12
effective d02 timestep = 4 s
effective d03 timestep = 1.333 s
```

If the operator wants maximum similarity and accepts higher CFL risk,
`time_step = 15` gives a 1.667 s d03 effective timestep. The conservative first
conveyor should use 12 s.

## Wallclock Estimate

From the completed 3/1 km run:

```text
24 simulated hours -> 02:08:35 wrf.exe
about 5.4 wall-minutes per simulated hour
```

Adding a 151 x 151 333 m d03 roughly increases compute per parent step by about
one additional 1 km-domain-equivalent at 3x the d02 substeps. For a six-hour run:

```text
expected wrf.exe wallclock: 45-90 minutes
expected Slurm request: 03:00:00 for smoke/full first proof
```

If d03 is enlarged beyond 151 x 151, expect cost to grow approximately with
inner-domain grid-cell count.

## Stop Conditions

Stop and ask before WRF if:

- NAM-analysis staging cannot provide the 1200 UTC initialization and 1800 UTC
  boundary time for the requested window;
- `geogrid` places Pelican Lake near a d03 edge;
- `metgrid` lacks required land/soil/skin/snow fields;
- `real.exe` fails;
- the CFL gate finds true CFL/NaN/fatal patterns;
- quicklook control files would need `/tmp` or repo-local output.
