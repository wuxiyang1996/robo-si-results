# H6 physical task sandbox

**2026-10-23: not admitted.** The canonical box remains handle-free.
`trusted/record_reference.py` records through the bounded command channel,
snapshots the expert sources and audits every 200 Hz physics sample. It rejects
state/property writes and actuator/step bypasses. The formal recorder's new
development-handle run `release-handle-reference-20261022-2` lifts at 36.315 s,
climbs all ten ascent treads, passes the peak at 295.38 s, and stops at 338.68 s
before the first descent follow-foot step. Its 4.685 mm foot IK error exceeds
the unchanged 4 mm tolerance. It reaches 12/20 route predicates, with no
placement or final success: score 0, non-VOID, no alarms or state writes.
All 16,934 command rewards replay exactly across 67,737 physics samples.

The [unsigned full-video review packet](../acceptance/release-20261023/handle-reference-2-review/index.html)
contains original-video hashes, stage times and empty human fields. The tested
2 kg box with 20 cm handle posts is a development part; this incomplete run
does not establish canonical feasibility. The earlier 50 Hz pickup/two-step
positives remain historical diagnostics.

The canonical side-pinch controller now retains the optimized full pelvis
pose, keeps a fixed foot-heading frame, and avoids repeatedly lowering the
height target through successive optimizers. The complete
[development history](../acceptance/release-20261023/plain_pickup_history.json)
records finalized outcomes and links the original videos. New development
runs snapshot their full expert source closure and refuse nonempty output
directories. None is a formal full-task reference.

The fixed-waist descent failure is reproducible in offline planning. Allowing
small pelvis rotations solves that kinematic segment, but no such change has
been physically validated or enabled in the full-chain controller. See
`acceptance/release-20261023/descent_scan.json` and `descent_rotation_scan.json`.
Offline feasibility is not physical evidence. Older scans using an obsolete
hardcoded torso mass remain explicitly invalidated in
`acceptance/release-20261022/offline_scan_status.json`.

This package runs the G1 box pickup → stairs up → peak → stairs down → ground
placement → release and stand task through a trusted Genesis worker. Its
public agent interface reuses H1's robot-mounted sensors, authenticated RPC,
43-joint control and optional planning/balance helpers. The [task card](../task_card.md),
[machine specification](../task.toml) and [admission record](../admission.json)
describe the contract and outstanding evidence. **H6 is not admitted: a
complete dynamic reference and human acceptance are still missing.**

Since 2026-10-21 the worker skeleton, launcher, agent container, command
channel, chunked state log, monitors and run-level verifier wrapper come from
the shared runtime [`infra/sandbox`](../../../infra/sandbox/ONBOARDING.md);
H6 keeps its scenarios, world adapter, monitor profile (`trusted/monitors.py`)
and binary full-task scorer. Two policies changed with the move: recordings
made with other trusted sources are re-graded and flagged
(`recorded_with_other_sources`) instead of voided by a source-hash lock, and
the shared monitors run on every episode (a void alarm voids the run; success
inside an alarm window is withheld). Each run directory holds `trusted/`
(verdict, video, hash-chained request log, sealed scenario and delivery,
`run.json`, `agent_stdout_XX.log`, `episode_XX/` logs) and one `workspace_XX/`
per episode.

The [2026-10-19 validation report](validation.json) records 96 unit tests
(one Windows symlink-permission skip), 56 checked asset hashes, three fresh
container episodes across the three layers, an all-sensor/video episode,
and an invalid-authentication/private-RPC negative case. Valid hold-only
episodes each contain 41 physics samples over 0.2 seconds and score zero;
the negative case is VOID/0. A separate 63-bit-seed development check restores
pose, velocity and contact state exactly and verifies actual actuator effort.
These checks validate execution infrastructure, not the full transport policy.

中文：已验证三层容器运行、六类传感器与录像、越权拒绝及完整开发重置；
各正常测试仅保持初始姿态并得 0 分，完整搬运的物理成功仍待验证。

## Run from the repository root

Use the Python environment installed from `requirements-genesis.txt`. This
development command starts one physical episode, executes the example through
the real command channel, records it and invokes the offline verifier:

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe -m humanoid.g1_box_stair_transport.sandbox.launch task --mode dev --isolation process --backend cpu --sim-time 1 --sensors proprio --no-video --agent-dir humanoid/g1_box_stair_transport/sandbox/agent_sdk/examples -- python hello_robot.py
```

The example only exercises the interface and should score zero. The launcher
returns exit code 1 for an incomplete task as well as for invalid runs; inspect
the verdict's `void`, `score` and reason to distinguish them. Process mode is
development only: it is not a security boundary against malicious agent code.

For container evaluation, supply a directory containing your controller and
its dependencies. Docker must be available. Evaluation and grading reject
process mode. They default to container isolation:

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe -m humanoid.g1_box_stair_transport.sandbox.launch task --mode eval --agent-dir path/to/controller -- python agent.py
D:\rsi_vla\genesis_env\Scripts\python.exe -m humanoid.g1_box_stair_transport.sandbox.launch task --mode grade --episodes 9 --agent-dir path/to/controller -- python agent.py
```

GPU physics is the default; `--backend cpu` selects CPU. `--no-video` disables
trusted recording images. `--sim-time` sets the simulation budget and
`--budget-min` the per-episode agent wall budget (default 60). Omit `--sensors`
for all six modalities. Use `--layer 1`, `2` or `3` to restrict a diagnostic
run. Evaluation/grade seeds are privately sampled unless a trusted operator
provides `--seed`; agent code cannot choose a seed or read the sealed scenario.

