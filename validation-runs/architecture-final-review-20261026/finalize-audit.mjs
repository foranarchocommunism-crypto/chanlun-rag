import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const audit = dirname(fileURLToPath(import.meta.url));
const repo = resolve(audit, '../../chan-kg-agent');
const json = path => JSON.parse(readFileSync(path, 'utf8'));
const sha256 = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const artifact = path => ({ path, sha256: sha256(path) });
const latest = json(resolve(audit, 'latest.json'));
const result = json(latest.results);
assert.equal(result.completed, true);
assert.equal(result.production_unchanged, true);

const changed = Object.entries(result.protected_before)
  .filter(([path, expected]) => sha256(path) !== expected).map(([path]) => path);
assert.deepEqual(changed, [], 'Protected production files changed after tests');
const identity = result.observations.find(o => o.name === 'current_code_matches_verified_rc2');
for (const key of ['matches', 'package_matches', 'canonical_matches']) assert.equal(identity[key], true);

const metricsPath = resolve(repo, 'build/graph-v2/development-natural/metrics.json');
const metrics = json(metricsPath);
for (const [file, expected] of Object.entries(metrics.inputs.code)) {
  assert.equal(sha256(resolve(repo, 'src', file)), expected, file);
}
for (const [file, key] of [
  ['../shared-knowledge/v0.1.0/graph.sqlite', 'database'],
  ['indexes/lexical-1-307029129712/manifest.json', 'index'],
  ['profiles/default.json', 'profile'],
  ['profiles/graph-v2.json', 'experimental_profile'],
]) assert.equal(sha256(resolve(repo, file)), metrics.inputs[key], file);

const testPath = resolve(audit, 'current-tests.tap');
const tap = readFileSync(testPath, 'utf8');
const count = key => Number(tap.match(new RegExp(`^# ${key} (\\d+)$`, 'm'))?.[1]);
const tests = Object.fromEntries(['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo'].map(key => [key, count(key)]));
assert.equal(tests.tests, 109);
assert.equal(tests.pass, 109);
for (const key of ['fail', 'cancelled', 'skipped', 'todo']) assert.equal(tests[key], 0);
const validationPath = resolve(audit, 'current-canonical-validation.json');
const validation = json(validationPath);
assert.equal(validation.pass, true);
assert.deepEqual(validation.errors, []);

const issues = [
  { original_group: 1, name: '普通 Graph 新候选被 RRF 截断', status: 'partially_resolved', reason: '实验配置已证明候选实际准入；默认仍为旧路径，整体质量优势未证实。' },
  { original_group: 2, name: '图通道异常没有受控回退', status: 'resolved', reason: '新旧配置均通过严格报错、显式允许降级时与文本基线一致的实测；全局数据错误仍拒绝继续。' },
  { original_group: 3, name: '构建检查点和 manifest 非原子', status: 'unresolved', priority: 'P1', reason: '本次重新复现检查点间隙、projection 中断、半截 manifest 三种重试失败。' },
  { original_group: 4, name: '快照与可写 WAL 边界', status: 'unresolved', priority: 'P1', reason: '同版本 WAL 提交尚未 checkpoint 时，新文本与旧向量可同时被接受；需要可写数据库这一前提。' },
  { original_group: 5, name: '二跳预算及本体治理', status: 'partially_resolved', reason: '实验配置已限制资源并自然竞争；默认路径和本体治理仍有原缺口。二跳保底及专项收益已由用户取消。' },
  { original_group: 6, name: '独立质量及 trace', status: 'partially_resolved', reason: '观测、降级、排队、路径包装已改善；完整排名重放和广泛语义准确性仍不能证明。学生流程已取消。' },
];
const counts = Object.fromEntries(['resolved', 'partially_resolved', 'unresolved'].map(status => [status, issues.filter(i => i.status === status).length]));
assert.deepEqual(counts, { resolved: 1, partially_resolved: 3, unresolved: 2 });
const receipt = {
  schema_version: '1.0.0',
  client_audit_date: '2026-10-26',
  client_timezone: 'Asia/Shanghai',
  generated_at_host_utc: new Date().toISOString(),
  purpose: 'Read-only architecture final review against original six remediation groups',
  product_version: identity.version,
  default_profile: json(resolve(repo, 'profiles/default.json')).default_profile,
  experimental_profile_enabled_by_default: json(resolve(repo, 'profiles/graph-v2.json')).default_enabled,
  verdict: 'partially_closed',
  architecture_acceptance_passed: false,
  counts,
  issues,
  scope_decisions: {
    student_question_and_review_workflow: 'cancelled_by_user_not_passed_not_pending',
    two_hop_special_channel_floor_and_quality_gate: 'retired_by_user',
    two_hop_current_selection: 'natural_competition_shared_pool',
    no_subagents: true,
    no_html: true,
    no_production_edits: true,
  },
  limitations: [
    'Static local read-only use remains the assessed deployment boundary; no online-write consistency or arbitrary interruption recovery certification.',
    'Current source/rc.2 review does not update an older 0.3.0 client.',
    '240-case development and prior delivery/performance evidence were inspected and identity-checked, not rerun in full during this review.',
    'Traversal, candidate admission, complete returned path and retrieval quality are separate claims.',
  ],
  current_verification: {
    identity,
    tests,
    canonical_validation: validation,
    protected_file_count: Object.keys(result.protected_before).length,
    protected_files_unchanged_after_tests: changed.length === 0,
    live_probe_results: artifact(latest.results),
    live_probe_script: artifact(resolve(audit, 'checks.mjs')),
    test_log: artifact(testPath),
    canonical_log: artifact(validationPath),
  },
  reused_evidence: [
    metricsPath,
    resolve(repo, 'build/graph-v2/development-findings.json'),
    resolve(repo, 'build/graph-v2/acceptance/performance.json'),
    resolve(repo, 'build/graph-v2/acceptance/gate-results.json'),
    resolve(repo, 'fresh-extraction-delivery-receipt.json'),
  ].map(artifact),
  original_report: artifact(resolve(audit, '../architecture-review-20261025/架构技术审查报告.md')),
  final_report: artifact(resolve(audit, '架构终审报告.md')),
};
const output = resolve(audit, 'audit-receipt.json');
writeFileSync(output, JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify({ receipt: output, counts, tests, protected_files_unchanged: true }, null, 2));
