# M4 双 Go2 绳索协同拖运：隔离评测沙箱

本目录把 M4 放到仓库统一的沙箱运行时 [`infra/sandbox/`](../../../infra/sandbox/ONBOARDING.md) 上。结构照搬 H4
（`humanoid/g1_ramp_bridge_construction/sandbox/`）：任务只保留自己的场景、执行器细节、日志行、阶段谓词和监测配置，
其余（密封、交付快照、内容寻址的公开包与镜像、容器隔离、可信 worker、哈希链请求日志、运行级判定）都是共享运行时。

## 1. 场景与接口

| 项 | 内容 |
| --- | --- |
| 场景 | 专家解所解的两个场景变体，原样密封（物理内容按摘要冻结，见 `trusted/scenarios.py`）：第 1 层 **base** = `solution/task_tow.json`（走廊 2.6 m、货物 15 kg、地面 0.8）；第 2 层 **hard** = `solution/task_hard.json`（走廊 1.6 m、货物 50 kg、地面 0.3、时限 120 s）。两者都含预连接绳索和焊接挡边，参数不变 |
| 构建 | 与专家完全相同：`simulation_tasks.genesis_runner.TaskScene` + `solution/rig.py` 的 `RopeRig`（`sensor_factory` 钩子），CPU 后端；绳索生成文件写到本次运行的可信目录（`rig.OUT`），不写 `solution/` |
| 机器人 | 两台 Go2，`infra.sandbox.world.MultiRobotChannel`，每台一个 `RobotLimits`（12 关节）；命令与观测按机器人命名空间 `{"go2_a": …, "go2_b": …}` |
| 控制 | 50 Hz（= 4 个 0.005 s 物理步，正是专家行走策略的频率）。mode 1 伺服 = Genesis 位置 PD（默认 kp 35 / kd 1，与 TaskScene 和专家一致）；mode 0 电机 = 每个物理步重算 `tau_ff + kp(q*-q) + kd(dq*-dq)` 并限幅 |
| 限位 | 力矩/速度取 Go2 模型（go2.urdf）：髋/大腿 23.7 N·m、30.1 rad/s，小腿 35.55 N·m、20.07 rad/s（TaskScene 的力矩范围正是这些值）；关节位置限位取模型 |
| 增益上限 | kp ≤ 100、kd ≤ 5。依据：专家行走策略在 kp 35 / kd 1 下训练和运行（`locomotion/policy/policy.json`）；Unitree 官方 Go2 底层站立例程用 kp 60 / kd 5；上限覆盖两者并留余量，更硬的增益在真机伺服上没有对应 |
| 传感器 | 新增共享模块 [`infra/sandbox/sensors_legged.py`](../../../infra/sandbox/sensors_legged.py)（足式机器人通用，GO2 规格来自 URDF），每台一份，再用 `NamespacedSensors` 包成一体：`proprio`（q、dq、实际施加力矩 tau_est、机身 IMU：相对起始偏航的四元数 / 陀螺 / 加速度计）、`foot_force`（四足接触力，足端坐标系）、`rgb` / `depth`（头部前视相机 320×240） |
| 装备 | `info()` 公布每台机身上的拖钩位置（绳已连好，不能解开、重连或打结，没有 attach 命令）；不公布绳的另一端、平台、货物或任何场景量 |
| 结束 | `finish()` / `declare_infeasible()`、时间预算（默认 120 s，hard 变体上限为其自身的 120 s）、任一台摔倒（机身 < 0.14 m 或倾角 > 45°，任务约束）、仿真发散（非有限状态，记 0 分） |

公开包（`launch.build_bundle`，内容寻址）只含：`go2sandbox/`（共享线协议 `protocol.py` 原文件 + 双机客户端）、
`examples/`、`README.md`（agent 指南）、`instruction.md`、`robot/go2/`（仿真加载的 Go2 URDF 与网格）、`Dockerfile`。
共享运行时的 `build_bundle` 总会放入 G1 模型和 GR00T 权重，所以 M4 用 `launcher.launch` 的 `build` 钩子自建包（见第 8 节）。
**没有提供 Go2 行走控制器**：专家的 L1 策略是专家自己训练的（`solution/locomotion/`），属于参考解，是否作为公开 L1 技能由作者决定。

## 2. 运行（在 `D:\rsi_vla\robo-si` 下，模拟器运行都经过 GPU 队列）

