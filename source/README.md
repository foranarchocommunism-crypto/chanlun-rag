# 缠论知识检索 0.4.0

本项目面向 Agent 提供本地词法、向量、图关系与重排检索，返回条件、例外、来源身份、精确引文及实际 PDF 页。最终回答由调用方 Agent 生成。知识库已经固定，后续不再新增。

日常使用桌面正式发布仓库中的运行包；Node、模型、知识库和索引随包提供，无需安装开发工具。具体命令见 [运行说明](docs/portable-readme.md)，数据和恢复边界见 [固定版本说明](docs/fixed-release.md)。

## 源码与验证

CLI、JavaScript 与 MCP 共用 RetrievalService。源码依赖 Node 24，安装固定依赖使用 npm ci。npm test 检查证据、检索、故障和发布恢复，npm run validate 核对知识库引用及状态。

权威 SQLite 与两册固定 PDF 位于 ../shared-knowledge/v0.1.0；当前派生索引由 indexes/active.json 指定，模型位于 models。构建脚本只生成可复现的派生文件，不接收新知识。正式仓库提供的开发环境连接脚本可使用随包数据和运行时。

默认 knowledge 只返回 reviewed；research 单列 pending；source 保留真实发言者。语义复核状态、条件和歧义不因发布软件而改变。Agent 取证步骤见 [AGENT_GUIDE](AGENT_GUIDE.md)。

## 发布依据

0.4.0 的工程验收、Graph 对照、文件哈希和全新解压执行回执保存在正式发布仓库的验收记录中。历史 0.3.0 与 rc 候选包仅供追溯，不能替代本版本证据。

Windows x64 为本次运行平台。实际验证包括本机、隔离 PATH、关闭 Node 网络调用以及全新 ZIP 解压件；不把这些结果写成独立干净机器或真实断电验收。
