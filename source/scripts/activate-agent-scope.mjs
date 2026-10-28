import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const file = resolve('curation/delivery-scope.json');
const previous = readFileSync(file);
const old = JSON.parse(previous);
assert.equal(old.active_deliverable, 'shared_knowledge_base_only', 'Current scope already changed; inspect history instead of overwriting.');
const history = resolve('curation/scope-history');
mkdirSync(history, { recursive: true });
const historicalPath = resolve(history, '2026-10-20-knowledge-only.json');
assert.ok(!existsSync(historicalPath));
writeFileSync(historicalPath, previous);
writeFileSync(file, JSON.stringify({ updated_at: new Date().toISOString(), source: 'direct_user_instruction_implement_approved_plan',
  user_instruction: "Read and implement this plan '/C:/Users/13240/Desktop/RAG/完整实施计划.md'.",
  plan: '../../完整实施计划.md', active_deliverable: 'offline_windows_agent_rag_knowledge_graph',
  supersedes: { path: 'scope-history/2026-10-20-knowledge-only.json', sha256: createHash('sha256').update(previous).digest('hex') },
  required: ['Shared retrieval core: CLI/JSON, JavaScript API, MCP stdio', 'CPU offline lexical, semantic, evidence-supported graph retrieval',
    'Preserve reviewed claims including ambiguity; explicit research/source modes', 'Independent portable directory and ZIP including runtime/models/data/indexes/licenses',
    'M0-M7 gates and actual extracted-artifact verification from the approved plan'],
  excluded: ['Human desktop application', 'Required paid answer-generation API', 'Forced resolution or promotion of all ambiguous/pending claims'],
  knowledge_policy: 'Preserve canonical SQLite and fixed sources; formal semantic changes use separately versioned curation.',
  old_desktop_archive: 'Moved to Recycle Bin by user; restoring it is not required.',
  completion_rule: 'All M0-M7 requirements need current direct evidence; implementation, semantic coverage, and release verification remain distinct.'
}, null, 2) + '\n');
console.log(JSON.stringify({ active_scope: file, history: historicalPath }));
