// A general query-intent rule over actual concept aliases and structural graph supports.
// It promotes sourced definition candidates, not a case-ID whitelist or truth verdict.
const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export function definitionAnchors(corpus, query, eligible, budget = 2, { guard = () => {}, consume = () => true } = {}) {
  const q = query.normalize('NFKC').toLowerCase(), result = new Map();
  concepts: for (const concept of corpus.concepts.values()) {
    guard();
    const aliases = [concept.label, ...concept.aliases].map(x => x.normalize('NFKC').toLowerCase());
    const asksDefinition = aliases.some(alias => new RegExp(`(?:什么是\\s*${escape(alias)}|${escape(alias)}(?:的)?(?:是什么|如何定义|怎样定义|定义))`, 'u').test(q));
    if (!asksDefinition) continue;
    for (const r of corpus.relations) {
      guard(); if (!consume('edges')) break concepts;
      if (r.review_status !== 'reviewed' || r.source !== concept.id || !['defines', 'requires', 'composed_of'].includes(r.type)) continue;
      for (const id of r.claim_ids) {
        guard(); if (!consume('supports')) break concepts;
        const c = corpus.claims.get(id);
        if (!eligible(c) || c.kind !== 'explicit') continue;
        const head = c.text.normalize('NFKC').toLowerCase();
        if (!aliases.some(alias => new RegExp(`^${escape(alias)}(?:是|指|定义为|包括|分为)`, 'u').test(head))) continue;
        const existing = result.get(id) ?? { id, score: 0, relations: [], reasons: [{ channel: 'graph_definition_anchor', concept_id: concept.id,
          reason: 'Explicit definition query + subject-predicate wording + reviewed structural graph support; relevance only' }] };
        existing.relations.push(r); existing.score = existing.relations.length; result.set(id, existing);
      }
    }
  }
  return [...result.values()].sort((a, b) => b.score - a.score || a.id.localeCompare(b.id)).slice(0, budget);
}
