import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256, codepoints } from '../src/corpus.mjs';
import { rankedMetrics } from './lib/retrieval-baselines.mjs';
const run = resolve('../validation-runs/agent-implementation-20261022');
const output = resolve(run, 'm6-prospective-acceptance.json');
assert.ok(!existsSync(output), 'Held-out acceptance already exposed; preserve its result and do not silently tune/retest it.');
const freeze = JSON.parse(readFileSync(resolve(run, 'm6-profile-freeze.json')));
const manifest = JSON.parse(readFileSync('evaluation/acceptance-v1/manifest.json'));
const verifyInputs = () => {
  assert.equal(sha256('profiles/default.json'), freeze.profile_sha256);
  assert.equal(sha256('indexes/lexical-1-307029129712/manifest.json'), freeze.index_manifest_sha256);
  assert.equal(sha256('evaluation/acceptance-v1/cases.jsonl'), freeze.heldout_cases_sha256);
  assert.equal(freeze.heldout_cases_sha256, manifest.cases_sha256);
  for (const [path, hash] of Object.entries(freeze.source_files)) assert.equal(sha256(path), hash, path);
};
verifyInputs();
const service = new RetrievalService();
try {
  const cases = readFileSync('evaluation/acceptance-v1/cases.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
  const observations = [];
  const ids = packet => [...new Set(packet.data.reviewed.flatMap(c => [...new Set(c.evidence.map(e => e.passage_id))].sort()))];
  const check = packet => {
    assert.equal(packet.runtime.degraded, false); assert.equal(packet.data.research_leads.length, 0);
    assert.ok(codepoints(JSON.stringify(packet.data)) <= packet.data.budget.context_limit);
    assert.equal(codepoints(JSON.stringify(packet.data)), packet.data.budget.used_codepoints);
    for (const c of packet.data.reviewed) {
      const original = service.corpus.claims.get(c.id);
      assert.equal(c.review_status, 'reviewed'); assert.equal(c.text, original.text);
      assert.deepEqual(c.conditions, original.conditions); assert.deepEqual(c.exceptions, original.exceptions);
      assert.equal(c.review_note, original.review_note); assert.equal(c.ambiguity_status, original.ambiguity_status);
      for (const e of c.evidence) {
        const originalEvidence = service.corpus.evidence.get(e.id), p = service.corpus.passages.get(e.passage_id);
        assert.equal(e.claim_id, c.id); assert.equal(e.quote, originalEvidence.quote);
        assert.equal([...p.text].slice(e.quote_start, e.quote_end).join(''), e.quote);
        assert.equal(e.role, p.role); assert.equal(e.speaker, p.speaker); assert.equal(e.pdf_page, p.pdf_page);
        assert.equal(e.context_semantic_review, 'not_asserted');
      }
    }
    for (const path of packet.data.relation_paths) {
      const edge = service.corpus.relations.find(r => r.id === path.relation_id);
      assert.ok(edge); assert.equal(edge.source, path.source); assert.equal(edge.target, path.target);
      assert.ok(edge.claim_ids.includes(path.support_claim_id));
      assert.ok(path.support_evidence_ids.every(id => service.corpus.evidence.get(id).claim_id === path.support_claim_id));
    }
  };
  for (const item of cases) {
    const request = { query: item.query_text, limit: 20, contextBudget: 60000 };
    const lexical = await service.retrieve({ ...request, profile: 'lexical' });
    const actual = await service.retrieve(request);
    check(lexical); check(actual);
    const relevant = [...new Set(item.expected_source_refs.map(r => r.passage_id))];
    const a = ids(actual), b = ids(lexical);
    observations.push({ id: item.query_id, stratum: item.stratum, query: item.query_text,
      actual: { at10: rankedMetrics(a, relevant, 10), at20: rankedMetrics(a, relevant, 20), claim_ids: actual.data.reviewed.map(c => c.id), passages: a },
      lexical: { at10: rankedMetrics(b, relevant, 10), at20: rankedMetrics(b, relevant, 20) },
      elapsed_ms: actual.runtime.elapsed_ms, budget: actual.data.budget, issue_groups: actual.data.issues.map(i => i.issue_id),
      required_claim_found: item.required_claim_ids.every(id => actual.data.reviewed.some(c => c.id === id)) });
    if (observations.length % 6 === 0) console.log(JSON.stringify({ acceptance_cases: observations.length, total: cases.length }));
  }
  const average = (variant, k, field) => observations.reduce((s, o) => s + o[variant][k][field], 0) / observations.length;
  const aggregates = Object.fromEntries(['actual', 'lexical'].map(v => [v, Object.fromEntries(['at10', 'at20'].map(k => [k, Object.fromEntries(['recall', 'ndcg_binary', 'all_annotated_evidence_found'].map(f => [f, average(v, k, f)]))]))]));
  const differences = observations.map(o => o.actual.at20.recall - o.lexical.at20.recall);
  let state = 20261022;
  const random = () => { state ^= state << 13; state ^= state >>> 17; state ^= state << 5; return (state >>> 0) / 4294967296; };
  const bootstrap = Array.from({ length: 5000 }, () => differences.reduce(sum => sum + differences[Math.floor(random() * differences.length)], 0) / differences.length).sort((a, b) => a - b);
  const times = observations.map(o => o.elapsed_ms).sort((a, b) => a - b);
  const coldStart = performance.now();
  const cold = spawnSync(process.execPath, ['--import', pathToFileURL(resolve('scripts/deny-network.mjs')).href, resolve('bin/chan-kg.mjs'), 'retrieve', '中枢是什么，成立需要什么条件？', '--limit', '5'], { cwd: tmpdir(), encoding: 'utf8', timeout: 120000, maxBuffer: 8 * 1024 * 1024 });
  assert.equal(cold.status, 0, cold.stderr);
  const coldMs = performance.now() - coldStart;
  const resources = { warm_query_p50_ms: times[Math.floor(times.length * .5)], warm_query_p95_ms: times[Math.floor(times.length * .95)],
    cold_cli_ms: coldMs, process_peak_rss_bytes: process.resourceUsage().maxRSS * 1024 };
  const resourcePassed = resources.warm_query_p95_ms <= freeze.resources.warm_query_p95_ms_max && resources.cold_cli_ms <= freeze.resources.cold_cli_ms_max && resources.process_peak_rss_bytes <= freeze.resources.process_peak_rss_bytes_max;
  verifyInputs(); assert.equal(sha256(service.graph.path), freeze.canonical_database_sha256);
  const result = { created_at: new Date().toISOString(), cases: observations.length, frozen_profile_sha256: freeze.profile_sha256,
    independently_heldout_source_split: true, independent_human_annotation: false, generated_answers_scored: false,
    aggregates, paired_difference_recall20: { mean: differences.reduce((a, b) => a + b, 0) / differences.length, bootstrap_percentile95: [bootstrap[125], bootstrap[4874]], seed: 20261022, resamples: 5000,
      note: 'Small source-disjoint model-annotated set; interval expresses sampling uncertainty, not independent human correctness.' },
    improved20: differences.filter(x => x > 0).length, regressed20: differences.filter(x => x < 0).length, integrity_errors: 0,
    resource_limits_frozen_before_test: freeze.resources, resources, resource_passed: resourcePassed,
    quality_comparison_passed: aggregates.actual.at20.recall >= aggregates.lexical.at20.recall && aggregates.actual.at20.all_annotated_evidence_found >= aggregates.lexical.at20.all_annotated_evidence_found,
    inputs_unchanged: true, independent_windows_verified: false, independent_windows_status: 'deferred_by_user', observations };
  writeFileSync(output, JSON.stringify(result, null, 2) + '\n'); console.log(JSON.stringify({ ...result, observations: undefined }));
} finally { await service.close(); }
