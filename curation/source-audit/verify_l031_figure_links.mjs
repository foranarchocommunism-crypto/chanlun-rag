import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
import { KnowledgeGraph as DesktopGraph } from '../../../chan-kg-desktop/vendor/core.mjs';

const agent = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const root = resolve(agent, '../shared-knowledge/v0.1.0');
const sha = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const before = { database: sha(resolve(root, 'graph.sqlite')), manifest: sha(resolve(root, 'manifest.json')) };
const graph = new KnowledgeGraph(root), desktop = new DesktopGraph(root);
const expected = {
  'long-pressure-free-funds-and-leverage-story': ['p0219-b002', 'p0219-fig1', 'unverified'],
  'feb15-center-1048-1129-third-buy-1413': ['p0224-b006', 'p0224-fig1', 'later_annotation'],
  'feb16-1405-divergence-and-later-selloff-case': ['p0226-b008', 'p0226-fig1', 'later_annotation'],
  'weekly-three-legs-original-explicitly-qualified': ['p0231-b000', 'p0230-fig1', 'later_annotation'],
  'weekly-center-first-daily-then-expand-case': ['p0231-b003', 'p0230-fig1', 'later_annotation'],
};
const checks = [];
try {
  for (const [slug, [passage, figure, origin]] of Object.entries(expected)) {
    const cid = 'upper-l031-c-stage-' + slug;
    const c = graph.getClaim(cid);
    const e = c.evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-' + passage);
    assert.ok(e, cid); assert.deepEqual(e.figure_ids, ['volume_1-a53e99c37ca5-' + figure]);
    const shared = graph.query('evidence', { id: e.id });
    assert.equal(shared.data.evidence.figures.length, 1);
    assert.equal(shared.data.evidence.figures[0].origin_status, origin);
    assert.ok(shared.data.evidence.figures[0].note.length > 30);
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query('evidence', { id: e.id }))), JSON.parse(JSON.stringify(shared)));
    const cli = spawnSync(process.execPath, [resolve(agent, 'bin/chan-kg.mjs'), 'evidence', e.id, '--kb', root], { encoding: 'utf8', maxBuffer: 12 * 1024 * 1024 });
    assert.equal(cli.status, 0, cli.stderr); assert.deepEqual(JSON.parse(cli.stdout), JSON.parse(JSON.stringify(shared)));
    checks.push({ claim_id: cid, evidence_id: e.id, figure_ids: e.figure_ids, origin, cli_and_desktop_module_match: true });
  }
  assert.deepEqual({ database: sha(resolve(root, 'graph.sqlite')), manifest: sha(resolve(root, 'manifest.json')) }, before);
  const report = { graph_version: graph.metadata.graph_version, checks, pass: true,
    database_and_manifest_unchanged: true, limits: ['只证明五条证据配图关联与CLI/模块返回；不证明Windows实际图像显示或独立语义复核。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l031-figure-links-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, evidence_links_verified: checks.length, pass: true }));
} finally { graph.close(); desktop.close(); }
