# H1 implementation requirements and evidence ledger

<!-- official-asset-update -->
**Asset follow-up:** Official pinned A3, real Stretch 4, G1 + Inspire DFQ and Galaxea R1 sources are now cached. Six independent passive probes are now complete (A3, historical Stretch 4, Inspire DFQ, R1, current Stretch 3 and official rev1 Dex3), each with 400 steps / 2 seconds / 401 states; R1 redistribution/license gaps remain; see [source report](asset-sources.md) and [JSON](asset-sources.json). The current table reflects the selected embodiments; the initial binding audit is preserved separately in JSON. available models do not establish a frozen hand/sensor/controller/task configuration. Neutral-collision filtering, inertia approximations and absent stabilization control remain explicit; these probes are not task successes.

**Two separate isolated hand-drive probes:** Official Dex3-1 and Inspire DFQ each completed 800 steps / 4 seconds / 801 states. These are separate from the six passive imports and count as zero H1 task successes. The derived fixtures lock all 29 body joints, fix the root, disable gravity and omit the floor; original hand-joint XML is retained. Dex3's 14 candidate drivers pass the local response criteria. All 12 Inspire mimic equalities are measured, with maximum residual **0.043744 mrad** and zero direct follower control force; local coupling is no longer an unverified gap. Its current PD left-thumb hold error **10.7767 mrad exceeds the predeclared 10 mrad bound**. This is a controller-profile failure, not model infeasibility. Grasp/contact, whole-body balance, hardware motor mapping, sensing and full tasks remain unverified. [Measured hand-drive review](hand-drive-review.md), [numerical record](hand-drive-review.json), [local asset/hand package receipt](asset-and-hand-package.json).
<!-- /official-asset-update -->

2026-10-27 · Author-only development material · [Detailed Chinese requirements](implementation-status.md) · [JSON](implementation-status.json)

The user has authorized Gamma GPU execution and sub-agent implementation of the 22 selected tasks. This resumes physical development after the earlier design-only snapshot. The task count, historical H1 scoring and the existing 14-task inventory remain unchanged. Go1 with an arm and extra common-feasible calibration tasks are excluded.

This ledger separates executable contracts, asset/controller readiness, candidate expert plans, actual physical evidence and formal admission. Candidate plans and historical skill traces do not count as new complete witnesses. A new scoped claim requires a continuous generated run through the permitted action interface, matching scene/assets/physics/controller/scorer identity, and checked HL_LL, LL_TRAJ and HL_TRAJ mappings. At least one success establishes scoped design feasibility; three representative repeats, three grading repeats, human review and independent reproduction are reported separately.

## Latest user-selected embodiments

The user now specifies G1 29DoF + Dex3-1 as the main line, prioritizes the Inspire five-finger comparison, and supplies Stretch 3 hardware references. Official A3 T3.0 remains a cached/passively probed development candidate. Official IsaacLab Dex3/Inspire and XR BrainCo support does not establish Genesis integration here.

The prior Stretch 4 passive import remains exploratory and cannot validate Stretch 3. Fixed sources are audited for `stretch_urdf@c8c6e27e1f87db126118049f22611399253cbe2b` and `stretch_mujoco@c78d6a1cd79bb5ead1b679610299563c1a91124a`. Existing P4 runtime profiles and historical results keep their exact archived model identities. Current task requirements target Stretch 3. See [selected sources](embodiment-selection.md) and [matched-body audit](g1-matched-body-audit.json): 29 common movable joints, 7 common fixed joints and 37 common links match structurally. Inspire DFQ has 53 movable joints including 12 mimic joints, not 53 independent motors. Legacy Menagerie G1 evidence remains separate.

## Current measured outcome: zero new compliant complete witnesses

The frozen baseline 8034801 ran 434.22 simulation seconds / 86844 physics steps / 21712 states, then stopped at setdown alignment because contact QP reached its iteration limit. Original score is 0.1925, non-VOID, incomplete; this does not certify infeasibility. Source identity and executed-prefix mapping are checked; the remaining work is contact-QP alignment repair, a new full original-start execution, detailed refinement and human review. [Failure and mapping](baseline-execution-8034801.json.gz).

