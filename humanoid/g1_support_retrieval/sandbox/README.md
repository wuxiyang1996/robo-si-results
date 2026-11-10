# G1 支撑取物任务的隔离沙箱

<a id="stool_relay-v20"></a>

## stool_relay v2.2（relay-rubric/2.2：加入安全规则）

新完整任务入口为 `relay`；规格与验收范围见 [TASK_CARD.md](../TASK_CARD.md)、
[task.toml](../task.toml) 和 [readiness.json](../acceptance/readiness.json)。
后文原 `task` / `official` 入口继续用于旧五类箱式环境。

从仓库根目录运行以下命令。`relay_noop.py` 会读取全部机载传感器、发送 2 秒保持指令并结束，
预期任务分为零；用于检查真实仿真、容器、日志和评分链路。

```powershell
python -m humanoid.g1_support_retrieval.sandbox.launch relay --mode grade --episodes 3 --layers 1 2 3 --seed 17 --isolation container --agent-dir humanoid/g1_support_retrieval/sandbox/agent_sdk/examples -- python relay_noop.py
```

开发自己的程序时，将 `--agent-dir` 指向独立交付目录，末尾换为 `-- python agent.py`。
`--mode dev` 允许有限次原始场景 reset；开发墙钟默认不设上限。评分默认每次执行 180 分钟，
模拟时间上限 1200 秒，两者分别记录。正式评测必须使用容器，禁止 LLM 网络和中途快照起步。

固定工程场景可用 `relay --mode dev --profile reference_v15 --seed 2`；它保留原红、绿箱布局，
不代表随机第一层的验收。三层随机场景用 `--layer 1/2/3`，能力披露另用
`--capability-tier explicit/partial/latent`，两者独立。

可信证据新增实际物体/板面/地面接触、脚底几何与每个 5 ms 物理步的执行器极值。
完整接力 `chain_complete`、终局交付 `success` 和过程分分别报告。越权、证据缺失、日志损坏、
物理执行器越限返回零分 VOID。失败和空操作轨迹也保留视频与日志。

参考录制器直接记录专家当前执行的物理状态，不把旧事件报告转换成接触证据：

```powershell
python humanoid/g1_support_retrieval/scripts/run_relay_reference.py --out <new-output-directory>
```

[完整录制 c](../acceptance/reference_c.json)已在原始起点连续执行后获得 1.0、success 和 chain_complete；实际覆盖 170052 个物理步，冻结评分器重判一致。主仓库 322 项回归通过。[快速录像](../media/stool_relay_c/motion-24x.mp4)保留完整时间范围。它仍是一次固定场景特权参考，不代表三层或重复性验收。

### 安全规则（relay-rubric/2.2，2026-10-21）

作者的五条安全规则已实现于 [relay_safety_rules.py](trusted/relay_safety_rules.py)，并追加在 agent 看到的
instruction 末尾（[SDK 说明](agent_sdk/README.md)“Safety rules”一节同文）。任一安全事件使 `success` 与
`chain_complete` 为 false，过程分保留，不判 VOID，事件逐条写入回合结果的 `safety_events`（规则、种类、时间、
实测值、阈值）；评分模式的每回合汇总也列出事件种类。阈值与校准见 [TASK_CARD.md](../TASK_CARD.md)“安全规则”和
[safety_rules_calibration.json](../acceptance/safety_rules_calibration.json)（由
`python -X utf8 humanoid/g1_support_retrieval/acceptance/calibrate_safety_rules.py` 重新生成）。

- 规则 5 使用共用命令模式监视器。共用的跌倒前截断把骨盆倾角 >50° 当作跌倒，c 在 32.6 s 的缓慢深弯之后
  818 s 不再检查；h1-monitors/2 改为只排除 H1 自己的跌倒前 1 s。由此 c 出现腰俯仰关节 50 N·m 额定处连续
  4.5 s（85.3 s）与 6.1 s（480.3 s）的饱和：**c 在 2.2 下得分 1.0、接力链实际完成，但 success=false。**
  阈值未为 c 调整，由作者决定。
- 物理攻击与探针（可信侧，[exploits.py](trusted/exploits.py)，一次密封 grade 世界，按 `verify_episode` 判定）：

```powershell
python -X utf8 -m humanoid.g1_support_retrieval.sandbox.trusted.exploits run --seed 7 --tag v1 --kinds jitter tip teleport mass
python -X utf8 -m humanoid.g1_support_retrieval.sandbox.trusted.exploits run --seed 7 --tag v2 --kinds lean
python -X utf8 -m humanoid.g1_support_retrieval.sandbox.trusted.exploits judge
```

  结果（[summary.json](runs/exploits/summary.json)）：`teleport-v1` 目标瞬移进目标区 → VOID（state_teleport、
  teleport 164.6 m/s、object_speed_severe）；`mass-v1` 目标质量 ×10 → VOID（第 10 s 周期检查记录
  world_params_changed，回合级判 VOID）；`jitter-v1` 双臂 5 Hz 抖动 → arm_shaking 告警（时间窗），零分；
  `tip-v1` 双踝前推整体前倒 → near_fall_tipping（2.66 s，倾角 0.25 s 内增 42.9°）、单脚失载倾斜、骨盆骤降，
  2.88 s 跌倒；`lean-v2` 面对柜体前倒、躯干靠在柜上 → cabinet_climb（0.25 s 均值 102.9 N，随后持续约 90 N）与
  near_fall_tipping，非 VOID；`lean-v1`（离柜 0.42 m、默认手臂姿态）手指先扶住隔板、被压过限位 12.9 mrad 而判 VOID，
  已被 lean-v2 替代。
- 旧五类评分的 `target_reached` 改为必须有 ≥2 N 手接触；官方锚点不变（step_up 0.25、push_box 0.33），见
  [重评记录](../acceptance/regrades/target_reached_contact_20261021/summary.json)。

可加 `--smoke-seconds 1` 检查录制接口；该输出会明确标记 diagnostic_only。
专家仍使用特权真值；它改走 agent 指令通道后的结果见下一节。恢复子任务时要求相同世界拓扑、物理参数、
元数据、快照哈希与有效时间；旧 oracle `.pkl` 和不同场景日志不会被直接当作有效起点。

### 参考专家经 agent 指令通道运行（动作通道一致性，2026-10-21）

canonical c 的专家 `oracle/stool_chain.py` 原来在进程内直接读写 Genesis。现在它作为程序跑在**参考容器**里：
每个动作都是一条 agent 用的 LowCmd `command`（steps=1，经同一套校验、增益上限和力矩截断），它需要的真值只来自
启动器密封的特权参考通道。做法照搬 H3（`g1_self_closing_door/sandbox/reference/`）：

```powershell
python -m humanoid.g1_support_retrieval.sandbox.launch relay --mode eval --profile reference_v15 --seed 2 --reference --budget-min 600 -- python -m humanoid.g1_support_retrieval.sandbox.reference.run_reference
```

- `--reference` 密封 `reference_channel=true` 的场景（只能是 relay、eval、1 个回合；固定场景 reference_v15 只在这种
  参考运行里允许离开 dev），worker 只在这种场景里多提供 `reference_info`、`reference_state`（普通运行里调用即违规），
  每次调用都记入哈希链请求日志并标 `privileged_reference`，`server_summary.json` 记调用次数；verdict 标
  `privileged_reference: true`，`result_kind` 写明不是 agent 结果；verifier 把这两个方法算作该运行的闭环读取。
- 参考 bundle `runs/_refbundle-<hash>/`（`launch.REFERENCE_FILES`）只含专家代码闭包、它读的数据文件（Agile 权重、
  凳与柜的 meta、SONIC 姿态）、G1 模型和适配器；可信沙箱代码、评分器、场景、仿真后端都不在内。c 之后改过的两个模块
  （`oracle/navigation.py`、`solution/step_up/contact_wbc.py`，H5 的新增项）取自 c 的冻结副本
  `reference/frozen_c/`；构建时 bundle 里凡是 c 归档过的文件（27 个）都按 c 的 `source_manifest.json` 逐个核对哈希，
  不一致即拒绝构建。镜像 `g1h1-reference:<hash>` = agent 镜像 + torch 2.11.0 CPU、osqp 1.1.3、imageio-ffmpeg 0.6.0
  （与宿主版本相同），运行时同样是 uid 1000、只读根文件系统、内部网络。
