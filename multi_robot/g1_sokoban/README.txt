Multi-G1 hidden-map box-clearing puzzle (prototype v2)

See TASK_NOTE.txt for the agreed task, oracle definitions, generation/verification
pipeline, evidence and implementation checkpoints. run_push_gamma.sbatch runs
a separate single-G1 calibration using the existing H1 controller scene.

Two free-base G1 robots start without a global map. Four movable crates obstruct
routes between rooms, including the shared doorway. Each robot must reach its
own labeled goal: g1_a to orange, g1_b to blue. Both must stand inside their own
goals, upright and slow, simultaneously for 2 seconds. Crates have no delivery
slots. Pushing them clears routes or creates space for the other robot to pass.
Either robot may help with any crate; pulling and grasping are outside the rules.

Physical validation entry points (privileged controllers, not hidden-map agents):
  sbatch multi_robot/g1_sokoban/run_skill_gamma.sbatch --speed .18 --height .65 --distance .9 --seconds 60
  sbatch multi_robot/g1_sokoban/run_navigation_gamma.sbatch
  sbatch multi_robot/g1_sokoban/run_reference_gamma.sbatch
  python -m multi_robot.g1_sokoban.review_run /path/to/recorded/run
Short and one-cell push/retract skills and separate doorway/yielding navigation
have passed Gamma tests. The full original 24-action puzzle was physically
completed in Gamma job 8006717 and its sampled trajectory independently reviewed;
see TASK_NOTE.txt for exact job IDs, scope, initialization fixes and failures.

Observations and communication
- Physical observe_agent(robot_id): own first-person RGB, own joint positions and
  velocities, body-frame gravity/angular velocity, own target ID/color, and inbox.
  It omits global layout, object poses, goal coordinates and invisible peer state.
- send_message(sender, recipient, text): explicitly exchanged text, at most
  256 UTF-8 bytes per message and 16 pending messages per recipient. No automatic
  shared map. Message bandwidth and sent bytes can be measured independently.
- LocalEpisode is a separate symbolic development adapter with radius-2 local
  cells and wall/crate/peer occlusion. It provides odometry relative to each
  robot's own start, not global coordinates. It is not a physical RGB sensor model.
- TaskScene.observe(), overhead images, scene.json and oracle plans are privileged
  developer/evaluator artifacts. Do not feed them to an unknown-map agent.
  The fixed development map is inspectable in source; unseen layouts remain work
  for a future evaluation cohort.

Unknown-map baseline (one independently reviewed development-layout witness)
Gamma job 8011370 completed 24 actions / 5 pushes in 279.18 simulated seconds.
Both robots held their own goals for 3 s. Independent review of 13,959 samples
and complete public-input CPU replay passed. This is an experimental candidate,
not an unseen-map performance claim or formal task admission.
  sbatch multi_robot/g1_sokoban/run_hidden_gamma.sbatch --seconds 1200
  python -m multi_robot.g1_sokoban.review_hidden /path/to/run --out /path/to/new-review.json
  python multi_robot/g1_sokoban/replay_inputs.py --run /path/to/run --source /path/to/hidden-source-JOBID --out /path/to/new-replay.json
Each job freezes its native task source and records every public agent input,
RGB image hash, explicit message, motor target and separate evaluator trace.
Only the public RGB, own proprioception and received messages enter HiddenAgent.
Its maps are inferred from pixels and exchanged through bounded messages; joint
planning treats unobserved space as blocked. A sensor replay tests this causal
interface, and must not be described as another physical execution. The current
development sensor assumes calibrated, noise-free IMU increments, flat floor,
known grid spacing, colored materials and known robot/crate dimensions. These
are declared prototype conditions, not claims of arbitrary-scene perception.
Artifacts and all retained attempts:
  /fs/gamma-projects/vlm-robot/robo-si-local-tests/20261026-hidden-map/
