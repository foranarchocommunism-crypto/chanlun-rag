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
const claim = slug => { const c = graph.getClaim('upper-l035-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l035-c-stage-%' AND review_status='reviewed'").get().n, 42);
  assert.match(claim('strict-trade-base-three-same-price-transactions').text, /每笔交易.*连续三笔相同价位/);
  assert.match(claim('strict-trade-base-three-same-price-transactions').review_note, /成交笔数而非后期技术笔.*非任意三根K/);
  assert.match(claim('lowest-n-centers-successive-higher-or-lower-continues').text, /N>2.*逐一/);
  assert.match(claim('lowest-up-ends-only-next-center-not-higher').text, /等于或低于/);
  assert.equal(claim('three-consecutive-lowest-types-price-intersection-upward-recursion').evidence.length, 2);
  assert.match(claim('minute-levels-practical-not-strict-trade-recursion').text, /15或30分.*不大严格/);
  checks.push('42新增；严格每笔成交三同价非后期笔或三K，连续三类型共同区间递归；分钟15或30为便利模本，最低依次位置及终结不偷换价格一跳');

  assert.match(claim('single-five-type-cannot-contain-thirty-center').text, /单个5分钟.*都不能.*三个以上5分钟走势类型连接才可能/);
  assert.match(claim('mixed-lower-level-connection-a-b-b-example').text, /a、b为1分.*两1分和三5分/);
  assert.match(claim('mixed-lower-level-connection-a-b-b-example').review_note, /不把a\+B\+b整体裸称中枢/);
  assert.match(claim('decomposition-two-regroup-at-least-three-direct-sublevels').review_note, /不少于三.*不把初始任意分段都要求等次级别/);
  assert.match(claim('a-b1-b2-b3-b-associative-regrouping-example').text, /\(a\+B1\)\+B2\+\(B3\+b\)/);
  assert.match(claim('type-connection-associative-not-commutative').text, /符合结合律.*不符合交换律/);
  assert.match(claim('decomposition-one-same-level-three-type-connections').review_note, /不是.*必须恰好包含三种或恰三段/);
  assert.notEqual(claim('five-up-down-up-two-rounds-thirty-no-trades-example').ambiguity_status, 'none');
  checks.push('单类型延续与多类型连接分开，混合小级别可重组直接次级，结合不等交换；a+B+b整体类型非裸中枢，三种分类不等恰三段，四背驰限例境');

  assert.match(claim('historical-t-plus-one-blocks-full-subminute-except-tzero').text, /T\+1.*完全用1分以下.*除非T\+0/);
  assert.match(claim('tiny-level-amplitude-cost-error-no-long-run-meaning').text, /相对波幅不够小/);
  assert.match(claim('recognition-execution-lag-price-error-small-level').text, /时间差.*价位差/);
  assert.match(claim('chosen-level-own-buy-sell-enter-exit-no-own-down').review_note, /非其内部所有低级回调/);
  assert.match(claim('partial-lower-level-trades-under-chosen-level').text, /部分操作.*次次级/);
  assert.notEqual(claim('zero-cost-only-risk-escape-author-assertion').ambiguity_status, 'none');
  checks.push('历史T+1/除非T+0不当现行全市场规则或盈利充分条件；成本/误差相对波幅、整仓本级与低级部分操作分开，零净现金成本不证明无经济风险');

  const theorem = claim('large-buy-sell-is-sublevel-or-below-not-necessarily-direct');
  assert.match(theorem.text, /次级别以下某一级别.*未必是直接次级别.*1分b/);
  assert.match(theorem.review_note, /不是任意小点都必转大点/);
  assert.equal(theorem.evidence.length, 2);
  assert.match(claim('buy-sell-level-proof-endpoint-completion-outline').review_note, /未替作者补完/);
  assert.match(claim('all-level-alignment-only-most-standard-coarse-theorem').text, /最规范.*粗糙/);
  assert.match(claim('all-level-alignment-only-most-standard-coarse-theorem').review_note, /不能改成所有大买卖点必在每级同步/);
  checks.push('大点必属次级以下某小点非必直接次级，逆命题不成立；端点完成矛盾为作者例证纲要，最规范全级同步非普遍必要要求，粗糙定理保留');

  assert.match(claim('mar9-five-top-divergence-expands-new-thirty-from-mar7').text, /昨日三买后两可能之一.*3月7日13点多2911/);
  assert.match(claim('mar8-2871-third-buy-then-new-thirty-from-mar7-2911').text, /3月12日.*3月8日2871形成三买/);
  assert.match(claim('mar12-near-2911-not-above-not-third-buy-next-retest').text, /附近止住但未在其上.*还不算三买.*次日若/);
  assert.match(claim('third-buy-after-second-center-not-guaranteed-up-daily-possible').text, /不意味着一定继续上扬.*日线中枢/);
  assert.match(claim('second-thirty-center-range-2892-2911').text, /2892到2911/);
  assert.match(claim('second-thirty-center-range-2892-2911').review_note, /不把读者ZG.*普遍定义/);
  assert.match(claim('ex-right-gap-treat-as-lowest-down-new-center-usual').review_note, /没有给前复权\/后复权数据算法/);
  assert.match(claim('gap-below-old-center-can-third-sell').review_note, /非所有除权一跳即完整三卖/);
  assert.match(claim('upward-running-second-high-third-slight-break-first-high').text, /第二段特别高.*第三段下跌稍微跌破第一段高点/);
  assert.notEqual(claim('self-review-not-market-blame-author-normative').ambiguity_status, 'none');
  checks.push('三买后可新30或日线，2871事后明确与34当时未认可读者价点分时保留；2911附近非在上、2892至2911为具体范围；除权缺口和向上奔走有范围，自责为训练非因果定律');

  for (const p of ['0261-b004-s01', '0262-b000', '0262-b001']) assert.equal(source(p).published_at, '2007-03-09 11:54:01');
  for (const p of ['0262-b002', '0262-b003', '0262-b004']) assert.equal(source(p).published_at, '2007-03-12 15:20:28');
  assert.equal(source('0261-b004').published_at, '2007-03-09 11:51:34');
  for (const p of ['0263-b000', '0263-b009', '0265-b001', '0265-b002']) assert.equal(source(p).role, 'reader');
  const links = {
    'mar9-five-top-divergence-expands-new-thirty-from-mar7': ['0262-b001', ['0262-fig1']],
    'mar12-thirty-extension-third-buy-and-two-next-paths': ['0262-b003', ['0263-fig1']],
    'mar7-thirty-center-running-type-less-common': ['0263-b001', ['0263-fig1']],
    'two-thirty-centers-below-2858-and-2911-up-or-a-prime-b': ['0263-b004', ['0263-fig1']],
    'mar8-2871-third-buy-then-new-thirty-from-mar7-2911': ['0264-b006', ['0264-fig1']],
    'mar12-near-2911-not-above-not-third-buy-next-retest': ['0264-b007', ['0264-fig1']],
    'third-buy-after-second-center-not-guaranteed-up-daily-possible': ['0264-b007', ['0264-fig1']],
    'second-thirty-center-range-2892-2911': ['0265-b003', ['0263-fig1', '0264-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f));
    assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 262 AND 264").all();
  assert.equal(figs.length, 3); assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 2);
  assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 1);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-035'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('6解盘来源日期分3/9和3/12而正文/读者不改；8命题9配图关联逐项确认，3图2后加1原发未核；全书未完成');

  const anchor = theorem.evidence[0].id;
  const requests = [
    ['search', { query: '连续三笔相同价位' }, ['search', '连续三笔相同价位']],
    ['concept', { id: '缠中说禅买卖点级别定理', limit: 20 }, ['concept', '缠中说禅买卖点级别定理', '--limit', '20']],
    ['neighbors', { id: '走势类型连接', depth: 1, limit: 100 }, ['neighbors', '走势类型连接', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 265 }, ['page', '--document-id', 'volume_1.pdf', '--page', '265']],
    ['search', { query: '第二个30分钟中枢', scope: 'source', limit: 8 }, ['search', '第二个30分钟中枢', '--scope', 'source', '--limit', '8']],
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
    intended_figure_links_checked: { claims: 8, associations: 9, unique_figures: 3 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未补完作者定理的形式证明，未验证历史实盘收益/当前交易制度或后图原博客身份。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l035-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