```powershell
$py = 'D:\rsi_vla\genesis_env\Scripts\python.exe'
$q  = 'C:/Users/wuxiy/AppData/Local/Temp/claude/d--rsi-vla/2f795ddc-4e2e-4209-82f7-00dd0d1f3417/scratchpad/unify/tools/gpu_queue.py'
$m  = 'multi_robot.dual_quadruped_cooperative_transport.sandbox'
# 单元测试（无模拟器）
& $py -m unittest "$m.tests.test_static" "$m.tests.test_scoring" "$m.tests.test_monitors"
# 开发冒烟（进程隔离）
& $py $q -- $py -X utf8 -m "$m.launch" --mode dev --isolation process --no-video --name dev-hello --agent-dir multi_robot/dual_quadruped_cooperative_transport/sandbox/agent_sdk/examples -- python hello_robot.py
# 容器评测 / 逃逸探针 / 打分（2 个密封回合：base、hard）
& $py $q -- $py -X utf8 -m "$m.launch" --mode eval --no-video --name eval-hello --agent-dir multi_robot/dual_quadruped_cooperative_transport/sandbox/agent_sdk/examples -- python hello_robot.py
& $py $q -- $py -X utf8 -m "$m.launch" --mode eval --no-video --name escape --agent-dir multi_robot/dual_quadruped_cooperative_transport/sandbox/tests/agents -- python escape_probes.py
& $py $q -- $py -X utf8 -m "$m.launch" --mode grade --episodes 2 --no-video --name grade-noop --agent-dir multi_robot/dual_quadruped_cooperative_transport/sandbox/agent_sdk/examples -- python noop.py
# 参考专家（黑盒）记录并判定
& $py $q -- $py -X utf8 -m "$m.trusted.record_reference" --variant base --out multi_robot/dual_quadruped_cooperative_transport/sandbox/runs/reference/<name>
& $py $q -- $py -X utf8 -m "$m.trusted.record_reference" --variant hard --out multi_robot/dual_quadruped_cooperative_transport/sandbox/runs/reference/<name>
# 重新判定
& $py -m "$m.trusted.verifier" --run multi_robot/dual_quadruped_cooperative_transport/sandbox/runs/<run>/trusted
& $py -m "$m.trusted.verifier" --episode multi_robot/dual_quadruped_cooperative_transport/sandbox/runs/reference/<name>/episode_00
```

## 3. 文件

| 文件 | 作用 |
| --- | --- |
| `launch.py` | `SandboxTask`、M4 选项（`--layer 1/2`、`--seed`、`--backend`、`--dev-resets`）、自建公开包 |
| `instruction.md` | 给 agent 的任务说明（不含解法提示） |
| `agent_sdk/go2sandbox/` | 双机客户端 `RobotPair`（只有传感器和关节命令） |
| `agent_sdk/examples/hello_robot.py`, `noop.py` | 读取全部传感器、发一次命令、结束 / 空操作下限 |
| `trusted/scenarios.py` | 密封场景：两个变体，物理摘要冻结；评测/打分种子私有生成 |
| `trusted/world.py` | `SandboxWorld(MultiRobotChannel)`：建场景、50 Hz 执行律、结束条件、公开信息、世界参数校验 |
| `trusted/sensors.py` | 每台一个 `LeggedSensors(GO2)`，`NamespacedSensors` 包装 |
| `trusted/statelog.py` | 每个控制步一行可信日志（见文件头），含专家证据层同款的接触汇总；扩展的世界参数摘要（质量、惯量、摩擦、力矩范围、电枢、阻尼、刚度） |
| `trusted/scoring.py` | 10 项物理证据、5 个阶段、过程分、成功判据、evaluate.py 样本 |
| `trusted/monitors.py` | 共享监测套件的 M4 配置 |
| `trusted/verifier.py` | `verify_episode` + `TaskVerifier` + `verify_run`（evaluate.py 交叉验证） |
| `trusted/server.py` | 共享 worker 的薄入口 |
| `trusted/record_reference.py` | 原样黑盒运行专家并写成沙箱日志格式，再用同一验证器判定 |
| `tests/` | `test_static`、`test_scoring`、`test_monitors`、`agents/escape_probes.py` |

## 4. 评分

**物理证据。** `multi_robot/evaluate.py` 要求每个采样都有 10 项证据标志，任一采样为假即判违规。`scoring.evidence()`
在可信日志上按专家证据层（`solution/monitor.py` 的 `CHECKS`）的定义和阈值、任务 `constraints` 重新计算这 10 项：
连续执行、无状态编辑、无接触绕过（碰撞掩码不变、动态体穿入墙/地 ≤ 2 cm）、机身稳定（≥ 0.14 m、≤ 45°）、执行器限位、
无剧烈碰撞（冲量 ≤ 25 N·s）、货物有支撑（贴合甲板或地面 ≤ 5 mm、倾角 ≤ 10°、机器人竖向托举 < 2 N、0.5 s 平均竖向支撑
≥ 30% 重量）、连接完整（焊点齐全、漂移 ≤ 10 mm、张力 ≤ 额定）、绳索张力与接触（绳段穿入墙/地 ≤ 1 cm）、牵引与滑移
（受力 > 15 N 的支撑足单次支撑内滑移 ≤ 5 cm）。日志里的接触汇总与专家监测层用同一个接触查询、同一套归属分类计算。
采样 = 已步进的行（t = 0 的初始行不是采样）。

**阶段**（README 的链条：张紧 → 直线拖运 → 转角 → 入区 → 放松/静置）：

