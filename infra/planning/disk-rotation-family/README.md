# DR：材质感知圆盘操作任务族

2026-10-29 · 9 个主任务均通过确定配置模拟验收：每项含两次正常初态执行、独立动作回放、分层计划、连续轨迹、物理审核和同次运行视频。DR-I01 仍不计入正式任务；未验证的身体、工具和泛化结论保持 unknown。

[中文](README.md) · [English](README-en.md) · [JSON](task-design.json)

统一目标：将自由放置的圆盘转至目标方向，控制圆心漂移，撤手后保持稳定。不指定工具、臂数或换点次数。圆盘保持桌面支撑，不通过抬起、焊接、位姿写入或对象外力完成旋转。

[执行证据汇总 / Execution evidence](EXECUTION.md) · [All attempts](/infra/disk-family-evidence/monitor.json) · [Source and video validation](/infra/disk-family-evidence/artifact-validation.json)

## 主任务清单

| ID | 分组 | 难度 | 任务 | 场景与考察 | 优先身体 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| [DR-01](/infra/task-dr-01-zh.html) | 原始 | L1 | 均质圆盘旋转 | 保留 0.1.0：均质圆盘、±30°，完成接触建立、旋转和稳定释放。 | Dual Panda | 已通过确定配置模拟验收 |
| [DR-02](/infra/task-dr-02-zh.html) | 接触推理 | L2 | 分区材质接触选择 | 侧面存在不同摩擦区域；通过观察或试探选择有效接触位置。初始有效区／低效区为配对配置，允许持续滑动到有效区。 | Dual Panda | 已通过确定配置模拟验收 |
| [DR-03](/infra/task-dr-03-zh.html) | 接触推理 | L2 | 旋转阻力与圆心漂移权衡 | 独立改变侧面和桌面摩擦；区分打滑、旋转阻力和中心漂移，调整接触力与运动方式。先用均质侧面隔离这一问题。 | Dual Panda | 已通过确定配置模拟验收 |
| [DR-04](/infra/task-dr-04-zh.html) | 接触推理 | L3 | 受限接近区域下的连续旋转 | 桌面固定障碍限制末端沿圆周连续运动，但保留候选接触区域；规划撤离、绕行、重新接触与后续旋转。换点必要性待验证。 | Dual Panda | 已通过确定配置模拟验收 |
| [DR-05](/infra/task-dr-05-zh.html) | 身体–场景相性 | L3 | 单臂与双臂的接触分工 | 同一圆盘与世界，比较单臂分段推动和双臂协同操作；考察有效力矩与圆心约束，不预设单臂不可解。 | Single Panda / Dual Panda | 已通过确定配置模拟验收 |
| [DR-06](/infra/task-dr-06-zh.html) | 身体–场景相性 | L3 | 移动改变接近方向 | 部分区域超出初始操作范围；移动机器人可绕桌建立工作位，固定臂检查其他合法路线。不同身体须分别核验可达性。 | Stretch 3 / Single Panda | 已通过确定配置模拟验收 |
| [DR-07](/infra/task-dr-07-zh.html) | 身体–接触相性 | L3 | 推动与夹持方式选择 | 共同可达区域内比较末端接触方式；允许侧推、侧面捏持等，圆盘始终保持桌面支撑。同一 G1 身体和基座条件，只换手及控制映射。 | G1 + Dex3 / G1 + Inspire five-finger hand | 已通过确定配置模拟验收 |
| [DR-08](/infra/task-dr-08-zh.html) | 身体–工具相性 | L3 | 可选接触附件选择 | 提供高摩擦垫、带柄接触块等；检查获取、稳定持用、切向力传递与撤出。原末端足够时可直接完成，附件必须真实改变接触物理。 | G1 + Dex3 / G1 + Inspire five-finger hand / Stretch 3 | 已通过确定配置模拟验收 |
| [DR-09](/infra/task-dr-09-zh.html) | 协作 | L3 | 异构机器人协作旋转 | 固定臂和移动操作机器人自主分配约束漂移、推动与重新定位的职责；结束时双方撤离。允许合法单机解，协作收益待验证。 | Panda + Stretch 3 | 已通过确定配置模拟验收 |

## 条件性对照（不计入 9 个主任务）

| ID | 分组 | 难度 | 任务 | 场景与考察 | 优先身体 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| DR-I01 | 条件性对照 | — | 当前身体与现场附件均无法完成 | 需排除全部合法路线，并配一个仅改变关键能力或附件的可解孪生。安全撤离、圆盘稳定后报告无法完成；证据不足保持 unknown。 | 待绑定 | 设计待验证 |

## 难度、配置与去重

