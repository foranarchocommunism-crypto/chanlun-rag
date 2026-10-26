import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, mkdirSync, readFileSync, renameSync, unlinkSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';
import { readCorpus, sha256, windows } from '../src/corpus.mjs';
import { atomicJson, acquireBuildLock } from './lib/durable-files.mjs';

const args = process.argv.slice(2);
const arg = (name, fallback) => args.includes(name) ? args[args.indexOf(name) + 1] : fallback;
const kb = resolve(arg('--kb', '../shared-knowledge/v0.1.0'));
const policyPath = resolve(arg('--policy', 'policies/ambiguity-issues.json'));
const output = resolve(arg('--output', 'indexes/lexical-1-307029129712'));
const sourceSha = sha256(resolve(kb, 'graph.sqlite')), manifestSha = sha256(resolve(kb, 'manifest.json'));
const graph = new KnowledgeGraph(kb);
const identity = { sourceSha, manifestSha, policySha: sha256(policyPath), schemaSha: sha256('contracts/retrieval-index.schema.sql') };
mkdirSync(dirname(output), { recursive: true });
const releaseLock = acquireBuildLock(output + '.build.lock');
const staging = output + '.building';
let derived;
try {
  if (existsSync(output)) {
    const prior = JSON.parse(readFileSync(resolve(output, 'manifest.json'), 'utf8'));
    assert.equal(prior.canonical_source_sha256, sourceSha, 'Published output belongs to another snapshot');
    assert.equal(prior.canonical_manifest_sha256, manifestSha);
    assert.equal(prior.policy_sha256, identity.policySha);
    assert.equal(prior.projection_sha256, sha256(resolve(output, 'projection.sqlite')));
    assert.equal(prior.build_status, 'validated');
    console.log(JSON.stringify({ output, completed: true, reused: true }));
  } else {
  mkdirSync(staging, { recursive: true });
  const statePath = resolve(staging, 'build-inputs.json');
  if (existsSync(statePath)) assert.deepEqual(JSON.parse(readFileSync(statePath, 'utf8')), identity, 'Resume requires the same frozen inputs');
  else atomicJson(statePath, identity);
  // Only owned, unfinished SQLite files are replaced; published output is never overwritten.
  for (const file of ['projection.sqlite', 'projection.sqlite-journal']) {
    const path = resolve(staging, file); if (existsSync(path)) unlinkSync(path);
  }
  const c = readCorpus(graph), policy = JSON.parse(readFileSync(policyPath, 'utf8'));
  assert.equal(policy.graph_version, graph.metadata.graph_version);
  derived = new DatabaseSync(resolve(staging, 'projection.sqlite'));
  derived.exec(readFileSync('contracts/retrieval-index.schema.sql', 'utf8'));
  derived.exec('BEGIN');
  const claimConcept = derived.prepare('INSERT INTO claim_concept VALUES(?,?)');
  const relationSupport = derived.prepare('INSERT INTO relation_support VALUES(?,?)');
  const ep = derived.prepare('INSERT INTO evidence_passage VALUES(?,?,?,?,?)');
  const doc = derived.prepare('INSERT INTO retrieval_documents VALUES(?,?,?,?,?,?,?,?)');
  const triage = derived.prepare('INSERT INTO candidate_triage VALUES(?,?,?,?)');
  const counts = { claims: 0, reviewed: 0, pending: 0, evidence_windows: 0, source_windows: 0, triage: { full_quote_coverage: 0, partial_quote_coverage: 0, no_reviewed_quote: 0 } };
  for (const claim of c.claims.values()) {
    for (const id of claim.concept_ids) claimConcept.run(claim.id, id);
    if (claim.review_status === 'rejected') continue;
    counts.claims++; counts[claim.review_status === 'reviewed' ? 'reviewed' : 'pending']++;
    const evidence = c.evidenceByClaim.get(claim.id) ?? [];
    doc.run(`claim:${claim.id}`, 'claim', claim.review_status, claim.id, null, null, null, c.structuredText(claim));
    for (const e of evidence) {
      ep.run(e.id, claim.id, e.passage_id, e.quote_start, e.quote_end);
      windows(e.quote).forEach((w, i) => { doc.run(`evidence:${e.id}:${i}`, 'evidence', claim.review_status, claim.id, e.id, e.passage_id, c.passages.get(e.passage_id).document_id,
        JSON.stringify({ text: w.text, start: e.quote_start + w.start, end: e.quote_start + w.end, offset_unit: 'unicode_codepoint' })); counts.evidence_windows++; });
    }
    if (claim.review_status === 'pending') {
      const related = evidence.flatMap(e => (c.evidenceByPassage.get(e.passage_id) ?? []).filter(r => c.claims.get(r.claim_id).review_status === 'reviewed'));
      let total = 0, covered = 0;
      for (const e of evidence) {
        total += e.quote_end - e.quote_start;
        const intervals = related.filter(r => r.passage_id === e.passage_id).map(r => [Math.max(r.quote_start, e.quote_start), Math.min(r.quote_end, e.quote_end)]).filter(([a, b]) => b > a).sort((a, b) => a[0] - b[0]);
        let until = e.quote_start;
        for (const [a, b] of intervals) { covered += Math.max(0, b - Math.max(a, until)); until = Math.max(until, b); }
      }
      const group = total && covered >= total ? 'full_quote_coverage' : covered ? 'partial_quote_coverage' : 'no_reviewed_quote';
      counts.triage[group]++;
      triage.run(claim.id, group, JSON.stringify([...new Set(related.map(r => r.claim_id))]), 'unreviewed');
    }
  }
  for (const r of c.relations) for (const id of r.claim_ids) { assert.ok(c.claims.has(id)); relationSupport.run(r.id, id); }
  for (const p of c.passages.values()) windows(p.text).forEach((w, i) => {
    doc.run(`source:${p.id}:${i}`, 'source', null, null, null, p.id, p.document_id,
      JSON.stringify({ text: w.text, start: w.start, end: w.end, offset_unit: 'unicode_codepoint' })); counts.source_windows++;
  });
  for (const [key, value] of Object.entries({ index_schema_version: '1.0.0', graph_version: graph.metadata.graph_version })) derived.prepare('INSERT INTO metadata VALUES(?,?)').run(key, JSON.stringify(value));
  derived.exec('COMMIT');
  assert.equal(derived.prepare('PRAGMA integrity_check').get().integrity_check, 'ok');
  derived.close(); derived = null;
  assert.equal(sha256(resolve(kb, 'graph.sqlite')), sourceSha);
  assert.equal(sha256(resolve(kb, 'manifest.json')), manifestSha);
  const manifest = { index_version: 'lexical-1', index_schema_version: '1.0.0', graph_version: graph.metadata.graph_version,
    schema_version: graph.metadata.schema_version, canonical_source_sha256: sourceSha, canonical_manifest_sha256: manifestSha,
    indexed_snapshot_sha256: sourceSha, policy_version: policy.policy_version, policy_sha256: sha256(policyPath),
    projection_sha256: sha256(resolve(staging, 'projection.sqlite')), created_at: new Date().toISOString(),
    text_processing: { normalization: 'NFKC-lowercase-v1', tokenizer: 'Han-2/3gram-ascii-binary-tf-v1', windows: { codepoints: 400, overlap: 80 }, offset_unit: 'unicode_codepoint' },
    counts, models: {}, build_status: 'validated', semantic_review_changed: false };
  graph.snapshot.assertCurrent();
  atomicJson(resolve(staging, 'manifest.json'), manifest);
  renameSync(staging, output);
  console.log(JSON.stringify({ output, ...manifest }, null, 2));
  }
} finally { derived?.close(); graph.close(); releaseLock(); }
