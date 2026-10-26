import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { hostname, release, tmpdir, cpus } from 'node:os';
import { basename, dirname, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import './deny-network.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const args = process.argv.slice(2), reportAt = args.indexOf('--report');
const reportPath = reportAt < 0 ? resolve(tmpdir(), `chan-kg-verification-${Date.now()}.json`) : resolve(args[reportAt + 1]);
const hash = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const report = { started_at: new Date().toISOString(), product_root: root, passed: false, checks: [],
  environment: { hostname: hostname(), os_release: release(), platform: process.platform, arch: process.arch, node: process.version,
    executable: process.execPath, cpu: cpus()[0]?.model, current_directory: process.cwd(),
    independent_clean_windows_verified: false, context: 'Actual portable artifact; independent environment identity requires separate review' },
  network_policy: 'Node fetch/http/https/net/tls/dns disabled by verification preload; OS connection state is not changed or claimed disconnected' };
let service, client;
try {
  const manifest = JSON.parse(readFileSync(resolve(root, 'release-manifest.json'), 'utf8'));
  assert.equal(process.platform, 'win32'); assert.ok(['x64', 'arm64'].includes(process.arch));
  const nativeArch = (process.env.PROCESSOR_ARCHITEW6432 || process.env.PROCESSOR_ARCHITECTURE).toUpperCase();
  assert.equal(process.arch, { AMD64: 'x64', ARM64: 'arm64' }[nativeArch], 'Use the native OS architecture; emulated x64 does not validate ARM64');
  const runtimeManifest = manifest.runtimes[process.arch];
  assert.equal(hash(process.execPath), runtimeManifest.sha256, 'Verifier must run with bundled node.exe');
  const timeout = Number(process.env.CHAN_KG_VERIFICATION_TIMEOUT_MS || 120000);
  assert.ok(Number.isInteger(timeout) && timeout >= 30000 && timeout <= 7200000);
  report.operation_timeout_ms = timeout;
  let verified = 0;
  for (const line of readFileSync(resolve(root, 'checksums.sha256'), 'utf8').trim().split('\n')) {
    const split = line.indexOf('  '), digest = line.slice(0, split), relative = line.slice(split + 2);
    assert.match(digest, /^[a-f0-9]{64}$/);
    const path = resolve(root, relative);
    assert.ok(path.startsWith(root + sep), 'Checksum path must stay inside product');
    assert.equal(hash(path), digest, `Checksum mismatch: ${relative}`); verified++;
  }
  report.checks.push({ name: 'all_file_checksums', passed: true, verified_files: verified });
  const runtime = resolve(root, runtimeManifest.path), cli = resolve(root, 'app/bin/chan-kg.mjs'), deny = pathToFileURL(resolve(root, 'app/scripts/deny-network.mjs')).href;
  const env = { ...process.env, PATH: `${dirname(runtime)};${process.env.SystemRoot}\\System32`, NODE_PATH: '', NODE_OPTIONS: '',
    CHAN_KG_PATH: resolve(root, 'knowledge'), CHAN_KG_INDEX: resolve(root, 'indexes/active') };
  const command = parameters => {
    const result = spawnSync(runtime, ['--import', deny, cli, ...parameters], { encoding: 'utf8', cwd: tmpdir(), env, timeout, maxBuffer: 16 * 1024 * 1024 });
    assert.equal(result.status, 0, result.stderr || result.error?.message); return JSON.parse(result.stdout);
  };
  const status = command(['status']);
  assert.equal(status.graph_version, manifest.graph_version); assert.equal(status.data.index_problem, null); assert.equal(status.data.dense_problem, null);
  assert.equal(status.data.capabilities.dense, true); assert.equal(status.data.capabilities.rerank, true);
  report.checks.push({ name: 'status_from_bundled_runtime_isolated_PATH', passed: true, graph_version: status.graph_version });
  const shell = resolve(process.env.SystemRoot, 'System32/cmd.exe');
  const launched = spawnSync(shell, ['/d', '/s', '/c', `""${resolve(root, 'chan-kg.cmd')}" status"`], {
    windowsVerbatimArguments: true, encoding: 'utf8', cwd: tmpdir(), env, timeout, maxBuffer: 16 * 1024 * 1024,
  });
  assert.equal(launched.status, 0, launched.stderr || launched.error?.message);
  assert.deepEqual(JSON.parse(launched.stdout), status);
  report.checks.push({ name: 'architecture_aware_CLI_launcher', passed: true, native_arch: nativeArch, node_arch: process.arch });
  const query = '中枢是什么，成立需要什么条件？';
  const started = performance.now();
  const packet = command(['retrieve', query, '--limit', '5', '--context-budget', '60000']);
  assert.equal(packet.runtime.degraded, false);
  assert.ok(packet.runtime.actual_channels.includes('semantic_vector') && packet.runtime.actual_channels.includes('cross_encoder_rerank'));
  assert.ok(packet.data.reviewed.slice(0, 3).some(c => c.id === 'upper-l017-center-definition'));
  assert.ok(packet.data.reviewed.every(c => c.review_status === 'reviewed'));
  assert.equal(packet.data.research_leads.length, 0);
  report.checks.push({ name: 'offline_default_retrieval', passed: true, elapsed_ms_cli: performance.now() - started, runtime: packet.runtime });
  const trace = command(['retrieve', query, '--trace', '--limit', '2']);
  assert.equal(trace.runtime.effective_request.trace, true);
  assert.equal(trace.runtime.identity.canonical, manifest.canonical_database_sha256);
  assert.ok(trace.runtime.rankings.lexical.length && trace.runtime.rankings.final.length);
  assert.ok(Object.keys(trace.runtime.selected_reasons).length);
  const seal = JSON.parse(readFileSync(resolve(root, 'knowledge/snapshot.json'), 'utf8'));
  assert.equal(seal.canonical_sha256, manifest.canonical_database_sha256);
  assert.equal(seal.manifest_sha256, manifest.canonical_manifest_sha256);
  report.checks.push({ name: 'sealed_snapshot_and_replay_trace', passed: true });
  const issue = command(['issue', 'issue-connection-level-scope']);
  assert.equal(issue.data.issue.resolution_status, 'unresolved');
  assert.ok(issue.data.claims.some(c => c.id === 'upper-l018-center-theorem-one'));
  assert.ok(issue.data.claims.some(c => c.id.startsWith('upper-l054-')));
  const pending = command(['claim', 'candidate-06fee67b46cd9475', '--mode', 'research']);
  assert.equal(pending.data.claim.review_status, 'pending');
  const source = command(['retrieve', 'volume_1-a53e99c37ca5-p0306-b000', '--mode', 'source', '--profile', 'lexical', '--limit', '1']);
  assert.equal(source.data.source_context[0].role, 'reader');
  assert.equal(source.data.source_context[0].semantic_review, 'not_asserted');
  report.checks.push({ name: 'ambiguity_research_source_modes', passed: true });
  const { RetrievalService } = await import(pathToFileURL(resolve(root, 'app/src/retrieval.mjs')));
  service = new RetrievalService({ kbPath: resolve(root, 'knowledge'), indexPath: resolve(root, 'indexes/active'), modelPath: resolve(root, 'models'),
    policyPath: resolve(root, 'policies/ambiguity-issues.json'), profilePath: resolve(root, 'profiles/default.json') });
  const js = await service.retrieve({ query, limit: 5, contextBudget: 60000 });
  assert.deepEqual(js.data, packet.data);
  const experimentRequest = { query, profile: 'hybrid-graph-v2-rerank', limit: 5, contextBudget: 60000 };
  const experimentJS = await service.retrieve(experimentRequest);
  const experimentCLI = command(['retrieve', query, '--profile', 'hybrid-graph-v2-rerank', '--limit', '5', '--context-budget', '60000']);
  assert.deepEqual(experimentJS.data, experimentCLI.data);
  assert.equal(experimentJS.runtime.requested_profile, 'hybrid-graph-v2-rerank');
  const textBaseline = await service.retrieve({ ...experimentRequest, graphDepth: 0, rerankBudget: 40 });
  const originalExpand = service.graphStage.expand;
  service.graphStage.expand = () => { throw new Error('PORTABLE_VERIFICATION_GRAPH_FAULT'); };
  const fallback = await service.retrieve({ ...experimentRequest, allowDegraded: true });
  assert.deepEqual(fallback.data, textBaseline.data); assert.equal(fallback.runtime.degraded, true);
  assert.equal(fallback.runtime.stages.graph.committed_paths, 0);
  await assert.rejects(service.retrieve(experimentRequest), e => e.code === 'GRAPH_EXECUTION_ERROR');
  service.graphStage.expand = originalExpand;
  const recovered = await service.retrieve(experimentRequest); assert.deepEqual(recovered.data, experimentJS.data);
  report.checks.push({ name: 'experimental_CLI_JS_and_graph_fault_strict_fallback_recovery', passed: true,
    rerank_input: experimentJS.runtime.stages.graph.admission?.rerank_input_ids.length,
    graph_status: experimentJS.runtime.stages.graph.status, fallback_primary_equal: true });
  const nativeModules = process.report.getReport().sharedObjects.filter(path => /(?:msvcp140|vcruntime140)/i.test(path));
  report.native_runtime_modules = nativeModules;
  for (const path of nativeModules) {
    const comparable = path.charCodeAt(0) === 92 && path.charCodeAt(1) === 92 && path[2] === '?' && path.charCodeAt(3) === 92 ? path.slice(4) : path;
    assert.ok(comparable.toLowerCase().startsWith(root.toLowerCase() + sep), `Runtime loaded outside bundle: ${path}`);
    const expected = runtimeManifest.native_dependencies.find(a => a.file.toLowerCase() === basename(path).toLowerCase());
    assert.ok(expected, path); assert.equal(hash(path), expected.sha256, path);
  }
  for (const expected of runtimeManifest.native_dependencies) {
    assert.ok(nativeModules.some(path => basename(path).toLowerCase() === expected.file.toLowerCase()), `Expected bundled MSVC module: ${expected.file}`);
  }
  report.checks.push({ name: 'native_dependencies_loaded_from_portable_runtime', passed: true, modules: nativeModules });
  await service.close(); service = null;
  const transport = new StdioClientTransport({ command: shell,
    args: ['/d', '/s', '/c', 'call', resolve(root, 'chan-kg-mcp.cmd')], cwd: tmpdir(),
    env: { ...env, NODE_OPTIONS: `--import=${deny}` }, stderr: 'pipe' });
  let diagnostics = ''; transport.stderr?.on('data', d => { diagnostics += String(d); });
  client = new Client({ name: 'portable-artifact-verifier', version: '1.0.0' }, { capabilities: {} });
  await client.connect(transport);
  assert.equal(client.getServerVersion()?.version, manifest.product_version, 'MCP server identity must match the release package');
  const tools = await client.listTools(); assert.ok(tools.tools.some(t => t.name === 'retrieve'));
  const mcp = await client.callTool({ name: 'retrieve', arguments: { query, limit: 5, contextBudget: 60000 } }, undefined, { timeout });
  assert.ok(!mcp.isError); assert.deepEqual(mcp.structuredContent.data, packet.data);
  const experimentMCP = await client.callTool({ name: 'retrieve', arguments: experimentRequest }, undefined, { timeout });
  assert.ok(!experimentMCP.isError); assert.deepEqual(experimentMCP.structuredContent.data, experimentJS.data);
  const graphConfig = JSON.parse(readFileSync(resolve(root, 'profiles/graph-v2.json'), 'utf8'));
  assert.equal(graphConfig.default_enabled, false);
  assert.equal(hash(resolve(root, 'profiles/graph-v2.json')), manifest.graph_v2.profile_sha256);
  report.checks.push({ name: 'experimental_MCP_CLI_JS_equality_and_default_disabled', passed: true });
  const exact = await client.callTool({ name: 'evidence', arguments: { id: packet.data.reviewed[0].evidence[0].id } });
  assert.ok(exact.structuredContent.data.evidence.pdf_page > 0);
  await client.close(); client = null;
  report.checks.push({ name: 'bundled_MCP_JS_CLI_equality_and_evidence_followup', passed: true, server_version: manifest.product_version, stdout_parse_errors: 0, stderr: diagnostics });
  assert.equal(hash(resolve(root, 'knowledge/graph.sqlite')), manifest.canonical_database_sha256);
  assert.equal(hash(resolve(root, 'knowledge/manifest.json')), manifest.canonical_manifest_sha256);
  report.checks.push({ name: 'canonical_files_unchanged', passed: true });
  report.examples = { definition: packet.data.reviewed.slice(0, 3).map(c => ({ id: c.id, text: c.text, conditions: c.conditions,
    citations: c.evidence.map(e => ({ id: e.id, filename: e.filename, pdf_page: e.pdf_page, quote: e.quote, role: e.role })) })),
    ambiguity: { issue_id: issue.data.issue.issue_id, resolution_status: issue.data.issue.resolution_status, claims: issue.data.claims.map(c => c.id) },
    research_candidate_status: pending.data.claim.review_status };
  report.passed = true;
} catch (error) {
  report.error = { message: error.message, stack: error.stack }; process.exitCode = 1;
} finally {
  await client?.close(); await service?.close(); report.finished_at = new Date().toISOString();
  writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ passed: report.passed, report: reportPath, checks: report.checks.map(c => c.name), error: report.error?.message }));
}
