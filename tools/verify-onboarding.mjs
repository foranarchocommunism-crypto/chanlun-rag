import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, readdirSync, mkdtempSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
const root = resolve(process.argv[2]), reportFile = resolve(process.argv[3]);
const expectedVersion = JSON.parse(readFileSync(resolve(root, 'release-manifest.json'), 'utf8')).product_version;
const node = resolve(root, 'runtime/x64/node.exe'), helper = resolve(root, 'onboarding/connect.mjs');
const call = (mode, input) => spawnSync(node, [helper, mode], { input, encoding: 'utf8', windowsHide: true, timeout: 300000, cwd: tmpdir() });
const launch = label => spawnSync(resolve(process.env.SystemRoot, 'System32/cmd.exe'),
  ['/d', '/s', '/c', `""${resolve(root, label + '.cmd')}" < nul"`],
  { windowsVerbatimArguments: true, encoding: 'utf8', windowsHide: true, timeout: 300000, cwd: tmpdir() });
const report = { root, passed: false, checks: [], independent_clean_windows_verified: false, gui_clients_verified: [] };
let client;
try {
  const result = launch('开始连接'); assert.equal(result.status, 0, result.stderr);
  const generated = JSON.parse(readFileSync(resolve(root, '连接资料/客户端配置.json'), 'utf8'));
  const server = generated.mcpServers['chanlun-rag'];
  assert.equal(server.command, node); assert.equal(server.args.length, 1); assert.ok(existsSync(server.args[0]));
  report.checks.push('paths_generated_from_actual_extracted_directory');
  const temporary = mkdtempSync(join(tmpdir(), 'chanlun-existing-'));
  const target = join(temporary, 'mcp.json');
  const before = JSON.stringify({ otherSetting: 42, mcpServers: { existing: { command: 'preserve-this' } } });
  writeFileSync(target, before);
  const merged = call('merge', target + '\n'); assert.equal(merged.status, 0, merged.stderr);
  const after = readFileSync(target, 'utf8'), config = JSON.parse(after);
  assert.equal(config.otherSetting, 42); assert.deepEqual(config.mcpServers.existing, { command: 'preserve-this' });
  assert.deepEqual(config.mcpServers['chanlun-rag'], server);
  const backup = readdirSync(temporary).find(x => x.endsWith('.bak')); assert.equal(readFileSync(join(temporary, backup), 'utf8'), before);
  assert.notEqual(call('merge', target + '\n').status, 0); assert.equal(readFileSync(target, 'utf8'), after);
  writeFileSync(target, '{invalid'); assert.notEqual(call('merge', target + '\n').status, 0); assert.equal(readFileSync(target, 'utf8'), '{invalid');
  report.checks.push('existing_connections_preserved_exact_backup_duplicate_and_invalid_json_refused');
  const Client = (await import(pathToFileURL(resolve(root, 'app/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js')))).Client;
  const StdioClientTransport = (await import(pathToFileURL(resolve(root, 'app/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js')))).StdioClientTransport;
  const deny = pathToFileURL(resolve(root, 'app/scripts/deny-network.mjs')).href;
  const transport = new StdioClientTransport({ ...server, cwd: tmpdir(), stderr: 'pipe', env: { ...process.env,
    PATH: resolve(root, 'runtime/x64') + ';' + process.env.SystemRoot + '\\System32', NODE_PATH: '', NODE_OPTIONS: '--import=' + deny } });
  client = new Client({ name: 'new-user-config-verifier', version: '1.0.0' }, { capabilities: {} });
  await client.connect(transport);
  assert.equal(client.getServerVersion().version, expectedVersion);
  const resultMCP = await client.callTool({ name: 'retrieve', arguments: { query: '中枢是什么，成立需要什么条件？', limit: 5 } }, undefined, { timeout: 300000 });
  assert.ok(!resultMCP.isError); assert.ok(resultMCP.structuredContent.data.reviewed.some(x => x.id === 'upper-l017-center-definition'));
  report.checks.push('generated_command_and_args_real_MCP_retrieve_with_network_denied');
  await client.close(); client = null;
  const checked = launch('检查是否正常'); assert.equal(checked.status, 0, checked.stderr); assert.ok(checked.stdout.includes('检查通过'));
  report.checks.push('plain_language_self_check_real_models_and_definition');
  report.passed = true;
} catch (error) { report.error = error.stack; process.exitCode = 1; }
finally { await client?.close(); writeFileSync(reportFile, JSON.stringify(report, null, 2)+'\n'); console.log(JSON.stringify(report)); }
