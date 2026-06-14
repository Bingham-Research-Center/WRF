# BRC WRF Case Scaffolds

This directory holds BRC-local case manifests and the cheap helper used to
review them before any WPS, WRF, or Slurm work starts.

The checkpoint is intentionally small:

1. Write or edit a `*.case.yaml` file.
2. Validate the schema and cheap local facts:

   ```bash
   python brc-cases/wrf_case.py validate brc-cases/jan2013_basin_nam.case.yaml
   ```

3. Use stricter file checks only after inputs and run directories exist:

   ```bash
   python brc-cases/wrf_case.py validate --strict-files brc-cases/jan2013_basin_nam.case.yaml
   ```

4. Render the Slurm script for review. This writes text only; it does not call
   `sbatch`.

   ```bash
   python brc-cases/wrf_case.py render-slurm brc-cases/jan2013_basin_nam.case.yaml
   ```

`wrf_case.py` uses only the Python standard library. Because this checkout does
not currently carry a YAML dependency, the `*.case.yaml` format is a deliberately
small subset: top-level sections, two-space-indented keys, quoted strings,
integers, booleans, and bracketed lists. Avoid anchors, nested lists, and complex
YAML features.

The helper is a pre-run review gate, not a workflow engine. Real WPS, `real.exe`,
`wrf.exe`, scaling sweeps, and Slurm submission still require explicit human
approval.
