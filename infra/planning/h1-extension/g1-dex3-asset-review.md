# G1 rev1 Dex3：官方资产与独立被动检查

Gamma 作业 `8036343` 完成 400 个物理步、2.0 秒、401 行连续实测状态。只检查模型加载及有限状态物理推进，不构成 H1 任务成功、手部控制验证或稳定性认证。此前 Inspire 证据保留。

## 来源与结构

使用 [Unitree 官方固定提交](https://github.com/unitreerobotics/unitree_ros/tree/7919cba47a3f68888f3b084945b0ffbf3bb3763a) 中 `robots/g1_description/g1_29dof_with_hand_rev_1_0.urdf`；[原许可证](asset-smoke-evidence/8036343_dex3/LICENSE-unitree_ros.txt)与逐文件哈希均保留。模型 SHA-256：`97da67732d067c3147fc5fb7b7bafc8982718f4e7f8c92ff82266a4d9c07200d`。

原始 URDF 有 53 个 link、52 个 XML joint，其中 43 个非 fixed joint；87 个网格引用全部存在。此次模型未转换，也未修改结构、驱动或质量。声明质量合计 34.394234 kg，不是实机称重。Genesis 导入结果为 49 个模拟自由度（包含自由根）及 50 个 qpos；这些是结构与模拟计数，不是电机数量。

[配对身体静态审计](g1-matched-body-audit.json)与此前 Inspire 候选的被动检查可分别复核。两套手部的 mimic 约束执行、独立驱动映射、控制器和配对任务结果仍未验证；不能将 Inspire 的结构关节数解释为电机数。

## 预声明设置与实测结果

| 项目 | 记录 |
| --- | --- |
| 预算 | 1 GPU，最多 2 秒仿真 / 400 步，20 分钟墙钟 |
| 物理设置 | dt 0.005 s；自由根；地面；self-collision 开关开启；seed 0 |
| 初始根位置 | `[0, 0, 0.85] m`，与原 Inspire probe 相同 |
| 控制 | 无；默认关节姿态的被动演化 |
| 实际状态 / 步数 | 401 / 400，连续时间核验通过 |
| 墙钟时间 | 57.26 秒 |
| 末根节点线速度 | `1.082937918 m/s` |
| 末根节点角速度 | `1.885588795 rad/s` |
| 日志中的中性碰撞过滤对 | 未见该类记录；不代表完整碰撞覆盖认证 |
| 凸包估算惯量警告 | 5 条；原始日志完整保留 |
| task_success / stable_pose_claimed | null / false |

末根位置约为 `[0.3852, 0.0841, 0.5032] m`，末段仍明显运动。本次无稳定控制器，不能据此推断手型优劣、任务可解性或不可解性。与 Inspire 的相同被动设置只用于接入检查，不是受控任务对照实验。

## 证据

[汇总 JSON](g1-dex3-asset-review.json)、[原始结果](asset-smoke-evidence/8036343_dex3/result.json)、[预声明计划](asset-smoke-evidence/8036343_dex3/predeclared-plan.json)、[来源与所有文件哈希](asset-smoke-evidence/8036343_dex3/preflight.json)、[静态审计](asset-smoke-evidence/8036343_dex3/static-audit.json)、[原始日志](asset-smoke-evidence/8036343_dex3/slurm.log)、[完整状态日志（无损 gzip）](asset-smoke-evidence/8036343_dex3/states.jsonl.gz)。

完整状态 SHA-256：`cd364e0db37a91998db3b54ab37ecf99af1542d2fa354793ee2697cf4d164294`。冻结执行工具 SHA-256：`46f3931dfa04f7f8026ccc552ad665c7dd57cc5c9ad7c0c58dd94de9b3204ff4`，与原 Inspire 及其他资产 probe 相同。所有源缓存文件、87 个引用、预声明计划与来源凭据均运行后复核。

独立原始工作区：`/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/asset-smoke-runs/8036343_dex3/`。聚合清单现有六个独立被动资产 probe；资产检查不进入 H1 任务成功或完整任务执行计数。