| 阶段 | 模式 | 权重 | 值 |
| --- | --- | --- | --- |
| tensioned | once | 0.10 | 0.5 × clip(E / 20 N)，E = 较大的一根绳 0.5 s 平均张力，或机器人对货物/平台/挡边的 0.5 s 平均接触力（不用绳的路线同样计分）；E 达到 20 N 后平台离开起点 ≥ 5 cm 记 1 |
| straight_tow | once | 0.20 | 货物中心沿第一段走廊的进度 clip((x − x0)/(x_内角 − x0)) |
| corner | once | 0.25 | 过弯进度 clip((y − y0)/(y_内角 − y0)) |
| in_goal | live | 0.25 | 货物（真实尺寸与朝向，evaluate.py 的 AABB 规则）完全在目标体内为 1；否则 0.9 × 足迹落在目标区的比例 |
| released_settled | live | 0.20 | 拖运停止、货物静置：clip(驻留 / 2 s)，驻留 = 当前一段连续"完全在内 + 线速度 ≤ 0.03 m/s + 角速度 ≤ 0.15 rad/s + 10 项证据全真"的时长 |

只有"干净"的采样才计分：一旦某项证据为假，此后不再获得新的阶段分（之前的保留），与 evaluate.py 拒绝任何违规采样一致。
回合分 = 加权进度随时间的峰值（once 阶段取历史最大）。**成功** = 最后一个采样 released_settled 为 1（最终驻留 ≥ 2 s）且全程无违规，
即 evaluate.py `goal_observed` 的规则；验证器把同一批采样交给 evaluate.py 交叉验证，不一致时标记 `success_disagreement`。
evaluate.py 自身的 `success` 还要求任务状态为 `physically_validated`，两个变体尚未准入，所以单独报告。
不单独要求"松绳"：变体无法解开绳子，专家 base 运行结束时仍有 20–30 N 残余张力而货物静止。

**监测器**（`trusted/monitors.py`，共享套件）：货物/平台/挡边的速度、瞬移、地面穿透、与四面墙及货物-甲板之间的 OBB 穿透、
无功能量（能量上界计入机器人接触力和平台上的绳张力）；每台机器人的力矩饱和、顶关节限位、机身瞬移（经 `extra`，告警带机器人键）；
进度尖峰与阶段乱序；不可行声明（两个变体都有参考解，故标记）、特权写入与超界增益（作废）。共享 `commands()` 的预摔倒屏蔽用的是
G1 的 0.35 m / 50°，这里把机身高度抬高 0.21 m 传入（等价于 Go2 的 0.14 m），倾角仍是 50°。

## 5. 参考专家记录（`trusted/record_reference.py`）

专家（`solution/run_expert.py`）原样黑盒运行，参数与其文档化成功运行相同（base：`runs/final-mu080` 的 coop 控制器、60 s 上限；
hard：`runs/hard-final` 的 anchor 控制器 + `plan_hard.json`、120 s），场景为密封场景文件。记录器从外部挂钩：
`TaskScene.__init__`（建好场景和绳索后挂上沙箱 StateLogger）、`TaskScene.step`（计物理步、保存裁剪后的关节目标，每 4 步写一行，
即专家自己的采样时刻；控制步内目标变化计数，预期 0）、RigidEntity 与刚体求解器的全部位姿/速度/属性/限位/焊接/外力 setter
（第一个物理步之后的调用记为特权写入，预期 0；超过沙箱增益上限的增益写入作废）、`rig.OUT`（生成文件写进记录目录）、
`gs.Scene.destroy`（销毁前封存日志）。专家自己的输出（trajectory.json、evaluation.json、motion.mp4）保存在 `<out>/expert`，
`record.json` 含沙箱判定，以及专家证据标志与沙箱重算结果的逐采样比较。`--attack teleport|mass` 是诊断用的作弊检验
（记录器自己在 5 s 时把货物瞬移进目标区 / 改货物质量），永远不是准入证据。

| 记录 | 变体 | 判定 | 分数 | 阶段时间 tensioned / straight / corner / in_goal / settled (s) | 最终驻留 | evaluate.py | 证据逐采样一致 | 特权写入 / 增益写入 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `runs/reference/base-v1`（含 motion.mp4） | base | 成功 | 1.0 | 2.16 / 10.34 / 24.50 / 30.38 / 33.38 | 4.92 s | goal_observed | 1815 × 10，0 不一致 | 0 / 0 |
| `runs/reference/base-v2` | base | 成功 | 1.0 | 同上 | 4.92 s | goal_observed | 一致 | 0 / 0 |
| `runs/reference/hard-v1`（含 motion.mp4） | hard | 成功 | 1.0 | 1.66 / 16.84 / 22.34 / 31.24 / 34.52 | 5.66 s | goal_observed | 1909 × 10，0 不一致 | 0 / 0 |
| `runs/reference/hard-v2` | hard | 成功 | 1.0 | 同上 | 5.66 s | goal_observed | 一致 | 0 / 0 |

最终驻留与专家文档中的 `final-mu080`（4.92 s）、`hard-final`（5.66 s）完全相同；最大张力 149 / 169 N、最大单次支撑滑移
4.71 / 4.24 cm、最大倾角 25.6° / 19.8°、最低机身 0.264 / 0.261 m，也与专家记录一致。CPU 后端确定：同一变体两次记录的
状态日志逐字段逐位相同（1816 / 1910 行，有无视频都一样）。阶段时间与专家的阶段事件吻合（1 s settle 后开始拖运；货物入区后
slack → hold）。

