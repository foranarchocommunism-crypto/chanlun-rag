import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync, statSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from './core.mjs';
import { readCorpus, sha256, codepoints, normalize } from './corpus.mjs';
import { locations, appRoot } from './config.mjs';
import { LexicalIndex, fuse } from './lexical.mjs';
import { DenseIndex } from './dense.mjs';
import { GraphStage, graphProblem } from './graph-stage.mjs';
import { graphFailure } from './graph-expansion.mjs';
import { Reranker } from './reranker.mjs';
import { openStaticDatabase } from './snapshot.mjs';

export class RetrievalError extends Error {
  constructor(code, message, details = {}) { super(message); this.code = code; this.details = details; }
}
const fail = (code, message, details) => { throw new RetrievalError(code, message, details); };
const defaults = { mode: 'knowledge', limit: 10, contextBudget: 60000, candidateBudget: 100,
  graphDepth: 1, graphBudget: 20, issueBudget: 20, rerankBudget: 40, profile: 'hybrid-graph-rerank', allowDegraded: false, trace: false };
const integerFields = { limit: [1, 100], contextBudget: [1000, 1000000], candidateBudget: [20, 1000], graphDepth: [0, 2], graphBudget: [0, 100], issueBudget: [0, 100] };
export function validateRequest(input, profileDefaults = {}) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail('INVALID_REQUEST', 'Request must be an object');
  const allowed = new Set(['query', ...Object.keys(defaults), 'documentId', 'conceptId']);
  for (const key of Object.keys(input)) if (!allowed.has(key)) fail('INVALID_REQUEST', `Unknown request field: ${key}`);
  const request = { ...defaults, ...profileDefaults, ...input };
  if (typeof request.query !== 'string' || !request.query.trim() || codepoints(request.query) > 4000) fail('INVALID_REQUEST', 'query must contain 1–4000 codepoints');
  request.query = request.query.trim();
  if (!['knowledge', 'research', 'source'].includes(request.mode)) fail('INVALID_REQUEST', 'Unknown mode');
  if (!['lexical', 'dense', 'hybrid', 'hybrid-rerank', 'hybrid-graph', 'hybrid-graph-rerank', 'hybrid-graph-v2-rerank'].includes(request.profile)) fail('INVALID_REQUEST', 'Unknown profile');
  if (typeof request.trace !== 'boolean') fail('INVALID_REQUEST', 'trace must be boolean');
  if (typeof request.allowDegraded !== 'boolean') fail('INVALID_REQUEST', 'allowDegraded must be boolean');
  if (![20, 40, 44, 48].includes(request.rerankBudget)) fail('INVALID_REQUEST', 'rerankBudget must be 20, 40, 44 or 48');
  for (const [key, [min, max]] of Object.entries(integerFields)) if (!Number.isInteger(request[key]) || request[key] < min || request[key] > max) fail('INVALID_REQUEST', `${key} must be an integer in ${min}–${max}`);
  for (const key of ['documentId', 'conceptId']) if (request[key] !== undefined && (typeof request[key] !== 'string' || !request[key])) fail('INVALID_REQUEST', `${key} must be a nonempty string`);
  return request;
}

