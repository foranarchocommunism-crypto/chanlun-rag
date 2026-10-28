# RAG + KG 检索迁移：本地事实核查与最小迁移边界

核查日期：2026-10-22。范围：本地现有数据、源码、既有评测和机器配置。本文是迁移研究，未运行测试、构建、导入、模型推理或下载，未改源码或知识库。唯一新增内容是本研究文档。桌面端及 backups 的外部归档不在本轮范围内。

用户已确定：交付 Windows 便携独立目录 ZIP，回答由调用方 Agent 生成，CLI / MCP 接口由研究拟定。本文中的“已核事实”来自当前文件、只读 SQL 和只读 CIM；“建议”是待实施及验收的设计，不能作为已交付功能。

## 1. 已核事实：现有事实源能够复用

当前共享知识库为 `shared-knowledge/v0.1.0`，版本 `0.1.0-review-307029129712`，Schema `1.1.0`。manifest 记录 2 份固定 PDF、907 页、110 个来源单元、9,650 个段落、528 张图、318 个概念、6,008 个命题、692 条关系和 3,459 条复核记录；coverage 与只读数据库查询一致，命题为 reviewed 3,369、pending 2,611、rejected 28。默认知识的证据引文为 4,584 条，全部证据共 7,225 条。[S1][S2][S3]

交付目录 `deliveries/chan-knowledge-20261022-307029129712` 的范围明确是 `shared_knowledge_base_only`，不包含已完成的 Agent 软件产品。共享库与实际交付复制件的 `graph.sqlite` 当前均为 71,626,752 字节，实读 SHA-256 均为 `3463d772e607c6e89104c17c02c6b3656cca766f444d226c011fb9d8a9017271`，与 delivery-manifest 的 canonical hash 一致。[S4]

`semantic_review_in_progress`、`semantic_completion=false` 与“108 课已逐来源处理”并不矛盾：来源处理闭合包含明确待核与排除，不能将 2,611 个候选或 473 条保留显式歧义的 reviewed 命题说成全部解释已经确认。265 张图保留原作者未核，263 张为后加图；后续检索不能将图像查看记录替换为原作者认证。[S1][S3][S5]

`KnowledgeGraph` 用 `node:sqlite` 的 `DatabaseSync(..., {readOnly:true})` 打开库；查询入口在读事务内重新读取 metadata、核对 manifest 的 graph/schema 版本，返回带版本的 JSON envelope。现有证据返回原文身份、PDF/印刷页、源 PDF 哈希、资源路径、字符区间、坐标、相邻语境和图记录。这层应保留为权威读取层。[S6]

## 2. 已核字段与建议映射

下表左列是现有主键/字段，右列是建议的检索适配含义。现有 ID 一律复用，不按新标签重新生成主键，不把数值向量行号用作对外 ID。[S2][S6][S7]

| 现有实体与主键 | 必须保留的字段 | 建议的索引/检索映射 |
|---|---|---|
| `documents.id` | filename、sha256、page_count、resource_path | `Document.document_id`；PDF 哈希是来源身份，不以磁盘绝对路径作为身份 |
| `units.id` | kind、lesson_number、published_at、document_id、起止页、processing_status、note | 来源单元/课程锚点；保留附录排除原因，不能只存课号 |
| `pages.id` | document_id、pdf_page、printed_page、width/height、raw_text、geometry_path | 页面定位；实际 PDF 页与印刷页分字段，geometry 通过包内相对路径定位 |
| `passages.id` | unit/document/page、block_index、role、speaker、published_at、text、raw_text、boxes、normalized_map、source_char_indices | `SourcePassage`；检索文本用 text，精确引用仍从本体读取；检索归一化另存，不能覆盖原文 |
| `concepts.id` | label、aliases、description、importance_level/reason | `Concept` 节点与实体链接入口；无独立 review_status，不能据“概念存在”推断其所有说法已复核 |
| `claims.id` | text、kind、conditions、exceptions、concept_ids、review_status、ambiguity_status、review_note、derivation、importance | `Claim` 检索记录；embedding/词法字段建议含正文、条件、例外及关联概念 label/alias；输出保留分离字段 |
| `evidence.id` | claim_id、passage_id、quote、quote_start/end、source_spans、figure_ids | `Evidence` 引文对象；命题到原文的权威桥接，支持关系不能跳过这一层 |
| `relations.id` | source、target、type、claim_ids、review_status、importance | `Relation` 有端点关系；另建 `relation_support(relation_id,claim_id)`，从支持命题展开 evidence，不捏造关系自己的 quote |
| `reviews.id` | claim_id、reviewer、checked_at、checks、result、note | 复核 provenance；检索得分不能覆盖该状态或声称复核者独立身份已经认证 |
| `figures.id` | document/page、bbox、origin_status、note | 图锚点；保留 later_annotation / unverified。文本向量不证明图形含义 |

