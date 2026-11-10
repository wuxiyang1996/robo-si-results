# Harbor skill-level benchmark

具身（embodied）方向的自我改进任务，按 rsi-exam / Harbor 的格式来写。被测的 agent 有 12 小时，用来写或改进一个控制程序。之后，独立的 verifier 会在 agent 从没见过的场景上从头重跑这个程序，并打分。

```
benchmarks/harbor/
├── tasks/                                  # 每个子目录是一个 Harbor 任务，可以直接放进 rsi-exam-v1/tasks/
│   └── g1_support_augmented_retrieval/
│       ├── instruction.md                  # agent 唯一能看到的题面（固定五节，英文）
│       ├── task.toml                       # 12h、三个 network_mode、verifier 用 separate 模式、[scoring] 里放 visible 锚点
│       ├── environment/                    # agent 镜像：模拟器、144 个 visible episode、starter、selfcheck
│       ├── solution/                       # 参考控制器，SOTA 锚点就是用它测的（oracle 模式会跑 solve.sh）
│       └── tests/                          # verifier 镜像：模拟器副本、288 个 sealed episode、grade.py、anchors.json
└── tools/
    └── g1_support_augmented_retrieval/     # 只给作者用，不进任何镜像：生成器、特权 oracle、测锚点、escape 测试
```

## 任务 1：`g1_support_augmented_retrieval`

**场景。** 一个房间里有一台 Unitree G1 和一个柜子。柜顶放着 2–4 个不同颜色的盒子，地上有 2–4 个可以搬或推的箱子。指令要求取下指定颜色的盒子，放进目标区。够不到时，可以把一个地上的箱子当垫脚；用任何单个箱子都做不到时，应该声明不可行。

**接口。** agent 提交 `/app/methods/main/controller.py`。每个 episode 启动一个新的子进程，通过 stdin/stdout 用 JSON-lines 协议调用 15 个中层技能：`NavigateTo`、`Inspect`、`Grasp`、`Lift`、`Release`、`CarryTo`、`Place`、`Push`、`ProbeSupport`、`StepOnto`、`StepDown`、`ReachTo`、`PlaceInGoal`、`Done`、`DeclareInfeasible`。

| 设计稿里的概念 | 在任务里的对应 |
|---|---|
| Variant A：能直接够到 | family `direct`，这时搬箱子只会浪费时间 |
| Variant B：需要一个垫脚箱 | family `one_support`，所有够高的箱子都能用 |
| Variant C：一稳一不稳 | family `choose_support`，至少有一个够高、但不能用的箱子：会晃（rock）、会塌（crush）、太高迈不上去、脚面太窄，或者搬不动 |
| Variant D：怎么都不行 | family `infeasible`，只有 `DeclareInfeasible` 得分 |
| Capability Knowledge：Explicit / Partial / Latent | `capability.tier`：给数值 / 只给定性描述 / 什么都不给 |
| Embodiment 轴 | 6 种 G1 机体变体（臂长、抬腿高度、载重、推力、体重各不相同），其中 2 种只出现在 sealed 集里 |
| Discovery → Attribution → Adaptation | 失败的 `Grasp`/`ReachTo` 会返回 `shortfall_m`，`ProbeSupport` 会返回形变、倾角、滑移和 `step_effort`，`Lift`/`Push` 会返回 `effort`。控制器要靠这些读数推断出是哪个能力不够，再换策略 |

**物理模型（skill-level，纯 Python，只用 CPU）。** 可达性按“肩到抓取点的距离”算；直线会穿过柜沿时，改成绕过柜沿的两段路径。能不能踩上箱子取决于抬腿上限、脚面大小、压溃载荷、倾角（底面缺陷加细长比）和滑移（贴住柜子可以防滑）。搬运受载重限制，推动受推力限制。所有随机性都由 episode seed 决定，同一串动作永远得到同一个结果。

**评分。** 先算每个 episode 的分数，再取平均（`mean_episode_score`）。可行的 episode 成功时得 `0.5 + 0.5·min(1, t_ref/t)`，其中 `t_ref` 是特权 oracle 知道全部隐藏参数时规划出的时间。不可行的 episode 只有声明不可行才得 1 分。摔倒、拿错盒子或超时都是 0 分。

