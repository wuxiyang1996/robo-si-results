# 装配专家控制与轨迹

控制器只输出 43 维绝对关节位置目标，使用真实刚体接触完成操作。开发环境固定 G1 骨盆，控制器读取关节状态与物体真值；不属于视觉策略或自由站立控制。

已验证轨迹：[expert_001](recordings/expert_001/summary.json)，115.67 秒、5784 步，完整成功且[独立动作回放通过](recordings/expert_001/replay/replay_report.json)。[视频](recordings/expert_001/video.mp4)与[NPZ 数据](recordings/expert_001/trajectory.npz)可直接查看和使用。

## 录制与回放

从仓库根目录运行：

```powershell
../genesis_env/Scripts/python.exe -m humanoid.g1_tabletop_assembly.solution.run_expert --prefix <工具阶段轨迹目录> --policy expert:parts_after_support --output <新输出目录> --video --replay
```

`--prefix` 从默认场景逐步执行已保存的关节目标；随后控制器切换到套筒和顶盖操作。每个阶段都等待物理评分器确认，不能通过策略声明跳过依赖。

`--replay` 重新创建默认场景，仅执行录制的动作。只有完整成功、阶段顺序一致、环境源码与配置一致、最终物体位姿在规定误差内，才设置 `replay_verified=true`。

| 文件 | 内容 |
|---|---|
| `trajectory.npz` | 50 Hz 关节目标、关节位置与速度、物体位姿与速度、接触状态、阶段和时间 |
| `trace.jsonl` | 初始观测，以及每个动作执行后的完整状态、接触力和控制阶段 |
| `summary.json` | 最终物理判定、阶段序列、力矩峰值、配置与源码 SHA256、状态写入审计 |
| `events.json` | 抓取、移动、松手、验收等控制器事件 |
| `video.mp4` / `final.png` | 使用 `--video` 时保存的 10 FPS 预览与最终场景 |
| `controller_sources/` | 本次运行使用的控制器源码副本 |
| `replay/replay_report.json` | 使用 `--replay` 时保存的独立回放结果 |

NPZ 的 `target_q[i]` 是从 `time_start[i]` 到 `time[i]` 执行的动作；同一行的状态是该动作执行后的结果。初始状态单独保存在 `initial_observation_json`。关节名称和物体顺序见 `metadata_json`。位置单位米、角度单位弧度，物体四元数顺序为 `wxyz`。终止动作可能少于一个完整的 20 ms 控制周期，应使用保存的时间戳。

```python
import json
import numpy as np

with np.load("trajectory.npz", allow_pickle=False) as data:
    metadata = json.loads(str(data["metadata_json"]))
    targets = data["target_q"]       # (T, 43)，绝对关节目标
    measured = data["joint_position"]
    stages = data["stage"]
```

## 证据边界

`runner_runs/`、`tool_runs/`、`parts_runs/` 和 `grasp_search_runs/` 保存开发实验，包含失败尝试与局部分段测试。不能把所有文件合并为成功示范。预置支撑块或零件的诊断明确标记 `object_pose_setters_used=true`、`robot_task_solution=false`。

完整专家必须由默认场景开始，审计确认没有机器人或物体状态写入，经历阶段 `0 → 1 → 2 → 3`，最终松手稳定两秒。应同时检查 `summary.json` 的 `full_task_success` 和独立回放报告的 `replay_verified`。
