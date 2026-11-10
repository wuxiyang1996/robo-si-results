# Stretch 3：固定官方资产与独立 Gamma 被动检查

Stretch 3 SE3 / DW3 / SG3 已完成独立加载检查：Gamma 作业 `8036300`，400 个物理步、2.0 秒、401 行连续实测状态。没有接入任务控制器，不构成 H1 任务成功、稳定操控或完整自碰撞认证。原 Stretch 4 文件及证据均保留，未覆盖。

## 来源与静态审计

- 官方 [stretch_urdf 固定提交](https://github.com/hello-robot/stretch_urdf/tree/c8c6e27e1f87db126118049f22611399253cbe2b)：使用 `stretch_urdf/SE3/stretch_description_SE3_eoa_wrist_dw3_tool_sg3.urdf`，模型 SHA-256 为 `14ef56041efaa5cae405ce2ae4aa7a6ac45c98cc0bdc0c3ff2a873c6241627f1`。许可证为 [Clear BSD](https://github.com/hello-robot/stretch_urdf/blob/c8c6e27e1f87db126118049f22611399253cbe2b/LICENSE.md)。
- 61 个 link、60 个 joint、71 个网格引用，引用文件全部存在；URDF 声明质量合计 `24.789443580770484 kg`，不等于实机称重或承载能力。
- 三个原始零质量 link 是固定 ArUco 标记：`link_aruco_shoulder`、`link_aruco_top_wrist`、`link_aruco_inner_wrist`。因此通用审计的“所有声明质量均正值”标记为 false；没有把这些零质量改成虚构质量，也没有修改驱动、关节结构或网格。
- 官方 [stretch_mujoco 固定提交](https://github.com/hello-robot/stretch_mujoco/tree/c78d6a1cd79bb5ead1b679610299563c1a91124a) 的 `stretch_mujoco/models/stretch.xml` 也已缓存；[Clear BSD 许可证](https://github.com/hello-robot/stretch_mujoco/blob/c78d6a1cd79bb5ead1b679610299563c1a91124a/LICENSE)保留。101 个直接 mesh / texture 引用全部存在，本次没有执行该 MJCF 模型。

无需模型转换。配套 MJCF 使用 `compiler assetdir="assets"`；静态审计器原先没有识别它，曾误报缺文件。已按照 [MuJoCo 官方定义](https://mujoco.readthedocs.io/en/stable/XMLreference.html#compiler-assetdir)补齐 `assetdir` 对 `meshdir` / `texturedir` 的默认规则和显式覆盖优先级，复核为无缺失。这个修复只影响静态路径解析，没有改资产或正在运行的冻结 probe 源码。

## 真实 GPU 结果

| 项目 | 记录 |
| --- | --- |
| 预算 | 1 GPU，最多 2 秒仿真 / 400 步，20 分钟墙钟 |
| 物理设置 | dt = 0.005 s；自由根节点；地面；自碰撞开关开启；seed 0 |
| 初始根位置 | `[0, 0, 0.1] m`，与旧 Stretch 4 被动检查相同 |
| 控制 | 无；默认关节姿态的被动演化 |
| 实际状态 / 步数 | 401 / 400，时间连续性核查通过 |
| 总墙钟 / 加载墙钟 | 108.35 s / 103.30 s |
| 导入自由度 | 20 个 dof（包含自由根）；21 个 qpos |
| 末根节点线速度 | `2.8860445378e-7 m/s` |
| 末根节点角速度 | `1.0300557816e-5 rad/s` |
| 中性碰撞对过滤 | 23 对，原始清单保留 |
| 凸包估算惯量警告 | 1 条 |
| task_success / stable_pose_claimed | null / false |

尽管末速度较小，当前没有稳定控制或带载操控验证。Genesis 导入器依然过滤中性姿态碰撞对，并使用了惯量近似；不能把自碰撞开关开启解释为完整碰撞认证，也不能从这次资产检查推断任务可解或不可解。

## 可复查证据

[汇总 JSON](stretch3-asset-review.json)、[原始结果](asset-smoke-evidence/8036300_stretch3/result.json)、[预声明计划](asset-smoke-evidence/8036300_stretch3/predeclared-plan.json)、[来源与所有文件哈希](asset-smoke-evidence/8036300_stretch3/preflight.json)、[静态审计](asset-smoke-evidence/8036300_stretch3/static-audit.json)、[配套 MJCF 引用审计](asset-smoke-evidence/8036300_stretch3/companion-mjcf-static-audit.json)、[原始日志](asset-smoke-evidence/8036300_stretch3/slurm.log)、[完整状态日志（无损 gzip）](asset-smoke-evidence/8036300_stretch3/states.jsonl.gz)。

完整状态源 SHA-256：`44ba0f348d48a01912bc938052ae12eab986c7dd2e39d9618ecfa914da9b38a0`。冻结运行源码 SHA-256：`46f3931dfa04f7f8026ccc552ad665c7dd57cc5c9ad7c0c58dd94de9b3204ff4`，与旧四个资产 probe 完全相同。源 URDF、所有网格及逐文件缓存哈希已在运行后重新检查。

独立工作区：`/fs/gamma-projects/vlm-robot/robo-si-local-tests/h1-implementation-20261027/asset-smoke-runs/8036300_stretch3/`。聚合清单现为五个独立被动资产 probe；H1 任务成功计数仍为零，资产检查不进入任务执行计数。