- `reference/remote_env.py` 是 Chain.build 场景和专家用到的全部 Genesis 实体方法的替身；`reference/run_reference.py`
  用 c 的命令行（去掉 `--save-checkpoint`）运行原专家，只替换场景，开局核对专家解析出的 96 项配置与 c 的
  `config.json` 一致；`reference/compare_c.py` 在可信侧逐控制步比较运行日志与 c 的可信录制。

**仿真器访问清单与对应通道**（静态检索专家闭包 + 适配器运行时逐方法计数）：

| 专家的访问 | c 里 | 通道运行里 |
| --- | --- | --- |
| 场景构建：房间、柜、箱、折叠凳实体，物理开关（自碰撞/扭转摩擦/椭圆摩擦关），机器人 armature/阻尼/摩擦 | Chain.build 自建场景 | 可信 world 构造时完成（RelayEnv reference_v15）；`reference_info` 给出物理开关，runner 核对与专家参数一致 |
| 初始摆放：机器人根位姿、43 个关节、折叠凳位姿（凳质量 1.5 kg 与 meta 相同，c 未写） | `place_initial` 的 set_pos / set_quat / set_dofs_position | 不发送；适配器核对与密封初态一致（误差 0 / 7.5e-9 m），不一致即停止（`UnavailableWrite`） |
| 关节增益 set_dofs_kp/kv：腿 3000/40，腰 5000/5（起凳、站起、放凳时腰俯仰 kd 40），臂 3000/10，手 20/2 | 运行中写 Genesis | 每条 LowCmd 的 kp/kd（伺服关节）；全部在 GAIN_BOUNDS 以内 |
| 位置目标 control_dofs_position | Genesis 隐式 PD | mode 1 伺服，q* |
| 接触 QP 腿力矩 control_dofs_force（登凳、凳上、下凳、带凳行走） | 力矩模式 | mode 0，kp = kd = 0，tau |
| env.step（Agile 行走、地面重取、送箱） | 腿：DC 电机 PD（kp 100/200/20，kd 2.5/5/0.2/0.1）每子步重算；上身伺服 | 腿 mode 0（同样 kp/kd，dq* = 0），上身 mode 1 |
| set_dofs_force_range | (a) ±物理额定；(b) 每个 5 ms 子步按关节速度重设腿的 DC 电机包络 | (a) 等于通道力矩上限，无需发送；(b) 力矩关节在第一个子步按包络预截断；伺服关节无法表达（通道伺服的力范围固定为额定），只统计 |
| scene.step()（5 ms 子步） | 直接推进 | 每 4 次合成一条 command(steps=1)；其余 3 次不推进，期间专家的改动只统计 |
| 读：基座位姿与速度、关节 q/dq、实际关节力、连杆位姿、连杆净接触力 | Genesis getter | `reference_state`（float32 原值） |
| 读：凳/箱位姿与速度；接触（机器人-凳、机器人-箱、凳的全部、机器人的全部） | getter、get_contacts | `reference_state` 的物体状态和全场接触表；适配器按 Genesis 相同的 geom 区间掩码重建 get_contacts |
| 读：机器人连杆质量/质心/惯量、连杆描述（惯性系、偏移、足底球）、场景连杆名 | sync_planner_model / model_audit | `reference_info` |
| 任务核心：目标、柜型、层高、goal、in_goal，env.step 返回的成功/跌倒 | env.core | 适配器本地 TaskCore（与 Chain.build 同配置、种子 2），开局与 worker 的核心逐项核对 |
| 静态场景知识：柜体碰撞盒、凳几何、箱尺寸、goal 中心 | task_spec、assets meta | 参考 bundle 里的文件（agent bundle 没有） |
| 相机 set_pose / render、专家自录视频、检查点保存 | 渲染、序列化 | 空相机；motion.mp4 由可信 worker 录制；不保存检查点 |
| 运行中 agent 做不到的写入（位姿、质量、摩擦、reset） | c 声明除初始摆放外没有 | 未发现：适配器对这类调用一律拒绝，运行中 0 次 |

**命令在通道里的表达方式（只改适配器，专家代码、通道限幅、物理参数都不变）**：

1. 每 4 次 `scene.step()` 合成一条 `command(steps=1)`，即 50 Hz 零阶保持；c 在一个控制步的 4 个子步里位置目标、
   QP 力矩和增益本来就不变（全程统计：子步之间这些量的改动 0 次）。
2. DC 电机力矩-速度包络：力矩关节按第一个子步的包络预截断；伺服关节和 env.step 的腿 PD 无法表达包络（通道只按额定
   截断）。全程统计：专家要求的力范围从未窄于额定，力矩从未贴着包络，实际施加的力矩从未超出 c 会允许的范围（0 次）。
3. env.step 的 DC 电机腿：mode 0，kp/kd 与任务相同、dq* = 0，通道每个物理子步按同一控制律重算，只缺上面的包络。
4. 力矩模式关节的 q 字段填实测关节角（kp = kd = 0，不起作用），只为通过通道的限位校验。
5. 初始摆放只核对、不发送；专家自录视频换成帧计数器；专家归档自身源码只拷内容（容器挂载不允许 copystat），
   bundle 外的 `genesis_env.py`、`cabinets.py` 跳过；不保存检查点。
6. 专家在容器里用 CPU（torch CPU）和 Linux 的数值库计算。

通道本身的差异（增益上限、控制频率、每次调用的步数、延迟、模式语义）都没有造成影响：增益全部在上限内，worker
没有截断任何字段（kp/kd/tau/q 截断计数 0），控制频率与 c 相同（50 Hz），每条指令 1 步，指令同步执行
（worker 一步中位 16.6 ms，`reference_state` 5.5 ms），唯一的语义差异就是第 2 条的包络，全程未起作用。

**结果**（`runs/` 下；compare_c 与 summary 文件在对应运行目录里）：

| 运行 | 内容 | 结果 |
| --- | --- | --- |
| `refdev-plumb-1`，本机进程隔离 | 2 s 冒烟 | 100 条指令、102 次真值调用；初始摆放与密封初态误差 0（凳 7.5e-9 m），任务核心逐项一致，配置与 c 相同 96 项；按共用规则判 VOID（评测模式不认进程隔离），这是预期的 |
| `refdev-smoke-host-1`，本机进程隔离（与 c 相同的 Windows 数值库） | 140 s 冒烟：接近、起凳、站起、开始带凳行走 | 与 c 的可信录制逐控制步对比（[compare_c.json](runs/refdev-smoke-host-1/compare_c.json)）：前 60 s 骨盆偏差 ≤14 µm、关节 ≤2e-6 rad，凳 0；接触密集的起凳开始后才分开（关节偏差首次 >0.05 rad 在 80.3 s，凳 >1 cm 在 82.5 s），140 s 时骨盆 3.9 cm、凳 3.4 cm。专家事件到第一步与 c 相差 0.0–0.1 s，140 s 内 ≤3.0 s；`support_handled` 81.90 s（c 82.24 s）；规则 5 腰俯仰饱和 3.9 s @84.7 s（c 4.5 s @85.3 s）。VOID 原因同上 |
| `reference-smoke-1`，参考容器 | 140 s 冒烟 | 非 VOID，privileged_reference。专家在 Linux 上规划出的接近过程只有 14.1 s（c 73.0 s，见下），此后各阶段时长与 c 相差 ≤0.1 s（起凳到稳持 8.04 s，站起到稳持 59.0 s 偏移不变），140 s 内全部专家事件顺序与 c 相同 |
| **`reference-full-1`，参考容器** | **完整接力，c 的冻结配置** | **非 VOID，privileged_reference，得分 0.9999，专家自评 success（箱子在目标区静置、双手离开）；物理结局复现 c**。40960 条指令、40962 次真值调用、0 次 observe、0 次违规，模拟 819.2 s（c 850.26 s），墙钟 2.41 h（c 1.24 h）。详见 [summary_vs_c.json](runs/reference-full-1/summary_vs_c.json) |

