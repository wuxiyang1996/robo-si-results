# Version A — Humanoid and Mobile-Gripper Collaborative Retrieval (M1)

**第一层资料发布（2026-10-24）：** 13 条完整成功 / 8 个物理种子，严格重复 3/3，全部 1.0；CPU 特权反馈参考。[中英文任务页](../../infra/task-m1-zh.html)、[发布包](https://github.com/wuxiyang1996/robo-si/releases/tag/m1-layer1-20261024)与[人工审阅工作台](acceptance/layer1-20261024/index.html)已发布。用户本人负责录像与阶段审阅，独立第二人待安排；覆盖和监视／捷径验收仍待完成，`admitted=false`。完整包提供冻结源码与每次运行的原始源码副本；下方正文及本目录开发源码是历史版本，不代表最新冻结候选。R9 和可选高层延期。

**Category:** Multi-robot cooperation · **Embodiment:** Unitree G1 with Dex3-1 hands + a mobile gripper (ARX X5 arm on a
differential-drive base) · **Task ID:** M1 · **Scene version:** `M1-v0.3` (scene.py)

**Status (2026-10-23): not admitted.** The author confirmed the current v0.3 scene,
the X5 finger conversion and supported placement, and authorized both new cube
monitor rules. `m1-scoring/2-supported-release` requires cabinet support before
final robot release. `m1-monitors/3.1-numeric-boundary` adds residual cube-energy and sampled
center-in-material windows. All 11 historical final positives still pass;
the old low-throw success is rejected and its original verdict is preserved.
Fresh copied-source reference validation is underway. Range/subtask coverage,
release-scope requirements, short default-gain finger diagnostics, human review
and second-person reproduction remain unfinished. See
[current policy evidence](acceptance/APPROVED_POLICY_20261023.md) and
[dated validation history](sandbox/README.md).

## Task

A 4.5 cm yellow cube lies in a plastic crate on the 0.90 m level of a steel shelf. Put it onto the tray at the back of
a low cabinet and leave it there, resting on the tray and released by both robots.
The cabinet must already support the cube before final release. One agent controls both robots
through the robots' own sensors and joint commands only.

Neither robot can do it alone (the cooperation the proposal asks for is built into the geometry, not into a rule):

| | G1 | mobile gripper |
|---|---|---|
| reach the cube in the crate (rim 1.10 m) | yes (grasps shelves up to ~1.15 m from the floor) | no: its grasp point reaches at most ~1.03 m, and only within ~0.1 m of its shoulder axis; the shelf's side and back panels stop it from sliding the crate off the board |
| reach the tray (0.62 m inside height, centre 0.80 m deep) | no: cannot enter; crouched, its hand reaches ~0.35-0.4 m past the opening | yes: drives in (0.43 m folded, ~0.55 m holding the cube) |

Intended route (not given to the agent, not rewarded as such): the G1 takes the crate off the shelf and sets it on the
hand-over stand (a 0.28-0.32 m pedestal table), the mobile gripper picks the cube out of the crate and drives it into
the cabinet onto the tray. Other routes are allowed (the G1 takes the cube out and hands it over, ...).

## Scene (scene.py)

Room 5.0 x 3.75 m with walls; the steel shelf (Poly Haven `steel_frame_shelves_01`, colliders from the H1 asset) against
the north wall with sheet side and back panels; the crate (Poly Haven `plastic_crate_01` visual; 0.35 x 0.30 x 0.20 m,
0.6-0.8 kg, 2 cm outward lip) on its 0.90 m level; the cube in the crate; the pedestal stand; the low cabinet against
the west wall, opening east, with the tray (0.30 m, 2.2 cm rim) 0.80 m inside. Randomised per (seed, episode): robot
start poses, crate position and mass, cube offset / yaw / mass, stand position and height, cabinet position. Layers:
1 necessary objects; 2 + a second crate with a blue cube on the 0.55 m level and a carton on the floor; 3 + a bench
that narrows the approach to the cabinet.

## Part changes against the sources (all properties of objects or robots, no simulator settings)

- Mobile gripper ([x5_model.py](x5_model.py)): ARX's own X5 joint ranges, velocity and torque limits (arx5-sdk
  `config.h`; M3 kept placeholders: +-10 rad, 100 N m); a 0.40 x 0.30 m, 4.5 kg base with the drive wheels at the centre
  and swivel casters front and rear (M3's 1.2 kg base tipped over when the 3.4 kg arm swung up); per-joint rotor
  inertia (Genesis' default 0.1 kg m^2 would lock the casters); finger force 40 N (assumption: the gripper linkage
  ratio is not published).
- Shelf side and back panels; cabinet inside height 0.62 m (0.50 m first proposed: the arm's elbow stands 0.53-0.61 m
  when it holds the cube low with the gripper down); stand height 0.28-0.32 m (the gripper points straight down only
  up to ~0.47 m).

## Scoring (sandbox/trusted/scoring.py)

| stage | mode | weight | value |
|---|---|---|---|
| container_handled | once | 0.10 | robot hand / finger contact with the crate or the cube that moved one of them |
| off_shelf | once | 0.20 | the cube out of the shelf, not falling, for 1 s (partial: how far out) |
| mobile_grasp | once | 0.20 | the mobile gripper alone holds the cube for 1 s (partial: both fingers pressing) |
| in_cabinet | once | 0.20 | the cube inside the cabinet (0.5-1 by depth), 1 over the tray |
| delivered | live | 0.30 | the cube rests on the tray, supported before final release and at rest, released, slow, 2 s dwell |

Success: delivered at the end of the episode, no fall / tip-over, no object dropped (free fall above ~0.3 m).

## Files

`scene.py` sealed scene generator · `env.py` the Genesis world (both robots, compound objects) · `x5_model.py` the mobile
gripper model (one source, simulator and bundle renderings) · `instruction.md` · `task.toml` · `sandbox/` (see its
README) · `solution/` the reference expert (an SDK program over the reference channel).