- L1：基础接触执行；L2：接触条件判断与方法选择；L3：身体能力、接触切换、工具或协作适配。难度是设计目标，须经实测确认。
- 独立操作问题算任务。embodiment、旋转方向、角度、材质参数、seed、信息披露和消融作为配置；不铺满笛卡尔积。
- 参数公开、材质适配未知、部分物理参数隐藏单列。隐藏指不向被测 agent 暴露真值；作者配置和审计仍保存完整参数。
- DR-02 先固定底面条件考接触区域选择；DR-03 先用均质侧面考阻力与漂移。若 DR-04 与 DR-06 只有同一工作空间瓶颈，合并或降为配置。
- DR-05 改变臂数；DR-07 同一身体只改变手。DR-06 的跨平台比较同时改变底盘、末端和工作空间，只解释为整体身体适应。
- Stretch 优先核验已有 Stretch 3 资产；Stretch 4 后续另验，不借用厂商参数。现有 Panda 参考是球形推头，不能把夹持当作已验证能力。

## 共同判定与证据边界

主指标为完整有效成功。接受所有满足目标和公开约束的合法解；不用工具、不换点、单臂完成均不扣分。完成时间、探测行为、接触切换、中心偏移、峰值接触力、协作方式和附件使用单独记录，不补偿失败。

DR-01 冻结 0.1.0 原配置、评分与参考证据：两个确定配置各三次完整执行（6/6），独立动作回放 2/2；重复不代表随机域验证。名义场景 fixed_contacts 为 18.52 s，完整专家为 43.48 s。fixed_contacts 仍沿圆周运动，只是不撤离换点。因此换点必要性、双臂不可替代性和异构协作收益均未成立。

新增场景以原判据为起点：最终角度误差 ≤3°，全过程／最终圆心偏移 ≤30／10 mm，撤手后稳定 2 s，倾斜 ≤5°；沿用原速度、受力口径及 120 s 预算作为初始候选。所有调整须在扩展配置中公开、执行前冻结，不能追溯改写原参考。每种身体的执行器和稳定性约束独立核验。

侧面摩擦、盘底–桌面有效摩擦、质量与惯量独立配置。Genesis 1.4.3 的接触摩擦取两侧系数的较大值：只降低盘面系数可能被高摩擦推头掩盖，必须核验实际接触对。分区随物体旋转；附件通过真实接触传力。先固定质量、惯量与几何，避免把多个变化混成材质效果。

特权状态反馈专家与感知 agent 分开统计。比较 fixed_contacts、single_arm、原完整反馈专家及接触自适应专家；它们是对照策略，不新增任务。单次失败、超时或 IK 搜索失败均不构成全路线不可解证书。DR-I01 只有全路线证据及可解孪生成立后才可计为正确退出评测。

## 开发顺序与当前状态

先 DR-01—04；身体相性探针后绑定 DR-05—08 的配置；最后 DR-09 与 DR-I01。每项保留完整目标、候选路线、能力边界、证据状态和实际使用策略。未验证项保持 unknown，不能把草稿代码当作参考见证。

已按后续授权恢复实现并运行逐项专家与消融。当前结果以执行证据汇总及各任务页为准；启动错误、物理失败和完整成功都保留。G1、单臂和移动机器人路线尚未验证的部分保持 unknown。没有全路线证书时不把 DR-I01 标为不可解。

## 参考资料

[原版任务页](/infra/task-disk-rotation-zh.html) · [任务族总表](../task-families.md) · [装配任务族](../assembly-family/README.md) · [受限空间任务](/infra/task-space-extraction-zh.html)


## 当前执行与验收

- [DR-01](/infra/task-dr-01-zh.html): accepted_simulation_scope · rc01 · 43.480000000000004 s.
- [DR-02](/infra/task-dr-02-zh.html): accepted_simulation_scope · rc01 · 60.5 s.
- [DR-03](/infra/task-dr-03-zh.html): accepted_simulation_scope · rc01 · 45.04 s.
- [DR-04](/infra/task-dr-04-zh.html): accepted_simulation_scope · rc03 · 78.54 s.
- [DR-05](/infra/task-dr-05-zh.html): accepted_simulation_scope · rc01 · 98.5 s.
- [DR-06](/infra/task-dr-06-zh.html): accepted_simulation_scope · a12 · 114.22 s.
- [DR-07](/infra/task-dr-07-zh.html): accepted_simulation_scope · rc01 · 85.0 s.
- [DR-08](/infra/task-dr-08-zh.html): accepted_simulation_scope · a06 · 85.0 s.
- [DR-09](/infra/task-dr-09-zh.html): accepted_simulation_scope · rc03 · 63.32 s.

[完整验收报告](/infra/disk-family-evidence/acceptance.json) · [执行前冻结的验收条件](/infra/disk-family-evidence/acceptance-contract.json)

DR-02/03 的 fixed_contacts 仍能成功；DR-04 的差异只支持所测控制器及障碍配置。DR-05 的单臂与双臂均可解。G1 五指手、附件成功持用、协作必要性及跨随机域泛化尚无结论。失败记录不会改写为不可解证明。
