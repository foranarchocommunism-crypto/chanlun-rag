import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { resolve } from 'node:path';
const root = resolve(process.argv[2]);
for (const args of [['/d', '/s', '/c', 'call', resolve(root, 'chan-kg-mcp.cmd')], ['/d', '/c', 'call', resolve(root, 'chan-kg-mcp.cmd')]]) {
  let diagnostics = '', client;
  try {
    const transport = new StdioClientTransport({ command: resolve(process.env.SystemRoot, 'System32/cmd.exe'), args, stderr: 'pipe' });
    transport.stderr?.on('data', d => { diagnostics += String(d); });
    client = new Client({ name: 'launcher-quote-probe', version: '1.0.0' }, { capabilities: {} });
    await client.connect(transport);
    console.log(JSON.stringify({ args, connected: true, server: client.getServerVersion() }));
  } catch (error) { console.log(JSON.stringify({ args, connected: false, error: error.message, diagnostics })); }
  finally { await client?.close(); }
}