完整运行的阶段时间（2.2 判据）与 c 对比：

| 阶段 | 通道运行 s | c s | 差 |
| --- | --- | --- | --- |
| support_handled | 22.80 | 82.24 | −59.4 |
| support_relocated | 456.14 | 519.10 | −63.0 |
| on_support | 601.88 | 655.96 | −54.1 |
| target_secured | 628.74 | 680.82 | −52.1 |
| target_staged | 650.82 | 702.92 | −52.1 |
| descended_empty | 750.26 | 786.74 | −36.5 |
| target_reacquired | 784.74 | 817.40 | −32.7 |
| carried | 最好 0.9991，未满 | 835.60 | — |
| delivered | 817.90 | 849.12 | −31.2 |

- 提前约 59 s 全部来自接近阶段：专家的接近 IK（`planner.reach` + least_squares）对数值库敏感。同一份规划代码不同步
  惯量时，Windows 得 14.1 s、Linux 镜像得 70.2 s（关节速度最大跳变 1.4 对 7.0 rad/s，换了 IK 分支，时间缩放跟着变）；
  同步惯量后两者对调，与 c 的 73 s 和容器里的 14 s 一致。这是专家自身的脆弱性，不是通道差异。其后行走短 3.6 s、放凳到
  登凳入口短 1.7 s，凳上取箱长 12.2 s、下凳长 18.2 s、地面重取与送箱长 2.8 s（专家自己的门控等待与重规划），接近之后
  合计慢 28 s（3.6%）。
- `carried` 差 0.09% 没有满：800.66 s 手与箱的相对速度（腕连杆原点对箱心）0.257/0.263 m/s，超过 `matched_hand` 的
  0.25 m/s，持续一个 20 ms 间隔；当时手箱距离恒为 0.193 m、夹持力 13–18 N（刚性夹持转身，不是滑脱）。这一步的 22 mm
  前进不计，`carried` 停在 0.9991，`observed_relay_chain` 因而为 false，得分 0.9999（c 1.0）。箱子在 803.14 s 被双手夹着
  进入目标区，`goal_delivered_ignoring_safety` 为 true。这是判据的灵敏度（工作流 B），不是通道问题。
- 安全事件只有规则 5：腰俯仰在 50 N·m 额定处饱和，2 段、最长 5.9 s（24.9 s 起凳时与 423 s 放凳前后，对应 c 的
  85.3 s 4.5 s 与 480.3 s 6.1 s，同一关节、同一阶段、时长相近），所以 `success=false`，与 c 在 2.2 下相同。其余规则的
  量与 c 接近：最大骨盆倾角 77.5°（c 78.6°），单脚支撑倾角 26.4°（c 26.2°），凳承重时倾斜 0.22°、滑动 12 mm（c 0.34°、
  10 mm），踩柜 0 N，松手时箱底 0.62 m、0.25 m/s（c 0.61 m、0.39 m/s）。
- 运行期间工作流 B 改了 `relay_safety.py`、`relay_safety_rules.py`、`statelog.py`（启动后 5 分钟），所以
  `launch_scope_source_frozen=false`：回合日志由启动时的 statelog 写成，判定用的是改后的 2.2 代码，日志完整性检查通过。

**尚未完成**：同一冻结配置的另外两次完整重复（作者可能因直接够取的研究改动场景，暂缓；`reference_rerun_spread`
仍待定）；规则 5 对 c 和通道运行都成立，需作者决定阈值或专家；接近阶段的 IK 平台敏感性（换平台即差约 59 s）应在专家里
固定（例如固定接近时长或 IK 种子）；`matched_hand` 的瞬时相对速度判据对刚性转身敏感；随机层场景未做。

正式统计遵循 [infra protocol](../../../infra/protocol-zh.html) 的两个三次要求：
三次独立开发交付，每份交付在相同密封回合集上重放三次。
使用 [evaluate_relay.py](../scripts/evaluate_relay.py) 生成执行计划；默认仅 dry-run，
显式 `--execute` 才启动容器。单份交付只可用于明确标记的诊断报告。

```powershell
python -m humanoid.g1_support_retrieval.scripts.evaluate_relay --submission-dir session1 --submission-dir session2 --submission-dir session3 --entry solve.py --out private_eval
python -m humanoid.g1_support_retrieval.scripts.evaluate_relay --plan private_eval/plan.json --execute
```

计划含私有种子，只保存在可信侧；三个目录应来自三次真正独立的开发会话。
运行器会冻结交付文件，不能替用户证明开发会话独立性。资产准备沿用仓库 `setup_assets.py`，
折叠凳另运行 `humanoid/g1_support_retrieval/scripts/prepare_stool.py`；实际文件哈希记录在
[assets.json](../acceptance/assets.json)。

结构与证据检查：

```powershell
python humanoid/g1_support_retrieval/scripts/check_relay_task.py
python -m unittest discover -s humanoid/g1_support_retrieval/sandbox/tests -t . -v
```

`check_relay_task.py --admission` 只有全部入库门槛完成后才通过，当前未完成项在验收清单中保留。

---

本目录给 H1 任务（G1 从柜子上取指定颜色的箱子）搭了一个隔离沙箱，用来评测 coding agent：

- **感知只走机器人自己的传感器**。agent 只能读机载传感器（头部 RGB-D、LiDAR、关节编码器、IMU、手部触觉、足底力），只能给机器人自己的 43 个关节发指令。
- **世界状态 agent 碰不到**。仿真世界在另一个可信进程里，物体位姿、尺寸、质量、摩擦和仿真设置都读不到，也改不了。
- **官方解只作特权参考解**。官方解（`solution/`、`verified/`）原样保留为参考轨迹，它读了仿真真值，所以只证明物理上可行、给分数定上锚点，不当作 Terminal-Bench 意义上的 oracle。官方轨迹可以按子目标切开当作起点，但官方解用到的特权设定 agent 一律用不了。
- **按过程计分**。是否把箱子当工具、箱子推到位了几成、是否站上箱子、是否碰到并取下目标、搬了多远，每个阶段都按完成程度连续给分，回合得分取进度峰值。判定只看可信侧记录的物理状态，不看 agent 自己怎么说（见 5.4）。
- **交付后重评**。正式打分不看开发会话，而是把 agent 交付的控制程序放到 N 个密封的新回合上各跑一次，再汇总（见 5.5）。

以下编号章节保留 2026-10-18 旧 `task` / `official` 版本的验证历史和限制；
其中“尚未串联”等表述仅指当时对应接口，不覆盖本页开头的新 `stool_relay` 版本。
新版本的当前证据与待验收项以 [readiness.json](../acceptance/readiness.json) 为准。

## 1. 三条要求怎么落实

