# Windows / Linux 部署工具包

[English guide](README.md)

本工具包为已发布的 10 个完整包、11 项任务提供统一下载、SHA-256 校验、依赖安装与独立运行入口。支持 x86-64 Windows 和 Linux + NVIDIA GPU；Python 固定为 3.12.7，分别提供带哈希的依赖锁。任务的完成范围不因此扩大，H1 不在这 11 项内。

`check` 是源码、资产和导入检查；`run` 启动物理参考程序。进程正常退出不等于任务得分通过，必须继续检查输出的 verdict / record、告警及视频。当前机器上的新环境验证也不等于另一台物理机器的独立复现。最新实测结果见 `validation.json`。

## 下载与权限

GitHub 仓库与 Hugging Face 数据集都是私有的，部署账号需同时有权限。安装 GitHub CLI 后执行 `gh auth login`；设置 `HF_TOKEN` 或使用 Hugging Face 已保存的登录令牌。工具不会把令牌写入日志，也不会把 HF Authorization 转发到其他域名。

Windows 还需安装 x64 [Microsoft Visual C++ v14 运行库](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)，[PyTorch 官方 Windows 说明](https://docs.pytorch.org/docs/main/notes/windows.html)列出了此系统依赖；本次主机版本为 v14.51.36247.00。Windows 的 GPU 容器使用 [Docker Desktop 的 WSL2 后端](https://docs.docker.com/desktop/features/gpu/)，原生 Linux 的 GPU 容器需配置 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。请先完成这些主机依赖，再运行 Python 安装入口；驱动、Docker 和系统运行库不包含在 Python 依赖锁中。

完整包约 6.25 GB，解压、依赖、容器镜像及录像另占空间。建议为整个工作目录预留至少 60 GB，并为 Docker 的存储卷另留空间。`catalog.json` 固定了每个包的版本、下载地址、大小和 SHA-256。不要用 review 包替代完整包。

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.5，然后在本目录执行。`--root` 可换成自己的路径，Windows 建议使用较短路径，例如 `C:/rs`。以下 `python` 指启动工具的 Python 3.12+：

如果机器尚未安装 Python 3.12，可用 `./bootstrap.ps1 -Action install -RootPath C:/rs`（Windows）或 `bash bootstrap.sh install --root /data/rs`（Linux）；uv 会下载指定的 Python。其余操作可将 `-Action` / 第一个参数换成 `prepare`、`check`、`run`。Windows 通过 `-Task M2` 选择任务，Linux 使用 `--task M2`。

```powershell
python deploy.py list
python deploy.py install --root C:/rs
python deploy.py prepare --root C:/rs --task all
python deploy.py check --root C:/rs --task all
python deploy.py plan --root C:/rs --task M2
python deploy.py run --root C:/rs --task M2 --run-name test-01
```

Linux 原生环境使用相同命令，将根目录换成 `/data/rs`。系统要求 glibc ≥ 2.35（例如 Ubuntu 22.04/24.04 或 Debian 12）、可用的 NVIDIA 驱动，以及 EGL/OpenGL 运行库。系统库安装示例参见本目录 Dockerfile；不要在已有工作机上替换显卡驱动。

已有完整 ZIP 可以离线准备，仍会检查大小与哈希：

```powershell
python deploy.py prepare --root C:/rs --task M3 --archive C:/downloads/m3-functional-reference-20261025.zip
```

如果解压目标已存在，工具拒绝覆盖。保留已有输出，改用新根目录或新运行名称。下载缓存校验不通过时也会停止，不静默覆盖原文件。源代码归档保持原样；桌面任务的补充元数据另见下节。

共享计算机必须在 `run` 时传入现有队列适配器 `--queue PATH`，该适配器接收 `--` 后的实际命令。本机现有队列容量不应改变。单人独占的新机器可以省略队列。`check` 不执行物理仿真。

## Linux 容器

Dockerfile 使用固定摘要的官方 Python 3.12.7 / Debian 12 镜像、Linux 依赖锁、EGL/OpenGL 库。主机需安装支持 GPU 的 Docker / NVIDIA Container Toolkit；Windows Docker Desktop 需使用 WSL2 Linux 引擎。容器不包含账号令牌、完整任务包或历史成功缓存。

```sh
docker build -t robo-si-deployment:portable-20261025 .
# 假设 /data/rs 已通过 prepare 下载、解压，/path/to/deployment 是此目录。
docker run --rm --gpus all --shm-size 2g \
  -v /path/to/deployment:/kit:ro -v /data/rs:/work \
  robo-si-deployment:portable-20261025 \
  python /kit/deploy.py check --root /work --python /opt/venv/bin/python --task all
docker run --rm --gpus all --shm-size 2g \
  -v /path/to/deployment:/kit:ro -v /data/rs:/work \
  robo-si-deployment:portable-20261025 \
  python /kit/runtime_probe.py --physics --out /work/linux-physics.json
```

Windows 的 `-v` 左侧改用绝对 Windows 路径。`runtime_probe.py` 验证 CUDA、100 个物理步和一帧实际渲染；它不代替任务验收。容器内运行任务时，将第一条命令的 `check` 改成 `run --run-name test-01`。**M1 的 sandbox 以及 M2 的 RPC 回放需要宿主机 Docker 服务；不要给参考运行容器挂 Docker socket。** 这两种隔离流程应在 Windows/Linux 宿主机的锁定虚拟环境运行。M2 的特权参考 capture 可直接在运行容器执行。

## 修复及各任务边界

| 项目 | 本工具包处理 | 保留的边界 |
| --- | --- | --- |
| M1 | Windows/Linux 完整 Python 依赖锁；冻结源码及可移植路径；agent 镜像也锁定完整依赖 | CPU、特权参考、第一层；仅通过明确的 Dockerfile 覆盖生成新内容摘要镜像；人工签审和第二人复现不自动代签 |
| M2 | `prepare_m2.py` 去除原 C/D 盘默认路径；通过所选 Python 的 sysconfig 查询依赖位置；校验 211 个源码及 2 个交付文件、3 个求解器源码哈希；补齐原网格引用的材质、贴图 | 固定 0.25 kg、1.8 m；capture 使用特权反馈。9 kg 未完成。RPC 命令及挂载探针保存在准备计划中，单独执行、单独评判 |
| Hanoi / Assembly | 补齐共享模块导入需要的 7 个柜体元数据文件；Assembly 使用已发布流水线的第一层场景与 `closed_loop:run` 资格入口 | 两套冻结运行时保持独立；旧版名义场景的轨迹回放不作为第一层部署入口 |
| H4 | 记录当前发布源码的哈希，补齐缺失的录像模块、资产生成模块和原版场景资产，另行生成新运行证据；附历史源码恢复审计 | 12 个历史源码差异版本已找回 7 个，仍缺 5 个，不能精确重建全部历史成功运行；不得以当前源码重写旧记录 |
| H2 / H5 / H6 | 按完整包准备运行目录；H2 自动展开嵌套完整包；H5/H6 保留源码哈希校验 | 各自声明的第一层、开发机构或固定参数范围不变；本工具默认仅选择一个代表性案例，非完整覆盖重跑 |
| H3 | 独立冻结 runtime、no_prop / heavy_prop 两条入口；Linux heavy_prop 开启确定性严格数学模式并独立重评 | 原生特权参考，尚无隔离的双机器人 agent 接口；原 Linux 推箱偏移失败保留，控制器、积分步长和限值未改 |
| M3 | Windows 保留发布入口；Linux 使用已验证的反馈与返回适配器，补齐 4 个含许可证的 WBC 文件并绑定源码哈希 | hooks-v0.1、柜架支撑取物、特权参考；不外推到全程悬空取物或普通 RPC |
| M4 | Linux base 通过已有公开参数 `--ctl '{"v_arc": 0.10}'` 将转弯速度从 0.15 降至 0.10；Windows base 和两边的 hard 保留原控制参数 | 原 Linux base 触发 50 mm 打滑上限，较慢转弯作为新的部署配置单独留证；未改限值或评分。自主对接完整链仍未完成 |

Linux M3 采用反馈行走、基于实测躯干与小机器人位置的手臂目标，以及避开自身碰撞的整身返回路径。摆运用时 8 秒，在原 420 秒总时限内保留落地、脱手和目标稳定确认。完整运行从初始场景开始，无状态恢复，得分 1.0、执行完成且无告警。这是无录像的完整物理验证；原 Windows 录像保留，不宣称新的 Linux 完整成功录像验收。`m3-runtime-provenance.json` 将部署入口和辅助模块逐字节绑定到通过记录；`supplements/m3-wbc/manifest.json` 保留模型文件与许可证来源。中间快照实验不计为完整成功，包括曾得 1.0 但控制器收尾超时的记录。

补丁来源与哈希分别见 `m2-adapter-provenance.json` 与 `supplements/` 中各项 manifest，包括 `h4-code-manifest.json`。原完整 ZIP 和历史判决没有替换。

Linux 汉诺塔采用已发布的 3、4、5 盘资格验收场景与控制器，开启 Genesis 确定性算法及 debug 严格数学模式。验收程序检查新运行及其本地动作回放；该数值运行配置没有改变积分步长或任务限值，也不宣称与 Windows 历史轨迹逐位一致。原 Linux 严格轨迹对比失败及 NaN 记录均保留。Windows 继续使用已通过的严格参考入口。各盘数实际完成的验收结果见 `validation.json`。

Linux H3 重支撑物配置在 169.66 秒完成，并通过独立交付及支门路线重评。`h3-runtime-provenance.json` 将部署适配器绑定到该运行；与已验证脚本仅模块说明文字不同，可执行 AST 一致。Windows H3 及 Linux 无支撑物案例继续使用原运行配置。

H5 的录像适配器持续读取 FFmpeg stderr，避免原写入器仅在结束时读取造成管道堵塞。WSL2 容器即使可用 CUDA，也可能使用软件 EGL。原配置、单线程及关闭阴影的录像均出现停滞，失败记录保留。单独的无录像诊断完成五个评分阶段，得分 1.0、150.92 秒、非 VOID；该诊断不计入完整录像参考的通过数。使用 Debian 官方 Bookworm 回移版 Mesa 25.0.7 后，完整纹理录像运行已通过：1.0、150.94 秒、五阶段全部完成、非 VOID、无告警。Dockerfile 已固定该版本。原生 Linux 如使用软件 EGL，应采用 Mesa 25.0.7 或更新版本；固定版本容器是本轮已验证的方式，无需改动主机 GPU 驱动。冻结任务源码、控制和评分保持不变。

M1 的 `run` 自动选用锁定 agent 镜像。M2 的 `run` 默认执行特权 capture；必须先在**目标环境本地**生成成功动作，再通过普通 SDK 回放。实测将 Windows 的旧动作直接带到 Linux，接口虽完成执行，任务仅得 0.3。原动作包保留作历史对照。新 Dockerfile 生成新的内容摘要镜像标签；依赖根版本与历史一致，新增完整传递依赖锁，不包含可选 LLM CLI。

```powershell
# 先在本环境完成 deploy.py run --task M2 --run-name test-01。
# 共享机器的两条命令均须添加 --queue PATH。
C:/rs/venv/Scripts/python.exe replay_capture.py --runtime C:/rs/runtimes/m2 --capture C:/rs/runs/m2-test-01 --name rpc-local-01
```

Linux 将解释器换成 `/data/rs/venv/bin/python`，其他路径对应替换。第一次 agent 镜像构建需要联网；其运行阶段沿用原 launcher 的网络、权限、资源和动作约束。

回放助手要求 capture 成功且采用 RPC 初始化，核对命令与客户端哈希，只向 agent 提供这两个文件，并单独检查新 RPC 判决。这仍是开环命令接口验证，不是纯传感器闭环解。

Linux 的转发层通过本地 Unix socket 连接仍只监听回环地址的 worker；只有原 socat 转发容器挂载该 socket，agent 的内部私有网络、令牌校验和资源限制保持原样。两套系统的转发镜像均固定摘要。内核缓存保存在所选部署根目录下。

原生 Ubuntu 22.04 / Debian 12 在 `check` 前需安装系统库：

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates libegl1 libgl1 libglib2.0-0 libgomp1 libxrender1 libxext6 libsm6 libopengl0 libglx0 fonts-dejavu-core ffmpeg
```

M1 和 M2 RPC 要求 `docker info --format '{{.OSType}}'` 返回 `linux`。Windows 使用 Docker Desktop 的 WSL2 Linux 引擎，原生 Linux 使用宿主 Docker 服务；启动器会在物理运行前检查。

## 新机器验收

Linux H6 已采用严格数值计算配置，原控制器完整物理运行通过：**585.87 秒、1.0、非 VOID、无告警、无特权状态写入**，20 个路线检查点、放置、释放和站立保持均完成。Linux 默认使用原程序已有的 `--no-video` 选项，**不把本次结果表述为 Linux 新完整录像验收通过**；Windows 保留已验证的录像入口。`h6-runtime-provenance.json` 记录便携入口与实测初始化、校验函数的一致性。如需新录制 Linux 视频，可在 `plan` 输出的命令中去掉 `--no-video`，该可选录像仍须单独验证。原开发挂架范围和 600 秒时限保持不变。

先运行 `check --task all`，再通过现有资源队列运行 `runtime_probe.py --physics`，最后逐项执行参考程序。每次测试保留 `checks/`、`logs/`、`runs/` 和安装回执；记录 OS、GPU、驱动、Docker 版本和依赖锁哈希。确认任务 verdict 成功、无非法告警、阶段完成、录像正确；有扰动或重复要求的任务应完成原验收清单，而非只跑本工具的代表案例。

任何失败都保留日志和原输出，再用新名称重试。本工具不会把成功退出自动写成正式准入，也不会把当前机器的新环境测试算作第二人复现。
