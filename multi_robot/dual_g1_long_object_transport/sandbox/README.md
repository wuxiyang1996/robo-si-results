# 双 G1 地面搬运基础设施

**2026-10-24 当前状态：**固定第一层的 09/10/11 有界动作特权参考均为 1.0；09d 普通容器回放也为 1.0，全部记录状态与 09 相同。C 盘后续记录现已校验归档，入口见[第一层证据包](../acceptance/layer1-20261024/README.md)。下面的 02/03 等记录是历史过程。正式 `eval` 仍关闭，人工验收与第二人复现未签署。

按 [`infra`](../../../infra/README.md) 的可信侧记录、独立阶段评分、容器隔离与正反例校准组织。
任务合同见 [TASK_CARD.md](../TASK_CARD.md)，机器规格见 [task.toml](../task.toml)。
这是固定轻箱场景的开发评测实现；正式入库缺项在任务卡中明确列出，`eval` 当前拒绝启动。
Historical privileged kd60 references and earlier regression/calibration results are in [VALIDATION.md](VALIDATION.md). Current bounded-reference and replay outcomes are reported below.


## Release candidate update, 2026-10-22

See [RELEASE_CANDIDATE.md](RELEASE_CANDIDATE.md) for the current author route decision, bounded command-interface validation and blockers by type. Wall-contact-free alternative routes are allowed under existing constraints; no planar containment rule is added. Bounded privileged-feedback capture02 reaches 1.0 but retains an uncaptured-setter limitation. Capture03 uses RPC initialization and suppresses checked identical setters; it fails at 0.5165 after coordination loss at 178.88 s. Its ordinary container replay03 scores the same 0.5165 and exactly reproduces all recorded states, solver snapshots and parameters across 8,944 executed commands; this is reproduction of a failed trajectory. The original global source-freeze flag remains false solely for an admission.json wording/evidence update during replay, with runtime dependencies unchanged. Ordinary fixed-command reproduction is separate from the permitted privileged-feedback reference gate; open-loop success is not an extra admission requirement. Both evidence types and the governing records.py/ONBOARDING guidance are linked in the release report.

## Acceptance continuation, 2026-10-22

See [the consolidated evidence and limitations](ACCEPTANCE_2026-10-22.md) and the [unimplemented randomisation/coverage proposal](RANDOMISATION_PROPOSAL.md).

| Gate | Current conclusion |
| --- | --- |
| automatic_pipeline | partial: recovered full CPU 6/6, GPU 1/1, container 4/4; fresh selected CPU 4/4; no automatic trigger |
| grading_mode | passed for the fixed-scene lifecycle: two sealed episodes, fresh container/workspace each, 1 s default hold scores 0/non-VOID; not a formal result |
| predicate_labels | partial: two available success videos have stage sheets and an unsigned review template |
| shortcut_audit | partial: two physical probes and eight synthetic state cases; complete solo/over-wall physical routes untested |
| verifier_validity | partial: over-wall route allowance clarified by author; G2/E2 authorized and implemented with focused regressions; physical strategy and full interface evidence remain open |
| coverage / randomisation | pending: proposals only |
| video_review / independent_reproduction | pending: no signed human review or second-person reproduction |

Fresh checks: 17 shared-runtime tests, 27 sandbox tests, 19 task regressions, admission schema with zero problems; offline recheck 7 positives, 5 negatives, 2 forbidden probes and 10 current-rule shortcut expectations. Known contract mismatches are not converted to passes. [Selected CPU record](../acceptance/pipeline/20261022-211602-cpu.json).

The prior session changed RPC pelvis initialization from 1.5772 to 0.7842 m to match reference start height. This is a change to historical RPC sealed state, requires author review, and does not prove full reference/RPC equivalence. G2/E2 now separate authenticated finish and normal simulation limits from attributable agent errors and integrity VOID; see AUTHOR_RULES_2026-10-23.md. Historical verdicts are retained. Source hashes, limitations and author decisions are in the consolidated report. All verdicts remain admission_eligible=false; eval stays closed; pre-admission grade is available in addition to dev.

