// Prospective source-disjoint tests. Run before tuning; never rewrite a frozen file.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';

const output = resolve('evaluation/acceptance-v1');
assert.ok(!existsSync(output), 'Acceptance set already frozen; preserve it.');
const entries = [
  ['upper-l032-c-stage-chosen-thirty-level-follow-buy-sell-rhythm', '选定三十分钟为操作尺度后，顶底背驰出现时怎样保持交易节奏？', 'level_scope'],
  ['lower-l105-c-stage-jun17-2917-possible-second-center-2976-strength', '2008年6月17日，2917和2976分别用于判断什么？突破前者是否已确认第二中枢？', 'historical_condition'],
  ['lower-l104-c-stage-mar28-3499-and-five-fifteen-condition', '3月28日提到3499支撑时，对下周五分钟和十五分钟MACD提出哪些联合观察条件？', 'conditions'],
  ['lower-l062-inclusion-downward', '相邻K线互相包含且按向下方向处理时，合并后的最高和最低价格各取哪一个？', 'definition'],
  ['upper-l007-c-stage-fundamentals-as-other-beliefs', '第七课要求散户了解别人的基本面看法，与自己相信基本面有什么区别？', 'scope'],
  ['upper-l041-c-stage-apr2-shenzhen-second-line-sector-strength-historical-view', '2007年4月2日为什么让看不清上海指数的人参考深圳？二线板块被如何描述？', 'historical_source'],
  ['upper-l033-c-stage-unskilled-can-leave-wait-weekly-bottom-divergence', '盘整阶段技术不足的人可以怎样等待？作者提出的周线底背驰办法适用于什么人？', 'capability_condition'],
  ['lower-l100-c-stage-feb27-one-minute-type-up-or-consolidation', '2008年2月27日4331附近的反弹，哪些一分钟结构已经形成，盘整还是上涨是否已经确定？', 'completion_state'],
  ['upper-l017-c-stage-static-classification-dynamic-completion', '走势终完美如何把静态分类转成当下的动态分析？', 'cross_page'],
  ['lower-l073-c-stage-allocation-stable-rank-change-swap', '长期行业组合中企业排序没有变化时要换股吗？什么基本面变化才触发等市值替换？', 'exception'],
  ['upper-l025-c-stage-jan25-weekly-center-maximum-not-duration-guarantee', '2007年1月25日说最恶劣形成周线中枢，是已经确认必走周线调整且保证固定时长吗？', 'uncertainty'],
  ['upper-l052-c-stage-near-opposite-points-use-large-unless-skilled-exit-room', '大级别买卖点与反向小级别点很接近时应服从哪一层？小级别操作例外需要什么能力和空间？', 'exception'],
  ['upper-l037-c-stage-c-must-new-trend-high-or-low', '典型趋势背驰结构的c段，在整体上涨和整体下跌时分别必须达到怎样的新高新低条件？', 'direction'],
  ['upper-l040-c-stage-mar29-zero-cost-safe-negative-only-profit-author-strong-wording', '作者说成本为零才安全、零以下才是利润，应怎样保留这句话的作者主张身份？', 'author_claim'],
  ['upper-l026-c-stage-319-last-exit-not-from-chart-self-report', '作者自述319最后一天平仓是依据图形还是此前327交易取消的教训？这段经历是否独立核实？', 'attribution'],
  ['upper-l031-c-stage-capacity-thirty-float-versus-minute-ten-day-volume', '第三十一课里流通盘千分之五和十天均量百分之一对应哪两种操作容量经验？能否当成实测通用标准？', 'qualitative_rule'],
  ['upper-l030-c-stage-absolute-convergence-only-one-participant-boundary', '绝对趋同示例中只剩一个参与者与还有别人持有一股有什么区别？一股是不是安全交易阈值？', 'boundary'],
  ['upper-l053-c-stage-literal-bing-chuji-versus-no-same-level-first-point-unresolved', '第五十三课关于小级别背驰并触及第一类点与没有本级第一类点的文字张力，当前能否唯一校正？', 'source_tension'],
  ['upper-l047-c-stage-actual-1443-tick-divergence-morning-star-large-rebound-case', '第四十七课14点43分背驰与早晨之星案例中的百分之百保证，是本项目测得的成功率吗？', 'empirical_limit'],
  ['upper-l028-c-stage-below-one-minute-histogram-special-comparison', '只有一分钟图又想辅助判断更低走势时，第二十八课怎样比较MACD柱组？是否真的观察了秒级图？', 'reference_frame'],
  ['upper-l027-c-stage-not-daily-buy-point-forming-five-minute-partial', '第二十七课说五分钟买点正在形成时，哪些资金和股票能部分介入？这是否已确认所有人都应买入？', 'forming_vs_confirmed'],
  ['upper-l056-c-stage-rebound-participation-level-stock-cost-futures-hypothetical-T0-literal', '第五十六课B盘背回补例子里，操作级别、股票成本和T+0原字应怎样保留？可以静默改成T+1吗？', 'literal_source'],
  ['upper-l061-c-stage-jun22-46-87-thirty-center4067-4192-third-leg-unfinished', '第六十一课说46到87构成三十分中枢4067至4192时，第三段已经完成了吗？', 'definition_boundary'],
  ['lower-l103-c-stage-mar21-daily-3941-not-sixty-3780', '2008年3月21日3941是哪个图表周期的分型上沿，站住后与原六十分钟中枢有什么关系？', 'chart_vs_level'],
];
const graph = new KnowledgeGraph(resolve('../shared-knowledge/v0.1.0'));
try {
  const snapshot = JSON.parse(readFileSync('build/final-kb-retrieval-307029129712/snapshot.json', 'utf8'));
  const devFile = resolve('build/final-kb-retrieval-307029129712/cases.jsonl');
  const development = readFileSync(devFile, 'utf8').trim().split('\n').map(JSON.parse);
  assert.equal(development.length, 240);
  const used = new Set(development.flatMap(c => c.expected_source_refs.map(r => r.passage_id)));
  const cases = entries.map(([id, query, stratum], i) => {
    const claim = graph.getClaim(id);
    assert.ok(claim, id);
    assert.ok(claim.evidence.every(e => !used.has(e.passage_id)), `Source overlap: ${id}`);
    return { query_id: `acceptance-v1-${String(i + 1).padStart(2, '0')}`, query_text: query, mode: 'knowledge', stratum,
      required_claim_ids: [id], required_evidence_ids: claim.evidence.map(e => e.id),
      expected_source_refs: claim.evidence.map(e => ({ passage_id: e.passage_id, role: e.role, speaker: e.speaker, document_id: e.document_id, pdf_page: e.pdf_page })),
      acceptable_conditions: claim.conditions, acceptable_exceptions: claim.exceptions,
      expected_ambiguity: claim.ambiguity_status, review_note_sha256: createHash('sha256').update(claim.review_note).digest('hex'),
      annotation: { author: 'Codex implementation agent, source-backed prospective annotation', human_reviewed: false, independently_semantically_reviewed: false },
    };
  });
  const body = cases.map(c => JSON.stringify(c)).join('\n') + '\n';
  const manifest = { schema: 'chan-kg-acceptance/1', created_at: new Date().toISOString(), graph_version: graph.metadata.graph_version,
    frozen_before_tuning: true, cases: cases.length, development_cases: development.length, shared_gold_passages_with_development: 0,
    data_split_independent_of_development: true, annotator_independent_of_implementation: false, human_gold: false,
    annotation_limits: 'Separate prospective source-disjoint test, not an independent human gold or blind semantic review. Questions and annotations authored before runtime tuning by the implementation agent.',
    cases_sha256: createHash('sha256').update(body).digest('hex'), development_snapshot: snapshot,
    strata: Object.fromEntries([...new Set(cases.map(c => c.stratum))].map(s => [s, cases.filter(c => c.stratum === s).length])),
    evaluation: { ks: [10, 20], compare: ['structured_lexical', 'dense', 'hybrid', 'hybrid_graph', 'hybrid_graph_rerank'],
      same_final_context_budget: true, input: 'Unmodified query_text only; expected IDs and text are never passed to retrieval.',
      integrity_hard_gate_errors: 0, generated_answers_scored_separately: true,
      use_after_profile_freeze: true, reuse_after_tuning: 'Mark exposed set as development and freeze fresh source-disjoint cases before independent revalidation.' } };
  mkdirSync(output, { recursive: true });
  writeFileSync(resolve(output, 'cases.jsonl'), body);
  writeFileSync(resolve(output, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log(JSON.stringify({ output, cases: cases.length, sha256: manifest.cases_sha256, source_overlap: 0 }));
} finally { graph.close(); }