| 要求 | 落实方式 | 代码 |
| --- | --- | --- |
| (1) agent 与环境隔离，只用机器人传感器做决策；可以调用 L1–L3 求解器，或自己写代码规划轨迹 | agent 和仿真分属两个进程，评测时 agent 在 Linux 容器里，两边只有一条 RPC 通道。通道只开放 8 个方法，读数只来自挂在机器人身上的传感器，坐标系都是传感器或关节自身的坐标系。L1–L3 都在 agent 这一侧（见 3.1）：L1 是 GR00T WBC，L2 是目标点轨迹规划，L3 是中间点加 IK/FK 暴力求解。它们只用 IMU、关节编码器、机器人自身模型和 agent 自己估计出的障碍物。 | `trusted/server.py`、`trusted/sensors.py`、`agent_sdk/g1sandbox/` |
| (2) 环境执行动作，杜绝 agent 暴力修改环境设置（物体位置、大小等） | 世界在可信进程启动时按密封的场景文件建好，之后没有任何能改它的入口。指令只能作用于 43 个关节：先校验，再按硬件力矩上限截断。物体质量和摩擦参数每 500 步核对一次哈希；verifier 再检查有没有物体瞬移。 | `trusted/world.py`、`trusted/verifier.py` |
| (3) 保留官方轨迹，可以沿用现在的设定并切成若干子目标，但 agent 不能用作弊设定 | 官方脚本一行不改，由录制器在外面记录全状态和子目标时间点。官方轨迹的身份是**特权参考解**：用来证明可行、给分数定上锚点，不当 oracle。沙箱可以从官方轨迹的任意时刻起步，但之后 agent 和完整任务一样，只有传感器和关节指令。官方解读真值、用 `set_pos` 摆位置这些做法只留在参考轨迹里；agent 侧既没有对应接口，也没有相应的代码和文件。评分按过程给分，判据与官方轨迹的时间线共用同一套代码。 | `trusted/record_official.py`、`trusted/scenarios.py`、`trusted/subgoals.py`、`trusted/scoring.py` |

## 2. 结构

```
agent 一侧（评测：Linux 容器，uid 1000，根文件系统只读，capabilities 全部丢弃）
  /opt/g1sandbox  只读：g1sandbox SDK、GR00T WBC 权重（L1）、solvers（L2/L3）、机器人 MJCF、示例
  /workspace      唯一可写目录
        │  TCP + 会话令牌；帧格式为长度前缀 JSON，数组用 dtype/shape/raw 编码，不用 pickle
        │  容器在 internal 网络里，唯一出口是一个 socat 转发器，只通向 worker 的端口
        ▼
可信 worker（Windows 宿主，genesis_env）
  SandboxWorld   原样复用 genesis_env.py 的场景，另加机载相机和执行器限幅
  server.py      8 个白名单方法：info status observe command command_sequence
                 declare_infeasible finish reset(仅开发模式)
                 另有一条只对启动器开放的控制管道（stdin）：评分模式下“换下一回合”和“关闭”
        │  只由可信侧写入
        ▼
trusted/   密封场景、令牌、特权状态日志（含按物体记录的接触）、全身快照、俯视录像、请求日志
        └─► verifier.py ─► verdict.json（过程分与是否成功、各阶段时间线、多回合汇总、违规审计）
```

可信侧代码（`trusted/`、任务代码、官方解、场景和日志）不会进入 agent 的路径，也不会进入容器。`tests/test_static.py` 会检查 bundle 里只有 SDK、求解器、机器人模型和示例。

2026-10-21 起，上面与任务无关的部分都放在共用运行时 [`infra/sandbox`](../../../infra/sandbox/ONBOARDING.md)：g1sandbox SDK、容器、帧协议、worker 骨架、启动器、指令通道、机载传感器、分块状态日志格式、监视器和 run 级评分外壳。H1 只保留场景和 `SandboxWorld`、启动参数、接力判据（relay-rubric/2.1）和监视器配置（`trusted/monitors.py`）。所有任务的沙箱共用同一套 run 记录格式和 `admission.json` 验收记录。

## 3. agent 拿到什么、拿不到什么

**拿得到**（都在机器人自身坐标系里）：

- 关节 `q`、`dq`、`tau_est`（实际施加的力矩）。
- 骨盆和躯干两个 IMU：姿态四元数（偏航角相对开局方向，没有世界朝向）、陀螺、加速度计（含噪声，噪声值取自 MJCF）。
- 头部 D435 位置的 RGB-D：640×480，垂直视场 58°，深度有效范围 0.1–10 m。
- 头部 MID-360 位置的 LiDAR：30 条仰角线（-7°–51°）×360 个方位，量程 0.15–40 m，同时给距离图和点云。
- Dex3 每个手部连杆的接触力，和两只脚的接触力。

安装位姿取自 Unitree G1 官方 URDF（`d435_joint`、`mid360_joint`，父连杆 `torso_link`）。场景文件可以关掉其中任何一种传感器，只有 `proprio` 关不掉。

此外 agent 还能拿到：

- 任务指令；
- 按能力披露档位给出的能力信息（`explicit` 给数值，`partial` 给粗略描述，`latent` 什么都不给）；
- 关节限位、名义（硬件）力矩上限、增益上限、控制周期和传感器规格；
- 机器人自身的 MuJoCo 模型。

**拿不到**：

- 任何物体的位姿、速度、尺寸、质量、摩擦；
- 柜子层高；
- 目标属于哪一类（family）；
- 场景种子；
- 本回合的真实力矩缩放和负载（`explicit` 档除外）；
- 第三人称相机、分割图；
- 物体上的接触力；
- 奖励和成功判定；
- 官方解和它的轨迹。

`finish()` 之后也不会告诉 agent 成功与否。

### 3.1 agent 侧的 L1–L3

| 层级 | 是什么 | 在 bundle 里 | 输入 |
| --- | --- | --- | --- |
| **L1** GR00T WBC | GR00T Decoupled WBC 的站立（`balance.onnx`）和行走（`walk.onnx`）策略，来自 `controllers/g1_wbc`。给定机体坐标系下的速度指令（vx、vy、wz）和骨盆高度，输出 12 个腿部关节和 3 个腰部关节的目标值，用策略自带的 PD 增益在电机模式下跟踪；手臂和手保持姿态。 | `g1sandbox.wbc`、`skills.stand` / `skills.walk`，权重在 `wbc/groot/` | 骨盆 IMU 的角速度和姿态（由姿态推算重力方向）、29 个身体关节的角度和速度、上一步动作，取 6 帧历史。**不用基座线速度，也不用世界坐标**，所以全部来自 `proprio`。 |
| **L2** 目标点轨迹规划 | 给定目标（关节角，或手等部位要到的位置），在机器人自身的 MuJoCo 模型上做 IK，再做带碰撞检查的直线插值或 RRT 绕障，输出一条关节轨迹 | `solvers.MotionSolver.solve`、`g1sandbox.planning` | 当前关节角加 IMU 姿态；障碍物由 agent 自己从深度或 LiDAR 估计，再加进模型 |
| **L3** 中间点 + IK/FK 暴力求解 | agent 自己给出中间点，逐段用 IK/FK 求解再拼接；某一段失败会指出是哪一段。agent 也可以直接在机器人模型上自己写 IK/FK | `solvers.MotionSolver.solve_waypoints`、`planning.robot_model` | 同 L2 |

L2/L3 的结果用 `skills.track` 执行（按时间戳伺服跟踪关节轨迹）。`hold`、`move_joints`、`track` 是执行用的辅助函数，不算 L1。

L1 的权重遵循 NVIDIA Open Model License（`wbc/groot/LICENSE`），只在本机的 agent 镜像里使用，不对外分发。和 `controllers/g1_wbc` 里验证时的设置相比，有三处不同：

- 沙箱的陀螺仪读数由一个控制周期内的有限差分得到，并且加了噪声；
- 上身关节的 armature 用的是任务里的 0.001，那边是 0.03；
- 任务会随机缩放腿部力量（0.85–1.0），并在躯干上加最多 5 kg 负载。

L2/L3 只做运动学规划：位置目标、基座固定、不考虑平衡和接触。规划成功只说明几何上可达。走路、站稳交给 L1；抓取、登箱、搬运还没有可用的 L1 技能，需要 agent 自己写控制器。

### 3.2 传感器实现说明

LiDAR 是模拟出来的：Genesis 1.4.3 没有射线传感器，所以在 MID-360 安装点放了四个朝向各差 90° 的深度相机，再按扫描方向查表换算成距离。扫描图案是规则网格，不是 MID-360 的非重复扫描。IMU 的角速度和加速度由一个控制周期内的有限差分得到，没有模拟陀螺零漂。

## 4. 动作通道与限幅

每个关节一条指令：`mode`、`q`、`dq`、`kp`、`kd`、`tau`，格式参照 Unitree LowCmd。

