// Fixed, previously exposed development set: evidence recall, not independent answer correctness.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { RetrievalService } from '../src/retrieval.mjs';
import { Reranker } from '../src/reranker.mjs';
import { sha256 } from '../src/corpus.mjs';
import { atomicJson } from './lib/durable-files.mjs';
const output = resolve('build/formal-release/graph-value-final'); mkdirSync(output, { recursive: true });
const casePath = resolve('evaluation/fixed-corpus/cases.jsonl');
const cases = readFileSync(casePath, 'utf8').trim().split('\n').map(JSON.parse);
const s = new RetrievalService();
const inputs = { cases: sha256(casePath), canonical: sha256(s.graph.path), index: sha256(resolve(s.paths.indexPath, 'manifest.json')),
  profile: sha256(s.paths.profilePath), graph_profile: sha256(s.graphConfigPath), evaluator: sha256('scripts/evaluate-fixed-corpus.mjs'),
  code: Object.fromEntries(readdirSync('src').filter(x => x.endsWith('.mjs')).map(n => [n, sha256(resolve('src', n))])) };
const progressPath = resolve(output, 'progress.json');
const progress = existsSync(progressPath) ? JSON.parse(readFileSync(progressPath, 'utf8')) : { inputs, rows: [] };
assert.deepEqual(progress.inputs, inputs, 'Evaluation resume requires identical inputs');
s.reranker = new Reranker(s.paths.modelPath, s.index.models.reranker);
const rawScore = s.reranker.score.bind(s.reranker), cache = new Map(); let computed = 0, reused = 0;
s.reranker.score = async (query, texts) => {
  const scores = [], truncated = []; let score_meaning;
  for (let i = 0; i < texts.length; i += 4) {
    const batch = texts.slice(i, i + 4), key = JSON.stringify([query, batch]); let r = cache.get(key);
    if (!r) { r = await rawScore(query, batch); cache.set(key, r); computed++; } else reused++;
    scores.push(...r.scores); truncated.push(...r.truncated); score_meaning = r.score_meaning;
  }
  return { scores, truncated, score_meaning };
};
const arms = { D: {}, T40: { profile: 'hybrid-rerank', rerankBudget: 40 }, T48: { profile: 'hybrid-rerank', rerankBudget: 48 },
  G1: { profile: 'hybrid-graph-v2-rerank', graphDepth: 1, rerankBudget: 48 }, G2: { profile: 'hybrid-graph-v2-rerank', graphDepth: 2, rerankBudget: 48 } };
try {
  for (const c of cases.slice(progress.rows.length)) {
    cache.clear(); const gold = [...new Set(c.expected_source_refs.map(x => x.passage_id))];
    const row = { id: c.query_id, query: c.query_text, arms: {} };
    for (const [name, options] of Object.entries(arms)) {
      const p = await s.retrieve({ query: c.query_text, limit: 20, contextBudget: 60000, ...options });
      const byId = new Map(p.data.reviewed.map(x => [x.id, x]));
      const evidence = [...new Set(p.runtime.primary_result_ids.flatMap(id => byId.get(id)?.evidence.map(e => e.passage_id) ?? []))];
      const hits = gold.filter(id => evidence.includes(id)).length;
      assert.ok(p.data.reviewed.every(x => x.review_status === 'reviewed' && x.evidence.length && x.evidence.every(e => e.claim_id === x.id)));
      row.arms[name] = { recall: hits / gold.length, complete: hits === gold.length, primary: p.runtime.primary_result_ids, evidence,
        graph_promoted: p.runtime.stages.graph.admission?.final_primary_ids ?? [],
        graph_only_promoted: (p.runtime.stages.graph.admission?.promoted ?? []).filter(x => x.kind === 'graph_only'),
        two_hop_selected: p.runtime.stages.graph.hop2_paths ?? 0,
        complete_two_hop_paths: p.data.relation_paths.filter(x => x.depth === 2 && x.evidence_chain_complete).length,
        actual_rerank_candidates: p.runtime.stages.rerank.candidates };
    }
    progress.rows.push(row); atomicJson(progressPath, progress);
    if (progress.rows.length % 10 === 0) console.log(JSON.stringify({ completed: progress.rows.length, total: cases.length }));
  }
  const mean = list => list.reduce((a, b) => a + b, 0) / list.length;
  const summary = Object.fromEntries(Object.keys(arms).map(name => [name, { recall: mean(progress.rows.map(r => r.arms[name].recall)),
    complete_fraction: mean(progress.rows.map(r => Number(r.arms[name].complete))),
    graph_promoted_queries: progress.rows.filter(r => r.arms[name].graph_promoted.length).length,
    two_hop_queries: progress.rows.filter(r => r.arms[name].two_hop_selected).length,
    complete_two_hop_queries: progress.rows.filter(r => r.arms[name].complete_two_hop_paths).length }]));
  const comparisons = Object.fromEntries(['D', 'G1', 'G2'].map(name => { const base = name === 'D' ? 'T40' : 'T48'; return [name, {
    against: base, improved: progress.rows.filter(r => r.arms[name].recall > r.arms[base].recall).map(r => r.id),
    regressed: progress.rows.filter(r => r.arms[name].recall < r.arms[base].recall).map(r => r.id),
    mean_delta: summary[name].recall - summary[base].recall }]; }));
  for (const [name, hash] of Object.entries(inputs.code)) assert.equal(sha256(resolve('src', name)), hash);
  const result = { scope: 'fixed exposed development corpus; not independent semantic or answer-quality acceptance', cases: cases.length,
    real_local_models: true, inputs, summary, comparisons,
    batch_reuse: { computed, reused, exact_ordered_batches_of_4: true, timings_not_performance_evidence: true },
    default_decision: 'Preserve established definition retrieval with bounded graph execution; new admission remains optional without a claim of overall quality gain',
    two_hop_policy: 'natural competition only; no dedicated channel or floor', completed: true };
  atomicJson(resolve(output, 'metrics.json'), result); console.log(JSON.stringify(result));
} finally { await s.close(); }
