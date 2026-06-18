# Handoff To brc-tools: Tighten The WRF Link

Use this when opening a `brc-tools` session to close the remaining seams between
input staging and this `brc-wrf` fork. It supersedes older untracked scratch
handoffs for current work.

## Paste Prompt

```text
You are in ~/gits/brc-tools, working on the WRF input staging side.

Read:
- docs/WRF-INPUT-STAGING.md
- docs/WRF-STAGING-STATE-PLAYBOOK.md
- ../brc-wrf/brc-docs/BRC-WRF-STATE-PLAYBOOK.md
- ../brc-wrf/brc-docs/BRC-WRF-FIRST-CASE.md
- ../brc-wrf/brc-cases/jan2013_basin_nam.case.yaml
- ../brc-wrf/brc-cases/jan2013_basin_nam.contract.json

Goal: tighten the brc-tools <-> brc-wrf handoff without running WPS, WRF, Slurm,
or heavy downloads unless explicitly approved.

Start with login-safe planning checks. Do not run manifest verification from a
login node; it hashes staged scratch artifacts and belongs in an approved
compute/batch context or on the appropriate transfer node.

python scripts/stage_wrf_inputs.py --plan --case jan2013_basin_gefs \
  --init-time "2013-01-31 00Z" --source nam_analysis --fxx-window 12,48

Then address the open link issues below in small commits.
```

## Current Truth

| Topic | Status |
| --- | --- |
| Proven run | NAM-only Jan-2013 Basin proof reached WPS, `real.exe`, `wrf.exe`, archive, and quicklooks. |
| Old scratch manifest | Verifies `28/28 OK`, but was written before fresh contract sidecars and includes partial GEFS files not consumed by WPS. |
| Current brc-wrf case | Points to a tracked reconstructed NAM-only contract so strict validation is clean. |
| Fresh brc-tools contract | Should still be the canonical sidecar for any new staging pass. |
| GEFS+NAM two-stream | Still unproven through WPS/`real.exe`; do not mark it production-ready. |

## Issues To Tighten In brc-tools

| Priority | Issue | Desired result |
| --- | --- | --- |
| 1 | Old proof scratch predates `contract_<case>.json`. | Docs explain that `brc-wrf` carries a reconstructed legacy NAM-only contract, while fresh staging emits the real sidecar. |
| 2 | The proof manifest includes both `nam_analysis` and partial `gefs_reforecast`, but WPS consumed NAM-only. | Avoid deriving NAM-only WPS truth from mixed-source proof manifest fields; use the contract/source intent instead. |
| 3 | brc-wrf now validates `owned_notch392_max` against `brc-knowledge`. | brc-tools docs should not suggest Slurm settings; they should point to `brc-wrf`/`brc-knowledge` for run profiles. |
| 4 | Fresh-stage acceptance is not yet cross-checked end-to-end against `brc-wrf` strict validation. | For the next approved fresh NAM-only stage, confirm `contract_<case>.json` lets `brc-wrf` strict validation pass without the reconstructed fallback. |
| 5 | GEFS+NAM needs a field-map handoff before WPS work. | If two-stream remains desired, produce a compact list of GEFS variable-level tokens, Vtable implications, and missing fields NAM must fill. |
| 6 | Several root handoff notes are stale/untracked in both repos. | Promote only current state into `docs/`; leave or delete scratch notes by explicit human decision. |

## Acceptance Criteria

- `brc-tools` docs clearly say: NAM-only is proven; GEFS+NAM is not.
- `docs/WRF-INPUT-STAGING.md` points to the matching `brc-wrf` state playbook
  and first-case runbook.
- Fresh staging continues to emit `manifest_<case>.json` and
  `contract_<case>.json`.
- `brc-tools` does not grow WPS, WRF, or Slurm run-wrapper ownership.
- No heavy download, DTN job, WPS run, WRF run, or Slurm submission happens
  without explicit approval.

## Useful Commands

```bash
cd ~/gits/brc-tools

python scripts/stage_wrf_inputs.py --plan --case jan2013_basin_gefs \
  --init-time "2013-01-31 00Z" --source nam_analysis --fxx-window 12,48

python scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json

pytest -q tests/test_wrf_staging.py
```

The `--verify-manifest` command is off-login because it hashes staged files.
The `--plan` command is login-safe metadata planning. The test suite can take
normal Python-test time. Do not submit DTN or WRF jobs from this handoff.
