import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { RetrievalService } from '../src/retrieval.mjs';
import { fuse } from '../src/lexical.mjs';
import { expandGraph } from '../src/graph-expansion.mjs';
import { rankedMetrics, uniquePassages } from './lib/retrieval-baselines.mjs';
const s = new RetrievalService();
try {
  const previous = JSON.parse(readFileSync('../validation-runs/agent-implementation-20261022/m3-hybrid-development.json', 'utf8'));
  const gold = new Map(readFileSync('build/final-kb-retrieval-307029129712/cases.jsonl', 'utf8').trim().split('\n').map(JSON.parse).map(c => [c.query_id, [...new Set(c.expected_source_refs.map(e => e.passage_id))]]));
  const evidence = new Map([...s.corpus.claims.values()].filter(c => c.review_status === 'reviewed').map(c => [c.id, [...new Set((s.corpus.evidenceByClaim.get(c.id) ?? []).map(e => e.passage_id))].sort()]));
  const observations = previous.observations.map(item => {
    const baseChannels = [{ name: 'lexical', weight: 1, results: item.raw_lexical }, { name: 'dense', weight: .5, results: item.raw_dense }];
    const base = fuse(baseChannels, 100);
    const variants = { hybrid: base };
    for (const depth of [1, 2]) {
      const graph = expandGraph(s.corpus, base, { query: item.query_text, mode: 'knowledge', limit: 20, graphDepth: depth, graphBudget: 20 }, c => c.review_status === 'reviewed');
      for (const weight of [.05, .1, .25]) {
        const seen = new Set();
        const results = graph.paths.filter(p => { if (seen.has(p.support_claim_id)) return false; seen.add(p.support_claim_id); return true; }).map(p => ({ id: p.support_claim_id, score: 0 }));
        variants[`depth${depth}_weight${weight}`] = fuse([...baseChannels, { name: 'graph', weight, results }], 100);
      }
    }
    const metrics = Object.fromEntries(Object.entries(variants).map(([name, rank]) => { const passages = uniquePassages(rank, evidence, 100); return [name, { at10: rankedMetrics(passages, gold.get(item.query_id), 10), at20: rankedMetrics(passages, gold.get(item.query_id), 20) }]; }));
    return { query_id: item.query_id, variants: metrics };
  });
  const aggregates = Object.fromEntries(Object.keys(observations[0].variants).map(name => [name, {
    recall10: observations.reduce((a, o) => a + o.variants[name].at10.recall, 0) / observations.length,
    recall20: observations.reduce((a, o) => a + o.variants[name].at20.recall, 0) / observations.length,
    groups20: observations.reduce((a, o) => a + o.variants[name].at20.all_annotated_evidence_found, 0) / observations.length,
    improved20: observations.filter(o => o.variants[name].at20.recall > o.variants.hybrid.at20.recall).length,
    regressed20: observations.filter(o => o.variants[name].at20.recall < o.variants.hybrid.at20.recall).length,
    changed_cases: observations.filter(o => o.variants[name].at20.recall !== o.variants.hybrid.at20.recall).map(o => ({ id: o.query_id, before: o.variants.hybrid.at20.recall, after: o.variants[name].at20.recall })) }]));
  const output = { created_at: new Date().toISOString(), development_cases: observations.length, prospective_acceptance_run: false,
    scope: 'Small declared graph-depth/weight grid on cached development rankings; unique source evidence metrics, no test tuning.', aggregates, observations };
  writeFileSync('../validation-runs/agent-implementation-20261022/m4-graph-development.json', JSON.stringify(output, null, 2) + '\n');
  console.log(JSON.stringify(aggregates));
} finally { await s.close(); }
