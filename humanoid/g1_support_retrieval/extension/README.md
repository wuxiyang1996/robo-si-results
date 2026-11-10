# H1 selected-task physical development

This directory implements the first bounded **H1S-07.P4 ground-push delivery** candidate. It does not assert implementation or physical success for the other 21 registrations. Its result remains unknown until a fresh execution passes the independent measured-state verifier. Existing H1 and historical push/climb demonstrations are not counted as new successes.

## Frozen development configuration

`p4-development.json` freezes the scene, public payload rule, execution budget and representative repeat count before a run. `expert-plan.json` defines the high-level goals, low-level contact/locomotion operations and trajectory-generation method. The 5 kg target exceeds the declared 2 kg **lifted** payload rule; ground-supported pushing is allowed. This proves neither a mechanical inability to lift 5 kg nor a general push capability. The no-handle variant and this nominal seed are the only configured scope; handle pairing, randomized scenes and sensor-only control are pending.

The ground box starts at `(2.30, 0, 0.09)` m with size `(0.45, 0.50, 0.18)` m. D is centered at `(2.66, 0)` m, size `(0.60, 0.70)` m. The controller approaches, makes three 0.12 m push strokes interleaved with independently planned foot placements, clears its hands, stands and holds for four seconds. Reference phases are diagnostic: any complete legal route satisfying the goal is accepted by the verifier.

## Historical v2 run on Gamma

The bare launcher command below selects the original `p4-development.json`, whose three complete runs failed the strict 1 mrad rule. For the repaired v3 candidate, use the explicit profile and prospective-contract command in the later v3 section; preserve explicit arguments when reproducing a result.

From repository root, with the existing Genesis environment and isolated OSQP dependency:

```bash
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python -m pip install \
  --target /fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-extension-deps --no-deps osqp==1.1.3
sbatch humanoid/g1_support_retrieval/extension/run_gamma.sbatch
```

The job requests one Gamma GPU, four CPU cores and 24 GB for at most one hour. Each attempt gets a new directory named by its Slurm job ID. A fresh process executes an independent source snapshot and copied assets, including the actual generated cabinet colliders. There are no resets, restored checkpoints or old replay segments. A nominal run is limited to 600 simulated seconds at 0.005 s physics / 0.02 s control intervals. Three repeats are prescribed, not assumed completed.

`H1_EXTENSION_PYTHON` can override the interpreter. The isolated OSQP path in the job script is an execution-environment dependency; `environment.json` records actual versions and GPU identity. No shared Python environment is modified by these instructions.

## Physical evidence and verification

```bash
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python \
  -m humanoid.g1_support_retrieval.extension.verify_p4 \
  humanoid/g1_support_retrieval/extension/validation/attempt-JOBID
/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python \
  -m unittest humanoid.g1_support_retrieval.extension.test_verify_p4 -v
```

The verifier requires all oriented target corners in D, target contact with the floor, no robot-target contact links, target speed at most 0.03 m/s, angular speed at most 0.05 rad/s and tilt at most 5 degrees. The robot must have linear speed at most 0.03 m/s and angular speed at most 0.05 rad/s. Actual two-foot standing and non-foot contacts are recorded as reference diagnostics; safe non-foot support or non-hand pushing is not a hidden route prohibition. These conditions must hold continuously for the final three seconds. Heavy-target ground support and actuator bounds are checked over the recorded execution. Controller completion is recorded separately from the physical goal.

The recorder captures each control-rate measured state and the final executed endpoint, as well as actuator extrema after **every physics step**. `command_trace.json` contains reference commands; `physics_commands.npz` contains the exact clipped per-substep requested force/position commands. It must not be confused with a successful independent replay. Native actual actuator effort is audited separately. All evidence is privileged author-side material and must stay out of agent bundles.

