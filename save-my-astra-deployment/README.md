# Save My Astra Windows 安装记录

日期：2026-10-04（Asia/Shanghai）。上游：https://github.com/fengxiaohu/save-my-astra

## 当前结论

尚未完成本机安装，不能宣称部署成功。临时目录安装、静态校验和回滚已通过；实际安装在创建 `C:\Users\Administrator\.codex\backups` 时被拒绝访问。用户已授权目录写入，但当前执行环境仍然拒绝。没有修改实际 Codex 配置，没有进行实际 Luna 子 agent 运行验收。

## 已执行步骤

1. 检查环境：Windows PowerShell，Codex CLI `0.159.0-alpha.12.1`，Git 可用。
2. 审查 README、安装脚本、Python 合并逻辑和 worker 模板，核对官方子 agent 配置文档。
3. Git 的 Windows TLS 下载失败；改用 Python urllib 下载 GitHub codeload ZIP 成功。
4. Python 依赖 PyYAML 6.0.3 通过下载匹配 CPython 3.12 Windows x64 wheel 并解压到工作区加载。未修改全局 Python。
5. 增加 Windows Python 安装包装：备份全部四个改动文件、记录 SHA-256、保留已有 AGENTS.md、校验无关配置；失败时恢复原文件。
6. 在临时目录安装 astra-luna，verify_install 通过。回滚后原文件内容及新增文件状态恢复。
7. 申请并获得 `.codex` 写入授权，但 Python 和 PowerShell 均无法创建实际备份目录。安装在修改配置之前终止。
8. 将文档和脚本同步到独立分支的 save-my-astra-deployment 目录；不上传用户配置、备份或认证文件。

## 本机执行方法

下载并解压提供的安装包。需要 Python 3.11+ 和 PyYAML；包内附带的 python-deps 是 CPython 3.12 Windows x64 版本，其他版本请自行安装兼容 PyYAML。

在普通本机 PowerShell、安装包目录中运行（可将 python 换成本机 Python 完整路径）：

```powershell
python manage_install.py test .\test-home
python manage_install.py install "$env:USERPROFILE\.codex"
```

记录安装输出中的 BACKUP 路径。脚本合并配置、固定 Astra low / gpt-5.6-luna max，最多四个并发 worker。安装器会拒绝损失原有无关 agents 或 features 设置的合并；这种情况下恢复原文件并报错，需要针对现有配置调整后重试。

## 真实运行验收（待完成）

重新启动 Codex 并新建聊天，请求一个只读扫描子 agent：

> 请使用 gpt-5.6-luna，reasoning_effort=max，fork_turns=none 创建一个子 agent，只读扫描仓库并总结目录。请提供实际 spawn 元数据；如模型不可用，明确报错。

成功需要实际元数据或运行记录确认 child=gpt-5.6-luna，不能仅以模型自述或静态 verify 通过作为成功证据。Luna 不可用时停止；若需改用 Terra，要记录配置与验收结果。

## 卸载 / 回滚

```powershell
python manage_install.py rollback '安装时输出的完整 BACKUP 路径'
```

恢复之前存在文件的原始字节；删除本次新建的四个安装文件。保留备份供审计。若安装后文件又被修改，脚本拒绝覆盖，需先人工保存新的修改，再按 manifest 和备份逐项恢复。重启 Codex 并新建聊天使恢复后的配置生效。

## 验证范围与限制

可回滚机制已在临时目录运行验证；实际目录因权限问题尚未安装。订阅额度节省和 API 成本不是同一指标，尚未测量节省效果。所有配置和认证文件留在本机。

官方配置说明：https://learn.chatgpt.com/docs/agent-configuration/subagents

未来迁移时复制 save-my-astra-deployment 目录到新仓库即可；无需合并当前分支到 MCU 项目主分支。

