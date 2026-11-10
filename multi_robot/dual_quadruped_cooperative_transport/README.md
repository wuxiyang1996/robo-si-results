# Version H — Dual Quadruped Cooperative Long-Object Transport

**Category:** Tool Discovery · **Embodiment:** Multi-Robot (two Unitree Go1/Go2 quadrupeds) · **Task ID:** M4 · **Priority:** P0 — multi-robot cooperation and autonomous control harness construction

**Status:** The fixed preconnected base/hard privileged reference is complete and [published](../../infra/task-m4-en.html): 6/6 historical successes, current rejudgment 28/28 expectations matched, perturbations base 4/6 and hard 10/12. Autonomous docking, loading and detachment are incomplete. Connector v2 is stopped after B08/B09; [new mechanism design task](acceptance/release-preconnected-20261024/autonomous-coupler-next-design.json) is separate. Human review and second-person reproduction remain pending; `admitted=false`.

## 专家解（2026-10-20）

见 [solution/README.md](solution/README.md)。在场景变体 [solution/task_tow.json](solution/task_tow.json)（原 task.json + 两根预连接绳索 + 平台挡边，其余不变）上，两台 Go2 用训练的行走策略 + 脚本化协同拖运控制器完成张紧、直线拖运、L 形转角、入区与静置；独立监测层给出的 10 项物理证据全部为真，`multi_robot/evaluate.py` 判定 `goal_observed: true`（`success` 待作者准入）。原始地面摩擦 0.8 下 6 次扰动重复 4 次通过（外侧机器人转弯时接近抓地极限），地面 0.3 下 6/6。发现的设计问题：Genesis 摩擦取最大值，平台 0.3 摩擦在 0.8 地面上不起作用；单台 Go2 就能拖动满载平台，当前配置下协作不是必需的。视频：[μ=0.8](solution/runs/final-mu080/motion.mp4) · [μ=0.3](solution/runs/final-mu030/motion.mp4)。

**困难版**（[solution/task_hard.json](solution/task_hard.json)）：走廊收窄到 1.6 m、货物 50 kg、地面 0.3、时限 120 s。只拴平台前端两根绳时，1.5 m 以下的走廊不存在可拖拽的过弯路径；单台 Go2 在 120 s 内卡在拐角入口，基础版的编队控制器会让机器人失稳。专家解先在 (x, y, θ) 空间规划平台位姿，再让两台各自用纯追踪把自己的锚点拉向规划位置：38 s 送达，12 次扰动重复中 10 次全部通过。视频：[困难版](solution/runs/hard-final/motion.mp4)。

Two Unitree Go1/Go2 robots must cooperatively transport a long cargo box to a designated region through narrow passages and a 90° L-shaped corridor. Without manipulators, the quadrupeds cannot directly grasp the box. Ropes, towing connection points, a drag platform, and other interactive objects are available. The agent must discover a feasible towing and transport method and write the cooperative control program.

## Task

- Through physical interaction, discover each robot's towing capability and mobility limits, together with the cargo's mass, friction, and geometric constraints. Assess whether one robot can complete transport alone.
- Independently discover how ropes, connection points, or the drag platform can form a transport arrangement. Explore how connection locations affect cargo translation, rotation, and stability.
- Write a multi-robot control harness coordinating robot motion, towing direction, relative position, and rope tension for stable transport.
- At the L-shaped corner, jointly plan cargo translation and rotation. Adjust towing direction, speed, and formation to pass through narrow space without severe collisions or connection failure.
- Diagnose stuck cargo, slack ropes, insufficient towing force, or unsynchronized robot motion from execution feedback. Revise the towing strategy, motion order, or control harness.

These are candidate strategies for benchmark design, not instructions specifying a correct connection or cooperative program. Evaluate each robot alone and distinguish cooperation-required instances from cases where cooperation only reduces cost. Credit valid solo routes when they exist.

## Advanced Variants

Vary cargo length, mass, center of mass, ground friction, corridor width, and each quadruped's effective towing capability. Include unequal towing or mobility capabilities so the agent must discover the differences and dynamically allocate primary pulling and steering roles.

Every admitted solvable instance must retain at least one physically validated executable solution with the assigned controllers and resources. Test whether the agent adapts connection arrangements, cooperation strategies, and its control program. Capability changes must affect physical or controller behavior rather than only descriptive metadata.

## Connection and Tool-Use Interface

The robots have no manipulators. Do not assume they can grasp loose ropes, tie knots, load the drag platform, or move attachment points without a validated mechanism. During implementation, specify which connections are initially present and which attachment, release, or reconnection operations can be physically executed by the available bodies and hardware.

If docking or passive coupling is provided, publish its interface and physical preconditions without identifying the best connection point. Reconnection requires reaching and satisfying those conditions; an arbitrary remote attach command cannot substitute for physical interaction. A preconnected scene can validate towing control, but cannot demonstrate autonomous attachment construction. Drag-platform loading and use must likewise be executable or explicitly part of the initial scene.

## Physical Validation

Validate the full chain from the declared initial connection state through tensioning, straight towing, corner negotiation, recovery, and stable delivery. Check ground traction, actuator limits, gait stability, cargo friction, rope slack and tension, connection loads, and clearance for both robots, the cargo, and the towing geometry.

Rope behavior must represent the relevant slack, tensile force, and contact effects. Do not replace ropes with rigid links that transmit compression or allow them to pass through walls. Validate the supported rope/coupling model and controller before admitting a configuration. Any release or reconnection used by a solution must be part of the validated trajectory.

## Evaluation Contract

Deliver the correct cargo into the designated region and leave it stably supported while satisfying declared collision, robot stability, and connection-integrity constraints. Define numerical tolerances, severe-collision thresholds, and the final dwell time before evaluation. Deliberate release through a permitted interface is distinct from unintended connection failure.

Record both robots' actions, waits, towing geometry, tension feedback where available, stalls, slips, connection changes, recovery attempts, and total interaction costs. Evaluate whether the agent distinguishes insufficient traction or pulling capability from poor towing geometry, slack, synchronization errors, and geometric obstruction. Ground-truth force or cargo-state information is available only in tracks that explicitly permit it.

Verify continuous physical execution without state edits, external cargo propulsion, unphysical attachment changes, or contact bypasses. A successful straight pull alone does not establish feasibility through the L-shaped corridor.

## Implementation Priorities

- [ ] Build the two-quadruped scene, long cargo box, narrow passages, L-shaped corridor, tools, and target region.
- [ ] Define and validate initial connections and physically executable coupling, release, and platform-use operations.
- [ ] Validate single-robot capability limits and cooperative towing, tension control, turning, and recovery.
- [ ] Provide per-robot observations and control interfaces, and implement delivery, collision, stability, and connection checks.
- [ ] Validate at least one complete executable solution per admitted configuration.
- [ ] Add asymmetric capabilities and physical variants; evaluate role allocation, tool discovery, and cooperative harness adaptation.

## Core Capabilities Evaluated

Multi-Robot Coordination · Autonomous Tool Discovery · Cooperative Towing · Physical Reasoning · Harness Construction · Embodied Self-Modeling · Long-Horizon Planning · Failure Recovery

See the [Tool Discovery category](../../README.md#tool-discovery) and the benchmark proposal in [English](../../doc/self-modeling-benchmark-v4-en.html#team-m4) or [中文](../../doc/self-modeling-benchmark-v4-zh.html#team-m4).
