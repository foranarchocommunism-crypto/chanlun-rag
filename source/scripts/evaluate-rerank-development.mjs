import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { RetrievalService } from '../src/retrieval.mjs';
import { Reranker } from '../src/reranker.mjs';
import { fuse } from '../src/lexical.mjs';
import { expandGraph } from '../src/graph-expansion.mjs';
import { rankedMetrics, uniquePassages } from './lib/retrieval-baselines.mjs';
const s = new RetrievalService(), reranker = new Reranker(s.paths.modelPath);
const outputPath = '../validation-runs/agent-implementation-20261022/m4-rerank-development.json';
const progressPath = '../validation-runs/agent-implementation-20261022/m4-rerank-progress.json';
assert.ok(!existsSync(outputPath), 'Already evaluated; preserve results.');
try {
  const input = JSON.parse(readFileSync('../validation-runs/agent-implementation-20261022/m3-hybrid-development.json', 'utf8'));
  const gold = new Map(readFileSync('build/final-kb-retrieval-307029129712/cases.jsonl', 'utf8').trim().split('\n').map(JSON.parse).map(c => [c.query_id, [...new Set(c.expected_source_refs.map(e => e.passage_id))]]));
  const evidence = new Map([...s.corpus.claims.values()].filter(c => c.review_status === 'reviewed').map(c => [c.id, [...new Set((s.corpus.evidenceByClaim.get(c.id) ?? []).map(e => e.passage_id))].sort()]));
  const observations = existsSync(progressPath) ? JSON.parse(readFileSync(progressPath, 'utf8')).observations : [];
  const initial = observations.length;
  for (const item of input.observations.slice(initial)) {
    const channels = [{ name: 'lexical', weight: 1, results: item.raw_lexical }, { name: 'dense', weight: .5, results: item.raw_dense }];
    const base = fuse(channels, 100);
    const graph = expandGraph(s.corpus, base, { query: item.query_text, mode: 'knowledge', limit: 20, graphDepth: 1, graphBudget: 20 }, c => c.review_status === 'reviewed');
    const graphSeeds = [...new Set(graph.paths.map(p => p.support_claim_id))].map(id => ({ id, score: 0 }));
    const rank = fuse([...channels, { name: 'graph', weight: .1, results: graphSeeds }], 100);
    const documents = rank.slice(0, 40).map(r => { const c = s.corpus.claims.get(r.id); return [c.text, ...c.conditions, ...c.exceptions].join(' '); });
    const start = performance.now();
    const scored = await reranker.score(item.query_text, documents);
    const variants = { graph_no_rerank: rank };
    for (const budget of [20, 40]) variants[`rerank${budget}`] = [...rank.slice(0, budget).map((r, i) => ({ ...r, rerank_score: scored.scores[i] }))
      .sort((a, b) => b.rerank_score - a.rerank_score || a.id.localeCompare(b.id)), ...rank.slice(budget)];
    const metrics = Object.fromEntries(Object.entries(variants).map(([name, ranked]) => { const passages = uniquePassages(ranked, evidence, 100); return [name, { at10: rankedMetrics(passages, gold.get(item.query_id), 10), at20: rankedMetrics(passages, gold.get(item.query_id), 20), top20: passages.slice(0, 20) }]; }));
    observations.push({ query_id: item.query_id, elapsed_ms_rerank40: performance.now() - start, scores: scored.scores, document_ids: rank.slice(0, 40).map(r => r.id), truncated_inputs: scored.truncated, variants: metrics });
    writeFileSync(progressPath, JSON.stringify({ model_manifest_sha256: reranker.manifestSha256, observations }, null, 2));
    if (observations.length % 10 === 0) console.log(JSON.stringify({ scored_cases: observations.length, total: input.observations.length, elapsed_ms_latest: observations.at(-1).elapsed_ms_rerank40, rss_bytes: process.memoryUsage().rss }));
  }
  const times = observations.map(o => o.elapsed_ms_rerank40).sort((a, b) => a - b);
  const aggregates = Object.fromEntries(['graph_no_rerank', 'rerank20', 'rerank40'].map(name => [name, Object.fromEntries(['at10', 'at20'].map(k => [k,
    Object.fromEntries(['recall', 'ndcg_binary', 'all_annotated_evidence_found'].map(field => [field, observations.reduce((sum, x) => sum + x.variants[name][k][field], 0) / observations.length]))]))]));
  const result = { created_at: new Date().toISOString(), development_cases: observations.length, model_manifest_sha256: reranker.manifestSha256,
    prospective_acceptance_run: false, elapsed_ms_rerank40: { p50: times[Math.floor(times.length * .5)], p95: times[Math.floor(times.length * .95)] },
    peak_rss_bytes: process.resourceUsage().maxRSS * 1024, aggregates, observations };
  writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify({ ...result, observations: undefined }));
} finally { await reranker.close(); await s.close(); }
