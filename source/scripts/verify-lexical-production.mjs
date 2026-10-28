import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { RetrievalService } from '../src/retrieval.mjs';
import { LexicalIndex, rankedMetrics, uniquePassages } from './lib/retrieval-baselines.mjs';
import { sha256 } from '../src/corpus.mjs';
const service = new RetrievalService();
const before = sha256(service.graph.path);
try {
  const c = service.corpus;
  const claims = [...c.claims.values()].filter(x => x.review_status === 'reviewed');
  const baseline = new LexicalIndex(claims.map(x => ({ id: x.id, text: c.structuredText(x) })));
  const evidence = new Map(claims.map(x => [x.id, [...new Set((c.evidenceByClaim.get(x.id) ?? []).map(e => e.passage_id))].sort()]));
  const cases = readFileSync('build/final-kb-retrieval-307029129712/cases.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
  const observed = [];
  for (const item of cases) {
    const start = performance.now();
    const actual = service.lexicalSearch({ query: item.query_text, mode: 'knowledge', candidateBudget: 100 });
    const expected = baseline.search(item.query_text, 100);
    assert.deepEqual(actual.map(x => [x.id, x.score]), expected.map(x => [x.id, x.score]));
    const ranked = uniquePassages(actual, evidence, 100);
    const relevant = [...new Set(item.expected_source_refs.map(x => x.passage_id))];
    observed.push({ id: item.query_id, elapsed_ms: performance.now() - start, at10: rankedMetrics(ranked, relevant, 10), at20: rankedMetrics(ranked, relevant, 20) });
  }
  assert.equal(sha256(service.graph.path), before);
  const mean = (k, field) => observed.reduce((s, x) => s + x[k][field], 0) / observed.length;
  const result = { created_at: new Date().toISOString(), graph_version: service.graph.metadata.graph_version, cases: observed.length,
    exact_baseline_rank_score_matches: observed.length, canonical_unchanged: true,
    recall_at10: mean('at10', 'recall'), recall_at20: mean('at20', 'recall'), complete_group_at20: mean('at20', 'all_annotated_evidence_found'),
    prospective_acceptance_run: false, scope: 'Production candidate scoring against frozen strong structured lexical baseline; packaging and generated answers not scored', observed };
  writeFileSync('../validation-runs/agent-implementation-20261022/m2-lexical-parity.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ ...result, observed: undefined }));
} finally { service.close(); }
