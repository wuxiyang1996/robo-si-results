# 14 项任务：分层规划与可行性筛查

<!-- current-retrieval-registration -->
当前 H1/M1/M3 登记：[总表](task-families.md) · [English](task-families-en.md) · [JSON](current-task-registry.json)。H1 共 22 个选定独立任务（20 项拆分＋2 项新增操作），接受全部合法完整解；M1 登记 9 个 case（含原始任务）；M3 登记 6 个 case（含原始任务），载荷能力待核验。
<!-- /current-retrieval-registration -->

## M1 extension · 2026-10-27

[M1 任务族设计](m1-extension/README.md) · [English](m1-extension/README-en.md) · [JSON](m1-extension/task-design.json)。一个任务族：直接取／找帮助 × 五指灵巧手／三指手／轮式 × 指定机械臂交接交付要求 Y/N，共 12 个候选格。N 仍允许找帮助，Y 的要求公开写入指令；Y/N 保持身体、场景、辅助机器人和工具不变。先验证三指四格，难度逐实例标注。01–08 保留为族内场景／对照，04 推车暂缓；不可完成对照仍须全员空手到 Q 停稳。仅设计，新增仿真 0，原 M1 证据及 14 项统计不变。

## H1 extension · 2026-10-27

[跨身体工具选择与主动放弃任务卡](h1-extension/README.md) · [English](h1-extension/README-en.md) · [JSON](h1-extension/task-design.json)。目标为 5 种平台、6 种配置，包含机械臂型号待定的 Go1＋轻量臂＋夹爪；8 个任务族与 4 类不可完成对照，放弃须实际移动到 Q 区并停稳。当前为设计提案，未新增仿真；不计入原 14 项交付或 H1 已验证范围。

当前取物任务族：[H1 / M1 / M3 总表](task-families.md) · [English](task-families-en.md)。H1 自主登高；M1 目标交接与低柜交付；M3 为轻量伙伴辅助取物的条件性设计。旧 H1 协作补充已被取代；新 M3 抬升先审核当前 2 kg 约束与资产。

<!-- reference-design-index -->
**14/14 scoped reference execution witnesses; 14 reference design documents.** [参考解与设计总览 / Reference design index](../reference-designs-zh.html). Sandbox runtime acceptance and formal admission remain separate; original scores are unchanged.
<!-- /reference-design-index -->


**14 项统一目录：** [原 12 项＋DiskFlip＋Sokoban](INVENTORY.md)。原批次 62 个技能已展开为 193 个动作；新增两项使用原生的具体案例映射，不与合同动作混算。

**新口径剩余工作：** [12 项逐任务盘点](hierarchical-evaluation/READINESS.md) 已选定每项的完整成功核对候选。原批次已有 12 份高层计划、62 个技能与 193 个有序动作；其 12 项三层映射审阅仍待完成。通用滚动规划、任意随机起点衔接和连续技能区间不作为最低设计门槛。

[分层评分与专家解设计 v0.2](hierarchical-evaluation/README.md) 已提供 12 项、62 个技能的专家合同。当前最低目标是验证高层→低层→轨迹的映射，并至少有一条声明配置的连续端到端生成见证；不要求任意随机状态可解或通用技能拼接。新通用控制接口未绑定不否定已有专家见证，原始评分不变。

