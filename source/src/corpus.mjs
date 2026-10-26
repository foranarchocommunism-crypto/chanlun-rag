import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

const jsonColumns = new Set(['aliases', 'conditions', 'exceptions', 'concept_ids', 'derivation', 'boxes', 'source_spans', 'figure_ids', 'claim_ids']);
export const decode = row => row ? Object.fromEntries(Object.entries(row).map(([k, v]) => [k, jsonColumns.has(k) ? JSON.parse(v) : v])) : null;
export const sha256 = path => createHash('sha256').update(readFileSync(path)).digest('hex');
export const codepoints = text => [...text].length;
export const normalize = text => String(text).normalize('NFKC').toLowerCase();
const corrupt = message => { throw Object.assign(new Error(message), { code: 'CANONICAL_CORRUPT' }); };
export function windows(text, width = 400, overlap = 80) {
  const chars = [...text], result = [];
  for (let start = 0; start < chars.length; start += width - overlap) {
    const end = Math.min(start + width, chars.length);
    result.push({ text: chars.slice(start, end).join(''), start, end });
    if (end === chars.length) break;
  }
  return result;
}

export function readCorpus(graph) {
  const db = graph.db;
  const rows = (sql, ...params) => db.prepare(sql).all(...params).map(decode);
  db.exec('SAVEPOINT corpus_read');
  try {
    graph.readMetadata(); graph.validateManifest();
    const concepts = new Map(rows('SELECT * FROM concepts ORDER BY id').map(x => [x.id, x]));
    const claims = new Map(rows('SELECT * FROM claims ORDER BY id').map(x => [x.id, x]));
    const passages = new Map(rows(`SELECT p.id,p.unit_id,p.document_id,p.pdf_page,p.block_index,p.role,p.speaker,p.published_at,p.text,p.boxes,
      pg.printed_page,pg.width AS page_width,pg.height AS page_height,d.filename,d.sha256 AS document_sha256,d.resource_path,u.title AS unit_title
      FROM passages p JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page JOIN documents d ON d.id=p.document_id
      LEFT JOIN units u ON u.id=p.unit_id ORDER BY p.id`).map(x => [x.id, x]));
    const evidence = new Map(rows('SELECT * FROM evidence ORDER BY id').map(x => [x.id, x]));
    const relations = rows('SELECT * FROM relations ORDER BY id');
    for (const r of relations) if (!concepts.has(r.source) || !concepts.has(r.target) || r.claim_ids.some(id => !claims.has(id))) corrupt(`Invalid canonical relation references: ${r.id}`);
    const evidenceByClaim = new Map(), evidenceByPassage = new Map();
    for (const e of evidence.values()) {
      if (!claims.has(e.claim_id) || !passages.has(e.passage_id)) corrupt(`Invalid evidence references: ${e.id}`);
      const p = passages.get(e.passage_id);
      if ([...p.text].slice(e.quote_start, e.quote_end).join('') !== e.quote) corrupt(`Codepoint quote mismatch: ${e.id}`);
      for (const [map, key] of [[evidenceByClaim, e.claim_id], [evidenceByPassage, e.passage_id]]) {
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(e);
      }
    }
    const structuredText = claim => [claim.text, ...claim.conditions, ...claim.exceptions,
      ...claim.concept_ids.map(id => { const c = concepts.get(id); if (!c) throw new Error(`Unknown concept: ${id}`); return [c.label, ...c.aliases].join(' '); })].join(' ');
    const hydrateEvidence = e => {
      const p = passages.get(e.passage_id), c = claims.get(e.claim_id);
      if (!p || !c) corrupt(`Missing canonical evidence source: ${e.id}`);
      const { text: _text, id: _id, ...source } = p;
      return { ...e, ...source, kind: c.kind, review_status: c.review_status,
        offset_unit: 'unicode_codepoint', context_semantic_review: 'not_asserted',
        evidence_review_basis: 'owner_claim_and_exact_quote_only', source_context_id: p.id };
    };
    const hydrateClaim = (id, retrieval = {}) => {
      const claim = claims.get(id);
      if (!claim) return null;
      return { ...claim, evidence: (evidenceByClaim.get(id) ?? []).map(hydrateEvidence), retrieval };
    };
    return { concepts, claims, passages, evidence, relations, evidenceByClaim, evidenceByPassage, structuredText, hydrateEvidence, hydrateClaim };
  } finally { db.exec('RELEASE corpus_read'); }
}
