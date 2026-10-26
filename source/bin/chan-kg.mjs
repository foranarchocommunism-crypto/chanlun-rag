#!/usr/bin/env node
import { KnowledgeGraph } from '../src/core.mjs';
import { RetrievalService } from '../src/retrieval.mjs';
import { locations } from '../src/config.mjs';

const argv = process.argv.slice(2);
if (!argv.length || argv.includes('--help')) {
  console.log(`chan-kg <retrieve|status|claim|issue|relation|search|concept|neighbors|evidence|coverage|concepts|sources|page> [query/id] [options]
  --kb <directory>            shared graph package directory
  --index <directory>         version-bound derived retrieval index
  --mode knowledge|research|source   retrieve default: knowledge
  --profile lexical|dense|hybrid|hybrid-rerank|hybrid-graph|hybrid-graph-rerank|hybrid-graph-v2-rerank
  --trace                     include bounded stage rankings for replay
  --context-budget <codepoints> --candidate-budget <n>
  --graph-depth <0|1|2> --graph-budget <n> --issue-budget <n>
  --rerank-budget <20|40|44|48>  v2 experimental default48; protects40 text candidates
  --allow-degraded            explicitly permit visible lexical fallback
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
  const paths = {};
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (key === '--include-unreviewed') args.includeUnreviewed = true;
    else if (key === '--allow-degraded') args.allowDegraded = true;
    else if (key === '--trace') args.trace = true;
    else if (key.startsWith('--')) {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(`${key} 需要参数`);
      if (key === '--kb') paths.kbPath = value;
      else if (key === '--index') paths.indexPath = value;
      else if (key === '--models') paths.modelPath = value;
      else if (key === '--policy') paths.policyPath = value;
      else if (['--mode', '--profile'].includes(key)) args[key.slice(2)] = value;
      else if (['--context-budget', '--candidate-budget', '--graph-depth', '--graph-budget', '--issue-budget', '--rerank-budget'].includes(key)) {
        if (!/^\d+$/.test(value)) throw new Error(`${key} requires an integer`);
        const name = key.slice(2).replace(/-([a-z])/g, (_m, c) => c.toUpperCase()); args[name] = Number(value);
      }
      else if (['--scope', '--limit', '--offset', '--depth'].includes(key)) args[key.slice(2)] = value;
      else if (key === '--review') args.reviewStatus = value;
      else if (key === '--relation-type') args.relationType = value;
      else if (key === '--max-importance') args.maxImportance = value;
      else if (key === '--document-id') args.documentId = value;
      else if (key === '--concept-id') args.conceptId = value;
      else if (key === '--page') args.page = value;
      else throw new Error(`未知选项：${key}`);
    } else positional.push(key);
  }
  const query = positional.join(' ');
  const serviceCommands = ['retrieve', 'status', 'claim', 'issue', 'relation'];
  if (command === 'retrieve') {
    args.query = query;
    if (args.limit !== undefined && /^\d+$/.test(args.limit)) args.limit = Number(args.limit);
  } else if (serviceCommands.includes(command)) { if (query) args.id = query; }
  else { args.query = query; if (command !== 'search') args.id = query; }
  graph = serviceCommands.includes(command) ? new RetrievalService(paths) : new KnowledgeGraph(locations(paths).kbPath);
  console.log(JSON.stringify(await graph.query(command, args), null, 2));
} catch (error) {
  console.error(JSON.stringify({ status: 'error', code: error.code ?? 'INVALID_REQUEST', message: error.message, details: error.details }));
  process.exitCode = 1;
} finally { await graph?.close(); }
