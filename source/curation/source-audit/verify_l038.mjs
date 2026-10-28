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
const claim = slug => { const c = graph.getClaim('upper-l038-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l038-c-stage-%' AND review_status='reviewed'").get().n, 40);
  assert.match(claim('same-level-decomposition-fixed-level-definition').text, /一个固定级别/);
  assert.notEqual(claim('good-rule-unique-and-same-level-uniqueness-author-claim').ambiguity_status, 'none');
  assert.match(claim('same-level-no-extension-three-overlap-six-two-consolidations').text, /三段5分.*共同价格区间.*六段.*两个30分盘整/);
  assert.match(claim('consolidation-plus-consolidation-allowed-only-mode-scope').text, /非同级别分解方式/);
  assert.match(claim('hybrid-rule-own-level-all-below-and-above-ignored').text, /本级以下所有级别.*以上级别在该分解视角不考虑/);
  assert.match(claim('hybrid-rule-own-level-all-below-and-above-ignored').review_note, /本级\/全部以下\/以上/);
  checks.push('40新增；固定规则内唯一为作者未全证主张，本级不延伸可盘整+盘整、以下允许延伸禁该连接、以上只视角不考虑，六次级类型非六K');

  assert.match(claim('procedure-start-down-divergence-first-up-exit').text, /从下跌背驰开始.*第一向上/);
  assert.match(claim('procedure-second-not-break-first-low-rebuy').text, /不跌破第一向上段低点/);
  assert.match(claim('procedure-second-break-low-compare-prior-down-else-wait').text, /第一段前的向下段.*否则继续观望.*新的下跌背驰/);
  assert.match(claim('procedure-third-below-first-high-sell').review_note, /未在此单列等高处理/);
  assert.match(claim('procedure-third-above-first-high-diverge-sell-else-hold').text, /盘整背驰则卖出.*不盘背则继续持有/);
  assert.match(claim('procedure-repeat-up-until-no-new-high-or-divergence').text, /不创新高或盘整背驰/);
  assert.match(claim('procedure-down-side-sell-before-buy-reverse').review_note, /未授权裸卖空/);
  checks.push('30分程序全支：下背起、首上出、二下不破/破低比此前下段或等新下背、三上高低与盘背、循环和反向；等高/成交细节不捏造，先卖后买非裸空授权');

  assert.match(claim('return-first-not-third-later-not-return-can-be-third').text, /回到中枢者不是三买.*第二次未回才是/);
  assert.match(claim('first-effective-retest-only-later-no-return-not-third').text, /第一次有效回抽.*之后再上去.*不再算三买卖点/);
  assert.match(claim('two-subsub-retests-complete-one-sublevel-retest').text, /至少三段次次级.*完成该次级回抽/);
  assert.match(claim('third-point-and-center-extension-end-same-object').review_note, /不覆盖本课同级别模式/);
  assert.equal(source('0285-b003').role, 'reader');
  checks.push('回中枢仍震荡不算有效回抽，首有效不回三买后再不回非同中心重复三买；内部两次次次级完成一次次级，延伸终结语境不套本级不定义延伸模式');

  assert.match(claim('abc-macd-five-chart-ac-compare-c-internal-precision').text, /5分图通常较清楚.*A和C.*C内部/);
  assert.match(claim('abc-macd-five-chart-ac-compare-c-internal-precision').review_note, /没有.*单独回答.*刚上0轴/);
  assert.match(claim('consolidation-c-need-not-highest-no-new-high-weak-macd-aux').text, /ABC盘整的C不必高过A/);
  assert.match(claim('consolidation-c-need-not-highest-no-new-high-weak-macd-aux').review_note, /非37整体趋势末c/);
  assert.match(graph.getClaim('upper-l037-c-stage-c-must-new-trend-high-or-low').text, /必须创该走势新高/);
  assert.equal(source('0285-b006').role, 'reader');
  assert.match(claim('daily-divergence-possible-two-centers-or-one-more').review_note, /可能非已确认.*未逐字确认读者双0轴/);
  checks.push('盘整C不必新高与37趋势末c新极值分对象；MACD5分较清楚仍A/C及C内两层、刚上轴问未单答，读者旧引文非新答；日背可能非已确认');

  assert.notEqual(claim('active-swings-profit-time-proportional-author-claim').ambiguity_status, 'none');
  assert.notEqual(claim('mar21-hold-partial-swings-more-cash-no-fewer-shares-self-report').ambiguity_status, 'none');
  assert.match(claim('nested-divergence-exit-staged-by-capital').text, /陆续退出.*小资金.*大资金/);
  assert.match(claim('miss-first-sell-use-second-not-wait-third').text, /第一卖点未走应在第二卖点走/);
  assert.match(claim('mar22-small-consolidation-divergence-and-shanghai-shenzhen-after-1430').review_note, /两指数比较.*不静合MACD技术背驰/);
  assert.match(claim('stock-not-one-group-no-reader-orderflow-story-endorsement').review_note, /未认证读者.*庄家动机/);
  checks.push('利润线性/永远不败为未核作者主张；区间套退出按容量分批非统一跌幅，首二卖纪律依级别；沪深背离非MACD背驰，读者大单故事未背书');

  for (const p of ['0282-b006', '0283-b000', '0283-b001']) assert.equal(source(p).published_at, '2007-03-22 15:29:02');
  assert.equal(source('0282-b005').published_at, '2007-03-21 15:24:07');
  assert.match(source('0282-b005').text, /2007-03-2215:29:02$/);
  for (const key of ['text', 'role', 'speaker', 'published_at']) assert.equal(source('0283-b005')[key], source('0277-b007')[key]);
  assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id='volume_1-a53e99c37ca5-p0283-b005'").get().n, 0);
  const links = {};
  for (const slug of ['procedure-start-down-divergence-first-up-exit', 'procedure-second-not-break-first-low-rebuy', 'procedure-second-break-low-compare-prior-down-else-wait', 'procedure-third-below-first-high-sell', 'procedure-third-above-first-high-diverge-sell-else-hold', 'procedure-repeat-up-until-no-new-high-or-divergence', 'procedure-down-side-sell-before-buy-reverse']) links[slug] = ['0282-b000', ['0281-fig1']];
  Object.assign(links, {
    'mar22-three-closes-and-jan24-feb27-pressure-line': ['0282-b006', ['0283-fig1']],
    'daily-divergence-possible-two-centers-or-one-more': ['0284-b001', ['0284-fig1']],
    'mar22-small-consolidation-divergence-and-shanghai-shenzhen-after-1430': ['0285-b014', ['0286-fig1']],
  });
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f));
    assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 281 AND 286").all();
  assert.equal(figs.length, 4); assert.ok(figs.every(f => f.origin_status === 'later_annotation'));
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-038'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('3段改3/22且前段尾头原字符留存；3/20同文答复保留重复台账不重抽，10命题10配图逐项确认，4图全部后加；全书未完成');

  const anchor = claim('hybrid-rule-own-level-all-below-and-above-ignored').evidence[0].id;
  const requests = [
    ['search', { query: '第一次有效回抽不到中枢' }, ['search', '第一次有效回抽不到中枢']],
    ['concept', { id: '同级别分解', limit: 20 }, ['concept', '同级别分解', '--limit', '20']],
    ['neighbors', { id: '同级别分解', depth: 1, limit: 100 }, ['neighbors', '同级别分解', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 285 }, ['page', '--document-id', 'volume_1.pdf', '--page', '285']],
    ['search', { query: '黄白线刚上0轴', scope: 'source', limit: 8 }, ['search', '黄白线刚上0轴', '--scope', 'source', '--limit', '8']],
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
    intended_figure_links_checked: { claims: 10, associations: 10, unique_figures: 4 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未证明分解唯一或利润线性，未补全等高/成交算法，未回答原作者未答的0轴与全部边界。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l038-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
