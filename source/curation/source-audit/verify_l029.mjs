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
const claim = slug => { const c = graph.getClaim('upper-l029-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l029-c-stage-%' AND review_status='reviewed'").get().n, 38);
  assert.match(claim('divergence-reversal-theorem-three-outcomes').text, /趋势的背驰.*最后一个中枢.*更大级别的盘整.*以上级别的反趋势/);
  assert.notEqual(claim('divergence-reversal-theorem-three-outcomes').ambiguity_status, 'none');
  assert.match(claim('rebound-must-touch-dd-not-zd').review_note, /DD为.*不是ZD中枢下沿/);
  assert.match(claim('down-plus-consolidation-requires-larger-center').conditions.join(''), /完成走势类型/);
  assert.match(claim('down-plus-up-may-be-same-level').text, /不要求.*5分钟下跌后接5分钟上涨/);
  checks.push('38条新增；三类定理保留趋势/最后/更大盘整/以上反趋势，DD非ZD，反趋势允许同级而两完成类型的盘整须更大');

  assert.match(claim('nine-one-minute-count-conditional-illustration').conditions.join(''), /假设均为1分钟.*统一计量/);
  assert.match(claim('nine-one-minute-count-conditional-illustration').review_note, /9个依赖.*非所有趋势刚好9段/);
  assert.match(claim('last-center-expansion-one-unfinished-type').text, /一个未完成.*两个完成/);
  assert.match(claim('expansion-regroups-a-tilde-and-may-evolve').text, /可继续.*也可有其他演化/);
  assert.match(claim('trend-completion-final-leg-sublevel-below-divergence').review_note, /未在此提供.*充分确认/);
  assert.match(claim('previous-type-last-center-not-reassigned-forward').text, /前一个走势类型.*不能把前面归到后面/);
  checks.push('9段统一计量须另设a/b/c均1分；扩展仍一个未完成类型，30分下跌仅后续可能；末段小背驰与前后类型归属不能补成充分完结算法');

  assert.match(claim('first-sublevel-rebound-heuristic-not-absolute').text, /并不绝对/);
  assert.match(claim('feb6-first-rebound-enters-last-center-case-judgment').text, /完全排除/);
  assert.notEqual(claim('feb6-first-rebound-enters-last-center-case-judgment').ambiguity_status, 'none');
  assert.match(claim('no-v-prejudgment-from-this-theorem').text, /不由本章定理解决/);
  const quotes = graph.db.prepare("SELECT e.quote FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.id LIKE 'upper-l029-c-stage-%'").all();
  assert.ok(quotes.every(e => !e.quote.includes('（备注：')));
  assert.ok(source('0206-b003').text.includes('（备注：第一次'));
  assert.ok(source('0209-b000').text.includes('（备注：趋势背驰'));
  assert.notEqual(claim('first-buy-safe-profit-rare-weak-author-claim').ambiguity_status, 'none');
  checks.push('首次回抽通论非绝对与个例完全排除并存；两处未署名备注原文保留但未作作者命题引文；V预判明确超本章，安全/效率/概率未实测');

  assert.match(claim('one-minute-lowest-three-k-only-if-chosen').text, /如果把1分钟当最低级别.*如果把每笔成交当最低/);
  assert.ok(claim('one-minute-lowest-three-k-only-if-chosen').conditions.length);
  assert.match(claim('one-minute-lowest-three-k-only-if-chosen').review_note, /每笔成交非后期几何笔/);
  assert.notEqual(claim('one-minute-lowest-three-k-only-if-chosen').ambiguity_status, 'none');
  assert.match(claim('large-breakout-one-divergence-may-only-intraday').text, /可能只完成盘中震荡.*大级别背驰段.*二买初升或主升/);
  assert.match(claim('600640-nesting-before-small-signal-and-third-fall').review_note, /不认可读者13:45/);
  checks.push('三K中枢仅自选最低1分口径，每笔成交非几何笔；大级别背驰段与初升/主升不同，小信号可盘中化解，读者600640点位未认证');

  assert.match(claim('small-capital-or-skilled-exit-rebuy-third').conditions.join(''), /特别小，或/);
  assert.ok(claim('first-wave-exit-ignore-weak-with-rare-exceptions').exceptions.length);
  assert.match(claim('retest-select-reached-center-prefer-break-and-hold').review_note, /最好而非.*唯一必要/);
  assert.match(claim('average-area-rough-definition-macd-measure-proof-absent').review_note, /测度论证明未在此给出.*读者.*不是作者认可/);
  assert.match(claim('gap-question-capital-level-daily-leg-nested-exit').text, /按资金选日线或30分.*日线背驰段再用区间套/);
  checks.push('小资金或熟练、最好突破站稳、弱股例外均保留；均线面积粗糙/MACD辅助不补测度论证明，操作级别与大背驰段限制独立');

  assert.equal(source('0210-b001').published_at, '2007-02-09 15:09:19');
  for (const short of ['0210-b002', '0210-b003']) assert.equal(source(short).published_at, '2007-02-12 15:15:26');
  assert.equal(source('0212-b000').role, 'reader');
  assert.equal(source('0213-b002').role, 'reader');
  const figs = graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 204 AND 213").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 4);
  assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 8);
  assert.equal(figs.filter(f => /署.*张大山习作/.test(f.note)).length, 4);
  assert.match(figs.find(f => f.id.endsWith('p0208-fig1')).note, /20080703—0718/);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-029'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('2解盘日期修正而前段不改，读者问题仍隔离；12图4后加8未核含4张大山习作，2008年7月后图不混2007作者原发，全书未完成');
  const anchor = claim('rebound-must-touch-dd-not-zd').evidence[0].id;
  const requests = [
    ['search', { query: '预先判断V型反转不由本章定理解决' }, ['search', '预先判断V型反转不由本章定理解决']],
    ['concept', { id: '缠中说禅背驰-转折定理', limit: 20 }, ['concept', '缠中说禅背驰-转折定理', '--limit', '20']],
    ['neighbors', { id: '超跌', depth: 1, limit: 100 }, ['neighbors', '超跌', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 206 }, ['page', '--document-id', 'volume_1.pdf', '--page', '206']],
    ['search', { query: '精确的背驰定义', scope: 'source', limit: 8 }, ['search', '精确的背驰定义', '--scope', 'source', '--limit', '8']],
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
      '未验证实际收益保证、唯一中枢分段、未署名备注作者身份、完整测度论证明或所有级别算法。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l029-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
