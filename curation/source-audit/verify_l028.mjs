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
const claim = slug => { const c = graph.getClaim('upper-l028-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l028-c-stage-%' AND review_status='reviewed'").get().n, 49);
  assert.equal(claim('fund-pyramid-language-is-author-opinion').importance_level, 4);
  assert.notEqual(claim('fund-pyramid-language-is-author-opinion').ambiguity_status, 'none');
  assert.match(claim('fund-pyramid-language-is-author-opinion').review_note, /不是法律分类/);
  assert.match(claim('fund-redemption-and-capital-horizon-risk-view').text, /类比为借来的钱.*开放式基金.*赎回.*长期稳定/);
  assert.notEqual(claim('fund-monthly-adjustment-collapse-forecast').ambiguity_status, 'none');
  assert.match(claim('fund-nav-position-constraint-author-view').review_note, /未给具体数值或法规来源/);
  checks.push('49新增；基金/传销/借贷/净值约束和崩溃为作者历史观点，非法律事实或当前申赎规则，赎回与资金期限条件分别保留');

  assert.match(claim('exrights-long-no-short-temporary-author-choice').text, /超长线不用复权.*短线.*一定时间.*熟练者也可不用/);
  assert.match(graph.getClaim('upper-l015-c-stage-five-ten-ex-rights-daily-vs-week-month').text, /5\/10.*日线.*周\/月线.*可以复权/);
  assert.notEqual(claim('exrights-long-no-short-temporary-author-choice').ambiguity_status, 'none');
  assert.match(claim('macd-instead-of-private-average-force-not-prerequisite').text, /直接MACD即可.*不是先MACD再另编/);
  assert.notEqual(claim('macd-center-divergence-95-author-claim').ambiguity_status, 'none');
  assert.match(claim('kiss-crossing-broad-answer-only-auxiliary').review_note, /不将11课飞吻\/唇吻.*所有吻必穿越/);
  assert.match(claim('600495-reader-profit-not-real-buy-point').text, /碰巧.*并非真正.*不|买在买卖点之间而非真正三类买点/);
  assert.match(claim('600495-reader-profit-not-real-buy-point').review_note, /浮盈3%不等买点判断被认可/);
  checks.push('超长线/均线系统复权意见分范围，MACD替代不是共同必要；95%非本项目指标，宽泛吻交叉不改细分，读者3%浮盈不认证买点');

  assert.match(claim('shanghai-2980-five-minute-three-center-dates').text, /1301055—1301345、2011105—2021110、2051005—2051330/);
  assert.match(claim('jan30-1035-previous-type-center-not-current').text, /01301035属于前一走势类型/);
  assert.match(claim('center-label-first-three-extension-optional').text, /前三段.*延伸可省写/);
  assert.match(claim('completion-not-short-average-standing').text, /均线无关.*次级别.*完结.*29课/);
  assert.match(claim('below-one-minute-histogram-special-comparison').text, /最低图.*远离零轴.*绿转红再绿.*价创新低/);
  assert.match(claim('below-one-minute-histogram-special-comparison').review_note, /特例.*不能抹去普通本级MACD回轴前提/);
  assert.match(claim('triple-nesting-five-one-subminute-case').text, /5分背驰段内1分背驰段.*更低级.*第二波.*不是.*第一波/);
  assert.match(claim('third-five-center-departure-one-centers-two-needed').text, /02051410—02051436仅第一.*9:51—10:08为第二/);
  checks.push('三中枢原时间不按读者笔误说改；前类型/现类型与省写延伸分开，完结还需29课；最低1分内更低柱比较特例不抹普通回轴，三重定位需对应包含');

  assert.match(claim('connections-sublevel-or-lower-not-exact').text, /不一定.*次级别以下/);
  assert.match(claim('gap-infinitely-low-not-center-constituent').text, /无限低.*不能成为任何中枢中的一段/);
  assert.match(claim('type-level-by-contained-centers-not-connections').text, /已完成.*一个日线中枢.*盘整.*两个以上.*趋势.*连接段级别无关/);
  assert.match(claim('600151-one-divergence-can-generate-five-rise').text, /否定.*5分背驰.*1分背驰.*扩展/);
  assert.match(claim('divergence-at-least-own-type-larger-via-expansion').text, /至少.*5分走势类型.*经中枢扩展/);
  assert.match(claim('minimum-five-three-done-further-center-development').text, /5分三段走势.*最低要求.*延伸扩展/);
  assert.match(claim('minimum-five-three-done-further-center-development').review_note, /不静改成已形成上涨趋势/);
  assert.match(claim('post-divergence-not-necessarily-v-reversal').text, /先盘整再选方向.*不必V形/);
  checks.push('连接段/纯跳空/中枢/完成走势类型分层；1分可经扩展导致5分上涨，最低三段非必成趋势，后续靠中枢演化，非原背驰无限推动');

  assert.match(claim('thirty-first-sell-aligned-daily-leg').text, /至少30分.*恰在日线背驰段.*日线第一类卖点/);
  assert.match(claim('after-thirty-top-two-five-types-second-sell').text, /先5分向下完成.*5分向上反抽.*也可为盘整/);
  assert.match(claim('center-max-low-min-high-first-three-not-all-shrinking').text, /MAX低点、MIN高点.*未必很窄.*前三段.*延伸与扩展/);
  assert.match(claim('third-buy-smaller-center-than-broken-one').review_note, /不等第三买点自身级别必须小于原中枢/);
  assert.match(claim('small-divergence-large-impact-two-contexts').text, /大级别背驰段.*行情急促/);
  assert.match(claim('feb7-rewritten-five-rise-end-one-divergence').text, /待后两日/);
  assert.match(claim('feb8-five-center-expands-thirty-conditions').text, /中枢确认且.*背驰后站稳2720/);
  assert.notEqual(claim('double-rise-half-sale-negative-cost-self-report').ambiguity_status, 'none');
  checks.push('大级别对齐、二卖盘整类型、三买中枢指代和MAX低MIN高前提保留；2/7待定与2/8联合条件不改已确认，负成本/概率/涨幅未实证');

  assert.equal(source('0190-b001').published_at, '2007-02-06 15:12:35');
  for (const short of ['0191-b000', '0191-b001', '0191-b002', '0191-b003']) assert.equal(source(short).published_at, '2007-02-07 20:43:08');
  for (const short of ['0191-b004', '0191-b005', '0191-b006', '0191-b007', '0192-b000']) assert.equal(source(short).published_at, '2007-02-08 15:10:09');
  for (const short of ['0198-b004', '0198-b005', '0198-b006']) { assert.equal(source(short).role, 'reader'); assert.equal(source(short).speaker, '深潜'); assert.equal(source(short).published_at, '2007-02-24 19:43:19'); }
  assert.equal(source('0198-b003').role, 'author_reply'); assert.equal(source('0198-b008').role, 'reader');
  for (const id of ['candidate-693b784d46de28fc', 'candidate-76aa7ad83b38644d']) assert.equal(graph.db.prepare('SELECT review_status FROM claims WHERE id=?').get(id).review_status, 'rejected');
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 187 AND 203").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 6); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 4);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-028'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('9解盘日期和3深潜读者修正，嵌引作者标题/CCTV读者分开；2误归候选拒绝，10图6后加4未核，28有记录而全书未完成');

  const anchor = claim('shanghai-2980-five-minute-three-center-dates').evidence[0].id;
  const requests = [
    ['search', { query: '买在买卖点之间而非真正三类买点' }, ['search', '买在买卖点之间而非真正三类买点']],
    ['concept', { id: '复权', limit: 20 }, ['concept', '复权', '--limit', '20']],
    ['neighbors', { id: '基金赎回', depth: 1, limit: 100 }, ['neighbors', '基金赎回', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 198 }, ['page', '--document-id', 'volume_1.pdf', '--page', '198']],
    ['search', { query: '第二中枢大家都认为', scope: 'source', limit: 8 }, ['search', '第二中枢大家都认为', '--scope', 'source', '--limit', '8']],
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
    limits: ['同模型边界检查与模块一致性，不是独立语义审查、账户/历史预测核验或Windows实际离线/PDF交互。',
      '未验证基金法律性质/崩溃预言、95%准确、反弹收益、无限低实际可交易或所有级别算法。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l028-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