可核查的一条完整链：`relation-00ed3bf86d87cad6` 将 `concept-6912d5c0e563f45b`（区间套）通过 `qualifies` 指向 `concept-3403e6e29ce58f3f`（次级别），支持命题为 `upper-l037-c-stage-standard-c-internal-trend-recursive-interval-nesting`，证据 `evidence-29f0735b0d1a85ec`，原文 `volume_1-a53e99c37ca5-p0274-b001`，`lesson-037`，`author_body / 缠中说禅`，实际 PDF 274 页、印刷 268 页。迁移后的任一路径结果均应可恢复这类完整链，而不是只返回“区间套 → 次级别”。该示例来自本次只读 JOIN。[S2][S6][S8]

导入器目前的概念 ID 可由标签摘要生成，关系 ID 来自 source + type + target 的摘要，证据 ID 来自命题、序号、段落的摘要。重建这些 ID 会破坏既有题目和证据链接；迁移必须读取现有 ID，而非再次调用导入算法。[S7][S9]

`quote_start/end` 的契约是 Unicode 码点区间；Python 审核用该区间验证归一原文的精确子串。若 Node 侧新增切片，不能直接将码点偏移当 UTF-16 `String.slice` 偏移。建议切块时保存 `parent_passage_id`、码点起止和 canonical text hash，以原文映射恢复 PDF 坐标。[S7]

现有 JSONL 导出带 graph_version，claims 为 reviewed 且内嵌证据，concepts 为完整概念清单，relations 按自身 reviewed 导出。导出脚本没有复制 `neighbors` 对 `claim_ids` 的逐项过滤逻辑，因此消费关系导出时仍要 JOIN 当前 reviewed 支持命题，不能把“导出一条关系”自动当作其全部支持项满足当前策略。待核候选、完整原文/映射和复核记录仍需 canonical SQLite；仅导入这三份 JSONL 不是完整迁移。[S10]

## 3. 默认复核与来源角色：现状和迁移策略

已核：`claimWhere` 默认 `review_status='reviewed'`；`includeUnreviewed=true` 默认放行非 rejected 项；显式请求 pending/rejected 还必须开启 includeUnreviewed。evidence 跟随命题状态；neighbors 同时筛关系状态和支持命题状态，过滤后无支持项的边不返回。importance 与复核状态独立。[S6]

已核：原文 `search(scope='source')` 不作命题复核过滤，也不筛角色；排序只优先 author_body / author_reply，没有同等优先 author_commentary。`getEvidence.context` 读取同来源单元相邻 ±1 PDF 页的段落，其中可含读者、未知身份等，仅提供上下文。[S6]

本次只读统计的原文角色为 author_commentary 3,718、author_reply 1,864、author_body 1,827、reader 1,777、unknown 464。reviewed 证据分别来自 author_body 1,926、author_commentary 1,612、author_reply 1,046，没有 reader/unknown。[S2][S3]

现有审核契约允许的作者角色是 author_body、author_reply、author_commentary，speaker 必须为“缠中说禅”；author_commentary 还要求 review_note 分别记录语境与适用条件，compiler_appendix 不得支持作者知识。[S7]

