import { DatabaseSync } from 'node:sqlite';
import { existsSync, readFileSync } from 'node:fs';
import { resolve, sep } from 'node:path';

const jsonColumns = new Set(['aliases', 'conditions', 'exceptions', 'concept_ids', 'derivation', 'boxes', 'source_spans', 'figure_ids', 'claim_ids', 'checks']);
function decode(row) {
  if (!row) return null;
  return Object.fromEntries(Object.entries(row).map(([k, v]) => [k, jsonColumns.has(k) ? JSON.parse(v) : v]));
}
function bounded(value, fallback, max) {
  if (value === undefined) return fallback;
  if (typeof value !== 'number' && !(typeof value === 'string' && /^\d+$/.test(value))) throw new Error('数值参数必须是整数或CLI十进制整数字符串');
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1 || n > max) throw new Error(`limit 必须是 1–${max} 的整数`);
  return n;
}

export class KnowledgeGraph {
  constructor(kbPath) {
    this.root = resolve(kbPath);
    this.path = resolve(this.root, 'graph.sqlite');
    if (!existsSync(this.path)) throw new Error(`图谱不存在：${this.path}`);
    this.db = new DatabaseSync(this.path, { readOnly: true });
    try {
      this.readMetadata();
      this.validateManifest();
    } catch (error) { this.db.close(); throw error; }
  }
  readMetadata() {
    this.metadata = Object.fromEntries(this.db.prepare('SELECT key,value FROM metadata').all().map(r => [r.key, JSON.parse(r.value)]));
    if (!['1.0.0', '1.1.0'].includes(this.metadata.schema_version)) throw new Error(`不支持的图谱格式：${this.metadata.schema_version}`);
  }
  validateManifest() {
    const manifest = JSON.parse(readFileSync(resolve(this.root, 'manifest.json'), 'utf8'));
    if (manifest.graph_version !== this.metadata.graph_version || manifest.schema_version !== this.metadata.schema_version) throw new Error('图谱正在发布或数据包不完整，请稍后重试');
  }
  close() { this.db.close(); }
  envelope(data, extra = {}) {
    return { schema_version: this.metadata.schema_version, graph_version: this.metadata.graph_version, data, ...extra };
  }
  claimWhere(options = {}, prefix = '') {
    if (options.includeUnreviewed !== undefined && typeof options.includeUnreviewed !== 'boolean') throw new Error('includeUnreviewed 必须是 boolean');
    if (options.reviewStatus && !['pending', 'reviewed', 'rejected'].includes(options.reviewStatus)) throw new Error('未知复核状态');
    if (options.reviewStatus && options.reviewStatus !== 'reviewed' && !options.includeUnreviewed) throw new Error('查询待核或拒绝项需要 includeUnreviewed');
    const state = options.reviewStatus ? `${prefix}review_status='${options.reviewStatus}'` : options.includeUnreviewed ? `${prefix}review_status!='rejected'` : `${prefix}review_status='reviewed'`;
    if (options.maxImportance !== undefined && this.metadata.schema_version === '1.0.0') throw new Error('重要性筛选需要图谱格式1.1.0');
    const importance = options.maxImportance === undefined ? '' : ` AND ${prefix}importance_level<=${bounded(options.maxImportance, 4, 4)}`;
    return state + importance;
  }
  priorityOrder(prefix = '') { return this.metadata.schema_version === '1.1.0' ? `coalesce(${prefix}importance_level,5),` : ''; }
  getClaim(id, options = {}) {
    const claim = decode(this.db.prepare(`SELECT * FROM claims WHERE id=? AND ${this.claimWhere(options)}`).get(id));
    if (!claim) return null;
    claim.evidence = this.db.prepare('SELECT id FROM evidence WHERE claim_id=? ORDER BY id').all(id).map(r => this.getEvidence(r.id, options));
    return claim;
  }
  getEvidence(id, options = {}) {
    const row = this.db.prepare(`SELECT e.*,p.unit_id,p.document_id,p.pdf_page,p.role,p.speaker,p.published_at,p.text AS passage_text,
      pg.printed_page,pg.width AS page_width,pg.height AS page_height,d.filename,d.sha256,d.resource_path,u.title AS unit_title,c.kind,c.review_status
      FROM evidence e JOIN claims c ON c.id=e.claim_id JOIN passages p ON p.id=e.passage_id
      JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page JOIN documents d ON d.id=p.document_id
      LEFT JOIN units u ON u.id=p.unit_id WHERE e.id=? AND ${this.claimWhere(options, 'c.')}`).get(id);
    if (!row) return null;
    const result = decode(row);
    result.context = this.db.prepare(`SELECT id,text,role,speaker,pdf_page FROM passages WHERE document_id=? AND pdf_page BETWEEN ? AND ? AND unit_id IS ? ORDER BY pdf_page,block_index`).all(row.document_id, Math.max(1, row.pdf_page - 1), row.pdf_page + 1, row.unit_id).map(decode);
    result.figures = result.figure_ids.map(fid => decode(this.db.prepare('SELECT * FROM figures WHERE id=?').get(fid)));
    return result;
  }
  search(query, options = {}) {
    const q = String(query ?? '').trim();
    const limit = bounded(options.limit, 20, 100);
    const offset = Number(options.offset ?? 0);
    if (!Number.isInteger(offset) || offset < 0) throw new Error('offset 必须是非负整数');
    if (options.scope && !['knowledge', 'source'].includes(options.scope)) throw new Error('scope 只能是 knowledge 或 source');
    if (options.scope === 'source') {
      if (!q) throw new Error('原文检索需要非空查询');
      const count = this.db.prepare('SELECT count(*) AS n FROM passages WHERE instr(text,?)>0').get(q).n;
      const useFts = [...q].length >= 3;
      const rankCte = useFts ? 'WITH ranked AS (SELECT passage_id,rank FROM passage_fts WHERE passage_fts MATCH ?) ' : '';
      const rankJoin = useFts ? ' LEFT JOIN ranked ON ranked.passage_id=p.id ' : '';
      const rankOrder = useFts ? 'coalesce(ranked.rank,0),' : '';
      const ftsParams = useFts ? [`"${q.replaceAll('"', '""')}"`] : [];
      const rows = this.db.prepare(`${rankCte}SELECT p.id,p.text,p.role,p.speaker,p.published_at,p.document_id,p.pdf_page,p.unit_id,p.boxes,
        u.title AS unit_title,pg.printed_page,d.filename,d.resource_path
        FROM passages p LEFT JOIN units u ON u.id=p.unit_id JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page
        JOIN documents d ON d.id=p.document_id ${rankJoin} WHERE instr(p.text,?)>0
        ORDER BY CASE WHEN p.role IN ('author_body','author_reply') THEN 0 ELSE 1 END,${rankOrder}p.document_id,p.pdf_page,p.block_index LIMIT ? OFFSET ?`).all(...ftsParams, q, limit, offset).map(decode);
      return this.envelope({ scope: 'source', query: q, results: rows, total: count, offset, limit, truncated: offset + rows.length < count, next_offset: offset + rows.length < count ? offset + rows.length : null, status: rows.length ? 'found' : 'no_source_match' });
    }
    const concepts = this.db.prepare('SELECT * FROM concepts').all().map(decode).filter(c => q && (c.label.includes(q) || q.includes(c.label) || c.aliases.some(a => a.includes(q) || q.includes(a))));
    concepts.sort((a, b) => Number(b.label === q || b.aliases.includes(q)) - Number(a.label === q || a.aliases.includes(q)) || a.label.length - b.label.length);
    const where = this.claimWhere(options);
    const ids = concepts.map(c => c.id);
    const directMatch = `instr(text,?)>0
      OR EXISTS (SELECT 1 FROM json_each(claims.conditions) AS condition WHERE instr(condition.value,?)>0)
      OR EXISTS (SELECT 1 FROM json_each(claims.exceptions) AS exception WHERE instr(exception.value,?)>0)`;
    const clause = [`(${directMatch})`, ...ids.map(() => 'instr(concept_ids,?)>0')].join(' OR ');
    const params = [q, q, q, ...ids];
    const total = this.db.prepare(`SELECT count(*) AS n FROM claims WHERE ${where} AND (${clause})`).get(...params).n;
    const rows = this.db.prepare(`SELECT id FROM claims WHERE ${where} AND (${clause}) ORDER BY CASE WHEN (${directMatch}) THEN 0 ELSE 1 END,${this.priorityOrder()}id LIMIT ? OFFSET ?`).all(...params, q, q, q, limit, offset);
    return this.envelope({ scope: 'knowledge', query: q, concepts, results: rows.map(r => this.getClaim(r.id, options)), total, offset, limit, truncated: offset + rows.length < total, next_offset: offset + rows.length < total ? offset + rows.length : null, status: rows.length ? 'found' : 'insufficient_reviewed_evidence' });
  }
  concept(identifier, options = {}) {
    const concepts = this.db.prepare('SELECT * FROM concepts').all().map(decode);
    const match = concepts.find(c => c.id === identifier || c.label === identifier || c.aliases.includes(identifier));
    if (!match) return this.envelope({ status: 'unknown_concept', concept: null, claims: [] });
    const limit = bounded(options.limit, 50, 100);
    const ids = this.db.prepare(`SELECT id FROM claims WHERE instr(concept_ids,?)>0 AND ${this.claimWhere(options)} ORDER BY ${this.priorityOrder()}id LIMIT ?`).all(match.id, limit + 1);
    return this.envelope({ status: ids.length ? 'found' : 'insufficient_reviewed_evidence', concept: match, claims: ids.slice(0, limit).map(r => this.getClaim(r.id, options)), truncated: ids.length > limit });
  }
  neighbors(identifier, options = {}) {
    const center = this.concept(identifier, { ...options, limit: 1 }).data.concept;
    if (!center) return this.envelope({ status: 'unknown_concept', nodes: [], edges: [] });
    const depth = bounded(options.depth, 1, 2);
    const limit = bounded(options.limit, 100, 200);
    const allRelations = this.db.prepare(`SELECT * FROM relations WHERE ${this.claimWhere(options)} ORDER BY ${this.priorityOrder()}id`).all().map(decode).map(r => ({ ...r, claim_ids: r.claim_ids.filter(id => this.db.prepare(`SELECT id FROM claims WHERE id=? AND ${this.claimWhere(options)}`).get(id)) })).filter(r => r.claim_ids.length && (!options.relationType || r.type === options.relationType));
    const included = new Set([center.id]);
    const edges = new Map();
    let frontier = new Set([center.id]), truncated = false;
    for (let level = 0; level < depth; level++) {
      const next = new Set();
      for (const edge of allRelations) {
        if (!frontier.has(edge.source) && !frontier.has(edge.target)) continue;
        const additional = [edge.source, edge.target].filter(id => !included.has(id));
        if (included.size + additional.length > limit) { truncated = true; continue; }
        additional.forEach(id => { included.add(id); next.add(id); });
        edges.set(edge.id, edge);
      }
      frontier = next;
    }
    const nodes = this.db.prepare('SELECT * FROM concepts').all().map(decode).filter(c => included.has(c.id));
    return this.envelope({ status: edges.size ? 'found' : 'no_reviewed_relations', center: center.id, depth, nodes, edges: [...edges.values()], truncated });
  }
  evidence(id, options = {}) {
    const result = this.getEvidence(id, options);
    return this.envelope({ status: result ? 'found' : 'not_found_or_not_reviewed', evidence: result });
  }
  coverage() {
    const counts = Object.fromEntries(['documents', 'pages', 'units', 'passages', 'figures', 'concepts', 'claims', 'relations'].map(t => [t, this.db.prepare(`SELECT count(*) AS n FROM ${t}`).get().n]));
    const reviews = this.db.prepare('SELECT review_status,count(*) AS count FROM claims GROUP BY review_status').all().map(decode);
    const units = this.db.prepare(`SELECT u.*,count(DISTINCT p.id) AS passages,count(DISTINCT c.id) AS candidate_claims,
      count(DISTINCT CASE WHEN c.review_status='reviewed' THEN c.id END) AS reviewed_claims
      FROM units u LEFT JOIN passages p ON p.unit_id=u.id LEFT JOIN evidence e ON e.passage_id=p.id LEFT JOIN claims c ON c.id=e.claim_id GROUP BY u.id ORDER BY u.document_id,u.start_page,u.id`).all().map(decode);
    return this.envelope({ counts, review_status: reviews, units, unresolved_figures: this.db.prepare("SELECT count(*) AS n FROM figures WHERE origin_status='unverified'").get().n, source_extraction_complete: !!this.metadata.source_extraction_complete, semantic_completion: this.metadata.semantic_completion ?? false });
  }
  sources() {
    return this.envelope({ documents: this.db.prepare('SELECT * FROM documents ORDER BY filename').all().map(decode) });
  }
  concepts(options = {}) {
    if (options.includeUnreviewed !== undefined && typeof options.includeUnreviewed !== 'boolean') throw new Error('includeUnreviewed 必须是 boolean');
    const includeUnreviewed = !!options.includeUnreviewed;
    const all = this.db.prepare('SELECT * FROM concepts ORDER BY label').all().map(decode);
    return this.envelope({ concepts: all.map(concept => ({ ...concept,
      reviewed_claims: this.db.prepare("SELECT count(*) AS n FROM claims WHERE review_status='reviewed' AND instr(concept_ids,?)>0").get(concept.id).n,
      pending_claims: includeUnreviewed ? this.db.prepare("SELECT count(*) AS n FROM claims WHERE review_status='pending' AND instr(concept_ids,?)>0").get(concept.id).n : undefined,
    })) });
  }
  page(options = {}) {
    if (typeof options.documentId !== 'string') throw new Error('需要documentId');
    const document = decode(this.db.prepare('SELECT * FROM documents WHERE id=? OR filename=?').get(options.documentId, options.documentId));
    if (!document) throw new Error('未知原文文档');
    const pageNumber = Number(options.page ?? 1);
    if (!Number.isInteger(pageNumber) || pageNumber < 1 || pageNumber > document.page_count) throw new Error(`页码必须是 1–${document.page_count} 的整数`);
    const page = decode(this.db.prepare('SELECT * FROM pages WHERE document_id=? AND pdf_page=?').get(document.id, pageNumber));
    const passages = this.db.prepare('SELECT id,unit_id,pdf_page,block_index,role,speaker,published_at,text,raw_text,boxes FROM passages WHERE document_id=? AND pdf_page=? ORDER BY block_index').all(document.id, pageNumber).map(decode);
    const figures = this.db.prepare('SELECT * FROM figures WHERE document_id=? AND pdf_page=? ORDER BY id').all(document.id, pageNumber).map(row => ({ ...row, bbox: JSON.parse(row.bbox) }));
    return this.envelope({ document, page, passages, figures });
  }
  query(command, args = {}) {
    this.db.exec('BEGIN');
    try {
      this.readMetadata();
      this.validateManifest();
      switch (command) {
        case 'search': return this.search(args.query, args);
        case 'concept': return this.concept(args.id ?? args.query, args);
        case 'neighbors': return this.neighbors(args.id ?? args.query, args);
        case 'evidence': return this.evidence(args.id, args);
        case 'coverage': return this.coverage();
        case 'sources': return this.sources();
        case 'concepts': return this.concepts(args);
        case 'page': return this.page(args);
        default: throw new Error(`未知命令：${command}`);
      }
    } finally { this.db.exec('ROLLBACK'); }
  }
  resourcePath(relativePath) {
    const path = resolve(this.root, relativePath);
    if (path !== this.root && !path.startsWith(this.root + sep)) throw new Error('资源路径超出图谱包');
    return path;
  }
}
