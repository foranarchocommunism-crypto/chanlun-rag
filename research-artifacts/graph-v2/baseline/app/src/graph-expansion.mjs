// Bounded association discovery. Original direction is preserved, never converted to entailment.
export function expandGraph(corpus, seeds, request, eligible) {
  if (!request.graphDepth || !request.graphBudget || request.mode === 'source') return { additions: [], paths: [], truncated: false };
  const included = new Set(seeds.slice(0, request.limit).map(x => x.id)), additions = [], paths = [], visitedRelations = new Set();
  const seedRank = new Map(seeds.map((s, i) => [s.id, i]));
  const query = request.query.normalize('NFKC').toLowerCase();
  const mentioned = new Set([...corpus.concepts.values()].filter(c => [c.label, ...c.aliases].some(t => query.includes(t.normalize('NFKC').toLowerCase()))).map(c => c.id));
  const relationPriority = r => (mentioned.has(r.source) ? 1000 : 0) + (mentioned.has(r.target) ? 1000 : 0) +
    Math.max(...r.claim_ids.map(id => 100 - (seedRank.get(id) ?? 100)), 0);
  const orderedRelations = [...corpus.relations].sort((a, b) => relationPriority(b) - relationPriority(a) || a.id.localeCompare(b.id));
  let frontier = new Map();
  for (const seed of seeds.slice(0, 5)) for (const concept of corpus.claims.get(seed.id)?.concept_ids ?? []) {
    if (!frontier.has(concept)) frontier.set(concept, { seed_claim_id: seed.id, nodes: [concept], relation_ids: [] });
  }
  let truncated = false;
  for (let depth = 1; depth <= request.graphDepth; depth++) {
    const next = new Map();
    for (const r of orderedRelations) {
      if (visitedRelations.has(r.id) || r.review_status !== 'reviewed' && !(request.mode === 'research' && r.review_status === 'pending')) continue;
      const from = frontier.has(r.source) ? r.source : frontier.has(r.target) ? r.target : null;
      if (!from) continue;
      const to = from === r.source ? r.target : r.source;
      const prior = frontier.get(from), direction = from === r.source ? 'source_to_target' : 'target_to_source_association_only';
      const support = r.claim_ids.filter(id => eligible(corpus.claims.get(id)) && (corpus.evidenceByClaim.get(id)?.length ?? 0) > 0);
      if (!support.length) continue;
      for (const id of support) {
        if (paths.length >= request.graphBudget) { truncated = true; break; }
        const path = { relation_id: r.id, relation_type: r.type, source: r.source, target: r.target, traversal_direction: direction,
          original_review_status: r.review_status, supporting_claim_ids: support, support_claim_id: id,
          support_evidence_ids: corpus.evidenceByClaim.get(id).map(e => e.id), seed_claim_id: prior.seed_claim_id,
          depth, concept_path: [...prior.nodes, to], relation_path: [...prior.relation_ids, r.id],
          semantics: 'evidence_supported_association_not_transitive_inference', depends_on_interpretation: false };
        paths.push(path);
        if (!included.has(id)) { additions.push({ id, score: 0, reasons: [{ channel: 'supported_graph_expansion', relation_id: r.id, depth }] }); included.add(id); }
      }
      visitedRelations.add(r.id);
      if (!next.has(to)) next.set(to, { seed_claim_id: prior.seed_claim_id, nodes: [...prior.nodes, to], relation_ids: [...prior.relation_ids, r.id] });
      if (paths.length >= request.graphBudget) break;
    }
    frontier = next;
    if (paths.length >= request.graphBudget) { truncated = true; break; }
  }
  return { additions, paths, truncated };
}