明确推荐新 `retrieve` 默认只检索 reviewed 命题及其关联证据：结构化分支索引命题正文、条件/例外、概念；证据分支索引这些命题的精确引文并保留parent passage身份。关系扩展只用 reviewed 且仍有 reviewed 支持命题的关系。这里“reviewed证据”表示所属命题已reviewed；evidence表本身没有独立review_status列，不新增一个虚假的来源状态。

全原文检索保留在显式 `scope=source|context`，可再用 `sourceRoles` 选择作者或所有角色，并明确标 `source_role`、`speaker` 和 `semantic_review='not_asserted'`。reader、unknown、汇编附录按真实身份提供研究语境，不用于作者命题支持。即使一个parent passage关联了reviewed evidence，也不能把该段其余未被引证句子全部升级为reviewed；如返回整段，它的非引文部分只作context。

这个默认与既有“全角色原文 A 分支”的候选集合不同，不能直接继承A分支Recall。后续基线应单独标明reviewed-only和显式source模式，不以提高召回为由默默混入待核原文断言。

调用方应拿到 `kind`、conditions、exceptions、ambiguity、review_status、来源身份与支持链，不得仅拿一个拼接字符串。返回的相邻上下文标为 context，不能隐式转为 evidence。3 条 inferred 命题需要保留 derivation.supporting_claim_ids，不能被重排器改为 explicit。[S3][S6][S7]

## 4. 关系可遍历性、有向性及索引不足

已核：现有 692 条关系均 reviewed，类型为 qualifies 380、related 128、requires 111、distinguishes 31、composed_of 20、defines 20、illustrates 2。本地契约规定类型枚举和 source/target，但未提供每种类型的完整形式语义、逆关系或传递律。[S2][S7]

`neighbors` 的 depth 只允许 1–2，节点 limit 最大 200。它先读取所有允许关系、逐项查支持命题，再按“frontier 包含 source **或** target”扩展。因此现有遍历是无向可达遍历，输出仍保留 source/target；它没有证明 `A requires B` 可反向推出 `B requires A`，也不返回每一步具体证据路径。new frontier 只包含新发现节点，不能把返回 edge 集直接当作所有长度 ≤ depth 的逻辑推理链。[S6]

建议保留旧 neighbors 行为以兼容，引入新扩展参数 `direction=out|in|both`、类型白名单、hop 上限和每概念边数上限；在 path 中显式记录 `traversed_direction`，逆向取证只是查找用途，不改写原关系。requires / composed_of 等默认按已存方向探索；related / distinguishes 可候选双向导航，但须先抽样核对源数据方向约定。对 qualifies / defines / illustrates 先保留原端点与类型，不创造传递闭包。任何图扩展加分都必须伴随 relation_id → 支持 claim_id → evidence_id → passage_id 的链。并列存在、发布时间较晚不能自动生成“修订/反驳/限制”关系。[S6][S7][S11]

已核的 SQL 索引只有 passages_page、passages_unit、passages_role、claims_status、evidence_claim 这些显式 B-tree 索引，加上各主键/唯一索引和 `passage_fts` 的 FTS5 trigram。没有原生向量索引，没有 relation source/target 索引，没有 relation_support / claim_concept 规范化连接表。`concept_ids` 与 `claim_ids` 都是 JSON TEXT；生产检索用 `instr(concept_ids,?)`，概念/别名在内存扫描。neighbors 扫描所有关系并逐支持项查询。目前规模可运行，不代表适合每次扩展全图。[S2][S6]

本轮额外读取了 live `sqlite_master` 的全部 table/view 定义：claims / concepts / relations 的 importance_level / importance_reason、JSON字段和主外键与本轮读取的 contracts/schema.sql 对应；未发现额外 relation_support、relation_supports、claim_concept 表或 view。下述规范化支持表是建议建立在派生索引内的结构，不是现有字段。实施时仍应核对 live metadata、实际表结构与所支持 schema版本，不能仅凭仓库SQL文件或版本字符串臆造列。

