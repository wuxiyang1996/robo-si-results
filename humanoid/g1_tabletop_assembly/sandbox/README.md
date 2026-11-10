# G1 工具辅助桌面装配：隔离评测沙箱

本任务的评测沙箱建在仓库统一运行时 [`infra/sandbox/`](../../../infra/sandbox/ONBOARDING.md) 上，与[汉诺塔](../../g1_tabletop_hanoi/sandbox/README.md)共用桌面层 [`humanoid/g1_tabletop/sandbox/`](../../g1_tabletop/sandbox/)。本目录只保留装配任务特有的部分。共享层的设计（环境视图、命令通道、状态日志、评分器回放、二值得分与交叉核对）详见汉诺塔沙箱 README 第 3、4 节，两任务完全相同，此处只写差异。

## 1. 文件

| 文件 | 作用 |
|---|---|
| `launch.py` | `SandboxTask` + 本任务选项（`--seed`、`--backend`、`--dev-resets`）→ `infra.sandbox.launcher.launch()` |
| `trusted/scenarios.py` | 密封场景：任务名义场景（铰接夹具初始 0.28 rad、支撑块、套筒、顶盖），时限 120 s；任务没有经验证的随机化器，评分模式重复同一密封 episode |
| `trusted/world.py` | 共享桌面世界 + `G1TabletopAssemblyGenesis(cfg=TaskConfig())`，物理不变 |
| `trusted/statelog.py`、`sensors.py`、`server.py` | 共享记录器（测量体：brace、sleeve、cap、fixture 平台）、G1 传感器、共享 worker 入口 |
| `trusted/scoring.py` | 回放 `task_spec.Evaluator` 的四个连续阶段值 + 独立终态检查 |
| `trusted/monitors.py`、`verifier.py` | 共享监视器套件与判定 |
| `trusted/record_reference.py` | `replay`（expert_001 的 `target_q` 经命令通道回放）、`live`（`run_expert.py`：前缀 `tool_runs/direct_09` + 策略 `expert:parts_after_support`，黑盒录制）、`exploit` |
| `agent_sdk/`、`tests/`、`../admission.json` | 同汉诺塔 |

## 2. 运行（仓库根目录；仿真经 GPU 队列）

```powershell
$py = 'D:\rsi_vla\genesis_env\Scripts\python.exe'
& $py -X utf8 -m humanoid.g1_tabletop_assembly.sandbox.launch task --mode dev --seed 1 --isolation process --no-video --name dev-hello --agent-dir humanoid/g1_tabletop_assembly/sandbox/agent_sdk/examples -- python hello_robot.py
& $py -X utf8 -m humanoid.g1_tabletop_assembly.sandbox.launch task --mode eval --agent-dir <交付目录> -- python solve.py
& $py -X utf8 -m humanoid.g1_tabletop_assembly.sandbox.launch task --mode grade --episodes 3 --agent-dir <交付目录> -- python solve.py
& $py -X utf8 -m humanoid.g1_tabletop_assembly.sandbox.trusted.record_reference replay --out <新目录>
& $py -X utf8 -m humanoid.g1_tabletop_assembly.sandbox.trusted.record_reference live --out <新目录>
& $py -X utf8 -m humanoid.g1_tabletop_assembly.sandbox.trusted.verifier --run <run>/trusted
& $py -X utf8 -m unittest humanoid.g1_tabletop_assembly.sandbox.tests.test_static humanoid.g1_tabletop_assembly.sandbox.tests.test_scoring humanoid.g1_tabletop_assembly.sandbox.tests.test_monitors
```

默认 CPU 后端（任务默认、参考录制所用）。

## 3. 与汉诺塔沙箱的差异

- 测量体 4 个：`brace`、`sleeve`、`cap` 与 `fixture`（铰接平台连杆，原点在转轴，即平台中心）。日志中的评分器输入包含 `fixture_contact`、`fixture_load_n` 等装配评分器读取的全部字段。
- 回合结束：评分器锁存（成功，或错序插入、工具支承失效 0.1 s、掉落、超时）。对 agent 同样只报 `task_ended` / `time_limit`。
- 阶段（`trusted/scoring.py`，只读回放的评分器内部状态）：

| 阶段 | 模式 | 权重 | 值 |
|---|---|---|---|
| `brace_supported` | once | 0.25 | 评分器 stage ≥ 1 → 1；之前 0.5 × 支撑块稳定保持比例（0.5 s） |
| `sleeve_seated` | once | 0.25 | stage ≥ 2 → 1；stage 1 时 0.5 × 套筒稳定保持比例 |
| `cap_seated` | once | 0.20 | 完整装配（支撑、套筒、顶盖均到位且全部释放）保持 0.5 s → 1；之前 0.5 × 该比例 |
| `assembled_released` | live | 0.30 | 评分器锁存成功 → 1；之前最终 2 s 保持比例 |

  得分为二值（`task.toml`: `partial_progress_is_score = false`）；`process_score` 仅诊断。