export class RetrievalService {
  constructor(options = {}) {
    this.paths = locations(options); this.graph = new KnowledgeGraph(this.paths.kbPath);
    try {
      this.corpus = readCorpus(this.graph);
      if (!existsSync(this.paths.policyPath)) fail('INDEX_MISSING', 'Research policy missing');
      this.policy = JSON.parse(readFileSync(this.paths.policyPath, 'utf8'));
      this.profile = JSON.parse(readFileSync(this.paths.profilePath, 'utf8')); this.reranker = null;
      this.graphConfigPath = resolve(this.paths.root, 'profiles/graph-v2.json');
      this.graphConfig = JSON.parse(readFileSync(this.graphConfigPath, 'utf8'));
      this.graphStage = new GraphStage(this.corpus, this.graphConfig);
      if (this.policy.graph_version !== this.graph.metadata.graph_version) fail('INDEX_STALE', 'Research policy graph version mismatch');
      this.validatePolicy();
      this.index = null; this.indexProblem = null; this.dense = null; this.denseProblem = null;
      this.loadIndex();
      this.fingerprints = this.fingerprint();
      const digest = path => existsSync(path) ? sha256(path) : null;
      this.identity = {
        product_version: JSON.parse(readFileSync(resolve(appRoot, 'package.json'), 'utf8')).version,
        code: Object.fromEntries(readdirSync(resolve(appRoot, 'src')).filter(n => n.endsWith('.mjs')).map(n => [n, digest(resolve(appRoot, 'src', n))])),
        canonical: this.graph.snapshot.sha256, canonical_manifest: digest(resolve(this.paths.kbPath, 'manifest.json')),
        index_manifest: digest(resolve(this.paths.indexPath, 'manifest.json')), policy: digest(this.paths.policyPath),
        profile: digest(this.paths.profilePath), graph_profile: digest(this.graphConfigPath),
        models: Object.fromEntries(['bge-small-zh-v1.5', 'bge-reranker-base'].map(n => [n, digest(resolve(this.paths.modelPath, 'Xenova', n, 'model-manifest.json'))])),
      };
      this.indexes = new Map();
      this.queue = Promise.resolve();
    } catch (error) { this.projection?.close(); this.graph.close(); throw error; }
  }
  validatePolicy() {
    const ids = new Set();
    for (const issue of this.policy.issues) {
      if (ids.has(issue.issue_id)) fail('INDEX_CORRUPT', 'Duplicate issue ID'); ids.add(issue.issue_id);
      for (const id of [...issue.trigger_claim_ids, ...issue.related_claim_ids]) if (!this.corpus.claims.has(id)) fail('INDEX_CORRUPT', `Unknown policy claim: ${id}`);
      for (const interpretation of issue.interpretations) {
        if (interpretation.graph_version !== this.graph.metadata.graph_version) fail('INDEX_STALE', 'Interpretation version mismatch');
        for (const id of [...interpretation.source_evidence_ids, ...interpretation.support_evidence_ids, ...interpretation.opposing_evidence_ids]) if (!this.corpus.evidence.has(id)) fail('INDEX_CORRUPT', `Unknown interpretation evidence: ${id}`);
      }
    }
  }
  fingerprint() {
    return [resolve(this.paths.kbPath, 'graph.sqlite'), resolve(this.paths.kbPath, 'manifest.json'), this.paths.policyPath,
      resolve(this.paths.indexPath, 'manifest.json'), resolve(this.paths.indexPath, 'projection.sqlite'), this.paths.profilePath, this.graphConfigPath,
      resolve(this.paths.indexPath, 'vectors.f32'), resolve(this.paths.indexPath, 'vector-rows.json'),
      resolve(this.paths.modelPath, 'Xenova/bge-small-zh-v1.5/model-manifest.json'),
      resolve(this.paths.modelPath, 'Xenova/bge-small-zh-v1.5/onnx/model_quantized.onnx'),
      resolve(this.paths.modelPath, 'Xenova/bge-reranker-base/model-manifest.json'),
      resolve(this.paths.modelPath, 'Xenova/bge-reranker-base/onnx/model_quantized.onnx')].map(path => {
      if (!existsSync(path)) return `${path}:missing`;
      const stat = statSync(path); return `${path}:${stat.size}:${stat.mtimeMs}:${stat.ctimeMs}`;
    }).join('|');
  }
  ensureCurrent() {
    this.graph.snapshot?.assertCurrent(); this.projectionSnapshot?.assertCurrent();
    if (this.fingerprints !== this.fingerprint()) fail('INDEX_STALE', 'Inputs changed during session; reopen service after matching publication');
    this.graph.readMetadata(); this.graph.validateManifest();
    if (this.index && this.index.graph_version !== this.graph.metadata.graph_version) fail('INDEX_STALE', 'Graph changed during session');
  }
  loadIndex() {
    const manifest = resolve(this.paths.indexPath, 'manifest.json'), projection = resolve(this.paths.indexPath, 'projection.sqlite');
    if (!existsSync(manifest) || !existsSync(projection)) { this.indexProblem = { code: 'INDEX_MISSING', message: 'Derived index missing; run build-index' }; return; }
    let data;
    try { data = JSON.parse(readFileSync(manifest, 'utf8')); }
    catch { fail('INDEX_CORRUPT', 'Cannot parse index manifest'); }
    if (data.index_schema_version !== '1.0.0' || data.build_status !== 'validated') fail('INDEX_CORRUPT', 'Unvalidated or unsupported derived index');
    if (data.canonical_source_sha256 !== sha256(this.graph.path) || data.canonical_manifest_sha256 !== sha256(resolve(this.paths.kbPath, 'manifest.json')) || data.graph_version !== this.graph.metadata.graph_version || data.policy_sha256 !== sha256(this.paths.policyPath)) {
      this.indexProblem = { code: 'INDEX_STALE', message: 'Index does not match canonical data or research policy' }; return;
    }
    if (data.projection_sha256 !== sha256(projection)) { this.indexProblem = { code: 'INDEX_CORRUPT', message: 'Derived projection checksum mismatch' }; return; }
    if (data.runtime_profile_sha256 && data.runtime_profile_sha256 !== sha256(this.paths.profilePath)) { this.indexProblem = { code: 'INDEX_STALE', message: 'Runtime profile does not match frozen index manifest' }; return; }
    this.projectionSnapshot = openStaticDatabase(projection, data.projection_sha256);
    this.projection = this.projectionSnapshot.db;
    this.index = data;
    if (data.models?.embedding) {
      try { this.dense = new DenseIndex(this.paths.indexPath, this.paths.modelPath, data.models.embedding); }
      catch (error) { this.denseProblem = { code: error.code ?? 'MODEL_MISSING', message: error.message }; }
    }
  }
  async close() { await this.queue; this.projection?.close(); this.graph.close(); await this.dense?.close?.(); await this.reranker?.close?.(); }
  eligible(claim, request) {
    if (!claim || claim.review_status === 'rejected' || request.mode === 'knowledge' && claim.review_status !== 'reviewed') return false;
    if (request.conceptId && !claim.concept_ids.includes(request.conceptId)) return false;
    if (request.documentId && !(this.corpus.evidenceByClaim.get(claim.id) ?? []).some(e => { const p = this.corpus.passages.get(e.passage_id); return p.document_id === request.documentId || p.filename === request.documentId; })) return false;
    return true;
  }
  lexicalIndex(mode) {
    const kind = mode === 'source' ? 'source' : mode === 'knowledge' ? 'reviewed' : 'research';
    if (this.indexes.has(kind)) return this.indexes.get(kind);
    let documents;
    if (kind === 'source') documents = [...this.corpus.passages.values()].map(p => ({ id: p.id, text: p.text }));
    else {
      // Match corpus statistics of the strong reviewed baseline exactly in knowledge mode.
      documents = [...this.corpus.claims.values()].filter(c => c.review_status === 'reviewed' || kind === 'research' && c.review_status === 'pending')
        .map(c => ({ id: c.id, text: this.corpus.structuredText(c) }));
    }
    const index = new LexicalIndex(documents); this.indexes.set(kind, index); return index;
  }
  lexicalSearch(request) {
    const accept = request.mode === 'source' ? doc => {
      const p = this.corpus.passages.get(doc.id);
      const documentMatches = !request.documentId || p.document_id === request.documentId || p.filename === request.documentId;
      const conceptMatches = !request.conceptId || (this.corpus.evidenceByPassage.get(p.id) ?? []).some(e => this.corpus.claims.get(e.claim_id).concept_ids.includes(request.conceptId));
      return documentMatches && conceptMatches;
    } : doc => this.eligible(this.corpus.claims.get(doc.id), request);
    const result = this.lexicalIndex(request.mode).search(request.query, request.candidateBudget, accept)
      .map(r => ({ ...r, reasons: [{ channel: 'structured_lexical', score: r.score }] }));
    const exact = request.mode === 'source' ? this.corpus.passages.get(request.query) : this.corpus.claims.get(request.query);
    if (exact && accept({ id: exact.id })) return [{ id: exact.id, score: 1, reasons: [{ channel: 'exact_id' }] }, ...result.filter(r => r.id !== exact.id)].slice(0, request.candidateBudget);
    return result;
  }
  issueGroups(ranked, request) {
    const selected = new Set(ranked.slice(0, request.limit).map(x => x.id));
    return this.policy.issues.filter(issue => issue.trigger_claim_ids.some(id => selected.has(id)));
  }
  package(ranked, request, runtime, paths = []) {
    // Full window/model reasons belong to runtime trace, outside the evidence budget.
    ranked = ranked.map(r => ({ ...r, reasons: (r.reasons ?? []).map(({ source_reasons, ...reason }) => reason) }));
    const data = { query: request.query, mode: request.mode, status: ranked.length ? 'found' : 'insufficient_evidence', answer_support: 'not_assessed_by_retrieval',
      reviewed: [], research_leads: [], source_context: [], issues: [], relation_paths: [], deferred: [],
      budget: { unit: 'unicode_codepoints_in_JSON_data_object', context_limit: request.contextBudget, requested_results: request.limit,
        candidate_limit: request.candidateBudget, graph_limit: request.graphBudget, issue_limit: request.issueBudget,
        used_codepoints: 0, truncated: false, returned_primary: 0, returned_issue_claims: 0, deferred_count: 0, deferred_list_truncated: false } };
    // Reserve only for bounded counter/status growth after an append. Count all metadata up front.
    const appendLimit = request.contextBudget - 32;
    const size = () => { for (let i = 0; i < 4; i++) data.budget.used_codepoints = codepoints(JSON.stringify(data)); return data.budget.used_codepoints; };
    const append = (key, value) => {
      data[key].push(value);
      if (size() > appendLimit) { data[key].pop(); return false; }
      return true;
    };
    const deferred = (id, reason, kind = 'claim') => {
      data.budget.truncated = true;
      const passage = kind === 'passage' ? this.corpus.passages.get(id) : null;
      const followUp = kind === 'passage' ? { command: 'page', documentId: passage.document_id, page: passage.pdf_page } : { command: kind, id, mode: request.mode };
      data.deferred.push({ id, kind, reason, follow_up: followUp });
    };
    const included = new Set();
    for (const r of ranked.slice(0, request.limit)) {
      let value, key;
      if (request.mode === 'source') {
        const p = this.corpus.passages.get(r.id);
        value = { ...p, semantic_review: 'not_asserted', retrieval: r }; key = 'source_context';
      } else {
        const claim = this.corpus.claims.get(r.id);
        if (!this.eligible(claim, request)) continue;
        value = this.corpus.hydrateClaim(r.id, { ...r, score_meaning: 'relevance_only_not_truth_confidence' });
        key = claim.review_status === 'reviewed' ? 'reviewed' : 'research_leads';
      }
      if (append(key, value)) { included.add(r.id); data.budget.returned_primary++; }
      else deferred(r.id, 'context_budget', request.mode === 'source' ? 'passage' : 'claim');
    }
    if (ranked.length > request.limit) data.budget.truncated = true;
    if (request.mode !== 'source') for (const issue of this.issueGroups(ranked, request)) {
      const permitted = issue.related_claim_ids.filter(id => this.eligible(this.corpus.claims.get(id), request));
      const additions = permitted.filter(id => !included.has(id));
      const record = { ...issue, omitted_claim_ids: issue.related_claim_ids.filter(id => !permitted.includes(id)),
        not_included_reason: permitted.length < issue.related_claim_ids.length ? 'research_mode_required_for_pending' : null,
        interpretation_identity: 'research_record_not_new_author_claim' };
      const snapshot = { reviewed: data.reviewed.length, research: data.research_leads.length, issues: data.issues.length };
      let ok = data.budget.returned_issue_claims + additions.length <= request.issueBudget;
      if (ok) {
        data.issues.push(record);
        for (const id of additions) {
          const item = this.corpus.hydrateClaim(id, { reasons: [{ channel: 'known_issue_group', issue_id: issue.issue_id }], score_meaning: 'relevance_only_not_truth_confidence' });
          data[item.review_status === 'reviewed' ? 'reviewed' : 'research_leads'].push(item);
        }
        ok = size() <= appendLimit;
      }
      if (!ok) {
        data.reviewed.length = snapshot.reviewed; data.research_leads.length = snapshot.research; data.issues.length = snapshot.issues;
        deferred(issue.issue_id, 'whole_issue_group_deferred_by_budget', 'issue');
      } else { additions.forEach(id => included.add(id)); data.budget.returned_issue_claims += additions.length; }
    }
    const auxiliary = new Set();
    for (const path of paths) if (included.has(path.support_claim_id)) {
      let value;
      try { value = this.graphStage.packagePath(path, c => this.eligible(c, request), included); }
      catch (error) { const problem = graphProblem(error); throw graphFailure(problem.code, problem.message, { cause: problem.cause }); }
      const extra = (value.auxiliary_claims ?? []).map(c => c.id).filter(id => !auxiliary.has(id));
      if (auxiliary.size + extra.length > 8 || !append('relation_paths', value)) {
        deferred(path.relation_id, 'whole_graph_path_deferred_by_budget', 'relation');
        const record = data.deferred.at(-1); record.path_id = path.path_id;
        record.follow_ups = (path.steps ?? [path]).map(s => ({ command: 'relation', id: s.relation_id, mode: request.mode }));
      } else extra.forEach(id => auxiliary.add(id));
    }
    // Keep defer metadata bounded, and account for the final budget fields themselves.
    if (!data.budget.returned_primary && ranked.length) data.status = 'budget_insufficient';
    data.budget.deferred_count = data.deferred.length;
    const finalSize = () => {
      data.budget.deferred_list_truncated = data.deferred.length < data.budget.deferred_count;
      for (let i = 0; i < 4; i++) data.budget.used_codepoints = codepoints(JSON.stringify(data));
      return data.budget.used_codepoints;
    };
    while (finalSize() > request.contextBudget && data.deferred.length) data.deferred.pop();
    if (finalSize() > request.contextBudget) fail('INVALID_REQUEST', 'contextBudget cannot fit request metadata; increase it');
    return { contract_version: '1.0.0', request_id: randomUUID(), schema_version: this.graph.metadata.schema_version,
      graph_version: this.graph.metadata.graph_version, index_version: this.index?.index_version ?? null, policy_version: this.policy.policy_version,
      data, runtime };
  }
  retrieve(input, context = {}) {
    const capacity = this.profile.resources?.queue_capacity ?? 8;
    if ((this.pendingRequests ?? 0) >= capacity) return Promise.reject(new RetrievalError('RESOURCE_BUSY', 'Retrieval queue is full; retry later'));
    this.pendingRequests = (this.pendingRequests ?? 0) + 1;
    const queued = performance.now();
    let timer, expired = false;
    const timeout = new Promise((_, reject) => { timer = setTimeout(() => { expired = true; reject(new RetrievalError('QUEUE_TIMEOUT', 'Retrieval queue deadline exceeded')); }, this.profile.resources?.queue_wait_ms_max ?? 30000); });
    const task = this.queue.then(() => {
      clearTimeout(timer);
      if (expired) throw new RetrievalError('QUEUE_TIMEOUT', 'Expired queued request skipped');
      return this.retrieveInternal(input, { ...context, queued });
    }).finally(() => { clearTimeout(timer); this.pendingRequests--; });
    this.queue = task.catch(() => {});
    return Promise.race([task, timeout]);
  }
  async retrieveInternal(input, context = {}) {
    const start = performance.now(), signal = context.signal;
    signal?.throwIfAborted();
    const request = validateRequest(input, input?.profile === 'hybrid-graph-v2-rerank' ? this.graphConfig.defaults : {
      profile: this.profile.default_profile ?? defaults.profile, graphDepth: this.profile.graph.default_depth, graphBudget: this.profile.graph.supported_path_budget, rerankBudget: this.profile.reranker.default_budget }); this.ensureCurrent();
    if (request.conceptId && !this.corpus.concepts.has(request.conceptId)) fail('UNKNOWN_ID', 'Unknown concept ID');
    const runtime = { requested_profile: request.profile, actual_channels: [], degraded: false, degradation_reasons: [], elapsed_ms: 0, queue_wait_ms: start - (context.queued ?? start), stages: {} };
    runtime.effective_request = { ...request };
    runtime.identity = this.identity ?? null;
    const rankings = request.trace ? {} : null;
    const record = (name, rows) => { if (rankings) rankings[name] = structuredClone(rows); };
    const degrade = problem => { if (!request.allowDegraded) fail(problem.code, problem.message); runtime.degraded = true; runtime.degradation_reasons.push(problem); };
    if (this.indexProblem) {
      if (['INDEX_STALE', 'INDEX_CORRUPT'].includes(this.indexProblem.code)) fail(this.indexProblem.code, this.indexProblem.message);
      degrade(this.indexProblem);
    }
    const t = performance.now();
    const channels = [];
    let ranked = this.lexicalSearch(request); runtime.actual_channels.push(request.mode === 'source' ? 'source_lexical' : 'structured_lexical');
    record('lexical', ranked);
    channels.push({ name: 'structured_lexical', weight: this.profile.fusion.lexical_weight, results: ranked });
    runtime.stages.lexical = { candidates: ranked.length, elapsed_ms: performance.now() - t };
    if (request.profile !== 'lexical') {
      if (!this.dense) degrade(this.denseProblem ?? { code: 'MODEL_MISSING', message: 'Dense model/index is not available in this build' });
      else {
        const denseStart = performance.now();
        try {
          const result = await this.dense.search(request.query, { mode: request.mode, limit: request.candidateBudget,
            accept: row => request.mode === 'source' ?
              (!request.documentId || row.document_id === request.documentId || this.corpus.passages.get(row.passage_id).filename === request.documentId) &&
              (!request.conceptId || (this.corpus.evidenceByPassage.get(row.passage_id) ?? []).some(e => this.corpus.claims.get(e.claim_id).concept_ids.includes(request.conceptId))) : this.eligible(this.corpus.claims.get(row.claim_id), request) });
          runtime.stages.dense = { candidates: result.results.length, elapsed_ms: performance.now() - denseStart,
            query_tokens: result.query_tokens, query_truncated: result.query_truncated, query_instruction_enabled: result.query_instruction_enabled };
          runtime.actual_channels.push('semantic_vector');
          record('dense', result.results);
          if (request.profile === 'dense') { ranked = result.results; runtime.actual_channels = ['semantic_vector']; }
          else {
            channels.push({ name: 'semantic_vector', weight: this.profile.fusion.dense_weight, results: result.results });
            ranked = fuse(channels, request.candidateBudget, this.profile.fusion.rrf_constant);
          }
        } catch (error) {
          signal?.throwIfAborted();
          if (error.name === 'AbortError' || error.code === 'CANONICAL_CORRUPT') throw error;
          degrade({ code: error.code ?? 'RESOURCE_ERROR', message: error.message, stage: 'dense' });
        }
      }
    }
    signal?.throwIfAborted();
    const base = structuredClone(ranked), v2 = request.profile === 'hybrid-graph-v2-rerank';
    record('text_fusion', base);
    const baseCount = Math.min(base.length, request.candidateBudget, request.rerankBudget, v2 ? 40 : request.rerankBudget);
    let stage = { ranked: base, paths: [], anchors: [], headCount: baseCount, trace: { status: 'skipped', reason: 'profile_without_graph', committed_paths: 0 } };
    const discardGraph = error => {
      this.graphStage.view = null;
      const problem = graphProblem(error, signal);
      const previous = runtime.stages.graph ?? stage.trace;
      runtime.stages.graph = { ...previous, status: 'failed', reason: problem.code, committed_paths: 0, supported_paths: 0, admission: null };
      runtime.actual_channels = runtime.actual_channels.filter(c => !['supported_graph_expansion', 'graph_definition_anchor'].includes(c));
      delete runtime.stages.definition_anchors;
      stage = { ranked: base, paths: [], anchors: [], headCount: baseCount, trace: runtime.stages.graph };
      degrade(problem);
    };
    if (request.profile.startsWith('hybrid-graph')) {
      const graphStart = performance.now();
      try {
        stage = this.graphStage.run(base, channels, request, this.profile.fusion, c => this.eligible(c, request), { signal });
        runtime.stages.graph = { ...stage.trace, elapsed_ms: performance.now() - graphStart };
        if (stage.paths.length) runtime.actual_channels.push('supported_graph_expansion');
        if (stage.anchors.length) {
          runtime.actual_channels.push('graph_definition_anchor');
          runtime.stages.definition_anchors = { claims: stage.anchors.map(a => a.id), source: 'concept aliases, exact subject predicate and reviewed structural relations' };
        }
      } catch (error) { discardGraph(error); runtime.stages.graph.elapsed_ms = performance.now() - graphStart; }
    } else runtime.stages.graph = stage.trace;
    ranked = stage.ranked;
    record('graph_admission', ranked);
    const scores = new Map();
    const scoreRows = async rows => {
      if (!rows.length) return;
      signal?.throwIfAborted();
      this.reranker ??= new Reranker(this.paths.modelPath, this.index?.models?.reranker);
      const texts = rows.map(r => request.mode === 'source' ? this.corpus.passages.get(r.id).text : (() => {
        const c = this.corpus.claims.get(r.id);
        return [c.text, ...c.conditions, ...c.exceptions].join(' ');
      })());
      const result = await this.reranker.score(request.query, texts);
      signal?.throwIfAborted();
      if (result.scores.length !== rows.length || result.scores.some(s => !Number.isFinite(s))) fail('RESOURCE_ERROR', 'Invalid reranker scores');
      rows.forEach((r, i) => scores.set(r.id, { rerank_score: result.scores[i], rerank_score_meaning: result.score_meaning }));
      runtime.stages.rerank ??= { candidates: 0, calls: 0, input_ids: [], truncated_inputs: 0, elapsed_ms: 0 };
      runtime.stages.rerank.candidates += rows.length; runtime.stages.rerank.calls++;
      runtime.stages.rerank.input_ids.push(...rows.map(r => r.id));
      runtime.stages.rerank.truncated_inputs += result.truncated.filter(Boolean).length;
    };
    const orderScored = (list, count) => [...list.slice(0, count).map(r => ({ ...r, ...scores.get(r.id) }))
      .sort((a, b) => b.rerank_score - a.rerank_score || a.id.localeCompare(b.id)), ...list.slice(count)];
    if (request.profile.endsWith('-rerank')) {
      const rerankStart = performance.now();
      try {
        await scoreRows(ranked.slice(0, stage.headCount));
        ranked = orderScored(ranked, stage.headCount);
        runtime.actual_channels.push('cross_encoder_rerank');
        runtime.stages.rerank.elapsed_ms = performance.now() - rerankStart;
      } catch (error) {
        signal?.throwIfAborted();
        if (error.name === 'AbortError' || error.code === 'CANONICAL_CORRUPT') throw error;
        degrade({ code: error.code ?? 'RESOURCE_ERROR', message: error.message, stage: 'rerank' });
        if (v2) {
          ranked = base; stage.paths = []; stage.anchors = [];
          runtime.stages.graph = { ...runtime.stages.graph, status: 'discarded', reason: 'reranker_unavailable', committed_paths: 0, admission: null };
          runtime.actual_channels = runtime.actual_channels.filter(c => !['supported_graph_expansion', 'graph_definition_anchor'].includes(c));
          delete runtime.stages.definition_anchors;
        }
      }
    }
    record('reranked', ranked);
    if (stage.anchors.length) {
      const ids = new Set(stage.anchors.map(a => a.id));
      ranked = [...stage.anchors.map(a => ({ ...(ranked.find(r => r.id === a.id) ?? a), definition_anchor_priority: true })), ...ranked.filter(r => !ids.has(r.id))];
    }
    const pinExact = list => {
      const exact = request.mode === 'source' ? this.corpus.passages.has(request.query) : this.eligible(this.corpus.claims.get(request.query), request);
      const item = exact && list.find(r => r.id === request.query);
      return item ? [item, ...list.filter(r => r.id !== request.query)] : list;
    };
    ranked = pinExact(ranked);
    let packet;
    try { packet = this.package(ranked, request, runtime, stage.paths); }
    catch (error) {
      if (error.stage !== 'graph') throw error;
      discardGraph(error);
      if (runtime.actual_channels.includes('cross_encoder_rerank')) {
        // V2 protects all baseline rows. Legacy anchoring can leave a few unscored rows.
        const missing = base.slice(0, baseCount).filter(r => !scores.has(r.id));
        if (missing.length) await scoreRows(missing);
        ranked = orderScored(base, baseCount);
      } else ranked = base;
      ranked = pinExact(ranked);
      packet = this.package(ranked, request, runtime, []);
    }
    signal?.throwIfAborted();
    const returned = new Set([...packet.data.reviewed, ...packet.data.research_leads, ...packet.data.source_context].map(c => c.id));
    runtime.primary_result_ids = ranked.slice(0, request.limit).map(r => r.id).filter(id => returned.has(id));
    runtime.selected_reasons = Object.fromEntries(ranked.filter(r => runtime.primary_result_ids.includes(r.id)).map(r => [r.id, structuredClone(r.reasons ?? [])]));
    runtime.stages.graph.committed_paths = packet.data.relation_paths.length;
    const admission = runtime.stages.graph.admission;
    if (admission) admission.final_primary_ids = admission.promoted.map(p => p.id).filter(id => runtime.primary_result_ids.includes(id));
    runtime.effective_pipeline = [...runtime.actual_channels];
    record('final', ranked);
    if (rankings) runtime.rankings = rankings;
    this.ensureCurrent();
    runtime.elapsed_ms = performance.now() - start;
    runtime.end_to_end_ms = runtime.elapsed_ms + runtime.queue_wait_ms;
    return packet;
  }
  status() {
    this.ensureCurrent();
    return this.graph.envelope({ product: 'chan-kg-agent', contract_version: '1.0.0', index: this.index, index_problem: this.indexProblem,
      policy_version: this.policy.policy_version, issue_groups: this.policy.issues.length,
      dense_problem: this.denseProblem,
      profile: this.profile,
      capabilities: { lexical: true, dense: !!this.dense, graph_expansion: true, rerank: existsSync(resolve(this.paths.modelPath, 'Xenova/bge-reranker-base/model-manifest.json')), research_mode: true, source_mode: true },
      counts: { reviewed: [...this.corpus.claims.values()].filter(c => c.review_status === 'reviewed').length,
        reviewed_ambiguity: [...this.corpus.claims.values()].filter(c => c.review_status === 'reviewed' && c.ambiguity_status !== 'none').length,
        pending: [...this.corpus.claims.values()].filter(c => c.review_status === 'pending').length },
      semantic_review_complete: false, release_verification_complete: false });
  }
  async query(command, args = {}) {
    if (command === 'retrieve') return this.retrieve(args);
    if (command === 'status') return this.status();
    if (command === 'claim') {
      this.ensureCurrent();
      const mode = args.mode ?? 'knowledge';
      if (!['knowledge', 'research'].includes(mode)) fail('INVALID_REQUEST', 'claim mode must be knowledge or research');
      const c = this.corpus.claims.get(args.id);
      if (!c || !this.eligible(c, { mode })) fail('UNKNOWN_ID', 'Claim not found in requested knowledge pool');
      return this.graph.envelope({ claim: this.corpus.hydrateClaim(args.id, { reasons: [{ channel: 'exact_id' }] }) });
    }
    if (command === 'issue') {
      this.ensureCurrent();
      const mode = args.mode ?? 'knowledge';
      if (!['knowledge', 'research'].includes(mode)) fail('INVALID_REQUEST', 'issue mode must be knowledge or research');
      const issue = this.policy.issues.find(x => x.issue_id === args.id);
      if (!issue) fail('UNKNOWN_ID', 'Unknown issue ID');
      const permitted = issue.related_claim_ids.filter(id => this.eligible(this.corpus.claims.get(id), { mode }));
      return this.graph.envelope({ issue, claims: permitted.map(id => this.corpus.hydrateClaim(id, { reasons: [{ channel: 'explicit_issue_lookup' }] })),
        omitted_claim_ids: issue.related_claim_ids.filter(id => !permitted.includes(id)), mode });
    }
    if (command === 'relation') {
      this.ensureCurrent(); const mode = args.mode ?? 'knowledge';
      if (!['knowledge', 'research'].includes(mode)) fail('INVALID_REQUEST', 'relation mode must be knowledge or research');
      const relation = this.corpus.relations.find(x => x.id === args.id && (x.review_status === 'reviewed' || mode === 'research' && x.review_status === 'pending'));
      if (!relation) fail('UNKNOWN_ID', 'Relation not found in requested knowledge pool');
      const support = relation.claim_ids.filter(id => this.eligible(this.corpus.claims.get(id), { mode }));
      if (!support.length) fail('UNKNOWN_ID', 'No eligible supporting claims');
      return this.graph.envelope({ relation: { ...relation, claim_ids: support }, supporting_claims: support.map(id => this.corpus.hydrateClaim(id)) });
    }
    this.ensureCurrent(); return this.graph.query(command, args);
  }
}
