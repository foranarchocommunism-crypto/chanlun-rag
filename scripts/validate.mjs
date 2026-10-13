import { KnowledgeGraph } from '../src/core.mjs';
import { resolve } from 'node:path';
const graph = new KnowledgeGraph(resolve(process.argv[2] ?? process.env.CHAN_KG_PATH ?? '../shared-knowledge/v0.1.0'));
try {
  const errors = [];
  const fk = graph.db.prepare('PRAGMA foreign_key_check').all();
  if (fk.length) errors.push({ type: 'foreign_keys', rows: fk });
  const rows = graph.db.prepare("SELECT id FROM claims WHERE review_status='reviewed'").all();
  for (const { id } of rows) {
    const c = graph.getClaim(id);
    if (!c.evidence.length) errors.push({ id, type: 'missing_evidence' });
    if (![1, 2, 3, 4].includes(c.importance_level) || !c.importance_reason) errors.push({ id, type: 'missing_importance' });
    if (!graph.db.prepare('SELECT id FROM reviews WHERE claim_id=?').get(id)) errors.push({ id, type: 'missing_review_record' });
    for (const e of c.evidence) {
      if (e.passage_text.slice(e.quote_start, e.quote_end) !== e.quote) errors.push({ id, evidence: e.id, type: 'quote_mismatch' });
      if (!['author_body', 'author_reply'].includes(e.role) || e.speaker !== '缠中说禅') errors.push({ id, evidence: e.id, type: 'unverified_speaker' });
      if (!e.source_spans.length || e.source_spans.some(s => !s.boxes.length)) errors.push({ id, evidence: e.id, type: 'missing_geometry' });
    }
    if (c.kind === 'inferred') for (const parent of c.derivation.supporting_claim_ids ?? []) if (!graph.getClaim(parent)) errors.push({ id, type: 'missing_inference_premise', parent });
  }
  const result = { graph_version: graph.metadata.graph_version, reviewed_claims: rows.length, errors, coverage: graph.coverage().data.counts, pass: errors.length === 0 };
  console.log(JSON.stringify(result, null, 2));
  if (errors.length) process.exitCode = 1;
} finally { graph.close(); }
