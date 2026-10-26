import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { EmbeddingModel } from './embedding.mjs';
import { sha256 } from './corpus.mjs';
export class DenseIndex {
  constructor(indexPath, modelPath, settings) {
    this.settings = settings;
    const vectorPath = resolve(indexPath, 'vectors.f32'), rowPath = resolve(indexPath, 'vector-rows.json');
    if (sha256(vectorPath) !== settings.vectors_sha256 || sha256(rowPath) !== settings.rows_sha256) throw Object.assign(new Error('Vector matrix/row checksum mismatch'), { code: 'INDEX_CORRUPT' });
    this.model = new EmbeddingModel(modelPath, settings.dtype);
    if (this.model.manifestSha256 !== settings.model_manifest_sha256) throw Object.assign(new Error('Embedding revision differs from indexed model'), { code: 'INDEX_STALE' });
    this.rows = JSON.parse(readFileSync(rowPath, 'utf8'));
    this.bytes = readFileSync(vectorPath);
    this.matrix = new Float32Array(this.bytes.buffer, this.bytes.byteOffset, this.bytes.byteLength / 4);
    if (settings.dimensions !== 512 || this.matrix.length !== settings.unique_vectors * 512 || this.rows.length !== settings.text_rows) throw Object.assign(new Error('Vector shape mismatch'), { code: 'INDEX_CORRUPT' });
    for (const row of this.rows) if (!Number.isInteger(row.vector_row) || row.vector_row < 0 || row.vector_row >= settings.unique_vectors) throw Object.assign(new Error('Vector reference outside matrix'), { code: 'INDEX_CORRUPT' });
  }
  async search(query, { mode, limit, accept, instruction = true }) {
    const encoded = await this.model.encode([query], { query: true, instruction });
    const q = encoded.vectors[0], scores = new Map(), grouped = new Map();
    for (const row of this.rows) {
      if (mode === 'source' ? row.kind !== 'source' : row.kind === 'source' || mode === 'knowledge' && row.review_status !== 'reviewed') continue;
      if (!accept(row)) continue;
      let score = scores.get(row.vector_row);
      if (score === undefined) {
        score = 0; const start = row.vector_row * 512;
        for (let i = 0; i < 512; i++) score += q[i] * this.matrix[start + i];
        scores.set(row.vector_row, score);
      }
      const id = mode === 'source' ? row.passage_id : row.claim_id;
      if (!grouped.has(id) || score > grouped.get(id).score) grouped.set(id, { id, score,
        reasons: [{ channel: 'semantic_vector', score, document_kind: row.kind, evidence_id: row.evidence_id, passage_id: row.passage_id,
          window_start: row.window_start, window_end: row.window_end, offset_basis: row.offset_basis, model_revision: this.model.manifest.revision }] });
    }
    const results = [...grouped.values()].sort((a, b) => b.score - a.score || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)).slice(0, limit);
    return { results, query_tokens: encoded.input_lengths[0], query_truncated: encoded.truncated[0], query_instruction_enabled: instruction };
  }
  async close() { await this.model.close(); }
}
