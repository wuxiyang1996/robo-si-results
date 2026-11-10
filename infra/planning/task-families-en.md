# H1 / M1 / M3: current families and development scope

2026-10-27 · Design organization only; zero new simulations. Preserve existing references, scoring and the established 14-task inventory. This overview supersedes the classification of H1E-09–14 as additional H1 tasks and the discussed nine/eleven-case expansion.

[中文](task-families.md) · [Structured index](task-families.json) · [H1](h1-extension/README-en.md) · [M1](m1-extension/README-en.md) · [M3](m3-extension/README-en.md)

## Family boundaries

| Family | Main operation | Completion |
| --- | --- | --- |
| M1 | Change object support/control and delivery roles | Retrieve from an elevated crate and release with support deep inside a low cabinet |
| H1 | Change the robot's own workspace using environmental supports and its own weight shifts | Elevated retrieval, transfer if needed, return and stable ground delivery |
| M3 | Change a lightweight partner robot's workspace and support state | Retrieve through the partner, deliver on the ground, and finish independently stable without mutual carrying support |

These classify research instances, not mandated agent action sequences. Reward legal single-robot completion, report it as a no-cooperation control and revise necessity labels. Ordinary object transfer or independent tool use is insufficient evidence of necessary M3 cooperation.

## Current 2 kg constraint

The user reports a current 2 kg payload limit. The affected platform, per-arm versus combined interpretation, lever arm and dynamic conditions are not yet bound to assets/controllers. Use 2 kg as a conservative total external carried-load screening ceiling for new designs; do not sum two arms to 4 kg or infer arbitrary-pose capability. Include tools, target, attachments, moments and changing dynamic loads.

A humanoid's body is supported through its feet by the floor/platform while climbing. The manipulation limit is not a body-mass limit: supports must withstand the actual robot, attachments and payload. Movable tools need payload screening; heavier structures may be prepositioned, and pushing requires separate checks.

For M3, count the entire carried robot, attachments and held target. X5 compatibility is unknown; old reference success or silently reducing model mass cannot establish it. Without a suitable lightweight asset, new lifting cases do not proceed to implementation. Humanoid carrying, assisted humanoid climbing and partner-supported humanoid balancing are withdrawn.

## H1: 22 independent registrations

| ID | Task |
| --- | --- |
| H1S-01 | Frozen G1/Dex3 baseline |
| H1S-02 | G1 five-finger handling |
| H1S-03 | Wheels and movable ramp |
| H1S-04 | A3 retrieval |
| H1S-05 | G1 two tiers / A3 one tier |
| H1S-06 | Infeasibility and physical exit |
| H1S-07.P1 | Push clear and retrieve |
| H1S-07.P2 | Push a support into place |
| H1S-07.P3 | Turn or change pushing side |
| H1S-07.P4 | Push a target that cannot be lifted |
| H1S-08 | Stretch handled box |
| H1S-09 | Stretch infeasibility and exit |
| H1S-10.A | G1 support selection |
| H1S-10.B | A3 support selection |
| H1S-10.C | Wheeled platform and ramp choice |
| H1S-10.D | Stretch work/transfer surface choice |
| H1S-11.A | Directly reachable retrieval |
| H1S-11.B | Tool-enabled complete retrieval |
| H1S-11.C | No feasible route including tools; exit |
| H1S-12 | Same-color identification |
| H1S-13 | Autonomous transfer and safe return |
| H1S-14 | Body adaptation in a narrow workstation |

20 split registrations plus two new operations; parent groups 07/10/11 are not counted again. No extra common-feasible calibration tasks. Accept all legal complete solutions.

## M1: 9 capability-boundary and tool-use cases

**One original task + 6 extension operations + 2 infeasibility controls: 9 total.** The original task has scoped historical witnesses and retains its configuration and scorer. Extensions remain unknown; zero new simulations. Parent groups and Cartesian model/rule/tool combinations are not counted.

