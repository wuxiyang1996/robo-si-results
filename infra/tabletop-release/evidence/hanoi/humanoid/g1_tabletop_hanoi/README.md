# G1 桌面汉诺塔

任务 ID：`g1_tabletop_hanoi`；类别：`Sequential Manipulation`。控制带 Dex3 手的 Unitree G1，把叠在起始杆上的整叠圆盘搬到目标杆（绿色底座），第三根杆用于周转；一次只能移动一个顶盘，大盘不能放在小盘上。默认 3 盘，可配置为 4 或 5 盘。起始杆、目标杆、杆位、杆高、盘径、颜色和物性每回合随机，见[场景随机化方案](#场景随机化方案)；名义场景为 A 杆到 C 杆。

当前发布候选的[3–5 盘数据清单](solution/datasets/expert_3to5_release_20261023/manifest.json)包含 31,004 个 50 Hz 控制步，三条均通过同环境独立物理回放和 sandbox 命令回放。完整冻结扫描为 **58/58**，每个盘数三次全新运行的阶段时间波动为 0。见[自动审计](acceptance/release_20261022/automatic_audit_swept_thumb_v2.json)与[人工复核包](acceptance/release_20261022/review_swept_thumb_v2/index.html)。质量报告是离线描述，检查标记保留；NPZ 不含 RGB。旧 12 段和 24 段数据保留为历史档案。 三盘、四盘质量报告无检查标记；五盘第 8 次放置在 94.12 秒有一个约 20 ms 的双手接触中断样本，之后重新接触并于 95.675 秒合法放稳。该阶段最大采样倾角为 0.568 rad；对应独立物理录像片段已列入复核材料，人工结论仍待填写。

![Genesis 场景（旧 24 段版本）](media/scene.png)

这是固定骨盆的桌面操作任务：G1 使用 43 个关节，物理频率 200 Hz，动作频率 50 Hz。物体通过真实碰撞与接触运动。圆盘具有真实贯通的盘孔，碰撞几何由环形扇段组成，杆可以穿过盘孔；没有把圆盘吸附到手上或用状态写入替代搬运。

2026-10-23 已按用户决定保留现有 Hanoi，以 **Sequential Manipulation 独立任务**发布，不纳入主工具 benchmark，也不认证工具三层 R9。见[发布范围决定](acceptance/release_20261023_standalone/scope_decision.json)。全部 58 例和三盘数独立回放已通过；人工阶段标注、录像与捷径签审、第二人复现仍待完成，`admitted=false`。当前源码的全层流水线与发布预检见[发布状态](acceptance/release_20261023_standalone/index.html)。

独立任务发布预检使用 `python -m infra.sandbox.release_check humanoid/g1_tabletop_hanoi --scope standalone`。未指定范围时仍按主 benchmark 检查，不能把独立任务的通过记录用作主 benchmark 准入。

任务说明见 [instruction.zh.md](instruction.zh.md)，机器可读配置见 [task.toml](task.toml)。

## 必须依次完成的动作

每一步都依赖前一步产生的物理状态：

1. 选择某一杆的顶盘。只要另一盘正在搬运或等待释放稳定，就不能开始下一盘。
2. 用手抓取并向上提起，使整个圆盘的底部越过源杆顶端。必须实际观测到在源杆上方脱杆。
3. 把盘搬到目标杆上方；目标杆为空，或其顶盘比当前盘更大。
4. 把盘孔对准杆并放下。最底盘应由对应底座支撑，上层盘应由正下方的盘支撑。
5. 完全脱离机器人接触，并稳定保持 0.5 秒，才提交这次移动。整叠在目标杆完成后，再连续稳定保持 2 秒，任务才成功。

非法搬运非顶盘、同时搬多盘、大盘压小盘、未脱杆横穿杆、掉落、无效物理状态或超时会终止失败。合法的额外移动允许；提起后放回原杆不增加移动次数。失败与成功会保持到显式 `reset()`，环境不会自动重置。

## 启动

在 `robo-si` 目录中执行：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop.run --task hanoi --steps 150 --image humanoid/g1_tabletop_hanoi/media/scene.png --report humanoid/g1_tabletop_hanoi/validation/no_op.json
```

这条命令使用 CPU 执行 150 个控制步，即 600 个物理步、3 秒仿真；输出场景图片和报告。默认动作为零，保持初始关节目标。首次运行可能需要编译物理内核。

使用 `--disks 4` 或 `--disks 5` 切换盘数；`--viewer` 打开查看窗口。`--actions actions.json` 可执行一个 JSON 数组，每行含 43 个归一化关节动作。动作接口将目标设置为 `default_q + 0.25 * action`，并受关节限位和实际施加力矩上限约束。动作文件入口本身不提供完成任务的控制器。

Python 环境入口：

```python
from humanoid.g1_tabletop_hanoi.genesis_env import G1TabletopHanoiGenesis
from humanoid.g1_tabletop_hanoi.task_spec import TaskConfig

env = G1TabletopHanoiGenesis(cfg=TaskConfig(num_disks=3))
observation, reward, done, info = env.step([0.0] * 43)
env.close()
```

此开发接口会暴露物体真值与评分状态，没有评测隔离，不能直接作为防作弊的公开 agent 接口。

## 专家轨迹与数据集

当前发布候选的[3–5 盘数据清单](solution/datasets/expert_3to5_release_20261023/manifest.json)包含 31,004 个 50 Hz 控制步，三条均通过同环境独立物理回放和 sandbox 命令回放。完整冻结扫描为 **58/58**，每个盘数三次全新运行的阶段时间波动为 0。见[自动审计](acceptance/release_20261022/automatic_audit_swept_thumb_v2.json)与[人工复核包](acceptance/release_20261022/review_swept_thumb_v2/index.html)。质量报告是离线描述，检查标记保留；NPZ 不含 RGB。旧 12 段和 24 段数据保留为历史档案。 三盘、四盘质量报告无检查标记；五盘第 8 次放置在 94.12 秒有一个约 20 ms 的双手接触中断样本，之后重新接触并于 95.675 秒合法放稳。该阶段最大采样倾角为 0.568 rad；对应独立物理录像片段已列入复核材料，人工结论仍待填写。

下表是保留的历史名义参考，不代表当前默认入口：

[solution/README.md](solution/README.md)说明控制器、批量采集、轨迹格式、质量分析和独立物理回放。`run_expert`和`collect`默认使用`--controller centered`盘中心线双手夹持控制器及`CenteredConfig`，支持`--disks 3/4/5`；`--controller single`仅用于三盘初始顶盘的单手抓取探针。当前CPU、种子0结果如下，最新汇总见[12 段采用验证](validation/ring12_adoption.json)。

| 盘数 | 完整录制 | 移动数 / 仿真时间 | 同环境独立物理回放 | 录制质量 |
|---|---|---|---|---|
| 3 | [通过](solution/runs/ring12_20261022/disks3/nominal/expert/report.json) | 7 / 83.870 s | [通过](solution/runs/ring12_20261022/disks3/nominal/replay/report.json) | [无检查标记](solution/runs/ring12_20261022/disks3/nominal/expert/quality.json) |
| 4 | [通过](solution/runs/ring12_20261022/disks4/nominal/expert/report.json) | 15 / 173.840 s | [通过](solution/runs/ring12_20261022/disks4/nominal/replay/report.json) | [无检查标记](solution/runs/ring12_20261022/disks4/nominal/expert/quality.json) |
| 5 | [通过](solution/runs/ring12_20261022/disks5/nominal/expert/report.json) | 31 / 352.445 s | [通过](solution/runs/ring12_20261022/disks5/nominal/replay/report.json) | [见检查标记](solution/runs/ring12_20261022/disks5/nominal/expert/quality.json) |

三条新轨迹均完成逐步回放比较；五盘保留第 8 步右手接触力单样本缺失的质量标记，详见报告和下文。这些结果限于同环境 CPU 回放。下图及其录制来自旧 24 段版本，保留用于历史追溯。

![真实五盘成功终态，全部圆盘已释放并稳定叠在C杆](media/expert_5_disks.png)

上图来自`elliptic_5_002`的真实物理终态：31次合法移动，最终稳定保持2秒后环境判定成功。

旧圆柱底座上的[centered_probe_008](solution/runs/centered_probe_008/report.json)使用1.4秒慢下降，在17.16秒因`placement_dwell`未满足而停止，[最长放置保持仅0.03秒](diagnostics/centered008_release_stability.json)。后续[接触稳定性对照](diagnostics/contact_stability_evidence.json)支持改用同顶高的方形底座；在新底座执行旧动作的[局部回放](solution/runs/box_pad_replay008/report.json)于14.555秒提交首移，末尾盘稳定超过3秒。两类底座的结果属于不同环境版本，局部进展不构成完整任务成功。

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.run_expert --controller centered --disks 3 --seed 0 --output humanoid/g1_tabletop_hanoi/solution/runs/candidate_3_seed0 --image
```

每个新输出目录保存50 Hz控制步的动作前后观测、43维归一化动作与实际关节目标、奖励、环境判定、控制器阶段和累计力矩上限。成功、失败和未完成的尝试都会保留；只有新报告的`accepted = true`才允许进入成功轨迹集合。验收依赖真实环境终态、完整合法搬运、稳定释放和力矩限位，控制器的阶段标签不作为成功证据。`replay`可在新环境中重放动作并重新采集验收；本地验收仍使用公开真值开发接口，不构成隔离评测或任务准入。

离线验收的`recorded_evidence_accepted`与`accepted`一致，`independent_physics_replay_verified`和`physical_task_solution_verified`始终为`false`。只有默认真实环境回放的新轨迹通过验收，后两项才会设为`true`，且仅说明本次运行的环境；测试替身不能获得物理验证标记。回放比较源码、机器人资产、包版本和实际物理配置，`source_environment_match`单独说明来源环境是否匹配；`--require-same-environment`会在执行动作前拒绝差异或缺失证据。

批量尝试3、4、5盘，每个盘数使用种子0：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.collect --disks 3 4 5 --seeds 0 --controller centered --backend cpu --output humanoid/g1_tabletop_hanoi/solution/datasets/candidates_3to5_seed0
```

批次目录必须尚不存在。`manifest.json`中的`training_episodes`仅收录独立重新验收通过且采集进程正常退出的轨迹；其余尝试保留在拒收清单中。旧圆柱底座下的[历史3/4/5盘批次](solution/runs/preparation_3to5_seed0/manifest.json)当时全部被拒收：三盘扰动其他盘、四盘未建立手接触、五盘未脱杆，该历史批次的成功集合为空，与上表后续成功结果分开保留。每盘的`symbolic_plan.json`只是参考计划，不作为专家数据。

`centered` 发布候选的空手接近为三、四盘 1.2 秒，五盘至少 1.4 秒；下降 1.4 秒、释放 0.7 秒、释放后等待 0.3 秒、退回 0.8 秒。所有盘的水平五次插值轨迹峰值速度限制为 0.43 m/s，按实测盘位置跟踪提盘与下降，并按邻盘几何选择拇指姿态。该规则不读取种子或案例编号。`TaskConfig` 默认时限仍为三、四盘 180 秒、五盘 420 秒；`--config` 只覆盖控制器参数，仍可能使序列超时。2026-10-23 该统一候选已通过[冻结 58 例](acceptance/release_20261022/sweep_swept_thumb_release_v2/summary.json)，包括张手和完整撤手高度的拇指扫掠检查；无种子特判。历史录制保留实际配置；旧轨迹缺少时限字段时按 180 秒恢复。

## 场景与判定

以下是名义场景（`TaskConfig()` 的默认值，种子 0 专家录制所用）；评测场景的随机范围见「场景随机化方案」。

世界坐标单位为米，四元数顺序为 `wxyz`。桌面顶高 0.74，尺寸为 0.70 × 1.15；三根杆位于 `x = 0.46`，A/B/C 的 `y` 分别为 `+0.25 / 0 / -0.25`。当前默认`pad_shape="box"`，底座尺寸为0.21 × 0.21 × 0.025，顶面仍高0.765；杆半径0.012、杆高0.18。`pad_shape="cylinder"`保留旧半径0.105的圆柱底座用于对照；旧元数据缺少该字段时回放明确恢复圆柱底座，不自动迁移到方形底座。

当前汉诺塔默认`enable_torsional_friction=True`，圆盘材质显式设置`friction_torsional=0.005 m`，为接触处提供扭转摩擦。该修正针对双点夹持时绕接触连线的转动，已用于上表成功录制；旧圆柱底座与早期方形底座局部结果早于此修正。旧元数据缺少开关时回放恢复`False`，不自动采用新设置。移动合法性、释放和稳定性判定门槛不变。

摩擦模型当前默认`friction_model="elliptic"`，对应椭圆摩擦锥与`impratio=100`。在每侧接触恒定3 N、初始角速度0.5 rad/s的[独立微夹持对照](diagnostics/pinch_torsion_elliptic_001/summary.json)中，椭圆模型与0.005 m扭转摩擦组合保持双接触3秒，最大下滑约0.107 mm。该实验解释局部物理机制；完整G1求解证据以录制和独立回放报告为准。`"pyramidal"`保留用于历史对照；旧元数据缺少模型字段时回放恢复`"pyramidal"`，实际求解器选项随`physics_metadata`保存。

3 盘外半径依次为 0.09、0.07、0.05，`disk_0` 最大；4 或 5 盘在 0.09 与 0.05 之间等距取半径。盘孔半径 0.022，盘厚 0.025，每盘质量 0.12 kg。名义场景中起始圆盘由大到小叠放在 A 杆，孔与杆同轴，环形几何互不穿插；目标为 C 杆（绿色底座）。

| 判定项 | 默认要求 |
|---|---|
| 脱杆 | 圆盘最低点高于源杆顶至少 0.003 m |
| 放置位置 | 盘套在目标杆上：圆心离杆轴不超过 0.012 m（孔与杆的径向间隙 0.010 加接触余量 0.002）；垂直误差不超过 0.006 m |
| 放置姿态 | 盘面倾斜不超过 0.12 rad |
| 稳定速度 | 线速度不超过 0.03 m/s，角速度不超过 0.20 rad/s |
| 正确支撑 | 对应底座或正下方圆盘向上合力大于 0.05 N；其他物体不能提供超过 0.05 N 的向上支撑 |
| 放置提交 | 无任何机器人接触，连续满足条件 0.5 s |
| 完成 | 所有盘合法位于目标杆，全部释放、正确支撑并再稳定 2 s |
| 时间限制 | 3、4盘默认180 s；5盘默认420 s；显式`TaskConfig.max_episode_seconds`优先 |

放置与离位的水平容差由几何推出：`TaskConfig` 中这两项默认为 `None`，取盘孔半径 − 杆半径 + `ring_contact_allowance`。盘套在杆上时，圆心本来就只能在 0.010 m 的间隙内移动，所以这一项只判断盘在哪根杆上，不考对中精度；在叠放高度上，盘心离杆轴 0.012 m 以内却没套进杆，盘体就会与杆相交，物理上不会出现。2026-10-21 之前两项分别为 0.0075 m 和 0.009 m；旧录制的元数据带有显式旧值，回放时仍按旧值判定。

`Evaluator.update(states, dt)` 由可信环境在每个物理步调用。每个盘的状态必须包含 `pos`、`quat`、`linear_velocity`、`angular_velocity`、`hand_contact`、`robot_contact` 和 `support_forces`。其中 `support_forces` 是按真实接触物体名记录的向上合力，单位 N；不能用接触点数量替代。`support_contact` 仅为可选辅助信息，单独设置它不能满足支撑判定。

只有手部接触能提供抓取证据，任何机器人部位接触都会阻止释放判定。评分不使用策略声称的“抓起”“移动完成”事件。`success` 才对应 `score = 1`；`progress`、`move_count` 和 `phase` 仅用于诊断，没有部分成功分数。

## 符号计划与回归

`reference_moves(num_disks)` 返回 `(disk_name, source_peg, target_peg)` 序列。3、4、5 盘的最少步数分别为 7、15、31。该序列仅描述汉诺塔组合逻辑，不含机械臂轨迹、抓取规划或控制指令，也不是物理解。

运行独立于 Genesis 的评分回归：

```powershell
../genesis_env/Scripts/python.exe -m unittest discover -s tests -p test_tabletop_hanoi.py -v
```

回归覆盖完整符号序列、合法额外移动、非法大小关系、非顶盘、同时多盘、未释放、错误支撑对象、机器人身体接触、掉落、无效状态、超时与终止保持。合成状态测试通过证明这些判定行为，不证明 G1 已完成真实物理任务。

物理空跑另覆盖[四盘](validation/no_op_4_disks.json)和[五盘](validation/no_op_5_disks.json)，各运行 400 个物理步（2 秒），结果均为稳定起始栈、零移动、零分。公共环境为分块圆环增大了接触容量，避免多盘堆叠超过模拟器默认接触缓冲。

## 场景随机化方案

状态：已实现（2026-10-21），发布复测进行中（2026-10-22）。生成器是 [`randomization.py`](randomization.py)；sandbox 默认使用随机场景，`--nominal` 用于名义场景回放。原有 58 场景正在通过沙箱记录器和 verifier 重新验证，全部结果保存在 [release_20261022](acceptance/release_20261022)。`randomisation` 仍为 partial；新增提盘反馈、邻盘避碰和身体变化尚未全部通过，不作为发布默认。

做法按[任务设计指南第 04 节](../../infra/task-design-zh.html#random)：每个回合的场景由（种子、回合序号、抽取次数）作键，用 Philox 计数器式随机数抽取，写入封存的 episode spec。`check_scene` 只接受生成器能产生的场景，篡改或越界的 spec 会被拒收。

| 变量 | 名义场景 | 随机范围 | 收窄依据 |
|---|---|---|---|
| 起始杆、目标杆 | A → C | 6 种有序组合等概率；目标杆底座为绿色，其余为灰色 | — |
| 杆的 x | 0.46 | 每根杆独立取 0.42–0.47 | 原定 0.42–0.50；首轮所有够不到的位置都在 x ≥ 0.475 |
| 杆的 y | +0.25 / 0 / −0.25 | 中杆 y 取 ±0.02；相邻杆距 0.23–0.27（外侧杆 \|y\| ≤ 0.29） | 原定 ±0.03；外侧杆在 \|y\| = 0.30 的角点场景全部失败 |
| 杆高 | 0.18 | 0.16–0.20 | 未收窄 |
| 盘外半径 | 0.09 至 0.05 等距 | 最大盘 0.086–0.093，最小盘 0.046–0.054，相邻差 ≥ 0.008 | 未收窄 |
| 盘颜色 | 按尺寸固定 | 五种颜色随机排列 | — |
| 盘初始位姿 | 与杆同轴，yaw 0，恰好叠放 | 与杆同轴；yaw 在 0–2π 随机；每盘比下层高 1 mm，开局落稳 | 原定 ≤ 6 mm 平面偏移，因开局 NaN 取消（见下文） |
| 盘质量 | 0.12 kg | 0.10–0.13 kg | 原定 0.10–0.15；0.13 kg 以上时专家夹持失败 9/39，搬运途中掉盘全部发生在 ≥ 0.131 kg |
| 盘摩擦 | 0.7 | 0.7–0.9 | 原定 0.6–0.9；低于 0.7 时夹持失败 9/40，0.7 以上 5/62 |
| 身体参数 | 默认固定，可选实验模式 | 手臂力矩上限 ×0.85–1.0；14 个手臂关节初始角度 ±0.05 rad | `--body-variation`；实际力矩上限和变化范围公开，不增加硬件上限。边界验证尚未全部通过，默认关闭 |

拒绝规则（`randomization.rejections`）：相邻底座间隙至少 0.02；每根杆满足 hypot(x, \|y\| + 0.15) ≤ 0.62 m（专家双手夹持时，远侧那只手要从对侧肩伸过来；扫描中够到的杆都 ≤ 0.635，够不到的都 ≥ 0.630，取重叠区下方再留 1 cm）；相邻盘半径差至少 0.008。`TaskConfig` 另外保证底座在桌面内、整叠低于杆顶、最大盘加放置容差仍落在底座内。最终范围下接受率 82.7%，拒绝几乎全部来自可达性规则。

不随机：判定阈值、杆半径、盘孔半径、盘厚、桌高、机器人固定位置和求解器设置。盘数（3/4/5）仍是评分分层变量；本任务属顺序操作类，不设指南第 05 节的工具三层。

### 参考专家扫描

[`solution/sweep.py`](solution/sweep.py) 对每个场景单独运行一次 `run_expert --controller centered --task-config`。共六轮、193 次运行，每轮按上一轮的失败收窄一项；每次运行的场景、是否验收和终止原因都保留在 [validation/randomization/sweeps/](validation/randomization/sweeps/index.json)。专家读取仿真真值，扫描只说明这些范围可解，不代表 agent 的能力。

最后两轮：第 5 轮的随机场景与最终范围只差中杆平移（±0.03）；第 6 轮是最终范围的角点场景，即最远侧向、最远前方、最近最密和斜排四种布局，配最重、最滑的盘和最高的杆。

| 盘数 | 随机场景（第 5 轮） | 角点场景（第 6 轮） | 失败原因 |
|---|---|---|---|
| 3 | 15/16 | 5/5 | Genesis NaN 1 |
| 4 | 11/12 | 3/5 | NaN 2，提盘失败 1 |
| 5 | 7/8 | 3/5 | NaN 1，提盘失败 2 |

第 6 轮已经没有够不到的失败，剩下两类：

- **提盘失败**（`disk did not lift above rod`）：夹持后手已接触盘，但提起时盘留在杆上。专家已加入重试：盘仍在原位时，先在杆上方张开，再按盘的实际位置重新夹持，每次多夹紧 4 mm，最多 2 次（名义录制从未走到这条分支）。仍有约 5% 的回合失败。这是参考控制器的稳健性问题，不说明场景不可解。
- **Genesis NaN**：见下一节。

### 数值问题：叠放的分段圆环

Genesis 在一些场景中报 `Invalid constraint forces causing 'nan'`，回合直接中断。开局的检查记录在 [start_stability.json](validation/randomization/start_stability.json)。

- **名义场景本身就在临界上**：名义 5 盘场景把盘质量改 ±1 g（0.119 或 0.121 kg），或把摩擦从 0.70 改到 0.71，开局就会 NaN（10 种微小扰动中 3 种）。随机化只是把这个问题暴露了出来。
- **开局**：叠放时的平面偏移最容易触发。去掉偏移、保留随机 yaw、每盘抬高 1 mm 后：3 盘 0/12，4 盘 0/18，5 盘 1/72（两批各 36 个场景）。yaw 全部对齐（与名义场景相同）反而更糟：不抬高 19/54，抬高 25/54。
- **操作中**：扫描的 13 次 NaN 中，12 次发生在双手张开、放下盘的瞬间（大多是最小的盘落到空底座上），1 次在开局。

按现有规则（只改零件，不改求解器设置），修法是改圆环的碰撞几何，对比如下。

#### 碰撞几何对比（2026-10-21）

`TaskConfig.ring_segments` 与 `ring_segment_shape` 可以切换圆环的碰撞几何。以下是采用前的历史对照；当前默认已改为 12 段，见下节。旧录制保留原几何。开局检查见 [ring_geometry_start.json](validation/randomization/ring_geometry_start.json)：

| 圆环碰撞几何 | 严苛开局（同轴、yaw 0、不抬高，36 个 5 盘场景） | 名义 5 盘的 9 种微小扰动 |
|---|---|---|
| 24 段楔块（旧默认） | 13/36 NaN | 3/9 NaN |
| **12 段楔块** | **0/36** | **0/9** |
| 24 个 box 原语 | 8/36 | 7/9 |
| 12 个 box 原语 | 16/36 | 3/9 |

12 段楔块的专家扫描见 [ring_geometry_sweeps/](validation/randomization/ring_geometry_sweeps/)。3/4/5 盘都用最终随机范围，每个盘数都包括随机场景、角点场景、名义场景，以及原先在 24 段下出 NaN 的场景的重跑：

| 专家双手间距 | 随机场景 | 角点场景 | 原 NaN 场景 | 名义 3/4/5 盘 | NaN |
|---|---|---|---|---|---|
| 向 12 边形外表面内收（夹得紧） | 34/36 | 12/15 | 4/4 | 3、4 盘通过；5 盘第 20 步右腕够不到 | 0/61 |
| 沿用 24 段时的间距 | 28/36 | 9/15 | 2/4 | 全部通过 | 1/58 |

同样这些场景在 24 段楔块下约有 5 次 NaN。结论：12 段楔块基本消除了 NaN，但它改变了夹持几何。夹得紧时随机场景的结果最好，但名义 5 盘第 20 步（把半径 0.07 m 的盘放到 A 杆低处）右腕误差为 3.5–5.5 mm；把 IK 容差放宽到 5 mm 仍然过不去，这是当时固定补偿下降路径的可达极限；不能据此判定杆位本身不可达。沿用旧间距能解名义 5 盘，但搬运途中掉盘明显增多。

上述两种夹距对照完成后，继续调整了下降过程，结果如下。

#### 采用 12 段与下降反馈（2026-10-22）

默认现为 12 段楔块，`CenteredConfig.follow_ring_apothem=True`。下降时按盘的实测 XY 持续修正手位，增益 4/s，每轴速度不超过 0.03 m/s；24 段对照保留旧下降路径。IK 仍为 3 mm 容差、100 次求值，没有继续放宽。

复查发现，第 20 步在高处对齐时积累了约 4 cm 的横向补偿；将其固定带到低处会超出可达范围。此前的“杆位不可达”判断过强。新下降反馈已完成名义五盘全部 31 次移动，也解决了此前三盘斜排角点的放置失败。

原有 58 个场景全部重跑，结果见 [完整摘要](validation/ring12_adoption.json) 和 [逐场景记录](validation/randomization/ring12_20261022/)：

| 随机场景 | 角点场景 | 原 NaN 场景 | 名义 3/4/5 盘 | NaN |
|---|---|---|---|---|
| 34/36 | 13/15 | 4/4 | 3/3 | 0/58 |

总计 54/58 验收；失败场景、终止原因和完整录制均保留。三盘 `seed_69` 从旧扫描的通过退化为 `multiple_disks_moving`，发生在最后一次提盘时，需要继续修复；不能只看总成功率。有限扫描中未观察到 NaN 不等于证明所有场景都不会 NaN。名义三条轨迹共 30,509 步，独立物理回放逐步一致，沙箱回放盘位置最大差为 0 m；初始评分摘要字段集的差异单独记录，未拍摄本轮新视频。

五盘质量报告保留一项检查标记：第 8 次移动放置期间，右手接触力有 1 个 50 Hz 样本为零（约 20 ms），左手持续接触；搬运/放置最大盘倾角约 0.845 rad。该移动最终正确释放并稳定提交。任务验收通过不代表这些质量特征已通过人工视频审查。

### 当前复核状态

上述 54/58 与旧质量标记属于历史候选；当前冻结扫描为 58/58，全部旧失败保留。当前三条质量报告见 [acceptance/release_20261022/dataset_release_20261023](acceptance/release_20261022/dataset_release_20261023_v2/summary.json)。

可信子目标恢复只在新世界控制开始前执行，并核对封存文件、世界参数和评分历史。每个盘数两个释放态恢复和三个接触子任务均通过独立物理验证并有录像。六个释放态恢复统一执行记录后缀，必要时保持最后目标最多 1 秒，仍受原总时限和 2 秒最终保持要求限制；原严格后缀失败保留，追加时长逐项记录在 subgoals_settle_swept_thumb_v2。接触子任务工具仅证明当前这一合法移动；不声称整个塔完成，也不表示公共 held-checkpoint API 已开启。热启动缓存不在快照中，不能声称逐位连续。

发布范围已经确定为独立顺序操作任务。仍需人工阶段标注、录像/捷径签审与第二人复现；全层流水线须与冻结后的当前源码相符。身体变化保持 opt-in；有限边界实测不等于所有组合已验证。

## 隔离评测沙箱

任务已接入仓库统一沙箱运行时（`infra/sandbox/`），说明见 [sandbox/README.md](sandbox/README.md)，准入记录见 [admission.json](admission.json)。agent 只能读取机器人自身传感器并发送 43 维关节目标（servo 模式，环境固定增益），评分从可信侧状态日志回放本任务的 `Evaluator` 得出，与环境实时评分器和独立终态检查交叉核对；得分仍为二值。当前随机覆盖与三盘数独立回放均已通过。独立任务仍须通过当前源码的完整流水线及人工验收，发布范围选择本身不授予准入。