## 入口

在 `D:\rsi_vla\robo-si` 下执行。启动器、worker、容器、请求日志、记录格式和 run 级评分都是共用运行时
[`infra/sandbox`](../../../infra/sandbox/ONBOARDING.md)；M2 只保留固定场景、双机世界适配、记录行和评分。

```powershell
$py = 'D:\rsi_vla\genesis_env\Scripts\python.exe'
$queue = 'C:/Users/wuxiy/AppData/Local/Temp/claude/d--rsi-vla/2f795ddc-4e2e-4209-82f7-00dd0d1f3417/scratchpad/unify/tools/gpu_queue.py'
$env:INFRA_GPU_QUEUE = $queue
# 专家物理执行（维护者专用特权参考），共用格式记录、自动独立评分
& $py -X utf8 $queue -- $py -X utf8 -m multi_robot.dual_g1_long_object_transport.sandbox.record_expert --out multi_robot/dual_g1_long_object_transport/sandbox/runs/my-expert --fixed-armature --video
# Container dev submission (pre-admission fixed-scene grade is also available); runs: sandbox/runs/<name>/
& $py -X utf8 $queue -- $py -X utf8 -m multi_robot.dual_g1_long_object_transport.sandbox.launch --mode dev --name my-noop --agent-dir multi_robot/dual_g1_long_object_transport/sandbox/agent_sdk/examples -- python solve.py
# --vision 加头部 RGB-D；隔离检查：入口换成 python probe_isolation.py；越权反例：python probe_forbidden.py，预期 VOID/0
# 重新评分：一个运行目录 / 一条记录
& $py -m multi_robot.dual_g1_long_object_transport.sandbox.trusted.verifier multi_robot/dual_g1_long_object_transport/sandbox/runs/my-expert/trusted
& $py -m unittest multi_robot.dual_g1_long_object_transport.sandbox.tests.test_infra
```

2026-10-21 起的新记录使用共用分块格式（`episode_00/` 下 meta.json、world_params.npz、state/snapshots 分块、events.jsonl、
recording.json、files.json）；此前的记录（states.jsonl.gz + manifest.json）仍按原格式验证。

`trusted/` 保存密封场景、200 Hz 状态与接触、10 Hz 全场位置/速度快照、物性核对、请求摘要链、
文件清单和 `verdict.json`。这些目录不挂载给 agent。SDK 只有传感器和关节控制接口，另附机器人模型和通用 GR00T 运动工具。
`--isolation process` 只供本地调试，不提供恶意代码隔离。

`record_expert` 是维护者专用特权参考入口，不能向这里传入不可信 agent 脚本。
它复用与 RPC worker 相同的 `Recorder` 和 `verifier`。专家能读真值；普通提交不能。
运行期间 robot/object 状态 setter 会被记录；质量、摩擦定期核对，实际关节控制力矩独立检查。
原专家进入行走时改变 motor armature 的遗留行为单独标记；新参考用 `--fixed-armature` 开局固定物性。
正式任务验收仍需任务卡列出的随机层验证、RPC 等价复核和人工检查。

## 校准结论如何阅读

[calibration.json](calibration.json) 分开保存真实历史运行与合成破坏测试。
对照预期：完整参考满分；空操作、无接触、只有单机接触为 0；只抬起为 0.30；
到达未放下为 0.70；放下后出目标区未松稳可以保留 0.85；最后保持不足 2 秒不能判成功。
阶段连续分可以接近 1，所以不能把 `score > 0.99` 当成成功。
`success` 与分数单独报告，原始控制器 `task_success` 不参与判定。

哈希清单用于检测可信目录意外损坏，不是签名认证。不要接受任意用户上传的“trusted”目录。
自动测试不替代人工视频标注，不把固定 seed 的三次重跑当成三层随机验证。
