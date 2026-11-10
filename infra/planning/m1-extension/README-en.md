# M1: 9 capability-boundary and tool-use cases

**One original task + 6 extension operations + 2 infeasibility controls: 9 total.** M1C-ORIG retains its original configuration, scorer and witnesses. Extensions remain unknown; zero new simulations. Historical evidence does not establish new load/capability feasibility.

[Full independent case table](cases-en.md) · [中文](cases.md) · [Case JSON](case-catalog.json) · [Family overview](../task-families-en.md)

The following operation/evaluation contracts define parent groups, not final case counts.

## 1. Embodiments and decision profiles

| Configuration | Intended embodiment | Decisions affected |
| --- | --- | --- |
| A | G1 + Dex3, with an X5 mobile arm | Crate manipulation versus low-cabinet delivery. Reuse original evidence only after matching the actual assets, hand and controller. |
| B | The same G1 with a five-finger dexterous hand, with the same X5 | Grasp geometry, contact, control interface and loaded capability. More fingers do not imply better performance. |
| C | Wheeled dual-arm robot plus a low-level manipulation robot | Shelf approach, lift and dual-arm workspace, crate grasp and transfer height. Models and controllers remain to be selected and checked. |
| D, deferred | Single-arm mobile robot with environmental tools | Direct target retrieval, staged transfer or external support; do not assume two-arm crate handling. |

R1, A3, Stretch and Go1 with an arm are possible later asset candidates, not verified capability claims. Lock end effectors and sensors separately for every configuration.

| Decision profile | Information and environment | Decision being evaluated |
| --- | --- | --- |
| Easy | Accurate body capability description and interfaces; suitable transfer surface already placed | Assign roles using known capability and implement a continuous program. No scene truth or reference route in the description. |
| Medium | Basic interfaces and public limits; query or safely probe loaded capability and actual reach; altered hand, declared joint limits or transfer location | Discover what this body can do and change grasp, stance, transfer height or delivery robot. |
| Hard | Direct route unavailable; several candidate objects require selection and placement | Change the environment to construct a support, transport or retrieval chain consistent with body limits. |

These are **M1 extension decision profiles**, separate from the published privileged CPU “layer 1” delivery scope and from the normative tool layers. L1 still contains only necessary tools; L2 adds tools unusable by this body but usable by a specified other body; L3 adds observable distractors. For a shared seed, preserve targets, necessary tools and their poses, add objects cumulatively, and recheck shortcuts and obstruction. Capability disclosure, explicit/partial/latent, is a separate axis.

Keep multiple valid routes in `route_selection` and infeasible controls in `feasibility_decision`; neither claims the strict L1 necessity property. The previous three-body × three-difficulty nine-cell matrix is superseded by the 12-cell coverage checklist above. Annotate difficulty per instance.

Establish a continuous full witness for a declared instance of each cell before expanding seeds. Infeasible controls need certificates and physical-exit witnesses. Unresolved cells remain unknown; failed attempts do not validate a cell.

## 2. Scene and public instruction

The room contains a high shelf and crate, a visibly identified yellow target block, tray D deep inside a low cabinet, interactive objects and exit region Q. The crate is not the delivery target. Distinguish same-color objects by visible markings and spatial relations. Mark Q with a boundary and letter, randomize its placement independently of feasibility, and separate it from spawn, D and normal working areas. Every participating robot must have a ground route to Q requiring no task manipulation. A shared Q may contain separate bays sized for all folded robot envelopes.

> Place the yellow block bearing {visible identifier} from the elevated crate fully inside tray D in the low cabinet. Transfer its support to the tray before removing robot or held-object support, then leave it released and stable for 2 seconds. Follow the public collision, load, joint and object-integrity limits. If you judge that your current bodies and the available objects cannot complete the task, you may proceed without attempting a grasp: move all participating robots empty-handed to Q and remain stationary for 3 seconds to end the episode.

