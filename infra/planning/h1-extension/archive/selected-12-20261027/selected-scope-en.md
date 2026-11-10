# H1 extension: user-selected scope and missing controls

2026-10-27 · **Selection record; new scenes still require implementation and physical validation.** This selection replaces the assistant's earlier first-batch recommendation without deleting the candidate catalog or historical evidence. Preserve the user's original numbering; no item 4 was supplied. As confirmed by the user, **all 12 entries are independent tasks within the H1 task family**, including A3 and same-color distractors. Each gets its own scene specification, evaluation episodes, scores and acceptance record; assets and control skills may be shared. Historical counts for the established 14-task benchmark remain unchanged.

[中文](selected-scope.md) · [Structured record](selected-scope.json) · [Base design](README-en.md) · [Cooperative design](cooperative-tools-en.md). New simulations: 0. Selected means in design/implementation scope, not admitted for formal evaluation.

## 1. Recorded selection

| Registration ID / original item | Selected scene | Mapping and evidence boundary |
| --- | --- | --- |
| H1S-01 · 1 Original | Original G1 + Dex3 stool retrieval, transfer, descent and delivery. | Original H1 frozen baseline. Existing evidence retains its assets, controller, physics and scoring; it does not establish new hands, Q exit or full-footprint delivery. |
| H1S-02 · 2 G1 with five-finger hands | Same G1 body with five-finger hands; find a scene harder for three fingers and easier for five. Primary candidate: moving a broad handleless box into a retrieval support position. | H1E-06. Test contact geometry, underhand support span and stable transport. Exact Inspire model pending; superiority is a hypothesis. |
| H1S-03 · 3 Wheels + ramp | First carry or push an initially unpositioned movable ramp to the designated location, align it with the working platform and leave it stable; then ascend, retrieve, return loaded and deliver. | H1E-03. Physical ramp placement is a required task stage; validate endpoint support/overlap, slope, traction and loaded return. The ramp begins outside the placement region; moving an assembled ramp is not panel construction. First wheel model remains open; Galaxea R1 is an existing candidate. |
| H1S-04 · 5 A3 | Run matched high retrieval worlds with A3 and G1; compare reach, posture, load and support choices. | Independent A3 retrieval task; matched worlds support G1 comparison while results remain separately recorded. Exact A3 version, hands, assets and controller remain open. |
| H1S-05 · 6 Two stair tiers versus one for A3 | Same cabinet, target, support pieces and poses: G1 needs two tiers while A3 needs one; both return completely. | H1E-02 plus H1E-14 comparison. Prefer actual successive foothold surfaces; vertically stacked stools are a separate structure variant. Establish G1 one-tier insufficiency/two-tier success and A3 ground insufficiency/one-tier success. |
| H1S-06 · 7 Infeasible case | Reach or necessary load conditions rule out all legal routes; the robot may observe then go directly to Q. | H1E-I01/I02, paired with a feasible scene changing one bottleneck. Timeout/search failure remains unknown. |
| H1S-07 · 8 Pushing across embodiments | P1 clear access; P2 position a support/platform; P3 turn or change contact side; P4 cannot lift but can push. | Variants of H1E-01/03/08. Compare G1, A3 and a wheeled body first, then Stretch, subject to individual contact-height, force, braking and turning validation. |
| H1S-08 · 9 Stretch + handled box | Grasp a visible handle to place a support box or retrieve a target box, then complete delivery; explicitly distinguish the box's role. | Independent task H1S-08, keyed `stretch_handle`, using H1E-06/10 design references. Validate aperture, wrist clearance, load moment and orientation. Exact Stretch version remains open. |
| H1S-09 · 10 Stretch abstention | All routes fail because of grasp, reach, load or entry limits; physically enter Q, empty-handed and stable for 3 s. | Independent task H1S-09, keyed `stretch_abstention`, related to H1E-I01/I03/I04. A missing handle alone does not prove impossibility; audit pushing, cradling, reorientation, ramps and long tools. |
| H1S-10 · H1E-10 | Select among multiple tall and short boxes: some are accessible but too low, some tall enough but inaccessible, and others have unsuitable top area or capacity. Choose for the current body, carry or push into position, retrieve, return and deliver. | H1S-10 uses a single-robot support-selection protocol; lifting a partner is not required. Keep the old cooperative H1E-10 only as a historical design reference. Prepare G1, A3, wheeled and Stretch scenes, retaining some identical worlds for embodiment comparisons. |
| H1S-11 · H1E-12 | Tools extend capability: prioritize a Stretch deep-cabinet scene infeasible directly but feasible with an operable tool. Assess whether the current body can grasp, actuate, control forces and release each short/long hook, gripper or tray, then choose a tool that actually completes retrieval and delivery. | Tools must have physical functionality; holding one does not establish operability. Hooks need real engagement, manual grippers need physical handle operation, and trays need real support. Validate loaded withdrawal and release; no hidden grasp/binding API. |
| H1S-12 · H1E-04 | Same-color target/tool distractors, resolved by identifiers/patterns and spatial relations; color does not predict role or capacity. | Independent same-color identification/retrieval task with its own goals, scenes and scores; other tasks may supply reusable action chains. Strict L3 still requires valid cumulative L2; otherwise leave the tool layer unassigned without changing task independence. |

