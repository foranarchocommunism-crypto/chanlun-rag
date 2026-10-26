import assert from 'node:assert/strict';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256 } from '../src/corpus.mjs';
const read = p => JSON.parse(readFileSync(p, 'utf8'));
const root = resolve('.'), run = resolve('build/formal-release');
const tap = readFileSync(resolve(run, 'tests-final.tap'), 'utf8');
const count = key => Number(tap.match(new RegExp(`^# ${key} (\\d+)$`, 'm'))?.[1]);
assert.ok(count('tests') >= 116); assert.equal(count('pass'), count('tests')); assert.equal(count('fail'), 0); assert.equal(count('skipped'), 0);
const knowledge = read(resolve(run, 'knowledge-integrity.json')), canonical = read(resolve(run, 'canonical-validation.json'));
assert.equal(knowledge.pass, true); assert.equal(knowledge.canonical_unchanged, true); assert.equal(canonical.pass, true);
const value = read(resolve(run, 'graph-value-final/metrics.json')); assert.equal(value.completed, true); assert.equal(value.cases, 240);
assert.equal(read(resolve(run, 'definition-and-fallback.json')).pass, true);
for (const [n, hash] of Object.entries(value.inputs.code)) assert.equal(sha256(resolve('src', n)), hash, n);
const paths = [];
const walk = folder => { for (const e of readdirSync(folder, { withFileTypes: true })) { const p = resolve(folder, e.name); if (e.isDirectory()) walk(p); else paths.push(p); } };
for (const folder of ['src', 'bin', 'contracts', 'profiles', 'policies']) walk(resolve(folder));
for (const file of ['package.json', 'package-lock.json', 'AGENT_GUIDE.md', 'scripts/package-portable.mjs', 'scripts/verify-portable.mjs', 'scripts/build-index.mjs', 'scripts/build-vectors.mjs', 'scripts/lib/durable-files.mjs']) paths.push(resolve(file));
for (const file of ['retrieval-contract.md', 'MAINTENANCE.md', 'agent-answer-examples.md', 'COMPATIBILITY.md', 'graph-v2.md', 'fixed-release.md', 'portable-readme.md']) paths.push(resolve('docs', file));
const service = new RetrievalService();
try {
  paths.push(resolve(service.paths.indexPath, 'manifest.json'), service.graph.path, resolve(service.paths.kbPath, 'manifest.json'));
  assert.equal(service.indexProblem, null); assert.equal(service.denseProblem, null);
  assert.equal(sha256(service.paths.profilePath), value.inputs.profile);
  assert.equal(sha256(resolve(service.paths.indexPath, 'manifest.json')), value.inputs.index);
  const result = { passed: true, product_version: read('package.json').version, scope: 'fixed-corpus Windows x64 engineering release',
    tests: { total: count('tests'), passed: count('pass'), failed: 0, skipped: 0 },
    knowledge_integrity: true, interruption_recovery: true, controlled_graph_fallback: true, trace_and_queue_limits: true,
    graph_quality: { independent_semantic_acceptance: false, overall_unique_gain_claimed: false, two_hop_special_gate: 'retired_by_user' },
    current_default_profile: service.profile.default_profile,
    evidence: Object.fromEntries(['tests-final.tap', 'knowledge-integrity.json', 'canonical-validation.json', 'graph-value-final/metrics.json', 'definition-and-fallback.json'].map(p => [p, sha256(resolve(run, p))])),
    inputs: Object.fromEntries(paths.sort().map(p => [relative(root, p).replaceAll('\\', '/'), sha256(p)])),
    artifact_execution: 'Required after packaging and again after fresh ZIP extraction; external receipt records it' };
  writeFileSync(resolve(run, 'gates.json'), JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify({ passed: true, version: result.product_version, tests: result.tests }));
} finally { await service.close(); }