已核：原文 search 的 WHERE 是完整 `instr(p.text,q)>0`，trigram FTS 仅在 q 长度 ≥3 时左连接做辅助排序，并未把整句自然问题分解为词法候选。knowledge search 是整句子串/条件/例外与概念包含匹配，排序主要为直接命中、重要性和 ID。离线中文 2/3-gram BM25 与 RRF 仍在 evaluation 脚本，尚未接入 core 或 CLI。[S6][S12][S13]

建议在派生检索库建立精确的 `claim_concept`、`relation_support`、双向邻接和 evidence_passage 映射，并在该派生库索引，而不 ALTER canonical graph。词法、向量和图扩展各自保留命中 ID、原始分数/名次、过滤原因，融合结果必须能解释来源；importance 是整理优先级，不应直接冒充相似度或事实置信度。

## 5. 派生索引应绑定哪些版本

当前 core 只核 manifest 与 DB metadata 中的 schema_version / graph_version 相等，不校验图谱文件摘要。已有评测快照额外绑定 DB、manifest、case 和实现摘要；快照脚本通过 SQLite backup 复制读事务中的数据库。[S6][S13][S14]

最终自然问句报告绑定的快照 DB SHA-256 是 `2b1a086310896336e15bb6e6b8a07c0974c062386de5086ac73d04d97d37ff6e`，当前 canonical 文件是 `3463d7...`，二者具有同一 graph_version，报告保留原始 source_kb 和快照时间。backup 文件与原文件字节可不同；本轮未做全表逻辑等价认证，不能把两个物理摘要混写为同一个文件的摘要。[S4][S13][S14]

建议每个索引包使用独立 `index-manifest.json`，至少绑定：

- canonical graph_version / schema_version、canonical database SHA-256、manifest SHA-256；若 builder 用备份，另记 indexed_snapshot_sha256 与 canonical_source_sha256。
- 两份来源 PDF 的 document_id / sha256；role_parser_revision、source_structure_revision、source_segmentation_revision 与 provenance 文件摘要。
- 行集合策略与过滤版本、claim/passsage/edge 计数、字段序列化/文本归一化/切块版本、稳定 chunk→parent/码点区间映射。
- embedding 模型名称、不可变 revision、文件摘要、license、tokenizer/推理运行时版本、dtype/量化、维度、池化/归一化、相似度和所需 query/document 前缀。
- 词法 tokenizer / BM25 参数；图类型和方向策略；融合权重、RRF 常数（若采用）；reranker 模型、不可变 revision、摘要、max_length、candidate 数及 truncation 策略；builder 代码摘要和构建时间。

建议在启动时严格检查这些绑定；不匹配的派生索引不参与结果。可明确报 `stale_index` 并回退现有只读查询，或拒绝新 retrieve；不要静默混用。新索引在独立临时目录完成后，以完整版本目录切换，旧版本可回退。索引构建不应接触原图谱写入、review 状态或出版流程。

## 6. 240 题：已证明的层级与尚未证明的事项

当前应引用最终报告 `stage-h-final-baselines-307029129712.results.json`，而不是早期 b24/b25 的不同库版本指标。其 240 题全部进入排序统计，输入是未改写的 query_text，未执行既定 retrieval_plan，未使用 gold ID 或证据原文改写问题；比较单位是唯一 passage_id，命题先展开证据段落，再去重。source / structured / production 返回候选预算各 100；fusion 从两通道各取 50，不能把这个预算误说成 CPU 成本相同。[S12][S13]

| 已存方案 | Recall@10 | Recall@20 | 已存单次热缓存 p95 |
|---|---:|---:|---:|
| A 原文词法（全角色） | 0.433472 | 0.512302 | 3.453 ms |
| C reviewed 结构化词法 | 0.720010 | 0.818889 | 1.968 ms |
| D 等权 RRF（常数 60） | 0.673795 | 0.795952 | 5.364 ms |
| 当前生产 search 整句输入 | 0.069643 | 0.125347 | 106.265 ms |

