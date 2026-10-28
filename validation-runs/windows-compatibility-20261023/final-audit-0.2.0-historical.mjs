import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { sha256 } from '../src/corpus.mjs';
const workspace = resolve('..'), run = resolve(workspace, 'validation-runs/agent-implementation-20261022');
const read = name => JSON.parse(readFileSync(resolve(run, name), 'utf8'));
const freeze = read('m6-profile-freeze.json'), acceptance = read('m6-prospective-acceptance.json');
const gates = read('release-gates.json'), directory = read('m7-directory-verification.json'), extraction = read('m7-zip-extraction.json'), moved = read('m7-extracted-verification.json');
const base = read('baseline.json');
assert.equal(directory.passed, true); assert.equal(moved.passed, true); assert.equal(gates.local_release_gates_passed, true);
assert.equal(sha256(extraction.archive), extraction.sha256);
for (const [file, hash] of Object.entries(base.canonical_inputs)) assert.equal(sha256(resolve(workspace, file)), hash);
for (const [file, hash] of Object.entries(freeze.source_files)) assert.equal(sha256(file), hash, file);
assert.equal(sha256('evaluation/acceptance-v1/cases.jsonl'), freeze.heldout_cases_sha256);
const product = resolve(workspace, 'deliveries/chan-kg-agent-0.2.0-307029129712');
const manifest = JSON.parse(readFileSync(resolve(product, 'release-manifest.json'), 'utf8'));
for (const entry of manifest.entrypoints) assert.ok(existsSync(resolve(product, entry)));
for (const forbidden of ['app/curation', 'app/test', 'app/build', 'chan-kg-desktop', '.git']) assert.equal(existsSync(resolve(product, forbidden)), false, forbidden);
assert.equal(JSON.parse(readFileSync(resolve(run, 'canonical-validation-direct.json'))).pass, true);
const requirements = [
  ['M0', 'Current scope, baseline backup, frozen source-disjoint tests and interface/index contracts', 'implemented_verified', ['baseline.json', 'm6-profile-freeze.json']],
  ['M1', '473 ambiguous reviewed records preserved; 2611 pending separated; 2116/61/434 source-coverage triage; eight sourced issues and Unicode/provenance', 'implemented_verified', ['pre-release-tests.log', 'retrieval-contract-current.log']],
  ['M2', 'Complete-query production lexical matches strong baseline on all 240 cases and old eight commands remain compatible', 'implemented_verified', ['m2-lexical-parity.json', 'pre-release-tests.log']],
  ['M3', 'Pinned offline embedding, original encoder parameter match, FP32/q8 check, exact vector scan and fusion experiments', 'implemented_verified', ['m3-author-weights.json', 'm3-embedding-consistency.json', 'm3-hybrid-development.json']],
  ['M4', 'Bounded typed/directed supported graph, one/two-hop and weights ablations, issue alternatives, 20/40 rerank comparison and whole-unit budgets', 'implemented_verified', ['m4-graph-development.json', 'm4-rerank-development.json', 'm4-production-development.json', 'pre-release-tests.log']],
  ['M5', 'Shared CLI/JS/MCP, actual stdio client/default-profile roundtrip, schema errors, follow-up evidence and caller-agent answer examples', 'implemented_verified', ['m5-default-mcp-roundtrip.json', 'm5-agent-example-inputs.json', 'release-gates.json']],
  ['M6', 'Prospective quality comparison after configuration freeze, all source/condition/path gates, CPU resources, source hashes and truthful annotation limits', 'implemented_verified', ['m6-profile-freeze.json', 'm6-prospective-acceptance.json', 'canonical-validation-direct.json', 'release-gates.json']],
  ['M7', 'Actual portable directory and ZIP, bundled runtimes/models/knowledge/licenses, Unicode/space relocation, denied Node network APIs, isolated PATH, loaded native DLL proof and equal CLI/JS/MCP', 'local_delivery_verified', ['m7-directory-verification.json', 'm7-zip-extraction.json', 'm7-extracted-verification.json']],
  ['M7-independent-Windows', 'Execute on a separate clean Windows installation without global runtimes', 'deferred_by_explicit_user_instruction', []],
];
const audit = { audited_at: new Date().toISOString(), plan: '../完整实施计划.md', local_delivery_complete: true,
  full_original_environment_acceptance_complete: false, independent_windows_deferred_by_user: true,
  user_instruction: '暂时没有，先完成本机与交付件验证',
  requirements: requirements.map(([id, requirement, status, evidence]) => ({ id, requirement, status,
    evidence: evidence.map(file => ({ file, sha256: sha256(resolve(run, file)) })) })),
  primary_artifacts: { directory: product, archive: extraction.archive, zip_sha256: extraction.sha256, archive_bytes: extraction.archive_bytes, product_manifest_sha256: sha256(resolve(product, 'release-manifest.json')) },
  canonical_inputs_unchanged: true, frozen_source_and_cases_unchanged: true,
  no_formal_semantic_promotions: true, human_gold_claimed: false,
  quality: { development_recall20: read('m4-production-development.json').aggregates.at20.recall, heldout_recall20: acceptance.aggregates.actual.at20.recall, heldout_cases: acceptance.cases, sampling_uncertainty: acceptance.paired_difference_recall20 },
  remaining_required_external_verification: ['Independent clean Windows execution, deferred while no environment is available'],
};
writeFileSync(resolve(run, 'completion-audit.json'), JSON.stringify(audit, null, 2) + '\n');
writeFileSync(`${extraction.archive}.delivery-receipt.json`, JSON.stringify({ product: manifest.product, product_version: manifest.product_version,
  graph_version: manifest.graph_version, archive: extraction.archive, bytes: extraction.archive_bytes, sha256: extraction.sha256,
  files: extraction.files, directory_verification_passed: true, actual_zip_extraction_verification_passed: true,
  independent_windows_verified: false, independent_windows_status: 'deferred_by_user', completion_audit_sha256: sha256(resolve(run, 'completion-audit.json')) }, null, 2) + '\n');
console.log(JSON.stringify({ local_delivery_complete: true, archive: extraction.archive, sha256: extraction.sha256, independent_windows_deferred: true }));