| Case ID | Capability boundary | Scene and complete goal | Tools / partner | Status |
| --- | --- | --- | --- | --- |
| M1C-ORIG | Original M1: crate lowering, target retrieval and cabinet delivery | Original G1 + Dex3 lowers the crate to the transfer stand; X5 retrieves the block and places it deep in the low cabinet with support before release. Retain original v0.3 / V4 configuration, scorer and budget: 13 complete successes, eight physical seeds and 3/3 strict repeats; no new simulation. | Crate, original transfer stand, G1 + X5 | Witnessed in original scope |
| M1C-B01 | Crate cannot be lifted, but can be repositioned by pushing | Current grasp/carry limits block crate lifting and its initial position obstructs picking; controlled pushing and environmental support may establish retrieval access before cabinet delivery. | Crate and support surfaces | unknown |
| M1C-B02 | Held crate blocks safe picking; independent support needed | Provide supports with different top areas, capacities and handling geometry; determine which can independently support the released crate through retrieval and cabinet delivery. | Stands, boxes and work surfaces | unknown |
| M1C-B03 | Direct grasp falls short; an operable tool extends retrieval | Target in a fixed crate is beyond direct grasp; hooks, extended grippers, rods and short tools coexist. Check grasp, useful force and withdrawal, then complete cabinet delivery. | Hook, extended gripper, rod, short tool | unknown |
| M1C-B04 | Useful tool is inoperable by self but operable by partner | Keep target and tool working-end conditions; current hand is limited by handle, actuation or wrist moment, while a partner may operate the tool. Change operator or use another legal tool to deliver; no forced initial failure. | Tools with different body compatibility and a partner | unknown |
| M1C-B05 | Hand cannot enter the cabinet; a tool may deliver | Target fits the cabinet entrance but current hand envelope/reach prevents deep placement; choose a pusher or carrier with continuous support and complete tool withdrawal. | Narrow pusher, thin/thick carriers | unknown |
| M1C-B06 | Own tool cannot complete withdrawal; change deliverer | Target can enter, but the current body/tool combination cannot complete support transfer and withdrawal; a lower or smaller-hand partner is a candidate alternative. Insertion with retained tool support is not success. | Transfer surface, low-level operator and delivery tools | unknown |
| M1C-I01 | No body or available tool completes retrieval | Exclude all body poses, crate movement, alternative approaches, tool combinations and cooperation; only an all-route certificate establishes correct abstention. | All available tools and participants | unknown |
| M1C-I02 | Target itself cannot pass the cabinet entrance | The intact rigid target and sole entrance form the bottleneck, not hand width; exclude alternative openings, disassembly and deformation, then verify physical exit. | All delivery tools and participants | unknown |

Original-task evidence: [JSON](/infra/m1-current-evidence.json). New capability, Y/N, Q-exit and 2 kg screening rules below apply to extension designs, not retroactively to the original task. Historical witnesses do not validate extensions.

**Body/tool compatibility:** bind embodiments to explicit boundaries through asset and capability probes. Add a case only when body changes create a materially different feasible-route set or tool-operation problem; model-name swaps do not add cases. Test grasp, actuation, useful force, moments, transfer, withdrawal and final delivery, not merely tool pickup. Differences must be observable, never inferred from brands or appearance.

| Candidate profile | Embodiment |
| --- | --- |
| A | G1 + Dex3 + X5 |
| B | G1 + five-finger hand + same X5 |
| C | Wheeled dual-arm + low-level manipulator |

Y/N remain separately reported public-rule versions within each case: N permits help; Y requires designated-manipulator receipt and final delivery. Pairs change only rules, holding world, bodies, tools and sensors fixed. Direct/help records actual routes, never hidden prescribed solutions. Multiple routes, tool mismatch and recovery belong to concrete scenes; do not force an initial mistake. Cart 04, I02/I04 and D remain deferred.

**Implementation and scoring:** audit body/tool interfaces and complete routes before freezing parameters and priorities. Complete retrieval, required transfer, return/delivery and support release; accept all legal goal-satisfying solutions. Infeasibility requires all-route exclusion and all robots physically in Q, empty-handed and independently stable for 3 seconds. A failed route is insufficient. Seeds are instances, not cases. The 2 kg external-load screen remains provisional; component, pose and dynamic scope need verification.

## M3: 6 capability-boundary and tool-use cases

**One original task + 4 extension operations + 1 infeasibility controls: 6 total.** The original task has scoped historical witnesses and retains its configuration and scorer. Extensions remain unknown; zero new simulations. Parent groups and Cartesian model/rule/tool combinations are not counted.

| Case ID | Capability boundary | Scene and complete goal | Tools / partner | Status |
| --- | --- | --- | --- | --- |
| M3C-ORIG | Original M3: lift X5, supported retrieval, lowering and delivery | Original G1 lifts X5 for box-supported retrieval of the 65 mm ball, then lowers X5 for ground-tray delivery. Preserve hooks-v0.1, original scorer and 420-second budget: 2/2 normal-start successes, 411.16 seconds each, same-parameter repeats. This does not establish the new 2 kg compatibility. | Original support box, carrying interfaces, G1 + X5 | Witnessed in original scope |
| M3C-B01 | Lift candidate, but manipulation requires independent platform support | Prepared platform; complete lifting/lowering capability remains unverified and suspended manipulation is not assumed. Retrieve with independent platform support, then lower, release support and deliver. | Prepared platform and partner support interfaces | unknown |
| M3C-B02 | Existing supports are unsuitable; select and establish a workstation | Provide candidate supports varying in height, footprint and rating; assess partner support, extended-arm operation and safe return; establish a suitable workstation and complete retrieval/delivery. | Multiple support objects | unknown |
| M3C-B03 | Lifting is unsafe; a ramp is a candidate alternative | Keep cabinet, tools and partner; carrying capability is insufficient. Assess partner mobility, traction and ramp geometry for ascent and loaded return. Rejected lifting alone does not justify abstention. | Ramp, platform and partner mobility | unknown |
| M3C-B04 | Partner cannot use ramp; lifting is a candidate alternative | Retain B03 scene structure; partner chassis or drive capability prevents ramp use. Assess carrier lift, supported retrieval and lowering; lifting still requires the 2 kg and dynamic capability audit. | Carrying interfaces, platform and ramp | unknown |
| M3C-I01 | Lifting and every alternative route are infeasible | Carrying is unsuitable and direct retrieval, ramps, other supports, tools and combined routes are excluded; safely settle all participants independently before Q exit. | All available tools and participants | unknown |

