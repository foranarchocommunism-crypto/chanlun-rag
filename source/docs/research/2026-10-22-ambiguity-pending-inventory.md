# 473条已复核显式歧义与2611条待核候选：全量只读盘点

日期：2026-10-22；固定版本 `0.1.0-review-307029129712`，schema 1.1.0。机器清单 `2026-10-22-ambiguity-pending-inventory.json` 包含**3084条不重叠稳定ID**：`records.reviewed_ambiguity` 473行、`records.pending_candidates` 2611行，顶层 `row_count=3084`、`counts.total=3084`。逐条保存文本与审核说明哈希、证据来源页与字符区间、条件/概念字段完整性、现有审核ID、逐段台账行号、历史待核/部分解决导航及字面重叠标志；不复制大段原文，不更改任何知识或审核状态。

## 数字的精确定义

- **473** = `claims.review_status='reviewed' AND ambiguity_status<>'none'`，属于3369条reviewed命题。它不是473对矛盾，不表示作者473处说错。
- **2611** = `claims.review_status='pending'`。它与上下册pending日志事项不是同一集合，也不是2611个独立理论缺口。
- 当前6008条claims = reviewed 3369 + pending 2611 + rejected 28。manifest与数据库版本一致；本轮473个ID与既有最终歧义清单全等。[S1][S2]
- reviewed在本工程表示已有出处、身份、转述和条件的复核记录。作者理论、经验收益、数学证明、解释统一和独立人工复核不因此成立；`kind=explicit`也必须与review_status一起读取。[S3][S5]

## 473条保留的并不只有“矛盾”

全量共有**443种非none标签**、**473份不同review_note**。426种标签各出现1次，另17种出现多次。这是细粒度自由文本标记，不是统一的矛盾分类。全部443种分布及473份审核说明的SHA256、长度、短预览和所属ID在机器清单；重复标签如下。

| ambiguity_status | 命题数 |
|---|---:|
| `definition_boundary` | 8 |
| `formal_proof_not_reproduced` | 5 |
| `author_probability_not_independently_verified` | 4 |
| `chart_period_fractal_vs_strict_structural_level` | 3 |
| `macd_necessary_wording_vs_auxiliary_scope` | 3 |
| `chart_reference_frame_vs_strict_structural_level` | 2 |
| `daily_center_forming_vs_oscillation_formed` | 2 |
| `empirical_accuracy_percentage_not_verified` | 2 |
| `execution_boundary` | 2 |
| `explicit_mar19_correction_to_mar17_stroke_state` | 2 |
| `general_executable_vs_specific_capability_gate` | 2 |
| `macd_defense_filter_vs_general_indicator_necessity` | 2 |
| `named_author_theorem_assertion_no_proof_in_source` | 2 |
| `rebound_numbering_and_pronoun_reference_scope` | 2 |
| `six_bar_minimum_vs_l081_joint_rule_scope` | 2 |
| `source_proof_branch_overlap` | 2 |
| `source_typographic_discrepancy` | 2 |

473条全部为explicit，各自均有reviewed审核记录和至少一条证据，所有概念ID可解析。共**618条证据**，记录角色为正文273、答复174、解盘171，记录speaker均为缠中说禅，涉及74个课程单元。全部引文字面区间、来源字符映射及非空坐标数据通过本轮全量比较；这不是新的语义审核、作者身份认证或图像判读。

**285条**conditions数组非空，**188条**为空；12条例外数组非空。空数组只说明该结构化字段没有条目，不能据此断言作者没有条件；条件可能在claim.text、review_note、邻接读者问题或后续短答中。检索与回答若只拿claim.text，会丢失这些边界。

本轮仅用ambiguity_status的字面正则做多标签分流，用于导航下一轮阅读，**不作新的语义裁定**。全部规则和逐条命中保存在JSON的 `heuristics` 及 `heuristic_label_tags`；命中数不能相加为473。75条未被本轮规则命中也不等于“没有问题”。

| 标签字面特征分流 | 命中命题数 |
|---|---:|
| `scope_level_time_or_execution_boundary` | 165 |
| `empirical_performance_or_external_verification` | 163 |
| `text_number_formula_or_figure_discrepancy` | 99 |
| `unmatched` | 75 |
| `formal_proof_or_algorithm_missing` | 63 |
| `ellipsis_reference_or_context` | 46 |
| `source_attribution_or_provenance` | 4 |

## 2611条是角色修订2的技术词召回遗留

2611条全部使用同一句审核说明：**技术词召回候选；角色解析修订2，语义与发言者仍待逐项复核**。重建 `candidate-` + SHA256(passage_id)前16位，2611/2611与现ID一致；2611/2611的claim.text等于当前来源完整段落，并各只有1条全文引文。这与 `repair_roles.py` 写入逻辑一致，足以核准它们是角色修订2产生后仍保留pending的原文召回候选，不是逐条裁定出来的歧义命题。[S4][S5]

