# brc-tools → brc-wrf handoff — GFS analysis as the second Pelican forcing

**From:** brc-tools (`nwp/gfs-analysis-source` branch) · **2026-06-30**
**Re:** Prompt B of `BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md` (GFS/FNL pass)
**Scope note:** John authorized going past Prompt B's "stop before staging" line,
so this is not just a feasibility verdict — **the inputs are staged and verified**.
brc-tools owns source/staging only; **WPS/`real`/`wrf`/Slurm are yours.**

**WRF-side closeout:** consumed on 2026-06-30 by job `13753673` for
`pelican2013_gfs_3_1_333m_75lev`. WPS used `Vtable.GFS`, metgrid produced
`num_metgrid_levels = 27` and `NUM_METGRID_SOIL_LEVELS = 4`, `real.exe` and
`wrf.exe` completed, and the archive is
`/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_gfs_3_1_333m_75lev/full6h/run_20260630T181555Z/`.
Paired NAM/GFS WRF-output quicklooks were then rendered by job `13755401` under
each archive's `quicklooks/standardized_compare_20260630T214000Z/`.

## 1. Feasibility verdict — CONFIRMED (not inferred)

Target source: **NCEI GFS grid-004 (0.5°, GRIB2)** historical analysis — auth-free,
same NCEI archive tree as NAM/RAP. Chosen over NCAR-RDA FNL `ds083.2` because the
NCEI path needs no RDA account/`cdsapi`, and 0.5° is *finer* than 2013 FNL's 1°.

Field adequacy was read directly from the live `.inv` for
`gfsanl_4_20130202_1200_000` (metadata only, no GRIB body), and it carries exactly
what `real.exe` needs — including the two fields that blocked RAP:

| Field (RAP failure mode) | GFS grid-4 `.inv` |
| --- | --- |
| **Layered soil temp** (killed pressure-RAP) | ✅ `TMP:{0-0.1, 0.1-0.4, 0.4-1, 1-2} m below ground` (4 layers) |
| **Layered soil moisture** | ✅ `SOILW:` same 4 layers |
| **Real-ready 3D atmosphere** (killed hybrid-RAP) | ✅ 26 pressure levels: `HGT/TMP/RH/UGRD/VGRD` |
| Land mask / skin / ice / snow | ✅ `LAND:surface`, `TMP:surface`, `ICEC:surface`, `WEASD:surface` |
| MSLP / 2 m / 10 m | ✅ `PRMSL`+`MSLET`, `TMP/RH:2 m`, `UGRD/VGRD:10 m` |

**Caveat (minor):** humidity is **RH** (which `Vtable.GFS` expects); snow is
**`WEASD`** (water-equiv) only — no `snod` (snow depth). metgrid will produce
`SNOW`; `SNOWH` may be absent and Noah can derive it. Not a `real.exe` blocker.

## 2. Case name

`pelican2013_gfs_3_1_333m_75lev` — the GFS analog of `pelican2013_nam_3_1_333m_75lev`.

## 3. Staged inputs + contract (READY on scratch)

```
/scratch/general/vast/$USER/wrf_inputs/pelican2013_gfs_3_1_333m_75lev/
├── gfs_analysis/
│   ├── gfsanl_4_20130202_1200_000.grb2   (51,685,546 B)
│   └── gfsanl_4_20130202_1800_000.grb2   (51,165,651 B)
├── manifest_pelican2013_gfs_3_1_333m_75lev.json
└── contract_pelican2013_gfs_3_1_333m_75lev.json
```

`verify_manifest` → **2/2 OK** (SHA-256 re-hashed). The contract is a structural
**mirror of the NAM baseline** (same window, same 2 cycles, same interval):

```json
{
  "case": "pelican2013_gfs_3_1_333m_75lev",
  "valid_window": { "start": "2013-02-02T12:00:00Z", "end": "2013-02-02T18:00:00Z" },
  "sources": ["gfs_analysis"],
  "source_file_counts": { "gfs_analysis": 2 },
  "cadence_hours": { "gfs_analysis": 6 },
  "interval_hours": 6,
  "interval_seconds": 21600,
  "wps_fg_name": ["GFS"]
}
```

## 4. WPS Vtable

**`Vtable.GFS`** (ships with WPS; GRIB2 grid-004; humidity = RH). The contract's
`wps_fg_name=["GFS"]` is the metgrid `fg_name` token. Single stream — no filler.

## 5. brc-wrf next steps

1. `link_grib.csh` the two `gfs_analysis/*.grb2`, `ln -sf Vtable.GFS Vtable`,
   `ungrib.exe` → metgrid → `real.exe` → `wrf.exe`. Reuse the
   `pelican2013_nam_3_1_333m_75lev` namelists; only the forcing differs.
2. `&time_control interval_seconds = 21600` (from the contract). Window is the
   same 2013-02-02_12:00:00 → 18:00:00 as NAM.
3. **Acceptance check — the whole point:** confirm metgrid writes
   `NUM_METGRID_SOIL_LEVELS > 0` (expect 4) and a full `num_metgrid_levels`
   stack. That is the exact failure mode that stopped RAP; GFS should clear it.
4. If `real.exe` complains about `SNOWH`, it is the `snod` gap above — safe to
   proceed (Noah derives depth from `SNOW`/`WEASD`).

## 6. Approval text (brc-wrf side)

```
Approve a WPS → real.exe → wrf.exe run in brc-wrf for
pelican2013_gfs_3_1_333m_75lev using the staged GFS contract
(/scratch/general/vast/$USER/wrf_inputs/pelican2013_gfs_3_1_333m_75lev/),
Vtable.GFS, interval_seconds=21600, reusing the pelican2013_nam namelists.
Acceptance: SUCCESS COMPLETE WRF + NUM_METGRID_SOIL_LEVELS > 0.
```

## 7. Optional fast-follow (brc-tools, only if you want finer LBCs)

grid-4 ships `_003`/`_006` forecast offsets, so 3-hourly boundaries
(`interval_seconds=10800`, 12/15/18Z from the 12Z+18Z cycles) are available with a
small brc-tools stager change (the analysis filename template currently hardcodes
`_000`). Ask and I'll wire it; the 6-hourly set above matches the NAM baseline for
a clean apples-to-apples ensemble pair.

## 8. What changed in brc-tools (branch `nwp/gfs-analysis-source`)

- `brc_tools/nwp/lookups.toml` — `[models.gfs_analysis]` (NCEI grid-004 templates,
  `cadence_hours=6`, `wps_fg_name="GFS"`).
- `brc_tools/nwp/wrf_staging.py` — `stage_gfs_analysis()` wrapper; `gfs_analysis`
  in the `fg_name` fallback + CLI help. (Routing/contract were already source-generic.)
- `docs/nwp/NWP-SOURCE-MATRIX.md` — new `gfs_analysis` row.
- `tests/test_wrf_staging.py` — staging + contract tests (full suite 110 passed).
- Reproduce the stage:
  `conda run -n brc-tools-2026 python -m brc_tools.nwp.wrf_staging --case pelican2013_gfs_3_1_333m_75lev --init-time "2013-02-02 12Z" --source gfs_analysis --fxx-window 0,6 --http-ipv4-only --no-quicklook`
