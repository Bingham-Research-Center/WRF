# BRC WRF Multiscale Roadmap

Terse state map for the current BRC WRF lane: what matters next, how big each
step is, and where to stop. This is a summary, not a replacement for
`doc/BRC_WRF_MICROTASK_HANDOFF.md`.

## North Star

Use the proven Pelican 3/1/0.333 km NAM baseline as the comparison anchor, then
hot-swap one forcing source at a time through `brc-tools` staging contracts and
`brc-wrf` WPS/WRF consumption proof.

Keep the loop small:

```text
source support -> staged contract -> WPS field adequacy -> real/wrf smoke/full
-> archive -> standardized quicklooks -> compare to NAM baseline -> decide
```

## Current Active Lane

The active lane is reviewing the first completed Pelican forcing pair. RAP was
the first attempted source and is blocked as RAP-only input before `real.exe`;
ERA5 is locally blocked by CDS tooling/credentials and missing source support;
GFS analysis completed WPS, `real.exe`, `wrf.exe`, archive, and paired
standardized quicklooks against the NAM baseline. FNL is optional third-source
work after the NAM/GFS review. GEFS+NAM two-stream is parked legacy context.

Confirmed current RAP state:

| Layer | State |
| --- | --- |
| `brc-tools` | RAP analysis source support exists; Pelican RAP input bundle is staged and verified on scratch. |
| Contract | `rap_analysis`, 7 hourly NCEI `rap_130` files, `wps_fg_name = ["RAP"]`, `interval_seconds = 3600`. |
| `brc-wrf` | RAP case manifest exists and points at the staged manifest/contract. |
| WPS proof packet | `render-wps-field-proof` renders the approval-gated RAP WPS-only script and evidence checklist. |
| WPS proof result | Hybrid-Vtable job `13744756` and pressure-Vtable job `13745030` both completed WPS but failed RAP-only field adequacy for WRF startup. |
| WPS Vtable | No generic `Vtable.RAP` exists in John's WPS root. `Vtable.RAP.hybrid.ncep` did not produce usable 3D atmosphere; `Vtable.RAP.pressure.ncep` produced 38 atmospheric levels but no layered soil temperature/moisture. |
| Open blocker | RAP-only staged product is incomplete for `real.exe`; fix source-product staging or design an explicit filler stream before any WRF run. |
| External dependency | The proof currently reuses NAM 333 m baseline `geo_em` files from scratch; if they expire, restore them or approve a geogrid rerun. |

Immediate stop point: do not run `real.exe` against the current RAP-only
`met_em` output.

ERA5 is the next listed source, but local evidence currently blocks immediate
staging: `brc-tools` has no `era5` WRF-staging source, `brc-tools-2026` lacks
`cdsapi`/`ecmwfapi`, and no CDS credentials are configured. The WPS side has a
plausible `Vtable.ECMWF`; the missing piece is the source/access path.

The active handoff is `brc-docs/BRC-WRF-PELICAN-NWP-HOTSWAP-HANDOFF.md`.
Use it for the NAM/GFS review path and for any explicit third-source approval.

## Near Term

| Priority | Task | Size | Stop point |
| ---: | --- | --- | --- |
| 1 | Inspect the paired NAM/GFS quicklooks. | S | Concise science-review packet: useful, suspect, or rerun/skip. |
| 2 | Preserve the current RAP and ERA5 blocker evidence in docs. | XS | Hybrid/pressure RAP proof outcomes and ERA5 local blocker stay file-backed. |
| 3 | Decide whether to ask for FNL or a corrected RAP/ERA5 path. | S | Exact approval text only; no new source work by default. |

## Medium Term

Only after John approves another source or corrected design:

