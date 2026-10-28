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
const claim = (lesson, slug) => {
  const c = graph.getClaim(`upper-l${String(lesson).padStart(3, '0')}-c-stage-${slug}`);
  assert.ok(c, `${lesson}:${slug}`); return c;
};
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'upper-l010-c-stage-%' OR id LIKE 'upper-l011-c-stage-%' OR id LIKE 'upper-l012-c-stage-%') AND review_status='reviewed'").get().n, 61);
  assert.match(claim(11, 'flying-kiss-definition').text, /略走平后继续按原趋势/);
  assert.match(claim(11, 'lip-kiss-definition').text, /不跌破或升破/);
  assert.match(claim(11, 'wet-kiss-definition').text, /甚至出现反复/);
  assert.match(claim(11, 'flying-kiss-strong-trend-and-later-shake').text, /出现较少，一般在特别强/);
  assert.match(claim(11, 'average-position-short-above-long-bull').text, /短线上、长线下.*女上位.*短线下、长线上.*男上位/);
  checks.push('61新增；飞吻/唇吻/湿吻及均线体位定义完整，甚至反复非必要，飞吻少见且通常特强的语序保留');
  assert.match(claim(11, 'relative-strength-five-versus-ten').text, /5日线上而在10日线下/);
  assert.match(claim(11, 'parameters-capital-time-t0-context').conditions[1], /T\+0/);
  assert.match(claim(11, 'technical-analysis-core-classification').text, /不保证.*百分百/);
  assert.match(claim(11, 'wet-kiss-two-turn-paths-first-exception').exceptions[0], /第一次湿吻/);
  assert.match(claim(12, 'any-entry-risk-no-perfect-kiss-prediction').text, /任何位置.*风险.*100%/);
  checks.push('强弱按评价系统、资金和时间分开；指标不保证路径，第一次湿吻例外和任何位置有风险共同保留');
  const entry = claim(12, 'two-average-buy-points-not-risk-free');
  const strict = graph.query('concept', { id: '第一类买点', limit: 1 }).data.concept;
  const average = graph.query('concept', { id: '均线系统第一买点', limit: 1 }).data.concept;
  assert.notEqual(strict.id, average.id);
  assert.ok(entry.concept_ids.includes(average.id) && !entry.concept_ids.includes(strict.id));
  assert.match(claim(12, 'two-average-sell-points').text, /女上位缠绕后.*第一卖点.*转男上位后首次.*第二卖点/);
  assert.match(claim(12, 'prefer-second-buy-first-sell-asymmetry').text, /第二买点买.*第一卖点卖/);
  assert.match(claim(12, 'system-only-two-principle-and-later-clarification').text, /并非其他点不能买.*风险更大.*只是一招/);
  checks.push('均线系统第一二买卖点独立于严格三类点，买二卖一偏好与其他点可买但风险更大/只是一招限定可查');
  assert.deepEqual(claim(10, 'morning-entry-t0-exceptions').exceptions, ['强力突破走势', '着眼中线逐步建仓']);
  assert.deepEqual(claim(11, 'thirty-average-hold-acceleration-exception-case').exceptions, ['出现放量加速上涨']);
  assert.match(claim(10, 'full-position-reduce-vs-small-position-hold-case').text, /若满仓.*减仓.*占比不高可继续留/);
  assert.match(claim(10, 'nov23-index-divergence-not-technical-beichi').review_note, /不直接等同.*严格趋势背驰/);
  checks.push('无T+0早盘通常不买的两例外、30日线持有的放量加速例外和满仓/低仓分支完整，沪深背离不冒充严格背驰');
  const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get(`volume_1-a53e99c37ca5-p${short}`);
  for (const [short, time] of [['0030-b000', '2006-11-24 12:15:10'], ['0030-b002', '2006-11-23 13:42:46'], ['0030-b003', '2006-11-23 15:11:58'], ['0030-b005', '2006-11-24 13:34:49'], ['0030-b006', '2006-11-24 13:50:35'], ['0030-b007', '2006-11-24 14:14:17'], ['0030-b008', '2006-11-24 15:00:18'], ['0032-b013', '2006-11-27'], ['0034-b004', '2006-11-27 12:19:44'], ['0034-b005', '2006-11-27 15:10:23'], ['0034-b007', '2006-11-28 12:15:13'], ['0034-b008', '2006-11-28 14:56:17'], ['0038-b005', '2006-11-29 15:14:38'], ['0039-b000', '2006-11-30 15:13:57'], ['0042-b005', '2006-12-01 11:37:58'], ['0042-b006', '2006-12-01 12:16:49'], ['0042-b007', '2006-12-01 15:02:23']]) assert.equal(source(short).published_at, time, short);
  assert.equal(source('0030-b002').role, 'author_commentary');
  assert.equal(source('0039-b002').role, 'author_commentary');
  assert.equal(source('0027-b009').published_at, null);
  for (const short of ['0033-b004', '0033-b005', '0033-b006', '0034-b000', '0034-b001', '0034-b002']) {
    const p = source(short); assert.equal(p.role, 'unknown'); assert.match(p.speaker, /喜欢数学的女孩.*未核/);
    assert.equal(graph.db.prepare("SELECT count(*) AS n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=? AND c.review_status='reviewed'").get(p.id).n, 0);
  }
  checks.push('裸时间仅管后文；自引昨日解盘非读者，11/27回放非11/24回复，2005旧名转载六段unknown未用作作者证据，课程10不造完整日期');
  const figures = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 27 AND 43").all();
  assert.equal(figures.filter(x => x.origin_status === 'later_annotation').length, 3);
  assert.equal(figures.filter(x => x.origin_status === 'unverified').length, 3);
  const historical = claim(12, '000958-weekly-two-points-not-best-now');
  assert.match(historical.text, /7月22日约2.2.*11月3日约2.6/); assert.doesNotMatch(historical.text, /2005/);
  assert.deepEqual(claim(12, 'maotai-ten-hold-no-sell-yet').evidence.map(e => e.pdf_page).sort((a, b) => a - b), [41, 42]);
  for (const lesson of ['010', '011', '012']) assert.equal(graph.db.prepare('SELECT processing_status FROM units WHERE id=?').get(`lesson-${lesson}`).processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('3后加3未核图，000958正文不补2005年，茅台跨页当时未有卖点；三课仍with_pending，全书语义false');
  const anchor = claim(12, 'maotai-ten-hold-no-sell-yet').evidence.find(e => e.pdf_page === 42).id;
  const requests = [
    ['search', { query: '唇吻指短期均线' }, ['search', '唇吻指短期均线']],
    ['concept', { id: '均线系统第一买点', limit: 30 }, ['concept', '均线系统第一买点', '--limit', '30']],
    ['neighbors', { id: '湿吻', depth: 1, limit: 100 }, ['neighbors', '湿吻', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 33 }, ['page', '--document-id', 'volume_1.pdf', '--page', '33']],
    ['search', { query: '喜欢数学的女孩', scope: 'source', limit: 8 }, ['search', '喜欢数学的女孩', '--scope', 'source', '--limit', '8']],
    ['coverage', {}, ['coverage']],
  ];
  const parity = [];
  for (const [command, args, argv] of requests) {
    const a = JSON.parse(JSON.stringify(graph.query(command, args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command, args))), a);
    const cli = spawnSync(process.execPath, [resolve(agent, 'bin/chan-kg.mjs'), ...argv, '--kb', root], { encoding: 'utf8', maxBuffer: 24 * 1024 * 1024 });
    assert.equal(cli.status, 0, cli.stderr); assert.deepEqual(JSON.parse(cli.stdout), a);
    parity.push({ command, args, cli_matches_shared: true, desktop_module_matches_shared: true });
  }
  assert.deepEqual({ database: sha(resolve(root, 'graph.sqlite')), manifest: sha(resolve(root, 'manifest.json')) }, before);
  const report = { graph_version: graph.metadata.graph_version, schema_version: graph.metadata.schema_version, checks, parity,
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['不是Windows成品真实离线、PDF缩放旋转或交互验收。', '同模型边界检查不代表独立语义复核或吻/均线系统的收益、概率、风险最优性证明。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l010-l012-verification.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
