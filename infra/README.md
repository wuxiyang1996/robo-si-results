# Infrastructure and contributor guide

<!-- current-retrieval-registration -->
Current H1/M1/M3 registrations: [overview](planning/task-families-en.md) / [中文](planning/task-families.md) / [JSON](planning/current-task-registry.json). H1 has 22 selected independent tasks: 20 split registrations plus two new operations; all legal complete solutions are accepted. M1 registers 9 cases, including its original task. M3 registers 6 cases, including its original task; current load capability requires verification.
<!-- /current-retrieval-registration -->

## M1 extension design · 2026-10-27

[中文任务族设计](planning/m1-extension/README.md) · [English family design](planning/m1-extension/README-en.md) · [Machine-readable design](planning/m1-extension/task-design.json). One M1 family: direct retrieval / seek help × five-finger dexterous / three-finger / wheeled embodiment × required designated-manipulator transfer Y/N = 12 candidate cells. N permits help; Y requires public transfer and final delivery constraints. Keep world, helpers and tools fixed in Y/N pairs. Start with the three-finger four-cell slice; difficulty is a separate annotation. Legacy 01–08 are scene recipes/controls, cart recipe 04 is deferred, and four infeasibility controls retain physical all-robot Q exit. Design only, zero new simulations; original M1 evidence, scores and 14-task counts are unchanged.

## H1 extension design · 2026-10-27

[中文任务卡](planning/h1-extension/README.md) · [English task cards](planning/h1-extension/README-en.md) · [Machine-readable design](planning/h1-extension/task-design.json). Intended support: five platforms, six configurations, including Go1 with an undecided lightweight arm and gripper. Eight task families cover tool combinations, ramps, same-color distractors, load limits and whole-body manipulation; four infeasibility controls require physical exit to Q. Design only, no new simulation or admission claim; excluded from the established 14-task counts.

Current retrieval families: [H1 / M1 / M3](planning/task-families-en.md) / [中文](planning/task-families.md). H1 self-climbing, M1 target transfer/cabinet delivery, and conditional lightweight-partner M3 are separate. The former H1 cooperative supplement is superseded; new M3 lifting requires a current 2 kg capability/asset audit.

<!-- reference-design-index -->
**14/14 scoped reference execution witnesses; 14 reference design documents.** [参考解与设计总览 / Reference design index](reference-designs-zh.html). Sandbox runtime acceptance and formal admission remain separate; original scores are unchanged.
<!-- /reference-design-index -->


<!-- unified-14-start -->
## Unified 14-task inventory

The [inventory](website-completion.json) tracks **14 task projects: 14 scoped reference/design deliveries, 0 in progress, 14 with published materials (including 1 experimental candidate), and 0 formal admissions**. There are 10 existing GitHub task releases and 3 additional HF packet versions. H1 now has a published scoped packet; Sokoban remains an experimental candidate with `task_success=null`.

[DiskFlip 中文](task-disk-flip-zh.html) / [English](task-disk-flip-en.html) · [Sokoban 中文](task-sokoban-zh.html) / [English](task-sokoban-en.html) · [All 14 planning entries](planning/INVENTORY.md).

The original 12-task cohort has 193 ordered contract actions with pending joint physical mappings. DiskFlip has two measured mappings (26/27 segments); Sokoban has one measured mapping (76 segments). These are different units and are not summed. No new simulation or formal sign-off is claimed.
<!-- unified-14-end -->

The current minimum design gate is demonstrated **high-level → low-level → trajectory refinement plus one scoped, generated continuous end-to-end success witness**. It does not require solving all random states, arbitrary skill composition or a general rolling planner. [Mapping review for the original 12-task cohort](planning/hierarchical-evaluation/READINESS.md): existing success candidates are selected; detailed action/segment mappings and generation provenance still need review. Original scores and H1 status are unchanged.

