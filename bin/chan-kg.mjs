#!/usr/bin/env node
import { KnowledgeGraph } from '../src/core.mjs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help')) {
  console.log(`chan-kg <search|concept|neighbors|evidence|coverage|concepts|sources|page> [query/id] [options]
  --kb <directory>            shared graph package directory
  --scope knowledge|source   default: knowledge
  --include-unreviewed       explicitly allow pending candidates
  --review pending|reviewed|rejected
  --limit <n> --offset <n> --depth <1|2> --relation-type <type>
  --max-importance <1|2|3|4> include levels at or above this importance
  --document-id <id|filename> --page <physical-pdf-page> for page browsing
All query results are JSON; diagnostics use stderr. Source search includes speaker identity.`);
  process.exit(0);
}
let graph;
try {
  const command = argv.shift();
  const args = {};
  let kb = process.env.CHAN_KG_PATH;
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (key === '--include-unreviewed') args.includeUnreviewed = true;
    else if (key.startsWith('--')) {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(`${key} 需要参数`);
      if (key === '--kb') kb = value;
      else if (['--scope', '--limit', '--offset', '--depth'].includes(key)) args[key.slice(2)] = value;
      else if (key === '--review') args.reviewStatus = value;
      else if (key === '--relation-type') args.relationType = value;
      else if (key === '--max-importance') args.maxImportance = value;
      else if (key === '--document-id') args.documentId = value;
      else if (key === '--page') args.page = value;
      else throw new Error(`未知选项：${key}`);
    } else positional.push(key);
  }
  args.query = positional.join(' ');
  if (command !== 'search') args.id = args.query;
  kb ??= resolve(dirname(fileURLToPath(import.meta.url)), '../../shared-knowledge/v0.1.0');
  graph = new KnowledgeGraph(kb);
  console.log(JSON.stringify(graph.query(command, args), null, 2));
} catch (error) {
  console.error(JSON.stringify({ status: 'error', message: error.message }));
  process.exitCode = 1;
} finally { graph?.close(); }