| 作弊检验 | 判定 | 原因 |
| --- | --- | --- |
| `runs/exploits/teleport-v1`：5 s 时 set_pos 把货物移进目标区 | VOID | privileged_writes、teleport、object_speed_severe |
| `runs/exploits/mass-v1`：5 s 时 set_mass(1 kg) | VOID | world parameters changed、privileged_writes |

（mass-v1 中专家自己的证据层没有挂钩 set_mass，仍报 no_state_edits 为真；沙箱的监视清单更宽，这是两者唯一的不一致。）

## 6. 验证结果（2026-10-21，全部经 GPU 队列）

| 检查 | 运行目录（`runs/`） | 结果 |
| --- | --- | --- |
| 单元测试 | — | 55 个通过（test_static 13、test_scoring 18、test_monitors 24） |
| 开发冒烟（进程隔离） | `dev-hello-v3` | 非作废，0 分；两台机器人全部传感器读取、一次双机命令、finish；请求日志哈希链完整 |
| 开发重置 | `dev-reset-v3` | 重置后重建场景，起始姿态逐位恢复（`q` 差 0），计入最后一个回合，0 分，非作废 |
| 容器评测 | `eval-hello-v3` | 非作废，0 分（容器内读取两台的 proprio / foot_force / rgb / depth） |
| 逃逸探针 | `escape-v3` | 47/47 符合预期，20 次接口违规，VOID |
| 打分模式 | `grade-noop-v3` | 2 个密封回合（base、hard），每回合一次连接，均 0 分，非作废 |
| 参考专家 | `reference/*` | 4/4 成功，与 evaluate.py 一致（见第 5 节） |
| 作弊检验 | `exploits/*` | 2/2 VOID |
| 重新判定 | `validation/report.json` | 全部记录与运行用最终代码（m4-verifier/1，sha256 f87348bf0408…）重判，结论同上 |
| 准入记录 | `../admission.json` | `python -m infra.sandbox.records` 无问题 |

`*-v1` / `*-v2` 是同样的运行在两次代码修订前的版本（v1 之后：开发重置改为重建、张紧分加 5 N 死区；v2 之后：采纳共享运行时的
回合结束顺序与无批次读取器），判定与 v3 相同，保留作对照。v3 运行早于 `source_hashes()` 显式加入 `sensors_legged.py`
（只影响元数据）。

## 7. 监测器校准（m4-monitors/1）

全部使用共享默认阈值（`THRESHOLDS = {}`）。参考记录和 v3 沙箱回合都没有任何告警；实测最大值与阈值：

| 监测 | 参考记录最大 | 沙箱回合最大 | 阈值（窗口 / 作废） |
| --- | --- | --- | --- |
| 物体速度（位置差分） | 0.30 m/s | 0.015 m/s | 9 / 15 m/s |
| 单步瞬移（物体 / 机身） | 0.33 / 0.91 m/s | 0.015 / 1.28 m/s（起始落地） | 20 m/s 作废 |
| 地面穿透 | 0.8 mm | 0.1 mm | 3 / 10 cm |
| 墙体 OBB 重叠 | 0.5 mm | 0 | 3 / 10 cm |
| 货物-甲板重叠 | 0.8 mm | 0.2 mm | 3 / 10 cm |
| 无功能量 | 0.002 J | 0.001 J | 6 / 60 J |
| 力矩饱和（每台） | 0.04 s | 0 | 3 s |
| 顶关节限位（每台） | 0 | 0 | 2 s |
| 进度尖峰 | 0 | 0 | 0.25 |

单元测试中每个监测都有必须触发的作弊样例（瞬移、发射、无功能量、地面/墙/甲板穿透、每台的饱和与顶限位、机身瞬移、
进度尖峰、阶段乱序、声明、特权写入、超界增益）和不得触发的样例（步态式的关节反转不算抖动）。

## 8. 已知缺口与待作者决定

- **变体尚未准入**：两个变体的 `status` 是 `expert_candidate_not_admitted` 并列有覆盖缺口，evaluate.py 自身的 `success` 因此恒为假；
  沙箱报告的是物理部分 `goal_observed`。
- **Randomisation remains incomplete:** two fixed scenes. The 18 settle-time perturbations and two sandbox-recorded failures are now tabulated; see section 10.
- **专家读取特权状态**（平台位姿、绳张力），是特权参考解；它的 L1 行走策略没有作为公开技能提供，agent 只能从关节接口自建步态。
- **绳张力不是 agent 传感器**：变体里没有装在机器人上的测力计；是否加一个"拖钩测力计"由作者决定。
- **评分规则待确认**：不用绳的推送路线和单机路线同样计分；除"货物静止"外不要求证明松绳。
- **Other gates:** manual video labels, signed human review and independent reproduction remain pending. Shortcut evidence, review materials and manual pipeline runs are documented in section 10; the GPU simulator backend is unvalidated.
- 建图前的接触缓冲：第一个物理步之前 Genesis 的接触力还是建图时（腿伸直）的碰撞结果，`foot_force` 在第一步前报 0；
  可信日志的 t = 0 行不作为证据采样。

