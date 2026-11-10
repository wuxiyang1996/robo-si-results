# G1 桌面汉诺塔：隔离评测沙箱

本任务的评测沙箱建在仓库统一运行时 [`infra/sandbox/`](../../../infra/sandbox/ONBOARDING.md) 上，两个桌面任务（汉诺塔、[工具辅助装配](../../g1_tabletop_assembly/sandbox/README.md)）共用桌面层 [`humanoid/g1_tabletop/sandbox/`](../../g1_tabletop/sandbox/)。本目录只保留汉诺塔特有的部分：密封场景生成、评分谓词、监视器配置、参考专家录制。结构照抄 H4（`g1_ramp_bridge_construction/sandbox/`）。

## 1. 文件

| 文件 | 作用 |
|---|---|
| `launch.py` | `SandboxTask` + 本任务选项（`--disks 3/4/5`、`--seed`、`--backend`、`--dev-resets`、`--nominal`）→ `infra.sandbox.launcher.launch()` |
| `trusted/scenarios.py` | 密封场景：每个 episode 的盘数、时限（3/4 盘 180 s，5 盘 420 s）和随机场景（任务的 `randomization.sample_scene`，由种子与 episode 序号决定，`check_scene` 拒收篡改或越界的场景；`--nominal` 改用名义场景，只用于回放种子 0 录制）；dev/eval 默认 3 盘，grade 依次 3、4、5 盘 |
| `trusted/world.py` | 共享桌面世界 `TabletopWorld` + `G1TabletopHanoiGenesis(cfg=TaskConfig(num_disks, max_episode_seconds))`，物理不变 |
| `trusted/statelog.py`、`sensors.py`、`server.py` | 共享记录器、G1 传感器套件、共享 worker 的薄入口 |
| `trusted/scoring.py` | 回放任务自身 `task_spec.Evaluator` 得到四个连续阶段值 |
| `trusted/monitors.py` | 共享监视器套件（`infra.sandbox.monitors.run_profile`）+ 桌面视图与几何 |
| `trusted/verifier.py` | `verify_episode` / `verify_run`（共享桌面判定 + 共享运行级判定） |
| `trusted/record_reference.py` | 参考专家证据：`replay`（数据集动作经沙箱命令通道回放）、`live`（专家控制器黑盒录制）、`exploit`（真实特权写入攻击） |
| `agent_sdk/` | 公开包中的 agent 指南与 `hello_robot.py`、`noop.py` |
| `tests/` | `test_static`、`test_scoring`、`test_monitors`、`agents/escape_probes.py` |
| `../admission.json` | `infra-admission/1` 准入记录 |

共享桌面层（两任务共用，`humanoid/g1_tabletop/sandbox/`）：`envview.py`（环境视图，见第 3 节）、`world.py`、`statelog.py`、`evaluation.py`（评估器回放）、`scoring.py`、`monitors.py`、`verifier.py`、`reference.py`（回放 / 黑盒录制 / 攻击录制）、`scenarios.py`、`sensors.py`、`testing.py`（无仿真器的合成 episode）。

## 2. 运行（仓库根目录；仿真经 GPU 队列）

```powershell
$py = 'D:\rsi_vla\genesis_env\Scripts\python.exe'
# 开发（进程隔离，仅开发用）
& $py -X utf8 -m humanoid.g1_tabletop_hanoi.sandbox.launch task --mode dev --seed 1 --isolation process --no-video --name dev-hello --agent-dir humanoid/g1_tabletop_hanoi/sandbox/agent_sdk/examples -- python hello_robot.py
# 评测（Docker 容器）与评分（每个密封 episode 一次、全新工作区）
& $py -X utf8 -m humanoid.g1_tabletop_hanoi.sandbox.launch task --mode eval --agent-dir <交付目录> -- python solve.py
& $py -X utf8 -m humanoid.g1_tabletop_hanoi.sandbox.launch task --mode grade --episodes 3 --agent-dir <交付目录> -- python solve.py
# 参考专家证据（可信侧）
& $py -X utf8 -m humanoid.g1_tabletop_hanoi.sandbox.trusted.record_reference replay --disks 3 --out <新目录>
& $py -X utf8 -m humanoid.g1_tabletop_hanoi.sandbox.trusted.record_reference live --disks 3 --out <新目录>
# 重新判定
& $py -X utf8 -m humanoid.g1_tabletop_hanoi.sandbox.trusted.verifier --run <run>/trusted
& $py -X utf8 -m unittest humanoid.g1_tabletop_hanoi.sandbox.tests.test_static humanoid.g1_tabletop_hanoi.sandbox.tests.test_scoring humanoid.g1_tabletop_hanoi.sandbox.tests.test_monitors
```

