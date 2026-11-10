# G1 搬箱子与走上箱顶：分开验证

日期：2026-10-16。以下是本机仿真证据，不是实机测试或成功率评测。

## 1. 能搬箱子：已验证，但属于 Arena GR00T + Decoupled WBC

最新一次完整闭环：`runs/sonic-box-teacher/result.json`。

- 输入：拿起架子上的棕色箱子，放进右侧桌上的蓝色箱子。
- 19.26 秒、963 个控制步、61 次真实模型推理，通过 Arena 官方任务成功判定（1 个 episode）。
- 物理轨迹中箱子最高抬升 0.17819 m，起终点水平距离 1.93473 m。
- 场景、接触物理和上游成功条件未修改，没有将箱子绑定到手上或逐帧设置箱子位置。
- 官方成功条件是到达目标容器的空间容差；未增加长时间静置判定。单次通过不能推导稳健成功率。

[视频](runs/sonic-box-teacher/ego.mp4) · [结果](runs/sonic-box-teacher/result.json) · [完整状态数据](runs/sonic-box-teacher/teacher_trajectory.npz)

`sonic-box-teacher` 这个目录名表示为 SONIC 准备的教师数据。**此处实际执行器仍然是 Decoupled WBC，不是 N1.7 + SONIC。** 图像和全身/箱子状态已按 50 Hz 记录；尚未转为经过 SONIC 跟踪验证的训练标签。

## 2. 原有预训练策略的上箱测试：未通过

场景：现有 Genesis G1 环境，箱体 0.45 × 0.50 × 0.18 m、5 kg、可移动；箱心初始位置 (1.45, 0, 0.09) m，机器人从地面 x=0.8 m 开始。没有外力托举、运动学传送或关闭跌倒判定。

成功要求连续 2 秒同时满足：

- 左右脚分别与箱顶接触，向上支撑力各超过 5 N；接触点在顶部平面容差 2.5 cm 内。
- 双脚踝投影位于箱顶范围内并留有边缘余量。
- 机身 upright > 0.9，根节点速度 < 0.15 m/s。
- 箱体速度 < 0.05 m/s，箱体 upright > 0.98。

| 控制器 | 输入方式 | 测试长度 | 结果 |
|---|---|---:|---|
| HANDOFF | 指向箱心的速度命令 | 12 秒 | 未踩上；箱子被推到 x=2.045 m |
| GR00T Decoupled 步行策略 | 指向箱心的速度命令 | 12 秒 | 未踩上；箱子被推到 x=2.775 m |
| N1.7 BonesSeed-V2 + SONIC | 实时 RGB/状态 + `Walk onto the box and stand on top of it.` | 9.94 秒 | 未踩上，随后触发跌倒判定；25 次推理 |

三次测试的双脚箱顶有效支撑计数均为 0，稳定站立时间均为 0。速度控制器只收到速度命令，没有高度感知或脚步目标；N1.7 测试使用当前有限运动 checkpoint。结果说明这些现有配置尚未满足上箱要求，**不能证明 G1 本体或 SONIC 原理上做不到**。

补充低箱对照：相同底面和 5 kg 质量、仅高度降低到 0.06 m，HANDOFF 仍未建立箱顶支撑，并在 5.16 秒触发倾斜跌倒判定。该次也未成功：[视频](runs/step06-handoff/motion.mp4)。

[HANDOFF 视频](runs/step18-handoff/motion.mp4) · [GR00T 视频](runs/step18-groot/motion.mp4) · [N1.7 + SONIC 视频](runs/step18-n17-sonic/motion.mp4)

每个目录包含 `result.json`、`box_step_result.json`、逐帧接触力/箱子与脚位置 `box_step_contacts.json`。

## 检测器正对照：能在箱顶承重站立，但不算爬箱

另一次测试明确将机器人初始位置设置在箱顶，SONIC 站立参考在 2.04 秒内达到连续 2 秒双脚支撑标准，箱子没有明显滑移。这是承重/判定校验；**没有从地面走上去，不计为第二项成功**。

[正对照视频](runs/step18-scorer-positive-control/motion.mp4) · [判定报告](runs/step18-scorer-positive-control/box_step_result.json)

## 复现

从 `D:\rsi_vla` 运行（原有模型环境已安装）：

```powershell
.\robo-si\controllers\g1_wbc\run_arena_vla.ps1
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/run.py --backend genesis --method handoff --box-step 0.18 --seconds 12 --headless --video
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/run.py --backend genesis --method groot --box-step 0.18 --seconds 12 --headless --video
```

N1.7 模型服务启动后可运行语言上箱测试（服务启动见 [SONIC_N17.md](SONIC_N17.md)）：

```powershell
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/run.py --backend genesis --method sonic --box-step 0.18 --seconds 12 --headless --video --prompt 'Walk onto the box and stand on top of it.'
```

