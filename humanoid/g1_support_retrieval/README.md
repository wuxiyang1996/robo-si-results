# Example Task: G1 Support-Assisted Object Retrieval (Genesis + Isaac Lab)

**当前验收范围：分层证据交付。** 已有固定场景完整成功、重复与容器证据；C026 的随机 Layer1 seed63、963 也已完整成功。原三组样本全部保留，当前为两个“有完整成功证据”、一个“未确定”；不要求每个随机实例生成完整解。旧五次原生加一次容器补跑清单保留为历史计划，不再作为本次资料交付前提。仿真继续暂停，正式准入和全随机范围验证未完成。见[分层验收资料与筛查入口](../../infra/planning/h1/README.md)。

**Category:** Tool Discovery · **Embodiment:** Humanoid · **Task ID:** H1

This is an example task in robo-si. See the [project README](../../README.md) for the benchmark proposal and documentation.

The new **`H1.stool_relay` v2.1** task is defined by [TASK_CARD.md](TASK_CARD.md) and
[task.toml](task.toml): move a distant support, retrieve the elevated target, use the
lower board, return to the floor and deliver. It has a dedicated seeded three-layer
scene generator, a 1200 s simulation budget, sensor-only sandbox entry, physical
stage verifier and repeated-evaluation runner. Start with the
[relay commands](sandbox/README.md#stool_relay-v21).
Its [acceptance ledger](acceptance/readiness.json) distinguishes implemented checks
from the physical calibration, repeated expert trials and independent human review
still required for benchmark admission. The legacy five-family training environment
described below has separate observation and time-budget conventions.

The [canonical reference c](acceptance/reference_c.json) completed all nine stages
from the original start in 850.26 s, with score 1.0 and 55/55 engineering checks
under the historical relay-rubric/2.1. Under the current safety rules it is **not
successful**: sustained waist torque saturation exceeds the 3 s threshold.
The [actual sandbox command-channel run](sandbox/runs/reference-full-1/trusted/verdict.json)
also completed delivery but failed the same safety rule (longest saturation 5.9 s).
These are privileged fixed-scene runs with self-collision disabled. Repeats,
randomized coverage and independent human review remain incomplete.
[Watch the historical preview](media/stool_relay_c/motion-24x.mp4).

The current first release targets **randomized Layer 1 at the original 1.25 m
shelf**, including position, mass and friction variation. Layers 2 and 3 are
deferred. The fixed-scene C371 reference has separately passed three native
full runs and one matching C373 container run; its sealed archive does not
qualify randomized Layer 1. One [randomized original-start full run](acceptance/formal_20261025/candidate_007/runs/full-l1-seed2/full_run_audit.json)
now passes (C007, development seed 2, 1007.08 s, score approximately 1.0,
non-VOID, no safety events). Other random cases and a matching randomized
container run remain in progress.
Human sign-off and second-person reproduction remain deferred and unsigned.
See the [release scope](acceptance/formal_20261025/layer1_release_scope.json),
[current work](acceptance/formal_20261025/status.json) and
[formal admission ledger](admission.json).

A Unitree G1 (29 degrees of freedom plus two Dex3 hands, for a total of 43 joints) must retrieve a box of the instructed color from the top three shelves of a realistic cabinet and place it in a target zone. If the box is out of reach, the robot can use boxes on the floor as supports or arrange them into steps. If no support arrangement makes the target reachable, it should declare the task "infeasible."

The same task is implemented in both **Genesis** and **Isaac Lab**, with matching scenes, observations, actions, rewards, and termination conditions.

<p align="center"><img src="media/scene_bookshelf_seed101.png" width="100%"></p>

Genesis is on the left and Isaac Sim is on the right, rendering the same episode. Videos are available in [media/](media/).

## Task

| Difficulty | Target box height | Correct approach |
|---|---|---|
| `direct` | Approx. 1.05 m | Retrieve the box directly |
| `one_support` | Approx. 1.25 m | Use one low support box (0.18 m or 0.26 m) |
| `choose_support` | Approx. 1.25 m | Same as above; an additional tall, narrow box is high enough but unsuitable as a support, serving as a distractor |
| `staircase` | Approx. 1.50 m | First place the 0.45 m platform box against the front of the cabinet, then place a low box in front of it as a step |
| `infeasible` | Top surface at 2.06–2.13 m | Declare the task infeasible. These scenes contain neither the platform box nor the tall, narrow box; no stacking arrangement of the remaining floor boxes can make the target reachable |

- **Cabinets:** Three realistic CC0 models from [Poly Haven](https://polyhaven.com) (steel-frame shelves, a worn wooden bookshelf, and a narrow gray bookshelf), each with two shelf-height layouts.
- **Colored boxes:** 2–4 boxes, placed on the cabinet's top three shelves, 1–2 cm behind the front edge. The target box is alone on its shelf and at least 10 cm from the side panels, so both hands can reach its sides.
- **Floor boxes:** Up to five: two 0.18 m low boxes, one 0.26 m medium box, one 0.45 m platform box, and one 0.44 m tall, narrow box. Mass and friction are randomized each episode.
- **Robot:** Physical capability is randomized: leg torque limits are scaled by 0.85–1.0, and an additional 0–5 kg load is added to the torso.
- **Capability information:** Three levels of disclosure to the agent: `explicit` provides numerical values, `partial` provides only coarse descriptions, and `latent` provides no information.

**Actions (44 dimensions):** 43 joint position targets (default pose + 0.25 × action), plus one dimension for declaring infeasibility. The final dimension must exceed 2.0 for 25 consecutive steps (0.5 s) to count as a declaration. The control frequency is 50 Hz, and the physics simulation runs at 200 Hz.

**Observations (240 dimensions):** Proprioception (positions and velocities of all 43 joints, base velocity, and gravity direction), the previous action, the heights of the three cabinet shelves, colored box positions and colors, the target color, floor box positions, orientations, and dimensions, the target zone position, both hand positions, and capability information.

**Rewards:** +20 for success, +10 for correctly declaring infeasibility, −5 for an incorrect declaration, and −10 for falling, plus potential-based progress rewards and an action-smoothness regularization term. All weights can be adjusted in `TaskConfig.rewards`. Each episode lasts at most 60 s.

## Consistency Between Simulators

- **Same robot model:** Genesis loads the G1 MJCF from MuJoCo Menagerie directly; Isaac uses a USD converted from the same MJCF. Joint names, joint limits, and individual link masses match across both simulators, with numerical differences within 1e-6.
- **Same actuator model:** Gains follow Isaac Lab's official `G1_29DOF_CFG`. Leg torques are computed by the same function (`task_spec.dc_motor_torque`, implementing Isaac Lab's DCMotor model) and applied directly. The waist, arms, and hands use each simulator's native implicit PD controllers.
- **Same friction rule:** All contacts use the maximum of the two objects' friction coefficients. This rule is hard-coded in Genesis, and Isaac is configured to match it.
- **Same cabinets:** Both simulators use the same box-shaped collision geometry fitted to the realistic models. The textured models are used only for visualization.
- **Same scene sequence:** Random seeds are derived by hashing (seed, environment index, episode index), so episode k in environment i has the same scene in both simulators, regardless of when resets occur. `scripts/check_sampling.py` verified identical results with torch 2.7 and 2.11.
- **Measured dynamics comparison** (`probe_walk.py` + `compare_probes.py`, using the same locomotion policy across 32 environments):
  - After standing for 1 second, base positions differ by 2 mm.
  - After walking straight for 3 seconds, they differ by 4 cm.
  - During in-place turns, an individual environment's heading can differ by approximately 0.37 rad because the two engines use different contact solvers.

## Installation

Run the commands below from the repository root (`robo-si/`).

**Genesis** (Python 3.12):
```bash
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-genesis.txt
```

**Isaac:** Isaac Sim 5.1 + Isaac Lab 2.3.2 (conda environment, Python 3.11, torch 2.7.0+cu128).

**Download and generate assets** (assets are not included in the repository; the following two steps download and generate them automatically):
```bash
python setup_assets.py                                   # G1 model, locomotion policy, and 6 cabinet variants; requires numpy + trimesh
<isaaclab python> humanoid/g1_support_retrieval/scripts/convert_mjcf_to_usd.py   # Required only for Isaac
```

## Usage

```python
import sys; sys.path.insert(0, "<repo>")
from humanoid.g1_support_retrieval.genesis_env import G1SupportRetrievalGenesis

env = G1SupportRetrievalGenesis(num_envs=1024)
obs, reward, done, extras = env.step(actions)            # actions: (N, 44)
```
For Isaac, use `isaac_env.G1SupportRetrievalIsaac` (DirectRLEnv), and start `AppLauncher` first. See `scripts/smoke_isaac.py` for usage.

| Script | Purpose |
|---|---|
| `scripts/smoke_genesis.py` / `smoke_isaac.py` | Build scenes, check box placement, and measure throughput |
| `scripts/check_sampling.py` | Verify that scene sampling is independent of reset timing and torch version |
| `scripts/probe_walk.py` + `compare_probes.py` | Compare locomotion dynamics between the two simulators |
| `scripts/render.py` | Render the same episode in both simulators and combine the outputs into side-by-side images and videos |
| `scripts/prepare_cabinets.py` / `preview_cabinets.py` | Generate cabinet variants (with configurable shelf counts and heights) and preview collision geometry |
| `scripts/check_kinematics.py` | Validate the forward kinematics in `solution/kinematics.py` using Genesis |

## Current Status

- [x] Environments, scenes, observations, rewards, and consistency checks for both backends
- [x] Realistic cabinet assets with configurable shelf counts and boxes placed on the top three shelves
- [x] Isolated agent sandbox (Genesis): the agent sees only robot-mounted sensors and commands only its own joints, the world runs in a separate trusted process, and official trajectories are reused as subgoal checkpoints. See [`sandbox/README.md`](sandbox/README.md) (in Chinese).
  - Scoring is by process: each stage (using a box as a tool, placing it, standing on it, reaching, lifting, carrying, delivering the target) earns continuous credit, and an episode scores its peak progress. Task success (0/1) is reported separately.
  - Formal scoring re-runs the agent's delivered program on N new sealed episodes (`--mode grade`, optionally one per family), with a fresh copy per episode and no network or LLM.
  - The solutions in `solution/` and `verified/` read simulator ground truth, so they serve only as privileged reference solutions (feasibility proof and upper anchor), not as sandbox agents. Recorded sandbox reference scores include `step_up` (0.25) and `push_box` (0.33). The separate [fixed-scene stool retrieval program](oracle/README.md) completed one fresh episode (`full-chain-physical-v15`, seed 2) without checkpoint restoration or skipped stages: carry the stool approximately 0.989 m, climb it, place the retrieved box on the lower board, step down empty-handed, then retrieve and deliver the box. Its independent audit passed 55/55 checks, including actual actuator limits. This took 887.02 simulated seconds and uses privileged state with robot self-collision disabled; it does not establish the 60 s benchmark, repeated reliability, or generalization. The final box was physically released and settled sideways; goal acceptance checks its center, not full footprint containment.
- [ ] Reference solution (expert policy or skill graph). Existing components:
  - `solution/agile.py`: NVIDIA's G1 lower-body locomotion policy, working in both simulators.
  - `solution/kinematics.py`: Batched forward kinematics, center-of-mass computation, and IK based on the MJCF model.
- [ ] Calibrate shelf heights for each difficulty level. Current thresholds are estimated from G1 kinematics and will need recalibration using actual success rates once the reference solution is complete.

## Third-Party Assets and Licenses

- **Unitree G1 model:** From [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/unitree_g1), licensed under BSD-3-Clause and downloaded by `setup_assets.py`.
- **Locomotion policy:** NVIDIA Isaac Lab's Agile lower-body policy, downloaded from NVIDIA's public asset server and subject to NVIDIA's license. This repository does not redistribute it.
- **Cabinets:** Poly Haven's [steel_frame_shelves_01](https://polyhaven.com/a/steel_frame_shelves_01), [wooden_bookshelf_worn](https://polyhaven.com/a/wooden_bookshelf_worn), and [Shelf_01](https://polyhaven.com/a/Shelf_01), all CC0.
