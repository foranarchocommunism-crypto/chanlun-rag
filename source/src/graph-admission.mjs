// Candidate admission is independent of RRF magnitude. Scores remain relevance only.
export function admitGraph(base, channels, paths, anchors, request, maxAdditions = 8) {
  const capacity = Math.min(request.rerankBudget, request.candidateBudget);
  const protectedCount = Math.min(40, capacity);
  const head = base.slice(0, protectedCount).map(x => ({ ...x }));
  const baseIds = new Set(head.map(x => x.id));
  const union = new Set(channels.flatMap(c => c.results.map(x => x.id)));
  const selected = new Set(baseIds), promotions = [], deferred = [], acceptedAnchors = [];
  const allowance = Math.min(8, maxAdditions, Math.max(0, capacity - protectedCount));
  const category = id => baseIds.has(id) ? 'already_in_base' : union.has(id) ? 'graph_rescued' : 'graph_only';
  const bundle = p => [...new Set((p.steps ?? [p]).map(s => s.support_claim_id))];
  const add = (ids, reason, quota) => {
    const fresh = ids.filter(id => !selected.has(id));
    if (fresh.length > quota || promotions.length + fresh.length > allowance) return false;
    for (const id of fresh) {
      selected.add(id);
      const item = { id, score: base.find(x => x.id === id)?.score ?? 0,
        graph_origin: reason.channel === 'graph_definition_anchor' ? 'definition_anchor' : category(id), reasons: [reason] };
      head.push(item); promotions.push(item);
    }
    return true;
  };
  for (const anchor of anchors.slice(0, 2)) {
    if (add([anchor.id], { channel: 'graph_definition_anchor', ...anchor.reasons?.[0] }, allowance)) acceptedAnchors.push(anchor);
    else deferred.push({ id: anchor.id, reason: 'graph_admission_budget_exhausted' });
  }
  // Stable per-root round robin after sorting paths by novelty and seed rank.
  const order = list => {
    const groups = new Map();
    for (const p of [...list].sort((a, b) =>
      Number(bundle(b).some(id => category(id) === 'graph_only')) - Number(bundle(a).some(id => category(id) === 'graph_only')) ||
      (a.seed_rank ?? Infinity) - (b.seed_rank ?? Infinity) || a.path_id.localeCompare(b.path_id))) {
      const root = p.concept_path[0]; if (!groups.has(root)) groups.set(root, []); groups.get(root).push(p);
    }
    const result = [];
    while ([...groups.values()].some(g => g.length)) for (const g of groups.values()) if (g.length) result.push(g.shift());
    return result;
  };
  const accepted = new Set();
  const acceptPaths = (list, quota) => {
    let spent = 0;
    for (const p of order(list)) {
      const before = promotions.length;
      if (add(bundle(p), { channel: 'supported_graph_expansion', path_id: p.path_id, depth: p.depth }, quota - spent)) accepted.add(p.path_id);
      spent += promotions.length - before;
    }
  };
  acceptPaths(paths, allowance - promotions.length);
  for (const p of paths) if (!accepted.has(p.path_id)) deferred.push({ id: p.path_id, reason: 'whole_path_promotion_deferred' });
  const tail = base.filter(x => !selected.has(x.id));
  return { ranked: [...head, ...tail].slice(0, request.candidateBudget), headCount: head.length,
    protectedIds: [...baseIds], paths: paths.filter(p => accepted.has(p.path_id)), anchors: acceptedAnchors,
    trace: { capacity, text_protected: baseIds.size, graph_allowance: allowance, selection_policy: 'shared_pool_no_hop_reservations', promoted: promotions.map(x => ({ id: x.id, origin: x.graph_origin })),
      graph_only: promotions.filter(x => x.graph_origin === 'graph_only').length,
      graph_rescued: promotions.filter(x => x.graph_origin === 'graph_rescued').length,
      definition_anchors: promotions.filter(x => x.graph_origin === 'definition_anchor').length,
      rerank_input_ids: head.map(x => x.id), deferred,
      reason: allowance ? null : 'graph_admission_budget_exhausted' } };
}