| Artifact | Meaning |
| --- | --- |
| `profile.json`, `expert-plan.json` | Predeclared scene, budgets, high-/low-level reference |
| `environment.json`, `execution_identity.json` | GPU/Slurm/software identity and executed frozen source root |
| `source_snapshot/`, `source_hashes.json` | Actual executed source/config copies and hashes |
| `asset_hashes.json`, `effective_asset_hashes.json` | Before/after effective asset identity |
| `execution/approach_plan.npz` | Generated approach reference; planning alone is not success |
| `execution/trace.json` | Measured target, robot, contacts, support, speed and phase records |
| `execution/joint_trace.npz` | Continuous measured 50-element floating-base qpos trajectory |
| `execution/command_trace.json` | Control-rate reference targets and QP references |
| `execution/physics_commands.npz` | Per-physics-step exact clipped commands and force bounds |
| `execution/actuator_audit.json` | Every-physics-step joint position, speed and effort extrema |
| `execution/world_params.npz` | Actual initialized rigid-body masses and friction ratios |
| `execution/motion.mp4` | 5 fps two-view video, including failed executions when available |
| `plan_mapping.json` | Actual contiguous high-/low-level segments mapped to measured state and command indices |
| `outcome.json`, `manifest.json` | Independent physical outcome and hash-bound evidence list |

Synthetic negative-control tests cover partial containment, lost support, retained contact, force cancellation, an unstable robot, interrupted dwell, actuator violations, missing steps, wrong mass, nonfinite commands, invalid qpos shape and forbidden pose-write declarations. They validate software rules, not physical feasibility. Human video review, isolated agent-interface acceptance, independent replay, scene/asset license review and formal admission are separate pending gates.

## Retained attempts

- `8034725`: startup dependency failure (`osqp` absent), zero executed physics steps; the failure and environment remain preserved.
- `8034773`: first native GPU development attempt. Its v1 recorder sampled target angular velocity one control interval later than its position. It is retained as a diagnostic and cannot become a full witness.
- `8034839`: v2 frozen-source attempt with aligned timestamps and exact substep commands. Read its actual `outcome.json` and Slurm state; submission alone is not validation.

No failure or timeout proves infeasibility. The original task pages, baseline scores and formal admission remain independent of this development candidate.

## Environment and exact repetitions

The observed core versions are pinned in `requirements-observed.txt`: Genesis 1.4.3, PyTorch 2.11.0+cu128, MuJoCo 3.14.0, SciPy 1.18.1, NumPy 2.5.3 and OSQP 1.1.3. These are observed package pins, not a claim of a complete transitive dependency lock or second-machine reproduction. The shared Genesis installation is reused; OSQP is installed into a task-local directory. On another machine, set both variables explicitly:

```bash
export H1_EXTENSION_PYTHON=/absolute/path/to/python
export H1_EXTENSION_DEPS=/absolute/path/to/task-local/python-packages
"$H1_EXTENSION_PYTHON" -m pip install --target "$H1_EXTENSION_DEPS" --no-deps osqp==1.1.3
sbatch humanoid/g1_support_retrieval/extension/run_gamma.sbatch
```

The launcher prepends `H1_EXTENSION_DEPS` to `PYTHONPATH`. Its default absolute path is a convenience for this Gamma workspace, not a portable dependency specification. Confirm the remaining packages and CUDA runtime against the recorded environment before reproduction.

To repeat an existing immutable runtime instead of the current development checkout:

```bash
export H1_REPEAT_FROM=/absolute/path/to/validation/attempt-8034839
sbatch --export=ALL,H1_REPEAT_FROM humanoid/g1_support_retrieval/extension/run_gamma.sbatch
```

`repeat_frozen.py` validates the baseline source/asset manifests, copies the complete source/asset tree, and executes the copied entrypoint with a new output directory and fresh simulator. It copies no checkpoint or historical trajectory. Attempt 8035059 uses this path. The physical controller, simulator environment and recorder sources for 8034839 and 8034905 match across 107 entries; all 203 copied asset files match, as do profiles and core package versions. Their postprocessing code and asset-manifest enumeration differ; `repeat-identity-audit.json` therefore explicitly reports that the **entire** source manifests are not equal. The three configured repetitions are same-seed repetitions, not independent randomized instances.

For future development runs, the current launcher reserves 90 seconds within the original one-hour wall budget for evidence finalization and signals the worker before that deadline. The updated recorder writes `trajectory.partial.jsonl` continuously and catches stop signals while executing physics. Earlier v2 frozen runtimes lack this streaming revision; their logs and any video remain preserved if an external hard timeout prevents final trace output. This instrumentation revision is not silently substituted into an exact frozen repeat.

The independent semantic review is separate from geometric goal verification:

```bash
"$H1_EXTENSION_PYTHON" -m humanoid.g1_support_retrieval.extension.verify_skill_refinement review \
  /absolute/path/to/attempt \
  --contract humanoid/g1_support_retrieval/extension/skill-refinement-contract-v7.json
```

