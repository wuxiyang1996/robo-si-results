# H1: 22 selected independent tasks

<!-- implementation-authorization -->
**Implementation update · 2026-10-27:** The user has authorized Gamma GPU and sub-agent implementation with physics validation. Earlier zero-run/paused statements below describe the design snapshot, not current authorization. See [requirements](implementation-status-en.md) and the [execution ledger](execution-progress.json) for current scope, budgets and retained failures. Candidate plans are not measured trajectories; original scores and formal admission do not change automatically.
<!-- /implementation-authorization -->

2026-10-27 · **20 tasks from existing scene splits plus two new operations: 22 total.** No additional easy common-feasible two-body/two-hand calibration tasks. Each task owns its scenes, episodes, scoring and acceptance. Former H1S-07/10/11 are groups and are not counted alongside their children.

[中文](selected-scope.md) · [JSON](selected-scope.json) · [Historical 12 registrations](archive/selected-12-20261027/selected-scope.json)

**The benchmark does not require a unique solution.** Judge goals and public constraints; accept every legal complete route, including direct retrieval, regrasping, tool combinations or alternative supports. Reference traces are not hidden success conditions. Retain legal success and revise tool-necessity, transfer-necessity or infeasibility labels when contradicted. Historical reference scoring retains its original scope. Zero new simulations; new scenarios remain unknown.

## 1. Current 22 registrations

| ID | Independent task | Origin |
| --- | --- | --- |
| H1S-01 | Frozen G1/Dex3 baseline | Retained |
| H1S-02 | G1 five-finger handling | Retained |
| H1S-03 | Wheels and movable ramp | Retained |
| H1S-04 | A3 retrieval | Retained |
| H1S-05 | G1 two tiers / A3 one tier | Retained |
| H1S-06 | Infeasibility and physical exit | Retained |
| H1S-07.P1 | Push clear and retrieve | Promoted scene |
| H1S-07.P2 | Push a support into place | Promoted scene |
| H1S-07.P3 | Turn or change pushing side | Promoted scene |
| H1S-07.P4 | Push a target that cannot be lifted | Promoted scene |
| H1S-08 | Stretch handled box | Retained |
| H1S-09 | Stretch infeasibility and exit | Retained |
| H1S-10.A | G1 support selection | Promoted scene |
| H1S-10.B | A3 support selection | Promoted scene |
| H1S-10.C | Wheeled platform and ramp choice | Promoted scene |
| H1S-10.D | Stretch work/transfer surface choice | Promoted scene |
| H1S-11.A | Directly reachable retrieval | Promoted scene |
| H1S-11.B | Tool-enabled complete retrieval | Promoted scene |
| H1S-11.C | No feasible route including tools; exit | Promoted scene |
| H1S-12 | Same-color identification | Retained |
| H1S-13 | Autonomous transfer and safe return | New operation |
| H1S-14 | Body adaptation in a narrow workstation | New operation |

The existing directly reachable H1S-11.A remains within the accepted 20-task split; no extra common-feasible calibration tasks are added.

## 2. Establishing the hand and stair comparisons

The hand candidate is grounded in the existing [Dex3 side-carry record](../../../humanoid/g1_support_retrieval/solution/side_carry/README.md): eight attempts failed that experiment's complete criterion, with slip, contact loss and low/wide workspace issues. The [underhand record](../../../humanoid/g1_support_retrieval/solution/underhand_lift/README.md) also reports support-span and thumb-interference problems. These are local observations under particular settings/controllers, not impossibility proofs for all three-finger grasps; no five-finger result exists here.

First probe grasping at a height in both hands' good arm workspace, then validate complete support placement and retrieval from the actual start. Freeze object geometry/mass/friction, body, goal, sensor access and tuning/compute budgets. Allow appropriate hand-specific controllers instead of replaying the other hand's joints. Record hand/mount inertia, collision geometry and real actuator limits; do not invent favorable friction or hidden attachments. Compare repeated success, slip, load margin, regrasp count and completion time—not one success against one failure.

