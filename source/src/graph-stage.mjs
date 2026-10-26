import { expandGraphV2, buildGraphView, graphGuard, graphFailure, GRAPH_LIMITS } from './graph-expansion.mjs';
import { admitGraph } from './graph-admission.mjs';
import { definitionAnchors } from './definition-anchors.mjs';
import { fuse } from './lexical.mjs';

// The optional stage owns its draft and cache. Retrieval commits the returned delta.
export class GraphStage {
  constructor(corpus, config) { this.corpus = corpus; this.config = config; this.view = null; this.clock = () => performance.now(); }
  prepare(guard) { return this.view ?? buildGraphView(this.corpus, guard); }
  expand(base, request, eligible, context) {
    return expandGraphV2(this.corpus, base, request, eligible, context);
  }
  anchors(request, eligible, context) { return definitionAnchors(this.corpus, request.query, eligible, Math.min(2, request.graphBudget), context); }
  validate(paths, request, eligible) {
    if (!Array.isArray(paths) || paths.length > request.graphBudget) throw graphFailure('GRAPH_OUTPUT_INVALID', 'Invalid graph path budget');
    for (const p of paths) {
      if (!Number.isInteger(p.depth) || p.depth < 1 || p.depth > request.graphDepth || p.relation_path.length !== p.depth || p.concept_path.length !== p.depth + 1 ||
        p.steps && (p.steps.length !== p.depth || new Set(p.concept_path).size !== p.concept_path.length)) throw graphFailure('GRAPH_OUTPUT_INVALID', 'Invalid graph path shape');
      for (const [i, s] of (p.steps ?? [p]).entries()) {
        const r = this.corpus.relations.find(r => r.id === s.relation_id);
        if (!r || r.source !== s.source || r.target !== s.target || r.type !== s.relation_type || !r.claim_ids.includes(s.support_claim_id) ||
          !eligible(this.corpus.claims.get(s.support_claim_id)) || !s.support_evidence_ids?.length ||
          s.support_evidence_ids.some(id => this.corpus.evidence.get(id)?.claim_id !== s.support_claim_id) ||
          r.review_status !== 'reviewed' && !(request.mode === 'research' && r.review_status === 'pending')) throw graphFailure('GRAPH_OUTPUT_INVALID', 'Invalid graph evidence path');
        if (p.steps && (p.relation_path[i] !== s.relation_id || !(s.source === p.concept_path[i] && s.target === p.concept_path[i + 1] || s.target === p.concept_path[i] && s.source === p.concept_path[i + 1]) ||
          s.traversal_direction !== (s.source === p.concept_path[i] ? 'source_to_target' : 'target_to_source_association_only'))) throw graphFailure('GRAPH_OUTPUT_INVALID', 'Disconnected or reversed graph path');
      }
    }
  }
  run(base, channels, request, fusion, eligible, { signal } = {}) {
    const start = this.clock(), guard = graphGuard({ clock: this.clock, start, signal });
    const v2 = request.profile === 'hybrid-graph-v2-rerank';
    if (request.mode === 'source' || !request.graphDepth || !request.graphBudget) return { ranked: base, anchors: [], paths: [], headCount: Math.min(base.length, v2 ? 40 : request.rerankBudget, request.rerankBudget), trace: { status: 'skipped', reason: request.mode === 'source' ? 'source_mode' : 'graph_disabled', committed_paths: 0 } };
    const view = this.prepare(guard);
    const expansion = this.expand(base, request, eligible, { view, guard }); guard();
    const consume = kind => {
      const key = kind === 'edges' ? 'edge_reads' : 'support_checks';
      if (expansion.trace[key] >= GRAPH_LIMITS[kind]) {
        expansion.trace.status = 'budget_exhausted'; expansion.truncated = true;
        if (!expansion.trace.truncation_reasons.includes('anchor_' + kind + '_limit')) expansion.trace.truncation_reasons.push('anchor_' + kind + '_limit');
        return false;
      }
      expansion.trace[key]++; return true;
    };
    const anchors = expansion.trace?.status === 'skipped' ? [] : this.anchors(request, eligible, { guard, consume }); guard();
    const paths = [...expansion.paths];
    for (const a of anchors) {
      const r = a.relations[0];
      if (paths.some(p => p.relation_id === r.id && p.support_claim_id === a.id)) continue;
      const step = { relation_id: r.id, relation_type: r.type, source: r.source, target: r.target, traversal_direction: 'source_to_target', original_review_status: r.review_status,
        supporting_claim_ids: [a.id], support_claim_id: a.id, support_evidence_ids: this.corpus.evidenceByClaim.get(a.id).map(e => e.id) };
      paths.unshift({ ...step, ...(v2 ? { path_id: `anchor:${r.id}:${a.id}`, steps: [step] } : {}), seed_claim_id: a.id, depth: 1, concept_path: [r.source, r.target], relation_path: [r.id],
        semantics: 'evidence_supported_association_not_transitive_inference', depends_on_interpretation: false, query_intent: 'definition' });
    }
    while (paths.length > request.graphBudget) {
      paths.pop();
    }
    this.validate(paths, request, eligible); guard();
    const trace = { ...(expansion.trace ?? { status: paths.length ? expansion.truncated ? 'budget_exhausted' : 'success' : 'empty' }),
      additional_candidates: expansion.additions.length, supported_paths: paths.length, attempted_paths: paths.length, committed_paths: paths.length, truncated: expansion.truncated };
    let result;
    if (v2) {
      const admission = admitGraph(base, channels, paths, anchors, request, this.config.graph_additions_max);
      result = { ...admission, trace: { ...trace, admission: admission.trace, committed_paths: admission.paths.length } };
    } else {
      const ids = [...new Set(paths.map(p => p.support_claim_id))];
      let ranked = fuse([...channels, { name: 'supported_graph_expansion', weight: fusion.graph_weight, results: ids.map(id => ({ id, score: 0 })) }], request.candidateBudget, fusion.rrf_constant);
      if (anchors.length) { const anchorIds = new Set(anchors.map(a => a.id)); ranked = [...anchors.map(a => ({ id: a.id, score: ranked.find(r => r.id === a.id)?.score ?? 0, reasons: a.reasons })), ...ranked.filter(r => !anchorIds.has(r.id))].slice(0, request.candidateBudget); }
      result = { ranked, anchors, paths, headCount: Math.min(ranked.length, request.rerankBudget), trace };
    }
    guard(); this.view = view;
    return result;
  }
  packagePath(path, eligible, included) {
    if (!path.steps) return path;
    const auxiliary_claims = [];
    for (const id of new Set(path.steps.map(s => s.support_claim_id))) {
      if (!eligible(this.corpus.claims.get(id))) throw graphFailure('GRAPH_OUTPUT_INVALID', 'Ineligible path support');
      if (!included.has(id)) auxiliary_claims.push(this.corpus.hydrateClaim(id, { reasons: [{ channel: 'graph_bridge_support' }], score_meaning: 'relevance_only_not_truth_confidence' }));
    }
    const value = { ...path, auxiliary_claims, evidence_chain_complete: true };
    JSON.stringify(value); return value;
  }
}

export function graphProblem(error, signal) {
  signal?.throwIfAborted();
  if (error.name === 'AbortError' || error.code === 'ABORT_ERR' || error.code === 'CANONICAL_CORRUPT' || error.code?.startsWith('INDEX_') || error.code === 'INVALID_REQUEST') throw error;
  return { code: error.code?.startsWith('GRAPH_') ? error.code : 'GRAPH_EXECUTION_ERROR', message: 'Optional graph stage failed; text retrieval is available', stage: 'graph', cause: error.message };
}
