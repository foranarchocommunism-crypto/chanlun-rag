// Development only. Prospective acceptance data is never loaded by this runner.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { RetrievalService } from '../src/retrieval.mjs';
import { fuse } from '../src/lexical.mjs';
import { expandGraph } from '../src/graph-expansion.mjs';
import { rankedMetrics, uniquePassages } from './lib/retrieval-baselines.mjs';
import { sha256 } from '../src/corpus.mjs';
const s = new RetrievalService();
const dbHash = sha256(s.graph.path);
assert.ok(s.dense, 'Vector construction must finish before development evaluation.');
try {
  const cases = readFileSync('build/final-kb-retrieval-307029129712/cases.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
  const evidence = new Map([...s.corpus.claims.values()].filter(c => c.review_status === 'reviewed').map(c => [c.id, [...new Set((s.corpus.evidenceByClaim.get(c.id) ?? []).map(e => e.passage_id))].sort()]));
  const observations = [];
  for (const item of cases) {
    const t = performance.now(), request = { query: item.query_text, mode: 'knowledge', limit: 20, candidateBudget: 100, graphDepth: 1, graphBudget: 20 };
    const lexical = s.lexicalSearch(request);
    const dense = await s.dense.search(item.query_text, { mode: 'knowledge', limit: 100, accept: row => row.review_status === 'reviewed' });
    const variants = { lexical, dense: dense.results };
    for (const weight of [.1, .25, .5, 1, 2]) variants[`hybrid_w${weight}`] = fuse([{ name: 'lexical', weight: 1, results: lexical }, { name: 'dense', weight, results: dense.results }], 100);
    const base = variants.hybrid_w1;
    const graph = expandGraph(s.corpus, base, request, c => s.eligible(c, request));
    const seen = new Set();
    variants.hybrid_w1_graph = [...base.slice(0, 5), ...graph.additions.slice(0, 5), ...base.slice(5), ...graph.additions.slice(5)]
      .filter(x => { if (seen.has(x.id)) return false; seen.add(x.id); return true; }).slice(0, 100);
    const relevant = [...new Set(item.expected_source_refs.map(e => e.passage_id))];
    const results = Object.fromEntries(Object.entries(variants).map(([name, rank]) => {
      const passages = uniquePassages(rank, evidence, 100);
      return [name, { at10: rankedMetrics(passages, relevant, 10), at20: rankedMetrics(passages, relevant, 20), top20: passages.slice(0, 20) }];
    }));
    observations.push({ query_id: item.query_id, query_text: item.query_text, query_type: item.query_type, variants: results,
      raw_lexical: lexical, raw_dense: dense.results, graph_additions: graph.additions, graph_paths: graph.paths, elapsed_ms: performance.now() - t });
    if (observations.length % 20 === 0) console.log(JSON.stringify({ evaluated: observations.length, total: cases.length }));
  }
  const names = Object.keys(observations[0].variants);
  const aggregates = Object.fromEntries(names.map(name => [name, Object.fromEntries(['at10', 'at20'].map(k => [k,
    Object.fromEntries(['recall', 'ndcg_binary', 'all_annotated_evidence_found'].map(field => [field, observations.reduce((sum, x) => sum + x.variants[name][k][field], 0) / observations.length]))]))]));
  assert.equal(sha256(s.graph.path), dbHash);
  const result = { created_at: new Date().toISOString(), graph_version: s.graph.metadata.graph_version, development_cases: cases.length,
    prospective_acceptance_run: false, canonical_unchanged: true, comparison: 'Same source corpus, unique passage IDs, final K10/20 and at most 100 intermediate candidates. No packet/issue supplementation in these candidate ranking metrics.',
    model: s.index.models.embedding, aggregates, observations };
  writeFileSync('../validation-runs/agent-implementation-20261022/m3-hybrid-development.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ aggregates }));
} finally { await s.close(); }
