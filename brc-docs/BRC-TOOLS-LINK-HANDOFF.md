# Handoff To brc-tools: Tighten The WRF Link

Use this when opening a `brc-tools` session to close the remaining links between
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
| Fresh brc-tools contract | Gate 5 fresh NAM-only sidecars passed; the scratch `contract_<case>.json` remains canonical for new staging. |
| RAP source support | Branch `feat/wrf-rap-source` adds `rap_analysis` whole-file hourly planning/contract support and confirmed the 2013-02-02 12-18Z NCEI URLs. WRF-side Vtable and field proof remain open. |
| Practical testing | Now in `brc-wrf`; first row failed from WRF/run provenance, not input staging. No `brc-tools` code change is needed unless new staging is requested. |
| GEFS+NAM two-stream | Parked optional path. Still unproven through WPS/`real.exe`; do not mark it production-ready or treat it as the default alternate-forcing route. |

## Issues To Tighten In brc-tools

| Priority | Issue | Desired result |
| --- | --- | --- |
| 1 | Old proof scratch predates `contract_<case>.json`. | Docs explain that `brc-wrf` carries a reconstructed legacy NAM-only contract, while fresh staging emits the real sidecar. |
| 2 | The proof manifest includes both `nam_analysis` and partial `gefs_reforecast`, but WPS consumed NAM-only. | Avoid deriving NAM-only WPS truth from mixed-source proof manifest fields; use the contract/source intent instead. |
| 3 | brc-wrf now validates `owned_notch392_max` against `brc-knowledge`. | brc-tools docs should not suggest Slurm settings; they should point to `brc-wrf`/`brc-knowledge` for run profiles. |
| 4 | Fresh-stage acceptance has one Gate 5 pass. | Keep the reconstructed fallback until John explicitly accepts the retirement policy and compatibility story. |
| 5 | RAP source support exists, but WRF adequacy does not. | Keep RAP field/Vtable/run proof in `brc-wrf`; `brc-tools` should provide only source metadata, plans, manifests, contracts, and staging behavior. |
| 6 | GEFS+NAM needs a field-map handoff before WPS work if revived. | If two-stream becomes desired again, produce a compact list of GEFS variable-level tokens, Vtable implications, and missing fields NAM must fill. |

## Acceptance Criteria

- `brc-tools` docs clearly say: NAM-only is proven; RAP source support is a
  staging/contract proof only; GEFS+NAM is parked and not production-ready.
- `docs/WRF-INPUT-STAGING.md` points to the matching `brc-wrf` state playbook
  and first-case runbook.
- Fresh staging continues to emit `manifest_<case>.json` and
  `contract_<case>.json`.
- `brc-tools` does not grow WPS, WRF, or Slurm run-wrapper ownership.
- Practical scaling/memory results stay in `brc-wrf`; `brc-tools` only needs a
  doc sync if those results change the input-staging contract.
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
