import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, copyFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { sha256 } from '../src/corpus.mjs';
const run = resolve('../validation-runs/agent-implementation-20261022');
assert.ok(!existsSync(resolve(run, 'm6-profile-freeze.json')), 'Already frozen: preserve prior acceptance inputs');
const result = JSON.parse(readFileSync(resolve(run, 'm4-production-development.json'), 'utf8'));
assert.equal(result.development_cases, 240); assert.equal(result.integrity_errors, 0);
assert.ok(result.aggregates.at20.recall > result.aggregates.lexical_at20.recall);
const tests = readFileSync(resolve(run, 'pre-release-tests.log'), 'utf8');
assert.match(tests, /# fail 0|ℹ fail 0/);
const profilePath = resolve('profiles/default.json');
copyFileSync(profilePath, resolve(run, 'development-profile.json'));
const profile = JSON.parse(readFileSync(profilePath, 'utf8'));
profile.profile_version = '1.0.0'; profile.status = 'release_candidate_frozen_before_prospective_acceptance';
profile.frozen_at = new Date().toISOString();
profile.resources = { environment: 'CPU i5-1038NG7 / Windows10 x64 / about16GiB', warm_query_p95_ms_max: 6000, cold_cli_ms_max: 12000, process_peak_rss_bytes_max: 2147483648,
  basis: 'CPU development run 240 real API calls: warm p95 about2076ms and peakRSS about1.315GB; conservative limits frozen before held-out execution.' };
writeFileSync(profilePath, JSON.stringify(profile, null, 2) + '\n');
const indexFile = resolve('indexes/lexical-1-307029129712/manifest.json');
copyFileSync(indexFile, resolve(run, 'index-manifest-pre-freeze.json'));
const index = JSON.parse(readFileSync(indexFile));
index.runtime_profile_sha256 = sha256(profilePath);
index.models.reranker = { repo: 'Xenova/bge-reranker-base', revision: '280bcc27a84e0b898c251e06fddb25171bd9b101', dtype: 'q8',
  model_manifest_sha256: sha256('models/Xenova/bge-reranker-base/model-manifest.json'), score: 'raw_logit_relevance_not_truth', default_budget: 40 };
index.index_version = 'hybrid-1-release-profile-1';
writeFileSync(indexFile, JSON.stringify(index, null, 2) + '\n');
const hashDirectory = directory => Object.fromEntries(readdirSync(directory, { withFileTypes: true }).filter(e => e.isFile()).map(e => [`${directory}/${e.name}`, sha256(`${directory}/${e.name}`)]));
const freeze = { frozen_at: profile.frozen_at, prospective_acceptance_already_run: false, profile_sha256: sha256(profilePath), index_manifest_sha256: sha256(indexFile),
  canonical_database_sha256: sha256('../shared-knowledge/v0.1.0/graph.sqlite'),
  source_files: { ...hashDirectory('src'), ...hashDirectory('bin'), ...hashDirectory('contracts') },
  heldout_cases_sha256: sha256('evaluation/acceptance-v1/cases.jsonl'), resources: profile.resources,
  quality_rule: 'Pair same final K and context budget against strong lexical baseline. Selected default must have no identity/condition/path gate errors, and report held-out paired recall, complete groups, wins/losses and uncertainty without tuning on this set.',
  independent_annotation: false, independent_windows: 'Deferred by user; local and extracted artifact verification still required.' };
writeFileSync(resolve(run, 'm6-profile-freeze.json'), JSON.stringify(freeze, null, 2) + '\n');
console.log(JSON.stringify({ frozen: true, profile: profile.profile_version, index: index.index_version }));