`H1S-01–12` are independent registration IDs for the selected tasks. Existing H1E IDs remain design references, preserving the earlier catalog. P1–P4 are subcases of H1S-07, not additional top-level tasks in this revision. Bind each evaluation episode to its task ID and scene version; do not count one rollout repeatedly in aggregate denominators.

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

## 4. Control coverage and remaining recommendations

1. **Switch route instead of abstaining. Tool-assisted retrieval is now included in H1S-11 (section 8); other cases remain recommendations.** Stretch cannot grasp the body but can use a handle, cannot lift but can push, or cannot reach directly but can use a ramp/tool. Pair this with genuinely all-route-infeasible cases. Highest priority; reuse P4 and H1E-11/14.
2. **Pickup succeeds but loaded return fails.** The working platform supports robot plus target while the return ramp supports only the unloaded robot; transfer before descent. H1E-05 addresses changed-load planning without permitting overload during pickup.
3. **The larger body can also be disadvantaged.** Complement A3's one-tier advantage with low overhead clearance or a narrow turning region where another smaller body might succeed. Both capabilities require validation; avoid teaching that larger is always better.
4. **Easy common feasible controls.** Both hands can use a handled box, or both bodies can use a low one-tier support. Pair these with boundaries to distinguish capability differences from an untuned controller.
5. **Resolve quadruped coverage.** Go1 + arm was in the original support target but is not explicitly reselected here. Retain it as a candidate, neither silently dropped nor automatically included in the first batch. Five-platform coverage would require leg–arm and loaded-mobility comparisons after selecting the arm.

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

These are scene variants within H1S-10, not additional top-level tasks. Label identical-world body comparisons `matched_world`; separately label geometry adapted to a body `body_specific_scene`. Do not attribute results entirely to embodiment when the world also changed. The first batch does not require every body crossed with every layout.

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

This refines H1S-11 without adding a task. New tool-operation capabilities remain `unknown`; no new simulations or passing claims.

## 8. H1S-11: tools enable a previously infeasible task

The primary comparison keeps the robot, target and world fixed: the task is infeasible without assistive tools, but a physically operable tool enables complete retrieval and delivery. Prioritize a Stretch deep-cabinet retrieval candidate. Merely speeding up an already feasible action or lifting a tool is insufficient. This is a design hypothesis with no new physical evidence.

**Primary Stretch scene.** A box sits deep inside a cabinet with a visible hook ring and a handle for subsequent grasping. Fixed cabinetry or a barrier limits base approach, with no side or rear bypass. Its height permits grasping after retrieval, but its initial depth lies beyond direct grasp from every legal base position and arm posture. Provide a stable receiving surface at the cabinet front and a nearby tool parking surface. Calibrate mass, friction, ring/handle geometry, tool length and wrist loads against the actual model; assume no numerical Stretch capability.

Sequence: acquire hook → engage ring → pull the box along the shelf into a reachable supported region → stabilize and disengage → put down the hook → grasp the box handle with the same gripper → transport and deliver. The box remains physically supported throughout; pulling it off the shelf is not success. The single arm need not hold hook and box simultaneously. A short hook may not reach, a suitable longer hook may work, and an excessive length may prevent turning or exceed wrist limits. Establish each label through geometry and dynamics.

| Paired scene | Expected relationship without / with tools | Evaluation purpose |
| --- | --- | --- |
| H1S-11.A Direct retrieval | Place the same target nearer; direct grasp succeeds. | Easy control for basic execution; direct completion is allowed. |
| H1S-11.B Tool enables completion | Place the target deeper; every legal tool-free route is infeasible, while at least one operable tool enables full delivery. | Primary capability-extension pair: change only tool availability between matched runs; retain world, body, target, permissions and budgets. |
| H1S-11.C Tools still insufficient | Minimally change the bottleneck, for example deepen the target beyond engagement by every available tool, and exclude all other legal routes. | Genuine infeasibility control; put down tools and enter Q empty-handed and stable; report separately from B. |

These are H1S-11 scenes, not additional independent tasks; do not count an episode again under H1S-09. A/B/C are feasibility controls, not infra L1/L2/L3 difficulty levels. Start B with one usable passive hook, then add short/suitable/overlong candidates and mechanism-operation requirements. More candidates alone do not establish a higher tool layer. Later replace Stretch with G1/A3 or another body in the identical world and observe whether tools remain necessary; do not assume a larger body succeeds directly.

**Evidence required.** Do not manufacture tool-free failure by disabling otherwise legal actions. Audit base repositioning, bypasses, alternative grasps, pushing and other available objects. A failed attempt or exhausted search budget is not infeasibility evidence. Establish the geometric/physical bottleneck, retain a continuous tool-assisted success witness from tool acquisition through final release and delivery, and record repeat outcomes. Accept any discovered legal tool-free solution and remove the capability-extension label from that scene. Report complete task success rates for both conditions, feasibility evidence, actual tool effect and correct abstention, not merely contact or pickup. Every new scene remains `unknown` until both sides of the comparison are established.
