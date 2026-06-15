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

5. Render no-run visual quicklooks from the existing proof artifacts:

   ```bash
   python brc-cases/wrf_quicklook.py check brc-cases/jan2013_basin_nam.case.yaml
   python brc-cases/wrf_quicklook.py render brc-cases/jan2013_basin_nam.case.yaml
   ```

   The quicklook helper verifies the `brc-tools` input manifest first, then
   reads existing WPS `met_em` files and archived `wrfout` files. It does not
   run WPS, `real.exe`, `wrf.exe`, Slurm, or new input staging. Generated PNGs
   go under `brc-cases/quicklooks/<case>/`, which is intentionally ignored by
   git. The workflow source is tracked in `jan2013_nam_workflow.mmd`.

`wrf_case.py` uses only the Python standard library. Because this checkout does
not currently carry a YAML dependency, the `*.case.yaml` format is a deliberately
small subset: top-level sections, two-space-indented keys, quoted strings,
integers, booleans, and bracketed lists. Avoid anchors, nested lists, and complex
YAML features.

The helper is a pre-run review gate, not a workflow engine. Real WPS, `real.exe`,
`wrf.exe`, scaling sweeps, and Slurm submission still require explicit human
approval.

`wrf_quicklook.py` is separate from `wrf_case.py` on purpose: the case validator
stays dependency-free, while quicklook rendering uses the local NetCDF and
plotting stack when visual QA is wanted.
