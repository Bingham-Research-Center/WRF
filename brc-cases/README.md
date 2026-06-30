# BRC WRF Case Scaffolds

This directory holds BRC-local case manifests and the cheap helper used to
review them before any WPS, WRF, or Slurm work starts.

The checkpoint is intentionally small:

1. Write or edit a `*.case.yaml` file.
2. Validate the schema and cheap local facts:

   ```bash
   python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
   ```

   The Jan-2013 manifest points to the original `brc-tools` scratch manifest,
   and its contract path points to a tracked reconstructed NAM-only contract in
   this directory. Fresh `brc-tools` staging should emit a scratch
   `contract_<case>.json` next to the manifest instead.

3. Use stricter file checks only after inputs and run directories exist:

   ```bash
   python brc-cases/wrf_case.py validate --strict-files brc-cases/jan2013_basin_nam.case.yaml
   ```

   Strict validation also checks the declared WRF/WPS executable roots. The WRF
   build root must expose `main/real.exe`, `main/wrf.exe`, and runtime source
   files under `run/`; a scratch run directory with copied executables is not a
   build root. The WPS root must expose top-level `geogrid.exe`, `ungrib.exe`,
   `metgrid.exe`, `link_grib.csh`, and the case's configured
   `wps.vtable` under `ungrib/Variable_Tables/` (`Vtable.NAM` by default). It
   also rejects repo-local staged inputs, run directories, archive roots, logs,
   and generated data paths.

4. Render the Slurm script for review. This writes text only; it does not call
   `sbatch`.

   ```bash
   python brc-cases/wrf_case.py render-slurm brc-cases/jan2013_basin_nam.case.yaml
   ```

   This case uses the `owned_notch392_max` Slurm profile: owned `lawson-np`,
   `notch392`, one node, 56 tasks, `900G`, and `srun --mpi=pmi2`, matching the
   current `brc-knowledge` WRF quickstart. The earlier proof showed lower memory
   was enough; this profile deliberately reserves most of the large node for a
   high-powered single run.

   The rendered run wrapper writes a compact debug layer beside WRF's native
   `rsl.*` logs:

   | File | Purpose |
   | --- | --- |
   | `debug/run_debug_summary.txt` | Host, job, commit, paths, natural-language settings table, five gotchas, final status. |
   | `debug/run_phase_times.tsv` | `real.exe`, marker checks, `wrf.exe`, and archive phase timings with exit codes. |
   | `debug/run_file_inventory.tsv` | Counts, bytes, and newest mtimes for key `met_em`, `wrfinput`, `wrfbdy`, `wrfout`, and log patterns. |

   These files are first written under `<wrf_run>/brc_run_debug/` and then
   copied to `<archive-run>/debug/`, including failure exits when the archive
   path can be created.

5. Render the Gate 11 practical-test harness packet. This writes review
   artifacts outside the checkout; it does not submit Slurm or read staged,
   WPS/WRF, NetCDF, or archive artifacts.

   ```bash
   python brc-cases/wrf_case.py render-practical-harness \
     brc-cases/jan2013_basin_nam.case.yaml \
     --output-dir /tmp/brc_gate11_jan2013_basin_gefs
   ```

   The packet contains a `README.md`, `PREPARE_CHECKLIST.md`,
   `APPROVAL_PACKET.md`, approval-gated `prepare_<scenario>.sh` copy/check
   helpers, a baseline Slurm wrapper, scaling wrappers for 16/28/56 tasks,
   optional memory-candidate wrappers, approval boundaries, validation
   commands, blank result tables, and a closeout record template. Generated
   wrappers keep per-scenario scratch and archive paths under
   `practical_tests/<scenario>/`, fail fast if the scenario `wrf_run` directory
   is not prepared with `real.exe`, `wrf.exe`, `namelist.input`, and `met_em`
   files, or if the scenario executables do not byte-match
   `paths.wrf_build/main/{real.exe,wrf.exe}`. Runtime physics/table files must
   also byte-match John's `paths.wrf_build/run/` source files before `real.exe`
   starts. The prepare checklist sources executables and runtime physics files
   from John's compiled WRF tree, and uses the approved proven run artifacts
   only for `namelist.input` and `met_em` files. Current-case runtime preflight includes
   `CAMtr_volume_mixing_ratio`, `RRTMG_LW_DATA`, `RRTMG_SW_DATA`, ozone files,
   and core land-surface tables. Practical scripts set Slurm `--chdir`,
   stdout, and stderr to the shared
   `/uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_build_logs/brc-wrf`
   root so early failures remain visible even when review packets are rendered
   under `/tmp`. They report the full missing preflight set before exiting, so
   a failed setup is not mistaken for WRF runtime evidence. The generated prep
   helpers require `BRC_PREP_APPROVED=YES`, refuse Michael-owned comparison
   paths, copy/check files only, and never submit Slurm or execute WRF. Any
   copy/check of scratch or archive WRF files remains off-login and
   approval-gated, and `sbatch` still requires explicit approval.