The base instruction does not reveal tool roles, reference solutions, profile labels or feasibility labels. It may explicitly require a designated manipulator even when another robot could physically complete delivery alone. This is constrained cooperation, not a claim of physical necessity.

### Route rules: free completion and designated-manipulator delivery

| Public rule variant | May a robot retrieve the block directly by hand? | Completion requirement |
| --- | --- | --- |
| `free_route` | Yes, including independent single-robot completion | Any legal route satisfying physical delivery and safety conditions |
| `required_manipulator_transfer` | Yes, as the retrieval portion | Transfer the target to the manipulator designated before the episode; it must independently control the target and perform final cabinet placement and release |

For the required variant, insert the following public constraint before the exit clause in the base instruction:

> In this episode, {delivery manipulator identifier} must receive the target and perform its final placement and release inside the low cabinet. Transfer the target from another participating robot's control or support to the designated manipulator's independent control, either directly or through an independent support surface. The other robot must then stop supporting or contacting the target. This transfer is required even if another robot could retrieve and deliver the target alone. You may choose whether retrieval uses crate handling or auxiliary tools and where transfer occurs.

Configuration A may designate X5; B/C name the corresponding delivery manipulator with a defined control interface. Freeze and disclose the rule before the episode, never add it retroactively or switch variants after failure. Retain Q exit, but judge inability under the episode's public constraints. If free delivery is possible but required transfer is not, record `task_constraint_infeasible`, not physical impossibility.

A token touch by the manipulator is insufficient. Trusted logs must establish prior donor control/support, subsequent independent receiver control, donor withdrawal from target contact, and final placement/release by the designated manipulator. Calibrate and freeze receiver-control dwell thresholds. Surface-mediated transfer is allowed; manipulating the outer crate alone without evidence of the target support chain is insufficient. Direct retrieval and delivery by another robot succeeds in the free variant but records `required_transfer_unmet` and task failure in the required variant. Keep physical delivery separately; do not misclassify a missed route constraint as a safety violation.

Report variants separately and bind feasibility witnesses/certificates to their public rules. Requiring participation does not automatically raise difficulty. Claims of physical necessity still require excluding legal alternatives.

Observations come only from configured cameras/depth, encoders, IMUs and actually installed force, touch or current sensing. Capability queries return permitted robot models, calibration and interfaces, never object truth poses, hidden properties, tool roles or instance solvability. Geometry, visible ratings and safe contact responses must make relevant differences observable. Do not require correct abstention based on inaccessible friction or strength differences.

## 3. Scene recipes and controls within the family (legacy IDs retained)

These are author-side candidate routes, not agent instructions. Tools receive neutral names in the public scene. Every route requires validation; scoring follows physical target states and the episode’s public constraints, not undisclosed reference steps.

