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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'upper-l015-c-stage-%' OR id LIKE 'upper-l016-c-stage-%') AND review_status='reviewed'").get().n, 60);
  assert.match(claim(15, 'chart-rise-higher-high-and-low').text, /高点高于前高.*且.*低点高于前低/);
  assert.match(claim(15, 'chart-consolidation-expanding-or-contracting').text, /高点更高且低点更低，或高点更低且低点更高/);
  assert.match(claim(16, 'platform-exception-initial-definition-not-strict').text, /顺势平台.*不完全严格/);
  assert.notEqual(graph.query('concept', { id: '价值中枢' }).data.concept.id, graph.query('concept', { id: '宏观估值中枢' }).data.concept.id);
  assert.match(claim(16, 'level-as-filter-channel-small-frame-trend').text, /日线.*只算趋势一段.*5\/30分钟.*完整趋势/);
  checks.push('60新增；早期高低点且/或、顺势平台与作者不严格限定保留，价值中枢不合并宏观估值，日图一段与小图趋势不同');
  assert.match(claim(15, 'trend-force-between-kisses-area').text, /前吻结束至后吻开始.*面积.*同向/);
  assert.match(claim(15, 'trend-force-between-kisses-area').review_note, /不是MACD柱面积/);
  assert.match(claim(15, 'average-force-area-divided-by-time').text, /至当下.*面积除以时间.*将形成/);
  assert.match(claim(15, 'confirmed-area-lag-lower-chart-localization').text, /再次吻后.*距离.*降一级/);
  assert.notEqual(claim(15, 'average-force-area-divided-by-time').ambiguity_status, 'none');
  checks.push('两均线面积/平均面积除时间与MACD柱面积分开；等再次吻确认有滞后，平均力度将形成非已确认，未补积分或长度算法');
  assert.match(claim(15, 'patch-peak-three-day-turn-not-price-turn').text, /今日短于昨日且昨日长于前日/);
  assert.match(claim(15, 'histogram-divergence-peak-compare-with-lines').text, /该波峰值低于前波峰值.*DEA\/DIFF/);
  assert.match(claim(15, 'macd-patch-to-patch-with-current-shrinking-alert').text, /片与片.*关注.*其他条件/);
  assert.match(claim(15, '600900-thirty-already-day-not-zero-retest').text, /30分钟背离早已发生、日线没有.*黄白线.*线和柱/);
  checks.push('柱片内峰转与前波峰比较、线柱/回轴组合分别记录；关注不是完成背驰，30分已背不升级日线');
  assert.match(claim(15, 'buy-first-if-skilled-second-for-unfamiliar').text, /熟悉.*第一类买点更好.*不熟悉.*第二类/);
  assert.match(claim(15, 'first-entanglement-exclusion-only-trend-search').text, /只针对趋势.*盘整一次缠绕.*周\/月/);
  assert.equal(claim(15, 'first-entanglement-exclusion-only-trend-search').evidence.length, 3);
  assert.match(claim(15, '000932-box-entry-not-upgrade-to-day-hold').text, /日\/周买点.*须最初.*不是标准一买而是箱型/);
  assert.match(claim(16, 'same-chart-two-same-direction-trends-premise').text, /同一级别图.*两段同方向趋势/);
  checks.push('买一/买二按能力，首次非最后只限趋势并有周月盘整例外；000932箱型不事后升级，同级两段同向是背驰联合前提');
  assert.match(claim(15, 'macd-law-first-below-second-first-retest').text, /零轴下.*首次上零轴后回抽确认.*卖点反向/);
  assert.notEqual(claim(15, 'macd-law-first-below-second-first-retest').ambiguity_status, 'none');
  const warrant = claim(15, '038004-risk-warning-homework-not-recommendation');
  assert.match(warrant.text, /认沽风险极大.*要求不要买/);
  assert.ok(warrant.concept_ids.includes(graph.query('concept', { id: '认沽权证' }).data.concept.id));
  assert.ok(!warrant.concept_ids.includes(graph.query('concept', { id: '认购权证' }).data.concept.id));
  assert.match(claim(15, 'gap-types-not-all-fill').text, /已经上涨最后/);
  assert.doesNotMatch(claim(15, 'gap-types-not-all-fill').text, /以及上涨最后/);
  assert.notEqual(claim(15, '038004-author-lots-zero-cost-not-audit').ambiguity_status, 'none');
  checks.push('早期MACD定律保留条件，038004认沽非认购且教学禁买边界不删，成本0不作账户证明，缺口原词已经未静默改以及');
  assert.match(claim(16, 'first-buy-then-reduce-consolidation-general').text, /盘整先减仓.*保留部分/);
  assert.match(claim(16, 'down-up-strategy-refuses-consolidation').text, /无论后来怎样都退出/);
  assert.match(claim(16, 'entry-second-down-exit-new-consolidation').text, /只选下跌\+盘整\+下跌.*第二段下跌.*一买.*一旦盘整/);
  assert.match(claim(16, 'exclude-prior-up-down-not-no-profit').text, /不考虑不意味着不能盈利/);
  assert.match(claim(16, 'profit-and-half-risk-author-assertions').text, /作者断言.*一半/);
  assert.notEqual(claim(16, 'profit-and-half-risk-author-assertions').ambiguity_status, 'none');
  assert.match(claim(16, 'half-million-three-stocks-return-rhetoric').conditions[0], /50万/);
  checks.push('一般先减与特定拒绝盘整全退分开，第二跌一买入/再盘整退三步完整，排除不等不能盈利；半概率/必盈利/300%未实证');
  const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
  for (const short of ['0064-b004', '0064-b005']) { assert.equal(source(short).role, 'reader'); assert.equal(source(short).speaker, '舞者'); assert.equal(source(short).published_at, null); }
  assert.equal(source('0064-b006').role, 'author_reply'); assert.equal(source('0064-b006').published_at, null);
  assert.equal(source('0074-b007').role, 'reader'); assert.equal(source('0074-b007').published_at, null);
  const figures = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 58 AND 75").all();
  assert.equal(figures.filter(f => f.origin_status === 'later_annotation').length, 10);
  assert.equal(figures.filter(f => f.origin_status === 'unverified').length, 4);
  for (const lesson of ['015', '016']) assert.equal(graph.db.prepare('SELECT processing_status FROM units WHERE id=?').get(`lesson-${lesson}`).processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('64读者/无时间作者回复和74截断年份null保留；14图10后加4未核，两课仍with_pending，全书语义false');
  const anchor = claim(15, 'histogram-divergence-peak-compare-with-lines').evidence.find(e => e.pdf_page === 65).id;
  const requests = [
    ['search', { query: '同一级别图存在两段同方向趋势' }, ['search', '同一级别图存在两段同方向趋势']],
    ['concept', { id: '缠中说禅趋势平均力度', limit: 20 }, ['concept', '缠中说禅趋势平均力度', '--limit', '20']],
    ['neighbors', { id: '下跌+上涨买卖法', depth: 1, limit: 100 }, ['neighbors', '下跌+上涨买卖法', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 64 }, ['page', '--document-id', 'volume_1.pdf', '--page', '64']],
    ['search', { query: '顺势平台', scope: 'source', limit: 8 }, ['search', '顺势平台', '--scope', 'source', '--limit', '8']],
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
    limits: ['非Windows真实离线、打包和PDF交互验收。', '同模型边界检查不是独立审查、MACD/均线定律形式证明、半概率/300%收益回测或所有历史解释已统一。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l015-l016-verification.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