Original-task evidence: [JSON](/infra/m3-current-evidence.json). New capability, Y/N, Q-exit and 2 kg screening rules below apply to extension designs, not retroactively to the original task. Historical witnesses do not validate extensions.

**Body/tool compatibility:** bind embodiments to explicit boundaries through asset and capability probes. Add a case only when body changes create a materially different feasible-route set or tool-operation problem; model-name swaps do not add cases. Test grasp, actuation, useful force, moments, transfer, withdrawal and final delivery, not merely tool pickup. Differences must be observable, never inferred from brands or appearance.

| Candidate profile | Embodiment |
| --- | --- |
| G | G1 + X5 |
| H | Other dual-arm humanoid + same X5 |
| W | Wheeled dual-arm + same X5 |

X5 is an unaudited partner candidate; compatibility with the current 2 kg condition is unknown. Do not rescale mass or silently substitute a lightweight robot. Rebind assets and capabilities for a partner change, adding a case only for a new bottleneck. Lift/ramp labels are unverified hypotheses, not prescribed solutions. Humanoid carrying and standalone return-posture tasks remain withdrawn.

**Implementation and scoring:** audit body/tool interfaces and complete routes before freezing parameters and priorities. Complete retrieval, required transfer, return/delivery and support release; accept all legal goal-satisfying solutions. Infeasibility requires all-route exclusion and all robots physically in Q, empty-handed and independently stable for 3 seconds. A failed route is insufficient. Seeds are instances, not cases. The 2 kg external-load screen remains provisional; component, pose and dynamic scope need verification.

## Shared evaluation and exit

Record family, case, embodiment, capability profile and seed separately, with tool layer, disclosure and route labels. Do not count Cartesian products as developed tasks. Infra L1/L2/L3 retain necessary tools, other-body-usable additions and observable distractors. Multiple routes and infeasibility are separate tracks.

Adequate observable evidence may justify direct retreat without failed manipulation. All participating robots must physically reach their Q bays, empty-handed, independently stable and without mutual support, simultaneously for 3 seconds. Previously moved objects remain legally and independently supported. Freeze speed/geometry thresholds per body. Exiting a feasible case is false abstention; unknown correctness remains null; timeout is not abstention. One rejected route or exhausted search is not an infeasibility certificate.

Current registrations: H1 22; M1 9 cases (one original + eight extensions); M3 6 cases (one original + five conditional extensions). Registration is not implementation or validation; no Cartesian body/rule counting.

## Legacy disposition

H1E-09 → M3E-01; H1E-10 → M3E-02 (self-climbing variants belong to H1); H1E-11 → M3E-03 with independent ramp completion as a control. H1E-12 generic long-tool selection belongs to relevant H1/M1 scenes. H1E-13 self-climbing tool composition belongs to H1; humanoid partner-support variants are withdrawn. H1E-14 becomes an embodiment/capability comparison axis. H1E-I05–I07 are historical proposals; only M3E-I01 remains in the current conditional M3 shortlist.

Retain old documents and links with superseded notices. Original H1/M1 IDs and published witnesses remain traceable and do not transfer to new configurations.

<!-- assembly-family-overview:start -->
## Assembly suite: 10 independent tasks

10 independent tasks: Assembly 4, Gear Assembly 3, Reference Assembly 3; three originals and seven new tasks. Embodiment and difficulty are evaluation configurations, not extra tasks. Five-finger evaluation starts with Gear tool compatibility. New designs remain unverified; this update runs no simulation.

[Full design and task list](/infra/task-assembly-family-en.html) · [Markdown](assembly-family/README-en.md) · [JSON](assembly-family/task-design.json)

<!-- assembly-family-overview:end -->

<!-- disk-flip-family-overview:start -->
## Disk Flip family

4 task variants, 3 embodiments and 6 selected settings, using 3 object profiles (2 main geometries). All six have candidate experts and physics executions; 5 complete witnesses, 1 still unresolved.

[Task list / 任务与盘体设计](/infra/task-disk-flip-en.html#disk-flip-family) · [Markdown](disk-flip-family/README-en.md) · [JSON](disk-flip-family/task-design.json)

<!-- disk-flip-family-overview:end -->

<!-- disk-rotation-family-overview:start -->
## Disc manipulation family · 9 main tasks

Nine main tasks plus one conditional control. Implementation and physical execution are active. Each task page records its expert, high/low planning, matching trajectory, physics audit and video. Successes, controller failures and build errors are separate; bodies, parameters and reruns do not add tasks.

[完整清单 / Full list](/infra/task-disk-rotation-family-en.html) · [Markdown](/infra/planning/disk-rotation-family/README-en.md) · [JSON](/infra/planning/disk-rotation-family/task-design.json)

<!-- disk-rotation-family-overview:end -->
