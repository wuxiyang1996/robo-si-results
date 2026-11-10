# DR: Material-Aware Disc Manipulation

2026-10-29 · All nine primary tasks pass exact-configuration simulation qualification: two normal-reset runs, independent actuator replay, hierarchical plans, continuous trajectories, physics audits and same-run video. DR-I01 remains excluded; untested bodies, tools and generalization claims remain unknown.

[中文](README.md) · [English](README-en.md) · [JSON](task-design.json)

Rotate a freely resting disc to the target orientation, control centre drift, then withdraw and leave it stable. No required tool, arm count or recontact count. Keep table support; lifting, welding, object-pose writes and externally applied object forces are not solutions.

[执行证据汇总 / Execution evidence](EXECUTION-en.md) · [All attempts](/infra/disk-family-evidence/monitor.json) · [Source and video validation](/infra/disk-family-evidence/artifact-validation.json)

## Main task list

| ID | Group | Tier | Task | Scene and purpose | Priority bodies | Status |
| --- | --- | --- | --- | --- | --- | --- |
| [DR-01](/infra/task-dr-01-en.html) | Original | L1 | Uniform disc rotation | Preserve 0.1.0: a uniform disc, ±30°, contact acquisition, rotation and stable release. | Dual Panda | accepted_simulation_scope |
| [DR-02](/infra/task-dr-02-en.html) | Contact reasoning | L2 | Select contacts on a segmented rim | Observe or probe heterogeneous rim sectors to find useful contacts. Effective and ineffective initial sectors are paired configurations; continuous sliding to a useful sector is legal. | Dual Panda | accepted_simulation_scope |
| [DR-03](/infra/task-dr-03-en.html) | Contact reasoning | L2 | Balance rotational resistance and centre drift | Vary rim and support friction independently; distinguish slip, rotational resistance and centre drift, then adjust force and motion. Start with a uniform rim to isolate this problem. | Dual Panda | accepted_simulation_scope |
| [DR-04](/infra/task-dr-04-en.html) | Contact reasoning | L3 | Rotate through restricted approach sectors | Fixed table obstacles restrict continuous end-effector travel while leaving candidate contact sectors. Plan withdrawal, clearance and further rotation; recontact necessity is unverified. | Dual Panda | accepted_simulation_scope |
| [DR-05](/infra/task-dr-05-en.html) | Body–scene compatibility | L3 | Single-arm and dual-arm contact roles | Compare segmented single-arm pushing and coordinated dual-arm manipulation in the same world; assess torque and centre control without assuming single-arm infeasibility. | Single Panda / Dual Panda | accepted_simulation_scope |
| [DR-06](/infra/task-dr-06-en.html) | Body–scene compatibility | L3 | Change approach direction through mobility | Some sectors lie outside the initial workspace. A mobile robot may establish another work position; a fixed arm may use other legal routes. Verify reachability separately. | Stretch 3 / Single Panda | accepted_simulation_scope |
| [DR-07](/infra/task-dr-07-en.html) | Body–contact compatibility | L3 | Select pushing or grasping contacts | Compare side pushing and side pinching in a shared reachable region while keeping the disc table-supported. Use the same G1 body and base constraints, changing the hand and control mapping. | G1 + Dex3 / G1 + Inspire five-finger hand | accepted_simulation_scope |
| [DR-08](/infra/task-dr-08-en.html) | Body–tool compatibility | L3 | Select optional contact aids | Offer high-friction pads or handled contact blocks; test acquisition, stable use, tangential-force transfer and withdrawal. Direct completion is legal; aids must change contact physics. | G1 + Dex3 / G1 + Inspire five-finger hand / Stretch 3 | accepted_simulation_scope |
| [DR-09](/infra/task-dr-09-en.html) | Cooperation | L3 | Heterogeneous cooperative rotation | A fixed arm and mobile manipulator allocate drift control, pushing and repositioning, then both withdraw. Legal single-robot solutions count; cooperation benefit is unverified. | Panda + Stretch 3 | accepted_simulation_scope |

## Conditional control (outside the nine main tasks)

| ID | Group | Tier | Task | Scene and purpose | Priority bodies | Status |
| --- | --- | --- | --- | --- | --- | --- |
| DR-I01 | Conditional control | — | No feasible route with available bodies and aids | Require exclusion of all legal routes and a feasible twin changing only a critical capability or aid. Withdraw safely and leave the disc stable before reporting inability; absent evidence remains unknown. | To be bound | Design; unverified |

## Difficulty, configurations and deduplication

