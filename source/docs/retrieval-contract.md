# 检索实现合同 1.0

当前固定交付范围见 fixed-release.md；实际验证见发布仓库中的本版回执。canonical schema 不变，`retrieval-index.schema.sql` 仅用于独立派生库。

请求以 `contracts/retrieval-request.schema.json` 为准，三入口共用验证。返回以 `contracts/evidence-packet.schema.json` 为准。字符预算计算证据数据对象的 JSON Unicode 码点数；返回运行元数据不计入该预算，单独报告。条件、例外、完整引文和解释组按完整单元保留，放不下则整个延期，返回稳定 ID 续取。

knowledge 只返回 reviewed 命题和支持关系，包含显式歧义；research 显式增加 pending，分区返回；source 保留所有原文角色并标记语义复核未断言。evidence 通过所属 claim 继承读取身份，父段落语境不继承语义复核。

派生库、模型和策略各自固定哈希。启动核验 canonical 源库、manifest、策略与投影文件；向量和重排 profile 另核模型文件和推理配置。缺失／损坏／陈旧默认错误；只有 `allowDegraded=true` 可使用仍有效的词法路径并列出实际通道。

图路径保存原关系方向、实际遍历方向、类型和支持 claim/evidence；关联发现不构成反向蕴含。研究解释有独立身份与版本；候选覆盖映射仅描述字符范围，不代表语义同义或替代。

错误码包括 INVALID_REQUEST、UNKNOWN_ID、INDEX_MISSING、INDEX_STALE、INDEX_CORRUPT、MODEL_MISSING、MODEL_INVALID、RESOURCE_ERROR、RESOURCE_BUSY、QUEUE_TIMEOUT。CLI stdout 为 JSON，stderr 为日志；MCP stdio stdout 仅用于协议。

M0 验收集是与既有 240 道开发题无 gold 段落重叠的前瞻冻结集，实施者也是标注者，尚无人类或独立语义复核。它支持数据隔离的验证，不能据此声称独立人工金标准；公开八例及门槛测试另行统计。独立测试仅在 profile 冻结后运行，若据结果调参则更换复验集。

运行参数和内容指纹始终返回；trace=true 返回有候选数量上限的各阶段排名及原始命中理由。固定快照拒绝 WAL 和写入日志，保持只读事务。INDEX_STALE、INDEX_CORRUPT 与 canonical 损坏始终失败，不受 allowDegraded 放宽。
