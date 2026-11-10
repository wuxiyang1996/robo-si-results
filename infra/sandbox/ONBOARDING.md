# Putting a task on the shared sandbox runtime

Every task is evaluated in the same sandbox (infra pages: sandbox, scoring and verification, acceptance). The
runtime lives in `infra/sandbox/`; a task's `sandbox/` keeps only what is specific to the task. The most complete
example is H4 (`humanoid/g1_ramp_bridge_construction/sandbox/`): copy its structure.

## 1. Layout

```
<task>/admission.json                 infra-admission/1 record (python -m infra.sandbox.records validates it)
<task>/sandbox/
  __init__.py
  launch.py                           SandboxTask + the task's CLI options -> infra.sandbox.launcher.launch()
  README.md                           how to run it, what was validated (numbers, run directories), open gaps
  agent_sdk/README.md                 the agent guide shipped in the public bundle (task-specific notes only)
  agent_sdk/examples/hello_robot.py   reads info + every sensor, sends one command, finishes
  agent_sdk/examples/noop.py          finishes without moving (grading / no-op control)
  trusted/                            never in a bundle
    __init__.py
    scenarios.py    Scenario dataclass (mode, episodes, sim_time_limit_s, max_observations, dev_resets, sensors,
                    label, + the task's sealed episode specs), save()/load(), task(...) generator
    world.py        SandboxWorld(CommandChannel or MultiRobotChannel): builds the task's own environment, unchanged
                    physics; _apply(cmd) = one 50 Hz control step; _check_end; public_info; episode lifecycle
    sensors.py      the robot-mounted sensor suite (G1: infra.sandbox.sensors.RobotSensors / AppliedEffortSensors)
    statelog.py     StateLogger(infra.sandbox.statelog.ChunkedLog): one row per control step (standard fields below)
    scoring.py      stage predicates (wrap the task's own evaluator; reuse its constants, never re-tune physics)
    monitors.py     MonitorProfile + run_all() (infra.sandbox.monitors.run_profile), calibrated (section 5)
    verifier.py     verify_episode(ep_dir) + TaskVerifier + verify_run(trusted, out=None)
    server.py       thin: run_worker(__doc__, Scenario, make_world)
    record_reference.py   the existing expert, unchanged, recorded into the sandbox format and judged (section 4)
  tests/            test_static.py (bundle allowlist, scenario sealing), test_scoring.py (stage negatives),
                    test_monitors.py (exploit cases trigger, positive does not), agents/escape_probes.py
```

## 2. Module contracts (copy from H4 and adapt)

* **launch.py**: `BUNDLE = L.BundleSpec(examples=..., readme=..., instruction=...)`, `SANDBOX = L.SandboxTask(task_id,
  task_dir, image="g1<id>-agent", net_prefix, worker_module, verifier_module, bundle, ...)`, `build_bundle()`,
  `main(argv)`: `L.add_common_arguments`, the task's own options, `L.parse_argv`, `L.check_common`, build the private
  scenario, `return L.exit_code(L.launch(SANDBOX, args, command, scenario))`.
* **server.py**: `run_worker(__doc__, Scenario, lambda sc, d, video: SandboxWorld(sc, d, video=video))`.
* **world.py**: inherit `infra.sandbox.world.CommandChannel` (one robot) or `MultiRobotChannel` (several robots,
  `self.limits = {robot: RobotLimits}`, `self.cmd = {robot: full command}`, sensors wrapped in
  `infra.sandbox.sensors.NamespacedSensors`). Required attributes: `sc, t, steps, over, cmd, observations, episode,
  episode_dir, events, sensors, env, digest0` (and for one robot `q_lo, q_hi, vel_limit, kp_max, kd_max` and the torque
  limit named by `TAU_LIMIT`; `num_joints` if not 43). Implement `_apply(cmd)` (advance physics one control step under
  LowCmd: mode 0 motor = tau_ff + kp (q* - q) + kd (dq* - dq) every physics substep, clipped to the torque limit;
  mode 1 servo = the simulator's implicit PD; a task whose environment only takes joint-position targets offers mode
  1 only via `MODES = (1,)` (one robot) or `RobotLimits(modes=(1,))`, and says so in `public_info`),
  `_end_episode(reason)` (event `episode_over`, then `try: self._check_params("episode_end") finally: <close the
  log>`: a changed world is logged as an event inside the sealed record, the record is sealed in any case, and the
  error then voids the run), `reset_dev()` (`self._use_reset()` first), `next_episode()`,
  `public_info()` (instruction, budgets, robot limits, sensor spec; nothing about objects, seeds or scores), `close()`.
  Torque limits are the real robot's: `min(task effort, MJCF actuatorfrcrange)` (`infra.sandbox.world.hardware_effort`).
  Check world parameters every 500 control steps (`self._check_params("periodic")`).
  Scenes built without a batch axis: `statelog.world_params`, `full_state` and `set_full_state` handle both layouts,
  but the G1 sensors and `ContactSplitter` index environment 0; wrap such an env in a read-only view that adds the
  axis, as `humanoid/g1_tabletop/sandbox/envview.py` does.