- L1: basic contact execution. L2: infer contact conditions and select a method. L3: adapt body capabilities, contact switching, aids or cooperation. These are design targets pending measurement.
- Count independent manipulation problems. Embodiment, rotation direction/angle, materials, seeds, disclosure and ablations are configurations, not a Cartesian task expansion.
- Record known parameters, unknown compatibility and partly hidden physics separately. Hide truth from the evaluated agent, not from author configurations and audit records.
- DR-02 fixes support conditions to test contact selection; DR-03 starts with a uniform rim to test resistance and drift. Merge DR-04/06 or demote one to a configuration if they expose only the same workspace problem.
- DR-05 varies arm count; DR-07 varies hands on the same body. DR-06 changes base, end effector and workspace together and measures overall embodiment adaptation.
- Verify the existing Stretch 3 asset first; Stretch 4 needs separate validation. The existing Panda reference has spherical pushers and does not establish grasping capability.

## Shared scoring and evidence boundaries

The primary metric is complete valid success. Accept every legal solution satisfying the goal and public constraints, including no-tool, no-recontact and single-arm solutions. Report time, probes, contact switches, centre drift, peak force, cooperation and aid use separately; they do not compensate for failure.

DR-01 preserves 0.1.0 configurations, scoring and evidence: three complete executions for each of two exact configurations (6/6) and two independent action replays (2/2). Repeats do not establish random-domain performance. On the nominal case, fixed_contacts succeeds in 18.52 s versus 43.48 s for the full expert. It still moves around the rim but does not withdraw to recontact. Necessary recontact, indispensable dual-arm use and heterogeneous-cooperation benefits remain unproved.

New scenes start from the original criteria: final heading error ≤3°, maximum/final centre drift ≤30/10 mm, two-second stable release and tilt ≤5°, with the original speed/force definitions and 120 s budget as initial candidates. Declare and freeze any extension changes before execution; do not rewrite historical results. Verify actuator and stability constraints per body.

Configure rim friction, effective bottom–table friction, mass and inertia independently. Genesis 1.4.3 takes the larger coefficient of a contact pair; a high-friction pusher can mask a low-friction rim. Verify the actual contact pairs. Sectors rotate with the disc and aids transmit real contact forces. Initially fix geometry, mass and inertia.

Separate privileged state-feedback experts from perception agents. Compare fixed_contacts, single_arm, the original full expert and an adaptive contact expert as policies, not extra tasks. One failure, timeout or unsuccessful IK search is not a global infeasibility certificate. DR-I01 needs all-route evidence and a feasible twin before scoring correct exits.

## Development order and current status

Start with DR-01–04, bind DR-05–08 configurations after body-compatibility probes, then address DR-09 and DR-I01. Preserve goals, candidate routes, capability boundaries, evidence status and observed strategies. Unverified entries remain unknown; draft code is not a reference witness.

Implementation resumed under the subsequent request, with per-task expert attempts and controls. See the execution summary and task pages for retained build errors, physical failures and complete successes. Unverified G1, single-arm and mobile routes remain unknown. DR-I01 is not declared infeasible without an all-route certificate.

## References

[Original task](/infra/task-disk-rotation-en.html) · [Family overview](../task-families-en.md) · [Assembly suite](../assembly-family/README-en.md) · [Constrained extraction](/infra/task-space-extraction-en.html)


## Current execution and qualification

- [DR-01](/infra/task-dr-01-en.html): accepted_simulation_scope · rc01 · 43.480000000000004 s.
- [DR-02](/infra/task-dr-02-en.html): accepted_simulation_scope · rc01 · 60.5 s.
- [DR-03](/infra/task-dr-03-en.html): accepted_simulation_scope · rc01 · 45.04 s.
- [DR-04](/infra/task-dr-04-en.html): accepted_simulation_scope · rc03 · 78.54 s.
- [DR-05](/infra/task-dr-05-en.html): accepted_simulation_scope · rc01 · 98.5 s.
- [DR-06](/infra/task-dr-06-en.html): accepted_simulation_scope · a12 · 114.22 s.
- [DR-07](/infra/task-dr-07-en.html): accepted_simulation_scope · rc01 · 85.0 s.
- [DR-08](/infra/task-dr-08-en.html): accepted_simulation_scope · a06 · 85.0 s.
- [DR-09](/infra/task-dr-09-en.html): accepted_simulation_scope · rc03 · 63.32 s.

[Full qualification report](/infra/disk-family-evidence/acceptance.json) · [Predeclared criteria](/infra/disk-family-evidence/acceptance-contract.json)

Fixed contacts still succeed on DR-02/03. DR-04 only distinguishes the tested controllers and obstacle configuration. Both single and dual arms solve DR-05. Five-finger G1 hands, successful aid use, cooperation necessity and randomized-domain generalization remain unverified. Failed trials are not infeasibility proofs.
