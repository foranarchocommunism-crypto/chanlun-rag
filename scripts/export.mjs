import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';

const root = resolve(process.argv[2] ?? process.env.CHAN_KG_PATH ?? '../shared-knowledge/v0.1.0');
const graph = new KnowledgeGraph(root);
try {
  const out = resolve(root, 'exports');
  mkdirSync(out, { recursive: true });
  const claims = graph.db.prepare("SELECT id FROM claims WHERE review_status='reviewed' ORDER BY importance_level,id").all().map(r => graph.getClaim(r.id));
  const concepts = graph.concepts().data.concepts;
  const relations = graph.db.prepare("SELECT * FROM relations WHERE review_status='reviewed' ORDER BY importance_level,id").all().map(r => ({ ...r, claim_ids: JSON.parse(r.claim_ids) }));
  for (const [name, rows] of [['claims', claims], ['concepts', concepts], ['relations', relations]]) {
    writeFileSync(resolve(out, `${name}.jsonl`), rows.map(r => JSON.stringify({ graph_version: graph.metadata.graph_version, ...r })).join('\n') + '\n');
  }
  const sections = claims.map(c => `## ${c.text}\n\n- ID：${c.id}\n- 重要性：${c.importance_level}级；${c.importance_reason}\n- 类型：${c.kind === 'explicit' ? '原文明说' : '整理推论'}；复核状态：${c.review_status}\n- 条件：${c.conditions.join('；') || '见命题及原文'}\n- 例外：${c.exceptions.join('；') || '未在本条单独列出'}\n\n${c.evidence.map(e => `> ${e.quote}\n\n出处：${e.filename}，实际PDF第${e.pdf_page}页，印刷第${e.printed_page ?? '未标'}页；${e.role} / ${e.speaker}；证据ID ${e.id}。`).join('\n\n')}`);
  writeFileSync(resolve(out, 'reviewed-knowledge.md'), `# 缠中说禅已复核知识\n\n图谱版本：${graph.metadata.graph_version}。分级为整理判断。\n\n${sections.join('\n\n')}`);
  writeFileSync(resolve(out, 'coverage.json'), JSON.stringify(graph.coverage(), null, 2));
  console.log(JSON.stringify({ graph_version: graph.metadata.graph_version, exported_claims: claims.length, concepts: concepts.length, relations: relations.length, output: out }));
} finally { graph.close(); }
