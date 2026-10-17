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
  const c = graph.getClaim(`lower-l${lesson}-c-stage-${slug}`);
  assert.ok(c, `${lesson}:${slug}`);
  return c;
};
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'lower-l107-c-stage-%' OR id LIKE 'lower-l108-c-stage-%') AND review_status='reviewed'").get().n, 54);
  assert.match(claim(107, 'running-rebound-later-high-not-guaranteed').text, /末上不保证高过首上.*手续费/);
  assert.match(claim(107, 'segment-from-first-rise-author-safety-wording').text, /30分钟反弹按5分钟节奏/);
  assert.match(claim(107, 'aug21-t1-first-sell-second-sell-after-low-open').text, /T\+1可能.*无法卖出.*不破顶或盘整背驰/);
  checks.push('54新增；奔走型末上/手续费风险、30按5分段与T+1首卖无法执行同时可查，二卖原句或不误为且');
  const formation = claim(107, 'uptrend-formation-wording-not-completed-type');
  assert.notEqual(formation.ambiguity_status, 'none');
  assert.match(formation.text, /第三类买点并形成非背驰.*未有扭转信号/);
  assert.match(graph.getClaim('upper-l017-trend-definition').text, /至少.*两个.*完成走势类型/);
  assert.notEqual(claim(107, 'center-three-subtypes-up-down-up-context').ambiguity_status, 'none');
  assert.match(graph.getClaim('lower-l064-uptrend-center-standard-decomposition').text, /标准分解.*下上下/);
  checks.push('趋势形成信号与两中枢完成趋势并列；反弹上下上与标准上涨中枢下上下未因日期覆盖');
  const bottom = claim(108, 'bottom-precise-first-buy-to-first-third-point');
  assert.match(bottom.text, /第一类买点.*其引发中枢首次.*先三卖.*失败.*先三买/);
  assert.match(claim(108, 'fractal-bottom-coarser-entry').text, /较粗糙/);
  assert.match(claim(108, 'fractal-bottom-low-fail-upper-success-at-least-stroke').text, /跌破最低点.*失败.*有效站住.*至少/);
  assert.deepEqual(claim(108, 'fractal-bottom-low-fail-upper-success-at-least-stroke').evidence.map(e => e.pdf_page).sort((a, b) => a - b), [421, 422]);
  assert.match(claim(108, 'buy-failed-down-probe-not-upper-boundary').text, /不是在底部的区间上买.*下探失败.*分型意义/);
  checks.push('底部精确类型/较粗分型两入口独立，第一/首次/所属中枢与三卖失败保留，跨页和下探失败买入可查');
  assert.match(claim(108, 'aug29-month-2284-no-break-september').text, /2284—2952.*若9月破2284.*10月/);
  assert.match(claim(108, 'month-no-market-before-october-effective-2952').text, /10月有效确认站住2952前/);
  assert.deepEqual(claim(108, 'week-2284-2601-containment-2523-exception').exceptions, ['8月29日当周最后一天突然突破2523']);
  assert.match(claim(108, 'day-bottom-2284-2455-still-building').text, /2284—2455/);
  assert.equal(claim(108, 'aug29-month-2284-no-break-september').evidence[0].published_at, '2008-08-29');
  checks.push('月2284/2952、周2284/2601及2523例外、日2284/2455分层；未把图嵌09:15:01反填课程时间');
  const date = short => graph.db.prepare('SELECT role,speaker,published_at FROM passages WHERE id=?').get(`volume_2-5332cd1b6038-p${short}`);
  assert.equal(date('0425-b003').published_at, '2008-09-02 15:15:15');
  assert.equal(date('0425-b004').published_at, '2008-09-03 15:14:03');
  assert.equal(date('0425-b005').published_at, '2008-09-03 15:14:03');
  assert.equal(date('0425-b006').published_at, '2008-09-05 15:08:42');
  assert.equal(date('0426-b009').published_at, '2008-09-11 16:14:14');
  assert.equal(date('0426-b010').published_at, '2008-09-12 12:59:29');
  assert.equal(date('0426-b010').role, 'author_commentary');
  assert.equal(date('0426-b010').speaker, '缠中说禅');
  assert.equal(date('0427-b000').published_at, '2008-09-18 10:26:15');
  for (const [short, time] of [['0427-b008', '2008-09-23 15:40:14'], ['0427-b009', '2008-09-24 14:38:08'], ['0427-b010', '2008-09-25 20:14:17'], ['0427-b011', '2008-09-26 10:32:38']]) assert.equal(date(short).published_at, time);
  checks.push('13段日期身份修正逐项核对；426结束语非读者、9/12独立解盘；427被引9/4标题未污染9/18');
  assert.match(claim(108, 'sep25-daily-stroke-confirmed-weekly-open').text, /日笔已无问题.*周笔仍看/);
  assert.match(claim(108, 'sep11-larger-center-next-buy-new-level').text, /下一买点须站在新级别/);
  assert.equal(claim(108, 'sep12-nonfirst-center-ninety-estimate').ambiguity_status, 'author_probability_not_independently_verified');
  assert.ok(claim(108, 'sep12-nonfirst-center-ninety-estimate').conditions[0].includes('非第一中枢'));
  assert.match(claim(108, 'sep1-october-beauty-not-timing-rule').text, /美学.*实际操作可不理/);
  checks.push('9/25日笔已成与周笔待定、9/11新级别数中枢、9/12非首中枢和90%作者估计及美学周期边界保留');
  const figures = graph.db.prepare("SELECT * FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 416 AND 427").all();
  assert.equal(figures.length, 5);
  assert.ok(figures.every(f => f.origin_status === 'later_annotation'));
  for (const lesson of [107, 108]) assert.equal(graph.db.prepare('SELECT processing_status FROM units WHERE id=?').get(`lesson-${lesson}`).processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('5图均后加且制作者未核；两课semantic_read_with_pending，全书语义完成仍false');
  const anchor = claim(108, 'fractal-bottom-low-fail-upper-success-at-least-stroke').evidence.find(e => e.pdf_page === 422).id;
  const requests = [
    ['search', { query: '上下上反弹的末上不保证' }, ['search', '上下上反弹的末上不保证']],
    ['concept', { id: '底', limit: 50 }, ['concept', '底', '--limit', '50']],
    ['neighbors', { id: '底', depth: 1, limit: 100 }, ['neighbors', '底', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_2.pdf', page: 426 }, ['page', '--document-id', 'volume_2.pdf', '--page', '426']],
    ['search', { query: '收盘马上有事', scope: 'source' }, ['search', '收盘马上有事', '--scope', 'source']],
    ['coverage', {}, ['coverage']],
  ];
  const parity = [];
  for (const [command, args, argv] of requests) {
    const a = JSON.parse(JSON.stringify(graph.query(command, args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command, args))), a);
    const cli = spawnSync(process.execPath, [resolve(agent, 'bin/chan-kg.mjs'), ...argv, '--kb', root], { encoding: 'utf8', maxBuffer: 24 * 1024 * 1024 });
    assert.equal(cli.status, 0, cli.stderr);
    assert.deepEqual(JSON.parse(cli.stdout), a);
    parity.push({ command, args, cli_matches_shared: true, desktop_module_matches_shared: true });
  }
  assert.deepEqual({ database: sha(resolve(root, 'graph.sqlite')), manifest: sha(resolve(root, 'manifest.json')) }, before);
  const report = { graph_version: graph.metadata.graph_version, schema_version: graph.metadata.schema_version, checks, parity,
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['CLI及公共/桌面查询模块一致不是Windows成品真实交互/离线验收。', '同模型边界检查不是独立语义审查、收益/概率回测或所有跨课歧义解决。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l107-l108-verification.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