* **Shared task layers** outside the task directory (for example `humanoid/g1_tabletop/sandbox` for the two tabletop
  tasks) are listed in `SandboxTask.source_files` so they enter the source manifest.
* **statelog.py**: rows contain the standard fields `t, root_pos, root_quat, joint_pos, joint_vel, tau, obj_pos (K,3),
  obj_quat (K,4), obj_vel (K,3), obj_ang (K,3), contact (K objects x 4 classes: hand_left, hand_right, foot, other)` plus
  whatever the task's predicates need; meta.json lists `bodies` (log order), `contact_objects`, object sizes and
  masses, `joint_names`, `effort`, `source_hashes` (task files + `infra_hashes(extra=(<the infra add-on modules the
  task uses>,))`; the core runtime is always included, other tasks' add-ons never), `simulator()`. The shared
  `world_params` digest covers link masses and geometry friction ratios; a task whose cheats could go through motor
  armature or force ranges adds them in its log's `_world_params` (as M2 does).
* **verifier.py**: `verify_episode(ep_dir)`: `statelog.check_manifest`, load, world-parameter digests, `sc0 =
  scoring.score(log, meta)`, `alarms = monitors.run_all(...)`, `M.apply_alarms(res, alarms)`, windows -> rescore,
  the task's own evaluator as a cross-check (`success_disagreement` flag), score in [0, 1]; any exception -> score 0
  with the error. `TASK = TaskVerifier(task_id, version, verify_episode=lambda d, sc, i: verify_episode(d),
  code_files=(...), task_toml=...)`; `verify_run(trusted, out=None) = infra_verifier.verify_run(trusted, TASK, out)`.

## 3. Rules

* The sandbox wraps the task's existing environment **unchanged**: same scene, physics options, friction, solver
  settings, assets. Never change physics parameters to make something pass; if a task needs a fix, it is a change to
  parts or scene layout decided by the task's author.
* Do not edit the task's `solution/` (experts may be under active development by other people), other tasks, or the
  existing files in `infra/sandbox/`. Robot-generic additions the runtime lacks (for example a quadruped sensor
  suite) go in a **new** module `infra/sandbox/<name>.py` and are reported.
* The agent gets only robot-mounted sensors and the joint command channel. No method sets poses, sizes, masses,
  friction or simulator options; nothing an agent sends reaches anything but the joints.
* Scores come only from the trusted records. Positive evidence comes from the reference expert recorded by the
  sandbox recorder and judged by the sandbox verifier (section 4), never from the expert's own success flag.

## 4. Reference expert evidence (record_reference.py)

Run the existing expert script unchanged, as a black box, on a sealed scenario, with the sandbox `StateLogger`
attached from outside (wrap the environment's step / target-application method so that one state-log row is written
per control step; wrap every Genesis setter that edits poses, states or properties after the first control step and
record the calls: expected none; gains above the command bounds are violations). Write the episode directory exactly as
the worker would (`episode_00/` with meta.json, world_params.npz, state chunks, snapshots, events.jsonl, recording.json
with `privileged_writes_after_start` and `gain_violations`, files.json), a `motion.mp4` when the expert renders one,
then `verify_episode()` it. Its verdict must be success with stage times matching the expert's own timeline and the
task's evaluator, and no monitor alarm. H4: `trusted/record_reference.py`, `trusted/validity.py`.

## 5. Monitors

`monitors.py` defines `PROFILE = M.MonitorProfile(version="<task>-monitors/1", view=..., thresholds=..., stage_values=...,
stages=..., chain=..., solvable_note=..., penetration=... or floor_z=..., bounds=..., extra=..., not_applicable=...)` and
`run_all = lambda log, meta, events, rec, sc: M.run_profile(PROFILE, log, meta, events, rec, sc)`. The view maps the
task's log fields onto the standard ones; command patterns are judged at the 50 Hz control rate (downsample faster
logs). Calibrate on every recorded episode: the reference positives and no-op runs must raise no alarm; synthetic or
real exploits (shaking arms, an object launched or sinking through the floor, energy from nowhere, saturated legs, a
stage spiking for one frame, a declaration on a solvable episode) must. Thresholds that differ from the shared defaults
are written in the module docstring with the measured margins.

