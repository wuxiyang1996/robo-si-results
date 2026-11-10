# G1 工具辅助桌面装配

**项目状态：已完成。** 用户于 2026-10-24 确认按[已发布的第一层参考范围](../../infra/tabletop-release/README.md)结项（8/8 场景、发布快照流水线 14/14）。历史三层 24/24 作为补充证据保留；下述人工验收、独立复现及旧证据引用同步作为后续事项，不阻塞本范围的完成标记。

选定的升级任务见 [按参考图装配齿轮机构并验转](../g1_gear_assembly/README.md)：真实 CAD 齿轮、底座、开窗上盖，七步图文指令，最后握持拨杆验证三轮真实传动。另保留 [三层置物架方案](../g1_reference_assembly/README.md)。本页保留套筒与顶盖基线及其已验证专家轨迹。

**Category:** Tool-assisted Assembly · **Embodiment:** Humanoid (Unitree G1) · **Task ID:** `g1_tabletop_assembly`

![Genesis 桌面装配场景](media/scene.png)

任务链为：**扶平倾斜夹具 → 放入支撑工具并松手稳定 0.5 秒 → 插入套筒并松手稳定 0.5 秒 → 插入顶盖 → 全部脱离机器人接触，保持 2 秒**。

夹具是绕 y 轴转动的无动力铰接平台，初始倾角为 0.28 rad。定位柱随平台一起倾斜，黄色 `brace` 支撑块必须放到平台右侧下方，持续承受平台载荷。支撑块留在原位时，平台才能保持要求的水平装配姿态。套筒提供顶盖的承托面；提前插入套筒或顶盖会终止任务，最终评分也会重新检查整条承托链。

当前闭环控制器 `closed_loop:run` 已通过冻结的 **24/24** 个场景（三层各五个种子、两个边界、一个名义场景）。三层独立物理回放和 sandbox 回放均通过；每层三次全新运行均成功，阶段时间波动为 0。见[自动证据审计](acceptance/release_20261022/automatic_audit_candidate20.json)与[人工复核材料](acceptance/release_20261022/review_candidate20/index.html)。最终全层流水线、干扰工具物理排除、人工标注和签审、第二人独立复现仍须满足，`admitted=false`。默认固定骨盆，参考读取物体真值；不声称视觉或自由站立控制已验证。

## 运行

从 `robo-si/` 根目录执行，默认使用 CPU：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop.run --task assembly --steps 150 --image humanoid/g1_tabletop_assembly/media/scene.png --report humanoid/g1_tabletop_assembly/validation/no_op.json
```

这会保持初始关节目标，运行 150 个控制步，即 3 秒模拟时间，并保存场景图与[空跑报告](validation/no_op.json)。空跑预期得 0 分，只检查场景与物理步进，不执行装配。添加 `--viewer` 可打开交互窗口；`--actions actions.json` 可读取每帧 43 维的关节动作。共享运行入口见 [`g1_tabletop/run.py`](../g1_tabletop/run.py)。

机器人复用仓库内带 Dex3 手的 G1 资产。物理频率为 200 Hz，控制频率为 50 Hz；每个物理步执行显式 PD，并按机器人资产中的限值裁剪施加力矩。动作目标为 `default_q + 0.25 * action`，再裁剪到关节限位内。工具、套筒和顶盖始终通过刚体接触运动，无焊接、吸附、抓取绑定或执行中的物体瞬移。

## 专家轨迹

当前三层示范见[数据清单](solution/datasets/expert_layers_release_20261023/manifest.json)，共 17,526 个控制步，均来自正常生成初始状态，无录制动作前缀。状态逐项与封存日志一致，目标角按实际 float32 servo 转换精确匹配；每层有独立物理与 sandbox 回放。新运行示例：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop.sandbox.qualification assembly --scene humanoid/g1_tabletop_assembly/acceptance/release_20261022/coverage_release_candidate_20/layer1_nominal/scene.json --policy closed_loop:run --out humanoid/g1_tabletop_assembly/solution/recordings/new_reference --video
```

六个释放态子目标按统一协议通过：先执行记录后缀，尚未终止时保持最后关节目标最多 1 秒，仍受原 120 秒预算和 2 秒最终保持条件限制。三个 stage-1 不需追加；三个 stage-2 均仅追加 0.005 秒。原严格后缀的三个失败保存在 [followups](acceptance/release_20261022/followups_release_candidate_20_v2/summary.json)，补充结果与真实物理录像见[静置验证](acceptance/release_20261022/subgoals_settle_candidate20/summary.json)。恢复不含求解器 warm-start 缓存，不声称逐位连续。

