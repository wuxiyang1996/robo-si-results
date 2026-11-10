# H1 实施选型与同身体换手对照

本次按用户补充锁定实施方向：G1 29DoF＋Dex3-1 为主线，Inspire 为五指对照优先项，Stretch 使用 **Stretch 3**。这些选择不会改写已经执行的历史 profile。逐项版本和来源见 [选型 JSON](embodiment-selection.json)。

| 平台 | 当前候选资产 | 已确认的支持 | 尚需完成 |
|---|---|---|---|
| G1＋Dex3-1 | 官方 rev1.0 29DoF 身体＋每手 7 个主动自由度 | 官方模型、Isaac Lab 和 XR 遥操作入口 | 官方 rev1 身体在本 benchmark 中的 Genesis 控制与任务验证 |
| G1＋Inspire | 同一官方 rev1.0 身体＋DFQ 五指模型 | 官方集成模型；已保存独立被动加载运行 | 12 个 mimic 关节耦合、驱动单位/限幅、手部接触和完整任务 |
| Stretch 3 | SE3／eoa_wrist_dw3_tool_sg3 | 官方未标定 URDF、Stretch MuJoCo；标准柔顺夹爪及 D405 | 本地 Genesis 导入与动态检查、控制器及任务 |
| Agibot A3 | 官方 T3.0 候选 | 官方静态 URDF/MJCF/mesh；独立 SONIC 控制参考；被动加载运行 | 控制器移植及完整任务，不能把静态模型仓库当作可直接运行的控制栈 |

官方资料：[G1 产品](https://www.unitree.com/g1/)、[Unitree 模型](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description)、[Isaac Lab](https://github.com/unitreerobotics/unitree_sim_isaaclab)、[XR 遥操作](https://github.com/unitreerobotics/xr_teleoperate)、[Stretch 3 硬件](https://docs-arch.hello-robot.com/0.3/hardware/hardware_guide_stretch_3/)、[Stretch URDF](https://github.com/hello-robot/stretch_urdf)、[Stretch MuJoCo](https://github.com/hello-robot/stretch_mujoco)、[A3 模型](https://github.com/AgibotTech/A3-A3U-robot-model)、[A3 SONIC](https://github.com/AgibotTech/sonic_for_a3)。官方 Isaac Lab／MuJoCo／遥操作支持不等于 Genesis 已接通，也不代表本任务可完成。BrainCo 保留为未集成备选，不混入当前 Inspire 证据组。

## 同身体的可复查静态证据

对固定 Unitree commit `7919cba47a3f68888f3b084945b0ffbf3bb3763a` 的两个 URDF 做递归 XML 比较：**29 个共用活动关节、7 个共用固定关节、37 个共用连杆结构完全相同**，连杆比较包含惯量、视觉和碰撞定义；同时记录引用 mesh 的 SHA-256。[完整审计](g1-matched-body-audit.json) 保留逐项名称、差异集合、文件与 mesh 哈希。可从仓库根目录运行 `python infra/planning/audit_h1_hand_pair.py` 复核。

Dex3 模型共有 43 个活动关节、无 mimic；Inspire DFQ 有 53 个活动关节，其中 12 个带 mimic。后者的 53 不能作为 53 个独立电机的声明；Genesis 中的耦合和实际命令维度仍需实测。

既有 H1 使用的 Menagerie G1 是另一个历史模型。其运行、成功或失败均不可直接移作官方 rev1.0 身体或换手后的证据。旧 Stretch 4 作业 `8035305_1` 仍完整保留，但只记历史探索，不算 Stretch 3 验证。

## 换手实验的实施要求

1. 预先固定相同身体、世界、目标物、材质参数、随机种子、观测、目标、五项安全规则及预算；只列明末端执行器及必要驱动接口差异。
2. 每种手分别审计碰撞、自碰撞过滤、关节/力矩边界、mimic 耦合、指令单位和接触记录。被动加载或短暂落地不能证明稳定抓持。
3. 同时保存 high-level 的工具/抓法选择、low-level 的控制调用与参数、逐步物理状态轨迹及失败尝试，核查换手后是否改变策略。
4. “抓杆、握把手、夹持工具”分别建立接触保持、滑移、释放及目标完成谓词，再执行原始起点的完整专家解。不能用官方支持列表代替成功轨迹。
5. 特权状态专家只证明限定场景可行性；传感器输入 agent、成对机制对照、稳健性和正式准入另行验收。
