# Historical single-G1 H3 — superseded by the multi-robot task

**Current H3 is [Dual G1 self-closing door delivery](../../multi_robot/dual_g1_self_closing_door/README.md): two robots, `heavy_prop` and `no_prop`, both with a 180-second limit. [Published reference](https://github.com/wuxiyang1996/robo-si/releases/tag/h3-cooperative-20261024).** This directory is retained for historical evidence and shared controller dependencies. The following single-G1 descriptions, sandbox results and 120-second configurations are archival; they are not the current task specification and are not counted toward the dual-G1 results.

---

# Version D — G1 Self-Closing Door Traversal

**Category:** Tool Discovery · **Embodiment:** Humanoid · **Task ID:** H3 · **Priority:** P0 — priority implementation

**Status:** Genesis and Isaac Lab environments implemented (scene revision 2026-10-20). Two complete expert delivery trajectories recorded in Genesis (`solution/runs/expert-v23` with the current scene, task success at 92.2 s of the 120 s budget; `expert-v20` with the table 0.15 m nearer); repeatability statistics and the Isaac expert run are pending. See [solution/README.md](solution/README.md). An isolated evaluation sandbox following robo-si/infra is in [sandbox/](sandbox/README.md). Under the real G1 torque limits the sandbox applies, the reworked expert (`run_expert.py --profile hardware`: palm-heel push with soft arms, masked exits and carry) completed the task in 3 of 3 final runs inside the reference container (verifier score 1.0, success) and 4 of 8 runs overall. Since 2026-10-21 the delivery table is a four-legged Poly Haven table and the pedestal and table are 0.70 m high, so the box is picked and placed standing; with that scene the hardware-profile expert succeeded in 3 of 3 in-process runs (93.7-103.0 s) and in the reference container (`sandbox/runs/reference-stand70-1`, verifier 1.0), see solution/README.md section 8.

## 专家参考解（2026-10-20，场景修订后）

作者同意修改环境后，场景改为：0.4 kg 小箱放在 A 房间的台子上，目标区内有同高的四腿木桌（2026-10-21 起两者都是 0.70 m，站着取放，见下方修订）；原 8 kg 重物换成 12 kg 高储物柜（0.70 × 0.40 × 0.90 m、摩擦 0.18）；地面摩擦 0.18；门宽 1.5 m，闭合阻尼 6 N·m·s；手掌硅胶垫（摩擦 2.0）；超时 120 s。专家解 `solution/run_expert.py` 复用 H4 的台面取箱、Agile 持箱行走和 H1 的接触 QP 站姿：**推柜子穿门洞、柜子前棱把门顶开到 1.23 rad 并卡住（门闭合力约 4 N，柜子地面摩擦 21 N）→ 走回台子侧夹取箱 → 持箱沿 0.80 m 净空穿门 → 站姿下把箱放到桌面**。[`runs/expert-v23`](solution/runs/expert-v23/result.json) 一次完整运行在 92.2 s 由环境核心判定成功（[视频](solution/runs/expert-v23/motion.mp4)），42 项记录审计通过；桌子后移前的 [`runs/expert-v20`](solution/runs/expert-v20/result.json) 也完成过一次（93.0 s）。这是两次成功记录，不是重复率统计：推柜后的收手停步段约一半概率把步态带跑，取箱和放箱阶段使用特权的腿部力矩直驱（`--leg-torque 1`，与 H4 验证取箱相同，v23 为 1361/4610 步），Isaac 后端只验证了环境冒烟。代码、实际动作/状态记录、失败清单和复现命令见 [参考解记录](solution/README.md)。

## 隔离沙箱（2026-10-20）

按 [infra](../../infra/README.md) 规范建了 [`sandbox/`](sandbox/README.md)：可信 Genesis worker + 加固的 Docker agent 容器 + 只读可信记录的
verifier，结构同 H1/H4/H6。专家解作为程序跑在参考容器里，动作全走 agent 的指令通道，真值只从启动器密封开启的特权通道读取。
单元测试 43 项、42 项逃逸探针、noop/hello/评分模式都通过。沙箱按 infra 用真实 G1 力矩上限（robot.py 的手臂、手腕、手指是
300 N·m，满限一步能把机器人弹到 21 m 高）；原专家依赖超限力矩，在真实上限下撑门失败。重做推柜（掌根推、软手臂）以及
后续的取箱、持箱停步、放箱之后，`--profile hardware` 在参考容器里最后 3 次全部完成任务（verifier 1.0、成功、
`proof_of_solvability: true`），最终配置共 8 次成功 4 次。21 次容器参考运行里 verifier 没有误给分或漏判失败。
详见 [sandbox/README.md](sandbox/README.md) 第 8–9 节和 [solution/README.md](solution/README.md) 第 6–7 节。

## 双模拟器环境（2026-10-18）

已实现 **Genesis + Isaac Lab / PhysX** 两个后端，共用 `task_spec.py` 的场景参数、动作接口和轨迹判定。机器人模型复用 H1 的 G1 MJCF 及由它转换的 USD；不依赖柜子资产。缺少机器人资产时参照 H1 的安装及转换说明。

从 `D:\rsi_vla\robo-si` 运行：

```powershell
# Genesis：两个并行场景、3 秒物理运行、验证自闭和重置
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_self_closing_door/scripts/smoke.py --sim genesis --num-envs 2 --steps 150 --door-angle 1.2 --image humanoid/g1_self_closing_door/media/genesis.png

# Isaac Lab：使用已经安装的 isaaclab 环境
$env:OMNI_KIT_ACCEPT_EULA = 'YES'
C:\Users\wuxiy\anaconda3\envs\isaaclab\python.exe humanoid/g1_self_closing_door/scripts/smoke.py --sim isaac --num-envs 2 --steps 150 --door-angle 1.2 --image humanoid/g1_self_closing_door/media/isaac.png
```

添加 `--viewer` 打开交互窗口；省略 `--image` 进行纯物理检查。
`--door-angle 1.2` 是诊断用初始条件；实际任务默认从关闭门开始。
Windows 启动脚本显式关闭 Vulkan，使用本机可运行的 D3D12 路径。
`--output result.json` 保存检查结果。Genesis 首次编译可能需要数分钟。
两个模拟器使用不同 Python 环境，可在两个终端分别运行。

### 场景与接口

默认优先使用现成素材，两个后端共用 `visual_assets/` 中的 OBJ 和纹理：

| 部件 | 复用来源 | 适配方式 |
|---|---|---|
| G1 | 仓库已有 Unitree G1 MJCF / USD | 继续共用原机器人资产 |
| 门板、把手和木纹 | [robosuite door.xml](https://github.com/ARISE-Initiative/robosuite/blob/5ce6643f3092639d08f7b0f90ed1c6a84f50552c/robosuite/models/assets/objects/door.xml) | 将原 MJCF 的门板及把手几何转换为带纹理网格，并适配本任务尺寸；保留 MIT 许可文件及原始来源注释 |
| 搬运箱 | [Poly Haven Wooden Crate 02](https://polyhaven.com/a/wooden_crate_02)（CC0） | 复用现成模型和 1K 纹理，缩放至任务箱体尺寸 |
| 送货桌 | [Poly Haven Wooden Table 02](https://polyhaven.com/a/wooden_table_02)（CC0） | 复用现成模型和 1K 纹理，缩放到 0.70 × 0.60 × 0.70 m（原模型高 0.80 m）；碰撞体按模型取桌面和四条腿（`TaskConfig.table_colliders`） |
| 房间、台子、木楔、储物柜 | 参数化几何 | 保留任务所需的尺寸和接触形状；没有用不匹配的装饰模型替换物理工具 |

上述素材只替换显示外观，原有门铰链、门板碰撞体、箱体碰撞体、质量和摩擦参数仍用于物理仿真；送货桌例外，它的碰撞体按模型做成桌面加四条腿（见下方场景修订）。**把手目前仅为外观，没有独立把手碰撞或门锁机构**；控制器应推门板，不能假定可以抓住把手。箱子的细节和绳把手同样不属于可独立抓取部件。`TaskConfig(use_asset_visuals=False)` 可切回基础几何外观作对照。

素材来源、固定的 robosuite 提交及下载 SHA-256 记录在 `visual_assets/sources.json`；现成运行素材已保存在本任务目录，启动时不联网。重新下载和转换：

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_self_closing_door/scripts/prepare_visual_assets.py
```

- 两个房间总范围为 x=0–6 m、y=−2–2 m，分隔墙位于 x=3 m。
- 门板宽 1.5 m（原 1.3 m）、高 2.1 m、厚 0.045 m、质量 12 kg；门框留出装配间隙。门角范围 0–1.75 rad，向 B 房间开启，门底离地 12 mm。
- 每个物理步施加自闭力矩 `tau = -3 * angle - 6 * angular_velocity`（阻尼原为 1.2：欠阻尼的门板被推动后会甩到前面再弹回撞击门挡；现在从 1.3 rad 自闭约 4 s），通过铰链和真实碰撞响应；没有门锁、冻结或吸附逻辑。
- **2026-10-20 场景修订（作者同意修改环境后）**：搬运箱改为 0.20 × 0.18 × 0.16 m、0.4 kg 的小箱，放在 A 房间一个 0.45 × 0.45 × 0.50 m 的固定台子上（箱子中心 `(1.45, 0.80, 0.583)`，箱子悬出台子近边 6 cm，便于侧夹时手腕让开台面）；目标区内放一张 0.70 × 0.60 × 0.50 m 的固定桌子（中心 `(5.20, 0.25)`，近边 x=4.85），箱子送到桌面上即可。原 8 kg 重物改为 0.70 × 0.40 × 0.90 m、12 kg 的高储物柜（`crate`，摩擦 0.18），初始位于 `(1.75, −0.33)`，与门铰链一侧对齐；地面摩擦由 0.6 改为 0.18（光滑地板）。两个模拟器都按接触对的较大摩擦系数计算，所以机器人鞋底（1.0）、箱子（0.7）、木楔（0.9）和门板（0.6）不受地面系数影响，只有柜子和轻物体在地面系数上滑动。机器人手掌与手腕链接加硅胶垫（摩擦 2.0，H1/H4 中已允许）。木楔（0.7 kg）和轻物体（0.12 kg）保留为自由刚体候选工具，轻物体仅是候选失败工具。
- **2026-10-20 第二次修订（作者同意）：送货桌改成四条腿的木桌**。占地（0.70 × 0.60 m）、位置和摩擦（0.7）不变，只是不再是实心块：桌面厚为桌高的 8.4 %（0.70 m 时 5.9 cm），四条腿 5.9 × 8.1 cm（距长边 3.4 cm、短边 4.7 cm），桌面下是空的（机器人面对的近侧两腿之间净宽 0.34 m），与 Poly Haven Wooden Table 02 模型一致。原因：实心块让膝盖无处可放，按实机力矩上限运行时机器人只能停在离桌边 0.42 m 处，放箱时双手要伸到身前 0.56 m，箱子放不到桌面（停在桌面上方 15–25 cm 后松手掉下），持箱停步后的前冲则让膝盖撞上桌面侧面（`solution/runs/hw-chain-v20/v21/v28`，接触力 956–1211 N，超过 800 N 限值记失败）。两个后端都是一个固定刚体：Genesis 为单连杆 URDF（5 个盒子碰撞体加模型外观），Isaac 为运动学刚体 USD（同样 5 个碰撞体，箱子接触传感器按 `/Table` 过滤）。验证：箱子放在桌面上，两个后端的桌面支撑力都等于箱重 3.924 N，两个后端的 smoke 都通过（`media/*-smoke.json`）。评分和成功条件不变。`TaskConfig(table_style="block")` 可换回实心块对照。
- **2026-10-21 第三次修订（作者：“搬箱子用最简单的就行”）：台子和桌子都升到 0.70 m**（`TaskConfig.stand_height`，原 0.50 m），箱子初始中心 `(1.45, 0.80, 0.783)`，其余不变。箱子中心原在 0.58 m，取箱和放箱都要下蹲（骨盆 0.60 m、前倾 0.4 rad），按实机力矩上限运行时取箱约一半摔倒：肩部只有 25 N·m，手臂伸出时带着躯干晃，腰俯仰伺服（kp 5000、kd 5，约 5 % 临界阻尼，50 N·m）被激起振荡，最高 12 rad/s，把机器人甩倒。0.70 m 时箱子在站立手高附近，取箱和放箱都站着做，持箱时箱底仍高出桌面约 8 cm。试过 0.65 m：站着够不到箱子两侧，夹不出力（`solution/runs/dev-stand65-place-1/2`）。验证：Genesis 和 Isaac 中箱子放在 0.70 m 桌面上都静止于 z 0.78，桌面支撑力 3.924 N，等于箱重；两个后端的 smoke 都通过（`media/genesis.png`、`media/isaac.png` 已按新高度重新生成）。
- 改动原因见 [solution/README.md](solution/README.md)：原 2 kg 地面箱在 Genesis 默认接触模型下夹不稳（数值蠕滑，最高只抬起 6.6 cm），原 8 kg、摩擦 0.9 的重物（推动需 70 N）只能用脚蹭，木楔要靠脚精确踢到门弧线下方；改成台面小箱和可手推的柜子后，H4 已验证的台面取箱、Agile 持箱行走和推物技能可以直接复用；门加宽到 1.5 m 并加大闭合阻尼是为了给柜子留出侧向漂移余量并避免门板回弹撞偏柜子。
- 目标区中心 `(5, 0)`、大小 1.1 × 1.1 m。默认超时 120 s（原 90 s），终点连续稳定放置 2 s。
- 控制 50 Hz，物理 200 Hz。43 维动作按 `robot.JOINT_NAMES` 排序，关节目标为 `default_q + 0.25 * action`，限制在关节范围内。电机参数沿用仓库的 G1 开发配置，尚非实机能力校准值。
- 199 维观测：关节位置/速度 86、上次动作 43、机器人根状态 13、箱子/木楔/柜子/轻物体各 13、门角/角速度 2、起箱/穿门/终点保持 3。每个刚体状态为位置、wxyz 四元数、线速度、角速度；位置采用各环境局部世界坐标。目前提供完整状态观测，未实现隐藏物性评测。

```python
import torch
from humanoid.g1_self_closing_door.genesis_env import G1SelfClosingDoorGenesis

env = G1SelfClosingDoorGenesis(num_envs=2, auto_reset=True)
obs, reward, done, extras = env.step(torch.zeros(2, 43, device=env.device))
env.reset([0])  # 只重置第一个场景
env.close()
```

Isaac 对应类为 `G1SelfClosingDoorIsaac`，必须在 `AppLauncher` 启动后导入；其 `reset/step/state/get_observations` 接口与 Genesis 相同。
`extras` 包含 `info`、`time_outs`、`final_observation` 和 `final_observation_mask`；默认自动重置，`auto_reset=False` 时调用方应在终止后停止控制或重置。

### 判定及验证边界

每个物理步检查“起箱”：箱底离地 6 cm、双手接触各超过 2 N，且地面或固定台面给箱子的竖直支撑力低于箱重的 25%（在台子上夹住但没抬起不算起箱）；穿过 x=3 的时刻要求箱子仍满足该条件，且箱体完整位于门洞宽高范围内。终点要求整个箱体位于目标区、正立、线速度低于 0.10 m/s、角速度低于 0.20 rad/s、地面或桌面支撑力超过半箱重、双手接触各低于 1 N，机器人已进入 B 房间，持续 2 s。摔倒、机器人越界及超限接触（含对台子、桌子的碰撞）记失败。`genesis_env.leg_tau_override` 是默认关闭的特权腿部力矩入口，仅供专家参考解在接触 QP 站姿阶段使用并计数。

当前碰撞检查为开发期近似：Genesis 检查机器人对门和墙的合接触力，Isaac 检查非足部净接触力，默认阈值 800 N。两者的接触聚合方式尚未统一，不能据此宣称严格的跨模拟器评分等价，也未实现材料损伤模型。原始 `state()` 返回手部接触、地板支撑、门及工具状态，可供后续控制器记录交互轨迹。

已保存 `media/genesis-smoke.json`、`media/isaac-smoke.json` 以及场景图。两个后端各运行 2 个场景、150 个控制步（600 个物理步），检查有限观测、自闭、地面接触、无假成功及重置。零动作保持默认关节姿态不能维持平衡，约 0.975 s 后记录失败；smoke 为检查门机构继续运行至 3 s，不属于有效任务轨迹。

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe -m unittest discover -s tests -p test_self_closing_door.py -v
```

10 项合成判定测试覆盖无搬运假成功、台上夹住不算起箱、放手及保持时间、摔倒、支撑力、完整目标包含、局部重置和场景布局。这些测试不证明物理可解。**尚未验证机器人开门、工具有效放置、双手搬箱穿门及失败恢复的完整连续执行**，因此不将任何参数变体标记为已验证可解。工具选择与使用不作为强制评分条件，以保留合法替代策略。

A single Unitree G1 must carry a box from room A to room B through a door with a self-closing mechanism. The G1 can open the door, but cannot keep holding it open while carrying the box with both hands. Wooden wedges, heavy objects, and other interactive objects are available. The agent must independently discover how to keep the door open.

## Task

- Through interaction, the agent discovers the door's closing mechanism, diagnoses why direct transport fails, and explores which objects can serve as temporary holding tools.
- The agent may use a wooden wedge, a heavy object, or another object to prevent closure, but must verify placement, friction, and the resulting holding effect.
- The agent independently writes a long-horizon control harness to coordinate opening the door, placing a tool, checking the door state, regrasping the box, traversing the doorway, and placing the box at its destination.
- If the door cannot remain stably open, the agent uses execution feedback to adjust the tool, its placement, or the passage sequence rather than repeatedly executing a failed strategy.

These are candidate strategies for benchmark design, not a prescribed solution. Evaluation instructions state the delivery goal and public constraints without identifying a correct tool or placement. Valid alternative strategies receive credit.

## Advanced Variants

Vary door closing force, friction coefficients, doorway width, box dimensions, and available tools' physical properties. Include ineffective wedges or heavy objects that slide easily. Every admitted variant must retain at least one physically executable solution with the available robot controller and scene resources. Test whether the agent recognizes tool failure and reconstructs its control program.

Physical feasibility remains to be validated. Confirm that the robot can open the door and carry the box, that two-handed carrying prevents continuous hand support of the door, and that at least one tool placement leaves sufficient stable clearance for both robot and box. Validate frictional holding, the closing mechanism, tool slippage, and the complete release–regrasp–traversal sequence. Do not substitute a scripted door lock for physical tool interaction.

## Evaluation Contract

The robot delivers the box from room A into the designated region in room B and places it stably, while satisfying declared collision, stability, and damage constraints. Define numerical tolerances and the final dwell time before evaluation. The door only needs to stay sufficiently open during passage; permanent door fixation or tool cleanup is not required unless explicitly included in the instance goal.

Verify success through continuous physical execution. Record opening attempts, tool choices and placements, door-state checks, regrasping, traversal attempts, failures, and recovery costs. Do not allow state edits, door freezing, or contact bypasses to replace tool use.

Use the observations allowed by the evaluation setting to assess whether the agent distinguishes ineffective tool geometry, insufficient friction, excessive closing force, and inadequate passage clearance. A plausible explanation without a successful physical adjustment does not establish recovery.

## Implementation Priorities

- [x] Build rooms A and B, the self-closing door, transport box, candidate tools, and destination region in Genesis and Isaac Lab.
- [x] Validate door opening, two-handed box transport, and the direct-transport limitation (Genesis, revised scene; one recorded trajectory).
- [x] Validate at least one physically effective tool placement and a complete delivery trajectory (`solution/runs/expert-v23` and `expert-v20`; repeatability pending).
- [x] Provide robot observations and control interfaces, and implement initial success, contact, and stability checks (physical calibration and contact parity pending).
- [ ] Add ineffective tools and physical variants with verified feasible solutions, then evaluate tool discovery and harness recovery.

## Core Capabilities Evaluated

Autonomous Tool Discovery · Physical Affordance Reasoning · Environmental Modification · Harness Construction · Long-Horizon Planning · Failure Recovery

See the [Tool Discovery category](../../README.md#tool-discovery) and the benchmark proposal in [English](../../doc/self-modeling-benchmark-v4-en.html#humanoid-h3) or [中文](../../doc/self-modeling-benchmark-v4-zh.html#humanoid-h3).

---

# Version D — G1 Self-Closing Door Traversal

> **Current work (2026-10-24):** Current A has verified full opening in two V30 physical repeats: 1.229908 rad at 33.12 s and 1.231071 rad at 32.86 s, each with 0.5 s loaded-contact dwell and sealed-record integrity checks. Initial opposed grasp and small-angle milestones remain verified. V36 also acquired native left leaf-edge contact for 0.5 s in one physical run (right bar still held). Independent left support, empty passage, prop transfer and full delivery have not succeeded. [Live evidence inventory](acceptance/release-progress-20261024/progress.json).

> **Release status: hold for technical completion.** V58 stopped at 47.62 s during thumb release, before its base-motion compensation activated. Reported left opening moment fell below the load gate while the door accelerated open and other door contacts were zero. V59 retains V58 motion commands and gates, and adds read-only telemetry at every 200 Hz physics step: native door contact force/moment by robot link and door collider, hinge angle/rate before and after, closer torque and native constraint torque. This diagnoses whether 50 Hz last-substep contact sampling represents the actual load. 124 focused regressions pass after updating the mocked worker fixture for the new observer. No scorer, physics, effort limits, geometry or task budget changes. Independent support, passage and delivery remain unverified. Original failures are retained. Human review and independent reproduction remain unsigned.

**Category:** Tool Discovery · **Embodiment:** Humanoid · **Task ID:** H3 · **Priority:** P0 — priority implementation

**Historical status (earlier scenes):** Genesis and Isaac Lab environments implemented (scene revision 2026-10-20). Two complete expert delivery trajectories recorded in Genesis (`solution/runs/expert-v23` with its recorded historical scene, task success at 92.2 s of the 120 s budget; `expert-v20` with the table 0.15 m nearer); repeatability statistics and the Isaac expert run are pending. See [solution/README.md](solution/README.md). An isolated evaluation sandbox following robo-si/infra is in [sandbox/](sandbox/README.md). Under the real G1 torque limits the sandbox applies, the reworked expert (`run_expert.py --profile hardware`: palm-heel push with soft arms, masked exits and carry) completed the task in 3 of 3 final runs inside the reference container (verifier score 1.0, success) and 4 of 8 runs overall. Since 2026-10-21 the delivery table is a four-legged Poly Haven table and the pedestal and table are 0.70 m high, so the box is picked and placed standing; with that scene the hardware-profile expert succeeded in 3 of 3 in-process runs (93.7-103.0 s) and in the reference container (`sandbox/runs/reference-stand70-1`, verifier 1.0), see solution/README.md section 8.

## 专家参考解（2026-10-20，场景修订后）

作者同意修改环境后，场景改为：0.4 kg 小箱放在 A 房间的台子上，目标区内有同高的四腿木桌（2026-10-21 起两者都是 0.70 m，站着取放，见下方修订）；原 8 kg 重物换成 12 kg 高储物柜（0.70 × 0.40 × 0.90 m、摩擦 0.18）；地面摩擦 0.18；门宽 1.5 m，闭合阻尼 6 N·m·s；手掌硅胶垫（摩擦 2.0）；超时 120 s。专家解 `solution/run_expert.py` 复用 H4 的台面取箱、Agile 持箱行走和 H1 的接触 QP 站姿：**推柜子穿门洞、柜子前棱把门顶开到 1.23 rad 并卡住（门闭合力约 4 N，柜子地面摩擦 21 N）→ 走回台子侧夹取箱 → 持箱沿 0.80 m 净空穿门 → 站姿下把箱放到桌面**。[`runs/expert-v23`](solution/runs/expert-v23/result.json) 一次完整运行在 92.2 s 由环境核心判定成功（[视频](solution/runs/expert-v23/motion.mp4)），42 项记录审计通过；桌子后移前的 [`runs/expert-v20`](solution/runs/expert-v20/result.json) 也完成过一次（93.0 s）。这是两次成功记录，不是重复率统计：推柜后的收手停步段约一半概率把步态带跑，取箱和放箱阶段使用特权的腿部力矩直驱（`--leg-torque 1`，与 H4 验证取箱相同，v23 为 1361/4610 步），Isaac 后端只验证了环境冒烟。代码、实际动作/状态记录、失败清单和复现命令见 [参考解记录](solution/README.md)。

## 隔离沙箱（2026-10-20）

按 [infra](../../infra/README.md) 规范建了 [`sandbox/`](sandbox/README.md)：可信 Genesis worker + 加固的 Docker agent 容器 + 只读可信记录的
verifier，结构同 H1/H4/H6。专家解作为程序跑在参考容器里，动作全走 agent 的指令通道，真值只从启动器密封开启的特权通道读取。
单元测试 43 项、42 项逃逸探针、noop/hello/评分模式都通过。沙箱按 infra 用真实 G1 力矩上限（robot.py 的手臂、手腕、手指是
300 N·m，满限一步能把机器人弹到 21 m 高）；原专家依赖超限力矩，在真实上限下撑门失败。重做推柜（掌根推、软手臂）以及
后续的取箱、持箱停步、放箱之后，`--profile hardware` 在参考容器里最后 3 次全部完成任务（verifier 1.0、成功、
`proof_of_solvability: true`），最终配置共 8 次成功 4 次。21 次容器参考运行里 verifier 没有误给分或漏判失败。
详见 [sandbox/README.md](sandbox/README.md) 第 8–9 节和 [solution/README.md](solution/README.md) 第 6–7 节。

## 双模拟器环境（2026-10-18）

已实现 **Genesis + Isaac Lab / PhysX** 两个后端，共用 `task_spec.py` 的场景参数、动作接口和轨迹判定。机器人模型复用 H1 的 G1 MJCF 及由它转换的 USD；不依赖柜子资产。缺少机器人资产时参照 H1 的安装及转换说明。

从 `D:\rsi_vla\robo-si` 运行：

```powershell
# Genesis：两个并行场景、3 秒物理运行、验证自闭和重置
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_self_closing_door/scripts/smoke.py --sim genesis --num-envs 2 --steps 150 --door-angle 1.2 --image humanoid/g1_self_closing_door/media/genesis.png

# Isaac Lab：使用已经安装的 isaaclab 环境
$env:OMNI_KIT_ACCEPT_EULA = 'YES'
C:\Users\wuxiy\anaconda3\envs\isaaclab\python.exe humanoid/g1_self_closing_door/scripts/smoke.py --sim isaac --num-envs 2 --steps 150 --door-angle 1.2 --image humanoid/g1_self_closing_door/media/isaac.png
```

添加 `--viewer` 打开交互窗口；省略 `--image` 进行纯物理检查。
`--door-angle 1.2` 是诊断用初始条件；实际任务默认从关闭门开始。
Windows 启动脚本显式关闭 Vulkan，使用本机可运行的 D3D12 路径。
`--output result.json` 保存检查结果。Genesis 首次编译可能需要数分钟。
两个模拟器使用不同 Python 环境，可在两个终端分别运行。

### 场景与接口

默认优先使用现成素材，两个后端共用 `visual_assets/` 中的 OBJ 和纹理：

| 部件 | 复用来源 | 适配方式 |
|---|---|---|
| G1 | 仓库已有 Unitree G1 MJCF / USD | 继续共用原机器人资产 |
| 门板、把手和木纹 | [robosuite door.xml](https://github.com/ARISE-Initiative/robosuite/blob/5ce6643f3092639d08f7b0f90ed1c6a84f50552c/robosuite/models/assets/objects/door.xml) | 将原 MJCF 的门板及把手几何转换为带纹理网格，并适配本任务尺寸；保留 MIT 许可文件及原始来源注释 |
| 搬运箱 | [Poly Haven Wooden Crate 02](https://polyhaven.com/a/wooden_crate_02)（CC0） | 复用现成模型和 1K 纹理，缩放至任务箱体尺寸 |
| 送货桌 | [Poly Haven Wooden Table 02](https://polyhaven.com/a/wooden_table_02)（CC0） | 复用现成模型和 1K 纹理，缩放到 0.70 × 0.60 × 0.70 m（原模型高 0.80 m）；碰撞体按模型取桌面和四条腿（`TaskConfig.table_colliders`） |
| 房间、台子、木楔、储物柜 | 参数化几何 | 保留任务所需的尺寸和接触形状；没有用不匹配的装饰模型替换物理工具 |

上述素材只替换显示外观，原有门铰链、门板碰撞体、箱体碰撞体、质量和摩擦参数仍用于物理仿真；送货桌例外，它的碰撞体按模型做成桌面加四条腿（见下方场景修订）。**把手目前仅为外观，没有独立把手碰撞或门锁机构**；控制器应推门板，不能假定可以抓住把手。箱子的细节和绳把手同样不属于可独立抓取部件。`TaskConfig(use_asset_visuals=False)` 可切回基础几何外观作对照。

素材来源、固定的 robosuite 提交及下载 SHA-256 记录在 `visual_assets/sources.json`；现成运行素材已保存在本任务目录，启动时不联网。重新下载和转换：

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe humanoid/g1_self_closing_door/scripts/prepare_visual_assets.py
```

- 两个房间总范围为 x=0–6 m、y=−2–2 m，分隔墙位于 x=3 m。
- 门板宽 1.5 m（原 1.3 m）、高 2.1 m、厚 0.045 m、质量 12 kg；门框留出装配间隙。门角范围 0–1.75 rad，向 B 房间开启，门底离地 12 mm。
- 每个物理步施加自闭力矩 `tau = -3 * angle - 6 * angular_velocity`（阻尼原为 1.2：欠阻尼的门板被推动后会甩到前面再弹回撞击门挡；现在从 1.3 rad 自闭约 4 s），通过铰链和真实碰撞响应；没有门锁、冻结或吸附逻辑。
- **2026-10-20 场景修订（作者同意修改环境后）**：搬运箱改为 0.20 × 0.18 × 0.16 m、0.4 kg 的小箱，放在 A 房间一个 0.45 × 0.45 × 0.50 m 的固定台子上（箱子中心 `(1.45, 0.80, 0.583)`，箱子悬出台子近边 6 cm，便于侧夹时手腕让开台面）；目标区内放一张 0.70 × 0.60 × 0.50 m 的固定桌子（中心 `(5.20, 0.25)`，近边 x=4.85），箱子送到桌面上即可。原 8 kg 重物改为 0.70 × 0.40 × 0.90 m、12 kg 的高储物柜（`crate`，摩擦 0.18），初始位于 `(1.75, −0.33)`，与门铰链一侧对齐；地面摩擦由 0.6 改为 0.18（光滑地板）。两个模拟器都按接触对的较大摩擦系数计算，所以机器人鞋底（1.0）、箱子（0.7）、木楔（0.9）和门板（0.6）不受地面系数影响，只有柜子和轻物体在地面系数上滑动。机器人手掌与手腕链接加硅胶垫（摩擦 2.0，H1/H4 中已允许）。木楔（0.7 kg）和轻物体（0.12 kg）保留为自由刚体候选工具，轻物体仅是候选失败工具。
- **2026-10-20 第二次修订（作者同意）：送货桌改成四条腿的木桌**。占地（0.70 × 0.60 m）、位置和摩擦（0.7）不变，只是不再是实心块：桌面厚为桌高的 8.4 %（0.70 m 时 5.9 cm），四条腿 5.9 × 8.1 cm（距长边 3.4 cm、短边 4.7 cm），桌面下是空的（机器人面对的近侧两腿之间净宽 0.34 m），与 Poly Haven Wooden Table 02 模型一致。原因：实心块让膝盖无处可放，按实机力矩上限运行时机器人只能停在离桌边 0.42 m 处，放箱时双手要伸到身前 0.56 m，箱子放不到桌面（停在桌面上方 15–25 cm 后松手掉下），持箱停步后的前冲则让膝盖撞上桌面侧面（`solution/runs/hw-chain-v20/v21/v28`，接触力 956–1211 N，超过 800 N 限值记失败）。两个后端都是一个固定刚体：Genesis 为单连杆 URDF（5 个盒子碰撞体加模型外观），Isaac 为运动学刚体 USD（同样 5 个碰撞体，箱子接触传感器按 `/Table` 过滤）。验证：箱子放在桌面上，两个后端的桌面支撑力都等于箱重 3.924 N，两个后端的 smoke 都通过（`media/*-smoke.json`）。评分和成功条件不变。`TaskConfig(table_style="block")` 可换回实心块对照。
- **2026-10-21 第三次修订（作者：“搬箱子用最简单的就行”）：台子和桌子都升到 0.70 m**（`TaskConfig.stand_height`，原 0.50 m），箱子初始中心 `(1.45, 0.80, 0.783)`，其余不变。箱子中心原在 0.58 m，取箱和放箱都要下蹲（骨盆 0.60 m、前倾 0.4 rad），按实机力矩上限运行时取箱约一半摔倒：肩部只有 25 N·m，手臂伸出时带着躯干晃，腰俯仰伺服（kp 5000、kd 5，约 5 % 临界阻尼，50 N·m）被激起振荡，最高 12 rad/s，把机器人甩倒。0.70 m 时箱子在站立手高附近，取箱和放箱都站着做，持箱时箱底仍高出桌面约 8 cm。试过 0.65 m：站着够不到箱子两侧，夹不出力（`solution/runs/dev-stand65-place-1/2`）。验证：Genesis 和 Isaac 中箱子放在 0.70 m 桌面上都静止于 z 0.78，桌面支撑力 3.924 N，等于箱重；两个后端的 smoke 都通过（`media/genesis.png`、`media/isaac.png` 已按新高度重新生成）。
- 改动原因见 [solution/README.md](solution/README.md)：原 2 kg 地面箱在 Genesis 默认接触模型下夹不稳（数值蠕滑，最高只抬起 6.6 cm），原 8 kg、摩擦 0.9 的重物（推动需 70 N）只能用脚蹭，木楔要靠脚精确踢到门弧线下方；改成台面小箱和可手推的柜子后，H4 已验证的台面取箱、Agile 持箱行走和推物技能可以直接复用；门加宽到 1.5 m 并加大闭合阻尼是为了给柜子留出侧向漂移余量并避免门板回弹撞偏柜子。
- 目标区中心 `(5, 0)`、大小 1.1 × 1.1 m。默认超时 120 s（原 90 s），终点连续稳定放置 2 s。
- 控制 50 Hz，物理 200 Hz。43 维动作按 `robot.JOINT_NAMES` 排序，关节目标为 `default_q + 0.25 * action`，限制在关节范围内。电机参数沿用仓库的 G1 开发配置，尚非实机能力校准值。
- 199 维观测：关节位置/速度 86、上次动作 43、机器人根状态 13、箱子/木楔/柜子/轻物体各 13、门角/角速度 2、起箱/穿门/终点保持 3。每个刚体状态为位置、wxyz 四元数、线速度、角速度；位置采用各环境局部世界坐标。目前提供完整状态观测，未实现隐藏物性评测。

```python
import torch
from humanoid.g1_self_closing_door.genesis_env import G1SelfClosingDoorGenesis

env = G1SelfClosingDoorGenesis(num_envs=2, auto_reset=True)
obs, reward, done, extras = env.step(torch.zeros(2, 43, device=env.device))
env.reset([0])  # 只重置第一个场景
env.close()
```

Isaac 对应类为 `G1SelfClosingDoorIsaac`，必须在 `AppLauncher` 启动后导入；其 `reset/step/state/get_observations` 接口与 Genesis 相同。
`extras` 包含 `info`、`time_outs`、`final_observation` 和 `final_observation_mask`；默认自动重置，`auto_reset=False` 时调用方应在终止后停止控制或重置。

### 判定及验证边界

每个物理步检查“起箱”：箱底离地 6 cm、双手接触各超过 2 N，且地面或固定台面给箱子的竖直支撑力低于箱重的 25%（在台子上夹住但没抬起不算起箱）；穿过 x=3 的时刻要求箱子仍满足该条件，且箱体完整位于门洞宽高范围内。终点要求整个箱体位于目标区、正立、线速度低于 0.10 m/s、角速度低于 0.20 rad/s、地面或桌面支撑力超过半箱重、双手接触各低于 1 N，机器人已进入 B 房间，持续 2 s。摔倒、机器人越界及超限接触（含对台子、桌子的碰撞）记失败。`genesis_env.leg_tau_override` 是默认关闭的特权腿部力矩入口，仅供专家参考解在接触 QP 站姿阶段使用并计数。

当前碰撞检查为开发期近似：Genesis 检查机器人对门和墙的合接触力，Isaac 检查非足部净接触力，默认阈值 800 N。两者的接触聚合方式尚未统一，不能据此宣称严格的跨模拟器评分等价，也未实现材料损伤模型。原始 `state()` 返回手部接触、地板支撑、门及工具状态，可供后续控制器记录交互轨迹。

已保存 `media/genesis-smoke.json`、`media/isaac-smoke.json` 以及场景图。两个后端各运行 2 个场景、150 个控制步（600 个物理步），检查有限观测、自闭、地面接触、无假成功及重置。零动作保持默认关节姿态不能维持平衡，约 0.975 s 后记录失败；smoke 为检查门机构继续运行至 3 s，不属于有效任务轨迹。

```powershell
D:\rsi_vla\genesis_env\Scripts\python.exe -m unittest discover -s tests -p test_self_closing_door.py -v
```

10 项合成判定测试覆盖无搬运假成功、台上夹住不算起箱、放手及保持时间、摔倒、支撑力、完整目标包含、局部重置和场景布局。这些测试不证明物理可解。**尚未验证机器人开门、工具有效放置、双手搬箱穿门及失败恢复的完整连续执行**，因此不将任何参数变体标记为已验证可解。工具选择与使用不作为强制评分条件，以保留合法替代策略。

A single Unitree G1 must carry a box from room A to room B through a door with a self-closing mechanism. The G1 can open the door, but cannot keep holding it open while carrying the box with both hands. Wooden wedges, heavy objects, and other interactive objects are available. The agent must independently discover how to keep the door open.

## Task

- Through interaction, the agent discovers the door's closing mechanism, diagnoses why direct transport fails, and explores which objects can serve as temporary holding tools.
- The agent may use a wooden wedge, a heavy object, or another object to prevent closure, but must verify placement, friction, and the resulting holding effect.
- The agent independently writes a long-horizon control harness to coordinate opening the door, placing a tool, checking the door state, regrasping the box, traversing the doorway, and placing the box at its destination.
- If the door cannot remain stably open, the agent uses execution feedback to adjust the tool, its placement, or the passage sequence rather than repeatedly executing a failed strategy.

These are candidate strategies for benchmark design, not a prescribed solution. Evaluation instructions state the delivery goal and public constraints without identifying a correct tool or placement. Valid alternative strategies receive credit.

## Advanced Variants

Vary door closing force, friction coefficients, doorway width, box dimensions, and available tools' physical properties. Include ineffective wedges or heavy objects that slide easily. Every admitted variant must retain at least one physically executable solution with the available robot controller and scene resources. Test whether the agent recognizes tool failure and reconstructs its control program.

Physical feasibility remains to be validated. Confirm that the robot can open the door and carry the box, that two-handed carrying prevents continuous hand support of the door, and that at least one tool placement leaves sufficient stable clearance for both robot and box. Validate frictional holding, the closing mechanism, tool slippage, and the complete release–regrasp–traversal sequence. Do not substitute a scripted door lock for physical tool interaction.

## Evaluation Contract

The robot delivers the box from room A into the designated region in room B and places it stably, while satisfying declared collision, stability, and damage constraints. Define numerical tolerances and the final dwell time before evaluation. The door only needs to stay sufficiently open during passage; permanent door fixation or tool cleanup is not required unless explicitly included in the instance goal.

Verify success through continuous physical execution. Record opening attempts, tool choices and placements, door-state checks, regrasping, traversal attempts, failures, and recovery costs. Do not allow state edits, door freezing, or contact bypasses to replace tool use.

Use the observations allowed by the evaluation setting to assess whether the agent distinguishes ineffective tool geometry, insufficient friction, excessive closing force, and inadequate passage clearance. A plausible explanation without a successful physical adjustment does not establish recovery.

## Implementation Priorities

- [x] Build rooms A and B, the self-closing door, transport box, candidate tools, and destination region in Genesis and Isaac Lab.
- [x] Validate door opening, two-handed box transport, and the direct-transport limitation (Genesis, revised scene; one recorded trajectory).
- [x] Validate at least one physically effective tool placement and a complete delivery trajectory (`solution/runs/expert-v23` and `expert-v20`; repeatability pending).
- [x] Provide robot observations and control interfaces, and implement initial success, contact, and stability checks (physical calibration and contact parity pending).
- [ ] Add ineffective tools and physical variants with verified feasible solutions, then evaluate tool discovery and harness recovery.

## Core Capabilities Evaluated

Autonomous Tool Discovery · Physical Affordance Reasoning · Environmental Modification · Harness Construction · Long-Horizon Planning · Failure Recovery

See the [Tool Discovery category](../../README.md#tool-discovery) and the benchmark proposal in [English](../../doc/self-modeling-benchmark-v4-en.html#humanoid-h3) or [中文](../../doc/self-modeling-benchmark-v4-zh.html#humanoid-h3).
