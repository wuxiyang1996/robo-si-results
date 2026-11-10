# M4 family 0.1.0-rc1

发布范围：六种 embodiment 的预装载、预连接专家参考。货物由地面／平台支撑；M2 的手部承重抬运不在此范围。正式 benchmark 准入仍为 false。

## 发布验证

最终 runtime revision 3 在冻结后用 seed 29、初始机器人 XY ±0.02 m 重跑，六项全部通过物理监测及离线复核；每项有高／低层计划、完整轨迹、阶段对应和实际仿真录像。17 项回归测试通过。独立目录复现使用相同已安装环境，不等于第二人或全新环境复现。

四 Go2 的旧控制器在 seed 17 超过 50 mm 滑移上限，失败保留。最终控制器降低平移和转弯速度，原始初态及 seed 1、2、17、29 通过；验收阈值未修改。这些有限样本不构成泛化成功率。

| Task | Embodiment | Final seed 29 | Time (s) | Peak stance slip (mm) |
|---|---|---|---:|---:|
| M4-01 | 2 Go2 | PASS | 45.41 | 44.71 |
| M4-02 | 1 G1 | PASS | 89.75 | 21.79 |
| M4-03 | 3 Go2 | PASS | 54.85 | 30.74 |
| M4-04 | 2 G1 | PASS | 42.81 | 11.49 |
| M4-05 | G1 + 2 Go2 | PASS | 73.99 | 20.36 |
| M4-06 | 4 Go2 | PASS | 82.61 | 33.35 |

匹配条件下，1、2、3 Go2 均可完成 15 kg、μ=0.3、2.6 m 通道运输。单机成功意味着该实例不能证明多机必要性；队形也随团队大小声明，不做纯数量因果归因。静止控制基线未到目标且未被误判成功。

## 下载与复现

运行包保留完整运行源码、机器人与视觉资源、策略权重、上游许可、环境版本及 SHA-256 清单。Go2 模型由 Genesis 安装提供，并逐文件校验。下载链接见发布任务页；沿用私有数据集权限。

```bash
cd m4-family-runtime
python verify_package.py
python -m unittest m4_family.test_family -v
PYOPENGL_PLATFORM=egl python -m m4_family.release_run --task M4-06 --out outputs/M4-06 --video --seed 29 --jitter .02
python -m m4_family.verify outputs/M4-06
```

过程退出正常不等于物理任务成功；检查 verification.json 中的 reference_success。CPU 仿真，已验证录像设置使用 EGL/GPU。每次使用新输出目录。

历史开发记录与本次发布尝试分别归档，含失败、初版缓存竞争故障与修复；不把挑选后的成功当成统计成功率。G1 使用骨盆固定牵引点，手抓、工具发现、自主连接、团队重配置、人工签审和正式准入不在本次发布结论内。
