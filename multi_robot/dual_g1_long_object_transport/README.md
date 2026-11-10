# Version B — Dual G1 Cooperative Long-Object Transport

**Current task-family design (2026-10-28):** [Six configurations — 中文](../../doc/m2-task-family.md) · [English](../../doc/m2-task-family-en.md). M2-1 retains the published fixed lightweight reference; M2-2–6 cover a G1 + Stretch partner, heavier cargo, movable obstacles and a third G1. New configurations remain unvalidated; this design does not change the historical scene, scorer or admission status.

**M2 first-layer reference release (2026-10-24):** [Release / Download](https://github.com/wuxiyang1996/robo-si/releases/tag/m2-layer1-20261024) · [中文报告](../../infra/task-m2-zh.html) · [English report](../../infra/task-m2-en.html). Fixed 0.25 kg: references 09/10/11 pass 3/3 and ordinary RPC replay 09d passes 1/1, all at 1.0 / 175.28 s. Full-height walls retained. Reference materials published; human review and independent reproduction pending, admitted=false.

**Category:** Tool Discovery · **Embodiment:** Multi-Robot (two humanoids) · **Task ID:** M2 · **Priority:** P0 — priority implementation

**Status (2026-10-24): fixed first-layer evidence verified; not admitted.** The current work scope is the implemented 0.25 kg box / 1.8 m corridor. Bounded privileged references 09, 10 and 11 each complete all six stages at score 1.0 in 175.28 s; ordinary container command replay 09d also succeeds and exactly matches the recorded trajectory. The later C-drive evidence is now archived here with checksums. See the [first-layer evidence and reproduction package](acceptance/layer1-20261024/README.md). These are one fixed scene and repeated seed, not randomized coverage or sensor-feedback solvability. Human stage/video review and independent human reproduction remain pending. The separate original 9 kg task and higher layers are deferred from this continuation, without certifying or changing their physics.

Two Unitree G1 robots cooperatively carry a long box through a narrow corridor with a 90° L-shaped turn and deliver it to a designated target region.

## 地面起箱与窄 L 通道（2026-10-19）

已跑通“从地面抬起 → 稳持 → 协同通过 90° L 弯 → 到位调整站距 → 同步下蹲 → 松手并静止”。入口为 [`floor_transport.py`](floor_transport.py)，无支架，长箱 **2.25 × 0.35 × 0.24 m、0.25 kg**，通道净宽 **1.8 m**。这是轻质箱的条件验证；原始 9 kg 场景与旧支架视频保留作历史对照。

**最终证据：** [连续视频（4 倍速，约 51 秒）](media/floor-l-corridor-v1/motion.mp4) · [关键帧](media/floor-l-corridor-v1/contact-sheet.jpg) · [执行结果](media/floor-l-corridor-v1/result.json) · [独立复核](media/floor-l-corridor-v1/audit.json) · [完整参数](media/floor-l-corridor-v1/run.json)。实际仿真时长 203.24 秒，`task_success` 与 `complete_route_passed` 均为 `true`。

- 搬运期间箱底最低离地 **68.68 cm**，最大倾斜 **1.14°**；空中下放阶段最大倾斜 **1.27°**。
- 箱体累计转向 **90.13°**；所有采样中的墙体接触力和非手部顶箱接触力均为 **0 N**。
- 四手松开后，箱子完整位于目标区域并静止 **2.10 秒**，最终中心距目标约 **1.03 cm**。
- 两台最低骨盆高度约 **0.398 m**；四手真实接触承重，无物体绑定、运行中位姿改写或根节点托举外力。

协作控制包括四手夹紧力与转向力矩分配、共同箱体路径、落后等待、抬手高度补偿，以及到位后重新对齐站距。[`floor_plan.py`](floor_plan.py) 根据两台实际停稳后的脚位分别规划下蹲；切换腿部刚度时保留支撑力矩，避免突然前冲。接近地面 3 mm 时停止下降，保持手部目标连续并逐渐松手。最终判定要求手部接触力低于 0.3 N、箱速低于 0.03 m/s、倾斜低于 3°，且完整落入目标区；包含关系声明 2 mm 数值接触容差。

默认使用 Genesis CPU、椭圆摩擦锥及抗扭摩擦、手部摩擦系数 1.0、每手基准夹紧力 10 N、路径推进速度 0.06 m/s。Genesis 执行受力矩限制且开启自碰撞的物理，MuJoCo 只计算运动学。视频中南侧和东侧墙面作剖切显示，**1.5 m 高的完整墙体碰撞仍保留**。

```powershell
# 从 D:\rsi_vla\robo-si 启动；必须使用新的输出目录
..\genesis_env\Scripts\python.exe -m multi_robot.dual_g1_long_object_transport.floor_transport --out multi_robot/dual_g1_long_object_transport/media/floor-new --plan multi_robot/dual_g1_long_object_transport/media/floor-l-corridor-v1/plan.npz
# 只验证地面起箱
..\genesis_env\Scripts\python.exe -m multi_robot.dual_g1_long_object_transport.floor_transport --out multi_robot/dual_g1_long_object_transport/media/floor-lift-new --lift-only --seconds 65
# 复核已完成的一轮
..\genesis_env\Scripts\python.exe -m multi_robot.dual_g1_long_object_transport.audit_floor_transport multi_robot/dual_g1_long_object_transport/media/floor-l-corridor-v1
```

省略 `--plan` 会重新生成起箱参考；`--video-speed 1` 输出原速录像，`--no-video` 只保存数值记录。每轮保存场景、控制代码与配置快照、起箱/放置参考和 50 Hz 轨迹。19 项回归测试通过，覆盖受力解析、承重判定、目标边界容差和通道几何。这里验证的是所述配置下的连续执行，不代表更重箱体、扰动成功率或采样间全部执行器约束均已验证。

早期 [0.5 kg 地面起箱](media/floor-v3/motion.mp4) 仅验证抬升；`floor-full-cpu-*` 与 `floor-record-*` 保留调试和失败记录。`floor-record-v8/v9` 的控制器曾报告完成，但旧记录末尾不足完整 2 秒，未通过当前独立复核；最终版本补齐终止帧并延长末尾保持时间。

## 先抬起，再尝试走（2026-10-18）

新增独立试验入口 [`cooperative_trial.py`](cooperative_trial.py)：长箱保留 **2.25 × 0.35 × 0.24 m**，默认试验质量从原任务的 9 kg 降至 **1 kg**，另有 2 kg 对照。两台 G1 面对面分站箱子两端，每台用双手接触箱子的两侧。先验证支架取箱；箱底初始高度 0.73 m，**尚不代表从地面深蹲取箱成功**。原始 `task.json` 和预览视频保留。

控制顺序为站稳、同步伸手、共同夹持、缓慢抬高 12 cm、稳持 1.5 秒，然后才允许尝试横向小步搬运。行走时根据两台机器人的前后偏差调节速度，领先的一台减速。四手接触、两端载荷分配、箱体离架高度和倾斜、双机稳定性均使用实际物理状态检查；未达标就终止该轮。行走与完整 L 形通道任务必须分别验证。

**已跑出的结果：** [1 kg 试验视频](media/lift-first-1kg/motion.mp4) · [结果](media/lift-first-1kg/result.json) · [轨迹复核](media/lift-first-1kg/review.json) · [关键帧](media/lift-first-1kg/contact-sheet.jpg)

- **双机抬起、稳持通过一次：** 最大离架 9.43 cm；连续稳持 1.5 秒期间最低离架 8.93 cm，最大倾斜 0.161°。两端分别承担约 4.89 N / 4.92 N，没有非手部承重接触。
- **已尝试迈步，步行阶段未通过：** 稳持后才发出双机横向步行命令，约 2.98 秒后保护终止；最后一个记录点的箱体横向位移 13.24 cm、最低离架约 5.00 cm。没有达到本轮 15 cm 搬运目标，不能记为完整搬运成功。
- **2 kg 对照未通过稳持：** [`lift-first-v8`](media/lift-first-v8/result.json) 最大离架 8.10 cm，随后高度回落，未进入步行。更早的调试轮次保留负面证据。

每手独立调节夹紧位置，目标侧向夹紧力 12 N；把侧向力与竖直承重分开，防止抬起后因总接触力增加而误松手。共同承重要求每台承担总重的 20–80%，两台合计至少 80%，非手部接触力各低于 3 N。以上只是单次 Genesis 仿真阶段验证，尚未验证重复成功率、地面取箱、转弯或运抵终点。

使用现有 GR00T 下肢平衡/步行策略和上肢 IK。MuJoCo 只计算运动学，Genesis 执行物理；不绑定箱子、不施加托举外力、不在运行中改写物体或机器人位姿。初始化修正 MJCF 自带骨盆高度叠加问题。视频隐藏南侧墙面以便观察，墙体碰撞仍保留。

从 `D:\rsi_vla\robo-si` 运行（输出目录必须是新目录）：

```powershell
..\genesis_env\Scripts\python.exe -m multi_robot.dual_g1_long_object_transport.cooperative_trial --out multi_robot/dual_g1_long_object_transport/media/lift-first-new --walk
```

去掉 `--walk` 只验证抬起稳持。每轮保存场景配置、控制代码快照、视频、50 Hz 状态与接触力轨迹，以及明确区分抬升/步行的 `result.json`。接触接口及承重判定的回归测试：

```powershell
..\genesis_env\Scripts\python.exe -m unittest multi_robot.dual_g1_long_object_transport.test_cooperative_trial
```

## Task

- Each G1 handles one end of the box. The agent independently writes the control harness that coordinates both robots.
- At the L-shaped corner, the robots must jointly adjust the box's position and orientation, their grasp points, and their relative formation to avoid collisions between the box and the walls.
- The robots may differ in effective payload capacity, grasp stability, or mobility limits. The agent must discover these capability boundaries through interaction and distribute the load appropriately.
- When direct carrying cannot negotiate the corner, the agent must explore alternatives, such as changing grasp positions, rotating the box in stages, or temporarily setting it down and regrasping it. These are candidate strategies for benchmark design, not a prescribed solution or hints supplied in the evaluation instruction.

## Advanced Variants

Vary the box's length, mass, and center of mass, the corridor width, and each robot's payload limit. Every admitted variant must retain at least one physically executable solution with the available robot controllers. Test whether the agent discovers the changed constraints and reconstructs a feasible cooperative control program.

Physical feasibility remains to be validated. Geometric clearance alone is insufficient: validation must include both robots' footprints, reach, grasp retention, load sharing, balance, and the transitions needed for any placement and regrasping strategy.

## Evaluation Contract

The goal is to deliver the box into the designated target region while respecting the declared collision, grasp, and robot stability constraints. Define numerical tolerances and the required final dwell time during implementation, before evaluation. Permit alternative valid strategies and temporary placements; do not require a particular grasp sequence or formation.

The agent controls both robots through public interfaces and receives the observations allowed by the evaluation setting. It constructs the synchronization, load-allocation, failure-detection, and recovery logic. Record both robots' actions, waits, failures, and interaction costs. Validate success from continuous physical execution without state edits or contact bypasses.

## Implementation Priorities

- [ ] Build the two-G1 scene, long box, L-shaped corridor, and target region.
- [ ] Validate cooperative lifting, carrying, turning, placement, and regrasping with the chosen controllers.
- [ ] Provide observations and a control interface for both robots, and implement success and constraint checks.
- [ ] Validate at least one executable solution per admitted configuration; check whether cooperation is necessary or only reduces cost.
- [ ] Add capability asymmetry and advanced variants, then evaluate agent-written harnesses.

## Core Capabilities Evaluated

Multi-Robot Coordination · Long-Horizon Planning · Physical Reasoning · Harness Construction · Embodied Self-Modeling

See the [Tool Discovery category](../../README.md#tool-discovery) and the benchmark proposal in [English](../../doc/self-modeling-benchmark-v4-en.html#team-m2) or [中文](../../doc/self-modeling-benchmark-v4-zh.html#team-m2).

## 开发评测基础设施

地面轻箱任务的隔离执行、专家录制和独立评分入口见 [sandbox/README.md](sandbox/README.md)，
评分约定和正式验收缺项见 [TASK_CARD.md](TASK_CARD.md)。旧录像复核与新环境侧记录分开标记。
