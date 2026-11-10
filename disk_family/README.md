# DR · Material-Aware Cooperative Disc Manipulation

任务族设计：[`infra/planning/disk-rotation-family/README.md`](../infra/planning/disk-rotation-family/README.md)。逐项实测结果：[`EXECUTION.md`](../infra/planning/disk-rotation-family/EXECUTION.md)。所有提交与失败保存在 `runs/<case>/<attempt>/`；以独立审核为准，不把运行结束、角度进展或生成视频计为完整成功。

每次执行包含：

- `plan.json`：构建场景之前冻结的 high-level / low-level 目标、父子关系和进入／退出条件。
- `source-code.zip`（网站）与 `workspace/`（本地）：专家、物理环境和审核代码的对应快照。各次尝试的 ZIP 不含大网格；正式参考解另提供包含机器人网格的完整归档，SHA-256 见 manifest。
- `trajectory.npz`：400 Hz 连续物理状态、50 Hz 控制目标；移动身体额外记录底盘状态、真实轮速命令和 mimic 从动关节。
- `segments.json`：每段计划对应的命令、物理采样与时间区间，以及真实进入／退出状态。`verification.json` 分别检查 HL↔LL、LL↔trajectory、HL 目标实现。
- `contacts.jsonl.gz`、`material_readback.json`：真实接触对、力、非预期接触以及实际摩擦读回。
- `video.mp4`、`overhead.mp4`：同次物理运行的视角；短失败保留真实首末帧。新录制提供 `video_frame_times.json`，不能把显示时长误认为仿真时长。
- `summary.json`：物理目标、约束峰值与诊断；`job.log` 保留启动错误。源码和配置在提交前复制，不从变化中的共享目录运行。

## 执行与监控

冻结环境为 Genesis 1.4.3。集群 Python：`/fs/gamma-projects/vlm-robot/conda/envs/genesis/bin/python`。

```bash
python -m disk_family.submit DR-02 new-attempt
python -m disk_family.submit DR-04 fixed-new --override disk_family/configs/dr04-fixed.json
python -m disk_family.monitor
python -m disk_family.monitor --output /tmp/dr-monitor.json
```

`submit` 为每次执行创建冻结工作区并提交 Slurm GPU 作业。`monitor` 只读现有结果，区分完整审核通过、物理成功但计划对应未通过、物理／策略失败、启动错误和运行中。它不是未来定时服务。

重新审核某个已完成记录：

```python
from disk_family.verify import verify
report = verify('disk_family/runs/DR-02/a01/evidence')
```

正式原始审核与 manifest 留在对应快照中。改过审核器后的重新审核不能覆盖原记录或冒充原版本结果。

## 正式验收与复现

验收范围为 DR-01–09 各一个确定配置的模拟参考解。每项必须由同一冻结源码完成两次正常初态运行，再从正常初态独立回放一次完整执行器输入；回放状态最大绝对差异不得超过 1e-5。三次运行均须通过原有物理阈值、400 Hz 连续轨迹和计划对应审核。视频实际解码帧数须匹配逐帧仿真时间。验收标准见 [acceptance-contract.json](acceptance-contract.json)，结果见 [acceptance-progress.json](acceptance-progress.json)。

网站的 `dr-simulation-reference-1.0.tar.gz` 按内容哈希去重打包九项冻结源码与机器人网格。解压后选择任务恢复到新目录：

```bash
tar -xzf dr-simulation-reference-1.0.tar.gz
python restore.py DR-06 restored-DR-06
cd restored-DR-06
export OMP_NUM_THREADS=4 PYOPENGL_PLATFORM=egl
python -m disk_family.run --case DR-06 --override reference-case.json --output evidence
```

冻结运行环境：Linux、Python 3.12.14、Genesis 1.4.3、PyTorch 2.11.0+cu128、NumPy 2.5.3、MuJoCo 3.14.0；需要 CUDA GPU 与 EGL 渲染支持。完整运行包的 `sources.json` 同时记录每项环境版本和文件哈希。恢复程序逐文件校验哈希，不依赖本项目原始绝对目录。开发期资产转换脚本中的原始缓存路径只用于重新制作模型，运行时使用归档中已冻结的派生模型。

独立重复与回放：

```bash
python -m disk_family.submit DR-06 repeat --repeat-of disk_family/runs/DR-06/reference
python -m disk_family.submit DR-06 replay --replay disk_family/runs/DR-06/reference
python -m disk_family.acceptance --output acceptance.json
```

`submit` 使用本集群 Slurm 配置；离线恢复后直接调用 `disk_family.run`。命令回放可用 `python -m disk_family.run --case DR-06 --replay /path/to/reference-evidence --output replay-evidence`。验收审计重新计算结果，不改写历史原始审核。研究假设（换点必要性、附件使用、异构协作收益）与这套参考解交付验收分开记录。

## 物理与证据范围

只对真实执行器发送限幅力矩／力。圆盘、附件、自由底盘与 mimic 从动关节没有运行时位姿、速度或外力写入。分区圆盘用单自由刚体的多个碰撞网格，底部与侧面摩擦独立，固定质量与惯量；Genesis 接触系数取双方较大值，因此推头设为 0.01，避免掩盖侧面材质。

Panda 使用原参考的球形推头。G1 使用固定骨盆与真实 Dex3 手模型，不声明步行能力；五指手对照尚未运行。Stretch 使用 SE3 / DW3 / SG3 的 Stretch 3 资产，不能称为 Stretch 4。伸缩臂内部嵌套网格与腕部的指定自碰撞排除在构建前声明，保持机器人与环境的碰撞；具体配对和资产来源写入代码及 material_readback。固定 Panda 配对比较与附件获取／持用路线尚未完整验证。

当前专家读取特权状态；这些执行不是视觉 agent 的评测成绩。失败不构成全路线不可解证书。DR-I01 仍为 unknown，没有全路线排除和可解孪生，不作为成功退出案例。

## 文档与网站构建

```bash
python -m disk_family.publish_evidence --root /path/to/robo-si
python -m disk_family.plot --root /path/to/robo-si
python infra/planning/render_disk_rotation_family.py --root /path/to/robo-si
```

按实际运行生成双语独立任务页、轨迹下载、计划对应表、消融与失败记录；原始 0.1.0 历史证据保持独立。部署通过 Sites 源码同步及发布流程进行。
