# BRC WRF Fork Highlight Reel

Plain-language summary of what changed in this fork layer since BRC work began
on top of upstream WRF 4.8.0.

## Microsteps

| Step | Commit or batch | Plain-language change | Why it mattered |
| --- | --- | --- | --- |
| 0 | upstream `06d4240a` | Started from WRF 4.8.0 release baseline. | Kept BRC work separate from upstream model code. |
| 1 | `067d6a19` | Added AI-agent context. | Made the first cold start less dependent on human memory. |
| 2 | `7a9181fb` | Added BRC WRF orientation. | Explained what this checkout is and is not. |
| 3 | `170ef2e0` | Documented fork boundaries. | Separated local BRC docs from upstream WRF source. |
| 4 | `f52b0c4b` | Documented `.sane/wrf` automation boundaries. | Prevented local automation from being mistaken for CHPC Slurm workflow. |
| 5 | `02e88abb` | Added a handoff doc. | Preserved next-session state without loading the whole tree. |
| 6 | `0560dc81` | Added concise BRC usage and roadmap docs. | Routed CHPC usage, WRF proof work, and future workflow ideas. |
| 7 | `f5ee2fc0` | Added WRF proof priorities. | Locked in the repo split: `brc-tools` stages inputs, `brc-wrf` consumes them, `brc-knowledge` owns CHPC truth. |
| 8 | `0f8dab0d` | Added the first case checkpoint. | Created a cheap `brc-cases/` manifest, validator, and render-only Slurm review gate. |
| 9 | current batch | Added no-run quicklooks. | Made the validated NAM-only proof visually inspectable without rerunning WPS or WRF. |
| 10 | current batch | Added a reconstructed NAM-only contract. | Removed the stale missing-contract warning while preserving that the old scratch manifest predates `brc-tools` sidecars. |
| 11 | current batch | Aligned the case Slurm profile with `brc-knowledge`. | Moved the local manifest to owned `notch392` max settings: `lawson-np`, 56 tasks, `900G`, `srun --mpi=pmi2`. |

## What Is Proven

| Topic | Current truth |
| --- | --- |
| Model baseline | Upstream WRF 4.8.0 source tree plus BRC-local docs and wrappers. |
| Input staging | `brc-tools` staged the Jan-2013 case inputs and verifies the manifest. |
| Validated forcing | NAM-only, `Vtable.NAM`, 6-hour cadence, Jan 31-Feb 2 2013 Basin case. |
| WPS output | 14 `met_em` files, d01/d02, with land, skin temp, snow, and soil fields. |
| WRF run | `real.exe` and `wrf.exe` reached success markers on CHPC. |
| Visual QA | Five PNG quicklooks render from existing WPS/WRF artifacts. |
| Not proven yet | GEFSv12 reforecast plus NAM two-stream forcing. |

## Current Review Commands

Login-node-safe source checks:

```bash
python -m py_compile brc-cases/wrf_case.py brc-cases/wrf_quicklook.py
```

Artifact checks below read manifests, scratch paths, WPS/WRF outputs, or
archives. Run them only inside an approved Slurm batch or interactive compute
context, not on a login node:

```bash
python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
python brc-cases/wrf_case.py render-slurm brc-cases/jan2013_basin_nam.case.yaml
python brc-cases/wrf_quicklook.py check brc-cases/jan2013_basin_nam.case.yaml
python brc-cases/wrf_quicklook.py render brc-cases/jan2013_basin_nam.case.yaml
```

These commands review existing metadata and artifacts. They do not run WPS,
`real.exe`, `wrf.exe`, Slurm, or a build.
