# 桌面汉诺塔：控制器与专家轨迹

当前发布候选的[3–5 盘数据清单](datasets/expert_3to5_release_20261023/manifest.json)包含 31,004 个 50 Hz 控制步，三条均通过同环境独立物理回放和 sandbox 命令回放。完整冻结扫描为 **58/58**，每个盘数三次全新运行的阶段时间波动为 0。见[自动审计](../acceptance/release_20261022/automatic_audit_swept_thumb_v2.json)与[人工复核包](../acceptance/release_20261022/review_swept_thumb_v2/index.html)。质量报告是离线描述，检查标记保留；NPZ 不含 RGB。旧 12 段和 24 段数据保留为历史档案。 三盘、四盘质量报告无检查标记；五盘第 8 次放置在 94.12 秒有一个约 20 ms 的双手接触中断样本，之后重新接触并于 95.675 秒合法放稳。该阶段最大采样倾角为 0.568 rad；对应独立物理录像片段已列入复核材料，人工结论仍待填写。

以下数据表保留历史参考；当前入口默认选择 expert_3to5_release_20261023。


当前默认使用 12 段楔块、贴合圆环外表面的夹距和下降过程的实测位置反馈。完整验证见[采用摘要](../validation/ring12_adoption.json)。

| 盘数 | 完整录制 | 移动数 / 仿真时间 | 同环境独立物理回放 | 录制质量 |
|---|---|---|---|---|
| 3 | [通过](runs/ring12_20261022/disks3/nominal/expert/report.json) | 7 / 83.870 s | [通过](runs/ring12_20261022/disks3/nominal/replay/report.json) | [无检查标记](runs/ring12_20261022/disks3/nominal/expert/quality.json) |
| 4 | [通过](runs/ring12_20261022/disks4/nominal/expert/report.json) | 15 / 173.840 s | [通过](runs/ring12_20261022/disks4/nominal/replay/report.json) | [无检查标记](runs/ring12_20261022/disks4/nominal/expert/quality.json) |
| 5 | [通过](runs/ring12_20261022/disks5/nominal/expert/report.json) | 31 / 352.445 s | [通过](runs/ring12_20261022/disks5/nominal/replay/report.json) | [见检查标记](runs/ring12_20261022/disks5/nominal/expert/quality.json) |

三条新轨迹的初始/前后观测、动作、目标、奖励、终态与力矩记录均与独立回放逐步一致。质量报告只描述已记录样本，不代替物理回放或沙箱准入。旧 24 段数据及其历史验证见[原摘要](../validation/expert_preparation.json)，所有原始文件保留。

历史失败与局部诊断仍保留：[box_full3_001](runs/box_full3_001/report.json)只完成两移，[centered_probe_008](runs/centered_probe_008/report.json)在旧圆柱底座上转移后未能稳定提交，[局部回放](runs/box_pad_replay008/report.json)只完成首移。它们帮助定位[接触稳定性问题](../diagnostics/contact_stability_evidence.json)，均未进入完整成功训练集。

任务支持3–5盘，固定骨盆、43个关节、200 Hz环境判定和50 Hz控制。默认时限为三、四盘180秒、五盘420秒，显式`TaskConfig.max_episode_seconds`优先。当前默认`pad_shape="box"`，底座尺寸0.21 × 0.21 × 0.025 m，顶面高度保持0.765 m；`"cylinder"`保留为旧场景对照。移动判定保持不变：取顶盘、在源杆上方脱杆、合法搬运、正确支撑放置、无机器人接触并稳定0.5秒；整叠在C杆还要稳定保持2秒。完整任务规则见[上级说明](../README.md)。

当前汉诺塔同时默认启用`enable_torsional_friction=True`，圆盘材质的`friction_torsional`显式设为0.005 m，针对双点夹持时绕接触连线的转动提供扭转摩擦。上表成功录制已采用该设置，早期局部诊断属于不同物理版本。实际开关及物理选项随元数据保存。

