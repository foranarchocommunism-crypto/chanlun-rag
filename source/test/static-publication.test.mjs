import assert from 'node:assert/strict';
import { test, after } from 'node:test';
import { DatabaseSync } from 'node:sqlite';
import { mkdtempSync, cpSync, writeFileSync, readFileSync, statSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256 } from '../src/corpus.mjs';
import { fakeService } from './fixtures/graph-v2-fixture.mjs';

const root = mkdtempSync(resolve(tmpdir(), 'chan-static-release-'));
const kb = resolve(root, 'kb'), policy = resolve('test/fixtures/lifecycle/policy.json');
cpSync('test/fixtures/lifecycle/kb', kb, { recursive: true });
after(() => { assert.ok(root.startsWith(resolve(tmpdir()) + sep + 'chan-static-release-')); rmSync(root, { recursive: true, force: true }); });
const read = path => JSON.parse(readFileSync(path, 'utf8'));
const run = (script, args = [], preload) => spawnSync(process.execPath,
  [...(preload ? ['--import', pathToFileURL(preload).href] : []), script, ...args],
  { cwd: resolve('.'), encoding: 'utf8', windowsHide: true, timeout: 120000, maxBuffer: 4e6 });
const build = (path, preload) => run('scripts/build-index.mjs', ['--kb', kb, '--policy', policy, '--output', path], preload);
const vectors = (path, preload) => run('scripts/build-vectors.mjs', ['--index', path], preload);
const ok = r => assert.equal(r.status, 0, r.stderr);
function crashAt(name, body) {
  const path = resolve(root, name + '.mjs');
  writeFileSync(path, `import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const rename=fs.renameSync;let n=0;fs.renameSync=function(from,to){${body};return rename.call(this,from,to);};syncBuiltinESMExports();`);
  return path;
}

test('WAL-mode canonical snapshots are rejected even when main-file hashes match', () => {
  const copy = resolve(root, 'wal-kb'); cpSync(kb, copy, { recursive: true });
  const writer = new DatabaseSync(resolve(copy, 'graph.sqlite'));
  try {
    writer.exec('PRAGMA journal_mode=WAL; PRAGMA wal_autocheckpoint=0');
    const before = sha256(resolve(copy, 'graph.sqlite'));
    writer.prepare('UPDATE claims SET text=? WHERE id=?').run('unpublished WAL text', 'audit-claim-00');
    assert.equal(sha256(resolve(copy, 'graph.sqlite')), before);
    assert.throws(() => new RetrievalService({ kbPath: copy, policyPath: policy }), e => e.code === 'INDEX_STALE');
  } finally { writer.close(); }
  assert.throws(() => new RetrievalService({ kbPath: copy, policyPath: policy }), e => e.code === 'INDEX_STALE');
});

test('projection interruption leaves no published directory; retry publishes a valid immutable snapshot', () => {
  const out = resolve(root, 'projection');
  const crash = crashAt('projection-crash', `if(String(to).endsWith('manifest.json'))process.exit(91)`);
  assert.equal(build(out, crash).status, 91); assert.equal(existsSync(out), false);
  ok(build(out)); const first = sha256(resolve(out, 'projection.sqlite'));
  ok(build(out)); assert.equal(sha256(resolve(out, 'projection.sqlite')), first);
  assert.equal(read(resolve(out, 'manifest.json')).projection_sha256, first);
});

test('vector fsync/checkpoint interruption verifies prefix, truncates uncommitted tail and resumes identically', () => {
  const out = resolve(root, 'vectors'), clean = resolve(root, 'clean');
  ok(build(out)); ok(build(clean));
  const crash = crashAt('checkpoint-crash', `if(String(to).endsWith('vector-progress.json')&&++n===3)process.exit(92)`);
  assert.equal(vectors(out, crash).status, 92);
  assert.equal(read(resolve(out, 'vector-progress.json')).next, 12);
  assert.equal(statSync(resolve(out, 'vectors.f32')).size / 2048, 24);
  ok(vectors(out)); ok(vectors(clean));
  assert.equal(sha256(resolve(out, 'vectors.f32')), sha256(resolve(clean, 'vectors.f32')));
  assert.equal(sha256(resolve(out, 'vector-rows.json')), sha256(resolve(clean, 'vector-rows.json')));
  const manifest = sha256(resolve(out, 'manifest.json')); ok(vectors(out));
  assert.equal(sha256(resolve(out, 'manifest.json')), manifest);
});

