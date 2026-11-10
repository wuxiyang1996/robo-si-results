# Free-standing G1 table tennis

A hierarchical state-based reference for one legal return with a floating-base, 29-joint Unitree G1. Legs, waist and arms are controlled together through bounded motor torques. The simulation includes real foot-ground contact; the pelvis is neither fixed nor actuated.

The reference has three goals: prepare interception, return to the target, and recover stable ready stance. A CUDA search scores 28,033 ballistic candidates. Scratch-data right-arm IK and quintic trajectories specify racket motion; a 500 Hz contact-constrained inverse-dynamics QP controls the entire body. MuJoCo integrates physical contacts at 2 kHz. The QP enforces floating-base dynamics, stance constraints, unilateral friction pyramids and motor effort limits. Its predicted contact forces are never injected into the simulator.

See the [English task page](../../infra/task-g1-table-tennis-en.html), [中文任务页](../../infra/task-g1-table-tennis-zh.html), [expert contract](expert_contract.json), [task manifest](task.toml), and [data card](DATA_CARD.md).

[Owner-approved publication](PUBLICATION.md) · [Download release](https://github.com/wuxiyang1996/robo-si/releases/tag/table-tennis-0.1.0)

## Run and reproduce

From the repository root, using Python 3.12 and the pinned dependencies:

```bash
python -m pip install -r humanoid/g1_table_tennis/requirements.txt
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
python -m humanoid.g1_table_tennis.run --device cuda --case nominal --video --output /tmp/g1-tt-run
python -m humanoid.g1_table_tennis.verify /tmp/g1-tt-run
python -m humanoid.g1_table_tennis.run --device cuda --replay /tmp/g1-tt-run --output /tmp/g1-tt-replay
python -m humanoid.g1_table_tennis.campaign --device cuda --output /tmp/g1-tt-campaign
python -m unittest discover -s tests -p test_g1_table_tennis.py
```

For Gamma allocation, use `scripts/run_gamma.sh OUTPUT_DIRECTORY`. CUDA planning fails explicitly if CUDA is unavailable. `--device cpu` supports local debugging. Physics runs on CPU; CUDA executes candidate scoring and EGL renders video. No real-time timing claim is made.

## Scoring and evidence

The independent grader uses `stage-scoring/1`: legal racket contact 25, net clearance 25, opponent landing 20, target landing 15, stable recovery 15. The first four are once-only milestones. Recovery is live at the endpoint and includes both foot support forces, root stability, ready joint tolerance and a continuous 0.12 s dwell. Falling after landing revokes recovery and full success while preserving earlier valid milestone credit. Integrity failures clear every awarded point. Planner phases and success labels award no points.

The public stance requires each foot's measured contact force above 5 N after 0.05 s, horizontal foot slip below 4 cm, root height at least 0.65 m, and tilt below 20 degrees. Recovery tightens tilt to 5 degrees, root linear speed to 0.03 m/s and angular speed to 0.05 rad/s. Motor efforts follow the model; joint speed is capped at 6 rad/s. These are simulation task thresholds, not hardware safety certification.

`trajectory.npz` records all physics substeps, root/joint/ball states, torques, reference derivatives, racket pose, contacts, foot forces, slip and COM. `segments.json` maps every action to a contiguous trajectory range. `verify.py` independently reconstructs stage scores and checks HL→LL, LL→trajectory and HL→trajectory. Fresh torque replay starts from reset and checks physical state reproduction; no recorded state is imposed during replay.

## Scope

Four exact public feeds, three repeats each, establish a finite reference cohort. Hold, zero-torque and unreachable-feed controls are included. Development failures are retained. There is no random-distribution success claim. The feed has no initial spin, aerodynamic model or perception noise. This is stationary double support with whole-body balance, not locomotion, continuous rallies or doubles. The 120 g racket is a passive rigid wrist attachment, not a learned grasp. No learned WBC weights or HOPE G1 controller are required.

The release is a published scoped engineering reference. Owner approval is recorded in PUBLICATION.md. Reproduction by another person and isolated untrusted-agent runtime integration remain separate technical steps. Existing benchmark task counts are unchanged.

## Extension task and metric design

[Interception, relocation and rally metrics](../../infra/planning/table-tennis/extensions/README.md) cover G1 stepping, fixed-arm wide interception, powered-rail movement and continuous rallies. This is a proposed evaluation design; current reference results do not validate these extensions.
