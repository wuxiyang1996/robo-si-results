# Assembly suite: 25 tasks

2026-10-28 · 25 registered designs: Assembly 9, Gear Assembly 8, Reference Assembly 8; three originals and 22 extensions. Bodies: G1 Dex3, G1 Inspire five-finger hand and Stretch 3. Six five-finger compatibility/combined tasks are added. All extensions remain unverified; this update runs no simulation.

[中文](README.md) · [English](README-en.md) · [JSON](task-design.json)

## Counting and bodies

Count scene × embodiment. Difficulty, disclosure, seeds, probes and ablations add no tasks. The 25 registrations are a design ceiling, to be frozen after body × method probes; configurations without meaningful differences may be merged with an explicit registry revision. R1, A3, Go2 with arm and infeasibility-exit tasks are not counted.

| Family | Original | Reasoning | Compatibility | Combined | Total |
| --- | --- | --- | --- | --- | --- |
| Assembly | 1 | 2 | 3 | 3 | 9 |
| Gear Assembly | 1 | 1 | 3 | 3 | 8 |
| Reference Assembly | 1 | 1 | 3 | 3 | 8 |
| Total | 3 | 4 | 9 | 9 | 25 |

| Code | Embodiment |
| --- | --- |
| G | G1 + Dex3 |
| F | G1 + Inspire five-finger hand |
| S | Stretch 3 |

For G/F comparisons, use the same official G1 body and base constraints, changing only the hand and necessary control mapping; calibrate each hand independently. Historical G1 models and 43-dimensional trajectories do not validate the new bodies. Freeze base constraints, asset hashes and controller versions before execution. S uses the existing Stretch 3, not Stretch 4 or R1 Pro specifications. G/S changes arm count, end effector, workspace and base together, so it measures whole-body adaptation.

## Difficulty and information

D1 executes a known feasible method; D2 selects among candidates; D3 composes methods, repairs an assembly or changes intermediate constraints. Preserve original L1–L3 definitions. Difficulty does not rank part counts or robot models; the listed D values are design targets.

Record disclosure separately: known capabilities, unknown compatibility, or partly hidden physical parameters with low-risk probes and observable feedback. Composition or one successful run alone does not establish self-modeling. Software-tool discovery is a separate interface condition, not another physical task.

## Complete task list

### ASM · 9

| ID | Group | Body | Difficulty | Task | Scene and purpose | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ASM-01 | Original | G | Original | Original support-assisted sleeve and cap assembly | Retain the original configuration and scorer: independent support, assembly and stable release. | Historical scoped witness |
| ASM-02 | Reasoning | G | D2 | Select among candidate supports | Fixed body; vary support height, insertion access and load capacity, checking actual load transfer. | Design; unverified |
| ASM-03 | Reasoning | G | D3 | Compose a support | Individual pieces are insufficient; a stand and shims are candidates. Exclude other single-piece routes before claiming composition is necessary. | Design; unverified |
| ASM-04.G | Compatibility | G | D2 | Body compatibility of support methods | One shared world with a push-in wedge, grasp-and-place stand and shims; methods are physically effective, while deployment and release depend on the body. | Design; unverified |
| ASM-04.F | Compatibility | F | D2 | Body compatibility of support methods | One shared world with a push-in wedge, grasp-and-place stand and shims; methods are physically effective, while deployment and release depend on the body. | Design; unverified |
| ASM-04.S | Compatibility | S | D2 | Body compatibility of support methods | One shared world with a push-in wedge, grasp-and-place stand and shims; methods are physically effective, while deployment and release depend on the body. | Design; unverified |
| ASM-05.G | Combined | G | D3 | Joint support validity and body compatibility | Vary physical usefulness and body operability together; validate at least one complete route per scored embodiment. | Design; unverified |
| ASM-05.F | Combined | F | D3 | Joint support validity and body compatibility | Vary physical usefulness and body operability together; validate at least one complete route per scored embodiment. | Design; unverified |
| ASM-05.S | Combined | S | D3 | Joint support validity and body compatibility | Vary physical usefulness and body operability together; validate at least one complete route per scored embodiment. | Design; unverified |

### GEAR · 8

| ID | Group | Body | Difficulty | Task | Scene and purpose | Status |
| --- | --- | --- | --- | --- | --- | --- |
| GEAR-01 | Original | G | Original | Original illustrated assembly and drive test | Retain the original seven stages, contact-driven transmission, tool placement and final release. | Saved v6 witness; current-source revalidation pending |
| GEAR-02 | Reasoning | G | D3 | Diagnose, repair and retest | Use observable evidence to distinguish incomplete seating, interference or failed transmission. New rules explicitly permit rework; hidden fault labels are unavailable. | Design; unverified |
| GEAR-03.G | Compatibility | G | D2 | Grasp, guide and drive-tool compatibility | Shared handles, guides and drive tools test acquisition, alignment, torque transfer and withdrawal; five fingers are not assumed superior. | Design; unverified |
| GEAR-03.F | Compatibility | F | D2 | Grasp, guide and drive-tool compatibility | Shared handles, guides and drive tools test acquisition, alignment, torque transfer and withdrawal; five fingers are not assumed superior. | Design; unverified |
| GEAR-03.S | Compatibility | S | D2 | Grasp, guide and drive-tool compatibility | Shared handles, guides and drive tools test acquisition, alignment, torque transfer and withdrawal; five fingers are not assumed superior. | Design; unverified |
| GEAR-04.G | Combined | G | D3 | Assembly under tool-fit and workspace constraints | A grippable tool may not fit the workspace; allow regrasping, tool changes or base refixturing before completing the drive test. | Design; unverified |
| GEAR-04.F | Combined | F | D3 | Assembly under tool-fit and workspace constraints | A grippable tool may not fit the workspace; allow regrasping, tool changes or base refixturing before completing the drive test. | Design; unverified |
| GEAR-04.S | Combined | S | D3 | Assembly under tool-fit and workspace constraints | A grippable tool may not fit the workspace; allow regrasping, tool changes or base refixturing before completing the drive test. | Design; unverified |

