import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { resolve, dirname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { sha256 } from '../src/corpus.mjs';

// Preserve the original quality receipts. Append current environment evidence;
// the original deferred-Windows decision no longer describes the delivery scope.
const agent = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const workspace = resolve(agent, '..');
const quality = resolve(workspace, 'validation-runs/agent-implementation-20261022');
const run = resolve(workspace, 'validation-runs/x64-delivery-20261023');
const seal = process.argv.includes('--seal-delivery');
assert.ok(process.argv.slice(2).every(arg => arg === '--seal-delivery'), 'Usage: node scripts/final-audit.mjs [--seal-delivery]');
const read = path => JSON.parse(readFileSync(path, 'utf8').replace(/^\uFEFF/, ''));
const old = name => read(resolve(quality, name));
const proof = path => ({ file: relative(workspace, path).replaceAll('\\', '/'), sha256: sha256(path) });
const zip = read(resolve(run, 'zip-build.json'));
const product = zip.archive.replace(/\.zip$/i, '');
assert.equal(dirname(resolve(zip.archive)), resolve(workspace, 'deliveries'));
const manifest = read(resolve(product, 'release-manifest.json'));
assert.equal(manifest.product_version, read(resolve(agent, 'package.json')).version);
assert.equal(sha256(zip.archive), zip.sha256); assert.equal(statSync(zip.archive).size, zip.bytes);
assert.equal(zip.crc_checked, true);
assert.deepEqual(manifest.compatibility.native_architectures, ['x64']);
const scope = read(resolve(run,'scope-change.json'));
assert.deepEqual(scope.required_architectures, ['x64']);
const requirements = [];
function check(id, description, files, validate) {
  const row = { id, description, passed: false, evidence: [] };
  try {
    for (const file of files) { assert.ok(existsSync(file), `Missing evidence: ${relative(workspace, file)}`); row.evidence.push(proof(file)); }
    validate(); row.passed = true;
  } catch (error) { row.error = error.message; }
  requirements.push(row);
}
const freeze = old('m6-profile-freeze.json');
check('canonical-and-freeze', 'Unchanged canonical inputs, retrieval sources, held-out cases and selected profile/index', [resolve(quality,'baseline.json'),resolve(quality,'m6-profile-freeze.json'),resolve(run,'frozen-retrieval-preserved.json')], () => {
  for (const [file, hash] of Object.entries(old('baseline.json').canonical_inputs)) assert.equal(sha256(resolve(workspace,file)), hash, file);
  for (const [file, hash] of Object.entries(freeze.source_files)) {
    // Only the version lookup changed after freeze; pin its exact reviewed bytes.
    const expected = file === 'bin/chan-kg-mcp.mjs' ? '203d606df620ef0e0430aac69eb1d4b9d9f7a49207b206747b1142c24d68b51b' : hash;
    assert.equal(sha256(resolve(agent,file)), expected, file);
    if (existsSync(resolve(product,'app',file))) assert.equal(sha256(resolve(product,'app',file)), expected, `packaged ${file}`);
  }
  assert.equal(sha256(resolve(agent,'evaluation/acceptance-v1/cases.jsonl')), freeze.heldout_cases_sha256);
  assert.equal(manifest.profile_sha256, freeze.profile_sha256);
  assert.equal(manifest.index_manifest_sha256, freeze.index_manifest_sha256);
});
const stages = [
  ['M0','Baseline, backups, scope, source-disjoint split and contracts',['baseline.json','m6-profile-freeze.json']],
  ['M1','473 reviewed ambiguities, 2611 pending, 3084-item triage, sourced alternatives and whole conditions',['pre-release-tests.log','retrieval-contract-current.log']],
  ['M2','240 lexical baseline matches and original-command compatibility',['m2-lexical-parity.json','pre-release-tests.log']],
  ['M3','Author encoder weights, offline FP32/q8 agreement, vector and fusion experiments',['m3-author-weights.json','m3-embedding-consistency.json','m3-hybrid-development.json']],
  ['M4','Supported graph paths, declared depth/weight/rerank ablations, alternatives and budgets',['m4-graph-development.json','m4-rerank-development.json','m4-production-development.json','pre-release-tests.log']],
  ['M5','Actual SDK MCP/CLI/JS equality, follow-up evidence and caller-agent examples',['m5-default-mcp-roundtrip.json','m5-agent-example-inputs.json','release-gates.json']],
  ['M6','Frozen quality, resources and source/condition/path gates, truthful annotation limits',['m6-prospective-acceptance.json','canonical-validation-direct.json','release-gates.json']],
];
for (const [id, description, names] of stages) check(id, description, names.map(name => resolve(quality,name)), () => {
  const gates = old('release-gates.json');
  for (const [file, hash] of Object.entries(gates.receipts)) assert.equal(sha256(resolve(quality,file)), hash, file);
  assert.equal(gates.local_release_gates_passed, true); assert.equal(gates.integrity_errors, 0);
  if (id === 'M2') assert.equal(old('m2-lexical-parity.json').exact_baseline_rank_score_matches, 240);
  if (id === 'M3') { assert.equal(old('m3-author-weights.json').used_encoder_parameter_element_coverage, 1); assert.equal(old('m3-embedding-consistency.json').passed, true); }
  if (id === 'M6') {
    const acceptance = old('m6-prospective-acceptance.json');
    for (const key of ['quality_comparison_passed','resource_passed','inputs_unchanged']) assert.equal(acceptance[key], true, key);
    assert.equal(acceptance.integrity_errors, 0); assert.equal(acceptance.independent_human_annotation, false);
    assert.equal(old('canonical-validation-direct.json').pass, true);
  }
});
function portable(file, arch) {
  const report = read(file); assert.equal(report.passed, true); assert.equal(report.environment.arch, arch);
  for (const name of ['all_file_checksums','status_from_bundled_runtime_isolated_PATH','architecture_aware_CLI_launcher','offline_default_retrieval','ambiguity_research_source_modes','native_dependencies_loaded_from_portable_runtime','bundled_MCP_JS_CLI_equality_and_evidence_followup','canonical_files_unchanged']) assert.equal(report.checks.find(item => item.name === name)?.passed, true, name);
  assert.equal(report.checks.find(item => item.name === 'architecture_aware_CLI_launcher').node_arch, arch);
  assert.equal(report.checks.find(item => item.name === 'bundled_MCP_JS_CLI_equality_and_evidence_followup').server_version, manifest.product_version);
}
check('M7-artifact', 'Current ZIP and directory, complete checksums, both runtimes, source checks, no desktop/development tree', [resolve(run,'zip-build.json'),resolve(product,'release-manifest.json'),resolve(run,'local-portable-verification.json'),resolve(run,'universal-source-tests.log')], () => {
  portable(resolve(run,'local-portable-verification.json'), 'x64');
  const tests = readFileSync(resolve(run,'universal-source-tests.log'), 'utf8');
  assert.match(tests, /(?:#|ℹ) fail 0/); assert.match(tests, /(?:#|ℹ) pass 47/);
  for (const entry of manifest.entrypoints) assert.ok(existsSync(resolve(product,entry)), entry);
  for (const name of ['app/curation','app/test','app/build','chan-kg-desktop','.git']) assert.equal(existsSync(resolve(product,name)), false, name);
  for (const arch of ['x64']) assert.equal(sha256(resolve(product,manifest.runtimes[arch].path)), manifest.runtimes[arch].sha256);
  assert.equal(existsSync(resolve(product,'runtime/arm64')), false);
  const sums = readFileSync(resolve(product,manifest.checksums_file), 'utf8').trim().split(/\r?\n/);
  for (const line of sums) {
    const match = /^([0-9a-f]{64})\s+\*?(.+)$/.exec(line); assert.ok(match, 'Invalid checksum record');
    const path = resolve(product,match[2]); assert.ok(path.startsWith(product + sep), 'Checksum path escapes product');
    assert.equal(sha256(path), match[1], match[2]);
  }
  assert.equal(sums.length + 1, zip.files);
});
function native(prefix, arch) {
  const receipt = read(resolve(run,prefix,'native-guest-receipt.json'));
  const file = resolve(run,prefix,'native-portable-verification.json');
  assert.equal(receipt.passed, true); assert.equal(receipt.zip_sha256, zip.sha256);
  assert.equal(receipt.verification_report_sha256, sha256(file)); assert.equal(receipt.environment.architecture, arch);
  for (const key of ['administrator','node_on_PATH','python_on_PATH']) assert.equal(receipt.environment[key], false, key);
  assert.deepEqual(receipt.environment.active_network_adapters, []); assert.match(receipt.extracted_directory, /移位验收 空格路径/);
  portable(file, arch === 'AMD64' ? 'x64' : 'arm64');
}
check('M7-x64-clean-Windows', 'Current ZIP: offline standard user, no global runtimes, Unicode/spaces, x64 models/MCP', [resolve(run,'native-guest-receipt.json'),resolve(run,'native-portable-verification.json')], () => native('', 'AMD64'));
check('current-scope', 'User explicitly cancelled ARM64 and container validation and requested x64 delivery plus complete temporary-environment cleanup', [resolve(run,'scope-change.json')], () => {
  assert.equal(scope.ARM64_validation, 'cancelled_by_user');
  assert.equal(scope.windows_container_validation, 'cancelled_by_user');
});
check('environment-cleanup', 'Task-installed tools, VM, containers, downloads and host optional-feature additions removed', [resolve(run,'environment-cleanup.json')], () => {
  assert.equal(read(resolve(run,'environment-cleanup.json')).passed, true);
});
check('redundant-artifact-cleanup', 'Duplicate extractions and cancelled staging removed, unique sources/audits and a usable rollback archive retained', [resolve(run,'backup-cleanup.json'),resolve(run,'verified-duplicate-artifacts.json')], () => {
  assert.equal(read(resolve(run,'backup-cleanup.json')).passed, true);
});
check('delivered-copy-after-cleanup', 'The delivered x64 copy still executes a real retrieval after temporary infrastructure removal', [resolve(run,'post-cleanup-smoke.json'),resolve(run,'post-cleanup-query.json'),resolve(run,'post-cleanup-live-check.json')], () => {
  assert.equal(read(resolve(run,'post-cleanup-smoke.json')).passed, true);
  const state = read(resolve(run,'post-cleanup-live-check.json'));
  for (const key of ['software','processes','services']) assert.deepEqual(state[key], []);
  assert.ok(state.paths.every(item => item.exists === false));
  assert.equal(state.user_path_references_task, false); assert.equal(state.machine_path_references_task, false);
});
const acceptance = old('m6-prospective-acceptance.json');
const audit = { audited_at: new Date().toISOString(), product_version: manifest.product_version,
  verification_complete: requirements.every(item => item.passed), requirements,
  artifact: { directory: product, archive: zip.archive, sha256: zip.sha256, bytes: zip.bytes, files: zip.files },
  quality: { development_recall20: old('m4-production-development.json').aggregates.at20.recall,
    heldout_recall20: acceptance.aggregates.actual.at20.recall, cases: acceptance.cases,
    uncertainty: acceptance.paired_difference_recall20, independent_human_annotation: false, answer_accuracy_claimed: false },
  scope_change: scope,
  cleanup_complete: requirements.find(item => item.id === 'environment-cleanup')?.passed === true,
  remaining: requirements.filter(item => !item.passed).map(item => item.id),
};
const auditPath = resolve(run,'universal-completion-audit.json');
writeFileSync(auditPath, JSON.stringify(audit,null,2) + '\n');
if (seal) {
  assert.equal(audit.verification_complete, true, `Required proof incomplete: ${audit.remaining.join(', ')}`);
  const report = resolve(workspace,'交付与验收报告.md'); assert.ok(readFileSync(report,'utf8').includes(zip.sha256));
  const receipt = { project_delivered: true, product: manifest.product, product_version: manifest.product_version,
    graph_version: manifest.graph_version, archive: zip.archive, bytes: zip.bytes, sha256: zip.sha256, files: zip.files,
    required_architectures: ['x64'], required_architectures_verified: true, independent_windows_verified: true,
    windows_container_verified: false, windows_container_status: 'cancelled_by_user', ARM64_status: 'cancelled_by_user',
    completion_audit: proof(auditPath), report: proof(report), delivered_at: new Date().toISOString(), cleanup_complete: audit.cleanup_complete,
    Windows_servicing_restart_pending: read(resolve(run,'environment-cleanup.json')).Windows_servicing_restart_pending,
    host_restart_performed: false };
  for (const path of [resolve(workspace,'deliveries/delivery-receipt.json'), `${zip.archive}.delivery-receipt.json`]) writeFileSync(path, JSON.stringify(receipt,null,2) + '\n');
}
console.log(JSON.stringify({ verification_complete: audit.verification_complete, pending: audit.remaining, delivery_receipt_written: seal, audit: auditPath }));
