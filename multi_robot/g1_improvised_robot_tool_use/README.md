# Version F — G1 High-Shelf Retrieval via Improvised Robot Tool Use

**Current development status, 2026-10-25:** the fixed hooks-v0.1 functional reference is complete and [published](../../infra/task-m3-en.html): normal-start 2/2, score 1.0, 411.16 s, no benchmark monitor alarms and zero physical state restores. G1 raises X5 for box-supported shelf retrieval, returns it to the floor, and X5 releases the original 65 mm ball in the goal tray. Small motion is accepted if operation remains valid. Same-author / same-parameter repeats are array-identical, not independent seeds or second-person reproduction. This privileged reference replays the first 222 s and then uses feedback control; ordinary RPC, general planning, human sign-off, coverage and formal admission remain pending (`admitted=false`). See [current evidence](../../infra/m3-current-evidence.json) and [audit](acceptance/release-functional-20261025/reproduction-audit.json). The frozen portable source is in the release package; the development source remains on C:.

**Historical integration evidence (superseded by 474/475):** a new run from normal initialization, without physical state resets, reaches the return-lift hold at 349.36 s before a controller geometry guard stops it. Local re-evaluation remains 0.55, with no monitor alarms, falls, tips or object drops; it does not complete delivery. Separate checkpoint tests now complete the turn and lower the small robot about 19 cm onto the floor while retaining the object. Floor-support transfer, hand withdrawal, final delivery and complete-run repeats remain unverified. These are privileged reference diagnostics, not ordinary RPC or formal admission results.

**Author decision, 2026-10-22:** the user approved the complete v0.1 part proposal below and continued
development of a transverse hook-bar carry handle, with the load seated close to the wrist.
The side-squeeze `handles` model and its recorded failures remain available as the baseline.
At that historical stage the hook-bar prototype was a development variant; hardware effort limits,
friction, timestep and solver settings stay unchanged. No end-to-end success was claimed at that stage.

**Earlier physical update, 2026-10-23:** the 6.389 kg hooks prototype passes the placed-start
lift / five-second hold / return / release probe (`resume-hook-lift-20261022-i`),
and full-start prefixes place and release it on the low box at 82.68 s. Full
retrieval remains unresolved. Six new brace trials stop on lost bilateral
contact before acquiring the ball (99.20–113.56 s). Their verifier results are
all score 0, non-VOID, no alarms. These iterations use different expert sources
and do not constitute repeat successes.

The final trial, `release-hook-braked-chain-20261023-2`, holds the real wheel
angles and uses the original transport grasp. It loses left contact at 113.56 s
(0 / 1.10 N; 5.63 degrees tilt). The tighter finger clamp was removed because it
pushed the base backwards even with wheel angles held. Every trial keeps the
bilateral-contact and tilt guards, hardware limits and original physics. See
[six-trial contact and wheel diagnostics](acceptance/release-20261022/brace_diagnostics_20261023.json)
and the original full videos linked there. The hooks variant is still a
development part, and `admitted` remains false.

**Category:** Tool Discovery · **Embodiment:** Multi-Robot (Unitree G1 and a small wheeled robot with a manipulator) · **Task ID:** M3 · **Priority:** P0/P1 — creative tool use and multi-robot cooperation

**Historical baseline (2026-10-21):** Genesis task env on the shared sandbox runtime ([sandbox/](sandbox/README.md)). The scene as specified ([task.json](task.json), rebuilt as scene `M3-v0.0`) is **not solvable** (feasibility below). The proposed scene `M3-v0.1` makes the wheeled robot a tool the G1 must place; the author approved its part changes on 2026-10-22. The reference expert is **partial**. Each wheeled-robot stage works from a placed start: the shelf pick from the box, and delivery to the tray (verifier success). The G1 lifts the 6.4 kg robot every time, but set it on the box in only 2 of 8 attempts: its wrists saturate at the 5 N m hardware limit. No run has succeeded from the task start. Not admitted ([admission.json](admission.json)).

A Unitree G1 must retrieve a small ball from a box on a high bookshelf and place it in a designated region. The target height and limited box opening make precise direct grasping difficult. Several boxes that could serve as steps and a small wheeled robot equipped with a manipulator are available. The agent can control both robots, but receives no predefined tool-use plan or cooperative program.