以下 `expert_001` 是保留的历史名义参考：

[`expert_001`](solution/recordings/expert_001/summary.json) 从默认场景完成 **支撑工具就位 → 安装套筒 → 安装顶盖 → 松手保持 2 秒**，共 **115.67 秒、5784 个控制步**，阶段序列为 `0 → 1 → 2 → 3`，最终得分为 1。审计未发现机器人或物体状态写入；支撑工具始终保留并实际承重。

- [完整视频](solution/recordings/expert_001/video.mp4)
- [专家动作与状态 NPZ](solution/recordings/expert_001/trajectory.npz)
- [逐步状态与接触记录](solution/recordings/expert_001/trace.jsonl)
- [独立回放报告](solution/recordings/expert_001/replay/replay_report.json)：仅重放保存的关节目标，完整成功，阶段一致，最终四个物体的位置与姿态误差均为 0。
- [最终装配场景](solution/recordings/expert_001/final.png)与[控制器及数据格式说明](solution/README.md)。

专家动作通过 `env.step_targets(target_q)` 输入绝对关节角，NPZ 同时记录实际关节状态与时间。重新运行完整控制器并录像、独立回放：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_assembly.solution.run_expert --prefix humanoid/g1_tabletop_assembly/solution/tool_runs/direct_09 --policy expert:parts_after_support --output humanoid/g1_tabletop_assembly/solution/recordings/expert_002 --video --replay
```

仅回放现有专家动作：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_assembly.solution.recording humanoid/g1_tabletop_assembly/solution/recordings/expert_001/trajectory.npz --output humanoid/g1_tabletop_assembly/solution/recordings/expert_001_recheck
```

输出目录必须是新目录。开发实验中的失败轨迹和预置夹具测试保留在各 `*_runs/` 目录，不能作为完整成功示范使用。

## 场景与阶段

单位为米；世界坐标 z 向上，四元数顺序为 wxyz。

| 物体 | 默认几何与位置 |
|---|---|
| 桌面 | 高 0.74，尺寸 0.70 × 1.15 × 0.05，中心 xy=(0.55, 0) |
| 铰接平台 | 尺寸 0.36 × 0.20 × 0.025，转轴中心 (0.46, 0, 0.815) |
| 定位柱 | 截面 0.036 × 0.024，高 0.12；平台水平时中心 xy=(0.50, 0)，柱底 z=0.8275 |
| 支撑工具 `brace` | 0.07 × 0.18 × 0.0625；目标中心 (0.59, 0, 0.77125) |
| 套筒 `sleeve` | 外廓 0.12 × 0.10，高 0.045；贯通孔 0.044 × 0.032；目标中心 z=0.85 |
| 顶盖 `cap` | 外廓 0.10 × 0.08，高 0.025；贯通孔 0.044 × 0.032；目标中心 z=0.885 |

套筒和顶盖各由四面实体墙组成一个刚体，中央保留真实贯通孔。孔与柱均为矩形，绕竖直方向旋转 180° 可以配合，旋转 90° 无法满足装配检查。

| 阶段 | 完成条件 | 对后续阶段的作用 |
|---|---|---|
| 0：支撑夹具 | 工具到达平台右侧下方，受桌面承托并向上托住平台；工具与平台脱离机器人接触，水平低速稳定 0.5 秒 | 建立可用的装配基准面，允许插入套筒 |
| 1：安装套筒 | 套筒套住定位柱并落到平台上，姿态与高度正确、低速且脱离机器人接触，连续 0.5 秒 | 建立顶盖的承托面，允许插入顶盖 |
| 2：安装顶盖并释放 | 顶盖套住柱并落在套筒上；工具支承、套筒与顶盖位置及接触全部正确；连续保持 2 秒 | 完整成功，进入阶段 3 |

工具是最终结构的一部分，装配后仍须保留。每帧都检查当前支承和零件状态；拆开套筒或重新接触零件会清空最终保持时间，历史阶段记录不能替代当前装配状态。

## 接触判定与失败

评分读取模拟器提供的物体位姿、线速度、角速度和接触力，不能用策略声明替代。必须满足的载荷路径为：

```text
桌面 → 支撑工具 → 铰接平台 → 套筒 → 顶盖
```

