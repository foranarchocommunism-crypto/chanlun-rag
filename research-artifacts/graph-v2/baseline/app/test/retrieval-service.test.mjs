import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { mkdtempSync, cpSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, sep } from 'node:path';
import { RetrievalService, validateRequest } from '../src/retrieval.mjs';
import { sha256, codepoints, windows } from '../src/corpus.mjs';
const service = new RetrievalService();
const dbHash = sha256(service.graph.path);
after(async () => { assert.equal(sha256(service.graph.path), dbHash); await service.close(); });
const request = (query, extra = {}) => ({ query, profile: 'lexical', ...extra });

test('reviewed and candidate pools match the fixed graph; triage is character coverage, not semantic equivalence', () => {
  const s = service.status().data;
  assert.deepEqual(s.counts, { reviewed: 3369, reviewed_ambiguity: 473, pending: 2611 });
  const groups = service.projection.prepare('SELECT coverage_class,count(*) AS n FROM candidate_triage GROUP BY coverage_class').all();
  assert.deepEqual(Object.fromEntries(groups.map(x => [x.coverage_class, x.n])), { full_quote_coverage: 2116, no_reviewed_quote: 434, partial_quote_coverage: 61 });
  assert.equal(service.projection.prepare("SELECT count(*) AS n FROM candidate_triage WHERE semantic_status!='unreviewed'").get().n, 0);
});
test('all 473 ambiguous reviewed claims remain accessible with exact original conditions and notes', async () => {
  for (const c of service.corpus.claims.values()) if (c.review_status === 'reviewed' && c.ambiguity_status !== 'none') {
    const result = (await service.query('claim', { id: c.id })).data.claim;
    assert.equal(result.ambiguity_status, c.ambiguity_status); assert.equal(result.review_note, c.review_note);
    assert.deepEqual(result.conditions, c.conditions); assert.deepEqual(result.exceptions, c.exceptions);
    assert.ok(result.evidence.length);
  }
});
test('pending content requires explicit research and cannot be enabled by string false', async () => {
  const id = 'candidate-06fee67b46cd9475';
  await assert.rejects(service.query('claim', { id }), e => e.code === 'UNKNOWN_ID');
  const p = await service.retrieve(request(id, { mode: 'research', limit: 1 }));
  assert.equal(p.data.research_leads[0].id, id); assert.equal(p.data.research_leads[0].review_status, 'pending');
  assert.ok(p.data.reviewed.every(x => x.review_status === 'reviewed'));
  assert.throws(() => validateRequest(request('中枢', { allowDegraded: 'false' })), e => e.code === 'INVALID_REQUEST');
});
test('known scope tension brings both sides and preserves unresolved identity', async () => {
  const id = 'upper-l054-c-stage-same-level-centers-must-have-sublevel-connection-in-this-decomposition';
  const result = await service.retrieve(request(id, { limit: 1, contextBudget: 100000 }));
  assert.ok(result.data.reviewed.some(x => x.id === 'upper-l018-center-theorem-one'));
  assert.equal(result.data.issues[0].resolution_status, 'unresolved');
  assert.ok(result.data.issues[0].interpretations[0].assumed_conditions.length);
  assert.equal(result.data.research_leads.length, 0);
});
test('qualitative guidance returns unknown thresholds and literal qualified wording', async () => {
  const result = await service.retrieve(request('lower-l092-c-stage-secondary-trend-last-center-condition', { limit: 1, contextBudget: 100000 }));
  assert.ok(result.data.issues[0].interpretations[0].unknown_conditions.some(x => x.includes('阈值')));
  const c = (await service.query('claim', { id: 'upper-l041-c-stage-completion-question-basically-yes-qualified-not-equivalence' })).data.claim;
  assert.equal(c.conditions.length, 0); assert.match(c.text + c.review_note + c.evidence.map(e => e.quote).join(''), /基本上/);
});
test('source mode preserves reader attribution and never marks paragraph context reviewed', async () => {
  const id = 'volume_1-a53e99c37ca5-p0306-b000';
  const result = await service.retrieve(request(id, { mode: 'source', limit: 1 }));
  assert.equal(result.data.source_context[0].id, id);
  assert.equal(result.data.source_context[0].role, 'reader');
  assert.equal(result.data.source_context[0].semantic_review, 'not_asserted');
  assert.equal(result.data.reviewed.length, 0);
});
test('tiny budgets defer whole evidence/issue units and preserve a real continuation command', async () => {
  const result = await service.retrieve(request('upper-l054-c-stage-same-level-centers-must-have-sublevel-connection-in-this-decomposition', { limit: 1, contextBudget: 1000 }));
  assert.equal(result.data.reviewed.length, 0);
  assert.equal(result.data.status, 'budget_insufficient');
  assert.ok(result.data.budget.truncated);
  assert.ok(result.data.deferred.length > 0);
  assert.ok(codepoints(JSON.stringify(result.data)) <= 1000);
  assert.equal(result.data.budget.used_codepoints, codepoints(JSON.stringify(result.data)));
  assert.equal(result.data.deferred[0].follow_up.command, 'claim');
});
test('unicode windows use codepoints and can join a supplementary character without corrupting source offsets', () => {
  const text = '甲😀乙丙丁戊己';
  const parts = windows(text, 4, 1);
  assert.deepEqual(parts.map(p => p.text), ['甲😀乙丙', '丙丁戊己']);
  for (const part of parts) assert.equal([...text].slice(part.start, part.end).join(''), part.text);
  const e = service.corpus.hydrateClaim('lower-l092-c-stage-secondary-trend-last-center-condition').evidence[0];
  assert.equal(e.offset_unit, 'unicode_codepoint'); assert.equal(e.context_semantic_review, 'not_asserted');
  assert.equal([...service.corpus.passages.get(e.passage_id).text].slice(e.quote_start, e.quote_end).join(''), e.quote);
});
test('a deferred source passage gives executable page parameters and preserves source attribution', async () => {
  const id = 'volume_1-a53e99c37ca5-p0306-b000';
  const result = await service.retrieve(request(id, { mode: 'source', contextBudget: 1000, limit: 1 }));
  const item = result.data.deferred.find(x => x.kind === 'passage');
  assert.ok(item);
  const { command, ...args } = item.follow_up;
  const page = await service.query(command, args);
  assert.ok(page.data.passages.some(p => p.id === id && p.role === 'reader'));
});
test('missing/stale/corrupt index is explicit and fallback requires a boolean opt-in', async () => {
  const temporary = mkdtempSync(resolve(tmpdir(), 'chan-kg-index-contract-'));
  let missing, stale;
  try {
    missing = new RetrievalService({ indexPath: resolve(temporary, 'missing') });
    await assert.rejects(missing.retrieve(request('中枢')), e => e.code === 'INDEX_MISSING');
    const fallback = await missing.retrieve(request('中枢', { allowDegraded: true }));
    assert.equal(fallback.runtime.degraded, true); assert.equal(fallback.runtime.actual_channels[0], 'structured_lexical');
    const bad = resolve(temporary, 'bad'); cpSync(service.paths.indexPath, bad, { recursive: true });
    const manifest = JSON.parse(readFileSync(resolve(bad, 'manifest.json'), 'utf8'));
    manifest.canonical_source_sha256 = '0'.repeat(64); writeFileSync(resolve(bad, 'manifest.json'), JSON.stringify(manifest));
    stale = new RetrievalService({ indexPath: bad });
    await assert.rejects(stale.retrieve(request('中枢')), e => e.code === 'INDEX_STALE');
    const original = JSON.parse(readFileSync(resolve(service.paths.indexPath, 'manifest.json'), 'utf8'));
    writeFileSync(resolve(bad, 'manifest.json'), JSON.stringify(original));
    await assert.rejects(stale.retrieve(request('中枢')), e => e.code === 'INDEX_STALE');
  } finally {
    await missing?.close(); await stale?.close();
    assert.ok(resolve(temporary).startsWith(resolve(tmpdir()) + sep + 'chan-kg-index-contract-'));
    rmSync(temporary, { recursive: true });
  }
});