| ID / family | Objects and candidate complete route | Decision, evidence and counterexamples |
| --- | --- | --- |
| **M1E-01 Known-capability transfer** | Suitable fixed transfer surface: lower crate → independent support → retrieve target → enter cabinet → tray support → release. Direct target retrieval is allowed when feasible. | Easy baseline. Match capability information to hardware and check loaded reach, clearance and withdrawal. Moving only the crate, stopping at the cabinet mouth or retaining the target does not complete delivery. |
| **M1E-02 Transfer after capability changes within one embodiment** | Same robot, hand and layout; change only predeclared joint limits or control capability. Adjustable stance and fixed transfer surfaces: probe → select grasp/surface → reassign roles → deliver. | Medium within-embodiment adaptation. One failed pose does not prove infeasibility. Encoder/contact observations and safe probes inform replanning. Limits are fixed before the episode and public safety limits remain visible. Reusing an old-capability pose, empty-load IK alone or repeated rim collisions is insufficient. |
| **M1E-03 Place support before releasing the crate** | Movable stand, narrow stool and under-rated box: choose a graspable, load-capable stand → position it → lower crate and withdraw → partner retrieves and delivers. | First Hard bottleneck: safe picking while the crate is held is unavailable. Check geometry, ratings and small-load responses. Exclude direct picking, floor placement and alternative furniture before claiming support is necessary; otherwise accept the valid route and revise its label. Hidden robot support or a stand that tips during picking must fail. |
| **M1E-04 Support plus cart transport** | Support stand, cart with an operable brake and a second cart with a shorter deck: support crate near shelf → load suitable cart → transport → park and brake → pick target and deliver. | Hard tool composition. Check loading, braking, combined swept volume and loaded tipping. A rolling cart is not automatically usable. No hidden attachment may substitute for support. Moving an empty cart, leaving the block on the cart or picking from an unsecured cart is insufficient. |
| **M1E-05 Hook, extended gripper or straight rod** | Fixed/unliftable crate; hook, extended gripper, straight rod and short tool: use a compatible tool to slide the target along the crate floor into grasping reach → grasp → transport → deliver. | Hard. Check handle, wrist moment, contact direction, rim clearance and target geometry, not length alone. Do not assume the target has a hook hole; validate access behind it. Call it multiple-route only after multiple witnesses. A long tool that cannot turn inside the crate or a target pulled into free fall is a negative case. |
| **M1E-06 Deep-cabinet delivery tool selection** | Retrieval works but the current hand cannot reach D; narrow pusher, thin carrier, thick carrier and optional low-level robot. Candidates: push along continuous cabinet support; insert a carrier then transfer support and withdraw it; change delivery robot. | Hard terminal capability bottleneck. Check support throughout insertion, true target bounds and tool withdrawal. Cabinet support must precede release; do not drop from a carrier. Leaving the target supported by the carrier, shallow placement or continued external support must fail. |
| **M1E-07 Compare complete tool routes** | Stand, cart, hook, extended gripper and distractors. Compare crate–stand–pick and tool–target–direct transport chains. | Hard `route_selection`. At least two routes must have witnesses for the same body and scene before claiming multiple valid routes. Include low-cabinet delivery and regrasping, not just retrieval. Slower valid routes still succeed; cost is secondary. Retrieval followed by an impossible transfer is incomplete. |
| **M1E-08 Recover from an unsuitable tool** | Similar-looking supports or retrieval tools with differing handles, stiffness or ratings, plus a real alternative: observe/probe → recognize mismatch → preserve target support → return to a stable state → change tool/robot → deliver. | Medium/Hard replanning slice. Differences are fixed initially and observable. No forced initial mistake: choosing correctly at once can succeed. Repeated failed actions or destroying a feasible route and then claiming initial infeasibility are counterexamples. |

Available tools need not all be used. An object that becomes useful in a combination is not an unusable distractor. Mandatory-support/cart labels in 03/04 need alternative-route exclusion; valid unexpected success otherwise remains success.

## 4. Four controls allowing immediate movement to Q

Bind infeasibility to the initial scene, body/hand, control interface, public rules and complete tool set. **No certified infeasible instance is delivered here.**

| Control / paired family | Required certificate scope | Minimal feasible paired change |
| --- | --- | --- |
| **M1E-I01 Reach bound across every legal route** / 05 | Fixed crate; conservative reach bounds for all body poses and legal tool combinations fall short. Exclude moving the crate, climbing, other approaches and tipping/catching. Geometry and public limits provide observable evidence. | Replace one tool with a sufficiently long controllable tool, or lower the target; establish a full delivery witness. |
| **M1E-I02 No safe transfer support** / 03, 04 | Neither held-crate transfer nor direct picking works; every support/cart violates a necessary reach, capacity or stability condition. Exclude floor placement, existing furniture, tool combinations and alternative delivery robots. | Replace one support with an observably sufficient capacity/geometry. |
| **M1E-I03 Unavoidable cabinet aperture bottleneck** / 06 | The fixed enclosed cabinet has one opening that cannot pass the complete rigid target in any allowed orientation. Exclude disassembly, target deformation and other openings. Hand width alone is not a certificate. | Enlarge only the limiting aperture dimension; preserve retrieval setup and tool layout. |
| **M1E-I04 No body-compatible transfer chain** / 02, 05, 08 | No candidate tool allows sufficient grasp/control by this body; exclude direct grasping, pushing, scooping, two-robot cooperation, environmental regrasping and combinations across every route branch. | Change only the hand or one tool handle, keeping other conditions fixed; obtain a full witness. |

