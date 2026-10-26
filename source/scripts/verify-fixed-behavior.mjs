import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256 } from '../src/corpus.mjs';
const s = new RetrievalService(), before = sha256(s.graph.path), records = [];
const query = '中枢是什么，成立需要什么条件？', expected = 'upper-l017-center-definition';
try {
  for (const [name, options] of Object.entries({ default: {}, text40: { profile: 'hybrid-rerank', rerankBudget: 40 }, text48: { profile: 'hybrid-rerank', rerankBudget: 48 }, graph_admission: { profile: 'hybrid-graph-v2-rerank', graphDepth: 1 } })) {
    const p = await s.retrieve({ query, limit: 5, ...options });
    const ids = p.runtime.primary_result_ids;
    records.push({ name, primary_ids: ids, expected_definition_rank: ids.includes(expected) ? ids.indexOf(expected) + 1 : null,
      graph_anchors: p.runtime.stages.definition_anchors?.claims ?? [], graph_paths: p.data.relation_paths,
      actual_channels: p.runtime.actual_channels });
  }
  assert.ok(records[0].expected_definition_rank && records[0].expected_definition_rank <= 3);
  const failures = [];
  for (const profile of ['hybrid-graph-rerank', 'hybrid-graph-v2-rerank']) {
    const request = { query, profile, limit: 3 }, baseline = await s.retrieve({ ...request, graphDepth: 0 });
    const original = s.graphStage.expand;
    s.graphStage.expand = () => { throw new Error('FIXED_RELEASE_GRAPH_PROBE'); };
    await assert.rejects(s.retrieve(request), e => e.code === 'GRAPH_EXECUTION_ERROR');
    const degraded = await s.retrieve({ ...request, allowDegraded: true });
    assert.deepEqual(degraded.data, baseline.data); assert.equal(degraded.runtime.degraded, true);
    assert.ok(!degraded.runtime.actual_channels.some(x => x.includes('graph')));
    s.graphStage.expand = original;
    const restored = await s.retrieve(request); assert.equal(restored.runtime.degraded, false);
    failures.push({ profile, strict_error: 'GRAPH_EXECUTION_ERROR', fallback_data_equal: true, subsequent_request_recovered: true });
  }
  const unrelated = await s.retrieve({ query: '如何烤披萨？', limit: 1 });
  assert.equal(unrelated.runtime.stages.graph.reason, 'no_query_anchor');
  assert.ok(!unrelated.runtime.actual_channels.some(x => x.includes('graph')));
  assert.equal(sha256(s.graph.path), before);
  const result = { pass: true, canonical_unchanged: true, definition_query: query, definition_expected_id: expected,
    scope: 'Existing functional regression and controlled mechanism probe; not an independent representative semantic benchmark',
    definition_comparison: records, graph_failures: failures,
    unrelated_graph_skipped: true, unrelated_text_status: unrelated.data.status,
    source_code: s.identity.code, default_profile: s.profile.default_profile };
  writeFileSync('build/formal-release/definition-and-fallback.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ pass: true, definitions: records.map(({ name, expected_definition_rank }) => ({ name, expected_definition_rank })), graph_failures: failures }));
} finally { await s.close(); }
