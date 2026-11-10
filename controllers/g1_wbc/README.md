# G1 controllers in the existing task environments

本目录保存 GR00T Decoupled WBC、HANDOFF、ULTRA 的参数和本机推理适配器。使用已有 `humanoid/g1_support_retrieval` 场景和 G1 模型，物理运动由 Genesis 或 Isaac Lab/PhysX 实际计算。Genesis 环境新增可选 `self_collision=True`，用于约束规划实验；默认配置保留原行为。

新增的语言到动作搬箱验证使用独立的官方 Arena 场景，见 [ARENA_VLA.md](ARENA_VLA.md)。

## 启动

在 `D:\rsi_vla` 的 PowerShell 中：

```powershell
.\robo-si\controllers\g1_wbc\run.ps1 -Backend genesis -Method groot -Seconds 5 -Headless -Video
.\robo-si\controllers\g1_wbc\run.ps1 -Backend genesis -Method handoff -Seconds 5 -Headless -Video
.\robo-si\controllers\g1_wbc\run.ps1 -Backend genesis -Method ultra -Seconds 5 -Headless -Video
.\robo-si\controllers\g1_wbc\run.ps1 -Backend isaac -Method handoff -Seconds 5 -Headless
```

Isaac 的 `-Method` 同样支持 `groot` 和 `ultra`。本机 Isaac 无渲染仿真通过；`-Video` 测试在 Kit/Hydra 初始化阶段崩溃，录像和交互窗口尚未验证可用。Genesis 三种方法均有录像。启动器沿用本工作区既有 Isaac 启动脚本的 EULA 环境设置。

GR00T/HANDOFF 可指定 `-Vx 0.2 -Vy 0 -Wz 0`（m/s、m/s、rad/s）；前 1 秒站立，然后执行命令。ULTRA 使用参考动作，忽略速度参数。当前没有自然语言入口。默认运行 5 秒；更长运行及其他速度尚未验证。

## 参数与输出

- `configs/{groot,handoff,ultra}.json`：源仓库提交、29 个身体关节顺序、默认姿态、PD 增益、力矩限制、armature、控制频率、观测大小及权重 SHA256。
- `artifacts/<method>/`：本机权重、ULTRA 参考动作/运动学资源和上游许可证，已忽略 Git。请遵守各上游许可证。
- `runs/<backend>-<method>/result.json`：完成状态、位移、最低根节点高度及直立程度。
- `trajectory.npz`：每控制步的时间、根位置、直立程度，以及身体目标关节角。
- `run_config.json`：本次完整关节映射和执行器参数；早期测试产生的目录可能没有此新增文件。
- `motion.mp4` / `preview.png`：可选录像/预览。相同方法再次运行会覆盖对应输出；直接调用 `run.py --out <path>` 可另存。

运行时使用 Windows 本机环境，不依赖 WSL。Genesis 使用 `genesis_env`，Isaac 使用 `anaconda3/envs/isaaclab`，可用 `-PythonPath` 覆盖。新增依赖为 ONNX Runtime 1.23.2；Isaac 另需 MuJoCo 3.8.1 和 glfw。未更换既有 torch/numpy。场景资产由本机原 `Benchmark/envs/g1_support_retrieval/assets` 复制到任务资产目录。

`export_assets.py <method>` 在对应 WSL 上游 `.venv` 中运行，可重新导出参数和资源；源仓库默认在 `~/rsi_wbc`。原始 MuJoCo 安装说明见工作区 `WBC_SETUP.md`，旧 `scripts/run_wbc.ps1` 启动的是原始演示。

## 已完成的验证（2026-10-16）

| 方法 | Genesis | Isaac Lab |
|---|---|---|
| GR00T Decoupled WBC | 5 秒，前进约 0.57 m | 5 秒，前进约 0.65 m |
| HANDOFF | 5 秒，前进约 0.71 m | 5 秒，前进约 0.68 m |
| ULTRA teacher | 5 秒参考动作闭环执行 | 5 秒参考动作闭环执行 |

以上均未触发跌倒判定（根高度 < 0.4 m 或身体竖直方向余弦 < 0.3）。这只表示短时运行通过，不代表完整任务成功或长期稳定。GR00T、HANDOFF 的观测构造分别与上游代码比较 20 组随机输入通过；ULTRA 导出的 teacher 与原网络输出比较通过。

## 适配边界

身体 29 关节按名称映射到现有 43 关节 G1。Genesis 手指使用原生位置保持，身体使用显式限幅 PD 力矩；Isaac 使用显式 PD。四元数为 wxyz，根速度输入为世界坐标，策略内转为所需坐标。

- GR00T：当前仅 Decoupled WBC 的站立/行走策略，未接上肢 IK、SONIC 或 N1.7 VLA。
- HANDOFF：执行预训练基础策略，未接 Molmo 上层规划或原部署腕部后处理/CBF。
- ULTRA：执行 teacher，使用真实仿真反馈构造观测；MuJoCo 仅做前向运动学，不推进物理。物体以原物体包围盒近似，初始位置/质量匹配参考；之后物体由当前后端物理驱动，不逐帧瞬移。现有 Dex3 手与源模型仍有差异，尚未验证完整抓取/搬运，student 未接入。

测试关闭载荷/强度随机化和起始扰动，绕过任务计分与自动 reset，`task_success_evaluated=false`。目前未验证搬箱垫高、登箱、柜顶取物或实机控制。

SONIC 后续应作为独立控制器接入，不能将本目录 `groot` 的成功记录当作 SONIC 验证。官方 [VLA workflow](https://nvlabs.github.io/GR00T-WholeBodyControl/tutorials/vla_workflow.html) 和 [model card](https://nvlabs.github.io/GR00T-WholeBodyControl/model_card.html) 描述了另一套 G1 latent-action 接口。
# N1.7 + SONIC

搬运与登箱的独立证据见 [BOX_CAPABILITY.md](BOX_CAPABILITY.md)：Arena 搬运通过；三种现有控制方案登上 18 cm 可移动箱子的测试均未通过。

安装与测试记录见 [SONIC_N17.md](SONIC_N17.md)。SONIC 站立已在 Genesis 和 Isaac 验证；N1.7 + SONIC 已在 Genesis 完成首次 5 秒实时语言蹲起测试，搬箱子尚未验证。

