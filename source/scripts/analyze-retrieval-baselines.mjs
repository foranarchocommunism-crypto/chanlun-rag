import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';

assert.equal(process.argv.length, 4, 'Usage: node scripts/analyze-retrieval-baselines.mjs REPORT.json ANALYSIS.json');
const report = JSON.parse(readFileSync(resolve(process.argv[2]), 'utf8'));
const graph = new KnowledgeGraph(report.snapshot.snapshot_directory);
try {
  assert.equal(graph.metadata.graph_version, report.graph_version);
  const covered = new Set(graph.db.prepare(`SELECT DISTINCT e.passage_id FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'`).all().map(x => x.passage_id));
  const caseAnalysis = report.observations.map(item => {
    const missing = item.annotated_passage_ids.filter(id => !covered.has(id));
    const m = Object.fromEntries(Object.entries(item.variants).map(([name, value]) => [name, value.metrics[10]]));
    const categories = [];
    if (missing.length) categories.push('gold_partly_outside_reviewed_claim_evidence');
    if (!m.C_structured_lexical?.hit) {
      categories.push('structured_has_no_top10_annotated_hit');
      if (!missing.length) categories.push('structured_ranking_miss_with_covered_gold');
    }
    if (m.D_lexical_fusion?.recall < m.C_structured_lexical?.recall) categories.push('equal_rrf_reduces_recall_at10');
    if (m.D_lexical_fusion?.hit && !m.C_structured_lexical?.hit) categories.push('fusion_recovers_first_hit_at10');
    return { query_id: item.query_id, query_text: item.query_text, categories,
      annotated_gold_not_in_reviewed_evidence: missing.sort(),
      at10: Object.fromEntries(Object.entries(m).map(([name, value]) => [name, value && Object.fromEntries(['recall', 'hit', 'all_annotated_evidence_found'].map(f => [f, value[f]]))])) };
  });
  const counts = {};
  for (const item of caseAnalysis) for (const category of item.categories) counts[category] = (counts[category] ?? 0) + 1;
  const analysis = { graph_version: report.graph_version, cases: caseAnalysis.length, categories: counts,
    case_analysis: caseAnalysis, automatic_categories_only: true,
    limits: ['来源未被reviewed命题覆盖与排序漏召回分开；分类不证明其余返回段不相关。',
      'RRF退化/救回按当前已标注集合计算，不为每道题调权或用gold改写查询。'] };
  writeFileSync(resolve(process.argv[3]), JSON.stringify(analysis, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, cases: caseAnalysis.length, categories: counts }));
} finally { graph.close(); }
