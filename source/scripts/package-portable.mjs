import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { cpSync, copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256 } from '../src/corpus.mjs';
import { assertStaticDatabase } from '../src/snapshot.mjs';
const source = resolve(dirname(fileURLToPath(import.meta.url)), '..'), workspace = resolve(source, '..');
const args = process.argv.slice(2), candidate = args.includes('--candidate');
const architectures = args.includes('--include-arm64') ? ['x64', 'arm64'] : ['x64'];
const at = args.indexOf('--output');
const pkg = JSON.parse(readFileSync(resolve(source, 'package.json'), 'utf8'));
const output = at < 0 ? resolve(workspace, `deliveries/chan-kg-agent-${pkg.version}-windows-${architectures.join('-')}-307029129712`) : resolve(args[at + 1]);
assert.ok(!existsSync(output), 'Output already exists; create a new version instead of overwriting.');
const gatesPath = resolve(workspace, 'validation-runs/agent-implementation-20261022/release-gates.json');
if (!candidate) {
  const formalPath = resolve(source, 'build/formal-release/gates.json');
  assert.ok(existsSync(formalPath), 'Current fixed-corpus release gates are required');
  const formal = JSON.parse(readFileSync(formalPath, 'utf8'));
  assert.equal(formal.passed, true); assert.equal(formal.product_version, pkg.version);
  for (const [file, digest] of Object.entries(formal.inputs)) assert.equal(sha256(resolve(source, file)), digest, `Release input changed: ${file}`);
}
const service = new RetrievalService();
try {
  assert.equal(service.indexProblem, null); assert.equal(service.denseProblem, null); assert.ok(service.dense);
  assert.ok(service.status().data.capabilities.rerank);
  mkdirSync(output, { recursive: true });
  const app = resolve(output, 'app'); mkdirSync(app);
  for (const directory of ['bin', 'src', 'contracts']) cpSync(resolve(source, directory), resolve(app, directory), { recursive: true });
  for (const file of ['package.json', 'package-lock.json', 'AGENT_GUIDE.md']) copyFileSync(resolve(source, file), resolve(app, file));
  const dependencyRoot = resolve(source, 'node_modules');
  const includeDependency = path => {
    const rel = relative(dependencyRoot, path).split(sep).join('/');
    if (/^onnxruntime-node\/bin\/napi-v6\/(linux|darwin)(\/|$)/.test(rel)) return false;
    if (!architectures.includes('arm64') && (/^onnxruntime-node\/bin\/napi-v6\/win32\/arm64(?:\/|$)/.test(rel) || /^@img\/sharp-win32-arm64(?:\/|$)/.test(rel))) return false;
    if (/^@img\/(sharp|sharp-libvips)-(?!win32-(?:x64|arm64)(?:\/|$))/.test(rel)) return false;
    return !rel.split('/').some(p => p === '.cache');
  };
  cpSync(dependencyRoot, resolve(app, 'node_modules'), { recursive: true, filter: includeDependency });
  mkdirSync(resolve(app, 'scripts'));
  for (const file of ['verify-portable.mjs', 'deny-network.mjs', 'doctor.ps1']) copyFileSync(resolve(source, 'scripts', file), resolve(app, 'scripts', file));
  assert.equal(process.platform, 'win32'); assert.equal(process.arch, 'x64');
  const armRoot = resolve(source, 'build/portable-platforms/arm64');
  let armManifest;
  if (architectures.includes('arm64')) {
  armManifest = JSON.parse(readFileSync(resolve(armRoot, 'platform-manifest.json'), 'utf8'));
  const signatures = JSON.parse(readFileSync(resolve(armRoot, 'arm64-asset-signatures.json'), 'utf8').replace(/^\uFEFF/, ''));
  assert.ok(signatures.length >= 6 && signatures.every(s => s.status === 'Valid'));
  assert.equal(sha256(resolve(armRoot, 'node.exe')), armManifest.node.sha256);
  cpSync(resolve(armRoot, 'sharp-win32-arm64'), resolve(app, 'node_modules/@img/sharp-win32-arm64'), { recursive: true });
  }
  for (const arch of architectures) mkdirSync(resolve(output, 'runtime', arch), { recursive: true });
  copyFileSync(process.execPath, resolve(output, 'runtime/x64/node.exe'));
  if (architectures.includes('arm64')) copyFileSync(resolve(armRoot, 'node.exe'), resolve(output, 'runtime/arm64/node.exe'));
  const nativeManifest = JSON.parse(readFileSync(resolve(source, 'build/native-runtime/native-runtime-manifest.json'), 'utf8'));
  for (const arch of architectures) {
    const assets = arch === 'x64' ? nativeManifest.assets : armManifest.native_dependencies;
    for (const asset of assets) {
      const from = resolve(arch === 'x64' ? resolve(source, 'build/native-runtime') : resolve(armRoot, 'native-runtime'), asset.file);
      assert.equal(sha256(from), asset.sha256); copyFileSync(from, resolve(output, 'runtime', arch, asset.file));
      // Node loads addons with an altered DLL search path: CRT files must also sit by each addon.
      for (const directory of [`node_modules/onnxruntime-node/bin/napi-v6/win32/${arch}`, `node_modules/@img/sharp-win32-${arch}/lib`]) {
        assert.ok(existsSync(resolve(app, directory)), `Missing native module directory: ${directory}`);
        copyFileSync(from, resolve(app, directory, asset.file));
      }
    }
  }
  cpSync(service.paths.kbPath, resolve(output, 'knowledge'), { recursive: true, filter: path => !/building\.failed|\.(?:sqlite-wal|sqlite-shm)$/.test(path) });
  service.ensureCurrent();
  const canonicalHash = assertStaticDatabase(resolve(output, 'knowledge/graph.sqlite'));
  assert.equal(canonicalHash, service.graph.snapshot.sha256);
  writeFileSync(resolve(output, 'knowledge/snapshot.json'), JSON.stringify({ contract: 'fixed_read_only_delete_mode_v1',
    canonical_sha256: canonicalHash, manifest_sha256: sha256(resolve(output, 'knowledge/manifest.json')), online_writes: false }, null, 2) + '\n');
  const indexDirectory = 'active';
  cpSync(service.paths.indexPath, resolve(output, 'indexes', indexDirectory), { recursive: true,
    filter: path => !['vector-progress.json', 'vector-build.lock'].includes(path.split(sep).at(-1)) });
  writeFileSync(resolve(output, 'indexes/active.json'), JSON.stringify({ directory: indexDirectory }) + '\n');
  cpSync(service.paths.modelPath, resolve(output, 'models'), { recursive: true, filter: path => !path.endsWith('.part') });
  mkdirSync(resolve(output, 'policies')); copyFileSync(service.paths.policyPath, resolve(output, 'policies/ambiguity-issues.json'));
  mkdirSync(resolve(output, 'profiles')); copyFileSync(service.paths.profilePath, resolve(output, 'profiles/default.json'));
  copyFileSync(service.graphConfigPath, resolve(output, 'profiles/graph-v2.json'));
  cpSync(resolve(source, 'licenses'), resolve(output, 'licenses'), { recursive: true });
  copyFileSync(resolve(source, 'build/native-runtime/native-runtime-manifest.json'), resolve(output, 'licenses/native-runtime-provenance.json'));
  for (const file of architectures.includes('arm64') ? ['platform-manifest.json', 'arm64-asset-signatures.json', 'MSVC-RUNTIME-LICENSE.rtf'] : []) {
    copyFileSync(resolve(armRoot, file), resolve(output, 'licenses', `arm64-${file}`));
  }
  mkdirSync(resolve(output, 'docs'));
  for (const file of ['retrieval-contract.md', 'MAINTENANCE.md', 'agent-answer-examples.md', 'COMPATIBILITY.md', 'graph-v2.md', 'fixed-release.md']) copyFileSync(resolve(source, 'docs', file), resolve(output, 'docs', file));
  if (!candidate) copyFileSync(resolve(source, 'build/formal-release/gates.json'), resolve(output, 'docs/fixed-release-gates.json'));
  copyFileSync(resolve(source, 'docs/portable-readme.md'), resolve(output, 'README.md'));
  const launcher = entry => `@echo off\r\nsetlocal\r\nset "CHAN_KG_NATIVE_ARCH=%PROCESSOR_ARCHITECTURE%"\r\nif defined PROCESSOR_ARCHITEW6432 set "CHAN_KG_NATIVE_ARCH=%PROCESSOR_ARCHITEW6432%"\r\nset "CHAN_KG_NODE_ARCH="\r\nif /I "%CHAN_KG_NATIVE_ARCH%"=="AMD64" set "CHAN_KG_NODE_ARCH=x64"\r\n${architectures.includes('arm64') ? 'if /I "%CHAN_KG_NATIVE_ARCH%"=="ARM64" set "CHAN_KG_NODE_ARCH=arm64"\r\n' : ''}if not defined CHAN_KG_NODE_ARCH (echo Unsupported Windows architecture: %CHAN_KG_NATIVE_ARCH% 1>&2 & exit /b 1)\r\n"%~dp0runtime\\%CHAN_KG_NODE_ARCH%\\node.exe" "%~dp0app\\${entry.replaceAll('/', '\\')}" %*\r\nexit /b %errorlevel%\r\n`;
  writeFileSync(resolve(output, 'chan-kg.cmd'), launcher('bin/chan-kg.mjs'));
  writeFileSync(resolve(output, 'chan-kg-mcp.cmd'), launcher('bin/chan-kg-mcp.mjs'));
  writeFileSync(resolve(output, 'verify.cmd'), launcher('scripts/verify-portable.mjs'));
  writeFileSync(resolve(output, 'doctor.cmd'), '@echo off\r\nsetlocal\r\n"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0app\\scripts\\doctor.ps1" %*\r\nexit /b %errorlevel%\r\n');
  const dependencies = [];
  function collectDependencies(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
      const path = resolve(directory, entry.name);
      if (entry.name.startsWith('@')) { collectDependencies(path); continue; }
      const manifest = resolve(path, 'package.json');
      if (existsSync(manifest)) {
        const p = JSON.parse(readFileSync(manifest, 'utf8'));
        dependencies.push({ name: p.name, version: p.version, license: p.license ?? null,
          package_path: relative(output, path).split(sep).join('/'),
          license_files: readdirSync(path).filter(f => /^(license|licence|copying|notice)/i.test(f)) });
      }
    }
  }
  collectDependencies(resolve(app, 'node_modules'));
  writeFileSync(resolve(output, 'licenses/third-party-packages.json'), JSON.stringify(dependencies, null, 2) + '\n');
  if (existsSync(gatesPath)) copyFileSync(gatesPath, resolve(output, 'docs/legacy-release-gates-reference.json'));
  const newGatesPath = resolve(source, 'build/graph-v2/acceptance/gate-results.json');
  if (existsSync(newGatesPath)) copyFileSync(newGatesPath, resolve(output, 'docs/graph-v2-gates-at-build.json'));
  const git = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: source, encoding: 'utf8' });
  const manifest = { product: 'chan-kg-agent', product_version: pkg.version, built_at: new Date().toISOString(),
    status: candidate ? 'candidate_incomplete_validation' : 'portable_release_environment_results_in_external_receipt',
    graph_version: service.graph.metadata.graph_version, schema_version: service.graph.metadata.schema_version,
    index_version: service.index.index_version, policy_version: service.policy.policy_version,
    canonical_database_sha256: sha256(service.graph.path), canonical_manifest_sha256: sha256(resolve(service.paths.kbPath, 'manifest.json')),
    index_manifest_sha256: sha256(resolve(output, 'indexes/active/manifest.json')), profile_sha256: sha256(service.paths.profilePath),
    model_manifest_sha256: { embedding: sha256(resolve(output, 'models/Xenova/bge-small-zh-v1.5/model-manifest.json')), reranker: sha256(resolve(output, 'models/Xenova/bge-reranker-base/model-manifest.json')) },
    runtimes: Object.fromEntries(architectures.map(arch => [arch, {
      version: process.version, platform: 'win32', arch, path: `runtime/${arch}/node.exe`,
      sha256: sha256(resolve(output, `runtime/${arch}/node.exe`)), license: 'licenses/NODE-LICENSE.txt',
      native_dependencies: arch === 'x64' ? nativeManifest.assets : armManifest.native_dependencies,
      native_license: arch === 'x64' ? 'licenses/MSVC-RUNTIME-LICENSE.txt' : 'licenses/arm64-MSVC-RUNTIME-LICENSE.rtf',
    }])),
    code_commit: args.includes('--source-commit') ? args[args.indexOf('--source-commit') + 1] : git.status === 0 ? git.stdout.trim() : null,
    code_identity_basis: 'actual app file checksums; source commit supplied for the standalone release repository',
    entrypoints: ['chan-kg.cmd', 'chan-kg-mcp.cmd', 'verify.cmd', 'doctor.cmd'], checksums_file: 'checksums.sha256',
    compatibility: { native_platform: 'win32', native_architectures: architectures, minimum_windows_build: 17763,
      target_systems: ['Windows 10 1809+ '+architectures.join('/'), 'Windows 11 '+architectures.join('/')],
      outside_scope: ['Windows 7/8/8.1', '32-bit Windows', ...(!architectures.includes('arm64') ? ['ARM64 Windows'] : [])],
      required_user_installations: [], administrator_required_for_queries: false },
    environment_verification: { status_at_build: 'awaiting_actual_zip_execution', results: 'External ZIP delivery-receipt.json; build metadata does not assert test completion' },
    local_release_gates: null,
    legacy_release_reference: existsSync(gatesPath) ? { path: 'docs/legacy-release-gates-reference.json', sha256: sha256(gatesPath), certifies_this_version: false } : null,
    graph_v2: { default_enabled: false, semantic_acceptance_passed: false, profile_sha256: sha256(service.graphConfigPath),
      hop_selection_policy: 'shared_pool_no_reservations_no_floors', rerank_input_policy: 'same_claim_text_conditions_exceptions_for_all_candidates',
      user_cancelled_student_annotation: true, decision: 'experimental only; related source pairs do not prove necessary multi-hop reasoning',
      gate_snapshot: existsSync(newGatesPath) ? 'docs/graph-v2-gates-at-build.json' : null },
    canonical_changed_by_packaging: false, source_research_complete: false, required_global_runtimes: [],
    fixed_corpus: { online_writes: false, knowledge_updates_planned: false, snapshot_contract: 'fixed_read_only_delete_mode_v1',
      engineering_gates: candidate ? null : 'docs/fixed-release-gates.json', quality_scope: 'exposed development comparisons, not independent answer correctness' },
  };
  writeFileSync(resolve(output, 'release-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  const files = [];
  function walk(path) { for (const e of readdirSync(path, { withFileTypes: true })) { const p = resolve(path, e.name); if (e.isDirectory()) walk(p); else files.push(p); } }
  walk(output); files.sort();
  const checksums = files.map(path => `${sha256(path)}  ${relative(output, path).split(sep).join('/')}`).join('\n') + '\n';
  writeFileSync(resolve(output, 'checksums.sha256'), checksums);
  const receipt = { output, files: files.length + 1, bytes: files.reduce((n, p) => n + statSync(p).size, 0),
    manifest_sha256: sha256(resolve(output, 'release-manifest.json')), checksums_sha256: sha256(resolve(output, 'checksums.sha256')), candidate };
  writeFileSync(`${output}.build-receipt.json`, JSON.stringify(receipt, null, 2) + '\n'); console.log(JSON.stringify(receipt));
} finally { await service.close(); }