Successful run: hidden-gamma-8011370/. See validation.json, independent-review.json,
sensor-replay.json, trajectory-summary.png and motion.mp4. The local candidate
archive is in the sibling robo-si-local-tests/releases/ directory.

Case-specific hierarchical acceptance is documented in HIERARCHICAL_WITNESS.txt.
Published evidence location (rc2, including the hierarchy):
  https://huggingface.co/datasets/IntelligenceLab/robo-si/tree/main/releases/g1-sokoban-hidden-map-0.1.0-rc2
After unpacking, run python VERIFY.py --hierarchy. The accompanying release.json
binds the archive hash and GitHub source commit. See the rc2 release notes.
The existing continuous witness maps 24 high-level operations to 76 low-level
segments and all 27,918 per-robot joint-target vectors, including preparation,
waiting and final standing. This checks high/low/trajectory representations in
one declared case; arbitrary skill composition and random-state solvability are
not prerequisites. Generate a separate annotation without rerunning physics:
  python -m multi_robot.g1_sokoban.hierarchical --run /path/to/run --out /path/to/new-mapping.json

Oracle import and local packaging (after complete physical review and replay):
  python -m infra.oracle.hidden_reference --run /path/to/complete/run
  python -m multi_robot.g1_sokoban.build_candidate --repo /path/to/robo-si --experiment /path/to/experiment --run /path/to/complete/run --out /path/to/new-candidate
Add --hierarchy /path/to/mapping-final.json to include and verify the complete
case-specific high/low/trajectory mapping in the packet.
The importer requires the retained shared-dependency manifest and hardware record.
The packet contains an integrity verifier; it does not upload or publish anything.
  python VERIFY.py
  python VERIFY.py --review


Implementation
The scene is generated from levels/exploration.json on a 0.9 m grid. Physical
bodies move continuously; the grid planner never sets their poses. Initialization
sets starts; step() accepts 43 absolute joint targets for each robot and advances
motor-controlled physics. No attachment or object-force command is exposed.
Task parameters are in task.json. RobotGoalTracker checks arrivals and joint
hold time but returns task_success=null: goal geometry does not establish legal
push-only execution. A full-map physical reference now completes the development
level. Independent sampled checks cover crate floor clearance/tilt, robot posture,
contact duration and both own-goal dwell. Complete no-grasp/contact certification,
and generalization remain pending. The observation-matched baseline now has one
complete, independently reviewed development-layout witness.

The full-map A* solver is a privileged reference upper bound, not the unknown-map
agent. It uses interleaved cardinal moves, forbids chain pushes and pulling, and
reports search_limit if the search budget expires. Static crate-corner pruning
is disabled in the robot-target task because parking boxes in corners can help.
The older two-crate delivery level is retained in levels/crossing.json for rule
regressions; its goal logic and results do not describe the current v2 task.

Run from the repository root with the existing genesis conda environment:
  python -m unittest multi_robot.g1_sokoban.test_task -v
  python -m multi_robot.g1_sokoban.preview --out /tmp/g1-sokoban-exploration.html
  sbatch multi_robot/g1_sokoban/run_gamma.sbatch

The interactive preview defaults to robot 1's local view. Its global toggle is
explicitly privileged, and its trajectory comes from the full-map oracle.
The batch job runs natively on Gamma, without a container or sandbox, and checks
8 seconds of independent standing control for both G1s, finite crate/robot state,
agent-camera images and goal diagnostics. The standing policy is not a task
solver. Each output directory must be new. Job artifacts are stored under:
  /fs/gamma-projects/vlm-robot/robo-si-local-tests/20261025-sokoban/gamma-JOBID

Next implementation milestones: robust skills across initial perturbations and
new layouts; complete contact-validity checks; robust exploration/communication;
unseen maps and matched single-robot comparisons; then three/four robots and an
Isaac backend. Do not claim cooperation necessity or benefit merely from having
two robots present. This is outside the published task inventory.
