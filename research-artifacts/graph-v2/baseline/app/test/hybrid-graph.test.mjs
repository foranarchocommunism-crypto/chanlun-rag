import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { readFileSync } from 'node:fs';
import { AjvJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/ajv-provider.js';
import { RetrievalService } from '../src/retrieval.mjs';
import { expandGraph } from '../src/graph-expansion.mjs';
const service = new RetrievalService();
after(async () => { await service.close(); });

test('default hybrid graph reranker returns precise cited definition, complete conditions and true channels', async () => {
  const result = await service.retrieve({ query: '中枢是什么，成立需要什么条件？', limit: 5, contextBudget: 60000 });
  assert.ok(result.data.reviewed.slice(0, 3).some(x => x.id === 'upper-l017-center-definition'));
  const definition = result.data.reviewed.find(x => x.id === 'upper-l017-center-definition');
  assert.ok(definition.conditions.some(c => c.includes('完成')));
  assert.deepEqual(result.runtime.actual_channels, ['structured_lexical', 'semantic_vector', 'supported_graph_expansion', 'graph_definition_anchor', 'cross_encoder_rerank']);
  assert.equal(result.runtime.degraded, false);
  assert.ok(result.data.reviewed.every(c => c.review_status === 'reviewed'));
  assert.equal(result.data.answer_support, 'not_assessed_by_retrieval');
  const schema = JSON.parse(readFileSync('contracts/evidence-packet.schema.json', 'utf8')); delete schema.$schema;
  const validation = new AjvJsonSchemaValidator().getValidator(schema)(result);
  assert.equal(validation.valid, true, validation.errorMessage);
});
test('graph paths preserve direction, hops, real supports and a hard path budget', () => {
  const request = { query: '中枢与次级别有哪些关系？', mode: 'knowledge', candidateBudget: 100, limit: 20, graphDepth: 2, graphBudget: 3 };
  const seeds = service.lexicalSearch(request);
  const result = expandGraph(service.corpus, seeds, request, c => c.review_status === 'reviewed');
  assert.ok(result.paths.length > 0 && result.paths.length <= 3);
  for (const p of result.paths) {
    const original = service.corpus.relations.find(r => r.id === p.relation_id);
    assert.equal(p.source, original.source); assert.equal(p.target, original.target); assert.equal(p.relation_type, original.type);
    assert.ok(original.claim_ids.includes(p.support_claim_id));
    assert.ok(p.support_evidence_ids.every(id => service.corpus.evidence.get(id).claim_id === p.support_claim_id));
    assert.ok(p.depth <= 2); assert.equal(p.relation_path.length, p.depth);
    assert.equal(p.semantics, 'evidence_supported_association_not_transitive_inference');
  }
});
test('semantic research still partitions pending and preserves cross-page sources', async () => {
  const result = await service.retrieve({ query: 'candidate-09120e714f8fe0f3', mode: 'research', limit: 1, contextBudget: 100000, profile: 'hybrid' });
  assert.equal(result.data.research_leads[0].id, 'candidate-09120e714f8fe0f3');
  assert.ok(result.data.research_leads.some(c => c.id === 'candidate-a0ade5e49c0ea61b'));
  assert.ok(result.data.issues.some(i => i.issue_id === 'issue-cross-page-continuation'));
  assert.ok(result.data.research_leads.flatMap(c => c.evidence).every(e => e.offset_unit === 'unicode_codepoint'));
});
test('concurrent API requests are serialized through one model session and failure does not poison the queue', async () => {
  const requests = await Promise.allSettled([
    service.retrieve({ query: '', profile: 'lexical' }),
    service.retrieve({ query: 'upper-l017-center-definition', profile: 'hybrid', limit: 1 }),
    service.retrieve({ query: 'upper-l017-minimum-level-center', profile: 'hybrid', limit: 1 }),
  ]);
  assert.equal(requests[0].status, 'rejected');
  assert.equal(requests[1].value.data.reviewed[0].id, 'upper-l017-center-definition');
  assert.equal(requests[2].value.data.reviewed[0].id, 'upper-l017-minimum-level-center');
});
