# H2 隔离评测沙箱（G1 手推车辅助重物搬运）

2026-10-22 发布准备：将承载推运中的横向居中误差改为相对车道方向计算后，默认
rails 场景、真实硬件力矩上限下的三次同源重复全部成功：83.22、81.42、84.80 s，
均为 1.0 分、非 VOID、无报警或状态写入。完整 200 Hz 原始物理输入的离线回放
与现场结果一致。见 [重复统计](../acceptance/release-20261022/centering_repeats.json)
和 [未签署审核包](../acceptance/release-20261022/review-1/index.html)：包含三份原始录像、
阶段帧和评分时间线；当前审计正例 3/3、负例 5/5、攻击例 4/4。

早先收手修正前后的 1/3、2/3 结果分别保留在
[历史复测证据](../acceptance/resume-20261022/current_repeats.json)，不与本批合并。
历史 `rails-fin2` 的物理失败和 50 Hz / 200 Hz 分歧仍明确保留。默认有效性检查仍报告
该分歧；流水线用 `--known-legacy-regressions` 核对这份精确哈希的旧记录仍失败、仍有
原来的警告，并将它作为历史采样负回归，绝不计入正例验收。未恢复缺失数据或放宽判分。
随机范围、三层设计、子任务、人工标注和独立复现仍未完成；`admitted=false`。

本目录是 H2 在仓库统一沙箱运行时 `infra/sandbox/` 上的任务专属部分（结构照 H4/H3，契约见
`infra/sandbox/ONBOARDING.md`）。只用 Genesis 后端；世界直接包装任务自己的
`genesis_env.G1CartAssistedTransportGenesis`，场景、材料、摩擦、求解器、轮子与滚轮均不改动。
准入记录：`../admission.json`（`python -m infra.sandbox.records` 校验）。

## 1. 目录

```
launch.py                 SandboxTask + H2 选项（--scene、--effort-limits）-> infra.sandbox.launcher.launch()
instruction.md            智能体看到的任务说明（草稿，见第 9 节待作者决定）
agent_sdk/README.md       公开 bundle 里的智能体指南；examples/hello_robot.py、examples/noop.py
trusted/                  永不进入 bundle
  scenarios.py            Scenario（mode、episodes、scene、task_config、sensors、预算、effort_limits），两个场景预设
  world.py                SandboxWorld(CommandChannel)：任务环境原样构建；_apply = 一个 50 Hz 控制步（4 个物理步，每步后 TaskCore.update）
  sensors.py              infra.sandbox.sensors.AppliedEffortSensors（tau_est = 实际施加力矩）
  statelog.py             每控制步一行（标准字段 + 推车车轮、托举力、碰撞力、TaskCore 标志）；meta 里有任务几何
  scoring.py              阶段谓词（全额判据直接调用任务自己的 TaskCore）、任务评估器回放 evaluate()
  monitors.py             共享监控套件 + H2 profile（平地、固定碰撞体、货架排、房间边界）
  verifier.py             verify_episode / TaskVerifier / verify_run
  server.py               run_worker(...)
  record_reference.py     把现有专家（solution/floor_push/run_grasp_push.py）作为黑盒录进沙箱日志格式并判分
  record_shortcut.py      原场景、真实上限下录制现有地面推箱控制器的捷径尝试；不作为参考正例
  exploits.py             物理攻击录制（同一录制器，脚本只做一个攻击：teleport / mass / jitter），检验验证器作废或扣分
  validity.py             验证器有效性：只读重判全部录制（正例、诊断、负例、攻击），写 report.md / review_record.json
tests/                    test_static / test_scoring / test_monitors，agents/escape_probes.py、agents/hold_agent.py
runs/                     运行目录（reference/ 为参考录制）
```

## 2. 场景：两个封存预设（H2 没有随机化）

`task_spec.TaskConfig` 是一个固定场景，环境每次从同一初始状态开始；评分模式（grade）的每个 episode 都相同
（`randomization` 字段写明）。在建沙箱期间任务定义被另一会话改动了（`task_spec.py` 2026-10-21 01:37 默认改为
rails 码头，20 kg、摩擦 0.5 的货箱；02:08 又加了 `RAIL_RAISE`），所以场景按内容封存：

