// Compare real question strings on a frozen corpus; never execute saved gold plans.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';
import { LexicalIndex, rankedMetrics, reciprocalRankFusion, uniquePassages } from './lib/retrieval-baselines.mjs';

const args = process.argv.slice(2);
assert.equal(args.length, 2, 'Usage: node scripts/evaluate-retrieval-baselines.mjs SNAPSHOT_DIRECTORY REPORT.json');
const [snapshotDir, reportFile] = args.map(x => resolve(x));
const readJson = name => JSON.parse(readFileSync(resolve(snapshotDir, name), 'utf8'));
const sha = file => createHash('sha256').update(readFileSync(file)).digest('hex');
const pinned = readJson('snapshot.json');
const before = { database: sha(resolve(snapshotDir, 'graph.sqlite')), manifest: sha(resolve(snapshotDir, 'manifest.json')), cases: sha(resolve(snapshotDir, 'cases.jsonl')) };
assert.equal(before.database, pinned.database_sha256);
assert.equal(before.manifest, pinned.manifest_sha256);
assert.equal(before.cases, pinned.cases_sha256);
const cases = readFileSync(resolve(snapshotDir, 'cases.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
assert.equal(cases.length, pinned.cases);
const graph = new KnowledgeGraph(snapshotDir);
const json = value => JSON.parse(value);
const CANDIDATE_BUDGET = 100, KS = [5, 10, 20];

try {
  assert.equal(graph.metadata.graph_version, pinned.graph_version);
  const setupStart = performance.now();
  const passages = graph.db.prepare(`SELECT p.id,p.text,p.document_id,p.pdf_page,p.role,p.speaker,p.published_at,pg.printed_page
    FROM passages p JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page ORDER BY p.id`).all();
  const sourceById = new Map(passages.map(p => [p.id, p]));
  const conceptText = new Map(graph.db.prepare('SELECT id,label,aliases FROM concepts ORDER BY id').all()
    .map(c => [c.id, [c.label, ...json(c.aliases)].join(' ')]));
  const claims = graph.db.prepare("SELECT id,text,conditions,exceptions,concept_ids FROM claims WHERE review_status='reviewed' ORDER BY id").all();
  const evidenceByClaim = new Map();
  for (const e of graph.db.prepare(`SELECT e.claim_id,e.passage_id FROM evidence e JOIN claims c ON c.id=e.claim_id
    WHERE c.review_status='reviewed' ORDER BY e.claim_id,e.passage_id,e.id`).all()) {
    if (!evidenceByClaim.has(e.claim_id)) evidenceByClaim.set(e.claim_id, []);
    evidenceByClaim.get(e.claim_id).push(e.passage_id);
  }
  const sourceIndex = new LexicalIndex(passages);
  const structuredIndex = new LexicalIndex(claims.map(c => ({ id: c.id,
    text: [c.text, ...json(c.conditions), ...json(c.exceptions), ...json(c.concept_ids).map(id => conceptText.get(id) ?? '')].join(' ') })));
  const setupMs = performance.now() - setupStart;
  const observations = [];
  for (const item of cases) {
    assert.equal(item.coverage_status, 'executable');
    const gold = [...new Set(item.expected_source_refs.map(ref => ref.passage_id))];
    const goldIdentityMismatches = [];
    for (const ref of item.expected_source_refs) {
      const p = sourceById.get(ref.passage_id);
      for (const field of ['document_id', 'pdf_page', 'printed_page', 'role', 'speaker', 'published_at']) {
        if (Object.hasOwn(ref, field) && p?.[field] !== ref[field]) goldIdentityMismatches.push({ passage_id: ref.passage_id, field, expected: ref[field], actual: p?.[field] ?? null });
      }
    }
    // Query input is exactly query_text, never required IDs, expected quotes, or retrieval_plan.
    const timings = {};
    const timed = (name, work) => { const t = performance.now(); const value = work(); timings[name] = performance.now() - t; return value; };
    const raw = timed('A_source_lexical', () => sourceIndex.search(item.query_text, CANDIDATE_BUDGET));
    const structured = timed('C_structured_lexical', () => uniquePassages(structuredIndex.search(item.query_text, CANDIDATE_BUDGET), evidenceByClaim, CANDIDATE_BUDGET));
    // Fusion has the same 100 passage candidate slots: 50 from each channel.
    const fusionStart = performance.now();
    const fusion = reciprocalRankFusion([raw.slice(0, 50), structured.slice(0, 50)], CANDIDATE_BUDGET);
    const fusionOnlyMs = performance.now() - fusionStart;
    // Both channels' measured costs are included, not only the cheap merge.
    timings.D_lexical_fusion = timings.A_source_lexical + timings.C_structured_lexical + fusionOnlyMs;
    const production = timed('production_search_control', () => {
      const result = graph.query('search', { query: item.query_text, limit: CANDIDATE_BUDGET });
      return uniquePassages(result.data.results.map(c => ({ id: c.id, score: null })), evidenceByClaim, CANDIDATE_BUDGET);
    });
    const ranked = { A_source_lexical: raw, C_structured_lexical: structured, D_lexical_fusion: fusion, production_search_control: production };
    observations.push({ query_id: item.query_id, query_text: item.query_text, query_type: item.query_type,
      gold_created_graph_version: item.graph_version, annotated_passage_ids: gold,
      gold_identity_mismatches: goldIdentityMismatches, eligible_for_rank_metrics: gold.length > 0 && !goldIdentityMismatches.length,
      variants: Object.fromEntries(Object.entries(ranked).map(([name, list]) => [name, {
        elapsed_ms: timings[name], candidate_passages: list.length, top20: list.slice(0, 20),
        metrics: Object.fromEntries(KS.map(k => [k, rankedMetrics(list, gold, k)])),
      }])), generated_answer_scored: false });
  }
  const eligible = observations.filter(x => x.eligible_for_rank_metrics);
  const variants = ['A_source_lexical', 'C_structured_lexical', 'D_lexical_fusion', 'production_search_control'];
  const metricFields = ['recall', 'annotated_precision_lower_bound', 'reciprocal_rank', 'ndcg_binary', 'hit', 'all_annotated_evidence_found'];
  const mean = xs => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
  const aggregates = Object.fromEntries(variants.map(name => {
    const times = observations.map(x => x.variants[name].elapsed_ms).sort((a, b) => a - b);
    return [name, { evaluated_cases: eligible.length,
      at_k: Object.fromEntries(KS.map(k => [k, Object.fromEntries(metricFields.map(f => [f, mean(eligible.map(x => x.variants[name].metrics[k][f]))]))])),
      elapsed_ms: { mean: mean(times), p50: times[Math.floor((times.length - 1) * .5)], p95: times[Math.floor((times.length - 1) * .95)] },
      per_query_candidate_budget: CANDIDATE_BUDGET }];
  }));
  const after = { database: sha(resolve(snapshotDir, 'graph.sqlite')), manifest: sha(resolve(snapshotDir, 'manifest.json')), cases: sha(resolve(snapshotDir, 'cases.jsonl')) };
  assert.deepEqual(after, before);
  const report = { stage: 'G-retrieval-baselines', created_at: new Date().toISOString(), graph_version: graph.metadata.graph_version,
    snapshot: pinned, implementation_sha256: { runner: sha(new URL(import.meta.url)), algorithms: sha(new URL('./lib/retrieval-baselines.mjs', import.meta.url)) },
    executable_cases: cases.length, eligible_rank_cases: eligible.length, target_cases: 240,
    source_passages: passages.length, reviewed_claims: claims.length,
    query_input: 'Unmodified query_text only; no saved retrieval_plan, gold IDs, expected evidence text, or per-case rewriting.',
    comparison_unit: 'Unique source passage ID; claims expanded to evidence passages in passage-ID order, then deduplicated.',
    candidate_budget: { A: 100, C: 100, D: { source_passage_slots: 50, structured_passage_slots: 50, total: 100 }, production_control: 100,
      note: 'Equal returned candidate slots, not equal CPU cost. C examines at most 100 ranked claims before passage expansion. Fusion computes both channels; full channel timings are charged.' },
    baselines: {
      A_source_lexical: { status: 'run', implementation: 'Raw fixed-corpus paragraphs; Chinese 2/3-grams and ASCII terms; BM25 length/IDF weighting with binary term frequency. All source roles retained.' },
      B_vector: { status: 'not_implemented', run: false, metrics: null, reason: 'No embedding model, vector index, or vector infrastructure exists in this package. No fabricated comparison.' },
      C_structured_lexical: { status: 'run', implementation: 'Same tokenizer/scoring; reviewed claim text, conditions, exceptions, linked concept labels and verified aliases. No relation expansion or source text in scoring.' },
      D_lexical_fusion: { status: 'run', implementation: 'Evaluation-only reciprocal rank fusion (constant 60) of A and C; no vector component or production search change.' },
      production_search_control: { status: 'run', implementation: 'Current KnowledgeGraph.search on the complete question; native ranking, reviewed defaults, same snapshot.' },
    }, indexing_and_load_ms: setupMs, aggregates, observations,
    gold_review_status: 'model_reviewed_development', human_gold_reviewed: false, independent_test_set: false,
    generated_answers_evaluated: false, generated_model_token_cost: null,
    snapshot_and_gold_unchanged: true, live_database_written: false,
    limits: ['开发题与整理知识由同模型形成，无独立留出集或人工金标准；不得据此宣称泛化质量。',
      'gold是已标注证据子集，未标注结果不自动判不相关；Precision与nDCG仅对当前标注集合计算。',
      '所报告MRR为MRR@K；返回唯一段落排序不能证明多跳路径、语义蕴含、条件保留或回答忠实度。',
      '结构化集合限已复核知识，原文集合涵盖全部907页。覆盖不足和算法漏召回须逐案分析，不能全部归为算法失败。',
      '融合是离线评测实现，不等同现有CLI或Windows应用已经具备融合自然问题检索能力。',
      '单次本机热缓存运行，包含分词/检索/证据段落展开；索引准备单列，未做冷启动、重复测速或显著性检验。',
      '日期字段仅在原题标注存在时核对；当前gold普遍缺少published_at，未因此声称日期归属全量通过。',
      '未生成或评分回答，未评测反幻觉/冲突处理/视觉位置或Windows离线交互；未完成项目完整验收。'] };
  writeFileSync(reportFile, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ report: reportFile, graph_version: report.graph_version, cases: cases.length, eligible: eligible.length,
    mismatched_cases: observations.filter(x => x.gold_identity_mismatches.length).map(x => x.query_id), aggregates }, null, 2));
} finally { graph.close(); }