当前默认`friction_model="elliptic"`，使用椭圆摩擦锥与`impratio=100`，以减小微夹持对照中观测到的软约束持续滑移。[独立微夹持实验](../diagnostics/pinch_torsion_elliptic_001/summary.json)的`torsion_5mm`组以每侧接触3 N、初始角速度0.5 rad/s运行3秒，双接触保持、最大下滑约0.107 mm、末0.5秒平均转速约2.2×10⁻¹² rad/s；这是椭圆模型与0.005 m扭转摩擦的组合结果，不是真实G1完整抓取。`"pyramidal"`保留为原金字塔模型对照。微夹持结果不替代完整汉诺塔物理成功，实际模型和求解器选项分别保存在`TaskConfig`与`physics_metadata`。

## 控制器与运行范围

| 入口 | 用途与当前范围 |
|---|---|
| `--controller centered` | 当前默认：翻转手掌，使两侧接触靠近盘中心线，使用`CenteredConfig`；3、4、5盘种子0均已完整成功，同环境独立回放状态见上表。 |
| `--controller horizontal` | 保留的水平手腕双手夹持候选，接收3、4、5盘配置。 |
| `--controller bimanual` | 保留的倾斜手腕双手夹持候选，同样接收3、4、5盘配置。 |
| `--controller single` | 仅针对三盘初始栈顶`disk_2`的单手抓取探针，可测试接触与提起；未实现完整搬运、释放或多盘求解。 |
| `kinematics.py` | 使用MuJoCo进行正向运动学、雅可比、逆运动学与重力估计，再把关节目标交给Genesis执行。 |
| `grasp_search.py` | 静态Dex3抓取几何筛选，输出只能作为候选参数，不作为物理抓取成功证据。 |
| `recording.py` | 逐控制步记录与离线验收，无需导入Genesis即可检查已有文件。 |
| `collect.py` | 按盘数和种子独立启动采集进程，更新批次清单并严格筛选可训练轨迹。 |
| `replay.py` | 用原始环境重新执行保存的动作，在新目录采集本次物理证据。 |
| `quality.py` | 统计已记录的接触、双手力、倾角、放置误差和稳定释放证据，不执行物理回放。 |
| `export_dataset.py` | 验收来源与同环境独立回放配对后，导出可用`allow_pickle=False`加载的NPZ数组。 |

控制器使用物体真值与环境评分状态进行开发。运行期间不写入圆盘位姿、不把圆盘附着到手上，物体运动由Genesis碰撞与接触产生。运动学计算和阶段标签均不替代环境判定。

## 采集候选轨迹

以下命令均在`robo-si`目录执行，使用已安装Genesis、PyTorch、MuJoCo、SciPy与NumPy的环境。首次运行可能编译仿真内核。

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.run_expert --controller centered --disks 3 --seed 0 --backend cpu --output humanoid/g1_tabletop_hanoi/solution/runs/candidate_3_seed0 --image
```

`--disks`可改为`4`或`5`，并为每个盘数、种子和参数版本使用新的输出目录。`--backend gpu`切换计算后端；`--config config.json`覆盖所选控制器配置类中的参数；`--image`保存最终画面。目录必须是新目录或空目录，已有轨迹不会被覆盖。

所有盘数的默认`CenteredConfig`设置36 mm的开口余量、12 mm的接触预压偏移和1.005 m的搬运中心高度；下降1.4秒，提起、转移各1.5秒，放下1.4秒，释放0.7秒、释放后等待0.3秒、退回0.8秒。其余阶段继承`ControllerConfig`。实际成功录制的全部参数保存在各自`metadata.json`中；修改参数、环境或种子后应重新验收。

五盘不再自动覆盖为快速节奏；31次最少移动使用与三、四盘相同的控制器时序，默认时限增至420秒。实际动作可能因等待接触、放置稳定或重试而增加耗时；增加时限不构成完整成功保证，也不会降低任何移动与释放判定门槛。

`configs/`保留历史实验参数，不能用配置名替代对应版本的成功证据。[centered_careful.json](configs/centered_careful.json)显式设置1.4秒下降，对应旧008探针；[centered_firm.json](configs/centered_firm.json)与[centered_gentle.json](configs/centered_gentle.json)用于比较夹持几何和时序。[grip_12mm.json](configs/grip_12mm.json)与[grip_18mm.json](configs/grip_18mm.json)分别设置12 mm和18 mm预压偏移。`--config`覆盖控制器默认参数，不修改任务时限，仍可能使完整序列超时；每次更改均需重新采集和验收。

只检查三盘初始顶盘的抓取时：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.run_expert --controller single --disks 3 --seed 0 --max-moves 1 --output humanoid/g1_tabletop_hanoi/solution/runs/single_grasp_probe --image
```