## 9. 对共享运行时的建议（未修改）

1. `BundleSpec` 应能关掉 G1 模型和 GR00T 权重（`copy_robot_model`、`wbc` 目前总会放进包），并允许指定别的机器人模型；
   M4 目前用 `launch()` 的 `build` 钩子和私有的 `_seal_bundle` 自建公开包。
2. `monitors.commands()` / `pre_fall_mask()` 应接受摔倒高度与倾角参数（现为 G1 的 0.35 m / 50°）；M4 只能把机身高度抬高 0.21 m 传入。
3. `MultiRobotChannel` 的 SDK 端：`g1sandbox.RobotClient._full` 假定单机 `info()["robot"]`，所以 M4 带了自己的
   `go2sandbox.RobotPair`（只依赖共享的 `protocol.py`）。共享运行时随后出现了 `infra/sandbox/agent_sdk/multisandbox`，
   但它导入 `g1sandbox`（包里会带上 G1 的 SDK）；若把协议与多机客户端从 G1 包里拆出来，M4 可以直接改用它。
4. 世界参数摘要（`statelog.world_params`）只含质量和摩擦比；力矩范围、电枢、阻尼、刚度（M4 的绳测力计弹簧）也应覆盖，
   M4 目前自己扩展。
5. `run_profile` 在视图没有关节数据时写入 `not_applicable["commands"]`，多机任务在 `extra` 里逐台判定时应能声明这一点
   （M4 用自己的 `not_applicable` 条目覆盖）。

## 10. Acceptance work recovered on 2026-10-22

This section finalizes evidence generated on 2026-10-21 and the resumed checks on 2026-10-22. New simulations in this resumed session used the specified Python and original GPU queue with its default single slot. No scoring, threshold, scene, physics or shared-runtime changes were made on resume.

Provenance: the inherited uncommitted `trusted/world.py` change only moves the episode-end parameter check before sealing, with `log.close` in `finally`; its inherited static test verifies that order. It does not change initial state or physics. The inherited `shortcuts.py` includes one explicitly modified-scene diagnostic (`hard-solo-scene-v1`); that historical recording is preserved and is not a sealed-agent route. Resumed code changes only add representative-sheet provenance to `stage_review.py`. Documentation and admission records were finalized here.

### 10.1 Manual pipeline: pending to partial

| Record under task `acceptance/pipeline/` | Tier | Result | Interpretation |
| --- | --- | --- | --- |
| `20261021-142043-cpu.json`, `20261021-142351-cpu.json` | cpu | 4/4 | Historical unit tests, rejudge and admission checks |
| `20261021-152121-gpu.json` | gpu | 0/2 | Both steps exhausted 1800 s while waiting for the shared queue; no episode output |
| `20261021-162435-container.json` | container | 1/3 | Eval/escape queue timeouts; two-layer grade passed after the lock became available |
| `20261021-184702-gpu.json` | gpu | **2/2** | Finished after the prior agent stopped responding; dev hello/reset 0, non-void; reset probe `ok: true` |
| `20261022-210714-container.json` | container | **3/3** | Resumed eval 56.4 s, escape 46.1 s, two-layer grade 60.7 s |
| `20261022-211558-cpu.json` | cpu | **4/4** | Resumed runtime tests, 55 task tests, rejudge and admission checks |

New runs: `pipeline-{eval-hello,escape,grade-noop}-20261022-210714`. Hello scores 0 and is non-void; escape probes all behave as expected and 20 interface violations make the run VOID; both grade episodes score 0 and are non-void. Each new container run's `source_manifest_end.json` reports `launch_scope_source_frozen: true` and no changed source.

All three launchers return **1** because `infra.sandbox.launcher.exit_code` defines unsuccessful/VOID episodes that way. Their trusted verdicts match `expect`, so the pipeline passes and returns 0. The successful historical GPU negative cases likewise return 1. These are not launch failures.

Each tier now has a complete passing record. They were manually invoked, not triggered on every code change, so `automatic_pipeline` remains **partial**. Historical queue-timeout failures are retained: pipeline step timeout includes time waiting for the queue. A proposed shared-runtime fix would start execution timeout after acquiring the lock; no queue or runtime edit was made. Historical aborted all-tier attempts without final records are not counted as passes.

**Historical approval rejection (resolved by explicit authorization in section 11):** the prior session tried adding `stage_review --no-sheets`, `shortcuts --check`, and `rerun_spread` as three CPU steps in `pipeline.json`. Auto mode rejected the action as dangerous, with no explanation. The exact command and rejection are preserved in `../acceptance/resume-20261022/approval_rejections.json`. A historical log-wait loop was separately rejected as `[Interfere With Workloads]`. At the recovery checkpoint neither denied action was retried. The user subsequently explicitly authorized the three pipeline stages; section 11 records their integration and passing validation. The unrelated denied log-wait loop was not retried.

The final CPU record captures source state before the last text-only documentation/readability corrections and addition of its own evidence link. No runtime source changed afterward.

### 10.2 Predicate labels: pending to partial