**除 H1 外的 11 项状态已按分层标准更新：** [网页总览](../status-zh.html#layered-progress) · [机器可读状态](layered-status.json)。分别报告任务级完整见证、技能证据、实例级未确定项和执行级规划要求；不要求逐随机实例完整求解。本次 H1 文件和状态保持原样。

**技能证据整理第一批：** [H2、H5、Hanoi、Assembly](skill-evidence/README.md) 已把历史完整运行、局部探针、检查点后缀、重复与失败绑定到 19 个技能合同，并归档实际联合配置。连续适用区间仍未声明，没有新增仿真或随机筛查通过记录。

**2026-10-26 设计与验收原则已更新：** [设计原则](../task-design-zh.html#hierarchical-planning)、[验收标准](../acceptance-zh.html#screening)、[统计规则](../protocol-zh.html#feasibility-reporting)及[机器可读政策](acceptance-policy.json)。四类实例结果与任务准入 gate 分开，完整解不再是每个随机实例的前置要求。

本目录把当前任务整理为 **高层子目标 → 低层技能与接触合同 → 关键状态 → 按需生成局部轨迹**。本轮交付的是作者侧规划设计和机器可读数据；没有生成完整轨迹，没有启动新仿真，也没有实现通用在线规划器。

已有成功记录继续提供对应配置的物理见证。随机实例不要求逐个求完整解；先检查必要条件、关键动作与段间衔接，证据不足则保留“未确定”。本目录不改变已有评分、任务完成标记、公开限值或正在进行的验收工作。

| 任务 | 高层参考路线 | 最需要检查的局部环节 |
| --- | --- | --- |
| [H1 支撑物取物](tasks/H1.md) | 移动支撑物 → 登高 → 取物 → 中转放置 → 空手下降 → 重抓交付 | 支撑承重、下降与重抓入口衔接；固定与两组随机完整见证已有；原三组账本2个完整见证、1个未确定 |
| [H2 推车运货](tasks/H2.md) | 轨道对准 → 装车 → 第一通道 → 第二通道 → 车载交付 | 装载支撑转移、机器人与车货组合转角 |
| [H3 双 G1 自闭门搬运](tasks/H3.md) | 开门 → 建立支撑 → 取件 → 穿门 → 台面交付 | heavy_prop 的独立箱撑门；no_prop 的另一机器人持续撑门 |
| [H4 搭板过缺口](tasks/H4.md) | 布桥 → 空载过桥 → 取物 → 负载返回 → 放置 | 板端支撑、负载后的足点与抗滑 |
| [H5 杠杆辅助运输](tasks/H5.md) | 杠杆接合 → 抬升 → 轮滑托架承接 → 推运 → 停稳 | 力臂与接触可行性、撤去抬举后的独立支撑 |
| [H6 负重上下楼](tasks/H6.md) | 地面取箱 → 逐级上楼 → 峰顶稳定 → 逐级下降 → 放箱站稳 | 每级踏面与连续双手承托 |
| [M1 双机货架取物](tasks/M1.md) | G1 取出容器 → X5 夹取 → 到低柜 → 柜内放置 → 释放 | 交接可达性、最后机器人接触之前的柜体承重 |
| [M2 双 G1 长物搬运](tasks/M2.md) | 两端抓持 → 合抬 → 转弯 → 搬运 → 下放释放 | 两机与长箱联合净空、两端负载同步；限 0.25 kg |
| [M3 小机器人辅助取物](tasks/M3.md) | 承托抬升 → 箱面取物 → 返回重抓 → 下放 → 撤手 → 交付 | 接触与承重转移；允许不影响操作的轻微运动 |
| [M4 双四足拖运](tasks/M4.md) | 预连接检查 → 张紧 → 直拖 → 转角 → 目标停稳 | 张力分配、滑移与整体扫掠；没有自主对接／解绑步骤 |
| [Hanoi 桌面汉诺塔](tasks/Hanoi.md) | 选合法顶盘 → 脱杆 → 转移 → 放置提交 → 循环 | 符号规则与真实放置提交一致，不预展开全程关节轨迹 |
| [Assembly 桌面装配](tasks/Assembly.md) | 工具扶稳平台 → 套筒 → 顶盖 → 全部释放稳定 | 工具→平台→套筒→顶盖的持续支撑链 |

## 每个实例生成什么

1. **高层计划**：子目标、所选分支和依赖关系。
2. **低层技能合同**：进入条件、操作、支撑与接触、完成条件、失败处理。
3. **关键状态要求**：目标位姿区域、速度条件、接触模式和承重要求。H1 已绑定两个连续成功实例的实际关键状态；其余未提供数值见证的条目保留 `null`，不能当作已求解。
4. **筛查记录**：哪些检查通过、失败、缺证或超时，使用的场景／资产／控制器版本以及证据引用。
5. **局部求解请求**：只有执行或关键片段验证需要时才生成；本轮没有生成此类轨迹。

完整成功记录不自动转化为每个技能的独立验证，更不自动形成适用于随机区间的技能库。当前每项 `applicability_interval` 和随机数值范围都为 `null`，避免把场景生成器允许的范围当作已验证范围。

## 筛查顺序与结果

| 顺序 | 检查 | 无法确认时 |
| --- | --- | --- |
| 1 | 任务、变体、资产、物体身份、公开规则和证据版本是否匹配 | 未确定，不能借用另一个变体的成功 |
| 2 | 必要几何条件：目标容纳、开口、落足／支撑面、基本通路 | 有明确必要条件反例才拒绝；IK 搜索没找到解仍是未确定 |
| 3 | 关键状态：IK、碰撞、载荷与接触力平衡 | 静态检查通过仅保留候选，不等于动态执行通过 |
| 4 | 前段退出与后段进入是否在实际状态上兼容 | 未知速度、接触、估计误差或剩余时间均不能跳过 |
| 5 | 必要时对支撑切换等困难环节做短探测 | 使用计算预算；未完成记未确定，不默认启动全程 |
| 6 | 汇总证据，决定保留路线、换路线或停止 | 筛查通过仍不称为完整物理可解证明 |

结果分为 `witnessed_full`（匹配实例已有完整物理见证）、`screen_pass`（指定必要检查已通过）、`unknown`（缺证／超时／未实现检查）、`rejected`（有明确检查失败）。另外记录拒绝范围：某条路线失败，不代表所有路线无解。完整见证必须匹配场景与源码等身份信息，不能仅匹配 seed 或任务名。

`instance-template.json` 给出了记录格式，初始全部为 `not_run` / `unknown`。新抽样数仍为 **0**；H1 已对原三组实例完成证据分类，结果见[实际账本](h1/ledger.json)，没有把模板当成已通过结果。

## 计算与执行策略

- 默认只生成计划与检查请求，不启动仿真。调用方另设筛查墙钟、IK 候选数、短探测数和探测步数预算；未设置预算时不自动运行求解器。H1 已提供限制检查数量和墙钟的证据筛查入口，短仿真预算固定为零；通用物理求解与探测调度器尚未实现。
- 优先复用身份匹配的关键状态或局部记录；改变质量、摩擦、几何或控制器后，相关证据需要重新匹配，不能只按任务 ID 命中缓存。
- 只为活动阶段生成短段轨迹。实际上一阶段的位姿、速度、抓持、支撑和剩余任务时间必须满足下一阶段条件；不靠恢复理想快照拼接完整成功。
- 微小抖动本身不构成失败，功能、真实接触、公开限值与原判定必须继续成立。已有内部控制器保护与基准硬限分别保留；本材料不放宽任一执行检查。
- 代表性全程执行用于方案确认、回归或原有发布要求，不为每个随机实例自动执行。H1 已按用户后续决定迁移为[分层证据验收](h1/README.md)：原三组样本与旧补跑清单保留，完整补跑不再是资料交付前提；仿真保持暂停。
- 保留全部抽样、拒绝、超时和失败。基准样本不因失败而换 seed；自建候选生成与基准评测分别统计。

## 证据与文件

- [catalog.json](catalog.json)：14 项计划索引（原 12 项合同及新增 2 项原生映射）。
- `tasks/<任务>.json`：结构化计划；`tasks/<任务>.md`：中文审阅版。
- [source_snapshot.json](source_snapshot.json)：生成时的任务状态快照；每个计划另绑定实际来源文件的 SHA-256。
- [validation.json](validation.json)：任务清单、状态／技能引用、来源哈希和生成期间一致性检查。它不是物理验收结果。
- [generate_plans.py](generate_plans.py)：标准库生成器，不导入或运行仿真。重新生成会更新本目录生成文件，应先检查源状态是否发生变化。

本目录属于作者参考材料，包含路线与特权参考证据。本轮未修改 agent 的指令或运行接口；后续集成打包时应将本目录排除在 agent 可见文件之外。H3 采用当前双机器人版本；旧单机器人 H3 不混入。M3 当前完整证据仍使用 65 mm 球，方块变体需要独立检查。H4 五个历史源码版本的缺口继续保留。

<!-- assembly-family-index:start -->
## 装配任务族 · 2026-10-28

10 个独立任务：Assembly 4、Gear Assembly 3、Reference Assembly 3；含 3 个原始任务和 7 个新增任务。身体与难度作为评测配置，不重复计数。五指手优先用于 Gear 工具相性；新增设计均待验证，本次新增仿真 0。

[完整设计](assembly-family/README.md) · [English](assembly-family/README-en.md) · [JSON](assembly-family/task-design.json)
<!-- assembly-family-index:end -->

<!-- disk-flip-family-index:start -->
## Disk Flip family · 2026-10-29

4 个 task variants、3 种 embodiment、6 个选定 settings，使用 3 类盘体（2 套主要几何）。6 个配置均有候选专家与物理执行；5 个完整成功见证，1 个仍待完成。

[中文设计](disk-flip-family/README.md) · [English design](disk-flip-family/README-en.md) · [JSON](disk-flip-family/task-design.json)

Original evidence and admission remain scoped to DF-01-G.
<!-- disk-flip-family-index:end -->

<!-- disk-rotation-family-index:start -->
## DR 圆盘操作任务族 · 2026-10-28

9 个主任务＋1 个条件性对照。已启动逐项实现与物理执行；各任务页记录专家、high/low planning、对应轨迹、物理审核及视频。成功、控制失败和启动错误分别列出；身体、参数与重复运行不增加任务数。

[完整清单](disk-rotation-family/README.md) · [English](disk-rotation-family/README-en.md) · [JSON](disk-rotation-family/task-design.json)
<!-- disk-rotation-family-index:end -->
