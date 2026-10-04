# 独立准备

从当前分支下载 save-my-astra-deployment 目录。在该目录运行 `python bootstrap.py`，它从上游 main 下载源码；然后按照 README 执行 test、install 和 rollback。需要 Python 3.11+；bootstrap 对 CPython 3.12 Windows x64 下载并校验 PyYAML 6.0.3 wheel，其他平台请自行安装兼容 PyYAML。

注意上游 main 可变化；bootstrap 会输出下载包 SHA-256。此仓库记录的是 2026-10-04 安装尝试，并不表示未来上游版本已验证。

补充验证：已在带原有 model 设置及中文 AGENTS.md 的临时目录中成功安装、回滚；原文件 SHA-256 相同。实际用户目录因拒绝访问未修改，真实 Luna spawn 尚未执行。

目录独立存放，后续迁移只需复制此目录；无需合并到 MCU 项目主分支。