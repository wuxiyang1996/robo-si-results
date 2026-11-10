# M2 固定第一层：完成证据与复现入口

2026-10-24。按本轮“先做这个，第一层即可”，范围限定为已实现的 **0.25 kg、2.25 × 0.35 × 0.24 m 长箱，1.8 m L 形通道，两台 G1**。

本轮新增[图文验收材料](presentation/index.html)与[离线阅读包](m2-layer1-review-20261024.zip)：沿用已发布 H4 报告的六部分结构，含高位跟随、固定全景、原始09录像对照、六阶段截图、审计快照、素材来源及未签署人审模板。渲染保留 Unitree 来源 G1 模型及 Poly Haven 木箱／墙面，新增库内混凝土贴图；按用户反馈恢复四面墙完整的 1.5 m 高度，通过抬高机位展示操作。从封存状态重建画面，不推进物理、不更改原判决。渲染与打包结果见 [presentation-package.json](presentation-package.json)。旧剖切版本单独保留为历史材料；本材料尚未发布，不构成正式入库。

**固定场景完整参考与公开命令回放已验证。** 09、10、11 三次参考均成功，09d 普通容器回放也成功。后三条记录此前留在 C 盘，因当时 D 盘容量不足未同步；本轮补齐归档、独立离线重评、动作边界和视频检查，并更新任务状态。没有启动新仿真，没有改控制器、物理、评分或监视阈值。正式准入仍为 `false`。

## 完整执行

| 运行 | 执行类型 | 分数／成功／VOID | 仿真时长 | 视频 |
| --- | --- | --- | ---: | --- |
| [09](../../sandbox/runs/bounded-reference-09/trusted/verdict.json) | 有界命令＋特权反馈参考 | 1.0／true／false | 175.28 s | [原始录像](../../sandbox/runs/bounded-reference-09/reference/motion.mp4) |
| [10](../../sandbox/runs/bounded-reference-10/trusted/verdict.json) | 同场景同种子独立启动参考 | 1.0／true／false | 175.28 s | [原始录像](../../sandbox/runs/bounded-reference-10/reference/motion.mp4) |
| [11](../../sandbox/runs/bounded-reference-11/trusted/verdict.json) | 同场景同种子独立启动参考 | 1.0／true／false | 175.28 s | [原始录像](../../sandbox/runs/bounded-reference-11/reference/motion.mp4) |
| [09d](../../sandbox/runs/bounded-rpc-replay-09d/trusted/verdict.json) | 普通 SDK／隔离容器／开环命令带 | 1.0／true／false | 175.28 s | 本次回放未录视频；记录状态与09逐项相同 |

全部无告警、无 flags。三次参考分数极差为 0，六阶段完成时间也相同：抓取 18.595 s、抬升 33.015 s、转弯 120.255 s、运输 154.845 s、下放 173.150 s、放置 175.170 s。原始录制结束于 175.28 s；末帧之外没有额外视频，不能重复末帧声称更多保持时间。

每次参考有 8,764 帧双机 LowCmd、35,056 个物理步进和 35,057 个 200 Hz 状态样本；全部导出 q/dq/kp/kd/前馈力矩及实际执行器力矩均在限制内，71 次物理参数检查不变，没有运行中状态写入。三次参考的状态、求解器快照、参数、命令和记录源码／资产完全一致。每条视频完整解码 878 帧，并逐帧匹配实际记录时间。

- [三次参考复核：每条15/15检查通过，重复比较通过](offline09/README.md)
- [普通容器回放：23/23检查通过](rpc09d/README.md)
- [转角关键帧](review/turn.jpg) · [放置关键帧](review/place.jpg)
- [未签署的人审模板](offline09/reference09-v2/human_review_template.json)

09d 的 88 个命令块摘要、181 条请求链和全部 8,764 个实际控制帧通过核对，没有裁剪或拒绝。agent/worker 均退出0；agent用时208.62 s，整次239.77 s，记录的agent预算为1,200 s。三次独立参考捕获的wall time为359.329／331.187／328.140 s；它们未走隔离agent预算验收，不能写成默认300 s预算的三次通过。

