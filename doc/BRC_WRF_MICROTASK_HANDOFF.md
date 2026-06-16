# BRC WRF Microtask Handoff

This is the WRF-run-side control board for a Codex session picking up the
remaining input-staging handshake, WPS/WRF proof, run-tuning, and documentation
refresh work.

It is intentionally a planning and routing artifact. It is not approval to run
DTN staging, WPS, `real.exe`, `wrf.exe`, Slurm submissions, scaling sweeps, or
large downloads.

The file includes `brc-tools` tasks because WRF cannot safely consume staged
forcing until the manifest/contract side is trustworthy. Keep implementation
batches repo-clean:

| Repo | Owns | Do not do there |
| --- | --- | --- |
| `brc-wrf` | WRF source, WPS/WRF consumption docs, case manifests, validators, run templates, benchmark plans, WRF-output quicklooks. | NWP downloader or GRIB staging logic. |
| `brc-tools` | GRIB download/staging, manifests, contracts, token checks, input quicklooks. | WPS, `real.exe`, `wrf.exe`, or WRF run Slurm profiles. |
| `brc-knowledge` | Canonical CHPC node, storage, scheduler, proxy, and validated script facts. | Repo-local code or case manifests. |

## Codex Cold Start

Start in `~/gits/brc-wrf` and keep the first pass small:

1. `git status --short --branch --untracked-files=all`
2. `sed -n '1,180p' AGENTS.md`
3. `sed -n '1,180p' doc/BRC_WRF_MICROTASK_HANDOFF.md`
4. `sed -n '1,140p' brc-docs/BRC-WRF-STATE-PLAYBOOK.md`
5. `sed -n '1,180p' brc-docs/BRC-WRF-FIRST-CASE.md`
6. `sed -n '1,130p' ../brc-tools/docs/HANDOFF-TO-BRC-WRF.md`

Then read only the task-owned files named below. Do not broad-scan WRF source
or load high-token scripts until `rg` points to a specific function, test, or
doc section.

Cheap checks that are allowed from this repo:

```bash
python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/jan2013_basin_gefs/manifest_jan2013_basin_gefs.json

python brc-cases/wrf_case.py validate \
  brc-cases/jan2013_basin_nam.case.yaml --strict-files

git diff --check
```

Do not run WPS, `real.exe`, `wrf.exe`, `sbatch`, scaling sweeps, or large
download/stage commands without explicit human approval. On CHPC login nodes,
limit work to light inspection, small Python checks, docs, and local tests.

## Progress Survey

| Area | Current state | Evidence or next check |
| --- | --- | --- |
| NAM-only Jan-2013 proof | Proven through WPS, `real.exe`, `wrf.exe`, archive, and no-run quicklooks. | `brc-docs/BRC-WRF-FIRST-CASE.md`; `brc-cases/wrf_case.py validate ... --strict-files`; `brc-cases/wrf_quicklook.py check ...`. |
| Input contract handshake | Old proof scratch predates fresh sidecars; `brc-wrf` carries a reconstructed NAM-only contract for strict validation. `brc-tools` manifest schema v2 is additive for this repo because `brc-wrf` reads the contract sidecar, not manifest `staged_files`. | Fresh `brc-tools` staging should later emit `contract_<case>.json`; validate it before retiring the reconstructed fallback. |
| GEFS+NAM two-stream | Not proven. Treat as a WPS/field-coverage design task until approved WPS evidence exists. | `../brc-tools/docs/WRF-GEFS-NAM-FIELD-MAP.md`; stop before `real.exe`. |
| WRF run tuning | Not benchmarked. Current max owned-node profile is a safe high-power default, not the efficiency knee. | Prepare 16/28/56 task and memory tables; no `sbatch` without approval. |
| Docs/router state | This file is the detailed queue; `AGENTS.md` and `doc/BRC_WRF_HANDOFF.md` should stay short. | Update detailed counts here, then leave only pointers in router docs. |

## Current Countdown

Tracked remaining microtasks from the `brc-tools` handoff and WRF run side: 11.
The 2026-06-16 `brc-tools` hygiene pass closed #4, #5, #6, #11, #12, and
#31 upstream. This `brc-wrf` caretaker pass closes #32 by keeping current
staging-doc and scratch-layout references wired here.

| Bucket | Count | Tasks | Meaning |
| --- | ---: | --- | --- |
| Codex can do, then human reviews | 3 | #7, #10, #13 | Remaining `brc-tools` staging design/test work. Real staging or large transfer proof stays approval-gated. |
| Codex plus human decision/review | 1 | #16 | Codex can prepare design/docs; human decides whether to pursue the two-stream proof. |
| Human-only or human-led | 5 | #17, #21, #23, #24, #33 | WPS inspection, domain/geog judgment, DTN submission, helpdesk/proxy answer, retention/promotion decision. |
| brc-wrf run-tuning, approval-gated | 2 | #26, #27 | Codex can draft scripts/tables, but actual WRF benchmark runs need approval. |

