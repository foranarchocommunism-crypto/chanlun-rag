import assert from 'node:assert/strict';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';
import { readCorpus } from '../src/corpus.mjs';
const path = resolve('policies/ambiguity-issues.json');
assert.ok(!existsSync(path), 'Research records already exist; revise with history, not overwrite.');
const specs = [
  ['construction-entry', 'source_explicit', '作者明确区分最初最低级别入口与分型构造入口。此项是防止误报矛盾的对照，不证明所有入口全域等价。',
    ['lower-l075-c-stage-one-price-limit-two-constructions', 'upper-l017-minimum-level-center', 'lower-l080-c-stage-early-pure-center-not-overturned'], [], [], ['两套入口对任意走势的映射或等价证明'], 'rule_conditions_explicit'],
  ['trend-completion', 'hypothesis', '形成中的发展信号与已完成类型分类可能是两个观察状态；仍未证明两定义等价，也未见本段明确修订旧定义。',
    ['lower-l107-c-stage-uptrend-formation-wording-not-completed-type', 'upper-l017-trend-definition'],
    ['以形成过程和完成类型的对象差异解释两处表述'], ['二者全域兼容尚未证明'], ['从信号到完成类型的完整转换条件'], 'qualitative_guidance'],
  ['qualified-answer', 'context_supported', '复合问题后的基本认可须保留“基本上”和级别限制，不能改写成三个当且仅当规则。',
    ['upper-l041-c-stage-completion-question-basically-yes-qualified-not-equivalence'], [], [], ['各对象逐一成立的必要与充分条件'], 'qualitative_guidance'],
  ['numbering-tension', 'unresolved', '第49课分类编号与后续买点指代存在张力；可能的校号只是研究假说，需页面及来源核查。',
    ['upper-l049-c-stage-near-new-buy-entry-but-completed-submove-top-divergence-wait-number-tension'], [], ['可能把第三种写成第二种，尚未确认'], ['错误产生环节和唯一正确编号'], 'parameters_unspecified'],
  ['connection-level-scope', 'unresolved', '第54课分解语境与第18课一般连接规则的范围可能不同，尚不能证明统一，不按时间较晚自动覆盖。',
    ['upper-l054-c-stage-same-level-centers-must-have-sublevel-connection-in-this-decomposition', 'upper-l018-center-theorem-one', 'upper-l018-c-stage-center-connection-not-necessarily-trend'],
    ['特定分解与一般趋势连接可能适用不同范围'], ['两范围完全分离尚未得到明确文字证明'], ['必须次级与允许更低级之间的完整适用边界'], 'qualitative_guidance'],
  ['zn-cooperation', 'unresolved', '次级趋势、Zn配合、中枢位置和后续完成区间有结构信息；相应配合的唯一数值判据仍未给出。',
    ['lower-l092-c-stage-secondary-trend-last-center-condition', 'lower-l092-c-stage-axis-and-secondary-midpoints', 'lower-l092-c-stage-boundary-cross-not-sufficient'],
    [], [], ['Zn配合的阈值、连续次数、容差和未完成区间采样规则'], 'parameters_unspecified'],
  ['candidate-overlap', 'source_explicit', '整段自动候选与细分reviewed命题共享出处，不等于两种相反理论；共享出处也不足以自动判定语义完全覆盖。',
    ['candidate-06fee67b46cd9475', 'upper-l017-trend-definition'], [], [], ['候选全部含义是否被细分命题覆盖仍需逐项判定'], 'not_an_independent_proposition'],
  ['cross-page-continuation', 'context_supported', '第77课“当然线／段A”须跨页连读，并保留A、B、C只是确认前假设称呼的限制。此记录不证明图形和数学论证。',
    ['candidate-09120e714f8fe0f3', 'candidate-a0ade5e49c0ea61b'], [], [], ['图80—83和第二种情况论证的独立核验'], 'not_an_independent_proposition'],
];
const graph = new KnowledgeGraph(resolve('../shared-knowledge/v0.1.0'));
try {
  const corpus = readCorpus(graph);
  const issues = specs.map(([id, status, text, ids, contextConditions, assumptions, unknown, formalization]) => {
    ids.forEach(id => assert.ok(corpus.claims.has(id), id));
    const evidenceIds = [...new Set(ids.flatMap(id => (corpus.evidenceByClaim.get(id) ?? []).map(e => e.id)))];
    const interpretation = { interpretation_id: `interpretation-${id}-v1`, original_claim_ids: ids, source_evidence_ids: evidenceIds,
      proposed_by: 'Codex source-research synthesis, 2026-10-22; not author wording', interpretation_text: text,
      explicit_conditions: [...new Set(ids.flatMap(id => corpus.claims.get(id).conditions))], context_supported_conditions: contextConditions,
      assumed_conditions: assumptions, unknown_conditions: unknown, support_evidence_ids: evidenceIds,
      opposing_evidence_ids: [], unresolved_questions: unknown, status, formalization_status: formalization,
      graph_version: graph.metadata.graph_version, visual_verification: 'not_performed_in_this_research',
      resolution_basis: 'Eight text-grounded cases; see docs/research/2026-10-22-ambiguity-source-cases.md' };
    return { issue_id: `issue-${id}`, title: id, trigger_claim_ids: ids, related_claim_ids: ids,
      resolution_status: status, evidence_balance: 'insufficient',
      evidence_balance_note: 'Not a formal contradiction verdict; source differences and comparison conditions remain explicit.',
      interpretations: [interpretation] };
  });
  mkdirSync(resolve('policies'), { recursive: true });
  const policy = { policy_version: '1.0.0', graph_version: graph.metadata.graph_version, created_at: new Date().toISOString(),
    source: 'Approved plan section 6 and text-grounded research', semantic_review_scope: 'Research records, no canonical promotion', issues };
  writeFileSync(path, JSON.stringify(policy, null, 2) + '\n');
  console.log(JSON.stringify({ path, issues: issues.length }));
} finally { graph.close(); }
