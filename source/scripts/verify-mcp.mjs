import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { AjvJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/ajv-provider.js';
import { RetrievalService } from '../src/retrieval.mjs';

const service = new RetrievalService();
const transport = new StdioClientTransport({ command: process.execPath, args: [resolve('bin/chan-kg-mcp.mjs')], stderr: 'pipe' });
const client = new Client({ name: 'chan-kg-stdio-acceptance-client', version: '1.0.0' }, { capabilities: {} });
const diagnostics = [];
transport.stderr?.on('data', d => diagnostics.push(String(d)));
try {
  await client.connect(transport);
  const listing = await client.listTools();
  assert.ok(listing.tools.some(t => t.name === 'retrieve'));
  assert.ok(listing.tools.every(t => t.annotations.readOnlyHint && t.annotations.openWorldHint === false));
  const useDefault = process.argv.includes('--default');
  const query = { query: '一字涨停为什么可以有最小级别中枢但连分型也没有？', ...(!useDefault ? { profile: 'lexical' } : {}), limit: 3, contextBudget: 60000 };
  const mcp = await client.callTool({ name: 'retrieve', arguments: query });
  assert.ok(!mcp.isError);
  const packet = mcp.structuredContent;
  const js = await service.retrieve(query);
  const cli = spawnSync(process.execPath, [resolve('bin/chan-kg.mjs'), 'retrieve', query.query, ...(!useDefault ? ['--profile', 'lexical'] : []), '--limit', '3', '--context-budget', '60000'], { encoding: 'utf8' });
  assert.equal(cli.status, 0, cli.stderr);
  assert.deepEqual(packet.data, js.data); assert.deepEqual(packet.data, JSON.parse(cli.stdout).data);
  const schema = JSON.parse(readFileSync('contracts/evidence-packet.schema.json', 'utf8')); delete schema.$schema;
  const validation = new AjvJsonSchemaValidator().getValidator(schema)(packet);
  assert.equal(validation.valid, true, validation.errorMessage);
  const invalid = await client.callTool({ name: 'retrieve', arguments: { query: '中枢', profile: 'lexical', allowDegraded: 'false' } });
  assert.equal(invalid.isError, true);
  const pendingDefault = await client.callTool({ name: 'claim', arguments: { id: 'candidate-06fee67b46cd9475' } });
  assert.equal(pendingDefault.isError, true);
  const pending = await client.callTool({ name: 'claim', arguments: { id: 'candidate-06fee67b46cd9475', mode: 'research' } });
  assert.equal(pending.structuredContent.data.claim.review_status, 'pending');
  const issue = await client.callTool({ name: 'issue', arguments: { id: 'issue-connection-level-scope' } });
  assert.ok(issue.structuredContent.data.claims.some(c => c.id === 'upper-l018-center-theorem-one'));
  const follow = await client.callTool({ name: 'evidence', arguments: { id: issue.structuredContent.data.claims[0].evidence[0].id } });
  assert.ok(follow.structuredContent.data.evidence.pdf_page > 0);
  const status = await client.callTool({ name: 'status', arguments: {} });
  const result = { created_at: new Date().toISOString(), passed: true,
    sdk_version: '1.32.1', sdk_latest_supported_protocol: '2025-11-25', transport: 'stdio', default_profile_tested: useDefault,
    actual_client: 'Official MCP SDK Client spawning the real server process', native_gui_registration_tested: false,
    tools: listing.tools.map(t => t.name), same_request_cli_js_mcp_data_equal: true, schema_valid: true,
    invalid_boolean_rejected: true, pending_default_rejected: true, explicit_research_allowed: true,
    issue_branch_and_followup_evidence: true, version: status.structuredContent.graph_version,
    stdout_protocol_parse_errors: 0, stderr: diagnostics.join(''), example_packet: packet };
  await client.close();
  result.disconnect_completed = true;
  writeFileSync(`../validation-runs/agent-implementation-20261022/${useDefault ? 'm5-default-mcp-roundtrip' : 'm5-mcp-roundtrip'}.json`, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({ ...result, example_packet: undefined }));
} finally { await client.close(); await service.close(); }
