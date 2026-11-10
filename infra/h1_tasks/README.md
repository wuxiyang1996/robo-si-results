# H1 selected-task execution contracts

This author-only package compiles the **22 selected independent registrations**
and validates a portable **trusted-worker** evidence bundle. It is executable
infrastructure, not a robot controller. Compiled expert routes are conditional
candidates; they generate neither physics trajectories nor successful witnesses.
Do not include this directory, the selected-scope source, certificates or trusted
logs in the agent bundle.

Current author-side results: [22-task requirements](../planning/h1-extension/implementation-status.md),
[execution ledger](../planning/h1-extension/execution-progress.json),
[measured trajectory viewer](../planning/h1-extension/trajectory-viewer.html), and
[the executable P4 expert](../../humanoid/g1_support_retrieval/extension/README.md).
The viewer only displays evidence. The ledger separates complete task attempts,
short controller diagnostics, startup failures and cancellations; passive asset
probes are recorded separately.

From the repository root:

```sh
python -m infra.h1_tasks compile --out infra/planning/h1-extension/implementation-contracts.json
python -m unittest infra.h1_tasks.tests.test_contracts -v
python -m infra.h1_tasks validate /path/to/bundle --binding /path/to/frozen-binding.json --out /path/to/report.json
```

`compile_registry()` returns `h1-execution-contract-catalog/1`, bound to the
selected-scope source SHA-256. It checks exactly 22 unique independent task IDs,
excludes the three non-scoring parent groups, preserves their original names,
scene descriptions and solution policy, and adds one finite candidate expert
route per task. `tasks[].expert_candidate.subgoals` contains causal dependencies,
entry/effect contracts, support/contact constraints and ordered low-level actions.
`trajectory=null`, `physical_witness_count=0` and `candidate_only` are deliberate.
Compilation must never promote a task to implemented physics or witnessed success.
The H1S-05 route is a G1 two-tier candidate; its A3 single-tier comparison needs a
separate bound route. H1S-08 must freeze whether the handled box is the target or a
tool before selecting the appropriate full route. H1S-01 candidates do not replace
its original frozen expert or scoring. All candidate plans remain revisable after
asset-specific feasibility checks.

`validate_binding(binding)` rejects missing identities, unresolved robot models,
checkpoint starts and missing/nonfinite budgets. `h1-execution-binding/1` contains:

- `task_id`, concrete `robot_configuration`, `seed`, `origin="original_start"`,
  `simulator_version`, `public_rule_version` and positive `control_dt`.
- Lowercase SHA-256 identities: `scene_sha256`, `robot_sha256`,
  `controller_sha256`, `physics_sha256`, `sensors_sha256`, `verifier_sha256`.
- Frozen `budgets`: `max_control_steps`, `max_observations`, `max_tokens`,
  `max_resets`, `wall_seconds`, `local_probe_steps`.
- For extension tasks: `target_id`, `regions.D` as `[min_xyz,max_xyz]`,
  `regions.Q` as `[min_xy,max_xy]`, and `outcome_limits`: `hold_seconds` (at
  least 3), `target_linear_speed`, `target_angular_speed`, `robot_linear_speed`
  (at most 0.03 m/s), `robot_angular_speed` (at most 0.05 rad/s).

These are explicit author-frozen limits, not calibration results produced by this
package. Scene validity, contact-force limits, loaded structural capability,
asset/controller fidelity, observation interfaces and task-specific requirements
must be checked by the corresponding physics adapter. A declared source hash
alone does not demonstrate that a simulator loaded the correct bytes.

## Portable trusted-worker bundle

`manifest.json` uses `h1-evidence-manifest/1` and a `sha256` dictionary for each
artifact below. Hashes establish identity, **not authenticity or physical truth**.
The caller supplies a separately frozen binding; accepting arbitrary agent-authored
logs or an arbitrary agent-chosen binding would defeat the trust boundary.

| Artifact | Required contents |
| --- | --- |
| `binding.json` | Exactly matches the separately frozen binding |
| `run.json` | Original start, integer `reset_count=0`, `checkpoint_spliced=false`, `recorded_by="trusted_worker"`, `device_type="cuda"`, nonempty `hostname`/`gpu_name`, matching simulator version, consumed `wall_seconds`, `observations`, `tokens`, `local_probe_steps` |
| `states.jsonl` | Original state at step/time zero and one state after every command; integer contiguous `step`, `time=step*control_dt`, finite nonempty `qpos`/`qvel`, `hard_violations=[]`, measured `target` and `robot` |
| `actions.jsonl` | One per transition; matching `step`/`time`, finite nonempty actual `control`, `public_limits_pass=true` |
| `plan.json` | `status="executed"`, matching task ID, `subgoals` with unique IDs, causal dependencies, preconditions/effects/contact constraints and unique ordered low-level action IDs |
| `segments.json` | Ordered nonempty contiguous transition spans `[start_step,end_step]`, action/subgoal IDs, exact `measured_start`/`measured_end` state records, `entry_pass`/`effect_pass`/`constraints_pass`, `generation.method` and matching `generation.controller_sha256` |
| `outcome.json` | Matching verifier hash, `independent_goal_checks=true`, boolean `task_success` and `safe_exit`; independent verdict must agree with measured final dwell |