默认后端为 CPU：这是任务的默认后端，也是全部参考录制所用后端；在 CPU 上同一动作序列逐位复现（第 6 节）。`--backend gpu` 可用，但未做复现验证。

## 3. 环境与命令通道

- **环境不变。** worker 构建的就是任务自己的 `G1TabletopHanoiGenesis`：同一场景、摩擦（椭圆锥、扭转摩擦）、求解器选项、资产、力矩上限和评分器。一个 50 Hz 控制步就是一次 `env.step_targets(q)`：4 个 5 ms 物理步，每步按固定增益 `tau = kp (q* - q) - kd dq` 计算并裁剪到 G1 MJCF `actuatorfrcrange`，评分器逐物理步更新（结果锁存时最后一个控制步可短于 4 个物理步）。
- **环境视图（`envview.py`）。** 该环境用 `scene.build()` 建立无批次轴的场景，而共享运行时（`infra.sandbox.sensors`、`statelog.world_params / full_state / ContactSplitter`）按单环境批次读取并取 `[0]`。`EnvView` 只读地给机器人和刚体求解器的 getter 加上该轴（无 setter），环境对象本身不变。传感器相机必须在 `scene.build()` 之前加入而环境没有钩子，因此构造期间临时包装 `Scene.build`，先加相机再建场景（相机只在读取时渲染，不参与物理）。
- **只提供 servo 模式。** 环境只接受绝对关节目标，故 mode 1 = 该环境的固定增益显式 PD（不是仿真器隐式 PD），mode 0（motor）以 `ValueError` 拒绝；`kp`/`kd` 只能省略或等于 `info["robot"]["servo_gains"]`；`dq*`、`tau_ff` 与其他任务的 servo 模式一样被忽略；`q` 裁剪到关节限位（环境拒绝越界目标）并报告裁剪数。力矩上限 = MJCF 上限（世界构建时用 `infra.sandbox.world.hardware_effort` 核对）。
- **回合结束。** 评分器锁存结果（成功或违规：非顶盘、多盘、大压小、横穿杆、掉落）时结束，原因对 agent 只报 `task_ended`（评分器超时报 `time_limit`），不透露成败；另外是时限、`finish`/`declare_infeasible`、启动器关闭。骨盆固定，不会摔倒。
- **传感器**：共享 G1 套件（头部 D435 RGB-D、MID-360 仿真、IMU、Dex3 触觉、足底力），`tau_est` 为上一物理步实际施加力矩。
- 质量与摩擦每 500 控制步做摘要核对（经视图得到全部 60 个连杆质量与 136 个几何体摩擦比）。

## 4. 记录与评分

**状态日志**（`g1_tabletop/sandbox/statelog.py`）：每控制步一行，含 ONBOARDING 第 2 节的标准字段（`t, root_pos, root_quat, joint_pos, joint_vel, tau, obj_pos/quat/vel/ang, contact`）与指令目标 `target`；另含**评分器所需的全部输入**：该控制步每个物理步传给评分器的测量（float32 位姿与速度——环境交给评分器的正是这些值、四个接触标志、接触/支撑/夹具力、按名支撑力及其存在掩码），以及环境评分器的实时锁存状态（`live_success/failed/progress`）。5 Hz 求解器快照、SHA-256 清单等由共享运行时提供。

**评分**（`trusted/scoring.py`）：verifier 用未修改的 `task_spec.Evaluator` 逐物理步回放日志中的输入，每控制步只读其内部状态：

| 阶段 | 模式 | 权重 | 值 |
|---|---|---|---|
| `disk_lifted_clear` | once | 0.10 | 活动盘有手接触并越过源杆顶 → 1；之前为 0.5 × 抬升比例 |
| `first_move` | once | 0.10 | 第一次合法移动提交 → 1；之前为 0.5 × 在其他杆上的放置保持比例 |
| `tower_progress` | once | 0.50 | 1 − d/(2^n − 1)，d 为已提交盘位到目标的最少剩余步数（来回搬动不得分） |
| `goal_hold` | live | 0.30 | 评分器锁存成功 → 1；之前为最终 2 s 保持比例 |

