> Current contract (2026-10-23): supported release and m1-monitors/3.1-numeric-boundary are implemented
> after explicit author approval. The v0.3 scene and X5 36 rad/m conversion are
> confirmed. [Current policy and validation](../acceptance/APPROVED_POLICY_20261023.md)
> supersede the pending decisions and old-rule conclusions in the dated history below.

# M1 sandbox (shared infra runtime, two robots)

M1 was built on the shared sandbox runtime (`infra/sandbox`, layout of `infra/sandbox/ONBOARDING.md`) from the start:
the world, the recorder, the scorer, the monitors and the verifier are the ones every agent run uses, and the reference
expert is a program on the agents' command channel (plus the privileged reference channel), so there is no later move
of an in-process expert into the sandbox. It is the first task on the runtime's multi-robot channel
(`infra.sandbox.world.MultiRobotChannel`: one agent, one session, two robots).

## Layout

```
launch.py                 seal a scenario, run a delivery (or the reference expert), verify
agent_sdk/README.md       the agent guide shipped in the public bundle; examples/hello_robots.py, examples/noop.py
reference/Dockerfile.reference   reference image = public agent image + the expert's code closure
trusted/  (never in a bundle)
  scenarios.py   sealed Scenario: per-episode scenes from ../scene.py, per-robot sensors, budgets, reference_channel
  world.py       SandboxWorld(MultiRobotChannel): M1Env (../env.py) unchanged; both robots' LowCmd laws in one 200 Hz loop
  sensors.py     G1: the shared G1 suite; mobile gripper: infra.sandbox.mobile_sensors.MobileArmSensors
  statelog.py    50 Hz rows: G1 standard fields, mobile gripper base/joints/effort/fingers, objects, contacts per robot
                 link class and object, cube and crate support forces; 200 Hz actual body poses; 5 Hz solver snapshots
  scoring.py     five stages along the cube's way (README of the task), success test
  monitors.py    shared monitor suite, M1 profile m1-monitors/2 (finger units and actual compound collision geometry)
  physics_poses.py   validates four actual physics-step poses per control row, with explicit legacy compatibility
  verifier.py    episode judgement + shared run-level verifier; cross-check with multi_robot/evaluate.py
  server.py      shared worker + reference_info / reference_state when the scenario enables the reference channel
  exploits.py    in-process exploit and shortcut probes, judged by verify_episode; the agent-side probes' delivery
  validity.py    every recording re-judged: positives, negatives, exploits, margins, keyframe sheets, review record
tests/  test_static.py, test_scoring.py, test_monitors.py; agents/escape_probes.py, agents/m1_probes.py
```

Additions to the shared runtime (new modules; no existing infra file was changed):