`single`只支持初始三盘栈，`--max-moves`可省略或设为`1`，不会执行后续汉诺塔序列。双手候选也可用`--max-moves 1`采集前缀诊断；抓到盘、提起盘或完成一个前缀都不能满足完整任务的成功验收。

正常结束时，只有`report.json`中的`accepted = true`返回退出码`0`；失败或未完成返回`2`并保留诊断。异常会保留已记录的步骤和拒收报告，再向调用方报告错误。

## 批量采集3–5盘候选

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.collect --disks 3 4 5 --seeds 0 --controller centered --backend cpu --output humanoid/g1_tabletop_hanoi/solution/datasets/candidates_3to5_seed0
```

默认对3、4、5盘各运行一次种子0；可用`--seeds 0 1 2`增加种子，也可缩小`--disks`范围。每个组合通过独立Python子进程实际调用`run_expert`，使用当前任务的逐盘时限和评分规则。`--config`可选，批次会保存配置快照供各次尝试使用。顶层输出目录必须尚不存在，已有空目录也会被拒绝。

旧圆柱底座、统一180秒时限下的[3/4/5盘种子0批次清单](runs/preparation_3to5_seed0/manifest.json)包含3次物理尝试，`training_episodes`为空：

| 盘数 | 该次尝试的停止原因 |
|---|---|
| 3 | 源杆其他圆盘发生扰动，环境判定`multiple_disks_moving`。 |
| 4 | 抓取阶段没有观测到真实手部接触。 |
| 5 | 提起后未达到源杆脱杆高度。 |

这些记录保留各自运行时的参数与源码哈希；后续修改默认配置不会改变已归档结果。当前默认参数和慢下降探针的进展应结合[验证摘要](../validation/expert_preparation.json)与对应单次报告查看。

目录按`disks_3/seed_0`等名称组织。每盘另有`symbolic_plan.json`，包含7、15或31步参考计划，并明确标记`symbolic_only = true`、`expert_data = false`；这些计划不属于成功训练数据。每次尝试保留旁置的标准输出、错误日志以及`collection_validation.json`。

`manifest.json`在进度变化时原子更新，路径均相对于它所在的目录：

- `training_episodes`只列出重新调用`validate_trajectory`得到`accepted = true`、且采集子进程退出码为`0`的轨迹目录；源`report.json`中的成功标签不会直接获得准入。
- `rejected_episodes`保留拒收目录、原因和退出码。失败不影响后续组合继续执行；手动中断时，未执行组合会明确标记。
- `all_passed`仅在全部请求组合通过时为真。此时批量命令退出`0`；存在拒收或未运行组合时退出`2`。

训练入口只读取`training_episodes`，不要遍历整个批次目录把符号计划、失败记录或未完成抓取混入成功数据集。清单中没有通过项时，仅表示该批次没有可供成功训练的轨迹；旧失败批次不代表上表已验收录制的状态。最终NPZ训练合集还要求每条来源均有同环境独立物理回放配对通过。

## 输出与时间对齐

| 文件 | 内容 |
|---|---|
| `trajectory.jsonl` | 首行保存初始观测和环境状态；随后每行对应一次实际完成的`env.step`；末行保存最终状态、累计力矩和中止原因。 |
| `actions.json` | 按原顺序保存43维归一化动作数组，可直接输入公共runner的`--actions`。 |
| `metadata.json` | 完整有效`TaskConfig`、盘数、动作映射、关节顺序、默认关节姿态、关节与力矩限位；`extra`包含种子、后端、控制器参数、源码及机器人资产SHA256、包版本、实际`physics_metadata`和回放来源。 |
| `report.json` | 录制证据验收、独立物理回放验证标记、环境成功标记、移动数、力矩检查、拒收原因及最终环境状态。 |
| `quality.json` | 运行质量分析后生成的逐移动、逐阶段统计及来源哈希；不修改验收结果。 |
| `diagnostics.json` | 候选控制器的阶段诊断、对象状态、停止原因和运行耗时；由`run_expert`生成。 |
| `final.png` | 指定`--image`时保存的最终画面。 |

每条转移保存：

- `pre_observation`和`post_observation`：动作前后关节位置、速度、物体位姿、速度、接触、支撑力与仿真时间。前一条的后观测自动成为下一条的前观测。
- `action`和`target`：43维归一化动作与环境实际采用的绝对关节目标，顺序遵循观测的`joint_names`。映射为`target = clip(default_q + 0.25 * action, joint_limits)`；归一化动作不要求位于`[-1, 1]`。
- `reward`、`done`和`info`：本次环境调用的原始返回值。`info.moves`记录环境确认提交的合法移动及其时间。
- `controller`：阶段、当前移动或回放源步骤等辅助信息。
- `max_applied_torque_nm`：环境从回合开始到当前时刻测得的各关节最大绝对施加力矩。

这是50 Hz控制步数据。环境在内部每个5 ms物理步执行判定；普通控制步包含4个物理步，终止控制步可能只有1–3个物理步。文件不会补齐或伪造终止后的状态。当前格式未保存每个200 Hz物理步的全部观测，也未保存逐物理步瞬时力矩；累计最大力矩用于限位检查。

## 成功数据的验收门槛

`accepted = true`要求以下检查全部通过：

1. 最后一条真实环境返回`done = true`、`success = true`、`failed = false`、`score = 1`，且完成最终稳定保持；最终汇总状态必须与该条返回一致。
2. 环境累计移动日志可从初始A栈逐步重建，满足取顶盘和大盘不压小盘，最终完整叠放在C杆。3、4、5盘至少需要7、15、31次移动，合法额外移动允许。
3. 最终观测中每个盘的位置、姿态、速度、无机器人接触和实际支撑满足任务要求；最后一次移动后的稳定时间足够。
4. 所有转移的观测、动作、目标、奖励和时间关系有效，动作数组与JSONL一致，关节目标在限位内，轨迹完整收尾且未超过其`TaskConfig`的有效时限。
5. 实测累计力矩不超过各关节上限，且没有中止或损坏记录。

失败、未完成、仅抓取或仅前缀的轨迹保留为诊断材料，不进入成功训练集。`environment_success`单独为真仍可能被一致性检查拒收；筛选时使用新生成的`accepted`，不要根据文件名、控制器阶段或单独的移动数推断成功。

报告区分录制证据与独立物理回放：

| 字段 | 离线`validate_trajectory`的输出 | 默认真实环境`replay`通过后的输出 |
|---|---|---|
| `accepted` | 本次录制证据是否通过全部检查 | 新回放轨迹是否通过全部检查 |
| `recorded_evidence_accepted` | 与`accepted`一致 | 与新回放的`accepted`一致 |
| `independent_physics_replay_verified` | 始终为`false` | 仅新回放`accepted = true`时为`true` |
| `physical_task_solution_verified` | 始终为`false` | 仅新回放`accepted = true`时为`true` |

离线验收通过不会自动获得物理回放验证标记。通过`env_factory`注入测试替身的回放始终保留后两项为`false`，即使合成记录通过数据检查也不声称物理验证。该环境公开真值与评分状态，文件也没有防篡改隔离；真实回放通过仍不能替代隔离评测、多个种子的物理复现或任务级`admitted`判定。

## 重新执行物理回放

推荐使用独立回放入口：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.replay --episode humanoid/g1_tabletop_hanoi/solution/runs/candidate_3_seed0 --backend cpu --output humanoid/g1_tabletop_hanoi/solution/runs/replay_3_seed0
```