- `mode=0` 电机模式：每个物理子步（200 Hz）按 `tau_ff + kp(q*-q) + kd(dq*-dq)` 重新计算力矩。
- `mode=1` 伺服模式：Genesis 的隐式 PD。

两种模式合起来，覆盖官方执行器用到的全部驱动方式（腿部 3000/40 伺服、220/10 电机 PD、QP 力矩）。所以 agent 和官方解比，只少了信息，执行能力并不更弱。

worker 对指令的处理：

- 非有限值、形状不对、多出来的字段：直接拒绝。
- `q` 截到关节限位；`dq` 截到速度上限；`kp`、`kd` 截到增益上限；`tau` 截到名义力矩。
- 真正施加的力矩还要再截到本回合的实际上限：min(task_spec 力矩, MJCF `actuatorfrcrange`) × 腿部力量系数。前一项和官方执行器所用的一致；力量系数不公开。

没有基座外力，没有物体绑定，不能改重力或时间步长，不能复位到任意状态。开发模式的 `reset` 只能回到本回合的密封初始状态，且有次数上限；评测模式和评分模式都没有 reset。

仿真只在 `command` 调用期间推进，agent 思考不消耗仿真时间。回合在以下情况结束：

- agent 调用 `finish()` 或 `declare_infeasible()`；
- 仿真时间用完；
- 机器人摔倒：骨盆低于 0.40 m，或骨盆倾斜超过约 73°。阈值与 TaskCore 相同，但 TaskCore 看的是躯干，这里改看骨盆。原因是官方推箱时会有意把躯干前倾到接近水平（躯干 z 轴投影低至 -0.05），而骨盆的投影始终 ≥0.446、高度 ≥0.459 m。如果沿用躯干判据，照官方方式推箱的 agent 会被判为摔倒。

## 5. 官方轨迹、过程计分、重评与锚点

### 5.1 官方轨迹是特权参考解，不是 oracle

Terminal-Bench / Harbor 要求 oracle 和 agent 走同一个接口，而且拿满分，以此证明任务可解。这里做不到：官方解每一步都读仿真真值，换成只用传感器的参考解，成功与否都没把握。所以官方轨迹的身份定为**特权参考解**，只用来证明物理上可行、给分数定上锚点。

| 官方解 | 读了哪些 agent 拿不到的真值 | 开局的特权写入 |
| --- | --- | --- |
| `step_up` | 机器人基座的世界位姿、线速度、角速度（`env.state()`）；箱子的位姿和速度；机器人与箱子之间的接触（`get_contacts(with_entity=box)`） | `set_pos`/`set_quat` 放机器人，`set_dofs_position` 设关节，`set_mass` 设箱子质量 |
| `push_box` | 基座位姿和速度；箱子位姿和速度（每个控制步都读） | 机器人和箱子的位置，箱子的质量和摩擦 |
| `stool_carry` | 基座位姿和速度；凳子位姿和速度 | 机器人和凳子的位置，凳子质量 |
| `carry_walk` | 基座位姿和速度；箱子位姿和速度；机器人与箱子的接触；各连杆接触力 | 机器人和箱子的位置，箱子质量 |

这张表是对四个执行脚本做 grep 统计出来的，只列出现过的读取，不代表每一步都用到。

参考解**能**证明：在同一个世界、同样的物理设定和力矩上限下，这一步动作在物理上做得到。

参考解**不能**证明：只凭 agent 的传感器也做得到。所以如果所有 agent 都在某一步失败，没法区分是这一步太难，还是只靠传感器就做不到。第 9 节列出了这一点。

参考解与 agent 在执行条件上也不完全一样：

- 官方执行器以 200 Hz 子步直接调用 Genesis，agent 的指令以 50 Hz 控制步下发；
- 官方解开局用 `set_pos` 把机器人和箱子摆到便利的位置，agent 的场景则由 TaskCore 抽样决定。

### 5.2 录制

`trusted/record_official.py` 把官方脚本当黑盒运行，脚本参数与 `verified/*.ps1` 相同。它从外面记录以下内容：

- `world.json`：构造参数、脚本改过的 `task_spec` 常量、物理开关，以及首个物理步之后的所有特权写入（应为零，否则会列出来）；
- `world_params.npz`：全部刚体的质量和摩擦系数；
- `log/`：与沙箱 worker 同格式的特权状态日志，外加 10 Hz 的全身快照；
- `phases.json`：官方脚本自己 trace 里的阶段时间线。

`verifier.py --recording` 用和评测 agent 时同一套判据，标出官方轨迹在什么时刻达到哪一步，写到 `timeline.json`。

状态日志每个控制步按物体记录机器人与它的接触力，并分成“手、脚、其他身体部位”三类。“手在操作哪只箱子”就靠这项来判断。

### 5.3 阶段判据

判据只看可信侧记录的物理状态，不看 agent 说了什么，也不看用什么方法做到的。“识别出箱子可以当工具”同样按行为证据判定：agent 在文字里声称打算用箱子，不算数。

下表是各阶段“完成”的条件；过程分里各阶段的连续取值见 5.4。

| 阶段 | 判定条件 |
| --- | --- |
| `tool_engaged` 把箱子当工具用 | 两种情况之一：<br>• 用手操作过某只地面箱：手与它的接触力 ≥5 N，累计 ≥0.5 s，且箱子移动 ≥5 cm 或升高 ≥5 cm；<br>• 脚踩到它的顶面：脚与它的接触力 ≥50 N，且脚高于箱顶。<br>身体其他部位碰到、或手扫过但箱子没动，都不算。 |
| `support_placed` 把支撑物放到位 | 一只可用的箱子开局不在放置区，后来立在放置区内，立正、静止 1 s。放置区：箱子前沿离柜子 ≤0.15 m，箱子中心与目标的横向距离 ≤0.30 m。这是“站上去能够到柜子”的几何近似，还没有用实测够取距离校准。（原来用的“柜前 0.8 m 以内”太宽：官方推箱只推了 33 cm，箱子前沿离柜子还有 0.45 m，却也会被判为到位。） |
| `on_support` 站上支撑物 | 双脚踩在可用箱子的顶面上（脚踝连杆原点高出箱顶 1.5–7 cm，落在顶面范围内），每只脚竖直力的 0.1 s 滑动平均 >5 N，身体直立，持续 2 s |
| `target_reached` 碰到目标 | 手与目标的接触力 ≥2 N，或手（腕部连杆原点）离目标中心 ≤0.15 m |
| `target_lifted` 取到目标 | 目标箱比起始高 ≥3 cm，且在手边 0.25 m 以内，持续 1 s |
| `descended_holding` 带着目标下来 | 双脚回到地面，身体直立，目标仍在手边、离地 ≥0.3 m，持续 1 s |
| `carried` 搬运目标 | 目标离开货架（比起始高 ≥3 cm 或低 ≥0.3 m）且在手边 0.25 m 以内时，按水平方向走完的距离比例计；放进目标区为完成 |
| `delivered` 放到目标区 | 与 TaskCore 的 `in_goal` 判据相同，没有别的箱子在里面，目标静止，机器人没摔倒，持续 1 s |

另外两个判据用于官方单技能轨迹的时间线：

- `support_moved`：箱子在地面上移动 ≥20 cm，立正且静止；
- `support_lifted`：箱底离地 ≥3 cm，在机器人 0.6 m 以内。

几点约定：

- **可用的箱子**：开局时在房间内的地面箱，去掉 `choose_support` 里那只高而窄的干扰箱（`narrow`）。是否在场按开局位置判断，不看 TaskCore 的 `floor_present`，因为官方解先用 `floor_boxes=False` 建环境，再自己摆放要用的箱子。
- **足底力用 0.1 s 滑动平均**：官方 `step_up` 收尾时重心压在左脚，右脚的瞬时竖直力会在单个 20 ms 采样里掉到 5 N 以下。逐帧判定会把官方自评成功的轨迹判成失败；用滑动平均后，判定时刻与官方自己的判据一致（见第 8 节）。

### 5.4 按过程计分