| `--scene` | 内容 | 专家 |
|---|---|---|
| `default`（启动器默认） | 封存时任务的 `TaskConfig()`（当前为 rails 码头） | 当前横向居中修订 3/3 成功；见本页开头的同源记录 |
| `wedge` | 冻结在 `trusted/scenarios.py` 的 `WEDGE`：cart-v109/v112/v114 通过时的场景（固定楔形坡、漏斗边、导向路缘；10 kg、摩擦 0.12；圆形把手杆、无车道导轨、车轮 frictionloss 0.01、Genesis 默认车轮 armature 0.1），不影响 wedge 场景的字段取 2026-10-21 的默认值 | run_grasp_push.py，见第 6 节 |

02:52-02:58 `TaskConfig` 又新增了 `lane_guides`、`guide_north_x`、`box_handle_shape`、`wheel_armature` 四个字段，并把 `wheel_frictionloss` 默认改为 0.035：冻结的 `WEDGE` 一度无法往返，worker 按设计拒绝构建（第一次 wedge 开发 smoke 即因此失败）；之后按 task_spec.py 对“录制通过时”的注释补上这四个字段（无导轨、bar、0.1）。两次参考录制是在这些字段出现之前做的，其 meta 里的配置是旧版 `WEDGE`（物理上相同）。

封存的配置必须原样通过任务的 `TaskConfig` 往返（无未知/缺失/被改写的字段）且等于其预设，否则 worker 拒绝；
任务改动之后不会被悄悄构建。模块常量（例如 `RAIL_RAISE`）不在 `TaskConfig` 里，靠 meta 的 `source_hashes`
记录，验证器对录制后改动过的源文件打 `recorded_with_other_sources` 标志（不作废）。

## 3. 运行（仓库根目录，模拟器命令走 GPU 队列）

```powershell
$Q = "C:/Users/wuxiy/AppData/Local/Temp/claude/d--rsi-vla/2f795ddc-4e2e-4209-82f7-00dd0d1f3417/scratchpad/unify/tools/gpu_queue.py"
$PY = "D:\rsi_vla\genesis_env\Scripts\python.exe"
# 开发（进程隔离）
& $PY $Q -- $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.launch --mode dev --isolation process --no-video --name <run> --agent-dir humanoid/g1_cart_assisted_transport/sandbox/agent_sdk/examples -- python hello_robot.py
# 评测 / 评分（Docker 容器）
& $PY $Q -- $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.launch --mode eval --no-video --agent-dir <delivery> -- python solve.py
& $PY $Q -- $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.launch --mode grade --episodes 2 --no-video --agent-dir <delivery> -- python solve.py
# 参考专家录制（智能体的真实 G1 扭矩上限；--scene default = rails，wedge = 冻结场景）与重判
& $PY $Q -- $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.trusted.record_reference --out humanoid/g1_cart_assisted_transport/sandbox/runs/reference/<name> --scene default --effort-limits hardware
& $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.trusted.record_reference --judge humanoid/g1_cart_assisted_transport/sandbox/runs/reference/<name>
# 物理攻击录制（teleport / mass / jitter）与验证器有效性报告（只读，不改录制）
& $PY $Q -- $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.trusted.exploits --kind teleport --out humanoid/g1_cart_assisted_transport/sandbox/runs/exploits/teleport-v1
& $PY -X utf8 -m humanoid.g1_cart_assisted_transport.sandbox.trusted.validity --out humanoid/g1_cart_assisted_transport/sandbox/runs/validation/<name> --sheets
# 自动检查流水线（cpu 层；--tier all 含 gpu / container，需设 INFRA_GPU_QUEUE）
& $PY -X utf8 -m infra.sandbox.pipeline humanoid/g1_cart_assisted_transport --tier cpu
# 单元测试
& $PY -X utf8 -m unittest humanoid.g1_cart_assisted_transport.sandbox.tests.test_static humanoid.g1_cart_assisted_transport.sandbox.tests.test_scoring humanoid.g1_cart_assisted_transport.sandbox.tests.test_monitors
```

## 4. 接口

* 只有共享的 G1 LowCmd 通道（`infra.sandbox.world.CommandChannel`）：模式 0 电机律
  `tau = tau_ff + kp (q* - q) + kd (dq* - dq)`，腿部 12 个关节按任务的 DC 电机包络（`robot.dc_motor_torque`）限幅；
  模式 1 为仿真器隐式 PD。用任务自己的增益（腿模式 0、kp/kd 取 robot.py，其余模式 1）时，一个命令与
  `env.step(action)` 的物理完全相同；每个物理步后运行任务的 `TaskCore.update(env.state())`（与 env.step 一致）。