组合“搬箱垫高 → 自己踩上箱子 → 高处取物”尚未完成闭环验证。

## 3. 当前场景中的物理约束 fallback（2026-10-16）

新增 `constrained_step.py`、`contact_wbc.py` 和 `run_constrained_step.py`。原 `solvers.MotionSolver` 的固定基座接口保持不变；上箱需要浮动基座、脚掌姿态和支撑切换，因此使用单独的全身 IK 与接触力求解实现，并非调用原接口就自动具备爬箱能力。

约束与执行：

- 双脚位姿、重心转移、后脚脚跟抬起/脚尖支撑；避开伸直膝关节的 IK 分支奇异点。
- 使用场景模型关节限位；参考速度不超过 1 rad/s，离散参考加速度不超过 4 rad/s²；超过 0.10 rad 的相邻解跳变拒绝执行。
- 浮动基座动力学与接触力可行性、摩擦锥的保守四面体近似、5 kg 可动箱子的底部摩擦和倾覆余量。规划力矩预留 20% 控制余量。
- 独立加密采样检查机器人自碰撞、地面与箱子碰撞。局部规划模型未包含远处柜体；仅用于已清空的箱前区域。
- Genesis 执行开启自碰撞；腿部使用状态反馈接触 QP 与力矩—转速限制，上肢使用原生隐式 PD。仅初始化时写机器人位置；执行不施加根节点外力、不固定箱子、不将箱子绑定到机器人。
- 依赖新增 `osqp==1.1.3`，已装入本机 `genesis_env`。重装命令：`uv pip install --python genesis_env/Scripts/python.exe osqp==1.1.3`。

最新规划：`runs/constrained-step-collision-aware/`，53.3943 秒；最大参考速度 0.68156 rad/s，离散加速度 4 rad/s²，最大前馈力矩为模型额定上限的 46.76%；加密采样未检出超过 2 mm 的碰撞。规划不等于执行成功。

**实际执行通过一次：** `runs/constrained-step-collision-aware-execution/`，从箱前地面 x=0.95 m 的站姿开始，45.885 秒时达到连续 2 秒双脚箱顶支撑判定。末帧双脚支撑力约 222.1 / 115.2 N，机身 upright=0.99959，箱体水平位移约 0.856 mm。自碰撞开启。观测到的最大关节控制力矩为模型上限的 44.51%，最大实际关节速度为对应上限的 2.94%；采样关节位置最大限位超调 0.000801 rad，属于仿真约束的数值误差，未隐去。录像已人工查看关键帧。

[开启自碰撞的上箱视频](runs/constrained-step-collision-aware-execution/motion.mp4) · [实际结果](runs/constrained-step-collision-aware-execution/result.json) · [规划加密检查](runs/constrained-step-collision-aware/dense_audit.json)

这次证明的是显式全身规划 + 接触 WBC 的从地面登箱能力，不是 N1.7 + SONIC 的语言泛化。起点已在箱前；尚未验证从远处走近、搬箱后接续登箱、更多箱尺寸/初态或 Isaac 后端。

历史排错记录不能作为最终成功证据：`constrained-step-smooth-execution` 虽然触发双脚站稳判定，但其参考轨迹随后未通过自碰撞检查，且该次仿真关闭了自碰撞，因此不接受为物理有效成功。

```powershell
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/constrained_step.py --out robo-si/controllers/g1_wbc/runs/constrained-step-collision-aware
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/audit_step_plan.py robo-si/controllers/g1_wbc/runs/constrained-step-collision-aware/plan.npz
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/run_constrained_step.py --contact-qp --plan robo-si/controllers/g1_wbc/runs/constrained-step-collision-aware/plan.npz --out robo-si/controllers/g1_wbc/runs/constrained-step-collision-aware-execution
```

### Arena 搬箱模型迁入当前场景

`arena_scene_policy.py` 将当前真实相机、关节状态传到本机 Arena GR00T 服务，使用具名手指映射和可移植 GR00T WBC。下层控制器和场景均与原 Arena demo 不同，属于迁移实验。上肢参考限速 2 rad/s，腿部参考限速为电机速度上限的 50%，腿部执行受 DC 力矩—转速包络限制。

`runs/arena-current-scene-box-v2/`：56 次模型调用，17.72 秒后跌倒。视频显示机器人推碰/翻动箱子，没有抓取搬运；箱子最高增高 0.136 m、水平位移 1.619 m **不能单独判为搬运成功**。当前场景搬箱仍未复现。

```powershell
# 先启动已有 Arena 模型服务（端口 5557）
.\genesis_env\Scripts\python.exe robo-si/controllers/g1_wbc/run.py --backend genesis --method groot --arena-box --seconds 20 --headless --video --out robo-si/controllers/g1_wbc/runs/arena-current-scene-box-v2
```
