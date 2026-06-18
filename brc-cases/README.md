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
   root must contain `real.exe` and `wrf.exe`; the WPS root must contain
   `geogrid.exe`, `ungrib.exe`, `metgrid.exe`, `link_grib.csh`, and
   `ungrib/Variable_Tables/Vtable.NAM`. It also rejects repo-local staged
   inputs, run directories, archive roots, logs, and generated data paths.

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
   `APPROVAL_PACKET.md`, a baseline Slurm wrapper, scaling wrappers for
   16/28/56 tasks, optional memory-candidate wrappers, approval boundaries,
   validation commands, blank result tables, and a closeout record template.
   Generated wrappers keep per-scenario scratch and archive paths under
   `practical_tests/<scenario>/`, fail fast if the scenario `wrf_run` directory
   is not prepared with `real.exe`, `wrf.exe`, `namelist.input`, and `met_em`
   files, and still require explicit approval before `sbatch`. The prepare
   checklist describes how to stage those per-scenario `wrf_run` directories
   from the approved proven run artifacts, but any copy/check of scratch or
   archive WRF files remains off-login and approval-gated.

6. Render no-run visual quicklooks from the existing proof artifacts:

   ```bash
   python brc-cases/wrf_quicklook.py check brc-cases/jan2013_basin_nam.case.yaml
   python brc-cases/wrf_quicklook.py render brc-cases/jan2013_basin_nam.case.yaml
   ```

   The quicklook helper verifies the `brc-tools` input manifest first, then
   reads existing WPS `met_em` files and archived `wrfout` files. It does not
   run WPS, `real.exe`, `wrf.exe`, Slurm, or new input staging. It must run
   from an approved compute or interactive context, not a login node.
   Generated PNGs default to `<archive-run>/quicklooks/` under the durable
   `lawson-group6` archive; repo-local PNG output is refused.
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
download logic.

`wrf_quicklook.py` is separate from `wrf_case.py` on purpose: the case validator
stays dependency-free, while quicklook rendering uses the local NetCDF and
plotting stack when visual QA is wanted.