That review freezes skill entry/effect, measured contact and transition checks and may return partial/unknown even when a task goal succeeds. `plan_mapping.json` by itself only proves time/index coverage. The semantic report must be read before claiming a full high-level → low-level → trajectory refinement witness.

Semantic contract v7 is a development audit frozen during job execution, before complete outcomes were available. It is not retroactively described as a pre-job acceptance protocol. The scene, controller and execution budgets were frozen before each job.

## Strict-standard correction and controller repair

The first completed v2 run (8034839) physically delivered the target and held the geometric/stability goal for 6.46 s, but its maximum actual joint overshoot was **4.585 mrad**. The initially written development checker mistakenly permitted 20 mrad. That threshold was incompatible with the existing **1 mrad** rule in `sandbox/trusted/relay_scoring.py:31` and `TASK_CARD.md:18`; it has been corrected. The strict outcome is `physical_goal_met=true`, `task_success=false`, not a compliant full witness. Prior checker/verdict copies are retained under the attempt's `review_history/`, including the exact original checker recovered by matching its recorded SHA-256.

`limit-diagnosis.json` locates the observed violations. Initial joint positions are legal. At 50 Hz, the first thumb violations occur at 13.10–13.14 s during pushing, and the first waist-pitch violation at 17.48 s during the first step transition. Physics extrema are sampled at 200 Hz, so their exact peak time is not inferred from the coarser trajectory.

The separately frozen `p4-margin-v3.json` repairs the controller by reducing the online IK upper waist reference from 0.50 to 0.44 rad and changing the mirrored thumb fold reference from -1.047 to -0.99 rad. Physical joint limits, object mass, friction, scene, target and acceptance tolerance are unchanged. The 20 s diagnostic prefix `p4-margin-v3-probe.json` covers both previously observed triggers and has a separate 20-minute wall budget; it cannot count as a full solution. A complete v3 run retains the original 600 s simulation / one-hour wall budget.

The semantic v7 leaf audit also remains preserved: several reference-label boundaries occur before measured contact/landing or after a contact interruption. Post-execution macro annotation can describe the measured physical action, but cannot retroactively turn those earlier leaf contracts into passes. Future online boundary control must wait for measured raw contact, released/stopped target state and actual foot support before committing the corresponding transition.

## Original five safety rules and prospective v3 binding

A low base velocity alone cannot certify that a stationary robot has not fallen. The full verifier now also requires `original_safety_review.json` to have `complete=true` and `safety_passed=true`. This adapter calls the existing `sandbox/trusted/relay_safety.py` and `relay_safety_rules.py` without changing their thresholds. Safe knee/seat support is handled by those shared rules; a hidden feet-only or hands-only route restriction is not introduced. The modules retain their published calibration limitations. The original v2 runs lack the complete input channels and therefore receive `unknown` for full safety coverage in addition to their measured 1 mrad violation.

The v3 recorder creates `execution/safety_trace.npz` at the same 50 Hz state times, including the original initial state and a freshly measured terminal state. It records root pose/velocity, exact physical foot-sphere bottoms, floor loads, all nine movable objects and object contacts per hand/foot/body, cabinet contacts, nonfoot ground support, and Genesis current-state signed clipped control forces with joint positions in the declared actuator order. The force API recomputes current-state PD/force output with clipping; it is the original trusted monitor channel, not a mechanical torque sensor or the previous substep `qf_applied`. All nine physical collision-enabled objects are included in rule 2, including parked objects; the original episode presence mask is retained separately. `safety_meta.json` binds sizes, physical presence, joint limits, actual robot mass, link identities and foot-collider source hash. Contact magnitudes come from each individual contact through the original trusted classifier; opposing forces cannot cancel into a false release. These fields supplement, rather than replace, the 200 Hz actuator extrema and exact requested substep commands.

The future full v3 profile is bound before the first physics step to `prospective-macro-contract-margin-v3-r3.json`. This contract was developed from v2 observations and is prospective only for the new v3 execution. It defines measured composite ground strokes and physical advances; the stricter original leaf diagnostics remain visible separately. The runner checks the contract's profile copy, profile source hash and every runtime source binding before execution, then writes `refinement_contract_binding.json` with its hash and UTC binding time. A mismatch stops the attempt before simulation.

