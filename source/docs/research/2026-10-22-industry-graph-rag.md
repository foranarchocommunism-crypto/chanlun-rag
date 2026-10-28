# 业界官方 RAG 与知识图谱检索方案核查

核查日期：2026-10-22。范围：10 个一手文档页面，覆盖 Microsoft GraphRAG、Neo4j GraphRAG Python、Elastic、Azure AI Search。本文只研究检索方案与迁移取舍，不修改程序、图谱或索引，不把厂商文档当作独立效果评测。

## 可采用的结论

建议把本项目的主要候选方案确定为：**关键词与 dense 双路召回 → 融合 → 从命中的概念、命题沿已核关系有限扩展 → 对小候选集做语义重排 → 返回带原文证据与审校状态的结果**。这是将官方产品已经实现的检索构件组合到本项目的工程建议，尚不是在本语料上得到验证的最优配置。[Elastic 混合检索](https://www.elastic.co/docs/solutions/search/hybrid-search)、[Elastic 重排](https://www.elastic.co/docs/solutions/search/ranking/semantic-reranking)、[Neo4j 检索器](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#hybrid-cypher-retrievers)

官方证据能够证明这些构件在成熟厂商产品和维护中的 SDK 里有正式入口；不能证明市场占有率、行业统一默认值、中文缠论语料效果或“学界公认最优”。本文不承担学术效果证据综述。

GraphRAG 有两个需区分的含义：本文用“图谱增强 RAG”指利用图结构辅助检索与上下文构造的一类方法；“Microsoft GraphRAG”专指微软这个索引与查询框架。Neo4j 的混合命中后 Cypher 扩展也是图谱增强 RAG，采用该模式不要求换成微软的实体、社区与报告体系。[微软索引说明](https://microsoft.github.io/graphrag/index/overview/)、[Neo4j 检索器说明](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#retriever-configuration)

## 官方实现的实际位置

| 构件 | 官方证据 | 对本项目的解释与边界 |
| --- | --- | --- |
| 关键词 + dense/向量混合检索 | Azure 把全文与向量并行执行后 RRF 融合作为正式能力；Elastic 也提供此组合并推荐 RRF | 适合作为基线候选架构；专门术语、编号和异形词仍需要词法召回。厂商推荐不能决定本项目融合权重 |
| 语义 reranking | Elastic 明确定位为小 top-k 候选集上的后阶段；Azure 提供可选 semantic ranker | 与召回、RRF 是不同步骤。RRF 按已有名次融合，reranker 重新判断查询与候选内容的相关性；都无法召回未进入候选集的证据 |
| 图谱局部扩展 | Neo4j `VectorCypherRetriever`、`HybridCypherRetriever` 将索引命中的节点传入开发者提供的 Cypher | 适合为概念命中补充条件、例外、证据和显式关联；“多跳”只是关系路径，不自动构成逻辑蕴含 |
| query routing | Neo4j `ToolsRetriever` 用 LLM 选择一个或多个检索工具；微软提供不同查询模式 | 有正式产品入口，但不是检索质量必然提升。路由本身会错且有额外开销；本项目可先采用明确参数与简单规则 |
| 全局报告与探索 | Microsoft Global/DRIFT | 面向全书主题或宽问题，不应让所有查定义、找原文的问题都经过社区报告 |

表中事实来源：[Azure Hybrid Search，Why use / How does](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview#why-use-hybrid-search)、[Elastic Hybrid Search](https://www.elastic.co/docs/solutions/search/hybrid-search)、[Elastic Semantic Reranking，概述](https://www.elastic.co/docs/solutions/search/ranking/semantic-reranking)、[Neo4j Retriever Configuration / Tools Retriever](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#retriever-configuration)、[Microsoft Query Engine](https://microsoft.github.io/graphrag/query/overview/)。最后一列是针对本项目的推断和建议。

## Microsoft GraphRAG：三个查询模式并不互相替代

**Local** 先通过实体描述的 embedding 找到图入口，再组合相连实体、关系、社区报告与关联原文块，按上下文预算筛选。适合围绕某个明确概念查相关论述；直接采用时需把本项目的命题、来源身份和证据映射到其数据模型。[Local Search，Methodology](https://microsoft.github.io/graphrag/query/local_search/#methodology)

**Global** 以某一社区层级的报告为输入，分批生成中间回答，再筛选汇总。它适合“整套材料有哪些共同主题”这类跨数据集汇总；不是从单条原文命中自然升级而来的通用精确检索。官方说明，更细的社区层级可能提高详尽程度，同时增加时间和 LLM 资源。[Global Search，Methodology](https://microsoft.github.io/graphrag/query/global_search/#methodology)

**DRIFT** 先选择相关社区报告，产生初步回答和后续问题，再进行 Local 搜索，形成逐步细化的问答层次。适合起点宽泛、需要探索多个侧面的研究问题；本项目应把轮数、分支数和 token 设为预算参数，避免一次术语查询触发多次生成。[DRIFT Search，Methodology](https://microsoft.github.io/graphrag/query/drift_search/#methodology)

微软的标准索引流程包括实体/关系/命题提取、社区发现、分层报告生成与 embedding，默认产物是 Parquet 与配置的向量存储，因此不必附带 Neo4j 服务。该标准流程会产生一套模型提取知识，若未经映射直接重跑，不会天然继承本项目人工核定的事实身份。[Indexing Overview](https://microsoft.github.io/graphrag/index/overview/)

不过，微软并非只支持重新抽取。官方 **Bring Your Own Graph** 支持已有 `entities`、`relationships`，以及按查询模式需要的 `text_units`。可只运行社区发现和报告生成；Local/DRIFT 等模式还需原文单元与 embedding。因此保留人工图谱再做派生实验是可行方向。适配是否完整需要另行验证，特别是命题的条件、证据 ID、发言者与 `review_status`；官方列出的基础字段本身不提供这些业务语义。[Bring Your Own Graph，Tables / Workflow Configuration / Optional Additional Config](https://microsoft.github.io/graphrag/index/byog/)

## Neo4j：更直接的局部图谱检索参照

`VectorCypherRetriever` 的流程是向量命中节点后执行固定 `retrieval_query`；`HybridCypherRetriever` 把入口改成向量与全文共同命中。Cypher 能按本项目的明确边类型补充上下文，概念或命题可继续保留为稳定节点。官方接口支持结果格式化和 metadata，便于带回证据定位。实际采用 Neo4j SDK 则需 Neo4j 数据库与索引；在 SQLite 中复用同样的检索模式，属于自行实现兼容行为，不等于已经采用其 SDK。[Neo4j，Vector Cypher Retriever / Hybrid Cypher Retrievers / Format the Results](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#vector-cypher-retriever)

不要混淆固定 Cypher 扩展与 `Text2CypherRetriever`：后者会让 LLM 生成查询，多一次生成环节，官方也不保证其语法始终正确；它可以不使用 embedding。`ToolsRetriever` 则让 LLM 在提供的工具间选择，适合后续扩展。[Neo4j，Text2Cypher Retriever / Tools Retriever](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#text2cypher-retriever)

据此推断：本项目优先借鉴可审查的固定邻域扩展，比立即迁到自由生成图查询更容易保留原有取证语义；这是一项工程取舍，不能据此断言准确率一定更高。

## 运行依赖与成本结构

以下是从官方流程推导的成本模型，不是报价或实测。API 次数受 batching、缓存、重试与实现影响；最终回答生成的成本应与检索成本分开记录。

| 方案 | 建索引成本 | 一次查询的主要开销 | 数据库/服务要求 |
| --- | --- | --- | --- |
| 词法 + dense + 融合 | 文本 embedding、词法与向量索引 | 查询 embedding、双路检索与名次融合；融合无需生成式 LLM | 算法不要求图数据库；直接使用 Azure/Elastic 产品需相应服务/部署 |
| 上述方案 + cross-encoder rerank | 不必重新做 KG 抽取；需重排模型部署或服务 | 对有限数量的查询-候选文本对推理，候选数与长度影响延迟和费用 | 可用托管 inference 或本地模型；本地仍消耗计算资源 |
| 固定图谱邻域扩展 | 已有 KG 可复用；可能需邻接索引 | 图查询、去重、上下文裁剪；固定遍历本身不需 LLM | Neo4j SDK 需 Neo4j；同类模式可在现有存储上实现 |
| Microsoft Local | 实体描述等 embedding 与框架数据适配 | 查询 embedding、上下文拼装和回答 LLM | Parquet/向量存储；不必安装图数据库服务器 |
| Microsoft Global | 社区发现、报告 LLM、更新后的派生物维护 | 多批报告 map 与最终 reduce LLM；随报告量增长 | 同上；可由已有图谱构建社区 |
| Microsoft DRIFT / LLM 路由 | 依赖相应报告、向量或工具描述 | 初步生成、后续检索和生成；路由另有 LLM 决策 | 取决于所调用工具和存储 |

成本依据：[Elastic Semantic Reranking，Cross-encoder / Handling long documents](https://www.elastic.co/docs/solutions/search/ranking/semantic-reranking#cross-encoder-and-bi-encoder-models)、[Microsoft Local](https://microsoft.github.io/graphrag/query/local_search/)、[Global](https://microsoft.github.io/graphrag/query/global_search/)、[DRIFT](https://microsoft.github.io/graphrag/query/drift_search/)、[Bring Your Own Graph](https://microsoft.github.io/graphrag/index/byog/)、[Neo4j User Guide](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html)。未核查任何商业套餐、美元价格、许可条款或中文模型的实际延迟，不应据此形成预算报价。

## 与现有人工审校图谱的迁移约束

本节属于本项目设计建议。当前取证要求以 [AGENT_GUIDE.md](../../AGENT_GUIDE.md) 为准：保留条件、例外、命题种类与复核状态，沿关系阅读证据，区分作者正文、作者回复、读者上下文及来源身份。

1. **保留事实源，建立可重建索引。** embedding、BM25 文档、图邻域缓存、社区报告都应引用稳定 ID 和图谱版本；不让检索索引成为新事实源。
2. **先确定允许召回的集合。** 默认 reviewed 检索池应由已核命题及其关联证据组成；全原文检索保留独立 scope 和来源身份。向量命中或重排高分不能把未核内容变成已核事实。
3. **为中文和专门术语保留词法通道。** 分词、别名、全半角及数字规格应单独验证；不能把“加了 BM25”理解为中文召回自动合格。dense 用来补问法变化，词法用来保留精确术语证据。
4. **图扩展必须有类型和预算。** 初期只扩展明确需要的概念-命题-证据、条件和例外关系；设最大跳数、节点数与证据数。仅因两个命题共享概念而接近，不能声称互相支持或存在时间修订关系。
5. **重排时保留完整证据单元。** 候选内容应包含命题及关键条件、原文摘录与来源身份，并返回原稳定 ID。不能只对失去条件的标题打分，也不能在拼装结果时丢掉被截断的例外。
6. **按问题类型选择模式。** 原话/出处走原文词法优先；明确概念走混合召回和有限邻域；概念比较走多实体检索；全书主题才进入带覆盖说明的摘要路径。LLM 路由可作为后续可消融的层，不应成为第一期依赖。
7. **摘要应标为派生解释。** 若试验 Global/DRIFT，应只在指定已核图版本上生成，记录输入 ID、图版本和模型；结果继续回到原始证据，不能把生成报告自身当作作者原话。当前人工复核覆盖不完整时，报告也不能声称代表全书。

建议先比较相同允许语料、相同 top-k 下的词法、dense、混合、混合加重排、再加图扩展。固定候选预算，分别报告证据 Recall@K、排序质量、来源身份正确性、条件/例外完整率与延迟；使用独立人工核定问题，并把开发集与测试集分开。结果不支持时应保留词法基线，不能因为 RRF 被官方推荐就跳过本语料比较。本文没有运行上述实验，也不引用旧开发评估作为新方案验收。

## 一手来源与复核入口

以下均于 2026-10-22 联网读取。短摘录只用于定位，结论以上文边界为准；`current` 文档会变化，迁移实施时仍需固定 SDK/框架版本。

| ID | 官方页面与章节 | 定位短摘录 | 支持的事实 |
| --- | --- | --- | --- |
| S1 | [Microsoft Local Search — Methodology](https://microsoft.github.io/graphrag/query/local_search/#methodology) | “entities serve as access points” | 实体入口、图关系和原文上下文 |
| S2 | [Microsoft Global Search — Methodology](https://microsoft.github.io/graphrag/query/global_search/#methodology) | “in a map-reduce manner” | 分层社区报告汇总及资源随报告量变化 |
| S3 | [Microsoft DRIFT Search — Methodology](https://microsoft.github.io/graphrag/query/drift_search/#methodology) | “initial answer and follow-up questions” | 报告引导后续 Local 探索 |
| S4 | [Microsoft Query Engine — Overview](https://microsoft.github.io/graphrag/query/overview/) | “This is a resource-intensive method” | Local/Global/DRIFT/Basic 的不同用途 |
| S5 | [Microsoft Indexing — Overview](https://microsoft.github.io/graphrag/index/overview/) | “stored as Parquet tables by default” | 标准抽取、社区、报告和向量流程 |
| S6 | [Microsoft Bring Your Own Graph — Workflow Configuration](https://microsoft.github.io/graphrag/index/byog/#workflow-configuration) | “create_communities, create_community_reports” | 复用已有图谱与最小 Global 工作流 |
| S7 | [Neo4j GraphRAG Python — Retriever Configuration](https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#retriever-configuration) | “both a vector and a full-text index” | 混合入口、固定图扩展及可选 LLM 工具路由 |
| S8 | [Elastic Hybrid Search](https://www.elastic.co/docs/solutions/search/hybrid-search) | “full-text search and vector search” | 双路与 RRF 的正式产品能力 |
| S9 | [Elastic Semantic Reranking — Overview](https://www.elastic.co/docs/solutions/search/ranking/semantic-reranking) | “a small top-k result set” | 后阶段重排、cross-encoder 成本与长文本限制 |
| S10 | [Azure AI Search — Hybrid Search Overview](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview) | “Runs full-text search and vector search in parallel” | 并行检索、RRF、可选 semantic ranker；页面标注更新日 2026-08-31 |

检索过程中出现的二手博客、论坛、搜索摘要未作为本文证据。官方支持能力与独立学术效果、真实采用率、本项目验收结果是三个不同层次，不能互相替代。
