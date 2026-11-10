# G1 抱箱上下楼并在目标区放箱的 IK/FK 参考轨迹

参考路线为：**地面起箱 → 持箱接近楼梯 → 上 10 级 → 通过最高平台 → 从另一侧下 10 级 → 走到地面目标区 → 放箱、松手、站起 → 箱子留在地面，机器人稳定站立 2 秒**。
最高平台是必经检查点，地面目标区才是终点；未经最高处不能得分，详见[任务定义](../README.md)。

这是一条“实测起箱前段 + IK/FK 全身规划续接”的运动学参考。
视频通过 MuJoCo FK 回放位姿；完整路线尚未在 Genesis 中验证自由动力学执行，几何审计不等于任务成功。

2026-10-19 已完成[专家参考与评分器复核](SCORER_REVIEW.md)：修复四类评分边界问题，23 组逻辑回放全部通过。
该轮直接调用 worker 的关节跟踪诊断未成功起箱，完整物理正例缺失，不能宣称评分标准已完成物理标定。
新增[放箱段减速参考](runs/reference_up_down_place_retimed4x/validation_summary.json)，总长 519.97 秒，
近地速度与全部几何检查通过；原始参考和视频保留。机器可读汇总见 [scorer_calibration.json](scorer_calibration.json)。

后续新增[容器 oracle 验证](ORACLE_VALIDATION.md)：agent 正常读取六类传感器，通过公开关节接口跟踪参考；
可信端逐命令计算 reward，离线从真实物理记录重算。首次实跑已识别真实起箱，随后掉箱；失败奖励与 verifier 一致。
入口为 [`run_oracle.py`](run_oracle.py)，独立检查为 [`check_oracle.py`](check_oracle.py)。
机器可读结果为 [`oracle_calibration.json`](oracle_calibration.json)；未获得完整物理成功正例，准入状态仍为 false。

## 当前完整路线

完整参考已生成并通过独立几何审计，正式目录为 [`runs/reference_up_down_place`](runs/reference_up_down_place/)。终点阶段为
`place_lower → place_settle → place_release → place_retreat → stand_after_place → hold_placed`；
最后必须箱子落地、双手离开、机器人站起，不能以持箱停住代替放置。

- [`preview.mp4`](runs/reference_up_down_place/preview.mp4)：**6 倍速**完整路线预览，约 78 秒。
- [`motion.mp4`](runs/reference_up_down_place/motion.mp4)：按轨迹原始时间回放，约 7 分 47 秒。
- [`placement.mp4`](runs/reference_up_down_place/placement.mp4)：从原速回放的约 425.33 秒处裁出的终点放箱、松手与站起片段，约 41 秒。
- [`contact_sheet.png`](runs/reference_up_down_place/contact_sheet.png)：15 个关键帧，包括放箱、落地等待、松手、撤手与最终站立。
- [`trajectory.npz`](runs/reference_up_down_place/trajectory.npz)：带时间戳的机器人、箱子及足部参考。
- [`joint_targets.csv`](runs/reference_up_down_place/joint_targets.csv)：时间戳与 43 个关节角。
- [`audit.json`](runs/reference_up_down_place/audit.json)：独立 FK、碰撞、路线及放箱释放终点审计。
- [`rollout_summary.json`](runs/reference_up_down_place/rollout_summary.json)：起箱、上下楼、终点放箱和释放后站立的分段时间线。
- [`phases.json`](runs/reference_up_down_place/phases.json) 与 [`provenance.json`](runs/reference_up_down_place/provenance.json)：阶段时间与输入文件追溯信息。

轨迹共 **25,340 帧、466.63 秒**。独立审计的 **27,682 个加密样本全部通过检查**：
双脚依序覆盖上下楼踏面，经过最高平台，完整箱体和双脚最终均在地面目标区。
最终箱底落地，双手与箱体碰撞几何的最小间距约 **0.255 m**，没有手箱接触；机器人根高度 **0.757 m**，直立保持 **2.10 秒**。
足部 FK 最大误差 1.503 mm，重心参考误差 0.803 mm；参考关节速度不超过 1.5 rad/s。
这些结果验证几何参考，**不代表整条路线已经完成自由动力学执行**。

当前生成器默认规划完整上下楼和终点放箱。可使用 `--prefix-run` 复用已有运输轨迹，
从目标区继续规划放箱，从而避免重复求解已验证几何的前段；也支持复用上楼前段再续接下楼，使用 `--from-scratch` 则重新生成完整参考。
复用的是既有轨迹记录，完整路线仍需在包含下楼段的新场景中重新审计。

## 复用实验与规划方法

- `g1_support_retrieval/solution/carry_walk/runs/verified-script-test` 的 `joint_trace.npz` 与 `trace.json`：
  复用成功物理实验的 reach / close / lift / hold 前段（原实验 0–27.74 s），整体沿 x 平移 −1.4 m。
- `carry_walk/plan_walk.py` 及其 `carry_box/plan_carry.py` 基类：复用浮动基座全身 IK、关节限位与双拇指接触点几何。
- `step_up/constrained_step.py`：沿用转移重心、抬脚、前移、落脚的分阶段方法，为连续上楼和下楼重新求解。