- 独立终态检查：平台水平（3°）且位于转轴；支撑块在目标位（0.012/0.020/0.004 m）且姿态端正；套筒、顶盖在柱上（相对平台的位置、高度、倾角）且矩形孔与柱的四角相容（90° 转角不通过）；四个体低速且无机器人接触。

## 4. 监视器与校准

监视器配置与汉诺塔相同（共享套件 + 桌面视图与几何；支撑面只有桌面与地面），阈值为共享默认值，物体能量缩小为窗口 0.3 J、作废 3 J（零件 0.12–0.35 kg，平台 1.2 kg）。已记录 episode 的最大值（各 verdict 的 `monitor_metrics`；全部无报警）：

| episode | 物体速度 m/s | 单步速度 m/s | 支撑穿透 m | 无功能量 J | 手指反转 Hz | 手臂抖动 | 饱和 s | 顶限位 s | 进度尖峰 |
|---|---|---|---|---|---|---|---|---|---|
| 阈值 | 9 | 20 | 0.03 | 0.3 | 8 | 3.0 | 3 | 2 | 0.25 |
| replay-expert_001 | 0.838 | 0.936 | 0.001 | 0.001 | 1 | 0.096 | 0 | 0 | 0 |
| live-expert | 0.838 | 0.936 | 0.001 | 0.001 | 1 | 0.096 | 0 | 0 | 0 |
| dev-hello / eval-hello / grade-noop | 0.123 | 0.123 | 0.001 | 0.001 | 0 | 0.045 | 0 | 0 | 0 |

合成攻击（`tests/test_monitors.py`）全部触发：瞬移、抛射（窗口 / 作废）、顶盖陷入桌面（窗口 / 作废）、无功升高（窗口 / 作废）、手臂与手指抖动、饱和与顶限位、进度尖峰、阶段乱序、不可行声明、特权写入与超界增益；最终保持期间的手臂抖动窗口使成功不被计入。

## 5. 参考专家证据

| 运行目录（`runs/`） | 方式 | 判定 | 与原录制比较 |
|---|---|---|---|
| `reference/replay-expert_001` | `expert_001/trajectory.npz` 的 `target_q` 经命令通道回放，含 `motion.mp4` | 成功，无报警 | 5784 控制步、115.67 s；阶段转换 55.68 / 86.72 / 115.67 s 一致；四个测量体位置最大差 0.0 m，终态差 0.0 m |
| `reference/live-expert` | `run_expert.py`（前缀 `tool_runs/direct_09` + `expert:parts_after_support`）黑盒运行，外挂记录器 | 成功，无报警 | 同上，逐位一致 |
| `exploits/teleport-sleeve` | 真实攻击：保持 1 s 后可信侧 `set_pos` 把套筒瞬移到柱上 | **VOID**（特权写入、瞬移、速度、无功能量） | — |

`expert_001` 录制之后 `g1_tabletop/genesis_env.py` 有改动（源哈希 298a39ce → 86cd6b5d，加入汉诺塔的摩擦选项），但装配场景的设置未变：回放逐位一致。每个参考 episode 中回放的评分器与实时评分器在同一控制步锁存成功，独立终态检查一致，特权写入为 0。

## 6. 验证记录（2026-10-21）

| 检查 | 运行目录（`runs/`） | 结果 |
|---|---|---|
| 单元测试 | — | 38 项通过（static 9、scoring 17、monitors 12） |
| 开发冒烟（进程隔离） | `dev-hello` | 非 VOID，0 分；哈希链完整 |
| 容器评测 hello | `eval-hello` | 非 VOID，0 分 |
| 逃逸探针 | `escape` | 38/38 符合预期，17 次接口违规，**VOID** |
| 评分模式 no-op | `grade-noop` | 2 个密封 episode，各一次连接，0 分，非 VOID |
| 开发重置 | （进程内冒烟） | `reset` 恢复初始姿态，两个 episode 均可判定 |
| 参考录制 | `reference/*` | 见第 5 节 |
| 重新判定 | `validation/` | 当前 verifier 重新判定全部运行与参考 episode，与启动时的判定一致（`validation/summary.json`） |
| 准入记录 | `../admission.json` | `python -m infra.sandbox.records` 无问题 |

## 7. 缺口与待定

- 没有随机化器：每个评分 episode 都是名义场景，参考专家只有一条轨迹。随机化方案已由作者确定（2026-10-21，见任务 [README「场景随机化方案」](../README.md#场景随机化方案)），尚未实现；前提是先把专家的开环工具阶段改为闭环。
- 只在 CPU 后端验证了逐位复现；GPU 未验证。
- 人工阶段标注、视频签审、捷径审计、第二人复现、自动流水线未完成。
- 共享运行时问题同汉诺塔 README 第 8 节（未修改）。`task.toml` 的沙箱字段属于任务作者，未改动。