Practical-test countdown:

| Step | Gate | Can a Codex session advance it now? | Stop point |
| --- | --- | --- | --- |
| 1 | Keep NAM-only baseline truth clean in docs and validators. | Yes. | No WPS/WRF claims beyond current evidence. |
| 2 | Keep the merged `brc-tools` hygiene reflected in run-side docs. | Yes, docs/checks only. | No WRF-side change needed for additive manifest schema v2. |
| 3 | Prove a fresh NAM-only `contract_<case>.json` validates in `brc-wrf`. | Partly. Codex can plan and wire the case file; fresh staging needs DTN approval if not already present. | `wrf_case.py validate --strict-files` passes against the fresh contract. |
| 4 | Decide whether GEFS+NAM two-stream is worth pursuing now. | Codex can prepare the design table; human chooses the science path. | Do not run WPS yet. |
| 5 | If two-stream is approved, build/select `Vtable.GEFS` and ungrib/metgrid to inspect fields. | Partly. Prep is Codex-friendly; WPS execution is approval-gated. | Stop before `real.exe`; show `met_em` field list and warnings. |
| 6 | Run practical WRF setting tests: scaling and memory on `notch392`. | Codex can render scripts and result tables. | No `sbatch` or WRF run without explicit approval. |
| 7 | Refresh docs all round after evidence changes. | Yes. | Update only facts supported by commands, logs, or accepted human decisions. |

## Recommended Next No-Run Batch

The `brc-tools` hygiene batch is merged upstream. Keep the next work here in
the WRF-run-side lane unless a separate `brc-tools` session is opened.

The current John/Michael no-run handout is
`brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md`. It packages the first contract
validation checklist, settings map, approval gates, and blank result tables for
pair-programming without WPS/WRF execution.

### Lane 1: Bang Out Here In `brc-wrf`

| Order | Task | Why first | Evidence to leave |
| ---: | --- | --- | --- |
| 1 | Fresh NAM-only contract validation checklist. | Makes Goal A actionable the moment a fresh `contract_<case>.json` exists. | Exact manifest/contract paths and `wrf_case.py validate --strict-files` command. |
| 2 | #16 GEFS+NAM two-stream design checklist. | Lets a future approved WPS pass stop at field evidence instead of improvising. | Expected GEFS/NAM field split, `Vtable.GEFS` implications, and `real.exe` stop point. |
| 3 | #26/#27 benchmark table templates. | Prepares scaling/memory work without consuming allocation time. | Empty result table with tasks, memory, wall time, status, archive, and recommendation columns. |
| 4 | #21 domain/geog evidence pointer. | Separates syntax checks from human domain judgment. | Exact doc/namelist paths to inspect; no claim of fresh scientific approval. |

### Lane 2: Future `brc-tools` Batch

| Order | Task | Why next | Evidence to leave |
| ---: | --- | --- | --- |
| 1 | #7 Multi-member staging proof. | Pressure-tests per-member layout before ensemble WRF use. | Mocked or small proof evidence; real transfer only after approval. |
| 2 | #10 Operational GEFS post-2017 path. | Needed for recent cases, not the Jan-2013 reforecast proof. | Reused staging abstractions and tests. |
| 3 | #13 Pin `wps_variable_levels` per data-year if token evidence supports it. | Prevents silent reforecast-token drift across 2000-2019. | Evidence-backed token map or explicit decision not to split. |

Recently closed upstream in `brc-tools`: #4 token preflight, #5
`obs_sanity_overlay` test, #6 cached `.idx` lead-time labeling/schema v2, #11
manifest byte/time provenance, #12 240 h boundary behavior, and #31 wishlist
pointer. Closed here: #32 cross-repo doc sync.

### Lane 3: Human Gates

| Decision | Needed before | Default stop point |
| --- | --- | --- |
| Whether GEFS+NAM two-stream is scientifically needed now. | Any WPS two-stream proof work. | Keep improving NAM-only repeatability. |
| Whether to refresh the NAM-only staged contract. | Retiring `brc-cases/jan2013_basin_nam.contract.json`. | Validate reconstructed contract only. |
| Whether to spend allocation on scaling/memory sweeps. | Any `sbatch`, `real.exe`, or `wrf.exe` benchmark. | Render/check templates only. |
| Whether to promote staged inputs. | Copying scratch inputs to durable group storage. | Inventory paths and run manifest verification only. |

## WRF-Side No-Run Templates

### Fresh NAM-Only Contract Validation

Use this only after fresh `brc-tools` staging has produced a real sidecar:

```bash
python ../brc-tools/scripts/stage_wrf_inputs.py --verify-manifest \
  /scratch/general/vast/$USER/wrf_inputs/<case>/manifest_<case>.json

# Then point a review copy of the case yaml at:
# /scratch/general/vast/$USER/wrf_inputs/<case>/contract_<case>.json
python brc-cases/wrf_case.py validate <case>.yaml --strict-files
```

Acceptance: strict validation passes against the fresh `contract_<case>.json`.
Only then consider retiring `brc-cases/jan2013_basin_nam.contract.json`.

### GEFS+NAM Two-Stream Proof Prep

Prepare the design before any approved WPS execution:

| Item | Expected handling |
| --- | --- |
| GEFS pressure fields | Include both `_pres` and `_pres_abv700mb` tokens for `hgt`, `tmp`, `ugrd`, `vgrd`, and `spfh`; humidity is specific humidity, not RH. |
| GEFS near-surface fields | Map `pres_msl`, `pres_sfc`, `hgt_sfc`, `tmp_2m`, `spfh_2m`, `tmp_sfc`, `ugrd_hgt`, and `vgrd_hgt`. |
| NAM filler fields | Keep NAM responsible for `LANDSEA`, `SKINTEMP`/SST, `SNOWH`, and standard 4-layer soil unless a reviewed Vtable proves otherwise. |
| WPS stream settings | Use separate ungrib streams and `metgrid fg_name = 'GEFS','NAM'`; two-stream interval is expected to be `10800`. |
| Stop point | After metgrid, show `met_em` field list, `num_metgrid_levels`, and warnings. Do not run `real.exe` without a new approval. |

### Scaling And Memory Result Tables

Use these tables after a human approves benchmark submissions.

| Tasks | Memory request | Wall time | Sim hours | Wall time per sim hour | WRF marker | Archive path | Notes |
| ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| 16 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| 28 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| 56 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

| Run | Memory request | Peak memory evidence | WRF marker | Archive path | Recommendation |
| --- | ---: | --- | --- | --- | --- |
| Baseline | `900G` | TBD | TBD | TBD | TBD |
| Right-size candidate | TBD | TBD | TBD | TBD | TBD |

### Wrapper Robustness Checklist

Keep these checks attached to any future maintained run wrapper:

- Treat WRF success, `real.exe` success, archive completeness, and Slurm state as
  separate facts. Required markers are `SUCCESS COMPLETE REAL_EM INIT` and
  `SUCCESS COMPLETE WRF`.
- Archive WRF colon filenames as local paths, for example
  `rsync -av ./wrfout_d0* ...`, so `rsync` does not parse the timestamp colon as
  a remote host separator.
- Do not use `srun --jobid` probes inside a fully occupied WRF allocation; use
  `squeue`, exact logs, success markers, and on-disk artifacts instead.

## Parked For Human Review Or Approval

Do not lose sight of these. They are not good login-node free-running tasks.

| Task | Owner | Why parked | What Codex can prepare | Human decision or action |
| --- | --- | --- | --- | --- |
| Fresh NAM-only contract validation, handoff Goal A | `brc-tools` + `brc-wrf` | Needs fresh `contract_<case>.json`; may require DTN staging if not already on scratch. | Plan command, case-yaml patch, validation checklist. | Approve or provide fresh stage; decide when reconstructed fallback can retire. |
| #16 GEFS+NAM two-stream proof | `brc-wrf` with brc-tools context | WPS work and eventual `real.exe` are approval-gated; science value must be chosen. | Draft `Vtable.GEFS` mapping and field-source table from `WRF-GEFS-NAM-FIELD-MAP.md`. | Decide whether two-stream is needed now. |
| #17 Ungrib staged reforecast and inspect fields | Human-led WPS proof | Runs WPS tooling and inspects meteorological field coverage. | Build checklist and expected field list. | Approve WPS/ungrib execution; review missing fields. |
| #21 Confirm geogrid, `geog_data_path`, and Basin domain | Human-led review | This is scientific/domain judgment, not just syntax. | Collect exact namelist paths and current expected values. | Confirm the domain/geog setup is the intended baseline. |
| #23 Full DTN stage | Human-led CHPC transfer | Multi-GB stage belongs on `notchpeak-dtn`, not login nodes. | Check script path and render plan; verify command shape. | Approve `sbatch scripts/stage_inputs.dtn.slurm` or equivalent. |
| #24 Compute-node internet/proxy answer | Human-led CHPC policy | Requires helpdesk or CHPC policy confirmation. | Draft the question and place to record answer in `brc-knowledge`. | Ask helpdesk and accept the canonical answer. |
| #26/#27 Scaling and memory benchmarks | `brc-wrf` run tuning | Real WRF runs consume allocation time. | Render scripts, result table template, archive checklist. | Approve run submissions and choose task/memory sweep. |
| #33 Retention/promotion | Human-led storage policy | Scratch purges; durable promotion consumes group storage. | Inventory current paths and manifest verification command. | Decide whether to promote staged inputs to `lawson-group6`. |