## 本轮机器检查

| 检查 | 结果 |
| --- | --- |
| M2 sandbox 测试 | 58/58通过 |
| M2 task／evaluator／controller 测试 | 27/27通过 |
| M2 admission 结构及证据路径 | 独立检查0问题，最终元数据另行校验 |
| 评分校准 | 22/22符合预期 |
| 历史 verifier 复核 | 24/24符合现行期望：7正例、5负例、2禁请求、10捷径案例 |
| 共享 runtime | **16/17通过**；全库 Records 检查因桌面装配任务17条证据路径缺失而失败 |

[原始测试日志与分组报告](cpu/report.json)、[历史校准与复核](cpu/historical_summary.json)、[全库路径故障清单](cpu/record_path_inventory.json)均保留。历史 kd60 参考得到状态评分不代表其动作合规；本轮只用09/10/11的单独动作审计证明公开动作限制。共享检查的失败没有被隐藏，当前全套 CPU/GPU/container 流水线也没有被标为全通过。

## 运行故障已保留

09b 的深层目录容器挂载读取失败，没有执行动作；09c 改用短 D 盘路径后执行至168 s，但磁盘写满，未完成封存；09d 使用短 C 盘工作区成功。历史对照支持采用短路径并先检查磁盘和实际挂载读取，但没有单独隔离出 Docker／Windows 的确切根因。

三个原始ZIP共约270 MB，原样归档于 [archives/](archives/)，包括冻结源码、成功运行和失败尝试。[transfer-receipt.json](transfer-receipt.json)记录306个展开文件及全部档案哈希；旧报告中的“待转移”字段作为历史保留，本收据记录转移已经完成。六份旧状态文档保存在 [prior_metadata/](prior_metadata/)。

## 复核和复现

离线审计脚本只读原始记录，新的结果必须写入新目录。运行方式见 [参考审计](offline09/README.md)和 [RPC审计](rpc09d/README.md)。第一次报告生成工具的 NumPy bool 序列化失败产物已明确标记；正式参考结果只使用 `reference09-v2`、`reference10-v2`、`reference11-v2`。

复现准备器从封存源码及公共包补充文件准备一个短路径工作区，验证203个核心文件、8个公共包文件和2个交付文件，拒绝路径越界或覆盖不同内容，并检查剩余空间。它只准备文件及命令，不自动启动模拟：

```powershell
# 在仓库根目录执行；新复现使用新的短路径。
& 'D:/rsi_vla/genesis_env/Scripts/python.exe' -B -X utf8 `
  'multi_robot/dual_g1_long_object_transport/acceptance/layer1-20261024/rpc09d/prepare_reproduction.py' `
  --workspace 'C:/Users/wuxiy/rsi_releases/m2_l1_repro_20261024'
```

本轮已准备该工作区并实际通过只读 Docker 挂载预检；[准备验证结果](rpc09d/preparation_validation.json)记录文件哈希和路径拒绝检查。工作区的 `reproduction_plan.json` 提供参考和RPC命令，保持原0.06 m到位偏移、50 Hz控制／200 Hz物理、公开限制和现有默认单槽队列。逐个执行，保留每次成功与失败；运行前另检查Docker存储和归档卷空间。完整依赖锁定不由三个求解器文件哈希代替。

## 范围与未完成项

[scope.json](scope.json)记录本轮范围。第一层目前仅是一个固定场景；0.20–0.30 kg及位姿变化仍是未采用的提案。这里没有把同一种子重复写成随机覆盖，也没有把固定命令带写成公共传感器反馈控制器。第二、三层、R9和原始9 kg任务延期，未被标记为通过。

正式入库仍需真实的人工录像／阶段标注和第二人复现，以及适用范围的覆盖、独立物理子任务起点、完整物理捷径与监视校准、资源计量和当前全套流水线证据。人审模板保持空白；`admitted=false`、`admission_eligible=false`，正式 `eval` 继续关闭。本轮没有提交、上传或发布。