原则：**尽量按过程给分**。做法参照 EmbodiedSWE 的 rubric grader（`trusted/scoring.py`）：

- 每个阶段在每个控制步上都有一个 0–1 的连续值，表示这一阶段做到了几成，而不只看最后有没有完成。
- 阶段分两种模式：
  - `once`（里程碑）：取迄今最好值，状态丢了也保留；
  - `live`：取当前值，比如目标被碰出目标区就掉分。
- 进度(t) = Σ 权重 × 阶段值(t) / Σ 权重。**回合得分取整个回合中进度的峰值**，写在 `verdict.json` 的 `score`；结束时的进度另记为 `final_progress`。

| 阶段 | 模式 | 需要垫脚的三类 | direct | 取值 |
| --- | --- | --- | --- | --- |
| `tool_engaged` 把箱子当工具用 | once | 0.10 | – | 有行为证据后为 1（判据见 5.3） |
| `support_placed` 支撑物到位 | once | 0.15 | – | 可用的箱子从起点向放置区走完的距离比例；在区内静止 1 s 记 1 |
| `on_support` 站上支撑物 | once | 0.15 | – | 一只脚踩上箱顶并受力 0.5；两只脚 0.75；两只脚站稳 2 s 记 1 |
| `target_reached` 碰到目标 | once | 0.10 | 0.20 | 手与目标接触 ≥2 N，或手离目标中心 ≤0.15 m，记 1 |
| `target_lifted` 取到目标 | once | 0.15 | 0.30 | 目标比起始高 ≥3 cm 且在手边，保持 1 s 后记 1 |
| `descended_holding` 带着目标下来 | once | 0.10 | – | 双脚回到地面、目标仍在手边，保持 1 s 后记 1 |
| `carried` 搬运目标 | once | 0.10 | 0.20 | 目标离开货架且在手边时，从货架到目标区走完的水平距离比例；放进目标区记 1 |
| `delivered` 放到目标区 | live | 0.15 | 0.30 | 目标静止在目标区内、机器人没摔倒时为 1 |

“需要垫脚的三类”指 one_support、choose_support、staircase。`infeasible` 类只看是否正确声明不可行，声明了得 1。

规则：

- 本回合拿不到的阶段直接去掉，剩余权重重新归一。例如开局就有可用的箱子在放置区，`support_placed` 不计分。
- 动用了干扰箱：只能拿到 `tool_engaged`，并在报告里标为 `distractor_engaged`。
- 摔倒或声明会结束回合，之前的进度保留。对可行的任务声明不可行，记为 `wrong_declaration`，不额外扣分。
- 是否完成任务（`success`）单独给出，与 Terminal-Bench 的 0/1 口径一致：可行的任务看结束时目标是否在目标区，不可行的任务看是否声明了。
- 整次运行若判为 VOID（越权、世界参数被改、瞬移），得分记为 0。

权重和阶段阈值都是初始设定，还没有用真实 agent 的结果校准。

### 5.5 交付后重评（评分模式）

开发会话里只有一个回合，开发模式下还能反复 reset 回同一个初始状态，那一回合的得分代表不了能力。所以正式打分和 EmbodiedSWE 一样，用**评分模式** `--mode grade`：

1. agent 在开发会话结束时交付一个只调用 SDK 的控制程序（目录里放 `solve.py` 之类的入口）。
2. 可信侧在同一个已建好的场景里，按私有种子依次抽出 N 个新回合。每个回合的柜子、层高、箱子、质量、摩擦、力量系数、披露档位都重新抽取，不需要重建场景。
3. 每个回合给交付程序**一份全新的工作目录副本**，在容器里运行一次。容器内只有 worker 端口可达，没有 LLM，也不能 reset。每次运行有墙钟预算。
4. 一次运行结束（不论是否连上过 worker），启动器才通知 worker 换下一回合。所以程序崩溃也不会把同一回合留给下一次运行，没跑成的回合记 0 分。
5. `verdict.json` 汇总以下统计：`success_rate`、`score_mean`/`std`/`min`/`max`、每个阶段的平均最好值 `stage_best_mean`、按任务类型分组的 `by_family`，以及每个回合的明细。

`--families` 可以让 N 个回合按指定的任务类型轮流抽取，例如每类一个回合；其余属性仍由私有种子决定。N 很小时，不指定任务类型会让得分的波动很大。

### 5.6 锚点

- **下锚点**：什么都不做的程序（`examples/hello_robot.py`、`tests/agents/hold_agent.py`）得 0 分。评分模式下按五类任务各跑一个回合，也是全 0。
- **上锚点**：由特权参考解给出。官方轨迹都是单技能场景，用“需要垫脚”的权重来算：

| 官方轨迹 | 过程分 | 达到的阶段 |
| --- | --- | --- |
| `step_up` | 0.25 | `tool_engaged`（23.5 s 脚踩箱顶）、`on_support`（45.78 s） |
| `push_box` | 0.33 | `tool_engaged`（12.66 s 手推）、`support_placed` 0.53（箱子向放置区走了 53%，官方本来就没推到柜前）、`on_support`（352.8 s） |

- **没有上锚点的部分**：
  - `support_placed` 只证明到 0.53：还没有官方轨迹把箱子推进放置区（前沿离柜子 ≤0.15 m）。
  - `target_reached`、`target_lifted`、`descended_holding`、`carried`、`delivered` 没有任何官方参考解，合计占 0.6 的权重。串联方案 `carry_climb_retrieve` 还没有完整成功过，所以这些阶段连物理上是否可行都还没有证据。
  - 目前已证明可达的过程分是 0.33（`push_box`）；前三个阶段全拿满是 0.40，但还没有参考解。

### 5.7 子目标场景

`scenarios.official` 的流程：

1. 读入一份录制，恢复它的世界参数和某一时刻的全身快照；
2. 用 `INSTRUCTIONS` 里的英文句子告诉 agent 要完成哪些子目标；
3. 此后 agent 只能用传感器和关节指令，和完整任务完全一样。

这样就可以拿官方轨迹的中间状态（比如“推完箱子、站在箱前”）作起点，单独考某一个子目标；而官方解读真值、摆位置的设定，agent 一样也用不上。

凳子方案（`stool_carry`）的凳子是在任务环境之外另加的实体，当前的检查点恢复还不能重建它，所以先不支持。`push_box`、`step_up` 和 `carry_walk` 只用任务环境自带的地面箱。

## 6. 隔离级别

| 级别 | agent 在哪里 | 隔离到什么程度 | 用途 |
| --- | --- | --- | --- |
| `container` | Docker Desktop 的 Linux 容器。uid 1000，根文件系统只读，`--cap-drop ALL`，`no-new-privileges`，限制 pids、内存和 CPU。只挂载 bundle（构建进镜像）和当前回合的 `workspace_XX/`。网络是 `--internal`，只能经 socat 转发器到 worker 端口；加 `--llm-proxy` 时，再经 squid 访问白名单里的 `api.anthropic.com`。 | 文件系统、网络和接口三层都隔离 | 评测 |
| `process` | 本机的独立 Python 进程。只有 SDK bundle 在 `PYTHONPATH` 上，环境变量清理过。 | 只有接口隔离。D: 盘是 exFAT，没有权限位，同一用户的进程能读盘上任何文件。 | 调试 SDK 和 agent 代码，不能作评测 |

仿真留在 Windows 宿主上运行，原因是 Isaac/Genesis 渲染在 WSL2 里只能用到 llvmpipe（见 `ISAAC_SETUP.md`）。agent 侧只需要 CPU，所以放进 Linux 容器。这个分工和 Harbor 的“agent 容器 + 可信 worker + 独立 verifier”是同一种结构。

## 7. 用法

在 `robo-si/` 下运行，Python 用 `D:\rsi_vla\genesis_env`：