The [official Dex3-1 specification](https://www.unitree.com/mobile/Dex3-1/) describes three fingers and seven degrees of freedom; the wristless [Inspire RH56DFX specification](https://en.inspire-robots.com/product/rh56dfx/) lists five fingers and six degrees of freedom. Finger count alone therefore does not determine dexterity, load or geometric capability. RH56DFX is not selected as the final model here, and vendor load claims under different test conditions are not compared.

For the stair pair, screen cabinet heights where G1's effective one-tier reach is insufficient and two tiers have a candidate solution, while A3 cannot work from the floor but has a one-tier candidate. Effective reach includes the required grasp pose and cabinet depth, not the highest fingertip point. Then validate step area, ascent entry, assembly reach, load, retrieval and descent. Screening is not a full witness. Keep the world identical; replacing the complete robot compares overall embodiment and does not isolate height as the sole cause.

## 3. Four pushing subcases

| Subcase | Scene and objective | Embodiment checks |
| --- | --- | --- |
| P1 Clear access | Push a blocking box into a side parking region, then complete cabinet retrieval. | Contact height, force/friction, usable cleared space and body-specific posture. |
| P2 Position a platform | A box is pushable but hard to lift. Position it at the cabinet; legs require validated ascent, wheels also need a ramp. | Functional placement tolerance, traction, capacity and loaded return. |
| P3 Turn or change side | Straight pushing hits an obstacle; reposition contact without losing access to the next push. | Swept body/arm/box clearance and an actual route to change side. |
| P4 Cannot lift, can push | A target box exceeds lifting capability but can be pushed under control to ground region D; pair handled and handleless versions. | Reject the inference that inability to lift implies failure; validate propulsion and stopping with every legal delivery method allowed. |

P4 is an auxiliary ground-transport variant, not high-cabinet retrieval. Report identical-world comparisons separately from body-scaled geometry/mass comparisons; changed worlds cannot be described as changing only the body.

## 4. Added operations and scope decisions

- **H1S-13 Autonomous transfer and safe return:** choose direct loaded return, intermediate placement or any other legal complete route. A transfer surface is available but its use is not instructed. Establish transfer necessity with evidence, not reference-trace imitation.
- **H1S-14 Narrow-workstation body adaptation:** start with approach/turning clearance for robot, tool and target. Compare stance, orientation, support placement and withdrawal in matched worlds. No complex crouching/crawling requirement or assumed larger-body disadvantage.
- Route switching remains within existing tasks; no forced initial failure or duplicate generic replanning task.
- Do not add common-feasible hand/body calibration tasks.
- Go1 with an arm is deferred pending model, inertia and controller integration; outside the 22 tasks.

Screen objects/tools against the current 2 kg manipulation ceiling, while platforms support actual robot/attachment/payload weight. For H1S-13, audit loaded pose, descent clearance and dynamic stability rather than fabricating necessity with a finely tuned whole-body capacity threshold. H1S-14 feasibility comes from actual geometry and complete routes, not robot names. Parameters, budgets and witnesses remain pending.

## 5. Difficulty and readiness

Operational structure progresses from single-tool preparation to composition and route selection. Infra still uses only L1 necessary tools, L2 tools usable by another body but not the current one, and L3 distractors. Two stair tiers can be L1; five-finger performance gains do not automatically establish L2; same-color additions alone do not establish full L3. Abstention is a separate feasibility track. Distinguish candidate selection, demonstrated multiple solutions, required composition and embodiment adaptation.

Only historical H1 has full witnesses within its frozen scope. New choices still need frozen assets, ranges, thresholds, budgets and representative samples; new-scene feasibility remains `unknown`. Q dwell/velocity conditions inherit the extension draft and need runtime integration/calibration. This record does not resume simulation or change existing scores/admission.

## 6. H1S-10: multiple boxes and embodiment-specific scenes

The common goal is to use available objects for retrieval, return and delivery. Provide several tall and short boxes, optionally differing in top area, handles, mass and capacity. Separately assess access, useful height, ability to relocate and loaded return; the tallest box is not necessarily best. Boxes begin away from the working position and must be carried or pushed into place when needed.

| Scene | Body and layout | Selection behavior to inspect |
| --- | --- | --- |
| H1S-10.A Multiple box heights | G1; several boxes including accessible-but-too-low, sufficiently tall but beyond direct step access, too-narrow tops, and a candidate supporting a complete route. | Select a movable, accessible, sufficiently high support with a valid return, then place it and complete retrieval. Actual usability requires calibration. |
| H1S-10.B Same world, A3 | First retain A's cabinet, boxes, target and poses while changing to A3; separately identify A3-specific layouts. | The same box may have different usefulness: A3 might use a lower box or face different step/clearance constraints. Record actual choices without requiring them to differ. |
| H1S-10.C Wheeled platform selection | Multiple box platforms and a movable ramp, with varying heights, platform areas, overlap and placement geometry. | Select a continuous wheel-access route with sufficient base and working-pose space. Relocate boxes/ramp when needed, then complete loaded return. Do not assume wheels can climb a vertical box edge. |
| H1S-10.D Stretch-accessible box selection | Several box heights and handle locations provide candidate transfer/work surfaces; any platform-ascent variant also needs a validated ramp. | Choose boxes that the gripper, single arm, lift and base can position and use for the full task. Report transfer-surface and platform-ascent episodes separately; do not require assumed box climbing by Stretch. |

H1S-10.A–D are independent task registrations; H1S-10 is a non-scoring group. Label identical-world body comparisons `matched_world`; separately label geometry adapted to a body `body_specific_scene`. Do not attribute results entirely to embodiment when the world also changed. The first batch does not require every body crossed with every layout.

Start with height and top-area choices, then add relocation, load and return constraints. This internal complexity does not automatically assign infra L1/L2/L3. Freeze dimensions, mass, friction, capacity and usability labels only with actual body profiles and observable evidence. Accept legal combinations of boxes, grasps or routes; one unusable box does not imply global infeasibility. Establish a full route witness for an ordinary completion scene; score deliberate infeasibility pairs separately. Unverified candidates do not justify an expected Q exit.

Record chosen boxes, physical placement, genuine support, correct-target delivery and a stable returned robot. Selecting an intended box ID or merely reaching its top is insufficient. Cooperation is not required here; historical M3/cooperative H1E-10 evidence does not establish this task. A–D remain design scenes with `unknown` feasibility and no new physics runs.

## 7. H1S-11: tools must be physically operable

Validate tool functionality separately from whether the assigned robot can operate it. Different bodies may have different tool usability, but a candidate cannot be only a visual prop without its mechanism or support function implemented. An ordinary feasible scene needs at least one body/target-compatible tool with a complete retrieval, withdrawal, transport and release witness; other candidates need not all be usable by that body.

| Tool | Required physical operation | Insufficient evidence or invalid behavior |
| --- | --- | --- |
| Short/long hook | Hold the handle, engage a visible compatible ring/edge, pull under control in an effective direction, then disengage or transfer. | Binding on proximity, assuming a ringless target is hookable, cabinet collision or excessive loaded wrist moment. |
| Manual long-handled gripper | Stabilize the handle while pressing/moving real controls; a physical transmission operates the remote jaws, maintains grip and permits release. | Holding the shaft without operating the trigger, exceeding trigger stroke/force, or bypassing the handle with a hidden remote-jaw command. |
| Tray/support tool | Grasp usable geometry, place the tray under the target, establish real support, preserve loaded orientation and transfer/place the target. | Attaching the target to the tray, unloaded-only stability, or a single arm having no hand or independent surface for the next transfer. |

An electric gripper must explicitly declare the device model, real actuator, power/communication and publicly permitted control interface in a separate protocol. Never silently motorize a passive tool. Declare actual sensors and observable handle stroke/force; agents do not receive hidden operability labels.

Check the chain: approach/grasp handle → actuate or engage → extract under control → withdraw and maintain loaded stability → place/release. Validate closure/interference, required fingers/hands, operating force/stroke, wrist and body load, swept clearance and support after release. A single arm unable to hold a tool and receive the target simultaneously needs a real independent transfer surface or viable action sequence. Dimensions, masses, forces and tolerances remain to be calibrated.

First validate a simple passive hook with a compatible target interface, then consider manual grippers after mechanism and robot-operation validation. Add trays for actual transfer needs. Keep tool-by-body evidence separate; merely picking up a tool, static IK, or directly commanding jaws from a privileged controller does not establish operability. Tool-use stages require real functional interaction. If an open task permits another legal route, score its final physical goal and record separately whether tool use occurred.

These operation checks apply to the independently registered H1S-11.A–C tasks. New tool-operation capabilities remain `unknown`; no new simulations or passing claims.

## 8. H1S-11: tools enable a previously infeasible task

The primary comparison keeps the robot, target and world fixed: the task is infeasible without assistive tools, but a physically operable tool enables complete retrieval and delivery. Prioritize a Stretch deep-cabinet retrieval candidate. Merely speeding up an already feasible action or lifting a tool is insufficient. This is a design hypothesis with no new physical evidence.

**Primary Stretch scene.** A box sits deep inside a cabinet with a visible hook ring and a handle for subsequent grasping. Fixed cabinetry or a barrier limits base approach, with no side or rear bypass. Its height permits grasping after retrieval, but its initial depth lies beyond direct grasp from every legal base position and arm posture. Provide a stable receiving surface at the cabinet front and a nearby tool parking surface. Calibrate mass, friction, ring/handle geometry, tool length and wrist loads against the actual model; assume no numerical Stretch capability.

Sequence: acquire hook → engage ring → pull the box along the shelf into a reachable supported region → stabilize and disengage → put down the hook → grasp the box handle with the same gripper → transport and deliver. The box remains physically supported throughout; pulling it off the shelf is not success. The single arm need not hold hook and box simultaneously. A short hook may not reach, a suitable longer hook may work, and an excessive length may prevent turning or exceed wrist limits. Establish each label through geometry and dynamics.

| Paired scene | Expected relationship without / with tools | Evaluation purpose |
| --- | --- | --- |
| H1S-11.A Direct retrieval | Place the same target nearer; direct grasp succeeds. | Easy control for basic execution; direct completion is allowed. |
| H1S-11.B Tool enables completion | Place the target deeper; every legal tool-free route is infeasible, while at least one operable tool enables full delivery. | Primary capability-extension pair: change only tool availability between matched runs; retain world, body, target, permissions and budgets. |
| H1S-11.C Tools still insufficient | Minimally change the bottleneck, for example deepen the target beyond engagement by every available tool, and exclude all other legal routes. | Genuine infeasibility control; put down tools and enter Q empty-handed and stable; report separately from B. |

H1S-11.A–C are now independent tasks; H1S-11 is a non-scoring group. Never count an episode again under H1S-09.

**Evidence required.** Do not manufacture tool-free failure by disabling otherwise legal actions. Audit base repositioning, bypasses, alternative grasps, pushing and other available objects. A failed attempt or exhausted search budget is not infeasibility evidence. Establish the geometric/physical bottleneck, retain a continuous tool-assisted success witness from tool acquisition through final release and delivery, and record repeat outcomes. Accept any discovered legal tool-free solution and remove the capability-extension label from that scene. Report complete task success rates for both conditions, feasibility evidence, actual tool effect and correct abstention, not merely contact or pickup. Every new scene remains `unknown` until both sides of the comparison are established.

<!-- p4-development-boundary -->
**First P4 development binding:** Existing G1 + Dex3, a 5 kg floor-supported target and a public 2 kg lifted-payload limit; ground-supported pushing is allowed. This tests delivery when lifting is disallowed by the public rule, not an absolute physical inability to lift 5 kg. Dimensions, friction, D, budgets and three repeats are recorded in the [frozen profile](../../../humanoid/g1_support_retrieval/extension/p4-development.json). Handled pairing, other masses and bodies remain unverified. Score physical goals and public constraints; do not require two-hand pushing or a particular reference phase.
<!-- /p4-development-boundary -->