## Remaining Microtask Table

| Task | Label | Repo | Current classification | Next Codex action | Human review or stop point |
| --- | --- | --- | --- | --- | --- |
| #7 | Multi-member staging proof | `brc-tools` | Codex can partially do | Design per-member layout and mocked manifest aggregation. | Any real multi-member stage needs transfer approval. |
| #10 | Operational GEFS post-2017 path | `brc-tools` | Codex can do after design | Reuse staging abstractions and tests. | Review source naming and scope before live use. |
| #13 | Pin `wps_variable_levels` per data-year if needed | `brc-tools` | Codex can do after evidence review | Add structure only if token evidence supports it. | Human/science review if year differences affect WPS. |
| #16 | GEFS+NAM Vtable and two-stream WPS proof | `brc-wrf` | Codex plus human | Draft Vtable/field-source design; no execution. | Approval before WPS and before `real.exe`. |
| #17 | Ungrib staged reforecast and inspect fields | `brc-wrf` | Human-led | Prepare expected field checklist. | WPS execution and field review. |
| #21 | Confirm geogrid/path/domain | `brc-wrf` | Human-led | Point to exact namelist and runbook evidence. | Human confirms domain/geog baseline. |
| #23 | Full DTN stage | `brc-tools` | Human-led | Verify script and plan command only. | Approve DTN `sbatch`. |
| #24 | Compute-node internet/proxy answer | `brc-knowledge` | Human-led | Draft helpdesk question and doc destination. | Human obtains/records answer. |
| #26 | Scaling benchmark | `brc-wrf` | Approval-gated run tuning | Prepare scripts and result table. | Approve WRF submissions. |
| #27 | Memory benchmark | `brc-wrf` | Approval-gated run tuning | Prepare memory sweep and accounting table. | Approve WRF submissions. |
| #33 | Retention/promotion | `brc-tools` + `brc-wrf` + storage | Human-led | Inventory scratch and durable target commands. | Human decides what to promote. |

## Recently Closed Microtasks

| Task | Close evidence |
| --- | --- |
| #4 | `brc-tools` merged offline-tested token preflight; live S3 list-URL format remains a first-live-run caveat. |
| #5 | `brc-tools` added the synthetic `obs_sanity_overlay` test. |
| #6 | `brc-tools` manifest schema v2 labels cached lead-time limitations/additions; additive for `brc-wrf`. |
| #11 | `brc-tools` records manifest byte/time provenance. |
| #12 | `brc-tools` pins the 240 h boundary behavior as warn+partial. |
| #31 | `brc-tools` added the `WISHLIST-TASKS.md` pointer. |
| #32 | `brc-wrf` docs point to current `../brc-tools/docs/WRF-INPUT-STAGING.md`, scratch layout, and handoff files; link-check passes with binary files ignored. |

## Documentation Refresh Map

Update docs where the evidence belongs, not all in one place.

| Evidence changes | Primary doc | Secondary pointer |
| --- | --- | --- |
| Remaining microtask counts or routing changes | `doc/BRC_WRF_MICROTASK_HANDOFF.md` | `AGENTS.md` only as a short router |
| NAM-only run proof facts | `brc-docs/BRC-WRF-FIRST-CASE.md` | `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` |
| Case manifest or render-only Slurm review | `brc-cases/README.md` | `doc/BRC_WRF_HANDOFF.md` |
| brc-tools staging behavior, manifests, contracts | `../brc-tools/docs/WRF-INPUT-STAGING.md` | `brc-docs/BRC-WRF-FIRST-CASE.md` |
| GEFS+NAM field split and Vtable design | `../brc-tools/docs/WRF-GEFS-NAM-FIELD-MAP.md` until WPS proof exists | This microtask board and `brc-docs/BRC-WRF-FIRST-CASE.md` |
| CHPC node, storage, proxy, Slurm truth | `../brc-knowledge/scholarium/reference-base/resources/` | BRC-WRF docs should point, not duplicate |
| Benchmark results | `brc-docs/BRC-WRF-STATE-PLAYBOOK.md` | `brc-docs/BRC-WRF-FIRST-CASE.md` if runbook changes |

## Standing Preferences For The Next Session

- Treat this as a large upstream-style WRF tree with a thin BRC-local layer.
- Prefer docs, validators, and focused tests before any run-scale workflow.
- Keep `brc-tools`, `brc-wrf`, and `brc-knowledge` ownership separate.
- Leave breadcrumbs: command, evidence, owner repo, and stop point.
- If a task starts needing WPS, WRF, Slurm, large downloads, or CHPC policy,
  stop and park it in the human/approval table instead of improvising.
- Keep `AGENTS.md` as a router. Put detailed state here or in the workflow doc
  that owns the evidence.
