import { RetrievalService } from '../../src/retrieval.mjs';
import { GraphStage } from '../../src/graph-stage.mjs';
export const request = { query: '起点甲经过桥接后最终校验口令是什么？', profile: 'hybrid-graph-v2-rerank', mode: 'knowledge', limit: 20, contextBudget: 60000, candidateBudget: 100, rerankBudget: 48, graphDepth: 2, graphBudget: 20, issueBudget: 0, allowDegraded: false };
export function fixture(noise = 120) {
  const corpus = { concepts: new Map(), claims: new Map(), evidence: new Map(), passages: new Map(), evidenceByClaim: new Map(), relations: [] };
  const concept = (id, label = id) => corpus.concepts.set(id, { id, label, aliases: [] });
  const claim = (id, text, concepts = [], status = 'reviewed') => {
    const c = { id, text, concept_ids: concepts, review_status: status, kind: 'explicit', conditions: ['仅适用于隔离测试语料'], exceptions: [], ambiguity_status: 'none', review_note: 'Synthetic test fixture, not author knowledge' };
    const p = { id: 'p-' + id, document_id: 'd-' + id, filename: 'fixture.txt', pdf_page: 1, text, role: 'author', speaker: 'fixture', source_spans: [] };
    const e = { id: 'e-' + id, claim_id: id, passage_id: p.id, quote: text, quote_start: 0, quote_end: [...text].length, source_spans: [], ...p, id: 'e-' + id, claim_id: id, passage_id: p.id, review_status: status, context_semantic_review: 'not_asserted' };
    corpus.claims.set(id, c); corpus.passages.set(p.id, p); corpus.evidence.set(e.id, e); corpus.evidenceByClaim.set(id, [e]); return c;
  };
  const relation = (id, source, target, claim_ids, status = 'reviewed') => { const r = { id, source, target, type: 'related_to', claim_ids, review_status: status }; corpus.relations.push(r); return r; };
  concept('A', '起点甲'); concept('B', '桥接乙'); concept('C', '终点丙');
  claim('seed', '起点甲是隔离测试装置的入口。', ['A']);
  claim('bridge', '起点甲连接桥接乙，必须经过桥接乙才能查询终点。', ['A','B']);
  claim('answer', '桥接乙到达终点丙，最终校验口令是紫色天鹅。', ['B','C']);
  relation('r001', 'A', 'B', ['bridge']); relation('r002', 'B', 'C', ['answer']);
  for (let i = 0; i < noise; i++) claim('n' + String(i).padStart(3, '0'), '天气记录第' + i + '号：下午阴天，气温二十度。');
  corpus.hydrateClaim = (id, retrieval = {}) => ({ ...corpus.claims.get(id), evidence: corpus.evidenceByClaim.get(id), retrieval });
  const base = ['seed', ...[...corpus.claims.keys()].filter(id => id.startsWith('n'))].slice(0, 100).map((id, i) => ({ id, score: 100 - i, reasons: [{ channel: 'fixture_text' }] }));
  return { corpus, base, concept, claim, relation };
}
export function fakeService(f = fixture()) {
  const s = Object.create(RetrievalService.prototype);
  Object.assign(s, { corpus: f.corpus, graph: { metadata: { schema_version: 'fixture', graph_version: 'fixture' } }, index: { index_version: 'fixture' }, paths: {},
    profile: { fusion: { lexical_weight: 1, dense_weight: .5, graph_weight: .1, rrf_constant: 60 }, graph: { default_depth: 1, supported_path_budget: 20 }, reranker: { default_budget: 40 } },
    graphConfig: { defaults: { graphDepth: 2, graphBudget: 20, rerankBudget: 48 }, graph_additions_max: 8 },
    policy: { policy_version: 'fixture', issues: [] }, queue: Promise.resolve(), ensureCurrent() {}, calls: { dense: 0, rerank: 0 } });
  s.graphStage = new GraphStage(s.corpus, s.graphConfig);
  s.lexicalSearch = req => req.mode === 'source' ? [...s.corpus.passages.keys()].map(id => ({ id, score: 1 })) : structuredClone(f.base.slice(0, req.candidateBudget));
  s.dense = { search: async (_q, opts) => { s.calls.dense++; return { results: opts.mode === 'source' ? [] : structuredClone(f.base.slice(0, opts.limit)), query_tokens: 12, query_truncated: false }; } };
  s.reranker = { score: async (_q, texts) => { s.calls.rerank++; return { scores: texts.map(text => text.includes('紫色天鹅') ? 10 : text.includes('起点甲') ? 5 : 0), truncated: texts.map(() => false), score_meaning: 'synthetic_test_score_not_model_quality' }; } };
  return s;
}