### REF · 8

| ID | Group | Body | Difficulty | Task | Scene and purpose | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REF-01 | Original | G | Original | Original eight-part shelf assembly | Retain the specified sequence, stage releases and support-chain criteria; initialized mechanism checks are not robot witnesses. | Mechanism diagnostics; full robot assembly unverified |
| REF-02 | Reasoning | G | D3 | Schedule and reuse limited temporary fixtures | Limited fixtures make ordering affect access and withdrawal; the open-planning variant explicitly permits legal sequence changes. | Design; unverified |
| REF-03.G | Compatibility | G | D2 | Active holding and passive positioning compatibility | Compare simultaneous manipulation, grasp envelopes and release in one world with active holding and passive fixtures; environmental support remains legal for a single arm. | Design; unverified |
| REF-03.F | Compatibility | F | D2 | Active holding and passive positioning compatibility | Compare simultaneous manipulation, grasp envelopes and release in one world with active holding and passive fixtures; environmental support remains legal for a single arm. | Design; unverified |
| REF-03.S | Compatibility | S | D2 | Active holding and passive positioning compatibility | Compare simultaneous manipulation, grasp envelopes and release in one world with active holding and passive fixtures; environmental support remains legal for a single arm. | Design; unverified |
| REF-04.G | Combined | G | D3 | Replan around body limits and fixture obstruction | A usable fixture can obstruct later parts or withdrawal, requiring temporary-constraint transfer; all eight parts must form the final stable support chain. | Design; unverified |
| REF-04.F | Combined | F | D3 | Replan around body limits and fixture obstruction | A usable fixture can obstruct later parts or withdrawal, requiring temporary-constraint transfer; all eight parts must form the final stable support chain. | Design; unverified |
| REF-04.S | Combined | S | D3 | Replan around body limits and fixture obstruction | A usable fixture can obstruct later parts or withdrawal, requiring temporary-constraint transfer; all eight parts must form the final stable support chain. | Design; unverified |

## Compatibility and success

Measure physical usefulness and body operability separately, then intersect their feasible sets. The complete use chain covers reach, acquisition, holding and actuation, effective work, support transfer, and release or withdrawal. Tool pickup alone is insufficient. Record feasible, excluded or unknown with evidence for each body × method; one failure does not certify infeasibility.

Compatibility tasks share the world and tools; combined tasks vary usefulness and operability together. Body-specific table or layout changes are conditioned scenes, not same-world comparisons. Five fingers may reduce tool dependence or introduce envelope/control limitations; both are hypotheses. There is no prescribed best tool or model-name capability ranking.

Assembly requires independent final support, with no continuing hand support. Gear requires real tooth-contact transmission and tool release; repair is a new variant, not a change to the original seven-stage scorer. Reference retains eight parts and real support chains. Open-order extensions explicitly disclose their rules, preserving the original prescribed recipes. Each variant publicly states whether temporary fixtures must be withdrawn; do not silently change the original permission to retain its fixture. Accept every legal complete route.

The primary metric is complete physical success; historical scoring versions are preserved. Report method selection, capability calibration, probe cost, recovery and execution cost separately. Pair known/unknown capability, matched/mismatched tools, with/without tools and capability changes on the same physical seed. These ablations add no tasks. Do not reward a prescribed tool choice as success.

## Implementation and evidence

Start with original Assembly, support selection and composition, plus G/F/S body × method probes. Complete its compatibility and combined tasks for nine registrations, then eight Gear and eight Reference tasks: 9 → 17 → 25. A complete eight-part Reference robot expert remains a prerequisite.

Each new scored configuration needs a full physical witness matching assets and rules: freeze scene and high/low plans before execution; start normally and run continuously; save commands, contacts, trajectories, segment mappings, video and independent verification. No runtime pose writes, artificial attachment or hidden binding. Probes and static mechanism diagnostics do not substitute for complete witnesses. Retain failures and unknowns; a failed route is not a certificate excluding every route.

This update changes design only and runs zero simulations. Original ASM retains its released scope. Original GEAR retains only the saved v6 scope, with current-source revalidation and portable publication pending. Original REF has mechanism and idle-interface checks, without a full robot assembly witness. Three originals do not mean three verified successes. All 22 extensions are unverified; the established 14-task inventory and admission status are unchanged.