```powershell
# 静态检查和过程计分（不需要 GPU）；传感器几何与每步耗时（需要 GPU，约 4 分钟）
python -m unittest humanoid.g1_support_retrieval.sandbox.tests.test_static -v
python -m unittest humanoid.g1_support_retrieval.sandbox.tests.test_scoring -v
python -m humanoid.g1_support_retrieval.sandbox.tests.check_sensors

# 逃逸探针：在容器里以 agent 身份尝试越权，结果应全部符合预期，且整次运行判 VOID
python -m humanoid.g1_support_retrieval.sandbox.launch task --isolation container --no-video `
    --agent-dir humanoid\g1_support_retrieval\sandbox\tests\agents -- python /workspace/escape_probes.py

# 完整任务，评测模式：一个交互回合，agent 在容器里（种子不写，由可信侧私下抽取）。正式打分用下面的评分模式
python -m humanoid.g1_support_retrieval.sandbox.launch task --isolation container `
    --agent-dir <你的 agent 目录> -- python /workspace/agent.py

# 开发模式，指定 family 和能力披露档位，本机进程（只有接口隔离）
python -m humanoid.g1_support_retrieval.sandbox.launch task --family one_support --tier explicit `
    --seed 101 --mode dev --isolation process --agent-dir <dir> -- python agent.py

# 评分：把交付的程序放到 5 个密封新回合（五类任务各一个）上各跑一次，每次限时 120 分钟
python -m humanoid.g1_support_retrieval.sandbox.launch task --mode grade --episodes 5 `
    --families direct one_support choose_support staircase infeasible --isolation container `
    --budget-min 120 --agent-dir <交付目录> -- python /workspace/solve.py

# 录制官方轨迹，然后从录制的第 t 秒开始考某个子目标
python -m humanoid.g1_support_retrieval.sandbox.trusted.record_official --preset step_up --out <rec>
python -m humanoid.g1_support_retrieval.sandbox.trusted.verifier --recording <rec>
python -m humanoid.g1_support_retrieval.sandbox.launch official --recording <rec> --at 0 --goals on_support `
    --isolation container --agent-dir <dir> -- python /workspace/agent.py
```

agent 能读的 bundle 按内容哈希放在 `sandbox/runs/_bundle-<digest>/`，镜像标签用同一个哈希（`g1sandbox-agent:<digest>`）。所以 SDK、WBC 权重、求解器或机器人模型一改，就会生成新的 bundle 和新的镜像。

清理过期的 bundle 和镜像（只保留当前哈希；运行记录、官方录制和其他镜像都不动）：`python -m humanoid.g1_support_retrieval.sandbox.prune`，先加 `--dry-run` 可以只看会删什么。

每次运行写到 `sandbox/runs/<name>/`：

- `trusted/`：只有可信侧使用，内容包括 `verdict.json`、`motion.mp4`、`run.json`、哈希链请求日志 `requests.jsonl`、密封场景 `scenario.json` + `scenario.sealed`、交付快照 `delivery/` + `delivery.json`、源码清单 `source_manifest*.json`、每个回合的 agent 输出 `agent_stdout_XX.log`，以及 `episode_XX/` 状态日志（分块状态、`recording.json`、文件清单 `files.json`）；
- `workspace_00/`、`workspace_01/` …：每个回合 agent 唯一的可写目录。评分模式下每个回合拿到一份新的交付程序副本。

官方轨迹的录制放在 `sandbox/runs/official/<名字>/`。

agent 侧的接口说明在 `agent_sdk/README.md`（英文，会放进 bundle），示例在 `agent_sdk/examples/`。

## 8. 验证记录

2026-10-25：`tests/check_sensors_gate.py` 现检查初始姿态和补充校准姿态。初始姿态因房间与柜体遮挡只有 721 个地面回波，四项原有精度检查仍保留；补充姿态通过关节指令在 1 秒内将腰部 pitch 后移 0.15 rad、保持 0.5 秒，获得 1,013 个地面回波。两种姿态均须满足原精度阈值，补充姿态还须独立达到原 1,000 点门槛，不合并点数、不改传感器安装或物理参数。[主目录 GPU 流水线](../acceptance/pipeline/20261025-022633-gpu.json)已通过；[原始失败与修复验证](../acceptance/release_20261024/canonical_sensor_twopose_validation.json)保留了检查范围和旧记录。这只证明传感器几何检查，不代表完整任务或全部流水线通过。

2026-10-18，在本机上完成：RTX 5090，Genesis 1.4.3，Docker Desktop 29.5.3（WSL2 后端）。每次运行的原始记录都在 `sandbox/runs/` 下，失败的也保留了。

| 检查项 | 怎么做 | 结果 |
| --- | --- | --- |
| 静态检查 | `tests/test_static.py`，共 8 项：帧格式、白名单、bundle 内容 | 全部通过。bundle 里只有 SDK、求解器、机器人模型、示例和 Dockerfile，没有任务代码、可信侧代码和场景文件 |
| 传感器几何 | `tests/check_sensors.py`：用真实的躯干位姿和安装变换，把读数换到世界坐标 | 头部深度与 Genesis 自带点云相比，中位误差 1.3 mm，p99 4.8 mm；地面像素的 z 中位 1.0 mm。<br>LiDAR 地面回波的 z 中位 0.7 mm，p99 18 cm。尾部误差来自平面判据不成立、回退到最近像素的点，例如墙顶与墙外地面的交界。 |
| 速度 | 同上 | 单独运行时每个控制步 30–80 ms（物理约 8–27 ms，特权日志约 7–22 ms；本机同时还开着别的程序）。<br>一次读取全部传感器约 0.1 s。<br>与另一个仿真同时跑时会降到 0.67 s/步，所以要逐个运行。 |
| 端到端，process 模式 | `examples/hello_robot.py` | 六种传感器都读到了，按姿态保持 2 s，关节最大误差 0.0036 rad。判定 FAIL（它本来就不做任务），不是 VOID，0 次违规 |
| 逃逸探针，container 模式，评测 | `tests/agents/escape_probes.py`，共 36 项 | 全部符合预期：<br>• 协议层 4 项（错误令牌、pickle 帧、超长帧头、未认证就发指令），12 个不存在的方法（如 `set_pos`、`set_mass`、`eval`），1 个 object dtype 数组 —— 共记录 17 次违规，判定 VOID；<br>• 值层 12 项被拒：要求分割图或物体位姿等不存在的传感器、带 `root_force`/`set_pos` 字段的指令、NaN、形状错误、超长序列、评测模式下 reset；<br>• 力矩 1e6 N·m、增益 1e9 被截断，实际力矩与名义上限之比为 1.000；<br>• 容器内 import genesis、import 任务代码、读 trusted 文件、读仓库、直连 github.com 和 api.anthropic.com 全部失败。 |
| 逃逸探针，process 模式 | 同上 | 接口层与 container 模式结果相同（17 次违规，VOID）。OS 层有 5 项能做到：import genesis、读 trusted 场景文件、读仓库、两项外网。这是 process 模式已知的限制，报告里标为 `LIM`。 |
| L1（GR00T WBC），container 模式 | `examples/l1_walk.py`：站 1 s，以 0.3 m/s 指令前进 4 s，再站 1.5 s。这一回合抽到的腿部力量系数为 0.89，躯干负载 4.8 kg | 全程没有摔倒，骨盆最低 0.725 m。按可信日志：<br>• 行走 4 s 前进 0.79 m（平均约 0.2 m/s），侧向漂移 7 cm，偏航变化 0.07 rad，停下后站稳；<br>• 开头站立的 1 s 里后退了 12 cm，这是从任务初始姿态过渡到 WBC 默认姿态造成的；<br>• 每个控制步（含往返通信和 ONNX 推理）中位 38 ms。 |
| L2，container 模式 | `examples/l2_reach.py` | 在容器里用 MotionSolver 规划双臂前伸，15 个采样点，用 `skills.track` 执行。跟踪误差最大 0.0097 rad，用实测关节做 FK 得到的腕部目标误差为 3.5 mm |
| 生命周期，container 模式，开发 | `tests/agents/lifecycle_agent.py`，infeasible 场景 | 6 项检查全部通过：<br>• 仿真时间推进；<br>• `reset` 把时间和姿态还原（误差 <1e-4）并扣减次数；<br>• `declare_infeasible` 结束回合；<br>• 结束后再发指令被拒。<br>verdict 按 reset 之后的回合判，结果 PASS（场景本身不可行，又做了声明）。这只说明判定逻辑正确，不代表 agent 有能力。 |
| 官方轨迹录制 | `record_official --preset step_up`，录了两次（第二次带按物体记录的接触） | 两次结果一致：官方脚本原样运行，自评成功（双脚在箱顶稳定 2.0 s），全程 45.88 s，首个物理步之后特权写入 0 次。<br>verifier 用同一套判据得到：`tool_engaged` 在 23.5 s 成立（第一只脚踩上箱顶，接触力 >50 N），`on_support` 在 45.78 s 成立。 |
| 官方 `push_box` 录制 | `record_official --preset push_box` | 官方脚本原样运行，全程 363 s，首个物理步之后特权写入 0 次。<br>`tool_engaged` 12.66 s（手推箱子），`support_moved` 106 s（箱子移动 ≥20 cm），`on_support` 352.8 s（推完后站上箱子）。<br>按原来的躯干判据，这条轨迹会在推箱的 2217 个控制步里被判为摔倒；改用骨盆判据后不再误判（见第 4 节）。 |
| 过程计分 | `tests/test_scoring.py`，12 项，用合成的状态日志 | 全部通过：<br>• 什么都不做得 0 分；<br>• 完整解得 1 分；<br>• 只完成前三个阶段得 0.40 分；<br>• 箱子推到一半，`support_placed` 得 0.5；<br>• 只有一只脚站上箱子，`on_support` 得 0.5，两只脚得 0.75；<br>• 目标放进目标区后又被碰出：得分取峰值 1.0，结束时进度为 0.85；<br>• 手扫过但箱子没动、或身体其他部位碰到，都不算用工具；<br>• 动用干扰箱只得 0.10；<br>• 开局就已在位的阶段不计分，其余权重重新归一；<br>• 躯干前倾到水平不算摔倒，骨盆倾斜 80° 算摔倒；<br>• `direct` 和 `infeasible` 两类的计分正确；<br>• 汇总时没跑成的回合记 0 分。 |
| 评分模式（交付后重评） | `--mode grade`，交付程序为 `hold_agent.py`，在容器里跑 | 两次运行都正常：<br>• 3 个回合，任务类型不指定：每次运行各对应一个回合（日志里连接 1/2/3 分别落在回合 0/1/2），三个回合的柜子、力量系数、负载各不相同，得分都是 0。<br>• 5 个回合，`--families` 指定五类各一：任务类型依次为 direct、one_support、choose_support、staircase、infeasible，按任务类型汇总的得分都是 0。<br>第一次运行里三个回合恰好都是 direct 且目标都是黄色。离线用同一个种子抽 40 个回合检查过：任务类型分布在 5–11 之间，颜色分布在 8–12 之间，属于巧合，不是随机数的问题；但它说明回合数少时必须指定任务类型。 |
| 检查点还原 | `official --at {0, 43.5, 45.8}` + `hold_agent.py` | 还原后的第一帧与录制快照对比：机器人根部、全部关节、箱子、手的位置误差为 0（脚 3e-8 m）。<br>• t=0：站在箱前保持 4 s，没有上箱 → FAIL，符合预期；<br>• t=43.5：官方当时还在用 QP 主动转移重心，僵硬保持 1.74 s 后后仰摔倒 → FAIL；<br>• t=45.8：官方结束时的稳定站姿，保持 4 s → `on_support` PASS（正对照）。 |

