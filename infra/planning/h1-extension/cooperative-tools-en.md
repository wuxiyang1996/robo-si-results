# H1 extension: cooperative retrieval, tool choice and physical abstention

> **Superseded; no longer counted as active H1 tasks.** Use the [family overview](../task-families-en.md) and [conditional M3 design](../m3-extension/README-en.md). The historical counts, nine-cell plan and routes not screened against the current 2 kg constraint below are not active commitments.

2026-10-27 · **Design proposal; no implementation or new simulation.** These tasks belong to H1 extension. M3 supplies historical contact-chain reference only. Six new families **H1E-09–14** and three controls **H1E-I05–I07** supplement the original eight families and four controls: **14 extension families and seven controls**, separate from the established 14-task benchmark inventory.

[中文](cooperative-tools.md) · [Structured cards](cooperative-tools.json) · [Original extension](README-en.md) · [Infra difficulty policy](../../task-design-en.html#layers) · [Historical M3 scope](../../m3-current-evidence.json). Inherit the original observation isolation, randomization, budgets, assets, seven attack categories and layered acceptance requirements. Every new configuration remains `unknown`; there are no new success witnesses or infeasibility certificates.

## 1. Shared goal and two protocols

Public instruction for open solving:

> Put the visibly identified target from the elevated container into ground tray D, release it and leave it stable. All robots must finish independently stable on the ground with no mutual carrying support. Respect public load and operating limits. If you judge that the current robots and available objects cannot complete the task, you may skip manipulation attempts and move all robots to their marked bays in exit region Q, empty-handed, without mutual support, and remain stationary for 3 seconds.

Freeze each ball or box `target_profile` separately, including collision geometry, mass, grasp requirements and evidence. A ball witness does not validate a box. Q has body-sized Q-A/Q-B bays, separated from D, spawn and ordinary transport paths. Validate access and simultaneous parking for both bodies at initialization; randomize Q independently of feasibility.

A separate **cooperative execution** protocol requires lifting, supported retrieval, regrasping and lowering. Its required phases cannot be replaced by direct retrieval. The **open solving** protocol prescribes no tool or lifting route and accepts legal single-robot solutions. Two robots in the scene do not establish that cooperation is necessary. Execution-protocol infeasibility does not establish open-protocol infeasibility.

## 2. Scene structure and robot combinations

Infra reserves L1/L2/L3 for cumulative tool layers. Record the proposed operational structures separately as S1/S2/S3.

| Structure | Layout and decision | Tasks |
| --- | --- | --- |
| S1 Prepared cooperative workstation | Support box, carrying access and cabinet approach ready; execute the complete return chain | H1E-09 |
| S2 Construct a workstation | Select and position supports; retrieval and return-carry poses differ | H1E-10 |
| S3 Select or change a body-dependent route | Direct reach, partner lift, ramp and long tools are candidates | H1E-11–14 |

| Pair ID | Initial candidate | Measurements required |
| --- | --- | --- |
| C1 | G1 + X5; hand and support interface pending | Lift, independent box support, loaded regrasp and ground handoff |
| C2 | Another dual-arm humanoid + the same X5; model pending | Reach, dual-arm load, carrying height, stance and clearance |
| C3 | Wheeled dual-arm robot + the same X5; model pending | Base approach/turning, torso workspace, loaded stability and ramp placement |

The first comparison has **three scene structures × three pairs = nine design cells**. Also record task, seed, protocol and target profile. Hold X5 fixed initially; C1 does not automatically inherit M3 evidence. Other operators and an arm-equipped quadruped are later candidates. Robot names establish neither carrying capacity nor X5 ramp capability.

Strict L1 has only necessary tools; L2 adds tools unusable by the current body but evidenced usable by another; L3 adds observable distractors. Hold target, necessary tools and poses fixed across layers for a seed. Multiple effective routes, direct-reach cases and deliberate infeasibility use separate tracks rather than claiming strict L1. S3 is not L3, and switching to shorter arms does not relabel scene structure.

## 3. Six additional families

These are author-side candidate routes. Every completion requires delivery and both robots independently on the ground without mutual support.

| ID / task | Scene and tools | Candidate complete route and observations | Paired change and negatives |
| --- | --- | --- | --- |
| H1E-09 Prepared cooperative retrieval | Positioned support box, X5 carrying surfaces, elevated container, D and Q; S1 | Inspect interfaces → lift → independent box support → retrieve → stow/align → regrasp → lower → withdraw → deliver. Observe contacts, poses and configured load feedback. | Execution baseline; open solving may use direct reach. Negatives: continuous suspended picking claimed as box support, correct height without ground loading, or partner left elevated. |
| H1E-10 Select and place a support | Tall narrow, low broad and adequately high/load-rated candidate boxes, initially unpositioned; S2 | Inspect dimensions, handles and visible ratings; compare target depth and return clearance; select, move and place support, then execute 09. Audit stacking alternatives. | Change only carrier reach/carrying height in the same world. Negatives: tallest box tips, support blocks return regrasp, or prepositioned support counted as autonomous placement. |
| H1E-11 Lift or ramp | Stable platform, boards of different lengths/widths, carrying interface; direct reach may also exist; S3 | Lift-and-support route, or place board → verify overlap → X5 ascends → retrieves → descends loaded → delivers, or either robot retrieves directly. Observe reach, ratings, board geometry, wheel spacing and safe probes. | Reduce carrier lift capability while preserving a complete ramp alternative. Negatives: immediate abstention after rejecting lifting, unloaded-only ramp proof, or unverified board joining. |
| H1E-12 Choose a long retrieval tool | Short hook, long hook, long-handled gripper, shallow tray, supports; deep target with observable interfaces; S3 | Hook a compatible ring/edge and draw target into grasp range, use an operable gripper, or change workstation and grasp directly; return and deliver. Check handle closure, wrist moment, swept clearance and retention. | Change hand closure or tool operation capability only. Negatives: assume a ringless target is hookable or tool names imply compatibility. Accept legal combined extensions if discovered. |
| H1E-13 Ramp, platform and tool composition | Boards, platform, long gripper/hook and transfer tray; ground-level tool reach and bare-hand platform reach each insufficient; S3 | Build access → bring usable tool → ascend/stabilize → retrieve with tool → independently transfer target → stow tool/reposition → recover target → return/deliver. A single arm needs real placement support. | Construct necessity controls removing platform or compatible long tool, auditing other combinations. Negatives: tool occupies the only hand needed for ramp work, unreachable transfer placement, hidden target/tool fixation. |
| H1E-14 Change plans after a body change | Same cabinet, target, supports, boards, long tools and poses as 11/12; S3 | Long reach may enable direct retrieval; another profile may lift; insufficient payload may require a ramp or long tool. Screen from observable geometry and safe probes; replan from the actual state after contrary evidence. | Change one capability at a time and bind all remaining world/body parameters. A witnessed alternative is required for an expected route switch; all-route exclusion is required for expected abstention. Negatives: replay old actions after body change or treat final success alone as self-modeling evidence. |

Distinguish `candidate_selection`, `multiple_feasible_routes` (at least two complete witnesses for the same configuration) and `tool_composition`. None of the new configurations currently has validated multiple effective routes.

## 4. Three additional direct-to-Q controls

| ID / parents | Proposed obstruction and observable evidence | Minimal feasible pair |
| --- | --- | --- |
| H1E-I05 / 11, 13, 14 | Conservative bounds exclude both robots' direct reach, legal supports/stacks, partner lifting, all board combinations and long tools. Geometry is visible; audit pulling/catching, detours and fixed-cabinet alternatives. | Replace one board or tool and witness a complete route. Sufficient observable evidence permits no manipulation before exiting. |
| H1E-I06 / 10, 11, 13 | Carrier cannot safely lift the partner; platforms/ramps cannot support the required combined loads; direct and tool routes also lack a valid load/return path. Ratings or safe physical responses must make the distinction observable. | Replace one load-bearing item or one public capability limit; validate access, retrieval, transfers and return. Rejecting partner lifting alone is insufficient. |
| H1E-I07 / 12, 14 | Neither hand can control the target, hooks cannot engage and grippers cannot be operated; exclude pushing, cradling, tilting, environment-assisted regrasp and legal combinations. Interfaces are visible or safely probeable. | Replace one end effector or compatible tool and witness completion. Color alone cannot change feasibility. |

These are **certificate specifications, currently unknown**. Bind certificates to initial state, robot/tool/controller versions, public rules, covered alternatives and observable evidence; distinguish physical obstructions from public operating constraints. Search timeout, one controller failure or one rejected route is insufficient. Dangerous overload attempts are unnecessary; observation alone may justify immediate retreat.

## 5. Joint exit and capability-adaptation scoring

Intent starts `active → retreating`; commit `abstained` only when **all robots simultaneously satisfy the predicates for 3 seconds**. Each complete horizontal body envelope must be inside its own Q bay, feet/wheels independently supported by legal ground, with no held/suspended object or mutual support and stable posture. Draft speed bounds remain 0.03 m/s and 0.05 rad/s, pending per-body calibration. One robot arriving, carrying a partner into Q, falling, a one-frame pass or stopping outside is insufficient.

After interaction starts, establish legal independent support for the partner and payload before releasing and retreating. Arbitrary failures are not assumed recoverable; unsafe or incomplete exits remain failures, without teleportation/reset. Neither prior task-object manipulation nor a verbal declaration is required.

Use the existing extension's separate denominators: exiting a witnessed-feasible episode is `false_abstention`; exiting a certified-infeasible episode is `correct_abstention` with `task_success=0`; unknown correctness is null. Timeout is not abstention, and destroying an initially feasible route earns no correct-abstention credit. Draft delivery dwell is 3 seconds with both robots stable; historical M3's 2-second rule remains untouched.

Record timestamped route acceptance/rejection and evidence, first choice, probes, revisions and time. Report switching when the old route is unavailable and a witnessed alternative remains, false abstention, correct abstention and physical exit success. Matched worlds with one changed capability provide the comparison; verbal rationale or delivery success alone does not establish self-modeling. Keep author labels and certificates out of agent bundles.

## 6. Refinement evidence and implementation work

Map high-level goals to contact actions and actual trajectory segments. Placing a partner on a box requires alignment, supported lift, box contact, load transfer and withdrawal, verified by actual support/forces. Return regrasp starts from the actual loaded pose and checks cabinet/wrist clearance, preload, lift-off and ground handoff. Pass actual poses, velocities, contacts, loads and remaining budgets across phases; never stitch ideal checkpoint states into a full witness.

Historical M3 covers fixed hooks-v0.1, a 65 mm ball and box-supported retrieval. It does not validate autonomous support choice/placement, new bodies, ramps, long tools or Q exits. Preserve its evidence scope rather than registering it as a new extension witness.

Order: freeze C1/target assets → 09 contact chain and joint terminal states → 10 support selection/placement → 11 ramp alternative → 12 tool interfaces → 13 composition → 14 matched bodies and I05–I07 certificates. Probe C2/C3 capabilities before entering the nine-cell comparison. Tools, ramps and weak supports require real contact/structural response; tool joints need physical actuation or a public validated actuator interface, not a hidden grasp function.

Ranges, simulator parameters, per-cell budgets, representative seeds, tolerances, reviewers and reproducers remain pending. Inherit at least three representative runs and three scoring checks. Retain failures/unknowns without replacing seeds; require a continuous complete witness and skill boundaries for each claimed route before broadening scope. Unset budgets do not start a solver. This delivery is reviewable design only.

Static review: from the repository root run `python infra/planning/h1-extension/validate_cooperative_tools.py`. It checks IDs, bilingual links, the nine-cell matrix, terminal contracts and source hashes. The [review receipt](cooperative-tools-validation.json) is not physical feasibility evidence.