全部kind=explicit、ambiguity_status=none、conditions=[]、exceptions=[]、importance_level=null，且**没有任何reviews记录**。这里none是初始化默认值，不能解释为“复核后确认无歧义”；explicit也是当时原文候选类型，不等于其全部含义已获核准。

| 当前来源角色 | 候选数 |
|---|---:|
| `author_body` | 1038 |
| `author_commentary` | 929 |
| `author_reply` | 644 |

来源分布涉及**106个课程单元**，没有来自汇编后记单元的pending候选；这仍是现有来源元数据，不代表本轮重核作者身份。257条没有概念ID，2354条至少有1个概念，已有概念ID均可解析。关联源自词/别名命中，不能证明语义等价。2611条字面引文、来源字符映射和非空坐标均完整。

## 与已复核命题的机械重叠

| 机械比较 | 候选数 | 可得结论 |
|---|---:|---|
| 同一passage已有reviewed证据 | 2177 | 同段原文已被某些已复核命题使用 |
| 同一passage没有reviewed证据 | 434 | 需要按台账读取其原有内容角色 |
| 某条reviewed证据引用相同全文及字符区间 | 2106 | 完整证据段共享，不证明命题同义 |
| reviewed引文区间并集覆盖候选全文 | 2116 | 字符范围全部被引用，不证明语义全部覆盖 |
| 仅部分引文字符范围重叠 | 61 | 仍需区分未引范围与已引范围的含义 |
| 完全无引文重叠 | 434 | 与没有同段reviewed证据一致 |
| 候选claim.text与某reviewed claim.text完全相同 | 0 | 没发现整段字段完全重复 |
| 仅删除Unicode空白后claim.text相同 | 0 | 没发现这种更弱的字面重复 |

**2177条同段重用不能转述为2177条已被语义覆盖或替代；0条整段文字相同也不能转述为2611条都是新知识。** 候选通常是一整段，reviewed通常是其中一个条件化原子命题；相同引文可能支持不同命题。当前schema也没有candidate到reviewed的等价/替代关系；relations连接概念，不承担候选替代证明。[S3][S5]

## 最新台账与追加式历史的边界

本轮按最新checkpoint的逐课路径读取ledger，并应用来源分拆overlay，重建**9305条课程来源台账**。2611条候选和473条歧义命题的证据全部有对应台账。253条候选所在台账明确写 `candidate_status_changed=false`；2196条候选的台账直接关联了reviewed ID。原候选状态与新的细分命题并存，不能据此猜测需要批量升格或删除。

在434条无同段reviewed证据的候选中，**19条**台账仍关联其他位置的reviewed命题。下表是其现有标签的前20项；完整分布保存在JSON。它们包括背景、历史案例、重复陈述、教学、修辞、未回答问题等不同角色，不能整体叫“434个遗漏”或“矛盾”。旧台账可使用categories多标签，标签频数不是互斥人数。

| 434条的已有台账标签（前20项） | 条数 |
|---|---:|
| `historical_session_context` | 36 |
| `historical_case` | 24 |
| `historical_case_or_background` | 14 |
| `existing_claim_retained` | 13 |
| `source_header` | 13 |
| `historical_context` | 10 |
| `historical_capability_and_rhetoric` | 7 |
| `historical_policy_context` | 7 |
| `historical_session_and_personal` | 6 |
| `theoretical_stance_and_philosophy` | 6 |
| `historical-policy-and-capability-context` | 5 |
| `historical-sector-rotation-and-rhetoric` | 5 |
| `historical_four-fates_and_self-knowledge` | 5 |
| `existing_claim` | 4 |
| `existing_local_repeat` | 4 |
| `historical-economic-and-training-context` | 4 |
| `historical-political-economic-and-forecast-context` | 4 |
| `historical-practice-and-market-language` | 4 |
| `historical_and_rhetorical_context` | 4 |
| `historical_annual_forecast_context` | 4 |

历史台账没有原文哈希的情况继续显式保留：本轮473组中3条、2611组中54条涉及这样的旧台账；有历史哈希的均与当前原文一致，0条不匹配。本轮没有为旧记录伪造历史哈希。

上下册主pending日志共**508行**（上346、下162），有501个非空且不同的事项ID，7行无ID。这些事项ID与2611个current candidate ID交集为0。它们是追加式工程研究历史，不能将每一条旧pending状态直接计作当前未解决错误。