搭建过程中发现并修好的问题：

- `launch.py` 用 argparse 的 REMAINDER 接收 agent 命令，结果把后面所有选项都吞掉了。现在改成在 `--` 处切分命令行。
- 官方解不设 `floor_present`，导致子目标判据看不到箱子。现在改成按位置判断箱子是否在场。
- 足底力按单帧判定太严，改用滑动平均（见第 5 节）。
- LiDAR 原来取最近像素，掠射角下地面误差达 4–18 cm。现在先做平面判据，成立时对 1/深度做双线性插值。
- worker 一次只服务一个会话，协议层探针原来排在主会话后面，根本没有到达服务端。现在挪到主会话之前。
- `robo-si/solvers/motion.py` 里有两处 `numpy.int32 in (mujoco 枚举, ...)`，在 Linux 上恒为 False，导致 L2 在容器里无法构造求解器。现在改成按整数比较；求解器原有的 8 项单元测试仍然通过。
- Windows 上无法把新 bundle 改名覆盖到正在被占用的目录，现在改成按内容哈希命名目录。
- 摔倒判据原来沿用 TaskCore，看的是躯干倾斜。官方 `push_box` 推箱时躯干前倾到接近水平，按这个判据会被当成摔倒，等于禁止 agent 用官方的方式推箱。现在改看骨盆倾斜，阈值不变。

## 9. 范围和限制

- 隔离只针对软件层面的篡改和信息泄漏。仿真本身的漏洞（穿模、接触求解异常）属于另一类问题。verifier 只能查出“瞬移”（相邻控制步之间速度超过 20 m/s），其余要靠录像和人工复核。
- L1 目前只有 GR00T WBC 的站立和行走，并且只验证了直行一次（见第 8 节），转向、侧移、改变高度和长时间行走都还没测。GR00T 的上肢 IK、SONIC 和 N1.7 都没有接入。
- 官方已验证的推箱、搬凳、登箱、搬箱四项技能都读真值，所以没有放进 L1；要放进去，得把其中的真值读取换成 agent 给的估计参数，并重新验证。另据 `controllers/g1_wbc/BOX_CAPABILITY.md`，现有三种控制方案登 18 cm 可移动箱子的测试都没通过。
- 行走策略 `solution/agile.py` 需要基座线速度。真机测不到这个量，沙箱里也不提供，所以没有放进 L1，L1 的行走由 GR00T WBC 承担。
- 子目标判据是几何近似，阈值写在 `subgoals.py` 里，还没有用大量运行校准过；阶段权重、放置区大小、过程分的分档（例如一只脚记 0.5）同样是初始设定。
- 评分模式很耗时：每个控制步 30–80 ms，一个 1200 s 仿真时长的回合大约要 30–80 分钟墙钟时间，5 个回合就是几个小时。另外场景构建一次约 3 分钟，各回合共用。
- 没有 oracle，只有特权参考解（见 5.1）。所以某一步若所有 agent 都没做到，无法区分是太难还是只凭传感器做不到。碰到目标、取到目标、带着目标下来、搬运、放到目标区这五个阶段，以及把箱子推进放置区，连特权参考解都还没有（见 5.6）。
- `tool_engaged` 只认手操作或脚踩这两种行为证据。agent 若想到了用箱子但没能碰到它，这一步不给分。这是有意的：只按物理状态计分，不按文字陈述计分。
- 已录制官方 `step_up` 和 `push_box`。`carry_walk` 在 `record_official` 里已有预设，还没有录制；`stool_carry` 需要先支持额外实体。
- 检查点场景从官方轨迹中途开始时，机器人带着当时的动量。像 t=43.5 那样，官方控制器正在主动平衡的时刻，agent 必须马上接手平衡，否则会摔倒。挑检查点时要考虑这一点。
- container 模式下，LLM 代理（`--llm-proxy` 加 squid 白名单，镜像构建参数 `INSTALL_CLAUDE=1`）的配置已经写好，但这个镜像还没有构建过，也没有用真实 API key 跑过完整的 coding agent 会话。上面的验证都是用脚本当 agent 做的。
- 容器的出口目前只通向 worker 端口和（可选的）LLM API。容器隔离能挡住读文件、联网和改代码，但挡不住 agent 对白名单接口本身的滥用，比如狂发请求、耗光观测预算。这类行为靠预算和请求日志来约束。
- 这台机器的 D: 是 exFAT，process 模式不能当评测用。如果要在 Windows 上做到文件级隔离，只能把 agent 放进容器。
