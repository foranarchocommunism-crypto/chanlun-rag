import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { createHash } from 'node:crypto';
import { existsSync, openSync, closeSync, readFileSync, writeSync, statSync, fsyncSync, ftruncateSync } from 'node:fs';
import { resolve } from 'node:path';
import { EmbeddingModel } from '../src/embedding.mjs';
import { sha256, windows } from '../src/corpus.mjs';
import { openStaticDatabase } from '../src/snapshot.mjs';
import { atomicWrite, atomicJson, acquireBuildLock, prefixHash } from './lib/durable-files.mjs';
const args = process.argv.slice(2), indexAt = args.indexOf('--index');
const root = resolve(indexAt < 0 ? 'indexes/lexical-1-307029129712' : args[indexAt + 1]);
const manifestPath = resolve(root, 'manifest.json');
const original = JSON.parse(readFileSync(manifestPath, 'utf8'));
assert.equal(original.projection_sha256, sha256(resolve(root, 'projection.sqlite')));
if (original.models.embedding) {
  assert.equal(original.models.embedding.vectors_sha256, sha256(resolve(root, 'vectors.f32')));
  assert.equal(original.models.embedding.rows_sha256, sha256(resolve(root, 'vector-rows.json')));
  console.log(JSON.stringify({ completed: true, reused: true }));
  process.exit(0);
}
const projection = openStaticDatabase(resolve(root, 'projection.sqlite'), original.projection_sha256);
const db = projection.db;
const documents = db.prepare('SELECT * FROM retrieval_documents ORDER BY id').all().flatMap(doc => {
  if (doc.kind === 'claim') return windows(doc.text, 350, 60).map((w, i) => ({ ...doc, id: `${doc.id}:w${i}`, text: w.text.normalize('NFKC'),
    window_start: w.start, window_end: w.end, offset_basis: 'structured_retrieval_text' }));
  const span = JSON.parse(doc.text);
  return [{ ...doc, text: span.text.normalize('NFKC'), window_start: span.start, window_end: span.end, offset_basis: 'canonical_passage_codepoints' }];
});
db.close();
const unique = [], vectorsByText = new Map();
const rows = documents.map(doc => {
  let index = vectorsByText.get(doc.text);
  if (index === undefined) { index = unique.length; unique.push(doc.text); vectorsByText.set(doc.text, index); }
  const { text, ...metadata } = doc; return { ...metadata, vector_row: index };
});
const model = new EmbeddingModel(resolve('models'));
const settings = { model_manifest_sha256: model.manifestSha256, projection_sha256: original.projection_sha256, dimensions: 512, dtype: 'q8', pooling: 'cls', normalize: true,
  query_instruction: model.manifest.query_instruction, input_normalization: 'NFKC', text_rows: rows.length, unique_vectors: unique.length,
  unique_text_hash: createHash('sha256').update(JSON.stringify(unique)).digest('hex') };
const file = resolve(root, 'vectors.f32'), progressFile = resolve(root, 'vector-progress.json');
const releaseLock = acquireBuildLock(resolve(root, 'vector-build.lock'));
let fd;
try {
  let next = 0;
  if (existsSync(progressFile)) {
    const progress = JSON.parse(readFileSync(progressFile, 'utf8'));
    assert.deepEqual(progress.settings, settings); next = progress.next;
    const committedBytes = next * 512 * 4;
    assert.ok(Number.isInteger(next) && next >= 0 && next <= unique.length);
    assert.ok(statSync(file).size >= committedBytes, 'Committed vectors are missing');
    assert.equal(prefixHash(file, committedBytes), progress.prefix_sha256, 'Committed vector checksum mismatch');
    fd = openSync(file, 'r+');
    ftruncateSync(fd, committedBytes); fsyncSync(fd);
  } else {
    assert.ok(!existsSync(file) || statSync(file).size === 0, 'Untracked vector file exists; inspect before replacing.');
    fd = openSync(file, existsSync(file) ? 'r+' : 'wx');
    atomicJson(progressFile, { settings, next: 0, total: unique.length, prefix_sha256: prefixHash(file, 0) });
  }
  const rolling = createHash('sha256').update(readFileSync(file));
  const start = performance.now(); let last = start;
  const batchSize = 12;
  for (let i = next; i < unique.length; i += batchSize) {
    const batch = unique.slice(i, i + batchSize), result = await model.encode(batch);
    assert.ok(!result.truncated.some(Boolean), `Document windows exceed tokenizer limit near ${i}`);
    const bytes = new Float32Array(result.vectors.length * 512);
    result.vectors.forEach((vector, j) => bytes.set(vector, j * 512));
    const buffer = Buffer.from(bytes.buffer);
    for (let written = 0; written < buffer.length;) written += writeSync(fd, buffer, written, buffer.length - written, i * 512 * 4 + written);
    fsyncSync(fd);
    rolling.update(buffer);
    const progress = { settings, next: i + batch.length, total: unique.length, prefix_sha256: rolling.copy().digest('hex'), updated_at: new Date().toISOString(), elapsed_ms_this_run: performance.now() - start };
    atomicJson(progressFile, progress);
    if (performance.now() - last > 10000 || progress.next === unique.length) { console.log(JSON.stringify({ embedded: progress.next, total: unique.length, elapsed_seconds: (performance.now() - start) / 1000, rss_bytes: process.memoryUsage().rss })); last = performance.now(); }
  }
  closeSync(fd); fd = undefined;
  atomicWrite(resolve(root, 'vector-rows.json'), JSON.stringify(rows));
  const manifest = { ...original, index_version: 'hybrid-1', models: { embedding: { ...settings, repo: model.manifest.repo, revision: model.manifest.revision,
    vectors_sha256: sha256(file), rows_sha256: sha256(resolve(root, 'vector-rows.json')), byte_order: 'little_endian', query_instruction_enabled: true } },
    vector_built_at: new Date().toISOString() };
  assert.equal(sha256(resolve(root, 'projection.sqlite')), original.projection_sha256);
  atomicJson(manifestPath, manifest);
  console.log(JSON.stringify({ completed: true, unique_vectors: unique.length, rows: rows.length, vector_bytes: statSync(file).size }));
} finally { if (fd !== undefined) closeSync(fd); await model.close(); releaseLock(); }