test('partial temporary manifest never replaces usable manifest, and retry completes', () => {
  const out = resolve(root, 'manifest'); ok(build(out));
  const previous = sha256(resolve(out, 'manifest.json'));
  const crash = crashAt('manifest-crash', `if(String(to).endsWith('manifest.json')){fs.writeFileSync(from,'{"interrupted":');process.exit(93)}`);
  assert.equal(vectors(out, crash).status, 93);
  assert.equal(sha256(resolve(out, 'manifest.json')), previous);
  assert.equal(read(resolve(out, 'manifest.json')).build_status, 'validated');
  ok(vectors(out)); assert.ok(read(resolve(out, 'manifest.json')).models.embedding);
});

test('a damaged committed vector prefix is rejected, not silently resumed', () => {
  const out = resolve(root, 'corrupt'); ok(build(out));
  const crash = crashAt('corrupt-crash', `if(String(to).endsWith('vector-progress.json')&&++n===3)process.exit(94)`);
  assert.equal(vectors(out, crash).status, 94);
  const path = resolve(out, 'vectors.f32'), bytes = readFileSync(path); bytes[0] ^= 255; writeFileSync(path, bytes);
  const result = vectors(out); assert.equal(result.status, 1); assert.match(result.stderr, /Committed vector checksum mismatch/);
  assert.equal(read(resolve(out, 'manifest.json')).models.embedding, undefined);
});

test('queue capacity and wait deadline reject excess work and skip expired tasks', async () => {
  const s = fakeService(); s.profile.resources = { queue_capacity: 2, queue_wait_ms_max: 30 };
  let release, calls = 0; const gate = new Promise(r => { release = r; });
  s.retrieveInternal = async () => { calls++; await gate; return 'ok'; };
  const first = s.retrieve({}); await Promise.resolve();
  const waiting = s.retrieve({});
  await assert.rejects(s.retrieve({}), e => e.code === 'RESOURCE_BUSY');
  await assert.rejects(waiting, e => e.code === 'QUEUE_TIMEOUT');
  release(); assert.equal(await first, 'ok'); await s.queue;
  assert.equal(calls, 1); assert.equal(await s.retrieve({}), 'ok');
});

test('Windows transient rename denial retries without deleting the last valid file', { skip: process.platform !== 'win32' }, () => {
  const target = resolve(root, 'retry.json'), script = resolve(root, 'rename-retry.mjs');
  writeFileSync(target, '{"version":1}');
  writeFileSync(script, `import fs from 'node:fs';import assert from 'node:assert/strict';import {syncBuiltinESMExports} from 'node:module';
    const target=${JSON.stringify(target)}, rename=fs.renameSync;let n=0;fs.renameSync=function(from,to){
    if(to===target&&n++<3){assert.equal(JSON.parse(fs.readFileSync(target)).version,1);throw Object.assign(Error('scanner temporarily holds destination'),{code:'EPERM'});}
    return rename.call(this,from,to);};syncBuiltinESMExports();
    const {atomicJson}=await import(${JSON.stringify(pathToFileURL(resolve('scripts/lib/durable-files.mjs')).href)});
    atomicJson(target,{version:2});assert.equal(n,4);assert.equal(JSON.parse(fs.readFileSync(target)).version,2);`);
  ok(run(script));
});

test('trace binds effective request, full stage rankings, source reasons and current artifact hashes', async () => {
  const s = new RetrievalService();
  try {
    const p = await s.retrieve({ query: '中枢的成立条件', profile: 'hybrid-rerank', rerankBudget: 20, limit: 2, trace: true });
    assert.equal(p.runtime.effective_request.trace, true);
    assert.equal(p.runtime.identity.canonical, sha256(s.graph.path));
    assert.equal(p.runtime.identity.code['retrieval.mjs'], sha256('src/retrieval.mjs'));
    assert.ok(p.runtime.rankings.dense.length && p.runtime.rankings.reranked.length);
    const dense = p.runtime.rankings.text_fusion.flatMap(r => r.reasons).find(r => r.channel === 'semantic_vector');
    assert.ok(dense.source_reasons.length);
  } finally { await s.close(); }
});