支撑工具收到桌面的向上合力须大于 0.05 N，工具对平台的向上承托力也须大于 0.05 N；同时检查平台收到工具的向上合力。套筒必须收到平台、顶盖必须收到套筒各大于 0.05 N 的向上合力。仅有侧面碰撞、接触布尔值或错误物体的承托均不能通过。

释放要求 `hand_contact=false` 且 `robot_contact=false`，因此手腕、前臂或其他机器人部位仍在托住零件时不能计为释放。稳定速度上限为 0.025 m/s 和 0.15 rad/s，平台允许姿态偏差为 3°，零件倾斜上限为 5°；还须满足孔柱几何配合：相对定位柱每轴位置误差不超过 0.005 m（孔柱单边间隙 0.004 加接触余量 0.001，由几何参数推出，只判断零件套在柱上，不考对中精度；2026-10-21 之前为 0.004 m，旧录制回放仍按旧值），高度误差不超过 0.004 m。

以下情况终止并得 0 分：

- 工具支承阶段完成前插入套筒，或套筒稳定阶段完成前插入顶盖。
- 已建立的工具支承资格连续失效 0.1 秒，例如工具撤走、平台失稳或机器人继续代持。
- 任一可移动物体中心低于桌面 0.12 m，即默认 z < 0.62。
- 超过 120 秒，或出现缺失、非有限、格式错误的状态及不合法采样间隔。

最终稳定条件中断会立即清空 2 秒计时；工具支承失效的 0.1 秒容差不会保留这段计时。`success` 才产生 `score=1`，其他情况均为 0。`progress` 和 `stage` 仅作开发诊断。成功或失败结果会锁存，直到显式重置。

## 验证范围

[35 项评分器测试](../../tests/test_tabletop_assembly.py)覆盖阶段顺序、连续稳定时间、矩形孔方向、指定对象承托、侧接触、机器人身体接触、拆件、掉落、无效数据和超时。运行：

```powershell
../genesis_env/Scripts/python.exe -m unittest discover -s tests -p test_tabletop_assembly.py -v
```

这些是合成状态序列测试，用来验证评分规则；物理空跑报告用于检查环境运行。两者均不构成完整装配成功证据。开发接口暴露真值，隔离评测另走 [sandbox](sandbox/README.md) 的受限动作与传感器接口。

另有[物理夹具测试报告](validation/mechanism.json)：无支撑平台倾斜；放入支撑块后实际承重；套筒和顶盖通过重力与碰撞座落；撤走支撑块触发 `fixture_support_lost`。这些检查已通过。测试直接设置阶段测试物件的位置，报告明确标记 `object_pose_setters_used=true`、`robot_task_solution=false`；[装配态图片](media/fixture_test_assembled.png)展示的是该测试夹具状态，并非机器人完成轨迹。复现方法见[公共环境说明](../g1_tabletop/README.md)。

工具允许推入，不要求双手同时夹持。当前专家先将支撑块搬到夹具侧面，再用右手按压平台近端、左拇指从侧面推入支撑块；松手验收后依次抓取和安装套筒、顶盖。该默认场景策略已通过上述完整物理执行与动作回放。

任务元数据见 [`task.toml`](task.toml)，操作说明见[中文指令](instruction.zh.md)，参数及评分实现见 [`task_spec.py`](task_spec.py)，物理环境见[共享环境](../g1_tabletop/genesis_env.py)。

## 场景随机化方案

状态：2026-10-22 已实现实验生成器 [`randomization.py`](randomization.py)、三层干扰支撑块和可选身体变化，当前实现范围已通过固定 24 例物理覆盖，评分默认仍为名义场景。`--randomized` 开启实验场景，`--difficulty 1/2/3` 选择层，`--body-variation` 加入公开的身体变化。当前实验范围较下表原计划窄：零件位置变化约厘米量级、yaw ±0.03 rad、物体质量 ×0.9–1.1、摩擦 0.65–0.8、铰链阻尼 0.04–0.10；精确范围以代码的 `RANGES` 为准。下表是原计划，不能视为已经实现或验证的覆盖范围。

所有闭环候选和失败保存在 [release_20261022](acceptance/release_20261022)。当前候选 20 的[完整扫描](acceptance/release_20261022/coverage_release_candidate_20/summary.json)为 24/24；源码、场景与配置均冻结，未修改评分阈值、物理参数或力矩上限。旧候选失败保留。24 段完整的 5 Hz 记录状态可视化已生成并标识采样方式；独立物理录像另列，不能混为一类。人体参数边界试验之外的全部组合尚未认证。

