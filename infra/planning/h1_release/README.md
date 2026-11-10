# H1 限定范围参考发布包

完整参考包已上传 Hugging Face，大小 **5,256,221,453 字节**，包含 **7257 个文件**。源码、资产、原始录像/日志、审计、分层设计材料和运行入口齐全。项目完成指声明范围的参考执行与设计交付；正式准入仍单独待验收。

- [固定版本下载](https://huggingface.co/datasets/IntelligenceLab/robo-si/resolve/71ea702d485b28be849a28c894750b9538a40fe0/releases/h1-layered-reference-20261026/h1_layered_reference_20261026.zip)
- [上传与远端校验回执](publication.json)。原封存包及 DELIVERY.json 中“尚未上传”等文字是封存时的历史状态，以此回执为准。

- 发布包：`C:\Users\wuxiy\rsi_releases\h1_layer1_20261024\h1_layered_reference_20261026.zip`
- SHA-256：`300630ebf965ef40e6b8c16c231dfe7671fd84dabd70684b842b4138f6d03e03`
- [交付清单](DELIVERY.json) · [封存校验](seal.json) · [换目录验证报告](relocation-verification.json)
- 解压后的操作说明：`C:\Users\wuxiy\rsi_releases\h1_layer1_20261024\h1_layered_reference_20261026\README.md`

固定 C371/C373 保留 3 次原生成功和 1 次实际容器成功。随机 C026 保留 seed 63、963 完整成功及 985 原始失败；三组账本为 **2 个 witnessed_full、1 个 unknown**。不宣称三组全部成功或整个随机范围已充分验证。

已从最终 ZIP 解压到另一个含空格的目录，通过完整文件哈希、原证据链、14 个数值关键状态、两套源码隔离导入、5 个只打印复现命令及预算筛查检查。全部证据访问使用包内映射，未回退到原归档路径。13 项打包/筛查回归测试通过。

本次未执行物理仿真，未新增成功案例。换目录验证仍使用同一机器现有 Python 环境，不冒充全新机器安装或第二人独立物理复现。人工签审、第二人复现继续暂缓；未验证的技能范围与动力学检查保留 unknown。

封装入口：`../build_h1_reference_package.py`；换目录核验入口：`../audit_h1_reference_package.py`。本目录的 Python 文件是包根目录入口模板，应使用发布包内副本运行。

历史分卷清单保留于 [upload-parts.json](upload-parts.json)，当前远端下载使用上面的完整 ZIP。
