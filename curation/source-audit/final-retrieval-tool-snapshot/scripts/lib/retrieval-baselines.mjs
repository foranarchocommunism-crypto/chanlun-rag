// Evaluation-only retrieval. No graph mutation and no gold-aware query rewriting.
export function tokenize(text) {
  const result = new Set();
  for (const match of String(text).normalize('NFKC').toLowerCase().matchAll(/[\p{Script=Han}]+|[a-z]+|\d+(?:\.\d+)?/gu)) {
    const word = match[0];
    if (/^\p{Script=Han}+$/u.test(word)) {
      const chars = [...word];
      // Chinese unigrams are deliberately omitted: two-character terms remain searchable.
      for (const n of [2, 3]) for (let i = 0; i <= chars.length - n; i++) result.add(chars.slice(i, i + n).join(''));
    } else result.add(word);
  }
  return [...result];
}

export class LexicalIndex {
  constructor(documents) {
    this.documents = new Map();
    this.postings = new Map();
    let lengthSum = 0;
    for (const doc of documents) {
      if (this.documents.has(doc.id)) throw new Error(`Duplicate index ID: ${doc.id}`);
      const terms = tokenize(doc.text);
      this.documents.set(doc.id, { length: terms.length, doc });
      lengthSum += terms.length;
      for (const term of terms) {
        if (!this.postings.has(term)) this.postings.set(term, []);
        this.postings.get(term).push(doc.id);
      }
    }
    this.averageLength = lengthSum / Math.max(1, documents.length);
  }

  search(query, limit) {
    const scores = new Map(), n = this.documents.size;
    // Binary term frequency avoids rewarding repeated/duplicated paragraphs or metadata.
    const k1 = 1.2, b = 0.75;
    for (const term of tokenize(query)) {
      const hits = this.postings.get(term) ?? [];
      const idf = Math.log(1 + (n - hits.length + 0.5) / (hits.length + 0.5));
      for (const id of hits) {
        const length = this.documents.get(id).length;
        const contribution = idf * (k1 + 1) / (1 + k1 * (1 - b + b * length / Math.max(1, this.averageLength)));
        scores.set(id, (scores.get(id) ?? 0) + contribution);
      }
    }
    return [...scores].map(([id, score]) => ({ id, score }))
      .sort((a, b) => b.score - a.score || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)).slice(0, limit);
  }
}

export function uniquePassages(rankedClaims, evidenceByClaim, limit) {
  const seen = new Set(), result = [];
  for (const claim of rankedClaims) {
    for (const id of evidenceByClaim.get(claim.id) ?? []) {
      if (seen.has(id)) continue;
      seen.add(id); result.push({ id, score: claim.score, claim_id: claim.id });
      if (result.length === limit) return result;
    }
  }
  return result;
}

export function reciprocalRankFusion(channels, limit, constant = 60) {
  const scores = new Map();
  for (const channel of channels) {
    const seen = new Set(); let rank = 0;
    for (const item of channel) {
      if (seen.has(item.id)) continue;
      seen.add(item.id); rank++;
      scores.set(item.id, (scores.get(item.id) ?? 0) + 1 / (constant + rank));
    }
  }
  return [...scores].map(([id, score]) => ({ id, score }))
    .sort((a, b) => b.score - a.score || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)).slice(0, limit);
}

export function rankedMetrics(ranked, relevant, k) {
  const gold = new Set(relevant);
  if (!gold.size) return null;
  const ids = [...new Set(ranked.map(x => typeof x === 'string' ? x : x.id))].slice(0, k);
  const ranks = ids.flatMap((id, i) => gold.has(id) ? [i + 1] : []);
  const dcg = ranks.reduce((sum, rank) => sum + 1 / Math.log2(rank + 1), 0);
  const idcg = Array.from({ length: Math.min(k, gold.size) }, (_, i) => 1 / Math.log2(i + 2)).reduce((a, b) => a + b, 0);
  return { recall: ranks.length / gold.size, annotated_precision_lower_bound: ranks.length / k,
    reciprocal_rank: ranks.length ? 1 / ranks[0] : 0, ndcg_binary: dcg / idcg,
    hit: Number(ranks.length > 0), all_annotated_evidence_found: Number(ranks.length === gold.size),
    annotated_hits: ranks.length, returned: ids.length, annotated_gold_count: gold.size };
}
