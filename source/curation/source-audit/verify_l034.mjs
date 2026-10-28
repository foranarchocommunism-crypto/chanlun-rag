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
const claim = slug => { const c = graph.getClaim('upper-l034-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l034-c-stage-%' AND review_status='reviewed'").get().n, 16);
  assert.match(claim('four-zheng-means-current-not-claimed-correct').text, /正.*不是名言上自称正确.*当下/);
  assert.notEqual(claim('all-secrets-in-current-path-author-view').ambiguity_status, 'none');
  assert.notEqual(claim('percentage-loss-not-proven-equal-ruin-probability').ambiguity_status, 'none');
  assert.match(claim('percentage-loss-not-proven-equal-ruin-probability').review_note, /不同断言.*没有模型或样本/);
  checks.push('16新增命题；四正为本课当下释义，走势一切秘密和同归零概率保留作者主张及未核边界，不当实证定理');

  assert.match(claim('current-level-by-capital-and-tolerance-not-second').text, /并非每秒变化.*资金及承受能力.*操作级别/);
  assert.deepEqual(claim('exit-when-chosen-level-actual-path-opposes-operation').conditions, ['已有操作与事先选择级别的实际当下走势相反']);
  assert.match(claim('beast-reflex-after-danger-no-emotional-shadow').review_note, /不保证.*预知.*不能推出禁止/);
  assert.match(claim('rotation-no-chase-but-five-main-rise-not-all-small-exits').text, /5分仍主升.*每个1分以下背驰/);
  assert.match(claim('rotation-no-chase-but-five-main-rise-not-all-small-exits').review_note, /非所有小背驰都没用/);
  checks.push('退出条件是选定级别实际反向而非每秒噪音，野兽反应不保证预知风险；5分主升的小信号范围不抹33中枢回拉下次1可重要');

  assert.match(claim('mar7-2915-stable-third-buy-or-two-range-shapes').text, /有效站稳2915并最终形成三买/);
  assert.notEqual(claim('mar7-2915-stable-third-buy-or-two-range-shapes').ambiguity_status, 'none');
  assert.match(claim('mar8-five-retest-not-back-2858-thirty-third-buy').text, /5分回试不回2858原30分中枢.*三买.*2915.*须确认/);
  assert.match(claim('mar8-can-return-five-and-expand-new-thirty').text, /可能.*2915不能被有效跌破/);
  assert.match(claim('mar8-can-return-five-and-expand-new-thirty').review_note, /原30分.*新30分不是同一对象/);
  assert.match(graph.getClaim('upper-l032-c-stage-2915-is-gg-not-center-top-2894-correction').text, /2915/);
  checks.push('3/7联合确认及两分支、3/8已判三买与压力突破待确认分对象；原30分2858和未来新30分分开，2915不偷换ZG');

  const short = claim('front-is-back-not-short-reply-referent-unclear');
  assert.notEqual(short.ambiguity_status, 'none');
  assert.match(short.review_note, /不能唯一配对.*不能据此建立a\+A\+b为中枢/);
  assert.equal(short.evidence[0].passage_id, 'volume_1-a53e99c37ca5-p0258-b006');
  assert.match(source('0258-b005').text, /a[+＋]A[+＋]b.*b[+＋]B[+＋]c/);
  assert.equal(source('0258-b005').role, 'reader');
  assert.match(claim('third-buy-confirm-look-inside-sublevel').text, /看次级内部走势/);
  assert.match(claim('third-buy-confirm-look-inside-sublevel').review_note, /没有认可读者2871\/2888/);
  checks.push('复合问句和前后短答留歧义，不造a+A+b中枢裸规则；次级内部确认不扩成读者价点、半仓或固定K数均获作者认可');

  assert.match(claim('a-plus-b-plus-b-area-sum-not-maximum-bar').text, /a\+B\+b.*面积而非单根最长柱/);
  assert.match(claim('a-plus-b-plus-b-area-sum-not-maximum-bar').review_note, /不静改a\+A\+b.*不废33/);
  assert.match(claim('five-center-formed-prior-close-later-pull-and-gap-oscillate').text, /前一天尾盘已形成.*围绕中枢震荡/);
  assert.match(claim('five-center-formed-prior-close-later-pull-and-gap-oscillate').review_note, /不将读者.*完整推断当作者认可/);
  checks.push('原a+B+b记号和具体例面积非峰高不改写全局黄白线/多级优先；作者说前晚已成5分中枢，不背书读者两中枢完整拼法');

  for (const p of ['0257-b002', '0257-b003', '0258-b000', '0258-b001', '0258-b002']) assert.equal(source(p).published_at, '2007-03-08 15:30:24');
  assert.match(source('0257-b001').published_at, /^2007-03-07/);
  for (const p of ['0258-b007', '0258-b008', '0259-b004', '0259-b005']) assert.equal(source(p).role, 'reader');
  const links = {
    'mar7-index-levels-observe-not-commentator-following': ['0256-b001', ['0256-fig1', '0256-fig2', '0257-fig1']],
    'mar7-2915-stable-third-buy-or-two-range-shapes': ['0257-b001', ['0257-fig1']],
    'mar8-five-retest-not-back-2858-thirty-third-buy': ['0257-b003', ['0257-fig2', '0258-fig1']],
    'mar8-can-return-five-and-expand-new-thirty': ['0258-b000', ['0257-fig2', '0258-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f));
    assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 256 AND 258").all();
  assert.equal(figs.length, 5); assert.ok(figs.every(f => f.origin_status === 'later_annotation'));
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-034'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('5跨日来源日期修正而3/7段不改；4命题8配图关联逐项确认，5本课图全后加，254前课图不重复计入；全书未完成');

  const anchor = short.evidence[0].id;
  const requests = [
    ['search', { query: '正闻、正见、正学、正行' }, ['search', '正闻、正见、正学、正行']],
    ['concept', { id: '正闻正见正学正行', limit: 20 }, ['concept', '正闻正见正学正行', '--limit', '20']],
    ['neighbors', { id: '正闻正见正学正行', depth: 1, limit: 100 }, ['neighbors', '正闻正见正学正行', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 259 }, ['page', '--document-id', 'volume_1.pdf', '--page', '259']],
    ['search', { query: 'a+A+b', scope: 'source', limit: 8 }, ['search', 'a+A+b', '--scope', 'source', '--limit', '8']],
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
    intended_figure_links_checked: { claims: 4, associations: 8, unique_figures: 5 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未验证作者信息完备或同归零概率主张、历史实盘收益及后图原博客身份。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l034-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