### 锚点（已经实测）

| 档位 | 方法 | visible | sealed | reward |
|---|---|---:|---:|---:|
| baseline | starter：只认 3 种颜色，从不探测、从不推、从不判不可行 | 0.2683 | 0.1961 | 0 |
| SOTA | `solution/controller.py`：作者写的能力感知启发式，没用任何特权信息 | 0.9069 | 0.8803 | 0.6 |
| upper | 理论上限 1.0。特权 oracle 在 sealed 上实测也是 1.0000 | — | 1.0 | 1.0 |

参考控制器在 sealed 上的表现：可行 episode 成功率 96.8%，不可行的召回率 98.6%，摔倒率 0.35%。它和上限的差距主要在效率：用时约为 `t_ref` 的 1.4 倍。

### 已经验证过的内容（Docker，固定 digest 的 python:3.12-slim）

- 两个镜像都能构建。nop（starter 原样提交）走完 Harbor 的 separate verifier 流程后 reward = **0.0**；oracle（`solution/solve.sh`）reward = **0.6**，指标和本地不加沙箱时完全一致。
- 四类 escape 都得 0 分：直接读答案、monkeypatch 评分函数、扫描磁盘、自己写 reward 文件（`/logs/verifier` 改成所有人可写也一样）。另外开 socket 和给父进程发信号都会被 seccomp 拦下。
- 故意让 grader 崩溃（数据集 hash 不匹配、SIGKILL）时，结果都是 reward 0，`score_details.json` 里带 `grader failed:` 标记。
- rsi-exam 的 `auto-review` 跑了 7 项检查，6 项是 0 findings。`network_policy` 需要装了 harbor 的解释器，这台机器上还没跑。

## 常用命令

```bash
# 本地自测（Windows 也能跑；不加沙箱，结果和容器里一致）
python tasks/g1_support_augmented_retrieval/environment/selfcheck.py --family choose_support --tier latent
python tasks/g1_support_augmented_retrieval/environment/selfcheck.py --episode v-0007     # 打印完整 transcript

# 走 Harbor 的完整流程（需要 Docker 和 harbor）
harbor run -p tasks/g1_support_augmented_retrieval --agent nop    -e docker -o jobs/   # 应该得 0
harbor run -p tasks/g1_support_augmented_retrieval --agent oracle -e docker -o jobs/   # 应该得 0.6

# 重新生成数据或改了模拟器之后（tools/g1_support_augmented_retrieval/ 下）
python generate.py --sealed-seed <自己保密的整数>   # 重写 visible 和 sealed 两个 episode 集
python finalize.py --measure                         # 转成 LF、同步 tests/g1sim、重测锚点、写入 dataset_sha256
python measure.py --split sealed --controller oracle # 查看特权上限
```

改过 `environment/g1sim/` 之后一定要跑 `finalize.py`。它会把模拟器同步到 `tests/g1sim/`，并重测锚点。grade.py 会核对 sealed 文件的 sha256，数据集和锚点对不上时会直接 fail-closed。

## 已知局限和后续工作

- **抽象层级。** 这是技能层的解析模型，不是刚体物理仿真。这样选，是为了让任务能在 Harbor 的 CPU Docker 里跑，而这台机器上的 Isaac Sim 进不了 Docker/WSL 渲染。技能 API 是固定的，以后可以在同一套 API 后面换成 Isaac Lab / Genesis 的 whole-body 后端。
- **G1 参数。** 身高 1.32 m、体重 35 kg 是官方数值。肩高 1.02 m、臂展 0.48 m、抬腿 0.22 m、载重 5 kg 是估算值，还没有对照 URDF 校准。
- **难度。** 作者花几个小时写的启发式在 sealed 上已经有 96.8% 的成功率，剩下的空间主要在效率和泛化。如果要更难，可以调这几处：加大感知噪声、在 agent 镜像里只提供技能文档不给模拟器源码、允许叠箱子、让探测本身有风险、增加多目标任务。
- **另一种用法。** 想直接测 LLM/VLA 规划器（不让它写代码）时，可以在同一个模拟器外面加一层交互式 CLI，做成 terminal-bench 风格，每个 episode 一个任务。
