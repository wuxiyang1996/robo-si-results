# DR 0.2.0-rc1 发布补充

本次交付是可复现研究候选包：九项确定配置参考解、机器人接口、隔离运行和有限扰动／消融证据。主 benchmark 正式准入仍为 false。参考解验收、隔离接口验证、独立 coding agent 成绩和人工签署分别记录。

## 可运行内容

- DR-01–09：原有每项两次正常初态执行与一次独立执行器回放，保留专家、high/low plan、400 Hz 轨迹、物理判据和两个视角视频。
- Agent SDK：只提供机器人关节状态、真实末端坐标系固定的 RGB 相机，以及按 URDF 标定的 Stretch 头部 RGB 相机、公开目标和关节命令；不提供物体状态、材料系数、奖励、场景文件或 simulator setter。
- Trusted worker：使用原有 Genesis 1.4.3 场景与受限执行器，400 Hz 连续记录；50 Hz 控制。评分器从轨迹重新计算成功和历史约束。
- 运行隔离：普通进程仅用于开发；评测使用只读容器文件系统、独立网络／进程／挂载命名空间和唯一 Unix RPC 通道。集群实际验证使用 Bubblewrap；Podman 启动失败记录保留，不计为通过。
- 执行记录：冻结场景、交付程序、源码清单、镜像身份、哈希链 RPC、每段命令对应的物理区间。Agent 自填的 planning label 是记录，不自动认定为正确推理。

下载文件及 SHA-256 见 `downloads-0.2.json`。作者源码包含场景、专家、评测器与模型，不得挂载给被测 agent；SDK 是单独的严格白名单包。隐藏采样密钥、配置、轨迹和视频不公开。

## 运行

使用与参考包相同的 Linux / Python 3.12 / Genesis 1.4.3 / CUDA / EGL 环境。在源码根目录：

```bash
export OMP_NUM_THREADS=4 PYOPENGL_PLATFORM=egl
python -m unittest disk_family.sandbox.tests.test_contract disk_family.sandbox.tests.test_scoring tests.test_disk_materials tests.test_disk_rotation
python -m disk_family.sandbox.launch --mode dev --isolation process --case DR-01 --agent-dir disk_family/sandbox/agent_sdk/examples -- python inspect.py
python -m disk_family.sandbox.launch --mode eval --case DR-01 --rootfs-archive /path/to/dr-agent-rootfs.tar --agent-dir /path/to/agent -- python solve.py
python -m disk_family.sandbox.launch --mode grade --episodes 2 --case DR-01 --rootfs-archive /path/to/dr-agent-rootfs.tar --agent-dir /path/to/agent -- python solve.py
```

上述 grading 命令是同一公开场景的接口检查。真正的隐藏评测须以 `--scenario-file /private/schedule.json` 提供作者密封的 schedule。每轮均从正常初态和新的交付目录启动；eval / grade 不允许 reset。

Agent 根文件系统是 Dockerfile 所声明固定 Python 镜像和 NumPy 2.5.3 的 OCI 导出，不含 Genesis、场景、专家或隐藏数据。解压文件的完整校验在运行前执行。可在具备 rootless Podman 的主机上构建；集群无 subordinate UID 映射时使用发布的 rootfs 和 Bubblewrap。不要把 process 模式改名为隔离评测。该环境没有外部网络代理。

Stretch 初始头部图像不保证盘面可见。额外的非特权观测试验通过真实头部关节扫描，在 8 秒后取得含圆盘的 RGB 图像（`sensor-0.2.json`）；该试验只验证可观测性，不计作操作成功。

完整轨迹回放通过公共关节接口，证明接口可承载成功执行；它使用已发布的参考动作，属于 open-loop integration witness，不是独立 coding agent 或策略发现结果。空操作和越权程序是测试夹具，也不是模型成绩。

## 扰动与消融协议

42 项预先固定运行：18 项开发配置（每任务标称／反向），18 项 held-out 配置（姿态／材料，阻力／质量），6 项控制对照。参数在执行前采样并以 SHA-256 承诺；不替换失败 seed，不用完成时间、局部旋转或生成视频代替完整成功。具体结果见 `cohort-0.2.json`。

另加两项事后可行性复核：DR-02 原自适应参考解在两个 held-out 场景超时后，以未修改的旧 fixed-contact 策略运行完全相同物理配置，分别在 31.94 s、34.40 s 完整成功。此两项单列，不混入原 42 项的预注册统计。它们说明当前策略有局限，不支持“分区摩擦必然要求换点”。

控制器失败不构成全策略不可行证明。DR-09 关闭一位伙伴的控制器是在同一双机器人场景中的策略消融，不能直接推出所有单机器人策略都不可能。DR-08 的参考解没有使用辅助物件，不能宣称工具必要性。当前移动模型是 Stretch 3，不是未经验证的 Stretch 4；G1 使用固定骨盆，不代表自由行走全身控制。

## 正式准入仍待完成

`infra/sandbox/records.py` 要求视频人工签署，以及由第二人复现声明的参考运行；本包不填写任何虚构签名。`review-form-0.2.json` 列出九项视频与轨迹入口，供真实审核人记录观察、判定和日期。自动图像解码和本人重放不能替代这些签署。

独立 coding agent 的传感器闭环评测与工具／协作收益研究尚无完整成绩。当前仓库的主 benchmark R9 范围也不能由本候选包自行豁免；共有发布检查器保持原样。DR-I01 仍是 unknown，不计作不可行任务。

正式签署前可以分享研究候选源码与证据，但不能把本页表述为主 benchmark 已准入。已验证的内容和未完成的研究问题均保留在任务页。
