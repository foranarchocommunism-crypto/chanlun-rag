# 已审校知识图谱的 RAG 检索路线：原始学术证据与迁移建议

核查日期：2026-10-22。范围：只研究检索路线，不修改检索代码、正式图谱或评测集。联网依据限于论文原文、正式会议论文集及作者仓库；作者出版物页只用于核对出版状态。

任务背景为已有人工审校的 SQLite 概念—命题—证据图谱，提供的规模为 3,369 条 reviewed claims、9,650 个 paragraphs、318 个 concepts、692 条 relations；这些数值是本研究的输入背景，本篇没有重新统计数据库。交付目标是 Windows 便携的本地 Agent 检索工具，由调用方 Agent 生成答案，不依赖面向人的桌面程序。

## 研究结论

有正式学术依据的 GraphRAG 已经形成多条路线，尚不能从这些论文证明存在统一最佳方案或统一行业标准。“作者开源”“正式会议发表”“在特定基准取得优势”是三种不同证据，也不足以证明企业部署占有率。

本项目最适合首先借鉴 **KG2RAG 的种子召回 → 图扩展 → 上下文组织**，结合 **Microsoft local search 的结构化知识与原文共同返回**；从 LightRAG 借鉴概念/具体命题与关系/主题的双通道召回。保留词法、别名和段落语义召回作为种子来源，图谱负责补足关联、条件和证据，不必先让 LLM 重抽现有图。**HippoRAG 2 的 PPR 可作为后续可比较实验；Microsoft global search 的社区摘要、BYOKG-RAG 的多策略查询规划适合后续需求明确时再引入。** 这是根据本项目约束作出的工程判断，不是论文对中文缠论图谱的验证结论。

## 正式状态与路线概览

| 路线 | 已核查状态 | 检索核心 | 原方案中的模型工作 | 对当前项目的定位 |
|---|---|---|---|---|
| KG2RAG | NAACL 2025 主会长文，8912–8924 页 | 语义种子块、KG 的 m-hop 扩展、上下文组织 | 实验离线用 LLM 抽三元组；在线检索含 embedding/reranker，后接回答模型 | 首版最接近的组织方式 |
| Microsoft GraphRAG | 原论文 2024 预印本；arXiv v2 为 2025-02-19；作者出版物页仍标 Preprint | local：实体及关联原文；global：层级社区摘要与 map-reduce | 离线抽图及社区摘要；global 在线生成局部答案再归并 | 借鉴 local；global 按需延后 |
| LightRAG | EMNLP 2025 **Findings**，10746–10761 页；预印本始于 2024 | 低层实体/细节 + 高层关系/主题，向量匹配与邻域扩展 | 离线抽实体/关系和描述；在线提取关键词、最终生成 | 借鉴双层索引思路，不整套替换审校图 |
| HippoRAG / HippoRAG 2 | NeurIPS 2024 主会 / ICML 2025，PMLR 267 | 查询链接后以 PPR 传播，2 加入 passage 节点和 query-to-triple | 离线 OpenIE；1 查询 NER；2 在线用 LLM 过滤候选三元组 | 后续 PPR 检索实验 |
| BYOKG-RAG | EMNLP 2025 主会，27881–27898 页 | LLM 生成多个图检索线索，工具完成实体链接、路径/三元组/查询检索，迭代细化 | 在线 KG-Linker、可执行图查询及答案生成 | 支持“调用方 Agent + 确定性工具”的方向；完整流程较重 |