抓持方式沿用已验证实验的双侧拇指夹持。起箱后将箱子抬至适合登阶的位置，再保持手臂姿态和手箱相对关系，求解腿部与根位置。
重心目标包含机器人和箱子的组合质量。规划按踏面安排左右脚落点，顶部经过双脚进入平台的检查点，再沿另一侧逐级下降。
下楼采用较短的 0.20 m 前进步长，后脚跟进时在抬脚段先前移最多 0.12 m，给摆动腿与支撑腿留出空间。
最后一级从 0.12 m 高踏面下降到地面，之后继续走至目标区。终点先保持双手夹持并降低箱子，
待箱子由地面承托后松手、撤开双手并站起，最后保持箱子落地且机器人直立。放箱段必须单独审计，不能直接以运输段的持箱检查替代。
放箱规划先调整足位，再倒序复用已接受的起箱位姿，并加入落地等待与最终站立保持；这是运动学位姿续接，不是倒放物理仿真。

## 场景与轨迹约定

本参考使用已验证搬箱实验的 **0.24 × 0.24 × 0.44 m、1 kg** 箱子，区别于任务默认的 2 kg 低箱。
每级高 0.12 m、深 0.40 m，最高处 1.20 m；顶层平台连接上下楼梯，目标区位于下楼后的地面。
完整配置保存在运行目录的 `config.json`。初始机器人 x 约为 0.85 m，箱子 x=1.15 m，是原实验平移后的起点。
这些参考位姿和负载参数不能直接代表默认箱子配置已通过物理验证。

`trajectory.npz` 的主要字段：

| 字段 | 形状/含义 |
|---|---|
| `time`, `phase` | 时间戳（秒）和阶段名称；按时间读取，不能假定统一采样间隔 |
| `qpos` | N×57，机器人根位置与四元数、43 关节、箱子位置与四元数；与同目录 `model.xml` 对应 |
| `qvel` | N×55，MuJoCo 广义速度布局 |
| `joint_pos`, `joint_names` | N×43 关节角（弧度）及名称，顺序与任务动作接口一致 |
| `root_pos`, `root_quat` | 机器人根位姿；四元数 wxyz |
| `box_pos`, `box_quat` | 箱子参考位姿；四元数 wxyz |
| `support` | N×2，计划的左右脚支撑标记，不是实测接触力 |
| `feet_target`, `hand_target`, `com_target` | 足部、拇指点及组合重心参考，供独立 FK 复核 |
| `com_includes_box` | 每帧重心计算是否包括箱子；释放后单独审计机器人站立，不能把组合重心诊断当作仍在负重 |

根位姿和箱子位姿是规划参考，不能作为机器人可直接执行的动作。
控制器需按时间戳插值关节目标，通过反馈控制跟踪，并重新检查真实接触、负载与平衡。
原录制前段保留原始时间；新规划段根据最大关节速度重新定时，目标上限为 1.5 rad/s。
任务当前时间预算为 600 秒；轨迹时长与几何检查不能替代真实接触驱动的成功判定。

## 生成、检查与回放

从 `robo-si/` 运行，使用现有 Genesis Python 环境中的 MuJoCo、SciPy、NumPy、Torch、Pillow 和 imageio：

```powershell
$py = 'D:/rsi_vla/genesis_env/Scripts/python.exe'
$out = 'humanoid/g1_box_stair_transport/solution/runs/my_up_down_place_trajectory'
$prefix = 'humanoid/g1_box_stair_transport/solution/runs/reference_up_down'
& $py humanoid/g1_box_stair_transport/solution/plan_trajectory.py --out $out --prefix-run $prefix
& $py humanoid/g1_box_stair_transport/solution/audit_trajectory.py --run $out
& $py humanoid/g1_box_stair_transport/solution/render_trajectory.py --run $out --fps 20 --preview-speed 6
```

需要重新求解前段时，将生成命令的 `--prefix-run $prefix` 换成 `--from-scratch`。输出目录必须为空，避免覆盖已有实验。

`audit.json` 从模型独立重算 FK，并加密检查关节范围、相邻变化、速度、足部支撑几何、手箱相对变换、碰撞、
上楼与下楼踏面覆盖、最高平台经过及地面目标位置；放箱参考还需验证箱底落地、释放后手箱分离和最终机器人站立。
审计只证明运动学和几何条件，不能证明摩擦、夹持力、关节力矩或动力学平衡。
原录制前段的软关节限位偏差使用 0.0001 rad 数值容差；碰撞穿透容差为 2 mm。

回放产物包括原速 `motion.mp4`、6 倍速 `preview.mp4`、`overview.png` 和 `contact_sheet.png`，视频标明
“IK/FK reference — not physics rollout”。失败尝试保留 `partial_trajectory.npz` 和失败原因，不作为完整轨迹；
可用 `--trajectory partial_trajectory.npz --preview-only` 检查失败前段。

## 历史参考

[`runs/reference_up_down`](runs/reference_up_down/) 保留旧版持箱到地面目标区的轨迹和视频：22,998 帧、425.33 秒。
当时的 25,340 个加密样本通过了运输路线几何审计，但终点仍持箱，没有放箱、释放和站起阶段，因此不满足当前任务终点。
它可作为新生成器的 `--prefix-run` 输入；新增放箱段与整个续接轨迹必须重新审计。

[`runs/reference_10_stairs`](runs/reference_10_stairs/) 保留旧版起箱到顶部的轨迹与视频：11,488 帧，约 220.29 秒。
该实验的 12,736 个加密样本通过了当时的上楼几何审计；它没有下楼和地面终点，不能单独作为当前任务的完整解。
其输出可作为完整路线生成器的 `--prefix-run` 输入。历史模型和结果保留原样；新的下楼续接必须使用当前完整场景并重新审计。