任务定义为二值得分（`task.toml`: `partial_progress_has_score = false`），所以 episode 分数 = 1（经核实的成功）或 0；加权阶段峰值仅作为诊断 `process_score` 报告。成功需同时满足：回放评分器锁存成功且最后阶段在报警窗口之外保持到结束；环境实时评分器同样锁存成功（交叉核对）；回放与实时逐行一致（同一行锁存、同一原因、同一耗时、同一移动序列）；独立的终态检查（各盘在 C 杆槽位、倾角、低速、无机器人接触）通过。任一不一致记为 question 2 标记并判不成功。沙箱 episode 若无任何 `observe()` 而得正分则清零（开环）。

## 5. 监视器与校准

`trusted/monitors.py` = 共享监视器套件（`infra.sandbox.monitors.run_profile`）+ 桌面视图与几何（`g1_tabletop/sandbox/monitors.py`）：物体速度（由记录位姿差分）与瞬移（含固定骨盆）、物体最低点低于其下方支撑（底座、桌面、地面；圆环最低点按倾角计算，细杆不算支撑）、无机器人接触做功的物体能量增加、指令模式（手指抖动、手臂抖动、腿/腰力矩饱和、顶关节限位）、进度尖峰、阶段乱序、可解任务上的不可行声明、参考录制中的特权写入。没有墙（物体掉下桌面由评分器判掉落），骨盆不会摔倒。

阈值沿用共享默认值（H4 标定），只有物体能量一项按轻物体缩小：窗口 0.3 J、作废 3 J（H4 为 6 / 60 J，对应数千克的板与箱；0.12 kg 的盘要凭空升高约 5 m 才会触发原阈值）。合成攻击测试中盘无接触升高 0.8 m 触发窗口、3 m 触发作废。一秒以内的极短 episode 不判指令模式（共享 `commands()` 的 1 s 窗口在更短日志上会形状出错，见第 8 节）。

以下为旧 24 段 episode 的最大值（各 episode verdict 的 `monitor_metrics`；全部无报警）：

| episode | 物体速度 m/s | 单步速度 m/s | 支撑穿透 m | 无功能量 J | 手指反转 Hz | 手臂抖动 | 饱和 s | 顶限位 s | 进度尖峰 |
|---|---|---|---|---|---|---|---|---|---|
| 阈值 | 9 | 20 | 0.03 | 0.3 | 8 | 3.0 | 3 | 2 | 0.25 |
| replay-3disks | 0.743 | 0.743 | 0.001 | 0.000 | 0 | 0.157 | 0 | 0 | 0 |
| replay-4disks | 0.743 | 0.743 | 0.001 | 0.001 | 0 | 0.157 | 0 | 0 | 0 |
| replay-5disks | 0.756 | 0.756 | 0.001 | 0.001 | 0 | 0.157 | 0 | 0 | 0 |
| live-3disks / 4disks / 5disks | ≤0.756 | ≤0.756 | 0.001 | ≤0.001 | 0 | 0.157 | 0 | 0 | 0 |
| dev-hello / eval-hello / grade-noop | 0.136 | 0.234 | 0.000 | ≤0.001 | 0 | 0.042 | 0 | 0 | 0 |

合成攻击（`tests/test_monitors.py`）全部触发：瞬移（作废）、抛射 12 / 17 m/s（窗口 / 作废）、盘陷入底座 5 / 15 cm（窗口 / 作废）、无功升高（窗口 / 作废）、手臂抖动、手指抖动、腰部饱和与肘部顶限位、单帧进度尖峰、阶段乱序与不可行声明（标记）、特权写入与超界增益（作废）；最终保持期间手臂抖动的窗口使成功不被计入。

## 6. 参考专家证据

当前默认使用 12 段数据集。2026-10-22 重录后的 `ring12-replay-3disks`、`ring12-replay-4disks`、`ring12-replay-5disks` 均通过命令通道回放和 verifier，无报警、无特权写入，盘位置与源录制最大差 0 m；本轮使用 `--no-video`。步数、移动时刻和监视器数值见[验证摘要](../validation/ring12_adoption.json)。