这些是既有报告读数，本轮未重跑。词法索引及加载准备另记约 1,458.76 ms；未做冷启动、重复测速或显著性检验。当前报告明确 `B_vector=not_implemented`，所以不存在“已证明向量更优”的证据。等权 RRF 的平均 Recall 低于 C，不能依据“混合检索常见”直接宣布等权融合可发布。[S13]

另一个既定取证计划回归是 239/240 通过，来源身份 240/240 通过；已知失败为 g-b05-coincidence，原“重合”top20 未取得指定第21课命题。这个结果与整句自然问题检索是两个层级。[S3][S5]

可用这些题证明：在该冻结开发题、该证据标注子集和该版本上，比较候选排序的标注证据召回；回归稳定 ID、出处身份与既有读取接口；暴露截断、条件、来源身份等可复现问题。

不能证明：独立测试集泛化、人工认可的证据充分性、所有未标注结果不相关、多跳路径推理成立、条件/例外在回答中保留、矛盾解决正确、语义蕴含、图像解释、生成回答忠实度、反幻觉、日期全量正确或 Windows 便携运行。原题文件虽然有 acceptable_answer_conditions 与 forbidden_inferences，本次历史报告没有生成或评分回答；gold 由模型复核，`human_gold_reviewed=false`、`independent_test_set=false`。不能更名为独立金标准。[S12][S13][S15]

## 7. 本机资源与本地向量/重排可行性

本次只读 CIM 与命令发现：

| 项目 | 实读结果 | 对方案的约束/建议 |
|---|---|---|
| CPU | Intel Core i5-1038NG7 @2.00GHz，4核/8逻辑线程，64位 | 首版以 CPU 为基线；线程数、批量和并发必须后续实测 |
| RAM | 16,972,886,016 字节，约15.81 GiB；采样时空闲约6.55 GiB | 可容纳当前规模的向量本体；模型与其他程序共享内存，空闲值只代表采样时刻 |
| GPU | Intel Iris Plus Graphics，CIM AdapterRAM 1,073,741,824，驱动31.0.101.2140 | 集显报告不是推理可用显存/加速认证；不把 CUDA 作为交付前提 |
| OS | Windows10 专业版，10.0.19045，64位 | 在该机及干净Windows环境验证便携包；新增运行时需核兼容性 |
| Node | `C:\Program Files\nodejs\node.exe`，v24.15.0 | 已满足现有 package 的 Node>=24；ZIP 应携带审核后的 Node 与许可证 |
| Python | Python3.12.10，`C:\Users\13240\AppData\Local\Programs\Python\Python312\python.exe` | 当前环境有 numpy2.5.0 / scipy1.18.1；不能作为目标机器已安装依赖的假设 |
| 当前 Python 分发包元数据 | torch、sentence-transformers、transformers、onnxruntime、onnxruntime-gpu、faiss-cpu、hnswlib、FlagEmbedding、tokenizers 均未发现 | 只代表该 Python 环境，不是全盘软件缺失证明；没有加载模型或安装依赖 |
| PATH 命令发现 | 未发现 nvidia-smi、ollama | 只代表命令发现，不推断机器其他目录完全不存在这些软件 |

在最简单的“9,650段落 + 3,369 reviewed命题”双对象集合上，共13,019向量。以 float32 粗算，384维向量数组约19.07 MiB，1,024维约50.86 MiB，尚未计模型、tokenizer、索引结构、文本元数据和运行时。这是包括显式source模式的全量段落容量示例，不是默认reviewed-only集合的定义，也不是模型内存或速度测试；证据引文去重、作者角色过滤、切块及多向量会改变N。

建议首轮比较 CPU 小型多语/中文 embedding 与较强中文模型的实际收益；精确向量扫描可作为当前小集合的简单基线，只有规模/延迟证明需要时再增加 ANN 依赖。重排只对有界 top-N 候选启用（建议先比较20/40，最终值待实测），模型常驻/按需两种模式测峰值内存和冷启动。默认路径必须在无 GPU 情况下完成，重排缺失或超时应产生可解释降级状态。未下载或测试任何模型，因此本文不承诺模型大小、吞吐或秒级响应。