回放读取源目录的`TaskConfig`、种子和动作，通过原始`env.step`重新执行，并将新观测、奖励、环境判定与力矩写入新目录。遇到真实终态即停止，不复用源目录的观测或成功标签。报告中的`replay_source`保存来源路径及元数据、动作文件的SHA256；这些字段仅用于追溯来源，验收由本次新采集的物理结果决定。默认真实环境入口只有在新轨迹`accepted = true`时才设置两项物理验证标记；命令也只有本次`accepted = true`才返回退出码`0`。

回放保留已记录的显式配置值。旧元数据缺少`pad_shape`时明确补`"cylinder"`，缺少`enable_torsional_friction`时补`false`，缺少`friction_model`时补`"pyramidal"`，缺少`max_episode_seconds`时补180秒，并将这些兼容默认记录在`replay_source.task_config_compatibility_defaults`中；不会自动采用新物理设置或因当前五盘默认420秒而延长旧轨迹时限。旧元数据缺少 `ring_segments` / `ring_segment_shape` 时明确恢复为 24 / `wedge`。新记录总会保存实际生效的圆环几何、底座形状、摩擦模型、扭转摩擦开关和时限。

`environment_comparison`比较源记录与当前源码/机器人资产哈希、包版本、实际物理设置、任务配置及动作接口。默认允许跨版本迁移验证，但差异或证据缺失都会使`source_environment_match = false`；`independent_physics_replay_verified`与`physical_task_solution_verified`仅说明新执行的当前环境。只有成功回放且来源环境匹配，`same_environment_replay_verified`才为`true`。追加`--require-same-environment`可在第一条动作前拒绝差异或缺失证据，并保存拒收报告。版本匹配也不保证逐位确定性或隔离评测有效性。