`trusted/stage_review.py` rejudged six successful references, eight shortcut attempts, eight negative sandbox runs and four void checks: **26/26 expectations match**. Output is in `runs/validation/resume-20261022/stage-review/`: `report.json`, `report.md`, `review_record.json` and `keyframes/`.

Each sheet takes the nearest 20 fps video frames at the verifier stage time -1/0/+1 s, preserves the HUD and marks the two inner-corner thresholds. Original videos exist only for base-v1 and hard-v1. Every trusted state array in v2/v3 is byte-identical to its variant's v1 and the verifier stage times match. Each no-video repeat therefore has its own clearly labelled **REPRESENTATIVE** sheet, with original-video path and SHA-256 provenance. It is not an independent video of that repeat.

The human review template contains verifier times, expected verdicts, video hashes and a three-question checklist. Manual times, answers, reviewer/date/signature are empty and `signed` is false. `visual_review_resume.json` records Codex's unsigned observations from the two original sheets: tensioning, turning, entry into the green goal, similar final cargo poses and standing robots are visible; base has residual rope tension at rest. Sparse frames cannot independently establish 5 cm displacement, averaged force, continuous 2 s dwell or absence of all physics violations. The historical draft's stronger claim that every center frame proves exact completion is not adopted; hard's nearest settled center frame is about 0.02 s early.

Human video labels, signed review and independent reproduction remain pending. Missing original videos for four repeats are an explicit limitation, not silently replaced by representative footage.

### 10.3 Shortcut audit: pending to partial

M4 has no standalone task card. The task README credits valid solo routes and distinguishes cooperation-required instances from cases where cooperation reduces cost. The task-design shortcut list asks authors to rule out solo completion when claiming cooperation is required. Existing expert components were used through the sandbox recorder, with per-run `shortcut.json` explaining whether its expectation is a contract or merely a recorded regression outcome.

| Recording under `runs/shortcuts/` | Observation | Current score / outcome |
| --- | --- | --- |
| `hard-solo-slack-v1` | Sealed hard scene; partner follows with slack rope. Cargo stalls at corner entry within 120 s; first stance-slip violation at 3.00 s | 0.0525, unsuccessful, non-void |
| `hard-solo-scene-v1` | Historical modified-scene diagnostic: second robot/rope removed, remaining rope centered. Reproduces expert solo stall; not a sealed-agent route | 0.0518, unsuccessful, non-void |
| `base-solo-slack-v1` | A single puller delivers cargo through the L and leaves it at rest. A 7.7 cm stance slip at 39.22 s violates the 5 cm rule | 0.7632, unsuccessful, non-void |
| `base-solo-gentle-v1` | Gentler single pull remains in the corner at 120 s; stance slip begins at 3.56 s | 0.1068, unsuccessful, non-void |
| `base-passive-partner-v1` | Inactive partner is dragged, tips over and contacts cargo; slip begins at 4.56 s | 0.1266, unsuccessful, non-void |
| `base-push-back-v1` | Robots push the front of the platform away from the goal; contact still earns full tensioned credit. Robot vertical cargo contact violates target support at 12.58 s | 0.1054, unsuccessful, non-void |
| `hard-formation-v1` | Naive formation delivers late but slips and becomes unstable earlier; motion after violation earns no new credit | 0.2213, unsuccessful, non-void |
| `hard-keepout-off-v1` | Removing controller keepout induces no robot/platform contact. Cargo settles, then stance slip reaches 5.07 cm during hold | **1.0000, unsuccessful**, non-void |

Current-verifier `shortcuts --check` matches all eight recorded expectations. This is regression agreement, not proof that eight shortcuts have been eliminated. In the hard scene the two tested single-puller strategies fail; this does not prove every possible solo strategy impossible. In base the physical delivery succeeds but the rule rejects its slip, so the evidence does not establish that cooperation is physically necessary.

A genuinely rope-free scene is absent from the sealed variants. Their short preattached tethers prevent robots reaching behind the platform for forward pushing; only front/side contact was sampled. Removing ropes requires a separately designed variant and log/scoring support, which was not implemented. `hard-keepout-off` did not produce dragging by body contact, so that route has **no successful physical sample** and remains unclosed. Vertical body contact on cargo is rejected by target support in the push-back/passive-partner samples.

Proposals only, requiring author decisions:

- Require forward first-leg displacement for tensioned progress; pushing 0.36 m away currently earns 0.10. Physically valid contact routes remain credited by the unchanged scorer.
- Gate corner progress on first-leg completion or use route progress. Lateral drift in the first corridor earns corner credit (hard-formation about 0.098 weighted; push-back about 0.0054 weighted).
- Decide whether peak score 1.0 without terminal success is intended. A last-sample live-stage score or unsuccessful-score cap would change this contract; neither is implemented.
- The authorized work retains the 5 cm slip constraint and must improve reference robustness. No threshold change is pending implementation.
- Qualify cooperation claims by tested evidence. A new cooperation-required instance or R9 tool-layer design needs its own physical validation; no such design is implemented here.

The gate stays partial because base solo capability is unresolved, rope-free/contact-drag routes are not comprehensively tested, and human confirmation is absent.