## Task

- Explore shelf height, box opening, target position, and the G1's reach, grasp precision, and body stability to assess direct-grasp feasibility.
- **Solution A — Box-Assisted Retrieval:** Discover that available boxes can form temporary steps, increase the G1's effective operating height, and enable an attempt to retrieve the ball from the container.
- **Solution B — Robot-as-a-Tool:** Discover that the wheeled robot's manipulator may be better suited to precise ball grasping, while its own height or workspace is insufficient. Explore having the G1 lift or support the lightweight wheeled robot to raise its manipulator's operating height, then use that manipulator to grasp the ball.
- Independently write a multi-robot control harness to coordinate the G1's grasping, lifting, and stable support with the wheeled manipulator's positioning, extension, visual servoing, grasping, and object handoff.
- Use execution feedback to assess the G1's effective payload, the wheeled robot's mass and center of mass, manipulator workspace, support stability, and target-grasp precision. Select or revise a physically executable strategy.

Solutions A and B are candidate strategies for benchmark design, not plans supplied to the agent. A scene with two controllable robots does not require using both in every instance. Credit valid box-only or direct-retrieval routes where feasible, and distinguish them from instances that require the second manipulator.

## Advanced Variants

Vary shelf height, box load capacity, wheeled-robot weight, manipulator reach, and the G1's effective payload. Physical validation must establish at least one feasible solution for every admitted solvable instance.

Include instances suited to step construction, instances requiring the second robot's manipulator, and instances where combining both tools is necessary. Validate these route distinctions rather than inferring them solely from height or payload metadata. Keep tool roles, route labels, and reference programs outside the agent's evaluation instruction.

## Physical Validation

For box-assisted routes, validate box load capacity, placement, footholds, ascent, manipulation posture, and descent with the retrieved ball. Height gain alone does not establish a feasible route.

For robot-as-a-tool routes, validate grasp or support contacts on the actual wheeled robot, combined center of mass, payload and torque limits, balance, and reactions from manipulator motion. Check that the arm and gripper can operate while the base is supported or lifted, with adequate visibility and access through the container opening. Validate acquisition, stable support, precision grasping, handoff or direct delivery, and eventual stable placement of the supported robot.

Combined routes require end-to-end validation under the combined load. Do not substitute a scripted attachment, frozen robot base, teleportation, or a hidden cooperative macro for physical lifting and support. Missing controller capabilities remain explicit coverage gaps.

## Evaluation Contract

Retrieve the correct ball from the shelf container and place it stably in the designated region while respecting declared contact, fall, damage, and load constraints. Define tolerances and the final dwell time before evaluation. Allow valid alternative strategies and direct delivery by either robot; handoff is required only when the chosen route needs it.

**Functional acceptance clarification, 2026-10-25:** the user prioritizes the complete operation: G1 lifts or supports the small robot, the small robot retrieves the object from the shelf container, and the object is placed at the target. Minor jitter or relative rotation is acceptable when it does not prevent the operation. A perfectly rigid grasp is not an additional success condition. Retain the declared physical limits and end-to-end delivery checks; checkpoint lifts and offline path checks do not establish complete-task success.

Record observations and robot-specific action status, capability probes, tool choices, support changes, synchronization, grasp attempts, failures, recovery, and both robots' interaction costs. Evaluate whether feedback changes the agent's capability estimates and produces a workable harness revision. A verbal proposal to lift another robot is not evidence of physical success.

This task extends the task catalog with embodied robot-as-a-tool discovery. The existing M1 humanoid–mobile-gripper collaboration task remains separate.

## Implementation Priorities

- [x] Build the G1, wheeled manipulator, shelf container, ball, candidate step boxes, and destination region (`env.py`, `scene.py`: the specified scene `M3-v0.0` and the proposed `M3-v0.1`).
- [x] Validate direct reach and grasp limits and the basic controllers for both robots (probes and offline bounds below).
- [ ] Validate complete box-assisted and robot-as-a-tool solutions in suitable configurations. Box-assisted is ruled out on both scene versions. Robot-as-a-tool is partial on `M3-v0.1`.
- [x] Provide observations and control interfaces for both robots, and implement support, grasp, delivery, and constraint checks (`sandbox/`: shared runtime, four scored stages, monitors, verifier).
- [ ] Add physically validated variants that favor or require different routes, including combined-tool instances.
- [ ] Evaluate autonomous affordance discovery, route selection, and cooperative harness construction under the P0/P1 plan.

