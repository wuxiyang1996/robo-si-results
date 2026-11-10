# 14 项沙盒交付

参考解与参考设计、沙盒接口、正式任务验收分别记录。参考执行与设计材料覆盖 14 项；本目录提供 14 项运行入口。实际单元测试、容器运行、RGB 与越权探针的结果以配套验证清单为准，存在文件不计作运行通过。

## 启动

完整沙盒工作区包包含源码、机器人模型、控制器权重及许可证；HF 上各任务的历史参考包继续单独保留。先按 `infra/deployment/README-zh.md` 安装对应 Windows / Linux Python 3.12 环境及 Docker，只使用其中的 `install` 创建环境，再在本工作区根目录执行下列命令。该部署工具的旧 `prepare/run` 仍针对原 11 项历史参考包；当前 14 项沙盒使用本页统一入口。完整包地址与 SHA-256 见包根的 `REFERENCE-PACKAGES.json`。工作区、冻结参考包和依赖锁不要跨版本混用。

```sh
python -m infra.sandbox.verify_workspace
python -m infra.sandbox.inventory list
python -m infra.sandbox.inventory check --task all
python -m infra.sandbox.inventory launch --task DiskFlip --mode eval --sim-time 1 --no-video --name disk-smoke --agent-dir humanoid/g1_tabletop_disk_flip/sandbox/agent_sdk/examples -- python hello_sensors.py
python -m infra.sandbox.inventory launch --task Sokoban --name paired-smoke --sim-time 1 --agent-a multi_robot/g1_sokoban/sandbox/agent_sdk/examples --agent-b multi_robot/g1_sokoban/sandbox/agent_sdk/examples -- python hello_sensors.py
```

Windows 和 Linux 使用相同入口；容器网络适配与宿主环境检查以部署脚本为准。每次使用新的运行目录名。共享机器的物理仿真须经现有资源队列，不能绕开队列或改变槽位容量。

统一入口在 Linux 为每个代理建立独立本地 socket 转发；在 WSL 中只为沙盒子进程优先选择 `/usr/lib/wsl/lib` 的宿主 CUDA 驱动，不修改系统驱动。宿主依赖仍需安装，GPU 驱动不包含在 Python 锁或工作区包内。当前实测为同一物理机上的 Windows 与 WSL2 Ubuntu 22.04，不等同于第二台机器复现。H3、DiskFlip 的短运行使用原生 CPU 后端；Sokoban 使用 GPU。

## 三项新增适配

- H3 接入当前双 G1 场景；历史单 G1 沙盒不计作当前任务验证。每个 200 Hz 原始评分样本写到可信日志，再由独立评分器重放。
- DiskFlip 使用发布包中的原始 64 位、400 Hz 后端，另存为 `humanoid/g1_tabletop/disk_release_backend.py`，不替换 Hanoi／Assembly 的现有后端。配置、摩擦、积分步长和评分器保持原定义。
- Sokoban 为每台机器人分配独立令牌、容器、网络和工作目录；只提供自己的 RGB、本体状态及显式消息。两条关节指令到齐后才推进共同世界，不自动共享地图或对方状态。

## 评分与范围

沙盒冒烟测试预期得 0 分：它验证读传感器、发送动作、隔离和可信记录，并不执行完整任务。越权探针预期 VOID，必须同时核对探针进程的退出结果，不能把任意错误造成的 VOID 算作安全测试成功。

Sokoban 的到达诊断和完整“仅推不抓”物理有效性仍分开：`task_success=null`，未完成有效性认证时不给成功分。此限制不因补上隔离接口而消失。其他任务原评分和声明范围不变，M2 的 9 kg、自主对接版 M4、独立机器复现及人工签审均不从短运行推断通过。
