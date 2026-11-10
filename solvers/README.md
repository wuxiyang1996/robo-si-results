# L2 / L3 motion solver

首版实现固定基座、有限位单自由度关节的运动学规划。复用现有 G1 MJCF，MuJoCo 仅用于规划副本上的 FK、Jacobian 和碰撞检测，不调用 `mj_step`，不修改在线仿真的状态。模块独立于 Genesis / Isaac，可将输出作为其控制器的关节参考；尚未接入任务 RPC 或 WBC 在线执行。

- **L2**：当前完整 `qpos` + 关节目标或一个/多个末端位置目标 → 阻尼最小二乘 IK → 直线路径碰撞检查 → 必要时 RRT 绕行。
- **L3**：agent 显式给出 waypoint 序列，逐段使用同一求解器；共享总时间预算，拼接后返回 waypoint 索引。失败定位到段，不把部分路径当作成功结果。
- 输出含完整关节配置轨迹、时间戳、活动关节映射、碰撞检查次数、规划耗时与结构化失败原因。`success=true` 表示找到规划，`execution_verified` 始终为 `false`。

## 运行

在 `D:\rsi_vla\robo-si` 下，使用现有环境，无需安装新依赖：

```powershell
$solverPython = '..\genesis_env\Scripts\python.exe'
& $solverPython -m solvers --model solvers/examples/planar.xml --request solvers/examples/l2.json --out solvers/runs/l2.json
& $solverPython -m solvers --model solvers/examples/planar.xml --request solvers/examples/l3.json --out solvers/runs/l3.json
& $solverPython -m solvers.demo_g1
& $solverPython -m unittest discover -s tests -p test_motion_solver.py -v
```

其他环境使用 Python 3.12 和 `pip install -r solvers/requirements.txt`。平面示例与单元测试不需要下载资产。G1 示例需要先运行仓库 `setup_assets.py`，默认输出到 `solvers/runs/g1/`。命令行规划成功退出码为 0，规划失败为 2；无效配置、JSON 或模型加载错误会直接报错。

平面示例中，L2 自动绕过中间障碍；L3 使用输入文件中显式提供的上方中间位置。示例路径不是机器人任务的隐藏解法。

## Python API

```python
import mujoco
from solvers import MotionSolver, PositionTarget, SolverConfig, Waypoint

model = mujoco.MjModel.from_xml_path('solvers/examples/planar.xml')
solver = MotionSolver(model, ['x', 'y'], SolverConfig(seed=7))
start = [-0.7, 0.0]  # 在线使用时必须来自当前测得的 qpos
goal = Waypoint(targets=[PositionTarget('tool', [0.7, 0.0, 0.0])])
result = solver.solve(start, goal, budget_s=5.0)
if not result.success:
    # agent 根据 result.reason / diagnostic 生成中间状态；不自动发明接触技能。
    waypoints = [Waypoint(joint_positions=[-0.7, 0.7]),
                 Waypoint(joint_positions=[0.7, 0.7]), goal]
    remaining = max(0.0, 5.0 - result.stats['elapsed_s'])
    if remaining > 0:
        result = solver.solve_waypoints(start, waypoints, budget_s=remaining)
```

每个 waypoint 必须且只能指定一种目标：`joint_positions` 按 `active_joints` 顺序排列；`targets` 可同时约束多个 body 的位置，并可设置 body 局部坐标中的 `offset`。位置是模型世界坐标、单位米；hinge 关节为弧度，slide 为米。目前不支持姿态目标、自由基座规划、接触模式切换或动态障碍。

`start` 与 `trajectory` 使用 **MuJoCo 完整 qpos 顺序**，不是 G1 的 43 维 action。`joint_names` 是模型 joint 列表，`stats.joint_qpos_addresses` 给出各 joint 的 qpos 起点；自由关节占 7 维。`stats.active_joints` 与 `stats.qpos_indices` 一一对应。接控制器时必须按名称映射、以当前状态复核，再使用时间戳发送参考，不能直接把 full qpos 当作 Genesis/Isaac action，也不能调用 set_state 来播放路径。

## 预算、验证与限制

- `budget_s` 是整次调用共享的协作式 wall-clock 预算，在 IK、碰撞采样和 RRT 迭代中检查；不能抢占正在运行的原生数值调用。另有 `max_nodes`、`ik_iterations` 与 `ik_restarts` 上限。同一实例不要并发调用。
- 起点、关节限位、有限数值与四元数归一化在规划前检查。规划只改指定活动关节，其他 qpos 保持不变。IK 不收敛仅表示此算法在预算内未找到解，不证明任务无解。
- 碰撞检测遵从输入模型的 collision masks、排除对和几何。可用 `allowed_contacts` 显式声明允许的 geom-name 对；它只忽略该对碰撞，不建模抓取或支撑。障碍须已包含在模型里，且来自该 track 允许的几何观测；模块不读取任务私有状态或 verifier。
- 路径是按 `resolution` 离散采样的碰撞检查，不提供连续碰撞或正间隙保证。薄障碍需更小采样步长和独立执行检查。不要假定仅加载机器人 MJCF 就包含柜子、地面或箱子。
- 时间戳限制每个活动标量关节的插值速度；分段线性路径没有加速度/力矩、平衡与动力学可行性保证。执行器仍需平滑、跟踪、停止和物理结果验证。

失败原因包括 `invalid_request`、`invalid_start`、`invalid_goal`、`ik_not_converged`、`ik_collision`、`planning_exhausted`、`path_validation_failed` 和 `timeout`。失败返回空轨迹；`failed_segment` 是从 0 开始的段号，起点/请求失败时可能为 null。

## 验证记录（2026-10-16）

真实 MuJoCo 几何测试覆盖 L2 位置目标、RRT 避障与固定 seed 复现、L3 顺序/连续性、速度限值、冻结关节与在线数据隔离、不可达 IK、碰撞、超时和无效输入。RRT 输出另以更细采样独立检查碰撞。

G1 smoke test 在现有 50 维 qpos / 43 个标量关节模型上，仅移动 14 个双臂关节。L2 返回 7 个配置，L3 返回 8 个配置；双腕终点误差均通过 3 mm 阈值，基座和非活动关节保持不变。目标由已知姿态的 FK 构造，只验证规划，不代表自主感知、平衡、抓取、搬箱或 H1 任务成功。

后续接入点：Genesis 原生 planner / cuRobo backend；带姿态与接触约束的求解；轨迹跟踪执行器；成功执行后的参数化 skill 注册。当前不自动将未经物理验证的规划提升为 L1 skill。
