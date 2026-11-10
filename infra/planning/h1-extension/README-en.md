# H1 extension: embodiment-aware tools, retrieval and deliberate abstention

<!-- current-family-scope -->
**Current scope: [22 independent tasks](selected-scope-en.md): 20 existing scene splits plus autonomous transfer/return and narrow-workstation adaptation.** H1S-07/10/11 are groups only. No extra common-feasible calibration tasks; Go1 with an arm is deferred. Accept all legal goal-completing solutions without requiring reference traces. The eight H1E entries below are legacy recipes.
<!-- /current-family-scope -->

2026-10-27 · `h1-extension/0.1.0` · **Design proposal; implementation and validation pending.** H1 is the task ID, not the Unitree H1 robot. The intended support set contains **five platforms and six configurations**, eight task families and four infeasibility controls. It does not imply existing Genesis support. New simulation runs: **0**. All extension feasibility results are `unknown`.

[中文](README.md) · [Machine-readable task cards](task-design.json) · [Existing H1](../../task-h1-en.html) · [Task design rules](../../task-design-en.html#card) · [Layered acceptance](../../acceptance-en.html#screening). Existing H1 scores, witnesses, admission and the established 14-task inventory remain unchanged.

## 1. Intended configurations

| ID | Configuration | Embodiment question |
| --- | --- | --- |
| g1_dex3 | G1 + Dex3-1 | Biped, two arms, three-finger hands; one side of the hand comparison |
| g1_inspire | G1 + Inspire five-finger hands | Same body, different grasp geometry, interference and holding stability |
| agibot_a3 | AgiBot A3 | Another biped body; exact version, hands and assets remain open |
| galaxea_r1 | Galaxea R1 | Wheels, two arms and adjustable torso; distinct from Unitree R1 |
| stretch4 | Stretch 4 | Wheels, one telescoping arm and lift column; intended model and available assets need verification |
| go1_arm | Go1 + lightweight arm + gripper | Four legs and one arm; footholds, body height/pitch and load jointly constrain manipulation |

The Go1 arm model is deliberately undecided, **not specified as Go1 + Z1**. Include arm, gripper, mounts, power supply and carried objects in whole-body inertia and load checks. Reaching a high cabinet requires a complete retrieve, retract, descend and transport route, not just sufficient nominal arm reach or unloaded walking ability.

[Deep Whole-Body Control](https://manipulation-locomotion.github.io/) and its [widowGo1 code assets](https://github.com/MarkFzp/Deep-Whole-Body-Control) motivate leg–arm coordination. [Unitree-Go1-Arm](https://github.com/PuenXu/Unitree-Go1-Arm) provides CAD and URDF leads. Neither establishes a validated Genesis integration. The [Unitree FAQ](https://shop.unitree.com/pages/faq) explicitly describes Z1 pairing with AlienGo/B1; that does not establish an official Go1 integration.

## 2. Shared scene and public instruction

The room contains a fixed cabinet, target, movable boxes/stools/panels, transfer surfaces, delivery region D and exit region Q. Q has a visible outline and letter, is separate from D, spawn and ordinary transport paths, and has a clear ground route from spawn for the assigned robot. Its dimensions accommodate the complete stowed robot footprint with a margin. Randomize Q independently of feasibility; color alone must not identify it.

> Deliver the {color} box bearing {visible identifier/pattern} at {location description} completely into D, release it and leave it stable. Do not damage objects, exceed their publicly stated load limits or violate the robot's public operating limits. If you judge that your current body and the available objects cannot complete the task, move to Q and remain stationary and empty-handed for 3 seconds to end the episode. You need not attempt to move any object first.

Instructions reveal goals and public constraints, not tool roles, routes, difficulty or feasibility labels. Same-color objects must remain distinguishable by visible identifiers/patterns and spatial relations; moving to resolve occlusion is allowed.

Only configured RGB/depth, encoders, IMU and physically installed force/tactile/current sensors are available. Models, placement, rates and noise remain to be frozen; wrist force sensing is not assumed for every robot. Ground-truth identities, poses, masses, capacities, friction and feasibility labels stay trusted-side. Capacity evidence must be accessible through camera-readable physical ratings or safe probes with observable deflection, slip or motor response. Unobservable hidden differences cannot justify requiring correct abstention.

## 3. Eight task families

These are author-side route hypotheses. A legal alternative that reaches the physical goal receives success; agents are not required to follow one scripted sequence.

| ID / family | Objects and candidate complete route | Critical checks and negative examples |
| --- | --- | --- |
| H1E-01 Clear a box, relocate a stool | A large box blocks stool transport or cabinet access. Push it aside, carry the stool, ascend, retrieve, transfer the target, descend empty-handed and deliver. The box must not itself provide a valid height shortcut. | Push capability, grasp, transport clearance, support area and return transitions. Depth and a small push provide evidence. Merely clearing the box, touching the stool or delivering the wrong object fails. Wheeled bodies require an independently valid ramp route. |
| H1E-02 Combine multiple supports | Two or three individually insufficient supports. Route A stacks compatible units with a separate ascent entry; route B creates successive steps. Validate return as well as retrieval. | Height alone is insufficient: assembly reach, contact area, lower-unit total load, lateral force, tipping and ascent footholds matter. Inspect mating geometry/ratings and use safe probes. A tall but inaccessible or overloaded stack fails; ordinary stools are not assumed stackable. |
| H1E-03 Ramp and platform | Arrange a box platform and panel ramp, ascend, retrieve and return. Wheels require continuous rolling support. A separate pre-positioned-ramp variant tests use, not construction. | Slope, width, wheel spacing, clearance, turning platform, overlap, traction and loaded braking. Front wheels reaching the platform while rear wheels hang, or an unloaded-only route, fails. No teleportation or assumed wheel climbing. |
| H1E-04 Same-color target and tools | At least two same-color boxes; the target has another visible identifier. Same-color supports differ in geometry, handles and ratings. Apply routes from 01/02/03. | Color is independent of role/capacity. Correct identity and usable support are separate requirements. A substitute box in D, an unreadable identifier treated as certain or memorized color-to-strength mapping fails. |
| H1E-05 Load limits and return | A return step/ramp carries the unloaded robot but not robot plus target. The working platform must carry the loaded robot, with a reachable target-rated transfer surface. Retrieve, unload there, descend empty, regrasp and deliver. | Include body, attachments and all supported objects, local contact forces and moments. Single-arm robots need independent support before releasing; unloading later cannot excuse overload during pickup. Retrieval without return, a weak transfer surface or overload fails. |
| H1E-06 Same body, different hands | Supports offer different handle widths, thicknesses and clearances. Compare both G1 hands in the same layout while selecting movable/pushable tools, preparing access and delivering. | Do not assume five fingers outperform three. Check closure, finger interference, friction and wrist moments; inspect pushing/cradling alternatives. Reachable IK without a stable grasp, cosmetic hand swaps or hidden welds fail. |
| H1E-07 Go1 whole-body retrieval | Initial arm reach is constrained. Reposition feet, change body height/pitch, grasp, retract/recover and transport. High-cabinet variants additionally require a validated broad platform/ramp; place the target down before changing footholds where necessary. | Support polygon, arm moment and total center of mass change together. Use configured perception, IMU and joint/load feedback. Fixed-base IK alone, unchanged unloaded gait after pickup or a posture with no recovery path fails. |
| H1E-08 Multiple-route selection | Box-plus-stool, multiple supports, ramp panels and transfer surfaces coexist with same-color distractors and load limits. Require two validated routes for the current configuration before calling an instance multi-solution. | Compare complete access, handling, stability and loaded return. Efficiency is secondary. With only one established route, label candidate selection. A fast overloaded route, becoming stranded or unjustified immediate exit fails. |

## 4. Four infeasibility controls

These are specifications to construct, **not established infeasibility certificates**. Bind labels to scene, body, hand, attachments and public rules at the initial state. Cover all legal combinations and alternatives, not one failed route.

| ID / related families | Required obstruction certificate | Feasible pair |
| --- | --- | --- |
| H1E-I01 / 02, 07 | Even a conservative maximum over legal supports and body postures cannot reach the required contact height; rule out other support, pulling, tipping and catch routes. | Change only support height or target shelf height and witness a full route. |
| H1E-I02 / 05, 08 | Every access, grasp, transfer and return route violates at least one necessary load condition. Ratings or safe observable responses must expose the obstacle. | Replace one limiting support or reduce target mass. |
| H1E-I03 / 03 | A mandatory raised platform has no adequate wheeled entry: all panels/combinations fail length, width, strength or overlap. Also exclude ground reach, torso adjustment and detours. | A valid ramp for the same robot; a different-body feasible comparison is a separate pairing. |
| H1E-I04 / 06 | The current hand cannot handle all necessary supports/target, including alternatives through pushing, cradling, reorientation, tools and environmental contacts. | Swap the hand on the same body, or change only grasp geometry; demonstrate full completion. |

Direct abstention permits observing then going to Q without touching task objects; failed attempts are not required. Hidden properties may require safe probes. Missing evidence, failed finite IK search, timeout and a weak controller remain `unknown`, not physical impossibility. An agent that destroys an initially feasible route cannot earn correct-abstention credit.

## 5. Exit contract and scoring

Proposed state machine: `active → retreating → abstained`, with separate `delivered / timed_out / invalid` terminal outcomes. Entering Q expresses exit intent. The trusted worker commits one terminal event after physical completion; a language declaration is unnecessary. If connected, existing `declare_infeasible` records intent/reason only and cannot bypass movement. This proposal does not change the current H1 API.

Q completion requires the full horizontal robot envelope inside Q, every load-bearing foot/wheel on legal ground, no held or suspended object, linear speed ≤0.03 m/s, angular speed ≤0.05 rad/s, stability for 3 s and no hard violation. These are draft thresholds to calibrate and freeze per configuration. Falling into Q, grazing it, reaching in with an arm, spawning there or missing logs fails. Delivery requires the correct target completely inside D, independently supported, released and stable for 3 s. Never backfill skipped stages.

| Initial trusted label | Valid delivery | Valid exit at Q | No completed exit / timeout |
| --- | --- | --- | --- |
| witnessed feasible | `task_success=1` | `task_success=0, false_abstention=true` | Failure / timeout |
| certified infeasible | Certificate contradiction; retain run and review label | `task_success=0, correct_abstention=true` | Missed abstention / exit failure |
| unknown | May establish a matching full witness after validation | `task_success=0, abstention_correctness=null` | Unknown label retained |

`screen_pass` is not witnessed feasibility. Certified infeasibility needs an additional necessary-condition certificate and scope; a route-level `rejected` result is insufficient. Keep the existing four-state screening ledger separate. Safe exit is an execution metric, not proof of correct impossibility judgment.

Report delivery on feasible episodes, correct abstention on infeasible episodes, false abstention on feasible episodes, exit execution success, unknown count, decision/exit time, probes and violations. Unknown labels do not enter feasible/infeasible denominators. Always abstaining scores zero on feasible episodes. Do not add retrieval-stage credit to abstention rewards or turn timeout into abstention. An optional aggregate is balanced decision success over both certified classes; omit it when either class is missing.

## 6. Difficulty, randomization and skill contracts

Preserve three layers: L1 contains only the objects necessary for one route; L2 adds tools unusable by this body but usable by a specified other body; L3 adds same-color and physically weak distractors. L2 requires evidence for both bodies, not assumptions from appearance/finger count. Keep targets and necessary objects fixed for the same seed, add objects cumulatively and recheck clearance/shortcuts. Family 04 is an L3 analysis slice, not another layer.

Family 08 has a separate `route_selection` track because simultaneously valid alternative tool sets do not meet strict L1 necessity. Infeasible controls have a separate `feasibility_decision` track. Report identical-world `matched_world` comparisons separately from capability-adjusted `body_scaled` comparisons. Explicit/partial/latent capability disclosure is an independent axis and never exposes scene truth.

Randomize shelf/target location, tool and Q positions, dimensions, grasp geometry, mass, friction, capacity and identifiers. Numeric ranges are null until calibrated. Color must not predict role/capacity, and Q must not predict feasibility. Record geometry rejection rates/reasons, including overlap and unreachable Q. Retain all prescribed evaluation failures, unknowns and timeouts; do not replace seeds. Keep development and sealed evaluation splits separate.

| Subtask | Entry → exit | Low-level/contact checks |
| --- | --- | --- |
| Observe | Initial scene → unique target and candidate evidence | Change view, read identifiers, safely probe; resolve ambiguity |
| Prepare | Candidate route → stable load-bearing structure | Push/grasp/lift/place/release; actual contact, overlap and deflection |
| Access | Stable ground → working pose | Weight shift and footholds, or wheel ramp motion; traction, clearance, drive force |
| Retrieve | Target supported by shelf → correct target held clear | Grasp/cradle, lift and retract; load and center-of-mass changes |
| Return | Working pose → ground delivery state | Transfer, release, empty descent, regrasp as needed; actual state continuity |
| Deliver | Held target → released and stable in D | Lower, confirm independent support, withdraw and dwell |
| Exit | Safely mobile state → empty and stable in Q | Stabilize/unload, retreat, stow, stop; no assumed safe recovery from arbitrary failures |

Generate physically valid standalone starts for curriculum evaluation, but never concatenate checkpoint fragments into a full witness. Draft diagnostic weights are Prepare 0.2, Retrieve 0.3 and Deliver 0.5, each credited once. Keep task success and abstention separate. A legal route bypassing tool preparation can succeed without receiving unperformed stage credit; reassess tool necessity.

## 7. Implementation and acceptance work

Target backend: Genesis. Freeze version, timestep/substeps, solver/contact settings, self-collision, each robot's source/license/hash/scale/inertia/controller and actual sensor configuration before execution. Prefer official robot and detailed object assets. Custom geometry for precise load or assembly behavior needs a recorded reason for not using higher-priority sources. Weak supports require physical deflection, instability or failure mechanisms, not a rigid prop with an arbitrary scoring penalty. Static mass ratings do not substitute for dynamic contact-force and moment checks.

Control-step, observation, token, reset, wall-clock and probe budgets remain null; do not launch solvers before budgets are declared. The difficulty hypothesis is that tool composition, contact transitions, hand limits and uncertainty require substantial coding-agent iteration; the guideline's four-hour target is unmeasured.

Suggested implementation order: 01/05 connect to H1; 03 adds wheels; 06 isolates hand changes; 02/04 add composition/distractors; 07 follows Go1 asset selection; 08 combines established routes. Predeclare representative configurations/routes/layers, skill checks, boundary negatives, reviewers and independent reproducers. A claimed task scope needs a generated continuous end-to-end success witness, without requiring full solutions for every random draw. Keep four-state results, check scope, budgets and evidence identity. Representative runs require at least three repeats and three scoring passes per episode; remaining sample counts/tolerances are pending.

Seven attack groups must be covered: privileged truth/certificate access; world modification or teleporting into Q; penetration/welds/contact energy exploits; wrong identity, single-frame or fallen-in-region triggers; repeated exit or stage-reward farming; cross-episode seed/color memorization; and shortcuts through ground reach, tool combinations or load transfer. Reward legal alternatives and revise route labels; prohibited methods require explicit public or physical constraints. These negative cases are designed, not executed.

Human review must check identity and complete region containment, actual support, loaded return, damage/overload/hidden attachments, Q movement and dwell, certificate coverage of alternatives, and matching recording/source/asset/log identities. This directory and its machine-readable cards are author-side materials and must be excluded from agent bundles.

## 8. Current family boundaries and historical cooperative proposal

[Current H1 / M1 / M3 overview](../task-families-en.md) · [Conditional M3 design](../m3-extension/README-en.md). H1 now prioritizes single-step ascent, foothold-sequence selection and light-payload balance/return. The former H1E-09–14 cooperative supplement is reclassified and no longer counted as active H1 tasks; the original eight entries and four controls retain their IDs. New M3 lifting requires auditing the current 2 kg constraint and a compatible lightweight partner; humanoid carrying is excluded. The [old proposal](cooperative-tools-en.md) is historical only.