* 扭矩上限为真实 G1：`min(robot.py effort, MJCF actuatorfrcrange)`（`infra.sandbox.world.hardware_effort`），
  同时作用于电机律限幅和伺服的 force range。腿和腰不变；肩、肘、腕滚 25 N m，腕俯仰/偏航 5 N m，Dex3 手指
  1.4-2.45 N m（robot.py 是 300 N m）。`--effort-limits task` 仅作诊断，判决里写 `diagnostic: true`。
* 传感器只有机载：`infra.sandbox.sensors.AppliedEffortSensors`（proprio、头部 RGB-D、MID-360 仿真、触觉、足底力）。
* episode 在 `finish()` / `declare_infeasible()` / 时间预算（180 s）/ 任务失败时结束。任务失败即 TaskCore 的条件：
  骨盆低于 0.42 m、躯干倾斜超过 60°、推车翻倒、货箱低于地面、机器人/货箱/推车出房间、非足部接触力超过 800 N；
  世界每个控制步自己检查（TaskCore 成功后会停止更新）。成功不结束 episode，验证器要求交付在结束时仍成立。

## 5. 评分（`trusted/scoring.py`，只读可信日志）

全额判据来自任务自己的代码：每一行日志喂给一个新的 `task_spec.TaskCore`（批量，一行一个环境），得到每步的
任务 on-cart 判据（货箱底面在车板范围内、最低角在车板平面、推车承托至少一半重量、推车直立）、失败条件和
交付判据（8 个角都在目标方形内、静止、直立、在车上）。部分得分是连续几何量。

| 阶段 | 模式 | 权重 | 数值 |
|---|---|---|---|
| `crate_pushed` | once | 0.05 | 机器人接触货箱（>= 5 N）累计 0.5 s 且货箱移动 >= 5 cm |
| `cargo_loaded` | once | 0.25 | 0.5 x 货箱底面落在车板上的最大比例（机器人接触后）；任务 on-cart 判据成立过且货箱 riding 0.5 s 时为 1 |
| `through_passage_1` | once | 0.15 | 0.5 x 装载后货箱从推车停放处到越过第一排货架的进度；货箱在车上、整体越过货架远侧面 0.5 s 时为 1 |
| `through_passage_2` | once | 0.20 | 0.5 x 沿路线（第一排东侧 -> 两排之间向北 -> 向东到第二排远侧面）的进度；在车上整体越过第二排 0.5 s 时为 1 |
| `delivered` | live | 0.35 | 在车上时 0.5 x 货箱底面在目标方形内的比例；任务交付判据连续成立满任务的 2 s 驻留时为 1 |

`riding`（运输阶段用）：任务 on-cart 的几何部分 + 地面不承重（< 10 % 重量）+ 推车在过去 1 s 内平均承托 >= 25 %
重量。原因：推车柄被拳头推着时，拳头承担了一部分重量，推车对货箱的竖直接触力在 0 到 3.4 倍重量之间逐步跳动；
任务的瞬时判据（每个物理步 > 50 %）在推的过程中只有 51-62 % 的步成立（wedge-r1），若直接要求它连续 0.5 s，
装载要等到推完才算（wedge-r1 第一版：装载 25.6 s，任务核心 14.3 s）。1 s 平均份额在两次录制的推送中最低 0.36（r1）。
交付保持任务自己的瞬时判据（那时货箱静止）。

所有阶段只在机器人未失败时计分。分数 = 随时间的 sum(权重 x 值) 的峰值；成功（0/1）= 结束时交付仍成立、整条链
（装载、通道 1、通道 2）完成、worker 里 200 Hz 的任务核心自己的 success 标志已置位、且未失败。验证器另外把任务
评估器在日志上回放（`scoring.evaluate`：一个 TaskCore，每个控制步 4 次更新，即物理步之间零阶保持），
阶段判据、实时任务核心、回放三者不一致时打 `success_disagreement` 标志。监控器窗口内首次达到的阶段水平
之后也不计（与 H4 相同的窗口语义）。

## 6. 参考专家录制（`trusted/record_reference.py`）

