// Production equivalent of the frozen structured lexical baseline.
// Binary TF, Han 2/3-grams and deterministic ties preserve the development comparison.
export function tokenize(text) {
  const terms = new Set();
  for (const match of String(text).normalize('NFKC').toLowerCase().matchAll(/[\p{Script=Han}]+|[a-z]+|\d+(?:\.\d+)?/gu)) {
    const word = match[0];
    if (/^\p{Script=Han}+$/u.test(word)) {
      const chars = [...word];
      for (const n of [2, 3]) for (let i = 0; i <= chars.length - n; i++) terms.add(chars.slice(i, i + n).join(''));
    } else terms.add(word);
  }
  return [...terms];
}
export class LexicalIndex {
  constructor(documents) {
    this.documents = new Map(); this.postings = new Map();
    let total = 0;
    for (const doc of documents) {
      if (this.documents.has(doc.id)) throw new Error(`Duplicate index ID: ${doc.id}`);
      const terms = tokenize(doc.text);
      this.documents.set(doc.id, { length: terms.length, doc }); total += terms.length;
      for (const term of terms) { if (!this.postings.has(term)) this.postings.set(term, []); this.postings.get(term).push(doc.id); }
    }
    this.averageLength = total / Math.max(1, documents.length);
  }
  search(query, limit, accept = () => true) {
    const scores = new Map(), n = this.documents.size, k1 = 1.2, b = 0.75;
    for (const term of tokenize(query)) {
      const hits = this.postings.get(term) ?? [];
      const idf = Math.log(1 + (n - hits.length + 0.5) / (hits.length + 0.5));
      for (const id of hits) {
        if (!accept(this.documents.get(id).doc)) continue;
        const length = this.documents.get(id).length;
        scores.set(id, (scores.get(id) ?? 0) + idf * (k1 + 1) / (1 + k1 * (1 - b + b * length / Math.max(1, this.averageLength))));
      }
    }
    return [...scores].map(([id, score]) => ({ id, score }))
      .sort((a, b) => b.score - a.score || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)).slice(0, limit);
  }
}
export function fuse(channels, limit, constant = 60) {
  const values = new Map();
  for (const { name, weight = 1, results } of channels) {
    const seen = new Set(); let rank = 0;
    for (const result of results) {
      if (seen.has(result.id)) continue;
      seen.add(result.id); rank++;
      const value = values.get(result.id) ?? { id: result.id, score: 0, reasons: [] };
      value.score += weight / (constant + rank);
      value.reasons.push({ channel: name, rank, score: result.score, source_reasons: structuredClone(result.reasons ?? []) }); values.set(result.id, value);
    }
  }
  return [...values.values()].sort((a, b) => b.score - a.score || a.id.localeCompare(b.id, 'en')).slice(0, limit);
}