[Layered status for all 14 tasks](status-en.html#layered-progress) separates scoped witnesses, action mappings, unknown instance checks and formal admission. Original 12-task evidence remains explicitly labeled as a historical cohort.

[Skill evidence registry: H2, H5, Hanoi and Assembly](planning/skill-evidence/README.md) binds existing reports to 19 skill contracts and preserves tested joint configurations, checkpoint scope, repeats and failures. Source JSON copies are hash-checked and portable for review; no new physics runs, continuous applicability envelopes or admission changes are claimed.

## Layered planning and acceptance policy · 2026-10-26

A complete solution for every random instance is **not** a prerequisite. Deliver high-level plans, selected skills and constraints, key states and feasibility-check results. Use a finite predeclared set of complete references at task level, validate skill applicability and transitions, screen instances within budgets, and generate local trajectories only when executing.

Record `witnessed_full`, `screen_pass`, `unknown` and `rejected` separately. Screening passes do not count as full success; search failure or budget exhaustion does not prove infeasibility. Preserve all prescribed benchmark draws and results. Existing successful/failed runs, unsigned reviews, finite acceptance cohorts and agent grading requirements remain separate and are not automatically changed.

[Design principles (中文)](task-design-zh.html#hierarchical-planning) · [English](task-design-en.html#hierarchical-planning) · [Acceptance standard (中文)](acceptance-zh.html#screening) · [English](acceptance-en.html#screening) · [Versioned policy](planning/acceptance-policy.json) · [Plans for all 14 tasks](planning/INVENTORY.md). The policy defines evidence requirements; feasibility solvers and budget scheduling are not implemented by these documents.

[H1 layered evidence workflow](planning/h1/README.md) now imports existing full witnesses, records observed skill/key-state evidence, and provides a budgeted evidence-screening CLI. The original three draws are retained as two exact full witnesses and one unknown. Missing dynamic checks remain unknown; physics stays paused and formal admission is unchanged.

Pages for people who add new tasks to Embodied Terminal-Bench (robo-si). Open the HTML files in a browser; no build step is needed. The directory currently contains 45 HTML pages: eight core topics in English and Chinese, task reports, deployment guides and landing pages. Keep both languages in sync when editing task descriptions.

Open [index.html](index.html) for the default Chinese home page; switch to English from the navigation. All 14 tasks have scoped reference/design materials and published packets. The [completion overview](status-en.html#completion) and [Chinese overview](status-zh.html#completion) cover all 14; [website-completion.json](website-completion.json) records scopes and source hashes.

| Page | English | Chinese | What it covers |
| --- | --- | --- | --- |
| Home | [contribute-en.html](contribute-en.html) | [contribute-zh.html](contribute-zh.html) | Overview and page map, current tasks, contribution process, submission checklist, roles and licensing |
| Windows / Linux deployment | [deployment-en.html](deployment-en.html) | [deployment-zh.html](deployment-zh.html) | Verified full-archive downloads, hashed dependency locks, portable runtime commands and measured per-OS results; independent-machine acceptance remains separate |
| Task design | [task-design-en.html](task-design-en.html) | [task-design-zh.html](task-design-zh.html) | The eleven hard requirements; scene and instruction, simulators and assets, randomisation, three difficulty layers, subtasks, corner cases, sensors and tools, scoring and protection material, self-check, task card and machine-readable spec |
| Acceptance | [acceptance-en.html](acceptance-en.html) | [acceptance-zh.html](acceptance-zh.html) | Reference expert solution, official trajectories and subgoal scenarios, manual feasibility verification, verifier validity, the human check of the task, the automatic check pipeline |
| Sandbox | [sandbox-en.html](sandbox-en.html) | [sandbox-zh.html](sandbox-zh.html) | The four sandbox requirements, structure and deployment, isolation and perception, tools and skills, the uneditable world, feedback, the agent side, multiple robots and realistic execution |
| Scoring | [verifier-en.html](verifier-en.html) | [verifier-zh.html](verifier-zh.html) | Where the verifier lives, stage predicates, scoring rules, automatic scoring rules, monitors, fabrication checks, attacks and defences |
| Protocol | [protocol-en.html](protocol-en.html) | [protocol-zh.html](protocol-zh.html) | Budgets, delivery snapshots, reporting, three repeats and statistics, baselines, versions, leakage |
| Status | [status-en.html](status-en.html) | [status-zh.html](status-zh.html) | What the shared runtime and the H1 reference implementation do, the H1 task's progress, verification records, the merged to-do list |
| Glossary | [glossary-en.html](glossary-en.html) | [glossary-zh.html](glossary-zh.html) | Glossary, common questions with one-line answers, the Terminal-Bench and EmbodiedSWE comparison |
| H2 layer 1 closeout report | [task-h2-en.html](task-h2-en.html) | [task-h2-zh.html](task-h2-zh.html) | Published first-layer reference report: 5/5 full runs, 20/20 standalone subtasks, 14/15 repeats, 11/11 integration checks; videos, retained failure and portable evidence |
| M1 layer 1 reference release | [task-m1-en.html](task-m1-en.html) | [task-m1-zh.html](task-m1-zh.html) | Completed privileged CPU reference: 13 successes / 8 seeds, 3/3 strict repeats, published videos and review workbench |
| M3 functional reference release | [task-m3-en.html](task-m3-en.html) | [task-m3-zh.html](task-m3-zh.html) | Normal-start 2/2, score 1.0, fixed box-supported picking and complete delivery; raw evidence, videos and pending review |
| M2 layer 1 reference release | [task-m2-en.html](task-m2-en.html) | [task-m2-zh.html](task-m2-zh.html) | Fixed 0.25 kg: 3/3 bounded privileged references + one ordinary RPC replay; full-wall videos, evidence and pending human review |
| H4 layer 1 release | [task-h4-en.html](task-h4-en.html) | [task-h4-zh.html](task-h4-zh.html) | Published first-layer reference materials: 11/14 full runs, failures retained, historical appendix and pending review |
| H5 layer 1 release | [task-h5-en.html](task-h5-en.html) | [task-h5-zh.html](task-h5-zh.html) | Published reference materials: full runs 5/5, standalone subtasks 20/20, videos, review status and offline packet |
| Tabletop release | [tabletop-en.html](tabletop-en.html) | [tabletop-zh.html](tabletop-zh.html) | Published Hanoi 3/4/5 disks and Assembly layer 1: videos, scoring, reproduction, release download and pending human review |
| Proposal (in `doc/`) | [v6 English](../doc/self-modeling-benchmark-v6-en.html) | [v6 Chinese](../doc/self-modeling-benchmark-v6-zh.html) | The research proposal: research questions, evaluation tracks, executors and skill distillation, difficulty, task progress, experiments, roadmap; it links here for every specification |

Each topic is covered on one page only and linked from the others. The specification pages contain no implementation status; everything about where H1 stands is on the status page. The research proposal [v6](../doc/self-modeling-benchmark-v6-en.html) ([Chinese](../doc/self-modeling-benchmark-v6-zh.html)) uses the same navigation bar and stylesheet and supersedes v5 where they differ; these pages also document the implemented H1 sandbox ([`humanoid/g1_support_retrieval/sandbox`](../humanoid/g1_support_retrieval/sandbox/README.md)).

## Shared sandbox runtime

The code every task sandbox uses lives in [`sandbox/`](sandbox/ONBOARDING.md): the RPC protocol and agent SDK (`g1sandbox`), the trusted worker (`server.py`), the launcher with sealed scenarios, delivery snapshots and content-addressed bundles (`launcher.py`), the command channel for one or several robots (`world.py`), the G1 sensor suite (`sensors.py`), the chunked state-log format (`statelog.py`), the monitors (`monitors.py`), the run-level verifier wrapper (`verifier.py`), the agent container (`container/`) and the admission-record schema (`records.py`). A task sandbox keeps only its scene, world adapter, recording rows, monitor profile and stage scorer. [ONBOARDING.md](sandbox/ONBOARDING.md) gives the module contracts and the checklist for putting a new task on the runtime.

```powershell
cd D:\rsi_vla\robo-si
$py = 'D:\rsi_vla\genesis_env\Scripts\python.exe'
& $py -m unittest infra.sandbox.tests.test_runtime   # runtime tests
& $py -m infra.sandbox.records                       # admission gates of every task (admission.json)
```

Each task's `admission.json` (schema `infra-admission/1`) records the 15 standard gates, task-specific items and pending decisions, with evidence paths relative to the task directory.

## H5 layer 1 reference-data release

The author approved the current first-layer pages and evidence on 2026-10-23. [Chinese](task-h5-zh.html) · [English](task-h5-en.html) · [Release and offline evidence packet](https://github.com/wuxiyang1996/robo-si/releases/tag/h5-layer1-20261023). The packet contains 5/5 full references, 20/20 standalone subtasks, original recordings, the new camera views and frozen reproduction sources. Main-benchmark admission remains pending.

For local video playback and frozen reproduction sources, download the complete offline packet from the release and open `workspace/infra/task-h5-zh.html` or `task-h5-en.html`. The Git repository contains the review pages and lightweight evidence; the private dataset hosts the recordings.

The H5 review pages now live in this local infra directory; their recordings and frozen evidence resolve to `C:/Users/wuxiy/rsi_releases/h5_release_artifact_20261023/workspace/`. Keep that packet in place for these local links. GitHub uses the portable release links above.

## Tabletop reference-data release (2026-10-23)

[Chinese overview](tabletop-zh.html) · [English overview](tabletop-en.html) · [Hanoi Chinese](task-hanoi-zh.html) / [English](task-hanoi-en.html) · [Assembly Chinese](task-tabletop-assembly-zh.html) / [English](task-tabletop-assembly-en.html) · [GitHub Release](https://github.com/wuxiyang1996/robo-si/releases/tag/tabletop-20261023).

User-authorized publication includes Hanoi 3, 4 and 5 disks (58/58 scenarios, 19/19 final checks) and Assembly layer 1 (8/8 scenarios, 14/14 checks). Four human-review gates remain unsigned for each task; formal admission remains false. [Download and reproduction](tabletop-release/README.md). The separate frozen snapshots in the release packet preserve the two distinct runtime digests.

## H4 layer 1 reference-data release (2026-10-24)

[Chinese](task-h4-zh.html) · [English](task-h4-en.html) · [Release and offline packet](https://github.com/wuxiyang1996/robo-si/releases/tag/h4-layer1-20261024). The primary cohort is 11/14 first-layer full runs; all three failures are preserved. Historical layer 2/3 evidence remains an appendix (4/4 each). The offline packet includes original sealed evidence and a publication-time source snapshot with a historical hash audit. Independent subtasks, itemized human review and second-person reproduction remain pending; `admitted=false`, R9 deferred.

## Current task completion (2026-10-25)

The [unified website snapshot](website-completion.json) now follows the 14-task counts above; historical cohort counts remain attached to their original release evidence.

H1 remains in progress for its explicitly selected randomized Layer-1 first release; layers 2 and 3 are deferred; its fixed 1.25 m reference milestone passes native C371 3/3 and matching container LowCmd C373 1/1, each score 1.0 with no safety events. Its verified reproduction archive remains local; publishing the website review evidence does not publish that archive. See [H1 report](task-h1-en.html). H3 is now a multi-robot task: both dual-G1 variants are published as a native host reference, with final heavy 2/2 and no_prop 1/1. The original single-G1 candidate A is historical; its evidence does not transfer to the new task. H6 fixed 2 kg library-crate baseline is user-accepted and published (1/1, 587.74 s); its unfinished continuous tool task remains outside that scope. M3 fixed functional reference is complete and published: normal-start 2/2, score 1.0, 411.16 s, no benchmark monitor alarms. Picking uses box support; same-parameter repeats are not independent seeds. See [M3 report](task-m3-en.html). M4 preconnected towing reference is complete and published (6/6 historical successes; perturbations base 4/6, hard 10/12). Autonomous docking/loading/detachment remain incomplete; v2 is stopped and a new mechanism has a separate design task. See [M4 report](task-m4-en.html). Human sign-off and second-person reproduction remain separate acceptance work.

The [website audit](website-audit.json) checks all 43 top-level HTML pages, local file and fragment targets, status evidence hashes, inventory counts and the ten remote non-draft releases. It does not execute physics or sign human acceptance. Run `python -B infra/tools/audit_website.py --remote --out infra/website-audit.json` from the repository root to refresh it.

## M2 first-layer reference release (2026-10-24)

[Chinese](task-m2-zh.html) · [English](task-m2-en.html) · [Release and offline packet](https://github.com/wuxiyang1996/robo-si/releases/tag/m2-layer1-20261024). Fixed 0.25 kg / 1.8 m corridor: references 09/10/11 pass 3/3 and ordinary container replay 09d passes 1/1, each at 1.0 in 175.28 s. All six stages complete; public command and actual-effort bounds pass. The report retains complete 1.5 m walls and uses elevated cameras. Same fixed scene/seed, privileged feedback and open-loop replay are explicitly scoped; human sign-off and independent reproduction remain pending, admitted=false. See [M2 evidence](m2-current-evidence.json). Original 9 kg and higher layers are outside this release.

## H6 accepted reference · 2026-10-24

[Chinese](task-h6-zh.html) / [English](task-h6-en.html): library-crate full run 1/1, 587.74 s; user acceptance recorded, archive and recordings published. Poly Haven Wooden Crate 02, CC0. Historical 3/3 and 6/6 remain separate. Formal admission and second-person reproduction remain pending.

## H3 multi-robot reference release

[English](task-h3-en.html) · [中文](task-h3-zh.html) · [Release](https://github.com/wuxiyang1996/robo-si/releases/tag/h3-cooperative-20261024). Two G1 robots, heavy_prop and no_prop, common 180 s. Frozen native runtime, all failed attempts and independent audits are included in the release. Formal admission, isolated agent interface, human sign-off and second-person reproduction remain pending.

## Directory layout and cleanup

| Location | Purpose |
|---|---|
| `index.html`, `contribute-*.html`, `status-*.html` | Website entry points and current task summaries |
| `task-*.html`, shared CSS/JS | Bilingual task descriptions, recordings and evidence links |
| `website-completion.json` | Authoritative current inventory; H3 is `multi_robot`, two G1 robots, two variants |
| `website-audit.json`, `tools/audit_website.py` | Current website validation and its reproducible checker |
| `*-release/`, `website-status-evidence/` | Referenced release materials and byte-bound evidence; preserve their contents and links |
| `sandbox/` | Shared runtime code; independent of website housekeeping |
| [archive/20261025](archive/20261025/README.md) | Superseded audit and unreferenced index snapshots, with restoration hashes |

`current-task-status.json` and `resumed-task-evidence.json` are historical progress snapshots, not the current task inventory. They remain at their original paths because retained provenance records bind those paths or bytes. Do not replace them with new results.

The 2026-10-25 cleanup archived four old metadata files and moved five Python cache directories out of `infra`. Nothing was permanently deleted. Referenced recordings, failed attempts, frozen release evidence and sandbox source files remain in place. See the [cleanup receipt](archive/20261025/cleanup-receipt.json) for exact paths and hashes. The published H3 packet remains unchanged.

## Website status refresh (2026-10-25)

The bilingual home-page counters and H1 cards now use the same inventory as the status pages. H1 review evidence is frozen under `website-status-evidence/h1-fixed-reference-20261025/`; the separate 3.83 GB reproduction archive has not been uploaded. M3 remains published with normal-start 2/2 success. Eight superseded, unreferenced H1 status snapshots are retained in [the status archive](archive/20261025-status-refresh/README.md). Current and historical failure evidence, recordings, byte-bound provenance and runtime source are retained.

## Additional local task development

The existing 14-task inventory keeps its published scope. Additional development includes [Jenga](../humanoid/g1_tabletop_jenga/README.md), [support-block extraction](../humanoid/g1_support_block_extraction/README.md), [fragile-flask transport](../humanoid/g1_fragile_flask_transport/README.md), and a published dual-arm disk-rotation GPU reference candidate: 6/6 continuous runs, 2/2 independent replays and verified three-level mappings ([English](task-disk-rotation-en.html), [中文](task-disk-rotation-zh.html)). These additions do not change the existing completion denominator or admission decisions.

## G1 space extraction reference release

[English](task-space-extraction-en.html) · [中文](task-space-extraction-zh.html) · [Release](https://github.com/wuxiyang1996/robo-si/releases/tag/g1-space-extraction-0.1.0). Two free-base G1 tasks run on Gamma GPU physics. Appliance 3/3 and retrieval 1/3 fresh complete executions; both raw action replays fail. Full scoring, three-level mappings, 22 retained draws and 53 original attempts are included. Human review and formal admission remain pending; historical counts are unchanged.

## Fragile Flask Transport reference release

[中文任务页](task-fragile-flask-zh.html) · [English task page](task-fragile-flask-en.html) · [Release](https://github.com/wuxiyang1996/robo-si/releases/tag/g1-fragile-flask-0.1.0).
Gamma GPU validation: three fresh three-flask successes, one fresh single-flask
success and two independent physical replays; 39 software tests and nine mechanism
checks pass. Both videos, per-run results and verified publication evidence are
available directly on the task pages. The files in `fragile-flask-release/` make
these pages portable when serving `infra/` alone; their hashes are recorded in
[the asset manifest](fragile-flask-release/manifest.json).

The bilingual home, status and reference indexes link this separate candidate.
Owner approval is recorded in [approval.json](fragile-flask-release/approval.json);
0.1.0 is the formal reference release. Existing 14-task inventory totals remain
unchanged. Fixed pelvis and nominal scenes only; full benchmark technical
admission remains separate.

Block reference candidates: [Jenga](task-jenga-en.html) and [support extraction](task-support-block-extraction-en.html) each have 3/3 complete Gamma GPU runs and one independent full replay for their declared seed 0 profiles. Videos, measurements and the compact expert reproduction workspace are linked from the task pages. Fixed pelvis and privileged state; human sign-off and formal admission remain pending.
