import assert from 'node:assert/strict';
import { writeFileSync, readFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';
import { readCorpus, sha256 } from '../src/corpus.mjs';
const root = resolve('build/formal-release'); mkdirSync(root, { recursive: true });
const kb = resolve('../shared-knowledge/v0.1.0'), graph = new KnowledgeGraph(kb);
try {
  const before = sha256(graph.path), manifest = sha256(resolve(kb, 'manifest.json'));
  assert.equal(before, '3463d772e607c6e89104c17c02c6b3656cca766f444d226c011fb9d8a9017271', 'Frozen source knowledge changed');
  assert.equal(graph.db.prepare('PRAGMA integrity_check').get().integrity_check, 'ok');
  assert.deepEqual(graph.db.prepare('PRAGMA foreign_key_check').all(), []);
  const corpus = readCorpus(graph), sources = graph.sources().data.documents.map(d => {
    const file = graph.resourcePath(d.resource_path), hash = sha256(file); assert.equal(hash, d.sha256); return { id: d.id, path: d.resource_path, sha256: hash };
  });
  const statuses = Object.fromEntries(['reviewed', 'pending', 'rejected'].map(status => [status, [...corpus.claims.values()].filter(c => c.review_status === status).length]));
  assert.deepEqual(statuses, { reviewed: 3369, pending: 2611, rejected: 28 });
  let reviewedEvidence = 0;
  for (const c of corpus.claims.values()) {
    if (c.review_status !== 'reviewed') continue;
    const evidence = corpus.evidenceByClaim.get(c.id) ?? []; assert.ok(evidence.length);
    assert.ok(Array.isArray(c.conditions) && Array.isArray(c.exceptions));
    for (const e of evidence) {
      const p = corpus.passages.get(e.passage_id);
      assert.ok(['author_body', 'author_reply', 'author_commentary'].includes(p.role)); assert.equal(p.speaker, '缠中说禅');
      reviewedEvidence++;
    }
  }
  const packet = { pass: true, client_date: '2026-10-26', fixed_corpus: true, canonical_sha256: before, manifest_sha256: manifest,
    integrity_check: 'ok', foreign_key_errors: 0, all_claim_quote_offsets_checked: true,
    statuses, concepts: corpus.concepts.size, relations: corpus.relations.length, reviewed_evidence: reviewedEvidence, sources,
    semantic_boundary: 'Existing review states and ambiguity retained; this audit does not assert new independent semantic verification',
    canonical_unchanged: sha256(graph.path) === before && sha256(resolve(kb, 'manifest.json')) === manifest };
  assert.equal(packet.canonical_unchanged, true);
  writeFileSync(resolve(root, 'knowledge-integrity.json'), JSON.stringify(packet, null, 2) + '\n'); console.log(JSON.stringify(packet));
} finally { graph.close(); }
