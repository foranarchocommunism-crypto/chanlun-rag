# 缠论 Agent 0.2.0：交付与验收报告

日期：2026-10-23。**本机实现、完整便携目录和实际 ZIP 解压件验证已完成。独立干净 Windows 环境验收按用户“暂时没有，先完成本机与交付件验证”的决定延期，尚未宣称通过。**

追加实施状态：用户随后要求自行配置容器环境，覆盖 Windows 10/11 x64＋ARM64，并在整个项目交付后清理临时环境和无用备份。此要求取代上述延期安排。0.3.0 双架构 ZIP 已通过本机完整校验及独立 x64 Windows 的断网、普通用户、中文与空格路径验收，SHA-256 为 `1d827fbfc168b16ef8de99ac689df2f8b737f3b7e9237eed4737a7e897ece4af`。Windows 容器与 ARM64 Windows 运行验证尚在进行，整体交付尚未完成。追加证据保存于 `validation-runs/windows-compatibility-20261023`。以下保留 0.2.0 历史交付记录，待追加验收完成后更新最终入口。

## 直接使用

| 产物 | 位置 |
| --- | --- |
| 独立运行目录 | [chan-kg-agent-0.2.0-307029129712](deliveries/chan-kg-agent-0.2.0-307029129712/) |
| 最终 ZIP，约498.4 MiB | [下载／打开 ZIP](deliveries/chan-kg-agent-0.2.0-307029129712.zip) |
| 上手及 MCP 配置模板 | [运行包 README](deliveries/chan-kg-agent-0.2.0-307029129712/README.md) |
| ZIP 校验文件 | [SHA-256](deliveries/chan-kg-agent-0.2.0-307029129712.zip.sha256) |
| 最终交付回执 | [delivery receipt](deliveries/chan-kg-agent-0.2.0-307029129712.zip.delivery-receipt.json) |
| 完整执行计划 | [完整实施计划](完整实施计划.md) |

可直接在 PowerShell 执行，无需从源码构建或另外安装 Node/Python：

```powershell
& "C:\Users\13240\Desktop\RAG\deliveries\chan-kg-agent-0.2.0-307029129712\chan-kg.cmd" retrieve "中枢是什么，最低级别的定义有什么不同？"
```

Agent 接入使用 CLI、JavaScript API 或本地 MCP stdio；MCP 配置模板在运行包 README。包内同时提供 verify.cmd，可检查当前解压件并把报告保存到用户临时目录，不修改知识库。使用 MCP 时从 retrieve 开始，再按稳定 ID 追加 claim／issue／evidence 取证。调用方 Agent 负责最终回答。

ZIP SHA-256：

```text
39e0fc6038f88fd6ebeb4145f80465ef0ddb394f4901c6a14ad6a62b90d9542b
```

## 已交付能力

默认链路为中文结构化词法、术语与别名＋本地向量召回 → 加权 RRF → 有证据支持的局部图扩展 → 40候选重排 → 完整证据包。默认词法／向量／图权重为1／0.5／0.1；图扩展默认一跳，节点、关系、候选与上下文均有预算。精确概念定义查询另有基于真实概念别名、主谓表述和 reviewed 结构关系的定义锚点。

知识、研究和原文三种模式共用核心。默认 reviewed 集合包含全部3369条命题及其中473条显式歧义；2611条 pending 仅在显式研究模式单列。字符覆盖分队复现2116条全文覆盖、61条部分覆盖、434条无同段reviewed引文，均不自动判定语义等价或升格。

八个有来源的研究问题组保存解释、假设、未知条件和待核项。已知分歧命中时补取相关分支；未决内容保留身份。条件、例外、否定、原歧义说明及完整引文按单元返回，预算不足则延期并提供实际可调用的续取参数。

运行包内含 Node 24.15.0、固定 revision 的中文 embedding 和重排模型、知识／原文／索引、策略、配置、许可证和校验清单。原生依赖另外核查并随包放置：实测 MSVC DLL 从包内原生模块目录加载，没有使用本机 System32 中对应文件。包内不含桌面端、完整 curation 工程、原项目 test/build 或开发软件安装包。

## 质量与资源证据