### 10.4 Reference rerun spread: remains partial

`runs/validation/resume-20261022/rerun-spread/report.md` confirms three same-argument recordings per variant: base 1816 rows, hard 1910 rows, matching state arrays, verdicts and stage times. Same-seed CPU spread is zero.

Existing settle-time perturbations pass base **4/6**, hard **10/12**. Maximum stance slip spans 3.3-7.5 cm / 3.9-6.2 cm around the current 5 cm constraint. Two failed settings are recorded through the sandbox: `perturbations/base-settle1.15-v1` and `hard-settle1.45-v1`, scoring 0.3405 / 0.6363, with first slip violations at 17.78 / 26.18 s. Sandbox, task evaluator and expert evidence agree sample by sample.

This verifies detection of current-rule failures and exposes reference sensitivity to perturbations. The current authorization retains the strict 5 cm physical rule. GPU backend, random-range endpoints and restored subtask starts remain unvalidated.

### 10.5 Randomisation and coverage: proposals only

No random ranges were implemented; each layer remains one fixed sealed scene. These are candidate ranges requiring author validation, not approved physical edits.

| Layer | Candidate variation | Candidate range | Required validation |
| --- | --- | --- | --- |
| base | Robot start positions / headings | +/-5 cm, +/-5 degrees | Reference robustness and collision/tether feasibility |
| base | Cargo mass | 10-15 kg | Endpoints and middle; 20 kg had slip failures in expert evidence |
| base | Cargo position on deck | +/-3 cm along length | Initial support and no rim overlap |
| hard | Corridor width | 1.6-1.8 m | Towable paths exist geometrically; record references at 1.7/1.8 m |
| hard | Cargo mass | 45-50 kg | Especially test solo completion at the lower endpoint before claiming cooperation required |
| hard | Robot start positions / headings | +/-3 cm, +/-3 degrees | Narrow-corridor feasibility and success spread |
| both | Unequal actuator capability | A separately justified hardware variant | Author design decision; reference and single-robot controls required |

Keep current friction values while validating these candidate ranges; friction was not changed. Development and evaluation seeds should remain separate, every accepted scene sealed by digest, and sampling should reject initial overlaps and impossible tether geometry.

Proposed coverage matrix: each layer x endpoints/middle of every accepted range (at least five seeds) x tensioning, straight transport, corner, goal entry and settling. Record full references and solo controls for every sample, plus reference starts at each subtask boundary. Existing 5 Hz solver snapshots are not yet a validated restoration interface. M4 must separately verify complete rope/robot state restoration and weld integrity; its prior reset attempt showed 9 cm anchor drift, so another task's restoration result is not sufficient evidence.

## 11. Release-readiness follow-up (2026-10-22)

The user explicitly authorized integration and validation of the three previously rejected offline CPU steps. `pipeline.json` now includes `stage_review --no-sheets`, `shortcuts --check` and `rerun_spread`. The expanded CPU tier passes **7/7** in `../acceptance/pipeline/20261022-220711-cpu.json`, including 55 task tests, 28 stage-review expectations and all 10 recorded shortcut expectations. Invocation is still manual; `automatic_pipeline` remains partial.

Two new bounded contact-drag probes use only existing locomotion joint targets on the unchanged sealed variants. `runs/shortcuts/base-contact-rake-release-v1` scores 0.0501 and fails target support at 5.72 s. `hard-contact-rake-release-v1` scores 0.0500 and fails target support at 4.72 s, then slip at 9.38 s. Both are non-void, have original videos, contain zero privileged/gain writes, and agree with all 800 expert evidence samples each.

Unlike the earlier keepout-off attempt, both produce measured platform contact with low rope tension. Before the first violation, contact >=20 N with each rope <=5 N occurs for 2.60 s (base) / 0.60 s (hard); largest continuous-interval net platform displacement is 5.9 / 1.4 mm. These are analysis cutoffs, not scoring changes. Neither is a valid delivery or proof that every contact route fails. Rope transients occur later, so neither full episode is labelled rope-free.

`trusted/contact_audit.py` also computes conservative nominal collision reach from the actual Go2 URDF: 1.560 / 1.594 m from a front anchor including slide/weld allowances, versus at least 1.985 m needed to reach the platform rear face. The bound assumes valid rigid articulation, slide limits and welds. It supports the rear-push limitation but does not exclude side-contact routes or physics violations; the SDK still has no detach operation.

The complete local report, original-video review template (unsigned), two sheets, conditional geometry evidence and concrete author options are in [`acceptance/release-readiness-20261022/`](../acceptance/release-readiness-20261022/README.md). **M4 is not ready for admitted release**: human stage labels/signoff, independent reproduction, scope/score/resource decisions and validated random/subtask coverage remain open. Base must not be artificially forced into a cooperation-required label. Physics, scene, scoring and monitor thresholds remain unchanged; no commit, upload or publication was performed.

## 12. Hold feedback and optional gait experiment (2026-10-23)