也可用公共runner执行动作。下面示例按三盘、种子0及最多9000个控制步运行：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop.run --task hanoi --disks 3 --seed 0 --steps 9000 --actions humanoid/g1_tabletop_hanoi/solution/runs/candidate_3_seed0/actions.json --trace humanoid/g1_tabletop_hanoi/solution/runs/public_replay_3_seed0.jsonl --report humanoid/g1_tabletop_hanoi/solution/runs/public_replay_3_seed0.json
```

公共runner需要手动保持盘数和种子一致，也不会自动恢复源目录的自定义`TaskConfig`或运行本目录的完整数据验收。它按`--steps`与动作长度中的较小值执行，终态出现时提前停止；仅运行该命令不产生本格式的`accepted`报告。

## 质量分析与训练数组导出

质量分析读取现有记录，按环境提交的每次移动重建合法栈，用控制器阶段划分提起、搬运、放置和释放窗口：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.quality --episode humanoid/g1_tabletop_hanoi/solution/runs/elliptic_release3_001 --output humanoid/g1_tabletop_hanoi/solution/runs/elliptic_release3_001/quality_new.json
```

默认输出为新建`quality.json`，已有文件不覆盖。报告包含接触缺失的采样时长估计、左右手力的最小值与中位数、最大倾角、脱杆和环境阶段见证、提交后首个样本的目标误差、稳定释放与最终保持。采样接触缺失时长按每个末端样本代表其前一个控制区间估计，不是连续物理测量；双手力来自已记录的真实接触力求和诊断。`review_flags`用于人工复查，质量分析不执行仿真，不新增专家准入结论，其退出码`0`只表示分析完成。

导出器要求来源和回放均重新通过离线验收，并检查同环境独立物理回放标记及来源元数据、动作哈希：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_hanoi.solution.export_dataset --episode humanoid/g1_tabletop_hanoi/solution/runs/elliptic_release3_001 --replay humanoid/g1_tabletop_hanoi/solution/runs/elliptic_release3_001_replay --output humanoid/g1_tabletop_hanoi/solution/datasets/export_3_seed0_new
```

可按相同顺序重复`--episode`与`--replay`导出多条轨迹，输出目录必须不存在。NPZ保存动作、目标、奖励、终止标记、前后关节位置/速度、物体位姿/速度、接触、时间、阶段和移动序号；JSONL仍是完整证据来源。导出会重新加载NPZ并逐数组比较，训练时使用`numpy.load(path, allow_pickle=False)`。该数组导出不含RGB帧，也不构成隔离评测准入。

## 离线检查与回归

不启动物理仿真即可重新检查文件：

```python
from humanoid.g1_tabletop_hanoi.solution.recording import validate_trajectory

report = validate_trajectory("humanoid/g1_tabletop_hanoi/solution/runs/candidate_3_seed0")
print(report["accepted"], report["issues"])
```

离线检查不信任已有`report.json`的成功标签，也不重建控制步之间未保存的物理状态。即使检查的是曾经成功回放的目录，本次离线返回的两项物理验证标记仍为`false`，不会沿用旧报告的声明。损坏JSON、缺失文件、错误类型、非有限数值、时间错位和非法移动日志会被拒收。

```powershell
../genesis_env/Scripts/python.exe -m unittest discover -s tests -p test_hanoi_recording.py -v
../genesis_env/Scripts/python.exe -m unittest discover -s tests -p test_hanoi_collection.py -v
```

这些测试使用合成记录和回放测试替身验证数据契约与拒收行为；通过测试不证明机器人已经完成物理汉诺塔。
