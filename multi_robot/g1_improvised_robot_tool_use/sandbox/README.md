# M3 sandbox (shared infra runtime, two robots)

2026-10-22: the author approved v0.1 parts and hook-bar development. The hooks
prototype passes a lift/5 s hold/return/release probe and reaches box placement
and release from the task start. Shelf pickup and the complete route remain
unresolved; all new hook runs are development evidence. See
[the run history](../acceptance/resume-20261022/hook_chain_history.json).

M3 is built on the shared sandbox runtime (`infra/sandbox`, layout of `infra/sandbox/ONBOARDING.md`) from the start,
as M1 is: the world, the recorder, the scorer, the monitors and the verifier are the ones every agent run uses, and
the reference expert and the feasibility probes are programs on the agents' command channel (plus the privileged
reference channel), judged by the same verifier.

## Layout

```
launch.py                 seal a scenario, run a delivery (or the reference expert), verify; --version M3-v0.0 runs
                          the scene as specified (development only), --dev-edit / --dev-model / --dev-set set up probes
agent_sdk/README.md       the agent guide shipped in the public bundle; examples/hello_robots.py, examples/noop.py
reference/Dockerfile.reference   reference image = public agent image + the expert's code closure
pipeline.json             automatic checks (infra-pipeline/1)
trusted/  (never in a bundle)
  scenarios.py   sealed Scenario: per-episode scenes from ../scene.py, per-robot sensors, budgets, reference_channel
  world.py       SandboxWorld(MultiRobotChannel): M3Env (../env.py) unchanged; both robots' LowCmd laws in one 200 Hz
                 loop (M1's command laws); G1 fall (pelvis < 0.40 m or tilt > 45 deg) and wheeled-robot tip-over (> 30
                 deg) end the episode
  sensors.py     G1: the shared G1 suite; wheeled robot: infra.sandbox.mobile_sensors.MobileArmSensors (mounts per variant)
  statelog.py    50 Hz rows: G1 standard fields, wheeled-robot base/joints/effort/fingers, objects, contacts per robot
                 link class and object, the ball's and the wheeled robot's support forces, G1-robot contact; 5 Hz snapshots
  scoring.py     four stages along the ball's way (ball_touched, out_of_container, off_shelf, delivered); route
                 diagnostics (which robot touched the ball, robot on a box, robot carried by the G1, G1 on a box)
  monitors.py    shared monitor suite (m3-monitors/0: shared defaults, not calibrated)
  verifier.py    episode judgement + shared run-level verifier; cross-check with multi_robot/evaluate.py
  server.py      shared worker + reference_info / reference_state when the scenario enables the reference channel
tests/            test_static.py (bundle allowlist, generator, specified scene, v0.1 geometry, sealing), test_scoring.py
                  (stage negatives), agents/escape_probes.py (M1's probe set adapted)
```

No existing infra file was changed. Shared pieces used as they are: `MultiRobotChannel`, `RobotLimits`,
`mobile_sensors.MobileArmSensors` / `PerRobotSensors`, `statelog.ChunkedLog` / `ContactSplitter`, `monitors.run_profile`,
`verifier.verify_run`, `launcher.launch`, `agent_sdk/multisandbox`. The wheeled robot's model is M1's mobile-gripper
rendering with M3's part changes applied (`../wheeled_model.py`); the expert imports M1's G1 and mobile-gripper skills.

## Running (from the repository root, `D:\rsi_vla\genesis_env\Scripts\python.exe -X utf8`)

```powershell
# development, local process; hello / no-op
python -m multi_robot.g1_improvised_robot_tool_use.sandbox.launch --mode dev --seed 3 --isolation process --backend cpu `
    --agent-dir multi_robot/g1_improvised_robot_tool_use/sandbox/agent_sdk/examples -- python hello_robots.py
# a feasibility probe on the scene as specified (see ../README.md for the list and the dev edits each one uses)
python -m multi_robot.g1_improvised_robot_tool_use.sandbox.launch --mode dev --seed 1 --isolation process --backend cpu `
    --version M3-v0.0 --dev-reference -- python -m multi_robot.g1_improvised_robot_tool_use.solution.run_expert --phase x5_drive
# the v0.1 reference chain (development; --start swing|pick|lift_off|deliver with dev edits starts later)
python -m multi_robot.g1_improvised_robot_tool_use.sandbox.launch --mode dev --seed 3 --isolation process --backend cpu `
    --fixed-scene --dev-reference -- python -m multi_robot.g1_improvised_robot_tool_use.solution.run_expert --phase all
# re-judge a run
python -m multi_robot.g1_improvised_robot_tool_use.sandbox.trusted.verifier --run <run>/trusted
```

Simulator runs go through the shared GPU queue when they render (`gpu_queue.py --slots 3 -- ...`); the `dbg-*`
development runs used `--backend cpu --no-video` with proprio-only sensors.

## Validation so far

| run | what | verdict |
|---|---|---|
| smoke-hello-01 (v0.0), smoke-v01-hello-01 (v0.1) | hello_robots, process isolation, proprio only | not void, score 0 |
| unit tests | tests/test_static.py (18), tests/test_scoring.py (5) | 23 OK |
| probe-* / dbg-* (50 runs) | feasibility probes and expert development (../README.md, "Runs") | judged by the verifier like any run; none void |
| dbg-deliver-03 | dev start: floor pick, then delivery to the tray | success 1.0 (the `delivered` predicate with its dwell and support check, on a real delivery) |
| probe-shelfpick-01, dbg-shelfpick-06, dbg-chain-10 | dev start on the box: shelf pick | 0.55 (ball_touched, out_of_container, off_shelf) |

Current integration evidence: `acceptance/pipeline/20261022-222514-all.json`
passed all three tiers; strict post-checks verified process/container exits,
45 escape probes, request chains and two grading episodes. The 11-step pipeline
now performs those post-checks itself. Use `infra.sandbox.release_check` for
current-source freshness; historical passes alone cannot authorize release.

Still incomplete: a full-start positive reference, monitor calibration,
physical shortcut audits, random and three-layer coverage, standalone subtask
validation, human review and independent reproduction. The six latest hooks
brace failures are recorded in
`acceptance/release-20261022/brace_diagnostics_20261023.json`; all score 0 and
non-VOID. Unit/integration checks do not turn these into successful references.

## Runtime notes (no infra change made)

* M3 needed nothing new from `infra/sandbox`: the multi-robot channel, `mobile_sensors`, the recorder, the monitors
  and the verifier are used as they are.
* Development starts later in the chain need `--dev-edit` placements. The verdict then credits stages the placement
  skipped: dbg-deliver-03 scored out_of_container and off_shelf with the ball placed on the floor. Development
  verdicts are labelled `privileged_reference` and never count. A shared way to mark a dev-edited run's stage credit
  as "placed" would make these runs easier to read.