| Priority | Task | Size | Stop point |
| ---: | --- | --- | --- |
| 1 | For FNL or another clean source, create/stage a contract in `brc-tools`. | M | Manifest/contract verified; no WPS until approved. |
| 2 | Run WPS/`real.exe` proof only after field adequacy is clear. | M | `SUCCESS COMPLETE REAL_EM INIT`; archive logs/debug separately from WRF run success. |
| 3 | Run the 6h WRF conveyor. | L | `SUCCESS COMPLETE WRF`, durable archive, compact debug evidence. |
| 4 | Render standardized quicklooks. | M | 10 PNGs per available domain under `<archive-run>/quicklooks/<stamp>/dXX/`. |
| 5 | Compare against NAM 333 m baseline. | M | Visual/science decision: useful, suspect, or rerun/skip. |

## Task-Size Ladder

| Size | Meaning | Examples |
| --- | --- | --- |
| XS | Login-safe metadata or doc preservation. | Validate case schema, update one router pointer, commit current RAP batch. |
| S | Review-only setup or approval packet. | Render/review WPS script text, write exact approval request, inspect Vtable names. |
| M | Approved off-login proof that reads staged/WPS artifacts. | Manifest verification, WPS-only field proof, `real.exe` proof, quicklook render. |
| L | Approved model run and archive workflow. | Six-hour WRF run, archive, quicklooks, NAM-vs-source comparison packet. |
| XL | Programmatic source campaign. | Repeat the hot-swap loop across RAP, ERA5, GEFSv12, GFS/FNL, CFSv2, and NARR. |

## Ownership Rules

| Repo | Owns | Do not put here |
| --- | --- | --- |
| `brc-tools` | Source access, downloads, staging, manifests, contracts, input quicklooks. | WPS, `real.exe`, `wrf.exe`, Slurm WRF wrappers. |
| `brc-wrf` | Case manifests, WPS/WRF consumption, validators, Slurm renderers, WRF-output quicklooks. | Downloader or GRIB-staging logic. |
| `brc-knowledge` | CHPC node, scheduler, storage, module, and validated Slurm guidance. | Repo-local case or source logic. |

Any `brc-tools` Python, Herbie, source-planning, staging, manifest verification,
or tests must be run with `conda run -n brc-tools-2026 ...` or the absolute
`brc-tools-2026` interpreter. Do not use bare `python`/`pytest`; Codex can
inherit unrelated envs.

## Parallel But Not Active

These matter, but they are not the default Pelican RAP lane:

| Item | Why it matters | When to resume |
| --- | --- | --- |
| Gate 10 NAM science acceptance | Confirms the NAM baseline is physically useful, not only technically complete. | When John/Michael want science review before more source experiments. |
| `scaling_t016` benchmark recovery | Improves runtime/memory efficiency evidence. | When practical benchmarking is explicitly reapproved. |
| GEFS+NAM two-stream | May be useful as a filler or ensemble path. | RAP-only does lack fields; revive only with explicit filler-design approval, not by default. |

## Anti-Drift Rules

- One forcing source at a time.
- Evidence before claims.
- Smallest useful proof before the next expensive run.
- No WPS, `real.exe`, `wrf.exe`, Slurm, NetCDF-heavy checks, or quicklooks
  without explicit approval for that class of work.
- Keep generated controls, logs, archives, NetCDF, and PNGs out of the repo.
- If a source fails field adequacy, stop and report missing fields before adding
  a filler stream.
- Do not let GEFS+NAM wording reappear as the current default path.
- Do not trust the active shell env for `brc-tools`; force
  `conda run -n brc-tools-2026 ...` before making Herbie/source claims.

## Next Review Prompt

```text
Inspect the completed NAM/GFS standardized quicklooks for the Pelican 2013
12-18Z, 3/1/0.333 km, 75-level hot-swap lane and summarize the forcing
sensitivity.

Use the paired quicklook roots under standardized_compare_20260630T214000Z.
Do not start FNL, corrected RAP, ERA5, downloads, staging, WPS, real.exe,
wrf.exe, or new quicklooks without explicit approval.
```