6. Render the RAP WPS-only field proof packet when working the Pelican RAP
   hot-swap. This writes review artifacts only; it does not submit Slurm or run
   WPS by itself. The rendered script requires
   `BRC_WPS_FIELD_PROOF_APPROVED=YES` and stops after `ungrib.exe`,
   `metgrid.exe`, `met_em` field extraction, `num_metgrid_levels`, warning
   capture, and the field checklist. It never runs `real.exe`, `wrf.exe`, the
   full conveyor, or quicklooks.

   ```bash
   python brc-cases/wrf_case.py render-wps-field-proof \
     brc-cases/pelican2013_rap_3_1_333m_75lev.case.yaml \
     --output-dir /uufs/chpc.utah.edu/common/home/lawson-group6/jrlawson/wrf_archive/pelican2013_rap_3_1_333m_75lev/control/wps_field_proof_<UTC>
   ```

   The RAP proof packet uses the durable Pelican control `namelist.wps` as a
   template and the existing NAM 333 m `geo_em.d0*.nc` files as the domain
   source. If those scratch `geo_em` files have expired, stop and either restore
   them or explicitly approve a geogrid rerun before continuing.

7. Render a one-command no-run report when you want a compact login-safe
   checkpoint for handoff or approval review:

   ```bash
   python brc-cases/wrf_case.py render-no-run-report \
     brc-cases/jan2013_basin_nam.case.yaml
   ```

   The report writes under `/tmp` by default, renders the Gate 11 packet and a
   standalone Slurm review script outside the checkout, records branch/SHA,
   dirty state, case metadata validation, shell syntax status, artifact paths,
   and the explicit stop point. It does not run strict file checks, hash
   manifests, read NetCDF/archive artifacts, render quicklooks, submit Slurm, or
   run WPS/WRF.

8. Render no-run visual quicklooks from the existing proof artifacts:

   ```bash
   python brc-cases/wrf_quicklook.py check brc-cases/jan2013_basin_nam.case.yaml
   python brc-cases/wrf_quicklook.py render brc-cases/jan2013_basin_nam.case.yaml
   ```

   The quicklook helper verifies the `brc-tools` input manifest first, then
   reads existing WPS `met_em` files and archived `wrfout` files. It does not
   run WPS, `real.exe`, `wrf.exe`, Slurm, or new input staging. It must run
   from an approved compute or interactive context, not a login node.
   Generated PNGs default to `<archive-run>/quicklooks/standardized_<UTC>/`
   under the durable `lawson-group6` archive; repo-local PNG output is refused.
   Current WRF-output quicklooks render 10 standardized PNGs per case domain
   under `<archive-run>/quicklooks/<stamp>/dXX/`: temperature/wind, temperature
   anomaly, 2 m potential temperature, wind speed, PBL height, snow depth, skin
   temperature, surface pressure, and W-E/S-N potential-temperature
   cross-sections. The helper is a WRF-file adapter; reusable plotting
   primitives live in `../brc-tools/brc_tools/visualize/grid.py`.
   Path-only quicklook unit tests are login-node safe because they do not
   verify manifests, open NetCDF files, read archives, or render PNGs.
   The workflow source is tracked in `jan2013_nam_workflow.mmd`.

`wrf_case.py` uses only the Python standard library. Because this checkout does
not currently carry a YAML dependency, the `*.case.yaml` format is a deliberately
small subset: top-level sections, two-space-indented keys, quoted strings,
integers, booleans, and bracketed lists. Avoid anchors, nested lists, and complex
YAML features.

The helper is a pre-run review gate, not a workflow engine. Real WPS, `real.exe`,
`wrf.exe`, scaling sweeps, and Slurm submission still require explicit human
approval.

Input downloads and staging are not owned here. Use `../brc-tools`, its
Herbie-backed paths where available, and `notchpeak-dtn` for full NWP transfer
work. This repo should consume the fresh `contract_<case>.json` sidecar, not add
download logic. The RAP review case
`pelican2013_rap_3_1_333m_75lev.case.yaml` points at the staged RAP contract
and deliberately leaves metgrid-derived counts pending until the WPS-only
field-adequacy proof runs off-login.

When a case-review task needs sibling `brc-tools` Python, Herbie, source
planning, staging, manifest verification, or tests, force the maintained env:

```bash
conda run -n brc-tools-2026 python ...
conda run -n brc-tools-2026 pytest ...
```

Do not use bare `python` or `pytest` for `brc-tools` commands from this repo;
Codex shells can inherit unrelated environments.

`wrf_quicklook.py` is separate from `wrf_case.py` on purpose: the case validator
stays dependency-free, while quicklook rendering uses the local NetCDF and
plotting stack when visual QA is wanted.