做法照 H4：用 runpy 原样运行 `solution/floor_push/run_grasp_push.py --out <out>/oracle --video`（cart-v109/v112
的命令），从外部挂钩 `G1CartAssistedTransportGenesis`：每个 `env.step`（一个控制步）写一行日志；第一控制步后对
Genesis 实体/link 的任何位姿、状态、属性、限值 setter 调用都记录（期望 0），增益超出命令通道上界即作废。
从外部提供的只有封存场景：专家用 `TaskConfig(**kw)` 取任务默认值，而默认值在它的通过之后改成了 rails 码头，
所以录制器把 `run_cart_push.TaskConfig` 换成封存场景的配置（默认 `--scene wedge`），并在专家构建的环境配置
与封存场景不一致时拒绝录制。专家代码文件的摘要与副本存在 `record.json` / `expert_sources/`（另一会话正在
修改专家：wedge-r1 用的 run_grasp_push.py 摘要 c9cddd01，wedge-r2 用的是 01:55 版 ae4a649e）。

| 录制 | 扭矩上限 | 专家自己的结果 | 沙箱判决 | 阶段时间（s）：pushed / loaded / passage 1 / passage 2 / delivered | 任务核心（200 Hz） / 回放评估器 |
|---|---|---|---|---|---|
| `runs/reference/wedge-r1` | robot.py（与 cart-v109/v112 相同） | task_success 87.96 s（腿结束 14.5/24.1/40.5/80.2） | 成功，1.0，无告警，0 次特权写 | 6.94 / 14.78 / 19.84 / 75.22 / 87.86 | loaded 14.30 / 14.34；success 87.98 / 87.86 |
| `runs/reference/wedge-r2` | robot.py | task_success 71.57 s（腿结束 13.3/22.8/39.6/63.6） | 成功，1.0，无告警，0 次特权写 | 6.08 / 13.74 / 18.70 / 58.74 / 71.44 | loaded 13.26 / 13.28；success 71.58 / 71.44 |
| `runs/reference/wedge-hw1` | 真实 G1（诊断，构建时施加） | execution_exception: walk timeout（41 s，停在第一个路点前 7.5 cm） | 失败，0，不作废 | 全部未达 | 未装载 |

两次按原命令的重录都成功，判决、实时任务核心与回放评估器一致；阶段时间与专家自己的时间线一致（装载在专家
完成 leg 0 后 0.2-0.4 s，第二通道在最后一段推送中，交付比任务核心早 0.12-0.14 s：50 Hz 的驻留在物理步之间取零阶保持）。
专家在 robot.py 的 300 N m 手臂限值下运行（与它的通过一致），而智能体拿到的是真实 G1 限值；在真实限值下专家
走不到货箱（1 次诊断）。所以 H2 目前**没有**在智能体限值下的参考解。

## 7. 监控器与校准（`trusted/monitors.py`，h2-monitors/1）

共享监控套件，阈值全部沿用共享默认值（无改动）。场景几何：平地（z = 0）对货箱和车板；所有固定盒碰撞体（墙、
货架板与立柱、存放托盘与箱、装载托架、wedge 码头的路缘和漏斗边）对货箱和车板；货架排作为实心包络只对货箱
（货箱比板间距高，薄板的最小穿透深度最多 2.5 cm，测不出穿越）；货箱对车板；房间边界为 TaskCore 的边界。
H2 的阶段在构造上不会尖峰（驻留、门控）也不会乱序（每个阶段以前一阶段为前提），progress_spike 只做接线测试。
只在 wedge 场景（有已证明的解）上，宣告不可行会被标记。

| 指标 | 参考录制最大值（r1 / r2 / hw1） | no-op / hello / 探针最大值 | 阈值（共享默认） |
|---|---|---|---|
| 物体速度 m/s | 0.50 / 0.69 / 0.12 | 0.12 | 9（窗口） / 15（作废） |
| 无功能量 J | 1.06 / 0.53 / 0.01 | 0.01 | 6（窗口） / 60（作废） |
| 手臂抖动 | 1.86 / 2.27 / 1.96 | 0.02 | 3.0（窗口） |
| 腿/腰饱和 s | 0.28 / 0.26 / 0.06 | 0 | 3（窗口） |
| 穿透 m（盒 / 地面） | 0.002 / 0.0006（三次录制） | 0 | 0.03（窗口） / 0.10（作废） |

合成的利用场景（`tests/test_monitors.py`）全部触发：瞬移作废、推车被踢飞（12 m/s 窗口、17 m/s 作废）、货箱凭空
升高（0.2 m 窗口、1.5 m 作废）、货箱沉入地面/车板、货箱穿过货架排、推车穿墙出房间（作废）、手臂抖动、手指抖动
（腿部步态不触发）、腿饱和、顶关节限位、特权写与超界增益（作废）、伪造的进度尖峰。