| 集合与口径 | 强词法 | 默认方案 |
| --- | ---: | ---: |
| 240题开发集，证据 Recall@10 | 72.00% | 87.11% |
| 240题开发集，证据 Recall@20 | 81.89% | 92.15% |
| 240题开发集，完整标注证据组@20 | 72.08% | 86.25% |
| 24题冻结前瞻集，证据 Recall@20 | 95.83% | 100% |

开发集逐题比较为39题提高、1题下降。下降项为 g-b16-red-not-confirmed：“2/18有MACD红柱就无忧且结构上涨已成吗？”，Recall@20从1降到2/3。该项保留在逐题结果中，不以平均分掩盖。

前瞻集在调参前冻结，与开发题的标注来源段落无重叠，标注者仍为实施 Agent，尚无人类或独立语义复核。24题较小；配对Recall@20差值的bootstrap 95%区间为[0, 0.125]，不足以作广泛效果保证。上述是标注证据召回，生成答案另有四个来源可核查的端到端示例，未提供独立答案正确率基准。

冻结前瞻集实测：单服务查询p50约1.63秒、p95约2.28秒，独立CLI冷启动约7.06秒，进程峰值约0.93 GiB，均在事先冻结的本机资源限额内。完整开发API运行峰值约1.22 GiB。具体环境为i5-1038NG7、Windows10 x64、约16 GiB内存。

47项发布前测试通过；默认知识校验通过；前瞻返回中的来源、状态、条件、引文和支持路径检查错误数为0。数据、模型、索引、policy、profile及核心代码均绑定版本或哈希。

## 实际交付件验收

完整目录和从最终ZIP解压到“移位验收 空格路径”的副本均通过：

- 7782个文件校验项，另含校验清单本身；ZIP共7783个文件。
- 包内node.exe运行，隔离全局Node/Python相关路径，从另一工作目录查询成功。
- 禁用Node fetch/http/https/net/tls/dns接口后，本地模型及查询成功；系统网络状态未更改，也未伪称已物理断网。
- 默认混合／图／重排通道实际运行；knowledge、research、source身份分区正确。
- CLI、JS与实际MCP SDK stdio客户端对同一请求返回相同证据内容，能够继续读取原文证据。
- 已加载原生运行库路径和哈希均指向包内文件。
- 运行前后canonical SQLite、manifest和两册PDF哈希一致。

已验证实际stdio协议客户端；未修改或声称验证了某个GUI客户端的全局MCP注册状态。

## 目录整理、维护与剩余边界

旧桌面端及其归档按用户决定不恢复。活动共享知识目录的失败构建数据库移到验收资料中保留；本轮失败派生索引集中保留；已被最终版本替代、可重建的约1 GiB不完整产品副本已清理。原始PDF、正式知识源、实施前备份、审校研究、仍被评测引用的冻结快照和旧知识库交付继续保留。

首个增强检索版本没有更早的同产品完整ZIP；实施前的源文件／知识备份及旧知识库交付可供恢复。以后升级应保留上一整套匹配目录，按运行包维护说明回滚，不能只替换一个DB或模型文件。

独立干净Windows执行是唯一仍延期的环境验收项。全部473条歧义和2611条候选的逐条语义解决属于持续研究；首版保留、检索和明确标注这些信息，没有批量改review状态，也不声称全部解释已经统一。

## 审计入口

- [逐阶段实施状态](chan-kg-agent/docs/implementation-status.json)
- [逐要求完成审计](validation-runs/agent-implementation-20261022/completion-audit.json)
- [冻结前瞻质量与资源结果](validation-runs/agent-implementation-20261022/m6-prospective-acceptance.json)
- [真实生产API开发结果](validation-runs/agent-implementation-20261022/m4-production-development.json)
- [运行目录验收](validation-runs/agent-implementation-20261022/m7-directory-verification.json)
- [实际ZIP解压件验收](validation-runs/agent-implementation-20261022/m7-extracted-verification.json)
- [目录清理回执](validation-runs/agent-implementation-20261022/m7-directory-cleanup.json)
- [调用方Agent回答示例与出处](chan-kg-agent/docs/agent-answer-examples.md)