- `infra/sandbox/mobile_sensors.py`: `MobileArmSensors` (wheeled arm: proprio with base IMU and applied effort, RGB-D
  cameras from a mount description, finger contact forces) and `PerRobotSensors` (namespaced `robot:modality` names,
  each robot only its own sensors; the sandbox page's section 07).
- `infra/sandbox/agent_sdk/multisandbox/`: `MultiRobotClient` and `RobotView` (one robot behind the `g1sandbox.RobotClient`
  interface, so `g1sandbox.wbc.GrootWBC` drives the G1 while the other robot keeps its command). Shipped in the bundle.

## Running (from the repository root, `D:\rsi_vla\genesis_env\Scripts\python.exe -X utf8`)

```powershell
# development, local process; hello / no-op
python -m multi_robot.g1_mobile_gripper_retrieval.sandbox.launch --mode dev --seed 3 --isolation process --backend cpu `
    --agent-dir multi_robot/g1_mobile_gripper_retrieval/sandbox/agent_sdk/examples -- python hello_robots.py
# the reference expert while developing it: development mode, reference channel sealed in, the expert's code closure
# delivered; --dev-edit moves an object or robot in the sealed scene (recorded as dev_edits; refused outside dev mode)
python -m multi_robot.g1_mobile_gripper_retrieval.sandbox.launch --mode dev --seed 3 --isolation process --backend cpu `
    --dev-reference [--dev-edit crate=1.126,0.771,0.420,90 ...] -- python -m multi_robot.g1_mobile_gripper_retrieval.solution.run_expert --phase all|g1|x5
# the reference expert as a reference run (one evaluation episode, reference container by default)
python -m multi_robot.g1_mobile_gripper_retrieval.sandbox.launch --reference -- python -m multi_robot.g1_mobile_gripper_retrieval.solution.run_expert
# re-judge a run
python -m multi_robot.g1_mobile_gripper_retrieval.sandbox.trusted.verifier --run <run>/trusted
```

The CPU backend is used for development here: the GPU is shared with other sessions. A world builds in ~80 s on CPU.

## Validation (2026-10-21, scene M1-v0.3)

Interface and isolation:

| run | what | verdict |
|---|---|---|
| dev-hello-01, dev-cams-01 | hello_robots / camera probe, process isolation | not void, score 0; cameras as intended |
| container-hello-01 | hello_robots in the agent container (multisandbox in the image) | not void, score 0 |
| container-escape-01 | tests/agents/escape_probes.py in the container: 45 probes | all as expected, 19 violations, **VOID** |
| container-grade-noop-01 | grading, 3 sealed episodes (layers 1, 2, 3), noop.py | 0 / 0 / 0, not void |
| unit tests | tests/test_static.py (17, with the mobile arm's reach check), tests/test_scoring.py (11) | 28 OK |

Reference expert, historical final controller version (recordings predate the 2026-10-22 sealing fix;
rejudged with the current verifier, not rerun with current `world.py`; one program, both robots, the agents' command channel, real torque limits; the
verifier's verdicts):

| run | scene | result |
|---|---|---|
| full-47..51 | seeds 5, 11 (layer 1), 7 (layer 2), 9 (layer 3), 21 (layer 1) | **1.0, success** each, no monitor alarm |
| full-52, full-53 | seeds 13 (layer 1) and 17 (layer 2), never run before | **1.0, success** each |
| spread-04..06 | seed 3 three times | **1.0, success** x3; delivered at 153.1 / 120.0 / 152.9 s. CPU runs are not bit-reproducible: identical runs diverge, first visibly at the G1's release |
| **reference-03** | private evaluation seed, layer 1, **reference container** (`--reference`) | **1.0, success** |

Delivered between 119 and 199 s of the 300 s budget (layer 2: 157 and 199 s).

Development history (what failed and what changed; details in the docstrings of `solution/`):

| runs | scene / code | result |
|---|---|---|
| full-01..04 | v0.1, loose cube | 0.3: the cube slid against the crate's wall, the gripper could not grasp it (v0.2 insert) |
| full-05..11, reference-01 | v0.2 | 1.0 on seeds 3, 11, 5, 7 (layer 2) and the private seed; full-08/10 out of reach at the shelf |
| full-12..29 | v0.2, other shelf approaches | 0.1-0.2: aiming the stance, tucked arms or stepping in bursts let the gait coast into the board (reverted) |
| full-30..33 | v0.3 (crate 1-3 cm behind the board's edge) | seeds 7 (layer 2), 21: 1.0; seed 3: 0.3 (the 0.2 m/s speed floor overshot the stand, the crate went down at the arms' limit, pitched 39 deg and was dragged off in the release); seed 9 (layer 3): 0 (stopped 5 cm to the side, far hand short) |
| full-34..39 | + waist roll by IK, 0.10 m/s floor to the stand | five 1.0; seed 11: 0.7 (the cube crept through the fingers, struck the tray's rim and fell onto the tray; the flickering "delivered" then lost its credit to the progress-spike window) |
| full-40..42 | + carry with the fingers above and below the cube | 1.0 x3 |
| full-43..46, spread-01..03, reference-02 | same | 7 of 8 1.0; spread-03: 0.3, the G1 stepped in place beside the stand, the mobile gripper drove into it and tipped over (fixed: retreat at 0.3 m/s backwards, approach side chosen clear of the G1) |

Audits:

| run / check | what | finding |
|---|---|---|
| tests/test_static.py::test_mobile_arm_below_the_crate_lip | mobile gripper alone at the shelf | no arm point above 1.064 m (1.060 m from 0.10 m out); the crate's lip underside is at 1.089 m, the rim 1.10 m |
| offline IK bound + audit-g1cab-01 | G1 alone at the cabinet | palm at most 0.43 m in at 0.55 m height, nowhere at 0.15 m or lower; the tray's front rim is 0.65 m in. Throwing or sliding the cube in is not excluded by geometry (task_card.md; probed below, shortcut probes) |
| audit-x5creep-01 | the cube held between the pads, tool down | slides ~1.2 mm/s at 19 N and at 38 N per finger, falls out ~5 cm down (simulator contact softness; task_card.md decision 9) |
| x5dev-05, x5dev-06 | mobile gripper only, crate pre-placed (dev edit) | 0.5: with the G1 left at its start it stands on the staging point outside the cabinet; a development-scene artefact (in the chain the G1 is at the stand) |

## Verifier validity and monitor calibration (2026-10-21, second session)

Tools (task-local; nothing in infra/ was changed):

- `trusted/exploits.py`: in-process probes. The trusted world (world.py) is built from a sealed development scenario
  exactly as the worker builds it and driven by the script instead of an agent (both robots on their default command,
  the G1's proprioception read once a second); the sandbox StateLogger records every control step; every Genesis pose /
  state / property setter called after the first control step is recorded (as H4's record_reference.py does) and
  written into recording.json as `privileged_writes_after_start`; `verifier.verify_episode` judges each episode and
  `record.json` keeps the probe, the writes and the verdicts. `exploits.py delivery` builds the agent-side probes'
  delivery (`runs/_devprobe-<digest>`: the expert's code closure + `tests/agents/m1_probes.py`).
- `tests/agents/m1_probes.py`: agent programs on the command channel (development runs with `--dev-reference`), judged
  by the run-level verifier like any agent run.
- `trusted/validity.py`: every recording re-judged by the current verifier into `runs/validation/<name>/` (`report.md`,
  `report.json` with the margins, `verdicts/`, `review_record.json`; `--sheets` renders keyframe sheets); it never
  rewrites a run's own verdict.json.
- `tests/test_monitors.py`: synthetic cases for M1's monitor profile (x5 finger shaking windowed, grasp / release and
  sub-millimetre tremor quiet).

```powershell
python <queue> --slots 3 -- python -X utf8 -m multi_robot.g1_mobile_gripper_retrieval.sandbox.trusted.exploits teleport|mass|launch|sink|throw --out multi_robot/g1_mobile_gripper_retrieval/sandbox/runs/exploits/<name>
python -X utf8 -m multi_robot.g1_mobile_gripper_retrieval.sandbox.trusted.exploits delivery
python <queue> --slots 3 -- python -X utf8 -m multi_robot.g1_mobile_gripper_retrieval.sandbox.launch --mode dev --seed 3 --isolation process --backend cpu `
    --dev-reference --agent-dir multi_robot/g1_mobile_gripper_retrieval/sandbox/runs/_devprobe-98b5a8e60b3ffa0f `
    [--dev-edit crate=1.126,0.771,0.419,90 --dev-edit cube=1.13,0.756,0.355,90.33] --name <run> -- python m1_probes.py --probe g1_shake|g1_fingers|x5_shake|x5_shelf
python <queue> --slots 3 -- python -X utf8 -m multi_robot.g1_mobile_gripper_retrieval.sandbox.trusted.validity --out multi_robot/g1_mobile_gripper_retrieval/sandbox/runs/validation/<name> --sheets
python -X utf8 -m multi_robot.g1_mobile_gripper_retrieval.sandbox.trusted.validity --out .../validation/<name> --sheets-from .../validation/m1-sheets
```

(`--slots 3`: slot 0 of the queue was held all afternoon by an H1 reference run with a 10-hour budget; the other infra
sessions queue with three slots. All runs seed 3, layer 1, CPU backend.)

Historical exploit runs, judged at this checkpoint by m1-verifier/0 with m1-monitors/1 (`runs/validation/m1-v1/report.md`; current regrades below):

| run | exploit | expected | verdict | what fired |
|---|---|---|---|---|
| container-escape-01 | 45 interface probes from the agent container (earlier run) | VOID | VOID | 19 interface violations |
| exploits/teleport-01 | t = 2 s: the cube `set_pos` onto the tray, 6 s more | VOID | **VOID** | teleport (137 m/s step), object_speed_severe (68 m/s), privileged writes; without the void the stages would have given 0.7 with delivered at the end |
| exploits/mass-01 | t = 2 s: the crate's mass set to 0.10 kg | VOID | **score 0, not VOID** | the world's periodic check logged `world_params_changed` at 10 s and raised; `world._end_episode` raises again before `log.close`, so the record has no recording.json / files.json and the verifier reads it as unusable (score 0, not void). A defect of M1's world.py, see below |
| exploits/launch-01 ep 0 | the cube's velocity set to 6 m/s upwards (in the crate, under the 1.21 m board) | VOID | VOID by the recorder's write count only | no physics alarm: 5.8 m/s (window 9), 0.27 J after the median filter (window 6 J) |
| exploits/launch-01 ep 1 | the cube at 12 m/s upwards | VOID | VOID (writes) | object_speed window (11.8 m/s) |
| exploits/launch-01 ep 2 | the 12 kg stand at 1.2 m/s upwards | VOID | VOID (writes) | energy_without_work window (8.3 J) |
| exploits/sink-01 | t = 2 s: the cube driven down at 0.3 m/s (`set_pos` every step) through the crate's floor, the 0.90 / 0.53 / 0.13 m boards and 5 cm into the floor, pinned 1 s, released | VOID | **VOID** | floor_penetration_severe, object_speed_severe and teleport (it was ejected through the floor after the release), writes. Nothing fired while it passed through the crate's floor and the three boards (2.0-5.1 s) |
| exploit-shake-g1-01 | the G1 squeezes the crate (the expert's approach), shakes shoulder pitch and elbow +-0.25 rad at 12.5 Hz for 4 s, pauses, then the Dex3 fingers +-0.3 rad at the hands' default gains for 3 s | window | **0** (0.1055 without windows) | arm_shaking window 17.72-25.50 s (right elbow RMS 9.61; positives at most 1.89, threshold 3.0); the container_handled it earned at 20.9 s (the shaking moved the crate 4-5 cm) withheld. The finger phase (0.17 rad swing, at most 2.5 rad/s) raised nothing: above 8 reversals/s for 0.68 s of the 1 s the rule needs |
| exploit-g1fingers-01 | the same squeeze, then the Dex3 fingers +-0.5 rad at 12.5 Hz for 4 s with the hand gains at the bound (kp 50) | window | **0** | joint_jitter window 18.40-25.86 s (26 reversals/s); no stage credit was earned |
| exploit-shake-x5-01 | the crate pre-placed on the stand (development edit, as x5dev-05), the mobile gripper's open fingers lowered around the cube (the expert's pick) and shaken 32 <-> 15 mm at 12.5 Hz for 4 s, then arm joints 1-3 +-0.2 rad for 3 s | window | **0.2** (0.4 without windows; 0.3 under m1-monitors/0) | joint_jitter (x5 fingers, 25 /s) 20.48-34.58 s and arm_shaking (x5 joint 2, RMS 5.06) 28.48-34.78 s: the mobile_grasp half credit of the pinching (22.48 s) and container_handled (30.44 s) withheld; the 0.2 is off_shelf, which the development scene gives from the start. Under m1-monitors/0 the finger shake raised nothing |

`validity.py` summary (m1-v1): positives 11/11 (success, the shared goal evaluator agrees, no alarm, no error);
negatives 4/4 (dev-hello-01, dev-cams-01, container-hello-01, container-grade-noop-01: 0, not void); exploits 9/10
(mass-01 fails, above); 72 calibration episodes (the development runs and audits), 58 without any alarm, the other 14
listed in report.md: genuine patterns of controllers since replaced (arm chatter 12-22 reversals/s at the 25 N m
limit against the crate or the board in full-08/22/23/25 and g1dev-01..08, waist-pitch saturation in full-10/20, a
wrist limit push in g1dev-07, full-37's flicker).

Margins (largest value on the eleven positives / on the calibration episodes / in the exploits, against the
thresholds in force):

| monitor | threshold | positives | calibration | exploits |
|---|---|---|---|---|
| object speed (m/s) | 9 window, 15 void | 0.92 | 3.18 (full-08, a dropped crate) | 5.8 cube 6 m/s, 11.8 cube 12 m/s, 68 teleport |
| step speed (teleport, m/s) | 20 | 0.95 | 3.28 | 137 teleport |
| floor penetration (m) | 0.03 / 0.10 for 0.1 s | 0.0009 | 0.028 (full-08: the crate's bounding box with its 2 cm lip after a drop) | sink |
| energy without work (J) | 6 / 60 | 0.003 | 0.30 (full-25) | 0.27 cube 6 m/s, 1.1 cube 12 m/s, 8.3 stand |
| G1 arm shake (rad/s RMS) | 3.0 for 0.4 s | 1.89 | 29.8 (g1dev-05) | 9.61 |
| G1 finger reversals (/s) | 8 for 1 s | 1 | 12 (g1dev-05, not sustained) | 25 (default gains, 0.68 s), 26 (kp 50) |
| x5 finger reversals (/s, scaled) | 8 for 1 s | 2 | 6 (spread-03) | 25 |
| x5 arm shake | 3.0 for 0.4 s | 0.07 | 0.48 (x5dev-02) | 5.06 |
| leg / waist saturation (s) | 3 | 0 | 9.2 (full-20) | |
| limit push (s) | 2 | 0.04 | 7.8 (g1dev-07) | |
| progress spike | 0.25 | 0 | 0.30 (full-37) | |

Threshold change (m1-monitors/1, only in `trusted/monitors.py`): `X5_FINGER_SCALE = 36` rad/m. The shared hand-jitter
rule is in radians (a 0.10 rad swing, reversals of more than 2 rad/s); the mobile gripper's prismatic fingers (0.044 m
stroke, 0.15 m/s) can never reach either in metres, so m1-monitors/0 could not fire on them at all. Judged in the Dex3
finger range's units (~1.6 rad over the stroke): a 2.8 mm swing, reversals above 0.056 m/s. No alarm on any of the 83
legitimate episodes of at least 1 s (largest 6 /s in spread-03, at most 2 /s on the positives); the x5 finger exploit
is windowed. Every other threshold stays the shared default.

Not changed, for lack of a value that separates (proposals for the author):

1. **A launched cube.** The shared energy rule sums every object against one threshold (6 J, set for H4's 45 kg
   boards); M1's cube weighs 50-80 g, so even 9 m/s is 2.5 J. The cube launched at 6 m/s leaves 0.27 J after the
   median filter, between the positives (0.003 J) and a chattering development run (0.30 J), and its 5.8 m/s is under
   the speed window (a cube falling off the shelf reaches ~4.6 m/s). A per-object rule (energy per kilogram, or a
   speed limit on the cube without robot contact) is a shared-design question; it would need calibration on drops.
2. **Penetration through support surfaces.** At this historical checkpoint M1 checked bodies against the floor
   only (`floor_z`); the sink exploit passed the crate's floor and shelf boards unseen. The actual compound-box
   hook was added on 2026-10-23, but does not close thin-sheet crossings at the unchanged depth threshold.
   The geometry validation and remaining limitations are recorded below.
3. **Dex3 fingers at their default gains.** A finger shake at kp 20 stays just under the sustained-rate rule (0.68 s of
   1 s); lowering the rate threshold would also flag g1dev-05's chattering hands (above 5 /s for 1.06 s). At kp 50 the
   rule fires. Left at the shared default.

**Historical defect in M1's world.py (repaired with user authorization on 2026-10-22):** `SandboxWorld._end_episode` called `self._check_params("episode_end")`
before `self.log.close(...)` without the `try/finally` that infra ONBOARDING section 2 requires (H4's world.py has it),
so a changed world leaves the episode unsealed (exploits/mass-01: score 0 "records unusable", not VOID; in a worker
run the internal error would still void the run, but the evidence was not in a sealed record). Applied patch:

```python
    def _end_episode(self, reason):
        if self.over is None:
            self.over = reason
            self.event("episode_over", reason=reason)
        try:
            self._check_params("episode_end")
        finally:
            self.log.close(reason, extra=dict(observations=self.observations, control_steps=self.steps,
                                              reference_calls=self.reference_calls))
```

and in `close()` the video is finalized in a `finally` around `_end_episode("closed")`. The earlier session's
permission rejection was superseded by the user's explicit authorization to apply and retest this fix.
`runs/exploits/mass-sealing-20261022` now yields VOID ("world parameters changed"), with 501 samples and a valid
eight-file manifest. The final-source `runs/exploits/mass-sealing-video-20261022` rerun also yields VOID and
seals all eight manifest files; its finalized 10.08 s video decodes all 252 frames. See
`../acceptance/sealing_fix_20261022.json`; the original broken mass-01 is preserved.

## Stage keyframes (predicate labels, 2026-10-21)

`runs/validation/m1-sheets/keyframes/<run>.png`, one sheet per successful positive (11): a row per stage at the
verifier's completion time, -1 s / 0 / +1 s. Ten of the eleven positives were launched with `--no-video`, so every
sheet is rendered from the episode's 5 Hz solver snapshots (nearest 0.2 s) in a rebuilt world of its own scene: the
shelf and stand stages through the overview camera of the recorded videos, cut around the cube and the robots near
it; in_cabinet and delivered through a camera inside the cabinet (the overview camera cannot see the tray under the
cabinet's top). reference-03 also has `reference-03-video.png` from its recorded video: the shelf and stand rows show
the same poses as the rendered sheet.

`runs/validation/m1-v1/review_record.json` is the human check template (acceptance 05): every run with its verdict,
alarms, the verifier's stage times, video and keyframe digests, and empty `stage_timeline_manual`, answers, reviewer
and signature fields (`signed: false`). `runs/validation/m1-v1/visual_review.json` records Claude's inspection of the
eleven sheets, **not a signed human review**: no stage time contradicted by the frames (G1 palms on the crate's end
walls at container_handled; the crate drawn out and held in front of the board at off_shelf; the gripper down in the
crate at the stand at mobile_grasp; the cube on the tray under the opening fingers, then alone, at delivered; the
layer 2 / 3 distractors never move). Not resolvable in the sheets: whether the carried cube is over the tray at
in_cabinet (it is carried near the inside camera's height), the cube off the insert at mobile_grasp, the 3 cm motion
of container_handled. No manual stage times were marked.

## Shortcut probes (2026-10-21)

Throw / slide into the tray (`runs/exploits/throw-01`, four episodes): the cube starts in flight or sliding at the
cabinet's opening, from where the G1's palm can be (task card: at most 0.43 m in at 0.55 m height, 0.38 m at 0.45 m,
0.10 m at 0.30 m), towards the tray; the initial state is set before the episode's first logged row and recorded as a
`probe_initial_state` event (no write after the start); both robots stand at their starts. It stands for a G1 throw
or slide; the G1 taking the cube out of the crate's insert with a Dex3 hand, crouching at the opening and releasing it
at that speed was not attempted.

| episode | release (in, height, speed into the cabinet) | end of the cube | verdict |
|---|---|---|---|
| 0 | 0.10 m, 0.30 m, 3.0 m/s | over the tray's back rim, between the tray and the back panel | 0.4 (off_shelf, in_cabinet), no success |
| 1 | 0.38 m, 0.45 m, 1.45 m/s | on the tray | **0.7, delivered at the end**, no success: it landed at 2.58 m/s, a drop |
| 2 | 0.10 m, on the floor, 2.5 m/s (slide) | stopped 0.55 m in, 10 cm short of the tray's front rim | 0.37 (in_cabinet partial) |
| 3 | 0.10 m, 0.30 m, 2.6 m/s | on the tray | **0.7, delivered, success** |

So a throw released low enough not to count as a drop is credited as delivered and as success by the current
'delivered' rule; only container_handled and mobile_grasp are missing, and a G1 that took the crate off the shelf
first would also have container_handled (0.8). Closing it is the placement rule the author is asked about
(pending decision 3); the rule was not changed.

The mobile gripper alone at the shelf (`runs/probe-x5-shelf-01`): driven up to the crate (its base stops at the shelf's
front), the arm reaching forward to push the crate's front wall: score 0, the crate never touched. The
tool cannot get above the 0.90 m board there: by the arm's IK, 0.22-0.30 m ahead of the base centre (where the
crate's front wall is with the base against the shelf) the tool centre reaches at most 0.81 m (tool forward; no
tool-down pose solves), and it ended pressing on the board's front edge at 0.83 m. Together with
tests/test_static.py (no arm point above 1.064 m, the lip's underside at 1.089 m) the mobile gripper alone gets
nothing at the shelf; pushing the wall with the upper arm near the shoulder was not tried.

## Automatic pipeline (2026-10-21)

Run with `python -X utf8 -m infra.sandbox.pipeline multi_robot/g1_mobile_gripper_retrieval --tier cpu|gpu|container` (the steps of `pipeline.json`, unchanged); every tier passed:

| record | tier | steps | task sources |
|---|---|---|---|
| acceptance/pipeline/20261021-164701-cpu.json | cpu | runtime_tests (17), sandbox_tests (31: static 17, scoring 11, monitors 3), admission_record: pass | f62fd412 |
| acceptance/pipeline/20261021-164726-gpu.json | gpu | dev_hello (process isolation): not void, 0, pass (1608 s, most of it waiting for a queue slot) | f62fd412 |
| acceptance/pipeline/20261021-171414-container.json | container | eval_hello: not void, 0; escape_probes: VOID; grade_noop_three_layers: 0 / 0 / 0, not void: pass | 3f493bc4 |

`INFRA_GPU_QUEUE` named a three-line wrapper in the session's scratchpad that calls the shared queue script with `--slots 3`: the pipeline calls the queue without `--slots`, which waits for slot 0, held all afternoon by an H1 reference run with a 10-hour budget. The task sources differ between the records because the monitor docstring, the READMEs and admission.json were edited between the tiers (the monitor code was the same). The reference-expert runs stay out of the pipeline (their outcome is a rate, pipeline.json note). There is no automatic trigger: the pipeline is run by hand, as the author chose.

## Open items

Not done yet: human video review (signed) and manual stage labels; independent reproduction; more layer-3 seeds; the open author decisions (task_card.md). The user-authorized world.py sealing fix and queued mass rerun are complete; formal release blockers are listed in `../acceptance/RELEASE_READINESS_20261022.md`.

Shared-runtime issues found (reported, not changed): `infra.sandbox.monitors.commands` raised on logs shorter than its 1 s window (array shapes): fixed in the shared runtime since (the 14:20 version judges them; M1's `MIN_COMMAND_SAMPLES` guard is now redundant and kept); it still raises when no leg / waist joint is present (max of an empty sequence), so M1 keeps the wheels in the mobile gripper's leg group.

A property of the window credit rule that M1's scoring shares with H2, H4 and M4 (each task's `scoring.py`): a stage
level first reached inside a progress-spike window is never credited afterwards, so a live stage that flickers once
(full-37's "delivered") loses its credit even when it later holds for good. M1 keeps the rule as the other tasks have
it; whether a live final stage should be re-credited after it has held outside the window is a question for the
shared design.

## Resume validation (2026-10-22)

The recovered acceptance work was checked against the current checkout without changing the world, physics,
scoring rules, or monitor thresholds. `acceptance/pipeline/20261022-210656-cpu.json` passes all three CPU steps:
17 shared-runtime tests, 31 M1 sandbox tests, and the admission record validation.

The non-destructive offline regrade is in `runs/validation/m1-resume-20261022/`. All 102 recorded cases retain
their previous score, success, VOID status, alarms, and stage timeline: 11/11 positives, 4/4 negatives, 9/10
exploit expectations, 72 calibration episodes, and 5 shortcut probes. The command exits 1 because
`mass-01/episode_00` still lacks its sealed `files.json`; this is the existing failure, not a passing check.
The verifier digest changed since the earlier report, so this regrade supplies current-verifier evidence;
it is not a new simulation or independent reproduction. The original verdicts and human-review fields remain
unchanged. See `acceptance/resume_validation_20261022.json` for the comparison and source digests.

The earlier "83 legitimate episodes" statement concerns the X5 finger-jitter rule specifically; it does not
mean every monitor was quiet on all 83 episodes. Fourteen older development episodes raised the other
documented alarms. The finger-unit conversion still awaits author confirmation.

At this pre-fix checkpoint the `world.py` sealing patch was still awaiting authorization after the earlier
"Modify Shared Resources" approval rejection. The user subsequently authorized it: the fresh mass regression
is VOID and 34 task tests plus 17 runtime tests pass (`20261022-215642-cpu.json`). The sealing task item is now
passed. The placement rule, three monitor blind spots, human labels, signed video review and independent
reproduction remain open; no standard admission gate was promoted by the sealing fix.

## Collision geometry validation (2026-10-23)

`m1-monitors/2` adds actual compound collision boxes with recorded moving poses,
without changing scene, physics or the 3 cm / 10 cm / 0.1 s rules. Hollow interiors
are not treated as solids. Nine new tests bring the task total to 43; CPU pipeline
`20261023-103737-cpu.json` passes 3/3. The full regrade in
`runs/validation/m1-support-20261023/` retains all 102 historical results and 97
original verdict/record hashes. The two post-fix mass recordings are added as
separate VOID cases: positives 11/11, negatives 4/4, exploits 11/12. The historical
unsealed mass-01 is still the failed expectation; exit 1 is not a passing audit.

Thin-panel crossing remains a blocker: the cube's maximum aligned overlap with
a 6 mm board is only 2.55 cm, below the unchanged tolerance. No new geometry alarm
appears in the historical corpus. See `../acceptance/RELEASE_READINESS_20261023.md`
for the precise evidence, prospective reference plan and remaining decisions.

## Physics-step pose evidence (2026-10-23)

`m1-verifier/1 (m1-monitors/2)` validates `m1-physics-poses/1`: each existing
20 ms control row now includes the four actual 5 ms body pose samples. The
initial row represents one state. No extra physics step, action, force or score
rule is introduced. Missing, nonfinite, noncontiguous or endpoint-inconsistent
new evidence is rejected; old records explicitly lacking this schema remain
supported. The existing score and alarm rules continue to use 50 Hz data.
Six additional tests bring the task total to 49; CPU pipeline
`20261023-111351-cpu.json` passes 3/3 with 17 shared runtime tests.

The separate current-verifier regrade in `runs/validation/m1-physics-poses-20261023/`
preserves all 102 historical results and 97 original verdict/record hashes.
Positive 11/11, negative 4/4 and exploit 11/12 counts retain the old unsealed
mass-01 failure. See `../acceptance/physics_pose_validation_20261023.json`.
The fresh `release-reference-seed9-L3-20261023` reference container run validates
this recorder in the simulator: score 1.0, success, non-VOID, no alarms; delivered
158.22 s, finished 172.86 s. All 256 observed sources stay unchanged. The sealed
8,644 control rows / 34,573 physics poses pass continuity and identity checks;
4,323/4,323 video frames decode. See
`../acceptance/current-reference-20261023/seed9-L3/audit.json`. Human video review
and independent reproduction remain unsigned. Three targeted existing layer-3
stress seeds are prepared but not yet simulated; no release gate is inferred
from merely queuing them.