P4 run 8034839 ran 248.62 simulation seconds / 49724 physics steps / 12432 states. The 5 kg target entered D and remained released/stable for 6.46 seconds. However, maximum joint overshoot was **4.585 mrad, exceeding the original 1 mrad allowance**, so strict task success is false. The earlier checker accidentally allowed 20 mrad; its original source/verdict is retained and superseded by strict regrading. Geometric completion is not compliant completion.

Original v7 semantic review retains 16 passed / 5 failed macro segments and 43 passed / 11 failed / 3 unknown leaf actions. Failures include missing raw contact at Touch exit, unsettled early Push exits, and actual touchdown one control step after nominal land-label boundaries; three internal labels are missing. V8 restores strict actuator checking without erasing these results. Whole measured foot-reposition macros do show both actual unloaded swings and landings.

A separate [post-execution macro explanation](p4-evidence/attempt-8034839/observed_macro_mapping.json.gz) groups continuous observed transport/reposition/release effects with original command ranges, raw boundary states and all leaf failures. It is explicitly retrospective and cannot upgrade the original skill contracts or actuator verdict. Semantic audit definitions were developed after jobs started; original D/profile/budgets were frozen beforehand.

Independent identity audit matched 110 source and 101 asset files, pre/post asset hashes and archived verifier identity. Actual commands and measured states have continuous coverage. Assistant spot inspection decoded the two-view video and final frame; human review remains unsigned. Six passive model probes, baseline failure, startup failures, old-recorder diagnostics and subsequent controller revisions are separate evidence classes. Corrected-controller physical results remain pending; all other unexecuted scopes remain unknown. [Code review](implementation-code-review.json).

All three v2 original-start executions are retained: 8034839 / 8034905 / 8035059 ran 248.62 / 235.40 / 246.78 seconds, with maximum joint overshoot 4.585 / 4.719 / 4.585 mrad. All reached the geometric goal; all fail the original 1 mrad rule and lack complete five-rule safety channels. Thus **0/3 compliant complete witnesses**. Leaf counts are 43/11/3, 45/9/3 and 43/11/3 (passed/failed/unknown). Source and asset snapshots match for all three. [Independent summary](p4-v2-independent-review-summary.json).

V3 adds control margins and original-rule safety recording. A 20-second prefix measured 0.493 mrad maximum overshoot; this is not a full success. The three full v3 jobs subsequently completed and failed original safety rule 5; the prefix was not a full success.

V3 now has complete original five-rule safety measurement, but all three full runs fail: 8035717 (A4000, 250.62 s) pushes the right elbow against its upper limit for 8.00 s; 8035839 (A5000, 262.76 s) does so for 5.14 s; 8035840 (A5000, 252.18 s) has left-elbow limit pushing and 3.747 mrad maximum position overshoot. The first two stay below the original 1 mrad position allowance, demonstrating why position-only checking was insufficient. The rule also prohibits outward torque above half its limit within .02 rad of a joint stop for two seconds.

All eight declared macro effects are measured for 8035717, but its safety gate fails. The other two also have failed per-sample foot-support conditions in the final release macro. For 8035839, both feet are unloaded at 240.42/240.44 s (two samples/.04 s): shorter than the original near-fall .06 s dwell, but still a failure of the stricter predeclared author macro. No thresholds are relaxed. Source/assets/pre-post/manifest identity checks pass for all three. **Zero compliant complete new witnesses.** [V3 independent review](p4-v3-independent-review-summary.json).

V4 diagnostic 8036294 stopped under the predeclared wall budget at125.84 simulated seconds before StandUp completed. Original five-rule safety passes on the recorded interval, but waist pitch overshoots2.765mrad against the unchanged1mrad tolerance; both feet lose load at104.16/104.18s, and the interrupted terminal physics-command coverage is incomplete. Elbow references≤2.0rad and terminal inward finger references≥.06rad passed only their scoped command checks. This is a failed diagnostic. [Independent V4 review](p4-v4-independent-review-summary.json).

