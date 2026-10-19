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
const claim = slug => { const c = graph.getClaim('upper-l037-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l037-c-stage-%' AND review_status='reviewed'").get().n, 39);
  assert.match(claim('trend-divergence-requires-trend-and-same-level-a-b').text, /整体为趋势.*A、B为同级别中枢/);
  assert.match(claim('a-larger-than-b-whole-oscillates-around-a-at-most-consolidation').text, /A级别大于B.*最多按盘整背驰/);
  assert.match(claim('local-b-perspective-not-forget-whole-trend').review_note, /局部B.*整体趋势并存/);
  assert.match(claim('c-direct-sublevel-contains-b-third-point').text, /c为次级别.*第三类买卖点/);
  assert.match(claim('b-can-smaller-gaps-strongest-and-not-higher-than-c').text, /b.*不能大于c/);
  assert.match(claim('c-must-new-trend-high-or-low').text, /必须创该走势新高.*必须创新低/);
  assert.match(claim('c-no-new-extreme-even-third-point-use-consolidation').text, /即使含B的第三类买卖点.*盘整背驰/);
  checks.push('39新增；整体趋势/同级A-B、c次级含三买卖点与新极值联合前提，局部B观察不取消整体；b可更小但不能大c，无新极值仍用盘背方法');

  assert.notEqual(claim('c-internal-two-sublevel-centers-original-relative-level').ambiguity_status, 'none');
  assert.match(claim('c-internal-two-sublevel-centers-original-relative-level').review_note, /未擅补唯一层级或改字/);
  assert.match(claim('standard-c-internal-trend-recursive-interval-nesting').review_note, /并非所有c都强制标准小趋势/);
  assert.notEqual(claim('c-gaps-while-b-sublevel-divergence-less-likely-weakest').ambiguity_status, 'none');
  assert.match(claim('comparable-force-can-use-consolidation-divergence-method').review_note, /可用方法不等已判盘背/);
  assert.match(claim('trend-divergence-ends-trend-consolidation-may-same-type').text, /盘整背驰不一定结束.*同一类型/);
  assert.match(claim('trend-divergence-ends-trend-consolidation-may-same-type').review_note, /结束趋势不等必直接形成反向趋势/);
  checks.push('c内两个次级别中枢保留原词及相对层级歧义，内部成趋势是标准情形非强制；缺口频率未量化，盘背可仍同类型，趋势结束不必直接反向');

  assert.match(claim('all-buy-sell-ultimately-first-points-different-levels').text, /都是第一类买卖点.*级别不同/);
  assert.match(claim('all-buy-sell-ultimately-first-points-different-levels').review_note, /未.*完整证明\/唯一层级算法/);
  assert.match(claim('no-absolute-prediction-consolidation-trend-respond-current').text, /无绝对规则.*较大盘整或趋势两支/);
  assert.match(claim('consolidation-extension-ends-third-point-when-probabilistic').review_note, /其后仍可成更大中枢/);
  assert.notEqual(claim('over-ninety-prediction-accuracy-auxiliary-claim-not-method').ambiguity_status, 'none');
  assert.match(claim('over-ninety-prediction-accuracy-auxiliary-claim-not-method').review_note, /未给手段、预测事件、样本、分母/);
  checks.push('所有点归一类是级别归结非本级改名或完整算法；三买后两支按当下应对、盘整延伸退出不保证无大中枢；90%以上无协议数据不当项目成绩');

  assert.equal(source('0279-b011').role, 'reader');
  assert.match(claim('center-overlap-not-occasional-wick-movement').review_note, /未明确回答.*须连续还是只同中枢/);
  assert.match(claim('center-overlap-not-occasional-wick-movement').review_note, /不据此普遍删除上下影线/);
  assert.equal(source('0278-b010').role, 'reader');
  assert.match(claim('reader-forex-question-author-futures-second-point-caution').review_note, /问外汇而答期货.*未确认读者银行/);
  assert.match(claim('index-futures-direction-unchanged-extension-stronger-author-view').review_note, /推出前的作者预判/);
  checks.push('中枢重叠非外围偶然价，未答三K连续不造作者规则或删所有影线；外汇问/期货答分对象，读者杠杆银行及现行制度不认证');

  const forecast = claim('mar19-twenty-years-thirty-thousand-points-conditional-forecast');
  assert.equal(forecast.conditions.length, 1); assert.notEqual(forecast.ambiguity_status, 'none');
  assert.match(forecast.review_note, /上升3万点不静改目标指数3万/);
  assert.match(claim('mar19-phase-one-reform-weights-marketcap-gdp-threshold').review_note, /不是本项目认定的无泡沫阈值/);
  assert.notEqual(claim('600195-three-to-eleven-and-fivefold-self-report-not-reconciled').ambiguity_status, 'none');
  assert.notEqual(claim('twofold-no-limit-up-implies-five-ten-author-strong-claim').ambiguity_status, 'none');
  assert.match(claim('medium-holding-partial-swings-not-limit-up-quality').review_note, /不取消按本级卖点退出/);
  checks.push('20年/上升3万点和三阶段是历史假设预测，市值/GDP非认证泡沫门槛；600195价区间/5倍未合，2倍必5/10倍未核，中线持股不取消本级退出');

  for (const p of ['0276-b005', '0276-b006', '0277-b000', '0277-b001', '0277-b002', '0277-b003']) assert.equal(source(p).published_at, '2007-03-20 15:24:15');
  assert.equal(source('0276-b004').published_at, '2007-03-19 15:18:14');
  assert.match(source('0276-b004').text, /2007-03-2015:24:15$/);
  const links = {
    'mar19-one-attack-not-stable-three-thousand': ['0276-b001', ['0276-fig1']],
    'mar20-two-day-three-thousand-lower-volume-then-up-view': ['0276-b005', ['0276-fig1']],
    '600195-three-to-eleven-and-fivefold-self-report-not-reconciled': ['0277-b001', ['0277-fig1']],
    'twofold-no-limit-up-implies-five-ten-author-strong-claim': ['0277-b001', ['0277-fig1']],
    'oscillating-climb-amplitude-potential-and-large-capacity': ['0277-b002', ['0277-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f));
    assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 276 AND 277").all();
  assert.equal(figs.length, 2); assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 1);
  assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 1);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-037'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('6段跨日改3/20、3/19段尾时间头原字符留存；5命题5配图逐项确认，2图1后加1原发未核；全书未完成');

  const anchor = claim('c-internal-two-sublevel-centers-original-relative-level').evidence[0].id;
  const requests = [
    ['search', { query: '整体为趋势，A、B为同级别中枢' }, ['search', '整体为趋势，A、B为同级别中枢']],
    ['concept', { id: '全流通', limit: 20 }, ['concept', '全流通', '--limit', '20']],
    ['neighbors', { id: '全球成长性', depth: 1, limit: 100 }, ['neighbors', '全球成长性', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 279 }, ['page', '--document-id', 'volume_1.pdf', '--page', '279']],
    ['search', { query: '这3根是连续的', scope: 'source', limit: 8 }, ['search', '这3根是连续的', '--scope', 'source', '--limit', '8']],
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
    intended_figure_links_checked: { claims: 5, associations: 5, unique_figures: 2 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未解决c内部相对次级词或三K未答问题，未验证宏观/收益/90%预测或期货引入因果。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l037-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