| 历史主日志状态 | 行数 |
|---|---:|
| `pending` | 504 |
| `partially_resolved` | 1 |
| `resolved` | 1 |
| `resolved_by_explicit_later_source` | 1 |
| `resolved_textual_correction` | 1 |

另有**53份**resolution/partial-resolution日志、**258行**记录；254行明确 `global_pending_not_closed=true`。其中**179个**不同主事项ID被resolution的pending_id/resolves_pending_id字段直接引用。多数记录表示找到了新的来源，但全局条件仍待核；不能自动关闭事项，也不能只按时间较晚就废弃此前论述。全部日志导航保存文件行号。[S6][S7]

## 建议的后续处理方式

1. **473条继续保留默认reviewed身份，并带出原始歧义说明。** 查到作者明确说过某话，与相信该话已被证明是两项判断；证据包应保留条件、例外、角色、时间和明确的不确定性。
2. **2611条保留候选身份，提供显式研究入口。** 先为2177条同段重用候选形成“哪条reviewed处理了哪些内容、剩余哪些信息”的覆盖映射，再按已有台账阅读434条无同段证据候选。此顺序是成本路由，不能据字面覆盖、词相似度或向量阈值自动删去、升格或判替代。
3. **含蓄表达保存为有来源的解释假设。** 将作者原文、整理者推导、替代解释和仍未决问题分开。解释假设要列前提、支持/反例来源与适用范围，不能把整理者补出的意思回填成author explicit。
4. **先统一比较前提，再讨论冲突。** 并列检查对象、级别、时点、形成中/已完成、量词、图表周期/严格结构级别、案例/一般规则、理论保证/实际执行及读者问题指代。可以相容则保留各自条件；仍解释不通则保留双方证据，而不强求合成唯一说法。
5. **为疑似冲突形成成对或成组的研究记录。** 保存双方ID、最小表面冲突、已统一的条件、可相容解释、尚缺证据及处理状态。作者明确补充或修正须有文字依据，不能由日期或检索排名推断；原字、数值和图文差异保留原貌，校勘意见另记。
6. **没有形式证明或外部验算，也仍可保留作者信息。** 回答可以表述为“作者主张/作者经验/某次案例”；不得转成项目已证定理、可执行收益或外部事实。这样既保留表面矛盾的研究价值，也保留可追溯的证据边界。

这是研究与后续迁移策略。本轮没有进行3084条的新语义裁决，没有改变review状态、批量移除候选或实现任何迁移代码。

## 核查来源与文件保护

- [S1] `shared-knowledge/v0.1.0/manifest.json`：版本、总数及默认review策略。
- [S2] `chan-kg-agent/curation/source-audit/stage-h-final-reviewed-ambiguities.jsonl`、`stage-h-final-kb-quality.json`：473定义和既有清单。
- [S3] `chan-kg-agent/contracts/schema.sql`：claims/reviews/relations字段及默认值。
- [S4] `chan-kg-agent/tools/repair_roles.py:118`起的候选写入；`tools/extract_corpus.py:35`的digest公式。仅阅读，未执行这些写入脚本。
- [S5] 当前 `shared-knowledge/v0.1.0/graph.sqlite`：只用 `?mode=ro` 和 `PRAGMA query_only=ON`。机器清单保留全量稳定ID及机械比较结果。
- [S6] `chan-kg-agent/curation/source-audit/stage-h-l064-checkpoint.json`及其逐课ledger路径，叠加 `stage-h-annotation-split.coverage.jsonl`。
- [S7] `chan-kg-agent/curation/upper/pending.jsonl`、`lower/pending.jsonl`及机器清单 `resolution_log_index` 所列日志。

盘点前后比较**3721个既有文件**（1,008,593,597字节）的SHA256。范围包含全部当前共享知识包、Agent目录既有文件（排除.git、node_modules、build、__pycache__、.pytest_cache）及根AGENTS和两PDF。**0个非预期变化、0个缺失**。仅记录一项主线已授权的并行变化：主代理将已有 `docs/research/2026-10-22-rag-kg-migration.md` 更新为用户已确认的accepted状态；该文件不是本盘点改写。所有canonical DB、manifest、源PDF、查询代码、curation/evaluation与其他基线文件均未改变。逐文件哈希及授权例外的前后哈希保存在JSON `integrity`。

canonical graph SHA256：`3463d772e607c6e89104c17c02c6b3656cca766f444d226c011fb9d8a9017271`。

canonical manifest SHA256：`4eafc2500d74089d2b8a113598afb83470c4553d53748a5ca6207f614c238aac`。

本轮仅新增这份Markdown和对应JSON；未执行测试、构建、导入、重新抽取、PDF渲染或外部原博客核验。它是全量结构、字面证据和历史关联盘点，不能替代逐条语义判断。
