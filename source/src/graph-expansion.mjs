// Bounded association discovery. Original direction is preserved, never converted to entailment.
export const GRAPH_LIMITS = Object.freeze({ seeds: 8, fanout: 4, adjacencyReads: 32, nodes: 64, edges: 512, supports: 1024, deadlineMs: 100 });
export function graphFailure(code, message, details = {}) {
  return Object.assign(new Error(message), { code, stage: 'graph', details });
}
export function graphGuard({ clock = () => performance.now(), signal, start = clock() } = {}) {
  return () => {
    signal?.throwIfAborted();
    if (clock() - start >= GRAPH_LIMITS.deadlineMs) throw graphFailure('GRAPH_TIMEOUT', 'Optional graph stage exceeded its deadline');
  };
}
export function buildGraphView(corpus, guard = () => {}) {
  const adjacency = new Map();
  for (const r of corpus.relations) {
    guard();
    for (const id of new Set([r.source, r.target])) {
      if (!adjacency.has(id)) adjacency.set(id, []);
      adjacency.get(id).push({ ...r, claim_ids: [...r.claim_ids].sort() });
    }
  }
  for (const edges of adjacency.values()) { guard(); edges.sort((a, b) => a.id.localeCompare(b.id)); }
  return adjacency;
}
export function expandGraphV2(corpus, seeds, request, eligible, { view, guard = () => {} } = {}) {
  const trace = { status: 'empty', reason: null, attempted_depth: 0, completed_depth: 0, edge_reads: 0, support_checks: 0,
    nodes: 0, seed_nodes: 0, hop1_paths: 0, hop2_paths: 0, max_adjacency_reads: 0, max_fanout: 0, truncation_reasons: [] };
  const result = paths => ({ additions: [...new Set(paths.flatMap(p => p.steps.map(s => s.support_claim_id)))].map(id => ({ id, score: 0 })),
    paths, truncated: trace.truncation_reasons.length > 0, trace });
  if (request.mode === 'source' || !request.graphDepth || !request.graphBudget || corpus.claims.has(request.query)) {
    trace.status = 'skipped'; trace.reason = request.mode === 'source' ? 'source_mode' : corpus.claims.has(request.query) ? 'exact_claim' : 'graph_disabled'; return result([]);
  }
  const rank = new Map(seeds.map((s, i) => [s.id, i + 1])), q = request.query.normalize('NFKC').toLowerCase();
  const roots = [...corpus.concepts.values()].filter(c => c.id === request.conceptId || [c.label, ...c.aliases].some(x => x && q.includes(x.normalize('NFKC').toLowerCase())))
    .map(c => { const seed = seeds.find(s => corpus.claims.get(s.id)?.concept_ids.includes(c.id)); return { node: c.id, nodes: [c.id], steps: [], seed: seed?.id ?? null, rank: rank.get(seed?.id) ?? Number.MAX_SAFE_INTEGER }; })
    .sort((a, b) => Number(b.node === request.conceptId) - Number(a.node === request.conceptId) || a.rank - b.rank || a.node.localeCompare(b.node));
  if (!roots.length) { trace.status = 'skipped'; trace.reason = 'no_query_anchor'; return result([]); }
  const mark = reason => { if (!trace.truncation_reasons.includes(reason)) trace.truncation_reasons.push(reason); };
  if (roots.length > GRAPH_LIMITS.seeds) mark('seed_limit');
  const frontier = roots.slice(0, GRAPH_LIMITS.seeds), visitedNodes = new Set(frontier.map(f => f.node));
  trace.seed_nodes = frontier.length;
  view ??= buildGraphView(corpus, guard);
  const depth = request.graphBudget < 2 ? 1 : request.graphDepth;
  if (depth < request.graphDepth) trace.reason = 'path_budget_requires_depth1';
  const layer = (states, level) => {
    trace.attempted_depth = level;
    const grouped = new Map(), pool = [], pathIds = new Set();
    for (const s of states) { if (!grouped.has(s.node)) grouped.set(s.node, { states: [], cursor: 0, neighbors: new Set() }); grouped.get(s.node).states.push(s); }
    let active = true;
    while (active) {
      active = false;
      for (const [node, work] of grouped) {
        guard(); const edges = view.get(node) ?? [];
        if (work.cursor >= edges.length) continue;
        if (work.cursor >= GRAPH_LIMITS.adjacencyReads) { mark('adjacency_limit'); continue; }
        if (work.neighbors.size >= GRAPH_LIMITS.fanout) { mark('fanout_limit'); continue; }
        if (trace.edge_reads >= GRAPH_LIMITS.edges || trace.support_checks >= GRAPH_LIMITS.supports) { mark(trace.edge_reads >= GRAPH_LIMITS.edges ? 'edge_limit' : 'support_limit'); return pool; }
        active = true; const r = edges[work.cursor++]; trace.edge_reads++;
        trace.max_adjacency_reads = Math.max(trace.max_adjacency_reads, work.cursor);
        if (r.review_status !== 'reviewed' && !(request.mode === 'research' && r.review_status === 'pending')) continue;
        const to = r.source === node ? r.target : r.source;
        if (work.neighbors.has(to) || !work.states.some(s => !s.nodes.includes(to))) continue;
        if (!visitedNodes.has(to) && visitedNodes.size >= GRAPH_LIMITS.nodes) { mark('node_limit'); continue; }
        const support = [];
        for (const id of r.claim_ids) {
          guard(); if (trace.support_checks >= GRAPH_LIMITS.supports) { mark('support_limit'); break; }
          trace.support_checks++;
          if (eligible(corpus.claims.get(id)) && corpus.evidenceByClaim.get(id)?.length) support.push(id);
        }
        if (!support.length) continue;
        support.sort((a, b) => Number(corpus.claims.get(b).review_status === 'reviewed') - Number(corpus.claims.get(a).review_status === 'reviewed') ||
          (rank.get(a) ?? Infinity) - (rank.get(b) ?? Infinity) || a.localeCompare(b));
        const id = support[0], step = { relation_id: r.id, relation_type: r.type, source: r.source, target: r.target,
          traversal_direction: r.source === node ? 'source_to_target' : 'target_to_source_association_only', original_review_status: r.review_status,
          supporting_claim_ids: support, support_claim_id: id, support_review_status: corpus.claims.get(id).review_status, support_evidence_ids: corpus.evidenceByClaim.get(id).map(e => e.id) };
        work.neighbors.add(to); visitedNodes.add(to); trace.max_fanout = Math.max(trace.max_fanout, work.neighbors.size);
        for (const s of work.states) {
          guard(); if (s.nodes.includes(to)) continue;
          const steps = [...s.steps, step], nodes = [...s.nodes, to], path_id = `${nodes[0]}:${steps.map(x => x.relation_id).join('/')}`;
          if (pathIds.has(path_id)) continue; pathIds.add(path_id);
          pool.push({ ...step, path_id, steps, depth: level, concept_path: nodes, relation_path: steps.map(x => x.relation_id),
            seed_claim_id: s.seed, seed_rank: s.rank, semantics: 'evidence_supported_association_not_transitive_inference', depends_on_interpretation: false });
          if (pool.length >= 100) { mark('layer_candidate_limit'); trace.completed_depth = level; return pool; }
        }
      }
    }
    trace.completed_depth = level; return pool;
  };
  const firstPool = layer(frontier, 1);
  const next = firstPool.map(p => ({ node: p.concept_path.at(-1), nodes: p.concept_path, steps: p.steps, seed: p.seed_claim_id, rank: p.seed_rank }));
  const secondPool = depth === 2 && next.length ? layer(next, 2) : [];
  // Both depths compete in one pool under the same relevance proxy and stable ties.
  // Discovery is bounded independently; no hop has reserved output slots or a floor.
  const grouped = new Map(), selected = [];
  for (const p of [...firstPool, ...secondPool].sort((a, b) => a.seed_rank - b.seed_rank ||
    (rank.get(a.support_claim_id) ?? Infinity) - (rank.get(b.support_claim_id) ?? Infinity) || a.path_id.localeCompare(b.path_id))) {
    const root = p.concept_path[0]; if (!grouped.has(root)) grouped.set(root, []); grouped.get(root).push(p);
  }
  while (selected.length < request.graphBudget && [...grouped.values()].some(g => g.length)) {
    for (const g of grouped.values()) if (g.length && selected.length < request.graphBudget) selected.push(g.shift());
  }
  if (firstPool.length + secondPool.length > selected.length) mark('path_limit');
  trace.nodes = visitedNodes.size; trace.hop1_paths = selected.filter(p => p.depth === 1).length; trace.hop2_paths = selected.filter(p => p.depth === 2).length;
  trace.selection_policy = 'shared_pool_no_hop_reservations'; trace.hop1_discovered = firstPool.length; trace.hop2_discovered = secondPool.length;
  trace.status = trace.truncation_reasons.length ? 'budget_exhausted' : selected.length ? 'success' : 'empty';
  return result(selected);
}
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