## Implementation (shared sandbox runtime)

| file | what |
|---|---|
| `env.py` | `M3Env`: Genesis scene from a scene dict (boxes, URDF compounds, the ball, visual markers), the G1 (29 DoF + Dex3, hardware effort limits), the wheeled robot as a variant from `wheeled_model.py`, seeded reset, privileged read-outs |
| `scene.py` | sealed generator: `M3-v0.0` is `task.json` unchanged (development only), `M3-v0.1` (default) is `scene_v01.py`; layer 1 randomises the robots' starts, the tray, the bin and the ball across the shelf and both boxes (the 0.18 m box stays at the shelf) |
| `scene_v01.py` | the proposed scene (part changes listed below) |
| `wheeled_model.py` | the wheeled robot: `original` is `real_wheeled_x5.urdf` (M3's source) with the ARX X5 limits; `handles` is M1's mobile-gripper rendering with M3's part changes (rear battery, carry handles, flat finger pads) |
| `instruction.md`, `task.toml` | the agent's instruction (no route hint) and the task spec |
| `sandbox/` | the run harness on `infra/sandbox` (world, sensors, recorder, scoring, monitors, verifier, launcher, agent SDK): [sandbox/README.md](sandbox/README.md) |
| `solution/run_expert.py` | one program for the probes (`--phase x5_drive / x5_ball / g1_step / g1_lift / x5_shelf_pick`) and the reference chain (`--phase all [--start swing / pick / deliver]`), run over the agents' command channel with the privileged reference channel |
| `solution/probes.py` | the feasibility probes |
| `solution/m3_skills.py` | wheeled-robot skills on M1's `x5_skills` (variant wheel track, handle frame, ball grasp, creep to the box's edge, shelf pick) |
| `solution/x5_plan.py` | MuJoCo collision model of the arm, its own base and handles, the shelf, the bin and the box. Damped IK plus RRT-Connect gets the arm in under the 0.90 m board |
| `solution/carry.py` | the G1 holding the wheeled robot by its handles: walking pickup (GR00T), and the waist swing in one crouched held stance (onto the box, off it) |
| `solution/chain.py` | the v0.1 chain: stance, swing onto the box, shelf pick, swing off, delivery to the tray |

M1's G1 skills (`g1_skills`: GR00T walking, held stance, arm IK, Dex3 presets), wheeled-robot skills (`x5_skills`,
`x5_kinematics`, `route`) and reference link are imported read-only. No `infra/` file was changed.


## Feasibility of the scene as specified (M3-v0.0, `task.json`)

The prototype scene is rebuilt unchanged as scene version `M3-v0.0` (`scene.py`; development mode only). Every route
fails on it, for physical reasons that no controller can remove:

| question | evidence | finding |
|---|---|---|
| Does the specified wheeled robot drive and steer? | `probe-x5drive-01` (video), `dbg-x5drive-01` | 0.25 m/s for 4 s moved it 0.54 m (the fixed rear sphere carries ~40 % of its weight and drags); a 92 deg in-place turn command turned it 17 deg; a 0.6 m closed-loop drive took 68 s. **It tipped over (33 deg)** the first time its arm reached 0.40 m ahead with the tool down: 1.2 kg base, drive axle 7 cm ahead of the base centre, nothing in front of the axle (M1 saw the same in x5dev-01). |
| Can its gripper take the ball? | `probe-x5ball-01` (video), `dbg-x5ball-02` | The 9 cm ball is wider than the gripper's 8.88 cm full opening. The simulator nevertheless let the open fingers slide over it with ~1 cm of interpenetration and lift it: not a physically valid grasp, and it fell out within 2.5 s in the slower run. |
| Can the G1 step onto a box? | `probe-g1step-01` (video), `dbg-g1step-01` | The L1 gait (GR00T WBC) walking into the 0.18 m box at 0.3 m/s **fell after 5.1 s** and pushed the box 7-9 cm. Climbing needs a planned step-up controller; H1's verified 0.18 m step-up exists only outside the sandbox channel. |
| Can the G1 reach the ball in the crate (rim 1.72 m)? | offline kinematic bound (`g1_target.py`, MuJoCo G1 model with collisions, no balance) | No: the closest the palm gets to the ball's centre is 17 cm from the floor and 12-12.5 cm standing on the 0.18 m box, the 0.32 m box or both stacked (0.50 m); fingertips stay >= 11 cm away. The crate's 0.2 m walls stop the hand above the ball. |
| Can the wheeled robot reach it, or be put where it can? | arm envelope (M1's `x5_kinematics`) | Its arm reaches at most 0.89 m above its base centre, the grasp point at most 0.45 m above it with the tool within 45 deg of down. Reaching into a crate whose rim is 1.72 m needs the base at >= ~1.3 m: on any box stack it is at most 0.64 m, and the G1 cannot hold or set a 5-6 kg robot higher than ~1.0 m. |
| Is any route trivially solvable? | the rows above | No. The scene is **not solvable** as specified. |

## Proposed scene changes (M3-v0.1, `scene_v01.py`) - author decisions

Smallest set of part changes found that keeps the room's pieces and makes each robot short of the ball in a
different way, so that tool use is needed. Each item is a property of a part, none a simulator setting.

1. **Container**: the crate moves from the 1.52 m board to the back of the 0.55 m board (under the 0.90 m board,
   0.31 m clearance) and becomes a low bin (0.30 x 0.35 m, 10 cm walls); the ball rests against its back wall,
   0.43 m in from the shelf's front. *Why*: the G1's arm is short and its torso cannot enter the 0.31 m opening; the
   wheeled robot's arm is long (0.76 m from shoulder to grasp point) but its base is low.
2. **Ball**: 6.5 cm instead of 9 cm (the gripper opens 8.9 cm).
3. **Shelf side and back panels** (M1's steel-shelf change; the shelf stands against the wall): the bin is reachable
   only through the front opening.
4. **Wheeled robot** (`wheeled_model.py`, variant `handles`): M1's base layout (drive wheels under the centre, swivel
   casters front and rear; M3's base tipped), a 2 kg base whose battery sits 12 cm behind the centre (with the mass at
   the centre the robot rocked forward when the arm reached out, dbg-x5ball-01), **two carry handles** (side plates
   with a lip, 0.75 m high so a G1 grips them standing or slightly crouched), **flat finger pads** (the source finger
   touches only with a 15 x 18 mm tapered tip ridge; a ball squeezed there rode up and rolled out, dbg-x5ball-04).
   6.39 kg.
5. **Goal**: a 0.40 m tray with a 3 cm rim on the floor (a released ball rolls on a flat floor, dbg-x5ball-04).
6. **Layer 1 box layout**: the 0.18 m box stands against the shelf under the bin (lateral +-0.06 m, gap 3-12 mm);
   the 0.32 m box elsewhere. Moving a box into place is left for a later layer.
7. **Still open: the carry interface.** With the side-plate handles the G1 can lift the robot but cannot hold it
   steady (see the blocker below). A handle that loads the G1's wrists less is the next part change to try.

Alternative routes stay allowed. Offline, the wheeled robot standing on the 0.32 m box at the shelf also has
collision-free grasps. The box-only route (the G1 on a box) is ruled out by the G1 bound in the table below.

What v0.1 asks of the robots (offline bounds and probes):

| claim | evidence |
|---|---|
| the G1 alone cannot grasp the ball | kinematic bound (G1 model with the shelf, panels excluded = generous): palm >= 6.8 cm from the ball's centre in GR00T's posture envelope (pelvis >= 0.50 m, pitch <= 0.45 rad, any waist and arm), >= 8.9 cm standing on the 0.18 m box; fingertips touch it (1.3-1.9 cm) but cannot lift it over a 10 cm wall it rests against. A random search with deeper crouches (pelvis 0.35 m, torso pitch 0.9 rad) found 4.0-7.1 cm in different runs: the bound is a search, not a proof, and a G1-alone physical probe is still open. |
| the wheeled robot alone cannot | from the floor no collision-free grasp exists (IK + collision sampling, 511 IK solutions, 0 collision-free) |
| the wheeled robot (v0.1 variant) drives, turns and stays up | `probe-x5drive-02` (video): 0.92 m in 4 s at 0.25 m/s, 79 of 92 deg commanded in place, a 0.6 m closed-loop drive 5.8 cm off; the tool 0.40 m ahead and down tilts the base < 1 deg; **reaching 0.65 m ahead low tips it over** (21.7 deg, then the episode ends): a limit the agent has to find |
| it grasps and holds the 6.5 cm ball | `probe-x5ball-03` (floor, tool down): 26.9 N per finger, held 15 s, slip 0.05 mm/s along the fingers |
| the wheeled robot on the 0.18 m box can take it | collision-free grasps with the tool 55-65 deg from down, up to 0.675 m from its base centre (the ball is 0.64-0.66 m out with the base at the box's front edge). An RRT path (`solution/x5_plan.py`) gets the arm in and out under the 0.90 m board. **dbg-shelfpick-06, probe-shelfpick-01 (video)**: placed on the box, it crept to the edge, took the ball out of the bin and off the shelf by 27 s, and held it 10 s in the carry pose (score 0.55: ball_touched, out_of_container, off_shelf) |
| a G1 can lift the robot | v0.0 handles probes `dbg-g1lift-10/11`: in a held stance, the robot backed its handles in between the hands, a 19 N squeeze per side lifted it 3-7 cm clear. GR00T cannot stand or walk with it: the pelvis pitched 24 deg and the G1 ran 3-4 m. v0.1 chain runs (waist swing, below): lifted 0.27-0.33 m clear in 8 of 8 attempts, but held unreliably |


## Reference expert on M3-v0.1 (partial)

`solution/chain.py` is one program for both robots on the agents' command channel. It reads ground truth from the
privileged reference channel and runs under real limits: G1 hardware efforts, the ARX X5 limits, no welds and no
teleports. It runs in development reference mode (`sandbox/launch.py --dev-reference`). All runs below use the
nominal scene (`--fixed-scene`, seed 3) on the CPU backend. `--start swing|pick|deliver` starts later with the robots
placed by `--dev-edit`. Stage by stage:

| # | stage | status | evidence |
|---|---|---|---|
| 1 | the robot raises its arm; the G1 walks to its stance behind the 0.18 m box, facing the shelf | works | dbg-chain-01..04, 11, 13: at the stance at 45.5-45.7 s. GR00T stops 11-15 cm past the planned spot, which the later stages tolerate |
| 2 | the G1 crouches and turns its waist to -90 deg; the robot backs its handles in between the hands | works 8 of 8 | handles within 1.3 cm, yaw 0.8-5.2 deg off. Slow: 26-53 s |
| 3 | squeeze, then lift 0.27 m | robot off the floor 8 of 8, still upright after the lift 5 of 8 | squeeze 16-25 N per hand. The robot tipped at the end of the lift in chain-01/02/05 (blocker above) |
| 4 | swing over the box, set the robot on the box's rear half, let go | 2 of 8 | **dbg-chain-11: set squarely on the box at 133.8 s** (1.6 cm off the line, 0.7 deg; stage `x5_on_box` at 135.4 s). **dbg-chain-04**: on the box at 133.5 s, but 9 cm off the line, with a hand left on a handle. Failures: chain-03 set it down and it tipped; chain-06 and chain-13 the G1 fell (in chain-13 its stance slid 15 cm forward during the swing and one hand let go) |
| 5 | creep to the box's front edge, plan the arm in under the 0.90 m board, take the ball, carry pose | works with the G1 away (3 of 3), unreliable with the G1 crouched behind the box (1 of 3) | G1 away: probe-shelfpick-01 (video), dbg-shelfpick-06, dbg-shelfpick-07 (5.5 kg robot) took the ball off the shelf at ~27 s; 07 then dropped it during the hold. G1 behind the box: dbg-chain-10 took it (29.5 s). dbg-chain-09 struck the shelf board with a 60 deg plan (55 deg is now first). **dbg-chain-11** (from the task start): the creep was fine (7 mm), but a finger struck the bin (38 N) on the way in and pushed the robot 15 cm across the box, and the G1's body touched the robot; no ball. Fixes tried and reverted: 2 cm plan clearance plus a G1 keep-out box (dbg-chain-12: arm on the bin, the G1's hand on the robot), and tucking the G1's arms (dbg-chain-14: the tuck knocked the robot over). Not counted: chain-07/08, where the default arm pose ran into the 0.55 m board (fixed), and chain-04, where the G1's hand blocked the creep |
| 6 | reverse to the box's rear half; the G1 grips again, lifts the robot off, swings it to the floor at its right side | fails | dbg-chain-10: the ball, held 14 mm off the grip centre after the shelf grasp, fell out of the carry grip while reversing (34.4 s). The G1's reach to the handles then shoved the robot (66 N) and it tipped (36.3 s) |
| 7 | drive to the tray square to one side, put the ball in it | works from a placed start | **dbg-deliver-03**: floor pick, then delivery: released in the tray at 38.3 s, verifier success (1.0). deliver-01/02 failed before two fixes: dither at the spot with 1.2 rad/s turns, and a diagonal approach that ran the front caster into the tray's rim. In both the ball was shaken out |

No run has gone from the task start to the tray. The furthest is **dbg-chain-11**: the robot was set squarely on the box at 135 s of the 420 s budget, and the shelf pick failed at 152 s. Stages 5 and 7 take ~80 s together, so the time budget is not the limit. The code in `solution/` is the code dbg-chain-11 ran (docstrings aside).

Expert defects still open besides the blocker:

* **Carry grip.** After the shelf grasp the ball sits ~14 mm off the grip centre. In the carry pose (closing axis
  vertical) it fell out under small jolts: dbg-chain-10, dbg-shelfpick-05/07. After a centred floor grasp (5.6 mm)
  it rode 25 s of driving (dbg-deliver-03).
* **G1 too close.** The G1's hands and body stay close to the parked robot. A hand left on a handle (dbg-chain-04), contact during the shelf pick (dbg-chain-11/12), and an arm tuck that knocked the robot over (dbg-chain-14) all came from the tight stance the waist swing needs.
* **Regrip.** The G1's reach for the regrip has no collision check against the handles (dbg-chain-10).
* **Walk accuracy.** The G1's walk to the stance overshoots by 13-15 cm.

### The open blocker: the G1's two-hand carry of the wheeled robot

GR00T cannot stand or walk with the 6.4 kg robot held ~0.3 m ahead. Everything loaded therefore happens in one held,
crouched stance (legs locked, M1's stance mode): the waist yaw is the transport joint. The robot is picked up at the
G1's right side, swung round over the box and set down. The grip is a side squeeze of the two handle plates (16-25 N
per hand). Each hand carries ~31 N of weight. The contact sits 0.1-0.2 m ahead of the wrist pitch axis, so the static
moment alone is 3-6 N m against the G1's 5 N m wrist pitch/yaw limit. In the traces both wrist pitch joints sit at
-5 N m from the lift onwards. The robot then turns in the grip (dbg-chain-05: yaw to 75 deg, roll to -27 deg) and
tips over, is put down crooked, or the G1 falls:

| run | start | lifted (s) | outcome |
|---|---|---|---|
| dbg-chain-01 | task | 113.2 | robot tipped at the end of the lift (one hand lost contact) |
| dbg-chain-02 | task | 116.9 | tipped at the end of the lift |
| dbg-chain-03 | task | 118.9 | swung over the box, set on it at 129.0 s (68 N on the box, 14 deg tilt), tipped at 129.8 s |
| dbg-chain-04 | task | 118.8 | **set on the box at 133.5 s** (63.9 N, 8.5 deg, 9 cm off the line). The G1's released hand kept pressing on a handle (~10 N), one wheel spun, and the creep ended 9.2 cm short of the edge with a 7.4 deg yaw error, so no grasp existed |
| dbg-chain-05 | swing (dev) | 57.6 | fingers pitched 0.2 rad down to relieve the wrist: tipped at the end of the lift |
| dbg-chain-06 | swing (dev) | 56.0 | lighter robot (5.5 kg: 1.3 kg base, 0.35 kg handles): the G1 fell during the swing (66 s) |
| dbg-chain-11 | task | 119.2 | **set squarely on the box at 133.8 s** (1.6 cm off, 0.7 deg); the shelf pick then failed (stage 5) |
| dbg-chain-13 | task | 90.7 | the G1's stance slid 15 cm forward during the swing, one hand let go, the G1 fell (105.3 s) |

Options, all part changes (author decisions, none proven):

1. **Handles that load the wrist less**: a transverse bar the palms hook under, seated near the wrist (H5's hook
   grip), instead of side plates squeezed by the fingers. This is the most promising option.
2. **A lighter robot**: tried at 5.5 kg (dbg-chain-06, dbg-shelfpick-07). It was no better: the G1 fell, and the
   lighter base dropped the ball once while holding it on the box.
3. **A ramp part** the wheeled robot drives up onto the box. This removes the lift, and with it most of the G1's role.
   It is a different task.

Raising the G1's wrist limits is ruled out: those are the hardware limits, and the task rules forbid changing them.

## Runs

All runs are in `sandbox/runs/<name>` (gitignored; the run outputs go to the private Hugging Face dataset). Each was
judged by the sandbox verifier, and none was void. `probe-*` runs rendered a video through the shared GPU queue;
`dbg-*` runs are CPU, `--no-video`, proprio-only.

| runs | scene | what | result |
|---|---|---|---|
| smoke-hello-01, smoke-v01-hello-01 | v0.0, v0.1 | hello_robots | 0, not void |
| probe-x5drive-01, dbg-x5drive-01 | v0.0 | specified wheeled robot: drive, turn, arm reach | 0.54 m of 1.0, 17 of 92 deg; tipped at 33 deg |
| probe-x5ball-01, dbg-x5ball-01..02 | v0.0 | specified 9 cm ball | slid through the open fingers with interpenetration; fell out |
| dbg-x5ball-03..05, probe-x5ball-02..03 | v0.0 + dev model / set | 6.5 cm ball, handles variant, finger pads | probe-x5ball-03: held 15 s, 0.05 mm/s slip |
| probe-g1step-01, dbg-g1step-01 | v0.0 | GR00T walking onto the 0.18 m box | fell after 5.1 s, box pushed 7 cm |
| dbg-g1lift-01..11, probe-g1lift-01 | v0.0 + handles | G1 lifts the wheeled robot by its handles | probe-g1lift-01 slipped out (16 N squeeze, 2.5 cm rise); dbg-g1lift-10/11 lifted it 3-7 cm clear in a stance, then GR00T ran away with it |
| probe-x5drive-02 | v0.0 + handles | v0.1 wheeled robot: drive, turn, arm reach | drives and turns; tipped reaching 0.65 m ahead low |
| dbg-shelfpick-01..07, probe-shelfpick-01 | v0.1 | wheeled robot placed on the box: shelf pick | 01-04 development (no grasp configuration / path); 05 dropped in the hold; 06 and probe-01 held 10 s; 07 (5.5 kg) dropped in the hold |
| dbg-chain-01..06 | v0.1 | chain from the task start (01-04) or the swing start (05-06) | table above: robot on the box once (chain-04) |
| dbg-chain-07..10, 12, 14 | v0.1 | chain from the pick start (robot placed on the box) | 07/08 creep blocked by the arm pose; 09 arm struck the shelf; 10 ball out at 29.5 s, then dropped and tipped; 12 (wider plan clearance, G1 keep-out) arm on the bin; 14 (G1 arm tuck) robot knocked over at 10 s |
| dbg-chain-11, 13 | v0.1 | chain from the task start, final code (11) | 11: on the box at 133.8 s, no ball; 13: the G1 fell during the swing |
| dbg-deliver-01..03 | v0.1 | floor pick, then delivery to the tray | 03 success (1.0) after two fixes |

## Core Capabilities Evaluated

Creative Tool Use · Robot-as-a-Tool · Autonomous Affordance Discovery · Multi-Robot Harness Construction · Embodied Self-Modeling · Physical Reasoning · Long-Horizon Planning

See the [Tool Discovery category](../../README.md#tool-discovery) and the benchmark proposal in [English](../../doc/self-modeling-benchmark-v4-en.html#team-m3) or [中文](../../doc/self-modeling-benchmark-v4-zh.html#team-m3).