Each measured target contains `id`, full world-axis `world_bounds`, three-component
`linear_velocity` and `angular_velocity`, boolean `independently_supported`,
`grasped` and `intact`. Each robot contains full-body `world_bounds`, those velocity
vectors, boolean `stable` and `legal_ground_support`, `held_object_ids` and integer
`suspended_object_count`. Bounds must include the actual whole shape, not its
center or an arbitrarily chosen base link. The trusted adapter owns this extraction.

Delivery requires the correct intact target wholly in D, released, independently
supported and below the frozen speeds for the final uninterrupted hold, with the
robot stable and below its speed limits. A target spawned in D does not establish
new delivery. Physical exit requires the whole robot inside Q, all support legal,
no held/suspended objects and final uninterrupted dwell. A robot spawned in Q does
not establish exit. Any hard violation, dropped state/action, nonfinite data,
missing measurement, mismatched endpoint, changed identity, candidate-only plan,
reordered/omitted mapping or budget overrun fails closed as `unknown`.

H1S-01 instead requires `outcome.policy="original_frozen_verifier"`,
`original_verifier_artifact="original-verdict.json"`, a hashed original verdict
and matching verifier identity. The caller remains responsible for freezing the
correct historical verifier. This package does not modify its scores.

A legal executed route may differ from the candidate route. The validator checks
its own complete measured refinement, not a mandatory tool ID or candidate trace.
`witnessed_full` is a scoped trusted execution with a delivered outcome. It does
not claim all random starts, task-specific necessity comparisons, three repeats,
independent reproduction, human approval or formal admission.

A valid Q exit leaves `task_success=false` and `abstention_correctness=null` unless
the caller passes `expected_certificate_sha256` from an independent certificate
review. The matching `infeasibility-certificate.json` must bind task, scene, robot
and public rules, declare `review_status="verified_necessary_conditions"` and
`all_legal_routes_covered=true`. This checks the reviewed certificate's identity
and scope; it does not prove its mathematical argument. Search failure, budget
exhaustion or a successful exit never generate an infeasibility certificate.

All unit fixtures are explicitly synthetic and temporary. Their success paths
exercise the checker and must never enter the physical-run counts. Native P4 GPU
evidence uses its dedicated logger/verifier; a converter to this portable bundle
has not been implemented. Report those validation paths separately.

## Required substep hardware and integrity audit

The binding also freezes `physics_dt`, integer `physics_steps_per_control` with
`control_dt = physics_dt * physics_steps_per_control`, unique `joint_names` and
same-length `joint_lower`, `joint_upper`, `joint_velocity_limit`,
`joint_effort_limit` arrays. Each command row requires `actuator_interval` with
`physics_samples` exactly equal to the decimation and measured
`joint_position_min`, `joint_position_max`, `joint_speed_abs_max`,
`joint_effort_abs_max` arrays. Every interval must remain within the frozen limits;
control-rate snapshots alone are insufficient.

`run.integrity_audit` must record `world_parameter_hash_unchanged=true`,
`monitor_coverage_complete=true`, and integer zero counts for
`runtime_pose_writes`, `runtime_parameter_writes`, `attachment_creations` and
`external_root_wrench_calls`. These are recorder-derived measurements. Missing
coverage fails closed rather than treating an absent alarm as a passing monitor.
Per-skill `entry_pass`, `effect_pass`, and `constraints_pass` remain trusted adapter
predicate results; the generic checker validates their presence and binding and
recomputes the aggregate D/Q goal. It does not independently derive arbitrary
skill effects from free-text contracts.

## Frozen original H1 execution reports

`python -m infra.h1_tasks.baseline_report RECEIPT_DIRECTORY --out REPORT.json`
collects a new execution of the unmodified original fixed reference. It preserves
the original verifier result, runtime and source identities, actual event anchors,
measured stage endpoints and available generated low-level plan spans. The native
state log includes per-control-step joint state, actual torque and substep actuator
extrema; full solver snapshots are sampled separately. This report deliberately
sets `fine_grained_refinement_complete=false`: coarse associations do not replace
independent checks of each low-level primitive's entry, effect and transition.
The original self-collision-off privileged scope remains explicit.

A portable wrapper is available for subsequent allocated-GPU runs:

```sh
python -m infra.h1_tasks.run_frozen_baseline --packet /path/to/verified/baseline-packet --receipts /path/to/new-receipts --name gamma-fixed-new --wall-seconds 3540
```

Verify the downloaded archive before extraction (expected SHA-256
`300630ebf965ef40e6b8c16c231dfe7671fd84dabd70684b842b4138f6d03e03`); retain the
`fixed/evidence/validation.json`, `fixed/workspace`, `reproduce.py` and
`packet_common.py` paths. The wrapper rechecks the frozen source hashes, requires
CUDA, refuses an existing output name, freezes the wall budget, captures package
and hardware identities and preserves the original result. Run it inside a Gamma
allocation, never on a login node. The current first run uses an equivalent local
wrapper saved with its Slurm script; it is not altered during execution.
