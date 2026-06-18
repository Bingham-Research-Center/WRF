# BRC WRF Gate 3 Few-Clicks Packet

Purpose: make Roadmap Gate 3, the John-owned WPS proof, as close as possible to
one reviewed `sbatch` command while preserving the approval boundary.

This packet is not approval by itself. Gate 3 is compile-scale WPS work. Run the
submit command only after John explicitly approves Gate 3 and the stop point
below.

## Stop Point

WPS executable proof only:

- no `geogrid.exe`, `ungrib.exe`, or `metgrid.exe` execution;
- no `real.exe`;
- no `wrf.exe`;
- no staging, strict artifact reads, NetCDF/archive checks, quicklooks, scaling,
  or memory benchmarks.

## One Command

If a WPS source checkout or tarball is already available:

```bash
cd ~/gits/brc-wrf
BRC_GATE3_APPROVED=YES \
BRC_WPS_SOURCE=/path/to/WPS-source-or-WPS.tar.gz \
BRC_WPS_CONFIGURE_OPTION=<wps-configure-menu-number> \
sbatch brc-cases/gate3_wps_proof.slurm
```

If the John-owned WPS root has already been built and only needs proof:

```bash
cd ~/gits/brc-wrf
BRC_GATE3_APPROVED=YES BRC_GATE3_MODE=verify \
sbatch brc-cases/gate3_wps_proof.slurm
```

The script intentionally does not guess `BRC_WPS_CONFIGURE_OPTION`. Use the WPS
configure menu entry that matches the approved Intel classic stack and desired
WPS build mode.

Known successful 2026-06-18 proof:

```bash
BRC_GATE3_APPROVED=YES \
BRC_WPS_SOURCE=/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_sources/WPS-v4.6.0 \
BRC_WPS_CONFIGURE_OPTION=23 \
sbatch brc-cases/gate3_wps_proof.slurm
```

For WPS v4.6.0 on this CHPC stack, option `23` selected Linux x86_64 Intel
Classic compilers with `dmpar`. The helper pins Intel MPI wrappers after
configure so `configure.wps` uses `mpif90 -f90=$(SFC)` and `mpicc -cc=$(SCC)`.

## Defaults

| Field | Default |
| --- | --- |
| WRF root | `$HOME/gits/brc-wrf` |
| WPS root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build/WPS` |
| Build-log root | `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf` |
| Static geography | `/uufs/chpc.utah.edu/common/home/lawson-group6/WPS_GEOG` |
| Slurm target | `lawson-np`, `notch392`, 1 node, 8 tasks, 32G, 2 hours |
| Module stack | Intel oneAPI compilers/MPI, HDF5, netCDF-C, netCDF-Fortran |

## Evidence Written

Each run writes to:

```text
/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf/gate3_<UTC>_<jobid>/
```

Expected files:

- `source_state.txt`
- `modules_loaded.txt`
- `build_env.txt`
- `configure_transcript.txt`
- `configure.wps`
- `compile_wps.log` when build mode is used
- `executable_inventory.txt`
- `closeout.txt`
- `gate3_wps_proof.log`

Gate 3 passes only if the John-owned WPS root contains:

- `geogrid.exe`
- `ungrib.exe`
- `metgrid.exe`
- `link_grib.csh`
- `ungrib/Variable_Tables/Vtable.NAM`
- `configure.wps` with `-DUSE_JPEG2000` and `-DUSE_PNG`

## Gate 4 Follow-Up

After Gate 3 passes, the next no-run item is Roadmap Gate 4, case manifest root
alignment:

```bash
cd ~/gits/brc-wrf
bash brc-cases/gate4_manifest_alignment_review.sh
```

Review the rendered Slurm text only. Do not submit it as part of Gate 4.

The 2026-06-18 metadata review passed with `OK: no findings` and rendered:
`/tmp/jan2013_basin_nam.gate4.20260618T054655Z.rendered.slurm`.
