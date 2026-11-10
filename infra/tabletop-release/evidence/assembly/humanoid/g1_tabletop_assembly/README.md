# G1 基础桌面装配 0.3：第一层候选

本版只含铰接平台、基础支撑工具、套筒和顶盖；评测入口拒绝第二、三层，不生成远端重块或固定干扰块。机器人为固定骨盆的 Unitree G1，带 Dex3 双手，43 维关节目标通过固定增益、限幅力矩 PD 执行。物理频率 200 Hz，控制频率 50 Hz，回合上限 120 秒。公开目标见[中文指令](instruction.zh.md)。

## 物理评分

平台先由已释放物体稳定承托 0.5 秒；套筒正确装入并释放稳定 0.5 秒后，顶盖才能装入。最终全部物体脱离机器人接触，结构低速稳定 2 秒。只有完整成功得 1 分，阶段进度不计分。

实际载荷路径为“桌面 → 一个或多个已释放承载物体 → 平台 → 套筒 → 顶盖”，有效向上接触力须大于 0.05 N。评分不限定支撑物体身份、摆放点或指定路线。全部承载分支都须接地；悬空循环、手持分支、未知承载体、零力和缺测量不能通过。沙箱另用自底向上的承载图复核终态。

平台倾角上限 3°、零件倾角上限 5°，线速度/角速度上限为 0.025 m/s、0.15 rad/s；孔柱几何、顺序、掉落和稳定时间均保留。连续 0.1 秒失去已建立的支撑资格会失败。

## 随机化与轨迹

grade 始终使用第一层；启用 `--randomized` 后按种子和回合随机化，默认仍为名义场景。精确范围见 [randomization.py](randomization.py) 的 `RANGES`；厘米级位置变化、yaw ±0.03 rad、质量 ×0.9–1.1、摩擦 0.65–0.8、铰链阻尼 0.04–0.10 保持原值。固定的五个种子、两个边界及一个名义场景共 8 个输入全部保留，有限覆盖不认证所有连续组合。身体变化仍为未全面认证的显式开发选项。

[覆盖结果](acceptance/first_layer_20261023/coverage/summary.json)和[第一层训练数据](acceptance/first_layer_20261023/dataset/manifest.json)属于本版本。训练数组与封存测量逐项核对，动作按实际 servo 的 float32 转换比较；数据含开发真值，不含 RGB。错序反例及独立沙箱回放保存在 `acceptance/first_layer_20261023/shortcuts/cap_before_sleeve/`。

## 验证范围与验收

本版本只交付第一层。`release.scope=first_layer`、`released_layers=[1]`、`main_benchmark_included=false`；范围来自用户原话“我们两个任务都先只做第一层”。[范围记录](acceptance/first_layer_20261023/scope_decision.json)不代表人工验收。

冻结输入、全部成功和失败记录、封存测量及完整记录状态录像均保留。参考控制器可以读取开发真值，仅证明物理可行性，不构成受限传感器 agent 成绩。5 Hz 测量快照视频用于查看记录，独立物理回放另有报告和录像。

[自动审计](acceptance/first_layer_20261023/automatic_audit.json)核对覆盖、同一输入三次全新执行、独立物理与沙箱动作回放，以及两个释放子目标。子目标统一允许在原回合上限内执行录制后缀后，最多保持最后关节目标 1 秒；严格后缀的原始结果仍保留。这不声称恢复求解器全部内部状态。

[复核入口](acceptance/first_layer_20261023/review/index.html)提供逐场景复现命令、录像和空白签审表。[最终流水线证据](acceptance/first_layer_20261023/final_pipeline_evidence.json)记录 CPU、物理、容器全量检查的实际结果。人工录像/阶段标注、第一层捷径签审和第二人独立复现仍待完成，`admitted=false`；仅剩这些项目时按用户决定暂缓发布。

规则依据：[验收规范](../../infra/acceptance-zh.html)第 03–05 节。旧的高层候选完整保存在原候选工作区，不作为本版本证据。本版不认证完整三层工具设计，R9 高层设计资格不属于本版范围。

## 复现检查

在本候选工作区根目录执行：

```powershell
python -X utf8 -m infra.sandbox.pipeline humanoid/g1_tabletop_assembly --tier all
python -X utf8 -m infra.sandbox.release_check humanoid/g1_tabletop_assembly --scope first_layer
```

人工验收前第二条命令应返回 `NOT READY`。受限 agent 的运行方式见 [sandbox/README.md](sandbox/README.md)。