Default grading uses three independent primary seeds × three cumulative
layers, for nine episodes. Each episode runs the same sealed submitted files
in a fresh process/container; files written by one episode are not reused by
the next. This stratification is distinct from three exact repeats of a fixed
seed. Default scenes keep ten steps per side. `--stairs 2` through `--stairs 10`
set that count; `--fixed-scene` uses the default dimensions and payload instead
of randomizing geometry. Trusted Python callers can use
`scenarios.task(num_steps=None)` to sample the 2–10-step range or
`randomize=False` for the exact default dimensions. Candidate ranges are not yet physically
validated. There is no public subtask/checkpoint CLI.

## Trust boundary and observations

`launch.build_bundle()` explicitly includes the SDK, instructions, robot-only
MJCF/meshes, generic planning code, local GR00T helpers and examples. It excludes
the task specification, environment, generator, scorer, solution recordings,
seeds and trusted run data. The bundle, delivered program and scenario are
hashed before execution. Docker receives the public image and per-episode
workspace, not the repository or trusted directory; its only task network
endpoint is the authenticated robot worker.

Allowed calls are `info`, `status`, `observe`, `command`, `command_sequence`,
`declare_infeasible`, `finish` and budgeted dev-only `reset`. Declaring
infeasibility or calling finish is not success. The trusted worker uses explicit
PD at 200 Hz and clamps the actual applied torque to the actuator limits.
Mode 0 applies feedforward plus position/velocity PD; mode 1 is target servo,
using position PD and velocity damping while ignoring feedforward and requested
velocity. The sandbox does not use Genesis implicit PD for force enforcement.
There is no root/object pose command or attachment
operation. Private planning may use a robot model, but its states do not alter
the physical simulation. Invalid requests are recorded for the verifier.

Public modalities are `proprio`, `rgb`, `depth`, `lidar`, `tactile` and
`foot_force`. Their models and mounts are disclosed by `info()`; all readings
come from robot-mounted sensors. Proprioceptive IMU yaw is relative to episode
start. LiDAR is emulated from four depth views, rather than a real Livox scan
pattern. Hand and foot forces are in link frames. Object poses, base world
coordinates, hidden mass/friction, task stages and score flags are withheld.
The raw 174-dimensional training observation is privileged and never returned
to sandbox agents.

## Trusted records and offline scoring

Runs live under `sandbox/runs/<run>/trusted/`: sealed scenario, delivery and
bundle identity; worker/RPC logs; per-episode state logs, solver snapshots and
physical parameter/source manifests; and `verdict.json`. These are operator
artifacts, not agent observations. The verifier checks integrity and replays
the contact-based scorer at every 200 Hz physics sample. It recomputes whole
foot and box footprints and ignores any supplied progress/success claims.
Unrun grading episodes count as zero. The only task score is 1 for full
physical completion; all partial progress is diagnostic and scores zero.

Each executed joint command also produces a private `control_reward` event,
using `TaskCore.reward`: `20*success_edge - 10*failure_edge -
0.001*mean((action-previous_action)^2)`, where the accepted joint target is
converted to `action=(q-default_joint_pos)/0.25`. The first previous action is
zero. A terminal command can contain fewer than four physics steps and still
produces exactly one reward. Its event is written before the episode is sealed.
The verifier independently replays command/state history and exposes
`reward_audit` in the trusted verdict. Missing, unsealed, misaligned or
inconsistent reward events invalidate current physical recordings. This
reward never crosses the agent RPC and is distinct from the binary score.

The sensor-consuming reference oracle is in
[`solution/oracle_agent`](../solution/oracle_agent/README.md).
[`solution/run_oracle.py`](../solution/run_oracle.py) prepares a private
joint-only delivery and a reference-matched ground scene, then uses this same
container launcher and verifier. The trusted Python scenario hook is operator
configuration, not an agent RPC. Successful `observe` calls record returned
modality names in the trusted request log, allowing sensor consumption to be
audited independently of agent telemetry.

An IK/FK replay cannot become physical evidence by renaming files: recording
source, actual action execution, state-write policy, timestep continuity,
physical parameter hashes and monitor results are checked. Diagnostic solver
snapshot helpers are internal. Scenario loading currently rejects checkpoint
and subtask entry until the required physical chain and restore validation
exist. Geometric reference videos remain in `solution/runs/` separately.

## Selfcheck and acceptance

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_box_stair_transport/scripts/check_task.py --check-assets --bundle --tests
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_box_stair_transport/scripts/check_task.py --require-admitted
```

The first command checks metadata, generator invariants, installed asset
hashes, public bundle contents and H6 unit regressions without starting a
physics rollout. The second deliberately fails while admission is incomplete.
Neither a passed selfcheck nor a valid zero-score physical smoke run proves
task feasibility. Required work is tracked in `admission.json`: complete
physical oracle across seeds/layers, physical negative and repeatability runs,
real subtask starts, signed video review, independent reproduction, difficulty
calibration and explicit resolution of R1/R9's tool-discovery scope.

中文：这里是物理任务的隔离执行与复核入口。默认每侧 10 级，路线最终要求在地面目标区
放箱、松手、站起并稳定 2 秒。开发模式可用本机进程，正式评测必须使用容器。
公开观测仅来自机器人传感器，174 维训练观测、场景真值和评分状态不向 agent 暴露。
三层默认评分是 3 组种子 × 3 层的 9 次独立执行，不是同一场景重复 3 次。
当前完整物理解与人工验收仍待完成，不能将 IK/FK 几何参考当作动力学成功。
