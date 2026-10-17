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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'upper-l013-c-stage-%' OR id LIKE 'upper-l014-c-stage-%') AND review_status='reviewed'").get().n, 41);
  assert.match(claim(13, 'active-entrapment-two-meanings-and-protection').text, /两层意思.*大资金.*更重要.*防护.*盈亏无关/);
  assert.match(claim(13, 'passive-entrapment-blind-entry').text, /不知为何介入.*被动带套/);
  assert.match(claim(13, 'exit-when-structure-no-longer-tradable-not-pnl').text, /即使已大幅盈利.*退出/);
  assert.notEqual(graph.query('concept', { id: '主动带套' }).data.concept.id, graph.query('concept', { id: '主动买套' }).data.concept.id);
  checks.push('41新增；主动带套两义与被动盲目介入、按走势而非盈亏退出可查，主动带套不自动别名105主动买套');
  assert.match(claim(13, 'average-first-entry-another-bear-kiss-invalid').text, /又出现男上位缠绕.*并非最后/);
  assert.match(claim(13, 'average-second-entry-break-old-bear-low-exit').text, /该缠绕跌破前面男上位最低位.*反弹中出清/);
  assert.match(claim(14, 'maotai-aug7-not-break-prior-may26-low').text, /5月26日37元多.*未被破/);
  assert.equal(claim(13, 'half-position-warning-and-last-retest-not-guaranteed').ambiguity_status, 'half_reference_not_defined_and_retest_not_guaranteed');
  assert.doesNotMatch(claim(13, 'half-position-warning-and-last-retest-not-guaranteed').text, /50%/);
  checks.push('一买再男吻/二买破前男低两种失效分开，8/7不是破5/26前低；一半位置未补50%公式，反抽一般非保证');
  assert.match(claim(13, 'tcl-cost-topup-specific-not-universal-lump').conditions[0], /TCL/);
  assert.match(claim(13, 'tcl-swing-added-lot-not-original-holding').text, /原套仓暂不动.*补仓部分.*短线能力/);
  assert.notEqual(claim(13, 'program-strength-ninety-author-estimate').ambiguity_status, 'none');
  assert.match(claim(13, 'no-sell-signal-no-speculative-switch').text, /未出卖出信号.*持有/);
  checks.push('TCL一次补/原仓暂留是案例，短差只用补仓部分且有能力条件；90%为作者估计、无卖点换股不能凭事后更好');
  assert.match(claim(14, 'entanglement-includes-all-three-kisses').text, /包括飞吻、唇吻、湿吻/);
  const law = claim(14, 'buy-point-law-corresponding-next-level');
  assert.match(law.text, /次一级别相应走势.*周线二买对应日线一买/);
  assert.deepEqual(law.evidence.map(e => e.pdf_page).sort((a, b) => a - b), [47, 48]);
  assert.notEqual(law.ambiguity_status, 'none');
  assert.match(claim(14, 'weekly-hold-large-capital-small-use-daily').text, /50亿以上.*10亿以下/);
  checks.push('缠绕包括三吻，买点定律跨页保留次一级别/相应走势和均线框架；50亿与10亿仅例，不造中间分档算法');
  assert.match(claim(14, 'short-difference-program-reduce-rebuy-order').text, /第一类卖点.*可先减仓.*第一类买点.*回补/);
  assert.match(claim(14, '000503-thirty-sell-five-buy-case').text, /12月1日10:30.*30分钟.*9.7.*12月5日10:25.*5分钟.*9.2/);
  assert.match(claim(14, 'divergence-no-promised-duration-amplitude').text, /不承诺调整时间或幅度/);
  checks.push('短差先次级卖减再买补，000503具体30卖/5买时间价格独立；背驰不承诺调整长短和幅度，不把高效自述当实测最优');
  assert.equal(claim(14, 'macd-double-period-and-double-head-context').ambiguity_status, 'macd_doubled_period_parameters_not_explicitly_supplied');
  assert.doesNotMatch(claim(14, 'macd-double-period-and-double-head-context').text, /24.*52.*18/);
  assert.match(claim(14, 'dec6-week-none-daily-double-head-not-finished').text, /周线不存在.*日线将.*先跌近零轴/);
  assert.match(claim(14, 'macd-lines-and-histogram-combined').text, /都要看、综合看/);
  assert.match(claim(14, '600050-equal-low-not-standard-first-buy').text, /同为2.43.*没有创新低.*不是标准/);
  assert.match(claim(14, '000063-reader-count-corrected-not-endorsed').text, /1999年4月30日为第二类.*2003年1月3日12.69/);
  checks.push('长一倍未补具体MACD参数；周无/日待/30短差分开，线柱综合不造优先级，等低非失败标准点及000063日期纠正保留');
  const plan = JSON.parse(readFileSync(resolve(agent, 'curation/source-audit/stage-c-l013-l014-source-plan.json'), 'utf8'));
  for (const op of plan.operations.filter(x => x.table === 'passages')) {
    const p = graph.db.prepare('SELECT * FROM passages WHERE id=?').get(op.id);
    for (const [k, v] of Object.entries(op.after)) assert.equal(p[k], v, op.id + ':' + k);
    assert.equal(createHash('sha256').update(p.text).digest('hex'), op.text_sha256);
  }
  for (const short of ['0047-b000', '0047-b001']) {
    const p = graph.db.prepare('SELECT role,speaker,published_at FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
    assert.equal(p.role, 'reader'); assert.equal(p.speaker, '瞎鼓捣'); assert.equal(p.published_at, null);
  }
  const figures = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 44 AND 57").all();
  assert.equal(figures.filter(x => x.origin_status === 'later_annotation').length, 9);
  assert.equal(figures.filter(x => x.origin_status === 'unverified').length, 9);
  for (const lesson of ['013', '014']) assert.equal(graph.db.prepare('SELECT processing_status FROM units WHERE id=?').get(`lesson-${lesson}`).processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('14源修正与哈希逐项一致，读者47无伪造时间；18图9后加9未核，43前课图不重算，两课仍with_pending');
  const anchor = law.evidence.find(e => e.pdf_page === 48).id;
  const requests = [
    ['search', { query: '主动带套有两层意思' }, ['search', '主动带套有两层意思']],
    ['concept', { id: '缠中说禅买点定律', limit: 30 }, ['concept', '缠中说禅买点定律', '--limit', '30']],
    ['neighbors', { id: '缠中说禅短差程序', depth: 1, limit: 100 }, ['neighbors', '缠中说禅短差程序', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 52 }, ['page', '--document-id', 'volume_1.pdf', '--page', '52']],
    ['search', { query: '瞎鼓捣', scope: 'source', limit: 8 }, ['search', '瞎鼓捣', '--scope', 'source', '--limit', '8']],
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
    limits: ['不是Windows成品离线或PDF真实交互验收。', '同模型边界检查不是独立审查，不证明吻/买点定律/短差程序的收益、胜率、最优性、专利权或统一后的跨课算法。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l013-l014-verification.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