A separately predeclared V5 route retains intermediate stepping but ends the final Push/Retreat with supported crouch settling and a6s hold. Standing is not a public goal. Original safety,1mrad, per-sample support,D and3s dwell requirements remain unchanged. Fresh-start one-cycle diagnostic8036707 is submitted under frozen contract SHA `58151ac4781bb43abf65978928a692ae315f0ed7ed4f0f7830a95c18d76c60d5`; it can never count as a complete task witness. Full original-start three-cycle execution remains required.


V4 controller repair is underway: interior elbow/finger references and slower/smoother final hand clearance and standing. A separate diagnostic may test the tail, followed by a new full original-start run; diagnostic prefixes or stitched tails cannot become full witnesses.

Exact scope remains a single-seed unhandled wide box, target material friction .5 and inherited plane material friction .1; no effective contact-pair coefficient is inferred. The public 2 kg lifted-payload rule excludes lifting this 5 kg target without asserting mechanical impossibility. A4000/A5000 repeats are not same-GPU deterministic replication. Handled pairs, random scope, sensor-only execution and formal admission remain incomplete.

Official Dex3 remains moving at the end of its passive probe; Stretch 3 importer filtering and inertia approximations remain explicit. Neither passive import demonstrates active control or task success; the separate hand-drive diagnostics below establish only local fixture response. [Stretch 3 measured report](stretch3-asset-review.md), [official Dex3 measured report](g1-dex3-asset-review.md).


V5 one-cycle diagnostic 8036707 independently passed: 24.76 simulated seconds, 4,952 physics steps, maximum actual position overshoot 0.00786 mrad, and complete passing original five-rule safety. All three predeclared macros have measured effects and continuous shared trajectories; settling lasts 1.02 s and Hold 6.02 s. The original leaves remain 4 passed / 2 failed at their nominal contact/speed boundaries. D is not reached, so there are still **zero complete task witnesses**. Full three-cycle original-start run 8036941 is submitted under its separately frozen contract. [Independent V5 diagnostic](p4-v5-diagnostic-independent-summary.json).

## Readiness of all 22 registrations

| Task | Name | Implementation state | New physical evidence |
| --- | --- | --- | --- |
| H1S-01 | Frozen G1/Dex3 baseline | `frozen_baseline_executed_qp_failure` | `failed_incomplete` |
| H1S-02 | G1 five-finger handling | `isolated_hand_drive_measured_task_control_pending` | Coupling measured in isolated fixture; current Inspire tracking fails; full task unknown |
| H1S-03 | Wheels and movable ramp | `asset_binding_missing` | `unknown` |
| H1S-04 | A3 retrieval | `asset_binding_missing` | `unknown` |
| H1S-05 | G1 two tiers / A3 one tier | `paired_asset_and_scene_missing` | `unknown` |
| H1S-06 | Infeasibility and physical exit | `certificate_and_exit_pending` | `unknown` |
| H1S-07.P1 | Push clear and retrieve | `scene_and_chain_pending` | `unknown` |
| H1S-07.P2 | Push a support into place | `scene_and_chain_pending` | `unknown` |
| H1S-07.P3 | Turn or change pushing side | `scene_and_chain_pending` | `unknown` |
| H1S-07.P4 | Push a target above the public lifted-payload limit | `development_diagnostic_passed_full_validation_running` | One-cycle diagnostic passed; no compliant full witness yet |
| H1S-08 | Stretch 3 handled box | `stretch3_asset_selected_task_control_pending` | `unknown` |
| H1S-09 | Stretch 3 infeasibility and exit | `stretch3_asset_selected_task_control_pending` | `unknown` |
| H1S-10.A | G1 support selection | `scene_and_chain_pending` | `unknown` |
| H1S-10.B | A3 support selection | `asset_binding_missing` | `unknown` |
| H1S-10.C | Wheeled platform and ramp choice | `asset_binding_missing` | `unknown` |
| H1S-10.D | Stretch 3 work/transfer surface choice | `stretch3_asset_selected_task_control_pending` | `unknown` |
| H1S-11.A | Directly reachable retrieval | `stretch3_asset_selected_task_control_pending` | `unknown` |
| H1S-11.B | Tool-enabled complete retrieval | `stretch3_asset_selected_task_control_pending` | `unknown` |
| H1S-11.C | No feasible route including tools; exit | `stretch3_asset_selected_task_control_pending` | `unknown` |
| H1S-12 | Same-color identification | `perception_scene_pending` | `unknown` |
| H1S-13 | Autonomous transfer and safe return | `reusable_relay_runtime_new_scope_pending` | `unknown` |
| H1S-14 | Body adaptation in a narrow workstation | `scene_and_paired_asset_pending` | `unknown` |