## 8. 建议最小迁移模块与兼容 API

现有 public API 为 `KnowledgeGraph` 及 query 的 search / concept / neighbors / evidence / coverage / sources / concepts / page；CLI 将参数映射到同一 query 并把 JSON 写 stdout、诊断写 stderr。源码中未发现已实现的 MCP server。旧 `scripts/package.mjs` 能复制 Node 与许可证，但默认图谱路径仍为相邻 `../shared-knowledge/v0.1.0`，并复制 scripts/test；这还不是用户本次确定的独立目录 ZIP 产品结构。[S6][S16][S17]

建议只新增下列职责，保留上述八个旧命令及字段语义：

| 模块 | 最小职责 | 明确边界 |
|---|---|---|
| canonical adapter | 复用 KnowledgeGraph，精确 ID hydration / policy filter / evidence | canonical DB 只读；新排序不改旧 search 默认行为 |
| offline index builder | 从固定版本生成词法、向量、精确连接与邻接；写 index-manifest | 单独开发/发布工具；日常用户无需 PDF 抽取、import 或构图模型 |
| retrieval service | entity linking → 有界词法/向量候选 → 受支持图扩展 → 可选重排 → 去重与完整证据回填 | 不生成最终回答，不重新抽取命题/关系，不写回图谱 |
| shared query contract | `retrieve(query, options)`、`health/status`、已有 query 统一校验 | 同一策略/预算/JSON数据模型；不是 CLI 和 MCP 各实现一套检索 |
| CLI adapter | 新增 retrieve / status 与旧命令并存；稳定退出码 | stdout 仅结果 JSON，日志 stderr；调用方可无会话调用 |
| MCP stdio adapter | 同进程服务或同库调用，公开相同工具契约 | 传输适配；不能执行知识库写入或使回答依赖某一 Agent 品牌 |
| portable package | `runtime/`、`app/`、`knowledge/`、`indexes/`、`models/`、licenses、启动cmd与校验清单 | 以包根定位；移动、空格/中文路径、离线首次启动均应验收 |

建议新 retrieve 输出 `retrieval_version`、graph/schema/index/model 版本、applied_filters、budget、degraded/status、候选 ID 与来源、完整命题和证据、支持路径、截断原因及可继续取证入口。分数要区分 lexical / vector / rerank / fused，不把多通道分数当概率或真实性。可在新工具返回精简摘要与 ID，由旧 evidence/concept 按需取完整内容，避免 getEvidence.context 的全页语境撑爆上下文预算。

## 9. 建议分阶段验收：每阶段回答一个实质问题

1. **契约与无损投影**：固定同一 canonical hash；概念/命题/证据/关系支持 ID 全量可回溯；条件、例外、角色、码点、页码、歧义、推论前提不丢失。覆盖 pending/rejected、作者解盘、读者/未知、后加图与附录的负向样例。旧八命令输出与复核政策保持兼容。这里只验证读入契约，不重做原书语义复核。
2. **自然问题检索**：先把已有 C_structured_lexical 作为明确基线，再独立比较纯向量、词法+向量、加图、加重排；同 query、同库版本、相同最终候选/上下文预算。沿用240题作开发回归并逐案解释回退；新增真正独立、人工核证据的留出集，用成对比较/区间评估是否值得发布。候选输出必须零 pending/rejected 默认泄露、零读者冒作者、零不支持边。具体质量阈值在拿到留出集前固定；不能先调参再用这240题命名为独立验收。
3. **图扩展贡献**：单独设计 requires/qualifies、双向查找、1–2 hop、无边概念、过大邻域与方向反例；检查每跳 relation/support/evidence 成立和路径预算。对照无图版本，衡量新增证据召回与无关上下文率；不只统计“返回了边”。
4. **调用方回答验收**：库层只交付证据，仍需由目标调用方 Agent 生成回答样例，人工核对引用、条件/例外、明说/推论/争议和不足时停止。分离“检索没找到”与“Agent没使用/误用了证据”。不把第三方Agent输出质量归结为纯检索指标。
5. **独立 ZIP 与运行性能**：在目标机及未安装Node/Python/模型的干净Windows环境解压，断网运行 CLI 与 MCP，相同请求核对同一结果；移动目录和中文/空格路径；校验 runtime/models/indexes/knowledge 真实哈希、许可证和来源；禁止运行时联网下载。记录冷启动/热查询 p50/p95、不同候选数与并发、峰值RAM、重排关闭/缺失/超时及陈旧索引回退。验收对象是实际 ZIP 解压件，而不是开发工作目录。原库及PDF前后哈希不变。

