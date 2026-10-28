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
const claim = slug => { const c = graph.getClaim('upper-l033-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l033-c-stage-%' AND review_status='reviewed'").get().n, 50);
  assert.match(claim('extension-six-added-plus-three-initial-nine').text, /新增延伸一般不超过五段.*新增六段.*本身三段.*共九段/);
  assert.equal(claim('extension-six-added-plus-three-initial-nine').conditions.length, 2);
  assert.match(claim('extension-six-added-plus-three-initial-nine').review_note, /不是九根K.*连续\/重叠.*波动/);
  assert.match(graph.getClaim('upper-l032-c-stage-nine-sublevel-extension-author-limit-with-wave-premise').text, /不能超过9个次级/);
  assert.match(claim('consolidation-plus-consolidation-can-increase-level').text, /更大级别盘整/);
  checks.push('50新增；初始三与新增六共九，新增延伸至五为止的口径与32原九次级句分别保留，数量不代替完成/连续/重叠/波动，盘整相加可变级别');

  assert.match(claim('strict-level-from-trades-not-fixed-time-periods').text, /每笔成交.*不依赖固定5分、30分/);
  assert.match(claim('strict-level-from-trades-not-fixed-time-periods').review_note, /每笔成交非后期几何笔/);
  assert.match(claim('chart-seven-or-fifteen-sixty-arrangements-possible').text, /7分.*15分与60分替代30分/);
  assert.match(claim('one-minute-process-shown-on-fifteen-not-level').text, /1分走势.*15分图展示.*作者|1分走势.*15分图展示.*走势计时/);
  assert.match(claim('one-minute-process-shown-on-fifteen-not-level').review_note, /4小时.*非自然日历.*13:37.*13:38/);
  assert.match(claim('valid-multiple-interpretations-not-all-to-eliminate').text, /多种符合理论内在逻辑/);
  checks.push('每笔成交递归与图周期模本分开，7分/15加60可选不是结构级别随意改名；1分过程用15分图，4小时非自然日历差，13:37/38原文不同不静合，合理多义不等任意划分');

  assert.match(claim('macd-same-side-divergence-versus-opposite-cross-zero').text, /普通背驰.*同一侧.*不同侧.*不要求原样回拉.*至少穿越一次0轴/);
  assert.match(claim('larger-b-can-reverse-and-same-side-excursions').text, /先一次向上、再一次向上/);
  assert.match(claim('larger-b-can-reverse-and-same-side-excursions').review_note, /不撤销构中枢三段的交替方向/);
  assert.match(claim('opposite-departure-strength-and-third-buy-retest').review_note, /后例又比较c与b.*不擅合/);
  assert.match(claim('existing-centers-and-current-trades-two-forces').text, /上方者给向上作用、下方者给向下作用/);
  assert.notEqual(claim('existing-centers-and-current-trades-two-forces').ambiguity_status, 'none');
  checks.push('中枢回拉为另一释义而非已证物理方程，同向背驰同侧回轴与反向比较异侧穿轴分对象；两次同向离开不废三段构成方向，参照a+A+b或b不擅统一');

  assert.match(claim('mar5-weekly-only-if-no-up-break-daily-alternative').text, /可能成周线.*不向上突破.*仍可能只是第一段日线/);
  assert.equal(claim('weekly-then-1500-up-is-conditional-forecast').conditions.length, 2);
  assert.match(claim('daily-jan4-feb6-three-thirty-not-nine-thirty').text, /1月4日至2月6日.*5分、非30分/);
  assert.match(claim('weekly-first-leg-until-april-or-up-no-weekly').text, /只算第一段.*4月以后.*直接上破.*不构成周线/);
  assert.match(claim('expansion-word-one-center-not-two-same-centers').text, /扩张针对一个中枢/);
  assert.match(claim('new-center-at-least-same-nonoverlap-old-enters-system').text, /至少同级且不重叠.*旧中枢并非无作用/);
  checks.push('周线未成两支与第一段日线范围保留，1500仅若形成且结束后的历史预测；扩张一个对象与20扩展两同级原词分开，旧中枢归大系统并非失效消失');

  assert.match(claim('third-buy-center-edge-versus-swing-high-strongest').text, /不跌回中枢里面.*最高点.*更强/);
  assert.match(claim('third-buy-center-edge-versus-swing-high-strongest').review_note, /不擅补触边相等/);
  assert.match(claim('sudden-index-fall-destroys-forming-third-buy').review_note, /形成中的.*不等已成立后/);
  assert.match(claim('end-by-divergence-not-necessarily-direct-sublevel').text, /至少结束该级别.*不一定.*紧邻次级/);
  assert.match(claim('macd-just-crossed-zero-not-own-level-divergence').text, /刚上0轴.*本级无背驰/);
  assert.match(claim('subminute-pull-important-under-five-thirty-center').conditions.join(''), /5分或30分.*1分走势/);
  assert.match(claim('bull-third-buy-daily-then-thirty-watch-pool').review_note, /观察池不是同时持仓数/);
  assert.notEqual(claim('center-alternation-reference-not-absolute').ambiguity_status, 'none');
  checks.push('三买定义不入中枢与不回GG更强分开，形成中被破坏非已成任意撤销；至少本级非只限直接次级，小信号回拉重要须5/30中枢且1分离开，观察池非持仓，交替只是未测参考');

  assert.equal(source('0247-b001').published_at, '2007-03-02 15:21:15');
  for (const s of ['0247-b002', '0247-b003', '0247-b004']) assert.equal(source(s).published_at, '2007-03-05 11:56:42');
  for (const s of ['0247-b005', '0247-b006', '0248-b000', '0248-b001', '0248-b002']) assert.equal(source(s).published_at, '2007-03-05 21:14:20');
  for (const s of ['0248-b003', '0249-b000']) assert.equal(source(s).published_at, '2007-03-06 15:22:36');
  for (const s of ['0250-b013', '0251-b008', '0253-b007']) assert.equal(source(s).role, 'reader');
  const links = {
    'one-minute-process-shown-on-fifteen-not-level': ['0245-b002', ['0245-fig1']],
    'c-return-b-origin-2915-or-small-top-before': ['0246-b000', ['0245-fig1']],
    'weak-c-reentry-b-2888-2859-sell-case': ['0246-b000', ['0245-fig1']],
    'mar5-1017-subminute-top-range-operation': ['0247-b002', ['0247-fig1']],
    'mar5-evening-pressure-line-2888-2858': ['0247-b006', ['0247-fig1']],
    'mar6-three-waves-broken-line-and-next-day-conditions': ['0248-b003', ['0248-fig1', '0249-fig1']],
    'weekly-then-1500-up-is-conditional-forecast': ['0251-b002', ['0253-fig1']],
    'macd-just-crossed-zero-not-own-level-divergence': ['0253-b000', ['0252-fig1']],
    'daily-jan4-feb6-three-thirty-not-nine-thirty': ['0253-b003', ['0253-fig1']],
    'weekly-first-leg-until-april-or-up-no-weekly': ['0253-b004', ['0253-fig1']],
    'macd-lines-generally-area-complex-multilevel-first': ['0254-b000', ['0254-fig1']],
    'subminute-pull-important-under-five-thirty-center': ['0254-b000', ['0254-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f)); assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 243 AND 254").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 6); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 1);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-033'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('10解盘日期按3/5午/夜和3/6修，3/2原答及读者身份不改；12命题13图关联逐项核，7图6后加1未核，33有记录全书未完成');
  const anchor = claim('one-minute-process-shown-on-fifteen-not-level').evidence.find(e => e.passage_id.endsWith('p0246-b000')).id;
  const requests = [
    ['search', { query: '新增六段，加上形成中枢本身三段' }, ['search', '新增六段，加上形成中枢本身三段']],
    ['concept', { id: '中枢回拉作用', limit: 20 }, ['concept', '中枢回拉作用', '--limit', '20']],
    ['neighbors', { id: '走势多义性', depth: 1, limit: 100 }, ['neighbors', '走势多义性', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 253 }, ['page', '--document-id', 'volume_1.pdf', '--page', '253']],
    ['search', { query: '两个同级中枢扩张后', scope: 'source', limit: 8 }, ['search', '两个同级中枢扩张后', '--scope', 'source', '--limit', '8']],
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
    limits: ['同模型边界检查与模块一致性，不是独立语义审查、历史行情/测度论证明核验或Windows实际离线/PDF交互。',
      '未验证中枢回拉作用的物理/数值模型、历史实盘/收益、所有周线构造及完整力度公式。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l033-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