```bash
export H1_EXTENSION_PROFILE=humanoid/g1_support_retrieval/extension/p4-margin-v3.json
export H1_REFINEMENT_CONTRACT=humanoid/g1_support_retrieval/extension/prospective-macro-contract-margin-v3-r3.json
sbatch --export=ALL,H1_EXTENSION_PROFILE,H1_REFINEMENT_CONTRACT \
  humanoid/g1_support_retrieval/extension/run_gamma.sbatch
```

Do not use `H1_REPEAT_FROM` with that command: the repeat path intentionally executes the specified older frozen runtime. New v3 runs and the earlier three v2 repetitions are separate controller revisions. All preexisting outcomes, failed attempts and development audits stay archived.

A stop signal arriving inside a four-substep control interval is an incomplete attempt: the all-physics sample count then disagrees with the completed-control timeline, and strict coverage rejects it. The partial JSONL, actuator sample count and scheduler log must be retained. Such an interrupted tail must not be presented as a complete aligned trajectory; a future recorder revision should explicitly label the residual physics interval and its actual terminal time.

The v3 series uses different allocated GPU models: 8035717 runs on RTX A4000, while 8035839 and 8035840 run on RTX A5000. Their 122 frozen source entries, 203 assets, profile/contract bytes and core package versions match. They are representative same-seed repetitions across those devices, not a same-hardware deterministic replication. Exact host, GPU and driver reports remain in each `environment.json` and the series identity audit.

## V3 results and the V4 diagnostic

All three v3 executions delivered the box and completed their controller sequence, but **none passed the original standard**. The complete five-rule audit exposed sustained outward elbow control force close to the upper joint limit. The third run also violated the original 1 mrad position tolerance during ClearHands. These are preserved physical failures, not missing evidence or a reason to relax the rules.

| Job | Simulated seconds | Final geometric dwell / s | Maximum actual position overshoot / mrad | Full outcome |
|---|---:|---:|---:|---|
| 8035717 | 250.62 | 6.46 | 0.474 | failed |
| 8035839 | 262.76 | 6.48 | 0.562 | failed |
| 8035840 | 252.18 | 6.20 | 3.747 | failed |

`v3-repeat-series.json` retains exact rule-5 events. The independent semantic review also found a 0.04 s double-foot unloading interval in one ClearHands execution; this is below the original near-fall event duration but fails the stricter, prospectively declared macro support predicate. Both verdicts remain visible. The selected-frame AI video review of 8035717 observes box transport and final release, but cannot establish torque compliance and does not override that failure.

V4 adds an interior elbow IK reference ceiling of 2.0 rad, keeps mirrored index/middle flex and distal references 0.06 rad inward even when StandUp requests zero opening, starts ClearHands from the measured MCP positions rather than stale unreachable commands, doubles ClearHands to 6 s, lengthens StandUp to 20 s, and bounds body-joint changes inside the terminal-phase IK solve to 0.005 rad per 20 ms. Thumb2 neutral is unchanged and remains physically audited. No real joint position, hardware limit, mass, contact parameter or safety threshold is clipped or changed.

The old online exception filter also mistook every reach error containing the key `palms` for a hand-only miss. V4 parses the finite numeric fields: foot errors above 3 mm or COM errors above 4 mm stop execution; only a palm-only miss may retain the existing fallback. This is a controller constraint, not a new task route restriction.

The bounded one-cycle diagnostic starts from the original scene and runs through pushing, walking, ClearHands, StandUp and final hold. Its unchanged D is intentionally not shortened. Its 180 s simulation / 1800 s wall budget and explicit acceptance are frozen before physics; the native checker refuses to count any diagnostic or partial-start profile as a full witness, even if it happens to reach the task goal.

```bash
export H1_EXTENSION_PROFILE=humanoid/g1_support_retrieval/extension/p4-interior-v4-probe.json
export H1_REFINEMENT_CONTRACT=humanoid/g1_support_retrieval/extension/prospective-macro-contract-interior-v4-probe-r2.json
sbatch --time=00:30:00 --export=ALL,H1_EXTENSION_PROFILE,H1_REFINEMENT_CONTRACT \
  humanoid/g1_support_retrieval/extension/run_gamma.sbatch
```

