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
const claim = slug => { const c = graph.getClaim('upper-l025-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l025-c-stage-%' AND review_status='reviewed'").get().n, 50);
  assert.match(claim('kiss-average-and-macd-auxiliary-not-center').text, /或然率.*辅助工具.*不能与中枢.*混用/);
  assert.match(claim('macd-usual-parameters-and-ultrafast-limit').text, /一般使用12、26、9.*太慢/);
  assert.match(claim('macd-usual-parameters-and-ultrafast-limit').review_note, /不能反推14课/);
  assert.match(claim('rapid-one-minute-height-exception-600779').conditions[0], /一分钟急促上升/);
  assert.match(claim('rapid-one-minute-height-exception-600779').text, /两次柱高不再突破.*即使面积更大/);
  assert.match(claim('rapid-one-minute-height-exception-600779').review_note, /其他情况必须配黄白线/);
  checks.push('50新增；吻/均线/MACD辅助与中枢分开，12/26/9不倒填长一倍，急速一分钟柱高警告保留面积更大和特殊前提');

  assert.match(claim('limit-up-sine-indicator-not-divergence').text, /一字涨停.*不能按通常背驰.*中枢.*持续上移/);
  assert.match(claim('limit-up-longer-macd-and-resistance-warning').text, /警告.*阻力及涨停失封/);
  assert.match(claim('usual-two-center-final-lines-or-area-or-height').text, /黄白线不创新高，或柱面积、或伸长高度/);
  assert.match(claim('usual-two-center-final-lines-or-area-or-height').review_note, /不静默改成线柱必须全部同弱/);
  assert.match(claim('shrinking-bars-not-divergence-combined-conditions').text, /不是一回事.*综合条件.*零轴/);
  assert.match(claim('zero-axis-center-at-least-chart-level').text, /不一定恰为该级别.*至少.*周线.*三段/);
  checks.push('一字涨停指标失真、零轴至少级别、常见两中枢形态的或项与柱缩非背驰分开，不省完整结构');

  assert.match(claim('outer-high-touch-needs-sublevel-retrace').text, /尚不能断言.*至少30分钟.*单5分钟/);
  assert.match(claim('direct-break-old-up-center-needs-second-new-down').text, /再成第二个下方中枢.*罕见|罕见.*再成第二个下方中枢/);
  assert.match(claim('thirty-minute-center-needs-five-minute-three').text, /三段30分钟.*至少三段5分钟/);
  assert.match(claim('daily-three-overlap-bars-practical-heuristic').text, /至少三根以上重合.*基本/);
  assert.match(claim('daily-three-overlap-bars-practical-heuristic').review_note, /非充分必要/);
  assert.match(claim('three-straight-chart-swings-not-daily-center').review_note, /不是所有三根K线/);
  checks.push('外围高点/中枢沿与回拉级别、前上涨中枢/两个新下跌中枢、图上直线/递归走势及实用提示/严格定义分开');

  assert.match(claim('third-buy-needs-subsub-divergence-or-double-retest').text, /次次级别背驰或双次回拉确认/);
  assert.match(claim('execute-level-points-not-extra-confirmation').text, /相应级别.*额外确认.*部分/);
  assert.match(claim('mobile-fraction-quarter-third-half-in-bull').text, /1\/4至1\/3.*1\/2.*牛市/);
  assert.match(claim('rapid-market-one-minute-mobile-exit-not-only-frame').text, /机动资金.*不得追高.*综合30分钟.*缓和.*5或30/);
  assert.match(claim('mobile-cash-and-small-capital-all-in-condition').text, /特别小资金.*前提.*充分把握/);
  assert.match(claim('imminent-suspension-risk-no-time-to-correct').text, /快停牌.*技术再好.*没时间改错/);
  assert.notEqual(claim('imminent-suspension-risk-no-time-to-correct').ambiguity_status, 'none');
  checks.push('三买信号确认与不等额外确认分开；机动比例/快速行情/小资金条件保留，临停不能改错不被复利必然修辞覆盖');

  assert.match(claim('jan26-one-minute-not-five-and-time-difference').text, /否定5分.*1分.*10:56.*10:57/);
  assert.match(claim('jan26-first-second-buy-and-lowest-third-difficult').text, /最低.*很难/);
  assert.match(claim('jan26-first-second-buy-and-lowest-third-difficult').review_note, /很难不是绝对不存在/);
  assert.match(claim('first-second-third-price-order-original-claim').text, /第一类买点比第二类低/);
  assert.match(graph.getClaim('lower-l101-c-stage-second-buy-below-first-permitted').text, /二买最弱.*可以跌破一买/);
  assert.notEqual(claim('first-second-third-price-order-original-claim').ambiguity_status, 'none');
  assert.ok(claim('macd-zero-retrace-before-level-divergence').evidence.every(e => !e.quote.includes('从图上看个人认为')));
  assert.match(source('0153-b012').text, /从图上看个人认为/);
  assert.match(claim('life-insurer-49-45-38-branches-case').text, /49那天不是背驰/);
  checks.push('1分/5分与10:56/10:57不抹差异，最低级三买难非绝无；25价序与101二买可更低并存，未核括注及人寿原语气不补确定解释');

  for (const [short, speaker] of [['0149-b009', '赚到了'], ['0150-b005', '天山飞狐'], ['0150-b006', '天山飞狐']]) {
    assert.equal(source(short).role, 'reader'); assert.equal(source(short).speaker, speaker); assert.equal(source(short).published_at, null);
  }
  assert.equal(source('0151-b008').speaker, null);
  assert.equal(source('0151-b009').published_at, '2007-01-24 14:59:52');
  for (let block = 10; block < 16; block++) { const p = source(`0151-b${String(block).padStart(3, '0')}`); assert.equal(p.role, 'author_commentary'); assert.equal(p.published_at, '2007-01-24 15:40:48'); }
  for (let block = 4; block < 7; block++) assert.equal(source(`0156-b${String(block).padStart(3, '0')}`).published_at, '2007-01-25 21:16:36');
  assert.equal(source('0161-b002').published_at, '2007-01-26 15:39:30');
  for (let block = 3; block < 7; block++) assert.equal(source(`0161-b${String(block).padStart(3, '0')}`).published_at, '2007-01-29 15:22:17');
  for (const id of ['candidate-a99741755b8a7b42', 'candidate-989aab17c194d6fb']) assert.equal(graph.db.prepare('SELECT review_status FROM claims WHERE id=?').get(id).review_status, 'rejected');
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 145 AND 166").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 8); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 5);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-025'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('19段身份时间修正及2误归候选拒绝；源原文/几何留存，13图8后加5未核，25已读仍with_pending、全书false');

  const anchor = claim('macd-zero-retrace-before-level-divergence').evidence[0].id;
  const requests = [
    ['search', { query: '两次柱高不再突破' }, ['search', '两次柱高不再突破']],
    ['concept', { id: '机动资金', limit: 20 }, ['concept', '机动资金', '--limit', '20']],
    ['neighbors', { id: '乖离极限', depth: 1, limit: 100 }, ['neighbors', '乖离极限', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 151 }, ['page', '--document-id', 'volume_1.pdf', '--page', '151']],
    ['search', { query: '怎么又变成要两次回试呢', scope: 'source', limit: 8 }, ['search', '怎么又变成要两次回试呢', '--scope', 'source', '--limit', '8']],
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
    limits: ['这是同模型来源边界检查和模块一致性，不是独立语义审查或Windows实际离线/PDF交互。',
      '未证实MACD或买卖点可保证盈利、历史预测已兑现、括注署名或全书价序解释已统一。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l025-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
