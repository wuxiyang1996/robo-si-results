# Reference trajectory data card

This finite dataset records four public exact configurations, three repetitions
each, four action replays, one stationary-arm control and one nonexecuted invalid
feed. The three repetitions of a configuration are deterministic resets, not
different random seeds. No confidential test split is included.

Each episode begins at the normal reset and uses a single continuous simulator
clock. `trajectory.npz` stores numeric arrays only and loads with
`numpy.load(..., allow_pickle=False)`:

| Array | Shape | Meaning |
|---|---|---|
| time | N | Simulation seconds, 0.0005 s spacing |
| qpos | N × 13 | Six UR joint angles, ball XYZ, ball quaternion WXYZ |
| qvel | N × 12 | Six joint speeds, ball linear velocity, ball angular velocity |
| torque | N × 6 | Actual bounded torques applied over the preceding physics interval |
| target | N × 6 | Commanded reference joint positions, held at 500 Hz |
| reference_dq / reference_ddq | N × 6 | Planned velocity / acceleration, held at 500 Hz |
| racket_pos / racket_normal / racket_velocity | N × 3 | Measured racket geometry and velocity |
| contacts | N × 5 | Measured ball contact flags: table, racket, net, floor, other |
| unsafe | N | Measured robot collision flag |
| ball_contact_force | N | Maximum ball contact force, newtons |
| segment_index | N | Low-level action index; reset row is -1 |

Coordinates are world Cartesian SI: table center at XY=(0,0), tabletop Z=0.76;
X points from the robot half to the opponent half, Y is lateral, Z is up.
UR joint order is shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3.
The reset row has no preceding command. For interval `[i, i+1)`, row `i+1`
contains the torque and target that produced state `i+1`.

`high_level_plan.json` contains current-observation planning input identity,
the selected physical contact/landing targets and three high-level subgoals.
`segments.json` maps five low-level actions to **half-open command indices** and
the corresponding inclusive state endpoints. `events.json` is recomputed from
trusted physical samples; it is not supplied by the controller.

`summary.json` records outcome, the independent scoring rubric version, physics
and planner devices, source/asset hashes, runtime, and Slurm job identity.
`sources/` freezes Python implementations, while `manifest.json` binds all run
artifacts by SHA-256. Robot meshes are supplied once in the release workspace.

`video.mp4` runs at 25 fps and displays the measured physical execution. It is a
view of the much denser 2 kHz record and is not the collision verifier. A 2.4 s
episode contains 61 frames including the reset frame (2.44 s encoded duration).

All prescribed failures are retained. Earlier development attempts live in a
separate `development/` appendix; their original parameters and scorer versions
must not be pooled with the final campaign. The first attempt used an unstable
contact setting and is explicitly invalid as a physical success witness.

The data supports reference inspection, implementation testing and imitation
experiments. Split by whole configuration/episode when constructing a new
learning experiment; do not scatter adjacent frames across train and test.
Public reference results are not evidence of unseen-distribution performance.