推荐实施顺序：保留 canonical 只读接口 → reviewed 结构化词法产品化与统一CLI/MCP → CPU向量候选与受支持图扩展 → 在数据证明收益后决定融合权重和rerank → 独立ZIP实机验收。当前证据支持“现有事实源与读取接口可复用、自然问句召回需升级”；不支持“迁移一定要另建图库服务”或“向量/等权融合已经通过验收”。

## 来源与核查方法

以下均为本地一手源码/实际交付记录。硬件表来自本轮 `Get-CimInstance Win32_Processor / Win32_ComputerSystem / Win32_OperatingSystem / Win32_VideoController`；运行时来自 `Get-Command`、版本命令与 `importlib.metadata`；数据统计用 SQLite URI `mode=ro&immutable=1` 的 SELECT。未运行 curation、validate、test、package、export 或 retrieval evaluator。

- [S1 当前manifest](../../../shared-knowledge/v0.1.0/manifest.json)
- [S2 Schema](../../contracts/schema.sql)；本轮对graph.sqlite的只读SELECT（显式索引、角色、关系类型、证据与链路）。
- [S3 最终质量审计](../../../deliveries/chan-knowledge-20261022-307029129712/audit/final-quality.json)
- [S4 实际交付manifest](../../../deliveries/chan-knowledge-20261022-307029129712/delivery-manifest.json)；本轮Get-FileHash比对共享库/交付复制件。
- [S5 知识库交付说明](../../../deliveries/chan-knowledge-20261022-307029129712/README.md)
- [S6 查询核心](../../src/core.mjs)
- [S7 审核字段/身份/码点契约](../../tools/curation_contract.py)
- [S8 同版本关系导出](../../../shared-knowledge/v0.1.0/exports/relations.jsonl)及[命题导出](../../../shared-knowledge/v0.1.0/exports/claims.jsonl)
- [S9 导入器的ID与支持项逻辑](../../tools/import_curation.py)
- [S10 导出脚本](../../scripts/export.mjs)
- [S11 Agent取证指南](../../AGENT_GUIDE.md)
- [S12 离线词法/融合算法](../../scripts/lib/retrieval-baselines.mjs)及[评测runner](../../scripts/evaluate-retrieval-baselines.mjs)
- [S13 最终240题自然问句结果](../../evaluation/stage-h-final-baselines-307029129712.results.json)
- [S14 冻结快照脚本](../../scripts/snapshot-retrieval-eval.py)及[最终快照provenance](../../../deliveries/chan-knowledge-20261022-307029129712/audit/retrieval-snapshot.json)
- [S15 原始开发题示例](../../evaluation/stage-g-batch-25.cases.jsonl)
- [S16 CLI](../../bin/chan-kg.mjs)及[包元数据](../../package.json)
- [S17 现有打包脚本](../../scripts/package.mjs)及[cmd启动器](../../chan-kg.cmd)

本轮写入前后已读取并比对原有8项untracked对应文件的SHA-256，8项均未变化：b24.analysis、b24/b25.results、analyze/evaluate脚本、scripts/lib/retrieval-baselines.mjs、snapshot脚本及retrieval-baselines.test.mjs。本文不将这些既存文件算作本轮新增或迁移实现。