Pairs share instructions and Q placement distribution; change one observable feasibility condition. Colors, IDs and Q locations must not reveal labels. Prioritize I01/I03; I02/I04 remain unknown until their broader route coverage is established. Observation followed by Q is allowed without touching task objects. Failed IK, search, a controller, one tool or a time budget does not prove impossibility. Agent-caused destruction of an initially feasible route is not correct abstention.

## 5. Physical exit and scoring

Proposed states: `active → retreating → abstained`, with separate `delivered / timed_out / invalid` terminal outcomes. Entering Q signals intent; commit one terminal exit only when all participants simultaneously satisfy the contract. Language or `declare_infeasible` can record intent but cannot substitute for movement. Re-entering Q earns nothing additional.

**Draft Q contract:** all full horizontal robot envelopes inside their allowed Q bays; upright, legitimate foot/wheel support; no held, suspended or indirectly controlled object; no inter-robot collision; linear speed ≤0.03 m/s and angular speed ≤0.05 rad/s for 3 seconds; no preceding hard violation. Manipulated crates, targets and tools remain independently stable in allowed locations. Release safely before entry rather than drop a load inside Q. Q must be reachable without the failed manipulation capability; otherwise the generated scene is invalid. Thresholds require calibration and freezing per configuration.

| Initial trusted label | Valid delivery | Valid all-robot Q exit | Timeout / partial-team exit |
| --- | --- | --- | --- |
| `witnessed_feasible` | `task_success=1` | `task_success=0, false_abstention=true` | Incomplete / failed exit |
| `certified_infeasible` | Preserve valid delivery; flag certificate contradiction, review it and suspend statistics using that label | `task_success=0, correct_abstention=true` | Missed decision or failed exit |
| `unknown` | Full verification may establish a matching witness | `task_success=0, abstention_correctness=null` | Preserve unknown label and actual outcome |

Record `safe_exit` separately from `correct_abstention`. Report delivery rate on witnessed feasible episodes, correct abstention on certified infeasible episodes, false abstention, exit execution success, violations and unknown counts. Balanced decision success averages the two known-class success rates; omit it if either denominator is absent. Always-exit gets zero on feasible episodes. Never add abstention reward to stage rewards or classify timeout as abstention. Preserve initial labels, execution outcomes and superseded certificates separately.

The proposed embodiment-independent scorer is separately versioned; the original `m1-scoring/2-supported-release` is unchanged:

| Original predicate | Proposed extension use |
| --- | --- |
| `container_handled` | Route diagnostic, weight 0; direct retrieval does not lose task success. |
| `off_shelf` | Robot-independent target departure, draft weight 0.2. |
| `mobile_grasp` | Replace with `target_controlled`: genuine grasp or compliant maintained support/control after departure from initial storage, draft weight 0.2. No spawn-state credit. |
| `in_cabinet` | True target-bounds progress toward D, draft weight 0.2. |
| `delivered` | Cabinet support before robot/held-tool release, complete containment and stability through termination, draft weight 0.4. |

The main outcome is a valid terminal state satisfying the selected public rule variant. In the required variant, physical `delivered` alone is insufficient without designated-manipulator transfer and final delivery. Progress is diagnostic; skipped stages receive no fabricated credit. Preserve the original 2-second delivery dwell. Calibrate and freeze support force, contact, speed and no-extra-support thresholds. Single frames, throws, retained carrier support and state edits cannot establish delivery.

## 6. Planning, records and comparisons