## 8. 验证清单（ONBOARDING 第 6 节，2026-10-21）

| 检查 | 运行目录 | 结果 |
|---|---|---|
| 单元测试 | `tests/` | 56 个全部通过（test_static 10、test_scoring 19、test_monitors 27），约 55 s |
| 开发 smoke（进程隔离，default 场景） | `runs/dev-hello` | hello_robot 读完全部传感器、保持 2 s；非 VOID，0 分，请求日志链 ok |
| 开发 smoke（进程隔离，wedge 场景） | `runs/dev-hello-wedge` | 冻结 wedge 场景（含 02:52 新字段）构建成功；hold_agent 保持 4 s；非 VOID，0 分，链 ok（第一次尝试因 TaskConfig 新增字段被按设计拒绝，见第 2 节） |
| 开发 smoke（采用 2026-10-21 运行时更新之后） | `runs/dev-hello-infra2` | hello_robot；非 VOID，0 分 |
| 容器 eval hello（default） | `runs/eval-hello` | 非 VOID，0 分，1 次连接、2 次 observe、1 次 command，链 ok（7 条） |
| 逃逸探针（容器） | `runs/escape` | 44/44 探针符合预期（力矩 1e6 截到上限，max_ratio 1.0000；增益 1e9 截断），23 次接口违规，VOID |
| 评分 `--episodes 2` no-op（容器） | `runs/grade-noop` | 2 个 episode 各 1 次连接，均 0 分，非 VOID，链 ok（15 条） |
| 参考录制 | `runs/reference/wedge-r1`、`wedge-r2`、`wedge-hw1` | 见第 6 节：2/2 成功（robot.py 限值），真实限值诊断失败 |
| 准入记录 | `../admission.json` | `python -m infra.sandbox.records` 无问题 |

## 9. 剩余缺口与待作者决定

* **任务定义仍在变**：建沙箱期间默认场景改成了 rails 码头（且又改了一次）。沙箱两个场景都能封存，但准入的是哪一个
  要作者定；rails 场景还没有专家。改场景后要重录参考。
* **智能体扭矩限值下没有参考解**：专家只在 robot.py 的 300 N m 手臂限值下通过；真实 G1 限值下 1 次诊断在第一个
  路点前卡住（`wedge-hw1`）。
* **instruction.md 是草稿**：说明了“货箱只有放在推车上才算交付”（评分器自 2026-10-20 起要求），没有给策略提示；
  这削弱了“自己发现推车”的意图，需作者确认措辞。
* **riding 判据**（1 s 平均承托 >= 25 % 重量）是为推送时拳头承担部分重量而设，阈值只在 2 次录制上校准。
* 只有 2 个正例：重复性（>= 3 次）、视频人工复核、阶段人工标注、捷径审计、独立复现、真实利用录制均未做。
* 每次录制都带 `recorded_with_other_sources` 标志（之后 task_spec.py / assets.py / visual_assets.py 被另一会话改过），
  不作废，重判用当前代码。

## 10. 共享运行时

未新增 infra 模块，任务专属的东西都在本目录。已采用 2026-10-21 的运行时更新：`_end_episode` 先写 `episode_over`、
封存日志、再 `_check_params`；`MODES = (0, 1)`；batch 轴无关的 `world_params` 等（H2 场景本来就是 batched，结果不变）。
给运行时的建议（未自行修改）：

* `statelog.infra_hashes()` 对 `infra/sandbox/*.py` 全部取摘要，其他任务新加的模块（`mobile_sensors.py`、
  `sensors_legged.py`）会进入每个任务的 `source_hashes`，改动后造成无关的 `recorded_with_other_sources`；H2 的验证器
  只看录制时已有、之后被改或删除的文件。建议运行时只对任务实际导入的模块取摘要。
* `statelog.world_params` 只摘要 `links_mass` 和 `geoms_friction_ratio`；`set_friction`（几何体摩擦本身）、armature、
  frictionloss、force range 的改动不进摘要。专家录制器的 setter 监视能看到这些，智能体运行时没有通道可改，但摘要可以更全。
* Genesis 的接触力逐步噪声很大（推车对货箱的竖直力在推动中 0-3.4 倍重量跳动），基于瞬时接触力的谓词需要时间平均；
  可以考虑在 `infra.sandbox.monitors` 或 statelog 里提供一个共享的 trailing-mean 工具。
