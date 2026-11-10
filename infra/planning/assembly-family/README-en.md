# Assembly suite: 10 independent tasks

2026-10-28 · 10 independent tasks: Assembly 4, Gear Assembly 3, Reference Assembly 3; three originals and seven new tasks. Embodiment and difficulty are evaluation configurations, not extra tasks. Five-finger evaluation starts with Gear tool compatibility. New designs remain unverified; this update runs no simulation.

[中文](README.md) · [English](README-en.md) · [JSON](task-design.json)

## Counting and bodies

Count independent manipulation problems as tasks. Body, difficulty, disclosure, seeds, probes and ablations are configurations. This explicitly replaces the earlier 25-entry scene × embodiment convention. The three combined scenes become D3 configurations within their compatibility tasks; retain the experiments without counting extra tasks. R1, A3, Go2 with arm and infeasibility-exit tasks are not counted.

| Family | Original | Reasoning | Compatibility | Total |
| --- | --- | --- | --- | --- |
| Assembly | 1 | 2 | 1 | 4 |
| Gear Assembly | 1 | 1 | 1 | 3 |
| Reference Assembly | 1 | 1 | 1 | 3 |
| Total | 3 | 4 | 3 | 10 |

| Code | Embodiment |
| --- | --- |
| G | G1 + Dex3 |
| F | G1 + Inspire five-finger hand |
| S | Stretch 3 |

Priority pairs: G/S for support establishment in ASM-04; G/F for grasping and actuation in GEAR-03; G/S for workspace, sequence and fixture adaptation in REF-03. Other tasks start with G. The current plan lists 13 body configurations, including three originals; this is a development count, not verified coverage. Add other five-finger or Stretch configurations only after probes establish their value, without a Cartesian expansion.

For G/F comparisons, use the same official G1 body and base constraints, changing only the hand and necessary control mapping; calibrate each hand independently. Historical G1 models and 43-dimensional trajectories do not validate the new bodies. Freeze base constraints, asset hashes and controller versions before execution. S uses the existing Stretch 3, not Stretch 4 or R1 Pro specifications. G/S changes arm count, end effector, workspace and base together, so it measures whole-body adaptation.

## Difficulty and information

D1 executes a known feasible method; D2 selects among candidates; D3 composes methods, repairs an assembly or changes intermediate constraints. Preserve original L1–L3 definitions. Difficulty does not rank part counts or robot models; the listed D values are design targets.

Record disclosure separately: known capabilities, unknown compatibility, or partly hidden physical parameters with low-risk probes and observable feedback. Composition or one successful run alone does not establish self-modeling. Software-tool discovery is a separate interface condition, not another physical task.

## Complete task list

### ASM · 4

| ID | Group | Body | Difficulty | Task | Scene and purpose | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ASM-01 | Original | G | Original | Original support-assisted sleeve and cap assembly | Retain the original configuration and scorer: independent support, assembly and stable release. | Historical scoped witness |
| ASM-02 | Reasoning | G | D2 | Select among candidate supports | Fixed body; vary support height, insertion access and load capacity, checking actual load transfer. | Full checks passed |
| ASM-03 | Reasoning | G | D3 | Compose a support | Individual pieces are insufficient; a stand and shims are candidates. Exclude other single-piece routes before claiming composition is necessary. | Attempted; full witness pending |
| ASM-04 | Compatibility | G/S | D2/D3 | Body compatibility of support methods | One shared world with a push-in wedge, grasp-and-place stand and shims; methods are physically effective, while deployment and release depend on the body. D3: vary load-bearing usefulness and body operability together, requiring a nonempty feasible intersection. | Full checks passed |

### GEAR · 3

| ID | Group | Body | Difficulty | Task | Scene and purpose | Status |
| --- | --- | --- | --- | --- | --- | --- |
| GEAR-01 | Original | G | Original | Original illustrated assembly and drive test | Retain the original seven stages, contact-driven transmission, tool placement and final release. | Saved v6 witness; current-source revalidation pending |
| GEAR-02 | Reasoning | G | D3 | Diagnose, repair and retest | Use observable evidence to distinguish incomplete seating, interference or failed transmission. New rules explicitly permit rework; hidden fault labels are unavailable. | Attempted; full witness pending |
| GEAR-03 | Compatibility | G/F | D2/D3 | Grasp, guide and drive-tool compatibility | Shared handles, guides and drive tools test acquisition, alignment, torque transfer and withdrawal; five fingers are not assumed superior. D3: grippable tools face workspace clearance limits, requiring regrasping, another tool or base refixturing. | Attempted; full witness pending |