Command patterns are judged up to 1 s before the first fall. By default a fall is the root dropping below 0.35 m;
root tilt alone is not a fall (a supported deep bend tilts the pelvis past 70 degrees, and the old 50-degree rule
left the rest of H1's canonical c unjudged, hiding 6 s of waist torque saturation). A task with its own fall
monitor passes it as `fallen` (bool per sample) in the view.

## 6. Validation checklist (all runs from the repository root, simulator runs through the GPU queue)

1. Unit tests: `python -m unittest <task>.sandbox.tests.test_static <...>.test_scoring <...>.test_monitors`.
2. Development smoke, process isolation: `launch ... --mode dev --isolation process --no-video --name <run>
   --agent-dir <sandbox>/agent_sdk/examples -- python hello_robot.py` -> non-void verdict, chained request log.
3. Container: the same with `--mode eval` (default container isolation) -> non-void; escape probes
   (`--agent-dir <sandbox>/tests/agents -- python escape_probes.py`) -> every probe as expected, violations recorded,
   run VOID; grading `--mode grade --episodes 2 ... -- python noop.py` -> one connection per episode, 0, not void.
4. Reference recordings: at least the expert's documented successes re-recorded through record_reference.py and
   judged successful; failures judged failures.
5. `python -m infra.sandbox.records` lists the task's admission.json without problems.
6. README: what was run, results with run directory names, and the remaining gaps.
7. Automatic pipeline: list the checks above in `<task>/sandbox/pipeline.json` (schema `infra-pipeline/1`, tiers
   cpu / gpu / container; a run step names its run directory and the verdict fields it must have) and run
   `python -m infra.sandbox.pipeline <task dir> --tier all` (set `INFRA_GPU_QUEUE` to the queue script). Each run
   writes `<task>/acceptance/pipeline/<stamp>-<tier>.json` with the source digest; cite it under the
   `automatic_pipeline` gate. H1's `sandbox/pipeline.json` is the example.

Simulator commands go through the queue: `python C:/Users/wuxiy/AppData/Local/Temp/claude/d--rsi-vla/2f795ddc-4e2e-4209-82f7-00dd0d1f3417/scratchpad/unify/tools/gpu_queue.py -- <command>`
(the queue path is specific to this rollout). Use `D:\rsi_vla\genesis_env\Scripts\python.exe -X utf8`.

## 7. Release scope

Release preflight defaults to the main tool benchmark, including its R9 tool-layer requirement.
The explicitly selected standalone sequential-manipulation profile is checked with
`python -m infra.sandbox.release_check <task dir> --scope standalone`.
It currently supports the declared disk-count layers of Hanoi. The specification and admission must carry the
same `[release]` fields (`scope = "standalone"`, `main_benchmark_included = false`, and `decision_record`).
The decision file records the user's scope choice; it is not a human video review or an admission signature.
All physical, human, isolation and current-source pipeline gates still apply. A standalone pass cannot be used
as main benchmark admission; the default check continues to reject that scope.

## 8. Known gaps of the runtime (2026-10-21, found while onboarding H2, M4 and the tabletop tasks)

* `BundleSpec` always bundles the G1 model and the GR00T weights. A task with another robot builds its bundle through
  the `build` hook of `launch()` (M4 does this).
* `monitors.pre_fall_mask` uses the G1's fall rule (pelvis below 0.35 m or tilted over 50 degrees). Another robot
  passes a log whose root height is shifted (M4 adds 0.21 m to the Go2 trunk height).
* `run_profile` notes "no joint data" for a multi-robot task that judges command patterns per robot in `extra`; the
  task overrides the note (M2, M4).
* The G1 sensors and `ContactSplitter` expect a batched scene (see the `envview.py` pattern above).
* Genesis contact forces jump from step to step under load; predicates on support forces use a trailing mean (H2
  uses a 1 s mean). There is no shared helper yet.