| 变量 | 当前 | 随机范围 | 备注 |
|---|---|---|---|
| 零件初始位置 | 支撑块 (0.43, 0.40)，套筒 (0.43, 0.25)，顶盖 (0.43, −0.25) | 各件 x 取 0.36–0.52，\|y\| 取 0.18–0.42；每件位于夹具哪一侧随机 | 优先实现 |
| 零件 yaw（第一期） | 0 | 套筒、顶盖 ±0.5 rad；支撑块 ±0.4 rad | 孔绕竖直方向 180° 对称 |
| 零件 yaw（第二期） | — | 套筒、顶盖 ±π/2 | 需要手内调转或换手；参考专家做到后才启用 |
| 夹具转轴水平位置 | (0.46, 0) | x ±0.03，y ±0.06 | 支撑块目标点随转轴平移（转轴 x + 0.13） |
| 初始倾角 | 0.28 rad | 0.20–0.32 rad | |
| 转轴高度、支撑块高度 | 0.075 / 0.0625 | 转轴高度 0.065–0.085；支撑块高度 = 转轴高度 − 0.0125 | 平台水平的约束，见 `TaskConfig.__post_init__` |
| 支撑块底面 | 0.07 × 0.18 | 各边 ±10% | |
| 套筒、顶盖外形 | 外廓见上表；高 0.045 / 0.025 | 外廓 ±10%，高度 ±15% | 孔 0.044 × 0.032 与柱 0.036 × 0.024 不变，保持 8 mm 间隙，不做精度难度 |
| 物性 | 零件 0.35 / 0.20 / 0.12 kg，摩擦 0.7；平台 1.2 kg；铰链阻尼 0.06 | 零件质量 ×0.8–1.25，摩擦 0.5–0.9；平台 1.0–1.5 kg；阻尼 0.04–0.10 | 压平平台所需的力可由手臂关节力矩读出 |
| 身体参数 | 固定 | 手臂力矩上限 ×0.85–1.0（公开范围）；初始关节目标 ±0.05 rad | 与汉诺塔相同 |
| 下沉方向（第二期） | x 正向一侧（离机器人较远的一侧）下沉 | 夹具绕竖直轴转 90°，下沉侧取远侧、左侧或右侧之一 | 评分要改在夹具坐标系中计算，指令"平台右侧下方"改为"平台下沉一侧下方" |

拒绝规则：零件与零件、零件与夹具摆动范围之间的间隙至少 0.03；零件完整落在桌面内；套筒高 + 顶盖高 < 柱高；全部零件及目标点在参考专家双手可达范围内（范围由实测给出）。

不随机：判定阈值、孔与柱截面、桌高、零件颜色（指令按颜色指认零件）、机器人固定位置、求解器设置。

三层难度已实现为逐层添加物体：第 2 层加入远处 8 kg 支撑块，第 3 层再加入过矮与过高的支撑块；同一种子保持必要零件相同。各层完整参考已通过；新增物体的物理排除证据和人工捷径复核尚未齐备，不能据此宣称工具辨识验收已通过。

实现步骤：

1. 专家改为闭环：工具阶段替换开环前缀，零件阶段读取实际位姿与 yaw。
2. `TaskConfig` 增加零件初始位姿、转轴、倾角、尺寸、物性字段，`scene_objects` 从配置读取，`brace_goal_xy` 由转轴推出；`sandbox/trusted/scenarios.py` 实现生成器与范围校验，并保留名义场景，用于回放 `expert_001`。
3. 参考专家按预先固定的角点与随机样本实测，保留全部失败，修复控制器后重新跑完整清单；不能以缩小范围替代本轮覆盖。
4. 在抽样场景上重录参考轨迹，更新准入记录与 `task.toml`。第二期（大角度 yaw、下沉方向）在第一期通过后再做。

## 隔离评测沙箱

任务已接入仓库统一沙箱运行时（`infra/sandbox/`），说明见 [sandbox/README.md](sandbox/README.md)，准入记录见 [admission.json](admission.json)。agent 只能读取机器人自身传感器并发送 43 维关节目标（servo 模式，环境固定增益），评分从可信侧状态日志回放本任务的 `Evaluator` 得出，与环境实时评分器和独立终态检查交叉核对；得分仍为二值。`expert_001` 经沙箱命令通道回放、以及专家黑盒重跑均成功，与原录制逐位一致。随机化器已实现；新默认控制器的完整覆盖已通过；最终流水线、工具排除、人工标注、视频签审和第二人复现尚待完成，因此仍为 `admitted = false`。
