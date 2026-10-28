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
const claim = slug => { const c = graph.getClaim('upper-l027-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l027-c-stage-%' AND review_status='reviewed'").get().n, 36);
  assert.match(claim('trend-divergence-after-at-least-second-center').text, /至少有两个同级别.*至少第二中枢之后.*不能.*已经背驰/);
  assert.notEqual(claim('second-center-proportion-author-estimate').ambiguity_status, 'none');
  assert.match(claim('consolidation-divergence-compare-first-third-types').text, /往往.*第一、第三.*不必都是趋势.*两个盘整/);
  assert.notEqual(claim('first-center-only-consolidation-divergence').ambiguity_status, 'none');
  assert.match(claim('low-position-consolidation-and-buy-types').text, /多数一买.*趋势背驰.*严格一买肯定.*类一买/);
  for (const [strict, analogous] of [['第一类买点', '类第一类买点'], ['第二类买点', '类第二类买点']]) assert.notEqual(graph.query('concept', { id: strict }).data.concept.id, graph.query('concept', { id: analogous }).data.concept.id);
  checks.push('36新增；至少两个同级中枢/第二后不等必背驰，两个盘整可比；多数/肯定及严格与类一二买分别保留，盘背非一律回中枢');

  assert.match(claim('nested-legs-must-be-inside-parent').text, /季度第三段内.*月线段应在季度段内且更小.*每笔成交/);
  assert.match(claim('nested-legs-must-be-inside-parent').review_note, /不等后期严格定义的几何笔/);
  assert.match(claim('precision-theorem-recursive-until-minimum').text, /相应段内.*最低级别.*范围内/);
  assert.match(claim('finite-levels-no-unique-mathematical-point').text, /级别不无限可分.*不能证明.*唯一点状精度.*区间/);
  assert.notEqual(claim('divergence-leg-named-by-type-and-level').ambiguity_status, 'none');
  assert.match(claim('feb5-leg-entered-not-precise-end').text, /只算进入背驰段.*精确点还看1分/);
  assert.match(graph.getClaim('lower-l064-divergence-segment-vs-success').text, /可能.*失效.*成功/);
  checks.push('对应段包含/有限最低级与成交分笔非几何笔完整；不能证明无限唯一点，背驰段命名不覆盖同课或64的未确认/失效状态');

  assert.match(source('0179-b002').text, /17周/);
  assert.match(claim('vanke-quarter-three-segments-original-dates').review_note, /17周不静改季度/);
  assert.match(claim('vanke-numeric-iron-bottom-author-downplays').text, /2.99.*意义不大/);
  assert.match(claim('vanke-quarter-lines-or-area-divergence-signal').text, /任一项.*信号.*两项.*更标准/);
  assert.match(claim('vanke-quarter-lines-or-area-divergence-signal').review_note, /限该季线三段盘背实例/);
  assert.match(claim('analogous-second-buy-no-new-low-600685').text, /不再新低.*600685.*2005第三季2.21.*类第二类/);
  assert.match(claim('large-consolidation-historical-bottom-scope').text, /周线也可能仅长线底部.*日线.*可靠性较低/);
  assert.match(claim('weekly-long-bottom-not-always-historic').review_note, /30年.*猜测而非周期定律/);
  checks.push('万科17周/数字分析自我降权/季线MACD或项不补算法，类二买/周线未必历史底与日线可靠性限制保留');

  assert.match(claim('life-insurer-thirty-no-zero-only-one-forming').text, /否定.*最多正在形成1分钟/);
  assert.match(claim('zero-retest-one-condition-look-lower-end').text, /只是一个条件.*其后股价新低后是否创新低.*5分钟/);
  assert.notEqual(claim('zero-retest-one-condition-look-lower-end').ambiguity_status, 'none');
  assert.match(claim('600331-feb1-center-flanks-comparable').text, /昨天已成.*010935到011410.*两侧各一段/);
  assert.match(claim('not-daily-buy-point-forming-five-minute-partial').text, /有时两三天.*正形成.*大资金与好股票.*部分/);
  assert.match(claim('macd-b-must-retrace-near-zero-not-arbitrary-three').text, /零轴附近.*不能任意.*三段/);
  assert.match(claim('center-b-may-exceed-a-extreme-with-overlap').review_note, /不能抹去同级\/连续次级走势/);
  checks.push('一次回轴非充分、30否定/1分形成、代词未详及600331原时段保留；部分布局非全体已确认，B/中枢三段保留结构前提');

  assert.match(claim('big-leg-before-small-divergence-precision').text, /先.*大级别背驰段.*30分钟急跌.*5分背驰段.*1分定位/);
  assert.match(claim('thirty-down-break-five-down-divergence-third-sell-risk').text, /30分钟下跌刚破位.*5分钟.*99%.*30分钟刚上涨/);
  assert.notEqual(claim('thirty-down-break-five-down-divergence-third-sell-risk').ambiguity_status, 'none');
  assert.match(claim('small-third-buy-t1-not-executable-profit').text, /并非买后不涨.*T\+1.*未必能卖出/);
  assert.match(claim('life-insurer-second-down-center-and-49-confirmation').text, /49元上涨背驰.*30元.*100/);
  assert.match(claim('life-insurer-second-down-center-and-49-confirmation').review_note, /不改旧引文/);
  assert.notEqual(claim('feb2-five-minute-buy-next-week-author-forecast').ambiguity_status, 'none');
  checks.push('大级别方向和背驰段先行、下破/初涨两支及T+1限制不省；99%/10%/30与100为作者展望，49明确旁证不改25原话');

  assert.equal(source('0178-b006').published_at, '2007-02-02 15:11:27');
  assert.equal(source('0182-b006').published_at, '2007-02-02 15:11:27');
  assert.equal(source('0182-b009').published_at, '2007-02-02 15:19:09');
  for (const short of ['0182-b010', '0182-b011', '0182-b012', '0182-b013']) assert.equal(source(short).published_at, '2007-02-05 15:18:33');
  for (const short of ['0182-b014', '0183-b000', '0183-b001']) assert.equal(source(short).published_at, '2007-02-05 15:25:03');
  assert.equal(source('0183-b004').role, 'reader'); assert.match(source('0183-b004').text, /中信证券600640/);
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 179 AND 187").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 5); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 2);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-027'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('19正文补标题时间、7解盘段按两个2/5嵌头分组，前段原日期/读者代码保留；7图5后加含2011图2未核，全书未完成');

  const anchor = claim('precision-theorem-recursive-until-minimum').evidence[0].id;
  const requests = [
    ['search', { query: '级别不无限可分' }, ['search', '级别不无限可分']],
    ['concept', { id: '类第一类买点', limit: 20 }, ['concept', '类第一类买点', '--limit', '20']],
    ['neighbors', { id: '缠中说禅精确大转折点寻找程序定理', depth: 1, limit: 100 }, ['neighbors', '缠中说禅精确大转折点寻找程序定理', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 182 }, ['page', '--document-id', 'volume_1.pdf', '--page', '182']],
    ['search', { query: '中信证券600640', scope: 'source', limit: 8 }, ['search', '中信证券600640', '--scope', 'source', '--limit', '8']],
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
    limits: ['同模型边界检查与模块一致性，不是独立语义审查、数学区间套证明或Windows实际离线/PDF验收。',
      '未验证历史底部必然、MACD普遍充分规则、90%/99%/10%或作者长线价格展望。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l027-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