状态来源：[KG2RAG 正式条目](https://aclanthology.org/2025.naacl-long.449/)、[GraphRAG 作者出版物页](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/)、[GraphRAG arXiv v2](https://arxiv.org/html/2404.16130v2)、[LightRAG 正式条目](https://aclanthology.org/2025.findings-emnlp.568/)、[HippoRAG 正式论文](https://proceedings.neurips.cc/paper_files/paper/2024/file/6ddc001d07ca4f319af96a3024f6dbd1-Paper-Conference.pdf)、[HippoRAG 2 正式条目](https://proceedings.mlr.press/v267/gutierrez25a.html)、[BYOKG-RAG 正式条目](https://aclanthology.org/2025.emnlp-main.1417/)。

## 各路线的适用范围

### 1. KG2RAG：检索种子后，让图谱补全并组织证据

论文先按语义相似度选 seed chunks，再沿这些块关联的 KG 做 m-hop 扩展，读取新增三元组对应的原文块。组织阶段对图和块进行相关性筛选，并利用连通结构组织上下文。第 2.1 节明确允许使用已有 KG，通过链接建立 chunk–KG 关联；论文实验为了不依赖已有 KG 才采用 LLM 抽图。因此，**复用审校图谱符合方法接口，不需要因采用该思路而重抽正式知识库**。在线图扩展可由 BFS 等图算法完成，不以 LLM 查询规划为前提。[论文 §2.1–2.3](https://aclanthology.org/2025.naacl-long.449.pdf)

本项目可把 seed chunks 替换为“初始命题及原文证据”；通过已审校的概念—命题—证据映射扩展，输出原文、命题条件、关系及路径。论文的实体事实图与本项目带条件、审校和身份边界的知识结构不同，因此只迁移流程，不应把命题降成无条件三元组。

评测以 HotpotQA 及其变体为主，分别比较检索事实的 precision/recall/F1 与生成答案对标准答案的 precision/recall/F1。其公开实现也按 distractor/fullwiki 基准组织，不能当作现成 Windows 便携产品。[正式条目](https://aclanthology.org/2025.naacl-long.449/)、[作者实现](https://github.com/nju-websoft/KG2RAG)

### 2. Microsoft GraphRAG：local 与 global 解决不同问题

原论文重点是 corpus-wide 的 query-focused summarization：从 LLM 派生实体图，建立层级社区和社区摘要；查询时对摘要生成局部回答，再归并全局答案。实验集中于两份约百万 token 的播客/新闻语料及全局 sensemaking 问题，以生成答案的全面性、多样性等评价；作者明确指出跨领域泛化与编造率评估仍需补强。它不是局部原文证据检索 Recall 的通用胜出证明。[原论文 §3–6](https://arxiv.org/html/2404.16130v2)

作者仓库的 local search 则以语义相关实体为入口，联合获取关联实体、关系、原文 text units 等，按上下文预算筛选后交给回答模型。global search 使用社区报告进行 map-reduce。两者不能只因同名 GraphRAG 而混成一个检索器，也不能拿原论文 global 实验替 local 背书。[作者 local 实现说明](https://raw.githubusercontent.com/microsoft/graphrag/main/docs/query/local_search.md)、[作者 global 实现说明](https://raw.githubusercontent.com/microsoft/graphrag/main/docs/query/global_search.md)

本项目首版可以采用 local 的“知识 + 原文 + 预算”接口。只有出现稳定的“全书主题、跨课总体分布”需求时，才值得另做可追溯、可版本化的摘要索引；社区摘要本身应保留派生身份，不能自动获得 reviewed 原文命题的证据地位。

### 3. LightRAG：双层检索值得借鉴，生成胜率不能当检索召回

正式论文的 low-level 聚焦具体实体及关系，high-level 聚焦主题及更广关系。查询抽取两层关键词，分别向量匹配实体/关系，并补充邻域；索引阶段由 LLM 抽实体、关系及描述。这里的 high-level 不等同于 Microsoft 的层级社区报告。[正式论文 §3](https://aclanthology.org/2025.findings-emnlp.568.pdf)

主评测选 UltraDomain 的四个领域语料，LLM 生成每域 125 个全局问题，再由 GPT-4o-mini 对答案做成对偏好评价。Table 1 的胜率是**答案偏好**，不是 gold evidence 的 Recall@K。表中 LightRAG 对 GraphRAG 的 Mix Overall 为 **49.6%**，也显示不能概括为每域、每指标全面领先。[正式论文 Table 1、Appendix 9.1；已对 PDF 第 6 页图像核对数值](https://aclanthology.org/2025.findings-emnlp.568.pdf)

迁移时可建立“概念/别名/具体命题”和“关系/主题描述”两个召回入口，再回到同一证据集。应先证明双通道在本地独立问题集有增益；正式论文的生成实验没有替本项目验证中文别名、短词、条件识别或作者身份。作者仓库提供持续演进的框架，论文算法与当前软件功能也需版本区分。[作者仓库](https://github.com/HKUDS/LightRAG)

### 4. HippoRAG / 2：PPR 是检索排序机制，不是逻辑证明

HippoRAG 离线用 OpenIE 构图并连接同义概念；查询时 NER 和检索编码器找到图节点，以 Personalized PageRank 传播，然后聚合回原文段落排序。正式实验分别报告 passage Recall@2/5 和答案 EM/F1，主要是各抽取 1,000 个验证问题的多跳 QA 设置。它的优势受任务结构影响，论文也讨论实体中心设计与上下文信号之间的取舍。[NeurIPS 2024 论文 §2–4](https://proceedings.neurips.cc/paper_files/paper/2024/file/6ddc001d07ca4f319af96a3024f6dbd1-Paper-Conference.pdf)

HippoRAG 2 加入 passage 节点，直接匹配 query-to-triple，使用 LLM 过滤候选 triples，将短语和段落共同作为 PPR 种子；无法形成 triple 种子时退回 dense passage 检索。正式 ICML 表 2 报生成答案 F1，表 3 报 passage Recall@5；表 3 明确未列 GraphRAG/LightRAG，因为它们不直接产生这种 passage 检索结果。[正式论文 §3、§4.3、Tables 2–3](https://raw.githubusercontent.com/mlresearch/v267/main/assets/gutierrez25a/gutierrez25a.pdf)

迁移优先级应低于可解释的有限邻域扩展：当前审校图的边类型、方向和覆盖密度与 OpenIE 图不同；PPR 概率不能证明“条件满足”或“作者支持”。若试验，应把命题/原文节点纳入，限制来源身份与审校状态，记录传播路径，并与“无传播”“一跳扩展”做消融。[作者代码](https://github.com/OSU-NLP-Group/HippoRAG)

### 5. BYOKG-RAG：调用方 Agent 规划，专门工具完成检索

该方案针对 bring-your-own KG：LLM 生成问题实体、候选答案、关系路径和 OpenCypher 等线索；工具完成链接、路径/三元组/图查询检索，反馈上下文后迭代。它证明了“Agent 的模型能力与专门检索工具分工”是一条正式研究路线，而非必须把模型和图数据库封在同一程序内。[正式条目](https://aclanthology.org/2025.emnlp-main.1417/)

其五组 KGQA 基准包含 Freebase、时序、医疗和企业图，主指标有答案 Hit、Hit@2 和执行结果的 LLM judge；另有检索 Recall@K，不能混称统一检索准确率。论文限制部分承认上下文可能膨胀，且 KG 是唯一外部信息源，原文数据库属于未来扩展。因此，这不是本项目“完整原文证据链”的直接验证。[正式论文 §4、Limitations](https://aclanthology.org/2025.emnlp-main.1417.pdf)

本项目可以保留固定工具，由调用方 Agent 决定何时组合调用；无须为首版复制完整的 OpenCypher 生成与多轮模型编排。用户选定调用方生成答案后，检索工具应优先返回确定、可审计的证据包。

## 经原文核对的数值如何使用

下面只保留三个能说明评测差异的例子，不构成跨论文排行榜。

| 例子 | 经核对的数值 | 实际含义与边界 |
|---|---|---|
| KG2RAG，HotpotQA distractor，Table 2 | 检索 F1 **0.436**，precision **0.301**，recall **0.908**；Hybrid RAG 为 **0.354 / 0.222 / 0.921** | 图组织改善该设置下的精确率/F1，同时召回并非每项都最高；与答案 F1 是不同表 |
| LightRAG 对 GraphRAG，Mix，Table 1 | Overall 胜率 **49.6%** | LLM 对生成答案的成对偏好，不能读成 evidence Recall，也不支持所有任务全面最佳 |
| HippoRAG 2，Table 3 | 平均 passage Recall@5 **78.2**，NV-Embed-v2 为 **73.4** | 该表五类数据的段落召回平均；对应 Table 2 的七任务生成 F1 平均为 **59.8 / 57.0**，两组平均不能互换 |

数值来源：[KG2RAG Table 2](https://aclanthology.org/2025.naacl-long.449.pdf)、[LightRAG Table 1](https://aclanthology.org/2025.findings-emnlp.568.pdf)、[HippoRAG 2 Tables 2–3](https://raw.githubusercontent.com/mlresearch/v267/main/assets/gutierrez25a/gutierrez25a.pdf)。后两份正式 PDF 的相关表格同时经过本地渲染和目视核对。不同论文的语料、抽图模型、查询类型、重排器、预算及 reader 不同；上述数字没有给出本项目预期增益。

## 成熟首版建议：以现有审校图为事实层，增加检索层

以下为针对当前约束的建议设计，不是已实现、已验证能力。

1. **种子召回保留多个入口。** 精确概念/别名和中文词法召回承担术语问题，段落/命题语义召回承担自然改写；先收集候选，再统一去重和排序。把权重、候选数量和 reranker 作为评测参数，不能因“混合”二字直接预设等权 RRF 最好。
2. **先做有预算的确定性图扩展。** 从种子命题、概念和原文段落出发，优先沿已审校、类型明确的边补前提、例外、对比及直接证据；初版可从一跳开始，但跳数、条数和 token 预算都应可配置。关系路径是召回解释，不自动成为推理结论。
3. **按证据单元组织返回。** 一个单元至少包含稳定 ID、完整条件化命题、review 状态、来源身份、原文、实际 PDF 页码/段落 ID、相关边及命中原因。相邻原文只补足必要上下文，避免把读者问题并成作者结论。返回截断与覆盖信息，让调用方知道还缺什么。
4. **由调用方 Agent 处理表达与追加检索。** 本地工具可提供一次“检索并组织证据”的入口，同时保留 concept/neighbors/evidence 等细读接口。需要模型拆问题、关键词或候选路径时，调用方可显式传入；这些仅是查询线索，不写入 reviewed 知识。
5. **索引与事实版本分开。** Embedding、词法倒排、主题描述、PPR 图或未来摘要都是可重建的派生索引，绑定图版本与构建参数；正式 SQLite 的命题、身份和审校状态仍为事实依据。便携交付应测试真实离线运行、模型/索引资源、移动目录及独立于桌面软件的调用，论文开源并未完成这些验收。

此方案的价值是充分使用已有人工审校成本，兼容未来模型或算法更换，也让“证据从哪来、为什么被召回”在返回数据中可查。其有效性仍须由项目独立评测决定。

## 评测应先回答的几个问题

至少区分：术语/定义、条件与例外、跨课多证据、关系比较、来源身份、全局综述及证据不足。开发集用于调参数；独立保留集用于验收，人工标注应给允许的证据集合与必须同时命中的证据组，避免单一段落字符串充当所有问题的答案。

检索先比较“词法/别名”“语义”“两者融合”“融合 + 一跳扩展”“融合 + 图扩展 + 重排”；之后有需要才加 PPR。除 Recall@K、nDCG/MRR 外，还要统计：完整证据组覆盖率、条件/例外覆盖率、错误来源身份、未审校泄漏、预算内有效证据、查询时延与索引体积。别名和短中文词应有单独结果切片。

生成回答由调用方 Agent 完成，另行固定 reader 与提示词，评价引用正确性、事实支持、条件保留和恰当拒答。证据命中与回答正确分开报告。全局综述需要另一类 gold/覆盖设计，不能只用事实短答 F1；LLM 偏好评分也不能替代人工审校证据的正确性核验。

## 不宜直接套用

- 为采用某框架重抽并覆盖人工审校图，或把抽出的实体边视为已审校命题。
- 用社区摘要、LLM 实体描述或候选答案替代原文证据；把主题邻近等同于论证支持。
- 将所有关系无差别双向化后做 PPR，或以传播高分推断作者认可与条件成立。
- 复制论文的全局合成问题和 LLM 胜率就宣称检索达标；把作者重现实验中某基线低分概括为该方法普遍无效。
- 为本地便携首版引入完整云图数据库、自由图查询生成或 GNN 训练。当前证据支持方法思想可迁移，未证明这些额外设施对本项目必要。

## 复核记录

- 已读取本仓库 `AGENTS.md` 与 `AGENT_GUIDE.md`；本研究不解释缠论概念，因此未调用内容检索 CLI，不将研究文献写入原文知识库。
- LightRAG 使用 ACL 正式版 PDF，HippoRAG 2 使用 PMLR 正式版 PDF；没有用旧预印本表格替换正式结果。
- GraphRAG 的 local/global 机制引用作者仓库说明，并明确与原论文 global 实验区分。
- 本篇只形成方法研究和建议，没有运行项目代码、建立索引或评测任何新检索方案。
