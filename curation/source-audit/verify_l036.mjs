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
const claim = slug => { const c = graph.getClaim('upper-l036-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l036-c-stage-%' AND review_status='reviewed'").get().n, 35);
  assert.match(claim('associativity-mixed-levels-and-multiple-not-vague').text, /级别可以不同.*不能等同概念含糊/);
  assert.match(claim('a-n-m-level-decomposition-and-operation-choice').review_note, /下标在抽取中串到相邻段.*不修写/);
  assert.equal(claim('a-n-m-level-decomposition-and-operation-choice').evidence.length, 3);
  assert.match(claim('completion-depends-on-level-two-five-not-thirty-complete').text, /两段5分类型A\+B在30分.*尚未完成/);
  assert.match(claim('mixed-five-thirty-redivide-regroup-last-unfinished').text, /末项F`在30分意义下未完成/);
  checks.push('35新增；异级结合不交换、多义非含糊；下标公式按原页释义而原文映射不动，两5分已完非30分完成，重分末项未完成');

  assert.match(claim('mar8-1000-third-buy-below-old-swing-high-not-center-top').text, /2760—2858.*2871.*2888/);
  assert.notEqual(claim('regroup-mar8-retest-into-mar5-up-new-start-mar9-1030').ambiguity_status, 'none');
  assert.match(claim('regroup-mar8-retest-into-mar5-up-new-start-mar9-1030').review_note, /图标13:25\/10:05不同不能静改/);
  assert.match(claim('2892-above-2888-conditional-thirty-up-not-yet-proof').text, /若.*仍可能跌破2888/);
  assert.match(claim('simplify-unfinished-second-center-not-cancel-expansion-definition').text, /两个中枢都完全走出.*第二中枢未完/);
  assert.match(claim('chosen-combination-must-use-own-center-third-buy-boundary').text, /2905—2947.*2892—2911.*参照不同/);
  assert.match(claim('chosen-combination-must-use-own-center-third-buy-boundary').review_note, /不得用新组合同时偷用旧边界/);
  assert.match(graph.getClaim('upper-l035-c-stage-second-thirty-center-range-2892-2911').text, /2892到2911/);
  checks.push('旧中枢上沿2858非波动高2888；新旧组合及其三买边界联动，未完第二中枢非两已完中枢；图文13:25/13:30和10:05/10:30差异不静合，不回写35旧时点');

  assert.match(claim('daily-oscillation-can-below-thirty-even-gap').text, /不必全是直接次级.*跳空/);
  assert.match(claim('stay-around-daily-eventually-thirty-last-a-m-less-nine').text, /若仍围绕.*m<9/);
  assert.match(claim('stay-around-daily-eventually-thirty-last-a-m-less-nine').review_note, /不是9根K或9自然天/);
  assert.match(claim('five-leave-and-retest-may-thirty-third-not-daily').text, /按日线还不构成.*可能构成.*30分/);
  assert.match(claim('after-thirty-third-can-return-daily-via-thirty-type').text, /回到日线中枢/);
  assert.notEqual(claim('absolute-safety-relative-to-thirty-not-universal').ambiguity_status, 'none');
  assert.match(claim('daily-operator-attend-early-thirty-third-if-trend').review_note, /若\/往往\/适量/);
  checks.push('围绕中枢小级/缺口不混构成三段次级，m是段序数非K/日；早30分信号非日线三买仍可返回，安全为作者相对对象强词，若/往往/适量不改全仓规则');

  assert.match(claim('abc-compare-ac-consolidation-divergence-and-c-internal').text, /A、C比较盘整背驰.*C内部小级别背驰/);
  assert.match(claim('abc-compare-ac-consolidation-divergence-and-c-internal').review_note, /两层配合而非任选一项充分/);
  assert.notEqual(claim('ipo-open-gap-short-answer-original-wording-unclear').ambiguity_status, 'none');
  assert.match(claim('ipo-open-gap-short-answer-original-wording-unclear').text, /就把开盘到跳空缺口上涨/);
  assert.match(claim('second-third-line-conventional-performance-price-not-strict').text, /并无严格区分.*业绩和价位约定/);
  assert.match(claim('second-third-line-conventional-performance-price-not-strict').review_note, /非官方分类.*不等大盘\/小盘/);
  checks.push('作者答A/C盘整背驰与C内部小背驰配合，非任选单项；IPO不顺短句原字及歧义保留，二三线为业绩价位俗称非官方/股本/指数身份');

  for (const p of ['0269-b003', '0269-b007', '0269-b013', '0269-b015', '0269-b017', '0270-b003', '0272-b005']) assert.equal(source(p).role, 'reader');
  assert.match(claim('third-buy-sublevel-leave-retest-not-reenter-general-answer').review_note, /不能把第一次回抽与第一次离开混同/);
  assert.equal(claim('third-buy-sublevel-leave-retest-not-reenter-general-answer').evidence[0].passage_id, 'volume_1-a53e99c37ca5-p0273-b009');
  assert.notEqual(claim('late-fourth-fifth-center-third-buy-expands-nearly-all-claim').ambiguity_status, 'none');
  assert.match(claim('late-fourth-fifth-center-third-buy-expands-nearly-all-claim').review_note, /无样本或概率校准/);
  assert.notEqual(claim('small-new-sme-float-and-profit-author-history-claim').ambiguity_status, 'none');
  assert.match(claim('key-after-third-trend-versus-larger-center-not-yet-algorithm').text, /具体判断留待后课/);
  checks.push('改革引文和第一次离开/回抽辩论均读者，作者末答独立；晚4/5中枢几乎百分百及IPO利润安全无样本，三买后趋势/更大中枢算法本课未给');

  for (const p of ['0271-b001', '0271-b002', '0271-b003', '0271-b004', '0271-b005']) assert.equal(source(p).published_at, '2007-03-14');
  assert.equal(source('0271-b000').published_at, '2007-03-14 08:58:13');
  assert.equal(source('0271-b006').published_at, '2007-03-15 15:23:22');
  const links = {
    'mar8-1000-third-buy-below-old-swing-high-not-center-top': ['0266-b001', ['0266-fig1', '0267-fig1', '0267-fig2']],
    'regroup-mar8-retest-into-mar5-up-new-start-mar9-1030': ['0266-b001', ['0266-fig1', '0267-fig1', '0267-fig2']],
    '2892-above-2888-conditional-thirty-up-not-yet-proof': ['0266-b001', ['0267-fig1', '0267-fig2']],
    'chosen-combination-must-use-own-center-third-buy-boundary': ['0268-b000', ['0267-fig1', '0267-fig2']],
    'mar15-still-2905-2947-thirty-center-oscillation': ['0271-b006', ['0272-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f));
    assert.equal(e.figures.length, figures.length);
  }
  assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.figure_ids LIKE '%volume_1-a53e99c37ca5-p0270-fig1%'").get().n, 0);
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 266 AND 272").all();
  assert.equal(figs.length, 5); assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 4);
  assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 1);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-036'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('附录5段只知3/14日级时点，晨帖和3/15独立；5命题11配图关联逐项确认，5图4后加1原发未核，读者270图不挂作者命题；全书未完成');

  const anchor = claim('chosen-combination-must-use-own-center-third-buy-boundary').evidence[0].id;
  const requests = [
    ['search', { query: '采取哪种组合就按其图形意义' }, ['search', '采取哪种组合就按其图形意义']],
    ['concept', { id: '新股', limit: 20 }, ['concept', '新股', '--limit', '20']],
    ['neighbors', { id: '走势类型连接', depth: 1, limit: 100 }, ['neighbors', '走势类型连接', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 268 }, ['page', '--document-id', 'volume_1.pdf', '--page', '268']],
    ['search', { query: '第一次回抽', scope: 'source', limit: 12 }, ['search', '第一次回抽', '--scope', 'source', '--limit', '12']],
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
    intended_figure_links_checked: { claims: 5, associations: 11, unique_figures: 4, reader_context_figures_not_attached_to_author_claims: 1 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未给图文时分差唯一解释，未验证作者概率/IPO收益或补完所有扩展、最佳分解和日线三买判定算法。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l036-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