G1/Dex3 model, Agile policy, Genesis runtime and relay runtime exist locally; exact inspected file hashes are in the JSON. Official sources and passive imports exist for Inspire DFQ, A3 T3.0 and candidate R1; official Stretch 3 SE3/sg3 and official rev1 Dex3 completed independent passive jobs 8036300 and 8036343. Stretch 4 remains historical exploration. Source/license selection is no longer the main gap for Inspire/A3. Inspire local mimic coupling is now measured in a fixed-root zero-gravity fixture; improve the failed thumb tracking profile and verify grasp/contact, whole-body balance, hardware mapping, sensors/collisions and complete task chains. This is an audit of the selected repository, not a claim that external assets do not exist. A model name or local file alone does not establish usable control.

## First frozen physical development profile

[`H1S-07.P4 / g1_dex3_ground_push_v1`](../../../humanoid/g1_support_retrieval/extension/p4-development.json) freezes one Gamma GPU, 3600 s wall time and 600 s simulation per attempt, physics dt 0.005 s, control dt 0.02 s, 120000 physics steps / 30000 control steps, one candidate, 60 s screening, zero short probes, zero in-episode resets and three intended representative repeats. The deterministic privileged expert calls no language model; this explains the null token budget.

The 5 kg ground target exceeds a public 2 kg lifted-payload limit; supported pushing is allowed. This is a public-rule distinction, not proof that the robot is physically unable to lift 5 kg. Score the full measured target AABB in D, independent ground support, released hand contact, speed bounds and a three-second dwell. The runner has executed. Run 8034839 reached the geometric delivery goal but failed original actuator compliance; no compliant complete new witness is established.

For other tasks, the proposed screening budget is 60 s, three candidate routes and at most two probes of 1000 physics steps each. It is not frozen globally: bind a numerical runtime limit, budgets and identities before each executable task. Budget exhaustion remains unknown. Keep all failed attempts and prescribed draws; a later change requires a new manifest.

The candidate catalog compiler is `python -m infra.h1_tasks compile --out infra/planning/h1-extension/implementation-contracts.json`; its schema is `h1-execution-contract-catalog/1`. It describes author-side subgoals, low-level actions, preconditions/effects and contact/support constraints. Trajectories stay null until actual execution. It is not a scene/controller or physical feasibility solver.

## Acceptance rules that affect implementation

- Accept every complete legal solution. Intended tool identities, intermediate transfers and reference action sequences are not hidden success requirements. Revise mechanism labels when a legal alternative succeeds.
- H1S-03 requires autonomous placement of an initially unpositioned ramp. Prepositioned-ramp use is a separate diagnostic. H1S-07.P4 is ground delivery, not elevated retrieval.
- H1S-11 prioritizes a real passive hook and compatible target ring: grasp hook, engage, pull along independent support, disengage, park hook, grasp the target handle, transport and release. No hidden attachments or remote passive-tool actuation.
- A Q exit requires the whole robot horizontal envelope in Q, legal ground support, empty hands, no hard violation, speed at most 0.03 m/s and 0.05 rad/s continuously for three seconds. These remain draft thresholds until calibrated and frozen per body. Safe exit does not establish correct abstention.
- Correct abstention requires an initial-scene all-route infeasibility certificate. Failed IK, search exhaustion or one failed route is insufficient. Unknown-scene abstention correctness stays null.
- Preserve actions and measured states with continuous step/time, actual effort, support/contact and monitor logs. Each low-level segment must map to its high-level parent and exact executed frame interval, including failed and unexecuted segments.
- Keep original resets, runtime logs, videos, hashes, failed attempts and repeat results. No post-start pose writes, teleportation, hidden attachments, changed physics or checkpoint stitching.

Formal admission and unsigned human-review gates remain unchanged. Full details, task-specific acceptance checks and reusable-source limitations are in the Chinese document and machine-readable ledger.