The ordinary velocity-command hold correction passed three hard settle_s=1.30 recordings and one default recording per sealed variant. See `../solution/README.md` section 9 and `../acceptance/hold-feedback-*` for source hashes, original videos, exact state comparisons, physics/write audits and the preserved first-run queue-lock anomaly. Identical repeats establish same-configuration reproducibility only; the historical base 4/6 and hard 10/12 perturbation grids have not been replaced by a new complete grid. Human review and independent reproduction remain pending. Admission status is unchanged.

The task CPU test list now includes the hold-feedback and optional swing-clearance tests. The gait correction remains default-disabled and uses bounded joint targets and the existing net calf-link contact-force quantity. Its first hard settle_s=1.45 video run passes with a 4.592 cm maximum stance slide. Actual foot clearance near the former failure remains only about 1 mm; intermittent unloading does not establish a clean swing. Lower body height and higher peak tension also require regression checks. See `../acceptance/swing-clearance-hard145-20261023-v1/response-audit.json`. No randomization, physical attachment hardware or shared CI changes were made. Original task loading may be explicitly initial, as already declared in task.json; unresolved physical attachment/release/reconnection, layout exploration and a same-resource public reference are separate gaps.

Proposed automatic trigger, not installed: on task controller/test/verifier edits, snapshot source hashes and run the task CPU tier; queue video reference regressions through the original one-slot queue only after CPU checks pass. Freeze task source from enqueue through completion, preserve failures, and report exact scene/configuration coverage. Physics/scene changes would require a separately approved campaign; human signoff and independent reproduction must never be auto-promoted by this trigger.

The explicitly enabled 0.015 m gait candidate subsequently fails the default hard regression at 22.70 s: go2_b FL reaches exactly 0.050015684041936376 m stance displacement. Do not round this to a pass or loosen 0.05 m. Its residual is zero throughout that loaded stance. The batch stopped before base-default or hard1.45-repeat trials; the candidate remains default-disabled. Original video, exact telemetry and source/physics/write audits are archived in `../acceptance/swing-clearance-default-hard-20261023-v1/`.

The user has separately authorized the bounded real mechanical coupling prototype on 2026-10-23. Authorization, the original proposal hash, the 28-case/1040-s budget and the preserved 84-file legacy source are in `../acceptance/coupler-prototype-20261023-v1/`. It uses a separately named candidate, keeps the preloaded-platform initial condition and all existing physical limits, and does not promote admission. The mechanical baseline keeps the gait residual disabled; its evidence must not be mixed with legacy welded towing results.

## 13. Separate coupler fixture and release inventory

`solution/coupler_v1/campaign.py` reserves each bounded case before invoking the original queue with its default single slot. It freezes task hashes and mtimes, preserves failed attempts, enforces the geometry/case/time limits and records original video. Its CPU geometry/audit/budget tests are in the existing task CPU test list; they start no simulator. Mechanical cases are not automatically added to the ordinary pipeline.

`centre50-v1-03` physically captured, retained 50 N and released, but **failed strict hardware travel**: actual maximum 0.040029656141996384 m exceeds 0.040 m. Its original checker incorrectly allowed 1 mm tolerance. The pass claim is withdrawn; original result, 4000 state samples and 401 video frames are preserved, with `cases/centre50-v1-03/strict-boundary-correction.json` documenting the correction. No forbidden writes or parameter changes were observed. Subsequent ordinary target margin is 0.039 m; actual travel, force and speed are checked without tolerance. The first two instrumentation failures and fourth pre-queue cancellation remain fully charged. The fixture constrains five other eye/carriage DOFs and adds .500 kg fixture mass. Free-rope/Go2 docking, full transport, a 300 N rating and real-material strength remain unvalidated. AI observations do not supply human acceptance.

Further review of 03 found only nine complete control intervals (0.18 s) between the first low sensor reading and opening, although physical load had been low for over 0.2 s. The controller now requires ten complete intervals / eleven consecutive low readings using integer control indices. The declared 10 N / 0.2 s interlock is unchanged. Case 05 failed at zero steps in Windows LLVM initialization; case 06 was cancelled before queue acquisition for this timing repair. Both remain fully charged and provide no mechanical result.

`centre50-v1-07` passes the corrected strict 50 N fixture check: 4000 states, 401 fully decoded original frames, capture at 8.605 s and release at 16.995 s. Peak actual q is 0.039294276386499405 m, force 0.5095199346542358 N and speed 0.021623509004712105 m/s. Complete low-load dwell, loaded-open rejection, gain/limit readback, unchanged source/parameters and zero forbidden writes were independently audited. This is a fixture result only; 03 remains failed and human acceptance remains pending.

`../task.toml` inventories the real candidate version and required generator/layers/subtasks/stages/evaluation/reference sections. The old two sealed mass/corridor variants do not establish three R9 tool layers; randomisation, independent subtask starts, a same-resource full reference and current all-tier acceptance remain incomplete. The original preloaded cargo, valid-solo-route credit and 5 cm limit are retained. Previously authorized CPU integration and the bounded coupler/sensor design are recorded as resolved authorizations in `../admission.json`; incomplete implementation and genuinely unresolved resource/score/R9 decisions remain visible. No admission gate is promoted by this metadata.
