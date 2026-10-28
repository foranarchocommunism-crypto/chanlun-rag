import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { sha256 } from '../src/corpus.mjs';
import { KnowledgeGraph } from '../src/core.mjs';
const run = resolve('../validation-runs/agent-implementation-20261022');
const read = name => JSON.parse(readFileSync(resolve(run, name), 'utf8'));
const acceptance = read('m6-prospective-acceptance.json'), protocol = read('m5-default-mcp-roundtrip.json');
const freeze = read('m6-profile-freeze.json'), baseline = read('baseline.json');
assert.equal(acceptance.quality_comparison_passed, true); assert.equal(acceptance.resource_passed, true);
assert.equal(acceptance.integrity_errors, 0); assert.equal(acceptance.inputs_unchanged, true);
assert.equal(protocol.passed, true); assert.equal(protocol.default_profile_tested, true);
const tests = readFileSync(resolve(run, 'pre-release-tests.log'), 'utf8'); assert.match(tests, /# fail 0|ℹ fail 0/);
for (const [file, hash] of Object.entries(freeze.source_files)) assert.equal(sha256(file), hash);
for (const [file, hash] of Object.entries(baseline.canonical_inputs)) assert.equal(sha256(resolve('..', file)), hash);
const graph = new KnowledgeGraph(resolve('../shared-knowledge/v0.1.0'));
try {
  const checkedIds = [];
  const examples = readFileSync('docs/agent-answer-examples.md', 'utf8');
  for (const id of new Set(examples.match(/evidence-[0-9a-f]{16}/g))) {
    assert.ok(graph.getEvidence(id, { includeUnreviewed: true }), id); checkedIds.push(id);
  }
  const result = { created_at: new Date().toISOString(), local_release_gates_passed: true,
    scope: 'Code/data/model/policy, frozen prospective quality/resource checks, contract tests, real MCP SDK roundtrip, sourced caller-agent examples. Artifact/ZIP validation follows packaging.',
    graph_version: graph.metadata.graph_version, profile_sha256: freeze.profile_sha256,
    heldout: { cases: acceptance.cases, independently_heldout_source_split: true, independent_human_annotation: false,
      quality_comparison_passed: true, aggregates: acceptance.aggregates, paired_difference_recall20: acceptance.paired_difference_recall20 },
    integrity_errors: 0, resources: acceptance.resources, resources_passed: true, canonical_inputs_unchanged: true,
    mcp: { real_stdio_sdk_client: true, native_gui_registration_tested: false, same_CLI_JS_MCP_data: true },
    generated_examples: { cases: 4, path: 'docs/agent-answer-examples.md', checked_evidence_ids: checkedIds,
      caller: 'Current Codex agent, platform-described GPT-6 family; exact serving variant not separately exposed', independent_answer_review: false },
    receipts: Object.fromEntries(['m6-profile-freeze.json', 'm6-prospective-acceptance.json', 'm5-default-mcp-roundtrip.json', 'pre-release-tests.log', 'm3-author-weights.json', 'm3-embedding-consistency.json'].map(f => [f, sha256(resolve(run, f))])),
    independent_windows_verified: false, independent_windows: 'Deferred by direct user instruction: 暂时没有，先完成本机与交付件验证',
    full_independent_environment_acceptance_complete: false,
  };
  writeFileSync(resolve(run, 'release-gates.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ local_release_gates_passed: true, sources_checked: checkedIds.length, independent_windows_deferred: true }));
} finally { graph.close(); }