### REF · 3

| ID | Group | Body | Difficulty | Task | Scene and purpose | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REF-01 | Original | G | Original | Original eight-part shelf assembly | Retain the specified sequence, stage releases and support-chain criteria; initialized mechanism checks are not robot witnesses. | Mechanism diagnostics; full robot assembly unverified |
| REF-02 | Reasoning | G | D3 | Schedule and reuse limited temporary fixtures | Limited fixtures make ordering affect access and withdrawal; the open-planning variant explicitly permits legal sequence changes. | Attempted; full witness pending |
| REF-03 | Compatibility | G/S | D2/D3 | Body adaptation in a constrained workspace | Compare simultaneous manipulation, grasp envelopes and release in one world with active holding and passive fixtures; environmental support remains legal for a single arm. D3: a usable fixture blocks later parts or withdrawal, requiring constraint transfer to complete the eight-part structure. | Attempted; full witness pending |

## Compatibility and success

Measure physical usefulness and body operability separately, then intersect their feasible sets. The complete use chain covers reach, acquisition, holding and actuation, effective work, support transfer, and release or withdrawal. Tool pickup alone is insufficient. Record feasible, excluded or unknown with evidence for each body × method; one failure does not certify infeasibility.

D2 compatibility configurations share the world and tools; D3 combined configurations vary usefulness and operability together. Body-specific table or layout changes are conditioned scenes, not same-world comparisons. Five fingers may reduce tool dependence or introduce envelope/control limitations; both are hypotheses. There is no prescribed best tool or model-name capability ranking.

Distinct scope: ASM-02 fixes the body and isolates support usefulness; ASM-04 D2 starts with physically effective methods and isolates operability. REF-02 fixes the body with ample workspace to test limited-fixture dependencies and reuse; REF-03 starts with enough fixtures and tests body/workspace fit, adding obstruction at D3. Gear compatibility must test alignment, torque transfer and functional verification rather than repeat load-bearing support selection.

Assembly requires independent final support, with no continuing hand support. Gear requires real tooth-contact transmission and tool release; repair is a new variant, not a change to the original seven-stage scorer. Reference retains eight parts and real support chains. Open-order extensions explicitly disclose their rules, preserving the original prescribed recipes. Each variant publicly states whether temporary fixtures must be withdrawn; do not silently change the original permission to retain its fixture. Accept every legal complete route.

The primary metric is complete physical success; historical scoring versions are preserved. Report method selection, capability calibration, probe cost, recovery and execution cost separately. Pair known/unknown capability, matched/mismatched tools, with/without tools and capability changes on the same physical seed. These ablations add no tasks. Do not reward a prescribed tool choice as success.

## Implementation and evidence

Start with four Assembly tasks and ASM-04 G/S probes, then three Gear tasks with priority Dex3/five-finger comparison in GEAR-03, followed by three Reference tasks. Task counts progress 4 → 7 → 10; body configurations are reported separately. A complete eight-part Reference robot expert remains a prerequisite.

Each new scored configuration needs a full physical witness matching assets and rules: freeze scene and high/low plans before execution; start normally and run continuously; save commands, contacts, trajectories, segment mappings, video and independent verification. No runtime pose writes, artificial attachment or hidden binding. Probes and static mechanism diagnostics do not substitute for complete witnesses. Retain failures and unknowns; a failed route is not a certificate excluding every route.

Implementation and physical attempts have started after design registration; see [execution progress](/infra/task-assembly-evidence-en.html) for current runs, failures and evidence. Original ASM retains its released scope. Original GEAR retains only the saved v6 scope, with current-source revalidation and portable publication pending. Original REF has mechanism and idle-interface checks, without a full robot assembly witness. Three originals do not mean three verified successes. All seven new tasks and new body configurations are unverified; the established 14-task inventory and admission status are unchanged.

## Legacy IDs

The [historical 25-entry JSON](history/proposal-25-task-design.json) is superseded for current counting. All `.G/.F/.S` suffixes identify body configurations, not independent tasks. These merges retain the original experimental questions:

| Old scene | Current task | Disposition |
| --- | --- | --- |
| ASM-05 | ASM-04 | D3 configuration; not separately counted |
| GEAR-04 | GEAR-03 | D3 configuration; not separately counted |
| REF-04 | REF-03 | D3 configuration; not separately counted |
