# BRC WRF State Playbook

Short print-oriented explanation for John/JRL and Michael. It describes where
the current `brc-wrf` fork fits, what is proven, and what should happen next.

## One-Sentence State

We have a BRC-local review layer around WRF 4.8.0, and one NAM-only Jan-2013
Basin case is proven through `brc-tools` input staging, WPS, `real.exe`,
`wrf.exe`, archive checks, and no-run quicklooks.

## Mental Model

| Layer | Owns | Does not own |
| --- | --- | --- |
| `brc-tools` | Downloading/staging WRF-ready GRIB files, manifests, contracts, input quicklooks. | WPS, `real.exe`, `wrf.exe`, Slurm run wrappers. |
| `brc-wrf` | WRF source, WPS/WRF consumption docs, case manifests, validators, Slurm rendering, WRF-output quicklooks. | NWP downloader logic. |
| `brc-knowledge` | Canonical CHPC hardware, storage, scheduler, and validated example Slurm scripts. | Repo-local code or case manifests. |

The AI tooling is useful because it keeps these contracts visible and checks
cheap facts before expensive runs. It is also another layer to audit, so every
AI-assisted step should leave a small, readable breadcrumb: command, evidence,
owner repo, and stop point.

## Who Can Understand This Today?

| Audience | Current readiness | What still feels hard |
| --- | --- | --- |
| John/JRL | High enough to audit and steer science decisions. | The GEFS+NAM two-stream path still needs WPS/`real.exe` proof before it is science-ready. |
| Michael/new developer | Medium if starting from the reading packet below. | WRF requires both software-install knowledge and meteorological forcing knowledge; the repo split must be read first. |
| Future AI agent | Medium-high for no-run review tasks. | It must not confuse old NAM-only proof artifacts with unproven GEFS+NAM workflow. |

## Where We Are

| Area | Status |
| --- | --- |
| Fork orientation | Usable. `README.md`, `AGENTS.md`, and `doc/BRC_FORK_GUIDE.md` explain the local layer. |
| CHPC posture | Usable. Canonical CHPC facts live in `brc-knowledge`; this repo points there. |
| First case | Proven NAM-only path for Jan 31-Feb 2 2013, d01/d02 Basin nest. |
| Case review | Usable. `brc-cases/wrf_case.py` validates metadata and renders Slurm text only. |
| Visual QA | Usable. `brc-cases/wrf_quicklook.py` renders five no-run PNGs from existing proof artifacts. |
| Slurm profile | Aligned to max owned-node profile: `lawson-np`, `notch392`, 1 node, 56 tasks, `900G`, `srun --mpi=pmi2`. |
| GEFS+NAM | Not proven. Treat as a design/proof task, not a working production method. |

## Where We Should Go Next

| Order | Next move | Stop point |
| --- | --- | --- |
| 1 | Review the quicklook PNGs with meteorological eyes. | Decide whether the NAM-only proof looks physically plausible enough to keep as baseline. |
| 2 | Commit this docs/validator/quicklook checkpoint. | Branch has a clean, reviewable milestone. |
| 3 | Push or otherwise account for the current local commit stack. | Remote and local state are not ambiguous. |
| 4 | Decide whether GEFS+NAM is still needed for the next science question. | If yes, draft the two-stream WPS proof; if no, improve NAM-only repeatability. |
| 5 | For any real run, render Slurm and inspect it against `brc-knowledge` before `sbatch`. | Human approval only after the rendered script matches current CHPC truth. |

## Reading Packet

Read these in order for a milestone review:

1. `brc-docs/BRC-WRF-MICHAEL-PRACTICAL-PACKET.md` for a pair-programming
   walkthrough.
2. `brc-docs/BRC-WRF-FORK-HIGHLIGHTS.md`
3. `brc-docs/BRC-WRF-FIRST-CASE.md`
4. `brc-cases/README.md`
5. `brc-docs/BRC-WRF-USAGE.md`
6. `../brc-tools/docs/WRF-STAGING-STATE-PLAYBOOK.md`
7. `brc-docs/BRC-TOOLS-LINK-HANDOFF.md` if opening a `brc-tools` session
8. `../brc-knowledge/scholarium/reference-base/resources/chpc-team-resource-inventory.md` sections 1-3 and Q1
9. `../brc-knowledge/scholarium/reference-base/resources/wrf-on-chpc-quickstart.md` sections 2, 3, and 8

For Michael, start with items 1, 3, 4, and 6 before the full CHPC resource
inventory. For John, start with items 2, 3, 6, 8, and 9; add item 7 when the
next task is in `brc-tools`.

## Maximum Owned-Node WRF Profile

Use this when the goal is a high-powered, non-preemptible single WRF run on the
team-reserved node:

| Slurm setting | Value | Source |
| --- | --- | --- |
| account | `lawson-np` | `brc-knowledge` resource inventory |
| partition | `lawson-np` | `brc-knowledge` resource inventory |
| node | `notch392` | preferred WRF workhorse |
| nodes | `1` | avoids asymmetric two-node WRF costs |
| tasks | `56` | all Slurm cores on `notch392` |
| memory | `900G` | reserves most of the ~996 GiB node |
| launcher | `srun --mpi=pmi2` | validated Intel MPI fix |
| preemptible? | no | owned partition |

Do not move to preemptible Granite or multi-node Notchpeak until the case needs
more than one `notch392` can provide.