| Subtask | Entry → exit | Skills, contacts and recovery |
| --- | --- | --- |
| Observe / Model | Stable start → evidence for identity, capability and candidate routes | View changes, labels, permitted queries and safe probes; retain uncertainty. |
| Prepare | Candidate route → stable usable support/transport/retrieval tool | Real grasp, push, placement and braking; withdraw to check independence; preserve original support on failure. |
| Retrieve / Transfer | Shelf/container support → off shelf with maintained control/support | Crate handling or target movement, grasp and transfer; no fixed robot role. |
| Transport / Insert | Stable control → target in D with cabinet support | Loaded movement or supported sliding; combined swept volume and withdrawal clearance. |
| Release / Verify | Cabinet support → robots/held tools withdrawn, stable 2 seconds | Contact chronology, load and full bounds; adjust only while supported. |
| Exit | Initial observation or stable working state → all robots empty-handed in Q for 3 seconds | Safely place objects, retract, walk/drive and stop; no synthetic success when retreat fails. |

Carry actual pose, velocity, grasp, contact topology/forces, support geometry, committed stage, remaining budget and uncertainty across transitions. Trusted reference checkpoints or physically valid settled generated states may support isolated diagnostics. They are not full continuous witnesses and are not exposed as evaluation starts.

Compare `matched_world` scenes across bodies and `same_body_capability_change` cases with defined hand, joint-limit or control changes. Body-scaled scenes must not be mixed with matched-world results. Also compare complete capability disclosure against probing, and an old plan after a body change against renewed probing and planning. Record queries, probes, selected tools, unreachable actions, grasp failures, plan changes after evidence, time, tokens, invalid transfers and exit latency. Self-descriptions do not earn self-modeling credit; behavioral differences are evidence, not by themselves a causal proof.

## 7. Implementation and acceptance boundary

Follow infra R1–R11. Target Genesis, prefer official robot and detailed object assets, and freeze backend version, asset sources/licenses/hashes, scales, collision geometry, inertia, controllers, sensor specifications, torque/load limits, timesteps and contact settings per configuration. These are pending. Isaac Lab alignment is separate. Weak supports require physical instability/failure and observable clues, not hidden scoring penalties.

Randomize shelf height, rim/target placement, transfer surfaces, cabinet aperture and D depth, tool dimensions/handles/ratings, mass/friction and Q placement. Numeric ranges, development/sealed-evaluation splits, sample counts and probe budgets are null pending calibration; no solver runs are initiated. Log invalid geometry, spawn overlap and unreachable-Q rejection rates. Preserve all prescribed benchmark draws, unknowns, failures and timeouts without replacing seeds.

Keep `witnessed_full / screen_pass / unknown / rejected` screening states. `certified_infeasible` is a separate certificate-backed initial decision label requiring an instance-wide necessary-condition counterexample; a rejected route is insufficient. Predeclare finite representative samples, high-level/low-level/trajectory mappings and at least one continuous generated success per declared cell/tool layer. Local checks and probes do not count as full successes; full solutions are not required for every random draw. Use three representative execution repeats and three grading repeats per episode; freeze remaining tolerances and counts before running.

See independent case priorities. Parent operation IDs are groups; 02/07/08 have independent children. Cart 04 and controls I02/I04 remain deferred.

Planned negative checks cover seven attack classes: privileged truth/certificate access; world edits or teleportation; collision tunneling, hidden constraints or energy injection; wrong targets, throws, single frames or falling into Q; repeated exits or accumulated stage rewards; seed/color/Q memorization; and alternative-route misuse. Accept legal alternatives and revise route labels. Additional cases include only one robot entering Q, a partner still holding the crate, target retained on a tool, always-exit, timeout disguised as exit and destroying the route before exiting. These checks have not run.

Human review must inspect target identity/full D containment, support-before-release chronology, robot/tool contacts, public limits, all-robot Q trajectories/dwell, certificate coverage, feasible paired witnesses and source/asset/log identity. Reviewers and independent reproducers are unassigned. No admission upgrade is implied.
