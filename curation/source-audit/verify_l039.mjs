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
const claim = slug => { const c = graph.getClaim('upper-l039-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l039-c-stage-%' AND review_status='reviewed'").get().n, 28);
  assert.match(claim('a-plus-A-regroup-five-types-and-A-contains-thirty-center').text, /a规整为5分.*m段5分.*A包含30分/);
  assert.match(claim('a-plus-A-regroup-five-types-and-A-contains-thirty-center').review_note, /不静改A本身必为一个纯30分中枢/);
  assert.match(claim('A0-a-odd-down-even-up-A1-not-break-a-low').text, /奇数为向下、偶数为向上.*A1不得跌破a低点/);
  assert.match(claim('A2-break-a-high-A3-not-return-absorb-into-a-prime').text, /A2升破a高点且A3不跌回a高点/);
  assert.match(claim('general-A3-break-a-high-three-form-thirty-center').review_note, /等于a高点未被此句单列/);
  checks.push('28新增；a正规化5分、A含30分中心非等于纯中心；向上A0起奇下偶上和A1条件，A2突破且A3不回才吸收，A3破高三段成中心保留前提及等值未详');

  assert.match(claim('compare-Ai-Ai-plus-two-force-consolidation-method').review_note, /i与i\+2同向而非相邻异向/);
  assert.match(claim('pair-divergence-even-i-plus-two-sell-odd-buy').text, /i\+2为偶数卖出.*奇数买入/);
  const even = claim('no-divergence-even-hold-until-protection-break-then-exit');
  assert.match(even.text, /无盘背且i偶.*Ai\+3不跌破Ai高点.*Ai\+k\+3跌破Ai\+k高点.*Ai\+k\+4卖出.*k为偶数/);
  assert.equal(even.conditions.length, 1);
  const odd = claim('no-divergence-odd-stay-cash-until-protection-break-rebuy');
  assert.match(odd.text, /无盘背且i奇.*Ai\+3不升破Ai低点.*Ai\+k\+3升破Ai\+k低点.*Ai\+k\+4回补/);
  assert.notEqual(odd.ambiguity_status, 'none');
  assert.match(odd.review_note, /没有重新写取值约定/);
  checks.push('比较Ai/i+2，先盘背奇偶买卖，未盘背才用保护位及后续弱势段联合；偶支k偶明写，奇支沿记号无重写，不把破位压成立即同价成交');

  assert.notEqual(claim('new-Ai-plus-two-not-rewrite-prior-unique-decomposition').ambiguity_status, 'none');
  assert.match(claim('center-can-grow-thirty-to-year-still-five-pair-operation').review_note, /高层中心升级与固定低层分解/);
  assert.match(claim('two-pattern-classes-divergence-vs-protected-continuation').review_note, /不.*互斥穷尽.*90%读者头晕为修辞非预测准确率/);
  assert.match(claim('step-wrong-stop-adjust-mind-rhythm-before-resume').text, /停止操作.*再继续/);
  assert.notEqual(claim('physiological-response-from-training-author-analogy').ambiguity_status, 'none');
  checks.push('未来段不回写已完唯一是作者主张，高层可升级不取消38低层规则；两类总结非已证穷尽，90%读者头晕非准确率，生理反应只是类比，失步暂停不许诺盈利');

  assert.match(claim('no-high-exit-low-purchase-is-add-not-repurchase').text, /加仓.*不是回补/);
  const typo = claim('small-capital-sell-all-buy-original-contradictory-wording');
  assert.notEqual(typo.ambiguity_status, 'none');
  assert.match(typo.text, /卖就全买/); assert.match(source('0290-b002').text, /卖就全买/);
  assert.match(typo.review_note, /不静改全卖/);
  assert.match(claim('fearful-entry-can-split-two-no-proportions').review_note, /两笔是次数而非必等额50%/);
  assert.notEqual(claim('not-lowest-print-may-be-underwater-direction-author-view').ambiguity_status, 'none');
  assert.equal(source('0290-b004').role, 'reader');
  assert.notEqual(claim('theory-europe-us-same-futures-certificate-variable-source-scope').ambiguity_status, 'none');
  checks.push('高未卖后买是加仓，分两笔非50%；卖就全买原页原字歧义不修成全卖，大方向没问题非风险保证；欧美制度属读者、期货凭证即时可变变量未定义');

  assert.match(claim('mar23-1325-minimum-divergence-not-five-return-center').text, /否定该级别.*最小级别背驰/);
  assert.match(claim('mar23-1325-minimum-divergence-not-five-return-center').review_note, /没有给最小级确为1分\/线段/);
  assert.equal(source('0289-b015').role, 'reader');
  assert.match(claim('mar26-pressure-break-still-needs-confirmation').text, /有效性仍需确认/);
  assert.match(claim('mar26-second-line-ten-fifteen-and-third-line-regulatory-risk').review_note, /非二三线定义或现价推荐/);
  assert.match(claim('corrected-sector-rotation-not-only-third-line').review_note, /未认可读者对601333的动员/);
  checks.push('13:25最小级不等5分、未命名确为1分或线段，图周期不改结构；3/23未破和3/26突破待确认分时，历史10/15元和监管观点非今推荐，读者动员未认证');

  for (const p of ['0288-b005', '0289-b000', '0289-b001']) assert.equal(source(p).published_at, '2007-03-26 15:20:49');
  assert.equal(source('0288-b004').published_at, '2007-03-23 15:18:15');
  assert.match(source('0288-b004').text, /2007-03-2615:20:49$/);
  const links = {
    'compare-Ai-Ai-plus-two-force-consolidation-method': ['0288-b001', ['0288-fig1', '0288-fig2']],
    'pair-divergence-even-i-plus-two-sell-odd-buy': ['0288-b001', ['0288-fig1', '0288-fig2']],
    'no-divergence-even-hold-until-protection-break-then-exit': ['0288-b001', ['0288-fig2']],
    'no-divergence-odd-stay-cash-until-protection-break-rebuy': ['0288-b001', ['0288-fig1']],
    'mar23-pressure-line-not-effectively-broken-patience': ['0288-b003', ['0290-fig1']],
    'mar26-pressure-break-still-needs-confirmation': ['0288-b005', ['0290-fig1']],
    'mar23-1325-minimum-divergence-not-five-return-center': ['0289-b016', ['0290-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f)); assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 288 AND 290").all();
  assert.equal(figs.length, 3); assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 1);
  assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 2);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-039'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('3段改3/26且前段尾头字符留存；7命题9配图逐项确认，2公式示意原发未核1行情后加；原字及全书待核不伪称完成');

  const anchor = odd.evidence[0].id;
  const requests = [
    ['search', { query: 'Ai与Ai+2盘背时' }, ['search', 'Ai与Ai+2盘背时']],
    ['concept', { id: '监管风险', limit: 20 }, ['concept', '监管风险', '--limit', '20']],
    ['neighbors', { id: '同级别分解', depth: 1, limit: 100 }, ['neighbors', '同级别分解', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 288 }, ['page', '--document-id', 'volume_1.pdf', '--page', '288']],
    ['search', { query: '卖就全买', scope: 'source', limit: 8 }, ['search', '卖就全买', '--scope', 'source', '--limit', '8']],
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
    intended_figure_links_checked: { claims: 7, associations: 9, unique_figures: 3 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未补全k/等值/完成/成交算法，未修源字歧义或定义期货凭证变量，未认证历史风险收益与现行制度。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l039-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