Job 8036294 stopped at its predeclared wall deadline, preserving 125.84 simulated seconds. It failed the diagnostic: two ClearHands samples lost both foot loads, the recorded maximum actual position overshoot was 2.765 mrad, and the interrupted final interval lacked complete control coverage. The original five-rule audit passed, which does not override those separate failures. No full v4 execution was launched. The runner also hashes and copies contract-referenced frozen documents into both `frozen_documents/` and the immutable snapshot before launching physics.


## Prospective V5 released crouch route

The public task does not require standing after releasing the target. V5 changes the expert action sequence: the first two complete-task strokes still reposition the feet and hands, but the last stroke ends with `Retreat → SettleRelease → Hold`. It removes the final repositioning, ReturnHands, ClearHands and StandUp sequence that caused prior terminal violations. It does not truncate an old trace: every diagnostic and full execution starts from the original scene with its own continuous simulation.

`SettleRelease` captures the last commanded posture reference after retreat and continues ordinary bounded PD plus the same leg gravity/balance feedback. Actual joints and the free base remain dynamic. `terminal_reference_freeze.json` records this command reference; the name refers only to the reference, never a fixed physical state. The planner reference stays constant, while the separately recorded feedback leg targets and actual applied force requests may vary. No controller gain, hardware limit, mass, friction, or original acceptance threshold changes.

The controller allows up to 8 s to establish 1 s of continuously measured release, target support, target/root velocity bounds and foot support. A subsequent 6 s physical hold remains independently checked. Internal timer fields in each `settle_release_evidence` row are diagnostic: the verifier recomputes stability from raw state timestamps, contacts and velocities. The full task still requires the entire target in the original D and at least 3 s final stable dwell, the original 1 mrad position tolerance, all five safety rules and the prospectively declared macro support predicate.

The single-cycle original-start diagnostic 8036707 uses `p4-crouch-v5-probe.json`, with an unchanged D, 180 s simulation / 1800 s wall budget. It need not reach D and can never count as a full task witness. The expert plan, acceptance document, leaf contract, macro contract and required source hashes were bound before physics. Two independent CPU checks verified route topology, copied reference independence, stable-timer reset on support loss and the bounded failure deadline; those checks are software evidence only.

```bash
export H1_EXTENSION_PROFILE=humanoid/g1_support_retrieval/extension/p4-crouch-v5-probe.json
export H1_REFINEMENT_CONTRACT=humanoid/g1_support_retrieval/extension/prospective-macro-contract-crouch-v5-probe-r1.json
sbatch --time=00:30:00 --export=ALL,H1_EXTENSION_PROFILE,H1_REFINEMENT_CONTRACT \
  humanoid/g1_support_retrieval/extension/run_gamma.sbatch
```

After the diagnostic passes, the three-cycle `p4-crouch-v5.json` profile requires its own prospective contract and fresh full execution. The launcher now performs native postprocessing from each attempt's immutable `source_snapshot`; later stricter independent reviews must archive their exact source separately. All previous failures remain in the ledger.


V5 diagnostic 8036707 completed 24.76 simulated seconds / 4952 physical steps. Independent acceptance passed: maximum actual joint overshoot 0.007864 mrad, original five safety rules passed, and all three declared diagnostic macros had measured effects and complete command coverage. The six leaf diagnostics remain four passed / two failed; macro acceptance does not rewrite those fine boundaries. The one-cycle target remained outside the full D goal as expected. A three-frame AI video review (initial, pushing, terminal) confirms visible floor transport and terminal crouch only; human review is pending.

Full job **8036941** was then launched with `p4-crouch-v5.json` and the separately pre-frozen `prospective-macro-contract-crouch-v5-full-r1.json` (SHA-256 `b742d05979bbd4b411a0e6ee018c3997fa87e66324668fe2558d786025972a0e`). It uses Gamma RTX A5000, a fresh original scene, three strokes, two intermediate foot repositionings, and the released crouch terminal route. The 600 s simulation / 3600 s wall budget is unchanged. It is one full execution, not three successful repetitions. Until its complete physical and independent reports exist, full success remains unverified.

The native `plan_mapping.json` is a phase-to-index coverage aid with historical broad phase labels. For V5 high/low semantic claims, use the prospectively bound `prospective_macro_mapping.json`: it assigns the final withdrawal to its declared transport macro and settling/hold to the release macro. Shared endpoint states, exact command ranges and preserved leaf diagnostics are recorded there; phase names alone are not semantic evidence.
