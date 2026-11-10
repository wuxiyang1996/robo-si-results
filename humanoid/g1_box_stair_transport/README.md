# H6 - G1 Box Pickup, Stair Traversal and Ground Placement

**Category:** Loaded Locomotion · **Embodiment:** Humanoid (Unitree G1) · **Task ID:** H6

## Accepted layer 1 reference - 2026-10-24

The user accepted the baseline and authorized publication, website updates and cleanup. The released scope is a privileged-state reference with fixed seed 0 and **2 kg total mass including handles**. The crate uses **Poly Haven Wooden Crate 02 (CC0)**; its top carrying handles are task-authored. The library-asset version completes **1/1 full run in 587.74 s**, with score 1.0, non-VOID status and no alarms. Historical procedural-asset results remain separate: **3/3 full runs, 6/6 standalone subtasks and 12/12 infrastructure checks**.

[English report and recordings](../../infra/task-h6-en.html) · [Chinese report](../../infra/task-h6-zh.html) · [Release and downloads](https://github.com/wuxiyang1996/robo-si/releases/tag/h6-layer1-20261024) · [Acceptance and reproduction guide](acceptance/release-layer1-20261024/README.md).

The ZIP contains the frozen source, assets and dependency inventory. Reproduce through its documented entry points. The visual replacement preserves mass, inertia, collisions, friction and torque limits. Baseline delivery is complete; formal `admitted=false` and independent second-person reproduction remain pending. Tool extensions, randomized coverage, the handle-free box and layers 2/3 are outside this success claim. Original user instructions remain verbatim in the evidence records.

## Historical tool development - 2026-10-24

This development round targets layer 1; R9 and layers 2/3 are deferred. The handled-box baseline completed a continuous **587.74 s** run. Standalone subtasks using the packaged controller passed **6/6**: pickup, ascent, peak, descent, placement, and released upright settling. See the [sealed subtask summary](acceptance/release-resume-20261024/packaged_subtasks.json). Independently launched ascent, peak and descent checks newly reached their targets after 217.260, 12.475 and 239.585 s, respectively; these are not full-task times. Results from the older external entry point are excluded.

**The tool extension is not ready for publication.** Actual R1 tool deployment and use, a continuous run including the tool, randomized/boundary coverage, tool-task human review and second-person reproduction remain incomplete. A passive spring-caster candidate passed its first standalone push-deployment check in 30.02 s: the module moved from x=0.45 m to approximately 1.813 m and settled. Load bearing and a continuous pickup/stair-transport chain remain unverified. This is not a successful full tool task. See the [deployment record](acceptance/release-resume-20261024/tool_preparation.json).

![Recorded Genesis sandbox scene](media/sandbox_scene.png)

The 2026-10-19 infrastructure check passed 96 tests (one symlink-permission skip) and 56 asset hashes. Three-layer container grading, all six sensor types and recording, privilege-violation rejection, 63-bit seeds and full development reset were checked. The program only held its initial posture and correctly scored zero; it was not a full transport success. See the [validation report](sandbox/validation.json).

## Route and existing references

The route is **floor pickup, ten ascending steps, double support on the highest platform, ten descending steps on the other side, arrival at the ground goal, controlled placement and release, then upright settling for two seconds**. `peak_passed` requires valid double support at the highest platform. Reaching the goal without the peak always scores zero. Reaching the top alone is an intermediate checkpoint. The robot must hold the box during transport and complete placement, release and standing at the goal; merely holding it in the goal does not succeed.

The package implements Genesis geometry, contact-based scoring, reproducible reset, sealed scene generation, sensor/joint-command isolation and offline physical-log verification. The accepted handled baseline has full free-dynamics and standalone-subtask evidence; the R1 tool task remains unverified.

Entry points: [`task.toml`](task.toml), [`task_card.md`](task_card.md), [English agent instruction](instruction.md), [Chinese agent instruction](instruction.zh.md), and the [sandbox guide](sandbox/README.md). Formal acceptance gaps are tracked separately in [`admission.json`](admission.json).

Historical IK/FK planning, replay and generation are documented in [`solution/README.md`](solution/README.md). The complete placement/release/standing reference at [`solution/runs/reference_up_down_place`](solution/runs/reference_up_down_place/) contains 25,340 frames over 466.63 s, with 27,682 densely sampled states passing an independent geometric audit. View the [6x preview](solution/runs/reference_up_down_place/preview.mp4), [normal-speed replay](solution/runs/reference_up_down_place/motion.mp4), or approximately 41-second [placement and standing segment](solution/runs/reference_up_down_place/placement.mp4). The final box is fully within the ground goal, the minimum hand-to-box distance is approximately 0.255 m, and upright settling lasts 2.10 s.

The older 425.33 s [`reference_up_down`](solution/runs/reference_up_down/) ends while still holding the box. It remains historical transport/planning material and does not satisfy the placement endpoint. These references reuse H1's measured pickup prefix and the original experiment's 1 kg box; geometric audits do not establish physical success for the default 2 kg task. The earlier approximately 220 s `reference_10_stairs` reaches only the top and is also historical.

## Runtime

Run from the `robo-si/` root using the dependencies in H1's `requirements-genesis.txt`. The task reuses `g1_support_retrieval/assets/unitree_g1/g1_with_hands.xml` and its meshes. If robot assets are missing, run `python setup_assets.py` first.

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_box_stair_transport/scripts/smoke_genesis.py --num-envs 2 --steps 100 --image humanoid/g1_box_stair_transport/media/scene_up_down.png
```

Add `--viewer` for an interactive window; `--stairs 2` through `--stairs 10` select the steps per side. This smoke script holds the initial joint posture, checks physics stepping and saves a scene image. It does not execute the full route.

Run a development example through the public agent interface:

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe -m humanoid.g1_box_stair_transport.sandbox.launch task --mode dev --isolation process --backend cpu --sim-time 1 --sensors proprio --no-video --agent-dir humanoid/g1_box_stair_transport/sandbox/agent_sdk/examples -- python hello_robot.py
```

Expected score is zero; this checks stepping, recording and verification. Native process isolation is for development only; evaluation and grading require containers. Default `--mode grade` executes one submission over three independent seeds and three scene layers per seed, for nine runs with fresh working directories. This differs from the acceptance requirement to repeat one scene three times. See the sandbox guide for commands and trust boundaries. `--fixed-scene` uses default geometry and box properties; `--stairs 2` through `--stairs 10` set the step count.

```python
import torch
from humanoid.g1_box_stair_transport.genesis_env import G1BoxStairTransportGenesis
from humanoid.g1_box_stair_transport.task_spec import TaskConfig

env = G1BoxStairTransportGenesis(num_envs=1, cfg=TaskConfig(num_steps=10), seed=0)
actions = torch.zeros(1, env.num_actions, device=env.device)
obs, reward, done, extras = env.step(actions)
```

## Scene geometry

The robot starts at x=0.65 m; the box is on the floor at x=1.15 m. Default box dimensions are 0.30 x 0.36 x 0.24 m, mass 2 kg and friction coefficient 0.8. Stairs extend along +x with default rise 0.12 m, tread depth 0.40 m and width 1.20 m.

| Region | Default extent or dimensions |
|---|---|
| Ascent | x=1.80-5.80 m; ten treads rising from 0.12 m to 1.20 m |
| Peak platform | x=5.80-7.00 m; height 1.20 m; length 1.20 m |
| Descent | x=7.00-10.60 m; nine treads descending from 1.08 m to 0.12 m, with the final drop to the floor forming step ten |
| Ground goal | x=11.20-12.40 m, y=-0.45-0.45 m; 0.60 m gap after the stairs |
| Episode budget | 600 s |

`TaskConfig.num_steps` is the step count per side, from 2 to 10. `surfaces()` returns the ascent treads, peak platform and descent treads in route order: `2 * num_steps` solid surfaces. Floor contact verifies the final descent step. `ascent_surfaces()` retains ascent-only geometry; full references use the entire route. `goal_distance`, `goal_depth` and `goal_width` default to 0.60, 1.20 and 0.90 m.

In direct training environments, the seed determines lateral start perturbations per environment and reset; geometry and box properties are configured at construction. The sandbox additionally uses private seeds for tread geometry, width, height and box properties, with ranges in `task.toml`. It defaults to ten steps per side; only the trusted Python API's `num_steps=None` samples 2-10. The main route is identical across three layers for a given seed. Layers 2 and 3 each add two neutral boxes outside the route. These cumulative scene changes do not establish R1/R9 tool effects, usability by another embodiment or effective distractors. Development seed defaults to 0; evaluation seeds and generator parameters stay on the trusted side. Configured ranges are not validated solvability claims.

## Actions, observations and information

The vector observation and `extras` below belong to the **trusted training interface**, including world coordinates, box ground truth and scoring state. They are not public agent observations. The sandbox provides robot-mounted joint/IMU, RGB, depth, simulated LiDAR, hand tactile and foot-force sensors; it does not expose this 174-dimensional vector. Sandbox commands use explicit PD at every 200 Hz physics step and clamp applied torque. This target-servo interface does not depend on Genesis implicit-PD torque limits. Direct-training target offsets and internal actuation differ from sandbox commands.

Actions are 43 joint-target offsets in H1 order: `default_q + 0.25 * action`, subject to joint and motor-torque limits. Control runs at 50 Hz; physics at 200 Hz. The 174-dimensional observation contains joint positions/velocities (86), robot root pose/velocity (13), box pose/velocity (13), previous action (43), public scene parameters (13), and six values for route progress, pickup, consecutive endpoint settling, peak passage, legal placement and released placement. Coordinates are environment-local world coordinates; quaternion order is wxyz.

`extras['info']` returns `success/failed/lifted/route/hold/elapsed/peak_passed/placing/placed/score`. `route` counts supported surfaces completed in order, normally 0-20. `peak_passed` remains true after valid peak traversal until reset. `score` is the complete-success flag as a float: 1 for success, otherwise 0.

Automatic reset is enabled by default. Terminal observations are in `extras['final_observation']`, with valid rows indicated by `final_observation_mask`; `time_outs` marks timeout. With `auto_reset=False`, the caller retains terminal state and must stop or reset after `done`.

## Scoring and failure conditions

Checks run at every physics step and require simulator-provided contact information.

1. **Physical pickup.** First observe floor support. The box bottom must then rise more than 6 cm, each hand must contact it with more than 2 N, and upward support from the robot must exceed half the box weight.
2. **Continuous carrying.** After pickup, box contact with the floor, stairs or platform above 2 N fails, except during legal controlled placement at the goal. Losing load-bearing contact for more than 0.10 s fails. Dragging or setting the box on successive steps is not allowed.
3. **Ascent and peak.** Each tread needs actual upward foot support above 5 N for 0.08 s; skipping a support surface fails. At the peak, both feet must be supported, with their complete collision geometries inside the platform and a 4 cm margin. Only valid carrying and support duration set `peak_passed=True`; one-foot contact or airborne passage does not count.
4. **Descent on the other side.** After the peak, verify all descending treads in sequence. Jumping directly from the peak to the goal is invalid. The route ends by descending to the floor and entering the goal.
5. **Controlled placement.** All support surfaces must be completed and `peak_passed=True`. Both complete feet must be inside the goal with more than 5 N of floor support each; the complete box must be inside the goal. The box bottom must be within 1.5 cm of the floor, floor contact must exceed 2 N, and the box must be upright and slow. Both hands must still contact it above 2 N at touchdown to enter `placing`. Early release, throwing into the goal or setting the box on stairs cannot pass.
6. **Release and upright settling.** Floor support exceeding half the box weight, with both hand contact and robot support below 2 N, records `placed`. The box must remain floor-supported, robot root height must be at least 0.65 m, robot/box tilt cosines must exceed 0.94, linear speeds must be below 0.15 m/s and angular speeds below 0.30 rad/s. Both feet must remain in the goal for two consecutive seconds. Any interruption resets the settling timer.

Non-foot contact with static geometry above 20 N, significant tipping, out-of-bounds state or invalid numerical values also fail; the episode times out after 600 s. **No peak passage means no score; pickup, ascent or reaching the top alone scores zero.** Training reward gives +20 once for complete success, -10 for failure, plus an action-change penalty. Positive pickup/tread rewards were removed to prevent accumulated reward without peak traversal.

The direct training interface contains an in-environment trajectory scorer. Formal agents use the independent sandbox through sensors and actions and cannot write poses, contacts or task state. The trusted recorder logs hidden state/contact at every physics step; the offline verifier checks sealed configuration, program and asset integrity, then recomputes route and endpoint conditions. Benchmark score is always binary full success; training reward and diagnostic stage progress are not partial benchmark credit. IK/FK references aid planning only; success requires physical dynamics. Contact/posture thresholds still require calibration against full-controller execution.

Scorer boundary review checks box velocity in both the current and previous physics frames at first controlled goal touchdown, preventing an impact-induced stop from hiding excessive landing speed. Floor contact compares upward support against 2 N; other static contacts use force magnitude. After legal touchdown, brief motion or tilt resets settling if the box remains floor-supported and fully within the goal; recovery starts a new two-second interval. Raising the box bottom above 1.5 cm revokes `placing/placed`; a new controlled set-down is required. See the [scorer review](solution/SCORER_REVIEW.md) for experiments, counterexamples and limitations.

See [oracle validation](solution/ORACLE_VALIDATION.md) for container execution. That agent reads all six sensor classes and controls the robot through public joint commands. The trusted side records reward for each executed command, and the verifier independently recomputes it. `run_oracle.py` prepares the expert-matched ground start and private joint input; `check_oracle.py` checks physical evidence and reward. Passing these checks is reported separately from full-task score.

## Validation and remaining scope

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe -m unittest discover -s tests -p 'test_box_stair_transport*.py' -v
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_box_stair_transport/scripts/check_task.py --check-assets --bundle --tests
```

Synthetic state regressions cover the complete ascent/peak/descent/endpoint chain, reaching the goal without the peak, one-foot or partial-foot peak contact, skipped descent treads, absent carrying, dropped boxes, interrupted goal settling and per-environment reset isolation of peak flags. Placement regressions reject continued carrying, missing release, premature release, thrown touchdown, a box outside the goal and failure to stand. Geometric audits check peak/descent ordering, support duration, placement/release ordering, interrupted settling and invalid timestamps.

Historical validation passed 30 scorer tests, 10 geometric-audit tests and a Genesis smoke check with two environments and 20 physics steps, confirming observation dimension 174. Synthetic tests validate decision logic, not physical solvability. Sealed-scene tests cover private seeds, deterministic development, cumulative layers, layered grading, parameter boundaries, invalid input and rejection of airborne IK/FK subtask starts. `check_task.py` reports package checks separately from admission; `--require-admitted` fails while required admission evidence is missing.

The accepted library-asset release additionally records 54 task tests and 60 sandbox tests (one Windows symlink-permission skip), full decoding of both recordings, 1,339 verified packet files and 1,010 frozen source/asset files. Its 1/1 full success and historical standalone checks do not establish randomized or tool-task coverage.

- [x] Continuous ascent, highest platform, opposite-side descent and ground goal.
- [x] Mandatory peak flag, ordered contacts, carrying and endpoint settling checks.
- [x] Task card, bilingual public instructions, sealed generation, robot-sensor boundaries, physical logs and offline verification.
- [x] User-accepted fixed 2 kg handled baseline with full physical pickup, traversal, placement, release and upright settling.
- [x] Placement-endpoint IK/FK reference and videos; earlier carrying-only reference retained for planning.
- [ ] Solvability over 2-10 steps and load/geometry variation; frozen evaluation thresholds and budgets.
- [ ] Complete tool-task subtask starts and all-layer oracle evidence, broad repeat coverage, required itemized review and independent second-person reproduction.
- [ ] Resolve the distinction between R1/R9 tool discovery and loaded locomotion; validate difficulty. Neutral scene objects do not establish tool layers.

The task centers on load-induced center-of-mass changes, ascent propulsion, descent foot placement/braking and continuous whole-body balance. The fixed stairs do not require carrying boxes to build support. H1's `carry_box`, `carry_walk` and `step_up` are development references; independently working components do not establish full loaded stair transport.

See the [project task index](../../README.md), benchmark v6 in [English](../../doc/self-modeling-benchmark-v6-en.html#tasks) or [Chinese](../../doc/self-modeling-benchmark-v6-zh.html#tasks), and [acceptance requirements](../../infra/acceptance-en.html). The earlier v5 three-step-ascent definition is historical.
