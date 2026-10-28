// Evaluate the real API packet, not an approximate replay. Never reads held-out cases.
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { RetrievalService } from '../src/retrieval.mjs';
import { rankedMetrics } from './lib/retrieval-baselines.mjs';
import { sha256 } from '../src/corpus.mjs';
const service = new RetrievalService();
const path = '../validation-runs/agent-implementation-20261022/m4-production-development.json';
const progress = '../validation-runs/agent-implementation-20261022/m4-production-progress.json';
assert.ok(!existsSync(path), 'Preserve prior results; use a new run ID after code changes.');
const inputs = { database: sha256(service.graph.path), profile: sha256(service.paths.profilePath),
  source: Object.fromEntries(['retrieval', 'corpus', 'embedding', 'dense', 'lexical', 'graph-expansion', 'definition-anchors', 'reranker'].map(name => [name, sha256(`src/${name}.mjs`)])) };
try {
  const cases = readFileSync('build/final-kb-retrieval-307029129712/cases.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
  const prior = existsSync(progress) ? JSON.parse(readFileSync(progress, 'utf8')) : { inputs, observations: [] };
  assert.deepEqual(prior.inputs, inputs, 'Resume only identical code/config/data.');
  const observations = prior.observations;
  const passageIds = packet => [...new Set(packet.data.reviewed.flatMap(c => [...new Set(c.evidence.map(e => e.passage_id))].sort()))];
  for (const item of cases.slice(observations.length)) {
    const request = { query: item.query_text, limit: 20, contextBudget: 1000000 };
    const lexical = await service.retrieve({ ...request, profile: 'lexical' });
    const actual = await service.retrieve(request);
    const gold = [...new Set(item.expected_source_refs.map(e => e.passage_id))];
    const ranked = passageIds(actual), baseline = passageIds(lexical);
    for (const c of actual.data.reviewed) { assert.equal(c.review_status, 'reviewed'); assert.ok(c.evidence.every(e => e.claim_id === c.id)); }
    assert.equal(actual.data.research_leads.length, 0); assert.equal(actual.runtime.degraded, false);
    observations.push({ query_id: item.query_id, query_text: item.query_text, stratum: item.query_type,
      at10: rankedMetrics(ranked, gold, 10), at20: rankedMetrics(ranked, gold, 20),
      lexical_at10: rankedMetrics(baseline, gold, 10), lexical_at20: rankedMetrics(baseline, gold, 20),
      context_gold_coverage: gold.filter(id => ranked.includes(id)).length / gold.length,
      actual_claim_ids: actual.data.reviewed.map(c => c.id), source_passages: ranked,
      runtime: actual.runtime, budget: actual.data.budget, paths: actual.data.relation_paths.length, issues: actual.data.issues.map(x => x.issue_id) });
    writeFileSync(progress, JSON.stringify({ inputs, observations }, null, 2));
    if (observations.length % 20 === 0) console.log(JSON.stringify({ actual_api_cases: observations.length, total: cases.length, latest_ms: actual.runtime.elapsed_ms, rss_bytes: process.memoryUsage().rss }));
  }
  const average = (key, field) => observations.reduce((s, o) => s + o[key][field], 0) / observations.length;
  const times = observations.map(o => o.runtime.elapsed_ms).sort((a, b) => a - b);
  const aggregates = Object.fromEntries(['at10', 'at20', 'lexical_at10', 'lexical_at20'].map(k => [k, Object.fromEntries(['recall', 'ndcg_binary', 'all_annotated_evidence_found'].map(field => [field, average(k, field)]))]));
  const result = { created_at: new Date().toISOString(), inputs, graph_version: service.graph.metadata.graph_version,
    real_api_evaluated: true, development_cases: observations.length, prospective_acceptance_run: false,
    comparison: 'Same real packet API, mode knowledge, limit20 and one-million-codepoint budget; unique passage IDs in claim rank order, sorted passage IDs inside each claim; metrics cut at K10/20. Whole issue groups beyond primary limit reported separately.',
    aggregates, elapsed_ms: { p50: times[Math.floor(times.length * .5)], p95: times[Math.floor(times.length * .95)] }, peak_rss_bytes: process.resourceUsage().maxRSS * 1024,
    improved20: observations.filter(o => o.at20.recall > o.lexical_at20.recall).length, regressed20: observations.filter(o => o.at20.recall < o.lexical_at20.recall).length,
    integrity_errors: 0, observations };
  assert.equal(sha256(service.graph.path), inputs.database); assert.equal(sha256(service.paths.profilePath), inputs.profile);
  for (const [name, hash] of Object.entries(inputs.source)) assert.equal(sha256(`src/${name}.mjs`), hash);
  writeFileSync(path, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify({ ...result, observations: undefined }));
} finally { await service.close(); }