以下表格保留旧 24 段版本的历史证据：

| 运行目录（`runs/reference/`） | 方式 | 判定 | 与原录制比较 |
|---|---|---|---|
| `replay-3disks` | 数据集 `disks_3_seed_0` 的关节目标经命令通道回放，含 `motion.mp4` | 成功，无报警 | 4195 控制步、83.885 s、7 次移动及时间一致，盘位置最大差 0.0 m |
| `replay-4disks` | 同上，4 盘，含视频 | 成功，无报警 | 8660 步、173.19 s、15 次移动一致，差 0.0 m |
| `replay-5disks` | 同上，5 盘，含视频 | 成功，无报警 | 17589 步、351.78 s、31 次移动一致，差 0.0 m |
| `live-3disks`、`live-4disks`、`live-5disks` | `solution/run_expert.py --controller centered --seed 0` 黑盒运行，外挂记录器 | 成功 3/3，无报警 | 与数据集录制逐位一致（差 0.0 m；7 / 15 / 31 次移动） |
| `../exploits/teleport-disk` | 真实攻击：保持 1 s 后可信侧 `set_pos` 把顶盘瞬移到 C 杆 | **VOID**（特权写入、瞬移、速度、无功能量） | — |

每个参考 episode 中，回放的评分器与环境实时评分器在同一控制步锁存同一结果，独立终态检查一致；特权写入与超界增益写入均为 0。回放时 394 个目标值因 float32 表示略超 float64 关节限位而被裁剪，裁剪后转为 float32 与原目标相同，因此轨迹逐位一致。

## 7. 验证记录（2026-10-21）

| 检查 | 运行目录（`runs/`） | 结果 |
|---|---|---|
| 单元测试 | — | 38 项通过（static 9、scoring 17、monitors 12） |
| 开发冒烟（进程隔离） | `dev-hello` | 非 VOID，0 分；请求日志哈希链完整（7 条） |
| 容器评测 hello | `eval-hello` | 非 VOID，0 分；全部 6 种传感器读取 |
| 逃逸探针 | `escape` | 38/38 符合预期，17 次接口违规，**VOID** |
| 评分模式 no-op | `grade-noop` | 2 个密封 episode（3、4 盘），各一次连接，0 分，非 VOID |
| 开发重置 | （进程内冒烟） | `reset` 恢复初始姿态，重置前后两个 episode 均可判定 |
| 参考录制 | `reference/*` | 见第 6 节 |
| 重新判定 | `validation/` | 当前 verifier 重新判定全部运行与参考 episode，与启动时的判定一致（`validation/summary.json`） |
| 准入记录 | `../admission.json` | `python -m infra.sandbox.records` 无问题 |

## 8. 缺口与待定

- 随机化器已实现（2026-10-21，见任务 [README「场景随机化方案」](../README.md#场景随机化方案)）：评分 episode 默认使用随机场景。本轮随机场景已使用可信记录器保存并经 verifier 判分，完整回归与保留的失败见 `../acceptance/release_20261022/`。身体变化已实现为 `--body-variation` 实验选项，尚未通过完整物理覆盖，默认关闭。
- 只在 CPU 后端验证了逐位复现；GPU 后端可运行但未验证。
- 人工阶段标注、视频签审、捷径审计和第二人复现仍未完成。CPU 流水线已有通过记录；最终版本的全层流水线仍需完成（见 `admission.json`）。
- 共享运行时问题（未修改，已在报告中提出）：`infra.sandbox.monitors.commands()` 在不足 1 s 的日志上抛形状错误（本任务的视图对 ≤1 s 的 episode 跳过指令模式）；`infra.sandbox.statelog.world_params()` 对 `get_links_mass()` 取 `[0]`，而 Genesis 的连杆质量没有环境轴，批次场景中摘要只覆盖第 0 个连杆的质量（桌面层经 `EnvView` 得到完整向量，不受影响）。
- `task.toml` 已记录 sandbox 可用，但 `admitted=false` 与发布门槛独立保留；Hanoi 仍按文档定义的顺序操作任务分类，不声称已经通过工具发现三层设计验收。
