# 缠论 Agent 检索包

此包为 **0.4.0 固定知识库正式版**。知识库不再新增内容，程序、模型和索引成套提供。已修复快照一致性、构建中断恢复、Graph 受控降级和运行追踪。请阅读 [本版使用边界](docs/fixed-release.md) 与发布仓库中的验收记录；正式软件发布不表示所有待核知识已经完成语义复核。

本目录提供本地知识图谱增强检索，回答由调用它的 Agent 生成。运行时、中文向量模型、可选重排模型、知识库和索引随包提供，日常查询无需安装 Node、Python 或开发工具。

## 开始使用

在 PowerShell 中进入解压目录，执行：

```powershell
.\doctor.cmd -Full
.\chan-kg.cmd status
.\chan-kg.cmd retrieve "中枢成立需要哪些条件，最低不可分解级别又有什么不同？"
.\chan-kg.cmd retrieve "第54课与第18课关于中枢连接级别为何不同？" --limit 10
.\chan-kg.cmd issue issue-connection-level-scope
.\chan-kg.cmd claim upper-l017-center-definition
.\chan-kg.cmd evidence evidence-6ac9c06be7bdc831
```

任意工作目录也可使用启动器的绝对路径。目录可以移动，支持中文与空格。先用少量结果定位，再按稳定 ID 读取 claim、issue、evidence 或 page。文件名和页码以实际 PDF 页为准。

本原生包面向 Windows 10 1809 及以后版本、Windows 11 的 x64 设备，使用包内 `runtime/x64`。日常运行不需要 Docker 或管理员权限。兼容目标和实际测试环境见 [Windows 兼容说明](docs/COMPATIBILITY.md) 及 ZIP 旁的交付回执。Windows 7/8、32 位及 ARM64 系统不在本次交付范围内。

## 三种用途

默认 knowledge 只使用 reviewed 命题，包括已有显式歧义。结果保留条件、例外、kind、review_status、ambiguity_status、review_note、精确引文、角色、页码及图路径。

```powershell
.\chan-kg.cmd retrieve "走势完成的定义与形成过程有什么区别？" --mode knowledge
.\chan-kg.cmd retrieve "第77课跨页的线段A是假设称呼还是已确认？" --mode research
.\chan-kg.cmd claim candidate-06fee67b46cd9475 --mode research
.\chan-kg.cmd retrieve "基本上可以这样理解" --mode source
```

research 的 pending 单列为 research_leads，不能当作已复核知识。source 包含读者、作者、附录等真实角色，原文语境不会因命中自动获得复核身份。歧义解释列出提出者、来源、假设和未知条件；没有数值阈值的定性信息仍可利用，但不能把工程选择改称作者明说。

## MCP stdio

把下面模板中的绝对路径替换为本解压目录，加入目标 Agent 的 MCP 配置。不同客户端的外层配置位置可能不同；启动器支持中文和空格路径。

```json
{
  "mcpServers": {
    "chan-kg": {
      "command": "C:\\Windows\\System32\\cmd.exe",
      "args": ["/d", "/s", "/c", "call", "C:\\你的解压目录\\chan-kg-mcp.cmd"]
    }
  }
}
```

工具包括 retrieve、status、claim、issue、relation、concept、neighbors、evidence、coverage、sources、page。先 retrieve，再按 ID 追加取证；同一核心也可由 JavaScript API `RetrievalService` 调用。MCP stdout 仅输出协议，诊断日志走 stderr。

客户端也可直接运行 `runtime/x64/node.exe`，参数为 `app/bin/chan-kg-mcp.mjs` 的绝对路径。

## 预算、模式与故障

```powershell
.\chan-kg.cmd retrieve "什么是背驰？" --limit 10 --context-budget 60000
.\chan-kg.cmd retrieve "第三类买点如何确认？" --profile lexical
.\chan-kg.cmd retrieve "第三类买点如何确认？" --profile hybrid-graph-rerank --rerank-budget 20
```

字符预算统计证据数据对象 JSON 的 Unicode 码点，运行元数据另列。放不下的完整命题或解释组放入 deferred，按给出的命令续取。相关性分数不是正确性概率，`answer_support` 表示检索尚未判断最终答案是否充分。

索引、模型和知识版本不符时明确报错，不能拼用不同版本的文件。仅在明确接受降级时加 `--allow-degraded`，并查看 runtime 中的实际通道和原因。模型全部从本地加载，运行时关闭远程模型下载。

## 知识与验证边界

两册 PDF 是固定汇编底本，没有声明与原博客逐字一致。reviewed 表示本工程的来源、转述及条件复核，不证明收益、数学定理或全部解释已经统一。候选计数不等于独立知识缺口，来源重复不构成独立确认。

`release-manifest.json` 记录产品、数据、模型、策略、配置及 x64 运行时。ZIP 旁的交付回执记录实际完成的环境验证，构建清单本身不代表验收通过。

运行 `verify.cmd` 可生成当前解压件的校验与调用报告；不修改知识库。首次运行可能需要等待本地模型加载。维护重建步骤和版本回滚方法见 docs；更新应更换一整套匹配的知识、索引、模型和策略，并保留上一可用目录。
