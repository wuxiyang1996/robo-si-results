# H1S-01 原始冻结专家：新 Gamma 执行 8034801

这次实际执行没有完成任务。原始判决为 `success=false`、`chain_complete=false`、`integrity.ok=true`、`void=false`，原评分 `0.1925`；不能把它改成成功，也不能据此判定 H1S-01 不可解。历史成功包与这次新机器失败必须分别保留。

本次严格恢复固定压缩包 SHA-256 `300630ebf965ef40e6b8c16c231dfe7671fd84dabd70684b842b4138f6d03e03` 中的 `fixed/workspace`，执行原 `reference_v15`、seed 2、原评分器与原 controller 参数。源码与实际世界参数审计未发现变化；原设置仍是**机器人自碰撞关闭、privileged expert、非正式准入**。没有用当前新实现覆盖原始源码。

Gamma 作业 `8034801` 在 `gammagpu07` 的 NVIDIA RTX A5000 上运行，分配 1 GPU、4 CPU、24 GB；Slurm 记录 43 分 51 秒，外层执行计时 2618.18 秒。Linux/Python 3.12.14 是新机器环境，不能混作历史 Windows/Python 3.12.7 的同一执行。核心包版本及完整命令保留在 [环境](baseline-evidence-8034801/receipt-environment.json) 与 [预声明](baseline-evidence-8034801/receipt-predeclared-scope.json)。

## 执行到哪里

| 源码中的高层阶段 | 对应低层动作 | 实测区间 / 样本索引 | 真实结果 |
| --- | --- | --- | --- |
| 接近凳子 | 地面定位、左右脚调整、形成抓取站位 | 0–58.04 s / 0–2902 | 阶段结束事件与 actuator 审计存在；没有把该事件单独当成任意技能效果证明 |
| 抓取、举升、站起 | 下蹲、接触承托、抬起、带载站起 | 58.04–141.56 s / 2902–7078 | expert 的 lift / standup 为 done；连续实测保留 |
| 带载搬运凳子 | 规划脚步、左右转移重量、迈步、接触确认 | 141.56–397.38 s / 7078–19869 | walk 为 done；17 步，躯干前进约 1.0129 m |
| 放置前对齐 | 左右脚对齐、支撑转换、回中 | 397.38–434.22 s / 19869–21711 | `center:qp_failed:contact QP maximum iterations reached`；凳子尚未完成放置 |
| 登高、取物、暂存、下降、重抓与交付 | 原专家中仍有后续规划逻辑 | 没有本次执行轨迹 | 未执行，不能补成成功示范或目标证据 |

失败发生于放置前脚部对齐后的回中 QP，终态是 `setdown:alignment:center:qp_failed:contact QP maximum iterations reached`。这是此次执行的控制求解失败；尚未通过诊断定位具体数值原因。它不是预算截断，不是 STOP 请求，不是程序证据作废。为保护原边界预备的 57 分钟 STOP watcher 检测到执行自然结束后退出，没有写 STOP。未重跑或修改原始基线。

`actuators:stage_end` 中的 `completed_stage=setdown` 只表示该阶段的 actuator 审计收尾，**不等于放置技能成功**。原语义评分仅 `support_handled` 达成完整证据，其余任务链没有完成。

## 实际轨迹与计划对应

共记录 **21,712 个连续 20 ms 状态、86,844 个 5 ms 物理子步、434.22 秒仿真**。43 个关节有实际位置、实际力矩和每个记录区间的子步 position / velocity / effort extrema；原评分器判定安全覆盖完整、没有 gap、最大关节限位超出 0、最大 effort ratio 1.0、最大 speed ratio 0.068929。具体阈值与评分语义仍以冻结原始版本为准，不能套用扩展任务的新 D/Q 语义。

[计划—实测映射 JSON](baseline-execution-8034801.json.gz) 包含 4 个高层阶段 span、259 个事件到实测样本的锚点、118 个有生成时间和 duration 的低层计划段，并逐段保存端点关节状态。计划请求超出实际结束时间的区间明确标记未完整观测。这个映射是完整连续物理日志的索引，不是独立重放认证，也没有证明每个低层动作的所有前置条件与效果；`fine_grained_refinement_complete=false`。

## 证据位置

- [原始判决](baseline-evidence-8034801/verdict.json)、[原始记录元数据](baseline-evidence-8034801/recording.json)、[外层 receipt](baseline-evidence-8034801/receipt-result.json) 均原样保留。
- [源文件身份](baseline-evidence-8034801/source_manifest.json)、[原始事件流](baseline-evidence-8034801/expert-events.jsonl)、[完整 expert report 的本地归档与哈希](baseline-evidence-8034801/manifest.json)、[Slurm 原始输出](baseline-evidence-8034801/slurm.log) 可供审阅。
- [全量证据清单与 SHA-256](baseline-evidence-8034801/manifest.json) 指向本地完整归档，包含全部 trusted recording 状态/接触/actuator 记录、冻结源码、原始视频与报告；不是只保存最后一帧。
- 原始输出目录：`/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/baseline-packet/reproductions/gamma-fixed-8034801/`。
- 全量归档：`/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/baseline-evidence-8034801.tar.gz`。

后续如要修复 QP，应另建开发配置、记录参数差异并从原始初态重新运行；当前失败证据及原评分保持不变。当前没有新增完整 H1 成功，没有把失败证明成不可解。
